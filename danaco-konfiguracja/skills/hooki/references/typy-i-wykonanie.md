# Typy obsługi hooków, wykonanie, miejsca definicji i polityki

Źródła: `cc:hooks` („Hook handler fields”, „Reference scripts by path”, „Hooks in skills
and agents”, „Run hooks in the background”, „Security considerations”), `cc:hooks-guide`,
`cc:settings-reference` (`hooks`, `disableAllHooks`, `allowManagedHooksOnly`,
`allowedHttpHookUrls`, `httpHookAllowedEnvVars`), `cc:plugins/components`.

## 1. Pola wspólne

| Pole | Opis |
|---|---|
| `type` | `command`, `http`, `mcp_tool`, `prompt`, `agent` |
| `if` | jedna reguła w składni uprawnień (`Bash(git *)`, `Edit(*.ts)`); tylko `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` — na innych zdarzeniach hook z `if` **nigdy** się nie uruchomi; dopasowanie „best effort” (przy nieparsowalnym poleceniu hook rusza zawsze) |
| `timeout` | sekundy; domyślnie 600 (`command`, `http`, `mcp_tool`), 30 (`prompt`), 60 (`agent`); 30 dla `UserPromptSubmit` i `*ModelSwitch`, 10 dla `MessageDisplay` |
| `statusMessage` | tekst wskaźnika postępu |
| `once` | tylko we frontmatterze skilla: usuń po pierwszym udanym uruchomieniu |

`if` dla `Bash`: przypisania zmiennych zdejmowane, każde podpolecenie sprawdzane, także
w `$(…)` i odwrotnych apostrofach; wzorce dłuższe niż nazwa programu uruchamiają hook przy
`$(…)`/`$VAR` zawsze. `Edit(src/**)` = tylko `src` w katalogu roboczym (od 2.1.214);
na każdej głębokości `Edit(**/src/**)`.

## 2. `command`

| Pole | Opis |
|---|---|
| `command` | polecenie powłoki; z `args` — plik wykonywalny |
| `args` | forma exec: bez powłoki, każdy element to jeden argument, placeholdery podstawiane dosłownie |
| `async` | w tle, bez blokowania; wynik (`additionalContext`, `systemMessage`) w następnej turze; w `-p` zabijany przy końcu |
| `asyncRewake` | w tle; exit 2 budzi model (stderr jako przypomnienie), także w bezczynności |
| `shell` | `bash` (domyślnie) albo `powershell` |

Placeholdery i zmienne procesu: `${CLAUDE_PROJECT_DIR}` (katalog startu — nie zmienia się
po wejściu do worktree), `${CLAUDE_PLUGIN_ROOT}` (katalog instalacji wtyczki),
`${CLAUDE_PLUGIN_DATA}` (trwałe dane wtyczki), `${user_config.*}` (tylko forma exec we
wtyczce; w formie powłoki `$CLAUDE_PLUGIN_OPTION_<KLUCZ>`). Forma powłoki: `sh -c` (Linux,
macOS), Git Bash lub PowerShell (Windows) — cytuj placeholdery `"${CLAUDE_PLUGIN_ROOT}"`.

`CLAUDE_ENV_FILE` (tylko `SessionStart`): plik, do którego dopisujesz `export ZMIENNA=…`
(`>>`, nie `>`), wczytywany przed każdym poleceniem Bash sesji.

## 3. `http`

| Pole | Opis |
|---|---|
| `url` | adres POST (ciało = wejście JSON) |
| `headers` | nagłówki; `$ZMIENNA`/`${ZMIENNA}` tylko dla nazw z `allowedEnvVars` (pozostałe → pusty tekst) |
| `allowedEnvVars` | lista zmiennych dozwolonych w nagłówkach |

Wynik: 2xx + pusty → jak exit 0; 2xx + JSON → decyzje; 2xx + tekst, nie-2xx, brak
połączenia → błąd nieblokujący. **Status HTTP nie blokuje** — blokada tylko przez 2xx
z JSON-em decyzji. Polityki: `allowedHttpHookUrls` (lista wzorców adresów, scalana
z wszystkich poziomów, obejmuje też hooki zarządzane), `httpHookAllowedEnvVars`.

## 4. `mcp_tool`

| Pole | Opis |
|---|---|
| `server` | nazwa serwera; dla serwera z wtyczki `plugin:<wtyczka>:<serwer>` |
| `tool` | nazwa narzędzia |
| `input` | argumenty; teksty z podstawieniem `${tool_input.file_path}`, `${session_id}` itd. |

