# Hierarchia i scalanie ustawień — reguły szczegółowe

Źródła: `cc:settings`, `cc:settings-reference`, `cc:permissions` („Project allow rules and
workspace trust”), `cc:agent-sdk/claude-code-features`, `cc:env-vars` („Precedence”),
`cc:managed-settings`. Stan dokumentacji: 01.10.2026 (CLI 2.1.287 w dokumentacji,
2.1.286 sprawdzone próbą).

## 1. Pliki i ich położenie

| Zakres | Plik | Kto tworzy | Uwagi |
|---|---|---|---|
| użytkownik | `~/.claude/settings.json` (albo `$CLAUDE_CONFIG_DIR/settings.json`) | Ty lub `/config`, `/model` | zapisują tu polecenia sesji |
| projekt wspólny | `.claude/settings.json` w katalogu roboczym startu | zespół (commit) | czytany z **głównego katalogu roboczego** sesji; po `/cd` z nowego |
| projekt lokalny | `.claude/settings.local.json` | Ty lub CLI | od 2.1.211 w korzeniu repozytorium (wyjątki: poza gitem, korzeń = katalog domowy, Windows, cudzy właściciel `.git`) |
| zarządzane | `/etc/claude-code/managed-settings.json` (Linux), `managed-settings.d/*.json`, MDM, rejestr, serwer | administrator | szczegóły: pakiet `zarzadzanie-flota` |
| sesja | `--settings <plik lub JSON>` | wywołujący | plik zwykły ≤ 2 MiB |
| globalna konfiguracja | `~/.claude.json` | CLI | stan, MCP `user`/`local`, zaufanie folderów, 12 kluczy `Global config` |

Kopie zapasowe uszkodzonego `~/.claude.json`: `~/.claude/backups/.claude.json.corrupted.<znacznik>`,
pięć ostatnich `.claude.json.backup.<znacznik>` do ręcznego przywrócenia.

## 2. Drabina pierwszeństwa

1. zarządzane (najwyższe; między źródłami zarządzanymi wygrywa jedno — patrz `zarzadzanie-flota`),
2. wiersz poleceń (`--settings`, flagi kluczy),
3. `.claude/settings.local.json`,
4. `.claude/settings.json`,
5. `~/.claude/settings.json`.

Zmienne środowiskowe rozstrzyga się parami (wpis klucza: pole „Per-session overrides”).
Przykłady par:

| Para | Zwycięzca |
|---|---|
| `ANTHROPIC_MODEL` vs `model` z pliku | zmienna |
| `--model` vs `ANTHROPIC_MODEL` | flaga |
| `ANTHROPIC_DEFAULT_MODEL` vs `model` | klucz (zmienna tylko gdy klucza brak) |
| `CLAUDE_CODE_EFFORT_LEVEL` vs `--effort`, `/effort` | zmienna |
| `CLAUDE_CODE_PROMPT_CACHE_TTL` vs `promptCacheTtl` | zmienna; nad obiema `FORCE_PROMPT_CACHING_5M` |
| `--permission-mode` vs `permissions.defaultMode` | flaga |
| zmienna w powłoce vs ta sama w `env` pliku | w większości sesji wartość z `env` (CLI wpisuje ją do środowiska procesu) |

W bloku `env` można ustawić zmienną, ale nie można jej usunąć. Zmienną, której nie
kontrolujesz (np. `CLAUDE_CODE_USE_VERTEX` z profilu powłoki), neutralizuje pusta wartość:
`"CLAUDE_CODE_USE_VERTEX": ""`.

## 3. Scalanie

- skalary — wygrywa najwyższy poziom;
- listy — suma ze wszystkich poziomów (`permissions.*`, `additionalDirectories`, hooki,
  `allowedMcpServers`, `deniedMcpServers`, `sandbox.filesystem.*`, `sandbox.network.*Domains`…);
- wyjątki: `fallbackModel` (całość z najwyższego), `modelPicker` (managed > `--settings` >
  user), `availableModels` (managed stosowane w całości, chyba że host z
  `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST`), `modelSettings` (model po modelu);
- uprawnienia — kolejność **deny → ask → allow**, pierwszy trafiony wygrywa, szczegółowość
  reguły nie zmienia kolejności; `allowManagedPermissionRulesOnly` w managed odcina reguły
  wszystkich innych źródeł;
