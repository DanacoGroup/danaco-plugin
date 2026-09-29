# Dekompozycja: od problemu do modułów

Dekompozycja jest jedyną decyzją architektoniczną, której nie da się później zmienić
tanio. Zmiana bazy to migracja. Zmiana frameworka to przepisanie warstwy. Zmiana granic
modułów to przepisanie wszystkiego, bo granice określają, co o czym wie.

## Krok 1: wypisz czasowniki, nie rzeczowniki

Model domyślnie dzieli system po rzeczownikach z opisu („użytkownik”, „produkt”,
„zamówienie”) i dostaje moduł na tabelę. To nie jest dekompozycja, to lista tabel.

Zacznij od czasowników — od tego, co system **robi**:

> przyjmuje zgłoszenie, przydziela je serwisantowi, rejestruje czas pracy, wystawia
> rozliczenie, powiadamia klienta, zamyka zgłoszenie po akceptacji

Zgrupuj czasowniki, które: (a) dzielą ten sam słownik, (b) zmieniają się z tego samego
powodu, (c) muszą być spójne w tym samym momencie. Grupa czasowników = kandydat na moduł.

Sprawdzenie: **przydziela** i **rejestruje czas** dzielą pojęcie serwisanta i zmieniają
się razem, gdy zmieni się polityka przydziału. **Powiadamia** nie dzieli nic — używa
tylko identyfikatorów. To osobny moduł, i to peryferyjny.

## Krok 2: wykryj granicę po słowniku

Ta sama nazwa oznaczająca dwie różne rzeczy to najpewniejszy sygnał granicy.

| Słowo | W module A znaczy | W module B znaczy | Wniosek |
| --- | --- | --- | --- |
| „Klient” | podmiot z NIP-em i umową (`rozliczenia`) | osoba logująca się do panelu (`dostep`) | Dwa modele, nie jeden. Wspólny jest tylko identyfikator |
| „Produkt” | pozycja w katalogu z opisem i zdjęciem (`katalog`) | pozycja magazynowa z SKU i stanem (`magazyn`) | Dwa modele. Katalog nie zna stanów magazynowych |
| „Zamówienie” | koszyk w trakcie składania (`sprzedaz`) | dokument do skompletowania (`logistyka`) | Dwa modele. Przejście między nimi to zdarzenie |

Błąd domyślny: jedna klasa `Klient` z 40 polami, z których 12 jest zawsze `null`
w połowie przypadków użycia. To jest dowód, że skleiłeś dwa modele.

Poprawka nie polega na dziedziczeniu ani na polach opcjonalnych. Polega na dwóch
osobnych typach w dwóch modułach i jawnej mapie identyfikatorów między nimi.

## Krok 3: wyznacz granice transakcyjne

Granica transakcyjna to zbiór danych, które muszą być spójne **w tym samym momencie**.
Wszystko poza nią może być spójne za chwilę.

Reguła praktyczna: jedna transakcja obejmuje **jeden agregat**. Agregat to encja główna
plus dane, które nie mają sensu bez niej (zgłoszenie + jego zdarzenia; zamówienie +
jego pozycje). Operacja na dwóch agregatach naraz w jednej transakcji jest dopuszczalna
w monolicie, ale każde takie miejsce jest przyszłą granicą usługi — oznacz je.

Pytania rozstrzygające:

| Pytanie | Odpowiedź „tak” znaczy |
| --- | --- |
| Czy niespójność między X a Y przez 2 sekundy jest widoczna dla użytkownika i szkodliwa? | Ta sama transakcja |
| Czy niespójność jest odwracalna kompensacją? | Osobne transakcje + kompensacja |
| Czy Y jest tylko powiadomieniem o tym, że X się zdarzyło? | Osobne. Wzorzec outbox |
| Czy X i Y są modyfikowane przez różnych aktorów w różnym tempie? | Osobne agregaty |

**Wzorzec outbox** — jedyny poprawny sposób połączenia zmiany danych z efektem
zewnętrznym (e-mail, webhook, wpis do kolejki):

