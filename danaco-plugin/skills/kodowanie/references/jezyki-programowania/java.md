# Java — karta

## Standard stylu i nazewnictwa
Stosuj Google Java Style Guide jako obowiązujący standard formatowania. Egzekwuj go
narzędziem google-java-format (formatter) oraz Checkstyle z konfiguracją `google_checks.xml`.
Do analizy statycznej stosuj Error Prone lub SpotBugs; nie wyłączaj reguł bez uzasadnienia
w komentarzu.

Konwencje nazw:
- Klasy, interfejsy, rekordy, enumy: `UpperCamelCase` (`InvoiceProcessor`, `PaymentStatus`).
- Metody, pola, zmienne lokalne, parametry: `lowerCamelCase` (`calculateNetAmount`).
- Stałe (`static final` o niemutowalnej wartości): `UPPER_SNAKE_CASE` (`MAX_RETRY_COUNT`).
- Pakiety: wyłącznie małe litery, bez podkreśleń (`pl.danaco.billing.invoice`).
- Parametry typów generycznych: pojedyncza wielka litera (`T`, `E`, `K`, `V`) lub nazwa
  z sufiksem `T` (`RequestT`).

Nie stosuj notacji węgierskiej ani prefiksów `m_`, `s_`. Nie skracaj nazw kosztem
czytelności (`repo` dopuszczalne, `rpstry` — nie).

## Struktura projektu
Stosuj standardowy układ Maven/Gradle. Nie wymyślaj własnych struktur katalogów.

```
projekt/
├── pom.xml                  (lub build.gradle.kts + settings.gradle.kts)
├── src/
│   ├── main/
│   │   ├── java/pl/danaco/billing/
│   │   └── resources/
│   └── test/
│       ├── java/pl/danaco/billing/
│       └── resources/
└── .gitignore               (target/, build/, .idea/, *.iml)
```

Pakiety organizuj według domeny (`invoice`, `customer`), a nie według warstwy technicznej
(`controllers`, `services`) — chyba że istniejący projekt stosuje inną konwencję; wtedy
zachowaj spójność z projektem. Nie twórz katalogów `utils` jako zbiornika na przypadkowy
kod. Nie commituj katalogów `target/` ani `build/`.

## Budowa i zależności
Stosuj Maven lub Gradle zgodnie z istniejącym projektem; dla nowych projektów preferuj
Gradle z Kotlin DSL (`build.gradle.kts`) lub Maven, jeżeli zespół już go używa.

- Celuj w aktualną wersję LTS: Java 17+ LTS jako minimum, Java 21+ LTS dla nowych
  projektów. Ustaw ją jawnie (`maven.compiler.release` / `java.toolchain`).
- Przypinaj dokładne wersje zależności. W Maven stosuj `dependencyManagement` i BOM-y
  (np. `spring-boot-dependencies`); w Gradle — version catalog (`gradle/libs.versions.toml`)
  lub platformy (`platform(...)`).
- Nie dodawaj zależności, której nie użyjesz. Przed dodaniem biblioteki sprawdź, czy JDK
  lub już obecne zależności nie pokrywają potrzeby (np. `java.net.http.HttpClient`
  zamiast kolejnego klienta HTTP).
- Commituj wrapper (`mvnw`, `gradlew`) i buduj przez wrapper, nie przez lokalną instalację.

## Testy
Stosuj JUnit 5 (JUnit Jupiter) z AssertJ do asercji oraz Mockito do atrap. Nie stosuj
JUnit 4 w nowym kodzie.

- Testy umieszczaj w `src/test/java` w pakiecie lustrzanym wobec kodu produkcyjnego.
- Nazwa klasy testowej: `<KlasaTestowana>Test`. Nazwy metod opisują zachowanie,
  np. `rejectsInvoiceWithNegativeAmount`.
- Stosuj `@ParameterizedTest` zamiast kopiowania niemal identycznych testów.
- Testuj zachowanie przez publiczne API; nie zmieniaj widoczności metod wyłącznie
  na potrzeby testu.
