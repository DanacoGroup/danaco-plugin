# danaco-praca

Plugin Claude Code z jednym mechanizmem: **trybem ciągłej pracy**. Użytkownik wydaje
zlecenie komendą `/pracuj`, a hooki pluginu odbierają modelowi trzy rzeczy — zakończenie
tury, zadawanie pytań i czekanie na pierwszym planie. Zlecenie zamyka wyłącznie
użytkownik komendą `/stop`.

Wersja 4.6.0. Mechanizm wydzielono z pluginu `danaco-plugin` (wspólna historia do
2.3.2). Paczki standardów inżynierskich i walidatory dyscypliny zostały w tamtym
pluginie; oba da się mieć zainstalowane naraz.

## Komendy

| Komenda | Działanie |
| --- | --- |
| `/pracuj <zlecenie>` | Włącza tryb ciągłej pracy: hook zakłada znacznik zlecenia. |
| `/stop` | Kończy tryb: zdejmuje znacznik, model składa krótki raport. |
| `/blokada` | Blokada podagentów: model pracuje wyłącznie sam, najwyżej 12 godzin. |
| `/blokada-stop` | Zdejmuje blokadę podagentów. |
| `/stop-skrypt` | Blokada pracy maszynowej: koniec z hurtową podmianą treści, bezterminowo. |
| `/skrypt` | Zdejmuje blokadę pracy maszynowej — natychmiast. |

Każda komenda działa też z prefiksem `/danaco-praca:` oraz — jako alias dla sesji
otwartych przed wydzieleniem — z prefiksem `/danaco-plugin:`. Komenda liczy się
wyłącznie na początku wiadomości albo w osobnej linii: wzmianka w cytacie, w ścieżce
czy we wklejonym logu niczego nie uruchamia ani nie zdejmuje.

Tryb włącza i kończy **wyłącznie użytkownik**. Model nie zakłada znacznika z własnej
oceny sytuacji i nie ma technicznej możliwości jego zdjęcia.

## Włączenie trybu

Znacznik zakłada **hook `UserPromptSubmit`**, nie model. W chwili, gdy użytkownik
wysyła wiadomość zaczynającą się od `/pracuj`, hook:

1. wyznacza korzeń projektu z pola `cwd` zdarzenia (kolejno `CLAUDE_PROJECT_DIR`,
   najbliższy katalog z `.git`, katalog roboczy) i odmawia w katalogu domowym oraz
   w korzeniu systemu plików;
2. zapisuje `.danaco/zadania/<sesja>.json` z opisem zlecenia wziętym z treści wiadomości
   po odjęciu komendy, identyfikatorem sesji z pola `session_id`, terminem 24 h i kopią
   zapasową poza katalogiem projektu;
3. wypisuje modelowi katalog zlecenia, treść zlecenia i reguły trybu.

Model nie uruchamia niczego — jeżeli w ogóle nie zareaguje na komendę, tryb i tak
obowiązuje. Do wersji 3.0.1 znacznik zakładał model poleceniem `zadanie.py start`;
pominięcie tego kroku albo uruchomienie go w innym katalogu cicho wyłączało cały
mechanizm, a użytkownik widział wczytaną paczkę i był przekonany, że tryb działa.

Powtórna komenda `/pracuj` niczego nie nadpisuje — hook potwierdza tylko, że tryb jest
aktywny. `scripts/zadanie.py start` zostaje jako droga dla człowieka z terminala.

## Sprawdzenie, czy tryb działa

```bash
python3 scripts/zadanie.py status     # czy tryb aktywny tu i teraz, czyj znacznik, kiedy wygasa
python3 scripts/zadanie.py raport     # co model faktycznie wywołał w zleceniach tego katalogu
python3 scripts/zadanie.py diagnoza   # czy mechanizm w tym katalogu w ogóle zadziała
```

`status` pisze po ludzku: stan trybu, ścieżkę znacznika, zakres zapisów, sesję
właściciela, termin ważności, licznik blokad zakończenia tury i ostatnie kroki.

`diagnoza` odpowiada na pytanie „dlaczego nie działa": czy plugin jest widoczny
w konfiguracji Claude Code, czy interpreter Pythona jest osiągalny z powłoki hooków,
gdzie szukany jest znacznik dla bieżącego katalogu i jaki wynik zwróciłby tu hook
`Stop` (0 czy 2).

## Jak to działa

