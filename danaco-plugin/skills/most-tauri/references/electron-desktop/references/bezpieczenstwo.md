# Bezpieczeństwo Electrona — lista kontrolna

Odniesienie: Electron 43.2.0, oficjalna lista 20 zaleceń z `docs/tutorial/security`.
Kolumna „domyślne” mówi, co robi E43 bez twojej ingerencji — połowa listy sprowadza się
do „nie psuj domyślnych”.

## Tabela zbiorcza

| # | Zalecenie | Ustawienie | Domyślne w E43 | Co się stanie, jeśli złamiesz |
| --- | --- | --- | --- | --- |
| 1 | Tylko bezpieczne źródła | `https:`, `wss:` | — | MITM podmienia kod aplikacji |
| 2 | Bez Node dla zdalnych treści | `nodeIntegration: false` | `false` (od E5) | XSS = wykonanie poleceń systemowych |
| 3 | Izolacja kontekstu | `contextIsolation: true` | `true` (od E12) | strona nadpisuje funkcje preloadu i przechwytuje IPC |
| 4 | Sandbox renderera | `sandbox: true` | `true` (od E20) | ucieczka z renderera = pełne prawa procesu |
| 5 | Obsługa uprawnień | `setPermissionRequestHandler` | brak = wszystko dozwolone dla `file://` | strona włącza kamerę i mikrofon bez pytania |
| 6 | Nie wyłączaj `webSecurity` | `webSecurity: true` | `true` | znika CORS i same-origin policy |
| 7 | CSP | nagłówek albo `<meta>` | brak | wstrzyknięty skrypt ładuje kod z sieci |
| 8 | Bez mieszanej treści | `allowRunningInsecureContent: false` | `false` | HTTP-owy skrypt na stronie HTTPS |
| 9 | Bez funkcji eksperymentalnych | `experimentalFeatures: false` | `false` | niezaudytowane API Blinka |
| 10 | Bez `enableBlinkFeatures` | — | brak | jak wyżej |
| 11 | Bez `allowpopups` na `<webview>` | — | `false` | osadzona strona otwiera okna bez twojej kontroli |
| 12 | Weryfikacja `<webview>` | `will-attach-webview` | brak | strona osadza `<webview>` z własnym preloadem |
| 13 | Ograniczenie nawigacji | `will-navigate` | brak | strona nawiguje okno aplikacji na cudzy adres |
| 14 | Ograniczenie nowych okien | `setWindowOpenHandler` | otwiera `BrowserWindow` | `window.open` tworzy okno z twoim preloadem |
| 15 | `shell.openExternal` tylko z walidacją | — | — | `file:///`, `smb://`, schemat systemowy = wykonanie kodu |
| 16 | Aktualny Electron | — | — | znane CVE Chromium bez łatki |
| 17 | Walidacja nadawcy IPC | `event.senderFrame` | brak | podramka woła API systemowe |
| 18 | Unikaj `file://` | własny protokół | — | `file://` ma nadmiarowe przywileje |
| 19 | Fuses | `@electron/fuses` | patrz niżej | `ELECTRON_RUN_AS_NODE` zamienia aplikację w interpreter |
| 20 | Nie wystawiaj API Electrona | `contextBridge` | — | patrz `references/electron-desktop/references/ipc-i-preload.md` |

## `webPreferences` — jedyna dopuszczalna konfiguracja

```ts
const BEZPIECZNE: Electron.WebPreferences = {
  preload: path.join(__dirname, 'preload.js'),
  contextIsolation: true,
  sandbox: true,
  nodeIntegration: false,
  nodeIntegrationInWorker: false,
  nodeIntegrationInSubFrames: false,
  webSecurity: true,
  allowRunningInsecureContent: false,
  experimentalFeatures: false,
  webviewTag: false,
  enableWebSQL: false,
  spellcheck: true,
};
```

Każde odstępstwo wymaga komentarza z powodem i datą przeglądu. `sandbox: false` jest
jedynym, który czasem ma uzasadnienie — gdy preload musi używać modułu natywnego
(np. `keytar`, `better-sqlite3`) i nie da się tego przenieść do procesu głównego.
**Preferowane rozwiązanie: przenieś do procesu głównego i wystaw przez IPC**, wtedy
sandbox zostaje włączony.

## CSP

Nagłówek, nie `<meta>` — `<meta>` nie obejmuje workerów i jest podatny na wstrzyknięcie
przed nim. Ustawiaj w sesji, nie w HTML:

```ts
import { session } from 'electron';

app.whenReady().then(() => {
  session.defaultSession.webRequest.onHeadersReceived((szczegoly, callback) => {
    callback({
      responseHeaders: {
        ...szczegoly.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self';",
          "script-src 'self';",
          "style-src 'self' 'unsafe-inline';",   // wymagane dla stylów inline z bundlerów
          "img-src 'self' data: blob:;",
          "font-src 'self' data:;",
          "connect-src 'self' https://api.danacogroup.com.pl;",
          "object-src 'none';",
          "frame-src 'none';",
          "base-uri 'none';",
          "form-action 'none';",
        ].join(' '),
      },
    });
  });
});
```

**`'unsafe-eval'` jest zakazane.** Jeśli jakaś biblioteka go wymaga (stare wersje Vue
z kompilatorem szablonów w runtime, `eval`-owe silniki reguł) — wymień bibliotekę.
Electron pokazuje ostrzeżenie w konsoli dev, gdy CSP jest zbyt luźna albo brak —
traktuj je jako błąd.

**W dev CSP musi być luźniejsza** (Vite wstrzykuje `<script type="module">` z portu
lokalnego i używa `ws:` do HMR). Rozdziel:

```ts
const csp = app.isPackaged
  ? CSP_PRODUKCJA
  : "default-src 'self' http://localhost:5173; script-src 'self' 'unsafe-inline' http://localhost:5173; connect-src 'self' ws://localhost:5173;";
```

Nigdy nie zostawiaj wariantu dev w buildzie produkcyjnym — sprawdzaj `app.isPackaged`,
a nie `NODE_ENV` (`NODE_ENV` w spakowanej aplikacji bywa niezdefiniowany).

## Blokowanie nawigacji i nowych okien

To jest jedna z dwóch rzeczy, które faktycznie zatrzymują atak po XSS-ie (druga to CSP).

```ts
import { app, shell } from 'electron';
import { URL } from 'node:url';

const DOZWOLONE_HOSTY = new Set(['danacogroup.com.pl', 'api.danacogroup.com.pl']);

app.on('web-contents-created', (_e, contents) => {
  // 1. nawigacja w tym samym oknie
  contents.on('will-navigate', (event, url) => {
    const cel = new URL(url);
    const zrodlo = new URL(contents.getURL());
    if (cel.origin !== zrodlo.origin) {
      event.preventDefault();
      if (cel.protocol === 'https:' && DOZWOLONE_HOSTY.has(cel.hostname)) {
        shell.openExternal(url);
      }
    }
  });

  // 2. nawigacja w ramce (iframe) — osobne zdarzenie od E22
  contents.on('will-frame-navigate', (event) => {
    if (!event.frame?.url.startsWith('file://')) event.preventDefault();
  });

  // 3. przekierowania serwera
  contents.on('will-redirect', (event, url) => {
    if (!url.startsWith('https://')) event.preventDefault();
  });

  // 4. nowe okna
  contents.setWindowOpenHandler(({ url }) => {
    const cel = new URL(url);
    if (cel.protocol === 'https:' && DOZWOLONE_HOSTY.has(cel.hostname)) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  // 5. próba osadzenia <webview>
  contents.on('will-attach-webview', (event, webPreferences, params) => {
    delete webPreferences.preload;
    webPreferences.nodeIntegration = false;
    webPreferences.contextIsolation = true;
    if (!params.src.startsWith('https://')) event.preventDefault();
  });
});
```

`app.on('web-contents-created')` łapie **wszystkie** `WebContents`, także te w
`WebContentsView` i `<webview>` — dlatego pisz to raz globalnie, a nie per okno.

## `shell.openExternal` — walidacja

```ts
const DOZWOLONE_SCHEMATY = new Set(['https:', 'mailto:']);

export async function otworzZewnetrznie(url: string): Promise<void> {
  let parsed: URL;
  try { parsed = new URL(url); } catch { throw new Error('Niepoprawny URL'); }
  if (!DOZWOLONE_SCHEMATY.has(parsed.protocol)) {
    throw new Error(`Zabroniony schemat: ${parsed.protocol}`);
  }
  await shell.openExternal(parsed.toString());
}
```

Bez tego filtra `shell.openExternal('file:///C:/Windows/System32/calc.exe')` uruchamia
program, a `shell.openExternal('ms-msdt:...')` (Follina) albo `search-ms:` na Windows
otwierają wektory znane z realnych ataków. Na macOS analogicznie dowolny schemat
zarejestrowany przez inną aplikację.

