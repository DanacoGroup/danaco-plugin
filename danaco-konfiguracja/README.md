# danaco-konfiguracja

Wtyczka daje agentowi pełną wiedzę i narzędzia do poprawnej konfiguracji Claude Code
i Claude Code CLI — w trybie interaktywnym, w trybie `-p`, w aplikacjach na Agent SDK
i w produktach, które osadzają CLI dla wielu użytkowników.

**Informacje szczegółowe dokumentu:**

| | |
|---|---|
| **Tytuł** | danaco-konfiguracja — opis wtyczki |
| **Klasa dokumentu** | Stan wdrożenia |
| **Odbiorcy** | administrator i agent konfigurujący Claude Code |
| **Przeznaczenie** | opisuje zawartość wtyczki, wymagania, sposób użycia, narzędzia i ograniczenia |
| **Zakres** | skille, polecenie i podagent audytu, skrypty, indeksy, testy, struktura katalogów |
| **Poza zakresem** | treść merytoryczna poszczególnych obszarów — w plikach `SKILL.md` i `references/` |
| **Dokumenty powiązane** | [CHANGELOG.md](CHANGELOG.md) · [LICENSE](LICENSE) · [wspolne/pokrycie-dokumentacji.md](wspolne/pokrycie-dokumentacji.md) |
| **Wersja wtyczki** | 1.0.0 |
| **Sprawdzona na** | Claude Code 2.1.286, dokumentacja z 01–02.10.2026 |
| **Data** | 2026-10-02 |

## Spis treści