- hooki — suma; identyczny handler z dwóch plików uruchamia się raz; kopia we wtyczce lub
  skillu zostaje osobna.

## 4. Wyjątki bezpieczeństwa (wartość restrykcyjna z niższego poziomu wygrywa)

| Klucz | Honorowana wartość | Skąd |
|---|---|---|
| `disableClaudeAiConnectors` | `true` | dowolne źródło |
| `enableArtifact` / `disableArtifact` | `false` / `true` | dowolne źródło (≥2.1.242) |
| `isolatePeerMachines` | `true` | dowolne źródło |
| `remoteControlAtStartup` | `false` | `.claude/settings.json`, `.claude/settings.local.json` |
| `crossSessionInbound` | ostrzejsza na drabinie `accept` < `hold` < `refuse` | pliki projektu |
| `useAutoModeDuringPlan` | `false` | managed, `--settings`, user, local (nie wspólny projekt) |
| `syncClaudeAiSkills`, `syncClaudeAiPlugins` | `false` | managed, `--settings`, user, local (nie wspólny projekt) |
| `maxEffortLevel` | najniższy sufit | wszystkie źródła, także `--settings` (≥2.1.267) |

## 5. Klucze i wartości, które z danego pliku nie działają

- zasięg `Managed` — tylko ustawienia zarządzane; `--settings` ich nie ustawi;
- zasięg `Global config` — tylko `~/.claude.json`;
- zasięg `User or managed` — nie z plików projektu (wspólnego i lokalnego);
- zasięg `User, local, or managed` — nie ze wspólnego pliku projektu;
- `permissions.defaultMode: "auto"` i `"bypassPermissions"` — nie z plików projektu
  i lokalnych (sesja startuje wtedy w trybie wbudowanym, a nie w trybie z pliku użytkownika);
- `autoMode` — klasyfikator nie czyta go z plików projektu;
- `env` w plikach projektu/lokalnym ignoruje: `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`,
  `HOME`, `TMPDIR`, `TMP`, `TEMP`, `XDG_*`, `OTEL_LOG_RAW_API_BODIES`,
  `ENABLE_BETA_TRACING_DETAILED`, `BETA_TRACING_ENDPOINT`, `CLAUDE_CODE_ENABLE_TELEMETRY`,
  zmienne eksporterów OTel (`OTEL_*_EXPORTER`, `OTEL_EXPORTER_OTLP_*_{ENDPOINT,HEADERS,PROTOCOL,CERTIFICATE,CLIENT_KEY,INSECURE}`,
  `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_*`, `OTEL_LOG_ASSISTANT_RESPONSES`),
  `CLAUDE_CODE_PROCESS_WRAPPER`, `CLAUDE_CODE_SYNC_SKILLS`, `CLAUDE_CODE_SYNC_PLUGINS`,
  `CLAUDE_CODE_PLUGIN_CACHE_DIR`, `CLAUDE_CODE_PLUGIN_SEED_DIR` (wartości wyłączające
  telemetrię, np. `none`, `0`, nadal działają; ≥2.1.282 dla grupy OTel);
- `env` w **każdym** pliku ignoruje: `CLAUDE_CODE_PROJECT_DIR_NAME`, `CLAUDE_CODE_RESTRICTED`,
  `CLAUDE_CODE_REMOTE`, `CLAUDE_CODE_ACCOUNT_UUID`, `CLAUDE_CODE_MESSAGING_SOCKET`,
  `CLAUDE_CODE_MESSAGING_TOKEN`, `CLAUDE_CODE_DISABLE_POWERSHELL_CMD_RM_DENY`,
  `CLAUDE_CODE_DISABLE_DANGEROUS_RM_TIMEOUT`, `CLAUDE_CODE_DISABLE_SUBSTITUTION_RM_PROMPT`
  — te trzeba podać w środowisku procesu.

Walidator `waliduj_ustawienia.py` zgłasza każdy z tych przypadków.

## 6. Zaufanie folderu (workspace trust)

Zaufanie przypisuje się do korzenia repozytorium (w worktree — do głównego checkoutu),
poza repozytorium do katalogu startu (obejmuje podkatalogi poza zagnieżdżonymi
repozytoriami); w katalogu domowym tylko na czas sesji.

