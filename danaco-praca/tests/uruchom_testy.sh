#!/bin/sh
# Uruchamia zestaw testów pluginu `danaco-praca` (biblioteka standardowa Pythona,
# bez zależności zewnętrznych). Użycie: sh tests/uruchom_testy.sh [argumenty unittest]
#
# Kandydaci na interpreter: python3, python, py -3 (launcher Windows) - ta sama lista
# co w hooks/straznik.sh. Przed przekazaniem sterowania sprawdzamy wersję: testy
# używają składni `list[str] | None`, więc wymagają Pythona 3.10 lub nowszego.
# Bez tego sprawdzenia `python` wskazujący Pythona 2 dostawał sterowanie bezpowrotnie
# przez `exec`, a użytkownik widział błąd składni zamiast komunikatu o braku
# właściwego interpretera.
#
# Zestaw jest jeden: tests/test_straznik.py - hooki, strażnik, znacznik i zadanie.
# Walidatory dyscypliny i kontrola po zapisie należą do pluginu `danaco-plugin`.
#
# Kody wyjścia: 1 - brak interpretera w wymaganej wersji; w pozostałych przypadkach
# kod zwrócony przez unittest (0 gdy testy przeszły).

set -u

# Testy nie zapisują plików bajtkodu w drzewie pluginu.
PYTHONDONTWRITEBYTECODE=1
export PYTHONDONTWRITEBYTECODE

KATALOG=$(cd "$(dirname "$0")" && pwd)
SPRAWDZENIE_WERSJI='import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'

INTERPRETER=""
INTERPRETER_ARGUMENT=""
for kandydat in python3 python; do
  if command -v "$kandydat" >/dev/null 2>&1 &&
     "$kandydat" -c "$SPRAWDZENIE_WERSJI" >/dev/null 2>&1; then
    INTERPRETER="$kandydat"
    break
  fi
done
if [ -z "$INTERPRETER" ] && command -v py >/dev/null 2>&1 &&
   py -3 -c "$SPRAWDZENIE_WERSJI" >/dev/null 2>&1; then
  INTERPRETER="py"
  INTERPRETER_ARGUMENT="-3"
fi

if [ -z "$INTERPRETER" ]; then
  echo "Brak interpretera Pythona 3.10 lub nowszego (sprawdzono: python3, python, py -3) - nie można uruchomić testów. Zainstaluj Pythona 3 i dodaj go do PATH." >&2
  exit 1
fi

"$INTERPRETER" $INTERPRETER_ARGUMENT -m unittest discover \
  -s "$KATALOG" -t "$KATALOG" -p "test_*.py" "$@"
