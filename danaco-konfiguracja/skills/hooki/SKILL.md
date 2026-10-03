---
name: hooki
description: >
  Hooki Claude Code: 33 zdarzenia (SessionStart, UserPromptSubmit, PreToolUse,
  PermissionRequest, PostToolUse, Stop, SubagentStart, PreModelSwitch, ConfigChange…),
  pięć typów obsługi (command, http, mcp_tool, prompt, agent), matcher i `if`, kody
  wyjścia, wyjście JSON i decyzje (permissionDecision, decision: block, updatedInput,
  updatedToolOutput), additionalContext, CLAUDE_ENV_FILE, async, hooki we wtyczkach,
  skillach i agentach, zaufanie folderu, allowManagedHooksOnly. Stosuj, gdy pada „za każdym
  razem gdy…”, „przed/po narzędziu”, „zablokuj polecenie”, „dodaj kontekst”, „wymuś
  weryfikację przed końcem”, „hook nie działa”, „gwarancja zamiast prośby w instrukcji”.
---

# Hooki

## Kiedy stosować

Hook to **gwarancja**, instrukcja to prośba. Jeśli zasada ma obowiązywać zawsze
(blokada polecenia, kontekst na starcie, formatowanie po edycji, weryfikacja przed
końcem tury, dziennik zdarzeń), zrób z niej hook — nie zapis w CLAUDE.md. Hooki egzekwuje
CLI, model ich nie pomija.

## Trzy poziomy konfiguracji

```json
{"hooks": {"<Zdarzenie>": [ {"matcher": "<filtr>", "hooks": [ {"type": "command", "command": "…"} ]} ]}}
```

1. **zdarzenie** — punkt cyklu (tabela niżej, pełna: `references/zdarzenia-i-decyzje.md`);
2. **grupa z matcherem** — `"*"`, `""` lub brak = wszystko; litery/cyfry/`_`/`-`/spacje/`,`/`|`
   = dokładne nazwy (`Edit|Write`); inne znaki = wyrażenie regularne JS **bez kotwic**
   (`Edit.*` łapie też `NotebookEdit` — pisz `^Edit$`); narzędzia MCP: `mcp__serwer__.*`
   (samo `mcp__serwer` nie trafi w nic); serwer z wtyczki: `mcp__plugin_<wtyczka>_<serwer>__.*`;
3. **obsługa** — `command`, `http`, `mcp_tool`, `prompt`, `agent`; pole `if` (jedna reguła
   w składni uprawnień, np. `Bash(rm *)`) zawęża tylko na zdarzeniach narzędzi.

Wszystkie pasujące hooki działają **równolegle**; ten sam handler z dwóch plików — raz.

## Wybór zdarzenia

| Potrzeba | Zdarzenie | Mechanizm |
|---|---|---|
| kontekst na starcie, po wznowieniu, po kompakcji | `SessionStart` (matcher `startup`/`resume`/`compact`) | stdout lub `additionalContext` (≤10 000 znaków na łańcuch) |
| zmienne dla poleceń Bash całej sesji | `SessionStart` | `export …` dopisywane do `$CLAUDE_ENV_FILE` |
| kontekst dla podagentów (nie dziedziczą SessionStart) | `SubagentStart` | `additionalContext` |
| blokada / zmiana / zatwierdzenie wywołania | `PreToolUse` | `permissionDecision` allow/deny/ask/defer, `updatedInput` |
| polityka zgód zamiast człowieka | `PermissionRequest` | `decision.behavior`, `updatedPermissions` |
| formatowanie, lint, testy po edycji | `PostToolUse` (`Edit\|Write`) | efekt uboczny; `additionalContext`; `async` dla długich |
| ukrycie lub korekta wyniku narzędzia | `PostToolUse` | `updatedToolOutput` (kształt wyniku narzędzia) |
| filtr promptów użytkownika | `UserPromptSubmit` | `decision: block`, `additionalContext` |
| blokada `/skill` wpisanego ręcznie (omija PreToolUse) | `UserPromptExpansion` | `decision: block` |
| weryfikacja przed końcem tury | `Stop` | `decision: block` + `reason`; sprawdzaj `stop_hook_active` |
| rejestr zmiany modelu (także fallback) | `PostModelSwitch` | dziennik, `additionalContext` |
| zakaz zmiany modelu | `PreModelSwitch` | `permissionDecision: deny` (timeout też blokuje) |
| audyt zmian ustawień | `ConfigChange` | `decision: block` (poza `policy_settings`) |
| błędy API w turze | `StopFailure` | tylko dziennik (wyjście ignorowane) |
| sprzątanie | `SessionEnd` | budżet 1,5 s (do 60 s przy dłuższym `timeout`) |

