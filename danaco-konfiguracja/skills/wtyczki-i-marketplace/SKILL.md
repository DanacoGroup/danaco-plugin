---
name: wtyczki-i-marketplace
description: >
  Wtyczki Claude Code i marketplace: układ wtyczki (skills, commands, agents, hooks/hooks.json,
  .mcp.json, .lsp.json, bin/, output-styles, monitors, settings.json), plugin.json (userConfig,
  dependencies, version), ${CLAUDE_PLUGIN_ROOT}/${CLAUDE_PLUGIN_DATA}, marketplace.json
  i źródła (ścieżka, github, git-subdir, npm, archive, command), strict, instalacja i zakresy,
  enabledPlugins, extraKnownMarketplaces, --plugin-dir, aktualizacje i wersje, polityki
  organizacji (strictKnownMarketplaces, blockedMarketplaces, seed CI), walidacja i koszt
  tokenów. Stosuj, gdy pada „zbuduj wtyczkę”, „plugin.json”, „marketplace”, „zainstaluj
  wtyczkę zespołowi”, „wtyczka się nie ładuje”, „--plugin-dir”.
---

# Wtyczki i marketplace

## Kiedy stosować

Gdy skille, agenci, hooki, serwery MCP/LSP i polecenia mają trafić do wielu osób, projektów
lub produktu **jednym, wersjonowanym artefaktem**. Wtyczka to także właściwa forma pakietu
konfiguracji produktu osadzającego CLI (`--plugin-dir` z katalogu wydania).

## Układ wtyczki

| Element | Domyślne miejsce | Uwagi |
|---|---|---|
| manifest | `.claude-plugin/plugin.json` | opcjonalny; wszystko inne w korzeniu, nie w `.claude-plugin/` |
| skille | `skills/<nazwa>/SKILL.md` | polecenie `/wtyczka:nazwa`; `SKILL.md` w korzeniu = wtyczka z jednym skillem |
| polecenia | `commands/*.md` | starszy format — dla nowych skille |
| agenci | `agents/*.md` (podkatalogi w nazwie) | bez `hooks`, `mcpServers`, `permissionMode` |
| hooki | `hooks/hooks.json` | forma exec z `${CLAUDE_PLUGIN_ROOT}`; `${user_config.x}` tylko w `args` |
| MCP | `.mcp.json` lub `mcpServers` w manifeście | narzędzia `mcp__plugin_<wtyczka>_<serwer>__…`, serwer w hookach `plugin:<wtyczka>:<serwer>` |
| LSP | `.lsp.json` | inteligencja kodu |
| pliki wykonywalne | `bin/` | w `PATH` narzędzia Bash; claude.ai i Cowork nie zainstalują takiej wtyczki |
| style wyjścia, motywy, workflowy, monitory | `output-styles/`, `themes/`, `workflows/`, `monitors/monitors.json` | — |
| ustawienia domyślne | `settings.json` | tylko `agent` i `subagentStatusLine` |
| `CLAUDE.md` w korzeniu | — | **nie jest ładowany** (walidator ostrzega) — instrukcje do skilla |

Zmienne: `${CLAUDE_PLUGIN_ROOT}` (katalog bieżącej wersji — zmienia się przy aktualizacji,
nie zapisuj tam stanu), `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`, przetrwa
aktualizacje, usuwany przy odinstalowaniu z ostatniego miejsca), `${CLAUDE_PROJECT_DIR}`.

## Manifest — decyzje

- `name` w kebab-case (identyfikator przed `@`), `version` (semver), `description`, `author`
  — brak = ostrzeżenie (z `--strict` błąd).
- **Wersja**: manifest > wpis marketplace > SHA/skrót źródła. Przypięta `version` trzyma
  użytkowników na kopii w pamięci podręcznej, dopóki jej nie zmienisz; bez `version` każdy
  commit to nowa wersja.
- `userConfig` (`type`, `title`, `description`, `required`, `default`, `options` ≥2.1.271,
  `multiple`, `sensitive`, `min/max`): wartości w `pluginConfigs` ustawień, `sensitive`
  w magazynie poświadczeń; obiekty ścisłe — nieznany klucz blokuje wtyczkę.
- `dependencies`, `defaultEnabled`, `displayName`, `metadata`; nieznane pole główne jest
  usuwane z ostrzeżeniem.

## Marketplace

`.claude-plugin/marketplace.json`: `name` (część po `@`), `owner.name`, `plugins[]`
(`name`, `source`, opisy, `category`, `tags`, `strict`, `dependencies`, `defaultEnabled`).
Źródła wtyczek: ścieżka względna `./…` (lub goła nazwa przy `metadata.pluginRoot`,
≥2.1.239), `github` (`repo`, `ref`, `sha`), `url` (repozytorium git), `git-subdir`, `npm`
(bez skryptów instalacyjnych), `archive` (zip + `sha256`, ≥2.1.224), `command` (≥2.1.229).
`strict: true` (domyślnie) — `plugin.json` jest autorytetem, komponenty z wpisu dopisywane;
`false` + komponenty w obu = konflikt. Marketplace typu `url` (sam plik) nie obsłuży ścieżek względnych.

## Instalacja, włączanie, zakresy

