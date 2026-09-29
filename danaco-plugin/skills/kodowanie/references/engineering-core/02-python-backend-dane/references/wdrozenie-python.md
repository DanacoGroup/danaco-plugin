# Pakowanie i wdrożenie usługi Pythona — karta

Karta obejmuje wdrożenie usługi Pythona: obraz kontenera, sekrety, health, logowanie
strukturalne, zamykanie na sygnał. Wdrożenie w ujęciu ogólnym — lista kontrolna wydania,
migracje bez przestoju, wdrożenie kroczące, wycofanie — opisuje
`references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.
Stan na sierpień 2026; wersje traktuj jako orientacyjne.

uv **0.12.1**, Python **3.14.6**, structlog **26.1.0**, prometheus-client **0.26.0**,
gunicorn **26.0.0**, uvicorn **0.52.1**.

## Dockerfile wielostopniowy z uv

```dockerfile
# syntax=docker/dockerfile:1.7

# ---------- etap 1: budowanie środowiska ----------
FROM python:3.14-slim-bookworm AS builder

# uv jako statyczne binarium z obrazu Astral — wersja PRZYPIĘTA, nie :latest
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Warstwa zależności osobno od kodu: zmiana kodu nie unieważnia cache zależności.
# --mount=type=bind zamiast COPY — pliki nie zostają w warstwie.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ---------- etap 2: obraz uruchomieniowy ----------
FROM python:3.14-slim-bookworm AS runtime

# biblioteki systemowe potrzebne w czasie działania; NIE build-essential
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl tini \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src
COPY --from=builder --chown=app:app /app/migrations /app/migrations
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# tini jako PID 1: przekazuje sygnały i zbiera procesy zombie
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--timeout-graceful-shutdown", "30", "--proxy-headers"]
```

`.dockerignore` — bez niego kontekst budowania ma setki megabajtów i cache jest bezużyteczny:

```
.git
.venv
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
.hypothesis/
htmlcov/
tests/
docs/
*.md
.env*
data/
dist/
```

| Ustawienie | Dlaczego |
|---|---|
| `UV_COMPILE_BYTECODE=1` | prekompilacja `.pyc` w obrazie; szybszy start kontenera, kosztem czasu budowania |
| `UV_LINK_MODE=copy` | cache uv i katalog docelowy są na różnych systemach plików — twarde dowiązania nie zadziałają |
| `UV_PYTHON_DOWNLOADS=0` | używaj Pythona z obrazu bazowego zamiast pobierać drugi |
| `--locked` | błąd, gdy `uv.lock` nie odpowiada `pyproject.toml` (odpowiednik `--frozen` z dodatkową kontrolą) |
| `--no-editable` | pakiet skopiowany do `.venv`, nie dowiązany do `/app/src` |
| `--no-dev` | pytest, ruff i mypy nie trafiają do obrazu produkcyjnego |
| `--no-install-project` w pierwszym `sync` | warstwa z zależnościami zmienia się tylko przy zmianie locka |
| `PYTHONFAULTHANDLER=1` | ślad stosu przy segfault w rozszerzeniu C |
| `tini` jako PID 1 | Python jako PID 1 nie zbiera zombie i wymaga własnej obsługi sygnałów |

Rozmiar: `python:3.14-slim-bookworm` daje obraz ok. 150–250 MB z typowym zestawem
zależności. `alpine` bywa mniejszy, ale musl łamie koła binarne — pakiety z rozszerzeniami
C (psycopg, pydantic-core, numpy, polars) trzeba wtedy kompilować, co wydłuża budowanie
o kilkanaście minut. `distroless` daje najmniejszy obraz, ale brak powłoki uniemożliwia
diagnostykę wewnątrz kontenera. Domyślnie `slim`.

Sprawdzenie, co zajmuje miejsce: `docker history obraz:tag` i `dive obraz:tag`.

## Zmienne środowiskowe i sekrety

Jedno miejsce czytające środowisko — klasa `Settings` (patrz `references/fastapi.md` w tej podpaczce). Reszta kodu
importuje `get_settings()`, nikt nie sięga do `os.environ`.

| Warstwa | Sposób |
|---|---|
| Lokalnie | `.env` w katalogu projektu, w `.gitignore`, plus `.env.example` z pustymi wartościami w repo |
| CI | sekrety repozytorium wstrzykiwane jako zmienne środowiskowe joba |
| Kontener/orkiestrator | Secret montowany jako plik albo zmienna; nigdy `ENV` w Dockerfile |
| VPS | plik `/etc/danaco/app.env` z `chmod 600`, `EnvironmentFile=` w unicie systemd |

Zasady, których złamanie jest niemożliwe do cofnięcia:

- **Nigdy `ENV SECRET_KEY=...` w Dockerfile.** Wartość zostaje w warstwie obrazu i jest
  widoczna dla każdego, kto ma dostęp do rejestru — także po usunięciu z Dockerfile.
- **Nigdy `--build-arg` do sekretu.** Trafia do historii obrazu. Do sekretu w czasie
  budowania: `RUN --mount=type=secret,id=token ...`.
- Sekret w repozytorium = sekret spalony. Rotacja, nie usunięcie commita.
- `SecretStr` z Pydantic dla wartości wrażliwych — nie wyciekną przez `repr` w logu ani
  przez `model_dump()`.

Sekret w postaci pliku (montowany przez orkiestrator):

```python
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: SecretStr

    @field_validator("secret_key", mode="before")
    @classmethod
    def z_pliku(cls, v: str) -> str:
        # wartość "file:/run/secrets/klucz" -> odczyt z pliku
        if isinstance(v, str) and v.startswith("file:"):
            return Path(v[5:]).read_text(encoding="utf-8").strip()
        return v
