# Electron — karta

Karta obejmuje Electron jako framework aplikacji: układ procesów i podstawy pracy.
Pełne opracowanie — bezpieczeństwo, IPC i preload, warstwa natywna, pakowanie,
podpisywanie, aktualizacje, wydajność — leży w paczce `most-tauri`:
`../most-tauri/references/electron-desktop/electron-desktop.md`.

Przeczytaj tę kartę w całości przed rozpoczęciem pracy z kodem Electron. Model bezpieczeństwa
opisany poniżej jest nienegocjowalny: proces renderujący traktuj jak nieufną stronę internetową,
nawet gdy wyświetla wyłącznie lokalne pliki aplikacji.

## Struktura projektu

Przyjmij układ rozdzielający trzy konteksty wykonania:

```
projekt/
├── package.json          # pole "main" wskazuje punkt wejścia procesu głównego
├── electron-builder.yml  # konfiguracja pakowania
├── src/
│   ├── main/             # proces główny: okna, cykl życia, IPC, dostęp do systemu
│   │   ├── index.js      # punkt wejścia, tworzenie BrowserWindow
│   │   └── ipc/          # procedury obsługi ipcMain, pogrupowane domenowo
│   ├── preload/
│   │   └── index.js      # most contextBridge — jedyny łącznik między światami
│   └── renderer/         # interfejs użytkownika (HTML/JS lub framework)
└── build/                # ikony i zasoby instalatora
```

Przestrzegaj granic: dostęp do systemu plików, powłoki, urządzeń i sekretów należy wyłącznie do
procesu głównego; renderer wyłącznie prezentuje dane i zgłasza żądania przez most preload; preload
zawiera możliwie mało kodu — tylko definicję udostępnianego API. Nie importuj modułów Node w kodzie
renderera. Nie twórz logiki biznesowej w preload. Nie umieszczaj kodu procesu głównego i renderera w
jednym pliku ani wspólnym module z importami obu środowisk.

## Konwencje frameworka

- Twórz `BrowserWindow` wyłącznie z bezpiecznymi ustawieniami `webPreferences`: `contextIsolation:
  true`, `nodeIntegration: false`, `sandbox: true`, `preload` wskazujący skrypt mostu. Są to
  wartości zgodne z domyślnymi zaleceniami Electron — nie osłabiaj ich.
- Udostępniaj rendererowi wyłącznie wąskie, nazwane API przez `contextBridge.exposeInMainWorld`.
  Nigdy nie eksponuj całych obiektów `ipcRenderer`, `require` ani modułów Node — udostępniaj
  konkretne funkcje o ustalonej sygnaturze.
- Komunikację żądanie–odpowiedź prowadź przez `ipcRenderer.invoke` i `ipcMain.handle`; powiadomienia
  z procesu głównego wysyłaj przez `webContents.send` z nasłuchem w preload. Nie używaj
  przestarzałego modułu `remote` ani `sendSync`, który blokuje renderer.
- Waliduj w procesie głównym każde wejście z IPC (typy, zakresy, ścieżki plików) — renderer może być
  skompromitowany, więc procedura obsługi nie może ufać argumentom. Nie buduj procedur ogólnych w
  rodzaju „wykonaj dowolne polecenie” ani „odczytaj dowolną ścieżkę”.
- Nie ładuj zdalnych treści w oknach z dostępem do IPC. Jeżeli aplikacja musi wyświetlić stronę
  zewnętrzną, użyj osobnego, w pełni odizolowanego okna bez skryptu preload z uprawnieniami; blokuj
  nawigację (`will-navigate`) i otwieranie okien (`setWindowOpenHandler`), a odnośniki zewnętrzne
  kieruj do przeglądarki systemowej przez `shell.openExternal` po walidacji adresu.
- Utrzymuj responsywność procesu głównego: żadnych ciężkich obliczeń ani synchronicznego IO w jego
  pętli zdarzeń, ponieważ zawieszenie procesu głównego zamraża wszystkie okna aplikacji.
- Obsługuj cykl życia zgodnie z platformą: na macOS aplikacja działa po zamknięciu okien (zdarzenie
  `activate` odtwarza okno), na pozostałych platformach `window-all-closed` kończy aplikację.

