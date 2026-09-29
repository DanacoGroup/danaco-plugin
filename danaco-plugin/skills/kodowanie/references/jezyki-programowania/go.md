# Go — karta

## Standard stylu i nazewnictwa
Stosuj Effective Go oraz zbiór Go Code Review Comments jako obowiązujący standard.
Formatowanie jest niedyskusyjne: każdy plik musi przechodzić przez `gofmt` (lub
`goimports`, który dodatkowo porządkuje importy). Lintowanie: `go vet` zawsze;
dodatkowo `staticcheck` lub agregator `golangci-lint`, jeżeli projekt go konfiguruje.

Konwencje nazw:
- Eksportowane identyfikatory: `UpperCamelCase` (`InvoiceProcessor`); nieeksportowane:
  `lowerCamelCase` (`parseAmount`). Wielka litera na początku = publiczne — dobieraj
  widoczność świadomie.
- Akronimy zachowują wielkość liter: `ServeHTTP`, `userID`, `parseURL` — nie `Http`, `Id`.
- Nazwy pakietów: krótkie, jednowyrazowe, małe litery, bez podkreśleń (`invoice`,
  nie `invoice_utils`). Nie powtarzaj nazwy pakietu w identyfikatorach:
  `invoice.Parse`, nie `invoice.ParseInvoice`.
- Interfejsy jednometodowe: sufiks `-er` (`Reader`, `Validator`).
- Odbiorniki metod: krótkie, spójne w typie (`func (p *Processor) ...`), nie `this`/`self`.

## Struktura projektu
Moduł Go wyznacza plik `go.mod` w korzeniu repozytorium. Zaczynaj płasko; katalogi
dodawaj dopiero, gdy rośnie liczba pakietów.

```
projekt/
├── go.mod
├── go.sum
├── main.go                  (mały serwis: wszystko w korzeniu)
├── cmd/
│   └── billingd/main.go     (przy wielu binariach)
├── internal/
│   └── invoice/             (kod niedostępny dla innych modułów)
└── .gitignore               (binarki; NIE ignoruj go.sum)
```

Stosuj `internal/` dla kodu, który nie ma być importowany z zewnątrz. Nie twórz
katalogów `src/`, `pkg/` z przyzwyczajenia ani struktury pakietów według warstw
(`models`, `controllers`) — pakiety grupuj według odpowiedzialności. Jeden katalog =
jeden pakiet; testy leżą obok kodu, nie w osobnym drzewie.

## Budowa i zależności
Stosuj wyłącznie moduły Go (`go mod`); mechanizm `GOPATH`/`dep` jest przeszłością.

- Celuj w aktualną stabilną wersję Go; Go wspiera dwie ostatnie wydania główne
  (wydania co pół roku). Dyrektywa `go` w `go.mod` deklaruje minimalną wersję języka.
- `go.sum` commituj zawsze — przypina sumy kontrolne wszystkich zależności i zapewnia
  powtarzalność budowy. Wersje zależności są przypięte w `go.mod` (semantyka MVS).
- Cykl pracy: `go get pakiet@wersja` → `go mod tidy` (porządkuje `go.mod`/`go.sum`) →
  `go build ./...`. Uruchamiaj `go mod tidy` po każdej zmianie importów.
- Preferuj bibliotekę standardową: `net/http` (od Go 1.22 router obsługuje metody
  i wieloznaczniki ścieżek), `encoding/json`, `log/slog` — zanim sięgniesz po
  framework zewnętrzny.

## Testy
Stosuj pakiet standardowy `testing`; asercje biblioteką `testify`
(`github.com/stretchr/testify`) tylko, jeżeli projekt już jej używa — czysty
`testing` z `t.Errorf`/`t.Fatalf` jest w Go pełnoprawnym standardem.

- Plik `foo_test.go` obok `foo.go`, w tym samym pakiecie (lub `foo_test` dla testów
  czarnoskrzynkowych). Funkcje `func TestXxx(t *testing.T)`.
- Stosuj testy tabelaryczne z podtestami:
  `for _, tc := range cases { t.Run(tc.name, func(t *testing.T) { ... }) }`.
- Uruchamianie: `go test ./...`; z detektorem wyścigów: `go test -race ./...`
  (obowiązkowo przed oddaniem kodu współbieżnego); pojedynczy test:
  `go test -run TestParseAmount ./internal/invoice`.
