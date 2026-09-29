# Przeglądarka, kiosk i osadzanie treści webowej

Odniesienie: Electron 43.2.0 (Chromium 150). To jest jedyny obszar, w którym Electron
nie ma realnej konkurencji — dostajesz Chromium z pełnym dostępem do `webRequest`,
sesji, ciasteczek i rozszerzeń.

## Wybór mechanizmu osadzania

| Mechanizm | Status w E43 | Kiedy |
| --- | --- | --- |
| **`WebContentsView` w `BaseWindow`** | zalecany | przeglądarka, karty, panel z osadzoną stroną, kiosk |
| `BrowserView` | **przestarzały od E29**, nadal działa | tylko istniejący kod; migruj |
| `<webview>` | odradzany przez dokumentację, `webviewTag: false` domyślnie | ostatnia deska ratunku, gdy potrzebujesz osadzenia w układzie CSS |
| `<iframe>` | standard | treść z tego samego origin albo prosta strona bez potrzeby izolacji procesu |

Dokumentacja Electrona mówi o `<webview>` wprost: opiera się na komponencie Chromium
przechodzącym „dramatyczne zmiany architektoniczne”, co wpływa na stabilność renderowania,
nawigacji i routingu zdarzeń. Traktuj to jako ostrzeżenie, nie formalność.

### Migracja `BrowserView` → `WebContentsView`

| `BrowserView` | `WebContentsView` |
| --- | --- |
| `new BrowserView({ webPreferences })` | `new WebContentsView({ webPreferences })` |
| `win.addBrowserView(view)` | `win.contentView.addChildView(view)` |
| `win.removeBrowserView(view)` | `win.contentView.removeChildView(view)` |
| `view.setBounds({...})` | `view.setBounds({...})` (bez zmian) |
| `view.setAutoResize({ width: true })` | **brak odpowiednika** — przelicz w `win.on('resize')` |
| `view.webContents` | `view.webContents` (bez zmian) |
| `win.setTopBrowserView(view)` | kolejność w `contentView.children`; `addChildView(view)` przenosi na wierzch |
| `BrowserWindow` jako kontener | `BaseWindow` (lżejszy, bez własnego `WebContents`) |

Brak `setAutoResize` to najczęstsze zaskoczenie: po migracji widok zostaje w rozmiarze
początkowym przy zmianie rozmiaru okna.

## Szkielet przeglądarki z kartami

