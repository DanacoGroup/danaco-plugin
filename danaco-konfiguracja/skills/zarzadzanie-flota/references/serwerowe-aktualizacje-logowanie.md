# Ustawienia serwerowe, aktualizacje, logowanie, wiele kont

Źródła: `cc:server-managed-settings`, `cc:setup` (Update Claude Code), `cc:authentication`,
`cc:admin-setup`, `cc:corporate-launcher`, `cc:data-usage`, `cc:settings-reference`.

## 1. Ustawienia serwerowe (konsola claude.ai)

- Wymagania: plan Team/Enterprise, rola Owner/Primary Owner, dostęp do `api.anthropic.com`.
- Pobierane przy: logowaniu Team/Enterprise, `CLAUDE_CODE_OAUTH_TOKEN`, kluczu API podanym
  wprost, profilu `user_oauth` (≥2.1.257). **Nie** przy `apiKeyHelper`, WIF, `CLAUDE_CODE_USE_*`,
  własnym `ANTHROPIC_BASE_URL` (eksport w powłoce — nie da się go cofnąć ładunkiem serwerowym;
  `""` w `env` ustawień użytkownika przywraca pobieranie).
- Pierwsze uruchomienie: przy logowaniu do 5 s czekania na politykę; inaczej sesja startuje,
  a ograniczenia wchodzą po pobraniu. Kolejne: cache od razu, poza `modelPricing`,
  `managedMcpServers` (do 30 s) i wstrzymanymi zmiennymi `env` (proxy/TLS, routing i wybór
  dostawcy, poświadczenia, `CLAUDE_CONFIG_DIR`, katalogi systemowe) — czekają na potwierdzenie.
- Odpytywanie co godzinę; przy następnym starcie: eksport OTel, `model`, usunięcie zmiennej `env`.
- Zgody: hooki, `apiKeyHelper`, `statusLine`, `otelHeadersHelper`, binarki i luzowanie piaskownicy,
  `env` proxy/base URL/endpoint OTel, część `ANTHROPIC_CUSTOM_HEADERS` → dialog w sesji
  interaktywnej (odrzucenie = wyjście). `-p`/SDK/IDE: stosowane na przebieg, bez zapisu.
  Zgoda zapisywana w katalogu konfiguracji (per organizacja dla logowania claude.ai).
- `forceRemoteSettingsRefresh: true` — start dopiero po świeżym pobraniu, inaczej wyjście
  (`claude auth` zwolnione); utrwala się w cache. Ustaw też w pliku/MDM, by działało od pierwszego startu.
- Ograniczenia: jedna polityka na organizację (bez grup), bez `managed-mcp.json` (zamiast tego
  `allowedMcpServers`/`deniedMcpServers`/`managedMcpServers`), bez `policyHelper` i
  `wslInheritsWindowsSettings`.
- Bezpieczeństwo: kontrola po stronie klienta — edycja cache działa do następnego pobrania,
  zmiana dostawcy omija politykę. Audyt zmian: Compliance API / eksport logu audytu.

## 2. Aktualizacje i wersje

| Cel | Ustawienie |
|---|---|
| kanał | `autoUpdatesChannel`: `"latest"` (domyślnie) / `"stable"` (ok. tydzień opóźnienia, bez wydań z regresjami) |
| podłoga aktualizacji | `minimumVersion` (aktualizacje nie zejdą niżej; przy przejściu na stable `/config` może ją ustawić) |
| zakres uruchamiania | `requiredMinimumVersion`, `requiredMaximumVersion` (tylko zarządzane; odmowa startu poza zakresem; błędna wartość — pomijana; aktualizacje respektują sufit) |
| bez automatycznych aktualizacji | `DISABLE_AUTOUPDATER=1` (`claude update` działa; `doctor`: `Auto-updates: disabled (set by env…)`) |
| bez jakichkolwiek aktualizacji | `DISABLE_UPDATES=1` (własna dystrybucja wersji) |
| menedżery pakietów | Homebrew/WinGet ręcznie lub `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=1`; apt/dnf/apk — ręcznie |
| własny launcher | `~/.local/bin/claude` zastąpiony skryptem — aktualizator go nie nadpisuje (≥2.1.207), trzyma wszystkie wersje |

