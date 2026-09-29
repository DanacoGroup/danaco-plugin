# Delphi / Object Pascal — karta

## Standard stylu i nazewnictwa

- Stosuj oficjalny Object Pascal Style Guide (dokumentacja Embarcadero DocWiki) jako podstawę stylu;
  ustalenia projektu zastanego mają pierwszeństwo, jeżeli są spójne.
- Nazewnictwo przedrostkowe zgodne z konwencją języka:
  - `T` dla klas i typów (`TInvoiceCalculator`), `I` dla interfejsów (`IInvoiceRepository`), `E` dla
    klas wyjątków (`EInvoiceNotFound`);
  - `F` dla pól prywatnych (`FConnection`), `A` dla parametrów tam, gdzie kolidują z nazwami
    właściwości (`AOwner`);
  - `PascalCase` dla metod, właściwości i zmiennych lokalnych; słowa kluczowe języka pisane małymi
    literami (`begin`, `end`, `procedure`).
- Używaj pełnych nazw jednostek z przestrzeniami nazw (`System.SysUtils`,
  `System.Generics.Collections`, `Vcl.Forms`), nie form skróconych z wersji sprzed Delphi XE2.
- Nie używaj konstrukcji `with` — zaciemnia zasięg identyfikatorów i jest powszechnie uznawana za
  szkodliwą; pisz odwołania jawnie lub wprowadź zmienną lokalną.
- Metody wirtualne nadpisuj zawsze ze słowem `override`; jego brak tworzy metodę przesłaniającą i
  cichą zmianę zachowania polimorficznego.
- Deklaracje `var` inline (`var Total := 0;`) stosuj tylko, gdy projekt celuje w Delphi 10.3 Rio lub
  nowsze; w kodzie dla starszych wersji deklaruj zmienne w sekcji `var` przed `begin`.

## Struktura projektu

- Minimalny profesjonalny układ:
  - plik projektu `*.dpr` (program) oraz `*.dproj` (ustawienia budowy MSBuild);
  - jednostki `*.pas` w katalogu źródeł, formularze jako pary `*.pas` + `*.dfm` (VCL) lub `*.fmx`
    (FireMonkey);
  - opcjonalnie `*.groupproj` dla wielu projektów (aplikacja + testy);
  - `.gitignore` obejmujący `*.dcu`, `*.exe`, `*.local`, `*.identcache`, `*.stat` oraz katalog
    `__history`.
- Rozdzielaj logikę od interfejsu: jednostki domenowe nie mogą zależeć od `Vcl.*` ani `FMX.*`;
  formularz wywołuje logikę, nigdy odwrotnie.
- Ustal na starcie framework interfejsu — VCL (Windows) albo FireMonkey (wieloplatformowo) — i nie
  mieszaj ich jednostek w jednym module.
- Czego nie tworzyć:
  - plików `*.dcu` i katalogów wyjściowych w repozytorium;
  - logiki biznesowej w procedurach obsługi zdarzeń formularza (`Button1Click` z setką wierszy);
  - komponentów o domyślnych nazwach (`Button1`, `Edit3`) — nadawaj nazwy znaczące
    (`btnSaveInvoice`, `edtCustomerName`);
  - globalnych zmiennych stanu w sekcji `interface` jednostek.

## Budowa i zależności

- Buduj z wiersza poleceń przez MSBuild po załadowaniu środowiska `rsvars.bat` (`msbuild
  Projekt.dproj /t:Build /p:Config=Release`); kompilatorem jest `dcc32`/`dcc64` wywoływany przez
  MSBuild.
- Utrzymuj konfiguracje Debug i Release w `*.dproj`: Debug z pełną informacją debugową, asercjami i
  kontrolą zakresu (`Range checking`, `Overflow checking`); Release zoptymalizowany.
- Zależności zewnętrzne dokumentuj jawnie: źródło (GetIt Package Manager, repozytorium dostawcy),
  dokładną wersję i procedurę instalacji; ekosystem Delphi nie ma jednego dominującego menedżera
  pakietów z lockfile, więc przypinanie wersji egzekwuj przez wendorowanie źródeł lub zapis wersji w
  dokumentacji budowy.
