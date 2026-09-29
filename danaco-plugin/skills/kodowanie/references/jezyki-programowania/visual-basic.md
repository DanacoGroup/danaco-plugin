# Visual Basic .NET — karta

Karta dotyczy Visual Basic .NET na platformie .NET. Odróżniaj go od środowisk zastanych: VBA (makra
pakietu Office, środowisko VBE, brak platformy .NET) oraz klasycznego VB6 (zakończony rozwój, COM,
brak CLR) to odrębne języki o innej semantyce i bibliotekach. Przed pisaniem kodu ustal
jednoznacznie, którego środowiska dotyczy zadanie; wzorców z tej karty nie przenoś mechanicznie do
VBA ani VB6.

## Standard stylu i nazewnictwa

- Stosuj wytyczne Microsoft: .NET Framework Design Guidelines oraz Visual Basic Coding Conventions z
  dokumentacji Microsoft Learn.
- W nagłówku każdego projektu wymuś `Option Strict On`, `Option Explicit On` oraz `Option Infer On`
  (najlepiej w pliku projektu, aby obowiązywały globalnie). Kod z `Option Strict Off` traktuj jako
  niezgodny ze standardem Danaco, chyba że wymaga tego świadomie późne wiązanie COM.
- Nazewnictwo: `PascalCase` dla typów, metod, właściwości, zdarzeń i stałych publicznych;
  `camelCase` dla zmiennych lokalnych i parametrów; przedrostek `I` dla interfejsów
  (`IInvoiceRepository`); pola prywatne z przedrostkiem `_` (`_connectionString`).
- Pamiętaj, że VB jest niewrażliwy na wielkość liter — nie twórz identyfikatorów różniących się
  wyłącznie wielkością liter.
- Stosuj `&` do konkatenacji łańcuchów (nie `+`, które przy `Option Strict Off` wykonuje
  niejednoznaczną koercję); do budowy dłuższych tekstów używaj interpolacji `$"..."` lub
  `StringBuilder`.
- Porównania łańcuchów wykonuj przez `String.Equals` z jawnym `StringComparison`; nie polegaj na
  ustawieniu `Option Compare`.
- Obsługę zdarzeń deklaruj przez `Handles` przy stałym powiązaniu lub `AddHandler`/`RemoveHandler`
  przy dynamicznym; każdemu `AddHandler` musi odpowiadać `RemoveHandler` w cyklu życia obiektu.

## Struktura projektu

- Minimalny profesjonalny układ:
  - plik rozwiązania `*.sln` w katalogu głównym;
  - projekt `*.vbproj` w stylu SDK (`<Project Sdk="Microsoft.NET.Sdk">`);
  - katalogi źródeł odzwierciedlające przestrzenie nazw;
  - osobny projekt testowy `*.Tests.vbproj` dołączony do rozwiązania;
  - `.gitignore` obejmujący co najmniej `bin/`, `obj/` i pliki `*.user`.
- W pliku `*.vbproj` ustaw jawnie `TargetFramework` (np. `net8.0`), `OptionStrict`, `OptionExplicit`
  oraz `RootNamespace`; nie polegaj na wartościach domyślnych szablonu.
- Rozdzielaj warstwy: logika domenowa w bibliotece klas bez odwołań do WinForms/WPF; interfejs
  użytkownika wyłącznie jako warstwa prezentacji.
- Czego nie tworzyć:
  - projektów w formacie sprzed stylu SDK dla nowego kodu;
  - modułów (`Module`) pełniących rolę worka na funkcje globalne — preferuj klasy z jawnymi
    zależnościami;
  - katalogów `bin/`, `obj/` ani plików `*.user` w repozytorium;
  - kopii formularzy i klas z przyrostkami `_old`, `2`, `Kopia`.

## Budowa i zależności

- Buduj przez `dotnet build` (lub MSBuild w rozwiązaniach zastanych); testy uruchamiaj przez `dotnet
  test`. Kompilacja z ostrzeżeniami traktowanymi poważnie: rozważ `TreatWarningsAsErrors`
  przynajmniej dla ostrzeżeń o niejawnych konwersjach.
