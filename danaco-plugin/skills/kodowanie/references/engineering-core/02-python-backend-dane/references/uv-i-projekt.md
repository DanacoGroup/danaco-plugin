# uv, pyproject.toml, ruff, kontrola typów — sierpień 2026

uv **0.12.1**, ruff **0.16.1**, mypy **2.3.0**, ty **0.0.66** (beta), pre-commit **4.6.1**.

## Czy uv wyparł pip i poetry

Praktycznie tak, w tym sensie, że w 2026 jest domyślnym wyborem dla nowych projektów
i pokrywa zakres pip + pip-tools + pipx + poetry + pyenv + virtualenv jednym binarium bez
zależności od Pythona. Pip nie zniknął — pozostaje warstwą, na której stoją stare pipeline'y
i wiele obrazów bazowych. Zasada praktyczna:

- Nowy projekt → uv, bez wyjątków.
- Projekt na poetry, który działa → nie migruj przy okazji; migracja to osobne zadanie
  (`uv init` w kopii, przepisanie `[tool.poetry.dependencies]` na `[project.dependencies]`,
  porównanie rozwiązanych wersji).
- `requirements.txt` w projekcie, który dostajesz → `uv add -r requirements.txt`, potem
  `uv lock`, potem usunięcie pliku. Jeśli coś na zewnątrz wymaga `requirements.txt`:
  `uv export --format requirements-txt --no-dev -o requirements.txt` w CI, nie ręcznie.
- uv obsługuje też standardowy `pylock.toml` (PEP 751): `uv export --format pylock.toml`.
  `uv.lock` pozostaje formatem roboczym — jest bogatszy i międzyplatformowy.

## Polecenia uv, których faktycznie używasz

### Projekt

```bash
uv init --package --python 3.14 nazwa      # układ src/, backend uv_build, pakiet
uv init --app nazwa                        # aplikacja bez pakowania (od 0.12 też z build-system)
uv init --lib nazwa                        # biblioteka
uv init --bare                             # sam pyproject.toml, bez modułu i README
uv python pin 3.14                         # zapisuje .python-version

uv add fastapi "sqlalchemy>=2.0.51"        # dodaje do [project.dependencies] i instaluje
uv add --dev pytest ruff mypy              # grupa dev ([dependency-groups])
uv add --group docs mkdocs                 # dowolna nazwana grupa
uv add --optional pdf reportlab            # extra ([project.optional-dependencies])
uv add "polars[all]>=1.43"                 # z extras
uv add git+https://github.com/x/y@v1.2.3   # ze źródła
uv add --editable ../wspolna-biblioteka    # lokalna zależność w trybie edycji
uv remove fastapi

uv lock                                    # przelicza uv.lock
uv lock --upgrade                          # podnosi wszystko w granicach ograniczeń
uv lock --upgrade-package pydantic         # podnosi jeden pakiet
uv lock --check                            # błąd, jeśli lock nie odpowiada pyproject.toml

uv sync                                    # środowisko = lock (domyślnie z grupą dev)
uv sync --frozen                           # bez przeliczania locka — to jest tryb CI
uv sync --frozen --no-dev                  # to jest tryb obrazu produkcyjnego
uv sync --all-extras --all-groups          # pełne środowisko deweloperskie

uv run pytest                              # uruchomienie w środowisku projektu
uv run --no-sync python -c "import app"    # bez sprawdzania środowiska (szybciej w pętli)
uv run --with ipython ipython              # jednorazowa zależność, bez dodawania do projektu
uv run --group docs mkdocs serve

uv tree                                    # drzewo zależności — do diagnozy konfliktów
uv tree --package pydantic --invert        # kto ciągnie pydantic
uv export --format requirements-txt --no-dev -o requirements.txt
uv build                                   # sdist + wheel do dist/
uv publish                                 # na PyPI (token w UV_PUBLISH_TOKEN)
```

### Wersje Pythona

```bash
uv python list                             # co jest dostępne i co zainstalowane
uv python install 3.14 3.13                # pobiera interpretery (nie systemowe)
uv python install 3.14t                    # build free-threaded
uv python find 3.14                        # ścieżka do interpretera
uv venv --python 3.13                      # ręczne środowisko, gdy nie ma projektu
```

