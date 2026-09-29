# Katalog usterek do wykrywania w przeglądzie

Karta rozwija procedurę z `references/przeglad-kodu/przeglad-kodu.md`. Każda pozycja: **sygnatura**
(po czym poznać usterkę — wzorce do wyszukania) → **scenariusz** (konkretne
dane → błędny skutek) → **poprawka** (najmniejsza zmiana usuwająca przyczynę,
nie objaw). Zgłaszaj wyłącznie ustalenia poparte scenariuszem.

## A. Bezpieczeństwo

1. **Wstrzyknięcie SQL (CWE-89).** Sygnatura: zapytanie budowane konkatenacją
   lub interpolacją z danymi spoza kodu (`execute(f"`, `execute("... " +`,
   dynamiczne `ORDER BY` ze zmiennej). Scenariusz: parametr `1 OR 1=1` zwraca
   całą tabelę; `1; DROP TABLE users` wykonuje drugie polecenie. Poprawka:
   zapytania parametryzowane dla wartości; dla identyfikatorów (kolumna
   sortowania, tabela) — lista dozwolonych wartości w kodzie.

2. **Wstrzyknięcie polecenia powłoki (CWE-78).** Sygnatura: `os.system`,
   `subprocess` z `shell=True`, `exec`/`spawn` z jednym tekstem polecenia
   zawierającym dane użytkownika. Scenariusz: nazwa pliku `raport.txt; rm -rf ~`
   wykonuje oba polecenia z uprawnieniami procesu. Poprawka: wywołanie bez
   powłoki, z listą argumentów (`subprocess.run([...])`, `execFile`); gdy
   powłoka niezbędna — lista dozwolonych wartości, nie ucieczkowanie.

3. **XSS (CWE-79).** Sygnatura: `innerHTML`, `dangerouslySetInnerHTML`,
   `v-html`, `|safe`, `mark_safe`, HTML składany konkatenacją z danymi
   użytkownika. Scenariusz: komentarz `<img src=x onerror=...>` wykonuje
   skrypt u każdego czytelnika — kradzież sesji. Poprawka: domyślne
   ucieczkowanie silnika szablonów (`textContent`, interpolacja JSX); HTML od
   użytkownika tylko po sanityzacji sprawdzoną biblioteką; CSP jako druga
   warstwa.

4. **Przejście ścieżki (CWE-22).** Sygnatura: ścieżka pliku sklejana z danych
   żądania: `open(base + name)`, `path.join(katalog, nazwa_z_parametru)`.
   Scenariusz: nazwa `../../etc/passwd` wychodzi poza katalog docelowy
   i czyta plik z sekretami. Poprawka: ścieżka kanoniczna (`realpath`,
   `resolve`) i kontrola, że wynik zaczyna się od katalogu bazowego; pliki
   identyfikowane kluczem z bazy, nie nazwą z żądania.

5. **Deserializacja niezaufanych danych (CWE-502).** Sygnatura:
   `pickle.loads`, `yaml.load` bez `SafeLoader`, `unserialize`,
   `ObjectInputStream.readObject` na danych z sieci, pliku, kolejki.
   Scenariusz: spreparowany strumień bajtów tworzy przy deserializacji obiekt
   wykonujący dowolny kod — przejęcie procesu. Poprawka: formaty czysto
   danowe (JSON, protobuf) na granicach zaufania; `yaml.safe_load`; format
   binarny tylko z podpisem sprawdzanym przed deserializacją.

6. **SSRF (CWE-918).** Sygnatura: klient HTTP na adresie z żądania
   (`requests.get(url_z_parametru)`, `fetch(body.url)`); funkcje „podgląd
   adresu”, webhooki. Scenariusz: `http://169.254.169.254/latest/meta-data/`
   odczytuje poświadczenia chmurowe; `http://localhost:8080/admin` sięga do
   usługi wewnętrznej. Poprawka: lista dozwolonych hostów; odrzucenie adresów
   prywatnych **po** rozwiązaniu DNS (także przy przekierowaniach); ruch
   wychodzący przez proxy bez dostępu do sieci wewnętrznej.

