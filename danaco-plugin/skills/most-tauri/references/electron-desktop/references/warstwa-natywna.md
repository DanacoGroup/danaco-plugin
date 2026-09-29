# Warstwa natywna

Odniesienie: Electron 43.2.0. Wszystko poniżej żyje w **procesie głównym** i jest
wywoływane z renderera przez IPC (patrz `references/electron-desktop/references/ipc-i-preload.md`).

## System plików

Renderer nigdy nie dotyka dysku. Proces główny robi to za niego, po walidacji ścieżki.

```ts
import { app, dialog, BrowserWindow } from 'electron';
import fs from 'node:fs/promises';
import path from 'node:path';

// Katalogi standardowe — nie wymyślaj własnych.
const KATALOGI = {
  dane: app.getPath('userData'),      // ~/Library/Application Support/<Nazwa>, %APPDATA%\<Nazwa>, ~/.config/<Nazwa>
  logi: app.getPath('logs'),          // ~/Library/Logs/<Nazwa>, %APPDATA%\<Nazwa>\logs, ~/.config/<Nazwa>/logs
  cache: app.getPath('cache'),
  temp: app.getPath('temp'),
  dokumenty: app.getPath('documents'),
  pobrane: app.getPath('downloads'),
  pulpit: app.getPath('desktop'),
  home: app.getPath('home'),
  awarie: app.getPath('crashDumps'),
};
```

**Zapis atomowy** — obowiązkowy dla wszystkiego, co użytkownik uzna za swoje dane.
Przerwanie zapisu (padnięcie prądu, kill) na zwykłym `writeFile` zostawia obcięty plik.

```ts
export async function zapiszAtomowo(cel: string, dane: string | Uint8Array): Promise<void> {
  const tymczasowy = `${cel}.${process.pid}.tmp`;
  const uchwyt = await fs.open(tymczasowy, 'w');
  try {
    await uchwyt.writeFile(dane);
    await uchwyt.sync();               // wymusza zrzut na dysk przed rename
  } finally {
    await uchwyt.close();
  }
  await fs.rename(tymczasowy, cel);    // rename na tym samym woluminie jest atomowy
}
```

`fs.rename` jest atomowy tylko w obrębie jednego systemu plików — plik tymczasowy twórz
w katalogu docelowym, nie w `os.tmpdir()`.

**Obserwacja zmian:** `fs.watch` na macOS gubi zdarzenia przy szybkich zmianach i nie
działa rekurencyjnie na Linuksie. Do obserwacji katalogu użytkownika użyj `chokidar`
z `awaitWriteFinish` — inaczej dostaniesz zdarzenie na w połowie zapisanym pliku.

## Dialogi

```ts
const wynik = await dialog.showOpenDialog(okno, {
  title: 'Wybierz dokumenty',
  defaultPath: ustawienia.get('ostatniKatalog') ?? app.getPath('documents'),
  buttonLabel: 'Otwórz',
  filters: [
    { name: 'Dokumenty', extensions: ['pdf', 'docx', 'odt'] },
    { name: 'Wszystkie pliki', extensions: ['*'] },
  ],
  properties: ['openFile', 'multiSelections'],
});
if (!wynik.canceled && wynik.filePaths.length > 0) {
  ustawienia.set('ostatniKatalog', path.dirname(wynik.filePaths[0]));
}
```

**Zmiana w E43:** dialogi domyślnie otwierają katalog Pobrane zamiast pamiętać ostatnio
używany. Jeśli chcesz starego zachowania — zapisuj `path.dirname` wyniku i podawaj jako
`defaultPath`, jak wyżej. Bez tego użytkownicy zgłoszą regresję po aktualizacji.

**Zmiana w E43, Linux:** własność `showHiddenFiles` została usunięta (GTK wycofało API).

Dialog z rodzicem (`dialog.showOpenDialog(okno, ...)`) jest modalny wobec okna; bez
rodzica jest modalny wobec aplikacji na macOS i niemodalny na Windows. Zawsze podawaj
rodzica.

