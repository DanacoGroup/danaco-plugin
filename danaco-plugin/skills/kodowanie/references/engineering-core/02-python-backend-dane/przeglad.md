# Python w produkcji — przegląd modułu

Moduł obejmuje pisanie i utrzymanie kodu Pythona w produkcji: usługi HTTP, pracę
asynchroniczną, warstwę danych, testy, narzędzia projektu i wdrożenie. Karty pogłębione
wymienia tabela „Mapa plików referencyjnych” poniżej, a wszystkie moduły
`references/engineering-core/` — `references/engineering-core/spis.md`. Poza modułem:
sama składnia języka w `references/jezyki-programowania/python.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Stan na sierpień 2026. Każda reguła ma przypisaną wersję — jeśli w projekcie jest starsza,
reguła może nie obowiązywać i trzeba to sprawdzić, a nie zakładać.

## Kiedy wczytać ten moduł

- Piszesz lub zmieniasz kod w Pythonie: usługę HTTP, zadanie wsadowe, skrypt, bibliotekę, CLI.
- Zakładasz nowy projekt Pythona albo porządkujesz istniejący (`pyproject.toml`, lint, typy, CI).
- Diagnozujesz wydajność, blokowanie pętli zdarzeń, N+1 w ORM, zużycie pamięci przy danych.
- Piszesz testy do kodu Pythona albo naprawiasz kruchy zestaw testów.
- Pakujesz usługę Pythona do kontenera albo uruchamiasz ją na VPS.

**Nie używaj gdy:**

- Chodzi o Next.js, TypeScript albo komponenty interfejsu → `references/frameworki/nextjs.md`,
  `references/jezyki-programowania/javascript-typescript.md`, paczka `../ui-ux-pro/SKILL.md`.
- Chodzi o granice modułów, podział na usługi, kontrakty między systemami, ADR →
  `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`. Ten moduł mówi *jak
  napisać moduł kodu*, tamten *jakie moduły*.
- Chodzi o RAG, embeddingi, bazy wektorowe, chunking →
  `references/engineering-core/04-bazy-i-rag/przeglad.md`. (SQLAlchemy i Postgres jako baza
  relacyjna — tutaj. pgvector i wyszukiwanie semantyczne — tam.)
- Budujesz serwer MCP → `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md`.

## Wersje odniesienia (zweryfikowane 2026-08)

| Element | Wersja | Uwaga |
|---|---|---|
| CPython | **3.14.6** | wydanie z 2026-06-10; EOL 2030-10. 3.15.0 planowane 2026-10-01 (b4) |
| CPython minimum dla nowego projektu | **3.13** | 3.10 wygasa 2026-10-31, nie zaczynaj na nim |
| uv | **0.12.1** | menedżer projektu, wersji Pythona i narzędzi |
| ruff | **0.16.1** | lint + format; od 0.16 **413 reguł domyślnie** (było 59) |
| ty (Astral) | **0.0.66** | beta od 2025-12; stabilne zapowiadane na 2026 |
| mypy | **2.3.0** | od 2.0: `--num-workers`, minimum Python 3.10 |
| FastAPI | **0.141.1** | wymaga `starlette>=0.46`, `pydantic>=2.9` |
| Starlette | **1.3.1** | 1.0 w 2026-03: usunięto `on_event`, `@app.route`, `add_event_handler` |
| Pydantic | **2.13.4** | v1 nie używamy w nowym kodzie |
| pydantic-settings | **2.14.2** | konfiguracja z env |
| SQLAlchemy | **2.0.51** | 2.1 wciąż w beta (2.1.0b1, 2026-01) — na produkcji 2.0 |
| Alembic | **1.18.5** | |
| psycopg | **3.3.4** | `psycopg`, nie `psycopg2` |
| polars | **1.43.2** | silnik streaming przez `collect(engine="streaming")` |
| pandas | **3.0.5** | **3.0 = przełom**: Copy-on-Write obowiązkowy, dtype `str`, `pd.col()` |
| pyarrow / numpy | **25.0.0** / **2.5.1** | numpy 2.5 wymaga Pythona ≥ 3.12 |
| duckdb | **1.5.5** | |
| pytest | **9.1.1** | **9.0 = przełom**: `[tool.pytest]` w TOML, natywne subtesty, min. Python 3.10 |
| pytest-asyncio | **1.4.0** | |
| hypothesis / testcontainers | **6.165.0** / **4.15.0** | |
| uvicorn / granian / gunicorn | **0.52.1** / **2.8.0** / **26.0.0** | |
| typer / rich / click | **0.27.1** / **15.0.0** / 8.x | |
| celery / arq / rq / APScheduler | **5.6.3** / **0.28.0** / **2.10.0** / **3.11.3** | |
| structlog | **26.1.0** | |
| httpx | **0.28.1** | |

Jeśli piszesz regułę, przy której wersja ma znaczenie, podaj ją w kodzie lub komentarzu.

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
|---|---|---|
| `references/engineering-core/02-python-backend-dane/references/python-nowoczesny.md` | typowanie (generyki PEP 695, `Protocol`, `TypedDict`, `Literal`, `Self`, `ParamSpec`), `match`, dataclass vs Pydantic vs NamedTuple vs msgspec, menedżery kontekstu, generatory, `functools`, `ExceptionGroup`, PEP 649/750, lista rzeczy przestarzałych | zawsze przy pisaniu nowego kodu; przy code review; gdy widzisz `Dict[str, Any]`, `Optional[X]`, `typing.List` |
| `references/engineering-core/02-python-backend-dane/references/uv-i-projekt.md` | `uv init/add/sync/lock/run/tool/python`, cały `pyproject.toml` z komentarzem sekcja po sekcji, konfiguracja `ruff`, `mypy`/`ty`, pre-commit, układ katalogów, workspace w monorepo | zakładanie projektu, porządkowanie istniejącego, dodanie zależności, CI |
| `references/engineering-core/02-python-backend-dane/references/fastapi.md` | routery, `Depends`, Pydantic v2 w API, OAuth2/JWT i klucze API, jednolity format błędów, `lifespan`, `BackgroundTasks`, pliki, streaming i SSE, CORS, OpenAPI, wersjonowanie, uruchomienie produkcyjne | każda usługa HTTP w Pythonie |
| `references/engineering-core/02-python-backend-dane/references/async-i-zadania.md` | `asyncio` w praktyce: `TaskGroup`, anulowanie, `timeout`, semafory, `to_thread`, pule procesów, czego NIE robić; wybór między Celery / arq / RQ / APScheduler, ponawianie, idempotencja, harmonogram | kod async, wolne endpointy, kolejki, cron aplikacyjny |
| `references/engineering-core/02-python-backend-dane/references/bazy-i-orm.md` | SQLAlchemy 2.0 (deklaratywnie, sesje, relacje, `selectinload`, transakcje, async), Alembic, psycopg3, pule połączeń, surowy SQL, SQLite vs Postgres w testach, indeksy | model danych, zapytania, migracje, N+1, wolna baza |
| `references/engineering-core/02-python-backend-dane/references/dane.md` | polars vs pandas 3.0, leniwa ewaluacja, Parquet/CSV/JSON, czyszczenie, `join`, agregacje, daty i strefy, dane większe niż RAM, walidacja (Pandera/Pydantic), Jupyter jako narzędzie eksploracji | ETL, raporty, analiza, import plików od klienta |
| `references/engineering-core/02-python-backend-dane/references/testy-pytest.md` | struktura, fixtures i zasięgi, parametryzacja, testy async, `monkeypatch`/`respx`, testcontainers, pokrycie, Hypothesis, szybkość zestawu | pisanie testów, kruche testy, wolne CI |
| `references/engineering-core/02-python-backend-dane/references/wdrozenie-python.md` | Dockerfile wielostopniowy z uv, użytkownik nie-root, env i sekrety, health, logowanie strukturalne, metryki, sygnały i graceful shutdown, VPS vs kontener vs funkcja, cron | wdrożenie, kontener, obserwowalność |
| `references/engineering-core/02-python-backend-dane/references/cli-i-narzedzia.md` | Typer/Click, konfiguracja, wyjście dla człowieka i dla maszyny, kody wyjścia, `rich` postęp, `uv tool`/pipx, skrypty PEP 723 | narzędzie z linii poleceń, skrypt jednorazowy, automatyzacja |

## Co budujesz → co czytasz

```
Python
├── usługa HTTP / API
│   ├── endpointy, walidacja, uwierzytelnianie ...... fastapi.md
│   ├── dostęp do bazy ............................. bazy-i-orm.md
│   ├── wolne operacje w żądaniu ................... async-i-zadania.md
│   └── kontener, health, logi ..................... wdrozenie.md
├── zadanie w tle / kolejka / harmonogram .......... async-i-zadania.md
├── przetwarzanie danych (ETL, raport, import)
│   ├── ramki, pliki, agregacje .................... dane.md
│   ├── zapis do bazy .............................. bazy-i-orm.md
│   └── walidacja wejścia .......................... dane.md + python-nowoczesny.md
├── narzędzie CLI / skrypt ......................... cli-i-narzedzia.md
├── biblioteka do wielokrotnego użytku ............. uv-i-projekt.md + python-nowoczesny.md
├── testy do czegokolwiek .......................... testy-pytest.md
└── nowy projekt od zera ........................... uv-i-projekt.md (+ szkielet niżej)
```

## Szkielet nowego projektu — polecenia obowiązkowe

Każdy nowy projekt Pythona w DANACO zaczyna się dokładnie tak. Nie `python -m venv`,
nie `pip install`, nie `poetry`. uv zastępuje pip, pip-tools, pipx, poetry, pyenv i virtualenv
jednym narzędziem; różnica w czasie instalacji to rząd wielkości, a `uv.lock` jest
międzyplatformowy, czego `requirements.txt` nie daje.

```bash
# 0. uv (raz na maszynę); aktualizacja: uv self update
curl -LsSf https://astral.sh/uv/install.sh | sh

