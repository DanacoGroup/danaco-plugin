# Niezawodność i eksploatacja — karta

Przeczytaj kartę w całości przed pracą nad kopiami zapasowymi, migracją
wysokiego ryzyka, diagnozą awarii lub planowaniem pojemności — dla PostgreSQL
i SQLite. Zasada nadrzędna: niezawodność mierzy się w scenariuszu awarii —
każdy mechanizm z tej karty przećwicz, zanim będzie potrzebny.

## Kopie zapasowe

### PostgreSQL — kopia logiczna a fizyczna

- `pg_dump -Fc <baza>` (format custom) to kopia logiczna: spójna migawka
  z chwili startu, odtwarzalna selektywnie przez `pg_restore` (pojedyncze
  tabele, `--jobs`). Role i ustawienia klastra zabezpiecza osobno
  `pg_dumpall --globals-only`. Odtwarza wyłącznie stan z chwili zrzutu,
  a odtworzenie dużej bazy (dane, indeksy, walidacja ograniczeń) trwa godziny.
- Kopia fizyczna z archiwizacją WAL to podstawa odtwarzania do punktu w czasie
  (PITR): `pg_basebackup` plus ciągła archiwizacja WAL (`archive_mode = on`,
  `archive_command`; produkcyjnie pgBackRest lub WAL-G — kompresja, retencja,
  weryfikacja). Odtwarzanie: rozpakuj kopię bazową, wskaż archiwum
  w `restore_command`, ustaw `recovery_target_time`, utwórz `recovery.signal`
  — serwer zatrzyma się tuż przed wskazaną chwilą. To jedyna obrona przed
  „omyłkowym `DELETE` o 14:37” — odtwarzasz stan z 14:36.
- Dobór: kopia logiczna wystarcza, gdy utrata dnia danych jest akceptowalna;
  PITR jest obowiązkowy, gdy RPO liczy się w minutach.
- Nie kopiuj katalogu danych działającego serwera narzędziami plikowymi — taka
  kopia jest niespójna i nieodtwarzalna.

### SQLite — kopia działającej bazy

- Kopię bazy używanej wykonuj wyłącznie mechanizmem świadomym transakcji:
  `sqlite3 app.db ".backup 'kopia.db'"` (lub Backup API sterownika) albo
  `VACUUM INTO 'kopia.db'` (SQLite 3.27+) — ten drugi defragmentuje kopię
  kosztem pełnego przepisania bazy.
- Kopiowanie pliku (`cp`, rsync) jest bezpieczne tylko, gdy żaden proces nie ma
  bazy otwartej; inaczej ryzykujesz kopię z połowy transakcji, a w trybie WAL —
  pominięcie plików `-wal` i `-shm`, czyli utratę zatwierdzonych danych sprzed
  punktu kontrolnego. Snapshot systemu plików musi być atomowy
  i obejmować wszystkie trzy pliki.
- Kopię weryfikuj po wykonaniu: `sqlite3 kopia.db "PRAGMA integrity_check;"`
  musi zwrócić `ok`.

### Test odtworzeniowy

- Kopia nietestowana odtworzeniem nie istnieje. Procedura minimalna, co najmniej
  raz na kwartał (po zmianie mechanizmu kopii — natychmiast):
  1. pobierz najnowszą kopię z miejsca składowania (nie z serwera źródłowego),
  2. odtwórz na osobnym środowisku, mierząc czas — to rzeczywiste RTO,
  3. zweryfikuj spójność (PostgreSQL: serwer startuje, `pg_dump` przechodzi;
     SQLite: `PRAGMA integrity_check` = `ok`),
  4. zweryfikuj merytorycznie: liczności kluczowych tabel, sumy wybranych
     agregatów, data najnowszego wiersza,
  5. dla PITR: przećwicz odtworzenie do wskazanej minuty,
  6. zapisz wynik (czas, wolumen, problemy) w dokumentacji eksploatacyjnej.
- Składuj kopie poza maszyną bazy (inna strefa awarii), z retencją na piśmie;
  obejmij je tymi samymi wymogami szyfrowania i dostępu co bazę.

## Migracje wysokiego ryzyka

### PostgreSQL — zmiany blokujące a bezpieczne

