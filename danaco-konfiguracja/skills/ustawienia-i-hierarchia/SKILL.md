---
name: ustawienia-i-hierarchia
description: >
  Pliki ustawień Claude Code i ich hierarchia: ~/.claude/settings.json, .claude/settings.json,
  .claude/settings.local.json, ustawienia zarządzane (plik, MDM, serwer), --settings, flagi
  i zmienne, ~/.claude.json; kolejność nadpisywania, scalanie list, wyjątki dla kluczy
  bezpieczeństwa, zaufanie folderu, zasięg każdego z 243 kluczy. Stosuj, gdy trzeba ustawić
  lub przenieść klucz, gdy „ustawienie nie działa”, „gdzie to wpisać”, „co wygrywa”,
  „dlaczego kolega tego nie ma”, „settings.json”, „--settings”, oraz do wyszukania klucza
  w przeszukiwalnej referencji settings-reference. Uprawnienia szczegółowo prowadzi
  `uprawnienia-i-tryby`, polityki organizacji — `zarzadzanie-flota`.
---

# Ustawienia i ich hierarchia

## Kiedy stosować

Gdy decydujesz, **w którym miejscu** ustawić klucz, dlaczego ustawiona wartość nie działa,
albo budujesz plik `--settings` dla jednej sesji lub produktu. Ten pakiet daje model
warstw i mapę zasięgów; treść poszczególnych obszarów (uprawnienia, piaskownica, hooki,
MCP…) prowadzą osobne pakiety, do których odsyła tabela na końcu.

## Model warstw — od najsilniejszej

| Poziom | Źródło | Kto obejmuje | Uwagi |
|---|---|---|---|
| 1 | **Zarządzane**: `managed-settings.json` (+ `managed-settings.d/*.json`), MDM/rejestr, ustawienia serwerowe z konsoli claude.ai, `managedSettings` hosta SDK | organizacja, maszyna | nic ich nie nadpisuje poza wyjątkami bezpieczeństwa (niżej); jedyne źródło kluczy o zasięgu `Managed` |
| 2 | **Wiersz poleceń**: `--settings <plik lub JSON>` i flagi kluczy (`--model`, `--effort`, `--permission-mode`…) | jedna sesja | `--settings` scala się z plikami jak kolejny poziom; nie ustawi kluczy `Managed` ani `Global config`; plik ≤ 2 MiB |
| 3 | **Lokalny projektu**: `.claude/settings.local.json` | Ty, ten projekt | CLI sam dopisuje go do globalnych wykluczeń gita; tu trafiają reguły z „Yes, and don't ask again” |
| 4 | **Wspólny projektu**: `.claude/settings.json` | zespół (w repozytorium) | część kluczy czeka na zaufanie folderu; klucze `User…` są ignorowane |
| 5 | **Użytkownika**: `~/.claude/settings.json` (`$CLAUDE_CONFIG_DIR/settings.json`) | Ty, każdy projekt | — |
| obok | `~/.claude.json` | Ty | stan CLI, MCP zakresu `user`/`local`, zaufanie, 12 kluczy `Global config` |

Zmienne środowiskowe **nie są poziomem** tej drabiny: o pierwszeństwie zmiennej względem
klucza decyduje para (np. `ANTHROPIC_MODEL` wygrywa z `model` z każdego pliku,
`ANTHROPIC_DEFAULT_MODEL` działa tylko, gdy żaden plik nie ustawia `model`;
`CLAUDE_CODE_EFFORT_LEVEL` wygrywa z `--effort`, a `--model` wygrywa z `ANTHROPIC_MODEL`).
Wpis klucza w referencji (`szukaj.py <klucz> --pelny`, pole „nadpisania”) mówi, co wygrywa.

## Scalanie — co się sumuje, a co zastępuje

- **Wartości skalarne**: wygrywa najwyższy poziom, który klucz ustawia.
- **Listy się sumują** (`permissions.allow/ask/deny`, `additionalDirectories`, hooki,
  `allowedMcpServers`…): każdy poziom dokłada wpisy, nie usuwa cudzych. Dlatego wyłączenie
  reguły z niższego poziomu robi się regułą `deny`/`ask`, nie „pustą listą” wyżej.
- **Wyjątki od sumowania list**: `fallbackModel` (cały łańcuch z najwyższego źródła),
  `modelPicker` (managed > `--settings` > user; projekt ignorowany; ≥2.1.242),
  `availableModels` (lista zarządzana stosowana w całości), `modelSettings`
  (rozstrzygane model po modelu razem z `effortLevel`).
