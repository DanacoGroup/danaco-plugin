#!/usr/bin/env python3
"""Sprawdzenie definicji podagentów: pliki .md z frontmatterem albo JSON dla --agents.

Reguły z `cc:sub-agents`: wymagane `name` i `description`; `name` bez `:` i bez `-` na
początku; pola w camelCase dokładnie jak w dokumentacji (nieznane CLI pomija po cichu);
wartości `model`, `permissionMode`, `effort`, `memory`, `isolation`, `color`; `tools` z
nazwami narzędzi wbudowanych lub `mcp__…`; `Agent(typ)` w tools działa tylko dla agenta
głównego (`--agent`); pola ignorowane we wtyczkach (`hooks`, `mcpServers`, `permissionMode`);
w `--agents` ignorowane `color`, `experimental`. Opcjonalnie uruchamia
`claude plugin validate` na katalogu agentów (≥2.1.233).

Użycie:
  sprawdz_agenta.py PLIK.md|KATALOG|PLIK.json [--wtyczka] [--cli /sciezka/claude]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402

POLA = {"name", "description", "tools", "disallowedTools", "model", "permissionMode", "maxTurns", "skills",
        "mcpServers", "hooks", "memory", "background", "omitClaudeMd", "effort", "isolation", "color",
        "initialPrompt", "experimental", "prompt"}
WARTOSCI = {
    "permissionMode": {"default", "manual", "acceptEdits", "auto", "dontAsk", "bypassPermissions", "plan"},
    "effort": {"low", "medium", "high", "xhigh", "max"},
    "memory": {"user", "project", "local"},
    "isolation": {"worktree"},
    "color": {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"},
}
NIE_DLA_PODAGENTOW = {"AskUserQuestion", "EnterPlanMode", "ScheduleWakeup", "WaitForMcpServers", "Workflow",
                      "EndConversation"}


def frontmatter(tekst: str) -> tuple[dict, str] | None:
    if not tekst.startswith("---\n"):
        return None
    koniec = tekst.find("\n---", 4)
    if koniec < 0:
        return None
    dane: dict = {}
    klucz = None
    for linia in tekst[4:koniec].splitlines():
        if not linia.strip() or linia.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", linia)
        if m and not linia.startswith((" ", "\t")):
            klucz, wartosc = m.group(1), m.group(2).strip()
            dane[klucz] = wartosc if wartosc else []
        elif klucz is not None and linia.strip().startswith("- ") and isinstance(dane.get(klucz), list):
            dane[klucz].append(linia.strip()[2:].strip())
        elif klucz is not None and isinstance(dane.get(klucz), list):
            dane[klucz] = {"_zlozone": True}
    return dane, tekst[koniec + 4:].strip()


def lista(wartosc) -> list[str]:
    if isinstance(wartosc, list):
        return [str(x).strip().strip("'\"") for x in wartosc]
    if isinstance(wartosc, str):
        return [x.strip() for x in re.split(r",(?![^()]*\))", wartosc) if x.strip()]
    return []


def ocen(nazwa_zrodla: str, d: dict, cialo: str, wtyczka: bool, z_json: bool) -> list[str]:
    uwagi = []
    nazwa = str(d.get("name", ""))
    if not z_json:
        if not nazwa:
            uwagi.append("BŁĄD: brak `name` — CLI potraktuje plik jak dokumentację i pominie")
        if not d.get("description"):
            uwagi.append("BŁĄD: brak `description` — CLI pominie plik")
    if nazwa.startswith("-") or ":" in nazwa:
        uwagi.append("BŁĄD: `name` zaczyna się od `-` albo zawiera `:` — plik pominięty")
    for pole in d:
        if pole not in POLA:
            podobne = [p for p in POLA if p.lower() == pole.lower() or p.lower() == pole.replace("_", "").lower()]
            uwagi.append(f"BŁĄD: pole `{pole}` nieznane — CLI pominie je po cichu" + (f" (chodziło o `{podobne[0]}`?)" if podobne else ""))
    for pole, dozwolone in WARTOSCI.items():
        if pole in d and isinstance(d[pole], str) and d[pole] and d[pole] not in dozwolone:
            uwagi.append(f"BŁĄD: {pole}={d[pole]!r} spoza {sorted(dozwolone)}")
    opis = str(d.get("description", ""))
    if opis and len(opis) < 60:
        uwagi.append("uwaga: krótki opis — opis decyduje o automatycznym delegowaniu; napisz kiedy używać i czego agent nie robi")
    narzedzia = cc.narzedzia()
    for pole in ("tools", "disallowedTools"):
        for n in lista(d.get(pole)):
            baza = n.split("(")[0]
            if baza.startswith("mcp__") or baza in narzedzia or baza in ("Task",):
                if baza in NIE_DLA_PODAGENTOW and pole == "tools":
                    uwagi.append(f"uwaga: `{n}` nie jest dostępne podagentom (odfiltrowane)")
                if pole == "tools" and n.startswith("Agent(") and not z_json:
                    uwagi.append("uwaga: `Agent(typy)` działa tylko dla agenta głównego (`--agent`); w podagencie lista typów ignorowana")
                if pole == "disallowedTools" and "(" in n:
                    uwagi.append(f"uwaga: `{n}` w disallowedTools usuwa całe narzędzie {baza}; do blokady poleceń użyj permissions.deny")
                continue
            uwagi.append(f"BŁĄD: `{n}` w {pole} nie jest nazwą narzędzia — przy samych błędnych nazwach podagent się nie uruchomi")
    if wtyczka:
        for pole in ("hooks", "mcpServers", "permissionMode", "initialPrompt"):
            if pole in d:
                uwagi.append(f"uwaga: `{pole}` jest ignorowane dla podagentów z wtyczki")
    if z_json:
        for pole in ("color", "experimental"):
            if pole in d:
                uwagi.append(f"uwaga: `{pole}` jest ignorowane w --agents")
    if d.get("permissionMode") == "bypassPermissions":
        uwagi.append("uwaga: bypassPermissions w podagencie działa tylko, gdy sesja główna jest w bypass (≥2.1.267)")
    if d.get("memory") and str(d.get("omitClaudeMd")).lower() == "true":
        pass
    if not z_json and not cialo:
        uwagi.append("uwaga: pusta treść — podagent nie dostanie instrukcji systemowej")
    return uwagi or ["bez uwag"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cel", type=Path)
    parser.add_argument("--wtyczka", action="store_true", help="pliki z katalogu agents/ wtyczki")
    parser.add_argument("--cli", default="")
    a = parser.parse_args()
    bledy = 0
    if a.cel.suffix == ".json":
        dane = json.loads(a.cel.read_text(encoding="utf-8"))
        for nazwa, d in dane.items():
            if nazwa.startswith("-"):
                print(f"[{nazwa}] BŁĄD: nazwa nie może zaczynać się od `-`")
            uwagi = ocen(nazwa, {**d, "name": nazwa}, d.get("prompt", ""), False, True)
            for u in uwagi:
                print(f"[{nazwa}] {u}")
                bledy += u.startswith("BŁĄD")
    else:
        pliki = sorted(a.cel.rglob("*.md")) if a.cel.is_dir() else [a.cel]
        for plik in pliki:
            wynik = frontmatter(plik.read_text(encoding="utf-8"))
            if wynik is None:
                print(f"[{plik.name}] BŁĄD: brak frontmattera od pierwszego wiersza — plik traktowany jak dokumentacja")
                bledy += 1
                continue
            d, cialo = wynik
            for u in ocen(plik.name, d, cialo, a.wtyczka, False):
                print(f"[{plik.name}] {u}")
                bledy += u.startswith("BŁĄD")
        if a.cli and a.cel.is_dir():
            wynik = subprocess.run([a.cli, "plugin", "validate", str(a.cel)], capture_output=True, text=True)
            print(f"claude plugin validate: kod {wynik.returncode}; {wynik.stdout.strip().splitlines()[-1] if wynik.stdout.strip() else wynik.stderr.strip()[:200]}")
            bledy += wynik.returncode != 0
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
