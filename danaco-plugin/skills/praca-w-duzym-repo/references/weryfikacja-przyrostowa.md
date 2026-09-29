# Weryfikacja przyrostowa

## Dlaczego nie „uruchom wszystko”

W repozytorium ponadmilionowym pełny zestaw kontroli trwa minuty. Uruchamiany po każdej edycji
zamienia pracę w czekanie, a co gorsza — miesza sygnały. Gdy naraz zawodzi kompilacja Go, kontrola
typów TypeScriptu i piętnaście testów, ustalenie, która z tych rzeczy jest przyczyną, a które
skutkiem, zajmuje więcej niż sama poprawka.

Drabina rozwiązuje oba problemy: każdy szczebel jest tańszy od następnego i eliminuje klasę
przyczyn, zanim uruchomi się droższe narzędzia.

## Szczeble

### 1. Kontrakt

```bash
task contract:check          # albo: python3 tools/contract_tool.py check --root .
```

Sekundy. Wykluczasz najbardziej mylącą klasę usterek: rozjazd między `shared/contract.json`
a wygenerowanym kodem. Rozjazd objawia się wyżej jako „nieznane pole”, „brak metody”,
„typ nie pasuje” — w miejscach, które z kontraktem pozornie nie mają związku.

### 2. Go — tylko dotknięte pakiety

```bash
go build ./server/internal/session/...
go vet ./server/internal/session/...
```

Kompilacja jednego poddrzewa zamiast całego modułu. `go vet` łapie rzeczy, których kompilator
nie zgłasza: nieużyte wyniki, podejrzane znaczniki struktur, błędne formaty `Printf`.

Gdy zmiana dotyka węzła, `go build ./...` i tak będzie potrzebne — ale dopiero po tym, jak sam
pakiet się kompiluje.

### 3. TypeScript

```bash
npx tsc --noEmit
```

Kontrola typów obejmuje cały projekt klienta i nie da się jej sensownie zawęzić — ale jest
znacznie szybsza od testów i wychwytuje większość skutków zmiany kontraktu.

### 4. Testy dotknięte

```bash
python3 tools/impact.py --root . --staged
```

Narzędzie wypisuje gotowe polecenia `go test` i `npx vitest run` ograniczone do zasięgu zmiany.

Gdy w wyniku pojawia się informacja, że żaden z dotkniętych modułów nie ma własnego testu, to nie
jest usterka narzędzia, tylko ustalenie: zmieniasz kod, którego nic nie chroni. Warto to
odnotować, nawet jeśli akurat teraz nie dopisujesz testu.

### 5. Lint

```bash
golangci-lint run --timeout 5m
staticcheck ./...
```

Osobny szczebel, bo znajduje inną klasę rzeczy niż kompilator: martwy kod, nieobsłużone błędy,
podejrzane konwersje, wycieki zasobów. Uruchamiaj przed commitem, nie po każdej edycji —
jest wolniejszy od kompilacji i jego uwagi rzadko blokują dalszą pracę.

### 6. Pełny zestaw

```bash
task go:test          # gotestsum z równoległością wyliczoną z liczby rdzeni
cd client && npx vitest run
```

`gotestsum` daje czytelne podsumowanie zamiast strumienia `ok/FAIL`, co przy kilkuset pakietach
jest różnicą między odczytaniem wyniku a przewijaniem. `GO_PAR` w `Taskfile.yml` jest liczone
z `nproc` (połowa rdzeni, nie mniej niż 2), więc `task go:test` dopasowuje się do maszyny;
wartość nadpiszesz zmienną środowiskową, gdy kompilacja i testy konkurują o pamięć.

