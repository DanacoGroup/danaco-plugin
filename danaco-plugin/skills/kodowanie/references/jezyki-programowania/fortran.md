# Fortran — karta

Karta dotyczy współczesnego Fortranu (norma ISO/IEC 1539-1; wydania potocznie zwane
Fortran 90/95/2003/2008/2018/2023). Pisz wyłącznie w formacie swobodnym (free form),
z modułami i jawną typizacją. Zastany FORTRAN 77 (format stały, kolumny 7–72)
traktuj jako kod odziedziczony: czytaj go, ale nie powielaj jego stylu w nowym kodzie.

## Standard stylu i nazewnictwa

- Stosuj format swobodny: pliki z rozszerzeniem `.f90` (konwencjonalnie także dla nowszych
  wydań normy), bez znaczenia kolumn, kontynuacja wiersza znakiem `&`.
- Rozpoczynaj każdą jednostkę programową od `implicit none`. Nigdy nie polegaj na
  niejawnej typizacji (reguła I–N dla liczb całkowitych to relikt FORTRAN-u).
- Nazwy pisz małymi literami ze znakiem podkreślenia: `compute_flux`, `grid_size`.
  Fortran nie rozróżnia wielkości liter — nie twórz nazw różniących się tylko nią.
- Deklaruj rodzaje liczb przez stałe z modułu wbudowanego `iso_fortran_env`
  (`real64`, `int32`), a nie przez niestandardowe zapisy `real*8` czy `double precision`.
- Deklaruj `intent(in)`, `intent(out)` lub `intent(inout)` dla każdego argumentu procedury.
- Stosuj operatory `==`, `/=`, `<=` zamiast archaicznych `.eq.`, `.ne.`, `.le.`.
- Zamykaj konstrukcje pełnymi końcówkami: `end do`, `end if`, `end function compute_flux`.
- Nie używaj: `goto`, `common`, `equivalence`, instrukcji `entry`, arytmetycznego `if`,
  funkcji statement function. Wszystkie mają współczesne zamienniki (moduły, typy pochodne).

```fortran
module flux_mod
   use iso_fortran_env, only: real64
   implicit none
   private
   public :: compute_flux
contains
   pure function compute_flux(density, velocity) result(flux)
      ! Strumień masy: iloczyn gęstości i prędkości
      real(real64), intent(in) :: density, velocity
      real(real64) :: flux
      flux = density * velocity
   end function compute_flux
end module flux_mod
```

## Struktura projektu

- Grupuj kod w modułach; jeden moduł na plik, nazwa pliku zgodna z nazwą modułu.
- Program główny trzymaj osobno; logikę umieszczaj w procedurach modułowych, aby były
  testowalne i miały jawne interfejsy sprawdzane przez kompilator.
- Ogranicz widoczność: `private` jako domyślne w module, `public` tylko dla API.
- Układ zgodny z konwencją fpm: `src/` (moduły), `app/` (programy), `test/` (testy),
  manifest `fpm.toml` w katalogu głównym.
- W projektach mieszanych oddzielaj zastane pliki `.f`/`.for` (format stały) od nowych
  `.f90`; nie konwertuj ich hurtowo bez testów regresyjnych.

## Budowa i zależności

- Preferuj fpm (Fortran Package Manager): `fpm build`, `fpm run`, `fpm test`;
  zależności deklaruj w `fpm.toml`.
- Przy bezpośrednim wywołaniu gfortran pamiętaj o kolejności kompilacji: moduł musi być
  skompilowany przed jednostką, która go używa (powstają pliki `.mod`).
- Standardowe flagi rozwojowe gfortran: `-std=f2018 -Wall -Wextra -Werror=implicit-interface`.
- Alternatywne kompilatory (ifx/ifort, flang) różnią się flagami i formatem plików `.mod`
  — nie mieszaj obiektów z różnych kompilatorów w jednym programie.
- Do większych systemów budowania stosuj CMake z włączoną obsługą języka Fortran.

## Testy

