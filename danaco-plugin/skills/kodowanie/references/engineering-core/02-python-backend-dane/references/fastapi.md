# FastAPI w produkcji — karta

Karta obejmuje wydanie bieżące: wersje przypięte, API usunięte, wzorce produkcyjne.
Strukturę warstwową projektu i granice warstw opisuje `references/frameworki/fastapi.md`.
Stan na sierpień 2026; wersje traktuj jako orientacyjne i sprawdzaj w projekcie.

FastAPI **0.141.1**, Starlette **1.3.1**, Pydantic **2.13.4**, pydantic-settings **2.14.2**,
uvicorn **0.52.1**, gunicorn **26.0.0**, granian **2.8.0**, httpx **0.28.1**.

## Co psuje kod pisany z pamięci

Starlette 1.0 (marzec 2026) usunęło rzeczy deprecjonowane od lat. FastAPI 0.141 wymaga
`starlette>=0.46` bez górnej granicy, więc instalacja pociągnie 1.x i stary kod przestanie
się importować.

| Usunięte w Starlette 1.0 | Zamiast |
|---|---|
| `on_startup=`, `on_shutdown=` w `FastAPI(...)`/`Router` | `lifespan=` |
| `@app.on_event("startup")` / `("shutdown")` | `lifespan=` |
| `app.add_event_handler(...)` | `lifespan=` |
| `@app.route`, `@app.websocket_route`, `@app.exception_handler`, `@app.middleware` na gołym `Starlette()` | `Route(...)`, `exception_handlers={...}`, `middleware=[Middleware(...)]` |
| `Jinja2Templates(..., **env_options)` | `Jinja2Templates(env=jinja2.Environment(...))` |
| `TemplateResponse(name, context)` | `TemplateResponse(request, name, context)` |
| `FileResponse(..., method=...)` | — |

W FastAPI dekoratory `@app.get`, `@app.exception_handler` i `@app.middleware("http")`
nadal działają — to warstwa FastAPI, nie Starlette. Martwe jest wyłącznie `@app.on_event`.

## Szkielet aplikacji

`src/app/config.py` — jedyne miejsce, które czyta środowisko:

```python
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_nested_delimiter="__",   # APP_DB__HOST -> settings.db.host
        extra="ignore",
        frozen=True,
    )

    srodowisko: Literal["dev", "test", "prod"] = "dev"
    database_url: PostgresDsn
    secret_key: SecretStr                       # nie pokaże się w repr ani w logu
    jwt_ttl_minut: int = Field(default=30, ge=1, le=1440)
    cors_origins: list[str] = Field(default_factory=list)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def debug(self) -> bool:
        return self.srodowisko == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()      # type: ignore[call-arg]  # wartości z env
```

`lru_cache` jest tu konieczny: bez niego każde `Settings()` czyta `.env` z dysku, a przy
zależności per-żądanie to setki odczytów na sekundę. `SecretStr` w logu i w `model_dump()`
daje `**********`; wartość wyciągasz przez `.get_secret_value()` — jawnie, więc w review
widać, gdzie sekret opuszcza obiekt.

`src/app/main.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.errors import zarejestruj_handlery
from app.api.v1 import faktury, zdrowie
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    engine = create_async_engine(
        str(s.database_url), pool_size=10, max_overflow=5,
        pool_pre_ping=True, pool_recycle=1800,
    )
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))
    try:
        yield
    finally:
        await app.state.http.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="DANACO Rozliczenia",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if s.debug else None,        # brak Swagger UI na produkcji
        redoc_url=None,
        openapi_url="/openapi.json" if s.debug else None,
    )
    if s.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=s.cors_origins,             # nigdy ["*"] razem z credentials
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
            max_age=600,
        )
    zarejestruj_handlery(app)
    app.include_router(zdrowie.router)
    app.include_router(faktury.router, prefix="/api/v1")
    return app


app = create_app()
```

