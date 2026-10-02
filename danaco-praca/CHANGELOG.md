# Historia zmian

Zapis prowadzony w układzie Keep a Changelog. Wersje zgodne z wersjonowaniem
semantycznym. Wpis każdego wydania podaje wersję klienta Claude Code, na której
mechanizm trybu ciągłej pracy był weryfikowany.

Historia wspólna do 2.3.2 (plugin `danaco-plugin`). Plugin `danaco-praca` powstał w
wersji 3.0.0 przez wydzielenie mechanizmu trybu ciągłej pracy z pluginu
`danaco-plugin`; wpisy poniżej wersji 3.0.0 opisują ten mechanizm w jego dawnym
miejscu i zostały przeniesione bez zmian.

## [5.1.0] — 2026-10-02

Rozbudowa przed publikacją: komendy przejmowania sesji, nowe blokady i jedna, spójna
konwencja nazw par włącz/wyłącz. Sprawdzane na kliencie Claude Code 2.1.287.

### Zmienione (niezgodne wstecz)

- **Nowa konwencja nazw blokad:** każda para to `/<temat>-blokuj` (włącza) i
  `/<temat>-odblokuj` (zdejmuje). Zastępuje niespójne `/bez-…`/`/z-…` i `/sudo-nie`/`/sudo-tak`.
  Zmiana nazw: `/bez-bash`→`/bash-blokuj`, `/z-bash`→`/bash-odblokuj`;
  `/bez-python`→`/python-blokuj`, `/z-python`→`/python-odblokuj`;
  `/bez-masowych`→`/masowe-blokuj`, `/z-masowymi`→`/masowe-odblokuj`;
  `/reczne-pisanie`→`/skrypty-blokuj`, `/z-skryptami`→`/skrypty-odblokuj`;
  `/bez-sleep`→`/sleep-blokuj`, `/z-sleep`→`/sleep-odblokuj`;
  `/bez-podagentow`→`/podagenci-blokuj`, `/z-podagentami`→`/podagenci-odblokuj`;
  `/sudo-nie`→`/sudo-blokuj`, `/sudo-tak`→`/sudo-odblokuj`. Tryb pracy i polecenia stanu
  bez zmian (`/praca`, `/koniec-pracy`, `/tryb`).
- Sama komenda sterująca (bez zadania dla agenta) nie uruchamia już modelu — hook pokazuje
  wynik przez `decision: block`. `/koniec-pracy` i `/praca <zlecenie>` dalej przepuszczają
  turę (raport końcowy albo start pracy).

### Dodane

- **Komendy sesji:** `/sesja-id` (wypisuje identyfikator bieżącej sesji), `/sesje`
  (lista sesji obu kont — `danaco-przejmij-sesje --lista`) i `/przejmij <id>` (nakładka na
  `danaco-przejmij-sesje <id>`, podaje gotowe `claude --resume`; identyfikator sprawdzany
  wzorcem). Samego `claude --resume` hook nie odpala (brak terminala) — wkleja właściciel.
- **Trzy nowe blokady:** `/siec-blokuj` (WebFetch, WebSearch, `curl`/`wget`/`ssh`/`scp`,
  zdalny `rsync`, `git clone`/`fetch`/`pull`/`push`, pobieranie menedżerami pakietów),
  `/zapis-blokuj` (tryb tylko-odczyt: narzędzia plikowe i zmiana plików w powłoce; odczyt,
  analiza i budowa przechodzą) oraz `/pytania-blokuj` (AskUserQuestion, ExitPlanMode).
- **Polecenie `/dziennik`** — ostatnie wpisy dziennika tej sesji (zmiany trybów, odmowy,
  bezpiecznik) pokazane właścicielowi — oraz **`/wyczysc-tryby`** — zdjęcie naraz trybu
  pracy i wszystkich blokad.
- 28 skilli poleceń (było 17), wszystkie z `disable-model-invocation: true`.

### Egzekwowanie

- `scripts/reguly.py`: `blokada_sieci`, `blokada_zapisu` (reguły sieci i zapisu), rozbiór
  zdalnych celów `rsync`/`scp`.
- `hooks/hooks.json` bez zmian co do zdarzeń (`UserPromptSubmit`, `PreToolUse`, `Stop`,
  `SessionStart`, `SubagentStart`).
- Testy: `tests/test_hooki.py` rozszerzone do 53 testów (nowe blokady, komendy sesji,
  `/dziennik`, `/wyczysc-tryby`, spójność konwencji nazw); atrapa `danaco-przejmij-sesje`
  w testach (`DANACO_PRZEJMIJ_CMD`).

## [5.0.0] — 2026-10-02

Przebudowa od podstaw: wtyczka daje właścicielowi polecenia „/” sterujące trybem pracy
agenta, egzekwowane hookami. Zmiana niezgodna wstecz — dawne polecenia i pliki stanu nie
działają. Sprawdzane na kliencie Claude Code 2.1.287 (próba na żywo z atrapą API).

### Dodane

- 17 poleceń (skille z `disable-model-invocation: true`): `/praca` ↔ `/koniec-pracy`,
  `/bez-bash` ↔ `/z-bash`, `/bez-python` ↔ `/z-python`, `/bez-masowych` ↔ `/z-masowymi`,
  `/reczne-pisanie` ↔ `/z-skryptami`, `/bez-sleep` ↔ `/z-sleep`,
  `/bez-podagentow` ↔ `/z-podagentami`, `/sudo-nie` ↔ `/sudo-tak` oraz `/tryb`.
- `scripts/stan.py` — stan osobny na sesję w `${CLAUDE_PLUGIN_DATA}/stan`, podpisany
  HMAC-SHA256, z dziennikiem `dziennik.jsonl` (każda zmiana z podpisaną migawką, odmowy,
  bezpiecznik pętli). Zmieniony lub skasowany plik stanu wraca z dziennika.
- `scripts/reguly.py` — reguły blokad: Python, praca masowa, pisanie ręczne, czekanie,
  podagenci, sudo; rozbiór `bash -c`, `ssh '…'`, `$(…)`, `find -exec`, `xargs`, heredoców
  i treści uruchamianych skryptów.
- `scripts/hak.py` + `hooks/hak.sh` — jedno wejście dla `UserPromptSubmit`, `PreToolUse`,
  `Stop`, `SessionStart`, `SubagentStart`.
- Praca ciągła agenta głównego: `Stop` z `decision: block`; bezpiecznik pętli — po trzech
  kolejnych próbach zakończenia bez wywołania narzędzia czwarta przechodzi z komunikatem
  dla właściciela (`DANACO_PRACA_LIMIT_PETLI`). Podagent oddaje wynik od razu
  (`SubagentStop` nie jest blokowany). W `/praca` odrzucane jest czekanie na pierwszym
  planie, `ScheduleWakeup`, `CronCreate` i blokujący odbiór wyniku; `Monitor` i polecenia
  w tle przechodzą. Ściślejsze `/bez-sleep` odrzuca też czekanie w tle i `Monitor`.
- Ochrona przełączania: odmowa dostępu do katalogu stanu, wywołania poleceń wtyczki
  narzędziem `Skill`, podrzucenia polecenia w powłoce lub wiadomości, `claude --resume`
  z wnętrza sesji, zmiany plików wtyczki i `settings.json` oraz `disableAllHooks`.
- `scripts/straz_dysku.py` — straż dysku systemowego z gałęzi `straz-dysku-systemowego`
  (48 przypadków `--test`), odnośnik do `/etc/danaco/zasady/serwer.md`. Milczy, gdy
  konto lub ustawienia zarządzane rejestrują już `danaco-straz-dysku-hook`
  (`DANACO_PRACA_STRAZ_DYSKU=wtyczka|system` rozstrzyga ręcznie).
- `tests/test_hooki.py` (38 testów, kilkaset przypadków), `tests/proba_na_zywo.py`
  i `tests/atrapa_api.py`.

### Usunięte

- Polecenia `/pracuj`, `/stop`, `/blokada`, `/blokada-stop`, `/stop-skrypt`, `/skrypt`
  (zastępują je kolejno `/praca`, `/koniec-pracy`, `/bez-podagentow`, `/z-podagentami`,
  `/bez-masowych`, `/z-masowymi`).
- Ograniczenie trybu pracy do katalogu projektu (zakres zapisów strażnika) i wszystkie
  ograniczenia narzędzi w trybie pracy: wymóg pracy w tle, lista „wglądu” na pierwszym
  planie, bramka ciszy, bramka sprawdzeń stanu, wykrywanie powtórzeń, zakaz pytań,
  zakaz zatrzymywania zadań w tle, zakaz narzędzi wysyłających wiadomość.
- Znacznik `.danaco/zadania/<sesja>.json` w katalogu projektu i kopia `~/.danaco-kopie`
  (stan jest w danych wtyczki).
- Hooki `PostToolUse` (odtwarzanie skasowanego znacznika — zbędne, stan jest poza
  zasięgiem modelu) i `PreCompact` (zapis stanu zlecenia — stan przeżywa kompakcję sam,
  a `SessionStart` przypomina go po niej; katalog sesji prowadzi `danaco-sesja-hook`).
- `scripts/straznik.py`, `znacznik.py`, `zadanie.py`, `sesja.py`, `hooks/straznik.sh`,
  `tests/test_straznik.py` i 12 nieprzechodzących testów parytetu z 4.7.0.

## [4.7.0] — 2026-09-29

Wydanie przywraca hooki w samym pluginie. Paczki 4.6.0 rozprowadzone na serwery
straciły katalog `hooks/`, więc strażnik działał wyłącznie tam, gdzie wpisano go ręcznie
do `~/.claude/settings.json` konta. Pierwsze wydanie prowadzone w repozytorium
`DanacoGroup/danaco-plugin`. Sprawdzane na kliencie Claude Code 2.1.284.

### Dodane

- `hooks/hooks.json` rejestruje te same zdarzenia co ręczne wpisy z `settings.json`,
  z tymi samymi matcherami i limitami czasu:
  - `PreToolUse` `Bash` → tryb `sekrety` (10 s) i `PreToolUse` `.*` → `pretool` (30 s);
  - `UserPromptSubmit` → `prompt` (30 s);
  - `PostToolUse` `^(Bash|PowerShell)$` → `kontrola` (20 s);
  - `Stop` → `stop` (30 s);
  - `SessionStart` → `sesja` (15 s);
  - `PreCompact` → `kompakt` (15 s).
- `hooks/straznik.sh` — wrapper POSIX sh na miejsce utraconego. Ustawia
  `CLAUDE_PLUGIN_ROOT` (z klienta, a bez niego z położenia wrappera)
  i `PYTHONDONTWRITEBYTECODE=1`, woła `/usr/bin/python3` po ścieżce bezwzględnej i jest
  fail-open wobec awarii instalacji: brak interpretera albo skryptu trybu daje kod 0
  z komunikatem na stderr. Polecenie w `hooks.json` nie woła interpretera wprost, bo
  `python3` z nieistniejącym plikiem kończy się kodem 2, czyli blokadą — przy `Stop`
  sesja nie mogłaby zakończyć tury. Kodem 2 kończy się też `sh` (dash) z nieistniejącym
  plikiem, więc polecenia mają postać `[ -f "<wrapper>" ] && sh "<wrapper>" <tryb>`:
  brak wrappera daje kod 1 (błąd nieblokujący), kod wrappera przechodzi bez zmian.
- `scripts/sesja.py` — obsługa `SessionStart` przeniesiona z `~/.claude/hooks/danaco-praca/`.
  Moduły bierze z własnego katalogu, każdy błąd kończy kodem 0 bez wyjścia.
- `scripts/straz_sekretow.py` — straż sekretów i operacji nieodwracalnych przeniesiona
  z `~/.claude/hooks/` bez zmian (74 wbudowane przypadki `--test`). Działa niezależnie
  od znacznika zlecenia.

### Zmienione

- README: tabela zdarzeń z trybem `sekrety`, opis wrappera, wydajność, struktura
  i wymagania (`/usr/bin/python3`).

### Znane braki

- Nie odtworzono szybkiej ścieżki dawnego wrappera (sprawdzenie znacznika w powłoce bez
  uruchamiania Pythona), pliku potwierdzenia wykonania ani wrappera PowerShell
  `hooks/straznik.ps1`. Python startuje przy każdym narzędziu.
- Zestaw testów: 314 z 326 przechodzi. Nie przechodzi 12 przypadków, które sprawdzają
  utracone elementy dawnego wrappera: `TestParytetWrapperow` (7, brak `straznik.ps1`),
  `TestGranicaSpojna` (2, stałe szybkiej ścieżki), `TestBrakInterpretera`
  `test_pretool_blokuje` i `test_stop_blokuje_z_komunikatem` (dawny wrapper blokował
  przy braku interpretera, nowy przepuszcza) oraz `TestAtrapyInterpretera`
  `test_kod_zero_bez_potwierdzenia_blokuje` (atrapa `python3` w `PATH` nie jest
  uruchamiana, polecenie blokuje strażnik, a nie komunikat o braku potwierdzenia).

