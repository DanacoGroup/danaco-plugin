# Agent SDK i Claude Managed Agents — odpowiedniki w Claude Code CLI

Źródła: `cc:agent-sdk/overview`, `cc:agent-sdk/configuration`, `cc:agent-sdk/typescript`,
`cc:agent-sdk/python`, `pl:managed-agents/*` (overview, agent-setup, tools, permission-policies,
sessions, events-and-streaming, environments, self-hosted-sandboxes, multiagent-orchestration,
skills, memory, budgets), macierz pełna CLI (tabele „Opcje Agent SDK” i „Mapa pojęć”).

## 1. Agent SDK → CLI

Agent SDK (TypeScript, Python) uruchamia tę samą binarkę CLI; większość opcji ma odpowiednik
we flagach, `--settings` albo protokole stream-json.

| Opcja SDK | CLI |
|---|---|
| `model`, `fallbackModel`, `effort` | `--model`, `--fallback-model`, `--effort` |
| `systemPrompt` (string, preset `claude_code` + `append`, `snapshot`, tablica z `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`, `excludeDynamicSections`) | `--system-prompt(-file)`, `--append-system-prompt(-file)`, `--system-prompt-snapshot`, wiersz `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__`, `--exclude-dynamic-system-prompt-sections` |
| `permissionMode`, `allowedTools`, `disallowedTools`, `tools` | `--permission-mode`, `--allowed-tools`, `--disallowed-tools`, `--tools` |
| `canUseTool` | host przez stream-json (`can_use_tool`) albo `--permission-prompt-tool` |
| `permissionPromptToolName`, `permissionPrompts` | `--permission-prompt-tool`, `--permission-prompts` |
| `settingSources`, `settings` | `--setting-sources`, `--settings` |
| `managedSettings` (host) | brak flagi — plik zarządzany w izolacji procesu |
| `mcpServers` (także `type: "sdk"` w procesie), `strictMcpConfig`, `setMcpServers()` | `--mcp-config`, `--strict-mcp-config` (serwera w procesie brak — most stdio) |
| `agents`, `agent` | `--agents`, `--agent` |
| `hooks` (wywołania zwrotne w procesie) | `hooks` w `--settings` (`command`, `http`, `mcp_tool`) |
| `skills`, `plugins` | brak listy skilli (`--disable-slash-commands`, `skillOverrides`); `--plugin-dir` |
| `outputFormat` | `--json-schema` |
| `resume`, `continue`, `forkSession`, `title` | `--resume`, `--continue`, `--fork-session`, `--name` |
| `sessionStore` | brak (tylko SDK) |
| `enableFileCheckpointing` | `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=true` |
| `sandbox` | `--settings '{"sandbox": …}'` |
| `maxTurns`, `maxBudgetUsd`, `taskBudget` | `--max-turns`, `--max-budget-usd`; `taskBudget` — brak |
| `includePartialMessages`, `forwardSubagentText`, `promptSuggestions` | `--include-partial-messages`, `--forward-subagent-text`, `--prompt-suggestions` |
| `env`, `cwd`, `additionalDirectories`/`add_dirs` | środowisko procesu, katalog roboczy, `--add-dir` |
| `thinking`, `maxThinkingTokens` | `MAX_THINKING_TOKENS`, `alwaysThinkingEnabled` |
| `interrupt()`, `setModel()`, `setPermissionMode()`, `applyFlagSettings()` | żądania sterujące stream-json |
| `cli_path`, `extra_args`, `spawnClaudeCodeProcess` | własny proces (np. w izolacji) |

Kiedy SDK zamiast CLI: potrzebny serwer MCP w procesie aplikacji (bez mostu), hooki jako
funkcje, `canUseTool` z interfejsem produktu (także dla `requiresUserInteraction`),
`SessionStore` w bazie produktu, `classifierContext` z wagą intencji użytkownika.

## 2. Claude Managed Agents → CLI

Managed Agents to uprząż agenta w infrastrukturze Anthropic (sesje, środowiska, piaskownice
chmurowe lub własne). Odpowiedniki pojęć:

| Managed Agents | CLI |
|---|---|
| `model` (`id`, `effort`, `speed`) | `--model`, `--effort`, `--fallback-model`, `modelSettings` |
| `system` | `--system-prompt-file` (+ dopiski, znacznik granicy) |
| `tools` (`agent_toolset_…`, `default_config.enabled`, `configs[]`) | `--tools` (jawna lista), `--disallowed-tools` |
| `permission_policy` (`always_allow`, `always_ask`, `auto`) | allow, ask + host zgód, tryb `auto` |
| `allowed_domains`/`blocked_domains` (web_fetch/web_search) | `WebFetch(domain:…)`; dla WebSearch tylko całe narzędzie |
| narzędzia `custom` | narzędzia MCP produktu (lub `type: "sdk"` w SDK) |
| `mcp_servers` + skarbce poświadczeń | `--mcp-config`, `headersHelper`, OAuth |
| `skills` | skille we wtyczce (`--plugin-dir`) |
| `multiagent` | `--agents`, `Agent`, deny `Agent(...)` |
| sesje, nadpisania na sesję, `budget` | `--session-id`/`--resume`, flagi przebiegu, `--max-budget-usd` |
| zdarzenia sesji, przerwanie | stream-json, `interrupt` |
| `environments` (`networking.limited.allowed_hosts`, pakiety) | piaskownica Bash (`allowedDomains`, `strictAllowlist`) + izolacja procesu |
| piaskownica samodzielnie hostowana | CLI w izolacji na własnym serwerze, narzędzia MCP poza izolacją |
| `memory` (magazyny pamięci) | pamięć automatyczna / `memory` podagenta (w usługach zwykle wyłączona) |
| limit wyniku narzędzia 100 000 znaków → plik | `MAX_MCP_OUTPUT_TOKENS`, `maxResultSizeChars`, `bashOutputMaxChars`; hook 10 000 znaków |

Bez odpowiednika w MA: style wyjścia, hooki (w MA ich rolę pełnią zdarzenia i potwierdzenia),
wtyczki, pliki ustawień i polityki zarządzane, OpenTelemetry (w MA konsola i `usage`).
