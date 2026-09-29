# PHP — karta

## Standard stylu i nazewnictwa

Stosuj PSR-1 (podstawy), PSR-12 oraz jego następcę PER Coding Style jako obowiązujące standardy
stylu, a PSR-4 dla autoloadingu. Egzekwuj konwencje nazewnicze:

- klasy, interfejsy, traity, enumy: `PascalCase` (np. `InvoiceRepository`, `PaymentStatus`);
- metody i zmienne: `camelCase` (np. `findByCustomerId`, `$totalAmount`);
- stałe klasowe: `UPPER_SNAKE_CASE` (np. `MAX_RETRY_COUNT`);
- pliki klas: jedna klasa na plik, nazwa pliku identyczna z nazwą klasy (`InvoiceRepository.php`),
  ścieżka zgodna z przestrzenią nazw (PSR-4);
- interfejsy z przyrostkiem opisowym tylko wtedy, gdy przyjęto to w projekcie — sprawdź istniejący
  kod.

Rozpoczynaj pliki wyłącznie z kodem PHP od `<?php` i deklaracji `declare(strict_types=1);`. Typuj
wszystkie parametry, wartości zwracane i właściwości. Narzędzia przyjęte zawodowo: PHP-CS-Fixer lub
PHP_CodeSniffer (`phpcs`/`phpcbf`) do stylu; PHPStan lub Psalm do analizy statycznej — respektuj
poziom (`level`) ustawiony w konfiguracji projektu.

## Struktura projektu

Stosuj minimalny profesjonalny układ zgodny z Composerem i PSR-4:

```
projekt/
├── composer.json         # metadane, zależności, mapowanie autoload PSR-4
├── composer.lock         # commitowany w aplikacjach
├── public/
│   └── index.php         # jedyny punkt wejścia HTTP (front controller)
├── src/                  # przestrzeń nazw App\ lub Vendor\Package\
│   ├── Controller/
│   ├── Repository/
│   └── Service/
├── config/
├── tests/                # struktura lustrzana wobec src/
└── vendor/               # generowany; nigdy nie commitowany, nie edytowany
```

Kanoniczne jest mapowanie autoload w `composer.json` (`"App\\": "src/"`). Czego nie tworzyć: plików
z ręcznymi łańcuchami `require`/`include` do ładowania klas (od tego jest autoloader), kodu
aplikacji w katalogu `public/` poza front controllerem, ani plików mieszających HTML z logiką
domenową — separuj szablony od usług.

## Budowa i zależności

Composer jest jedynym standardem zarządzania zależnościami. Zasady:

- deklaruj zależności w `composer.json` z ograniczeniami semver (`"monolog/monolog": "^3.0"`); nie
  używaj `*` ani `dev-master`;
- `composer.lock` commituj w aplikacjach (powtarzalne wdrożenia); w bibliotekach commit pliku lock
  nie jest wymagany;
- instaluj przez `composer install` (środowiska CI/produkcyjne: `--no-dev --optimize-autoloader`);
  aktualizuj świadomie przez `composer update vendor/package`, nie hurtowo;
- deklaruj wymaganą wersję języka w polu `require.php` (dla nowego kodu PHP 8.1+ ze względu na
  enumy, readonly i typy przecięć);
- po zmianie mapowania przestrzeni nazw uruchom `composer dump-autoload`.

Wersję PHP i rozszerzenia (`ext-pdo`, `ext-mbstring` itd.) traktuj jako zależności jawne w
`composer.json`. Skrypty pomocnicze (lint, testy) rejestruj w sekcji `scripts`.

## Testy

Stosuj PHPUnit jako standardowy framework; Pest jest akceptowalną nadbudową, jeżeli projekt już go
używa — nie mieszaj obu stylów w jednym projekcie. Układ i praktyki:

- katalog `tests/` lustrzany wobec `src/`, klasy `*Test.php` rozszerzające
  `PHPUnit\Framework\TestCase`;
- konfiguracja w `phpunit.xml` lub `phpunit.xml.dist` w katalogu głównym;
- dostawcy danych (`#[DataProvider]`) dla wariantów wejść; `expectException()` dla asercji wyjątków;
- podwójne obiekty twórz przez wbudowane `createMock()`/`createStub()`; nie odpytuj prawdziwej bazy
  ani sieci w testach jednostkowych — warstwę dostępu izoluj interfejsami.

