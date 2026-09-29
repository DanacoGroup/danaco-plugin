# Struktury referencyjne — wzorcowe drzewa katalogów projektów Danaco

Drzewa poniżej są punktem wyjścia, nie sztywnym szablonem: katalog powstaje, gdy ma zawartość, a
odstępstwo od wzorca wymaga zapisu w dokumencie architektury. Przy każdym katalogu podano, po co
istnieje i co w nim NIE mieszka — druga część jest ważniejsza, bo degeneracja zaczyna się od
wkładania rzeczy „gdzie się zmieści”. Szczegóły konwencji poszczególnych technologii podają karty
`../kodowanie/references/frameworki/frameworki.md` i `jezyki-programowania`.

## 1. Aplikacja FastAPI (src-layout, moduły domenowe)

```
projekt/
├── pyproject.toml          # jedyny manifest: zależności, narzędzia, metadane
├── README.md               # uruchomienie, konfiguracja — dokument kanoniczny
├── docs/
│   ├── architektura.md     # decyzje i granice warstw; NIE opisy chwilowego stanu kodu
│   └── adr/                # zapisy decyzji architektonicznych, numerowane
├── src/
│   └── nazwa_aplikacji/
│       ├── main.py         # tworzenie aplikacji, montowanie routerów; NIE logika
│       ├── konfiguracja.py # jedno źródło ustawień (pydantic-settings); NIE stałe po modułach
│       ├── faktury/        # moduł domenowy — pełny pion jednego obszaru
│       │   ├── router.py   # endpointy HTTP; NIE reguły biznesowe, NIE SQL
│       │   ├── schematy.py # modele wejścia/wyjścia API (Pydantic)
│       │   ├── uslugi.py   # logika biznesowa; NIE zna Request/Response
│       │   ├── modele.py   # modele ORM tego obszaru
│       │   └── repozytorium.py  # zapytania do bazy; jedyna warstwa znająca SQL
│       ├── kontrahenci/    # kolejny moduł domenowy o tej samej budowie wewnętrznej
│       └── wspolne/        # tylko elementy naprawdę przekrojowe: błędy, zależności DI;
│                           # NIE wysypisko „utils" — moduł nazwany po odpowiedzialności
├── migrations/             # migracje Alembic; NIE ręczne skrypty SQL obok
├── tests/                  # lustro src/: tests/faktury/test_uslugi.py itd.
│   └── conftest.py         # wspólne fixture'y; baza testowa tymczasowa, nie w drzewie
└── .env.example            # wzór zmiennych środowiskowych; NIGDY .env z sekretami w repo
```

Uzasadnienia. Src-layout wymusza instalację pakietu do testów — testy sprawdzają to, co zostanie
wdrożone, nie przypadkowy import z bieżącego katalogu. Podział domenowy (`faktury/`, `kontrahenci/`)
zamiast technicznego (`routers/`, `models/` dla wszystkiego) trzyma razem kod zmieniający się razem:
nowa funkcja obszaru to zmiany w jednym katalogu, nie w pięciu. Kierunek zależności wewnątrz modułu:
`router → uslugi → repozytorium`; odwrotny import jest naruszeniem granic (karta
`references/praktyki-produktowe/katalog-degeneracji.md`, poz. 5).

Reguły rozrostu. Nowy moduł domenowy powstaje, gdy pojawia się nowy obszar
pojęciowy — nie nowy endpoint. Plik `uslugi.py` > ~400 linii dzieli się
według pod-odpowiedzialności (`uslugi_naliczania.py`,
`uslugi_wysylki.py`) wewnątrz tego samego modułu. Moduł używany przez
inne moduły domenowe przez import wewnętrzny → sygnał, że część wspólna
powinna zejść do `wspolne/` lub stać się osobnym obszarem.

Testy lustrzane: struktura `tests/` powtarza `src/`, dzięki czemu brak
lustra od razu wskazuje kod bez testów
(`diff <(cd src/nazwa_aplikacji && find . -type d | sort) <(cd tests && find . -type d | sort)`).

## 2. Aplikacja Next.js (App Router)

