# Testy: pytest 9, Hypothesis, testcontainers — sierpień 2026

pytest **9.1.1**, pytest-asyncio **1.4.0**, pytest-cov **7.1.0**, hypothesis **6.165.0**,
testcontainers **4.15.0**, respx **0.23.1**, httpx **0.28.1**.

## Co zmieniło pytest 9.0

| Zmiana | Skutek |
|---|---|
| **Natywna konfiguracja TOML**: `[tool.pytest]` w `pyproject.toml`, albo `pytest.toml` | koniec z `[tool.pytest.ini_options]` i wartościami wyłącznie tekstowymi; typy TOML działają wprost |
| Minimum Python **3.10** | 3.9 odpada |
| `PytestRemovedIn9Warning` → **błąd** | kod korzystający z rzeczy deprecjonowanych w 8.x przestaje działać |
| **Natywne subtesty** | asercje w pętli bez przerywania na pierwszym błędzie, gdy parametryzacja niemożliwa na etapie zbierania |
| Opcja `strict` | jedno ustawienie włącza `strict_config`, `strict_markers`, `strict_parametrization_ids`, `strict_xfail` |
| `pytest a/ a/b` | traktowane jak `pytest a` — koniec z podwójnym uruchamianiem testów |
| Wykrywanie CI wymaga **niepustej** wartości `$CI`/`$BUILD_NUMBER` | `CI=` (puste) nie włącza już trybu CI |
| 9.1: `pytest.register_fixture()`, `--max-warnings`, `pytest.approx` dla `datetime`/`timedelta` | |

Konfiguracja (w `pyproject.toml`):

```toml
[tool.pytest]
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--strict-config"]
asyncio_mode = "auto"
markers = [
  "slow: wolniejszy niż 1 s",
  "integration: wymaga bazy lub sieci",
  "e2e: pełna ścieżka przez API",
]
filterwarnings = ["error"]              # ostrzeżenie = błąd testu
```

Nie umieszczaj równocześnie `[tool.pytest]` i `[tool.pytest.ini_options]` — pytest 9 użyje
nowej tabeli i po cichu zignoruje starą, przez co część ustawień zniknie.

## Struktura

```
tests/
├── conftest.py              fixtures globalne
├── unit/                    bez I/O, bez bazy, bez sieci; milisekundy
│   ├── test_faktura.py
│   └── test_walidacja.py
├── integration/             baza w kontenerze, prawdziwe zapytania
│   ├── conftest.py
│   └── test_repo_faktur.py
└── e2e/                     przez klienta HTTP, cała aplikacja
    └── test_api_faktur.py
```

Nazewnictwo: pliki `test_*.py`, funkcje `test_*`, klasy `Test*` bez `__init__`. Jeden plik
testowy na jeden moduł produkcyjny — łatwiej znaleźć, gdzie brakuje pokrycia.

Nazwa testu opisuje warunek i oczekiwanie, nie nazwę funkcji:
`test_faktura_bez_pozycji_odrzucona`, nie `test_utworz_fakture_2`.

## Fixtures i zasięgi

```python
# tests/conftest.py
from collections.abc import AsyncIterator, Iterator
from decimal import Decimal

import pytest


@pytest.fixture(scope="session")
def dane_referencyjne() -> dict[str, str]:
    """Zasięg session: liczone raz na cały przebieg. Tylko dla obiektów NIEZMIENNYCH."""
    return {"waluta": "PLN", "kraj": "PL"}


@pytest.fixture
def faktura() -> Faktura:
    """Zasięg function (domyślny): świeży obiekt na każdy test."""
    return Faktura(
        numer="FV/2026/001",
        kwota_netto=Decimal("1000.00"),
        stawka_vat=Decimal("0.23"),
    )


@pytest.fixture
def katalog_tymczasowy(tmp_path) -> Iterator[Path]:
    """tmp_path jest wbudowany; ten pokazuje wzorzec sprzątania."""
    katalog = tmp_path / "dane"
    katalog.mkdir()
    yield katalog
    # sprzątanie po yield — wykona się nawet gdy test padnie
```

