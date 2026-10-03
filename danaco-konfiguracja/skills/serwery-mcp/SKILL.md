---
name: serwery-mcp
description: >
  MCP w Claude Code: zakresy serwerów (local, project/.mcp.json, user, wtyczka, konektory
  claude.ai, managed), --mcp-config i --strict-mcp-config, typy stdio/http/sse/ws,
  rozwijanie ${VAR}, uwierzytelnianie (OAuth, headers, headersHelper), tool search
  i alwaysLoad, instrukcje serwera i limit CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH,
  list_changed, limity wyniku (MAX_MCP_OUTPUT_TOKENS, maxResultSizeChars), zasoby, prompty,
  requiresUserInteraction, managed-mcp.json, allowedMcpServers/deniedMcpServers, projekt
  narzędzi według praktyk Anthropic. Stosuj, gdy pada „dodaj serwer MCP”, „.mcp.json”,
  „serwer nie łączy się”, „narzędzia MCP nie widać”, „zbuduj serwer MCP”, „polityka MCP”.
---

# Serwery MCP

## Kiedy stosować

Gdy agent ma dostać narzędzia, dane lub zasoby z zewnętrznego systemu przez MCP, gdy trzeba
ustalić, skąd serwer się wczytuje i kto go zatwierdza, gdy projektujesz własny serwer
(np. dla produktu osadzającego CLI) albo politykę MCP dla organizacji.

## Gdzie definiować serwer

| Zakres | Plik | Kiedy | Uwagi |
|---|---|---|---|
| local (domyślny `claude mcp add`) | `~/.claude.json` → `projects[<ścieżka>].mcpServers` | osobiste, z poświadczeniami | tylko ten projekt |
| project | `.mcp.json` w korzeniu projektu | wspólne dla zespołu | interaktywnie zgoda przed użyciem; w `-p`/SDK/chmurze **łączone bez pytania** |
| user | `~/.claude.json` → `mcpServers` | osobiste we wszystkich projektach | — |
| wtyczka | `.mcp.json` wtyczki lub `mcpServers` w `plugin.json` | dystrybucja z wtyczką | nazwy narzędzi `mcp__plugin_<wtyczka>_<serwer>__…` |
| sesja | `--mcp-config plik.json` (+ `--strict-mcp-config`) | produkt, CI | flagi nie są zapamiętywane przy `--resume` — podawaj ponownie |
| organizacja | `managed-mcp.json` (wyłączna kontrola) albo `managedMcpServers` (dodatek) | polityka | szczegóły: `references/zarzadzanie-mcp.md` |

Pierwszeństwo przy tej samej nazwie: local > project > user > wtyczka > konektory claude.ai
(wtyczki i konektory dopasowywane po adresie/poleceniu); `managedMcpServers` ponad
wszystkim (≥2.1.259). Wpis brany w całości z najwyższego źródła, pola nie są scalane.

**Produkt osadzający / CI:** `--strict-mcp-config --mcp-config <plik>` — tylko serwery
z flagi (bez `.mcp.json` projektu, serwerów użytkownika i konektorów claude.ai), plus
`allowedMcpServers` i `disableClaudeAiConnectors: true` jako obrona w głąb. W `-p` CLI
czeka przed pierwszą turą na łączące się serwery do `MCP_TIMEOUT` (domyślnie 30 s,
≥2.1.221); serwer z pamięcią podręczną listy narzędzi łączy się przy pierwszym użyciu.
Sprawdzaj `system/init.mcp_servers[].status` i przerywaj przebieg, gdy serwer kluczowy
nie jest `connected`.

## Konfiguracja wpisu

| Typ | Pola |
|---|---|
| `stdio` | `command`, `args`, `env`; dostaje `CLAUDE_PROJECT_DIR` w środowisku; `roots/list` = katalogi robocze |
| `http` (zalecany zdalny) | `url`, `headers`, `headersHelper`, `oauth` (`clientId`, `callbackPort`…), `timeout`, `alwaysLoad` |
| `sse` | jak `http` (starszy transport) |
| `ws` | `url`, `headers`, `headersHelper`, `timeout`, `alwaysLoad` — bez OAuth i bez `claude mcp add --transport` |

