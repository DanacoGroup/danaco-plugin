# SQLite — karta

Przeczytaj kartę w całości przed pracą z bazą SQLite (dotyczy SQLite 3.35+). Stosuj wskazania
bezwzględnie; każde odstępstwo uzasadnij w opisie zmiany.

## Konwencje schematu

- Nazywaj tabele rzeczownikami w liczbie mnogiej, w snake_case: `orders`, `invoice_items`.
- Nazywaj kolumny w liczbie pojedynczej: `customer_id`, `created_at`, `total_amount`.
- Nazywaj obiekty pomocnicze według stałego wzorca: indeksy `idx_<tabela>_<kolumny>`,
  ograniczenia unikalności `uq_<tabela>_<kolumny>`, klucze obce `fk_<tabela>_<tabela_docelowa>`.
- Deklaruj tabele z klauzulą `STRICT` (SQLite 3.37+): bez niej SQLite stosuje typowanie
  elastyczne i przyjmie łańcuch do kolumny `INTEGER`. W tabelach STRICT dozwolone typy to
  `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB`, `ANY`.
- Klucz główny definiuj jako `INTEGER PRIMARY KEY` — staje się aliasem wewnętrznego `rowid`
  i jest najtańszym możliwym kluczem. Dodaj `AUTOINCREMENT` wyłącznie, gdy identyfikatory
  nie mogą być nigdy ponownie użyte; w pozostałych przypadkach to zbędny koszt.
- Deklaruj `NOT NULL` domyślnie na każdej kolumnie; dopuszczenie NULL musi być świadomą decyzją.
- Kwoty pieniężne przechowuj jako `INTEGER` w najmniejszej jednostce (grosze, centy) —
  SQLite nie posiada typu dziesiętnego o stałej precyzji, a `REAL` wprowadza błędy zaokrągleń.
- Daty i czas przechowuj jako `TEXT` w formacie ISO 8601 UTC (`YYYY-MM-DD HH:MM:SS`)
  albo jako `INTEGER` (epoka uniksowa). Oba formaty sortują się poprawnie i współpracują
  z wbudowanymi funkcjami `date()`, `datetime()`, `strftime()`.
- Wartości logiczne przechowuj jako `INTEGER` 0/1 z ograniczeniem `CHECK (col IN (0, 1))`.
- Wzorzec definicji tabeli:

```sql
CREATE TABLE orders (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers (id),
    status       TEXT    NOT NULL DEFAULT 'pending',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
) STRICT;
```

- Egzekwowanie kluczy obcych jest domyślnie wyłączone: wykonuj `PRAGMA foreign_keys = ON`
  po otwarciu każdego połączenia — ustawienie nie jest trwałe ani globalne.

## Migracje i zmiany schematu

- Prowadź zmiany schematu przez wersjonowane migracje (Alembic, dbmate, goose, mechanizm
  frameworku) albo — w małych projektach — przez `PRAGMA user_version` i skrypty numerowane.
- `ALTER TABLE` w SQLite jest ograniczony: obsługuje `RENAME TO`, `RENAME COLUMN`,
  `ADD COLUMN` oraz `DROP COLUMN` (3.35+, z zastrzeżeniami dla kolumn indeksowanych
  lub objętych ograniczeniami). Nie obsługuje zmiany typu kolumny ani dodania ograniczenia.
- Zmiany niewspierane wykonuj procedurą dwunastu kroków z dokumentacji SQLite, w skrócie:
  utwórz nową tabelę o docelowej definicji, przenieś dane przez `INSERT INTO ... SELECT`,
  usuń starą tabelę, zmień nazwę nowej, odtwórz indeksy i wyzwalacze — wszystko w jednej
  transakcji, z `PRAGMA foreign_keys = OFF` na czas operacji.
- Po takiej przebudowie wykonaj `PRAGMA foreign_key_check` przed zatwierdzeniem transakcji.
- Ścieżka wycofania: przed każdą migracją wykonaj kopię pliku bazy (poleceniem `.backup`
  lub `VACUUM INTO`); wycofanie polega na przywróceniu kopii albo skrypcie odwrotnym (down).
