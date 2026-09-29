# Przetwarzanie danych: polars, pandas 3.0, DuckDB — sierpień 2026

polars **1.43.2**, pandas **3.0.5**, pyarrow **25.0.0**, numpy **2.5.1** (wymaga Pythona ≥3.12),
duckdb **1.5.5**, pandera **0.32.1**, narwhals **2.24.0**.

## Który silnik do czego

| Sytuacja | Wybór |
|---|---|
| Nowy kod, dane tabelaryczne, dowolny rozmiar | **polars** |
| Dane większe niż RAM, przebieg jednorazowy | polars lazy + `sink_parquet` |
| Zadanie jest w istocie SQL-em (złączenia, agregacje, okna) | **DuckDB** |
| Biblioteka trzecia zwraca/przyjmuje `DataFrame` pandas (scikit-learn, statsmodels, wiele API) | pandas |
| Istniejący kod na pandas, który działa | zostaw; nie przepisuj przy okazji |
| Kod ma działać na obu bez zmian (biblioteka) | narwhals jako warstwa pośrednia |
| Tablice liczbowe bez kolumn | numpy |

polars jest szybszy o rząd wielkości na typowych operacjach grupowania i złączeń, zużywa
mniej pamięci i ma czytelniejsze API wyrażeń. pandas ma szerszy ekosystem. Przy nowym
kodzie w DANACO domyślnie polars; pandas gdy wymusza go biblioteka odbiorcza.

## pandas 3.0 — co się zmieniło i psuje stary kod

pandas 3.0 jest największą zmianą od 1.0. Kod pisany z pamięci trafia w usunięte zachowania.

| Zmiana | Skutek |
|---|---|
| **Copy-on-Write jest jedynym trybem** | przypisanie łańcuchowe `df["a"][maska] = 1` nie działa — cicho nic nie zmienia albo rzuca błąd |
| `SettingWithCopyWarning` usunięte | ostrzeżenie, na którym opierał się stary debug, zniknęło |
| **Domyślny dtype tekstu to `str`, nie `object`** | `df.dtypes` pokazuje `str`; kod sprawdzający `== object` przestaje działać; `pyarrow` zalecany |
| **Rozdzielczość czasu nie jest już domyślnie nanosekundowa** | daty przed 1678 i po 2262 przestają wybuchać; `dtype` może być `datetime64[us]` |
| `pd.col()` — nowa składnia wyrażeń | `df.assign(x=pd.col("a") * 2)` zamiast lambdy |
| Usunięte API deprecjonowane w 2.x | `append`, `iteritems`, `mad`, `DataFrame.applymap` (→ `.map`) i inne |

Migracja: najpierw podnieś do pandas 2.3, uruchom testy z `-W error::DeprecationWarning`,
usuń wszystkie ostrzeżenia, dopiero potem 3.0.

```python
import pandas as pd

# ŹLE — przypisanie łańcuchowe, po CoW nie ma efektu
df["kwota"][df["status"] == "nowy"] = 0

# DOBRZE
df.loc[df["status"] == "nowy", "kwota"] = 0

# ŹLE — modyfikacja wycinka w nadziei, że zmieni oryginał
podzbior = df[df["rok"] == 2026]
podzbior["flaga"] = True          # zmienia tylko kopię

# DOBRZE — jawna kopia albo operacja na oryginale
podzbior = df[df["rok"] == 2026].copy()
podzbior["flaga"] = True

# nowa składnia wyrażeń
df = df.assign(
    brutto=pd.col("netto") * (1 + pd.col("vat")),
    duza=pd.col("netto") > 10_000,
)
```

## polars — podstawy, których model nie stosuje

Trzy rzeczy odróżniają polars od pandas i decydują o wydajności:

1. **Wyrażenia zamiast pętli i lambd.** `pl.col("x")` buduje opis operacji, który silnik
   wykonuje równolegle w Rust. `map_elements` wraca do Pythona wiersz po wierszu i jest
   100× wolniejsze — używaj go tylko, gdy naprawdę nie ma wyrażenia.
