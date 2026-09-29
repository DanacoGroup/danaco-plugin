# Rzemiosło refaktoryzacji — karta

Karta pogłębia sekcję „Refaktoryzacja” ze `SKILL.md`. Definicja obowiązuje bez
wyjątków: refaktoryzacja zmienia budowę wewnętrzną **bez zmiany zachowania
obserwowalnego**. Zmiana, po której system robi coś innego, nie jest
refaktoryzacją — jest zmianą funkcjonalną i podlega innym rygorom.

## Katalog przekształceń z warunkami bezpieczeństwa

Każde przekształcenie ma warunki, których spełnienie czyni je bezpiecznym.
Przekształcenie prowadzone bez sprawdzenia warunków to zgadywanie z edytorem.

### Wydzielenie funkcji (extract function)

Fragment ciała funkcji przenieś do nowej funkcji o nazwie mówiącej **co**,
nie **jak**; w miejscu fragmentu zostaw wywołanie.

Warunki bezpieczeństwa: zidentyfikuj wszystkie zmienne czytane przez fragment
(staną się parametrami) i wszystkie zapisywane a używane dalej (staną się
wynikiem — jeżeli jest ich więcej niż jedna, fragment jest źle wybrany albo
potrzebny jest obiekt wyniku). Uwaga na wyjścia w środku fragmentu (`return`,
`continue`, `break`) — po wydzieleniu zmieniają znaczenie; fragment z takim
wyjściem przekrój inaczej albo przekaż decyzję wynikiem. Preferuj mechaniczne
wykonanie narzędziem środowiska (refaktoryzacje IDE), które te analizy robi
za ciebie; ręcznie — po jednej zmiennej na raz, z uruchomieniem testów.

### Wydzielenie modułu

Grupę funkcji i danych o wspólnej odpowiedzialności przenieś do osobnego pliku.
Warunki: najpierw ustal graf zależności grupy — co grupa importuje i kto
importuje grupę. Przenosiny prowadź tak, by nie powstał import cykliczny
(patrz niżej); w kroku przejściowym stary moduł może reeksportować nowe
położenie (import z gwiazdką jest zakazany — reeksport imienny), by nie zmieniać
wszystkich miejsc użycia w jednej rewizji. Reeksport przejściowy usuń w rewizji
domykającej — ma termin, nie jest stanem docelowym.

### Wprowadzenie parametru

Wartość zaszytą w funkcji (literał, zmienna globalna, odwołanie do konfiguracji)
zamień na parametr z wartością domyślną równą dotychczasowej. Warunki: wartość
domyślna zachowuje zachowanie wszystkich obecnych wywołań — dzięki temu zmiana
jest zgodna wstecz i może wejść osobno, a wywołania przestawiaj po kolei.
Gdy parametrów przybywa ponad trzy–cztery, nie dokładaj kolejnych — wprowadź
obiekt parametrów. Nie przenoś do parametrów zależności „na zapas”; parametr
wprowadza się, gdy istnieje drugie wywołanie z inną wartością albo potrzeba
testu (patrz szew).

### Zamiana warunków na wielopostaciowość

Gdy ten sam łańcuch `if/elif` po typie lub rodzaju obiektu powtarza się
w kilku miejscach, przenieś gałęzie do metod wariantów: klasa bazowa lub
protokół z metodą, warianty implementują swoje zachowanie, miejsca użycia
wywołują metodę bez rozgałęzień. Warunki bezpieczeństwa: przekształcenie
wykonuj wtedy, gdy rozgałęzienie po rodzaju występuje **wielokrotnie** —
pojedynczy `if/elif` w jednym miejscu jest prostszy niż hierarchia klas
i zostaw go w spokoju. Sprawdź, że gałąź domyślna (`else`) ma odpowiednik:
brak dopasowania musi zachowywać się identycznie po zmianie (wariant domyślny
albo jawny błąd — ten sam co przed zmianą). Kolejność sprawdzeń w łańcuchu
bywa znacząca (warunki nierozłączne) — wielopostaciowość ją gubi, więc
najpierw upewnij się, że warunki są rozłączne. W językach z typami suma
(wyliczenia, unie dyskryminowane) rozważ odwrotny kierunek: jedno dopasowanie
wzorca z kontrolą zupełności bywa czytelniejsze niż rozproszenie zachowania
po klasach — wybierz oś, wzdłuż której projekt częściej rośnie (nowe warianty →
wielopostaciowość; nowe operacje → dopasowanie).

