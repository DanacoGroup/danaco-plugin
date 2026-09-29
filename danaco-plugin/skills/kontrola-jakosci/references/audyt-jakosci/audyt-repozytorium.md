# Audyt repozytorium — karta

Karta rozszerza etapy 1–3 procedury audytu o techniki badania repozytorium jako
materiału dowodowego. Repozytorium mówi więcej niż deklaracje zespołu: historia
zmian, drzewo zależności i struktura plików zapisują faktyczny przebieg prac.
Stosuj poniższe techniki w podanej kolejności; wyniki każdej z nich przytaczaj
w raporcie liczbowo, z poleceniem, które je wytworzyło.

## 1. Analiza historii Git jako źródła wiedzy

Historia Git jest jedynym obiektywnym zapisem tego, gdzie projekt naprawdę
koncentruje pracę i ryzyko. Zbadaj ją przed czytaniem kodu — wyniki wskażą,
które pliki dobrać jako próbki w etapie 3.

### 1.1 Churn plików — częstotliwość zmian

Policz, ile razy każdy plik był zmieniany w całej historii:

```
git log --format='' --name-only | sort | uniq -c | sort -rn | head -30
```

Dla okresu ograniczonego (np. ostatni rok — bardziej miarodajne w starych
projektach):

```
git log --since='12 months ago' --format='' --name-only | sort | uniq -c | sort -rn | head -30
```

Interpretacja:
- Wysoki churn pliku produkcyjnego to sygnał jednej z trzech przyczyn: plik jest
  naturalnym centrum domeny (akceptowalne), plik ma zbyt wiele odpowiedzialności
  (usterka struktury), albo plik jest wielokrotnie poprawiany, bo poprzednie
  poprawki nie usuwały przyczyny (usterka projektowa — patrz 1.3).
- Pliki konfiguracyjne i changelog naturalnie mają wysoki churn — odfiltruj je
  przed interpretacją, nie raportuj ich jako hotspotów.

### 1.2 Hotspoty — churn × rozmiar

Sam churn nie wystarcza: plik 40-liniowy zmieniany 80 razy jest mniej groźny niż
plik 2000-liniowy zmieniany 30 razy. Hotspot definiuj jako iloczyn liczby zmian
i rozmiaru pliku. Wyznacz go, łącząc wynik churn z rozmiarem:

```
git log --format='' --name-only | sort | uniq -c | sort -rn \
  | while read n f; do [ -f "$f" ] && echo "$((n * $(wc -l < "$f"))) $n $(wc -l < "$f") $f"; done \
  | sort -rn | head -20
```

Kolumny wyniku: iloczyn, liczba zmian, liczba linii, ścieżka. Pierwsze 5–10
pozycji to obowiązkowe próbki do etapu 3. W raporcie hotspoty prezentuj tabelą;
każdy hotspot bez pokrycia testami zgłoś jako ustalenie co najmniej istotne,
bo łączy trzy czynniki ryzyka: częste zmiany, duży rozmiar, brak siatki
bezpieczeństwa.

### 1.3 Poprawki wielokrotne tego samego pliku — sygnał usterki projektowej

Wyszukaj rewizje naprawcze i sprawdź, które pliki naprawiano wielokrotnie:

```
git log --format='%H %s' | grep -iE 'fix|naprawa|poprawka|hotfix|bug' | wc -l
git log --format='' --name-only --grep='fix' -i --regexp-ignore-case | sort | uniq -c | sort -rn | head -20
```

Plik naprawiany 5 i więcej razy w krótkim okresie to dowód, że poprawki leczą
objawy, nie przyczynę. Sprawdź wtedy dodatkowo, czy naprawy dotykają tych samych
linii:

```
git log -L :nazwaFunkcji:sciezka/do/pliku --oneline
```

Ustalenie formułuj jako usterkę projektową miejsca, nie jako listę pojedynczych
błędów: przyczyną powtarzających się napraw jest zwykle zbyt złożona funkcja,
brak testu regresyjnego albo niejasny kontrakt modułu.

### 1.4 Bus factor — wiedza skupiona w jednej osobie

Zmierz rozkład autorstwa:

```
git shortlog -sn --all
git shortlog -sn --all -- sciezka/do/katalogu
```

