# Wydajność i rozmiar

Odniesienie: Electron 43.2.0 (Chromium 150, V8 15.0, Node 24.18.0).

## Budżety

Ustal je przed optymalizacją, bo inaczej optymalizujesz w nieskończoność.

| Metryka | Budżet | Jak mierzyć |
| --- | --- | --- |
| czas do pierwszego widocznego okna (zimny start) | ≤ 1,5 s na SSD, ≤ 3 s na HDD | `Date.now()` w pierwszej linii main → `ready-to-show` |
| czas do interaktywności renderera | ≤ 2,5 s | Performance panel, `DOMContentLoaded` + pierwsza reakcja |
| pamięć procesu głównego w spoczynku | ≤ 80 MB | `app.getAppMetrics()` |
| pamięć całej aplikacji, jedno okno, spoczynek | ≤ 250 MB | suma z `getAppMetrics()` |
| rozmiar instalatora | ≤ 120 MB (bez modeli/zasobów) | `du -sh` |
| CPU w spoczynku | ≤ 0,5 % | Monitor aktywności / Menedżer zadań |

Referencja: pusta aplikacja Electron 43 to około 90-110 MB instalatora na platformę
i 130-180 MB RAM przy jednym oknie. Wszystko powyżej to twój kod i zależności.

## Czas startu

Sekwencja zimnego startu i gdzie idzie czas:

| Etap | Typowy czas | Co go wydłuża |
| --- | --- | --- |
| uruchomienie procesu, mapowanie binarki | 100-300 ms | rozmiar binarki, antywirus na Windows, pierwszy start po instalacji |
| wykonanie `main.js` do `whenReady` | **twoje 20-500 ms** | `require` na górze pliku, synchroniczne I/O, odczyt konfiguracji |
| `whenReady` → `new BrowserWindow` | 50-150 ms | budowa menu domyślnego, inicjalizacja sesji |
| ładowanie HTML + JS renderera | **twoje 100-2000 ms** | rozmiar bundle'a, brak code splittingu |
| pierwsze malowanie → `ready-to-show` | 50-200 ms | ilość DOM-u, CSS, fonty |

Pomiar:

```ts
// pierwsza linia src/main.ts
const START = Date.now();
import { app, BrowserWindow } from 'electron';

app.whenReady().then(() => {
  console.log(`start → whenReady: ${Date.now() - START} ms`);
  const okno = new BrowserWindow({ show: false, backgroundColor: '#111213' });
  okno.once('ready-to-show', () => {
    console.log(`start → widoczne okno: ${Date.now() - START} ms`);
    okno.show();
  });
  okno.loadFile('renderer/index.html');
});
```

### Lazy require w procesie głównym

```ts
// ŹLE — 300 ms zanim aplikacja w ogóle zacznie się uruchamiać
import Database from 'better-sqlite3';
import { PDFDocument } from 'pdf-lib';
import sharp from 'sharp';

// DOBRZE — ładowane przy pierwszym użyciu
let _db: import('better-sqlite3').Database | null = null;
async function baza() {
  if (!_db) {
    const { default: Database } = await import('better-sqlite3');
    _db = new Database(sciezkaBazy);
  }
  return _db;
}
```

Pomiar kosztu pojedynczego modułu:

```bash
node --cpu-prof -e "require('better-sqlite3')"
node -e "const t=Date.now();require('sharp');console.log(Date.now()-t)"
```

Moduły, które regularnie kosztują ponad 100 ms: `sharp`, `puppeteer`, `aws-sdk` (v2),
`moment` z locale, `pdfjs-dist`, `@prisma/client`. Ładuj je leniwie albo przenieś do
`utilityProcess`.

### Pominięcie domyślnego menu

```ts
import { Menu } from 'electron';
Menu.setApplicationMenu(null);   // PRZED app.whenReady()
```

Oszczędza 20-60 ms, bo Electron nie buduje domyślnego szablonu menu. Na macOS musisz potem ustawić
własne menu (patrz `references/electron-desktop/references/warstwa-natywna.md`), bo bez niego
przestaje działać Cmd+C.

### Cache kodu V8

`v8-compile-cache` (2.4.0, ostatnie wydanie 2023) buforuje skompilowany bytecode modułów
CommonJS. **Nie używaj go w nowych projektach**: jest niekonserwowany, a Node 22+ ma
wbudowany `module.enableCompileCache()`.