### 7. Bramki domowe

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <ścieżki>
```

Zbiorczy cel Taskfile/CI nosi nazwę `standard` i nie jest osobną
binarka — patrz `SKILL.md` sekcja o drabinie. Realnie uruchamia `style_guard.py`
(reguły `limit-dlugosci-komentarza` i `udzial-komentarzy`) oraz `nazwy_guard.py`
(reguła `wymyslony-kod`). Kontrola pojęć spoza korpusu, pisowni i literówek
(Vale, Semgrep, `typos`, `codespell`, `hunspell-pl`,
LanguageTool) nie jest częścią tego pluginu — to osobne narzędzia repozytorium,
jeśli je masz skonfigurowane. Progi bramek `style_guard.py`/`nazwy_guard.py` ustawia
się plikiem `--config` (patrz umiejętność `weryfikatory-dyscypliny`).

Te bramki **odmawiają**, a nie doradzają — dlatego uruchamiaj je przed commitem, a nie na koniec
dnia. Bramka, która odmówi po dwudziestu plikach, kosztuje dwadzieścia poprawek zamiast jednej.

Dwie rzeczy dotyczą tego repozytorium szczególnie:

- **Pliki generowane muszą być wyłączone spod reguły `udzial-komentarzy`.** Wygenerowany
  `contract.go` ma na kontrakcie startowym (32 tryby) około 12 000 znaków komentarza na 1000 linii,
  a `contract.ts` około 8 400 — wielokrotność każdego rozsądnego progu, bo komentuje każdy tryb,
  każde pole i każdy kod błędu. To nie jest proza do skrócenia, tylko tabela, w której komentarz
  jest jedynym miejscem z opisem trybu. Zmierz to na własnym kontrakcie: liczby rosną razem z nim.
- **Komunikaty błędów pokazywane użytkownikowi nie mogą zawierać kodów ani nazw komunikatów** —
  pilnuje tego reguła Semgrep. Kod przekazuj polem `error_code` w kopercie, nie w treści zdania.

### 8. End-to-end

```bash
cd client && npx playwright test
```

Przeglądarki są już pobrane. Testy end-to-end łapią to, czego nie widzą testy jednostkowe:
przepływ między modułami, zachowanie po zerwaniu połączenia, stan interfejsu przy przełączaniu
trybów. Przy 40 trybach sesyjnych to jedyna praktyczna kontrola tego, że nawigacja faktycznie
działa w każdym z nich.

Po testach przepływu warto sprawdzić jakość samego interfejsu — to szczebel, który łatwo
pominąć, bo nic się nie psuje, gdy się go pominie:

```bash
pa11y http://localhost:5173            # WCAG, konfiguracja w /etc/danaco/pa11y.json
lighthouse http://localhost:5173 --quiet --chrome-flags="--headless"
```

Przy 40 trybach sesyjnych nie sprawdzisz ich wszystkich ręcznie. Napisz test Playwright, który
przechodzi po `MODE_IDS` z kontraktu i dla każdego trybu robi zrzut oraz kontrolę `pa11y` —
rejestr trybów jest generowany, więc taki test sam obejmie każdy nowy tryb bez dopisywania
kolejnej pozycji na liście.

### 9. Budowa powłoki

```bash
cd desktop && cargo tauri build
```

Najdroższy szczebel, uruchamiany przed wydaniem. Wychwytuje rzeczy niewidoczne wcześniej:
błędy konfiguracji uprawnień, brakujące zasoby, problemy pakowania procesu pobocznego.
`sccache` i `mold` skracają powtórną budowę wielokrotnie — pierwsza i tak potrwa.

Wydanie pod Windows idzie przez `cargo-xwin` i `llvm-mingw` bez opuszczania Linuksa; gotowy
instalator sprawdzisz w QEMU z KVM albo pod Wine. To istotne przy on-premise, gdzie stacje
klienckie bywają windowsowe, a maszyna wytwórcza nie jest.

## Typowe komunikaty i ich prawdziwe przyczyny

| Komunikat | Pierwszy trop |
|---|---|
| Go: `undefined: shared.MsgCosTam` | kontrakt zmieniony, kod niezregenerowany — szczebel 1 |
| Go: `cannot use x (variable of type *T) as T value` | pole stało się opcjonalne w kontrakcie (wskaźnik) |
| TS: `Property 'x' does not exist on type` | pole usunięte lub przemianowane w kontrakcie |
| TS: `Type 'string' is not assignable to type 'ModeId'` | tryb podany literałem zamiast stałą z rejestru |
| Vitest: skrót kontraktu się nie zgadza | zregenerowano tylko jedną stronę |
| Tauri: komenda nie odpowiada | brak wpisu w `capabilities` albo proces rdzenia nie wystartował |
| `gofmt -l` wskazuje `contract.go` | generator uruchomiony bez `gofmt` w PATH — narzędzie o tym ostrzega |
| `staticcheck` zgłasza martwy kod po zmianie kontraktu | usunięte pole miało jedynego odbiorcę |
| test przechodzi lokalnie, pada w zestawie | wspólny stan między testami — sprawdź kolejność i zasoby |

## Zmiany etapowe

Zmiana przekrojowa (16+ plików) powinna dać się podzielić na etapy, z których **każdy kompiluje
się i przechodzi testy**. Wzorzec dla zmiany łamiącej w kontrakcie:

1. Dodaj nowe pole jako opcjonalne, zregeneruj, zbuduj. Nic jeszcze go nie używa — kompiluje się.
2. Wypełniaj nowe pole w rdzeniu, zostawiając stare. Buduj, testuj.
3. Przełącz odbiorców na nowe pole, pakiet po pakiecie. Po każdym — szczeble 2 i 3.
4. Usuń stare pole z kontraktu, zregeneruj, zbuduj.

Każdy z tych etapów jest osobnym commitem, do którego można wrócić. Wykonanie całości jednym
ciągiem daje stan, w którym nic się nie kompiluje i nie wiadomo, który z czterech kroków zawinił.

## Weryfikacja bez uruchamiania

Nie wszystko wymaga wykonania kodu. Tańsze i często wystarczające:

- `git diff --stat` — czy zmiana ma rozmiar, którego się spodziewasz; nagły plik z setką zmienionych
  linii to zwykle przypadkowe przeformatowanie
- `git diff -- '*_test.go'` — czy testy zmieniły się razem z kodem, którego dotyczą
- `rg 'TODO|FIXME|XXX' <zmienione pliki>` — czy nie zostawiasz notatek roboczych
- `task contract:validate` — czy kontrakt jest spójny, jeszcze przed generowaniem
- `gofmt -l .` — czy nie wchodzi do diffu plik sformatowany przypadkiem; wygenerowany
  `contract.go` przechodzi przez `gofmt`, więc nie powinien się tu pojawić

Ostatnia z tych rzeczy bywa najbardziej opłacalna: błąd w kontrakcie wykryty przed generowaniem
kosztuje jedną poprawkę, wykryty po — regenerację i ponowną kompilację obu światów.
