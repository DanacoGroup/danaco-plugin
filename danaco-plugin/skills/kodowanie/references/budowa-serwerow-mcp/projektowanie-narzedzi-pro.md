# Projektowanie zestawu narzędzi MCP — karta

Karta rozwija zasady projektowe `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md` do poziomu,
na którym projektuje się zestawy narzędzi dla systemów produkcyjnych. Zasada nadrzędna:
użytkownikiem interfejsu MCP jest model LLM. Projektuj więc pod jego mechanikę — ograniczone okno
kontekstu, dobór narzędzia na podstawie opisu, uczenie się z komunikatów błędów — a nie pod estetykę
API dla programisty.

## 1. Budżet kontekstu jako kryterium projektowe

Każdy element zestawu narzędzi zjada okno kontekstu modelu dwukrotnie:

- **na wejściu** — opisy wszystkich narzędzi i ich schematy trafiają do kontekstu
  przy każdej rozmowie, niezależnie od tego, czy narzędzie zostanie użyte;
- **na wyjściu** — każda odpowiedź narzędzia zostaje w kontekście do końca rozmowy
  i konkuruje o miejsce z treścią zadania użytkownika.

Traktuj więc znaki jak budżet i rozliczaj z niego każdą decyzję projektową.

### Projektowanie odpowiedzi narzędzia

1. **Zwracaj pola niezbędne, nie rekord źródłowy.** Odpowiedź API usługi zewnętrznej
   zawiera zwykle kilkadziesiąt pól — znaczniki wewnętrzne, adresy HATEOAS, metadane
   replikacji. Model potrzebuje najczęściej pięciu. Zdefiniuj jawny model wyjścia
   (Pydantic/zod) i mapuj na niego odpowiedź źródłową; wszystko, co nie przechodzi
   przez model wyjścia, nie istnieje dla modelu LLM.
2. **Zawsze zwracaj identyfikatory do dalszych wywołań.** Wynik wyszukiwania bez
   identyfikatora rekordu jest ślepą uliczką — model widzi obiekt, ale nie może go
   pobrać, zaktualizować ani powiązać. Każdy element listy: identyfikator + pola
   pozwalające go rozpoznać (nazwa, data, status).
3. **Streszczenia zamiast surowych rekordów w wynikach zbiorczych.** Narzędzie
   listujące zwraca skrót rekordu (identyfikator, tytuł, jedno–dwa pola
   rozstrzygające); pełny rekord zwraca dopiero narzędzie `get_...` po
   identyfikatorze. To dwustopniowy wzorzec „lista → szczegół” — standard każdego
   zestawu pro.
4. **Limity i stronicowanie kursorem.** Każde narzędzie zwracające listę ma parametr
   `limit` z rozsądną wartością domyślną (10–25) i twardym maksimum po stronie
   serwera. Stronicuj kursorem: odpowiedź zawiera `next_cursor` (nieprzezroczysty
   token) albo `null`, gdy wyników nie ma więcej; kolejne wywołanie przekazuje
   kursor bez zmian. Kursor jest odporniejszy od `offset` na zmiany danych między
   wywołaniami i nie kusi modelu do arytmetyki stron.
5. **Sygnalizuj obcięcie jawnie.** Gdy wynik został przycięty, powiedz to w
   odpowiedzi: `"zwrócono 25 z 214 wyników; przekaż cursor, aby pobrać kolejne,
   albo zawęź filtr date_from"`. Model, który nie wie o obcięciu, wyciąga wnioski
   z danych niepełnych.

### Praktyczna miara

Przed zatwierdzeniem zestawu policz: (a) łączną objętość opisów narzędzi
i schematów, (b) objętość typowej odpowiedzi każdego narzędzia przy danych
rzeczywistych. Jeśli pojedyncza odpowiedź listy przekracza kilka tysięcy znaków —
przytnij pola albo obniż limit domyślny. Jeśli same opisy zestawu idą w dziesiątki
tysięcy znaków — zestaw jest za szeroki albo opisy za rozwlekłe.