Znacznik `.danaco/zadania/<sesja>.json` leży w katalogu zlecenia (kopia poza katalogiem
projektu pozwala odtworzyć skasowany plik). Dopóki znacznik żyje — najwyżej 24 godziny — hooki pilnują reguł:

| Zdarzenie | Tryb wrappera | Rola |
| --- | --- | --- |
| `Stop` | `stop` | Nie pozwala zakończyć tury; zwalnia dopiero na widok komendy `/stop` w transkrypcji. |
| `UserPromptSubmit` | `prompt` | Włącza tryb na `/pracuj` i jest jedyną zwykłą drogą zwolnienia. Nigdy nie blokuje wiadomości użytkownika. Obsługuje też `/blokada`, `/blokada-stop`, `/stop-skrypt` i `/skrypt`. |
| `PreToolUse` | `pretool` | Kontrola wszystkich narzędzi (matcher `.*`) — patrz niżej. |
| `PostToolUse` (`Bash`, `PowerShell`) | `kontrola` | Odtwarza znacznik skasowany poleceniem powłoki. |
| `SessionStart` | `sesja` | Nowa sesja w katalogu z aktywnym zleceniem dowiaduje się o nim od razu. |
| `PreCompact` | `kompakt` | Zapisuje `.danaco/zadania/stan-<sesja>.md`, żeby zlecenie przetrwało kompresję kontekstu. |

Cała logika decyzji leży w `scripts/straznik.py`; `hooks/straznik.sh` (POSIX sh) i
`hooks/straznik.ps1` (Windows bez Git Bash) tylko znajdują interpreter Pythona 3
i przekazują mu zdarzenie. Kody wyjścia: 0 przepuszcza, 2 blokuje.

## Kontrola pierwszego planu

Reguła nadrzędna: **model nigdy nie czeka na wynik na pierwszym planie**. W trakcie
trwającego wywołania narzędzia nie odpala się żaden hook, więc użytkownik nie ma jak się
odezwać. Chodzi o czekanie, nie o same procesy — proces ma spokojnie działać, tylko
w tle.

Matcher `PreToolUse` obejmuje wszystkie narzędzia, a rozstrzyga reguła odwrócona:

- **Przepustki** (przechodzą bez sprawdzania reguł pierwszego planu): `Read`, `Glob`,
  `Grep`, `TodoWrite`, `ToolSearch`, `Skill`, `NotebookRead`, `ListMcpResources`,
  `ReadMcpResource`. Bramka ciszy i bramka sprawdzeń stanu obejmują je mimo to — obie
  stoją przed listą przepustek.
- **Odbiór wyniku zadania tłowego** (`TaskOutput`, `BashOutput`, `AgentOutputTool`,
  `BashOutputTool`, `TaskGet`): tylko wariant natychmiastowy — `block: false` albo
  limit czasu do 5 sekund. Wariant domyślny czeka na zakończenie zadania i jest
  odrzucany.
- **Narzędzia z własnymi regułami**: `AskUserQuestion` (odrzucane), harmonogram i
  wybudzenia (odrzucane), `Task`/`Agent`/`Workflow` (tylko w tle),
  `Write`/`Edit`/`MultiEdit`/`NotebookEdit` (zakres zlecenia i ochrona mechanizmu),
  `Bash`/`PowerShell` (filtr heurystyczny plus wymóg pracy w tle: na pierwszym planie
  zostaje wyłącznie wgląd — `ls`, `cat`, `head`, `tail -n`, `grep`, `find`, `wc`,
  `stat`, `sed -n`, `diff`, `git status|log|diff|show`, `ps`, `kill`, `echo`, `pwd`
  i ich odpowiedniki w PowerShellu — pod warunkiem, że polecenie ma z czego czytać
  i gdzie skończyć: `cat` bez pliku czeka na standardowe wejście, `cat /dev/zero` nie
  kończy się nigdy, a `find /` i `grep -r wzorzec /` chodzą po całym dysku, więc te
  postaci wglądem nie są. Każde inne polecenie wymaga `run_in_background`
  albo `nohup … &`, także z krótkim `timeout`; niezależnie od tego zadeklarowany limit
  powyżej 120 sekund wymaga tła nawet dla wglądu).
- **Wszystkie pozostałe**, w tym `mcp__*`, `WebFetch` i `WebSearch`: przechodzą z
  deklaracją pracy w tle albo z limitem czasu do 120 sekund. Rozpoznawane pola limitu:
  `timeout`, `timeout_ms`, `timeoutMs`, `max_duration`, `deadline_s`. Pole `timeout`
  narzędzia powłoki liczone jest w milisekundach, zgodnie z klientem.
