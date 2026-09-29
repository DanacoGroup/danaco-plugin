# JavaScript i TypeScript — karta

## Standard stylu i nazewnictwa

- Stosuj ESLint z zestawami `@eslint/js` (recommended) oraz `typescript-eslint` (strict + stylistic)
  jako źródło reguł jakości.
- Formatowanie pozostaw wyłącznie Prettierowi; konflikty reguł formatujących eliminuj przez
  `eslint-config-prettier`. Nie formatuj kodu ręcznie wbrew konfiguracji projektu.
- Włącz w `tsconfig.json` opcję `"strict": true` oraz dodatkowo `"noUncheckedIndexedAccess": true` i
  `"exactOptionalPropertyTypes": true`. Kod pisany bez trybu strict traktuj jako niezgodny ze
  standardem Danaco.
- Nazewnictwo: `camelCase` dla zmiennych i funkcji, `PascalCase` dla klas, typów, interfejsów i
  komponentów React, `UPPER_SNAKE_CASE` wyłącznie dla stałych modułowych o charakterze
  konfiguracyjnym.
- Nie stosuj przedrostka `I` w nazwach interfejsów ani przyrostka `Type` w nazwach typów — obie
  konwencje są w ekosystemie TS uznawane za przestarzałe.
- Preferuj `type` dla unii, krotek i typów pomocniczych; `interface` dla kształtów obiektów
  podlegających rozszerzaniu. Wybór stosuj konsekwentnie w obrębie projektu.
- Deklaruj zmienne przez `const`; `let` używaj tylko przy faktycznej reasygnacji. `var` jest
  zakazany.
- Eksportuj nazwane symbole (`export function parseInvoice`); `export default` ograniczaj do
  przypadków wymaganych przez framework (np. strony Next.js).
- Typuj jawnie wartości zwracane funkcji publicznego API modułu; wewnątrz modułu dopuszczaj
  inferencję.

## Struktura projektu

- Minimalny profesjonalny układ:
  - `package.json` — manifest z jawnym polem `"type"`, skryptami `build`, `test`, `lint`,
    `typecheck`;
  - `tsconfig.json` — konfiguracja kompilatora z trybem strict;
  - `eslint.config.js` (flat config) i `.prettierrc`;
  - `src/` — źródła; testy w `test/` lub obok źródeł jako `*.test.ts`;
  - `.gitignore` obejmujący co najmniej `node_modules/` i `dist/`.
- Ustaw jawnie `"type": "module"` albo `"type": "commonjs"` i konsekwentnie trzymaj się wybranego
  systemu modułów w całym projekcie.
- Dla nowych projektów Node stosuj ESM z `"module": "nodenext"` i `"moduleResolution": "nodenext"`;
  dla projektów bundlowanych (Vite, esbuild) — `"module": "esnext"` z `„moduleResolution”:
  „bundler”`.
- Rozdzielaj kod domenowy od infrastruktury: logika biznesowa nie może importować bezpośrednio
  warstwy HTTP ani klienta bazy danych.
- Czego nie tworzyć:
  - katalogu `dist/` ani plików `*.js` wygenerowanych z `*.ts` w repozytorium;
  - kopii zapasowych w drzewie źródeł (`utils_old.ts`, `helpers2.ts`, `index.backup.ts`);
  - pustych plików i katalogów „na przyszłość”;
  - ręcznych deklaracji `*.d.ts` tam, gdzie wystarczy `"declaration": true`.

## Budowa i zależności

- Instaluj zależności przez `npm ci` na CI oraz `npm install` lokalnie; plik `package-lock.json`
  zawsze commituj do repozytorium — to on gwarantuje odtwarzalność budowy. Nigdy nie usuwaj lockfile
  w celu „naprawienia” instalacji bez ustalenia przyczyny.
- Przypinaj wersje świadomie: zakresy `^` są akceptowalne przy obecności lockfile; dokładne wersje
  (`"1.4.2"` bez prefiksu) stosuj dla zależności o znanej niestabilności API.
