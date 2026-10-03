#!/usr/bin/env python3
"""Pokazuje warstwy ustawień Claude Code dla katalogu projektu i to, która warstwa wygrywa.

Czyta (jeśli istnieją): ustawienia zarządzane (/etc/claude-code/managed-settings.json
i managed-settings.d/*.json albo --zarzadzane), pliki --settings, .claude/settings.local.json,
.claude/settings.json, <konfiguracja>/settings.json. Składa je według drabiny
managed > --settings > local > project > user: skalary z najwyższej warstwy, listy sumowane
(z wyjątkiem fallbackModel, modelPicker, availableModels z managed). Oznacza klucze,
których zasięg nie pozwala na dany plik (zostaną pominięte przez CLI).

To przybliżenie logiki CLI do szybkiej diagnozy, nie jej kopia: wyjątki bezpieczeństwa
(np. najniższy maxEffortLevel) są sygnalizowane uwagą. Wartości z bloku `env` nie są
wypisywane — tylko nazwy zmiennych i warstwa.

Użycie:
  warstwy_ustawien.py [--projekt KATALOG] [--konfiguracja ~/.claude] [--settings PLIK]…
                      [--zarzadzane PLIK]… [--klucz NAZWA] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402

NIE_SCALANE = {"fallbackModel", "modelPicker"}
WYJATKI = {"disableClaudeAiConnectors", "enableArtifact", "disableArtifact", "isolatePeerMachines",
           "remoteControlAtStartup", "crossSessionInbound", "useAutoModeDuringPlan", "syncClaudeAiSkills",
           "syncClaudeAiPlugins", "maxEffortLevel"}
RODZAJ = {"managed": "managed", "--settings": "flaga", "local": "local", "project": "project", "user": "user"}


def wczytaj(sciezka: Path) -> dict | None:
    try:
        dane = cc.czytaj_json(sciezka)
        return dane if isinstance(dane, dict) else None
    except (OSError, cc.BladJson) as blad:
        print(f"! {sciezka}: {blad}", file=sys.stderr)
        return None


def splaszcz(dane: dict, prefiks: str = "") -> dict[str, object]:
    """Spłaszcza permissions.* i sandbox.* do kluczy z kropką; reszta zostaje na górze."""
    wynik: dict[str, object] = {}
    for klucz, wartosc in dane.items():
        pelny = f"{prefiks}.{klucz}" if prefiks else klucz
        if isinstance(wartosc, dict) and pelny in ("permissions", "sandbox", "sandbox.network",
                                                   "sandbox.filesystem", "sandbox.credentials", "attribution",
                                                   "worktree", "autoMode"):
            wynik.update(splaszcz(wartosc, pelny))
        else:
            wynik[pelny] = wartosc
    return wynik


def dozwolony(klucz: str, warstwa: str) -> str:
    wpis = cc.klucze_ustawien().get(klucz)
    if not wpis:
        return ""
    zasieg = wpis["zasieg"]
    rodzaj = RODZAJ[warstwa]
    if zasieg.startswith("Managed") and rodzaj != "managed":
        return "tylko managed"
    if zasieg == "Global config":
        return "tylko ~/.claude.json"
    if zasieg == "User or managed" and rodzaj in ("project", "local"):
        return "nie z projektu"
    if zasieg.startswith("User, local") and rodzaj == "project":
        return "nie ze wspólnego projektu"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--projekt", type=Path, default=Path.cwd())
    parser.add_argument("--konfiguracja", type=Path,
                        default=Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")))
    parser.add_argument("--settings", type=Path, action="append", default=[])
    parser.add_argument("--zarzadzane", type=Path, action="append", default=[])
    parser.add_argument("--klucz", default="", help="pokaż tylko klucze zawierające ten tekst")
    parser.add_argument("--json", action="store_true")
    a = parser.parse_args()

    zarzadzane = a.zarzadzane or [Path("/etc/claude-code/managed-settings.json"),
                                  *sorted(Path("/etc/claude-code/managed-settings.d").glob("*.json"))]
    warstwy: list[tuple[str, Path]] = [("managed", p) for p in zarzadzane]
    warstwy += [("--settings", p) for p in a.settings]
    warstwy += [("local", a.projekt / ".claude" / "settings.local.json"),
                ("project", a.projekt / ".claude" / "settings.json"),
                ("user", a.konfiguracja / "settings.json")]

    zrodla: list[tuple[str, Path, dict]] = []
    for nazwa, sciezka in warstwy:
        if sciezka.is_file():
            dane = wczytaj(sciezka)
            if dane is not None:
                zrodla.append((nazwa, sciezka, splaszcz(dane)))

    wynik: dict[str, dict] = {}
    for nazwa, sciezka, dane in zrodla:  # od najwyższej warstwy
        for klucz, wartosc in dane.items():
            if klucz == "$schema" or (a.klucz and a.klucz.lower() not in klucz.lower()):
                continue
            blokada = dozwolony(klucz, nazwa)
            wpis = wynik.setdefault(klucz, {"wartosc": None, "zrodlo": None, "skladniki": [], "pominiete": []})
            if blokada:
                wpis["pominiete"].append(f"{nazwa} ({blokada})")
                continue
            if klucz == "env" and isinstance(wartosc, dict):
                wpis["skladniki"].append(f"{nazwa}: {', '.join(sorted(wartosc))}")
                if wpis["zrodlo"] is None:
                    wpis["zrodlo"], wpis["wartosc"] = nazwa, "(nazwy zmiennych w składnikach)"
                continue
            if isinstance(wartosc, list) and klucz not in NIE_SCALANE and \
                    not (klucz == "availableModels" and wpis["zrodlo"] == "managed"):
                wpis["skladniki"].append(f"{nazwa}: {len(wartosc)} wpisów")
                wpis["wartosc"] = (wpis["wartosc"] or []) + [w for w in wartosc if w not in (wpis["wartosc"] or [])]
                wpis["zrodlo"] = wpis["zrodlo"] or "suma warstw"
            elif wpis["zrodlo"] is None:
                wpis["wartosc"], wpis["zrodlo"] = wartosc, nazwa
            else:
                wpis["skladniki"].append(f"{nazwa}: przesłonięte przez {wpis['zrodlo']}")

    if a.json:
        print(json.dumps({"warstwy": [(n, str(p)) for n, p, _ in zrodla], "klucze": wynik},
                         ensure_ascii=False, indent=1, default=str))
        return 0
    print("Wczytane warstwy (od najsilniejszej):")
    for nazwa, sciezka, _ in zrodla:
        print(f"  {nazwa:<11} {sciezka}")
    if not zrodla:
        print("  (brak plików ustawień)")
    print()
    for klucz in sorted(wynik):
        wpis = wynik[klucz]
        wartosc = json.dumps(wpis["wartosc"], ensure_ascii=False)
        if len(wartosc) > 110:
            wartosc = wartosc[:107] + "…"
        print(f"{klucz} = {wartosc}   [{wpis['zrodlo'] or 'pominięte'}]")
        for s in wpis["skladniki"]:
            print(f"    · {s}")
        for p in wpis["pominiete"]:
            print(f"    ✗ pominięte: {p}")
        if klucz in WYJATKI:
            print("    ! wyjątek bezpieczeństwa: wartość restrykcyjna z niższej warstwy może wygrać")
    return 0


if __name__ == "__main__":
    sys.exit(main())
