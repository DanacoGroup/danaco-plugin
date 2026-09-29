# Debugowanie, testy, wdrożenia — przegląd modułu

Moduł obejmuje drabinę weryfikacji kodu: diagnozę usterki, strategię testów,
obserwowalność, wdrożenie i reakcję na awarię. Karty pogłębione wymienia tabela
„Mapa plików referencyjnych” poniżej, a wszystkie moduły `references/engineering-core/` —
`references/engineering-core/spis.md`. Poza modułem: procedura diagnostyczna paczki
w `references/debugowanie/debugowanie.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Model ma dwa domyślne odruchy, które ten moduł blokuje.

**Pierwszy: zgadywanie przyczyny.** Widzi komunikat błędu, czyta kod, wymyśla
prawdopodobne wyjaśnienie i naprawia to, co pasuje do wyjaśnienia. Trafia w objaw albo
w niewłaściwe miejsce, a przy okazji psuje działający kod.

**Drugi: deklarowanie gotowości bez uruchomienia.** Pisze „gotowe”, „zaimplementowałem”,
„powinno działać” o kodzie, którego nie wykonał, i o interfejsie, którego nie otworzył.

Jedna reguła zastępuje oba odruchy:

> **Odtworzenie → zawężenie → hipoteza falsyfikowalna → potwierdzenie POMIAREM →
> naprawa przyczyny → test regresyjny → uruchomienie.**

Żadnego kroku nie wolno pominąć. Żadna diagnoza nie liczy się bez pomiaru, który ją
potwierdził. Żadna deklaracja gotowości nie liczy się bez wyniku uruchomienia.

## Kiedy wczytać ten moduł

- Coś nie działa: wyjątek, ślad stosu, zły wynik, biała strona, 500, zawieszenie.
- „Działa lokalnie, nie działa na produkcji” albo „czasami pada”.
- Trzeba napisać testy, zaprojektować strategię testów albo naprawić migoczący zestaw.
- **Zbudowałeś albo zmieniłeś cokolwiek widocznego w przeglądarce** — samokontrola
  przed oddaniem jest obowiązkowa.
- Wdrożenie: lista kontrolna, migracja, przełączniki funkcji, wycofanie, CI/CD.
- Produkcja się zepsuła: ocena wagi, komunikacja, przywrócenie, analiza po incydencie.
- Logi, metryki, ślady, alarmy — projektowanie i naprawa.
- Coś działa wolno i trzeba ustalić dlaczego (profilowanie, testy obciążeniowe).

**Nie używaj gdy:** pytanie dotyczy podziału systemu na moduły, wyboru technologii albo
projektu API bez istniejącego błędu. To architektura, nie debugowanie.

## Granice

| Temat | Materiał właściwy |
| --- | --- |
| Granice modułów, wybór technologii, ADR, model danych, projekt API, dług techniczny | `../architektura-i-dokumentacja/references/engineering-core/przeglad.md` |
| Core Web Vitals, LCP/INP/CLS, rozmiar pakietu, obrazy, czcionki, SEO | `../kontrola-jakosci/references/audyt-jakosci/audyt-web.md` |
| Składnia i API Pythona, FastAPI, pandas, SQLAlchemy, ETL | `references/engineering-core/02-python-backend-dane/przeglad.md` |
| Składnia i API Next.js, TypeScript | `references/frameworki/nextjs.md` · `references/jezyki-programowania/javascript-typescript.md` (API React 19 i Prisma nie są w tym pluginie opisane) |

Podział: tam **piszesz kod**, tutaj **dowodzisz, że działa, i utrzymujesz go w działaniu**.
„Jak napisać ten komponent” — tam. „Dlaczego ten komponent rzuca wyjątkiem i jak to
sprawdzić” — tutaj.

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
| --- | --- | --- |
| `references/engineering-core/07-debug-testy-deploy/references/metoda-debugowania.md` | Pełna metoda: minimalizacja przypadku, `git bisect`, połowienie ścieżki, czytanie śladu stosu, hipotezy falsyfikowalne, `strace`/debuggery/`EXPLAIN`, błędy nieodtwarzalne (wyścigi, czas, strefa, kolejność testów, cache), „działa lokalnie a nie na produkcji” — 12 przyczyn w kolejności prawdopodobieństwa, kiedy przestać | Masz błąd i nie znasz przyczyny; błąd pojawia się losowo; działa u ciebie a nie na produkcji |
| `references/engineering-core/07-debug-testy-deploy/references/testowanie-w-przegladarce.md` | **Procedura samokontroli agenta w siedmiu krokach**; Playwright 1.62: konfiguracja, selektory, oczekiwanie zamiast `sleep`, przechwytywanie sieci i konsoli, `trace viewer`, zrzuty i migawki ARIA, uwierzytelnianie raz, równoległość, wiele przeglądarek, axe, agenty testowe | Zbudowałeś/zmieniłeś UI; piszesz testy e2e; test przeglądarkowy pada |
| `references/engineering-core/07-debug-testy-deploy/references/strategia-testow.md` | Co testować a czego nie, piramida i trofeum, jednostka jako pojęcie, atrapy i ich nadużywanie, integracyjne z `testcontainers`, kontraktowe, testy migracji, fabryki danych, determinizm, testy migoczące, pokrycie jako sygnał, budżety czasu zestawu | Projektujesz zestaw testów; zestaw jest wolny albo migocze; ktoś pyta o pokrycie |
| `references/engineering-core/07-debug-testy-deploy/references/obserwowalnosc.md` | Logi strukturalne i **lista danych, których NIGDY nie logować**, poziomy, korelacja żądań, cztery złote sygnały, RED/USE, kardynalność, OpenTelemetry (SDK 0.221 / semconv 1.43), próbkowanie po fakcie, Sentry v10, alarmy na objawy i budżet błędów, zmęczenie alarmowe, retencja i koszt | Trzeba zdiagnozować produkcję; projektujesz logi/metryki/alarmy; błąd nieodtwarzalny wymaga danych |
| `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md` | Lista kontrolna przed wydaniem, wersjonowanie i dziennik zmian, migracje rozszerz-przenieś-usuń, operacje blokujące w PostgreSQL, przełączniki funkcji, wdrożenia kroczące/niebiesko-zielone/kanarkowe, progi i procedura wycofania, sekrety i konfiguracja, etapy CI/CD i buforowanie, wdrożenie w piątek, testy dymne | Wdrażasz; planujesz migrację; budujesz potok CI/CD; trzeba wycofać wydanie |
| `references/engineering-core/07-debug-testy-deploy/references/awaria.md` | Ocena wagi A1–A4, role (dowodzący, operacyjny, komunikujący, protokolant), kolejność przywracania, zbieranie dowodów przed restartem, komunikaty do użytkowników, oś czasu, analiza bez szukania winnego, pięć „dlaczego”, wnioski wykonalne, szablon raportu, miary | Produkcja jest zepsuta teraz; piszesz raport po incydencie |
| `references/engineering-core/07-debug-testy-deploy/references/wydajnosc-i-profilowanie.md` | Kolejność szukania wąskiego gardła, profilowanie Node (`--cpu-prof`, `clinic`, pętla zdarzeń, pamięć), Python (`py-spy`, `scalene`), `pg_stat_statements` i `EXPLAIN ANALYZE`, N+1 z testem-budżetem, indeksy, pule, buforowanie i unieważnianie, k6 2.0 i Locust, budżety wydajnościowe w CI | Coś działa wolno; przed premierą albo szczytem ruchu; regresja wydajności |

| Skrypt | Do czego |
| --- | --- |
| `references/engineering-core/07-debug-testy-deploy/scripts/z_serwerem.py` | Uruchamia serwer(y), czeka na **rzeczywistą** gotowość HTTP, wykonuje polecenie, sprząta, a przy niewstaniu wypisuje wyjście serwera. Używaj zawsze zamiast `npm run dev &`. |
| `references/engineering-core/07-debug-testy-deploy/scripts/kontrola_strony.py` | Samokontrola, kroki trzeci i czwarty: przechodzi podane kroki w przeglądarce, zbiera błędy konsoli, wyjątki strony, odpowiedzi ≥ 400 i naruszenia axe; kod wyjścia 1 przy jakimkolwiek problemie. |

Uruchamiaj skrypty przez `--help`, nie wczytuj ich do kontekstu. Wczytuj **jeden do dwóch**
plików referencyjnych na zadanie.

---

## PROCEDURA DEBUGOWANIA

To jest serce tego modułu. Każdy krok ma **warunek przejścia**. Brak spełnionego warunku
oznacza powrót, nie skok naprzód.

### D0. Zbierz fakty — nie diagnozuj

Zdobądź dosłownie: (a) pełny komunikat ze śladem stosu, (b) polecenie/kliknięcie
wywołujące błąd, (c) środowisko (wersja runtime'u, commit, tryb `dev`/`prod`).

> **Przejście do D1:** masz wszystkie trzy. Brakuje któregoś — zdobądź je albo poproś.
> **Nie wolno** w tym kroku napisać zdania zaczynającego się od „prawdopodobnie”.

### D1. Odtwórz błąd

Uruchom. Nie czytaj kodu w poszukiwaniu wyjaśnienia — najpierw zobacz błąd na własne oczy.
Cel: jedna linia polecenia, która niezawodnie go wywołuje.

> **Przejście do D2:** błąd odtworzony.
> **Po 3 nieudanych próbach** (to samo polecenie, wyrównane środowisko, 20 powtórzeń):
> przejdź do gałęzi „błędy nieodtwarzalne” w `references/engineering-core/07-debug-testy-deploy/references/metoda-debugowania.md`.
> **Zakaz:** nie naprawiaj błędu, którego nie odtworzyłeś — nie będziesz mógł
> zweryfikować naprawy.

### D2. Zminimalizuj przypadek

Tnij wejście przez połowienie i odcinaj warstwy (bez HTTP, bez bazy, bez middleware).
Zapisz, co odcięło błąd — to już połowa diagnozy.

> **Przejście do D3:** usunięcie czegokolwiek sprawia, że błąd znika.

### D3. Ustal ostatni działający stan

`git bisect run` z poleceniem z D1. Gdy bisekcja nie wchodzi w grę: `git log -S`,
`git blame`, różnica pliku blokad zależności.

> **Przejście do D4:** znasz commit/wersję winowajcę **albo** stwierdzasz „to nigdy nie
> działało” (to też jest wynik — szukasz błędu w projekcie, nie regresji).

### D4. Zawężaj przez połowienie ścieżki

Masz odcinek `wejście poprawne → ??? → wyjście złe`. Zmierz wartość **w połowie**. Nie
zgaduj, po której stronie jest problem. Każdy pomiar połowi przestrzeń poszukiwań.
Loguj wartość **i typ**, nie samo „tu jestem”.

> **Przejście do D5:** masz jedną funkcję lub linię, gdzie wejście jest poprawne,
> a wyjście już złe.

### D5. Sformułuj hipotezę falsyfikowalną

Zapisz ją jawnie w formie: *„Jeśli przyczyną jest X, to pomiar M pokaże W. Jeśli M pokaże
co innego — hipoteza obalona.”*

> **Przejście do D6:** hipoteza zapisana i ma warunek obalenia.
> **Zakaz:** żadnej zmiany w kodzie przed D6.

### D6. Potwierdź hipotezę pomiarem

Wykonaj pomiar M. Jedna zmiana na jeden pomiar.

> **Hipoteza potwierdzona → D7.**
> **Hipoteza obalona → powrót do D4** z nową hipotezą.
> **Po 3 obalonych z tej samej klasy** zmień klasę hipotez w kolejności: dane wejściowe →
> stan → konfiguracja i środowisko → współbieżność i czas → kod biblioteki.
> Model domyślnie zaczyna od ostatniej klasy; to odwrotność prawdopodobieństwa.

### D7. Napraw przyczynę, nie objaw

Trzy pytania przed napisaniem poprawki: czy naprawa dotyka miejsca wskazanego przez
pomiar? czy opiszesz przyczynę jednym zdaniem bez słowa „jakoś”? czy ten sam wzorzec
występuje gdzie indziej (`grep`)?

> **Przejście do D8:** odpowiedź na wszystkie trzy jest twierdząca.
> `?.`, `try/except: pass`, `setTimeout`, podniesienie limitu czasu i `retry` **nie są
> naprawami przyczyny** — są dopuszczalne wyłącznie jako świadome obejście w trakcie
> awarii, z zapisanym zadaniem naprawy właściwej.

### D8. Test regresyjny — obowiązkowa kolejność

1. Napisz test odtwarzający błąd.
2. **Uruchom go na kodzie sprzed naprawy — musi paść.**
3. Zastosuj naprawę. 4. Uruchom test — musi przejść.

> **Przejście do D9:** test padł przed naprawą i przeszedł po niej. Test, który przechodzi
> także przed naprawą, nie testuje niczego — napisz go od nowa.

### D9. Uruchom całość

Pełny zestaw testów. Jeśli zmiana dotyczy interfejsu — **procedura samokontroli SK w przeglądarce**
(patrz niżej i w
`references/engineering-core/07-debug-testy-deploy/references/testowanie-w-przegladarce.md`).

> **Przejście do D10:** zestaw zielony, nic innego nie zaczęło padać, samokontrola bez
> błędów konsoli i odpowiedzi ≥ 400.

### D10. Zamknij pętlę

Jeden akapit: co było przyczyną, jak ją potwierdziłeś, co zmieniłeś, co zabezpiecza przed
nawrotem. Sprawdź `grep`-em, czy ten sam wzorzec nie siedzi w innych miejscach. Jeśli
błąd dotarł na produkcję — `references/engineering-core/07-debug-testy-deploy/references/awaria.md`.

---

## PROCEDURA SAMOKONTROLI (SK) — zanim powiesz „gotowe”

Obowiązkowa po każdej zmianie widocznej w przeglądarce.

1. **Krok 1.** Uruchom aplikację przez
   `references/engineering-core/07-debug-testy-deploy/scripts/z_serwerem.py` i potwierdź, że wstała.
2. **Krok 2.** Wypisz ścieżki: ekran zmieniany, pełny przepływ podstawowy, jedna ścieżka
   błędu, jeden widok z danymi z serwera.
3. **Krok 3.** Przejdź każdą **klikając**, zbierając błędy konsoli, wyjątki strony, odpowiedzi ≥ 400
   i zrzuty ekranu (`references/engineering-core/07-debug-testy-deploy/scripts/kontrola_strony.py`).
4. **Krok 4.** Bramka: **0 błędów konsoli, 0 wyjątków, 0 odpowiedzi ≥ 400** poza celowo
   testowanymi. Ostrzeżenia o kluczach React, `hydration mismatch`, 404 na czcionce —
   to usterki, nie szum.
5. **Krok 5.** Napraw znalezione, wróć do kroku 3. Pętla trwa do zielonej bramki.
6. **Krok 6.** Obejrzyj zrzuty w dwóch szerokościach (390 i 1440). Pusty kontener, tekst na
   tekście i przycisk poza ekranem nie generują błędu konsoli.
7. **Krok 7.** Dopiero teraz raportuj: które ścieżki przeszedłeś, co znalazłeś, co
   naprawiłeś, co zostawiłeś i dlaczego.

---

## Procedura wdrożeniowa (skrót)

1. Lista kontrolna przed wydaniem — pozycje blokujące w
   `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.
