# Egzekwowanie praktyk — narzędzia zamiast pamięci

Praktyka, której przestrzeganie zależy od pamięci i dobrej woli, przestaje
obowiązywać przy pierwszym terminie. Praktyka trwała to praktyka wymuszona
narzędziem: naruszenie zatrzymuje budowę albo scalenie, a nie czeka, aż ktoś
je zauważy. Ta karta opisuje, jak zamienić zasady procedury na strażników
automatycznych, jak zarządzać świadomie zaciągniętym długiem i jak utrzymać
strukturę w pracy wielosesyjnej z modelami AI.

## 1. Strażnicy automatyczni

Zasada nadrzędna: standard egzekwowany prośbą w przeglądzie kodu jest
standardem opcjonalnym. Przenoś egzekwowanie do CI, a przegląd ludzki
zostaw na to, czego narzędzie nie sprawdzi — sens, nazwy, granice
odpowiedzialności.

**Formatowanie i lint — wymuszone, nie zalecane.** Formater (black/ruff
format, prettier) i linter (ruff, eslint) działają w CI w trybie kontroli:

```
ruff format --check . && ruff check .        # Python
npx prettier --check . && npx eslint .       # JS/TS
```

Wynik niezerowy blokuje scalenie. Konfiguracja mieszka w repozytorium
(`pyproject.toml`, `eslint.config.js`) — jedna dla wszystkich, bez ustawień
osobistych nadpisujących projektowe. Spory o styl rozstrzyga się raz, zmianą
konfiguracji przez ADR, nie dyskusją przy każdej rewizji.

**Granice architektury.** Kontrakt warstw zapisany deklaratywnie
i sprawdzany w CI:

```
# .importlinter (Python)
[importlinter]
root_package = nazwa_aplikacji
[importlinter:contract:warstwy]
name = Kierunek zaleznosci
type = layers
layers =
    nazwa_aplikacji.faktury.router
    nazwa_aplikacji.faktury.uslugi
    nazwa_aplikacji.faktury.repozytorium
```

Dla JS/TS — `dependency-cruiser` z regułami `no-circular` oraz zakazem
importu `app/ → repositories/` z pominięciem warstwy usług. Naruszenia
zastane w chwili wdrożenia strażnika trafiają na listę wyjątków — nowa lista
wyjątków może wyłącznie maleć, co sprawdza skrypt porównujący jej długość
z gałęzią główną.

**Zakaz stylów w logice.** Reguły ESLint: `react/forbid-dom-props` z zakazem
`style`, `react/forbid-component-props` analogicznie; stylelint
z `declaration-property-value-allowed-list` wymuszającym zmienne zamiast
wartości wprost dla kolorów. Wyjątek dopuszczalny wyłącznie adnotacją
w linii z uzasadnieniem — i te adnotacje też licz w CI, próg rosnący
oznacza erozję.

**Kontrola plików-narośli.** Jeden skrypt w CI, uruchamiany przy każdym scaleniu, wykrywający
naroślą strukturalne z karty `references/praktyki-produktowe/katalog-degeneracji.md`:
pliki `_v2|_stary|_kopia|_backup`, katalogi z listy zakazanej (`utils`,
`misc`, `temp`), pliki `.md` spoza listy kanonicznej, pliki > progu linii,
pliki robocze (`*.tmp`, `*.log`, zrzuty baz) w drzewie. Skrypt wypisuje
trafienia i kończy się błędem; progi trzyma w konfiguracji na górze pliku,
nie rozsiane po kodzie.

**Pre-commit — z rozwagą.** Do haka lokalnego trafia wyłącznie to, co działa
w pojedynczych sekundach i naprawia się samo: formatowanie zmienionych
plików, porządek importów, skaner sekretów (`gitleaks protect`), zakaz
plików > 1 MB. NIE trafiają tam: pełny zestaw testów, budowa projektu,
analiza całego repozytorium — hak wolny bywa omijany (`--no-verify`),
a omijany hak uczy omijania wszystkich haków. Prawda jest w CI; pre-commit
to tylko szybsze sprzężenie zwrotne. Konfigurację haka wersjonuj w repo
(`.pre-commit-config.yaml`), by wszyscy mieli tę samą.

## 2. Dług techniczny jako rejestr, nie jako TODO

Komentarz `# TODO: naprawić` to dług niezaciągnięty, tylko ukryty — nie ma
właściciela, terminu ani widoczności, więc nie istnieje dla planowania.
Prowadź dług jak rejestr zobowiązań w systemie zgłoszeń:

- **Każda pozycja nazwana**: co jest nie tak, gdzie (ścieżki plików), jaki
  mechanizm degeneracji reprezentuje, co się stanie, jeśli zostanie
  (konsekwencja, nie ogólnik „będzie gorzej”).
