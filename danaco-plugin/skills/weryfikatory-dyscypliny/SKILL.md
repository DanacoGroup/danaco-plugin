---
name: weryfikatory-dyscypliny
description: >
  Uruchamianie i strojenie maszynowych bramek pluginu: `style_guard.py` (reguły
  `limit-dlugosci-komentarza`, `udzial-komentarzy`, `ton-nieformalny`, `wymyslony-kod`)
  i `nazwy_guard.py` (`etykieta-jako-zdanie`, `oznaczenie-literowo-numeryczne`,
  `nazwa-metaforyczna`) — wagi, kody wyjścia 0/2/3/4, progi i allowlisty w pliku
  `konfiguracja-dyscypliny.json` oraz wpięcie w pre-commit, CI i hook `PostToolUse`
  uruchamiany po zapisie pliku. Stosuj, gdy pada „walidator zgłasza”, „fałszywe trafienie”,
  „jak wyłączyć regułę”, „podnieś próg komentarzy”, „dodaj token do allowlisty”, „wepnij
  kontrolę w pre-commit”, „co znaczy kod wyjścia 3”. Ta paczka obejmuje wyłącznie walidatory
  i hook po zapisie; tryb ciągłej pracy prowadzi osobny plugin `danaco-praca`.
---

# Weryfikatory dyscypliny

## Kiedy stosować

Stosuj, gdy przedmiotem pracy jest sam walidator: trzeba uruchomić kontrolę dyscypliny,
zrozumieć zgłoszenie, ocenić fałszywe trafienie, dostroić próg, dopisać token do allowlisty
albo wpiąć kontrolę w pre-commit lub CI.

Tryb ciągłej pracy prowadzi osobny plugin `danaco-praca` — ta paczka go nie obejmuje.
Samych norm (co wolno w komentarzu, jaki ton, jaki zakres zmiany) nie ustala ta paczka,
lecz `dyscyplina-inzynierska`; nazw i etykiet — `standardy-nazewnictwa`.

## Co realnie istnieje w tej paczce

Dwa działające walidatory na bibliotece standardowej Pythona, bez instalacji zależności:

- `${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py` — objętość
  i ton komentarzy, wymyślone kody literowo-numeryczne w komentarzach.
- `${CLAUDE_PLUGIN_ROOT}/skills/standardy-nazewnictwa/scripts/nazwy_guard.py` — walidator
  nazewnictwa (identyfikatory, etykiety UI, metafory). Mieszka w paczce
  `standardy-nazewnictwa`; oba narzędzia uzupełniają się i uruchamiaj je razem (patrz
  „Masowe uruchomienie” niżej).

Obsługiwane rozszerzenia w `style_guard.py`: `.go`, `.ts`, `.tsx`, `.js`, `.rs`, `.py`.

Wszystkie polecenia podawaj z `${CLAUDE_PLUGIN_ROOT}`. Katalogiem roboczym modelu jest
repozytorium użytkownika, nie katalog paczki, więc forma `python3 scripts/style_guard.py`
kończy się błędem „No such file or directory”.

## Procedura