2. Migracja bazy według rozszerz-przenieś-usuń, jako **osobny krok przed** wdrożeniem
   kodu, nigdy przy starcie aplikacji.
3. Progi wycofania zapisane **liczbowo przed** wdrożeniem, z imieniem osoby obserwującej.
4. Wdrożenie kroczące lub kanarkowe; zmiana widoczna dla użytkownika — za przełącznikiem.
5. Testy dymne po wdrożeniu, w tym sprawdzenie, że wdrożony commit jest tym oczekiwanym.
6. Obserwacja 30 minut. Przekroczenie progu → wycofaj najpierw, diagnozuj potem.

## Wersje odniesienia (sierpień 2026)

| Narzędzie | Wersja | Uwaga istotna |
| --- | --- | --- |
| `@playwright/test` | 1.62.1 | agenty (planner/generator/healer) od 1.56 przez `npx playwright init-agents --loop=claude`; serwer MCP i CLI wbudowane od 1.62 (`npx playwright mcp`) |
| `playwright` (Python) | 1.62.0 | `pytest-playwright` 0.8.0 |
| Vitest | 4.1.10 | tryb przeglądarkowy stabilny, ale wymaga osobnego dostawcy `@vitest/browser-playwright`; `toMatchScreenshot`; reporter `basic` usunięty; Vitest 5 w wersji beta |
| pytest | 9.1.1 | |
| `@opentelemetry/api` / `sdk-node` | 1.9.1 / 0.221.0 | semantic conventions 1.43.0; konwencje GenAI wydzielone do osobnego repozytorium i wciąż zmienne |
| `opentelemetry-sdk` (Python) | 1.44.0 | `opentelemetry-instrument` + `opentelemetry-bootstrap -a install` |
| `@sentry/node` | 10.69.0 | `enableLogs` przeniesione z `_experiments` na najwyższy poziom; `hasTracingEnabled` → `hasSpansEnabled`; FID już nieraportowany (zastąpiony przez INP); od 10.4 adres IP tylko przy `sendDefaultPii: true` |
| `sentry-sdk` (Python) | 2.66.1 | |
| k6 | 2.0 | `ramping-arrival-rate` dla API; `thresholds` decydują o kodzie wyjścia |
| Locust | 2.46.3 | |
| `@axe-core/playwright` | 4.12.1 | wykrywa ok. 30–40% naruszeń WCAG — nie zastępuje sprawdzenia klawiaturą |

