# Zgłoszenie problemu z konfiguracją Claude Code

> Wypełnij bez sekretów: żadnych tokenów, kluczy, haseł, wartości zmiennych z `TOKEN`/`KEY`/`SECRET`.
> Wyniki narzędzi wklejaj z raportu `zbierz_diagnostyke.py` (maskuje klucze i nagłówki `Bearer`).

## 1. Co nie działa

- Oczekiwane zachowanie:
- Rzeczywiste zachowanie (dokładny komunikat):
- Tryb: interaktywny / `-p` / Agent SDK / usługa (nazwa):
- Od kiedy (wersja CLI przed i po):

## 2. Środowisko

- `claude --version`:
- System i powłoka:
- Dostawca: Anthropic API / Bedrock / Agent Platform / Foundry / brama:
- `CLAUDE_CONFIG_DIR` (ścieżka, bez zawartości):

## 3. Co się załadowało

- `/status` — `Setting sources` i `Skipped sources`:
- `/context` — czy plik/skill/serwer jest obecny:
- `/permissions`, `/hooks`, `/mcp` — odpowiedni fragment:

## 4. Wyniki narzędzi

- `claude doctor` (sekcje Invalid settings, Managed settings, Organization policy):
- `zbierz_diagnostyke.py` — sekcja „Wnioski”:
- `waliduj_ustawienia.py PLIK --rodzaj … --cli claude`:

## 5. Izolacja

- [ ] `claude --safe-mode` — problem występuje? tak / nie
- [ ] czysty profil (`CLAUDE_CONFIG_DIR=/tmp/claude-czysty`) — tak / nie
- [ ] próba na atrapie (`proba_cli.py -- <flagi>`) — wynik:

## 6. Fragment logu debug

```
(wiersze z --debug-file dotyczące problemu, po przeglądzie pod kątem danych wrażliwych)
```
