# Aktualizacje

Odniesienie: `electron-updater` 6.8.9, `update-electron-app` 3.3.0, `electron-builder` 26.15.3,
Electron 43.2.0.

## Wybór mechanizmu

| Mechanizm | Kiedy | Ograniczenia |
| --- | --- | --- |
| `update-electron-app` + `update.electronjs.org` | projekt open source na publicznym GitHubie | **wymaga publicznego repo**; tylko macOS i Windows; macOS wymaga podpisu; brak delta, brak kanałów, brak stopniowego wdrażania |
| `update-electron-app` + własny serwer | Forge, prywatny kod | musisz postawić serwer zgodny ze Squirrelem (Nucleus, ERS, Hazel) |
| **`electron-updater`** + electron-builder | domyślny wybór firmowy | tylko z electron-builderem; Windows tylko NSIS |
| `autoUpdater` z rdzenia Electrona | pełna kontrola, egzotyczne przypadki | musisz sam obsłużyć feed, wersje, Linuksa |
| brak auto-update | MSI wdrażane przez IT, Flatpak, Snap, sklepy | aktualizuje kanał dystrybucji |

Dla aplikacji zamkniętych DANACO: **`electron-updater` z providerem `generic` (własny serwer
statyczny) albo `s3`/`r2`.** Provider `github` wymaga publicznego repo albo tokenu w aplikacji —
token w aplikacji desktopowej jest publiczny (patrz
`references/electron-desktop/references/bezpieczenstwo.md`), więc `github` do prywatnych wydań nie
nadaje się.

## Wersjonowanie i kanały

`package.json` → `version` jest **jedynym** źródłem prawdy. `app.getVersion()` czyta stamtąd.

Semver z prereleasem wyznacza kanał automatycznie w `electron-updater`:

| Wersja | Kanał | Kto dostaje |
| --- | --- | --- |
| `1.4.2` | `latest` | wszyscy |
| `1.5.0-beta.1` | `beta` | tylko `channel: 'beta'` |
| `1.5.0-alpha.3` | `alpha` | tylko `channel: 'alpha'` |

```ts
import { autoUpdater } from 'electron-updater';

autoUpdater.channel = ustawienia.get('kanal') ?? 'latest';
autoUpdater.allowPrerelease = autoUpdater.channel !== 'latest';
autoUpdater.allowDowngrade = false;    // domyślnie false; zostaw
```

Kanał `alpha` widzi też `beta` i `latest`; `beta` widzi `latest`. To jest hierarchia
wbudowana — użytkownik na becie dostanie stabilne 1.4.3, jeśli jest nowsze niż jego beta.

Pliki metadanych generowane przez electron-builder i publikowane razem z artefaktami:
`latest.yml` (Windows), `latest-mac.yml` (macOS), `latest-linux.yml` (Linux, AppImage).
Dla kanałów: `beta.yml`, `beta-mac.yml` itd. **Brak któregoś pliku = cicha awaria
aktualizacji na tej platformie.**

## Konfiguracja publikacji

```yaml
# electron-builder.yml
publish:
  provider: generic
  url: https://wydania.danacogroup.com.pl/moja-aplikacja/${channel}
  channel: latest
```

Warianty:

```yaml
# S3
publish: { provider: s3, bucket: danaco-wydania, region: eu-central-1, path: moja-aplikacja }
# Cloudflare R2
publish: { provider: spaces, name: danaco-wydania, region: auto, path: moja-aplikacja }
# GitHub (tylko publiczne repo)
publish: { provider: github, owner: danaco, repo: moja-aplikacja }
```

Serwer `generic` to zwykły serwer statyczny. Wymagania: HTTPS, poprawny `Content-Length`,
obsługa `Range` (dla delta), brak agresywnego cache na `latest*.yml`
(`Cache-Control: no-cache` na plikach `.yml`, długi cache na binariach z hashem w nazwie).

## Kod w procesie głównym

