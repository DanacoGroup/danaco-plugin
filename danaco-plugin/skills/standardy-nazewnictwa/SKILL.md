---
name: standardy-nazewnictwa
description: >
  Nadawanie nazw w kodzie i dokumentach Danaco: nazwa opisuje funkcję, nie metaforę; żadnych
  wymyślonych oznaczeń literowo-numerycznych komponentów (`MOD-01`, `CMP-100`); kody
  wyłącznie z `shared/contract.json`; etykieta UI to krótka nazwa funkcji (docelowo do trzech
  słów), nie zdanie; konwencje Go, TypeScriptu i Rusta. Stosuj, gdy nadawana jest nazwa
  pliku, zmiennej, funkcji, typu, komponentu, etykiety albo nagłówka dokumentu, i gdy pada
  „jak to nazwać”, „nie wymyślaj nazw”, „bez abstrakcyjnych określeń”, „nie nadawaj własnych
  kodów”, „nazwa komponentu”, „etykieta przycisku”. Ta paczka rozstrzyga wyłącznie nazwy —
  komentarze, ton i zakres zmiany należą do `dyscyplina-inzynierska`.
---

# Standardy nazewnictwa Danaco

## Kiedy stosować

Stosuj, gdy nadawana jest nazwa pliku, zmiennej, funkcji, typu, komponentu, etykiety
interfejsu albo nagłówka dokumentu, oraz gdy trzeba ocenić nazwę już istniejącą.

Nie stosuj tej paczki do reguł komentarzy, tonu i zakresu zmiany — to
`dyscyplina-inzynierska`. Formy dokumentu (metryka, klasy, spis treści, stopka) nie ustala ta
paczka, lecz `standard-redakcyjny-jezykowy`. Kodów błędów i nazw komunikatów nie wymyśla się
tutaj: ich źródłem jest kontrakt, którym zajmuje się `kontrakt-zrodlo-prawdy`.

## Reguła

Nazwa nazywa to, czym element jest i co robi. Nie jest obrazem, metaforą ani kodem z głowy.
Jeśli dla pojęcia istnieje termin w dokumentacji, kontrakcie lub normie — używasz go, nie
tworzysz synonimu.

## Cztery zakazy

1. **Bez metafor przestrzennych i poetyckich.** Zakazane: „korzeń-wejścia”, „przedpokój”,
   „szyna lewa”, „kręgosłup”, „serce systemu”, „mózg”, „dusza”. Element nazywasz wg roli:
   `entryPoint`, `navigation`, `sidebar`, `layoutRoot`, `messageBus`.

2. **Bez wymyślonych oznaczeń literowo-numerycznych.** Zakazane: `MOD-01`, `K-3`, `CMP-100`,
   `WS_12` jako własne kody komponentów. Kody istnieją wyłącznie w kontrakcie
   (`shared/contract.json`): kody błędów, tryby sesyjne, komunikaty. Nie tworzysz własnej
   numeracji ani systemu oznaczeń.

3. **Etykieta UI to nazwa funkcji, nie opis.** Zakazane: „filtr wyszukiwania per sesja” jako
   etykieta. Piszesz `Filtry`.
   - Norma: najwyżej trzy słowa i bez fraz sesyjnych („per sesja”, „w tej sesji”). Egzekwuje
     ją przegląd, nie walidator.
   - Próg bramki: `nazwy_guard.py` zgłasza etykietę powyżej sześciu słów (reguła
     `etykieta-jako-zdanie`, ostrzeżenie). Szerszy próg bramki jest celowy, żeby nie trafiać
     fałszywie na uzasadnione etykiety czterosłowowe.

4. **Nazwy plików i nagłówki rzeczowe.** Nazwa pliku wynika z funkcji i konwencji katalogu.
   Nagłówek dokumentu opisuje treść, nie jest metaforą.

## Poprawne wzorce

- Go: `PascalCase` eksport, `camelCase` lokalnie, pakiety krótkie i rzeczowe.
- TypeScript: `camelCase` zmienne i funkcje, `PascalCase` typy i komponenty React.
- Rust: `snake_case` funkcje i zmienne, `PascalCase` typy, `SCREAMING_SNAKE_CASE` stałe.
- Wszędzie: identyfikatory po angielsku, komentarze i etykiety po polsku.

## Procedura, gdy nie znasz właściwej nazwy

Nie wymyślaj. Kolejno:

1. Sprawdź dokumentację i kontrakt (`shared/contract.json`).
2. Sprawdź, jak nazwano analogiczny element w sąsiednim module.
3. Gdy nadal brak wzorca — zaproponuj nazwę jawnie jako propozycję do zatwierdzenia, nie
   wprowadzaj jej po cichu.

Pełny katalog antywzorców z zamiennikami: `references/katalog-antywzorcow-nazewnictwa.md`.

## Narzędzie: nazwy_guard.py

`nazwy_guard.py` sprawdza automatycznie to, co reszta tej paczki opisuje: wymyślone
oznaczenia literowo-numeryczne komponentów, etykiety UI będące zdaniami zamiast krótkich nazw
funkcji oraz identyfikatory zbudowane z metafory zamiast funkcji.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py" \
  <plik-lub-katalog> [...]
python3 "${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py" \
  --config konfiguracja.json src/
```

Wszystkie trzy reguły nazewnicze są ostrzeżeniami: `etykieta-jako-zdanie`,
`oznaczenie-literowo-numeryczne` i `nazwa-metaforyczna`. Blokują wyłącznie `kodowanie-pliku`
(plik nie w UTF-8) i `plik-nieczytelny`. Kody wyjścia jak w `style_guard.py`: `0` czysto,
`2` same ostrzeżenia, `3` naruszenie blokujące, `4` błąd konfiguracji narzędzia.

Ostrzeżenie nie zwalnia z normy — normę egzekwuje przegląd. Słownik metafor
(`slowaMetaforyczne`) i allowlistę uzasadnionych technicznie oznaczeń (`allowlistaNazw`, np.
`Tauri2`, `SHA256`, `OAuth2`) dostrajasz w pliku `konfiguracja-dyscypliny.json` — podanym
przez `--config` albo znalezionym w korzeniu repozytorium — bez edycji skryptu. Strojenie
progów i obsługa fałszywych trafień: paczka `weryfikatory-dyscypliny`.

## Kryteria zakończenia

Nazewnictwo w zmianie jest gotowe, gdy zachodzą wszystkie cztery warunki:

- `nazwy_guard.py` na zmienionym zakresie zwraca `0` albo `2`, a każde ostrzeżenie zostało
  ocenione, nie pominięte;
- żadna nowa nazwa nie jest metaforą ani własnym kodem literowo-numerycznym;
- każdy użyty kod błędu, tryb i komunikat pochodzi z `shared/contract.json`;
- każda nowa etykieta interfejsu mieści się w normie trzech słów albo ma zapisane
  uzasadnienie odstępstwa.

## Materiały

- `references/katalog-antywzorcow-nazewnictwa.md` — antywzorce nazewnicze z poprawnymi zamiennikami
- `${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py` — walidator
  nazewnictwa

## Rozgraniczenie z paczkami sąsiednimi

- `dyscyplina-inzynierska` — komentarze, ton, zakres zmiany, kotwica w zadaniu.
- `weryfikatory-dyscypliny` — wagi reguł, progi, allowlista, wpięcie w pre-commit i CI.
- `standard-redakcyjny-jezykowy` — forma dokumentu i słownik wiążący terminologii.
- `kontrakt-zrodlo-prawdy` — źródło kodów błędów, trybów i nazw komunikatów.
