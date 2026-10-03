# Dziennik debug — włączanie i czytanie

Źródła: `cc:debug-your-config`, `cc:cli-reference` (`--debug`, `--debug-file`), `cc:env-vars`
(`DEBUG`, `CLAUDE_CODE_DEBUG_LOGS_DIR`, `CLAUDE_CODE_DEBUG_LOG_LEVEL`, `CLAUDE_CODE_OTEL_DIAG_STDERR`),
`cc:hooks` (Debug hooks), `cc:monitoring-usage`, próba 2.1.286 (`--debug-file` na atrapie, 388 wierszy).

## Włączanie

| Sposób | Zakres |
|---|---|
| `claude --debug` | cały dziennik do `<konfiguracja>/debug/<sesja>.txt` |
| `claude --debug=mcp,hooks` / `--debug='!1p'` | filtr kategorii (tylko forma z `=`) |
| `claude --debug-file /ścieżka` | dziennik do pliku (włącza debug; wygrywa z `CLAUDE_CODE_DEBUG_LOGS_DIR`) |
| `DEBUG=1` | jak `--debug` |
| `CLAUDE_CODE_DEBUG_LOGS_DIR=/plik` | ścieżka **pliku** (mimo nazwy); wymaga włączenia debug |
| `CLAUDE_CODE_DEBUG_LOG_LEVEL` | `verbose`, `debug` (domyślnie), `info`, `warn`, `error` |
| `/debug [opis]` | w trwającej sesji: włącza log i prosi Claude o diagnozę |
| `CLAUDE_CODE_OTEL_DIAG_STDERR=1` | błędy eksportera OTel na stderr |

## Wzorce wierszy (2.1.286)

| Szukasz | Wzorzec | Przykład z próby |
|---|---|---|
| które pliki ustawień czytano | `Broken symlink or missing file encountered for settings.json`, `Watching for changes in setting files` | brak pliku użytkownika/projektu; obserwowane `…/settings.json, /etc/claude-code/managed-settings.json` |
| polityka zarządzana | `this machine has managed settings`, `MDM settings load`, `Remote settings` | „cc-plugin-sec-default@builtin seated outermost: this machine has managed settings” |
| reguły z flag | `Applying permission update` | „Adding 1 allow rule(s) to destination 'flagSettings': ["Bash(echo *)"]” |
| tool search | `[ToolSearch` | „disabled: ANTHROPIC_BASE_URL=… is not a first-party Anthropic host” |
| MCP | `[MCP]`, `MCP configs resolved`, `mcp` | „--mcp-config servers running fully async (nonblocking)” |
| skille | `getSkills returning` | „0 skill dir commands, 0 plugin skills, 39 bundled skills, 1 builtin plugin skills” |
| wtyczki wbudowane | `hooks module`, `plugin.register` | `cc-plugin-sec-default`, `cc-plugin-agents-md` |
| hook użytkownika | `Hook <Zdarzenie>:<matcher>` | „Hook PreToolUse:Bash (PreToolUse) success: stderr: hak-ok” |
| wyjście hooka nie-JSON | `Hook output does not start with {` | decyzje JSON nie zostaną odczytane |
| wywołanie narzędzia | `[Stall] tool_dispatch_start/end` | `tool=Bash … outcome=ok durationMs=70` |
| powłoka Bash | `Creating shell snapshot`, `Shell config file not found` | snapshot `~/.bashrc` w `<konfiguracja>/shell-snapshots/` |
| żądanie do API | `[API:timing]`, `[API REQUEST]`, `first byte after` | „dispatching to firstParty model=claude-sonnet-5-5” |
| ruch nieistotny | `Nonessential traffic disabled`, `[Bootstrap] Skipped` | przy `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` |
| telemetria | `[3P telemetry]` | „isTelemetryEnabled=false (CLAUDE_CODE_ENABLE_TELEMETRY=undefined)” |
| tryb auto | `[auto-mode] verifyAutoModeGateAccess` | stan bramki klasyfikatora |
| fast mode | `Fast mode unavailable` | „not available in the Agent SDK” (w `-p`) |
| zapis konfiguracji | `Failed to save config with lock` | pierwszy start w pustym katalogu — niegroźne |

Filtrowanie bez szumu zapisu plików:
`grep -vE "temp file|Temp file|Renaming|written atomically|Preserving|Applied original" log.txt`.

## Bezpieczeństwo logu

Dziennik zawiera ścieżki, nazwy serwerów, polecenia Bash i nagłówek rozliczeniowy
(`x-anthropic-billing-header` z wersją i punktem wejścia). Nie publikuj go bez przeglądu;
nie zawiera tokenów uwierzytelnienia w próbie, ale polecenia Bash mogą zawierać sekrety
wpisane przez użytkownika.
