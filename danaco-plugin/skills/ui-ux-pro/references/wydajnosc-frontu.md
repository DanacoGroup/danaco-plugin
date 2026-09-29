# Wydajność frontu — karta

Karta obejmuje budżety i pomiar wydajności interfejsu: rozmiar pakietu, wskaźniki
ładowania i reakcji, obrazy i czcionki. Audyt gotowej witryny z metodyką pomiaru
prowadzi `../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`; wydajność w oknie
Tauri — `references/tauri-ui.md`.

Narzędzia zakładane przez tę kartę: Vite jako bundler, Vitest do testów, Playwright do
pomiarów w przeglądarce. Sprawdź ich obecność (`npx vite --version`,
`npx playwright --version`) zamiast zakładać, że są skonfigurowane.

## Budżety (domyślne dla projektów Danaco)

JS initial ≤ 200 KB gzip (aplikacja) / ≤ 90 KB (strona marketingowa) · LCP ≤ 2.5 s · CLS ≤ 0.1 · INP
≤ 200 ms · obraz hero ≤ 150 KB.

## Bundle (Vite)

1. Zmierz: `pnpm vite build` → rozmiary z outputu; szczegóły: `pnpm vite build -- --mode production`
   + `rollup-plugin-visualizer` (dodaj tylko na czas analizy).
2. Code-splitting: `import()` dla tras i ciężkich paneli (edytory, wykresy); wykresy/mapy ładuj po
   interakcji lub w viewport (IntersectionObserver).
3. Sprawdź duplikaty i ciężkie zależności: `rg "from '(lodash|moment|dayjs|date-fns)" src -n` — lodash→lodash-es z importami nazwanymi, moment→natywne Intl/Temporal.
4. Fonty: self-host, `woff2`, subset (latin-ext dla polskiego), `font-display: swap`, preload tylko
   display font.

## Obrazy (ImageMagick na maszynie)

```bash
magick input.png -resize 1600x -quality 82 output.webp     # web
magick input.png -resize 800x -quality 80 output-m.webp    # mobile, użyj srcset
```

Zawsze: wymiary `width/height` w HTML (zapobiega CLS), `loading="lazy"` poniżej foldu,
`fetchpriority="high"` na LCP.

## Pomiar (Playwright, bez instalacji Lighthouse)

```js
// perf.mjs — node perf.mjs <url>
import { chromium } from 'playwright';
const page = await (await chromium.launch()).newPage();
await page.goto(process.argv[2]);
const m = await page.evaluate(() => new Promise(res => {
  const out = {};
  new PerformanceObserver(l => { for (const e of l.getEntries()) out.lcp = e.startTime; })
    .observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver(l => { out.cls = (out.cls ?? 0) + l.getEntries().reduce((s, e) => s + (e.hadRecentInput ? 0 : e.value), 0); })
    .observe({ type: 'layout-shift', buffered: true });
  setTimeout(() => res(out), 3000);
}));
console.log(m);
```

Testuj z throttlingiem CPU (`page.emulateCPUThrottling` przez CDP session) — maszyna deweloperska
16-rdzeniowa maskuje problemy.

## Runtime

1. Re-rendery React: memo tylko po pomiarze (React DevTools profiler / `why-did-you-render`
   tymczasowo).
2. Listy > 100 wierszy: wirtualizacja.
3. Debounce inputów wyszukiwania (150–300ms), `AbortController` na przestarzałe fetche.

## Integracja

Taskfile: `task perf` → build + skrypt perf.mjs + wypis rozmiarów bundle vs budżety; przekroczenie
budżetu = zadanie niezakończone. Vitest pozostaje od logiki — wydajność mierz wyłącznie na buildzie
produkcyjnym (`vite preview`), nigdy na dev serverze.