Wzorzec kompletnego toru IPC:

```js
// src/main/index.js — okno z pełną izolacją, ścieżki od __dirname
const window = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, "../preload/index.js"),
  },
});

// src/main/ipc/notes.js — walidacja wejścia w procesie głównym
ipcMain.handle("notes:read", async (_event, noteId) => {
  if (typeof noteId !== "string" || !/^[a-z0-9-]+$/.test(noteId)) {
    throw new Error("Niepoprawny identyfikator notatki");
  }
  return readNoteFromUserData(noteId); // ścieżka budowana wewnątrz userData
});
```

```js
// src/preload/index.js — wąskie API o stałych kanałach, nic ponad to
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  readNote: (noteId) => ipcRenderer.invoke("notes:read", noteId),
  onNoteChanged: (callback) =>
    ipcRenderer.on("notes:changed", (_event, note) => callback(note)),
});
```

## Konfiguracja i sekrety

- Konfigurację użytkownika zapisuj w katalogu `app.getPath("userData")`; nigdy w katalogu instalacji
  aplikacji, który bywa tylko do odczytu.
- Sekrety użytkownika (tokeny, hasła) przechowuj przez `safeStorage` (szyfrowanie magazynem
  systemowym), nie w plikach jawnych ani w `localStorage` renderera.
- Pamiętaj, że pakiet aplikacji (asar) jest jawny — każdy wpisany w kod sekret zostanie wydobyty.
  Klucze usługowe trzymaj po stronie serwera; aplikacja desktopowa uwierzytelnia się tokenami
  użytkownika.
- Nie commituj: certyfikatów i profilów podpisywania kodu, haseł do nich, plików `.env`, katalogów
  `dist/` i `node_modules/`. Sekrety podpisywania podawaj w potoku CI przez zmienne środowiskowe.
- Konfigurację `electron-builder` trzymaj w `electron-builder.yml` (lub polu `build` w
  `package.json`): identyfikator `appId`, cele platform, wzorce `files` ograniczające zawartość
  pakietu, zasoby instalatora. Nie pakuj plików źródłowych, testów ani sekretów — kontroluj wzorce
  `files`.

Minimalny szkielet `electron-builder.yml`:

```yaml
appId: pl.danaco.example-app
files:
  - "dist/**"          # wyłącznie artefakty builda
  - "package.json"
directories:
  output: release
mac:
  target: dmg
win:
  target: nsis
linux:
  target: AppImage
```

## Testy

- Wydzielaj logikę z procedur obsługi IPC do czystych modułów i testuj je jednostkowo w Vitest lub
  `node:test`, bez uruchamiania Electron.
- Testy end-to-end prowadź w Playwright, który wspiera Electron przez `_electron.launch`: uruchamia
  aplikację, daje dostęp do okien i pozwala wykonywać kod w procesie głównym. Traktuj to wsparcie
  jako eksperymentalne i utrzymuj testy odporne na drobne zmiany.
- Interfejs renderera testuj jak zwykłą aplikację przeglądarkową (React Testing Library itp.) z
  podmienionym API mostu preload — testy komponentów nie wymagają Electron.
- Testuj kontrakt IPC: dla każdego kanału sprawdź odrzucanie niepoprawnych argumentów, nie tylko
  ścieżkę poprawną.
- Weryfikuj build spakowany (`electron-builder`) na docelowych platformach przed wydaniem; różnice
  ścieżek (asar, zasoby) ujawniają się dopiero w pakiecie, nie w trybie deweloperskim.

## Diagnostyka

- Rozróżniaj dzienniki dwóch światów: błędy procesu głównego trafiają do terminala, z którego
  uruchomiono aplikację; błędy renderera — do DevTools danego okna (`webContents.openDevTools`, w
  trybie deweloperskim także skrótem klawiszowym). Szukaj komunikatu we właściwym procesie.
- W aplikacji spakowanej terminal nie jest widoczny — zapisuj dziennik procesu głównego do pliku w
  `userData` (np. pakietem electron-log lub własnym zapisem), inaczej awarie u użytkowników będą
  niediagnozowalne.
