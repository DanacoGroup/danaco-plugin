#!/bin/sh
# Uruchamia caly zestaw testow pluginu (biblioteka standardowa Pythona,
# bez zależności zewnętrznych). Użycie: sh tests/uruchom_testy.sh [argumenty unittest]
#
# Kandydaci na interpreter: python3, python, py -3 (launcher Windows) - ta sama lista
# co w hooks/po_zapisie.sh. Przed przekazaniem sterowania sprawdzamy wersję: testy
# używają składni `list[str] | None`, więc wymagają Pythona 3.10 lub nowszego.
# Bez tego sprawdzenia `python` wskazujący Pythona 2 dostawał sterowanie bezpowrotnie
# przez `exec`, a użytkownik widział błąd składni zamiast komunikatu o braku
# właściwego interpretera.
#
# Kody wyjścia: 1 - brak interpretera w wymaganej wersji; w pozostałych przypadkach
# kod zwrócony przez unittest (0 gdy testy przeszły).

set -u

# Testy nie zapisuja plikow bajtkodu w drzewie pluginu.
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

# Dwa zestawy: testy wspolne pluginu (tests/, biblioteka standardowa) oraz testy skryptow
# paczki ui-ux-pro (pytest). Kod wyjscia jest niezerowy, gdy zawiodl ktorykolwiek zestaw.
PACZKA_UI="$KATALOG/../skills/ui-ux-pro/scripts/tests"
KOD=0

uruchom() {
  katalog_startowy="$1"
  if [ ! -d "$katalog_startowy" ]; then
    echo "Pominieto: katalog $katalog_startowy nie istnieje." >&2
    return 0
  fi
  if [ -n "$INTERPRETER_ARGUMENT" ]; then
    "$INTERPRETER" "$INTERPRETER_ARGUMENT" -m unittest discover \
      -s "$katalog_startowy" -t "$katalog_startowy" -p "test_*.py" "$@"
  else
    "$INTERPRETER" -m unittest discover \
      -s "$katalog_startowy" -t "$katalog_startowy" -p "test_*.py" "$@"
  fi
}

uruchom "$KATALOG" "$@" || KOD=1

# Testy paczki ui-ux-pro sa napisane pod pytest (fixtures), wiec unittest ich nie zbierze.
# Bez pytest w srodowisku zestaw jest pomijany z komunikatem, nie po cichu.
if [ -d "$PACZKA_UI" ]; then
  if "$INTERPRETER" $INTERPRETER_ARGUMENT -c "import pytest" >/dev/null 2>&1; then
    "$INTERPRETER" $INTERPRETER_ARGUMENT -m pytest -q "$PACZKA_UI" || KOD=1
  else
    echo "Pominieto testy paczki ui-ux-pro: brak pytest. Instalacja: pip install -r skills/ui-ux-pro/scripts/tests/requirements.txt" >&2
  fi
fi

exit "$KOD"
