# Katalog degeneracji — mechanizmy rozkładu projektu

Projekt nie psuje się jednym złym commitem — psuje się serią małych ustępstw.
Katalog opisuje dwanaście mechanizmów rozkładu: jak postępują, po czym poznać
je wcześnie (poleceniami, nie wrażeniem) i późno, jak naprawić i zabezpieczyć
trwale. Progi liczbowe kalibruj do projektu, ale ich nie usuwaj.

## 1. Pączkowanie pliku (plik-bóg)

**Mechanizm.** Plik rośnie, bo „już jest otwarty”: każda kolejna funkcja
trafia tam, gdzie edytor akurat stoi. Po kilkunastu sesjach plik obsługuje
faktury, pocztę i walidację naraz; import wciąga wszystko, a każda zmiana
grozi regresją w obszarze niepowiązanym.

**Sygnały wczesne.**

```
find src -name '*.py' | xargs wc -l | sort -rn | head -10
git log --since='6 months ago' --name-only --pretty=format: | sort | uniq -c | sort -rn | head -10
```

Progi: > 400 linii — obserwuj; > 700 — zaplanuj podział; plik w czołówce
rozmiaru i zarazem częstości zmian — dziel w najbliższej iteracji. Sygnałem
jest też > 15 importowanych modułów oraz opis zawartości wymagający „oraz”.

**Sygnały późne.** Plik > 1500 linii; większość rewizji projektu dotyka
tego jednego pliku; nikt nie zmienia go bez „przeczytania całości”.

**Recepta.** 1) Zbuduj testy charakteryzujące obecne zachowanie
(`../kodowanie/references/budowa-kodu/budowa-kodu.md`). 2) Wypisz odpowiedzialności — każda grupa
funkcji ze swoimi danymi to kandydat na moduł. 3) Wydzielaj po jednej odpowiedzialności na rewizję:
przenieś, zaktualizuj odwołania, testy, zatwierdź. 4) Nie dziel mechanicznie („część 1 / część 2”) —
granicą jest odpowiedzialność. 5) Na końcu usuń martwe resztki pliku-źródła.

**Zabezpieczenie.** Skrypt w CI raportujący pliki powyżej progu (ostrzeżenie
od 400 linii, błąd od 900; progi w konfiguracji); reguła przeglądu: funkcja
dopisana do pliku spoza jej odpowiedzialności wraca do autora.

## 2. Katalog-wysypisko `utils`

**Mechanizm.** Powstaje katalog „na drobiazgi” (`utils/`, `helpers/`,
`common/`, `misc/`); trafia tam każda funkcja, której autor nie chce
klasyfikować. Importuje go wszystko, więc zmiana w nim potencjalnie psuje
cały projekt; nazwy (`utils2.py`) przestają znaczyć cokolwiek.

**Sygnały wczesne.**

```
find src -type d \( -name 'utils' -o -name 'helpers' -o -name 'common' -o -name 'misc' \)
grep -rl 'from .*utils import\|require(.*utils' src | wc -l
```

Progi: sam fakt istnienia — sygnał; > 5 plików w środku lub > 30% modułów
projektu importujących — działaj teraz.

**Sygnały późne.** `utils/` największym katalogiem projektu; zawiera logikę
domenową; istnieje `utils/utils.py`.

**Recepta.** 1) Dla każdej funkcji ustal wołających (`grep -rn 'nazwa' src`).
2) Wołaną z jednego modułu przenieś do niego. 3) Wołane z wielu pogrupuj do
modułów nazwanych po tym, co robią (`formatowanie_dat.py`, nie `utils.py`).
4) Niewołane usuń. 5) Kroki jako osobne rewizje z zielonymi testami; na
końcu usuń pusty katalog.

**Zabezpieczenie.** Test struktury w CI: budowa pada, gdy w drzewie istnieje
katalog z listy zakazanej (`utils`, `helpers`, `common`, `misc`, `temp`,
`inne`); konwencja zapisana w dokumencie konwencji projektu.

## 3. Dryf technologiczny — druga biblioteka tej samej klasy

**Mechanizm.** Projekt używa `httpx`; nowa sesja tego nie sprawdza i dodaje
`requests`. Odtąd są dwa sposoby robienia tego samego: dwie konfiguracje
limitów czasu, dwie obsługi błędów, dwa zestawy zależności do
aktualizowania. Dotyczy też walidacji, ORM, testów, dat.

