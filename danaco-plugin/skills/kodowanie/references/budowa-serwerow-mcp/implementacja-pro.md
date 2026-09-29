# Implementacja serwera MCP — karta

Karta podaje wzorce implementacyjne klasy produkcyjnej dla obu ekosystemów oraz
szczegóły transportu i konfiguracji klientów. Interfejsy SDK ewoluują — wzorce
poniżej są stabilne co do zasady, ale sygnatury i nazwy metod weryfikuj zawsze
w dokumentacji wersji pakietu zainstalowanej w projekcie, nie z pamięci.

## 1. Python / FastMCP

### Struktura projektu serwera

Nie trzymaj całego serwera w jednym pliku. Układ sprawdzony:

```
serwer-mcp-crm/
├── pyproject.toml          # zależności przypięte, entry point serwera
├── README.md               # konfiguracja klienta, zmienne środowiskowe
├── src/crm_mcp/
│   ├── __init__.py
│   ├── server.py           # instancja FastMCP, lifespan, składanie modułów
│   ├── config.py           # wczytanie i walidacja zmiennych środowiskowych
│   ├── models.py           # modele Pydantic wejścia/wyjścia narzędzi
│   ├── errors.py           # wyjątki domenowe i mapowanie na komunikaty
│   ├── tools/
│   │   ├── customers.py    # narzędzia domeny klientów
│   │   ├── invoices.py     # narzędzia domeny faktur
│   │   └── notes.py
│   └── services/           # logika dostępu do danych, bez zależności od MCP
│       ├── db.py
│       └── crm_client.py
└── tests/
```

Reguła rozdziału: moduły w `tools/` są cienkie — walidują, wołają `services/`,
formatują wynik dla modelu. Logika domenowa żyje w `services/` i daje się
testować bez protokołu MCP.

### Rejestracja narzędzi modułami

Dekorator `@mcp.tool` wymaga instancji serwera, więc przy podziale na moduły
zastosuj wzorzec funkcji rejestrującej:

```python
# tools/customers.py
def register(mcp, services):
    @mcp.tool()
    def search_customers(query: str, limit: int = 20) -> CustomerSearchResult:
        """Wyszukuje klientów po nazwie, NIP lub e-mailu. ..."""
        return services.customers.search(query, limit=min(limit, 50))
```

a w `server.py` złóż całość: `customers.register(mcp, services)` dla każdego
modułu. Alternatywnie użyj mechanizmu składania serwerów, jeśli wersja FastMCP
go udostępnia (sprawdź w bieżącej dokumentacji) — zasada pozostaje ta sama:
jeden moduł na domenę, rejestracja w jednym miejscu.

### Modele Pydantic wejścia i wyjścia

- **Wejście:** typuj parametry adnotacjami; dla struktur złożonych przyjmuj
  model Pydantic — schemat JSON generuje się z typów i nigdy nie rozjeżdża
  z kodem. Ograniczenia zapisuj w typach (`Field(ge=1, le=50)`, `Literal[...]`
  dla enumów), opisy parametrów w `Field(description=...)`.
- **Wyjście:** zdefiniuj model wyniku i zwracaj jego instancję — to jest warstwa przycinania
  odpowiedzi do pól niezbędnych (karta
  `references/budowa-serwerow-mcp/projektowanie-narzedzi-pro.md`). Model wyjścia dokumentuje
  kontrakt narzędzia równie mocno jak model wejścia.
- Nie pisz schematów JSON ręcznie. Jedynym źródłem prawdy są typy.

### Kontekst i lifespan — zasoby dzielone

Zasoby kosztowne (pula połączeń do bazy, klient HTTP z keep-alive, sesja
uwierzytelniona do API) otwieraj **raz**, w funkcji lifespan serwera, nie przy
każdym wywołaniu narzędzia:

```python
@asynccontextmanager
async def lifespan(server):
    pool = await create_pool(config.database_url)   # otwarcie raz
    http = httpx.AsyncClient(timeout=15.0)
    try:
        yield AppContext(pool=pool, http=http)      # wstrzykiwane do narzędzi
    finally:
        await http.aclose()
        await pool.close()                          # zamknięcie czyste

mcp = FastMCP("crm", lifespan=lifespan)
```

W narzędziu odbieraj kontekst przez parametr `Context` (FastMCP wstrzykuje go
automatycznie po adnotacji typu) i sięgaj do zasobów z kontekstu lifespan.
Antywzorzec: `connect()` w ciele narzędzia — pod obciążeniem wyczerpie pulę
połączeń bazy i ukryje koszt w czasie odpowiedzi każdego wywołania. Drugi
antywzorzec: zasoby w zmiennych globalnych modułu bez zamykania — brak
zamknięcia czystego przy zakończeniu procesu.

### Obsługa błędów — wyjątki domenowe mapowane na komunikaty

Zdefiniuj wąską hierarchię wyjątków domenowych (`NotFoundError`,
`ValidationError`, `PermissionError`, `UpstreamError`) rzucanych przez
`services/`. Na granicy narzędzia mapuj je na komunikaty uczące model
(reguła stan → przyczyna → następny krok); wyjątki nieprzewidziane loguj
z pełnym śladem na stderr, a modelowi zwracaj zdanie ogólne bez szczegółów
wewnętrznych. Nigdy nie przepuszczaj do modelu surowego wyjątku sterownika
bazy ani odpowiedzi 500 usługi zewnętrznej.

