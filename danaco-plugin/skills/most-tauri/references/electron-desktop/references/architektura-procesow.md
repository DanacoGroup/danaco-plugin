# Architektura procesów Electrona

Odniesienie: Electron 43.2.0 (Chromium 150, Node 24.18.0). Zachowania oznaczone wersją
tam, gdzie różnią się między 41 a 43.

## Cztery rodzaje procesów

| Proces | Środowisko | Ile ich jest | Co tu należy | Czego tu nie wolno |
| --- | --- | --- | --- | --- |
| główny (main) | Node.js, pełne API systemu | dokładnie jeden | cykl życia aplikacji, okna, menu, tray, dialogi, dostęp do dysku, sieć uprzywilejowana | ciężkie obliczenia, synchroniczne I/O, parsowanie dużych plików |
| renderer | Chromium, bez Node (domyślnie) | jeden na `WebContents` | interfejs, logika prezentacji, `fetch` do własnego API | dostęp do systemu plików, `require`, klucze |
| preload | most; ma `require` do wbudowanych modułów Electrona, gdy `sandbox: true` | jeden na renderer | `contextBridge`, wąskie API dla okna | logika biznesowa, sekrety, długie operacje |
| utility | Node.js, osobny proces potomny | ile chcesz | CPU-bound, parsery, niepewny kod stron trzecich, moduły natywne, które lubią się wywalać | UI, `BrowserWindow` |

`utilityProcess` różni się od `child_process.fork` jednym: potrafi dostać `MessagePort`
połączony bezpośrednio z rendererem, więc dane nie przechodzą przez proces główny.

```ts
// main.ts — utility process do parsowania dużego PDF-a
import { utilityProcess, MessageChannelMain, app } from 'electron';
import path from 'node:path';

function uruchomParser() {
  const child = utilityProcess.fork(path.join(__dirname, 'parser.js'), [], {
    serviceName: 'parser-dokumentow',
    stdio: 'pipe',
  });
  child.stdout?.on('data', (d) => console.log('[parser]', d.toString()));
  child.on('exit', (code) => {
    if (code !== 0 && !app.isQuittingForUpdate) uruchomParser();  // restart po awarii
  });
  return child;
}

// bezpośredni kanał renderer <-> utility, z pominięciem main
function polaczZRendererem(child: Electron.UtilityProcess, wc: Electron.WebContents) {
  const { port1, port2 } = new MessageChannelMain();
  child.postMessage({ typ: 'port-renderera' }, [port1]);
  wc.postMessage('port-parsera', null, [port2]);
}
```

**Kiedy utility, a kiedy worker thread:** worker thread dzieli przestrzeń adresową z
procesem, który go stworzył — awaria modułu natywnego zabija cały proces. Utility process
ma własną przestrzeń; awaria to `exit` z kodem, który obsłużysz. Dla `better-sqlite3`
w trybie tylko-do-odczytu worker wystarcza; dla parsowania obcych plików (PDF, DOCX,
archiwa) użyj utility.

## Cykl życia aplikacji

```ts
import { app, BrowserWindow } from 'electron';

// 1. Blokada drugiej instancji MUSI być przed whenReady.
const mamyBlokade = app.requestSingleInstanceLock();
if (!mamyBlokade) {
  app.quit();       // druga instancja kończy się natychmiast
} else {
  app.on('second-instance', (_e, argv, _cwd) => {
    // przyszedł drugi start (np. użytkownik kliknął plik) — obsłuż argv i podnieś okno
    const okno = BrowserWindow.getAllWindows()[0];
    if (okno) {
      if (okno.isMinimized()) okno.restore();
      okno.focus();
    }
  });

  app.whenReady().then(() => {
    utworzOkno();
    app.on('activate', () => {
      // macOS: kliknięcie w dock przy zamkniętych oknach
      if (BrowserWindow.getAllWindows().length === 0) utworzOkno();
    });
  });
}

app.on('window-all-closed', () => {
  // macOS: aplikacja żyje bez okien. Windows/Linux: kończymy.
  if (process.platform !== 'darwin') app.quit();
});
```

Kolejność zdarzeń przy zamykaniu — ważna, bo tu ludzie gubią dane:

1. `app.quit()` albo zamknięcie ostatniego okna →
2. `before-quit` (można `event.preventDefault()`) →
3. `close` na każdym oknie (można `preventDefault()`) →
4. `will-quit` (ostatni moment na **asynchroniczne** sprzątanie — trzymaj przez
   `event.preventDefault()` i wywołaj `app.exit()` sam) →