## Twarde reguły

1. **Nie diagnozujesz bez odtworzenia.** Naprawa błędu, którego nie widziałeś, jest
   nieweryfikowalna. Naruszenie: „naprawiasz” działający kod, a błąd zostaje.
2. **Nie naprawiasz bez pomiaru potwierdzającego hipotezę.** Naruszenie: trafiasz w objaw,
   błąd wraca w innym miejscu za tydzień.
3. **Jedna zmiana na jeden pomiar.** Naruszenie: nie wiesz, która zmiana pomogła, a która
   dołożyła nowy błąd.
4. **Nie mówisz „gotowe” bez uruchomienia.** Kod bez wykonania, UI bez otwarcia
   w przeglądarce, test bez uruchomienia — to nie jest wynik, to deklaracja.
5. **Test regresyjny musi paść przed naprawą.** Naruszenie: masz test, który nie chroni
   przed niczym, i fałszywe poczucie pokrycia.
6. **Zero `sleep`/`waitForTimeout` w testach.** Czekaj na warunek. Naruszenie: test migocze
   na wolniejszym CI, a zespół uczy się ignorować czerwone.
7. **Selektory po roli i tekście, nie po klasach CSS.** Naruszenie: testy padają przy
   zmianie stylu i przestają być uruchamiane.