- **Narzędzia oczekiwania** (nazwa z `wait`, `sleep`, `poll`) są odrzucane — czekanie
  jest ich jedyną funkcją.
- **Narzędzia wysyłające wiadomość poza turę** (`SendMessage`, `PushNotification`,
  `SlashCommand`, odpowiedniki `mcp__*`) są odrzucane: taka wiadomość wraca do sesji
  wpisem nieodróżnialnym od wpisu użytkownika, więc jest drogą do wstrzyknięcia
  polecenia kończącego.
- **Powłoka pod inną nazwą**: narzędzie MCP z polem `command`, `script` albo `cmd`
  przechodzi ten sam komplet reguł co `Bash` — wymóg tła, zakaz czekania, granice
  wglądu i bramkę sprawdzeń stanu.

Narzędzie, które nie ma żadnego pola limitu i żadnego pola tła, **nie jest blokowane**:
wywołanie przechodzi, a wpis (nazwa narzędzia, czas, powód) trafia do
`.danaco/dziennik-ciszy.jsonl`. Podagent jest wyjątkiem od tej zasady: `Task`, `Agent`
i `Workflow` bez deklaracji pracy w tle są odrzucane także wtedy, gdy klient nie ma
w schemacie pola tła — takie wywołanie czeka na wynik tak samo, a zakres, którego nie
da się zlecić w tle, model wykonuje sam serią krótkich wywołań.

### Zlecenie jest sesyjne

Każda rozmowa ma własne zlecenie: `<projekt>/.danaco/zadania/<sesja>.json`. W jednym
projekcie może ich trwać kilka naraz i są od siebie niezależne:

- `/pracuj` w drugiej rozmowie zakłada **własny** znacznik, nie przejmuje cudzego;
- reguły obowiązują wyłącznie rozmowę, do której zlecenie należy — pozostałe sesje
  w tym samym katalogu pracują normalnie;
- `/stop` zdejmuje **tylko** zlecenie tej rozmowy i wypisuje, ile zleceń innych sesji
  trwa dalej;
- zlecenia z minionym terminem ważności są sprzątane przy każdym `/pracuj`;
- kopia zapasowa (`~/.danaco-kopie`) jest osobna dla każdego zlecenia.

Plik `<projekt>/.danaco/zadanie-w-toku.json` to układ sprzed 4.0.0. Jest czytany dalej:
przypisuje się pierwszej rozmowie, która po niego sięgnie, i zostaje przeniesiony do
pliku sesyjnego razem z kopią.

### Bramka ciszy

Zlecenie ma jeden raport — końcowy. Hook `PreToolUse` czyta ostatnią wypowiedź modelu na
czacie (wyłącznie bloki tekstu) i rozstrzyga po tym, co ją poprzedza:

- wypowiedź **między wywołaniami narzędzi** (po wyniku narzędzia) — odrzucenie
  wywołania, **bez progu długości**: jedno zdanie liczy się tak samo jak akapit;
- wypowiedź **po wiadomości użytkownika** — dozwolona do 350 znaków, powyżej odrzucenie.

Odrzucenie jest jednorazowe dla danej wypowiedzi (identyfikator w
`.danaco/napomnienie-ciszy.json`), więc powtórzone wywołanie przechodzi i praca idzie
dalej, ale każdy kolejny meldunek kosztuje kolejne odrzucone wywołanie. Bramka obejmuje
wszystkie narzędzia, także przepustki. Nieczytelna transkrypcja niczego nie blokuje.

### Powtórzenie i pętla wywołań

Bramka sprawdzeń stanu liczy wyłącznie wywołania, które umie rozpoznać jako zaglądanie
do biegu. Model odpytywał więc stan pliku `.rc` i `pgrep` co kilka sekund przez pół
godziny — formalnie zwykłym poleceniem, którego żadna reguła nie zatrzymywała. Stąd
reguła ogólna, niezależna od klasyfikacji:

- **czwarte podobne wywołanie z rzędu**, które niczego nie zmienia, jest odrzucane;
- **szóste wywołanie z rzędu**, w którym padły najwyżej dwa różne polecenia na przemian,
  jest odrzucane jako pętla;
