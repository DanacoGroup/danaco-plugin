# Lista kontrolna bezpieczeństwa — profil `usluga`

Pliki: `skills/headless-i-osadzanie/examples/produkt-czat.flaga.settings.json`; flagi: `skills/headless-i-osadzanie/examples/produkt-czat.flagi.txt`; zmienne: `skills/headless-i-osadzanie/examples/produkt-czat.zmienne.txt`

| Id | Punkt | Wynik | Do zrobienia | Źródło |
|---|---|---|---|---|
| U01 | tryb omijania zablokowany (disableBypassPermissionsMode) | OK |  | cc:permissions |
| U02 | jawny tryb uprawnień przy starcie, nie bypass/auto | OK |  | cc:permission-modes |
| U03 | tryb auto wyłączony lub świadomie skonfigurowany | OK |  | cc:auto-mode-config |
| U04 | brak szerokich zgód (Bash, Bash(*), interpretery z *) | OK |  | cc:permissions |
| U05 | odczyt sekretów zablokowany (Read(./.env*), sekrety, klucze) | OK |  | cc:permissions |
| U06 | sudo zablokowane | OK |  | cc:permissions |
| U07 | skipDangerousModePermissionPrompt nie jest włączony | OK |  | cc:settings-reference |
| U08 | additionalDirectories bez katalogu głównego i domowego | OK |  | cc:permissions |
| U09 | goła reguła Edit nie udaje pokrycia Write | OK |  | próba wtyczki |
| S01 | ograniczenie sieci (piaskownica z listą domen albo zakazy curl/wget + WebFetch) | OK |  | cc:sandboxing |
| S02 | piaskownica nie degraduje się po cichu (failIfUnavailable) | OK |  | cc:sandboxing |
| S03 | brak ucieczki z piaskownicy na prośbę modelu | OK |  | cc:sandboxing |
| S04 | poświadczenia poza zasięgiem podprocesów (SCRUB lub sandbox.credentials) | OK |  | cc:env-vars |
| K01 | brak sekretów jawnym tekstem w env ustawień | OK |  | cc:settings-reference#env |
| K02 | hooki http tylko na dozwolone adresy (allowedHttpHookUrls) | OK |  | cc:hooks |
| R01 | MCP tylko z jawnej konfiguracji (--strict-mcp-config) | OK |  | cc:mcp |
| R02 | brak automatycznej zgody na serwery projektu | OK |  | cc:mcp |
| R03 | izolacja od plików konfiguracji maszyny/repozytorium (--setting-sources "" lub --bare) | OK |  | cc:headless |
| R04 | klient nie steruje sesją poleceniami / (--disable-slash-commands) | OK |  | analiza CLI Nexusa |
| R05 | publikacja i zdalny dostęp wyłączone (artefakty, Remote Control, wiadomości między sesjami) | OK |  | cc:settings-reference |
| R06 | konektory i synchronizacja z claude.ai wyłączone | OK |  | cc:settings-reference |
| D01 | osobny katalog konfiguracji i projektu na dzierżawcę | OK |  | cc:sessions |
| D02 | pamięć automatyczna wyłączona | OK |  | cc:memory |
| D03 | przypięta wersja CLI (bez automatycznych aktualizacji) | OK |  | cc:setup |
| D04 | retencja transkryptów ustawiona | OK |  | cc:settings-reference |
| C01 | limit tur lub budżetu przebiegu | OK |  | cc:headless |
| C02 | kontrola modeli (availableModels lub deny Agent(model:*)) i sufit effortu | OK |  | cc:model-config |
| P01 | telemetria bez treści rozmów | OK |  | cc:monitoring-usage |
