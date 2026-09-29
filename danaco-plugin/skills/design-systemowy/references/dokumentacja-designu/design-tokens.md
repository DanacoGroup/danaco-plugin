# Tokeny projektowe — karta

Stosuj niniejszą kartę przy definiowaniu, dokumentowaniu i weryfikowaniu tokenów
projektowych (design tokens) w projektach Danaco. Traktuj tokeny jako fundament
systemu projektowego — bez uporządkowanych tokenów żadna warstwa wyżej (CSS,
komponenty, księga projektowa) nie utrzyma spójności.

## Rola i hierarchia tokenów

Traktuj tokeny jako jedyne źródło prawdy dla wartości projektowych: kolorów,
odstępów, typografii, promieni, cieni i czasów animacji. Każda wartość wizualna
użyta w produkcie musi pochodzić z tokenu — wartość wpisana wprost w komponencie
(np. `#3366ff` albo `margin: 13px`) stanowi usterkę i podlega poprawie podczas
przeglądu kodu.

Utrzymuj trójwarstwową hierarchię tokenów:

1. **Tokeny bazowe (palette)** — surowe wartości bez znaczenia semantycznego,
   np. `blue-500: #2563eb`, `gray-100: #f3f4f6`, `space-4: 1rem`. Nie odwołuj
   się do nich bezpośrednio z komponentów.
2. **Tokeny semantyczne** — nazwane od roli, nie od wyglądu, np.
   `color-surface`, `color-text-primary`, `color-border-subtle`. Wskazują na
   tokeny bazowe. To one stanowią podstawowy interfejs dla stylów.
3. **Tokeny komponentowe** — opcjonalna warstwa dla wartości specyficznych dla
   komponentu, np. `button-primary-background`. Twórz je wyłącznie wtedy, gdy
   komponent wymaga wartości odmiennej od tokenu semantycznego.

Kieruj zależności zawsze w dół hierarchii: komponent → token komponentowy lub
semantyczny → token bazowy. Nie dopuszczaj odwołań komponentu wprost do palety.

## Nazewnictwo

Stosuj konwencję kebab-case dla wszystkich nazw tokenów: `color-text-primary`,
`font-size-lg`, `space-2`. Nie mieszaj konwencji w obrębie projektu.

Nadawaj nazwy semantyczne, opisujące rolę wartości, a nie jej wygląd. Pisz
`color-danger`, nie `color-red`; `color-surface-raised`, nie `color-light-gray`.
Nazwa opisowa wyglądu przestaje być prawdziwa po zmianie palety lub w trybie
ciemnym i wymusza kosztowną migrację.

Buduj skale odstępów i typografii jako uporządkowane ciągi z krótkimi,
przewidywalnymi nazwami: `space-1` … `space-8`, `font-size-sm`, `font-size-md`,
`font-size-lg`. Utrzymuj skalę zwięzłą — kilka świadomie dobranych stopni
zamiast kilkunastu wartości przypadkowych.

Przestrzegaj zasady: jedna nazwa na jedno pojęcie w całym projekcie. Nie
dopuszczaj synonimów typu `color-bg` obok `color-background` ani `spacing-*`
obok `space-*`. Przy dodawaniu tokenu sprawdź najpierw, czy pojęcie już nie
istnieje pod inną nazwą.

## Format i implementacja

Utrzymuj tokeny w jednym pliku źródłowym. Minimalna poprawna implementacja to
zmienne CSS zadeklarowane w `:root`:

```css
:root {
  --color-surface: #ffffff;
  --color-text-primary: #1f2937;
  --space-4: 1rem;
  --radius-md: 0.5rem;
}
```

W projektach wieloplatformowych rozważ plik JSON zgodny z formatem
opracowywanym przez W3C Design Tokens Community Group (DTCG), z którego
generowane są zmienne CSS oraz stałe dla innych platform. Nie utrzymuj dwóch
równoległych, ręcznie synchronizowanych źródeł wartości.

