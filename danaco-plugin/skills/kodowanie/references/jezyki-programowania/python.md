# Python — karta

## Standard stylu i nazewnictwa

Stosuj PEP 8 jako obowiązujący standard stylu oraz PEP 257 dla docstringów. Egzekwuj konwencje
nazewnicze:

- funkcje, metody, zmienne, moduły i pliki: `snake_case` (np. `calculate_invoice_total`,
  `payment_gateway.py`);
- klasy i wyjątki: `PascalCase` (np. `InvoiceProcessor`, `PaymentDeclinedError`);
- stałe modułowe: `UPPER_SNAKE_CASE` (np. `MAX_RETRY_COUNT`);
- składowe niepubliczne: pojedynczy podkreślnik wiodący (`_internal_cache`);
- nazwy testów: `test_<zachowanie>` opisujące oczekiwany rezultat, nie implementację.

Stosuj adnotacje typów (PEP 484 i nowsze) we wszystkich publicznych sygnaturach. Narzędzia przyjęte
zawodowo:

- formatowanie: Black lub `ruff format` (długość linii zgodna z konfiguracją projektu);
- lintowanie: Ruff (obejmuje reguły Flake8, isort, pyupgrade, flake8-bugbear);
- kontrola typów: mypy lub Pyright.

Jeżeli projekt zawiera już konfigurację w `pyproject.toml`, respektuj ją bez wyjątków — nie narzucaj
własnych ustawień formatera.

## Struktura projektu

Stosuj układ `src/` jako kanoniczny dla pakietów instalowalnych:

```
projekt/
├── pyproject.toml        # jedyne źródło metadanych i konfiguracji narzędzi
├── README.md
├── src/
│   └── package_name/
│       ├── __init__.py   # eksport publicznego API pakietu
│       ├── core.py
│       └── cli.py        # punkt wejścia rejestrowany w [project.scripts]
└── tests/
    ├── conftest.py       # współdzielone fixtures
    └── test_core.py
```

Umieszczaj całą konfigurację (build, Ruff, mypy, pytest) w `pyproject.toml`. Czego nie tworzyć:

- `setup.py` ani `setup.cfg` w nowych projektach — deklaratywny `pyproject.toml` (PEP 517/518/621)
  jest standardem;
- `requirements.txt` równolegle do zależności zadeklarowanych w `pyproject.toml`, chyba że pełni
  rolę pliku blokady generowanego narzędziem;
- pustych plików `__init__.py` poza katalogami pakietów;
- katalogów narzędziowych typu `utils/` z jednym plikiem — umieszczaj kod w module o nazwie
  opisującej dziedzinę.

## Budowa i zależności

Pracuj wyłącznie w środowisku wirtualnym (`python -m venv`, uv lub Poetry) — nigdy nie instaluj
zależności globalnie. Zasady:

- deklaruj zależności w `pyproject.toml` w sekcji `[project.dependencies]` z zakresami wersji (np.
  `requests>=2.31`);
- dokładne wersje przypinaj w pliku blokady (`uv.lock`, `poetry.lock` lub `requirements.txt` z
  `pip-compile`); plik blokady commituj w aplikacjach, w bibliotekach przypinaj tylko zakresy;
- zależności deweloperskie (pytest, ruff, mypy) trzymaj w osobnej grupie (`[dependency-groups]` lub
  odpowiedniku danego narzędzia);
- instaluj projekt w trybie edytowalnym podczas prac: `pip install -e .` lub `uv sync`;
- przed wyborem polecenia instalacji sprawdź, którego menedżera używa projekt (obecność `uv.lock`,
  `poetry.lock`, `Pipfile`).

Wymagaj Python 3.10+ dla nowego kodu, chyba że projekt deklaruje inaczej w polu `requires-python`.

## Testy

Stosuj pytest jako standardowy framework — nie pisz nowych testów w stylu `unittest.TestCase`,
jeżeli projekt tego nie wymaga. Układ i praktyki:

- katalog `tests/` odzwierciedlający strukturę pakietu; pliki `test_*.py`, funkcje `test_*`;
- fixtures (w `conftest.py` dla współdzielonych) zamiast metod `setUp`/`tearDown`;
- `pytest.mark.parametrize` dla wariantów danych wejściowych;
- `pytest.raises` z argumentem `match=` dla asercji wyjątków;
- `monkeypatch` lub `unittest.mock` do izolacji zależności zewnętrznych; nie wykonuj prawdziwych
  żądań sieciowych w testach jednostkowych.

