# Granice i wzorce — karta

Karta rozwija etap 2 procedury (granice i moduły). Stosuj ją przy podziale
systemu na moduły, przy decyzji o komunikacji między nimi oraz przy każdej
propozycji wydzielenia osobnej usługi.

## 1. Spójność i sprzężenie jako narzędzia decyzyjne

Spójność (co trzymać razem) i sprzężenie (jak mocno rzeczy rozdzielone
zależą od siebie) nie są etykietami do oceny cudzego kodu — są narzędziem
podejmowania decyzji o granicach. Każdą propozycję granicy oceniaj pytaniem:
jakie sprzężenie ta granica wytworzy i czy jest ono znośne.

### Rodzaje sprzężeń, od najgorszego do znośnego

1. **Sprzężenie przez zawartość** — moduł sięga do wnętrza innego modułu:
   czyta jego prywatne pola, woła funkcję pomocniczą nieprzeznaczoną na
   zewnątrz, importuje z głębi cudzego pakietu (`from faktury.wewnetrzne.obliczenia
   import zaokraglij`). Każda zmiana wnętrza łamie sąsiada. Zakazane bez wyjątków.
2. **Sprzężenie przez wspólne dane trwałe** — dwa moduły piszą i czytają tę
   samą tabelę bazy danych. Schemat tabeli staje się niejawnym, niewersjonowanym
   kontraktem; migracja wymaga uzgodnienia wszystkich piszących naraz. Odmiana
   szczególnie zdradliwa, bo niewidoczna w grafie importów. Dopuszczalne tylko
   w układzie jeden właściciel pisze, pozostali czytają przez interfejs właściciela
   (karta `dane-i-kontrakty`, sekcja 1).
3. **Sprzężenie przez wspólny stan ulotny** — moduły komunikują się przez
   zmienną globalną, wspólną pamięć podręczną albo plik tymczasowy. Kolejność
   wykonania staje się niejawnym warunkiem poprawności; błędy ujawniają się
   tylko pod współbieżnością.
4. **Sprzężenie przez kontrolę** — moduł przekazuje drugiemu flagę sterującą
   jego zachowaniem (`generuj_raport(tryb="uproszczony")`, gdzie tryb zmienia
   logikę odbiorcy). Zastępuj dwiema jawnie nazwanymi operacjami albo
   przeniesieniem decyzji do wołanego.
5. **Sprzężenie temporalne** — poprawność zależy od kolejności wywołań
   nieegzekwowanej przez typy ani interfejs (`otworz()` musi poprzedzić
   `przetworz()`). Egzekwuj kolejność konstrukcją: obiekt, którego nie da się
   utworzyć w stanie niegotowym, albo funkcja przyjmująca wynik poprzedniej.
6. **Sprzężenie przez strukturę danych (stemplowe)** — moduł dostaje całą
   encję, choć potrzebuje dwóch pól. Znośne wewnątrz modułu, niewskazane na
   granicy — na granicy przekazuj to, co kontrakt nazywa.
7. **Sprzężenie przez dane** — moduł dostaje dokładnie te wartości proste
   lub obiekty kontraktowe, których potrzebuje. To sprzężenie docelowe.
8. **Sprzężenie przez nazwę** — moduł zna wyłącznie nazwę interfejsu drugiego
   modułu. Najsłabsze osiągalne; więcej rozprzęgać się nie opłaca.

Reguła decyzyjna: obniżenie sprzężenia o stopień ma cenę (pośrednictwo,
mapowanie, kod). Płać ją na granicach modułów; wewnątrz modułu silniejsze
sprzężenie klas jest normalne i tanie.

### Heurystyka podziału: razem się zmienia — razem mieszka

Najlepszym predyktorem dobrej granicy nie jest podobieństwo pojęć, lecz
wspólna przyczyna zmian. Kod zmieniający się w tych samych zleceniach
umieszczaj w jednym module; kod zmieniający się z różnych powodów rozdzielaj,
nawet jeśli pojęciowo brzmi podobnie. Sprawdzaj empirycznie na historii
repozytorium: pliki wielokrotnie modyfikowane w tych samych rewizjach,
a leżące w różnych modułach, to sygnał źle poprowadzonej granicy (analiza
współzmienności: `git log --name-only` plus zliczenie par). Granicę, którą
każda typowa zmiana musi przekraczać, przesuń, zamiast dopisywać procedury
koordynacji.