- **zapis przerywa serię**: `Write`, `Edit` i polecenie z przekierowaniem albo
  z `mv`/`cp`/`rm` zerują licznik, bo powtórzona poprawka tego samego pliku to normalna
  praca;
- po pięciu minutach od ostatniego powtórzenia licznik rusza od nowa.

Podobieństwo liczy się po tym, **co polecenie uruchamia i czego dotyka** (nazwy poleceń
i nazwy plików), a nie po dosłownym tekście: zmiana `printf "%.1fG"` na `printf "%.2fG"`
nie czyni z odpytania nowego wywołania. Cztery różne odczyty, przegląd wielu plików
i pętla „czytaj — popraw — czytaj" przechodzą bez przeszkód.

### Ochrona transkrypcji i potwierdzenie wykonania

Dwie drogi pełnego odłączenia, zamknięte w 4.6.0:

- **Podrobienie polecenia kończącego.** Hook `Stop` zwalnia blokadę na widok `/stop`
  w transkrypcji rozmowy, więc dopisanie tam wiersza roli `user` kończyło tryb.
  Transkrypcja tej rozmowy oraz katalog rozmów klienta (`.claude/projects/`) są teraz
  chronione tak samo jak znacznik — narzędziami plikowymi, powłoką i narzędziami MCP,
  także wtedy, gdy ścieżka leży w zagnieżdżonym polu wywołania
  (`{"files":[{"devicePath": …}]}`).
- **Atrapa interpretera w `PATH`.** Plik `python3` kończący się kodem 0 przepuszczał
  każde wywołanie, bo wrapper widział „interpreter zadziałał". Strażnik zostawia teraz
  potwierdzenie wykonania; kod 0 bez potwierdzenia jest traktowany jako blokada
  (wiadomości użytkownika nie są blokowane nigdy).

### Dziennik pracy i raport

Każde wywołanie narzędzia przy aktywnym zleceniu trafia do
`.danaco/zadania/praca-<sesja>.jsonl` — z czasem, nazwą narzędzia, skróconym poleceniem
i znacznikiem odrzucenia albo pracy w tle. Dziennik **zostaje po zakończeniu zlecenia**:
jest jedynym zapisem tego, co model faktycznie robił.

- Przy `/stop` hook podaje modelowi podsumowanie z dziennika (liczba wywołań, odrzucenia,
  biegi w tle, zapisane pliki) z poleceniem, żeby raport powstał z niego, a nie z pamięci.
- `python3 scripts/zadanie.py raport` pokazuje to samo człowiekowi, dla wszystkich
  rozmów w tym katalogu.
- Dzienniki starsze niż siedem dni są sprzątane przy kolejnym `/pracuj`.

### Czekanie nie jest pracą do przeniesienia w tło

Zakaz czekania na pierwszym planie da się obejść od drugiej strony: zamiast czekać
samemu, model robi z czekania osobne **zadanie tłowe** — pętlę `for i in $(seq 1 28); do
… sleep 20; done` pod nazwą „Wait for the dump to finish" — i znika na kilkanaście minut.
W interfejsie widać wtedy „running task", za którym nie stoi żadna praca.

Odrzucane jest więc każde wywołanie, którego całą treścią jest odliczanie albo
odpytywanie — **także w tle**: `sleep 540`, `wait`, `wait $PID &`, pętla `while`/`until`/
`for` ze `sleep`, `tail --pid`, `flock` bez trybu nieblokującego. Odrzucane jest też
wywołanie, którego opis zapowiada czekanie (`description: "Wait for …"`), a treść
odpytuje stan w pętli.

Osobno liczy się **odliczanie wszyte w polecenie robocze**: `sleep 100; wc -l < plik.tsv`
pod nazwą „Check … distribution" to minutnik z pomiarem doklejonym na końcu, a nie
praca. `sleep` powyżej pięciu sekund — pojedynczy albo w sumie — jest odrzucany
niezależnie od tła; krótka przerwa przed właściwym poleceniem (`sleep 3 && npm test`)
przechodzi.

Praca w tle działa bez zmian: `npm test`, budowa, zrzut bazy, `nohup … &` — także z
krótkim `sleep` przed właściwym poleceniem i z opisem wspominającym oczekiwanie na
wynik. Reguła dotyczy czekania, nie długości pracy.

### Bramka sprawdzeń stanu

