# Budowa serwerów MCP — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`) oraz karta
języka implementacji (`references/jezyki-programowania/python.md` lub
`references/jezyki-programowania/javascript-typescript.md` w `jezyki-programowania`). Serwer MCP to
interfejs, którego użytkownikiem jest model LLM — projektuje się go pod zdolności i ograniczenia
modelu, nie pod wygodę implementacji.

## Projektowanie narzędzi — najpierw, implementacja — potem

1. **Narzędzia według zadań, nie według punktów końcowych API.** Model potrzebuje
   narzędzia „znajdź fakturę klienta”, a nie czterech narzędzi odwzorowujących
   REST-owe zasoby, które musiałby składać. Jedno narzędzie = jedna czynność
   domknięta, o wyniku zdatnym do bezpośredniego użycia.
2. **Nazwy i opisy piszą się dla modelu.** Nazwa czasownikowa w snake_case
   (`search_invoices`, `create_case_note`); opis mówi, co narzędzie robi, kiedy
   go użyć, czego nie robi, i co zwraca. Opisy parametrów z jednostkami
   i formatami (daty ISO 8601). To dokumentacja robocza modelu — od jej jakości
   zależy trafność wywołań.
3. **Wyniki zwięzłe i strukturalne.** Zwracaj to, czego model potrzebuje do dalszej
   pracy; stronicuj listy; komunikat błędu narzędzia ma mówić modelowi, co poprawić
   („brak klienta o identyfikatorze 118; użyj search_customers”), nie zrzucać śladu stosu.
4. **Mało narzędzi dobrych zamiast wielu płytkich.** Każde narzędzie w zestawie
   zwiększa ryzyko błędnego wyboru; łącz warianty parametrem zamiast mnożyć nazwy.

## Implementacja

- **Python:** FastMCP (dekoratory `@mcp.tool`), typy parametrów przez adnotacje
  i modele Pydantic — schemat generuje się z kodu, nie pisze ręcznie. FastMCP może
  współistnieć z aplikacją FastAPI w jednym projekcie.
- **TypeScript/Node:** oficjalny MCP SDK; schematy parametrów przez zod;
  rejestracja narzędzi w jednym module, logika w osobnych.
- Transport: stdio dla serwera lokalnego uruchamianego przez klienta;
  HTTP (streamable) dla serwera zdalnego — wybór zapisz w README wraz z konfiguracją
  uruchomienia dla klienta MCP.
- Konfiguracja i sekrety przez zmienne środowiskowe, nigdy w kodzie ani w pliku
  konfiguracji klienta trzymanym w repozytorium.

## Bezpieczeństwo

- Serwer wykonuje działania w imieniu modelu — obowiązuje zasada najmniejszych
  uprawnień: konto techniczne serwera ma dostęp tylko do zasobów, których
  narzędzia rzeczywiście wymagają.
- Waliduj każdy parametr po stronie serwera (zakresy, formaty, listy dozwolonych
  wartości) — model bywa źródłem wejść błędnych jak każdy klient. Zapytania SQL
  wyłącznie parametryzowane; ścieżki plików ograniczone do katalogów dozwolonych.
- Narzędzia niszczące (usuwanie, wysyłka, płatność) projektuj tak, aby wymagały
  jawnego parametru potwierdzenia i zwracały opis skutków przed wykonaniem
  właściwym, albo wydziel je do osobnego serwera włączanego świadomie.
- Treści zwracane przez narzędzia z systemów zewnętrznych traktuj jako dane,
  nie polecenia — nie przenoś ich do opisów narzędzi.

## Testowanie i diagnostyka

- Testuj warstwowo: logika narzędzi testami jednostkowymi bez protokołu;
  cały serwer — narzędziem MCP Inspector (wywołania rzeczywiste, oględziny
  schematów) przed podłączeniem do klienta docelowego.
- Dziennik zdarzeń serwera na stderr lub do pliku — nigdy na stdout przy
  transporcie stdio, bo stdout należy do protokołu; to najczęstsza przyczyna
  „serwer się nie łączy”.
- Weryfikacja końcowa zgodnie z zasadą 6 standardów: przytocz wynik rzeczywistego
  wywołania każdego narzędzia (Inspector lub klient), nie deklarację, że działa.

## Typowe błędy modeli LLM przy budowie serwerów MCP

- Odwzorowanie 1:1 cudzego API w narzędziach zamiast projektowania pod zadania modelu.
- Opisy narzędzi pisane jak dokumentacja dla człowieka (marketing, ogólniki)
  zamiast instrukcji decyzyjnej dla modelu.
- Zwracanie surowych odpowiedzi API (całe JSON-y z polami bez znaczenia) —
  marnuje okno kontekstu modelu i pogarsza trafność dalszych kroków.
- Wypisywanie dziennika na stdout przy transporcie stdio — zerwanie protokołu.
- Schematy parametrów pisane ręcznie i rozjeżdżające się z kodem — generuj z typów.
- Mieszanie wersji SDK i wzorców z różnych okresów protokołu — sprawdź wersję
  zainstalowanego pakietu i jego dokumentację, nie pamięć.

## Karty referencyjne

Wczytaj kartę właściwą dla bieżącego etapu pracy; przy budowie serwera od zera
przejdź karty w kolejności poniżej.

| Karta | Zakres | Kiedy wczytać |
|---|---|---|
| `references/budowa-serwerow-mcp/projektowanie-narzedzi-pro.md` | Budżet kontekstu jako kryterium projektowe, projektowanie odpowiedzi i stronicowania kursorem, przestrzeń nazw i siatka czasowników, opisy narzędzi jako instrukcje decyzyjne, projektowanie parametrów (enumy, dry_run, ISO 8601), komunikaty błędów uczące model, ewaluacja zestawu z transkryptami, antywzorce zestawów | Przed zaprojektowaniem lub przebudową zestawu narzędzi; przy przeglądzie zestawu, którego model źle używa |
| `references/budowa-serwerow-mcp/implementacja-pro.md` | Struktura projektu i rejestracja modułami w Python/FastMCP oraz TypeScript/MCP SDK, modele Pydantic/zod, lifespan i zasoby dzielone, wyjątki domenowe, adnotacje narzędzi, transport stdio i streamable HTTP z uwierzytelnianiem, zasoby i szablony promptów, konfiguracja klientów (w tym ścieżki Windows), wydajność i współbieżność | Przed napisaniem kodu serwera; przy wyborze transportu; przy konfigurowaniu klienta MCP |
| `references/budowa-serwerow-mcp/testy-i-eksploatacja.md` | Piramida testów (jednostkowe bez protokołu, klient w pamięci, MCP Inspector CLI), testy bezpieczeństwa parametrów i ścieżek, ocena zachowania modelu z transkryptami, protokół diagnozy awarii połączenia z sygnaturami przyczyn, wersjonowanie i wygaszanie narzędzi, dziennik strukturalny, limity i aktualizacje | Przed napisaniem testów; przy objawie „serwer się nie łączy”; przy wydaniu i utrzymaniu serwera |