## Uprawnienia sesji

```ts
const UPRAWNIENIA_DOZWOLONE = new Set<string>(['clipboard-sanitized-write', 'notifications']);

session.defaultSession.setPermissionRequestHandler((wc, uprawnienie, callback, szczegoly) => {
  const zrodlo = szczegoly.requestingUrl;
  if (!zrodlo.startsWith('file://') && !zrodlo.startsWith('app://')) return callback(false);
  callback(UPRAWNIENIA_DOZWOLONE.has(uprawnienie));
});

// wersja synchroniczna — pytana m.in. przy getUserMedia z poziomu Blinka
session.defaultSession.setPermissionCheckHandler((_wc, uprawnienie, zrodlo) => {
  if (!zrodlo?.startsWith('file://') && !zrodlo?.startsWith('app://')) return false;
  return UPRAWNIENIA_DOZWOLONE.has(uprawnienie);
});

// od E42: osobny handler dla wyświetlania (screen capture)
session.defaultSession.setDisplayMediaRequestHandler((request, callback) => {
  // pokaż własny wybór ekranu; bez tego getDisplayMedia zawiesza się bez odpowiedzi
  desktopCapturer.getSources({ types: ['screen', 'window'] }).then((zrodla) => {
    callback({ video: zrodla[0] });   // w produkcji: dialog wyboru
  });
});
```

Lista uprawnień, które padają najczęściej: `media` (kamera+mikrofon), `geolocation`,
`notifications`, `midi`, `pointerLock`, `fullscreen`, `openExternal`, `clipboard-read`.
Domyślnie dla `file://` Electron **przyznaje** większość bez pytania — dlatego handler
jest obowiązkowy nawet w aplikacji bez treści zdalnych.

## Fuses

Fuses to bity w binarce Electrona przestawiane w czasie pakowania. Są objęte podpisem
kodu — użytkownik nie zmieni ich bez unieważnienia podpisu.

| Fuse | Domyślnie | Ustaw na | Powód |
| --- | --- | --- | --- |
| `runAsNode` | włączony | **`false`** | `ELECTRON_RUN_AS_NODE=1 MojaApp.exe skrypt.js` uruchamia dowolny kod Node z podpisem twojej aplikacji |
| `enableNodeOptionsEnvironmentVariable` | włączony | **`false`** | `NODE_OPTIONS=--require zły.js` wstrzykuje kod przy starcie |
| `enableNodeCliInspectArguments` | włączony | **`false`** | `--inspect` daje debugger w procesie głównym |
| `enableEmbeddedAsarIntegrityValidation` | wyłączony | **`true`** | bez tego podmiana `app.asar` przechodzi niezauważona |
| `onlyLoadAppFromAsar` | wyłączony | **`true`** | bez tego katalog `app/` obok `app.asar` ma pierwszeństwo i omija walidację |
| `enableCookieEncryption` | wyłączony | **`true`** | ciasteczka sesyjne szyfrowane kluczem systemowym |
| `loadBrowserProcessSpecificV8Snapshot` | wyłączony | zostaw | tylko dla własnych snapshotów |
| `grantFileProtocolExtraPrivileges` | włączony | `false`, jeśli używasz własnego protokołu | `file://` przestaje być traktowany jako uprzywilejowane origin |
| `wasmTrapHandlers` | włączony | zostaw | wyłączenie psuje wydajność WASM |

```ts
// weryfikacja po zbudowaniu — dodaj do CI jako krok obowiązkowy
// npx @electron/fuses read --app out/MojaApp-darwin-arm64/MojaApp.app
```

**Kolejność operacji przy pakowaniu ma znaczenie:** fuses muszą być przestawione
**przed** podpisaniem. Forge z `@electron-forge/plugin-fuses` i electron-builder z
`electronFuses` robią to poprawnie. Ręczne `flipFuses` po podpisie unieważnia podpis.

## ASAR integrity

Weryfikuje SHA-256 archiwum `app.asar` przy starcie. Hash jest zapisany w `Info.plist`
(macOS) albo w zasobach `.exe` (Windows) i objęty podpisem kodu.

