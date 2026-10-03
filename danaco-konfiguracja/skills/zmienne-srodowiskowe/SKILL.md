---
name: zmienne-srodowiskowe
description: >
  Zmienne środowiskowe Claude Code: pełny indeks 376 zmiennych w 20 kategoriach
  (uwierzytelnianie i dostawcy, model i effort, cache, kontekst, sesje i osadzanie, podagenci,
  narzędzia, MCP, wtyczki, uprawnienia, bezpieczeństwo, telemetria, sieć, aktualizacje,
  diagnostyka), skąd CLI je bierze (powłoka, blok env ustawień, zarządzane, launcher), które
  pliki ich nie mogą ustawić, pierwszeństwo wobec flag i ustawień, zmienne usunięte
  i nieudokumentowane. Stosuj przy „jaka zmienna do…”, „zmienna nie działa”, „env w
  settings.json”, „środowisko usługi/systemd/kontenera”, przy literówkach w nazwach.
---

# Zmienne środowiskowe

## Kiedy stosować

Gdy konfiguracja idzie przez środowisko procesu (usługa, kontener, CI, `pam_env`, profil
powłoki) albo blok `env` w ustawieniach — i trzeba wiedzieć, czy zmienna istnieje, czy zadziała
z tego źródła i co wygrywa.

## Skąd CLI bierze zmienne

| Źródło | Kiedy działa | Uwagi |
|---|---|---|
| środowisko procesu (powłoka, systemd, docker, launcher) | start | jedyne źródło dla `CLAUDE_CODE_PROJECT_DIR_NAME`, `CLAUDE_CODE_RESTRICTED`, zmiennych `…_RM_…`, `CLAUDE_CODE_REMOTE`, `CLAUDE_CODE_ACCOUNT_UUID`, `CLAUDE_CODE_MESSAGING_*` |
| `env` w ustawieniach user / `--settings` / zarządzanych | start i po zapisie pliku (OTel tylko start) | nadpisuje wartość z powłoki; zarządzane wygrywają z niższymi |
| `env` w ustawieniach project / local | po zaufaniu folderowi; w `-p` od razu przy starcie | **ignorowane**: katalogi (`CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`, `HOME`, `TMPDIR`, `XDG_*`), eksport treści i włączanie OTel, `CLAUDE_CODE_PROCESS_WRAPPER`, synchronizacja i katalogi wtyczek (≥2.1.251; OTel ≥2.1.282) |
| launcher (aplikacja Desktop, runner środowisk samodzielnie hostowanych) | start | jego zmienne wygrywają z `env` wszystkich plików |

Zasady:
- Zmiennej nie da się usunąć z pliku — ustaw `""` (np. `"CLAUDE_CODE_USE_VERTEX": ""`).
- `NO_COLOR`/`FORCE_COLOR` z `env` trafiają tylko do podprocesów.
- Wartości `env` to jawny tekst przekazywany **każdemu podprocesowi** — sekrety przez
  `apiKeyHelper`, `otelHeadersHelper`, `headersHelper` MCP, nie przez `env`.
- Pierwszeństwo zmienna ↔ flaga zależy od funkcji: `--model` > `ANTHROPIC_MODEL` > `model`;
  `CLAUDE_CODE_EFFORT_LEVEL` > `--effort`; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` > `--autocompact`.

## Najczęściej potrzebne (skrót; pełna lista — `references/indeks-zmiennych.md`)

| Cel | Zmienne |
|---|---|
| uwierzytelnienie | `ANTHROPIC_API_KEY` (w `-p` zawsze wygrywa), `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK|VERTEX|FOUNDRY|ANTHROPIC_AWS|MANTLE` |
| model | `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU,FABLE}_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_DISABLE_FAST_MODE` |
| cache | `CLAUDE_CODE_PROMPT_CACHE_TTL`, `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`, `FORCE_PROMPT_CACHING_5M`, `DISABLE_PROMPT_CACHING*` |
| izolacja usługi | `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_PROJECT_DIR_NAME`, `CLAUDE_CODE_TMPDIR`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CLAUDE_CODE_DISABLE_CLAUDE_MDS`, `DISABLE_AUTOUPDATER` |
| ograniczenia | `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`, `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS`, `CLAUDE_CODE_DISABLE_WORKFLOWS`, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, `CLAUDE_CODE_DISABLE_CRON`, `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` |
| MCP | `MCP_TIMEOUT`, `MCP_TOOL_TIMEOUT`, `MAX_MCP_OUTPUT_TOKENS`, `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH`, `ENABLE_TOOL_SEARCH` |
| sieć | `HTTPS_PROXY`, `NO_PROXY`, `API_TIMEOUT_MS`, `CLAUDE_CODE_MAX_RETRIES`, `CLAUDE_CODE_CLIENT_CERT`/`_KEY` |
| prywatność | `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `OTEL_LOG_*` (domyślnie wyłączone) |
| diagnostyka | `CLAUDE_CODE_DEBUG_LOG_LEVEL`, `CLAUDE_CODE_DEBUG_LOGS_DIR`, `CLAUDE_CODE_STARTUP_FAILURE_RESULTS` |

## Procedura

1. Znajdź zmienną: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/szukaj.py" --typ zmienna SŁOWO [--pelny]`
   albo `--kategoria NAZWA`.
