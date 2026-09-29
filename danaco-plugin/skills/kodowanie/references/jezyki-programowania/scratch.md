# Scratch — karta

Scratch jest językiem blokowym: program składa się ze skryptów zbudowanych z bloków, przypisanych do
duszków (sprite) i sceny. Karta zachowuje układ kart Danaco Code, a treść dostosowuje do specyfiki
środowiska blokowego. Bloki przywołuj polskimi nazwami z oficjalnej lokalizacji edytora Scratch;
nazwy własne (duszki, zmienne, komunikaty, bloki własne) zapisuj po angielsku, spójnie w całym
projekcie.

## Standard stylu i nazewnictwa

- Nadawaj duszkom nazwy opisowe (`Player`, `Enemy`, `ScoreDisplay`); nigdy nie zostawiaj domyślnych
  (`Duszek1`, `Sprite2`).
- Zmienne nazywaj rzeczownikowo (`score`, `livesLeft`, `gameState`); listy — w liczbie mnogiej
  (`highScores`). Rozróżniaj świadomie zasięg: „dla wszystkich duszków” tylko dla stanu wspólnego,
  „tylko dla tego duszka” dla stanu lokalnego (także dla klonów — każdy klon ma własne kopie
  zmiennych lokalnych).
- Komunikaty (bloki „nadaj […]”) nazywaj jak zdarzenia: `game-start`, `player-hit`,
  `level-complete`. Nie używaj domyślnej nazwy `wiadomość1`.
- Bloki własne (kategoria „Moje bloki”) nazywaj czasownikowo (`move player`, `draw bar`), z
  parametrami o jasnych nazwach; blok własny pełni w Scratchu rolę procedury.
- Utrzymuj porządek wizualny: skrypty jednego duszka rozmieszczaj w kolumnach tematycznych, bez
  nachodzenia na siebie; osierocone bloki (niepodpięte pod żaden kapelusz) usuwaj.
- Dodawaj komentarze (prawy przycisk na bloku → „dodaj komentarz”) przy skryptach o nieoczywistym
  działaniu; komentarze pisz po polsku.

## Struktura projektu

- Projekt zapisuj jako plik `.sb3` — jest to archiwum ZIP zawierające `project.json` (definicje
  sceny, duszków i skryptów) oraz zasoby multimedialne (kostiumy, tła, dźwięki). Nie edytuj
  `project.json` ręcznie bez ważnego powodu; źródłem prawdy jest edytor.
- Struktura logiczna projektu:
  - scena — tła, globalna muzyka, skrypty sterujące przebiegiem całości (np. zmiana poziomów);
  - duszki — po jednym na byt gry lub element interfejsu; każdy duszek zawiera własne kostiumy,
    dźwięki i skrypty;
  - skrypty — każdy zaczyna się blokiem kapeluszowym („kiedy kliknięto zieloną flagę”, „kiedy
    otrzymam […]”, „gdy zaczynam jako klon”).
- Jedna odpowiedzialność na skrypt: osobny skrypt do sterowania ruchem, osobny do reakcji na
  kolizje, osobny do inicjalizacji. Skrypty w różnych duszkach łącz komunikatami, nie duplikatami
  kodu.
- Do powielania bytów (pociski, przeciwnicy) używaj klonów („utwórz klona […]”, „gdy zaczynam jako
  klon”, „usuń tego klona”), nie kopii duszka.
- Czego nie tworzyć:
  - duszków-kopii różniących się wyłącznie skryptem (stosuj klony lub komunikaty);
  - zmiennych globalnych przechowujących stan jednego duszka;
  - skryptów-monolitów na kilkadziesiąt bloków bez bloków własnych;
  - nieużywanych kostiumów, teł i dźwięków zwiększających rozmiar pliku;
  - zmiennych i komunikatów o nazwach domyślnych lub jednoliterowych.

## Budowa i zależności

- Scratch nie ma etapu kompilacji ani menedżera pakietów; „budową” jest zapis projektu. Zapisuj
  regularnie do pliku `.sb3` („Plik → Zapisz na swoim komputerze”) i przechowuj kolejne wydania pod
  nazwami z numerem wersji (`game-v3.sb3`) — edytor nie prowadzi historii zmian.