```sql
BEGIN;
UPDATE zgloszenia SET status = 'zamkniete' WHERE id = $1;
INSERT INTO outbox (id, typ, payload, utworzono)
VALUES (uuidv7(), 'zgloszenie.zamkniete', $2, now());
COMMIT;
-- osobny proces czyta outbox, wysyła, oznacza jako wysłane
```

Bez outboxu masz dwa scenariusze awarii: e-mail wysłany, transakcja wycofana (klient
dostaje informację o zdarzeniu, które się nie stało) albo transakcja zatwierdzona,
e-mail nie poszedł (nikt się nie dowiedział). Outbox eliminuje pierwszy i czyni drugi
przejściowym.

## Krok 4: oddziel rdzeń od peryferii

Nie każdy moduł zasługuje na tę samą staranność. Rozdziel:

| Kategoria | Definicja | Jak traktować |
| --- | --- | --- |
| **Rdzeń** | To, za co klient płaci. Reguły, których nikt inny nie ma | Własny kod, testy jednostkowe reguł, model domenowy bez I/O, najwyższa staranność przeglądu |
| **Wspierające** | Potrzebne, ale niewyróżniające. Katalog, uprawnienia, konfiguracja | Prosty kod, CRUD, bez ceremonii, testy integracyjne |
| **Ogólne** | Rozwiązane problemy: auth, e-mail, płatności, PDF, logowanie | Kup albo weź gotowe. Własna implementacja tutaj to strata |

Praktyczna konsekwencja: model domyślnie wkłada tyle samo wysiłku w system uprawnień
(ogólny) co w silnik wyceny (rdzeń). To odwrócenie priorytetów. Silnik wyceny zasługuje
na czyste funkcje, property-based testy i ADR. System uprawnień zasługuje na bibliotekę.

Test przynależności do rdzenia: **czy konkurent, który skopiuje ten moduł, zabierze wam
przewagę?** Jeśli nie, to nie jest rdzeń.

## Krok 5: przewidź osie zmian

Architektura ma być odporna nie na wszystko, tylko na to, co faktycznie się zmieni.
Wypisz 3–5 najbardziej prawdopodobnych zmian w perspektywie 18 miesięcy i sprawdź,
ile plików dotyka każda.

| Oś zmiany | Typowe źródło | Ile plików powinna dotknąć |
| --- | --- | --- |
| Nowy typ dokumentu / produktu / zgłoszenia | Sprzedaż | 1 moduł, najlepiej 1 plik z definicją |
| Zmiana reguły cenowej / rabatowej | Biznes | 1 plik w domenie, zero w infrastrukturze |
| Nowy kanał wejścia (API dla partnera, aplikacja mobilna) | Rozwój | Warstwa prezentacji, zero w domenie |
| Zmiana dostawcy (płatności, poczta, magazyn plików) | Koszty, awaria | 1 adapter |
| Nowy rynek / waluta / język | Ekspansja | Konfiguracja + tłumaczenia, nie logika |
| Wymóg zgodności (retencja, eksport danych, audyt) | Prawo | Warstwa danych + jeden przekrojowy mechanizm |

Jeśli którakolwiek z tych zmian dotyka więcej niż dwóch modułów, granice są źle
postawione. Przesuń je teraz, kiedy jest tanio.

Odwrotność też jest błędem: uelastycznianie osi, które **nie** będą się zmieniać.
Konfigurowalny silnik reguł dla trzech reguł zapisanych w umowie na 5 lat to koszt bez
zwrotu. Zmienność, której nie potwierdzono, nie jest wymaganiem.

## Krok 6: monolit modularny — domyślna forma

### Dlaczego prawie zawsze monolit na starcie

| Wymiar | Monolit modularny | Usługi |
| --- | --- | --- |
| Zmiana granicy modułu | Refaktoryzacja w jednym repo, kompilator wskazuje błędy | Zmiana kontraktu + wersjonowanie + koordynacja wdrożeń |
| Transakcja obejmująca dwie domeny | `BEGIN ... COMMIT` | Saga, kompensacje, stany pośrednie |
| Debugowanie | Jeden stos wywołań | Trace rozproszony, korelacja logów |
| Wdrożenie | Jeden artefakt | Orkiestracja, wersje, zgodność wsteczna |
| Środowisko lokalne | `npm run dev` | Docker Compose z 6 kontenerami albo atrapy |
| Koszt osobowy | 1 programista wystarczy | ~1 zespół na usługę, żeby to miało sens |

