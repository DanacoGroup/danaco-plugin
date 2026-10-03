# Definicje podagentów, wybór modelu, narzędzia i kontekst startowy

Źródła: `cc:sub-agents`, `cc:cli-reference` (`--agents`, `--agent`,
`--append-subagent-system-prompt*`), `cc:env-vars`, `cc:agent-sdk/subagents`. Stan 01.10.2026.

## 1. Wbudowani agenci

| Agent | Model | Narzędzia | Uwagi |
|---|---|---|---|
| `Explore` | model sesji, na API ograniczony do Opus | tylko odczyt | pomija CLAUDE.md i migawkę git; poziom szczegółowości quick/medium/very thorough; nie da się go wznowić |
| `Plan` | model sesji | tylko odczyt | jak Explore; używany w trybie plan |
| `general-purpose` | model sesji | wszystkie dostępne podagentom | zadania złożone, zmiany kodu; cel wywołań bez `subagent_type` |
| `claude` | wg kolejności modeli | wszystkie | domyślny agent sesji w tle |
| `statusline-setup` | Sonnet | Read, Edit | `/statusline` |
| `claude-code-guide` | Haiku | — | pytania o Claude Code |

Własny agent o nazwie `Explore` w projekcie/użytkowniku zastępuje wbudowanego
(np. `model: haiku` dla taniej eksploracji).

## 2. Pola definicji

Plik `.md`: frontmatter YAML od pierwszego wiersza, treść = instrukcja systemowa podagenta
(podagent nie dostaje instrukcji Claude Code — tylko swoją + szczegóły środowiska).
JSON `--agents`: klucz = nazwa, `prompt` = treść, pozostałe pola jak we frontmatterze;
`color` i `experimental` ignorowane.

| Pole | Wartości | Uwagi |
|---|---|---|
| `name` | bez `:` i bez `-` na początku | wymagane w pliku; w hookach jako `agent_type` |
| `description` | tekst | wymagane; podstawa delegowania |
| `tools` | lista lub tekst z przecinkami | brak = wszystkie dostępne podagentom; `mcp__serwer`, `mcp__serwer__*`; same błędne nazwy → podagent się nie uruchomi |
| `disallowedTools` | jak `tools` | stosowane przed `tools`; `mcp__*` usuwa wszystkie MCP |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, pełne ID, `inherit` | — |
| `permissionMode` | `default`/`manual`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` | działa tylko przy sesji w `default`/`dontAsk`/`plan`; ignorowane we wtyczce |
| `maxTurns` | liczba | wynik częściowy, można wznowić |
| `skills` | lista | pełna treść od startu; nie dla `disable-model-invocation` |
| `mcpServers` | lista nazw lub definicji inline | inline z projektu wymaga zaufania; ignorowane we wtyczce |
| `hooks` | jak w ustawieniach | tylko gdy podagent działa; `Stop` → `SubagentStop`; ignorowane we wtyczce |
| `memory` | `user`, `project`, `local` | katalogi `~/.claude/agent-memory/`, `.claude/agent-memory/`, `.claude/agent-memory-local/` |
| `background` | `true` | zawsze w tle |
| `omitClaudeMd` | `true` | bez CLAUDE.md użytkownika/projektu/local (zarządzane zostają) |
| `effort` | `low`…`max` | nadpisuje effort sesji |
| `isolation` | `worktree` | tymczasowy worktree od gałęzi domyślnej; sprzątany, gdy bez zmian |
| `color` | 8 kolorów | wygląd |
| `initialPrompt` | tekst | pierwsza tura, gdy agent jest agentem sesji (`--agent`) |
| `experimental.cacheTtl` | `5m`, `1h` | TTL cache żądań podagenta |

## 3. Kolejność wyboru modelu

1. parametr `model` wywołania `Agent` (blokowany przez deny `Agent(model:*)`),
2. `model` z definicji (`inherit` = model sesji),
3. `CLAUDE_CODE_SUBAGENT_MODEL`,
4. model sesji.

Alias rodziny zgodny z rodziną modelu sesji = dokładny model sesji (z `[1m]`).
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (≥2.1.257): wszyscy podagenci, członkowie zespołu
i agenci workflow na modelu ze zmiennej (albo sesji), także Explore/Plan; fork i skill
`context: fork` z `model: inherit` zostają na modelu sesji. `availableModels` filtruje
wszystkie trzy źródła (alias rodziny → najnowsza dozwolona wersja). Podagenci dziedziczą
konfigurację myślenia (≥2.1.198) i łańcuch `--fallback-model`. Model podagenta: `/tasks`.

## 4. Narzędzia dostępne podagentom

Zawsze odfiltrowane: `Agent` (na granicy głębokości), `AskUserQuestion`, `EndConversation`,
`EnterPlanMode`, `ExitPlanMode` (poza `permissionMode: plan`), `ScheduleWakeup`,
`WaitForMcpServers`, `Workflow`. Podagent w tle ma tylko: `Read`, `Grep`, `Glob`, `LSP`,
`Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`,
`Skill` (i kilka innych) + wszystkie MCP. Członkowie zespołu dodatkowo narzędzia zadań i cron.

## 5. Co podagent dostaje na starcie

Instrukcję własną + szczegóły środowiska, zlecenie od modelu głównego, CLAUDE.md
(wszystkie poziomy; Explore/Plan i `omitClaudeMd` — nie), migawkę git (Explore/Plan — nie),
skille z `skills`, listę rodzeństwa (gdy ma `SendMessage`, ≥2.1.206), dopisek z
`--append-subagent-system-prompt(-file)`, kontekst hooków `SubagentStart`. Nie dostaje:
historii rozmowy, stylu wyjścia, pamięci automatycznej sesji; okno kontekstu zgodne z
własnym modelem.

## 6. Zakresy i ładowanie

Pierwszeństwo: managed > `--agents` > `.claude/agents/` (najbliższy katalogowi roboczemu)
> `~/.claude/agents/` > wtyczka. `--add-dir` wczytuje `.claude/agents/` dodanego katalogu
(bez obserwacji zmian). Wykrywanie problemów: `claude plugin validate .claude/agents`
(≥2.1.233; nie zgłasza pliku bez `name`), `--debug` (pominięte pliki z powodem), `/doctor`
(duplikaty nazw).

## 7. Agent jako sesja (`--agent`, klucz `agent`)

Instrukcja agenta zastępuje instrukcję sesji (pusty `prompt` bez `memory` — instrukcja
bez zmian, ≥2.1.281); `tools: Agent(a, b)` ogranicza typy, które agent główny może uruchomić;
`initialPrompt` jako pierwsza tura; hooki dostają `agent_type`; `--resume` przywraca agenta.
