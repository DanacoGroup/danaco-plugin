# Katalog antywzorców nazewnictwa — karta

Karta obejmuje antywzorce w nazywaniu bytów: plików, zmiennych, funkcji, typów,
komponentów i etykiet. Antywzorce w samym kodzie — historia w komentarzach, kopie
plików, martwy kod — leżą w `../../wspolne/standardy-zawodowe/katalog-antywzorcow.md`.

Lewa kolumna to wzorce odrzucane przez walidator lub przegląd. Prawa to kierunek poprawy.
Konkretna poprawna nazwa zależy od funkcji elementu i konwencji repozytorium.

## Metafory przestrzenne i poetyckie

| Antywzorzec | Kierunek poprawy |
|---|---|
| `korzenWejscia`, `korzen-wejscia` | `entryPoint`, `appRoot` |
| `przedpokoj` | `layout`, `shell`, `frame` |
| `szynaLewa`, `szyna-lewa` | `sidebar`, `navRail`, `leftNav` |
| `kregoslup`, `kregoslupUI` | `layoutRoot`, `mainLayout` |
| `serceSystemu` | nazwa wg rzeczywistej roli, np. `scheduler`, `dispatcher` |
| `mozg`, `dusza` | nazwa wg funkcji, np. `decisionEngine`, `stateStore` |
| `wrota`, `swiatynia`, `labirynt` | nazwa wg funkcji, np. `gateway`, `registry`, `router` |

Uwaga: terminy przyjęte w Danaco nie są metaforą — „most” (bridge Tauri), „kanał”
(channel WebSocket), „magistrala” (bus) to standard architektury i pozostają.

## Wymyślone oznaczenia literowo-numeryczne

| Antywzorzec | Kierunek poprawy |
|---|---|
| `MOD-01`, `moduleMOD01` | nazwa modułu wg funkcji; kod tylko jeśli definiuje go kontrakt |
| `K-3`, `CMP-100` | nazwa komponentu wg roli, np. `MessageList`, `CaseHeader` |
| `WS_12` (własny kod komunikatu) | typ komunikatu z kontraktu (`shared/contract.json`) |
| własny system numeracji błędów | kody błędów wyłącznie z kontraktu |

## Etykiety UI

| Antywzorzec | Kierunek poprawy |
|---|---|
| „filtr wyszukiwania per sesja” | „Filtry” |
| „przycisk otwierający panel ustawień” | „Ustawienia” |
| „lista wszystkich spraw użytkownika” | „Sprawy” |
| etykieta dłuższa niż trzy słowa | krótka nazwa funkcji |

## Nazwy plików

| Antywzorzec | Kierunek poprawy |
|---|---|
| `przedpokoj.ts` | `layout.ts` / `AppShell.tsx` |
| `szyna.tsx` | `Sidebar.tsx` |
| `serce.go` | nazwa wg pakietu i funkcji, np. `dispatcher.go` |

## Zasada rozstrzygająca

Gdy wahasz się między nazwą opisową a obrazową — wybierasz opisową. Gdy kusi Cię nadanie
kodu lub numeru — sprawdzasz kontrakt; jeśli kodu tam nie ma, nie tworzysz go.