### Adnotacje narzędzi

Protokół przewiduje adnotacje-podpowiedzi opisujące charakter narzędzia,
m.in. `readOnlyHint` (narzędzie nie zmienia stanu) i `destructiveHint`
(narzędzie może nieodwracalnie zmienić lub usunąć dane). Ustawiaj je zgodnie
z prawdą przy każdym narzędziu — klienty używają ich do potwierdzeń
i automatycznej akceptacji wywołań tylko-do-odczytu. Adnotacje są wskazówką,
nie zabezpieczeniem: kontrola uprawnień pozostaje po stronie serwera.
Składnię przekazywania adnotacji sprawdź w dokumentacji używanej wersji SDK.

## 2. TypeScript / MCP SDK

### Struktura i rejestracja

Układ analogiczny do pythonowego: `src/server.ts` (instancja serwera,
składanie), `src/tools/*.ts` (moduły domen eksportujące funkcję rejestrującą),
`src/services/` (logika bez zależności od MCP), `src/schemas.ts` lub schematy
przy narzędziach. Rejestracja narzędzia w oficjalnym SDK przyjmuje nazwę,
metadane z opisem i schematem wejścia oraz funkcję obsługi; dokładną sygnaturę
(`registerTool` / starsze warianty) sprawdź w dokumentacji zainstalowanej
wersji `@modelcontextprotocol/sdk`.

### zod jako źródło schematów

Schematy wejścia definiuj w zod i przekazuj SDK — schemat JSON generuje się
z kodu:

```ts
const searchInvoicesInput = {
  query: z.string().describe("Fraza: numer faktury, kontrahent lub NIP"),
  status: z.enum(["draft", "sent", "paid", "overdue"]).optional()
    .describe("Filtr statusu płatności"),
  limit: z.number().int().min(1).max(50).default(20),
};
```

`.describe()` na każdym polu — to są opisy parametrów widziane przez model.
Ten sam obiekt zod służy do walidacji w czasie wykonania i jako typ statyczny
(`z.infer`) — jedno źródło prawdy, zero rozjazdu schematu z kodem.

### Obsługa sygnałów i zamykanie czyste

Proces serwera stdio jest dzieckiem procesu klienta i musi umieć umrzeć czysto:

```ts
async function shutdown(signal: string) {
  console.error(`[crm-mcp] zamykanie po ${signal}`);
  await pool.end();          // zamknięcie zasobów w kolejności odwrotnej
  process.exit(0);
}
process.on("SIGINT", () => void shutdown("SIGINT"));
process.on("SIGTERM", () => void shutdown("SIGTERM"));
```

Dodatkowo obsłuż zamknięcie transportu (klient kończy sesję) tym samym torem.
Nieobsłużone odrzucenia promise loguj na stderr i kończ proces kodem
niezerowym — serwer w stanie nieokreślonym jest gorszy niż serwer martwy,
bo klient nie wie, że ma go zrestartować.

## 3. Transport — szczegółowo

### stdio

- **Cykl życia:** klient uruchamia proces serwera jako podproces, pisze żądania
  na jego stdin, czyta odpowiedzi ze stdout; zakończenie klienta kończy serwer.
  Jeden proces = jedna sesja jednego klienta.
- **stdout należy wyłącznie do protokołu.** Każdy bajt spoza ramek protokołu
  psuje parser klienta. Dziennik obowiązkowo na stderr (`console.error`,
  `logging` z handlerem na stderr); w Pythonie upewnij się, że żadna zależność
  nie ma skonfigurowanego `print`/handlera na stdout. To najczęstsza przyczyna
  „serwer się nie łączy”.
- **Buforowanie:** stdout w trybie potokowym bywa buforowany blokowo — upewnij
  się, że warstwa transportu SDK wypycha ramki natychmiast (SDK robią to same;
  problem powstaje, gdy kod obchodzi SDK i pisze na stdout bezpośrednio — nie
  rób tego nigdy).

### Streamable HTTP

- Serwer zdalny, wielu klientów równolegle; żądania POST na jeden punkt
  końcowy MCP, odpowiedzi zwykłe lub strumieniowane (SSE). Protokół przewiduje
  identyfikator sesji nadawany przy inicjalizacji i przekazywany w nagłówku
  kolejnych żądań oraz mechanizm wznawiania strumienia po zerwaniu —
  obsługę zapewnia SDK; nazwy nagłówków i szczegóły wznawiania sprawdź
  w bieżącej specyfikacji MCP, bo ta warstwa ewoluuje.
- **Uwierzytelnianie:** serwer HTTP wystawiony poza localhost wymaga
  uwierzytelnienia zawsze. Minimum: statyczny token okaziciela w nagłówku
  `Authorization`, sprawdzany na każdym żądaniu, przechowywany w zmiennej
  środowiskowej. Docelowo: OAuth zgodnie z bieżącą specyfikacją autoryzacji
  MCP (serwer jako resource server; nie implementuj przepływów OAuth ręcznie —
  użyj wsparcia SDK lub bramy API). TLS obowiązkowy poza siecią lokalną.