# 1. projekt aplikacyjny (usługa, CLI) — układ src/, z backendem budowania
uv init --package --python 3.14 nazwa-projektu
cd nazwa-projektu

# 1a. biblioteka do publikacji — identycznie, uv init --package już ustawia uv_build
# 1b. jednorazowa analiza bez pakietu:  uv init --bare  (sam pyproject.toml, bez modułu)

# 2. przypnij wersję Pythona dla całego zespołu (tworzy .python-version)
uv python pin 3.14

# 3. zależności produkcyjne
uv add "fastapi[standard]" "pydantic-settings" "sqlalchemy>=2.0.51" "alembic" "psycopg[binary,pool]" "structlog"

# 4. zależności deweloperskie (grupa dev, nie trafia do obrazu produkcyjnego)
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy hypothesis testcontainers respx

# 5. odtworzenie środowiska u kogoś innego / w CI — wyłącznie to
uv sync --frozen          # instaluje dokładnie to, co w uv.lock; błąd, jeśli lock nieaktualny

# 6. uruchamianie czegokolwiek w środowisku projektu
uv run pytest
uv run ruff check --fix .
uv run ruff format .
uv run mypy src
uv run fastapi dev src/nazwa_projektu/main.py     # tryb deweloperski z przeładowaniem

# 7. narzędzia globalne, poza projektem (nie dodawaj ich do zależności)
uv tool install ruff
uvx ruff check .          # uruchomienie bez instalacji
```

Po kroku 4 uzupełnij `pyproject.toml` o sekcje `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]` —
gotowy blok do wklejenia jest w
`references/engineering-core/02-python-backend-dane/references/uv-i-projekt.md`. Bez tego bloku
`ruff` od wersji 0.16 włączy 413 reguł domyślnych i zaleje projekt zgłoszeniami przy pierwszym
uruchomieniu; konfiguracja ustawia świadomy podzbiór.

Układ katalogów, który wychodzi i którego się trzymamy:

```
nazwa-projektu/
├── pyproject.toml          jedyne źródło konfiguracji: zależności, lint, typy, testy
├── uv.lock                 commitowany zawsze; nie edytowany ręcznie
├── .python-version         3.14
├── src/nazwa_projektu/     kod; układ src/ wymusza testowanie zainstalowanej paczki
│   ├── __init__.py
│   ├── main.py             punkt wejścia ASGI / CLI
│   ├── config.py           Settings (pydantic-settings), jedno miejsce na env
│   ├── api/                routery FastAPI
│   ├── domain/             logika, bez importów z api/ i db/
│   ├── db/                 modele SQLAlchemy, sesje, repozytoria
│   └── tasks/              zadania w tle
├── tests/                  lustro src/, plus conftest.py
├── migrations/             Alembic
└── Dockerfile              wielostopniowy, uv w etapie budowania
```

## Wybory domyślne DANACO

Bierz to z tabeli, chyba że masz powód, żeby zrobić inaczej — i wtedy napisz ten powód
w kodzie albo w opisie zmiany. Dyskusja o alternatywach należy do plików referencyjnych.

| Potrzeba | Domyślnie | Alternatywa i kiedy |
|---|---|---|
| Menedżer projektu | `uv` | brak; poetry tylko w projektach, które już go mają |
| Lint + format | `ruff` (jedno narzędzie) | brak; nie dokładamy black/isort/flake8 |
| Kontrola typów | `mypy` w trybie strict | `ty` gdy liczy się czas w CI — beta, więc obok mypy, nie zamiast |
| Framework HTTP | FastAPI | Starlette gdy nie ma modeli i OpenAPI; Litestar tylko jeśli zespół go zna |
| Walidacja na granicy | Pydantic v2 | `msgspec` gdy profil pokazuje, że walidacja jest wąskim gardłem |
| Klient HTTP | `httpx` | `requests` tylko w kodzie synchronicznym, którego nie ruszamy |
| ORM | SQLAlchemy 2.0 (styl deklaratywny) | surowy SQL przez `text()` dla raportów i zapytań analitycznych |
| Baza | PostgreSQL + `psycopg` 3 | SQLite dla narzędzi jednostanowiskowych i lokalnych danych |
| Migracje | Alembic | brak |
| Ramki danych | polars | pandas gdy biblioteka trzecia wymaga; DuckDB gdy zadanie jest SQL-owe |
| Format plików pośrednich | Parquet | CSV wyłącznie na wejściu/wyjściu do świata zewnętrznego |
| Kolejka zadań | arq (stos async) / Celery (stos sync, wiele workerów) | RQ dla prostych kolejek; APScheduler tylko dla harmonogramu w procesie |
| Serwer ASGI | uvicorn pod gunicornem | granian gdy zależy na wydajności i zespół to obsłuży |
| Testy | pytest | brak |
| Logi | `structlog` → JSON na stdout | `logging` z `JSONFormatter` gdy nie chcemy zależności |
| CLI | Typer | Click gdy potrzebne grupy i pluginy, których Typer nie wystawia |
| Kwoty pieniężne | `decimal.Decimal` | nigdy `float` |
| Serializacja JSON w gorącej ścieżce | `orjson` | biblioteka standardowa wszędzie indziej |

## Dwa wzorce startowe

Minimalna usługa, która się uruchamia (`uv run fastapi dev src/app/main.py`):

```python
# src/app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")
    database_url: str = "postgresql+psycopg://localhost/app"
    debug: bool = False


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # tutaj: pula połączeń, klient HTTP, rozgrzewka cache
    yield
    # tutaj: zamknięcie zasobów


