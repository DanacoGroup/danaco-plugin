#!/usr/bin/env bash
# Testy wtyczki: unittest (bez sieci). Z CLAUDE_BIN=<binarka claude> dochodzą próby na atrapie API,
# `claude doctor` w walidacji przykładów i `claude plugin validate --strict`.
# Pliki tymczasowe: $TMPDIR. Użycie: tests/uruchom_testy.sh [-k WZORZEC]
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m unittest -v tests.test_wtyczka "$@" 2>&1
