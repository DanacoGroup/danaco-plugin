# Budowa kodu — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`: nazewnictwo,
dyscyplina plików, weryfikacja, profesjonalny język). Ta procedura opisuje sposób prowadzenia
budowy.

Powód istnienia procedury: model LLM pozostawiony bez dyscypliny buduje „szeroko” —
tworzy od razu wiele plików, warstwy abstrakcji na zapas, szkielety nieistniejących
funkcji i dokumenty pomocnicze. Taki kod wygląda imponująco, ale większość z niego
jest martwa, a jego utrzymanie obciąża projekt. Budowa profesjonalna jest wąska
i przyrostowa: każdy krok kończy się kodem działającym i sprawdzonym.

## Przed pierwszą linią kodu

1. **Poznaj zastane.** W istniejącym projekcie przeczytaj strukturę katalogów,
   konwencje nazewnictwa, sposób obsługi błędów i konfiguracji. Nowy kod ma być
   nieodróżnialny stylem od zastanego — chyba że zastany styl łamie standardy
   zawodowe; wtedy zgłoś to właścicielowi projektu zamiast po cichu wprowadzać
   trzeci styl.
2. **Ustal zakres słowami.** Wypowiedz w rozmowie, co powstanie, z jakich elementów
   i po czym poznać, że działa. Niejasności rozstrzygnij pytaniem przed budową,
   nie założeniem w trakcie.
3. **Sprawdź interfejsy w źródle.** Wersje bibliotek, sygnatury funkcji, schematy tabel, kształty
   odpowiedzi API — do wglądu w rzeczywistej dokumentacji lub kodzie, nie z pamięci. Konwencje i
   narzędzia właściwe dla języka pobierz z karty języka w
   `references/jezyki-programowania/jezyki-programowania.md` (odpowiednio: `bazy-danych`,
   `frameworki`, `narzedzia-budowy`).

## Budowa przyrostowa

- Buduj pionowymi przyrostami: najmniejszy działający przepływ od wejścia do wyjścia,
  potem kolejne. Nie buduj poziomo (wszystkie modele, potem wszystkie usługi, potem
  cały interfejs) — przy budowie poziomej błędy projektu ujawniają się dopiero na końcu.
- Po każdym przyrocie uruchom kod lub testy. Przyrost niesprawdzony nie istnieje —
  nie rozpoczynaj kolejnego na niesprawdzonym fundamencie.
- Twórz wyłącznie pliki potrzebne bieżącemu przyrostowi. Żadnych modułów „na
  przyszłość”, pustych klas, interfejsów z jedną implementacją wprowadzonych
  „bo kiedyś się przyda”. Abstrakcję wprowadza się przy drugim rzeczywistym
  zastosowaniu, nie przy pierwszym wyobrażonym.
- Obsługę błędów pisz razem z kodem głównym, nie „potem”: każdy punkt styku
  z zewnętrzem (plik, sieć, baza, proces) ma określone zachowanie w razie
  niepowodzenia, zgodne z konwencją projektu.
- Konfigurację (ścieżki, adresy, klucze, limity) trzymaj poza kodem — w mechanizmie
  konfiguracji przyjętym w projekcie. Sekrety nigdy w repozytorium.

## Struktura projektu budowanego od zera

- Zacznij od najmniejszej struktury uznanej zawodowo w danym ekosystemie — wzorzec
  podaje sekcja „Struktura projektu” karty języka w `jezyki-programowania`.
  Katalogi dodawaj, gdy pojawia się zawartość, która ich wymaga.
- Od pierwszej rewizji: kontrola wersji Git, plik ignorowania (`.gitignore`)
  właściwy dla ekosystemu, plik z zależnościami przypiętymi do wersji
  (np. `requirements.txt`, `package.json` z `package-lock.json`).
- Zbiór opracowań kanonicznych nowego projektu: `README.md` (przeznaczenie,
  wymagania, uruchomienie) i `CHANGELOG.md` (od pierwszego wydania). Każdy dodatkowy
  dokument wymaga uzgodnienia z właścicielem projektu — zgodnie z zasadą 4
  standardów zawodowych (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`).

## Refaktoryzacja

- Refaktoryzacja zmienia budowę wewnętrzną bez zmiany zachowania — dlatego prowadź ją
  wyłącznie przy zielonych testach (jeżeli testów brak, najpierw pokryj zmieniany
  obszar testami charakteryzującymi obecne zachowanie).
- Małe kroki, po każdym uruchomienie testów. Nie łącz refaktoryzacji ze zmianą
  funkcjonalną w jednej rewizji.
- Stare pliki i funkcje usuwaj, nie zostawiaj obok nowych „na wszelki wypadek” —
  Git przechowuje wszystko, co usunięto.

## Zakończenie budowy

Przed przekazaniem pracy wykonaj kontrolę końcową z
`../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` oraz dodatkowo sprawdź:

1. Czy każdy utworzony plik jest używany? Plik nieużywany — usuń.
2. Czy zależności są przypięte do wersji i kompletne (projekt zbuduje się na czystej
   maszynie)?
3. Czy `README.md` odpowiada stanowi faktycznemu po zmianach (uruchomienie, wymagania)?
4. Czy wynik pełnego uruchomienia lub zestawu testów został przytoczony w raporcie?
5. Czy katalog pracy przekazywany właścicielowi nie zawiera żadnych plików
   roboczych — baz testowych, katalogów `__pycache__`, wyników pośrednich,
   skryptów jednorazowych? Sprzątnięcie po budowie jest częścią zadania,
   nie uprzejmością: właściciel otrzymuje wyłącznie to, co należy do projektu.

Raport z budowy przekaż w rozmowie: co powstało, jak zweryfikowano, co świadomie
pominięto i dlaczego. Bez tworzenia pliku raportu.

## Karty referencyjne

Karty pogłębiają procedurę o techniki zawodowe. Sięgaj po kartę wtedy, gdy
zadanie wchodzi w jej obszar — nie czytaj wszystkich przy każdej budowie.

| Karta | Zawartość | Kiedy sięgnąć |
|---|---|---|
| `references/budowa-kodu/techniki-przyrostowe.md` | Szkielet kroczący, plastry pionowe i poziome, przełączniki funkcji, wzorzec dusiciela, testy charakteryzujące, budowa pod kontraktem, sterowanie testami, praca z generatorem kodu, najmniejszy krok wdrażalny | Budowa nowego systemu lub większej funkcji; przejmowanie i wymiana systemu zastanego; scalanie pracy niedokończonej |
| `references/budowa-kodu/jakosc-od-poczatku.md` | Architektura obsługi błędów, warstwy konfiguracji, idempotentność, obserwowalność, jawne granice zasobów, projektowanie na niepowodzenie zewnętrza, higiena zależności | Każda budowa dotykająca zewnętrza (sieć, baza, pliki, procesy); nowy projekt od zera; dobór bibliotek |
| `references/budowa-kodu/rzemioslo-refaktoryzacji.md` | Katalog przekształceń z warunkami bezpieczeństwa, rozbiór dużego pliku, siatka testów charakteryzujących, sygnały wykrywania kodu do refaktoryzacji, kiedy nie refaktoryzować, refaktoryzacja a wydajność, zapis w rewizjach | Refaktoryzacja wykraczająca poza zmianę kosmetyczną; praca z kodem zastanym bez testów; decyzja „refaktoryzować czy nie” |
