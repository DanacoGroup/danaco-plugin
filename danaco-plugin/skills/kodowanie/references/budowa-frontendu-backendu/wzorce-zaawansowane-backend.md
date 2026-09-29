# Backend, wzorce zaawansowane — karta ekspercka Danaco Code

Karta rozszerza `references/budowa-frontendu-backendu/backend.md` o wzorce poziomu zawodowego.
Wczytaj ją, gdy serwis wychodzi poza prosty CRUD: buforuje dane, przetwarza zadania w tle, woła
zewnętrzne API, obsługuje wielu klientów na wspólnej bazie albo ma działać bez okien serwisowych.
Podstawy z `references/budowa-frontendu-backendu/backend.md` obowiązują nadal.

## Pamięć podręczna warstwowo

Buforowanie wprowadzaj po pomiarze, nie prewencyjnie — każda warstwa pamięci podręcznej to nowe
źródło niespójności i nowa klasa błędów.

**Co wolno buforować.** Dane odczytywane często, zmieniane rzadko: słowniki, konfiguracja, wyniki
drogich agregacji. Nie buforuj wyników zależnych od uprawnień wołającego pod kluczem wspólnym —
wynik zbuforowany dla administratora nie może trafić do zwykłego użytkownika; przy buforowaniu per
użytkownik lub per klient tożsamość wchodzi do klucza. Nie buforuj danych, których świeżość jest
wymogiem domeny (stany rozliczeń, blokady zasobów).

**Unieważnianie po zapisie.** Wzorzec domyślny: przy odczycie sprawdź bufor, przy chybieniu odczytaj
z bazy i zapisz do bufora z czasem życia; przy zapisie danych **usuń** wpis z bufora — nie nadpisuj
go wartością z pamięci procesu, bo równoległy zapis konkurencyjny utrwali wartość przestarzałą. TTL
ustawiaj zawsze — jest zaworem bezpieczeństwa, gdy unieważnienie zawiedzie. Kolejność: najpierw
zatwierdź transakcję bazy, potem unieważnij bufor; odwrotna pozwala równoległemu odczytowi wpisać z
powrotem starą wartość.

**Stampede i blokada odświeżania.** Wygaśnięcie popularnego klucza uwalnia lawinę: sto równoczesnych
żądań chybia i sto razy wykonuje drogie zapytanie. Zapobiegaj blokadą odświeżania — pierwsze żądanie
po wygaśnięciu zdobywa blokadę (np. `SET NX` z krótkim TTL) i przelicza wartość, pozostałe serwują
wartość przestarzałą albo czekają krótko i ponawiają odczyt. Uzupełniająco rozrzucaj TTL losowo
(±10–20%).

**Klucze z wersją.** Buduj klucze według stałej konwencji:
`zasób:wersja-schematu:identyfikator:parametry`, np. `invoice:v3:1842:summary`. Po zmianie kształtu
danych podbij wersję w kodzie, a stare wpisy umrą z TTL — to jedyny bezpieczny sposób masowego
unieważnienia w magazynach bez taniego przeglądu kluczy.

## Zadania w tle

**Kolejka w bazie zanim broker.** Dopóki wolumen nie przekracza rzędu dziesiątek zadań na sekundę,
prowadź kolejkę w tabeli bazy głównej — zyskujesz transakcyjność z danymi domenowymi (zlecenie
zadania w tej samej transakcji, co zapis, który je wywołał) i zero nowej infrastruktury. Zadania
pobieraj wzorcem `SKIP LOCKED`, który pozwala wielu wykonawcom pobierać równolegle bez wzajemnego
blokowania:

```sql
UPDATE tasks SET status = 'processing', started_at = now()
WHERE id = (
  SELECT id FROM tasks
  WHERE status = 'queued' AND run_after <= now()
  ORDER BY run_after
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

Brokera komunikatów wprowadzaj dopiero, gdy pomiar wykaże, że kolejka dławi bazę — jako jawną
decyzję architektoniczną.

**Ponawianie z odczekaniem wykładniczym i limitem.** Zadanie nieudane wraca do kolejki z rosnącym
opóźnieniem (np. 1 min, 5 min, 30 min) i twardym limitem prób. Rozróżniaj błędy trwałe (walidacja,
brak zasobu — od razu do odrzutów) od przejściowych (sieć, przekroczenie czasu — ponawiaj). Przy
zadaniu zapisuj licznik prób i treść ostatniego błędu.

**Zadania trujące i kolejka odrzutów.** Zadanie, które wyczerpało limit prób, przenoś do kolejki
odrzutów (dead letter) z pełnym kontekstem: treść, historia błędów, znaczniki czasu. Kolejka
odrzutów ma alarm — rosnąca liczba odrzutów to incydent. Zapewnij ścieżkę ponownego zlecenia z
odrzutów po naprawie przyczyny; bez niej odrzuty są cmentarzem danych.

**Idempotentność wykonawcy.** Wykonawca może dostać to samo zadanie dwukrotnie (awaria po wykonaniu,
przed potwierdzeniem) — zaprojektuj skutek tak, by powtórzenie było bezpieczne: zapis z
ograniczeniem unikalności na identyfikatorze zadania, operacje „ustaw stan” zamiast „zwiększ o”, a
dla skutków zewnętrznych (wysyłka e-maila, obciążenie płatności) klucz idempotentności przekazywany
do systemu zewnętrznego. Ukończenie zadania i skutki domenowe zapisuj w jednej transakcji, jeżeli
żyją w tej samej bazie.

## Odporność na zewnętrzne API

**Timeouty zawsze.** Każde wywołanie zewnętrzne ma jawny limit czasu — połączenia i odpowiedzi
osobno. Domyślne „bez limitu” większości klientów HTTP oznacza, że jedno wiszące API zatrzymuje
wątki całego serwisu. Limit dobieraj do budżetu odpowiedzi własnego punktu końcowego: skoro
obiecujesz odpowiedź w 2 s, wywołanie zależne nie może mieć limitu 30 s.

**Ponawiaj tylko operacje idempotentne.** Odczyt ponawiaj z odczekaniem wykładniczym i rozrzutem
losowym, małą liczbą prób (2–3). Zapisów nie ponawiaj na ślepo: przekroczenie czasu nie mówi, czy
operacja zaszła — ponowienie POST bez klucza idempotentności to ryzyko podwójnego skutku. Jeżeli
dostawca wspiera klucz idempotentności, przekazuj go i ponawiaj śmiało; jeżeli nie — zapisz operację
jako nierozstrzygniętą do uzgodnienia.

**Bezpiecznik (circuit breaker) w wersji minimalnej.** Gdy zależność pada, kolejne próby przedłużają
agonię: żądania czekają pełny timeout, zasoby się wyczerpują. Minimalny bezpiecznik to licznik i
znacznik czasu na proces: po N kolejnych błędach w oknie czasu otwórz obwód — przez M sekund
odrzucaj wywołania natychmiast, bez czekania na timeout; po upływie M przepuść żądanie próbne —
sukces zamyka obwód, błąd otwiera na kolejne M. Stan bezpiecznika eksponuj w metrykach; otwarcie
obwodu to zdarzenie alarmowe.

**Degradacja: wynik częściowy zamiast 500.** Sklasyfikuj każdą zależność jako krytyczną (bez niej
odpowiedź nie ma sensu — zwróć błąd) albo uzupełniającą (zwróć odpowiedź bez jej wkładu, z jawnym
oznaczeniem braku, np. polem `null` i flagą częściowości — nigdy z wartością zmyśloną ani zerem
udającym daną). Klasyfikację przeprowadź projektując punkt końcowy — w trakcie awarii jest za późno.

## Limity i ochrona

**Rate limiting kubełkiem tokenów per klient.** Każdy klient (klucz API, konto, w ostateczności
adres IP) ma kubełek o pojemności B tokenów uzupełniany w tempie R na sekundę; żądanie zdejmuje
token, brak tokenu daje 429 z nagłówkiem `Retry-After`. Stan kubełków trzymaj w magazynie wspólnym
dla instancji; operacja „sprawdź i zdejmij” musi być atomowa. Zwracaj nagłówki `RateLimit-Limit` /
`RateLimit-Remaining`. Limity różnicuj: operacje drogie (raporty, eksporty) i wrażliwe (logowanie,
reset hasła) mają limity ostrzejsze niż odczyt; limit na logowanie per konto i per IP chroni też
przed zgadywaniem haseł.

**Limity rozmiaru treści.** Maksymalny rozmiar ciała żądania ustaw na poziomie serwera HTTP lub
odwrotnego proxy — zanim treść dotknie aplikacji — oraz limity szczegółowe w aplikacji: długości
pól, liczności tablic, głębokości zagnieżdżenia JSON, rozmiaru i typu plików. Odpowiadaj 413 dla
treści zbyt dużej. Brak limitu liczności tablicy w żądaniu zbiorczym to zaproszenie do zajęcia bazy
jednym żądaniem.

**Ochrona przed powolnym klientem.** Klient wysyłający bajt na sekundę trzyma połączenie godzinami
(atak slowloris). Egzekwuj limity czasu odczytu nagłówków i ciała oraz limit połączeń równoczesnych
per adres — na poziomie serwera HTTP lub proxy, bo aplikacja widzi żądanie dopiero po odebraniu.

## Wielodostęp

W systemie wielu klientów (tenantów) na wspólnej bazie wyciek danych między klientami jest
najpoważniejszą możliwą awarią — traktuj izolację jako wymóg konstrukcyjny, nie konwencję.

**Filtr obowiązkowy na każdym zapytaniu.** Każda tabela danych klientowych ma kolumnę identyfikatora
klienta i każde zapytanie — odczyt, zapis, aktualizacja, usunięcie, agregacja — filtruje po niej bez
wyjątku. Zapytanie „po identyfikatorze rekordu, bo przecież unikalny” bez filtru klienta to
podatność IDOR z `references/budowa-frontendu-backendu/backend.md` o zasięgu międzyfirmowym.

**Wzorce egzekwowania — dyscyplina nie wystarczy.** Ręczne dopisywanie filtru zawiedzie
statystycznie; wybierz mechanizm egzekwujący:

- Identyfikator klienta ustalaj wyłącznie z kontekstu uwierzytelnienia (token, sesja) w jednym
  miejscu — nigdy z parametru żądania, któremu można nadać cudzą wartość.
- Repozytoria przyjmują kontekst klienta w konstruktorze lub jako obowiązkowy parametr każdej
  metody; nie istnieje publiczna metoda czytająca dane klientowe bez kontekstu. Wariant ORM:
  globalny filtr dokładany automatycznie do każdego zapytania na encjach klientowych.
- Zapora ostateczna w bazie: w PostgreSQL zabezpieczenia na poziomie wierszy (RLS) z polityką
  porównującą kolumnę klienta ze zmienną sesji ustawianą na początku każdej transakcji — chronią
  także przed zapytaniem ręcznym i pominiętym filtrem.

Zasoby zagnieżdżone weryfikuj w całym łańcuchu: pozycja faktury należy do faktury, która należy do
klienta — sprawdzenie samej pozycji nie wystarczy.

**Testy izolacji.** Utrzymuj stały zestaw testów z danymi co najmniej dwóch klientów, sprawdzający
dla każdego punktu końcowego: odczyt cudzego zasobu po identyfikatorze zwraca 404 (nie 403 — nie
potwierdzaj istnienia cudzych zasobów), listy nie zawierają cudzych rekordów, agregacje nie liczą
cudzych danych, mutacja cudzego zasobu jest odrzucona. Test izolacji dla nowego punktu końcowego
jest częścią definicji ukończenia.

## Migracje bez przestoju

Przy wdrożeniu kroczącym stara i nowa wersja aplikacji działają równocześnie na jednym schemacie —
każda migracja musi być zgodna z wersją aplikacji n-1. Stąd żelazna reguła: **nigdy nie łącz w
jednym wydaniu zmiany schematu łamiącej ze zmianą kodu, która jej wymaga.**

**Rozszerz–przenieś–zwęź.** Zmianę łamiącą (zmiana nazwy kolumny, typu, przeniesienie danych)
rozkładaj na wydania:

1. **Rozszerz** — dodaj nowy element (kolumna dopuszczająca NULL lub z wartością domyślną, nowa
   tabela) bez usuwania starego. Migracja zgodna wstecz; stara aplikacja jej nie widzi.
2. **Przenieś** — nowy kod pisze do obu miejsc (albo wyzwalacz bazy replikuje zapisy), a dane
   historyczne dosypuje uzupełnienie wsadowe partiami z ograniczeniem tempa — nie jednym UPDATE
   milionów wierszy, który trzyma blokady i wysyca I/O. Odczyt przełącz na nowe miejsce dopiero po
   zweryfikowanej zgodności danych.
3. **Zwęź** — po pełnym przełączeniu i okresie obserwacji usuń stare miejsce i zapisy podwójne,
   osobnym wydaniem. Dopóki żyje kod czytający starą kolumnę, kolumna zostaje.

**Operacje niebezpieczne na działającej bazie.** Zanim napiszesz migrację, sprawdź jej wpływ na
blokady w używanym silniku: zmiana typu, dodanie NOT NULL czy indeksu potrafią blokować tabelę na
czas przepisania. W PostgreSQL buduj indeksy przez `CREATE INDEX CONCURRENTLY`, a NOT NULL
wprowadzaj przez ograniczenie CHECK dodane jako `NOT VALID` i walidowane osobno. Każdej migracji
ustaw `lock_timeout`, aby migracja czekająca na blokadę nie zakorkowała ruchu — lepiej, by padła i
wróciła później.

## Obserwowalność pro

**Metryki RED per punkt końcowy.** Zbieraj: częstość żądań (Rate), odsetek błędów (Errors — 5xx
osobno od 4xx; wzrost 4xx to zwykle problem klienta lub kontraktu, wzrost 5xx to awaria), czas
odpowiedzi (Duration) jako histogram, z którego liczysz percentyle 50/95/99 — nigdy samą średnią, bo
średnia ukrywa ogon, a użytkownicy żyją w ogonie. Etykietuj metryki metodą i szablonem ścieżki
(`/invoices/{id}`, nie ścieżką z konkretnym identyfikatorem — eksplozja liczności etykiet zabija
system metryk). Te same sygnały zbieraj dla wykonawców zadań w tle, plus wiek najstarszego zadania w
kolejce.

**Korelacja żądań przez system.** Identyfikator korelacyjny z
`references/budowa-frontendu-backendu/backend.md` propaguj przez wszystkie granice: do zadań w tle
(zapisany w treści zadania), do wywołań zewnętrznych (nagłówek), do wpisów dziennika wykonawców.
Ślad ma odpowiadać na pytanie „co się stało z żądaniem X” od wejścia HTTP po ostatnie zadanie
pochodne — bez korelacji przez granicę kolejki diagnoza urywa się w połowie.

**Progi alarmów z histerezą.** Alarmuj na objawach widocznych dla użytkownika (odsetek błędów,
percentyl czasu, wiek kolejki, otwarte bezpieczniki), nie na przyczynach wewnętrznych (zużycie CPU)
— przyczyny obserwuj na pulpitach, alarmuj na skutkach. Każdy alarm definiuj z histerezą: warunek
musi trwać nieprzerwanie przez okno czasu (np. 5 minut powyżej progu), a wygaszenie wymaga zejścia
poniżej progu niższego niż próg zapłonu — inaczej metryka oscylująca wokół progu generuje trzepot
powiadomień, który uczy zespół ignorowania alarmów.

## Bezpieczeństwo operacyjne

**Rotacja sekretów.** Projektuj system tak, by każdy sekret dało się wymienić bez przestoju:
aplikacja czyta sekrety ze środowiska lub magazynu sekretów przy starcie, a weryfikacja akceptuje
przejściowo dwa klucze (stary i nowy) na czas rotacji. Sekret, którego wymiana wymaga zmiany kodu,
jest błędem konstrukcyjnym. Sekret raz zapisany w historii repozytorium traktuj jako ujawniony na
zawsze — odpowiedzią jest natychmiastowa rotacja, nie przepisywanie historii.

**Zależności: audyt w CI.** Uruchamiaj audyt znanych podatności zależności przy każdej zmianie i
cyklicznie na harmonogramie; podatność krytyczna lub wysoka w zależności produkcyjnej blokuje
scalenie. Utrzymuj plik blokady wersji i aktualizuj zależności regularnie małymi krokami — kwartalna
aktualizacja hurtowa jest ryzykowniejsza niż cotygodniowa drobna.

**Nagłówki odpowiedzi.** Ustaw komplet nagłówków ochronnych centralnie (middleware lub odwrotne
proxy), nie per trasa: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
`Content-Security-Policy` (dla API czyste `default-src 'none'`; dla treści HTML polityka dopasowana
do zasobów), `Referrer-Policy`, a dla odpowiedzi z danymi wrażliwymi `Cache-Control: no-store`. Usuń
nagłówki zdradzające wersje serwera i frameworka. CORS konfiguruj listą dozwolonych źródeł — nigdy
odbiciem nagłówka `Origin` ani `*` przy żądaniach z poświadczeniami.