```ts
// src/main/przegladarka.ts
import { BaseWindow, WebContentsView, session, shell } from 'electron';
import path from 'node:path';

const WYSOKOSC_CHROME = 88;   // pasek adresu + pasek kart

type Karta = { id: number; widok: WebContentsView; tytul: string; url: string };

export class Przegladarka {
  private okno: BaseWindow;
  private chrome: WebContentsView;              // nasz interfejs (pasek adresu, karty)
  private karty = new Map<number, Karta>();
  private aktywna: number | null = null;
  private nastepnyId = 1;

  constructor() {
    this.okno = new BaseWindow({ width: 1400, height: 900, backgroundColor: '#1a1a1a' });

    this.chrome = new WebContentsView({
      webPreferences: {
        preload: path.join(__dirname, 'preload-chrome.js'),
        contextIsolation: true,
        sandbox: true,
        nodeIntegration: false,
      },
    });
    this.okno.contentView.addChildView(this.chrome);
    this.chrome.webContents.loadFile(path.join(__dirname, '../chrome/index.html'));

    this.okno.on('resize', () => this.ulozenie());
    this.ulozenie();
  }

  private ulozenie() {
    const { width, height } = this.okno.getContentBounds();
    this.chrome.setBounds({ x: 0, y: 0, width, height: WYSOKOSC_CHROME });
    const k = this.aktywna !== null ? this.karty.get(this.aktywna) : null;
    k?.widok.setBounds({ x: 0, y: WYSOKOSC_CHROME, width, height: height - WYSOKOSC_CHROME });
  }

  nowaKarta(url: string): number {
    const id = this.nastepnyId++;
    const partycja = `persist:karty`;            // wspólna sesja kart, oddzielona od chrome

    const widok = new WebContentsView({
      webPreferences: {
        partition: partycja,
        preload: path.join(__dirname, 'preload-strona.js'),
        contextIsolation: true,
        sandbox: true,
        nodeIntegration: false,
        webSecurity: true,
        // NIGDY nie dawaj tu preloadu z API systemowym — to obca strona
      },
    });

    const wc = widok.webContents;

    wc.on('page-title-updated', (_e, tytul) => {
      const k = this.karty.get(id);
      if (k) { k.tytul = tytul; this.powiadomChrome(); }
    });
    wc.on('did-navigate', (_e, u) => this.aktualizujUrl(id, u));
    wc.on('did-navigate-in-page', (_e, u) => this.aktualizujUrl(id, u));
    wc.on('did-start-loading', () => this.chrome.webContents.send('karta:ladowanie', { id, stan: true }));
    wc.on('did-stop-loading', () => this.chrome.webContents.send('karta:ladowanie', { id, stan: false }));
    wc.on('did-fail-load', (_e, kod, opis, url, glowna) => {
      if (glowna && kod !== -3) wc.loadFile(path.join(__dirname, '../chrome/blad.html'), {
        query: { kod: String(kod), opis, url },
      });
    });

    // window.open ze strony -> nowa karta, nie nowe okno
    wc.setWindowOpenHandler(({ url: nowyUrl, disposition }) => {
      if (disposition === 'new-window' || disposition === 'foreground-tab' || disposition === 'background-tab') {
        this.nowaKarta(nowyUrl);
      }
      return { action: 'deny' };
    });

    this.karty.set(id, { id, widok, tytul: '', url });
    wc.loadURL(url);
    this.przelacz(id);
    return id;
  }

  przelacz(id: number) {
    const poprzednia = this.aktywna !== null ? this.karty.get(this.aktywna) : null;
    if (poprzednia) this.okno.contentView.removeChildView(poprzednia.widok);
    const k = this.karty.get(id);
    if (!k) return;
    this.okno.contentView.addChildView(k.widok);
    this.okno.contentView.addChildView(this.chrome);   // chrome zawsze na wierzchu
    this.aktywna = id;
    this.ulozenie();
    k.widok.webContents.focus();
  }

  zamknij(id: number) {
    const k = this.karty.get(id);
    if (!k) return;
    this.okno.contentView.removeChildView(k.widok);
    k.widok.webContents.close();                 // zwalnia proces renderera
    this.karty.delete(id);
    if (this.aktywna === id) {
      const nastepna = [...this.karty.keys()][0];
      if (nastepna !== undefined) this.przelacz(nastepna);
      else this.aktywna = null;
    }
  }

  private aktualizujUrl(id: number, url: string) {
    const k = this.karty.get(id);
    if (k) { k.url = url; this.powiadomChrome(); }
  }

  private powiadomChrome() {
    this.chrome.webContents.send('karty:stan', {
      karty: [...this.karty.values()].map(({ id, tytul, url }) => ({ id, tytul, url })),
      aktywna: this.aktywna,
    });
  }
}
```

**Trzy rzeczy, które trzeba zrobić dokładnie tak:**

1. **`removeChildView` przy przełączaniu, nie `setVisible(false)`.** Widok pozostawiony
   w drzewie nadal renderuje i zużywa GPU.
2. **`addChildView(this.chrome)` po dodaniu karty** — kolejność dodania wyznacza
   kolejność malowania; bez tego pasek adresu znika pod stroną.
3. **`webContents.close()` przy zamykaniu karty**, nie tylko usunięcie z mapy. Bez tego
   proces renderera żyje dalej i po 30 kartach masz 2 GB RAM.

## Nawigacja i historia

```ts
const wc = karta.widok.webContents;

wc.navigationHistory.canGoBack();      // E30+; wcześniej wc.canGoBack()
wc.navigationHistory.canGoForward();
wc.navigationHistory.goBack();
wc.navigationHistory.goForward();
wc.navigationHistory.getAllEntries();  // [{ url, title }]
wc.navigationHistory.getActiveIndex();
wc.navigationHistory.goToIndex(3);
wc.navigationHistory.clear();

wc.reload();
wc.reloadIgnoringCache();
wc.stop();
```

