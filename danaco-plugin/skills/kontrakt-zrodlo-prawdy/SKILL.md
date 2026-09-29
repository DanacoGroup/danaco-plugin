---
name: kontrakt-zrodlo-prawdy
description: >
  Kontrakt jako jedyne źródło prawdy w Danaco Console: `shared/contract.json` → generowanie
  `shared/contract.go` i `client/src/contract.ts`, walidacja i wykrywanie rozjazdu
  Go↔TypeScript. Stosuj zawsze, gdy powstaje lub zmienia się typ danych, komunikat WebSocket,
  komenda Tauri, kod błędu albo tryb sesyjny (środowisko.moduł) — również wtedy, gdy pada
  zwykłe „dodaj pole”, „nowy endpoint”, „nowy moduł”, „zmień strukturę odpowiedzi” i nikt nie
  wspomina o kontrakcie. Sięgaj po nią także przy „klient dostaje undefined”, „pole nie
  dochodzi”, rozjeździe wersji klienta i rdzenia oraz przy wpinaniu kontroli kontraktu
  w pre-commit, testy i wydania. Kontrakt jest zawsze krokiem pierwszym: obsługę komunikatu
  w kanale prowadzi `kanal-websocket`, komendę w powłoce `most-tauri`, widoczność trybu
  `macierz-trybow-sesji`.
---

# Kontrakt jako źródło prawdy

## Kiedy stosować

Stosuj zawsze, gdy powstaje lub zmienia się typ danych, komunikat WebSocket, komenda Tauri,
kod błędu albo tryb sesyjny — także wtedy, gdy prośba brzmi zwyczajnie („dodaj do sprawy pole
z terminem przedawnienia”, „zrób komunikat, który wysyła postęp modelu AI”) i nikt nie
wspomina o kontrakcie. Stosuj też przy rozjeździe typów, `undefined` po stronie klienta
i rozjeździe wersji klienta i rdzenia.

Kontrakt jest krokiem pierwszym, nie alternatywą. Nie stosuj tej paczki do obsługi komunikatu
w kanale (kolejność, wznowienie, przeciwciśnienie) — to `kanal-websocket`. Implementacji
komendy w Rust, uprawnień i wydania nie prowadzi ta paczka, lecz `most-tauri`; tego, co dany
tryb widzi i gdzie zapisuje — `macierz-trybow-sesji`.

Trzy światy Danaco Console (rdzeń Go, interfejs TypeScript, powłoka Rust) nie mają wspólnego
kompilatora. Jeśli kształt danych żyje w trzech miejscach naraz, rozjazd jest kwestią czasu —
i to rozjazd, którego żaden kompilator nie wykryje.

## Zasada nadrzędna

> Każda zmiana kształtu danych zaczyna się w `shared/contract.json`. Nigdy w `contract.go`,
> nigdy w `contract.ts`.

Wygenerowanych plików nikt nie edytuje ręcznie; strażnik rozjazdu pilnuje, żeby tak zostało.

## Krok zerowy: zainstaluj narzędzie w repozytorium

Sprawdź, czy repozytorium ma `tools/contract_tool.py`. Jeśli nie ma — zainstaluj je:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/scripts/contract_tool.py" \
    install --root .
```

Narzędzie musi być **wersjonowane razem z kontraktem**, a nie uruchamiane z katalogu wtyczki:
generator i kontrakt tworzą parę. Jeśli dwie osoby albo maszyna deweloperska i wydanie mają
różne wersje generatora, ten sam `contract.json` da różny kod i strażnik rozjazdu zacznie
zgłaszać różnice, których nikt nie wprowadził. Bez tego kroku nie działają też hak pre-commit
i cele `task`, bo odwołują się do ścieżki w repozytorium.

## Procedura zmiany

1. **Znajdź kontrakt.** Zwykle `shared/contract.json` w korzeniu repozytorium. Jeśli go nie
   ma, zacznij od `assets/contract.example.json` z tej paczki — gotowy szkielet Danaco
   Console z czterema środowiskami po osiem modułów, czyli 32 trybami.
2. **Ustal, gdzie zmiana należy.** Tabela „Co mieści kontrakt” niżej rozstrzyga, czy to nowy
   typ, komunikat, komenda, kod błędu czy tryb.
3. **Wprowadź zmianę w JSON-ie.** Trzymaj się nazewnictwa: typy i enumy w `PascalCase`, pola
   w `camelCase`, kanały i komendy w `snake_case`, kody błędów `WIELKIMI_LITERAMI`.
4. **Podnieś `contractVersion`.** Zasady w `references/wersjonowanie.md` — w skrócie: zmiana
   dodająca to `MINOR`, zmiana łamiąca to `MAJOR`.
5. **Zwaliduj i wygeneruj:**
   ```bash
   python3 tools/contract_tool.py gen --root .
   ```
6. **Skompiluj oba światy.** `go build ./...` oraz `npx tsc --noEmit`. Jeśli coś się nie
   kompiluje, to jest dokładnie ta informacja, którą kontrakt miał dostarczyć — miejsca,
   które zmiana psuje, są teraz wypisane przez kompilator, a nie odkrywane w produkcji.
7. **Dopisz logikę ręczną.** Kontrakt daje typy, stałe i rejestry. Obsługa nowego komunikatu
   w rdzeniu Go i w kliencie to kod pisany ręcznie — ale pisany na wygenerowanych typach.

## Kryteria zakończenia

Zmiana kontraktu jest gotowa, gdy zachodzą wszystkie pięć warunków:

- `contract_tool.py validate` zwraca `0`;
- `contract_tool.py check` zwraca `0`, czyli dysk zgadza się z kontraktem;
- `go build ./...` i `npx tsc --noEmit` przechodzą po regeneracji;
- `contractVersion` jest podniesione zgodnie z rodzajem zmiany (dodająca lub łamiąca);
- każde miejsce, które zmiana zepsuła, jest obsłużone ręcznie napisanym kodem na
  wygenerowanych typach, a nie obejściem w pliku generowanym.

## Narzędzie

`scripts/contract_tool.py` — czysty Python 3.9+, biblioteka standardowa, bez instalacji.
Świadomie nie jest to program w Go: ma działać także wtedy, gdy moduł Go się nie kompiluje,
bo najczęściej właśnie wtedy jest potrzebny.

```bash
CT="${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/scripts/contract_tool.py"

