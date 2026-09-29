# Granice pakietów i konwencje

## Układ repozytorium

```
danaco-console/
├── shared/                     kontrakt i kod z niego wygenerowany
│   ├── contract.json           JEDYNE źródło prawdy dla kształtu danych
│   ├── contract.go             generowany — nie edytować
│   └── CHANGELOG.md            historia wersji kontraktu
├── server/                     rdzeń w Go (moduł danacoconsole obejmuje server/ i shared/)
│   ├── cmd/danaco-console/     punkt wejścia: wczytanie konfiguracji, złożenie zależności, start
│   └── internal/               cała logika; niedostępne spoza modułu
├── client/                     interfejs Vite + TypeScript, bez frameworka
│   ├── src/contract.ts         generowany — nie edytować
│   └── src/                    warstwa kanału, powłoka, moduły
├── desktop/src-tauri/          powłoka Tauri 2 w Rust
└── tools/                      narzędzia repozytorium (m.in. contract_tool.py)
```

## Reguły zależności

Zależności układają się w jedną stronę. Naruszenie tej kolejności jest źródłem cykli, których
w Go nie da się skompilować, a w TypeScripcie kompilują się i psują dopiero w czasie działania.

```
cmd  →  internal/transport  →  internal/{session, ai, mail}  →  internal/store  →  shared
```

- **`shared/` nie importuje niczego z repozytorium.** Jest liściem. Jeśli kusi Cię, żeby wciągnąć
  tam pakiet pomocniczy, to znak, że do kontraktu trafiła logika, która do niego nie należy.
- **`cmd/` nie zawiera logiki.** Wyłącznie: wczytanie konfiguracji, utworzenie zależności,
  uruchomienie, obsługa sygnału zamknięcia. Logika w `cmd/` jest nietestowalna, bo nie da się jej
  zaimportować.
- **Pakiety `internal/` mają wąską powierzchnię publiczną.** Im więcej pakietów importuje dany
  pakiet, tym mniej powinien eksportować — każdy eksportowany symbol jest zobowiązaniem wobec
  wszystkich importujących.
- **Klient ma jedną warstwę kanału.** Moduły interfejsu nie tworzą własnych połączeń WebSocket.
  Wspólna warstwa daje jedno miejsce na wznowienie po zerwaniu, kolejkowanie, korelację
  i obsługę błędów. Rozproszenie tego po modułach oznacza, że każdy z nich obsługuje zerwanie
  połączenia inaczej — czyli w praktyce część z nich nie obsługuje go wcale.
- **Powłoka Rust nie zawiera logiki dziedzinowej.** Cykl życia okna, uprawnienia, nadzór nad
  procesem rdzenia — tyle. Rust jest tu najtrudniejszą warstwą do przetestowania i najdroższą
  do zmiany.

## Gdzie założyć nowy kod

| Co powstaje | Gdzie | Sygnał, że to złe miejsce |
|---|---|---|
| nowy kształt danych przez granicę | `shared/contract.json` | ręczna struktura w Go i TS o tej samej nazwie |
| logika dziedzinowa rdzenia | `server/internal/<obszar>/` | nowy plik w `cmd/` |
| obsługa komunikatu | `server/internal/transport/` | parsowanie koperty w pakiecie dziedzinowym |
| moduł interfejsu | `client/src/modules/<moduł>/` | odwołanie do WebSocketu wprost z modułu |
| element wspólny interfejsu | `client/src/lib/` | ten sam kod w dwóch modułach |
| komenda systemowa | `desktop/src-tauri/` | logika dziedzinowa w Rust |
| narzędzie repozytorium | `tools/` | skrypt w korzeniu bez opisu |
| test end-to-end | `client/e2e/` | test Playwright wśród testów jednostkowych |

Pytanie rozstrzygające przy wątpliwości: **kto jeszcze będzie tego potrzebował?** Rzecz potrzebna
jednemu modułowi zostaje w module. Rzecz potrzebna dwóm idzie do warstwy wspólnej. Rzecz
potrzebna po obu stronach granicy języków idzie do kontraktu.

## Konwencje kodu

