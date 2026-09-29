# Modelowanie danych

Schemat bazy przeżyje trzy przepisania warstwy aplikacyjnej. Błąd w kodzie poprawiasz
wdrożeniem; błąd w schemacie poprawiasz migracją na żywych danych, których część
już jest nieodwracalnie uszkodzona. Dlatego dane projektuje się wcześniej i staranniej
niż kod.

Przykłady w składni PostgreSQL 18.

## Model domenowy a schemat bazy

To dwie różne rzeczy o różnych celach i nie muszą być izomorficzne.

| | Model domenowy | Schemat bazy |
| --- | --- | --- |
| Cel | Wyrażać reguły i niezmienniki | Trwale przechowywać i szybko odpytywać |
| Optymalizuje | Czytelność reguły, niemożność stanu niepoprawnego | Rozmiar, indeksy, spójność referencyjną |
| Zmienia się, gdy | Zmienia się reguła biznesowa | Zmieniają się wzorce zapytań lub zakres danych |
| Reprezentacja | Typy sumaryczne, obiekty wartości, niezmienność | Tabele, kolumny, ograniczenia |

Klasyczna rozbieżność: w domenie `Platnosc` jest typem sumarycznym (`Karta | Przelew |
Gotowka`), w bazie to jedna tabela z kolumną `rodzaj` i kolumnami warunkowo `NULL`,
z ograniczeniem `CHECK` pilnującym spójności. Mapowanie żyje w repozytorium.

```sql
CREATE TABLE platnosci (
  id            uuid PRIMARY KEY DEFAULT uuidv7(),
  rodzaj        text NOT NULL CHECK (rodzaj IN ('karta','przelew','gotowka')),
  kwota_grosze  bigint NOT NULL CHECK (kwota_grosze > 0),
  waluta        char(3) NOT NULL,
  -- pola tylko dla karty
  karta_ostatnie4   char(4),
  karta_autoryzacja text,
  -- pola tylko dla przelewu
  przelew_iban      text,
  CONSTRAINT spojnosc_rodzaju CHECK (
    (rodzaj = 'karta'   AND karta_ostatnie4 IS NOT NULL AND przelew_iban IS NULL) OR
    (rodzaj = 'przelew' AND przelew_iban IS NOT NULL AND karta_ostatnie4 IS NULL) OR
    (rodzaj = 'gotowka' AND karta_ostatnie4 IS NULL AND przelew_iban IS NULL)
  )
);
```

Bez `CHECK spojnosc_rodzaju` po roku znajdziesz płatności kartą bez numeru karty
i przelewy z autoryzacją kartową. Baza jest ostatnią linią obrony niezmienników —
aplikacja ma błędy, migracje mają błędy, skrypty naprawcze mają błędy.

**Nie modeluj pod ekran.** Jeśli schemat zmienia się przy zmianie układu widoku,
modelujesz widok, nie domenę. Widok składasz zapytaniem albo widokiem materializowanym.

## Normalizacja i kiedy jej nie stosować

Domyślnie normalizuj do 3NF: każdy fakt zapisany w jednym miejscu. Denormalizacja jest
optymalizacją — a optymalizacja bez pomiaru to zgadywanie.

### Kiedy denormalizacja jest uzasadniona

| Przypadek | Co robisz | Dlaczego to nie jest błąd |
| --- | --- | --- |
| Dane historyczne dokumentu | Kopiujesz nazwę, adres, NIP i cenę do pozycji faktury | Faktura ma odzwierciedlać stan z dnia wystawienia. Zmiana adresu klienta **nie może** zmienić wystawionej faktury |
| Licznik odczytywany bardzo często | `zgloszenia.liczba_wiadomosci` aktualizowana wyzwalaczem | `COUNT(*)` przy każdym wyświetleniu listy to N+1 na poziomie SQL |
| Zmaterializowany raport | Widok materializowany odświeżany co godzinę | Agregacja po milionach wierszy nie należy do ścieżki żądania |
| Dane zmienne per klient | Kolumna `JSONB` z indeksem GIN | Alternatywa (EAV) jest gorsza pod każdym względem |

Kryterium rozstrzygające: **czy skopiowana wartość ma pozostać niezmieniona, gdy
zmieni się źródło?** Jeśli tak — to nie denormalizacja, to poprawne modelowanie faktu
historycznego. Jeśli nie — to cache, który się rozjedzie, i potrzebujesz mechanizmu
odświeżania.

### Czego nie robić nigdy