2. Sprawdź źródło przed wdrożeniem:
   - plik usługi: `scripts/sprawdz_zmienne.py --plik usluga.env --usluga --cli claude`,
   - działająca usługa: `scripts/sprawdz_zmienne.py --pid PID`,
   - blok `env` pliku ustawień: `scripts/sprawdz_zmienne.py --ustawienia PLIK --rodzaj project`
     (lub pełny walidator `${CLAUDE_PLUGIN_ROOT}/scripts/waliduj_ustawienia.py`).
   Skrypt nie wypisuje wartości bez `--wartosci`, sekrety zawsze maskuje.
3. Potwierdź działanie bez modelu: `${CLAUDE_PLUGIN_ROOT}/scripts/proba_cli.py --srodowisko K=V … -- <flagi>`
   (zdarzenie `init`, stderr, żądanie do atrapy).
4. Na serwerach Danaco nowa zmienna konta trafia do **obu** plików: `/etc/security/pam_env.conf`
   i `/etc/profile.d/51-danaco-cache.sh` (sesje aplikacji Claude dziedziczą środowisko serwera
   z chwili startu — wczytaj `. /etc/profile.d/51-danaco-cache.sh`).

## Pułapki

- **`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` wymusza tryb `default`** (próba 2.1.286, stderr
  „Permission mode forced to default — … allowed_non_write_users hardening”): `--permission-mode`
  i `defaultMode` są pomijane także przy jawnym `--allowed-tools`. W `-p` działają reguły allow,
  reszta jest odrzucana (jak w `dontAsk`), ale `acceptEdits`/`auto`/`bypassPermissions` przepadają.
  Na Linuksie tworzy też w katalogu roboczym **puste pliki-zaślepki** (`.env*`, `.npmrc`,
  `.yarnrc*`, `bunfig.toml`, `package.json`, `*lock*`, `.gitmodules`, `node_modules/.bin`,
  `.claude/commands`, `.claude/agents`), jeśli ich nie było — zostają po sesji.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, `DO_NOT_TRACK`,
  `DISABLE_GROWTHBOOK` wyłączają pobieranie flag funkcji: brak `/auto-mode-setup`, Remote Control,
  synchronizacji skilli/wtyczek, doradcy; `-p` bez jawnego trybu startuje w `auto` (≥2.1.285).
- Kolejność poświadczeń: `CLAUDE_CODE_USE_*` > `ANTHROPIC_AUTH_TOKEN` > `ANTHROPIC_API_KEY` > `apiKeyHelper` > `CLAUDE_CODE_OAUTH_TOKEN` > profil > `/login`. Klucz API i token OAuth naraz — w `-p` wygrywa klucz (`apiKeySource: ANTHROPIC_API_KEY`), domyślny
  TTL cache spada z 1h do 5m (próba).
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW` przyjmuje tylko liczbę (`500k` = 500 → przycięte).
- Zmienne usunięte bez błędu (no-op): `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` (2.1.224),
  `TASK_MAX_OUTPUT_LENGTH` (2.1.277), `CLAUDE_SUBAGENT_BG_SHELL_MAX_MS` (2.1.260),
  `CLAUDE_CODE_CONNECT_TIMEOUT_MS` (2.1.186), `CLAUDE_CODE_OPUS_4_6_FAST_MODE_OVERRIDE` (2.1.160);
  przestarzałe: `ANTHROPIC_SMALL_FAST_MODEL`, `ENABLE_PROMPT_CACHING_1H_BEDROCK`.
- Binarka 2.1.286 zawiera ok. 660 nazw `CLAUDE_*`/`ANTHROPIC_*` spoza `cc:env-vars` (wewnętrzne,
  np. `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`) — działają, ale bez gwarancji; skrypt z `--cli`
  oznacza je jako NIEUDOKUMENTOWANE.
- `OTEL_*` nie są przekazywane podprocesom; `env` z `.claude/settings.json` nie włączy telemetrii.

## Szablony

- `examples/usluga.zmienne.txt` — środowisko procesu usługi osadzającej CLI (bez sekretów;
  sprawdzone `sprawdz_zmienne.py --usluga` i próbą na atrapie: TTL `1h`, 2 skille zamiast 17).

## Referencje

- `references/indeks-zmiennych.md` — 376 zmiennych w 20 kategoriach (generowany `scripts/buduj_indeks_md.py`).
- Pakiety tematyczne: `model-cache-i-koszty` (model, cache, OTel), `headless-i-osadzanie`
  (sesje, izolacja), `piaskownica-i-izolacja` (poświadczenia, scrub), `serwery-mcp` (MCP_*).
