# Postgres jako baza domyślna — karta

Podstawy pracy z bazą, migracje i parametryzację opisuje
`references/bazy-danych/postgresql.md`. Ta karta obejmuje to, co robi silnik: typy,
indeksy, plan zapytania, blokady, wyszukiwanie pełnotekstowe po polsku,
partycjonowanie i stan wydań.

Stan: PostgreSQL **18** stabilny (18.0 wydane 25.09.2025, wydanie poprawkowe 18.6).
Wersja **19 jest wciąż w becie** (Beta 3 z 13.08.2026) — nie wolno jej przyjmować za
wydaną ani planować na niej produkcji, dopóki wydanie finalne nie ogłoszone. PG 14 traci
wsparcie **12.11.2026** — jeśli klient na nim siedzi, to jest termin, nie sugestia.
Stan sprawdzony 2026-09-03 na postgresql.org/support/versioning; przy każdym użyciu tej
karty potwierdź numer wydania u źródła, nie w karcie.

Co przyszło w 18 i realnie zmienia decyzje:
- **Asynchroniczne I/O** (`io_method` = `worker` domyślnie na Linuksie, `io_uring` opcjonalnie).
  Skany sekwencyjne i bitmapowe potrafią być 2–3× szybsze na dyskach sieciowych.
- **`uuidv7()`** wbudowane — koniec z `gen_random_uuid()` jako kluczem głównym (patrz niżej).
- **Skip scan dla indeksów btree** — indeks złożony `(a, b)` bywa użyteczny dla predykatu
  tylko na `b`, gdy `a` ma mało odrębnych wartości. Nie znosi to reguły o kolejności kolumn,
  ale zmniejsza liczbę potrzebnych indeksów.
- `EXPLAIN ANALYZE` pokazuje `Index Searches` — liczbę faktycznych przeszukań indeksu.

W 19 (beta): stemmery Snowball dla **polskiego** i esperanto, `FOR PORTION OF` (tabele
temporalne), SQL/PGQ (grafy właściwościowe). Stemmer polski jest dla nas najważniejszy —
patrz sekcja o FTS.

## Typy: wybieraj wąsko

Typ jest pierwszym indeksem. Zły typ kosztuje przez całe życie systemu.

| Potrzeba | Typ | Uwagi |
|---|---|---|
| Klucz główny | `bigint GENERATED ALWAYS AS IDENTITY` albo `uuid` z `uuidv7()` | `uuidv7()` jest czasowo uporządkowany, więc wstawia się na koniec indeksu; `gen_random_uuid()` (v4) rozrzuca wstawienia po całym btree i podnosi WAL |
| Tekst | `text` | `varchar(n)` nie jest szybszy; ograniczenie długości daj `CHECK`, łatwiej zmienić |
| Pieniądze | `numeric(12,2)` | nigdy `float`; `money` jest zależny od locale |
| Czas zdarzenia | `timestamptz` | `timestamp` bez strefy to błąd, który wyjdzie przy pierwszej zmianie czasu |
| Data bez czasu | `date` | |
| Okres obowiązywania | `daterange` / `tstzrange` | z `EXCLUDE USING gist` gwarantuje brak nakładania |
| Zbiór wartości | domena + `CHECK` albo tabela słownikowa | `enum` tylko gdy wartości są naprawdę stabilne — patrz niżej |
| Dane półstrukturalne | `jsonb` | nigdy `json` (nie ma indeksowania, przechowuje tekst dosłownie) |
| Lista identyfikatorów | `bigint[]` albo tabela łącząca | tablica tylko gdy nie ma potrzeby dołączeń i integralności |
| IP, sieć | `inet`, `cidr` | |
| Suma kontrolna | `bytea` | |

### enum

`ALTER TYPE ... ADD VALUE` działa (od PG 12 także wewnątrz transakcji, z ograniczeniem:
nowej wartości nie można użyć w tej samej transakcji). **Usunięcie ani zmiana kolejności
wartości nie są możliwe** — trzeba przepisać typ i wszystkie kolumny. Dlatego enum tylko
dla rzeczy jak `('draft','published','archived')`, nigdy dla „rodzajów pism procesowych”,
których w praktyce przybywa i ubywa.

### jsonb

Używaj do rzeczy naprawdę zmiennokształtnych (surowe metadane z parsera, ładunek webhooka).
Nie używaj jako sposobu na uniknięcie projektu schematu.