- macOS: od Electron 16, Windows: od Electron 30. **Linux: brak wsparcia.**
- Wymaga obu fuses: `EnableEmbeddedAsarIntegrityValidation` i `OnlyLoadAppFromAsar`.
- Wymaga `@electron/asar` ≥ 3.1.0 (aktualnie 4.2.1).
- Electron Forge ≥ 7.4.0 i `@electron/packager` ≥ 18.3.1 konfigurują to automatycznie,
  gdy `asar: true` i fuses są ustawione.
- Obsługiwany jest wyłącznie SHA-256.

**Czego ASAR integrity nie robi:** nie chroni plików rozpakowanych przez `asarUnpack`
(moduły natywne, binaria). Jeśli tam trzymasz coś krytycznego, sprawdzaj hash sam.

## Sekrety w aplikacji desktopowej

**Nie ma bezpiecznego miejsca na sekret w aplikacji, którą wysyłasz użytkownikowi.**
To nie jest ostrożne sformułowanie — to jest fakt wynikający z modelu zagrożeń: właściciel
maszyny ma pełne prawa do procesu twojej aplikacji.

| Miejsce | Trudność wyciągnięcia | Wniosek |
| --- | --- | --- |
| stała w kodzie renderera | otwórz DevTools, Ctrl+F | zero ochrony |
| stała w `app.asar` | `npx asar extract app.asar out` | zero ochrony |
| zmienna środowiskowa wstrzyknięta w buildzie | `strings` na binarce | zero ochrony |
| plik obok aplikacji, zaszyfrowany kluczem w kodzie | 10 minut z debuggerem | zero ochrony |
| `safeStorage` (Keychain/DPAPI) | brak — ale to działa tylko na tej maszynie i dla tego użytkownika | ochrona **przed innym użytkownikiem tej maszyny**, nie przed właścicielem |
| obfuskacja, bytenode, natywny moduł | godziny do dni dla zdeterminowanego | opóźnienie, nie zabezpieczenie |

**Co robić zamiast:**
- Klucze do API stron trzecich (OpenAI, płatności, Google) **zostają na twoim serwerze**.
  Aplikacja dzwoni do twojego backendu, backend dzwoni dalej. Jeśli to niemożliwe,
  załóż, że klucz jest publiczny i ogranicz go po stronie dostawcy (limity, scope,
  ograniczenie IP).
- Token użytkownika: krótko żyjący access token + refresh token w `safeStorage`.
  Refresh token unieważnialny po stronie serwera.
- Licencjonowanie: weryfikacja po stronie serwera z podpisem asymetrycznym. Klucz
  **publiczny** w aplikacji, prywatny na serwerze. Aplikacja weryfikuje podpis licencji,
  nie generuje go.

```ts
import { safeStorage, app } from 'electron';
import fs from 'node:fs/promises';
import path from 'node:path';

const PLIK = path.join(app.getPath('userData'), 'token.bin');

export async function zapiszToken(token: string): Promise<void> {
  if (!safeStorage.isEncryptionAvailable()) {
    // Linux bez gnome-libsecret/kwallet: safeStorage użyje zaszytego hasła = brak ochrony
    throw new Error('Brak magazynu haseł systemu — token nie zostanie zapisany');
  }
  const szyfr = await safeStorage.encryptStringAsync(token);
  await fs.writeFile(PLIK, szyfr, { mode: 0o600 });
}

export async function odczytajToken(): Promise<string | null> {
  try {
    const szyfr = await fs.readFile(PLIK);
    return await safeStorage.decryptStringAsync(szyfr);
  } catch { return null; }
}
```

`safeStorage`: macOS → Keychain, Windows → DPAPI, Linux → `gnome-libsecret`/`kwallet`.
**Na Linuksie bez działającego magazynu haseł Electron używa zaszytego hasła w kodzie** —
`safeStorage.getSelectedStorageBackend()` powie ci, co jest aktywne. Wersje asynchroniczne
(`encryptStringAsync`) są zalecane; synchroniczne mogą zostać oznaczone jako przestarzałe.

`keytar` (7.9.0, ostatnie wydanie 2022) jest **porzucony i zarchiwizowany** — nie
używaj go w nowym kodzie, `safeStorage` go zastępuje.

## Zależności

- `npm audit --omit=dev` w CI jako bramka. Podatność w zależności renderera jest tak samo
  groźna jak w mainie, bo preload i main są w tym samym drzewie zależności.
- Moduły natywne kompilują kod C++ w twoim procesie głównym — traktuj je jak zależność
  o najwyższym ryzyku. Przed dodaniem sprawdź: ostatnie wydanie, liczba maintainerów,
  czy repozytorium żyje.