- Uruchamianie: `./mvnw test` lub `./gradlew test`. Pojedyncza klasa:
  `./mvnw test -Dtest=InvoiceProcessorTest` albo `./gradlew test --tests '*.InvoiceProcessorTest'`.

## Diagnostyka
- Czytaj ślad stosu od góry: pierwszy wpis wskazujący na kod projektu to zwykle miejsce
  błędu. Analizuj też sekcje `Caused by:` — przyczyna źródłowa jest na końcu łańcucha.
- `NullPointerException` w Java 15+ zawiera helpful message wskazujący, które wyrażenie
  było nullem — cytuj go w diagnozie zamiast zgadywać.
- Do profilowania stosuj Java Flight Recorder (`java -XX:StartFlightRecording=...`,
  analiza w JDK Mission Control) lub VisualVM; do szybkiego wglądu w działający proces —
  `jcmd`, `jstack` (zrzut wątków, wykrywanie deadlocków), `jmap`/`jcmd GC.heap_dump`
  (zrzut sterty), Eclipse MAT do analizy wycieków pamięci.
- Typowe klasy błędów: `NullPointerException` (brak walidacji wejścia, `Optional.get()`
  bez sprawdzenia), `ConcurrentModificationException` (modyfikacja kolekcji podczas
  iteracji), `ClassCastException` po surowych typach generycznych, deadlocki przy
  zagnieżdżonych `synchronized`, wycieki wątków przy niezamkniętych `ExecutorService`.

## Typowe błędy modeli LLM w tym języku
1. **`java.util.Date` i `SimpleDateFormat` zamiast `java.time`.** Stosuj `LocalDate`,
   `Instant`, `ZonedDateTime`, `DateTimeFormatter` — są niemutowalne i bezpieczne
   wątkowo; `SimpleDateFormat` nie jest i powoduje trudne do wykrycia błędy współbieżne.
2. **`Optional.get()` bez sprawdzenia obecności.** Stosuj `orElse`, `orElseThrow`,
   `map`, `ifPresent`. Nie stosuj `Optional` jako typu pola ani parametru metody —
   to typ zwracany.
3. **Puste lub logujące-i-połykające bloki `catch (Exception e)`.** Łap najwęższy
   sensowny typ wyjątku; propaguj albo opakuj z zachowaniem przyczyny
   (`throw new DomainException("...", e)`). Nigdy nie gub oryginalnego wyjątku.
4. **Porównywanie obiektów przez `==` zamiast `equals`.** Dotyczy `String`, `Integer`
   (cache tylko dla -128..127) i innych obiektów. `==` porównuje referencje; poprawnie:
   `Objects.equals(a, b)`.
5. **Ręczne klasy DTO z getterami/setterami i mutowalnym stanem tam, gdzie wystarczy
   `record`.** Od Java 16 stosuj `record` dla niemutowalnych nośników danych; nie
   generuj dziesiątek wierszy boilerplate.
6. **Konkatenacja `String` w pętli.** Stosuj `StringBuilder` albo `String.join` /
   `Collectors.joining`; konkatenacja w pętli ma złożoność kwadratową.
7. **Niezamykanie zasobów.** Każdy `InputStream`, `Connection`, `HttpClient`-owe body
   itd. otwieraj w `try-with-resources`. Nie polegaj na finalizerach ani na GC.
8. **Halucynowane API i wersje bibliotek.** Nie wywołuj metod, których istnienia nie
   jesteś pewien (np. nieistniejące metody na `List` czy w Springu); sprawdź w kodzie
   projektu lub javadoc dostępnej wersji zależności — sygnatury różnią się między
   wersjami frameworków.
9. **Nadużywanie streamów tam, gdzie pętla jest czytelniejsza** — i odwrotnie: mutowanie
   zewnętrznego stanu wewnątrz `forEach`. Stream ma być czysty; efekty uboczne wykonuj
   w zwykłej pętli albo przez `collect`.
10. **Ignorowanie ostrzeżeń o surowych typach i niesprawdzonych rzutowaniach.**
    Parametryzuj typy generyczne w pełni; `@SuppressWarnings("unchecked")` stosuj
    tylko z komentarzem uzasadniającym lokalne bezpieczeństwo rzutowania.