- **Każda pozycja ma właściciela i plan spłaty**: konkretną iterację albo
  warunek wyzwalający („przy najbliższej pracy nad modułem faktur”).
  Pozycja bez planu to nie dług, to rezygnacja.
- **Widoczność w planowaniu**: rejestr przeglądany przy planowaniu każdej
  iteracji; stały udział czasu na spłatę (praktyczny zakres 10–20%
  przepustowości) zamiast mitycznego „sprintu porządkowego kiedyś”.

Kiedy dług wolno zaciągnąć świadomie: termin zewnętrzny nieprzesuwalny,
rozwiązanie docelowe znane, koszt odroczenia oszacowany, wpis do rejestru
utworzony w tej samej chwili co skrót w kodzie — wszystkie cztery warunki
naraz. Skrót w kodzie oznaczaj odnośnikiem do pozycji rejestru, nie gołym
TODO. Kontrola w CI domyka pętlę:

```
grep -rn 'TODO\|FIXME' src --include='*.py' --include='*.ts' | grep -vE 'DLUG-[0-9]+' && exit 1
```

TODO bez odnośnika do rejestru nie przechodzi.

## 3. Reguła skauta — z granicami

„Zostaw obszar czystszym, niż zastałeś” działa tylko z twardymi granicami;
bez nich zamienia każde zadanie w niekończącą się refaktoryzację.

- **Poprawiaj obszar, którego dotykasz** — plik, w którym robisz zmianę,
  wolno ci uporządkować: nazwa myląca, martwy kod, styl w logice, brak testu
  dla zmienianej funkcji.
- **W osobnej rewizji** — porządki przed zmianą właściwą lub po niej, nigdy
  zmieszane z nią. Rewizja porządkowa nie zmienia zachowania i przechodzi
  te same testy; recenzent widzi osobno „co uporządkowano” i „co zmieniono”.
- **Bez rozszerzania zakresu** — porządek wykraczający poza dotykany obszar
  (sąsiedni moduł, przekrojowa zmiana nazewnictwa, migracja biblioteki) to
  nie sprzątanie, to zadanie: wpis do rejestru długu i osobne planowanie.
  Praktyczny wyznacznik: sprzątanie mieści się w kilkunastu minutach
  i dotyka plików, które zmiana właściwa i tak otwiera.
- **Odkrycie ≠ obowiązek naprawy**: znaleziony problem poza zakresem
  zgłoś (rejestr długu), nie naprawiaj po cichu — po cichu naprawione nie
  podlega przeglądowi i nie uczy zespołu.

## 4. Przegląd struktury — rytm kwartalny

Strażnicy łapią naruszenia punktowe; trendy widać dopiero z dystansu.
Raz na kwartał wykonaj przegląd strukturalny — godzina pracy z poleceniami,
wynik jako krótki zapis z decyzjami (co do rejestru długu, co do ADR):

```
# rozkład rozmiarów plików: czy ogon rośnie
find src -name '*.py' -o -name '*.ts' | xargs wc -l | sort -rn | head -20
cloc src --by-file --quiet | tail -25

# przyrost zależności od poprzedniego przeglądu
git diff HEAD@{3.months.ago} -- package.json pyproject.toml requirements*.txt
pip list --outdated | wc -l ; npm outdated | wc -l

# mapa importów: nowe cykle, nowe skróty przez warstwy
lint-imports ; npx depcruise src --output-type err-long

# pliki najgorętsze (częstość zmian x rozmiar = kandydaci do podziału)
git log --since='3 months ago' --name-only --pretty=format: | sort | uniq -c | sort -rn | head -15

# duplikacja i pominięte testy — trend względem poprzedniego kwartału
npx jscpd src --min-tokens 50 ; grep -rc 'skip' tests | awk -F: '$2>0'
```

Porównuj z wynikami poprzedniego przeglądu — wartości bezwzględne znaczą mniej niż kierunek zmian.
Trzy pytania na koniec: który mechanizm z karty
`references/praktyki-produktowe/katalog-degeneracji.md` postąpił od ostatniego przeglądu, czy któryś
strażnik wymaga zaostrzenia progu, czy struktura nadal odpowiada wzorcowi z karty
`references/praktyki-produktowe/struktury-referencyjne.md` — a jeśli nie, czy odstępstwo ma ADR.

## 5. Praca wielosesyjna z modelami AI

Projekt rozwijany sesjami modelu LLM degeneruje szybciej niż rozwijany przez
zespół ludzi — z przyczyny strukturalnej: model nie ma pamięci konwencji
między sesjami. Każda sesja zaczyna od zera i bez przeciwdziałania podejmuje
lokalne decyzje na nowo: dobiera „swoją” bibliotekę HTTP (dryf), dopisuje do
otwartego pliku (pączkowanie), tworzy pomocniczy `utils.py` (wysypisko),
zostawia plik podsumowania (narośl). Dwadzieścia sesji to potencjalnie
dwadzieścia kompletów lokalnych konwencji w jednym drzewie.

