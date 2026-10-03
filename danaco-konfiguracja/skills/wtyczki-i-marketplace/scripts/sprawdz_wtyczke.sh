#!/bin/sh
# Sprawdzenie wtyczki lub marketplace Claude Code bez modelu i bez zmian w konfiguracji konta.
#   1. claude plugin validate --strict (manifest, ścieżki, MCP, ostrzeżenia jako błędy)
#   2. claude plugin details przez --plugin-dir (inwentarz, koszt tokenów stały i przy wywołaniu)
#   3. sesja -p na atrapie API (proba_cli.py): system/init — wtyczki, skille, agenci, MCP, błędy wtyczek
# Wszystko w odizolowanym CLAUDE_CONFIG_DIR w $TMPDIR.
# Użycie: sh sprawdz_wtyczke.sh KATALOG_WTYCZKI_LUB_MARKETPLACE [ścieżka do claude]
set -u
CEL=${1:?podaj katalog wtyczki albo marketplace}
CLI=${2:-${CLAUDE_BIN:-$(command -v claude)}}
TU=$(cd "$(dirname "$0")" && pwd)
KORZEN=$(cd "$TU/../../.." && pwd)
BAZA=$(mktemp -d "${TMPDIR:-/tmp}/wtyczka-XXXXXX")
mkdir -p "$BAZA/profil" "$BAZA/dom"
SRODOWISKO="HOME=$BAZA/dom PATH=/usr/bin:/bin CLAUDE_CONFIG_DIR=$BAZA/profil CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1"
kod=0
echo "== 1. claude plugin validate --strict $CEL"
env -i $SRODOWISKO "$CLI" plugin validate "$CEL" --strict || kod=1
if [ -f "$CEL/.claude-plugin/plugin.json" ] || [ -d "$CEL/skills" ] || [ -f "$CEL/SKILL.md" ]; then
  NAZWA=$(python3 -c "import json,sys,os; p=os.path.join(sys.argv[1],'.claude-plugin','plugin.json'); print(json.load(open(p))['name'] if os.path.exists(p) else os.path.basename(os.path.abspath(sys.argv[1])))" "$CEL")
  echo "== 2. claude plugin details $NAZWA (--plugin-dir)"
  env -i $SRODOWISKO "$CLI" --plugin-dir "$CEL" plugin details "$NAZWA" || kod=1
  echo "== 3. sesja -p na atrapie API"
  TMPDIR="$BAZA" python3 "$KORZEN/scripts/proba_cli.py" --cli "$CLI" --nazwa sesja --json -- --permission-mode dontAsk --plugin-dir "$CEL" \
    | python3 -c "
import json, sys
r = json.load(sys.stdin); i = r.get('init') or {}
n = sys.argv[1]
print('wtyczki:', [p.get('source') for p in i.get('plugins', [])])
print('skille wtyczki:', [s for s in i.get('skills', []) if s.startswith(n + ':')])
print('agenci wtyczki:', [a for a in i.get('agents', []) if a.startswith(n + ':')])
print('MCP wtyczki:', [(s.get('name'), s.get('status')) for s in i.get('mcp_servers', []) if n in s.get('name', '')])
print('błędy wtyczek:', i.get('plugin_errors') or 'brak')
if r.get('stderr'): print('stderr:', r['stderr'][:300])
" "$NAZWA"
fi
echo "(katalog próby: $BAZA)"
exit $kod