### Zgodność

- Konta z ręcznymi wpisami hooków w `~/.claude/settings.json` muszą je usunąć zaraz po
  włączeniu 4.7.0 — inaczej każdy hook wykona się dwa razy. Pliki
  `~/.claude/hooks/straz_sekretow.py` i `~/.claude/hooks/danaco-praca/` usuwa się
  dopiero po zdjęciu tych wpisów: `python3` i `sh` z nieistniejącym plikiem kończą się
  kodem 2, więc osierocony wpis blokowałby każde polecenie `Bash`, każde narzędzie,
  wiadomość użytkownika i zakończenie tury.

## [4.6.0] — 2026-09-09

Wydanie z trzech audytów wersji 4.5.0 i z dwóch nagrań pracy modelu. Weryfikowane na
kliencie Claude Code 2.1.265.

### Naprawione — stanie, którego nie widziała żadna reguła

- **Powtarzanie tego samego wywołania.** Bramka sprawdzeń stanu liczy wyłącznie
  wywołania rozpoznane jako zaglądanie do biegu, więc model odpytywał stan pliku `.rc`
  i `pgrep` co kilka sekund przez pół godziny - formalnie zwykłym poleceniem. Czwarte
  podobne wywołanie z rzędu, które niczego nie zmienia, jest teraz odrzucane.
- **Pętla dwóch wywołań na przemian** (odpytanie, odczyt, odpytanie, odczyt) omijała
  licznik powtórzeń; szóste wywołanie z rzędu przy najwyżej dwóch różnych odciskach
  jest odrzucane.
- **Kosmetyczne warianty polecenia.** Model zmieniał w odpytaniu format wydruku
  (`%.1fG` na `%.2fG`), przez co dokładne porównanie tekstu zawodziło. Podobieństwo
  liczone jest po zbiorze nazw uruchamianych poleceń i nazw plików.
- Zapis (`Write`, `Edit`, przekierowanie, `mv`/`cp`/`rm`) przerywa serię, a po pięciu
  minutach licznik rusza od nowa - powtórzona poprawka tego samego pliku i praca
  przeplatana sprawdzaniem przechodzą bez zmian.

### Naprawione — dwie drogi pełnego odłączenia

- **Podrobienie polecenia kończącego w transkrypcji.** Hook `Stop` zwalnia blokadę na
  widok `/stop` w transkrypcji, więc dopisanie tam wiersza roli `user` (`dd of=`,
  `echo >>`, narzędzie MCP) kończyło tryb nieodwracalnie. Transkrypcja tej rozmowy
  i katalog rozmów klienta są chronione tak samo jak znacznik.
- **Ścieżka w zagnieżdżonym polu wywołania MCP** (`{"files":[{"devicePath": …}]}`)
  omijała ochronę: sprawdzane były wyłącznie pola pierwszego poziomu. Przeglądane jest
  całe wejście narzędzia.
- **Atrapa interpretera w `PATH`.** Plik `python3` kończący się kodem 0 przepuszczał
  każde wywołanie. Strażnik zostawia potwierdzenie wykonania, a wrapper traktuje kod 0
  bez potwierdzenia jako blokadę. Wiadomości użytkownika nie są blokowane nigdy.
- **Wiszący odczyt na pierwszym planie**: `tail -n0 -f`, `tail --follow=name`,
  `less +F`, `nc -l`, `socat`, `tcpdump`, `strace -p`.

### Naprawione — fałszywe trafienia blokujące pracę

- **Pole `timeout` narzędzia powłoki czytane jako sekundy.** Klient podaje je
  w milisekundach, więc `timeout: 1000` (jedna sekunda) był odrzucany jako limit
  tysiąca sekund, a `timeout: 30000` przechodził.
- **`WebFetch` i narzędzia MCP z polami `prompt` i `description`** były brane za
  zlecenie dla podagenta i odrzucane. Para tych pól liczy się teraz tylko wtedy, gdy
  wywołanie nie ma pola narzędziowego (`url`, `file_path`, `query`, `command`).
- **Nazwa narzędzia z członem `agent`/`workflow`** dopasowywana jako podciąg odrzucała
  `workflow_status` i `run_agentless_check`; dopasowanie idzie po członach nazwy,
  a końcówki odczytu (`_status`, `_list`, `_get`) są wyłączone.

### Dodane — dziennik pracy i raport

- Każde wywołanie narzędzia przy aktywnym zleceniu trafia do
  `.danaco/zadania/praca-<sesja>.jsonl` (czas, narzędzie, skrócone polecenie, znacznik
  odrzucenia i pracy w tle). Dziennik zostaje po zakończeniu zlecenia.
- `/stop` podaje modelowi podsumowanie z dziennika i każe zbudować raport z niego,
  a nie z pamięci.
- Nowe polecenie `zadanie.py raport` pokazuje to samo człowiekowi. Dzienniki starsze
  niż siedem dni są sprzątane przy kolejnym `/pracuj`.
- Plik licznika sprawdzeń jest kasowany razem ze zleceniem - dotąd zostawał w projekcie
  na stałe, po jednym na rozmowę.

### Zmienione

- Zestaw testów: 292 → 324 testy.

## [4.5.0] — 2026-09-09

### Naprawione — odliczanie wszyte w polecenie robocze

- **`sleep` w środku polecenia sprawdzającego, puszczony w tle.** Reguła 4.4.0
  odrzucała wywołanie, którego CAŁĄ treścią jest czekanie; przechodziło więc zadanie
  tłowe `cd dane/naprawa-w53; sleep 100; wc -l < typy-eli.tsv; awk …` pod nazwą
  „Check ELI text-type distribution" - minutnik z pomiarem doklejonym na końcu. Próg
  odliczania (pięć sekund) obowiązuje teraz niezależnie od tła i liczy `sleep` również
  łącznie, więc `sleep 4; sleep 4; sleep 4` też jest odrzucane.
- Krótka przerwa przed właściwym poleceniem (`sleep 3 && npm test`) przechodzi bez
  zmian - próg dotyczy odliczania, nie pracy.
- Zestaw testów: 289 → 292 testy; w klasie `TestCzekaniaWTle` leży postać z drugiego
  zgłoszenia użytkownika.

## [4.4.0] — 2026-09-09

### Naprawione — czekanie przeniesione w tło

- **Zadanie tłowe, którego całą treścią jest czekanie.** Zakaz czekania na pierwszym
  planie model obchodził od drugiej strony: robił z czekania osobne zadanie tłowe
  (`for i in $(seq 1 28); do [ -e …rc ] && break; pgrep … || break; sleep 20; done`
  pod nazwą „Wait for the lex.db dump to finish") i znikał na kilkanaście minut, a
  w interfejsie widać było „running task" bez żadnej pracy za nim. Odrzucane jest teraz
  każde wywołanie, którego całą treścią jest odliczanie albo czekanie na cudzy proces -
  także z `run_in_background`: `sleep 540`, `wait`, `wait $PID &`. Pętle odpytujące były
  odrzucane już wcześniej, niezależnie od tła.
- **Opis zapowiadający czekanie.** Wywołanie z opisem `Wait for …` (pole `description`,
  `name`, `title`, `label`), którego treść odpytuje stan w pętli, jest odrzucane nawet
  wtedy, gdy samo polecenie mieści się w innych regułach.
- Praca w tle działa bez zmian, także z krótkim `sleep` przed właściwym poleceniem
  (`sleep 3 && npm test`) i z opisem wspominającym oczekiwanie na wynik - reguła dotyczy
  czekania, nie długości pracy.
- Zestaw testów: 285 → 289 testów (nowa klasa `TestCzekaniaWTle`, w tym postać z
  prawdziwego zgłoszenia użytkownika).

## [4.3.0] — 2026-09-09

Wydanie w całości naprawcze: wynik audytu wersji 4.2.0 (szczelność mechanizmu oraz
fałszywe trafienia nowych reguł). Weryfikowane na kliencie Claude Code 2.1.265.

### Naprawione — obejścia ochrony mechanizmu

- **Kasowanie zlecenia wzorcem wieloznacznym w członie katalogu.** Filtr nazw brał pod
  uwagę wyłącznie ostatni człon ścieżki, więc `rm -f .*/zadania/*.json ~/.*-kopie/*`
  przechodził: nazwa pliku nie miała związku ze zleceniem, a katalog `.*` trafiał
  w `.danaco`. Jedno takie polecenie kasowało wszystkie zlecenia projektu razem
  z kopiami, po których mechanizm odtwarza znacznik. Sprawdzany jest teraz każdy człon
  ścieżki; tą samą drogą przechodziły `truncate`, przekierowanie i kasowanie licznika.
- **Pliki układu sesyjnego poza ochroną nazw.** Do listy plików zlecenia dopisane
  zostały katalog `zadania`, licznik sprawdzeń, dziennik ciszy i plik napomnienia.
- **Paczki komend pluginu bez ochrony.** Chroniony był wyłącznie `skills/pracuj`;
  `skills/stop`, `skills/blokada` i `skills/stop-skrypt` dało się skasować. Ochrona
  obejmuje teraz cały katalog `skills`.
- **Znacznik niewidoczny w głębokim podkatalogu.** Limit ośmiu poziomów wędrówki w górę
  gubił katalog `.danaco` przy pracy dziewięć poziomów poniżej korzenia projektu: hook
  milkł, a tryb wyglądał na zdjęty. Limit podniesiony do 64 poziomów w module i w obu
  wrapperach; wędrówkę i tak zatrzymuje korzeń repozytorium oraz katalog domowy.
- **Wstrzyknięcie polecenia kończącego cudzą wiadomością.** Przy aktywnym zleceniu
  odrzucane są narzędzia wysyłające wiadomość poza turę (`SendMessage`,
  `PushNotification`, `SlashCommand`, odpowiedniki `mcp__*`): taka wiadomość wraca do
  sesji wpisem nieodróżnialnym od wpisu użytkownika.

### Naprawione — bramka sprawdzeń stanu (dawniej „bramka jałowego czekania")

- **Odrzucone wywołanie zerowało licznik.** Bramka stała przed regułami odrzucającymi
  i każde wywołanie niebędące sprawdzeniem uznawała za pracę - także takie, które
  strażnik za chwilę odrzucał. Cykl „trzy sprawdzenia, jedno odrzucone wywołanie" dawał
  przerwę bez końca. Licznik prowadzą teraz wyłącznie wywołania DOPUSZCZONE.
- **Dowolne tanie wywołanie zerowało licznik.** Nie zerują go już narzędzia neutralne
  (`TodoWrite`, `ToolSearch`, `Skill`) ani powtórzenie tego samego odczytu.
- **Rozpoznawanie logu po nazwie pliku.** Wzorzec brał za log każdy plik z ciągiem
  „log" w nazwie (`login.tsx`, `blog.md`, `CHANGELOG.md`) i nie widział logu nazwanego
  inaczej (`wynik.txt`). Logiem biegu jest teraz plik zarejestrowany przy uruchomieniu
  biegu w tle oraz `nohup.out`; analiza cudzego logu jest zwykłą pracą.
- **Zapis liczony jako sprawdzenie.** `echo "krok 3" >> notatki.md` — forma, którą
  zaleca sam komunikat bramki — była klasyfikowana jako sprawdzenie stanu. Segment
  z przekierowaniem sprawdzeniem nie jest.
- Nazwy przeniesione na opisowe: `bramka_sprawdzen_stanu`, `_wywolanie_jest_sprawdzeniem`,
  `_sciezka_licznika_sprawdzen`, `LIMIT_KOLEJNYCH_SPRAWDZEN`. Plik licznika nazywa się
  `sprawdzenia-<sesja>.licznik`.

### Naprawione — blokada pracy maszynowej

- **Hurtowy `UPDATE` podany przez `echo` w potoku.** Cytowany argument `echo` był
  wycinany z całego polecenia przed sprawdzeniem, więc `echo "UPDATE t SET a=1" |
  sqlite3 baza.db` przechodził — czyli dokładnie ta operacja, od której wzięła się cała
  reguła. Treść podana do wykonania (potokiem, przez `cat` albo przez `$(cat plik)`)
  jest teraz sprawdzana jak kod.
- **Cała rodzina hurtowych podmian poza regułami.** Dopisane: `patch`, `git apply`,
  `git checkout -- …`, `git restore`, `git stash pop`, `git reset --hard`,
  `git filter-branch`, `rsync`, `ed`, `ex -sc`, `vim -es`, `dos2unix`, `recode`,
  `iconv -o`, `yq -i`, `sd`, `parallel`.
- **Zmienne powłoki i skrypt bez rozszerzenia.** Polecenie jest teraz rozwijane tak samo
  jak w filtrze mechanizmu (`A=sed; B=-i; $A $B …`), a treść czytana jest z każdego
  pliku URUCHAMIANEGO, niezależnie od rozszerzenia.
- **Podagent i narzędzie MCP jako droga naokoło.** Zlecenie hurtowej podmiany podagentowi
  jest odrzucane po treści zlecenia, a narzędzie MCP z polem `command`, `script` albo
  `cmd` przechodzi ten sam filtr co powłoka.
- **Wiele zmian w jednym wywołaniu.** Narzędzie plikowe z ponad dwudziestoma zmianami
  naraz jest odrzucane; dotąd ograniczał je wyłącznie `replace_all`.

### Naprawione — fałszywe trafienia

- **Odczyt pliku skryptu był blokowany jak jego uruchomienie.** `cat napraw.py`,
  `grep -n def napraw.py`, `wc -l napraw.py`, `git diff napraw.py` — wszystkie
  odrzucane, bo treść pliku czytana była z każdego polecenia, które go wymieniało.
  Treść czytana jest teraz wyłącznie dla pliku uruchamianego.
- **Szukanie zakazanej frazy w dokumentacji.** `grep -rn 'sed -i' docs/` i
  `git log --grep='sed -i'` były odrzucane; argument-wzorzec wyszukiwania oraz treść
  heredoca kierowanego do pliku są wyłączone z analizy.
- **`psql -f raport.sql` z samym `SELECT`** przechodzi: o blokadzie rozstrzyga treść
  wczytywanego pliku, a nie sam fakt wczytania.
- **Pętla bez zapisu.** `for f in src/*.py; do python3 -m py_compile $f; done` była
  odrzucana, bo sama nazwa interpretera liczyła się jako zmiana treści. W ciele pętli
  wymagany jest teraz znak zapisu.
- **Czwarty odczyt zwykłego pliku z „log" w nazwie** nie jest już odrzucany (patrz
  bramka sprawdzeń stanu).

