---
name: uprawnienia-i-tryby
description: >
  Uprawnienia Claude Code: tryby (default/Manual, acceptEdits, plan, auto, dontAsk,
  bypassPermissions), tryb startowy sesji i -p, reguły allow/ask/deny i ich składnia
  (Bash, Read/Edit, WebFetch, MCP, Agent, parametry narzędzi), kolejność oceny, granice
  reguł Bash, polecenia tylko do odczytu, ścieżki chronione i krytyczne, katalogi robocze,
  tryb auto i klasyfikator (autoMode, koszt, kiedy nie), host uprawnień
  (--permission-prompt-tool, --permission-prompts, PermissionRequest), --restricted.
  Stosuj, gdy pada „zezwól na polecenie”, „zablokuj”, „dlaczego pyta”, „dlaczego odmówił”,
  „dontAsk”, „auto mode”, „klasyfikator”, „uprawnienia w CI/usłudze”. Granicą
  bezpieczeństwa jest piaskownica (`piaskownica-i-izolacja`), nie reguły.
---

# Uprawnienia, reguły i tryby

## Kiedy stosować

Gdy ustalasz, **co agent może zrobić bez pytania**, co ma być zawsze odrzucone i kto
odpowiada na pytania o zgodę (człowiek, host, nikt). Reguły i tryby egzekwuje CLI, nie
model — instrukcja w CLAUDE.md niczego nie blokuje.

## Decyzja: który tryb

| Sytuacja | Tryb | Dlaczego |
|---|---|---|
| praca interaktywna z przeglądem każdego kroku | `default` (etykieta Manual, alias `manual` ≥2.1.200) | pyta o wszystko poza odczytami |
| iteracja nad kodem, który przeglądasz | `acceptEdits` | edycje i `mkdir/touch/mv/cp/sed` w katalogach roboczych bez pytania |
| rozpoznanie przed zmianą | `plan` | blokuje edycje do akceptacji planu |
| długie zadania bez pytań, z kontrolą bezpieczeństwa | `auto` | klasyfikator przed akcją; koszt i opóźnienie (niżej) |
| **CI, usługa, produkt osadzający, każdy `-p` bez człowieka** | **`dontAsk`** | wszystko, co by pytało, jest odrzucane; działa tylko to, co dozwolone regułą lub hookiem — wynik deterministyczny |
| kontener/VM bez wartości do ochrony | `bypassPermissions` | tylko w izolacji; uruchamiaj jako nie-root |

**Zawsze podawaj tryb jawnie w `-p`.** Tryb wbudowany `-p` to `default`, ale w sesjach,
które nie pobierają flag funkcji (inny dostawca, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`,
`DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `DISABLE_GROWTHBOOK`), od **2.1.285 startuje w `auto`**.
Tryb startowy: flaga → `permissions.defaultMode` → wbudowany; `disableAutoMode: "disable"`
w dowolnym pliku sprowadza wbudowany do `default`.

## Kolejność oceny wywołania

1. `PreToolUse` hooki (mogą odrzucić, wymusić pytanie, zatwierdzić, zmienić wejście).
2. Reguły **deny → ask → allow** (pierwsze trafienie wygrywa; szczegółowość nie zmienia
   kolejności; `allow` nie wycina wyjątku z `deny`). Hook „allow” nie przebija deny ani ask.
3. Tryb (co zatwierdza bez reguły) i kontrole stałe: ścieżki chronione, ścieżki krytyczne
   (`rm -rf /`, `~`, katalog roboczy — nigdy auto, także przez allow i hook), polecenia
   wymagające człowieka (`AskUserQuestion`, MCP z `requiresUserInteraction`).
4. Gdy nic nie rozstrzygnęło: pytanie (człowiek, host przez `--permission-prompt-tool`
   lub SDK `canUseTool`, hook `PermissionRequest`); w `dontAsk` i bez hosta — odmowa.

Deny z gołą nazwą (`Bash`, `mcp__*`, `*`) **usuwa narzędzie z kontekstu** (wyjątek:
`EndConversation`, dopóki jest inne narzędzie). Deny z argumentem zostawia narzędzie
i odrzuca pasujące wywołania.

