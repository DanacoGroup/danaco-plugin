# Dane i kontrakty — karta

Karta rozwija etap 3 procedury z `references/architektura/architektura.md` (dane). Stosuj ją przy
projektowaniu modelu danych, kontraktów, transakcji, zapisu czasu oraz migracji. Decyzje o danych są
najtrudniej odwracalne — kod można przepisać, dane trzeba przenieść.

## 1. Właścicielstwo danych

Każda encja ma dokładnie jednego właściciela: moduł będący źródłem prawdy,
jedynym uprawnionym do zapisu i jedynym znającym reguły spójności encji.
Zapis encji „klient” z modułu „faktury” to usterka architektury, nawet jeśli
technicznie baza na to pozwala.

- **Czytelnicy przez interfejs, nie przez wspólną tabelę.** Moduł potrzebujący
  cudzych danych woła publiczny interfejs właściciela albo subskrybuje jego
  zdarzenia — nie wykonuje `SELECT` na cudzej tabeli. Wspólna tabela to
  niejawny kontrakt: właściciel traci prawo zmiany własnego schematu, bo
  nie wie, kto na nim stoi. W monolicie egzekwuj to osobnymi schematami
  bazy na moduł (PostgreSQL: `CREATE SCHEMA faktury`), co czyni naruszenie
  widocznym w kodzie zapytania.
- **Wyjątki świadome, zapisane w ADR:**
  - *Raportowanie i analityka* — zapytania przekrojowe mogą czytać wiele
    schematów, ale wyłącznie do odczytu i przez dedykowane widoki utrzymywane
    przez właścicieli; widok jest wtedy kontraktem, a właściciel może
    zmieniać tabele pod nim bez łamania raportów.
  - *Replika do odczytu* — kopia danych właściciela u czytelnika (zasilana
    zdarzeniami) dla wydajności lub odporności. Kopia jest jawnie wtórna:
    przy rozbieżności prawda leży u właściciela, a mechanizm odtworzenia
    kopii od zera musi istnieć od pierwszego dnia.
- **Dane słownikowe** (waluty, kody krajów, stawki VAT) traktuj jak encje
  z właścicielem — moduł „słowniki” z interfejsem odczytowym — zamiast stałych
  powielanych w modułach, które rozjadą się przy pierwszej zmianie stawki.

## 2. Projektowanie kontraktów

Kontrakt to schemat danych na granicy: odpowiedź API, treść zdarzenia,
format pliku wymiany, argumenty publicznego interfejsu modułu. Od zwykłej
struktury różni się tym, że jego zmiana wymaga koordynacji ze stronami,
których nie kontrolujesz w tej samej rewizji.

### Rozszerzanie bez łamania

Zmiany bezpieczne (nie wymagają wersji ani koordynacji):
- dodanie pola opcjonalnego z sensowną wartością domyślną,
- dodanie nowej operacji lub nowego typu zdarzenia,
- poszerzenie zakresu przyjmowanych wartości na wejściu.

Zmiany łamiące (wymagają nowej wersji i planu wygaszenia):
- usunięcie lub zmiana nazwy pola, zmiana typu lub znaczenia pola,
- dodanie pola wymaganego na wejściu,
- zwężenie zakresu wartości, zmiana semantyki kodów błędów.

Reguły projektowe:
- **Nowe pola zawsze opcjonalne.** Pole obowiązkowe można dodać tylko w nowej
  wersji. Projektując kontrakt od zera, ogranicz pola wymagane do minimum —
  każde pole wymagane to przyszła zmiana łamiąca w zarodku.
- **Tolerancyjny czytelnik.** Odbiorca ignoruje pola, których nie zna,
  i waliduje wyłącznie te, których używa. Deserializacja odrzucająca nieznane
  pola zamienia każde bezpieczne rozszerzenie nadawcy w awarię odbiorcy
  (w Pydantic nie ustawiaj `extra="forbid"` na modelach kontraktów
  przychodzących; w walidacji JSON Schema nie używaj `additionalProperties:
  false` po stronie czytelnika).
- **Nie przeciekaj modelu wewnętrznego.** Kontrakt to osobna struktura,
  mapowana z modelu domenowego, a nie encja bazy serializowana wprost —
  inaczej każda zmiana tabeli staje się zmianą kontraktu.