Fabryka `create_app()` zamiast globalnego `app = FastAPI(...)`: test może zbudować
aplikację z innymi ustawieniami, a sam import modułu nie tworzy puli połączeń.
`allow_origins=["*"]` razem z `allow_credentials=True` jest odrzucane przez przeglądarkę —
CORS nie zadziała wcale, a błędu będziesz szukał po stronie serwera.

Zadanie okresowe uruchomione w `lifespan` **musi** zostać anulowane, inaczej proces nie
zakończy się po SIGTERM:

```python
    zadanie = asyncio.create_task(petla_odswiezania_cache(app))
    try:
        yield
    finally:
        zadanie.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await zadanie
```

## Routery i zależności

```python
# src/app/api/v1/faktury.py
router = APIRouter(prefix="/faktury", tags=["faktury"])


@router.get("", summary="Lista faktur")
async def lista(
    sesja: Sesja,
    uzytkownik: AktualnyUzytkownik,
    strona: Annotated[int, Query(ge=1)] = 1,
    na_stronie: Annotated[int, Query(ge=1, le=200)] = 50,
    status_: Annotated[str | None, Query(alias="status")] = None,
) -> StronaFaktur:
    pozycje, razem = await repo.lista(
        sesja,
        organizacja_id=uzytkownik.organizacja_id,   # filtr dzierżawy ZAWSZE z tokenu
        status=status_,
        limit=na_stronie,
        offset=(strona - 1) * na_stronie,
    )
    return StronaFaktur(
        pozycje=[FakturaOdp.model_validate(p) for p in pozycje],
        razem=razem, strona=strona, na_stronie=na_stronie,
    )


@router.get("/{faktura_id}")
async def pobierz(faktura_id: UUID, sesja: Sesja, uzytkownik: AktualnyUzytkownik) -> FakturaOdp:
    obiekt = await repo.pobierz(sesja, faktura_id, uzytkownik.organizacja_id)
    if obiekt is None:
        raise NieznalezionoZasobu("faktura", str(faktura_id))
    return FakturaOdp.model_validate(obiekt)


@router.post("", status_code=status.HTTP_201_CREATED)
async def utworz(dane: FakturaTworz, sesja: Sesja, uzytkownik: AktualnyUzytkownik) -> FakturaOdp:
    faktura = zbuduj_fakture(dane, organizacja_id=uzytkownik.organizacja_id)
    sesja.add(faktura)
    await sesja.flush()          # nadaje id przed zbudowaniem odpowiedzi
    return FakturaOdp.model_validate(faktura)
```

Typ zwracany w adnotacji zastępuje `response_model=`; ten drugi podawaj tylko wtedy, gdy
schemat odpowiedzi ma być inny niż typ zwracany (obcięcie pól).

Identyfikator organizacji bierz **wyłącznie z tokenu**, nigdy z parametru żądania.
`organizacja_id` w URL-u pozwala każdemu zalogowanemu czytać cudze dane.

`src/app/api/deps.py` — zależności jako aliasy typów, żeby sygnatury były krótkie:

```python
async def get_sesja(request: Request) -> AsyncIterator[AsyncSession]:
    maker = request.app.state.sessionmaker
    async with maker() as sesja:
        try:
            yield sesja
            await sesja.commit()
        except Exception:
            await sesja.rollback()
            raise


Sesja = Annotated[AsyncSession, Depends(get_sesja)]
Ustawienia = Annotated[Settings, Depends(get_settings)]
AktualnyUzytkownik = Annotated[Uzytkownik, Depends(odczytaj_token)]
```

Kod po `yield` uruchamia się **po** wysłaniu odpowiedzi, więc wyjątek podniesiony tam nie
zmieni już kodu HTTP. W obrębie jednego żądania ta sama zależność liczy się raz;
wyłączenie: `Depends(f, use_cache=False)`. Uprawnienia jako zależność bez wyniku:

```python
def wymagaj_roli(*role: str) -> Callable[..., Awaitable[Uzytkownik]]:
    async def sprawdz(u: AktualnyUzytkownik) -> Uzytkownik:
        if u.rola not in role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "brak uprawnień")
        return u

    return sprawdz


@router.delete("/{id_}", status_code=204, dependencies=[Depends(wymagaj_roli("admin"))])
async def usun_twardo(id_: UUID, sesja: Sesja) -> None:
    await sesja.execute(delete(Faktura).where(Faktura.id == id_))
```

