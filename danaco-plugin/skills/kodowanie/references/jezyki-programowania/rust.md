# Rust — karta

## Standard stylu i nazewnictwa

Stosuj `rustfmt` z domyślną konfiguracją — nie dyskutuj ze stylem: uruchamiaj `cargo fmt` przed
każdą rewizją i wymuszaj `cargo fmt --check` w CI. Odstępstwa dopuszczaj wyłącznie przez jawny plik
`rustfmt.toml`. Lintuj przez `cargo clippy -- -D warnings` w CI; wyciszenia `#[allow(...)]` stosuj
punktowo, z komentarzem uzasadniającym, nigdy globalnie na całą skrzynkę (crate).

Projekt API prowadź według Rust API Guidelines:

- konwersje nazywaj `as_`/`to_`/`into_` zgodnie z kosztem operacji i przejęciem własności;
- konstruktory: `new` oraz `with_...`; iteratory przez `iter`/`iter_mut`/`into_iter`;
- dokumentuj publiczne API komentarzami `///` z sekcjami `# Examples`, `# Errors`, `# Panics` —
  przykłady w dokumentacji są kompilowane i uruchamiane jako testy.

Konwencje nazewnicze (wymuszane ostrzeżeniami kompilatora):

- typy, cechy (traits) i warianty wyliczeń: `UpperCamelCase`;
- funkcje, metody, moduły, pola i zmienne: `snake_case`;
- stałe i statyki: `SCREAMING_SNAKE_CASE`; nazwy skrzynek: `snake_case`.

## Struktura projektu

Kanoniczny układ narzuca Cargo — nie odtwarzaj go ręcznie i nie wymyślaj własnego:

```
projekt/
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── lib.rs           # korzeń biblioteki
│   ├── main.rs          # korzeń binarki (cienka warstwa nad lib.rs)
│   └── parser.rs        # jeden plik na moduł
├── tests/               # testy integracyjne (osobne skrzynki)
│   └── integration.rs
└── benches/             # benchmarki (tylko gdy istnieją)
```

Zasady i zakazy:

- moduły deklaruj w stylu współczesnym: `src/parser.rs` oraz podmoduły w `src/parser/`; nie twórz
  plików `mod.rs` w nowym kodzie (styl sprzed edycji 2018);
- w programie wykonywalnym trzymaj logikę w `lib.rs`, a `main.rs` ogranicz do parsowania argumentów
  i wywołania biblioteki — inaczej testy integracyjne nie mają czego importować;
- nie twórz katalogów `src/utils/` bez spójnej odpowiedzialności; w większych repozytoriach stosuj
  workspace Cargo z wieloma skrzynkami.

## Budowa i zależności

Buduj wyłącznie przez Cargo: `cargo build`, `cargo build --release`, `cargo check` do szybkiej
weryfikacji typów. Zasady:

- edycję deklaruj jawnie w `Cargo.toml` (`edition = "2021"` lub nowsza, jednolicie w całym
  workspace); edycja steruje idiomami składniowymi, nie wersją kompilatora — minimalną wersję
  kompilatora przypinaj polem `rust-version` (MSRV);
- zależności zapisuj z wersją semantyczną (`serde = "1"` oznacza zakres zgodny); dokładne wersje
  przypina `Cargo.lock` — w aplikacjach i usługach commituj `Cargo.lock` do repozytorium;
- cechy (features) zależności włączaj jawnie: `serde = { version = "1", features = ["derive"] }`;
  wyłączaj `default-features`, gdy ograniczasz zależności transytywne;
- audytuj łańcuch dostaw: `cargo audit` (baza RustSec) i `cargo deny` w CI;
- toolchain przypinaj plikiem `rust-toolchain.toml`, gdy projekt wymaga konkretnego kanału
  (stable/nightly).

## Testy

Framework testowy jest wbudowany w język i Cargo — nie dodawaj zewnętrznego frameworka do zwykłych
testów. Układ:

- testy jednostkowe w tym samym pliku co kod, w module `#[cfg(test)] mod tests`, funkcje `#[test]` —
  mają dostęp do elementów prywatnych;
- testy integracyjne w `tests/`; każdy plik jest osobną skrzynką i testuje wyłącznie publiczne API
  biblioteki;
- testy dokumentacyjne (przykłady w `///`) traktuj jako pełnoprawne testy publicznego API;
- asercje: `assert!`/`assert_eq!`; testy oczekujące paniki oznaczaj `#[should_panic(expected =
  „...”)]`;
- do testów własnościowych stosuj `proptest`, do benchmarków `criterion`.

Uruchamianie: `cargo test`; pojedynczy test `cargo test nazwa_testu`; wydruk z testów `cargo test --
--nocapture`.

## Diagnostyka

Czytaj diagnostykę kompilatora w całości — rustc wskazuje przyczynę, zakres życia pożyczki i często
gotową poprawkę. Kody błędów wyjaśniaj poleceniem `rustc --explain E0502`. Nie „przepychaj” kodu na
ślepo, dopóki nie rozumiesz, którą regułę własności naruszyłeś. Narzędzia:

- debugger: `rust-gdb` lub `rust-lldb` (nakładki z formatowaniem typów Rusta); buduj profil `dev`
  albo `release` z `debug = true`;
- panika: ustaw `RUST_BACKTRACE=1`, aby otrzymać ślad stosu; w usługach traktuj panikę jako defekt,
  nie mechanizm obsługi błędów;
- kod `unsafe` weryfikuj Miri (`cargo +nightly miri test`) — wykrywa niezdefiniowane zachowanie,
  którego kompilator nie widzi; sanitizery (ASan/TSan) są dostępne przez flagę `-Z sanitizer` na
  kanale nightly;
- profilowanie: `perf` oraz `cargo flamegraph`; buduj z optymalizacjami i symbolami;
- błędy konsolidacji zdarzają się głównie przy FFI (`extern "C"`) — sprawdzaj zgodność nazw symboli
  i atrybut `#[no_mangle]`.

Wyścigi danych w bezpiecznym Ruście blokuje kompilator (cechy `Send`/`Sync`); nadal możliwe są
zakleszczenia (`Mutex` trzymany podczas drugiego `lock`) i wyścigi logiczne — analizuj kolejność
zajmowania blokad.

## Typowe błędy modeli LLM w tym języku

1. **Walka z borrow checkerem przez `.clone()`**: klon przy pierwszym błędzie E0502/E0382 zamiast
   poprawy struktury własności. Przekaż `&T`/`&mut T`, zawęź zakres pożyczki albo przenieś własność;
   `clone` jest dopuszczalny świadomie, nie jako uniwersalna ucieczka, a `Rc<RefCell<T>>` nie jest
   domyślnym wzorcem projektowym.
2. **`unwrap()`/`expect()` w kodzie produkcyjnym**: panika zamiast obsługi błędu. Poprawny wzorzec:

```rust
// biblioteka: konkretny typ błędu; aplikacja: propagacja przez `?`
fn load_config(path: &Path) -> Result<Config, ConfigError> {
    let raw = fs::read_to_string(path)?; // błąd wraca do wywołującego
    parse_config(&raw)
}
```

   `unwrap` rezerwuj dla testów i niezmienników udowodnionych w kodzie, z komentarzem dlaczego; w
   bibliotekach definiuj typ błędu (`thiserror`), w aplikacjach dodawaj kontekst (`anyhow`).
3. **Przestarzałe idiomy sprzed edycji 2018**: `extern crate`, makro `try!`, pliki `mod.rs`,
   `#[macro_use]` zamiast importu makr przez `use`. Współczesny Rust importuje przez `use
   nazwa_skrzynki::...` bez dodatkowych deklaracji.
4. **Halucynowane API skrzynek i mieszanie ich wersji**: wymyślone metody oraz składnia z różnych
   wersji popularnych skrzynek (np. rand, tokio, clap — styl builder kontra derive). Sprawdź wersję
   w `Cargo.toml` i dokumentację na docs.rs dla tej wersji, zanim użyjesz API.
5. **`String`/`Vec<T>` w sygnaturach zamiast pożyczek**: wymuszanie własności u wywołującego
   powoduje kaskadę klonów. Argumenty przyjmuj jako `&str` i `&[T]`; własność w argumencie jest
   właściwa tylko, gdy funkcja rzeczywiście ją przejmuje (np. buduje z niej strukturę).
6. **Zbędne `collect()` i alokacje pośrednie**: `iter().map(...).collect::<Vec<_>>()` tylko po to,
   by zaraz iterować ponownie. Utrzymuj leniwy łańcuch iteratorów do miejsca konsumpcji; `collect`
   wywołuj raz, na końcu, do docelowego kontenera.
7. **Nadużycie `unsafe` bez uzasadnienia**: sięganie po `transmute` i surowe wskaźniki, gdy istnieje
   bezpieczny odpowiednik (`split_at_mut`, typy biblioteki standardowej). Każdy blok `unsafe` wymaga
   komentarza `// SAFETY:` z dowodem zachowania niezmienników; kod, który nie przechodzi Miri, nie
   przechodzi przeglądu.
8. **Indeksowanie zamiast wzorców i kombinatorów**: `v[0]` oraz `s.chars().nth(i)` panikują lub mają
   zły koszt. Stosuj `first()`, `get(i)`, dopasowanie `if let Some(x) = ...` oraz kombinatory
   `map`/`and_then`/`unwrap_or_else` na `Option`/`Result`.
9. **Trzymanie blokady przez punkt `.await`**: `std::sync::MutexGuard` utrzymany przez `await`
   blokuje wątek wykonawczy i grozi zakleszczeniem. Zwalniaj blokadę przed `await` (osobny zasięg)
   albo stosuj `tokio::sync::Mutex` tam, gdzie sekcja krytyczna musi objąć `await`.
10. **Ignorowanie ostrzeżeń i lintów jako „szumu”**: ostrzeżenia rustc i clippy w tym języku niemal
    zawsze wskazują realny defekt lub martwy kod. Oddawaj kod z zerową liczbą ostrzeżeń przy `cargo
    clippy -- -D warnings`.