- Wersjonuj kontrakty zgodnie z SemVer (etap 3 procedury): zmiana łamiąca
  podnosi wersję główną, rozszerzenie — podrzędną.

### Kiedy v2 i jak wygaszać v1

- Nową wersję główną otwieraj dopiero, gdy zmiany nie da się wyrazić
  rozszerzeniem — nagromadzenie drobnych niewygód nie wystarcza, bo koszt
  utrzymania dwóch wersji jest trwały, a niewygody jednorazowe.
- Procedura wygaszania: (1) udostępnij v2 i przenieś własnych klientów;
  (2) ogłoś termin końca v1 z datą, w dokumentacji i w odpowiedziach
  (nagłówek `Deprecation` lub `Sunset` w API HTTP); (3) mierz ruch v1 —
  wygaszanie bez pomiaru to zgadywanie; (4) po terminie zwracaj jednoznaczny
  błąd z instrukcją przejścia (HTTP 410 z odnośnikiem), nie ciche błędne dane.
- Wewnątrz systemu utrzymuj jedną realizację logiki: v1 realizuj jako
  tłumaczenie do v2 na brzegu (adapter), nie jako drugą gałąź kodu — dwie
  gałęzie logiki rozjadą się merytorycznie.
- Przy wdrożeniach on-premise zakładaj, że klienci aktualizują rzadko:
  okresy wygaszania licz w miesiącach, a zdolność systemu do odczytu danych
  zapisanych przez kilka wersji wstecz traktuj jako wymaganie, nie uprzejmość.

## 3. Spójność transakcyjna a ostateczna

### Granica transakcji = granica agregatu

Agregat to zbiór danych zmienianych razem, dla których reguły spójności
muszą zachodzić w każdej chwili — np. zamówienie z pozycjami, gdzie suma
pozycji musi zgadzać się z nagłówkiem. Wyznacz agregaty świadomie:

- Jedna transakcja bazy zmienia jeden agregat. Transakcja obejmująca wiele
  agregatów (a tym bardziej wiele modułów) to sygnał źle wyznaczonej granicy
  albo sekwencji, która powinna być ostateczna.
- Trzymaj agregaty małe. Duży agregat („klient ze wszystkimi zamówieniami”)
  serializuje współbieżne zapisy i wydłuża blokady; jeśli reguła spójności
  nie wymaga natychmiastowości, dane należą do osobnych agregatów.
- Między agregatami spójność jest ostateczna: skutek propaguje się po
  zatwierdzeniu transakcji, a system przez chwilę bywa niespójny przekrojowo.
  To nie usterka, lecz właściwość do zaprojektowania: określ, jak długo
  niespójność jest dopuszczalna i co widzi użytkownik w oknie niespójności.

### Sekwencje wielomodułowe: skrzynka nadawcza

Problem: moduł zapisuje dane i musi powiadomić inne moduły lub systemy;
zapis i powiadomienie nie mogą się rozjechać (zapis bez powiadomienia albo
powiadomienie bez zapisu). Publikacja do brokera wewnątrz transakcji bazy
nie rozwiązuje problemu — broker i baza nie mają wspólnej transakcji.

Rozwiązanie — skrzynka nadawcza (outbox):
1. W tej samej transakcji, która zmienia dane, zapisz wiersz do tabeli
   `skrzynka_nadawcza` (identyfikator, typ zdarzenia, treść, czas).
2. Osobny proces (albo pętla w tle) czyta niewysłane wiersze, publikuje je
   i oznacza jako wysłane; po awarii wznawia od niewysłanych.
3. Odbiorcy muszą być idempotentni — wiersz może zostać opublikowany
   powtórnie po awarii między publikacją a oznaczeniem. Idempotentność
   realizuj tabelą przetworzonych identyfikatorów po stronie odbiorcy
   albo operacją naturalnie powtarzalną (ustaw stan, nie dolicz).

W monolicie z jedną bazą skrzynka bywa zbędna — zdarzenie obsłużone w tej
samej transakcji jest spójne z definicji. Konieczna staje się, gdy odbiorca
jest poza transakcją: osobna usługa, serwer poczty, system klienta.
Najczęstszy przypadek w praktyce Danaco to poczta: wiersz w skrzynce zamiast
wywołania SMTP w transakcji, bo SMTP potrafi trwać sekundy i zawieść.

### Kompensacje

