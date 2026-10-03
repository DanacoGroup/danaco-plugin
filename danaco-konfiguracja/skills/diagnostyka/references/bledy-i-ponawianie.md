# Komunikaty błędów i ponawianie

Źródło: `cc:errors` (indeks „Find your error”, ok. 200 komunikatów), `cc:troubleshoot-install`,
`cc:network-config`. Poniżej mapa kategorii z komunikatami, które najczęściej wynikają
z konfiguracji. Dokładny opis: sekcja o tej samej nazwie w `cc:errors`.

## Ponawianie automatyczne

Do 10 prób z wykładniczym odstępem dla: błędów serwera/przeciążenia/limitu czasu przed
strumieniem, zerwanych połączeń (przed ukończonym blokiem), zawieszonych strumieni (raz),
tymczasowych 429, przekroczenia kontekstu przez `max_tokens` (z mniejszym `max_tokens`),
wygasłych poświadczeń chmury (2 razy), 401/403 przy `apiKeyHelper` (ponowne uruchomienie skryptu).
Bez ponawiania: błąd certyfikatu TLS, błąd po ukończonym bloku/narzędziu (tura kontynuowana od
wyników — „The response above may be incomplete”), odmowa polityki organizacji (Inference hooks).

| Zmienna | Domyślnie | Kiedy zmieniać |
|---|---|---|
| `CLAUDE_CODE_MAX_RETRIES` | 10 (maks. 15) | skrypty: mniej, by szybciej zobaczyć błąd |
| `CLAUDE_CODE_RETRY_WATCHDOG=1` | — | CI/usługi: 429/529 ponawiane bez końca (poza limitem wydatków), inne błędy do 300 prób |
| `API_TIMEOUT_MS` | 600000 | wolna sieć/proxy |
| `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS` | — (≥2.1.242) | brama z długim czasem do pierwszego bajtu |

W `-p`: zdarzenie `system/api_retry` (`attempt`, `retry_delay_ms`, `error`) — host pokazuje „ponawiam”.

## Kategorie

| Kategoria | Komunikaty (wybór) | Typowa przyczyna konfiguracyjna |
|---|---|---|
| serwer | `API Error: 500`, `Repeated 529 Overloaded`, `Request timed out`, `No response from API`, `The response above may be incomplete` | brama/proxy ucina strumień; `API_TIMEOUT_MS`; łańcuch `fallbackModel` |
| tryb auto | `Auto mode cannot determine the safety…`, `server returned no safety verdict` | model klasyfikatora niedostępny (Bedrock, `availableModels`) |
| limity | `You've hit your session/weekly limit`, `Request rejected (429)`, `Credit balance is too low`, `spend limit reached`, `Usage credits required for 1M context` | plan/konto; rotacja; `CLAUDE_CODE_DISABLE_1M_CONTEXT` |
| uwierzytelnienie | `Not logged in`, `Invalid API key`, `Your apiKeyHelper script is failing`, `Invalid ANTHROPIC_CUSTOM_HEADERS`, `OAuth token revoked or expired`, `Login expired`, `401 Invalid authentication credentials`, `Could not refresh your login because another Claude Code process is refreshing it` | kolejność poświadczeń (`ANTHROPIC_API_KEY` wygrywa w `-p`), wygasły token, wiele procesów na jednym `CLAUDE_CONFIG_DIR` |
| polityka organizacji | `Your organization has disabled API key authentication`, `Administrator policy requires a Cloud gateway sign-in`, `Managed settings don't allow this API provider`, `Claude Code can't start: your organization's managed settings block the default model` | `forceLoginMethod`, `allowedProviders`, `availableModels`/`deniedModels` |
| MCP | `MCP server "<nazwa>" needs you to sign in again`, `MCP server URL is missing`, `Tool input schema is invalid`, `MCP permission prompt tool not found` | OAuth serwera, zła konfiguracja, schemat narzędzia, nazwa narzędzia zgody |
| sieć | `Unable to connect to API`, `SSL certificate errors`, `Socket is closed`, `Host not allowed in a cloud session` | proxy, CA, `NO_PROXY`, lista hostów środowiska chmurowego |
| żądanie | `Prompt is too long`, `Request too large`, `Extra inputs are not permitted`, `Model is not a recognized model id`, `Model not found`, `Claude Code does not support this model`, `thinking.type.enabled is not supported` | brama zmienia treść; zbyt stary CLI dla modelu; `CLAUDE_CODE_MAX_CONTEXT_TOKENS` |
| wiersz poleceń | `Settings file exceeds the 2MiB limit`, `The current directory no longer exists`, `No conversation found with the session ID`, `Cannot add MCP server to the managed scope` | rozmiar ustawień, katalog roboczy, `--resume` z innym `CLAUDE_CONFIG_DIR`/`CLAUDE_CODE_PROJECT_DIR_NAME` |
| wtyczki | `Marketplace is registered from an untrusted source`, `Plugin archive integrity check failed`, `Path escapes plugin directory`, `Failed to load marketplace configuration` | `strictKnownMarketplaces`, ścieżki w manifeście |
| narzędzia | `Agent would be spawned with zero tools`, `File is covered by a Read deny rule`, `pkill pattern matches the Claude Code process` | `tools`/`disallowedTools` agenta, reguły deny |
| sesje w tle | `Commands refused in a background session`, `Workspace not trusted when dispatching…` | zaufanie folderu, `CLAUDE_CODE_PROCESS_WRAPPER` |
| zapis sesji | `Transcript writes are failing` | prawa/miejsce w `<konfiguracja>/projects` |
| konfiguracja | `Workspace has not been trusted`, `headersHelper not run`, `Is not matched by file permission checks`, `Has a wildcard before the rest of the command`, `Stale sandbox mask files…` | zaufanie, reguły uprawnień, zaślepki piaskownicy |

`Unrecognized model` w logu (`[claude-code:unrecognized_model]`, ≥2.1.233): identyfikator spoza
znanych — `modelOverrides` z tą wartością wycisza wiersz; literówka w `ANTHROPIC_DEFAULT_*_MODEL`
lub `model` podagenta (`query_source` zaczyna się od `agent:`).
