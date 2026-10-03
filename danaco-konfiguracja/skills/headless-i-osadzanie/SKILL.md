---
name: headless-i-osadzanie
description: >
  Tryb nieinteraktywny Claude Code (-p) i osadzanie CLI w produkcie lub usłudze: formaty
  wejścia/wyjścia (text, json, stream-json), zdarzenia strumienia (system/init, api_retry,
  hook_*, result, permission_denials), żądania sterujące (interrupt), sesje (--session-id,
  --resume, --fork-session, --no-session-persistence), izolacja dzierżawców
  (CLAUDE_CONFIG_DIR, CLAUDE_CODE_PROJECT_DIR_NAME), --bare, --setting-sources,
  --disable-slash-commands, --json-schema, --max-turns, --max-budget-usd, SIGTERM vs SIGINT,
  rotacja kont a cache, odpowiedniki Agent SDK i Claude Managed Agents. Stosuj, gdy pada
  „claude -p”, „skrypt/CI”, „osadzić Claude Code w aplikacji”, „stream-json”, „wznowienie
  sesji”, „wielu użytkowników”, „wyjście strukturalne”, „przerwanie tury”.
---

# Headless i osadzanie CLI w produkcie

## Kiedy stosować

Gdy Claude Code działa **bez człowieka przy terminalu**: skrypt, CI, zadanie cykliczne, usługa
wywołująca CLI dla wielu użytkowników (jak Danaco Nexus), aplikacja na Agent SDK (SDK
uruchamia tę samą binarkę). Każda decyzja tutaj dotyczy determinizmu, izolacji i kosztu.

## Profil uruchomienia usługi (szkielet)

```sh
claude -p \
  --input-format stream-json --output-format stream-json --verbose \
  --include-partial-messages --include-hook-events --replay-user-messages \
  --setting-sources "" --settings "$WYDANIE/ustawienia.json" \      # izolacja od plików + polityka produktu
  --strict-mcp-config --mcp-config "$RUN/mcp.json" \
  --tools "<jawna lista>" --permission-mode dontAsk --permission-prompts none \
  --disable-slash-commands \                                        # klient nie steruje sesją przez /…
  --system-prompt-file "$RUN/instrukcja.txt" --system-prompt-snapshot off \
  --agents "$RUN/agenci.json" --append-subagent-system-prompt-file "$RUN/podagenci.txt" \
  --max-turns 200 \
  (--session-id <uuid> | --resume <uuid>)
# środowisko: CLAUDE_CONFIG_DIR=<dzierżawca>, CLAUDE_CODE_PROJECT_DIR_NAME=<dzierżawca>,
# CLAUDE_CODE_DISABLE_AUTO_MEMORY=1, DISABLE_AUTOUPDATER=1, przypięta binarka
```

Gotowy komplet (ustawienia + flagi + zmienne) generuje
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generuj_ustawienia.py" --profil czat|kod|ci|tylko-odczyt …`.

## Decyzje

| Pytanie | Rozstrzygnięcie |
|---|---|
| izolacja od konfiguracji maszyny | `--setting-sources ""` (+ jawne wyłączenia: pamięć, konektory, CLAUDE.md) albo `--bare` (bez OAuth — wymaga `ANTHROPIC_API_KEY`/`apiKeyHelper`; „stanie się domyślny dla `-p`”) |
| kto odpowiada na zgody | nikt: `dontAsk` + `--permission-prompts none`; produkt: `--permission-prompt-tool` (`uprawnienia-i-tryby`) |
| polecenia `/…` od klienta | `--disable-slash-commands` — inaczej klient wpisze `/effort max`, `/config model=…`, `/mcp disable …`, skille Anthropic (próba macierzy) |
| tryb startowy | **zawsze jawny** `--permission-mode` (bez flag funkcji `-p` startuje w `auto` od 2.1.285) |
| wynik maszynowy | `--json-schema` (+ `--output-format json` lub `stream-json`): CLI dodaje narzędzie `StructuredOutput`, waliduje i każe poprawić; sprawdzaj `structured_output != null` |
| przerwanie | `control_request` `interrupt` na stdin (albo SIGINT), dopiero potem SIGTERM — SIGTERM (kod 143) zostawia turę bez wyniku |
| sesje | `--session-id <uuid>` nowa, `--resume <uuid>` kontynuacja, `--fork-session` rozgałęzienie, `--no-session-persistence` bez zapisu (bez wznawiania) |
| dzierżawcy | osobny `CLAUDE_CONFIG_DIR` + `CLAUDE_CODE_PROJECT_DIR_NAME` + `cwd`; reguły sieci per dzierżawca |
| limity | `--max-turns`, `--max-budget-usd` (wg cen API, liczony po stronie klienta), limity podagentów, `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` |

## Zdarzenia strumienia, które host musi obsłużyć

| Zdarzenie | Co zrobić |
|---|---|
| `system/init` | bramka: `mcp_servers[].status == connected` dla serwerów kluczowych, brak `plugin_errors`, `mcp_server_errors`; zapisz `model`, `permissionMode`, `capabilities` (wykrywanie funkcji zamiast wersji) |
| `system/api_retry` | stan „ponawiam” (`attempt`, `retry_delay_ms`, `error`) |
| `hook_started`/`hook_response` | dziennik (`--include-hook-events`) |
| `system/permission_denied` | dziennik odmów |
| `assistant`/`user` (+ `parent_tool_use_id` z `--forward-subagent-text`) | interfejs, transkrypt |
| `stream_event` (`--include-partial-messages`) | tekst na żywo |
| `control_response` | potwierdzenie `interrupt` (`still_queued`) |
| `result` | `subtype` (`success`, `error_max_turns`, `error_during_execution`…), `is_error`, `usage` (w tym `cache_read_input_tokens`, `cache_creation_input_tokens`), `total_cost_usd`, `permission_denials`, `structured_output` |