- Kompiluj przez `tsc`; przy bundlerze stosuj `tsc --noEmit` jako bramkę kontroli typów uruchamianą
  obok bundlowania.
- Rozróżniaj `dependencies` od `devDependencies`: kompilator, linter, framework testowy i pakiety
  `@types/*` należą do `devDependencies`.
- Nie dodawaj zależności dla trywialnych operacji (padding łańcuchów, sprawdzanie parzystości,
  kopiowanie obiektów) — używaj wbudowanych API języka i Node.
- Przed użyciem API pakietu sprawdź zainstalowaną wersję w `package.json`/lockfile; nie zakładaj
  najnowszego API.

## Testy

- Stosuj Vitest w projektach z Vite lub czystym ESM; Jest w projektach zastanych, które już go
  używają. Nie mieszaj obu frameworków w jednym pakiecie.
- Testy jednostkowe umieszczaj w plikach `*.test.ts`; testuj zachowanie publicznego API modułu, nie
  szczegóły implementacji.
- Funkcje asynchroniczne testuj przez `async`/`await` w ciele testu; asercję odrzucenia promisy
  zapisuj jako `await expect(fn()).rejects.toThrow(...)` — nieoczekiwana promisa bez `await`
  sprawia, że test przechodzi fałszywie.
- Izoluj zależności zewnętrzne (sieć, zegar, system plików) przez wstrzykiwanie zależności lub
  `vi.mock`/`jest.mock`; testy nie mogą wykonywać rzeczywistych żądań HTTP.
- Kod zależny od czasu testuj z fałszywym zegarem (`vi.useFakeTimers()`), nie przez `setTimeout` z
  rzeczywistym oczekiwaniem.
- Uruchamiaj testy przed zgłoszeniem zadania jako ukończone: `npm test` musi przechodzić w całości,
  nie tylko testy nowo dodane.

## Diagnostyka

- W przeglądarce używaj DevTools: zakładki Console, Sources z punktami przerwania i Network; w Node
  uruchamiaj `node --inspect-brk` i podłączaj debugger przez `chrome://inspect` lub debugger VS
  Code. Nie diagnozuj wyłącznie przez `console.log`.
- Czytaj błędy TypeScript metodycznie:
  - `Type 'X' is not assignable to type 'Y'` — porównaj typy po najgłębszej różnicy w rozwinięciu
    komunikatu, nie po pierwszym wierszu;
  - `TS2345` — niezgodny argument wywołania; `TS2339` — nieistniejąca właściwość (często literówka
    lub zły typ źródłowy); `TS18048` / `TS2532` — wartość możliwie `undefined`, wymagane zawężenie;
  - kaskadę błędów usuwaj od pierwszego błędu w pliku — kolejne bywają następstwami.
- Typowe klasy błędów wykonania:
  - `TypeError: Cannot read properties of undefined` — brak zawężenia typu lub dostęp do indeksu bez
    sprawdzenia; stosuj `?.` wraz z jawną obsługą braku wartości, nie ślepe `!`;
  - zgubione `this` — metoda przekazana jako callback traci wiązanie; stosuj funkcje strzałkowe lub
    `bind` w konstruktorze;
  - wyścigi w kodzie asynchronicznym — dwie operacje modyfikujące wspólny stan bez sekwencjonowania;
    porządkuj przez `await`, a niezależne operacje zbieraj w `Promise.all` i obsługuj częściowe
    niepowodzenia przez `Promise.allSettled`.
- Nieobsłużone odrzucenia promis (`unhandledRejection`) traktuj jako defekt, nie szum: każda promisa
  musi być awaitowana albo mieć jawny `catch`.
- Przy diagnozie zaczynaj od minimalnej reprodukcji; nie poprawiaj kodu „na ślepo” w wielu miejscach
  naraz.

## Typowe błędy modeli LLM w tym języku

