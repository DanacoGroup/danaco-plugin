# Nowoczesny Python — składnia i idiomy, sierpień 2026

Odniesienie: CPython 3.14.6. Przy każdej konstrukcji podana wersja, od której działa.
Nowy kod DANACO celuje w 3.13+; składni wyłącznie z 3.14 używaj tylko przy
`requires-python = ">=3.14"`.

## Co zmieniło się na tyle niedawno, że pamięć zawodzi

| Zmiana | Wersja | Skutek praktyczny |
|---|---|---|
| Składnia generyków `def f[T]()`, `class C[T]`, `type Alias = ...` | 3.12 (PEP 695) | `TypeVar` i `Generic[T]` są zbędne w nowym kodzie |
| Leniwe adnotacje (PEP 649/749) | **3.14** | `from __future__ import annotations` niepotrzebne; cudzysłowy przy typach przyszłych niepotrzebne; introspekcja przez `annotationlib` |
| `except A, B:` bez nawiasów (PEP 758) | **3.14** | tylko gdy brak `as` |
| t-stringi `t"..."` (PEP 750) | **3.14** | `string.templatelib.Template`; szablon *nie* jest sklejany — do bezpiecznego SQL/HTML |
| `concurrent.interpreters` (PEP 734) | **3.14** | subinterpretery + `InterpreterPoolExecutor` |
| Free-threading oficjalnie wspierane (PEP 779) | **3.14** | build `python3.14t`; koszt jednowątkowy ~5–10%, nie 40% jak w 3.13 |
| JIT: binaria eksperymentalne dla Windows/macOS | **3.14** | zysk ~3–5% geometrycznie; nie licz na to |
| `compression.zstd` (PEP 784) | **3.14** | zstd w bibliotece standardowej |
| `datetime.utcnow()` / `utcfromtimestamp()` usunięte | **3.14** | `datetime.now(UTC)` |
| `ExceptionGroup`, `except*` | 3.11 | zbierane błędy z `TaskGroup` |
| `asyncio.TaskGroup`, `asyncio.timeout` | 3.11 | zastępują `gather` i `wait_for` |
| `tomllib` w bibliotece standardowej | 3.11 | odczyt TOML bez zależności (zapisu brak) |
| `Self` | 3.11 | zwracanie własnego typu |
| `match` | 3.10 | dopasowanie strukturalne |
| `X | Y` w adnotacjach | 3.10 | `Optional`/`Union` niepotrzebne |

### Free-threading — kiedy w ogóle rozważać

Build `3.14t` zdejmuje GIL i pozwala wątkom liczyć równolegle. Realnie ma sens tylko dla
zadań CPU-bound w czystym Pythonie, w jednym procesie, gdzie kopiowanie danych między
procesami byłoby drogie. Warunki: wszystkie rozszerzenia C w projekcie muszą mieć koła
`cp314t` (numpy, pyarrow, pydantic-core mają; wiele mniejszych bibliotek nie). Instalacja:
`uv python install 3.14t`, a w projekcie `uv venv --python 3.14t`.

Nie przełączaj na free-threading usługi HTTP (wąskim gardłem jest I/O, asyncio załatwia to
lepiej) ani kodu liczącego w numpy/polars (te i tak zwalniają GIL). Zmierz przed i po.

## Typowanie

### Generyki (3.12+)

```python
from collections.abc import Callable, Iterable, Sequence

def pierwszy[T](xs: Sequence[T]) -> T | None:
    return xs[0] if xs else None


class Cache[K, V]:
    def __init__(self) -> None:
        self._dane: dict[K, V] = {}

    def get(self, klucz: K, domyslny: V | None = None) -> V | None:
        return self._dane.get(klucz, domyslny)

    def set(self, klucz: K, wartosc: V) -> None:
        self._dane[klucz] = wartosc


# alias typu — leniwy, może odwoływać się do rzeczy zdefiniowanych dalej
type Handler[T] = Callable[[T], None]
type JSON = str | int | float | bool | None | list["JSON"] | dict[str, "JSON"]


# ograniczenie górne: T musi być podtypem
def najwiekszy[T: Comparable](xs: Iterable[T]) -> T:
    return max(xs)


# zbiór dozwolonych typów (constraint), nie podtypowanie
def podwoj[T: (int, str)](x: T) -> T:
    return x * 2
```

