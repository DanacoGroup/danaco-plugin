# Electron — indeks modułu

Moduł opisuje Electron jako alternatywę dla Tauri: API bieżącego wydania i dystrybucję
gotowej aplikacji. Danaco Console jest zbudowana na Tauri 2 — powłokę produktu opisuje
reszta paczki `most-tauri`, a ten katalog służy wyłącznie pracom w cudzym projekcie
opartym na Electronie. Karty pogłębione modułu wymienia tabela „Karty referencyjne”
poniżej; wczytuj z niej wyłącznie to, czego wymaga zadanie.

Materiał jest o **API bieżącego Electrona i o dystrybucji**. Model z pamięci pisze kod pod
Electron 20-28, używa `BrowserView`, `remote`, `nodeIntegration: true` i zakłada, że
certyfikat OV da się położyć jako `.pfx` w CI. W sierpniu 2026 każde z tych czterech
założeń jest błędne i kosztuje albo lukę bezpieczeństwa, albo tydzień na wydanie.

## Kiedy wczytać ten moduł

- Zakładasz nowy projekt desktopowy albo dodajesz warstwę desktopową do istniejącego weba.
- Piszesz kod w procesie głównym, preloadzie, kanałach IPC albo `utilityProcess`.
- Potrzebujesz dostępu do systemu: pliki, menu, tray, powiadomienia, schowek, autostart,
  protokół `myapp://`, moduł natywny (`better-sqlite3`).
- Pakujesz, podpisujesz, notaryzujesz albo publikujesz wydanie; konfigurujesz auto-update.
- Budujesz przeglądarkę, kiosk, panel z osadzonymi obcymi stronami.
- Ktoś pyta „czy to ma być Electron, czy Tauri” albo „czemu to waży 240 MB”.

**Nie używaj gdy:** pytanie dotyczy wyglądu interfejsu, kolorów, typografii — to
`../design-systemowy/SKILL.md`. Kod komponentów w rendererze — `../ui-ux-pro/SKILL.md`. Podział
systemu na usługi, granice modułów, decyzje architektoniczne —
`../architektura-i-dokumentacja/references/engineering-core/przeglad.md`.

## Granice

| Temat | Materiał właściwy |
| --- | --- |
| Estetyka okna, ikony w UI, kompozycja, motyw ciemny | `../design-systemowy/SKILL.md` |
| Komponenty w rendererze, TypeScript, Tailwind, stan | `../ui-ux-pro/SKILL.md` · `../kodowanie/references/jezyki-programowania/javascript-typescript.md` |
| Podział na usługi, granice kontekstów, ADR | `../architektura-i-dokumentacja/references/engineering-core/przeglad.md` |
| Backend, do którego aplikacja dzwoni | `../kodowanie/references/engineering-core/05-uslugi-sieciowe/przeglad.md` |
| SQLite jako baza wiedzy, wektory, RAG lokalnie | `../kodowanie/references/engineering-core/04-bazy-i-rag/przeglad.md` |
| CI/CD ogólnie, testy jednostkowe | `../kodowanie/references/engineering-core/07-debug-testy-deploy/przeglad.md` |

Tu należy wszystko, co jest **specyficzne dla środowiska desktopowego**: proces główny,
IPC, pakowanie, podpisywanie, natywne API. Jeśli ten sam kod działałby na serwerze — to
nie tutaj.

## Wersje odniesienia (zweryfikowane 2026-08-04: registry npm, releases.electronjs.org, docs)