## 2. Monolit modułowy jako architektura pierwszego wyboru

Dla systemów klasy Danaco (zespół mały, wdrożenia także on-premise) domyślną
architekturą jest monolit modułowy: jeden proces wdrożeniowy, wewnątrz twarde
granice modułów — pod warunkiem, że granice są egzekwowane maszynowo, nie
umową ustną.

### Egzekwowanie granic wewnątrz monolitu

- **Importy jednokierunkowe.** Wyznacz dozwolony kierunek zależności
  (np. `www → uslugi → domena`; moduły biznesowe nie importują się nawzajem
  poza interfejsami). Cykl importów między modułami to usterka architektury —
  napraw przez odwrócenie zależności (interfejs w module niższym, realizacja
  w wyższym), nie przez import lokalny w funkcji.
- **Publiczny interfejs modułu.** Każdy moduł wystawia jeden punkt wejścia
  (w Pythonie: `__init__.py` pakietu z jawnym `__all__`; w Node/TypeScript:
  `index.ts` z eksportami). Import z głębi cudzego modułu jest zakazany,
  nawet gdy technicznie możliwy.
- **Narzędzia egzekwujące, uruchamiane w CI:**
  - Python: `import-linter` — kontrakty `layers` (porządek warstw),
    `forbidden` (zakaz konkretnej zależności), `independence` (moduły
    równorzędne nie znają się nawzajem). Plik kontraktów trzymaj obok
    dokumentu architektury i zmieniaj je razem.
  - JavaScript/TypeScript: `eslint-plugin-boundaries` (typy elementów i
    macierz dozwolonych zależności) albo `dependency-cruiser` (reguły
    zakazów i walidacja cykli, wraz z generowaniem grafu zależności).
- Test zależności, który nigdy nie był czerwony, jest podejrzany — po
  wdrożeniu reguł wprowadź celowo łamiący import i upewnij się, że CI go
  odrzuca.

## 3. Porty i adaptery bez ceremonii

Wzorzec portów i adapterów (architektura heksagonalna) oddziela logikę od
świata zewnętrznego: logika definiuje port (interfejs w swoim języku),
adapter tłumaczy port na konkretną technologię. Stosuj go proporcjonalnie
do niestabilności otoczenia, nie rytualnie.

- **Zawsze port:** styk z systemem zewnętrznym, który może zostać wymieniony
  lub którego nie kontrolujesz — bramka płatności, serwer poczty, API
  urzędowe, system klienta przy wdrożeniu on-premise. Port pozwala też
  testować logikę bez sieci: adapter testowy zamiast atrap protokołu HTTP.
- **Port zwykle zbędny:** własna baza danych w monolicie, którą kontrolujesz
  w całości. Abstrahowanie „na wypadek zmiany bazy” to projektowanie na
  zapas — zmiana bazy zdarza się rzadko i i tak wymaga migracji danych,
  której żaden interfejs nie ukryje. Wystarczy zebranie zapytań w jednym
  miejscu modułu (repozytorium jako konwencja, nie jako pięć interfejsów).
- **Sygnał przerostu ceremonii:** interfejs z dokładnie jedną realizacją
  produkcyjną, której wymiana nie jest przewidywana wymaganiami, oraz
  mapowania obiekt-w-obiekt bez zmiany treści. Usuń pośrednika.
- Kierunek zależności jest ważniejszy niż liczba warstw: technologia zależy
  od logiki, nigdy odwrotnie.

## 4. Warstwa antykorupcyjna przy systemie zastanym

Przy integracji z systemem zastanym (ERP klienta, stara aplikacja, format
plików sprzed lat) nie wpuszczaj cudzego modelu w głąb własnego. Warstwa
antykorupcyjna to moduł tłumaczący na granicy:

- Cudze pojęcia kończą się w warstwie tłumaczącej; do wnętrza wchodzą
  wyłącznie pojęcia własnego modelu. Jeśli system zastany nazywa kontrahenta
  „konto”, a wasz model „klient”, tłumaczenie następuje raz, na granicy —
  wystąpienie „konta” w module domenowym to usterka.
- Warstwa tłumaczy także reguły dziwności: puste pola oznaczające brak,
  daty zapisane tekstem, kody słownikowe. Waliduj i normalizuj na wejściu;
  wnętrze systemu ma prawo zakładać dane poprawne.
- Warstwa jest szersza niż adapter: adapter tłumaczy protokół, warstwa
  antykorupcyjna — model pojęciowy. Przy prostym, zdrowym API zewnętrznym
  wystarczy adapter; warstwę buduj, gdy cudzy model jest rozległy, niespójny
  lub sprzeczny z waszym. Jej koszt (podwójne definicje, mapowania)
  uzasadnia ochrona modelu, na którym stoi logika; dla integracji wąskiej
  i odczytowej wystarczy funkcja tłumacząca.

## 5. Komunikacja między modułami — kryteria twarde

Trzy podstawowe mechanizmy, w kolejności rosnącego kosztu:

### Wywołanie bezpośrednie (funkcja przez publiczny interfejs modułu)
- Stosuj, gdy: wołający potrzebuje wyniku, aby kontynuować; operacja jest
  częścią tej samej transakcji; niepowodzenie odbiorcy ma zatrzymać wołającego.
- Koszty: sprzężenie czasowe (odbiorca musi działać teraz) i zależność
  kierunkowa (wołający zna odbiorcę). W monolicie oba koszty są niskie.
- To domyślny mechanizm. Odejście od niego wymaga uzasadnienia, nie odwrotnie.

### Zdarzenie domenowe (w procesie, synchronicznie lub po zatwierdzeniu transakcji)
- Stosuj, gdy: nadawca nie powinien znać odbiorców („faktura zatwierdzona” —
  księgowość, powiadomienia i statystyki reagują niezależnie); liczba
  odbiorców będzie rosła; reakcja odbiorcy nie warunkuje powodzenia nadawcy.
- Kryterium twarde: jeśli nadawca musi wiedzieć, czy odbiorca się powiódł,
  to nie jest zdarzenie — to wywołanie w przebraniu. Wróć do wywołania.
- Koszty: przepływ sterowania niewidoczny w kodzie nadawcy (loguj publikację
  i obsługę z jednym identyfikatorem korelacji); pokusa ukrytych łańcuchów
  zdarzeń; obsługa w transakcji wiąże czasy, obsługa po transakcji wymaga
  przemyślenia awarii odbiorcy.
- Nazywaj zdarzenia w czasie przeszłym dokonanym („ZamowienieZlozone”),
  nigdy trybem rozkazującym — zdarzenie stwierdza fakt, nie wydaje polecenia.

### Kolejka trwała (osobny broker lub tabela w bazie)
- Stosuj, gdy: praca musi przetrwać restart procesu; odbiorca bywa niedostępny
  lub wolniejszy od nadawcy (bufor wyrównawczy); wymagane są ponowienia
  z odstępem; przetwarzanie wsadowe poza godzinami szczytu.
- Koszty — wymieniaj je w ADR wprost: dostarczenie co najmniej raz wymusza
  idempotentnych odbiorców; kolejność bywa niegwarantowana; pojawia się
  operacyjna powierzchnia (monitoring długości kolejki, kolejka niedoręczonych,
  procedura odtwarzania); diagnostyka wymaga śledzenia rozproszonego.
- W monolicie z PostgreSQL zacznij od kolejki w tabeli (`SELECT ... FOR
  UPDATE SKIP LOCKED`) zamiast brokera — jedna technologia mniej, a
  przepustowość wystarcza do rzędu setek zadań na sekundę. Broker wprowadzaj,
  gdy liczby z wymagań dowodzą, że tabela nie wystarczy.

## 6. Kryteria wydzielenia usługi z monolitu