### Rozplątanie zależności cyklicznej

Cykl importów (A importuje B, B importuje A) sygnalizuje, że granica modułów
przebiega w złym miejscu. Trzy wyjścia, w kolejności preferencji:

1. **Wydziel trzeci moduł.** Zwykle cykl istnieje, bo oba moduły dzielą wspólny
   fragment (typy, stałe, funkcje pomocnicze) — przenieś go do modułu trzeciego,
   od którego oba zależą; strzałka podwójna zamienia się w dwie zgodne.
2. **Odwróć jedną zależność.** Moduł niższy nie woła wyższego wprost — wyższy
   przekazuje niższemu funkcję zwrotną lub implementację protokołu (odwrócenie
   zależności). Właściwe, gdy jedna strona cyklu jest pojęciowo „niżej”.
3. **Scal moduły** — jeżeli podział był sztuczny i nic go nie uzasadnia,
   dwa małe splecione moduły uczciwiej żyją jako jeden.

Import wewnątrz funkcji jako obejście cyklu traktuj wyłącznie jako opatrunek
tymczasowy z terminem — ukrywa problem przed narzędziami i czytelnikiem.
Warunek bezpieczeństwa wspólny: po każdym kroku uruchom import całego pakietu
i testy — cykle potrafią pękać w porządku inicjalizacji, nie w składni.

### Wprowadzenie szwu (seam)

Szew to miejsce, w którym można podmienić zachowanie bez edycji kodu
podmienianego — warunek testowalności kodu zależnego od zewnętrza (zegar, sieć,
baza, losowość, system plików). Technika minimalna: zależność, którą funkcja
dziś pobiera sama (tworzy klienta HTTP, woła `datetime.now()`), przenieś do
parametru z wartością domyślną równą dotychczasowej — zachowanie produkcyjne
bez zmian, a test podaje atrapę. W kodzie obiektowym odpowiednikiem jest
wstrzyknięcie zależności przez konstruktor. Warunki bezpieczeństwa: szew
wprowadzaj przekształceniem najprostszym z możliwych, bo często robisz to
w kodzie **jeszcze niepokrytym testami** — to przekształcenie otwierające,
po którym dopiero budujesz siatkę. Nie buduj przy tej okazji frameworka
wstrzykiwania ani hierarchii interfejsów; jeden parametr, jedno miejsce.
Łatanie globalne (monkeypatching w testach) jest dopuszczalnym szwem doraźnym,
ale sygnalizuje, że kod właściwego szwu nie ma — odnotuj to.

## Kolejność rozbioru dużego pliku

Plik-moloch (kilka tysięcy linii, kilkanaście odpowiedzialności) rozbieraj
w ustalonym porządku, nie „od góry”:

1. **Sporządź mapę odpowiedzialności.** Przejdź plik i wypisz grupy: co jest
   czystym przekształceniem danych, co dostępem do zewnętrza, co logiką
   dziedziny, co sklejką. Zanotuj zależności między grupami. Mapa jest notatką
   roboczą w rozmowie, nie dokumentem w repozytorium.
2. **Zbuduj lub uzupełnij siatkę testów** dla obszarów, które będą ruszane
   (testy charakteryzujące — patrz niżej). Rozbiór bez siatki to przepisywanie,
   nie refaktoryzacja.
3. **Wydzielaj od liści.** Najpierw grupy bez zależności od reszty pliku:
   stałe, typy, czyste funkcje pomocnicze. Każde wydzielenie to osobna mała
   rewizja; po każdej — testy. Liście wychodzą tanio i zmniejszają splątanie
   rdzenia.
4. **Potem grupy zależne tylko od liści**, warstwa po warstwie w porządku
   topologicznym. Jeżeli grupa nie chce wyjść, bo jest spleciona z inną —
   najpierw rozplecz (wprowadzenie parametru, odwrócenie zależności), potem
   wydzielaj.
5. **Rdzeń na końcu.** To, co zostało po wyprowadzeniu liści i warstw pośrednich,
   jest właściwym rdzeniem odpowiedzialności pliku — często okazuje się
   zaskakująco mały i bywa, że po rozbiorze zasługuje już tylko na lepszą nazwę.

