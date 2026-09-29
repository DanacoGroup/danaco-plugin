# PostgreSQL — karta

Karta obejmuje pracę z PostgreSQL w wersji 14 i nowszych: schemat, migracje,
parametryzację, transakcje. Wydania 18 i 19, pgvector oraz wyszukiwanie znaczeniowe
opisuje `references/engineering-core/04-bazy-i-rag/references/postgres.md` — tam sięgaj
po stan wersji, tutaj po podstawy pracy z bazą.

Przeczytaj kartę w całości przed pracą z bazą PostgreSQL (dotyczy PostgreSQL 14+). Stosuj wskazania
bezwzględnie; każde odstępstwo uzasadnij w opisie zmiany.

## Konwencje schematu

- Nazywaj tabele rzeczownikami w liczbie mnogiej, w snake_case: `orders`, `invoice_items`.
- Nazywaj kolumny w liczbie pojedynczej: `customer_id`, `created_at`, `total_amount`.
- Nie stosuj wielkich liter ani cudzysłowów w identyfikatorach — PostgreSQL składa niecytowane
  identyfikatory do małych liter, a identyfikator raz zacytowany wymusza cytowanie na zawsze.
- Nazywaj obiekty pomocnicze według stałego wzorca:
  - indeksy: `idx_<tabela>_<kolumny>`,
  - ograniczenia unikalności: `uq_<tabela>_<kolumny>`,
  - klucze obce: `fk_<tabela>_<tabela_docelowa>`,
  - ograniczenia CHECK: `ck_<tabela>_<reguła>`.
- Typy zalecane:
  - `text` zamiast `varchar(n)` — brak różnicy wydajności; limit egzekwuj ograniczeniem CHECK,
  - `timestamptz` zamiast `timestamp` — poprawne przechowywanie chwil czasu,
  - `numeric` dla kwot pieniężnych, `bigint` dla identyfikatorów, `boolean` dla flag,
  - `jsonb` zamiast `json`, `uuid` dla identyfikatorów eksponowanych publicznie.
- Typy odradzane: `money` (problemy z lokalizacją), `char(n)` (dopełnianie spacjami),
  `timestamp` bez strefy, `serial` (patrz sekcja błędów), `float` dla wartości finansowych.
- Klucz główny definiuj następująco:

```sql
CREATE TABLE orders (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id  bigint NOT NULL REFERENCES customers (id) ON DELETE RESTRICT,
    status       text   NOT NULL DEFAULT 'pending',
    created_at   timestamptz NOT NULL DEFAULT now()
);
```

- Deklaruj `NOT NULL` domyślnie na każdej kolumnie; dopuszczenie NULL musi być świadomą decyzją.
- Definiuj klucze obce zawsze z jawną regułą `ON DELETE` (`RESTRICT` domyślnie;
  `CASCADE` wyłącznie dla danych ściśle podrzędnych).

## Migracje i zmiany schematu

- Prowadź zmiany schematu wyłącznie przez wersjonowane migracje (Alembic, Flyway, Liquibase,
  sqitch lub mechanizm frameworku). Nie wykonuj ręcznego DDL na środowiskach współdzielonych.
- Zmiany bezpieczne (krótka blokada, bez przepisywania tabeli):
  - dodanie kolumny dopuszczającej NULL,
  - dodanie kolumny z domyślną wartością stałą (PostgreSQL 11+ nie przepisuje tabeli),
  - `CREATE INDEX CONCURRENTLY`,
  - poszerzenie `varchar(n)`.
- Zmiany blokujące lub kosztowne:
  - zmiana typu kolumny wymagająca przepisania tabeli,
  - dodanie kolumny `NOT NULL` bez wartości domyślnej do tabeli z danymi,
  - `CREATE INDEX` bez `CONCURRENTLY` na dużej tabeli,
  - dodanie klucza obcego lub CHECK bez klauzuli `NOT VALID`.
- Wprowadzaj kosztowne ograniczenia dwuetapowo — walidacja nie blokuje wtedy zapisów:

```sql
ALTER TABLE orders ADD CONSTRAINT fk_orders_customers
    FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customers;
```