| Pakiet | Wersja | Uwaga krytyczna |
| --- | --- | --- |
| `electron` | **43.2.0** (2026-07-21) | Chromium 150.0.7871.129, Node 24.18.0, V8 15.0, ABI `modules` 148 |
| `electron` 42.x | 42.8.0 | Chromium 148, Node 24.18, ABI 146 |
| `electron` 41.x | 41.10.3 | Chromium 146, Node 24.14+, ABI 145 — **koniec wsparcia ok. 2026-08-25** |
| `@electron-forge/cli` | **7.11.2** | Rekomendowany przez zespół Electrona; makery i publishery w jednym |
| `electron-builder` | **26.15.3** | Alternatywa; jedyna droga do AppImage i delta na NSIS |
| `electron-updater` | **6.8.9** | Idzie z electron-builderem, nie z Forge |
| `update-electron-app` | **3.3.0** | Owija `autoUpdater`; wymaga publicznego repo GitHub |
| `@electron/fuses` | **2.1.3** | `flipFuses`, `npx @electron/fuses read` |
| `@electron/notarize` | **3.1.1** | `notarytool` (`altool` martwe od 2023) |
| `@electron/osx-sign` | **2.6.0** | Podpis macOS |
| `@electron/windows-sign` | **2.0.6** | Wspólna warstwa podpisu Windows dla Forge |
| `@electron/rebuild` | **4.2.0** | Przebudowa modułów natywnych pod ABI Electrona |
| `@electron/asar` | **4.2.1** | ASAR integrity wymaga ≥ 3.1.0 |
| `electron-vite` | **5.0.0** | Bundler main+preload+renderer, niezależny od Forge |
| `better-sqlite3` | **13.0.2** | Typowy moduł natywny; wymaga rebuildu |
| `electron-store` | **11.0.2** | Konfiguracja użytkownika (nadbudowa `conf` 15.x) |
| `electron-log` | **5.4.4** | Log do pliku w `app.getPath('logs')` |
| `@tauri-apps/cli` / `tauri` | **2.11.4 / 2.11.5** | Alternatywa — patrz `references/electron-desktop/references/alternatywy.md` |

**Wsparcie:** trzy najnowsze majory (43, 42, 41). Nowy major co ~8 tygodni. E44 planowany
ok. 2026-08-25 — wtedy 41 wypada. Zasada firmowa: **nie schodź poniżej N-1**, bo łatki
bezpieczeństwa Chromium trafiają tylko do wspieranych linii.

**Zmiany, o których model nie wie:**
- E42: pakiet `electron` **nie pobiera binariów w `postinstall`** — pobiera przy pierwszym
  uruchomieniu; `ELECTRON_SKIP_BINARY_DOWNLOAD` nie działa. Obrazy CI bez sieci przy
  `npm start` się wywalą.
- E42: powiadomienia macOS przeszły na `UNNotification` — **aplikacja musi być podpisana**,
  inaczej powiadomienia nie działają nawet w dev.
- E43: `dialog.showOpenDialog`/`showSaveDialog` domyślnie otwierają katalog Pobrane,
  a nie ostatnio używany. Jeśli chcesz stary UX — trzymaj ścieżkę sam i podaj `defaultPath`.
