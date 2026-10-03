# Zdarzenia hooków i ich decyzje

Źródło: `cc:hooks` (stan 01.10.2026; lista zdarzeń potwierdzona komunikatem `claude doctor` 2.1.286: 33 zdarzenia). Indeks maszynowy: `${CLAUDE_PLUGIN_ROOT}/wspolne/indeksy/hooki-zdarzenia.tsv`.

## 1. Tabela zdarzeń

| Zdarzenie | Kiedy | Matcher filtruje | Blokuje (exit 2) | Wzorzec decyzji | Uwagi |
|---|---|---|---|---|---|
| `SessionStart` | start lub wznowienie sesji | źródło: startup, resume, clear, compact, fork | nie | additionalContext, initialUserMessage, sessionTitle, watchPaths, reloadSkills; zwykły stdout trafia do kontekstu | CLAUDE_ENV_FILE dla trwałych zmiennych Bash; hooki mcp_tool pomijane przy starcie i wznowieniu |
| `Setup` | --init-only, albo --init/--maintenance w -p | init, maintenance | nie | brak | jednorazowe przygotowanie w CI; hooki mcp_tool pomijane |
| `InstructionsLoaded` | wczytanie CLAUDE.md lub .claude/rules/*.md | powód: session_start, nested_traversal, path_glob_match, include, compact | nie | brak | diagnostyka pamięci |
| `UserPromptSubmit` | wysłanie promptu, przed modelem | brak | tak (odrzuca prompt) | decision: block, reason; additionalContext; zwykły stdout trafia do kontekstu | domyślny timeout 30 s; nie podmienia treści promptu |
| `UserPromptExpansion` | rozwinięcie polecenia /skill w prompt | nazwa polecenia | tak (blokuje rozwinięcie) | decision: block; additionalContext | wpisanie /skill omija PreToolUse — tu jest kontrola |
| `MessageDisplay` | wyświetlanie tekstu odpowiedzi | brak | nie | hookSpecificOutput.displayContent (tylko ekran) | domyślny timeout 10 s; nie zmienia transkryptu |
| `PreToolUse` | przed wywołaniem narzędzia | nazwa narzędzia | tak (blokuje wywołanie) | hookSpecificOutput.permissionDecision allow/deny/ask/defer, permissionDecisionReason, updatedInput, additionalContext | precedencja deny > defer > ask > allow; timeout command/http/mcp_tool NIE blokuje |
| `PermissionRequest` | potrzebna decyzja uprawnień | nazwa narzędzia | nie (exit 2 ignorowany) | hookSpecificOutput.decision.behavior allow/deny, updatedInput, updatedPermissions | odmowa tylko przez obiekt decision |
| `PermissionDenied` | odmowa w trybie auto | nazwa narzędzia | nie | hookSpecificOutput.retry: true | dziennik odmów |
| `PostToolUse` | po udanym narzędziu | nazwa narzędzia | nie (stderr do modelu) | decision: block, reason; additionalContext; updatedToolOutput | narzędzie już się wykonało |
| `PostToolUseFailure` | po nieudanym narzędziu | nazwa narzędzia | nie (stderr do modelu) | decision: block; additionalContext | — |
| `PostToolBatch` | po partii równoległych wywołań | brak | tak (zatrzymuje pętlę) | decision: block; additionalContext | przed kolejnym żądaniem do modelu |
| `Notification` | powiadomienie Claude Code | typ: permission_prompt, idle_prompt, auth_success, elicitation_*, agent_needs_input, agent_completed, quota_auto_resume_* | nie | brak (terminalSequence działa) | efekty uboczne |
| `SubagentStart` | start podagenta | typ agenta | nie | additionalContext | podagenci nie dziedziczą SessionStart |
| `SubagentStop` | koniec podagenta | typ agenta | tak (podagent pracuje dalej) | decision: block, reason; additionalContext; last_assistant_message na wejściu | Stop w frontmatterze agenta zamienia się na SubagentStop |
| `TaskCreated` | tworzenie zadania TaskCreate | brak | tak (cofa utworzenie) | decision: block | — |
| `TaskCompleted` | oznaczenie zadania jako ukończone | brak | tak (nie ukończy) | exit 2 albo continue: false | — |
| `Stop` | koniec odpowiedzi modelu | brak | tak (model pracuje dalej) | decision: block, reason; hookSpecificOutput.additionalContext; stop_hook_active na wejściu | limit 8 kolejnych kontynuacji (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP); nie odpala przy przerwaniu przez użytkownika |
| `StopFailure` | tura zakończona błędem API | typ błędu: rate_limit, overloaded, authentication_failed, billing_error, server_error, max_output_tokens… | nie | brak (wyjście ignorowane) | tylko dziennik |
| `TeammateIdle` | członek zespołu agentów kończy pracę | brak | tak | exit 2 albo continue: false | agent teams |
| `ConfigChange` | zmiana pliku konfiguracji w trakcie sesji | źródło: user_settings, project_settings, local_settings, policy_settings, skills | tak (poza policy_settings) | decision: block | audyt zmian ustawień |
| `CwdChanged` | zmiana katalogu roboczego | brak | nie | watchPaths | np. direnv |
| `DirectoryAdded` | dodanie katalogu /add-dir lub register_repo_root | slash_command, register_repo_root | nie | brak | — |
| `FileChanged` | zmiana obserwowanego pliku | dosłowne nazwy plików (np. .envrc|.env) | nie | watchPaths | matcher buduje listę obserwowanych plików |
| `WorktreeCreate` | tworzenie worktree | brak | tak (każdy kod ≠ 0) | ścieżka na stdout (command) lub hookSpecificOutput.worktreePath (http) | zastępuje domyślne git worktree |
| `WorktreeRemove` | usuwanie worktree | brak | tak (każdy kod ≠ 0) | tylko kod wyjścia | — |
| `PreCompact` | przed kompakcją | manual, auto | tak (blokuje kompakcję) | decision: block | — |
| `PostCompact` | po kompakcji | manual, auto | nie | brak | diagnostyka cache |
| `PreModelSwitch` | przed zmianą modelu zleconą przez użytkownika lub klienta | kanoniczna nazwa modelu docelowego | tak (blokuje zmianę) | permissionDecision allow/deny/ask lub decision: block | timeout BLOKUJE zmianę; ask poza /model = odmowa; tylko command/http/mcp_tool |
| `PostModelSwitch` | po zmianie modelu (także automatycznej) | kanoniczna nazwa modelu docelowego | nie | additionalContext; zwykły stdout trafia do kontekstu | rejestr fallbacku modelu |
| `SessionEnd` | koniec sesji | powód: clear, resume, logout, prompt_input_exit, other | nie | brak | timeout CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS |
| `Elicitation` | serwer MCP prosi o dane | nazwa serwera MCP | tak (odrzuca) | hookSpecificOutput.action accept/decline/cancel, content | przy --permission-prompts none elicitation jest anulowana |
| `ElicitationResult` | po odpowiedzi na elicitation | nazwa serwera MCP | tak (decline) | hookSpecificOutput.action, content | — |

Kadencje: na sesję `SessionStart`, `SessionEnd`; na turę `UserPromptSubmit`, `Stop`, `StopFailure`; na każde wywołanie narzędzia `PreToolUse`, `PostToolUse` (poza `EndConversation`).
## 2. Wejście wspólne (stdin `command`, ciało POST `http`)

| Pole | Znaczenie |
|---|---|
| `session_id` | identyfikator sesji |
| `prompt_id` | UUID bieżącego promptu, zgodny z atrybutem `prompt.id` OTel (≥2.1.196) |
| `transcript_path` | transkrypt (zapis asynchroniczny — może nie mieć bieżącej tury; na `Stop` używaj `last_assistant_message`) |
| `cwd` | katalog bieżący (po `cd` lub wejściu do worktree — nowy) |
| `scratchpad_dir` | katalog roboczy sesji (≥2.1.257) |
| `permission_mode` | `default`, `plan`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions` (Manual = `default`) |
| `effort.level` | effort w chwili hooka |
| `hook_event_name` | nazwa zdarzenia |
| `agent_id`, `agent_type` | w podagencie lub sesji `--agent` |

Pola zdarzeń: narzędziowe — `tool_name`, `tool_input`, `tool_use_id` (i wynik w `Post*`);
`SessionStart` — `source`, `model` (nie zawsze), `agent_type`, `session_title`, przy
wznowieniu `seconds_since_last_response`, `context_tokens`, `prompt_cache_likely_expired`,
`estimated_cache_write_usd` (≥2.1.251); `Stop`/`SubagentStop` — `stop_hook_active`,
`last_assistant_message`, `background_tasks`, `session_crons`; `*ModelSwitch` — `from_model`,
`to_model`; `PermissionRequest` — `permission_suggestions`. Zmiennej `$CLAUDE_MODEL` nie ma.

Proces hooka dziedziczy środowisko CLI bez zmiennych eksporterów `OTEL_*` i — przy
`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` — bez poświadczeń. Hooki działają bez terminala
(nie ma `/dev/tty`); powiadomienia przez pole `terminalSequence` (tylko interaktywnie).

## 3. Wyjście — pola uniwersalne

| Pole | Skutek |
|---|---|
| `continue: false` + `stopReason` | zatrzymuje pracę (pierwszeństwo nad decyzjami zdarzenia) |
| `systemMessage` | ostrzeżenie dla użytkownika (w stream-json jako komunikat informacyjny) |
| `suppressOutput` | bez skutku |
| `terminalSequence` | OSC 0/1/2/9/99/777 lub BEL (powiadomienie, tytuł okna); ignorowane w `-p` |
| `hookSpecificOutput.hookEventName` | wymagane w każdym `hookSpecificOutput` |

Limit 10 000 znaków na każde `additionalContext`, `systemMessage`, `initialUserMessage`
i na zwykły stdout — nadmiar do pliku z podglądem 2 000 znaków (limitu nie da się podnieść).

## 4. Decyzje według zdarzeń

| Zdarzenia | Pola |
|---|---|
| `UserPromptSubmit`, `UserPromptExpansion`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `SubagentStop`, `ConfigChange`, `PreCompact` | `decision: "block"`, `reason` (Stop/SubagentStop także `hookSpecificOutput.additionalContext` jako informacja zwrotna bez błędu) |
| `PreToolUse` | `hookSpecificOutput.permissionDecision` (`allow`/`deny`/`ask`/`defer`), `permissionDecisionReason` (dla `deny` do modelu, dla `ask` do użytkownika), `updatedInput` (całe wejście), `additionalContext` |
| `PermissionRequest` | `hookSpecificOutput.decision.behavior` (`allow`/`deny`), `updatedInput`, `updatedPermissions`, `message`, `interrupt` |
| `PermissionDenied` | `hookSpecificOutput.retry: true` |
| `PreModelSwitch` | `permissionDecision` `allow`/`deny`/`ask` albo `decision: "block"`; `ask` poza `/model` = odmowa |
| `TeammateIdle`, `TaskCompleted` | exit 2 albo `continue: false` |
| `TaskCreated` | exit 2 albo `decision: "block"` |
| `WorktreeCreate` | ścieżka na stdout (`command`) / `hookSpecificOutput.worktreePath` (`http`) |
| `WorktreeRemove` | kod wyjścia |
| `Elicitation`, `ElicitationResult` | `hookSpecificOutput.action` (`accept`/`decline`/`cancel`), `content` |
| `MessageDisplay` | `hookSpecificOutput.displayContent` (tylko ekran) |
| `SessionStart`, `SubagentStart`, `PostModelSwitch` | `additionalContext`; `SessionStart` także `initialUserMessage` (pierwsza tura w `-p`), `sessionTitle`, `watchPaths`, `reloadSkills` |
| `Setup`, `Notification`, `SessionEnd`, `PostCompact`, `InstructionsLoaded`, `StopFailure`, `CwdChanged`, `DirectoryAdded`, `FileChanged` | brak decyzji (efekty uboczne) |

Treść podmieniają: `PreToolUse.updatedInput` (wejście narzędzia), `PermissionRequest.decision.updatedInput`,
`PostToolUse.updatedToolOutput` (wynik; kształt wyniku narzędzia, np. Bash: `stdout`, `stderr`,
`interrupted`, `isImage`). `UserPromptSubmit` nie podmieni promptu.

## 5. Gdzie trafia `additionalContext`

`SessionStart`, `SubagentStart` — na początku rozmowy; `UserPromptSubmit`,
`UserPromptExpansion` — przy prompcie; `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
`PostToolBatch` — przy wyniku narzędzia; `Stop`, `SubagentStop` — na końcu tury (praca
trwa dalej); `PostModelSwitch` — przy następnym żądaniu. Przy `--resume` kontekst z hooków
w trakcie sesji jest odtwarzany z transkryptu (wartości mogą być nieaktualne), a
`SessionStart` uruchamia się ponownie ze `source: resume`/`fork`.

## 6. Hooki a strumień `-p`

`--include-hook-events` dodaje zdarzenia `hook_started`/`hook_response` do stream-json
(`SessionStart` i `Setup` zawsze). `Notification`, `SessionEnd`, `PreCompact`, `PostCompact`
nie dają `hook_started`. `systemMessage` hooka pojawia się jako komunikat informacyjny.
