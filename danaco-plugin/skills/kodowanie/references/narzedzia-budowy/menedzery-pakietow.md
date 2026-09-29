# Menedżery pakietów — karta

## Procedury podstawowe

**Zasada nadrzędna.** Przed jakąkolwiek instalacją ustal, którego menedżera używa projekt. Obecność
`package-lock.json` oznacza npm, `yarn.lock` — Yarn, `pnpm-lock.yaml` — pnpm; `requirements.txt`,
`pyproject.toml` lub `poetry.lock` wskazują odpowiednie narzędzia Pythona. Używaj wyłącznie
menedżera już obecnego w projekcie.

**npm — instalacja i przypinanie.** Nowe zależności dodawaj jawnie, rozróżniając zależności
uruchomieniowe i deweloperskie:
```
npm install nazwa-pakietu
npm install --save-dev nazwa-pakietu
```
Każda instalacja aktualizuje `package.json` i `package-lock.json` — oba pliki zatwierdzaj razem.
Plik `package-lock.json` przypina pełne drzewo zależności do dokładnych wersji i sum kontrolnych;
nie edytuj go ręcznie.

**npm — odtwarzanie środowiska na czystej maszynie.** Używaj `npm ci`, nie `npm install`:
```
npm ci
```
`npm ci` instaluje dokładnie to, co opisuje `package-lock.json`, usuwając uprzednio istniejący
`node_modules`, i kończy się błędem przy niezgodności locka z `package.json` — to właściwe polecenie
dla CI oraz świeżych stanowisk.

**npm — polecenia informacyjne.** Przed zmianami zależności ustal stan faktyczny:
```
npm ls --depth=0
npm outdated
npm view nazwa-pakietu versions
```

