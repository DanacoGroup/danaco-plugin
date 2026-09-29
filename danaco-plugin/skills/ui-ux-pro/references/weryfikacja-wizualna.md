# Weryfikacja wizualna — karta

Karta obejmuje pętlę oglądania własnego interfejsu przed scaleniem: zrzuty ekranu
w kilku szerokościach, porównanie z odniesieniem i kontrolę konsoli. Dostępność
sprawdza `references/dostepnosc-wcag.md`, wydajność — `references/wydajnosc-frontu.md`.

Sprawdź środowisko, zanim zaczniesz, i nie zakładaj jego stanu:

```bash
npx playwright --version    # odpowiedź = Playwright zainstalowany
magick -version             # odpowiedź = ImageMagick dostępny
nproc                       # liczba rdzeni do zrównoleglenia viewportów
```

Jeśli `npx playwright --version` odpowiada numerem wersji, przeglądarki są zwykle już
pobrane — uruchom `npx playwright install --with-deps chromium firefox` tylko wtedy, gdy
pierwszy zrzut zawiedzie z komunikatem o brakującej przeglądarce. Wersje traktuj jako
orientacyjne; stan faktyczny podaje polecenie wyżej.

## Pętla podstawowa (obowiązkowa po budowie UI)

1. Uruchom dev server (Vite: `pnpm dev --port 5173` lub przez `task dev`, jeśli Taskfile go
   definiuje) w tle; poczekaj na gotowość portu (`curl -s -o /dev/null localhost:5173`).
2. Zrzuty przez skrypt Playwright (nie MCP, gdy działasz w CLI):

```js
// screenshot.mjs — node screenshot.mjs <url> <prefix>
import { chromium } from 'playwright';
const [url, prefix = 'shot'] = process.argv.slice(2);
const vps = { mobile: [390, 844], tablet: [820, 1180], desktop: [1440, 900], wide: [1920, 1080] };
const browser = await chromium.launch();
await Promise.all(Object.entries(vps).map(async ([name, [w, h]]) => {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${prefix}-${name}.png`, fullPage: true });
}));
await browser.close();
```

3. OBEJRZYJ każdy zrzut narzędziem Read. Oceń wg listy: hierarchia typograficzna, kontrast, spacing
   na siatce, overflow/ucięcia na mobile, spójność komponentów, stany puste.
4. Popraw kod → powtórz. Minimum 2 iteracje, kończ dopiero gdy wszystkie viewporty są poprawne.

## Porównanie z referencją / regresja wizualna (ImageMagick)

```bash
# metryka różnicy (0 = identyczne); próg akceptacji ustal na projekt (np. < 0.01 RMSE)
magick compare -metric RMSE aktualny.png referencja.png diff.png 2>&1
# diff.png podświetla różnice na czerwono — obejrzyj go Readem
```

Zrzuty-referencje trzymaj w `tests/visual/__snapshots__/`; alternatywnie użyj wbudowanego
`expect(page).toHaveScreenshot()` w testach Playwright.

## Stany i interakcje

Testuj nie tylko stan początkowy: hover/focus (`page.hover`, `page.focus` + zrzut), formularze z
błędami walidacji, stany puste i ładowania, tryb ciemny (`page.emulateMedia({ colorScheme: 'dark'
})`), `prefers-reduced-motion`.

## Aplikacje Tauri

WebView Tauri na tej maszynie to webkit2gtk — silnik klasy WebKit, nie Chromium. Dlatego:

1. Front testuj w OBU pobranych przeglądarkach: chromium + **firefox**; różnice chromium↔firefox
   wychwytują większość problemów niechromiumowych silników.
2. Unikaj CSS wymagającego najnowszego Chromium; sprawdzaj wsparcie webkit2gtk dla nowinek (subgrid,
   `:has()`, container queries — zweryfikuj wersję webkit2gtk: `pkg-config --modversion
   webkit2gtk-4.1`).
3. Pełny test w realnym oknie: `cargo tauri dev` + zrzut okna przez `import` (ImageMagick, X11) lub
   testy WebDriver Tauri.

## Konsola i sieć

Przy każdej sesji zrzutów zbieraj też błędy: `page.on('console', ...)` i `page.on('pageerror', ...)`
— czysta konsola to część definicji ukończenia.