- Ustaw `SET lock_timeout = '5s'` przed każdą migracją DDL, aby oczekiwanie na blokadę
  nie zatrzymało ruchu produkcyjnego; po niepowodzeniu ponów migrację poza szczytem.
- Pamiętaj: `CREATE INDEX CONCURRENTLY` nie działa wewnątrz transakcji — wydziel je z migracji
  transakcyjnej.
- Dla każdej migracji przygotuj ścieżkę wycofania: skrypt odwrotny (down), a dla zmian
  nieodwracalnych (usunięcie kolumny, tabeli) — procedurę dwufazową: najpierw zaprzestanie
  użycia w kodzie, usunięcie obiektu w kolejnym wydaniu, poprzedzone kopią zapasową.

## Zapytania i indeksy

- Parametryzuj każde zapytanie (`$1`, `$2` lub mechanizm sterownika). Nigdy nie składaj SQL
  przez konkatenację ani interpolację łańcuchów — dotyczy również wartości „zaufanych”.
- Przed optymalizacją odczytaj plan wykonania: `EXPLAIN (ANALYZE, BUFFERS) <zapytanie>`.
  Porównuj rzeczywiste liczby wierszy z szacowanymi; duża rozbieżność wskazuje na
  nieaktualne statystyki — wykonaj `ANALYZE` na tabeli.
- Zakładaj indeks, gdy kolumna występuje w `WHERE`, `JOIN` lub `ORDER BY` częstych zapytań na
  dużych tabelach. Nie indeksuj kolumn o znikomej selektywności ani tabel o kilkuset wierszach.
- W indeksach złożonych umieszczaj najpierw kolumny porównywane przez równość, potem kolumny
  zakresowe lub sortowane. Indeks `(a, b)` obsługuje warunki na `a` oraz `a, b`, lecz nie na samo
  `b`.
- Stosuj indeksy częściowe dla aktywnych podzbiorów danych:

```sql
CREATE INDEX idx_orders_pending ON orders (created_at) WHERE status = 'pending';
```

- Stosuj indeksy funkcyjne dla wyszukiwań po wyrażeniu, np. `ON users (lower(email))`,
  i używaj identycznego wyrażenia w zapytaniu.
- Dla kolumn `jsonb` przeszukiwanych operatorami `@>` i `?` stosuj indeks GIN.
- Pobieraj wyłącznie potrzebne kolumny; unikaj `SELECT *` w kodzie aplikacyjnym.
- Przy stronicowaniu dużych zbiorów stosuj paginację kluczową
  (`WHERE id > $1 ORDER BY id LIMIT n`) zamiast rosnącego `OFFSET`.

## Transakcje i współbieżność

- Domyślny poziom izolacji to `READ COMMITTED`: każde polecenie widzi dane zatwierdzone przed
  jego rozpoczęciem. Nie zakładaj powtarzalności odczytów w ramach transakcji na tym poziomie.
- Stosuj `REPEATABLE READ` dla spójnych odczytów wielokrokowych oraz `SERIALIZABLE` dla logiki
  wymagającej pełnej szeregowalności. Na obu poziomach obsłuż błąd serializacji
  (`SQLSTATE 40001`) przez ponowienie całej transakcji — to zachowanie oczekiwane, nie awaria.
- Utrzymuj transakcje krótkie. Nie wykonuj wywołań sieciowych ani operacji na plikach
  w otwartej transakcji — długie transakcje wstrzymują odśmiecanie wersji i eskalują blokady.
- Dla wzorca „odczytaj, zmodyfikuj, zapisz” stosuj `SELECT ... FOR UPDATE` (blokada
  pesymistyczna) albo kolumnę wersji i warunek w `UPDATE` (blokada optymistyczna).
- Pobieraj blokady wielu wierszy zawsze w tym samym porządku (np. `ORDER BY id`),
  aby wykluczyć zakleszczenia.
- Do wstawień idempotentnych stosuj `INSERT ... ON CONFLICT (col) DO UPDATE / DO NOTHING`
  zamiast pary SELECT + INSERT, która zawiera warunek wyścigu.
- Diagnozuj oczekiwania na blokady przez `pg_locks` złączone z `pg_stat_activity`.

## Eksploatacja

