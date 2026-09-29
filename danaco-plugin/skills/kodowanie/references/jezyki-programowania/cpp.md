# C++ — karta

## Standard stylu i nazewnictwa

Stosuj C++ Core Guidelines (Stroustrup/Sutter) jako nadrzędny standard projektowy; w kwestiach
czysto redakcyjnych dopuszczalny jest Google C++ Style Guide, o ile projekt przyjął go jawnie. Nie
mieszaj obu w jednym repozytorium. Narzędzia przyjęte zawodowo:

- formatowanie: `clang-format` z plikiem `.clang-format` w korzeniu repozytorium — format wymuszaj w
  CI, nie ręcznie;
- analiza statyczna: `clang-tidy` z włączonymi co najmniej grupami `bugprone-*`, `modernize-*`,
  `performance-*`, `cppcoreguidelines-*`; dodatkowo `cppcheck` jako drugie sito.

Konwencje nazewnicze i zakazy stylistyczne:

- typy w `PascalCase` lub `snake_case` (jedna konwencja na projekt — wzorem biblioteki standardowej
  albo przewodnika Google); funkcje i zmienne konsekwentnie w `snake_case` bądź `camelCase` zgodnie
  z przyjętym przewodnikiem;
- stałe przez `constexpr`, nie przez makra; makra wyłącznie `UPPER_SNAKE_CASE` i tylko tam, gdzie
  preprocesor jest niezbędny;
- żadnego `using namespace std;` w nagłówkach ani w zasięgu globalnym plików źródłowych;
- żadnych rzutowań w stylu C — stosuj `static_cast`, `const_cast`, `reinterpret_cast` z jawną
  intencją.

## Struktura projektu

Kanoniczny minimalny układ biblioteki lub usługi:

```
projekt/
├── CMakeLists.txt
├── .clang-format
├── .clang-tidy
├── include/danaco/      # nagłówki publiczne
│   └── parser.hpp
├── src/                 # implementacja i nagłówki prywatne
│   └── parser.cpp
├── tests/
│   └── parser_test.cpp
└── cmake/               # własne moduły CMake (tylko gdy istnieją)
```

Jeden nagłówek publiczny odpowiada jednej spójnej jednostce API. Czego nie tworzyć:

- katalogów `common/`, `misc/`, `utils/` pełniących rolę zsypu;
- pustych klas i plików nagłówkowych „na przyszłość”;
- hierarchii dziedziczenia tam, gdzie wystarczy kompozycja lub zwykła funkcja wolna.

## Budowa i zależności

Stosuj CMake z podejściem target-centrycznym: `target_compile_features(parser PUBLIC cxx_std_20)`,
`target_include_directories`, `target_link_libraries`. Nie ustawiaj globalnych flag przez
`CMAKE_CXX_FLAGS`, gdy wystarczy właściwość celu. Zasady:

- standard języka deklaruj jawnie: domyślnie C++20, C++17 gdy wymaga tego łańcuch narzędzi klienta;
  wyłącz rozszerzenia (`CXX_EXTENSIONS OFF`);
- kompiluj z `-Wall -Wextra -Werror` (MSVC: `/W4 /WX /permissive-`);
- zależnościami zarządzaj menedżerem pakietów: vcpkg (tryb manifestu `vcpkg.json` z polem
  `builtin-baseline`) lub Conan (`conanfile.py`/`conanfile.txt` z lockfile); wersje przypinaj w
  manifeście;
- `FetchContent` stosuj z pełnym hashem rewizji lub znacznikiem wydania, nigdy z nazwą gałęzi;
- konfiguracje budowania rozdzielaj katalogami (`build/debug`, `build/release`); do wydań stosuj
  `Release` lub `RelWithDebInfo`.

## Testy

Stosuj GoogleTest (z GoogleMock) jako domyślny standard branżowy; Catch2 lub doctest wtedy, gdy
projekt już je przyjął. Układ i praktyki:

- testy w `tests/`, plik `parser_test.cpp` dla `parser.cpp`; integracja z CTest przez
  `gtest_discover_tests`;
- uruchamianie: `ctest --output-on-failure` z katalogu budowania; pojedynczy przypadek filtruj
  `--gtest_filter=ParserTest.HandlesEmptyInput`;
- testuj zachowanie przez API publiczne; atrapy wstrzykuj przez interfejsy (klasy abstrakcyjne) lub
  szablony, nie przez podmianę symboli przy konsolidacji;
- w CI utrzymuj osobny wariant budowania testów z ASan/UBSan.

## Diagnostyka

Debuguj przez `gdb` lub `lldb`; buduj `-g -O0`, a w razie awarii produkcyjnej analizuj zrzut rdzenia
(`bt`, `frame`, `print`). Narzędzia dynamiczne:

- `-fsanitize=address,undefined` w każdej budowie deweloperskiej; `-fsanitize=thread` w osobnej
  budowie do wykrywania wyścigów (nie łącz TSan z ASan);
- Valgrind memcheck, gdy przebudowa z sanitizerami jest niemożliwa;
- profilowanie: `perf` na Linuksie, Instruments na macOS — wyłącznie na budowach zoptymalizowanych z
  symbolami.

Błędy kompilatora czytaj od pierwszego komunikatu — kolejne są zwykle lawiną wtórną. W błędach
szablonowych szukaj wiersza `required from here` i właściwej klauzuli `note:`; komunikaty
koncepcyjne C++20 wskazują wprost niespełnione wymaganie. Błędy konsolidatora: `undefined reference`
— brak definicji (nie dołączono pliku lub biblioteki, zła kolejność bibliotek, brak instancjacji
szablonu w jednostce translacji); `multiple definition` — złamanie ODR, zwykle definicja w nagłówku
bez `inline`. Typowe klasy błędów: naruszenia pamięci (wiszące referencje, unieważnione iteratory),
niezdefiniowane zachowanie (przepełnienie ze znakiem, dostęp poza zakres), wyścigi danych przy
współdzielonym stanie bez synchronizacji.

## Typowe błędy modeli LLM w tym języku

1. **Surowe `new`/`delete` zamiast RAII**: ręczne zarządzanie pamięcią rodem z lat
   dziewięćdziesiątych. Stosuj `std::unique_ptr` i `std::make_unique`; `delete` w kodzie
   aplikacyjnym to sygnał błędu projektowego, a `std::shared_ptr` wybieraj tylko przy rzeczywiście
   współdzielonej własności, nie „na wszelki wypadek”.
2. **Przekazywanie ciężkich obiektów przez wartość bez potrzeby**: `void process(std::string s)`
   tam, gdzie wystarczy `const std::string&` lub `std::string_view`. Odwrotnie: gdy funkcja
   przejmuje własność, przyjmuj przez wartość i przenoś (`std::move`).
3. **Wiszący `std::string_view` i wiszące referencje**: zwracanie `string_view` do tymczasowego
   `std::string` albo przechowywanie w polu klasy referencji do wyniku wyrażenia tymczasowego.
   `string_view` nie posiada danych — nie może przeżyć obiektu źródłowego.
4. **`std::map::operator[]` do odczytu**: wywołanie `m[key]` wstawia element domyślny, gdy klucza
   brak, i wymaga niestałej mapy. Do odczytu stosuj `find` lub `at`; w C++20 do sprawdzenia
   obecności — `contains`.
5. **Unieważnianie iteratorów podczas modyfikacji kontenera**: usuwanie z `std::vector` w pętli
   zakresowej lub `push_back` w trakcie iteracji. Poprawny wzorzec:

```cpp
// usunięcie elementów spełniających warunek bez unieważniania iteracji
std::erase_if(values, [](int v) { return v < 0; });          // C++20
values.erase(std::remove_if(values.begin(), values.end(),
                            [](int v) { return v < 0; }),
             values.end());                                  // C++17
```

6. **Złamanie reguły pięciu/zera**: dopisany destruktor zwalniający zasób bez usunięcia lub
   zdefiniowania operacji kopiowania prowadzi do podwójnego zwolnienia. Preferuj regułę zera (zasoby
   wyłącznie w typach RAII); jeżeli definiujesz jedną operację specjalną, rozstrzygnij wszystkie
   pięć.
7. **API spoza zadeklarowanego standardu**: `std::string::contains` (C++23), `std::format` i
   `std::ranges` (C++20) w projekcie C++17 albo halucynowane metody kontenerów. Sprawdź wymagany
   standard w `CMakeLists.txt`, zanim użyjesz nowego API; przy niepewności co do sygnatury sprawdź
   dokumentację zamiast zgadywać.
8. **`std::endl` w każdym wierszu**: wymusza opróżnienie bufora i degraduje wydajność we/wy. Stosuj
   `'\n'`; opróżniaj jawnie (`std::flush`) tylko tam, gdzie to konieczne.
9. **Lambdy przechwytujące przez referencję poza czas życia zasięgu**: przekazanie `[&]` do
   `std::thread`, `std::async` lub kolejki zadań, gdy lambda wykona się po zakończeniu funkcji.
   Przechwytuj przez wartość lub przenoś własność do lambdy (`[data = std::move(data)]`).
10. **Wyłapywanie wyjątków przez wartość i puste `catch (...)`**: łapanie przez wartość tnie obiekt
    wyjątku (slicing), a puste `catch` połyka błędy. Łap przez `const std::exception&`, obsługuj
    albo propaguj dalej — nigdy nie wyciszaj bez logowania.
