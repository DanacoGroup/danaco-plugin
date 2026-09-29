# Historia zmian

Zapis prowadzony w układzie Keep a Changelog. Wersje zgodne z wersjonowaniem
semantycznym. Wpisy do wersji 2.3.2 włącznie obejmują także tryb ciągłej pracy, który
od wersji 3.0.0 prowadzi osobny plugin `danaco-praca`; podawana w nich wersja klienta
Claude Code dotyczy weryfikacji tamtego mechanizmu.

## 3.3.0 (29.09.2026)
- Serwer MCP danaco-programy: katalog wymiany na nexusie liczony od konta, jako które loguje się SSH (`id -un` na nexusie) - usługi na kontach systemowych mogą korzystać z `uruchom`.

## 3.2.0 (29.09.2026)
- Serwer MCP danaco-programy: skille wiązane z programami przez pole „skill” rejestru (nowy katalog: 15 działów, 1157 wpisów); skill powiązany z programem nie dubluje się w wynikach.

## 3.1.1 (29.09.2026)
- Serwer MCP danaco-programy: gdy w trybie zdalnym nie uda się pobrać katalogu z nexusa, wynik zawiera ostrzeżenie z przyczyną zamiast pustej listy.

## [3.1.0] — 2026-09-29

Wydanie dokłada serwer MCP katalogu programów Danaco. Pierwsze wydanie prowadzone
w repozytorium `DanacoGroup/danaco-plugin`, jednym źródle wtyczek dla wszystkich
serwerów i kont. Sprawdzane na kliencie Claude Code 2.1.284.

### Dodane

- Serwer MCP `danaco-programy` (`mcp/danaco-programy.py`, wersja serwera 1.1.0)
  zarejestrowany w `.mcp.json` pluginu i uruchamiany interpreterem `/usr/bin/python3`.
  Narzędzia: `szukaj`, `opis`, `dzialy`, `lista`, `uruchom`. Tryb wybierany po nazwie
  hosta albo zmienną `DANACO_PROGRAMY_TRYB`:
  - `lokalny` na danaco-nexus — katalog `/danaco/programy/katalog` z dysku, `uruchom`
    liczy na miejscu;
  - `zdalny` na pozostałych serwerach — kopia katalogu z nexusa przez `rsync` (najwyżej
    raz na 10 minut), `uruchom` wysyła pliki na nexusa, liczy tam jako to samo konto
    i ściąga wyniki. Wymaga `ssh`, `rsync` i wpisu `Host danaco-nexus`
    w `~/.ssh/config` konta.
- README: rozdział 6 „Serwer MCP katalogu programów”, wymagania serwera i wpis
  w znanych ograniczeniach; kolejne rozdziały przesunięte o jeden numer.

### Znane braki

- Katalog `hooks/` (`hooks.json`, `po_zapisie.sh`, `hooks/README.md`) nie przetrwał
  pakowania wersji 3.0.0 i nie ma go w repozytorium. Hook kontroli po zapisie opisany
  w rozdziale 5 README nie jest więc rejestrowany, a `tests/test_po_zapisie.py` nie
  przechodzi. Walidatory działają z wiersza poleceń.

## [3.0.0] — 2026-09-05

Wydanie dzieli dotychczasowy plugin na dwa niezależne. `danaco-plugin` zostaje warstwą
wiedzy i umiejętności oraz maszynowych walidatorów; tryb ciągłej pracy wychodzi w całości
do nowego pluginu `danaco-praca` (wspólna historia do 2.3.2).

### Usunięte

- Paczki `pracuj`, `stop` i `blokada` wraz z komendami `/pracuj`, `/stop`, `/blokada`
  i `/blokada-stop`.
- Skrypty `scripts/straznik.py`, `scripts/znacznik.py` i `scripts/zadanie.py` — logika
  strażnika, znacznika zadania w toku i blokady podagentów.
- Wrappery `hooks/straznik.sh` i `hooks/straznik.ps1`.
- Zestaw `tests/test_straznik.py`; klasa pokrywająca hook po zapisie została z niego
  wydzielona (patrz „Dodane”).
- Zdarzenia `UserPromptSubmit`, `PreToolUse`, `Stop`, `SessionStart` i `PreCompact` oraz
  wpis `PostToolUse` z matcherem `^(Bash|PowerShell)$` w `hooks/hooks.json`.

### Dodane

- `tests/test_po_zapisie.py` — przypadki hooka `PostToolUse` po zapisie oraz kontrakt
  `hooks/hooks.json` wobec plików pluginu, wydzielone z `tests/test_straznik.py`.
- Rozdział README o podziale na dwa pluginy: oba są niezależne, a przy obu
  zainstalowanych ich hooki `PostToolUse` sumują się na rozłącznych matcherach.

### Zmienione

- `hooks/hooks.json` rejestruje wyłącznie `PostToolUse` z matcherem
  `^(Write|Edit|MultiEdit|NotebookEdit)$` wołający `hooks/po_zapisie.sh`.
- `skills/weryfikatory-dyscypliny/SKILL.md` opisuje wyłącznie walidatory i hook po
  zapisie; opis techniczny hooków trybu ciągłej pracy usunięty, pole `description`
  poprawione.
- Odesłania do paczek `pracuj`, `stop` i `blokada` w pozostałych paczkach (m.in.
  `orkiestracja-agentow`) zastąpione formułą „paczka `pracuj` pluginu `danaco-praca`,
  jeśli jest zainstalowany”.
