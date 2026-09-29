# Techniki zaawansowane — warsztat diagnostyczny klasy zawodowej

Karta rozwija etapy 2 i 3 procedury głównej o techniki stosowane, gdy proste
czytanie śladu stosu i przeglądanie kodu nie wystarcza. Zasada nadrzędna bez
zmian: każda technika ma dostarczyć obserwację zdolną obalić hipotezę, nie
utwierdzić diagnostę w przekonaniach.

## Bisekcja historii

Bisekcja przekształca pytanie „co zepsuło program” w pytanie „która zmiana” —
a na nie odpowiada wyszukiwanie binarne, nie intuicja.

### git bisect z automatem

Ręczna bisekcja jest podatna na błąd oznaczenia (jedno pomylone `good`/`bad`
unieważnia przebieg). Gdy błąd daje się wykryć poleceniem, pisz skrypt i oddaj
bisekcję automatowi:

```
git bisect start
git bisect bad HEAD
git bisect good v2.4.0
git bisect run ./test-blad.sh
```

Skrypt `test-blad.sh` musi zwracać kod 0 dla rewizji poprawnej, 1–124 lub
126–127 dla wadliwej, oraz 125 dla rewizji niesprawdzalnej (np. nie kompiluje
się z powodu niezwiązanym z diagnozą) — kod 125 każe bisekcji pominąć rewizję
zamiast błędnie ją oznaczyć. W skrypcie odtwarzaj dokładnie scenariusz z
etapu 1 procedury. Po zakończeniu wykonaj `git bisect log` (zachowaj do
raportu) i `git bisect reset`.

Wynik bisekcji wskazuje rewizję, nie mechanizm — etap 3 procedury nadal
obowiązuje: przeczytaj diff wskazanej rewizji i wyjaśnij, dlaczego ta zmiana
wywołuje objaw. Jeżeli nie potrafisz, bisekcja mogła paść ofiarą błędu
niedeterministycznego — patrz sekcja o heisenbugach.

### Bisekcja danych i konfiguracji

Bisekcja nie ogranicza się do rewizji kodu. Ten sam algorytm połowienia stosuj do:

- **Danych wejściowych** — plik o 100 000 wierszy wywołuje błąd: podziel na pół,
  sprawdź obie połowy, powtarzaj na połowie wadliwej — po kilkunastu krokach
  masz wiersz-sprawcę. Jeżeli żadna połowa osobno nie wywołuje błędu, sprawcą
  jest kombinacja wierszy — stosuj delta debugging (niżej).
- **Konfiguracji** — dwa środowiska, jedno działa: wypisz różnice (`diff` na
  zrzutach zmiennych środowiskowych, plików ustawień, wersji zależności),
  następnie przenoś różnice połówkami z konfiguracji wadliwej do działającej,
  aż zostanie pojedynczy klucz.
- **Zależności** — regresja po aktualizacji wielu pakietów naraz: przywróć plik
  blokady wersji z rewizji działającej, potem aktualizuj pakiety połówkami.
- **Migracji bazy** — stosuj migracje do połowy listy, sprawdzaj, połowij dalej.

Warunek stosowalności każdej bisekcji: wykrywalność błędu deterministyczna albo
sprowadzona do deterministycznej (pętla powtórzeń — niżej), a kryterium
`good`/`bad` jednoznaczne i zapisane przed startem.

## Minimalizacja przypadku

Najmniejszy przypadek wywołujący błąd to najcenniejszy materiał diagnostyczny:
usuwa z pola widzenia wszystko, co dla mechanizmu nieistotne.

### Delta debugging — systematyczne połowienie wejścia

Postępuj algorytmicznie, nie „na wyczucie”:

1. Podziel wejście (dane, kroki scenariusza, opcje) na n części (start: n = 2).
2. Sprawdź każdą część osobno oraz każde dopełnienie (wejście bez tej części).
3. Jeżeli któraś część lub dopełnienie nadal wywołuje błąd — przyjmij ją za nowe
   wejście i wróć do kroku 1.
