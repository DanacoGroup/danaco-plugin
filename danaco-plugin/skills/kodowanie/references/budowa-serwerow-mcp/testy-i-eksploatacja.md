# Testowanie i eksploatacja serwera MCP — karta

Karta obejmuje pełny cykl: od testów jednostkowych logiki narzędzi, przez testy
protokołu i kontraktu, testy bezpieczeństwa i ocenę zachowania modelu, po
diagnostykę awarii połączenia, wersjonowanie i eksploatację produkcyjną.
Obowiązuje zasada weryfikacji ze standardów zawodowych: dowodem działania jest
wynik rzeczywistego wywołania, nie deklaracja.

## 1. Piramida testów serwera MCP

Testuj na trzech poziomach, od najtańszego do najdroższego. Większość testów ma
żyć na dole piramidy.

### Poziom 1 — logika narzędzi jednostkowo, bez protokołu

Warstwa `services/` (logika domenowa) testuje się zwykłymi testami
jednostkowymi bez żadnej zależności od MCP — to nagroda za rozdział warstw
z karty implementacji. Testuj tu: reguły biznesowe, mapowanie rekordów
źródłowych na modele wyjścia (czy pola zbędne odpadają, czy identyfikatory są
obecne), przycinanie do limitów, budowę i rozbiór kursorów stronicowania,
mapowanie wyjątków domenowych na komunikaty dla modelu. Zależności zewnętrzne
(baza, API) zastępuj dublami; dla bazy preferuj lekką bazę rzeczywistą
(SQLite/kontener PostgreSQL) nad atrapą sterownika.

### Poziom 2 — warstwa protokołu przez klienta testowego w pamięci

FastMCP udostępnia klienta testowego łączonego z serwerem w pamięci
(bez procesu i bez transportu) — wzorzec w pytest:

```python
import pytest
from fastmcp import Client

@pytest.mark.asyncio
async def test_search_invoices_zwraca_kursor():
    async with Client(mcp) as client:          # mcp = instancja serwera
        result = await client.call_tool(
            "search_invoices", {"query": "Nowak", "limit": 5}
        )
        # asercje na strukturze odpowiedzi widzianej przez model
```

Składnię klienta sprawdź w dokumentacji zainstalowanej wersji FastMCP.
W TypeScript analogicznie: para transportów w pamięci
(`InMemoryTransport.createLinkedPair()` w oficjalnym SDK) łączy instancję
klienta z instancją serwera w jednym procesie testowym.

Co testować na tym poziomie: (a) rejestrację — lista narzędzi zawiera
dokładnie narzędzia zamierzone, z opisami niepustymi; (b) schematy — wejście
niezgodne (zła wartość enum, limit poza zakresem, brak pola wymaganego) jest
odrzucane z czytelnym błędem; (c) kształt odpowiedzi — pola kontraktu obecne,
pola zakazane nieobecne; (d) ścieżki błędów — brak rekordu zwraca komunikat
uczący model, nie ślad stosu.

### Poziom 3 — kontrakt end-to-end przez MCP Inspector

MCP Inspector uruchamia serwer naprawdę (proces, transport, inicjalizacja
protokołu) i pozwala wywoływać narzędzia. Tryb interaktywny do oględzin:

```bash
npx @modelcontextprotocol/inspector /sciezka/.venv/bin/python -m crm_mcp.server
```

Tryb CLI do sprawdzeń powtarzalnych (składnię flag sprawdź w bieżącej
dokumentacji Inspectora):

```bash
npx @modelcontextprotocol/inspector --cli \
  /sciezka/.venv/bin/python -m crm_mcp.server --method tools/list
npx @modelcontextprotocol/inspector --cli \
  /sciezka/.venv/bin/python -m crm_mcp.server \
  --method tools/call --tool-name search_invoices \
  --tool-arg query=Nowak --tool-arg limit=5
```

Ten poziom wykrywa to, czego klient w pamięci nie widzi: zanieczyszczony
stdout, złe ścieżki, brakujące zmienne środowiskowe, błędy startu procesu.
Przebieg minimalny przed każdym wydaniem: `tools/list` + jedno wywołanie
każdego narzędzia z parametrami rzeczywistymi; wyniki przytocz w weryfikacji
końcowej zadania.

## 2. Testy bezpieczeństwa narzędzi

Traktuj każdy parametr narzędzia jak wejście z internetu — model przekazuje
także treści pochodzące od użytkownika i z dokumentów zewnętrznych.

- **Wstrzyknięcia w parametry.** Do parametrów tekstowych podawaj ładunki
  SQL (`'; DROP TABLE --`, `" OR 1=1`), fragmenty poleceń powłoki
  (`; rm -rf /`, backticki), znaczniki HTML/skrypty. Oczekiwanie: wartość
  potraktowana jako dane (zapytania parametryzowane, argumenty procesów
  przekazywane listą, nigdy przez sklejanie łańcucha polecenia).
