# PowerShell i CMD — karta

## Procedury podstawowe

Na stacjach Danaco domyślną powłoką Windows jest PowerShell. Rozróżniaj Windows PowerShell 5.1
(`powershell.exe`, wbudowany w system) i PowerShell 7+ (`pwsh.exe`, instalowany osobno). Wersję
sprawdzaj przed użyciem funkcji nowszej składni:
```powershell
$PSVersionTable.PSVersion
```

**Składnia.** Polecenia PowerShell to cmdlety w konwencji Czasownik-Rzeczownik (`Get-ChildItem`,
`Set-Location`, `Copy-Item`). Parametry poprzedzaj myślnikiem, wartości podawaj po spacji:
```powershell
Get-ChildItem -Path C:\Projekty -Recurse -Filter *.log
Copy-Item -Path .\dane.csv -Destination D:\Kopie\ -Force
```

**Potok obiektów.** PowerShell przekazuje potokiem obiekty .NET, nie tekst. Filtruj i przekształcaj
właściwościami obiektów, a nie wycinaniem łańcuchów:
```powershell
Get-Process | Where-Object { $_.WorkingSet64 -gt 500MB } |
    Sort-Object WorkingSet64 -Descending |
    Select-Object Name, Id, WorkingSet64
```
Nazwy właściwości obiektu odczytuj poleceniem `Get-Member`, a nie zgaduj.

**Obsługa błędów.** Rozróżniaj błędy kończące (przerywają wykonanie) i niekończące (domyślnie tylko
sygnalizowane). Aby `try/catch` przechwytywał również błędy niekończące, wymuś ich eskalację:
```powershell
$ErrorActionPreference = 'Stop'
try {
    Invoke-WebRequest -Uri $adres -OutFile $plik
}
catch {
    Write-Error "Pobieranie nie powiodło się: $($_.Exception.Message)"
    exit 1
}
```
W skryptach wywołujących programy zewnętrzne (git, npm, docker) sprawdzaj `$LASTEXITCODE` po każdym
wywołaniu — `try/catch` nie reaguje na niezerowy kod wyjścia programu natywnego.

**Różnice PowerShell vs CMD.** Nie mieszaj składni obu powłok:
- CMD: `%ZMIENNA%`, `set ZMIENNA=wartosc`, `dir`, `del`, łączenie poleceń `&&`.
- PowerShell: `$env:ZMIENNA`, `$env:ZMIENNA = 'wartosc'`, `Get-ChildItem`, `Remove-Item`; operatory `&&` i `||` działają dopiero od PowerShell 7 — w Windows PowerShell 5.1 rozdzielaj polecenia średnikiem i sprawdzaj `$LASTEXITCODE`.
- Skrypty `.bat`/`.cmd` uruchamiaj w CMD lub przez `cmd /c`; skrypty `.ps1` — wyłącznie w
  PowerShell.

Przykład tej samej operacji w obu powłokach:
```
CMD:        set NODE_ENV=production && node app.js
PowerShell: $env:NODE_ENV = 'production'; node app.js
```

## Bezpieczne wzorce

