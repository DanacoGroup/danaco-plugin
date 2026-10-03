# CLAUDE.md, reguły, AGENTS.md, pamięć automatyczna i style wyjścia

Źródła: `cc:memory`, `cc:output-styles`, `cc:large-codebases`, `cc:context-window`,
`cc:settings-reference` („Memory and context”), próby 2.1.286.

## 1. Pliki instrukcji

| Zakres | Położenie | Wspólne z |
|---|---|---|
| organizacja | Linux `/etc/claude-code/CLAUDE.md` (macOS `/Library/Application Support/ClaudeCode/`, Windows `C:\Program Files\ClaudeCode\`) lub `claudeMd` w managed | wszyscy na maszynie; nie do wykluczenia |
| użytkownik | `~/.claude/CLAUDE.md`, `~/.claude/rules/*.md` | Ty |
| projekt | `./CLAUDE.md` lub `./.claude/CLAUDE.md`, `.claude/rules/*.md` | zespół (git) |
| lokalny | `./CLAUDE.local.md` | Ty (dodaj do `.gitignore`) |

Ładowanie: przy starcie katalog roboczy i nadrzędne (od korzenia do katalogu roboczego);
podkatalogi przy pierwszym czytaniu plików w nich; wszystko konkatenowane. `--add-dir` —
tylko z `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`. Próba: CLAUDE.md z katalogu
roboczego i jego import `@docs/wydania.md` dotarły w pierwszej wiadomości; reguła z `paths`
nie została wczytana przy starcie; komentarz HTML usunięty; `--setting-sources ""`
i `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` wyłączyły CLAUDE.md projektu.

## 2. Jak pisać

- konkretnie i sprawdzalnie; sekcje i punkty; < 200 wierszy na plik;
- części dotyczące fragmentu kodu → `.claude/rules/*.md` z `paths:` (globy jak w regułach);
- importy `@ścieżka` (względem pliku zawierającego, do 4 poziomów; ścieżki ze spacjami
  przez `\ `; w backtickach i blokach kodu nie importują);
- bez sprzeczności (model wybierze jedną dowolnie); okresowy `/doctor prompt-audit`;
- notatki dla ludzi w `<!-- … -->` (usuwane przed wstrzyknięciem);
- zakazy, które muszą działać — w uprawnieniach lub hookach, nie w CLAUDE.md.

## 3. AGENTS.md

Domyślnie (`claude-md-or-agents-md`) czytany, gdy w katalogu i wyżej nie ma CLAUDE.md ani
CLAUDE.local.md. Tryby: `claude-md-and-agents-md`, `claude-md`, `managed-only` — w `/config`
(„Project instructions”) albo `pluginConfigs["agents-md@builtin"].options.instructionFiles`
w user/managed/`--settings` (projekt i local ignorowane). Wspólny plik dla wielu narzędzi:
CLAUDE.md z importem `@AGENTS.md` albo dowiązanie.

## 4. Wykluczenia

`claudeMdExcludes`: globy ścieżek bezwzględnych (plik lub cel dowiązania, ≥2.1.239), listy
sumowane ze wszystkich warstw; zarządzanego CLAUDE.md nie wykluczysz. Monorepo: wyklucz
CLAUDE.md innych zespołów w `.claude/settings.local.json`.

## 5. Pamięć automatyczna

| Element | Zachowanie |
|---|---|
| katalog | `~/.claude/projects/<projekt>/memory/` (wspólny dla worktree repozytorium); `autoMemoryDirectory`; przy `CLAUDE_CODE_PROJECT_DIR_NAME` — `<config>/projects/<nazwa>/memory/` |
| `MEMORY.md` | indeks: pierwsze 200 wierszy lub 25 KB w każdej sesji; CLI przypomina o skracaniu |
| pliki tematów | czytane na żądanie; frontmatter dostaje pole `modified` |
| retencja | poza `cleanupPeriodDays` (zostają do usunięcia) |
| podagenci | nie dziedziczą (fork tak); własna przez `memory:` |
| wyłączenie | `autoMemoryEnabled: false` (dowolny plik), `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` |
| zapisy | narzędziami Write/Edit — przy ich braku pamięć się nie zapisze, ale nadal się wczyta |

Usługi wielodzierżawne: wyłącz pamięć jawnie — `--setting-sources ""` jej nie odcina,
a `CLAUDE_CODE_PROJECT_DIR_NAME` per dzierżawca rozdziela katalogi.

## 6. Style wyjścia

| Wbudowany | Charakter |
|---|---|
| `Default` | domyślny |
| `Proactive` | więcej autonomii bez pytań |
| `Concise` | krótko |
| `Explanatory` | z wyjaśnieniami „Insight” |
| `Learning` | zostawia fragmenty do napisania człowiekowi |

Własne: `~/.claude/output-styles/`, `.claude/output-styles/` (najbliższy katalogowi
roboczemu wygrywa), managed, wtyczki (`force-for-plugin: true` wymusza). Frontmatter:
`name`, `description`, `keep-coding-instructions` (bez niego styl usuwa instrukcje
inżynierskie Claude Code), `force-for-plugin`. Wybór: `outputStyle` (wielkość liter
dokładnie jak nazwa), `/output-style` (także w `-p`, ≥2.1.269), `/config`. Zmiana w trakcie —
od następnej wiadomości, bez unieważnienia cache (≥2.1.251). Plik stylu czytany przy starcie
(edycja wymaga restartu). Podagenci (poza forkiem) stylu nie dostają.

Styl a inne mechanizmy: głos/format/rola sesji → styl; wiedza o projekcie → CLAUDE.md;
procedura zadania → skill; gwarancja → hook; dopisek na start → `--append-system-prompt`.
W produkcie zastępującym instrukcję fragmenty aplikacji lepiej trzymać w części zmiennej
instrukcji niż w stylach (macierz CLI, O3).