Granice modułów w monolicie są **odwracalne**. Granice usług są **kontraktami
sieciowymi** — praktycznie nieodwracalne, bo po drugiej stronie ktoś już na nich polega.

Sekwencja, która działa: monolit modularny → moduł zaczyna boleć konkretnym, mierzalnym
bólem → wydzielenie tego jednego modułu → reszta zostaje. Sekwencja, która nie działa:
sześć usług od pierwszego dnia i odkrycie w trzecim miesiącu, że granice są w złych
miejscach.

### Kiedy jednak wydzielić usługę

Wydzielasz, gdy zachodzi **co najmniej jeden** z tych warunków — i zapisujesz to w ADR:

1. **Niezależne wdrożenia z powodów organizacyjnych.** Dwa zespoły blokują się nawzajem
   na wspólnym wydaniu. To jedyny naprawdę częsty powód.
2. **Profil zasobowy różny o rząd wielkości.** Moduł przetwarzania wideo potrzebuje GPU
   i 32 GB RAM; reszta aplikacji potrzebuje 512 MB. Skalowanie razem jest marnotrawstwem.
3. **Izolacja awarii wymagana kontraktem.** Padnięcie modułu raportów nie może położyć
   przyjmowania zamówień, a nie da się tego zapewnić w jednym procesie.
4. **Wymóg zgodności wymuszający izolację.** Dane medyczne/płatnicze w osobnym obwodzie
   z osobnym audytem dostępu.
5. **Inny cykl życia technologicznego.** Moduł musi działać na innym runtimie
   (np. model ML w Pythonie przy backendzie w TypeScript).

Nie są powodami: „bo tak się teraz robi”, „bo będziemy skalować”, „bo to czystsze”,
„bo każdy zespół chce swój stack”, „bo tak było w poprzedniej firmie”.

### Jak wygląda dobrze zrobiony moduł w monolicie

```
src/modules/zgloszenia/
  index.ts              ← JEDYNY plik eksportujący cokolwiek na zewnątrz
  domain/               ← encje, reguły, typy; zero importów spoza modułu
  application/          ← przypadki użycia; importuje domain i porty
  infrastructure/       ← repozytoria, adaptery; implementuje porty
  http/                 ← kontrolery/route'y tego modułu
```

Reguły, które czynią to modułem, a nie katalogiem:

- Inny moduł importuje **wyłącznie** z `modules/zgloszenia` (czyli z `index.ts`).
  Import z `modules/zgloszenia/domain/Zgloszenie` z zewnątrz jest naruszeniem.
- `index.ts` eksportuje: funkcje przypadków użycia, typy DTO, typy zdarzeń. **Nie**
  eksportuje encji domenowych ani repozytoriów.
- Moduł ma własne tabele. Żaden inny moduł nie pisze do nich i nie robi na nich JOIN-a.
  Odczyt cudzych danych — przez funkcję z `index.ts` albo przez widok czytelniczy.
- Komunikacja między modułami: wywołanie funkcji z `index.ts` (synchronicznie) albo
  zdarzenie przez outbox (asynchronicznie). Nigdy przez wspólną tabelę.

Egzekwowanie tych reguł narzędziami — `references/engineering-core/references/granice-i-warstwy.md`.

## Krok 7: skalowanie jako decyzja odroczona

Skalowanie jest decyzją, którą **trzeba umieć podjąć później**, a nie podjąć teraz.
Twoim zadaniem dziś jest nie zamknąć sobie drogi, a nie zbudować drogę.

Co zrobić teraz (tanie, nie komplikuje):

- Aplikacja bezstanowa: żadnego stanu sesji w pamięci procesu, żadnych plików na dysku
  instancji, żadnych timerów `setInterval` zakładających jedną instancję.
- Zadania w tle idempotentne i możliwe do uruchomienia równolegle.
- Zapytania do bazy zawsze ograniczone (`LIMIT`) i indeksowane. Brak zapytań
  „pobierz wszystko i przefiltruj w aplikacji”.