1. **Mieszanie CommonJS z ESM** — `require` w pliku z `"type": "module"` albo `import` w projekcie
   CJS bez transpilacji. Sprawdź pole `type` w `package.json` i ustawienie `module` w
   `tsconfig.json` przed napisaniem pierwszego importu; w jednym pliku stosuj wyłącznie jeden system
   modułów.
2. **`any` zamiast typu** — `any` wyłącza kontrolę typów tranzytywnie i ukrywa defekty do czasu
   wykonania. Stosuj `unknown` na granicach systemu (dane z sieci, `JSON.parse`) i zawężaj przez
   sprawdzenia lub bibliotekę walidacyjną (np. Zod); `any` dopuszczaj tylko z komentarzem
   uzasadniającym.
3. **Brak `await` przy wywołaniu asynchronicznym** — funkcja zwracająca `Promise` wywołana bez
   `await` powoduje, że błędy giną, a dalszy kod wykonuje się przed zakończeniem operacji. Reguły
   `@typescript-eslint/no-floating-promises` i `no-misused-promises` muszą przechodzić bez wyjątków.
4. **`==` zamiast `===`** — luźne porównanie wykonuje koercję typów (`0 == ""` jest prawdą). Stosuj
   wyłącznie `===` i `!==`; jedyny akceptowalny wyjątek to `x == null` jako świadomy skrót dla
   `null` lub `undefined`.
5. **Sekwencyjne `await` w pętli dla operacji niezależnych** — `for (const id of ids) await
   fetchItem(id)` wykonuje żądania szeregowo i wielokrotnie wydłuża czas. Dla operacji niezależnych
   buduj tablicę promis i stosuj `Promise.all`; pętlę z `await` zostaw tam, gdzie wymagana jest
   kolejność lub limit współbieżności.
6. **Rzutowanie `as` maskujące błąd typów** — `as unknown as T` ucisza kompilator zamiast naprawić
   model danych. Popraw typ źródłowy albo napisz predykat zawężający (`function isInvoice(x:
   unknown): x is Invoice`); rzutowanie bez walidacji na danych zewnętrznych jest zakazane.
7. **Mutowanie stanu i parametrów** — `array.sort()` sortuje w miejscu, modyfikacja obiektu
   przekazanego jako argument zaskakuje wywołującego. Stosuj `toSorted`/`toReversed` lub kopię
   (`[...items]`, `{ ...obj }`); w React nigdy nie mutuj stanu bezpośrednio.
8. **Przechwytywanie błędu i kontynuacja po cichu** — pusty `catch` lub `catch (e) { console.log(e)
   }` z dalszym wykonaniem na niespójnym stanie. Obsługuj błąd na poziomie, który umie zareagować; w
   pozostałych miejscach pozwól mu się propagować. W TS zmienna `catch` ma typ `unknown` — zawęź ją
   przed odczytem `message`.
9. **Halucynowane API bibliotek** — wywołania metod nieistniejących w zainstalowanej wersji pakietu.
   Zweryfikuj sygnaturę przez `tsc` lub dokumentację właściwej wersji; błąd kompilacji traktuj jako
   sygnał, nie przeszkodę do obejścia rzutowaniem.
10. **Nadmiarowa abstrakcja** — fabryki, klasy-wrappery i generyki tam, gdzie wystarczy funkcja
    modułowa. Pisz najprostszą konstrukcję realizującą wymaganie; abstrakcję wprowadzaj dopiero przy
    drugim rzeczywistym wariancie użycia.

Wzorzec poprawny — granica danych zewnętrznych:

```ts
// Waliduj dane z sieci na granicy systemu — dalej pracuj na typie pewnym.
const raw: unknown = await response.json();
const invoice = invoiceSchema.parse(raw); // Zod: rzuca wyjątek przy niezgodności
await postInvoice(invoice); // brak await byłby defektem klasy no-floating-promises
```

Wzorzec poprawny — niezależne operacje asynchroniczne:

```ts
// Wykonuj żądania równolegle; kolejność wyników odpowiada kolejności identyfikatorów.
const items = await Promise.all(ids.map((id) => fetchItem(id)));
```