- `${VAR}` i `${VAR:-domyślna}` w `command`, `args`, `env`, `url`, `headers`; brak wartości
  bez domyślnej = dosłowny tekst + ostrzeżenie. **W `url`/`headers` serwera zdalnego
  zmienne poświadczeń (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `HTTPS_PROXY`,
  `NPM_TOKEN`…) są czytane jako puste** — skopiuj do zmiennej o własnej nazwie.
- `${CLAUDE_PROJECT_DIR}` poza wtyczką wymaga domyślnej: `${CLAUDE_PROJECT_DIR:-.}`.
- `claude mcp add … -- <polecenie>`: `--` oddziela opcje CLI od polecenia serwera;
  `--env` przyjmuje wiele par — wstaw inną opcję przed nazwą serwera.
- Nazwy zastrzeżone (`workspace`, `claude-in-chrome`, `computer-use`, `Claude Preview`,
  `Claude Browser`) są pomijane; serwer `anthropic-skills` nie wystawi promptów.

## Kontekst, tool search i limity

- **Tool search** (domyślnie): na starcie ładują się tylko nazwy narzędzi i **instrukcje
  serwera**; definicje na żądanie przez `ToolSearch`. Wyłączony przy `ANTHROPIC_BASE_URL`
  innym niż Anthropic (proxy), `ENABLE_TOOL_SEARCH=false`, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`;
  `auto[:N]` — próg % okna. Przy tool search dołączenie/odłączenie serwera nie unieważnia cache.
- `alwaysLoad: true` (serwer) albo `_meta["anthropic/alwaysLoad"]` (narzędzie) — narzędzia
  od startu bez kroku wyszukiwania; start czeka na serwer do 5 s. Tylko dla kilku narzędzi
  rdzenia.
- **Instrukcje serwera i opisy narzędzi ucinane do 2048 znaków**;
  `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` (≥2.1.280) zmienia limit dla wszystkich.
  Próba 2.1.286: instrukcje 5 600 znaków ucięte przy domyślnym limicie, pełne przy `8000`;
  trafiają do pierwszej wiadomości (sekcja „# MCP Server Instructions”), nie do `system`.
- Wynik narzędzia: ostrzeżenie > 10 000 tokenów, limit `MAX_MCP_OUTPUT_TOKENS` (25 000);
  ponad limit → plik w `tool-results` z odwołaniem. Per narzędzie
  `_meta["anthropic/maxResultSizeChars"]` do 500 000 znaków (tekst; obrazy nadal wg tokenów).
- Wywołanie dłuższe niż 2 min przechodzi w tło (≥2.1.212; nie w `-p` bez
  `CLAUDE_AUTO_BACKGROUND_TASKS=1`, nie u podagentów); limity `MCP_TOOL_TIMEOUT`,
  `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`.
- `list_changed` — CLI odświeża narzędzia, zasoby i prompty; nieudane odświeżenie
  zostawia poprzednią listę (≥2.1.214).

## Uwierzytelnianie zdalnych serwerów

OAuth przez `/mcp` lub `claude mcp login <nazwa>` (`--no-browser` przez SSH); stały port
zwrotny `callbackPort`; wstępnie zarejestrowany klient `--client-secret`; ograniczenie
zakresów; `headersHelper` dla własnych schematów (JSON nagłówków na stdout, 10 s, uruchamiany
przy każdym połączeniu, ponawiany po 401/403; z `.mcp.json` dopiero po zaufaniu folderu —
w `-p` nie uruchamia się). `Authorization` z helpera wyłącza OAuth dla serwera.

## Procedura

1. Wybierz zakres (tabela wyżej); produkt/CI — `--mcp-config` + `--strict-mcp-config`.
2. Napisz wpis; sprawdź: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/serwery-mcp/scripts/sprawdz_mcp.py" <plik> --polacz`
   (struktura, sekrety, zmienne, a dla stdio — uzgodnienie protokołu, instrukcje, opisy,
   schematy, `_meta`).
