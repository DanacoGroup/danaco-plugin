#!/usr/bin/env python3
"""Hook PreToolUse (Bash): odrzuca polecenia niszczące i wyjście poza repozytorium.

Wejście: JSON zdarzenia na stdin. Wyjście: JSON z permissionDecision "deny" i powodem
dla modelu albo brak wyjścia (exit 0) — wtedy decyduje zwykły przepływ uprawnień.
To „pas” na typową postać polecenia; granicą bezpieczeństwa jest piaskownica.
"""
import json
import re
import sys

WZORCE = [
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*f?\s+(/|~|\$HOME)(\s|$)", "usuwanie katalogu głównego lub domowego"),
    (r"\bgit\s+push\b.*\s(--force|-f)\b", "wymuszony push"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard (utrata zmian)"),
    (r"\bcurl\b[^|]*\|\s*(ba)?sh\b", "pobieranie i wykonywanie skryptu"),
    (r"\b(chmod|chown)\s+-R\s+\S+\s+/(\s|$)", "rekursywna zmiana uprawnień od korzenia"),
]

zdarzenie = json.load(sys.stdin)
polecenie = str((zdarzenie.get("tool_input") or {}).get("command", ""))
for wzorzec, opis in WZORCE:
    if re.search(wzorzec, polecenie):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Zablokowane przez politykę zespołu: {opis}. Zaproponuj bezpieczniejszą alternatywę.",
        }}, ensure_ascii=False))
        sys.exit(0)
sys.exit(0)