Uruchamiaj testy przez `vendor/bin/phpunit` (lub skrypt `composer test`, jeżeli zdefiniowany). Testy
integracyjne wydzielaj do osobnej suity w `phpunit.xml`, aby dało się je pomijać w szybkim cyklu
deweloperskim.

Przykład nazewnictwa testu — nazwa metody opisuje zachowanie:

```php
public function testDeclinesPaymentWhenCardIsExpired(): void
{
    // przygotowanie, działanie, asercja — w tej kolejności
}
```

## Diagnostyka

Do debugowania krokowego stosuj Xdebug (tryb `debug` z IDE); do profilowania — Xdebug w trybie
`profile` lub Blackfire. W środowisku deweloperskim ustaw `error_reporting(E_ALL)` i
`display_errors=On`; na produkcji wyłącznie logowanie (`log_errors=On`, `display_errors=Off`). Ślad
stosu czytaj od góry: pierwsza linia to miejsce zgłoszenia, kolejne ramki `#0`, `#1`... prowadzą
przez wywołania; szukaj najwyższej ramki z kodu projektu, nie z `vendor/`.

Typowe klasy błędów i ich rozpoznanie:

- `TypeError` — niezgodność typów przy `strict_types=1`; sprawdź sygnaturę i miejsce wywołania, nie
  osłabiaj typów;
- `Error: Call to a member function ... on null` — odpowiednik dereferencji wartości pustej; łańcuch
  wywołań na wyniku, który może być `null` (np. `find()` bez trafienia);
- `Warning: Undefined array key` — dostęp do nieistniejącego klucza; stosuj `??`, `isset()` lub
  jawna walidacja wejścia;
- `Class ... not found` — błąd autoloadingu: niezgodność przestrzeni nazw ze ścieżką pliku lub brak
  `composer dump-autoload`;
- `PDOException` — konfiguruj PDO z `PDO::ERRMODE_EXCEPTION`, aby błędy SQL nie przechodziły
  bezgłośnie.

## Typowe błędy modeli LLM w tym języku

1. **Funkcje `mysql_*`** (`mysql_connect`, `mysql_query`): usunięte z języka od PHP 7. Stosuj PDO
   lub MySQLi — zawsze z zapytaniami przygotowanymi.
2. **Sklejanie danych użytkownika do SQL**: prosta droga do wstrzyknięcia. Poprawny wzorzec:

```php
// parametry wiązane, nigdy interpolacja zmiennych w SQL
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);
```

3. **Luźne porównania `==`**: pułapki koercji typów (np. `'abc' == 0` w starych wersjach, `'1e2' ==
   '100'`). Stosuj `===`/`!==`; do porównań przełącznikowych — `match`, który porównuje ściśle.
4. **Brak `declare(strict_types=1);`**: bez niej deklaracje typów działają w trybie koercji i
   maskują błędy. Dodawaj ją w każdym nowym pliku.
5. **Zamykający znacznik `?>` na końcu pliku czysto PHP**: ryzyko wysłania przypadkowych białych
   znaków (błędy `headers already sent`). Pomijaj znacznik zamykający — tak nakazuje PSR-12.
6. **Halucynowane helpery frameworków w czystym PHP**: funkcje typu `dd()`, `collect()`, `env()`,
   `route()` istnieją w Laravelu, nie w języku. Sprawdź, czy projekt używa danego frameworku, zanim
   użyjesz jego API; w czystym PHP stosuj `var_dump()` tylko diagnostycznie i usuwaj przed oddaniem
   kodu.
7. **Tłumienie błędów operatorem `@`** oraz mieszanie `die()`/`exit()` z logiką: ukrywa awarie i
   uniemożliwia obsługę. Zgłaszaj wyjątki i obsługuj je na granicy aplikacji.
8. **Przestarzała składnia i idiomy**: `array()` zamiast `[]`, zmienne globalne (`global $db`)
   zamiast wstrzykiwania zależności, `create_function()` zamiast funkcji strzałkowych `fn() =>`.
   Stosuj konstruktory z promocją właściwości i `readonly` tam, gdzie wersja języka na to pozwala.
9. **Operacje na datach przez `date()`/`strtotime()` bez stref czasowych**: stosuj
   `DateTimeImmutable` z jawnym `DateTimeZone`; unikaj mutowalnego `DateTime` w kodzie domenowym.
10. **Porównywanie i haszowanie haseł ręcznie** (`md5`, `sha1`): stosuj wyłącznie `password_hash()`
    i `password_verify()`.