Drugie polecenie uruchom osobno dla każdego katalogu krytycznego
(uwierzytelnianie, płatności, rdzeń domeny). Interpretacja:
- Jeden autor odpowiada za ponad 80% zmian w module krytycznym → bus factor 1
  dla tego modułu; zgłoś jako ryzyko organizacyjne (utrata jednej osoby blokuje
  utrzymanie modułu). To ustalenie o strukturze wiedzy, nie o jakości pracy
  autora — sformułuj je tak wprost.
- Rozkład autorstwa porównaj ze stanem zatrudnienia: moduły, których jedyny
  znaczący autor już nie pracuje w zespole, oznacz jako „kod osierocony” i
  traktuj przy próbkowaniu jak kod obcy — czytaj uważniej.

### 1.5 Rytm i świeżość zmian

```
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
git log -1 --format='%ad' --date=short
```

Długie przerwy w historii, po których następują serie masowych zmian, wskazują
na prace zrywami bez ciągłego utrzymania — skoreluj to z wersjami zależności
(sekcja 2): projekt rozwijany zrywami niemal zawsze ma zaległości aktualizacyjne.

## 2. Analiza zależności

### 2.1 Drzewo zależności i wersje

Wygeneruj pełne drzewo i zapisz je jako materiał dowodowy:

```
npm ls --all                # Node.js
pip freeze                  # Python (środowisko)
pipdeptree                  # Python (drzewo)
mvn dependency:tree         # Java/Maven
go mod graph                # Go
```

Zbadaj trzy sprawy:

1. **Wersje porzucone i bez utrzymania.** Dla każdej zależności bezpośredniej
   sprawdź datę ostatniego wydania i status utrzymania (`npm view <pakiet> time`,
   strona projektu). Zależność bez wydania od ponad 2 lat w aktywnym ekosystemie
   oznacz do przeglądu; zależność oficjalnie porzuconą (deprecated, archiwum
   repozytorium) zgłoś jako ustalenie istotne, bo nie otrzyma poprawek
   bezpieczeństwa. Rozjazd wersji zainstalowanej względem bieżącej o więcej niż
   jedną wersję główną odnotuj z podaniem obu numerów.
2. **Duplikaty klas rozwiązań jako dowód dryfu.** Dwie biblioteki tej samej klasy
   w jednym projekcie (dwa klienty HTTP, dwie biblioteki dat, dwa frameworki
   formularzy, dwa ORM-y) to dowód dryfu technologicznego: kolejni autorzy
   dodawali własne przyzwyczajenia zamiast stosować przyjęte w projekcie.
   Wypisz pary duplikatów z liczbą miejsc użycia każdej
   (`grep -rc "from biblioteka" src/ | grep -v ':0'`); w planie naprawy wskaż,
   którą bibliotekę zostawić (zwykle tę z większą liczbą użyć lub lepszym
   utrzymaniem).
3. **Licencje.** Wygeneruj zestawienie (`npx license-checker --summary`,
   `pip-licenses`). Zależności na licencjach copyleft (GPL, AGPL) w produkcie
   własnościowym zgłoś jako ustalenie wymagające decyzji prawnej — audyt
   techniczny stwierdza obecność licencji, nie rozstrzyga jej skutków prawnych.

### 2.2 Audyt podatności

```
npm audit --omit=dev        # Node.js, tylko zależności produkcyjne
pip-audit                   # Python
```

Wyniki przytaczaj z podziałem na wagi zgłaszane przez narzędzie i z rozróżnieniem
zależności produkcyjnych od deweloperskich — podatność w narzędziu budowania ma
inny skutek niż w bibliotece serwera. Nie przepisuj wag narzędzia wprost do wag
ustaleń audytu: podatność krytyczna w funkcji, której projekt nie wywołuje,
pozostaje ustaleniem istotnym (do aktualizacji), nie krytycznym.

## 3. Wykrywanie kodu martwego

Kod martwy zawyża koszt utrzymania i maskuje rzeczywisty rozmiar projektu.
Badaj trzema technikami, od najtańszej:

