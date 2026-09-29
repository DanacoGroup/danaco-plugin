# Wydajność i profilowanie — mierz, zanim zoptymalizujesz

Wersje odniesienia (sierpień 2026): Node 22/24 LTS, Python 3.13/3.14, k6 **2.0**,
Locust **2.46.3**, `clinic`/`0x` dla Node, `py-spy` i `scalene` dla Pythona.

Granica z sąsiadem: wydajność strony w przeglądarce (LCP, INP, CLS, rozmiar pakietu, obrazy,
czcionki) należy do `../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`. Tutaj: serwer,
baza, procesy, profilowanie i testy obciążeniowe.

---

## Reguła: bez pomiaru nie ma optymalizacji

Trzy liczby przed jakąkolwiek zmianą:

1. **Ile jest teraz** (bazowa, powtarzalna, z percentylem — nie ze średniej).
2. **Ile ma być** (cel z uzasadnieniem biznesowym, nie „szybciej”).
3. **Gdzie idzie czas** (profil, nie przypuszczenie).

Bez punktu 3 optymalizacja jest zgadywaniem i statystycznie trafia w niewłaściwe miejsce.
Typowy rozkład w aplikacji webowej: 70–90% czasu żądania to oczekiwanie na I/O (baza,
HTTP), a nie obliczenia. Model domyślnie optymalizuje obliczenia — czyli pozostałe 10%.

Zasada Amdahla w praktyce: przyspieszenie dwukrotne fragmentu zajmującego 5% całości daje
2,5% zysku. Ten sam wysiłek włożony we fragment 60-procentowy daje 30%. Profil mówi,
który to fragment.

### Kolejność szukania

```
Żądanie wolne
  → Ile z tego to baza?            (log czasu zapytań, APM, ślad)
      tak → EXPLAIN ANALYZE, indeksy, N+1
      nie ↓
  → Ile to wywołania zewnętrzne?   (ślad, metryki klienta HTTP)
      tak → równolegle zamiast sekwencyjnie, cache, limit czasu
      nie ↓
  → Ile to CPU aplikacji?          (profil próbkujący)
      tak → profil płomieniowy, algorytm, serializacja
      nie ↓
  → Ile to oczekiwanie na zasób?   (pula połączeń, kolejka, GC, blokady)
```

Ponad 80% realnych problemów wydajnościowych kończy się na pierwszym kroku.

---

## Profilowanie w Node

### Profil CPU

```bash
# 1. Wbudowany profiler — bez dodatkowych paczek
node --cpu-prof --cpu-prof-dir=./profile dist/serwer.js
# zatrzymaj proces, otwórz plik .cpuprofile w DevTools (chrome://inspect → Load profile)

# 2. Wykres płomieniowy jedną komendą
npx 0x -- node dist/serwer.js          # generuje interaktywny flamegraph HTML

# 3. Diagnostyka „co to za rodzaj problemu"
npx clinic doctor -- node dist/serwer.js     # wskazuje: CPU / I/O / GC / pętla zdarzeń
npx clinic flame -- node dist/serwer.js
npx clinic bubbleprof -- node dist/serwer.js # wizualizacja opóźnień asynchronicznych
```

Czytanie wykresu płomieniowego: **szerokość = czas, wysokość = głębokość stosu**. Szukasz
szerokich płaskowyżów. Wysoki, wąski stos jest nieszkodliwy. Funkcja szeroka i płytka to
najlepszy kandydat do naprawy.

### Blokowanie pętli zdarzeń

Najczęstszy problem wydajnościowy w Node i najtrudniejszy do zauważenia: jedno
synchroniczne wywołanie blokuje **wszystkie** żądania.

```ts
import { monitorEventLoopDelay } from 'node:perf_hooks';
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();
setInterval(() => {
  console.log('opóźnienie pętli p99 ms:', (h.percentile(99) / 1e6).toFixed(1));
  h.reset();
}, 10_000);
```

