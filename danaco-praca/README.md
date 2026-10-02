# danaco-praca

Wtyczka Claude Code z poleceniami „/”, którymi właściciel steruje trybem pracy agenta.
Polecenia nie są prośbą w instrukcji: stan zapisuje hook, a każdą regułę egzekwują hooki
`PreToolUse` i `Stop`. Do tego wtyczka niesie dwie twarde zasady serwera Danaco: straż
sekretów i straż dysku systemowego.

Wersja 5.1.0. Pełny opis zmian w `CHANGELOG.md` (5.1.0 — komendy sesji, nowe blokady,
nowa konwencja nazw; 5.0.0 — przebudowa od podstaw względem 4.7.0).

## Konwencja nazw

Jedna zasada dla wszystkich blokad: **`/<temat>-blokuj`** włącza blokadę,
**`/<temat>-odblokuj`** ją zdejmuje. Tryb pracy ciągłej ma własną, naturalną nazwę
(`/praca` ↔ `/koniec-pracy`), bo jest trybem, nie blokadą. Polecenia stanu i sesji są
pojedyncze (`/tryb`, `/dziennik`, `/wyczysc-tryby`, `/sesja-id`, `/sesje`, `/przejmij`).

## Polecenia

### Tryb pracy

| Polecenie | Przeciwne | Co egzekwuje hook |
| --- | --- | --- |
| `/praca [zlecenie]` | `/koniec-pracy` | Praca ciągła agenta głównego: `Stop` odrzuca zakończenie tury z przypomnieniem zlecenia; odrzucane jest czekanie na pierwszym planie (`sleep`, `wait`, pętle oczekiwania), `ScheduleWakeup`, `CronCreate` i blokujący odbiór wyniku. Procesy, agenci i monitoring (także narzędzie `Monitor`) wolno uruchamiać. Podagenci oddają wynik normalnie. Bez innych ograniczeń narzędzi i miejsc zapisu. |

### Blokady (para `/<temat>-blokuj` ↔ `/<temat>-odblokuj`)

| Temat | Blokuje | Zwalnia | Co egzekwuje hook |
| --- | --- | --- | --- |
| Bash | `/bash-blokuj` | `/bash-odblokuj` | narzędzia `Bash`, `PowerShell`, `Monitor` i narzędzia MCP wykonujące polecenia powłoki |
| Python | `/python-blokuj` | `/python-odblokuj` | `python`, `python3`, `pip`, `uv run`, `uvx`, `pytest`, `poetry run` i pokrewne, skrypty `.py` i pliki z interpreterem Pythona, zapis `.py` przekierowaniem i `tee`, tworzenie `.py` narzędziem `Write` oraz `NotebookEdit` (edycja istniejącego `.py` narzędziem `Edit` przechodzi) |
| Praca masowa | `/masowe-blokuj` | `/masowe-odblokuj` | edytory w miejscu na więcej niż jednym pliku, z maską albo rekurencyjnie; `find -exec`/`-delete`; `xargs`/`parallel` z zapisem; pętle po plikach z zapisem; kod i skrypty zapisujące w pętli; `patch`, `git apply`, `git reset --hard`, `git checkout .`; `UPDATE`/`DELETE` bez `WHERE` |
| Pisanie ręczne | `/skrypty-blokuj` | `/skrypty-odblokuj` | generowanie treści poleceniem lub skryptem: przekierowania i `tee` do plików (poza `.log`/`.out`/`.err`, `/tmp`, `$TMPDIR`), edytory w miejscu, `patch`, `truncate`, `dd of=`, kod i skrypty zapisujące pliki. Pliki zmienia się narzędziami `Edit`/`Write` |
| Uśpienie | `/sleep-blokuj` | `/sleep-odblokuj` | `sleep`, `timeout … sleep`, `wait`, `tail -f`, `watch`, pętle oczekiwania i odpytywania, uśpienie w kodzie, `ScheduleWakeup`, `Monitor`, `CronCreate`, blokujący odbiór wyniku — także w tle (poza pętlą monitoringu z dziennikiem) i poza trybem pracy. Ściślej niż sam `/praca` |
| Podagenci | `/podagenci-blokuj` | `/podagenci-odblokuj` | narzędzia `Agent`, `Task`, `Workflow`, `TeamCreate` oraz `claude -p` i `codex exec` |
| sudo | `/sudo-blokuj` | `/sudo-odblokuj` | `sudo`, `doas`, `pkexec`, `run0`, `su -c` (także w `ssh host '…'`, `bash -c '…'`, `find -exec`). Domyślnie sudo zgodnie z kontem |
| Sieć | `/siec-blokuj` | `/siec-odblokuj` | narzędzia `WebFetch`, `WebSearch` oraz w powłoce `curl`, `wget`, `nc`, `ssh`, `scp`, `sftp`, zdalny `rsync`, `git clone`/`fetch`/`pull`/`push` i pobieranie menedżerami pakietów (`pip`/`npm`/`uv`/`cargo`/`hf` install/download) |
| Zapis plików (tylko-odczyt) | `/zapis-blokuj` | `/zapis-odblokuj` | narzędzia `Write`, `Edit`, `MultiEdit`, `NotebookEdit` oraz w powłoce każda zmiana plików (`rm`, `mv`, `cp`, `mkdir`, `touch`, `tee`, przekierowania poza `/tmp`/`$TMPDIR`/dziennikami, edytory w miejscu, `git commit`/`add`/`reset`/`checkout`…). Odczyt, analiza i budowa przechodzą |
| Pytania | `/pytania-blokuj` | `/pytania-odblokuj` | narzędzia `AskUserQuestion` i `ExitPlanMode` — agent przyjmuje najrozsądniejsze założenie i pracuje dalej |

