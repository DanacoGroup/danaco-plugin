#!/bin/sh
# Wrapper hooka obowiązku opisu danaco-plugin (POSIX sh): uruchamia hooks/obowiazek_opisu.py
# w trybie "po" (PostToolUse na `opis`) albo "przed" (PreToolUse na Bash, Monitor, `uruchom`
# i zapisie plików). Interpreter szukany jak w po_zapisie.sh; brak skryptu albo Pythona 3.10+
# kończy hook kodem 0 bez decyzji.
KORZEN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SKRYPT="$KORZEN/hooks/obowiazek_opisu.py"
[ -f "$SKRYPT" ] || exit 0
SPRAWDZENIE_WERSJI='import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
for kandydat in python3 python; do
	if command -v "$kandydat" >/dev/null 2>&1 &&
	   "$kandydat" -c "$SPRAWDZENIE_WERSJI" >/dev/null 2>&1; then
		exec "$kandydat" "$SKRYPT" "$1"
	fi
done
exit 0
