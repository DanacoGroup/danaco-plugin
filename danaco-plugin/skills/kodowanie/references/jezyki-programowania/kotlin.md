# Kotlin — karta

## Standard stylu i nazewnictwa
Stosuj oficjalne Kotlin Coding Conventions (kotlinlang.org) jako obowiązujący standard.
Formatowanie i lintowanie egzekwuj narzędziem ktlint (styl oficjalny) lub ktfmt; do
analizy statycznej stosuj detekt. W Gradle ustaw `kotlin.code.style=official`
w `gradle.properties`.

Konwencje nazw:
- Klasy, interfejsy, obiekty, aliasy typów: `UpperCamelCase` (`InvoiceRepository`).
- Funkcje, właściwości, zmienne lokalne: `lowerCamelCase` (`fetchOverdueInvoices`).
- Stałe `const val` oraz niemutowalne wartości top-level o charakterze stałych:
  `UPPER_SNAKE_CASE` (`DEFAULT_TIMEOUT_MS`).
- Pakiety: małe litery, bez podkreśleń (`pl.danaco.billing.invoice`).
- Funkcje testowe mogą mieć nazwy w grawisach: `` fun `rejects negative amount`() ``.

Nie stosuj prefiksów `m` ani `I` dla interfejsów. Preferuj wyrażenia jednowierszowe
(`fun total() = items.sumOf { it.amount }`) tylko wtedy, gdy pozostają czytelne.

## Struktura projektu
Stosuj układ Gradle; dla czystego Kotlina katalog `src/main/kotlin`, dla projektów
mieszanych z Javą — oba katalogi równolegle.

```
projekt/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle/libs.versions.toml     (version catalog)
├── src/
│   ├── main/
│   │   ├── kotlin/pl/danaco/billing/
│   │   └── resources/
│   └── test/
│       └── kotlin/pl/danaco/billing/
└── .gitignore                    (build/, .gradle/, .idea/)
```

Wiele powiązanych, małych deklaracji (np. sealed interface z wariantami) trzymaj
w jednym pliku — Kotlin tego nie zabrania i konwencje to zalecają. Nie twórz pliku
na każdą klasę na wzór Javy, jeżeli deklaracje są ściśle powiązane. Nie commituj
katalogu `build/`.

## Budowa i zależności
Stosuj Gradle z Kotlin DSL (`build.gradle.kts`); Maven tylko wtedy, gdy wymaga tego
istniejący projekt.

- Celuj w aktualną stabilną wersję Kotlina (linia 2.x) i JVM toolchain oparty na
  Java 17+ LTS (`kotlin { jvmToolchain(21) }` dla nowych projektów).
- Przypinaj wersje zależności w version catalogu (`gradle/libs.versions.toml`);
  nie wpisuj wersji literałami rozsianymi po plikach budowy.
- Współprogramy: zależność `kotlinx-coroutines-core` (oraz `kotlinx-coroutines-test`
  w testach); serializacja: `kotlinx-serialization` z pluginem kompilatora.
- Commituj wrapper i buduj przez `./gradlew`; nie zakładaj lokalnej instalacji Gradle.

## Testy
Stosuj JUnit 5 jako silnik uruchomieniowy; asercje pisz w kotlin.test, AssertJ lub
Kotest (assertions) — spójnie z resztą projektu. Do atrap stosuj MockK (naturalny dla
Kotlina), nie Mockito, chyba że projekt już standaryzuje Mockito z mockito-kotlin.

- Testy w `src/test/kotlin`, pakiet lustrzany wobec kodu produkcyjnego; klasa
  `<KlasaTestowana>Test`.
- Kod z współprogramami testuj przez `runTest` z `kotlinx-coroutines-test` — nie przez
  `runBlocking` z ręcznymi opóźnieniami; `runTest` przewija wirtualny czas (`delay`
  nie blokuje testu).
- Uruchamianie: `./gradlew test`; pojedyncza klasa:
  `./gradlew test --tests '*.InvoiceProcessorTest'`.