Stary zapis `T = TypeVar("T")` + `class C(Generic[T])` nadal działa i jest konieczny przy
`requires-python < 3.12`. W nowym kodzie go nie pisz.

### `Protocol` — typowanie strukturalne

Używaj, gdy zależy ci na *kształcie*, nie na dziedziczeniu. Klasa implementująca nie musi
nic importować.

```python
from typing import Protocol, runtime_checkable


class Zapisywalny(Protocol):
    def zapisz(self, sciezka: str) -> None: ...


class Repozytorium[T](Protocol):
    def pobierz(self, id_: int) -> T | None: ...
    def zapisz(self, obiekt: T) -> None: ...


def eksportuj(obiekty: list[Zapisywalny], katalog: str) -> None:
    for i, o in enumerate(obiekty):
        o.zapisz(f"{katalog}/{i}.dat")


@runtime_checkable
class MaDlugosc(Protocol):
    def __len__(self) -> int: ...


assert isinstance([1, 2], MaDlugosc)
```

`@runtime_checkable` sprawdza wyłącznie obecność metod, nie ich sygnatury. Protokół jest
właściwym typem parametru w funkcjach domeny: pozwala podstawić atrapę w teście bez
dziedziczenia po klasie produkcyjnej.

### `TypedDict`, `NotRequired`, `Literal`, `Self`, `ParamSpec`

```python
from typing import Literal, NotRequired, ParamSpec, Self, TypedDict, TypeVar, overload
from collections.abc import Callable
import functools
import time


class OdpowiedzAPI(TypedDict):
    id: int
    nazwa: str
    opis: NotRequired[str]        # klucz może nie istnieć
    status: Literal["nowy", "w_toku", "zamkniety"]


def opis_lub_pusty(o: OdpowiedzAPI) -> str:
    return o.get("opis", "")


class Budowniczy:
    def __init__(self) -> None:
        self._czesci: list[str] = []

    def dodaj(self, czesc: str) -> Self:      # 3.11; działa też w podklasach
        self._czesci.append(czesc)
        return self

    def zbuduj(self) -> str:
        return " ".join(self._czesci)


P = ParamSpec("P")
R = TypeVar("R")


def mierz(fn: Callable[P, R]) -> Callable[P, R]:
    """Dekorator zachowujący sygnaturę funkcji dekorowanej."""

    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"{fn.__name__}: {time.perf_counter() - start:.3f}s")

    return wrapper
```

`Literal` to najtańsza walidacja, jaka istnieje — łapie literówkę w stałej na etapie
kontroli typów, bez kosztu w czasie działania. Używaj go do trybów, statusów i flag zamiast
gołych `str`. `@overload` gdy typ zwracany zależy od argumentu:

```python
@overload
def parsuj(tekst: str, *, jako_liste: Literal[True]) -> list[str]: ...
@overload
def parsuj(tekst: str, *, jako_liste: Literal[False] = False) -> str: ...
def parsuj(tekst: str, *, jako_liste: bool = False) -> str | list[str]:
    return tekst.split(",") if jako_liste else tekst.strip()
```

### Adnotacje leniwe (3.14)

W 3.14 adnotacje nie są obliczane przy definicji, tylko przy odczycie. Trzy skutki:

1. `from __future__ import annotations` jest zbędne w nowych plikach.
2. Odwołanie w przód nie wymaga cudzysłowów: `def f(x: Wezel) -> Wezel:` przed definicją
   `Wezel` przechodzi.
3. Kod czytający adnotacje ma używać `annotationlib.get_annotations`, nie `__annotations__`:

```python
from annotationlib import Format, get_annotations


def f(x: NieistniejacyTyp) -> int:  # noqa: F821 — celowo
    return 0


print(get_annotations(f, format=Format.STRING))     # {'x': 'NieistniejacyTyp', 'return': 'int'}
print(get_annotations(f, format=Format.FORWARDREF)) # ForwardRef zamiast wyjątku
```

Uwaga przy bibliotekach opartych na introspekcji (Pydantic, FastAPI, SQLAlchemy) — w 3.14
działają, ale jeśli sam piszesz kod czytający typy w czasie działania, `typing.get_type_hints`
nadal jest właściwym wejściem, bo rozwiązuje odwołania.