`CLAUDE_CODE_STARTUP_FAILURE_RESULTS=1` (≥2.1.274) — błąd startu jako zdarzenie `result`.

## Procedura

1. Wygeneruj profil (`generuj_ustawienia.py`) i zwaliduj (`--cli` = `claude doctor`).
2. Złóż instrukcję (`instrukcja-systemowa-i-pamiec/scripts/buduj_instrukcje.py`).
3. Uruchom próbę bez modelu: `proba_cli.py -- <flagi produktu>` — `init`: narzędzia, tryb,
   polecenia (`0`), skille (`0`), agenci, MCP; żądanie: instrukcja, narzędzia, `effort`.
4. Host: wzorzec `scripts/host_stream_json.py` (stream-json, bramka `init`, `interrupt`,
   `--resume`, katalogi dzierżawcy). Próba z atrapą: `--przerwij-po 2` → `control_response`
   `success`, wynik `error_during_execution`, sesja wznawialna.
5. Monitoruj koszty i cache (`model-cache-i-koszty`), bezpieczeństwo (`bezpieczenstwo-wdrozenia`).

## Pułapki

- `Glob`/`Grep` na Linuksie są poza domyślnym zestawem — przywraca je wymienienie w `--tools`
  lub `--allowed-tools` (reguła allow w pliku ustawień nie wystarcza) albo brak Bash w sesji.
- `-p` w niezaufanym folderze **wykonuje** hooki projektu i łączy `.mcp.json`, ale pomija allow
  z projektu — odetnij źródła (`--setting-sources ""`, `--strict-mcp-config`, `--bare`).
- Flagi `--mcp-config`, `--settings`, `--plugin-dir`, `--fallback-model`, `--add-dir` nie są
  zapisywane w sesji — podawaj je przy każdym `--resume`; tryb uprawnień przy `-p --resume`
  jak dla nowego `-p` (jawny `--permission-mode`).
- Wznowienie z innym tekstem instrukcji bez `--system-prompt-snapshot off` = stara instrukcja.
- Prompt w argumencie, a stdin otwarte (potok, usługa) → CLI czeka 3 s na dane
  („no stdin data received in 3s”); zamykaj stdin (`< /dev/null`) albo podawaj treść stdin.
- Flagi wieloargumentowe (`--allowed-tools`, `--disallowed-tools`, `--mcp-config`, `--add-dir`)
  połykają następny argument — prompt przed nimi lub przez stdin.
- `--json-schema`: gdy model nie wywoła `StructuredOutput`, wynik bywa `success` z
  `structured_output: null` (próba 2.1.286); po `MAX_STRUCTURED_OUTPUT_RETRIES` nieudanych
  walidacjach przebieg kończy się błędem. `format` w schemacie nie jest egzekwowany.
- `CLAUDE_CODE_PROJECT_DIR_NAME` tylko w środowisku procesu (z `env` ustawień ignorowany)
  i tylko razem z `CLAUDE_CONFIG_DIR`; 1–64 znaki `[A-Za-z0-9_-]` (próba: `projects/k123/`).
- Zadania Bash w tle są zabijane ok. 5 s po wyniku; podagenci/workflow w tle — `-p` czeka
  (do 10 min bezczynności, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`); hooki `async` — zabijane.
- Wiadomość w kolejce przy `--max-turns` w stream-json zaczyna nową turę z własnym limitem.
- `--output-format json` zwraca jeden obiekt na końcu — dla interfejsów na żywo `stream-json`.
- Rotacja kont: cache nie jest dzielony między organizacjami — przyklejaj rozmowę do konta
  (`model-cache-i-koszty`).
- Usunięty katalog roboczy w trakcie `-p` — patrz `cc:headless` („If the working directory is deleted”).

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `capabilities` w `init`, błąd na złym `--json-schema` | 2.1.205 |
| `--forward-subagent-text` (zagnieżdżone 2.1.219) | 2.1.211 |
| `--max-budget-usd` egzekwowany | 2.1.217 |
| `interrupt` z `cancel_queued` | 2.1.219 |
| czekanie na serwery MCP przed 1. turą | 2.1.221 |
| `CLAUDE_CODE_PROJECT_DIR_NAME` | 2.1.234 |
| `--system-prompt-snapshot` | 2.1.257 |
| `--permission-prompts` | 2.1.259 |
| `CLAUDE_CODE_STARTUP_FAILURE_RESULTS` | 2.1.274 |
| `--agents` z pliku | 2.1.281 |
| `plugin_errors[].path` | 2.1.283 |
| `-p` bez flag funkcji startuje w `auto` | 2.1.285 |

## Szablony

- `examples/produkt-czat.flaga.settings.json`, `examples/produkt-czat.flagi.txt`, `examples/produkt-czat.zmienne.txt` — profil z generatora (doctor + próba).
- `examples/uruchom_przebieg.sh` — skrypt przebiegu z izolacją dzierżawcy i bramką wyniku.
- `examples/klasyfikacja.schema.json` — schemat dla `--json-schema` (próba: walidacja i poprawka).
- `scripts/host_stream_json.py` — host stream-json z `interrupt` (próba).

## Referencje

- `references/strumien-i-sesje.md` — formaty, zdarzenia, żądania sterujące, sesje, transkrypty, retencja.
- `references/osadzanie-w-produkcie.md` — wzorzec usługi wielodzierżawnej, lista kontrolna, Danaco Nexus.
- `references/sdk-i-managed-agents.md` — opcje Agent SDK ↔ CLI, pojęcia Managed Agents ↔ CLI.