python3 "$CT" install  --root .   # kopiuje narzędzie do tools/ (raz na repozytorium)
python3 "$CT" validate --root .   # sprawdza kontrakt, nic nie zapisuje
python3 "$CT" gen      --root .   # generuje contract.go i contract.ts
python3 "$CT" check    --root .   # porównuje dysk z kontraktem, pokazuje różnice
```

Po instalacji wołaj wersję z repozytorium: `python3 tools/contract_tool.py gen --root .`.

Kody wyjścia: `0` w porządku, `2` kontrakt niepoprawny, `3` rozjazd, `4` błąd wejścia lub
wyjścia. Dzięki temu `check` wchodzi wprost do haka pre-commit i do wydania.

Ścieżki docelowe narzędzie bierze z sekcji `generated` kontraktu, więc przeniesienie plików
jest zmianą w JSON-ie, nie w narzędziu. Przełącznik `--doc-comments none` generuje kod bez
komentarzy przeniesionych z pól `doc`.

**Nazwa komunikatu na drucie.** Powstaje z kanału i nazwy, przy czym wspólny przedrostek jest
odcinany: `AiPrompt` w kanale `ai` daje `ai.prompt`, nie `ai.ai.prompt`. Komunikat o nazwie
niezaczynającej się od kanału (`Ping` w kanale `session`) daje `session.ping`. Pole `wire`
w kontrakcie nadpisuje tę regułę w całości — używaj go, gdy nazwa na drucie jest już ustalona
przez działającego klienta.

**Rejestry są emitowane zawsze**, także dla kontraktu bez sekcji `modes`, `messages` czy
`errors`. `Envelope` odwołuje się do `ModeID` i `ErrorCode`, a testy z `assets/` do `Modes`,
`MessageDirection` i `ErrorMessages` — kontrakt w budowie musi się kompilować tak samo jak
pełny.

Wygenerowany kod Go przechodzi przez `gofmt`, więc wynik przechodzi `gofmt -l` bez zastrzeżeń
i odruchowe `gofmt -w .` nie wciągnie go do diffu. Gdy `gofmt` nie jest dostępny, narzędzie
ostrzega — bo wtedy ten sam kontrakt da inny wynik na maszynie z Go, czyli fałszywy rozjazd.

## Co mieści kontrakt

| Sekcja | Co opisuje | Co z tego powstaje |
|---|---|---|
| `enums` | zamknięte zbiory wartości (`IsolationLevel`, `AiRole`, `SessionState`) | Go: typ + stałe + `Valid()`; TS: unia + tablica + strażnik `isX` |
| `types` | struktury danych przechodzące przez granicę | Go: `struct` ze znacznikami JSON; TS: `interface` |
| `modes` | rejestr trybów sesyjnych `środowisko.moduł` | Go: `ModeID`, `Modes`, `LookupMode`; TS: `ModeId`, `MODES`, `ENVIRONMENTS`, `MODULES_BY_ENVIRONMENT` |
| `messages` | komunikaty kanału WebSocket wraz z kierunkiem | Go: `MessageType`, `MessageDirection`, `MessageResponse`, `NewPayload`, `Envelope`; TS: `MESSAGE_TYPES`, `MessagePayloads`, `MESSAGE_RESPONSE`, `Envelope<T>` |
| `commands` | komendy IPC Tauri | Go: `CommandName`; TS: `Commands` |
| `errors` | kody błędów i ich bezpieczne treści | Go: `ErrorCode` + `ErrorMessages`; TS: `ERROR_CODES` + `ERROR_MESSAGES` |

Pełny schemat każdego pola: `references/schemat-kontraktu.md`.

## Co należy do kontraktu, a co nie

**Należy** wszystko, co przekracza granicę procesu lub języka: kształt komunikatu, nazwa
trybu, kod błędu, wartość enumu widoczna w interfejsie.

**Nie należy** to, co żyje wyłącznie po jednej stronie: struktury wewnętrzne pakietów
`internal/`, kształt wierszy w bazie, stan lokalny komponentu, pomocnicze typy pośrednie.
Wciąganie ich do kontraktu zamienia go w wysypisko i sprawia, że każda drobna zmiana
wewnętrzna wymusza regenerację całości.

Test rozstrzygający: **czy druga strona granicy musi znać ten kształt, żeby poprawnie
zadziałać?** Jeśli nie — zostaw poza kontraktem.

## Uzgodnienie kontraktu w czasie działania

Generator wpisuje do obu plików `ContractVersion` i `ContractHash` (skrót kanonicznej postaci
kontraktu). Wykorzystaj to: przy otwarciu połączenia klient przesyła swój `CONTRACT_HASH`,
rdzeń porównuje z własnym i przy różnicy odrzuca połączenie kodem `E_CONTRACT_MISMATCH`.

To zamienia najgorszą klasę usterek — cichy rozjazd wersji po częściowej aktualizacji
aplikacji desktopowej — w jednoznaczny, natychmiastowy komunikat.

**Czego ta bramka nie łapie.** Skrót liczony jest z `contract.json`, a nie z wygenerowanych
plików. Jeśli ktoś ręcznie poprawi `contract.go` albo `contract.ts`, obie strony zgłoszą
identyczny skrót i uzgodnienie przejdzie, mimo że kod jest rozjechany. Ręczną edycję plików
generowanych wykrywa wyłącznie `check`, i tylko dlatego musi być podpięty pod pre-commit
i pod wydanie. Uzgodnienie skrótu i strażnik rozjazdu pilnują dwóch różnych rzeczy i żadne
z nich nie zastępuje drugiego.

## Podpięcie pod codzienną pracę

Strażnik działa tylko wtedy, gdy uruchamia się sam. Gotowe fragmenty leżą w `assets/`:

- `assets/Taskfile.yml` — cele `contract`, `contract:check`, `check`, `standard` oraz cała
  drabina weryfikacji (`task --list`); to podstawowy sposób uruchamiania w tym repozytorium
- `assets/Makefile.fragment` — te same cele dla `make`
- `assets/pre-commit.sample` — hak odrzucający commit z rozjazdem
- `assets/contract_test.go` — test Go sprawdzający kompletność rejestru trybów i mapy błędów
- `assets/contract.test.ts` — test Vitest sprawdzający zgodność skrótu i spójność rejestru

Skopiuj je do repozytorium i dostosuj ścieżki. Szczegóły: `references/integracja.md`.

**Kolejność wobec pozostałych generatorów.** W repozytorium pracują też `sqlc`,
`oapi-codegen` i `mockery`. Kontrakt idzie pierwszy: jego typy bywają wejściem dla
pozostałych, a odwrotna kolejność daje generowanie na podstawie nieaktualnych struktur. Cel
`task contract` powinien poprzedzać każdy inny krok generowania.

## Kontrakt a bramki dyscypliny

Trzy ustalenia, które trzeba znać przed pierwszym uruchomieniem bramek na wygenerowanym
kodzie. Pomiary, konfiguracja wyłączeń i wymagania narzędzi zewnętrznych repozytorium
(Vale, LanguageTool, `hunspell-pl`, Semgrep): `references/integracja.md`.

- **Pliki generowane trzeba wyłączyć spod reguły `udzial-komentarzy`.** Wygenerowany kontrakt
  przekracza próg wielokrotnie, bo komentuje każdy tryb, każde pole i każdy kod błędu. Limit
  ma pilnować prozy pisanej ręcznie, nie tabeli, w której komentarz przy każdym trybie jest
  jedynym miejscem, gdzie widać, czym ten tryb jest. `--doc-comments none` istnieje na
  wypadek, gdyby wyłączenie było niemożliwe, ale samo w sobie pod limit nie zejdzie.
- **Wymyślone oznaczenia.** W komentarzach zgłasza je `style_guard.py` regułą
  `wymyslony-kod`, a w identyfikatorach `nazwy_guard.py` regułą
  `oznaczenie-literowo-numeryczne` — obie jako ostrzeżenia, nie bramki blokujące. Kody błędów
  z kontraktu (`E_MODE_UNKNOWN`) są identyfikatorami wewnętrznymi i nie podlegają zakazowi.
  Podlega mu natomiast każde odwołanie do normy, przepisu czy sygnatury w polach `doc`
  i `message`: jeśli nie masz pewności, że dana norma istnieje i brzmi dokładnie tak, nie
  wpisuj jej do kontraktu.
- **Polszczyzna w polach `doc` i `message`.** Wartości trafiają wprost do komentarzy w Go
  i TypeScripcie. Pisz je poprawną polszczyzną z polskimi znakami. Identyfikatory (`id`
  trybu, `environment`, `module`, nazwy typów i pól) zostają po angielsku i bez diakrytyki,
  bo są kodem, nie prozą. Pole `message` w sekcji `errors` bywa pokazywane użytkownikowi,
  więc nie może zawierać kodu błędu ani nazwy komunikatu — kod przekazuj osobnym polem
  `error_code` w kopercie.

Wagi reguł, progi i strojenie: paczka `weryfikatory-dyscypliny`.

## Zmiany dodające i łamiące

Kontrakt jest umową między rdzeniem a interfejsem, które w aplikacji desktopowej **nie
aktualizują się jednocześnie**. Użytkownik może mieć starszą powłokę i nowszy rdzeń albo
odwrotnie.

- **Dodająca** (`MINOR`): nowe pole opcjonalne, nowy typ, nowy komunikat, nowy tryb, nowy kod
  błędu. Starsza strona zignoruje to, czego nie zna.
- **Łamiąca** (`MAJOR`): usunięcie lub zmiana nazwy pola, zmiana typu pola, zmiana wartości
  enumu, zmiana kierunku komunikatu, usunięcie trybu. Wymaga okresu przejściowego.

Wzorzec wycofywania pola (dodaj nowe → oznacz stare jako `deprecated` → usuń dopiero po dwóch
wydaniach) opisuje `references/wersjonowanie.md`.

## Częste pułapki

- **Ręczna poprawka w wygenerowanym pliku.** Znika przy najbliższym `gen`. Jeśli kusi Cię,
  żeby coś dopisać do `contract.go`, to znak, że brakuje tego w kontrakcie albo że to logika,
  która powinna trafić do osobnego pliku obok.
- **Tryb dodany w kodzie, nie w kontrakcie.** Rejestr `Modes` przestaje być kompletny, a wraz
  z nim routing, uprawnienia i nawigacja interfejsu. Każdy tryb musi jawnie deklarować
  `isolation` — walidator odrzuci tryb bez tego pola.
- **Dane wrażliwe w treści błędu.** Pole `message` bywa pokazywane użytkownikowi i trafia do
  dzienników. Trzymaj tam ogólne komunikaty; szczegóły przekazuj identyfikatorami
  technicznymi w `payload`.
- **`response` mylone z typem ładunku.** Pole `response` wskazuje **komunikat** odpowiedzi
  (`SessionOpen` → `SessionOpened`), nie typ danych. Walidator odrzuca nazwę spoza sekcji
  `messages` oraz `response` przy komunikacie wysyłanym przez rdzeń.
- **`int64` w TypeScripcie.** Generator odwzorowuje go na `number`, co gubi precyzję powyżej
  2^53. Dla identyfikatorów używaj `uuid` albo `string`; `int64` zostaw dla liczników
  i znaczników czasu.
- **Komentarze po angielsku.** W tym repozytorium dokumentacja i komentarze idą po polsku,
  identyfikatory po angielsku.

## Materiały

- `references/schemat-kontraktu.md` — pełny schemat `contract.json`, każde pole i jego
  odwzorowanie na Go i TypeScript
- `references/wersjonowanie.md` — zmiany dodające i łamiące, wycofywanie pól, migracja danych
- `references/integracja.md` — Taskfile, Makefile, pre-commit, testy Go i Vitest, wyłączenia
  bramek dla plików generowanych, wydania
- `assets/contract.example.json` — gotowy kontrakt startowy Danaco Console
- `assets/Taskfile.yml` — wspólny plik celów dla całego repozytorium, w tym `standard`

## Rozgraniczenie z paczkami sąsiednimi

- `kanal-websocket` — obsługa, kolejność i wznowienie komunikatu zadeklarowanego tutaj.
- `most-tauri` — implementacja komendy w Rust, uprawnienia, `generate_handler!`, wydanie.
- `macierz-trybow-sesji` — co tryb widzi i gdzie zapisuje; rejestr trybów mieszka tutaj.
- `weryfikatory-dyscypliny` — wagi i progi bramek dyscypliny.
- `praca-w-duzym-repo` — kolejność weryfikacji, w której kontrakt jest szczeblem pierwszym.