## Składnia reguł — skrót

| Reguła | Znaczenie |
|---|---|
| `Bash(npm run build)` | dokładnie to polecenie |
| `Bash(npm run *)` | rodzina; `*` dopasowuje dowolny tekst; końcowe ` *` łapie też samo `npm run` |
| `Bash(ls:*)` | to samo co `Bash(ls *)`; `:*` tylko na końcu |
| `Read(./.env)`, `Edit(/src/**)`, `Read(~/x)`, `Read(//etc/**)` | ścieżki w składni gitignore: `./`/brak = katalog bieżący, `/` = **źródło ustawień**, `~/` = dom, `//` = korzeń |
| `WebFetch(domain:*.example.com)` | domena (subdomeny dowolnej głębokości, bez samej domeny) |
| `mcp__serwer`, `mcp__serwer__*`, `mcp__serwer__narzedzie` | narzędzia MCP; **w plikach bez nawiasów** (reguła `mcp__…(…)` z pliku jest pomijana) |
| `Agent(Explore)`, `Agent(model:*)`, `Agent(isolation:*)` | typ podagenta; parametr wywołania (tylko deny/ask) |
| `Bash(run_in_background:true)` | parametr wejścia narzędzia (tylko deny/ask) |
| `Skill(skill:nazwa)` | skill pod każdą z jego nazw |
| `Cd(~/code/**)` | cele polecenia `/cd` |
| `*`, `mcp__*`, `B*` | glob nazwy narzędzia — tylko w deny/ask; w allow tylko po `mcp__<serwer>__` |

Pełne reguły dopasowania: `references/skladnia-regul.md`.

## Reguły Bash nie są granicą bezpieczeństwa

`Bash(curl *)` w deny zatrzyma `curl https://…`, ale nie `/usr/bin/curl …`, `sh -c 'curl …'`,
`git -C . push` ani `git -c … push`. Reguły dopasowują tekst polecenia po podziale na
podpolecenia (`&&`, `||`, `;`, `|`, `&`, nowa linia) i zdjęciu opakowań (`timeout`, `time`,
`nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob`, gołe `xargs`). Twardą granicę
dla sieci i plików daje **piaskownica** (`sandbox.network`, `sandbox.filesystem`) albo
izolacja całego procesu; reguły to „pas”, który zatrzymuje typową postać polecenia.

Polecenia tylko do odczytu (`ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`,
`which`, `diff`, `stat`, `du`, `cd`, odczytowe `git`) przechodzą bez pytania w **każdym**
trybie, także w `dontAsk` (próba 2.1.286: `echo` przeszło, `touch` odrzucone).
Przekierowanie `> plik` sprawdzane jest jak `Edit` celu, `< plik` jak `Read` (≥2.1.257),
cele `tee` jak `Edit` (≥2.1.269).

## Ścieżki chronione i krytyczne

Zapis do `.git`, `.claude` (poza `.claude/worktrees`), `.vscode`, `.idea`, `.husky`,
`.cargo`, `.devcontainer`, `.yarn`, `.mvn`, `.config/git`, katalogu z `--plugin-dir` oraz
plików `.bashrc`, `.zshrc`, `.profile`, `.gitconfig`, `.npmrc`, `.mcp.json`, `.claude.json`,
`.pre-commit-config.yaml` i innych (lista: `references/skladnia-regul.md`) **nigdy nie jest
zatwierdzany regułą allow**: `default`/`acceptEdits` pytają, `auto` pyta klasyfikator,
`dontAsk` odrzuca, `bypassPermissions` przepuszcza.

**Pułapka sprawdzona próbą:** katalog roboczy leżący **wewnątrz** `.claude/`
(np. `~/.claude/sesje/...`) czyni każdy zapis zapisem do ścieżki chronionej — w `dontAsk`
nawet `Bash` w allow nic nie przepuści. Katalogi robocze usług trzymaj poza `.claude`.

## Tryb auto i klasyfikator — kiedy tak, kiedy nie