## Diagnostyka
- Ślady stosu czytaj jak w Javie (sekcje `Caused by:` do końca łańcucha). W kodzie
  z współprogramami ślady bywają ucięte na granicach wznowień; w środowisku
  deweloperskim pomaga `-Dkotlinx.coroutines.debug` (nazwy współprogramów w wątkach).
- Profilowanie na JVM: Java Flight Recorder + JDK Mission Control, VisualVM, async-profiler.
  Zrzut wątków: `jstack`; deadlocki `synchronized` są w nim oznaczane wprost.
- Typowe klasy błędów: `NullPointerException` na granicy z Javą (typy platformowe —
  wartości z API Javy bez adnotacji nullowalności), `KotlinNullPointerException` /
  NPE z operatora `!!`, `ConcurrentModificationException`, zawieszenia przy
  `runBlocking` wywołanym z wątku dyspozytora, anulowanie współprogramu połknięte
  przez zbyt szeroki `catch`.
- Przy zawieszonym programie sprawdź, czy `Job` nie czeka na dzieci, których nikt
  nie anulował, oraz czy kanały/`Flow` mają odbiorców.

## Typowe błędy modeli LLM w tym języku
1. **Nadużywanie operatora `!!`.** `!!` zamienia null w wyjątek w miejscu użycia i jest
   przyznaniem się do braku obsługi. Stosuj `?.`, `?:` (elvis), `requireNotNull(x) { "..." }`
   z komunikatem albo przeprojektuj typ na nienullowalny.
2. **Pisanie Javy w składni Kotlina.** Ręczne gettery/settery, klasy z mutowalnymi polami
   i `if (x != null)` zamiast idiomów: `data class`, `val` domyślnie, `let`/`when`,
   parametry domyślne zamiast przeciążeń i wzorca builder.
3. **`lateinit var` tam, gdzie wystarczy konstruktor lub `by lazy`.** `lateinit` odracza
   błąd do czasu wykonania (`UninitializedPropertyAccessException`); rezerwuj go dla
   wstrzykiwania zależności przez framework.
4. **`GlobalScope.launch` do uruchamiania współprogramów.** Łamie ustrukturyzowaną
   współbieżność: brak anulowania i propagacji błędów. Stosuj zakres cyklu życia
   (`viewModelScope`, `lifecycleScope`, własny `CoroutineScope` z `SupervisorJob`)
   albo `coroutineScope { }`.
5. **`runBlocking` wewnątrz kodu asynchronicznego.** Blokuje wątek dyspozytora i potrafi
   zakleszczyć aplikację; `runBlocking` jest dozwolony w `main`, testach bez `runTest`
   i na granicy z kodem blokującym — nigdzie indziej.
6. **Łapanie `Exception` w współprogramach z połknięciem `CancellationException`.**
   Anulowanie propaguje się wyjątkiem; po złapaniu szerokiego typu przerzuć je dalej
   (`if (e is CancellationException) throw e`) albo łap węższe typy.
7. **Mutowalne kolekcje i `var` w API publicznym.** Zwracaj `List`, `Map`, `Set`
   (interfejsy tylko do odczytu) i deklaruj `val`; `MutableList` w sygnaturze publicznej
   wyklucza gwarancje niemutowalności.
8. **Ignorowanie typów platformowych na granicy z Javą.** Wartość z Javy traktuj jak
   potencjalnie nullowalną: przypisuj jawny typ (`val name: String?`) albo waliduj
   na wejściu, zamiast pozwolić NPE wystąpić w głębi programu.
9. **Halucynowane funkcje biblioteki standardowej i API coroutines.** Nie wymyślaj
   wariantów `mapNotNullIndexed`-podobnych ani przeciążeń `Flow`; sprawdź istnienie
   funkcji w dokumentacji lub przez kompilację, zanim jej użyjesz.
10. **`data class` do wszystkiego.** `data class` wymaga sensownej semantyki równości
    po wszystkich właściwościach konstruktora głównego; dla bytów z tożsamością
    (encje) lub klas usługowych stosuj zwykłą klasę.