- Przed migracją na bazie produkcyjnej ustaw limity w sesji migracyjnej:
  `SET lock_timeout = '5s'; SET statement_timeout = '60s';` — migracja, która nie może
  dostać blokady, ma się poddać i zostać ponowiona poza szczytem.
- Dodanie kolumny z `DEFAULT` stałym jest bezpieczne w PostgreSQL 11+ (wartość
  w metadanych, bez przepisania tabeli). `DEFAULT` z funkcją zmienną
  (np. `now()`) przepisuje tabelę — wtedy: dodaj kolumnę
  NULL, uzupełniaj partiami, `DEFAULT` ustaw na końcu.
- `NOT NULL` na istniejącej kolumnie nakładaj sekwencją z walidacją osobno —
  CHECK `NOT VALID` waliduje się bez blokowania zapisów, a PostgreSQL 12+
  wykorzystuje go jako dowód przy `SET NOT NULL`:

```sql
ALTER TABLE orders ADD CONSTRAINT ck_orders_status_not_null
    CHECK (status IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT ck_orders_status_not_null;
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT ck_orders_status_not_null;
```

- Indeksy na bazie z ruchem twórz wyłącznie przez `CREATE INDEX CONCURRENTLY`
  (poza transakcją migracyjną); po niepowodzeniu pozostaje indeks `INVALID` —
  usuń go (`DROP INDEX CONCURRENTLY`) i ponów.
- Zmianę typu kolumny wymagającą przepisania, `DROP COLUMN` na gorącej tabeli
  i zmianę klucza głównego rozkładaj na wydania: nowa kolumna → podwójny zapis
  w aplikacji → migracja danych partiami → przełączenie odczytów → usunięcie
  starej kolumny w kolejnym wydaniu.
- Masowe `UPDATE`/`DELETE` dziel na partie (np. po 5–10 tys. wierszy
  z zatwierdzaniem między nimi) — jedna transakcja na miliony wierszy wstrzymuje
  odśmiecanie, rozdyma WAL i trzyma blokady wierszy do końca.

### SQLite — ograniczenia ALTER TABLE i przebudowa tabeli

- `ALTER TABLE` obsługuje wyłącznie `RENAME TO`, `RENAME COLUMN`, `ADD COLUMN`
  i `DROP COLUMN` (3.35+, z zastrzeżeniami). Zmiana typu, dodanie ograniczenia
  lub zmiana klucza wymaga przebudowy tabeli wzorcem dwunastu kroków
  z dokumentacji SQLite; rdzeń procedury:

```sql
PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;
CREATE TABLE orders_new ( /* docelowa definicja */ ) STRICT;
INSERT INTO orders_new (id, customer_id, status, created_at)
    SELECT id, customer_id, status, created_at FROM orders;
DROP TABLE orders;
ALTER TABLE orders_new RENAME TO orders;
-- odtwórz indeksy, wyzwalacze i widoki zależne
PRAGMA foreign_key_check;
COMMIT;
PRAGMA foreign_keys = ON;
```

  Krok notorycznie pomijany: odtworzenie wszystkich indeksów, wyzwalaczy
  i widoków starej tabeli (spisz je z `sqlite_schema`). `PRAGMA foreign_key_check`
  przed `COMMIT` jest obowiązkowy — `foreign_keys=OFF` wyłączył egzekwowanie.
- Przed każdą taką migracją wykonaj kopię (`.backup` albo `VACUUM INTO`) —
  jej przywrócenie jest najtańszą ścieżką wycofania. Migrację wykonuj przy
  wyłącznym dostępie do pliku, w krótkim oknie bez zapisów aplikacji.

## Spójność danych

- Ograniczenia w bazie to ostatnia linia obrony — walidacja w aplikacji ich nie
  zastępuje, bo do bazy piszą też migracje, skrypty naprawcze i przyszłe usługi.
  Reguła, której złamanie psuje dane trwale, musi być ograniczeniem.
- `CHECK` egzekwuje niezmienniki wiersza: `CHECK (total_amount >= 0)`,
  `CHECK (closed_at IS NULL OR closed_at >= created_at)`.
- Unikalność częściowa (indeks unikalny z `WHERE`, oba systemy) wyraża reguły
  typu „jeden aktywny rekord na klienta”:
  `CREATE UNIQUE INDEX uq_subscriptions_active ON subscriptions (customer_id)
  WHERE status = 'active';`