- README, `hooks/README.md` i `INSTALACJA-VPS.md` przepisane pod jedną warstwę: 15 paczek,
  jedno zdarzenie hooka, trzy skrypty wspólne, zaktualizowany wykaz testów.
- `.claude-plugin/plugin.json` i `.claude-plugin/marketplace.json`: wersja `3.0.0`, opis
  bez wzmianki o trybie ciągłej pracy.

### Zgodność

- Instalacja obu pluginów naraz nie powoduje kolizji hooków. Kto potrzebuje trybu
  ciągłej pracy, instaluje `danaco-praca` osobno.

## [2.3.2] — 2026-09-05

### Zmienione

- Podagenci (`Task`, `Agent`, `Workflow`) przechodzą wyłącznie uruchomieni w tle;
  wariant synchroniczny jest odrzucany. Dotąd dawał tylko wskazówkę, przez co model
  nadal znikał za „running tools" na czas pracy podagenta, a użytkownik nie miał jak się
  odezwać. Blokada dotyczy czekania, nie samej pracy wieloagentowej: wariant tłowy
  działa bez zmian, procesy nie są przerywane ani zabijane.

## [2.3.1] — 2026-09-04

Wydanie domyka ustalenia dwóch audytów kontrolnych wersji 2.3.0: zamyka pozostałe drogi
samozwolnienia, przywraca płynność codziennej pracy i porządkuje wydanie.

### Naprawione

- **Dwuetapowe samozwolnienie zamknięte.** Katalog kopii `~/.danaco-kopie`, pliki kopii i
  nagrobki są chronione tak samo jak `.danaco` (również w zapisie `$HOME/…` i `~/…`), a
  `rm`, `mv` i `rmtree` z celem pochodzącym z podstawienia polecenia `$( )` albo z
  backticków są odrzucane — nazwy takiego celu nie da się sprawdzić przed wykonaniem.
- **`/blokada` bez aktywnego zlecenia nie jest kasowalna.** Kontrola poleceń i zapisów
  działa również wtedy, gdy aktywna jest sama blokada podagentów; plik
  `blokada-subagentow.json` jest chroniony jak znacznik. `zadanie.py start` przechodzi.
- **Parytet `hooks/straznik.ps1` z `hooks/straznik.sh`.** Wzorzec komendy tylko na
  początku wiadomości albo linii (cytat już nie zdejmuje blokady), sprawdzenie
  właściciela sesji i tokenu, sprawdzenie terminu ważności, odczyt pola `prompt` z
  sekwencjami ucieczki, `Remove-Item -Recurse` przy zdejmowaniu znacznika oraz wypis
  `stan-zlecenia.md` w trybie `sesja`. Parytetu pilnuje test statyczny.
- **Ucieczka ścieżką względną.** Cele zapisu bez prefiksu `cd <ścieżka bezwzględna> &&`
  liczone są od katalogu roboczego zdarzenia hooka, więc `echo x > ../poza.txt` jest
  odrzucane jak każde inne wyjście poza katalog zlecenia.
- **Bezterminowy znacznik poza deklaracją modelu.** `--limit-godzin 0` wymaga teraz
  dowodu spoza sesji (brak `CLAUDE_PLUGIN_ROOT` i `CLAUDE_PROJECT_DIR` albo interaktywny
  terminal); flaga `--poza-sesja` jest wyłącznie dodatkowym potwierdzeniem.
- **Token nie przejmuje cudzego zlecenia.** Własność raz ustalona nie jest przepisywana
  na inną sesję na podstawie samego tokenu w transkrypcji (użytkownik mógł go tam
  wkleić); przejęcie jest możliwe dopiero, gdy dotychczasowy właściciel przez pół godziny
  nie wywołał żadnego hooka.

### Zmienione

- **Próg pierwszego planu podniesiony do 300 s.** `go build`, `npm run build`, `npm test`,
  `pytest -q`, `make`, `mvn`, `gradle`, `docker build` i `pip install` przechodzą bez
  deklarowania limitu czasu. Blokowane pozostają polecenia z natury nieskończone
  (serwery, `tail -f`, `watch`), `sleep` powyżej progu oraz limit zadeklarowany powyżej
  progu.
- **Mniej fałszywych trafień w polskim repozytorium.** Gołe `import znacznik` i
  `from zadanie …` nie są już obejściem (liczy się nazwa funkcji mechanizmu), zniknął
  relikt `.klucz`, a nazwy plików zlecenia (`zadanie-w-toku`, `stan-zlecenia`,
  `blokada-subagentow`) liczą się wyłącznie jako CEL operacji destrukcyjnej — `rg
  zadanie-w-toku` i `echo … >> lista.txt` przechodzą. `git clean -n` i `--dry-run`
  przechodzą; rozpoznawane są też `/stop.` i `/stop!`.
- **Kontrola treści zapisu tylko dla plików skryptowych i konfiguracyjnych** (`.sh`,
  `.ps1`, `.py`, `.bat`, `.cmd`, `.json`, `.yaml`, `.yml`, `.toml`). README, runbook i
  CHANGELOG mogą opisywać polecenia.
- **Porządek w `~/.danaco-kopie`.** Każdy `start` kasuje kopie i nagrobki starsze niż
  siedem dni, a nieudany zapis kopii jest sygnalizowany na stdout.

### Wydajność

- **Hooki nie uruchamiają Pythona bez potrzeby.** Obecność znacznika (albo pliku blokady)
  sprawdza powłoka we wszystkich trybach `hooks/straznik.sh`; tryb `kontrola` woła
  interpreter dopiero wtedy, gdy znacznik zniknął, a katalog kopii istnieje. Koszt hooka
  bez aktywnego zlecenia spadł z ok. 54 ms do ok. 8 ms. `hooks/po_zapisie.sh` filtruje
  rozszerzenie w powłoce i uruchamia oba walidatory w jednym procesie.

