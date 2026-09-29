#!/bin/sh
# Wrapper hooków danaco-praca, rejestrowany w hooks/hooks.json pluginu.
#
# Całe rozstrzyganie leży w skryptach Pythona pluginu; wrapper ustala katalog pluginu,
# wyłącza zapis bajtkodu i przekazuje zdarzenie (stdin) skryptowi właściwemu dla trybu.
# Interpreter to zawsze /usr/bin/python3: ścieżka bezwzględna, więc atrapa `python3`
# podłożona w PATH nie przejmie hooka.
#
# Fail-open instalacji: brak interpretera albo skryptu kończy hook kodem 0 z komunikatem
# na stderr. Wywołanie `python3 brakujacy.py` wprost z hooks.json kończyłoby się kodem 2,
# który Claude Code czyta jako blokadę — przy zdarzeniu Stop sesja nie mogłaby zakończyć
# tury, a przy PreToolUse każde narzędzie byłoby odrzucane. Tak samo kończy się `sh`
# (dash) z nieistniejącym plikiem, dlatego polecenia w hooks.json poprzedza
# `[ -f wrapper ] &&`: brak samego wrappera daje kod 1, czyli błąd nieblokujący.
#
# Tryby:
#   stop, prompt, pretool, kompakt, kontrola  scripts/straznik.py (kod 0 przepuszcza, 2 blokuje)
#   sesja                                     scripts/sesja.py (SessionStart, nigdy nie blokuje)
#   sekrety                                   scripts/straz_sekretow.py (PreToolUse Bash,
#                                             decyzja w JSON na stdout)
# Nieznany tryb rozstrzyga strażnik: przy aktywnym zleceniu blokuje (fail-closed).
KORZEN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CLAUDE_PLUGIN_ROOT="$KORZEN"
PYTHONDONTWRITEBYTECODE=1
export CLAUDE_PLUGIN_ROOT PYTHONDONTWRITEBYTECODE
PYTHON=/usr/bin/python3

case "$1" in
sesja) SKRYPT="$KORZEN/scripts/sesja.py" ;;
sekrety) SKRYPT="$KORZEN/scripts/straz_sekretow.py" ;;
*) SKRYPT="$KORZEN/scripts/straznik.py" ;;
esac

if [ ! -x "$PYTHON" ] || [ ! -f "$SKRYPT" ]; then
	# Awaria instalacji nie może zamknąć sesji na stałe: komunikat i przepuszczenie.
	echo "[danaco-praca] brak $PYTHON albo $SKRYPT — hook pominięty" >&2
	exit 0
fi

case "$1" in
sesja)
	# Opis trwającego zlecenia trafia do kontekstu nowej sesji; błędy są wyciszane.
	"$PYTHON" "$SKRYPT" 2>/dev/null
	exit 0
	;;
sekrety)
	exec "$PYTHON" "$SKRYPT"
	;;
*)
	exec "$PYTHON" "$SKRYPT" "$1"
	;;
esac
