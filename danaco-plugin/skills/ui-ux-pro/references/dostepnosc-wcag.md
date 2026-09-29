# Dostępność WCAG 2.2 AA — karta

Karta obejmuje kontrolę dostępności interfejsu przed oddaniem: audyt automatyczny,
kontrolę ręczną i dziewięć kryteriów dodanych w WCAG 2.2. Obowiązującą normą jest
WCAG 2.2 (rekomendacja W3C z 5 października 2023, aktualizacja 12 grudnia 2024), poziom
AA. Audyt gotowej witryny z mapowaniem ustaleń na kryteria prowadzi
`../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`; wzorce ARIA komponentów —
`references/shadcn-accessibility.md`.

Jeśli `npx playwright --version` odpowiada numerem wersji, Playwright jest zainstalowany
i przeglądarki są pobrane — nie uruchamiaj wtedy `playwright install`. Jeśli polecenie
zawodzi, zainstaluj Playwright i przeglądarki, zanim uruchomisz skrypty z tej karty.
Wersje bibliotek podane niżej traktuj jako orientacyjne — sprawdź stan w projekcie.

## Audyt automatyczny (axe przez Playwright)

```js
// a11y.mjs — node a11y.mjs <url>
import { chromium } from 'playwright';
const page = await (await chromium.launch()).newPage();
await page.goto(process.argv[2], { waitUntil: 'networkidle' });
await page.addScriptTag({ url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js' });
const r = await page.evaluate(() => axe.run());
console.log(JSON.stringify(r.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help })), null, 2));
process.exit(r.violations.some(v => ['critical','serious'].includes(v.impact)) ? 1 : 0);
```

Przefiltruj wynik przez `jq` przy dużych raportach. Zero naruszeń critical/serious = warunek
oddania. Uruchom dla trybu jasnego I ciemnego.

## Kontrola ręczna (checklist)

1. **Klawiatura**: przejdź cały widok Tabem — każdy interaktywny element osiągalny, widoczny
   `:focus-visible` (nigdy `outline: none` bez zamiennika), brak pułapek focusa, Escape zamyka
   dialogi, focus wraca do wyzwalacza.
2. **Semantyka**: nagłówki h1→h2→h3 bez przeskoków, landmarki (`main`, `nav`, `header`), przyciski
   to `<button>`, linki to `<a>` — nigdy klikalne divy.
3. **Formularze**: każdy input ma `<label>`, błędy tekstem powiązanym `aria-describedby` (nie tylko
   czerwoną ramką), `autocomplete` na polach danych osobowych.
4. **Kolor**: informacja nigdy samym kolorem (dodaj ikonę/tekst do stanów błędu/sukcesu). Kontrast:
   tekst 4.5:1, duży tekst i elementy UI 3:1.
5. **Cele dotykowe** (kryterium 2.5.8): min. 24×24 px albo odstęp gwarantujący brak
   nakładania okręgów 24 px; na urządzeniu dotykowym celuj w 44×44 px.
6. **Motion**: `prefers-reduced-motion` redukuje animacje do opacity lub zera.
7. **ARIA**: minimum — poprawny HTML zamiast ARIA gdzie się da; `aria-live="polite"` na komunikaty
   asynchroniczne; nazwy dostępne na przyciskach-ikonach (`aria-label`).

## Integracja

- Dodaj do Taskfile: `task a11y` uruchamiający skrypt axe na kluczowych widokach.
- Wynik audytu raportuj tabelą: naruszenie / waga / liczba wystąpień / poprawka. Poprawiaj od
  critical w dół, po poprawkach uruchom audyt ponownie.

## Dziewięć kryteriów dodanych w WCAG 2.2

Automat nie wykrywa żadnego z nich w pełni. Kryterium 4.1.1 Parsowanie zostało
w wersji 2.2 wycofane — nie zgłaszaj go jako naruszenia.

| Kryterium | Poziom | Wymóg wykonawczy |
|---|---|---|
| 2.4.11 Fokus niezasłonięty (minimum) | AA | Element z fokusem nie może być zasłonięty przez przyklejony nagłówek, stopkę ani panel zgód — sprawdź `scroll-margin-top` na elementach interaktywnych i wysokość przyklejonego nagłówka |
| 2.4.12 Fokus niezasłonięty (rozszerzony) | AAA | Wskaźnik fokusa widoczny w całości; wdrażaj przy zadeklarowanym AAA |
| 2.4.13 Wygląd fokusa | AAA | Wskaźnik obejmuje kontur elementu, grubość co najmniej 2 px, kontrast 3:1 wobec stanu bez fokusa |
| 2.5.7 Ruchy przeciągania | AA | Każda czynność przeciągania ma odpowiednik na jedno wskazanie: suwak z polem liczbowym, lista z przyciskami „w górę”/„w dół”, mapa z przyciskami przesuwania |
| 2.5.8 Rozmiar celu (minimum) | AA | Cel co najmniej 24×24 px albo wystarczający odstęp; dotyczy ikon w paskach narzędzi, przycisków zamknięcia i przełączników w wierszach tabel |
| 3.2.6 Spójna pomoc | A | Wejście do pomocy (kontakt, czat, instrukcja) w tym samym miejscu układu na każdym widoku, na którym występuje |
| 3.3.7 Powtórne wprowadzanie | A | W kreatorze wieloetapowym dane raz podane wypełniaj automatycznie albo udostępniaj do wyboru; wyjątek dla haseł i danych wymagających potwierdzenia |
| 3.3.8 Dostępne uwierzytelnianie (minimum) | AA | Logowanie bez testu poznawczego: `autocomplete="current-password"`, wklejanie dozwolone, alternatywa dla CAPTCHA |
| 3.3.9 Dostępne uwierzytelnianie (rozszerzone) | AAA | Jak wyżej, bez wyjątku rozpoznawania obiektów |

Do zgodności na poziomie AA wchodzą 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7 i 3.3.8.

## Kontrola przed oddaniem

1. Audyt automatyczny bez naruszeń o wadze critical i serious, w trybie jasnym i ciemnym.
2. Pełny widok przejdziony klawiaturą, wskaźnik fokusa widoczny i niezasłonięty.
3. Sześć kryteriów 2.2 z poziomu A i AA sprawdzonych ręcznie.
4. Kontrast zmierzony narzędziem, także dla stanów hover, focus i disabled.
5. Cele dotykowe zmierzone w rzeczywistym oknie, nie oszacowane.

Źródła: https://www.w3.org/WAI/standards-guidelines/wcag/ oraz
https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/ (stan na 2026-09-03).
