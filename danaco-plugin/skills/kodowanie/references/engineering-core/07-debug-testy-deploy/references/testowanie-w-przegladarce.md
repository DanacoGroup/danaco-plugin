# Testowanie w przeglądarce — Playwright i samokontrola agenta

Wersje odniesienia (sierpień 2026): `@playwright/test` **1.62.1**, `playwright` (Python)
**1.62.0**, `pytest-playwright` **0.8.0**, `@axe-core/playwright` **4.12.1**,
Vitest **4.1.10** z `@vitest/browser-playwright` **4.1.10**.

---

## Część I — NAJWAŻNIEJSZA: agent sprawdza własną robotę, zanim powie „gotowe”

To jest jedyna część tego pliku, którą wykonujesz **zawsze**, gdy zbudowałeś albo
zmieniłeś cokolwiek widocznego w przeglądarce. Reszta pliku to warsztat pisania testów
dla projektu.

**Zakaz:** nie wolno napisać „gotowe”, „zaimplementowałem”, „powinno działać” o interfejsie,
którego nie otworzyłeś. Konsekwencja złamania: użytkownik dostaje białą stronę z błędem
w konsoli, a twoja odpowiedź twierdzi, że funkcja działa. To najkosztowniejszy pojedynczy
błąd, jaki popełnia model przy pracy nad frontendem.

### Procedura samokontroli (SK)

**Krok 1. Uruchom aplikację i upewnij się, że w ogóle wstała.**

```bash
python ../scripts/z_serwerem.py --serwer "npm run dev" --url http://localhost:3000 \
  -- python /tmp/kontrola.py
```

Serwer, który nie wstał, ma zwykle przyczynę w pierwszych 30 liniach własnego wyjścia — skrypt
`references/engineering-core/07-debug-testy-deploy/scripts/z_serwerem.py` je wypisuje przy
niepowodzeniu. Nie zgaduj; przeczytaj.

**Krok 2. Zbuduj listę ścieżek do przejścia — zanim otworzysz przeglądarkę.**

Minimalny zestaw: (a) strona główna albo ekran, który zmieniałeś; (b) pełny przepływ
podstawowy tej funkcji od pustego stanu do wyniku; (c) jedna ścieżka błędu (puste pole,
zła wartość); (d) jeden widok wymagający danych z serwera.

**Krok 3. Otwórz każdą ścieżkę i wykonaj ją naprawdę.** Klikanie, nie oglądanie. Po każdym
kroku zbieraj:

- błędy konsoli (`page.on('console')` z `msg.type() === 'error'`),
- nieprzechwycone wyjątki strony (`page.on('pageerror')`),
- żądania, które padły lub zwróciły ≥ 400 (`page.on('response')`),
- zrzut ekranu.

**Krok 4. Zastosuj bramkę zero-błędów.** Wynik `0 błędów konsoli, 0 pageerror, 0 odpowiedzi
≥ 400 poza celowo testowanymi` jest warunkiem przejścia dalej. Ostrzeżenia React o
kluczach, `hydration mismatch`, `404` na czcionce — to są usterki, nie szum.

**Krok 5. Napraw znalezione i powtórz krok 3.** Pętla trwa, dopóki bramka nie jest zielona.

**Krok 6. Obejrzyj zrzuty ekranu.** Nie tylko przeczytaj log. Pusty kontener, tekst na tekście,
przycisk poza ekranem — nie generują błędu konsoli. Zrzut w dwóch szerokościach: 390 i 1440.

**Krok 7. Dopiero teraz raportuj.** W raporcie podaj: które ścieżki przeszedłeś, co znalazłeś,
co naprawiłeś, co pozostało nienaprawione i dlaczego.

### Gotowy skrypt samokontroli

Skrypt `../scripts/kontrola_strony.py` robi kroki 3 i 4
automatycznie. Uruchom `python ../scripts/kontrola_strony.py --help`, zanim zaczniesz pisać własny —
skrypt jest przeznaczony do użycia jako czarna skrzynka, nie do wczytywania do kontekstu.

```bash
python ../scripts/kontrola_strony.py \
  --url http://localhost:3000/faktury \
  --klik "role=button[name=Nowa faktura]" \
  --wpisz "label=Kwota netto=1500,00" \
  --klik "role=button[name=Zapisz]" \
  --oczekuj-tekst "Faktura zapisana" \
  --zrzuty /tmp/kontrola --a11y
```

