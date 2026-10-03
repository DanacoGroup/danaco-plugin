---
name: model-cache-i-koszty
description: >
  Wybór i ograniczanie modelu w Claude Code (aliasy, kolejność ustawiania, availableModels,
  enforceAvailableModels, deniedModels, fallbackModel, automatyczne przełączanie po
  klasyfikatorze, opusplan), poziomy effort (effortLevel, modelSettings, maxEffortLevel,
  ultracode), prompt cache (prefiks, TTL 5m/1h, promptCacheTtl, co unieważnia cache, zakres
  między sesjami i dzierżawcami, rotacja kont), koszty (/usage, modelPricing, --max-budget-usd)
  i OpenTelemetry (metryki, zdarzenia, blokada kolektora). Stosuj przy pytaniach „który
  model”, „dlaczego drogo”, „cache nie trafia”, „TTL”, „limit effortu”, „telemetria”,
  „koszty zespołu/usługi”.
---

# Model, effort, prompt cache, koszty, telemetria

## Kiedy stosować

Gdy trzeba ustalić, **na jakim modelu i z jakim wysiłkiem** działa sesja, kto może to zmienić,
ile to kosztuje i czy cache działa. Dotyczy stanowisk, floty i usług osadzających CLI.

## Kolejność rozstrzygania

| Co | Kolejność (pierwsze wygrywa) |
|---|---|
| model | `/model` w sesji → `--model` → `ANTHROPIC_MODEL` → `model` w ustawieniach → `ANTHROPIC_DEFAULT_MODEL` → domyślny konta/organizacji; wznowienie przywraca model sesji (chyba że flaga/zmienna) |
| ograniczenie | `availableModels` (zarządzane: tylko jedna lista, bez scalania) + `deniedModels`/`availableModelsMatch` (tylko zarządzane, ≥2.1.283) + `enforceAvailableModels` (opcja Default) + restrykcje organizacji Enterprise |
| effort | `CLAUDE_CODE_EFFORT_LEVEL` / `--effort` / `/effort` → `modelSettings`/`effortLevel` → domyślny modelu (Opus 5.5 i Sonnet 5.5: `medium`; inne: `high`; Opus 4.7: `xhigh`); sufit `maxEffortLevel` i limity organizacji zawsze |
| TTL cache | `FORCE_PROMPT_CACHING_5M` → zmienna kubełka → ustawienie (`promptCacheTtl`, `subagentPromptCacheTtl`) → `experimental.cacheTtl` podagenta → `ENABLE_PROMPT_CACHING_1H` → domyślne (subskrypcja w limicie: główna rozmowa 1h; klucz API/chmura/kredyty: 5m) |
| model zapasowy | `--fallback-model` → `fallbackModel` (maks. 3, filtr `availableModels`, tylko na turę) |

## Decyzje

| Sytuacja | Ustawienie |
|---|---|
| zespół ma pracować na określonej rodzinie | zarządzane: `availableModels` + `enforceAvailableModels: true` (+ `env.ANTHROPIC_DEFAULT_*_MODEL` dla wersji) |
| wstrzymać nową wersję | `deniedModels` lub `availableModelsMatch: "exact"` + `requiredMinimumVersion` (starsze CLI ignorują klucze) |
| ograniczyć koszt rozumowania | `maxEffortLevel` (sufit, także dla frontmattera), domyślnie `modelSettings.<model>.effortLevel` |
| usługa z kluczem API i przerwami > 5 min | `promptCacheTtl: "1h"` (droższy zapis, tańszy powrót); krótkie serie bez przerw — `5m` |
| usługa wielodzierżawna, wspólna instrukcja | identyczna instrukcja i narzędzia, **pamięć automatyczna wyłączona** (ścieżka pamięci jest w instrukcji systemowej — próba), ten sam model i effort |
| rotacja wielu kont | cache jest per organizacja — przyklejaj rozmowę do konta, rotuj nowe rozmowy, nie tury |
| raporty kosztów wg umowy | `modelPricing` (tylko zarządzane) — dotyczy `/usage`, `total_cost_usd`, `--max-budget-usd`, OTel |
| telemetria organizacji | zarządzane `env`: `CLAUDE_CODE_ENABLE_TELEMETRY=1`, eksportery, `OTEL_EXPORTER_OTLP_ENDPOINT` (blokuje przekierowanie sygnałów przez użytkownika) |

## Procedura

1. Ustal stan: `/status`, `/model`, `/usage` (linia `Prompt cache (main)` ≥2.1.251, przyczyna
   chybienia ≥2.1.260); w `-p` — `init.model` i `result.usage`/`modelUsage`.
2. Zaprojektuj ustawienia z `examples/` i zwaliduj:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/waliduj_ustawienia.py" PLIK --rodzaj … --cli claude`.
3. Sprawdź, co CLI wysyła (bez modelu): `${CLAUDE_PLUGIN_ROOT}/scripts/proba_cli.py -- <flagi>` i
   `scripts/zadania_cache.py <katalog>/zadania [--porownaj <inny>/zadania]` — model, effort,
   znaczniki `cache_control` z TTL, skróty instrukcji i narzędzi.