- Nie modyfikuj schematu równolegle z ruchem produkcyjnym — zmiana schematu wymaga
  wyłącznego dostępu do bazy na czas transakcji DDL.

## Zapytania i indeksy

- Parametryzuj każde zapytanie (`?` lub parametry nazwane `:name`). Nigdy nie składaj SQL
  przez konkatenację ani interpolację łańcuchów.
- Przed optymalizacją odczytaj plan: `EXPLAIN QUERY PLAN <zapytanie>`. Szukaj wpisów
  `SCAN <tabela>` (pełny skan) i zastępuj je `SEARCH ... USING INDEX`, gdy zapytanie
  jest częste, a tabela duża.
- Zakładaj indeks, gdy kolumna występuje w `WHERE`, `JOIN` lub `ORDER BY` częstych zapytań.
  Nie indeksuj tabel o kilkuset wierszach — pełny skan bywa tańszy.
- W indeksach złożonych umieszczaj najpierw kolumny porównywane przez równość, potem
  zakresowe lub sortowane. Indeks `(a, b)` obsługuje warunki na `a` oraz `a, b`, nie na samo `b`.
- Stosuj indeksy częściowe dla aktywnych podzbiorów danych:

```sql
CREATE INDEX idx_orders_pending ON orders (created_at) WHERE status = 'pending';
```

- Stosuj indeksy na wyrażeniach dla wyszukiwań po funkcji, np. `ON users (lower(email))`,
  i używaj identycznego wyrażenia w zapytaniu.
- `LIKE 'fraza%'` korzysta z indeksu tylko przy spełnionych warunkach optymalizacji
  (m.in. `case_sensitive_like` lub kolumna `NOCASE`); wzorzec z wiodącym `%` nie korzysta
  z indeksu nigdy — do wyszukiwań pełnotekstowych stosuj moduł FTS5.
- Po masowych zmianach danych wykonaj `ANALYZE` (lub `PRAGMA optimize` przy zamykaniu
  połączenia), aby planer dysponował aktualnymi statystykami.

## Transakcje i współbieżność

- Włącz tryb WAL: `PRAGMA journal_mode = WAL` (ustawienie trwałe dla pliku bazy).
  WAL pozwala czytelnikom działać równolegle z jednym zapisującym; domyślny tryb rollback
  journal blokuje czytelników na czas zapisu.
- SQLite dopuszcza dokładnie jednego zapisującego naraz — niezależnie od trybu dziennika.
  Projektuj aplikację tak, aby zapisy były krótkie i serializowane (np. jedna kolejka zapisów).
- Ustaw `PRAGMA busy_timeout = 5000` (milisekundy) na każdym połączeniu; bez tego
  równoczesny zapis kończy się natychmiastowym błędem `SQLITE_BUSY` zamiast oczekiwania.
- Transakcje zapisu rozpoczynaj przez `BEGIN IMMEDIATE`, aby uzyskać blokadę zapisu od razu;
  `BEGIN DEFERRED` może zakończyć się `SQLITE_BUSY` w trakcie transakcji, przy próbie
  eskalacji z odczytu do zapisu, gdy inny zapis został już zatwierdzony.
- Izolacja: pojedyncze połączenie widzi migawkę spójną w ramach transakcji (serializacja
  zapisów daje w praktyce izolację szeregowalną między połączeniami). Nie współdziel
  jednego połączenia między wątkami bez serializacji dostępu.
- Grupuj masowe wstawienia w jawne transakcje: tysiące pojedynczych `INSERT` bez transakcji
  oznacza tysiące synchronizacji z dyskiem i spadek wydajności o rzędy wielkości.

## Eksploatacja

- Kopie zapasowe wykonuj poleceniem `.backup` powłoki `sqlite3`, interfejsem SQLite Backup API
  albo `VACUUM INTO 'kopia.db'`. Nie kopiuj pliku bazy narzędziami systemowymi, gdy baza jest
  używana — kopia będzie niespójna; w trybie WAL pominięcie plików `-wal` i `-shm` gubi dane.
- Regularnie wykonuj `PRAGMA integrity_check` (pełna kontrola) lub `PRAGMA quick_check`
  (szybsza); wynik inny niż `ok` oznacza uszkodzenie — przywróć bazę z kopii.
