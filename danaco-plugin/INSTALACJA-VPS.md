# Instalacja pluginu na serwerze zdalnym

Najważniejsze: **plugin instaluje się osobno na każdej maszynie.** Instalacja w aplikacji
Claude na komputerze lokalnym nie przenosi się automatycznie na serwer. Przy połączeniu
z serwerem — także przez integrację SSH w aplikacji Claude — Claude Code działa na
serwerze i czyta konfigurację z katalogu `~/.claude` **użytkownika SSH na tym serwerze**;
plugin musi tam trafić.

Wymagania, opis hooka kontroli po zapisie i wykaz paczek: [README.md](README.md).

## Wymagania na serwerze

| Wymaganie | Sprawdzenie | Skutek braku |
|---|---|---|
| Claude Code | `claude --version` | plugin nie ma czego załadować |
| `python3` w wersji 3.10 lub nowszej | `python3 --version` | kontrola dyscypliny po zapisie nie działa; walidatory nie uruchomią się także ręcznie |
| POSIX `sh` | `command -v sh` | hook nie uruchamia się wcale |

Interpreter Pythona wrapper szuka kolejno jako `python3`, `python` i `py -3`. Plugin
nie ma zależności zewnętrznych Pythona; `bash` nie jest wymagany.

## Metoda pierwsza — instalacja trwała przez lokalny marketplace (zalecana)

Katalog pluginu zawiera `.claude-plugin/marketplace.json`, więc jest jednocześnie własnym
marketplace.

1. Skopiuj rozpakowany katalog pluginu na serwer:
   ```bash
   scp -r <katalog-pluginu> UZYTKOWNIK@SERWER:~/
   ```
   albo prześlij archiwum i rozpakuj je na serwerze:
   ```bash
   scp <katalog-pluginu>.zip UZYTKOWNIK@SERWER:~/
   ssh UZYTKOWNIK@SERWER "unzip -o ~/<katalog-pluginu>.zip -d ~/<katalog-pluginu>"
   ```

2. Prawa wykonania nie są konieczne — `hooks/hooks.json` wywołuje wrapper przez
   `sh <plik>`, co nie wymaga bitu wykonywalności ginącego przy rozpakowaniu archiwum.
   Jeśli mimo to wolisz je nadać:
   ```bash
   ssh UZYTKOWNIK@SERWER
   chmod +x ~/<katalog-pluginu>/hooks/*.sh ~/<katalog-pluginu>/tests/*.sh
   ```

3. Zarejestruj marketplace i zainstaluj plugin na serwerze:
   ```bash
   claude plugin marketplace add ~/<katalog-pluginu>
   claude plugin install danaco-plugin@danaco --scope user
   ```

4. Sprawdź instalację:
   ```bash
   claude plugin list
   ```
   Plugin powinien być na liście jako włączony. W sesji `claude` paczki są dostępne pod
   nazwą pluginu i nazwą paczki, na przykład `danaco-plugin:kodowanie`.

5. Po każdej aktualizacji plików pluginu na serwerze odśwież marketplace:
   ```bash
   claude plugin marketplace update danaco
   ```
   i zrestartuj sesję (albo użyj `/reload-plugins`, jeśli wersja klienta to obsługuje).

## Metoda druga — test bez instalacji, na czas jednej sesji

```bash
claude --plugin-dir ~/<katalog-pluginu>
```

Ładuje plugin razem z hookiem tylko na czas tej sesji. Dobre do sprawdzenia, czy kontrola
po zapisie działa na tym serwerze, zanim instalacja stanie się trwała.

## Weryfikacja hooka na serwerze

1. Uruchom testy paczki — sprawdzają prawdziwy wrapper `sh` z JSON-em zdarzenia na
   standardowym wejściu:
   ```bash
   sh ~/<katalog-pluginu>/tests/uruchom_testy.sh
   ```
   Oczekiwany wynik: `OK`.

2. W sesji z załadowanym pluginem zapisz plik `.py` z komentarzem dłuższym niż 350 znaków.
   Przy działającym hooku `PostToolUse` model dostaje w tej samej turze raport
   z regułą `limit-dlugosci-komentarza`. Brak raportu oznacza, że klient nie wykonuje
   hooków pluginu.

## Uwagi

- Zakresy instalacji: `--scope user` obejmuje `~/.claude` użytkownika, czyli wszystkie
  jego projekty na serwerze; `--scope project` obejmuje `.claude/` w katalogu projektu.
- Tryb ciągłej pracy prowadzi osobny plugin `danaco-praca`; instaluje się go tą samą
  metodą i niezależnie od tego pluginu.
- Środowiska, które nie wykonują hooków pluginu — w tym część interfejsów okiennych
  i Cowork — nie uruchamiają kontroli po zapisie. Pozostaje wtedy treść normatywna paczek
  i ręczne wywołanie walidatorów z wiersza poleceń.