| Treść z repozytorium | Zaufany tylko folder nadrzędny | `-p`/SDK, folder niezaufany |
|---|---|---|
| hooki w plikach ustawień, `env`, `apiKeyHelper`, hooki i `allowed-tools` skilli projektu | używane | **używane** |
| `permissions.allow`, `additionalDirectories` | po akceptacji okna | **pomijane**, ostrzeżenie na stderr |
| hooki we frontmatterze podagentów projektu, wtyczka `@skills-dir` projektu, `extraKnownMarketplaces` | pomijane | pomijane |
| `mcpServers` w frontmatterze podagenta | pomijane | pomijane |
| serwery z `.mcp.json` | pytanie przed połączeniem | łączone bez pytania (SDK tylko z `settingSources` zawierającym projekt) |
| `headersHelper` serwera z `.mcp.json` | po akceptacji okna | nie uruchamiany; tylko statyczne `headers` |

Próba (CLI 2.1.286, atrapa API): projekt z `allow: ["Bash(touch *)"]` i hookiem
`PreToolUse` w `-p --permission-mode dontAsk` — hook się wykonał, reguła allow została
pominięta z komunikatem „Ignoring 1 permissions.allow entry from .claude/settings.json:
this workspace has not been trusted…”, a `touch` odrzucony.

Plik lokalny `.claude/settings.local.json` normalnie omija zaufanie, ale gdy jest
śledzony w gicie albo `.claude` jest dowiązaniem — traktowany jest jak plik repozytorium.

## 7. `--setting-sources` i czego nie odcina

`--setting-sources user,project,local` wybiera, które pliki czytać; `""` = żaden.
Niezależnie od tej flagi CLI czyta:

| Wejście | Jak wyłączyć |
|---|---|
| ustawienia zarządzane (plik, MDM, serwer — przy kwalifikującym poświadczeniu) | usunąć plik/profil; serwerowych nie wyłączysz izolacją plików |
| `~/.claude.json` | inny `CLAUDE_CONFIG_DIR` |
| pamięć automatyczna `~/.claude/projects/<projekt>/memory/` | `autoMemoryEnabled: false` lub `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` |
| konektory MCP claude.ai (przy logowaniu claude.ai) | `--strict-mcp-config`, `disableClaudeAiConnectors: true`, `ENABLE_CLAUDEAI_MCP_SERVERS=false` |
| wpisy `deny` i `mask` z `sandbox.credentials` w `~/.claude/settings.json` | usunąć z pliku |
| wtyczki wbudowane (`…@builtin`, widoczne w `system/init.plugins`) | — (próba 2.1.286: obecne także przy `--setting-sources ""`) |

## 8. Kiedy zmiana działa

- Przeładowywane w trakcie sesji: uprawnienia, hooki, `apiKeyHelper`, `env` (nowe i zmienione wartości), pliki utworzone w trakcie w istniejącym katalogu; zdarzenie `ConfigChange` dla każdej zmiany pliku.
- Czytane tylko przy starcie: `model`, `effortLevel`, `modelSettings`, zmienne OTel, `requiredMinimumVersion` i inne klucze administracyjne; usunięcie zmiennej z `env`.
- Ustawienia zarządzane z MDM i serwera docierają według harmonogramu dostarczania, nie przy zapisie.

## 9. Sesje w chmurze

Czytają tylko wspólny `.claude/settings.json` (przy jednym repozytorium; przy wielu tylko
`enabledPlugins` i `extraKnownMarketplaces`) oraz ustawienia serwerowe. Plik użytkownika,
lokalny i zarządzany z urządzenia do chmury nie trafiają; `dontAsk` i `bypassPermissions`
z plików są w chmurze ignorowane.

## 10. Diagnoza „ustawienie nie działa”

1. `/status` → „Setting sources” (które pliki wczytane; w nawiasie źródło zarządzane).
2. `claude doctor` → „Invalid settings” (pominięte wpisy z powodem).
3. Wyższy poziom ustawia ten sam klucz? (`warstwy_ustawien.py`).
4. Zasięg klucza pozwala na ten plik? (`szukaj.py <klucz> --pelny`).
5. Flaga lub zmienna nadpisuje klucz? (pole „nadpisania”).
6. Wyjątek bezpieczeństwa trzyma wartość restrykcyjną?
7. Folder niezaufany (allow z projektu pominięte)?
8. Klucz czytany tylko przy starcie — uruchom sesję ponownie.
