# SQL — karta

Karta dotyczy SQL jako języka zdefiniowanego normą ISO/IEC 9075. Każdy system
implementuje normę częściowo i z rozszerzeniami — pisz zapytania możliwie blisko
normy, a odstępstwa dialektowe stosuj świadomie i tylko dla dialektu faktycznie
używanego w projekcie. Szczegóły operacyjne systemów PostgreSQL i SQLite
(konfiguracja, typy specyficzne, indeksowanie, plany wykonania) opisuje
`references/bazy-danych/bazy-danych.md` — tam sięgaj po wiedzę o konkretnym silniku;
ta karta dotyczy samego języka.

## Standard stylu i nazewnictwa

- Słowa kluczowe pisz wielkimi literami (`SELECT`, `LEFT JOIN`, `GROUP BY`),
  identyfikatory małymi literami w snake_case: `invoice_line`, `customer_id`.
- Nie cytuj identyfikatorów bez potrzeby; nazwy wymagające cudzysłowów (wielkość
  liter, spacje) to źródło błędów przenośności.
- Wypisuj kolumny jawnie; `SELECT *` dopuszczaj wyłącznie w zapytaniach doraźnych.
- Stosuj wyłącznie jawną składnię złączeń `JOIN ... ON`; nie używaj przecinkowej
  listy tabel z warunkiem w `WHERE`.
- Nadawaj aliasy krótkie, lecz znaczące (`inv`, `cust`), słowo `AS` stosuj
  konsekwentnie przy aliasach kolumn.
- Formatuj zapytania wielowierszowo: każda klauzula od nowego wiersza, warunki `ON`
  i `AND` wcięte pod swoją klauzulą.
- Rozbijaj złożone zapytania na CTE (`WITH`) o nazwach opisujących zawartość kroku;
  CTE zastępuje zagnieżdżone podzapytania i dokumentuje tok przekształceń.
- Stosuj funkcje okna zamiast samozłączeń tam, gdzie liczysz rangi, sumy narastające
  lub wartości sąsiednich wierszy.

```sql
-- Ostatnia faktura każdego klienta: funkcja okna zamiast samozlaczenia
WITH ranked_invoices AS (
    SELECT
        inv.customer_id,
        inv.invoice_id,
        inv.issued_at,
        ROW_NUMBER() OVER (
            PARTITION BY inv.customer_id
            ORDER BY inv.issued_at DESC, inv.invoice_id DESC
        ) AS rn
    FROM invoice AS inv
)
SELECT customer_id, invoice_id, issued_at
FROM ranked_invoices
WHERE rn = 1;
```

## Struktura projektu

- Trzymaj SQL w plikach `.sql`, nie w łańcuchach rozproszonych po kodzie aplikacji;
  zapytania wielokrotnego użytku nazywaj plikami po ich funkcji (`report_overdue.sql`).
- Oddzielaj DDL (schemat) od DML (dane) i od zapytań raportowych — różne katalogi,
  różny cykl zmian.
- Widoki i funkcje traktuj jak kod: definicje w repozytorium, zmiany przez migracje,
  nigdy ręcznie na działającej bazie.

## Budowa i zależności

- Zmiany schematu prowadź wyłącznie przez ponumerowane, niemodyfikowalne migracje
  (`migrations/0007_add_invoice_index.sql`); raz zastosowanej migracji nie edytuj —
  poprawki wprowadzaj kolejną migracją.
- Każda migracja ma być samodzielna i uruchamialna w transakcji, jeśli silnik na to
  pozwala; instrukcje pisz idempotentnie tam, gdzie dialekt to wspiera
  (`IF NOT EXISTS`), ale nie udawaj idempotencji składnią nieistniejącą w dialekcie.
- Definiuj migrację odwrotną (down) albo jawnie odnotuj jej brak przy operacjach
  nieodwracalnych (usunięcie kolumny z danymi).
- Zapytania osadzane w aplikacji parametryzuj zawsze (placeholdery sterownika);
  sklejanie SQL z danych wejściowych jest zakazane — to wektor SQL injection.

## Testy

- Testuj zapytania na małych, jawnie zbudowanych zestawach danych: fixture wstawiane
  w transakcji wycofywanej po teście (rollback) utrzymują testy niezależne.
- Pokrywaj przypadki brzegowe danych: brak wierszy, duplikaty kluczy biznesowych,
  wartości NULL w kolumnach złączeń i agregacji, wiersze na granicach zakresów dat.
- Dla migracji testuj pełny przebieg: świeża baza → wszystkie migracje → asercje na
  schemacie; przy migracji przekształcającej dane dodaj test na danych zastanych.
