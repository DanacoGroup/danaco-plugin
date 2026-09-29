---
name: praca-w-duzym-repo
description: >
  Metoda pracy w repozytorium Danaco Console (ponad milion linii, Go + TypeScript +
  Rust/Tauri): orientacja przed edycją, mapa repozytorium, liczenie zasięgu zmiany, budżet
  zmiany, drabina weryfikacji przyrostowej i granice pakietów. Stosuj przed pierwszą edycją
  w nieznanej części repozytorium, gdy zmiana dotyka wielu pakietów naraz, gdy pada „gdzie to
  jest”, „co się zepsuje, jeśli to zmienię”, „jak to jest zorganizowane”, „skąd zacząć”, gdy
  budowa lub testy trwają zbyt długo, gdy kontekst zapełnia się czytaniem plików, oraz przy
  planowaniu refaktoryzacji albo rozbicia dużego pliku i zakładaniu nowego modułu. Ta paczka
  odpowiada za orientację, zasięg i kolejność weryfikacji; samo pisanie kodu prowadzi
  `kodowanie`, reguły stylu `dyscyplina-inzynierska`.
---

# Praca w repozytorium ponadmilionowym

## Kiedy stosować

Stosuj przed pierwszą edycją w nieznanej części repozytorium, przy zmianie dotykającej wielu
pakietów, przy planowaniu refaktoryzacji lub rozbicia dużego pliku oraz gdy budowa i testy
zaczynają trwać zbyt długo.

Nie stosuj tej paczki do samego pisania kodu — to `kodowanie`. Reguł komentarzy, tonu
i zakresu zmiany nie ustala ta paczka, lecz `dyscyplina-inzynierska`; oceny gotowej zmiany
raportem — `kontrola-jakosci`; kształtu danych przechodzących granicę Go↔TypeScript —
`kontrakt-zrodlo-prawdy`.

Zasada nadrzędna: w repozytorium tej wielkości wąskim gardłem jest kontekst, nie pisanie
kodu. Każde czytanie pliku ma koszt i musi być uzasadnione. Metoda sprowadza się do:
zorientuj się tanio, zawęź zanim przeczytasz, zmieniaj wąsko, sprawdzaj przyrostowo.

## Protokół orientacji

Zanim otworzysz pierwszy plik w nieznanej części repozytorium:

1. **Przeczytaj `REPOMAP.md`.** Jeśli go nie ma albo jest stary, wygeneruj:
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/praca-w-duzym-repo/scripts/repo_map.py" tools/
   cp "${CLAUDE_PLUGIN_ROOT}/skills/praca-w-duzym-repo/scripts/impact.py" tools/
   python3 tools/repo_map.py --root . --out REPOMAP.md
   ```
   Mapa daje w jednym czytaniu: rozkład języków, obszary, pakiety Go z liczbą zależności,
   diagram zależności w Mermaid (do 40 pakietów — powyżej byłaby plątanina), moduły
   TypeScriptu o największym zasięgu, największe pliki i listę plików generowanych.
2. **Znajdź węzły.** Sekcja „Węzły” w mapie wskazuje pakiety importowane przez wiele innych.
   Zmiana w węźle to inna klasa ryzyka niż zmiana w liściu — warto o tym wiedzieć przed
   edycją, nie po niej.
3. **Policz zasięg zamierzonej zmiany:**
   ```bash
   python3 tools/impact.py --root . --changed server/internal/session/store.go
   ```
   Narzędzie liczy domknięcie zwrotne grafu zależności — pakiety Go i moduły TypeScriptu,
   które zależą od zmienianego miejsca pośrednio — i wypisuje gotowe polecenia weryfikacji.
4. **Dopiero teraz czytaj kod**, i to wycinkami.

Pominięcie tych kroków nie oszczędza czasu. Przenosi go z fazy orientacji do fazy
debugowania, gdzie kosztuje wielokrotnie więcej.

## Budżet zmiany

Przed edycją wypisz listę plików, które zamierzasz zmienić, i trzymaj się jej. Jeśli w trakcie
lista rośnie ponad dwukrotnie, to nie jest ta sama zmiana co na początku — zatrzymaj się
i przeformułuj zadanie, zamiast ciągnąć rozrastającą się edycję.

| Zakres | Plików | Co to znaczy |
|---|---|---|
| punktowa | 1–3 | zwykła poprawka, weryfikacja lokalna wystarczy |
| modułowa | 4–15 | sprawdź zasięg przed edycją, przetestuj cały dotknięty pakiet |
| przekrojowa | 16+ | rozbij na etapy, każdy osobno kompilowalny i przetestowany |

Zmiana przekrojowa wykonana jednym ciągiem jest praktycznie nieodwracalna: gdy na końcu coś
nie działa, nie ma stanu pośredniego, do którego można wrócić.

## Reguły czytania kodu

- **Czytaj wycinkiem, nie plikiem.** `sed -n '120,180p' plik.go` zamiast całości. Numer linii
  bierz z wyszukiwania, nie ze zgadywania.
- **Zawężaj typem pliku.** `rg --type go 'func \(m \*Manager\)'` zamiast przeszukiwania
  wszystkiego.
- **Szukaj po deklaracji, nie po użyciu.** `rg 'func NewManager' -n` znajduje jedno miejsce;
  `rg 'NewManager'` znajduje sto.
- **Korzystaj z konwencji układu** zamiast przeszukiwać całość. W Danaco Console warstwy mają
  stałe miejsca — szczegóły w `references/granice-i-konwencje.md`.
- **Pliki generowane pomijaj.** Mapa je wypisuje. Czytanie `shared/contract.go`, żeby
  zrozumieć strukturę danych, to strata — źródłem prawdy jest `shared/contract.json`.

Pełny zestaw wzorców wyszukiwania: `references/playbooki-wyszukiwania.md`.

## Drabina weryfikacji

To kanoniczny opis drabiny dla całego pluginu. Sprawdzaj od najtańszego do najdroższego
i **zatrzymuj się na pierwszym niepowodzeniu**.

| Szczebel | Polecenie | Kiedy | Rząd czasu |
|---|---|---|---|
| 1. kontrakt | `task contract:check` | po każdej zmianie w `shared/` | sekunda |
| 2. Go — dotknięty pakiet | `go build ./<pakiet>/...` + `go vet` | po każdej edycji Go | sekundy |
| 3. TS — typy | `task client:types` (`tsc --noEmit`) | po każdej edycji TS | sekundy |
| 4. testy dotknięte | polecenia z `impact.py` | przed commitem | sekundy–minuta |
| 5. lint | `golangci-lint run`, `staticcheck ./...` | przed commitem | minuta |
| 6. testy pełne | `task go:test`, `npx vitest run` | przed scaleniem | minuty |
| 7. bramki domowe | `task standard` | przed commitem | minuta |
| 8. end-to-end i jakość interfejsu | `npx playwright test`, `pa11y`, `lighthouse` | przed wydaniem | minuty |
| 9. budowa powłoki | `cargo tauri build` | przed wydaniem | minuty |

Szczebel 1 jest pierwszy nie przez przypadek: rozjazd kontraktu objawia się na szczeblu 2 i 3
jako lawina błędów o mylących przyczynach. Wykluczenie go najpierw oszczędza szukania.

Szczebel 7 to cel `standard` ze wspólnego pliku
`${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — bramki domowe, które **odmawiają**.
Cel jest wrapperem na jedno polecenie pluginu:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <ścieżki>
```

Uruchamia ono `style_guard.py` i `nazwy_guard.py` razem z audytem porządku repozytorium.
Poszczególne reguły tych walidatorów nazywają się `limit-dlugosci-komentarza`,
`udzial-komentarzy`, `ton-nieformalny`, `wymyslony-kod`, `oznaczenie-literowo-numeryczne`,
`etykieta-jako-zdanie` i `nazwa-metaforyczna`; ich wagi i strojenie opisuje paczka
`weryfikatory-dyscypliny`. Uruchamiaj ten szczebel przed commitem, nie po całym dniu pracy:
bramka, która odmawia po dwudziestu plikach, kosztuje dwadzieścia poprawek.

Szczeble 5–6 są tańsze, niż sugeruje odruch: `task go:test` dobiera równoległość z liczby
rdzeni maszyny (`GO_PAR`), a Vitest zrównolegla domyślnie. To nie jest powód, żeby pomijać
drabinę i od razu uruchamiać wszystko — kolejność oszczędza czas diagnozowania, nie tylko
czas wykonania.

Szczegóły i typowe komunikaty: `references/weryfikacja-przyrostowa.md`.

## Kryteria zakończenia

Zmiana jest gotowa, gdy zachodzą wszystkie cztery warunki:

- lista zmienionych plików mieści się w budżecie zmiany ustalonym przed edycją;
- zasięg zmiany został policzony (`impact.py`), a wskazane przez nie testy przeszły;
- drabina weryfikacji przeszła do szczebla właściwego dla etapu pracy (commit: 1–5 i 7;
  scalenie: dodatkowo 6; wydanie: dodatkowo 8–9);
- nowy plik lub moduł leży w obszarze wskazanym przez sekcję „Granice pakietów”, nie
  w pierwszym pasującym katalogu.

## Narzędzia pomocnicze

**Sprawdź dostępność narzędzia przed użyciem; przy braku pomiń krok, nie przerywaj pracy.**
Plugin nie kontroluje wyposażenia maszyny użytkownika, więc poniższa tabela jest listą
preferencji, nie deklaracją stanu środowiska.

| Zamiast | Użyj, jeśli jest dostępne |
|---|---|
| czytania pakietu, żeby poznać jego API | `go doc ./server/internal/session` |
| zgadywania, gdzie jest definicja | `gopls definition`, `gopls references` |
| ręcznego przeglądu jakości | `golangci-lint run`, `staticcheck ./...` |
| debugowania Go przez `printf` | `dlv test ./server/internal/session` |
| pisania atrap ręcznie | `mockery` |
| ręcznego kodu dostępu do bazy | `sqlc` |
| własnego parsera OpenAPI | `oapi-codegen` |
| `grep` po całym repozytorium | `rg` z `--type`, albo `impact.py` |
| podmiany po tekście | `ast-grep` — wzorzec `store.New($$$)` zamiast wyrażenia regularnego |
| ręcznego liczenia rozmiaru obszarów | `tokei`, `cloc` |
| `find` | `fd` |
| czytania surowego diffu | `delta` |
| ręcznego przeglądania JSON-a | `jq` |
| ręcznego klikania po interfejsie | `npx playwright test` |
| zgadywania, czy interfejs jest dostępny | `pa11y` (WCAG), `lighthouse` (liczbowo) |
| opisywania architektury słowami | diagram z `repo_map.py`, `mermaid-cli`, PlantUML |

Tam, gdzie sprzężenie zwrotne jest dostępne, korzystaj z niego: przy czterdziestu trybach
sesyjnych zrzut ekranu z uruchomionego trybu jest tańszą i pewniejszą odpowiedzią na pytanie
„czy to działa” niż czytanie kodu, który to renderuje.

Dwie rzeczy przy planowaniu pracy. **Kolejność generatorów**: `task contract` idzie przed
`sqlc`, `oapi-codegen`, `mockery` oraz `prisma`/`drizzle-kit`, bo typy z kontraktu bywają dla
nich wejściem — odwrotna kolejność generuje poprawnie wyglądający kod na nieaktualnych
strukturach. **Równoległość jest wyliczana, nie wpisana na sztywno**: `GO_PAR`
w `Taskfile.yml` bierze połowę rdzeni maszyny, więc ten sam cel działa sensownie na stacji
deweloperskiej i na maszynie wydania.

## Granice pakietów

Danaco Console ma cztery obszary o różnych regułach:

- **`shared/`** — kontrakt i to, co z niego wygenerowane. Jedyna dozwolona zależność obu
  światów. Nie umieszczaj tu logiki.
- **`server/`** — rdzeń Go. `cmd/danaco-console` to wyłącznie punkt wejścia i złożenie
  zależności; cała logika mieszka w `internal/`. Pakiety `internal/` nie importują się
  nawzajem w pętli, a im bliżej węzła, tym mniejsza powinna być powierzchnia publiczna.
- **`client/`** — interfejs Vite + TypeScript bez frameworka. Warstwa dostępu do kanału jest
  jedna i wspólna; moduły nie rozmawiają z WebSocketem bezpośrednio.
- **`desktop/src-tauri/`** — powłoka Rust. Zawiera cykl życia okna, uprawnienia i nadzór nad
  procesem rdzenia, nie logikę dziedzinową.

Nowy moduł zakładaj po ustaleniu, do którego obszaru należy. Rozwinięcie:
`references/granice-i-konwencje.md`.

## Kiedy zlecać pracę podagentom

Podagent to nie przyspieszenie, tylko sposób na oszczędzenie kontekstu: czyta dziesiątki
plików, a wraca z wnioskiem. Zlecaj, gdy odpowiedź wymaga przejrzenia wielu miejsc, a
potrzebny jest tylko wynik („znajdź wszystkie miejsca, gdzie tryb jest wybierany na podstawie
łańcucha znaków zamiast `ModeID`”). Nie zlecaj, gdy wiesz, gdzie patrzeć — jedno wyszukanie
jest wtedy tańsze niż uruchomienie agenta.

## Antywzorce

- **Wyszukiwanie zamiast mapy.** Seria `grep` po całym repozytorium daje setki trafień
  i zapełnia kontekst. Mapa odpowiada na to samo pytanie raz.
- **Czytanie w celu upewnienia się.** Kompilator odpowie na to taniej i pewniej.
- **Edycja pliku generowanego.** Zawsze zniknie. Mapa oznacza takie pliki osobną sekcją.
- **Zmiana bez policzonego zasięgu.** Zmiana „lokalna” bywa lokalna tylko z pozoru.
- **Pełne testy po każdej edycji.** Drabina weryfikacji istnieje, żeby tego uniknąć.
- **Nowy plik w pierwszym pasującym katalogu.** Granice pakietów są tańsze do utrzymania niż
  do naprawienia.

## Materiały

- `references/playbooki-wyszukiwania.md` — wzorce znajdowania rzeczy w Go, TypeScripcie
  i Rust
- `references/weryfikacja-przyrostowa.md` — drabina weryfikacji, polecenia, typowe komunikaty
- `references/granice-i-konwencje.md` — układ katalogów, reguły zależności, konwencje
  nazewnicze
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — wspólne cele, w tym `standard`

## Rozgraniczenie z paczkami sąsiednimi

- `kodowanie` — jak przepisać kod, karty języków i frameworków.
- `dyscyplina-inzynierska` — reguły prowadzenia pliku: komentarze, ton, zakres zmiany.
- `weryfikatory-dyscypliny` — uruchamianie i strojenie bramek ze szczebla 7.
- `architektura-i-dokumentacja` — czy struktura projektu jest właściwa.
- `kontrola-jakosci` — treść oceny zmiany i raport ustaleń.