```ts
// src/main/aktualizacje.ts
import { autoUpdater, type UpdateInfo, type ProgressInfo } from 'electron-updater';
import { app, dialog, BrowserWindow } from 'electron';
import log from 'electron-log';

autoUpdater.logger = log;
log.transports.file.level = 'info';

autoUpdater.autoDownload = false;          // pytamy użytkownika przed pobraniem
autoUpdater.autoInstallOnAppQuit = true;   // instaluj przy zamknięciu, nie w trakcie pracy

export function uruchomAktualizacje(okno: BrowserWindow) {
  if (!app.isPackaged) return;             // w dev nie ma czego aktualizować
  if (process.platform === 'linux' && !process.env.APPIMAGE) return;  // deb/rpm: aktualizuje menedżer pakietów

  autoUpdater.on('checking-for-update', () => log.info('Sprawdzam aktualizacje'));

  autoUpdater.on('update-available', async (info: UpdateInfo) => {
    const { response } = await dialog.showMessageBox(okno, {
      type: 'info',
      buttons: ['Pobierz teraz', 'Później'],
      defaultId: 0, cancelId: 1,
      message: `Dostępna wersja ${info.version}`,
      detail: info.releaseNotes ? String(info.releaseNotes).slice(0, 500) : undefined,
    });
    if (response === 0) autoUpdater.downloadUpdate();
  });

  autoUpdater.on('update-not-available', () => log.info('Wersja aktualna'));

  autoUpdater.on('download-progress', (p: ProgressInfo) => {
    if (!okno.isDestroyed()) {
      okno.setProgressBar(p.percent / 100);
      okno.webContents.send('aktualizacja:postep', Math.round(p.percent));
    }
  });

  autoUpdater.on('update-downloaded', async (info: UpdateInfo) => {
    okno.setProgressBar(-1);
    const { response } = await dialog.showMessageBox(okno, {
      type: 'info',
      buttons: ['Uruchom ponownie', 'Przy następnym starcie'],
      defaultId: 0, cancelId: 1,
      message: `Wersja ${info.version} gotowa do instalacji`,
    });
    if (response === 0) {
      aplikacjaSieZamyka = true;             // pomiń własny handler 'close'
      setImmediate(() => autoUpdater.quitAndInstall(false, true));
    }
  });

  autoUpdater.on('error', (err) => {
    log.error('Błąd aktualizacji', err);
    // NIE pokazuj dialogu — brak sieci to normalny stan, nie awaria
  });

  autoUpdater.checkForUpdates();
  setInterval(() => autoUpdater.checkForUpdates(), 4 * 60 * 60 * 1000);   // co 4 h
}
```

Cztery decyzje w tym kodzie, które są nieoczywiste:

1. **`autoDownload = false`.** Domyślne `true` pobiera 100-200 MB w tle bez pytania —
   na łączu mobilnym albo w firmie z limitem to jest problem.
2. **`quitAndInstall` w `setImmediate`.** Wywołane synchronicznie w handlerze dialogu
   potrafi zawiesić proces na Windows, bo Squirrel/NSIS startuje zanim Electron zdąży
   posprzątać.
3. **`quitAndInstall(false, true)`** — pierwszy argument `isSilent` na Windows,
   drugi `isForceRunAfter` (uruchom po instalacji). Bez `true` w drugim aplikacja
   nie wstanie sama i użytkownik pomyśli, że się zepsuła.
4. **Błąd aktualizacji nie jest widoczny dla użytkownika.** Serwer niedostępny, brak
   sieci, VPN blokujący — to zdarza się codziennie. Dialog przy każdym takim zdarzeniu
   nauczy użytkownika ignorować dialogi.

**Sprawdzanie przy starcie:** odczekaj 10-30 sekund po `ready`, żeby nie konkurować
o pasmo i CPU z pierwszym renderem.

## Aktualizacje delta

`electron-updater` obsługuje różnicowe pobieranie:

- **Windows NSIS:** blokowe różnice względem zainstalowanej wersji. Wymaga, żeby poprzednia
  wersja była zbudowana tym samym electron-builderem i żeby pliki `.blockmap` były
  opublikowane obok instalatorów. Typowa oszczędność: 90 % przy zmianie samego kodu
  aplikacji, ~0 % przy podniesieniu Electrona (zmienia się cała binarka).
- **macOS:** różnice na poziomie plików w `.zip`. Wymaga publikacji `.zip` obok `.dmg`.
- **Linux AppImage:** delta przez `zsync`, wymaga pliku `.AppImage.zsync`.

Blokowanie delta (gdy powoduje problemy):

```yaml
nsis: { differentialPackage: false }
```

**Jeśli delta się nie powiedzie, updater pobiera pełny plik** — to nie jest błąd
krytyczny, ale sprawdź logi, bo cicha degradacja do pełnego pobrania przy każdej
aktualizacji to marnowanie pasma użytkowników.

## Stopniowe wdrażanie

```yaml
# w latest.yml, dodawane ręcznie po publikacji albo przez skrypt
stagingPercentage: 10
```