## Dopasowanie strukturalne (`match`, 3.10+)

Nie jest to `switch`. Wartość ma sens, gdy rozbierasz strukturę, a nie porównujesz jedną
wartość — do tego wystarczy `if`/`elif` albo słownik.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Punkt:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Okrag:
    srodek: Punkt
    promien: float


def opisz(ksztalt: Punkt | Okrag | list[Punkt]) -> str:
    match ksztalt:
        case Punkt(x=0, y=0):
            return "punkt w początku układu"
        case Punkt(x=x, y=y) if x == y:
            return f"punkt na przekątnej: {x}"
        case Punkt(x=x, y=y):
            return f"punkt ({x}, {y})"
        case Okrag(srodek=Punkt(x=0, y=0), promien=r):
            return f"okrąg wyśrodkowany, r={r}"
        case [Punkt() as p]:
            return f"jeden punkt na liście: {p}"
        case [Punkt(), Punkt(), *reszta]:
            return f"co najmniej dwa punkty, dodatkowo {len(reszta)}"
        case _:
            return "nieznany kształt"


def obsluz_zdarzenie(z: dict[str, object]) -> str:
    match z:
        case {"typ": "platnosc", "kwota": int(kwota) | float(kwota), "waluta": str(w)}:
            return f"płatność {kwota} {w}"
        case {"typ": "zwrot", "id_platnosci": str(pid)}:
            return f"zwrot dla {pid}"
        case {"typ": str(t)}:
            return f"nieobsługiwany typ: {t}"
        case _:
            raise ValueError("zdarzenie bez pola 'typ'")
```

Pułapka: `case Status.NOWY:` działa (kropka = wartość), ale `case NOWY:` to **przypisanie**
do nazwy `NOWY`, które łapie wszystko. Gołe nazwy w `case` zawsze wiążą, nigdy nie porównują.
Konsekwencja: gałąź poniżej staje się martwa i nikt tego nie zauważa, bo kod się uruchamia.

## Struktury danych: co wybrać

| Konstrukcja | Kiedy | Koszt |
|---|---|---|
| `@dataclass(slots=True, frozen=True)` | struktura wewnętrzna, brak walidacji, potrzeba `__eq__`/`__repr__` | zerowy narzut poza tworzeniem |
| `NamedTuple` | krotka z nazwami, rozpakowywanie, zgodność z API krotkowym | najmniejszy ślad pamięci |
| `TypedDict` | słownik z zewnątrz (JSON, API), którego nie chcesz przepakowywać | zerowy — to zwykły `dict` |
| `pydantic.BaseModel` | granica systemu: HTTP, plik, env, kolejka; potrzebna walidacja i serializacja | walidacja w Rust, ale to wciąż praca |
| `msgspec.Struct` | jak Pydantic, ale gdy profil pokazuje, że walidacja to wąskie gardło | najszybszy z walidujących |
| zwykła klasa | zachowanie ważniejsze niż dane | — |

```python
from dataclasses import dataclass, field
from decimal import Decimal
from typing import NamedTuple

from pydantic import BaseModel, ConfigDict, Field, field_validator


# wewnątrz aplikacji
@dataclass(frozen=True, slots=True)
class PozycjaFaktury:
    nazwa: str
    ilosc: int
    cena_netto: Decimal
    stawka_vat: Decimal = Decimal("0.23")

    @property
    def brutto(self) -> Decimal:
        return self.cena_netto * self.ilosc * (1 + self.stawka_vat)


@dataclass(slots=True)
class Koszyk:
    pozycje: list[PozycjaFaktury] = field(default_factory=list)   # nigdy = []


class Wspolrzedne(NamedTuple):
    szerokosc: float
    dlugosc: float


