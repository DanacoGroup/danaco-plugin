# Tryb `-p`: formaty, zdarzenia, żądania sterujące, sesje, transkrypty

Źródła: `cc:headless`, `cc:sessions`, `cc:cli-reference`, `cc:agent-sdk/streaming-output`,
`cc:agent-sdk/streaming-vs-single-mode`, `cc:agent-sdk/sessions`, `cc:agent-sdk/typescript`
(typy wiadomości), `cc:claude-directory`, próby 2.1.286 na atrapie.

## 1. Formaty

| Flaga | Wartości | Uwagi |
|---|---|---|
| `--output-format` | `text` (domyślnie), `json` (jeden obiekt na końcu), `stream-json` (JSON w wierszach) | `stream-json` wymaga `--verbose` |
| `--input-format` | `text`, `stream-json` | `stream-json`: wiadomości i żądania sterujące na stdin, sesja trwa do zamknięcia stdin |
| `--include-partial-messages` | — | zdarzenia `stream_event` (delty tekstu) |
| `--replay-user-messages` | — | echo wiadomości użytkownika (potwierdzenie przyjęcia) |
| `--include-hook-events` | — | `hook_started`/`hook_progress`/`hook_response` (SessionStart/Setup zawsze) |
| `--forward-subagent-text` | — | tekst i myślenie podagentów z `parent_tool_use_id` |
| `--prompt-suggestions` | — | `prompt_suggestion` po turze |
| `--json-schema` | schemat JSON | narzędzie `StructuredOutput`; wynik w `structured_output` |

Wiadomość wejściowa stream-json (próba):
`{"type":"user","message":{"role":"user","content":[{"type":"text","text":"…"}]}}`.

## 2. Zdarzenia wyjściowe

| `type`/`subtype` | Zawartość |
|---|---|
| `system/init` | `cwd`, `session_id`, `tools`, `mcp_servers[{name,status}]`, `model`, `permissionMode`, `slash_commands`, `apiKeySource`, `claude_code_version`, `output_style`, `agents`, `skills`, `plugins[{name,path,source}]`, `plugin_errors`, `mcp_server_errors`, `capabilities` (np. `interrupt_receipt_v1`, `interrupt_cancel_queued_v1`, `msg_lifecycle_v1`, `mcp_read_resource_v1`), `memory_paths`, `fast_mode_state` |
| `system/api_retry` | `attempt`, `max_retries`, `retry_delay_ms`, `error_status`, `error`, `no_response` |
| `system/hook_*` | zdarzenia hooków |
| `system/permission_denied` | odmowa (przy `--permission-prompts none`) |
| `system/compact_boundary` | kompakcja |
| `assistant`, `user` | treść i wyniki narzędzi |
| `stream_event` | delty (z `--include-partial-messages`) |
| `control_response` | odpowiedź na żądanie sterujące |
| `result` | `subtype` (`success`, `error_max_turns`, `error_during_execution`, `error_max_budget_usd`…), `is_error`, `num_turns`, `result`, `session_id`, `total_cost_usd`, `usage`, `modelUsage`, `permission_denials`, `structured_output`, `stop_reason` |

Próby: `interrupt` po 2 s wolnej odpowiedzi → `control_response` `{"subtype":"success",
"response":{"still_queued":[]}}`, wynik `error_during_execution`, `is_error: true`, sesja
wznawialna `--resume`. `--json-schema` bez wywołania `StructuredOutput` → `success`
z `structured_output: null`; błędne dane → wynik narzędzia z listą błędów walidacji
i poprawka w kolejnej turze.

## 3. Żądania sterujące (stdin, `--input-format stream-json`)

`{"type":"control_request","request_id":"<id>","request":{"subtype":"interrupt"}}` — kończy
turę (zapisana w sesji; z `cancel_queued` usuwa kolejkę). Inne podtypy używane przez SDK:
`initialize`, `set_model`, `set_permission_mode`, `can_use_tool` (odpowiedź hosta),
`mcp_*`, `stop_task`, `apply_flag_settings` — opis w `cc:agent-sdk/typescript`.
Sygnały: SIGINT kończy turę jak `interrupt`; SIGTERM → kod 143, tura bez wyniku, polecenia
Bash zabite, wykonane hooki `SessionEnd`; `CLAUDE_CODE_RESUME_INTERRUPTED_TURN=1` każe
przy wznowieniu dokończyć przerwaną turę.

## 4. Sesje

| Operacja | Flaga |
|---|---|
| nowa z ustalonym ID | `--session-id <uuid>` |
| wznowienie | `--resume <uuid|nazwa|ścieżka .jsonl>`, `--continue` (ostatnia w katalogu; w `-p` obejmuje sesje `-p`/SDK) |
| rozgałęzienie | `--resume <id> --fork-session` |
| nazwa | `--name`/`-n` |
| bez zapisu | `--no-session-persistence` (`-p`), `CLAUDE_CODE_SKIP_PROMPT_HISTORY` (każdy tryb) |

Wznowienie przywraca: historię (przerwane wywołanie narzędzia oznaczone jako ucięte,
≥2.1.281), model (chyba że flaga/zmienna wybiera inny lub model wycofany/niedozwolony),
agenta (`--agent`), aktywny `/goal`, zadania cykliczne. **Nie przywraca**: `--mcp-config`,
`--settings`, `--plugin-dir`, `--fallback-model`, `--add-dir`. Tryb uprawnień w `-p --resume`
— jak dla nowego `-p` (plan tylko z hostem). Instrukcja — utrwalona (snapshot `on`).

## 5. Transkrypty i retencja

`<CLAUDE_CONFIG_DIR>/projects/<projekt>/<sesja>.jsonl` (`<projekt>` = ścieżka katalogu
roboczego z zamienionymi znakami, >200 znaków — skrót) albo `projects/<CLAUDE_CODE_PROJECT_DIR_NAME>/`
(próba: `projects/k123/`). Format wewnętrzny, zmienny między wersjami — do integracji
`/export`, SDK (`listSessions`, `getSessionMessages`) albo `SessionStore` (tylko SDK).
Retencja: `cleanupPeriodDays` (domyślnie 30; `0` niedozwolone), `claude project purge
[ścieżka] [--dry-run] [--all]`. Wyniki narzędzi ponad limity: `tool-results/` w katalogu sesji.

## 6. `--bare`

Pomija automatyczne wykrywanie: hooki, skille, polecenia, podagentów, wtyczki, serwery MCP,
pamięć, CLAUDE.md; nie czyta OAuth ani pęku kluczy (wymaga `ANTHROPIC_API_KEY` lub
`apiKeyHelper` w `--settings`); narzędzia Bash, odczyt, edycja. Kontekst podajesz flagami
(`--append-system-prompt`, `--settings`, `--mcp-config`, `--agents`, `--plugin-dir`).
Zapis instrukcji (snapshot) w `--bare` wyłączony, chyba że `on`. Zapowiedziany jako
przyszły domyślny tryb `-p` — usługi na OAuth muszą to śledzić w notach wydań.
