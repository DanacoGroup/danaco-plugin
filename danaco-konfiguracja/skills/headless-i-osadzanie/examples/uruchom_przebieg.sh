#!/bin/sh
# Przebieg Claude Code w usłudze: jeden dzierżawca, jedna tura, wynik JSON ze sprawdzeniem.
# Użycie: uruchom_przebieg.sh DZIERZAWCA "TREŚĆ PROŚBY" [UUID_SESJI]
#   DZIERZAWCA — identyfikator 1–64 znaki [A-Za-z0-9_-] (katalog konfiguracji i projektu)
# Wymaga: CLAUDE_BIN (przypięta binarka), KATALOG_USLUGI (konfiguracja, katalogi dzierżawców),
#         poświadczenia modelu w środowisku usługi (nie w tym pliku).
set -eu
DZIERZAWCA=$1
PROSBA=$2
SESJA=${3:-}
: "${CLAUDE_BIN:?ustaw CLAUDE_BIN}" "${KATALOG_USLUGI:?ustaw KATALOG_USLUGI}"
case "$DZIERZAWCA" in *[!A-Za-z0-9_-]*|'') echo "zły identyfikator dzierżawcy" >&2; exit 2 ;; esac

KONF="$KATALOG_USLUGI/dzierzawcy/$DZIERZAWCA/konfiguracja"
PRACA="$KATALOG_USLUGI/dzierzawcy/$DZIERZAWCA/praca"
mkdir -p "$KONF" "$PRACA"
if [ -n "$SESJA" ]; then TRYB_SESJI="--resume $SESJA"; else TRYB_SESJI="--session-id $(cat /proc/sys/kernel/random/uuid)"; fi

cd "$PRACA"
# Prompt jako pierwszy argument po -p: flagi wieloargumentowe nie połkną go.
# shellcheck disable=SC2086
WYNIK=$(CLAUDE_CONFIG_DIR="$KONF" CLAUDE_CODE_PROJECT_DIR_NAME="$DZIERZAWCA" \
  CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 DISABLE_AUTOUPDATER=1 CLAUDE_CODE_STARTUP_FAILURE_RESULTS=1 \
  "$CLAUDE_BIN" -p "$PROSBA" --output-format json \
  --setting-sources "" --settings "$KATALOG_USLUGI/wydanie/produkt-czat.flaga.settings.json" \
  --tools "WebSearch,WebFetch" --permission-mode dontAsk --permission-prompts none \
  --disable-slash-commands --max-turns 30 $TRYB_SESJI < /dev/null)  # zamknięte stdin: bez 3 s czekania
printf '%s\n' "$WYNIK" | python3 -c '
import json, sys
w = json.load(sys.stdin)
u = w.get("usage") or {}
print(json.dumps({"sesja": w.get("session_id"), "wynik": w.get("subtype"), "blad": w.get("is_error"),
                  "tekst": (w.get("result") or "")[:500], "odmowy": len(w.get("permission_denials") or []),
                  "cache_odczyt": u.get("cache_read_input_tokens"), "cache_zapis": u.get("cache_creation_input_tokens")},
                 ensure_ascii=False))
sys.exit(1 if w.get("is_error") else 0)'
