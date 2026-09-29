# Node.js — karta

Przeczytaj tę kartę w całości przed rozpoczęciem pracy z kodem serwerowym Node.js. Dotyczy ona
Node.js jako środowiska uruchomieniowego usług zaplecza; konwencje frameworków przeglądarkowych
opisują odrębne karty.

## Struktura projektu

Przyjmij układ warstwowy z jawnym punktem wejścia i rozdzieleniem transportu od logiki:

```
projekt/
├── package.json        # "type": "module", skrypty, silniki
├── src/
│   ├── index.js        # punkt wejścia: start serwera, obsługa sygnałów
│   ├── app.js          # złożenie aplikacji (np. instancja Express/Fastify)
│   ├── config.js       # odczyt i walidacja zmiennych środowiskowych
│   ├── routes/         # warstwa transportu HTTP: parsowanie, kody statusu
│   ├── services/       # logika biznesowa, bez wiedzy o HTTP
│   ├── repositories/   # dostęp do danych, zapytania, sterowniki
│   └── middleware/     # uwierzytelnianie, dzienniki, obsługa błędów
└── test/               # testy odzwierciedlające strukturę src/
```

Przestrzegaj granic: trasy nie zawierają zapytań do bazy, serwisy nie importują obiektów
`req`/`res`, repozytoria nie znają reguł biznesowych. Oddziel tworzenie aplikacji (`app.js`) od jej
uruchomienia (`index.js`) — umożliwia to testowanie bez otwierania portu. Nie twórz katalogu „utils”
jako składowiska przypadkowego kodu; nie generuj plików konfiguracyjnych narzędzi, których projekt
nie używa.

## Konwencje frameworka

- Pisz w ESM: `import`/`export`, `"type": "module"` w `package.json`. W zastanym projekcie CommonJS
  pozostań przy `require` — nigdy nie mieszaj obu systemów w jednym pliku.
- Używaj `async`/`await` z obowiązkowym `try`/`catch` na granicach warstw; nie pozostawiaj wywołań
  asynchronicznych bez obsługi odrzucenia. Nieprzechwycone odrzucenie obietnicy kończy proces Node.
- W Express przekazuj błędy asynchroniczne do `next(err)` i centralnego middleware błędów (sygnatura
  czteroargumentowa); pamiętaj, że Express 4 nie przechwytuje samoczynnie wyjątków z funkcji `async`
  — wymagane jest `try`/`catch` lub opakowanie. Fastify obsługuje funkcje `async` natywnie.
- Preferuj wbudowane moduły z prefiksem `node:` (`node:fs/promises`, `node:path`, `node:crypto`) nad
  zewnętrznymi zależnościami o tej samej funkcji.
- Strumienie łącz przez `pipeline` z `node:stream/promises`, który propaguje błędy i sprząta zasoby;
  nie używaj gołego `.pipe()` bez obsługi zdarzenia `error` na każdym strumieniu.
- Obsługuj `SIGTERM`/`SIGINT`: zamknij serwer (`server.close`), dokończ bieżące żądania, zamknij
  pule połączeń, zakończ proces jawnie. Usługa bez łagodnego zamknięcia gubi żądania przy wdrożeniu.
- Nie blokuj pętli zdarzeń: ciężkie obliczenia przenieś do `worker_threads`, kryptografię wywołuj w
  wariantach asynchronicznych, nie używaj wariantów `*Sync` po starcie serwera.
- Rzucaj wyłącznie instancje `Error` (lub podklas) i zachowuj przyczynę pierwotną przez opcję
  `cause`; nie rzucaj łańcuchów znaków ani obiektów bez śladu stosu.

Wzorce obowiązkowe:

```js
// index.js — start i łagodne zamknięcie procesu
const server = app.listen(config.port);

async function shutdown() {
  // najpierw przestań przyjmować nowe połączenia, potem zwolnij zasoby
  await new Promise((resolve) => server.close(resolve));
  await db.end();
  process.exit(0);
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
```

