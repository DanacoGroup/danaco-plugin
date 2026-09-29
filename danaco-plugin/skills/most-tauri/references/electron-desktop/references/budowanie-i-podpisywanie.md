# Budowanie, pakowanie i podpisywanie

Odniesienie sprawdzone 2026-08-04: `@electron-forge/cli` 7.11.2, `electron-builder` 26.15.3,
`@electron/notarize` 3.1.1, `@electron/osx-sign` 2.6.0, `@electron/windows-sign` 2.0.6,
`@electron/packager` 20.1.1.

## Forge czy electron-builder

Electron **nie rekomenduje oficjalnie żadnego** — dokumentacja opisuje oba neutralnie.
Różnica realna:

| Kryterium | Electron Forge 7.11 | electron-builder 26.15 |
| --- | --- | --- |
| Właściciel | organizacja `electron/` | społeczność, jeden główny maintainer |
| Podpis | `@electron/osx-sign`, `@electron/windows-sign`, `@electron/notarize` — te same moduły, co reszta ekosystemu | własna implementacja |
| Auto-update | `update-electron-app` albo własny serwer; `electron-updater` **nie jest wspierany** | `electron-updater` w komplecie, delta na NSIS |
| Windows | Squirrel.Windows, WiX MSI, MSIX, AppX | NSIS (z delta), MSI, Squirrel, AppX, portable |
| macOS | dmg, pkg, zip | dmg, pkg, zip, mas |
| Linux | deb, rpm, flatpak, snap | deb, rpm, **AppImage**, snap, pacman, flatpak |
| Publikacja | GitHub, S3, GCS, Bitbucket, Snapcraft, ERS, Nucleus | GitHub, S3, Spaces, R2, Keygen, generic |
| Konfiguracja | `forge.config.ts` — kod, typowany | `electron-builder.yml` — deklaracja |
| Bundler | wtyczka Vite albo Webpack w komplecie | osobno (`electron-vite`) |

**Wybierz Forge**, gdy: nowy projekt, chcesz zostać przy oficjalnym łańcuchu, wystarczą
ci deb/rpm na Linuksie, auto-update przez GitHub Releases.

**Wybierz electron-builder**, gdy: potrzebujesz AppImage, chcesz delta na Windows,
potrzebujesz `electron-updater` z własnym serwerem generic/S3, publikujesz na R2.

**Nie mieszaj.** Uruchamianie obu na tym samym projekcie kończy się dwoma różnymi
`app.asar`, dwiema konfiguracjami fuses i tygodniem szukania, czemu podpis nie przechodzi.

## Cele instalacyjne — co wybrać

| System | Cel | Kiedy | Uwagi |
| --- | --- | --- | --- |
| Windows | **NSIS** | domyślny wybór | instalacja per-user bez UAC, delta w `electron-updater`, skojarzenia plików deklaratywnie |
| Windows | Squirrel | gdy Forge i prosty przypadek | brak UI instalatora, brak skojarzeń plików bez kodu |
| Windows | MSI (WiX) | wdrożenia korporacyjne przez GPO/Intune | brak auto-update, aktualizacja przez IT |
| Windows | MSIX/AppX | Microsoft Store | sandbox systemowy, inne ścieżki `userData` |
| macOS | **dmg + zip** | domyślny wybór | zip jest wymagany przez `electron-updater` do metadanych |
| macOS | pkg | wdrożenia przez MDM | podpis Developer ID **Installer**, nie Application |
| macOS | mas | Mac App Store | App Sandbox, inne entitlements, brak auto-update własnego |
| Linux | **AppImage** | dystrybucja uniwersalna, jedyna z auto-update | tylko electron-builder |
| Linux | deb + rpm | repozytoria, wdrożenia | brak auto-update poza menedżerem pakietów |
| Linux | Flatpak/Snap | sklepy | sandbox, własny mechanizm aktualizacji |

Architektury: `x64` i `arm64` na wszystkich trzech systemach. Na macOS dodatkowo
`universal` (jeden plik z dwiema architekturami) — waży prawie dwa razy tyle, ale
upraszcza dystrybucję. **`ia32` na Windows i `armv7l` na Linuksie znikają w E44** —
przestań budować te cele.