- Klucze obce zawsze z przemyślaną regułą `ON DELETE`: `RESTRICT` domyślnie
  (usunięcie rodzica z dziećmi ma być błędem jawnym), `CASCADE` wyłącznie dla
  danych ściśle podrzędnych (pozycje zamówienia), `SET NULL` dla powiązań
  opcjonalnych. W SQLite pamiętaj o `PRAGMA foreign_keys = ON` na każdym połączeniu.
- Przed nałożeniem nowego ograniczenia wykryj dane, które je naruszą:

```sql
-- kandydat na CHECK / NOT NULL:
SELECT count(*) FROM orders WHERE total_amount < 0 OR total_amount IS NULL;
-- kandydat na klucz obcy (wiersze osierocone):
SELECT o.id FROM orders o LEFT JOIN customers c ON c.id = o.customer_id
WHERE c.id IS NULL;
```

  Naruszenia napraw osobną migracją danych (decyzja właściciela danych,
  nie skryptu), dopiero potem nakładaj ograniczenie — w PostgreSQL dwuetapowo
  przez `NOT VALID` + `VALIDATE CONSTRAINT`.

## Awarie i diagnoza

### PostgreSQL — dziennik serwera i połączenia

- Skonfiguruj dziennik, zanim wystąpi awaria — diagnoza bez dziennika to zgadywanie:
  - `log_min_duration_statement = 500` (ms) — rejestr zapytań wolnych;
    `0` (wszystko) tylko chwilowo,
  - `log_lock_waits = on` — oczekiwania na blokady dłuższe niż `deadlock_timeout`,
  - `log_checkpoints = on` — checkpointy częstsze niż `checkpoint_timeout`
    wskazują na zbyt małe `max_wal_size`,
  - `log_autovacuum_min_duration = 0` — widoczność pracy autovacuum,
  - `log_line_prefix` z `%m %p %u %d %a`.
- Wyczerpanie połączeń (`FATAL: sorry, too many clients already`): przyczyną
  jest niemal zawsze aplikacja bez puli połączeń albo pule łącznie większe niż
  `max_connections`. Napraw architekturę, nie parametr: pula rzędu dziesiątek,
  przy wielu instancjach aplikacji — PgBouncer w trybie transaction pooling;
  `max_connections` ponad kilkaset maskuje problem i degraduje wydajność.
  Sesje `idle in transaction` w `pg_stat_activity` to wyciek transakcji w kodzie
  — napraw go i ustaw `idle_in_transaction_session_timeout` jako zabezpieczenie.

### SQLite — „database is locked” i kontrola spójności

- Błąd `database is locked` / `SQLITE_BUSY` diagnozuj drzewem przyczyn, w kolejności:
  1. brak `PRAGMA busy_timeout` — połączenie poddaje się natychmiast zamiast
     czekać; ustaw na każdym połączeniu,
  2. tryb rollback journal zamiast WAL — zapis blokuje czytelników i odwrotnie;
     włącz `PRAGMA journal_mode = WAL`,
  3. transakcja `BEGIN DEFERRED` eskalująca do zapisu — przegrywa wyścig
     o blokadę w środku transakcji (`busy_timeout` tego nie ratuje, transakcję
     trzeba ponowić); zapisy zaczynaj od `BEGIN IMMEDIATE`,
  4. długo otwarta transakcja (kursor nieodczytany do końca, zawieszony proces)
     — znajdź i domknij; to także przyczyna rosnącego `-wal`,
  5. plik na udziale sieciowym (NFS/SMB) — wadliwe blokady; przenieś na dysk lokalny,
  6. rywalizacja wielu procesów o zapis mimo poprawnej konfiguracji — granica
     architektury SQLite; migruj do PostgreSQL.
- `PRAGMA integrity_check` wykonuj w harmonogramie (np. tygodniowo;
  `PRAGMA quick_check` jako tańszy wariant częstszy). Wynik inny
  niż `ok` oznacza uszkodzenie: nie naprawiaj w miejscu — zabezpiecz plik,
  odtwórz bazę z ostatniej sprawnej kopii, lukę uzupełnij z dziennika aplikacji
  i przed powrotem do eksploatacji ustal przyczynę (dysk, udział sieciowy,
  kopiowanie pliku na żywo).