`dependencies=[...]` (a nie argument) dla zależności, których wyniku nie używasz —
uprawnienia, limity, audyt. Wynik jest odrzucany, ale wyjątek zatrzyma żądanie.

## Pydantic v2 w API

```python
NIP = Annotated[str, StringConstraints(pattern=r"^\d{10}$", strip_whitespace=True)]


class PozycjaWe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nazwa: str = Field(min_length=1, max_length=200)
    ilosc: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    cena_netto: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class FakturaTworz(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nabywca_nip: NIP
    data_wystawienia: date
    termin_platnosci: date
    pozycje: list[PozycjaWe] = Field(min_length=1, max_length=500)

    @field_validator("data_wystawienia")
    @classmethod
    def nie_z_przyszlosci(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("data wystawienia nie może być w przyszłości")
        return v

    @model_validator(mode="after")
    def termin_po_wystawieniu(self) -> Self:
        if self.termin_platnosci < self.data_wystawienia:
            raise ValueError("termin płatności przed datą wystawienia")
        return self


class FakturaOdp(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # budowanie z obiektu ORM

    id: UUID
    numer: str
    kwota_netto: Decimal
    kwota_vat: Decimal

    @computed_field
    @property
    def kwota_brutto(self) -> Decimal:
        return self.kwota_netto + self.kwota_vat
```

`extra="forbid"`: żądanie z nieznanym polem jest odrzucane zamiast po cichu ignorowane.
Bez tego literówka w nazwie pola po stronie klienta wygląda jak poprawne żądanie
z wartością domyślną.

Mapa v1 → v2, bo z pamięci wychodzi v1:

| v1 | v2 |
|---|---|
| `class Config:` | `model_config = ConfigDict(...)` |
| `.dict()`, `.json()` | `.model_dump()`, `.model_dump_json()` |
| `parse_obj()`, `parse_raw()` | `model_validate()`, `model_validate_json()` |
| `@validator` | `@field_validator` (wymaga `@classmethod`) |
| `@root_validator` | `@model_validator(mode="before"/"after")` |
| `orm_mode = True` | `from_attributes=True` |
| `Field(..., regex=)` | `Field(..., pattern=)` |
| `copy()`, `schema()` | `model_copy()`, `model_json_schema()` |
| `allow_mutation = False` | `frozen=True` |

Z Pydantic 2.13 przydatne przy API: `exclude_if` na `computed_field`,
`polymorphic_serialization=True` (bez niego odpowiedź zawierająca podklasę traci jej pola),
`ascii_only` w `StringConstraints`.

Wydajność: `.model_dump()` buduje słownik Pythona, który FastAPI dopiero serializuje.
Przy dużych listach szybciej jest zwrócić `Response(content=model.model_dump_json(),
media_type="application/json")` z `response_model=None` — kosztem walidacji wyjścia.

## Uwierzytelnianie

```python
# src/app/security.py
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt                                   # PyJWT
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import Settings, get_settings

pwd = CryptContext(schemes=["argon2"], deprecated="auto")   # pwd.hash / pwd.verify
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
ALGORYTM = "HS256"


class DaneTokenu(BaseModel):
    sub: str
    org: str
    rola: str
    exp: datetime


def wystaw_token(uzytkownik_id: str, organizacja: str, rola: str, s: Settings) -> str:
    payload: dict[str, Any] = {
        "sub": uzytkownik_id, "org": organizacja, "rola": rola,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=s.jwt_ttl_minut),
    }
    return jwt.encode(payload, s.secret_key.get_secret_value(), algorithm=ALGORYTM)


async def odczytaj_token(
    token: Annotated[str, Depends(oauth2)],
    s: Annotated[Settings, Depends(get_settings)],
) -> DaneTokenu:
    try:
        dane = jwt.decode(
            token,
            s.secret_key.get_secret_value(),
            algorithms=[ALGORYTM],           # lista jawna; nigdy z nagłówka tokenu
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token wygasł",
                            headers={"WWW-Authenticate": "Bearer"}) from None
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "nieprawidłowy token",
                            headers={"WWW-Authenticate": "Bearer"}) from None
    return DaneTokenu.model_validate(dane)


@router.post("/auth/token")
async def zaloguj(
    formularz: Annotated[OAuth2PasswordRequestForm, Depends()], sesja: Sesja, s: Ustawienia
) -> dict[str, str]:
    u = await repo.po_emailu(sesja, formularz.username)
    # ten sam komunikat dla obu przypadków — inaczej ujawniasz, które konta istnieją
    if u is None or not pwd.verify(formularz.password, u.hasz_hasla):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "nieprawidłowe dane logowania")
    return {"access_token": wystaw_token(str(u.id), str(u.organizacja_id), u.rola, s),
            "token_type": "bearer"}
```