Metody `canGoBack`/`goBack` bezpośrednio na `webContents` są przestarzałe od E30 —
używaj `navigationHistory`.

Normalizacja wpisu użytkownika w pasku adresu:

```ts
function interpretujWpis(wpis: string): string {
  const t = wpis.trim();
  if (/^[a-z][a-z0-9+.-]*:/i.test(t)) return t;                    // ma schemat
  if (/^([\w-]+\.)+[a-z]{2,}(\/|$|:)/i.test(t)) return `https://${t}`;  // wygląda jak domena
  if (/^localhost(:\d+)?(\/|$)/i.test(t)) return `http://${t}`;
  return `https://duckduckgo.com/?q=${encodeURIComponent(t)}`;      // fraza -> wyszukiwarka
}
```

## Sesje i partycje

Partycja wyznacza izolowany zestaw: ciasteczka, `localStorage`, IndexedDB, cache,
uprawnienia, magazyn haseł.

| Zapis | Znaczenie |
| --- | --- |
| brak `partition` | sesja domyślna (`session.defaultSession`), trwała |
| `'persist:nazwa'` | trwała, zapisana na dysku w `userData/Partitions/nazwa` |
| `'nazwa'` (bez `persist:`) | w pamięci, ginie przy zamknięciu aplikacji |

```ts
import { session } from 'electron';

const sesjaKart = session.fromPartition('persist:karty');
const sesjaPrywatna = session.fromPartition('incognito');   // bez persist: = w pamięci

// osobna partycja per profil użytkownika przeglądarki
const sesjaProfilu = session.fromPartition(`persist:profil-${idProfilu}`);
```

**Kiedy izolować:**
- Interfejs przeglądarki (`chrome`) i strony w kartach — **zawsze osobne partycje**.
  Inaczej strona może odczytać `localStorage` twojego interfejsu.
- Tryb prywatny — partycja w pamięci.
- Kilka kont tej samej usługi — osobna partycja na konto.
- Osadzony widget strony trzeciej w aplikacji biznesowej — osobna partycja.

Czyszczenie:

```ts
await sesjaPrywatna.clearStorageData({
  storages: ['cookies', 'localstorage', 'indexdb', 'websql', 'serviceworkers', 'cachestorage'],
});
await sesjaPrywatna.clearCache();
await sesjaPrywatna.clearAuthCache();
```

**Zmiana w E42:** obiekt `quotas` został usunięty z `clearStorageData()` — jeśli twój
kod go przekazuje, usuń, bo argument jest ignorowany, a w przyszłości może rzucać.

Konfiguracja sesji przed pierwszym załadowaniem:

```ts
sesjaKart.setUserAgent(
  sesjaKart.getUserAgent().replace(/ Electron\/[\d.]+/, ''),  // ukryj, że to Electron
);
sesjaKart.setSpellCheckerLanguages(['pl', 'en-US']);
sesjaKart.setProxy({ mode: 'system' });   // albo { proxyRules: 'https=proxy:8080' }
```

Usunięcie `Electron/43.2.0` z User-Agenta jest **konieczne** dla przeglądarki — część
serwisów (Google Login) blokuje logowanie z osadzonych przeglądarek rozpoznanych po UA.

## Ciasteczka

```ts
const ciasteczka = await sesjaKart.cookies.get({ domain: 'example.com' });

await sesjaKart.cookies.set({
  url: 'https://example.com',
  name: 'sesja',
  value: 'abc',
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  expirationDate: Math.floor(Date.now() / 1000) + 3600,
});

await sesjaKart.cookies.remove('https://example.com', 'sesja');
await sesjaKart.cookies.flushStore();     // wymuś zapis na dysk

