# Model zagrożeń i izolacja

Źródła: `cc:agent-sdk/secure-deployment`, `cc:security`, `cc:sandboxing` (Security limitations),
`cc:data-usage`, `cc:zero-data-retention`, `cc:legal-and-compliance`.

## 1. Zagrożenia

| Zagrożenie | Przykład | Warstwa ochrony |
|---|---|---|
| wstrzyknięcie instrukcji | plik/strona/wynik MCP każe wysłać `.env` na zewnątrz | brak kanału wyjścia (sieć), deny odczytu sekretów, przegląd zmian |
| błąd modelu | usunięcie katalogu, `git push --force` | deny + hook `PreToolUse`, ścieżki krytyczne (CLI pyta o `rm` na `/`, `~`), kopia/checkpoint |
| eskalacja przez konfigurację | repozytorium z `.claude/settings.json`, hookami, `.mcp.json` | zaufanie folderu; w `-p` — `--setting-sources ""`/`--bare`, `--strict-mcp-config` |
| eskalacja przez pliki startowe | zapis do `~/.bashrc`, katalogu w `$PATH` | ścieżki chronione, piaskownica `denyWrite`, kontener tylko do odczytu |
| wyciek poświadczeń przez podproces | `env`, `/proc/*/environ`, `cat ~/.claude/.credentials.json` | `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`, `sandbox.credentials`, deny ścieżek |
| obejście listy domen | domain fronting (proxy nie terminuje TLS) | proxy z terminacją TLS, wyjście tylko do znanych usług |
| przejęcie przez rozszerzenie | złośliwy serwer MCP/wtyczka | listy dozwolonych, przegląd kodu, `allowManagedHooksOnly` |
| przeciek między dzierżawcami | wspólny `~/.claude`, pamięć, transkrypty | katalogi per dzierżawca, pamięć wyłączona, osobne `cwd` |

„Lethal trifecta”: dane prywatne + treść niezaufana + kanał wyjścia. Usuń przynajmniej jedno
w każdym przepływie (najczęściej: kanał wyjścia).

## 2. Technologie izolacji

| Technologia | Siła | Narzut | Złożoność | Uwagi |
|---|---|---|---|---|
| piaskownica Bash (sandbox-runtime: bwrap/Seatbelt + proxy) | dobra | bardzo mały | mała | wspólne jądro; bez inspekcji TLS; zagnieżdżona w kontenerze może wymagać `allowAllUnixSockets` lub `enableWeakerNestedSandbox` (słabsza) |
| kontener (Docker) | zależna od konfiguracji | mały | średnia | `--cap-drop ALL`, `no-new-privileges`, seccomp, `--read-only`, `--tmpfs`, `--network none` + gniazdo proxy, limity, `--user` |
| gVisor (`runsc`) | bardzo dobra | średni/duży (I/O do 10–200×) | średnia | wielodzierżawność, treści niezaufane |
| VM (Firecracker, QEMU) | bardzo dobra | duży | średnia/duża | ruch przez vsock do proxy |
| chmura | — | — | — | prywatna podsieć bez bramy, zapora wyjścia tylko do proxy, minimalne IAM, log proxy |

CLI (lub aplikacja SDK) działa **wewnątrz** granicy; kontrolki ograniczają, co agent osiągnie z wnętrza.

## 3. Poświadczenia

- **Wzorzec proxy**: agent wysyła żądania bez poświadczeń, proxy poza granicą je dokłada,
  egzekwuje listę i loguje. Dla API Claude: `ANTHROPIC_BASE_URL` (proxy widzi treść).
  Dla innych HTTPS: proxy z terminacją TLS i zaufanym CA w kontenerze albo narzędzie MCP
  działające poza granicą (agent widzi tylko interfejs narzędzia).
- `HTTP(S)_PROXY` respektuje większość narzędzi; Node `fetch()` dopiero z `NODE_USE_ENV_PROXY=1`
  (Node 24+); pełne pokrycie — proxy przezroczyste (iptables) lub proxychains.
- W CLI: `apiKeyHelper` (rotacja; ponowne uruchomienie przy 401/403), `sandbox.credentials`
  (`deny`/`mask` + `tlsTerminate`), `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`.

Pliki do wykluczenia z montowania lub zablokowania odczytu: `.env`, `.env.local`,
`~/.git-credentials`, `~/.aws/credentials`, `~/.config/gcloud/application_default_credentials.json`,
`~/.azure/`, `~/.docker/config.json`, `~/.kube/config`, `.npmrc`, `.pypirc`,
`*-service-account.json`, `*.pem`, `*.key`, a także `~/.claude/.credentials.json` i `~/.claude.json`.

## 4. Dane i retencja

- Plany komercyjne (Team, Enterprise, API, chmury): bez trenowania na kodzie i promptach;
  retencja zależy od dostawcy; ZDR dla kwalifikowanych kont Enterprise.
- Lokalnie: transkrypty w `<konfiguracja>/projects/` (retencja `cleanupPeriodDays`, czyszczenie
  `claude project purge`), wyniki narzędzi w `tool-results/`, kopie plików do `/rewind`
  (`fileCheckpointingEnabled`).
- Telemetria operacyjna do Anthropic: `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`,
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`; własna OTel bez treści.
- WebFetch: sprawdzenie bezpieczeństwa domeny (wyłączalne `skipWebFetchPreflight` — tylko gdy
  wymaga tego sieć firmowa).
