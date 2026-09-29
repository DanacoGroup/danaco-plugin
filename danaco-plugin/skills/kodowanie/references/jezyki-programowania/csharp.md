# C# / .NET — karta

## Standard stylu i nazewnictwa
Stosuj Microsoft .NET naming guidelines oraz C# Coding Conventions (learn.microsoft.com) jako
obowiązujący standard. Egzekwuj je przez `dotnet format`, plik `.editorconfig` z regułami stylu
(IDE####/CA####) oraz wbudowane analizatory Roslyn (`<AnalysisLevel>latest</AnalysisLevel>`,
`<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>`).

Konwencje nazw:
- Klasy, rekordy, struktury, enumy, metody, właściwości, zdarzenia: `PascalCase`
  (`InvoiceProcessor`, `CalculateNetAmount`).
- Interfejsy: `PascalCase` z prefiksem `I` (`IInvoiceRepository`).
- Parametry i zmienne lokalne: `camelCase`; pola prywatne: `_camelCase` z podkreśleniem.
- Stałe: `PascalCase` (`MaxRetryCount`), nie `UPPER_SNAKE_CASE`.
- Metody asynchroniczne zwracające `Task`/`ValueTask`: sufiks `Async` (`SaveAsync`).
- Parametry typów generycznych: prefiks `T` (`TEntity`, `TResult`).

Stosuj `var`, gdy typ jest oczywisty z prawej strony przypisania. Włącz nullable
reference types (`<Nullable>enable</Nullable>`) w każdym nowym projekcie.

## Struktura projektu
Stosuj układ solucji .NET: plik `.sln` w korzeniu, projekty w podkatalogach.

```
Danaco.Billing/
├── Danaco.Billing.sln
├── Directory.Build.props          (wspólne ustawienia projektów)
├── Directory.Packages.props       (central package management)
├── src/
│   ├── Danaco.Billing.Api/        (Danaco.Billing.Api.csproj)
│   └── Danaco.Billing.Domain/
├── tests/
│   └── Danaco.Billing.Domain.Tests/
└── .gitignore                     (bin/, obj/, *.user)
```

Nazwa projektu = nazwa katalogu = domyślna przestrzeń nazw. Nie edytuj plików `.sln`
ręcznie — używaj `dotnet sln add`. Nie commituj `bin/`, `obj/` ani ustawień
użytkownika IDE. Nie twórz osobnego projektu na każdą drobną warstwę — dziel solucję
tylko wzdłuż rzeczywistych granic wdrożeniowych lub domenowych.

## Budowa i zależności
Stosuj CLI `dotnet` (`dotnet build`, `dotnet run`, `dotnet test`) i pakiety NuGet.

- Celuj w aktualną wersję LTS platformy: .NET 8+ LTS (`<TargetFramework>net8.0</TargetFramework>`
  lub nowszy LTS). Wersję języka zostaw domyślną dla frameworka, chyba że projekt
  wymaga inaczej.
- Przypinaj dokładne wersje pakietów; w solucjach wieloprojektowych stosuj Central
  Package Management (`Directory.Packages.props` z `<PackageVersion ...>`), aby jedna
  wersja pakietu obowiązywała w całej solucji.
- Przed dodaniem pakietu sprawdź, czy BCL nie pokrywa potrzeby (`System.Text.Json`
  zamiast Newtonsoft.Json w nowym kodzie, `HttpClient` przez `IHttpClientFactory`).
- Wspólne właściwości (`LangVersion`, `Nullable`, `TreatWarningsAsErrors`) definiuj
  raz w `Directory.Build.props`, nie w każdym `.csproj`.

## Testy
Stosuj xUnit jako domyślny framework; NUnit lub MSTest tylko, gdy projekt już je
standaryzuje. Asercje: wbudowane w xUnit lub FluentAssertions/AwesomeAssertions —
spójnie z projektem. Atrapy: NSubstitute lub Moq.

- Projekty testowe w katalogu `tests/`, nazwa `<Projekt>.Tests`; referencja do
  projektu testowanego przez `dotnet add reference`.
- xUnit: `[Fact]` dla przypadków pojedynczych, `[Theory]` z `[InlineData]` dla
  parametryzowanych. Konstruktor i `IDisposable`/`IAsyncLifetime` zamiast atrybutów
  setup/teardown.