5. `quit`.

`app.exit(kod)` pomija całą tę kolejkę. Używaj tylko po awarii.

```ts
let mozeZamknac = false;

okno.on('close', (e) => {
  if (mozeZamknac) return;
  e.preventDefault();
  zapiszNiezapisane()                    // Promise
    .then(() => { mozeZamknac = true; okno.close(); })
    .catch(() => { /* pokaż dialog "zapisać?" */ });
});
```

**Pułapka:** `before-quit` nie odpala się przy wymuszonym wyłączeniu systemu ani przy
`app.relaunch()`+`app.exit()`. Do wyłączania systemu na Windows użyj zdarzenia `session-end`
na oknie; zapisz tam **synchronicznie**, bo system nie czeka.

## Tworzenie okna — wzorzec produkcyjny

```ts
import { BrowserWindow, shell, screen } from 'electron';
import path from 'node:path';

function utworzOkno() {
  const okno = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 940,
    minHeight: 600,
    show: false,                          // nie pokazuj pustego białego prostokąta
    backgroundColor: '#111213',           // widoczne zanim renderer namaluje pierwszą klatkę
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,             // domyślne od E12, wpisz jawnie
      sandbox: true,                      // domyślne od E20
      nodeIntegration: false,             // domyślne od E5
      webviewTag: false,
      spellcheck: true,
    },
  });

  okno.once('ready-to-show', () => okno.show());

  // linki zewnętrzne otwieraj w przeglądarce systemowej, nigdy w oknie aplikacji
  okno.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://')) shell.openExternal(url);
    return { action: 'deny' };
  });

  okno.loadFile(path.join(__dirname, '../renderer/index.html'));
  return okno;
}
```

`show: false` + `ready-to-show` to jedyny sposób na uniknięcie białego błysku. `paint`
i `did-finish-load` odpalają się za wcześnie albo za późno.

**Pozycja i rozmiar między uruchomieniami.** Zapisuj sam, do `userData`; pakiet
`electron-window-state` (5.0.3, ostatnie wydanie 2018) nie ma obsługi wielu ekranów po
zmianach w Chromium. Sprawdzaj, czy zapisane współrzędne mieszczą się w którymś z
aktualnych ekranów:

```ts
function bezpiecznaPozycja(zapis: { x: number; y: number; width: number; height: number }) {
  const pasuje = screen.getAllDisplays().some((d) => {
    const b = d.workArea;
    return zapis.x >= b.x && zapis.y >= b.y &&
           zapis.x + zapis.width <= b.x + b.width &&
           zapis.y + zapis.height <= b.y + b.height;
  });
  return pasuje ? zapis : { width: zapis.width, height: zapis.height };  // bez x/y = wycentruj
}
```

## Model wielookienny

Trzy warianty, w kolejności rosnącej złożoności:

**1. Jedno okno, routing wewnątrz renderera.** Domyślny wybór. Okna modalne to dialogi
HTML. Jedna sesja, jedna instancja stanu.

**2. Wiele niezależnych okien tego samego typu** (edytor z wieloma dokumentami). Trzymaj
mapę `Map<numer, BrowserWindow>` w procesie głównym; identyfikuj okno po
`BrowserWindow.fromWebContents(event.sender)` w handlerach IPC, nie po globalnej zmiennej.

```ts
const okna = new Map<number, BrowserWindow>();
const sciezkiDokumentow = new Map<number, string>();

ipcMain.handle('dokument:zapisz', async (event, tresc: string) => {
  const okno = BrowserWindow.fromWebContents(event.sender);
  if (!okno) throw new Error('Brak okna źródłowego');
  const sciezka = sciezkiDokumentow.get(okno.id);
  if (!sciezka) throw new Error('Okno nie ma przypisanego dokumentu');
  await zapiszAtomowo(sciezka, tresc);
  okno.setDocumentEdited(false);        // macOS: kropka w przycisku zamknięcia
  return sciezka;
});
```

**3. Okno główne + okna pomocnicze różnego typu** (ustawienia, podgląd, „o programie”).
Okna pomocnicze twórz jako `parent: oknoGlowne` i `modal: true` tam, gdzie mają blokować.
Na macOS `modal` daje arkusz przyklejony do okna rodzica; na Windows blokuje rodzica.

