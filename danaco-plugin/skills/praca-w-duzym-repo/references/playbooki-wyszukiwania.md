# Playbooki wyszukiwania

Zestaw sprawdzonych sposobów na znalezienie rzeczy w repozytorium ponadmilionowym bez zapełniania
kontekstu. Zasada wspólna: **zawężaj, zanim przeczytasz**.

## Spis treści

1. [Go](#go)
2. [TypeScript](#typescript)
3. [Rust / Tauri](#rust--tauri)
4. [Przez granice języków](#przez-granice-języków)
5. [Przez historię git](#przez-historię-git)
6. [Kiedy nic nie znajdujesz](#kiedy-nic-nie-znajdujesz)

## Go

**Gdzie jest zdefiniowany typ albo funkcja**

```bash
rg --type go '^(type|func) NazwaSzukana' -n
```

Kotwica `^` odcina użycia i zostawia deklaracje. Bez niej trafień jest zwykle dwa rzędy wielkości
więcej.

**Metody na typie**

```bash
rg --type go 'func \([a-z]+ \*?Manager\)' -n
```

**Kto woła tę funkcję**

```bash
rg --type go '\bNewManager\(' -n --glob '!*_test.go'
```

Wykluczenie testów bywa istotne — w dojrzałym pakiecie testy generują większość trafień, a rzadko
o nie chodzi.

**Co eksportuje pakiet, bez czytania plików**

```bash
go doc ./server/internal/session
go doc ./server/internal/session Manager
```

To najtańszy sposób poznania powierzchni pakietu: kilkanaście linii zamiast kilkuset.

**Kto importuje ten pakiet**

```bash
go list -f '{{.ImportPath}} {{.Imports}}' ./... | rg 'internal/session'
```

Albo `impact.py`, który liczy to samo przechodnio i od razu podaje polecenia weryfikacji.

**Gdzie obsługiwany jest komunikat**

W Danaco Console komunikaty pochodzą z kontraktu, więc szukaj po stałej, nie po łańcuchu znaków:

```bash
rg --type go 'MsgAiPrompt' -n
```

Jeśli znajdziesz porównanie do literału `"ai.prompt"` zamiast stałej `shared.MsgAiPrompt`, to samo
w sobie jest usterką — literał nie zostanie zaktualizowany przy zmianie kontraktu.

## TypeScript

**Gdzie zdefiniowany**

```bash
rg --type ts '^export (function|const|class|interface|type) NazwaSzukana' -n
```

**Kto importuje moduł**

```bash
rg --type ts "from ['\"].*nazwa-modulu" -n
```

Dokładniej i przechodnio: `impact.py --changed client/src/lib/ws.ts`.

**Kto dotyka kanału bezpośrednio, omijając wspólną warstwę**

```bash
rg --type ts 'new WebSocket\(' -n
```

Wynik powinien mieć jedno trafienie — wspólną warstwę kanału. Każde kolejne to moduł, który
buduje własne połączenie i wypada poza wspólne wznowienie, kolejkowanie i obsługę błędów.

**Gdzie używany jest tryb sesyjny**

```bash
rg --type ts 'MODES\[|isModeId|ModeId' -n
```

**Nieuzasadnione rzutowania**

```bash
rg --type ts ' as (any|unknown)' -n
```

W kodzie zbudowanym na wygenerowanym kontrakcie rzutowanie na `any` prawie zawsze oznacza, że ktoś
obszedł typ zamiast poprawić kontrakt.

## Rust / Tauri

**Komendy udostępnione interfejsowi**

```bash
rg --type rust '#\[tauri::command\]' -A 2 -n
```

**Uprawnienia powłoki**

```bash
rg -n 'permissions|capabilities' desktop/src-tauri/capabilities/ desktop/src-tauri/tauri.conf.json
```

Powierzchnia Rust w tej aplikacji ma być mała. Jeśli lista komend rośnie, to sygnał, że logika
przecieka z rdzenia Go do powłoki — a powłoka jest najtrudniejszą warstwą do przetestowania.

## Wyszukiwanie po składni, nie po tekście

`ast-grep` dopasowuje wzorce do drzewa składniowego, więc nie myli deklaracji z użyciem,
komentarza z kodem ani `store.New` z `mystore.Newton`.

```bash
ast-grep --lang go --pattern 'store.New($$$)'          # wszystkie wywołania konstruktora
ast-grep --lang go --pattern 'func ($_ $_) Handle($$$) $$$'
ast-grep --lang ts --pattern 'new WebSocket($$$)'
```

Podmiana też idzie po strukturze:

```bash
ast-grep --lang go --pattern 'store.New()' --rewrite 'store.New(dataDir)' --update-all
```

To jest właściwe narzędzie do zmian przekrojowych. `sed` po dziesiątkach plików w repozytorium tej
wielkości prędzej czy później trafi w komentarz albo w łańcuch znaków, a błąd wyjdzie tygodnie
później. Przy zmianie obejmującej kilkanaście plików warto najpierw uruchomić `ast-grep` bez
`--update-all`, obejrzeć trafienia i dopiero wtedy podmieniać.

## Przez granice języków

Najczęstsze pytanie w tym repozytorium brzmi: „gdzie jest druga strona tego kształtu danych”.
Odpowiedź prawie zawsze prowadzi przez kontrakt:

```bash
rg -n '"name": "AiPrompt"' shared/contract.json     # deklaracja
rg --type go 'AiPrompt' -n server/                  # strona Go
rg --type ts 'AiPrompt' -n client/                  # strona TypeScript
```

Zaczynanie od kontraktu, a nie od jednej ze stron, oszczędza czytania: kontrakt jest krótki
i mówi wprost, co po drugiej stronie ma się znaleźć.

## Przez historię git

**Rozmiar obszaru, zanim go otworzysz**

```bash
tokei server/internal/session    # linie kodu, komentarzy i pustych, wg języka
fd -e go . server/internal | wc -l
```

**Od kiedy to tak wygląda**

```bash
git log --oneline -15 -- server/internal/session/
git log -S 'NewManager' --oneline          # commity, w których łańcuch pojawił się lub zniknął
```

`git log -S` jest niedocenianym narzędziem: znajduje moment wprowadzenia nazwy w całej historii,
zwykle szybciej niż czytanie kodu.

**Co zmieniło się od gałęzi odniesienia**

```bash
git diff --stat main...HEAD
git diff --name-only main...HEAD | head -50
git diff main...HEAD | delta     # czytelniejszy podgląd przy przeglądaniu większej zmiany
```

`--stat` przed pełnym diffem to nawyk wart utrwalenia — pokazuje rozkład zmiany, zanim rzuci
w oczy jej treścią.

## Kiedy nic nie znajdujesz

Kolejno, od najtańszego:

1. **Sprawdź nazewnictwo.** Identyfikatory w tym repozytorium są po angielsku, komentarze po
   polsku. Szukanie `sprawa` w kodzie Go zwróci komentarze; szukaj `case`, `matter`, `Sprawa`
   tylko w komentarzach.
2. **Sprawdź, czy to nie jest generowane.** Nazwy z kontraktu nie występują w żadnym pliku
   źródłowym poza `contract.json`.
3. **Sprawdź, czy nie pominąłeś katalogu.** Domyślnie pomijane są `node_modules`, `target`,
   `dist`, `vendor` — słusznie, ale jeśli szukasz czegoś w zależności, trzeba to wyłączyć jawnie.
4. **Cofnij się do mapy.** Jeśli nie wiadomo, w którym obszarze szukać, przeszukiwanie całości
   jest najdroższym możliwym sposobem, żeby się tego dowiedzieć.