Wartość p99 powyżej 100 ms oznacza, że coś blokuje. Typowi winowajcy: `JSON.parse`
na wielomegabajtowym ciele, `crypto.pbkdf2Sync`/`bcrypt` synchronicznie, `fs.readFileSync`
w obsłudze żądania, wyrażenie regularne z nawrotami wykładniczymi (ReDoS), pętla po
100 tys. elementów.

Rozwiązania w kolejności: wariant asynchroniczny → `worker_threads` dla CPU → strumień
zamiast wczytania całości → przeniesienie do zadania w tle.

### Pamięć i wycieki

```bash
node --heapsnapshot-signal=SIGUSR2 dist/serwer.js
kill -SIGUSR2 <pid>        # zrzut przed obciążeniem
# ...obciąż aplikację...
kill -SIGUSR2 <pid>        # zrzut po
# porównaj w DevTools → Memory → Comparison; szukaj rosnących liczników obiektów
```

```ts
setInterval(() => {
  const m = process.memoryUsage();
  log.info({ rss: m.rss, heapUsed: m.heapUsed, external: m.external }, 'pamięć');
}, 30_000);
```

Wyciek rozpoznajesz po tym, że `heapUsed` rośnie monotonicznie **po** zakończeniu
obciążenia i po pełnym GC. Najczęstsze przyczyny: nasłuchiwacze zdarzeń dodawane bez
usuwania (`MaxListenersExceededWarning` to sygnał), cache bez limitu i bez wygasania,
domknięcia trzymające duże obiekty, globalna tablica „na wszelki wypadek”, timery bez
`clearInterval`.

---

## Profilowanie w Pythonie

```bash
# py-spy — próbkuje DZIAŁAJĄCY proces, także produkcyjny, bez restartu i bez narzutu kodu
py-spy top --pid 1234
py-spy record -o profil.svg --pid 1234 --duration 60      # wykres płomieniowy
py-spy dump --pid 1234                                     # stosy wszystkich wątków TERAZ

# scalene — CPU + pamięć + GPU, rozróżnia czas w Pythonie od czasu w kodzie natywnym
scalene --html --outfile profil.html skrypt.py

# wbudowane, dla skryptów
python -X importtime -c 'import app' 2>&1 | sort -k2 -nr | head -20   # wolny start
python -m cProfile -o profil.out skrypt.py && python -m pstats profil.out
```

`py-spy dump` jest najszybszą diagnozą zawieszonego procesu: pokazuje, w której linii
utknął każdy wątek. Zadziała bez przygotowania, na produkcji, w kontenerze (wymaga
`--cap-add=SYS_PTRACE`).

Pomiar punktowy:

```python
import time, contextlib

@contextlib.contextmanager
def zmierz(nazwa: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        log.info("czas", extra={"etap": nazwa, "ms": (time.perf_counter() - start) * 1000})

with zmierz("pobranie_faktur"):
    faktury = repo.pobierz(rok=2026)
with zmierz("generowanie_pdf"):
    pdf = zloz(faktury)
```

`time.perf_counter()`, nie `time.time()` — ten drugi może cofnąć się przy synchronizacji
NTP i dać ujemne czasy.

---

## Profilowanie w przeglądarce (część serwerowa problemu)

DevTools → Performance: nagraj interakcję, szukaj **długich zadań** (>50 ms, oznaczone
czerwonym trójkątem) — blokują reakcję na wejście użytkownika.

DevTools → Network: kolumna **Waterfall**. Szukasz łańcuchów sekwencyjnych — żądanie
czekające na poprzednie, które czekało na jeszcze wcześniejsze. To zwykle problem
architektury pobierania danych, nie sieci.

```js
performance.mark('start-tabeli');
// ...render...
performance.mark('koniec-tabeli');
performance.measure('render-tabeli', 'start-tabeli', 'koniec-tabeli');
console.table(performance.getEntriesByType('measure'));
```

