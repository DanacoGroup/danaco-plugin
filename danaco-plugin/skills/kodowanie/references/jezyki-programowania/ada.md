# Ada — karta

Karta dotyczy języka Ada według normy ISO/IEC 8652 (wydania potocznie zwane Ada 95,
Ada 2005, Ada 2012, Ada 2022). Domyślnie pisz w Adzie 2012 lub nowszej, z aspektami
kontraktowymi (`Pre`, `Post`, `Type_Invariant`). Dla kodu o podwyższonych wymaganiach
niezawodności rozważ SPARK — formalnie zdefiniowany podzbiór Ady poddający się
weryfikacji statycznej narzędziem GNATprove (dowody braku błędów wykonania).

## Standard stylu i nazewnictwa

- Stosuj konwencję Mixed_Case z podkreśleniami: `Compute_Checksum`, `Max_Buffer_Size`.
  Słowa kluczowe pisz małymi literami. Ada nie rozróżnia wielkości liter, ale konwencja
  jest jednolita w całej bibliotece standardowej — nie odstępuj od niej.
- Rozróżniaj przypisanie `:=` od porównania `=`. Nie istnieje operator `==`.
- Modeluj dziedzinę typami: definiuj typy pochodne i podtypy z zakresami
  (`subtype Percent is Integer range 0 .. 100;`) zamiast używać gołego `Integer`
  do wszystkiego. Silna typizacja Ady wykrywa pomieszanie jednostek w kompilacji.
- Preferuj `with` bez `use`; kwalifikuj nazwy (`Ada.Text_IO.Put_Line`). Klauzulę `use`
  ograniczaj do wąskich zakresów lub stosuj `use type` dla samych operatorów.
- Nazywaj pętle i bloki, gdy są zagnieżdżone (`Outer : loop ... end loop Outer;`).
- Kończ jednostki powtórzoną nazwą: `end Compute_Checksum;`.

```ada
--  Specyfikacja pakietu: kontrakt widoczny dla klientów
package Checksums is
   type Byte is mod 2 ** 8;
   type Byte_Array is array (Positive range <>) of Byte;

   function Compute_Checksum (Data : Byte_Array) return Byte
     with Pre => Data'Length > 0;  --  Warunek wstępny sprawdzany w trybie asercji
end Checksums;
```

## Struktura projektu

- Dziel kod na pakiety: specyfikacja w pliku `.ads`, ciało w pliku `.adb`. W konwencji
  GNAT nazwa pliku odpowiada nazwie jednostki małymi literami, z kropkami zastąpionymi
  myślnikami (`Checksums.CRC` → `checksums-crc.ads`).
- Umieszczaj w specyfikacji wyłącznie to, co potrzebne klientom; szczegóły ukrywaj
  w części prywatnej (`private`) lub w ciele pakietu.
- Układ projektu Alire: manifest `alire.toml`, źródła w `src/`, testy w osobnym
  podprojekcie (crate) testowym; budowę opisuje plik projektu GNAT `.gpr`.
- Pakiety potomne (`Parent.Child`) służą do rozrastania API bez łamania klientów.

## Budowa i zależności

- Stosuj Alire (polecenie `alr`) jako menedżer zależności i środowisk: `alr init`,
  `alr with <crate>`, `alr build`, `alr run`. Alire pobiera i konfiguruje toolchain GNAT.
- Kompilator GNAT (front-end GCC) buduje przez gprbuild sterowany plikiem `.gpr`;
  tam deklaruj katalogi źródeł, flagi i warianty konfiguracji.
- Flagi rozwojowe GNAT: `-gnatwa` (szerokie ostrzeżenia), `-gnata` (włączenie asercji
  i kontraktów), `-gnato` (kontrola przepełnień), `-g -O0` do debugowania.
- Sprawdzaj dostępność biblioteki w indeksie Alire (`alr search`) zamiast zakładać jej
  istnienie; ekosystem crate'ów Ady jest znacznie mniejszy niż npm czy PyPI.
- Dla kodu SPARK uruchamiaj GNATprove jako etap budowy; poziom dowodzenia dobieraj
  do budżetu czasowego (tryby `check`, `flow`, `prove`).

## Testy

- Stosuj AUnit — framework testów jednostkowych dla Ady (dostępny jako crate w Alire):
  przypadki testowe jako typy pochodne od `Test_Case`/`Test_Fixture`, zestawy `Suite`,
  asercje przez `Assert`.