Wynik narzędzia czytany jak stdout (`isError: true` → błąd nieblokujący). Na zdarzeniach,
które mogą blokować, CLI czeka na łączący się serwer (do `MCP_TIMEOUT` i `timeout`
hooka); na obserwacyjnych — nie. Hook nigdy nie uruchamia OAuth. **`SessionStart` przy
starcie/wznowieniu i `Setup` pomijają `mcp_tool`** („no MCP client context”) — kontekst
startowy dawaj hookiem `command` lub flagą `--append-system-prompt-file`.

## 5. `prompt` i `agent`

`prompt`: jedno wywołanie modelu (domyślnie model zadań pomocniczych), `$ARGUMENTS` =
wejście JSON (bez placeholdera wejście dopisywane na końcu; `\$` dla dosłownego `$`).
Odpowiedź: `{"ok": true}` albo `{"ok": false, "reason": "…", "impossible": true|false}`.
Skutek `ok: false`: `Stop`/`SubagentStop` — powód jako następne polecenie (z
`impossible: true` tura się kończy); `PreToolUse` — odmowa i koniec tury, z
`continueOnBlock: true` powód wraca do modelu jako błąd narzędzia; `PostToolUse` —
podobnie; `PermissionRequest` i `PermissionDenied` — bez skutku (użyj `command`).

`agent`: podagent z narzędziami (Read, Grep, Glob) weryfikujący warunek; 60 s; działa jak
`prompt` z `continueOnBlock: true`; bez `impossible`. Eksperymentalne.

## 6. Miejsca definicji

| Miejsce | Zasięg | Uwagi |
|---|---|---|
| `~/.claude/settings.json` | wszystkie projekty | — |
| `.claude/settings.json` | projekt (commit) | interaktywnie po zaufaniu; w `-p` zawsze |
| `.claude/settings.local.json` | projekt, osobiście | — |
| ustawienia zarządzane | organizacja | nie wyłączy ich `disableAllHooks` spoza managed |
| `--settings` | sesja | kanał produktów osadzających |
| wtyczka `hooks/hooks.json` | gdy wtyczka włączona | opcjonalne pole `description` |
| frontmatter skilla | od wywołania skilla do końca sesji | `once: true`; w projekcie podlega zaufaniu jak pliki ustawień |
| frontmatter podagenta | gdy podagent działa | `Stop` → `SubagentStop`; z projektu tylko po zaufaniu folderu (nie w `-p`) |

Wtyczka może wymagać zgody: hook z `"ask"` pokazuje źródło `[settings]`, `[plugin:<nazwa>]`
lub `[skill]`.

## 7. Polityki organizacji

- `allowManagedHooksOnly: true` (managed, ≥2.1.238): blokuje hooki użytkownika, projektu,
  local i wtyczek (poza wtyczkami wymuszonymi w managed `enabledPlugins`); zawęża też
  `statusLine`, `fileSuggestion`, `subagentStatusLine`; wyłącza wtyczki ze źródłem
  `command` i `headersHelper` marketplace (chyba że `disableCommandPluginSources: false`).
- `disableAllHooks: true` — wartość po scaleniu warstw (projekt `false` przebije Twój `true`);
  na jedną sesję: `--settings '{"disableAllHooks": true}'`.
- Hooki zmieniane w plikach są przeładowywane automatycznie; `/hooks` pokazuje stan i źródło
  każdego handlera (tylko do odczytu).

## 8. Bezpieczeństwo hooków

Hook `command` wykonuje się z uprawnieniami użytkownika, **poza piaskownicą Bash**.
Zasady: waliduj i cytuj wejście (`"$VAR"`), blokuj `..` w ścieżkach, używaj ścieżek
bezwzględnych lub placeholderów, nie dotykaj plików z sekretami, testuj na atrapie przed
wdrożeniem. Przed `claude -p` na cudzym repozytorium przejrzyj `.claude/` albo wyłącz hooki.

## 9. Diagnostyka

`claude --debug-file /ścieżka/log` (albo `--debug` → `~/.claude/debug/<sesja>.txt`);
`CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` pokazuje dopasowania matcherów. Ręczny test:
`echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./hook.sh; echo $?` albo
`scripts/test_hooka.py`. Typowe przyczyny: matcher wrażliwy na wielkość liter, zła
pozycja pola JSON (np. `permissionDecision` poza `hookSpecificOutput`), echo z profilu
powłoki przed JSON-em, brak `chmod +x`, `jq` niedostępny.
