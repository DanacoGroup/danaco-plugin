# C — karta

## Standard stylu i nazewnictwa

Stosuj jeden nazwany standard w całym projekcie i egzekwuj go narzędziami, nie recenzją ręczną:

- formatowanie: `clang-format` z jawnym plikiem `.clang-format` w korzeniu repozytorium (baza: styl
  `LLVM` lub styl jądra Linux — wybierz jeden i nie mieszaj);
- analiza statyczna: `clang-tidy` (włącz co najmniej grupy `bugprone-*`, `clang-analyzer-*`,
  `cert-*`) oraz `cppcheck`;
- w projektach o podwyższonych wymaganiach odwołuj się do SEI CERT C Coding Standard; w systemach
  krytycznych — MISRA C.

Konwencje nazewnicze:

- funkcje i zmienne: `snake_case`; makra i stałe preprocesora: `UPPER_SNAKE_CASE`;
- własne `typedef` z sufiksem `_t` tylko wtedy, gdy nie kolidują z nazwami zastrzeżonymi przez
  POSIX;
- publiczne API biblioteki prefiksuj nazwą modułu (np. `danaco_buffer_init`) — C nie ma przestrzeni
  nazw;
- nie rozpoczynaj identyfikatorów od podkreślenia: nazwy `_X` i `__x` są zarezerwowane dla
  implementacji;
- każdy nagłówek zabezpieczaj klasycznym include guardem (`#ifndef DANACO_BUFFER_H`); `#pragma once`
  stosuj tylko, gdy projekt jawnie go przyjął.

## Struktura projektu

Utrzymuj minimalny, kanoniczny układ; nie twórz katalogów „na zapas”:

```
projekt/
├── CMakeLists.txt
├── .clang-format
├── include/danaco/     # nagłówki publiczne (instalowane)
│   └── buffer.h
├── src/                # implementacja i nagłówki prywatne
│   └── buffer.c
└── tests/
    └── test_buffer.c
```

Nagłówki publiczne trzymaj wyłącznie w `include/<nazwa_projektu>/`, prywatne obok źródeł w `src/`.
Czego nie tworzyć:

- katalogów `utils/`, `common/`, `helpers/` bez konkretnej, spójnej zawartości;
- plików `.h` bez odpowiadającej im potrzeby API;
- równoległych systemów budowania (jednocześnie `Makefile` i `CMakeLists.txt`), jeżeli projekt tego
  nie wymaga.

## Budowa i zależności

Stosuj CMake jako domyślny system budowania; czysty `make` dopuszczaj tylko w małych,
jednoplatformowych projektach. Zasady:

- deklaruj standard jawnie: `set(CMAKE_C_STANDARD 17)` wraz z `CMAKE_C_STANDARD_REQUIRED ON` i
  `CMAKE_C_EXTENSIONS OFF`; domyślnie wybieraj C17 (poprawiona rewizja C11), C11 tylko gdy wymaga
  tego łańcuch narzędzi — nie pisz kodu w stylu C89 bez wymagania platformy;
- kompiluj zawsze z `-Wall -Wextra -Werror`, a tam gdzie kod na to pozwala, także `-Wconversion`;
- zależności systemowe wykrywaj przez `find_package` lub `pkg-config`;
- zależności źródłowe dołączaj przez `FetchContent` z przypiętym znacznikiem wydania lub pełnym
  hashem rewizji — nigdy przez gałąź `master`/`main`;
- rozdzielaj konfiguracje: `Debug` do pracy bieżącej, `RelWithDebInfo` do profilowania, `Release` do
  wydań.

## Testy

Stosuj jeden z uznanych frameworków: Unity, CMocka lub Check; CMocka wybieraj, gdy potrzebne są
atrapy (mocki) funkcji. Układ i praktyki:

- testy w `tests/`, po jednym pliku na testowany moduł (`test_buffer.c` dla `buffer.c`);
- rejestracja w CTest przez `add_test`; uruchamianie poleceniem `ctest --output-on-failure` z
  katalogu budowania;
- testuj przez publiczne API z `include/` — nie dołączaj plików `.c` do testów, żeby dostać się do
  funkcji `static`; jeżeli funkcja wymaga testu, wydziel ją do API wewnętrznego;
- w CI uruchamiaj testy dodatkowo w wariancie z sanitizerami (osobny katalog budowania).

## Diagnostyka

Debuguj przez `gdb` (na macOS `lldb`); buduj z `-g -O0`. Do analizy zrzutów rdzenia stosuj `gdb
./program core` oraz polecenia `bt`, `frame`, `info locals`. Narzędzia dynamiczne:

- `-fsanitize=address,undefined` w budowie deweloperskiej wykrywa przepełnienia buforów,
  use-after-free i niezdefiniowane zachowanie;
