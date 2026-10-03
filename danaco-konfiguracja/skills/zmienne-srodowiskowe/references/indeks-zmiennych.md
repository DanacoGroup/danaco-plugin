# Indeks zmiennych środowiskowych Claude Code

Wygenerowano z `wspolne/indeksy/zmienne.tsv` (376 zmiennych, strona `cc:env-vars`, stan 01.10.2026) skryptem `scripts/buduj_indeks_md.py`. Opis — pierwsze zdanie dokumentacji (oryginał); pełny opis: `scripts/szukaj.py --typ zmienna NAZWA --pelny`.

## Spis treści

- [Uwierzytelnianie i dostawcy](#uwierzytelnianie-i-dostawcy) — 67
- [Model, effort i myślenie](#model-effort-i-myślenie) — 46
- [Cache promptu](#cache-promptu) — 12
- [Kontekst, kompakcja i wyjście](#kontekst-kompakcja-i-wyjście) — 10
- [Sesje, headless i osadzanie](#sesje-headless-i-osadzanie) — 27
- [Podagenci, zespoły i zadania w tle](#podagenci-zespoły-i-zadania-w-tle) — 33
- [Narzędzia wbudowane](#narzędzia-wbudowane) — 29
- [MCP](#mcp) — 20
- [Skille, wtyczki i polecenia](#skille-wtyczki-i-polecenia) — 21
- [Uprawnienia i tryby](#uprawnienia-i-tryby) — 7
- [Bezpieczeństwo i izolacja](#bezpieczeństwo-i-izolacja) — 4
- [Pamięć i CLAUDE.md](#pamięć-i-claudemd) — 5
- [Instrukcja i tożsamość](#instrukcja-i-tożsamość) — 3
- [Hooki](#hooki) — 2
- [Telemetria i prywatność](#telemetria-i-prywatność) — 31
- [Sieć, proxy i niezawodność](#sieć-proxy-i-niezawodność) — 22
- [Aktualizacje i instalacja](#aktualizacje-i-instalacja) — 5
- [Ustawienia i zarządzanie](#ustawienia-i-zarządzanie) — 2
- [Diagnostyka i logi](#diagnostyka-i-logi) — 3
- [Interfejs terminala i IDE](#interfejs-terminala-i-ide) — 27

## Uwierzytelnianie i dostawcy

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `ANTHROPIC_API_KEY` |  | API key sent as `X-Api-Key` header. |
| `ANTHROPIC_AUTH_TOKEN` |  | Custom value for the `Authorization` header (the value you set here will be prefixed with `Bearer `) |
| `ANTHROPIC_AWS_API_KEY` |  | Workspace API key for Claude Platform on AWS, generated in the AWS Console. |
| `ANTHROPIC_AWS_BASE_URL` |  | Override the Claude Platform on AWS endpoint URL. |
| `ANTHROPIC_AWS_WORKSPACE_ID` |  | Required for Claude Platform on AWS. |
| `ANTHROPIC_BASE_URL` | 2.1.196 | Override the API endpoint to route requests through a proxy or gateway. |
| `ANTHROPIC_BEDROCK_BASE_URL` |  | Override the Amazon Bedrock endpoint URL. |
| `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` |  | Override the Amazon Bedrock Mantle endpoint URL. |
| `ANTHROPIC_BEDROCK_REGION_PREFIX` | 2.1.224 | Cross-region inference profile prefix (`us`, `eu`, `apac`, `jp`, `au`, or `global`) Claude Code tries first instead of the one derived from the AWS region. |
| `ANTHROPIC_BEDROCK_SERVICE_TIER` |  | Amazon Bedrock service tier (`default`, `flex`, or `priority`). |
| `ANTHROPIC_BETAS` |  | Comma-separated list of additional `anthropic-beta` header values to include in API requests. |
| `ANTHROPIC_CUSTOM_HEADERS` | 2.1.227 | Custom headers to add to requests (`Name: Value` format, newline-separated for multiple headers). |
| `ANTHROPIC_FEDERATION_RULE_ID` |  | Federation rule ID for Workload Identity Federation. |
| `ANTHROPIC_FOUNDRY_API_KEY` |  | API key for Microsoft Foundry authentication (see Microsoft Foundry) |
| `ANTHROPIC_FOUNDRY_AUTH_TOKEN` | 2.1.203 | Bearer token for Microsoft Foundry authentication, such as a Microsoft Entra access token. |
| `ANTHROPIC_FOUNDRY_BASE_URL` |  | Full base URL for the Microsoft Foundry resource (for example, `https://my-resource.services.ai.azure.com/anthropic`). |
| `ANTHROPIC_FOUNDRY_RESOURCE` |  | Microsoft Foundry resource name (for example, `my-resource`). |
| `ANTHROPIC_ORGANIZATION_ID` |  | Organization ID for Workload Identity Federation. |
| `ANTHROPIC_PROFILE` |  | Name of the Anthropic profile to authenticate with, such as one created by `ant auth login` or by signing in to a Console account without an API key. |
| `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION` |  | Override AWS region for the Haiku-class model when using Amazon Bedrock or Amazon Bedrock Mantle. |
| `ANTHROPIC_VERTEX_BASE_URL` |  | Override Google Cloud's Agent Platform endpoint URL. |
| `ANTHROPIC_VERTEX_PROJECT_ID` |  | GCP project ID that Google Cloud's Agent Platform requests are addressed to. |
| `ANTHROPIC_WORKSPACE_ID` |  | Workspace ID for workload identity federation. |
| `AWS_BEARER_TOKEN_BEDROCK` |  | Amazon Bedrock API key for authentication (see Amazon Bedrock API keys) |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` |  | Interval in milliseconds at which credentials should be refreshed (when using `apiKeyHelper`) |
| `CLAUDE_CODE_AWS_CHAIN_RESOLVE_TIMEOUT_MS` | 2.1.207 | Time in milliseconds Claude Code waits for the AWS default credential provider chain to produce credentials before the request fails with `AWS default-chain credential resolve timed out` (default: `60000`). |
| `CLAUDE_CODE_DISABLE_AUTH_REFRESH_LOCK` | 2.1.286 | Set to `1` to make a Claude Code process run its `gcpAuthRefresh` or `awsAuthRefresh` command itself instead of waiting while another process runs it. |
| `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` |  | Set to `1` to populate the `/model` picker from your gateway's `/v1/models` endpoint when `ANTHROPIC_BASE_URL` points at an Anthropic-compatible gateway such as LiteLLM, Kong, or an internal proxy. |
| `CLAUDE_CODE_GATEWAY_HINT_HEADERS` | 2.1.273 | Set to `1` to send the gateway hint headers, such as `x-claude-code-request-class` and `x-claude-code-compaction`, on a custom proxy or a third-party provider such as Amazon Bedrock or Claude Platform on AWS. |
| `CLAUDE_CODE_GATEWAY_MODEL_DISCOVERY_TIMEOUT_MS` | 2.1.269 | Timeout in milliseconds for the gateway model discovery request that `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` turns on (default: `3000`). |
| `CLAUDE_CODE_OAUTH_REFRESH_TOKEN` |  | OAuth refresh token for Claude.ai authentication. |
| `CLAUDE_CODE_OAUTH_SCOPES` |  | Space-separated OAuth scopes the refresh token was issued with, such as `"user:profile user:inference user:sessions:claude_code"`. |
| `CLAUDE_CODE_OAUTH_TOKEN` |  | OAuth access token for claude.ai authentication. |
| `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` |  | Set by host platforms that embed Claude Code and manage model provider routing on its behalf. |
| `CLAUDE_CODE_SKIP_ANTHROPIC_AWS_AUTH` |  | Skip client-side authentication for Claude Platform on AWS, for gateways that sign requests themselves |
| `CLAUDE_CODE_SKIP_AWS_CRED_CACHE` | 2.1.207 | Set to `1` to turn off the in-process cache of credentials resolved from the AWS default credential provider chain, so Claude Code resolves the chain on every API request. |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` |  | Skip AWS authentication for Amazon Bedrock (for example, when using an LLM gateway) |
| `CLAUDE_CODE_SKIP_FOUNDRY_AUTH` | 2.1.203 | Skip Azure authentication for Microsoft Foundry, for a proxy or gateway that injects its own `Authorization` header. |
| `CLAUDE_CODE_SKIP_MANTLE_AUTH` |  | Skip AWS authentication for Amazon Bedrock Mantle (for example, when using an LLM gateway) |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` |  | Skip Google authentication for Google Cloud's Agent Platform (for example, when using an LLM gateway) |
| `CLAUDE_CODE_USE_ANTHROPIC_AWS` |  | Use Claude Platform on AWS |
| `CLAUDE_CODE_USE_BEDROCK` |  | Use Amazon Bedrock |
| `CLAUDE_CODE_USE_FOUNDRY` |  | Use Microsoft Foundry |
| `CLAUDE_CODE_USE_MANTLE` |  | Use the Amazon Bedrock Mantle endpoint |
| `CLAUDE_CODE_USE_VERTEX` |  | Use Google Cloud's Agent Platform |
| `DISABLE_LOGIN_COMMAND` |  | Set to `1` to hide the `/login` command. |
| `DISABLE_LOGOUT_COMMAND` |  | Set to `1` to hide the `/logout` command |
| `MCP_OAUTH_CALLBACK_PORT` |  | Fixed port for the OAuth redirect callback, as an alternative to `--callback-port` when adding an MCP server with pre-configured credentials |
| `VERTEX_REGION_CLAUDE_3_5_HAIKU` |  | Override region for Claude 3.5 Haiku when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_3_5_SONNET` |  | Override region for Claude 3.5 Sonnet when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_3_7_SONNET` |  | Override region for Claude 3.7 Sonnet when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_0_OPUS` |  | Override region for Claude 4.0 Opus when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_0_SONNET` |  | Override region for Claude 4.0 Sonnet when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_1_OPUS` |  | Override region for Claude 4.1 Opus when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_5_OPUS` |  | Override region for Claude Opus 4.5 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_5_SONNET` |  | Override region for Claude Sonnet 4.5 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_6_OPUS` |  | Override region for Claude Opus 4.6 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_6_SONNET` |  | Override region for Claude Sonnet 4.6 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_7_OPUS` |  | Override region for Claude Opus 4.7 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_4_8_OPUS` |  | Override region for Claude Opus 4.8 when using Google Cloud's Agent Platform |
| `VERTEX_REGION_CLAUDE_5_5_OPUS` | 2.1.280 | Override region for Claude Opus 5.5 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_5_5_SONNET` | 2.1.284 | Override region for Claude Sonnet 5.5 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_5_OPUS` | 2.1.219 | Override region for Claude Opus 5 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_5_SONNET` | 2.1.197 | Override region for Claude Sonnet 5 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_FABLE_5` | 2.1.170 | Override region for Claude Fable 5 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_FABLE_5_1` | 2.1.257 | Override region for Claude Fable 5.1 when using Google Cloud's Agent Platform. |
| `VERTEX_REGION_CLAUDE_HAIKU_4_5` |  | Override region for Claude Haiku 4.5 when using Google Cloud's Agent Platform |

## Model, effort i myślenie

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `ANTHROPIC_CUSTOM_MODEL_OPTION` |  | Model ID to add as a custom entry in the `/model` picker. |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION` |  | Display description for the custom model entry in the `/model` picker. |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` |  | Display name for the custom model entry in the `/model` picker. |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_SUPPORTED_CAPABILITIES` |  | Comma-separated list of capabilities the custom model supports, for example `effort,thinking`. |
| `ANTHROPIC_DEFAULT_FABLE_MODEL` |  | Model ID that the `fable` alias resolves to, and the ID Claude Code recognizes as a Fable model for automatic model fallback on third-party providers. |
| `ANTHROPIC_DEFAULT_FABLE_MODEL_DESCRIPTION` |  | Display description for the pinned Fable model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_FABLE_MODEL_NAME` |  | Display name for the pinned Fable model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_FABLE_MODEL_SUPPORTED_CAPABILITIES` |  | Comma-separated list of capabilities the pinned Fable model supports, for example `effort,thinking`. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` |  | Model ID that the `haiku` alias resolves to, also used for background functionality. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL_DESCRIPTION` |  | Display description for the pinned Haiku model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME` |  | Display name for the pinned Haiku model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL_SUPPORTED_CAPABILITIES` |  | Comma-separated list of capabilities the pinned Haiku model supports, for example `effort,thinking`. |
| `ANTHROPIC_DEFAULT_MODEL` | 2.1.236 | Model that new sessions start on by default. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` |  | Model ID that the `opus` alias resolves to, and that `opusplan` uses while Plan Mode is active. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION` |  | Display description for the pinned Opus model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_NAME` |  | Display name for the pinned Opus model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES` |  | Comma-separated list of capabilities the pinned Opus model supports, for example `effort,thinking`. |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` |  | Model ID that the `sonnet` alias resolves to, and that `opusplan` uses when Plan Mode is not active. |
| `ANTHROPIC_DEFAULT_SONNET_MODEL_DESCRIPTION` |  | Display description for the pinned Sonnet model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_SONNET_MODEL_NAME` |  | Display name for the pinned Sonnet model in the `/model` picker. |
| `ANTHROPIC_DEFAULT_SONNET_MODEL_SUPPORTED_CAPABILITIES` |  | Comma-separated list of capabilities the pinned Sonnet model supports, for example `effort,thinking`. |
| `ANTHROPIC_MODEL` |  | Name of the model setting to use (see Model Configuration) |
| `ANTHROPIC_SMALL_FAST_MODEL` |  | \DEPRECATED Name of Haiku-class model for background tasks |
| `CLAUDE_CODE_ALWAYS_ENABLE_EFFORT` |  | Set to `1` to send the effort parameter with every request, even when Claude Code does not recognize the model ID as effort-capable. |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` |  | Set to `1` to disable 1M context window support. |
| `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` |  | Set to `1` to disable adaptive reasoning on Opus 4.6 and Sonnet 4.6 and fall back to the fixed thinking budget controlled by `MAX_THINKING_TOKENS`. |
| `CLAUDE_CODE_DISABLE_ADVISOR_TOOL` |  | Set to `1` to disable the advisor tool. |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | 2.1.227 | Set to `1` to strip Anthropic-specific `anthropic-beta` request headers and beta tool-schema fields (such as `defer_loading` and `eager_input_streaming`) from API requests. |
| `CLAUDE_CODE_DISABLE_FAST_MODE` |  | Set to `1` to disable fast mode |
| `CLAUDE_CODE_DISABLE_LEGACY_MODEL_REMAP` |  | Set to `1` to prevent automatic remapping of Opus 4.0 and 4.1 to the current Opus version on the Anthropic API. |
| `CLAUDE_CODE_DISABLE_MODEL_ACCESS_FALLBACK` | 2.1.285 | Set to `1` to stop Claude Code on Amazon Bedrock and Google Cloud's Agent Platform from switching to an older model when your account loses access to a session's model mid-session; the refused request fails at once instead. |
| `CLAUDE_CODE_DISABLE_THINKING` |  | Set to `1` to omit the `thinking` parameter from API requests entirely. |
| `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT` | 2.1.223 | Set to `1` to skip proactive auto-compaction when Claude Code doesn't recognize the model ID, such as an LLM gateway alias. |
| `CLAUDE_CODE_EFFORT_LEVEL` |  | Set the effort level for supported models. |
| `CLAUDE_CODE_ENABLE_OPUS_4_7_FAST_MODE` | 2.1.142 | Removed in v2.1.142, when the fast mode default moved from Opus 4.6 to Opus 4.7 |
| `CLAUDE_CODE_EXTRA_BODY` | 2.1.206 | JSON object to merge into the top level of every API request body. |
| `CLAUDE_CODE_OPUS_4_6_FAST_MODE_OVERRIDE` | 2.1.160 | Removed in v2.1.160 and now a no-op. |
| `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS` |  | Set to `1` to treat a failed fast mode availability check as available, for networks that block the check's direct request to `api.anthropic.com`. |
| `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK` |  | Set to `1` to skip the client-side fast mode availability check, for proxies that intercept the check's request rather than refuse it. |
| `CLAUDE_CODE_SKIP_MODEL_ACCESS_MEMORY` | 2.1.285 | The startup model checks on Amazon Bedrock and Google Cloud's Agent Platform remember on this machine which models they found your account can't invoke, for up to a day. |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 2.1.251 | The default model for subagents, agent team teammates, and workflow agents that aren't assigned a model another way. |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | 2.1.257 | Set to `1` to force one model onto subagents, teammates, and workflow agents. |
| `CLAUDE_EFFORT` |  | Set automatically in Bash tool subprocesses and hook commands to the effort level in effect when the subprocess starts: `low`, `medium`, `high`, `xhigh`, or `max`. |
| `DISABLE_INTERLEAVED_THINKING` |  | Set to `1` to prevent sending the interleaved-thinking beta header. |
| `FALLBACK_FOR_ALL_PRIMARY_MODELS` | 2.1.160 | Set to any non-empty value, such as `1`, to make Claude Code stop retrying on repeated overload errors for every model when no fallback model is configured. |
| `MAX_THINKING_TOKENS` |  | Fixed token budget for extended thinking. |

## Cache promptu

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_PROMPT_CACHE_TTL` | 2.1.242 | Set `5m` or `1h`, the only values Claude Code accepts, to choose the prompt cache TTL for the main conversation: your interactive, `-p`, and SDK turns, plus the helpers that run inline with them. |
| `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` | 2.1.242 | Set `5m` or `1h`, the only values Claude Code accepts, to choose the prompt cache TTL for requests outside the main conversation, such as subagents, workflows, and background work. |
| `CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS` | 2.1.233 | Set to the number of milliseconds WebFetch keeps each fetched URL's response cached. |
| `DISABLE_PROMPT_CACHING` |  | Set to `1` to disable prompt caching for all models (takes precedence over per-model settings) |
| `DISABLE_PROMPT_CACHING_FABLE` |  | Set to `1` to disable prompt caching for Fable models |
| `DISABLE_PROMPT_CACHING_HAIKU` |  | Set to `1` to disable prompt caching for the default Haiku model, wherever it runs |
| `DISABLE_PROMPT_CACHING_OPUS` |  | Set to `1` to disable prompt caching for the default Opus model |
| `DISABLE_PROMPT_CACHING_SONNET` |  | Set to `1` to disable prompt caching for the default Sonnet model |
| `ENABLE_PROMPT_CACHING_1H` |  | Set to `1` to request a 1-hour prompt cache TTL instead of the default 5 minutes. |
| `ENABLE_PROMPT_CACHING_1H_BEDROCK` |  | Deprecated. |
| `FORCE_PROMPT_CACHING_5M` |  | Set to `1` to force the 5-minute prompt cache TTL even when 1-hour TTL would otherwise apply. |
| `MCP_DISCOVERY_CACHE_TTL_S` | 2.1.238 | Seconds for which Claude Code uses a discovery-cache entry without refreshing it (default: 900). |

## Kontekst, kompakcja i wyjście

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `BASH_MAX_OUTPUT_LENGTH` |  | Maximum number of characters of bash output that Claude Code reads back into a command's result (default: 30000; maximum: 150000). |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` |  | Set the percentage (1-100) of the auto-compact window at which auto-compaction triggers. |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` |  | Set the auto-compact window in tokens, from `100000` to `1000000`. |
| `CLAUDE_CODE_DISABLE_ATTACHMENTS` |  | Set to `1` to disable attachment processing. |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` |  | Override the default token limit for file reads. |
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS` | 2.1.193 | Override the context window size Claude Code assumes for the active model. |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` |  | Set the maximum number of output tokens for most requests. |
| `DISABLE_AUTO_COMPACT` |  | Set to `1` to disable automatic compaction when approaching the context limit. |
| `DISABLE_COMPACT` |  | Set to `1` to disable all compaction: both automatic compaction and the manual `/compact` command |
| `MAX_STRUCTURED_OUTPUT_RETRIES` |  | Number of attempts Claude Code allows when the model's response fails validation against the `--json-schema` in non-interactive mode with the `-p` flag; after that many failed attempts with no valid output, the run fails. |

## Sesje, headless i osadzanie

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CCR_FORCE_BUNDLE` |  | Set to `1` to force `claude --cloud` to bundle and upload your local repository instead of cloning from its remote |
| `CLAUDECODE` |  | Set to `1` in subprocesses Claude Code spawns (Bash and PowerShell tools, tmux sessions, hook commands, status line commands, stdio MCP server subprocesses). |
| `CLAUDE_CODE_BRIDGE_SESSION_ID` | 2.1.199 | Set automatically in Bash tool and hook command subprocesses while the session has an active Remote Control connection, and removed when the connection ends. |
| `CLAUDE_CODE_ENABLE_AWAY_SUMMARY` |  | Override session recap availability. |
| `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION` | 2.1.238 | Set to `false` to turn off prompt suggestions, the grayed-out predictions that appear in your prompt input. |
| `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY` |  | Time in milliseconds to wait after the query loop becomes idle before automatically exiting. |
| `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` | 2.1.178 | Set to `1` to force transcript persistence, prompt history, and `claude agents` registration even when this `claude` was launched from inside another Claude Code session. |
| `CLAUDE_CODE_FORCE_SYNC_OUTPUT` |  | Set to `1` to force-enable DEC private mode 2026 synchronized output when your terminal supports it but is not auto-detected. |
| `CLAUDE_CODE_GOAL_CHECKIN_MINUTES` | 2.1.234 | How many minutes background work can keep an active goal waiting before Claude Code asks Claude to check on it. |
| `CLAUDE_CODE_MAX_TURNS` |  | Cap the number of agentic turns when no explicit limit is passed. |
| `CLAUDE_CODE_NONBLOCKING_STDOUT` | 2.1.261 | Set to `1` to write terminal output through a second non-blocking file descriptor, so a terminal that stops reading, such as a paused tmux control-mode pane or a stalled SSH connection, can't freeze Claude Code mid-session. |
| `CLAUDE_CODE_PROJECT_DIR_NAME` | 2.1.234 | Set together with `CLAUDE_CONFIG_DIR` to choose the `projects/` directory name Claude Code stores that session's transcripts and auto memory under, in place of one derived from the working directory path. |
| `CLAUDE_CODE_REMOTE` |  | Set automatically to `true` when Claude Code is running as a cloud session. |
| `CLAUDE_CODE_REMOTE_SESSION_ID` |  | Set automatically in cloud sessions to the current session's ID. |
| `CLAUDE_CODE_RESUME_INTERRUPTED_TURN` | 2.1.221 | Set to `1` to automatically resume if the previous session ended mid-turn. |
| `CLAUDE_CODE_RESUME_INTERRUPTED_TURN_MAX_AGE_MS` | 2.1.211 | Maximum age in milliseconds of the last transcript message for a session that ended mid-turn to continue automatically on resume. |
| `CLAUDE_CODE_RESUME_PROMPT` |  | Override the continuation message Claude Code sends to Claude when `CLAUDE_CODE_RESUME_INTERRUPTED_TURN` continues an interrupted turn instead of resending its prompt, or when you resume a deferred tool call with `-p`. |
| `CLAUDE_CODE_SESSION_ID` |  | Set automatically to the current session ID in Bash and PowerShell tool subprocesses, hook command subprocesses, and stdio MCP server subprocesses. |
| `CLAUDE_CODE_SIMPLE` |  | Set to `1` to run with a minimal system prompt and only the Bash, file read, and file edit tools. |
| `CLAUDE_CODE_SKIP_PROMPT_HISTORY` |  | Set to `1` to skip writing prompt history and session transcripts to disk. |
| `CLAUDE_CODE_STARTUP_FAILURE_RESULTS` | 2.1.274 | Set to `1` to have a session started with `--output-format stream-json` write a result message naming why Claude Code refused to start for startup failures that otherwise end with stderr alone. |
| `CLAUDE_CODE_TMPDIR` |  | Override the temp directory used for internal temp files. |
| `CLAUDE_CONFIG_DIR` |  | Override the configuration directory (default: `~/.claude`). |
| `CLAUDE_ENV_FILE` |  | Path to a shell script whose contents Claude Code runs before each Bash command in the same shell process, so exports in the file are visible to the command. |
| `CLAUDE_PID` | 2.1.214 | Claude Code sets this to its own process ID in the subprocesses it spawns: Bash and PowerShell tool commands and hook commands. |
| `CLAUDE_REMOTE_CONTROL_SESSION_NAME_PREFIX` |  | Prefix for auto-generated Remote Control session names when no explicit name is provided. |
| `IS_DEMO` |  | Set to any non-empty value, such as `1`, to enable demo mode: hides your email and organization name from the header and `/status` output, and skips onboarding. |

## Podagenci, zespoły i zadania w tle

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_AFK_COUNTDOWN_MS` | 2.1.198 | How many milliseconds before auto-continue the on-screen countdown appears on an unanswered `AskUserQuestion` dialog. |
| `CLAUDE_AFK_TIMEOUT_MS` | 2.1.198 | How many milliseconds of idle time before an unanswered `AskUserQuestion` dialog auto-continues without you. |
| `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS` |  | Set to `1` to disable all built-in subagent types such as Explore and Plan. |
| `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS` |  | Stall timeout in milliseconds for subagents. |
| `CLAUDE_AUTO_BACKGROUND_TASKS` | 2.1.212 | Set to `1` to force-enable automatic backgrounding of long-running agent tasks. |
| `CLAUDE_CODE_AUTO_BACKGROUND_WORKER_CHECKIN_SECONDS` | 2.1.248 | When `CLAUDE_AUTO_BACKGROUND_TASKS` is enabled, seconds between reminders to Claude to check on background subagents that are still running. |
| `CLAUDE_CODE_BG_TASKS_REPORT_RUNNING` | 2.1.269 | Set to `0` to make a non-interactive session report an idle status to its host at every turn end, even while background work is still running. |
| `CLAUDE_CODE_CHILD_SESSION` | 2.1.172 | Set to `1` in subprocesses Claude Code spawns via the Bash, PowerShell, and Monitor tools, hook commands, and status line commands. |
| `CLAUDE_CODE_DISABLE_AGENT_VIEW` |  | Set to `1` to turn off background agents and agent view: `claude agents`, `--bg`, `/background`, and the on-demand supervisor. |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` |  | Set to `1` to disable all background task functionality, including the `run_in_background` parameter on Bash and subagent tools, auto-backgrounding, and the Ctrl+B shortcut |
| `CLAUDE_CODE_DISABLE_BG_EXIT_HANDOFF` | 2.1.198 | Set to `1` to stop a background session's running background shell commands, dynamic workflows, and, as of v2.1.198, background subagents when the supervisor stops, restarts, or updates that session's process, instead of handing them to th… |
| `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP` | 2.1.193 | Set to `1` to stop Claude Code from terminating background shell commands under memory pressure. |
| `CLAUDE_CODE_DISABLE_CRON` |  | Set to `1` to disable scheduled tasks. |
| `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS` | 2.1.198 | Set to `1` to disable the built-in Explore and Plan subagents. |
| `CLAUDE_CODE_DISABLE_WORKFLOWS` |  | Set to `1` to disable workflows. |
| `CLAUDE_CODE_ENABLE_BACKGROUND_PLUGIN_REFRESH` |  | Set to `1` to refresh plugin state at turn boundaries in non-interactive mode after a background install completes. |
| `CLAUDE_CODE_ENABLE_TASKS` |  | Selects which task-tracking tools Claude Code provides in sessions that have them. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` |  | Set to `1` to enable agent teams. |
| `CLAUDE_CODE_FORK_SUBAGENT` | 2.1.232 | Controls fork mode, which lets Claude spawn forked subagents itself and is on by default in interactive sessions only. |
| `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT` | 2.1.211 | Set to `1` to emit subagent text and thinking blocks in `claude -p --output-format stream-json` output, the same behavior as the `--forward-subagent-text` flag. |
| `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | 2.1.217 | How many subagents can be running in one session before the Agent tool refuses to spawn another (default: 20). |
| `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` | 2.1.224 | Removed in v2.1.224 and now a no-op. |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | 2.1.217 | Number of subagent layers allowed below the main conversation (default: 3). |
| `CLAUDE_CODE_MESSAGING_SOCKET` | 2.1.224 | Set by Claude Code, not by you: in sessions that bind an inbox socket, Claude Code exports that socket's path to hooks and Bash commands when it binds the socket. |
| `CLAUDE_CODE_MESSAGING_TOKEN` | 2.1.228 | Set by Claude Code, not by you: in sessions that bind an inbox socket, Claude Code exports this per-session token to hooks and Bash commands alongside `CLAUDE_CODE_MESSAGING_SOCKET`. |
| `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` | 2.1.182 | Ceiling in milliseconds on idle waiting for background subagents and workflows after the final turn in non-interactive mode with the `-p` flag. |
| `CLAUDE_CODE_TASK_LIST_ID` |  | Share a task list across sessions. |
| `CLAUDE_CODE_TEAM_TEARDOWN_PARK_TIMEOUT_MS` | 2.1.206 | Override, in milliseconds, how long a non-interactive session waits at exit for its agent team to finish tearing down. |
| `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` | 2.1.269 | How many agents a single workflow run executes at once, from `1` to `256`. |
| `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` | 2.1.229 | Upper bound in milliseconds on how long a workflow agent waits for a same-prefix sibling's first response to begin before sending its own first request. |
| `CLAUDE_JOB_DIR` |  | Set by Claude Code in each background session to that session's `~/.claude/jobs/<id>` directory. |
| `CLAUDE_SUBAGENT_BG_SHELL_MAX_MS` | 2.1.260 | Removed in v2.1.260 and now a no-op. |
| `TASK_MAX_OUTPUT_LENGTH` | 2.1.277 | Removed in v2.1.277 and now a no-op, together with the `TaskOutput` tool it sized. |

## Narzędzia wbudowane

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `BASH_DEFAULT_TIMEOUT_MS` | 2.1.285 | Default timeout for a foreground Bash or PowerShell tool command, in milliseconds (default: 120000, or 2 minutes). |
| `BASH_MAX_TIMEOUT_MS` | 2.1.285 | Maximum timeout the model can set for a foreground Bash or PowerShell tool command, in milliseconds (default: 600000, or 10 minutes). |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` |  | Return to the original working directory after each Bash or PowerShell command in the main session |
| `CLAUDE_CODE_ARTIFACT_AUTO_OPEN` |  | Set to `0` to stop Claude Code from opening the browser automatically when a new artifact is published |
| `CLAUDE_CODE_ARTIFACT_COMMENTS` | 2.1.221 | Set to `0` to stop Claude reading and replying to comments on an artifact. |
| `CLAUDE_CODE_ARTIFACT_COMMENTS_AUTOREACT` | 2.1.228 | Set to `0` to stop Claude replying on its own to comments sent to it. |
| `CLAUDE_CODE_DISABLE_ARTIFACT` |  | Set to `1` to turn off the Artifact tool, which publishes session output as a private web page on claude.ai. |
| `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` |  | Set to `1` to disable file checkpointing. |
| `CLAUDE_CODE_DISABLE_POWERSHELL_CMD_RM_DENY` | 2.1.283 | Set to `1` to turn off the PowerShell tool check that denies the `cmd` built-ins `rd`, `rmdir`, `del`, and `erase` on a system path, such as a drive root or your home directory. |
| `CLAUDE_CODE_DISABLE_WEB_FETCH` | 2.1.285 | Set to `1` to turn off the WebFetch tool. |
| `CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER` | 2.1.269 | Set to `1` to start PowerShell tool commands on Windows directly instead of through the `cmd.exe` launcher. |
| `CLAUDE_CODE_ENABLE_FINE_GRAINED_TOOL_STREAMING` |  | Controls whether tool call inputs stream from the API as Claude generates them. |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS` | 2.1.233 | Set to `1` to get the task-tracking tools on every model. |
| `CLAUDE_CODE_GIT_BASH_PATH` | 2.1.219 | Windows only: path to the Git Bash executable (`bash.exe`). |
| `CLAUDE_CODE_GLOB_HIDDEN` |  | Set to `false` to exclude dotfiles from results when Claude invokes the Glob tool. |
| `CLAUDE_CODE_GLOB_NO_IGNORE` |  | Set to `false` to make the Glob tool respect `.gitignore` patterns. |
| `CLAUDE_CODE_GLOB_TIMEOUT_SECONDS` |  | Timeout in seconds for Glob tool file discovery. |
| `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` |  | Maximum number of read-only tools and subagents that can execute in parallel (default: 10). |
| `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` | 2.1.212 | Cap on the total number of WebSearch calls one session can make (default: 200). |
| `CLAUDE_CODE_PERFORCE_MODE` |  | Set to `1` to enable Perforce-aware write protection. |
| `CLAUDE_CODE_POWERSHELL_RESPECT_EXECUTION_POLICY` |  | Set to `1` to stop Claude Code from passing `-ExecutionPolicy Bypass` when spawning PowerShell for tool calls, hooks, and status line commands, and respect the machine's effective execution policy instead. |
| `CLAUDE_CODE_SCRIPT_CAPS` |  | JSON object limiting how many times specific scripts may be invoked per session when `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` is set. |
| `CLAUDE_CODE_SHELL` |  | Set the shell Claude Code uses to run Bash tool commands. |
| `CLAUDE_CODE_SHELL_PREFIX` |  | Command prefix that wraps shell commands Claude Code spawns: Bash tool calls, hook commands, status line commands, and stdio MCP server startup commands. |
| `CLAUDE_CODE_USE_NATIVE_FILE_SEARCH` |  | Set to `1` to discover custom commands, subagents, and output styles using Node.js file APIs instead of ripgrep. |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL` |  | Controls the PowerShell tool. |
| `CLAUDE_CODE_WEBFETCH_DEADLINE_MS` | 2.1.268 | Upper bound in milliseconds on how long WebFetch waits for a page to download, including any redirects it follows. |
| `ENABLE_TOOL_SEARCH` | 2.1.221 | Controls MCP tool search. |
| `USE_BUILTIN_RIPGREP` |  | Set to `0` to use system-installed `rg` instead of `rg` included with Claude Code |

## MCP

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_AGENT_SDK_MCP_NO_PREFIX` |  | Set to `1` to skip the `mcp__<server>__` prefix on tool names from SDK-created MCP servers. |
| `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` | 2.1.280 | Maximum length in characters of each MCP tool description and each MCP server's instructions that Claude Code sends to the model (default: 2048). |
| `CLAUDE_CODE_MCP_ALLOWLIST_ENV` |  | Set to `1` to spawn stdio MCP servers with only a safe baseline environment plus the server's configured `env`, instead of inheriting your shell environment |
| `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` | 2.1.212 | Elapsed time in milliseconds before a still-running MCP tool call moves to a background task (default: 120000, or 2 minutes). |
| `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` | 2.1.274 | How long in milliseconds the first turn of a non-interactive session waits for MCP servers that are still connecting, in place of the default first-turn wait. |
| `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` | 2.1.187 | Idle timeout in milliseconds for MCP tool calls. |
| `ENABLE_CLAUDEAI_MCP_SERVERS` |  | Set to `false` to stop Claude Code from fetching claude.ai MCP servers. |
| `MAX_MCP_OUTPUT_TOKENS` |  | Maximum number of tokens allowed in MCP tool responses. |
| `MCP_CLIENT_SECRET` |  | OAuth client secret for MCP servers that require pre-configured credentials. |
| `MCP_CONNECTION_NONBLOCKING` |  | Controls whether startup waits for MCP servers to connect before the first query. |
| `MCP_CONNECT_TIMEOUT_MS` |  | How long blocking MCP startup waits, in milliseconds, for the connection batch before snapshotting the tool list (default: 5000). |
| `MCP_DISCOVERY_CACHE` | 2.1.238 | Turns the MCP discovery cache on or off. |
| `MCP_DISCOVERY_CACHE_MAX_STALE_S` | 2.1.238 | Maximum age, in seconds, of a discovery-cache entry (default: 14400, or 4 hours). |
| `MCP_DISCOVERY_CACHE_STRIKES` | 2.1.238 | At a start where a discovery-cache entry is older than `MCP_DISCOVERY_CACHE_TTL_S`, Claude Code refreshes it in the background. |
| `MCP_PROTOCOL_NEGOTIATION` | 2.1.221 | On the v2 MCP client runtime only, whether Claude Code probes servers for MCP protocol revision 2026-07-28. |
| `MCP_REMOTE_SERVER_CONNECTION_BATCH_SIZE` |  | Maximum number of remote MCP servers (HTTP/SSE) to connect in parallel during startup (default: 20) |
| `MCP_SDK_GENERATION` | 2.1.221 | Pin which MCP client runtime this process connects to MCP servers with: `v1`, built on MCP TypeScript SDK 1.x, or `v2`, built on MCP TypeScript SDK 2.0. |
| `MCP_SERVER_CONNECTION_BATCH_SIZE` |  | Maximum number of local MCP servers (stdio) to connect in parallel during startup (default: 3) |
| `MCP_TIMEOUT` |  | Timeout in milliseconds for MCP server startup (default: 30000, or 30 seconds) |
| `MCP_TOOL_TIMEOUT` | 2.1.203 | Timeout in milliseconds for MCP tool execution (default: 100000000, about 28 hours). |

## Skille, wtyczki i polecenia

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` |  | Set to `1` to disable the skills and workflows included with Claude Code: bundled skills and workflows are removed entirely, while built-in commands like `/init` stay typable but are hidden from the model. |
| `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` |  | Set to `1` to disable automatic registration of the official plugin marketplace. |
| `CLAUDE_CODE_DISABLE_POLICY_SKILLS` |  | Set to `1` to skip loading skills from the system-wide managed skills directory. |
| `CLAUDE_CODE_PLUGIN_CACHE_DIR` |  | Override the plugins root directory. |
| `CLAUDE_CODE_PLUGIN_DIRS` | 2.1.280 | Plugin directories to load for the session, each loaded the way a `--plugin-dir` flag loads it. |
| `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` |  | Timeout in milliseconds for cloning or refreshing a plugin marketplace (default: 120000). |
| `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` |  | Set to `1` to skip the re-clone attempt and keep using the existing marketplace checkout when a marketplace refresh can't reach or authenticate to the remote. |
| `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` |  | Set to `1` to clone GitHub `owner/repo` shorthand sources over HTTPS instead of SSH. |
| `CLAUDE_CODE_PLUGIN_SEED_DIR` |  | Path to one or more read-only plugin seed directories, separated by `:` on Unix or `;` on Windows. |
| `CLAUDE_CODE_SYNC_PLUGIN_INSTALL` |  | Set to `1` in non-interactive mode (the `-p` flag) to wait for plugin installation to complete before the first query. |
| `CLAUDE_CODE_SYNC_PLUGIN_INSTALL_TIMEOUT_MS` |  | Timeout in milliseconds for synchronous plugin installation. |
| `CLAUDE_CODE_SYNC_SKILLS` | 2.1.273 | Set to `1` in non-interactive mode with the `-p` flag to make Claude Code download the skills enabled for your claude.ai account in that run and wait for the list of them, up to `CLAUDE_CODE_SYNC_SKILLS_WAIT_TIMEOUT_MS`, before it runs the… |
| `CLAUDE_CODE_SYNC_SKILLS_INSTALL_TIMEOUT_MS` |  | Timeout in milliseconds for the skills resync that runs mid-session when an app built on the Agent SDK reloads skills (default: 30000). |
| `CLAUDE_CODE_SYNC_SKILLS_WAIT_TIMEOUT_MS` |  | Timeout in milliseconds for the first query to wait for the initial skill list when `CLAUDE_CODE_SYNC_SKILLS` is set (default: 5000). |
| `CLAUDE_DISABLE_ADOPT` | 2.1.195 | Set to `1` to stop in-flight background work instead of carrying it over when you background a session by pressing `←` or with `/background`. |
| `DISABLE_DOCTOR_COMMAND` | 2.1.205 | Set to `1` to hide the `/doctor` setup checkup skill and its `/checkup` alias. |
| `DISABLE_EXTRA_USAGE_COMMAND` |  | Set to `1` to hide the `/usage-credits` command that lets users purchase additional usage beyond rate limits |
| `DISABLE_INSTALL_GITHUB_APP_COMMAND` |  | Set to `1` to hide the `/install-github-app` command. |
| `DISABLE_UPGRADE_COMMAND` |  | Set to `1` to hide the `/upgrade` command |
| `FORCE_AUTOUPDATE_PLUGINS` |  | Set to `1` to force plugin auto-updates even when the main auto-updater is disabled via `DISABLE_AUTOUPDATER` |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` |  | Override the character budget for skill metadata shown to the Skill tool. |

## Uprawnienia i tryby

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_AUTO_MODE_SERVER` | 2.1.281 | Controls whether Claude Code asks the server to review auto mode actions. |
| `CLAUDE_CODE_DISABLE_CFC_PROMPT` | 2.1.257 | Set to `1` to keep the Claude in Chrome browser tools available while omitting the Chrome section of the system prompt and the `/claude-in-chrome` bundled skill. |
| `CLAUDE_CODE_DISABLE_DANGEROUS_RM_TIMEOUT` | 2.1.281 | Set to `1` to turn off the time limit on critical-path removal prompts. |
| `CLAUDE_CODE_DISABLE_PERMISSION_PROMPT_NOTIFY_HOOKS` | 2.1.233 | Set to `1` to stop Claude Code from running your `Notification` hooks for unanswered permission requests in sessions where Claude Code sends them to the Agent SDK's `canUseTool` callback, which is how Claude Desktop and the VS Code extensi… |
| `CLAUDE_CODE_DISABLE_SUBSTITUTION_RM_PROMPT` | 2.1.281 | Set to `1` to turn off the critical-path check for a recursive `rm` whose target is entirely the output of a command substitution, such as `rm -rf "$(pwd)"`. |
| `CLAUDE_CODE_ENABLE_AUTO_MODE` | 2.1.158 | Accepted for compatibility with older releases and has no effect. |
| `CLAUDE_CODE_USER_DIALOG_TIMEOUT_MS` | 2.1.236 | Deadline in milliseconds before Claude Code cancels a dialog it forwards to a remote client such as a Remote Control or SDK host, or the approval dialog for a held cross-session message; permission prompts and `AskUserQuestion` questions u… |

## Bezpieczeństwo i izolacja

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_PROCESS_WRAPPER` | 2.1.210 | Launch the processes Claude Code starts from its own binary, such as the background service that hosts agent view sessions, through a corporate launcher given as an argv prefix like `/opt/corp/launcher`. |
| `CLAUDE_CODE_RESTRICTED` | 2.1.248 | Set to `1` to start the session in restricted mode, the same as passing `--restricted`. |
| `CLAUDE_CODE_SAFE_MODE` |  | Set to `1` to start in safe mode: CLAUDE.md, skills, plugins, hooks, MCP servers, custom commands and agents, output styles, workflows, custom themes, custom keybindings, status line and file-suggestion commands, LSP servers, and auto memo… |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | 2.1.251 | Set to `1` to strip credentials from subprocess environments (Bash tool, hooks, MCP stdio servers): Anthropic and cloud provider credentials, any other variable that Claude Code recognizes as a credential, and credentials embedded in packa… |

## Pamięć i CLAUDE.md

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` |  | Set to `1` to load memory files from directories specified with `--add-dir`. |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` |  | Set to `1` to disable auto memory. |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS` |  | Set to `1` to prevent loading any CLAUDE.md memory files into context, including user, project, and auto memory files |
| `CLAUDE_CODE_TOOL_MEMORY_CGROUP_EXCLUDE` | 2.1.246 | On Linux and WSL, set to a comma-separated list of the kinds of processes Claude Code excludes from the tool memory cap, such as `mcp` or `lsp`. |
| `CLAUDE_CODE_TOOL_MEMORY_LIMIT` | 2.1.246 | On Linux and WSL, set to a size such as `4G` to cap the memory that Bash and PowerShell tool commands can use, and Monitor tool commands on v2.1.246 or later. |

## Instrukcja i tożsamość

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_ATTRIBUTION_HEADER` | 2.1.181 | Set to `0` to omit the attribution block, which carries the client version and a prompt fingerprint, from the start of the system prompt. |
| `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` |  | Set to `1` to remove built-in commit and PR workflow instructions and the git status snapshot from Claude's context. |
| `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT` |  | Set to `1` to use a shorter system prompt and abbreviated tool descriptions on any model. |

## Hooki

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` |  | Override the time budget in milliseconds for SessionEnd hooks. |
| `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` |  | Maximum number of consecutive times a Stop or SubagentStop hook may block the turn from ending before Claude Code overrides it and ends the turn anyway (default: 8). |

## Telemetria i prywatność

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `BETA_TRACING_ENDPOINT` |  | OTLP endpoint for detailed beta tracing: with `ENABLE_BETA_TRACING_DETAILED=1`, logs and traces go there instead of to the configured exporters. |
| `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` |  | Set to `1` to disable the "How is Claude doing?" session quality surveys. |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` |  | Set to any non-empty value, such as `1`, to disable nonessential network traffic: auto-updates, telemetry, error reporting, the `/feedback` command, Claude-drafted feedback, release notes, the PR and MR status badge checks, and availabilit… |
| `CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL` |  | Set to `1` to route the "How is Claude doing?" session quality survey to your own OpenTelemetry collector when Anthropic-bound nonessential traffic is blocked. |
| `CLAUDE_CODE_ENABLE_TELEMETRY` |  | Set to `1` to enable OpenTelemetry data collection for metrics and logging. |
| `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` | 2.1.214 | Maximum length of content-bearing OpenTelemetry attributes (model responses, tool content, system prompts, raw API bodies), truncation marker included, in UTF-16 code units (default: 61440, i.e. |
| `CLAUDE_CODE_OTEL_DIAG_STDERR` | 2.1.179 | Set to `1` to write OpenTelemetry exporter diagnostic errors to stderr. |
| `CLAUDE_CODE_OTEL_FLUSH_TIMEOUT_MS` |  | Timeout in milliseconds for flushing pending OpenTelemetry spans (default: 5000). |
| `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` |  | Interval for refreshing dynamic OpenTelemetry headers in milliseconds (default: 1740000 / 29 minutes). |
| `CLAUDE_CODE_OTEL_SHUTDOWN_TIMEOUT_MS` |  | Timeout in milliseconds for the OpenTelemetry exporter to finish on shutdown (default: 2000). |
| `CLAUDE_CODE_PROPAGATE_TRACEPARENT` | 2.1.152 | Set to `1` to propagate W3C trace context when `ANTHROPIC_BASE_URL` points at a custom proxy. |
| `CLAUDE_CODE_SEND_FEEDBACK` |  | Set to `0` to turn off Claude-drafted feedback for a session. |
| `DISABLE_COST_WARNINGS` |  | Set to `1` to disable cost warning messages |
| `DISABLE_ERROR_REPORTING` |  | Set to any non-empty value, such as `1`, to opt out of error reporting. |
| `DISABLE_FEEDBACK_COMMAND` | 2.1.212 | Set to `1` to disable the `/feedback` command and Claude-drafted feedback. |
| `DISABLE_GROWTHBOOK` |  | Set to `1` or `true` to disable GrowthBook feature-flag fetching and use code defaults for every flag. |
| `DISABLE_TELEMETRY` |  | Set to any non-empty value, such as `1`, to opt out of telemetry. |
| `DO_NOT_TRACK` |  | Set to `1` to opt out of telemetry, with the same effect as `DISABLE_TELEMETRY`, including on feature-flag fetching. |
| `ENABLE_BETA_TRACING_DETAILED` |  | Set to `1`, together with `BETA_TRACING_ENDPOINT`, to turn on detailed beta tracing, which adds content-bearing span attributes and the `claude_code.hook` span. |
| `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT` | 2.1.214 | Standard OpenTelemetry SDK limit on attribute value length. |
| `OTEL_LOG_ASSISTANT_RESPONSES` | 2.1.193 | Set to `1` to include the model's response text on `assistant_response` OpenTelemetry log events. |
| `OTEL_LOG_RAW_API_BODIES` |  | Emit Anthropic Messages API request and response JSON as `api_request_body` / `api_response_body` log events. |
| `OTEL_LOG_TOOL_CONTENT` |  | Set to `1` to include tool content in the `tool.output` OpenTelemetry span event. |
| `OTEL_LOG_TOOL_DETAILS` |  | Set to `1` to include tool input arguments; MCP server names; user-authored workflow names; raw error strings on tool failures; the refusal `category` on `api_refusal` events; real agent, skill, plugin, and MCP server names on cost and tok… |
| `OTEL_LOG_USER_PROMPTS` |  | Set to `1` to include user prompt text in OpenTelemetry traces and logs. |
| `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` |  | Set to `false` to exclude account UUID from metrics attributes (default: included). |
| `OTEL_METRICS_INCLUDE_ENTRYPOINT` | 2.1.152 | Set to `true` to include the session entrypoint in metrics attributes (default: excluded). |
| `OTEL_METRICS_INCLUDE_REPOSITORY` | 2.1.269 | Set to `true` to tag OpenTelemetry metrics and events with `vcs.*` attributes identifying the session's repository (default: excluded). |
| `OTEL_METRICS_INCLUDE_RESOURCE_ATTRIBUTES` | 2.1.161 | As of v2.1.161, Claude Code attaches `OTEL_RESOURCE_ATTRIBUTES` keys to metric datapoint labels. |
| `OTEL_METRICS_INCLUDE_SESSION_ID` |  | Set to `false` to exclude session ID from metrics attributes (default: included). |
| `OTEL_METRICS_INCLUDE_VERSION` |  | Set to `true` to include Claude Code version in metrics attributes (default: excluded). |

## Sieć, proxy i niezawodność

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `API_FORCE_IDLE_TIMEOUT` |  | Override the 5-minute body idle timeout that aborts a streaming model response when no bytes arrive. |
| `API_TIMEOUT_MS` |  | Timeout for API requests in milliseconds (default: 600000, or 10 minutes; maximum: 2147483647). |
| `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` | 2.1.210 | Timeout in milliseconds for the byte-level streaming idle watchdog; when set, it takes precedence over `CLAUDE_STREAM_IDLE_TIMEOUT_MS` for that watchdog and leaves the event-level watchdog unchanged. |
| `CLAUDE_CODE_AUTO_CONNECT_IDE` |  | Override automatic IDE connection. |
| `CLAUDE_CODE_CERT_STORE` |  | Comma-separated list of CA certificate sources for TLS connections. |
| `CLAUDE_CODE_CLIENT_CERT` |  | Path to client certificate file for mTLS authentication |
| `CLAUDE_CODE_CLIENT_KEY` |  | Path to client private key file for mTLS authentication |
| `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE` |  | Passphrase for encrypted CLAUDE\_CODE\_CLIENT\_KEY (optional) |
| `CLAUDE_CODE_CONNECT_TIMEOUT_MS` | 2.1.186 | Removed in v2.1.186 and now a no-op. |
| `CLAUDE_CODE_DISABLE_MTLS_RELOAD_ON_STALE_CONNECTION` | 2.1.232 | Set to `1` to stop Claude Code from re-reading the mTLS client certificate and key when an API request fails with a connection-level error, such as a connection reset or a TLS handshake error. |
| `CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK` |  | Set to `1` to disable the non-streaming fallback when a streaming request fails mid-stream. |
| `CLAUDE_CODE_MAX_RETRIES` | 2.1.186 | Override the number of times to retry failed API requests (default: 10). |
| `CLAUDE_CODE_PROXY_RESOLVES_HOSTS` |  | Set to `1` to allow the proxy to perform DNS resolution instead of the caller. |
| `CLAUDE_CODE_RETRY_WATCHDOG` | 2.1.239 | Set to `1` for unattended sessions such as eval harnesses, CI jobs, or remote workers. |
| `CLAUDE_ENABLE_BYTE_WATCHDOG` | 2.1.222 | Set to `1` to force-enable the byte-level streaming idle watchdog, or set to `0` to force-disable it. |
| `CLAUDE_ENABLE_BYTE_WATCHDOG_BEDROCK` |  | Set to `1` to enable the byte-level streaming idle watchdog on Amazon Bedrock `vnd.amazon.eventstream` responses, which also enables the first-byte deadline on Bedrock streaming requests. |
| `CLAUDE_ENABLE_STREAM_WATCHDOG` | 2.1.196 | Set to `0` to force-disable the event-level streaming idle watchdog, or set to `1` to force-enable it. |
| `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS` | 2.1.242 | Deadline in milliseconds for the first response byte of a streaming request, on the connections where the first-byte deadline runs. |
| `CLAUDE_STREAM_IDLE_TIMEOUT_MS` |  | Timeout in milliseconds before the event- and byte-level streaming idle watchdogs close a stalled connection. |
| `HTTPS_PROXY` |  | Specify HTTPS proxy server for network connections |
| `HTTP_PROXY` |  | Specify HTTP proxy server for network connections |
| `NO_PROXY` |  | List of domains and IPs to which requests will be directly issued, bypassing proxy |

## Aktualizacje i instalacja

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL` |  | Set to `1` to skip auto-installation of IDE extensions. |
| `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE` |  | Set to `1` to let Claude Code run your package manager's upgrade command in the background when a new version is available. |
| `DISABLE_AUTOUPDATER` |  | Set to `1` to disable automatic background updates. |
| `DISABLE_INSTALLATION_CHECKS` |  | Set to `1` to disable installation warnings. |
| `DISABLE_UPDATES` |  | Set to `1` to block all updates including manual `claude update` and `claude install`. |

## Ustawienia i zarządzanie

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_DISABLE_ADMIN_ENV_UNION` | 2.1.223 | Set to `1` to stop Claude Code from merging managed settings `env` blocks per key across admin sources, so only the highest-priority source's whole `env` block applies, as before v2.1.223. |
| `OTEL_LOG_MANAGED_SETTINGS` | 2.1.274 | Set to `1` to add the redacted managed settings, and a SHA-256 digest of the settings before redaction, to `managed_settings_resolved` OpenTelemetry log events. |

## Diagnostyka i logi

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_CODE_DEBUG_LOGS_DIR` |  | Override the debug log file path. |
| `CLAUDE_CODE_DEBUG_LOG_LEVEL` |  | Minimum log level written to the debug log file. |
| `DEBUG` |  | Set to `1` to enable debug mode, equivalent to launching with `--debug`. |

## Interfejs terminala i IDE

| Zmienna | Wersja | Opis (dokumentacja) |
|---|---|---|
| `CLAUDE_AX_PREPARK_MS` | 2.1.287 | In screen reader mode, how many milliseconds Claude Code waits before it writes a new or changed line. |
| `CLAUDE_AX_SCREEN_READER` | 2.1.181 | Set to `1` to render screen-reader friendly output: flat text without decorative borders or animations. |
| `CLAUDE_AX_STARTUP_QUIET_MS` | 2.1.217 | In screen reader mode, how many milliseconds Claude Code holds the first interface render after the startup confirmation line, so your screen reader can speak the line in full before new output interrupts it. |
| `CLAUDE_CLIENT_PRESENCE_FILE` | 2.1.181 | Path to a file that an external tool, such as a screen-lock listener, creates when you unlock your screen and deletes when you lock it. |
| `CLAUDE_CODE_ACCESSIBILITY` |  | Set to `1` to keep the native terminal cursor visible and disable the inverted-text cursor indicator. |
| `CLAUDE_CODE_ALT_SCREEN_FULL_REPAINT` |  | Set to `1` to repaint the entire screen on every frame in fullscreen rendering instead of sending incremental updates. |
| `CLAUDE_CODE_BASH_EDIT_DIFF` | 2.1.269 | Set to `0` to turn off the diff of the files that changed while a Bash command ran, or `1` to record it in every permission mode. |
| `CLAUDE_CODE_BS_AS_CTRL_BACKSPACE` |  | Set to `0` to make Claude Code read the `0x08` byte, also written `^H`, as plain Backspace, or `1` to read it as Ctrl+Backspace. |
| `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN` |  | Set to `1` to disable fullscreen rendering and use the classic main-screen renderer. |
| `CLAUDE_CODE_DISABLE_BEDROCK_CONTENT_TYPE_DEFAULT` | 2.1.239 | Set to `1` to stop Claude Code from treating an Amazon Bedrock streaming response with a missing or empty `Content-Type` header as Amazon Bedrock's binary event stream. |
| `CLAUDE_CODE_DISABLE_BEDROCK_CONTENT_TYPE_GUARD` | 2.1.208 | Set to `1` to skip the check that an Amazon Bedrock streaming response carries the `application/vnd.amazon.eventstream` content-type. |
| `CLAUDE_CODE_DISABLE_MOUSE` |  | Set to `1` to disable mouse tracking in fullscreen rendering. |
| `CLAUDE_CODE_DISABLE_MOUSE_CLICKS` | 2.1.195 | Set to `1` to disable click, drag, and hover handling in fullscreen rendering while keeping mouse-wheel scrolling. |
| `CLAUDE_CODE_DISABLE_NOTIFICATION_PRESENCE_CHECK` | 2.1.193 | Set to `1` to send the `PushNotification` tool's desktop notification even while you are typing in or focused on the terminal. |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` |  | Set to `1` to disable automatic terminal title updates based on conversation context. |
| `CLAUDE_CODE_DISABLE_VIRTUAL_SCROLL` |  | Set to `1` to disable virtual scrolling in fullscreen rendering and render every message in the transcript. |
| `CLAUDE_CODE_FORCE_STRIKETHROUGH` | 2.1.186 | Set to `1` to force strikethrough rendering for `~~text~~` in Claude's responses when your terminal supports it but is not auto-detected, such as over SSH without `TERM_PROGRAM` forwarded. |
| `CLAUDE_CODE_HIDE_CWD` |  | Set to `1` to hide the working directory in the startup logo. |
| `CLAUDE_CODE_IDE_HOST_OVERRIDE` |  | Override the host address used to connect to the IDE extension. |
| `CLAUDE_CODE_IDE_SKIP_VALID_CHECK` |  | Set to `1` to skip validation of IDE lockfile entries during connection. |
| `CLAUDE_CODE_NATIVE_CURSOR` |  | Set to `1` to show the terminal's own cursor at the input caret instead of a drawn block. |
| `CLAUDE_CODE_NEW_INIT` |  | Set to `1` to make `/init` run an interactive setup flow. |
| `CLAUDE_CODE_NO_FLICKER` |  | Set to `1` to enable fullscreen rendering, a research preview that reduces flicker and keeps memory flat in long conversations. |
| `CLAUDE_CODE_SCROLL_SPEED` |  | Set the mouse wheel scroll multiplier in fullscreen rendering. |
| `CLAUDE_CODE_SYNTAX_HIGHLIGHT` |  | Set to `false` to disable syntax highlighting in diff output. |
| `CLAUDE_CODE_TMUX_TRUECOLOR` |  | Set to any non-empty value, such as `1`, to allow 24-bit truecolor output inside tmux. |
| `FORCE_HYPERLINK` |  | Set to `1` to enable clickable OSC 8 hyperlinks when your terminal supports them but isn't auto-detected, or `0` to disable them. |
