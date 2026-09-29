# Metoda debugowania — od objawu do przyczyny, przez pomiar

## Reguła zerowa: dosłowność

Zanim cokolwiek zrobisz, musisz mieć trzy rzeczy **dosłownie**, nie w parafrazie:

1. Pełny komunikat błędu ze śladem stosu (nie „coś z połączeniem”).
2. Dokładne polecenie / żądanie / kliknięcie, które go wywołało.
3. Środowisko: wersja runtime'u, system, gałąź i skrót commita, tryb (`dev`/`prod`).

Jeśli któregoś brakuje — **poproś o nie albo je zdobądź**. Nie zaczynaj od czytania kodu
i wymyślania, co mogło pójść nie tak. Komunikat błędu zawiera informację, której nie
odtworzysz z kodu: numer linii, wartość, nazwę pliku, kod błędu systemowego.

```bash
node -v && npm -v                       # runtime
git rev-parse --short HEAD && git status -sb
git log --oneline -5
cat .env.example                        # jakie zmienne są wymagane (nie .env)
```

Antywzorzec: „prawdopodobnie to problem z asynchronicznością” napisane przed
uruchomieniem czegokolwiek. To zdanie nie ma wartości informacyjnej i kieruje pracę
na losowy tor. Konsekwencja: zmieniasz działający kod, dokładasz drugi błąd, tracisz
punkt odniesienia.

---

## Krok 1. Odtworzenie błędu

Błąd nieodtworzony to błąd niezdiagnozowany. Naprawa bez odtworzenia jest zgadywaniem
i nie da się jej zweryfikować — po naprawie nie wiesz, czy błąd zniknął, czy tylko się
schował.

### Kolejność prób odtworzenia

| Próba | Co robisz | Kiedy przechodzisz dalej |
| --- | --- | --- |
| 1 | Uruchom dokładnie to, co uruchomił zgłaszający, w tym samym trybie | Błąd wystąpił → krok 2 |
| 2 | Wyrównaj środowisko: ten sam commit, ta sama wersja runtime'u, te same dane | Błąd wystąpił → krok 2 |
| 3 | Powtórz 20 razy — może być niedeterministyczny | Błąd wystąpił choć raz → sekcja „Błędy nieodtwarzalne” |
| 4 | Odtwórz na środowisku, gdzie występuje (staging/prod), a nie u siebie | Błąd wystąpił → krok 2, ale ostrożnie |

Po trzech nieudanych próbach **nie przechodź do naprawy**. Idź do sekcji „Błędy
nieodtwarzalne” albo do „Kiedy przestać”.

### Zapisz warunek odtworzenia jako polecenie

Docelowo chcesz mieć jedną linię, którą wklejasz i dostajesz błąd:

```bash
pytest tests/test_faktury.py::test_korekta_ujemna -x -q      # 0,4 s, pada
curl -sS -X POST localhost:3000/api/faktury -H 'content-type: application/json' \
  -d '{"kwota":-100}' -w '\n%{http_code}\n'                  # zwraca 500
```

Ta linia jest walutą całego procesu: pozwala mierzyć postęp minimalizacji i weryfikować
naprawę. Bez niej pracujesz na wrażeniach.

---

## Krok 2. Minimalizacja przypadku

Cel: najmniejszy zestaw danych i kodu, przy którym błąd nadal występuje. Przy okazji
minimalizacji przyczyna często ujawnia się sama.

### Procedura połowienia danych wejściowych

Masz plik/JSON/zapytanie, które wywala aplikację. Nie czytaj go — tnij:

1. Usuń drugą połowę wejścia. Błąd nadal jest? Zostaw tę wersję. Nie ma? Cofnij i usuń
   pierwszą połowę.
2. Powtórz na tym, co zostało.
3. Zatrzymaj się, gdy usunięcie czegokolwiek sprawia, że błąd znika.

Przy 10 000 wierszy CSV to około 14 kroków. Ręcznie to 5 minut, skryptem 20 sekund.