Metryki użytkownika i Core Web Vitals: `../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`.

---

## Wąskie gardła bazy danych

To pierwsze miejsce do sprawdzenia i najczęstsza przyczyna.

### Znajdowanie kosztownych zapytań

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- największy sumaryczny koszt: zapytanie szybkie, ale wykonywane 100 tys. razy
-- bywa gorsze niż jedno wolne
SELECT calls, round(total_exec_time) AS suma_ms, round(mean_exec_time, 2) AS srednia_ms,
       rows, left(query, 120) AS zapytanie
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;

-- zapytania czekające na blokady
SELECT pid, state, wait_event_type, wait_event, now()-query_start AS trwa, left(query,100)
FROM pg_stat_activity WHERE state <> 'idle' ORDER BY query_start;

-- indeksy nigdy nieużywane (kosztują przy każdym zapisie)
SELECT relname, indexrelname, idx_scan FROM pg_stat_user_indexes
WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC;
```

Sortuj po `total_exec_time`, nie po `mean_exec_time`. Zapytanie trwające 3 ms wykonywane
50 000 razy na żądanie (N+1) nie pojawi się w rankingu średnich, a zjada całą wydajność.

### Czytanie `EXPLAIN (ANALYZE, BUFFERS)`

| Co widzisz | Znaczenie | Działanie |
| --- | --- | --- |
| `Seq Scan` na dużej tabeli z filtrem | brak indeksu albo niesarżowalny warunek | indeks; unikaj `WHERE lower(x)=...` bez indeksu funkcyjnego |
| `rows=100` (szacunek) vs `actual rows=50000` | nieaktualne statystyki | `ANALYZE tabela;`, rozważ `ALTER TABLE ... SET STATISTICS` |
| `loops=200` na węźle | N+1 wykonań | `JOIN` albo pobranie wsadowe |
| `Nested Loop` z dużymi wejściami | zły plan złączenia | statystyki, indeks na kluczu złączenia |
| `Sort` z `Sort Method: external merge Disk` | sortowanie nie mieści się w pamięci | `work_mem`, indeks pokrywający `ORDER BY` |
| `Heap Fetches` wysokie przy `Index Only Scan` | tabela wymaga odkurzenia | `VACUUM`, autovacuum |
| `Filter: ...` odrzucający większość wierszy | indeks nie pokrywa warunku | indeks złożony w kolejności: równość, `IN`, zakres, sortowanie |

### N+1 — najczęstszy pojedynczy błąd wydajnościowy

```ts
// ŹLE: 1 + N zapytań
const faktury = await db.faktura.findMany({ where: { rok: 2026 } });
for (const f of faktury) {
  f.kontrahent = await db.kontrahent.findUnique({ where: { id: f.kontrahentId } });
}

// DOBRZE: 1 zapytanie
const faktury = await db.faktura.findMany({
  where: { rok: 2026 },
  include: { kontrahent: true },
});
```

Wykrywanie automatyczne, zanim trafi na produkcję: policz zapytania w teście
integracyjnym i ustaw budżet.

```ts
it('lista faktur wykonuje najwyżej 3 zapytania', async () => {
  const zapytania: string[] = [];
  db.$on('query', (e) => zapytania.push(e.query));
  await pobierzListeFaktur({ rok: 2026 });         // 50 faktur w bazie testowej
  expect(zapytania.length).toBeLessThanOrEqual(3);
});
```

Ten test wyłapuje N+1 przy pierwszym wprowadzeniu, kiedy naprawa kosztuje minutę.
Po wdrożeniu ten sam błąd kosztuje incydent.

### Indeksy — reguły praktyczne

- Kolejność kolumn w indeksie złożonym: **równość → `IN` → zakres → sortowanie**.
  Indeks `(rok, kontrahent_id)` obsłuży `WHERE rok=2026 AND kontrahent_id=5`
  i `WHERE rok=2026`, ale nie samo `WHERE kontrahent_id=5`.
- Indeks częściowy dla zapytań z tym samym filtrem:
  `CREATE INDEX ... ON faktury (data) WHERE status='wystawiona'` — mniejszy i szybszy.
- Każdy indeks spowalnia `INSERT`/`UPDATE` i zajmuje miejsce. Usuwaj nieużywane
  (zapytanie wyżej).
- `CREATE INDEX CONCURRENTLY` na produkcji, zawsze — patrz
  `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.