**pip i venv — środowisko izolowane.** Nigdy nie instaluj pakietów projektu w interpreterze
globalnym. Na czystej maszynie z Windows utwórz i aktywuj środowisko wirtualne:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```
W CMD aktywacja to `.\.venv\Scripts\activate.bat`; w systemach POSIX — `source .venv/bin/activate`.
Katalog `.venv` wpisz do `.gitignore`. Weryfikuj aktywację poleceniem `where.exe python` (ścieżka ma
wskazywać `.venv`).

**pip — instalacja, przypinanie, odtwarzanie.** Instaluj z podaniem wersji i utrwalaj stan
środowiska:
```
python -m pip install requests==2.32.3
python -m pip install -r requirements.txt
python -m pip freeze > requirements.txt
```
Wywołuj pip jako `python -m pip`, aby mieć pewność, że dotyczy aktywnego środowiska. W projektach
rozróżniających zależności bezpośrednie od pełnego zrzutu utrzymuj konwencję projektu (np.
`requirements.in` + narzędzie kompilujące albo `pyproject.toml`); nie zmieniaj jej samowolnie.

**pip — odtwarzanie środowiska na czystej maszynie.** Pełna sekwencja dla Windows:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

## Bezpieczne wzorce

- **Lockfile w repozytorium.** `package-lock.json` (oraz odpowiedniki `yarn.lock`, `pnpm-lock.yaml`,
  `poetry.lock`) zatwierdzaj w repozytorium i nigdy nie wpisuj do `.gitignore`. Bez locka każda
  maszyna buduje inne drzewo zależności, a diagnoza „u mnie działa” staje się niemożliwa.
- **Wersje w manifestach.** W `requirements.txt` przypinaj wersje operatorem `==`. W `package.json`
  akceptuj zakresy (`^`), ponieważ dokładne wersje egzekwuje lock; nie rozszerzaj zakresów bez
  potrzeby.
- **Audyt podatności.** Po zmianach zależności uruchamiaj audyt i przekazuj wynik właścicielowi
  projektu:
  ```
  npm audit
  python -m pip install pip-audit
  pip-audit
  ```
  Nie stosuj `npm audit fix --force` — potrafi podnieść wersje główne pakietów i złamać zgodność;
  poprawki wersji głównych wprowadzaj świadomie i pojedynczo.
- **Skrypty cyklu życia.** Instalacja pakietów npm wykonuje skrypty instalacyjne pakietów, a `pip
  install` może wykonywać kod budujący. Instaluj wyłącznie pakiety o zweryfikowanej nazwie i
  pochodzeniu; literówka w nazwie (typosquatting) oznacza wykonanie obcego kodu.
- **Rejestry prywatne.** Konfigurację rejestru (`.npmrc`, `pip.ini`) utrzymuj w projekcie bez
  tokenów; tokeny przechowuj w zmiennych środowiskowych lub konfiguracji użytkownika, nigdy w
  repozytorium.
- **Jedno środowisko na projekt.** Dla Pythona utrzymuj `.venv` w katalogu projektu; nie współdziel
  środowiska między projektami, ponieważ konflikty wersji stają się wtedy nierozwiązywalne.

## Diagnostyka

- **Konflikty wersji npm.** Komunikat `ERESOLVE` opisuje sprzeczne wymagania równorzędne (peer
  dependencies). Przeczytaj, które pakiety są w sporze (`npm ls nazwa-pakietu` pokazuje, kto czego
  wymaga) i rozwiąż konflikt doborem zgodnych wersji. Flagę `--legacy-peer-deps` traktuj jako
  obejście ostatniej szansy stosowane za wiedzą właściciela projektu, nie jako domyślną odpowiedź.
- **Konflikty wersji pip.** `ResolutionImpossible` wskazuje pary pakietów o sprzecznych wymaganiach;
  `python -m pip check` wykrywa niespójności w już zainstalowanym środowisku. Ustal wymagania
  konfliktujących pakietów (`python -m pip show nazwa`) i dobierz wersje przecięcia; w razie
  potrzeby odtwórz środowisko od zera w nowym `.venv`.
- **Rozbieżność manifestu i locka.** Gdy `npm ci` zgłasza niezgodność, nie usuwaj locka — uruchom
  `npm install`, obejrzyj różnicę w `package-lock.json` i zatwierdź ją świadomie.
- **Czyszczenie pamięci podręcznej.** Stosuj dopiero po zdiagnozowaniu, że przyczyną jest uszkodzony
  wpis pamięci podręcznej (np. błędy sum kontrolnych):
  ```
  npm cache verify
  npm cache clean --force
  python -m pip cache purge
  ```
- **Diagnoza „skąd ten pakiet”.** `npm ls nazwa` pokazuje drzewo zależności prowadzące do pakietu;
  `python -m pip show nazwa` — wersję, lokalizację i pakiety zależne (`Required-by`).
- **Rozjazd interpreterów w Windows.** Przy wielu instalacjach Pythona sprawdzaj `py -0` (lista
  interpreterów) i `where.exe python`; błędy typu „pakiet zainstalowany, a import nie działa” niemal
  zawsze oznaczają instalację do innego interpretera niż uruchamiany.

## Operacje nieodwracalne — wymagają zgody właściciela projektu

Nie wykonuj poniższych poleceń bez wyraźnej zgody właściciela projektu udzielonej dla konkretnego
przypadku:

- `npm publish` — publikuje pakiet w rejestrze publicznym; opublikowanej wersji nie można nadpisać,
  a możliwość wycofania jest ograniczona czasowo i regulaminowo. Publikacja może ujawnić kod
  własnościowy Danaco.
- `npm unpublish` oraz `npm deprecate` — usuwają lub oznaczają wersje, na których mogą polegać inne
  zespoły.
- `pip uninstall` w środowisku globalnym (poza aktywnym `.venv`) — może usunąć pakiety, od których
  zależą narzędzia systemowe i inne projekty na maszynie użytkownika.
- Usuwanie plików lock (`package-lock.json`, `poetry.lock`) lub katalogu `.venv` z zawartością
  niewynikającą z manifestów — niszczy odtwarzalność środowiska; regeneracja locka zmienia wersje w
  całym drzewie zależności.
- `npm cache clean --force` i `python -m pip cache purge` w środowiskach o ograniczonym dostępie do
  sieci — mogą uniemożliwić ponowną instalację.
- Zmiana wersji głównych zależności (`npm install pakiet@latest`, edycja zakresów w `package.json`)
  — to zmiana kontraktu projektu, nie czynność techniczna.

## Typowe błędy modeli LLM przy tym narzędziu

1. **Instalacja globalna zamiast środowiska projektu.** `pip install` bez aktywnego `.venv` albo
   `npm install -g` dla zależności projektu zaśmieca maszynę i psuje odtwarzalność. Zawsze najpierw
   utwórz i aktywuj `.venv`; w npm instaluj lokalnie, a narzędzia uruchamiaj przez `npx`.
2. **`pip install pakiet` bez wersji.** Środowisko przestaje być odtwarzalne, a kolejna instalacja
   może przynieść niezgodną wersję. Podawaj `==wersja` i utrwalaj stan w `requirements.txt`.
3. **Mieszanie npm z yarn lub pnpm w jednym projekcie.** Powstają konkurencyjne pliki lock i
   niespójny `node_modules`. Ustal menedżera po istniejącym pliku lock i używaj wyłącznie jego.
4. **`npm install` w CI lub na czystej maszynie zamiast `npm ci`.** `npm install` może zmodyfikować
   lock i zainstalować inne wersje niż zatwierdzone. Do odtwarzania środowiska służy `npm ci`.
5. **Usuwanie `package-lock.json` lub `node_modules` jako uniwersalna „naprawa”.** Kasowanie locka
   zmienia wersje w całym drzewie i ukrywa realny problem. Najpierw przeczytaj komunikat błędu i
   zdiagnozuj konflikt; regeneracja locka wymaga zgody właściciela projektu.
6. **Pomijanie aktywacji `.venv` między poleceniami.** Każde nowe okno powłoki startuje bez
   aktywnego środowiska; kolejne `pip install` trafia wtedy do interpretera globalnego. Aktywuj
   środowisko w każdej sesji albo wywołuj wprost `.\.venv\Scripts\python.exe -m pip ...`.
7. **Wymyślanie nazw i wersji pakietów.** Nieistniejąca nazwa to w najlepszym razie błąd instalacji,
   w najgorszym — pakiet podszywający się. Weryfikuj nazwę i dostępne wersje (`npm view nazwa
   versions`, `python -m pip index versions nazwa` lub strona rejestru) przed instalacją.
8. **Edytowanie plików lock ręcznie.** Lock jest artefaktem generowanym z sumami kontrolnymi; ręczna
   edycja go unieważnia. Zmieniaj manifest i pozwól narzędziu przebudować lock.
9. **`npm audit fix --force` jako odruch na ostrzeżenia audytu.** Wymusza wersje główne i łamie
   zgodność interfejsów. Analizuj raport audytu i podnoś wersje pojedynczo, z uruchomieniem testów.
10. **Ignorowanie rozjazdu interpreterów w Windows.** Model instaluje przez `pip`, a uruchamia przez
    `py` lub inną instalację Pythona, po czym diagnozuje „zepsuty pakiet”. Konsekwentnie używaj
    `python -m pip` wewnątrz aktywnego `.venv` i weryfikuj interpreter poleceniem `where.exe
    python`.
