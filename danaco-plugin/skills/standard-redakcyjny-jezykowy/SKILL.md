---
name: standard-redakcyjny-jezykowy
description: >
  Obowiązujący kształt każdego opracowania Danaco: nagłówek i metryka, klasy dokumentów, spis
  treści, korpus, stopka, wymóg form wizualnych i normatywnej szczegółowości, słownik
  wiążący, zasady polszczyzny i typografii oraz konwencje zapisu bytów kodu w tekście.
  Stosuj przy redagowaniu i przeglądzie dokumentacji Danaco oraz gdy pada „jak to
  zredagować”, „standard dokumentu”, „metryka dokumentu”, „słownik terminów”, „zasady
  polszczyzny w dokumentacji”, „czy ten dokument jest zgodny ze standardem”. Ta paczka
  rozstrzyga formę dokumentu; jego zawartość merytoryczną (architektura, ADR, README, API,
  runbook) prowadzi `architektura-i-dokumentacja`, a nazwy bytów w kodzie —
  `standardy-nazewnictwa`.
---

# Standard redakcyjny i językowy Danaco

## Kiedy stosować

- Przy pisaniu nowego dokumentu wchodzącego do zbioru opracowań Danaco.
- Przy przeglądzie istniejącego dokumentu pod kątem zgodności ze standardem (nagłówek,
  metryka, klasy, spis treści, stopka, oznaczenia stanu wdrożenia).
- Przy wątpliwości co do terminologii, zapisu bytów kodu w tekście, zasad polszczyzny lub
  typografii.

Nie stosuj tej paczki do rozstrzygania zawartości merytorycznej dokumentu — co ma być
w README, jak zbudowany jest system, jaką decyzję zapisać w ADR prowadzi
`architektura-i-dokumentacja`. Przy pisaniu dokumentu stosuj obie: ta paczka odpowiada za
formę, tamta za treść. Nazw bytów w kodzie nie ustala ta paczka, lecz
`standardy-nazewnictwa`; reguł komentarzy w kodzie — `dyscyplina-inzynierska`. Tam, gdzie
zakresy się przenikają (komentarz w kodzie odsyłający do dokumentacji), stosuje się je
razem.

## Zasada nadrzędna

Opracowanie niesie zamknięty zbiór informacji. Jeśli dokument czegoś nie rozstrzyga,
wykonawca nie rozstrzyga tego sam za dokument — brak ustalenia trzeba oznaczyć i zapytać,
zamiast wypełniać go własnym domysłem.

## Procedura

1. Przeczytaj `references/standard-redakcyjny-i-jezykowy.md` w całości przed redagowaniem
   jakiegokolwiek opracowania wchodzącego do zbioru dokumentacji Danaco. Przy dokumencie
   kolejnym wystarczy część odpowiadająca jego klasie — dokument klasy „Nawigacja” ma inne
   wymogi niż specyfikacja techniczna, a standard to rozróżnia.
2. Zbuduj nagłówek i obie metryki zgodnie z wymaganym układem.
3. Zbuduj spis treści i korpus w kolejności narzuconej przez klasę dokumentu.
4. Zachowaj wymóg form wizualnych i normatywnej szczegółowości — unikaj luk wykończeniowych
   typu „i tak dalej”, „podobnie”, „standardowo”.
5. Trzymaj się słownika wiążącego; nie wymyślaj własnych terminów ani skrótów.
6. Zamknij dokument stopką i, jeśli dotyczy, oznaczeniem stanu wdrożenia.

## Kryteria zakończenia

Dokument jest gotowy, gdy zachodzą wszystkie pięć warunków:

- obie metryki są obecne i mają wypełniony komplet pól obowiązkowych;
- klasa dokumentu jest zadeklarowana, a układ korpusu jej odpowiada;
- udział wierszy w formach innych niż ciągła proza spełnia próg z rozdziału o formach
  wizualnych;
- objętość spełnia próg znakowy właściwy dla klasy dokumentu, a wykazy obowiązkowe są
  kompletne (jedno bez drugiego nie wystarcza);
- stopka jest obecna, a każdy termin pochodzi ze słownika wiążącego.

Pełne kryteria kontroli końcowej wraz z progami: `references/standard-redakcyjny-i-jezykowy.md`.

## Materiały

- `references/standard-redakcyjny-i-jezykowy.md` — pełna treść normatywna: metryka, klasy
  dokumentów, wymóg form wizualnych, słownik wiążący, zasady polszczyzny, typografia,
  konwencje zapisu bytów kodu, tryb postępowania przy braku ustalenia

## Rozgraniczenie z paczkami sąsiednimi

- `architektura-i-dokumentacja` — zawartość merytoryczna dokumentu: architektura, ADR,
  README, dokumentacja API, runbook. Stosuj razem z tą paczką.
- `standardy-nazewnictwa` — nazwy bytów w kodzie i nagłówki rzeczowe.
- `dyscyplina-inzynierska` — komentarze i ton w kodzie.
- `design-systemowy` — opracowania projektowe, które również podlegają temu standardowi
  formy.