```sql
-- indeks GIN: domyślny operator jsonb_ops obsługuje @>, ?, ?&, ?|
CREATE INDEX idx_dok_meta ON dokumenty USING gin (metadane);

-- jsonb_path_ops: mniejszy i szybszy, ale TYLKO dla @>
CREATE INDEX idx_dok_meta_path ON dokumenty USING gin (metadane jsonb_path_ops);

-- jedno pole odpytywane często: indeks wyrażeniowy btree bije GIN
CREATE INDEX idx_dok_sygnatura ON dokumenty ((metadane->>'sygnatura'));

-- kolumna generowana, gdy pole ma być pierwszej klasy
ALTER TABLE dokumenty
  ADD COLUMN sygnatura text GENERATED ALWAYS AS (metadane->>'sygnatura') STORED;
```

Pułapki: `->` zwraca `jsonb`, `->>` zwraca `text`. Porównanie `metadane->'rok' = '2024'`
nie zadziała tak, jak się spodziewasz (po lewej `jsonb`, po prawej `text`) — trzeba
`metadane->>'rok' = '2024'` albo `metadane->'rok' = '2024'::jsonb`.
Duże wartości `jsonb` idą do TOAST i każdy odczyt to dodatkowe I/O — nie trzymaj tam
całych treści dokumentów.

### tablice

```sql
CREATE INDEX idx_tagi ON dokumenty USING gin (tagi);
SELECT * FROM dokumenty WHERE tagi @> ARRAY['pilne'];   -- używa GIN
SELECT * FROM dokumenty WHERE 'pilne' = ANY(tagi);      -- NIE używa GIN
```

Różnica między `@>` a `= ANY()` to najczęstsza przyczyna „mam indeks GIN, a i tak seq scan”.

### zakresy i wykluczenia

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE rezerwacje (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  zasob_id   bigint NOT NULL,
  okres      tstzrange NOT NULL,
  EXCLUDE USING gist (zasob_id WITH =, okres WITH &&)
);
```

To jest jedyny sposób, żeby baza sama nie dopuściła do nakładania terminów. Sprawdzenie
w aplikacji przegrywa przy dwóch równoczesnych żądaniach.

## Indeksy

| Typ | Do czego | Kiedy nie |
|---|---|---|
| btree | równość, zakresy, `ORDER BY`, unikalność | tekst do wyszukiwania pełnotekstowego |
| GIN | `tsvector`, `jsonb`, tablice, trigramy | częste `UPDATE` indeksowanej kolumny (drogi zapis; złagodź `fastupdate`) |
| GiST | zakresy, geometria, wykluczenia, `pg_trgm` z `%` | tam, gdzie GIN wystarczy (GIN szybszy w odczycie) |
| BRIN | ogromne tabele z fizycznie skorelowaną kolumną (log po czasie) | dane wstawiane losowo — BRIN wtedy nic nie daje |
| Hash | tylko `=`, mniejszy od btree | cokolwiek innego |
| częściowy (`WHERE`) | gdy zapytania zawsze mają ten sam predykat | |
| pokrywający (`INCLUDE`) | żeby uzyskać Index Only Scan | |

### Reguły, których łamanie widać w planie

- **Kolejność kolumn w indeksie złożonym**: najpierw kolumny z równością, potem jedna
  z zakresem, potem `ORDER BY`. Indeks `(status, utworzono)` obsłuży
  `WHERE status='x' ORDER BY utworzono`; indeks `(utworzono, status)` już nie tak dobrze.
- **Funkcja na kolumnie zabija indeks**: `WHERE lower(email) = $1` wymaga indeksu
  `ON t (lower(email))`. `WHERE date(utworzono) = $1` wymaga przepisania na
  `WHERE utworzono >= $1 AND utworzono < $1 + 1`.
- **Niezgodność typów zabija indeks**: kolumna `bigint` porównana z parametrem `numeric`
  → seq scan. Rzutuj po stronie parametru, nie kolumny.
- **Indeks częściowy** przy silnej nierównowadze: jeśli 99% wierszy ma `usuniete = false`,
  indeks `WHERE usuniete = false` jest kilkakrotnie mniejszy i lepiej trafia w cache.
- **Index Only Scan** wymaga aktualnej mapy widoczności — po dużym `UPDATE` bez `VACUUM`
  planer wróci do Index Scan i wyda się, że indeks „przestał działać”.

```sql
-- częściowy + pokrywający
CREATE INDEX CONCURRENTLY idx_spraw_aktywne
  ON sprawy (kancelaria_id, zmodyfikowano DESC)
  INCLUDE (tytul, status)
  WHERE archiwum = false;
