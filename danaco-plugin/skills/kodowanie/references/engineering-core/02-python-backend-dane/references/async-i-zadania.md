# asyncio i zadania w tle — sierpień 2026

Python **3.14.6**. Celery **5.6.3**, arq **0.28.0**, RQ **2.10.0**, dramatiq **2.2.0**,
taskiq **0.12.4**, APScheduler **3.11.3**, anyio **4.14.2**.

## Kiedy async ma sens, a kiedy nie

| Rodzaj pracy | Właściwe narzędzie |
|---|---|
| Wiele równoczesnych operacji I/O (HTTP, baza, pliki sieciowe) | `asyncio` |
| Tysiące otwartych połączeń (WebSocket, SSE, long polling) | `asyncio` |
| Jedno wywołanie HTTP w skrypcie | zwykły kod synchroniczny — async nic nie da |
| Obliczenia na CPU (parsowanie, kompresja, kryptografia, pętle) | `ProcessPoolExecutor`, wolny build 3.14t, albo Rust/C |
| Blokująca biblioteka bez wersji async | `asyncio.to_thread` / `ThreadPoolExecutor` |
| Praca, która ma przetrwać restart procesu | kolejka zadań, nie asyncio |

Async **nie przyspiesza** pojedynczej operacji. Skraca łączny czas, gdy operacji jest wiele
i czekają na coś zewnętrznego. Jeśli program czeka na jedną rzecz naraz, async dokłada
złożoność bez zysku.

Trzy sygnały, że async jest błędnym wyborem: całość to jeden przebieg wsadowy; profil
pokazuje czas w Pythonie, nie w oczekiwaniu; biblioteka kluczowa dla zadania nie ma API
asynchronicznego.

## Podstawy, których model najczęściej nie stosuje

```python
import asyncio


async def main() -> None:
    async with httpx.AsyncClient() as klient:
        odp = await klient.get("https://example.com/status")
        print(odp.status_code)


asyncio.run(main())        # jedyne poprawne wejście; tworzy i zamyka pętlę
```

Nie `asyncio.get_event_loop()` (deprecjonowane), nie `loop.run_until_complete` w nowym
kodzie. Wewnątrz korutyny, gdy potrzebujesz pętli: `asyncio.get_running_loop()`.

### `TaskGroup` zamiast `gather` (3.11+)

```python
import asyncio

import httpx


async def pobierz(klient: httpx.AsyncClient, url: str) -> dict:
    odp = await klient.get(url)
    odp.raise_for_status()
    return odp.json()


async def pobierz_wszystkie(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as klient:
        async with asyncio.TaskGroup() as tg:
            zadania = [tg.create_task(pobierz(klient, u)) for u in urls]
    # wyjście z bloku czeka na wszystkie; przy błędzie anuluje resztę
    # i podnosi ExceptionGroup
    return [z.result() for z in zadania]
```

Różnice wobec `asyncio.gather`, które mają znaczenie:

- `TaskGroup` przy błędzie jednego zadania **anuluje pozostałe**. `gather` bez
  `return_exceptions=True` zwraca pierwszy wyjątek, ale reszta zadań biegnie dalej
  w tle i kończy się „Task exception was never retrieved” w logu.
- `TaskGroup` podnosi `ExceptionGroup` — masz komplet błędów, nie pierwszy z brzegu.
- `gather` pozostaje właściwy, gdy chcesz **wszystkie** wyniki niezależnie od błędów:
  `wyniki = await asyncio.gather(*zadania, return_exceptions=True)` i sprawdzenie
  `isinstance(w, Exception)` na każdym.

### Timeout

```python
async def z_limitem() -> str | None:
    try:
        async with asyncio.timeout(5.0):          # 3.11+
            return await wolna_operacja()
    except TimeoutError:
        return None


# przesunięcie terminu w trakcie
async def z_przedluzeniem() -> None:
    async with asyncio.timeout(10) as cm:
        await etap_pierwszy()
        cm.reschedule(asyncio.get_running_loop().time() + 30)
        await etap_drugi()


# termin bezwzględny
async def do_godziny(deadline: float) -> None:
    async with asyncio.timeout_at(deadline):
        await praca()
```

`asyncio.wait_for` nadal działa, ale `timeout` obejmuje wiele operacji jednym blokiem
i czyta się lepiej. **Zawsze** stawiaj timeout na wywołaniach sieciowych — domyślnie
`httpx.AsyncClient()` bez `timeout=` ma 5 s, `aiohttp` 5 minut, a wiele klientów bazy
nie ma go wcale.

### Anulowanie