| Antywzorzec | Objaw | Konsekwencja |
| --- | --- | --- |
| EAV (encja-atrybut-wartość) | Tabela `atrybuty(encja_id, nazwa, wartosc text)` | Brak typów, brak ograniczeń, każde zapytanie to seria `JOIN`-ów, plan zapytania nie do przewidzenia |
| Lista w kolumnie tekstowej | `tagi text` z wartością `'pilne,vip,reklamacja'` | Brak indeksowania, brak spójności, `LIKE '%vip%'` łapie `'vip-plus'` |
| Kolumny `pole1`..`pole10` | Rezerwa „na przyszłość” | Po roku `pole3` znaczy co innego dla dwóch klientów |
| Klucz naturalny zmienny jako PK | PESEL, NIP, e-mail jako `PRIMARY KEY` | Zmiana wartości kaskaduje po całej bazie; NIP bywa błędnie wprowadzony |
| Jedna tabela na wszystko z kolumną `typ` | `dokumenty(typ, pole_a, pole_b, ... )`, 60 kolumn, 80% `NULL` | Brak możliwości sensownych ograniczeń |

`JSONB` jest dopuszczalny dla danych, których kształtu **naprawdę** nie znasz z góry
(pola definiowane przez klienta, ładunek webhooka do audytu). Nie jest dopuszczalny
jako ucieczka od projektowania schematu. Test: czy piszesz zapytanie filtrujące po
tym polu? Jeśli tak — to jest kolumna, nie JSON.

## Klucze

### Klucz główny

| Wybór | Kiedy | Uwagi |
| --- | --- | --- |
| **UUIDv7** (`uuidv7()`, PG 18) | Domyślnie | Sortowalny czasowo → wstawianie nie fragmentuje indeksu B-tree jak UUIDv4; da się generować w aplikacji przed zapisem; nie ujawnia liczby rekordów |
| `BIGINT GENERATED ALWAYS AS IDENTITY` | Tabele czysto wewnętrzne, bardzo duże | 8 bajtów zamiast 16; ale wymaga rundy do bazy przed poznaniem id i ujawnia wolumen w URL-ach |
| Klucz naturalny | Prawie nigdy | Tylko gdy wartość jest niezmienna z definicji (kod kraju ISO, kod waluty) |
| Klucz złożony | Tabele łączące relację wiele-do-wielu | `PRIMARY KEY (zgloszenie_id, tag_id)` jest poprawne |

UUIDv4 jako klucz główny dużej tabeli to konkretny koszt: losowe wartości powodują
rozpraszanie zapisów po całym indeksie, rozszczepianie stron i puchnięcie indeksu.
UUIDv7 ma znacznik czasu na początku, więc kolejne wstawienia trafiają w tę samą część
indeksu. Przy tabelach powyżej kilku milionów wierszy różnica jest wyraźna.

Uwaga prywatności: UUIDv7 **ujawnia czas utworzenia** rekordu z dokładnością do
milisekund. Gdy to jest problemem (identyfikatory publiczne w systemie medycznym),
użyj osobnego identyfikatora publicznego generowanego losowo.

Wzorzec dwóch identyfikatorów, gdy potrzebujesz krótkiego identyfikatora dla ludzi:

```sql
CREATE TABLE zgloszenia (
  id            uuid PRIMARY KEY DEFAULT uuidv7(),   -- klucz techniczny, w relacjach
  numer         text UNIQUE NOT NULL,                 -- 'ZGL-2026-00412', dla ludzi
  ...
);
```

Nigdy nie używaj numeru czytelnego dla człowieka jako klucza obcego — te numery mają
zwyczaj zmieniać reguły numeracji na przełomie roku.

### Klucze obce

Zawsze deklaruj `FOREIGN KEY`. Argument „ograniczenia spowalniają” jest fałszywy przy
tej skali, a osierocone wiersze zawsze się pojawiają, gdy ich nie ma.

```sql
klient_id uuid NOT NULL REFERENCES klienci(id) ON DELETE RESTRICT
```

| Akcja | Kiedy |
| --- | --- |
| `ON DELETE RESTRICT` | Domyślnie. Usunięcie rodzica z istniejącymi dziećmi to błąd biznesowy, nie techniczny |
| `ON DELETE CASCADE` | Tylko dla danych całkowicie podrzędnych, bez wartości samodzielnej (pozycje dokumentu, załączniki) |
| `ON DELETE SET NULL` | Gdy relacja jest opcjonalna i utrata powiązania jest akceptowalna (`przypisany_do`) |