```python
# minimalizacja wejścia przez połowienie — działa dla list wierszy/rekordów
import subprocess, json, sys

def pada(wiersze: list[str]) -> bool:
    with open("/tmp/proba.csv", "w") as f:
        f.writelines(wiersze)
    r = subprocess.run(["python", "importer.py", "/tmp/proba.csv"], capture_output=True)
    return r.returncode != 0

def minimalizuj(wiersze: list[str]) -> list[str]:
    n = len(wiersze) // 2
    while n >= 1:
        i = 0
        while i < len(wiersze):
            kandydat = wiersze[:i] + wiersze[i + n:]
            if kandydat and pada(kandydat):
                wiersze = kandydat          # usunięcie nie uratowało — tnij dalej
            else:
                i += n
        n //= 2
    return wiersze

with open(sys.argv[1]) as f:
    naglowek, *reszta = f.readlines()
print("".join([naglowek] + minimalizuj(reszta)))
```

To jest `ddmin` (delta debugging). Dla wejść tekstowych sprawdza się też narzędzie
`creduce`/`shrinkray`, ale 30 linii powyżej wystarcza w 90% przypadków.

### Minimalizacja kodu

Ten sam ruch, tylko wycinasz warstwy:

- Wywołaj funkcję biznesową bezpośrednio, z pominięciem HTTP. Błąd nadal jest? Warstwa
  HTTP jest niewinna.
- Podstaw stałą zamiast wyniku zapytania do bazy. Błąd znika? Przyczyna jest w danych.
- Uruchom bez middleware/interceptorów. Błąd znika? To któryś z nich.

Zapisz, co odcięło błąd. To już jest połowa diagnozy.

---

## Krok 3. Ostatni działający stan

Pytanie „kiedy to działało?” jest tańsze niż pytanie „dlaczego to nie działa”.

### `git bisect` — pełna procedura

```bash
git bisect start
git bisect bad                       # obecny HEAD jest zły
git bisect good v1.4.2               # tag/commit, o którym wiesz, że działał
# git podaje commit do sprawdzenia; po każdym teście:
git bisect good   # lub: git bisect bad
git bisect reset                     # sprzątanie po zakończeniu
```

Automatyzacja — jedyna wersja, której powinieneś używać, gdy masz polecenie odtwarzające:

```bash
git bisect start HEAD v1.4.2
git bisect run bash -c 'npm ci --silent && npm test -- tests/faktury.test.ts'
```

Kody wyjścia dla `git bisect run`: `0` = dobry, `1–124` = zły, `125` = pomiń (nie da się
zbudować), `≥128` = przerwij bisekcję. Skrypt, który nie odróżnia „nie zbudowało się” od
„test padł”, da fałszywy wynik — zwracaj `125` przy błędzie budowania.

Pułapki:

- **Lockfile.** Przy skoku wstecz `node_modules` nie pasuje. Wstaw `npm ci` do skryptu.
- **Migracje bazy.** Bisekcja przez migracje wymaga świeżej bazy na każdym kroku
  (kontener na test) albo `git bisect skip` dla commitów migracyjnych.
- **Commity scalające.** `git bisect` radzi sobie z nimi, ale wynik może wskazać merge.
  Wtedy bisektuj wewnątrz gałęzi: `git bisect start HEAD <merge>^1`.

### Gdy `bisect` nie wchodzi w grę

```bash
git log -S 'nazwaFunkcji' --oneline -- src/            # kiedy pojawił się/zniknął ciąg
git log -G 'regexp' --oneline                          # zmiany pasujące do wyrażenia
git log --oneline -- path/do/pliku.ts                  # historia jednego pliku
git blame -L 40,60 src/faktury.ts                      # kto i kiedy dotknął tych linii
git diff v1.4.2..HEAD -- package-lock.json | head -100 # co się zmieniło w zależnościach
```

Gdy zmiana jest w zależnościach, nie w twoim kodzie:

```bash
npm ls nazwa-paczki          # która wersja jest naprawdę zainstalowana i przez kogo
npm why nazwa-paczki         # kto ją wciągnął
pip freeze > /tmp/teraz.txt && diff /tmp/dzialalo.txt /tmp/teraz.txt
```

