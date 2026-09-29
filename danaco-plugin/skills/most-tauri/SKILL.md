---
name: most-tauri
description: >
  Granica między powłoką desktopową Tauri 2 (Rust) a rdzeniem Go w Danaco Console: co jest
  komendą IPC, a co idzie kanałem WebSocket, capabilities domyślnie odmawiające, CSP, cykl
  życia rdzenia jako procesu pobocznego, uzgadnianie portu, pakowanie, podpisywanie i budowa
  krzyżowa pod Windows. Stosuj, gdy zmienia się konfiguracja powłoki lub uprawnień, a także
  gdy pada „aplikacja nie startuje”, „port jest zajęty”, „proces został po zamknięciu okna”,
  „komenda nie odpowiada”, „jak spakować instalator”, „jak podpisać wydanie” albo „jak
  zbudować wersję pod Windows”. Sięgaj po nią przy przeglądzie bezpieczeństwa powierzchni
  Rust i różnicach dev–produkcja. Samą deklarację komendy prowadzi `kontrakt-zrodlo-prawdy`.
---

# Most Tauri ↔ Go

## Kiedy stosować

Stosuj, gdy zmienia się konfiguracja powłoki lub uprawnień, gdy trzeba rozstrzygnąć, czy coś
jest komendą IPC, przy diagnozie startu aplikacji, zajętego portu, procesu-sieroty
i niedziałającej komendy, przy pakowaniu, podpisywaniu i budowie krzyżowej oraz przy
przeglądzie bezpieczeństwa powierzchni Rust.

Nie stosuj tej paczki do zadeklarowania nowej komendy — sekcja `commands` mieszka
w `shared/contract.json`, którym zajmuje się `kontrakt-zrodlo-prawdy`. Transportu, kolejności
i wznowienia komunikatów nie prowadzi ta paczka, lecz `kanal-websocket`; stylu i dostępności
samego widoku — `ui-ux-pro`.

## Podział, który trzeba rozstrzygnąć raz

Aplikacja ma dwie drogi komunikacji między interfejsem a resztą systemu: komendy IPC Tauri
i kanał WebSocket do rdzenia Go. Rozmycie tej granicy jest źródłem większości problemów
z powłoką — logika rozjeżdża się na dwa języki, a testowalność spada, bo warstwa Rust jest
najtrudniejsza do przetestowania i najdroższa do zmiany.

| Idzie komendą Tauri | Idzie kanałem WebSocket |
|---|---|
| rzeczy, które umie tylko system operacyjny: okno, zasobnik, otwarcie katalogu w powłoce | wszystko dziedzinowe: sesje, tryby, dokumenty, tory AI |
| cykl życia samego rdzenia (stan, restart) | stan aplikacji |
| ścieżki systemowe, uprawnienia plikowe | dane |

Test rozstrzygający: **czy to zadziała bez rdzenia Go?** Jeśli nie — nie jest komendą Tauri.
Powierzchnia Rust ma być mała; rosnąca lista komend to sygnał, że logika przecieka z rdzenia
do powłoki.

## Procedura

1. Rozstrzygnij podział z tabeli wyżej. Jeśli rzecz należy do kanału, przejdź do
   `kanal-websocket`.
2. Zadeklaruj komendę w `shared/contract.json` (paczka `kontrakt-zrodlo-prawdy`).
3. Zaimplementuj funkcję `#[tauri::command]` w `desktop/src-tauri/src/`.
4. Dopisz ją do `tauri::generate_handler![...]` — to miejsce, o którym najczęściej się
   zapomina.
5. Zbuduj capabilities od pustego zestawu w górę, na wzorze
   `assets/capabilities.default.json`.