- Stosuj pFUnit — framework testów jednostkowych dla Fortranu (asercje, parametryzacja,
  integracja z CMake i MPI). Testy pisz w plikach `.pf` przetwarzanych preprocesorem pFUnit.
- W projektach fpm prostą alternatywą są programy testowe w `test/` uruchamiane przez
  `fpm test`, kończone `error stop` przy niespełnionej asercji.
- Porównuj liczby zmiennoprzecinkowe z tolerancją względną lub bezwzględną, nigdy przez `==`.
- Testuj procedury `pure`/`elemental` w pierwszej kolejności — brak efektów ubocznych
  upraszcza przypadki testowe.

## Diagnostyka

- Kompiluj wersje diagnostyczne z: `-g -O0 -fcheck=all -fbacktrace
  -ffpe-trap=invalid,zero,overflow -finit-real=snan` (gfortran). `-fcheck=all` wykrywa
  wyjścia poza zakres tablic i błędy alokacji w czasie wykonania.
- Debuguj przez gdb; gfortran generuje standardowe informacje DWARF, a `-fbacktrace`
  wypisuje ślad stosu przy błędzie wykonania.
- Czytaj komunikaty o niezgodności interfejsów: „Type mismatch in argument” najczęściej
  oznacza wywołanie procedury bez jawnego interfejsu — przenieś ją do modułu.
- Sprawdzaj status operacji We/Wy i alokacji: `iostat=`, `iomsg=`, `stat=`, `errmsg=`;
  bez nich błąd kończy program bez kontekstu.

## Typowe błędy modeli LLM w tym języku

1. Mieszanie FORTRAN 77 ze współczesnym Fortranem: wstawianie `C` w pierwszej kolumnie
   jako komentarza, etykiet numerycznych z `continue`, pętli `do 10 i=1,n`. W formacie
   swobodnym komentarz to `!`, a pętlę zamyka `end do`.
2. Pominięcie `implicit none` — literówka w nazwie zmiennej tworzy wtedy nową zmienną
   o niejawnym typie zamiast błędu kompilacji. Wstawiaj `implicit none` w każdym module
   i programie bez wyjątku.
3. Niestandardowe deklaracje rodzaju: `real*8`, `integer*4`. Poprawny wzorzec:
   `use iso_fortran_env, only: real64` i `real(real64) :: x`.
4. Założenie indeksowania od zera i porządku wierszowego tablic. Domyślny dolny indeks
   to 1, a tablice są kolumnowe (column-major): w pętlach zagnieżdżonych najszybciej
   zmieniaj pierwszy indeks (`do j ... do i ... a(i, j)`).
5. Deklarowanie procedur jako zewnętrznych (external) zamiast modułowych — kompilator
   traci możliwość sprawdzenia zgodności argumentów. Umieszczaj procedury w modułach
   albo po `contains` w programie.
6. Brak `intent` przy argumentach oraz modyfikowanie argumentu wejściowego. Deklaruj
   `intent(in)` domyślnie; kompilator wychwyci wtedy przypadkowy zapis.
7. Traktowanie `character(len=n)` jak łańcuchów o zmiennej długości: porównania i wypisy
   uwzględniają dopełniające spacje. Stosuj `trim()` przy porównaniach i wypisywaniu
   oraz `character(len=:), allocatable` dla długości ustalanej w locie.
8. Dzielenie całkowite w wyrażeniach rzeczywistych: `1/2` daje `0`. Zapisuj literały
   rzeczywiste z rodzajem: `1.0_real64/2.0_real64`.
9. Zapominanie o dealokacji lub ponowna alokacja bez sprawdzenia `allocated()`;
   przy przypisaniu do tablicy `allocatable` korzystaj z automatycznej realokacji
   zamiast ręcznego cyklu deallocate/allocate.
10. Halucynowane procedury wbudowane lub przypisywanie rozszerzeń kompilatora normie
    (np. traktowanie `getarg` jako standardu). Standardowe odpowiedniki to
    `get_command_argument` i `command_argument_count`; w razie wątpliwości sprawdź
    kompilację z `-std=f2018`.
