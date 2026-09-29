# SQLAlchemy 2.0, Alembic, Postgres — sierpień 2026

SQLAlchemy **2.0.51** (2.1 wciąż w becie — `2.1.0b1` ze stycznia 2026; na produkcji zostaje
2.0 z ograniczeniem `<2.1`). Alembic **1.18.5**, psycopg **3.3.4**.

## Styl 2.0 — czego nie pisać

Styl 1.x nadal działa w trybie zgodności, ale nowy kod pisany z pamięci trafia w niego
odruchowo. Tabela zamian:

| Styl 1.x | Styl 2.0 |
|---|---|
| `session.query(User).filter(...).all()` | `session.scalars(select(User).where(...)).all()` |
| `session.query(User).get(1)` | `session.get(User, 1)` |
| `Column(Integer, primary_key=True)` | `Mapped[int] = mapped_column(primary_key=True)` |
| `Column(String(50), nullable=False)` | `Mapped[str] = mapped_column(String(50))` (`nullable` z typu) |
| `declarative_base()` | `class Base(DeclarativeBase): ...` |
| `relationship("Adres")` | `Mapped[list["Adres"]] = relationship(back_populates=...)` |
| `.filter()` | `.where()` |
| `session.query(...).count()` | `session.scalar(select(func.count()).select_from(User))` |
| `engine.execute("select 1")` | `conn.execute(text("select 1"))` w bloku `with` |

Nullowalność bierze się z adnotacji: `Mapped[str]` → `NOT NULL`, `Mapped[str | None]` →
kolumna nullowalna. Nadpisanie: `mapped_column(nullable=True)`. To najczęstsza różnica,
która sprawia, że migracja wygenerowana z modeli różni się od oczekiwań.

## Baza deklaratywna

```python
# src/app/db/base.py
from datetime import datetime
from typing import Any

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nazwy więzów generowane deterministycznie — bez tego Alembic nie potrafi
# usunąć ograniczenia, bo Postgres nadał mu losową nazwę.
KONWENCJA = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=KONWENCJA)

    def as_dict(self) -> dict[str, Any]:
        return {k.name: getattr(self, k.name) for k in self.__table__.columns}


class ZnacznikiCzasu:
    utworzono: Mapped[datetime] = mapped_column(server_default=func.now())
    zmieniono: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

Konwencja nazw jest jednym z tych ustawień, których brak boli dopiero po roku — przy próbie
usunięcia indeksu, którego nazwy nikt nie zna.

## Modele i relacje

```python
# src/app/db/models.py
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ZnacznikiCzasu


class StatusFaktury(StrEnum):
    SZKIC = "szkic"
    WYSTAWIONA = "wystawiona"
    OPLACONA = "oplacona"
    ANULOWANA = "anulowana"