- Usunięcie danych nie zmniejsza pliku bazy; wolne strony podlegają ponownemu użyciu.
  `VACUUM` przebudowuje plik i odzyskuje miejsce — wykonuj po masowych usunięciach,
  poza szczytem, mając wolną przestrzeń dyskową równą rozmiarowi bazy.
- W trybie WAL kontroluj rozmiar pliku `-wal`; punkt kontrolny wykonuje się automatycznie,
  a ręcznie przez `PRAGMA wal_checkpoint(TRUNCATE)` w oknie niskiego ruchu.
- Umieszczaj plik bazy na lokalnym systemie plików. Nie umieszczaj go na udziałach
  sieciowych (NFS, SMB) — wadliwe blokady plików prowadzą do uszkodzenia bazy.
- Rozważ `PRAGMA synchronous = NORMAL` w trybie WAL: trwałość zatwierdzeń względem utraty
  zasilania jest osłabiona, ale spójność bazy zachowana; `FULL` pozostaw tam, gdzie każda
  zatwierdzona transakcja musi przetrwać awarię zasilania.

## Typowe błędy modeli LLM przy pracy z tym systemem

1. Założenie ścisłych typów bez klauzuli `STRICT`: w zwykłej tabeli SQLite zapisze łańcuch
   `'abc'` do kolumny `INTEGER` bez błędu. Deklaruj tabele ze `STRICT` albo dodawaj
   ograniczenia `CHECK (typeof(col) = 'integer')`.
2. Równoległe zapisy bez trybu WAL i bez `busy_timeout`: aplikacja wielowątkowa lub
   wieloprocesowa zgłasza `SQLITE_BUSY` / „database is locked”. Poprawnie: `journal_mode = WAL`,
   `busy_timeout` na każdym połączeniu, krótkie transakcje `BEGIN IMMEDIATE`.
3. Przechowywanie dat w formatach niesortowalnych (`DD.MM.YYYY`, `MM/DD/YYYY`, lokalne strefy
   bez oznaczenia): porównania i `ORDER BY` dają błędne wyniki. Poprawnie: ISO 8601 w UTC
   albo epoka uniksowa w `INTEGER`.
4. Założenie, że klucze obce działają domyślnie: bez `PRAGMA foreign_keys = ON` na danym
   połączeniu SQLite nie egzekwuje ograniczeń referencyjnych i przyjmie wiersze osierocone.
5. Składnia innych systemów: `SERIAL`, `AUTO_INCREMENT`, `NOW()`, `TRUE/FALSE` jako typ kolumny,
   `VARCHAR(255)` z oczekiwaniem limitu długości — SQLite ignoruje deklarowaną długość.
   Poprawnie: `INTEGER PRIMARY KEY`, `datetime('now')`, `INTEGER` 0/1, limit przez `CHECK`.
6. Przechowywanie kwot w `REAL`: błędy zaokrągleń binarnych zniekształcają sumy.
   Poprawnie: `INTEGER` w najmniejszej jednostce waluty.
7. Masowe wstawianie bez jawnej transakcji: każdy `INSERT` w trybie autocommit to osobna
   synchronizacja z dyskiem. Poprawnie: jedna transakcja na partię oraz zapytania parametryzowane.
8. Nadużywanie `AUTOINCREMENT`: zbędne przy zwykłym `INTEGER PRIMARY KEY`; dodaje tabelę
   `sqlite_sequence` i koszt każdego wstawienia. Stosuj tylko przy zakazie ponownego użycia id.
9. Kopiowanie pliku aktywnej bazy poleceniem `cp` jako „kopia zapasowa”: kopia bywa niespójna,
   a w trybie WAL pomija niezatwierdzone punkty kontrolne. Poprawnie: `.backup` lub `VACUUM INTO`.
10. Traktowanie SQLite jak serwera dla wielu procesów o intensywnych zapisach: SQLite ma
    jednego zapisującego i blokuje na poziomie całej bazy. Przy trwałej rywalizacji o zapis
    rekomenduj migrację do systemu klient–serwer (np. PostgreSQL).