```

### Wykrywanie indeksów zbędnych i brakujących

```sql
-- nigdy nieużywane (uwaga: statystyki od ostatniego pg_stat_reset)
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelid NOT IN (SELECT conindid FROM pg_constraint)
ORDER BY pg_relation_size(indexrelid) DESC;

-- tabele skanowane sekwencyjnie mimo rozmiaru
SELECT relname, seq_scan, seq_tup_read, idx_scan,
       seq_tup_read / NULLIF(seq_scan,0) AS wierszy_na_skan
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC LIMIT 20;
```

Każdy indeks kosztuje przy każdym `INSERT`/`UPDATE`. Pięć indeksów na tabeli o dużym
ruchu zapisu to zwykle o trzy za dużo.

## EXPLAIN: jak sprawdzić, że indeks jest używany

```sql
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT TEXT)
SELECT ... ;
```

Czytaj od najgłębszego wcięcia. Cztery rzeczy, na które patrzysz:

1. **`rows=` szacowane vs `actual rows=`.** Rozjazd > 10× oznacza złe statystyki albo
   skorelowane kolumny. Lek: `ANALYZE tabela;` a jeśli to nie pomaga —
   `CREATE STATISTICS ... (dependencies, ndistinct) ON kol_a, kol_b FROM tabela;`
2. **`Buffers: shared hit=... read=...`.** `read` to odczyty z dysku (albo z cache systemu).
   Wysokie `read` przy małym wyniku = brak indeksu albo zły indeks.
3. **`Rows Removed by Filter`.** Duża liczba oznacza, że indeks dowiózł za dużo wierszy
   i filtr odsiał je dopiero po odczycie — brakuje kolumny w indeksie albo indeksu częściowego.
4. **Węzeł `Sort` z `Sort Method: external merge  Disk: ... kB`** — `work_mem` za małe
   dla tego zapytania. Podnieś `work_mem` sesyjnie, nie globalnie.

Objawy i przyczyny:

| Węzeł w planie | Co oznacza | Reakcja |
|---|---|---|
| `Seq Scan` na dużej tabeli z selektywnym `WHERE` | brak indeksu, funkcja na kolumnie, niezgodny typ | popraw predykat albo dodaj indeks |
| `Bitmap Heap Scan` z dużym `Rows Removed by Index Recheck` | `work_mem` za małe, bitmapa „lossy” | podnieś `work_mem` |
| `Nested Loop` z ogromną liczbą pętli | planer nie doszacował rozmiaru zewnętrznego | statystyki; ewentualnie przepisanie zapytania |
| `Hash Join` z `Batches: 8` | hash nie mieści się w `work_mem` | podnieś `work_mem` |
| `Index Scan` zamiast `Index Only Scan` | nieaktualna mapa widoczności | `VACUUM tabela;` |
| brak węzła `Parallel` przy dużym skanie | `max_parallel_workers_per_gather = 0` albo tabela za mała | konfiguracja |

Zapytania do znalezienia kandydatów (wymaga `pg_stat_statements`, `shared_preload_libraries`):

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT substr(query, 1, 100) AS zapytanie, calls,
       round(total_exec_time::numeric, 1) AS ms_lacznie,
       round(mean_exec_time::numeric, 2)  AS ms_srednio,
       rows / NULLIF(calls,0)             AS wierszy_na_wywolanie
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;
```

Optymalizuj według `total_exec_time`, nie `mean_exec_time`. Zapytanie trwające 2 ms
wywoływane 5 mln razy dziennie kosztuje więcej niż raport trwający 30 s.

## Transakcje i poziomy izolacji

Postgres używa MVCC. Domyślny poziom to **Read Committed** — każde polecenie w transakcji
widzi migawkę z momentu startu tego polecenia, nie transakcji.

| Poziom | Co eliminuje | Koszt |
|---|---|---|
| Read Committed (domyślny) | brudny odczyt | odczyt niepowtarzalny i fantomy możliwe |
| Repeatable Read | + odczyt niepowtarzalny, fantomy | błąd `could not serialize access` przy konflikcie zapisu — aplikacja musi ponawiać |
| Serializable | + anomalie serializacji (SSI) | więcej wycofań; wymaga logiki ponawiania |

