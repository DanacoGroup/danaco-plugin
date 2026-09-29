# Jakość od początku — karta

Jakość wbudowana, nie doklejona. Każdy element tej karty jest tani w pierwszej
wersji i drogi w doklejaniu, bo dopisanie go później wymaga przejścia przez
cały kod jeszcze raz. „Dodamy potem” w praktyce oznacza „dodamy po pierwszej
awarii”.

## Obsługa błędów jako architektura

Obsługa błędów nie jest zbiorem bloków `try/except` dopisywanych tam, gdzie coś
pękło — jest decyzją architektoniczną podejmowaną raz na projekt.

### Taksonomia błędów projektu

Ustal na początku trzy klasy i trzymaj się ich w całym kodzie:

1. **Błędy domenowe** — poprawne technicznie sytuacje przewidziane przez
   dziedzinę: brak środków na koncie, faktura już zaksięgowana, przekroczony
   limit. Są częścią kontraktu funkcji: reprezentuj je jawnie (dedykowane typy
   wyjątków dziedziczące ze wspólnej bazy projektu, albo typ wyniku
   sukces/porażka tam, gdzie ekosystem to preferuje). Na granicy API mapują się
   na odpowiedzi 4xx z czytelnym komunikatem dla użytkownika.
2. **Błędy techniczne** — zewnętrze zawiodło: sieć, baza, dysk, usługa obca.
   Nie są winą wywołującego; bywają przejściowe. Decyzja per punkt styku:
   ponowić (z wykładniczym odstępem i limitem prób — tylko dla operacji
   idempotentnych), zdegradować (wartość z pamięci podręcznej, funkcja
   ograniczona), czy przerwać. Na granicy API — 5xx lub 503, bez szczegółów
   wewnętrznych w treści odpowiedzi.
3. **Błędy programisty** — złamane założenie: `None` tam, gdzie obiecano wartość,
   ujemny indeks, nieobsłużony wariant wyliczenia. Ich nie obsługuje się —
   ujawnia się je jak najgłośniej (asercja, wyjątek nieprzechwycony poza
   najwyższą warstwą), bo każda próba „obsłużenia” maskuje defekt. Przechwycenie
   `except Exception: pass` wokół błędu programisty to najdroższa linia kodu
   w projekcie.

### Strategia per warstwa: propaguj, mapuj, loguj raz

- **Warstwy wewnętrzne propagują.** Funkcja, która nie umie sensownie zareagować
  na błąd, nie przechwytuje go — przepuszcza wyżej. Przechwycenie tylko po to,
  by zalogować i rzucić dalej, produkuje ten sam błąd w dzienniku pięć razy.
- **Granice warstw mapują.** Na przejściu między warstwami tłumacz błędy na
  słownik warstwy wyższej: wyjątek sterownika bazy nie wycieka do warstwy HTTP;
  repozytorium mapuje go na błąd techniczny projektu, zachowując oryginał jako
  przyczynę (łańcuchowanie: `raise ... from ...` w Pythonie, pole `cause`
  w JS) — bez łańcucha przyczyn diagnoza po fakcie jest zgadywaniem.
- **Loguj raz, na szczycie.** Jeden punkt w procesie (middleware, główna pętla,
  handler najwyższego poziomu) loguje błąd z pełnym śladem stosu i kontekstem.
  Reguła: albo obsługujesz błąd (i ewentualnie logujesz ostrzeżenie), albo
  propagujesz — nigdy „loguję jako błąd i rzucam dalej”.

Zachowanie każdego punktu styku z zewnętrzem w razie niepowodzenia ma być
wypowiedziane w kodzie, nie domyślne. Brak decyzji to też decyzja — zwykle zła.

## Projektowanie konfiguracji

### Warstwy nadpisań

Jedna, stała kolejność źródeł, od najsłabszego do najsilniejszego:

1. **Wartości domyślne w kodzie** — bezpieczne dla środowiska lokalnego,
   zdefiniowane w jednym miejscu (moduł konfiguracji), nie rozsiane po wywołaniach.
2. **Plik konfiguracyjny** — wersjonowany wzorzec (np. `config.example.toml`)
   w repozytorium; plik faktyczny środowiska poza repozytorium.