```ts
// pytanie tak/nie z domyślną i anulującą odpowiedzią
const { response } = await dialog.showMessageBox(okno, {
  type: 'warning',
  buttons: ['Zapisz', 'Nie zapisuj', 'Anuluj'],
  defaultId: 0,
  cancelId: 2,
  message: 'Dokument ma niezapisane zmiany.',
  detail: 'Zamknięcie bez zapisu spowoduje ich utratę.',
  noLink: true,          // Windows: bez tego przyciski renderują się jako "command links"
});
```

`cancelId` jest istotne: bez niego zamknięcie dialogu Escape'em zwraca `0`, czyli
u ciebie „Zapisz”.

## Menu i skróty

```ts
import { Menu, MenuItemConstructorOptions, app, shell } from 'electron';

const jestMac = process.platform === 'darwin';

const szablon: MenuItemConstructorOptions[] = [
  ...(jestMac ? [{
    label: app.name,
    submenu: [
      { role: 'about' as const, label: `O programie ${app.name}` },
      { type: 'separator' as const },
      { label: 'Ustawienia…', accelerator: 'Cmd+,', click: otworzUstawienia },
      { type: 'separator' as const },
      { role: 'services' as const }, { type: 'separator' as const },
      { role: 'hide' as const }, { role: 'hideOthers' as const }, { role: 'unhide' as const },
      { type: 'separator' as const }, { role: 'quit' as const, label: 'Zakończ' },
    ],
  }] : []),
  {
    label: 'Plik',
    submenu: [
      { label: 'Nowy', accelerator: 'CmdOrCtrl+N', click: nowyDokument },
      { label: 'Otwórz…', accelerator: 'CmdOrCtrl+O', click: otworzDokument },
      { label: 'Zapisz', accelerator: 'CmdOrCtrl+S', click: zapiszDokument },
      { type: 'separator' },
      jestMac ? { role: 'close', label: 'Zamknij okno' } : { role: 'quit', label: 'Zakończ' },
    ],
  },
  { label: 'Edycja', role: 'editMenu' },
  { label: 'Widok', role: 'viewMenu' },
  { label: 'Okno', role: 'windowMenu' },
  {
    label: 'Pomoc',
    role: 'help',
    submenu: [{ label: 'Dokumentacja', click: () => shell.openExternal('https://...') }],
  },
];

Menu.setApplicationMenu(Menu.buildFromTemplate(szablon));
```

**Na macOS pasek menu jest obowiązkowy.** Bez `editMenu` przestają działać Cmd+C/V
w polach tekstowych — to jest najczęstszy błąd zgłaszany jako „nie działa kopiowanie”.

**Jeśli nie chcesz menu w ogóle** (kiosk, narzędzie bez menu na Windows):
`Menu.setApplicationMenu(null)` **przed `app.whenReady()`** — wtedy Electron pomija
budowę menu domyślnego i start jest szybszy o kilkadziesiąt ms.

**Skróty globalne** (działają, gdy aplikacja nie ma fokusu) — używaj oszczędnie,
konflikty z innymi programami są niewidoczne dla użytkownika:

```ts
import { globalShortcut } from 'electron';

app.whenReady().then(() => {
  const zarejestrowano = globalShortcut.register('CommandOrControl+Shift+D', pokazSzybkieWejscie);
  if (!zarejestrowano) log.warn('Skrót globalny zajęty przez inny program');
});
app.on('will-quit', () => globalShortcut.unregisterAll());
```

Bez `unregisterAll` skrót zostaje zarezerwowany do restartu systemu na niektórych
środowiskach Linuksa.

**Menu kontekstowe** buduj w procesie głównym na żądanie z renderera, przekazując
kontekst (co kliknięto), a nie budując je w HTML — natywne menu wygląda właściwie
i obsługuje nawigację klawiaturą.

## Powiadomienia

```ts
import { Notification, app } from 'electron';

if (process.platform === 'win32') app.setAppUserModelId('pl.danaco.moja-aplikacja');

function powiadom(tytul: string, tresc: string) {
  if (!Notification.isSupported()) return;
  const n = new Notification({
    title: tytul,
    body: tresc,
    silent: false,
    urgency: 'normal',        // Linux: 'normal' | 'critical' | 'low'
  });
  n.on('click', () => { okno.show(); okno.focus(); });
  n.show();
}
```