2. **Tryb leniwy (`scan_*` + `collect`).** Optymalizator zsuwa filtry do odczytu pliku
   (predicate pushdown) i czyta tylko potrzebne kolumny (projection pushdown).
3. **Brak indeksu.** Nie ma `set_index`, `reset_index`, `MultiIndex`. Wszystko jest kolumną.

```python
import polars as pl

# tryb leniwy — nic się nie liczy do collect()
lf = (
    pl.scan_parquet("dane/faktury/*.parquet")
    .filter(pl.col("data_wystawienia") >= pl.date(2026, 1, 1))
    .filter(pl.col("status") != "anulowana")
    .with_columns(
        brutto=pl.col("netto") * (1 + pl.col("stawka_vat")),
        miesiac=pl.col("data_wystawienia").dt.truncate("1mo"),
    )
    .group_by("organizacja_id", "miesiac")
    .agg(
        pl.len().alias("liczba"),
        pl.col("brutto").sum().alias("suma_brutto"),
        pl.col("brutto").mean().round(2).alias("srednia"),
        pl.col("brutto").quantile(0.95).alias("p95"),
        pl.col("kontrahent_id").n_unique().alias("kontrahentow"),
    )
    .sort("miesiac", "suma_brutto", descending=[False, True])
)

print(lf.explain())            # plan zapytania — pokazuje, co zostało zsunięte do skanu
df = lf.collect()              # dopiero tutaj czytanie i liczenie
```

`explain()` przed optymalizacją wydajności, zawsze. Jeśli w planie nie widać
`SELECTION: ...` przy `Parquet SCAN`, filtr nie został zsunięty i czytasz cały plik.

### Silnik strumieniowy — dane większe niż RAM

```python
# przetwarzanie z ograniczonym zużyciem pamięci
df = lf.collect(engine="streaming")

# zapis bez materializacji w pamięci — jedyna droga przy zbiorze > RAM
lf.sink_parquet("wynik.parquet", compression="zstd")
lf.sink_csv("wynik.csv")
```

Silnik strumieniowy jest **opcjonalny**, nie domyślny. Nie wszystkie operacje mają
implementację strumieniową; dla brakujących polars po cichu wraca do silnika w pamięci
dla tego fragmentu. Sprawdzenie, co faktycznie idzie strumieniem:

```python
lf.show_graph(plan_stage="physical", engine="streaming")
```

### Przetwarzanie partiami, gdy strumień nie wystarcza

```python
from pathlib import Path

import polars as pl


def przetworz_katalog(katalog: Path, cel: Path) -> None:
    """Plik po pliku — stałe zużycie pamięci niezależnie od liczby plików."""
    czesci: list[Path] = []
    for i, plik in enumerate(sorted(katalog.glob("*.csv"))):
        wynik = (
            pl.scan_csv(plik, schema_overrides={"nip": pl.String})
            .filter(pl.col("kwota") > 0)
            .group_by("kontrahent")
            .agg(pl.col("kwota").sum())
        )
        czesc = cel.parent / f"czesc_{i:04d}.parquet"
        wynik.sink_parquet(czesc)
        czesci.append(czesc)

    # scalenie i finalna agregacja
    (
        pl.scan_parquet(czesci)
        .group_by("kontrahent")
        .agg(pl.col("kwota").sum())
        .sink_parquet(cel)
    )
    for c in czesci:
        c.unlink()
```

## Wczytywanie i zapis

