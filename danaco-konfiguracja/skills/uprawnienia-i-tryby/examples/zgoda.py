#!/usr/bin/env python3
"""Hook PermissionRequest: polityka zgód w kodzie (zamiast człowieka).

Zatwierdza polecenia Bash z listy prefiksów, odmawia reszcie z powodem. Odmowa wymaga
obiektu `decision` — exit 2 jest dla tego zdarzenia ignorowany.
"""
import json
import sys

DOZWOLONE = ("touch ", "mkdir -p ", "npm run lint", "npm test")

zdarzenie = json.load(sys.stdin)
narzedzie = zdarzenie.get("tool_name", "")
wejscie = zdarzenie.get("tool_input") or {}
polecenie = str(wejscie.get("command", ""))
if narzedzie == "Bash" and polecenie.startswith(DOZWOLONE):
    decyzja = {"behavior": "allow"}
else:
    decyzja = {"behavior": "deny", "message": f"Polityka zgód nie obejmuje: {narzedzie} {polecenie[:80]}"}
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": decyzja}}))