### Pula połączeń

```
rozmiar puli ≈ liczba rdzeni bazy × 2 + liczba dysków
```

Większa pula nie znaczy szybciej: przy 500 połączeniach PostgreSQL spędza czas na
przełączaniu kontekstu. Typowo 10–30 połączeń na instancję aplikacji, z pgBouncerem
przed bazą, gdy instancji jest wiele.

Metryka wykorzystania puli jest obowiązkowa
(`references/engineering-core/07-debug-testy-deploy/references/obserwowalnosc.md`) — wyczerpanie
puli objawia się jako „wszystko wolne”, a przyczyna jest niewidoczna w profilu aplikacji.

---

## Buforowanie

Cache jest ostatnim narzędziem, nie pierwszym. Najpierw indeks, zapytanie, algorytm.
Cache dodaje niespójność, klasę trudnych błędów i koszt operacyjny.

### Poziomy

| Poziom | Czas życia | Zastosowanie | Ryzyko |
| --- | --- | --- | --- |
| Pamięć procesu | sekundy–minuty | konfiguracja, słowniki, wyniki obliczeń | niespójność między instancjami |
| Redis / współdzielony | minuty–godziny | sesje, wyniki zapytań, ograniczanie tempa | dodatkowa awaryjność, koszt sieci |
| HTTP / CDN | minuty–dni | zasoby statyczne, odpowiedzi publiczne | trudne unieważnienie na brzegu |
| Przeglądarka | wg nagłówków | zasoby z odciskiem w nazwie | najtrudniejsze do unieważnienia |
| Baza (widoki zmaterializowane) | minuty–godziny | ciężkie agregaty raportowe | odświeżanie blokuje albo jest kosztowne |

### Unieważnianie

Trzy strategie, w kolejności niezawodności:

1. **Wygasanie czasowe (TTL)** — najprostsze i najbezpieczniejsze. Dane nieaktualne przez
   najwyżej TTL. Domyślny wybór.
2. **Unieważnianie przy zapisie** — świeże dane, ale wymaga znajomości wszystkich kluczy
   zależnych od zmienionej encji. Zapomniany klucz = trwale nieaktualne dane.
3. **Klucz zawierający wersję** — `faktura:8341:v17`, gdzie `v17` to `updated_at` albo
   licznik wersji. Stary wpis nie jest czytany i wygasa sam. Najlepszy kompromis dla
   danych zmiennych.

```ts
const klucz = `faktura:${id}:${faktura.updatedAt.getTime()}`;
```

Zasada: **cache nie może być źródłem prawdy.** Wyczyszczenie całego cache musi być
bezpieczne — spowoduje chwilowe obciążenie, nie utratę danych ani błędne wyniki.

### Nagłówki HTTP

```
Cache-Control: public, max-age=31536000, immutable      # zasób z odciskiem w nazwie
Cache-Control: private, no-cache                        # odpowiedź per użytkownik
Cache-Control: public, s-maxage=60, stale-while-revalidate=300   # treść publiczna
```

`immutable` tylko dla plików z sumą kontrolną w nazwie (`app.a3f9c21.js`). Na
`app.js` oznacza, że użytkownicy nie zobaczą aktualizacji przez rok.

### Nawałnica po wygaśnięciu