### Naprawione — dostępność i zasięg reguł

- **Powłoka pod inną nazwą omijała cały reżim pierwszego planu.** Narzędzie MCP z polem
  `command` przechodziło wyłącznie filtr nazw plików, więc `sleep 3000`, `npm run dev`
  i seria sprawdzeń stanu przechodziły nim bez przeszkód. Obowiązuje je teraz komplet
  reguł: wymóg tła, zakaz czekania, granice wglądu i bramka sprawdzeń stanu.
- **Wgląd, który potrafi nie wrócić.** `cat` bez pliku, `cat /dev/zero`,
  `sort /dev/urandom`, `find / -name …`, `grep -r wzorzec /` i `du -sh /` wglądem nie są
  — na pierwszym planie odcinały użytkownika do limitu klienta.

### Zmienione

- Dokumentacja zestrojona z kodem: ścieżki sesyjne znacznika i stanu zlecenia, lista
  przepustek bez `SlashCommand`, zasięg obu bramek, zachowanie `sleep` na pierwszym
  planie, sposób rozpoznawania logu, polecenie uruchamiania zestawu testów.
- Zestaw testów: 249 → 285 testów. Wszystkie klasy testowe stoją przed blokiem
  `__main__` — `TestPlikLicznikaSprawdzen` była za nim i przy uruchomieniu pliku wprost
  nie startowała.

## [4.2.0] — 2026-09-09

### Naprawione — przerwa schowana za uruchomionym procesem

- **Bramka jałowego czekania.** Zakaz czekania na pierwszym planie zamykał jedną drogę
  do przerwy i zostawiał otwartą drugą: model puszczał pracę w tło i zamiast robić
  kolejną część zlecenia odpytywał ten sam bieg w kółko (`BashOutput` z `block: false`,
  `tail -n 20 praca.log`, `ps`, znowu `BashOutput`). Każde takie wywołanie z osobna jest
  krótkie i legalne, więc żadna reguła go nie zatrzymywała, a użytkownik widział serię
  wywołań, za którą nie stała ani jedna wykonana praca. Hook `PreToolUse` rozpoznaje
  teraz wywołania będące wyłącznie zajrzeniem do biegu (odbiór wyniku zadania tłowego,
  `ps`, `pgrep`, `jobs`, `sleep`, `date`, odczyt pliku logu narzędziem `Read` i
  poleceniami `tail`, `cat`, `head`, `ls`, `wc`, `stat`) i odrzuca czwarte z rzędu, gdy
  między nimi nie było żadnej pracy. Licznik zeruje każde wywołanie wykonujące pracę;
  szukanie wzorca w logu (`grep`, `sed -n`, `rg`) liczy się jako praca. Wyjście
  awaryjne: po pięciu minutach od ostatniego dopuszczonego sprawdzenia licznik rusza od
  nowa, żeby zlecenie z jedną pozostałą pracą w tle nie kończyło się pętlą odrzuceń.
- **`sleep` na pierwszym planie ma własny, krótki próg (5 s).** Dotąd obowiązywał mu
  próg pierwszego planu (120 s), pisany dla poleceń, które coś robią; czyste czekanie
  mieściło się w nim w całości.
- Stan licznika leży w `.danaco/zadania/jalowe-sprawdzenia-<sesja>.licznik`, a
  odrzucenia trafiają do `.danaco/dziennik-ciszy.jsonl`. Rozszerzenie inne niż `.json`
  jest wymogiem: każdy plik `.json` w katalogu `zadania` liczy się jako zlecenie
  osobnej rozmowy.

### Dodane — blokada pracy maszynowej (`/stop-skrypt`, `/skrypt`)

- **Nowa para komend użytkownika.** `/stop-skrypt` odbiera modelowi hurtową podmianę
  treści, `/skrypt` oddaje ją natychmiast. Powód: zbiory danych giną nie od jednej
  pomyłki w jednym rekordzie, tylko od jednej pętli, która tę pomyłkę powiela po całym
  zbiorze. Blokada nie ma terminu ważności, wiąże rozmowę, w której ją włączono, działa
  także bez aktywnego zlecenia i obowiązuje tak samo w tle jak na pierwszym planie -
  przeniesienie hurtowej podmiany w tło nie czyni jej mniej hurtową.
- Odrzucane: podmiany w miejscu (`sed -i`, `perl -pi`, `awk -i inplace`, `rename`,
  `rpl`, `sponge`), `find -delete` i `find -exec` z poleceniem zmieniającym pliki,
  `xargs` z takim poleceniem, pętle powłoki z zapisem, kod podany wprost (`python -c`,
  `node -e`, heredoc) oraz skrypt na dysku, którego treść zawiera pętlę z zapisem albo
  podmianę w miejscu (hook czyta plik przed uruchomieniem, do 512 kB), zapis hurtowy do
  bazy danych (`UPDATE`, `DELETE FROM`, `INSERT INTO`, `DROP`, `TRUNCATE`,
  `ALTER TABLE`, import `.sql` przez `sqlite3`, `psql`, `mysql`, `mongosh`) oraz
  `replace_all` w narzędziu plikowym.
- Przechodzą bez zmian: odczyt i analiza (`SELECT`, `.schema`, `grep`, `git diff`),
  budowa i testy projektu, pojedyncza zmiana `Edit`/`Write` oraz notatka cytująca
  zakazane polecenie (`echo 'sed -i …' >> notatki.md`).
- `/stop-skrypt` nie jest wariantem `/stop`: wzorzec komendy kończącej ma po nazwie
  negatywny wgląd na `-`, więc nowa komenda nie zdejmuje zlecenia, a `/skrypt` nie
  trafia w `/stop-skrypt`.
- Plik `.danaco/blokada-skryptow.json` jest chroniony przed skasowaniem tak samo jak
  znacznik zlecenia, a wrapper powłoki budzi interpreter także wtedy, gdy w projekcie
  jest sama ta blokada.
- `zadanie.py status` pokazuje teraz stan obu blokad (podagentów i pracy maszynowej).
- Nowa paczka `skills/stop-skrypt`; paczka `pracuj` opisuje bramkę jałowego czekania
  i obie blokady dokładane przez użytkownika.

## [4.1.0] — 2026-09-07

### Naprawione

- **Podagent rozpoznawany po kształcie wywołania, nie po nazwie narzędzia.** Lista
  `Task`/`Agent`/`Workflow` nie obejmowała narzędzi, które w tym samym celu nazywają
  się inaczej (`Explore`, `Plan`, odpowiedniki `mcp__*`, narzędzia z polem
  `subagent_type`), więc model zlecał etap podagentowi, w interfejsie pojawiało się
  „Running agent", a tura stała do końca jego pracy - dokładnie ten stan, którego tryb
  zabrania. Odrzucane jest teraz każde wywołanie z polem wyboru rodzaju podagenta,
  z parą „opis + polecenie" albo o nazwie wskazującej na agenta/orkiestrację, o ile nie
  deklaruje pracy w tle. Odbiór wyniku zadania tłowego i zwykłe narzędzia z polem
  `prompt` (np. `WebFetch`) pozostają bez zmian.
- Paczka `pracuj` mówi wprost, że na pierwszym planie ma stać model, a w tle procesy:
  zakres, którego klient nie pozwala zlecić w tle, model wykonuje sam.

## [4.0.0] — 2026-09-07

### Zmienione — zlecenie jest sesyjne (zmiana niezgodna wstecz)

- **Każda rozmowa ma własne zlecenie.** Do 3.8.0 w katalogu projektu istniał jeden
  znacznik należący do jednej sesji: przy równoległej pracy w tym samym projekcie
  pozostałe rozmowy były poza trybem, a `/pracuj` w drugiej z nich **odbierało** tryb
  pierwszej. Praktycznie znaczyło to „czasem działa, czasem nie". Zlecenia leżą teraz
  w `<projekt>/.danaco/zadania/<sesja>.json` i są niezależne: `/pracuj` w drugiej
  rozmowie zakłada własne, a nie przejmuje cudzego.
- **Polecenie kończące zamyka wyłącznie zlecenie tej rozmowy** i podaje, ile zleceń
  innych sesji trwa dalej. Dotąd zdejmowało jedyny znacznik w projekcie.
- **Zniesione zostało przejmowanie własności**: wraz z nim znikły reguły „właściciel
  milczy pół godziny", „token w transkrypcji przepisuje właściciela" i ostrzeżenie
  o obcej sesji. Zlecenie innej rozmowy jest w tej sesji po prostu niewidoczne, więc
  nie ma czego przejmować ani o czym ostrzegać.
- Kopia zapasowa, stan zapisywany przed kompresją kontekstu i odtwarzanie skasowanego
  znacznika są od teraz per zlecenie, nie per katalog.
- Zlecenia z minionym terminem ważności są sprzątane przy każdym `/pracuj`, więc pliki
  po zamkniętych rozmowach nie zostają w projekcie.

### Zgodność

- Zlecenie w układzie sprzed 4.0.0 (`<projekt>/.danaco/zadanie-w-toku.json`) jest
  czytane dalej: przypisuje się pierwszej rozmowie, która po nie sięgnie, i zostaje
  przeniesione do pliku sesyjnego razem z kopią zapasową. Nic nie trzeba przenosić
  ręcznie.
- `zadanie.py status` i `diagnoza` wypisują wszystkie zlecenia w katalogu z opisem,
  właścicielem i terminem ważności; z terminala nie da się rozstrzygnąć, która sesja
  jest która, bo identyfikator rozmowy zna wyłącznie klient.
- Awaryjna ścieżka bez Pythona rozpoznaje plik zlecenia tej sesji, gdy identyfikator
  rozmowy da się zapisać wprost w nazwie pliku; w pozostałych przypadkach blokada
  zostaje (fail-closed).

### Testy

- 225 testów. Nowa klasa `TestZlecenSesyjnych` sprawdza dwa niezależne zlecenia w jednym
  projekcie, zamykanie wyłącznie własnego, brak blokady w rozmowie bez zlecenia,
  przeniesienie zlecenia z dawnego układu i sprzątanie wygasłych.

## [3.8.0] — 2026-09-06

Przegląd całego mechanizmu (3 211 linii kodu, 2 361 linii testów) przeprowadzony po
serii zgłoszeń „plugin nic nie robi". Poniżej wyłącznie wady potwierdzone odtworzeniem.

### Naprawione — obejścia reguł

