---
name: design-systemowy
description: >
  Dokumentowanie warstwy projektowej Danaco: system projektowy, tokeny, standard CSS, księga
  projektowa, identyfikacja wizualna marki, opracowania UI/UX, banery oraz agentic UX (pamięć
  między sesjami, stopniowanie autonomii agenta, wspólne planowanie). Stosuj, gdy pada
  „opracuj system projektowy”, „udokumentuj tokeny”, „księga projektowa”, „identyfikacja
  wizualna”, „standard CSS”, „zasady designu”, „wytyczne UI/UX”, „projekt baneru”, „UX
  aplikacji agentowej”. Ta paczka odpowiada za warstwę systemową i dokumentacyjną; wykonanie
  w kliencie Danaco Console (shadcn/ui, Tailwind, tryb ciemny, WCAG, wydajność w oknie Tauri)
  prowadzi `ui-ux-pro` — gdy zadanie brzmi „zbuduj ekran” albo „ostyluj komponent”, to tamta
  paczka, nie ta.
---

# Design systemowy

## Kiedy stosować

Stosuj, gdy trzeba opracować albo udokumentować warstwę systemową projektu: system
projektowy, tokeny, standard CSS, księgę projektową, identyfikację wizualną marki, wytyczne
UI/UX, projekt baneru albo UX aplikacji agentowej.

Nie stosuj tej paczki do wykonania interfejsu w kliencie — komponent shadcn/ui, klasy
Tailwind, tryb ciemny, wzorce ARIA, wydajność w oknie Tauri i kontrola wizualna przed
scaleniem należą do `ui-ux-pro`. Ta paczka odpowiada za warstwę systemową i dokumentacyjną,
tamta za wykonanie w kliencie. Formy dokumentu (metryka, klasy, spis treści, stopka) nie
ustala ta paczka, lecz `standard-redakcyjny-jezykowy`; zakazu stylów w plikach logiki —
`architektura-i-dokumentacja`.

## Procedura

1. **Zawsze najpierw** wczytaj `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` —
   zasady dyscypliny (jedno źródło prawdy, wiążąca terminologia, zamknięty zbiór dokumentów,
   profesjonalny język) obowiązują w opracowaniach projektowych tak samo jak w kodzie.
2. Wczytaj moduł właściwy dla zadania (tabela niżej).
3. Ustal miejsce zadania w hierarchii źródeł prawdy: identyfikacja wizualna → tokeny →
   standard CSS → komponenty. Nie projektuj poziomu niżej, dopóki poziom wyżej nie jest
   rozstrzygnięty.
4. Wczytaj karty pogłębione według tabeli w pliku głównym modułu.
5. Zapisz wynik jako dokument o kształcie zgodnym ze `standard-redakcyjny-jezykowy`, nie jako
   luźny zestaw ustaleń.

## Moduły

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Standardy zawodowe | `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` | zawsze |
| Dokumentacja designu | `references/dokumentacja-designu/dokumentacja-designu.md` | system projektowy, tokeny, standard CSS, księga projektowa, identyfikacja wizualna, opracowania UI/UX, banery |
| Agentic UX | `references/agentic-ux/agentic-ux.md` | interfejs aplikacji AI lub agenta: pamięć między sesjami, stopniowanie autonomii, wspólne planowanie, miary relacji |

Szczegóły i karty poszczególnych obszarów wymienia plik główny modułu
`dokumentacja-designu`.

## Kryteria zakończenia

Opracowanie jest skończone, gdy zachodzą wszystkie cztery warunki:

- hierarchia źródeł prawdy jest zachowana i jawnie wskazana (co wynika z czego);
- każdy token ma nazwę opisującą funkcję, nie wartość ani metaforę
  (`standardy-nazewnictwa`);
- dokument ma kształt zgodny ze `standard-redakcyjny-jezykowy` i zamknięty zbiór informacji —
  brak ustalenia jest oznaczony, nie wypełniony domysłem;
- zakres jest rozgraniczony wobec `ui-ux-pro`: dokument mówi, co jest normą, a nie jak ją
  zaimplementować w kliencie.

## Odwołania między modułami

W treściach modułów odwołania do „skilla X” oznaczają moduł `X` tej paczki. Moduł
`praktyki-produktowe` (m.in. zakaz stylów w plikach logiki) należy do paczki
`architektura-i-dokumentacja`; `budowa-frontendu-backendu` i karty języków — do paczki
`kodowanie`. Gdy zadanie wchodzi w ich zakres, stosuj zasady ogólne ze standardów zawodowych
i wskaż właścicielowi projektu właściwą paczkę.

## Materiały

- `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` — siedem zasad dyscypliny
  zawodowej
- `../../wspolne/standardy-zawodowe/jezyk-zawodowy.md` — język i ton opracowań zawodowych
- `references/dokumentacja-designu/dokumentacja-designu.md` — system projektowy, tokeny,
  księga
- `references/agentic-ux/agentic-ux.md` — UX aplikacji agentowych

## Rozgraniczenie z paczkami sąsiednimi

- `ui-ux-pro` — wykonanie interfejsu w kliencie Danaco Console: komponenty, klasy Tailwind,
  tryb ciemny, ARIA, wydajność w oknie Tauri, kontrola wizualna.
- `standard-redakcyjny-jezykowy` — forma opracowania i słownik wiążący.
- `architektura-i-dokumentacja` — struktura projektu i zakaz stylów w plikach logiki.
- `standardy-nazewnictwa` — nazwy tokenów, komponentów i etykiet.
