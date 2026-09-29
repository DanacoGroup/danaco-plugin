# Bazy danych — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Składnię
ogólną SQL i konwencje zapytań opisuje `references/jezyki-programowania/sql.md`; ten katalog
obejmuje pracę z konkretnymi systemami baz danych.

## Karty referencyjne

| System | Karta | Wczytaj gdy |
| --- | --- | --- |
| PostgreSQL | `references/bazy-danych/postgresql.md` | praca z bazą PostgreSQL: schematy, indeksy, EXPLAIN, blokady, role, kopie zapasowe |
| SQLite | `references/bazy-danych/sqlite.md` | praca z bazą plikową SQLite: tryb WAL, ograniczenia typów, współbieżność, osadzenie w aplikacji |
| oba systemy | `references/bazy-danych/wydajnosc-pro.md` | strojenie wydajności: analiza planów wykonania, projektowanie indeksów, przepisywanie wolnych zapytań, blokady i współbieżność, autovacuum i wzdęcie, monitoring pg_stat_statements |
| oba systemy | `references/bazy-danych/niezawodnosc-i-eksploatacja.md` | niezawodność: kopie zapasowe i test odtworzeniowy, migracje wysokiego ryzyka, ograniczenia spójności, diagnoza awarii („database is locked”, wyczerpanie połączeń), role i uprawnienia, pojemność i partycjonowanie |

Wczytaj kartę systemu, z którym prowadzona jest praca, przed wykonaniem pierwszej operacji na bazie.
Kartę `references/bazy-danych/wydajnosc-pro.md` wczytaj dodatkowo przy każdej diagnozie wolnego
zapytania lub projektowaniu indeksów; kartę `references/bazy-danych/niezawodnosc-i-eksploatacja.md`
— przy kopiach zapasowych, migracjach ryzykownych, awariach i planowaniu pojemności.

## Zasady nadrzędne dla obu systemów

1. **Schemat sprawdzaj w źródle.** Nazwy tabel i kolumn, typy oraz ograniczenia
   odczytuj z rzeczywistej bazy lub plików migracji — nigdy z pamięci ani z domysłu
   na podstawie nazw w kodzie aplikacji.
2. **Każda zmiana schematu przez migrację.** Zmiany wykonuj wyłącznie mechanizmem
   migracji przyjętym w projekcie (np. Alembic, node-pg-migrate, własne skrypty
   numerowane przez to narzędzie) — nigdy ręcznym poleceniem na żywej bazie bez
   zapisu w repozytorium. Migracja ma określoną ścieżkę wycofania.
3. **Zapytania parametryzowane, bez wyjątków.** Doklejanie wartości do tekstu SQL
   to podatność na wstrzyknięcie (CWE-89) — również w skryptach „tylko wewnętrznych”.
4. **Operacje wielokrokowe w transakcji.** Sekwencja zapisów, która ma sens tylko
   w całości, przebiega w jednej transakcji z określonym zachowaniem przy błędzie.
5. **Przed optymalizacją — pomiar.** Zapytanie przyspieszaj po obejrzeniu planu
   wykonania (`EXPLAIN`), nie na wyczucie; po zmianie przytocz plan lub czas „przed”
   i „po”.
6. **Dane produkcyjne to nie poligon.** Zapytania modyfikujące (`UPDATE`, `DELETE`)
   uruchamiaj najpierw jako `SELECT` z tym samym warunkiem `WHERE` i przytocz liczbę
   wierszy objętych zmianą; operacje nieodwracalne wymagają potwierdzenia właściciela
   projektu oraz aktualnej kopii zapasowej.