```ts
// pierwsza linia main, przed jakimkolwiek require
import module from 'node:module';
module.enableCompileCache?.(path.join(app.getPath('cache'), 'v8'));
```

Zysk: 20-40 % czasu parsowania i kompilacji JS przy drugim i kolejnych uruchomieniach.
Przy zbundlowanym mainie (jeden plik 500 kB) to jest 30-80 ms.
`[niepotwierdzone: pełne wsparcie module.enableCompileCache w Electron 43 — API pochodzi
z Node 22, Electron 43 ma Node 24.18, ale Electron ma własny loader modułów; zweryfikuj
istnienie funkcji przed użyciem, stąd `?.`]`

**Bundlowanie mainu i preloadu daje więcej niż cache.** Jeden plik zamiast 800 modułów
to jeden `open`+`read` zamiast 800 — na Windows z antywirusem różnica bywa
kilkusetmilisekundowa. Forge z wtyczką Vite i `electron-vite` robią to domyślnie.

### Snapshoty V8

`electron/mksnapshot` pozwala zapisać stan heapu V8 po wykonaniu kodu inicjalizującego
i wczytać go zamiast wykonywać. Zysk: 50-200 ms. Koszt: skomplikowana konfiguracja,
kod w snapshocie nie może dotykać I/O ani API Electrona, trudne debugowanie.

**Rekomendacja: nie rób tego, dopóki start nie przekracza budżetu po wszystkich
prostszych krokach.** To ostatnie 10 % za 80 % wysiłku.

### Renderer

- **Ładuj z lokalnego pliku, nigdy z sieci.** `loadURL('https://...')` w produkcji dodaje
  RTT + czas serwera do każdego startu i przestaje działać offline.
- **Code splitting po trasach.** Renderer to zwykła aplikacja webowa — obowiązują reguły
  z `../ui-ux-pro/references/wydajnosc-frontu.md`.
- **Nie renderuj listy 10 tys. elementów.** Wirtualizacja (`@tanstack/react-virtual`).
- **`backgroundColor` na oknie** zgodny z tłem aplikacji — eliminuje biały błysk bez
  żadnego kosztu.
- **Fonty lokalne, `font-display: swap`** — pobieranie fontu z sieci przy starcie
  desktopowej aplikacji to błąd projektowy.

## Pamięć

Każdy renderer to osobny proces Chromium: 40-90 MB bazowo, plus twój DOM i JS heap.
Dziesięć okien to 400-900 MB tylko na renderery.

| Strategia | Oszczędność | Koszt |
| --- | --- | --- |
| jedno okno + routing wewnętrzny | ~60 MB na każde niepowstałe okno | brak natywnego zachowania okien |
| `WebContentsView` w jednym `BaseWindow` zamiast wielu okien | procesy nadal osobne, ale wspólny GPU i sesja: ~10-15 MB na widok | zarządzanie `setBounds` ręcznie |
| ukrywanie zamiast zamykania okna | brak — proces żyje | szybkie ponowne pokazanie |
| `webContents.close()` przy ukrywaniu, odtworzenie przy pokazaniu | pełne zwolnienie | utrata stanu, ~200 ms na odtworzenie |
| `session` współdzielona między oknami | jeden cache zamiast N | brak izolacji |

Diagnostyka:

```ts
setInterval(() => {
  for (const m of app.getAppMetrics()) {
    log.info(`${m.type} pid=${m.pid} cpu=${m.cpu.percentCPUUsage.toFixed(1)}% ` +
             `mem=${Math.round((m.memory?.workingSetSize ?? 0) / 1024)} MB`);
  }
}, 60_000);
```

**Wycieki w rendererze:** DevTools → Memory → Heap snapshot, porównaj dwa zrzuty
(przed i po cyklu otwórz/zamknij widok). Typowe źródła w Electronie:
- `ipcRenderer.on` bez `removeListener` przy odmontowaniu komponentu,
- referencje do `WebContents` w `Map` w procesie głównym po zamknięciu okna,
- `setInterval` w rendererze, który przeżywa nawigację.

```ts
// sprzątanie w procesie głównym — obowiązkowe
okno.on('closed', () => {
  okna.delete(okno.id);
  timery.get(okno.id)?.forEach(clearInterval);
  timery.delete(okno.id);
});
```

**Ograniczenie heapu renderera** (chroni przed OOM całej maszyny przy wycieku):