## Ikony i metadane

| System | Format | Rozmiary | Gdzie |
| --- | --- | --- | --- |
| macOS | `.icns` | 16, 32, 128, 256, 512 pt + warianty `@2x` | `packagerConfig.icon` bez rozszerzenia |
| Windows | `.ico` | 16, 24, 32, 48, 64, 256 px w jednym pliku | jw. |
| Linux | `.png` | 512×512 (i 256 dla starszych DE) | `linux.icon` |

```bash
# .icns z katalogu iconset (macOS)
iconutil -c icns ikona.iconset
# .ico wieloformatowy (ImageMagick)
magick ikona-1024.png -define icon:auto-resize=256,64,48,32,24,16 ikona.ico
```

Metadane, które muszą się zgadzać między konfiguracją a rzeczywistością:

```jsonc
// package.json
{
  "name": "moja-aplikacja",          // bez spacji i wielkich liter — używane w ścieżkach Linuksa
  "productName": "Moja Aplikacja",   // nazwa widoczna; ZMIANA = utrata userData użytkowników
  "version": "1.4.2",                // jedyne źródło wersji; app.getVersion() czyta stąd
  "description": "…",                // trafia do metadanych deb/rpm i NSIS
  "author": "DANACO GROUP sp. z o.o. <biuro@danacogroup.com.pl>",  // wymagane przez deb/rpm
  "homepage": "https://danacogroup.com.pl"
}
```

`appId` (`pl.danaco.moja-aplikacja`) musi być stały przez cały cykl życia produktu —
na macOS jest kluczem tożsamości aplikacji dla Gatekeepera i Keychaina, na Windows dla
powiadomień i skojarzeń.

## Budowanie wieloplatformowe i jego granice

| Buduję na | Cel Windows | Cel macOS | Cel Linux |
| --- | --- | --- | --- |
| **Linux** | tak (NSIS przez Wine), podpis przez `osslsigncode`/`pkcs11`/`azure` | **nie** — dmg wymaga narzędzi Apple; podpis niemożliwy | tak |
| **macOS** | tak (przez Wine), podpis jw. | tak | tak (deb/rpm wymagają `fakeroot`, `dpkg`) |
| **Windows** | tak | **nie** | częściowo (przez WSL) |

Twarda zasada: **macOS buduj i podpisuj wyłącznie na macOS.** Notaryzacja wymaga
`xcrun notarytool`, którego nie ma poza macOS. Wszystko inne da się zrobić na Linuksie
w kontenerze, ale w CI i tak prościej użyć trzech runnerów.

Rekomendacja firmowa: **macierz w CI, trzy runnery, artefakty zbierane do jednego wydania.**
Budowanie krzyżowe zostaw dla lokalnych testów.

## macOS: podpis, entitlements, notaryzacja, stapling

### Certyfikaty

| Cel | Certyfikat | Skąd |
| --- | --- | --- |
| dystrybucja poza App Store | **Developer ID Application** | Apple Developer Program, 99 USD/rok |
| instalator `.pkg` poza App Store | **Developer ID Installer** | jw. |
| Mac App Store | 3rd Party Mac Developer Application + Installer | jw. |

W CI trzymaj certyfikat jako base64 pliku `.p12` w sekrecie:

```bash
base64 -i certyfikat.p12 | pbcopy   # do sekretu CSC_LINK
```

### Entitlements

```xml
<!-- build/entitlements.mac.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <!-- WYMAGANE dla Electrona pod hardened runtime: V8 kompiluje JIT -->
  <key>com.apple.security.cs.allow-jit</key><true/>
  <!-- WYMAGANE: Electron ładuje własne framework'i -->
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
  <key>com.apple.security.cs.disable-library-validation</key><true/>
  <!-- tylko jeśli faktycznie używasz -->
  <key>com.apple.security.device.camera</key><true/>
  <key>com.apple.security.device.audio-input</key><true/>
  <key>com.apple.security.network.client</key><true/>
</dict>
</plist>
```