- **ExecutionPolicy.** Zasady wykonywania nie zmieniaj globalnie. Gdy uruchomienie skryptu jest
  blokowane, stosuj zakres procesu:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  ```
  Zmianę na poziomie maszyny (`-Scope LocalMachine`) pozostaw administratorowi.
- **Cudzysłowy.** Apostrofy (`'...'`) oznaczają łańcuch dosłowny; cudzysłowy (`"..."`) interpolują
  zmienne i wyrażenia `$(...)`. Do łańcuchów z danymi używaj apostrofów, interpolację stosuj
  świadomie. Znak ucieczki to grawis (`` ` ``), nie ukośnik wsteczny; znak `$` w cudzysłowach
  zapisuj jako `` `$ ``, jeżeli ma być dosłowny.
- **Ścieżki ze spacjami.** Ścieżki typu `C:\Program Files\...` zawsze ujmuj w cudzysłowy lub
  apostrofy. Wykonanie pliku wskazanego łańcuchem wymaga operatora wywołania:
  ```powershell
  & 'C:\Program Files\Narzedzie\narzedzie.exe' --parametr wartosc
  ```
- **Budowanie ścieżek.** Łącz segmenty poleceniem `Join-Path`, nie konkatenacją łańcuchów;
  separatorem w Windows jest `\`, lecz PowerShell akceptuje również `/`.
- **Argumenty przekazywane dalej.** Przy wywołaniach programów natywnych z argumentami zawierającymi
  spacje lub cudzysłowy testuj wywołanie na danych nieszkodliwych; zachowanie cytowania różni się
  między PowerShell 5.1 a 7.
- **Nie wklejaj sekretów do poleceń.** Trafiają do historii sesji i transkrypcji. Odczytuj je ze
  zmiennych środowiskowych lub magazynu sekretów.

## Diagnostyka

- **`$Error`.** Automatyczna tablica ostatnich błędów sesji; `$Error[0]` to błąd najnowszy. Pełne
  szczegóły wyświetla:
  ```powershell
  $Error[0] | Format-List * -Force
  ```
  W PowerShell 7 dodatkowo `Get-Error` prezentuje błąd w formie rozwiniętej.
- **Przebieg próbny.** Cmdlety modyfikujące stan obsługują parametry wspólne `-WhatIf` (pokazuje
  skutki bez wykonania) i `-Confirm` (żąda potwierdzenia). Przed każdą operacją masową na plikach
  wykonaj wariant z `-WhatIf` i przeczytaj wynik:
  ```powershell
  Remove-Item -Path .\tmp\* -Recurse -WhatIf
  ```
- **Transkrypcja.** Rejestruj przebieg sesji diagnostycznej do pliku:
  ```powershell
  Start-Transcript -Path C:\Logi\sesja.txt
  Stop-Transcript
  ```
- **Śledzenie skryptu.** `Set-PSDebug -Trace 1` wypisuje wykonywane wiersze; wyłącz po diagnozie
  poleceniem `Set-PSDebug -Off`.
- **Weryfikacja poleceń i modułów.** `Get-Command nazwa` potwierdza istnienie polecenia i wskazuje
  moduł; `Get-Help nazwa -Full` opisuje parametry. Sprawdzaj zamiast zakładać, że cmdlet istnieje w
  danej wersji PowerShell.

## Operacje nieodwracalne — wymagają zgody właściciela projektu

Nie wykonuj poniższych poleceń bez wyraźnej zgody właściciela projektu udzielonej dla konkretnego
przypadku:

- `Remove-Item -Recurse -Force` — trwale usuwa katalog wraz z zawartością, z pominięciem atrybutów
  tylko-do-odczytu i bez kosza systemowego. Skierowane na złą ścieżkę (np. wskutek pustej zmiennej w
  ścieżce) potrafi usunąć katalog nadrzędny projektu. Zawsze poprzedzaj wariantem z `-WhatIf` i
  sprawdzeniem, że zmienne w ścieżce nie są puste.
- `del /s /q` oraz `rmdir /s /q` w CMD — odpowiedniki powyższego, bez pytania o potwierdzenie.
- `Format-Volume`, `Clear-Disk` — nieodwracalnie niszczą dane woluminu lub dysku.
- `Stop-Process -Force` na procesach nienależących do bieżącego zadania — może przerwać pracę
  użytkownika i uszkodzić otwarte pliki.
- `Set-ExecutionPolicy` w zakresie `LocalMachine`, modyfikacje rejestru (`Set-ItemProperty` w
  gałęziach `HKLM:`) oraz zmiany systemowych zmiennych środowiskowych — zmieniają konfigurację całej
  maszyny, nie tylko projektu.
- `Remove-ItemProperty`, `Unregister-ScheduledTask` i pokrewne operacje usuwające konfigurację
  systemową.

## Typowe błędy modeli LLM przy tym narzędziu

1. **Składnia bash w PowerShell.** Konstrukcje `export ZMIENNA=...`, `rm -rf`, `ls -la`, `which`,
   `$(cat plik)` nie są składnią PowerShell albo działają inaczej, niż model zakłada. Używaj
   `$env:ZMIENNA = '...'`, `Remove-Item`, `Get-ChildItem`, `Get-Command`, `Get-Content`.
2. **Użycie `&&` w Windows PowerShell 5.1.** Operator dostępny dopiero od PowerShell 7; w 5.1
   powoduje błąd składni. Rozdzielaj polecenia średnikiem i sprawdzaj `$LASTEXITCODE`, albo jawnie
   uruchamiaj `pwsh`.
3. **Aliasy w skryptach.** `ls`, `cd`, `cat`, `curl` to aliasy o zachowaniu zależnym od wersji (w
   PowerShell 5.1 `curl` wskazuje `Invoke-WebRequest`, nie program curl). W skryptach zapisuj pełne
   nazwy cmdletów; program curl wywołuj jako `curl.exe`.
4. **Łamanie ścieżek ze spacjami.** Wywołanie `C:\Program Files\App\app.exe` bez cudzysłowów i
   operatora `&` kończy się błędem lub uruchomieniem niewłaściwego pliku. Ujmuj ścieżkę w cudzysłowy
   i poprzedzaj operatorem `&`.
5. **Założenie, że `try/catch` przechwyci każdy błąd.** Błędy niekończące i niezerowe kody wyjścia
   programów natywnych nie trafiają do `catch`. Ustawiaj `$ErrorActionPreference = 'Stop'` (lub
   `-ErrorAction Stop`) i sprawdzaj `$LASTEXITCODE`.
6. **Traktowanie potoku jak strumienia tekstu.** Parsowanie wyników `Get-Process` czy
   `Get-ChildItem` wyrażeniami tekstowymi zamiast pracy na właściwościach obiektów jest kruche.
   Filtruj przez `Where-Object`, wybieraj przez `Select-Object`.
7. **Mieszanie składni CMD i PowerShell w jednym poleceniu.** `%PATH%` w PowerShell nie jest
   interpolowane, `set` tworzy co innego niż w CMD. Ustal powłokę docelową i trzymaj się jej składni
   w całym skrypcie.
8. **Kasowanie z `-Force` bez przebiegu próbnego.** Model „sprząta” katalogi jednym poleceniem bez
   weryfikacji ścieżki. Najpierw `-WhatIf` lub `Get-ChildItem` na tej samej ścieżce, potem — po
   zgodzie — usuwanie.
9. **Porównania do `$null` po niewłaściwej stronie.** W porównaniach z kolekcjami pisz `$null -eq
   $zmienna` (stała po lewej); zapis odwrotny filtruje kolekcję zamiast testować jej istnienie.
10. **Wymyślanie cmdletów i parametrów.** Model podaje nieistniejące polecenia lub parametry z innej
    wersji modułu. Przed użyciem nieoczywistego cmdletu potwierdź go przez `Get-Command` i
    `Get-Help`.