- Pakuj tylko `dependencies`, nigdy `devDependencies` (Forge i electron-builder robią to
  domyślnie, ale sprawdź przez `npx asar list app.asar | grep node_modules`).
- **`electron` musi być w `devDependencies`**, nie w `dependencies` — inaczej electron-builder
  spakuje całą binarkę Electrona wewnątrz `app.asar` i instalator urośnie dwukrotnie.

## Aktualizacja jako wektor ataku

Kanał aktualizacji jest najbardziej wartościowym celem: kto go przejmie, dostarcza
dowolny kod na wszystkie maszyny użytkowników, z pełnymi prawami, podpisany twoją nazwą.

Wymagane minimum:

1. **Wyłącznie HTTPS** z weryfikacją certyfikatu. Nie wyłączaj `strictSSL` w konfiguracji
   `electron-updater` „na chwilę do testów” — takie zmiany zostają w repo.
2. **Podpis pobranego pakietu weryfikowany przed instalacją.** Na Windows `electron-updater`
   sprawdza podpis Authenticode przez `publisherName` — **ustaw to jawnie**:
   ```yaml
   win:
     publisherName: "DANACO GROUP sp. z o.o."   # dokładnie jak CN w certyfikacie
   ```
   Bez tego pola updater przyjmuje dowolny podpisany plik. Na macOS Squirrel.Mac wymaga,
   by nowa wersja miała **ten sam Team ID** co zainstalowana.
3. **`latest.yml` / `latest-mac.yml` publikowane razem z artefaktami** i zawierające
   sha512 każdego pliku. `electron-updater` weryfikuje ten hash po pobraniu.
4. **Dostęp do zasobnika/repozytorium wydań ograniczony do CI.** Klucze do S3 z rotacją,
   uprawnienia tylko `PutObject` na prefiks wydań.
5. **Nie serwuj wydań z tego samego hosta, co treść generowaną przez użytkowników.**
6. **Nigdy nie pobieraj i nie wykonuj kodu poza mechanizmem aktualizacji.** „Gorąca łatka”
   pobierana jako JS i `eval`-owana omija podpis kodu, notaryzację i ASAR integrity —
   to jest tylna furtka, którą sam wbudowałeś. Apple zresztą zabrania tego w regulaminie
   dla aplikacji z App Store.

## Skanowanie automatyczne

`@electron-forge/plugin-electronegativity` (w paczce Forge 7.11.2) uruchamia
Electronegativity przy `npm run package` i wykrywa złe `webPreferences`, `nodeIntegration`,
brak CSP, użycie `remote`. Wpina się w CI. To nie zastępuje przeglądu, ale łapie regresje,
gdy ktoś doda okno bez przemyślenia.

```ts
// forge.config.ts
import { ElectronegativityPlugin } from '@electron-forge/plugin-electronegativity';
plugins: [ new ElectronegativityPlugin({ isSarif: true }) ]
```

## Lista przed wydaniem

- [ ] Każde `new BrowserWindow` / `new WebContentsView` używa stałej `BEZPIECZNE`.
- [ ] Konsola dev nie pokazuje ostrzeżeń „Electron Security Warning”.
- [ ] CSP produkcyjna bez `unsafe-eval`, rozdzielona od dev, wybierana przez `app.isPackaged`.
- [ ] `web-contents-created` z blokadą nawigacji, redirectów, `setWindowOpenHandler`
      i `will-attach-webview` — zarejestrowany globalnie.
- [ ] `setPermissionRequestHandler` + `setPermissionCheckHandler` odmawiają domyślnie.
- [ ] Każdy `ipcMain.handle` waliduje `senderFrame` i kształt argumentów.
- [ ] Fuses zweryfikowane przez `npx @electron/fuses read` na zbudowanym artefakcie.
- [ ] ASAR integrity aktywne na macOS i Windows (sprawdź przez podmianę bajtu w `app.asar` —
      aplikacja ma odmówić startu).
- [ ] Żaden sekret nie jest w `app.asar`: `npx asar extract app.asar /tmp/a && grep -rIn "sk-\|BEGIN PRIVATE\|api_key" /tmp/a`.
- [ ] `win.publisherName` ustawione; kanał aktualizacji po HTTPS; `latest*.yml` z sha512.
- [ ] `npm audit --omit=dev` bez podatności `high`/`critical`.
- [ ] Wersja Electrona w jednej z trzech wspieranych linii.