Bez `allow-jit` i `allow-unsigned-executable-memory` aplikacja z hardened runtime
**startuje i natychmiast się wywala** przy inicjalizacji V8. To jest najczęstszy błąd
przy pierwszym podpisie.

`disable-library-validation` jest potrzebne, bo Electron ładuje `Electron Framework`
i moduły natywne podpisane innym Team ID (albo niepodpisane). Apple to akceptuje przy
notaryzacji.

**`entitlementsInherit`** stosuje się do procesów potomnych (renderer, GPU, utility).
Ustaw ten sam plik — bez tego procesy renderera nie wstaną.

### Konfiguracja podpisu i notaryzacji

**electron-builder:**

```yaml
mac:
  hardenedRuntime: true
  gatekeeperAssess: false
  entitlements: build/entitlements.mac.plist
  entitlementsInherit: build/entitlements.mac.plist
  notarize:
    teamId: XXXXXXXXXX
  target:
    - { target: dmg, arch: [arm64, x64] }
    - { target: zip, arch: [arm64, x64] }
```

Zmienne środowiskowe (nigdy w repozytorium):

```bash
CSC_LINK=<base64 pliku .p12>            # albo ścieżka do pliku
CSC_KEY_PASSWORD=<hasło do .p12>
APPLE_ID=konto@danacogroup.com.pl
APPLE_APP_SPECIFIC_PASSWORD=xxxx-xxxx-xxxx-xxxx   # z appleid.apple.com, NIE hasło konta
APPLE_TEAM_ID=XXXXXXXXXX
```

Wariant z kluczem API App Store Connect (zalecany w CI — nie wygasa jak hasło,
nie wymaga 2FA):

```bash
APPLE_API_KEY=./AuthKey_ABC123.p8
APPLE_API_KEY_ID=ABC123
APPLE_API_ISSUER=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
```

**Electron Forge:**

```ts
// forge.config.ts
packagerConfig: {
  osxSign: {
    identity: 'Developer ID Application: DANACO GROUP sp. z o.o. (XXXXXXXXXX)',
    optionsForFile: () => ({
      hardenedRuntime: true,
      entitlements: 'build/entitlements.mac.plist',
      'entitlements-inherit': 'build/entitlements.mac.plist',
    }),
  },
  osxNotarize: {
    appleApiKey: process.env.APPLE_API_KEY!,
    appleApiKeyId: process.env.APPLE_API_KEY_ID!,
    appleApiIssuer: process.env.APPLE_API_ISSUER!,
  },
}
```

### Kolejność operacji — nie da się jej pomylić bezkarnie

1. Pakowanie (`.app` gotowy, fuses przestawione).
2. Podpis **od środka na zewnątrz**: najpierw wszystkie `.dylib`, `.node`, helper-aplikacje,
   `Electron Framework`, na końcu główny bundle. `@electron/osx-sign` robi to poprawnie;
   ręczne `codesign` w złej kolejności daje „code object is not signed at all”.
3. Weryfikacja podpisu: `codesign --verify --deep --strict --verbose=2 Moja.app`.
4. Notaryzacja: wysyłka `.zip` albo `.dmg` do Apple przez `notarytool`, oczekiwanie
   (zwykle 2-15 minut, bywa godzina).
5. **Stapling**: `xcrun stapler staple Moja.app` (i osobno `.dmg`). Przybija „bilet”
   notaryzacji do pliku, żeby Gatekeeper nie musiał pytać serwera Apple.
6. Weryfikacja: `xcrun stapler validate Moja.app` i `spctl --assess --type execute --verbose
   Moja.app` → oczekiwane `accepted, source=Notarized Developer ID`.

**`altool` nie działa od listopada 2023.** Wszystko idzie przez `notarytool`.
`@electron/notarize` 3.x używa wyłącznie `notarytool`.

**Stapling `.dmg` i `.app` osobno.** Jeśli spakujesz `.app` do `.dmg` po stapleniu `.app`,
`.dmg` nadal wymaga własnego stapla — inaczej użytkownik bez internetu dostanie
ostrzeżenie.

### Częste odrzucenia notaryzacji

