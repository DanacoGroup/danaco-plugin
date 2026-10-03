# Konfiguracja MCP: zakresy, zatwierdzanie, transporty, uwierzytelnianie, limity

Źródła: `cc:mcp`, `cc:mcp-quickstart`, `cc:settings-reference` (MCP), `cc:env-vars`,
`cc:permissions` (zaufanie), `cc:agent-sdk/mcp`. Próby: CLI 2.1.286.

## 1. Polecenia

| Polecenie | Zastosowanie |
|---|---|
| `claude mcp add [--scope local\|project\|user] [--transport stdio\|http\|sse] [--env K=V] [--header "K: V"] <nazwa> <url \| -- polecenie args>` | dodanie |
| `claude mcp add-json <nazwa> '<json>' [--scope …] [--client-secret]` | wpis z JSON (jedyna droga dla `ws` poza plikiem) |
| `claude mcp list`, `claude mcp get <nazwa>` | status: `✔ Connected`, `! Needs authentication`, `✘ Failed to connect` (+ szczegół), `⏸ Pending approval`, `✘ Rejected`, `⊘ Disabled` |
| `claude mcp remove <nazwa>` | usuwa także tokeny OAuth serwera |
| `claude mcp login <nazwa> [--no-browser]`, `claude mcp logout <nazwa>` | OAuth bez panelu |
| `claude mcp reset-project-choices` | reset zgód dla `.mcp.json` |
| `claude mcp serve` | Claude Code jako serwer MCP (stdio) |
| `/mcp` | panel: status, przełączanie, ponowne połączenie, uwierzytelnianie |

Przełączanie w `/mcp` zapisuje w `~/.claude.json` per projekt `disabledMcpServers`
(serwery zwykłe) albo `enabledMcpServers` (wbudowane domyślnie wyłączone, np. `computer-use`).
Niezwiązane z `enabledMcpjsonServers`/`disabledMcpjsonServers` (zatwierdzanie `.mcp.json`).

## 2. Zatwierdzanie serwerów projektu i zaufanie

- Interaktywnie: pytanie przed pierwszym użyciem serwera z `.mcp.json`.
- Zgody z repozytorium (`enableAllProjectMcpServers`, `enabledMcpjsonServers` w pliku
  projektu) nie działają przed zaufaniem folderu (≥2.1.196); działają zgody z
  `~/.claude/settings.json`, managed, `--settings`, nieśledzonego `settings.local.json`.
- `-p`, SDK, chmura: serwery z `.mcp.json` łączone **bez pytania** (SDK — gdy
  `settingSources` zawiera projekt); `bypassPermissions` + `skipDangerousModePermissionPrompt`
  też pomija pytanie.
- Blokady: `disabledMcpjsonServers` (każdy tryb), `--setting-sources` bez projektu,
  `--strict-mcp-config`.

## 3. Rozwijanie zmiennych

Składnia `${VAR}`, `${VAR:-domyślna}` w `command`, `args`, `env`, `url`, `headers`.
`/mcp`, `claude mcp list/get` pokazują odwołania, nie wartości (≥2.1.268). Lista
zmiennych czytanych jako puste w `url`/`headers` serwera zdalnego: poświadczenia Claude Code
(`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`…), dostawców chmurowych
(`AWS_BEARER_TOKEN_BEDROCK`…) i inne (`HTTPS_PROXY`, `NPM_TOKEN`); `ANTHROPIC_BASE_URL`
się rozwija. Debug: „never expanded toward a remote server”.

## 4. Środowiska uruchomieniowe klienta MCP

v1 (SDK TS 1.x) i v2 (SDK 2.0, rewizja protokołu 2026-07-28; domyślna od 2.1.232 przy
flagach funkcji, od 2.1.274 bez nich). v2: negocjacja wersji z serwerami HTTP,
`list_changed` przez trzymany strumień (ograniczenia ponownych otwarć), ścisła walidacja
wystawcy OAuth, tokeny tylko do punktu HTTPS lub localhost. Wybór: `MCP_SDK_GENERATION=v1|v2`,
`MCP_PROTOCOL_NEGOTIATION=auto|legacy`.

## 5. Połączenie i ponowne łączenie