```python
import polars as pl

# CSV — zawsze podawaj typy kolumn, które muszą pozostać tekstem
df = pl.read_csv(
    "faktury.csv",
    separator=";",                       # polskie eksporty
    encoding="utf8-lossy",               # nie wywala się na złym bajcie
    schema_overrides={"nip": pl.String, "kod_pocztowy": pl.String},
    null_values=["", "NULL", "brak", "-"],
    try_parse_dates=True,
    decimal_comma=True,                  # "1234,56" -> 1234.56
    ignore_errors=False,                 # domyślnie błąd zamiast cichego null
)

# CSV leniwie
lf = pl.scan_csv("dane/*.csv", separator=";")

# Parquet — format pośredni pierwszego wyboru
df.write_parquet("dane.parquet", compression="zstd", statistics=True)
lf = pl.scan_parquet("dane/**/*.parquet", hive_partitioning=True)

# Excel (wymaga fastexcel albo xlsx2csv)
df = pl.read_excel("raport.xlsx", sheet_name="Dane", engine="calamine")

# JSON: zwykły vs linia-po-linii
df = pl.read_json("dane.json")
lf = pl.scan_ndjson("zdarzenia.jsonl")

# baza — przez connectorx (szybkie) lub sqlalchemy
df = pl.read_database_uri(
    query="select * from faktury where rok = 2026",
    uri="postgresql://user:haslo@host/baza",
    engine="connectorx",
)

# zapis do bazy
df.write_database("faktury", connection="postgresql://...", if_table_exists="append")
```

`nip` i `kod_pocztowy` jako `String` to nie kaprys: bez tego `0012345678` zostanie
odczytane jako liczba `12345678` i wiodące zera znikną bezpowrotnie.

Parquet zamiast CSV wszędzie, gdzie plik jest pośredni: typy zachowane, 5–10× mniejszy,
odczyt wybranych kolumn bez czytania reszty, statystyki pozwalające pominąć całe grupy
wierszy przy filtrze. CSV wyłącznie na styku ze światem zewnętrznym.

## Czyszczenie danych

```python
import polars as pl

czyste = (
    pl.scan_csv("surowe.csv", separator=";")
    .rename({"Nazwa Kontrahenta": "kontrahent", "NIP ": "nip"})
    .with_columns(
        # tekst: przycięcie, normalizacja wielkości, puste na null
        pl.col("kontrahent").str.strip_chars().str.to_titlecase(),
        pl.col("nip").str.replace_all(r"[\s\-]", ""),
        pl.col("email").str.to_lowercase().str.strip_chars(),
        # liczby zapisane po polsku
        pl.col("kwota")
        .str.replace_all(r"\s| ", "")
        .str.replace(",", ".")
        .cast(pl.Float64, strict=False)
        .alias("kwota"),
        # daty w kilku formatach
        pl.coalesce(
            pl.col("data").str.strptime(pl.Date, "%Y-%m-%d", strict=False),
            pl.col("data").str.strptime(pl.Date, "%d.%m.%Y", strict=False),
            pl.col("data").str.strptime(pl.Date, "%d/%m/%Y", strict=False),
        ).alias("data"),
    )
    .with_columns(
        # puste napisy na null PO oczyszczeniu
        pl.when(pl.col("kontrahent").str.len_chars() == 0)
        .then(None)
        .otherwise(pl.col("kontrahent"))
        .alias("kontrahent"),
    )
    .filter(pl.col("nip").str.len_chars() == 10)     # odrzuć nieparsowalne
    .unique(subset=["nip", "data", "kwota"], keep="first")
    .drop_nulls(subset=["nip", "kwota"])
)
```

Kolejność ma znaczenie: normalizacja tekstu → konwersja typów → puste na null → filtrowanie
→ deduplikacja. Odwrotna kolejność (deduplikacja przed normalizacją) zostawia duplikaty
różniące się wyłącznie spacją.

`strict=False` przy `cast` i `strptime` zamienia niepowodzenie na null zamiast wyjątku.
Zawsze policz, ile wartości wyszło null, i porównaj z oczekiwaniem — cichy null jest
gorszy niż błąd:

```python
raport = czyste.select(
    pl.all().null_count().name.suffix("_null"),
    pl.len().alias("wierszy"),
).collect()
```

## Łączenie