- Identyfikatory generowane po stronie aplikacji (UUIDv7), nie przez `SERIAL` — to
  otwiera drogę do wstawiania wsadowego i replikacji bez konfliktów.
- Metryki: czas odpowiedzi p95, liczba zapytań na żądanie, rozmiar tabel. Bez pomiaru
  nie zauważysz momentu, w którym trzeba działać.

Czego **nie** robić teraz:

| Rzecz | Kiedy naprawdę | Koszt przedwczesnego wprowadzenia |
| --- | --- | --- |
| Cache (Redis) | Zmierzone zapytanie >200 ms po dodaniu indeksu, ruch odczytowy dominuje | Niespójność, unieważnianie, dodatkowa usługa do utrzymania |
| Broker kolejek (Kafka/RabbitMQ) | >1000 zdarzeń/s albo wielu konsumentów o różnym tempie | Operacje, dead-letter, kolejność, at-least-once w każdym konsumencie |
| Repliki odczytu | Baza obciążona odczytem >60% czasu | Opóźnienie replikacji — czytasz stan sprzed zapisu |
| Sharding | Pojedyncza tabela >500 GB albo zapisy przekraczają jedną maszynę | Brak transakcji między shardami, klucz shardingu nieodwracalny |
| CDN dla API | Ruch globalny i treści cache'owalne | Unieważnianie, nagłówki, debugowanie „u mnie działa” |
| Autoskalowanie poziome | Ruch zmienia się >5× w cyklu dobowym | Zimne starty, koszt, przepełnienie puli połączeń do bazy |

Jedna maszyna z Postgresem obsługuje więcej, niż model zakłada: kilka tysięcy żądań na
sekundę przy zapytaniach z indeksem, tabele do setek milionów wierszy. Zanim dodasz
warstwę, zmierz, gdzie faktycznie idzie czas.

## Test gotowej dekompozycji

Zanim przejdziesz do kodu, przejdź te sześć pytań. Każde „nie” wymaga poprawki.

1. Czy potrafisz opisać każdy moduł jednym zdaniem bez spójnika „i”? („Moduł zgłoszeń
   obsługuje cykl życia zgłoszenia **i** wysyła powiadomienia” = dwa moduły.)
2. Czy zmiana reguły biznesowej w module dotyka plików tylko tego modułu?
3. Czy potrafisz wskazać, które dane muszą być spójne natychmiast, a które mogą później?
4. Czy każdy moduł ma jawnie zadeklarowane publiczne API (nie „wszystko, co wyeksportowane”)?
5. Czy graf zależności między modułami jest acykliczny? Cykl A→B→A oznacza, że to jeden
   moduł albo brakuje trzeciego, do którego oba należą.
6. Czy dla każdego modułu potrafisz powiedzieć, czy jest rdzeniem, wspierającym czy
   ogólnym — i czy nakład pracy to odzwierciedla?

## Częste błędne podziały

| Podział | Dlaczego zawodzi | Zamiast |
| --- | --- | --- |
| Po warstwach technicznych na najwyższym poziomie (`controllers/`, `services/`, `models/`) | Każda zmiana funkcjonalna dotyka 4 katalogów; nie widać, co system robi | Domeny na górze, warstwy w środku domeny |
| Po typach encji, jedna encja = jeden moduł | Moduły ciągle się wołają; granice przecinają operacje | Po przypadkach użycia i słowniku |
| Po CRUD (`create`, `read`, `update`) | Rozbija operację biznesową na cztery moduły | Po intencji: `przyjmijZgloszenie`, `zamknijZgloszenie` |
| Moduł „common” / „shared” / „core” | Puchnie w zbiór wszystkiego, staje się zależnością wszystkich, blokuje zmiany | Kopiuj drobne rzeczy; wspólne tylko typy prymitywne i narzędzia bez logiki |
| Moduł na warstwę integracji ze wszystkimi dostawcami | Zmiana jednego dostawcy dotyka modułu używanego przez wszystkich | Adapter przy module, który go używa |
| Podział odwzorowujący strukturę organizacyjną z prezentacji zarządu | Struktura firmy zmieni się szybciej niż kod | Po słowniku domeny |
