# Osadzanie Claude Code CLI w produkcie wielodzierżawnym

Źródła: `cc:agent-sdk/hosting`, `cc:agent-sdk/secure-deployment`,
`cc:agent-sdk/claude-code-features`, `cc:sessions`, `cc:headless`, macierz pełna CLI
i analiza CLI Danaco Nexus (wnioski F1–F18, N1–N15), próby 2.1.286.

## 1. Model procesu

Jedna sesja = jeden proces `claude` (SDK również uruchamia binarkę). Stan na dysku:
transkrypty (`<config>/projects/`), CLAUDE.md, pliki katalogu roboczego — nie przetrwają
restartu kontenera bez trwałego wolumenu lub `SessionStore` (SDK).

## 2. Izolacja dzierżawców — minimum

| Element | Ustawienie |
|---|---|
| pliki konfiguracji | `--setting-sources ""` (SDK `settingSources: []`) |
| `~/.claude.json`, transkrypty, pamięć | `CLAUDE_CONFIG_DIR=<dzierżawca>`, `CLAUDE_CODE_PROJECT_DIR_NAME=<dzierżawca>` |
| pamięć automatyczna | `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` (nie odcina jej `--setting-sources`) |
| katalog roboczy | osobny `cwd` na dzierżawcę/rozmowę |
| sieć | reguły wyjścia per dzierżawca w proxy (IP, poświadczenia, lista domen) |
| poświadczenia | poza zasięgiem narzędzi (`apiKeyHelper`, deskryptor pliku `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR` — nieopisany w `cc:env-vars`, proxy wstrzykujące); `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` |
| ustawienia serwerowe organizacji | pobierane przy kwalifikującym poświadczeniu niezależnie od izolacji plików — kontroluj `claude doctor` |

## 3. Kontrola sterowania przez klienta

| Ryzyko | Zamknięcie |
|---|---|
| `/effort max`, `/config model=…`, `/fast on`, `/mcp disable …`, `/goal`, skille Anthropic (`/simplify`, `/batch`, `/design`) wpisane przez klienta | `--disable-slash-commands` (+ `disableBundledSkills`, `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`) |
| klasyfikator auto „przypadkiem” | jawny `--permission-mode`, `disableAutoMode: "disable"` |
| droższy model / izolacja podagenta | deny `Agent(model:*)`, `Agent(isolation:*)`, `availableModels`, `maxEffortLevel` |
| workflowy (słowo `ultracode`) | `disableWorkflows`, `workflowKeywordTriggerEnabled: false` |
| publikacja na claude.ai, Remote Control, wiadomości między sesjami | `enableArtifact: false`, `disableRemoteControl`, `crossSessionInbound: "refuse"`, `disableAgentView` |
| konektory i wtyczki z konta | `disableClaudeAiConnectors`, `syncClaudeAiSkills/Plugins: false`, `--strict-mcp-config` |
| fast mode, doradca | `CLAUDE_CODE_DISABLE_FAST_MODE=1`, `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` |

## 4. Instrukcja i cache

Instrukcja w pliku (`--system-prompt-file`), znacznik `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__`
(część stała wspólna dla rozmów konta, część zmienna per rozmowa), `--system-prompt-snapshot off`
(zmiany docierają do trwających rozmów; identyczna treść — trafienie w cache),
`--append-subagent-system-prompt-file` dla podagentów. Przyklejanie rozmowy do konta przy
rotacji kont (cache nie jest dzielony między organizacjami). Szczegóły:
`model-cache-i-koszty`.

## 5. Narzędzia produktu

Serwer MCP produktu (`--mcp-config` + `--strict-mcp-config`, `allowedMcpServers`):
instrukcje serwera (limit 2048 → `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH`), kilka narzędzi
rdzenia z `alwaysLoad`, `maxResultSizeChars` dla długich wyników, narzędzie zgody dla
`--permission-prompt-tool`, hooki `mcp_tool` dla strażników (poza `SessionStart`).
Bramka startu: `init.mcp_servers[].status == "connected"`.

## 6. Cykl przebiegu

1. Zbuduj polecenie w całości przy każdym przebiegu (nowym i wznawianym).
2. Uruchom z zamkniętym stdin (tryb jednorazowy) albo stream-json (rozmowa).
3. Bramka `init` → przerwij przebieg przy brakującym serwerze/wtyczce.
4. Obsłuż `api_retry`, `permission_denied`, `result`; zapisz `usage` (z polami cache).
5. Anulowanie: `interrupt` → limit czasu → SIGTERM do grupy procesów.
6. Retencja: `cleanupPeriodDays` + usuwanie `projects/<dzierżawca>/<sesja>.jsonl` przy
   usunięciu rozmowy, całego `projects/<dzierżawca>` przy usunięciu konta (RODO).

## 7. Lista kontrolna wdrożenia produktu

- [ ] przypięta wersja CLI (`DISABLE_AUTOUPDATER=1`), testy każdej nowej wersji na atrapie;
- [ ] profil `--settings` wygenerowany i przyjęty przez `claude doctor` tej wersji;
- [ ] `--setting-sources ""`, `--strict-mcp-config`, `--disable-slash-commands`, jawny tryb;
- [ ] `CLAUDE_CONFIG_DIR` + `CLAUDE_CODE_PROJECT_DIR_NAME` na dzierżawcę, pamięć wyłączona;
- [ ] izolacja procesu i sieci (pakiet `piaskownica-i-izolacja`);
- [ ] bramka `init`, obsługa `interrupt`, rejestracja `usage` i odmów;
- [ ] OpenTelemetry bez treści promptów (pakiet `model-cache-i-koszty`);
- [ ] lista kontrolna bezpieczeństwa (pakiet `bezpieczenstwo-wdrozenia`).
