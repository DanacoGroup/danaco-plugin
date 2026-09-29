# Rdzeń Go jako proces poboczny powłoki

## Uzgadnianie portu

Rdzeń wybiera wolny port sam i zgłasza go powłoce jedną linią na standardowym wyjściu:

```go
// server/cmd/danaco-console/main.go
ln, err := net.Listen("tcp", "127.0.0.1:0") // 0 = system przydziela wolny port
if err != nil {
    log.Fatalf("nie udalo sie otworzyc gniazda: %v", err)
}
port := ln.Addr().(*net.TCPAddr).Port

// Ta linia jest kontraktem z powloka. Musi byc pierwsza i musi isc na stdout.
fmt.Printf("PORT=%d\n", port)
os.Stdout.Sync()
```

Trzy rzeczy są tu istotne:

- **`127.0.0.1`, nigdy `0.0.0.0`.** Rdzeń ma być osiągalny wyłącznie z tej maszyny. Nasłuch na
  wszystkich interfejsach udostępnia akta sprawy całej sieci kancelarii.
- **Port przydzielany przez system.** Stały numer zawodzi u pierwszego klienta, który ma go zajęty
  — a objaw wygląda jak awaria sieci, nie jak konflikt portów.
- **Dziennik idzie na `stderr`.** Standardowe wyjście jest kanałem uzgodnienia; wymieszanie go
  z dziennikiem sprawia, że powłoka czyta linię dziennika zamiast portu.

## Nadzór

Powłoka trzyma uchwyt do procesu i sprawdza go w tym samym rytmie co heartbeat kanału.
Rozróżnienie dwóch sytuacji jest ważne, bo prowadzą do różnych działań:

| Stan | Objaw | Reakcja |
|---|---|---|
| rdzeń padł | proces zakończony | uruchom ponownie, pokaż informację, zachowaj stan interfejsu |
| rdzeń żyje, nie odpowiada | proces działa, brak odpowiedzi na ping | nie restartuj od razu — może kończyć długą operację |

Automatyczny restart przy braku odpowiedzi jest kuszący i bywa gorszy od problemu: rdzeń
w środku migracji bazy albo długiego zapisu wygląda tak samo jak rdzeń zawieszony.
Restart w takim momencie potrafi zostawić dane w stanie pośrednim.

Ograniczaj też ponowne uruchomienia. Rdzeń, który pada przy starcie z powodu uszkodzonej
konfiguracji, w pętli restartów zapełni dziennik i zamaskuje przyczynę. Trzy próby, potem
komunikat dla użytkownika.

## Zamykanie

Kolejność ma znaczenie:

1. Powłoka wysyła rdzeniowi sygnał zakończenia.
2. Rdzeń domyka sesje (`closing` → `closed`), opróżnia bufory, zapisuje stan.
3. Powłoka czeka określony czas.
4. Po jego upływie zabija proces.

Samo `kill` bez etapu drugiego oznacza utratę niezapisanego stanu sesji przy każdym zamknięciu
aplikacji. Samo czekanie bez etapu czwartego oznacza, że rdzeń, który się zawiesił, blokuje
zamknięcie okna — użytkownik zabija aplikację, a proces zostaje.

`Drop` w `assets/core_process.rs` realizuje wariant awaryjny: działa także wtedy, gdy powłoka
kończy się przez panikę, i to on ratuje przed procesem-sierotą.

## Awarie i ich objawy

| Objaw | Przyczyna |
|---|---|
| aplikacja startuje, okno puste, brak połączenia | rdzeń nie wypisał `PORT=` albo wypisał go na `stderr` |
| „port zajęty” przy drugim uruchomieniu | poprzedni rdzeń nie został zabity przy zamknięciu okna |
| działa w `tauri dev`, nie działa po instalacji | binarium rdzenia nieujęte w `bundle.externalBin` |
| działa u autora, nie u klienta | inna architektura albo brakująca zależność systemowa rdzenia |
| rdzeń startuje i natychmiast kończy | zły `--data-dir`: brak katalogu albo brak praw zapisu |
| restart w pętli | brak ograniczenia liczby prób; przyczyna utonęła w dzienniku |

## Ścieżka katalogu danych

To jedyna ścieżka, którą powłoka przekazuje rdzeniowi — i musi mieć **jedno źródło**. Powłoka zna
katalog danych aplikacji na danym systemie, więc to ona go wyznacza i przekazuje argumentem.

Rdzeń nie wyznacza go samodzielnie. Dwa niezależne wyobrażenia o tym, gdzie leżą dane, objawiają
się jako utrata danych po aktualizacji, a nie jako błąd konfiguracji — użytkownik po prostu widzi
pustą aplikację i swoje sprawy sprzed instalacji nigdzie.

Ta sama uwaga dotyczy komendy `open_data_dir`: otwiera katalog, który powłoka przekazała
rdzeniowi, a nie katalog wyliczony ponownie.