**Sygnały wczesne.**

```
grep -E 'requests|httpx|aiohttp' pyproject.toml requirements*.txt
grep -E '"(axios|node-fetch|got|superagent)"' package.json
pip check ; npm ls --depth=0 2>&1 | grep -i 'extraneous\|missing'
```

Próg: dwie biblioteki tej samej klasy w manifeście bez ADR — incydent, nie
obserwacja. Sprawdzaj przy każdym dodaniu zależności.

**Sygnały późne.** Trzy sposoby wykonania zapytania HTTP; na pytanie
„którego używamy?” padają różne odpowiedzi.

**Recepta.** 1) Ustal rozwiązanie docelowe decyzją ADR
(`references/architektura/architektura.md`). 2) Policz użycia odchodzącej biblioteki
(`grep -rn 'import requests' src | wc -l`). 3) Migruj moduł po module,
każda migracja z testami jako osobna rewizja. 4) Po ostatniej usuń
bibliotekę z manifestu — nie zostawiaj „tymczasowo obu”: tymczasowość bez
daty końca jest trwała.

**Zabezpieczenie.** Lista rozwiązań przyjętych w dokumencie konwencji;
w przeglądzie nowa pozycja manifestu wymaga wskazania, czego projekt jeszcze
nie robi; reguła lint zakazująca importu biblioteki odchodzącej.

## 4. Wyciek stylów do logiki

**Mechanizm.** Zaczyna się od jednego `style="margin-top: 8px"` „na chwilę”;
kolejne sesje kopiują wzorzec. Wartości projektowe rozmnażają się jako
liczby magiczne; zmiana koloru marki wymaga przeszukania kodu.

**Sygnały wczesne.**

```
grep -rn 'style="' src --include='*.html' --include='*.tsx' | wc -l
grep -rn 'style={{' src --include='*.jsx' --include='*.tsx' | wc -l
grep -rnE '#[0-9a-fA-F]{3,8}\b' src --include='*.tsx' | grep -v 'tokens\|theme' | wc -l
```

Progi: > 0 w projekcie z systemem arkuszy — naprawa przy najbliższej pracy
nad plikiem; > 20 wystąpień — osobne zadanie porządkowe.

**Sygnały późne.** Ten sam kolor w pięciu odcieniach; komponenty sklejające
łańcuchy CSS z warunków; zmiana typografii dotyka kilkudziesięciu plików.

**Recepta.** 1) Załóż jedno źródło prawdy wartości (tokeny, zmienne CSS —
`../design-systemowy/references/dokumentacja-designu/dokumentacja-designu.md`). 2) Zmapuj wartości
zastane na tokeny; odcienie „prawie takie same” scal świadomie. 3) Przenoś style plik po pliku do
mechanizmu przyjętego w projekcie; styl zależny od stanu wyrażaj przełączaniem klas. 4) Plik =
osobna rewizja bez zmian zachowania.

**Zabezpieczenie.** Reguły lint w CI: `react/forbid-dom-props` (zakaz
`style`), stylelint `color-no-hex` poza plikiem tokenów; przegląd odrzuca
wartości liczbowe wyglądu poza systemem stylów.

## 5. Erozja granic warstw — import na skróty

**Mechanizm.** Widok potrzebuje danych „tylko do jednej tabelki”, więc
importuje repozytorium z pominięciem warstwy usług. Skrót działa, więc jest
kopiowany. Po kwartale graf importów jest kłębkiem: domena zna framework
HTTP, dostęp do danych mieszka w komponentach.

**Sygnały wczesne.**

```
lint-imports                                   # Python, kontrakty w .importlinter
npx depcruise src --config .dependency-cruiser.js   # JS/TS
grep -rn 'from app.repositories\|from app.db' src/app/widoki | head
```

Próg: pierwszy import łamiący kierunek zależności — moment reakcji; drugi
oznacza, że wzorzec już się kopiuje. Cykl importów — zawsze błąd budowy,
nigdy ostrzeżenie.

**Sygnały późne.** Cykle wymuszające importy wewnątrz funkcji; zmiana
schematu bazy psuje komponenty widoku; testy domeny nie ruszą bez bazy
i frameworka.