3. `claude mcp list` / `claude mcp get <nazwa>` (status, `Issue:`), w sesji `/mcp`.
4. Uprawnienia: `mcp__serwer` w allow (bez nawiasów w plikach), `deny` dla narzędzi
   niebezpiecznych; w `dontAsk` narzędzie MCP bez allow jest odrzucane.
5. Próba: `proba_cli.py -- --mcp-config <plik> --strict-mcp-config --permission-mode dontAsk`
   — `system/init.mcp_servers`, lista narzędzi w żądaniu, instrukcje (`--szukaj`).
6. Projektując serwer — `references/projektowanie-serwera.md` i `examples/serwer_wzorcowy.py`.

## Pułapki

- `.mcp.json` z repozytorium w `-p` łączy się **bez pytania** (także niezatwierdzone);
  blokada: `--strict-mcp-config`, `--setting-sources` bez projektu, `disabledMcpjsonServers`.
  Repozytorium nie zatwierdzi własnych serwerów (`enableAllProjectMcpServers` z pliku
  projektu nie działa przed zaufaniem, ≥2.1.196).
- Matcher hooka `mcp__serwer` bez `__.*` nie trafia w nic; reguła uprawnień
  `mcp__serwer__narzedzie(…)` w pliku jest pomijana.
- `--strict-mcp-config` przy wdrożonym `managed-mcp.json` = błąd startu („You cannot
  dynamically configure MCP servers when an enterprise MCP config is present”).
- `allowedMcpServers` z samym `serverName` to nie kontrola bezpieczeństwa (nazwę nadaje
  użytkownik); egzekwują `serverCommand` i `serverUrl`.
- `--permission-prompts none` anuluje elicitation bez hooka `Elicitation`.
- `_meta["anthropic/requiresUserInteraction"]: true` — w `dontAsk` i przez
  `--permission-prompt-tool` zawsze odmowa; tylko człowiek lub SDK `canUseTool`.
- Serwer stdio piszący cokolwiek poza JSON-RPC na stdout psuje połączenie — dzienniki na stderr.
- Narzędzie z kombinatorem `anyOf/oneOf/allOf` w korzeniu schematu jest spłaszczane;
  właściwości poza `[A-Za-z0-9_.-]{1,64}` i schemat niezgodny z draft 2020-12 —
  narzędzie wykluczane (przy pobieraniu flag funkcji) albo całe żądanie 400.
- Pamięć podręczna listy narzędzi (`cached`) wyłączona domyślnie od 2.1.238 (`MCP_DISCOVERY_CACHE`).

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `requiresUserInteraction` | 2.1.199 |
| tło dla długich wywołań | 2.1.212 |
| odświeżenie zachowuje listę po błędzie | 2.1.214 |
| czekanie na serwery w `-p` przed 1. turą | 2.1.221 |
| `--strict-mcp-config` nie czeka na zatwierdzenie serwerów projektu | 2.1.246 |
| `managedMcpServers` | 2.1.259 |
| `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` | 2.1.280 |
| zapis obrazów z wyniku MCP do pliku | 2.1.283 |
| `alwaysLoad: false` odracza wszystkie narzędzia | 2.1.287 |

## Szablony (`sprawdz_mcp.py`, próba)

- `examples/zespol.mcp.json` — `.mcp.json` zespołu (stdio, http z `${VAR}`, `headersHelper`).
- `examples/produkt.mcp.json` — konfiguracja produktu dla `--mcp-config` z `alwaysLoad`.
- `examples/serwer_wzorcowy.py` — serwer stdio: instrukcje, `_meta`, zasób, narzędzie zgody (próba `--permission-prompt-tool`).
- `examples/managed-mcp.json` i `examples/polityka-mcp.managed.settings.json` — organizacja.

## Referencje

- `references/konfiguracja-i-zakresy.md` — zakresy, zatwierdzanie, transporty, uwierzytelnianie, statusy, limity.
- `references/projektowanie-serwera.md` — praktyki Anthropic dla narzędzi i serwerów, wzorzec dla produktu.
- `references/zarzadzanie-mcp.md` — `managed-mcp.json`, `managedMcpServers`, listy dozwolone/zakazane.