Jeśli „nigdy nie działało” — pomiń krok 3, idź do 4. To ważny wynik: szukasz błędu
w projekcie, nie w regresji.

---

## Krok 4. Zawężanie przez połowienie ścieżki wykonania

Masz odcinek: **wejście poprawne** → ??? → **wyjście złe**. Wybierz punkt w połowie tego
odcinka i **zmierz** wartość. Nie zgaduj, w której połowie jest problem — sprawdź.

```
[wejście OK] ---- A ---- B ---- C ---- D ---- [wyjście złe]
                        ^ zmierz tutaj najpierw
```

Jeśli w B wartość jest już zła — problem jest między wejściem a B. Jeśli dobra — między
B a wyjściem. Każdy pomiar połowi przestrzeń poszukiwań. Ścieżka o 1000 kroków to
10 pomiarów.

### Co znaczy „zmierz”

W kolejności od najlepszego:

1. **Debugger z punktem wstrzymania** — widzisz cały stan, nie tylko to, co przewidziałeś.
2. **Log strukturalny z wartością** — gdy nie da się zatrzymać (produkcja, wyścig).
3. **Asercja** — `assert wynik.kwota > 0` w środku ścieżki; pada dokładnie tam, gdzie stan
   przestaje być poprawny.
4. **`print`/`console.log`** — najsłabsze, ale legalne. Zawsze z etykietą i wartością:
   `console.log('[po walidacji] kwota=', kwota, typeof kwota)`. Sam `console.log('tu')`
   mówi tylko, że kod dotarł — to najmniej użyteczna informacja.

Loguj **typ i reprezentację**, nie tylko wartość. `console.log(x)` dla `"0"` i `0`
wygląda podobnie; `console.log(x, typeof x, JSON.stringify(x))` już nie.

### Uzbrojenie debuggerów

```bash
# Node — zatrzymanie na pierwszej linii, podłączenie DevTools/VS Code
node --inspect-brk ./dist/serwer.js
NODE_OPTIONS='--inspect' npm run dev
node --stack-trace-limit=50 --trace-uncaught app.js
node --trace-warnings app.js            # źródło ostrzeżeń deprecacji i odrzuconych obietnic

# Python
python -X dev -X faulthandler skrypt.py # tryb deweloperski + zrzut stosu na SIGSEGV
PYTHONBREAKPOINT=pdb.set_trace python skrypt.py   # albo breakpoint() w kodzie
python -m pdb -c continue skrypt.py     # wejście do pdb dopiero na wyjątku
pytest --pdb -x                         # pdb w miejscu padnięcia testu
python -X importtime -c 'import app' 2>&1 | sort -k2 -n -r | head   # co spowalnia start
```

Punkty wstrzymania warunkowe są ważniejsze niż zwykłe: w pętli po 50 000 rekordach
zatrzymuj się na `if rekord.id == 8341`, a nie klikaj „dalej” 8341 razy.

---

## Krok 5. Czytanie śladu stosu

Ślad stosu czyta się **od góry**, ale interesuje cię **pierwsza ramka w twoim kodzie**.
Wszystko powyżej to biblioteka, która tylko zgłosiła objaw.

```
TypeError: Cannot read properties of undefined (reading 'nip')
    at formatujKontrahenta (/app/src/pdf/naglowek.ts:42:31)   <-- TU. Twój kod.
    at Array.map (<anonymous>)
    at renderujFakture (/app/src/pdf/faktura.ts:118:24)        <-- kto to wywołał
    at POST (/app/src/app/api/faktury/route.ts:57:20)          <-- skąd całość
```

Odczyt: w `naglowek.ts:42` odczytano `.nip` z `undefined`. To znaczy, że element tablicy
był `undefined`, a nie że `nip` był `undefined`. Różnica przesądza o miejscu naprawy:
błąd jest w tym, **kto zbudował tę tablicę** (`faktura.ts:118`), nie w formatowaniu.

