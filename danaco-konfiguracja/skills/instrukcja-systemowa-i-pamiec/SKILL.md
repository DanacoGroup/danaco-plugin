---
name: instrukcja-systemowa-i-pamiec
description: >
  Instrukcja systemowa i pamięć Claude Code: --system-prompt(-file), --append-system-prompt(-file),
  --append-subagent-system-prompt(-file), --system-prompt-snapshot, znacznik
  __SYSTEM_PROMPT_DYNAMIC_BOUNDARY__, --exclude-dynamic-system-prompt-sections, co CLI dokłada
  poza instrukcją (przypomnienia, CLAUDE.md, git, atrybucja), CLAUDE.md i jego hierarchia,
  importy @, .claude/rules z paths, AGENTS.md, claudeMd i claudeMdExcludes, pamięć
  automatyczna (MEMORY.md, autoMemoryDirectory), style wyjścia. Stosuj, gdy pada „instrukcja
  systemowa”, „zastąp/dopisz prompt”, „CLAUDE.md nie działa”, „pamięć”, „reguły ścieżkowe”,
  „styl wyjścia”, „tożsamość agenta produktu”, „instrukcja nie zmienia się po --resume”.
---

# Instrukcja systemowa i pamięć

## Kiedy stosować

Gdy decydujesz, **jaki tekst** dostaje model i **gdzie** go umieścić: w instrukcji
systemowej (flagi), w kontekście rozmowy (CLAUDE.md, reguły, pamięć, hooki), w stylu wyjścia,
w skillu. Każde miejsce ma inną trwałość, koszt i wpływ na cache.

## Gdzie umieścić tekst

| Treść | Miejsce | Dlaczego |
|---|---|---|
| tożsamość i zasady agenta innego niż Claude Code (produkt, czat, nie-kod) | `--system-prompt-file` | zastępuje domyślną instrukcję; odpowiadasz za zasady narzędzi i bezpieczeństwa |
| dodatkowe zasady dla agenta kodującego | `--append-system-prompt(-file)` | nic nie zabiera z instrukcji Claude Code |
| część stała + zmienna w jednej instrukcji | wiersz `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` (≥2.1.275) | część nad znacznikiem w cache wspólnym; podział tylko przy bezpośrednim API |
| zasady wspólne wszystkim podagentom | `--append-subagent-system-prompt(-file)` (tylko `-p`) | podagenci nie dostają instrukcji sesji |
| konwencje projektu (polecenia, architektura, styl kodu) | `CLAUDE.md` | ładowany w każdej sesji, wersjonowany z repozytorium |
| zasady dla części kodu | `.claude/rules/*.md` z `paths:` | ładowane tylko przy pasujących plikach |
| zasady organizacji | zarządzany `CLAUDE.md` / `claudeMd` w managed | nie da się wykluczyć |
| głos, format, rola dla całej sesji | styl wyjścia (`outputStyle`) | przełączany bez restartu (od 2.1.251 bez unieważnienia cache) |
| wiedza na żądanie | skill | koszt tylko po wywołaniu |
| reguła obowiązkowa | hook | gwarancja zamiast prośby |
| fakty zmienne (stan, gałąź, plan klienta) | hook `SessionStart` (`additionalContext`) albo część pod znacznikiem | nie psuje części stałej |

## Co trafia do modelu niezależnie od flag

- `system[0]`: blok rozliczeniowy (wersja, skrót) — `CLAUDE_CODE_ATTRIBUTION_HEADER=0` go usuwa
  (cache na bezpośrednim API bez wpływu);
- `system[1]`: wiersz tożsamości („You are a Claude agent, built on Anthropic's Claude Agent
  SDK.” w `-p`) — zostaje także przy `--system-prompt`;
- przypomnienia w wiadomościach (`<system-reminder>`): CLAUDE.md, styl wyjścia, atrybucja
  `Co-Authored-By`, kontekst hooków, lista skilli i agentów, instrukcje serwerów MCP,
  „# Environment” (katalog, system, data), zmiany plików;
- zasady commitów i PR w **opisie narzędzia Bash** (nie w instrukcji) — wyłącz
  `includeGitInstructions: false` / `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1`.
Przy własnej instrukcji dopisz zdanie, czym są przypomnienia systemowe (kontekst aplikacji,
nie wiadomości użytkownika). Wyłączenia: `attribution` (`commit`/`pr` puste lub `false`
≥2.1.281), `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_ATTACHMENTS=1`
(przypomnienia o zadaniach, zmianach plików, lista skilli), `--setting-sources`.

## Utrwalanie instrukcji (snapshot)

Domyślnie (`--system-prompt-snapshot on`) instrukcja z **pierwszego żądania** jest zapisana
w sesji i obowiązuje do kompakcji — także po `--resume`/`--continue` z innym tekstem flag.
`--system-prompt-snapshot off` (≥2.1.257) przebudowuje ją przy każdym żądaniu: identyczna
treść trafia w cache, zmieniona — dochodzi od razu (kosztem odczytu bez cache). Produkty
ze zmienną instrukcją (nowa wersja, nowa lista narzędzi) — `off`.

## CLAUDE.md — reguły

- Kolejność (scalane, nie nadpisywane; bliższe później): zarządzany → `~/.claude/CLAUDE.md`
  → projekt `./CLAUDE.md` lub `./.claude/CLAUDE.md` (+ katalogi nadrzędne) → `./CLAUDE.local.md`;
  podkatalogi — gdy model czyta tam pliki.