sesjaKart.cookies.on('changed', (_e, cookie, powod, usuniete) => {
  // E41: wartości 'cause' rozszerzone o 'inserted-no-change-overwrite'
  //      i 'inserted-no-value-change-overwrite'
});
```

Włącz fuse `enableCookieEncryption`, żeby magazyn ciasteczek był szyfrowany kluczem
systemowym (patrz `references/electron-desktop/references/bezpieczenstwo.md`).

## `webRequest` i blokowanie treści

`webRequest` działa **per sesja** i jest jedynym miejscem, gdzie można modyfikować ruch
przed wysłaniem.

```ts
const BLOKOWANE = [
  /(^|\.)doubleclick\.net$/,
  /(^|\.)googlesyndication\.com$/,
  /(^|\.)facebook\.net$/,
];

sesjaKart.webRequest.onBeforeRequest({ urls: ['<all_urls>'] }, (szczegoly, callback) => {
  let host: string;
  try { host = new URL(szczegoly.url).hostname; } catch { return callback({}); }
  callback({ cancel: BLOKOWANE.some((r) => r.test(host)) });
});

// modyfikacja nagłówków żądania
sesjaKart.webRequest.onBeforeSendHeaders({ urls: ['<all_urls>'] }, (s, callback) => {
  const naglowki = { ...s.requestHeaders, 'DNT': '1' };
  delete naglowki['X-Requested-With'];
  callback({ requestHeaders: naglowki });
});

// zdejmowanie nagłówków blokujących osadzanie
sesjaKart.webRequest.onHeadersReceived({ urls: ['<all_urls>'] }, (s, callback) => {
  const h = { ...s.responseHeaders };
  delete h['x-frame-options'];
  delete h['X-Frame-Options'];
  callback({ responseHeaders: h });
});
```

**Ograniczenia, które trzeba znać:**

- **Tylko jeden listener na typ zdarzenia na sesję.** Kolejne wywołanie
  `onBeforeRequest` **zastępuje** poprzednie, nie dodaje się do łańcucha. Jeśli masz
  kilka modułów potrzebujących filtrowania, zbuduj własny dyspozytor.
- **`webRequest` jest wolniejszy niż `declarativeNetRequest`** przy dużych listach reguł,
  bo każde żądanie przechodzi przez IPC do procesu głównego. Przy listach typu EasyList
  (kilkadziesiąt tysięcy reguł) licz się z zauważalnym spowolnieniem ładowania.
- **Zdejmowanie `X-Frame-Options` i CSP obcych stron to obejście ich zabezpieczeń.**
  Robisz to na własną odpowiedzialność prawną i techniczną — strona miała powód,
  żeby ustawić ten nagłówek (najczęściej: obrona przed clickjackingiem).

**Rozszerzenia Chrome** jako alternatywa dla własnego blokowania:

```ts
// od E35 API rozszerzeń jest w session.extensions
const ext = await sesjaKart.extensions.loadExtension('/sciezka/do/rozszerzenia', {
  allowFileAccess: false,
});
sesjaKart.extensions.getAllExtensions();
```

Electron obsługuje **podzbiór** API rozszerzeń Chrome — MV3 z `declarativeNetRequest`
działa częściowo, `chrome.tabs` w ograniczonym zakresie. Nie zakładaj, że dowolne
rozszerzenie ze sklepu zadziała. `[niepotwierdzone: pełna macierz wspieranych API
rozszerzeń w E43 — dokumentacja podaje listę, ale zmienia się co major]`

## Wstrzykiwanie skryptów do obcych stron

Trzy sposoby, w kolejności rosnącej inwazyjności:

**1. `preload` w partycji** — wykonuje się przed skryptami strony, w izolowanym świecie,
ma `contextBridge`. To jest właściwy sposób na dodanie własnego API do stron, które
kontrolujesz (np. własna aplikacja webowa w kiosku).

```ts
sesjaKart.setPreloads([path.join(__dirname, 'preload-strona.js')]);
```

**2. `webContents.executeJavaScript`** — wykonuje w **głównym świecie** strony, po
załadowaniu. Widzi zmienne strony, strona widzi efekty.

```ts
wc.on('dom-ready', async () => {
  const tytul = await wc.executeJavaScript('document.title', true);
});
```

Drugi argument (`userGesture`) na `true` pozwala wywołać API wymagające interakcji
użytkownika (`play()`, pełny ekran).

**3. `webContents.insertCSS` / `executeJavaScriptInIsolatedWorld`** — styl albo skrypt
w osobnym świecie, niewidoczny dla strony.

```ts
const klucz = await wc.insertCSS('body { filter: invert(1) hue-rotate(180deg) }');
await wc.removeInsertedCSS(klucz);

