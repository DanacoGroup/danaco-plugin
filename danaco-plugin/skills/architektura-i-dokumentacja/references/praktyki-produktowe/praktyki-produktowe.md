# Praktyki produktowe — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Ta
procedura chroni strukturę produktu w czasie: projekt, który powstawał miesiącami w wielu sesjach,
psuje się nie przez pojedyncze błędy, lecz przez powolne rozmywanie struktury — pliki pęcznieją,
technologie się mnożą, style rozłażą się po logice. Każda z poniższych zasad blokuje jeden mechanizm
tego rozkładu.

## 1. Drzewo katalogów — konwencja ekosystemu, nie inwencja

- Układ katalogów bierze się z konwencji ekosystemu (wzorce podają karty
  w `jezyki-programowania` i `frameworki`), nie z pomysłu na dziś. Struktura
  niestandardowa wymaga zapisu decyzji w dokumencie architektury.
- Katalog istnieje, bo ma zawartość — nie tworzy się katalogów „na przyszłość”.
- Miejsce pliku wynika z jego odpowiedzialności; katalogi-wysypiska
  (`utils/`, `misc/`, `temp/`, `inne/`) są zabronione. Funkcja pomocnicza należy
  do modułu, któremu służy; pomocnicza dla wielu modułów — do modułu nazwanego
  po tym, co robi (`formatowanie-dat`, nie `utils`).
- Pliki robocze, wyniki pośrednie i bazy testowe nie mieszkają w drzewie
  projektu — powstają w katalogu tymczasowym i są usuwane po użyciu.

## 2. Kolejność budowy

Budowa przebiega w kolejności, która najwcześniej ujawnia błędy projektu (szczegóły:
`../kodowanie/references/budowa-kodu/budowa-kodu.md`): model danych i kontrakty → pionowy przepływ
krytyczny → kolejne przepływy → wykończenie. Interfejs użytkownika buduje się na działającym
przepływie danych, nie odwrotnie; „najpierw wygląd, logika potem” prowadzi do interfejsu udającego
działanie systemu.

## 3. Przydział odpowiedzialności i granice plików

- Jeden plik — jedna odpowiedzialność, nazwana w nazwie pliku. Test: jeżeli
  opis zawartości pliku wymaga spójnika „oraz” („obsługa faktur oraz wysyłka
  poczty oraz walidacja”), plik wymaga podziału.
- **Pączkowanie plików** — rozrost jednego pliku przez dopisywanie kolejnych
  funkcji „bo już jest otwarty” — jest zabronione. Nowa odpowiedzialność
  trafia do właściwego modułu, nawet jeżeli trzeba go utworzyć.
- Podział spuchniętego pliku prowadzi się według odpowiedzialności, nie
  mechanicznie (nie „część 1 / część 2”): wydziel spójne grupy funkcji wraz
  z ich danymi, nadaj nazwy zawodowe, zaktualizuj odwołania, usuń plik-źródło
  z martwych resztek. To refaktoryzacja — obowiązują zasady ze 
`../kodowanie/references/budowa-kodu/budowa-kodu.md` (zielone testy, małe kroki, osobne rewizje).
- Granice odpowiedzialności między warstwami są nieprzekraczalne: logika
  domenowa nie zna szczegółów interfejsu, dostęp do danych nie mieszka
  w komponentach widoku, walidacja biznesowa nie mieszka wyłącznie w formularzu.

## 4. Zakaz dryfu technologicznego

- Projekt ma dla każdego zadania jedno przyjęte rozwiązanie: jedną bibliotekę
  HTTP, jeden sposób walidacji, jeden mechanizm konfiguracji, jeden framework
  testowy. Przed dodaniem biblioteki sprawdź (`package.json`, `requirements.txt`,
  kod), czym projekt już to robi — i użyj tego.
- Wprowadzenie drugiego rozwiązania tej samej klasy to decyzja architektoniczna:
  wymaga zgody właściciela projektu i zapisu ADR (`references/architektura/architektura.md`) wraz
  z planem wycofania starego rozwiązania. Dwa rozwiązania „tymczasowo obok
  siebie” bez planu wycofania to początek dryfu.
