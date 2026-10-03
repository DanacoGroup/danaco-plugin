---
name: diagnostyka
description: >
  Diagnostyka konfiguracji Claude Code: co faktycznie się załadowało (/context, /status,
  /hooks, /mcp, /permissions, /skills, /memory), claude doctor i /doctor, /debug,
  --debug i --debug-file (kategorie, czytanie logu), --safe-mode i czysty profil
  (CLAUDE_CONFIG_DIR), typowe objawy i przyczyny (hook nie działa, skill się nie wyzwala,
  serwer MCP bez narzędzi, ustawienie ignorowane, tryb uprawnień inny niż ustawiony),
  komunikaty błędów API, logowania, sieci i limitów, ponawianie. Stosuj przy „nie działa”,
  „ignoruje ustawienie”, „hook się nie odpala”, „MCP nie łączy”, „błąd API”, „doctor
  pokazuje…”, „jak zdiagnozować”.
---

# Diagnostyka konfiguracji

## Kiedy stosować

Gdy konfiguracja nie działa tak, jak zapisano: coś się nie załadowało, załadowało z innego
miejsca, zostało nadpisane albo CLI zgłasza błąd. Zasada: **najpierw zobacz, co się
załadowało, dopiero potem zmieniaj pliki**.

## Kolejność kroków

1. **Zbierz stan bez zmian**:
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/diagnostyka/scripts/zbierz_diagnostyke.py" --projekt . [--konfiguracja ~/.claude]`
   — `claude doctor`, walidacja plików każdej warstwy, `.mcp.json`, nazwy zmiennych (bez wartości),
   CLAUDE.md/skille/agenci, piaskownica, zaślepki, logi debug → raport `diagnostyka.md`.
2. **W sesji**: `/context` (co zajmuje kontekst: instrukcja, narzędzia, MCP, agenci, pamięć, skille),
   potem `/status` (źródła ustawień, zarządzane, logowanie), `/permissions`, `/hooks`, `/mcp`,
   `/skills`, `/memory`. `/doctor` — pełny przegląd z propozycjami poprawek.
3. **Izoluj**: `claude --safe-mode` (bez CLAUDE.md, skilli, wtyczek, hooków, MCP, poleceń, agentów;
   polityka zarządzana nadal działa). Problem znika → winna personalizacja. Nie znika →
   czysty profil: `cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-czysty claude` (wymaga ponownego logowania).
   Bez modelu i konta: `${CLAUDE_PLUGIN_ROOT}/scripts/proba_cli.py -- <flagi>` (atrapa API).
4. **Obserwuj na żywo**: `claude --debug-file /ścieżka/log.txt` (albo `--debug=mcp,hooks`,
   `/debug [opis]` w sesji) i przeszukaj log wg `references/dziennik-debug.md`.
5. **Napraw jedną rzecz**, zwaliduj (`${CLAUDE_PLUGIN_ROOT}/scripts/waliduj_ustawienia.py PLIK --rodzaj … --cli claude`),
   sprawdź ponownie tym samym narzędziem.

## Najczęstsze przyczyny (skrót; pełna tabela — `references/objawy-i-przyczyny.md`)

| Objaw | Najpierw sprawdź |
|---|---|
| ustawienie ignorowane | wyższa warstwa (local > project > user; zarządzane; `--settings`), zmienna środowiskowa, klucz o złym zasięgu (np. `Managed` w pliku użytkownika), plik odrzucony w całości przez błąd schematu (`claude doctor`) |
| `permissions`/`hooks`/`env` w `~/.claude.json` | to stan aplikacji — przenieś do `~/.claude/settings.json` |
| hook się nie odpala | matcher jako tablica (odrzuca cały plik), małe litery (`bash`), przecinek przed 2.1.191, hooki w osobnym pliku zamiast `settings.json`, `disableAllHooks`, `allowManagedHooksOnly` |
| serwer MCP bez narzędzi | `.mcp.json` w `.claude/` lub klucz `servers`, brak zgody na serwer projektu, względna ścieżka w `command`, `mcpServers` w `settings.json` (nieczytane) |
| skill niewidoczny / niewyzwalany | plik `.md` zamiast katalogu z `SKILL.md`, `disable-model-invocation`, opis nie pasuje do próśb, budżet listy skilli, `skillOverrides` |
| tryb uprawnień inny niż podany | `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` wymusza `default` (stderr), `disableBypassPermissionsMode`/`disableAutoMode`, `-p` bez jawnego trybu startuje w `auto` (≥2.1.285) |
| allow nie działa w `-p` | folder niezaufany — reguły allow projektu pominięte (stderr), polecenie z `$ZMIENNA` („Contains simple_expansion”), goła reguła `Edit` nie obejmuje `Write` |
| zapis zgody „don't ask again” nie działa | 0-bajtowe zaślepki po przerwanej piaskownicy (`claude doctor`: „Stale sandbox mask files”) |

## Pułapki

- `claude doctor` czyta ustawienia bieżącego katalogu **bez pytania o zaufanie** — uruchamiaj
  go w katalogu projektu, którego dotyczy problem.
- Ustawienia zarządzane obowiązują także w `--safe-mode` i czystym profilu — sprawdź `/status`.
- Log debug zawiera ścieżki, nazwy serwerów i fragmenty poleceń — przed przekazaniem dalej
  usuń dane wrażliwe; skrypt wtyczki maskuje klucze `sk-ant-…` i nagłówki `Bearer`.
- Zmiana `settings.json` działa w trwającej sesji po chwili (także nowy `.claude/`, ≥2.1.257);
  OTel, `model` z ustawień serwerowych i część kluczy — dopiero po restarcie.
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` zostawia w katalogu roboczym puste zaślepki także po
  normalnym zakończeniu (próba 2.1.286) i `claude doctor` ich nie zgłasza (zgłasza tylko zaślepki
  piaskownicy z izolacją plików) — `zbierz_diagnostyke.py` je wykrywa.
- Na tej maszynie log debug pokazuje „this machine has managed settings” — polityka zarządzana
  istnieje; sprawdzaj ją `/status`, nie zakładaj czystego środowiska.

## Szablony

- `examples/zgloszenie-problemu.md` — szablon opisu problemu z wynikami narzędzi (bez sekretów).

## Referencje

- `references/objawy-i-przyczyny.md` — objawy konfiguracji, przyczyny, naprawy (dokumentacja + próby).
- `references/dziennik-debug.md` — włączanie logu, kategorie, wzorce wierszy do wyszukiwania.
- `references/bledy-i-ponawianie.md` — komunikaty API, logowania, sieci, limitów, żądań, wtyczek; ponawianie i jego strojenie.