- start: serwery łączone w tle (`MCP_CONNECTION_NONBLOCKING`), `alwaysLoad` czeka do 5 s;
  `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` (≥2.1.274); w `-p` czekanie do `MCP_TIMEOUT`;
- brak tool search → model czeka narzędziem `WaitForMcpServers`;
- zerwane połączenie zdalne → automatyczne ponowne łączenie; nieudane pierwsze połączenie
  i błędy wykrywania opisuje `cc:mcp` „Automatic reconnection”;
- `MCP_SERVER_CONNECTION_BATCH_SIZE`, `MCP_REMOTE_SERVER_CONNECTION_BATCH_SIZE` — równoległość łączenia.

## 6. Uwierzytelnianie

| Mechanizm | Kiedy | Uwagi |
|---|---|---|
| OAuth (dynamiczna rejestracja) | serwery HTTP/SSE z OAuth | `/mcp` → Authenticate, `claude mcp login` |
| stały port zwrotny | dostawca wymaga zarejestrowanego redirect | `oauth.callbackPort`, `MCP_OAUTH_CALLBACK_PORT` |
| klient wstępnie zarejestrowany | brak dynamicznej rejestracji | `oauth.clientId` + `--client-secret` (`MCP_CLIENT_SECRET`) |
| nadpisanie metadanych, zakresy | niestandardowy serwer autoryzacji | `oauth.*` (patrz `cc:mcp`) |
| nagłówek statyczny | token długoterminowy | `headers` z `${VAR}` — nie wpisuj tokenu dosłownie |
| `headersHelper` | Kerberos, SSO, krótkie tokeny | JSON na stdout, 10 s, zmienne `CLAUDE_CODE_MCP_SERVER_NAME`, `CLAUDE_CODE_MCP_SERVER_URL` |

## 7. Konektory claude.ai

Ładowane przy logowaniu claude.ai (nie przy tokenie z `claude setup-token`); wyłączenie:
`disableClaudeAiConnectors: true` (wartość `true` z dowolnego źródła wygrywa),
`ENABLE_CLAUDEAI_MCP_SERVERS=false`, `--strict-mcp-config`; pojedyncze — `deniedMcpServers`
(`serverName: "claude.ai Slack"` lub `serverUrl`). Organizacja może ustawić narzędzie
konektora na `ask` — allow nie działa, `dontAsk` odrzuca.

## 8. Uprawnienia i hooki dla MCP

Reguły: `mcp__serwer`, `mcp__serwer__*`, `mcp__serwer__narzedzie`; deny `mcp__*` usuwa
wszystkie narzędzia MCP; parametr narzędzia MCP tylko flagą `--disallowed-tools`.
Hooki: matcher `mcp__serwer__.*`; typ `mcp_tool` wywołuje narzędzie z hooka. Narzędzie
wskazane w `--permission-prompt-tool` CLI ukrywa przed modelem (próba).

## 9. Limity i zmienne

| Zmienna / klucz | Domyślnie | Znaczenie |
|---|---|---|
| `MCP_TIMEOUT` | 30 000 ms | start serwera / czekanie w `-p` |
| `MCP_TOOL_TIMEOUT` | — | limit czasu wywołania (per serwer `timeout`) |
| `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` | — | bezczynność wywołania |
| `MAX_MCP_OUTPUT_TOKENS` | 25 000 | limit wyniku (ostrzeżenie od 10 000) |
| `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` | 2048 | opisy narzędzi i instrukcje serwera (≥2.1.280) |
| `ENABLE_TOOL_SEARCH` | (włączony) | `true`/`auto[:N]`/`false` |
| `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` | 120 000 | próg przejścia w tło; `0` wyłącza |
| `MCP_DISCOVERY_CACHE` | wyłączony | pamięć listy narzędzi serwerów zdalnych |
| `CLAUDE_AGENT_SDK_MCP_NO_PREFIX` | — | SDK: nazwy narzędzi bez przedrostka |

## 10. Agent SDK

`mcpServers` w opcjach (stdio, http, sse, oraz `type: "sdk"` — serwer w procesie aplikacji,
pomija listy dozwolone), `strictMcpConfig`, `setMcpServers()`; odpowiedniki CLI:
`--mcp-config`, `--strict-mcp-config`. Serwer w procesie usuwa potrzebę mostu stdio
w produktach z izolacją procesu CLI.
