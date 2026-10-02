#!/bin/sh
# Wrapper hooka PostToolUse danaco-plugin (POSIX sh): po zapisie pliku uruchamia
# hooks/po_zapisie.py walidatorem dyscypliny i nazewnictwa.
#
# Interpreter szukany jak w tests/uruchom_testy.sh (python3, python, py -3), bo plugin
# działa też na Windows. Wymagany Python 3.10+ (składnia `list[str] | None`). Fail-open:
# brak skryptu albo interpretera kończy hook kodem 0 — usterka kontroli nie blokuje pracy,
# a w zdarzeniu PostToolUse plik i tak jest już zapisany. Zmienną korzenia czytamy z
# wartością domyślną, więc jej brak nie wywraca hooka (`set -u` nie jest tu włączony).
KORZEN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SKRYPT="$KORZEN/hooks/po_zapisie.py"
[ -f "$SKRYPT" ] || exit 0
SPRAWDZENIE_WERSJI='import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
for kandydat in python3 python; do
	if command -v "$kandydat" >/dev/null 2>&1 &&
	   "$kandydat" -c "$SPRAWDZENIE_WERSJI" >/dev/null 2>&1; then
		exec "$kandydat" "$SKRYPT"
	fi
done
if command -v py >/dev/null 2>&1 && py -3 -c "$SPRAWDZENIE_WERSJI" >/dev/null 2>&1; then
	exec py -3 "$SKRYPT"
fi
exit 0
