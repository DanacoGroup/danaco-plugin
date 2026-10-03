# Orkiestracja: tło, fork, wznawianie, limity, workflowy, zespoły, odpowiedniki SDK i MA

Źródła: `cc:sub-agents`, `cc:workflows`, `cc:agent-teams`, `cc:cross-session-messaging`,
`cc:agent-view`, `cc:agent-sdk/subagents`, `pl:managed-agents/multiagent-orchestration`.

## 1. Pierwszy plan i tło

| Sytuacja | Tryb podagenta |
|---|---|
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | zawsze pierwszy plan |
| fork mode włączony (domyślnie interaktywnie, ≥2.1.232) | zawsze tło; parametr `run_in_background` usunięty |
| fork mode wyłączony (domyślnie `-p` i SDK) | tło domyślnie, pierwszy plan gdy model potrzebuje wyniku; `background: true` wymusza tło |
| podagent członka zespołu w procesie | pierwszy plan |

Próba 2.1.286 (`-p`, atrapa): wywołanie `Agent` z typem własnym zwróciło „Async agent
launched successfully” — podagent ruszył w tle, `-p` czekał na jego wynik. Wynik tła
przychodzi jako powiadomienie w kolejnej turze. `Ctrl+B` przenosi zadanie w tło.

## 2. Fork

Dziedziczy całą rozmowę, instrukcję, narzędzia i model sesji → pierwsze żądanie czyta
cache rodzica (taniej niż świeży podagent). `/subtask <zadanie>` (≥2.1.212; wcześniej
`/fork`); model prosi o typ `fork`. Sterowanie: `CLAUDE_CODE_FORK_SUBAGENT=1|0`, deny
`Agent(fork)`. Fork nie tworzy kolejnych forków; może dostać `isolation: worktree`.

## 3. Wznawianie i nazwy

Każde wywołanie to nowa instancja; kontynuacja przez `SendMessage` (ID lub nazwa) —
pełna historia podagenta, w tle, z tym samym zestawem narzędzi. Explore i Plan są
jednorazowe. Podagent zatrzymany ręcznie (`x`, `stop_task`) nie wznawia się sam.
Model może nadać podagentowi `name`; przy włączonych zespołach nazwany podagent staje się
członkiem zespołu.

## 4. Limity

| Limit | Zmienna | Domyślnie |
|---|---|---|
| równoległe podagenty (Agent) | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | 20 |
| głębokość zagnieżdżeń | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | 3 (`1` = bez zagnieżdżeń) |
| podagenci na sesję | `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` | usunięta w 2.1.224 (bez skutku); brak limitu łącznego |
| agenci workflow naraz | `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (1–256) | 16 (mniej przy małej liczbie CPU) |
| agenci na przebieg workflow | — | 1000 |
| elementy `parallel()`/`pipeline()` | — | 4096 |

Przekroczenie równoległości: „Concurrent subagent limit reached”, model nie ponawia.
Wznowienie zakończonego podagenta zajmuje miejsce bez sprawdzania limitu.

## 5. Dynamic workflows

Skrypt JS orkiestrujący wielu agentów w tle (`Workflow`), uruchamiany przez wbudowane
workflowy (`/batch` itp.), polecenie w prompcie, słowo `ultracode` lub `--effort ultracode`.
Bez wejścia użytkownika w trakcie, bez bezpośredniego dostępu do plików z poziomu skryptu,
bez `import()`. Ostrzeżenie „Large workflow” od 25 agentów lub 1,5 mln tokenów
(`workflowSizeGuideline` zmienia próg). Model agentów jak dla podagentów; `availableModels`
podmienia zablokowane. Wyłączenie: `disableWorkflows: true` (także w managed), `/config`,
`CLAUDE_CODE_DISABLE_WORKFLOWS=1`; słowo kluczowe: `workflowKeywordTriggerEnabled: false`.
Workflow można zapisać i dystrybuować we wtyczce.

## 6. Zespoły agentów

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; tylko interaktywnie. Lider (sesja główna) +
członkowie (osobne sesje: w procesie albo w panelach tmux/iTerm2, `teammateMode`,
`--teammate-mode`), wspólna lista zadań, wiadomości `SendMessage`. Ograniczenia: jeden
zespół na sesję, bez zagnieżdżeń, `/resume` nie przywraca członków w procesie, uprawnienia
ustalane przy starcie. Bramki jakości: hooki `TeammateIdle`, `TaskCreated`, `TaskCompleted`.
Koszt: każdy członek to osobne okno kontekstu.

## 7. Wiadomości między sesjami

`SendMessage`/`ListAgents` między sesjami na tej maszynie (i dalej przez Remote Control);
`crossSessionInbound`: `accept` < `hold` < `refuse` (ostrzejsza wartość z projektu wygrywa),
`isolatePeerMachines: true`. Usługi: `refuse` + `disableAgentView: true`.

## 8. Odpowiedniki

| Agent SDK | CLI |
|---|---|
| `agents` (definicje) | `--agents` (JSON lub plik) |
| `agent` (sesja jako agent) | `--agent` |
| `forwardSubagentText` | `--forward-subagent-text` |
| `systemPrompt.append` dla podagentów | `--append-subagent-system-prompt(-file)` |
| zdarzenia zadań, `stop_task` | stream-json `task_*`, control request |

Claude Managed Agents: `multiagent` (koordynator, lista agentów, wątki) ≈ `--agents` +
narzędzie `Agent` + deny `Agent(...)`; brak hooków — ich rolę grają zdarzenia i potwierdzenia.