- **Ścieżki poza katalogiem dozwolonym.** Dla narzędzi plikowych testuj
  `../../etc/passwd`, ścieżki absolutne, dowiązania symboliczne wskazujące
  poza katalog, na Windows warianty `..\\` i litery dysków. Oczekiwanie:
  serwer normalizuje ścieżkę (realpath) i sprawdza, czy wynik leży w katalogu
  dozwolonym — test na przedrostku łańcucha nie wystarcza.
- **Wartości brzegowe schematów.** `limit=0`, `limit=-1`, `limit=10**9`,
  łańcuch pusty, łańcuch o długości setek kilobajtów, data `9999-12-31`,
  wartość spoza enum, typ zły (łańcuch zamiast liczby). Oczekiwanie: odmowa
  z komunikatem, nie wyjątek nieobsłużony ani zapis danych bezsensownych.
- **Operacje niszczące.** Sprawdź, że `delete_`/`update_` z `dry_run=true`
  niczego nie zapisuje (asercja na stanie bazy po teście) i że narzędzia
  oznaczone `readOnlyHint` rzeczywiście nie mają ścieżki kodu zmieniającej stan.
- Testy te zapisz jako stałą część zestawu testów poziomu 2 — regresja
  bezpieczeństwa ma oblewać budowę, nie czekać na audyt.

## 3. Testowanie zachowania modelu z zestawem

Testy protokołu dowodzą, że serwer działa; nie dowodzą, że model go dobrze
używa. Ocenę zachowania prowadź w kliencie rzeczywistym (Claude Desktop /
Claude Code) według metodyki z karty `references/budowa-serwerow-mcp/projektowanie-narzedzi-pro.md`
(sekcja „Ewaluacja zestawu narzędzi”):

1. Podłącz serwer do klienta w konfiguracji identycznej z docelową.
2. Wykonaj scenariusze zadań użytkownika — pozytywne i negatywne — z listy
   ewaluacyjnej projektu.
3. **Transkrypty są artefaktem oceny.** Dla każdego scenariusza zachowaj zapis:
   polecenie użytkownika, sekwencja wywołań (narzędzie, parametry, skrót
   odpowiedzi), wynik końcowy, werdykt zgodności z przebiegiem wzorcowym.
   Przechowuj transkrypty w repozytorium projektu obok listy scenariuszy —
   porównanie transkryptów między wersjami zestawu jest podstawą decyzji
   o zmianach opisów narzędzi.
4. Wnioski wprowadzaj do opisów i schematów, po czym powtórz przebieg —
   pojedyncza iteracja prawie nigdy nie wystarcza.

## 4. Diagnostyka awarii połączenia — protokół krok po kroku

Objaw „klient nie widzi serwera / serwer się nie łączy” diagnozuj w stałej
kolejności; nie zgaduj i nie zmieniaj konfiguracji na oślep.

**Krok 1 — czy proces startuje samodzielnie?** Uruchom w terminalu dokładnie
to polecenie, które ma w konfiguracji klient (ta sama ścieżka interpretera,
te same argumenty, te same zmienne środowiskowe). Błąd importu, brak modułu,
brak zmiennej — objawi się tu natychmiast.

**Krok 2 — czy stdout jest czysty?** Serwer stdio po starcie ma milczeć na
stdout aż do pierwszego żądania. Jeśli po uruchomieniu ręcznym widzisz na
stdout baner, log powitalny, ostrzeżenie biblioteki — znalazłeś przyczynę;
przenieś wszystko na stderr.

**Krok 3 — czy inicjalizacja protokołu przechodzi?** Uruchom serwer przez
MCP Inspector. Jeśli Inspector łączy się i listuje narzędzia, serwer jest
sprawny — problem leży w konfiguracji klienta docelowego.

