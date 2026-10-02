# danaco-praca

Wtyczka Claude Code z poleceniami „/”, którymi właściciel steruje trybem pracy agenta.
Polecenia nie są prośbą w instrukcji: stan zapisuje hook, a każdą regułę egzekwują hooki
`PreToolUse` i `Stop`. Do tego wtyczka niesie dwie twarde zasady serwera Danaco: straż
sekretów i straż dysku systemowego.

Wersja 5.3.0. Pełny opis zmian w `CHANGELOG.md` (5.3.0 — tryb pracy oddaje turę właścicielowi,
twarde zasady obejmują każde narzędzie, hartowanie stanu i reguł; 5.2.0 — nazwy z czasownikiem
na początku; 5.1.0 — komendy sesji i nowe blokady; 5.0.0 — przebudowa od podstaw).

## Czym są hooki w tej wtyczce

Hooki Claude Code to **warstwa sterowania trybami i warstwa pomocnicza, nie szczelna bariera**.
Model z uprawnieniami roota może w zasadzie obejść każdy lokalny hook, a rozbiór poleceń powłoki
jest heurystyczny — rozpoznaje typowe postaci, nie każdą. Dwie rzeczy są jednak realną ochroną,
nie tylko podpowiedzią: **straż sekretów** (sekret nie trafia na ekran ani do rozmowy) i **straż
dysku** (dane nie lądują na dysku systemowym). Obie działają dla każdego narzędzia i każdą
zablokowaną próbę zapisują w dzienniku stanu.

## Konwencja nazw

Czasownik stoi na początku, żeby menu kontekstowe grupowało polecenia po przedrostku.
Blokady to pary **`/blokuj-<temat>`** ↔ **`/odblokuj-<temat>`**. Polecenia stanu mają przedrostek
**`/tryb`** (`/tryb`, `/tryb-dziennik`, `/tryb-wyczysc`), a sesji **`/sesja-`** (`/sesja-id`,
`/sesja-lista`, `/sesja-przejmij`). Tryb pracy ciągłej ma własną, naturalną nazwę (`/praca` ↔
`/koniec-pracy`), bo jest trybem, nie blokadą.

## Polecenia

### Tryb pracy

| Polecenie | Przeciwne | Co egzekwuje hook |
| --- | --- | --- |
| `/praca [zlecenie]` | `/koniec-pracy` | Praca ciągła agenta głównego: `Stop` nie pozwala agentowi zakończyć tury z własnej woli (przypomina zlecenie), ale co pewien czas sam oddaje turę, żeby właściciel mógł wpisać wiadomość. Odrzucane jest czekanie (`sleep`, `wait`, pętle oczekiwania), `ScheduleWakeup`, `CronCreate` i blokujący odbiór wyniku. Procesy, agenci i monitoring (także narzędzie `Monitor`) wolno uruchamiać. Podagenci oddają wynik normalnie. Bez innych ograniczeń narzędzi i miejsc zapisu. |

### Blokady (para `/blokuj-<temat>` ↔ `/odblokuj-<temat>`)