## Kody wyjścia i JSON — reguły, które decydują o skuteczności

- **exit 0** — sukces; stdout trafia do kontekstu tylko w `SessionStart`,
  `UserPromptSubmit`, `UserPromptExpansion`, `PostModelSwitch`; gdzie indziej do dziennika.
- **exit 2** — blokada (na zdarzeniach, które blokują); stderr = powód. JSON nie odblokuje.
- **exit 1 i inne** — błąd **nieblokujący**: akcja idzie dalej. Hook polityki musi
  kończyć się `exit 2` albo JSON-em z decyzją.
- **Timeout** `command`/`http`/`mcp_tool` na `PreToolUse` **nie blokuje** (wywołanie idzie
  dalej); na `PreModelSwitch` blokuje. Domyślnie 600 s; 30 s na `UserPromptSubmit`
  i `*ModelSwitch`; 10 s na `MessageDisplay`; `prompt` 30 s, `agent` 60 s.
- JSON parsowany, gdy stdout zaczyna się `{` i kończy `}` — echo z profilu powłoki przed
  JSON-em psuje decyzję po cichu. Buduj JSON koderem (`jq -n`, `json.dumps`).
- Decyzja `PreToolUse` w `hookSpecificOutput.permissionDecision` (stare `decision`
  `approve/block` przestarzałe); `PermissionRequest` w `hookSpecificOutput.decision.behavior`
  (exit 2 ignorowany); `Stop`, `PostToolUse`, `UserPromptSubmit` — `decision: "block"` na górze.
- Pierwszeństwo przy wielu hookach `PreToolUse`: deny > defer > ask > allow.
  Hook „allow” **nie przebija** reguł deny/ask ani ścieżek krytycznych; hook „deny” blokuje
  nawet w `bypassPermissions`.
- `additionalContext` pisz jako fakty („Gałąź: feat/x”), nie polecenia systemowe — tekst
  udający instrukcje systemu model potraktuje jak wstrzyknięcie.

## Typy obsługi — kiedy który

| Typ | Kiedy | Uwagi |
|---|---|---|
| `command` | domyślnie | forma exec (`args`) dla ścieżek z `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`; `async`, `asyncRewake`, `shell` |
| `http` | usługa produktu zbiera decyzje/dzienniki | POST z JSON-em; blokada tylko przez 2xx + JSON; `allowedHttpHookUrls`, `allowedEnvVars` dla nagłówków |
| `mcp_tool` | logika w serwerze MCP (np. poza piaskownicą) | `input` z podstawieniami `${tool_input.x}`; **pomijany na `SessionStart` przy starcie/wznowieniu i na `Setup`** |
| `prompt` | ocena treści przez model (np. czy zadanie skończone) | odpowiedź `{"ok", "reason", "impossible"}`; `continueOnBlock`; koszt wywołania modelu |
| `agent` | weryfikacja z użyciem narzędzi (eksperymentalne) | 60 s; zachowuje się jak `prompt` z `continueOnBlock: true` |

## Procedura

1. Wybierz zdarzenie i typ (tabele wyżej); sprawdź zdarzenie:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/szukaj.py" <zdarzenie> --typ hook --pelny`.
2. Napisz skrypt czytający JSON ze stdin i zwracający decyzję koderem JSON; polityka →
   `exit 2` albo JSON z decyzją; `chmod +x`.
3. Przetestuj offline: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/hooki/scripts/test_hooka.py" --zdarzenie PreToolUse --narzedzie Bash --wejscie '{"command":"rm -rf build"}' -- <polecenie hooka>`
   (podaje kod wyjścia, sposób interpretacji wyjścia i błędy pól JSON dla zdarzenia).
4. Wpisz do pliku ustawień właściwego zakresu (zespół → `.claude/settings.json`, osobiste →
   `~/.claude/settings.json`, produkt → `--settings`, wtyczka → `hooks/hooks.json`).