### Porządki

- Usunięty martwy kod (`KOMUNIKAT_PODAGENT`, `_NAZWY_ZLECENIA_DO_GLOBU`,
  `POLECENIE_ZAKONCZENIA` w `hooks/straznik.sh`, rusztowanie `--fraza` w testach) oraz
  katalogi `.pytest_cache/` i `__pycache__/` z drzewa repozytorium.
- `plugin.json` i `marketplace.json` mówią o osiemnastu paczkach skilli (tyle ich jest);
  README podaje bieżącą wersję i liczbę przypadków testowych.
- `scripts/znacznik.py` i `scripts/straznik.py` przechodzą własny walidator dyscypliny
  (udział komentarzy poniżej progu 20%).
- Testy: 264 przypadki, izolacja katalogu domowego obejmuje wszystkie klasy testowe.

## [2.3.0] — 2026-09-04

Wydanie domyka ustalenia dwóch audytów kontrolnych mechanizmu trybu ciągłej pracy:
zamyka drogi obejścia blokady dostępne modelowi i zdejmuje ograniczenia, które dławiły
normalną pracę.

### Zmienione

- **Termin ważności poza zasięgiem modelu.** `--limit-godzin` przyjmuje wartości od 1 do
  24; `0` (bezterminowo) wyłącznie poza sesją modelu, z flagą `--poza-sesja`. Hook
  `PreToolUse` odrzuca też `zadanie.py start` przy już aktywnym znaczniku.
- **Rozpoznanie komend zawężone do początku wiadomości albo osobnej linii.** `/stop`,
  `/blokada` i `/blokada-stop` w cytacie, w ścieżce (`/stop-handler.md`, `/stop/x`),
  we wklejonym logu i w prozie nie wyzwalają niczego — także przy skanowaniu
  transkrypcji w hooku `Stop`.
- **Wiązanie znacznika z sesją tokenem**, nie zmienną `CLAUDE_SESSION_ID` (klienci jej
  nie eksportują). `start` losuje token i wypisuje go na standardowe wyjście; obecność
  tokenu w transkrypcji rozstrzyga własność, utrzymuje blokadę u właściciela mimo
  rozjazdu identyfikatora sesji i jest wymagana do zdjęcia znacznika, gdy zdarzenie nie
  ma identyfikatora sesji.
- **Granica `.git` znowu honorowana** przy szukaniu znacznika; znacznik z katalogu
  nadrzędnego obowiązuje, gdy katalog bieżący leży w jego `katalogProjektu`. `mkdir .git`
  niczego nie wyłącza, a sąsiednie repozytorium pozostaje wolne.
- **Zakres zlecenia w poleceniach powłoki** obejmuje teraz ostatni argument `cp`, `mv`,
  `install` i `rsync`, argument `tee`, `-o`/`--output`, `>|` oraz ścieżki względne po
  prefiksie `cd <katalog> &&`. Allowlista: `/tmp`, `/dev/*`, katalog cache.
- **Praca na pierwszym planie odblokowana dla poleceń skończonych.** `pytest`, `npm test`,
  `make` i `go test` przechodzą, gdy wywołanie deklaruje limit czasu do 60 sekund (pole
  `timeout` albo prefiks `timeout N`). Tło pozostaje wymagane dla poleceń z natury
  nieskończonych (serwery, `tail -f`, `watch`) i dla dłuższych limitów.
- **Zawężone heurystyki fałszywie trafiające.** Gołe `hooks`, `scripts` i `.claude-plugin`
  liczą się wyłącznie w katalogu pluginu (`mv hooks/old.js src/` w obcym repozytorium
  przechodzi), a nazwy funkcji mechanizmu — wyłącznie w kontekście wykonania Pythona
  (`python -c`, `-m`, heredoc), nie w `grep`, `git commit -m` ani `git log`.
- **Blokada podagentów zdejmowana wyłącznie przez sesję, która ją założyła.**
- **Termin ważności sprawdzany we wszystkich trybach strażnika**, także w
  `UserPromptSubmit` i `PreCompact`.

### Dodane

- **Kopia znacznika poza katalogiem projektu** (`~/.danaco-kopie/<skrót-ścieżki>.json`,
  uprawnienia 600) i nowy hook `PostToolUse` dla `Bash`/`PowerShell` (tryb `kontrola`):
  znacznik skasowany poleceniem powłoki wraca przy następnym wywołaniu, z komunikatem, że
  usunięcie znacznika nie kończy zlecenia. Legalne zdjęcie kasuje kopię i zostawia
  nagrobek, więc znacznik nie zmartwychwstaje.
- **Doszczelnione wzorce obejść**: wzorce wieloznaczne obejmujące katalog zlecenia
  (`.dana*`, `.d*o`), `find … -delete`/`-exec rm` z filtrem nazwy pasującym do plików
  zlecenia (także `-name "*.json"`), składanie nazwy ze zmiennych powłoki, heredoc
  uruchamiający Pythona oraz `base64 -d | sh`.
- **Ścieżka awaryjna bez Pythona doprowadzona do parytetu** w granicach POSIX `sh`:
  rozpoznanie komendy na początku wiadomości (z obsługą cudzysłowu po ukośniku
  odwrotnym), sprawdzenie właściciela sesji i tokenu oraz terminu ważności.