### Rzeczy, które model przeocza w śladach

| Zjawisko | Co przeoczyć łatwo | Co zrobić |
| --- | --- | --- |
| Łańcuch przyczyn | `Caused by:` / `during handling of the above exception` — prawdziwa przyczyna jest w **ostatniej** sekcji | Czytaj cały ślad do końca, nie pierwsze 5 linii |
| Async w Node | Ślad urywa się na granicy `await`/callbacku | Node ≥ 22 ma async stack traces domyślnie; w starszym `--async-stack-traces` |
| Odrzucone obietnice | `UnhandledPromiseRejection` bez miejsca powstania | `process.on('unhandledRejection', (r) => { console.error(r); process.exit(1) })` |
| Zminifikowany kod | Nazwy typu `t.a is not a function` | Włącz source mapy: Next.js `productionBrowserSourceMaps: true`, Sentry — wgrywanie map przy budowaniu |
| Python | `raise X from Y` gubi kontekst przy `from None` | Nie używaj `from None` poza jawnym ukrywaniem szczegółów; loguj `exc_info=True` |
| Kod błędu systemowego | `ECONNREFUSED`, `EACCES`, `ENOSPC`, `EMFILE` niosą pełną diagnozę | Przetłumacz kod, zanim zaczniesz czytać kod aplikacji |

Najczęstsze kody i ich znaczenie: `ECONNREFUSED` — nic nie nasłuchuje na tym porcie
(usługa nie wstała albo zły port). `ETIMEDOUT` — pakiety giną (firewall, grupa
bezpieczeństwa, zła sieć). `ENOTFOUND` — DNS. `EACCES` na porcie <1024 — brak uprawnień.
`ENOSPC` przy `watch` — wyczerpany limit `inotify`. `EMFILE` — wyczerpane deskryptory
plików (`ulimit -n`). `ECONNRESET` — druga strona zerwała połączenie, zwykle timeout
u niej albo zabity proces.

---

## Krok 6. Hipoteza falsyfikowalna

Hipoteza to zdanie w formie:

> **Jeśli** przyczyną jest X, **to** pomiar M wykaże wartość W. Jeśli M pokaże co innego,
> hipoteza jest obalona.

Hipoteza bez części „jeśli M pokaże co innego” nie jest hipotezą, tylko przeczuciem.

| Zła (niefalsyfikowalna) | Dobra (falsyfikowalna) |
| --- | --- |
| „To pewnie problem z cachem” | „Jeśli przyczyną jest stary wpis w Redisie, to `redis-cli GET faktura:8341` zwróci dokument z `wersja: 2`, podczas gdy baza ma `wersja: 3`” |
| „Coś jest nie tak z konfiguracją” | „Jeśli przyczyną jest brak `DATABASE_URL` w kontenerze, to `docker exec app printenv DATABASE_URL` nic nie wypisze” |
| „Może to wyścig” | „Jeśli to wyścig przy zapisie, to uruchomienie testu z `--repeat-each=50` da co najmniej jedno padnięcie, a z blokadą mutex zero padnięć na 50” |
| „Biblioteka ma buga” | „Jeśli błąd jest w `zod@4.1.0`, to przypięcie `4.0.17` sprawi, że ten sam test przejdzie bez zmiany kodu” |

Reguła: **maksymalnie jedna hipoteza naraz i maksymalnie jedna zmiana na pomiar.**
Dwie zmiany naraz i nie wiesz, która zadziałała — a jedna z nich mogła coś popsuć.

Po trzech obalonych hipotezach z tej samej klasy zmień klasę. Klasy w kolejności, w jakiej
warto je przechodzić:

1. Dane wejściowe (kształt, kodowanie, wartości brzegowe, `null`, puste, ujemne).
2. Stan (baza, cache, sesja, plik, kolejność operacji).
3. Konfiguracja i środowisko (zmienne, wersje, uprawnienia, sieć, strefa czasowa).
4. Współbieżność i czas.
5. Kod biblioteki/frameworka (ostatnia klasa, nie pierwsza — statystycznie rzadko).