- Klasyfikator to **druga bramka po regułach**, kontrola per akcja, nie granica izolacji.
  Wymaga obsługiwanego modelu; dodaje wywołania (na API/Enterprise liczone do zużycia)
  i opóźnienie przed akcją.
- Konfiguracja: `autoMode.environment` (proza: zaufane repozytoria, domeny, kubełki;
  zacznij od `"$defaults"`), `allow`/`soft_deny`/`hard_deny`; czytane z user, managed,
  `--settings` — **nie z plików projektu**. Podgląd: `claude auto-mode defaults`,
  `claude auto-mode config` (≥2.1.208), reset: `claude auto-mode reset` (≥2.1.212).
- Po 3 blokadach z rzędu lub 20 łącznie tryb auto przechodzi na pytania; w `-p` bez hosta
  akcja po prostu nie wykona się, a praca trwa.
- Usługa bez człowieka: zwykle **nie** — `dontAsk` + reguły + piaskownica daje wynik
  deterministyczny i tańszy. Zablokuj przypadkowe auto: `"disableAutoMode": "disable"`.
- Szczegóły: `references/tryb-auto-i-klasyfikator.md`.

## Kto odpowiada na pytanie o zgodę

| Mechanizm | Kiedy | Uwagi |
|---|---|---|
| człowiek w terminalu | interaktywnie | „Yes, and don't ask again” zapisuje regułę do `.claude/settings.local.json` w korzeniu repozytorium |
| `--permission-prompt-tool mcp__serwer__narzedzie` | `-p` z hostem (produkt) | CLI czeka na serwer do `MCP_TIMEOUT`; narzędzie zwraca JSON jak `PermissionResult` (`{"behavior":"allow","updatedInput":{…}}` / `{"behavior":"deny","message":"…"}`); nie zatwierdzi narzędzia z `requiresUserInteraction` (≥2.1.199) |
| SDK `canUseTool` | aplikacja na Agent SDK | odpowiedź po `control_request` w stream-json |
| hook `PermissionRequest` | każdy tryb | `decision.behavior` allow/deny, `updatedInput`, `updatedPermissions`; exit 2 ignorowany |
| `--permission-prompts none` (≥2.1.259) | nikt nie odpowie | odmowa bez czekania na hosta, model wie, by nie ponawiać; usuwa `AskUserQuestion`; odmowy w `permission_denials` wyniku |
| `dialogExpiry` | host SDK | czas na odpowiedź na dialog |

## Procedura

1. Ustal tryb z tabeli decyzji; w `-p` podaj `--permission-mode` jawnie.
2. Spisz **allow** dla tego, co ma przechodzić bez pytania (najwęższe formy, `*` po
   podpoleceniu), **ask** dla tego, co zawsze wymaga potwierdzenia, **deny** dla zakazów
   (pliki z sekretami, `Agent(model:*)`, `Agent(isolation:*)`, publikacja, push).
3. Zdecyduj, kto odpowiada na pytania (tabela wyżej); bez hosta: `--permission-prompts none`.
4. Zablokuj tryby niechciane: `permissions.disableBypassPermissionsMode: "disable"`,
   `disableAutoMode: "disable"` (w managed — nie do zdjęcia).
5. Zwaliduj reguły: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/uprawnienia-i-tryby/scripts/sprawdz_reguly.py" --plik <settings.json>`
   (składnia, reguły pomijane przez CLI, glob w allow, główne pola, kotwice ścieżek).
6. Sprawdź **próbą**, czy konkretne polecenie przejdzie:
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/uprawnienia-i-tryby/scripts/proba_regul.py" --settings <plik> --tryb dontAsk --bash "git push origin main"`
   (atrapa API zleca wywołanie `Bash`; wynik: przepuszczone / odrzucone + powód).
7. Granicę dla sieci i plików postaw piaskownicą (`piaskownica-i-izolacja`).

## Pułapki