```ts
app.commandLine.appendSwitch('js-flags', '--max-old-space-size=512');
```

## Rozmiar instalatora

Skład typowej aplikacji 130 MB:

| Składnik | Rozmiar | Da się zmniejszyć |
| --- | --- | --- |
| binarka Electrona + Chromium | 85-100 MB | nie (to jest cena Electrona) |
| ICU (dane lokalizacji) | ~10 MB | tak, `--with-intl=small-icu` w custom buildzie — rzadko warte |
| twój kod + zależności (`app.asar`) | **5-40 MB** | tak, tu jest cała robota |
| zasoby (ikony, fonty, modele) | zmienne | tak |

### Co sprawdzić najpierw

```bash
# co siedzi w paczce, posortowane
npx asar list dist/win-unpacked/resources/app.asar > /tmp/lista.txt
wc -l /tmp/lista.txt
grep -cE '\.map$' /tmp/lista.txt          # mapy źródeł — powinno być 0
grep -E 'node_modules/[^/]+/' /tmp/lista.txt | cut -d/ -f2 | sort -u | head -40

# rozmiar zależności produkcyjnych
npx howfat -r tree 2>/dev/null || du -sh node_modules/* | sort -rh | head -20
```

### Redukcje w kolejności skuteczności

1. **Bunduj main i preload.** Bundler wciąga tylko faktycznie używany kod; `node_modules`
   w ogóle nie trafia do paczki. Typowa redukcja: 30 MB → 3 MB. To jest największa
   pojedyncza wygrana i domyślne zachowanie `electron-vite` i wtyczki Vite w Forge.

   Wyjątek: **moduły natywne muszą zostać zewnętrzne** (`external`), bo bundler nie
   spakuje `.node`:
   ```ts
   // vite.main.config.ts
   export default { build: { rollupOptions: { external: ['better-sqlite3', 'sharp'] } } };
   ```

2. **Usuń mapy źródeł z produkcji** albo publikuj je osobno (dla Sentry) i wyklucz z paczki:
   ```yaml
   files: ['out/**/*', '!**/*.map', '!**/*.ts', '!**/{test,__tests__,tests,spec}/**']
   ```

3. **Maksymalna kompresja instalatora:**
   ```yaml
   compression: maximum       # electron-builder: LZMA zamiast domyślnego
   nsis: { differentialPackage: true }
   ```
   Kosztuje 2-5× dłuższy build, daje 10-20 % mniejszy plik.

4. **Nie buduj `universal` na macOS, jeśli nie musisz.** Dwa osobne DMG (arm64, x64)
   to dwa razy po 100 MB do pobrania przez jednego użytkownika 100 MB; jeden universal
   to 190 MB dla każdego.

5. **Zasoby na żądanie.** Modele ML, słowniki, duże szablony — pobieraj przy pierwszym
   użyciu do `userData`, nie pakuj do instalatora. Pamiętaj o weryfikacji sumy kontrolnej
   pobranego pliku.

6. **`asarUnpack` tylko dla tego, co musi.** Każdy plik poza ASAR-em to osobny plik
   w instalatorze; kilkaset małych plików spowalnia instalację na Windows bardziej
   niż jeden duży.

### Czego nie robić

