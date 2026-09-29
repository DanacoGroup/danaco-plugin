# Schemat `shared/contract.json`

## Spis treści

1. [Szkielet dokumentu](#szkielet-dokumentu)
2. [Wyrażenia typowe](#wyrażenia-typowe)
3. [`enums`](#enums)
4. [`types`](#types)
5. [`modes`](#modes)
6. [`messages`](#messages)
7. [`commands`](#commands)
8. [`errors`](#errors)
9. [Reguły walidatora](#reguły-walidatora)

## Szkielet dokumentu

```json
{
  "contractVersion": "1.0.0",
  "generated": {
    "go": { "path": "shared/contract.go", "package": "shared" },
    "ts": { "path": "client/src/contract.ts" }
  },
  "enums": [],
  "types": [],
  "modes": [],
  "messages": [],
  "commands": [],
  "errors": []
}
```

`contractVersion` — semver, obowiązkowy. `generated` — ścieżki docelowe względem korzenia
repozytorium; zmiana układu katalogów to zmiana tutaj, nie w generatorze.

## Wyrażenia typowe

| Wyrażenie | Go | TypeScript |
|---|---|---|
| `string` | `string` | `string` |
| `uuid` | `string` | `string` |
| `int` | `int` | `number` |
| `int64` | `int64` | `number` |
| `float` | `float64` | `number` |
| `bool` | `bool` | `boolean` |
| `timestamp` | `time.Time` | `string` (ISO 8601) |
| `bytes` | `[]byte` | `string` (base64) |
| `json` | `json.RawMessage` | `unknown` |
| `NazwaTypu` | `NazwaTypu` | `NazwaTypu` |
| `T[]` | `[]T` | `T[]` |
| `map<T>` | `map[string]T` | `Record<string, T>` |

Zagnieżdżenia działają: `map<string[]>`, `SessionRef[][]`.

`timestamp` po stronie TypeScriptu jest łańcuchem znaków, nie obiektem `Date` — konwersję rób
świadomie w warstwie interfejsu. Automatyczne parsowanie w wygenerowanym kodzie ukryłoby błędy
strefy czasowej, których w terminach procesowych nie wolno ukrywać.

## `enums`

```json
{
  "name": "IsolationLevel",
  "doc": "określa, ile stanu tryb dzieli z pozostałymi trybami sesji.",
  "values": [
    { "name": "Shared",   "value": "shared",   "doc": "stan widoczny dla całej sesji" },
    { "name": "Isolated", "value": "isolated", "doc": "własna przestrzeń nazw" }
  ]
}
```

`name` w `PascalCase`, `value` to postać na drucie. Powstaje:

- Go — typ `type IsolationLevel string`, stałe `IsolationLevelShared`, tablica
  `AllIsolationLevels`, metoda `Valid() bool`
- TS — `ISOLATION_LEVEL` (`as const`), typ `IsolationLevel`, strażnik `isIsolationLevel`

Strażnik jest istotny: dane z WebSocketu są nieufne, a `isIsolationLevel(v)` zawęża typ bez
rzutowania.

## `types`

```json
{
  "name": "SessionRef",
  "doc": "wskazuje konkretną sesję w konkretnym trybie.",
  "fields": [
    { "name": "sessionId", "type": "uuid", "doc": "identyfikator sesji" },
    { "name": "parentSessionId", "type": "uuid", "optional": true },
    { "name": "tags", "type": "string[]", "json": "labels" }
  ]
}
```

- `name` pola w `camelCase`; klucz JSON powstaje automatycznie jako `snake_case`
  (`sessionId` → `session_id`), chyba że podasz `json` jawnie
- `optional: true` → Go: wskaźnik + `,omitempty`; TS: pole opcjonalne
- tablice i mapy nie stają się wskaźnikami nawet jako opcjonalne — `nil` i pusta kolekcja są w Go
  nieodróżnialne po deserializacji, więc wskaźnik do wycinka daje złudne poczucie precyzji

## `modes`

```json
{
  "id": "kancelaria.sprawy",
  "environment": "kancelaria",
  "module": "sprawy",
  "isolation": "shared",
  "doc": "Rejestr spraw, sygnatury, statusy"
}
```

`id` musi mieć postać `środowisko.moduł`, małymi literami, a pola `environment` i `module` muszą
się z nim zgadzać — nadmiarowość jest celowa, bo walidator wychwytuje literówkę, której samo `id`
by nie wykryło.

`isolation` jest obowiązkowe. Brak wartości domyślnej to decyzja projektowa: w systemie z danymi
objętymi tajemnicą zawodową milcząca domyślna izolacja jest najkrótszą drogą do wycieku między
sprawami. Autor trybu musi zadeklarować zakres świadomie.

Powstaje: Go `ModeID` + stałe `ModeKancelariaSprawy` + mapa `Modes` + `LookupMode`; TS `ModeId`,
`MODES`, `ENVIRONMENTS`, `MODULES_BY_ENVIRONMENT`, `isModeId`.

`MODULES_BY_ENVIRONMENT` daje interfejsowi gotową nawigację — lista modułów środowiska nie jest
nigdzie przepisywana ręcznie.

## `messages`

```json
{
  "name": "AiAttach",
  "channel": "ai",
  "direction": "clientToServer",
  "payload": "AiAttachRequest",
  "response": "AiAttached",
  "doc": "podłącza model AI do sesji"
}
```

`response` wskazuje `AiAttached` — komunikat z sekcji `messages`, a nie typ `AiChannel`, który
ten komunikat niesie jako ładunek.

- `direction`: `clientToServer`, `serverToClient` albo `bidirectional`
- `wire` — nazwa na drucie; pominięta powstaje z `channel` i nazwy, ze ściętym wspólnym
  przedrostkiem (`AiPrompt` w kanale `ai` → `ai.prompt`; `Ping` w kanale `session` → `session.ping`)
- `response` — **nazwa komunikatu odpowiedzi**, nie typu ładunku; ma sens wyłącznie dla
  komunikatu wysyłanego przez klienta. Powstaje z tego mapa `MessageResponse` w Go
  i `MESSAGE_RESPONSE` w TypeScripcie

Powstaje Go: `MessageType`, stałe `MsgAiPrompt`, mapa `MessageDirection`, funkcja `NewPayload`
zwracająca pustą strukturę ładunku, oraz `Envelope`. TS: `MESSAGE_TYPES`, `MessagePayloads`,
`MESSAGE_DIRECTION`, `Envelope<T>`.

`NewPayload` jest sercem dekodera w Go — zdejmuje z każdego handlera obowiązek pamiętania,
jaka struktura odpowiada jakiej nazwie komunikatu.

`Envelope<T>` po stronie TypeScriptu wiąże `type` z `payload`, więc `env.type === "ai.delta"`
zawęża `env.payload` do `AiDelta` bez rzutowania.

## `commands`

```json
{ "name": "core_status", "request": "CoreStatusRequest", "response": "CoreStatus", "doc": "stan rdzenia" }
```

`name` w `snake_case` — tego wymaga Tauri. `request` i `response` są opcjonalne (komenda bez
argumentów i bez wyniku). Powstaje Go `CommandName` oraz TS `Commands` — mapa nazwa → kształt
żądania i odpowiedzi, na której buduje się typowaną otoczkę `invoke`.

## `errors`

```json
{ "code": "E_ISOLATION_VIOLATION", "message": "Próba dostępu poza przyznaną przestrzeń izolacji.", "doc": "tor AI sięgnął po stan spoza swojego zakresu" }
```

`code` wielkimi literami z podkreśleniami. Nazwa stałej powstaje po odcięciu prefiksu `E_`:
`E_SESSION_UNKNOWN` → `ErrSessionUnknown` / `"E_SESSION_UNKNOWN"`.

`message` bywa pokazywane użytkownikowi i trafia do dzienników — trzymaj tam treść ogólną.
Szczegóły przekazuj identyfikatorami technicznymi w ładunku, nigdy nazwiskiem, sygnaturą
powiązaną z osobą ani treścią pisma.

## Reguły walidatora

Walidator odrzuca kontrakt, gdy:

- `contractVersion` nie jest semverem
- nazwa typu lub enumu nie jest w `PascalCase` albo powtarza się między sekcjami
- pole nie jest w `camelCase`, powtarza się, koliduje ze słowem kluczowym Go lub TS,
  albo jego klucz JSON powtarza się w obrębie typu
- jakiekolwiek odwołanie typowe nie daje się rozwiązać (typ, enum lub prymityw)
- `id` trybu nie ma postaci `środowisko.moduł` albo nie zgadza się z polami `environment`/`module`
- tryb nie ma `isolation` lub ma wartość spoza enumu `IsolationLevel`
- `direction` komunikatu jest inne niż trzy dopuszczalne, `channel` nie jest w `snake_case`,
  albo nazwa na drucie powtarza się
- `payload` lub `response` komunikatu wskazuje nieistniejący typ
- nazwa komendy nie jest w `snake_case` albo się powtarza
- kod błędu nie jest zapisany wielkimi literami, powtarza się albo nie ma pola `message`
- nazwa typu lub enumu jest jedną z nazw wytwarzanych przez generator (`Envelope`, `ModeInfo`,
  `Commands`, `ErrorCode` i pokrewne) — w wygenerowanym kodzie powstałaby podwójna deklaracja
- dwa pola tego samego typu dają tę samą nazwę pola w Go (`caseId` i `caseID`)
- `response` komunikatu nie jest nazwą innego komunikatu albo stoi przy komunikacie
  wysyłanym przez rdzeń

Wszystkie błędy są wypisywane naraz, nie po jednym — przy dużym kontrakcie poprawianie ich
seriami byłoby stratą czasu.
