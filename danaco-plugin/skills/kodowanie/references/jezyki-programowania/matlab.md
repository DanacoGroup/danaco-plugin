# Matlab — karta

## Standard stylu i nazewnictwa

MATLAB nie ma jednego oficjalnego dokumentu stylu rangi PEP 8 — stosuj konwencje MathWorks widoczne
w dokumentacji i toolboxach oraz zalecenia wbudowanego Code Analyzer. Egzekwuj konwencje nazewnicze:

- funkcje i zmienne: `camelCase` (np. `computeSignalPower`, `sampleRate`); nazwa funkcji musi być
  identyczna z nazwą pliku (`computeSignalPower.m`);
- klasy: `PascalCase` w plikach `classdef` (np. `SignalProcessor.m`);
- pakiety przestrzeni nazw: katalogi z przedrostkiem `+` małymi literami (np. `+danaco`);
- stałe: metody statyczne klasy stałych lub zmienne `UPPER_SNAKE_CASE` w wąskim zakresie — zgodnie z
  konwencją projektu.

Każdą funkcję opatruj komentarzem pomocy H1 bezpośrednio pod sygnaturą (pierwsza linia widoczna w
`help` i `lookfor`). Waliduj argumenty blokiem `arguments` (R2019b+):

```matlab
function power = computeSignalPower(signal, sampleRate)
    arguments
        signal (1, :) double          % wektor wierszowy próbek
        sampleRate (1, 1) double {mustBePositive}
    end
    % ... dalsza logika funkcji
end
```

Do kontroli jakości stosuj Code Analyzer w edytorze oraz `checkcode` z linii poleceń; nie zostawiaj
w kodzie niewyjaśnionych ostrzeżeń, a tłumienia (`%#ok`) stosuj tylko z uzasadnieniem.

## Struktura projektu

Rozróżniaj trzy formy kodu: skrypty (sekwencje poleceń, tylko do eksploracji i orkiestracji),
funkcje (jednostka wielokrotnego użytku z jawnymi wejściami i wyjściami — domyślna forma kodu
produkcyjnego) oraz klasy `classdef` (stan i zachowanie). Minimalny profesjonalny układ, spinany
przez MATLAB Project (plik `.prj`):

```
project/
├── MyProject.prj         # definicja projektu: ścieżki, skróty, zależności
├── src/
│   └── +danaco/          # pakiet przestrzeni nazw z funkcjami i klasami
│       ├── computeSignalPower.m
│       └── @SignalProcessor/   # katalog klasy z wieloma plikami metod
├── tests/
│   └── ComputeSignalPowerTest.m
├── scripts/              # skrypty uruchomieniowe i eksploracyjne
└── data/
```

Kanoniczne jest zarządzanie ścieżką przez MATLAB Project, nie przez `addpath` rozsiane po skryptach.
Czego nie tworzyć: wielkich skryptów operujących na współdzielonym obszarze roboczym zamiast
funkcji, kopii plików w stylu `analysis_v2_final.m`, ani zależności od ręcznie ustawianej ścieżki
użytkownika. Funkcje lokalne umieszczaj pod funkcją główną w tym samym pliku; katalog `private/`
stosuj dla funkcji pomocniczych ograniczonych do katalogu nadrzędnego.

## Budowa i zależności

Zależnościami są przede wszystkim toolboxy MathWorks — przed użyciem funkcji sprawdź, do którego
toolboxa należy (nagłówek strony dokumentacji) i czy projekt ma do niego licencję (`ver`,
`license('test', ...)`). Wymagane produkty i pliki ustal narzędziem
`matlab.codetools.requiredFilesAndProducts`. Zasady:

- nie wprowadzaj zależności od toolboxa dla funkcjonalności osiągalnej w podstawowym MATLAB-ie bez
  wyraźnej potrzeby;
- kod współdzielony między projektami pakuj jako toolbox (`.mltbx`) lub dołączaj jako projekt
  odwołany (referenced project);
- automatyzację buduj przez `buildtool` z plikiem `buildfile.m` (R2022b+); starsze projekty mogą
  używać własnych skryptów — sprawdź konwencję projektu;
- uruchamianie wsadowe: `matlab -batch "nazwa_zadania"` w CI, nie tryb interaktywny;
- minimalną wersję MATLAB-a zapisuj w ustawieniach projektu i README; składnię nowszą niż wymagana
  wersja odrzucaj.

## Testy

Stosuj wbudowany framework matlab.unittest. Preferuj testy klasowe (`classdef ... <
matlab.unittest.TestCase`) z metodami w bloku `methods (Test)`; testy funkcyjne i skryptowe akceptuj
w mniejszych projektach. Praktyki:

- pliki testowe z przyrostkiem `Test` w katalogu `tests/` objętym ścieżką projektu;
- asercje kwalifikowane: `verifyEqual` (z parametrami `AbsTol`/`RelTol` dla liczb
  zmiennoprzecinkowych), `verifyError`, `verifySize`, `verifyClass`;