## Dostęp i granice bezpieczeństwa

- PostgreSQL — najmniejsze uprawnienia przez rozdział ról:
  - rola właścicielska (owner) obiektów: nie loguje się z aplikacji,
  - rola migracyjna: prawa DDL, używana wyłącznie przez proces migracji,
  - rola aplikacyjna: wyłącznie `SELECT/INSERT/UPDATE/DELETE` na potrzebnych
    tabelach i `USAGE` na sekwencjach — bez DDL i własności obiektów; aplikacja
    z prawami DDL zamienia wstrzyknięcie SQL w utratę schematu,
  - dla obiektów tworzonych przez migracje ustaw `ALTER DEFAULT PRIVILEGES
    FOR ROLE rola_migracyjna IN SCHEMA public GRANT ... TO rola_aplikacyjna;`
    — inaczej migracje zostawiają tabele bez uprawnień aplikacji,
  - odbierz prawa domyślne: `REVOKE ALL ON SCHEMA public FROM PUBLIC;`;
    w `pg_hba.conf` metoda `scram-sha-256` i zawężone zakresy adresów;
    poświadczenia w menedżerze sekretów, nigdy w repozytorium.
- SQLite — granicą bezpieczeństwa jest plik: proces z prawem odczytu czyta całą
  bazę, z prawem zapisu — modyfikuje ją dowolnie. Ustaw uprawnienia `0600`
  (lub `0640` dla wspólnej grupy) na pliku bazy i na katalogu (SQLite tworzy
  w nim pliki `-wal`, `-shm` i tymczasowe). Nie umieszczaj pliku bazy w katalogu
  serwowanym przez serwer WWW. Szyfrowanie spoczynkowe zapewnia system plików
  albo rozszerzenia (np. SQLCipher) — standardowy SQLite go nie ma.

## Obserwacja pojemności

- Mierz wzrost w czasie, nie stan chwilowy: raz na dobę zapisuj rozmiary
  największych obiektów i prognozuj trend z ostatnich tygodni; alarmuj przy
  prognozowanym przekroczeniu 70–80% miejsca — `VACUUM FULL` i `VACUUM` SQLite
  potrzebują przejściowo drugiego rozmiaru obiektu. PostgreSQL:

```sql
SELECT relname, pg_size_pretty(pg_table_size(c.oid)) AS table_size,
       pg_size_pretty(pg_indexes_size(c.oid)) AS index_size
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE relkind = 'r' AND n.nspname = 'public'
ORDER BY pg_total_relation_size(c.oid) DESC LIMIT 20;
```

  SQLite: rozmiar pliku bazy i pliku `-wal`; podział na tabele podaje
  `sqlite3_analyzer` albo rozszerzenie `dbstat`. Indeksy rosnące szybciej niż
  ich tabele to objaw wzdęcia (karta wydajnosc-pro.md).
- Dane zimne archiwizuj zamiast trzymać w tabelach operacyjnych: rosnące bez
  końca tabele zdarzeń wydłużają kopie, odtwarzanie, `ANALYZE` i migracje.
  Ustal na piśmie okres retencji, przenoś starsze dane do archiwum i usuwaj partiami.
- Partycjonowanie deklaratywne PostgreSQL (`PARTITION BY RANGE (created_at)`)
  stosuj, gdy zachodzi choć jedno: usuwanie danych okresami (odłączenie i `DROP`
  partycji zastępuje masowy `DELETE` z odśmiecaniem), tabela przerasta
  możliwości autovacuum i utrzymania indeksów (setki GB), zapytania niemal
  zawsze filtrują po kluczu partycjonowania. Partycjonowanie „na zapas” to
  czysty koszt: więcej obiektów, unikalność musi zawierać klucz partycjonowania,
  a zapytania bez filtra po nim odpytują wszystkie partycje. Partycje twórz
  z wyprzedzeniem automatem (np. `pg_partman`) — brak partycji na nowy okres to
  awaria zapisu. SQLite partycjonowania nie ma; potrzeba dzielenia danych na
  okresowe tabele lub pliki to sygnał, że przerosły SQLite.