W Postgresie Repeatable Read jest realizowany jako snapshot isolation i blokuje także
fantomy — inaczej niż w standardzie SQL.

Kiedy podnieść poziom: operacja czytająca kilka tabel i podejmująca na tej podstawie decyzję
zapisu (przelew, przydział zasobu, generowanie kolejnego numeru w repertorium).
Alternatywa bez podnoszenia poziomu — blokada jawna:

```sql
BEGIN;
SELECT saldo FROM konta WHERE id = $1 FOR UPDATE;   -- blokuje wiersz do końca transakcji
UPDATE konta SET saldo = saldo - $2 WHERE id = $1;
COMMIT;
```

`FOR UPDATE SKIP LOCKED` to poprawny sposób na kolejkę zadań w Postgresie:

```sql
UPDATE zadania SET status = 'w_toku', podjeto = now()
WHERE id IN (
  SELECT id FROM zadania WHERE status = 'oczekuje'
  ORDER BY priorytet DESC, id
  FOR UPDATE SKIP LOCKED
  LIMIT 10
)
RETURNING *;
```

Bez `SKIP LOCKED` równoległe procesy ustawiają się w kolejkę na tym samym wierszu.

Zasady, które oszczędzają awarie:
- Transakcja trzyma migawkę i blokuje `VACUUM` w całej bazie. **Nie wywołuj HTTP ani nie
  czekaj na użytkownika wewnątrz transakcji.** Konsekwencja: puchnięcie tabel (bloat),
  bo martwe krotki nie mogą być sprzątnięte.
- `idle_in_transaction_session_timeout` ustawiony (np. 60 s) — inaczej jedna zawieszona
  sesja aplikacji zatrzymuje sprzątanie w całej bazie.
- `statement_timeout` ustawiony per rola aplikacyjna. Bez tego jedno złe zapytanie
  zajmuje połączenie na godziny.
- `lock_timeout` (np. 3 s) dla migracji — inaczej `ALTER TABLE` czekający na blokadę
  ustawia za sobą kolejkę wszystkich zapytań do tej tabeli.

## Blokady i zakleszczenia

Postgres wykrywa zakleszczenia (`deadlock_timeout`, domyślnie 1 s) i wycofuje jedną
z transakcji z błędem `40P01`. Aplikacja musi to obsłużyć ponowieniem.

Trzy najczęstsze przyczyny:
1. **Różna kolejność aktualizacji wierszy** w dwóch ścieżkach kodu. Lek: zawsze aktualizuj
   w ustalonej kolejności (np. rosnąco po kluczu głównym).
2. **Klucz obcy bez indeksu po stronie dziecka.** `DELETE` na rodzicu skanuje sekwencyjnie
   dziecko i bierze blokady na wiele wierszy. Lek: indeks na każdej kolumnie FK.
3. **`ALTER TABLE` w godzinach ruchu.** `ACCESS EXCLUSIVE` czeka na zakończenie
   długiego `SELECT`, a wszystkie nowe zapytania czekają za nim.

Diagnostyka na żywo:

```sql
SELECT a.pid, a.state, now() - a.xact_start AS trwa,
       a.wait_event_type, a.wait_event,
       left(a.query, 120) AS zapytanie
FROM pg_stat_activity a
WHERE a.state <> 'idle' AND a.backend_type = 'client backend'
ORDER BY a.xact_start;

-- kto kogo blokuje (PG 9.6+)
SELECT pid, pg_blocking_pids(pid) AS blokowany_przez, left(query, 80)
FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Bezpieczna migracja: `SET lock_timeout = '3s';` + ponawianie w pętli, zamiast jednego
`ALTER TABLE` czekającego bez końca.

## Wyszukiwanie pełnotekstowe po polsku

Domyślna konfiguracja `english` na polskim tekście nie rozpoznaje odmiany: „umowa”,
„umowy”, „umowie” to trzy różne lematy. Recall spada mniej więcej do połowy.

### PostgreSQL 19 (wersja w becie — nie na produkcję)

Wbudowany stemmer Snowball dla polskiego jest w gałęzi rozwojowej 19 (dodany przez Toma Lane'a,
wymieniony w notach wydania 19). Po wydaniu finalnym wystarczy `to_tsvector('polish', ...)` bez
instalowania słowników. Do tego czasu obowiązuje droga dla wersji 18 i niższych opisana niżej.
Stemmer obcina końcówki algorytmicznie — jest gorszy od pełnego słownika morfologicznego, ale
bezobsługowy.

### PostgreSQL ≤ 18: hunspell/ispell

```bash
# słowniki z pakietu LibreOffice, konwersja do UTF-8 (Postgres wymaga UTF-8)
iconv -f iso-8859-2 -t utf-8 pl_PL.aff > pl_pl.affix
iconv -f iso-8859-2 -t utf-8 pl_PL.dic > pl_pl.dict
sudo cp pl_pl.affix pl_pl.dict /usr/share/postgresql/18/tsearch_data/
```

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TEXT SEARCH DICTIONARY polish_hunspell (
  TEMPLATE  = ispell,
  DictFile  = pl_pl,
  AffFile   = pl_pl,
  StopWords = polish          -- plik polish.stop w tsearch_data
);

CREATE TEXT SEARCH CONFIGURATION public.polski (COPY = pg_catalog.simple);

ALTER TEXT SEARCH CONFIGURATION public.polski
  ALTER MAPPING FOR asciiword, asciihword, hword_asciipart,
                    word, hword, hword_part
  WITH unaccent, polish_hunspell, simple;

ALTER TEXT SEARCH CONFIGURATION public.polski
  DROP MAPPING FOR email, url, url_path, sfloat, float;
```

Kolejność `unaccent, polish_hunspell, simple` jest istotna: `unaccent` normalizuje
diakrytyki, hunspell podaje lemat, `simple` łapie wszystko, czego hunspell nie zna
(nazwiska, terminy prawnicze spoza słownika). Bez `simple` na końcu nieznane słowa
wypadają z indeksu całkowicie.

### Kolumna, indeks, zapytanie

```sql
ALTER TABLE fragmenty
  ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('public.polski', tresc)) STORED;

CREATE INDEX CONCURRENTLY idx_fragmenty_tsv ON fragmenty USING gin (tsv);

-- zapytanie z rankingiem
SELECT id, dokument_id, strona,
       ts_rank_cd(tsv, q) AS ranga,
       ts_headline('public.polski', tresc, q,
                   'MaxFragments=2, MinWords=15, MaxWords=35') AS podglad
FROM fragmenty, websearch_to_tsquery('public.polski', $1) AS q
WHERE tsv @@ q
ORDER BY ranga DESC
LIMIT 50;
```

- `websearch_to_tsquery` przyjmuje składnię, którą ludzie znają: `"fraza dosłowna"`,
  `-wykluczenie`, `or`. `plainto_tsquery` łączy wszystko przez AND. `to_tsquery` wymaga
  poprawnej składni i wywala się na wejściu od użytkownika.
- `ts_rank_cd` uwzględnia bliskość terminów, `ts_rank` nie. Do dokumentów prawniczych
  `ts_rank_cd`.
- Kolumna generowana (`GENERATED ALWAYS AS ... STORED`) zastępuje trigger. Działa od PG 12.

### Sygnatury, nazwiska, dopasowanie przybliżone

FTS nie znajdzie „II CSK 123/19” wpisanego jako „IICSK123/19” ani literówki w nazwisku.
Do tego `pg_trgm`:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY idx_strony_nazwa_trgm
  ON strony USING gin (nazwa gin_trgm_ops);

SELECT nazwa, similarity(nazwa, $1) AS s
FROM strony
WHERE nazwa % $1               -- używa indeksu, próg z pg_trgm.similarity_threshold
ORDER BY s DESC LIMIT 20;
```

`ILIKE '%fraza%'` również korzysta z indeksu GIN trigramowego — to jedyny sposób na
szybkie dopasowanie „zawiera” bez skanowania tabeli.

### Alternatywa: pg_search (ParadeDB)

`pg_search` **0.25.0** (28.07.2026), oparty na Tantivy, daje w Postgresie prawdziwe BM25
z tokenizatorami, fasetami i podświetlaniem — czyli to, czego `tsvector` nie ma
(`ts_rank_cd` nie jest BM25 i nie uwzględnia statystyk korpusu tak samo).
Bierz go, gdy: (a) porównujesz jakość z Elasticsearch, (b) potrzebujesz strojenia
tokenizacji, (c) łączysz BM25 z wektorami w jednym zapytaniu. Koszt: dodatkowe
rozszerzenie, którego nie ma w zarządzanych Postgresach poza ParadeDB, Neon i kilkoma innymi.

## Partycjonowanie

Deklaratywne partycjonowanie (PG 10+). Sięgaj po nie, gdy tabela przekracza ~100 mln
wierszy **albo** gdy potrzebujesz taniego usuwania starych danych (`DROP PARTITION`
zamiast `DELETE` na milionach wierszy).

```sql
CREATE TABLE zdarzenia (
  id          bigint GENERATED ALWAYS AS IDENTITY,
  wystapilo   timestamptz NOT NULL,
  sprawa_id   bigint NOT NULL,
  tresc       jsonb NOT NULL
) PARTITION BY RANGE (wystapilo);

