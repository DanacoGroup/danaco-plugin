---
name: zarzadzanie-flota
description: >
  Zarządzanie flotą Claude Code: ustawienia zarządzane (plik systemowy i katalog drop-in,
  MDM/rejestr, ustawienia serwerowe z konsoli claude.ai, policyHelper, ustawienia hosta),
  ranking źródeł first-wins/merge, klucze tylko zarządzane i czytane ze wszystkich źródeł,
  zachowanie przy błędach (fail closed), weryfikacja (/status, claude doctor), aktualizacje
  i wersje (kanał, minimumVersion, requiredMinimum/MaximumVersion, DISABLE_UPDATES),
  wymuszanie logowania i dostawców, wiele kont na jednym serwerze (CLAUDE_CONFIG_DIR).
  Stosuj przy „polityka organizacji”, „managed settings”, „wdrożenie dla zespołu”,
  „zablokować dla wszystkich”, „aktualizacje Claude Code”, „kilka kont na jednej maszynie”.
---

# Zarządzanie flotą

## Kiedy stosować

Gdy konfiguracja ma obowiązywać **wielu ludzi lub maszyn** i nie może być nadpisana przez
użytkownika lub repozytorium: stanowiska zespołu, serwery CI, serwery z wieloma kontami.

## Mechanizmy dostarczania

| Mechanizm | Gdzie | Odczyt | Kiedy |
|---|---|---|---|
| serwerowe (konsola claude.ai, Claude apps gateway) | Admin Settings → Claude Code → Managed settings (Owner/Primary Owner) | start + co godzinę; cache lokalny | brak MDM, urządzenia niezarządzane, sesje w chmurze |
| MDM / polityka systemu | macOS `com.anthropic.claudecode`, Windows `HKLM\SOFTWARE\Policies\ClaudeCode` (`Settings`) | start + co 30 min | jest MDM / GPO |
| pliki | Linux/WSL `/etc/claude-code/` (`managed-settings.json`, katalog `managed-settings.d/*.json`, `managed-mcp.json`, `CLAUDE.md`), macOS `/Library/Application Support/ClaudeCode/`, Windows `C:\Program Files\ClaudeCode\` | start + przy zmianie pliku | serwery Linux, obrazy |
| HKCU (Windows/WSL) | `HKCU\SOFTWARE\Policies\ClaudeCode` | jak MDM | tylko gdy brak źródła administracyjnego |

Ranking: serwerowe → MDM/HKLM → pliki → HKCU. Domyślnie `managedSourcesBehavior: "first-wins"`
— działa **pierwsze** źródło z kluczem polityki, reszta jest pomijana (bez ostrzeżenia; `/status`
pokazuje `Skipped sources`), poza kluczami czytanymi ze wszystkich źródeł (blokady piaskownicy,
`allowManagedMcpServersOnly`, `deniedMcpServers`, `maxEffortLevel` — najniższy, `env` per zmienna,
`forceRemoteSettingsRefresh`, `enableArtifact`/`sync*` — `false` wygrywa, `allowedProviders`).
`"merge"` (≥2.1.242) — wszystkie źródła administracyjne: listy sumowane, blokady najsurowsze,
listy dozwolonych z najwyższego źródła.

## Decyzje

| Potrzeba | Rozwiązanie |
|---|---|
| polityka na serwerach Linux | plik + drop-iny (`10-telemetria.json`, `20-bezpieczenstwo.json`…) wdrażane narzędziem konfiguracji; chroń prawa (root, 0644) |
| konsola i pliki jednocześnie | pamiętaj, że konsola wygrywa w całości; klucze logowania trzymaj w obu; albo `managedSourcesBehavior: "merge"` w źródle najwyższym |
| tylko reguły organizacji | `allowManagedPermissionRulesOnly: true` (+ reguły allow dla folderów hostów, np. Cowork) |
| blokada trybu omijania | `permissions.disableBypassPermissionsMode: "disable"`, `disableAutoMode: "disable"` |
| tylko zatwierdzone rozszerzenia | `strictKnownMarketplaces`, `blockedMarketplaces`, `strictPluginOnlyCustomization`, `allowManagedHooksOnly`, `disableSideloadFlags` (uwaga na usługi z `--agents`/`--mcp-config`) |
| wersje | `autoUpdatesChannel: "stable"`, `minimumVersion` (podłoga aktualizacji), `requiredMinimumVersion`/`requiredMaximumVersion` (odmowa startu), `DISABLE_AUTOUPDATER` / `DISABLE_UPDATES` |
| logowanie i dostawcy | `forceLoginMethod`, `forceLoginOrgUUID` (blokują `ANTHROPIC_API_KEY`/`AUTH_TOKEN`/`apiKeyHelper`), `allowedProviders` (≥2.1.285; `customEndpoint` wymaga przypięcia URL w zarządzanym `env`) |
| wymuszone pobranie polityki | `forceRemoteSettingsRefresh: true` — bez sieci CLI nie wystartuje |
| wiele kont na jednej maszynie | osobny `CLAUDE_CONFIG_DIR` na konto (`examples/konta.sh`) — logowanie, sesje, zgody, cache osobno; polityka zarządzana wspólna dla wszystkich |

## Procedura

1. Złóż politykę z szablonów `examples/` i sprawdź scalenie, ryzyka i walidację:
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/zarzadzanie-flota/scripts/sprawdz_zarzadzane.py" --glowny baza.json --dodatki dodatki/*.json [--zdalne konsola.json] --wersja <wersja floty> --cli claude`.
2. Wdróż na jednej maszynie testowej; uruchom `/status` (`Setting sources: Enterprise managed
   settings (file + drop-ins)`, `Skipped sources`) i `claude doctor` (pominięte wpisy,
   `Managed settings (remote)`, `Organization policy`, `Auto-updates`).