| Temat | Blokuje | Zwalnia | Co egzekwuje hook |
| --- | --- | --- | --- |
| Bash | `/blokuj-bash` | `/odblokuj-bash` | narzędzia `Bash`, `PowerShell`, `Monitor` i narzędzia MCP wykonujące polecenia powłoki (w tym `uruchom` serwera `danaco-programy`, pole `polecenie`) |
| Python | `/blokuj-python` | `/odblokuj-python` | `python`, `python3`, `pip`, `uv run`, `uvx`, `pytest`, `poetry run` i pokrewne, skrypty `.py` i pliki z interpreterem Pythona, zapis `.py` przekierowaniem i `tee`, tworzenie `.py` narzędziem `Write` oraz `NotebookEdit` (edycja istniejącego `.py` narzędziem `Edit` przechodzi) |
| Praca masowa | `/blokuj-masowe` | `/odblokuj-masowe` | edytory w miejscu na więcej niż jednym pliku, z maską albo rekurencyjnie; `find -exec`/`-delete`; `xargs`/`parallel` z zapisem; pętle po plikach z zapisem; kod i skrypty zapisujące w pętli; `patch`, `git apply`, `git reset --hard`, `git checkout .`; `UPDATE`/`DELETE` bez `WHERE` |
| Pisanie ręczne | `/blokuj-skrypty` | `/odblokuj-skrypty` | generowanie treści poleceniem lub skryptem: przekierowania i `tee` do plików (poza `.log`/`.out`/`.err`, `/tmp`, `$TMPDIR`), edytory w miejscu, `patch`, `truncate`, `dd of=`, kod i skrypty zapisujące pliki. Pliki zmienia się narzędziami `Edit`/`Write` |
| Uśpienie | `/blokuj-sleep` | `/odblokuj-sleep` | `sleep`, `timeout … sleep`, `wait`, `tail -f`, `watch`, pętle oczekiwania i odpytywania, uśpienie w kodzie, `ScheduleWakeup`, `Monitor`, `CronCreate`, blokujący odbiór wyniku — także w tle (poza pętlą monitoringu z dziennikiem) i poza trybem pracy. Ściślej niż sam `/praca` |
| Podagenci | `/blokuj-podagenci` | `/odblokuj-podagenci` | narzędzia `Agent`, `Task`, `Workflow`, `TeamCreate` oraz `claude -p` i `codex exec` |
| sudo | `/blokuj-sudo` | `/odblokuj-sudo` | `sudo`, `doas`, `pkexec`, `run0`, `su -c` (także w `ssh host '…'`, `bash -c '…'`, `find -exec`). Domyślnie sudo zgodnie z kontem |
| Sieć | `/blokuj-siec` | `/odblokuj-siec` | narzędzia `WebFetch`, `WebSearch` oraz w powłoce `curl`, `wget`, `nc`, `ssh`, `scp`, `sftp`, zdalny `rsync`, `git clone`/`fetch`/`pull`/`push` i pobieranie menedżerami pakietów (`pip`/`npm`/`uv`/`cargo`/`hf` install/download) |
| Zapis plików (tylko-odczyt) | `/blokuj-zapis` | `/odblokuj-zapis` | narzędzia `Write`, `Edit`, `MultiEdit`, `NotebookEdit` oraz w powłoce każda zmiana plików (`rm`, `mv`, `cp`, `mkdir`, `touch`, `tee`, przekierowania poza `/tmp`/`$TMPDIR`/dziennikami, edytory w miejscu, `git commit`/`add`/`reset`/`checkout`…). Odczyt, analiza i budowa przechodzą |
| Pytania | `/blokuj-pytania` | `/odblokuj-pytania` | narzędzia `AskUserQuestion` i `ExitPlanMode` — agent przyjmuje najrozsądniejsze założenie i pracuje dalej |

### Stan (przedrostek `/tryb`) i sesje (przedrostek `/sesja-`)

| Polecenie | Działanie |
| --- | --- |
| `/tryb` | tabela stanu trybu pracy i wszystkich blokad tej sesji, pokazana właścicielowi bez angażowania modelu |
| `/tryb-dziennik` | ostatnie wpisy dziennika tej sesji: polecenia, odmowy hooka, oddania tury, naruszenia stanu |
| `/tryb-wyczysc` | zdejmuje naraz tryb pracy ciągłej i wszystkie blokady tej sesji |
| `/sesja-id` | wypisuje identyfikator bieżącej sesji (do skopiowania) |
| `/sesja-lista` | lista ostatnich sesji obu kont właściciela (`danaco-przejmij-sesje --lista`) |
| `/sesja-przejmij <id>` | przygotowuje przejęcie wskazanej sesji i podaje gotowe polecenie `claude --resume` do wklejenia w terminalu |

Każde polecenie działa też z prefiksem `/danaco-praca:` i liczy się wyłącznie na początku
wiersza wiadomości; kilka poleceń można wydać naraz, każde w osobnym wierszu. Wzmianka w zdaniu
(„opisz /koniec-pracy”) ani ścieżka (`skills/praca/SKILL.md`, `ls /praca`) niczego nie przełącza.
Sama komenda (bez zadania dla agenta) nie uruchamia modelu — hook pokazuje właścicielowi wynik
i blokuje turę; `/koniec-pracy` i `/praca <zlecenie>` przepuszczają turę, żeby model złożył raport
albo zaczął pracę.

## Praca ciągła i oddawanie tury właścicielowi

Przy włączonym `/praca` hook `Stop` odpowiada `decision: block` z przypomnieniem zlecenia, więc
agent nie kończy tury z własnej woli. Tryb **wyłącza wyłącznie** właściciel poleceniem
`/koniec-pracy` — nie ma „awaryjnego wyjścia” dla samego agenta.

Żeby trzymanie tury nie odcięło właściciela od rozmowy, hook `Stop` **okresowo sam oddaje turę**:

- Gdy klient przekaże hookowi, że właściciel ma nieobsłużoną wiadomość w kolejce, hook oddaje
  turę od razu — wiadomość zostaje odczytana natychmiast. Klient Claude Code 2.1.287 takiej
  informacji hookowi `Stop` nie przekazuje, więc działa mechanizm zastępczy niżej.
