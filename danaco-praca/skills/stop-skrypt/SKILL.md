---
name: stop-skrypt
description: >
  Blokada pracy maszynowej: po poleceniu `/stop-skrypt` model zmienia treść wyłącznie
  pojedynczo i pod kontrolą — odrzucane są podmiany w miejscu (`sed -i`, `perl -i`,
  `rename`), `find -exec` i `xargs` zmieniające pliki, pętle powłoki z zapisem, kod
  i skrypty przepisujące treść w pętli, zapis hurtowy do bazy danych oraz zamiana
  wszystkich wystąpień w pliku naraz. Blokada trwa do polecenia `/skrypt`, które
  zdejmuje ją natychmiast. Stosuj, gdy użytkownik wywoła `/stop-skrypt`, `/skrypt`
  albo postać z prefiksem `/danaco-praca:stop-skrypt`. Model nie włącza ani nie
  zdejmuje jej sam.
---

# Blokada pracy maszynowej

## Blokada jest już założona

Plik blokady zakłada hook `UserPromptSubmit` w chwili, gdy użytkownik wpisuje
`/stop-skrypt` — zanim ta paczka do Ciebie trafi. Niczego nie uruchamiasz i niczego nie
konfigurujesz. Zdejmuje ją wyłącznie polecenie użytkownika `/skrypt`, wpisane na
początku wiadomości albo w osobnej linii; wzmianka w prozie („opisz komendę
/skrypt") niczego nie zmienia. Blokada nie ma terminu ważności, wiąże rozmowę, w
której ją włączono, i jest niezależna od trybu ciągłej pracy oraz od blokady
podagentów — `/stop` jej nie zdejmuje.

## Skąd ta reguła

Bazy i zbiory dokumentów nie giną od jednej pomyłki w jednym rekordzie, tylko od jednej
pętli, która tę pomyłkę powiela po całym zbiorze. Pojedyncza zmiana jest widoczna
w przeglądzie i odwracalna; ta sama zmiana puszczona maszynowo po tysiącu pozycji nie
jest ani jednym, ani drugim. Ta blokada odbiera narzędzie, nie zadanie: pracę masz
wykonać, tylko ręcznie.

## Co jest odrzucane

Hook `PreToolUse` rozstrzyga po kształcie polecenia i po treści uruchamianego pliku —
tak samo na pierwszym planie i w tle, bo przeniesienie hurtowej podmiany w tło nie czyni
jej mniej hurtową:

- podmiana treści w miejscu: `sed -i`, `sed --in-place`, `perl -pi`, `awk -i inplace`,
  `rename`, `rpl`, `sponge`, `sd`, `dos2unix`, `recode`, `iconv -o`, `yq -i`;
- hurtowe nadpisanie plików: `patch`, `git apply`, `git checkout -- …`, `git restore`,
  `git stash pop`, `git reset --hard`, `git filter-branch`, `rsync`;
- edytor wsadowy wykonujący skrypt edycji: `ed`, `ex -sc`, `vim -es`;
- `find` z kasowaniem (`-delete`) oraz `find -exec` uruchamiający polecenie zmieniające
  pliki;
- `xargs` i `parallel` z poleceniem zmieniającym pliki (`mv`, `cp`, `rm`, `tee`,
  przekierowanie);
- pętle powłoki z zapisem: `for … do … done`, `while … do … done` z przekierowaniem albo
  z `mv`, `cp`, `rm`, `tee`;
- kod podany wprost w wywołaniu (`python -c`, `node -e`, heredoc do interpretera) oraz
  treść podana do wykonania w potoku: `echo "UPDATE …" | sqlite3`, `cat skrypt |
  python3`, `python3 -c "$(cat skrypt)"`;
- **plik uruchamiany jako program** — niezależnie od rozszerzenia — którego treść
  zawiera pętlę z zapisem, podmianę w miejscu albo zapis do bazy; hook czyta go przed
  uruchomieniem;
- zapis hurtowy do bazy danych: `UPDATE`, `DELETE FROM`, `INSERT INTO`, `DROP`,
  `TRUNCATE`, `ALTER TABLE`, `.import`, `COPY … FROM` przez `sqlite3`, `psql`, `mysql`,
  `mongosh` i pokrewne, a także wczytanie pliku `.sql`, którego treść zmienia bazę;
- zamiana wszystkich wystąpień w pliku naraz (`replace_all`) i wywołanie narzędzia
  plikowego z ponad dwudziestoma zmianami;
- zlecenie hurtowej podmiany podagentowi (rozstrzyga treść zlecenia) oraz narzędziu MCP
  z polem `command`, `script` albo `cmd`.

## Co przechodzi bez przeszkód

Odczyt i analiza: `cat`, `grep`, `sed -n`, `git diff`, `SELECT`, `.schema`, `EXPLAIN`.
**Czytanie pliku skryptu** też — `cat napraw.py`, `grep -n def napraw.py`, `wc -l
napraw.py`: blokada dotyczy uruchomienia, nie czytania. Szukanie zakazanej frazy
w dokumentacji (`grep -rn 'sed -i' docs/`, `git log --grep='sed -i'`). Wczytanie pliku
`.sql`, który wyłącznie czyta (`psql -f raport.sql`). Pętla bez zapisu (`for f in
src/*.py; do python3 -m py_compile $f; done`). Budowa, testy i narzędzia projektu
(`npm test`, `make`, `go build`). Pojedyncza, świadoma zmiana: `Edit` bez `replace_all`,
`Write` jednego pliku, dopisanie linii do notatki. Blokada dotyczy hurtu, nie pracy.

## Jak wtedy pracujesz

Zmieniasz pozycja po pozycji: czytasz treść przed zmianą, wprowadzasz zmianę, sprawdzasz
wynik. Zakres, który wygląda na zbyt duży na ręczną robotę, dzielisz na części i robisz
tyle, ile się da, a resztę odnotowujesz — z podaniem, gdzie skończyłeś. Nie szukasz
obejścia: inna powłoka, skrypt pomocniczy, podagent ani narzędzie MCP nie są tu drogą
naokoło, bo blokada dotyczy operacji, nie nazwy narzędzia. Nie proponujesz zdjęcia
blokady i nie pytasz, czy można ją zdjąć.

Gdy odrzucenie jest ewidentnie fałszywym trafieniem (na przykład notatka cytująca
`sed -i`), przeformułuj polecenie tak, żeby nie wyglądało na hurtową podmianę, i pracuj
dalej — bez komentowania blokady na czacie.