- Zależności zarządzaj wyłącznie przez NuGet z `PackageReference` w pliku projektu; nie kopiuj
  bibliotek DLL ręcznie do katalogu projektu.
- Przypinaj wersje pakietów jawnie w `PackageReference`; dla pełnej odtwarzalności włącz
  `RestorePackagesWithLockFile` i commituj `packages.lock.json`.
- Wersję SDK przypnij plikiem `global.json`, aby budowa była powtarzalna między stacjami i CI.
- Sprawdź `TargetFramework` przed użyciem API — nie zakładaj dostępności najnowszych API .NET w
  projektach celujących w starsze wersje lub .NET Framework 4.x.

## Testy

- Stosuj xUnit lub MSTest jako framework testów jednostkowych; w projektach zastanych utrzymuj
  framework już obecny (bywa nim NUnit) zamiast wprowadzać drugi.
- Projekt testowy nazwij `<NazwaProjektu>.Tests` i odwzoruj w nim strukturę przestrzeni nazw
  projektu testowanego.
- Nazywaj testy wzorcem `Metoda_Scenariusz_OczekiwanyRezultat` (np.
  `CalculateNetTotal_EmptyInvoice_ReturnsZero`).
- Testuj metody asynchroniczne jako `Async Function ... As Task` z `Await` przy asercjach; nigdy nie
  deklaruj testu asynchronicznego jako `Sub`, bo framework nie poczeka na jego zakończenie.
- Zależności zewnętrzne (baza danych, pliki, zegar) izoluj przez interfejsy i wstrzykiwanie; do
  atrap stosuj bibliotekę Moq lub NSubstitute.
- Przed zgłoszeniem zadania uruchom pełny zestaw: `dotnet test` musi przechodzić w całości.

## Diagnostyka

- Używaj debuggera Visual Studio: punkty przerwania warunkowe, okna Locals/Watch/Call Stack, Edit
  and Continue; w środowiskach bez VS stosuj debugger VS Code z rozszerzeniem C#/.NET (obsługuje
  projekty VB) lub logowanie strukturalne.
- Włącz w oknie Exception Settings przerywanie na wybranych wyjątkach pierwszej szansy, gdy wyjątek
  jest połykany gdzieś w warstwach pośrednich.
- Typowe klasy błędów:
  - `NullReferenceException` — odwołanie do składowej obiektu równego `Nothing`; sprawdzaj
    referencje operatorem `Is Nothing` / `IsNot Nothing` i stosuj operator `?.`;
  - błędy późnego wiązania (`MissingMemberException` w czasie wykonania) — skutek `Option Strict
    Off` i typu `Object`; przywróć typowanie statyczne;
  - `InvalidCastException` przy `CType`/`DirectCast` — sprawdź typ operatorem `TypeOf ... Is` albo
    użyj `TryCast` z kontrolą `Nothing`;
  - zakleszczenia i wyścigi w kodzie `Async` — nie blokuj wątku przez `.Result`/`.Wait()` na
    niezakończonym `Task`; stosuj `Await` na całej ścieżce wywołań.
- Czytaj pełny ślad stosu wyjątku łącznie z `InnerException` — w kodzie warstwowym przyczyna
  źródłowa jest zwykle w wyjątku wewnętrznym; `AggregateException` z kodu zadaniowego rozpakuj do
  wyjątków składowych.
- Diagnozuj metodycznie: najpierw minimalna reprodukcja, potem hipoteza, potem pojedyncza zmiana;
  nie modyfikuj wielu miejsc naraz.
- W aplikacjach WinForms/WPF błędy „znikające” bez komunikatu wychwytuj przez obsługę
  `Application.ThreadException` oraz `AppDomain.UnhandledException` z logowaniem.

## Typowe błędy modeli LLM w tym języku

1. **Mieszanie API VB6/VBA z VB.NET** — konstrukcje `Set x = ...`, typ `Variant`, `GoSub`, kolekcje
   COM czy sekwencje `Wend` nie istnieją w VB.NET. Używaj składni i bibliotek .NET; funkcje
   zgodnościowe z przestrzeni `Microsoft.VisualBasic` (np. `Mid`, `MsgBox`) zastępuj odpowiednikami
   .NET (`Substring`, `MessageBox.Show`) w nowym kodzie.
