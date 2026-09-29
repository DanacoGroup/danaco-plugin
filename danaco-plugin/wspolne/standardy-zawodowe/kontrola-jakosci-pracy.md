# Kontrola jakości pracy przed przekazaniem

Karta opisuje zawodowy protokół samokontroli wykonywany po zakończeniu prac,
a przed przekazaniem wyniku właścicielowi projektu. Protokół wykonuj w podanej
kolejności; każdy krok kończy się rozstrzygnięciem „zgodne / niezgodne — poprawiono”.
Kontrola dotyczy stanu faktycznego plików i repozytorium, nie własnych intencji —
sprawdzaj poleceniami, nie pamięcią.

## 1. Czytanie własnego diffu na zimno

Diff czytaj tak, jak czytałby go obcy recenzent: bez wiedzy o przebiegu prac,
wyłącznie z tego, co widać. Kolejność przeglądu jest wiążąca — od zmian
najbardziej ryzykownych strukturalnie do najdrobniejszych.

Punkt wyjścia:

```
git status
git diff --stat
git diff
```

Bez repozytorium Git porównaj listing katalogu sprzed pracy (sporządzony na początku
zadania) z listingiem bieżącym: `find . -type f | sort` w obu punktach czasu i `diff`
obu list. Jeżeli listingu początkowego nie sporządzono — odnotuj to w raporcie jako
ograniczenie kontroli.

### 1a. Pliki nowe

Do każdego nowego pliku zadaj pytania:

- Czy właściciel projektu zamówił ten plik wprost albo czy wynika on wprost
  z zakresu zadania (nowy moduł z zadania, nowy test do nowej funkcji)?
- Czy plik nie jest opracowaniem obok kanonu (`NOTATKI.md`, `PODSUMOWANIE.md`,
  raport w formie pliku)?
- Czy plik nie jest artefaktem roboczym (zrzut danych, próbna baza, wynik pośredni)?
- Czy nazwa i położenie pliku są spójne z zastaną strukturą projektu?

Plik, który nie przechodzi tych pytań, usuń przed przekazaniem.

### 1b. Pliki usunięte

- Czy usunięcie było zamówione albo konieczne dla zadania?
- Czy nic nie odwołuje się do usuniętego pliku — importy, ścieżki w konfiguracji,
  odnośniki w dokumentacji? Sprawdź grepem po nazwie pliku bez rozszerzenia:
  `grep -rn "nazwa_pliku" --include="*.py" --include="*.md" .`
- Czy usunięcie testu nie jest wyciszeniem niezaliczonego testu (pozycja zakazana)?

### 1c. Pliki zmienione

Do każdego zmienionego fragmentu:

- Czy każda zmieniona linia służy zadaniu? Linie kosmetyczne (formatowanie,
  kolejność importów, zmiana nazw bez potrzeby) wycofaj: `git checkout -p -- plik`.
- Czy diff nie miesza naprawy z refaktoryzacją? Jeżeli miesza — rozdziel na dwie rewizje.
- Czy w dodanych liniach nie ma komentarzy-kronik, odwołań do rozmowy, wymyślonych
  kodów, TODO bez zgłoszenia?
- Czy zmiana sygnatury funkcji lub schematu została odzwierciedlona u wszystkich
  wywołujących? Sprawdź grepem po nazwie funkcji, nie pamięcią.

## 2. Lista kontrolna 7+1 — polecenia weryfikacyjne

Każdą zasadę rdzenia sprawdza konkretne polecenie na zmienionych plikach.
Poniższe wzorce wykonuj na zbiorze zmienionych plików (`git diff --name-only`);
przy zmianach rozległych — na całym katalogu źródłowym.

**Zasada 1 — historia w komentarzach.** Wyszukaj wzorce kroniki i dat w dodanych liniach:

```
git diff -U0 | grep "^+" | grep -nE "(zmieniono|poprawiono|wcześniej było|dodano [0-9]{4}|20[0-9]{2}-[0-9]{2}-[0-9]{2})"
git diff -U0 | grep "^+" | grep -nE "(zgodnie z ustaleniami|na prośbę|z rozmowy|z sesji)"
```

Trafienie w komentarzu lub treści trwałej = niezgodność. Trafienie w danych
(np. rzeczywista data w rekordzie testowym) oceń kontekstowo.