3. Sesja `-p` na tej maszynie: stderr zawiera podsumowanie odrzuconych wpisów.
4. Dopiero potem cała flota; zmiany konsoli docierają co godzinę (część przy następnym starcie:
   `model`, eksport OTel, usunięcie zmiennej `env`, `requiredMinimumVersion`).

## Pułapki

- **Niepoprawny JSON pliku zarządzanego lub drop-inu = CLI odmawia startu** na każdej maszynie
  (nawet gdy inne źródło jest poprawne). Plik nieczytelny z braku praw = sesje bez tej polityki;
  inny błąd odczytu = wyjście z komunikatem.
- Klucze blokujące z błędną wartością działają restrykcyjnie (fail closed, ≥2.1.282): np. błędne
  `allowedMcpServers` = pusta lista, błędne `allowedProviders` = CLI nie startuje, błędne
  `availableModels` = tylko Default. `requiredMinimum/MaximumVersion` — błędne są pomijane.
- Plik z samymi kluczami sterującymi (`managedSourcesBehavior`) nie jest polityką.
- Ustawienia serwerowe: nie docierają przy `CLAUDE_CODE_USE_*`, własnym `ANTHROPIC_BASE_URL`,
  `apiKeyHelper`, WIF; w `-p` ustawienia wymagające zgody (hooki, `env` proxy/base URL,
  `apiKeyHelper`) **są stosowane na ten przebieg bez dialogu** i bez zapisu w cache.
  W cache `env` proxy/TLS/routing/poświadczenia/`CLAUDE_CONFIG_DIR` czekają na potwierdzenie serwera.
- Ustawienia serwerowe to kontrola po stronie klienta, nie granica bezpieczeństwa (użytkownik
  może edytować cache, zmienić dostawcę); twarde wymuszenie — pliki/MDM z prawami systemu.
- `model` w zarządzanych to wartość domyślna — `--model` ją zmienia; ograniczenie: `availableModels`.
- `disableSideloadFlags: true` wyłącza `--agents`, `--mcp-config`, `--plugin-dir`, `--plugin-url`
  — usługi osadzające CLI na tej maszynie przestaną działać.
- Wiele kont: keyless sign-in do Console (profil Anthropic) jest poza `CLAUDE_CONFIG_DIR`;
  cache promptu nie jest dzielony między organizacjami (rotacja kont = zimny cache).
- Na serwerach Danaco pliki w `/etc` są tylko do odczytu dla agentów, a straż pakietów blokuje
  zapis każdego pliku o nazwie pliku zarządzanego — politykę wdraża właściciel serwera.

## Szablony

- `examples/flota-baza.managed.settings.json` — baza: zakazy, blokada bypass/auto, kanał i wersje, logowanie i dostawca, marketplace, ogłoszenie.
- `examples/dodatki/10-telemetria.json`, `20-bezpieczenstwo.json`, `30-modele.json` — drop-iny (scalane alfabetycznie).
- `examples/konsola-ladunek.json` — przykład ładunku konsoli do symulacji `first-wins`.
- `examples/konta.sh` — wiele kont na jednej maszynie (`CLAUDE_CONFIG_DIR`), stan kont bez sekretów.

## Referencje

- `references/zrodla-i-scalanie.md` — ranking, first-wins/merge, klucze ze wszystkich źródeł, ustawienia hosta, policyHelper, fail closed, klucze tylko zarządzane.
- `references/serwerowe-aktualizacje-logowanie.md` — konsola (cache, zgody, dostępność), aktualizacje i wersje, logowanie i dostawcy, wiele kont.
- Powiązane: `serwery-mcp/references/zarzadzanie-mcp.md`, `wtyczki-i-marketplace/references/marketplace-i-dystrybucja.md`, `model-cache-i-koszty` (modele, OTel), `bezpieczenstwo-wdrozenia`.