- Włączaj kontrakty w testach (`-gnata`): warunki `Pre`/`Post` działają wtedy jak
  wykonywalne asercje i wykrywają błędne użycia API bez pisania osobnych przypadków.
- Testuj wartości brzegowe podtypów (`'First`, `'Last`) oraz oczekiwane wyjątki
  (`Constraint_Error` przy naruszeniu zakresu).
- W kodzie SPARK część własności zastępuj dowodami GNATprove zamiast testami —
  udowodniona nieobecność przepełnień nie wymaga testów losowych w tym zakresie.

## Diagnostyka

- Debuguj przez gdb; GNAT generuje pełne informacje o typach Ady. Przy wyjątkach
  nieobsłużonych czytaj komunikat runtime'u z nazwą wyjątku i miejscem zgłoszenia;
  ślad symboliczny uzyskasz z `-g` oraz (w GNAT) opcją wiązania `-E` i funkcjami
  z `Ada.Exceptions` / `GNAT.Traceback.Symbolic`.
- `Constraint_Error` to najczęstszy wyjątek: naruszenie zakresu, indeksu lub dzielenie
  przez zero. Komunikat wskazuje plik i wiersz — nie tłum wyjątku pustym handlerem,
  tylko usuń przyczynę lub zawęź typ.
- Czytaj ostrzeżenia `-gnatwa` w całości; GNAT wskazuje m.in. zmienne nieużywane,
  podejrzane konwersje i martwy kod. Traktuj ostrzeżenia jak błędy w CI.
- Błędy elaboracji („access before elaboration”) rozwiązuj aspektami/pragmami
  `Elaborate_All` lub przebudową zależności między pakietami, nie próbami losowej
  zmiany kolejności kompilacji.

## Typowe błędy modeli LLM w tym języku

1. Halucynowanie pakietów bibliotecznych — wymyślone jednostki potomne `Ada.*` lub
   `GNAT.*` albo crate'y nieobecne w indeksie Alire. Sprawdzaj istnienie jednostki
   w normie (Annex A) lub przez `alr search`; gdy pewności brak, napisz własną
   procedurę zamiast importować fikcyjną.
2. Składnia z języków C-podobnych: `==` zamiast `=`, `!=` zamiast `/=`, nawiasy
   klamrowe, `&&`/`||` zamiast `and then`/`or else`. Ada używa słów kluczowych
   i średników po `end`.
3. Mylenie `String` z łańcuchami dynamicznymi. `String` ma stałą długość ustaloną
   przy deklaracji; konkatenacja tworzy nową wartość, a przypisanie wymaga zgodnej
   długości. Do budowania tekstu w pętli stosuj
   `Ada.Strings.Unbounded.Unbounded_String` z funkcjami `To_Unbounded_String`/`To_String`.
4. Założenie, że tablice zaczynają się od 1 (lub od 0). Zakres tablicy jest częścią
   typu — iteruj przez `Data'Range`, indeksy graniczne pobieraj przez `Data'First`
   i `Data'Last`, długość przez `Data'Length`.
5. Pomijanie deklaracji `with` i pisanie samego `use`, albo odwrotnie — kwalifikowanie
   nazw bez `with`. Klauzula `with` udostępnia jednostkę, `use` jedynie skraca nazwy;
   `with` jest zawsze konieczne.
6. Mieszanie składni wydań normy: pragma `Precondition` (styl GNAT sprzed Ady 2012)
   obok aspektu `with Pre =>`, albo aspekty w kodzie kompilowanym jako Ada 95.
   Ustal wydanie języka w projekcie i stosuj jedną składnię kontraktów.
7. Traktowanie typów `access` jak wszechobecnych wskaźników z C: zwracanie accessów
   do zmiennych lokalnych, pomijanie sterty. W Adzie preferuj przekazywanie przez
   parametry `in out`, typy ograniczone i kontenery z `Ada.Containers`; typy `access`
   stosuj oszczędnie i świadomie zarządzaj czasem życia.
8. Funkcje z efektami ubocznymi pisane tam, gdzie potrzebna jest procedura. Rozróżniaj:
   funkcja zwraca wartość, procedura działa przez parametry trybów `out`/`in out`;
   w SPARK funkcje nie mogą mieć efektów ubocznych.
9. Ignorowanie ostrzeżenia o nieużywanym wyniku lub nieobsłużonym wyjątku przez
   dopisanie `when others => null;`. Pusty handler ukrywa błędy; co najmniej loguj
   `Ada.Exceptions.Exception_Information` albo pozwól wyjątkowi się propagować.