**Postgres nie indeksuje kluczy obcych automatycznie.** Brak indeksu na kolumnie FK
oznacza skan całej tabeli podrzędnej przy każdym usunięciu rodzica oraz wolne `JOIN`-y.
Zakładaj indeks ręcznie:

```sql
CREATE INDEX ix_zgloszenia_klient ON zgloszenia (klient_id);
```

### Klucze naturalne jako ograniczenia unikalności

Nie jako PK, ale jako `UNIQUE` — tak. Unikalność e-maila powinna być pilnowana przez
bazę, nie przez `SELECT ... IF NOT EXISTS` w aplikacji (który ma warunek wyścigu).

```sql
-- unikalność bez rozróżniania wielkości liter, tylko dla kont aktywnych
CREATE UNIQUE INDEX ux_uzytkownicy_email ON uzytkownicy (lower(email))
  WHERE dezaktywowano IS NULL;
```

## Czas

Trzy reguły, których naruszenie generuje błędy niewykrywalne w testach:

1. **W bazie zawsze `TIMESTAMPTZ`, nigdy `TIMESTAMP`.** `TIMESTAMP` nie przechowuje
   strefy i przy zmianie strefy serwera cała historia zmienia znaczenie. `TIMESTAMPTZ`
   w Postgresie przechowuje moment w UTC i konwertuje przy odczycie.
2. **Konwersja na strefę lokalną wyłącznie na brzegu prezentacji.** Domena i aplikacja
   operują na momentach, nie na „godzinie 14:00”.
3. **Gdy strefa ma znaczenie biznesowe, zapisz ją osobno.** „Spotkanie o 9:00 czasu
   warszawskiego” to moment + identyfikator strefy IANA, bo reguły czasu letniego mogą
   się zmienić między zapisem a wystąpieniem zdarzenia.

```sql
CREATE TABLE spotkania (
  id           uuid PRIMARY KEY DEFAULT uuidv7(),
  rozpoczyna   timestamptz NOT NULL,
  strefa       text NOT NULL DEFAULT 'Europe/Warsaw',  -- IANA, nie 'CET'
  czas_trwania interval NOT NULL
);
```

Nigdy nie zapisuj skrótów typu `CET`/`CEST` — są niejednoznaczne i nie kodują reguł
przejścia. Zawsze identyfikator IANA (`Europe/Warsaw`).

### Zakresy czasowe

Okresy obowiązywania (umowa, cennik, przypisanie) modeluj **domknięto-otwarto**
`[od, do)`. Rozwiązuje to problem „czy koniec należy do okresu” i eliminuje szczeliny.

Postgres ma typ zakresowy i ograniczenie wykluczające, które uniemożliwia nakładanie
się okresów — to reguła nie do zapisania zwykłym `CHECK`:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE cenniki (
  id           uuid PRIMARY KEY DEFAULT uuidv7(),
  klient_id    uuid NOT NULL REFERENCES klienci(id),
  obowiazuje   tstzrange NOT NULL,
  stawka_grosze bigint NOT NULL CHECK (stawka_grosze >= 0),
  EXCLUDE USING gist (klient_id WITH =, obowiazuje WITH &&)
);

