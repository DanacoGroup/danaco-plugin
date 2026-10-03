#!/usr/bin/env python3
"""Lint reguł uprawnień Claude Code (z pliku ustawień albo podanych w wierszu poleceń).

Sprawdza: składnię `Narzędzie(specyfikator)`, nazwy narzędzi, reguły pomijane przez CLI
(`mcp__…(…)` w pliku, glob w allow, dopasowanie po głównym polu), `:*` w środku wzorca,
gwiazdkę przed podpoleceniem, reguły ścieżek dla Write/Glob/NotebookEdit, kotwice ścieżek
(`/` = źródło ustawień, `//` = korzeń), konflikty allow/deny.

Użycie:
  sprawdz_reguly.py --plik settings.json
  sprawdz_reguly.py --allow "Bash(git *)" --deny "Read(/etc/passwd)" --ask "Bash(git push *)"
Kod wyjścia: 1, gdy jest choć jeden błąd.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402
import waliduj_ustawienia as w  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plik", type=Path)
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--ask", action="append", default=[])
    parser.add_argument("--deny", action="append", default=[])
    a = parser.parse_args()
    uprawnienia = {"allow": list(a.allow), "ask": list(a.ask), "deny": list(a.deny)}
    if a.plik:
        dane = cc.czytaj_json(a.plik)
        for lista in uprawnienia:
            uprawnienia[lista] += list((dane.get("permissions") or {}).get(lista, []) or [])
    if not any(uprawnienia.values()):
        parser.error("brak reguł do sprawdzenia")
    raport = w.Raport(str(a.plik or "wiersz poleceń"))
    w.sprawdz_uprawnienia({"permissions": uprawnienia}, raport)
    for lista, reguly in uprawnienia.items():
        print(f"{lista}: {len(reguly)} reguł")
    for b in raport.bledy:
        print(f"  BŁĄD  {b}")
    for o in raport.ostrzezenia:
        print(f"  OSTRZ {o}")
    for u in raport.uwagi:
        print(f"  uwaga {u}")
    if not (raport.bledy or raport.ostrzezenia or raport.uwagi):
        print("  bez uwag")
    print("Pamiętaj: reguły Bash dopasowują tekst polecenia — granicą jest piaskownica, nie reguła.")
    return 1 if raport.bledy else 0


if __name__ == "__main__":
    sys.exit(main())