| Komunikat | Przyczyna | Naprawa |
| --- | --- | --- |
| `The binary is not signed with a valid Developer ID certificate` | użyty certyfikat „Apple Development” zamiast „Developer ID Application” | wybierz właściwy `identity` |
| `The executable does not have the hardened runtime enabled` | brak `hardenedRuntime: true` | włącz |
| `The signature does not include a secure timestamp` | podpis bez `--timestamp` (brak sieci przy podpisywaniu) | zapewnij dostęp do `timestamp.apple.com` |
| `The binary uses an SDK older than the 10.9 SDK` | stary moduł natywny w paczce | przebuduj albo usuń |
| notaryzacja przechodzi, ale Gatekeeper blokuje | brak staplingu | `xcrun stapler staple` |

## Windows: podpis

### Co się zmieniło 1 czerwca 2023 — i czego model nie wie

Wymagania bazowe CA/Browser Forum: **klucze prywatne wszystkich publicznie zaufanych
certyfikatów code signing — również OV, nie tylko EV — muszą być generowane i przechowywane
w sprzęcie certyfikowanym FIPS 140-2 Level 2, Common Criteria EAL 4+ lub równoważnym.**

Konsekwencja praktyczna: **nie dostaniesz już od publicznego CA pliku `.pfx` z kluczem.**
Dostajesz token USB, dostęp do HSM w chmurze albo usługę podpisu. Wszystkie tutoriale
mówiące „wrzuć `.pfx` do sekretu CI” opisują stan sprzed czerwca 2023.

Cztery drogi w 2026:

| Droga | Koszt rocznie | CI-friendly | Reputacja SmartScreen |
| --- | --- | --- | --- |
| Token USB (OV lub EV) | ~250-600 USD | **nie** — token musi być fizycznie wpięty | OV: buduje się tygodniami; EV: natychmiast |
| HSM w chmurze CA (DigiCert KeyLocker, Sectigo, SSL.com eSigner, GlobalSign) | ~400-900 USD + opłaty za podpis | tak | zależnie od typu certyfikatu |
| **Azure Artifact Signing** (dawniej Trusted Signing) | ~9,99 USD/mies. tier Basic | tak | natychmiastowa, powiązana z tożsamością |
| Brak podpisu | 0 | — | SmartScreen blokuje; nie do klienta |

### Azure Artifact Signing (dawniej Trusted Signing)

Microsoft zmienił nazwę usługi z „Trusted Signing” na „Artifact Signing”; dokumentacja
i portal używają obu. Stan na sierpień 2026:

- **Koszt:** tier Basic ~9,99 USD/miesiąc z limitem 5 000 podpisów/miesiąc; tier Premium
  100 000 podpisów/miesiąc. `[niepotwierdzone: dokładna cena Premium — strona cennika
  Azure pokazuje wartości dopiero po zalogowaniu; potwierdź w kalkulatorze Azure]`
- **Certyfikat żyje 72 godziny** i jest odnawiany codziennie; nie dostajesz go do ręki.
  Podpisane pliki pozostają ważne bezterminowo dzięki znacznikowi czasu.
- **Reputacja SmartScreen jest natychmiastowa** i przywiązana do zweryfikowanej tożsamości,
  nie do konkretnego certyfikatu. Rotacja certyfikatu nie resetuje reputacji — to jest
  główna przewaga nad zwykłym OV.
- **Kwalifikacja:** pierwotnie wymagane 3 lata historii podatkowej organizacji; po
  ogólnej dostępności dopuszczone są też osoby samozatrudnione, a wymóg trzech lat jest
  zastępowany dodatkową weryfikacją tożsamości. Dostępne dla podmiotów z USA, Kanady,
  UE i Wielkiej Brytanii. `[niepotwierdzone: aktualny stan wymogu 3 lat i pełna lista
  krajów — Microsoft zmieniał to kilkukrotnie; sprawdź przed założeniem konta]`
- **Weryfikacja tożsamości trwa od kilku dni do kilku tygodni.** Zacznij ten proces
  w pierwszym tygodniu projektu, nie na tydzień przed wydaniem.
- Polska jest w UE, więc podmiot polski kwalifikuje się.

**electron-builder:**