- **Nie usuwaj `locales/*.pak`** z paczki Electrona „bo są niepotrzebne”. Zepsujesz
  podpis kodu na macOS (zmiana zawartości bundle'a po podpisie) i stracisz obsługę
  języków, których nie przewidziałeś. Jeśli naprawdę musisz — rób to **przed** podpisem,
  przez `packagerConfig.afterCopy`.
- **Nie kompresuj `app.asar` samemu.** ASAR nie jest kompresowany celowo — dostęp
  losowy do plików bez dekompresji jest szybszy przy starcie.

## Profilowanie

### Proces główny

```bash
# profil CPU startu, do wczytania w DevTools → Performance
electron --inspect-brk=5858 .
# chrome://inspect w Chrome → Open dedicated DevTools for Node
```

Uwaga: `--inspect` wymaga fuse `enableNodeCliInspectArguments`. W buildzie produkcyjnym
z wyłączonym fuse to nie zadziała — profiluj build deweloperski albo osobny build
z włączonym fuse, nigdy nie wypuszczaj takiego do klienta.

```ts
// profil programowy, działa też w produkcji
import { app } from 'electron';
import inspector from 'node:inspector';
import fs from 'node:fs';

const sesja = new inspector.Session();
sesja.connect();
sesja.post('Profiler.enable', () => {
  sesja.post('Profiler.start', () => {
    setTimeout(() => {
      sesja.post('Profiler.stop', (_e, { profile }) => {
        fs.writeFileSync(path.join(app.getPath('logs'), 'main.cpuprofile'), JSON.stringify(profile));
      });
    }, 10_000);
  });
});
```

### Renderer

Zwykłe DevTools Chromium: Performance, Memory, Coverage. Panel Coverage pokazuje,
ile procent bundle'a jest faktycznie wykonane przy starcie — powyżej 60 % nieużywanego
kodu oznacza brak code splittingu.

### Wszystkie procesy naraz

`app.getAppMetrics()` co minutę do logu (kod wyżej). Na macOS dodatkowo
Instruments → Time Profiler z filtrem po nazwie procesu.

## Zużycie energii na macOS

macOS pokazuje „Aplikacja zużywa znaczną ilość energii” i użytkownicy to zauważają.
Główne przyczyny w aplikacjach Electronowych:

| Przyczyna | Skutek | Naprawa |
| --- | --- | --- |
| `setInterval` w rendererze przy ukrytym oknie | timer działa mimo braku widoczności | `backgroundThrottling: true` (domyślne) + własne zatrzymanie na `hide` |
| animacja CSS bez końca (spinner, gradient) | GPU pracuje bez przerwy | zatrzymaj animacje przy `blur`/`hide` |
| `requestAnimationFrame` w pętli | jw. | `document.visibilityState !== 'visible'` → przerwij pętlę |
| polling HTTP co sekundę | budzi radio Wi-Fi | WebSocket albo interwał ≥ 30 s z jitterem |
| `powerSaveBlocker` zapomniany | system nie usypia | zwolnij zawsze w `finally` |
| ciężki proces GPU (WebGL, wiele warstw) | stały pobór | ogranicz warstwy kompozycji, `will-change` tylko gdy trzeba |

```ts
import { powerSaveBlocker, powerMonitor } from 'electron';

let blokada: number | null = null;
async function dlugaOperacja() {
  blokada = powerSaveBlocker.start('prevent-app-suspension');
  try { await zrobCos(); }
  finally { if (blokada !== null) { powerSaveBlocker.stop(blokada); blokada = null; } }
}

// zawieś pracę w tle na baterii
powerMonitor.on('on-battery', () => zmniejszCzestotliwoscSynchronizacji());
powerMonitor.on('on-ac', () => przywrocCzestotliwosc());
powerMonitor.on('suspend', () => zamknijPolaczenia());
powerMonitor.on('resume', () => odtworzPolaczenia());
```

**`backgroundThrottling` jest domyślnie `true`** i dławi timery w ukrytych oknach do
1 na sekundę. Nie wyłączaj go „bo licznik się zacina” — przenieś licznik do procesu
głównego i wysyłaj wynik do renderera.

**Pomiar:** Monitor aktywności → kolumna „Wpływ na energię”; wartość poniżej 5 w spoczynku
jest akceptowalna. `pmset -g thermlog` pokazuje throttling termiczny.

## Lista kontrolna wydajności

- [ ] Czas do widocznego okna zmierzony i mieści się w budżecie na najsłabszej wspieranej
      maszynie (nie na twoim laptopie).
- [ ] Main i preload zbundlowane do pojedynczych plików.
- [ ] Żaden ciężki moduł nie jest importowany na górze `main.ts`.
- [ ] `Menu.setApplicationMenu(null)` albo własne menu ustawione po `whenReady`.
- [ ] `show: false` + `ready-to-show` + `backgroundColor`.
- [ ] Renderer ładowany z pliku lokalnego, nie z sieci.
- [ ] Brak map źródeł, testów i plików `.ts` w `app.asar`.
- [ ] `app.getAppMetrics()` po 10 minutach pracy nie pokazuje wzrostu pamięci względem
      pierwszej minuty przy tym samym stanie UI.
- [ ] Wszystkie `ipcRenderer.on` mają odpowiadający `removeListener`.
- [ ] Animacje i timery zatrzymywane przy `hide`/`blur`.
- [ ] `powerSaveBlocker` zwalniany w `finally`.
- [ ] Rozmiar instalatora porównany z poprzednim wydaniem; skok > 20 % wyjaśniony.