### Stan i sesje

| Polecenie | Działanie |
| --- | --- |
| `/tryb` | tabela stanu trybu pracy i wszystkich blokad tej sesji, pokazana właścicielowi bez angażowania modelu |
| `/dziennik` | ostatnie wpisy dziennika tej sesji: polecenia, odmowy hooka, zadziałania bezpiecznika |
| `/wyczysc-tryby` | zdejmuje naraz tryb pracy ciągłej i wszystkie blokady tej sesji |
| `/sesja-id` | wypisuje identyfikator bieżącej sesji (do skopiowania) |
| `/sesje` | lista ostatnich sesji obu kont właściciela (`danaco-przejmij-sesje --lista`) |
| `/przejmij <id>` | przygotowuje przejęcie wskazanej sesji (`danaco-przejmij-sesje <id>`) i podaje gotowe polecenie `claude --resume` do wklejenia w terminalu |

Każde polecenie działa też z prefiksem `/danaco-praca:` i liczy się wyłącznie na
początku wiersza wiadomości; kilka poleceń można wydać naraz, każde w osobnym wierszu.
Wzmianka w zdaniu („opisz /koniec-pracy”) ani ścieżka (`skills/praca/SKILL.md`) niczego
nie przełącza. Sama komenda (bez zadania dla agenta) nie uruchamia modelu — hook pokazuje
właścicielowi wynik i blokuje turę; `/koniec-pracy` i `/praca <zlecenie>` przepuszczają
turę, żeby model złożył raport albo zaczął pracę.

## Przejmowanie sesji

`/sesja-id` pokazuje identyfikator bieżącej sesji, a `/sesje` — spis sesji obu kont
właściciela do przejęcia. `/przejmij <id>` jest cienką nakładką na systemowe
`danaco-przejmij-sesje`: hook uruchamia przygotowanie przejęcia i pokazuje właścicielowi
gotowe `cd <katalog> && claude --resume <id>`. Samego `claude --resume` hook nie odpala —
nie ma dostępu do terminala — więc polecenie wkleja właściciel. Identyfikator jest
sprawdzany wzorcem (`[A-Za-z0-9 _.-]`), żeby nie dało się nim wstrzyknąć polecenia powłoki.

## Kto przełącza tryby

Wyłącznie właściciel, i to na trzech poziomach:

1. Każdy skill polecenia ma `disable-model-invocation: true` — klient odmawia wywołania go
   narzędziem `Skill`.
2. Stan zapisuje hook `UserPromptSubmit`, czyli zdarzenie, które powstaje tylko z wiadomości
   wpisanej przez człowieka. Treść skilla jedynie informuje model o zmianie.