- przygotowanie i sprzątanie w blokach `TestMethodSetup`/`TestClassSetup` oraz przez `addTeardown`;
- parametryzację realizuj właściwościami w bloku `properties (TestParameter)`.

Uruchamiaj: `runtests` (bieżący katalog lub wskazany), `runtests("tests", IncludeSubfolders=true)`
dla całości; w CI — `matlab -batch "assertSuccess(runtests(...))"` lub zadanie testowe `buildtool`.
Nigdy nie porównuj wyników zmiennoprzecinkowych przez `isequal` bez tolerancji.

## Diagnostyka

Debugowanie: punkty przerwania w edytorze lub `dbstop in file at line`; `dbstop if error` zatrzymuje
wykonanie w miejscu nieprzechwyconego błędu z pełnym dostępem do obszaru roboczego (`dbup`/`dbdown`
do poruszania się po ramkach, `dbquit` na koniec). Profilowanie: `profile on; ...; profile viewer` —
analizuj czas własny funkcji i liczbę wywołań przed jakąkolwiek optymalizacją. Błędy zgłaszaj przez
`error("Danaco:computeSignalPower:invalidInput", ...)` z identyfikatorem komunikatu; przechwytuj
przez `try`/`catch ME` i analizuj `ME.identifier` oraz `ME.stack`. Ślad błędu czytaj od pierwszej
pozycji `Error in ... (line N)` — to najgłębsza ramka; kolejne pozycje pokazują łańcuch wywołań.

Typowe klasy błędów i ich rozpoznanie:

- `Index exceeds the number of array elements` / `Index in position ... exceeds array bounds` —
  indeks poza zakresem; pamiętaj o indeksowaniu od 1;
- `Unrecognized function or variable` — literówka, plik poza ścieżką projektu lub brak toolboxa;
- `Matrix dimensions must agree` / `Arrays have incompatible sizes` — niezgodność wymiarów; sprawdź
  orientację wektorów (wiersz vs kolumna) i reguły rozszerzania niejawnego;
- `Undefined function ... for input arguments of type 'cell'` — brak indeksacji zawartości: `c{1}`
  (zawartość) zamiast `c(1)` (podtablica komórkowa).

## Typowe błędy modeli LLM w tym języku

1. **Indeksowanie od zera i idiomy Pythona**: MATLAB indeksuje od 1, `x(end)` oznacza ostatni
   element, a indeksy ujemne nie istnieją. Zapis `x(0)` lub `x(-1)` jest zawsze błędem.
2. **Mylenie operatorów macierzowych i elementowych**: `*`, `/`, `^` to operacje macierzowe; dla
   działań element po elemencie stosuj `.*`, `./`, `.^`. Dla wektorów o tej samej długości `a * b`
   zwykle kończy się błędem wymiarów lub — gorzej — cichym iloczynem zewnętrznym/skalarnym.
3. **Rozrastanie tablic w pętli bez prealokacji**: degraduje wydajność kwadratowo. Poprawny wzorzec:

```matlab
n = numel(inputSignals);
results = zeros(n, 1);    % prealokacja przed pętlą
for k = 1:n
    results(k) = computeSignalPower(inputSignals{k});
end
```

4. **Pętle tam, gdzie kanoniczna jest wektoryzacja**: sumy, maski logiczne i operacje na całych
   tablicach zapisuj wektorowo (`total = sum(x(x > threshold))`), nie przez `for` z akumulatorem.
5. **Porównywanie tekstu przez `==`**: dla tablic znakowych `==` porównuje znak po znaku i wymaga
   równych długości. Stosuj `strcmp`/`strcmpi` albo łańcuchy w cudzysłowach podwójnych (`string`),
   pamiętając, że `'abc'` (char) i `"abc"` (string) to różne typy — nie mieszaj ich w jednym API.
6. **`i` oraz `j` jako zmienne pętli**: przesłaniają jednostkę urojoną i psują kod zespolony. Stosuj
   `k`, `idx` lub nazwy opisowe; jednostkę urojoną zapisuj jako `1i`.
7. **`clear all`, `clc`, `close all` wewnątrz funkcji**: niszczą stan wywołującego i spowalniają
   wykonanie. Te polecenia są dopuszczalne co najwyżej na początku skryptu eksploracyjnego, nigdy w
   kodzie wielokrotnego użytku.
8. **Halucynowane funkcje toolboxów**: wymyślone nazwy lub użycie funkcji z toolboxa, którego
   projekt nie posiada. Sprawdź istnienie funkcji (`which -all nazwa`, `exist("nazwa")`) i jej
   przynależność produktową w dokumentacji, zanim jej użyjesz.
9. **Poleganie na niejawnym wyjściu `ans` i skryptowym stanie globalnym**: zwracaj wartości przez
   jawne argumenty wyjściowe funkcji; nie używaj `global` ani `evalin`/`assignin` do przekazywania
   danych.
10. **`eval` do budowania nazw zmiennych** (`eval(['data' num2str(k) ' = ...'])`): antywzorzec
    uniemożliwiający analizę statyczną. Stosuj tablice komórkowe, struktury z polami dynamicznymi
    (`s.(fieldName)`) lub tablice `table`.