## 2. Przestrzeń nazw zestawu

Zestaw narzędzi to jeden spójny język, którym serwer mówi do modelu. Utrzymuj go
jak API publiczne.

1. **Przedrostek domenowy**, gdy klient może mieć podłączonych wiele serwerów
   albo serwer obsługuje kilka domen: `crm_search_customers`, `mail_send_message`,
   `billing_get_invoice`. Przedrostek grupuje narzędzia wizualnie w kontekście
   modelu i zapobiega kolizjom nazw między serwerami.
2. **Spójna siatka czasowników.** Ustal słownik i stosuj go bez wyjątków:
   - `search_` — wyszukiwanie po kryteriach, zwraca listę streszczeń z kursorami;
   - `get_` — pobranie jednego rekordu po identyfikatorze, zwraca pełny obiekt;
   - `list_` — wyliczenie elementów podrzędnych lub słownikowych (np. statusów),
     zawsze z limitem;
   - `create_` / `update_` / `delete_` — operacje zapisu, każda z osobna, nigdy
     złączone w jedno „upsert-kombajn” bez wyraźnej potrzeby.
3. **Zakaz synonimów.** Jedno pojęcie — jedna nazwa w całym zestawie. Jeżeli raz
   piszesz `customer`, nie pisz nigdzie `client` ani `account` na to samo. Jeżeli
   czasownikiem wyszukiwania jest `search_`, nie wprowadzaj `find_` ani `query_`.
   Synonim to dla modelu dwa różne byty — będzie zgadywał, czym się różnią.
4. **Ta sama siatka w nazwach parametrów.** `customer_id` wszędzie, nie raz
   `customer_id`, raz `id_klienta`, raz `cust`. Pola dat: `date_from`/`date_to`
   w całym zestawie.

## 3. Opisy narzędzi jako instrukcje decyzyjne

Opis narzędzia to jedyna dokumentacja, jaką model czyta przed wyborem. Pisz go
jako instrukcję decyzyjną według stałego wzorca:

1. **Co robi** — jedno zdanie oznajmujące, konkretne.
2. **Kiedy użyć** — typowe sytuacje wyzwalające, językiem zadań użytkownika.
3. **Kiedy NIE użyć** — odgraniczenie od narzędzi sąsiednich; wskaż narzędzie
   właściwe („do pobrania pełnych danych klienta użyj `get_customer`”).
4. **Co zwraca** — kształt wyniku: pola, limit domyślny, obecność kursora.
5. **Ograniczenia** — zakres danych (np. „obejmuje wyłącznie faktury z ostatnich
   24 miesięcy”), koszty, wymagane uprawnienia.

### Para opis słaby → mocny

Słaby:

> `search_invoices` — wyszukuje faktury.

Mocny:

> `search_invoices` — wyszukuje faktury po numerze, kontrahencie, statusie
> płatności lub zakresie dat wystawienia. Użyj, gdy użytkownik pyta o faktury,
> zaległości albo płatności, a nie zna numeru konkretnej faktury. NIE używaj do
> pobrania pełnej treści znanej faktury — do tego służy `get_invoice`. Zwraca do
> 20 streszczeń (invoice_id, numer, kontrahent, kwota brutto, status, termin
> płatności) oraz next_cursor, gdy wyników jest więcej. Obejmuje wyłącznie
> faktury sprzedażowe; faktur zakupowych dotyczy `search_purchase_invoices`.

Druga para — operacja zapisu. Słaby:

> `update_case` — aktualizuje sprawę.

Mocny:

> `update_case` — zmienia wybrane pola istniejącej sprawy (status, przypisanego
> opiekuna, priorytet). Użyj po potwierdzeniu zmiany przez użytkownika. NIE
> używaj do dodania notatki — do tego służy `create_case_note`. Przekazuj tylko
> pola zmieniane; pola pominięte pozostają bez zmian. Z parametrem dry_run=true
> zwraca opis planowanej zmiany bez zapisu. Zwraca sprawę po zmianie
> (case_id, status, opiekun, priorytet, data modyfikacji).