Nie planuj rozbioru „na raz w tydzień”: porządek liście-do-rdzenia pozwala
przerwać po dowolnym kroku, zostawiając projekt lepszym niż był — zgodnie
z zasadą najmniejszego kroku wdrażalnego z karty `references/budowa-kodu/techniki-przyrostowe.md`.

## Refaktoryzacja pod osłoną testów charakteryzujących

Kod zastany bez testów najpierw okrywa się siatką utrwalającą obecne zachowanie
(procedura budowy siatki — karta `references/budowa-kodu/techniki-przyrostowe.md`, sekcja „Testy
charakteryzujące”). Zasady użycia siatki podczas refaktoryzacji:

- Siatka pokrywa **gałęzie zmienianego obszaru**, nie cały plik; do wyników
  złożonych stosuj testy zatwierdzeniowe (golden master).
- Podczas refaktoryzacji siatka musi pozostać zielona **bez modyfikacji
  testów**. Konieczność poprawienia testu charakteryzującego w trakcie
  refaktoryzacji oznacza jedno z dwojga: zachowanie się zmieniło (to już nie
  refaktoryzacja — cofnij albo przekwalifikuj zmianę) albo test był sprzęgnięty
  z budową wewnętrzną, nie z zachowaniem (popraw test **przed** dalszą pracą,
  w osobnej rewizji).
- Dziwactwo utrwalone w siatce (zachowanie wyglądające na błąd) zgłoś
  właścicielowi projektu; jego naprawa to zmiana funkcjonalna po refaktoryzacji,
  nigdy „przy okazji” w jej trakcie.
- Po zakończeniu refaktoryzacji oceń siatkę: testy charakteryzujące pisane
  naprędce bywają kruche; te wartościowe przekształć w regularne testy
  jednostkowe z czytelnymi nazwami, nadmiarowe usuń.

## Wykrywanie kodu do refaktoryzacji — sygnały mierzalne

Refaktoryzuj tam, gdzie inwestycja się zwraca, a nie tam, gdzie kod „się nie
podoba”. Sygnały mierzalne, z progami orientacyjnymi (kalibruj do projektu):

- **Zmienność × złożoność.** Najsilniejszy sygnał: pliki jednocześnie często
  zmieniane i złożone. Zmienność policzysz z historii:
  `git log --since="12 months ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20`
  daje listę najczęściej dotykanych plików; skrzyżuj ją ze złożonością
  (narzędzie typu radon dla Pythona, złożoność cyklomatyczna z ESLint dla JS).
  Plik w czołówce obu list to pierwszy kandydat. Plik złożony, lecz nietykany
  od lat — kandydatem nie jest (patrz „Kiedy nie refaktoryzować”).
- **Długość funkcji.** Powyżej ~40–50 linii — przyjrzyj się; powyżej ~100 —
  funkcja niemal na pewno skleja kilka odpowiedzialności. Próg to sygnał do
  spojrzenia, nie przepis: płaska sekwencja kroków bywa czytelniejsza niż
  wymuszone pokrojenie na jednorazowe funkcje pomocnicze.
- **Głębokość zagnieżdżenia.** Powyżej 3–4 poziomów wcięć logiki — stosuj
  wyjścia wczesne (klauzule strażnicze), wydzielaj wnętrza pętli, odwracaj
  warunki. Złożoność cyklomatyczna funkcji powyżej ~10 — sygnał analogiczny.
- **Sygnały niemierzalne, lecz twarde:** ta sama zmiana wymaga edycji wielu
  plików naraz (rozproszona odpowiedzialność — shotgun surgery); poprawki
  błędów wracają w to samo miejsce; nikt nie chce dotykać pliku. Zmiana
  wracająca trzeci raz w to samo miejsce to silniejszy argument niż każda
  metryka.

## Kiedy NIE refaktoryzować

Odmowa refaktoryzacji bywa decyzją zawodową. Nie refaktoryzuj, gdy:

- **Kod jest stabilny i nie ma zmian planowanych.** Brzydki moduł działający
  bez zarzutu, nietykany od dwóch lat i nieprzewidziany do zmian, zostaw
  w spokoju — refaktoryzacja to inwestycja zwracana przyszłymi zmianami;
  bez przyszłych zmian zwrot nie istnieje, a ryzyko regresji tak.