**Recepta.** 1) Narysuj graf faktyczny (`pydeps`, `depcruise --output-type
dot`) i porównaj z zamierzonym. 2) Spisz naruszenia, uszereguj od
najtańszych. 3) Dla każdego wprowadź przejście przez właściwą warstwę,
przepnij import, testy, rewizja. 4) Cykle rozcinaj wydzielając wspólną
zależność do modułu niższego poziomu.

**Zabezpieczenie.** `import-linter` (Python) lub `dependency-cruiser` (JS/TS)
z kontraktem warstw jako brama scalenia w CI; naruszenia zastane na liście
wyjątków z planem spłaty (karta `references/praktyki-produktowe/egzekwowanie-praktyk.md`).

## 6. Kopie plików `_v2` / `_stary`

**Mechanizm.** Zamiast refaktoryzować, autor kopiuje plik do `modul_v2.py`
i rozwija kopię „bezpiecznie obok”. Część odwołań wskazuje starą, część
nową; poprawki trafiają tylko do jednej. Kontrola wersji zostaje zdublowana
ręcznie i gorzej.

**Sygnały wczesne.**

```
find src -regextype posix-extended \
  -regex '.*(_v[0-9]+|_old|_stary|_new|_nowy|_kopia|_backup|_bak|\.orig)\.[a-z]+'
```

Próg: jedno trafienie = jeden incydent do naprawy w tej samej iteracji.

**Sygnały późne.** Trzy pokolenia modułu w drzewie; błąd naprawiony rok temu
wraca, bo działa stara kopia; nikt nie wie, która wersja jest „prawdziwa”.

**Recepta.** 1) Ustal wersję żywą po odwołaniach (`grep -rn 'modul_v2' src`).
2) Przenieś do niej brakujące poprawki z kopii (`diff modul.py
modul_v2.py`). 3) Przepnij wszystkie odwołania na jedną wersję. 4) Usuń
kopie — historia jest w git. 5) Nadaj wersji żywej nazwę właściwą, bez `_v2`.

**Zabezpieczenie.** Skrypt kontroli plików-narośli w CI (wzorce nazw jak
wyżej — budowa pada przy trafieniu); zasada w konwencjach: wariantowanie
plików wyłącznie gałęziami kontroli wersji.

## 7. Konfiguracja rozproszona

**Mechanizm.** Limit czasu wpisany wprost w trzech miejscach, adres usługi
w pięciu — każda wartość dodawana tam, gdzie była akurat potrzebna. Zmiana
środowiska wymaga polowania po kodzie.

**Sygnały wczesne.**

```
grep -rnE 'https?://[a-z0-9.-]+|localhost:[0-9]+' src | grep -v 'config\|settings' | wc -l
grep -rn 'timeout' src --include='*.py' | grep -E '= ?[0-9]+' | sort | uniq -c | sort -rn | head
```

Próg: ta sama wartość środowiskowa w ≥ 2 miejscach poza modułem
konfiguracji — scal natychmiast; sekret w kodzie — incydent bezpieczeństwa,
nie porządkowy.

**Sygnały późne.** Wdrożenie wymaga edycji plików źródłowych; środowisko
testowe uderza w produkcyjną usługę „bo adres był zaszyty”.

**Recepta.** 1) Zinwentaryzuj wartości poleceniami wyżej. 2) Wprowadź jeden
moduł konfiguracji z warstwami: domyślne → plik → zmienne środowiskowe
(`../kodowanie/references/budowa-kodu/jakosc-od-poczatku.md`). 3) Podmieniaj
wystąpienia na odczyt z konfiguracji, grupami, z testami. 4) Sekrety do
mechanizmu sekretów; ujawnione unieważnij.

**Zabezpieczenie.** Walidacja konfiguracji przy starcie (brak wartości =
odmowa startu z czytelnym komunikatem); skaner sekretów w CI (`gitleaks`);
reguła przeglądu: nowa stała środowiskowa wyłącznie przez moduł konfiguracji.

## 8. Duplikacja logiki przez kopiuj-wklej

**Mechanizm.** Funkcja liczy podatek poprawnie, więc jest kopiowana do
drugiego modułu „żeby nie ruszać zależności”. Kopie żyją osobno: poprawka
stawki trafia do jednej, druga liczy po staremu — błąd ujawnia się jako
niezgodność dwóch raportów.

**Sygnały wczesne.**

```
npx jscpd src --min-tokens 50 --threshold 3
pylint --disable=all --enable=duplicate-code src/
```