```python
async def z_sprzataniem() -> None:
    try:
        await dluga_operacja()
    except asyncio.CancelledError:
        await zwolnij_zasoby()       # sprzątanie
        raise                        # ZAWSZE podnieś dalej
```

`CancelledError` dziedziczy po `BaseException` (od 3.8), więc `except Exception` go nie
łapie — i dobrze. Połknięcie `CancelledError` (brak `raise`) sprawia, że zadanie ignoruje
anulowanie: `TaskGroup` zawiesi się przy wyjściu, a proces nie zakończy się po SIGTERM.

Ochrona fragmentu, który musi się dokończyć:

```python
async def zapis_krytyczny(dane: bytes) -> None:
    await asyncio.shield(zapisz_do_bazy(dane))
```

`shield` chroni **wewnętrzne** zadanie; wołający i tak dostanie `CancelledError`. Do
faktycznego dokończenia pracy używaj `finally` z operacją bez `await` albo kolejki.

### Limit współbieżności

```python
import asyncio

import httpx

LIMIT = asyncio.Semaphore(10)


async def pobierz_z_limitem(klient: httpx.AsyncClient, url: str) -> dict:
    async with LIMIT:
        odp = await klient.get(url)
        odp.raise_for_status()
        return odp.json()


async def przetworz(urls: list[str]) -> list[dict]:
    limity = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    async with httpx.AsyncClient(limits=limity, timeout=10.0) as klient:
        async with asyncio.TaskGroup() as tg:
            zadania = [tg.create_task(pobierz_z_limitem(klient, u)) for u in urls]
    return [z.result() for z in zadania]
```

Bez semafora `TaskGroup` z 10 000 URL-i otworzy 10 000 zadań naraz: wyczerpanie deskryptorów,
odrzucenia po stronie serwera, zablokowanie adresu IP. Semafor jest obowiązkowy przy
każdym wachlarzu żądań o nieznanym rozmiarze.

Przy pracy strumieniowej — wzorzec producent/konsument z ograniczoną kolejką:

```python
async def pipeline(zrodlo: AsyncIterator[str], workerow: int = 8) -> None:
    kolejka: asyncio.Queue[str | None] = asyncio.Queue(maxsize=100)

    async def konsument() -> None:
        while True:
            element = await kolejka.get()
            try:
                if element is None:
                    return
                await przetworz_jeden(element)
            finally:
                kolejka.task_done()

    async with asyncio.TaskGroup() as tg:
        konsumenci = [tg.create_task(konsument()) for _ in range(workerow)]
        async for element in zrodlo:
            await kolejka.put(element)      # blokuje przy 100 — kontrola napływu
        for _ in konsumenci:
            await kolejka.put(None)
```

`maxsize` na kolejce daje kontrolę napływu. Bez niego szybki producent wciągnie cały plik
do pamięci, zanim konsumenci przetworzą pierwszy element.

## Czego NIE robić w korutynie

| Zapis blokujący | Zamiast |
|---|---|
| `time.sleep(1)` | `await asyncio.sleep(1)` |
| `requests.get(url)` | `await klient.get(url)` (`httpx.AsyncClient`) |
| `psycopg.connect(...)` (sync) | `psycopg` async / `create_async_engine` |
| `open(p).read()` na dużym pliku | `await asyncio.to_thread(p.read_bytes)` lub `aiofiles` |
| `subprocess.run(...)` | `await asyncio.create_subprocess_exec(...)` |
| `redis.Redis()` (sync) | `redis.asyncio.Redis()` |
| pętla licząca 200 ms | `await asyncio.to_thread(...)` lub `ProcessPoolExecutor` |
| `pandas.read_parquet` na 2 GB | `await asyncio.to_thread(...)` |
| `bcrypt.hashpw(...)` (~100 ms) | `await asyncio.to_thread(...)` |

Konsekwencja złamania: pętla zdarzeń jest jednowątkowa, więc blokada 200 ms zatrzymuje
**wszystkie** obsługiwane żądania na 200 ms. Przy 50 równoczesnych żądaniach ostatnie czeka
10 s. W profilu wygląda to jak wolna baza, bo czas rozkłada się równomiernie.

Wykrywanie:

```python
import asyncio

asyncio.run(main(), debug=True)   # ostrzeżenie o korutynie blokującej > 100 ms
```

albo `PYTHONASYNCIODEBUG=1`. W 3.14 dochodzi introspekcja z zewnątrz:

```bash
python -m asyncio ps <PID>        # tabela zadań
python -m asyncio pstree <PID>    # drzewo oczekiwań, wykrywa cykle
```