- **Przed terminem krytycznym.** Refaktoryzacja tuż przed wydaniem dokłada
  ryzyko w chwili najmniejszej tolerancji na ryzyko. Zanotuj zamiar, wykonaj
  po wydaniu.
- **Bez testów i bez czasu na ich zbudowanie.** Refaktoryzacja bez siatki nie
  jest refaktoryzacją, lecz hazardem. Jeżeli czasu na siatkę nie ma — nie ma
  refaktoryzacji: wykonaj bieżące zadanie najmniejszą bezpieczną zmianą
  i **zapisz dług** w formie przyjętej w projekcie (zgłoszenie w rejestrze
  zadań z opisem: co jest splątane, jaki koszt generuje, co trzeba zbudować,
  by ruszyć). Komentarz `TODO` w kodzie nie jest zapisem długu — nikt go nie
  planuje.
- Wyjątek stały: **refaktoryzacja przygotowawcza w skali mikro** — zmiana
  nazwy, wydzielenie funkcji, mały porządek w miejscu, które za chwilę
  zmieniasz funkcjonalnie („najpierw uczyń zmianę łatwą, potem wykonaj łatwą
  zmianę”) — pozostaje dozwolona zawsze, we własnej rewizji poprzedzającej.

## Refaktoryzacja a wydajność

Dwie dyscypliny, jedna kolejność:

- **Najpierw czytelność.** Domyślnym celem refaktoryzacji jest budowa
  zrozumiała; kod zrozumiały łatwiej zoptymalizować niż odwrotnie. Nie odrzucaj
  wydzielenia funkcji „bo wywołanie kosztuje” — w typowym kodzie usługowym
  koszt struktury jest niemierzalny wobec kosztów we/wy.
- **Optymalizacja wyłącznie po pomiarze.** Zanim zmienisz kod „dla wydajności”,
  zmierz profilerem lub testem obciążeniowym, **gdzie** jest koszt — intuicja
  wskazuje gorące miejsce błędnie zaskakująco często. Optymalizację prowadź jak
  refaktoryzację: siatka testów utrzymuje zachowanie, a pomiar przed/po
  (przytoczony w rewizji) dowodzi zysku. Optymalizacja bez pomiaru przed i po
  jest zmianą na wiarę.
- Gdy pomiar wykaże, że czytelna postać jest realnie za wolna w gorącym
  miejscu, wolno poświęcić czytelność **lokalnie** — z komentarzem wskazującym
  pomiar i powód, by następny czytelnik nie „poprawił” kodu z powrotem.

## Zapis refaktoryzacji w rewizjach

- **Osobno od zmian funkcjonalnych — zawsze.** Rewizja mieszana jest
  nieprzeglądalna: czytelnik nie odróżni przesunięcia kodu od zmiany logiki,
  a diff „przeniesiono i zmieniono” wygląda jak sto zmian zamiast dwóch.
  Sekwencja wzorcowa: rewizja przygotowawcza (refaktoryzacja) → rewizja
  funkcjonalna (mała, bo przygotowana) → ewentualna rewizja porządkująca.
- **Komunikat mówi „refaktoryzacja bez zmiany zachowania” i czym to poparte.**
  Wzór: pierwsza linia z przedrostkiem przyjętym w projekcie (np.
  `refactor: wydzielenie walidacji zamówienia do modułu orders/validation`),
  w treści — co przekształcono i dowód niezmienności zachowania: „testy
  jednostkowe modułu orders przechodzą bez modyfikacji testów” albo „zmiana
  mechaniczna narzędziem IDE, pełen zestaw testów zielony”. Deklaracja bez
  poparcia jest pustą etykietą.
- **Zmiany mechaniczne masowe** (formatowanie całego katalogu, zmiana nazwy
  w stu plikach, masowa zamiana importów) wydzielaj do własnych rewizji
  oznaczonych jako mechaniczne — przegląd takiej rewizji polega na sprawdzeniu
  polecenia, które ją wytworzyło, nie na czytaniu stu plików. Podaj to
  polecenie w komunikacie rewizji.
- Duża refaktoryzacja to seria małych rewizji, z których każda zostawia testy
  zielone — nigdy jedna rewizja „przebudowa modułu X” na trzy tysiące linii
  diffu. Granice rewizji pokrywają się z krokami rozbioru z sekcji o kolejności.