- **Wrapper PowerShell podłączony warunkowo**: `hooks/straznik.sh` przekazuje mu
  zdarzenie, gdy nie znajdzie Pythona, a `pwsh`/`powershell` jest dostępne. `.ps1`
  obsługuje tryby `kompakt` i `kontrola`.

## [2.2.0] — 2026-09-04

Wydanie przestawia tryb ciągłej pracy na zasady ustalone z operatorem: jawne wyzwalanie,
jedno polecenie kończące, brak wpływu na procesy i narzędzia, stała dostępność modelu.

### Zmienione

- **Wyzwalanie wyłącznie komendą** `/danaco-plugin:pracuj` (lub `/pracuj`). Opis paczki
  nie łapie już ogólnych sformułowań („dokończ całość”, „nie przerywaj”, „nie pytaj mnie
  o nic”), przez które tryb włączał się sam przy zwykłych poleceniach.
- **Kończenie wyłącznie poleceniem `/stop`** (`/danaco-plugin:stop`). Zniesiono frazę
  potwierdzenia, jej podpis HMAC i plik klucza: komenda jest widoczna w interfejsie, nie
  pada przypadkiem w rozmowie, a modelowi jest tak samo niedostępna, bo zdarzenie
  `UserPromptSubmit` powstaje wyłącznie z wpisu człowieka. Nowa paczka `stop`.
- **Znacznik należy do sesji, która go założyła** (`sesjaId` zapisywany przy pierwszym
  zdarzeniu hooka). Inna rozmowa otwarta w tym samym katalogu nie jest blokowana i nie
  przejmuje cudzego zlecenia.
- **Termin ważności znacznika: 24 h** (`--limit-godzin N`, `0` = bezterminowo). Zapomniany
  znacznik nie blokuje już pracy w nieskończoność.
- **Zakres zlecenia to katalog jego znacznika** — zapisy poza nim są odrzucane, żeby praca
  nie rozlewała się na sąsiednie repozytoria i inne produkty.
- **Nic nie jest zabijane, skracane ani odbierane**: procesy w tle, narzędzia i
  orkiestracja agentowa (`Task`, `Agent`, `Workflow`) działają normalnie. Odrzucane jest
  wyłącznie CZEKANIE na wynik na pierwszym planie — w trakcie takiego wywołania nie odpala
  się żaden hook i wiadomość użytkownika nie ma jak dojść. Wywołania oznaczone jako praca
  w tle przechodzą bez zmian.
- **Zniesiono skrzynkę poleceń i okno oddechu.** Obie protezy powstały przy założeniu, że
  wpisy użytkownika docierają dopiero na końcu tury. W rzeczywistości klient dostarcza je
  na granicy najbliższego wywołania narzędzia, więc przy zakazie czekania na pierwszym
  planie wiadomość z czatu dochodzi od razu i nie potrzeba pliku pośredniego.
- **Kompresja kontekstu przechodzi bez przeszkód i tryb ją przeżywa.** Nowy hook
  `PreCompact` niczego nie blokuje (także w awaryjnej ścieżce bez Pythona): zapisuje stan
  zlecenia do `.danaco/stan-zlecenia.md` i przypomina, że tryb obowiązuje dalej, a
  `SessionStart` podaje ten stan po kompresji i przy wznowieniu sesji. Bez tego kompresja
  albo się nie odbywała, albo model po niej nie wiedział, nad czym pracuje.
- **Cisza na czacie w trakcie zlecenia.** Komunikat hooka `Stop` i SKILL.md wymagają, by
  model nie pisał relacji z postępów: bez zapowiedzi, streszczeń kroków i podsumowań
  etapów. Raport — krótki, w punktach — powstaje dopiero po `/stop`. Powód: użytkownik i
  tak tej relacji nie czyta, a każdy akapit zużywa kontekst potrzebny na pracę.
- `skills/pracuj/SKILL.md` skrócone do reguł trybu: paczka nie narzuca już metody pracy
  ani prowadzenia dziennika — zlecenie użytkownika jest jedynym zakresem obowiązków.

### Dodane

- **Blokada podagentów `/blokada`** (paczka `blokada`): po tym poleceniu model pracuje
  wyłącznie samodzielnie — `Task`, `Agent` i `Workflow` są odrzucane, również uruchamiane
  w tle. Blokada trwa najwyżej 12 godzin albo do polecenia `/blokada-stop`, wiąże się
  z sesją, w której ją włączono, i jest niezależna od trybu ciągłej pracy (`/stop` jej nie
  zdejmuje). Stan trzyma plik `.danaco/blokada-subagentow.json` zapisywany przez hook
  `UserPromptSubmit`, więc model nie może jej ani włączyć, ani zdjąć.

### Zweryfikowane

- `tests/` — 195 testów, wszystkie przechodzą.

## [2.1.0] — 2026-09-03

Wydanie usuwa dziurę w projekcie trybu ciągłej pracy: użytkownik nie miał jak odezwać się
do modelu, dopóki tryb był aktywny.

### Przyczyna

Claude Code dostarcza modelowi wpisy użytkownika w momencie zakończenia tury. Hook `Stop`
odrzuca każde zakończenie tury, a własny limit klienta — osiem kolejnych blokad — zeruje
się przy każdym użyciu narzędzia, więc model realnie pracujący nigdy go nie dobija. Tura
nie kończyła się nigdy, a wpisy użytkownika stały w kolejce nieodczytane. Wady nie było
widać w wersji 1.1.0, bo blokada tam często w ogóle nie działała: znacznik był zakładany
w katalogu roboczym, a szukany od korzenia projektu (ustalenie A2-01), więc z podkatalogu
strażnik nie znajdował nic i przepuszczał zakończenie tury. Naprawa blokady w 2.0.0
odsłoniła dziurę, która istniała od początku.