Progi: duplikacja > 3% linii projektu — zadanie porządkowe; klon > 30 linii
logiki domenowej — scalenie natychmiast. Duplikaty w testach oceniaj
łagodniej — czytelność testu bywa ważniejsza.

**Sygnały późne.** Ta sama poprawka zgłaszana wielokrotnie w różnych
miejscach; dwa moduły dają różne wyniki dla tych samych danych.

**Recepta.** 1) Potwierdź, że to duplikacja pojęcia, nie przypadkowe
podobieństwo — scalaj tylko kod zmieniający się z tych samych powodów.
2) Wybierz wersję poprawniejszą, pokryj testami. 3) Wydziel do modułu
nazwanego po odpowiedzialności. 4) Przepnij miejsca użycia, usuwając kopie;
przy zmianach ryzykownych jedna rewizja na miejsce użycia.

**Zabezpieczenie.** `jscpd` w CI z progiem procentowym; nawyk: przed
napisaniem logiki domenowej sprawdź, czy już istnieje
(`grep -rn 'nazwa_pojęcia' src`).

## 9. Testy gnijące — wyłączone i pomijane

**Mechanizm.** Test pada po niezwiązanej zmianie. Zamiast diagnozy —
`@pytest.mark.skip("naprawić później")` albo `it.skip(...)`. Zielony pasek
wraca, „później” nie nadchodzi; zestaw przestaje chronić dokładnie te
miejsca, które najczęściej się psują.

**Sygnały wczesne.**

```
grep -rn '@pytest.mark.skip\|@unittest.skip\|it.skip\|test.skip\|xit(\|describe.skip' tests src | wc -l
pytest -q 2>&1 | tail -1   # skipped/xfailed w podsumowaniu
```

Progi: skip bez wpisu w rejestrze długu z terminem — naruszenie; > 2%
testów pomijanych — wstrzymaj dopisywanie funkcji do czasu spłaty. Test
niestabilny (raz zielony, raz czerwony) to skip w poczekalni.

**Sygnały późne.** Dziesiątki pominięć z komentarzami sprzed roku; zestaw
„zielony”, ale awarie produkcyjne w obszarach formalnie pokrytych.

**Recepta.** 1) Zinwentaryzuj pominięcia. 2) Dla każdego rozstrzygnij: test zły (testuje szczegół
implementacji) → przepisz lub usuń świadomie; test dobry, kod zły → napraw kod
(`../kodowanie/references/debugowanie/debugowanie.md`); test niestabilny → usuń źródło
niedeterminizmu (czas, kolejność, sieć). Zakaz trzeciej opcji „niech wisi”. 3) Pominięcia
środowiskowe (np. wymaga GPU) oznaczaj warunkiem wykonywalnym, nie gołym skipem.

**Zabezpieczenie.** Raport liczby pominięć w CI z progiem twardym; `skip`
wolno dodać wyłącznie z odnośnikiem do zgłoszenia i datą; przegląd odrzuca
rewizję wyłączającą test zamiast naprawy przyczyny.

## 10. Zależności zamrożone ze strachu

**Mechanizm.** Aktualizacja kiedyś coś zepsuła, więc zapada niepisana
decyzja: nie dotykamy wersji. Różnica wersji rośnie, z nią koszt i ryzyko
skoku; łatki bezpieczeństwa nie wpływają. W końcu aktualizacja jednej
biblioteki wymaga aktualizacji wszystkiego naraz — czyli nigdy.

**Sygnały wczesne.**

```
pip list --outdated | wc -l ; npm outdated | wc -l
pip-audit ; npm audit --audit-level=high
git log -1 --format=%ci -- package-lock.json requirements*.txt poetry.lock
```

Progi: plik blokady bez zmian > 3 miesiące — zaplanuj przegląd; podatność
high/critical bez reakcji > 2 tygodnie — incydent; > 30% zależności
przestarzałych — dług do rejestru z planem.

**Sygnały późne.** Framework bez wsparcia producenta; nowe biblioteki nie
instalują się przez konflikty.

**Recepta.** 1) Odbuduj siatkę bezpieczeństwa: testy dymne przepływów
krytycznych. 2) Kolejność: łatki bezpieczeństwa → patch → minor → major,
pojedynczo, każda jako osobna rewizja z pełnym przebiegiem testów. 3) Major
z listą zmian łamiących czytaną przed, nie po. 4) Regresję po aktualizacji
diagnozuj — nie cofaj odruchowo na stałe.