uv pobiera własne buildy CPythona (python-build-standalone). Nie musisz mieć Pythona w systemie ani
pyenv. W obrazie Dockera to samo — patrz
`references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.

### Narzędzia globalne

```bash
uv tool install ruff                       # instaluje w izolowanym środowisku, dodaje do PATH
uv tool install "harlequin[postgres]"
uv tool list
uv tool upgrade --all
uvx ruff check .                           # uruchom raz, bez instalacji (= uv tool run)
uvx --from httpie http GET example.com     # gdy nazwa polecenia ≠ nazwa pakietu
```

Narzędzie deweloperskie, którego używa cały zespół (ruff, mypy) → do `--dev` w projekcie,
żeby wersja była wspólna. Narzędzie osobiste (harlequin, httpie, ipython) → `uv tool`.

### Skrypty jednoplikowe (PEP 723)

```bash
uv init --script analiza.py --python 3.13
uv add --script analiza.py "polars>=1.43" typer
uv run analiza.py dane.parquet
```

Nagłówek w pliku, uv buduje środowisko w locie i cache'uje je. Szczegóły w
`references/engineering-core/02-python-backend-dane/references/cli-i-narzedzia.md`.

## `pyproject.toml` w całości

Poniższy plik jest kompletny i działa. Każda sekcja skomentowana.

```toml
# --- Metadane pakietu (PEP 621). Jedno miejsce prawdy o projekcie. -------------
[project]
name = "danaco-uslugi"                 # nazwa dystrybucji; moduł = danaco_uslugi
version = "0.3.0"                      # albo dynamic = ["version"], patrz niżej
description = "Usługa rozliczeń DANACO"
readme = "README.md"
requires-python = ">=3.13"             # dolna granica; wpływa na reguły ruff i mypy
license = "MIT"                        # od PEP 639 to napis SPDX, nie tabela
authors = [{ name = "DANACO", email = "dev@danacogroup.com.pl" }]
keywords = ["rozliczenia", "api"]
classifiers = ["Private :: Do Not Upload"]   # blokuje przypadkową publikację na PyPI

# Zależności produkcyjne. Górna granica TYLKO gdy wiesz o niezgodności —
# nadmiarowe "<2" blokuje aktualizacje całemu drzewu zależności.
dependencies = [
  "fastapi[standard]>=0.141",
  "pydantic>=2.13",
  "pydantic-settings>=2.14",
  "sqlalchemy>=2.0.51,<2.1",           # 2.1 w becie — świadome ograniczenie
  "alembic>=1.18",
  "psycopg[binary,pool]>=3.3",
  "structlog>=26.1",
  "httpx>=0.28",
]

# Extras: instalowane na żądanie przez odbiorcę pakietu (pip install pakiet[pdf]).
[project.optional-dependencies]
pdf = ["reportlab>=4.2"]
excel = ["openpyxl>=3.1"]

# Punkty wejścia — polecenia dostępne po instalacji pakietu.
[project.scripts]
danaco = "danaco_uslugi.cli:app"

[project.urls]
Repository = "https://github.com/danaco/uslugi"

# --- Grupy zależności deweloperskich (PEP 735). ---------------------------------
# NIE trafiają do wydanego pakietu, w przeciwieństwie do optional-dependencies.
[dependency-groups]
dev = [
  "pytest>=9.1",
  "pytest-asyncio>=1.4",
  "pytest-cov>=7.1",
  "ruff>=0.16",
  "mypy>=2.3",
  "hypothesis>=6.165",
  "respx>=0.23",
  "testcontainers[postgres]>=4.15",
]
docs = ["mkdocs-material>=9.5"]

# --- Backend budowania. uv_build jest najszybszy dla czystego Pythona. ----------
[build-system]
requires = ["uv_build>=0.12.1,<0.13"]  # zawsze z górną granicą
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = "src"                    # domyślnie src/
module-name = "danaco_uslugi"          # domyślnie znormalizowana nazwa projektu
# source-include = ["migrations/**"]   # co dołożyć do sdist
# wheel-exclude = ["**/tests/**"]

# --- Ustawienia uv dla tego projektu ------------------------------------------
[tool.uv]
default-groups = ["dev"]               # co instaluje samo `uv sync`
package = true                         # projekt jest instalowany do środowiska
# required-version = ">=0.12"          # wymuszenie wersji uv w zespole
# python-preference = "only-managed"   # ignoruj interpretery systemowe

