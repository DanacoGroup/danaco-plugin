# R — karta

## Standard stylu i nazewnictwa

Stosuj tidyverse style guide jako obowiązujący standard stylu. Egzekwuj konwencje nazewnicze:

- funkcje i zmienne: `snake_case` (np. `compute_monthly_revenue`, `input_data`); nazwy funkcji
  zaczynaj od czasownika;
- nie używaj kropek w nazwach własnych funkcji (`summary.default` to składnia dyspozycji S3 — kropka
  ma tam znaczenie techniczne);
- pliki: `snake_case` z rozszerzeniem `.R` (np. `clean_data.R`); w pakietach jeden spójny obszar
  tematyczny na plik;
- klasy S4/R5 oraz konstruktory obiektów: zgodnie z konwencją przyjętą w projekcie — sprawdź
  istniejący kod.

Stosuj `<-` jako operator przypisania na najwyższym poziomie (`=` rezerwuj dla argumentów funkcji). Stosuj `TRUE`/`FALSE` w pełnym zapisie. Operator potoku: natywny `|>` (R 4.1+) lub magrittr `%>%` — zgodnie z konwencją projektu, nie mieszaj obu w jednym pliku. Narzędzia przyjęte zawodowo: styler (formatowanie zgodne z tidyverse style guide), lintr (lintowanie), roxygen2 (dokumentacja funkcji w komentarzach `#'`).

## Struktura projektu

Dla kodu wielokrotnego użytku kanoniczna jest struktura pakietu R:

```
package/
├── DESCRIPTION          # metadane, zależności (Imports, Suggests)
├── NAMESPACE            # generowany przez roxygen2 — nie edytuj ręcznie
├── R/                   # wyłącznie definicje funkcji, bez kodu wykonywalnego
│   └── clean_data.R
├── tests/
│   ├── testthat.R
│   └── testthat/
│       └── test-clean_data.R
├── man/                 # generowany przez roxygen2 — nie edytuj ręcznie
├── data/                # zbiory danych pakietu (.rda)
└── vignettes/
```

Dla analiz stosuj projekt RStudio (plik `.Rproj`) z katalogami `R/` lub `scripts/`, `data/` (dane
surowe, tylko do odczytu) i `output/`. Czego nie tworzyć: plików `.Rhistory` i `.RData` w
repozytorium (wyłącz zapis obszaru roboczego), ręcznych wpisów w `NAMESPACE` i `man/`, ani skryptów
zależnych od `setwd()` — ścieżki buduj względem korzenia projektu (pakiet here lub `file.path`).

## Budowa i zależności

Do izolacji i przypinania zależności analiz oraz aplikacji stosuj renv: `renv::init()` tworzy
bibliotekę projektu, `renv::snapshot()` zapisuje dokładne wersje w `renv.lock` (commituj ten plik),
`renv::restore()` odtwarza środowisko. W pakietach zależności deklaruj w `DESCRIPTION`: pola
`Imports` (wymagane), `Suggests` (opcjonalne, np. testowe), `Depends` tylko dla wersji R. Cykl pracy
nad pakietem prowadź przez devtools i usethis:

- `devtools::load_all()` — załadowanie kodu do sesji;
- `devtools::document()` — regeneracja `NAMESPACE` i `man/` z roxygen2;
- `devtools::check()` — pełna weryfikacja `R CMD check`; utrzymuj wynik bez błędów i ostrzeżeń;
- `usethis::use_package("dplyr")` — poprawne dodanie zależności.

Pakiety instaluj z CRAN (`install.packages`) lub szybciej przez pak; wersje spoza CRAN dokumentuj
jawnie w `renv.lock` lub polu `Remotes`.

## Testy

Stosuj testthat jako standardowy framework. Układ: `tests/testthat/` z plikami `test-<nazwa>.R`
odpowiadającymi plikom w `R/`; szkielet twórz przez `usethis::use_testthat()` i
`usethis::use_test("clean_data")`. Praktyki:

- grupuj asercje w `test_that("opis zachowania", { ... })` z opisem oczekiwanego rezultatu;
- stosuj precyzyjne asercje: `expect_equal` (z tolerancją numeryczną), `expect_identical` (ścisła),
  `expect_error(..., regexp = )`, `expect_s3_class`;
- testy migawki (`expect_snapshot`) stosuj dla komunikatów i wydruków, nie dla logiki;
- nie porównuj liczb zmiennoprzecinkowych przez `==` — od tego jest tolerancja `expect_equal`.

