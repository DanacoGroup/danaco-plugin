# Strojenie wydajności — karta

Przeczytaj kartę w całości przed diagnozą wydajnościową bazy PostgreSQL lub SQLite.
Karta jest wspólna dla obu systemów; różnice oznaczono jawnie. Zasada
nadrzędna: żadnej zmiany bez pomiaru „przed” i „po” — na danych
o produkcyjnej wielkości.

## Czytanie planów wykonania

### PostgreSQL — EXPLAIN (ANALYZE, BUFFERS)

- Diagnozę zaczynaj od pełnego planu: `EXPLAIN (ANALYZE, BUFFERS) <zapytanie>`.
  Sam `EXPLAIN` pokazuje szacunki; `ANALYZE` wykonuje zapytanie i podaje
  rzeczywistość. Zapytania modyfikujące analizuj w transakcji wycofywanej:
  `BEGIN; EXPLAIN ANALYZE UPDATE ...; ROLLBACK;`.
- Czytaj plan od liści do korzenia — dane płyną z dołu do góry.
  Węzły do rozpoznawania:
  - `Seq Scan` — pełny skan; poprawny na małych tabelach i przy niskiej
    selektywności warunku, podejrzany, gdy `Rows Removed by Filter` jest
    znacznie większe od liczby wierszy zwróconych,
  - `Index Scan` — odczyt indeksu z sięganiem do tabeli po każdą krotkę,
  - `Index Only Scan` — odczyt wyłącznie z indeksu; wysokie `Heap Fetches`
    oznacza nieaktualną mapę widoczności — wykonaj `VACUUM` na tabeli,
  - `Bitmap Heap Scan` + `Bitmap Index Scan` — wariant dla warunków o średniej
    selektywności lub sumy kilku indeksów,
  - `Nested Loop` — dobry przy małej liczbie wierszy po stronie zewnętrznej
    i indeksie po wewnętrznej; katastrofalny, gdy planer nie doszacował wierszy,
  - `Hash Join` / `Merge Join` — właściwe dla dużych zbiorów; `Hash Join`
    przelewający się na dysk (`Batches` > 1) sygnalizuje za niskie `work_mem`,
  - `Sort` z `Sort Method: external merge Disk:` — sortowanie na dysku; rozważ
    indeks zgodny z porządkiem `ORDER BY` albo wyższe `work_mem` dla sesji.
- Porównuj `rows=` szacowane z `rows=` rzeczywistymi w każdym węźle. Rozjazd o rząd
  wielkości lub więcej to wada statystyk, nie zapytania. Kolejność napraw:
  1. `ANALYZE <tabela>;` — odświeżenie statystyk,
  2. dla kolumn o skośnym rozkładzie podnieś próbkę:
     `ALTER TABLE t ALTER COLUMN c SET STATISTICS 1000;` po czym `ANALYZE t;`,
  3. gdy rozjazd dotyczy warunku na kilku skorelowanych kolumnach (planer mnoży
     selektywności jak niezależne), załóż statystyki rozszerzone:

```sql
CREATE STATISTICS st_orders_region_status (dependencies, ndistinct)
    ON region, status FROM orders;
ANALYZE orders;
```

- Sekcja `Buffers:` mówi, skąd pochodzą dane: `shared hit` — pamięć podręczna,
  `read` — dysk. Zapytanie „raz szybkie, raz wolne” przy identycznym planie to
  zwykle zimna pamięć podręczna, nie zły plan. Duża liczba buforów przy małym
  wyniku wskazuje na wzdęcie tabeli lub indeksu (sekcja utrzymania).

### SQLite — EXPLAIN QUERY PLAN

- Stosuj `EXPLAIN QUERY PLAN <zapytanie>` (nie surowy `EXPLAIN`, który wypisuje
  kod bajtowy i nie służy do strojenia).