- Mechanizm zastępczy: co `DANACO_PRACA_PROG_ODDANIA` kolejnych prób zakończenia (domyślnie 6)
  hook jednorazowo pozwala turze się skończyć i pokazuje właścicielowi komunikat
  (`systemMessage`). To **nie wyłącza trybu** — `/praca` zostaje włączone, a praca ciągła wznawia
  się na następnej turze: wiadomość właściciela (`UserPromptSubmit`) lub wznowienie sesji
  (`SessionStart`) przypomina modelowi, że ma pracować dalej. Samo „kontynuuj” wystarczy.

Dzięki temu właściciel **zawsze** może wysłać wiadomość i zostanie ona odczytana, a agent po jej
obsłużeniu wraca do zlecenia. Licznik oddań zeruje każda wiadomość właściciela oraz samo oddanie
tury. Tryb wiąże wyłącznie agenta głównego: podagent oddaje wynik od razu (`SubagentStop` nie jest
blokowany — decyzja właściciela z 2026-10-02), a `SubagentStart` mówi mu o tym.

Czekanie a praca w tle: w samym `/praca` polecenie uruchomione w tle (`run_in_background` albo
`… &`) przechodzi zawsze — to proces albo monitoring, a agent pracuje dalej. Odrzucane jest
czekanie na pierwszym planie. Ściślejsza blokada `/blokuj-sleep` odrzuca także `sleep`, `wait`
i pętle odpytujące w tle oraz narzędzie `Monitor`; przechodzi wtedy tylko pętla monitoringu w tle
dopisująca do dziennika (`>>`).

## Kto przełącza tryby

Wyłącznie właściciel, i to na trzech poziomach:

1. Każdy skill polecenia ma `disable-model-invocation: true` — klient odmawia wywołania go
   narzędziem `Skill`.
2. Stan zapisuje hook `UserPromptSubmit`, czyli zdarzenie, które powstaje tylko z wiadomości
   wpisanej przez człowieka. Treść skilla jedynie informuje model o zmianie.
3. Hook `PreToolUse` odrzuca:
   - każde wywołanie narzędzia, którego wejście wskazuje katalog stanu wtyczki (odczyt i zapis);
   - narzędzie `Skill`/`SlashCommand` z poleceniem wtyczki (nazwa normalizowana: wielkość liter,
     prefiks, odstęp i argument nie pomagają obejść);
   - **samodzielne** polecenie wtyczki (cały wiersz) podrzucone narzędziem wysyłającym wiadomość
     albo polecenie powłoki, które podaje takie polecenie agentowi (`claude`/`codex`) — droga
     podrzucenia promptu. Wzmianka w ścieżce czy w komunikacie commita nią nie jest;
   - przy aktywnym trybie lub blokadzie: `claude --resume/--continue` z wnętrza sesji, zapis
     w plikach wtyczki i w `settings.json`, `disableAllHooks`, `claude plugin disable|uninstall`.

## Stan

Stan jest osobny dla każdej sesji (identyfikator `session_id` z wejścia hooka; podagenci dziedziczą
stan sesji głównej). Leży w katalogu danych wtyczki, **poza zasięgiem modelu** — każde wywołanie
narzędzia wskazujące ten katalog odrzuca `PreToolUse`, a komunikat odmowy nie zdradza ścieżki ani
nazwy pliku klucza. Na stan składa się podpisany HMAC-SHA256 plik sesji (0600), dziennik zmian
(`dziennik.jsonl` z podpisaną migawką każdej zmiany, odmowami, oddaniami tury i naruszeniami
stanu) oraz klucz HMAC i plik blokady `fcntl`.

Stan jest odporny na zniknięcie i uszkodzenie:

- Plik sesji zmieniony albo skasowany poza hookiem (podpis się nie zgadza albo pliku brak) wraca
  z ostatniej podpisanej migawki w dzienniku, a w dzienniku zostaje wpis `naruszenie-stanu`.
- Gdy stanu **nie da się zweryfikować** (utracony albo obcięty klucz lub podpis), hook nie zdejmuje
  blokad po cichu: odtwarza ostatnią odczytywalną migawkę sesji, a gdy jej brak — przechodzi w
  stan maksymalnie ograniczający (tryb pracy i wszystkie blokady włączone), z wpisem
  `stan-bezpieczny`. Zdjąć go może tylko właściciel (`/koniec-pracy`, `/odblokuj-…`, `/tryb-wyczysc`).
  Sam wpis w dzienniku bez zapisanej migawki (np. odmowa) nie liczy się jako stan — sesja, która
  nigdy nie miała trybu, wraca pusta.
- Zapisy pliku sesji i klucza są atomowe (plik tymczasowy + `os.replace`), więc obcięty klucz jest
  naprawiany bez błędu, a równoległe zapisy nie zostawiają połówek.

## Hooki

