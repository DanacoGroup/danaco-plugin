# Design interfejsu — karta

Karta obejmuje warstwę wizualną interfejsu klienta: typografię, kolor, siatkę, gęstość
i zakazy odróżniające projekt świadomy od wyniku domyślnego modelu. Tokeny i system
projektowy na poziomie produktu prowadzi
`../design-systemowy/references/dokumentacja-designu/system-projektowy.md`; dostępność —
`references/dostepnosc-wcag.md`; kontrolę wizualną przed scaleniem —
`references/weryfikacja-wizualna.md`.

## Zakazy

- Fonty **zakazane** jako główne: Inter, Roboto, Arial, Open Sans, Lato, Space Grotesk,
  Poppins.
- Zakaz fioletowo-niebieskich gradientów na hero, zakaz `border-radius: 9999px` na wszystkim, zakaz
  cieni `shadow-xl` wszędzie.
- Zakaz emoji jako ikon. Używaj spójnego zestawu SVG (lucide, phosphor, heroicons — jeden zestaw na
  projekt).
- Zakaz trzech kart w rzędzie z ikoną+nagłówkiem+tekstem jako domyślnej sekcji „features”.

## Typografia

1. Wybierz parę fontów **z charakterem** zanim napiszesz kod: display (nagłówki) + text (treść).
   Dobre kierunki: serif editorial (Fraunces, Newsreader, Source Serif 4), geometric z osobowością
   (General Sans, Cabinet Grotesk, Clash Display), mono-akcent (JetBrains Mono, Spline Sans Mono) na
   etykiety/liczby.
2. Skala modularna: ustal ratio (1.2–1.333) i trzymaj się jej. Definiuj w tokenach, nie ad hoc.
3. `line-height`: nagłówki 1.05–1.2, treść 1.5–1.7. `letter-spacing`: ujemny na dużych nagłówkach
   (-0.01 do -0.03em).
4. Maksymalna szerokość tekstu: 60–75 znaków (`max-width: 65ch`).

## Kolor

1. Zbuduj paletę z **jednego** koloru bazowego: 10–12 kroków neutrali z delikatnym odcieniem
   bazowego (nigdy czysta szarość #808080), 1 akcent, 1–2 kolory semantyczne (sukces/błąd).
2. Pracuj w OKLCH — równomierna percepcja jasności. Tło ciemne to nie #000, jasne to nie #fff:
   przesuń o 2–4% w stronę odcienia.
3. Kontrast: tekst treści ≥ 4.5:1, duży tekst ≥ 3:1 (sprawdza to `references/dostepnosc-wcag.md`).
4. Tryb ciemny projektuj równolegle, nie jako inwersję na końcu. Tokeny semantyczne (`--surface`,
   `--text-muted`), nie surowe kolory w komponentach.

## Spacing i layout

1. Siatka 4px lub 8px — każdy margines/padding to wielokrotność. Definiuj skalę (4, 8, 12, 16, 24,
   32, 48, 64, 96).
2. Hierarchia przez przestrzeń: odstęp między sekcjami ≥ 2× odstępu wewnątrz sekcji.
3. Unikaj symetrycznej nudy: świadoma asymetria, przełamanie siatki jednym elementem, zróżnicowane
   szerokości sekcji.
4. Gęstość dopasuj do typu: dashboard/narzędzie = gęsto (padding 8–12px w wierszach tabel),
   marketing = przestronnie.

## Motion

1. Animuj tylko `transform` i `opacity`. Czas: micro-interactions 120–200ms, przejścia widoków
   250–400ms.
2. Easing: `cubic-bezier(0.32, 0.72, 0, 1)` na wejścia, `ease-out` na hover. Nigdy `linear` poza
   spinnerami.
3. Wejścia elementów: stagger 30–50ms między elementami listy, translate 4–12px max.
4. Zawsze respektuj `prefers-reduced-motion`.

## Proces

1. PRZED kodem: określ w 2 zdaniach kierunek (np. „editorial, ciepłe neutrale, serif display, gęsta
   typografia”) i zapisz go w komentarzu na górze pliku tokenów.
2. Najpierw tokeny (`../design-systemowy/references/dokumentacja-designu/design-tokens.md`),
   potem komponenty.
3. **Po zbudowaniu** uruchom pętlę weryfikacji wizualnej (`references/weryfikacja-wizualna.md`) —
   obejrzyj własny interfejs i popraw, minimum 2 iteracje.