Kroki wykonują się w kolejności podania argumentów. Selektory: `role=rola[name=Nazwa]`,
`label=…`, `text=…`, `testid=…`, `placeholder=…`; wszystko inne to CSS. Bez cudzysłowów
wewnątrz nawiasu — cały argument jest już w cudzysłowie powłoki.

Wynik: kod wyjścia 0 tylko przy zerowej liczbie błędów konsoli, wyjątków strony i
odpowiedzi ≥ 400; w przeciwnym razie raport na stderr i kod 1.

### Minimalny własny skrypt, gdy potrzebujesz czegoś innego

```python
from playwright.sync_api import sync_playwright

bledy, wyjatki, zle_odpowiedzi = [], [], []

with sync_playwright() as p:
    przegladarka = p.chromium.launch(headless=True)
    strona = przegladarka.new_page(viewport={"width": 1440, "height": 900})

    strona.on("console", lambda m: bledy.append(f"{m.type}: {m.text}")
              if m.type == "error" else None)
    strona.on("pageerror", lambda e: wyjatki.append(str(e)))
    strona.on("response", lambda r: zle_odpowiedzi.append(f"{r.status} {r.url}")
              if r.status >= 400 else None)

    strona.goto("http://localhost:3000", wait_until="networkidle")
    strona.get_by_role("button", name="Nowa faktura").click()
    strona.get_by_label("Kwota").fill("1500,00")
    strona.get_by_role("button", name="Zapisz").click()
    strona.get_by_text("Faktura zapisana").wait_for(timeout=5000)
    strona.screenshot(path="/tmp/po-zapisie.png", full_page=True)

    przegladarka.close()

assert not bledy, f"Błędy konsoli: {bledy}"
assert not wyjatki, f"Wyjątki strony: {wyjatki}"
assert not zle_odpowiedzi, f"Odpowiedzi ≥400: {zle_odpowiedzi}"
print("Samokontrola: OK")
```

`headless=True` zawsze — w kontenerze nie ma serwera X, a tryb z oknem zawiesza się bez
komunikatu. Jeśli Playwright zgłasza brak przeglądarek: `python -m playwright install
chromium --with-deps` (w Node: `npx playwright install --with-deps chromium`).

### Statyczny HTML bez serwera

```python
import os
sciezka = os.path.abspath("dist/index.html")
strona.goto(f"file://{sciezka}")
```

Uwaga: przy `file://` moduły ES i `fetch` do względnych ścieżek są blokowane przez CORS.
Jeśli strona korzysta z `<script type="module">`, podnieś `python -m http.server` zamiast
`file://`, inaczej zdiagnozujesz błąd, którego nie ma w prawdziwym wdrożeniu.

### Rozpoznanie przed działaniem (gdy nie znasz strony)

Nie wymyślaj selektorów. Odczytaj je z wyrenderowanej strony:

```python
strona.goto(url, wait_until="networkidle")
print(strona.accessibility.snapshot())              # drzewo ról i nazw
print(strona.locator("button").all_inner_texts())
print(strona.get_by_role("link").all_inner_texts())
strona.screenshot(path="/tmp/rozpoznanie.png", full_page=True)
```

Od 1.49 lepszym narzędziem jest migawka ARIA w YAML — ten sam format, którego używa
`expect(...).to_match_aria_snapshot()`:

```python
print(strona.locator("main").aria_snapshot())
```

Wynik pokazuje strukturę tak, jak widzi ją czytnik ekranu i jak powinny wyglądać
selektory. Jeśli w migawce nie ma nazw ról — masz problem z dostępnością, nie z testem.

---

## Część II — pisanie testów Playwright dla projektu