8. **Nigdy nie logujesz haseł, tokenów, PESEL, e-maili, treści dokumentów.** Loguj po
   liście dozwolonej, nie zakazanej. Naruszenie: wyciek danych osobowych do systemu
   logów o szerszym dostępie i miesięcznej retencji.
9. **Migracja zgodna wstecz albo w trzech wdrożeniach** (rozszerz-przenieś-usuń).
   Naruszenie: stary kod na nowym schemacie pada w trakcie wdrożenia stopniowego.
10. **Progi wycofania ustalone przed wdrożeniem, liczbowo.** Naruszenie: decyzja
    podejmowana pod presją brzmi „poczekajmy jeszcze 10 minut” i awaria trwa godzinę.
11. **W awarii: przywrócenie przed diagnozą**, ale dowody zebrane **przed** restartem.
    Naruszenie: restart czyści jedyny ślad przyczyny.
12. **Nie optymalizujesz bez profilu.** Naruszenie: poprawiasz 5% ścieżki i tracisz
    czytelność; 80% problemów wydajnościowych siedzi w bazie.
13. **Nie dodajesz `retry` do migoczącego testu.** Ponowienie maskuje wyścig, który
    zobaczy użytkownik. Napraw albo usuń test.
14. **Nie testujesz obciążeniowo produkcji bez uzgodnienia.** To atak odmowy usługi na
    własną firmę.