| Zasięg | Kiedy | Ryzyko |
|---|---|---|
| `function` (domyślny) | wszystko, co test może zmodyfikować | brak |
| `class` | wspólny stan grupy testów w klasie | przeciek stanu między testami |
| `module` | drogi zasób używany przez cały plik | jak wyżej |
| `session` | kontener z bazą, wczytany duży plik, obiekt niezmienny | test modyfikujący zasób psuje kolejne, a objaw zależy od kolejności |

Reguła: zasięg szerszy niż `function` wolno nadawać wyłącznie obiektom, których test nie
modyfikuje, albo takim, które mają jawny mechanizm resetu (transakcja z rollbackiem).

Fixture automatyczny — wyłącznie do izolacji, nie do wstrzykiwania danych:

```python
@pytest.fixture(autouse=True)
def czysty_stan(monkeypatch) -> None:
    monkeypatch.setenv("APP_SRODOWISKO", "test")
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
```

Fixture z parametrami (fabryka) zamiast pięciu podobnych fixture'ów:

```python
@pytest.fixture
def buduj_fakture():
    def _buduj(**nadpisania) -> Faktura:
        dane = {"numer": "FV/1", "kwota_netto": Decimal("100"), "status": "szkic"}
        return Faktura(**(dane | nadpisania))
    return _buduj


def test_anulowana_nie_do_wyslania(buduj_fakture):
    f = buduj_fakture(status="anulowana")
    with pytest.raises(BladDomeny, match="anulowan"):
        f.wyslij()
```

## Parametryzacja

```python
import pytest
from decimal import Decimal


@pytest.mark.parametrize(
    ("netto", "stawka", "oczekiwane_brutto"),
    [
        (Decimal("100.00"), Decimal("0.23"), Decimal("123.00")),
        (Decimal("100.00"), Decimal("0.08"), Decimal("108.00")),
        (Decimal("100.00"), Decimal("0.00"), Decimal("100.00")),
        (Decimal("0.01"), Decimal("0.23"), Decimal("0.01")),      # zaokrąglenie w dół
    ],
    ids=["vat23", "vat8", "zwolniony", "grosz"],
)
def test_brutto(netto: Decimal, stawka: Decimal, oczekiwane_brutto: Decimal) -> None:
    assert policz_brutto(netto, stawka) == oczekiwane_brutto


@pytest.mark.parametrize("nip", ["", "123", "12345678901", "abcdefghij", "0000000000"])
def test_zly_nip_odrzucony(nip: str) -> None:
    with pytest.raises(ValueError, match="NIP"):
        Kontrahent(nip=nip, nazwa="X")


# oczekiwana porażka z powodem — nie usuwaj testu, oznacz go
@pytest.mark.parametrize(
    "wejscie",
    [
        "2026-01-01",
        pytest.param("01.01.2026", marks=pytest.mark.xfail(reason="format PL, zadanie #412")),
    ],
)
def test_parsowanie_daty(wejscie: str) -> None:
    assert parsuj_date(wejscie).year == 2026
```

`ids=` daje czytelne nazwy w raporcie; bez nich pytest generuje `test_brutto[Decimal0-...]`
i przy porażce nie wiadomo, który przypadek padł.

Subtesty (pytest 9) — gdy zbiór przypadków znany dopiero w czasie działania:

```python
def test_wszystkie_pliki_wzorcowe(subtests, katalog_wzorcow: Path) -> None:
    for plik in katalog_wzorcow.glob("*.json"):
        with subtests.test(msg="wzorzec", plik=plik.name):
            assert waliduj(plik.read_text()) == []
```

Bez subtestów pierwszy błędny plik przerywa pętlę i nie wiesz, ile jeszcze jest złych.

## Testy asynchroniczne

```toml
[tool.pytest]
asyncio_mode = "auto"        # bez tego każdy test async wymaga @pytest.mark.asyncio
```

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def klient() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):          # uruchom lifespan w teście
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def test_healthz(klient: AsyncClient) -> None:
    odp = await klient.get("/healthz")
    assert odp.status_code == 200
    assert odp.json() == {"status": "ok"}