1. [Do czego służy](#1-do-czego-służy)
2. [Wymagania](#2-wymagania)
3. [Użycie bez instalacji](#3-użycie-bez-instalacji)
4. [Skille](#4-skille)
5. [Polecenie i podagent audytu](#5-polecenie-i-podagent-audytu)
6. [Skrypty](#6-skrypty)
7. [Próby bez modelu — atrapa API](#7-próby-bez-modelu--atrapa-api)
8. [Testy](#8-testy)
9. [Struktura katalogów](#9-struktura-katalogów)
10. [Utrzymanie](#10-utrzymanie)
11. [Znane ograniczenia](#11-znane-ograniczenia)
12. [Licencja](#12-licencja)

## 1. Do czego służy

- **Uczy decyzji**, nie tylko kluczy: każdy skill ma tabelę „kiedy co stosować”, kolejność
  nadpisań, minimalne wersje CLI i sekcję pułapek potwierdzonych próbami.
- **Sprawdza konfigurację maszynowo**: walidator ustawień (JSON, schemat, reguły dokumentacji,
  `claude doctor`), lint reguł, hooków, MCP, agentów, skilli, zmiennych, polityki zarządzanej,
  lista kontrolna bezpieczeństwa.
- **Generuje** gotowe profile `--settings` + flagi + zmienne dla produktów osadzających CLI.
- **Pozwala sprawdzić zachowanie CLI bez modelu i konta** — lokalna atrapa Messages API.
- **Audytuje** konto i projekt i kończy się raportem z priorytetami poprawek.

Koszt stały w sesji: ok. 2,9 tys. tokenów (lista 15 skilli, polecenie, agent —
`claude plugin details`); treść skilla (1,2–3 tys. tokenów) ładuje się dopiero po wywołaniu.

## 2. Wymagania

- Claude Code ≥ 2.1.281 (zalecane 2.1.286 — na niej sprawdzono wszystkie próby).
- Python ≥ 3.10 (tylko biblioteka standardowa; `jsonschema` użyty, jeśli jest).
- Do prób piaskownicy na Linuksie: `bwrap` i `socat` (pakiety systemowe zatwierdza właściciel serwera).

## 3. Użycie bez instalacji

```sh
claude --plugin-dir /danaco/wymiana/admin/wtyczki-robocze/danaco-konfiguracja
```

Skille mają przestrzeń nazw `danaco-konfiguracja:` (np. `/danaco-konfiguracja:hooki`),
polecenie: `/danaco-konfiguracja:audyt-konfiguracji [projekt] [profil]`.
Skrypty działają też samodzielnie (`python3 scripts/…`).

## 4. Skille

| Skill | Zakres | Narzędzia |
|---|---|---|
| `ustawienia-i-hierarchia` | warstwy, scalanie, wyjątki, zasięgi kluczy, indeks 243 kluczy | `warstwy_ustawien.py` |
| `uprawnienia-i-tryby` | składnia reguł, tryby, `dontAsk`, auto i klasyfikator, ścieżki chronione, host zgód | `sprawdz_reguly.py`, `proba_regul.py` |
| `piaskownica-i-izolacja` | bwrap/Seatbelt, sieć, poświadczenia deny/mask, kontenery, zagnieżdżanie | `sprawdz_srodowisko.sh`, `proba_piaskownicy.py` |
| `hooki` | 33 zdarzenia, 5 typów, decyzje, `CLAUDE_ENV_FILE`, 15 przepisów | `test_hooka.py` |
| `serwery-mcp` | zakresy, `.mcp.json`, polityki, tool search, limity, projektowanie narzędzi | `sprawdz_mcp.py` (+ serwer wzorcowy) |
| `podagenci-i-zespoly` | definicje, model, limity, workflowy, zespoły, `--agents` | `sprawdz_agenta.py` |
| `budowa-skilli` | frontmatter, lista i budżet, `skillOverrides`, skille uczące, ewaluacje | `sprawdz_skill.py` |
| `wtyczki-i-marketplace` | manifest, komponenty, `userConfig`, marketplace, polityki, dystrybucja | `sprawdz_wtyczke.sh` |
| `instrukcja-systemowa-i-pamiec` | flagi instrukcji, znacznik granicy, snapshot, CLAUDE.md, reguły, style | `buduj_instrukcje.py`, `audyt_pamieci.py` |
| `headless-i-osadzanie` | `-p`, stream-json, sesje, przerwanie, izolacja dzierżawców, SDK i Managed Agents | `host_stream_json.py` |
| `model-cache-i-koszty` | modele, effort, fallback, prompt cache i TTL, koszty, OpenTelemetry | `zadania_cache.py`, `analiza_cache.py` |
| `zmienne-srodowiskowe` | 376 zmiennych w 20 kategoriach, źródła i pierwszeństwo | `sprawdz_zmienne.py`, `buduj_indeks_md.py` |
| `zarzadzanie-flota` | źródła zarządzane, first-wins/merge, fail closed, aktualizacje, logowanie, wiele kont | `sprawdz_zarzadzane.py` |
| `diagnostyka` | `/context`, `doctor`, debug, objawy → przyczyny, błędy i ponawianie | `zbierz_diagnostyke.py` |
| `bezpieczenstwo-wdrozenia` | model zagrożeń, warstwy, lista kontrolna produkcji | `lista_kontrolna.py` |

## 5. Polecenie i podagent audytu

- `commands/audyt-konfiguracji.md` — uruchamia `scripts/audyt_konfiguracji.py` (dowody w
  `$TMPDIR/audyt-claude-<czas>/`), deleguje analizę do podagenta lub robi ją sam, zwraca raport:
  problemy krytyczne / ważne / zalecenia z dowodem, poprawką i sposobem weryfikacji.
- `agents/audytor-konfiguracji.md` — tylko odczyt, narzędzia `Bash` i `Read`, wstępnie ładuje
  skille `bezpieczenstwo-wdrozenia` i `diagnostyka` (próba: treść obu w pierwszym żądaniu podagenta).

## 6. Skrypty

| Skrypt | Do czego |
|---|---|
| `scripts/szukaj.py` | wyszukiwanie w indeksach: klucz, zmienna, flaga, narzędzie, hook (`--zasieg`, `--od-wersji`, `--pelny`) |
| `scripts/waliduj_ustawienia.py` | walidacja pliku ustawień: JSON, schemat, reguły dokumentacji, `--rodzaj`, `--wersja`, `--cli` (`claude doctor`) |
| `scripts/generuj_ustawienia.py` | profile `czat`, `kod`, `ci`, `tylko-odczyt`: `settings.json` + flagi + zmienne, z walidacją |
| `scripts/atrapa_api.py` | lokalna atrapa Messages API ze scenariuszem wywołań narzędzi |
| `scripts/proba_cli.py` | uruchomienie CLI na atrapie w izolowanym profilu i streszczenie (`init`, hooki, wynik, żądania) |
| `scripts/audyt_konfiguracji.py` | zbieranie dowodów do audytu |
| `scripts/sprawdz_przyklady.py` | sprawdzenie wszystkich przykładów wtyczki według konwencji nazw |
| `scripts/indeksy/odswiez_indeksy.py` | pobranie dokumentacji i przebudowa indeksów z raportem różnic |
| `scripts/cc_wspolne.py` | wspólne funkcje (indeksy, wersje, JSON, schemat, sekrety) |

Konwencja nazw szablonów: `<opis>.<rodzaj>.settings.json`, gdzie rodzaj to `user`, `project`,
`local`, `managed` albo `flaga` (dla `--settings`).

## 7. Próby bez modelu — atrapa API

`proba_cli.py` uruchamia CLI z `ANTHROPIC_BASE_URL` na `127.0.0.1`, stałym napisem zamiast
poświadczenia (`atrapa-nie-sekret`), `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` i własnym
`CLAUDE_CONFIG_DIR`. Atrapa zapisuje każde żądanie (nagłówki uwierzytelnienia zamaskowane)
i odpowiada według scenariusza (`{"narzedzie": …, "wejscie": …}` / `{"tekst": …}`), więc można
sprawdzić: uprawnienia i tryby, hooki, piaskownicę, MCP, skille, agentów, instrukcję, cache
i TTL — bez modelu i konta. Zawsze podawaj `--permission-mode` (bez flag funkcji `-p`
startuje w `auto`). Katalog próby nigdy nie jest usuwany — istniejący dostaje przyrostek.

## 8. Testy

```sh
tests/uruchom_testy.sh                                   # 17 testów bez CLI (3 próby CLI pominięte)
CLAUDE_BIN=/danaco/uslugi/claude/bin/claude tests/uruchom_testy.sh   # 20 testów, z próbami CLI
```

## 9. Struktura katalogów

```
.claude-plugin/plugin.json   manifest
agents/                      audytor-konfiguracji
commands/                    audyt-konfiguracji
skills/<skill>/              SKILL.md, references/, scripts/, examples/
scripts/                     narzędzia wspólne (+ schematy/, indeksy/)
wspolne/indeksy/             ustawienia.tsv, zmienne.tsv, flagi-cli.tsv, narzedzia.tsv, hooki-zdarzenia.tsv
wspolne/pokrycie-dokumentacji.md   281 stron dokumentacji → skille
tests/                       test_wtyczka.py, uruchom_testy.sh
```

## 10. Utrzymanie

Po nowym wydaniu Claude Code:

1. `python3 scripts/indeksy/odswiez_indeksy.py --pobierz` — raport nowych/usuniętych kluczy,
   zmiennych, flag, narzędzi i zdarzeń hooków; `--zapisz` aktualizuje indeksy (kolumny polskie
   zostają, nowe pozycje wymagają opisu).
2. `python3 skills/zmienne-srodowiskowe/scripts/buduj_indeks_md.py` — referencja zmiennych.
3. `CLAUDE_BIN=… tests/uruchom_testy.sh` i `python3 scripts/sprawdz_przyklady.py --cli …`.
4. Przejrzyj sekcje „Pułapki” i „Minimalne wersje” skilli dotkniętych zmianami; wpisz wydanie
   do CHANGELOG.md.

## 11. Znane ograniczenia

- Próby wykonano na atrapie API — zachowanie modelu (wybór narzędzi, wyzwalanie skilli,
  klasyfikator trybu auto, przełączanie modeli po klasyfikatorze) nie było sprawdzane.
- Polityki zarządzanej nie umieszczono w `/etc/claude-code` (system tylko do odczytu; straż
  pakietów blokuje zapis pliku o tej nazwie) — scalanie źródeł jest symulowane skryptem.
- Schemat schemastore jest zaległy wobec dokumentacji (brak części kluczy, zdarzeń hooków,
  trybu `mask`) — walidator obniża takie różnice do ostrzeżeń, rozstrzyga `claude doctor`.
- Wtyczki wbudowane CLI (`cc-plugin-sec-default`, `agents-md`, `plugin-authoring`) ładują się
  także przy `--setting-sources ""` — skrypty je pokazują, ale ich nie oceniają.

## 12. Licencja

Licencja zastrzeżona — [LICENSE](LICENSE).