- E44 (nadchodzi): koniec macOS 12, koniec `ia32` na Windows i `armv7l` na Linuksie,
  moduł `clipboard` **znika z renderera** (zostaje `navigator.clipboard` + preload).

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
| --- | --- | --- |
| `references/electron-desktop/references/architektura-procesow.md` | Proces główny / renderer / preload / utility, `app.whenReady`, cykl życia okien i aplikacji, model wielookienny, single instance, zachowanie per system (dock, tray), gdzie trzymać stan i konfigurację | Zakładasz projekt, dodajesz okno, walczysz z zamykaniem aplikacji |
| `references/electron-desktop/references/ipc-i-preload.md` | `contextBridge`, `ipcMain.handle`/`invoke`, zdarzenia jednokierunkowe, `MessagePort`, strumienie i duże dane, typowanie kanałów w TS, walidacja wejścia i `sender`, wzorce błędne | Piszesz cokolwiek, co przechodzi granicę procesów |
| `references/electron-desktop/references/bezpieczenstwo.md` | Pełna lista kontrolna: `contextIsolation`, `sandbox`, CSP, blokowanie nawigacji i `window.open`, uprawnienia, `webSecurity`, fuses, ASAR integrity, sekrety w aplikacji desktopowej, aktualizacja jako wektor ataku | Przed każdym wydaniem; przy każdym `webPreferences` |
| `references/electron-desktop/references/warstwa-natywna.md` | System plików, dialogi, menu i skróty, powiadomienia, schowek, tray, protokoły `myapp://`, rejestracja typów plików, autostart, TCC na macOS, moduły natywne, `node-gyp`, `better-sqlite3`, ABI | Sięgasz po cokolwiek spoza przeglądarki |
| `references/electron-desktop/references/budowanie-i-podpisywanie.md` | Forge vs builder, cele instalacyjne, ikony i metadane, wieloplatformowość i jej granice, podpis macOS + notaryzacja + stapling, podpis Windows (token/HSM/Azure), Linux, CI wydań | Pakujesz, podpisujesz, konfigurujesz pipeline wydania |
| `references/electron-desktop/references/aktualizacje.md` | Kanały, wersjonowanie, `electron-updater` (github/s3/generic, delta, `stagingPercentage`), `update-electron-app`, aktualizacje wymuszone, migracje danych użytkownika, wycofanie wadliwego wydania, telemetria awarii | Wdrażasz albo naprawiasz auto-update |
| `references/electron-desktop/references/wydajnosc-i-rozmiar.md` | Czas startu, lazy loading, code cache i snapshoty V8, pamięć przy wielu oknach, rozmiar instalatora, `asarUnpack`, profilowanie, zużycie energii na macOS | „Wolno startuje”, „za duże”, „laptop grzeje” |
| `references/electron-desktop/references/przegladarka-i-osadzanie.md` | `WebContentsView`, karty, nawigacja i historia, sesje i partycje, ciasteczka, `webRequest`, blokowanie treści, wstrzykiwanie skryptów, kiosk, druk i PDF, pobierania, zdalne treści a bezpieczeństwo | Budujesz przeglądarkę, kiosk albo osadzasz obcą stronę |
| `references/electron-desktop/references/alternatywy.md` | Tauri 2, Wails, Neutralino, PWA, .NET MAUI — tabela porównawcza z liczbami, kiedy któreś bije Electrona, ścieżka migracji | Przed decyzją o stacku; gdy klient pyta o rozmiar/RAM |

## Procedura

1. **Rozstrzygnij, czy to ma być Electron.** Odpowiedz na pięć pytań poniżej („Electron czy nie”).
   Jeśli wynik to „nie” — otwórz `references/electron-desktop/references/alternatywy.md` i uzasadnij
   wybór pisemnie. Nie zaczynaj kodu przed tym krokiem.
2. **Ustal wersję.** W istniejącym repo `package.json` wygrywa nad tabelą wyżej. W nowym —
   `electron@43`. Sprawdź `npm show electron version` zamiast zgadywać.
3. **Postaw szkielet** (polecenia niżej). Wybierz Forge albo electron-builder od razu —
   zamiana w połowie projektu kosztuje dzień.
4. **Zaprojektuj granicę procesów przed pisaniem funkcji.** Wypisz listę operacji, które
   renderer musi zlecić głównemu procesowi. To jest kontrakt IPC. Patrz
   `references/electron-desktop/references/ipc-i-preload.md`.
5. **Ustaw `webPreferences` raz, poprawnie, i nie ruszaj.** Domyślne wartości w E43 są
   bezpieczne — każde odstępstwo wymaga komentarza w kodzie z uzasadnieniem.
6. **Warstwa natywna dopiero po IPC.** Menu, tray, dialogi żyją w procesie głównym i są
   wywoływane z renderera przez `invoke`, nigdy odwrotnie.
7. **Pakuj i podpisuj od pierwszego tygodnia, nie na końcu.** Certyfikat Developer ID i
   konto Azure Artifact Signing mają czas oczekiwania liczony w dniach do tygodni.
   `references/electron-desktop/references/budowanie-i-podpisywanie.md`.
8. **Włącz fuses i ASAR integrity przed pierwszym wydaniem publicznym.** Po wydaniu
   zmiana fuses to zmiana podpisu i pełna reinstalacja u części użytkowników.