**Zasada 2 — wymyślone kody.** Wyszukaj wzorce pseudokodów w dodanych liniach:

```
git diff -U0 | grep "^+" | grep -nE "\[[A-Z]{1,4}[-/][0-9A-Za-z.]+\]|ETAP-[A-Z0-9]|FIX-[0-9]"
```

Każde trafienie skonfrontuj z rejestrem rzeczywistym: numer zgłoszenia projektu,
standard branżowy, kod platformy. Brak rejestru = usuń oznaczenie.

**Zasada 3 — spójność nazw.** Dla każdego pojęcia wprowadzonego lub przemianowanego
w zadaniu sprawdź, czy w projekcie nie funkcjonuje już inna nazwa:

```
grep -rniE "(walidat|sprawdzacz|verifier|validator)" --include="*.py" . | cut -d: -f3 | sort | uniq -c
```

(wzorzec dobierz do pojęcia). Więcej niż jedna nazwa tego samego pojęcia = niezgodność;
ujednolić albo — przy nazwach zastanych — zgłosić właścicielowi.

**Zasada 4 — dyscyplina plików.** Porównaj listę plików przed/po i policz różnicę:

```
git status --short
git diff --stat HEAD | tail -1
ls *.md
find . -name "*_v2*" -o -name "*_final*" -o -name "*.bak" -o -name "*kopia*"
```

Każdy nowy plik musi mieć uzasadnienie z kroku 1a. Wynik `find` musi być pusty.

**Zasada 5 — przyczyna źródłowa.** Odtwórz pierwotny błąd na wersji sprzed zmiany
(`git stash` lub gałąź), potwierdź jego wystąpienie, przywróć zmianę, potwierdź
ustąpienie. Sprawdź, czy naprawa nie polega na wyciszeniu:

```
git diff -U0 | grep "^+" | grep -nE "(except.*pass|catch\s*\([^)]*\)\s*\{\s*\}|@pytest\.mark\.skip|\.skip\(|xit\(|xdescribe\()"
```

**Zasada 6 — weryfikacja.** Czy w notatkach do raportu jest dosłowne polecenie
uruchomienia i dosłowny wynik? Jeżeli nie ma — uruchom teraz. Interfejsy zewnętrzne
użyte po raz pierwszy w tej zmianie: wskaż źródło, w którym sprawdzono sygnaturę.

**Zasada 7 — język.** Przejrzyj dodane treści trwałe pod kątem kolokwializmów i ozdobników:

```
git diff -U0 | grep "^+" | grep -nE "(ogarn|myk|magia|hack |XD|:\)|!{2,})"
git diff -U0 | grep "^+" | grep -P "[\x{1F300}-\x{1FAFF}\x{2700}-\x{27BF}]"
```

**Punkt 8 — sprzątnięcie środowiska.** Wykaż, że katalog przekazywany właścicielowi
nie zawiera artefaktów pracy:

```
find . -name "__pycache__" -o -name "*.pyc" -o -name ".pytest_cache" -o -name "*.tmp"
find . -newer /tmp/znacznik_poczatku -type f | grep -vE "(\.git/|oczekiwane_zmiany)"
git status --ignored --short
```

Próbne bazy danych, zrzuty, wyniki pośrednie, dzienniki uruchomień diagnostycznych —
usuń albo przenieś poza katalog projektu. Modele notorycznie zostawiają te pliki;
traktuj ten punkt jako obowiązkowy, nie opcjonalny.

## 3. Technika „świeżego klona”

Praca, która działa wyłącznie w środowisku, w którym powstała, nie jest ukończona.
Sprawdź, czy projekt zbuduje się i przejdzie testy na czystej maszynie:

1. Sklonuj repozytorium do katalogu tymczasowego: `git clone . /tmp/klon-kontrolny`
   (klon lokalny obejmuje wyłącznie treści zarejestrowane w Git — to jest istotą testu:
   plik istniejący tylko w katalogu roboczym ujawni się jako brak).
2. W klonie utwórz świeże środowisko zależności: `python -m venv .venv && .venv/bin/pip
   install -r requirements.txt` albo `npm ci` — zgodnie z ekosystemem projektu.