4. Jeżeli nic nie wywołuje błędu — zwiększ n dwukrotnie (drobniejsze cięcie)
   i powtórz; zakończ, gdy n przekracza liczbę elementów.

Wynikiem jest wejście 1-minimalne: usunięcie dowolnego pojedynczego elementu
gasi błąd. Każdą próbę wykonuj tym samym skryptem-wyrocznią co przy bisekcji.
Przy danych strukturalnych (JSON, SQL, HTML) tnij po granicach struktury, nie
po bajtach — inaczej większość prób odpada na błędzie składni.

### Minimalizacja programu do reprodukcji dziesięcioliniowej

Docelowa postać reprodukcji: samodzielny program rzędu dziesięciu linii, bez
frameworka, bazy i sieci — wywołujący błąd przy każdym uruchomieniu. Dochodź
do niej iteracyjnie: skopiuj ścieżkę wykonania do osobnego pliku,
zastępuj zależności stałymi wartościami podpatrzonymi w środowisku wadliwym
(zrzucone odpowiedzi API, zserializowane wiersze bazy), usuwaj wszystko, po
czego usunięciu błąd nadal występuje. W dziesięciu liniach mechanizm widać
gołym okiem; a jeżeli w trakcie minimalizacji błąd znika, ostatni usunięty
element jest współsprawcą — to także wynik diagnostyczny. Reprodukcja
minimalna staje się wprost testem regresyjnym w etapie 5 procedury.

## Błędy niedeterministyczne (heisenbugi)

Heisenbug znika lub zmienia postać pod obserwacją: po dołączeniu debuggera,
dodaniu wypisu, włączeniu trybu diagnostycznego. Typowe mechanizmy: wyścig
wątków lub procesów, zależność od czasu (timeout, kolejność zdarzeń),
zależność od środowiska (kolejność iteracji po strukturze mieszającej, układ
pamięci, kolejność plików z systemu plików), niezainicjowana pamięć, losowość
bez ustalonego ziarna.

Strategie postępowania:

- **Logowanie o niskiej inwazyjności.** Debugger i wypisy na standardowe
  wyjście zmieniają przeploty czasowe i potrafią zgasić wyścig. Zapisuj
  zdarzenia do bufora w pamięci (czas monotoniczny, identyfikator wątku,
  zdarzenie) i zrzucaj bufor dopiero po wystąpieniu błędu; bufor per wątek,
  bez blokad w ścieżce logowania.
- **Powtarzanie w pętli z licznikiem.** Sprowadź błąd do mierzalnej
  częstotliwości: uruchom scenariusz w pętli 1000 razy, licz wystąpienia.
  Zmiana kodu obniżająca częstotliwość z 3% do 0% w 10 000 prób to dowód
  statystyczny; zmiana, po której częstotliwość nie drgnęła — poprawka
  pozorna. Pętla zamienia też błąd niedeterministyczny w wyrocznię zdatną do
  bisekcji (skrypt zwraca `bad`, gdy błąd wystąpił choć raz na N prób).
- **Przechwytywanie ziarna losowości.** Wypisuj ziarno generatora przy starcie
  każdego przebiegu; po wystąpieniu błędu uruchom ponownie z tym samym ziarnem —
  błąd staje się deterministyczny. Dotyczy to także frameworków losujących
  kolejność testów (pytest-randomly wypisuje ziarno; powtórz z
  `--randomly-seed=...`): błąd zależny od kolejności testów to niemal zawsze
  wyciek stanu między testami.
- **Wzmacnianie wyścigu.** Zamiast czekać na rzadki przeplot, prowokuj go:
  wstaw krótkie uśpienia w podejrzanych punktach, zwiększ liczbę wątków ponad
  liczbę rdzeni. Uśpienie, które podnosi częstotliwość błędu, wskazuje okno
  wyścigu.

## Debugowanie współbieżności

Błąd współbieżności to zawsze pytanie o przeplot: jaka kolejność operacji
wykonawców prowadzi do stanu niespójnego. Diagnozę prowadź tak:

1. Zidentyfikuj współdzielony zasób (zmienna, wiersz bazy, plik, licznik).
2. Wypisz sekwencję przeplotów: rozpisz operacje każdego wykonawcy na odczyty
   i zapisy zasobu i znajdź kolejność naruszającą niezmiennik (klasyka: dwa
   równoległe „odczytaj–zmodyfikuj–zapisz” gubią jedną modyfikację).
   Rozpisanie wykonuj na piśmie w rozmowie — to obserwacja wymagana przez
   etap 3.
3. Potwierdź narzędziem, zanim uznasz przeplot za dowiedziony:
   - **ThreadSanitizer (TSan)** dla C/C++/Rust: kompilacja z
     `-fsanitize=thread`; raportuje pary konfliktujących dostępów ze śladami
     stosu obu wątków. Narzut 5–15× — uruchamiaj na reprodukcji, nie na
     produkcji.
   - **Detektor wyścigów Go**: `go test -race`, `go build -race`; raport
     zawiera oba ślady stosu i moment utworzenia goroutine. Włączaj `-race`
     rutynowo w CI testów.
   - **Sygnatury blokad baz**: w SQLite `database is locked` / `SQLITE_BUSY`
     wskazuje rywalizację o zapis — sprawdź brak `busy_timeout`, transakcje
     trzymane przez czas operacji sieciowych, tryb dziennika (WAL dopuszcza
     czytelników równolegle z jednym piszącym). W PostgreSQL: `pg_locks`
     złączone z `pg_stat_activity` pokazuje, kto na kogo czeka; komunikat
     `deadlock detected` zawiera oba zapytania — gotowy przeplot do rozpisania.

Ostrzeżenie: brak raportu detektora nie dowodzi braku wyścigu — detektory
widzą tylko przeploty, które faktycznie zaszły. Wynik negatywny na jednym
przebiegu jest słabym dowodem; łącz z pętlą powtórzeń.

## Debugowanie pamięci

Rozróżniaj dwie klasy usterek o odmiennych narzędziach i sygnaturach:

- **Nadpisania i dostępy nieprawidłowe** (przepełnienie bufora, użycie po
  zwolnieniu, podwójne zwolnienie): objawiają się awarią daleko od miejsca
  powstania — uszkodzona zostaje cudza pamięć, a pada niewinny kod. Narzędzia:
  **AddressSanitizer (ASan)** — kompilacja z `-fsanitize=address`, narzut ok.
  2×, raport wskazuje miejsce błędnego dostępu oraz alokacji i zwolnienia
  bloku; **Valgrind (memcheck)** — bez rekompilacji, narzut 10–30×, wykrywa
  też odczyty pamięci niezainicjowanej. Gdy pada kod ewidentnie poprawny,
  podejrzewaj nadpisanie z zewnątrz i uruchom reprodukcję pod jednym z tych
  narzędzi, zanim postawisz hipotezę o padającym kodzie.
- **Wycieki** (pamięć przyrasta, program nie pada albo pada z wyczerpania):
  Valgrind `--leak-check=full` klasyfikuje bloki na pewne wycieki (definitely
  lost) i osiągalne przy wyjściu; LeakSanitizer działa w ramach ASan. W
  Pythonie wycieków z licznika referencji szukaj przez **tracemalloc**:
  `tracemalloc.start(25)`, wykonaj cykl operacji podejrzanej ścieżki, porównaj
  `take_snapshot()` przed i po (`snapshot.compare_to(poprzedni, 'traceback')`)
  — różnica wskazuje miejsca alokacji rosnących. Typowi sprawcy: pamięci
  podręczne bez ograniczenia rozmiaru (`lru_cache` bez `maxsize`,
  słowniki-rejestry), domknięcia trzymające duże obiekty.

## Debugowanie wydajności jako debugowanie

Problem wydajnościowy diagnozuj tą samą pięcioetapową procedurą — objaw brzmi
„za wolno” zamiast „pada”. Zasada żelazna: **profil przed hipotezą**. Intuicja
co do miejsca spowolnienia jest skrajnie zawodna; najpierw zmierz, które 3%
kodu zjada 97% czasu, potem formułuj hipotezy wyłącznie o zmierzonych
ogniskach.