9. **Auto-update z kanałem i wersjonowaniem od pierwszego wydania.** Dołożenie
   auto-update do aplikacji, która jest już u ludzi bez niego, wymaga ręcznej migracji.
10. **Przejdź listę kontrolną z `references/electron-desktop/references/bezpieczenstwo.md`** i
    sekcję „Kontrola przed oddaniem” niżej.

## Electron czy nie — pięć pytań

Odpowiedz na wszystkie. Trzy „tak” w kolumnie prawej = rozważ alternatywę.

| Pytanie | Electron | Rozważ alternatywę |
| --- | --- | --- |
| Czy aplikacja musi renderować identycznie na trzech systemach (edytor, narzędzie do treści, przeglądarka)? | tak | nie — Tauri wystarczy |
| Czy zespół zna wyłącznie JS/TS i nie ma czasu na Rusta/Go? | tak | nie — jest Rust/Go w zespole |
| Czy 80-250 MB instalatora i ~150-400 MB RAM jest akceptowalne? | tak | nie — narzędzie ma być lekkie, tray, agent |
| Czy potrzebujesz konkretnych API Chromium (WebRTC, WebGPU, rozszerzenia, PDF viewer, `webRequest`)? | tak | nie — starczy zwykły HTML |
| Czy aplikacja jest w istocie stroną, którą da się zainstalować jako PWA? | nie | tak — zrób PWA, oszczędzisz cały ten moduł |

Dwa twarde przypadki, gdzie **Electron jest jedynym rozsądnym wyborem**: (1) budujesz
przeglądarkę albo kiosk z pełną kontrolą nad silnikiem i `webRequest`; (2) potrzebujesz
tego samego zachowania renderowania co Chrome, bo aplikacja pokazuje obce treści.

Twardy przypadek, gdzie **Electron jest złym wyborem**: rezydentne narzędzie w tray,
które ma stać 8 godzin i nie zjadać pamięci. Tam Tauri albo natywny kod.

## Szkielet projektu — dokładne polecenia

### Wariant A: Electron Forge + Vite + TypeScript (domyślny dla nowych projektów)

```bash
npm create electron-app@latest moja-aplikacja -- --template=vite-typescript
cd moja-aplikacja
npm install
npm start                 # dev z HMR renderera
npm run package           # katalog out/ — aplikacja bez instalatora
npm run make              # out/make/ — instalatory pod bieżący system
npm run publish           # wysyłka do skonfigurowanego publishera
```

Dodaj od razu bezpieczne domyślne ustawienia i fuses:

```bash
npm install --save-dev @electron-forge/plugin-fuses @electron/fuses
```

```ts
// forge.config.ts
import type { ForgeConfig } from '@electron-forge/shared-types';
import { FusesPlugin } from '@electron-forge/plugin-fuses';
import { FuseV1Options, FuseVersion } from '@electron/fuses';
import { MakerSquirrel } from '@electron-forge/maker-squirrel';
import { MakerDMG } from '@electron-forge/maker-dmg';
import { MakerDeb } from '@electron-forge/maker-deb';
import { MakerRpm } from '@electron-forge/maker-rpm';
import { VitePlugin } from '@electron-forge/plugin-vite';

const config: ForgeConfig = {
  packagerConfig: {
    asar: true,                       // wymagane dla ASAR integrity
    icon: 'assets/icon',              // bez rozszerzenia: .ico/.icns/.png
    appBundleId: 'pl.danaco.moja-aplikacja',
    appCategoryType: 'public.app-category.productivity',
    extendInfo: { NSCameraUsageDescription: 'Skanowanie kodów QR.' },
  },
  makers: [
    new MakerSquirrel({ name: 'moja_aplikacja' }),
    new MakerDMG({ format: 'ULFO' }),
    new MakerDeb({ options: { maintainer: 'DANACO', homepage: 'https://danacogroup.com.pl' } }),
    new MakerRpm({ options: {} }),
  ],
  plugins: [
    new VitePlugin({
      build: [
        { entry: 'src/main.ts', config: 'vite.main.config.ts', target: 'main' },
        { entry: 'src/preload.ts', config: 'vite.preload.config.ts', target: 'preload' },
      ],
      renderer: [{ name: 'main_window', config: 'vite.renderer.config.ts' }],
    }),
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: false,
      [FuseV1Options.EnableCookieEncryption]: true,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
    }),
  ],
};
export default config;
```