Konfigurację trzymaj w `[tool.pytest.ini_options]` w `pyproject.toml`. Uruchamiaj testy poleceniem
`python -m pytest` z katalogu głównego projektu — forma `python -m` gwarantuje właściwe środowisko i
ścieżki importu. Pokrycie mierz narzędziem `pytest-cov` tylko wtedy, gdy projekt tego wymaga.

## Diagnostyka

Do interaktywnego debugowania stosuj `breakpoint()` (uruchamia pdb) zamiast tymczasowych wywołań
`print`. Do profilowania używaj `cProfile` (`python -m cProfile -s cumulative script.py`) oraz
`line_profiler` dla analizy pojedynczych funkcji; pamięć badaj narzędziem `tracemalloc`. Ślady
błędów (traceback) czytaj od dołu: ostatnia linia zawiera typ i komunikat wyjątku, a najniższa ramka
pochodząca z kodu projektu (nie z bibliotek) wskazuje miejsce błędu. Zwracaj uwagę na łańcuchy `The
above exception was the direct cause of...` — pierwotna przyczyna jest w najwyższym śladzie
łańcucha.

Typowe klasy błędów i ich rozpoznanie:

- `AttributeError: 'NoneType' object has no attribute ...` — funkcja zwróciła `None` zamiast
  oczekiwanego obiektu; szukaj brakującego `return` lub nieobsłużonego przypadku;
- `ImportError`/`ModuleNotFoundError` — złe środowisko wirtualne, brak instalacji w trybie
  edytowalnym lub import cykliczny;
- `TypeError` przy wywołaniu — niezgodność sygnatury; porównaj z definicją, nie zgaduj argumentów;
- `UnicodeDecodeError` — brak jawnego `encoding="utf-8"` przy otwieraniu plików tekstowych;
- `RuntimeError: dictionary changed size during iteration` — modyfikacja kolekcji podczas iteracji;
  iteruj po kopii lub zbieraj zmiany osobno.

## Typowe błędy modeli LLM w tym języku

1. **Mutowalne wartości domyślne argumentów** (`def f(items=[])`): lista jest współdzielona między
   wywołaniami. Poprawny wzorzec:

```python
def collect(items: list[str] | None = None) -> list[str]:
    # inicjalizacja wewnątrz funkcji, nie w sygnaturze
    items = items if items is not None else []
    return items
```

2. **Przestarzałe typy z modułu `typing`**: `List[int]`, `Dict[str, int]`, `Optional[str]` w kodzie dla Python 3.10+. Stosuj wbudowane generyki `list[int]`, `dict[str, int]` oraz składnię unii `str | None`.
3. **Gołe `except:` lub `except Exception: pass`**: przechwytuje także `KeyboardInterrupt` i maskuje
   błędy. Łap wyłącznie konkretne wyjątki; obsługuj je albo loguj i zgłaszaj ponownie (`raise`).
4. **`datetime.utcnow()`**: metoda przestarzała, zwraca czas naiwny (bez strefy). Stosuj
   `datetime.now(timezone.utc)`.
5. **Operacje na ścieżkach przez `os.path` i konkatenację łańcuchów**: stosuj `pathlib.Path`
   (`Path(base) / "data" / "input.csv"`), a pliki otwieraj wyłącznie przez menedżer kontekstu
   `with`.
6. **`requests` bez parametru `timeout`**: wywołanie może wisieć bez ograniczenia. Zawsze podawaj
   `timeout=`; przy wielu żądaniach używaj `requests.Session`.
7. **Halucynowane API bibliotek**: nieistniejące metody lub parametry pandas/NumPy oraz importy z
   niewłaściwych modułów. Jeżeli nie masz pewności co do sygnatury, sprawdź w dokumentacji lub w
   zainstalowanej wersji (`python -c "import inspect, mod; print(inspect.signature(mod.fn))"`),
   zamiast zgadywać.
8. **Formatowanie przez `%` lub `str.format` w nowym kodzie**: stosuj f-stringi. Wyjątkiem jest
   logowanie — przekazuj argumenty leniwie: `logger.info("user=%s", user_id)`, nie f-string.
9. **Efekty uboczne na poziomie modułu**: kod wykonywalny umieszczaj pod `if __name__ ==
   „__main__”:`, aby import modułu (także przez pytest) nie uruchamiał programu.
10. **`os.system` i ręczne sklejanie poleceń powłoki**: stosuj `subprocess.run([...], check=True)` z
    listą argumentów — bez `shell=True`, które otwiera drogę do wstrzyknięć poleceń.