1. Uruchom kontrolę na zakresie, który Cię interesuje:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
     app/ client/src/
   echo $?   # 3 = są naruszenia blokujące -> nie przepuszczaj tury, commita ani builda
   ```
2. Odczytaj każde zgłoszenie razem z jego wagą (sekcja „Reguły i wagi”). Ostrzeżenie nie jest
   powodem do zmiany progu.
3. Przy zgłoszeniu blokującym popraw kod, nie próg.
4. Przy podejrzeniu fałszywego trafienia zastosuj procedurę z sekcji „Fałszywe trafienia”:
   najpierw ustal, czy kod lub nazwa jest realnie zgodna ze standardem, a dopiero potem
   sięgaj po allowlistę albo `--config`.
5. Uruchom ponownie i sprawdź kod wyjścia.

## Kryteria zakończenia

Praca w zakresie tej paczki jest skończona, gdy zachodzą wszystkie trzy warunki:

- wywołanie walidatora na zmienionym zakresie zwraca `0` albo `2` (same ostrzeżenia,
  świadomie przyjęte);
- każda zmiana progu w `--config` ma zapisane uzasadnienie w komunikacie commita;
- każdy nowy wpis w `allowlistaKodow` jest realnym standardem, protokołem lub algorytmem,
  a nie obejściem dla wymyślonej nazwy własnej.

## Sposób blokowania: doradczy hook plus jawna bramka

`PostToolUse` w tym pluginie (`${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json` +
`${CLAUDE_PLUGIN_ROOT}/hooks/po_zapisie.sh`) **nie blokuje zapisu** — uruchamia
`style_guard.py` i `nazwy_guard.py` na zmienionym pliku zaraz po Write/Edit i wypisuje
naruszenia do kontekstu tury kodem wyjścia 2. To jest celowe: przerywanie
w połowie edycji zostawiałoby pracę w stanie pośrednim, a `PostToolUse` i tak działa już po
fakcie zapisu.

Twardą bramkę stawiaj jawnie tam, gdzie ma sens — koniec tury, pre-commit albo krok CI —
wołając walidator wprost i sprawdzając jego kod wyjścia.

## Dwa tryby wywołania

```bash
# Kontrola ręczna albo CI - jeden lub wiele plików albo katalog:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
  app/ client/src/

# Wynik jako JSON, do dalszego przetwarzania w CI:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
  --json app/ > raport.json
```

Nie ma osobnego „trybu hooka” czytającego zdarzenie ze stdin wewnątrz `style_guard.py` —
parsowanie zdarzenia `PostToolUse` (JSON na stdin, pole `tool_input.file_path`) robi
`hooks/po_zapisie.sh`, który następnie woła `style_guard.py` z samą ścieżką pliku jak
w trybie ręcznym. Nie doklejaj więc flagi `--hook` przy wywołaniach ręcznych — jej nie ma.

## Reguły i wagi

`style_guard.py` — blokujące (kod wyjścia `3`, `blokujace=True`):

- `limit-dlugosci-komentarza` — pojedynczy komentarz (liniowy lub blokowy) dłuższy niż
  `limitKomentarza` znaków (domyślnie 350).
- `udzial-komentarzy` — komentarze zajmują więcej niż `progUdzialu` całego pliku liczonego
  **w znakach** (domyślnie 20%). Reguła jest wyłączona dla plików krótszych niż
  `minZnakowDoUdzialu` (domyślnie 600 znaków) — na krótkim pliku jeden zdawkowy komentarz
  dokumentujący przekracza każdy procentowy próg, bo mianownik jest za mały, żeby proporcja
  cokolwiek mówiła o realnej esejowości kodu. Jeśli reguła mimo to trafia fałszywie na
  typowych plikach repozytorium, podnieś oba progi w `--config`, nie tylko `progUdzialu`.

`style_guard.py` — ostrzeżenia (nie blokują, tylko raportowane):

- `ton-nieformalny` — wielokrotne `!`, `?`, `...` albo emoji w komentarzu.
- `wymyslony-kod` — wzorzec litery-myślnik lub podkreślnik-alfanumeryk (np. `MOD-A7`)
  **w treści komentarza**. `style_guard.py` sprawdza to wyłącznie w komentarzach; ten sam
  wzorzec w identyfikatorach kodu (nazwach zmiennych, typów, komponentów) łapie
  `nazwy_guard.py` regułą `oznaczenie-literowo-numeryczne`. Obie te reguły są
  ostrzeżeniami — uruchamiaj oba skrypty razem, bo jeden samodzielnie nie pokrywa całego
  standardu.

`nazwy_guard.py` — wszystkie trzy reguły nazewnicze są ostrzeżeniami:

- `etykieta-jako-zdanie` — etykieta w polu `label`, `title` albo `placeholder` licząca więcej
  niż sześć słów (`MAKSIMUM_SLOW_ETYKIETY`).
- `oznaczenie-literowo-numeryczne` — możliwe wymyślone oznaczenie komponentu
  w identyfikatorze kodu.
- `nazwa-metaforyczna` — człon identyfikatora ze słowem metaforycznym zamiast opisu funkcji.
  Reguła dotyczy nazw, nie prozy: metafora w komunikacie dla użytkownika albo w literale
  nie jest naruszeniem nazewnictwa.

Oba walidatory — blokujące niezależnie od zakresu kontroli:

- `kodowanie-pliku` — plik nie jest w UTF-8.
- `plik-nieczytelny` — pliku nie da się odczytać.

Cichy pomyłkowy przebieg jest gorszy od odmowy, dlatego nieczytelny plik jest naruszeniem
blokującym, a nie pominięciem.

## Konfiguracja

Progi, allowlisty i słownik metafor są w jednym pliku JSON, nie w kodzie skryptów. Oba
walidatory czytają go z `--config` albo znajdują sam plik `konfiguracja-dyscypliny.json`
w korzeniu sprawdzanego repozytorium. Wartości domyślne mieszkają w
`${CLAUDE_PLUGIN_ROOT}/scripts/konfiguracja_kontroli.py`.

```json
{
  "limitKomentarza": 350,
  "progUdzialu": 0.20,
  "minZnakowDoUdzialu": 600,
  "allowlistaKodow": ["MOD-A7"],
  "slowaMetaforyczne": ["silnik"],
  "allowlistaNazw": ["Tauri2"]
}
```

Trzy pierwsze pola to wartości domyślne. Zmieniaj `progUdzialu` wyłącznie świadomie, po
analizie z sekcji „Fałszywe trafienia” — nie kopiuj niższej liczby bez powodu, bo to zaostrza
próg, a nie łagodzi.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
  --config konfiguracja-dyscypliny.json src/
```

- `allowlistaKodow` — dokładne dopasowania zwalniane z reguły `wymyslony-kod`. Dopisuj tam
  wyłącznie realne standardy i protokoły, nigdy jako obejście dla wymyślonej nazwy własnej.
  Wzorce standardów (`UTF-`, `ISO-`, `RFC-`, `SHA-`, `TLS-`, `WCAG-` i pozostałe
  z `WYJATKI_STANDARDOW`) są zwolnione bez wpisu.
- `slowaMetaforyczne` — słownik reguły `nazwa-metaforyczna`, dodawany do wpisów domyślnych.
- `allowlistaNazw` — identyfikatory zwalniane z reguły `oznaczenie-literowo-numeryczne`;
  wersje standardów stosu Danaco (`Tauri2`, `OAuth2`, `SHA256`, `PostgreSQL16` i pozostałe
  z `DOMYSLNE_WYJATKI_OZNACZEN`) są zwolnione bez wpisu.

Błąd konfiguracji (brak pliku, zepsuty JSON, zła wartość) kończy walidator kodem `4`, nie
tracebackiem — kod `1` nie występuje w kontrakcie walidatorów, więc CI nie odróżniłby awarii
narzędzia od naruszenia.

## Fałszywe trafienia

Gdy reguła trafia niesłusznie, wykonaj kolejno:

1. Sprawdź, czy kod lub nazwa naprawdę jest zgodna ze standardem (nazwa algorytmu, standardu,
   protokołu).
2. Jeśli tak — dodaj dokładny token do `allowlistaKodow` w pliku konfiguracyjnym, z
   uzasadnieniem w komunikacie commita.
3. Nie podnoś globalnie `limitKomentarza` ani `progUdzialu`, żeby uciszyć jeden przypadek.
   `progUdzialu` podnieś raz, świadomie, dopiero jeśli analiza wykaże, że domyślne 20% jest
   nierealne dla typowego rozmiaru plików w tym repozytorium.

## Podłączenie pod pre-commit i CI

```bash
# pre-commit - kontrola plików w indeksie:
git diff --cached --name-only -- '*.go' '*.ts' '*.tsx' '*.rs' '*.py' \
  | xargs -r python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py"

# CI - kontrola całego drzewa lub zakresu, oba walidatory naraz:
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify app/
```

Kody wyjścia obu walidatorów: `0` czysty przebieg, `2` same ostrzeżenia (przepuść, ale pokaż
w logu), `3` co najmniej jedno naruszenie blokujące (zatrzymuje commit lub build), `4` błąd
konfiguracji narzędzia. W repozytorium docelowym
te same bramki uruchamia cel `task standard` ze wspólnego pliku
`${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml`.

## Masowe uruchomienie razem z pozostałymi walidatorami

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <katalog>
```

Uruchamia `style_guard.py`, `nazwy_guard.py` (paczka `standardy-nazewnictwa`) i audyt porządku
repozytorium (paczka `kontrola-jakosci`) w jednym przebiegu i zwraca jeden zbiorczy kod
wyjścia — maksimum z kodów poszczególnych walidatorów.

## Testy

Hook po zapisie i konfiguracja hooków mają testy na bibliotece standardowej:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/tests/uruchom_testy.sh"
python3 "${CLAUDE_PLUGIN_ROOT}/tests/test_po_zapisie.py"
```

Dla `style_guard.py` i `nazwy_guard.py` plugin nie zawiera zestawu automatycznego. Jeśli
dostrajasz progi albo wzorce wyrażeń regularnych, sprawdź zmianę na małym przykładzie przed
wpięciem jej do CI:

```bash
mkdir -p /tmp/test-sg && cat > /tmp/test-sg/przyklad.go <<'EOF'
package main

func main() {}
EOF
python3 "${CLAUDE_PLUGIN_ROOT}/skills/weryfikatory-dyscypliny/scripts/style_guard.py" \
  /tmp/test-sg
```

## Zakres hooka PostToolUse

`PostToolUse` z matcherem `^(Write|Edit|MultiEdit|NotebookEdit)$` to jedyne zdarzenie
rejestrowane przez ten plugin (`${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json` →
`${CLAUDE_PLUGIN_ROOT}/hooks/po_zapisie.sh`). Obsługuje wyłącznie walidatory dyscypliny
i nazewnictwa. Nie ma w nim żadnego kanału wejścia użytkownika: wiadomości docierają do
modelu wprost z czatu, na granicy najbliższego wywołania narzędzia.

## Rozgraniczenie z paczkami sąsiednimi

- tryb ciągłej pracy prowadzi osobny plugin `danaco-praca`; ten plugin działa niezależnie
  od niego.
- `dyscyplina-inzynierska` — norma, czyli co wolno w komentarzu, jaki ton, jaki zakres zmiany.
- `standardy-nazewnictwa` — norma nazewnicza oraz miejsce, w którym leży `nazwy_guard.py`.
- `kontrola-jakosci` — ocena kodu przez człowieka lub model, kończona raportem ustaleń.