class Kontrahent(ZnacznikiCzasu, Base):
    __tablename__ = "kontrahenci"
    __table_args__ = (
        UniqueConstraint("nip", "organizacja_id", name="nip_w_organizacji"),
        Index("ix_kontrahenci_nazwa_trgm", "nazwa",
              postgresql_using="gin", postgresql_ops={"nazwa": "gin_trgm_ops"}),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organizacja_id: Mapped[UUID] = mapped_column(index=True)
    nip: Mapped[str] = mapped_column(String(10))
    nazwa: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    dane_dodatkowe: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    faktury: Mapped[list["Faktura"]] = relationship(
        back_populates="kontrahent", cascade="all, delete-orphan", passive_deletes=True
    )


class Faktura(ZnacznikiCzasu, Base):
    __tablename__ = "faktury"
    __table_args__ = (
        UniqueConstraint("numer", "organizacja_id"),
        CheckConstraint("kwota_netto >= 0", name="kwota_nieujemna"),
        Index("ix_faktury_org_status_data", "organizacja_id", "status", "data_wystawienia"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organizacja_id: Mapped[UUID] = mapped_column(index=True)
    kontrahent_id: Mapped[UUID] = mapped_column(
        ForeignKey("kontrahenci.id", ondelete="CASCADE"), index=True
    )
    numer: Mapped[str] = mapped_column(String(50))
    status: Mapped[StatusFaktury] = mapped_column(
        Enum(StatusFaktury, native_enum=False, length=20), default=StatusFaktury.SZKIC
    )
    data_wystawienia: Mapped[date]
    kwota_netto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    kwota_vat: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    zaplacono_at: Mapped[datetime | None]

    kontrahent: Mapped[Kontrahent] = relationship(back_populates="faktury", lazy="raise")
    pozycje: Mapped[list["Pozycja"]] = relationship(
        back_populates="faktura", cascade="all, delete-orphan", lazy="raise"
    )


class Pozycja(Base):
    __tablename__ = "pozycje"

    id: Mapped[int] = mapped_column(primary_key=True)
    faktura_id: Mapped[UUID] = mapped_column(
        ForeignKey("faktury.id", ondelete="CASCADE"), index=True
    )
    nazwa: Mapped[str] = mapped_column(String(200))
    ilosc: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    cena_netto: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    faktura: Mapped[Faktura] = relationship(back_populates="pozycje")
```

Trzy decyzje z tego przykładu, warte skopiowania:

- **`lazy="raise"` na relacjach.** Próba doczytania relacji poza jawnym `selectinload`
  podnosi wyjątek zamiast po cichu wykonać dodatkowe zapytanie. To jedyny mechanizm, który
  wyłapuje N+1 w czasie developmentu zamiast na produkcji.
- **`Numeric(12, 2)` do kwot**, mapowane na `Decimal`. `Float` przy kwotach daje różnice
  groszowe, których nikt później nie odtworzy.
- **`native_enum=False`** dla enumów: wartość leci jako `VARCHAR` z `CHECK`. Natywny typ
  enum w Postgresie wymaga `ALTER TYPE` przy każdej nowej wartości i blokuje tabelę.

`ondelete="CASCADE"` (baza) + `passive_deletes=True` (ORM): usuwanie wykonuje baza jednym
poleceniem. Bez `passive_deletes` SQLAlchemy najpierw wczyta wszystkie dzieci do pamięci
i usunie je pojedynczo.

## Sesje

```python
# src/app/db/session.py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

s = get_settings()

engine = create_async_engine(
    str(s.database_url),          # postgresql+psycopg://... (nie psycopg2)
    echo=False,
    pool_size=10,                 # stałe połączenia na worker
    max_overflow=5,               # dodatkowe w szczycie
    pool_timeout=30,              # ile czekać na wolne połączenie
    pool_recycle=1800,            # odnów po 30 min — proxy zrywa bezczynne
    pool_pre_ping=True,           # sprawdź przed użyciem; kosztuje jeden round-trip
)

Sesja = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def daj_sesje() -> AsyncIterator[AsyncSession]:
    async with Sesja() as sesja:
        try:
            yield sesja
            await sesja.commit()
        except Exception:
            await sesja.rollback()
            raise
```

`expire_on_commit=False` jest praktycznie obowiązkowe w kodzie async: bez tego dostęp do
atrybutu obiektu po `commit()` próbuje odświeżyć go z bazy, co w kontekście async po
zamknięciu sesji kończy się `MissingGreenlet`.

Rozmiar puli: `pool_size + max_overflow` przemnożone przez liczbę workerów nie może
przekroczyć `max_connections` Postgresa (domyślnie 100). Cztery workery gunicorna po
`10+5` to 60 połączeń — mieści się; osiem workerów to już 120 i baza zacznie odrzucać.
Przy wielu instancjach usługi wstaw PgBouncer w trybie `transaction` i wtedy w aplikacji
`poolclass=NullPool`.

## Zapytania

```python
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload, joinedload, load_only


# jeden obiekt
faktura = await sesja.get(Faktura, faktura_id)

# lista z filtrem i sortowaniem
zapytanie = (
    select(Faktura)
    .where(Faktura.organizacja_id == org_id, Faktura.status == StatusFaktury.WYSTAWIONA)
    .order_by(Faktura.data_wystawienia.desc())
    .limit(50)
    .offset(0)
)
faktury = (await sesja.scalars(zapytanie)).all()

# kolumny zamiast całych obiektów — mniej danych z bazy i brak identity map
wiersze = (
    await sesja.execute(
        select(Faktura.id, Faktura.numer, Faktura.kwota_netto).where(...)
    )
).all()

# agregacja
suma = await sesja.scalar(
    select(func.coalesce(func.sum(Faktura.kwota_netto), 0)).where(
        Faktura.organizacja_id == org_id
    )
)

# agregacja z grupowaniem
podsumowanie = (
    await sesja.execute(
        select(Faktura.status, func.count().label("ile"), func.sum(Faktura.kwota_netto))
        .where(Faktura.organizacja_id == org_id)
        .group_by(Faktura.status)
    )
).all()

# aktualizacja masowa bez wczytywania obiektów
await sesja.execute(
    update(Faktura)
    .where(Faktura.status == StatusFaktury.WYSTAWIONA, Faktura.termin < date.today())
    .values(status=StatusFaktury.PRZETERMINOWANA)
    .execution_options(synchronize_session=False)
)

# strumień przy dużym zbiorze — nie wczytuje wszystkiego naraz
async for faktura in await sesja.stream_scalars(
    select(Faktura).where(Faktura.organizacja_id == org_id)
):
    plik.write(f"{faktura.numer};{faktura.kwota_netto}\n")
```

`scalars()` zwraca obiekty; `execute()` zwraca krotki `Row`. Mieszanie tych dwóch to
najczęstsza przyczyna `AttributeError: 'Row' object has no attribute ...`.

### N+1 i jak go usunąć

```python
# N+1: jedno zapytanie o faktury, potem po jednym o pozycje każdej
faktury = (await sesja.scalars(select(Faktura))).all()
for f in faktury:
    print(len(f.pozycje))      # z lazy="raise" -> wyjątek zamiast cichego zapytania

# poprawnie: relacja jeden-do-wielu -> selectinload (drugie zapytanie z IN)
faktury = (
    await sesja.scalars(
        select(Faktura).options(selectinload(Faktura.pozycje)).where(...)
    )
).all()

# relacja wiele-do-jednego -> joinedload (jeden JOIN)
faktury = (
    await sesja.scalars(
        select(Faktura).options(joinedload(Faktura.kontrahent)).where(...)
    )
).all()

# zagnieżdżone
select(Faktura).options(
    selectinload(Faktura.pozycje).selectinload(Pozycja.produkt),
    joinedload(Faktura.kontrahent).load_only(Kontrahent.nazwa, Kontrahent.nip),
)
```

| Strategia | Kiedy | Skutek |
|---|---|---|
| `selectinload` | kolekcja (jeden-do-wielu, wiele-do-wielu) | 2 zapytania, brak duplikacji wierszy |
| `joinedload` | pojedynczy obiekt (wiele-do-jednego) | 1 zapytanie z LEFT JOIN |
| `joinedload` na kolekcji | prawie nigdy | mnoży wiersze; z `limit()` daje **złą** liczbę rekordów |
| `subqueryload` | historyczna | wyparta przez `selectinload` |
| `raiseload("*")` | audyt istniejącego kodu | wyjątek przy każdym doczytaniu |

`joinedload` razem z `.limit()` to pułapka: limit stosuje się do wierszy po złączeniu, więc
faktura z 5 pozycjami zjada 5 z limitu 50. Przy kolekcjach zawsze `selectinload`.

Diagnostyka: `create_async_engine(..., echo=True)` w środowisku deweloperskim albo licznik
zapytań w teście:

```python
from sqlalchemy import event


def policz_zapytania(engine) -> list[str]:
    zapytania: list[str] = []
    event.listen(engine.sync_engine, "before_cursor_execute",
                 lambda *a: zapytania.append(a[2]))
    return zapytania
```

Test, który asertuje liczbę zapytań, jest jedynym mechanizmem, który nie pozwoli N+1 wrócić.

## Transakcje

```python
# jawna transakcja
async with Sesja() as sesja, sesja.begin():
    sesja.add(faktura)
    await sesja.execute(update(Kontrahent).where(...).values(...))
    # commit automatyczny na wyjściu; rollback przy wyjątku


# punkt zapisu (zagnieżdżona transakcja)
async with Sesja() as sesja:
    async with sesja.begin():
        sesja.add(faktura)
        try:
            async with sesja.begin_nested():       # SAVEPOINT
                sesja.add(pozycja_ryzykowna)
        except IntegrityError:
            pass                                   # cofnięty tylko savepoint


# blokada wiersza przy odczycie-modyfikacji-zapisie
faktura = await sesja.scalar(
    select(Faktura).where(Faktura.id == id_).with_for_update()
)
faktura.status = StatusFaktury.OPLACONA
await sesja.commit()


# blokada nieblokująca — pomiń zajęte (kolejka zadań)
zadanie = await sesja.scalar(
    select(Zadanie).where(Zadanie.status == "oczekuje")
    .order_by(Zadanie.utworzono).limit(1)
    .with_for_update(skip_locked=True)
)
```

Reguły:

- Jedna transakcja na jedno żądanie HTTP. Zależność FastAPI z `yield` (patrz `references/fastapi.md` w tej podpaczce)
  zamyka ją automatycznie.
- Transakcja obejmuje wyłącznie zapisy do bazy. Wywołanie HTTP wewnątrz otwartej transakcji
  trzyma blokady na czas odpowiedzi obcego serwera.
- Blokada optymistyczna zamiast `FOR UPDATE`, gdy kolizje są rzadkie:
  kolumna `wersja: Mapped[int] = mapped_column(default=0)` +
  `__mapper_args__ = {"version_id_col": wersja}`. Konflikt daje `StaleDataError`.
- Przy `IntegrityError` sesja jest w stanie nieużywalnym do momentu `rollback()`. Kolejne
  operacje na niej podniosą `PendingRollbackError`.

## Alembic

```bash
uv run alembic init -t async migrations       # szablon async
uv run alembic revision --autogenerate -m "faktury i kontrahenci"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
uv run alembic history --verbose
uv run alembic upgrade head --sql > migracja.sql    # podgląd bez wykonania
```

`migrations/env.py` — fragmenty, które trzeba zmienić po `init`:

```python
from app.config import get_settings
from app.db.base import Base
import app.db.models  # noqa: F401  — import wymusza rejestrację modeli w metadanych

config.set_main_option("sqlalchemy.url", str(get_settings().database_url))
target_metadata = Base.metadata


# wewnątrz run_migrations_online(), w wywołaniu context.configure:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,               # wykrywaj zmiany typu kolumny
        compare_server_default=True,     # i zmiany wartości domyślnych
        include_schemas=False,
    )
```

Bez `compare_type=True` zmiana `String(50)` → `String(200)` nie trafi do wygenerowanej
migracji i rozjazd wyjdzie na produkcji.

Zasady:

- **Zawsze przeczytaj wygenerowaną migrację.** Autogeneracja nie wykrywa zmiany nazwy
  (widzi `drop column` + `add column`, co kasuje dane), zmian w `CHECK`, zmian typów enum
  ani przeniesień danych.
- **Migracja z danymi osobno od migracji ze schematem.** Przenoszenie danych w tej samej
  rewizji, która zmienia strukturę, uniemożliwia bezpieczny rollback.
- **Migracja musi działać na żywej bazie**, jeśli wdrożenie jest bez przestoju:

```python
# poprawnie: dodanie kolumny NOT NULL w trzech krokach, każdy w osobnym wdrożeniu
# 1) dodaj kolumnę nullowalną z wartością domyślną
op.add_column("faktury", sa.Column("waluta", sa.String(3), server_default="PLN"))
# 2) uzupełnij dane partiami (osobna rewizja)
op.execute("update faktury set waluta = 'PLN' where waluta is null")
# 3) ustaw NOT NULL (osobna rewizja, po wdrożeniu kodu piszącego kolumnę)
op.alter_column("faktury", "waluta", nullable=False)
```

- **Indeks na dużej tabeli**: `CREATE INDEX CONCURRENTLY`, poza transakcją:

```python
def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_faktury_org_data", "faktury", ["organizacja_id", "data_wystawienia"],
            postgresql_concurrently=True,
        )
```

Bez `CONCURRENTLY` tworzenie indeksu blokuje zapisy do tabeli na cały czas budowy.

- `downgrade()` piszemy zawsze, nawet jeśli nigdy go nie uruchomimy — wymuszenie
  odpowiedzi na pytanie „czy tę zmianę da się cofnąć”.
- Rozgałęzienia (dwie rewizje o tym samym `down_revision`) rozwiązuj przez
  `alembic merge`, nie przez ręczną edycję identyfikatorów.

## psycopg 3 i surowy SQL

```python
from sqlalchemy import text

# parametry ZAWSZE nazwane, nigdy f-string
wynik = await sesja.execute(
    text("""
        select k.nazwa, count(f.id) as ile, sum(f.kwota_netto) as suma
        from kontrahenci k
        join faktury f on f.kontrahent_id = k.id
        where k.organizacja_id = :org and f.data_wystawienia >= :od
        group by k.nazwa
        having sum(f.kwota_netto) > :prog
        order by suma desc
    """),
    {"org": org_id, "od": date(2026, 1, 1), "prog": Decimal("10000")},
)
for wiersz in wynik.mappings():
    print(wiersz["nazwa"], wiersz["suma"])
```

Surowy SQL jest lepszy niż ORM, gdy: zapytanie ma CTE, funkcje okna, `LATERAL`, `distinct on`,
operacje na JSONB, `insert ... on conflict` z warunkiem, albo gdy raport jest czytany raz
i nie potrzebuje obiektów. ORM jest lepszy, gdy wynik ma być zmodyfikowany i zapisany.

Wstawianie masowe — trzy poziomy:

```python
# 1. ORM, kilkaset rekordów
sesja.add_all([Faktura(...) for _ in range(500)])

# 2. Core, tysiące — jedno polecenie INSERT z wieloma wierszami
await sesja.execute(insert(Faktura), [{"numer": ..., "kwota_netto": ...}, ...])

# 3. COPY przez psycopg3, dziesiątki tysięcy i więcej
raw = await sesja.connection()
async with (await raw.get_raw_connection()).driver_connection.cursor() as cur:
    async with cur.copy(
        "copy faktury (id, numer, kwota_netto) from stdin"
    ) as copy:
        for w in wiersze:
            await copy.write_row((w.id, w.numer, w.kwota_netto))
```

`COPY` jest 10–50× szybszy od `INSERT` przy dużych wolumenach. Przy imporcie plików od
klienta to różnica między 40 sekundami a 20 minutami.

`insert ... on conflict` (upsert):

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

polecenie = pg_insert(Kontrahent).values(dane)
polecenie = polecenie.on_conflict_do_update(
    index_elements=["nip", "organizacja_id"],
    set_={"nazwa": polecenie.excluded.nazwa, "zmieniono": func.now()},
)
await sesja.execute(polecenie)
```

## SQLite w testach czy Postgres

**Postgres.** SQLite jako baza testowa wygląda kusząco (szybkie, bez zależności), ale:

| Różnica | Skutek |
|---|---|
| brak `JSONB`, `ARRAY`, typów `INET`, `tsvector` | modele używające ich w ogóle się nie utworzą |
| brak `on conflict` z `index_elements` w tej samej postaci | upsert trzeba pisać dwa razy |
| słabsza kontrola typów (dynamiczne typowanie) | test przechodzi, produkcja odrzuca |
| brak `FOR UPDATE SKIP LOCKED` | kolejka na tabeli nietestowalna |
| inne zachowanie sortowania i `LIKE` | testy tekstowe dają inne wyniki |
| brak wymuszania kluczy obcych domyślnie | test nie wykryje naruszenia więzów |

Testy jednostkowe logiki nie powinny w ogóle dotykać bazy (repozytorium jako `Protocol`). Testy
integracyjne uruchamiaj na Postgresie przez testcontainers — patrz
`references/engineering-core/02-python-backend-dane/references/testy-pytest.md`.

SQLite jest właściwy jako **baza produkcyjna** narzędzia jednostanowiskowego, aplikacji
desktopowej albo lokalnego cache. Wtedy: `PRAGMA journal_mode=WAL`,
`PRAGMA foreign_keys=ON` (domyślnie wyłączone), `PRAGMA synchronous=NORMAL`.

## Indeksy, które faktycznie pomagają

| Sytuacja | Indeks |
|---|---|
| `where organizacja_id = ? and status = ? order by data desc` | złożony `(organizacja_id, status, data desc)` — kolejność: równość, potem zakres/sortowanie |
| klucz obcy używany w `join` | osobny indeks — Postgres **nie** tworzy go automatycznie dla FK |
| `where usuniete_at is null` przy 5% aktywnych | częściowy: `... where usuniete_at is null` |
| `where lower(email) = ?` | funkcyjny: `create index on t (lower(email))` |
| wyszukiwanie po fragmencie `like '%tekst%'` | GIN + `pg_trgm` |
| pole JSONB odpytywane po kluczu | GIN na `dane->'klucz'` albo `jsonb_path_ops` |
| kolumna o dwóch wartościach (`aktywny bool`) | żaden — selektywność zbyt niska |

Czego nie robić: indeks na każdej kolumnie „na wszelki wypadek”. Każdy indeks spowalnia
`INSERT`/`UPDATE` i zajmuje miejsce; indeks nieużywany to czysty koszt.

Weryfikacja:

```sql
explain (analyze, buffers) select ...;
-- "Seq Scan" na dużej tabeli w zapytaniu z where = brak indeksu
-- "Rows Removed by Filter" duże = indeks jest, ale mało selektywny

-- indeksy nigdy nieużyte
select relname, indexrelname, idx_scan
from pg_stat_user_indexes where idx_scan = 0 order by relname;

-- najwolniejsze zapytania (wymaga rozszerzenia)
create extension if not exists pg_stat_statements;
select query, calls, mean_exec_time, total_exec_time
from pg_stat_statements order by total_exec_time desc limit 20;
```

Kolejność sprawdzania przy wolnej bazie: 1) N+1 w kodzie, 2) brak indeksu (`explain`),
3) zapytanie pobierające zbyt wiele kolumn/wierszy, 4) brak paginacji, 5) blokady
(`pg_locks`, `pg_stat_activity` ze stanem `idle in transaction`), 6) dopiero potem
parametry serwera.

`idle in transaction` na liście `pg_stat_activity` prawie zawsze oznacza, że kod
otwiera transakcję i czeka w niej na coś zewnętrznego — patrz reguła o wywołaniach HTTP
w transakcji.

## Paginacja

```python
# offset — prosta, ale wolna przy dużym offsecie (baza czyta i odrzuca wiersze)
select(Faktura).order_by(Faktura.id).limit(50).offset(strona * 50)

# kursorowa — stały czas niezależnie od głębokości
select(Faktura).where(Faktura.id > ostatni_id).order_by(Faktura.id).limit(50)
```

Powyżej kilku tysięcy wierszy przechodź na paginację kursorową. `OFFSET 100000` każe bazie
przeczytać 100 050 wierszy, żeby zwrócić 50.