```

## Kontrola stanu

Dwa różne endpointy, o różnym znaczeniu:

```python
from fastapi import APIRouter, Response, status
from sqlalchemy import text

router = APIRouter(tags=["stan"])


@router.get("/healthz", status_code=200)
async def zywotnosc() -> dict[str, str]:
    """Liveness: czy proces żyje. Bez zależności zewnętrznych.
    Porażka = restart kontenera, więc NIE wolno tu sprawdzać bazy —
    chwilowa niedostępność bazy zrestartowałaby wszystkie repliki naraz."""
    return {"status": "ok"}


@router.get("/readyz")
async def gotowosc(response: Response, sesja: Sesja) -> dict[str, object]:
    """Readiness: czy proces może przyjmować ruch.
    Porażka = wypadnięcie z puli load balancera, bez restartu."""
    kontrole: dict[str, str] = {}
    try:
        await sesja.execute(text("select 1"))
        kontrole["baza"] = "ok"
    except Exception as e:
        kontrole["baza"] = f"blad: {type(e).__name__}"

    ok = all(v == "ok" for v in kontrole.values())
    response.status_code = (
        status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return {"status": "ok" if ok else "degradacja", "kontrole": kontrole}


@router.get("/wersja")
async def wersja() -> dict[str, str]:
    return {"wersja": __version__, "commit": os.getenv("GIT_SHA", "nieznany")}
```

Pomylenie liveness z readiness jest klasycznym błędem: sprawdzanie bazy w `/healthz`
zamienia dziesięciosekundową awarię bazy w kaskadę restartów całej floty.

## Logowanie strukturalne

```python
# src/app/logging.py
import logging
import sys

import structlog

from app.config import get_settings


def skonfiguruj_logi() -> None:
    s = get_settings()

    procesory: list = [
        structlog.contextvars.merge_contextvars,     # kontekst per żądanie
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    if s.debug:
        procesory.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        procesory.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=procesory,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[s.log_level]
        ),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # logi bibliotek (uvicorn, sqlalchemy) też na stdout, w tym samym formacie
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=s.log_level)
    for nazwa in ("uvicorn.access", "uvicorn.error", "sqlalchemy.engine"):
        logging.getLogger(nazwa).handlers.clear()
        logging.getLogger(nazwa).propagate = True
```

Middleware nadające każdemu żądaniu identyfikator korelacji:

```python
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = structlog.get_logger()


class KontekstZadania(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=rid, sciezka=request.url.path, metoda=request.method
        )
        start = time.perf_counter()
        try:
            odpowiedz = await call_next(request)
        except Exception:
            log.exception("zadanie_nieudane", ms=round((time.perf_counter() - start) * 1000))
            raise
        czas = round((time.perf_counter() - start) * 1000, 1)
        log.info("zadanie", status=odpowiedz.status_code, ms=czas)
        odpowiedz.headers["X-Request-ID"] = rid
        return odpowiedz
```

Reguły logowania:

- **JSON na stdout.** Nie pliki, nie rotacja, nie syslog. Zbieraniem zajmuje się środowisko.
- Pola nazwane, nie sklejone napisy: `log.info("faktura_wystawiona", faktura_id=x, kwota=y)`,
  nie `log.info(f"wystawiono {x} na {y}")`. Sklejony napis jest nieprzeszukiwalny.
- **Zero danych wrażliwych**: haseł, tokenów, pełnych numerów kart, PESEL-i, treści
  dokumentów. Filtr na procesorze, jeśli ryzyko jest realne.
- `log.exception` (nie `log.error`) w bloku `except` — dodaje ślad stosu.
- Poziomy: `DEBUG` lokalnie, `INFO` na produkcji. `WARNING` = coś wymaga uwagi człowieka,
  `ERROR` = operacja się nie udała.
- Identyfikator korelacji przekazuj dalej w nagłówku do usług wewnętrznych.

## Metryki

```python
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from fastapi import Response