CREATE TABLE zdarzenia_2026_08 PARTITION OF zdarzenia
  FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
```

Zasady:
- Klucz partycjonowania **musi** wchodzić w skład klucza głównego i każdego unikalnego
  indeksu. To najczęstsza niespodzianka przy migracji istniejącej tabeli.
- Odcinanie partycji (partition pruning) działa tylko, gdy predykat na kluczu jest
  w zapytaniu. `WHERE sprawa_id = 5` bez warunku na `wystapilo` przeszuka wszystkie partycje.
- Nie rób setek partycji „na zapas”. Planowanie zapytania rośnie z ich liczbą;
  powyżej kilkuset partycji planer zaczyna być zauważalnym kosztem.
- Tworzenie kolejnych partycji zautomatyzuj (pg_partman albo własne zadanie).
  Brak partycji na jutro = błąd wstawienia o północy.

## Replikacja i kopie zapasowe

**Replikacja strumieniowa** (fizyczna): repliki tylko do odczytu, przełączenie ręczne albo
przez Patroni/repmgr. `synchronous_commit = on` na replice synchronicznej kosztuje
opóźnienie zapisu równe RTT — dla systemu dokumentowego zwykle nie jest potrzebne.
Odczyt z repliki wymaga akceptacji opóźnienia (`hot_standby_feedback = on` chroni przed
konfliktami, ale wstrzymuje `VACUUM` na primary).

**Replikacja logiczna**: wybrane tabele, między różnymi wersjami Postgresa. Do migracji
z minimalnym przestojem i do zasilania systemów analitycznych. Nie replikuje DDL — zmiana
schematu musi być zastosowana ręcznie po obu stronach.

**Kopie**:

| Metoda | Odtworzenie | Kiedy |
|---|---|---|
| `pg_dump -Fc` | pełne, do dowolnej wersji | bazy do ~100 GB, migracje |
| `pg_basebackup` + WAL | PITR, do dowolnego punktu w czasie | produkcja |
| pgBackRest / WAL-G | PITR, przyrostowe, do S3 | produkcja powyżej kilkuset GB |
| migawka wolumenu | szybkie, ale wymaga spójności | tylko z `pg_start_backup`/ zamrożeniem FS |

Reguła: **kopia nieprzetestowana w odtworzeniu nie istnieje.** Wpisz do harmonogramu
kwartalne odtworzenie na osobnej maszynie i zmierz RTO. Klient prawniczy dodatkowo
potrzebuje odpowiedzi na pytanie „jak odzyskać stan akt z 3 marca” — to jest PITR,
a nie nocny dump.

## Połączenia i pgbouncer

Każde połączenie do Postgresa to osobny proces (~5–10 MB). Powyżej ~2–3× liczby rdzeni
przepustowość spada. Aplikacja z pulą 100 połączeń na 8 rdzeniach szkodzi sama sobie.

pgbouncer, tryby:

| Tryb | Co daje | Czego nie wolno |
|---|---|---|
| `session` | połączenie na czas sesji klienta | mała oszczędność |
| **`transaction`** | połączenie zwalniane po COMMIT — właściwy wybór | `SET` sesyjny, tymczasowe tabele, `LISTEN/NOTIFY`, kursory WITH HOLD, instrukcje przygotowane (chyba że `max_prepared_statements > 0`) |
| `statement` | po każdym zapytaniu | brak transakcji wielopoleceniowych |

```ini
[databases]
akta = host=127.0.0.1 port=5432 dbname=akta