Gdy sekwencja obejmuje kroki w wielu modułach lub systemach bez wspólnej
transakcji (rezerwacja, obciążenie, wysyłka), projektuj ją jako łańcuch
kroków lokalnie transakcyjnych z akcjami odwrotnymi:

- Dla każdego kroku zdefiniuj kompensację (zwolnij rezerwację, zwróć
  obciążenie). Kompensacja to nowa operacja biznesowa, nie cofnięcie
  techniczne — ślad obu operacji zostaje w danych.
- Kroki porządkuj od najłatwiej odwracalnych; krok nieodwracalny (wysłana
  wiadomość, przelew) umieszczaj ostatni.
- Stan sekwencji zapisuj trwale (tabela procesów z krokiem bieżącym), aby
  po awarii wiedzieć, co dokończyć albo skompensować.
- Jeśli sekwencja mieści się w jednej bazie — zrób z niej jedną transakcję.
  Kompensacje są kosztem rozproszenia, nie ozdobą.

## 4. Modelowanie czasu

- **Zdarzenia niezmienne a stan bieżący.** Rozróżniaj zapis faktów (faktura
  wystawiona, płatność zaksięgowana) od stanu bieżącego (saldo, status).
  Fakty są niezmienne: korekta to nowy fakt odwołujący się do poprzedniego
  (faktura korygująca), nie edycja wiersza. Stan bieżący wolno nadpisywać,
  o ile da się go odtworzyć lub uzasadnić faktami.
- **Audytowalność projektuj, nie doklejaj.** Wymaganie „kto, co, kiedy
  zmienił” rozstrzygaj w etapie 1; dopisywanie dziennika zmian do systemu
  nadpisującego dane w miejscu jest wielokrotnie droższe. Minimum: tabele
  faktów tylko-dopisywalne dla operacji objętych odpowiedzialnością prawną,
  znacznik czasu i tożsamość sprawcy przy każdym zapisie.
- **Czas zdarzenia a czas zapisu.** Przechowuj oba: kiedy coś zaszło
  w rzeczywistości (data sprzedaży) i kiedy system się o tym dowiedział
  (czas rejestracji). Korekty wsteczne i raporty „stan na dzień według
  wiedzy z dnia” są niewykonalne, gdy istnieje tylko jeden czas. W systemach
  rozliczeniowych to rozróżnienie bywa wymogiem prawnym.
- **Strefy czasowe.** W zapisie wyłącznie UTC (PostgreSQL: `timestamptz`;
  nigdy `timestamp` bez strefy); strefa lokalna jest sprawą prezentacji.
  Wyjątek przemyślany: terminy umowne i harmonogramy przyszłe („codziennie
  o 8:00 czasu warszawskiego”) przechowuj jako czas lokalny plus nazwę
  strefy IANA (`Europe/Warsaw`), bo przeliczenie do UTC z wyprzedzeniem
  utrwala regułę zmiany czasu, która może się zmienić. Daty bez godziny
  (termin płatności) trzymaj jako datę, nie jako północ w UTC — północ
  w UTC to inna doba w Polsce przez pół roku. Format wymiany: ISO 8601
  z jawnym przesunięciem.

## 5. Migracje danych jako element architektury

Migracja schematu przy działającym systemie to manewr architektoniczny:
przez pewien czas współistnieją dwie wersje kodu i jedna baza, więc schemat
musi być zgodny z obiema.

- **Rozszerz, przenieś, zwęź (expand-migrate-contract).** Każdą zmianę
  łamiącą schemat rozbij na trzy wdrożenia: (1) *rozszerz* — dodaj nową
  kolumnę lub tabelę obok starej; kod pisze w obie, czyta ze starej;
  (2) *przenieś* — uzupełnij dane zastane wsadowo, przełącz odczyt na nowe,
  mierz zgodność; (3) *zwęź* — usuń starą kolumnę i kod przejściowy, w
  osobnym wdrożeniu, po okresie obserwacji. Etap trzeci planuj od razu
  i wykonuj rzeczywiście — porzucone etapy przejściowe to główne źródło
  martwych kolumn i podwójnych zapisów, których po roku nikt nie rozumie.
- **Migracje odwracalne.** Dla każdej migracji określ drogę odwrotu.
  Migracje strukturalne pisz z procedurą odwrotną; dla migracji z natury
  nieodwracalnych (usunięcie kolumny, stratna konwersja) drogą odwrotu jest
  kopia zapasowa — wykonaj ją bezpośrednio przed migracją i zapisz to
  w procedurze wdrożenia, nie w pamięci operatora.