5. Zwaliduj: `waliduj_ustawienia.py --cli …` (zdarzenia, matcher, `if`, `mcp_tool` na starcie).
6. Sprawdź próbą w CLI: `proba_cli.py --scenariusz …` z `--include-hook-events` albo
   `proba_regul.py` dla `PreToolUse`/`PermissionRequest`; w sesji: `/hooks`, `--debug-file`,
   `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`.

## Pułapki

- `-p` i SDK traktują folder jak zaufany: **hooki z repozytorium wykonają się** bez
  pytania. Na cudzym repozytorium: `--settings '{"disableAllHooks": true}'` lub `--bare`.
- `disableAllHooks` z pliku nie wyłączy hooków zarządzanych; `allowManagedHooksOnly` (managed)
  wyłącza hooki użytkownika, projektu, local i wtyczek (poza wymuszonymi w managed).
- `Stop` odpala się po każdej odpowiedzi, nie przy przerwaniu; bez `stop_hook_active`
  hook zapętli turę do limitu 8 kolejnych kontynuacji (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
- Hooki `async` w `-p` są zabijane przy zakończeniu (wynik `cancelled`); ich `decision`
  nie ma skutku.
- Kilka hooków z `updatedInput` dla tego samego narzędzia — wygrywa ostatni (kolejność losowa).
- `updatedToolOutput` zmienia tylko to, co widzi model — narzędzie już się wykonało,
  telemetria widzi oryginał.
- `PermissionRequest` w dokumentacji opisany jako niedziałający w czystym `-p`, ale w
  próbie 2.1.286 hook zatwierdził i odrzucił wywołania w `-p` (także bez
  `--permission-prompts none`) — dla przenośności polityki rób to w `PreToolUse`.
- Podagenci: hooki z ustawień działają też w podagentach (pola `agent_id`, `agent_type`);
  `Stop` z frontmattera agenta zamienia się w `SubagentStop`; hooki frontmattera
  podagenta z projektu wymagają zaufania folderu (w `-p` nie działają).
- Hook bez katalogu roboczego (usunięty worktree) uruchomi się z katalogu zapasowego.
- `${CLAUDE_PROJECT_DIR}` zostaje w katalogu startu po wejściu do worktree — bieżący
  katalog w polu `cwd` wejścia.
- Ścieżka skryptu z literówką = cicha brama: błąd nieblokujący (`exit 127`), wywołanie przechodzi.

## Minimalne wersje (wybór)

| Funkcja | Wersja |
|---|---|
| `prompt_id` w wejściu | 2.1.196 |
| hook „allow” nie pomija zgody dla narzędzi MCP z `requiresUserInteraction` | 2.1.199 |
| `continueOnBlock`, zachowanie `prompt` na `PreToolUse` | 2.1.210 |
| exit 2 z błędnym JSON-em nadal blokuje | 2.1.214 |
| `classifierContext` | 2.1.236 |
| błąd parsowania JSON jako błąd nieblokujący | 2.1.248 |
| pola kosztu wznowienia w `SessionStart` | 2.1.251 |
| `scratchpad_dir` w wejściu | 2.1.257 |
| `StopFailure` z `cloud_credential_error` | 2.1.267 |

## Szablony (walidator, `claude doctor`, próba)

- `examples/straznik-zespolu.project.settings.json` + `blokuj_niebezpieczne.py` — `PreToolUse` dla Bash.
- `examples/kontekst-sesji.project.settings.json` + `kontekst_sesji.sh` — `SessionStart` z `CLAUDE_ENV_FILE`.
- `examples/weryfikacja-stop.project.settings.json` + `weryfikacja_stop.py` — `Stop` ze `stop_hook_active`.
- `examples/produkt-hooki.flaga.settings.json` — `http` do usługi, `mcp_tool` na `PreToolUse`, `PostModelSwitch`.
- `examples/ocena-modelem.user.settings.json` — hook `prompt` na `Stop`.
- `examples/hooks.json` — hooki wtyczki z formą exec i `${CLAUDE_PLUGIN_ROOT}`.

## Referencje

- `references/zdarzenia-i-decyzje.md` — 33 zdarzenia: kiedy, matcher, blokowanie, wzorzec decyzji, wejście.
- `references/typy-i-wykonanie.md` — pola typów, formy exec/shell, zmienne, async, zaufanie, polityki.
- `references/przepisy.md` — gotowe rozwiązania typowych potrzeb (z uzasadnieniem).
