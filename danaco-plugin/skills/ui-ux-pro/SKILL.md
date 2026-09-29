---
name: ui-ux-pro
description: >
  Budowa i stylowanie interfejsu Danaco Console w kliencie TypeScript/Vite: komponenty
  shadcn/ui na Radix UI, Tailwind utility-first, tryb ciemny i jasny, wzorce klawiatury
  i ARIA, progi kontrastu WCAG tego produktu, wydajność frontu w oknie Tauri oraz kontrola
  wizualna zrzutem ekranu przed scaleniem. Stosuj, gdy powstaje lub zmienia się widok,
  komponent, formularz, tabela, panel albo layout, i gdy pada „jak to ostylować”, „dodaj
  komponent”, „tryb ciemny”, „responsywność”, „interfejs zwalnia”, „przeskoki layoutu”, „zrób
  zrzut ekranu przed scaleniem”. Ta paczka odpowiada za wykonanie w kliencie; projektowanie
  i dokumentowanie systemu projektowego, tokenów i identyfikacji marki należy do
  `design-systemowy`, a audyt dostępności całej witryny raportem — do `kontrola-jakosci`.
---

# UI/UX Pro — interfejs Danaco Console

## Kiedy stosować

Stosuj, gdy powstaje lub zmienia się widok, komponent, formularz, tabela, panel albo layout
w kliencie Danaco Console, gdy interfejs zwalnia albo skacze przy starcie, oraz gdy przed
scaleniem zmiany wizualnej trzeba wykonać kontrolę zrzutem ekranu.

Nie stosuj tej paczki do projektowania i dokumentowania systemu projektowego, tokenów, palety
i typografii marki — to `design-systemowy`. Audytu dostępności całej witryny zakończonego
raportem ustaleń nie prowadzi ta paczka, lecz `kontrola-jakosci`; nazw komponentów i etykiet —
`standardy-nazewnictwa`; reguł komentarzy i zakresu zmiany — `dyscyplina-inzynierska`. Ta
paczka stosuje tokeny i progi ustalone w `design-systemowy`, nie ustanawia ich.

## Trzy warstwy

- **Komponenty: shadcn/ui.** Gotowe, dostępne komponenty na prymitywach Radix UI,
  dystrybuowane przez kopiowanie do kodu (nie jako zależność `node_modules`) — dzięki temu
  komponent można dostosować bez patchowania biblioteki. TypeScript-first.
- **Styl: Tailwind CSS.** Utility-first, przetwarzane w czasie budowy, mobile-first, spójne
  tokeny (kolor, odstęp, typografia), automatyczne usuwanie nieużywanych klas.
- **Specyfika Danaco Console.** Interfejs działa w oknie Tauri (WebView natywny, nie
  przeglądarka z pełnym cache), więc obowiązują tu osobne wzorce wydajności i inne progi niż
  w przeglądarce: `references/tauri-ui.md`.

## Procedura

1. Ustal, czy zadanie jest wykonaniem, czy projektowaniem. Projektowanie tokenów, palety
   i typografii oddaj paczce `design-systemowy` i wróć tutaj z ustalonymi wartościami.
2. Skomponuj widok z istniejących prymitywów, zanim dodasz nowy komponent. Instalacja
   shadcn/ui z Tailwind: `npx shadcn@latest init`, potem
   `npx shadcn@latest add button card dialog form`. Setup samego Tailwind (Vite):
   `npm install -D tailwindcss @tailwindcss/vite`, wpis pluginu w `vite.config.ts`,
   `@import "tailwindcss";` w arkuszu głównym.
3. Styluj klasami utility bezpośrednio; wydzielaj komponent tylko przy prawdziwym
   powtórzeniu, nie na zapas.
4. Zacznij od układu mobilnego i dokładaj warianty responsywne — nawet jeśli produkt działa
   głównie w oknie desktopowym, layout musi znosić zmianę rozmiaru okna.
5. Dopnij focus, etykiety i wzorce klawiatury świadomie. Prymitywy Radix dają dostępność
   częściowo; progi kontrastu i wzorce wymagane w tym produkcie:
   `references/dostepnosc-wcag.md`.