Uruchamiaj: `devtools::test()` (całość), `testthat::test_file("tests/testthat/test-clean_data.R")`
(pojedynczy plik). W CI testy przebiegają w ramach `R CMD check`.

## Diagnostyka

Narzędzia debugowania i profilowania:

- `browser()` wstawiony w kod oraz `debug(fn)`/`debugonce(fn)` dla istniejących funkcji —
  debugowanie krokowe;
- `options(error = recover)` — wejście w ramki stosu bezpośrednio po błędzie;
- `traceback()` po błędzie — czytaj od góry: najwyższy wpis to miejsce zgłoszenia, schodząc w dół
  widzisz łańcuch wywołań; w kodzie tidyverse pełniejszy obraz daje `rlang::last_trace()`;
- profilowanie czasu: profvis (interaktywnie) lub `Rprof()`; pamięć: `lobstr::obj_size()`.

Typowe klasy błędów i ich rozpoznanie:

- `object of type 'closure' is not subsettable` — próba indeksowania funkcji zamiast danych; zwykle
  przesłonięcie nazwy (np. własna zmienna `df` nie została utworzona, a istnieje funkcja o tej
  nazwie);
- `could not find function "..."` — pakiet niezaładowany (`library()`) lub literówka; w pakietach:
  brak wpisu importu;
- `argument is of length zero` w `if` — warunek zwrócił wektor pustej długości; sprawdź filtrowanie
  powyżej;
- `missing value where TRUE/FALSE needed` — `NA` w warunku logicznym; obsłuż `NA` jawnie (`is.na`);
- ciche recyklingowanie wektorów o niezgodnych długościach — weryfikuj długości; ostrzeżenie pojawia
  się tylko przy braku podzielności.

## Typowe błędy modeli LLM w tym języku

1. **`1:length(x)` w pętlach**: dla `length(x) == 0` daje sekwencję `1, 0` i wykonuje pętlę na
   nieistniejących indeksach. Stosuj `seq_along(x)` oraz `seq_len(n)`.
2. **`sapply()` w kodzie produkcyjnym**: typ wyniku zależy od danych (wektor, macierz lub lista).
   Stosuj `vapply()` z deklaracją typu wyniku albo funkcje `purrr::map_*()`:

```r
# wynik gwarantowanie typu double, po jednym elemencie na wejście
means <- vapply(datasets, function(d) mean(d$value), numeric(1))
```

3. **`stringsAsFactors = FALSE` dodawane odruchowo lub zakładanie starego domyślnego**: od R 4.0
   `data.frame()` i `read.csv()` nie konwertują łańcuchów na faktory. Nie pisz kodu zakładającego
   zachowanie sprzed R 4.0.
4. **`attach()` na ramkach danych**: tworzy ukryte, nieaktualizowane odwołania i konflikty nazw.
   Stosuj `with()`, `df$col` lub semantykę maskowania danych w dplyr.
5. **Mieszanie idiomów base R i tidyverse w jednym potoku**: np. `df %>% subset(...) %>%
   mutate(...)`. Wybierz jedną konwencję zgodną z projektem i stosuj ją spójnie.
6. **Przestarzałe API dplyr/tidyr**: `summarise_each()`, `mutate_at()`, `gather()`/`spread()` w
   nowym kodzie. Stosuj `across()` wewnątrz `summarise()`/`mutate()` oraz
   `pivot_longer()`/`pivot_wider()`.
7. **`T`/`F` zamiast `TRUE`/`FALSE`**: `T` i `F` są zwykłymi zmiennymi i mogą zostać przesłonięte.
   Zapisuj wartości logiczne w pełnej formie.
8. **`library()` wewnątrz kodu pakietu**: modyfikuje ścieżkę wyszukiwania użytkownika. W pakietach
   deklaruj zależności w `DESCRIPTION` i odwołuj się przez `pkg::fun()` lub importy roxygen2
   (`@importFrom`).
9. **Częściowe dopasowanie `$`**: `df$val` dopasuje kolumnę `value`, jeżeli `val` nie istnieje —
   źródło cichych błędów. W kodzie programistycznym stosuj `df[["value"]]`.
10. **Halucynowane funkcje i argumenty pakietów**: wymyślone warianty funkcji ggplot2/dplyr lub
    nieistniejące argumenty. Jeżeli nie masz pewności, sprawdź `?nazwa_funkcji` lub dokumentację
    pakietu, zamiast zgadywać sygnaturę.