### Dodane

- `scripts/skrzynka.py` i `hooks/skrzynka.sh` — skrzynka poleceń użytkownika. Plik
  `.danaco/skrzynka.txt` powstaje razem ze znacznikiem, a hook `PostToolUse` czyta go po
  każdym użyciu narzędzia i przekazuje nowe linie do kontekstu tury kodem 2 (w tym
  zdarzeniu kod 2 nie przerywa wykonanej już operacji). Każda linia dochodzi dokładnie
  raz; pozycja odczytu w `.danaco/skrzynka.pozycja`.
- Odrzucanie frazy potwierdzenia w skrzynce. Skrzynka jest kanałem poleceń, nie drogą
  zakończenia zlecenia; blokadę zdejmuje wyłącznie wpis użytkownika na czacie
  (`UserPromptSubmit` z frazą podpisaną w znaczniku). Filtr jest w kodzie skryptu, nie
  w treści polecenia hooka.
- Rozdział „Wiadomość użytkownika w trakcie tury” w `skills/pracuj/SKILL.md`:
  pierwszeństwo polecenia ze skrzynki nad bieżącym krokiem, zależność opóźnienia od
  kadencji wywołań, zakaz łączenia długich zleceń podagentów w jeden nieprzerwany blok
  (blok bez wywołania pośredniego zamyka skrzynkę na cały swój czas) oraz zakaz
  zapewniania użytkownika, że jego wpis na czacie dojdzie.
- Rozdział „Budżet czasu jednego zlecenia podagenta” w
  `skills/orkiestracja-agentow/SKILL.md` — budżet czasu niezależny od budżetu tokenów,
  podział bloków równoległych na partie, przerwanie zlecenia z wynikiem częściowym.

### Zachowanie przy awarii

Skrzynka jest kanałem wygody, nie bramką bezpieczeństwa. Brak znacznika, brak interpretera
Pythona, niekompletna instalacja i pusta skrzynka dają kod 0 i ciszę — niedostępność
skrzynki nigdy nie przerywa pracy ani nie udaje naruszenia dyscypliny.

## [2.0.1] — 2026-09-03

Wydanie jednej reguły: prowadzenie rozmowy z użytkownikiem w trakcie długiej tury.

### Dodane

- Rozdział „Wiadomość użytkownika w trakcie tury” w `skills/pracuj/SKILL.md`. Wiadomość
  wpisana przez użytkownika, kiedy tura trwa, jest dostarczana wraz z wynikiem
  najbliższego wywołania narzędzia, a nie na granicy tury. Tryb ciągłej pracy wydłuża
  tury do godzin, więc sam wytwarza ryzyko, że użytkownik pisze w próżnię. Reguła
  narzuca kadencję wywołań (nie dłużej niż kilka minut bez wywołania), zakaz łączenia
  długich zleceń podagentów w jeden nieprzerwany blok, pierwszeństwo przychodzącej
  wiadomości nad bieżącym krokiem oraz zakaz tłumaczenia użytkownikowi, że wiadomość
  „nie dotarła”, przed sprawdzeniem własnej kadencji wywołań.
- Rozdział „Budżet czasu jednego zlecenia podagenta” w
  `skills/orkiestracja-agentow/SKILL.md` — budżet czasu niezależny od budżetu tokenów,
  podział bloków równoległych na partie, przerwanie zlecenia po przekroczeniu budżetu
  czasu z wynikiem częściowym.

### Uwaga o zakresie

Rozważana i odrzucona była skrzynka czytana strumieniem przez narzędzie `Monitor`
(z wyjątkiem w strażniku dla tego narzędzia). Powód odrzucenia: `Monitor` dostarcza
zdarzenia tą samą drogą co wpisy użytkownika, więc nie omijał granicy tury i nie usuwał
przyczyny ciszy. Skrzynka wróciła w wydaniu 2.1.0, podłączona do hooka `PostToolUse`,
który odpala się po każdym użyciu narzędzia i granicy tury nie potrzebuje.

## [2.0.0] — 2026-09-03

Wydanie porządkujące po audycie manifestów, dokumentacji, hooków, kodu wykonywalnego,
paczek skilli i integralności paczki. Weryfikowane na Claude Code 2.1.257.

### Dodane

- Plik `LICENSE` — licencja zastrzeżona Danaco Holding Group Sp. z o.o., użytek wewnętrzny.
  Pole `license` w `.claude-plugin/plugin.json` wskazuje ten plik.
- Plik `CHANGELOG.md` — historia zmian wyprowadzona z `README.md`.
- Plik `.gitignore` — reguły dla artefaktów Pythona, plików tymczasowych, artefaktów
  systemów plików oraz katalogu roboczego znacznika `.danaco/`.
- Plik `hooks/README.md` — opis zarejestrowanych zdarzeń, kodów wyjścia każdego hooka,
  granicy szukania znacznika i przenośności wrapperów.
- Hook `SessionStart` (tryb `sesja` wrapperów `hooks/straznik.sh` i `hooks/straznik.ps1`) —
  nowa sesja otwarta w katalogu z aktywnym znacznikiem dostaje na starcie ścieżkę
  znacznika, opis zlecenia, datę założenia i liczbę zapisanych kroków. Tryb zawsze
  kończy się kodem 0, także bez interpretera Pythona.