7. **Brak autoryzacji na poziomie obiektu — IDOR (CWE-639).** Sygnatura:
   `GET /zasob/{id}`, `UPDATE ... WHERE id = ?` — rekord pobierany wyłącznie
   po identyfikatorze; jest uwierzytelnienie, brak autoryzacji do rekordu.
   Scenariusz: zalogowany użytkownik zmienia `/faktury/1041` na
   `/faktury/1042` i czyta fakturę innego klienta. Poprawka: odczyt i zapis
   z warunkiem własności (`WHERE id = ? AND owner_id = ?`) albo kontrolą
   uprawnień we wspólnej warstwie; test: użytkownik A żąda zasobu
   użytkownika B → 403/404.

8. **Sekrety i PII w kodzie oraz dziennikach (CWE-798, CWE-532).** Sygnatura:
   literały kluczy (`api_key = "`, `password =`), tokeny w konfiguracji
   w repozytorium; logowanie całych obiektów żądania, nagłówka
   `Authorization`, PESEL. Scenariusz: dziennik trafia do systemu agregacji
   z szerokim dostępem — wyciek podlega zgłoszeniu z RODO; klucz z historii
   repozytorium działa po „usunięciu”. Poprawka: sekrety ze zmiennych
   środowiskowych lub magazynu sekretów; klucz ujawniony — unieważnić;
   logowanie pól wybranych jawnie; maskowanie we wspólnym filtrze.

9. **Porównanie sekretów zależne od czasu (CWE-208).** Sygnatura:
   `==`/`equals` na tokenie, podpisie HMAC, kodzie jednorazowym. Scenariusz:
   porównanie przerywa na pierwszym różnym bajcie — pomiar czasu odpowiedzi
   odtwarza sekret bajt po bajcie (praktyczne przy podpisach webhooków).
   Poprawka: porównanie o stałym czasie (`hmac.compare_digest`,
   `crypto.timingSafeEqual`); hasła wyłącznie przez weryfikację skrótu
   (bcrypt/argon2).

10. **Słaba losowość (CWE-338).** Sygnatura: `random.random`, `Math.random`,
    `rand()`, `java.util.Random` przy tokenach resetu hasła, identyfikatorach
    sesji, kluczach. Scenariusz: generator Mersenne Twister jest odtwarzalny
    z próbki wyjść — napastnik przewiduje tokeny resetu i przejmuje konta.
    Poprawka: generator kryptograficzny (`secrets`, `crypto.randomBytes`,
    `SecureRandom`, `crypto/rand`); token ≥ 128 bitów entropii.

## B. Poprawność

1. **TOCTOU (CWE-367).** Sygnatura: „sprawdź, potem działaj” na zasobie
   współdzielonym: `if exists(path): open(path)`, `if saldo >= kwota:
   zapisz(...)`, `SELECT` i osobny `UPDATE` bez blokady. Scenariusz: dwa
   równoległe żądania wypłaty widzą saldo 100, oba przechodzą kontrolę —
   konto schodzi poniżej zera. Poprawka: operacja atomowa: `UPDATE ... SET
   saldo = saldo - ? WHERE saldo >= ?` z kontrolą liczby zmienionych wierszy;
   otwarcie pliku z obsługą wyjątku zamiast `exists`; flagi `O_EXCL`/`wx`.

2. **Strefa czasowa i czas letni.** Sygnatura: czas naiwny bez strefy
   (`datetime.now()` bez `tz`), doba jako 24×3600 s, zapis czasu lokalnego do
   bazy. Scenariusz: w noc zmiany czasu (w Polsce marzec/październik) doba ma
   23 lub 25 godzin — zadanie cykliczne wykona się dwa razy albo wcale;
   raport dobowy z serwerów w różnych strefach gubi rekordy. Poprawka:
   przechowywanie i porównania w UTC; konwersja lokalna tylko przy
   prezentacji; arytmetyka kalendarzowa biblioteką strefową (`zoneinfo`,
   `java.time`, `Temporal`).

3. **Liczby zmiennoprzecinkowe dla pieniędzy.** Sygnatura:
   `float`/`double`/`Number` w kwotach; kolumna `FLOAT`/`REAL` na kwocie.
   Scenariusz: `0.1 + 0.2 != 0.3`; suma pozycji faktury różni się o grosz od
   kwoty brutto — dokument się nie bilansuje. Poprawka: typ dziesiętny
   (`Decimal`, `BigDecimal`, `NUMERIC`) albo liczby całkowite w groszach;
   zaokrąglanie jawne, w jednym miejscu, według reguły z wymagań.