**Krok 4 — dziennik klienta.** Czytaj log klienta (Claude Desktop: pliki
`mcp*.log` w katalogu logów aplikacji — `~/Library/Logs/Claude/` na macOS,
`%APPDATA%\Claude\logs\` na Windows; Claude Code: tryb diagnostyczny
`claude --mcp-debug` lub polecenie `/mcp`). Log podaje polecenie faktycznie
uruchomione, kod wyjścia procesu i pierwsze bajty, które zepsuły parser.

Najczęstsze przyczyny z sygnaturami:

| Sygnatura w logu / objaw | Przyczyna | Naprawa |
|---|---|---|
| błąd parsowania JSON z fragmentem tekstu ludzkiego | `print`/log na stdout | dziennik na stderr, usuń wypisy |
| proces kończy się natychmiast, kod ≠ 0 | brak modułu, zły interpreter | ścieżka absolutna do venv/binarki |
| `ENOENT` / „nie znaleziono polecenia” | ścieżka względna, `npx` na Windows, PATH klienta bez narzędzia | ścieżka absolutna; `cmd /c npx` na Windows |
| serwer startuje ręcznie, pada w kliencie | brak zmiennej środowiskowej we wpisie `env` | uzupełnij `env` w konfiguracji klienta |
| błąd składni przy starcie Node / stary Python | wersja środowiska niezgodna z wymaganą przez SDK | wskaż interpreter właściwej wersji w `command` |
| serwer znika po chwili bez błędu | proces zakończył się po stracie stdin albo wyjątek w tle | obsłuż zamknięcie transportu, loguj wyjątki na stderr |

Po każdej poprawce konfiguracji restartuj klienta w pełni i wracaj do kroku,
w którym diagnoza się zatrzymała.

## 5. Wersjonowanie i zgodność

- **Przypnij wersje pakietów SDK** (FastMCP, `@modelcontextprotocol/sdk`, zod,
  Pydantic) w plikach blokady (`uv.lock`/`package-lock.json`) i podnoś je
  świadomie, z lekturą informacji o wydaniu — protokół i SDK ewoluują szybko,
  a wzorce z różnych okresów nie są wymienne.
- **Schemat narzędzia to kontrakt API.** Zmiany łamiące — usunięcie narzędzia,
  zmiana nazwy, usunięcie lub przemianowanie parametru, zmiana typu, zawężenie
  enum, zmiana kształtu odpowiedzi — traktuj jak zmiany łamiące API
  publicznego. Zmiany niełamiące: nowy parametr opcjonalny, nowe pole
  odpowiedzi, nowe narzędzie, doprecyzowanie opisu.
- **Wygaszanie zamiast wyrywania.** Przy zmianie łamiącej wprowadź narzędzie
  nowe obok starego; w opisie starego dopisz na początku wskazanie następcy
  („Wycofywane — użyj search_invoices_v2, które…”); usuń stare po okresie
  przejściowym uzgodnionym z użytkownikami serwera. Odpowiednik nagłówka
  deprecation w API — tyle że czytelnikiem jest model.
- Prowadź wersję serwera (semver w metadanych serwera i w pakiecie) i notuj
  zmiany kontraktu narzędzi w informacji o wydaniu projektu.
- Po podniesieniu wersji SDK przepuść pełny poziom 2 i 3 piramidy — regresje
  zgodności protokołu wychodzą właśnie tam.

## 6. Eksploatacja

- **Dziennik strukturalny wywołań narzędzi.** Loguj każde wywołanie jako
  rekord strukturalny (JSON na stderr lub do pliku): czas, nazwa narzędzia,
  czas trwania, status (sukces/błąd/odmowa walidacji), rozmiar odpowiedzi,
  identyfikator sesji, skrócona klasa błędu. **Bez treści wrażliwych**: żadnych
  pełnych wartości parametrów (mogą zawierać dane osobowe i sekrety) ani
  pełnych treści odpowiedzi — wystarczą nazwy parametrów przekazanych
  i rozmiary. Dziennik służy do trzech pytań: co jest wolne, co się sypie,
  czego model używa naprawdę.
- **Limity i odcięcia dla narzędzi kosztownych.** Narzędzia drogie (pełne
  skanowanie, eksport, wywołanie płatnego API) obejmij limitem częstości
  po stronie serwera (np. wiadro żetonów na sesję) i twardym limitem czasu;
  po odcięciu zwracaj komunikat z czasem odczekania. Rozważ dzienny limit
  kosztowy dla API płatnych — serwer MCP potrafi być wywoływany w pętli.
- **Miary minimalne:** liczba wywołań na narzędzie, odsetek błędów na
  narzędzie, percentyle czasu trwania (p50/p95). Narzędzie nieużywane
  tygodniami to kandydat do usunięcia z zestawu (odzysk budżetu kontekstu);
  narzędzie z wysokim odsetkiem odmów walidacji to sygnał złego opisu lub
  schematu.
- **Aktualizacja zależności serwera.** Serwer MCP to zwykle proces
  długodziałający z dostępem do danych — obejmij go tym samym reżimem, co
  usługi produkcyjne: regularny przegląd podatności zależności
  (`pip-audit` / `npm audit`), aktualizacje bezpieczeństwa wprowadzane
  niezwłocznie, aktualizacje funkcjonalne w cyklu wydań z pełnym przebiegiem
  testów. Wersję środowiska uruchomieniowego (Python/Node) utrzymuj w oknie
  wsparcia.
- Sekrety rotuj zgodnie z polityką organizacji; serwer czyta je ze zmiennych
  środowiskowych przy starcie, więc rotacja wymaga restartu — zaplanuj go.