await wc.executeJavaScriptInIsolatedWorld(999, [
  { code: 'document.querySelectorAll(".reklama").forEach(e => e.remove())' },
]);
```

**Zasady bezpieczeństwa przy obcych stronach:**
- Preload dla obcych stron **nie może wystawiać żadnego API systemowego**. Osobny plik,
  osobna partycja, minimalna powierzchnia.
- Wynik `executeJavaScript` pochodzi ze strony — traktuj jak dane niezaufane i waliduj.
- Nie wstrzykuj skryptu z sekretem (token, klucz) do obcej strony. Strona go odczyta.

## Tryb kiosk

```ts
const okno = new BaseWindow({
  kiosk: true,               // pełny ekran, bez wyjścia standardowymi skrótami
  frame: false,
  fullscreen: true,
  alwaysOnTop: true,
  closable: false,
  minimizable: false,
  skipTaskbar: true,
});

// blokada skrótów wyjścia w rendererze
wc.on('before-input-event', (event, wejscie) => {
  const zablokowane = ['F11', 'F12', 'Escape'];
  const kombinacje =
    (wejscie.alt && wejscie.key === 'Tab') ||
    (wejscie.control && wejscie.key === 'w') ||
    (wejscie.meta && wejscie.key === 'q');
  if (zablokowane.includes(wejscie.key) || kombinacje) event.preventDefault();
});

// blokada menu kontekstowego i DevTools
wc.on('context-menu', (e) => e.preventDefault());
wc.on('devtools-opened', () => wc.closeDevTools());
```

Uzupełnienia poza Electronem, bez których kiosk nie jest kioskiem:

- **Automatyczny restart po awarii.** `app.on('render-process-gone')` → `reload()`;
  poza tym systemowy watchdog (`systemd` na Linuksie, usługa na Windows).
- **Autostart i blokada powłoki systemu.** Na Windows: zamiana powłoki na twoją
  aplikację (`Shell` w rejestrze) albo Assigned Access. Na Linuksie: sesja z twoją
  aplikacją jako jedynym klientem X/Wayland.
- **Blokada `Ctrl+Alt+Del`, menedżera zadań, klawiszy systemowych** — to jest polityka
  systemowa (GPO na Windows), nie da się z poziomu Electrona.
- **Reset stanu po bezczynności.** Timer 2-5 minut bez interakcji → wyczyść sesję,
  wróć do strony startowej. Bez tego kolejny użytkownik widzi dane poprzedniego.

```ts
let timerBezczynnosci: NodeJS.Timeout;
function resetujTimer() {
  clearTimeout(timerBezczynnosci);
  timerBezczynnosci = setTimeout(async () => {
    await sesjaKart.clearStorageData();
    wc.loadURL(STRONA_STARTOWA);
  }, 3 * 60 * 1000);
}
wc.on('before-input-event', resetujTimer);
wc.on('cursor-changed', resetujTimer);
```

## Drukowanie i PDF

```ts
// druk na drukarce systemowej
const drukarki = await wc.getPrintersAsync();
const ok = await new Promise<boolean>((resolve) => {
  wc.print({
    silent: false,                       // true = bez dialogu, wymaga deviceName
    deviceName: drukarki[0]?.name,
    printBackground: true,
    margins: { marginType: 'custom', top: 20, bottom: 20, left: 20, right: 20 },  // 1/1000 cala
    pageSize: 'A4',
    copies: 1,
    landscape: false,
  }, (sukces) => resolve(sukces));
});