- Białe okno po starcie oznacza zwykle błąd ładowania (`did-fail-load`), wyjątek w preload lub złą
  ścieżkę w `loadFile`/`loadURL` — sprawdź konsolę DevTools i zdarzenia `webContents`.
- Komunikat o niezdefiniowanym API mostu w rendererze wskazuje, że preload nie został załadowany
  (błędna ścieżka w `webPreferences.preload`, wyjątek podczas jego wykonania) albo nazwa w
  `exposeInMainWorld` nie zgadza się z użyciem.
- Błąd „An object could not be cloned” przy IPC oznacza przekazanie wartości niepodlegającej
  algorytmowi structured clone (funkcja, klasa, uchwyt) — przez IPC przesyłaj wyłącznie dane
  serializowalne.
- Zamrożony interfejs wszystkich okien to objaw zablokowanego procesu głównego; szukaj
  synchronicznego IO lub długich obliczeń w procedurach `ipcMain`.

## Typowe błędy modeli LLM w tym frameworku

1. **`nodeIntegration: true` lub `contextIsolation: false` „aby zadziałało”.** Daje stronie w
   rendererze pełny dostęp do Node — każda podatność XSS staje się zdalnym wykonaniem kodu na
   maszynie użytkownika. Zamiast osłabiać izolację, udostępnij potrzebną funkcję przez preload i
   `contextBridge`.
2. **Eksponowanie całego `ipcRenderer` przez most.** `contextBridge.exposeInMainWorld(„api”, {
   ipcRenderer })` niweczy izolację, bo renderer może wysyłać dowolne kanały. Udostępniaj funkcje o
   stałych kanałach: `getUser: () => ipcRenderer.invoke("user:get")`.
3. **`require` lub importy Node w kodzie renderera.** Przy poprawnej izolacji kod taki po prostu nie
   działa (`require is not defined`), a modele „naprawiają” go włączeniem `nodeIntegration`. Dostęp
   do systemu przenieś do procesu głównego i wywołuj przez IPC.
4. **Ładowanie zdalnych treści w oknie z uprawnieniami.** `loadURL` na adres zewnętrzny w oknie z
   mostem IPC oddaje obcemu serwerowi API aplikacji. Zdalne treści wyłącznie w oknie odizolowanym,
   bez preload z uprawnieniami, z zablokowaną nawigacją.
5. **Procedury IPC ufające argumentom renderera.** Obsługa `file:read` przyjmująca dowolną ścieżkę
   umożliwia odczyt całego dysku po kompromitacji renderera. Waliduj i ograniczaj argumenty w
   procesie głównym (np. ścieżki wyłącznie wewnątrz `userData`).
6. **Blokowanie procesu głównego.** Synchroniczne `fs.*Sync`, `execSync` lub długie pętle w
   procedurach `ipcMain` zamrażają wszystkie okna. Używaj wariantów asynchronicznych, a obliczenia
   przenoś do `utilityProcess` lub wątków roboczych.
7. **Użycie przestarzałych wzorców: moduł `remote`, `sendSync`, wyłączony `sandbox` bez powodu.**
   Moduł `remote` został usunięty z rdzenia Electron, a `sendSync` blokuje renderer. Stosuj
   `invoke`/`handle` i utrzymuj piaskownicę włączoną.
8. **Ścieżki liczone względem katalogu roboczego.** `loadFile("renderer/index.html")` działa w
   trybie deweloperskim, a zawodzi w pakiecie asar. Buduj ścieżki od `__dirname` lub
   `app.getAppPath()` i weryfikuj w buildzie spakowanym.
9. **Sekrety wkompilowane w aplikację.** Klucz API wpisany w kod procesu głównego jest do odczytania
   z pakietu przez każdego użytkownika. Sekrety usługowe trzymaj na serwerze; dane użytkownika
   szyfruj przez `safeStorage`.
10. **Pomijanie różnic platformowych cyklu życia i pakowania.** Kod zakładający zachowanie jednej
    platformy (zamknięcie aplikacji z ostatnim oknem, format ikon, elevacja instalatora) zawodzi na
    pozostałych. Obsłuż `darwin` odrębnie i konfiguruj cele `electron-builder` per platforma.