### Wariant B: electron-vite + electron-builder (gdy potrzebujesz AppImage, MSI z WiX-em bez Forge albo delta na NSIS)

```bash
npm create @quick-start/electron@latest moja-aplikacja
# wybierz: TypeScript -> React (albo vanilla)
cd moja-aplikacja && npm install
npm run dev
npm run build:win     # / build:mac / build:linux
```

`electron-builder.yml` minimum produkcyjne:

```yaml
appId: pl.danaco.moja-aplikacja
productName: Moja Aplikacja
directories: { output: dist, buildResources: build }
files: ['out/**/*', 'resources/**/*', '!**/*.map']
asar: true
electronFuses:
  runAsNode: false
  enableNodeOptionsEnvironmentVariable: false
  enableNodeCliInspectArguments: false
  enableCookieEncryption: true
  enableEmbeddedAsarIntegrityValidation: true
  onlyLoadAppFromAsar: true
mac:
  category: public.app-category.productivity
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  notarize: { teamId: XXXXXXXXXX }
  target: [{ target: dmg, arch: [arm64, x64] }, { target: zip, arch: [arm64, x64] }]
win:
  target: [{ target: nsis, arch: [x64, arm64] }]
  sign: { type: azure }
linux:
  target: [AppImage, deb, rpm]
  category: Utility
publish: { provider: generic, url: 'https://wydania.danacogroup.com.pl/moja-aplikacja' }
```

### Wybór narzędzia — decyzja w jednym zdaniu

Forge, jeśli chcesz być blisko oficjalnego łańcucha (`@electron/packager`,
`@electron/windows-sign`, `@electron/notarize`) i wystarczą ci Squirrel/MSI/dmg/deb/rpm.
electron-builder, jeśli potrzebujesz AppImage, aktualizacji delta na Windows, `pacman`,
albo gotowego `electron-updater` bez własnego serwera. **Electron nie rekomenduje
oficjalnie żadnego z nich** — dokumentacja opisuje oba neutralnie. Forge jest projektem
organizacji `electron/`, electron-builder jest społecznościowy.

## Twarde reguły

1. **`nodeIntegration: true` w oknie ładującym cokolwiek zdalnego jest zakazane.** Skutek:
   dowolny XSS na tej stronie to wykonanie kodu z prawami użytkownika, w tym `child_process`.
2. **`contextIsolation: false` jest zakazane.** Domyślnie `true` od E12; wyłączenie znosi
   izolację świata preloadu i pozwala stronie nadpisać wystawione funkcje.
3. **`sandbox: false` wymaga pisemnego uzasadnienia w komentarzu.** Domyślnie `true` od E20.
   Sandboxowany preload nie może używać ESM ani większości `require` — to jest cena, którą
   płacisz świadomie.
4. **Nie używaj `@electron/remote`.** Moduł istnieje (2.1.3), ale przywraca dokładnie ten
   model zagrożeń, który usunięto z rdzenia. Skutek: renderer dostaje uchwyt do obiektów
   procesu głównego.
5. **Nie wystawiaj `ipcRenderer` ani `fs` przez `contextBridge`.** Wystawiaj funkcje o
   wąskim kontrakcie. Skutek wystawienia `ipcRenderer.invoke`: strona woła dowolny kanał,
   w tym te, o których zapomniałeś.
6. **Waliduj `event.senderFrame` w każdym `ipcMain.handle`.** Bez tego osadzona ramka
   z obcej domeny woła twoje API systemowe.
7. **`BrowserView` jest przestarzały od E29.** Nowy kod: `BaseWindow` + `WebContentsView`.
   `BrowserView` nadal działa w E43, ale nie dostaje poprawek i zniknie.
