# Koszty i OpenTelemetry

Źródła: `cc:costs`, `cc:monitoring-usage`, `cc:settings-reference` (modelPricing,
otelHeadersHelper), `cc:env-vars` (kategoria OTel w `wspolne/indeksy/zmienne.tsv`),
`cc:agent-teams` (koszty zespołów).

## 1. Koszty — narzędzia

| Narzędzie | Uwagi |
|---|---|
| `/usage` | blok Session: koszt wg cennika (lub `modelPricing`), czasy, zmiany kodu, użycie per model; dla planów — paski limitów i podział (≥10% zachowania z poradą) |
| `result.total_cost_usd`, `modelUsage` (`-p`) | liczone po stronie klienta |
| `--max-budget-usd` (`-p`) | limit wg tych samych stawek (≥2.1.217 egzekwowany) |
| `modelPricing` (zarządzane, ≥2.1.242) | `multiplier` (0–10; >1 ≥2.1.271) i/lub `overrides` `{model: {input, output, cacheRead, cacheWrite}}` USD/1M; dotyczy `/usage`, linii statusu, SDK, budżetu, OTel |
| konsola / admin claude.ai | limity wydatków i analityka organizacji |

Tło (`<$0,04`/sesję): streszczenia do `--resume`, polecenia stanu; sugestie promptów używają
cache rozmowy.

## 2. Dlaczego zużycie rośnie

Długi kontekst (każde wywołanie narzędzia to kolejne żądanie z całą historią), chybienia po
przerwie > TTL, zadania cykliczne i wiadomości między sesjami w bezczynności, sprawdzanie `/goal`,
podagenci/workflowy/członkowie zespołu (każdy własne żądania), kompakcja dużego kontekstu.

Redukcja: `/clear` między zadaniami, `/compact` w naturalnych przerwach (z instrukcją, co
zachować), tańszy model dla podagentów (`model` we frontmatterze, `CLAUDE_CODE_SUBAGENT_MODEL`),
mniej serwerów MCP (tool search, `alwaysLoad` tylko dla rdzenia), wtyczki inteligencji kodu,
przeniesienie instrukcji z CLAUDE.md do skilli, hooki przetwarzające wyniki (filtrowanie
logów), niższy effort dla prostych zadań, precyzyjne prompty.

## 3. OpenTelemetry — konfiguracja

| Zmienna | Rola |
|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY=1` | włącza (wymagana) |
| `OTEL_METRICS_EXPORTER` | `otlp`, `prometheus`, `console`, `none` (lista) |
| `OTEL_LOGS_EXPORTER` | `otlp`, `console`, `none` (zdarzenia) |
| `OTEL_TRACES_EXPORTER` | ślady (beta) |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc`, `http/json`, `http/protobuf` — **brak domyślnego** |
| `OTEL_EXPORTER_OTLP_ENDPOINT` (+ `_METRICS_`/`_LOGS_`) | kolektor |
| `OTEL_EXPORTER_OTLP_HEADERS` | uwierzytelnienie (sekret — tylko w zarządzanych/środowisku, nie w repozytorium) |
| `otelHeadersHelper` (ustawienie) + `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` | nagłówki z polecenia, odświeżane (domyślnie 29 min) |
| `OTEL_METRIC_EXPORT_INTERVAL` / `OTEL_LOGS_EXPORT_INTERVAL` | 60000 / 5000 ms |
| `OTEL_METRICS_INCLUDE_*` | kardynalność: `SESSION_ID` (tak), `VERSION` (nie), `ACCOUNT_UUID` (tak), `ENTRYPOINT` (nie), `RESOURCE_ATTRIBUTES` (tak), `REPOSITORY` (nie, ≥2.1.269) |
| `OTEL_RESOURCE_ATTRIBUTES` | atrybuty zespołu/działu (`department=…,team.id=…`) |
| mTLS | `OTEL_EXPORTER_OTLP_CLIENT_KEY`, `…_CLIENT_CERTIFICATE` |

**Prywatność** — domyślnie wyłączone, włączaj świadomie:
`OTEL_LOG_USER_PROMPTS` (treść promptów), `OTEL_LOG_ASSISTANT_RESPONSES` (≥2.1.193; domyślnie
jak prompty), `OTEL_LOG_TOOL_DETAILS` (polecenia Bash, nazwy narzędzi/MCP/skilli, wejścia),
`OTEL_LOG_TOOL_CONTENT` (treść wyników w śladach), `OTEL_LOG_RAW_API_BODIES` (całe żądania
i odpowiedzi), `OTEL_LOG_MANAGED_SETTINGS`; limit długości `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH`.

**Zarządzanie**: `env` w ustawieniach zarządzanych. Ustawiony tam `OTEL_EXPORTER_OTLP_ENDPOINT`
usuwa endpointy per sygnał ustawione przez użytkownika, `…_PROTOCOL` — protokoły, nagłówki/
certyfikaty — poświadczenia i endpointy (≥2.1.217). Selektory eksporterów podlegają zwykłej
kolejności — ustaw je też w zarządzanych. `OTEL_*` w ustawieniach projektu są ignorowane;
nie trafiają do podprocesów.

Weryfikacja: metryka `claude_code.session.count` (start sesji) lub zdarzenie
`claude_code.user_prompt`; błędy eksportu w `claude --debug-file <plik>` jako `[3P telemetry]`.

## 4. Metryki

| Metryka | Jednostka |
|---|---|
| `claude_code.session.count` | — |
| `claude_code.lines_of_code.count` | — |
| `claude_code.pull_request.count`, `claude_code.commit.count` | — |
| `claude_code.cost.usage` | USD (atrybuty `model`, `query_source` main/subagent/auxiliary, `speed`, `effort`, `agent.name`, `skill.name`, `plugin.name`, `mcp_server.name`, `mcp_tool.name` — nazwy własne zastępowane `custom`/`third-party`, chyba że `OTEL_LOG_TOOL_DETAILS`) |
| `claude_code.token.usage` | tokeny, `type` = `input`/`output`/`cacheRead`/`cacheCreation` |
| `claude_code.code_edit_tool.decision` | decyzje zgód edycji |
| `claude_code.active_time.total` | s |

## 5. Zdarzenia (logi)

Nazwy z przedrostkiem `claude_code.`: `user_prompt`, `assistant_response`, `tool_result`, `api_request`, `api_error`, `api_refusal`,
`api_request_body`/`api_response_body` (tylko z `OTEL_LOG_RAW_API_BODIES`), `tool_decision`,
`permission_mode_changed`, `auth`, `mcp_server_connection`, `internal_error`, `plugin_installed`,
`plugin_loaded`, `skill_activated`, `at_mention`, `api_retries_exhausted`, `hook_registered`,
`hook_execution_start`/`hook_execution_complete`, `hook_plugin_metrics`, `compaction`,
`subagent_completed`, `feedback_survey`, `retention_sweep`, `managed_settings_resolved`.
Korelacja: `session.id`, `prompt.id`, identyfikatory żądań. Audyt bezpieczeństwa: decyzje
narzędzi, aktywność MCP, zmiany trybu, rozstrzygnięte ustawienia zarządzane.

## 6. Usługa osadzająca CLI

Koszt per dzierżawca: zapisuj `result.usage` i `modelUsage` po każdej turze (z polami cache),
`OTEL_RESOURCE_ATTRIBUTES=tenant.id=…` na proces, bez treści (`OTEL_LOG_*` wyłączone).
Alarmy: spadek udziału cache, wzrost `api_retries_exhausted`, `api_refusal` (przełączenia
modelu), koszt per sesja powyżej progu.
