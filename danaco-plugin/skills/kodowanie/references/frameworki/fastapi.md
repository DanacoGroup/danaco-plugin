# FastAPI — karta

Karta obejmuje strukturę warstwową projektu FastAPI i granice między warstwami,
niezależnie od wydania biblioteki. Wersje przypięte, API usunięte w bieżących wydaniach
Starlette i Pydantica oraz wzorce produkcyjne niesie
`references/engineering-core/02-python-backend-dane/references/fastapi.md` — przy pracy
nad kodem wczytaj obie.

Przeczytaj tę kartę w całości przed rozpoczęciem pracy z kodem FastAPI. Stosuj poniższe zasady
bezwzględnie, o ile zastany kod projektu nie narzuca świadomie innej konwencji.

## Struktura projektu

Przyjmij układ warstwowy z routerami dzielonymi według domeny, nie według typu HTTP:

```
app/
├── main.py            # utworzenie instancji FastAPI, rejestracja routerów, lifespan
├── config.py          # ustawienia (pydantic-settings), jedno źródło prawdy
├── routers/           # warstwa tras: walidacja wejścia, kody statusu, zależności
│   └── orders.py
├── services/          # logika biznesowa, bez importów z FastAPI
│   └── order_service.py
├── repositories/      # dostęp do danych (SQLAlchemy/SQL), bez logiki biznesowej
│   └── order_repository.py
├── schemas/           # modele Pydantic wejścia/wyjścia
│   └── order.py
└── models/            # modele ORM
    └── order.py
```

Przestrzegaj granic warstw: trasa przyjmuje i zwraca modele Pydantic oraz deleguje do serwisu;
serwis nie zna obiektów `Request` ani `Response`; repozytorium nie zwraca modeli Pydantic, lecz
obiekty ORM lub proste struktury. Nie umieszczaj zapytań SQL w funkcjach tras. Nie twórz katalogów
„utils”, „helpers” ani „common” jako składowiska kodu bez przypisanej odpowiedzialności. Nie twórz
nowej struktury, gdy projekt już istnieje — dostosuj się do zastanej.

## Konwencje frameworka

- Definiuj kontrakty wejścia i wyjścia wyłącznie modelami Pydantic. Deklaruj `response_model` (lub
  adnotację zwracanego typu) w każdej trasie; nie zwracaj surowych obiektów ORM ani słowników bez
  schematu.
- Rozdzielaj schematy wejściowe i wyjściowe (`OrderCreate`, `OrderRead`); nie używaj jednego modelu
  do obu celów, ponieważ pola takie jak `id` czy `created_at` różnią kontrakty.
- Wstrzykuj zależności przez `Depends` z adnotacją `Annotated`: sesję bazy danych, bieżącego
  użytkownika, ustawienia. Nie twórz zasobów (sesji, klientów HTTP) wewnątrz ciała funkcji trasy.
- Zasoby o cyklu życia aplikacji (pula połączeń, klient `httpx.AsyncClient`) inicjalizuj w
  menedżerze kontekstu przekazanym jako `lifespan`; nie używaj przestarzałych zdarzeń `on_event`.
- Błędy domenowe sygnalizuj wyjątkiem `HTTPException` w warstwie tras lub własnym wyjątkiem
  domenowym mapowanym przez `app.add_exception_handler`. Serwisy nie rzucają `HTTPException`.
- Ustawiaj jawnie kody statusu: `status_code=status.HTTP_201_CREATED` dla tworzenia zasobów, `204`
  bez treści dla usuwania.
- Stosuj składnię Pydantic v2 konsekwentnie: `model_config = ConfigDict(...)`, `field_validator`,
  `model_validator`, `model_dump()`. Jeżeli projekt używa Pydantic v1, stosuj wyłącznie idiomy v1 —
  nigdy nie mieszaj obu.
