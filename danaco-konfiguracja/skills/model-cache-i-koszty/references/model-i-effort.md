# Model i effort — konfiguracja szczegółowa

Źródła: `cc:model-config`, `cc:settings-reference` (availableModels, deniedModels,
availableModelsMatch, enforceAvailableModels, modelSettings, maxEffortLevel, fallbackModel,
switchModelsOnFlag, modelOverrides, modelPicker), `cc:fast-mode`, `cc:advisor`, próby 2.1.286.

## Spis treści

1. Aliasy
2. Wybór i ograniczanie modelu
3. Model zapasowy i automatyczne przełączanie
4. Effort i myślenie
5. Kontekst i kompakcja
6. Dostawcy chmurowi i bramy

## 1. Aliasy

| Alias | Znaczenie |
|---|---|
| `default` | czyści nadpisanie: domyślny konta (Pro/Max/Team/Enterprise/API/Bedrock/Agent Platform: Opus 5.5; Foundry: Sonnet 4.5) albo domyślny organizacji |
| `best` | `fable`, gdzie dostępny, inaczej `opus` |
| `fable`, `opus`, `sonnet`, `haiku` | najnowszy model rodziny dla dostawcy (np. Bedrock: `sonnet` → Sonnet 4.5) |
| `opus[1m]`, `sonnet[1m]` | okno 1M (dla modeli z natywnym 1M bez znaczenia) |
| `opusplan` | Opus w trybie planu, Sonnet w wykonaniu — każde przełączenie planu to zmiana modelu (cache) |

Przypinanie wersji: pełny identyfikator (`claude-opus-5-5`) albo `ANTHROPIC_DEFAULT_OPUS_MODEL`
(… `_SONNET_`, `_HAIKU_`, `_FABLE_`). Podagenci bez `model`: `CLAUDE_CODE_SUBAGENT_MODEL`.
`ANTHROPIC_SMALL_FAST_MODEL` — przestarzała (→ `ANTHROPIC_DEFAULT_HAIKU_MODEL`).

## 2. Wybór i ograniczanie modelu

- Kolejność: `/model` → `--model` → `ANTHROPIC_MODEL` → `model` → `ANTHROPIC_DEFAULT_MODEL`.
  `/model` w trybie interaktywnym zapisuje wybór w ustawieniach użytkownika (`s` — tylko sesja);
  w `-p` tylko sesja (≥2.1.205).
- `availableModels` obejmuje: model główny, rozwiązywanie aliasów, fast mode, podagentów
  i członków zespołu, `model` skilli i poleceń, `advisorModel`, agentów w tle. Zablokowany wybór:
  `/model` — błąd; `--model`/`ANTHROPIC_MODEL`/`model` — zamiana na domyślny (w `-p` po cichu,
  próba); podagent — model zapasowy; skill — model sesji; `--advisor` — błąd startu.
- Wpis z konkretną wersją wyłącza wieloznaczność rodziny: `["sonnet","claude-sonnet-4-5"]`
  = tylko Sonnet 4.5.
- `enforceAvailableModels: true` (z niepustą listą) — opcja Default też podlega liście.
  `availableModels: []` blokuje wszystkie nazwane wybory.
- `deniedModels`, `availableModelsMatch: "exact"` — tylko w zarządzanych (gdzie indziej
  ignorowane z ostrzeżeniem), ≥2.1.283; Default schodzi do najnowszej dozwolonej wersji rodziny,
  potem tańszych rodzin.
- Zarządzane `availableModels` nie są scalane między źródłami ani z niższymi warstwami.
  Wyjątek: host z `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` dostarcza własną konfigurację modeli.
- Restrykcje organizacji Enterprise (konsola) działają niezależnie od ustawień i obejmują
  logowanie oraz klucz użytkownika (nie klucze usługowe organizacji); Haiku zawsze dostępny.
- `modelOverrides` — mapowanie identyfikatorów Anthropic na identyfikatory dostawcy (ARN,
  wdrożenia Foundry); lista dozwolonych sprawdzana na identyfikatorze Anthropic.
- `modelPicker` (użytkownik lub zarządzane) — własne wiersze `/model`.

Pełna kontrola modelu stanowisk: `availableModels` + `enforceAvailableModels` + (opcjonalnie)
`deniedModels` + `model` + `env.ANTHROPIC_DEFAULT_*_MODEL` — jeden komplet w najwyższym
dostarczanym źródle zarządzanym.

## 3. Model zapasowy i automatyczne przełączanie