async def test_tworzenie_faktury(klient: AsyncClient, token: str) -> None:
    odp = await klient.post(
        "/api/v1/faktury",
        json={"nabywca_nip": "1234563218", "data_wystawienia": "2026-08-01",
              "termin_platnosci": "2026-08-15",
              "pozycje": [{"nazwa": "usługa", "ilosc": "1", "cena_netto": "100.00"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert odp.status_code == 201, odp.text
    assert odp.json()["kwota_netto"] == "100.00"
```

`app.router.lifespan_context(app)` uruchamia `lifespan`, bez którego `app.state` jest pusty
i wszystkie zależności padają na `AttributeError`. `TestClient` ze Starlette robi to sam,
ale jest synchroniczny i nie nadaje się do testowania kodu async z równoczesnością.

Przy pytest-asyncio 1.x nadpisanie pętli na cały przebieg:

```python
@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
```

## Atrapy i podmiany

### `monkeypatch` — do wszystkiego, co jest atrybutem

```python
def test_uzywa_zmiennej_srodowiskowej(monkeypatch) -> None:
    monkeypatch.setenv("APP_JWT_TTL_MINUT", "5")
    get_settings.cache_clear()               # lru_cache trzeba wyczyścić!
    assert get_settings().jwt_ttl_minut == 5


def test_czas_zamrozony(monkeypatch) -> None:
    from datetime import UTC, datetime
    ustalony = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return ustalony

    monkeypatch.setattr("app.domain.faktura.datetime", FakeDatetime)
    assert wygenerowany_numer().startswith("FV/2026/08")


def test_brak_dostepu_do_sieci(monkeypatch) -> None:
    def zablokuj(*a, **k):
        raise RuntimeError("test nie ma prawa wychodzić do sieci")

    monkeypatch.setattr("socket.socket.connect", zablokuj)
```

`monkeypatch` cofa zmianę po teście automatycznie. Ręczne `setattr` w teście bez cofnięcia
psuje kolejne testy w sposób zależny od kolejności — najgorszy rodzaj kruchości.

Pułapka z `lru_cache`: `get_settings` z `@lru_cache` zapamiętuje ustawienia z pierwszego
wywołania. Bez `cache_clear()` `monkeypatch.setenv` nie ma żadnego efektu.

### `respx` — atrapy HTTP dla httpx

```python
import httpx
import pytest
import respx


@respx.mock
async def test_wysylka_do_ksef() -> None:
    trasa = respx.post("https://ksef.example/faktury").mock(
        return_value=httpx.Response(200, json={"numer_referencyjny": "REF-1"})
    )
    wynik = await wyslij_do_ksef("FV/2026/001")
    assert wynik == "REF-1"
    assert trasa.called
    assert trasa.calls.last.request.headers["content-type"] == "application/json"


@respx.mock
async def test_ponawianie_przy_502() -> None:
    respx.post("https://ksef.example/faktury").mock(
        side_effect=[
            httpx.Response(502),
            httpx.Response(502),
            httpx.Response(200, json={"numer_referencyjny": "REF-2"}),
        ]
    )
    assert await wyslij_z_ponawianiem("FV/1") == "REF-2"


@respx.mock
async def test_timeout_obsluzony() -> None:
    respx.post("https://ksef.example/faktury").mock(
        side_effect=httpx.ConnectTimeout("timeout")
    )
    with pytest.raises(BladIntegracji, match="niedostępn"):
        await wyslij_do_ksef("FV/1")
```

`respx` dla httpx, `responses` dla `requests`. Nie podmieniaj własnych funkcji owijających
klienta HTTP — wtedy nie testujesz nagłówków, serializacji ani obsługi kodów błędów.

### `unittest.mock` — ostrożnie

```python
from unittest.mock import AsyncMock, Mock


def test_powiadomienie_wyslane() -> None:
    nadawca = Mock(spec=Nadawca)              # spec: literówka w nazwie metody = błąd
    usluga = UslugaFaktur(nadawca=nadawca)
    usluga.wystaw(faktura)
    nadawca.wyslij.assert_called_once_with(faktura.email, faktura.numer)
```

Zawsze `spec=` albo `autospec=True`. `Mock()` bez spec przyjmuje wywołanie dowolnej metody
i zwraca kolejny `Mock`, więc test przechodzi także po zmianie nazwy metody w kodzie
produkcyjnym — czyli nie testuje nic.

Lepiej niż mock: podstawienie prawdziwej, prostej implementacji przez `Protocol`.

```python
class NadawcaWPamieci:
    def __init__(self) -> None:
        self.wyslane: list[tuple[str, str]] = []

    def wyslij(self, email: str, numer: str) -> None:
        self.wyslane.append((email, numer))


def test_powiadomienie() -> None:
    nadawca = NadawcaWPamieci()
    UslugaFaktur(nadawca=nadawca).wystaw(faktura)
    assert nadawca.wyslane == [("k@example.com", "FV/2026/001")]
```

## Testy integracyjne z bazą

```python
# tests/integration/conftest.py
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.db.base import Base


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:17-alpine", driver="psycopg") as kontener:
        yield kontener


@pytest.fixture(scope="session")
async def engine(postgres: PostgresContainer):
    silnik = create_async_engine(postgres.get_connection_url(), poolclass=NullPool)
    async with silnik.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield silnik
    await silnik.dispose()


@pytest.fixture
async def sesja(engine) -> AsyncIterator[AsyncSession]:
    """Każdy test w transakcji, która jest wycofywana — pełna izolacja bez czyszczenia."""
    async with engine.connect() as polaczenie:
        transakcja = await polaczenie.begin()
        maker = async_sessionmaker(bind=polaczenie, expire_on_commit=False,
                                   join_transaction_mode="create_savepoint")
        async with maker() as s:
            yield s
        await transakcja.rollback()
```

`join_transaction_mode="create_savepoint"` sprawia, że `commit()` wewnątrz testowanego kodu
tworzy punkt zapisu zamiast faktycznie zatwierdzać — zewnętrzny rollback i tak cofnie
wszystko. Bez tego pierwszy `commit()` w kodzie produkcyjnym trwale zapisze dane i kolejne
testy zobaczą zaśmieconą bazę.

Alternatywa dla `create_all`: uruchomienie migracji Alembic na kontenerze. Wolniejsze, ale
testuje też migracje — warte tego w jednym teście dymnym.

Migracje jako test:

```python
def test_migracje_przechodza_w_obie_strony(postgres: PostgresContainer) -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", postgres.get_connection_url())
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
```

Uruchamianie warstwami:

```bash
uv run pytest tests/unit                         # sekundy, przy każdym zapisie
uv run pytest -m "not integration and not slow"  # szybka pętla
uv run pytest                                    # pełny przebieg, w CI
```

## Testy właściwościowe (Hypothesis)

Zamiast wymyślać przypadki brzegowe, opisz właściwość i pozwól bibliotece szukać
kontrprzykładu.

```python
from decimal import Decimal

from hypothesis import assume, given, settings, strategies as st


@given(
    netto=st.decimals(min_value=0, max_value=1_000_000, places=2),
    stawka=st.sampled_from([Decimal("0"), Decimal("0.05"), Decimal("0.08"), Decimal("0.23")]),
)
def test_brutto_nie_mniejsze_niz_netto(netto: Decimal, stawka: Decimal) -> None:
    assert policz_brutto(netto, stawka) >= netto


@given(st.text())
def test_normalizacja_idempotentna(tekst: str) -> None:
    raz = normalizuj(tekst)
    assert normalizuj(raz) == raz


@given(st.lists(st.integers(), min_size=1))
def test_sortowanie_zachowuje_elementy(xs: list[int]) -> None:
    assert sorted(moj_sort(xs)) == sorted(xs)


@given(st.builds(FakturaTworz, kwota=st.decimals(min_value=Decimal("0.01"), places=2)))
@settings(max_examples=200, deadline=500)
def test_serializacja_odwracalna(f: FakturaTworz) -> None:
    assert FakturaTworz.model_validate_json(f.model_dump_json()) == f
```

Zastosowania, w których Hypothesis zwraca się natychmiast: parsery, serializacja
(round-trip), normalizacja tekstu, arytmetyka na `Decimal`, konwersje dat i stref.

Hypothesis po znalezieniu kontrprzykładu **minimalizuje** go i zapisuje w `.hypothesis/` —
kolejne przebiegi zaczynają od znanych porażek. Katalog `.hypothesis` do `.gitignore`,
ale znaleziony kontrprzykład przepisz na zwykły test parametryzowany, żeby został na stałe.

## Pokrycie i co ono mierzy

```bash
uv run pytest --cov --cov-report=term-missing --cov-report=html
uv run pytest --cov --cov-branch --cov-fail-under=80
```

```toml
[tool.coverage.run]
source = ["src"]
branch = true                # bez tego "if x: return" liczy się jako pokryte przy jednej ścieżce
omit = ["*/migrations/*", "*/__main__.py"]

[tool.coverage.report]
exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError", "@overload",
                "if __name__ == .__main__.:"]
```

Pokrycie mierzy, które linie **zostały wykonane**. Nie mierzy, czy zostały sprawdzone.
Test wywołujący funkcję bez jednej asercji daje 100% pokrycia tej funkcji.

Praktycznie:

- 80% jako próg w CI to rozsądny kompromis; 100% wymusza testowanie kodu, który nie ma
  wartości do przetestowania (proste gettery, `__repr__`).
- `--cov-branch` obowiązkowo — bez tego gałęzie `else` są niewidoczne.
- Wartość jest w **raporcie braków**, nie w liczbie: `term-missing` pokazuje numery linii,
  których żaden test nie dotknął. Tam zwykle siedzi obsługa błędów, czyli miejsce, gdzie
  błędy są najdroższe.
- Nie ścigaj procentu przez testy wywołujące wszystko bez asercji. To gorsze niż brak testu,
  bo daje fałszywe poczucie bezpieczeństwa.

## Szybkość zestawu testów

```bash
uv run pytest --durations=15          # 15 najwolniejszych testów
uv run pytest -x -q --ff              # przerwij na pierwszym błędzie, zacznij od ostatnio nieudanych
uv run pytest --lf                    # tylko ostatnio nieudane
uv run pytest -n auto                 # równolegle (pytest-xdist)
uv run pytest -p no:randomly          # wyłącz losową kolejność przy diagnozie
```

| Przyczyna wolności | Naprawa |
|---|---|
| Kontener bazy wstaje na każdy test | `scope="session"` + izolacja przez rollback transakcji |
| `time.sleep` w teście | podmień zegar (`monkeypatch`), nie czekaj |
| Prawdziwe wywołania HTTP | `respx`; zablokuj `socket.connect` globalnie w `conftest.py` |
| Hashowanie haseł argon2/bcrypt w fixture | podmień kontekst na `plaintext` w testach |
| Wczytywanie dużego pliku w każdym teście | fixture `scope="session"` |
| Migracje Alembic przed każdym testem | `create_all` w testach, migracje w jednym teście dymnym |
| Testy integracyjne w pętli deweloperskiej | `-m "not integration"` lokalnie, pełny przebieg w CI |

Cel: zestaw jednostkowy poniżej 5 sekund. Powyżej tego nikt go nie uruchamia przed
commitem, a wtedy przestaje pełnić swoją funkcję.

## Czego nie testować

- Bibliotek trzecich. Test sprawdzający, że Pydantic waliduje `int`, testuje Pydantic.
- Prostych przypisań i getterów bez logiki.
- Dokładnych komunikatów błędów — sprawdzaj typ wyjątku i fragment przez `match=`.
- Szczegółów implementacji (nazw metod prywatnych, liczby wywołań wewnętrznych).
  Taki test blokuje refaktoryzację, nie chroni zachowania.

## Czego testować zawsze

- Reguły biznesowe i ich warunki brzegowe (kwota 0, lista pusta, data graniczna).
- Ścieżki błędów: co się dzieje, gdy zewnętrzna usługa zwraca 500, gdy plik jest pusty,
  gdy transakcja jest odrzucona.
- Serializację i deserializację na granicach systemu.
- Migracje bazy w obie strony.
- Każdy błąd zgłoszony z produkcji — najpierw test odtwarzający, potem poprawka.
