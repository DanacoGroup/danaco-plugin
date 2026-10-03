#!/usr/bin/env python3
"""Hook Stop: nie pozwala zakończyć tury, dopóki istnieje plik-znacznik niedokończonej pracy.

Pętla jest chroniona polem stop_hook_active: gdy hook już raz zablokował zakończenie,
drugi raz pozwala (CLI i tak przerywa po 8 kolejnych blokadach). Znacznik:
$CLAUDE_PROJECT_DIR/.do-zrobienia (dowolna treść = lista otwartych punktów).
"""
import json
import os
import sys
from pathlib import Path

zdarzenie = json.load(sys.stdin)
if zdarzenie.get("stop_hook_active"):
    sys.exit(0)
znacznik = Path(os.environ.get("CLAUDE_PROJECT_DIR", zdarzenie.get("cwd", "."))) / ".do-zrobienia"
if znacznik.is_file():
    otwarte = znacznik.read_text(encoding="utf-8").strip()[:500]
    print(json.dumps({"decision": "block",
                      "reason": f"Zostały otwarte punkty (plik .do-zrobienia): {otwarte}. Dokończ je albo usuń plik, "
                                f"jeśli praca jest skończona."}, ensure_ascii=False))
sys.exit(0)