4. Zmierz cache na prawdziwych sesjach:
   `scripts/analiza_cache.py ~/.claude/projects/<projekt>/ --ttl-s 3600 [--ceny ceny.json]`
   — udział wejścia z cache, chybienia z prawdopodobną przyczyną, przerwy ponad TTL.
5. Wdróż telemetrię (referencja `koszty-i-telemetria.md`) i sprawdź metrykę
   `claude_code.session.count` lub zdarzenie `claude_code.user_prompt` w kolektorze.

## Pułapki

- Zmiana modelu, effortu (poza Opus 5.5/Sonnet 5.5/Fable 5.1 na API/subskrypcji), włączenie
  fast mode, MCP/narzędzia bez tool search, odmowa całego narzędzia, kompakcja, obrazy,
  aktualizacja CLI — unieważniają cache. CLAUDE.md, tryb uprawnień, styl wyjścia, skille — nie.
- `model` w ustawieniach to **wybór początkowy**, nie wymuszenie — Default w `/model` omija go
  bez `enforceAvailableModels`.
- Model spoza `availableModels` podany `--model` w `-p` jest **po cichu** zastąpiony domyślnym
  (próba 2.1.286: brak komunikatu na stderr) — host porównuje `init.model` z oczekiwanym.
- Osobny `CLAUDE_CONFIG_DIR` na dzierżawcę + włączona pamięć automatyczna = inna instrukcja
  systemowa dla każdego dzierżawcy (ścieżka pamięci) — brak wspólnego cache (próba).
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` przywraca identyczny prefiks.
- Klucz API: domyślny TTL 5 min (próba: znaczniki `ttl` brak/`5m`); subskrypcja w limicie: 1h.
  Po wejściu w kredyty główna rozmowa spada do 5m, chyba że `promptCacheTtl: "1h"`.
- `DISABLE_PROMPT_CACHING=1` usuwa wszystkie znaczniki `cache_control` (próba) — tylko do diagnozy.
- Brama z `ANTHROPIC_BASE_URL` musi przekazywać `cache_control` i nagłówek `anthropic-beta`
  (`extended-cache-ttl-…`); bez tool search każda zmiana narzędzi MCP unieważnia cache.
- `max` i `ultracode` nie są akceptowane w `effortLevel`/`modelSettings`; `max` z `/effort`
  działa tylko w sesji; `ultrathink` w prompcie nie zmienia effortu w API.
- Automatyczne przełączenie po klasyfikatorze (Opus 5.5 → Opus 4.8/Opus 5) **zostaje** na
  modelu zapasowym; w `-p` przy `switchModelsOnFlag: false` tura kończy się odmową.
- `OTEL_*` w `.claude/settings.json` projektu są ignorowane; `OTEL_*` nie trafiają do
  podprocesów (Bash, hooki, MCP).
- `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_RAW_API_BODIES` wysyłają treści
  — w usługach z danymi klientów domyślnie wyłączone.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `enforceAvailableModels` | 2.1.175 |
| organizacyjny model domyślny | 2.1.196 |
| łańcuch `fallbackModel` dla podagentów | 2.1.247 |
| `promptCacheTtl`, `subagentPromptCacheTtl`, `modelPricing`, `modelPicker` | 2.1.242 |
| `cacheTtl` w `experimental` podagenta | 2.1.248 |
| `modelSettings`, linia `Prompt cache (main)` | 2.1.251 |
| przyczyna chybienia cache w `/usage` | 2.1.260 |
| `maxEffortLevel` | 2.1.267 |
| `modelPricing.multiplier` > 1 | 2.1.271 |
| Opus 5.5 / Sonnet 5.5 | 2.1.280 / 2.1.284 |
| `deniedModels`, `availableModelsMatch` | 2.1.283 |

## Szablony

- `examples/polityka-modeli.managed.settings.json` — lista modeli, wymuszenie Default, blokada wersji, sufit effortu, stawki, OTel z blokadą kolektora.
- `examples/oszczedny.user.settings.json` — model, effort per model, łańcuch zapasowy, TTL, próg kompakcji.
- `examples/produkt-cache.flaga.settings.json` — usługa: stały model i lista, TTL 1h dla obu kubełków, pamięć wyłączona (próba: `ttl: 1h` także z kluczem API).
- `examples/ceny-przyklad.json` — format stawek dla `analiza_cache.py --ceny` (stawki przykładowe — wpisz własne z cennika lub umowy).

## Referencje

- `references/model-i-effort.md` — aliasy, ograniczanie, fallback, klasyfikator, effort, kontekst i kompakcja, dostawcy chmurowi.
- `references/prompt-cache.md` — warstwy prefiksu, co unieważnia i co zachowuje cache, TTL, zakres, podagenci, bramy, próby.
- `references/koszty-i-telemetria.md` — `/usage`, `modelPricing`, limity, OpenTelemetry (zmienne, metryki, zdarzenia, prywatność).