**Zabezpieczenie.** Stały rytm aktualizacji (comiesięczne okno na patch
i minor); `pip-audit`/`npm audit` w CI; bot zależności (Renovate/Dependabot)
z automatycznym scalaniem patchy po zielonych testach.

## 11. Dokumentacja-fikcja

**Mechanizm.** Dokument opisuje system z chwili napisania; kod idzie dalej,
dokument stoi. Czytelnik wykonuje instrukcję z README, dostaje błąd i uczy
się ignorować dokumentację — odtąd nikt nie czyta i nikt nie aktualizuje.
Fikcja jest gorsza niż brak, bo uczy fałszu.

**Sygnały wczesne.**

```
git log -1 --format='%ci %h' -- README.md docs/
# odwołania do plików, których już nie ma
grep -oE '`[a-zA-Z0-9_/.-]+\.(py|ts|js|md)`' README.md docs/*.md | tr -d '`' | sort -u \
  | while read f; do [ -e "$f" ] || echo "MARTWE: $f"; done
```

Próg: instrukcja uruchomienia niedziałająca na czystej maszynie — naprawa
natychmiastowa; dokument kanoniczny bez zmian przez 2 kwartały żywego
rozwoju — przegląd.

**Sygnały późne.** Nowa osoba nie uruchomi projektu według README; dokumenty
opisują moduły usunięte rok temu; obowiązuje wiedza plemienna obok martwych
dokumentów.

**Recepta.** 1) Zredukuj zbiór do dokumentów kanonicznych
(`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`): README, architektura, ADR-y, runbook —
resztę usuń. 2) Przejdź instrukcję uruchomienia na czystym środowisku i popraw każdy krok, który
kłamie. 3) Usuń opisy szczegółów, które kod wyraża lepiej — dokumentuj decyzje i niezmienniki, nie
stan chwilowy.

**Zabezpieczenie.** Definicja ukończenia: zmiana łamiąca zachowanie opisane
w dokumencie kanonicznym aktualizuje dokument w tej samej rewizji; kontrola
martwych odwołań i łączy w CI (`lychee`, skrypt jak wyżej).

## 12. Commit-zlepek — wiele intencji w jednej rewizji

**Mechanizm.** Praca trwa cały dzień, na koniec jedno `git add -A`
i komunikat „poprawki”. Rewizja miesza funkcję, refaktoryzację, formatowanie
i pliki robocze: przegląd niewykonalny, `git bisect` wskaże zlepek zamiast
przyczyny, wycofanie jednej zmiany wycofuje pięć innych.

**Sygnały wczesne.**

```
git log --since='1 month ago' --shortstat --oneline | grep -E 'files? changed'
git log --since='1 month ago' --oneline | grep -icE 'wip|fix$|poprawki|zmiany|update'
```

Progi: rewizja > 20 plików lub > 600 linii poza wygenerowanymi —
podejrzana; komunikaty jednowyrazowe > 20% historii miesiąca — problem
procesu, nie jednostki.

**Sygnały późne.** `git bisect` bezużyteczny; wycofania ręcznym
wyskubywaniem; pliki robocze i sekrety w historii.

**Recepta.** 1) Historii opublikowanej nie przepisuj — naprawiaj praktykę
od dziś. 2) Dziel pracę intencjami: refaktoryzacja przygotowawcza → zmiana
właściwa → porządki, każda osobno (`git add -p` rozdziela zmiany już
zmieszane). 3) Komunikat opisuje intencję i skutek („Wydziel walidację NIP
do modułu domeny”), nie czynność („zmiany”). 4) Pliki robocze do
`.gitignore`, zanim powstaną.

**Zabezpieczenie.** Wzorzec komunikatu w dokumencie konwencji; kontrola
komunikatów w CI (commitlint lub skrypt formatu); przegląd odrzuca rewizje
wielointencyjne z prośbą o podział.

## Zasada wspólna

Każdy mechanizm ma ten sam cykl życia: pojedynczy przypadek → wzorzec kopiowany → norma projektu, a
koszt naprawy rośnie o rząd wielkości na każdym etapie. Mierz sygnały wczesne w stałym rytmie (karta
`references/praktyki-produktowe/egzekwowanie-praktyk.md`) i naprawiaj przypadek pojedynczy, zanim
zostanie wzorcem.