6. Sprawdź wydajność renderowania i przeskoki layoutu: `references/wydajnosc-frontu.md`.
7. Przed scaleniem wykonaj kontrolę wizualną według `references/weryfikacja-wizualna.md`.

## Kryteria zakończenia

Zmiana interfejsu jest gotowa, gdy zachodzą wszystkie pięć warunków:

- `task client:types` (`tsc --noEmit`) przechodzi bez błędów;
- widok działa w trybie ciemnym i jasnym oraz znosi zmianę rozmiaru okna;
- wzorce klawiatury i focus są sprawdzone, a progi kontrastu z
  `references/dostepnosc-wcag.md` spełnione;
- kontrola wizualna z `references/weryfikacja-wizualna.md` została wykonana i zrzut
  porównany ze stanem przed zmianą;
- nazwy komponentów i etykiety przechodzą `nazwy_guard.py` (paczka
  `standardy-nazewnictwa`).

## Nawigacja po referencjach

**Komponenty i motyw**
- `references/shadcn-components.md` — katalog komponentów i wzorce użycia
- `references/shadcn-theming.md` — tryb ciemny, zmienne CSS, warianty
- `references/shadcn-accessibility.md` — wzorce ARIA, klawiatura, focus

**Styl**
- `references/tailwind-utilities.md` — klasy layoutu, odstępów, typografii
- `references/tailwind-responsive.md` — mobile-first, punkty przełamania
- `references/tailwind-customization.md` — konfiguracja, tokeny, warianty własne

**Specyfika Danaco Console (Tauri)**
- `references/tauri-ui.md` — wydajność i zachowanie interfejsu w oknie Tauri
- `references/wydajnosc-frontu.md` — optymalizacja renderowania klienta
- `references/design-interfejsu.md` — wzorce interfejsu produktu
- `references/weryfikacja-wizualna.md` — procedura kontroli wizualnej przed scaleniem
- `references/dostepnosc-wcag.md` — progi kontrastu i wzorce dostępności dla Danaco

**Automatyzacja**
- `${CLAUDE_PLUGIN_ROOT}/skills/ui-ux-pro/scripts/shadcn_add.py` — instalacja komponentów
  z obsługą zależności
- `${CLAUDE_PLUGIN_ROOT}/skills/ui-ux-pro/scripts/tailwind_config_gen.py` — generowanie
  `tailwind.config.js`
- `${CLAUDE_PLUGIN_ROOT}/skills/ui-ux-pro/scripts/requirements.txt` — zależności obu
  skryptów; zainstaluj je przed pierwszym uruchomieniem
- `${CLAUDE_PLUGIN_ROOT}/skills/ui-ux-pro/scripts/tests/` — testy obu skryptów wraz
  z własnym plikiem `requirements.txt`; uruchamia je `tests/uruchom_testy.sh`, gdy w środowisku
  jest pytest

Pliki `references/shadcn-components.md`, `references/shadcn-theming.md`,
`references/shadcn-accessibility.md`, `references/tailwind-utilities.md`,
`references/tailwind-responsive.md` i `references/tailwind-customization.md` są w języku
angielskim — to dosłowna dokumentacja referencyjna bibliotek (nazwy klas, API komponentów),
nietłumaczona celowo, bo tłumaczenie nazw klas CSS i propsów wprowadzałoby rozjazd z tym, co
trzeba wpisać w kodzie. Pozostałe referencje tej paczki są po polsku.

## Rozgraniczenie z paczkami sąsiednimi

- `design-systemowy` — projektowanie i dokumentowanie systemu projektowego, tokenów, palety,
  typografii i identyfikacji marki. Ta paczka je stosuje, tamta je ustanawia.
- `kontrola-jakosci` — audyt dostępności całej witryny zakończony raportem ustaleń.
- `standardy-nazewnictwa` — nazwy komponentów, etykiety UI i kody.
- `dyscyplina-inzynierska` — komentarze, ton i zakres zmiany w plikach klienta.
- `most-tauri` — konfiguracja powłoki, CSP i uprawnienia okna.