6. Skopiuj narzędzie kontrolne do repozytorium (raz) i uruchom je:
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/most-tauri/scripts/tauri_check.py" tools/
   python3 tools/tauri_check.py --root .
   ```
7. Przed budową instalatora uruchom `task contract:check` oraz ponownie `tauri_check.py`.

`tauri_check.py` sprawdza zgodność trzech miejsc, które muszą mówić to samo, a nie mają
wspólnego kompilatora: sekcji `commands` w `shared/contract.json`, funkcji
`#[tauri::command]` w `desktop/src-tauri/src/**/*.rs` oraz listy w
`tauri::generate_handler![...]`. Komenda napisana i zadeklarowana w kontrakcie, ale nieujęta
w `generate_handler!`, nie istnieje z punktu widzenia interfejsu — i nie zgłasza tego ani
kompilator Rusta, ani TypeScript.

Narzędzie przegląda też konfigurację powłoki: brak CSP i jej osłabienia (`unsafe-eval`,
`unsafe-inline` w skryptach, brak origin IPC w `connect-src`), włączone `withGlobalTauri`,
zakresy z symbolem wieloznacznym, uprawnienia szerokiego dostępu do plików i pozwalające
uruchamiać programy z okna. Komendy w komentarzach pomija.

## Kryteria zakończenia

Zmiana w powłoce jest gotowa, gdy zachodzą wszystkie pięć warunków:

- `python3 tools/tauri_check.py --root .` zwraca `0` — trzy miejsca deklaracji komend
  zgadzają się ze sobą;
- `task contract:check` zwraca `0`;
- capabilities nie zawierają zakresu z `**` ani uprawnienia do uruchamiania programów z okna;
- CSP jest obecna, `connect-src` wymienia origin IPC, a `script-src` nie ma `'unsafe-eval'`
  ani `'unsafe-inline'`;
- zachowanie sprawdzone na **zbudowanym instalatorze**, nie tylko w `tauri dev` — CSP,
  ścieżki i uprawnienia zachowują się inaczej w obu trybach.

## Uprawnienia: domyślnie odmowa

Capabilities w Tauri 2 buduj od pustego zestawu w górę. Wzór minimalnego pliku:
`assets/capabilities.default.json`.

- **Żadnych zakresów z `**`.** Uprawnienie z symbolem wieloznacznym obejmuje więcej, niż
  ktokolwiek zamierzał, i nikt tego nie zauważa, dopóki nie jest za późno.
- **Interfejs nie uruchamia programów.** Rdzeń Go startuje z warstwy Rust, przy starcie
  aplikacji. Uprawnienie pozwalające uruchamiać programy z okna zamienia dowolny błąd
  wstrzyknięcia treści w wykonanie kodu — a ta aplikacja renderuje treść pism.

CSP nie jest formalnością. Powłoka wyświetla dokumenty i pisma, czyli treść pochodzącą
z zewnątrz. Bez polityki bezpieczeństwa dokument z osadzonym skryptem działa w kontekście
aplikacji mającej dostęp do mostu.

Punkt wyjścia: `assets/tauri.conf.fragment.json`. Dwie rzeczy w nim są łatwe do przeoczenia.
`connect-src` musi wymieniać origin IPC (`ipc: http://ipc.localhost`) — bez tego wywołania
komend bywają blokowane, a objaw wygląda jak niedziałająca komenda, nie jak CSP.
`'unsafe-eval'` i `'unsafe-inline'` w `script-src` znoszą ochronę, dla której ta polityka tu
jest; Tauri sam dokłada do niej nonce i skróty przy budowie.

## Cykl życia rdzenia

Gotowa, skompilowana i przetestowana implementacja: `assets/core_process.rs`. Moduł celowo
nie zależy od API Tauri, więc da się go budować i testować bez całego projektu powłoki.

1. Powłoka uruchamia rdzeń z argumentem `--data-dir`.
2. Rdzeń wybiera wolny port i wypisuje na standardowe wyjście jedną linię `PORT=<numer>`.
3. Powłoka czyta tę linię, zapamiętuje port i dopiero wtedy otwiera okno.
4. Przy zamknięciu okna proces rdzenia jest zabijany — również przez `Drop`.

**Uzgadnianie portu jest lepsze od stałego numeru.** Instalacja on-premise potrafi mieć zajęty
każdy port wybrany z góry, a wtedy aplikacja nie wstaje i wygląda to na awarię sieci.