- Parametry zapytania i ścieżki ograniczaj adnotacjami (`Annotated[int, Path(gt=0)]`,
  `Annotated[str, Query(max_length=100)]`); walidacja należy do warstwy deklaracji, nie do ciała
  funkcji.

Wzorzec trasy zgodny ze standardem Danaco:

```python
# routers/orders.py — trasa deleguje do serwisu, zależności przez Annotated
router = APIRouter(prefix="/orders", tags=["orders"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: DbSession,
    user: CurrentUser,
) -> OrderRead:
    # logika w serwisie; trasa tylko tłumaczy kontrakt HTTP
    order = await order_service.create_order(db, user, payload)
    return OrderRead.model_validate(order)
```

## Konfiguracja i sekrety

- Trzymaj konfigurację w jednej klasie ustawień opartej na `pydantic-settings` (`BaseSettings`),
  czytającej zmienne środowiskowe oraz plik `.env` w środowisku lokalnym.
- Udostępniaj ustawienia przez zależność (`Depends(get_settings)`) z pamięcią podręczną, nie przez
  import globalnej instancji rozsiany po warstwach niższych.
- Nie commituj: `.env`, kluczy API, haseł do bazy, certyfikatów. Commituj `.env.example` z nazwami
  zmiennych i wartościami zastępczymi.
- Nie wpisuj sekretów w kod źródłowy ani w wartości domyślne pól ustawień. Brak wymaganego sekretu
  ma powodować błąd startu aplikacji, nie ciche użycie wartości domyślnej.
- Adres bazy danych, tryb debugowania i pochodzenia CORS traktuj jako konfigurację środowiskową; nie
  utrwalaj w kodzie adresów konkretnych środowisk.

## Testy

- Używaj `pytest` z `TestClient` (`fastapi.testclient`) do testów synchronicznych lub
  `httpx.AsyncClient` z `ASGITransport` do testów asynchronicznych; w drugim przypadku skonfiguruj
  `pytest-asyncio` lub `anyio`.
- Testuj przez interfejs HTTP: buduj żądanie, sprawdzaj kod statusu i treść odpowiedzi. Logikę
  serwisów testuj dodatkowo jednostkowo, bez klienta HTTP.
- Podmieniaj zależności przez `app.dependency_overrides` (np. testowa sesja bazy, sztuczny
  użytkownik); po teście przywracaj stan, najlepiej w fixturze.
- Dla bazy danych używaj bazy testowej lub transakcji wycofywanej po każdym teście; nie testuj na
  bazie deweloperskiej.
- Sprawdzaj również ścieżki błędów: 404 dla brakującego zasobu, 422 dla niepoprawnego wejścia,
  401/403 dla braku uprawnień. Test wyłącznie ścieżki pozytywnej jest niekompletny.
- Nie mockuj warstw wewnętrznych aplikacji w testach integracyjnych; mockuj wyłącznie granice
  systemu (usługi zewnętrzne, czas, losowość).

Wzorzec testu asynchronicznego:

```python
# test_orders.py — test przez interfejs HTTP z podmienioną zależnością
@pytest.fixture
def client(test_db_session):
    app.dependency_overrides[get_db_session] = lambda: test_db_session
    yield app
    app.dependency_overrides.clear()

async def test_create_order_returns_201(client):
    transport = ASGITransport(app=client)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        response = await http.post("/orders", json={"product_id": 1, "quantity": 2})
    assert response.status_code == 201
    assert response.json()["quantity"] == 2
```

## Diagnostyka

- Odpowiedź 422 zawiera listę `detail` z polami `loc`, `msg`, `type`. Czytaj `loc` od początku:
  pierwszy element wskazuje źródło (`body`, `query`, `path`), kolejne — ścieżkę pola. Porównaj ją ze
  schematem Pydantic zamiast zgadywać.
- Dziennik uvicorn czytaj od pierwszego wpisu wyjątku, nie od ostatniej linii; pełny ślad stosu
  znajduje się przy pierwotnym błędzie. Odpowiedź 500 bez szczegółów w treści jest zamierzona —
  szczegóły są wyłącznie w dzienniku serwera.