**Język.** Identyfikatory po angielsku, komentarze i dokumentacja po polsku. To reguła całego
repozytorium Danaco. Komentarz wyjaśnia **dlaczego**, nie **co** — „co” widać w kodzie.

```go
// Sprawdzamy skrót kontraktu przed otwarciem sesji, bo w instalacji on-premise
// powłoka i rdzeń bywają aktualizowane niezależnie.
if req.ContractHash != shared.ContractHash {
    return shared.ErrContractMismatch
}
```

Ten sam przykład pokazuje regułę bramki językowej: komentarz jest po polsku **z polskimi
znakami**, a identyfikatory po angielsku.

**Go**

- nazwy pakietów krótkie, jednowyrazowe, bez podkreśleń: `session`, nie `session_manager`
- błędy zwracane, nie logowane w środku — decyzję o zalogowaniu podejmuje wywołujący
- `context.Context` jako pierwszy argument wszędzie, gdzie jest wejście/wyjście
- konstruktor `New` przyjmuje zależności, nie tworzy ich sam — inaczej pakiet jest nietestowalny

**TypeScript**

- tryb `strict` włączony; `any` traktowane jak błąd
- typy przychodzące z kanału zawężaj strażnikami z kontraktu (`isModeId`, `isIsolationLevel`),
  nie rzutowaniem
- moduł eksportuje jedną rzecz główną; wszystko poza nią zostaje prywatne
- brak frameworka to decyzja — nie wprowadzaj zależności odtwarzającej framework tylnymi drzwiami

**Rust / Tauri**

- każda komenda `#[tauri::command]` ma wpis w `capabilities`; domyślną odpowiedzią jest odmowa
- proces rdzenia Go uruchamiany z nadzorem i zamykany razem z oknem — proces-sierota po
  zamknięciu aplikacji blokuje port przy następnym starcie

## Dane wrażliwe

Danaco Console pracuje na danych objętych tajemnicą zawodową. Dwie reguły dotyczą każdego pliku
w tym repozytorium:

- **Do dzienników trafiają identyfikatory techniczne, nie treść.** `case_id`, `document_id`,
  typ operacji, wynik — nigdy nazwisko, treść pisma ani sygnatura powiązana z osobą.
- **Komunikaty błędów nie zawierają danych sprawy.** Kod błędu z kontraktu plus identyfikator
  techniczny w ładunku. Wyjątek z treścią rekordu jest usterką do naprawienia, nawet jeśli
  „działa”.

Przy przeglądzie zmiany sprawdź to osobno — jest to klasa błędu, której żaden kompilator
nie wykryje.

## Bramki domowe a styl pisania

`nazwy_guard.py` i `style_guard.py` (razem uruchamiane celem `task standard` — patrz
`SKILL.md`) sprawdzają komentarze i nazewnictwo. Kontrola prozy narzędziami typu Vale,
LanguageTool czy `hunspell-pl` NIE jest częścią tego pluginu — to osobne narzędzia, jeśli
masz je skonfigurowane w repozytorium. Z tego wynikają trzy praktyczne reguły przy pisaniu
kodu w tym repozytorium:

- **Komentarz po polsku pisz z polskimi znakami.** Pominięta diakrytyka jest błędem stylu,
  nie drobnostką, nawet jeśli żaden z tych dwóch skryptów jej dziś nie wykrywa.
- **Nie wymyślaj kodów ani odwołań do norm.** `nazwy_guard.py` (reguła `wymyslony-kod`)
  odrzuca kody bez pokrycia; wyjątek dotyczy norm faktycznie istniejących
  (allowlista w `--config`). Jeśli nie masz pewności co do sygnatury przepisu, nie wpisuj jej
  do komentarza.
- **Trzymaj się limitu gęstości komentarzy** (`style_guard.py`, reguła `udzial-komentarzy`;
  próg domyślny 20%, konfigurowalny przez `--config` — patrz
  umiejętność `weryfikatory-dyscypliny`). Wymusza komentowanie *dlaczego* zamiast opisywania
  *co* — a to i tak jest właściwy komentarz. Pliki generowane wymagają wyłączenia spod tej
  reguły; ręcznie pisane nie.