app = FastAPI(title="app", version="1.0.0", lifespan=lifespan)


class Echo(BaseModel):
    message: str = Field(min_length=1, max_length=280)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo", response_model=Echo)
async def echo(payload: Echo) -> Echo:
    return payload
```

Skrypt jednoplikowy z zależnościami w nagłówku (`uv run analiza.py dane.parquet`) —
bez projektu, bez wirtualnego środowiska do zakładania ręcznie:

```python
# /// script
# requires-python = ">=3.13"
# dependencies = ["polars>=1.43", "typer>=0.27"]
# ///
import sys
from pathlib import Path

import polars as pl
import typer


def main(plik: Path, kolumna: str = "kwota") -> None:
    if not plik.exists():
        typer.echo(f"brak pliku: {plik}", err=True)
        raise typer.Exit(code=2)
    lf = pl.scan_parquet(plik)
    wynik = lf.select(
        pl.col(kolumna).sum().alias("suma"),
        pl.col(kolumna).mean().alias("srednia"),
        pl.len().alias("wierszy"),
    ).collect()
    typer.echo(wynik.write_json())


if __name__ == "__main__":
    typer.run(main)
    sys.exit(0)
```

## Procedura

1. **Ustal, co to za rzecz.** Usługa HTTP, zadanie wsadowe, CLI, biblioteka czy jednorazowy skrypt.
   Od tego zależy wszystko dalej, łącznie z tym, czy w ogóle potrzebny jest projekt (skrypt
   jednoplikowy z PEP 723 często wystarcza —
   `references/engineering-core/02-python-backend-dane/references/cli-i-narzedzia.md`).
2. **Sprawdź, w czym pracujesz.** `cat pyproject.toml`, `ls uv.lock requirements.txt poetry.lock`,
   `python --version`. Istniejący projekt na poetry/pip: nie migruj go przy okazji innego
   zadania — zgłoś to jako osobną robotę.
3. **Nowy projekt: wykonaj szkielet powyżej co do polecenia.** Istniejący: dopasuj się do
   konwencji, które tam są, nawet jeśli nie są nasze.
4. **Zdefiniuj typy danych wejścia i wyjścia, zanim napiszesz logikę.** Pydantic dla granic systemu
   (HTTP, pliki od klienta, env), dataclass dla struktur wewnętrznych, `TypedDict` dla kształtów
   słowników z zewnątrz.
   `references/engineering-core/02-python-backend-dane/references/python-nowoczesny.md`.
5. **Napisz kod z pełnymi adnotacjami typów.** `Any` tylko z komentarzem, dlaczego.
6. **Wczytaj plik referencyjny dla tego obszaru przed pisaniem, nie po.** Konkretne API
   FastAPI, SQLAlchemy 2.0 i pandas 3.0 zmieniły się na tyle, że kod pisany z pamięci
   będzie używał usuniętych wywołań.
7. **Napisz testy.** Minimum: ścieżka szczęśliwa i jeden przypadek błędu na publiczną funkcję.
   Przy przetwarzaniu danych — test na pustym wejściu.
8. **Uruchom bramkę jakości**: `uv run ruff format . && uv run ruff check --fix . &&
   uv run mypy src && uv run pytest`. Cztery polecenia, wszystkie muszą przejść.
9. **Sprawdź, czy kod się uruchamia.** Nie „powinien działać”. Uruchom go.

## Twarde reguły

1. **`uv` do wszystkiego.** Zero `pip install` w instrukcjach i w Dockerfile, zero
   `python -m venv`, zero `poetry`, zero `conda`. Konsekwencja złamania: brak `uv.lock`,
   środowiska rozjeżdżają się między maszynami, „u mnie działa”.
2. **`uv.lock` w repozytorium, `uv sync --frozen` w CI i w obrazie.** Bez `--frozen` uv
   po cichu przelicza lock i wdrażasz inne wersje niż testowane.
3. **Adnotacje typów wszędzie w kodzie produkcyjnym.** Sygnatury funkcji i pola klas.
   Bez tego `mypy`/`ty` nic nie wykryje, a karta nie ma jak pomóc.
4. **Pydantic v2 na granicy, dataclass w środku.** Nie waliduj tego samego trzy razy; nie
   przenoś modeli Pydantic przez całą aplikację jako uniwersalnych struktur.
5. **Zero blokujących wywołań w korutynie.** `time.sleep`, `requests`, sterowniki
   synchroniczne, `open().read()` na dużym pliku — wszystko to zatrzymuje całą pętlę dla
   wszystkich żądań. Zamiana: `asyncio.sleep`, `httpx.AsyncClient`, `asyncio.to_thread`.
   Konsekwencja złamania: usługa pod obciążeniem stoi, a profiler nie pokazuje nic dziwnego.
6. **Sekrety wyłącznie ze zmiennych środowiskowych przez `Settings`.** Zero kluczy w kodzie,
   zero w `pyproject.toml`, zero w obrazie kontenera. Plik `.env` tylko lokalnie i w `.gitignore`.
7. **Bez `except:` i bez `except Exception: pass`.** Łap konkretny typ. Jeśli musisz złapać
   szeroko — zaloguj z `exc_info` i podnieś dalej albo zwróć jawny błąd.
8. **Bez mutowalnych wartości domyślnych** (`def f(x=[])`, `dataclass(field=[])`).
   `None` + sprawdzenie albo `field(default_factory=list)`.
9. **`pathlib.Path` zamiast `os.path`, `datetime` ze strefą zamiast naiwnego.**
   `datetime.now(UTC)`, nigdy `datetime.utcnow()` — usunięte w 3.14 po deprecjacji.
10. **Logowanie przez `logging`/`structlog`, nigdy `print` w kodzie usługi.** `print`
    dopuszczalny wyłącznie w CLI jako wyjście dla użytkownika.
11. **Kod ma być uruchamialny.** Żadnych `pass  # TODO`, żadnych `...` w ciele funkcji,
    którą oddajesz, żadnych wymyślonych nazw funkcji z bibliotek. Jeśli nie jesteś pewien
    API — sprawdź w źródle albo w sieci.