INSERT INTO cenniki (klient_id, obowiazuje, stawka_grosze)
VALUES ('...', tstzrange('2026-01-01', '2026-07-01', '[)'), 15000);
```

Próba wstawienia nakładającego się okresu dla tego samego klienta zakończy się błędem
bazy, a nie cichym rozjazdem rozliczeń.

### Częste pułapki czasowe

| Pułapka | Co się psuje |
| --- | --- |
| Doba jako 24 h w arytmetyce | Przy zmianie czasu doba ma 23 lub 25 godzin. Użyj `interval '1 day'` z `AT TIME ZONE`, nie `+ 86400` |
| „Ostatni dzień miesiąca” jako `+30 dni` | Luty. Użyj `date_trunc` i `interval '1 month'` |
| Porównanie dat po stronie aplikacji z konwersją stref | Rozjazd o godzinę na granicy doby. Filtruj w SQL |
| Data urodzenia jako `TIMESTAMPTZ` | Data urodzenia to `DATE` — nie ma momentu ani strefy |
| Godzina otwarcia sklepu jako `TIMESTAMPTZ` | To `TIME` plus strefa lokalizacji |

## Pieniądze

**Nigdy `FLOAT`, `REAL`, `DOUBLE PRECISION`.** `0.1 + 0.2 != 0.3` w arytmetyce
zmiennoprzecinkowej. Po tysiącu operacji saldo rozjeżdża się o groszy kilka, a
uzgodnienie z księgowością staje się niemożliwe.

Dwa dopuszczalne warianty:

| Wariant | Typ | Kiedy |
| --- | --- | --- |
| Liczba całkowita w najmniejszej jednostce | `BIGINT` (grosze) | Domyślnie. Prosto, szybko, bez zaokrągleń |
| Dziesiętny stałoprzecinkowy | `NUMERIC(19,4)` | Gdy potrzeba więcej niż 2 miejsc (ceny jednostkowe, kursy, stawki godzinowe) |

`BIGINT` w groszach: 9,2 · 10^18 groszy to 92 biliardy złotych — zapas wystarczający.

**Waluta zawsze obok kwoty.** Kolumna `waluta char(3)` z kodem ISO 4217. Kwota bez
waluty to liczba, nie pieniądz.

```sql
CREATE TABLE pozycje_faktury (
  id              uuid PRIMARY KEY DEFAULT uuidv7(),
  faktura_id      uuid NOT NULL REFERENCES faktury(id) ON DELETE CASCADE,
  opis            text NOT NULL,
  ilosc           numeric(12,4) NOT NULL CHECK (ilosc > 0),
  cena_jedn       numeric(19,4) NOT NULL CHECK (cena_jedn >= 0),
  waluta          char(3) NOT NULL,
  stawka_vat      numeric(5,4) NOT NULL,      -- 0.2300 dla 23%
  netto_grosze    bigint NOT NULL,            -- policzone i zapisane
  vat_grosze      bigint NOT NULL,
  brutto_grosze   bigint NOT NULL,
  CONSTRAINT suma_sie_zgadza CHECK (brutto_grosze = netto_grosze + vat_grosze)
);
```

Kwoty wynikowe **zapisujesz**, a nie liczysz przy każdym odczycie. Powód: reguła
zaokrąglania może się zmienić, a wystawiona faktura nie może zmienić kwoty. `CHECK`
pilnuje, żeby zapisane wartości były wewnętrznie spójne.

### Zaokrąglanie

Ustal jedną regułę i zapisz ją w ADR: gdzie zaokrąglasz (na pozycji czy na sumie),
w którą stronę (bankierskie czy pół w górę), do ilu miejsc. Rozbieżność między
aplikacją a systemem księgowym o 1 grosz na fakturze generuje więcej pracy niż
cały moduł rozliczeń.

W kodzie: nigdy typ zmiennoprzecinkowy w drodze. TypeScript — biblioteka dziesiętna
albo `bigint`. Python — `decimal.Decimal` z jawnym `getcontext().prec`, nigdy `float`.

## Usuwanie danych

Model domyślnie sięga po miękkie usuwanie (`deleted_at`) i to jest zwykle błąd.

### Koszty miękkiego usuwania

- **Każde zapytanie w systemie** musi pamiętać o `WHERE usunieto IS NULL`. Jedno
  zapomnienie i usunięte dane wracają na ekran.
- Ograniczenia `UNIQUE` przestają działać zgodnie z intuicją: nie da się utworzyć
  nowego rekordu z tym samym e-mailem, bo stary „usunięty” blokuje. Wymaga indeksu
  częściowego.
- Klucze obce wskazują na rekordy usunięte — spójność referencyjna nic nie mówi.
- RODO: „usunięte” dane osobowe nadal są w bazie i w kopiach zapasowych.

### Kiedy co stosować

| Potrzeba | Rozwiązanie |
| --- | --- |
| Rekord jest pomyłką, ma zniknąć | `DELETE`. Twarde |
| Trzeba wiedzieć, że i kiedy usunięto | `DELETE` + wpis w tabeli audytu |
| Funkcja „kosz” z możliwością przywrócenia przez 30 dni | Osobna tabela `X_usuniete` + zadanie czyszczące. Nie flaga |
| Rekord przestał być aktywny, ale historia go używa | To nie usunięcie, to **stan**: `status = 'archiwalny'`, `dezaktywowano timestamptz` |
| Wymóg prawny odtworzenia stanu na dowolny moment | Model zdarzeniowy (append-only), nie flaga |
| RODO — żądanie usunięcia danych | Anonimizacja: nadpisanie danych osobowych, zachowanie rekordu rozliczeniowego |

Rozróżnienie kluczowe: **„usunięte” a „nieaktywne” to różne rzeczy.** Klient, który
zakończył współpracę, nie jest usunięty — jego faktury dalej istnieją i muszą wskazywać
na niego. To stan `archiwalny`, filtrowany w miejscach, gdzie wybiera się aktywnych.

Anonimizacja pod RODO z zachowaniem spójności:

```sql
UPDATE uzytkownicy SET
  email       = 'usuniety+' || id::text || '@invalid',
  imie        = 'Usunięty',
  nazwisko    = 'Użytkownik',
  telefon     = NULL,
  zanonimizowano = now()