```python
wynik = faktury.join(
    kontrahenci,
    left_on="kontrahent_id",
    right_on="id",
    how="left",              # inner | left | right | full | semi | anti | cross
    suffix="_kontrahent",
    validate="m:1",          # sprawdza kardynalność — błąd, gdy prawa strona ma duplikaty
    coalesce=True,           # jedna kolumna klucza zamiast dwóch
)

# klucze złożone
a.join(b, on=["organizacja_id", "rok"], how="inner")

# semi/anti — filtr przez obecność, bez dołączania kolumn
tylko_z_fakturami = kontrahenci.join(faktury, left_on="id", right_on="kontrahent_id", how="semi")
bez_faktur = kontrahenci.join(faktury, left_on="id", right_on="kontrahent_id", how="anti")

# złączenie po najbliższej wcześniejszej dacie (kursy walut, ceny)
kursy_dla_faktur = faktury.sort("data").join_asof(
    kursy.sort("data"), on="data", by="waluta", strategy="backward"
)

# złączenie po przedziale
pl.LazyFrame.join_where(faktury, progi, pl.col("kwota") >= pl.col("prog_od"),
                        pl.col("kwota") < pl.col("prog_do"))
```

`validate="m:1"` to najtańsze zabezpieczenie przed najczęstszym błędem w łączeniu danych:
duplikat po prawej stronie mnoży wiersze i suma kontrolna rośnie bez powodu. Zawsze
sprawdzaj liczbę wierszy przed i po `join`.

## Agregacje i okna

```python
podsumowanie = (
    lf.group_by("organizacja_id", "miesiac")
    .agg(
        pl.len().alias("liczba"),
        pl.col("brutto").sum(),
        pl.col("brutto").mean().alias("srednia"),
        pl.col("brutto").median().alias("mediana"),
        pl.col("brutto").std().alias("odchylenie"),
        # agregacja warunkowa
        pl.col("brutto").filter(pl.col("status") == "oplacona").sum().alias("oplacone"),
        # liczenie warunkowe
        (pl.col("status") == "przeterminowana").sum().alias("przeterminowanych"),
        # pierwsza/ostatnia wartość po sortowaniu
        pl.col("numer").sort_by("data_wystawienia").last().alias("ostatnia_faktura"),
        # lista wartości do dalszej obróbki
        pl.col("kontrahent_id").unique().alias("kontrahenci"),
    )
)

# funkcje okna — agregat obok wiersza, bez grupowania
z_udzialem = lf.with_columns(
    suma_org=pl.col("brutto").sum().over("organizacja_id"),
    udzial=(pl.col("brutto") / pl.col("brutto").sum().over("organizacja_id")).round(4),
    numer_w_grupie=pl.col("brutto").rank("dense", descending=True).over("organizacja_id"),
    narastajaco=pl.col("brutto").cum_sum().over("organizacja_id", order_by="data"),
)

# przestawienie
szeroka = df.pivot(on="miesiac", index="organizacja_id", values="brutto",
                   aggregate_function="sum")
dluga = szeroka.unpivot(index="organizacja_id", variable_name="miesiac",
                        value_name="brutto")
```

## Daty i strefy czasowe

```python
import polars as pl

df = df.with_columns(
    # tekst -> data
    pl.col("data_txt").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S"),
    # nadanie strefy naiwnemu znacznikowi (dane przyszły jako czas lokalny)
    pl.col("ts").dt.replace_time_zone("Europe/Warsaw"),
    # konwersja między strefami (znacznik ma już strefę)
    pl.col("ts_utc").dt.convert_time_zone("Europe/Warsaw"),
    # składowe
    pl.col("data").dt.year().alias("rok"),
    pl.col("data").dt.month().alias("miesiac"),
    pl.col("data").dt.weekday().alias("dzien_tygodnia"),   # 1 = poniedziałek
    pl.col("data").dt.truncate("1mo").alias("poczatek_miesiaca"),
    pl.col("data").dt.offset_by("1mo").alias("za_miesiac"),
    # różnica
    (pl.col("zaplacono") - pl.col("wystawiono")).dt.total_days().alias("dni_do_zaplaty"),
)

# uzupełnienie brakujących dat w szeregu
pelny = df.upsample(time_column="data", every="1d").fill_null(strategy="forward")

# agregacja po oknie czasowym
tygodniowo = df.group_by_dynamic("data", every="1w", period="1w").agg(pl.col("kwota").sum())
```

Trzy reguły, których złamanie kosztuje najwięcej:

