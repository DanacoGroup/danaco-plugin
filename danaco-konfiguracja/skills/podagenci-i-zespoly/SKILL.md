---
name: podagenci-i-zespoly
description: >
  Podagenci Claude Code i orkiestracja: definicje (.claude/agents, ~/.claude/agents, managed,
  wtyczki, --agents JSON lub plik), frontmatter (tools, disallowedTools, model, effort,
  permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, isolation,
  omitClaudeMd), kolejność wyboru modelu, wbudowani agenci i ich wyłączanie, Agent(typ),
  limity równoległości i głębokości, fork, podagenci w tle, wznawianie, --agent jako agent
  sesji, --append-subagent-system-prompt(-file), dynamic workflows, ultracode, zespoły agentów.
  Stosuj, gdy pada „podagent”, „subagent”, „deleguj”, „równolegle”, „--agents”, „workflow”,
  „agent teams”, „ogranicz podagentów”, „podagent na tańszym modelu”.
---

# Podagenci, workflowy i zespoły agentów

## Kiedy stosować

Gdy praca ma się rozdzielić na wątki z osobnym kontekstem (wyszukiwanie, testy, badanie
źródeł), gdy trzeba ograniczyć narzędzia lub model części pracy, albo gdy produkt
dostarcza własnych agentów i musi kontrolować, co model może uruchomić.

## Wybór mechanizmu