8. **`<webview>` tylko wtedy, gdy `WebContentsView` naprawdę nie wystarcza.** Dokumentacja
   Electrona odradza go wprost z powodu niestabilności renderowania i routingu zdarzeń;
   `webviewTag` domyślnie `false`.
9. **Nie ma bezpiecznego miejsca na sekret w aplikacji desktopowej.** Klucz API w kodzie,
   w `asar`, w zmiennej środowiskowej albo w `safeStorage` — wszystko jest do wyjęcia przez
   właściciela maszyny. Sekrety zostają na serwerze; aplikacja dostaje token użytkownika.
10. **Aplikacja niepodpisana nie idzie do klienta.** Na macOS Gatekeeper ją zablokuje, na
    Windows SmartScreen pokaże ostrzeżenie, a od E42 powiadomienia macOS w ogóle nie działają
    bez podpisu.
11. **`asar: true` zawsze**, z `asarUnpack` dla `.node` i binariów. Bez ASAR-a instalator
    ma dziesiątki tysięcy plików i instaluje się minutami na Windows.
12. **Moduły natywne przebudowuj pod ABI Electrona**, nie pod ABI Node. E43 ma
    `process.versions.modules === '148'`. Skutek pominięcia: `NODE_MODULE_VERSION mismatch`
    przy pierwszym `require`.
13. **Nie pisz do katalogu instalacji.** Dane użytkownika idą do `app.getPath('userData')`,
    logi do `app.getPath('logs')`, cache do `app.getPath('cache')`.
14. **Jedno źródło prawdy o wersji: `package.json`.** `app.getVersion()` czyta stamtąd;
    nie duplikuj numeru w kodzie ani w konfiguracji aktualizacji.

## Kontrola przed oddaniem

- [ ] `webPreferences` każdego okna: `contextIsolation: true`, `sandbox: true`,
      `nodeIntegration: false`, `webSecurity: true`, `webviewTag: false`. Odstępstwa
      opisane komentarzem.
- [ ] CSP zdefiniowana i nie zawiera `unsafe-eval`; sprawdzona w DevTools (brak ostrzeżenia
      „Insecure Content-Security-Policy” w konsoli).
- [ ] `contents.setWindowOpenHandler` zwraca `{ action: 'deny' }` dla wszystkiego, czego nie
      przewidziałeś; `will-navigate` blokuje nawigację poza listę dozwoloną.
- [ ] Każdy `ipcMain.handle` waliduje typ argumentów i `senderFrame`.
- [ ] `contextBridge` wystawia funkcje, nie obiekty Electrona; żaden `fs`, `path`,
      `child_process`, `ipcRenderer` nie trafia do `window`.
- [ ] `session.setPermissionRequestHandler` ustawiony; domyślnie odmawia.
- [ ] Fuses: `runAsNode`, `nodeOptions`, `nodeCliInspect` wyłączone;
      `embeddedAsarIntegrityValidation` i `onlyLoadAppFromAsar` włączone. Zweryfikowane
      przez `npx @electron/fuses read --app <ścieżka>`.
- [ ] macOS: podpis Developer ID, hardened runtime, entitlements minimalne, notaryzacja
      przeszła, `xcrun stapler validate` zielone.
- [ ] Windows: podpis z tokenu/HSM/Azure obecny na `.exe` **i** na instalatorze;
      `signtool verify /pa /v` przechodzi.
- [ ] Auto-update: kanał ustawiony, plik `latest*.yml` publikowany razem z artefaktami,
      przetestowana ścieżka z wersji poprzedniej do bieżącej na czystej maszynie.
- [ ] Rozmiar instalatora znany i uzasadniony; `npx asar list` nie pokazuje `node_modules`
      narzędzi deweloperskich, map źródeł ani testów.
- [ ] Migracja danych użytkownika ma numer schematu i test „stary profil → nowa wersja”.
- [ ] Aplikacja startuje bez sieci i nie blokuje procesu głównego dłużej niż 100 ms
      w jednym kroku.
- [ ] Wersja Electrona jest jedną z trzech wspieranych (43, 42, 41 w sierpniu 2026).