Realizuj tryby jasny i ciemny wyłącznie przez przełączanie wartości tokenów
semantycznych — nie przez duplikację komponentów ani osobne arkusze stylów dla
każdego trybu:

```css
[data-theme="dark"] {
  --color-surface: #111827;
  --color-text-primary: #f9fafb;
}
```

Komponent odwołuje się zawsze do `var(--color-surface)` i pozostaje nieświadomy
aktywnego trybu. Tokeny bazowe nie zmieniają wartości między trybami — zmieniają
się jedynie przypisania w warstwie semantycznej.

## Zakres tokenów

Obejmij tokenami co najmniej następujące kategorie wartości:

- **Kolory** — powierzchnie, tekst, obramowania, stany (danger, success,
  warning, info), stany interakcji (hover, active, disabled).
- **Typografia** — rodziny pisma, skala rozmiarów, grubości, interlinia
  (line-height), odstępy międzyliterowe, jeśli są stosowane.
- **Odstępy** — jedna skala używana dla marginesów, dopełnień i odstępów w
  siatkach.
- **Promienie zaokrągleń** — np. `radius-sm`, `radius-md`, `radius-full`.
- **Cienie** — skala elewacji, np. `shadow-sm`, `shadow-md`, `shadow-lg`.
- **Czasy i krzywe animacji** — np. `duration-fast`, `duration-normal`,
  `easing-standard`.
- **Punkty łamania (breakpoints)** — wspólne dla całego projektu wartości
  progów responsywności.

Wartość spoza tych kategorii, powtarzająca się w co najmniej dwóch miejscach,
kwalifikuje się do zamiany na token.

## Weryfikacja

Sprawdzaj narzędziowo kontrast każdej pary tokenów tekst/tło przewidzianej do
wspólnego użycia, zgodnie z wymaganiami WCAG 2.2 na poziomie AA: co najmniej
4,5:1 dla tekstu zwykłego oraz 3:1 dla tekstu dużego. Dla elementów interfejsu
i grafik informacyjnych stosuj próg 3:1 wobec sąsiadujących kolorów. Nie
polegaj na ocenie wzrokowej.

Przeprowadzaj weryfikację odrębnie dla trybu jasnego i ciemnego — para
spełniająca wymagania w jednym trybie może ich nie spełniać w drugim.
Dokumentuj dozwolone pary tokenów (np. `color-text-primary` na
`color-surface`), aby wykluczyć zestawienia nieprzebadane.

Po każdej zmianie wartości tokenu powtórz kontrolę kontrastu dla wszystkich par,
w których token uczestniczy, oraz obejrzyj kluczowe widoki w obu trybach.

## Typowe błędy modeli LLM przy tokenach

Unikaj poniższych błędów, regularnie obserwowanych w kodzie generowanym przez
modele językowe:

1. Wpisywanie wartości heksadecymalnych i pikselowych wprost w komponentach,
   mimo że odpowiednie tokeny istnieją w projekcie — zawsze najpierw przeszukaj
   plik tokenów.
2. Nazywanie tokenów od wyglądu (`color-blue`, `color-light-gray`) zamiast od
   roli (`color-primary`, `color-surface-muted`).
3. Mnożenie tokenów jednorazowych — tworzenie nowego tokenu dla każdej drobnej
   wariacji zamiast użycia istniejącego stopnia skali.
4. Realizowanie trybu ciemnego jako osobnego zestawu komponentów lub
   zduplikowanych arkuszy zamiast przełączania wartości tokenów semantycznych.
5. Pomijanie kontroli kontrastu wg WCAG 2.2 AA przy doborze lub zmianie
   wartości kolorów.
6. Odwoływanie się komponentów bezpośrednio do tokenów bazowych (palety) z
   pominięciem warstwy semantycznej.
7. Wprowadzanie drugiej konwencji nazewniczej lub synonimów istniejących nazw
   (`bg` obok `background`, `spacing` obok `space`).
8. Definiowanie punktów łamania i czasów animacji jako wartości przypadkowych w
   miejscu użycia zamiast pobrania ich z tokenów.