- **Hooki** z różnych poziomów się sumują; ten sam handler zdefiniowany w dwóch plikach
  uruchamia się raz. `disableAllHooks` spoza ustawień zarządzanych nie wyłącza hooków
  zarządzanych.
- **Reguły uprawnień** łączą się według kolejności *deny → ask → allow* niezależnie od
  poziomu: `allow` z pliku lokalnego nie przebije `ask` z projektu ani zarządzanego.

## Wyjątki — wartość restrykcyjna wygrywa z każdego poziomu

| Klucz | Co jest honorowane mimo wyższego poziomu |
|---|---|
| `disableClaudeAiConnectors` | `true` z dowolnego pliku |
| `enableArtifact` | `false` (lub `disableArtifact: true`) z dowolnego pliku (≥2.1.242) |
| `isolatePeerMachines` | `true` z dowolnego pliku |
| `remoteControlAtStartup` | `false` z plików projektu |
| `crossSessionInbound` | ostrzejsza wartość z plików projektu (`accept` < `hold` < `refuse`) |
| `useAutoModeDuringPlan`, `syncClaudeAiSkills`, `syncClaudeAiPlugins` | `false` z managed, `--settings`, user, local (nie z wspólnego projektu) |
| `maxEffortLevel` | najniższy sufit ze wszystkich źródeł, także `--settings` (≥2.1.267) |

Host osadzający CLI z `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` przejmuje konfigurację modeli
od ustawień zarządzanych (`model`, `fallbackModel`, `modelPicker`, `modelOverrides`).

## Zasięg klucza decyduje, z którego pliku zadziała

Każdy z 243 kluczy ma w dokumentacji zasięg. Wpisanie klucza w złym pliku **nie daje błędu
w `-p`** — CLI po cichu go pomija.

| Zasięg | Działa z | Nie działa z |
|---|---|---|
| `Any file` (155) | każdy plik i `--settings` | — |
| `User or managed` (26) | `~/.claude/settings.json`, managed, `--settings` | `.claude/settings.json`, `.claude/settings.local.json` |
| `User, local, or managed` (4) | user, local, managed (dwa także `--settings`) | wspólny plik projektu |
| `Managed` (45) | tylko ustawienia zarządzane | wszystko inne, także `--settings` |
| `Global config` (12) | tylko `~/.claude.json` (pisze je `/config`) | każdy `settings.json` |

Do tego klucze o ograniczonych **wartościach**: `permissions.defaultMode` `auto`
i `bypassPermissions` nie działają z plików projektu i local (od 2.1.257 także bypass);
`autoMode` nie jest czytany z plików projektu; zmienne telemetrii i katalogów w `env`
projektu są ignorowane (lista w `references/hierarchia-i-scalanie.md`).

## Zaufanie folderu

Okno zaufania pojawia się tylko w sesji interaktywnej. Zachowanie w `-p`/SDK w folderze
nigdy niezaufanym jest **asymetryczne** i to najczęstsza pułapka automatyzacji:

| Co dostarcza repozytorium | Interaktywnie przed zaufaniem | `-p` / SDK, folder niezaufany |
|---|---|---|
| hooki z plików ustawień, blok `env`, `apiKeyHelper`, hooki i `allowed-tools` skilli projektu | czekają na zaufanie | **wykonują się** |
| `permissions.allow`, `additionalDirectories` z `.claude/settings.json` | czekają na zaufanie | **pomijane** (ostrzeżenie na stderr) |
| hooki we frontmatterze podagentów projektu, `extraKnownMarketplaces` | pomijane | pomijane |
| serwery z `.mcp.json` | pytanie przed połączeniem | **łączone bez pytania** |
| `deny`, `ask` | działają | działają |

Przed `claude -p` na cudzym repozytorium: `--setting-sources user` (bez plików projektu
i `.mcp.json`), `--bare`, albo `--settings '{"disableAllHooks": true}'` (samo
ustawienie użytkownika nie wystarczy — projekt może je nadpisać). Zaufanie ręcznie:
`projects["<korzeń repozytorium>"].hasTrustDialogAccepted: true` w `~/.claude.json`.

## Kiedy edycja zaczyna działać

CLI obserwuje pliki i przeładowuje większość kluczy w trakcie sesji (uprawnienia, hooki,
`apiKeyHelper`, `env`). Tylko przy starcie czytane są m.in. `model`, `effortLevel`,
`modelSettings` (w sesji zmienia je `/model`, `/effort`), zmienne OTel, klucze wersji.
Usunięcie zmiennej z `env` działa dopiero po ponownym uruchomieniu.

## Procedura

1. **Znajdź klucz i jego zasięg**:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/szukaj.py" <fraza> --typ klucz --pelny`
   (pełny indeks po kategoriach: `references/indeks-kluczy.md`).