```js
// przetwarzanie strumieniowe — pipeline propaguje błędy i sprząta zasoby
import { pipeline } from "node:stream/promises";
import { createReadStream, createWriteStream } from "node:fs";
import { createGzip } from "node:zlib";

await pipeline(
  createReadStream(inputPath),
  createGzip(),
  createWriteStream(outputPath),
);
```

## Konfiguracja i sekrety

- Czytaj konfigurację wyłącznie ze zmiennych środowiskowych, w jednym module (`config.js`), z
  walidacją obecności i typów przy starcie. Brak wymaganej zmiennej ma przerywać start procesu z
  czytelnym komunikatem.
- Lokalnie używaj pliku `.env` (natywna flaga `--env-file` w nowszych wydaniach Node lub pakiet
  `dotenv`). Nie wczytuj `.env` w kodzie produkcyjnym bezwarunkowo.
- Nie commituj: `.env`, kluczy prywatnych, tokenów, danych dostępowych do bazy, katalogu
  `node_modules`. Commituj `.env.example` oraz plik blokady zależności (`package-lock.json`).
- Nie wpisuj sekretów w kod, w `package.json` ani w pliki konfiguracyjne narzędzi. Nie rejestruj
  sekretów w dziennikach — maskuj je w warstwie logowania.
- Rozróżniaj konfigurację (port, adresy usług, poziomy dziennika) od sekretów (hasła, klucze); obie
  grupy pochodzą ze środowiska, ale sekrety podlegają dodatkowo rotacji i maskowaniu.

## Testy

- Używaj wbudowanego `node:test` z `node:assert/strict` (bez dodatkowych zależności) lub Vitest,
  jeżeli projekt już z niego korzysta. Wybierz jedno narzędzie na projekt.
- Testuj warstwę HTTP przez rzeczywiste żądania do instancji aplikacji (np. `fetch` na serwerze
  związanym z portem efemerycznym lub pakiet `supertest` dla Express); logikę serwisów testuj
  jednostkowo z podmienionymi repozytoriami.
- Wstrzykuj zależności przez parametry konstruktorów lub fabryk, aby testy nie wymagały mechanizmów
  podmiany modułów; podmiana importów ESM jest zawodna.
- Testuj ścieżki błędów: odrzucone obietnice, przerwane strumienie, przekroczenia czasu. Sprawdzaj
  odrzucenia przez `assert.rejects`, nie przez `try`/`catch` z flagą.
- Uruchamiaj testy skryptem `npm test`; testy muszą przechodzić bez dostępu do sieci zewnętrznej i
  bez wcześniej uruchomionych usług lokalnych.

Wzorzec testu w `node:test`:

```js
// test/order-service.test.js — repozytorium podmienione przez wstrzyknięcie
import { test } from "node:test";
import assert from "node:assert/strict";
import { createOrderService } from "../src/services/order-service.js";

test("create rejects on unknown product", async () => {
  const fakeRepository = { findProduct: async () => null };
  const service = createOrderService(fakeRepository);
  await assert.rejects(
    () => service.create({ productId: 999, quantity: 1 }),
    { name: "ProductNotFoundError" },
  );
});
```

## Diagnostyka

- Uruchom proces z flagą `--inspect` (lub `--inspect-brk` dla zatrzymania na starcie) i podłącz
  inspektor przez `chrome://inspect` albo debuger edytora; wstawianie `console.log` traktuj jako
  ostateczność, nie metodę pracy.
- Komunikat `ERR_UNHANDLED_REJECTION` oznacza odrzuconą obietnicę bez obsługi; znajdź wywołanie
  asynchroniczne pozbawione `await` lub `.catch`. Flaga `--trace-uncaught` i zdarzenie
  `process.on('unhandledRejection')` pomagają wskazać źródło, lecz nie zastępują poprawnej obsługi
  błędów.