3. **Zmienne środowiskowe** — kanał właściwy dla kontenerów i wdrożeń;
   ze stałym przedrostkiem projektu (np. `DANACO_DB_HOST`), by nie kolidować
   z otoczeniem.
4. **Argumenty wiersza poleceń** — najsilniejsze, do jednorazowych nadpisań.

Warstwa silniejsza nadpisuje słabszą per klucz, nie w całości. Nie każdy projekt
potrzebuje wszystkich warstw — skrypt może poprzestać na domyślnych plus
argumenty — ale kolejność, gdy warstwy istnieją, jest zawsze ta sama.

### Walidacja na starcie, nie przy użyciu

Całą konfigurację wczytaj i zweryfikuj w jednym miejscu przy starcie procesu:
typy, zakresy, spójność (np. wskazany katalog istnieje, adres ma poprawny
format). Przy braku lub błędzie zakończ proces natychmiast z komunikatem
mówiącym **co** jest złe i **skąd** wartość pochodzi: „DANACO_DB_PORT=abc —
oczekiwano liczby całkowitej 1–65535 (zmienna środowiskowa)”. Proces, który
startuje z błędną konfiguracją i pada godzinę później przy pierwszym użyciu
brakującego klucza, marnuje godzinę diagnozy na błąd wykrywalny w sekundę.
W Pythonie naturalnym narzędziem jest model pydantic (`BaseSettings`);
w Node — walidacja obiektu konfiguracji schematem (np. zod) na starcie.
Resztę kodu pisz tak, by przyjmowała gotowy, zweryfikowany obiekt konfiguracji —
żadnych `os.environ` w głębi logiki.

### Sekrety oddzielnie od konfiguracji

Sekret (hasło, klucz API, token) różni się od konfiguracji cyklem życia
i skutkiem wycieku, więc płynie innym kanałem: zmienne środowiskowe wstrzykiwane
przez mechanizm wdrożenia, plik poza repozytorium, magazyn sekretów. Twarde
zasady: sekret nigdy w repozytorium (także w historii — wyciek do historii
wymaga rotacji sekretu, nie tylko usunięcia pliku), nigdy w dzienniku (pole
sekretne maskuj w reprezentacji obiektu konfiguracji), nigdy w komunikacie
błędu. Wzorzec pliku (`.env.example`) zawiera nazwy kluczy z wartościami
pustymi lub fikcyjnymi.

## Idempotentność od pierwszej wersji

Operacja idempotentna wykonana wielokrotnie daje skutek jak wykonana raz.
W systemie, gdzie cokolwiek może zostać powtórzone — a powtórzone będzie:
ponowienie po błędzie sieci, dwuklik użytkownika, ponowna dostawa komunikatu,
wznowiony skrypt — idempotentność nie jest ozdobą, lecz warunkiem poprawności.

- **Klucze idempotentności dla operacji tworzących.** Tworzenie zasobu na
  żądanie zewnętrzne przyjmuje klucz idempotentności (od klienta lub wyliczony
  z treści żądania); zapisany unikalnie w bazie sprawia, że powtórka zwraca
  wynik pierwszego wykonania zamiast tworzyć duplikat. Ograniczenie `UNIQUE`
  w bazie jest tu egzekutorem — reguła wymuszana tylko w kodzie aplikacji
  przegrywa z wyścigiem dwóch równoczesnych żądań.
- **Powtarzalne migracje i skrypty.** Skrypt administracyjny i migracja danych
  muszą wytrzymać przerwanie w połowie i ponowne uruchomienie: konstrukcje
  warunkowe (`CREATE TABLE IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`),
  przetwarzanie partiami ze znacznikiem postępu, sprawdzenie stanu przed
  działaniem zamiast założenia stanu wyjściowego. Migracje schematu prowadź
  narzędziem z ewidencją wykonanych kroków (Alembic, migracje frameworka) —
  nigdy „ręcznym SQL-em z notatek”.
- **Nadawanie zamiast dodawania.** Tam gdzie to możliwe, projektuj operacje
  jako ustawienie stanu docelowego („ustaw status na X”), nie przyrost
  („zwiększ o 1”) — pierwsze jest idempotentne z natury, drugie wymaga
  dodatkowej ochrony przed powtórką.