1. **Przechowuj i licz w UTC, konwertuj na strefę lokalną wyłącznie przy wyświetlaniu.**
2. `replace_time_zone` (nadaje strefę, nie zmienia wartości) to co innego niż
   `convert_time_zone` (przelicza wartość). Pomylenie daje przesunięcie o 1–2 godziny,
   które widać dopiero na granicy doby.
3. Zmiana czasu: 2:30 czasu środkowoeuropejskiego w ostatnią niedzielę marca **nie istnieje**,
   a w październiku występuje dwa razy. Konwersja takich znaczników wymaga świadomej
   decyzji (`ambiguous="earliest"/"latest"/"raise"`).

W pandas 3.0 domyślna rozdzielczość znaczników nie jest już nanosekundowa, więc daty
historyczne (przed 1678) i odległe (po 2262) przestały przepełniać zakres. Kod zakładający
`datetime64[ns]` może dostać `datetime64[us]`.

## DuckDB — gdy zadanie jest SQL-em

```python
import duckdb
import polars as pl

conn = duckdb.connect()          # w pamięci; duckdb.connect("plik.db") na dysku

# odczyt bezpośrednio z plików, bez wczytywania do Pythona
wynik = conn.execute("""
    select
        k.nazwa,
        date_trunc('month', f.data_wystawienia) as miesiac,
        sum(f.kwota_netto) as suma,
        count(*) as liczba,
        sum(f.kwota_netto) / sum(sum(f.kwota_netto)) over () as udzial
    from read_parquet('dane/faktury/*.parquet') f
    join read_csv('dane/kontrahenci.csv', delim=';') k on k.id = f.kontrahent_id
    where f.data_wystawienia >= date '2026-01-01'
    group by 1, 2
    having sum(f.kwota_netto) > 10000
    order by suma desc
""").pl()                        # .pl() -> polars, .df() -> pandas, .arrow() -> pyarrow

# ramka polars widoczna dla SQL bez kopiowania
faktury = pl.scan_parquet("faktury.parquet").collect()
conn.execute("select count(*) from faktury").fetchone()

# zapis wyniku prosto do pliku
conn.execute("copy (select * from read_parquet('a.parquet') where x > 0) "
             "to 'wynik.parquet' (format parquet, compression zstd)")
```

DuckDB czyta Parquet i CSV bez ładowania całości do pamięci i radzi sobie z plikami
większymi niż RAM. Wybieraj go, gdy zapytanie ma wiele złączeń i funkcji okna — SQL jest
wtedy czytelniejszy niż łańcuch wyrażeń.

## Walidacja danych

Dane od klienta zawsze walidujesz przed przetworzeniem. Dwa narzędzia:

```python
# Pandera — walidacja całej ramki, deklaratywnie
import pandera.polars as pa
from pandera.typing.polars import LazyFrame


class SchematFaktur(pa.DataFrameModel):
    nip: str = pa.Field(str_matches=r"^\d{10}$")
    numer: str = pa.Field(unique=True)
    kwota_netto: float = pa.Field(ge=0, le=10_000_000)
    data_wystawienia: pa.DateTime
    status: str = pa.Field(isin=["szkic", "wystawiona", "oplacona", "anulowana"])
    email: str = pa.Field(nullable=True, str_matches=r"^[^@]+@[^@]+\.[a-z]{2,}$")

    class Config:
        strict = True            # nieznana kolumna = błąd
        coerce = True            # próba rzutowania typu

    @pa.check("kwota_netto")
    def suma_dodatnia(cls, s) -> bool:
        return s.sum() > 0


try:
    zwalidowane = SchematFaktur.validate(df, lazy=True)   # lazy: zbierz WSZYSTKIE błędy
except pa.errors.SchemaErrors as e:
    print(e.failure_cases)       # ramka z listą naruszeń: kolumna, reguła, wartość, indeks
```

```python
# Pydantic — walidacja rekord po rekordzie, gdy potrzebna logika w Pythonie
from pydantic import BaseModel, TypeAdapter

class Rekord(BaseModel):
    nip: str
    kwota: Decimal

adapter = TypeAdapter(list[Rekord])
rekordy = adapter.validate_python(df.to_dicts())
```

