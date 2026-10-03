# Marketplace, wersje, aktualizacje i polityki organizacji

Źródła: `cc:plugins/marketplace-reference`, `cc:plugins/create-marketplace`,
`cc:plugins/host-marketplace`, `cc:plugins/loading`, `cc:plugins/cli-reference`,
`cc:plugins/org`, `cc:plugins/install`, `cc:plugins/security`, `cc:plugins/publish`.

## 1. Polecenia `claude plugin`

| Polecenie | Uwagi |
|---|---|
| `init <nazwa>` | szkielet w `~/.claude/skills/<nazwa>/` (`@skills-dir`) |
| `validate <ścieżka> [--strict] [--json]` | manifest wtyczki/marketplace albo katalog skilli/agentów/poleceń |
| `install|i <nazwa[@marketplace]> [--scope user|project|local] [--config K=V]` | `@marketplace` odświeża katalog przed instalacją |
| `uninstall`, `enable`, `disable`, `update`, `prune` | `disable` = wyłączenie bez usuwania |
| `list [--json]`, `details <nazwa>` | koszt: stały (lista) i przy wywołaniu |
| `configure <wtyczka> [--values-stdin]` | opcje `userConfig` |
| `eval [cel]`, `eval init` | ewaluacja (model, ≥2.1.269) |
| `tag` | znaczniki wersji |
| `marketplace add|list|remove|update` | `add` przyjmuje `owner/repo[@ref]`, URL git, URL pliku, ścieżkę |

## 2. Źródła marketplace

| Typ | Pola | Uwagi |
|---|---|---|
| `github` | `repo`, `ref`, `path`, `sparsePaths` | `path` domyślnie `.claude-plugin/marketplace.json` |
| `git` | `url`, `ref`, `path`, `sparsePaths` | dowolny serwer git |
| `url` | `url`, `headers`, `headersHelper` | tylko plik — wtyczki muszą mieć źródła obiektowe |
| `file`, `directory` | `path` | lokalne; bez odświeżania |
| `settings` | `name`, `plugins`, `owner` | marketplace zdefiniowany w ustawieniach |
| `hostPattern`, `pathPattern`, `skills-dir` | — | tylko w listach polityk |

## 3. Wersje i aktualizacje

Wersja = `version` z manifestu > `version` wpisu > źródło (SHA 12 znaków dla git,
skrót SHA-256 dla archiwum, SHA katalogu w marketplace git, `unknown` dla lokalnych i npm).
Wersja nazywa katalog pamięci podręcznej; `update` pomija wtyczkę o niezmienionej wersji.
Wtyczka z lokalnego katalogu ładuje się „w miejscu” przy każdym starcie. Autoaktualizacja:
w sesji interaktywnej po pierwszej wiadomości (losowo do 10 min), nowe wersje od następnego
startu (`/reload-plugins` wcześniej). Wyłączenie: `DISABLE_AUTOUPDATER=1` (także CLI);
CLI przypięte, wtyczki aktualne: `DISABLE_AUTOUPDATER=1` + `FORCE_AUTOUPDATE_PLUGINS=1`;
bez sieci: `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` (wyłącza też autoaktualizację wtyczek).
Usunięcie wtyczek z marketplace u użytkowników: `forceRemoveDeletedPlugins: true`;
zmiana nazwy: `renames`.

## 4. Polityki organizacji (managed)

| Klucz | Skutek | Czego nie robi |
|---|---|---|
| `strictKnownMarketplaces` (alias `allowedMarketplaces`) | lista dozwolonych źródeł; `[]` blokuje wszystko (także oficjalny) | nie rejestruje marketplace, nie filtruje wpisów, nie blokuje `--plugin-dir` |
| `blockedMarketplaces` | lista zakazanych (sprawdzana przed dozwolonymi) | nie blokuje już zarejestrowanych z innego źródła |
| `enabledPlugins` | `true` wymusza, `false` blokuje i ukrywa | nie instaluje bez zarejestrowanego marketplace |
| `extraKnownMarketplaces` (alias `additionalMarketplaces`) | rejestruje marketplace | — |
| `disableSideloadFlags` | odrzuca `--plugin-dir`, `--plugin-url`, `--agents`, `plugins` SDK, `--mcp-config` (poza SDK), `CLAUDE_CODE_PLUGIN_DIRS` | nie ogranicza `.mcp.json` |
| `disableCommandPluginSources` | blokuje źródła `command` (domyślnie = `allowManagedHooksOnly`) | — |
| `strictPluginOnlyCustomization` | skille/agenci/hooki/MCP tylko z wtyczek, managed i wbudowanych (`true` lub lista typów) | — |
| `syncClaudeAiPlugins: false` | bez wtyczek z konta claude.ai (≥2.1.273) | pojedynczo: `"<nazwa>@synced": false` |
| `pluginSuggestionMarketplaces`, `pluginTrustMessage` | podpowiedzi instalacji, dopisek do ostrzeżenia | — |
| `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL=1` | bez automatycznej rejestracji oficjalnego marketplace | nie usuwa zarejestrowanego |

Wpisy list: `{"source":"github","repo":"org/*"}` (`owner/*` dozwolone tylko w politykach),
`{"source":"hostPattern","hostPattern":"<regex>"}`, `{"source":"pathPattern","pathPattern":"<regex>"}`.
Aliasy kluczy wymagają ≥2.1.232 — w mieszanej flocie używaj nazw kanonicznych.

## 5. Seed dla CI i kontenerów

Budowa obrazu: `CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/seed claude plugin marketplace add …`
i `… plugin install …`; obraz: `CLAUDE_CODE_PLUGIN_SEED_DIR=/opt/seed` (kilka po `:`),
`enabledPlugins` w managed lub repozytorium. Seed jest tylko do odczytu, autoaktualizacja
wyłączona, wpis seed nadpisuje wpis użytkownika o tej samej nazwie; polityki dotyczą
źródła, z którego zbudowano seed. Sprawdzenie: `claude -p --output-format stream-json
--verbose` → `init.plugins[].path` pod katalogiem seed. Prywatne repozytoria w CI:
pomocnik poświadczeń gita (`gh auth setup-git` z `GH_TOKEN`).

## 6. Bezpieczeństwo wtyczek

Wtyczka wykonuje kod (hooki, MCP, `bin/`, LSP) z uprawnieniami użytkownika i poza
piaskownicą Bash. Instaluj z zaufanych źródeł, przypinaj `sha` dla `github`/`url`,
`sha256` dla `archive`; ewaluacja (`plugin eval`) nie jest audytem bezpieczeństwa. Mody
(`plugins/mods`) mogą zmieniać decyzje uprawnień (`tool.check`) — `allowManagedModsOnly`.

## 7. Produkt osadzający CLI

Pakiet konfiguracji produktu (agenci, hooki, serwer MCP, skille domenowe) jako wtyczka
w katalogu wydania, ładowana `--plugin-dir` w każdym przebiegu (także przy `--resume`),
z bramką `init.plugin_errors`. Nie włączaj na hoście `disableSideloadFlags` ani
`strictPluginOnlyCustomization`, jeśli produkt używa flag `--agents`/`--mcp-config`.