**Zmiana w E42, macOS:** powiadomienia przeszły z `NSUserNotification` na `UNNotification`.
Konsekwencja: **aplikacja musi być podpisana kodem, żeby powiadomienia w ogóle działały** —
również w developmencie. Jeśli testujesz na macOS bez podpisu, `new Notification().show()`
nic nie zrobi i nie rzuci błędu. Podpisz ad-hoc (`codesign -s - Electron.app`) albo
testuj na Windows.

**Windows:** bez `setAppUserModelId` powiadomienia pokazują się jako „electron.app.Electron”
albo nie pokazują wcale. Wartość musi być zgodna z `appId` z konfiguracji builda.

## Schowek

```ts
import { clipboard, nativeImage } from 'electron';

clipboard.writeText('tekst');
clipboard.writeHTML('<b>tekst</b>');
clipboard.write({ text: 'tekst', html: '<b>tekst</b>' });   // kilka formatów naraz
const obraz = nativeImage.createFromPath('/tmp/zrzut.png');
clipboard.writeImage(obraz);
const zeSchowka = clipboard.readText();
```

**Zmiana w E44 (nadchodzi):** moduł `clipboard` **znika z renderera**. W rendererze zostaje
`navigator.clipboard` (asynchroniczne, wymaga uprawnienia `clipboard-read`), a operacje
wymagające formatów natywnych robisz w procesie głównym i wystawiasz przez preload.
Napisz tak od razu — kod działa w 41-43 i przeżyje 44.

## Tray

```ts
import { Tray, Menu, nativeImage, app } from 'electron';
import path from 'node:path';

let tray: Tray | null = null;

function utworzTray() {
  // macOS: ikona szablonowa (czarna z alfą, nazwa kończy się na Template) — sama
  // dostosuje się do jasnego/ciemnego paska menu.
  const nazwa = process.platform === 'darwin' ? 'trayTemplate.png' : 'tray.png';
  const ikona = nativeImage.createFromPath(path.join(process.resourcesPath, 'assets', nazwa));
  if (process.platform === 'darwin') ikona.setTemplateImage(true);

  tray = new Tray(ikona.resize({ width: 16, height: 16 }));
  tray.setToolTip('Moja Aplikacja');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Pokaż okno', click: () => { okno.show(); okno.focus(); } },
    { type: 'separator' },
    { label: 'Zakończ', click: () => { aplikacjaSieZamyka = true; app.quit(); } },
  ]));
  // Windows/Linux: kliknięcie lewym pokazuje okno; macOS: pokazuje menu
  tray.on('click', () => { if (process.platform !== 'darwin') okno.show(); });
}
```

**`tray` musi być trzymany w zmiennej o zasięgu modułu.** Zmienna lokalna zostanie
zebrana przez GC i ikona zniknie po kilkudziesięciu sekundach — to jest klasyczny
„ikona znika po minucie”.

**Rozmiary ikon:** macOS 16×16 pt (dostarcz `@2x`), Windows 16×16 z `.ico` zawierającym
warianty do 32×32, Linux 22×22 albo 24×24. Nie skaluj w locie dużej ikony — będzie
rozmyta na pasku.

**Linux:** obszar powiadomień zależy od środowiska. GNOME nie ma go od wersji 3.26 —
wymaga rozszerzenia AppIndicator. Zakładaj, że tray na Linuksie może po prostu nie
istnieć, i nie umieszczaj tam jedynego dostępu do funkcji.

## Protokół własny `myapp://`

Dwie rzeczy pod tą samą nazwą — nie myl ich:

**(A) Rejestracja w systemie**, żeby kliknięcie `myapp://cos` w przeglądarce uruchamiało
twoją aplikację:

```ts
// przed whenReady
if (process.defaultApp) {
  // tryb deweloperski: electron . -> trzeba podać ścieżkę
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('myapp', process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient('myapp');
}

// macOS: przychodzi jako zdarzenie
app.on('open-url', (event, url) => { event.preventDefault(); obsluzGlebokiLink(url); });

// Windows/Linux: przychodzi w argv drugiej instancji
app.on('second-instance', (_e, argv) => {
  const url = argv.find((a) => a.startsWith('myapp://'));
  if (url) obsluzGlebokiLink(url);
});
// oraz w argv pierwszej instancji przy zimnym starcie
const startowyUrl = process.argv.find((a) => a.startsWith('myapp://'));
```

