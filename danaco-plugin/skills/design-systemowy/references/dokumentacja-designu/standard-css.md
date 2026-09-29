# Standard CSS — karta

Stosuj niniejszą kartę przy pisaniu i przeglądaniu arkuszy stylów w projektach
Danaco. Karta zakłada istnienie pliku tokenów (zob. kartę „Tokeny projektowe”)
i reguluje sposób ich użycia w CSS.

## Organizacja arkuszy

Porządkuj pliki stylów według stałej sekwencji warstw, ładowanych w tej
kolejności:

1. **Tokeny** — zmienne CSS w `:root` oraz nadpisania dla trybów.
2. **Style bazowe / reset** — normalizacja przeglądarek, domyślna typografia
   elementów (`body`, nagłówki, odnośniki), `box-sizing`.
3. **Układ** — siatki, kontenery, szablony stron.
4. **Komponenty** — po jednym pliku lub sekcji na komponent.

Umieszczaj style wyłącznie w plikach stylów. Nie stosuj atrybutu `style` w znacznikach ani CSS
budowanego w logice aplikacji (sklejanie łańcuchów stylów w kodzie), zgodnie z
`../architektura-i-dokumentacja/references/praktyki-produktowe/praktyki-produktowe.md`. Wyjątkiem są
wartości z natury dynamiczne (np. pozycja elementu przeciąganego) — przekazuj je wówczas przez
zmienne CSS ustawiane na elemencie, a reguły trzymaj w arkuszu.

Nie duplikuj reguł między plikami. Wspólne wzorce przenoś do warstwy niższej
(układ, style bazowe) albo do klasy współdzielonej.

## Konwencje nazw klas

Wybierz jedną konwencję nazewniczą na projekt i stosuj ją bez wyjątków:
metodykę BEM (block__element--modifier) albo podejście utility-first (np.
Tailwind CSS) — nigdy obie równocześnie. Przed dopisaniem stylów ustal, która
konwencja obowiązuje w projekcie, i podporządkuj się jej.

Przy konwencji BEM przestrzegaj wzorca:

```css
.card { }
.card__header { }
.card__title { }
.card--highlighted { }
```

Nadawaj klasom nazwy opisujące rolę lub strukturę, nie wygląd. Zakazane są
klasy typu `.red-text`, `.big-margin`, `.blue-button` — po zmianie palety lub
motywu nazwa kłamie. Pisz `.error-message`, `.section-spacing`,
`.button--primary`.

Utrzymuj jedną nazwę na jedno pojęcie: nie twórz `.btn` obok `.button` ani
`.modal` obok `.dialog` dla tego samego komponentu.

## Selektory i specyficzność

Buduj selektory na klasach. Nie stylizuj po identyfikatorach (`#header`) —
zawyżają specyficzność i uniemożliwiają wielokrotne użycie. Ograniczaj
selektory elementów do warstwy stylów bazowych.

Utrzymuj płaską specyficzność: preferuj pojedynczą klasę
(`.card__title`) zamiast zagnieżdżeń (`.card .header .title`). Zagnieżdżenie
głębsze niż jeden poziom traktuj jako sygnał do refaktoryzacji. Płaska
specyficzność sprawia, że kolejność w arkuszu, a nie licytacja selektorów,
rozstrzyga o wyniku.

Nie używaj `!important`. Dopuszczalny wyjątek stanowią wąskie, świadomie
zaprojektowane klasy narzędziowe (np. `.visually-hidden`) oraz nadpisywanie
stylów wstrzykiwanych przez kod zewnętrzny, na który nie masz wpływu — każdy
taki przypadek opatrz komentarzem z uzasadnieniem.

## Układ i responsywność

Buduj układy wyłącznie za pomocą flexbox i CSS grid: grid dla struktur
dwuwymiarowych (siatki stron, karty w kolumnach), flexbox dla jednowymiarowych
(paski narzędzi, rzędy przycisków). Nie stosuj `float` ani `position: absolute`
do budowy układu — pozycjonowanie absolutne rezerwuj dla nakładek, plakietek i
elementów świadomie wyjętych z przepływu dokumentu.

Stosuj jednostki względne: `rem` dla typografii i odstępów, procenty oraz
jednostki `fr` dla wymiarów w siatkach. Piksele rezerwuj dla wartości z natury
stałych, takich jak szerokość obramowania.

Pobieraj punkty łamania z tokenów projektu — nie wpisuj progów przypadkowych w
poszczególnych plikach. Ponieważ zmienne CSS nie działają w warunkach
`@media`, utrzymuj progi w jednym miejscu (preprocesor, generator z pliku
tokenów lub udokumentowana stała) i odwołuj się wyłącznie do niego.

Wybierz jedno podejście — mobile-first (media queries `min-width`) albo
desktop-first (`max-width`) — i stosuj je konsekwentnie w całym projekcie.
Mieszanie obu podejść prowadzi do reguł wzajemnie się nadpisujących.

## Stany i interakcje

Definiuj komplet stanów dla każdego komponentu interaktywnego: `:hover`,
`:focus-visible`, `:active` oraz stan wyłączony (`:disabled` lub
`[aria-disabled="true"]`). Komponent bez zdefiniowanych stanów traktuj jako
nieukończony.

Zapewnij widoczny wskaźnik fokusa — to wymóg bezwzględny, wynikający z
WCAG 2.2 (kryterium 2.4.7 Focus Visible, poziom AA). Nie usuwaj obrysu
(`outline: none`) bez wprowadzenia równorzędnego, wyraźnego wskaźnika:

```css
.button:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
```

Preferuj `:focus-visible` zamiast `:focus`, aby wskaźnik pojawiał się przy
nawigacji klawiaturą, nie przy każdym kliknięciu. Pobieraj kolory i czasy
przejść stanów z tokenów; zadbaj, aby stany hover i active różniły się od stanu
spoczynkowego w sposób spełniający wymagania kontrastu.

## Typowe błędy modeli LLM w CSS

Unikaj poniższych błędów, regularnie obserwowanych w kodzie generowanym przez
modele językowe:

1. Sięganie po `!important` jako narzędzie pierwszego wyboru przy konflikcie
   stylów, zamiast obniżenia specyficzności lub poprawienia kolejności reguł.
2. Mieszanie konwencji nazewniczych — dopisywanie klas utility do projektu
   prowadzonego w BEM lub odwrotnie.
3. Wpisywanie wartości magicznych (`margin: 13px`, `color: #3a3a3a`) zamiast
   użycia tokenów istniejących w projekcie.
4. Budowanie układu na `position: absolute` z ręcznie dobranymi
   współrzędnymi zamiast flexbox lub grid.
5. Powielanie identycznych bloków reguł w wielu selektorach zamiast
   wydzielenia klasy wspólnej.
6. Media queries z wartościami przypadkowymi (`@media (min-width: 743px)`)
   zamiast punktów łamania zdefiniowanych w tokenach projektu.
7. Usuwanie `outline` z elementów fokusowalnych bez zastępczego wskaźnika
   fokusa.
8. Stylowanie inline w znacznikach lub sklejanie CSS w logice aplikacji zamiast
   utrzymania stylów w arkuszach.