- **Nazwa mechanizmu rozbita cudzysłowem omijała każdą regułę ochrony.** `rm -rf
  .dan""aco` i `rm -rf ~/.dan\aco-kopie` nie pasowały do żadnego wzorca, a powłoka
  sklejała nazwę przy wykonaniu — dawało to skasowanie znacznika razem z kopią, czyli
  zakończenie zlecenia bez `/stop`. Nazwy mechanizmu sprawdzane są teraz dodatkowo na
  tekście bez cudzysłowów i `\`-escapes.
- **Prefiksy uruchomienia robiły z pracy „wgląd".** `env ./budowanie.sh`, `nice -n 10
  make`, `stdbuf ./skrypt` przechodziły na pierwszym planie, bo pierwszym tokenem było
  polecenie z listy wglądu. Prefiksy (`env`, `nice`, `ionice`, `stdbuf`, `nohup`,
  `command`, `time`, `timeout`, `setsid`) są pomijane wraz z ich argumentami.
- **`wait` po ampersandzie czekał legalnie.** `nohup ./build.sh > log 2>&1 &` z `wait`
  w kolejnej linii uchodziło za pracę w tle, bo `&` w tekście wyłączało wszystkie
  kontrole pierwszego planu. Kontrola czekania działa teraz na części pierwszoplanowej
  polecenia, niezależnie od deklaracji tła.
- **Odpowiedniki powłoki i zapisu plików w serwerach MCP omijały mechanizm.** Ochrona
  była przypięta do nazw `Bash`/`PowerShell`/`Write`, więc `mcp__…__device_bash`
  z `rm -rf .danaco` przechodził. Narzędzia rozpoznawane są teraz po kształcie wejścia:
  pole `command` przechodzi heurystykę poleceń, pola `file_path`/`path`/`devicePath` —
  ochronę ścieżek.
- **`SlashCommand` zniknął z listy przepustek** — definicja komendy projektowej może
  zawierać polecenia powłoki, a przepustka omijała wszystkie reguły.

### Naprawione — stany, w których tryb cicho przestawał działać

- **Świeżo założony znacznik uchodził za porzucony.** `utworz_dane_zlecenia` nie
  zapisywało `ostatnioWidziano`, więc pierwsza obca sesja przejmowała zlecenie włączone
  sekundę wcześniej.
- **Przejęcie znacznika następowało w dowolnym hooku dowolnej sesji.** Sesja, która
  tylko czytała plik w tym repozytorium, wciągana była w cudze zlecenie. Przejęcie
  możliwe jest teraz wyłącznie przy wiadomości użytkownika — to znak, że w tej rozmowie
  jest człowiek.
- **`/pracuj` przy wygasłym znaczniku był pustym gestem**: hook meldował „tryb JEST JUŻ
  AKTYWNY", a pierwsze wywołanie narzędzia kasowało przeterminowany znacznik. Teraz
  wygasłe zlecenie jest zdejmowane, a komenda zakłada nowe.
- **Nieczytelny znacznik blokował wiecznie.** `wygasl(None)` zwracało `False`, więc
  uszkodzony plik (przerwany zapis, ręczna edycja) dawał blokadę nie do zdjęcia — `/stop`
  też potrzebuje odczytu. Teraz: najpierw odtworzenie z kopii, a gdy jej nie ma —
  zdjęcie znacznika z komunikatem.
- **Czas obecności z przyszłości** (cofnięty zegar, NTP) czynił właściciela wiecznie
  „widocznym" i uniemożliwiał przejęcie; liczony jest teraz jak brak zapisu.
- **Zapis spóźniony po `/stop` wskrzeszał znacznik** — równoległy hook zapisywał
  obecność już po zakończeniu zlecenia. Zapis odmawia działania, gdy istnieje nagrobek.
- **Odtwarzanie znacznika po skasowaniu szukało go tylko w korzeniu projektu**, więc
  w projekcie bez `.git` znacznik z katalogu nadrzędnego nie wracał. Kandydaci są teraz
  wspólni z resztą hooków.
- **Kopia zapasowa była odświeżana tylko przy zakładaniu zlecenia i zmianie
  właściciela**, więc odtworzenie cofało stan o wiele godzin. Odświeżana jest przy
  każdym zapisie znacznika (bez wskrzeszania po nagrobku).

### Naprawione — granice katalogów

- Katalog domowy i `CLAUDE_PROJECT_DIR` porównywane po ścieżce fizycznej: przy
  dowiązaniu symbolicznym znacznik dawał się założyć wprost w `~` i blokował wszystkie
  projekty pod nim.
- Korzeń repozytorium szukany bez ośmiopoziomowego limitu — w monorepo limit kończył
  wędrówkę przed `.git`, znacznik lądował w głębokim podkatalogu i znikał po `cd`.

### Naprawione — fałszywe trafienia

- `git -C <katalog> status|log|diff|show` przestało być klasyfikowane jako praca i jako
  zapis poza zakresem zlecenia; opcje `git` z argumentem (`-C`, `-c`, `--git-dir`,
  `--work-tree`) są pomijane przy wyborze podpolecenia.
- Ochrona treści plików wymaga zbieżności wzmianki o znaczniku i czasownika
  destrukcyjnego **w tej samej linii** — warunek liczony na całym pliku blokował zapis
  własnych testów pluginu i dokumentacji mechanizmu.
- Bramka ciszy ignoruje wypowiedzi starsze niż początek zlecenia: raport zamykający
  poprzednią turę nie kosztuje już odrzuconego wywołania po włączeniu trybu.

### Naprawione — wydajność hooka (odpala się przy każdym wywołaniu narzędzia)

- Token zlecenia czytany leniwie: w najczęstszej ścieżce odpadł odczyt do 8 MB
  transkrypcji przy każdym wywołaniu.
- Ogon transkrypcji dla bramki ciszy przeglądany od końca, z parsowaniem tylko
  potrzebnych wpisów, zamiast pełnego parsowania 256 KB.
- Zmierzony narzut po zmianach: około 58 ms na wywołanie przy aktywnym znaczniku
  i transkrypcji 383 KB.

### Naprawione — diagnostyka

- `zadanie.py diagnoza` parsuje pliki konfiguracji jako JSON zamiast szukać podciągów:
  wpis `"danaco-praca": false` był meldowany jako włączony, a `"disableAllHooks":true`
  zapisany bez spacji nie był w ogóle wykrywany.
- `status` i `diagnoza` odróżniają nieczytelny znacznik od jego braku — dotąd przy
  uszkodzonym pliku mówiły „tryb nieaktywny", choć hook blokował.

### Testy

- 239 testów (było 228). Nowa klasa `TestPrzegladu38` pokrywa każdą z powyższych wad
  przypadkiem odtworzeniowym.

## [3.7.0] — 2026-09-06

### Naprawione

- **Wygaśnięcie znacznika przestało być ciche.** Termin ważności zdejmował znacznik
  w dowolnym hooku, nie mówiąc o tym nikomu: tryb znikał w środku pracy, a model
  i użytkownik dalej sądzili, że obowiązuje. Hooki `UserPromptSubmit` i `PreCompact`
  ogłaszają teraz wygaśnięcie wraz z datą i nazwą zlecenia oraz informacją, że wraca
  się do trybu poleceniem `/pracuj`.
- **Przepuszczenie z powodu obcego właściciela zostawia ślad.** `PreToolUse` i `Stop`
  przechodziły bez śladu, gdy znacznik należał do innej rozmowy — to ta sama cicha
  ścieżka, przez którą martwy właściciel unieruchamiał tryb na całe dni. Każde takie
  przepuszczenie trafia teraz do `.danaco/dziennik-ciszy.jsonl` z nazwą narzędzia
  i powodem, więc widać je po fakcie nawet bez wiadomości od użytkownika.

### Przegląd

- Przejrzane zostały wszystkie ścieżki, którymi strażnik kończy się kodem 0 mimo
  aktywnego znacznika. Świadomie przepuszczane bez zapisu pozostają: narzędzia
  z listy przepustek, natychmiastowy odbiór wyniku zadania tłowego, wgląd w powłoce
  oraz narzędzia bez pola limitu i bez pola pracy w tle (te ostatnie z wpisem
  w dzienniku ciszy). Każda pozostała ścieżka albo blokuje, albo zostawia zapis.

## [3.6.0] — 2026-09-06

### Naprawione

- **Znacznik związany z zakończoną sesją unieruchamiał cały tryb.** Przepisanie
  własności wymagało tokenu zlecenia obecnego w transkrypcji, a token trafia tam
  wyłącznie wtedy, gdy człowiek uruchomił `zadanie.py start` z terminala. Znacznik
  zakładany przez hook — droga podstawowa od 3.1.0 — nie ma go nigdzie, więc gdy sesja
  właściciela się kończyła (restart klienta, awaria, nowa sesja po kompresji kontekstu,
  diagnostyczne wywołanie hooka), znacznik zostawał jej na zawsze: każda kolejna
  rozmowa w tym katalogu przechodziła przez hooki bez jednej blokady, a `status`
  i `diagnoza` dalej pokazywały tryb jako aktywny. Przejęcie opiera się teraz wyłącznie
  na milczeniu właściciela dłuższym niż pół godziny; token pozostaje potrzebny do
  zdjęcia znacznika bez identyfikatora sesji.
- **Rozjazd właściciela przestał być niewidoczny.** Sesja, która trafia na znacznik
  innej, czynnej rozmowy, dostaje jednorazową informację w kontekście tury: że tryb
  tutaj nie obowiązuje, kiedy ostatnio widziano właściciela i jak przejąć zlecenie
  poleceniem `/pracuj`. Dotąd hook przepuszczał takie zdarzenia po cichu.

### Zmienione

- `zadanie.py diagnoza` podaje właściciela znacznika (`sesjaId`), czas ostatniej
  obecności oraz werdykt „tryb w nowej sesji: OBOWIĄZUJE / NIE OBOWIĄZUJE”. Wynik
  hooka `Stop` opisany jest teraz jako dotyczący sesji-właściciela, a nie każdej.

## [3.5.0] — 2026-09-05

### Naprawione

- **Cisza między wywołaniami narzędzi obowiązuje bez progu długości.** Bramka z 3.4.0
  mierzyła długość wypowiedzi, więc przepuszczała to, co w praktyce zasypuje czat:
  serię jednozdaniowych meldunków („Historia brzmień na 59 aktach ze 137.”, „złoty test
  dalej liczy”) po każdym wywołaniu. Teraz rozstrzyga kontekst wypowiedzi, nie jej
  rozmiar: tekst napisany po wyniku narzędzia jest meldunkiem i odrzuca kolejne
  wywołanie niezależnie od długości, a próg 350 znaków dotyczy wyłącznie odpowiedzi na
  wiadomość, którą użytkownik napisał w trakcie pracy.

### Dodane

- **Zakaz zatrzymywania pracy uruchomionej w tle.** Model przenosił pracę w tło, a
  chwilę później sam ją kasował („17 background tasks stopped”), tracąc wynik, na który
  zlecenie czekało. Hook odrzuca teraz narzędzia zatrzymujące zadania (`TaskStop`,
  `KillShell`, `KillBash`, `StopTask` i odpowiedniki `mcp__*`) oraz powłokowe `pkill`,
  `killall`, `kill %1` i `jobs -p | xargs kill`. Bieg poprawiony uruchamia się obok,
  a nie zamiast poprzedniego.

## [3.4.0] — 2026-09-05

### Dodane

- **Bramka ciszy: zakaz raportowania w trakcie zlecenia jest egzekwowany maszynowo.**
  Reguła „jeden raport, końcowy" istniała dotąd wyłącznie jako zdanie w paczce `pracuj`
  i model podchodził do niej luźno — zasypywał czat zapowiedziami, raportami cząstkowymi
  i podsumowaniami etapów. Hook `PreToolUse` mierzy teraz ostatnią wypowiedź modelu na
  czacie i odrzuca pierwsze wywołanie narzędzia po wypowiedzi dłuższej niż 350 znaków,
  podając powód. Odrzucenie jest jednorazowe dla danej wypowiedzi (identyfikator w
  `.danaco/napomnienie-ciszy.json`), więc model wraca do pracy natychmiast po
  powtórzeniu wywołania. Liczy się wyłącznie tekst wysłany na czat — bloki rozumowania
  i wywołania narzędzi nie są raportowaniem. Bramka obejmuje także narzędzia z listy
  przepustek, bo inaczej raport zakończony wywołaniem `Read` omijałby regułę.

### Zmienione

- Paczka `pracuj` wylicza cztery reguły trybu wprost (bez kończenia tury, bez pytań,
  bez czekania na pierwszym planie, cisza na czacie) i podaje przy każdej, że pilnuje
  jej hook. Sekcja o ciszy nazywa zakazane formy wypowiedzi i wskazuje, gdzie zapisać
  treść, którą model chce zachować.
- Komunikaty hooków przy włączeniu trybu, przy otwarciu sesji i po kompresji kontekstu
  powtarzają regułę jednego raportu wraz z progiem.

## [3.3.0] — 2026-09-05

### Zmienione

- **Na pierwszym planie zostaje wyłącznie wgląd; praca idzie w tło niezależnie od
  zadeklarowanego limitu czasu.** Dotąd o dopuszczeniu polecenia na pierwszy plan
  decydował limit czasu, więc `npm test`, `ssh serwer 'make'`, `cp -r`, `python3
  skrypt.py` czy zapytanie do bazy przechodziły, o ile mieściły się w progu — a przez
  ten czas nie odpalał się żaden hook i użytkownik nie miał jak się odezwać. Limit mówi
  tylko, kiedy polecenie zostanie przerwane, a nie kiedy się skończy, więc nie chronił
  przed ciszą. Teraz na pierwszym planie zostaje zamknięta lista poleceń wglądu (`ls`,
  `cat`, `head`, `tail -n`, `grep`, `find`, `wc`, `stat`, `sed -n`, `diff`, `git
  status|log|diff|show`, `ps`, `kill`, `echo`, `pwd`, `cd` i pokrewne, w PowerShellu
  `Get-ChildItem`, `Get-Content`, `Select-String`, `Test-Path` i pokrewne), a każde inne
  wywołanie wymaga `run_in_background` albo `nohup … &`. Polecenia, którego na liście
  nie ma, hook kieruje w tło — lista jest zamknięta z rozmysłem.
- Rozstrzygnięcie obejmuje podstawienia poleceń (`$(…)`, odwrotne apostrofy),
  rozgałęzienia i pętle powłoki (`if`, `for`, `while`) oraz przełączniki, które
  z wglądu robią pracę (`sed -i`, `find -exec`, `find -delete`).
- Zadeklarowany limit powyżej progu 120 s dalej wymaga tła, także dla poleceń wglądu
  (`grep -rn … /` po całym dysku potrafi trwać).

## [3.2.0] — 2026-09-05

### Naprawione

- **Limit pierwszego planu obowiązuje każde polecenie, nie tylko rozpoznane z nazwy.**
  Dotąd wywołanie z zadeklarowanym limitem czasu powyżej progu blokowane było wyłącznie
  wtedy, gdy polecenie pasowało do listy „poleceń długich" (budowa, testy, instalacja).
  Wszystko spoza listy przechodziło na pierwszym planie bez ograniczenia czasu:
  `timeout 400 sqlite3 …`, `ssh serwer 'cd /srv && make'`, `scp`, `rsync`, własny skrypt
  — czyli dokładnie te wywołania, za którymi model znikał użytkownikowi na kilka minut
  („running tools", brak możliwości odezwania się). Reguła jest teraz odwrócona: limit
  ponad progiem wymaga tła bez względu na treść polecenia, a lista poleceń długich
  została usunięta.
- **Próg pierwszego planu obniżony z 300 s do 120 s.** Próg jest teraz równy domyślnemu
  limitowi narzędzia `Bash` w kliencie, więc wyznacza najdłuższą przerwę w kontakcie
  z użytkownikiem, jaka w tym trybie może w ogóle wystąpić. Wywołanie bez zadeklarowanego
  limitu przerwie klient po swoim limicie domyślnym — codzienna budowa i testy działają
  jak dotąd.
- **Brak pola pracy w tle w schemacie podagenta przestał być przepustką.** `Task`,
  `Agent` i `Workflow` bez deklaracji tła były przepuszczane z wpisem w dzienniku ciszy,
  gdy klient nie miał pola `run_in_background`. Takie wywołanie czeka na wynik tak samo
  jak z `run_in_background: false`, więc przepustka była obejściem jedynej reguły tego
  trybu. Teraz jest odrzucane: zakres, którego nie da się zlecić w tle, model wykonuje
  sam serią krótkich wywołań.
- **`zadanie.py diagnoza` przestała zgłaszać brak wpisu przy działającym pluginie.**
  Sprawdzała wyłącznie konfigurację Claude Code w terminalu (`settings.json`,
  `~/.claude.json`), a plugin instalowany z konta (Cowork, aplikacja desktopowa) ma wpis
  tylko w rejestrze `~/.claude/plugins/**/manifest.json`. Diagnoza czyta teraz również
  ten rejestr.

## [3.1.1] — 2026-09-05

### Naprawione

- `/pracuj` przy istniejącym znaczniku przypisuje go teraz sesji, która wydała polecenie.
  Dotąd tylko potwierdzał aktywność, więc znacznik związany wcześniej z obcym
  identyfikatorem (np. `test` z polecenia diagnostycznego albo pozostałość po starszej
  wersji) omijał rozmowę, w której użytkownik faktycznie pracował: blokada nie działała,
  choć `status` pokazywał tryb jako aktywny.

## [3.1.0] — 2026-09-05

### Zmienione

- **Tryb ciągłej pracy włącza HOOK, nie model.** Dotąd znacznik zakładał model,
  uruchamiając `scripts/zadanie.py start` po wczytaniu paczki `pracuj`. Gdy tego nie
  zrobił albo zrobił w innym katalogu, znacznik nie powstawał, hook `Stop` zwracał 0,
  model kończył tury i zadawał pytania — a użytkownik widział wczytaną paczkę i był
  przekonany, że tryb działa. Teraz komenda `/pracuj` (a także `/danaco-praca:pracuj`
  i stara postać `/danaco-plugin:pracuj`) jest rozpoznawana w hooku `UserPromptSubmit`
  tą samą regułą co pozostałe komendy — na początku wiadomości albo w osobnej linii —
  i to hook zapisuje znacznik: korzeń projektu wyznacza z pola `cwd` zdarzenia (ta sama
  logika co w `zadanie.py`, z odmową w katalogu domowym i w korzeniu systemu plików),
  opis zlecenia bierze z treści wiadomości po odjęciu komendy, a `sesjaId` z pola
  `session_id` zdarzenia — co przy okazji usuwa dotychczasowy wyścig wiązania znacznika
  z sesją. Powtórna komenda nie nadpisuje istniejącego zlecenia. Awaria zapisu idzie na
  stderr, nie wyjątkiem.
- **Paczka `skills/pracuj` nie każe już modelowi niczego uruchamiać.** Krok „uruchom
  `zadanie.py start`" zniknął; model dostaje wyłącznie reguły pracy i informację, że
  tryb jest już włączony. `scripts/zadanie.py start` zostaje jako droga dla człowieka
  uruchamiana z terminala.
- **`zadanie.py status` pisze po ludzku**, nie surowym JSON-em: czy tryb jest aktywny
  w tym katalogu, gdzie leży znacznik, do jakiej sesji należy, kiedy wygasa, ile było
  blokad zakończenia tury i jakie były ostatnie kroki.

### Dodane

- **`zadanie.py diagnoza`** — jedno polecenie odpowiadające na pytanie „czy mechanizm
  w tym katalogu w ogóle zadziała": widoczność pluginu w konfiguracji Claude Code,
  interpreter Pythona osiągalny z powłoki hooków, miejsce poszukiwania znacznika dla
  bieżącego katalogu oraz wynik, jaki zwróciłby tu hook `Stop` (0 czy 2).
- Testy włączania trybu przez hook: założenie znacznika w katalogu z `cwd` zdarzenia,
  przeniesienie opisu zlecenia z wiadomości, brak nadpisania przy powtórnej komendzie,
  odmowa w katalogu domowym, `sesjaId` z `session_id`, blokada `Stop` po założeniu
  i zdjęcie znacznika przez `/stop`, a także `status` i `diagnoza` z znacznikiem i bez.

## [3.0.1] — 2026-09-05

### Poprawione

- **Domknięta reguła zakazu czekania na zadanie tłowe.** Model potrafił uruchomić
  zadanie w tle, a potem stanąć przy nim na pierwszym planie i przestać odbierać
  wiadomości. Dwie luki: `TaskOutput` i `BashOutput` były na liście przepustek, a w
  kliencie Claude Code przyjmują pole `block` z wartością domyślną `true` i `timeout`
  z wartością domyślną 30000 ms oraz górną granicą 600000 ms — wywołanie bez tych pól
  czeka na zakończenie zadania. Druga luka to polecenia powłoki realizujące to samo
  czekanie. Teraz `TaskOutput`, `BashOutput`, `AgentOutputTool`, `BashOutputTool` i
  `TaskGet` przechodzą wyłącznie w wariancie natychmiastowym (`block: false` albo limit
  czasu do 5 sekund), a `PreToolUse` odrzuca polecenia `wait`, `jobs -p | xargs wait`,
  pętle `while`/`until`/`for` ze `sleep` lub `test -f`, `tail --pid`, `flock` bez `-n`
  oraz `wait-for-it`. Narzędzia, których jedyną funkcją jest czekanie, rozpoznaje
  szerszy wzorzec nazwy (`wait`, `sleep`, `poll`, `await`, `idle_until`). Samo pobranie
  wyniku pozostaje dozwolone — to jest zalecany sposób sprawdzania postępu.

### Zmienione

- Paczka `pracuj` dostała regułę pracy równoległej: po uruchomieniu zadania w tle model
  przechodzi do kolejnej niezależnej części zlecenia i wraca po wynik krótkim
  sprawdzeniem, a kolejność pracy planuje tak, żeby w czasie liczenia w tle było co
  robić.
- Testy `tests/test_straznik.py` obejmują każdą rozpoznaną formę oczekiwania oraz
  przypadki negatywne (`sleep 5`, `flock -n`, natychmiastowe pobranie wyniku).

## [3.0.0] — 2026-09-05

Wydzielenie trybu ciągłej pracy do osobnego pluginu `danaco-praca`. W pluginie zostają
wyłącznie paczki `pracuj`, `stop` i `blokada`, skrypty `straznik.py`, `znacznik.py`,
`zadanie.py`, wrappery hooków oraz ich testy. Paczki standardów inżynierskich i
walidatory dyscypliny (`weryfikatory-dyscypliny`, `dyscyplina-inzynierska` i pozostałe)
zostają w pluginie `danaco-plugin`; oba pluginy da się mieć zainstalowane naraz.

### Dodane

- **Kontrola pierwszego planu na wszystkich narzędziach.** Matcher `PreToolUse` to
  `.*`, a rozstrzyganie przeniesiono do `scripts/straznik.py` i oparto na regule
  odwróconej. Lista przepustek (`Read`, `Glob`, `Grep`, `BashOutput`, `TaskOutput`,
  `TodoWrite`, `ToolSearch`, `Skill`, `SlashCommand`, `NotebookRead`,
  `ListMcpResources`, `ReadMcpResource`) przechodzi bez sprawdzania; narzędzia plikowe
  i powłoki zachowują dotychczasowe reguły. Każde inne narzędzie — w tym `mcp__*`,
  `WebFetch` i `WebSearch` — przechodzi z deklaracją pracy w tle albo z limitem czasu
  do 300 sekund (pola `timeout`, `timeout_ms`, `timeoutMs`, `max_duration`,
  `deadline_s`). Poza kontrolą były dotąd narzędzia MCP z limitem 180 sekund,
  przeglądarka, pobieranie stron i narzędzia klienta.
- **Dziennik ciszy `.danaco/dziennik-ciszy.jsonl`.** Narzędzie bez pola limitu czasu i
  bez pola pracy w tle nie jest blokowane — wywołanie przechodzi, a nazwa narzędzia i
  czas trafiają do dziennika, żeby dało się później zobaczyć, co odcina użytkownika.
  Dziennik jest przycinany do 1000 ostatnich wpisów.
- **Blokada narzędzi oczekiwania.** Narzędzie, którego nazwa pasuje do `.*wait.*`,
  `.*sleep.*` albo `.*poll.*`, jest odrzucane z komunikatem: czekanie jest jego jedyną
  funkcją, więc żaden limit czasu go nie ratuje.

### Zmienione

- **Nowy prefiks komend.** Komendy to `/danaco-praca:pracuj`, `/danaco-praca:stop`,
  `/danaco-praca:blokada`, `/danaco-praca:blokada-stop` oraz postacie nagie (`/pracuj`,
  `/stop`, `/blokada`, `/blokada-stop`). Stary prefiks `/danaco-plugin:` działa dalej
  jako alias — w `znacznik.py`, `hooks/straznik.sh` i `hooks/straznik.ps1` — bo
  użytkownik ma otwarte sesje z komendami w tamtej postaci.
- **Podagent bez dostępnego pola tła nie jest odrzucany.** Gdy klient nie daje pola
  `run_in_background` (zmienna `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` albo brak tego
  klucza w poprawnie zbudowanym wywołaniu), wywołanie przechodzi, trafia do dziennika
  ciszy, a model dostaje na stderr informację, że użytkownik straci kontakt na czas
  pracy podagenta. Gdy pole jest dostępne, wariant synchroniczny jest odrzucany jak
  dotąd. Z `POLA_PRACY_W_TLE` zostało `run_in_background`; nazwy `background`,
  `is_background`, `run_in_bg`, `async`, `detached` są opisane jako zapas na wypadek
  zmiany nazwy pola w kliencie.
- **Wydajność wrappera.** Matcher `.*` oznacza wywołanie hooka przy każdym narzędziu,
  więc `hooks/straznik.sh` rozstrzyga w powłoce, czy tryb w ogóle jest aktywny, i
  kończy się kodem 0 bez uruchamiania Pythona. Zmierzony narzut przy nieaktywnym
  trybie: około 9 ms na wywołanie (aktywny tryb: około 46 ms).

### Usunięte

- Hook `PostToolUse` dla zapisów (`hooks/po_zapisie.sh`) i walidatory dyscypliny —
  zostają w pluginie `danaco-plugin`. `PostToolUse` w tym pluginie ma wyłącznie matcher
  `^(Bash|PowerShell)$` z trybem `kontrola`, który odtwarza skasowany znacznik.

## [2.3.2] — 2026-09-05

### Zmienione

- Podagenci (`Task`, `Agent`, `Workflow`) przechodzą wyłącznie uruchomieni w tle;
  wariant synchroniczny jest odrzucany. Dotąd dawał tylko wskazówkę, przez co model
  nadal znikał za „running tools" na czas pracy podagenta, a użytkownik nie miał jak się
  odezwać. Blokada dotyczy czekania, nie samej pracy wieloagentowej: wariant tłowy
  działa bez zmian, procesy nie są przerywane ani zabijane.

## [2.3.1] — 2026-09-04

Wydanie domyka ustalenia dwóch audytów kontrolnych wersji 2.3.0: zamyka pozostałe drogi
samozwolnienia, przywraca płynność codziennej pracy i porządkuje wydanie.

### Naprawione

- **Dwuetapowe samozwolnienie zamknięte.** Katalog kopii `~/.danaco-kopie`, pliki kopii i
  nagrobki są chronione tak samo jak `.danaco` (również w zapisie `$HOME/…` i `~/…`), a
  `rm`, `mv` i `rmtree` z celem pochodzącym z podstawienia polecenia `$( )` albo z
  backticków są odrzucane — nazwy takiego celu nie da się sprawdzić przed wykonaniem.
- **`/blokada` bez aktywnego zlecenia nie jest kasowalna.** Kontrola poleceń i zapisów
  działa również wtedy, gdy aktywna jest sama blokada podagentów; plik
  `blokada-subagentow.json` jest chroniony jak znacznik. `zadanie.py start` przechodzi.
- **Parytet `hooks/straznik.ps1` z `hooks/straznik.sh`.** Wzorzec komendy tylko na
  początku wiadomości albo linii (cytat już nie zdejmuje blokady), sprawdzenie
  właściciela sesji i tokenu, sprawdzenie terminu ważności, odczyt pola `prompt` z
  sekwencjami ucieczki, `Remove-Item -Recurse` przy zdejmowaniu znacznika oraz wypis
  `stan-zlecenia.md` w trybie `sesja`. Parytetu pilnuje test statyczny.
- **Ucieczka ścieżką względną.** Cele zapisu bez prefiksu `cd <ścieżka bezwzględna> &&`
  liczone są od katalogu roboczego zdarzenia hooka, więc `echo x > ../poza.txt` jest
  odrzucane jak każde inne wyjście poza katalog zlecenia.
- **Bezterminowy znacznik poza deklaracją modelu.** `--limit-godzin 0` wymaga teraz
  dowodu spoza sesji (brak `CLAUDE_PLUGIN_ROOT` i `CLAUDE_PROJECT_DIR` albo interaktywny
  terminal); flaga `--poza-sesja` jest wyłącznie dodatkowym potwierdzeniem.
- **Token nie przejmuje cudzego zlecenia.** Własność raz ustalona nie jest przepisywana
  na inną sesję na podstawie samego tokenu w transkrypcji (użytkownik mógł go tam
  wkleić); przejęcie jest możliwe dopiero, gdy dotychczasowy właściciel przez pół godziny
  nie wywołał żadnego hooka.

### Zmienione

- **Próg pierwszego planu podniesiony do 300 s.** `go build`, `npm run build`, `npm test`,
  `pytest -q`, `make`, `mvn`, `gradle`, `docker build` i `pip install` przechodzą bez
  deklarowania limitu czasu. Blokowane pozostają polecenia z natury nieskończone
  (serwery, `tail -f`, `watch`), `sleep` powyżej progu oraz limit zadeklarowany powyżej
  progu.
- **Mniej fałszywych trafień w polskim repozytorium.** Gołe `import znacznik` i
  `from zadanie …` nie są już obejściem (liczy się nazwa funkcji mechanizmu), zniknął
  relikt `.klucz`, a nazwy plików zlecenia (`zadanie-w-toku`, `stan-zlecenia`,
  `blokada-subagentow`) liczą się wyłącznie jako CEL operacji destrukcyjnej — `rg
  zadanie-w-toku` i `echo … >> lista.txt` przechodzą. `git clean -n` i `--dry-run`
  przechodzą; rozpoznawane są też `/stop.` i `/stop!`.
- **Kontrola treści zapisu tylko dla plików skryptowych i konfiguracyjnych** (`.sh`,
  `.ps1`, `.py`, `.bat`, `.cmd`, `.json`, `.yaml`, `.yml`, `.toml`). README, runbook i
  CHANGELOG mogą opisywać polecenia.
- **Porządek w `~/.danaco-kopie`.** Każdy `start` kasuje kopie i nagrobki starsze niż
  siedem dni, a nieudany zapis kopii jest sygnalizowany na stdout.

### Wydajność

- **Hooki nie uruchamiają Pythona bez potrzeby.** Obecność znacznika (albo pliku blokady)
  sprawdza powłoka we wszystkich trybach `hooks/straznik.sh`; tryb `kontrola` woła
  interpreter dopiero wtedy, gdy znacznik zniknął, a katalog kopii istnieje. Koszt hooka
  bez aktywnego zlecenia spadł z ok. 54 ms do ok. 8 ms. `hooks/po_zapisie.sh` filtruje
  rozszerzenie w powłoce i uruchamia oba walidatory w jednym procesie.

### Porządki

- Usunięty martwy kod (`KOMUNIKAT_PODAGENT`, `_NAZWY_ZLECENIA_DO_GLOBU`,
  `POLECENIE_ZAKONCZENIA` w `hooks/straznik.sh`, rusztowanie `--fraza` w testach) oraz
  katalogi `.pytest_cache/` i `__pycache__/` z drzewa repozytorium.
- `plugin.json` i `marketplace.json` mówią o osiemnastu paczkach skilli (tyle ich jest);
  README podaje bieżącą wersję i liczbę przypadków testowych.
- `scripts/znacznik.py` i `scripts/straznik.py` przechodzą własny walidator dyscypliny
  (udział komentarzy poniżej progu 20%).
- Testy: 264 przypadki, izolacja katalogu domowego obejmuje wszystkie klasy testowe.

## [2.3.0] — 2026-09-04

Wydanie domyka ustalenia dwóch audytów kontrolnych mechanizmu trybu ciągłej pracy:
zamyka drogi obejścia blokady dostępne modelowi i zdejmuje ograniczenia, które dławiły
normalną pracę.

### Zmienione

- **Termin ważności poza zasięgiem modelu.** `--limit-godzin` przyjmuje wartości od 1 do
  24; `0` (bezterminowo) wyłącznie poza sesją modelu, z flagą `--poza-sesja`. Hook
  `PreToolUse` odrzuca też `zadanie.py start` przy już aktywnym znaczniku.
- **Rozpoznanie komend zawężone do początku wiadomości albo osobnej linii.** `/stop`,
  `/blokada` i `/blokada-stop` w cytacie, w ścieżce (`/stop-handler.md`, `/stop/x`),
  we wklejonym logu i w prozie nie wyzwalają niczego — także przy skanowaniu
  transkrypcji w hooku `Stop`.
- **Wiązanie znacznika z sesją tokenem**, nie zmienną `CLAUDE_SESSION_ID` (klienci jej
  nie eksportują). `start` losuje token i wypisuje go na standardowe wyjście; obecność
  tokenu w transkrypcji rozstrzyga własność, utrzymuje blokadę u właściciela mimo
  rozjazdu identyfikatora sesji i jest wymagana do zdjęcia znacznika, gdy zdarzenie nie
  ma identyfikatora sesji.
- **Granica `.git` znowu honorowana** przy szukaniu znacznika; znacznik z katalogu
  nadrzędnego obowiązuje, gdy katalog bieżący leży w jego `katalogProjektu`. `mkdir .git`
  niczego nie wyłącza, a sąsiednie repozytorium pozostaje wolne.
- **Zakres zlecenia w poleceniach powłoki** obejmuje teraz ostatni argument `cp`, `mv`,
  `install` i `rsync`, argument `tee`, `-o`/`--output`, `>|` oraz ścieżki względne po
  prefiksie `cd <katalog> &&`. Allowlista: `/tmp`, `/dev/*`, katalog cache.
- **Praca na pierwszym planie odblokowana dla poleceń skończonych.** `pytest`, `npm test`,
  `make` i `go test` przechodzą, gdy wywołanie deklaruje limit czasu do 60 sekund (pole
  `timeout` albo prefiks `timeout N`). Tło pozostaje wymagane dla poleceń z natury
  nieskończonych (serwery, `tail -f`, `watch`) i dla dłuższych limitów.
- **Zawężone heurystyki fałszywie trafiające.** Gołe `hooks`, `scripts` i `.claude-plugin`
  liczą się wyłącznie w katalogu pluginu (`mv hooks/old.js src/` w obcym repozytorium
  przechodzi), a nazwy funkcji mechanizmu — wyłącznie w kontekście wykonania Pythona
  (`python -c`, `-m`, heredoc), nie w `grep`, `git commit -m` ani `git log`.
- **Blokada podagentów zdejmowana wyłącznie przez sesję, która ją założyła.**
- **Termin ważności sprawdzany we wszystkich trybach strażnika**, także w
  `UserPromptSubmit` i `PreCompact`.

### Dodane

- **Kopia znacznika poza katalogiem projektu** (`~/.danaco-kopie/<skrót-ścieżki>.json`,
  uprawnienia 600) i nowy hook `PostToolUse` dla `Bash`/`PowerShell` (tryb `kontrola`):
  znacznik skasowany poleceniem powłoki wraca przy następnym wywołaniu, z komunikatem, że
  usunięcie znacznika nie kończy zlecenia. Legalne zdjęcie kasuje kopię i zostawia
  nagrobek, więc znacznik nie zmartwychwstaje.
- **Doszczelnione wzorce obejść**: wzorce wieloznaczne obejmujące katalog zlecenia
  (`.dana*`, `.d*o`), `find … -delete`/`-exec rm` z filtrem nazwy pasującym do plików
  zlecenia (także `-name "*.json"`), składanie nazwy ze zmiennych powłoki, heredoc
  uruchamiający Pythona oraz `base64 -d | sh`.
- **Ścieżka awaryjna bez Pythona doprowadzona do parytetu** w granicach POSIX `sh`:
  rozpoznanie komendy na początku wiadomości (z obsługą cudzysłowu po ukośniku
  odwrotnym), sprawdzenie właściciela sesji i tokenu oraz terminu ważności.
- **Wrapper PowerShell podłączony warunkowo**: `hooks/straznik.sh` przekazuje mu
  zdarzenie, gdy nie znajdzie Pythona, a `pwsh`/`powershell` jest dostępne. `.ps1`
  obsługuje tryby `kompakt` i `kontrola`.

## [2.2.0] — 2026-09-04

Wydanie przestawia tryb ciągłej pracy na zasady ustalone z operatorem: jawne wyzwalanie,
jedno polecenie kończące, brak wpływu na procesy i narzędzia, stała dostępność modelu.

### Zmienione

- **Wyzwalanie wyłącznie komendą** `/danaco-plugin:pracuj` (lub `/pracuj`). Opis paczki
  nie łapie już ogólnych sformułowań („dokończ całość”, „nie przerywaj”, „nie pytaj mnie
  o nic”), przez które tryb włączał się sam przy zwykłych poleceniach.
- **Kończenie wyłącznie poleceniem `/stop`** (`/danaco-plugin:stop`). Zniesiono frazę
  potwierdzenia, jej podpis HMAC i plik klucza: komenda jest widoczna w interfejsie, nie
  pada przypadkiem w rozmowie, a modelowi jest tak samo niedostępna, bo zdarzenie
  `UserPromptSubmit` powstaje wyłącznie z wpisu człowieka. Nowa paczka `stop`.
- **Znacznik należy do sesji, która go założyła** (`sesjaId` zapisywany przy pierwszym
  zdarzeniu hooka). Inna rozmowa otwarta w tym samym katalogu nie jest blokowana i nie
  przejmuje cudzego zlecenia.
- **Termin ważności znacznika: 24 h** (`--limit-godzin N`, `0` = bezterminowo). Zapomniany
  znacznik nie blokuje już pracy w nieskończoność.
- **Zakres zlecenia to katalog jego znacznika** — zapisy poza nim są odrzucane, żeby praca
  nie rozlewała się na sąsiednie repozytoria i inne produkty.
- **Nic nie jest zabijane, skracane ani odbierane**: procesy w tle, narzędzia i
  orkiestracja agentowa (`Task`, `Agent`, `Workflow`) działają normalnie. Odrzucane jest
  wyłącznie CZEKANIE na wynik na pierwszym planie — w trakcie takiego wywołania nie odpala
  się żaden hook i wiadomość użytkownika nie ma jak dojść. Wywołania oznaczone jako praca
  w tle przechodzą bez zmian.
- **Zniesiono skrzynkę poleceń i okno oddechu.** Obie protezy powstały przy założeniu, że
  wpisy użytkownika docierają dopiero na końcu tury. W rzeczywistości klient dostarcza je
  na granicy najbliższego wywołania narzędzia, więc przy zakazie czekania na pierwszym
  planie wiadomość z czatu dochodzi od razu i nie potrzeba pliku pośredniego.
- **Kompresja kontekstu przechodzi bez przeszkód i tryb ją przeżywa.** Nowy hook
  `PreCompact` niczego nie blokuje (także w awaryjnej ścieżce bez Pythona): zapisuje stan
  zlecenia do `.danaco/stan-zlecenia.md` i przypomina, że tryb obowiązuje dalej, a
  `SessionStart` podaje ten stan po kompresji i przy wznowieniu sesji. Bez tego kompresja
  albo się nie odbywała, albo model po niej nie wiedział, nad czym pracuje.
- **Cisza na czacie w trakcie zlecenia.** Komunikat hooka `Stop` i SKILL.md wymagają, by
  model nie pisał relacji z postępów: bez zapowiedzi, streszczeń kroków i podsumowań
  etapów. Raport — krótki, w punktach — powstaje dopiero po `/stop`. Powód: użytkownik i
  tak tej relacji nie czyta, a każdy akapit zużywa kontekst potrzebny na pracę.
- `skills/pracuj/SKILL.md` skrócone do reguł trybu: paczka nie narzuca już metody pracy
  ani prowadzenia dziennika — zlecenie użytkownika jest jedynym zakresem obowiązków.

### Dodane

- **Blokada podagentów `/blokada`** (paczka `blokada`): po tym poleceniu model pracuje
  wyłącznie samodzielnie — `Task`, `Agent` i `Workflow` są odrzucane, również uruchamiane
  w tle. Blokada trwa najwyżej 12 godzin albo do polecenia `/blokada-stop`, wiąże się
  z sesją, w której ją włączono, i jest niezależna od trybu ciągłej pracy (`/stop` jej nie
  zdejmuje). Stan trzyma plik `.danaco/blokada-subagentow.json` zapisywany przez hook
  `UserPromptSubmit`, więc model nie może jej ani włączyć, ani zdjąć.

### Zweryfikowane

- `tests/` — 195 testów, wszystkie przechodzą.

## [2.1.0] — 2026-09-03

Wydanie usuwa dziurę w projekcie trybu ciągłej pracy: użytkownik nie miał jak odezwać się
do modelu, dopóki tryb był aktywny.

### Przyczyna

Claude Code dostarcza modelowi wpisy użytkownika w momencie zakończenia tury. Hook `Stop`
odrzuca każde zakończenie tury, a własny limit klienta — osiem kolejnych blokad — zeruje
się przy każdym użyciu narzędzia, więc model realnie pracujący nigdy go nie dobija. Tura
nie kończyła się nigdy, a wpisy użytkownika stały w kolejce nieodczytane. Wady nie było
widać w wersji 1.1.0, bo blokada tam często w ogóle nie działała: znacznik był zakładany
w katalogu roboczym, a szukany od korzenia projektu (ustalenie A2-01), więc z podkatalogu
strażnik nie znajdował nic i przepuszczał zakończenie tury. Naprawa blokady w 2.0.0
odsłoniła dziurę, która istniała od początku.

### Dodane

- `scripts/skrzynka.py` i `hooks/skrzynka.sh` — skrzynka poleceń użytkownika. Plik
  `.danaco/skrzynka.txt` powstaje razem ze znacznikiem, a hook `PostToolUse` czyta go po
  każdym użyciu narzędzia i przekazuje nowe linie do kontekstu tury kodem 2 (w tym
  zdarzeniu kod 2 nie przerywa wykonanej już operacji). Każda linia dochodzi dokładnie
  raz; pozycja odczytu w `.danaco/skrzynka.pozycja`.
- Odrzucanie frazy potwierdzenia w skrzynce. Skrzynka jest kanałem poleceń, nie drogą
  zakończenia zlecenia; blokadę zdejmuje wyłącznie wpis użytkownika na czacie
  (`UserPromptSubmit` z frazą podpisaną w znaczniku). Filtr jest w kodzie skryptu, nie
  w treści polecenia hooka.
- Rozdział „Wiadomość użytkownika w trakcie tury” w `skills/pracuj/SKILL.md`:
  pierwszeństwo polecenia ze skrzynki nad bieżącym krokiem, zależność opóźnienia od
  kadencji wywołań, zakaz łączenia długich zleceń podagentów w jeden nieprzerwany blok
  (blok bez wywołania pośredniego zamyka skrzynkę na cały swój czas) oraz zakaz
  zapewniania użytkownika, że jego wpis na czacie dojdzie.
- Rozdział „Budżet czasu jednego zlecenia podagenta” w
  `skills/orkiestracja-agentow/SKILL.md` — budżet czasu niezależny od budżetu tokenów,
  podział bloków równoległych na partie, przerwanie zlecenia z wynikiem częściowym.

### Zachowanie przy awarii

Skrzynka jest kanałem wygody, nie bramką bezpieczeństwa. Brak znacznika, brak interpretera
Pythona, niekompletna instalacja i pusta skrzynka dają kod 0 i ciszę — niedostępność
skrzynki nigdy nie przerywa pracy ani nie udaje naruszenia dyscypliny.

## [2.0.1] — 2026-09-03

Wydanie jednej reguły: prowadzenie rozmowy z użytkownikiem w trakcie długiej tury.

### Dodane

- Rozdział „Wiadomość użytkownika w trakcie tury” w `skills/pracuj/SKILL.md`. Wiadomość
  wpisana przez użytkownika, kiedy tura trwa, jest dostarczana wraz z wynikiem
  najbliższego wywołania narzędzia, a nie na granicy tury. Tryb ciągłej pracy wydłuża
  tury do godzin, więc sam wytwarza ryzyko, że użytkownik pisze w próżnię. Reguła
  narzuca kadencję wywołań (nie dłużej niż kilka minut bez wywołania), zakaz łączenia
  długich zleceń podagentów w jeden nieprzerwany blok, pierwszeństwo przychodzącej
  wiadomości nad bieżącym krokiem oraz zakaz tłumaczenia użytkownikowi, że wiadomość
  „nie dotarła”, przed sprawdzeniem własnej kadencji wywołań.
- Rozdział „Budżet czasu jednego zlecenia podagenta” w
  `skills/orkiestracja-agentow/SKILL.md` — budżet czasu niezależny od budżetu tokenów,
  podział bloków równoległych na partie, przerwanie zlecenia po przekroczeniu budżetu
  czasu z wynikiem częściowym.

### Uwaga o zakresie

Rozważana i odrzucona była skrzynka czytana strumieniem przez narzędzie `Monitor`
(z wyjątkiem w strażniku dla tego narzędzia). Powód odrzucenia: `Monitor` dostarcza
zdarzenia tą samą drogą co wpisy użytkownika, więc nie omijał granicy tury i nie usuwał
przyczyny ciszy. Skrzynka wróciła w wydaniu 2.1.0, podłączona do hooka `PostToolUse`,
który odpala się po każdym użyciu narzędzia i granicy tury nie potrzebuje.

## [2.0.0] — 2026-09-03

Wydanie porządkujące po audycie manifestów, dokumentacji, hooków, kodu wykonywalnego,
paczek skilli i integralności paczki. Weryfikowane na Claude Code 2.1.257.

### Dodane

- Plik `LICENSE` — licencja zastrzeżona Danaco Holding Group Sp. z o.o., użytek wewnętrzny.
  Pole `license` w `.claude-plugin/plugin.json` wskazuje ten plik.
- Plik `CHANGELOG.md` — historia zmian wyprowadzona z `README.md`.
- Plik `.gitignore` — reguły dla artefaktów Pythona, plików tymczasowych, artefaktów
  systemów plików oraz katalogu roboczego znacznika `.danaco/`.
- Plik `hooks/README.md` — opis zarejestrowanych zdarzeń, kodów wyjścia każdego hooka,
  granicy szukania znacznika i przenośności wrapperów.
- Hook `SessionStart` (tryb `sesja` wrapperów `hooks/straznik.sh` i `hooks/straznik.ps1`) —
  nowa sesja otwarta w katalogu z aktywnym znacznikiem dostaje na starcie ścieżkę
  znacznika, opis zlecenia, datę założenia i liczbę zapisanych kroków. Tryb zawsze
  kończy się kodem 0, także bez interpretera Pythona.
- Jawne limity czasu (`timeout`) dla każdego zarejestrowanego zdarzenia: 10 s dla
  `PostToolUse`, 15 s dla `SessionStart`, 30 s dla `Stop`, `PreToolUse`
  i `UserPromptSubmit`. Bez jawnego limitu przekroczenie domyślnego limitu było
  traktowane jako błąd niepowodujący blokady, czyli hook `Stop` przepuszczał turę.
- Sekcje `Wymagania`, `Instalacja`, `Znane ograniczenia` i `Licencja` w `README.md`
  oraz kolumna „Kiedy się uruchamia” w tabeli szesnastu paczek.

- Katalog `wspolne/standardy-zawodowe/` — jedna kanoniczna kopia standardów zawodowych
  zamiast czterech identycznych kopii w paczkach. Paczki odsyłają do niej ścieżką
  `../../wspolne/standardy-zawodowe/<plik>.md`, liczoną od korzenia paczki.
- Plik `skills/kodowanie/references/engineering-core/spis.md` — spis czterdziestu pięciu
  plików pięciu podpaczek `engineering-core` z jednozdaniowym przeznaczeniem każdego.
  Bez tego spisu 703 kB najświeższego materiału pluginu było nieosiągalne: `SKILL.md`
  paczki `kodowanie` podawał wyłącznie nazwy katalogów w prozie.
- Plik `skills/standard-redakcyjny-jezykowy/references/plik-referencyjny-skilla.md` —
  konwencja zapisu odsyłaczy w plikach paczek.
- Cztery nowe pliki testowe: `tests/test_walidatory.py`, `tests/test_mass_actions.py`,
  `tests/test_audyt_smieci.py`, `tests/test_kontrakt.py`. Zestaw testów wzrósł
  ze 124 do 265 przypadków przechodzących (190 w uruchomieniu przez `unittest`).
- Zdanie delimitujące w opisie każdej z szesnastu paczek — mówi, czego paczka nie
  obejmuje i do której paczki należy sięgnąć zamiast niej.

### Naprawione

- Hook `PostToolUse` nie dostarczał naruszeń do modelu. Walidatory pisały na standardowe
  wyjście, a hook kończył się kodem 0 — przy tym kodzie standardowe wyjście trafia
  wyłącznie do transkrypcji. Naruszenia idą teraz na standardowe wyjście błędów, a hook
  kończy się kodem 2, który w tym zdarzeniu nie blokuje narzędzia, lecz przekazuje raport
  do kontekstu tury. Plik bez naruszeń nie generuje żadnego wyjścia.
- Hook `PostToolUse` przerywał się komunikatem „unbound variable”, gdy zmienna
  `CLAUDE_PLUGIN_ROOT` nie docierała do powłoki hooka. Katalog pluginu jest teraz
  ustalany awaryjnie ze ścieżki skryptu.
- Zapisy plików powyżej około 128 kB nie były w ogóle sprawdzane. Całe zdarzenie było
  przekazywane jako argument wiersza poleceń, co przy dużej treści pliku kończyło się
  błędem „Argument list too long”, pustą ścieżką i cichym pominięciem kontroli.
  Zdarzenie jest teraz czytane ze standardowego wejścia.
- Znacznik zadania w toku był szukany w górę drzewa katalogów bez granicy, aż do korzenia
  systemu plików. Jeden znacznik w katalogu domowym blokował zakończenie tury we
  wszystkich projektach pod nim, w każdej kolejnej sesji. Wędrówka w górę zatrzymuje się
  teraz na korzeniu repozytorium git, na `CLAUDE_PROJECT_DIR` albo po ośmiu poziomach,
  a znacznik w katalogu domowym i w korzeniu systemu plików nie jest uznawany.
- Komunikat blokady podaje absolutną ścieżkę katalogu znacznika, bez której awaryjna
  instrukcja usunięcia katalogu `.danaco` wymagała zgadywania.
- Wzorzec zdarzenia `PostToolUse` pomijał narzędzia `MultiEdit` i `NotebookEdit`, choć
  wzorzec `PreToolUse` w tym samym pliku uznawał je za narzędzia zapisu. Kontrola
  dyscypliny była obchodzona samym wyborem narzędzia zapisu. Wydobycie ścieżki obsługuje
  teraz również pole `notebook_path`.
- Wzorce narzędzi są zakotwiczone z obu stron. Wzorzec niezakotwiczony dopasowywał także
  nazwy zawierające dopasowany ciąg, na przykład `BashOutput` przez `Bash`.
- Hook `PostToolUse` wymuszał `bash` i `python3`, wbrew analizie przenośności zapisanej
  w drugim wrapperze tego samego katalogu. Jest teraz w POSIX `sh`, rejestrowany przez
  `sh` i szuka interpretera w kolejności `python3`, `python`, `py -3`; bez Pythona
  zgłasza brak kontroli i przechodzi dalej, nie blokując pracy.
- Hook `PostToolUse` scalał standardowe wyjście błędów walidatorów z ich raportem, więc
  ślad wyjątku Pythona wyglądał identycznie jak naruszenie dyscypliny. Strumienie są
  rozdzielone, a brakujący plik walidatora daje jawny komunikat o niekompletnej instalacji.
- Walidatory były uruchamiane bez limitu czasu i bez rozpoznania własnej awarii. Każdy
  kod wyjścia poza 0, 2 i 3 jest teraz raportowany jako awaria walidatora, a nie jako
  wynik kontroli.
- `tests/uruchom_testy.sh` przekazywał sterowanie pierwszemu znalezionemu interpreterowi
  bez sprawdzenia wersji, więc `python` wskazujący Pythona 2 kończył się błędem składni.
  Skrypt sprawdza teraz wersję minimalną 3.10 i zna kandydata `py -3`.
- `README.md` nie zawierał sekcji o wymaganiach, instalacji ani licencji, a zależność od
  Pythona 3 — bez którego hook `Stop` blokuje turę — była opisana wyłącznie w instrukcji
  instalacji na serwerze.
- Opis w `.claude-plugin/plugin.json` liczył 387 znaków i był wyliczeniem spisu treści.
  Zastąpiony jednym zdaniem. Opis w `.claude-plugin/marketplace.json` mówił o „16 paczkach
  skilli plus tryb ciągłej pracy”, co dawało siedemnaście pozycji przy szesnastu
  faktycznych; oba pliki mają teraz identyczny opis i identyczną wersję.

- Nazwy wymyślone w bramkach akceptacji: cel `danaco-standard` nie istniał (rzeczywisty
  cel Taskfile'a nazywa się `standard`), a `danaco-kody`, `danaco-komentarze`
  i `danaco-terminy` nie odpowiadały żadnej regule walidatorów. Wpisane zostały
  rzeczywiste nazwy siedmiu reguł odczytane z kodu. Plugin łamał tu własny zakaz
  z paczki `standardy-nazewnictwa`, i to w bramce nazywanej wyrocznią pętli.
- Kolizja wyzwalania paczek `pracuj` i `weryfikatory-dyscypliny`: obie miały dosłownie tę
  samą frazę „nie przerywaj pracy", a wygranie drugiej dawało instrukcję obsługi
  walidatorów, która trybu ciągłej pracy nie uruchamia — znacznik nie powstawał
  i nikt się o tym nie dowiadywał. Fraza należy teraz wyłącznie do `pracuj`.
- Sprzeczność jednostki progu udziału komentarzy: paczka normatywna podawała procent
  wierszy, walidator liczy znaki. Opisany jest stan zgodny z kodem, wraz z progiem
  minimalnego rozmiaru pliku.
- Jedenaście plików `SKILL.md` leżało wewnątrz katalogów `references/`, gdzie system
  skilli ich nie rozpoznaje, a ich frontmatter opisywał warunki wyzwalania. Sześć
  w `engineering-core` przemianowano na `przeglad.md`, pięć katalogów paczki `ui-ux-pro`
  spłaszczono do plików `references/<nazwa>.md`; frontmatter usunięty.
- Sto dziesięć martwych odsyłaczy w plikach referencyjnych — ścieżki liczone od dawnego
  korzenia paczki. W dwóch przypadkach odsyłacz trafiał w plik o innej treści, bo nazwa
  występowała w paczce dwukrotnie.
- Sześćdziesiąt jeden odwołań do siedemnastu paczek, które nie istnieją.
- Znacznik zadania w toku był zakładany w katalogu roboczym, a szukany w katalogu
  roboczym, katalogach nadrzędnych i `CLAUDE_PROJECT_DIR`. Znacznik założony
  z podkatalogu był niewidoczny z korzenia projektu i cała blokada cicho przestawała
  działać. Miejsce znacznika jest teraz wyznaczane deterministycznie.
- Brak skryptu walidatora dawał wynik „zielono": `mass_actions.py verify` kończył się
  kodem 0, choć walidator nigdy się nie uruchomił. Nieobecność narzędzia to teraz
  niepowodzenie kontroli z kodem 4.
- Dopasowanie tagów systemowych zwalniało blokadę zakończenia tury przy tagu
  z atrybutem, tagu niedomkniętym i innej nazwie tagu — jedyne miejsce mechanizmu
  działające w kierunku niebezpiecznym. Gdy pochodzenia frazy nie da się rozstrzygnąć,
  blokada zostaje.
- `skills/kontrola-jakosci/scripts/audyt_smieci.py --usun` usuwał każdy pusty katalog
  w drzewie i wchodził do `node_modules` oraz `.venv`. Domyślny tryb to teraz podgląd,
  usuwanie działa tylko według jawnych wzorców, katalogi zależności i wytworów są
  pomijane, a usuwanie pustych katalogów wymaga osobnego przełącznika.
- Ścieżka zapisu generowanego kodu w `contract_tool.py` pochodziła z danych wejściowych
  i nie była ograniczana do katalogu głównego — kontrakt mógł zapisać plik poza
  repozytorium. Ścieżki są teraz normalizowane i ograniczane.
- Dwa obejścia strażnika (`rm -rf .dan*co`, `mv hooks hooks_off`) oraz fałszywe trafienie
  blokujące czytanie własnych źródeł pluginu.
- Materiał UI opisywał generację poprzednią: mapowanie `hsl(var(--x))`
  w `tailwind.config.ts` zamiast `@theme inline` z OKLCH, `React.forwardRef` usunięty
  z komponentów shadcn/ui, `require()` w module ESM (kod niewykonalny).
  Norma dostępności ujednolicona na WCAG 2.2 wraz z dziewięcioma brakującymi kryteriami;
  OWASP odniesiony do wydania 2025. Wersje sprawdzone w sieci, nie wpisane z pamięci.
- Polecenia uruchamiania skryptów podawane jako `python3 scripts/...` zawodziły
  z katalogu roboczego użytkownika. Wszystkie wystąpienia w szesnastu paczkach mają
  teraz postać `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
- `tests/uruchom_testy.sh` uruchamiał wyłącznie jeden plik testowy — uruchamia teraz
  cały zestaw.

### Zmienione

- Wersja pluginu 2.0.0.
- Klucz `description` usunięty z `hooks/hooks.json`; jedynym kluczem najwyższego poziomu
  jest `hooks`, zgodnie ze schematem konfiguracji hooków. Treść opisu przeniesiona do
  `hooks/README.md`.
- Historia zmian przeniesiona z `README.md` do tego pliku.
- Pochodzenie materiału źródłowego przeniesione z `README.md` do wpisu wersji 1.0.0.

- Nazwa pluginu zmieniona z `danaco-expert-pro` na `danaco-plugin` (nazwa widoczna:
  Danaco Plugin). Wywołanie paczek zmienia się z `danaco-expert-pro:<paczka>`
  na `danaco-plugin:<paczka>`. Nazwy szesnastu paczek pozostają bez zmian.
- Opis w `.claude-plugin/plugin.json` skrócony ze 452 do 166 znaków.
- Katalog współdzielony pluginu nosi nazwę `wspolne/`, nie `shared/` — nazwa `shared/`
  kolidowała z katalogiem `shared/` repozytorium docelowego, do którego plugin odsyła
  w kilkudziesięciu miejscach (`shared/contract.json`).
- Opisy wszystkich szesnastu paczek przepisane: konkretne frazy wyzwalające, tryb
  rozkazujący, rozgraniczenie wzajemne. Rozgraniczenie `design-systemowy` ↔ `ui-ux-pro`
  podane identycznie w obu opisach; roszczenie do projektowania tokenów usunięte
  z `ui-ux-pro`.
- Ciała paczek ujednolicone do układu: kiedy stosować, procedura, kryteria zakończenia,
  ścieżki plików referencyjnych, rozgraniczenie z paczkami sąsiednimi.
- Konfiguracja i progi walidatorów wyniesione z kodu do `konfiguracja-dyscypliny.json`.

### Usunięte

- Sekcja `Uwaga o duplikatach źródłowych` z `README.md` — opisywała archiwa z katalogu
  roboczego autora, których w paczce nie ma.
- Artefakty uruchomień pozostawione w drzewie paczki: katalogi `__pycache__`,
  katalog `.pytest_cache`, pliki `.pyc`.

- Cztery identyczne kopie katalogu `standardy-zawodowe` w paczkach — 143 kB nadmiaru
  i gwarancja rozjazdu po pierwszej edycji.
- Sto dwadzieścia pięć wierszy w `weryfikatory-dyscypliny/SKILL.md` pisanych do
  użytkownika, nie do modelu, wraz z obserwacjami dotyczącymi jednego numeru wydania
  klienta i konfiguracji jednej maszyny.
- Oznaczenia `SK-1`…`SK-7` oraz `A1`–`A4` — własna numeracja niezgodna z zakazem
  z paczki `standardy-nazewnictwa`.

## [1.1.0] — wcześniejsze wydanie

Poprawki mechanizmu trybu ciągłej pracy dla sytuacji, w których model „sam kończył”:

- hook `Stop` przepuszczał turę, gdy klient nie przekazał `transcript_path` — zaczął
  blokować;
- wrapper zakładał `python3` i `bash` — zastąpiony wrapperem POSIX `sh` z wyszukiwaniem
  `python3`, `python`, `py -3`; brak Pythona oznacza blokadę z komunikatem;
- komunikat blokady zawierał frazę potwierdzenia i trafiał do transkrypcji jako wpis
  użytkownika — komunikaty przestały zawierać frazę, a skaner pomija wpisy meta,
  streszczenia i wyniki narzędzi;
- fraza w wiadomości sprzed założenia znacznika zwalniała blokadę przy pierwszym `Stop` —
  liczą się tylko wiadomości późniejsze;
- `cd` do podkatalogu wyłączało blokadę, bo znacznik był szukany tylko w katalogu
  bieżącym — doszły katalogi nadrzędne i `CLAUDE_PROJECT_DIR`;
- `AskUserQuestion` i edycja plików mechanizmu były zabronione tylko behawioralnie —
  doszło zdarzenie `PreToolUse`;
- `plugin.json` wskazywał `hooks/hooks.json`, który Claude Code ładuje automatycznie;
  nowsze wersje klienta zgłaszały to jako błąd ładowania hooków — wpis usunięty;
- doszła droga zwolnienia blokady przez `UserPromptSubmit`, niezależna od transkrypcji.

## [1.0.0] — wydanie pierwsze

Konsolidacja trzech wcześniejszych pluginów (`danaco-code`, `danaco-console`,
`danaco-dyscyplina`) oraz materiału dodatkowego w jeden plugin o szesnastu paczkach
skilli. Wcześniejsze wersje opisywały standardy prozą — walidator dyscypliny był
wzmiankowany w opisie paczki, ale nie istniał jako uruchamialny kod; to wydanie dodało
działające skrypty na bibliotece standardowej Pythona i powłoce, bez zależności
zewnętrznych.

Pochodzenie materiału źródłowego:

- `danaco-code`, `danaco-console`, `danaco-dyscyplina` — pluginy przeniesione bez zmiany
  nazw skilli;
- materiał projektowy wchłonięty do paczki `ui-ux-pro` (tauri-ui, wydajność frontu,
  design interfejsu, weryfikacja wizualna, dostępność WCAG);
- materiał inżynierski wchłonięty jako uzupełnienie paczek
  `architektura-i-dokumentacja`, `kodowanie` i `most-tauri`;
- materiał kontroli jakości wchłonięty do paczki `kontrola-jakosci`;
- materiał komponentów interfejsu (shadcn/ui, Tailwind) jako podstawa paczki `ui-ux-pro`;
- standard redakcyjny i językowy jako podstawa paczki `standard-redakcyjny-jezykowy`.