- Zapisuj w projekcie wymaganą wersję Delphi (np. 11 Alexandria, 12 Athens) — pliki `*.dproj` i
  składnia nie są w pełni przenośne między wersjami.
- Ścieżki wyszukiwania (`Search Path`) definiuj w pliku projektu, nie wyłącznie w globalnych
  ustawieniach IDE — budowa musi działać na czystej stacji i na CI.

## Testy

- Stosuj DUnitX jako framework testów jednostkowych dla nowego kodu; klasyczny DUnit utrzymuj tylko
  w projektach zastanych, które już go używają.
- Projekt testowy prowadź jako osobny `*.dproj` konsolowy w tym samym `*.groupproj`; klasy testowe
  oznaczaj atrybutami `[TestFixture]` i `[Test]`, przypadki parametryzowane — `[TestCase]`.
- Testuj jednostki domenowe bez tworzenia formularzy; zależności izoluj przez interfejsy
  wstrzykiwane w konstruktorze, do atrap można stosować Delphi Mocks lub proste implementacje
  testowe.
- W testach kodu zarządzającego pamięcią sprawdzaj zwalnianie obiektów; włącz
  `ReportMemoryLeaksOnShutdown := True` w projekcie testowym, aby wycieki ujawniały się przy
  zakończeniu.
- Uruchamiaj pełny zestaw testów z wiersza poleceń (zbudowany runner konsolowy zwraca kod wyjścia)
  przed zgłoszeniem zadania jako ukończonego.

## Diagnostyka

- Używaj zintegrowanego debuggera IDE Delphi: punkty przerwania (także warunkowe i z licznikiem
  przejść), okna Local Variables, Watches, Call Stack, Events oraz widok CPU przy błędach
  niskopoziomowych.
- Włącz w konfiguracji Debug kontrole `Range checking` i `Overflow checking` — zamieniają ciche
  uszkodzenie danych na jawny wyjątek w miejscu błędu.
- Typowe klasy błędów:
  - `Access Violation` przy adresie bliskim zeru — odwołanie do obiektu `nil` lub użycie obiektu po
    zwolnieniu (`use-after-free`); ustal właściciela obiektu i moment zwolnienia;
  - wycieki pamięci — brak `Free` dla obiektu bez właściciela; diagnozuj przez
    `ReportMemoryLeaksOnShutdown` (wbudowany FastMM) i przeglądaj raport przy zamknięciu;
  - `EInvalidCast` przy `as` — sprawdzaj typ operatorem `is` przed rzutowaniem;
  - zawieszenia interfejsu — długa operacja w wątku głównym; przenoś pracę do `TTask`/`TThread`, a
    interfejs aktualizuj wyłącznie przez `TThread.Queue` lub `Synchronize`.
- Czytaj komunikaty kompilatora od pierwszego błędu w jednostce; błędy typu `Undeclared identifier`
  bywają skutkiem brakującej jednostki w klauzuli `uses`, nie literówki.
- Pamiętaj, że łańcuchy `string` są indeksowane od 1 na platformach desktopowych — błędy
  „off-by-one” przy pracy z `Copy`, `Pos` i indeksowaniem znaków są klasyczną pomyłką.
- Wyjątki „znikające” w kodzie zdarzeniowym wychwytuj przez `Application.OnException` z logowaniem;
  nie zostawiaj pustych bloków `except`.
- Diagnozuj metodycznie: minimalna reprodukcja, jedna hipoteza, jedna zmiana; nie poprawiaj wielu
  jednostek naraz bez potwierdzenia przyczyny.

## Typowe błędy modeli LLM w tym języku

1. **Przestarzałe komponenty i jednostki** — proponowanie BDE (`TTable`, `TQuery`, dawno
   wycofanego), starych nazw jednostek bez przestrzeni (`SysUtils` zamiast `System.SysUtils`) albo
   komponentów usuniętych z palety. Stosuj FireDAC do dostępu do danych i aktualne nazwy jednostek;
   sprawdź dostępność komponentu w docelowej wersji Delphi.