- Fragmenty wielokrotnego użytku przenoś między projektami przez plecak (backpack) w edytorze online
  albo eksport duszka do pliku `.sprite3`.
- Rozszerzenia (Pióro, Muzyka, Tłumacz, czujniki wideo) dodawaj wyłącznie te, których projekt
  faktycznie używa; każde rozszerzenie zwiększa złożoność projektu.
- Zasoby zewnętrzne (grafiki, dźwięki) wprowadzaj przez edytor; dbaj o prawa autorskie do materiałów
  i o rozsądny rozmiar plików dźwiękowych.
- Jeżeli projekt ma działać w środowiskach pochodnych (np. TurboWarp), nie polegaj na zachowaniach
  specyficznych dla tych środowisk — projekt musi działać poprawnie w standardowym edytorze Scratch.

## Testy

- Scratch nie ma frameworka testów automatycznych — testuj przez scenariusze ręczne. Przed oddaniem
  projektu przygotuj i wykonaj listę kontrolną scenariuszy:
  - start zieloną flagą z zimnego stanu (świeżo wczytany projekt) i ponowny start bez przeładowania
    — oba muszą dawać ten sam rezultat;
  - ścieżka podstawowa każdej mechaniki (ruch, punktacja, kolizje, zmiana poziomu);
  - przypadki brzegowe: wartości skrajne zmiennych (0 żyć, maksymalny wynik), krawędzie sceny,
    szybkie wielokrotne naciskanie klawiszy, jednoczesne zdarzenia;
  - zakończenie gry i powrót do stanu początkowego.
- Sprawdzaj poprawność inicjalizacji: każdy skrypt startowy musi jawnie ustawiać pozycję, kostium,
  widoczność, rozmiar i zmienne — Scratch zapamiętuje stan z poprzedniego uruchomienia.
- Testuj bloki własne w izolacji: kliknij definicję lub tymczasowy skrypt wywołujący blok ze
  skrajnymi wartościami parametrów (0, wartości ujemne, wartości maksymalne) i obserwuj wynik na
  czujnikach zmiennych.
- Testuj logikę obliczeniową w przyspieszeniu: uruchom projekt w trybie turbo, aby szybko przejść
  długie sekwencje i ujawnić błędy kumulujące się w czasie.
- Po każdej istotnej zmianie wykonaj ponownie pełną listę scenariuszy, nie tylko scenariusz
  zmieniony.

## Diagnostyka

- Obserwuj stan przez czujniki zmiennych na scenie: zaznacz pole wyboru przy zmiennej, aby widzieć
  jej wartość na żywo; podczas diagnozy pokaż zmienne pomocnicze, po zakończeniu — ukryj je.
- Stosuj blok „powiedz […]” lub tymczasową zmienną `debugTrace` jako odpowiednik logowania: wypisuj
  wartości w punktach kontrolnych skryptu.
- Używaj trybu turbo (w edytorze: menu Edycja → „Włącz tryb turbo”) do przyspieszonego wykonywania
  pętli obliczeniowych; pamiętaj, że tryb turbo zmienia tempo, więc błędy zależne od czasu diagnozuj
  w trybie normalnym.
- Typowe klasy błędów:
  - stan resztkowy — projekt działa inaczej za drugim uruchomieniem, bo zmienne lub pozycje nie są
    resetowane w skrypcie startowym;
  - wyścigi między skryptami — wiele skryptów kapeluszowych rusza równolegle po zielonej fladze lub
    komunikacie; kolejność wymuszaj przez „nadaj […] i czekaj” oraz jawne komunikaty
    sekwencjonujące;
  - klony-sieroty — klony bez „usuń tego klona” kumulują się i spowalniają projekt (limit liczby
    klonów w Scratchu istnieje i po jego osiągnięciu nowe klony nie powstają);
  - krucha detekcja — „dotyka koloru […]” zawodzi przy zmianie palety kostiumu; preferuj „dotyka
    […]” z konkretnym duszkiem.
- Izoluj problem: odłącz skrypt od bloku kapeluszowego (skrypt odłączony można uruchomić
  kliknięciem), sprawdź fragment samodzielnie, po diagnozie podepnij z powrotem.

## Typowe błędy modeli LLM w tym języku

