# Manifest wtyczki i komponenty

Źródła: `cc:plugins/manifest-reference`, `cc:plugins/components`, `cc:plugins/create`,
`cc:plugins/dependencies`, `cc:plugins/code-intelligence`, `cc:plugins/loading`.

## 1. Pola `plugin.json`

| Pole | Uwagi |
|---|---|
| `name` | kebab-case; przy `--plugin-dir` bez manifestu — nazwa katalogu |
| `displayName`, `description`, `author{name,email,url}`, `homepage`, `repository`, `license`, `keywords` | pola wyświetlane (wpis marketplace ma pierwszeństwo dla wyświetlania) |
| `version` | pierwszeństwo przed wpisem marketplace i SHA źródła |
| `defaultEnabled` | domyślnie `true`; wpis marketplace wygrywa |
| `dependencies` | `"nazwa"`, `"nazwa@marketplace"` lub obiekt; zależności spoza własnego marketplace tylko z `allowCrossMarketplaceDependenciesOn` |
| `metadata` | dane własne |
| `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`, `outputStyles` | ścieżki (w obrębie wtyczki, bez `..`) lub definicje inline; `commands` może mieć `source`/`content` + `description` |
| `experimental.themes`, `experimental.monitors`, `experimental.evals` | komponenty eksperymentalne; katalog ewaluacji |
| `userConfig` | pytania przy włączeniu (patrz niżej) |
| `channels` | kanały powiadomień (research preview) |
| `settings` | domyślne `agent`, `subagentStatusLine` |

Nieznane pole główne — usuwane z ostrzeżeniem. Obiekty ścisłe (`userConfig.*`, `channels[]`,
`lspServers.*`, `monitors[]`) — nieznany klucz blokuje wtyczkę. `claude plugin validate`
to autorytatywne sprawdzenie (od 2.1.281 sprawdza też wpisy MCP: odrzucane wpisy,
`${user_config.X}` bez deklaracji, nieprawidłowe `url`; ostrzega o `http://` do hostów
nie-lokalnych i dosłownych poświadczeniach w nagłówkach).

## 2. `userConfig`

Klucze `[A-Za-z_][A-Za-z0-9_]*`. Pola: `type` (`string`, `number`, `boolean`, `directory`,
`file`), `title`, `description` (wymagane), `required`, `default`, `options` (≥2.1.271,
etykiety 1–64 znaki; starsze CLI nie załadują wtyczki), `multiple`, `sensitive`, `min`, `max`.
Wartości: `pluginConfigs` w ustawieniach; `sensitive` — magazyn poświadczeń. Użycie:
`${user_config.KLUCZ}` w konfiguracji MCP/LSP, `args` hooków formy exec, treści skilli
i agentów (bez wartości wrażliwych); `CLAUDE_PLUGIN_OPTION_<KLUCZ>` w środowisku hooków.
Niedostępne dla poleceń monitorów i `headersHelper`. Konfiguracja: `/plugin configure`,
`claude plugin configure <wtyczka> [--values-stdin]`, `claude plugin install … --config K=V`.

## 3. Zmienne ścieżek

| Komponent | Gdzie rozwijane | Eksport do procesu |
|---|---|---|
| hooki | `command`, `args` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_OPTION_*` |
| monitory | `command` | — |
| MCP stdio | `command`, `args`, `env` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` |
| MCP http/sse/ws | `url`, `headers`, `headersHelper` | — |
| LSP | `command`, `args`, `env`, `workspaceFolder` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR` |
| skille, agenci | treść, `allowed-tools` | — |

W formie powłoki cytuj: `"${CLAUDE_PLUGIN_ROOT}"/skrypt.sh`; w formie exec bez cudzysłowów.

## 4. Komponenty — szczegóły

- **Skille**: `skills/<nazwa>/SKILL.md`; `name` w frontmatterze zmienia ostatni segment
  `/wtyczka:<name>` (prefiks wtyczki w `name` nie jest dublowany, ≥2.1.246); goła nazwa
  działa, gdy wolna; `skillOverrides` nie dotyczy skilli wtyczek.
- **Agenci**: `agents/`, podkatalog → `wtyczka:podkatalog:nazwa`; pola `hooks`,
  `mcpServers`, `permissionMode`, `initialPrompt` ignorowane (skopiuj agenta do
  `.claude/agents/`, jeśli ich potrzebujesz).
- **Hooki**: scalane z hookami użytkownika i projektu; źródło w pytaniu `[plugin:<nazwa>]`;
  `allowManagedHooksOnly` je wyłącza (poza wtyczkami wymuszonymi w managed).
- **MCP**: start przy włączeniu wtyczki, rozłączenie przy wyłączeniu; pakiety MCPB;
  serwer z pustym `url` = „not configured” (miejsce na konektor do uzupełnienia).
- **LSP**: definicje, odwołania, diagnostyka po edycji (narzędzie `LSP`); serwer języka
  musi być zainstalowany.
- **bin/**: polecenia dostępne w Bash bez ścieżki.
- **Zależności Node**: instalacja do `${CLAUDE_PLUGIN_DATA}` (patrz `cc:plugins/loading`).

## 5. Ładowanie i diagnostyka

`claude plugin list [--json]`, `claude plugin details <nazwa>` (inwentarz i koszt), w `-p`
`system/init.plugins` i `plugin_errors`; `/plugin` → Errors; `--debug`. Konflikt nazw:
`--plugin-dir` przesłania zainstalowaną wtyczkę o tej samej nazwie. Wtyczka z repozytorium
(`@skills-dir` w `.claude/skills/`) wymaga zaufania folderu.