```yaml
win:
  publisherName: "DANACO GROUP sp. z o.o."   # dokładnie CN z certyfikatu — używane przez electron-updater
  sign:
    type: azure
```

```bash
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_CODE_SIGNING_NAME=<nazwa konta podpisu>
AZURE_CERT_PROFILE_NAME=<nazwa profilu certyfikatu>
AZURE_ENDPOINT=https://weu.codesigning.azure.net
```

**Electron Forge** — przez `@electron/windows-sign` z własnym hookiem `signWithParams`
albo `windowsSign.hookFunction`.

### Pozostałe typy podpisu w electron-builder 26

`win.sign.type` przyjmuje cztery wartości:

| `type` | Do czego | Działa poza Windows |
| --- | --- | --- |
| `signtool` (domyślny) | plik `.pfx`/`.p12` albo magazyn certyfikatów Windows | tak, przez `osslsigncode` |
| `hsm` | token/HSM przez CSP Windows | **nie** (tylko Windows) |
| `pkcs11` | karta, token USB, HSM sieciowy przez moduł PKCS#11 | tak, przez `osslsigncode` |
| `azure` | Azure Artifact Signing | tak |

Domyślnie electron-builder podpisuje **podwójnie** (SHA-1 dla starych Windows i SHA-256).
Dla certyfikatów wydanych po 2023 SHA-1 jest zbędny — wyłącz, jeśli CA go nie wspiera.

### Co dokładnie trzeba podpisać

Nie wystarczy podpisać instalatora. Podpisz:
- główny `.exe` aplikacji,
- wszystkie `.dll` i `.node` w paczce (electron-builder robi to przez `signAndEditExecutable`),
- instalator (`.exe` NSIS albo `.msi`),
- przy Squirrelu dodatkowo `Update.exe` (`squirrelSetup.exe`).

Weryfikacja:

```powershell
signtool verify /pa /v "Moja Aplikacja Setup 1.4.2.exe"
# oczekiwane: "Successfully verified" + widoczny znacznik czasu
```

### SmartScreen

SmartScreen ocenia reputację **wydawcy + pliku**. Reguły w praktyce:

- Certyfikat OV bez historii: ostrzeżenie „Windows protected your PC” przez pierwsze
  tygodnie i pierwsze kilkaset-kilka tysięcy pobrań. Nie da się tego przyspieszyć płacąc.
- Certyfikat EV albo Azure Artifact Signing: brak ostrzeżenia od pierwszego pliku.
- **Zmiana certyfikatu resetuje reputację** przy OV/EV. Przy Azure Artifact Signing —
  nie, bo reputacja jest przy tożsamości.
- Brak znacznika czasu (`timestamp`) = po wygaśnięciu certyfikatu wszystkie stare
  instalatory stają się niepodpisane. **Zawsze podpisuj ze znacznikiem czasu.**

## Linux

Brak podpisu kodu w sensie Windows/macOS. Zamiast tego:

- **deb/rpm**: podpis repozytorium GPG (`debsign`, `rpm --addsign`). Wymagany, jeśli
  publikujesz przez własne repo APT/YUM.
- **AppImage**: opcjonalny podpis GPG osadzony w pliku; prawie nikt go nie weryfikuje.
  W praktyce liczy się checksum publikowany obok.
- **Flatpak/Snap**: sklep podpisuje za ciebie; wymagany manifest i przegląd.

```yaml
linux:
  target: [AppImage, deb, rpm]
  category: Office
  synopsis: "Krótki opis (deb)"
  desktop:
    entry:
      MimeType: "application/x-danaco-dokument;"
      StartupWMClass: "moja-aplikacja"   # bez tego ikona w docku GNOME się dubluje
deb:
  depends: ["libgtk-3-0", "libnotify4", "libnss3", "libxss1", "libxtst6", "xdg-utils", "libatspi2.0-0", "libuuid1", "libsecret-1-0"]
```

`StartupWMClass` musi odpowiadać nazwie klasy okna (`app.setName` / `--class`) — bez tego
GNOME pokazuje dwie ikony: skrót i działającą aplikację.

## CI dla wydań — macierz trzech runnerów