Zakaz czekania na pierwszym planie zamknął jedną drogę do przerwy i zostawił drugą:
model puszczał pracę w tło, po czym zamiast robić kolejną część zlecenia odpytywał ten
sam bieg w kółko — `BashOutput`, `tail -n 20 praca.log`, `ps`, znowu `BashOutput`. Każde
takie wywołanie z osobna jest krótkie i legalne, więc żadna reguła go nie zatrzymywała,
a za serią wywołań nie stała ani jedna wykonana praca.

Sprawdzeniem stanu jest: odbiór wyniku zadania tłowego w wariancie natychmiastowym,
przegląd zadań (`TaskList`), polecenia stanu (`ps`, `pgrep`, `jobs`, `sleep`, `date`,
`uptime`) oraz odczyt **logu biegu** poleceniami `tail`, `cat`, `head`, `ls`, `wc`,
`stat` albo narzędziem `Read`. Trzy sprawdzenia pod rząd przechodzą, czwarte jest
odrzucane.

- **Logiem biegu jest plik zarejestrowany przy uruchomieniu biegu w tle** (cel
  przekierowania w poleceniu z `&` albo z `run_in_background`) oraz `nohup.out`. Nazwa
  pliku nie ma znaczenia: `login.tsx`, `blog.md` i `CHANGELOG.md` nie są logami, a
  `wynik.txt` biegu puszczonego w tle — jest. Analiza cudzego logu, którego nikt tu nie
  uruchomił, jest zwykłą pracą.
- **Licznik zeruje wywołanie, które strażnik dopuścił i które wykonuje pracę.**
  Wywołanie odrzucone nie zeruje niczego — nigdy się nie wykonało. Nie zerują też
  narzędzia neutralne (`TodoWrite`, `ToolSearch`, `Skill`) ani powtórzenie tego samego
  odczytu: jedno wywołanie wplecione w kółko między sprawdzenia byłoby darmowym
  zerowaniem.
- **Szukanie wzorca** (`grep`, `sed -n`, `rg`) liczy się jako praca, także na logu —
  chyba że stoi w potoku za sprawdzeniem (`ps aux | grep serwer` jest sprawdzeniem).
- **Zapis nie jest sprawdzeniem**: `echo "krok 3" >> notatki.md` to praca, choć zaczyna
  się od `echo`.
- **Wyjście awaryjne**: po pięciu minutach od ostatniego dopuszczonego sprawdzenia
  licznik rusza od nowa, żeby zlecenie z jedną pozostałą pracą w tle nie kończyło się
  pętlą odrzuceń.
- `sleep` na pierwszym planie jest odrzucany bez względu na długość — nie ma go na
  liście wglądu.

Stan licznika leży w `.danaco/zadania/sprawdzenia-<sesja>.licznik` (rozszerzenie inne
niż `.json` jest wymogiem: każdy `.json` w katalogu `zadania` liczy się jako zlecenie
osobnej rozmowy), a odrzucenia trafiają do `.danaco/dziennik-ciszy.jsonl`.

### Blokada pracy maszynowej (`/stop-skrypt`)

Zbiory danych giną nie od jednej pomyłki w jednym rekordzie, tylko od jednej pętli,
która tę pomyłkę powiela po całym zbiorze. Komenda `/stop-skrypt` odbiera modelowi
hurtową podmianę treści — bezterminowo, do komendy `/skrypt`, która zdejmuje ją
natychmiast. Blokada wiąże rozmowę, w której ją włączono, działa **bez** aktywnego
zlecenia i obowiązuje tak samo w tle jak na pierwszym planie.

Odrzucane są:

- podmiany w miejscu: `sed -i`, `perl -pi`, `awk -i inplace`, `rename`, `rpl`, `sponge`,
  `sd`, `dos2unix`, `recode`, `iconv -o`, `yq -i`;
- hurtowe nadpisanie plików: `patch`, `git apply`, `git checkout -- …`, `git restore`,
  `git stash pop`, `git reset --hard`, `git filter-branch`, `rsync`;
- edytory wsadowe wykonujące skrypt edycji: `ed`, `ex -sc`, `vim -es`;
- `find … -delete` oraz `find … -exec <polecenie zmieniające pliki>`;
- `xargs` i `parallel` z poleceniem zmieniającym pliki;
- pętle powłoki z zapisem (`for`/`while`/`until` … `do` … `done`);
- kod podany wprost (`python -c`, `node -e`, heredoc do interpretera), treść podana do
  wykonania w potoku (`echo "UPDATE …" | sqlite3`, `cat skrypt | python3`,
  `python3 -c "$(cat skrypt)"`) oraz **plik uruchamiany jako program** — niezależnie od
  rozszerzenia — którego treść zawiera pętlę z zapisem, podmianę w miejscu albo zapis do
  bazy; hook czyta go przed uruchomieniem (do 512 kB);