1. **Eksporty bez importów** — narzędzia per ekosystem:
   - TypeScript/JavaScript: `npx knip` (nieużywane pliki, eksporty i zależności
     w jednym przebiegu) lub `npx ts-prune` (nieużywane eksporty TS).
   - Python: `vulture .` (nieużywane funkcje, klasy, zmienne; próg pewności
     ustaw `--min-confidence 80`, żeby ograniczyć fałszywe trafienia).
   - Wynik narzędzia zweryfikuj próbką ręczną: 5 losowych zgłoszeń sprawdź
     grepem po całym repozytorium, łącznie z konfiguracją i szablonami —
     narzędzia nie widzą wywołań dynamicznych (refleksja, rejestry wtyczek,
     nazwy w łańcuchach znaków).
2. **Moduły nieosiągalne** — pliki, do których nie prowadzi żaden import od
   punktów wejścia. `knip` wykrywa je w JS/TS; w innych ekosystemach zbuduj
   listę plików źródłowych i odejmij pliki osiągalne grepem po importach.
3. **Kod za martwymi flagami** — wyszukaj flagi funkcjonalne i sprawdź, które
   mają na stałe jedną wartość we wszystkich środowiskach; gałąź nigdy
   niewykonywana to kod martwy, choć narzędzia go nie zgłoszą.

W raporcie podaj skalę zjawiska (liczba plików/eksportów, szacunkowa liczba
linii), nie wyliczaj każdego przypadku — pełną listę załącz jako materiał
pomocniczy na życzenie.

## 4. Metryki złożoności z progami orientacyjnymi

Zmierz złożoność narzędziem, nie okiem:

```
radon cc -s -a src/                 # Python: złożoność cyklomatyczna
radon mi -s src/                    # Python: indeks utrzymywalności
npx eslint --rule '{"complexity": ["warn", 10]}' src/   # JS/TS
```

W ESLint stale skonfigurowanym w projekcie sprawdź, czy reguły `complexity`,
`max-lines-per-function`, `max-depth` są włączone — ich brak przy jednoczesnych
przekroczeniach to osobne ustalenie o procesie.

Progi orientacyjne (do przeglądu, nie do mechanicznego karania):

| Metryka | Bez uwag | Do przeglądu | Ustalenie |
|---|---|---|---|
| Złożoność cyklomatyczna funkcji | ≤ 10 | 11–20 | > 20 |
| Długość funkcji (linie logiczne) | ≤ 50 | 51–100 | > 100 |
| Głębokość zagnieżdżeń | ≤ 3 | 4 | ≥ 5 |
| Liczba parametrów funkcji | ≤ 4 | 5–6 | ≥ 7 |

Zasady interpretacji:
- Progi są orientacyjne: funkcja-dyspozytor (duży `switch` po typie zdarzenia)
  może mieć wysoką złożoność przy pełnej czytelności. Ustaleniem jest złożoność
  połączona z innym czynnikiem ryzyka: brakiem testów, wysokim churn (hotspot),
  położeniem w module krytycznym.
- Raportuj rozkład, nie tylko skrajności: „14% funkcji przekracza złożoność 10,
  mediana 4” mówi więcej niż lista dziesięciu najgorszych funkcji.
- Przecięcie zbiorów: funkcje jednocześnie w górnym decylu złożoności i w górnym
  decylu churn to pierwszorzędni kandydaci planu naprawy — refaktoryzacja tam
  zwraca się najszybciej.

## 5. Inwentaryzacja plików-narośli i kopii

Wyszukaj poleceniami, nie przeglądaniem drzewa:

```
find . -path ./node_modules -prune -o -type f \( \
  -name '*_v2*' -o -name '*_v3*' -o -name '*copy*' -o -name '*kopia*' \
  -o -name '*.bak' -o -name '*.old' -o -name '*_old*' -o -name '*_new*' \
  -o -name '*.orig' -o -name '*-final*' -o -name '*_backup*' -o -name '*.tmp' \
\) -print
find . -path ./node_modules -prune -o -type f -name '*.py' -size +100k -print
git ls-files --others --exclude-standard        # pliki poza kontrolą wersji
```

Dla każdego trafienia ustal grepem, czy plik jest gdziekolwiek importowany.
Kopia `_v2` używana równolegle z oryginałem to ustalenie poważniejsze niż kopia
martwa: oznacza, że dwie wersje tej samej logiki żyją jednocześnie i mogą się
rozjechać. Sprawdź też katalogi: `backup/`, `old/`, `archive/`, `temp/` w
drzewie źródeł. Duże pliki binarne w historii Git wykryj przez
`git rev-list --objects --all | sort -k2` w połączeniu z `git cat-file` — wpisz
do raportu tylko, gdy istotnie powiększają repozytorium.