Reguły, których złamanie to realna dziura:

- `algorithms=["HS256"]` jawnie. Przyjęcie algorytmu z nagłówka tokenu otwiera `alg: none`.
- Argon2 lub bcrypt do haseł. Nigdy SHA-256, nawet z solą.
- Token w nagłówku `Authorization`, nie w URL — URL trafia do logów proxy.
- Krótkie `exp` (15–60 min) + refresh token w bazie z możliwością unieważnienia. JWT sam
  z siebie nie da się unieważnić przed wygaśnięciem.

Klucz API zamiast JWT (integracje maszyna–maszyna):

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def sprawdz_klucz(
    klucz: Annotated[str | None, Depends(api_key_header)], sesja: Sesja
) -> Klient:
    if not klucz:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "brak nagłówka X-API-Key")
    # w bazie hasz klucza i jego jawny prefiks, nigdy pełny klucz
    kandydat = await repo.klient_po_prefiksie(sesja, klucz[:8])
    if kandydat is None or not hmac.compare_digest(hasz_klucza(klucz), kandydat.hasz):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "nieprawidłowy klucz")
    return kandydat
```

`hmac.compare_digest` zamiast `==`: porównanie stałoczasowe. Zwykłe `==` przerywa na
pierwszej różnicy i wycieka informację przez czas odpowiedzi.

## Błędy i jednolity format odpowiedzi

```python
# src/app/api/errors.py
class BladOdp(BaseModel):
    kod: str
    komunikat: str
    szczegoly: list[dict[str, Any]] | None = None
    id_zdarzenia: str


def _odp(status_code: int, kod: str, komunikat: str, szczegoly=None) -> JSONResponse:
    tresc = BladOdp(kod=kod, komunikat=komunikat, szczegoly=szczegoly,
                    id_zdarzenia=str(uuid.uuid4()))
    return JSONResponse(status_code=status_code, content=tresc.model_dump(mode="json"))