Ruff z regułami `ASYNC` (`ASYNC100`, `ASYNC101`, `ASYNC210`, `ASYNC230`) łapie część
statycznie: `open()` w korutynie, `time.sleep`, wywołania `requests`.

## Wątki i procesy

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor


# blokujące I/O -> wątek
async def wczytaj(sciezka: Path) -> bytes:
    return await asyncio.to_thread(sciezka.read_bytes)


# obliczenie CPU -> proces
def licz_hasz(dane: bytes) -> str:
    import hashlib
    return hashlib.sha256(dane).hexdigest()


async def hasze(pliki: list[Path]) -> list[str]:
    petla = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=4) as pula:
        zadania = [
            petla.run_in_executor(pula, licz_hasz, await wczytaj(p)) for p in pliki
        ]
        return await asyncio.gather(*zadania)
```

`asyncio.to_thread` używa domyślnej puli wątków interpretera (min. 5, maks. `32 + rdzenie`).
FastAPI ma własną pulę dla endpointów `def` — domyślnie 40. Jeśli wszystkie wątki są zajęte,
kolejne wywołania czekają w kolejce, a objaw wygląda jak zawieszenie serwera.

`ProcessPoolExecutor`: argumenty i wyniki są piklowane, więc funkcja musi być na poziomie
modułu (nie lambda, nie funkcja lokalna), a przesyłanie dużych obiektów jest kosztowne.
Przy tablicach numpy przekazuj ścieżkę do pliku, nie tablicę.

W 3.14 alternatywa bez piklowania procesowego: `InterpreterPoolExecutor`
(`concurrent.futures`, PEP 734) — subinterpretery w jednym procesie, lżejsze niż procesy,
ale wiele rozszerzeń C jeszcze ich nie obsługuje.

## Kolejki zadań: który wybrać

| | Celery 5.6 | arq 0.28 | RQ 2.10 | APScheduler 3.11 |
|---|---|---|---|---|
| Model | sync (workery procesowe) | async natywnie | sync | w procesie |
| Broker | Redis, RabbitMQ, SQS | Redis | Redis | dowolny magazyn lub brak |
| Ponawianie | rozbudowane, z backoff | tak, `max_tries` | podstawowe | brak (to nie kolejka) |
| Harmonogram | Celery Beat (osobny proces) | wbudowany `cron()` | `rq-scheduler` | to jest jego zadanie |
| Widoczność | Flower, zdarzenia, wiele narzędzi | skromna | `rq dashboard` | brak |
| Złożoność konfiguracji | wysoka | niska | najniższa | najniższa |
| Kiedy | wiele typów zadań, potoki, wiele zespołów | aplikacja async (FastAPI) | kilka prostych zadań | zadanie okresowe w jednej instancji |

Reguła decyzyjna:

- Aplikacja jest asynchroniczna (FastAPI) i zadań jest kilkanaście → **arq**. Ten sam styl
  kodu, ten sam Redis, brak mostu sync/async.
- Zadania są liczne, różnorodne, mają zależności między sobą, potrzebny podgląd operacyjny
  → **Celery**.
- Trzy zadania i chcesz skończyć dziś → **RQ**.
- Potrzebujesz tylko „raz dziennie o 3:00” w jednej instancji → **APScheduler**. Przy wielu
  instancjach APScheduler odpali zadanie tyle razy, ile jest procesów — potrzebna blokada
  w bazie albo przeniesienie na cron/beat.
- Wszystko już jest w Postgresie i nie chcesz Redisa → kolejka na tabeli z
  `SELECT ... FOR UPDATE SKIP LOCKED`. Wystarcza do kilkuset zadań na minutę.

### arq — konfiguracja kompletna

```python
# src/app/tasks/worker.py
import asyncio
from typing import Any

import httpx
import structlog
from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings

log = structlog.get_logger()


async def wyslij_fakture(ctx: dict[str, Any], faktura_id: str) -> str:
    klient: httpx.AsyncClient = ctx["http"]
    proba = ctx["job_try"]
    log.info("wysylka_faktury", faktura_id=faktura_id, proba=proba)
    odp = await klient.post("https://ksef.example/faktury", json={"id": faktura_id})
    odp.raise_for_status()
    return odp.json()["numer_referencyjny"]


async def sprzataj_pliki(ctx: dict[str, Any]) -> int:
    usuniete = await usun_stare_pliki(dni=30)
    log.info("sprzatanie", usuniete=usuniete)
    return usuniete


async def startup(ctx: dict[str, Any]) -> None:
    ctx["http"] = httpx.AsyncClient(timeout=30.0)


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["http"].aclose()