- `ERR_REQUIRE_ESM` i `ERR_MODULE_NOT_FOUND` to niemal zawsze konflikt systemów modułów lub brak
  rozszerzenia pliku w imporcie ESM — sprawdź pole `"type"` w `package.json` i pełne ścieżki z
  rozszerzeniem.
- `EADDRINUSE` oznacza zajęty port: znajdź proces (`lsof -i :PORT` lub `ss -ltnp`) zamiast zmieniać
  port na oślep.
- Wycieki pamięci diagnozuj zrzutami sterty (inspektor lub `--heapsnapshot-signal`), a zawieszenia
  pętli zdarzeń — profilowaniem procesora; nie zgaduj na podstawie objawów.

## Typowe błędy modeli LLM w tym frameworku

1. **Mieszanie `require` z `import` w jednym pliku.** Prowadzi do `ERR_REQUIRE_ESM` lub błędów
   składni. Ustal system modułów na podstawie `package.json` i istniejących plików, po czym stosuj
   go konsekwentnie; w ESM odpowiednikiem `__dirname` jest `import.meta.dirname` lub wyprowadzenie z
   `import.meta.url`.
2. **Brak obsługi błędów strumieni.** `readable.pipe(writable)` bez nasłuchu `error` na obu końcach
   gubi błędy i przecieka deskryptory. Używaj `pipeline` z `node:stream/promises` z `await` i
   `try`/`catch`.
3. **Trasa `async` w Express 4 bez przechwycenia błędu.** Odrzucona obietnica nie trafia do
   middleware błędów — żądanie wisi lub proces pada. Opakuj trasę w `try`/`catch` z `next(err)` albo
   użyj opakowania przekazującego odrzucenia do `next`.
4. **Operacje `*Sync` w ścieżce obsługi żądań.** `fs.readFileSync`, `crypto.pbkdf2Sync` czy
   `child_process.execSync` blokują pętlę zdarzeń dla wszystkich klientów. Warianty synchroniczne
   dopuszczaj wyłącznie w fazie startu procesu.
5. **Sekwencyjne `await` niezależnych operacji.** Pobrania niezależnych danych wykonuj równolegle:
   `Promise.all` (lub `Promise.allSettled`, gdy częściowe niepowodzenie jest dopuszczalne), zamiast
   łańcucha kolejnych `await`.
6. **`await` wewnątrz `Array.prototype.forEach`.** `forEach` ignoruje zwracane obietnice — pętla
   „kończy się” przed operacjami. Używaj `for...of` dla przebiegu sekwencyjnego lub
   `Promise.all(items.map(...))` dla równoległego.
7. **Instalowanie zależności zamiast użycia modułów wbudowanych.** Dodawanie pakietów do UUID,
   kopiowania plików czy prostych żądań HTTP, gdy istnieją `node:crypto` (`randomUUID`),
   `node:fs/promises` i globalny `fetch`. Każda zależność to koszt utrzymania i powierzchnia ataku.
8. **Budowanie zapytań SQL i poleceń powłoki przez konkatenację.** Wstrzyknięcia SQL i poleceń.
   Używaj zapytań parametryzowanych sterownika oraz `execFile`/`spawn` z tablicą argumentów zamiast
   `exec` ze sklejonym łańcuchem.
9. **Połykanie błędów.** Pusty blok `catch` lub `catch (e) { console.log(e) }` z kontynuacją
   przepływu ukrywa awarie. Błąd obsłuż (odpowiedź z właściwym kodem, ponowienie, wartość zastępcza)
   albo rzuć dalej z kontekstem (`throw new Error("...", { cause: e })`).
10. **Halucynowane API i wersje.** Zmyślone opcje `fs`, nieistniejące metody frameworków, składnia z
    innych środowisk uruchomieniowych (Deno, Bun). W razie niepewności sprawdź dokumentację lub
    istniejące użycia w projekcie zamiast zgadywać.