| Mechanizm | Wyzwalacz | Zakres | Konfiguracja |
|---|---|---|---|
| łańcuch zapasowy | przeciążenie, niedostępność, nieponawialny błąd serwera (nie: uwierzytelnienie, rozliczenia, limity, rozmiar) | tylko bieżąca tura; max 3 modele; także podagenci (≥2.1.247) i kompakcja (bez mniejszego okna) | `--fallback-model a,b`, `fallbackModel: [...]` |
| przełączenie po klasyfikatorze | oznaczenie treści (cyberbezpieczeństwo, biologia) na Fable, Opus 5.5, Sonnet 5.5, Opus 5 | **sesja zostaje** na modelu zapasowym | `switchModelsOnFlag` (domyślnie `true`); w `-p` przy `false` — odmowa |

Cele przełączenia (≥2.1.219): Fable/Opus 5.5 — biologia → Opus 5, cyber → Opus 4.8;
Sonnet 5.5 — cyber → Sonnet 5, biologia — odmowa; Opus 5 — cyber → Opus 4.8. Cel spoza
`availableModels` — odmowa zamiast przełączenia. Na Bedrock/Agent Platform/Foundry wymagane
przypięcia `ANTHROPIC_DEFAULT_OPUS_MODEL` (i `_FABLE_`, `_SONNET_`). Diagnoza fałszywych
oznaczeń: `claude --safe-mode` (bez CLAUDE.md, skilli, MCP, hooków). Hooki `PreModelSwitch`
/`PostModelSwitch` pozwalają zatwierdzać i rejestrować zmiany modelu.

## 4. Effort i myślenie

| Model | Poziomy | Domyślny |
|---|---|---|
| Fable 5.1, Fable 5 | low…max (z xhigh) | high |
| Opus 5.5, Sonnet 5.5 | low…max (z xhigh) | **medium** |
| Opus 5, Sonnet 5, Opus 4.8 | low…max (z xhigh) | high |
| Opus 4.7 | low…max (z xhigh) | xhigh |
| Opus 4.6, Sonnet 4.6 | low, medium, high, max | high |

- Nieobsługiwany poziom → najwyższy obsługiwany niższy (np. `xhigh` → `high` na Opus 4.6).
- `effortLevel` i `modelSettings.<model>.effortLevel`: `low|medium|high|xhigh` (bez `max`,
  bez `ultracode`); `max` tylko na sesję (lub `CLAUDE_CODE_EFFORT_LEVEL=max`).
- Starszy klucz `effortLevel` z ustawień użytkownika **nie dotyczy Opus 5.5** — używaj
  `modelSettings`.
- `maxEffortLevel` (≥2.1.267) — sufit dla wszystkich źródeł, także frontmattera skilli i
  podagentów; limity organizacji Enterprise per rola działają równolegle.
- `effortLevel` w zarządzanych to tylko wartość startowa — do limitu służy `maxEffortLevel`.
- `ultracode` — ustawienie (workflowy dynamiczne), nie poziom; `--effort ultracode` = `xhigh` +
  ultracode (≥2.1.203); niedostępne przy wyłączonych workflowach.
- `ultrathink` w prompcie — instrukcja w kontekście, effort w API bez zmian.
- Myślenie: Opus 5.5, Sonnet 5.5, Fable — nie da się wyłączyć (`MAX_THINKING_TOKENS=0`,
  `alwaysThinkingEnabled: false` bez skutku); Opus/Sonnet 4.6 — stały budżet przez
  `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` + `MAX_THINKING_TOKENS`.
- Próba: żądanie zawiera `thinking: {"type":"adaptive"}` i `output_config.effort`; zmiana
  effortu nie zmienia bloków instrukcji (Opus 5.5/Sonnet 5.5 na API/subskrypcji — cache zostaje).

## 5. Kontekst i kompakcja

- Okno 1M natywnie: Fable, Sonnet 5+, Opus 4.7+ (API); Opus/Sonnet 4.6 przez `[1m]`.
  `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` — kompakcja przy 200K.
- Próg kompakcji: `/autocompact 500k` (zapis `autoCompactWindow`), `--autocompact` (jedno
  uruchomienie), `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (wygrywa); 100K–1M; domyślnie dla 1M ok. 967K.
- Brama/własny identyfikator: `CLAUDE_CODE_MAX_CONTEXT_TOKENS` (zasady zależne od rozpoznania
  identyfikatora), `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1`.

## 6. Dostawcy chmurowi i bramy

- Przypinaj wersje `ANTHROPIC_DEFAULT_*_MODEL` od początku (aliasy dostawcy opóźniają się).
- Opisy i możliwości przypiętych modeli: `…_MODEL_NAME`, `…_MODEL_DESCRIPTION`,
  `…_MODEL_SUPPORTED_CAPABILITIES` (`effort`, `xhigh_effort`, `max_effort`, `thinking`,
  `adaptive_thinking`, `interleaved_thinking`).
- Ustawienia serwerowe nie docierają do Bedrock/Agent Platform/Foundry/Claude Platform on AWS —
  `availableModels` dostarczaj plikiem zarządzanym/MDM.
- Organizacyjny model domyślny i restrykcje działają tylko na API Anthropic (i bramach LLM
  dla restrykcji).
