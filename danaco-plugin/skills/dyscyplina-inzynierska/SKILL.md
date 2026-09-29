---
name: dyscyplina-inzynierska
description: >
  Reguły prowadzenia kodu produkcyjnego Danaco (Tauri 2, Go, TypeScript/Vite, IMAP,
  WebSocket): objętość i ton komentarzy (pojedynczy komentarz do 350 znaków, udział
  komentarzy w znakach pliku poniżej 20% na plikach od 600 znaków), zakaz zakomentowanego
  kodu i logów diagnostycznych, formalny ton, kotwica w zakresie zadania oraz obowiązek
  maszynowej weryfikacji przed uznaniem zmiany za gotową. Stosuj przy każdej zmianie kodu
  w repozytorium Danaco, gdy pojawia się dryf od zadania, komentarz-esej, refaktoryzacja
  przy okazji albo abstrakcja „na przyszłość”, i gdy pada „trzymaj się standardu”, „bez
  esejów w kodzie”, „dyscyplina kodu”, „nie rozszerzaj zakresu”. Nazwy i etykiety rozstrzyga
  `standardy-nazewnictwa`; uruchamianie i strojenie walidatorów — `weryfikatory-dyscypliny`.
---

# Dyscyplina inżynierska Danaco

## Kiedy stosować

Stosuj przy każdej zmianie kodu w repozytorium Danaco, a w szczególności gdy pojawia się
dryf od zadania, skłonność do komentarza-eseju, refaktoryzacja przy okazji albo abstrakcja
„na przyszłość”.

Nie stosuj tej paczki do nadawania nazw — nazwy plików, zmiennych, funkcji, typów,
komponentów i etykiet rozstrzyga `standardy-nazewnictwa`. Uruchamiania i strojenia samych
walidatorów nie opisuje ta paczka, lecz `weryfikatory-dyscypliny`. Rzemiosła języka
i frameworka — `kodowanie`. Orientacji w dużym repozytorium — `praca-w-duzym-repo`.

Kontekst techniczny: aplikacja hybrydowa Tauri 2 (powłoka Rust), rdzeń Go, interfejs
TypeScript/Vite, poczta IMAP, kanał WebSocket. Repozytorium liczone w setkach tysięcy linii.
Dane prawne objęte tajemnicą zawodową. Komentarze i dokumentacja po polsku, identyfikatory
po angielsku.

## Zasada nadrzędna: nie wymyślaj

Nazwy, terminy, kody, struktura i decyzje pochodzą z dokumentacji projektowej, kontraktu
(`shared/contract.json`) i konwencji repozytorium — nie z inwencji modelu. Gdy czegoś nie ma
w źródłach, zapytaj albo zaproponuj jawnie jako propozycję do zatwierdzenia. Nie wprowadzaj
własnych bytów po cichu jako faktu.

## Reguły egzekwowane

### Komentarze i opis

- Pojedynczy komentarz ciągły najwyżej 350 znaków; dłuższe wyjaśnienie idzie do dokumentacji.
- Komentarze najwyżej 20% pliku liczonego **w znakach**, nie w wierszach. Reguła jest
  wyłączona dla plików krótszych niż 600 znaków, bo na krótkim pliku mianownik jest za mały,
  żeby proporcja cokolwiek mówiła.
- Komentarz opisuje „dlaczego”, nie „co”. Bez esejów, historii decyzji, dygresji.
- Ton formalny. Bez „btw”, „hack”, „magia”, „na szybko”, „chyba”, „todo/fixme”.
- Bez `print`, `console.log` i `fmt.Println` diagnostycznych oraz bez zakomentowanego kodu.

### Nazewnictwo

- Nazwa opisuje funkcję, nie obraz. Metafory przestrzenne i poetyckie są zakazane.
- Bez wymyślonych oznaczeń literowo-numerycznych komponentów. Kody istnieją tylko
  w kontrakcie.
- Etykieta UI to krótka nazwa funkcji, nie opis zdaniowy.
- Pełny katalog antywzorców i poprawnych zamienników rozstrzyga paczka
  `standardy-nazewnictwa`. Ta paczka podaje tylko granicę, o którą się potyka najczęściej.

### Kotwica w zadaniu

- Przed edycją nieznanej części repozytorium zorientuj się w dokumentacji i sąsiednich
  modułach. Nie zgaduj struktury.
- Trzymaj się zakresu zadania. Rozmiar zmiany: możliwie jeden pakiet, jedna zmiana, jeden
  test. Bez refaktoryzacji przy okazji i abstrakcji „na przyszłość”.

## Procedura

1. Ustal zakres zadania i wypisz pliki, których zamierzasz dotknąć.
2. Wprowadź zmianę, trzymając się reguł wyżej.
3. Uruchom kontrolę dyscypliny na zmienionym zakresie:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
     <ścieżki>
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py" \
     <ścieżki>
   # albo oba naraz razem z audytem porządku repozytorium:
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <ścieżki>
   ```
4. Uruchom drabinę weryfikacji właściwą dla stosu: `references/drabina-weryfikacji.md`.
5. Popraw naruszenia blokujące w kodzie, nie przez podniesienie progu.

Walidator raportuje naruszenia po każdym zapisie pliku (hook `PostToolUse`) — to hook
doradczy, nie blokuje zapisu. Twardą bramkę (kod wyjścia `3` przy naruszeniu blokującym)
stawiasz jawnie przed scaleniem, w pre-commit albo w CI, wołając walidator wprost jak wyżej.

## Kryteria zakończenia

Zmiana jest gotowa dopiero, gdy zachodzą wszystkie cztery warunki:

- kontrola dyscypliny na zmienionym zakresie zwraca `0` albo `2` (same ostrzeżenia);
- drabina weryfikacji dla dotkniętego stosu przeszła;
- lista zmienionych plików odpowiada zakresowi ustalonemu przed edycją;
- żadna nowa nazwa, kod ani termin nie został wprowadzony bez pokrycia w dokumentacji,
  kontrakcie lub jawnej propozycji do zatwierdzenia.

Deklaracja poprawności nie jest kryterium. Uruchamiasz realne narzędzia i czytasz ich wynik.

## Materiały

- `references/standardy-kodu.md` — reguły komentarzy, logowania, struktury pliku
  z przykładami
- `references/jezyk-i-terminologia.md` — język, ton, terminologia formalna, praca z danymi
  wrażliwymi
- `references/drabina-weryfikacji.md` — polecenia weryfikacji dla całego stosu Danaco
- `${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py` — walidator
  dyscypliny
- `${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py` — walidator
  nazewnictwa

## Rozgraniczenie z paczkami sąsiednimi

- `standardy-nazewnictwa` — nazwy i etykiety: jak coś nazwać.
- `weryfikatory-dyscypliny` — reguły, wagi, progi i strojenie walidatorów.
- `kodowanie` — rzemiosło języka i frameworka.
- `praca-w-duzym-repo` — gdzie zmiana należy i jaki ma zasięg.
- `standard-redakcyjny-jezykowy` — forma dokumentacji; ta paczka dotyczy kodu.