| Zdarzenie | Tryb | Rola |
| --- | --- | --- |
| `UserPromptSubmit` | `prompt` | Rozpoznaje polecenia, zapisuje stan i dziennik, podaje modelowi nowy stan (`additionalContext`), właścicielowi potwierdzenie (`systemMessage`); `/tryb` pokazuje tabelę przez `decision: block`. Zwykła wiadomość przy włączonej pracy ciągłej zeruje licznik oddań i przypomina modelowi, że tryb trwa. |
| `PreToolUse` (`*`) | `narzedzie` | Ochrona stanu i mechanizmu, blokady sesji, straż sekretów i straż dysku — dla każdego narzędzia (nazwy narzędzi MCP też). Dopasowuje się po nazwie narzędzia MCP, nie tylko `Bash`. |
| `Stop` | `stop` | Praca ciągła agenta głównego i okresowe oddawanie tury właścicielowi. |
| `SessionStart`, `SubagentStart` | `sesja` | Po kompakcji i wznowieniu przypomina aktywne tryby; podagentowi mówi, które blokady go wiążą i że oddaje wynik normalnie; bez aktywnych trybów milczy. |

Wszystkie wołają `hooks/hak.sh <tryb>` → `/usr/bin/python3 scripts/hak.py <tryb>`. Brak interpretera
albo skryptu kończy hook kodem 0 z komunikatem (fail-open); każdy wyjątek w hooku też — usterka
wtyczki nie zamyka sesji. Decyzje idą wyłącznie przez JSON.

Wtyczka nie wstrzykuje zasad serwera ani `CLAUDE.md` (robi to `danaco-zasady-hook` w ustawieniach
kont) i nie prowadzi katalogów sesji (`danaco-sesja-hook`).

## Twarde zasady serwera

- **Straż sekretów** (`scripts/straz_sekretow.py`): odmowa wypisania sekretu i pytanie o zgodę
  przy operacji nieodwracalnej. Działa dla **każdego** narzędzia — polecenia powłoki (`Bash`,
  `PowerShell`, `Monitor`, MCP `uruchom`), odczytu pliku (`Read`, `NotebookRead`) oraz plików
  wejściowych programów MCP (`cat ~/.ssh/id_rsa` ani `cat /root/.env` nie przejdzie żadną z tych
  dróg). Zawsze, niezależnie od trybów.
- **Straż dysku systemowego** (`scripts/straz_dysku.py`): odmowa zapisu danych na `/` poza `/etc`,
  `/usr/local/sbin`, `/usr/local/bin`, z podpowiedzią miejsca na `/danaco`. Obejmuje polecenia
  powłoki każdego narzędzia i cele zapisu narzędzi plikowych oraz MCP. Działa wszędzie, gdzie
  `/danaco` jest osobnym dyskiem (ustala to tablica montowań); nie wyłącza się sama. `DANACO_PRACA_MOUNTINFO`
  pozwala wskazać inną tablicę montowań (diagnostyka i testy).
- Kosz zamiast kasowania i straż pakietów działają na poziomie serwera (nakładka `rm`, hook
  zarządzany); wtyczka ich nie zmienia.

Polecenie powłoki zbyt duże, by je bezpiecznie rozebrać (powyżej `DANACO_PRACA_LIMIT_ANALIZY`,
domyślnie 256 kB), jest **blokowane** — żeby straże i blokady nie zostały ominięte brakiem analizy.

## Ograniczenia

Rozbiór poleceń powłoki jest heurystyczny: rozpoznaje typowe postaci (także w `bash -c`,
`ssh host '…'`, `$(…)`, `find -exec`, `xargs`, heredocu do interpretera i w treści uruchamianego
pliku skryptu do 512 kB), nie każdą możliwą. Model z uprawnieniami roota może w zasadzie obejść
każdy lokalny hook; wtyczka zamyka znane drogi i każdą próbę zapisuje w dzienniku. Budowa projektów
(`make`, `npm run build`) nie jest analizowana pod kątem `/blokuj-masowe` i `/blokuj-skrypty`.

## Struktura

```
.claude-plugin/plugin.json   manifest
hooks/hooks.json             rejestracja pięciu zdarzeń
hooks/hak.sh                 wrapper POSIX sh, fail-open
scripts/hak.py               obsługa zdarzeń: prompt, narzedzie, stop, sesja
scripts/polecenia.py         polecenia właściciela i ich rozpoznanie
scripts/stan.py              stan sesji: podpis HMAC, dziennik, odtwarzanie, fail-safe
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

Wymagania: `/usr/bin/python3` (3.10+) i POSIX `sh`. Testy i walidację uruchamia też CI
(`.github/workflows/testy.yml`).

## Licencja

Patrz plik `LICENSE`.
