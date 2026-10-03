# Lista kontrolna wdrożenia produkcyjnego

Źródła: `cc:security`, `cc:agent-sdk/secure-deployment`, `cc:agent-sdk/hosting`,
`cc:sandboxing`, `cc:permissions`, `cc:permission-modes`, `cc:managed-settings`,
`cc:data-usage`, `cc:zero-data-retention`, `cc:monitoring-usage`, analiza CLI Danaco Nexus,
próby tej wtyczki. Kolumna „Skrypt” — identyfikator punktu w `lista_kontrolna.py`
(„ręcznie” = poza zasięgiem skryptu).

Profile: **S** stanowisko, **C** CI, **U** usługa. ● wymagane, ○ zalecane.

## 1. Uprawnienia

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| tryb omijania zablokowany (`disableBypassPermissionsMode: "disable"`) | ● | ● | ● | U01 |
| tryb jawny przy starcie (`--permission-mode`), bez `bypassPermissions`/`auto` poza izolacją | ○ | ● | ● | U02 |
| tryb auto wyłączony (`disableAutoMode`) lub skonfigurowany (`autoMode.environment`, `hard_deny`) | | ○ | ● | U03 |
| brak szerokich zgód (`Bash`, `Bash(*)`, interpretery z `*`, `Edit` bez ścieżki) | ● | ● | ● | U04 |
| zakaz odczytu sekretów (`.env*`, `secrets/`, klucze) lub brak narzędzi plikowych | ● | ● | ● | U05 |
| `sudo` zablokowane | ○ | ○ | ○ | U06 |
| `skipDangerousModePermissionPrompt` wyłączony | ● | ● | ● | U07 |
| `additionalDirectories` bez `/` i `~` | ● | ● | ● | U08 |
| reguły plikowe ze ścieżką (`Edit(./**)`), nie goła nazwa | ○ | ○ | ○ | U09 |
| `allowManagedPermissionRulesOnly` na stanowiskach zespołu (polityka) | ○ | | | ręcznie |
| hook `PreToolUse` dla twardych zakazów (np. `rm -rf`, `git push --force`) | ○ | ○ | ○ | ręcznie |

## 2. Piaskownica, sieć, poświadczenia

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| ograniczenie sieci (piaskownica z `allowedDomains` lub brak Bash; WebFetch po domenach) | ○ | ● | ● | S01 |
| `failIfUnavailable: true` (brak cichej pracy bez piaskownicy) | ○ | ● | ● | S02 |
| `allowUnsandboxedCommands: false` | ○ | ● | ● | S03 |
| poświadczenia poza podprocesami (`SCRUB` lub `sandbox.credentials`) | | ○ | ● | S04 |
| `bwrap`/`socat` obecne, userns działa (`sprawdz_srodowisko.sh`) | ○ | ● | ● | ręcznie |
| kontener: `--cap-drop ALL`, `no-new-privileges`, `--read-only`, `--network none`, limity pamięci/PID, użytkownik nie-root | | ○ | ● | ręcznie |
| proxy poza granicą: lista domen, wstrzykiwanie poświadczeń, log | | ○ | ● | ręcznie |
| reguły wyjścia per dzierżawca | | | ● | ręcznie |
| token modelu nieczytelny dla narzędzi (`apiKeyHelper`, deskryptor, proxy) | ○ | ● | ● | ręcznie |

## 3. Sekrety i hooki

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| brak sekretów w `env` ustawień | ● | ● | ● | K01 |
| hooki `http` tylko na adresy z `allowedHttpHookUrls`; zmienne w nagłówkach z `httpHookAllowedEnvVars` | ● | ● | ● | K02 |
| skrypty hooków z prawami tylko do odczytu dla agenta, ścieżki absolutne | ○ | ● | ● | ręcznie |
| `.env`, `.npmrc`, `~/.aws`, `~/.ssh`, `~/.kube`, `*.pem` poza zasięgiem (nie montowane / deny) | ● | ● | ● | ręcznie |

## 4. Rozszerzenia

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| `--strict-mcp-config` (tylko jawne serwery) | | ○ | ● | R01 |
| `enableAllProjectMcpServers` wyłączone | ● | ● | ● | R02 |
| `--setting-sources ""` lub `--bare` | | ○ | ● | R03 |
| `--disable-slash-commands` | | | ● | R04 |
| artefakty, Remote Control, wiadomości między sesjami wyłączone | | ○ | ● | R05 |
| konektory i synchronizacja claude.ai wyłączone | | ○ | ● | R06 |
| marketplace i wtyczki z listy (`strictKnownMarketplaces`, `blockedMarketplaces`) | ○ | ○ | | ręcznie |
| serwery MCP: własne lub sprawdzone; instrukcje i opisy przejrzane (`sprawdz_mcp.py --polacz`) | ● | ● | ● | ręcznie |

## 5. Izolacja dzierżawców, wersje, dane

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| `CLAUDE_CONFIG_DIR` + `CLAUDE_CODE_PROJECT_DIR_NAME` na dzierżawcę | | | ● | D01 |
| pamięć automatyczna wyłączona | | ○ | ● | D02 |
| przypięta wersja CLI, `DISABLE_AUTOUPDATER` | | ● | ● | D03 |
| retencja transkryptów (`cleanupPeriodDays`) i usuwanie przy usunięciu konta | ○ | ○ | ○ | D04 |
| osobny katalog roboczy na rozmowę; sprzątanie zaślepek po SCRUB | | ○ | ● | ręcznie |
| polityka danych dostawcy (trening, retencja, ZDR) zgodna z umową klienta | ● | ● | ● | ręcznie |

## 6. Koszty, prywatność, audyt

| Punkt | S | C | U | Skrypt |
|---|---|---|---|---|
| limit tur/budżetu przebiegu | | ○ | ● | C01 |
| kontrola modeli (`availableModels` / deny `Agent(model:*)`) i `maxEffortLevel` | ○ | ○ | ● | C02 |
| telemetria bez treści (`OTEL_LOG_*` wyłączone) | ● | ● | ● | P01 |
| OpenTelemetry lub log hosta: decyzje narzędzi, odmowy, `api_retry`, koszt | ○ | ○ | ● | ręcznie |
| hook `ConfigChange` / monitoring zmian plików ustawień | ○ | | | ręcznie |
| test regresji po każdej aktualizacji CLI (atrapa + lista kontrolna) | ○ | ● | ● | ręcznie |
