#!/usr/bin/env python3
"""Hook PostToolUse wtyczki: formatuje edytowany plik .py wybranym formaterem (błąd nie blokuje)."""
import json
import shutil
import subprocess
import sys

formater = sys.argv[1] if len(sys.argv) > 1 else "ruff"
zdarzenie = json.load(sys.stdin)
sciezka = str((zdarzenie.get("tool_input") or {}).get("file_path", ""))
if not sciezka.endswith(".py") or formater == "brak" or not shutil.which(formater):
    sys.exit(0)
polecenie = [formater, "format", "--quiet", sciezka] if formater == "ruff" else [formater, "--quiet", sciezka]
subprocess.run(polecenie, capture_output=True, timeout=25)
sys.exit(0)
