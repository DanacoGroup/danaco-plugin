# Skille: pola frontmattera, nazwy poleceń, miejsca ładowania, cykl życia

Źródła: `cc:skills`, `cc:commands`, `cc:settings-reference` („Plugins and skills”),
`pl:agents-and-tools/agent-skills/overview`, `pl:agents-and-tools/agent-skills/best-practices`.

## 1. Pola (wszystkie opcjonalne; zalecany `description`)

| Pole | Znaczenie | Uwagi |
|---|---|---|
| `name` | nazwa polecenia (domyślnie nazwa katalogu) | spec Agent Skills: ≤64 znaki, `[a-z0-9-]`, bez „anthropic”, „claude”; w `.claude/commands` niedostępne |
| `description` | co robi i kiedy | brak → pierwszy niepusty wiersz treści; spec ≤1024; z `when_to_use` ucinane do 1536 w liście |
| `when_to_use` | dodatkowe wyzwalacze | dopisywane do opisu |
| `argument-hint` | podpowiedź argumentów | np. `[numer-zgłoszenia]` |
| `arguments` | nazwy argumentów pozycyjnych | `$nazwa` |
| `disable-model-invocation` | tylko człowiek | opis poza kontekstem; nie da się wczytać do podagenta; blokuje uruchomienie przez zadanie cykliczne (≥2.1.196) |
| `user-invocable` | `false` = tylko model | ukryty w menu `/` |
| `allowed-tools` | narzędzia bez pytania w turze wywołania | spacje/przecinki/lista; podstawienia `${CLAUDE_SKILL_DIR}` w regułach Bash; zaufanie folderu nie blokuje |
| `disallowed-tools` | narzędzia odebrane na czas skilla | do następnej wiadomości |
| `model` | model do końca tury | `inherit`; filtrowany przez `availableModels` |
| `effort` | effort na czas skilla | `low`…`max` |
| `context` | `fork` = osobny podagent | treść skilla jako zlecenie |
| `agent` | typ podagenta dla `fork` | domyślnie `general-purpose`; `Explore`/`Plan` pomijają CLAUDE.md |
| `background` | `false` = czekaj na wynik `fork` | ≥2.1.218; w `-p` i tak czeka |
| `hooks` | hooki od wywołania do końca sesji | `once: true` |
| `paths` | globy aktywujące automatyczne ładowanie | składnia reguł ścieżkowych z `.claude/rules` |
| `shell` | `bash`/`powershell` dla `!` | — |
| `metadata`, `license`, `compatibility` | dane własne / spec | Claude Code ich nie interpretuje |

Wartości logiczne: `true/false/yes/no/on/off/1/0` (≥2.1.218). Publikacja na claude.ai,
Skills API i `package_skill.py` przyjmuje tylko: `name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools` (inne = twardy błąd „Unexpected key(s)”).

## 2. Nazwa polecenia

| Położenie | Polecenie |
|---|---|
| `~/.claude/skills/x/SKILL.md`, `.claude/skills/x/SKILL.md` | `/x` lub `/<name>` |
| zagnieżdżony skill o kolidującej nazwie | `/apps/web:x` |
| `.claude/commands/x.md` | `/x`; podkatalog `a/x.md` → `/a:x` |
| wtyczka `skills/x/SKILL.md` | `/wtyczka:x` (lub `/wtyczka:<name>`); goła nazwa, jeśli wolna |
| `SKILL.md` w korzeniu wtyczki | `/wtyczka:<name>` |
| skill z claude.ai | `/anthropic-skills:x` (lub `/x`, jeśli wolne) |

Pierwszeństwo przy kolizji: organizacja > osobiste > projekt; skill > plik polecenia;
Twój skill > wbudowany (aliasy wbudowanego zostają przy wbudowanym); wtyczki zawsze obok
(przestrzeń nazw); skill z claude.ai ustępuje każdemu innemu.

## 3. Miejsca ładowania

| Miejsce | Ładuje się w |
|---|---|
| organizacja: `.claude/skills/` w katalogu ustawień zarządzanych | wszystkich sesjach na maszynie |
| osobiste `~/.claude/skills/` | każdym projekcie (nie w chmurze i Cowork) |
| projekt `.claude/skills/` | sesjach w repozytorium (także z katalogów nadrzędnych do korzenia) |
| zagnieżdżone `<podkatalog>/.claude/skills/` | gdy model zacznie pracę w podkatalogu (lub `/add-dir`, ≥2.1.257) |
| `--add-dir` | ta sesja (obserwowane zmiany) |
| wtyczka `skills/` | gdy wtyczka włączona |
| konto claude.ai | Cowork, chmura, terminal zalogowany tym kontem (`~/.claude/skills/synced/`) |

Dowiązania symboliczne do katalogów skilli są dozwolone. `--bare`, `--safe-mode`,
`strictPluginOnlyCustomization` ograniczają źródła. W worktree bez `.claude/skills` —
skille głównego checkoutu (≥2.1.277).

## 4. Cykl życia treści

Opis — w liście w każdej turze (budżet 1% okna; `skillListingBudgetFraction`,
`SLASH_COMMAND_TOOL_CHAR_BUDGET`, `skillListingMaxDescChars`). Treść — po wywołaniu jedna
wiadomość na resztę sesji; ponowne wywołanie z tą samą treścią dodaje tylko notkę.
Plik nie jest czytany ponownie w kolejnych turach. Po kompakcji: ostatnie wywołanie
każdego skilla, pierwsze 5 000 tokenów, łącznie do 25 000. Edycja pliku w trakcie sesji
jest wykrywana (katalogi istniejące przy starcie).

## 5. Wstrzykiwanie poleceń

`` !`polecenie` `` (na początku wiersza lub po białym znaku) i blok ` ```! ` — wykonane raz
przed wysłaniem, wynik wstawiony jako tekst (bez ponownego skanowania). Uruchamiane
narzędziem Bash/PowerShell (katalog roboczy sesji, limit 2 min, stderr dołączany).
Błąd przerywa wywołanie („Shell command failed for pattern …”); deny/brak zgody —
„Shell command permission check failed…” (w auto — model dostaje polecenie do wykonania).
`disableSkillShellExecution: true` — dotyczy skilli użytkownika, projektu, wtyczek,
katalogów dodatkowych (nie wbudowanych i zarządzanych).

## 6. Skille wbudowane i ich kontrola

Skille Anthropic (np. `/verify`, `/run`, `/code-review`, `/simplify`, `/batch`, `/design`,
`/slides`, `/deep-research`, `/claude-api`, `/loop`, `/schedule`) — angielskie instrukcje,
część uruchamia wielu agentów lub publikuje artefakty. Wyłączenie: `disableBundledSkills`,
`CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`; selektywnie `skillOverrides`. W produkcie
osadzającym CLI całość zamyka `--disable-slash-commands` (próba macierzy: `/effort max`,
`/config model=…`, `/simplify` od klienta przestają działać).

## 7. Diagnostyka

„Skill się nie wyzwala”: słowa kluczowe w opisie, `What skills are available?`, `/nazwa`,
`--debug` (błąd YAML), `claude plugin validate .claude/skills` (≥2.1.233). „Za często”:
węższy opis, `disable-model-invocation`. „Przestał działać w trakcie”: zasada do hooka,
ponowne wywołanie po kompakcji, ważne na początek. „Opisy ucięte”: `/doctor`, `/skill-doctor`,
budżet listy. Zniknięte skille osobiste: `~/.claude/skills/.trash/`.