| Potrzeba | Mechanizm | Uwagi |
|---|---|---|
| wydzielone zadanie z podsumowaniem (dużo wyjścia, osobne narzędzia) | podagent (`Agent`) | świeży kontekst, wraca jedno streszczenie |
| ta sama wiedza w głównej rozmowie | skill | bez osobnego kontekstu |
| kontynuacja z pełnym kontekstem rozmowy, taniej (cache rodzica) | fork (`CLAUDE_CODE_FORK_SUBAGENT`, `/subtask`) | domyślnie w sesji interaktywnej; w `-p` wyłączony |
| setki plików / wiele etapów w tle | dynamic workflow (`Workflow`, słowo `ultracode`) | do 16 agentów naraz (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`), 1000 na przebieg; duży koszt |
| równoległe sesje rozmawiające ze sobą | zespoły agentów (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | eksperymentalne, tylko interaktywnie (w `-p` nie powstają) |
| cała sesja jako wyspecjalizowany agent | `--agent <nazwa>` / klucz `agent` | prompt agenta zastępuje instrukcję sesji; `initialPrompt` jako pierwsza tura |

## Gdzie definiować (pierwszeństwo przy tej samej nazwie)

1. ustawienia zarządzane (`.claude/agents/` w katalogu zarządzanym),
2. `--agents '<json>'` lub `--agents plik.json` (plik tylko w `-p`, ≥2.1.281),
3. `.claude/agents/` (od katalogu roboczego w górę do korzenia repozytorium; bliższy wygrywa),
4. `~/.claude/agents/`,
5. katalog `agents/` wtyczki (identyfikator `wtyczka:podkatalog:nazwa`; bez `hooks`,
   `mcpServers`, `permissionMode`).

Katalogi skanowane rekurencyjnie; identyfikatorem jest `name` z frontmattera (nie nazwa
pliku). Zmiany plików są wykrywane bez restartu (poza nowym katalogiem, `--add-dir`
i sesjami z `--disable-slash-commands`).

## Frontmatter — co ustawiać świadomie

| Pole | Zalecenie |
|---|---|
| `name`, `description` (wymagane) | opis decyduje o automatycznym delegowaniu: co robi, kiedy go używać, czego nie robi |
| `tools` / `disallowedTools` | najwęższy zestaw; `disallowedTools` z argumentem (`Bash(git push *)`) usuwa **całe** narzędzie — blokady poleceń w `permissions.deny` |
| `model` | `inherit` lub alias/ID; kolejność: parametr wywołania → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → model sesji (od 2.1.251); `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` wymusza jeden model wszystkim (≥2.1.257) |
| `effort`, `maxTurns` | koszt i bezpiecznik pętli; przy `maxTurns` wynik oznaczony jako częściowy (≥2.1.246) |
| `permissionMode` | działa tylko, gdy sesja jest w `default`/`dontAsk`/`plan`; w `bypass`/`acceptEdits`/`auto` podagent dziedziczy tryb sesji |
| `skills` | pełna treść wskazanych skilli od startu (nie da się wczytać skilli z `disable-model-invocation`) |
| `mcpServers` | serwery tylko dla podagenta (nie obciążają kontekstu sesji); inline z projektu wymaga zaufania folderu |
| `memory` | `user`/`project`/`local` → `~/.claude/agent-memory/<nazwa>/` itd.; wyłączone razem z pamięcią automatyczną |
| `omitClaudeMd` | `true` dla agentów, którym wystarcza zlecenie (mniej tokenów) |
| `isolation: worktree` | kopia repozytorium; zmiany poza worktree blokowane |
| `background` | `true` — zawsze w tle |
| `experimental.cacheTtl` | `5m`/`1h` cache dla żądań podagenta |

Nieznane pole lub literówka w camelCase jest **pomijana bez błędu**. Plik bez `name`,
z `---` nie w pierwszym wierszu, z `:` w nazwie albo bez `description` — pomijany po cichu.

## Kontrola nad podagentami w produkcie i CI

- Wbudowani: `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` (tylko `-p`/SDK — zostają wyłącznie
  Twoje typy; wywołanie bez `subagent_type` kończy się błędem), `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`,
  deny `Agent(Explore)`, deny gołego `Agent` (bez delegowania).
- Parametry wywołania: deny `Agent(model:*)` (model nie wybierze droższego modelu),
  `Agent(isolation:*)`; albo `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`.
- Limity: `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (domyślnie 20 jednocześnie, ≥2.1.217),
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (domyślnie 3 warstwy; `1` = bez zagnieżdżeń).
- Wspólne zasady wszystkim podagentom (także zagnieżdżonym, nie forkom):
  `--append-subagent-system-prompt-file` (≥2.1.261, tylko `-p`) — trafia do instrukcji
  podagenta (część jego prefiksu cache); albo hook `SubagentStart` z `additionalContext`.
- Strumień: `--forward-subagent-text` (stream-json) daje tekst i myślenie podagentów
  z `parent_tool_use_id`.
- `-p` czeka na podagentów w tle do końca (limit bezczynności
  `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`).

Próba (CLI 2.1.286, atrapa): `--agents produkt.agents.json` +
`CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` → `init.agents` = tylko `badacz`, `wykonawca`;
wywołanie `Agent(subagent_type: badacz)` uruchomiło podagenta w tle („Async agent launched”),
jego żądanie zawierało prompt agenta i dopisek z `--append-subagent-system-prompt-file`.

## Procedura

1. Zdecyduj, czy to podagent, skill, fork czy workflow (tabela wyboru).
2. Napisz definicję (plik `.md` albo JSON), opis 2–3 zdania, wąskie `tools`, `model`, `maxTurns`.
3. Sprawdź: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/podagenci-i-zespoly/scripts/sprawdz_agenta.py" <plik|katalog|agents.json> --cli "$(command -v claude)"`
   (zawiera `claude plugin validate` dla katalogu).
4. W produkcie: wyłącz wbudowanych, zablokuj `Agent(model:*)`, ustaw limity.
5. Próba: `proba_cli.py --scenariusz` ze zleceniem `Agent` — `init.agents`, żądanie podagenta (`--szukaj`).
6. W sesji: `/agents`, `/tasks` (model podagenta), `--debug` (pominięte pliki).

## Pułapki

- Na Linuksie, macOS i WSL narzędzi `Glob` i `Grep` domyślnie **nie ma** (wyszukiwanie przez Bash:
  wbudowane `bfs`/`ugrep`). Wracają, gdy agent wymienia je w `tools` **bez** `Bash` albo sesja
  nie ma Bash (próba 2.1.286: agent z `tools: Bash, Read, Grep, Glob` dostał tylko `Bash`, `Read`).
- `Agent(worker, researcher)` w `tools` działa tylko dla agenta głównego (`--agent`);
  w podagencie lista typów jest ignorowana.
- Podagenci nie widzą historii rozmowy ani wcześniej wczytanych skilli — przekazuj wszystko
  w zleceniu; nie dziedziczą stylu wyjścia ani pamięci automatycznej sesji.
- Podagenci w tle mają mniejszy zestaw narzędzi wbudowanych; w `-p` bez hosta pytania
  o zgodę z podagenta w tle są odrzucane.
- `CLAUDE_CODE_SUBAGENT_MODEL` jest domyślną, nie wymuszeniem (od 2.1.251).
- Zespoły agentów zmieniają zwykłe delegowanie: nazwany podagent staje się członkiem
  zespołu. W `-p` zespoły nie powstają.
- Workflow i ultracode: koszt rośnie z liczbą agentów; w usłudze wyłącz
  (`disableWorkflows: true`, `workflowKeywordTriggerEnabled: false`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1`)
  — słowo „ultracode” w treści klienta mogłoby uruchomić przebieg.
- Hooki z frontmattera podagenta z projektu i jego inline `mcpServers` nie działają w `-p`
  w folderze niezaufanym.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| Explore dziedziczy model sesji; `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS` | 2.1.198 |
| `--append-subagent-system-prompt` | 2.1.205 |
| skanowanie wyniku podagenta | 2.1.210 |
| `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, `…SPAWN_DEPTH` | 2.1.217 (domyślna głębokość 3 od 2.1.219) |
| walidacja `--agents` przy starcie | 2.1.242 |
| `CLAUDE_CODE_SUBAGENT_MODEL` jako domyślna (nie nadrzędna) | 2.1.251 |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | 2.1.257 |
| `--append-subagent-system-prompt-file` | 2.1.261 |
| `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` | 2.1.269 |
| `--agents` z pliku, pusty `prompt` | 2.1.281 |

## Szablony (sprawdzone `claude plugin validate`, `sprawdz_agenta.py`, próbą)

- `examples/produkt.agents.json` — dwa typy dla produktu (`--agents` z pliku).
- `examples/agents/recenzent-kodu.md` — recenzent tylko do odczytu.
- `examples/agents/badacz-dokumentacji.md` — badacz z pamięcią projektu i `cacheTtl`.

## Referencje

- `references/definicje-i-model.md` — pełne pola, zakresy, wybór modelu, narzędzia dostępne podagentom, kontekst startowy.
- `references/orkiestracja.md` — fork, tło, wznawianie, limity, workflowy, zespoły, odpowiedniki Agent SDK i Managed Agents.