- zapis hurtowy do bazy: `UPDATE`, `DELETE FROM`, `INSERT INTO`, `DROP`, `TRUNCATE`,
  `ALTER TABLE`, `.import`, `COPY … FROM` przez `sqlite3`, `psql`, `mysql`, `mongosh`
  i pokrewne, a także wczytanie pliku `.sql`, **którego treść zmienia bazę** (`psql -f
  raport.sql` z samym `SELECT` przechodzi);
- `replace_all` w narzędziu plikowym oraz wywołanie z ponad 20 zmianami naraz;
- zlecenie hurtowej podmiany podagentowi (rozstrzyga treść zlecenia) i narzędziu MCP
  z polem `command`, `script` albo `cmd`.

Przechodzą: odczyt i analiza (`SELECT`, `.schema`, `grep`, `git diff`), **czytanie pliku
skryptu** (`cat napraw.py`, `grep -n def napraw.py`, `wc -l napraw.py` — blokada dotyczy
uruchomienia, nie czytania), szukanie zakazanej frazy w dokumentacji (`grep -rn 'sed -i'
docs/`), budowa i testy projektu, pętla bez zapisu (`for f in src/*.py; do python3 -m
py_compile $f; done`), pojedyncza zmiana `Edit`/`Write` i notatka cytująca zakazane
polecenie. To filtr heurystyczny — rozstrzyga po kształcie polecenia i po treści pliku,
przed wykonaniem.

Plik blokady: `.danaco/blokada-skryptow.json`; jest chroniony przed skasowaniem tak samo
jak znacznik zlecenia. Stan obu blokad pokazuje `python3 scripts/zadanie.py status`.

### Zakaz zatrzymywania biegów tłowych

Narzędzia klienta zatrzymujące zadania (`TaskStop`, `KillShell`, `KillBash`, `StopTask`
i odpowiedniki `mcp__*`) oraz polecenia powłoki (`pkill`, `killall`, `kill %1`,
`jobs -p | xargs kill`) są odrzucane: bieg puszczony w tło ma dobiec do końca.

Wydajność: matcher `.*` znaczy wywołanie hooka przy każdym narzędziu, więc
`hooks/straznik.sh` sprawdza obecność znacznika i plików blokad w samej powłoce i kończy
się kodem 0 bez uruchamiania Pythona, gdy tryb jest nieaktywny. Zmierzony narzut: około
**9 ms** na wywołanie przy nieaktywnym trybie (przy aktywnym, z uruchomieniem
interpretera — około 46 ms).

## Struktura

```
.claude-plugin/plugin.json      manifest pluginu
.claude-plugin/marketplace.json wpis marketplace
hooks/hooks.json                rejestracja sześciu zdarzeń
hooks/straznik.sh               wrapper POSIX sh (Linux, macOS, Git Bash)
hooks/straznik.ps1              wrapper PowerShell (Windows bez Git Bash)
scripts/straznik.py             logika hooków - całe rozstrzyganie
scripts/znacznik.py             pliki zlecenia, korzeń projektu, rozpoznawanie komend
scripts/zadanie.py              start / krok / status / diagnoza / zakoncz
skills/pracuj, stop, blokada,
  stop-skrypt                   paczki komend
tests/test_straznik.py          testy mechanizmu
tests/uruchom_testy.sh          uruchomienie zestawu bez zależności
```

## Wymagania i testy

Python 3.10 lub nowszy w `PATH` powłoki, w której klient uruchamia hooki. Bez działającego
interpretera i przy aktywnym znaczniku wrapper blokuje (fail-closed) z komunikatem, co
zainstalować; wiadomości użytkownika nie są blokowane nigdy.

```bash
cd danaco-praca
sh tests/uruchom_testy.sh       # zestaw oparty na unittest, bez zależności
```

## Zdjęcie trybu poza sesją

Człowiek może zakończyć zlecenie z własnego terminala:

```bash
python3 scripts/zadanie.py zakoncz
```

albo usuwając katalog `.danaco` wraz z kopią w `~/.danaco-kopie`. Z wnętrza sesji model
tej drogi nie ma — próba liczy się jako obejście blokady.

## Licencja

Patrz plik `LICENSE`.
