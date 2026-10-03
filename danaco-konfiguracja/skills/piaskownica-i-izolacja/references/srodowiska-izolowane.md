# Środowiska izolowane: runtime, kontenery, VM, chmura, usługi wielodzierżawne

Źródła: `cc:sandbox-environments`, `cc:devcontainer`, `cc:agent-sdk/secure-deployment`,
`cc:agent-sdk/hosting`, `anthropic.com/engineering/how-we-contain-claude`,
`pl:managed-agents/self-hosted-sandboxes`. Stan: 01.10.2026.

## 1. Porównanie

| Podejście | Co izoluje | Docker | Wysiłek | Uwagi |
|---|---|---|---|---|
| piaskownica Bash | Bash, PowerShell, Monitor + potomne | nie | niski | MCP, hooki, narzędzia plikowe poza granicą |
| sandbox runtime (`@anthropic-ai/sandbox-runtime`, beta) | cały proces Claude Code | nie | niski | konfiguracja `~/.srt-settings.json` albo `--settings`; domyślnie bez sieci |
| dev container | całe środowisko | tak | średni | wzorzec Anthropic z zaporą iptables „domyślnie odmawiaj” |
| własny kontener | całe środowisko | tak | średni–wysoki | najczęstsze w CI; piaskownica Bash w środku jako druga warstwa |
| maszyna wirtualna (Firecracker, chmura) | system z własnym jądrem | nie | wysoki | najsilniejsza separacja, niezaufany kod |
| sesja w chmurze | VM Anthropic | nie | żaden | proxy z listą domen; token GitHub poza piaskownicą |

Izolacja nie zmienia tego, co wysyłane jest do modelu. Każde podejście z siecią wyjściową
może wyprowadzić dane, które agent przeczyta; zapisywalny katalog projektu może zostać
zmieniony.

## 2. Sandbox runtime — minimum konfiguracji

- zapis: katalog projektu, `~/.claude`, `~/.claude.json`, `/tmp` (na Linuksie ścieżki muszą
  istnieć przed startem: `mkdir -p ~/.claude; [ -f ~/.claude.json ] || echo '{}' > ~/.claude.json`);
- sieć: `api.anthropic.com` (albo punkt dostawcy; przy innym dostawcy zostaw też
  `api.anthropic.com` dla wstępnej kontroli WebFetch, chyba że `skipWebFetchPreflight`),
  `claude.ai` i `platform.claude.com` dla OAuth;
- `denyWrite` dla plików, z których Claude Code wczytuje konfigurację (inaczej sesja może
  zostawić sobie hooki i reguły na następny start);
- brak pliku ustawień = start z blokadą sieci (to nie dowód, że konfiguracja się wczytała);
  plik pusty lub błędny = odmowa startu;
- uruchomienie: `npx @anthropic-ai/sandbox-runtime claude`.

Format pliku runtime opisuje README pakietu (poza dokumentacją Claude Code) — wtyczka nie
zawiera szablonu, bo nie dało się go sprawdzić próbą bez instalacji pakietu npm.

## 3. Dev container

- Claude Code jako użytkownik nie-root, wersja przypięta w obrazie;
- zapora domyślnie odmawiająca, lista dozwolonych hostów (rejestry, GitHub, API);
- trwałość logowania i ustawień przez wolumen na `~/.claude`;
- polityka organizacji: plik `managed-settings.json` w obrazie;
- dopiero w takim kontenerze `--dangerously-skip-permissions` jest dopuszczalne.

## 4. Wzorzec usługi wielodzierżawnej (produkt osadzający CLI)

Zalecenia `cc:agent-sdk/hosting` i `cc:agent-sdk/secure-deployment`, sprawdzone na
architekturze Danaco Nexus:

| Warstwa | Rozwiązanie |
|---|---|
| proces | osobny proces CLI na przebieg, w izolacji systemowej (`bwrap --unshare-all --clearenv --die-with-parent`, kontener, gVisor, Firecracker) |
| system plików | widoczne tylko: binarki, katalog roboczy dzierżawcy, katalog zadania, profil CLI dzierżawcy; sekrety zasłonięte |
| konfiguracja | `CLAUDE_CONFIG_DIR` i `CLAUDE_CODE_PROJECT_DIR_NAME` na dzierżawcę, `--setting-sources ""`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `--settings` z pliku wydania |
| sieć | brak sieci w izolacji; ruch przez proxy poza granicą (`HTTPS_PROXY`) z listą domen i odmową adresów prywatnych |
| poświadczenia | token modelu poza zasięgiem narzędzi (deskryptor pliku `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR` — nieopisany w `cc:env-vars`, obecny w binarce 2.1.286; proxy z wstrzykiwaniem), `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, `sandbox.credentials` |
| narzędzia | serwer MCP produktu poza izolacją (most stdio ↔ gniazdo); hooki `mcp_tool` wykonują logikę poza granicą |
| druga warstwa | piaskownica Bash CLI w trybie ścisłym (zagnieżdżenie — patrz SKILL.md) |
| uprawnienia | `--permission-mode dontAsk`, `--permission-prompts none`, `disableAutoMode`, `disableBypassPermissionsMode`, deny `Agent(model:*)`, `Agent(isolation:*)` |
| zasoby | `CLAUDE_CODE_TOOL_MEMORY_LIMIT` (Linux, ≥2.1.233), limity cgroup/`prlimit` |

Ustawienia serwerowe organizacji pobierane przy kwalifikującym poświadczeniu działają
niezależnie od izolacji plików — sprawdzaj je `claude doctor` w środowisku usługi.

## 5. Managed Agents a własna izolacja

W Claude Managed Agents środowisko (`environments`: pakiety, `networking: limited` z
`allowed_hosts`, `allow_package_managers`, `allow_mcp_servers`) i piaskownica
samodzielnie hostowana (worker, pliki montowane, narzędzia własne) odpowiadają w CLI:
piaskownicy Bash z `allowedDomains`/`strictAllowlist` plus izolacji całego procesu na
własnym serwerze. Limit wyjścia narzędzia w MA (100 000 znaków → plik) odpowiada w CLI
`MAX_MCP_OUTPUT_TOKENS`, `_meta["anthropic/maxResultSizeChars"]` i `bashOutputMaxChars`.