- **Zgodność n-1.** Kod wersji n musi działać ze schematem wersji n+1
  (tolerancja nowej kolumny) albo procedura wdrożenia musi jawnie zakładać
  przerwę serwisową. Wybierz i zapisz w ADR — wdrożenia bez przerwy wymagają
  dyscypliny trzech kroków przy każdej zmianie łamiącej.
- **Duże tabele.** Operacje przepisujące tabelę (zmiana typu kolumny,
  `NOT NULL` na zastanych danych) blokują zapisy proporcjonalnie do
  rozmiaru. Rób je etapami: nowa kolumna, zapis podwójny, uzupełnienie
  wsadowe porcjami, walidacja, podmiana. W PostgreSQL: `ADD CONSTRAINT ...
  NOT VALID` plus późniejsze `VALIDATE CONSTRAINT`, `CREATE INDEX
  CONCURRENTLY` zamiast wariantów blokujących.
- Narzędzie migracji (Alembic dla SQLAlchemy, wbudowane mechanizmy innych
  stosów) trzymaj w repozytorium razem z kodem; migracja jest częścią
  rewizji, która jej wymaga, i przechodzi przez ten sam przegląd.

## 6. Architektura on-premise i desktopowa

Systemy Danaco bywają wdrażane u klienta (on-premise) lub jako aplikacje
pulpitu. To zmienia rachunek architektoniczny — wzorce projektowane dla
chmury przenoszą się źle.

Ograniczenia zastane:
- **Brak elastycznego skalowania.** Sprzęt klienta jest, jaki jest;
  „dołożymy instancję” nie istnieje. Wymiarowanie liczbami z etapu 1 musi
  uwzględniać najsłabszą przewidywaną maszynę, a degradacja pod obciążeniem
  ma być łagodna (kolejkowanie zadań wsadowych, limity równoległości),
  nie nagła.
- **Aktualizacje u klienta.** Wersji nie wdraża się jednym potokiem —
  klienci aktualizują z opóźnieniem i pomijają wersje pośrednie. Migracje
  muszą przechodzić skoki wieloetapowe (z 1.4 od razu do 2.1), a mechanizm
  migracji uruchamiać się przy starcie aplikacji, wykrywać wersję schematu
  i przeprowadzać łańcuch kroków. Testuj ścieżki aktualizacji z kilku
  wersji wstecz, nie tylko z poprzedniej.
- **Telemetria ograniczona.** Dzienniki i metryki zostają u klienta;
  diagnozować trzeba na podstawie tego, co system sam o sobie powie.

Konsekwencje projektowe:
- **Prostota operacyjna jako wymaganie twarde.** Każdy składnik (broker,
  pamięć podręczna, druga baza) to składnik, który administrator klienta
  musi zainstalować, aktualizować i przywracać. Domyślnie: jeden proces,
  jedna baza (PostgreSQL, a przy pulpicie SQLite), zadania w tle wewnątrz
  procesu. Odstępstwo uzasadniaj w ADR liczbami.
- **Samodiagnostyka wbudowana.** Punkt kontrolny (`/health` z wersją
  aplikacji, wersją schematu, stanem dysku i zaległością zadań), spójne
  dzienniki z identyfikatorem korelacji oraz eksport pakietu diagnostycznego
  jedną czynnością (dzienniki plus konfiguracja bez sekretów) do przesłania
  wsparciu.
- **Kopie zapasowe wbudowane.** Nie zakładaj, że klient ma procedury kopii.
  Wbuduj: kopię zaplanowaną z rotacją, kopię wymuszaną przed każdą migracją
  schematu oraz procedurę odtworzenia sprawdzaną testem automatycznym
  (kopia, z której nikt nigdy nie odtwarzał, nie jest kopią). Dla SQLite
  używaj mechanizmu wbudowanego (`VACUUM INTO` albo interfejs kopii),
  nigdy kopiowania pliku bazy w trakcie zapisu.
- **Zgodność wersji u klienta.** Interfejsy między waszymi składnikami
  traktuj jak kontrakty publiczne (sekcja 2) — u klienta mogą spotkać się
  kombinacje wersji, których nie zestawiliście w laboratorium.