Model domyślnie zaczyna od klasy 5 („to bug w Next.js”). To odwrotna kolejność do
prawdopodobieństwa.

---

## Krok 7. Narzędzia pomiaru poza debuggerem

### Sieć i procesy

```bash
ss -tlnp                                 # co nasłuchuje na jakim porcie
lsof -p <pid> | wc -l                    # ile deskryptorów zajmuje proces
strace -f -p <pid> -e trace=network -s 200        # jakie wywołania sieciowe robi
strace -f -e trace=openat,stat ./app 2>&1 | grep -i config   # jakich plików szuka
ltrace -p <pid>                          # wywołania bibliotek współdzielonych
curl -sv --max-time 5 https://api.example.com/v1/x 2>&1 | head -40
dig +short api.example.com               # co naprawdę zwraca DNS
openssl s_client -connect host:443 -servername host </dev/null 2>&1 | head -20
```

`strace -f -e trace=openat` rozwiązuje całą klasę błędów „nie widzi mojego pliku
konfiguracyjnego” w jednym uruchomieniu: widzisz dokładną ścieżkę, której szukał proces.
Na macOS odpowiednikiem jest `dtruss` (wymaga wyłączenia SIP dla części przypadków);
w kontenerze `strace` wymaga `--cap-add=SYS_PTRACE`.