## Antywzorce, które model popełnia najczęściej

| Antywzorzec | Co się dzieje | Zamiast tego |
| --- | --- | --- |
| „To prawdopodobnie problem z asynchronicznością” przed uruchomieniem czegokolwiek | Praca idzie w losowy tor; zmienia się działający kod | D0–D1: fakty, potem odtworzenie |
| Naprawa pierwszej rzeczy pasującej do komunikatu | Objaw znika, przyczyna zostaje | D4–D6: zawężenie i pomiar |
| Dodanie `?.` w miejscu wybuchu | `null` jedzie dalej i wybucha gdzie indziej, trudniej | Znajdź producenta `null` |
| `console.log('tu')` zamiast wartości i typu | Wiesz tylko, że kod dotarł — najmniej użyteczna informacja | `log('[po walidacji]', x, typeof x)` |
| „Zaimplementowałem, powinno działać” | Użytkownik dostaje białą stronę i błąd w konsoli | Procedura samokontroli w siedmiu krokach |
| Test e2e na walidację jednego pola | 500× droższy niż test jednostkowy o tej samej wartości | Przenieś test w dół piramidy |
| `waitForTimeout(2000)` po kliknięciu | Migotanie zależne od obciążenia maszyny | `await expect(loc).toBeVisible()` |
| `expect(await loc.textContent())` | Sprawdzenie jednorazowe, bez ponawiania | `await expect(loc).toHaveText(...)` |
| `retries: 2` jako odpowiedź na migotanie | Maskuje realny wyścig w kodzie produkcyjnym | Znajdź przyczynę migotania |
| Cel „100% pokrycia” | Testy trywialnego kodu, wyłączenia dla trudnego, wolny zestaw | Próg globalny 70–80%, rdzeń 90%, pokrycie różnicy |
| `log.info({ req })` | Do logu trafia `Authorization` i `Cookie` | Lista dozwolonych pól |
| Alarm „CPU > 80%” | Budzi bez powodu, milczy przy realnej awarii | Alarm na objaw u użytkownika (5xx, p95, powodzenie logowania) |
| Migracja przy starcie aplikacji | N instancji ściga się o blokadę; pętla restartów przy padnięciu | Osobny krok przed wdrożeniem kodu |
| Cache jako pierwsza odpowiedź na „wolno” | Niespójność i nowa klasa błędów bez zysku | Indeks → zapytanie → algorytm → dopiero cache |
| Restart produkcji przed zebraniem dowodów | Przyczyna nie do ustalenia; awaria wróci | 30 sekund na zrzut logów, metryk i stanu bazy |