Kryterium wyboru: Pandera dla ramek (szybka, wektorowa, raport wszystkich naruszeń naraz),
Pydantic dla strumienia rekordów i złożonych reguł międzypolowych. Pydantic na 5 milionach
wierszy jest za wolny — walidacja obiekt po obiekcie w Pythonie.

Minimalna walidacja, gdy nie chcesz zależności:

```python
def sprawdz(df: pl.DataFrame) -> None:
    problemy: list[str] = []
    if df.height == 0:
        problemy.append("pusty zbiór")
    wymagane = {"nip", "numer", "kwota_netto", "data_wystawienia"}
    if brak := wymagane - set(df.columns):
        problemy.append(f"brak kolumn: {sorted(brak)}")
    nulle = df.select(pl.col("nip").null_count()).item()
    if nulle:
        problemy.append(f"nip null w {nulle} wierszach")
    if df.select(pl.col("numer").is_duplicated().sum()).item():
        problemy.append("zduplikowane numery faktur")
    if problemy:
        raise ValueError("; ".join(problemy))
```

## Wydajność — co daje efekt

| Działanie | Zysk |
|---|---|
| `scan_*` + `collect()` zamiast `read_*` + operacje | duży — pushdown filtrów i kolumn |
| `select` tylko potrzebnych kolumn na początku | duży przy szerokich tabelach |
| Parquet zamiast CSV | 3–10× na odczycie |
| Wyrażenia zamiast `map_elements` / `apply` | 10–100× |
| `pl.Categorical` na kolumnach o niskiej liczności | mniej pamięci, szybsze grupowanie |
| Typy węższe (`Int32` zamiast `Int64`, `Float32`) | ~2× mniej pamięci |
| `join` po posortowanych kluczach | mniejsze zużycie pamięci |
| `engine="streaming"` przy zbiorze > RAM | możliwość wykonania w ogóle |

Antywzorce, które zabijają wydajność:

- `for wiersz in df.iter_rows()` — pętla po Pythonie zamiast wyrażenia. Jeśli musisz,
  przynajmniej `iter_rows(named=True)` i tylko na małym zbiorze.
- `df = pl.concat([df, nowy])` w pętli — kwadratowe kopiowanie. Zbieraj do listy,
  `pl.concat` raz na końcu.
- `collect()` w środku łańcucha „żeby zobaczyć” — przerywa optymalizację. Użyj `.head(5).collect()`.
- `map_elements` z funkcją, która ma odpowiednik w wyrażeniach (`str.contains`, `when/then`).
- Wczytanie 40 kolumn, gdy używasz 4.

## Jupyter — do czego, a do czego nie

Notatnik jest właściwy do: pierwszego kontaktu ze zbiorem, sprawdzenia hipotezy, wykresu
do prezentacji, dokumentacji analizy z wynikami.

Notatnik **nie** jest właściwy do: kodu uruchamianego cyklicznie, logiki importowanej przez
inne moduły, czegokolwiek, co ma testy, czegokolwiek na produkcji.

Powód nie jest estetyczny: stan komórek zależy od kolejności wykonania, a nie od kolejności
w pliku. Notatnik, który działa u autora, u kogoś innego wywala się w komórce 3, bo autor
uruchomił ją przed komórką 7 i już nie pamięta.

Ścieżka wyjścia z notatnika:

1. Funkcje wydzielone do `src/pakiet/analiza.py`, notatnik je importuje.
2. Test na każdej wydzielonej funkcji.
3. Skrypt wejściowy
   (`references/engineering-core/02-python-backend-dane/references/cli-i-narzedzia.md`) albo zadanie
   w kolejce.
4. Notatnik zostaje jako dokumentacja, nie jako kod produkcyjny.

Do jednorazowej analizy bez zakładania projektu: skrypt PEP 723 z `# /// script` —
`uv run analiza.py` sam zbuduje środowisko.

```bash
uv run --with jupyterlab --with polars --with altair jupyter lab
```

`uv run --with` zamiast dodawania jupytera do zależności projektu: notatnikowe zależności
nie zaśmiecają `pyproject.toml` usługi.
