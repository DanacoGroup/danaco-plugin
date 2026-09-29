# Języki programowania — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Ten katalog
dostarcza wiedzę właściwą dla konkretnego języka: każda karta w katalogu
`references/jezyki-programowania/` opisuje jeden język.

## Sposób użycia

1. Ustal język, w którym prowadzona jest praca (z treści zadania lub rozszerzenia pliku).
2. Wczytaj WYŁĄCZNIE kartę tego języka — nie wczytuj pozostałych; przy pracy
   wielojęzycznej wczytaj karty wszystkich używanych języków.
3. Stosuj kartę łącznie z procedurą właściwą dla zadania: `budowa-kodu` przy pisaniu,
   `debugowanie` przy naprawie, `przeglad-kodu` przy przeglądzie.
4. Gdy karta wskazuje standard zewnętrzny (np. PEP 8), a projekt ma własną, spójnie
   stosowaną konwencję — pierwszeństwo ma konwencja projektu.

## Spis kart

| Język | Karta |
| --- | --- |
| Python | `references/jezyki-programowania/python.md` |
| C | `references/jezyki-programowania/c.md` |
| C++ | `references/jezyki-programowania/cpp.md` |
| C# | `references/jezyki-programowania/csharp.md` |
| Java | `references/jezyki-programowania/java.md` |
| Kotlin | `references/jezyki-programowania/kotlin.md` |
| JavaScript / TypeScript | `references/jezyki-programowania/javascript-typescript.md` |
| Go | `references/jezyki-programowania/go.md` |
| Rust | `references/jezyki-programowania/rust.md` |
| PHP | `references/jezyki-programowania/php.md` |
| SQL | `references/jezyki-programowania/sql.md` |
| Visual Basic (VB.NET) | `references/jezyki-programowania/visual-basic.md` |
| Delphi (Object Pascal) | `references/jezyki-programowania/delphi.md` |
| Fortran | `references/jezyki-programowania/fortran.md` |
| Ada | `references/jezyki-programowania/ada.md` |
| COBOL | `references/jezyki-programowania/cobol.md` |
| Matlab | `references/jezyki-programowania/matlab.md` |
| R | `references/jezyki-programowania/r.md` |
| Asembler (x86-64) | `references/jezyki-programowania/asembler.md` |
| Scratch | `references/jezyki-programowania/scratch.md` |

## Budowa każdej karty

Każda karta ma jednakowy układ sekcji: Standard stylu i nazewnictwa · Struktura
projektu · Budowa i zależności · Testy · Diagnostyka · Typowe błędy modeli LLM
w tym języku. Sekcja ostatnia ma znaczenie szczególne — wymienia błędy, które
modele LLM popełniają w danym języku nagminnie; sprawdź własny kod względem tej
listy przed przekazaniem pracy.

Wersje narzędzi i bibliotek przywołane w kartach traktuj jako orientacyjne —
stan faktyczny sprawdzaj w środowisku projektu i oficjalnej dokumentacji.