### Konfiguracja (Playwright 1.62)

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,          // .only w CI = błąd, nie cichy skrót
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? '50%' : undefined,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['github'], ['json', { outputFile: 'wyniki.json' }]]
    : [['list']],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',             // ślad tylko gdy coś padło — tanio i wystarczy
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    testIdAttribute: 'data-testid',
    locale: 'pl-PL',
    timezoneId: 'Europe/Warsaw',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },
    { name: 'mobile',   use: { ...devices['iPhone 15'] } },
  ],
  webServer: {
    command: 'npm run build && npm start',   // build produkcyjny, nie dev
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

Dwie decyzje w tej konfiguracji, które model zwykle podejmuje źle:

- `webServer.command` musi uruchamiać **build produkcyjny**. Testowanie `next dev` daje
  fałszywą pewność: dev ma inne mapowanie źródeł, brak minifikacji, brak wstępnego
  renderowania i inne zachowanie hydratacji.
- `retries: 2` w CI to **środek maskujący**, nie rozwiązanie. Test, który przechodzi przy
  ponowieniu, jest migoczący i wymaga naprawy — patrz
  `references/engineering-core/07-debug-testy-deploy/references/strategia-testow.md`.

### Selektory — kolejność obowiązkowa

| Priorytet | Selektor | Kiedy | Przykład |
| --- | --- | --- | --- |
| 1 | Rola + dostępna nazwa | domyślnie, zawsze | `getByRole('button', { name: 'Zapisz fakturę' })` |
| 2 | Etykieta formularza | pola formularzy | `getByLabel('Numer NIP')` |
| 3 | Tekst widoczny | nagłówki, komunikaty | `getByText('Faktura zapisana')` |
| 4 | Placeholder / alt / title | gdy nie ma etykiety (a powinna być) | `getByPlaceholder('Szukaj…')` |
| 5 | `data-testid` | ostateczność: element bez semantyki, np. kontener wykresu | `getByTestId('wykres-przychodow')` |
| — | CSS/XPath po klasach | **nigdy** w testach e2e | `.css-1x2y3z > div:nth-child(3)` |

Selektor po klasie CSS z Tailwinda albo z CSS-in-JS pada przy pierwszej zmianie stylu,
która nie zmienia zachowania. Konsekwencja: zespół przestaje ufać testom i zaczyna je
wyłączać.

Gdy `getByRole` nie znajduje elementu, to zwykle nie jest wina testu: przycisk jest
`<div onClick>` bez roli, albo pole nie ma `<label for>`. **Napraw komponent, nie test.**
Zyskujesz dostępność za darmo.

Zawężanie zamiast dłuższych selektorów:

```ts
const wiersz = page.getByRole('row', { name: /FV\/2026\/08\/001/ });
await wiersz.getByRole('button', { name: 'Usuń' }).click();

// filtrowanie po zawartości potomka
await page.getByRole('listitem')
  .filter({ hasText: 'Kontrahent ACME' })
  .getByRole('link', { name: 'Szczegóły' }).click();
```

### Oczekiwanie zamiast `sleep`

`page.waitForTimeout(1000)` w teście to gwarancja migotania: na wolniejszej maszynie CI
sekunda nie wystarczy, na szybkiej zmarnujesz ją przy każdym uruchomieniu.

```ts
// ŹLE
await page.click('#zapisz');
await page.waitForTimeout(2000);
expect(await page.textContent('.status')).toBe('Zapisano');

// DOBRZE — asercja z automatycznym ponawianiem do 5 s
await page.getByRole('button', { name: 'Zapisz' }).click();
await expect(page.getByText('Zapisano')).toBeVisible();

// czekanie na konkretną odpowiedź sieciową
const odpowiedz = page.waitForResponse(r =>
  r.url().includes('/api/faktury') && r.request().method() === 'POST');
await page.getByRole('button', { name: 'Zapisz' }).click();
expect((await odpowiedz).status()).toBe(201);

// czekanie na zniknięcie ładowania
await expect(page.getByRole('progressbar')).toBeHidden();

// czekanie na warunek w przeglądarce
await page.waitForFunction(() => (window as any).__gotowe === true);
```

`expect(locator)` z Playwrighta ponawia sprawdzenie aż do `expect.timeout`. `expect(await
locator.textContent())` sprawdza **raz** — to najczęstsza przyczyna migotania w testach
pisanych przez model. Różnica: asercja na lokatorze, nie na już pobranej wartości.

`wait_until="networkidle"` nadaje się do rozpoznania strony, ale nie do testów aplikacji
z długim odpytywaniem czy WebSocketem — tam nigdy nie nastąpi bezczynność sieci. Czekaj
na konkretny element.

### Przechwytywanie sieci

```ts
// podmiana odpowiedzi — test ścieżki błędu bez psucia backendu
await page.route('**/api/faktury', route =>
  route.fulfill({ status: 500, body: JSON.stringify({ error: 'awaria' }) }));

// blokada zasobów zewnętrznych — przyspiesza i usuwa źródło migotania
await page.route(/\.(png|jpg|woff2)$/, route => route.abort());
await page.route('**/*.googletagmanager.com/**', route => route.abort());

// podgląd bez modyfikacji
page.on('request', r => console.log('→', r.method(), r.url()));
page.on('requestfailed', r => console.log('PADŁO', r.url(), r.failure()?.errorText));

// modyfikacja odpowiedzi rzeczywistej
await page.route('**/api/kurs', async route => {
  const odp = await route.fetch();
  const dane = await odp.json();
  await route.fulfill({ json: { ...dane, kurs: 4.35 } });
});
```

Blokowanie skryptów analitycznych i czcionek zewnętrznych skraca zestaw e2e zwykle o
20–40% i eliminuje padnięcia od cudzych awarii. Rób to domyślnie w `beforeEach`.

### Uwierzytelnianie — raz, nie w każdym teście

Logowanie w `beforeEach` to najdroższa rzecz w typowym zestawie e2e. Zamiast tego zapisz
stan przeglądarki raz:

```ts
// e2e/setup/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

setup('logowanie', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('E-mail').fill(process.env.TEST_EMAIL!);
  await page.getByLabel('Hasło').fill(process.env.TEST_HASLO!);
  await page.getByRole('button', { name: 'Zaloguj' }).click();
  await expect(page.getByRole('heading', { name: 'Pulpit' })).toBeVisible();
  await page.context().storageState({ path: 'e2e/.auth/uzytkownik.json' });
});
```

```ts
// playwright.config.ts — fragment projects
projects: [
  { name: 'setup', testMatch: /auth\.setup\.ts/ },
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/uzytkownik.json' },
    dependencies: ['setup'],
  },
],
```

`e2e/.auth/` musi być w `.gitignore`. Plik zawiera ważne ciasteczka sesyjne — wpuszczenie
go do repozytorium to wyciek poświadczeń.

### Zrzuty ekranu i porównanie wizualne

```ts
await expect(page).toHaveScreenshot('pulpit.png', {
  maxDiffPixelRatio: 0.01,
  animations: 'disabled',            // wyłącza CSS animations/transitions
  mask: [page.getByTestId('data-generowania')],   // maskuj to, co zmienne
  fullPage: true,
});
```

Trzy warunki, bez których porównanie wizualne generuje wyłącznie fałszywe alarmy:

1. **Maskuj zmienne**: daty, identyfikatory, awatary, wykresy z losowymi danymi.
2. **Zamroź czas i dane**: `page.clock.setFixedTime(new Date('2026-08-04T10:00:00Z'))`
   plus stała baza testowa.
3. **Generuj wzorce na tym samym systemie co CI** (kontener Linux). Wzorce z macOS nie
   przejdą na Linuksie — inny rendering czcionek. `npx playwright test --update-snapshots`
   uruchamiaj w tym samym obrazie Dockera co CI.

Bez tych trzech rzeczy porównanie wizualne kosztuje więcej czasu na przeglądanie różnic
niż wykrywa błędów. Jeśli nie możesz ich zapewnić — nie wprowadzaj go.

Vitest 4 ma odpowiednik dla testów komponentów: `expect(element).toMatchScreenshot()`
w trybie przeglądarkowym z `@vitest/browser-playwright`.

### Migawki ARIA — tańsza alternatywa dla porównania wizualnego

```ts
await expect(page.getByRole('main')).toMatchAriaSnapshot(`
  - heading "Faktury" [level=1]
  - table:
    - row "Numer Kontrahent Kwota":
      - cell "Numer"
      - cell "Kontrahent"
      - cell "Kwota"
  - button "Nowa faktura"
`);
```

Sprawdza strukturę i dostępne nazwy, ignoruje piksele. Nie pada od zmiany koloru,
pada od usunięcia nagłówka albo utraty roli. Dla większości ekranów to lepszy zwrot
z inwestycji niż zrzuty pikselowe.

### Debugowanie testów

```bash
npx playwright test --debug                      # Inspector, krok po kroku
npx playwright test --ui                         # tryb UI: oś czasu, DOM, sieć
npx playwright test plik.spec.ts:42 --headed --workers=1
PWDEBUG=1 npx playwright test                    # pauza z inspektorem
npx playwright test --trace on                   # ślad zawsze (wolne, do diagnozy)
npx playwright show-trace test-results/…/trace.zip
npx playwright codegen http://localhost:3000     # nagrywanie działań na selektory
```

`trace viewer` jest jedynym narzędziem, które pokazuje jednocześnie: migawkę DOM przed
i po każdej akcji, log sieci, konsolę i źródło testu. Przy padnięciu w CI **zawsze zacznij
od śladu**, zanim zaczniesz czytać kod testu. Artefakt `test-results/` musi być wgrywany
przez CI, inaczej diagnoza padnięcia w CI to zgadywanie.

W Playwright 1.60+ ślad może zawierać zapis HAR (`trace: { mode: 'on', ... }` z nagrywaniem
sieci), a od 1.59 dostępny jest zapis wideo z adnotacjami akcji.

### Uruchamianie równoległe i izolacja

```ts
test.describe.configure({ mode: 'parallel' });   // testy w pliku równolegle
test.describe.configure({ mode: 'serial' });     // gdy dzielą stan (unikaj)
```

Domyślnie Playwright zrównolegla pliki, nie testy w pliku. Każdy test dostaje własny
kontekst przeglądarki — czyste ciasteczka i `localStorage`. Współdzielony pozostaje
**backend i baza**. To jedyne realne źródło kolizji.

Reguła izolacji danych: każdy test tworzy własne dane z unikalnym kluczem i sprząta po
sobie, albo nie sprząta wcale, ale nigdy nie zakłada, że baza jest pusta.

```ts
const znacznik = `test-${test.info().parallelIndex}-${Date.now()}`;
await page.getByLabel('Nazwa').fill(`Kontrahent ${znacznik}`);
```

Test, który zakłada „na liście są 3 pozycje”, pada, gdy inny test doda czwartą. Asercja
powinna brzmieć „na liście jest pozycja o nazwie `Kontrahent test-2-1754...`”.

### Wiele przeglądarek i urządzeń

Uruchamianie pełnego zestawu na trzech silnikach potraja czas i zwykle nie zwraca się.
Sensowny podział:

| Zakres | Gdzie |
| --- | --- |
| Pełny zestaw | Chromium, przy każdym PR |
| Ścieżki krytyczne (logowanie, płatność, zapis) | + WebKit i Firefox, nocnie i przed wydaniem |
| Widok mobilny | Chromium z `devices['iPhone 15']` — tylko układ i nawigacja |

WebKit wyłapuje realne różnice: `Date` parsowanie niestandardowych formatów, obsługa
`Intl`, ograniczenia `localStorage` w trybie prywatnym, `position: sticky`. Firefox —
różnice w zdarzeniach fokusu i `input type=date`.

```ts
test.skip(({ browserName }) => browserName === 'webkit', 'WebKit nie wspiera <funkcja>');
```

Pomijanie jest lepsze niż wyłączanie całego projektu — zostaje ślad, czego nie sprawdzasz.

### Testy dostępności (axe)

```ts
import AxeBuilder from '@axe-core/playwright';

test('pulpit bez naruszeń dostępności', async ({ page }) => {
  await page.goto('/pulpit');
  const wynik = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .exclude('#widget-zewnetrzny')     // cudzy iframe, nad którym nie masz kontroli
    .analyze();

  expect(wynik.violations, JSON.stringify(wynik.violations, null, 2)).toEqual([]);
});
```

axe wykrywa automatycznie około 30–40% naruszeń WCAG. Zero naruszeń axe **nie znaczy**,
że strona jest dostępna — kolejność fokusu, sensowność tekstu alternatywnego i obsługa
klawiaturą wymagają sprawdzenia ręcznego:

```ts
await page.keyboard.press('Tab');
await expect(page.getByRole('link', { name: 'Przejdź do treści' })).toBeFocused();
```

Szersze omówienie dostępności i Core Web Vitals:
`../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`.

### Test przepływu — wzorzec kompletny

```ts
import { test, expect } from '@playwright/test';

test.describe('wystawienie faktury', () => {
  test.beforeEach(async ({ page }) => {
    await page.route(/googletagmanager|hotjar/, r => r.abort());
    await page.clock.setFixedTime(new Date('2026-08-04T09:00:00Z'));
  });

  test('od pustego formularza do PDF-a', async ({ page }) => {
    await page.goto('/faktury/nowa');

    await page.getByLabel('Kontrahent').fill('ACME sp. z o.o.');
    await page.getByRole('option', { name: 'ACME sp. z o.o.' }).click();
    await page.getByLabel('Kwota netto').fill('1500,00');
    await page.getByLabel('Stawka VAT').selectOption('23');

    await expect(page.getByTestId('kwota-brutto')).toHaveText('1 845,00 zł');

    const pobranie = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Wystaw i pobierz PDF' }).click();

    await expect(page.getByText(/Faktura FV\/2026\/08\/\d+ wystawiona/)).toBeVisible();
    const plik = await pobranie;
    expect(plik.suggestedFilename()).toMatch(/^FV_2026_08_\d+\.pdf$/);
  });

  test('odrzuca ujemną kwotę', async ({ page }) => {
    await page.goto('/faktury/nowa');
    await page.getByLabel('Kwota netto').fill('-100');
    await page.getByRole('button', { name: 'Wystaw i pobierz PDF' }).click();
    await expect(page.getByText('Kwota musi być dodatnia')).toBeVisible();
    await expect(page).toHaveURL(/\/faktury\/nowa/);   // nie przeszło dalej
  });
});
```

Zauważ: asercja pośrednia (`kwota-brutto`) sprawdza logikę **przed** kliknięciem zapisu.
Gdy test padnie, od razu wiesz, czy problem jest w wyliczeniu, czy w zapisie. Test bez
asercji pośrednich mówi tylko „nie działa”.

---

## Część III — agenty testowe Playwright (1.56+)

Playwright ma wbudowane definicje agentów do generowania i naprawy testów:

```bash
npx playwright init-agents --loop=claude      # także: vscode, codex, opencode
```

Powstają trzy role:

| Agent | Co robi | Wejście → wyjście |
| --- | --- | --- |
| **planner** | eksploruje aplikację i pisze plan testów w Markdown | uruchomiona aplikacja + `seed.spec.ts` → `specs/*.md` |
| **generator** | zamienia plan na pliki testowe, weryfikując selektory na żywo | `specs/*.md` → `tests/*.spec.ts` |
| **healer** | uruchamia zestaw i naprawia padające testy, oglądając stan UI | padający zestaw → poprawki |

Od 1.62 serwer MCP i CLI są dołączone do paczki: `npx playwright mcp`, `npx playwright cli`.

Ograniczenia, o których trzeba wiedzieć przed użyciem:

- **`healer` naprawia test, nie aplikację.** Jeśli test pada, bo funkcja jest zepsuta,
  healer „naprawi” go tak, by przechodził — i zamaskuje błąd. Używaj go tylko po
  świadomej zmianie UI, nigdy do padnięć nieznanego pochodzenia.
- Definicje agentów są statyczne i wersjonowane razem z Playwrightem — regeneruj po
  aktualizacji, inaczej używają nieistniejących API.
- Wygenerowany test jest punktem wyjścia, nie produktem. Przejrzyj selektory (czy nie
  wpadły w CSS po klasach) i asercje (czy nie sprawdzają wyłącznie `toBeVisible`).

---

## Kiedy Playwright, a kiedy coś tańszego

| Chcesz sprawdzić | Narzędzie | Koszt uruchomienia |
| --- | --- | --- |
| Logika czystej funkcji | Vitest 4 / pytest | ms |
| Renderowanie komponentu, jego stany | Vitest 4 browser mode + `@vitest/browser-playwright` | dziesiątki ms |
| Kontrakt endpointu HTTP | `supertest` / `httpx` + baza testowa | setki ms |
| Przepływ użytkownika przez wiele ekranów | **Playwright** | sekundy |
| Wygląd | migawka ARIA; zrzut pikselowy tylko z zamrożonymi danymi | sekundy |

Reguła doboru: każdy test przenieś **w dół** tabeli tak nisko, jak się da bez utraty
sensu. Test e2e sprawdzający walidację jednego pola to marnotrawstwo — ta sama informacja
kosztuje 500 razy mniej w teście jednostkowym. E2E rezerwuj dla ścieżek, które przechodzą
przez granice: przeglądarka → API → baza → z powrotem.

Uzasadnienie i proporcje:
`references/engineering-core/07-debug-testy-deploy/references/strategia-testow.md`.