Opis mocny jest dłuższy — i to jest wydatek z budżetu kontekstu poniesiony
świadomie: dobry opis zwraca się mniejszą liczbą błędnych wywołań.

## 4. Projektowanie parametrów

1. **Enumy zamiast wolnego tekstu wszędzie, gdzie dziedzina jest zamknięta.**
   Parametr `status` jako enum `["draft", "sent", "paid", "overdue", "cancelled"]`
   zamiast `string` — schemat sam koryguje halucynacje wartości. Wolny tekst
   zostaw wyłącznie tam, gdzie treść jest naprawdę otwarta (frazy wyszukiwania,
   treści notatek).
2. **Wartości domyślne przemyślane, nie przypadkowe.** Domyślny `limit` mały,
   domyślne sortowanie od najnowszych, domyślny zakres dat zawężony (np. 90 dni)
   z jawną informacją w opisie — model rzadko ustawia parametry opcjonalne,
   więc wartości domyślne wyznaczają zachowanie faktyczne narzędzia.
3. **Formaty jawne i jednolite.** Daty i czasy wyłącznie ISO 8601
   (`2026-08-16`, `2026-08-16T14:30:00Z`) — zapisz format w opisie parametru.
   Kwoty z jawną walutą i jednostką (grosze czy złote — rozstrzygnij i opisz).
   Identyfikatory jako łańcuchy, nawet gdy źródłowo są liczbami — unikniesz
   utraty precyzji i mieszania typów.
4. **`dry_run` dla operacji zapisu.** Każde narzędzie tworzące, zmieniające lub
   usuwające dane przyjmuje `dry_run: bool = false`; przy `true` serwer waliduje
   wejście i zwraca opis skutków („zostanie usuniętych requestów: 3, w tym…”)
   bez wykonania. To tani mechanizm bezpieczeństwa i naturalny krok
   „pokaż, co zrobisz” przed potwierdzeniem użytkownika.
5. **Mało parametrów wymaganych.** Każdy parametr wymagany to punkt, w którym
   model może wstawić wartość zmyśloną, byle przejść walidację. Wymagaj tylko
   tego, bez czego operacja nie ma sensu.

## 5. Komunikaty błędów uczące model

Błąd narzędzia to nie wyjątek do zalogowania — to odpowiedź, z której model ma
wywnioskować następny krok. Projektuj komunikaty według reguły: **stan → przyczyna
→ następny krok**.

- Brak rekordu: `"Nie znaleziono klienta o identyfikatorze CUST-118. Identyfikator
  mógł być zgadnięty — użyj search_customers z nazwą lub NIP-em, aby znaleźć
  właściwy."`
- Przekroczony limit wyników: `"Zapytanie pasuje do 4 812 rekordów — to za dużo,
  aby zwrócić listę. Zawęź date_from/date_to albo dodaj filtr status; możesz też
  stronicować przekazując next_cursor."`
- Walidacja: `"Parametr date_from ma wartość '16.08.2026' — wymagany format
  ISO 8601: '2026-08-16'."`
- Brak uprawnień: `"Konto serwera nie ma dostępu do modułu płac. Poinformuj
  użytkownika, że operacja wymaga uprawnień administratora systemu kadrowego —
  nie ponawiaj wywołania."`

Zasady twarde: nigdy nie zwracaj śladu stosu ani surowego błędu sterownika bazy
(wyciek szczegółów wewnętrznych i szum w kontekście); odróżniaj błędy do
ponowienia (chwilowy limit API — podaj czas odczekania) od błędów trwałych
(napisz wprost „nie ponawiaj”); komunikat pisz do modelu, w drugiej osobie
trybu rozkazującego.

## 6. Ewaluacja zestawu narzędzi

Zestaw uznaje się za dobry nie wtedy, gdy dobrze wygląda, lecz gdy model dobiera
właściwe narzędzia w zadaniach rzeczywistych. Ewaluuj metodycznie:

1. **Zbuduj listę scenariuszy zadań użytkownika** — 10–20 poleceń w języku
   naturalnym, takich jakie padną naprawdę („które faktury Nowak Sp. z o.o. są
   po terminie?”, „przepisz sprawę 4411 na Kowalską i podnieś priorytet”).
   Dołącz scenariusze negatywne: zadania, których zestaw nie obsługuje —
   model powinien to powiedzieć, a nie wywoływać narzędzia na siłę.
2. **Dla każdego scenariusza zapisz przebieg wzorcowy**: które narzędzia,
   w jakiej kolejności, z jakimi parametrami.
3. **Wykonaj próby z transkryptami.** Uruchom serwer w kliencie rzeczywistym
   (Claude Desktop / Claude Code), podaj scenariusz, zachowaj pełny transkrypt
   wywołań: wybrane narzędzie, parametry, odpowiedź, kroki kolejne. Transkrypt
   jest artefaktem oceny — przechowuj go przy projekcie i porównuj między
   wersjami zestawu.
4. **Mierz co najmniej dwie wielkości:**
   - **trafność pierwszego wyboru** — odsetek scenariuszy, w których pierwsze
     wywołane narzędzie jest zgodne z przebiegiem wzorcowym;
   - **liczba wywołań do celu** — ile wywołań narzędzi model potrzebował do
     poprawnego wyniku względem liczby wzorcowej; nadwyżka wskazuje opisy
     niedookreślone albo odpowiedzi bez identyfikatorów.
5. **Diagnozuj po transkryptach, nie po wrażeniu.** Model wybrał złe narzędzie —
   popraw sekcje „kiedy użyć / kiedy NIE użyć” obu narzędzi pomylonych. Model
   zmyślił parametr — zamień na enum albo dodaj format do opisu. Model utknął po
   pierwszym wywołaniu — sprawdź, czy odpowiedź zawiera identyfikatory
   i wskazówki kroku następnego.
6. **Powtórz ewaluację po każdej zmianie zestawu.** Zmiana opisu jednego
   narzędzia potrafi przestawić wybory w scenariuszach pozornie niezwiązanych.

## 7. Antywzorce zestawów narzędzi

- **Narzędzie-kombajn z 15 parametrami.** Jedno `manage_records(action, type,
  id, filters, payload, ...)` obsługujące wszystko. Model musi odgadnąć
  poprawną kombinację parametrów, a schemat nie chroni przed kombinacjami
  bezsensownymi. Rozbij na narzędzia jednoczynnościowe zgodne z siatką
  czasowników.
- **Lustrzane odbicie REST.** Cztery narzędzia CRUD na każdy zasób API,
  z których model ma sam składać procesy. Objaw: użytkownik pyta o jedną rzecz,
  model wykonuje sześć wywołań. Projektuj narzędzia wokół zadań („znajdź
  zaległości klienta”), nie wokół tabel.
- **`get_all` bez limitu.** Narzędzie zwracające pełną kolekcję zapycha okno
  kontekstu pierwszą odpowiedzią i działa tylko na danych testowych. Każda
  lista: limit + kursor, bez wyjątków.
- **Narzędzia bliźniacze.** Dwa narzędzia o zakresach zachodzących
  (`search_docs` i `find_documents`), między którymi model wybiera losowo.
  Scal albo rozgranicz jawnie w opisach.
- **Flagi zmieniające semantykę.** Parametr `mode`, który przełącza narzędzie
  między odczytem a zapisem — uniemożliwia poprawne adnotacje
  (readOnlyHint/destructiveHint) i kontrolę uprawnień. Odczyt i zapis to zawsze
  osobne narzędzia.
- **Opis pisany dla człowieka.** Marketingowe ogólniki („potężne narzędzie do
  zarządzania fakturami”) zamiast instrukcji decyzyjnej. Model nie kupuje —
  model wybiera; daj mu kryteria wyboru.
- **Wynik bez drogi dalszej.** Lista streszczeń bez identyfikatorów albo błąd
  bez wskazania narzędzia następnego — każda odpowiedź ma zostawiać modelowi
  jasny krok kolejny.