4. **Przepełnienia i konwersje (CWE-190).** Sygnatura: arytmetyka na typach
   o stałej szerokości bez kontroli zakresu, rzutowanie w dół (`long`→`int`),
   mieszanie typów ze znakiem i bez. Scenariusz: licznik bajtów przekracza
   2 147 483 647 i staje się ujemny — `if (size > limit)` przepuszcza
   gigantyczne żądanie; `-1 < (unsigned)0` daje fałsz. Poprawka: typ
   o zakresie dobranym do dziedziny (64-bitowy dla liczników); operacje
   z kontrolą przepełnienia; walidacja zakresu na granicy wejścia.

5. **Mutowalny stan współdzielony.** Sygnatura: zmienna modułowa/statyczna
   modyfikowana z obsługi żądań; słownik-cache bez blokady; konfiguracja
   zwracana referencją. Scenariusz: dwa żądania współdzielą listę — dane
   jednego użytkownika trafiają do odpowiedzi drugiego; testy przechodzą
   osobno, padają razem. Poprawka: stan argumentami lub w kontekście żądania;
   struktury tylko-do-odczytu po inicjalizacji (`frozen`, `Object.freeze`);
   współdzielenie zamierzone — jawna synchronizacja i komentarz „dlaczego”.

6. **Modyfikacja kolekcji podczas iteracji.** Sygnatura: `remove`/`del`/
   `splice` w pętli po tej samej kolekcji. Scenariusz: pominięte elementy
   (indeksy przesuwają się po usunięciu) albo wyjątek
   `ConcurrentModificationException`/`RuntimeError` — tylko przy określonym
   układzie danych. Poprawka: iteracja po kopii albo nowa kolekcja filtrem;
   usuwanie przez iterator, gdzie język to przewiduje.

7. **NULL / None / undefined.** Sygnatura: dostęp do pola wyniku funkcji
   dokumentującej zwrot pustki (`find`, `get`); brak rozróżnienia „brak
   wartości” od „zero/puste”. Scenariusz: rekord nieznaleziony → `NoneType
   has no attribute` — 500 zamiast 404; kwota `0` potraktowana jak brak
   wartości gałęzią `if (!x)`. Poprawka: obsłuż pustkę bezpośrednio przy
   wywołaniu; rozróżniaj jawnie (`x is None`, `x === undefined`, `x ?? d`
   zamiast `x || d`); typy opcjonalne w sygnaturach.

8. **Kodowania i normalizacja Unicode (CWE-176).** Sygnatura: plik bez
   jawnego kodowania; porównywanie nazw po `lower()` bez normalizacji;
   długość liczona bajtami/UTF-16 przy limicie w znakach. Scenariusz: plik
   z „ą/ś/ż” zapisany przy domyślnym cp1250 czyta się błędnie na serwerze
   UTF-8; dwa zapisy tej samej nazwy (NFC vs NFD) tworzą „duplikaty”.
   Poprawka: jawne `encoding="utf-8"`; normalizacja NFC na granicy wejścia,
   przed walidacją i porównaniami; limity długości w jednostce, w której są
   egzekwowane.

## C. Współbieżność

1. **Wyścig zapis–zapis (utracona aktualizacja).** Sygnatura:
   odczyt–modyfikacja–zapis bez atomowości: `UPDATE ... SET x = ?` z wartością
   z wcześniejszego `SELECT`; zapis całego dokumentu nadpisujący pola
   zmienione równolegle. Scenariusz: dwa procesy czytają licznik 41, oba
   zapisują 42 — zdarzenie znika. Poprawka: aktualizacja względna (`SET x =
   x + 1`), operacje atomowe, blokada optymistyczna (kolumna wersji + `WHERE
   version = ?` z kontrolą liczby wierszy) albo `SELECT ... FOR UPDATE`.