Na macOS schemat musi być dodatkowo zadeklarowany w `Info.plist` (`CFBundleURLTypes`) —
Forge: `packagerConfig.protocols`, electron-builder: `mac.protocols`.

```ts
// forge.config.ts
packagerConfig: {
  protocols: [{ name: 'Moja Aplikacja', schemes: ['myapp'] }],
}
```

**Walidacja głębokiego linku jest obowiązkowa.** Link przychodzi z zewnątrz — z przeglądarki,
z maila, od kogokolwiek. Traktuj go jak dane niezaufane: parsuj przez `new URL`, sprawdzaj
`host` i ścieżkę wobec listy dozwolonej, nigdy nie przekazuj do `shell.openExternal`,
`fs` ani `eval`.

**(B) Serwowanie własnych zasobów** zamiast `file://` — zalecenie #18 z listy bezpieczeństwa:

```ts
// przed whenReady
protocol.registerSchemesAsPrivileged([{
  scheme: 'app',
  privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true, corsEnabled: true },
}]);

// po whenReady
protocol.handle('app', async (request) => {
  const url = new URL(request.url);            // app://local/index.html
  const wzgledna = path.normalize(url.pathname).replace(/^(\.\.[/\\])+/, '');
  const plik = path.join(KATALOG_RENDERERA, wzgledna);
  if (!plik.startsWith(KATALOG_RENDERERA)) return new Response('403', { status: 403 });
  return net.fetch(pathToFileURL(plik).toString());
});

okno.loadURL('app://local/index.html');
```

Zysk: origin jest stabilny (`app://local`), więc `localStorage`, IndexedDB i cookies
działają normalnie; CSP i CORS zachowują się jak w sieci; możesz wyłączyć fuse
`grantFileProtocolExtraPrivileges`. `protocol.registerFileProtocol` i pokrewne są
przestarzałe od E25 — używaj `protocol.handle`.

## Rejestracja typów plików

```ts
// forge.config.ts — macOS
packagerConfig: {
  extendInfo: {
    CFBundleDocumentTypes: [{
      CFBundleTypeName: 'Dokument DANACO',
      CFBundleTypeRole: 'Editor',
      LSHandlerRank: 'Owner',
      LSItemContentTypes: ['pl.danaco.dokument'],
    }],
    UTExportedTypeDeclarations: [{
      UTTypeIdentifier: 'pl.danaco.dokument',
      UTTypeConformsTo: ['public.data'],
      UTTypeDescription: 'Dokument DANACO',
      UTTypeTagSpecification: { 'public.filename-extension': ['dnc'] },
    }],
  },
}
```

```yaml
# electron-builder.yml — Windows i macOS w jednym miejscu
fileAssociations:
  - ext: dnc
    name: Dokument DANACO
    description: Dokument DANACO
    icon: build/dokument.ico
    role: Editor
```

Odbiór otwieranego pliku:

```ts
// macOS
app.on('open-file', (event, sciezka) => { event.preventDefault(); otworz(sciezka); });
// Windows/Linux: ścieżka w argv (pierwsza instancja) albo w second-instance
```

Na Windows Squirrel dodatkowo wymaga obsługi zdarzeń instalatora
(`--squirrel-install`, `--squirrel-updated`, `--squirrel-uninstall`) do rejestracji
skojarzeń — `electron-squirrel-startup` robi to za ciebie, ale tylko dla skrótów;
skojarzenia plików w Squirrelu wymagają własnego kodu. **Z NSIS-em (electron-builder)
to działa deklaratywnie i jest jednym z powodów, żeby wybrać NSIS zamiast Squirrela.**

## Autostart

```ts
app.setLoginItemSettings({
  openAtLogin: true,
  openAsHidden: true,                        // macOS: start bez pokazywania okna
  args: ['--autostart'],                     // Windows: rozpoznaj tryb w argv
  path: process.execPath,                    // Windows
});

const { openAtLogin } = app.getLoginItemSettings();
```

Ograniczenia:
- **macOS z App Sandbox / MAS:** `setLoginItemSettings` nie działa; potrzebny helper
  aplikacji z `SMAppService`. Poza MAS działa normalnie.