- Kopie logiczne wykonuj przez `pg_dump -Fc` (format custom umożliwia selektywne odtwarzanie
  przez `pg_restore`); kopię ról i całego klastra przez `pg_dumpall`.
- Kopie fizyczne oraz podstawę odtwarzania punktowego (PITR z archiwizacją WAL) zapewnia
  `pg_basebackup`. Nie kopiuj katalogu danych działającego serwera narzędziami plikowymi — taka
  kopia jest niespójna.
- Regularnie testuj odtwarzanie kopii na osobnym środowisku; kopia nietestowana nie jest kopią.
- Autovacuum musi pozostać włączony. Ręczny `VACUUM` stosuj po masowych usunięciach;
  `ANALYZE` po masowych zmianach danych, aby odświeżyć statystyki planera.
- `VACUUM FULL` przepisuje tabelę pod blokadą wyłączną — stosuj wyłącznie świadomie,
  w oknie serwisowym.
- Monitoruj najbardziej kosztowne zapytania przez rozszerzenie `pg_stat_statements` (wymaga wpisu w
  `shared_preload_libraries`); analizuj `total_exec_time`, `calls`, `mean_exec_time`.
- Obserwuj martwe krotki (`n_dead_tup` w `pg_stat_user_tables`), rozrost indeksów,
  długotrwałe transakcje w `pg_stat_activity` oraz saturację puli połączeń;
  przy wielu krótkotrwałych połączeniach stosuj pooler (np. PgBouncer).

## Typowe błędy modeli LLM przy pracy z tym systemem

1. Składnia MySQL w PostgreSQL: grawisy wokół identyfikatorów, `AUTO_INCREMENT`,
   `ENGINE=InnoDB`, `ON DUPLICATE KEY UPDATE`, `IFNULL()`. Poprawnie: identyfikatory bez
   cudzysłowów, `GENERATED ALWAYS AS IDENTITY`, `ON CONFLICT ... DO UPDATE`, `COALESCE()`.
2. `VARCHAR(255)` bez uzasadnienia: liczba 255 nie daje w PostgreSQL żadnej korzyści
   wydajnościowej ani składowania. Stosuj `text`; rzeczywisty limit biznesowy egzekwuj
   przez `CHECK (char_length(col) <= n)`.
3. Brak indeksu na kolumnie klucza obcego: PostgreSQL nie tworzy go automatycznie.
   Skutek: skany sekwencyjne przy złączeniach i pełne skany tabeli podrzędnej przy `DELETE`
   z tabeli nadrzędnej. Twórz indeks na każdym kluczu obcym, chyba że pomiar wykaże zbędność.
4. `SERIAL` zamiast `GENERATED ALWAYS AS IDENTITY`: `serial` to przestarzały skrót tworzący
   luźno powiązaną sekwencję o odrębnych uprawnieniach; w PostgreSQL 10+ standardem jest IDENTITY.
5. `timestamp` zamiast `timestamptz`: chwile zdarzeń zapisuj w `timestamptz`;
   typ bez strefy rezerwuj dla czasu lokalnego z natury (np. godziny otwarcia).
6. SQL budowany f-stringami lub szablonami: ryzyko wstrzyknięcia SQL i brak ponownego użycia
   planu. Zawsze stosuj parametry sterownika.
7. `LIKE '%fraza%'` z oczekiwaniem użycia indeksu: wzorzec z wiodącym `%` nie korzysta
   z indeksu B-tree. Stosuj indeks GIN z rozszerzeniem `pg_trgm` albo wyszukiwanie
   pełnotekstowe (`tsvector`).
8. Zapytania w pętli aplikacji (problem N+1) zamiast jednego złączenia lub
   `WHERE id = ANY($1)`; wstawianie wierszy pojedynczo zamiast `INSERT` wielowierszowego lub `COPY`.
9. `CREATE INDEX` bez `CONCURRENTLY` w migracji produkcyjnej: blokada zapisów do tabeli
   na cały czas budowy indeksu.
10. Ignorowanie błędów serializacji i zakleszczeń: kod musi ponawiać transakcje zakończone
    `SQLSTATE 40001` oraz `40P01`; traktowanie ich jako awarii krytycznej jest błędem projektowym.
