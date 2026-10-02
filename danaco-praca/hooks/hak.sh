#!/bin/sh
# Wrapper hooków danaco-praca 5 (POSIX sh): ustala katalog wtyczki i przekazuje zdarzenie
# (stdin) do scripts/hak.py w trybie podanym w argumencie: prompt, narzedzie, stop, sesja.
#
# Interpreter po ścieżce bezwzględnej (/usr/bin/python3), więc podłożony w PATH `python3`
# nie przejmie hooka. Fail-open instalacji: brak interpretera albo skryptu kończy hook
# kodem 0 z komunikatem na stderr — kod 2 przy zdarzeniu Stop zamknąłby sesję w pętli,
# a przy PreToolUse odrzucałby każde narzędzie. Decyzje hook podaje wyłącznie w JSON.
KORZEN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CLAUDE_PLUGIN_ROOT="$KORZEN"
PYTHONDONTWRITEBYTECODE=1
export CLAUDE_PLUGIN_ROOT PYTHONDONTWRITEBYTECODE
PYTHON=/usr/bin/python3
SKRYPT="$KORZEN/scripts/hak.py"
if [ ! -x "$PYTHON" ] || [ ! -f "$SKRYPT" ]; then
	echo "[danaco-praca] brak $PYTHON albo $SKRYPT - hook pominięty" >&2
	exit 0
fi
exec "$PYTHON" "$SKRYPT" "$1"
