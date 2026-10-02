#!/bin/sh
# Cały zestaw automatyczny danaco-praca: testy hooków (unittest), wbudowane przypadki
# straży sekretów i dysku oraz walidacja wtyczki klientem Claude Code (gdy jest dostępny).
set -e
cd "$(dirname "$0")/.."
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest -v tests.test_hooki 2>&1 | tail -n 4
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 scripts/straz_sekretow.py --test | tail -n 1
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 scripts/straz_dysku.py --test | tail -n 1
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo /danaco/uslugi/claude/bin/claude)}"
if [ -x "$CLAUDE_BIN" ]; then
	"$CLAUDE_BIN" plugin validate --strict .
fi
