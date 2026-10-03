# Danaco Plugin

Plugin wnosi do Claude Code standardy inżynierskie Danaco w piętnastu paczkach skilli
oraz uruchamialne narzędzia kontroli: walidatory dyscypliny kodu i nazewnictwa, audyt
porządku, bramkę jakości i hook kontroli po zapisie pliku.

**Informacje szczegółowe dokumentu:**

| | |
|---|---|
| **Tytuł** | Danaco Plugin — opis paczki |
| **Klasa dokumentu** | Stan wdrożenia |
| **Odbiorcy** | deweloper instalujący i używający pluginu |
| **Przeznaczenie** | opisuje, co plugin zawiera, czego wymaga, jak się instaluje i jak działa jego warstwa techniczna |
| **Zakres** | paczki skilli, wymagania, instalacja, hooki, serwer MCP, skrypty, struktura katalogów, ograniczenia, licencja |
| **Poza zakresem** | instalacja na serwerze zdalnym — opisana w [INSTALACJA-VPS.md](INSTALACJA-VPS.md); historia wydań — w [CHANGELOG.md](CHANGELOG.md); treść normatywna standardów — w plikach `SKILL.md` poszczególnych paczek |
| **Dokumenty powiązane** | [INSTALACJA-VPS.md](INSTALACJA-VPS.md) · [CHANGELOG.md](CHANGELOG.md) · [hooks/README.md](hooks/README.md) · [LICENSE](LICENSE) |
| **Wersja pluginu** | 3.1.0 |
| **Data** | 2026-09-29 |

## Spis treści

