# Hooki danaco-plugin

Dwa hooki: kontrola po zapisie pliku (`po_zapisie`) i obowiązek opisu programów oraz skilla
maszyny (`obowiazek_opisu`). Rejestracja: `hooks.json`.

## Obowiązek opisu i skilla maszyny

`obowiazek_opisu.py` (wrapper `obowiazek_opisu.sh`):

| Zdarzenie | Matcher | Działanie |
| --- | --- | --- |
| `PostToolUse` (`po`) | `opis`, `maszyna` serwera `danaco-programy` | zapisuje w stanie sesji przeczytany program i skill; `opis` samego skilla i `maszyna` ze skillem zaliczają skill |
| `PreToolUse` (`przed`) | Bash, Monitor, zapis plików, `uruchom` | odmawia, gdy polecenie używa programu z rejestru bez przeczytanego w sesji `opis`, gdy wchodzi na maszynę (`danaco-srodowisko <strefa> <operacja>` albo nakładka maszyny z operacją inną niż `stan`, `kolejka`, pomoc) bez przeczytanego w sesji skilla tej maszyny, gdy strefa nie jest podana dosłownie, oraz gdy sięga do katalogu stanu |

Programy: `katalog/rejestr/*.json`; maszyny (strefa, skill, nakładka): `katalog/maszyny.json`.
Bez rejestru hook niczego nie blokuje, bez wykazu maszyn nie egzekwuje skilli maszyn. Testy:
`tests/test_obowiazek_opisu.py`.

## Kontrola po zapisie

`PostToolUse` z matcherem `^(Write|Edit|MultiEdit|NotebookEdit)$`. Po każdym zapisie pliku Claude
Code woła `hooks/po_zapisie.sh`, a ten uruchamia `hooks/po_zapisie.py`.

### Co robi

`po_zapisie.py` czyta zdarzenie PostToolUse ze standardowego wejścia, bierze ścieżkę zapisanego
pliku (`file_path`/`notebook_path`/`path`) i — jeśli to plik kodu (`.py`, `.go`, `.ts`, `.tsx`,
`.js`, `.jsx`, `.rs`) — uruchamia na nim dwa walidatory:

- `skills/weryfikatory-dyscypliny/scripts/style_guard.py` — limit długości komentarza, udział
  komentarzy, wymyślone kody, ton nieformalny, kodowanie pliku;
- `skills/standardy-nazewnictwa/scripts/nazwy_guard.py` — wymyślone oznaczenia komponentów,
  etykiety UI jako zdania, nazwy metaforyczne.

Progi i allowlisty: `scripts/konfiguracja_kontroli.py` oraz opcjonalny
`konfiguracja-dyscypliny.json` w korzeniu sprawdzanego repozytorium.

### Kontrakt wyjścia

| Sytuacja | Kod | Wyjście |
| --- | --- | --- |
| plik czysty albo spoza zakresu kontroli | 0 | brak |
| naruszenia (blokujące lub ostrzeżenia) | 2 | raport na stderr — Claude Code dokłada go do kontekstu tury, nie blokuje narzędzia (plik jest już zapisany) |
| brak ścieżki, zły JSON, brak modułów, zła konfiguracja | 0 | brak (fail-open) |

Kod 2 w zdarzeniu `PostToolUse` nie cofa zapisu — przekazuje tylko raport modelowi. Usterka
kontroli nigdy nie przerywa pracy: każdy błąd hooka kończy się kodem 0.

### Interpreter

`po_zapisie.sh` szuka interpretera tak jak `tests/uruchom_testy.sh` (`python3`, `python`, `py -3`)
i wymaga Pythona 3.10+. Korzeń pluginu bierze z `CLAUDE_PLUGIN_ROOT`, a przy jego braku z
położenia wrappera, więc hook działa też bez tej zmiennej.

### Testy

`tests/test_po_zapisie.py` woła prawdziwy wrapper `sh` z JSON-em zdarzenia na stdin i sprawdza
kody wyjścia oraz treść raportu, a także kontrakt `hooks.json` wobec plików pluginu.