- Interpretacja wpisów:
  - `SCAN <tabela>` — pełny skan; akceptowalny dla małych tabel i zapytań rzadkich,
  - `SEARCH <tabela> USING INDEX <nazwa> (kolumna=?)` — dostęp przez indeks; stan docelowy,
  - `SEARCH ... USING COVERING INDEX` — zapytanie obsłużone w całości z indeksu,
    bez sięgania do tabeli; najtańszy wariant — osiągaj go, dopisując do indeksu
    kolumny zwracane przez `SELECT`,
  - `USING INTEGER PRIMARY KEY` — wyszukiwanie po `rowid`, najszybszy dostęp punktowy,
  - `USE TEMP B-TREE FOR ORDER BY` / `FOR GROUP BY` — sortowanie doraźne; usuwaj
    indeksem zgodnym z porządkiem, gdy zapytanie jest częste.
- Statystyki planera SQLite pochodzą z `ANALYZE`; bez nich planer zgaduje.
  Po masowych zmianach danych wykonaj `ANALYZE`, a przy zamykaniu długo żyjących
  połączeń — `PRAGMA optimize` (SQLite 3.32+).

## Projektowanie indeksów

- Kolejność kolumn w indeksie złożonym: najpierw kolumny porównywane przez
  równość, potem jedna kolumna zakresowa lub sortowana. Dla
  `WHERE customer_id = ? AND created_at >= ? ORDER BY created_at` właściwy jest
  indeks `(customer_id, created_at)`; odwrotna kolejność `(created_at, customer_id)`
  zmusza do skanu całego zakresu dat. Kolumny za pierwszą kolumną zakresową
  nie zawężają przeszukiwania — służą co najwyżej pokryciu.
- Indeks częściowy zakładaj, gdy zapytania dotyczą wąskiego, stałego podzbioru:
  `CREATE INDEX idx_orders_pending ON orders (created_at) WHERE status = 'pending';`
  (składnia identyczna w obu systemach). Warunek zapytania musi implikować warunek
  indeksu, inaczej planer go nie użyje.
- Indeks pokrywający eliminuje sięganie do tabeli. W PostgreSQL 11+ stosuj klauzulę
  `INCLUDE` dla kolumn wyłącznie zwracanych:
  `CREATE INDEX idx_orders_customer ON orders (customer_id) INCLUDE (status, total_amount);`
  — kolumny z `INCLUDE` nie wchodzą do klucza, więc nie powiększają części
  przeszukiwanej. W SQLite odpowiednika `INCLUDE` brak — dopisz kolumny na końcu
  klucza indeksu.
- Indeks funkcyjny zakładaj pod wyrażenie używane w `WHERE`
  (np. `ON users (lower(email))`); wyrażenie w zapytaniu musi być identyczne
  znak w znak. W PostgreSQL wymaga funkcji `IMMUTABLE`.
- Każdy indeks kosztuje przy zapisie: `INSERT`, `DELETE` i `UPDATE` kolumn
  indeksowanych utrzymują wszystkie indeksy tabeli, a w PostgreSQL nadmiar
  indeksów wyklucza optymalizację HOT przy `UPDATE`. Tabela intensywnie
  zapisywana z ośmioma indeksami to sygnał do przeglądu, nie do dokładania dziewiątego.
- Wykrywaj indeksy nieużywane (PostgreSQL):

