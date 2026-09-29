---
name: architektura-i-dokumentacja
description: >
  Projektowanie systemu i wytwarzanie dokumentacji technicznej Danaco: granice modułów, model
  danych, dobór technologii, decyzje ADR, README, dokumentacja API, runbook, przewodnik
  wdrożeniowy, pełny pakiet dokumentacji architektury, a także porządkowanie struktury
  katalogów, dryf technologiczny i pęczniejące pliki. Stosuj, gdy pada „zaprojektuj
  architekturę”, „jak to podzielić na moduły”, „którą technologię wybrać”, „zapisz decyzję
  ADR”, „napisz README”, „dokumentacja API”, „runbook”, „uporządkuj strukturę projektu”. Ta
  paczka rozstrzyga, jak zbudowany jest system i co ma być w dokumencie. Obowiązujący
  kształt, metrykę, słownik i polszczyznę dokumentu prowadzi `standard-redakcyjny-jezykowy` —
  przy pisaniu dokumentu stosuj obie.
---

# Architektura i dokumentacja

## Kiedy stosować

Stosuj, gdy trzeba zaprojektować system lub jego część, wybrać technologię, zapisać decyzję
ADR, napisać README, dokumentację API, runbook albo przewodnik wdrożeniowy, a także przy
porządkowaniu struktury katalogów, dryfie technologicznym i pęczniejących plikach.

Nie stosuj tej paczki do rozstrzygania formy dokumentu — metrykę, klasy dokumentów, spis
treści, stopkę, słownik wiążący i polszczyznę prowadzi `standard-redakcyjny-jezykowy`. Przy
pisaniu dokumentu stosuj obie: ta paczka odpowiada za treść, tamta za kształt. Samego pisania
kodu nie prowadzi ta paczka, lecz `kodowanie`; oceny gotowej zmiany — `kontrola-jakosci`;
dokumentacji systemu projektowego i tokenów — `design-systemowy`.

## Procedura

1. **Zawsze najpierw** wczytaj `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` —
   zasady dyscypliny (jedno źródło prawdy, zamknięty zbiór dokumentów, wiążące nazewnictwo,
   profesjonalny język) obowiązują w architekturze i dokumentacji tak samo jak w kodzie.
2. Wczytaj moduł właściwy dla zadania (tabela niżej).
3. Wczytaj karty pogłębione według tabeli w pliku głównym modułu.
4. Przy pisaniu dokumentu zastosuj równolegle paczkę `standard-redakcyjny-jezykowy`.
5. Zapisz decyzje, które nie są oczywiste z kodu, jako ADR — decyzja bez zapisu wraca po pół
   roku jako pytanie.

## Moduły

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Standardy zawodowe | `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` | zawsze |
| Architektura | `references/architektura/architektura.md` | projektowanie systemu, granice modułów, model danych, dobór technologii, zapis ADR, ocena architektury |
| Dokumentacja techniczna | `references/dokumentacja-techniczna/dokumentacja-techniczna.md` | README, dokumentacja API, runbook, przewodnik wdrożeniowy, opracowanie technologiczne, pełny pakiet dokumentacji systemu |
| Praktyki produktowe | `references/praktyki-produktowe/praktyki-produktowe.md` | struktura projektu, drzewo katalogów, pączkowanie plików, dryf technologiczny, style w logice, sanacja projektu |
| Rozszerzenie architektury systemu | `references/engineering-core/przeglad.md` | wzorce architektoniczne, decyzje i kompromisy z materiału engineering-core |

Dla pełnego pakietu dokumentacji architektury systemu (komplet opracowań klasy: koncepcja,
architektura, model danych, kontrakty, specyfikacje, bezpieczeństwo, system wizualny) wczytaj
kartę `references/dokumentacja-techniczna/pakiet-dokumentacji-systemu.md` — zawiera skład
kanoniczny, standard redakcyjny i procedurę wytwarzania.

Rozszerzenie `references/engineering-core/` traktuj jako uzupełnienie, nie zamiennik głównych
referencji tej paczki — w razie sprzeczności rozstrzyga treść głównych `references/`.

## Kryteria zakończenia

Praca jest skończona, gdy zachodzą wszystkie cztery warunki:

- każda nieoczywista decyzja projektowa ma zapis (ADR albo rozdział opracowania) z powodem
  i odrzuconymi alternatywami;
- dokument ma kształt zgodny ze `standard-redakcyjny-jezykowy` (metryka, klasy, spis treści,
  stopka) i nie zawiera luk wykończeniowych typu „i tak dalej”, „standardowo”;
- granice modułów są wypisane wraz z regułą zależności, a nie tylko naszkicowane;
- każdy byt nazwany w dokumencie jest nazwany tak samo jak w kodzie i kontrakcie.

## Odwołania między modułami

W treściach modułów odwołania do „skilla X” oznaczają moduł `X` tej paczki. Moduły
`budowa-kodu`, `debugowanie`, `jezyki-programowania`, `frameworki` i `bazy-danych` należą do
paczki `kodowanie`; `przeglad-kodu` i `audyt-jakosci` — do paczki `kontrola-jakosci`;
`dokumentacja-designu` i `agentic-ux` — do paczki `design-systemowy`. Gdy zadanie wchodzi
w ich zakres, stosuj zasady ogólne ze standardów zawodowych i wskaż właścicielowi projektu
właściwą paczkę.

## Materiały

- `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` — siedem zasad dyscypliny
  zawodowej
- `../../wspolne/standardy-zawodowe/jezyk-zawodowy.md` — język i ton opracowań zawodowych
- `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` — kontrola końcowa
- `references/architektura/architektura.md` — projektowanie systemu i ADR
- `references/dokumentacja-techniczna/dokumentacja-techniczna.md` — rodzaje dokumentów
- `references/praktyki-produktowe/praktyki-produktowe.md` — struktura projektu i sanacja
- `references/engineering-core/przeglad.md` — rozszerzenie o architekturze systemu

## Rozgraniczenie z paczkami sąsiednimi

- `standard-redakcyjny-jezykowy` — forma dokumentu: metryka, klasy, spis treści, stopka,
  polszczyzna. Stosuj razem z tą paczką.
- `kodowanie` — jak przepisać kod wynikający z projektu.
- `praca-w-duzym-repo` — gdzie w istniejącym repozytorium leży miejsce zmiany.
- `kontrola-jakosci` — ocena gotowego kodu i projektu raportem ustaleń.
- `design-systemowy` — dokumentacja systemu projektowego, tokenów i identyfikacji wizualnej.
- `kontrakt-zrodlo-prawdy` — deklaracja kształtu danych przechodzących granicę.