3. Hook `PreToolUse` odrzuca:
   - każde wywołanie narzędzia, którego wejście wskazuje katalog stanu (odczyt i zapis,
     także `$CLAUDE_PLUGIN_DATA` i maskę `plugins/data/danaco-p*`);
   - narzędzie `Skill`/`SlashCommand` z poleceniem wtyczki;
   - polecenie powłoki albo narzędzie wysyłające wiadomość, które zawiera polecenie
     wtyczki (`/koniec-pracy`, `/bash-odblokuj`, `/przejmij` …) — droga podrzucenia promptu;
   - przy aktywnym trybie lub blokadzie: `claude --resume/--continue` z wnętrza sesji,
     zapis w plikach wtyczki i w `settings.json`, `disableAllHooks`,
     `claude plugin disable|uninstall`.

## Stan

Stan jest osobny dla każdej sesji (identyfikator `session_id` z wejścia hooka; podagenci
dziedziczą stan sesji głównej). Leży w `${CLAUDE_PLUGIN_DATA}/stan`
(`~/.claude/plugins/data/danaco-praca-danaco/stan` po instalacji z marketplace):

| Plik | Rola |
| --- | --- |
| `sesje/<sesja>.json` | stan sesji z podpisem HMAC-SHA256 (0600) |
| `dziennik.jsonl` | każda zmiana stanu z podpisaną migawką, odmowy hooka, zadziałania bezpiecznika i naruszenia stanu; po 5 MB przechodzi do `dziennik.jsonl.1` |
| `klucz` | klucz HMAC (0600), zakładany przy pierwszym użyciu |
| `blokada` | blokada `fcntl` dla zapisów równoległych |

Plik stanu zmieniony albo skasowany poza hookiem (podpis się nie zgadza albo pliku brak)
jest odtwarzany z ostatniej podpisanej migawki tej sesji w dzienniku, a w dzienniku
zostaje wpis `naruszenie-stanu`. Skasowanie pliku nie zwalnia więc żadnej blokady.

## Praca ciągła i bezpiecznik pętli

Przy włączonym `/praca` hook `Stop` odpowiada `decision: block` z przypomnieniem
zlecenia. Tryb wiąże wyłącznie agenta głównego: podagent oddaje wynik od razu
(`SubagentStop` nie jest blokowany — decyzja właściciela z 2026-10-02), a `SubagentStart`
mówi mu o tym. Agent może uruchamiać procesy i agentów w tle i stawiać monitoring, także
narzędziem `Monitor`, ale sam nie czeka.

Bezpiecznik: każde wywołanie narzędzia agenta głównego zeruje licznik prób zakończenia.
Gdy agent trzy razy z rzędu próbuje zakończyć turę bez żadnego wywołania narzędzia,
czwarta próba przechodzi, a właściciel dostaje komunikat (`systemMessage`), że pętla
została przerwana, a tryb trwa. Limit zmienia `DANACO_PRACA_LIMIT_PETLI` (domyślnie 3).
Wiadomość właściciela zeruje licznik.