# na granicy systemu
class ZamowienieWe(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nip: str = Field(pattern=r"^\d{10}$")
    kwota: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    uwagi: str | None = Field(default=None, max_length=500)

    @field_validator("nip")
    @classmethod
    def sprawdz_sume_kontrolna(cls, v: str) -> str:
        wagi = (6, 5, 7, 2, 3, 4, 5, 6, 7)
        suma = sum(w * int(c) for w, c in zip(wagi, v, strict=False))
        if suma % 11 != int(v[9]):
            raise ValueError("niepoprawna suma kontrolna NIP")
        return v
```

`slots=True` w dataclass: mniej pamięci i szybszy dostęp do pól, kosztem braku możliwości
dopisania atrybutu w locie. Włączaj domyślnie. `frozen=True` dodatkowo daje `__hash__`,
więc obiekt można trzymać w zbiorze i w kluczu słownika. Konfiguracja modeli Pydantic
w kontekście API — `references/fastapi.md` w tej podpaczce.

## Menedżery kontekstu

```python
import contextlib
import sqlite3
import time
from collections.abc import Iterator
from pathlib import Path


@contextlib.contextmanager
def zapis_atomowy(cel: Path) -> Iterator[Path]:
    """Zapis przez plik tymczasowy — cel nigdy nie jest w stanie połowicznym."""
    tmp = cel.with_suffix(cel.suffix + ".tmp")
    try:
        yield tmp
        tmp.replace(cel)          # atomowe w obrębie systemu plików
    finally:
        tmp.unlink(missing_ok=True)


with zapis_atomowy(Path("wynik.json")) as tmp:
    tmp.write_text('{"ok": true}', encoding="utf-8")


# wiele zasobów bez piramidy wcięć
with (
    sqlite3.connect("a.db") as a,
    sqlite3.connect("b.db") as b,
):
    a.execute("select 1")
    b.execute("select 1")


# zmienna liczba zasobów
def scal(sciezki: list[Path], cel: Path) -> None:
    with contextlib.ExitStack() as stack:
        pliki = [stack.enter_context(p.open("rb")) for p in sciezki]
        with cel.open("wb") as out:
            for f in pliki:
                out.write(f.read())


# tłumienie wyjątku — wyłącznie tam, gdzie brak zasobu jest normalny
with contextlib.suppress(FileNotFoundError):
    Path("cache.tmp").unlink()
```

`contextlib.suppress` nie jest odpowiednikiem `except: pass`. Ograniczasz go do jednego
konkretnego typu i jednej linii. Jeśli w bloku jest więcej niż jedna operacja, tłumisz
też błędy, o których nie wiesz.

## Generatory i iteratory

```python
from collections.abc import Iterable, Iterator
from itertools import batched, islice, groupby
from pathlib import Path


def wiersze_csv(sciezka: Path) -> Iterator[str]:
    """Czyta plik leniwie — pamięć niezależna od rozmiaru pliku."""
    with sciezka.open(encoding="utf-8") as f:
        next(f, None)                     # pomiń nagłówek
        for wiersz in f:
            wiersz = wiersz.rstrip("\n")
            if wiersz:
                yield wiersz


def paczki[T](it: Iterable[T], rozmiar: int) -> Iterator[tuple[T, ...]]:
    return batched(it, rozmiar)           # 3.12; wcześniej pętla ręczna


# przetwarzanie 10 GB pliku przy stałym zużyciu pamięci
for paczka in paczki(wiersze_csv(Path("duzy.csv")), 1000):
    kursor.executemany("insert into wiersze (tresc) values (?)",
                       [(w,) for w in paczka])


def pierwsze_n[T](it: Iterable[T], n: int) -> list[T]:
    return list(islice(it, n))
```

`itertools.groupby` grupuje **kolejne** elementy — wejście musi być posortowane po kluczu,
inaczej dostaniesz kilka grup o tym samym kluczu i nikt tego nie zauważy w małym teście.
Wyrażenie generatorowe zamiast listy wszędzie, gdzie wynik jest tylko przejściem:
`sum(x.kwota for x in pozycje)` nie tworzy listy pośredniej, `sum([...])` tworzy.

## `functools`

```python
import functools
from collections.abc import Callable


@functools.cache                    # 3.9; nieograniczony rozmiar
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)


@functools.lru_cache(maxsize=1024)  # gdy zbiór argumentów jest nieograniczony
def geokoduj(adres: str) -> tuple[float, float]:
    odp = httpx.get("https://nominatim.example/search", params={"q": adres})
    dane = odp.raise_for_status().json()[0]
    return float(dane["lat"]), float(dane["lon"])