[pgbouncer]
pool_mode = transaction
max_client_conn = 2000
default_pool_size = 25          ; ~2-3 x liczba rdzeni bazy
reserve_pool_size = 5
server_idle_timeout = 60
max_prepared_statements = 200   ; wymagane dla psycopg3/asyncpg z prepared statements
```

Sanity check: `default_pool_size` × liczba baz × liczba instancji pgbouncera musi być
mniejsze od `max_connections` w Postgresie.

## Katalog typowych błędów wydajnościowych

| Błąd | Co się dzieje |
|---|---|
| `SELECT *` w kodzie aplikacji | ciągnie TOAST-owane `jsonb`/`text`, zabija Index Only Scan; zmiana schematu psuje kod |
| Zapytanie N+1 z ORM | 200 zapytań po 1 ms zamiast jednego po 5 ms; widoczne dopiero na produkcji |
| `OFFSET 10000 LIMIT 20` | baza czyta i odrzuca 10 000 wierszy; użyj paginacji kluczowej (`WHERE (data, id) < ($1,$2)`) |
| `COUNT(*)` na dużej tabeli przy każdym żądaniu | pełny skan; użyj `reltuples` z `pg_class` do przybliżenia albo licznika materializowanego |
| Brak indeksu na kolumnie klucza obcego | `DELETE` na rodzicu skanuje sekwencyjnie dziecko; źródło zakleszczeń |
| `UPDATE` całego wiersza, gdy zmienia się jedno pole | nowa wersja krotki, aktualizacja wszystkich indeksów, więcej WAL |
| Kolumna `updated_at` aktualizowana przy każdym odczycie | zamienia odczyt w zapis i puchnie tabelę |
| `gen_random_uuid()` jako klucz główny dużej tabeli | losowe wstawienia rozbijają btree, rosną WAL i I/O; użyj `uuidv7()` (PG18) |
| `text` w kluczu głównym zamiast klucza sztucznego | szerokie indeksy we wszystkich tabelach potomnych |
| Brak `ANALYZE` po masowym wstawieniu | planer działa na zerowych statystykach i wybiera Nested Loop na 10 mln wierszy |
| Domyślne `default_statistics_target = 100` przy kolumnie o skośnym rozkładzie | złe szacunki; podnieś per kolumna: `ALTER TABLE t ALTER COLUMN c SET STATISTICS 1000` |
| `work_mem` globalnie podniesione do 256 MB | 100 równoczesnych sortowań = 25 GB; ustaw sesyjnie dla raportów |
| Długo otwarta transakcja w tle | `VACUUM` nie sprząta niczego w całej bazie; tabele puchną liniowo |
| Wyłączony autovacuum „bo obciąża” | zawijanie identyfikatorów transakcji i wymuszone zatrzymanie bazy |
| Indeks na kolumnie o dwóch wartościach (`aktywny bool`) | planer i tak wybierze seq scan; użyj indeksu częściowego |
| `LIKE '%fraza%'` bez `pg_trgm` | pełny skan przy każdym wyszukiwaniu |
| `ORDER BY random() LIMIT 1` | sortuje całą tabelę |
| Puste `WHERE` przy usuwaniu w migracji | blokada wszystkich wierszy i godziny WAL |

## Minimalna konfiguracja produkcyjna

Punkt wyjścia dla maszyny 8 rdzeni / 32 GB RAM, obciążenie mieszane:

```ini
shared_buffers = 8GB                 # ~25% RAM
effective_cache_size = 24GB          # ~75% RAM, tylko podpowiedź dla planera
work_mem = 32MB                      # per operacja sortowania/hasha, nie per zapytanie
maintenance_work_mem = 2GB           # przyspiesza CREATE INDEX i VACUUM
max_connections = 100                # reszta przez pgbouncer
random_page_cost = 1.1               # SSD/NVMe; domyślne 4.0 to dysk talerzowy
effective_io_concurrency = 200       # SSD
wal_compression = zstd
checkpoint_timeout = 15min
max_wal_size = 8GB
statement_timeout = 30s              # nadpisywane per rola dla zadań wsadowych
idle_in_transaction_session_timeout = 60s
log_min_duration_statement = 500ms
log_lock_waits = on
track_io_timing = on
shared_preload_libraries = 'pg_stat_statements'
io_method = worker                   # PG18; io_uring jeśli jądro na to pozwala
```

`random_page_cost = 4.0` na SSD to najczęstsza pojedyncza przyczyna wybierania seq scan
zamiast index scan na zarządzanych i domyślnie skonfigurowanych instancjach.