- Wyniki porównuj z uwzględnieniem porządku: bez `ORDER BY` porządek wierszy jest
  niezdefiniowany, więc test albo sortuje wynik, albo porównuje jako zbiór.
- Narzędzia testowe właściwe dla konkretnego silnika dobieraj według
  `references/bazy-danych/bazy-danych.md`.

## Diagnostyka

- Stosuj `EXPLAIN` jako pojęcie ogólne: każdy istotny silnik pokazuje plan wykonania
  zapytania (kolejność złączeń, użycie indeksów, szacunki liczności). Czytaj plan
  przed optymalizacją — nie zgaduj, dlaczego zapytanie jest wolne. Składnia i format
  wyniku są dialektowe (szczegóły w `references/bazy-danych/bazy-danych.md`).
- Diagnozuj złe wyniki przez dekompozycję: uruchamiaj CTE pojedynczo od góry
  i sprawdzaj liczności pośrednie (`SELECT COUNT(*)`); eksplozja wierszy po złączeniu
  oznacza zły lub niekompletny warunek `ON`.
- Czytaj komunikaty błędów dosłownie: błąd o kolumnie spoza `GROUP BY` lub
  o niezgodności typów wskazuje dokładne miejsce; nie obchodź go rzutowaniem na ślepo.
- Weryfikuj wpływ modyfikacji przed zatwierdzeniem: uruchom `SELECT` z tym samym
  `WHERE`, którego użyje `UPDATE`/`DELETE`, i sprawdź liczbę trafionych wierszy.

## Typowe błędy modeli LLM w tym języku

1. `SELECT *` w kodzie trwałym: łamie się przy zmianie schematu, pobiera zbędne dane
   i ukrywa zależności zapytania od kolumn. Wypisuj kolumny jawnie.
2. Porównania z NULL przez `=` lub `<>`: `col = NULL` nigdy nie jest prawdą — logika
   trójwartościowa daje UNKNOWN. Stosuj `IS NULL` / `IS NOT NULL`, a przy porównaniach
   „NULL-bezpiecznych” `IS DISTINCT FROM` (gdzie dialekt je wspiera).
3. Pomijanie skutków NULL poza porównaniami: `NOT IN` z podzapytaniem zawierającym
   NULL zwraca pusty wynik (preferuj `NOT EXISTS`), agregaty pomijają NULL,
   a `WHERE col <> 'x'` odrzuca także wiersze z NULL.
4. Przypisywanie funkcji niestandardowych złemu dialektowi: `IFNULL`, `GROUP_CONCAT`,
   `DATE_ADD` istnieją w jednych systemach, w innych odpowiadają im `COALESCE`,
   `STRING_AGG`/`LISTAGG`, arytmetyka interwałowa. Norma gwarantuje `COALESCE`,
   `NULLIF`, `CASE`; funkcje spoza normy weryfikuj dla dialektu projektu.
5. Konkatenacja łańcuchów operatorem `+` i cytowanie identyfikatorów odwrotnymi
   apostrofami w dialektach, które tego nie znają. Norma: konkatenacja `||`,
   identyfikatory w cudzysłowach `"`, literały tekstowe w apostrofach `'`.
6. Kolumny nieagregowane poza `GROUP BY`: niektóre silniki to tolerują (wybierając
   wiersz niedeterministycznie), inne odrzucają. Grupuj po wszystkich kolumnach
   nieagregowanych albo przenieś logikę do funkcji okna.
7. Użycie aliasu z `SELECT` lub funkcji okna w klauzuli `WHERE` — logiczna kolejność
   przetwarzania (`FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY`)
   na to nie pozwala. Owiń zapytanie w CTE lub podzapytanie i filtruj piętro wyżej.
8. `LIMIT`/`FETCH` bez pełnego, deterministycznego `ORDER BY`: wynik i stronicowanie
   stają się niepowtarzalne. Sortuj po kluczu jednoznacznym (dodaj kolumnę-tiebreaker).
9. Budowanie zapytań przez wstawianie wartości do tekstu SQL zamiast parametrów —
   ryzyko wstrzyknięcia i błędów cytowania. Wartości przekazuj placeholderami;
   w plikach przykładowych oznaczaj parametry jawnie.
10. Nadużywanie `DISTINCT` do maskowania zduplikowanych wierszy po złym złączeniu.
    Duplikaty po `JOIN` to objaw błędnego warunku `ON` lub złączenia z tabelą
    o innej ziarnistości — napraw przyczynę, nie tłum objawu.