- Gdy aplikacja nie startuje, sprawdź kolejno: błędy importu, walidację ustawień
  (`pydantic-settings` zgłasza brakujące zmienne), konflikty definicji tras.
- Gdy odpowiedzi są wolne, podejrzewaj blokujące IO w trasie `async def` — zweryfikuj, czy wywołania
  bazodanowe i sieciowe są rzeczywiście asynchroniczne.
- Do inspekcji kontraktu używaj `/docs` (Swagger UI) oraz `/openapi.json`; rozbieżność między
  dokumentacją a oczekiwaniem oznacza błąd w schematach lub adnotacjach, nie w kliencie.

## Typowe błędy modeli LLM w tym frameworku

1. **Blokujące IO w `async def`.** Wywołanie synchronicznego sterownika bazy, `requests` lub
   `time.sleep` w trasie `async def` blokuje całą pętlę zdarzeń i zatrzymuje wszystkie żądania.
   Reguła: `async def` wyłącznie z bibliotekami asynchronicznymi (`httpx.AsyncClient`,
   asynchroniczna sesja SQLAlchemy, `asyncio.sleep`); dla kodu synchronicznego użyj `def` — FastAPI
   wykona go w puli wątków.
2. **Mieszanie składni Pydantic v1 i v2.** Łączenie `class Config` z `model_config`, `@validator` z
   `@field_validator`, `.dict()` z `.model_dump()` w jednym projekcie. Ustal wersję na podstawie
   zależności projektu i stosuj wyłącznie jej idiomy.
3. **Zwracanie obiektów ORM bez `response_model`.** Wycieka pola wewnętrzne (np. hash hasła) i
   uzależnia kontrakt API od schematu bazy. Zawsze deklaruj model wyjściowy z
   `ConfigDict(from_attributes=True)` przy mapowaniu z ORM.
4. **Mutowalne wartości domyślne i zasoby w sygnaturze.** Konstruowanie sesji bazy lub klienta HTTP
   w ciele trasy zamiast przez `Depends` uniemożliwia podmianę w testach i zarządzanie cyklem życia.
   Wszystkie zasoby wstrzykuj.
5. **`HTTPException` rzucany z warstwy serwisów lub repozytoriów.** Wiąże logikę biznesową z HTTP.
   Serwis rzuca wyjątek domenowy; mapowanie na kod statusu należy do warstwy tras lub globalnego
   handlera.
6. **Halucynowane parametry dekoratorów i nieistniejące moduły.** Przykłady: wymyślone argumenty
   `@app.get`, importy w rodzaju `from fastapi import BaseModel` (poprawnie: `from pydantic import
   BaseModel`). W razie niepewności co do API zweryfikuj import i sygnaturę zamiast zgadywać.
7. **Jeden model Pydantic do wejścia, wyjścia i bazy.** Prowadzi do przyjmowania pól, których klient
   nie powinien ustawiać (`id`, `is_admin`) — luka typu mass assignment. Rozdzielaj schematy
   `Create`, `Update`, `Read`.
8. **Ignorowanie kodów statusu.** Zwracanie 200 dla utworzenia zasobu, treści przy 204 lub 500
   zamiast 409 przy konflikcie. Dobieraj kody świadomie i deklaruj je w dekoratorze trasy.
9. **CORS ustawiony na `allow_origins=["*"]` wraz z `allow_credentials=True`.** Kombinacja
   niepoprawna i niebezpieczna; specyfikacja CORS jej zabrania. Wymieniaj pochodzenia jawnie z
   konfiguracji środowiskowej.
10. **Testy omijające aplikację.** Testowanie funkcji trasy wywołaniem bezpośrednim zamiast przez
    klienta HTTP pomija walidację, zależności i serializację — czyli większość tego, co może się
    zepsuć. Testuj przez `TestClient` lub `httpx.AsyncClient`.