2. **Brak `try..finally` przy ręcznym zarządzaniu pamięcią** — Delphi (desktop) nie ma odśmiecania
   obiektów; każdy obiekt utworzony bez właściciela musi być zwolniony w `finally`. Wzorzec
   obowiązkowy: `Obj := TThing.Create; try ... finally Obj.Free; end;`.
3. **Ignorowanie modelu własności `TComponent`** — komponent utworzony z właścicielem
   (`TButton.Create(Form)`) zostanie zwolniony przez właściciela; ręczne `Free` takiego obiektu albo
   — odwrotnie — brak zwalniania obiektu utworzonego z `nil` prowadzi do podwójnego zwolnienia lub
   wycieku. Zawsze określ, kto jest właścicielem.
4. **Semantyka łańcuchów sprzed Delphi 2009** — założenie, że `string` to łańcuch jednobajtowy,
   rzutowania na `PChar` traktowane jak `PAnsiChar`, ręczne przeliczanie bajtów na znaki. Od Delphi
   2009 `string` = `UnicodeString` (UTF-16); do operacji bajtowych używaj `TEncoding` i `TBytes`.
5. **Logika w procedurach obsługi zdarzeń** — umieszczanie reguł biznesowych bezpośrednio w
   `OnClick`. Przenoś logikę do klas domenowych; zdarzenie ma tylko zebrać dane z kontrolek, wywołać
   metodę i zaprezentować wynik.
6. **Składnia nowsza niż docelowy kompilator** — inline `var`, wnioskowanie typów czy operatory
   ternarne z innych języków (Delphi nie ma operatora `?:` — istnieje funkcja `IfThen` z
   `System.Math`/`System.StrUtils`). Ustal wersję Delphi projektu przed pisaniem i trzymaj się jej
   składni.
7. **Mieszanie VCL z FireMonkey** — dodanie `Vcl.Dialogs` do projektu FMX (lub odwrotnie) kompiluje
   się czasem na Windows, ale łamie przenośność i dubluje typy o tych samych nazwach. W projekcie
   FMX używaj wyłącznie jednostek `FMX.*`.
8. **Porównywanie łańcuchów bez określenia wrażliwości** — `=` porównuje z rozróżnianiem wielkości
   liter. Używaj `SameText` dla porównań bez rozróżniania i `SameStr` dla ścisłych; nie pisz
   `LowerCase(A) = LowerCase(B)`.
9. **`FreeAndNil` i `Free` stosowane bez zrozumienia** — wywoływanie metod na zwolnionym obiekcie,
   bo referencja nie została wyzerowana, albo `FreeAndNil` na referencji interfejsu (zakazane —
   interfejsy zwalniaj przez przypisanie `nil` i zliczanie referencji). Nie mieszaj referencji
   obiektowych z interfejsowymi do tego samego egzemplarza.
10. **Aktualizacja interfejsu z wątku roboczego** — bezpośrednie ustawianie właściwości kontrolek z
    `TTask`/`TThread` powoduje losowe awarie. Każdą aktualizację UI kieruj przez `TThread.Queue`
    (asynchronicznie) lub `TThread.Synchronize` (synchronicznie).

Wzorzec poprawny — cykl życia obiektu bez właściciela:

```pascal
// try..finally gwarantuje zwolnienie także przy wyjątku.
var Report := TInvoiceReport.Create;
try
  Report.Build(Invoice);
  Report.SaveToFile(TargetPath);
finally
  Report.Free; // obiekt bez właściciela zwalniamy jawnie
end;
```

Wzorzec poprawny — bezpieczna aktualizacja interfejsu z wątku roboczego:

```pascal
// Praca w tle; wynik trafia do UI wyłącznie przez kolejkę wątku głównego.
TTask.Run(
  procedure
  var Total: Currency;
  begin
    Total := FCalculator.CalculateTotal(InvoiceId); // operacja długotrwała
    TThread.Queue(nil,
      procedure
      begin
        lblTotal.Caption := CurrToStr(Total); // aktualizacja w wątku głównym
      end);
  end);
```