class WorkerSettings:
    functions = [wyslij_fakture]
    cron_jobs = [cron(sprzataj_pliki, hour=3, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 20                   # równoległość w jednym workerze
    job_timeout = 300               # sekundy
    max_tries = 5
    retry_jobs = True
    keep_result = 3600              # ile trzymać wynik
    health_check_interval = 30
```

```bash
uv run arq app.tasks.worker.WorkerSettings
```

Kolejkowanie z endpointu:

```python
from arq import create_pool
from arq.connections import RedisSettings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.arq = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    try:
        yield
    finally:
        await app.state.arq.aclose()


@router.post("/faktury/{id_}/wyslij", status_code=202)
async def wyslij(id_: UUID, request: Request) -> dict[str, str]:
    zadanie = await request.app.state.arq.enqueue_job(
        "wyslij_fakture",
        str(id_),
        _job_id=f"wyslij:{id_}",              # klucz idempotencji
        _defer_by=timedelta(seconds=5),
    )
    return {"job_id": zadanie.job_id}
```

`_job_id` jest kluczem idempotencji: ponowne zakolejkowanie tego samego identyfikatora,
gdy zadanie jeszcze czeka lub biegnie, zostaje odrzucone. Bez tego dwukrotne kliknięcie
przycisku przez użytkownika wysyła fakturę dwa razy.

### Celery — minimum produkcyjne

```python
# src/app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

s = get_settings()
celery = Celery("danaco", broker=s.redis_url, backend=s.redis_url)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],          # nigdy pickle — wykonanie kodu z brokera
    result_serializer="json",
    timezone="Europe/Warsaw",
    enable_utc=True,
    task_acks_late=True,              # potwierdzenie PO wykonaniu, nie przy pobraniu
    task_reject_on_worker_lost=True,  # zadanie wraca do kolejki, gdy worker zginie
    worker_prefetch_multiplier=1,     # przy długich zadaniach; domyślne 4 tworzy zatory
    task_time_limit=600,              # twardy limit — SIGKILL
    task_soft_time_limit=540,         # miękki — SoftTimeLimitExceeded do obsłużenia
    broker_connection_retry_on_startup=True,
    task_default_queue="domyslna",
    task_routes={"app.tasks.raporty.*": {"queue": "ciezkie"}},
    beat_schedule={
        "nocne-sprzatanie": {
            "task": "app.tasks.utrzymanie.sprzataj",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
```

```python
# src/app/tasks/faktury.py
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded


@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,          # 1, 2, 4, 8 ... sekund
    retry_backoff_max=600,
    retry_jitter=True,           # rozrzut, żeby ponowienia nie uderzyły równocześnie
    max_retries=5,
    acks_late=True,
)
def wyslij_fakture(self, faktura_id: str) -> str:
    try:
        return wyslij_do_ksef(faktura_id)
    except SoftTimeLimitExceeded:
        zapisz_stan_czesciowy(faktura_id)
        raise
```

```bash
uv run celery -A app.tasks.celery_app worker \
  --loglevel=INFO --concurrency=4 --queues=domyslna,ciezkie --max-tasks-per-child=100
uv run celery -A app.tasks.celery_app beat --loglevel=INFO
```

`task_acks_late=True` + `task_reject_on_worker_lost=True` to para, bez której zadanie
przepada przy ubiciu workera w trakcie wdrożenia. Ceną jest możliwość wykonania zadania
dwa razy — stąd wymóg idempotencji.

`--max-tasks-per-child` odnawia proces workera; maskuje wycieki pamięci w bibliotekach
trzecich, których nie naprawisz.

### Kolejka na Postgresie, gdy nie chcesz Redisa

```sql
create table zadania (
  id bigserial primary key,
  typ text not null,
  ladunek jsonb not null,
  status text not null default 'oczekuje',
  prob smallint not null default 0,
  uruchom_po timestamptz not null default now(),
  utworzono timestamptz not null default now()
);
create index on zadania (status, uruchom_po) where status = 'oczekuje';
```

```python
POBIERZ = text("""
    update zadania set status = 'w_toku', prob = prob + 1
    where id = (
        select id from zadania
        where status = 'oczekuje' and uruchom_po <= now()
        order by uruchom_po
        for update skip locked
        limit 1
    )
    returning id, typ, ladunek, prob
""")
```

`FOR UPDATE SKIP LOCKED` pozwala wielu workerom pobierać zadania bez blokowania się
nawzajem. Indeks częściowy `where status = 'oczekuje'` utrzymuje rozmiar indeksu na
poziomie długości kolejki, nie historii.

## Idempotencja i ponawianie

Zadanie w kolejce **zostanie** wykonane więcej niż raz. Nie „może” — przy `acks_late`,
timeoutach sieci i restartach jest to normalny bieg rzeczy. Projektuj pod to:

1. **Klucz naturalny.** Zamiast „wyślij maila” → „wyślij powiadomienie nr 12345”;
   przed wysyłką sprawdź, czy `powiadomienia.wyslano_at` jest ustawione.
2. **Wstawianie warunkowe.** `insert ... on conflict (klucz_idempotencji) do nothing`
   i sprawdzenie liczby wstawionych wierszy.
3. **Przejścia stanu zamiast operacji.** `update faktury set status='wyslana'
   where id=%s and status='gotowa'` — drugie wykonanie zmienia 0 wierszy i kończy się bez
   skutku ubocznego.
4. **Klucz idempotencji u dostawcy.** Większość API płatniczych i fakturowych przyjmuje
   nagłówek `Idempotency-Key`; przekaż tam identyfikator zadania.

Polityka ponawiania:

| Rodzaj błędu | Ponawiać |
|---|---|
| Timeout, `ConnectionError`, HTTP 502/503/504 | tak, backoff wykładniczy z jitterem |
| HTTP 429 | tak, z opóźnieniem z nagłówka `Retry-After` |
| HTTP 400/422 (złe dane) | **nie** — kolejne próby dadzą ten sam wynik |
| HTTP 401/403 | nie; to problem konfiguracji |
| Wyjątek domenowy (reguła biznesowa) | nie |
| `IntegrityError` z bazy | nie, chyba że to konflikt współbieżności |

Kolejka błędnych zadań (DLQ): po wyczerpaniu prób zadanie ma trafić do miejsca, które ktoś
przegląda. arq: `on_job_failed`; Celery: `task_failure` + własna tabela. Zadanie, które
znika po piątej próbie bez śladu, to najdroższy rodzaj błędu — nikt się o nim nie dowie.

## Harmonogram

```python
# APScheduler w procesie usługi — tylko przy JEDNEJ instancji
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    sched = AsyncIOScheduler(timezone="Europe/Warsaw")
    sched.add_job(
        sprzataj,
        CronTrigger(hour=3, minute=0),
        id="sprzatanie",
        replace_existing=True,
        max_instances=1,          # brak nakładania się przebiegów
        misfire_grace_time=3600,  # dopuszczalne opóźnienie po przestoju
        coalesce=True,            # zaległe przebiegi scalone w jeden
    )
    sched.start()
    try:
        yield
    finally:
        sched.shutdown(wait=False)
```

Przy wielu replikach usługi APScheduler odpali zadanie w każdej z nich. Rozwiązania:
blokada doradcza Postgresa (`select pg_try_advisory_lock(...)` na początku zadania),
przeniesienie na Celery Beat lub arq `cron` (jeden proces harmonogramu), albo CronJob
w orkiestratorze.

Strefa czasowa: `Europe/Warsaw` z uwzględnieniem zmiany czasu. Zadanie o 2:30 w nocy
przesunięcia wiosennego nie wykona się wcale, a jesienią wykona się dwa razy. Zadania
krytyczne planuj poza 2:00–3:00 albo w UTC.

## Typowe pułapki

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| „Task was destroyed but it is pending” | zadanie z `create_task` bez zachowanej referencji zebrał GC | trzymaj referencję albo używaj `TaskGroup` |
| Usługa nie kończy się po Ctrl+C / SIGTERM | korutyna połyka `CancelledError` albo zadanie tła nie jest anulowane w `lifespan` | `raise` po sprzątaniu; anuluj w `finally` |
| „Event loop is closed” na wyjściu | zasób zamykany po zamknięciu pętli | zamykaj w `lifespan`/`finally`, nie w `__del__` |
| Wszystko wolne pod obciążeniem, baza pusta | blokujące wywołanie w korutynie | `debug=True`, reguły ruff `ASYNC` |
| „Too many open files” | brak semafora przy wachlarzu żądań | `asyncio.Semaphore` + `httpx.Limits` |
| Klient HTTP tworzony na każde żądanie | brak współdzielonego `AsyncClient` | jeden klient w `lifespan`, uzgadnianie TLS raz |
| Zadanie wykonane dwa razy | `acks_late` + brak idempotencji | klucz idempotencji, przejścia stanu |
| Celery „Received unregistered task” | worker nie importuje modułu z zadaniem | `include=` w `Celery(...)` albo `autodiscover_tasks` |
| Zadania stoją mimo wolnych workerów | `worker_prefetch_multiplier` zbyt duży, jeden worker zarezerwował kolejkę | ustaw na 1 przy długich zadaniach |