- Goła nazwa `Edit` w allow/deny obejmuje **tylko narzędzie Edit** — `Write` nie jest nią
  zatwierdzany ani blokowany (próba 2.1.286). Dla wszystkich narzędzi edytujących: `Edit(./**)`
  (lub `Edit(**)`), albo pary `"Edit", "Write"`.
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` wymusza tryb `default` niezależnie od `--permission-mode`
  i `defaultMode` (próba 2.1.286; stderr „Permission mode forced to default”) — w `-p` działa jak
  `dontAsk` z listą allow, `acceptEdits`/`auto`/`bypassPermissions` przepadają.

- `--allowed-tools`/`--disallowed-tools` przyjmują **wiele wartości** — prompt podany po
  nich zostaje połknięty jako reguła („Input must be provided…”). Prompt dawaj zaraz po
  `-p`, przez stdin albo po `--`.
- Polecenie z rozwinięciem zmiennej (`echo $X`, `cat "$PLIK"`) nie pasuje do reguły allow
  i nie jest „tylko do odczytu” — w `dontAsk` odmowa (próba 2.1.286: „Contains
  simple_expansion”). Allow działa na polecenia z literałami.
- `--allowed-tools` nie ogranicza zestawu narzędzi — do tego jest `--tools`. Allow tylko
  pre-zatwierdza.
- W `-p` reguły allow ze wspólnego `.claude/settings.json` niezaufanego folderu są
  **pomijane** (stderr: „workspace has not been trusted”), a hooki z tego pliku działają.
- `defaultMode: "auto"`/`"bypassPermissions"` w pliku projektu nie działa.
- `Bash(git *)` zatwierdza każde podpolecenie gita; `Bash(git * main)` — z opcjami typu
  `-c core.fsmonitor=…` włącznie (CLI ostrzega przy starcie).
- `Write(...)`, `Glob(...)`, `NotebookEdit(...)` z wzorcem ścieżki — nigdy nie
  sprawdzane; używaj `Edit(...)` (deny `Read` blokuje też zapis tej ścieżki ≥2.1.228).
- `Read(/etc/passwd)` w `~/.claude/settings.json` to `~/.claude/etc/passwd`; korzeń to `//`.
- Reguła `Bash(command:rm *)` (główne pole) jest ignorowana z ostrzeżeniem.
- `WebFetch` w allow nie zmienia listy domen piaskownicy; `WebFetch(domain:*)` — zmienia.
- Odmowy liczą się w `dontAsk` także dla ścieżek chronionych: `.mcp.json` czy `.claude/`
  nie zapiszesz bez `bypassPermissions`.
- `--add-dir` daje dostęp do plików, nie wczytuje `.claude/` z tego katalogu (poza skillami).

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `--permission-prompt-tool` odmawia dla `requiresUserInteraction` | 2.1.199 |
| alias `manual` | 2.1.200 |
| wbudowane `auto` w terminalu | 2.1.228 (Windows 2.1.233); 2.1.283 dla wszystkich planów |
| `--restricted` | 2.1.248 |
| `bypassPermissions` ignorowany z projektu, `blockReadsOutsideWorkingDirectories`, sprawdzanie `< plik` | 2.1.257 |
| `--permission-prompts` | 2.1.259 |
| `-p` bez flag funkcji startuje w `auto` | 2.1.285 |

## Szablony (sprawdzone walidatorem, `claude doctor` i próbą)

- `examples/ci-dokladna-lista.flaga.settings.json` — CI: `dontAsk`, dokładna lista.
- `examples/usluga-czat.flaga.settings.json` — produkt bez narzędzi kodu.
- `examples/zespol-acceptedits.project.settings.json` — zespół: allow/ask/deny.
- `examples/tryb-auto-srodowisko.user.settings.json` — tryb auto z opisem infrastruktury.
- `examples/hook-zgody.flaga.settings.json` — hook `PermissionRequest` jako host zgód.
- `examples/zgoda.py` — skrypt hooka `PermissionRequest` (polityka w kodzie).

## Referencje

- `references/skladnia-regul.md` — pełna składnia i dopasowanie reguł, ścieżki chronione, katalogi robocze.
- `references/tryb-auto-i-klasyfikator.md` — tryby szczegółowo, klasyfikator, `autoMode`, `--restricted`.
- `references/host-uprawnien.md` — `--permission-prompt-tool`, `PermissionRequest`, `canUseTool`, `--permission-prompts`.