1. [Do czego służy plugin](#1-do-czego-służy-plugin)
2. [Wymagania](#2-wymagania)
3. [Instalacja](#3-instalacja)
   - [3.1 Przejście z wersji 1.1.0](#31-przejście-z-wersji-110)
4. [Paczki skilli](#4-paczki-skilli)
5. [Hooki](#5-hooki)
6. [Serwer MCP katalogu programów](#6-serwer-mcp-katalogu-programów)
7. [Skrypty](#7-skrypty)
   - [7.1 Narzędzia wspólne pluginu](#71-narzędzia-wspólne-pluginu)
   - [7.2 Narzędzia paczek](#72-narzędzia-paczek)
   - [7.3 Testy](#73-testy)
8. [Struktura katalogów](#8-struktura-katalogów)
9. [Podział na dwa pluginy](#9-podział-na-dwa-pluginy)
10. [Znane ograniczenia](#10-znane-ograniczenia)
11. [Licencja](#11-licencja)

---

## 1. Do czego służy plugin

Plugin odpowiada na cztery potrzeby pracy z modelem nad kodem produkcyjnym:

| Potrzeba | Odpowiedź pluginu |
|---|---|
| Model ma pracować według jednego standardu, nie według własnych nawyków | piętnaście paczek skilli z treścią normatywną, wybieranych z opisu zadania |
| Standard ma być sprawdzalny maszynowo, nie tylko opisany prozą | walidatory dyscypliny i nazewnictwa, audyt porządku, bramka jakości, hook kontroli po zapisie |
| Naruszenie standardu ma być widoczne zaraz po zapisie, a nie dopiero w przeglądzie | hook `PostToolUse` uruchamiający oba walidatory na zmienionym pliku |
| Model ma sięgać po programy Danaco, zamiast instalować własne narzędzia | serwer MCP `danaco-programy` z katalogiem programów danaco-nexus i zdalnym uruchamianiem (rozdz. 6) |

Paczki skilli nie wymagają komend. Model dobiera je z opisu zadania na podstawie pola
`description` w plikach `SKILL.md`; można je też wywołać wprost nazwą paczki.

---

## 2. Wymagania

| Wymaganie | Znaczenie | Skutek braku |
|---|---|---|
| Claude Code w terminalu | hook pluginu wykonuje klient terminalowy; część interfejsów okiennych i Cowork go nie wykonuje | zostaje sama warstwa behawioralna paczek; kontrola po zapisie nie działa |
| `python3` w PATH (wersja 3.10 lub nowsza) | walidatory, audyt porządku, narzędzia kontraktu i testy są w Pythonie | patrz akapit poniżej |
| POSIX `sh` | wrapper hooka jest w POSIX `sh` (`dash`, `busybox ash`, Git Bash) | hook nie uruchamia się wcale |
| Git for Windows (tylko Windows) | dostarcza `sh` dla wrappera hooka | hook nie uruchamia się; walidatory zostają dostępne z wiersza poleceń |
| `/usr/bin/python3` | interpreter serwera MCP `danaco-programy` (ścieżka bezwzględna w `.mcp.json`) | serwer MCP nie startuje, klient pokazuje błąd połączenia; paczki i walidatory działają |
| `ssh`, `rsync` i `Host danaco-nexus` w `~/.ssh/config` (poza danaco-nexus) | tryb zdalny serwera MCP: kopia katalogu i uruchamianie programów na nexusie | katalog programów się nie odświeża, `uruchom` nie łączy się z nexusem |

**Zależność od Pythona 3 nie jest opcjonalna.** Wrapper szuka interpretera kolejno jako
`python3`, `python` i `py -3` (launcher Windows). Bez interpretera hook `PostToolUse`
zgłasza brak kontroli w transkrypcji i przechodzi dalej — praca nie jest przerywana.

Plugin nie ma zależności zewnętrznych Pythona — wszystkie skrypty korzystają wyłącznie
z biblioteki standardowej. Wyjątkiem są testy paczki `ui-ux-pro`
(`skills/ui-ux-pro/scripts/tests/requirements.txt`), które wymagają `pytest`.

---

## 3. Instalacja

Katalog pluginu jest jednocześnie własnym marketplace (zawiera
`.claude-plugin/marketplace.json`), więc instalacja nie wymaga zewnętrznego źródła.

```bash
claude plugin marketplace add <katalog-pluginu>
claude plugin install danaco-plugin@danaco --scope user
claude plugin list
```

Po każdej aktualizacji plików pluginu:

```bash
claude plugin marketplace update danaco
```

Szybki test bez instalacji trwałej, na czas jednej sesji:

```bash
claude --plugin-dir <katalog-pluginu>
```

Instalacja na serwerze zdalnym, nadanie praw wykonania skryptom, weryfikacja działania
hooków i zakresy instalacji: [INSTALACJA-VPS.md](INSTALACJA-VPS.md).

Historia wydań i wersja klienta, na której weryfikowano mechanizm blokady:
[CHANGELOG.md](CHANGELOG.md).

---

### 3.1 Przejście z wersji 1.1.0

Plugin nosił wcześniej nazwę `danaco-expert-pro`. Po instalacji wersji 2.0.0
odinstaluj poprzednią, inaczej w sesji działają dwa zestawy tych samych paczek
i model wybiera między nimi losowo:

```bash
claude plugin uninstall danaco-expert-pro
```

Wywołanie paczki zmienia nazwę: `danaco-expert-pro:kodowanie` staje się
`danaco-plugin:kodowanie`. Nazwy paczek przeniesionych z wersji 1.1.0 pozostają bez
zmian, więc odwołania w projektach wystarczy poprawić w przedrostku.


## 4. Paczki skilli

| # | Paczka | Przeznaczenie | Kiedy się uruchamia |
|---|---|---|---|
| 1 | `architektura-i-dokumentacja` | Projektowanie systemu, decyzje ADR, dokumentacja techniczna, runbooki, praktyki produktowe. | Trzeba zaprojektować system, wybrać technologię, zapisać decyzję ADR albo napisać README, dokumentację API lub przewodnik wdrożeniowy. |
| 2 | `design-systemowy` | Warstwa systemowa i dokumentacyjna projektowania: systemy projektowe, żetony, standard CSS, identyfikacja wizualna, agentic UX. | Powstaje lub jest dokumentowany system projektowy, zestaw żetonów, identyfikacja marki, baner albo interfejs aplikacji ze stopniowaniem autonomii modelu. |
| 3 | `dyscyplina-inzynierska` | Standard prowadzenia kodu produkcyjnego: limit komentarzy, formalny ton, zakaz wymyślonych nazw i kodów, drabina weryfikacji. | Pisany lub zmieniany jest kod w repozytorium Danaco; pojawia się dryf od zadania, skłonność do komentarzy-esejów albo do nadawania własnych oznaczeń. |
| 4 | `kanal-websocket` | Kanał komunikacyjny między rdzeniem Go a interfejsem TypeScript: koperta komunikatu, korelacja, wznowienie, przeciwciśnienie. | Dodawany lub zmieniany jest komunikat kanału; zdarzenia gubią się, przychodzą w złej kolejności albo połączenie się rwie. |
| 5 | `kodowanie` | Pisanie, budowa i debugowanie kodu: karty dwudziestu języków, frameworki, bazy danych, narzędzia budowy, podpaczki inżynierskie. | Trzeba napisać, poprawić lub zrefaktoryzować kod, zbudować aplikację, API, bazę danych albo serwer MCP; wystąpił błąd, ślad stosu lub awaria. |
| 6 | `kontrakt-zrodlo-prawdy` | Plik kontraktu w repozytorium produktu jako jedyne źródło prawdy i generowanie z niego kodu Go oraz TypeScript. | Powstaje lub zmienia się typ danych, komunikat, komenda, kod błędu albo tryb sesyjny; typy rozjeżdżają się między rdzeniem a interfejsem. |
| 7 | `kontrola-jakosci` | Przegląd kodu przed scaleniem i audyt projektu zakończony raportem ustaleń z planem naprawy. | Trzeba sprawdzić zmianę przed scaleniem, ocenić jakość lub bezpieczeństwo kodu albo wykonać audyt projektu bądź witryny. |
| 8 | `macierz-trybow-sesji` | Macierz trybów sesyjnych: środowiska, moduły, poziomy izolacji, widoczność danych, mosty między środowiskami. | Powstaje nowy tryb, moduł albo środowisko; zmienia się to, co dany tryb widzi lub gdzie zapisuje; badana jest izolacja danych. |
| 9 | `most-tauri` | Granica między powłoką Tauri 2 w Rust a rdzeniem Go: podział IPC i kanału, uprawnienia, cykl życia procesu, pakowanie. | Powstaje lub zmienia się komenda Tauri albo konfiguracja uprawnień; aplikacja nie startuje, port jest zajęty, proces zostaje po zamknięciu okna. |
| 10 | `orkiestracja-agentow` | Autonomiczna pętla czterech modeli: role, kolejka zadań, budżety, bramki akceptacji, warunki stopu, dziennik audytowy. | Projektowany jest przepływ z udziałem wielu modeli, przydzielane są role i budżety albo pętla utknęła bądź przepaliła budżet. |
| 11 | `praca-w-duzym-repo` | Metoda pracy w repozytorium powyżej miliona linii: orientacja przed edycją, mapa repozytorium, budżet zmiany, weryfikacja przyrostowa. | Pierwsza edycja w nieznanej części repozytorium; zmiana dotyka wielu pakietów; budowa albo testy trwają zbyt długo; planowana jest refaktoryzacja. |
| 12 | `standard-redakcyjny-jezykowy` | Jednolity kształt i język opracowań: nagłówek i metryka, klasy dokumentów, słownik wiążący, polszczyzna, typografia. | Pisany lub redagowany jest dokument wchodzący do zbioru dokumentacji Danaco albo istniejący dokument jest sprawdzany pod kątem zgodności ze standardem. |
| 13 | `standardy-nazewnictwa` | Nazwy opisujące funkcję, nie metaforę; zakaz wymyślonych oznaczeń literowo-numerycznych; etykiety jako krótkie nazwy funkcji. | Nadawane są nazwy plikom, zmiennym, funkcjom, typom, komponentom i etykietom; pada „jak to nazwać”, „nie wymyślaj nazw”. |
| 14 | `ui-ux-pro` | Budowa interfejsu klientem TypeScript: komponenty shadcn/ui, Tailwind, tryb ciemny i jasny, dostępność WCAG, wydajność w powłoce Tauri. | Powstaje lub zmienia się widok, komponent, formularz, tabela albo układ; pada „dodaj komponent”, „dostępność”, „interfejs zwalnia”. |
| 15 | `weryfikatory-dyscypliny` | Obsługa i strojenie walidatora dyscypliny oraz nazewnictwa, a także hooka kontroli po zapisie. | Trzeba uruchomić kontrolę dyscypliny, zrozumieć lub dostroić regułę, dodać token do listy dozwolonych, podłączyć kontrolę pod pre-commit albo CI. |

Katalog `skills/` zawiera dokładnie te piętnaście paczek i żadnej innej.

---

## 5. Hooki

Plugin rejestruje jedno zdarzenie. Pełny opis i kody wyjścia:
[hooks/README.md](hooks/README.md).

| Zdarzenie | Matcher | Wrapper | Limit czasu | Co robi |
|---|---|---|---|---|
| `PostToolUse` | `^(Write\|Edit\|MultiEdit\|NotebookEdit)$` | `hooks/po_zapisie.sh` | 10 s | Po zapisie pliku uruchamia walidator dyscypliny i walidator nazewnictwa; naruszenia trafiają na standardowe wyjście błędów z kodem 2, który w tym zdarzeniu przekazuje raport do kontekstu tury, nie blokuje narzędzia. Plik bez naruszeń nie generuje wyjścia. |

Kontrola po zapisie obejmuje pliki `.go`, `.ts`, `.tsx`, `.js`, `.jsx`, `.rs`, `.py`;
pozostałe hook pomija.

---

## 6. Serwer MCP katalogu programów

Od wersji 3.1.0 plugin uruchamia serwer MCP `danaco-programy`
(`mcp/danaco-programy.py`, rejestracja w `.mcp.json`). Serwer udostępnia modelowi
katalog programów Danaco z `/danaco/programy` na danaco-nexus — ponad tysiąc poleceń
w działach (grafika, wideo, dźwięk, 3D, dokumenty, kod, dane, web, devops,
bezpieczeństwo, testy, modele AI) — żeby model szukał narzędzia w katalogu, zanim
cokolwiek zainstaluje albo uzna, że go brak.

| Narzędzie | Co robi |
|---|---|
| `szukaj` | Wyszukuje programy i skille po temacie, zadaniu albo nazwie; zwraca krótką listę: polecenie, dział, przeznaczenie. |
| `opis` | Pełny opis programu albo skilla: ścieżka, przeznaczenie, test działania i instrukcja `SKILL.md`; model czyta go przed pierwszym użyciem programu. |
| `dzialy` | Lista działów katalogu z liczbą poleceń. |
| `lista` | Wszystkie polecenia jednego działu z jednozdaniowym opisem. |
| `maszyny` | Wykaz maszyn wirtualnych (strefy środowisk: system, gniazda, skill maszyny, jedno zdanie opisu) — ten sam, który stoi w instrukcjach serwera. |
| `maszyna` | Szczegółowy wykaz jednej maszyny (programy we wzorcu i braki, dostęp, zasoby, limity ról) i jej skill; skill maszyny jest obowiązkowy przed wejściem na nią. |
| `uruchom` | Wykonuje polecenie z programami Danaco na danaco-nexus: pliki z `pliki` trafiają do `$WE`, polecenie działa w `$WY`, a zawartość `$WY` wraca do `wyniki_do`. |

Instrukcje serwera podają wszystkie dziedziny katalogu i wszystkie maszyny z jednym zdaniem
opisu. Wykaz maszyn serwer czyta z `katalog/maszyny.json`, który `zbuduj_indeks.py` składa z
konfiguracji usługi stref (`/etc/danaco/srodowiska.json`), `WZORZEC-NARZEDZIA.md` i frontmattera
skilli maszyn — serwer niczego o maszynach nie powiela.

Tryb pracy serwer wybiera sam po nazwie hosta; zmienna `DANACO_PROGRAMY_TRYB`
(`lokalny` albo `zdalny`) go nadpisuje.

| Tryb | Gdzie | Źródło katalogu | Narzędzie `uruchom` |
|---|---|---|---|
| `lokalny` | danaco-nexus | `/danaco/programy/katalog` czytany z dysku; programy są w `PATH` | liczy lokalnie; pliki wejściowe dowiązuje do `$WE` bez kopiowania |
| `zdalny` | pozostałe serwery | kopia katalogu ściągana z nexusa przez `rsync` (najwyżej raz na 10 minut) do `$XDG_CACHE_HOME/danaco-programy/katalog`, domyślnie pod `~/.cache` | wysyła pliki na nexusa do `/danaco/wymiana/<konto>/<serwer>/<zadanie>/we`, liczy tam jako to samo konto i ściąga wyniki do `wyniki_do` |

Tryb zdalny wymaga na serwerze `ssh` i `rsync` oraz wpisu `Host danaco-nexus`
w `~/.ssh/config` konta, z kluczem technicznym przyjmowanym bez pytań (połączenie
w trybie `BatchMode`). Bez tego katalog się nie odświeża, a `uruchom` kończy się
komunikatem o braku połączenia; reszta pluginu działa bez zmian.

Zmienne pomocnicze: `DANACO_NEXUS_HOST` — nazwa hosta nexusa (domyślnie
`danaco-nexus`), `DANACO_KATALOG` — inne położenie katalogu. Serwer korzysta wyłącznie
z biblioteki standardowej Pythona i startuje interpreterem `/usr/bin/python3` (ścieżka
bezwzględna w `.mcp.json`).

---

## 7. Skrypty

Wszystkie skrypty działają na bibliotece standardowej Pythona i na POSIX `sh`.

### 7.1 Narzędzia wspólne pluginu

| Skrypt | Co robi |
|---|---|
| `scripts/mass_actions.py` | Orkiestrator: `verify`, `cleanup`, `quality-gate` na całym repozytorium jednym poleceniem. |
| `scripts/konfiguracja_kontroli.py` | Progi i słowniki kontroli dyscypliny oraz nazewnictwa w jednym miejscu; nadpisywane plikiem `konfiguracja-dyscypliny.json`. |
| `scripts/przechodzenie_repozytorium.py` | Jedna polityka przechodzenia drzewa repozytorium i przycinania katalogów dla wszystkich kontroli. |

Pełna weryfikacja repozytorium jednym poleceniem:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify /ścieżka/do/repozytorium
```

### 7.2 Narzędzia paczek

| Skrypt | Paczka | Co robi |
|---|---|---|
| `skills/weryfikatory-dyscypliny/scripts/style_guard.py` | `weryfikatory-dyscypliny` | Limit i udział komentarzy, wymyślone kody, ton wypowiedzi. |
| `skills/standardy-nazewnictwa/scripts/nazwy_guard.py` | `standardy-nazewnictwa` | Oznaczenia literowo-numeryczne, etykiety będące zdaniami, identyfikatory z metafory. |
| `skills/kontrola-jakosci/scripts/audyt_smieci.py` | `kontrola-jakosci` | Cache i pliki tymczasowe, puste katalogi, znaczniki TODO i FIXME. |
| `skills/kodowanie/scripts/quality_gate.sh` | `kodowanie` | Budowa, analiza statyczna, lint i testy dla Go, TypeScript, Rust i Pythona — wykrywane automatycznie. |
| `skills/kontrakt-zrodlo-prawdy/scripts/contract_tool.py` | `kontrakt-zrodlo-prawdy` | Walidacja kontraktu, generowanie kodu Go i TypeScript, wykrywanie rozjazdu. |
| `skills/kanal-websocket/scripts/channel_tool.py` | `kanal-websocket` | Generowanie i kontrola komunikatów kanału na podstawie kontraktu. |
| `skills/macierz-trybow-sesji/scripts/modes_tool.py` | `macierz-trybow-sesji` | Walidacja macierzy trybów sesyjnych i widoczności danych. |
| `skills/orkiestracja-agentow/scripts/workflow_tool.py` | `orkiestracja-agentow` | Walidacja definicji przepływu, budżetów i bramek akceptacji. |
| `skills/most-tauri/scripts/tauri_check.py` | `most-tauri` | Kontrola konfiguracji i uprawnień powłoki Tauri. |
| `skills/praca-w-duzym-repo/scripts/repo_map.py` | `praca-w-duzym-repo` | Mapa repozytorium: pakiety, rozmiary, granice. |
| `skills/praca-w-duzym-repo/scripts/impact.py` | `praca-w-duzym-repo` | Zasięg zmiany: co zależy od zmienianego pliku. |
| `skills/ui-ux-pro/scripts/shadcn_add.py` | `ui-ux-pro` | Dodawanie komponentów shadcn/ui z kontrolą wersji. |
| `skills/ui-ux-pro/scripts/tailwind_config_gen.py` | `ui-ux-pro` | Generowanie konfiguracji Tailwind z żetonów. |
| `skills/kodowanie/references/engineering-core/07-debug-testy-deploy/scripts/kontrola_strony.py` | `kodowanie` | Kontrola strony w przeglądarce: konsola, sieć, zrzuty ekranu. |
| `skills/kodowanie/references/engineering-core/07-debug-testy-deploy/scripts/z_serwerem.py` | `kodowanie` | Uruchomienie serwera na czas sond diagnostycznych i zatrzymanie go po nich. |

### 7.3 Testy

| Skrypt | Co obejmuje |
|---|---|
| `tests/uruchom_testy.sh` | Uruchamia oba zestawy pierwszym interpreterem w wersji 3.10 lub nowszej z listy `python3`, `python`, `py -3`. Zwraca kod niezerowy, gdy zawiódł którykolwiek zestaw. Nie zapisuje plików bajtkodu w drzewie pluginu. |
| `tests/test_po_zapisie.py` | Hook kontroli po zapisie i kontrakt `hooks/hooks.json` wobec plików pluginu; woła prawdziwy wrapper `sh` z JSON-em zdarzenia na standardowym wejściu. |
| `tests/test_walidatory.py` | Reguły obu walidatorów: trafienie i brak trafienia każdej reguły, przypadki brzegowe kodowania i rozmiaru pliku. |
| `tests/test_mass_actions.py` | Bramka zbiorcza: kody wyjścia, zachowanie przy braku skryptu walidatora. |
| `tests/test_audyt_smieci.py` | Audyt porządku: tryb podglądu, pomijane katalogi zależności, przełącznik usuwania pustych katalogów. |
| `tests/test_kontrakt.py` | Narzędzie kontraktu: walidacja, ograniczenie ścieżek zapisu do katalogu głównego. |
| `skills/ui-ux-pro/scripts/tests/` | Narzędzia paczki `ui-ux-pro`. Zestaw napisany pod `pytest`; bez niego `uruchom_testy.sh` pomija go z komunikatem. Zależności: `skills/ui-ux-pro/scripts/tests/requirements.txt`. |

Stan wydania 2.3.1: 264 przypadki w zestawie wspólnym (biblioteka standardowa), wszystkie
przechodzą; jeden przypadek pomijany wymaga uprawnień innych niż konto administracyjne.
Zestaw paczki `ui-ux-pro` uruchamia się osobno, pod `pytest`.

```bash
sh tests/uruchom_testy.sh
```

---

## 8. Struktura katalogów

```
.
├── .claude-plugin/
│   ├── plugin.json          manifest pluginu: nazwa, wersja, opis, licencja, słowa kluczowe
│   └── marketplace.json     wpis marketplace; katalog pluginu jest własnym marketplace
├── hooks/
│   ├── hooks.json           rejestracja jednego zdarzenia; jedyny klucz to `hooks`
│   ├── po_zapisie.sh        wrapper PostToolUse (POSIX sh, fail-open)
│   ├── po_zapisie.py        walidator dyscypliny i nazewnictwa po zapisie
│   └── README.md            opis hooka i kodów wyjścia
├── mcp/
│   └── danaco-programy.py   serwer MCP katalogu programów (rozdz. 6)
├── .mcp.json                rejestracja serwera MCP `danaco-programy`
├── scripts/                 narzędzia wspólne pluginu (rozdz. 7)
├── wspolne/
│   └── standardy-zawodowe/  jedna kanoniczna kopia standardów zawodowych dla paczek
├── skills/                  piętnaście paczek skilli (rozdz. 4)
├── tests/                   zestaw testów pluginu (rozdz. 7.3)
├── README.md                ten dokument
├── INSTALACJA-VPS.md        instalacja na serwerze zdalnym
├── CHANGELOG.md             historia wydań
├── LICENSE                  warunki korzystania
└── .gitignore
```

Każda paczka w `skills/` ma ten sam układ:

```
skills/<paczka>/
├── SKILL.md        wejście paczki: pole `description` decyduje o doborze paczki przez model
├── references/     treść normatywna czytana na żądanie
├── scripts/        narzędzia paczki (gdy paczka je ma)
└── assets/         pliki do skopiowania do projektu (gdy paczka je ma)
```

Plik `SKILL.md` występuje wyłącznie na pierwszym poziomie paczki — jeden na paczkę,
piętnaście w całym drzewie. Zagnieżdżone opracowania wprowadzające noszą nazwę
`przeglad.md`, żeby klient nie brał ich za osobne paczki. Dwie paczki mają materiał
wielopoziomowy:

| Paczka | Układ materiału |
|---|---|
| `kodowanie` | `references/engineering-core/` zawiera pięć podpaczek tematycznych, każda z własnym `przeglad.md`, katalogiem `references/` i — gdy dotyczy — `scripts/`; spis wszystkich plików podpaczek leży w `skills/kodowanie/references/engineering-core/spis.md` |
| `architektura-i-dokumentacja` | `references/engineering-core/` z materiałem uzupełniającym (`przeglad.md` i własny katalog `references/`) obok trzech katalogów tematycznych: `architektura/`, `dokumentacja-techniczna/`, `praktyki-produktowe/` |

Katalog `wspolne/standardy-zawodowe/` niesie jedną kopię standardów zawodowych — języka
zawodowego, kontroli jakości pracy i katalogu antywzorców — zamiast kopii powtórzonej
w każdej z paczek, które się do nich odwołują.

---

## 9. Podział na dwa pluginy

Od wersji 3.0.0 mechanizm trybu ciągłej pracy prowadzi osobny plugin `danaco-praca`
(od jego wersji 5.0.0: polecenia `/praca`, `/koniec-pracy`, blokady `/bez-…`/`/z-…`,
`/sudo-nie`/`/sudo-tak` i `/tryb`). Ten plugin zawiera wyłącznie warstwę wiedzy i umiejętności
oraz maszynowe walidatory.

Oba pluginy są niezależne: `danaco-plugin` działa w pełni bez `danaco-praca` i odwrotnie.
Instaluje się je osobno i wersjonuje osobno.

Przy obu zainstalowanych naraz hooki nie kolidują. Każdy plugin rejestruje własny
`hooks.json`, a Claude Code sumuje wpisy z obu: `danaco-plugin` obsługuje `PostToolUse`
z matcherem `^(Write|Edit|MultiEdit|NotebookEdit)$`, a `danaco-praca` (5.0.0) nie
rejestruje `PostToolUse` wcale — działa w `UserPromptSubmit`, `PreToolUse`, `Stop`,
`SessionStart` i `SubagentStart`.

---

## 10. Znane ograniczenia

| Ograniczenie | Skutek |
|---|---|
| Hook `PostToolUse` jest doradczy | zapis wykonał się przed jego uruchomieniem; naruszenie trafia do kontekstu tury, ale zapisu nie cofa |
| Klienci niewykonujący hooków pluginu | kontrola po zapisie nie działa; zostaje treść normatywna paczek i ręczne wywołanie walidatorów |
| Windows bez Git for Windows | wrapper `sh` nie uruchomi się; walidatory pozostają dostępne z wiersza poleceń |
| Zapisy przez narzędzia MCP | nie wywołują zdarzenia `PostToolUse` pluginu, więc nie są kontrolowane |
| Serwer MCP `danaco-programy` na systemie bez `/usr/bin/python3` (Windows) | serwer nie startuje; klient zgłasza błąd połączenia serwera MCP, reszta pluginu działa |
| Reguły `wymyslony-kod`, `nazwa-metaforyczna` i `oznaczenie-literowo-numeryczne` są heurystyczne | możliwe fałszywe trafienia; procedura ich obsługi leży w `skills/weryfikatory-dyscypliny/SKILL.md` |

Pełny opis walidatorów i ich granic: `skills/weryfikatory-dyscypliny/SKILL.md`.

---

## 11. Licencja

Licencja zastrzeżona Danaco Holding Group Sp. z o.o. — wszelkie prawa zastrzeżone, użytek
wewnętrzny. Warunki korzystania, zakazy i wyłączenie odpowiedzialności: [LICENSE](LICENSE).

---

*Koniec dokumentu. Danaco Plugin — opis paczki, wersja 3.0.0, 2026-09-05.*

---
*© 2026 Danaco Holding Group Sp. z o.o. Wszelkie prawa zastrzeżone.*
*Warunki korzystania: [LICENSE](LICENSE). Kontakt: support@danaco-group.pl*