2. **Wybierz warstwę** według tabeli zasięgów i celu: osobiste → user; zespół → projekt;
   tylko u siebie w projekcie → local; jedna sesja/produkt → `--settings`; polityka →
   zarządzane (`zarzadzanie-flota`).
3. **Pokaż, co dziś wygrywa** w danym katalogu:
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/ustawienia-i-hierarchia/scripts/warstwy_ustawien.py" --projekt <katalog> [--settings plik]`.
4. **Zapisz** ścisły JSON z `"$schema": "https://json.schemastore.org/claude-code-settings.json"`
   (komentarz `//` i przecinek końcowy to błąd pliku).
5. **Zwaliduj**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/waliduj_ustawienia.py" <plik> --rodzaj <user|project|local|managed|flaga> --wersja <wersja CLI> --cli "$(command -v claude)"`.
   Warstwa `--cli` uruchamia `claude doctor` w odizolowanym profilu — to walidacja własnym
   schematem binarki, pewniejsza niż schemastore (ten nie zna 45 nowszych kluczy).
6. **Potwierdź w sesji**: `/status` (wiersz „Setting sources”), `claude doctor`
   (sekcja „Invalid settings”); w `-p` brak okna błędu — zawsze sprawdzaj doctorem.

## Pułapki

- `--settings` **nie zastępuje** plików — scala się z nimi. Izolację daje dopiero
  `--setting-sources ""` (albo lista `user,project,local` bez wybranych), a i ona nie
  odcina: ustawień zarządzanych, `~/.claude.json`, pamięci automatycznej, konektorów
  claude.ai, wtyczek wbudowanych (`@builtin`).
- Pojedynczy `/` w regule ścieżki kotwiczy **w źródle ustawień**: w projekcie to katalog
  roboczy, w `~/.claude/settings.json` — `~/.claude`, w pliku `--settings` — katalog tego
  pliku. Ścieżka bezwzględna to `//…`.
- Nieznany klucz lub wartość w starszym CLI może odrzucić **cały plik** (np.
  `attribution: false` przed 2.1.281). Przypinaj wersję i podawaj `--wersja` walidatorowi.
- `/model`, `/config` zapisują do `~/.claude/settings.json`; gdy plik jest tylko do odczytu
  (generowany), zmiana żyje do końca sesji.
- `.claude/settings.local.json` w repozytorium śledzonym przez gita traci przywilej
  „bez zaufania” — jego allow czekają na zaufanie jak wspólny plik.
- Sesje w chmurze czytają tylko wspólny plik projektu i ustawienia serwerowe.

## Minimalne wersje (wybór)

| Funkcja | Wersja |
|---|---|
| `modelPicker`, `promptCacheTtl`, `subagentPromptCacheTtl`, `managedSourcesBehavior` | 2.1.242 |
| plik lokalny w korzeniu repozytorium (wcześniej w katalogu startu) | 2.1.211 |
| `permissions.blockReadsOutsideWorkingDirectories`, `bypassPermissions` ignorowany w projekcie | 2.1.257 |
| `maxEffortLevel` | 2.1.267 |
| `attribution: false` | 2.1.281 |
| zmienne OTel ignorowane w `env` projektu | 2.1.282 |

## Szablony (sprawdzone walidatorem i `claude doctor`)

- `examples/osobiste.user.settings.json` — ustawienia osobiste.
- `examples/zespol.project.settings.json` — wspólny plik zespołu (allow/ask/deny, hook, piaskownica).
- `examples/wlasne-wyjatki.local.settings.json` — nadpisania jednej osoby w projekcie.
- `examples/jedna-sesja.flaga.settings.json` — plik dla `--settings` (próba bez zmian w plikach).

## Powiązane pakiety

| Temat | Pakiet |
|---|---|
| reguły i tryby uprawnień | `uprawnienia-i-tryby` |
| piaskownica | `piaskownica-i-izolacja` |
| hooki | `hooki` |
| MCP | `serwery-mcp` |
| polityki organizacji, flota, wiele kont | `zarzadzanie-flota` |
| zmienne środowiskowe | `zmienne-srodowiskowe` |
| produkt osadzający CLI | `headless-i-osadzanie` |

## Referencje

- `references/hierarchia-i-scalanie.md` — pełne reguły warstw, scalania, zaufania, `env`, chmury.
- `references/indeks-kluczy.md` — 243 klucze po kategoriach z zasięgiem, wersją, opisem PL.
- Indeks maszynowy: `${CLAUDE_PLUGIN_ROOT}/wspolne/indeksy/ustawienia.tsv`.