## Obserwowalność od pierwszej wersji

System nieobserwowalny jest diagnozowany metodą dokładania wydruków po awarii —
na produkcji, pod presją. Minimalny standard od pierwszego przyrostu:

- **Dziennik strukturalny.** Wpis to zdarzenie z polami (JSON lub format
  klucz=wartość), nie sklejone zdanie: `{„event”: „invoice_posted”,
  „invoice_id”: ..., „duration_ms”: ...}`. Po polach da się filtrować
  i agregować; po zdaniach — tylko grep z żalem. Komunikat opisuje zdarzenie,
  dane zmienne idą w polach.
- **Poziomy używane konsekwentnie.** ERROR — wymaga reakcji człowieka; WARNING —
  zaskakujące, obsłużone samoczynnie; INFO — zdarzenia biznesowe i cykl życia
  procesu (start z wersją i zarysem konfiguracji bez sekretów, stop, migracje);
  DEBUG — diagnostyka wyłączona domyślnie na produkcji. Dziennik, w którym
  ERROR pojawia się rutynowo i jest ignorowany, przestał być dziennikiem.
- **Identyfikator korelacji przez cały przepływ.** Na wejściu żądania przyjmij
  lub nadaj identyfikator (nagłówek typu `X-Request-ID`), dołączaj do każdego
  wpisu dziennika w obrębie przepływu (kontekst logera: `contextvars`
  w Pythonie, `AsyncLocalStorage` w Node) i przekazuj dalej w wywołaniach do
  innych usług oraz w komunikatach do kolejek. Bez korelacji dziennik z ruchem
  równoległym jest nieczytelny.
- Emitowanie metryk i śladów rozproszonych dodawaj według potrzeb projektu,
  ale strukturę dziennika i korelację — zawsze, bo ich doklejenie po fakcie
  oznacza przejście przez każdy punkt logowania w systemie.

## Granice zasobów jawne

Każdy zasób bez jawnego limitu ma limit niejawny — poznasz go podczas awarii.

- **Timeout każdego wywołania zewnętrznego.** Domyślne zachowanie wielu
  bibliotek to czekanie bez końca (`requests` w Pythonie nie ma domyślnego
  timeoutu). Każde wywołanie sieciowe, zapytanie do bazy i uruchomienie
  podprocesu dostaje jawny limit czasu dobrany do operacji; wartość w
  konfiguracji, nie w literale przy wywołaniu. Rozróżniaj timeout nawiązania
  połączenia od timeoutu odczytu.
- **Limity rozmiaru wejścia.** Maksymalny rozmiar treści żądania, wysyłanego
  pliku, wiersza parsowanego pliku, głębokości zagnieżdżenia dokumentu —
  ustalone i egzekwowane na brzegu, zanim wejście dotknie logiki. Wejście bez
  limitu to zaproszenie do wyczerpania pamięci jednym żądaniem.
- **Paginacja od początku, nie „potem”.** Każde zapytanie listujące ma limit
  i mechanizm stronicowania od pierwszej wersji — końcówka zwracająca „wszystkie
  rekordy” działa pięknie na dziesięciu wierszach testowych i kładzie system
  na stu tysiącach produkcyjnych. Dodanie paginacji później to zmiana łamiąca
  kontrakt, więc najdroższy możliwy moment. Preferuj stronicowanie kursorem
  (po kluczu ostatniego elementu) nad `OFFSET` dla dużych zbiorów.
- **Pule i współbieżność.** Rozmiar puli połączeń do bazy, liczba równoczesnych
  zadań, pojemność kolejki wewnętrznej — jawne wartości w konfiguracji,
  z określonym zachowaniem przy wyczerpaniu (czekaj z limitem albo odrzuć).

## Projektowanie na niepowodzenie zewnętrza

Pytanie zadawane przy każdym przyroście dotykającym zewnętrza: **co się stanie,
gdy to zawiedzie w połowie?** Baza odmówi po zapisaniu pliku; proces padnie
między dwoma zapisami; sieć zerwie po wysłaniu, a przed odebraniem potwierdzenia.

