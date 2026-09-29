# Narzędzia CLI i skrypty — sierpień 2026

Typer **0.27.1**, Click **8.x**, rich **15.0.0**, uv **0.12.1**, Python **3.14.6**.

## Co wybrać

| Zadanie | Narzędzie |
|---|---|
| Jednorazowa analiza, skrypt uruchamiany ręcznie | skrypt PEP 723 + `uv run` |
| Narzędzie z kilkoma poleceniami, używane przez zespół | Typer w projekcie, punkt wejścia w `[project.scripts]` |
| Wtyczki, dynamiczne grupy poleceń, pełna kontrola | Click |
| Parsowanie 2–3 argumentów bez zależności | `argparse` |
| Narzędzie dla ludzi spoza zespołu | Typer + `rich` + jasne komunikaty błędów |

Typer stoi na Click i dodaje wyprowadzanie parametrów z adnotacji typów. Jeśli potrzebujesz
czegoś, czego Typer nie wystawia (własne `ParamType`, `CommandCollection`, lazy loading
grup), zejdź na Click — nie obchodź Typera hackami.

## Skrypt jednoplikowy z zależnościami inline (PEP 723)

Metadane w komentarzu na górze pliku. `uv run` czyta je, buduje środowisko w cache i
uruchamia skrypt. Bez `pyproject.toml`, bez ręcznego tworzenia venv.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx>=0.28",
#     "polars>=1.43",
#     "rich>=15.0",
# ]
# ///
"""Pobiera kursy NBP i zapisuje do Parquet."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import polars as pl
from rich.console import Console

console = Console(stderr=True)
URL = "https://api.nbp.pl/api/exchangerates/tables/A/{od}/{do}/?format=json"


def pobierz(od: date, do: date) -> pl.DataFrame:
    odp = httpx.get(URL.format(od=od.isoformat(), do=do.isoformat()), timeout=30.0)
    if odp.status_code == 404:
        return pl.DataFrame(schema={"data": pl.Date, "kod": pl.String, "kurs": pl.Float64})
    odp.raise_for_status()
    wiersze = [
        {"data": date.fromisoformat(t["effectiveDate"]), "kod": r["code"], "kurs": r["mid"]}
        for t in odp.json()
        for r in t["rates"]
    ]
    return pl.DataFrame(wiersze)


def main() -> int:
    do = date.today()
    od = do - timedelta(days=30)
    cel = Path("kursy.parquet")
    try:
        df = pobierz(od, do)
    except httpx.HTTPError as e:
        console.print(f"[red]Błąd pobierania:[/red] {e}")
        return 1
    if df.is_empty():
        console.print("[yellow]Brak danych w zadanym zakresie[/yellow]")
        return 1
    df.write_parquet(cel)
    console.print(f"[green]Zapisano[/green] {df.height} wierszy do {cel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

```bash
uv run kursy.py            # uv sam zbuduje środowisko
chmod +x kursy.py && ./kursy.py    # dzięki shebangowi z --script

uv init --script nowy.py --python 3.13      # tworzy nagłówek
uv add --script nowy.py httpx polars        # dopisuje zależności do nagłówka
uv lock --script nowy.py                    # tworzy nowy.py.lock — powtarzalność
```

Kiedy skrypt PEP 723 przestaje wystarczać: gdy ma więcej niż ~300 linii, gdy potrzebuje
testów, gdy inny moduł ma z niego importować. Wtedy `uv init --package` i przeniesienie
kodu do `src/`.

## Typer — narzędzie z poleceniami

```python
# src/danaco_narzedzia/cli.py
from __future__ import annotations

import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="danaco",
    help="Narzędzia DANACO do przetwarzania faktur.",
    no_args_is_help=True,           # wywołanie bez argumentów pokazuje pomoc
    add_completion=True,
    pretty_exceptions_show_locals=False,   # zmienne lokalne w śladzie stosu = wyciek
)
konsola = Console()
blad = Console(stderr=True)


class Format(StrEnum):
    TABELA = "tabela"
    JSON = "json"
    CSV = "csv"


class Kody:
    OK = 0
    BLAD_OGOLNY = 1
    ZLE_UZYCIE = 2
    BRAK_PLIKU = 3
    WALIDACJA = 4
    PRZERWANE = 130


@app.callback()
def wspolne(
    ctx: typer.Context,
    gadatliwy: Annotated[bool, typer.Option("--verbose", "-v", help="Więcej logów")] = False,
    cicho: Annotated[bool, typer.Option("--quiet", "-q", help="Tylko błędy")] = False,
    konfiguracja: Annotated[
        Path | None,
        typer.Option("--config", "-c", envvar="DANACO_CONFIG", help="Plik konfiguracji"),
    ] = None,
) -> None:
    """Opcje wspólne dla wszystkich poleceń."""
    if gadatliwy and cicho:
        blad.print("[red]--verbose i --quiet wykluczają się[/red]")
        raise typer.Exit(Kody.ZLE_UZYCIE)
    ctx.obj = {"gadatliwy": gadatliwy, "cicho": cicho, "config": konfiguracja}


@app.command()
def waliduj(
    plik: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True,
                                         help="Plik CSV z fakturami")],
    format_: Annotated[Format, typer.Option("--format", "-f")] = Format.TABELA,
    limit: Annotated[int, typer.Option("--limit", "-n", min=1, max=1000)] = 100,
) -> None:
    """Sprawdza plik faktur i wypisuje naruszenia."""
    naruszenia = sprawdz_plik(plik, limit=limit)

    if format_ is Format.JSON:
        # wyjście dla maszyny -> stdout, czysty JSON, nic więcej
        json.dump([n.__dict__ for n in naruszenia], sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        tabela = Table(title=f"Naruszenia w {plik.name}")
        tabela.add_column("Wiersz", justify="right")
        tabela.add_column("Pole")
        tabela.add_column("Problem")
        for n in naruszenia:
            tabela.add_row(str(n.wiersz), n.pole, n.problem)
        konsola.print(tabela)

    raise typer.Exit(Kody.WALIDACJA if naruszenia else Kody.OK)


@app.command()
def importuj(
    zrodlo: Annotated[Path, typer.Argument(exists=True)],
    baza: Annotated[str, typer.Option(envvar="DANACO_DB_URL", prompt=False)],
    na_sucho: Annotated[bool, typer.Option("--dry-run", help="Nie zapisuj")] = False,
    potwierdz: Annotated[bool, typer.Option("--yes", "-y", help="Bez pytania")] = False,
) -> None:
    """Wczytuje faktury z pliku do bazy."""
    liczba = policz_wiersze(zrodlo)
    if not na_sucho and not potwierdz:
        typer.confirm(f"Zaimportować {liczba} rekordów do bazy?", abort=True)
    wstawione = wykonaj_import(zrodlo, baza, na_sucho=na_sucho)
    konsola.print(
        f"[green]{'Do wstawienia' if na_sucho else 'Wstawiono'}:[/green] {wstawione}"
    )


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        blad.print("\n[yellow]Przerwano[/yellow]")
        sys.exit(Kody.PRZERWANE)


if __name__ == "__main__":
    main()
```

Rejestracja polecenia w `pyproject.toml`:

```toml
[project.scripts]
danaco = "danaco_narzedzia.cli:main"
```

Po `uv sync` polecenie `danaco` działa w środowisku projektu; po `uv tool install .`
dostępne jest globalnie.

`exists=True` i `dir_okay=False` w `typer.Argument` przenoszą walidację ścieżki do Typera:
komunikat jest jednolity, a kod polecenia nie zaczyna się od trzech `if`. `envvar=`
pozwala podać wartość ze środowiska bez dodatkowej logiki.

`pretty_exceptions_show_locals=False` jest istotne: domyślnie Typer przy nieobsłużonym
wyjątku drukuje zmienne lokalne, a wśród nich bywa hasło do bazy.

## Konfiguracja: kolejność źródeł

Ustalona kolejność, od najsilniejszego: **argument CLI → zmienna środowiskowa → plik
konfiguracyjny → wartość domyślna w kodzie**.

```python
import tomllib
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Konfiguracja(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DANACO_", env_file=".env")

    db_url: str = "postgresql://localhost/danaco"
    rownolegle: int = Field(default=4, ge=1, le=64)
    limit_wierszy: int = 100_000


def wczytaj(sciezka: Path | None, **nadpisania_cli) -> Konfiguracja:
    z_pliku: dict = {}
    kandydat = sciezka or Path("danaco.toml")
    if kandydat.exists():
        z_pliku = tomllib.loads(kandydat.read_text(encoding="utf-8")).get("danaco", {})
    # env obsługuje BaseSettings; plik i CLI podajemy jawnie,
    # CLI na końcu, żeby wygrywało
    jawne = {k: v for k, v in nadpisania_cli.items() if v is not None}
    return Konfiguracja(**(z_pliku | jawne))
```

`tomllib` jest w bibliotece standardowej od 3.11 (tylko odczyt). Do zapisu TOML potrzebny
`tomli-w`. Dla plików konfiguracyjnych narzędzi TOML jest właściwszy niż JSON (komentarze)
i niż YAML (brak niejednoznaczności typu `no` → `False`).

## Wyjście dla człowieka i dla maszyny

To jest jedyna rzecz, która odróżnia narzędzie użyteczne w potoku od zabawki.

| Strumień | Co tam trafia |
|---|---|
| **stdout** | wyłącznie wynik: dane, które ktoś przekieruje do pliku albo do `jq` |
| **stderr** | wszystko inne: postęp, ostrzeżenia, błędy, komunikaty diagnostyczne |

```python
konsola = Console()                 # stdout — wynik
blad = Console(stderr=True)         # stderr — komunikaty
```

Zasady:

- Flaga `--format json` (albo `--json`) na każdym poleceniu zwracającym dane.
- W trybie JSON na stdout **nic** poza JSON-em. Żadnych nagłówków, żadnych kolorów,
  żadnego „Gotowe!”. Inaczej `| jq` się wywala.
- Wykrywanie terminala: `sys.stdout.isatty()`. Brak terminala (przekierowanie, potok) →
  bez kolorów, bez paska postępu, bez tabel z ramkami. `rich.Console` robi to sam.
- Uszanuj `NO_COLOR` (dowolna niepusta wartość) i `TERM=dumb`.
- Jedna linia = jeden rekord w trybie strumieniowym (NDJSON), żeby dało się to przetwarzać
  bez czekania na koniec.

```python
def wypisz(dane: list[dict], format_: Format) -> None:
    match format_:
        case Format.JSON:
            json.dump(dane, sys.stdout, ensure_ascii=False, default=str)
            sys.stdout.write("\n")
        case Format.CSV:
            pisarz = csv.DictWriter(sys.stdout, fieldnames=list(dane[0]), delimiter=";")
            pisarz.writeheader()
            pisarz.writerows(dane)
        case Format.TABELA:
            if not sys.stdout.isatty():
                for r in dane:                      # potok -> forma prosta
                    print("\t".join(str(v) for v in r.values()))
            else:
                konsola.print(zbuduj_tabele(dane))
```

## Kody wyjścia

```python
class Kody:
    OK = 0
    BLAD_OGOLNY = 1
    ZLE_UZYCIE = 2          # zła składnia wywołania (Click/Typer używa 2 automatycznie)
    BRAK_PLIKU = 3
    WALIDACJA = 4           # dane niepoprawne, ale narzędzie zadziałało
    NIEDOSTEPNA_USLUGA = 5
    PRZERWANE = 130         # SIGINT: 128 + 2
```

Kod 0 oznacza sukces i **nic więcej**. Narzędzie walidujące, które znalazło błędy w danych,
zwraca kod niezerowy — inaczej `narzedzie waliduj && wdroz` wdroży złe dane.

Kody 1–125 są wolne; 126–165 zarezerwowane przez powłokę (126 = brak prawa wykonania,
127 = nie znaleziono polecenia, 128+n = zabity sygnałem n). Nie używaj wartości powyżej 125.

`raise typer.Exit(kod)` zamiast `sys.exit(kod)` wewnątrz polecenia — Typer wykona
sprzątanie kontekstu.

## Postęp i długie operacje

```python
from rich.progress import (
    BarColumn, MofNCompleteColumn, Progress, SpinnerColumn,
    TextColumn, TimeElapsedColumn, TimeRemainingColumn,
)


def przetworz_pliki(pliki: list[Path]) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=Console(stderr=True),      # postęp na stderr, nie na stdout
        transient=True,                    # znika po zakończeniu
        disable=not sys.stderr.isatty(),   # brak paska w CI i w potoku
    ) as postep:
        zadanie = postep.add_task("Przetwarzanie", total=len(pliki))
        for plik in pliki:
            przetworz(plik)
            postep.update(zadanie, advance=1, description=f"Przetwarzanie {plik.name}")
```

`disable=not sys.stderr.isatty()` jest obowiązkowe: pasek postępu w logu CI generuje
tysiące linii z sekwencjami sterującymi i czyni log nieczytelnym.

Przy operacji bez znanej liczby kroków: `SpinnerColumn` bez `total`, plus komunikat co
n sekund — użytkownik musi wiedzieć, że coś się dzieje.

## Komunikaty błędów

Zły: `Error: KeyError: 'nip'`
Dobry: `Błąd: plik faktury.csv nie zawiera kolumny "nip". Znalezione kolumny: numer, data, kwota.`

Komunikat błędu ma zawierać: co się stało, w czym (plik, wiersz, pole), i co z tym zrobić.

```python
def wczytaj_plik(sciezka: Path) -> pl.DataFrame:
    try:
        df = pl.read_csv(sciezka, separator=";")
    except FileNotFoundError:
        blad.print(f"[red]Nie znaleziono pliku:[/red] {sciezka}")
        raise typer.Exit(Kody.BRAK_PLIKU) from None
    except pl.exceptions.ComputeError as e:
        blad.print(f"[red]Nie udało się odczytać {sciezka.name}:[/red] {e}")
        blad.print("Sprawdź separator (oczekiwano ';') i kodowanie (oczekiwano UTF-8).")
        raise typer.Exit(Kody.BLAD_OGOLNY) from None

    if brak := {"nip", "kwota"} - set(df.columns):
        blad.print(f"[red]Brak wymaganych kolumn:[/red] {', '.join(sorted(brak))}")
        blad.print(f"Kolumny w pliku: {', '.join(df.columns)}")
        raise typer.Exit(Kody.WALIDACJA)
    return df
```

Ślad stosu tylko przy `--verbose` albo przy błędzie nieoczekiwanym. Użytkownik narzędzia
nie ma czytać `Traceback (most recent call last)`.

Operacja destrukcyjna wymaga potwierdzenia (`typer.confirm(..., abort=True)`) i ma mieć
`--dry-run`, który pokazuje, co by się stało. `--yes` do użycia w skryptach.

## Pakowanie i dystrybucja

```bash
# instalacja globalna z katalogu projektu
uv tool install .
uv tool install --editable .              # tryb rozwoju: zmiany widoczne od razu

# z repozytorium git
uv tool install git+https://github.com/danaco/narzedzia@v1.2.0

# jednorazowe uruchomienie bez instalacji
uvx --from git+https://github.com/danaco/narzedzia danaco waliduj plik.csv

uv tool list
uv tool upgrade danaco-narzedzia
uv tool uninstall danaco-narzedzia
```

`uv tool` instaluje w izolowanym środowisku i dowiązuje polecenia w `~/.local/bin`
(sprawdź `uv tool update-shell`, jeśli katalogu nie ma w `PATH`). Zastępuje pipx — nie
ma powodu instalować obu.

Uzupełnianie w powłoce (Typer generuje je sam):

```bash
danaco --install-completion       # bash, zsh, fish, powershell
```

Dystrybucja wewnątrz firmy: budowanie koła i instalacja z pliku albo z prywatnego indeksu.

```bash
uv build                                   # dist/*.whl + dist/*.tar.gz
uv tool install dist/danaco_narzedzia-1.2.0-py3-none-any.whl
```

Do publikacji na prywatnym indeksie dodaj w `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "danaco"
url = "https://pypi.wewnetrzny.danacogroup.com.pl/simple"
publish-url = "https://pypi.wewnetrzny.danacogroup.com.pl/upload"
```

```bash
UV_PUBLISH_TOKEN=... uv publish --index danaco
```

## Lista kontrolna narzędzia CLI

- [ ] `--help` opisuje, co narzędzie robi, i ma przykład wywołania.
- [ ] Wynik na stdout, komunikaty na stderr; tryb `--format json` bez zanieczyszczeń.
- [ ] Kod wyjścia 0 wyłącznie przy pełnym sukcesie.
- [ ] Kolory i pasek postępu wyłączone poza terminalem; `NO_COLOR` uszanowane.
- [ ] Operacja destrukcyjna: potwierdzenie + `--dry-run` + `--yes`.
- [ ] Ctrl+C kończy czysto (kod 130), bez śladu stosu.
- [ ] Komunikaty błędów po polsku, z nazwą pliku i wskazówką naprawy.
- [ ] Sekrety wyłącznie z `envvar=` albo pliku; nigdy w argumencie (widoczne w `ps` i historii
  powłoki).
- [ ] Sprawdzone na pustym wejściu i na pliku o złym formacie.