## Kontrola przed oddaniem

Zanim uznasz zadanie za skończone:

- [ ] Błąd został **odtworzony**, a nie tylko opisany.
- [ ] Przyczyna potwierdzona **pomiarem**, nie rozumowaniem; potrafisz ją streścić
      jednym zdaniem bez słowa „jakoś”.
- [ ] Naprawa dotyczy miejsca wskazanego przez pomiar, nie miejsca wybuchu.
- [ ] Sprawdzono `grep`-em, czy ten sam wzorzec nie występuje gdzie indziej.
- [ ] Test regresyjny **padał przed** naprawą i **przechodzi po**.
- [ ] Pełny zestaw testów uruchomiony i zielony; nic nowego nie pada.
- [ ] Jeśli zmiana dotyczy UI: procedura SK przeszła z zerową liczbą błędów konsoli,
      wyjątków i odpowiedzi ≥ 400; zrzuty obejrzane w dwóch szerokościach.
- [ ] Żaden nowy log nie zawiera hasła, tokenu, PESEL, e-maila ani treści dokumentu.
- [ ] Jeśli zmiana idzie na produkcję: migracja zgodna wstecz, progi wycofania zapisane,
      testy dymne przygotowane.
- [ ] W raporcie podano, **co dokładnie uruchomiono i z jakim wynikiem** — polecenie
      i wynik, nie „przetestowałem”.
- [ ] Jeśli czegoś nie sprawdzono — napisane jawnie, wraz z powodem.

Ostatnie pytanie do samego siebie: **czy potrafisz pokazać wynik uruchomienia, który
dowodzi, że to działa?** Jeśli nie — zadanie nie jest skończone, niezależnie od tego,
jak dobrze wygląda kod.
