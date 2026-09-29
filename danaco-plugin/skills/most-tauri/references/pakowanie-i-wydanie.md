# Pakowanie, podpisywanie i wydanie — karta

Plik z rozszerzeniem `.fragment` (`assets/tauri.conf.fragment.json`) to wycinek do
wklejenia do pliku już istniejącego w repozytorium, nie plik do skopiowania w całości —
skopiowany jako `tauri.conf.json` usunie pozostałą konfigurację powłoki.

## Co musi znaleźć się w instalatorze

- powłoka Tauri (binarium aplikacji)
- zasoby interfejsu zbudowane przez Vite
- **binarium rdzenia Go** wymienione w `bundle.externalBin`
- ikony, metadane, informacja o wersji

Pominięcie rdzenia w `externalBin` jest najczęstszym błędem pakowania, bo w `tauri dev` wszystko
działa — rdzeń jest wtedy uruchamiany z drzewa roboczego. Objaw pojawia się dopiero na maszynie
klienta i wygląda na awarię uruchomienia bez przyczyny.

## Kontrola przed budową

Instalator z rozjechaną granicą trafia na wszystkie stacje naraz, a wycofanie wydania
w środowisku on-premise oznacza obejście każdej z nich. Dlatego przed `cargo tauri build`:

```bash
task contract:check                    # kontrakt zgodny z kodem
python3 tools/tauri_check.py --root .  # granica Tauri zgodna z kontraktem
task check                             # pełna drabina weryfikacji
```

## Budowa krzyżowa pod Windows

Stacje klienckie w kancelariach bywają windowsowe, maszyna wytwórcza nie musi być.

```bash
cd desktop && cargo tauri build --target x86_64-pc-windows-msvc
```

Do tego `cargo-xwin` i `llvm-mingw`. Gotowy instalator sprawdź w QEMU z KVM (pełny system,
wierny obraz) albo pod Wine (szybciej, mniej wiernie). Rdzeń Go buduj tą samą komendą co zwykle
z `GOOS=windows GOARCH=amd64` i dołóż wynik do `externalBin` dla właściwego celu.

Sprawdź na zbudowanym instalatorze, nie w trybie deweloperskim. Różnice, które wychodzą dopiero
po instalacji: ścieżki zasobów, zachowanie CSP, uprawnienia do katalogu danych, obecność bibliotek
systemowych.

## Podpisywanie

Niepodpisany instalator na Windows wywołuje ostrzeżenie systemu, a w kancelarii oznacza to telefon
do administratora zamiast instalacji. Podpis jest w praktyce warunkiem wdrożenia, nie ozdobą.

Klucze trzymaj poza repozytorium — w zmiennych środowiskowych procesu budowy. Klucz w repozytorium
jest kompromitacją, której nie da się cofnąć: historia git zachowa go także po usunięciu pliku.

## Aktualizacje w środowisku on-premise

Aktualizacje docierają nierównomiernie: część stacji odkłada je tygodniami. Wynikają z tego trzy
rzeczy, które trzeba mieć zaprojektowane wcześniej niż przy pierwszym zgłoszeniu:

- **Bramka skrótu kontraktu** przy otwarciu sesji — powłoka i rdzeń jadą razem w instalatorze,
  ale częściowo nieudana aktualizacja potrafi je rozdzielić. Rozjazd ma dawać jednoznaczny
  komunikat, nie ciche złe zachowanie.
- **Migracje danych muszą znosić przeskok o kilka wersji.** Stacja pomijająca trzy wydania
  ma zastosować trzy migracje po kolei, a nie jedną „najnowszą”.
- **Wersja widoczna w interfejsie.** Przy zgłoszeniu z kancelarii pierwsze pytanie brzmi „jaka
  wersja”, i musi na nie odpowiedzieć użytkownik, a nie administrator z dostępem do plików.

## Lista kontrolna wydania

1. `task contract:check` — kontrakt zgodny z kodem
2. `python3 tools/tauri_check.py --root .` — granica Tauri zgodna z kontraktem
3. `python3 tools/modes_tool.py validate --root .` — macierz trybów bez naruszeń
4. `task check` — pełna drabina, łącznie z bramkami dyscypliny (`mass_actions.py verify`,
   cel `task standard` — patrz `../praca-w-duzym-repo/SKILL.md`)
5. `cargo tauri build` dla każdego celu
6. instalacja i uruchomienie na czystym systemie — nie na maszynie wytwórczej
7. sprawdzenie ścieżki katalogu danych i aktualizacji z poprzedniej wersji
8. podpis i wpis w dzienniku wydań