Kontrpraktyki:

- **Dokument konwencji czytany na starcie sesji.** Jeden plik (CLAUDE.md
  lub dokument konwencji wskazany w nim) z rozstrzygnięciami, które inaczej
  zapadałyby co sesję: rozwiązania przyjęte dla każdej klasy zadań
  (biblioteka HTTP, walidacja, testy, styl asynchroniczności), struktura
  katalogów z regułami rozrostu, konwencje nazw, polecenia budowy i testów,
  lista rzeczy zakazanych. Utrzymuj go krótkim i rozstrzygającym — dokument
  konwencji, którego nie da się przeczytać w dwie minuty, nie będzie
  stosowany. Aktualizuj go w tej samej rewizji, w której zapada nowa
  decyzja konwencji.
- **Kontrola końcowa po każdej sesji.** Przed zamknięciem sesji przejrzyj
  `git status` i `git diff` pod kątem podpisu degeneracji sesyjnej: nowe
  zależności w manifeście (czy uzgodnione?), nowe pliki poza wzorcem
  struktury, pliki `.md` spoza listy kanonicznej, style w logice, rozrost
  plików dotykanych. To samo sprawdzają strażnicy w CI — kontrola sesyjna
  łapie problem, zanim rewizja w ogóle powstanie.
- **Audyt strukturalny po serii sesji.** Po intensywnym okresie pracy
  z modelem (praktycznie: co 10–15 sesji albo po ukończeniu funkcji) wykonaj
  skrócony przegląd z sekcji 4 — sesje AI zagęszczają zmiany w czasie, więc
  rytm kwartalny bywa za rzadki. Szczególna uwaga: duplikacja logiki
  (model nie wie, że funkcja już istnieje, gdy nie szukał) i rozjazd
  dokumentów kanonicznych z kodem.
- **Strażnicy z sekcji 1 są tu podwójnie ważni**: model reaguje na czerwony
  wynik CI w tej samej sesji — to jedyna „pamięć” egzekwowana niezależnie
  od tego, co sesja przeczytała.

## 6. Przywracanie porządku w projekcie zdegenerowanym

Projekt po miesiącach bez dyscypliny naprawiaj w stałej kolejności — odruch
„najpierw wielka refaktoryzacja” pogłębia chaos, bo refaktoryzuje bez siatki
i bez zatrzymania dopływu.

**Krok 1 — inwentaryzacja.** Przebiegnij pełny zestaw sygnałów z karty
`references/praktyki-produktowe/katalog-degeneracji.md` (wszystkie polecenia, wyniki na listę).
Zbuduj obraz: które mechanizmy postąpiły, jak głęboko, co jest najtańsze w naprawie, co
najgroźniejsze w skutkach. Wynik to uszeregowany rejestr — bez naprawiania czegokolwiek na tym
etapie.

**Krok 2 — zamrożenie dopływu.** Wdroż strażników z sekcji 1 z listami
wyjątków obejmującymi stan zastany: od tej chwili degeneracja nie
przyrasta (nowe naruszenie = czerwone CI), choć stara jeszcze istnieje.
To najwyższa stopa zwrotu całej procedury — dzień pracy zatrzymujący
pogłębianie problemu. Ustal też mechanizm malejących list wyjątków.

**Krok 3 — naprawa struktury krokami z testami.** Spłacaj rejestr od pozycji o najlepszym stosunku
skutku do kosztu, zwykle w kolejności: sekrety i konfiguracja (ryzyko) → kopie plików i narośla
(tanie, czyszczą obraz) → wysypiska i pączkujące pliki (odblokowują dalszą pracę) → granice warstw
(najdroższe, wymagają testów charakteryzujących —
`../kodowanie/references/budowa-kodu/budowa-kodu.md`). Każdy krok: zielone testy przed, osobna
rewizja, zielone testy po. Naprawę przeplataj normalną pracą produktową w proporcji z rejestru długu
(sekcja 2) — projekt zamrożony „na czas wielkiego sprzątania” traci rację bytu szybciej, niż
odzyskuje strukturę.

**Krok 4 — strażnicy na przyszłość.** Po spłacie zasadniczej: opróżnij
listy wyjątków do zera i zablokuj ich rozrost, spisz dokument konwencji
(sekcja 5) na bazie decyzji podjętych w trakcie naprawy, zaplanuj pierwszy
przegląd kwartalny (sekcja 4) i wpisz go do kalendarza zespołu. Projekt,
który przeszedł procedurę bez kroku 4, wraca do stanu wyjściowego w dwa
kwartały.