```sql
SELECT schemaname, relname, indexrelname, idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

  Przed usunięciem sprawdź, od kiedy zbierane są statystyki
  (`pg_stat_get_db_stat_reset_time`), wyklucz indeksy unikalne i wspierające
  ograniczenia, uwzględnij zapytania rzadkie (raporty miesięczne); usuwaj przez
  `DROP INDEX CONCURRENTLY`. W SQLite licznika użyć brak — weryfikuj przydatność
  przez `EXPLAIN QUERY PLAN` kluczowych zapytań przed i po usunięciu.
- Duplikaty indeksów (indeks `(a)` obok `(a, b)`) usuwaj — przedrostkowy jest
  zbędny, chyba że jest unikalny albo znacząco mniejszy i gorący.

## Przepisywanie zapytań

- `EXISTS` zamiast `IN` przy podzapytaniach skorelowanych i zbiorach o nieznanej
  wielkości: `WHERE EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id)`
  kończy sprawdzanie po pierwszym trafieniu. Nigdy `NOT IN` z podzapytaniem
  mogącym zwrócić NULL — wynik jest wtedy pusty (trójwartościowa
  logika SQL); stosuj `NOT EXISTS`.
- Nie owijaj kolumny funkcją w `WHERE`: warunek `date(created_at) = '2026-08-16'`
  (SQLite) ani `created_at::date = ...` (PostgreSQL) nie użyje indeksu na
  `created_at`. Przepisuj na zakres półotwarty:
  `created_at >= '2026-08-16' AND created_at < '2026-08-17'`.
  Alternatywa: indeks funkcyjny pod dokładnie to wyrażenie.
- Paginacja kluczowa (keyset) zamiast `OFFSET` na dużych zbiorach: `OFFSET 100000`
  odczytuje i odrzuca sto tysięcy wierszy przy każdej stronie. Poprawnie:
  `WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 50`
  z indeksem `(created_at, id)` — koszt strony stały; porównanie krotkowe działa
  w PostgreSQL i SQLite 3.15+, a `id` w kluczu rozstrzyga remisy.
- Funkcje okna zamiast samozłączeń: „najnowszy wiersz na grupę” pisz przez
  `ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC)`
  i filtr `= 1` w zapytaniu zewnętrznym, zamiast złączenia tabeli z jej własnym
  agregatem `MAX`. W PostgreSQL rozważ też `DISTINCT ON (customer_id) ... ORDER BY
  customer_id, created_at DESC` — najszybsze przy zgodnym indeksie.
- CTE i materializacja: w PostgreSQL 12+ `WITH` jest domyślnie wciągane do
  zapytania głównego (predykaty się propagują); `WITH x AS MATERIALIZED (...)`
  wymusza zapis pośredni — stosuj przy CTE kosztownym i użytym wielokrotnie,
  a `NOT MATERIALIZED` znosi barierę, którą PostgreSQL stawia dla CTE
  wielokrotnych. W SQLite planer decyduje sam; słowa `MATERIALIZED` /
  `NOT MATERIALIZED` przyjmuje od wersji 3.35.
- Eliminuj N+1: zapytanie w pętli aplikacji zamieniaj na jedno złączenie albo
  `WHERE id = ANY($1)` (PostgreSQL) / `WHERE id IN (lista parametrów)` (SQLite).
- `count(*)` na wielkiej tabeli PostgreSQL jest kosztowny z natury (MVCC wymaga
  sprawdzenia widoczności); dla pasków postępu wystarcza szacunek
  z `pg_class.reltuples`.

## Blokady i współbieżność

### PostgreSQL

- DML pobiera na tabeli blokadę `ROW EXCLUSIVE` — zapisy różnych wierszy nie
  kolidują. Groźne są blokady DDL: `ALTER TABLE` bierze `ACCESS EXCLUSIVE`,
  a czekając na nią, blokuje wszystkie nowsze zapytania, także odczyty.
  Stąd obowiązkowy `lock_timeout` przy migracjach (karta postgresql.md).
- Wykrywaj łańcuchy oczekiwania:

```sql
SELECT blocked.pid AS blocked_pid,
       blocked.query AS blocked_query,
       blocking.pid AS blocking_pid,
       blocking.query AS blocking_query,
       now() - blocking.xact_start AS blocking_xact_age
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY (pg_blocking_pids(blocked.pid));
```

  Interesuj się źródłem łańcucha — często to sesja `idle in transaction`.
  Ustaw zabezpieczenie `idle_in_transaction_session_timeout` na wartość
  rzędu minut.
- Kolejki zadań w tabeli realizuj przez `FOR UPDATE SKIP LOCKED` — konkurujący
  pracownicy pomijają wiersze zajęte zamiast się na nich ustawiać:

```sql
WITH job AS (
    SELECT id FROM jobs
    WHERE status = 'queued'
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE jobs SET status = 'running'
FROM job WHERE jobs.id = job.id
RETURNING jobs.id;
```

  Wariant `FOR UPDATE NOWAIT` zgłasza błąd zamiast czekać — do operacji, które
  wolisz odrzucić niż wstrzymać.
- Zakleszczenia (`SQLSTATE 40P01`) eliminuj stałym porządkiem dostępu: wiersze
  blokuj posortowane (`ORDER BY id` przed `FOR UPDATE`), tabele modyfikuj
  w jednakowej kolejności we wszystkich ścieżkach, a `UPDATE` wielu wierszy
  jednym poleceniem zamiast pętli. Wystąpienia znajdziesz w dzienniku serwera
  (`deadlock detected` z oboma zapytaniami); kod ma ponawiać transakcję.

### SQLite

- WAL rozdziela czytelników od zapisującego: zapis dopisuje strony do pliku
  `-wal`, czytelnicy widzą migawkę z chwili rozpoczęcia odczytu. Punkt kontrolny
  przenosi strony do pliku głównego automatycznie (domyślnie co 1000 stron),
  lecz długi odczyt (otwarta transakcja, kursor nieodczytany do końca) wstrzymuje
  punkty kontrolne i rozdyma plik `-wal` — stale rosnący `-wal` to zawsze objaw
  przetrzymywanej transakcji.
- Zapisujący jest dokładnie jeden — to fakt architektury, nie parametr do
  podniesienia. Projektuj aplikację wokół tego: jedno połączenie zapisujące
  (lub kolejka zapisów w aplikacji), transakcje zapisu otwierane przez
  `BEGIN IMMEDIATE` i zamykane jak najszybciej, `busy_timeout` na każdym
  połączeniu. Pula wielu połączeń ma sens dla odczytów, nie dla zapisów.
- Gdy pomiary wykażą trwałą rywalizację o zapis mimo krótkich transakcji —
  właściwą poprawką jest migracja do PostgreSQL, nie dalsze strojenie SQLite.

## Utrzymanie wydajności

- Autovacuum (PostgreSQL) domyślnie budzi się przy ~20% martwych krotek —
  przy stu milionach wierszy to dwadzieścia milionów martwych. Dla gorących
  tabel schodź na progi bezwzględne per tabela:

```sql
ALTER TABLE orders SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.02
);
```

  Nigdy nie wyłączaj autovacuum; jeśli „przeszkadza”, jest zbyt opóźniony i przez to
  kosztowny — częstsze przebiegi są lżejsze. Obserwuj `n_dead_tup`
  i `last_autovacuum` w `pg_stat_user_tables`.
- Wzdęcie (bloat): tabele i indeksy rosną mimo stałej liczby wierszy, gdy
  odśmiecanie nie nadąża za zapisami albo długie transakcje wstrzymują usuwanie
  starych wersji. Objawy: rosnący `pg_total_relation_size()` bez wzrostu danych,
  wysokie `Buffers` w planach prostych zapytań; skalę szacuje rozszerzenie
  `pgstattuple`. Naprawa: indeksy — `REINDEX CONCURRENTLY` (PostgreSQL 12+);
  tabele — `pg_repack` bez długiej blokady albo `VACUUM FULL` wyłącznie w oknie
  serwisowym. Następnie usuń przyczynę: dostrój autovacuum, wyeliminuj długie
  transakcje.
- `pg_stat_statements` traktuj jako stały monitoring, nie narzędzie doraźne
  (wpis w `shared_preload_libraries`, po czym `CREATE EXTENSION pg_stat_statements`).
  Przegląd zaczynaj od czasu łącznego, nie średniego — zapytanie 5 ms wykonywane
  milion razy dziennie kosztuje więcej niż raport trwający 30 s:

```sql
SELECT round(total_exec_time) AS total_ms, calls,
       round(mean_exec_time, 2) AS mean_ms,
       rows, left(query, 120) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

  Dodatkowo sortuj po `shared_blks_read` (nacisk na dysk) i `calls` (kandydaci
  do usunięcia N+1). Po wdrożonej optymalizacji wykonaj
  `SELECT pg_stat_statements_reset();`.
- SQLite nie ma odpowiednika `pg_stat_statements` — pomiar czasu zapytań
  realizuj w aplikacji (rejestruj zapytania wolniejsze niż próg, z parametrami).
  Utrzymaniowo wystarczają: `ANALYZE` po masowych zmianach,
  `PRAGMA optimize` przy zamykaniu połączeń, kontrola rozmiaru `-wal`
  oraz `VACUUM` po masowych usunięciach.