def zarejestruj_handlery(app: FastAPI) -> None:
    @app.exception_handler(NieznalezionoZasobu)
    async def _nieznaleziono(request: Request, exc: NieznalezionoZasobu) -> JSONResponse:
        return _odp(status.HTTP_404_NOT_FOUND, "nie_znaleziono", str(exc))

    @app.exception_handler(KonfliktStanu)
    async def _konflikt(request: Request, exc: KonfliktStanu) -> JSONResponse:
        return _odp(status.HTTP_409_CONFLICT, "konflikt", str(exc))

    # handler klasy bazowej po podklasach — FastAPI dobiera po MRO
    @app.exception_handler(BladDomeny)
    async def _domena(request: Request, exc: BladDomeny) -> JSONResponse:
        return _odp(status.HTTP_422_UNPROCESSABLE_ENTITY, "regula_biznesowa", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _walidacja(request: Request, exc: RequestValidationError) -> JSONResponse:
        szczegoly = [
            {"pole": ".".join(str(x) for x in e["loc"][1:]), "problem": e["msg"]}
            for e in exc.errors()
        ]
        return _odp(status.HTTP_422_UNPROCESSABLE_ENTITY, "walidacja",
                    "niepoprawne dane wejściowe", szczegoly)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _odp(exc.status_code, "http", str(exc.detail))

    @app.exception_handler(Exception)
    async def _nieoczekiwany(request: Request, exc: Exception) -> JSONResponse:
        odp = _odp(status.HTTP_500_INTERNAL_SERVER_ERROR, "wewnetrzny",
                   "wystąpił błąd wewnętrzny")
        log.exception("nieobsluzony_wyjatek", sciezka=request.url.path,
                      metoda=request.method)
        return odp
```

Handler `Exception` **nie** przepuszcza treści wyjątku do klienta — ślad stosu w odpowiedzi
HTTP to wyciek struktury systemu. `id_zdarzenia` w odpowiedzi i w logu wiąże zgłoszenie
użytkownika z wpisem w logu, nie ujawniając niczego. FastAPI zwraca błąd walidacji z kodem
**422**, nie 400; jeśli kontrakt wymaga 400, zmień to w handlerze, nie w kliencie.

## `BackgroundTasks` — i kiedy to za mało

```python
@router.post("/faktury/{id_}/wyslij", status_code=202)
async def wyslij(id_: UUID, zadania: BackgroundTasks, sesja: Sesja) -> dict[str, str]:
    faktura = await repo.pobierz(sesja, id_)
    zadania.add_task(wyslij_mail, faktura.email, faktura.numer)
    return {"status": "przyjęto"}
```

Zadanie biegnie **w tym samym procesie, po odesłaniu odpowiedzi**. Właściwe dla: jednego
maila, wpisu do logu audytowego, unieważnienia cache.

Niewłaściwe dla wszystkiego, co trwa dłużej niż kilka sekund, musi przetrwać restart procesu, wymaga
ponowienia albo ma być widoczne dla operatora — restart podczas wdrożenia gubi takie zadanie bez
śladu. Wtedy kolejka:
`references/engineering-core/02-python-backend-dane/references/async-i-zadania.md`. Funkcja
synchroniczna w `add_task` zajmuje wątek z ograniczonej puli; korutyna biegnie w pętli zdarzeń.

## Pliki i strumieniowanie

```python
MAX_BAJTOW = 20 * 1024 * 1024


@router.post("/import")
async def importuj(plik: Annotated[UploadFile, File()], sesja: Sesja) -> dict[str, int]:
    if plik.content_type not in {"text/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "oczekiwano CSV")

    wczytane = 0
    bufor = io.BytesIO()
    while porcja := await plik.read(1024 * 1024):     # porcjami, nie .read() całości
        wczytane += len(porcja)
        if wczytane > MAX_BAJTOW:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "plik za duży")
        bufor.write(porcja)

    bufor.seek(0)
    czytnik = csv.DictReader(io.TextIOWrapper(bufor, encoding="utf-8-sig"))
    return {"wstawiono": await repo.wstaw_wiele(sesja, list(czytnik))}
```

`UploadFile.read()` bez argumentu wczytuje całość do pamięci; przy 2 GB pliku proces ginie.
Limit sprawdzaj w trakcie czytania — `Content-Length` klient może skłamać; drugi limit
ustaw na proxy (`client_max_body_size` w nginx). `utf-8-sig` przy plikach z Excela, inaczej
pierwsza nazwa kolumny zawiera BOM i nie pasuje. Server-Sent Events (strumieniowy eksport
CSV wygląda tak samo — generator bajtów, `media_type="text/csv"`, `Content-Disposition`):

```python
@router.get("/zdarzenia")
async def zdarzenia(request: Request) -> StreamingResponse:
    async def strumien() -> AsyncIterator[str]:
        licznik = 0
        while True:
            if await request.is_disconnected():        # klient zamknął — przerwij
                break
            dane = await pobierz_nowe_zdarzenia()
            if dane:
                licznik += 1
                yield f"id: {licznik}\nevent: aktualizacja\ndata: {json.dumps(dane)}\n\n"
            else:
                yield ": keepalive\n\n"                # komentarz podtrzymujący połączenie
            await asyncio.sleep(2)

    return StreamingResponse(
        strumien(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

`X-Accel-Buffering: no` jest konieczne za nginxem — bez tego nginx buforuje strumień
i klient nie dostaje nic aż do zamknięcia połączenia.

## OpenAPI i wersjonowanie

Wersjonowanie przez prefiks ścieżki (`app.include_router(v2.router, prefix="/api/v2")`) —
najprostsze dla klienta i dla routingu na proxy. Nagłówek `Accept-Version` daje czystsze
URL-e kosztem cache'owania i diagnostyki; nie jest tego wart poza publicznymi API
utrzymującymi wiele wersji naraz.

Wycofywanie endpointu: `@router.get(..., deprecated=True)` (widoczne w OpenAPI) + nagłówki
`Deprecation` i `Sunset` w odpowiedzi + minimum jeden cykl wydania zapowiedzi.

Stabilne identyfikatory operacji (generatory klientów robią z nich nazwy metod):
`FastAPI(generate_unique_id_function=lambda route: f"{route.tags[0]}_{route.name}")`.

Bez `generate_unique_id_function` identyfikator zawiera metodę i ścieżkę, więc każda zmiana
ścieżki przemianowuje metody w wygenerowanym kliencie. `responses={404: {"model": BladOdp}}`
na endpoincie dokumentuje kody błędów — bez tego klient z OpenAPI zna tylko odpowiedź 200.

## Uruchomienie produkcyjne

```bash
uv run fastapi dev src/app/main.py          # deweloperskie: przeładowanie, jeden proces

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 \
  --timeout-graceful-shutdown 30 --no-server-header \
  --proxy-headers --forwarded-allow-ips='10.0.0.5' --access-log
```

Na VPS, gdy chcesz wiele rdzeni w jednym procesie nadrzędnym — gunicorn z workerem uvicorna; unit
systemd i reszta w `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`:

```bash
uv run gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 --bind 0.0.0.0:8000 --timeout 60 --graceful-timeout 30 \
  --max-requests 2000 --max-requests-jitter 200 --access-logfile - --error-logfile -
```

| Parametr | Wartość | Dlaczego |
|---|---|---|
| liczba workerów | `2 × rdzenie + 1`, ograniczona pamięcią | każdy worker ma własną pulę; `workers × pool_size` < `max_connections` Postgresa |
| `--timeout` | dłuższy niż najdłuższy endpoint | worker po przekroczeniu jest ubijany w połowie żądania |
| `--max-requests` + jitter | 1000–5000 | odnawia workera i maskuje powolne wycieki; bez jittera wszystkie restartują się naraz |
| `--proxy-headers` | za proxy | inaczej `request.client.host` to adres proxy, a `url_for` generuje `http://` |
| `--forwarded-allow-ips` | adres proxy, nie `*` | `*` pozwala podszyć się pod dowolny adres przez `X-Forwarded-For` |

W kontenerze **jeden worker**: orkiestrator ma widzieć jeden proces, żeby go skalować
i zabijać. `granian` (2.8.0) to alternatywa dla pary gunicorn+uvicorn — jedno binarium,
HTTP/2; wybieraj świadomie, bo ekosystem gunicorna jest szerszy.

## Wydajność — kolejność sprawdzania

1. `async def` z blokującym wywołaniem w środku. Najczęstsza przyczyna; reguły `ASYNC`
   w ruffie łapią część statycznie.
2. Endpoint `def` zapychający pulę wątków — FastAPI puszcza `def` w `run_in_threadpool`,
   domyślnie 40 wątków; 41. żądanie czeka.
3. N+1 w ORM (`references/engineering-core/02-python-backend-dane/references/bazy-i-orm.md`),
   serializacja dużych list (uwaga o `model_dump_json` wyżej), brak `pool_pre_ping` dający losowe
   500 na zerwanych połączeniach.

`def` vs `async def`: funkcja robiąca I/O synchronicznie (sterownik sync, `requests`,
biblioteka bez async) ma być zadeklarowana jako `def` — FastAPI odsunie ją do puli wątków.
`async def` z synchronicznym I/O w środku to najgorszy możliwy wariant.