- **Python — cProfile**: `python -m cProfile -o profil.out program.py`, potem
  `python -m pstats profil.out` (`sort cumtime`, `stats 20`). Kolumna
  `tottime` prowadzi do ognisk obliczeniowych, `cumtime` — do
  architektonicznych. Wykresy płomieniowe: `py-spy record -o profil.svg --
  python program.py`; proces już działający — `py-spy dump --pid`.
- **Bazy danych — EXPLAIN**: wykonaj `EXPLAIN ANALYZE` (PostgreSQL) lub
  `EXPLAIN QUERY PLAN` (SQLite) na rzeczywistych danych — plan na pustej
  tabeli kłamie, bo optymalizator wybiera według statystyk wolumenu.
  Sygnatury: skan sekwencyjny tam, gdzie oczekiwano indeksu; złączenie pętlą
  zagnieżdżoną o wielkiej krotności; rozjazd estymaty i rzeczywistości
  (`rows=10` szacowane, `rows=1000000` faktyczne) — wtedy najpierw `ANALYZE`.
- **Przeglądarka — Chrome DevTools Performance**: nagraj przebieg; czytaj
  długie zadania (Long Tasks) blokujące wątek główny, wymuszone przeliczenia
  układu (naprzemienne odczyty i zapisy geometrii DOM w pętli), czas skryptów
  vs renderowania. Zakładka Network z wyłączoną pamięcią podręczną odróżnia
  wolny frontend od wolnego API.

Po każdej zmianie mierz ponownie tym samym scenariuszem i przytaczaj obie
liczby (przed/po) w raporcie — poprawa deklarowana bez pomiaru nie istnieje.

## Punkty obserwacyjne i warunkowe pułapki

Zwykła pułapka zatrzymuje za każdym przejściem — bezużyteczna w pętli o
milionie iteracji. Stosuj:

- **Pułapki warunkowe**: zatrzymanie tylko przy spełnieniu predykatu.
  GDB: `break plik.c:120 if licznik == 4999`; pdb (Python):
  `b modul.py:120, wartosc is None`; debuggery IDE — pole „condition”.
  Warunek formułuj na danych, nie na iteracji, jeżeli to dane są podejrzane.
- **Punkty obserwacyjne (watchpoints)**: zatrzymanie przy zmianie wartości —
  odpowiedź na pytanie „kto nadpisuje to pole”. GDB: `watch zmienna`
  (zapis), `rwatch` (odczyt), `awatch` (oba); sprzętowe działają bez
  spowolnienia, programowe spowalniają wykonanie znacznie. Technika
  pierwszego wyboru, gdy stan psuje się „nie wiadomo kiedy” między dwoma
  znanymi punktami.
- **Pułapki licznikowe**: `ignore <nr> 4999` w GDB pomija pułapkę zadaną
  liczbę razy — szybsze niż warunek, gdy numer iteracji znasz z logów.

## Technika dwóch implementacji

Gdy spór dotyczy poprawności wyniku (obliczenia finansowe, transformacja
danych, algorytm zoptymalizowany), zbuduj implementację odniesienia: naiwną,
bez optymalizacji — kilkanaście linii, których poprawność widać przy
czytaniu. Porównuj wyniki obu implementacji bit w bit
na wspólnym zbiorze wejść: przypadki brzegowe dobrane ręcznie plus wejścia
losowe o wypisanym ziarnie. Pierwsze wejście różnicujące jest gotową
reprodukcją minimalną; różnica wskazuje krok optymalizacji, w którym zgubiono
własność. Przy liczbach zmiennoprzecinkowych porównanie bit w bit zastąp
jawnie zadaną i uzasadnioną tolerancją — rozbieżność większa od niej pozostaje
błędem, nie „kwestią zaokrągleń”. Implementację odniesienia po diagnozie
przenieś do testów albo usuń — zgodnie z dyscypliną plików ze standardów
zawodowych (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`).