# Nadpisania źródeł: lokalne pakiety, gałęzie git, indeksy prywatne.
[tool.uv.sources]
# danaco-wspolne = { workspace = true }
# jakas-lib = { git = "https://github.com/org/lib", tag = "v2.1.0" }

[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple"
default = true

# --- ruff: lint + format, jedno narzędzie -------------------------------------
[tool.ruff]
target-version = "py313"               # musi zgadzać się z requires-python
line-length = 100
src = ["src", "tests"]                 # do rozpoznania importów pierwszej strony
extend-exclude = ["migrations/versions"]

[tool.ruff.lint]
# Od ruff 0.16 domyślnie włączonych jest 413 reguł. Jawna lista poniżej ustawia
# świadomy zestaw i nie zmienia się pod nami przy aktualizacji ruffa.
select = [
  "E", "W",     # pycodestyle
  "F",          # pyflakes — błędy rzeczywiste
  "I",          # isort — kolejność importów
  "UP",         # pyupgrade — składnia do target-version
  "B",          # flake8-bugbear — pułapki logiczne
  "C4",         # comprehensions
  "SIM",        # uproszczenia
  "RET",        # return
  "PTH",        # użyj pathlib zamiast os.path
  "DTZ",        # datetime bez strefy czasowej
  "ASYNC",      # pułapki asyncio (blokujące wywołania w korutynie)
  "S",          # bandit — bezpieczeństwo
  "T20",        # print/pprint w kodzie
  "ARG",        # nieużywane argumenty
  "TID",        # zakazane importy względne
  "RUF",        # reguły własne ruffa
  "N",          # nazewnictwo PEP 8
  "ANN",        # brakujące adnotacje
  "LOG", "G",   # poprawne użycie logging
]
ignore = [
  "E501",       # długość linii pilnuje formatter
  "ANN401",     # Any dozwolony tam, gdzie jest świadomy
  "S101",       # assert dozwolony (w testach); w kodzie łapie to review
  "B008",       # Depends()/Query() w wartości domyślnej — wzorzec FastAPI
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ANN201", "ARG001", "S105", "S106"]
"migrations/**" = ["ANN", "N", "F401"]
"__init__.py" = ["F401"]               # reeksporty

[tool.ruff.lint.isort]
known-first-party = ["danaco_uslugi"]
combine-as-imports = true

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"       # zakaz "from .." — dozwolone tylko "from ."

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true           # formatuje przykłady w docstringach
skip-magic-trailing-comma = false

# --- mypy ---------------------------------------------------------------------
[tool.mypy]
python_version = "3.13"
strict = true                          # włącza komplet: disallow_untyped_defs itd.
warn_unreachable = true
show_error_codes = true
pretty = true
files = ["src", "tests"]
# mypy 2.0: --local-partial-types, --strict-bytes i --allow-redefinition
# są już domyślnie włączone; nie trzeba ich wypisywać.
# num_workers = 8                      # przyspieszenie na dużych repo (mypy 2.0+)

[[tool.mypy.overrides]]
module = ["jakas_biblioteka_bez_typow.*"]
ignore_missing_imports = true

# --- pytest (pytest 9 czyta natywny TOML: [tool.pytest], nie ini_options) ------
[tool.pytest]
testpaths = ["tests"]
addopts = ["--strict-markers", "--strict-config", "-ra"]
asyncio_mode = "auto"                  # pytest-asyncio: bez dekoratora na każdym teście
markers = [
  "slow: test wolniejszy niż 1 s",
  "integration: wymaga bazy lub sieci",
]
filterwarnings = ["error", "ignore::DeprecationWarning:jakas_stara_lib.*"]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*"]

[tool.coverage.report]
exclude_also = [
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
  "@overload",
]
```

Uwagi, które kosztują czas, jeśli się o nich nie wie:

- `[tool.pytest]` z natywnymi typami TOML działa **od pytest 9.0**. Na pytest 8 nadal
  `[tool.pytest.ini_options]` z wartościami tekstowymi. Nie mieszaj obu tabel — pytest 9
  przy obecności obu użyje nowej i po cichu zignoruje starą.
- `dependency-groups` (PEP 735) to nie to samo co `optional-dependencies`. Grupy są
  wyłącznie dla dewelopera i nie da się ich zainstalować z wydanego pakietu.
- Wersję można wyliczać z kodu:
  `dynamic = ["version"]` + `[tool.uv.build-backend] ... ` albo prościej — trzymaj ją
  ręcznie i podnoś w commicie wydania; automatyzacja z gita psuje reprodukowalność sdist.
- `line-length = 100` w `[tool.ruff]` i ignorowanie `E501` w lincie to celowa para:
  formatter łamie linie, linter nie krzyczy na te, których złamać się nie da (długi URL).

## Struktura katalogów

### Aplikacja (usługa HTTP, worker)

```
projekt/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml           tylko zależności lokalne: postgres, redis
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── src/danaco_uslugi/
│   ├── __init__.py
│   ├── main.py                  tworzy obiekt ASGI, nic więcej
│   ├── config.py                Settings — jedyne miejsce czytające os.environ
│   ├── logging.py               konfiguracja structlog
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              zależności współdzielone (sesja, użytkownik)
│   │   ├── errors.py            handlery wyjątków → jednolity JSON
│   │   └── v1/
│   │       ├── faktury.py       APIRouter
│   │       └── zdrowie.py
│   ├── domain/                  logika; NIE importuje z api/ ani db/
│   │   ├── faktura.py
│   │   └── bledy.py
│   ├── db/
│   │   ├── base.py              DeclarativeBase, konwencje nazw
│   │   ├── models.py
│   │   ├── session.py           engine, sessionmaker
│   │   └── repo.py              zapytania
│   ├── tasks/                   zadania w tle
│   └── py.typed                 pusty plik — sygnał, że pakiet ma typy
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

Reguła kierunku zależności: `api → domain ← db`. `domain` nie importuje nic z `api` ani
`db`; jeśli potrzebuje zapisu, dostaje `Protocol` repozytorium jako argument. Złamanie tego
oznacza, że nie da się przetestować logiki bez bazy i bez klienta HTTP.

### Biblioteka

Ten sam układ `src/`, bez `api/` i `db/`, z `py.typed`, z `[project.scripts]` tylko jeśli
faktycznie wystawia polecenie. Układ `src/` nie jest ozdobą: bez niego `import pakiet`
w testach trafia w katalog roboczy, a nie w zainstalowaną paczkę, i błąd w liście plików
pakietu wychodzi dopiero u odbiorcy.

## Monorepo: workspace uv

Jeden `uv.lock` dla wszystkich pakietów, jedno środowisko, wspólne rozwiązanie wersji.

```
monorepo/
├── pyproject.toml            korzeń: tylko definicja workspace
├── uv.lock                   jeden dla całości
├── packages/
│   ├── wspolne/pyproject.toml
│   └── klient-ksef/pyproject.toml
└── apps/
    ├── api/pyproject.toml
    └── worker/pyproject.toml
```

Korzeń:

```toml
[project]
name = "danaco-monorepo"
version = "0.0.0"
requires-python = ">=3.13"
dependencies = []

[tool.uv.workspace]
members = ["packages/*", "apps/*"]
exclude = ["packages/archiwum"]

[dependency-groups]
dev = ["pytest>=9.1", "ruff>=0.16", "mypy>=2.3"]

[tool.ruff]                  # konfiguracja narzędzi w korzeniu, dziedziczona niżej
target-version = "py313"
line-length = 100
```

`apps/api/pyproject.toml`:

```toml
[project]
name = "danaco-api"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["danaco-wspolne", "fastapi[standard]>=0.141"]

[tool.uv.sources]
danaco-wspolne = { workspace = true }   # bierz z workspace, nie z PyPI

[build-system]
requires = ["uv_build>=0.12.1,<0.13"]
build-backend = "uv_build"
```

Polecenia:

```bash
uv sync                        # instaluje wszystkich członków workspace
uv run --package danaco-api pytest
uv add --package danaco-api httpx
uv lock                        # jeden lock dla całości
```

Kiedy workspace, a kiedy osobne repozytoria: workspace ma sens, gdy pakiety wydawane są
razem i mają wspólny cykl życia. Jeśli `klient-ksef` ma własne wydania i własnych odbiorców,
lepiej osobne repo i zwykła zależność wersjonowana — workspace wymusza jedną rozdzielczość
wersji na wszystko, co przy rozjeżdżających się cyklach jest kłopotem, a nie pomocą.

## Kontrola typów: mypy czy ty

| | mypy 2.3 | ty 0.0.66 |
|---|---|---|
| Dojrzałość | referencyjna, pełna specyfikacja typowania | beta od 2025-12, stabilne zapowiadane na 2026 |
| Szybkość | wolna; od 2.0 `--num-workers N` daje do ~5× na 8 procesach | ~20× szybszy od mypy w pomiarach Astral |
| Integracja | wtyczki (SQLAlchemy, Pydantic), szeroko wspierana | LSP w komplecie, wtyczek brak |
| Zalecenie DANACO | **bramka w CI** | uruchamiaj lokalnie dla szybkiego sprzężenia |

```bash
uv run mypy src                        # bramka
uv run mypy --num-workers 8 src        # duże repo
uvx ty check src                       # szybki przebieg lokalny
```

Konfiguracja ty (gdy go dodajesz):

```toml
[tool.ty.environment]
python-version = "3.13"

[tool.ty.rules]
possibly-unresolved-reference = "error"
```

Nie ustawiaj `ty` jako jedynej bramki, dopóki jest w becie — brakujące fragmenty
specyfikacji potrafią przepuścić błąd, który mypy łapie. Odwrotny układ (ty jako jedyna
szybka bramka lokalna, mypy w CI) jest bezpieczny.

Trzecia opcja, `pyrefly` (Meta, 1.2.0), jest już po 1.0 i również szybka — jeśli projekt
jej używa, nie migruj bez powodu.

## pre-commit

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.1
    hooks:
      - id: ruff-check
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.12.1
    hooks:
      - id: uv-lock            # pilnuje, że uv.lock pasuje do pyproject.toml

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: check-toml
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: detect-private-key

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false
```

```bash
uv tool install pre-commit
pre-commit install
pre-commit run --all-files
```

mypy jako hook `local` z `uv run`, a nie z repozytorium mirrors-mypy: hook z mirrorem
tworzy własne środowisko bez zależności projektu i zgłasza fałszywe „module has no
attribute” na wszystkim, co jest w `uv.lock`.

## CI (GitHub Actions)

```yaml
name: ci
on: [push, pull_request]

jobs:
  jakosc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.12.1"        # przypięte — uv aktualizuje się szybko
          enable-cache: true
      - run: uv sync --frozen --all-groups
      - run: uv run ruff format --check .
      - run: uv run ruff check --output-format=github .
      - run: uv run mypy src
      - run: uv run pytest --cov --cov-report=term-missing
```

`--frozen` jest istotne: bez niego uv przeliczy lock w CI i przetestujesz inny zestaw
wersji niż ten, który wdrożysz.

## Diagnostyka typowych problemów

| Objaw | Przyczyna | Działanie |
|---|---|---|
| `uv sync` zmienia `uv.lock` w CI | brak `--frozen` | dodaj `--frozen`, `uv lock` rób lokalnie |
| „No solution found when resolving dependencies” | konflikt granic wersji | `uv tree --invert --package <x>` żeby zobaczyć, kto co wymusza; poluzuj własne `<` |
| ruff nagle zgłasza setki błędów po aktualizacji | 0.16 podniósł domyślny zestaw z 59 do 413 reguł | ustaw jawny `select` w `[tool.ruff.lint]` |
| mypy nie widzi typów zainstalowanego pakietu | brak `py.typed` w tym pakiecie | `[[tool.mypy.overrides]] ignore_missing_imports = true` dla niego |
| import własnego pakietu w teście nie działa | brak układu `src/` albo `package = false` | `uv sync` po `uv init --package`; sprawdź `[tool.uv] package = true` |
| różne wersje u dwóch osób | ktoś użył `pip install` w środowisku projektu | `uv sync --frozen` odtwarza stan; nie mieszaj pip i uv |
| `uv run` wolne przy każdym wywołaniu | sprawdzanie środowiska | `uv run --no-sync` w pętli deweloperskiej |