| Cel | Sposób |
|---|---|
| jedna sesja, rozwój, produkt | `--plugin-dir <katalog|zip|folder wtyczek>` (folder ≥2.1.265); przesłania zainstalowaną o tej samej nazwie |
| osobiście | `claude plugin marketplace add <źródło>`, `claude plugin install nazwa@marketplace` (zakres `user`) |
| zespół w repozytorium | `.claude/settings.json`: `extraKnownMarketplaces` + `enabledPlugins` (wymaga zaufania folderu; wtyczkę z zewnętrznego źródła każdy instaluje raz) |
| organizacja | managed: `enabledPlugins` (wymuszenie/blokada), `strictKnownMarketplaces`, `blockedMarketplaces`, `extraKnownMarketplaces` |
| obraz CI/kontener bez sieci | seed: `CLAUDE_CODE_PLUGIN_CACHE_DIR` przy budowie, `CLAUDE_CODE_PLUGIN_SEED_DIR` w obrazie + `enabledPlugins` |

`--plugin-dir`, `--settings`, `--mcp-config` nie są zapamiętywane przy `--resume` — podawaj
je w każdym przebiegu. Przeładowanie w sesji: `/reload-plugins` (w `-p` nie łączy serwerów MCP wtyczek).

## Procedura

1. Szkielet: `claude plugin init <nazwa>` (tworzy w `~/.claude/skills/<nazwa>/`, ładuje się
   jako `<nazwa>@skills-dir`) albo ręcznie według układu wyżej.
2. Komponenty według pakietów: `budowa-skilli`, `podagenci-i-zespoly`, `hooki`, `serwery-mcp`.
3. Sprawdzenie: `sh "${CLAUDE_PLUGIN_ROOT}/skills/wtyczki-i-marketplace/scripts/sprawdz_wtyczke.sh" <katalog> "$(command -v claude)"`
   — `validate --strict`, `plugin details` (koszt stały i przy wywołaniu), sesja `-p` na
   atrapie (`init.plugins`, skille, agenci, MCP, `plugin_errors`).
4. Marketplace: `claude plugin validate <katalog marketplace> --strict`.
5. Ewaluacja wyzwalania skilli: `claude plugin eval` (wymaga modelu).
6. Dystrybucja: repozytorium git z tagami; w CI bramka `claude plugin validate --strict`
   i `system/init.plugin_errors` w `-p` („Fail CI when a plugin doesn't load”).

## Pułapki

- `claude plugin details <ścieżka>` nie działa — tylko nazwa wtyczki zainstalowanej albo
  z `--plugin-dir` (`claude --plugin-dir X plugin details nazwa`).
- `userConfig` z `default` i `options` nadal zgłasza „option not yet set” po instalacji —
  zatwierdzenie przez `/plugin configure` lub `--config KEY=VALUE`.
- Hooki we wpisie marketplace jako ścieżka pliku przechodzą walidację, ale nie działają —
  tylko obiekt inline.
- `${user_config.*}` w hooku formy powłoki, poleceniu monitora i `headersHelper` = błąd;
  w formie powłoki czytaj `$CLAUDE_PLUGIN_OPTION_<KLUCZ>`.
- Serwer MCP wtyczki nazywa się `plugin:<wtyczka>:<serwer>` — matcher hooka i reguły
  uprawnień pisane dla gołej nazwy nie trafią.
- Katalog z `--plugin-dir` jest **ścieżką chronioną** (zapis do niego zawsze pyta/odmawia).
- `strictKnownMarketplaces: []` blokuje wszystko, także oficjalny marketplace; nie blokuje
  `--plugin-dir` (to robi `disableSideloadFlags` — nie włączaj na hoście produktu, który
  używa `--plugin-dir`, `--agents`, `--mcp-config`).
- Wtyczki wbudowane (`…@builtin`) ładują się zawsze, także przy `--setting-sources ""`.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `renames` w marketplace | 2.1.193 |
| `metadata` we wpisie | 2.1.222 |
| źródło `archive` | 2.1.224 |
| źródło `command`, `disableCommandPluginSources` | 2.1.229 |
| aliasy `allowedMarketplaces`/`additionalMarketplaces` | 2.1.232 |
| `claude plugin validate` katalogu skilli/agentów | 2.1.233 |
| `headers`/`headersHelper` pobierania archiwów | 2.1.238 |
| `metadata.pluginRoot` | 2.1.239 |
| folder wtyczek w `--plugin-dir` | 2.1.265 |
| `claude plugin eval`, wiersze `userConfig` w `/config` | 2.1.269 |
| `userConfig.options` | 2.1.271 |
| `syncClaudeAiPlugins` | 2.1.273 |
| walidacja MCP w `plugin validate` | 2.1.281 |

## Szablony (sprawdzone `validate --strict`, `plugin details`, instalacją i sesją `-p`)

- `examples/marketplace-zespolu/` — marketplace z `pluginRoot` i wtyczką `narzedzia-zespolu`
  (skill, agent, hook z `userConfig`, `bin/`, `.mcp.json`).
- `examples/zespol-wtyczki.project.settings.json` — rejestracja marketplace i włączenie w repozytorium.
- `examples/polityka-wtyczek.managed.settings.json` — lista dozwolonych marketplace, blokady, wymuszenia.
- Ta wtyczka (`danaco-konfiguracja`) jest pełnym wzorcem wtyczki z 15 skillami, poleceniem, agentem i skryptami.

## Referencje

- `references/manifest-i-komponenty.md` — pola manifestu, komponenty, zmienne, ścieżki, zależności.
- `references/marketplace-i-dystrybucja.md` — źródła, wersje, aktualizacje, polityki organizacji, seed, polecenia CLI.
