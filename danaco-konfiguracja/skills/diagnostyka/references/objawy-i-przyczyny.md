# Objawy, przyczyny, naprawy

Źródła: `cc:debug-your-config` (Check common causes), `cc:troubleshooting`,
`cc:troubleshoot-install`, `cc:errors` (Configuration warnings), próby 2.1.286 na atrapie
(pakiety 1–13 tej wtyczki).

## Ustawienia i uprawnienia

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| wartość z `settings.json` nie działa | ten sam klucz w `settings.local.json`, wyższej warstwie lub zmiennej | `/status`; `scripts/warstwy_ustawien.py` (pakiet `ustawienia-i-hierarchia`) |
| cały plik ignorowany | błąd schematu (np. matcher jako tablica) — plik user/project/local odrzucany w całości | `claude doctor` → sekcja `Invalid settings`; walidator wtyczki |
| klucz bez efektu | zasięg `Managed`/`User or managed` w złym pliku; klucz nowszy niż CLI | `scripts/szukaj.py KLUCZ --pelny` (zasięg, wersja) |
| `permissions`/`hooks`/`env` w `~/.claude.json` | to plik stanu aplikacji | przenieś do `~/.claude/settings.json` |
| reguły allow projektu nie działają w `-p` | folder niezaufany: hooki i `env` projektu działają, allow pomijane (ostrzeżenie na stderr) | zaufaj folderowi interaktywnie albo przenieś reguły do `--settings` |
| `Bash(npm *)` nie zatwierdza `npm run $CEL` | rozwinięcie zmiennej („Contains simple_expansion”) | polecenie bez zmiennych lub hook `PermissionRequest` |
| allow `Edit` nie zatwierdza `Write` | goła nazwa obejmuje tylko narzędzie Edit (próba) | `Edit(./**)` lub `"Edit","Write"` |
| deny `Edit` nie blokuje `Write` | jw. (próba: Write przeszedł w `acceptEdits` i `bypassPermissions`) | `Edit(**)` lub oba narzędzia |
| tryb `default` mimo `--permission-mode` | `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` (stderr „Permission mode forced to default”) | lista allow zamiast trybu albo `…SCRUB=0` |
| `-p` w trybie `auto` | brak jawnego trybu, a flagi funkcji niepobrane (≥2.1.285) | zawsze `--permission-mode` |
| `Bash(rm *)` w deny nie blokuje `/bin/rm`, `find -delete` | reguły dopasowują tekst polecenia | hook `PreToolUse` lub piaskownica |
| zapis „Yes, and don't ask again” nie działa | 0-bajtowa zaślepka piaskownicy w miejscu pliku ustawień | usuń zaślepkę przy zamkniętych sesjach; `claude doctor` ją wskaże |
| zapis ustawień po `/config` wraca | wartość narzuca warstwa wyższa lub zarządzana | `/status` |