Gdy popularny klucz wygasa, tysiąc równoległych żądań uderza w bazę jednocześnie.
Zabezpieczenia: pojedynczy odświeżacz (blokada na klucz), losowe rozproszenie TTL
(`ttl * (0.9 + random*0.2)`), oraz `stale-while-revalidate` — zwracaj stare dane
i odświeżaj w tle.

---

## Testy obciążeniowe

### Kiedy mają sens

Przed premierą, przed przewidywanym szczytem (kampania, termin ustawowy), po zmianie
architektury, oraz jako regresja wydajnościowa w potoku nocnym. Nie przy każdym PR —
trwają za długo i szumią.

### k6 (2.0)

```js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    // stopniowe dochodzenie do docelowego natężenia
    narastanie: {
      executor: 'ramping-arrival-rate',
      startRate: 10, timeUnit: '1s',
      preAllocatedVUs: 50, maxVUs: 500,
      stages: [
        { target: 50,  duration: '2m' },
        { target: 200, duration: '5m' },
        { target: 200, duration: '10m' },   // utrzymanie — tu widać wycieki
        { target: 0,   duration: '2m' },
      ],
    },
  },
  thresholds: {
    http_req_failed:   ['rate<0.01'],                 // <1% błędów
    http_req_duration: ['p(95)<800', 'p(99)<2000'],
    checks:            ['rate>0.99'],
  },
};

export default function () {
  const odp = http.get(`${__ENV.BASE_URL}/api/faktury?rok=2026`, {
    headers: { Authorization: `Bearer ${__ENV.TOKEN}` },
    tags: { endpoint: 'lista_faktur' },               // tag = wzorzec, nie pełny URL
  });
  check(odp, {
    'status 200': (r) => r.status === 200,
    'ma dane':    (r) => r.json('dane.length') > 0,
  });
  sleep(1);
}
```

```bash
k6 run --out json=wyniki.json obciazenie.js
```

`ramping-arrival-rate` (stałe natężenie żądań) jest właściwym executorem dla API:
utrzymuje zadaną liczbę żądań na sekundę niezależnie od tego, jak wolno system odpowiada.
Executor oparty na wirtualnych użytkownikach (`ramping-vus`) sam zwalnia, gdy system
zwalnia — i maskuje degradację, którą chcesz zobaczyć.

`thresholds` decydują o kodzie wyjścia, więc test obciążeniowy działa jako bramka CI.

### Locust (Python)

```python
from locust import HttpUser, task, between

class UzytkownikFaktur(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        odp = self.client.post("/api/logowanie",
                               json={"email": "test@example.com", "haslo": "…"})
        self.client.headers["Authorization"] = f"Bearer {odp.json()['token']}"

    @task(3)
    def lista(self):
        # name= grupuje statystyki po wzorcu, nie po konkretnym URL
        self.client.get("/api/faktury?rok=2026", name="/api/faktury")

    @task(1)
    def szczegoly(self):
        self.client.get(f"/api/faktury/{self.losowy_id()}", name="/api/faktury/:id")
```

### Rodzaje testów i co wykrywają

| Rodzaj | Przebieg | Wykrywa |
| --- | --- | --- |
| Obciążeniowy | oczekiwany ruch, 10–30 min | czy cel jest dotrzymany |
| Wytrzymałościowy | umiarkowany ruch, 2–8 h | wycieki pamięci i połączeń, rosnące opóźnienie |
| Skokowy | nagły wzrost ×10 w 30 s | zachowanie autoskalowania, zimne starty, kolejki |
| Przeciążeniowy | narastanie aż do awarii | punkt załamania i **sposób** załamania |
| Progowy | powolne narastanie | próg, przy którym degradacja się zaczyna |

Test przeciążeniowy jest najbardziej pouczający: interesuje cię nie tyle liczba, przy
której system pada, ile **jak** pada. Poprawne zachowanie to odrzucanie nadmiaru żądań
z kodem 429 i utrzymanie obsługi reszty. Niepoprawne: kaskadowe timeouty, wyczerpanie
pamięci, restart wszystkich instancji naraz.

