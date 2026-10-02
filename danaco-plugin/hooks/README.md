# Hooki danaco-plugin

Jedno zdarzenie: `PostToolUse` z matcherem `^(Write|Edit|MultiEdit|NotebookEdit)$`. Po każdym
zapisie pliku Claude Code woła `hooks/po_zapisie.sh`, a ten uruchamia `hooks/po_zapisie.py`.

## Co robi

`po_zapisie.py` czyta zdarzenie PostToolUse ze standardowego wejścia, bierze ścieżkę zapisanego
pliku (`file_path`/`notebook_path`/`path`) i — jeśli to plik kodu (`.py`, `.go`, `.ts`, `.tsx`,
`.js`, `.jsx`, `.rs`) — uruchamia na nim dwa walidatory:

- `skills/weryfikatory-dyscypliny/scripts/style_guard.py` — limit długości komentarza, udział
  komentarzy, wymyślone kody, ton nieformalny, kodowanie pliku;
- `skills/standardy-nazewnictwa/scripts/nazwy_guard.py` — wymyślone oznaczenia komponentów,
  etykiety UI jako zdania, nazwy metaforyczne.

Progi i allowlisty: `scripts/konfiguracja_kontroli.py` oraz opcjonalny
`konfiguracja-dyscypliny.json` w korzeniu sprawdzanego repozytorium.

## Kontrakt wyjścia

| Sytuacja | Kod | Wyjście |
| --- | --- | --- |
| plik czysty albo spoza zakresu kontroli | 0 | brak |
| naruszenia (blokujące lub ostrzeżenia) | 2 | raport na stderr — Claude Code dokłada go do kontekstu tury, nie blokuje narzędzia (plik jest już zapisany) |
| brak ścieżki, zły JSON, brak modułów, zła konfiguracja | 0 | brak (fail-open) |

Kod 2 w zdarzeniu `PostToolUse` nie cofa zapisu — przekazuje tylko raport modelowi. Usterka
kontroli nigdy nie przerywa pracy: każdy błąd hooka kończy się kodem 0.

## Interpreter

`po_zapisie.sh` szuka interpretera tak jak `tests/uruchom_testy.sh` (`python3`, `python`, `py -3`)
i wymaga Pythona 3.10+. Korzeń pluginu bierze z `CLAUDE_PLUGIN_ROOT`, a przy jego braku z
położenia wrappera, więc hook działa też bez tej zmiennej.

## Testy

`tests/test_po_zapisie.py` woła prawdziwy wrapper `sh` z JSON-em zdarzenia na stdin i sprawdza
kody wyjścia oraz treść raportu, a także kontrakt `hooks.json` wobec plików pluginu.