Usługa osadzająca CLI: przypięta binarka (ścieżka do konkretnej wersji), `DISABLE_AUTOUPDATER=1`,
testy nowej wersji na atrapie (`scripts/proba_cli.py`) i `claude doctor` z profilem usługi.
Długie sesje nie są przerywane przez `requiredMinimumVersion`.

## 3. Logowanie i dostawcy

Kolejność poświadczeń: dostawca chmurowy (`CLAUDE_CODE_USE_*`) → `ANTHROPIC_AUTH_TOKEN` →
`ANTHROPIC_API_KEY` (w `-p` zawsze, gdy ustawiony) → `apiKeyHelper` → `CLAUDE_CODE_OAUTH_TOKEN`
→ profil Anthropic / WIF → logowanie `/login`. Sesja bramy (Claude apps gateway) — przed wszystkimi.

- `forceLoginMethod` (`claudeai`, `console`, `gateway`) i `forceLoginOrgUUID` (lista UUID) —
  blokują start z `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `apiKeyHelper`; dostawcy chmurowi
  tylko, gdy takie poświadczenie też jest. `claude setup-token` sprawdza tylko metodę.
  Wdrażaj plikiem/MDM (serwerowe nie przekierują pierwszego logowania) i trzymaj w obu źródłach.
- `allowedProviders` (≥2.1.285): `anthropic`, `bedrock`, `vertex`, `foundry`, `anthropicAws`,
  `mantle`, `customEndpoint` (wymaga przypięcia URL w zarządzanym `env`), `gateway`;
  pusta lub w pełni błędna lista = CLI nie startuje.
- Poświadczenia: Linux `~/.claude/.credentials.json` (0600) lub `<CLAUDE_CONFIG_DIR>/.credentials.json`;
  `claude setup-token` — token roczny dla CI (`CLAUDE_CODE_OAUTH_TOKEN`), nie jest zapisywany.

## 4. Wiele kont na jednej maszynie

| Element | Per `CLAUDE_CONFIG_DIR` | Wspólny |
|---|---|---|
| logowanie / klucz z `/login` | ✔ | |
| ustawienia użytkownika, sesje, pamięć, wtyczki, zgody na ustawienia serwerowe | ✔ | |
| polityka zarządzana (pliki, MDM) | | ✔ (cała maszyna) |
| keyless Console (profil Anthropic) | | ✔ `~/.config/anthropic` — rozdzielaj `ANTHROPIC_PROFILE` |
| cache promptu | per organizacja konta (po stronie API) | |

Wzorzec: funkcje powłoki (`examples/konta.sh`) albo osobne konta systemowe. Usługa używająca
kilku kont: katalog konfiguracji per konto, przypisanie rozmowy do konta (cache), rejestracja
`apiKeySource` i `usage` z każdego przebiegu. Na serwerach Danaco zmienne kont ustawia się
w `/etc/security/pam_env.conf` i `/etc/profile.d/51-danaco-cache.sh` (właściciel serwera).

## 5. Telemetria i dane

- Wyłączenie telemetrii operacyjnej dla organizacji: zarządzane `env.DISABLE_TELEMETRY=1`
  (bez dialogu; wyłącza też pobieranie flag funkcji i dane do pulpitu analityki).
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` — telemetria, raporty błędów, ankiety naraz.
- Własny monitoring: OpenTelemetry (`model-cache-i-koszty/references/koszty-i-telemetria.md`).
- Launcher korporacyjny: `processWrapper` / `CLAUDE_CODE_PROCESS_WRAPPER` dla procesów w tle
  (zamiast wyłączania `disableAgentView`).