- Jawne limity czasu (`timeout`) dla każdego zarejestrowanego zdarzenia: 10 s dla
  `PostToolUse`, 15 s dla `SessionStart`, 30 s dla `Stop`, `PreToolUse`
  i `UserPromptSubmit`. Bez jawnego limitu przekroczenie domyślnego limitu było
  traktowane jako błąd niepowodujący blokady, czyli hook `Stop` przepuszczał turę.
- Sekcje `Wymagania`, `Instalacja`, `Znane ograniczenia` i `Licencja` w `README.md`
  oraz kolumna „Kiedy się uruchamia” w tabeli szesnastu paczek.

- Katalog `wspolne/standardy-zawodowe/` — jedna kanoniczna kopia standardów zawodowych
  zamiast czterech identycznych kopii w paczkach. Paczki odsyłają do niej ścieżką
  `../../wspolne/standardy-zawodowe/<plik>.md`, liczoną od korzenia paczki.
- Plik `skills/kodowanie/references/engineering-core/spis.md` — spis czterdziestu pięciu
  plików pięciu podpaczek `engineering-core` z jednozdaniowym przeznaczeniem każdego.
  Bez tego spisu 703 kB najświeższego materiału pluginu było nieosiągalne: `SKILL.md`
  paczki `kodowanie` podawał wyłącznie nazwy katalogów w prozie.
- Plik `skills/standard-redakcyjny-jezykowy/references/plik-referencyjny-skilla.md` —
  konwencja zapisu odsyłaczy w plikach paczek.
- Cztery nowe pliki testowe: `tests/test_walidatory.py`, `tests/test_mass_actions.py`,
  `tests/test_audyt_smieci.py`, `tests/test_kontrakt.py`. Zestaw testów wzrósł
  ze 124 do 265 przypadków przechodzących (190 w uruchomieniu przez `unittest`).
- Zdanie delimitujące w opisie każdej z szesnastu paczek — mówi, czego paczka nie
  obejmuje i do której paczki należy sięgnąć zamiast niej.

### Naprawione

- Hook `PostToolUse` nie dostarczał naruszeń do modelu. Walidatory pisały na standardowe
  wyjście, a hook kończył się kodem 0 — przy tym kodzie standardowe wyjście trafia
  wyłącznie do transkrypcji. Naruszenia idą teraz na standardowe wyjście błędów, a hook
  kończy się kodem 2, który w tym zdarzeniu nie blokuje narzędzia, lecz przekazuje raport
  do kontekstu tury. Plik bez naruszeń nie generuje żadnego wyjścia.
- Hook `PostToolUse` przerywał się komunikatem „unbound variable”, gdy zmienna
  `CLAUDE_PLUGIN_ROOT` nie docierała do powłoki hooka. Katalog pluginu jest teraz
  ustalany awaryjnie ze ścieżki skryptu.
- Zapisy plików powyżej około 128 kB nie były w ogóle sprawdzane. Całe zdarzenie było
  przekazywane jako argument wiersza poleceń, co przy dużej treści pliku kończyło się
  błędem „Argument list too long”, pustą ścieżką i cichym pominięciem kontroli.
  Zdarzenie jest teraz czytane ze standardowego wejścia.
- Znacznik zadania w toku był szukany w górę drzewa katalogów bez granicy, aż do korzenia
  systemu plików. Jeden znacznik w katalogu domowym blokował zakończenie tury we
  wszystkich projektach pod nim, w każdej kolejnej sesji. Wędrówka w górę zatrzymuje się
  teraz na korzeniu repozytorium git, na `CLAUDE_PROJECT_DIR` albo po ośmiu poziomach,
  a znacznik w katalogu domowym i w korzeniu systemu plików nie jest uznawany.
- Komunikat blokady podaje absolutną ścieżkę katalogu znacznika, bez której awaryjna
  instrukcja usunięcia katalogu `.danaco` wymagała zgadywania.
- Wzorzec zdarzenia `PostToolUse` pomijał narzędzia `MultiEdit` i `NotebookEdit`, choć
  wzorzec `PreToolUse` w tym samym pliku uznawał je za narzędzia zapisu. Kontrola
  dyscypliny była obchodzona samym wyborem narzędzia zapisu. Wydobycie ścieżki obsługuje
  teraz również pole `notebook_path`.
- Wzorce narzędzi są zakotwiczone z obu stron. Wzorzec niezakotwiczony dopasowywał także
  nazwy zawierające dopasowany ciąg, na przykład `BashOutput` przez `Bash`.
- Hook `PostToolUse` wymuszał `bash` i `python3`, wbrew analizie przenośności zapisanej
  w drugim wrapperze tego samego katalogu. Jest teraz w POSIX `sh`, rejestrowany przez
  `sh` i szuka interpretera w kolejności `python3`, `python`, `py -3`; bez Pythona
  zgłasza brak kontroli i przechodzi dalej, nie blokując pracy.
- Hook `PostToolUse` scalał standardowe wyjście błędów walidatorów z ich raportem, więc
  ślad wyjątku Pythona wyglądał identycznie jak naruszenie dyscypliny. Strumienie są
  rozdzielone, a brakujący plik walidatora daje jawny komunikat o niekompletnej instalacji.
- Walidatory były uruchamiane bez limitu czasu i bez rozpoznania własnej awarii. Każdy
  kod wyjścia poza 0, 2 i 3 jest teraz raportowany jako awaria walidatora, a nie jako
  wynik kontroli.
- `tests/uruchom_testy.sh` przekazywał sterowanie pierwszemu znalezionemu interpreterowi
  bez sprawdzenia wersji, więc `python` wskazujący Pythona 2 kończył się błędem składni.
  Skrypt sprawdza teraz wersję minimalną 3.10 i zna kandydata `py -3`.