- **Kolejność zapisów według odwracalności.** Gdy operacja obejmuje kilka
  zapisów, których nie obejmuje jedna transakcja, wykonuj najpierw kroki
  odwracalne lub powtarzalne, na końcu krok nieodwracalny „przypieczętowujący”
  (np. najpierw zapisz plik pod nazwą tymczasową, na końcu jedna atomowa zmiana
  nazwy; najpierw rekord w stanie „w przygotowaniu”, na końcu przełączenie
  stanu). Przerwanie przed pieczęcią zostawia śmieć do sprzątnięcia, nie
  niespójność.
- **Transakcje tam, gdzie baza je daje.** Powiązane zapisy do jednej bazy
  obejmuj jedną transakcją — i nie rozciągaj transakcji na wywołania sieciowe
  ani inne operacje wolne, bo długa transakcja trzyma blokady. Wywołanie obcej
  usługi wewnątrz transakcji bazy to klasyczny błąd: po awarii sieci nie
  wiadomo, czy skutek zewnętrzny zaszedł, a wycofanie transakcji go nie cofnie.
- **Kompensacje zamiast złudzenia transakcji rozproszonej.** Sekwencję operacji
  na wielu systemach projektuj jako kroki z jawnymi działaniami odwrotnymi
  (utworzyłeś zasób u dostawcy, dalszy krok padł → usuń zasób) oraz stanem
  zapisanym po każdym kroku, by proces wznowiony mógł dokończyć albo skompensować.
  W prostych projektach wystarcza tabela stanów operacji i skrypt domykający;
  nazwa wzorca w literaturze: saga.
- **Wzorzec skrzynki nadawczej (outbox)** dla pary „zapisz w bazie i powiadom
  świat”: zamiast wysyłać komunikat po zatwierdzeniu transakcji (proces może
  paść pomiędzy), zapisz komunikat w tej samej transakcji do tabeli-skrzynki,
  a osobny mechanizm wysyła z niej i oznacza wysłane. Odbiorców i tak projektuj
  na powtórki — patrz idempotentność.

## Higiena zależności przy budowie

Każda zależność to kod, za który odpowiadasz, nie pisząc go.

Kryteria doboru biblioteki — sprawdź przed dodaniem, nie po:

- **Utrzymanie.** Data ostatniego wydania, reakcja na zgłoszenia, liczba
  opiekunów. Biblioteka bez wydań od trzech lat w aktywnie zmieniającym się
  ekosystemie to przyszły koszt; wyjątek stanowią biblioteki ukończone
  o stabilnym, wąskim zakresie.
- **Licencja.** Zgodna z przeznaczeniem projektu; licencje wirusowe (AGPL/GPL)
  w produkcie własnościowym wymagają decyzji właściciela projektu, nie
  przemilczenia.
- **Waga.** Rozmiar wraz z zależnościami przechodnimi. Nie dodawaj biblioteki
  dla jednej funkcji, którą pisze się w piętnaście linii — każda pozycja
  w drzewie zależności to powierzchnia ataku, praca przy aktualizacjach
  i ryzyko konfliktu wersji.

Zasady od pierwszej rewizji:

- **Przypinanie i lockfile.** Plik deklaracji określa zakresy, plik blokady
  (`package-lock.json`, `poetry.lock`/`uv.lock`, `requirements.txt` generowany
  z `pip-compile`) utrwala dokładne wersje całego drzewa — i jest w repozytorium.
  Budowa bez pliku blokady jest nieodtwarzalna: „u mnie działa” różni się od
  produkcji o jedną minor wersję zależności przechodniej.
- **Aktualizacje świadome.** Podnoszenie wersji to osobna rewizja z uruchomieniem
  testów, nie skutek uboczny innej pracy; wpis w dzienniku zmian biblioteki
  przeczytany przed podniesieniem wersji głównej.
- **Granica wokół zależności niepewnej.** Bibliotekę, co do której są wątpliwości
  (młoda, egzotyczna), obejmij własnym cienkim modułem osłonowym, by wymiana
  nie oznaczała zmian w całym kodzie. Nie osłaniaj rzeczy fundamentalnych
  (framework, sterownik bazy) — tej wymiany i tak nie przetrwa żadna osłona.
