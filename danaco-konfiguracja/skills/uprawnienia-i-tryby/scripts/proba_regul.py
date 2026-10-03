#!/usr/bin/env python3
"""Próba: czy dane wywołanie narzędzia przejdzie przy danych ustawieniach i trybie.

Atrapa API (scripts/atrapa_api.py) zleca jedno wywołanie (`Bash` z poleceniem albo dowolne
narzędzie z wejściem JSON), CLI ocenia je według reguł, hooków i trybu, a skrypt podaje
wynik: WYKONANE albo ODRZUCONE z komunikatem. Nie używa modelu ani konta.

Użycie:
  proba_regul.py --bash "git push origin main" [--settings plik.json] [--tryb dontAsk]
  proba_regul.py --narzedzie Write --wejscie '{"file_path":"a.txt","content":"x"}' --tryb acceptEdits
  proba_regul.py --bash "touch a" -- --allowed-tools "Bash(touch *)"   # dodatkowe flagi CLI po --

Uwaga: katalog roboczy próby leży w $TMPDIR (poza `.claude/`, bo tam każdy zapis jest
zapisem do ścieżki chronionej). Polecenie wykonuje się naprawdę w katalogu próby —
nie podawaj poleceń niszczących spoza niego.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]


def main() -> int:
    if "--" in sys.argv:
        i = sys.argv.index("--")
        wlasne, dodatkowe = sys.argv[1:i], sys.argv[i + 1:]
    else:
        wlasne, dodatkowe = sys.argv[1:], []
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bash")
    parser.add_argument("--narzedzie")
    parser.add_argument("--wejscie", default="{}")
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--tryb", default="dontAsk")
    parser.add_argument("--cli", default=os.environ.get("CLAUDE_BIN", ""))
    a = parser.parse_args(wlasne)
    if not (a.bash or a.narzedzie):
        parser.error("podaj --bash albo --narzedzie")
    krok = ({"narzedzie": "Bash", "wejscie": {"command": a.bash, "description": "próba reguły"}} if a.bash
            else {"narzedzie": a.narzedzie, "wejscie": json.loads(a.wejscie)})
    katalog = Path(tempfile.mkdtemp(prefix="proba-regul-"))
    scenariusz = katalog / "scenariusz.json"
    scenariusz.write_text(json.dumps([krok, {"tekst": "koniec"}], ensure_ascii=False))
    polecenie = [sys.executable, str(KORZEN / "scripts" / "proba_cli.py"), "--json", "--katalog", str(katalog / "p"),
                 "--scenariusz", str(scenariusz)]
    if a.cli:
        polecenie += ["--cli", a.cli]
    polecenie += ["--", "--permission-mode", a.tryb]
    if a.settings:
        polecenie += ["--settings", str(a.settings.resolve())]
    polecenie += dodatkowe
    wynik = subprocess.run(polecenie, capture_output=True, text=True)
    try:
        raport = json.loads(wynik.stdout)
    except json.JSONDecodeError:
        print(wynik.stdout, wynik.stderr)
        return 2
    odmowy = (raport.get("wynik") or {}).get("permission_denials") or []
    wyniki = [t for t in raport.get("teksty", []) if t.startswith("[tool_result")]
    print(f"Tryb: {(raport.get('init') or {}).get('permissionMode')}  wywołanie: {json.dumps(krok, ensure_ascii=False)}")
    if raport.get("stderr"):
        print(f"stderr CLI: {raport['stderr']}")
    if odmowy or any("BŁĄD" in t for t in wyniki):
        print("ODRZUCONE")
    else:
        print("WYKONANE")
    for t in wyniki:
        print(f"  {t}")
    print(f"(katalog próby: {katalog})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