- Benchmarki: `func BenchmarkXxx(b *testing.B)`, uruchamiane `go test -bench .`.

## Diagnostyka
- Panika drukuje pełny ślad stosu wszystkich ramek; czytaj od góry — pierwsza ramka
  w kodzie projektu wskazuje miejsce błędu (np. `nil pointer dereference`,
  `index out of range`).
- Debugger: Delve (`dlv debug`, `dlv test`); profilowanie: `pprof` — w testach
  `go test -cpuprofile`/`-memprofile`, w serwisach `net/http/pprof`, analiza
  `go tool pprof` (top, web, flamegraph). Śledzenie wykonania: `go tool trace`.
- Wyścigi danych wykrywaj detektorem: `go build -race` / `go test -race`; raport
  wskazuje oba konfliktujące dostępy wraz ze stosami goroutin.
- Typowe klasy błędów: wyciek goroutin (goroutyna blokuje się na kanale bez odbiorcy —
  widoczne w zrzucie `pprof/goroutine`), deadlock „all goroutines are asleep”,
  zapis do mapy z wielu goroutin (`fatal error: concurrent map writes`), użycie
  wartości po `err != nil`, dereferencja nil w metodach na wskaźnikowym odbiorniku.

## Typowe błędy modeli LLM w tym języku
1. **Ignorowanie błędów: `_ = err`, pominięty drugi wynik.** Każdy zwrócony `error` obsłuż albo
   propaguj z kontekstem: `if err != nil { return fmt.Errorf("parse invoice: %w", err) }`. Zawijaj
   przez `%w`, aby działały `errors.Is`/`errors.As`.
2. **`panic` do sygnalizowania zwykłych błędów.** Panika jest dla błędów programisty
   (naruszone niezmienniki), nie dla błędów wejścia czy I/O — te zwracaj jako `error`.
   Nie stosuj `recover` jako imitacji try/catch.
3. **Przestarzały idiom pętli: kopiowanie zmiennej `for i, v := range`.** Od Go 1.22
   zmienna pętli ma zakres iteracji — `v := v` nie jest już potrzebne w nowych
   projektach; sprawdź dyrektywę `go` w `go.mod`, zanim dodasz ten obejściowy zapis.
4. **Goroutyny bez synchronizacji i bez końca życia.** Każde `go func()` musi mieć
   jasny mechanizm zakończenia: `sync.WaitGroup`, kanał, `errgroup.Group` lub
   anulowanie przez `context`. Goroutyna pisząca do kanału bez odbiorcy wycieka.
5. **Ignorowanie `context.Context`.** Funkcje wykonujące I/O przyjmują `ctx context.Context`
   jako pierwszy parametr i przekazują go dalej; nie twórz `context.Background()`
   w środku stosu wywołań, skoro wywołujący dostarcza kontekst.
6. **`interface{}`/`any` i refleksja zamiast typów.** Od Go 1.18 stosuj typy
   generyczne tam, gdzie to naturalne; `any` w sygnaturze publicznej przenosi błędy
   typów do środowiska wykonawczego.
7. **Struktury „na wzór klas”: gettery/settery, interfejs dla każdej struktury.**
   Eksportuj pola wprost, gdy nie ma niezmienników; interfejs definiuj po stronie
   konsumenta i dopiero, gdy istnieje więcej niż jedna implementacja lub potrzeba atrapy.
8. **Niezamykanie zasobów i błędna kolejność z `defer`.** Po `resp, err := http.Get(...)`
   najpierw sprawdź `err`, dopiero potem `defer resp.Body.Close()` — odwrotna kolejność
   powoduje dereferencję nil. Uwaga na `defer` w pętli: wykonuje się przy wyjściu
   z funkcji, nie z iteracji.
9. **Porównywanie błędów po tekście: `err.Error() == "..."` lub `strings.Contains`.**
   Stosuj `errors.Is(err, os.ErrNotExist)` i `errors.As` dla typów błędów; treść
   komunikatu nie jest kontraktem API.
10. **Halucynowane pakiety i API.** Nie importuj pakietów, których nie ma w `go.mod`,
    i nie wymyślaj funkcji biblioteki standardowej; po dodaniu importu uruchom
    `go mod tidy` i `go build ./...`, aby zweryfikować istnienie API.