- **Kiedy który transport:** stdio — serwer lokalny na maszynie użytkownika,
  dostęp do plików/procesów lokalnych, dystrybucja „użytkownik instaluje
  pakiet”; streamable HTTP — serwer współdzielony przy danych centralnych,
  sekretach, których nie wolno rozdawać na stacje robocze, lub integracji
  utrzymywanej centralnie. W razie wątpliwości zacznij od stdio — mniejsza
  powierzchnia operacyjna; logikę trzymaj niezależnie od transportu, żeby
  zmiana była tania.

## 4. Zasoby (resources) i szablony promptów (prompts)

- **Narzędzie** — model decyduje o wywołaniu i przekazuje parametry; jedyny
  mechanizm wykonywania działań.
- **Zasób (resource)** — treść identyfikowana URI, udostępniana klientowi do
  wyboru jako kontekst (dokumenty, konfiguracje, słowniki). Użyj zamiast
  narzędzia, gdy treść jest względnie statyczna i ma trafić do kontekstu
  w całości, a nie być odpytywana parametrami. Szablony URI
  (np. `invoice://{id}`) pokrywają rodziny zasobów.
- **Szablon promptu (prompt)** — parametryzowany wzorzec rozmowy wybierany
  jawnie przez użytkownika w kliencie (np. „przegląd zaległości klienta X”).
  Użyj do utrwalenia powtarzalnych przebiegów pracy; nie zastępuje opisów
  narzędzi.

Zakres wsparcia zasobów i promptów różni się między klientami — sprawdź
w dokumentacji klienta docelowego, zanim oprzesz na nich funkcję krytyczną;
narzędzia są wspierane powszechnie.

## 5. Konfiguracja klientów

Wpis konfiguracyjny serwera stdio (Claude Desktop: `claude_desktop_config.json`;
Claude Code: `claude mcp add` lub `.mcp.json` w projekcie — format zbliżony):

```json
{
  "mcpServers": {
    "crm": {
      "command": "/absolutna/sciezka/do/.venv/bin/python",
      "args": ["-m", "crm_mcp.server"],
      "env": { "CRM_DATABASE_URL": "postgresql://...", "CRM_API_TOKEN": "..." }
    }
  }
}
```

Zasady i typowe błędy:

- **Ścieżki absolutne do interpretera i skryptu.** Klient uruchamia proces
  z własnym katalogiem roboczym i okrojonym środowiskiem — `python` z PATH
  bywa innym Pythonem niż venv projektu, a ścieżka względna nie istnieje.
- **`env` podaje wszystko, czego serwer wymaga.** Środowisko procesu klienta
  nie dziedziczy powłoki użytkownika; brak zmiennej w `env` to brak zmiennej
  w serwerze.
- **Windows:** w JSON odwrotne ukośniki podwajaj (`"C:\\projekty\\srv\\..."`)
  albo stosuj zwykłe `/`; polecenia npm wskazuj przez `cmd /c npx ...` lub
  pełną ścieżkę do `npx.cmd` — `npx` bez rozszerzenia nie jest plikiem
  wykonywalnym dla `CreateProcess`. Uważaj na spacje w ścieżkach profilu.
- Po każdej zmianie konfiguracji zrestartuj klienta w pełni — konfiguracja
  czytana jest przy starcie.
- Pliku konfiguracji klienta z sekretami nie commituj; w repozytorium trzymaj
  szablon z nazwami zmiennych bez wartości.

## 6. Wydajność

- **Operacje długie:** przy transporcie wspierającym powiadomienia zgłaszaj
  postęp przez mechanizm kontekstu (w FastMCP metody raportowania postępu
  i logowania na obiekcie `Context`) — klient widzi, że serwer żyje. Operacji
  wielominutowych nie projektuj jako jednego wywołania: rozdziel na
  `start_...` zwracające identyfikator zadania i `get_..._status`.
- **Limity czasu po stronie serwera:** każde wywołanie usługi zewnętrznej
  z twardym limitem (kilka–kilkanaście sekund) i komunikatem błędu mówiącym
  modelowi, czy ponowienie ma sens. Nie pozwól, by jedno zawieszone API
  wisiało do limitu klienta.
- **Współbieżne wywołania narzędzi:** klient może wywołać kilka narzędzi
  równolegle. Narzędzia asynchroniczne nie mogą blokować pętli zdarzeń —
  operacje blokujące (ciężkie obliczenia, synchroniczne sterowniki) wynoś do
  puli wątków (`anyio.to_thread.run_sync` / worker threads). Zasoby dzielone
  z lifespan muszą być bezpieczne współbieżnie: pule połączeń zamiast jednego
  połączenia współdzielonego, bez mutowalnego stanu globalnego między
  wywołaniami.
- Cache'uj odpowiedzi słownikowe (listy statusów, konfiguracje) z krótkim TTL
  zamiast odpytywać źródło przy każdym wywołaniu.