12. **Nowy kod celuje w Python 3.13+.** Składnia z 3.14 (`t-string`, `except A, B:`) tylko
    gdy `requires-python = ">=3.14"` jest w `pyproject.toml`.

## Najczęstsze błędy modelu w Pythonie (sierpień 2026)

Rzeczy, które kod pisany z pamięci robi źle, bo API zmieniło się niedawno:

| Zapis przestarzały | Poprawny dziś | Od kiedy |
|---|---|---|
| `@app.on_event("startup")` | `lifespan=` w `FastAPI(...)` | usunięte w Starlette 1.0 (2026-03) |
| `query = session.query(User).filter(...)` | `session.execute(select(User).where(...))` | SQLAlchemy 2.0 |
| `Column(Integer, primary_key=True)` | `Mapped[int] = mapped_column(primary_key=True)` | SQLAlchemy 2.0 |
| `class Config:` w modelu Pydantic | `model_config = ConfigDict(...)` | Pydantic v2 |
| `.dict()`, `.json()`, `parse_obj()` | `.model_dump()`, `.model_dump_json()`, `.model_validate()` | Pydantic v2 |
| `df["a"][df["b"] > 5] = 1` | `df.loc[df["b"] > 5, "a"] = 1` | pandas 3.0 — łańcuchowe przypisanie nie działa |
| `dtype: object` dla tekstu | dtype `str` domyślnie | pandas 3.0 |
| `[tool.pytest.ini_options]` | `[tool.pytest]` (natywny TOML) | pytest 9.0 |
| `@pytest.mark.asyncio` bez konfiguracji | `asyncio_mode = "auto"` w konfiguracji | pytest-asyncio 1.x |
| `datetime.utcnow()` | `datetime.now(UTC)` | usunięte w 3.14 |
| `typing.List`, `typing.Dict`, `Optional[X]` | `list`, `dict`, `X \| None` | 3.9 / 3.10 |
| `TypeVar("T")` + `Generic[T]` | `def f[T](x: T) -> T` | PEP 695, 3.12 |
| `psycopg2` | `psycopg` (3.x) | |
| `pip install -r requirements.txt` | `uv sync --frozen` | |