Wydzielenie osobnej usługi jest decyzją trudno odwracalną — wymaga ADR.
Uzasadnieniem są wyłącznie kryteria dowiedzione, nie moda:

1. **Skalowanie niezależne dowiedzione liczbami.** Jeden moduł potrzebuje
   zasobów rzędu wielokrotności pozostałych (np. przetwarzanie plików zajmuje
   80% procesora w szczycie, głodząc obsługę żądań), a skalowanie całego
   monolitu jest wymiernie droższe niż wydzielenie. Pokaż pomiar, nie
   przypuszczenie.
2. **Odrębny cykl wydań.** Moduł musi być wdrażany w innym rytmie lub przez
   inny zespół, a sprzęganie wydań powoduje mierzalne opóźnienia. W zespole
   jednoosobowym spełnia się rzadko.
3. **Granica awarii.** Zawodny lub zasobożerny fragment (integracja z
   niestabilnym systemem zewnętrznym, przetwarzanie plików zdolne wysycić
   pamięć) ma prawo paść bez zabierania reszty: pada usługa pomocnicza,
   monolit dalej obsługuje użytkowników.
4. **Odrębne wymagania środowiska.** Fragment wymaga innego systemu, sprzętu
   (GPU) albo strefy bezpieczeństwa nie do pogodzenia w jednym procesie.

Koszty wydzielenia — spisz je w ADR obok korzyści:
- **Sieć:** każde wywołanie zyskuje opóźnienie, limity czasu, ponowienia
  i możliwość częściowej awarii; funkcja staje się żądaniem, które może
  nie wrócić.
- **Spójność:** wspólna transakcja znika; sekwencje wielousługowe wymagają
  skrzynki nadawczej i kompensacji (karta `dane-i-kontrakty`, sekcja 3).
- **Operacje:** drugi potok wdrożeniowy, osobne dzienniki, wersjonowanie
  kontraktu, środowisko testowe z dwiema usługami; przy on-premise koszt
  rośnie u każdego klienta z osobna.

Warunek wstępny: wydzielaj wyłącznie moduł, który już w monolicie ma czyste
granice. Wydzielenie splątanego modułu zamienia splątanie lokalne na
sieciowe — najgorszy z możliwych wyników.

## 7. Ewolucja architektury bez wielkiego przepisania

Wielkie przepisanie systemu naraz to najdroższy i najrzadziej udany manewr
architektoniczny. Zamiast niego stosuj strategie przyrostowe:

- **Wzorzec dusiciela (strangler fig).** Postaw przed systemem zastanym
  fasadę kierującą ruch. Kolejne funkcje przejmuje nowy system, fasada
  przełącza trasy pojedynczo; stary system obumiera funkcja po funkcji.
  Warunki powodzenia: fasada od pierwszego dnia, przejmowanie od funkcji
  najmniej splątanych, mierzalny postęp (odsetek ruchu w nowym systemie),
  usuwanie martwego kodu starego systemu po przełączeniu trasy na stałe.
- **Równoległe działanie z porównaniem wyników (parallel run).** Nową
  realizację uruchamiaj obok starej: obie liczą, odpowiada stara,
  rozbieżności są logowane. Przełączenie po zadanym okresie zgodności
  (np. zero rozbieżności przez dwa tygodnie na ruchu produkcyjnym).
  Wskazane dla logiki obliczeniowej (podatki, rozliczenia), gdzie testy nie
  pokryją przypadków zastanych w danych. Koszt: podwójne liczenie i
  obowiązek przeglądania rozbieżności — ustal, kto przegląda i kiedy
  strategia się kończy.
- **Migracja czytelnicy-najpierw.** Przełączaj najpierw odczyty, potem
  zapisy: nowe źródło zasilane równolegle, czytelnicy przełączani stopniowo
  z możliwością natychmiastowego powrotu, zapis na końcu, gdy odczyty
  dowiodły zgodności. Odwrotna kolejność odbiera drogę odwrotu.

Zasada wspólna: każdy krok ewolucji zostawia system działający i wdrażalny.
Gałąź rozwojowa żyjąca miesiącami obok produkcji to wielkie przepisanie
w przebraniu.
