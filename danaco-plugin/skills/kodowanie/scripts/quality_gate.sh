#!/usr/bin/env sh
# Bramka jakości budowy (quality_gate.sh).
#
# Wykrywa rodzaj projektu po plikach znacznikowych (go.mod, package.json,
# Cargo.toml, requirements.txt/pyproject.toml) i uruchamia dla każdego
# odpowiednie polecenia budowy/lintu/testów, jeśli narzędzie jest zainstalowane.
# Brakujące narzędzie jest pomijane z ostrzeżeniem, a nie fatalnym błędem -
# repozytorium hybrydowe (Go + TypeScript + Rust) rzadko ma wszystkie trzy
# łańcuchy narzędzi na każdej maszynie deweloperskiej.
#
# POSIX sh, nie bash: orkiestrator (scripts/mass_actions.py) uruchamia bramkę
# powłoką znalezioną na maszynie (bash albo sh), a na Alpine i w minimalnych
# obrazach CI basha nie ma. Z tego samego powodu nie ma tu `set -o pipefail`,
# którego dash nie zna.
#
# Interpreter Pythona szukany jest tą samą listą co w hooks/po_zapisie.sh
# (python3, python, py -3), bo na Windows `python3` często nie istnieje.
#
# Użycie: ./quality_gate.sh [katalog]
# Kod wyjścia: 0 gdy wszystkie uruchomione kroki przeszły, 1 gdy co najmniej
# jeden krok zawiódł, 4 gdy nie rozpoznano projektu ani nie ma czego uruchomić.

set -u

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "Użycie: $0 [katalog]"
  echo "Wykrywa rodzaj projektu (go.mod / package.json / Cargo.toml / requirements.txt)"
  echo "i uruchamia dla niego build/vet/lint/test. Domyślny katalog: bieżący."
  exit 0
fi

KATALOG="${1:-.}"
cd "$KATALOG" || { echo "brak katalogu: $KATALOG" >&2; exit 4; }

BLAD=0
KROK=0

uruchom() {
  opis="$1"
  shift
  KROK=$((KROK + 1))
  echo "== [$KROK] $opis =="
  if "$@"; then
    echo "-- OK: $opis"
  else
    echo "-- BŁĄD: $opis" >&2
    BLAD=1
  fi
}

pominieto() {
  echo "-- pominięto: $1 (narzędzie niedostępne)"
}

if [ -f go.mod ]; then
  if command -v go >/dev/null 2>&1; then
    uruchom "go build ./..." go build ./...
    uruchom "go vet ./..." go vet ./...
    uruchom "go test -race ./..." go test -race ./...
    if command -v gofmt >/dev/null 2>&1; then
      NIEFORMATOWANE=$(gofmt -l . 2>/dev/null | grep -v vendor || true)
      if [ -n "$NIEFORMATOWANE" ]; then
        echo "-- BŁĄD: gofmt zgłasza niesformatowane pliki:" >&2
        echo "$NIEFORMATOWANE" >&2
        BLAD=1
      else
        echo "-- OK: gofmt"
      fi
    fi
  else
    pominieto "go build/vet/test"
  fi
fi

if [ -f package.json ]; then
  if command -v npx >/dev/null 2>&1; then
    if [ -f tsconfig.json ]; then
      uruchom "tsc --noEmit" npx tsc --noEmit
    fi
    if grep -q '"test"' package.json 2>/dev/null && command -v npm >/dev/null 2>&1; then
      uruchom "npm test" npm test --silent
    fi
  else
    pominieto "tsc/npm test"
  fi
fi

if [ -f Cargo.toml ]; then
  if command -v cargo >/dev/null 2>&1; then
    uruchom "cargo build" cargo build
    uruchom "cargo clippy --all-targets" cargo clippy --all-targets -- -D warnings
    uruchom "cargo test" cargo test
  else
    pominieto "cargo build/clippy/test"
  fi
fi

PYTHON=""
PYTHON_ARGUMENT=""
for kandydat in python3 python; do
  if command -v "$kandydat" >/dev/null 2>&1 &&
     "$kandydat" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    PYTHON="$kandydat"
    break
  fi
done
if [ -z "$PYTHON" ] && command -v py >/dev/null 2>&1 &&
   py -3 -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
  PYTHON="py"
  PYTHON_ARGUMENT="-3"
fi

PROJEKT_PYTHON=0
if [ -f requirements.txt ] || [ -f pyproject.toml ]; then
  PROJEKT_PYTHON=1
  if [ -n "$PYTHON" ]; then
    if [ -d tests ] || [ -d test ]; then
      if "$PYTHON" $PYTHON_ARGUMENT -c "import pytest" >/dev/null 2>&1; then
        uruchom "pytest" "$PYTHON" $PYTHON_ARGUMENT -m pytest -q
      else
        pominieto "pytest (moduł niezainstalowany)"
      fi
    else
      echo "-- projekt Python wykryty (requirements.txt/pyproject.toml), ale brak katalogu tests/ lub test/ - nic do uruchomienia"
    fi
  else
    pominieto "pytest (brak interpretera Pythona 3)"
  fi
fi

echo
if [ "$KROK" -eq 0 ]; then
  if [ "$PROJEKT_PYTHON" -eq 1 ]; then
    echo "Projekt Python rozpoznany w $KATALOG, ale nie znaleziono żadnego kroku do uruchomienia (brak tests/, test/ albo pytest)."
  else
    echo "Nie znaleziono żadnego rozpoznawanego projektu (go.mod / package.json / Cargo.toml / requirements.txt) w $KATALOG."
  fi
  exit 4
fi

if [ "$BLAD" -eq 0 ]; then
  echo "Bramka jakości: WSZYSTKO PRZESZŁO ($KROK kroków)."
else
  echo "Bramka jakości: SĄ BŁĘDY - patrz wyżej." >&2
fi

exit "$BLAD"