```
projekt/
├── package.json            # jedyny manifest; blokada wersji w repo
├── next.config.ts
├── app/                    # routing = struktura katalogów; TYLKO pliki routingu
│   ├── layout.tsx          # układ główny; NIE logika biznesowa
│   ├── page.tsx
│   ├── faktury/
│   │   ├── page.tsx        # komponent serwerowy: pobiera dane, składa widok
│   │   ├── actions.ts      # akcje serwerowe obszaru ('use server')
│   │   └── [id]/page.tsx
│   └── api/                # route handlers wyłącznie dla klientów zewnętrznych;
│                           # NIE dla własnych komponentów — te wołają akcje/lib
├── components/
│   ├── ui/                 # elementy prezentacyjne wielokrotnego użytku (przycisk, tabela)
│   └── faktury/            # komponenty jednego obszaru; NIE dostęp do bazy
├── lib/
│   ├── db.ts               # klient bazy — jedyny plik, który go tworzy
│   ├── faktury.ts          # logika domenowa i zapytania obszaru; wołana z serwera
│   └── konfiguracja.ts     # odczyt i walidacja zmiennych środowiskowych w jednym miejscu
├── styles/                 # arkusze globalne i tokeny; wartości projektowe TYLKO tutaj
├── public/                 # zasoby statyczne serwowane wprost; NIE pliki robocze
└── tests/                  # testy jednostkowe lib/ i komponentów; e2e w tests/e2e/
```

Uzasadnienia. Granica server/client jest architektoniczna: komponenty
serwerowe czytają dane przez `lib/`, komponenty klienckie (`'use client'`)
dostają dane w propsach i nie importują niczego, co dotyka bazy lub
sekretów. `lib/` pełni rolę warstwy usług — trzyma logikę poza plikami
routingu, dzięki czemu zmiana routingu nie rusza logiki i odwrotnie.

Reguły rozrostu. Komponent użyty w jednym miejscu mieszka przy miejscu
użycia; przenosi się do `components/` przy drugim użyciu, nie „na zapas”.
`lib/faktury.ts` > ~300 linii → katalog `lib/faktury/` z podziałem według
odpowiedzialności. Dyrektywę `'use client'` dodaje się najniżej, jak się
da — pęcznienie części klienckiej to dryf wydajnościowy.

## 3. Aplikacja Electron

```
projekt/
├── package.json
├── src/
│   ├── main/               # proces główny: okna, menu, cykl życia, dostęp do systemu
│   │   ├── index.ts
│   │   └── ipc/            # obsługa kanałów IPC pogrupowana obszarami
│   ├── preload/            # mosty context-bridge; JEDYNE miejsce styku main-renderer;
│   │                       # NIE logika — wyłącznie ekspozycja wąskiego API
│   ├── renderer/           # interfejs (React/Vue); NIE import modułów Node —
│   │                       # wszystko przez API z preload
│   └── wspolne/
│       └── typy.ts         # typy kontraktów IPC współdzielone przez oba procesy;
│                           # NIE kod wykonywalny zależny od środowiska
├── zasoby/                 # ikony, obrazy instalatora; NIE zasoby interfejsu (te w renderer)
├── tests/                  # lustro src/; testy main bez uruchamiania okien
└── docs/adr/
```

Uzasadnienia. Trzy katalogi odpowiadają trzem środowiskom wykonawczym
o różnych uprawnieniach — pomieszanie ich to prosta droga do luk
bezpieczeństwa (renderer z dostępem do systemu plików). Wspólne typy
kontraktów IPC w jednym pliku sprawiają, że zmiana kontraktu niezgodna po
obu stronach jest błędem kompilacji, nie awarią w działaniu.

Reguły rozrostu. Nowy obszar funkcjonalny dodaje parę: moduł w `main/ipc/`
plus odpowiadające typy w `wspolne/typy.ts`. Rozrost `preload/` ponad
cienkie mosty oznacza, że logika ucieka z `main/` — zawróć ją.

## 4. Pakiet Python biblioteczny