### Baza danych

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- rzeczywisty plan i liczba odczytów
SELECT query, calls, mean_exec_time, rows
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;
SELECT pid, state, wait_event_type, wait_event, query
FROM pg_stat_activity WHERE state <> 'idle';     -- co blokuje
SELECT * FROM pg_locks WHERE NOT granted;        -- kto czeka na blokadę
```

Trzy najczęstsze diagnozy z `EXPLAIN ANALYZE`: `Seq Scan` na dużej tabeli (brak indeksu),
rozjazd `rows=` szacowanych vs rzeczywistych o rząd wielkości (nieaktualne statystyki —
`ANALYZE tabela`), oraz zapytanie wykonane N razy zamiast raz (N+1, widoczne jako
`loops=N`).

### Przeglądarka

DevTools → Network: filtr po statusie, `Preserve log` przed przeładowaniem (inaczej
tracisz żądanie, które spowodowało przekierowanie). Sources → punkty wstrzymania na
zdarzeniu (`Event Listener Breakpoints`), na zmianie DOM (prawy przycisk na węźle →
Break on → subtree modifications), na żądaniu XHR pasującym do wzorca. `console.trace()`
w podejrzanym miejscu daje ślad wywołania bez zatrzymywania aplikacji.

Pełne pokrycie testów przeglądarkowych:
`references/engineering-core/07-debug-testy-deploy/references/testowanie-w-przegladarce.md`.

---

## Błędy nieodtwarzalne

„Czasami pada” to nie jest opis. Każdy taki błąd należy do jednej z poniższych klas
i każda ma swój test rozstrzygający.

| Klasa | Sygnał | Test rozstrzygający | Naprawa |
| --- | --- | --- | --- |
| **Wyścig** | Pada 1 na N uruchomień, częściej pod obciążeniem, znika przy dodaniu logu | `--repeat-each=50` (Playwright), `pytest-repeat -n 50`, sztuczne opóźnienie `setTimeout(…, 0)` w podejrzanym miejscu | Blokada, atomowy `UPDATE ... WHERE wersja = ?`, kolejka, `SELECT FOR UPDATE` |
| **Kolejność testów** | Pada tylko w pełnym zestawie, przechodzi w izolacji | `pytest -p randomly` / `vitest --sequence.shuffle`; potem `pytest --lf` na parze testów | Wyczyść stan globalny w `afterEach`; osobna baza/schemat na plik testowy |
| **Czas — granica okresu** | Pada na koniec miesiąca/roku, w nocy, przy zmianie czasu | Uruchom z zamrożonym zegarem na 2026-10-25T02:30, 2026-02-29, 2026-12-31T23:59 | Liczby dni z biblioteki dat, nie `+30*86400`; DST liczone w strefie, nie w UTC |
| **Strefa czasowa** | Wynik różni się o 1–2 h; działa u ciebie, nie u klienta | `TZ=Pacific/Kiritimati npm test` i `TZ=Pacific/Midway npm test` | Przechowuj UTC (`TIMESTAMPTZ`), konwertuj tylko przy wyświetlaniu; data biznesowa jako `DATE`, nie moment |
| **Cache** | Pierwszy raz działa, drugi nie (albo odwrotnie); znika po `rm -rf` | Usuń kolejno: `.next`, `node_modules/.cache`, `__pycache__`, cache CDN, cache przeglądarki (twarde przeładowanie) | Klucz cache zawierający wersję schematu; jawne unieważnianie przy zapisie |
| **Locale** | Sortowanie/parsowanie liczb różni się między maszynami | `LC_ALL=tr_TR.UTF-8` (słynne `i`/`İ`), `LC_NUMERIC=pl_PL.UTF-8` | `toLowerCase('en-US')` przy porównaniach technicznych; parsowanie liczb bez `parseFloat` na tekście lokalizowanym |
| **Zasoby** | Pada po godzinach działania, po dużym imporcie | `docker stats`, `ulimit -n`, `dmesg | grep -i oom` | Zamykanie połączeń/plików, strumieniowanie zamiast wczytywania całości |
| **Kolejność kluczy / niedeterminizm zbioru** | Test porównuje listy i czasem pada | Uruchom z `PYTHONHASHSEED=random` (Python domyślnie losuje) | Sortuj przed porównaniem albo porównuj zbiory |

Zasada nadrzędna: **przy błędzie nieodtwarzalnym najpierw zwiększ obserwowalność, potem szukaj
przyczyny.** Dołóż korelację żądań i log strukturalny w podejrzanej ścieżce
(`references/engineering-core/07-debug-testy-deploy/references/obserwowalnosc.md`), wypuść, poczekaj
na kolejne wystąpienie i przeczytaj dane zamiast zgadywać.

---

## „Działa lokalnie, nie działa na produkcji”

Lista w kolejności prawdopodobieństwa. Sprawdzaj od góry i **nie przeskakuj** — pierwsze
cztery pozycje odpowiadają za większość przypadków.

| # | Przyczyna | Polecenie sprawdzające |
| --- | --- | --- |
| 1 | Brakująca lub inna zmienna środowiskowa | `docker exec <c> printenv | sort` i porównanie z `.env.example`; w chmurze — panel zmiennych usługi |
| 2 | Inna wersja runtime'u / zależności (`node_modules` z cache, brak `npm ci`) | `docker exec <c> node -v`; `npm ls --prod --depth=0` w obrazie vs lokalnie |
| 3 | Migracja bazy niewykonana albo wykonana częściowo | `SELECT * FROM _prisma_migrations ORDER BY finished_at DESC LIMIT 5` / `alembic current` |
| 4 | Build produkcyjny robi coś innego niż dev (tree-shaking, minifikacja, `NODE_ENV`, wstępne renderowanie) | `npm run build && npm start` **lokalnie** — to pierwsze, co należy zrobić |
| 5 | Uprawnienia: pliki, katalog roboczy, użytkownik w kontenerze | `docker exec <c> id && ls -la /app/dane` |
| 6 | Sieć: usługa nieosiągalna, DNS wewnętrzny, reguły zapory, TLS | `docker exec <c> sh -c 'getent hosts db && nc -zv db 5432'` |
| 7 | Wielkość liter w nazwach plików (macOS/Windows nie rozróżnia, Linux tak) | `git ls-files | grep -i nazwaKomponentu` — czy import zgadza się co do znaku |
| 8 | Strefa czasowa i locale kontenera (zwykle UTC i `C`) | `docker exec <c> sh -c 'date && locale'` |
| 9 | Limity zasobów: pamięć kontenera, `ulimit`, limit czasu funkcji bezserwerowej | `docker stats`, log platformy z `OOMKilled` / `Task timed out` |
| 10 | Zimny start / stan współdzielony między instancjami (sesja w pamięci, cache lokalny) | Wyłącz jedną instancję; jeśli błąd znika — stan jest lokalny dla instancji |
| 11 | Nagłówki i pośrednicy: CDN, `X-Forwarded-Proto`, kompresja, limit rozmiaru ciała | `curl -sv` bezpośrednio do usługi z pominięciem CDN |
| 12 | Dane produkcyjne mają kształt, którego nie ma lokalnie (`NULL`, znaki spoza ASCII, rekordy z 2011) | Wyciągnij anonimizowaną próbkę tych rekordów i puść na nich test |

Krok 4 jest szczególny: **zawsze uruchom build produkcyjny lokalnie, zanim zaczniesz
diagnozować produkcję.** Połowa błędów „tylko na produkcji” odtwarza się po `npm run
build && npm start` i wtedy masz debugger zamiast logów.

---

## Krok 8. Naprawa przyczyny, nie objawu

Test przed napisaniem poprawki — odpowiedz na trzy pytania:

1. **Czy naprawa dotyka miejsca wskazanego przez pomiar?** Jeśli mierzyłeś, że tablica
   zawiera `undefined` w `faktura.ts:118`, a poprawiasz `naglowek.ts:42` przez `?.` —
   naprawiasz objaw. `undefined` pojedzie dalej i wywali się gdzie indziej.
2. **Czy potrafisz opisać przyczynę jednym zdaniem bez słowa „jakoś”?** „Zapytanie
   zwraca `LEFT JOIN` bez kontrahenta dla faktur anulowanych, a mapowanie zakłada, że
   kontrahent istnieje zawsze.”
3. **Czy ten sam błąd występuje w innym miejscu kodu?** `grep` po wzorcu. Jeśli wzorzec
   powtarza się w 5 miejscach, naprawa jednego to naprawa 20% błędu.

### Objaw vs przyczyna — katalog

| Poprawka objawowa | Co się stanie | Naprawa przyczyny |
| --- | --- | --- |
| `?.` / `try/except: pass` wokół miejsca wybuchu | Błąd wraca jako zły wynik zamiast wyjątku; trudniejszy do znalezienia | Znajdź, kto produkuje `null`, i albo napraw producenta, albo zadeklaruj `null` w typie i obsłuż świadomie |
| `setTimeout(…, 500)` „żeby zdążyło się załadować” | Pada na wolniejszej maszynie albo pod obciążeniem | Czekaj na warunek (`waitFor`, `await` na obietnicy), nie na czas |
| Zwiększenie limitu czasu / pamięci | Ukrywa wyciek albo N+1; wraca przy większej skali | Zmierz, co zjada czas/pamięć (`references/engineering-core/07-debug-testy-deploy/references/wydajnosc-i-profilowanie.md`) |
| `retry(3)` na losowo padającym żądaniu | Potraja obciążenie, maskuje przyczynę, zwielokrotnia skutki uboczne | Ustal, dlaczego pada; ponowienia zostaw dla błędów naprawdę przejściowych i z wykładniczym odstępem + idempotencją |
| Przypięcie starej wersji zależności bez zrozumienia | Zablokowany łańcuch aktualizacji, luka bezpieczeństwa | Przypnij tymczasowo **z komentarzem i linkiem do zgłoszenia**, załóż zadanie na odpięcie |
| Poprawka danych w bazie ręcznym `UPDATE` | Kod znowu je popsuje jutro | Napraw kod, potem jednorazowa migracja naprawcza z zapisem w historii |

Poprawka objawowa jest dopuszczalna **tylko** jako świadome działanie w trakcie awarii, z zapisanym
zadaniem naprawy właściwej — patrz
`references/engineering-core/07-debug-testy-deploy/references/awaria.md`.

---

## Krok 9. Test regresyjny

Obowiązkowa kolejność, bez skrótów:

1. Napisz test odtwarzający błąd.
2. **Uruchom go na kodzie sprzed naprawy — musi paść.** Test, który przechodzi przed
   naprawą, nie testuje niczego związanego z błędem.
3. Zastosuj naprawę.
4. Uruchom test — musi przejść.
5. Uruchom cały zestaw — nic innego nie może zacząć padać.

```bash
git stash                 # odłóż naprawę
npm test -- t/regresja.test.ts    # MUSI PAŚĆ; jeśli przechodzi — test jest bezwartościowy
git stash pop
npm test -- t/regresja.test.ts    # MUSI PRZEJŚĆ
npm test                          # cały zestaw
```

Test regresyjny nazywa się od zachowania, nie od numeru zgłoszenia:
`zwraca 422 gdy kwota korekty jest ujemna`, nie `test_bug_4471`. Numer zgłoszenia
w komentarzu, nie w nazwie — za rok nikt nie otworzy tego zgłoszenia.

---

## Krok 10. Kiedy przestać i poprosić o pomoc

Progi, po których dalsza samodzielna praca ma ujemną wartość oczekiwaną:

- **Trzy obalone hipotezy z różnych klas** i brak zawężenia obszaru.
- **60 minut bez odtworzenia** błędu w warunkach, w których powinien wystąpić.
- **Naprawa wymaga zmiany, której konsekwencji nie potrafisz opisać** (np. zmiana
  poziomu izolacji transakcji, podmiana wersji major frameworka).
- **Pojawia się pokusa zmiany czegoś „na wszelki wypadek”.** To sygnał, że skończyła się
  wiedza, a zaczęła się loteria.
- **Błąd dotyczy pieniędzy, danych osobowych albo bezpieczeństwa**, a przyczyna nie jest
  ustalona — eskaluj natychmiast, nie po godzinie.

Zgłoszenie o pomoc musi zawierać (inaczej rozmówca zacznie od kroku 1 za ciebie):

```markdown
## Objaw
<dosłowny komunikat + ślad stosu>

