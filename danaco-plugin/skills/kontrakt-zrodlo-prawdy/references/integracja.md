# Podpięcie strażnika kontraktu pod codzienną pracę — karta

Plik z rozszerzeniem `.fragment` (`assets/Makefile.fragment`) to wycinek do wklejenia do
pliku już istniejącego w repozytorium, nie plik do skopiowania w całości — skopiowany
jako `Makefile` nadpisze cele, które tam są.

Strażnik, którego trzeba pamiętać uruchomić, nie działa. Poniżej cztery miejsca, w których
kontrola powinna wykonać się sama.

## 0. Instalacja narzędzia

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/scripts/contract_tool.py" install --root .
```

Kopiuje generator do `tools/contract_tool.py`. Wersjonuj go razem z kontraktem — inaczej dwie
osoby wygenerują różny kod z tego samego JSON-a, a strażnik zacznie zgłaszać rozjazd, którego
nikt nie wprowadził.

## 1. Taskfile

Skopiuj `assets/Taskfile.yml` do korzenia repozytorium. Podstawowe cele:

```bash
task contract          # regeneruje kod z kontraktu
task contract:check    # przerywa przy rozjeździe
task check             # pełna drabina: kontrakt, Go, lint, testy, typy TS, Vitest
task --list            # pozostałe cele
```

`assets/Makefile.fragment` daje to samo dla `make`, jeśli wolisz.

**Kolejność wobec `sqlc`, `oapi-codegen` i `mockery`.** Kontrakt idzie pierwszy — jego typy bywają
wejściem dla pozostałych generatorów. Odwrotna kolejność oznacza generowanie na podstawie
nieaktualnych struktur, a wynik wygląda poprawnie i kompiluje się, więc błąd wychodzi dopiero
w działaniu.

**Równoległość.** `Taskfile.yml` wylicza `GO_PAR` z liczby rdzeni maszyny (połowa, nie mniej
niż 2), więc `task go:test` wykorzystuje sprzęt bez zapychania kompilacji i działa tak samo
na stacji deweloperskiej jak na maszynie wydania. Drabina weryfikacji przestaje być wtedy wąskim
gardłem — a to jest warunek tego, żeby faktycznie ją uruchamiać.

## 2. Hak pre-commit

`assets/pre-commit.sample` → `.git/hooks/pre-commit` (i `chmod +x`):

```sh
#!/bin/sh
if git diff --cached --name-only | grep -q '^shared/contract.json$'; then
  python3 tools/contract_tool.py gen --root . || exit 1
  git add shared/contract.go client/src/contract.ts
fi
python3 tools/contract_tool.py check --root . || {
  echo "Kod nie odpowiada kontraktowi. Uruchom: task contract"
  exit 1
}
```

Regeneracja przy zmianie kontraktu i dodanie wyniku do commita usuwa najczęstszy błąd: commit
z nową wersją `contract.json` i starym `contract.go`.

## 3. Test w Go

`assets/contract_test.go` → `shared/contract_test.go`. Sprawdza rzeczy, których generator
z definicji nie sprawdzi, bo sam je wytworzył:

- każdy tryb w `Modes` ma niepusty `Environment`, `Module` i `Isolation`
- `LookupMode` odnajduje każdą stałą trybu
- każdy kod błędu ma niepusty wpis w `ErrorMessages`
- `NewPayload` nie zwraca struktury dla typu spoza kontraktu
- `MessageResponse` wiąże wyłącznie komunikaty klienta z komunikatami z rejestru

Ten test jest tani, a wychwytuje regresje generatora po jego zmianie.

## 4. Test w Vitest

`assets/contract.test.ts` → `client/src/contract.test.ts`. Sprawdza:

- `CONTRACT_HASH` w kliencie zgadza się ze skrótem obliczonym z `shared/contract.json`
- każdy klucz `MODES` należy do `MODE_IDS`
- `MODULES_BY_ENVIRONMENT` pokrywa wszystkie tryby bez duplikatów
- każdy typ komunikatu ma wpis w `MESSAGE_DIRECTION`
- `MESSAGE_RESPONSE` wskazuje komunikaty z rejestru i nigdy nie stoi przy komunikacie rdzenia
- treść błędu pokazywana użytkownikowi nie zawiera własnego kodu (ta sama reguła co w Semgrepie)

Pierwsza asercja jest najważniejsza: łapie sytuację, w której ktoś zmienił kontrakt i zregenerował
tylko stronę Go.

## 5. Wydanie

Do skryptu budującego pakiet Tauri (`cargo tauri build`) dołóż na początku `task gen:check`
i `task tauri:check`. Zbudowanie instalatora z rozjechanym kontraktem oznacza wysłanie usterki
do wszystkich stacji naraz — a w środowisku on-premise wycofanie takiej wersji jest kosztowne.

## Kolejność przy dużej zmianie kontraktu

Gdy zmiana dotyka wielu typów naraz (np. wprowadzenie nowego środowiska z ośmioma modułami),
pracuj w tej kolejności — pozwala rozdzielić błędy kontraktu od błędów kodu:

1. `validate` — sam kontrakt musi być poprawny, zanim cokolwiek wygenerujesz
2. `gen` — regeneracja
3. `go build ./...` — kompilator wskazuje miejsca w rdzeniu wymagające uzupełnienia
4. `npx tsc --noEmit` — to samo po stronie interfejsu
5. dopiero teraz uzupełniaj logikę, plik po pliku, według listy z kompilatorów

Odwrotna kolejność (najpierw kod, potem kontrakt) sprawia, że kompilator zgłasza dziesiątki
błędów o nakładających się przyczynach i trudno odróżnić, które wynikają z niedokończonej
zmiany, a które z faktycznej pomyłki.