2. **Brak transakcji wokół sekwencji zapisów.** Sygnatura: kilka
   `INSERT`/`UPDATE` jednej operacji biznesowej bez wspólnej transakcji;
   zapis przeplatany wywołaniem zewnętrznym (poczta, płatność). Scenariusz:
   zapis zamówienia się udał, zdjęcie stanu magazynu padło — system sprzedaje
   towar, którego nie ma. Poprawka: jedna transakcja na sekwencję zapisów
   w jednej bazie; skutki zewnętrzne po zatwierdzeniu, z tabelą zdarzeń
   wychodzących (outbox) lub ponowieniami idempotentnymi.

3. **Zakleszczenie przez kolejność blokad.** Sygnatura: dwie blokady
   pobierane w różnej kolejności w różnych ścieżkach; blokady wierszy w pętli
   w kolejności z wejścia; wywołanie cudzego kodu pod trzymaną blokadą.
   Scenariusz: wątek 1 trzyma A i czeka na B, wątek 2 odwrotnie — stoją
   wiecznie; przelewy A→B i B→A padają z komunikatem zakleszczenia. Poprawka:
   globalna ustalona kolejność blokad (rosnąco po identyfikatorze);
   sortowanie rekordów przed blokowaniem; żadnych wywołań zewnętrznych pod
   blokadą.

4. **Async: brak `await`.** Sygnatura: wywołanie funkcji `async` bez
   `await`/`then`/`.catch`; `forEach(async ...)`. Scenariusz: odpowiedź wraca
   przed końcem zapisu — przy błędzie klient dostał już „OK”, wyjątek ginie;
   testy przechodzą, bo asercja biegnie przed skutkiem. Poprawka: `await`
   każdego wywołania, którego skutek lub błąd ma znaczenie; równoległość
   jawnie (`Promise.all`, `asyncio.gather`); linter `no-floating-promises`.

5. **Blokowanie pętli zdarzeń.** Sygnatura: synchroniczne we/wy w kodzie
   async: `requests.get`, `readFileSync`, `time.sleep`, ciężkie obliczenie
   CPU w funkcji `async`. Scenariusz: jedno wolne żądanie (API odpowiada
   10 s) zatrzymuje wszystkie równoległe żądania procesu — usługa wisi, choć
   CPU bezczynne. Poprawka: odpowiedniki asynchroniczne (klient async,
   `fs.promises`); operacje blokujące do puli wątków (`run_in_executor`,
   `worker_threads`); limit czasu na każde wywołanie zewnętrzne.

## D. Wydajność

1. **Zapytania N+1.** Sygnatura: zapytanie do bazy lub wywołanie API w pętli
   po wynikach innego zapytania; w ORM dostęp do relacji leniwej w pętli
   (`for order in orders: order.customer.name`). Scenariusz: lista 200
   zamówień wykonuje 201 zapytań; przy opóźnieniu 2 ms strona ładuje się pół
   sekundy samą komunikacją — w środowisku testowym niezauważalne. Poprawka:
   jedno zapytanie ze złączeniem albo dwa z `WHERE id IN (...)`; w ORM jawne
   ładowanie (`select_related`, `Include`, `joinedload`); w GraphQL
   DataLoader; w testach asercja na liczbę zapytań.

2. **Brak indeksu pod filtr lub złączenie.** Sygnatura: nowe zapytanie
   z `WHERE`/`JOIN`/`ORDER BY` po kolumnie bez indeksu w migracjach; klucz
   obcy bez indeksu; indeks złożony w kolejności niezgodnej z zapytaniem.
   Scenariusz: pełny skan — przy 10 tys. wierszy niewidoczny, przy 10 mln
   zapytanie trwa sekundy i kładzie usługę w szczycie. Poprawka: indeks
   pokrywający warunki (kolumny równościowe przed zakresowymi), w tej samej
   zmianie co zapytanie; weryfikacja `EXPLAIN` na produkcyjnej skali;
   w PostgreSQL `CONCURRENTLY` na dużych tabelach.

3. **Pobieranie nadmiarowe.** Sygnatura: `SELECT *` przy dwóch używanych
   kolumnach; `len(query.all())` zamiast `count()`; wczytywanie całego pliku
   do pamięci dla przetworzenia wierszami. Scenariusz: tabela z kolumną
   blob — każde zapytanie ciągnie megabajty nieużywanych danych; „wczytaj
   całość” na pliku 2 GB zabija proces. Poprawka: kolumny wskazane jawnie na
   gorącej ścieżce; `COUNT`/`EXISTS` po stronie bazy; przetwarzanie
   strumieniowe; `LIMIT 1` dla jednego rekordu.