Klient ma własny limit kolejnych blokad `Stop` (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`,
domyślnie 8). Próba na żywo (2.1.287) pokazała, że wywołanie narzędzia go zeruje: tura
z 12 blokadami przeplatanymi pracą trwała dalej. Bezpiecznik wtyczki (3) działa przed nim.

Czekanie a praca w tle: w samym `/praca` polecenie uruchomione w tle (`run_in_background`
albo `… &`) przechodzi zawsze — to proces albo monitoring, a agent pracuje dalej.
Odrzucane jest czekanie na pierwszym planie. Ściślejsza blokada `/sleep-blokuj` odrzuca także
`sleep`, `wait` i pętle odpytujące w tle oraz narzędzie `Monitor`; przechodzi wtedy tylko
pętla monitoringu w tle, która dopisuje do dziennika (`>>`).

## Hooki

| Zdarzenie | Tryb | Rola |
| --- | --- | --- |
| `UserPromptSubmit` | `prompt` | Rozpoznaje polecenia, zapisuje stan i dziennik, podaje modelowi nowy stan (`additionalContext`), właścicielowi potwierdzenie (`systemMessage`); `/tryb` pokazuje tabelę przez `decision: block`. Zwykła wiadomość zeruje liczniki pętli. |
| `PreToolUse` (`*`) | `narzedzie` | Ochrona stanu i mechanizmu, blokady sesji, straż sekretów, straż dysku. |
| `Stop` | `stop` | Praca ciągła agenta głównego i bezpiecznik pętli. |
| `SessionStart`, `SubagentStart` | `sesja` | Po kompakcji i wznowieniu przypomina aktywne tryby; podagentowi mówi, które blokady go wiążą i że oddaje wynik normalnie; bez aktywnych trybów milczy. |

Wszystkie wołają `hooks/hak.sh <tryb>` → `/usr/bin/python3 scripts/hak.py <tryb>`.
Brak interpretera albo skryptu kończy hook kodem 0 z komunikatem (fail-open); każdy
wyjątek w hooku też — usterka wtyczki nie zamyka sesji. Decyzje idą wyłącznie przez JSON.

Wtyczka nie wstrzykuje zasad serwera ani `CLAUDE.md` (robi to `danaco-zasady-hook`
w ustawieniach kont) i nie prowadzi katalogów sesji (`danaco-sesja-hook`).

## Twarde zasady serwera

- **Straż sekretów** (`scripts/straz_sekretow.py`, `Bash`): odmowa wypisania sekretu,
  pytanie o zgodę przy operacji nieodwracalnej. Zawsze.
- **Straż dysku systemowego** (`scripts/straz_dysku.py`, `Bash` i `Write`): odmowa zapisu
  danych na `/` poza `/etc`, `/usr/local/sbin`, `/usr/local/bin`, z podpowiedzią miejsca na
  `/danaco`. Bez dublowania: gdy `settings.json` konta albo ustawienia zarządzane
  rejestrują już `danaco-straz-dysku-hook`, wtyczka milczy. `DANACO_PRACA_STRAZ_DYSKU=wtyczka`
  wymusza straż wtyczki, `=system` ją wyłącza.
- Kosz zamiast kasowania i straż pakietów działają na poziomie serwera (nakładka `rm`,
  hook zarządzany `danaco-straz-pakietow-claude`); wtyczka ich nie zmienia.

## Ograniczenia

Rozbiór poleceń powłoki jest heurystyczny: rozpoznaje typowe postaci (także w `bash -c`,
`ssh host '…'`, `$(…)`, `find -exec`, `xargs`, heredocu do interpretera i w treści
uruchamianego pliku skryptu do 512 kB), nie każdą możliwą. Model z uprawnieniami roota
może w zasadzie obejść każdy lokalny hook; wtyczka zamyka znane drogi i każdą próbę zapisuje
w dzienniku. Budowa projektów (`make`, `npm run build`) nie jest analizowana pod kątem
`/masowe-blokuj` i `/skrypty-blokuj`.

## Struktura

```
.claude-plugin/plugin.json   manifest (5.0.0)
hooks/hooks.json             rejestracja pięciu zdarzeń
hooks/hak.sh                 wrapper POSIX sh, fail-open
scripts/hak.py               obsługa zdarzeń: prompt, narzedzie, stop, sesja
scripts/polecenia.py         polecenia właściciela i ich rozpoznanie
scripts/stan.py              stan sesji: podpis HMAC, dziennik, odtwarzanie
scripts/reguly.py            rozbiór poleceń powłoki i reguły blokad
scripts/straz_sekretow.py    straż sekretów (74 przypadki --test)
scripts/straz_dysku.py       straż dysku systemowego (48 przypadków --test)
skills/<polecenie>/SKILL.md  28 poleceń z disable-model-invocation
tests/test_hooki.py          testy hooków i poleceń na wejściach JSON
tests/proba_na_zywo.py       próba na prawdziwym kliencie z atrapą API
tests/atrapa_api.py          atrapa Messages API (scenariusz odpowiedzi)
tests/uruchom_testy.sh       cały zestaw automatyczny
```

## Testy

```bash
sh tests/uruchom_testy.sh                          # unittest + wbudowane przypadki straży + walidacja
claude plugin validate --strict .
python3 tests/proba_na_zywo.py <katalog-wynikow>   # klient Claude Code z --plugin-dir na atrapie API
```

Wymagania: `/usr/bin/python3` (3.10+) i POSIX `sh`.

## Licencja

Patrz plik `LICENSE`.
