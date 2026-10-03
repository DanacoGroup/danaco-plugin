#!/usr/bin/env python3
"""Sprawdza wszystkie przykłady i szablony wtyczki (skills/*/examples, agents, commands).

Reguły według nazwy pliku:
  *.<rodzaj>.settings.json        → waliduj_ustawienia.py --rodzaj <rodzaj> (user/project/local/managed/flaga)
  zarzadzanie-flota/examples/dodatki/*.json, konsola-ladunek.json → jak ustawienia zarządzane
  *.mcp.json, managed-mcp.json    → sprawdz_mcp.py
  *.agents.json, agents/*.md      → sprawdz_agenta.py
  katalog z SKILL.md              → sprawdz_skill.py
  katalog z .claude-plugin/       → claude plugin validate (przy --cli)
  pozostałe *.json                → poprawność JSON
  *.py                            → kompilacja; *.sh → bash -n
Użycie: sprawdz_przyklady.py [--cli claude] [--tylko FRAGMENT_ŚCIEŻKI] [--szczegoly]
Kod wyjścia 1, gdy którykolwiek przykład ma błędy.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[1]
S = KORZEN / "skills"
PY = sys.executable
RODZAJE = {"user", "project", "local", "managed", "flaga"}


def uruchom(polecenie: list[str]) -> tuple[bool, str]:
    try:
        w = subprocess.run(polecenie, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as blad:
        return False, str(blad)
    tekst = (w.stdout + w.stderr).strip()
    return w.returncode == 0, tekst


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cli", default="")
    p.add_argument("--tylko", default="")
    p.add_argument("--szczegoly", action="store_true")
    a = p.parse_args()

    zadania: list[tuple[str, Path, list[str] | None]] = []
    katalogi_skilli: set[Path] = set()
    for przyklady in sorted(S.glob("*/examples")):
        for skill_md in przyklady.rglob("SKILL.md"):
            katalogi_skilli.add(skill_md.parent)
        for plik in sorted(przyklady.rglob("*")):
            if not plik.is_file() or any(k in plik.parents for k in katalogi_skilli):
                continue
            n = plik.name
            czesci = n.split(".")
            if n.endswith(".settings.json") and len(czesci) >= 4 and czesci[-3] in RODZAJE:
                pol = [PY, str(KORZEN / "scripts/waliduj_ustawienia.py"), str(plik), "--rodzaj", czesci[-3]]
                zadania.append(("ustawienia", plik, pol + (["--cli", a.cli] if a.cli else [])))
            elif "zarzadzanie-flota" in plik.parts and n.endswith(".json") and ("dodatki" in plik.parts or n == "konsola-ladunek.json"):
                pol = [PY, str(KORZEN / "scripts/waliduj_ustawienia.py"), str(plik), "--rodzaj", "managed"]
                zadania.append(("ustawienia", plik, pol + (["--cli", a.cli] if a.cli else [])))
            elif n.endswith(".mcp.json") or n == "managed-mcp.json":
                zadania.append(("mcp", plik, [PY, str(S / "serwery-mcp/scripts/sprawdz_mcp.py"), str(plik)]))
            elif n.endswith(".agents.json"):
                zadania.append(("agenci", plik, [PY, str(S / "podagenci-i-zespoly/scripts/sprawdz_agenta.py"), str(plik)]))
            elif plik.parent.name == "agents" and n.endswith(".md"):
                zadania.append(("agenci", plik, [PY, str(S / "podagenci-i-zespoly/scripts/sprawdz_agenta.py"), str(plik)]))
            elif n.endswith(".json"):
                zadania.append(("json", plik, None))
            elif n.endswith(".py"):
                zadania.append(("python", plik, None))
            elif n.endswith(".sh") or (plik.parent.name == "bin" and plik.stat().st_mode & 0o111):
                zadania.append(("powloka", plik, ["bash", "-n", str(plik)]))
    for katalog in sorted(katalogi_skilli):
        if katalog.parent.name == "skills" and (katalog.parent.parent / ".claude-plugin").exists():
            continue  # skille wewnątrz przykładowej wtyczki sprawdza `claude plugin validate`
        pol = [PY, str(S / "budowa-skilli/scripts/sprawdz_skill.py"), str(katalog)]
        zadania.append(("skill", katalog, pol + (["--cli", a.cli] if a.cli else [])))
    for katalog in sorted(S.glob("*/examples/**/.claude-plugin")):
        if a.cli:
            zadania.append(("wtyczka", katalog.parent, [a.cli, "plugin", "validate", str(katalog.parent)]))
    for plik in sorted((KORZEN / "agents").glob("*.md")):
        zadania.append(("agenci", plik, [PY, str(S / "podagenci-i-zespoly/scripts/sprawdz_agenta.py"), str(plik)]))

    wyniki = []
    for rodzaj, cel, polecenie in zadania:
        if a.tylko and a.tylko not in str(cel):
            continue
        if rodzaj == "json":
            try:
                json.loads(cel.read_text(encoding="utf-8"))
                ok, tekst = True, "JSON poprawny"
            except json.JSONDecodeError as blad:
                ok, tekst = False, f"niepoprawny JSON: {blad}"
        elif rodzaj == "python":
            try:  # compile() w pamięci — bez zapisu __pycache__ obok przykładów
                compile(cel.read_text(encoding="utf-8"), str(cel), "exec")
                ok, tekst = True, "kompilacja OK"
            except SyntaxError as blad:
                ok, tekst = False, str(blad)
        else:
            ok, tekst = uruchom(polecenie)
            if ok and re.search(r"(?m)^\s*(BŁĄD|\[[^\]]+\] BŁĄD)", tekst):
                ok = False
        wyniki.append((rodzaj, cel, ok, tekst))

    bledne = [w for w in wyniki if not w[2]]
    licznik: dict[str, list[int]] = {}
    for rodzaj, _, ok, _ in wyniki:
        licznik.setdefault(rodzaj, [0, 0])[0 if ok else 1] += 1
    print(f"Przykłady: {len(wyniki)} sprawdzonych, {len(bledne)} z błędami")
    for rodzaj, (dobre, zle) in sorted(licznik.items()):
        print(f"  {rodzaj:<11} OK {dobre:>3}  błędy {zle:>2}")
    for rodzaj, cel, ok, tekst in wyniki:
        if not ok or a.szczegoly:
            print(f"\n[{'OK' if ok else 'BŁĄD'}] {rodzaj} {cel.relative_to(KORZEN)}")
            print("\n".join("    " + w for w in tekst.splitlines()[:15]))
    return 1 if bledne else 0


if __name__ == "__main__":
    sys.exit(main())