`electron-updater` liczy stabilny identyfikator z UUID zapisanego w `userData` i
porównuje z progiem — ten sam użytkownik zawsze wpada w tę samą grupę, więc podniesienie
z 10 do 50 % nie przetasowuje odbiorców.

Procedura firmowa dla wydania z ryzykiem:

1. Publikuj z `stagingPercentage: 5`, obserwuj telemetrię awarii przez 24 h.
2. Brak wzrostu awarii → 25 %, kolejne 24 h.
3. → 100 %.
4. Wzrost awarii na dowolnym etapie → usuń `latest.yml` (patrz „wycofanie”).

## Aktualizacje wymuszone

Aplikacja z API po stronie serwera prędzej czy później dojdzie do momentu, gdy stary
klient musi przestać działać (zmiana protokołu, luka bezpieczeństwa, zmiana prawna).

Wzorzec: serwer zwraca w każdej odpowiedzi minimalną obsługiwaną wersję.

```ts
type OdpowiedzApi<T> = { dane: T; minimalnaWersjaKlienta: string; zalecanaWersja: string };

function sprawdzWersje(odp: OdpowiedzApi<unknown>) {
  const moja = app.getVersion();
  if (semver.lt(moja, odp.minimalnaWersjaKlienta)) {
    zablokujInterfejs({
      tytul: 'Wymagana aktualizacja',
      tresc: `Ta wersja (${moja}) nie jest już obsługiwana. Zaktualizuj do ${odp.zalecanaWersja}.`,
      akcja: () => autoUpdater.checkForUpdatesAndNotify(),
    });
  }
}
```

Zasady:
- **Blokada dotyczy funkcji sieciowych, nie całej aplikacji.** Użytkownik musi móc
  odczytać i wyeksportować swoje lokalne dane nawet z zablokowanej wersji.
- **Zapowiedz z wyprzedzeniem.** Baner „ta wersja przestanie działać 1 października”
  przez dwa tygodnie przed twardą blokadą.
- **Miej ścieżkę ratunkową dla Linuksa deb/rpm**, gdzie auto-update nie działa —
  link do pobrania w komunikacie blokady.

## Migracje danych użytkownika

Każda struktura danych trwałych ma numer schematu. Migracja jest jednokierunkowa
(w przód) i idempotentna.

```ts
// src/main/migracje.ts
import Store from 'electron-store';
import Database from 'better-sqlite3';

const WERSJA_SCHEMATU = 5;

export function migruj(db: Database.Database) {
  const obecna = db.pragma('user_version', { simple: true }) as number;
  if (obecna === WERSJA_SCHEMATU) return;
  if (obecna > WERSJA_SCHEMATU) {
    throw new Error(
      `Dane pochodzą z nowszej wersji programu (schemat ${obecna} > ${WERSJA_SCHEMATU}). ` +
      'Zaktualizuj program albo przywróć kopię zapasową.',
    );
  }

  kopiaZapasowa(db);                        // przed czymkolwiek

  const kroki: Record<number, (d: Database.Database) => void> = {
    1: (d) => d.exec('ALTER TABLE dokument ADD COLUMN tagi TEXT'),
    2: (d) => d.exec('CREATE INDEX idx_dokument_utworzono ON dokument(utworzono)'),
    3: (d) => d.exec('CREATE TABLE zalacznik (id INTEGER PRIMARY KEY, dokument_id INTEGER NOT NULL REFERENCES dokument(id))'),
    4: (d) => d.exec("UPDATE dokument SET tagi = '[]' WHERE tagi IS NULL"),
    5: (d) => d.exec('ALTER TABLE dokument ADD COLUMN wersja INTEGER NOT NULL DEFAULT 1'),
  };

  const transakcja = db.transaction(() => {
    for (let v = obecna + 1; v <= WERSJA_SCHEMATU; v++) {
      kroki[v]?.(db);
      db.pragma(`user_version = ${v}`);
    }
  });
  transakcja();
}
```

Trzy reguły, które ratują dane:

1. **Kopia zapasowa przed migracją**, do `userData/kopie/dane-<wersja>-<data>.db`.
   Trzymaj trzy ostatnie. Bez tego nieudana migracja to utrata danych klienta.
2. **Wykryj dane z nowszej wersji i odmów.** Użytkownik, który zainstalował betę,
   a potem wrócił do stabilnej, ma na dysku schemat 7 przy programie oczekującym 5.
   Otwarcie takiego pliku „na siłę” niszczy dane.