1. **Spaghetti bloków bez bloków własnych** — jeden skrypt na kilkadziesiąt bloków z powtórzonymi
   sekwencjami. Wydzielaj powtarzalne sekwencje do bloków własnych („Moje bloki”) z parametrami;
   skrypt główny ma czytać się jak lista kroków.
2. **Duplikowanie skryptów między duszkami zamiast komunikatów** — kopiowanie tej samej logiki do
   wielu duszków. Nadawaj komunikat, a każdy duszek reaguje własnym „kiedy otrzymam […]”; wspólne
   obliczenia trzymaj w jednym miejscu (scena lub duszek-kontroler).
3. **Zły zasięg zmiennych** — zmienna „dla wszystkich duszków” używana jako stan pojedynczego klona,
   przez co wszystkie klony nadpisują sobie wartość. Stan klona trzymaj w zmiennych „tylko dla tego
   duszka”; globalne rezerwuj dla wyniku, poziomu i stanu gry.
4. **Brak inicjalizacji po zielonej fladze** — pominięcie ustawienia pozycji, kostiumu, widoczności
   i zerowania zmiennych na starcie. Każdy duszek musi mieć skrypt startowy przywracający pełny stan
   początkowy, bo Scratch zachowuje stan z poprzedniego wykonania.
5. **Założenie sekwencyjności skryptów równoległych** — poleganie na tym, że skrypty uruchomione tym
   samym zdarzeniem wykonają się w określonej kolejności. Kolejność w Scratchu nie jest
   gwarantowana; sekwencję wymuszaj przez „nadaj […] i czekaj” albo łańcuch komunikatów.
6. **„nadaj” tam, gdzie potrzebne „nadaj i czekaj”** — skrypt kontynuuje pracę, zanim odbiorcy
   zakończą reakcję na komunikat, co daje wyścigi stanu. Używaj „nadaj […] i czekaj”, gdy dalsze
   kroki zależą od zakończenia obsługi komunikatu.
7. **Pętle odpytujące bez oczekiwania** — konstrukcja „zawsze → jeżeli klawisz naciśnięty” jest
   poprawna, ale zagnieżdżanie ciężkich obliczeń w „zawsze” bez bloków oczekiwania obciąża projekt.
   Tam, gdzie chodzi o jednorazową reakcję, stosuj „czekaj aż […]” lub blok kapeluszowy „kiedy
   klawisz […] naciśnięty”.
8. **Liczby magiczne w blokach** — współrzędne, prędkości i limity wpisane wprost w dziesiątkach
   miejsc. Trzymaj parametry rozgrywki w zmiennych ustawianych w skrypcie inicjalizacyjnym
   (`playerSpeed`, `maxLives`), aby strojenie wymagało jednej zmiany.
9. **Klony tworzone bez sprzątania** — „utwórz klona” w pętli bez ścieżki „usuń tego klona”. Każdy
   scenariusz życia klona musi kończyć się jego usunięciem; w przeciwnym razie projekt degraduje
   wydajnościowo i osiąga limit klonów.
10. **Opisy projektów niewykonalne w Scratchu** — proponowanie mechanizmów, których standardowy
    Scratch nie posiada (dostęp do plików, prawdziwe funkcje zwracające wartość — blok własny nie
    zwraca wartości, wynik przekazuj przez zmienną). Projektuj w granicach rzeczywistego zestawu
    bloków; możliwości rozszerzeń sprawdzaj przed użyciem.

Wzorzec poprawny — inicjalizacja i sekwencja startu (zapis słowny skryptu):

```text
kiedy kliknięto zieloną flagę            // duszek Player
ustaw [livesLeft] na (3)                 // pełny reset stanu
przejdź do x: (-180) y: (0)
zmień kostium na [idle]
pokaż
nadaj [game-start] i czekaj              // dopiero potem rusza rozgrywka
```

Wzorzec poprawny — cykl życia klona (zapis słowny skryptu):

```text
gdy zaczynam jako klon                   // duszek Bullet
pokaż
powtarzaj aż [dotyka (Enemy)? lub dotyka (krawędź)?]
  zmień x o (bulletSpeed)                // bulletSpeed: zmienna, nie liczba wpisana wprost
usuń tego klona                          // każda ścieżka kończy się usunięciem klona
```