3. Uruchom budowę i testy dokładnie tak, jak opisuje to README projektu — nie
   poleceniami „które znasz”, lecz poleceniami udokumentowanymi. Rozjazd między
   README a rzeczywistością to usterka dokumentacji: napraw README w zakresie
   unieważnionym przez zmianę.
4. Klon i środowisko usuń po kontroli: `rm -rf /tmp/klon-kontrolny`.

Typowe usterki wykrywane wyłącznie tą techniką: zależność zainstalowana ręcznie,
lecz niewpisana do `requirements.txt`; plik konfiguracji obecny lokalnie, lecz
niezarejestrowany w Git; ścieżka bezwzględna z maszyny roboczej zaszyta w kodzie;
migracja bazy wykonana ręcznie z pominięciem skryptu migracyjnego.

Gdy pełny świeży klon jest w danym środowisku niewykonalny (brak zależności
systemowych, brak dostępu sieciowego), wykonaj wariant minimalny — `git stash
--include-untracked && <budowa/testy> && git stash pop` — i w raporcie nazwij
zakres, którego nie objęto.

## 4. Raport końcowy — zasady

Raport przekazuj w odpowiedzi tekstowej, nigdy w formie pliku w projekcie.
Struktura raportu:

1. **Co zmieniono** — wyliczenie plików ze ścieżkami i jednozdaniowym opisem
   zmiany w każdym.
2. **Weryfikacja** — dosłownie przytoczone polecenia i dosłownie przytoczone
   wyniki uruchomień. Nie parafrazuj wyników. Wzór:

   > Uruchomiono: `pytest tests/test_invoicing.py -q`
   > Wynik: `12 passed, 1 warning in 2.84s` (ostrzeżenie: przestarzałe wywołanie
   > `datetime.utcnow` w zależności, poza zakresem zmiany).

3. **Niezweryfikowane** — obowiązkowa sekcja, gdy cokolwiek pozostało niesprawdzone.
   Elementy niezweryfikowane nazywaj wprost i jednoznacznie; nie ukrywaj ich
   w przypisach ani nie osłabiaj („powinno działać”). Do każdego podaj przyczynę
   braku weryfikacji i sposób, w jaki właściciel może ją przeprowadzić.
4. **Poza zakresem** — zauważone usterki i propozycje nieobjęte zadaniem,
   po jednym zdaniu, bez wykonanej pracy.

Zakazy: żadnych deklaracji dojrzałości („gotowe do produkcji”, „w pełni
przetestowane”), żadnych ocen własnej pracy („elegancko”, „znacząco lepiej”),
żadnych wyników przybliżonych tam, gdzie dostępne są dokładne.

## 5. Wzorce rzetelnego przyznania niepewności

Rzetelne „nie zweryfikowano” jest zachowaniem zawodowym; fałszywe „działa” — nie.
Formuły do stosowania wprost:

- „Nie uruchomiono na środowisku produkcyjnym; zweryfikowano wyłącznie na SQLite,
  zapytanie zawiera składnię wspólną dla SQLite i PostgreSQL, lecz plan wykonania
  na PostgreSQL nie był badany.”
- „Sygnaturę `client.batch_send()` sprawdzono w dokumentacji biblioteki w wersji
  2.4; projekt deklaruje `>=2.0`, zgodności z wersjami 2.0–2.3 nie sprawdzono.”
- „Poprawka odtwarza i usuwa błąd dla danych z zgłoszenia #142; nie wykluczono
  innych ścieżek prowadzących do tego samego objawu.”
- „Test wymaga działającego serwera SMTP, niedostępnego w tym środowisku;
  test oznaczono pominięciem z przyczyną i numerem zgłoszenia, wymaga uruchomienia
  na środowisku przejściowym.”
- „Wpływu na wydajność nie zmierzono; ocena «bez istotnego wpływu» jest hipotezą
  opartą na niezmienionej złożoności, nie na pomiarze.”

Konstrukcja każdej formuły: co dokładnie sprawdzono → czego dokładnie nie
sprawdzono → dlaczego → jak można to sprawdzić. Unikaj zwrotów rozmywających:
„powinno być dobrze”, „raczej działa”, „wygląda poprawnie” — każdy z nich
zastąp jedną z formuł powyżej albo wykonaj brakującą weryfikację.