3. **Migracja przed pierwszym oknem.** Uruchom w `whenReady`, przed `createWindow`;
   jeśli trwa dłużej niż sekundę, pokaż okno postępu (`BrowserWindow` bez ramki
   z paskiem), nie zostawiaj użytkownika przed pustym ekranem.

**Zmiana `productName` zmienia katalog `userData`** — dla użytkownika to wygląda jak
utrata wszystkich danych. Jeśli musisz zmienić nazwę: przy pierwszym starcie sprawdź
istnienie starego katalogu i przenieś go.

## Wycofanie wadliwego wydania

Kolejność, w minutach od wykrycia:

1. **Usuń albo podmień `latest*.yml`** na serwerze wydań, przywracając wpis poprzedniej
   wersji. To zatrzymuje nowe pobrania natychmiast — updater czyta ten plik przy każdym
   sprawdzeniu. **Nie usuwaj binariów** — ci, którzy są w trakcie pobierania, dostaną 404
   i błąd zamiast czystego przerwania.
2. **Nie zdejmuj wersji z listy** przez podniesienie numeru wstecz. `allowDowngrade`
   jest domyślnie `false`, więc użytkownicy, którzy już zainstalowali 1.4.2, nie wrócą
   do 1.4.1 automatycznie.
3. **Wydaj 1.4.3 z poprawką albo z rewertem** i opublikuj jako nowy `latest`. To jedyna
   droga powrotu dla tych, którzy już mają wadliwą wersję.
4. Jeśli wada powoduje utratę danych — dodaj do 1.4.3 kod naprawczy uruchamiany raz
   przy starcie (flaga w `electron-store`), a nie polegaj na tym, że użytkownik
   przywróci kopię.

**Czego nie da się zrobić:** cofnąć instalacji zdalnie. Nie ma mechanizmu „odinstaluj”.
Wydanie, które trafiło do 100 % użytkowników i psuje dane, jest incydentem — patrz
procedura incydentu w `../kodowanie/references/engineering-core/07-debug-testy-deploy/przeglad.md`.

## Telemetria awarii

```ts
import { crashReporter, app } from 'electron';

// PRZED app.whenReady, żeby łapać awarie startu
crashReporter.start({
  submitURL: 'https://awarie.danacogroup.com.pl/zgloszenia',
  productName: 'Moja Aplikacja',
  uploadToServer: ustawienia.get('telemetria') === true,   // zgoda użytkownika
  compress: true,
  extra: { wersja: app.getVersion(), kanal: autoUpdater.channel ?? 'latest' },
});
```

- Zrzuty trafiają do `app.getPath('crashDumps')` niezależnie od `uploadToServer` —
  możesz je odczytać przy zgłoszeniu użytkownika, nawet gdy odmówił wysyłki.
- **Zgoda jest wymagana (RODO).** `uploadToServer: false` domyślnie, przełącznik
  w ustawieniach, informacja co jest wysyłane.
- `extra` ma limit rozmiaru i **nie może zawierać danych osobowych** — zrzut pamięci
  i tak może je zawierać, więc retencja po stronie serwera musi być krótka.

Uzupełnij zrzuty o zdarzenia, których crashReporter nie łapie:

```ts
// renderer padł bez zrzutu (OOM, kill)
wc.on('render-process-gone', (_e, d) => log.error('render-process-gone', d));
// proces GPU
app.on('child-process-gone', (_e, d) => log.error('child-process-gone', d));
// nieobsłużone odrzucenia w mainie
process.on('unhandledRejection', (r) => log.error('unhandledRejection', r));
```

**Metryki, które faktycznie mówią, czy wydanie jest dobre:**

| Metryka | Skąd | Próg alarmowy |
| --- | --- | --- |
| awarie na 1000 sesji | crashReporter | wzrost > 50 % wobec poprzedniej wersji |
| udane aktualizacje / rozpoczęte | zdarzenia `update-downloaded` vs `quitAndInstall` | < 80 % |
| czas do pierwszego okna | własny pomiar `ready-to-show` minus start | wzrost > 30 % |
| liczba uruchomień wersji N w tygodniu po wydaniu | ping startowy | brak wzrostu = aktualizacja nie działa |

Ostatnia metryka jest najważniejsza i najczęściej pomijana: **jeśli po tygodniu 70 %
użytkowników nadal jest na starej wersji, twój auto-update jest zepsuty** i nie dowiesz
się o tym z logów błędów, bo błąd zdarza się na maszynie użytkownika i nigdzie nie trafia.