- **Linux:** Electron nie ma natywnego wsparcia — zapisz plik `.desktop` do
  `~/.config/autostart/` sam.
- **Windows:** wpis idzie do `HKCU\...\Run`. Instalatory MSI/NSIS mogą chcieć wpisu
  systemowego — wtedy rób to w instalatorze, nie w kodzie.

Rozpoznanie startu automatycznego (żeby nie pokazywać okna):

```ts
const wystartowanoAutomatycznie =
  process.argv.includes('--autostart') || app.getLoginItemSettings().wasOpenedAtLogin;
```

## Uprawnienia macOS (TCC)

TCC (Transparency, Consent and Control) pyta użytkownika przy pierwszym użyciu zasobu.
Bez odpowiedniego opisu w `Info.plist` aplikacja **wywala się w momencie żądania**,
bez dialogu.

| Zasób | Klucz w `Info.plist` | Entitlement (hardened runtime) |
| --- | --- | --- |
| kamera | `NSCameraUsageDescription` | `com.apple.security.device.camera` |
| mikrofon | `NSMicrophoneUsageDescription` | `com.apple.security.device.audio-input` |
| lokalizacja | `NSLocationUsageDescription` | — |
| kontakty/kalendarz | `NSContactsUsageDescription` itd. | `com.apple.security.personal-information.*` |
| nagrywanie ekranu | — (systemowe okno ustawień) | — |
| dostępność (symulacja klawiatury) | — (systemowe okno ustawień) | — |
| pliki Pulpit/Dokumenty/Pobrane | `NSDesktopFolderUsageDescription` itd. | `com.apple.security.files.user-selected.read-write` |

```ts
packagerConfig: {
  extendInfo: {
    NSCameraUsageDescription: 'Skanowanie kodów kreskowych z dokumentów.',
    NSMicrophoneUsageDescription: 'Dyktowanie notatek do sprawy.',
  },
}
```

Opis musi mówić **po co**, konkretnie. Apple odrzuca notaryzację i recenzję MAS przy
opisach typu „Aplikacja potrzebuje dostępu”.

Sprawdzenie stanu bez wywoływania dialogu:

```ts
import { systemPreferences } from 'electron';
const stan = systemPreferences.getMediaAccessStatus('camera');  // 'not-determined'|'granted'|'denied'|'restricted'
if (stan === 'not-determined') await systemPreferences.askForMediaAccess('camera');
if (stan === 'denied') pokazInstrukcjeJakWlaczyc();   // nie da się poprosić ponownie
```

**`denied` jest ostateczne** — system nie pokaże dialogu drugi raz. Jedyne wyjście to
instrukcja „Ustawienia systemowe → Prywatność → Kamera”.

## Moduły natywne i ABI

Electron ma **inne ABI Node niż samo Node**. Moduł skompilowany dla Node 24 nie załaduje
się w Electronie 43, mimo że Electron 43 ma Node 24.18.0 — bo Electron używa własnego
V8 i własnego `NODE_MODULE_VERSION`.

| Electron | Node | `process.versions.modules` (ABI) |
| --- | --- | --- |
| 43.x | 24.18.0 | 148 |
| 42.x | 24.18.0 | 146 |
| 41.x | 24.14+ | 145 |
| 40.x | 24.11.1 | 143 |
| 39.x | 22.20.0 | 140 |

Objaw pominięcia rebuildu:
```
Error: The module '.../better_sqlite3.node' was compiled against a different
Node.js version using NODE_MODULE_VERSION 137. This version of Node.js requires
NODE_MODULE_VERSION 148.
```

### Trzy sposoby, w kolejności preferencji

**1. N-API / node-addon-api.** Moduł zbudowany na N-API jest stabilny między wersjami ABI
i **nie wymaga rebuildu**. Przy wyborze biblioteki sprawdź, czy używa N-API — to główne
kryterium. `better-sqlite3` używa N-API od wersji 9, ale nadal potrzebuje prebuildu pod
konkretną platformę i wersję N-API.

**2. Prebuildy.** `prebuild-install` / `node-gyp-build` pobierają gotowy binarny artefakt.
Ustaw `npm_config_runtime=electron` i `npm_config_target=43.2.0`, żeby pobrał wariant
dla Electrona.

**3. Rebuild lokalny przez `@electron/rebuild`** (4.2.0):