- Ta sama zasada dotyczy wzorców: jeden sposób obsługi błędów, jeden styl
  asynchroniczności, jedna konwencja nazw — w całym projekcie.

## 5. Style we właściwych plikach

Zasada bezwzględna: style opisuje się w plikach i mechanizmach do tego
przeznaczonych, nigdy w plikach logiki.

- Wartości projektowe (kolory, typografia, odstępy) mieszkają w jednym źródle
  prawdy — pliku tokenów lub zmiennych (np. zmienne CSS w arkuszu głównym),
  opisanym w `../design-systemowy/references/dokumentacja-designu/dokumentacja-designu.md`.
- Zabronione: atrybuty `style="..."` rozsiane po HTML; obiekty stylów i sklejane
  łańcuchy CSS wewnątrz plików logiki; kolory i wymiary wpisane liczbowo
  w komponentach („magiczne wartości”); znaczniki `<style>` w szablonach
  komponentów, gdy projekt ma system arkuszy.
- Dozwolony jest mechanizm stylowania przyjęty w projekcie — arkusze CSS,
  moduły CSS, biblioteka utility (np. Tailwind) — pod warunkiem, że jest jeden
  i stosowany konsekwentnie (zasada 4 tej procedury). Styl dynamiczny zależny od
  stanu wyraża się przełączaniem klas, nie budowaniem CSS w logice.
- Znaleziony styl w niewłaściwym miejscu przenosi się do systemu stylów
  w ramach najbliższej pracy nad danym plikiem, jako osobna rewizja.

## Kontrola struktury

Przy każdej pracy nad projektem sprawdź obszar, którego dotykasz: czy plik nie
przekroczył granic odpowiedzialności, czy nie przybyło drugie rozwiązanie tej
samej klasy, czy style nie wsiąkły w logikę, czy w drzewie nie osiadły pliki
robocze. Wykryte odstępstwa zgłoś właścicielowi projektu z propozycją naprawy —
nie naprawiaj po cichu poza zakresem zadania i nie udawaj, że ich nie ma.

## Karty referencyjne

Karty pogłębiają zasady tej procedury o warsztat zawodowy. Sięgaj po kartę wtedy,
gdy zadanie wchodzi w jej obszar — nie czytaj wszystkich przy każdej pracy.

| Karta | Zawartość | Kiedy sięgnąć |
|---|---|---|
| `references/praktyki-produktowe/katalog-degeneracji.md` | Dwanaście mechanizmów rozkładu projektu (plik-bóg, wysypisko utils, dryf technologiczny, wyciek stylów, erozja granic warstw, kopie `_v2`, konfiguracja rozproszona, duplikacja, testy gnijące, zależności zamrożone, dokumentacja-fikcja, commit-zlepek) — każdy z sygnałami mierzalnymi poleceniami, receptą naprawczą i zabezpieczeniem trwałym | Diagnoza kondycji projektu; podejrzenie któregoś z mechanizmów; planowanie naprawy struktury |
| `references/praktyki-produktowe/struktury-referencyjne.md` | Wzorcowe drzewa katalogów z uzasadnieniem każdego elementu i regułami rozrostu: FastAPI, Next.js (App Router), Electron, pakiet Python, serwer MCP, monorepo, skrypty PowerShell | Zakładanie nowego projektu; ocena struktury istniejącego; decyzja, gdzie umieścić nowy moduł lub plik |
| `references/praktyki-produktowe/egzekwowanie-praktyk.md` | Strażnicy automatyczni w CI (formatowanie, granice importów, zakaz stylów w logice, kontrola narośli, pre-commit z rozwagą), rejestr długu technicznego, reguła skauta z granicami, przegląd kwartalny struktury, kontrpraktyki pracy wielosesyjnej z modelami AI, procedura przywracania porządku | Wdrażanie automatycznej kontroli standardów; zarządzanie długiem; praca sesjami LLM nad jednym projektem; sanacja projektu zdegenerowanego |