WHERE id = $1;
```

Rekord zostaje, klucze obce działają, faktury zachowują spójność, dane osobowe znikają.

## Audyt zmian

Trzy poziomy — wybierz najniższy, który spełnia wymóg. Każdy wyższy kosztuje.

### Poziom 1: kolumny znacznikowe

```sql
utworzono     timestamptz NOT NULL DEFAULT now(),
utworzyl      uuid REFERENCES uzytkownicy(id),
zmodyfikowano timestamptz NOT NULL DEFAULT now(),
zmodyfikowal  uuid REFERENCES uzytkownicy(id)
```

Daje: kto i kiedy ostatnio dotknął. Nie daje: co zmienił, ile razy, jak było wcześniej.
Wystarcza dla większości danych.

### Poziom 2: tabela audytu

```sql
CREATE TABLE audyt (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tabela      text NOT NULL,
  rekord_id   uuid NOT NULL,
  operacja    text NOT NULL CHECK (operacja IN ('INSERT','UPDATE','DELETE')),
  przed       jsonb,
  po          jsonb,
  aktor_id    uuid,
  kiedy       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_audyt_rekord ON audyt (tabela, rekord_id, kiedy DESC);
```

Wypełniany wyzwalaczem (`to_jsonb(OLD)`, `to_jsonb(NEW)`) albo jawnie w repozytorium.
Wyzwalacz jest pewniejszy — łapie też zmiany ze skryptów naprawczych — ale nie zna
identyfikatora aktora bez ustawienia zmiennej sesyjnej.

Uwaga: `przed`/`po` w `JSONB` zawierają dane osobowe i hasła. Odfiltruj wrażliwe
kolumny w wyzwalaczu, inaczej tabela audytu staje się największym ryzykiem RODO.

### Poziom 3: model zdarzeniowy

Stan wynika ze strumienia niemutowalnych zdarzeń; nie ma `UPDATE`. Daje pełną historię
i możliwość odtworzenia stanu na dowolny moment.

Koszt: każde zapytanie odczytowe wymaga projekcji; zmiana kształtu zdarzenia wymaga
wersjonowania; nie da się poprawić błędnego zdarzenia inaczej niż zdarzeniem
kompensującym. Stosuj **wyłącznie** wtedy, gdy historia jest wymaganiem biznesowym
(księgowość, rejestry medyczne, rejestry prawne), nigdy „bo elastyczne”.

Wariant pośredni, wystarczający zaskakująco często: **główna encja mutowalna + tabela
zdarzeń append-only** dla tej jednej encji, która tego wymaga.

## Migracje bez przestoju

Zasada: **każda migracja musi być zgodna z aplikacją w wersji poprzedniej i następnej
jednocześnie.** Wdrożenie kroczące oznacza, że przez pewien czas działają obie wersje.

### Zmiany bezpieczne (jeden krok)

- Dodanie tabeli.
- Dodanie kolumny `NULL` bez wartości domyślnej.
- Dodanie kolumny `NOT NULL DEFAULT` — od PG 11 nie przepisuje tabeli.
- Dodanie indeksu z `CREATE INDEX CONCURRENTLY` (bez blokady zapisu).
- Rozszerzenie typu (`varchar(50)` → `text`).

### Zmiany wymagające wielu wdrożeń

**Usunięcie kolumny** — trzy wdrożenia:

1. Wdrożenie kodu, który **nie czyta i nie pisze** do kolumny.
2. Odczekanie (co najmniej jeden cykl wdrożenia, żeby dało się wycofać).
3. `ALTER TABLE ... DROP COLUMN`.

Kolejność odwrotna (najpierw `DROP`) kładzie starą wersję aplikacji, która jeszcze
działa na innych instancjach.

**Zmiana nazwy kolumny** — nigdy `RENAME` na żywej tabeli. Wzorzec rozszerz–migruj–zwęź:

```sql
-- Krok 1: dodaj nową kolumnę
ALTER TABLE zgloszenia ADD COLUMN priorytet_num smallint;

-- Krok 2: kod pisze do OBU kolumn, czyta ze starej
-- Krok 3: przepisz dane porcjami (nie jednym UPDATE na 10 mln wierszy)
UPDATE zgloszenia SET priorytet_num = CASE priorytet
  WHEN 'niski' THEN 1 WHEN 'sredni' THEN 2 WHEN 'wysoki' THEN 3 END
WHERE priorytet_num IS NULL AND id IN (
  SELECT id FROM zgloszenia WHERE priorytet_num IS NULL LIMIT 10000
);
-- powtarzaj aż 0 wierszy

-- Krok 4: kod czyta z nowej, pisze do obu
-- Krok 5: kod czyta i pisze tylko do nowej
-- Krok 6: ALTER TABLE zgloszenia DROP COLUMN priorytet;
```

Sześć kroków wygląda na przesadę, ale jest to jedyny sposób bez przestoju na tabeli,
do której ktoś pisze.

**Dodanie `NOT NULL` do istniejącej kolumny**:

```sql
-- 1. Ograniczenie niewalidowane — nie skanuje tabeli, nie blokuje
ALTER TABLE zgloszenia ADD CONSTRAINT zgloszenia_opis_nn
  CHECK (opis IS NOT NULL) NOT VALID;
-- 2. Uzupełnij braki porcjami
-- 3. Walidacja bierze słabszą blokadę niż SET NOT NULL
ALTER TABLE zgloszenia VALIDATE CONSTRAINT zgloszenia_opis_nn;
```

**Dodanie klucza obcego do dużej tabeli** — ten sam wzorzec: `NOT VALID`, potem
`VALIDATE CONSTRAINT`.

### Reguły operacyjne migracji

| Reguła | Powód |
| --- | --- |
| Migracja jest w repozytorium, wersjonowana, uruchamiana przez narzędzie | Ręczny `ALTER` na produkcji nie istnieje w historii i nie odtworzy się na środowisku testowym |
| Migracja ma odwrócenie albo jawne „nieodwracalna” | Nieodwracalne wdrożenie wymaga innej procedury (kopia, okno serwisowe) |
| `CREATE INDEX` na produkcji zawsze `CONCURRENTLY` | Zwykłe `CREATE INDEX` blokuje zapisy na czas budowy — minuty przy dużej tabeli |
| `ALTER TABLE` z `lock_timeout` | Bez limitu migracja czeka na blokadę i ustawia za sobą kolejkę wszystkich zapytań |
| Migracja danych osobno od migracji schematu | Zmiana schematu ma być szybka; przepisanie 10 mln wierszy trwa |
| Test migracji na kopii produkcji | Migracja działająca na 100 wierszach potrafi trwać 40 minut na 10 mln |

```sql
SET lock_timeout = '3s';
ALTER TABLE zgloszenia ADD COLUMN nowa_kolumna text;
```

Jeśli nie uda się wziąć blokady w 3 sekundy, migracja się przerywa — lepiej powtórzyć
niż zablokować aplikację na 10 minut.

## Lista kontrolna schematu

- [ ] Każda tabela ma klucz główny (UUIDv7 domyślnie).
- [ ] Każdy klucz obcy zadeklarowany i **zaindeksowany**.
- [ ] Kwoty jako `BIGINT` w groszach lub `NUMERIC(19,4)` — zero typów zmiennoprzecinkowych.
- [ ] Każda kwota ma obok siebie walutę.
- [ ] Wszystkie momenty jako `TIMESTAMPTZ`; daty bez czasu jako `DATE`.
- [ ] Strefy jako identyfikatory IANA tam, gdzie mają znaczenie biznesowe.
- [ ] Niezmienniki, które da się wyrazić w `CHECK`, są w `CHECK`.
- [ ] Unikalność pilnowana przez indeks unikalny, nie przez kod aplikacji.
- [ ] Okresy obowiązywania jako `[od, do)` z `EXCLUDE` przeciw nakładaniu.
- [ ] `NOT NULL` wszędzie, gdzie brak wartości nie ma sensu (domyślnie: wszędzie).
- [ ] Świadoma decyzja o usuwaniu (twarde/stan/anonimizacja), nie odruchowe `deleted_at`.
- [ ] Poziom audytu dobrany do wymogu, nie maksymalny.
- [ ] Każda migracja przetestowana na kopii wielkości produkcyjnej.
- [ ] Dane wrażliwe nie trafiają do tabeli audytu ani do logów.