## Hooki

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| hook nie widoczny w `/hooks` | hooki w osobnym pliku (poza wtyczką), plik ustawień odrzucony, `disableAllHooks`, `allowManagedHooksOnly` | klucz `hooks` w `settings.json` |
| widoczny, ale się nie odpala | matcher: wielkość liter, literówka, przecinek < 2.1.191, `mcp__serwer` bez `__.*` | `"Edit|Write"`, `mcp__serwer__.*`; `scripts/test_hooka.py` (pakiet `hooki`) |
| hook `mcp_tool` nie działa na `SessionStart` | typ pomijany na `SessionStart`/`Setup` | typ `command` |
| decyzja JSON ignorowana | wyjście nie zaczyna się od `{` (log: „Hook output does not start with {, treating as plain text”), kod ≠ 0 | czyste JSON na stdout, kod 0 |
| sprzątanie przy końcu się nie wykonuje | brak `SessionEnd` lub przekroczony limit (`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`) | hook `SessionEnd`, krótkie działanie |

## MCP

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| serwery z `.mcp.json` się nie ładują | plik w `.claude/` albo klucz `servers` (format VS Code) | `.mcp.json` w korzeniu, klucz `mcpServers` |
| serwery w `settings.json` | `settings.json` nie czyta `mcpServers` | `.mcp.json` lub `claude mcp add --scope user` |
| serwer projektu nie pojawia się | odrzucona jednorazowa zgoda | `/mcp` → zatwierdź |
| serwer nie startuje z niektórych katalogów | względna ścieżka w `command`/`args` | ścieżki absolutne |
| connected, 0 narzędzi | serwer nie zwraca listy | `/mcp` → Reconnect; `claude --debug=mcp`, stderr serwera w logu |
| brak zmiennych środowiskowych w serwerze | CLI usuwa część zmiennych z podprocesów (OTel, przy SCRUB poświadczenia) | `env` w wpisie serwera |
| instrukcje serwera ucięte | limit 2048 znaków | `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` (próba: 8000 → pełne) |
| wszystkie narzędzia MCP w kontekście | tool search wyłączony przy własnym `ANTHROPIC_BASE_URL` (log: `[ToolSearch:optimistic] disabled`) | `ENABLE_TOOL_SEARCH`, `alwaysLoad` tylko dla rdzenia |

## Skille, agenci, pamięć

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| skill nie w `/skills` | `.claude/skills/nazwa.md` zamiast `nazwa/SKILL.md`; błędny frontmatter | katalog + `SKILL.md`; `scripts/sprawdz_skill.py` |
| skill nie wyzwalany | `disable-model-invocation: true`, opis nie pasuje, budżet listy, `skillOverrides`, w `dontAsk` brak zgody na narzędzie `Skill` | opis z frazami użytkownika; allow `Skill` |
| CLAUDE.md z podkatalogu ignorowany | ładowany dopiero po odczycie pliku z katalogu (Read) | instrukcje krytyczne w głównym CLAUDE.md |
| podagent ignoruje CLAUDE.md | Explore i Plan pomijają CLAUDE.md; `omitClaudeMd` | instrukcja w prompcie delegacji lub w ciele agenta |
| reguła `paths` nie działa | ładowana dopiero po dotknięciu pasującego pliku (próba: brak w pierwszym żądaniu) | reguły bez `paths` dla zasad ogólnych |
| zła instrukcja po wznowieniu | utrwalona instrukcja (snapshot `on`) | `--system-prompt-snapshot off` |

## Środowisko, sieć, instalacja

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| zmienna nie działa | literówka; ustawiona w projekcie, a należy do ignorowanych; usunięta (no-op) | `sprawdz_zmienne.py` (pakiet `zmienne-srodowiskowe`) |
| piaskownica: „Failed to create bridge sockets” | za długa ścieżka `TMPDIR` (gniazda Unix) | krótszy `TMPDIR` |
| piaskownica: `apply-seccomp … setgroups` | zagnieżdżone przestrzenie nazw (kontener, jądro) | `network.allowAllUnixSockets: true` lub `enableWeakerNestedSandbox` |
| CLI czeka 3 s na start w skrypcie | otwarte stdin bez danych | `< /dev/null` |
| prompt połknięty przez flagę | flagi wieloargumentowe (`--allowed-tools`, `--mcp-config`, `--add-dir`) | prompt zaraz po `-p` lub przez stdin |
| `command not found: claude` | PATH bez `~/.local/bin` | `claude doctor` podaje poprawkę |
| `claude update`/`doctor` wisi | sieć/proxy, blokada pliku | `cc:troubleshoot-install` |
| TLS/SSL | proxy z inspekcją TLS bez CA | `NODE_EXTRA_CA_CERTS`, `CLAUDE_CODE_CERT_STORE` |
| „Settings file exceeds the 2MiB limit” | zbyt duży plik ustawień (np. setki reguł) | uprość reguły |
| „The current directory no longer exists” | katalog roboczy usunięty w trakcie | odtwórz katalog lub uruchom z innego |

## Jakość odpowiedzi

Bez błędów, a odpowiedzi „słabsze”: przełączenie modelu po klasyfikatorze (sesja zostaje na
modelu zapasowym), długi kontekst przed kompakcją, sprzeczne instrukcje w CLAUDE.md, niski effort.
Sprawdź `/model`, `/context`, `/usage`; `claude --safe-mode` wyklucza wpływ personalizacji.