**Okno rodzic-dziecko na `BaseWindow`.** Gdy jedno okno ma zawierać kilka niezależnych `WebContents`
(pasek narzędzi + treść, karty), nie używaj kilku `BrowserWindow` — użyj `BaseWindow` z
`WebContentsView`. Szczegóły w `references/electron-desktop/references/przegladarka-i-osadzanie.md`.

```ts
import { BaseWindow, WebContentsView } from 'electron';

const okno = new BaseWindow({ width: 1200, height: 800 });

const pasek = new WebContentsView({ webPreferences: { preload: preloadPaska } });
const tresc = new WebContentsView({ webPreferences: { preload: preloadTresci } });
okno.contentView.addChildView(pasek);
okno.contentView.addChildView(tresc);

function ulozenie() {
  const { width, height } = okno.getContentBounds();
  pasek.setBounds({ x: 0, y: 0, width, height: 48 });
  tresc.setBounds({ x: 0, y: 48, width, height: height - 48 });
}
okno.on('resize', ulozenie);
ulozenie();
```

`WebContentsView` **nie skaluje się sam** — musisz przeliczać `setBounds` przy każdym
`resize`. `BrowserView` miał `setAutoResize`; w `WebContentsView` tego nie ma i to jest
najczęstszy błąd przy migracji.

## Zachowanie per system

| Zachowanie | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Zamknięcie ostatniego okna | aplikacja **żyje** w docku | aplikacja kończy | aplikacja kończy |
| Menu aplikacji | globalny pasek u góry ekranu, wymagany | menu w oknie albo brak | zależy od środowiska; GNOME często ukrywa |
| Ikona w pasku zadań | dock; `app.dock.setBadge()`, `app.dock.bounce()` | tray + skoczna lista (`setJumpList`) | `Tray`, ale wsparcie zależy od DE (GNOME wymaga rozszerzenia) |
| Ramka okna | `titleBarStyle: 'hiddenInset'` daje natywne przyciski w treści | `titleBarOverlay` daje Window Controls Overlay | E43: bezramkowe okna mają domyślnie zaokrąglone rogi |
| Podwójne kliknięcie w pasek tytułu | zachowanie z ustawień systemu | maksymalizacja | zależy od DE |
| Powiadomienia | od E42 przez `UNNotification` — **wymagany podpis kodu** | Action Center; wymaga `app.setAppUserModelId()` | libnotify |

```ts
// macOS: ukrycie zamiast zamknięcia dla aplikacji rezydentnej
if (process.platform === 'darwin') {
  app.dock?.setBadge('3');
  okno.on('close', (e) => {
    if (!aplikacjaSieZamyka) { e.preventDefault(); okno.hide(); }
  });
}

// Windows: bez tego powiadomienia nie pokażą nazwy aplikacji
if (process.platform === 'win32') app.setAppUserModelId('pl.danaco.moja-aplikacja');
```

**Linux w E43:** `dialog.showOpenDialog` stracił `showHiddenFiles` (GTK usunęło API).
Bezramkowe okna dostały zaokrąglone rogi domyślnie — jeśli rysujesz własną ramkę,
sprawdź, czy nie masz teraz przezroczystych narożników.

## Stan i konfiguracja aplikacji

Trzy rozłączne rodzaje danych, trzy różne miejsca:

| Rodzaj | Gdzie | Czym | Czy przeżywa aktualizację |
| --- | --- | --- | --- |
| ustawienia użytkownika (motyw, język, ostatni katalog) | `app.getPath('userData')/config.json` | `electron-store` 11.x | tak, z migracją |
| dane robocze (baza, dokumenty, indeksy) | `app.getPath('userData')/dane/` | SQLite / pliki | tak, z wersją schematu |
| cache regenerowalny (miniatury, pobrane zasoby) | `app.getPath('cache')` albo `userData/cache` | cokolwiek | nie musi, kasowalne |

```ts
import Store from 'electron-store';

type Ustawienia = {
  motyw: 'jasny' | 'ciemny' | 'system';
  ostatniKatalog?: string;
  telemetria: boolean;
};

const ustawienia = new Store<Ustawienia>({
  name: 'ustawienia',
  defaults: { motyw: 'system', telemetria: false },
  schema: {
    motyw: { type: 'string', enum: ['jasny', 'ciemny', 'system'] },
    ostatniKatalog: { type: 'string' },
    telemetria: { type: 'boolean' },
  },
  migrations: {
    '2.0.0': (store) => {
      // do 1.x trzymaliśmy 'dark' zamiast 'ciemny'
      const stary = store.get('motyw') as string;
      if (stary === 'dark') store.set('motyw', 'ciemny');
    },
  },
});
```