- `README.md` nie zawierał sekcji o wymaganiach, instalacji ani licencji, a zależność od
  Pythona 3 — bez którego hook `Stop` blokuje turę — była opisana wyłącznie w instrukcji
  instalacji na serwerze.
- Opis w `.claude-plugin/plugin.json` liczył 387 znaków i był wyliczeniem spisu treści.
  Zastąpiony jednym zdaniem. Opis w `.claude-plugin/marketplace.json` mówił o „16 paczkach
  skilli plus tryb ciągłej pracy”, co dawało siedemnaście pozycji przy szesnastu
  faktycznych; oba pliki mają teraz identyczny opis i identyczną wersję.

- Nazwy wymyślone w bramkach akceptacji: cel `danaco-standard` nie istniał (rzeczywisty
  cel Taskfile'a nazywa się `standard`), a `danaco-kody`, `danaco-komentarze`
  i `danaco-terminy` nie odpowiadały żadnej regule walidatorów. Wpisane zostały
  rzeczywiste nazwy siedmiu reguł odczytane z kodu. Plugin łamał tu własny zakaz
  z paczki `standardy-nazewnictwa`, i to w bramce nazywanej wyrocznią pętli.
- Kolizja wyzwalania paczek `pracuj` i `weryfikatory-dyscypliny`: obie miały dosłownie tę
  samą frazę „nie przerywaj pracy", a wygranie drugiej dawało instrukcję obsługi
  walidatorów, która trybu ciągłej pracy nie uruchamia — znacznik nie powstawał
  i nikt się o tym nie dowiadywał. Fraza należy teraz wyłącznie do `pracuj`.
- Sprzeczność jednostki progu udziału komentarzy: paczka normatywna podawała procent
  wierszy, walidator liczy znaki. Opisany jest stan zgodny z kodem, wraz z progiem
  minimalnego rozmiaru pliku.
- Jedenaście plików `SKILL.md` leżało wewnątrz katalogów `references/`, gdzie system
  skilli ich nie rozpoznaje, a ich frontmatter opisywał warunki wyzwalania. Sześć
  w `engineering-core` przemianowano na `przeglad.md`, pięć katalogów paczki `ui-ux-pro`
  spłaszczono do plików `references/<nazwa>.md`; frontmatter usunięty.
- Sto dziesięć martwych odsyłaczy w plikach referencyjnych — ścieżki liczone od dawnego
  korzenia paczki. W dwóch przypadkach odsyłacz trafiał w plik o innej treści, bo nazwa
  występowała w paczce dwukrotnie.
- Sześćdziesiąt jeden odwołań do siedemnastu paczek, które nie istnieją.
- Znacznik zadania w toku był zakładany w katalogu roboczym, a szukany w katalogu
  roboczym, katalogach nadrzędnych i `CLAUDE_PROJECT_DIR`. Znacznik założony
  z podkatalogu był niewidoczny z korzenia projektu i cała blokada cicho przestawała
  działać. Miejsce znacznika jest teraz wyznaczane deterministycznie.
- Brak skryptu walidatora dawał wynik „zielono": `mass_actions.py verify` kończył się
  kodem 0, choć walidator nigdy się nie uruchomił. Nieobecność narzędzia to teraz
  niepowodzenie kontroli z kodem 4.
- Dopasowanie tagów systemowych zwalniało blokadę zakończenia tury przy tagu
  z atrybutem, tagu niedomkniętym i innej nazwie tagu — jedyne miejsce mechanizmu
  działające w kierunku niebezpiecznym. Gdy pochodzenia frazy nie da się rozstrzygnąć,
  blokada zostaje.
- `skills/kontrola-jakosci/scripts/audyt_smieci.py --usun` usuwał każdy pusty katalog
  w drzewie i wchodził do `node_modules` oraz `.venv`. Domyślny tryb to teraz podgląd,
  usuwanie działa tylko według jawnych wzorców, katalogi zależności i wytworów są
  pomijane, a usuwanie pustych katalogów wymaga osobnego przełącznika.
- Ścieżka zapisu generowanego kodu w `contract_tool.py` pochodziła z danych wejściowych
  i nie była ograniczana do katalogu głównego — kontrakt mógł zapisać plik poza
  repozytorium. Ścieżki są teraz normalizowane i ograniczane.
- Dwa obejścia strażnika (`rm -rf .dan*co`, `mv hooks hooks_off`) oraz fałszywe trafienie
  blokujące czytanie własnych źródeł pluginu.
- Materiał UI opisywał generację poprzednią: mapowanie `hsl(var(--x))`
  w `tailwind.config.ts` zamiast `@theme inline` z OKLCH, `React.forwardRef` usunięty
  z komponentów shadcn/ui, `require()` w module ESM (kod niewykonalny).
  Norma dostępności ujednolicona na WCAG 2.2 wraz z dziewięcioma brakującymi kryteriami;
  OWASP odniesiony do wydania 2025. Wersje sprawdzone w sieci, nie wpisane z pamięci.
- Polecenia uruchamiania skryptów podawane jako `python3 scripts/...` zawodziły
  z katalogu roboczego użytkownika. Wszystkie wystąpienia w szesnastu paczkach mają
  teraz postać `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
- `tests/uruchom_testy.sh` uruchamiał wyłącznie jeden plik testowy — uruchamia teraz
  cały zestaw.

### Zmienione

- Wersja pluginu 2.0.0.
- Klucz `description` usunięty z `hooks/hooks.json`; jedynym kluczem najwyższego poziomu
  jest `hooks`, zgodnie ze schematem konfiguracji hooków. Treść opisu przeniesiona do
  `hooks/README.md`.
- Historia zmian przeniesiona z `README.md` do tego pliku.
- Pochodzenie materiału źródłowego przeniesione z `README.md` do wpisu wersji 1.0.0.

- Nazwa pluginu zmieniona z `danaco-expert-pro` na `danaco-plugin` (nazwa widoczna:
  Danaco Plugin). Wywołanie paczek zmienia się z `danaco-expert-pro:<paczka>`
  na `danaco-plugin:<paczka>`. Nazwy szesnastu paczek pozostają bez zmian.
- Opis w `.claude-plugin/plugin.json` skrócony ze 452 do 166 znaków.
- Katalog współdzielony pluginu nosi nazwę `wspolne/`, nie `shared/` — nazwa `shared/`
  kolidowała z katalogiem `shared/` repozytorium docelowego, do którego plugin odsyła
  w kilkudziesięciu miejscach (`shared/contract.json`).
- Opisy wszystkich szesnastu paczek przepisane: konkretne frazy wyzwalające, tryb
  rozkazujący, rozgraniczenie wzajemne. Rozgraniczenie `design-systemowy` ↔ `ui-ux-pro`
  podane identycznie w obu opisach; roszczenie do projektowania tokenów usunięte
  z `ui-ux-pro`.
- Ciała paczek ujednolicone do układu: kiedy stosować, procedura, kryteria zakończenia,
  ścieżki plików referencyjnych, rozgraniczenie z paczkami sąsiednimi.
- Konfiguracja i progi walidatorów wyniesione z kodu do `konfiguracja-dyscypliny.json`.

### Usunięte

- Sekcja `Uwaga o duplikatach źródłowych` z `README.md` — opisywała archiwa z katalogu
  roboczego autora, których w paczce nie ma.
- Artefakty uruchomień pozostawione w drzewie paczki: katalogi `__pycache__`,
  katalog `.pytest_cache`, pliki `.pyc`.

- Cztery identyczne kopie katalogu `standardy-zawodowe` w paczkach — 143 kB nadmiaru
  i gwarancja rozjazdu po pierwszej edycji.
- Sto dwadzieścia pięć wierszy w `weryfikatory-dyscypliny/SKILL.md` pisanych do
  użytkownika, nie do modelu, wraz z obserwacjami dotyczącymi jednego numeru wydania
  klienta i konfiguracji jednej maszyny.
- Oznaczenia `SK-1`…`SK-7` oraz `A1`–`A4` — własna numeracja niezgodna z zakazem
  z paczki `standardy-nazewnictwa`.

## [1.1.0] — wcześniejsze wydanie

Poprawki mechanizmu trybu ciągłej pracy dla sytuacji, w których model „sam kończył”:

- hook `Stop` przepuszczał turę, gdy klient nie przekazał `transcript_path` — zaczął
  blokować;
- wrapper zakładał `python3` i `bash` — zastąpiony wrapperem POSIX `sh` z wyszukiwaniem
  `python3`, `python`, `py -3`; brak Pythona oznacza blokadę z komunikatem;
- komunikat blokady zawierał frazę potwierdzenia i trafiał do transkrypcji jako wpis
  użytkownika — komunikaty przestały zawierać frazę, a skaner pomija wpisy meta,
  streszczenia i wyniki narzędzi;
- fraza w wiadomości sprzed założenia znacznika zwalniała blokadę przy pierwszym `Stop` —
  liczą się tylko wiadomości późniejsze;
- `cd` do podkatalogu wyłączało blokadę, bo znacznik był szukany tylko w katalogu
  bieżącym — doszły katalogi nadrzędne i `CLAUDE_PROJECT_DIR`;
- `AskUserQuestion` i edycja plików mechanizmu były zabronione tylko behawioralnie —
  doszło zdarzenie `PreToolUse`;
- `plugin.json` wskazywał `hooks/hooks.json`, który Claude Code ładuje automatycznie;
  nowsze wersje klienta zgłaszały to jako błąd ładowania hooków — wpis usunięty;
- doszła droga zwolnienia blokady przez `UserPromptSubmit`, niezależna od transkrypcji.

## [1.0.0] — wydanie pierwsze

Konsolidacja trzech wcześniejszych pluginów (`danaco-code`, `danaco-console`,
`danaco-dyscyplina`) oraz materiału dodatkowego w jeden plugin o szesnastu paczkach
skilli. Wcześniejsze wersje opisywały standardy prozą — walidator dyscypliny był
wzmiankowany w opisie paczki, ale nie istniał jako uruchamialny kod; to wydanie dodało
działające skrypty na bibliotece standardowej Pythona i powłoce, bez zależności
zewnętrznych.

Pochodzenie materiału źródłowego:

- `danaco-code`, `danaco-console`, `danaco-dyscyplina` — pluginy przeniesione bez zmiany
  nazw skilli;
- materiał projektowy wchłonięty do paczki `ui-ux-pro` (tauri-ui, wydajność frontu,
  design interfejsu, weryfikacja wizualna, dostępność WCAG);
- materiał inżynierski wchłonięty jako uzupełnienie paczek
  `architektura-i-dokumentacja`, `kodowanie` i `most-tauri`;
- materiał kontroli jakości wchłonięty do paczki `kontrola-jakosci`;
- materiał komponentów interfejsu (shadcn/ui, Tailwind) jako podstawa paczki `ui-ux-pro`;
- standard redakcyjny i językowy jako podstawa paczki `standard-redakcyjny-jezykowy`.