class Raport:
    def __init__(self, dane: list[int]) -> None:
        self._dane = dane

    @functools.cached_property      # liczone raz na instancję
    def suma(self) -> int:
        return sum(self._dane)


@functools.singledispatch
def serializuj(x: object) -> str:
    raise TypeError(f"brak serializacji dla {type(x).__name__}")


@serializuj.register
def _(x: int) -> str:
    return str(x)


@serializuj.register
def _(x: list) -> str:
    return "[" + ",".join(serializuj(e) for e in x) + "]"
```

`functools.cache` na metodzie instancji trzyma referencję do `self` na zawsze — wyciek
pamięci; na metodach używaj `cached_property` albo cache poza klasą. Cache nie działa na
argumentach niehaszowalnych (`list`, `dict`, `set`) — konwertuj na `tuple`/`frozenset`
w warstwie zewnętrznej.

## Wyjątki i grupy wyjątków

```python
class BladDomeny(Exception):
    """Baza dla błędów tego modułu — pozwala łapać wszystko nasze jednym except."""


class NieznalezionoZasobu(BladDomeny):
    def __init__(self, typ: str, id_: int) -> None:
        self.typ = typ
        self.id = id_
        super().__init__(f"{typ} o id={id_} nie istnieje")


class NaruszenieReguly(BladDomeny):
    def __init__(self, regula: str, szczegoly: dict[str, object]) -> None:
        self.regula = regula
        self.szczegoly = szczegoly
        super().__init__(f"naruszono regułę: {regula}")
```

Zasady:

- Definiuj bazę wyjątków modułu. Bez niej wołający musi znać wszystkie typy szczegółowe.
- Dane w atrybutach, nie tylko w komunikacie — warstwa wyżej ma je odczytać, nie parsować napis.
- `raise ... from e` przy opakowywaniu (inaczej gubisz pierwotny ślad stosu);
  `raise ... from None`, gdy pierwotny błąd jest szumem (np. `KeyError` z wnętrza parsera).
- Nie łap `Exception`, żeby zalogować i zamilknąć. Albo obsługujesz, albo podnosisz dalej.

```python
try:
    dane = json.loads(surowe)
except json.JSONDecodeError as e:
    raise BladDomeny(f"niepoprawny JSON w odpowiedzi na pozycji {e.pos}") from e
```

### `ExceptionGroup` i `except*` (3.11+)

Gdy równoległe zadania mogą zawieść niezależnie, jeden wyjątek jest za mało.

```python
import asyncio


async def pobierz_wszystko(adresy: list[str]) -> list[bytes]:
    wyniki: list[bytes] = []
    try:
        async with asyncio.TaskGroup() as tg:
            zadania = [tg.create_task(pobierz(a)) for a in adresy]
    except* TimeoutError as eg:
        # eg.exceptions to krotka wszystkich TimeoutError z grupy
        logger.warning("przekroczono czas dla %d adresów", len(eg.exceptions))
    except* ValueError as eg:
        raise BladDomeny(f"{len(eg.exceptions)} adresów miało zły format") from eg
    else:
        wyniki = [z.result() for z in zadania]
    return wyniki
```

`except*` wykonuje **wszystkie** pasujące gałęzie, nie pierwszą. To inne zachowanie niż
zwykłe `except` i łatwo się na tym potknąć.

Grupę można też zbudować ręcznie, gdy walidujesz wiele rzeczy naraz i chcesz zwrócić
komplet błędów zamiast pierwszego:

```python
def waliduj(rekordy: list[dict]) -> None:
    bledy = []
    for i, r in enumerate(rekordy):
        try:
            sprawdz(r)
        except ValueError as e:
            bledy.append(ValueError(f"wiersz {i}: {e}"))
    if bledy:
        raise ExceptionGroup("walidacja nieudana", bledy)
