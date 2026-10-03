# Historia zmian

Zapis prowadzony w układzie Keep a Changelog. Wersje zgodne z wersjonowaniem semantycznym.

## [1.0.0] — 2026-10-02

Pierwsze wydanie. Sprawdzane na kliencie Claude Code 2.1.286 (atrapa API, `claude doctor`,
`claude plugin validate --strict`), dokumentacja z 01–02.10.2026. Dodatkowo zweryfikowane na
żywym modelu na kliencie 2.1.284: `claude plugin eval` (przypadki przykładowe, obie zaliczone)
oraz polecenie `/audyt-konfiguracji` z podagentem `audytor-konfiguracji`.

### Dodane

- 15 skilli z referencjami, skryptami i szablonami: `ustawienia-i-hierarchia`,
  `uprawnienia-i-tryby`, `piaskownica-i-izolacja`, `hooki`, `serwery-mcp`,
  `podagenci-i-zespoly`, `budowa-skilli`, `wtyczki-i-marketplace`,
  `instrukcja-systemowa-i-pamiec`, `headless-i-osadzanie`, `model-cache-i-koszty`,
  `zmienne-srodowiskowe`, `zarzadzanie-flota`, `diagnostyka`, `bezpieczenstwo-wdrozenia`.
- Polecenie `/audyt-konfiguracji` i podagent `audytor-konfiguracji` (tylko odczyt, raport
  z priorytetami); zbieracz dowodów `scripts/audyt_konfiguracji.py`.
- Indeksy wyszukiwalne (`wspolne/indeksy/`): 243 klucze ustawień, 376 zmiennych, 79 flag,
  46 narzędzi, 33 zdarzenia hooków; wyszukiwarka `scripts/szukaj.py`; odświeżanie
  `scripts/indeksy/odswiez_indeksy.py` z zachowaniem opisów polskich.
- Walidator ustawień `scripts/waliduj_ustawienia.py` (JSON, schemat schemastore z korektą
  zaległości, reguły dokumentacji, `claude doctor`), generator profili `--settings`
  `scripts/generuj_ustawienia.py` (czat, kod, ci, tylko-odczyt), atrapa Messages API
  `scripts/atrapa_api.py` i próby bez modelu `scripts/proba_cli.py`, sprawdzanie
  wszystkich przykładów `scripts/sprawdz_przyklady.py`.
- Testy `tests/uruchom_testy.sh` (21 testów; z `CLAUDE_BIN` także próby z CLI i walidacja
  manifestów wtyczki i marketplace).
- Mapa pokrycia dokumentacji `wspolne/pokrycie-dokumentacji.md` (281 stron → skille).
- Przykładowa wtyczka ucząca `skills/budowa-skilli/examples/` (`narzedzia-wydania`): skille
  `przeglad-migracji` i `polecenie-wdrozenia` oraz przypadki `claude plugin eval` w `evals/`,
  gotowe do uruchomienia (`claude plugin eval skills/budowa-skilli/examples`).
- Manifest marketplace `.claude-plugin/marketplace.json` (marketplace `danaco`, wpis
  `danaco-konfiguracja` ze źródłem `.`) — wtyczka gotowa do rejestracji
  (`claude plugin marketplace add <katalog>`), bez publikacji.