## 6. Ocena testów — nie tylko pokryciem

Procent pokrycia to najsłabsza z miar jakości testów: mierzy wykonanie linii,
nie weryfikację zachowania. Badaj cztery warstwy:

1. **Czy testy przechodzą na czysto.** Uruchom cały zestaw dwukrotnie z rzędu
   i raz w losowej kolejności (`pytest -p randomly`, `pytest --random-order`;
   w Jest kolejność plików bywa zależna od cache — uruchom z `--runInBand` i
   porównaj). Testy zależne od kolejności (przechodzą razem, padają osobno lub
   po przetasowaniu) zgłoś jako ustalenie istotne: dzielą stan i nie weryfikują
   tego, co deklarują. Testy niestabilne (flaky — różny wynik przy identycznym
   kodzie) wypisz imiennie.
2. **Testy bez asercji.** Wyszukaj testy, które niczego nie sprawdzają:
   `grep -rL 'assert\|expect' tests/ --include='test_*.py'` (przybliżenie —
   zweryfikuj trafienia ręcznie). Test bez asercji podnosi pokrycie, nie
   podnosząc jakości; policz je i podaj odsetek.
3. **Pokrycie mutacyjne jako pojęcie kontrolne.** Narzędzie mutacyjne
   (`mutmut` dla Pythona, `Stryker` dla JS/TS) wprowadza drobne zmiany do kodu
   i sprawdza, czy testy je wykrywają; odsetek wykrytych mutantów mierzy realną
   siłę asercji. Pełny przebieg jest kosztowny — w audycie uruchom go wyłącznie
   na 2–3 modułach krytycznych i przytocz wynik jako sondę: wysokie pokrycie
   liniowe przy niskim pokryciu mutacyjnym to dowód testów pozornych.
4. **Struktura piramidy.** Policz testy według rodzaju (jednostkowe /
   integracyjne / end-to-end) i czas wykonania całości. Zestaw trwający tak
   długo, że zespół go omija, nie pełni funkcji ochronnej niezależnie od
   pokrycia — czas wykonania podaj w raporcie.

## 7. Ocena dokumentacji względem kodu

Dokumentację oceniaj wyłącznie próbą, nie lekturą:

1. **README kontra rzeczywiste kroki uruchomienia — próba na czysto.** Wykonaj
   instrukcję uruchomienia literalnie, w czystym środowisku (świeży klon,
   kontener lub nowy katalog wirtualnego środowiska), bez wiedzy spoza
   dokumentu. Zapisz każde odstępstwo: brakujący krok, niewymienioną zmienną
   środowiskową, wersję narzędzia inną niż zadeklarowana, sekret, którego
   dokument nie mówi skąd wziąć. Liczba odstępstw jest miarą rozjazdu
   dokumentacji z kodem; niepowodzenie uruchomienia według README to ustalenie
   istotne samo w sobie.
2. **Dokumentacja API kontra kod.** Porównaj wygenerowaną specyfikację
   (OpenAPI z FastAPI, eksport tras) z dokumentem ręcznym, jeśli istnieje;
   wypisz endpointy obecne tylko po jednej stronie.
3. **Świeżość.** Zestaw daty ostatnich zmian dokumentów
   (`git log -1 --format='%ad' -- README.md`) z datami zmian kodu, który
   opisują; dokument architektury nietknięty od dwóch lat przy kodzie zmienianym
   co tydzień opisuje najpewniej system, którego już nie ma — zweryfikuj próbką
   dwóch twierdzeń dokumentu przeciw kodowi.

## Minimalny komplet dowodów z tej karty

Do raportu audytu z badania repozytorium dołącz co najmniej: tabelę 10 hotspotów
(churn × rozmiar), rozkład autorstwa modułów krytycznych, wynik audytu
podatności z podziałem na wagi, listę duplikatów klas rozwiązań, skalę kodu
martwego, rozkład złożoności z odsetkiem przekroczeń progów, wynik podwójnego
i przetasowanego przebiegu testów oraz protokół próby uruchomienia według README
na czysto. Każdy element z poleceniem, które go wytworzył — audyt ma być
powtarzalny przez inną osobę.