- Cel < 200 wierszy na plik; konkretne, sprawdzalne zdania („uruchom `npm test` przed
  commitem”), sekcje i punkty; sprzeczności usuwaj (`/doctor prompt-audit`, ≥2.1.283).
- Importy `@ścieżka` (względem pliku, do 4 poziomów; spacje `\ `; w backtickach nie importuje).
- Komentarze HTML blokowe są usuwane przed wstrzyknięciem (notatki dla ludzi bez kosztu).
- `.claude/rules/*.md` (także `~/.claude/rules/`), frontmatter `paths:` = reguła warunkowa.
- AGENTS.md: domyślnie gdy brak CLAUDE.md; tryb w `pluginConfigs["agents-md@builtin"].options.instructionFiles`.
- `claudeMdExcludes` (globy ścieżek bezwzględnych, listy się sumują) — nie wyklucza zarządzanego.
- Pliki do 4 MiB ładowane w całości; większe pomijane.

## Pamięć automatyczna

`~/.claude/projects/<projekt>/memory/MEMORY.md` (indeks, pierwsze 200 wierszy lub 25 KB
w każdej sesji) + pliki tematów czytane na żądanie; wspólna dla worktree repozytorium;
nie podlega `cleanupPeriodDays`. Wyłączenie: `autoMemoryEnabled: false`,
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` (wymagane w usługach wielodzierżawnych — `--setting-sources ""`
jej nie odcina). Lokalizacja: `autoMemoryDirectory` (bezwzględna lub `~/`) albo
`CLAUDE_CODE_PROJECT_DIR_NAME` + `CLAUDE_CONFIG_DIR` (jedna pamięć na nazwę). Podagenci
mają własną (`memory:`), nie dziedziczą pamięci sesji.

## Procedura

1. Wybierz miejsce dla każdej treści (tabela wyżej).
2. Instrukcja produktu: część stała → `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` → część zmienna;
   zbuduj i sprawdź: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/instrukcja-systemowa-i-pamiec/scripts/buduj_instrukcje.py" --stala stala.md --zmienna zmienna.md --wyjscie instrukcja.txt`
   (rozmiary, znacznik, zalecane flagi).
3. Pamięć projektu: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/instrukcja-systemowa-i-pamiec/scripts/audyt_pamieci.py" --projekt <katalog>`
   (hierarchia CLAUDE.md, rozmiary, importy, reguły `paths`, MEMORY.md).
4. Próba: `proba_cli.py --szukaj "<fraza z instrukcji>" -- --system-prompt-file …` — czy
   tekst dotarł, ile bloków `system`, co doszło w wiadomościach.
5. W sesji: `/memory`, `/context`, `/status`; żądania na żywo: `OTEL_LOG_RAW_API_BODIES=file:<katalog>`.

## Pułapki

- `--system-prompt` z długim tekstem w `argv` widać w `ps` — używaj `-file`.
- `--system-prompt` i `--system-prompt-file` wykluczają się; dopiski łączą się z każdą.
- `--exclude-dynamic-system-prompt-sections` działa tylko z domyślną instrukcją.
- Znacznik granicy: pierwsze wystąpienie dzieli, kolejne są usuwane; przez bramę LLM
  lub Bedrock/Vertex/Foundry **brak podziału** (próba 2.1.286 przez `ANTHROPIC_BASE_URL`:
  znacznik usunięty, jeden blok `system`).
- Snapshot `on` + `--resume` = stara instrukcja (próba macierzy: nowy tekst pominięty do kompakcji).
- CLAUDE.md to kontekst, nie egzekucja — zakazy przez uprawnienia lub hooki.
- `claudeMd` działa tylko w managed; `outputStyle` z nazwą wbudowaną wielkością liter
  (`Explanatory`) — inna pisownia = styl domyślny.
- Styl wyjścia bez `keep-coding-instructions: true` usuwa inżynierskie instrukcje Claude Code.
- `language` z `--settings` dociera do modelu także przy `--system-prompt` (próba 2.1.286).
- Po kompakcji CLAUDE.md jest wczytywany ponownie; instrukcje z rozmowy mogą zniknąć —
  stałe zasady trzymaj w plikach.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `--append-subagent-system-prompt` | 2.1.205 |
| zmiana stylu bez unieważnienia cache | 2.1.251 |
| `--system-prompt-snapshot` | 2.1.257 |
| `--append-subagent-system-prompt-file` | 2.1.261 |
| flagi instrukcji nie wyłączają już zapisu snapshotu | 2.1.265 |
| `/output-style` w `-p` | 2.1.269 |
| `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` (globalny cache części stałej) | 2.1.275 |
| `attribution: false` | 2.1.281 |
| `/doctor prompt-audit` | 2.1.283 |

## Szablony

- `examples/instrukcja-produktu.txt` — instrukcja z częścią stałą i zmienną (próba: znacznik usunięty).
- `examples/CLAUDE.md` — szablon projektu z importem i komentarzem dla ludzi.
- `examples/.claude/rules/api.md` — reguła ścieżkowa.
- `examples/output-styles/zwiezly-raport.md` — styl wyjścia.
- `examples/pamiec.project.settings.json`, `examples/tozsamosc-produktu.flaga.settings.json` — ustawienia pamięci i wyłączenia kontekstu wbudowanego.

## Referencje

- `references/instrukcja-systemowa.md` — flagi, kolejność, snapshot, znacznik, co dokłada CLI, odpowiedniki SDK.
- `references/pamiec-claude-md.md` — CLAUDE.md, importy, reguły, AGENTS.md, pamięć automatyczna, style wyjścia.