- `-fsanitize=thread` (osobna kompilacja, niełączona z ASan) wykrywa wyścigi danych;
- Valgrind (`valgrind --leak-check=full`) stosuj, gdy nie możesz przebudować z sanitizerami; jest
  wolniejszy i słabiej wykrywa błędy na stosie niż ASan;
- profilowanie: `perf record` / `perf report` na Linuksie, wyłącznie na budowie `RelWithDebInfo`.

Błędy konsolidatora czytaj dosłownie: `undefined reference` oznacza brak definicji symbolu (plik nie
wszedł do budowy albo zła kolejność bibliotek — biblioteki podawaj po plikach obiektowych);
`multiple definition` oznacza zwykle definicję zmiennej lub funkcji w nagłówku bez
`static`/`inline`. Typowe klasy błędów w C: naruszenia pamięci (przepełnienie bufora,
use-after-free, podwójne `free`), niezdefiniowane zachowanie (przepełnienie liczby ze znakiem, złe
specyfikatory `printf`), wycieki zasobów oraz wyścigi w kodzie wielowątkowym.

## Typowe błędy modeli LLM w tym języku

1. **Brak kontroli wyniku alokacji i operacji we/wy**: modele wywołują `malloc`, `fopen`, `fread`
   bez sprawdzenia wyniku, a wyłuskanie `NULL` to niezdefiniowane zachowanie, nie „wyjątek”.
   Sprawdzaj każdy zwrot:

```c
char *buf = malloc(len);
if (buf == NULL) {
    /* obsłuż błąd alokacji, nie kontynuuj */
    return -1;
}
```

2. **Niebezpieczne funkcje łańcuchowe**: `strcpy`, `sprintf`, `strcat`, a nawet `gets` (usunięte z
   języka w C11). Stosuj `snprintf` i warianty z jawnym rozmiarem bufora; przy `strncpy` pamiętaj,
   że nie gwarantuje terminatora `\0` — dopisuj go jawnie.
3. **Złe specyfikatory formatu**: nagminne `%d` dla `size_t` lub `long`. Stosuj `%zu` dla `size_t`,
   `%ld` dla `long`, makra `PRIu64` z `<inttypes.h>` dla typów o stałej szerokości; niezgodny
   specyfikator to niezdefiniowane zachowanie, nie tylko błędny wydruk.
4. **`char` zamiast `int` przy `getchar`/`fgetc`**: wynik tych funkcji musi trafiać do `int`,
   ponieważ `EOF` nie mieści się w `char`; porównanie `(char)c == EOF` bywa zawsze fałszywe albo
   błędnie prawdziwe zależnie od znakowości `char`.
5. **Zwracanie wskaźnika do zmiennej automatycznej**: `char buf[64]; ... return buf;` zwraca adres
   pamięci, która przestaje istnieć. Przekazuj bufor od wywołującego wraz z rozmiarem albo alokuj
   dynamicznie z udokumentowaną własnością pamięci.
6. **Bezwiedne niezdefiniowane zachowanie arytmetyczne**: przepełnienie `int` ze znakiem,
   przesunięcie o co najmniej szerokość typu, testy po przepełnieniu (`if (x + 1 < x)`) — kompilator
   ma prawo takie sprawdzenie usunąć. Sprawdzaj zakresy przed operacją lub używaj typów bez znaku ze
   świadomością ich zawijania modulo.
7. **`sizeof` na wskaźniku zamiast na obiekcie**: po zaniku tablicy do wskaźnika (parametr funkcji)
   `sizeof(arr)` zwraca rozmiar wskaźnika. Wzorzec `sizeof arr / sizeof arr[0]` działa tylko w
   zasięgu deklaracji tablicy; do funkcji przekazuj długość jawnie.
8. **Definicje w nagłówkach**: umieszczenie definicji zmiennej globalnej lub funkcji bez
   `static`/`inline` w pliku `.h` kończy się błędem `multiple definition` przy konsolidacji. W
   nagłówku deklaruj (`extern int counter;`), definiuj w dokładnie jednym pliku `.c`.
9. **Mieszanie stylów zwracania błędów**: w jednym module raz `0`/`-1`, raz kod `errno`, raz `NULL`.
   Przyjmij jedną konwencję dla całego API (np. `0` = sukces, ujemny kod = błąd) i dokumentuj ją
   przy każdej funkcji publicznej.
10. **Rzutowanie maskujące ostrzeżenia zamiast naprawy przyczyny**: rzutowanie `(int)` na wyniku
    `strlen` czy zdejmowanie `const` rzutowaniem ukrywa realną niezgodność typów. Popraw typy
    deklaracji zamiast uciszać kompilator.