- Testy metod asynchronicznych deklaruj jako `async Task`, nigdy `async void`.
- Uruchamianie: `dotnet test`; filtr: `dotnet test --filter
  „FullyQualifiedName~InvoiceProcessorTests”`.

## Diagnostyka
- Czytaj ślad stosu wraz z `InnerException` — dla `AggregateException` (np. po
  `Task.Wait()`) prawdziwa przyczyna jest w wyjątkach wewnętrznych.
- Narzędzia diagnostyczne CLI: `dotnet-trace` (profilowanie zdarzeń/CPU),
  `dotnet-counters` (metryki na żywo: GC, wątki, alokacje), `dotnet-dump` +
  `dotnet-dump analyze` (zrzuty procesu, analiza sterty i zakleszczeń),
  `dotnet-gcdump` (zrzut sterty zarządzanej). W IDE: debugger Visual Studio/Rider
  z oknem Parallel Stacks do analizy zakleszczeń async.
- Typowe klasy błędów: `NullReferenceException` (najczęściej w kodzie ignorującym
  ostrzeżenia nullable), deadlock async przy blokowaniu na `Task` (`.Result`,
  `.Wait()`) w środowisku z kontekstem synchronizacji, `ObjectDisposedException`
  po użyciu zasobu poza jego zakresem DI, wyczerpanie puli połączeń przy tworzeniu
  `HttpClient` per żądanie zamiast przez `IHttpClientFactory`.

## Typowe błędy modeli LLM w tym języku
1. **`async void` poza obsługą zdarzeń.** Wyjątek z `async void` nie jest obserwowalny
   przez wywołującego i może ubić proces. Zwracaj `Task`; `async void` wyłącznie dla
   procedur obsługi zdarzeń UI.
2. **Blokowanie na kodzie asynchronicznym: `.Result`, `.Wait()`, `.GetAwaiter().GetResult()`.**
   Grozi deadlockiem i marnuje wątki. Propaguj `async`/`await` w górę stosu
   („async all the way”); w `Main` stosuj `async Task Main`.
3. **Ignorowanie nullable reference types.** Wyciszanie ostrzeżeń operatorem `!`
   (null-forgiving) bez uzasadnienia przenosi błąd do środowiska wykonawczego.
   Modeluj nullowalność w typach (`string?`) i waliduj na granicach
   (`ArgumentNullException.ThrowIfNull(arg)`).
4. **`new HttpClient()` na każde żądanie.** Wyczerpuje gniazda (socket exhaustion).
   Stosuj `IHttpClientFactory` (`AddHttpClient`) albo jednego współdzielonego,
   długowiecznego klienta.
5. **`DateTime.Now` do znaczników czasu i logiki.** Stosuj `DateTimeOffset.UtcNow`
   lub `TimeProvider` (testowalne źródło czasu); `DateTime.Now` zależy od strefy
   maszyny i psuje porównania oraz serializację.
6. **Brak przekazywania `CancellationToken`.** Metody asynchroniczne przyjmujące pracę
   I/O deklaruj z parametrem `CancellationToken cancellationToken = default` i przekazuj
   go do wszystkich wywołań podrzędnych.
7. **Halucynowane API i mieszanie wersji frameworków.** Nie mieszaj wzorców
   ASP.NET (`Startup`/`Global.asax`) z minimal APIs .NET 8+; nie wywołuj metod
   rozszerzających, których pakietu nie ma w projekcie — sprawdź `.csproj`
   i istniejący kod przed użyciem.
8. **Łapanie `Exception` i kontynuowanie pracy.** Łap konkretne typy
   (`HttpRequestException`, `IOException`); przy ponownym rzucaniu stosuj `throw;`,
   nigdy `throw ex;` — to drugie niszczy ślad stosu.
9. **`List<T>` i typy konkretne w publicznych sygnaturach.** Przyjmuj
   `IEnumerable<T>`/`IReadOnlyList<T>`, zwracaj typy tylko do odczytu; ogranicza to
   przypadkowe mutacje i wiązanie z implementacją.
10. **Ręczny boilerplate zamiast idiomów języka.** Stosuj `record` dla niemutowalnych
    danych, pattern matching (`switch` z wzorcami) zamiast kaskad `if`-`is`-rzutowanie,
    interpolację `$"..."` zamiast `string.Format` i `string.IsNullOrWhiteSpace`
    zamiast ręcznych porównań.