## Kontrola przed oddaniem

- [ ] `uv run ruff format .` — bez zmian po uruchomieniu.
- [ ] `uv run ruff check .` — zero zgłoszeń, albo każde wyciszenie ma `# noqa: KOD` z powodem.
- [ ] `uv run mypy src` (lub `uv run ty check`) — zero błędów.
- [ ] `uv run pytest` — zielono; nowy kod ma testy, nie tylko stary.
- [ ] Kod faktycznie uruchomiony, nie tylko przeczytany.
- [ ] Zależności dodane przez `uv add`, `uv.lock` zaktualizowany i w commicie.
- [ ] Zero sekretów w kodzie i w plikach śledzonych przez git.
- [ ] W kodzie async: żadnego wywołania synchronicznego I/O bez `to_thread`.
- [ ] Zapytania do bazy przez ORM nie mają N+1 (sprawdzone `echo=True` albo `selectinload`).
- [ ] Wyjątki mają konkretne typy; nic nie jest połykane po cichu.
- [ ] `datetime` ze strefą; `Decimal` do kwot, nie `float`.
- [ ] Jeśli powstał obraz: nie-root, wielostopniowy, `uv sync --frozen --no-dev`.
- [ ] Wersje w tabeli odniesienia zgadzają się z tym, co jest w `uv.lock`; jeśli nie —
      napisano to jawnie zamiast udawać.