```

## Moduły i importy

- Importy **absolutne** (`from app.domain import faktura`). Względne (`from .domain import`)
  tylko wewnątrz jednego pakietu i tylko o jeden poziom.
- Import na górze pliku. Import wewnątrz funkcji wyłącznie dla: przerwania cyklu, ciężkiej
  zależności opcjonalnej (`import polars` w narzędziu, które zwykle jej nie potrzebuje),
  zależności platformowej.
- `__all__` w `__init__.py` pakietu — jawne API. Ruff (`F401`) inaczej zgłosi nieużywane
  reeksporty.
- Zero `from x import *` poza `conftest.py`. Zero logiki na poziomie modułu poza definicjami
  i stałymi: kod na poziomie modułu wykonuje się przy imporcie, więc test importujący moduł
  odpali połączenie do bazy.
- Cykl importów rozwiązuj przez `if TYPE_CHECKING:` (typ potrzebny tylko do adnotacji)
  albo przez wydzielenie wspólnego modułu — nie przez import w funkcji „na chwilę”.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import Uzytkownik   # tylko dla mypy, brak kosztu i cyklu


def opis(u: "Uzytkownik") -> str:          # w 3.14 cudzysłowy zbędne
    return u.email
```

## Uznane za przestarzałe — nie pisz tego

| Zamiast | Pisz | Powód |
|---|---|---|
| `typing.List`, `Dict`, `Tuple`, `Set` | `list`, `dict`, `tuple`, `set` | 3.9; `typing` aliasy są deprecjonowane |
| `Optional[X]`, `Union[X, Y]` | `X \| None`, `X \| Y` | 3.10 |
| `TypeVar` + `Generic[T]` | `def f[T]`, `class C[T]` | 3.12, PEP 695 |
| `from __future__ import annotations` | nic (przy 3.14) | PEP 649 |
| `os.path.join`, `os.listdir`, `glob.glob` | `pathlib.Path` | czytelniejsze, typowane |
| `datetime.utcnow()` | `datetime.now(UTC)` | usunięte w 3.14 |
| `%` i `.format()` w nowym kodzie | f-string | poza `logger.info("x %s", v)` |
| `dict(a=1)` | `{"a": 1}` | szybsze, bez ograniczeń nazw |
| `open(p)` + `close()` | `with p.open()` | |
| `asyncio.get_event_loop()` | `asyncio.get_running_loop()` / `asyncio.run()` | deprecjonowane |
| `asyncio.gather` do zadań zależnych | `asyncio.TaskGroup` | anulowanie rodzeństwa przy błędzie |
| `asyncio.wait_for` | `async with asyncio.timeout(...)` | 3.11 |
| `distutils`, `setup.py` | `pyproject.toml` + `uv_build` | `distutils` usunięte w 3.12 |
| `imp`, `cgi`, `telnetlib`, `nntplib`, `crypt`, `pipes` | — | usunięte w 3.13 (PEP 594) |
| `typing.Text`, `typing.ByteString` | `str`, `bytes` | |
| `unittest.TestCase` w nowych testach | funkcje pytest | |
| `logging` z f-stringiem: `logger.info(f"x {v}")` | `logger.info("x %s", v)` | formatowanie tylko gdy poziom aktywny |
| `float` do kwot | `decimal.Decimal` | `0.1 + 0.2 != 0.3` |
| `assert` do walidacji wejścia | jawny `raise` | `python -O` usuwa `assert` |

Ostatni punkt jest źródłem realnych dziur: `assert user.is_admin` w kodzie produkcyjnym
uruchomionym z `-O` przestaje cokolwiek sprawdzać.

## Wydajność — co faktycznie zmienia wynik

Kolejność sprawdzania, gdy coś jest wolne:

1. Zmierz. `time.perf_counter` wokół podejrzanego bloku, potem
   `python -m cProfile -s cumtime skrypt.py`, dla kodu async `python -m asyncio ps PID` (3.14).
2. Sprawdź złożoność: `x in lista` w pętli to O(n²) — zamień listę na `set`/`dict`.
3. Sprawdź I/O: liczba zapytań do bazy (N+1), liczba wywołań HTTP, otwieranie pliku w pętli.
4. Dopiero potem mikro-optymalizacje: `__slots__`, lokalne referencje w pętli, `bytes`
   zamiast `str` przy dużych buforach.
5. Jeśli to czysta arytmetyka na tablicach — numpy/polars, nie pętla po Pythonie.
   Różnica jest 50–200×, żadna optymalizacja pętli tego nie dogoni.

`sys.intern`, `array.array` i `memoryview` mają sens przy setkach megabajtów w pamięci;
poniżej tego są szumem.