```bash
npx electron-rebuild -f -w better-sqlite3
# albo dla wszystkich modułów natywnych w projekcie:
npx electron-rebuild
```

W Forge robi to automatycznie przy `npm start` i `npm run package`.
W electron-builder robi to hook `app-builder` (`npmRebuild: true`, domyślnie włączone).
`electron-vite` **nie robi tego sam** — dodaj skrypt `postinstall`:

```json
{ "scripts": { "postinstall": "electron-builder install-app-deps" } }
```

### Wymagania `node-gyp`

Rebuild kompiluje C++ lokalnie. Bez toolchainu dostaniesz błąd w CI, którego nie widziałeś
na swojej maszynie.

| System | Wymagane |
| --- | --- |
| Windows | Visual Studio Build Tools z „Desktop development with C++”, Python 3.9+ |
| macOS | Xcode Command Line Tools (`xcode-select --install`), Python 3.9+ |
| Linux | `build-essential`, `python3`, dla niektórych modułów `libsecret-1-dev` |

Na GitHub Actions runnery `windows-latest`, `macos-latest` i `ubuntu-latest` mają to
domyślnie — poza `libsecret-1-dev`, które trzeba doinstalować.

### `better-sqlite3` — pełny przypadek

```bash
npm install better-sqlite3
npm install --save-dev @electron/rebuild
npx electron-rebuild -f -w better-sqlite3
```

```ts
// src/main/baza.ts — TYLKO w procesie głównym albo utility process
import Database from 'better-sqlite3';
import path from 'node:path';
import { app } from 'electron';

const db = new Database(path.join(app.getPath('userData'), 'dane.db'));
db.pragma('journal_mode = WAL');       // równoległy odczyt podczas zapisu
db.pragma('synchronous = NORMAL');     // kompromis trwałość/szybkość dla WAL
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS dokument (
    id INTEGER PRIMARY KEY,
    tytul TEXT NOT NULL,
    utworzono INTEGER NOT NULL DEFAULT (unixepoch())
  );
`);

const wstaw = db.prepare('INSERT INTO dokument (tytul) VALUES (?)');
const wstawWiele = db.transaction((tytuly: string[]) => {
  for (const t of tytuly) wstaw.run(t);
});
```

**`better-sqlite3` jest synchroniczny.** Zapytanie zwracające 50 tys. wierszy zablokuje
proces główny na kilkaset ms i UI zamarznie. Trzy wyjścia: (a) trzymaj bazę w
`utilityProcess` i komunikuj się przez `MessagePort`; (b) trzymaj w worker threadzie;
(c) paginuj bezwzględnie każde zapytanie. Dla aplikacji z realną bazą wybierz (a).

**Pakowanie:** plik `.node` musi być rozpakowany z ASAR-a, bo `dlopen` nie czyta z archiwum.

```ts
// forge.config.ts
packagerConfig: { asar: { unpack: '**/*.node' } }
// albo wygodniej:
plugins: [ new AutoUnpackNativesPlugin({}) ]   // @electron-forge/plugin-auto-unpack-natives
```

```yaml
# electron-builder.yml
asarUnpack: ['**/*.node']
```

Po rozpakowaniu ścieżka w runtime zawiera `app.asar.unpacked` — biblioteki robią to
przezroczyście, ale jeśli sam liczysz ścieżkę:

```ts
const sciezka = __dirname.replace('app.asar', 'app.asar.unpacked');
```

### Alternatywy bez kompilacji

| Potrzeba | Moduł natywny | Alternatywa bez natywnego kodu |
| --- | --- | --- |
| SQLite | `better-sqlite3` | `node:sqlite` (wbudowany w Node 22+; w Electronie 41+ dostępny, ale API jeszcze eksperymentalne) — `[niepotwierdzone: stabilność node:sqlite w Electron 43]` |
| Hasła/tokeny | `keytar` (porzucony) | `safeStorage` (wbudowany) |
| Kompresja | `node-7z` | `node:zlib` |
| Obrazy | `sharp` | `nativeImage` do prostych operacji, `canvas` w rendererze |

Każdy usunięty moduł natywny to jedna platforma mniej do debugowania w CI i brak
problemu ABI przy podniesieniu Electrona.