```
pakiet/
├── pyproject.toml          # metadane publikacji, zależności minimalne;
│                           # narzędzia deweloperskie w grupie dev, nie w zależnościach
├── README.md               # przykład użycia w 10 linii — pierwszy kontakt użytkownika
├── CHANGELOG.md            # zmiany według wersji publikowanych; NIE dziennik commitów
├── LICENSE
├── src/
│   └── nazwa_pakietu/
│       ├── __init__.py     # API publiczne: świadome eksporty + __all__;
│       │                   # NIE automatyczny reeksport wszystkiego
│       ├── py.typed        # znacznik typowania dla odbiorców
│       └── _wewnetrzne/    # moduły z podkreśleniem = poza kontraktem publicznym
├── tests/
└── docs/                   # dokumentacja API, jeżeli wykracza poza README
```

Uzasadnienia. Biblioteka różni się od aplikacji tym, że ma kontrakt
publiczny: `__init__.py` definiuje, co jest obiecane użytkownikom, a prefiks
`_` mówi „to może się zmienić bez ostrzeżenia”. Zależności minimalne
i z zakresami wersji (nie przypięte na sztywno) — przypinanie należy do
aplikacji końcowej, biblioteka przypinająca wersje psuje instalacje
odbiorcom.

Reguły rozrostu. Każde nowe nazwisko w `__init__.py` to zobowiązanie —
dodawaj rozmyślnie, usuwaj tylko z okresem wycofania odnotowanym
w CHANGELOG. Funkcjonalność opcjonalna z ciężkimi zależnościami → extras
(`pip install pakiet[raporty]`), nie zależność obowiązkowa.

## 5. Serwer MCP

```
serwer-mcp/
├── pyproject.toml          # albo package.json dla wariantu TypeScript
├── README.md               # instalacja, konfiguracja klienta, wykaz narzędzi
├── src/
│   └── nazwa_serwera/
│       ├── main.py         # utworzenie serwera FastMCP, rejestracja, uruchomienie
│       ├── konfiguracja.py # adresy usług, klucze — ze zmiennych środowiskowych
│       ├── narzedzia/      # jeden plik = narzędzia jednego obszaru
│       │   ├── faktury.py  # definicje @tool: walidacja wejścia, opisy dla modelu
│       │   └── kontrahenci.py
│       ├── zasoby/         # definicje resources MCP, jeżeli serwer je udostępnia
│       └── klienci/        # komunikacja z systemami zewnętrznymi (API, baza);
│                           # NIE wewnątrz definicji narzędzi
└── tests/                  # testy logiki narzędzi bez uruchamiania protokołu
```

Uzasadnienia. Oddzielenie `narzedzia/` (kontrakt dla modelu: nazwy, opisy,
schematy wejścia) od `klienci/` (jak faktycznie gadamy z systemem) pozwala
testować logikę bez protokołu MCP i wymieniać system źródłowy bez zmiany
kontraktu narzędzi. Opis narzędzia jest interfejsem użytkownika dla modelu
LLM — zmiany opisów traktuj jak zmiany API. Szczegóły projektowania
narzędzi: `../kodowanie/references/budowa-serwerow-mcp/budowa-serwerow-mcp.md`.

Reguły rozrostu. Nowe narzędzia dopisuj do pliku obszaru; nowy plik
powstaje dla nowego obszaru, nie dla piątego narzędzia w starym. Serwer
z > ~20 narzędziami przemyśl: czy nie scalić operacji w narzędzia ogólniejsze
albo podzielić na dwa serwery.

## 6. Monorepo wielopakietowe

Zasadne, gdy kilka pakietów zmienia się razem i dzieli kod (aplikacja +
biblioteka kliencka + wspólne typy). Niezasadne dla projektów o osobnych
cyklach wydawniczych i osobnych zespołach — wtedy osobne repozytoria.

```
monorepo/
├── package.json            # korzeń: definicja workspaces i skrypty przekrojowe;
│                           # NIE zależności aplikacji — te w pakietach
├── pnpm-workspace.yaml     # (pnpm) wykaz pakietów
├── apps/
│   ├── panel/              # aplikacja Next.js — struktura jak w sekcji 2
│   └── api/                # usługa serwerowa
├── packages/
│   ├── wspolne-typy/       # typy kontraktów dzielone przez apps; NIE logika
│   ├── klient-api/         # wygenerowany/ręczny klient API dla panelu
│   └── konfiguracja-eslint/ # wspólna konfiguracja narzędzi jako pakiet
├── docs/adr/               # decyzje przekrojowe, w tym ADR o samym monorepo
└── .github/workflows/      # CI z filtrowaniem: buduj tylko pakiety dotknięte zmianą
```