### Warunki wiarygodności

- Środowisko o **proporcjonalnej** wielkości do produkcji, z tą samą architekturą.
  Test na jednej instancji z pustą bazą nie mówi nic o produkcji z 20 mln rekordów.
- Dane testowe o produkcyjnej objętości i rozkładzie. Zapytanie na 100 rekordach
  z pełnym skanem jest szybkie.
- Rozgrzewka przed pomiarem (JIT, cache, pule) — pierwsze 60 s odrzuć.
- Nie testuj przez CDN, jeśli mierzysz backend — zmierzysz cache.
- **Nigdy nie testuj obciążeniowo produkcji bez uzgodnienia.** Test obciążeniowy
  nieuzgodniony jest atakiem odmowy usługi na własną firmę.

---

## Budżety wydajnościowe w CI

Budżet jest liczbą, która blokuje merge. Bez blokowania jest to wykres, który nikt
nie ogląda, a wydajność degraduje się o 3% na wydanie — czyli dwukrotnie w rok.

| Budżet | Próg przykładowy | Narzędzie |
| --- | --- | --- |
| p95 kluczowego endpointu | < 500 ms przy 100 rps | k6 `thresholds` w potoku nocnym |
| Liczba zapytań SQL na żądanie | ≤ 5 dla listy, ≤ 3 dla szczegółów | test integracyjny liczący zapytania |
| Czas startu aplikacji | < 3 s do gotowości | pomiar w teście dymnym |
| Rozmiar pakietu klienckiego | wzrost > 10% wymaga uzasadnienia | `size-limit` / `bundlesize` |
| Zużycie pamięci po 1 h obciążenia | wzrost < 10% wobec wartości po rozgrzewce | test wytrzymałościowy nocny |

```yaml
# potok nocny — regresja wydajnościowa jako osobne zadanie, nie bramka na PR
wydajnosc:
  schedule: '0 2 * * *'
  steps:
    - run: k6 run --quiet obciazenie/api.js      # kod wyjścia ≠ 0 przy naruszeniu progu
    - run: node scripts/porownaj-z-baza.js wyniki.json   # skrypt projektu, nie pluginu
```

Porównuj z **własną bazą historyczną**, nie z wartością bezwzględną wpisaną raz do
konfiguracji. Regresja o 40% z 100 ms na 140 ms nie przekroczy progu 500 ms, a jest
dokładnie tym, co chcesz wychwycić.

---

## Antywzorce wydajnościowe

| Antywzorzec | Konsekwencja | Zamiast tego |
| --- | --- | --- |
| Optymalizacja bez profilu | Stracony czas na 5% ścieżki, utrata czytelności | Profil najpierw, zawsze |
| Cache jako pierwsza odpowiedź na „wolno” | Niespójność, trudne błędy, koszt operacyjny | Indeks → zapytanie → algorytm → dopiero cache |
| `Promise.all` na 5000 elementach | Wyczerpanie puli połączeń, przeciążenie usługi zewnętrznej | Ograniczona współbieżność (`p-limit`, `asyncio.Semaphore`) |
| Zwiększenie limitu czasu zamiast naprawy | Awaria wraca przy większej skali; blokuje zasoby dłużej | Zmierz, co zajmuje czas |
| Odczyt całego zbioru do pamięci | OOM przy wzroście danych | Strumienie, kursory, paginacja |
| Mikrooptymalizacja pętli w JS/Pythonie | Pomijalny zysk przy 90% czasu w I/O | Zajmij się I/O |
| Test wydajności na pustej bazie | Fałszywa pewność | Dane produkcyjnej objętości |
| Średnia zamiast percentyli | Ukrywa ogon, w którym siedzą realni użytkownicy | p50/p95/p99 |