ZADANIA = Counter("http_zadania_total", "Liczba żądań", ["metoda", "sciezka", "status"])
CZAS = Histogram(
    "http_czas_sekundy", "Czas obsługi", ["metoda", "sciezka"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
BLEDY_INTEGRACJI = Counter("integracja_bledy_total", "Błędy integracji", ["usluga", "kod"])


@app.get("/metrics", include_in_schema=False)
async def metryki() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Etykieta `sciezka` musi być **wzorcem trasy** (`/faktury/{id}`), nie konkretnym URL-em.
Użycie `request.url.path` tworzy nową serię czasową na każdy identyfikator i wysadza
bazę metryk w kilka godzin.

Cztery metryki, od których zaczynasz: liczba żądań, czas odpowiedzi (histogram, nie
średnia), odsetek błędów 5xx, zajętość puli połączeń do bazy. Reszta na żądanie.

`prometheus_client` z wieloma workerami gunicorna wymaga trybu wieloprocesowego
(`PROMETHEUS_MULTIPROC_DIR`), inaczej każdy worker raportuje własne, niepełne liczniki.

## Sygnały i wyłączanie z wdziękiem

Kolejność zdarzeń przy wdrożeniu: orkiestrator wysyła `SIGTERM` → proces przestaje
przyjmować nowe połączenia → kończy trwające żądania → zamyka zasoby → kończy się.
Jeśli nie skończy się w czasie `terminationGracePeriod`, dostaje `SIGKILL`.

Dla uvicorna wystarczy `--timeout-graceful-shutdown 30` plus zamykanie zasobów w `lifespan`.
Dla workera własnej roboty:

```python
import asyncio
import signal

import structlog

log = structlog.get_logger()


async def main() -> None:
    stop = asyncio.Event()
    petla = asyncio.get_running_loop()
    for sygnal in (signal.SIGTERM, signal.SIGINT):
        petla.add_signal_handler(sygnal, stop.set)

    log.info("worker_start")
    async with asyncio.TaskGroup() as tg:
        zadanie = tg.create_task(petla_robocza(stop))
        await stop.wait()
        log.info("sygnal_zamkniecia")
        # petla_robocza sama kończy się po ustawieniu zdarzenia;
        # anulowanie tylko gdy przekroczy limit
        try:
            async with asyncio.timeout(25):
                await zadanie
        except TimeoutError:
            log.warning("wymuszone_anulowanie")
            zadanie.cancel()
    log.info("worker_stop")


async def petla_robocza(stop: asyncio.Event) -> None:
    while not stop.is_set():
        element = await pobierz_zadanie()
        if element is None:
            await asyncio.sleep(1)
            continue
        await przetworz(element)      # przerywamy MIĘDZY zadaniami, nie w trakcie


if __name__ == "__main__":
    asyncio.run(main())
```

Warunek `while not stop.is_set()` sprawdzany między zadaniami, a nie anulowanie w połowie
przetwarzania — dzięki temu zadanie kończy się w spójnym stanie.

Limit łaski w orkiestratorze musi być większy niż wewnętrzny timeout aplikacji, inaczej
`SIGKILL` przyjdzie w trakcie sprzątania. Para: aplikacja 25 s, orkiestrator 40 s.

## VPS, kontener czy funkcja

| | VPS + systemd | Kontener (orkiestrator/PaaS) | Funkcja (serverless) |
|---|---|---|---|
| Czas startu | brak (usługa działa) | sekundy | zimny start 0,5–3 s |
| Skalowanie | ręczne | automatyczne | automatyczne, do zera |
| Stan w procesie (cache, pula, WebSocket) | tak | tak | nie |
| Zadania długie | tak | tak | limit czasu (zwykle 15 min) |
| Koszt przy stałym ruchu | najniższy | średni | najwyższy |
| Koszt przy ruchu sporadycznym | stały | stały | bliski zeru |
| Obsługa | pełna twoja | częściowa | minimalna |
| Kiedy | jedna usługa, przewidywalny ruch, ograniczenia danych | wiele usług, zmienny ruch, CI/CD | webhooki, zadania na zdarzenie |

Domyślnie dla DANACO: kontener. VPS z systemd, gdy usługa jest jedna, a zespół nie ma
orkiestratora. Funkcja tylko dla webhooków i przetwarzania na zdarzenie — usługa HTTP
z pulą połączeń do bazy w funkcji oznacza wyczerpanie `max_connections` przy skoku ruchu.

### systemd na VPS

```ini
# /etc/systemd/system/danaco-api.service
[Unit]
Description=DANACO API
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=exec
User=danaco
Group=danaco
WorkingDirectory=/srv/danaco-api
EnvironmentFile=/etc/danaco/api.env
ExecStart=/srv/danaco-api/.venv/bin/gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 --bind 127.0.0.1:8000 \
  --timeout 60 --graceful-timeout 30 --max-requests 2000 --max-requests-jitter 200 \
  --access-logfile - --error-logfile -
ExecReload=/bin/kill -s HUP $MAINPID
KillSignal=SIGTERM
KillMode=mixed
TimeoutStopSec=45
Restart=always
RestartSec=5

# ograniczenia przywilejów
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/danaco-api/dane
ProtectKernelTunables=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now danaco-api
sudo journalctl -u danaco-api -f --output=cat        # logi JSON bez prefiksów
```

Wdrożenie na VPS: `git pull && uv sync --frozen --no-dev && uv run alembic upgrade head
&& sudo systemctl reload-or-restart danaco-api`.

## Migracje przy wdrożeniu

Kolejność ma znaczenie i jest źródłem większości awarii wdrożeniowych:

1. Migracja **wstecznie zgodna** (dodanie kolumny nullowalnej, nowej tabeli, indeksu
   `CONCURRENTLY`) — uruchamiana **przed** wdrożeniem nowego kodu.
2. Wdrożenie kodu.
3. Migracja **domykająca** (ustawienie `NOT NULL`, usunięcie starej kolumny) — w kolejnym
   wdrożeniu, gdy stary kod już nie działa.

Migracja usuwająca kolumnę wdrożona razem z kodem powoduje, że stare instancje (w trakcie
wymiany rolling) sypią błędami przez cały okres wdrożenia.

Uruchamianie: osobny krok w potoku (job/`initContainer`), nie w `lifespan` aplikacji.
Migracja w `lifespan` przy czterech replikach uruchamia się cztery razy równolegle.
Alembic ma blokadę na tabeli wersji, więc trzy repliki będą czekać, a jeśli migracja jest
długa — timeout startu i restart w pętli.

## Cron i zadania okresowe

| Sposób | Kiedy |
|---|---|
| CronJob orkiestratora | domyślnie w kontenerach — izolacja, logi, historia |
| `systemd` timer | na VPS; lepszy od crona (logi w journalu, `Persistent=true` po przestoju) |
| Celery Beat / arq `cron` | gdy zadanie i tak korzysta z kolejki |
| APScheduler w procesie | tylko jedna instancja usługi; patrz `references/engineering-core/02-python-backend-dane/references/async-i-zadania.md` |
| `crontab` | ostateczność — brak logów, brak historii, cicha porażka |

```ini
# /etc/systemd/system/danaco-raport.timer
[Unit]
Description=Nocny raport DANACO

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true            # uruchom po starcie, jeśli termin minął w czasie przestoju
RandomizedDelaySec=300     # rozrzut, gdy maszyn jest wiele

[Install]
WantedBy=timers.target
```

Wymagania dla każdego zadania okresowego: idempotencja (patrz
`references/engineering-core/02-python-backend-dane/references/async-i-zadania.md`), blokada przed
nakładaniem przebiegów (`flock` albo `pg_try_advisory_lock`), sygnalizacja porażki do systemu
monitoringu (heartbeat po sukcesie — brak sygnału to alarm), limit czasu.

Zadanie okresowe, które po cichu przestało się uruchamiać, jest wykrywane średnio po
kilku tygodniach. Heartbeat wysyłany po każdym udanym przebiegu skraca to do jednego cyklu.

## Lista kontrolna wdrożenia

- [ ] Obraz budowany wielostopniowo, bez `build-essential` w warstwie uruchomieniowej.
- [ ] Użytkownik nie-root; `USER app` przed `CMD`.
- [ ] Wersja uv i obrazu bazowego przypięta, nie `:latest`.
- [ ] `uv sync --locked --no-dev`; `uv.lock` w repozytorium.
- [ ] Zero sekretów w obrazie (`docker history` nie pokazuje wartości).
- [ ] `/healthz` bez zależności zewnętrznych, `/readyz` z nimi.
- [ ] Logi JSON na stdout, z identyfikatorem korelacji.
- [ ] `SIGTERM` obsłużony; okres łaski orkiestratora > timeout aplikacji.
- [ ] Migracje jako osobny krok, wstecznie zgodne.
- [ ] Metryki wystawione, etykiety bez nieograniczonej liczności.
- [ ] Limity zasobów ustawione (pamięć, CPU) — proces bez limitu ubija sąsiadów.
- [ ] Ścieżka wycofania sprawdzona: poprzedni obraz startuje na aktualnym schemacie bazy.