## Odtworzenie
<jedno polecenie; jeśli nie odtwarzam — częstotliwość i warunki>

## Środowisko
runtime, wersja, commit, tryb, środowisko

## Co już wykluczyłem
- hipoteza A — obalona pomiarem <M>, wynik <W>
- hipoteza B — obalona pomiarem <M>, wynik <W>

## Gdzie utknąłem
<najwęższy odcinek, do jakiego udało się zawęzić>
```

To nie jest formalność. Sama próba wypełnienia tego szablonu rozwiązuje część błędów,
bo wymusza nazwanie tego, co się wie, i tego, czego się nie wie.

---

## Antywzorce debugowania, które model popełnia najczęściej

| Antywzorzec | Konsekwencja | Zamiast tego |
| --- | --- | --- |
| Diagnoza z samego czytania kodu, bez uruchomienia | Trafienie w niewłaściwe miejsce; zmiana działającego kodu | Odtwórz, zmierz, potem czytaj kod w miejscu wskazanym przez pomiar |
| Kilka zmian naraz „żeby przyspieszyć” | Nie wiadomo, która pomogła; nowe błędy | Jedna zmiana na pomiar |
| Przepisanie modułu zamiast naprawy | Nowy kod = nowe błędy; utrata punktu odniesienia | Napraw punktowo, refaktor osobnym commitem po zielonych testach |
| „Naprawiłem, powinno działać” bez uruchomienia | Deklaracja gotowości bez pokrycia w faktach | Uruchom polecenie odtwarzające i pokaż wynik |
| Usuwanie komunikatu błędu zamiast błędu | Objaw znika, dane się psują cicho | Traktuj każdy `catch` bez logu jako usterkę |
| Ignorowanie ostrzeżeń z konsoli/budowania | Ostrzeżenie zwykle wskazuje przyczynę następnego błędu | Czytaj ostrzeżenia; w CI ustaw `--max-warnings 0` na krytycznych regułach |
| Debugowanie na produkcji przez „szybką poprawkę” | Brak wycofania, brak śladu, ryzyko drugiej awarii | Odtwórz lokalnie albo na staging; na produkcji tylko wycofanie i przełączniki funkcji |