Uzasadnienia. Współdzielenie kodu przez pakiet workspace
(`"wspolne-typy": "workspace:*"`) zamiast kopiowania eliminuje degenerację
nr 8 z katalogu: jedna definicja typu, wersjonowana razem ze zmianą.
Granica apps/packages jest kierunkiem zależności: aplikacje importują
pakiety, pakiety NIGDY aplikacji ani siebie nawzajem bez jawnej zależności
w manifeście — pilnuje tego `dependency-cruiser` w CI.

Reguły rozrostu. Kod potrzebny drugiej aplikacji przenosi się do pakietu
w `packages/` — nie importuje przez ścieżkę względną między aplikacjami
(`../../apps/panel/...` to naruszenie budowy). Pakiet powstaje przy drugim
użyciu, nie przy pierwszym przeczuciu.

## 7. Projekt skryptów administracyjnych PowerShell

```
skrypty-administracyjne/
├── README.md               # wykaz skryptów: co robi, wymagane uprawnienia, przykład wywołania
├── modules/
│   └── DanacoNarzedzia/    # moduł wspólny: logowanie, obsługa poświadczeń, sesje
│       ├── DanacoNarzedzia.psd1   # manifest modułu z wersją i eksportami
│       └── DanacoNarzedzia.psm1
├── scripts/
│   ├── kopie-zapasowe/     # skrypty pogrupowane zadaniami administracyjnymi
│   │   └── Backup-BazaKlientow.ps1   # nazwy Czasownik-Rzeczownik z czasowników
│   │                                  # zatwierdzonych (Get-Verb)
│   └── konta/
│       └── Disable-KontaNieaktywne.ps1
├── config/
│   └── ustawienia.example.psd1  # wzorzec konfiguracji; NIE wartości środowisk w skryptach
└── tests/                  # testy Pester: Nazwa.Tests.ps1 obok logiki modułu
```

Uzasadnienia. Wspólny moduł zamiast kopiowania funkcji między skryptami —
skrypty administracyjne degenerują przez kopiuj-wklej szybciej niż
aplikacje, bo powstają pod presją czasu. Każdy skrypt: nagłówek pomocy
komentarzowej (`.SYNOPSIS`, `.PARAMETER`, `.EXAMPLE`), `[CmdletBinding()]`
i obsługa `-WhatIf` dla operacji zmieniających stan — skrypt bez `-WhatIf`
uruchamiany na produkcji to hazard. Poświadczenia wyłącznie przez mechanizm
sekretów (SecretManagement); hasło w skrypcie lub konfiguracji to incydent.

Reguły rozrostu. Funkcja użyta w drugim skrypcie przechodzi do modułu.
Skrypt > ~200 linii logiki → logika do funkcji modułu, skrypt zostaje
cienkim wywołaniem z parametrami.

## Reguły wspólne wszystkich struktur

- **Konfiguracja narzędzi** mieszka w plikach standardowych ekosystemu
  w korzeniu (`pyproject.toml`, `package.json`, `.editorconfig`) — nie
  w skryptach własnych powielających funkcje narzędzi.
- **Dokumenty kanoniczne** to zamknięta lista: README, architektura, ADR-y,
  CHANGELOG (biblioteki), runbook (usługi). Każdy inny plik `.md` wymaga
  uzasadnienia — pliki `NOTATKI.md`, `TODO.md`, `PODSUMOWANIE.md` w drzewie
  to narośla (standardy zawodowe, `../../wspolne/standardy-zawodowe/standardy-zawodowe.md`).
- **Pliki robocze** (zrzuty, wyniki pośrednie, bazy testowe) powstają
  w katalogu tymczasowym poza drzewem i giną po użyciu; `.gitignore`
  obejmuje je zawczasu.
- **Testy** mieszkają w `tests/` lustrzanie do źródeł; wyjątek stanowią
  ekosystemy z konwencją testu przy pliku (np. `*.test.ts` obok źródła) —
  wtedy stosuj konwencję ekosystemu, ale jedną, w całym projekcie.
- **Zasoby** (obrazy, czcionki, szablony) mieszkają w katalogu zasobów
  właściwej warstwy, nigdy między plikami kodu.