2. **`On Error GoTo` zamiast wyjątków** — obsługa błędów w stylu VB6 ukrywa przyczyny i łamie
   przepływ sterowania. Stosuj `Try ... Catch ... Finally` z przechwytywaniem konkretnych typów
   wyjątków; `Catch ex As Exception` dopuszczaj tylko na najwyższej warstwie z logowaniem.
3. **Składnia C# w kodzie VB** — średniki, klamry, `==`, `!=`, `//` jako komentarz. VB używa końca
   wiersza jako terminatora, `=`/`<>` w porównaniach, `'` jako komentarza oraz słów kluczowych
   `AndAlso`/`OrElse` (zwarciowych) zamiast `And`/`Or` w warunkach.
4. **Pominięcie `Await` lub blokowanie zadania** — wywołanie metody zwracającej `Task` bez `Await`
   gubi wyjątki i porządek wykonania, a `.Result` w kontekście UI prowadzi do zakleszczenia.
   Deklaruj metody jako `Async Function ... As Task` i awaituj na całej ścieżce; `Async Sub`
   rezerwuj wyłącznie dla procedur obsługi zdarzeń.
5. **Deklaracja tablicy przez rozmiar zamiast górnego indeksu** — `Dim items(10) As Integer` tworzy
   11 elementów (indeksy 0–10), bo VB deklaruje górną granicę. Dla n elementów pisz `Dim items(n -
   1)` albo — lepiej — używaj `List(Of T)`.
6. **Założenie, że parametry są `ByRef`** — w VB.NET domyślne jest `ByVal` (odwrotnie niż w VB6).
   Nie „naprawiaj” kodu dopisując `ByRef`; projektuj metody zwracające wartości zamiast mutujących
   argumenty.
7. **Dzielenie `/` tam, gdzie potrzebne całkowite `\`** — operator `/` zawsze zwraca `Double`, `\`
   wykonuje dzielenie całkowite, a `Mod` resztę. Przy `Option Strict On` pomyłka wyjdzie na
   kompilacji; nie obchodź jej rzutowaniem `CInt` bez uzasadnienia (uwaga: `CInt` zaokrągla, nie
   obcina).
8. **Porównywanie typów wartościowych z `Nothing`** — dla `Integer`, `Date` czy `Boolean` wartość
   `Nothing` oznacza wartość domyślną (0, `#1/1/0001#`, `False`), nie brak wartości. Dla
   opcjonalności stosuj `Nullable(Of T)` i sprawdzaj `HasValue`.
9. **Późne wiązanie przez `Object` „bo działa”** — deklarowanie zmiennych jako `Object` i
   wywoływanie składowych bez typu kompiluje się tylko przy `Option Strict Off` i przenosi błędy na
   czas wykonania. Utrzymuj `Option Strict On` i typuj jawnie; wyjątek stanowi celowa automatyzacja
   COM (np. Office Interop).
10. **Zdarzenia podpinane wielokrotnie** — ponowne `AddHandler` przy każdym odświeżeniu formularza
    powoduje wielokrotne wykonywanie procedury obsługi. Podpinaj raz w inicjalizacji, zdejmuj w
    `Dispose`, a przy stałych powiązaniach preferuj klauzulę `Handles`.

Wzorzec poprawny — typowanie i asynchroniczność:

```vb
' Option Strict On wymusza jawne konwersje; Await zachowuje wyjątki i kolejność.
Public Async Function LoadInvoiceAsync(invoiceId As Integer) As Task(Of Invoice)
    Dim invoice = Await _repository.GetByIdAsync(invoiceId)
    If invoice Is Nothing Then
        Throw New KeyNotFoundException($"Brak faktury o identyfikatorze {invoiceId}.")
    End If
    Return invoice
End Function
```

Wzorzec poprawny — bezpieczne rzutowanie zamiast późnego wiązania:

```vb
' TryCast zwraca Nothing zamiast rzucać InvalidCastException.
Dim button = TryCast(sender, Button)
If button IsNot Nothing Then
    button.Enabled = False ' wyłącz przycisk na czas operacji
End If
```