4. **Brak paginacji.** Sygnatura: punkt końcowy listy z `findAll()` bez
   `LIMIT`; eksport ładujący cały wynik do pamięci; `OFFSET` na głębokich
   stronach. Scenariusz: tabela urosła do 500 tys. wierszy — odpowiedź ma
   200 MB, klient mobilny pada; `OFFSET 900000` odczytuje i odrzuca 900 tys.
   wierszy na każdej stronie. Poprawka: obowiązkowy `LIMIT` z domyślnym
   i maksymalnym rozmiarem strony; paginacja kursorem (`WHERE id > ostatni
   ORDER BY id LIMIT n`); eksporty strumieniowo lub w tle.

5. **Praca w pętli zamiast zbiorczo.** Sygnatura: `INSERT`/`UPDATE`
   pojedynczych wierszy w pętli; commit po każdym wierszu; wywołanie HTTP na
   element, gdy API ma wariant wsadowy. Scenariusz: import 50 tys. wierszy po
   jednym `INSERT` z commitem trwa godzinę zamiast sekund — każda iteracja
   płaci pełny koszt komunikacji i fsync. Poprawka: operacje wsadowe
   (`executemany`, `bulk_create`, multiwierszowy `INSERT`, `COPY`),
   transakcja na partię rozsądnego rozmiaru, zasoby otwierane raz przed
   pętlą.

## E. Utrzymywalność według standardów Danaco

1. **Naruszenia kontroli końcowej z `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md`.**
   Sygnatura: historia zmian w komentarzach; wymyślone kody i etykiety własne zamiast terminologii
   zawodowej; pliki `_v2`, `_final`, `_kopia`; kod martwy i wykomentowane bloki; język
   nieprofesjonalny w treściach trwałych. Scenariusz: czytelnik nie odróżnia wersji obowiązującej od
   porzuconej; wykomentowany blok wraca w scaleniu i przywraca usterkę. Poprawka: historię zostawiaj
   systemowi kontroli wersji — usuń komentarze historyczne i kod martwy; terminologia wyłącznie
   standardowa; jeden plik obowiązujący.

2. **Duplikacja logiki istniejącej w projekcie.** Sygnatura: nowa funkcja
   walidacji/formatowania/przeliczeń, gdy projekt ma odpowiednik (szukaj po
   słowach dziedziny: NIP, VAT, zaokrągl); skopiowany blok z drobną zmianą;
   stała zdefiniowana ponownie z inną wartością. Scenariusz: poprawka trafia
   do jednej z dwóch kopii — druga liczy inaczej. Poprawka: użyj istniejącego
   odpowiednika; gdy nie pasuje — rozszerz zamiast kopiować; stałe
   dziedzinowe w jednym module.

3. **Nazwy mylące i kontrakty niedotrzymane.** Sygnatura: `get_...` z efektem
   ubocznym (zapis, wysyłka); `is_...` zwracające coś innego niż
   prawda/fałsz; parametr nieużywany; komentarz sprzeczny z kodem obok.
   Scenariusz: wywołujący ufa nazwie — woła `get_report` w pętli i wysyła sto
   wiadomości. Poprawka: nazwa opisuje pełny skutek; rozdziel odczyt od
   efektu ubocznego; usuń parametry martwe; komentuj „dlaczego”, nie „co”.

4. **Obsługa błędów zjadająca sygnał.** Sygnatura: puste `catch`/`except:
   pass`; ogólny wyjątek i zwrot wartości domyślnej bez logu; ponowne
   rzucenie gubiące ślad stosu (`raise e` zamiast `raise`). Scenariusz: zapis
   pada od tygodnia, system „działa” — dane cicho znikają; awaria bez śladu
   w dziennikach wydłuża diagnozę z minut do dni. Poprawka: przechwytuj
   wyjątki konkretne; przechwycony a nieobsłużony — loguj z treścią, śladem
   stosu i kontekstem; zachowuj przyczynę (`raise ... from e`, opcja
   `cause`); błędy krytyczne propaguj.