// generowanie PDF-a
const pdf = await wc.printToPDF({
  pageSize: 'A4',
  printBackground: true,
  landscape: false,
  margins: { top: 0.4, bottom: 0.4, left: 0.4, right: 0.4 },   // cale
  displayHeaderFooter: true,
  headerTemplate: '<div style="font-size:8px;width:100%;text-align:center">Nagłówek</div>',
  footerTemplate: '<div style="font-size:8px;width:100%;text-align:center"><span class="pageNumber"></span>/<span class="totalPages"></span></div>',
  generateTaggedPDF: true,     // dostępność
});
await fs.writeFile('/tmp/wynik.pdf', pdf);
```

- `printToPDF` renderuje **stan bieżący strony**; poczekaj na `did-finish-load`
  i na fonty (`document.fonts.ready`), inaczej dostaniesz PDF bez tekstu.
- `@media print` w CSS działa; `@page` w większości działa.
- Do generowania PDF-ów z szablonu bez pokazywania okna: `BaseWindow` z `show: false`,
  albo `WebContentsView` bez dodawania do okna — `webContents` działa i bez widoczności.
- **Zmiana w E41:** PDF-y nie tworzą już osobnego `WebContents` — renderują się
  w tym samym kontekście. Kod, który szukał osobnego `WebContents` dla podglądu PDF
  (np. przez `webContents.getAllWebContents()`), przestanie go znajdować.

## Pobieranie plików

```ts
sesjaKart.on('will-download', (event, item, wc) => {
  const nazwa = item.getFilename();
  const rozmiar = item.getTotalBytes();

  // decyzja o ścieżce — bez tego pokaże się dialog systemowy
  item.setSavePath(path.join(app.getPath('downloads'), bezpiecznaNazwa(nazwa)));

  item.on('updated', (_e, stan) => {
    if (stan === 'progressing' && !item.isPaused()) {
      const procent = rozmiar > 0 ? (item.getReceivedBytes() / rozmiar) * 100 : 0;
      chrome.webContents.send('pobieranie:postep', { nazwa, procent });
    }
  });

  item.once('done', (_e, stan) => {
    chrome.webContents.send('pobieranie:koniec', { nazwa, stan });  // 'completed'|'cancelled'|'interrupted'
  });
});

function bezpiecznaNazwa(n: string): string {
  return n.replace(/[/\\?%*:|"<>]/g, '_').replace(/^\.+/, '').slice(0, 200) || 'plik';
}
```

**Sanityzacja nazwy jest obowiązkowa** — serwer podaje `Content-Disposition: filename`,
które może zawierać `../../../etc/passwd`. Bez czyszczenia zapisujesz plik poza katalogiem
pobrań.

Nie otwieraj pobranego pliku automatycznie. `shell.openPath` na pobranym `.exe`, `.dmg`,
`.scr` to uruchomienie kodu z internetu jednym kliknięciem.

## Zdalne treści a bezpieczeństwo — reguły nienegocjowalne

1. **Obca strona nigdy nie dostaje preloadu z API systemowym.** Osobny, minimalny
   preload albo żaden.
2. **`nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`, `webSecurity: true`
   dla każdego widoku ładującego treść spoza aplikacji.** Bez wyjątków.
3. **Osobna partycja dla obcych treści.** Wspólna sesja z interfejsem aplikacji oznacza,
   że strona widzi twoje ciasteczka i `localStorage`.
4. **`setWindowOpenHandler` z `action: 'deny'`** i własną obsługą — inaczej strona otwiera
   `BrowserWindow` dziedziczący twoje `webPreferences`.
5. **`setPermissionRequestHandler` per partycja**, odmawiający domyślnie. Strona
   z kamerą i mikrofonem bez pytania to nie jest hipoteza.
6. **`will-navigate` z listą dozwoloną** dla widoków, które mają pokazywać jedną,
   konkretną stronę (kiosk, osadzony panel).
7. **Nie wyłączaj `webSecurity`, żeby obejść CORS.** Właściwe rozwiązanie: własny protokół
   z `corsEnabled` albo proxy w procesie głównym przez `net.fetch`.
8. **Zakładaj, że osadzona strona zostanie przejęta.** Projektuj tak, żeby przejęcie
   nie dawało dostępu do niczego poza jej własną partycją.