```yaml
# .github/workflows/wydanie.yml
name: Wydanie
on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-14        # arm64, buduje uniwersalnie
          - os: windows-latest
          - os: ubuntu-22.04    # starsze glibc = szersza kompatybilność
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '24', cache: 'npm' }

      - name: Zależności systemowe (Linux)
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y libsecret-1-dev fakeroot rpm

      - run: npm ci

      - name: Testy
        run: npm test

      - name: Buduj i publikuj
        run: npm run build -- --publish always
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # macOS
          CSC_LINK: ${{ secrets.MAC_CERT_P12_BASE64 }}
          CSC_KEY_PASSWORD: ${{ secrets.MAC_CERT_PASSWORD }}
          APPLE_API_KEY: ${{ secrets.APPLE_API_KEY_PATH }}
          APPLE_API_KEY_ID: ${{ secrets.APPLE_API_KEY_ID }}
          APPLE_API_ISSUER: ${{ secrets.APPLE_API_ISSUER }}
          # Windows
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}

      - name: Weryfikacja fuses
        run: npx @electron/fuses read --app ${{ runner.os == 'macOS' && 'dist/mac-arm64/Moja Aplikacja.app' || 'dist/win-unpacked/Moja Aplikacja.exe' }}
        if: runner.os != 'Linux'
```

Punkty, na których to się wykłada w praktyce:

1. **Od E42 `npm ci` nie pobiera binarki Electrona** (zniknął `postinstall`). Pobranie
   następuje przy pierwszym uruchomieniu. W obrazie CI bez dostępu do
   `github.com/electron/electron/releases` build padnie dopiero na etapie pakowania.
   Ustaw `ELECTRON_MIRROR` na wewnętrzne lustro, jeśli sieć jest ograniczona.
2. **Klucz `.p8` Apple zapisz do pliku w kroku, nie przekazuj treścią** —
   `APPLE_API_KEY` oczekuje ścieżki.
3. **Ubuntu 22.04, nie `ubuntu-latest`.** Binaria zbudowane pod nowsze glibc nie wstaną
   na starszych dystrybucjach użytkowników.
4. **`fail-fast: false`** — inaczej awaria notaryzacji macOS anuluje gotowy build Windows.
5. **Publikuj dopiero po wszystkich trzech.** Wydanie z brakującym `latest-mac.yml`
   psuje auto-update dla części użytkowników. Użyj `--publish always` z draftem i publikuj
   ręcznie po sprawdzeniu artefaktów albo osobnym jobem `needs: [build]`.

## Kontrola artefaktu przed publikacją

```bash
# co jest w paczce — szukaj map źródeł, testów, node_modules narzędzi
npx asar list dist/mac-arm64/Moja\ Aplikacja.app/Contents/Resources/app.asar | head -50
npx asar list ... | grep -E '\.map$|/test/|/__tests__/|\.ts$' | wc -l    # oczekiwane: 0

# fuses
npx @electron/fuses read --app "dist/mac-arm64/Moja Aplikacja.app"

# macOS: podpis + notaryzacja
codesign --verify --deep --strict --verbose=2 "dist/mac-arm64/Moja Aplikacja.app"
spctl --assess --type execute --verbose "dist/mac-arm64/Moja Aplikacja.app"
xcrun stapler validate "dist/Moja Aplikacja-1.4.2-arm64.dmg"

# Windows: podpis
signtool verify /pa /v "dist\Moja Aplikacja Setup 1.4.2.exe"

# rozmiar — porównaj z poprzednim wydaniem, skok > 20 % wymaga wyjaśnienia
du -sh dist/*.dmg dist/*.exe dist/*.AppImage
```

## Sekrety w konfiguracji builda — czego nigdy nie commitować

`.gitignore` musi zawierać: `*.p12`, `*.pfx`, `*.p8`, `*.cer`, `*.mobileprovision`,
`build/*.plist` z danymi osobowymi, `.env`, `.env.local`.

Wszystkie hasła i klucze wyłącznie jako sekrety CI. Certyfikat, który raz trafił do
historii gita, jest spalony — trzeba go unieważnić u CA, nie „usunąć commita”.