**Proces-sierota jest najczęstszą usterką tej warstwy.** Rdzeń, który przeżył zamknięcie
okna, blokuje port przy następnym starcie — objaw pojawia się przy kolejnym uruchomieniu,
więc nikt nie wiąże go z zamknięciem sprzed godziny. `Drop` w Rust jest tu właściwym
miejscem, bo działa także przy panice.

Szczegóły, w tym zamykanie łagodne i sytuacja, w której rdzeń nie odpowiada:
`references/proces-rdzenia.md`.

## Pakowanie i wydanie

- `bundle.externalBin` musi wymieniać binarium rdzenia, inaczej instalator go nie zawiera,
  a aplikacja u klienta nie ma czego uruchomić.
- Budowa pod Windows z Linuksa:
  `cargo tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc` (cel
  `task windows`). Ta ścieżka daje wyłącznie instalator NSIS, nie MSI, i jest w Tauri
  rozwiązaniem ostatecznym — maszyna wirtualna z Windows albo CI daje wierniejszy wynik.
  Gotowy instalator sprawdzisz w QEMU z KVM albo pod Wine.
- `sccache` i `mold`, jeśli są dostępne, skracają powtórną budowę wielokrotnie; pierwsza
  i tak potrwa.
- Wydanie z rozjechaną granicą trafia na wszystkie stacje naraz, a wycofanie w środowisku
  on-premise jest kosztowne — dlatego kontrola przed budową instalatora jest obowiązkowa.

Podpisywanie i aktualizacje: `references/pakowanie-i-wydanie.md`.

## Częste pułapki

- **Komenda w kontrakcie bez funkcji w Rust** albo odwrotnie. Interfejs wywołuje coś, czego
  nie ma, i dostaje błąd czasu działania zamiast błędu kompilacji. Kontroluje to
  `tauri_check.py`.
- **Komenda pominięta w `generate_handler!`.** Kompiluje się wszystko, nie działa nic.
- **Logika dziedzinowa w Rust.** Najtrudniejsza do przetestowania warstwa w całym
  repozytorium. Jeśli piszesz w Rust coś o sprawach albo dokumentach, to należy do rdzenia
  Go.
- **Stały port.** Działa u autora, zawodzi u klienta z zajętym portem.
- **Brak zabijania rdzenia przy zamknięciu okna.** Objaw pojawia się przy następnym starcie.
- **`withGlobalTauri` włączone „na czas debugowania”.** Zostaje w wydaniu.
- **Różnica dev–produkcja.** W trybie deweloperskim interfejs jedzie z serwera Vite,
  a w wydaniu z zasobów aplikacji. Sprawdź na zbudowanym instalatorze.

## Materiały

- `references/proces-rdzenia.md` — uruchamianie, uzgadnianie portu, nadzór, zamykanie,
  awarie
- `references/pakowanie-i-wydanie.md` — instalator, podpisywanie, budowa krzyżowa,
  aktualizacje
- `references/electron-desktop/electron-desktop.md` — powłoka Electron jako alternatywa;
  Danaco Console używa Tauri 2, więc sięgaj tu tylko przy pracy nad innym produktem Danaco
  albo przy świadomym porównaniu obu podejść
- `assets/core_process.rs` — nadzór nad rdzeniem, z testami, bez zależności od API Tauri
- `assets/capabilities.default.json`, `assets/tauri.conf.fragment.json` — punkt wyjścia
  konfiguracji
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — cele `tauri:check`, `tauri:dev`,
  `tauri:build` i `windows`

## Rozgraniczenie z paczkami sąsiednimi

- `kontrakt-zrodlo-prawdy` — deklaracja komendy w sekcji `commands`. Krok pierwszy.
- `kanal-websocket` — wszystko dziedzinowe, co nie jest komendą IPC.
- `ui-ux-pro` — styl, dostępność i wydajność samego widoku w oknie.
- `praca-w-duzym-repo` — granice pakietu `desktop/src-tauri/` i zasięg zmiany.