`electron-store` zapisuje synchronicznie przy każdym `set`. Przy 20 zapisach na sekundę
(np. pozycja okna podczas przeciągania) zablokujesz proces główny — dławij zapisy
przez `debounce` 500 ms.

**Nie trzymaj stanu w zmiennych modułowych procesu głównego jako jedynego źródła prawdy.**
Proces główny nie restartuje się w dev-HMR, ale w produkcji restartuje przy aktualizacji;
stan, którego nie zapisałeś, ginie.

**Katalog `userData` domyślnie zależy od `app.getName()`**, czyli od `productName`
w `package.json`. Zmiana nazwy produktu między wersjami = użytkownik traci dane.
Jeśli musisz zmienić nazwę, ustaw jawnie `app.setPath('userData', staraScieżka)` przed
`whenReady` albo przenieś katalog przy pierwszym starcie.

## `app.whenReady` — co wolno przed, co po

**Przed `whenReady` (i tylko tam):**
- `app.requestSingleInstanceLock()`
- `app.setPath(...)`
- `app.commandLine.appendSwitch(...)`
- `app.setAsDefaultProtocolClient(...)` na Windows/Linux
- `Menu.setApplicationMenu(null)` — jeśli nie chcesz domyślnego menu, to oszczędza czas startu
- rejestracja `protocol.registerSchemesAsPrivileged(...)` — **musi** być przed ready

**Po `whenReady`:**
- `BrowserWindow`, `Tray`, `dialog`, `protocol.handle`, `session`, `nativeTheme`
- import modułów ESM w procesie głównym (Electron wymaga `whenReady` przed ładowaniem ESM)

```ts
// przed ready — inaczej custom protocol nie dostanie uprawnień
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true } },
]);
```

## ESM w procesie głównym

Wsparcie od `electron@28`. Wymaga `"type": "module"` w `package.json` albo rozszerzenia
`.mjs`. Trzy ograniczenia, które zaskakują:

1. **Preload w trybie sandbox nie może być ESM.** Sandboxowany preload jest ładowany
   syntetycznie i nie ma loadera ESM. Trzymaj preload jako CommonJS (`.cjs`) albo
   bunduj go do CJS — tak robi `@electron-forge/plugin-vite` domyślnie.
2. **Import ESM w main musi nastąpić po `app.whenReady()`** dla modułów, które dotykają
   API Electrona, bo `import` jest asynchroniczny i może wypaść po pierwszym tick-u pętli.
3. Wiele pakietów natywnych nadal jest CJS — działa przez interop, ale nazwane eksporty
   z CJS bywają niedostępne (`import { x } from 'pakiet-cjs'` się wywala,
   `import pakiet from 'pakiet-cjs'` działa).

Dla nowych projektów firmowych: **main i preload budowane do CJS**, renderer w ESM
(tak działa domyślny szablon `vite-typescript`). To eliminuje całą klasę problemów
i nic nie kosztuje, bo i tak przechodzisz przez bundler.

## Diagnostyka procesów

```ts
// lista procesów aplikacji z PID, typem i zużyciem CPU
const metryki = app.getAppMetrics();
// [{ pid, type: 'Browser'|'Tab'|'Utility'|'GPU', cpu: { percentCPUUsage }, memory: {...} }]

// awaria renderera — zawsze obsłuż, inaczej użytkownik widzi puste okno
okno.webContents.on('render-process-gone', (_e, szczegoly) => {
  // szczegoly.reason: 'crashed' | 'oom' | 'killed' | 'launch-failed' | ...
  zapiszDoLogu('renderer padł', szczegoly);
  if (szczegoly.reason !== 'clean-exit') okno.webContents.reload();
});

// zawieszony renderer (pętla w JS)
okno.webContents.on('unresponsive', () => pokazDialogCzekacCzyZabic(okno));
okno.webContents.on('responsive', () => zamknijDialog());

// awaria utility process
child.on('exit', (kod) => zapiszDoLogu('utility exit', kod));
```

`app.getAppMetrics()` to jedyny sposób, żeby zobaczyć wszystkie procesy z poziomu kodu —
w menedżerze zadań systemu wyglądają jak N kopii tej samej aplikacji bez rozróżnienia roli.
