#!/usr/bin/env python3
"""Audyt konfiguracji Claude Code konta i projektu względem dobrych praktyk — zbiera dowody.

Uruchamia narzędzia wtyczki (tylko odczyt) i składa wyniki w jednym katalogu:
  warstwy.txt        — warstwy ustawień i zwycięskie wartości (warstwy_ustawien.py),
  ustawienia-*.txt   — walidacja każdego pliku (waliduj_ustawienia.py, z claude doctor przy --cli),
  reguly-*.txt       — lint reguł uprawnień (sprawdz_reguly.py),
  pamiec.txt         — CLAUDE.md, reguły, importy, pamięć automatyczna (audyt_pamieci.py),
  agenci-*.txt       — definicje podagentów (sprawdz_agenta.py),
  skille-*.txt       — skille użytkownika i projektu (sprawdz_skill.py),
  mcp.txt            — .mcp.json projektu (sprawdz_mcp.py, bez uruchamiania serwerów),
  zmienne.txt        — zmienne środowiskowe (tylko nazwy),
  lista-kontrolna.md — punkty bezpieczeństwa dla profilu (lista_kontrolna.py),
  diagnostyka/       — claude doctor, piaskownica, zaślepki, logi (zbierz_diagnostyke.py),
  podsumowanie.json  — liczniki błędów/ostrzeżeń na obszar (wejście dla raportu audytora).

Użycie:
  audyt_konfiguracji.py [--projekt DIR] [--konfiguracja ~/.claude] [--profil stanowisko|ci|usluga]
                        [--cli claude] [--wyjscie DIR]
Nie zmienia żadnego pliku konfiguracji. Wartości sekretów nie są wypisywane.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[1]
S = KORZEN / "skills"


def uruchom(nazwa: str, polecenie: list[str], wyj: Path, cwd: Path | None = None) -> dict:
    try:
        w = subprocess.run(polecenie, capture_output=True, text=True, timeout=300, cwd=cwd, stdin=subprocess.DEVNULL)
        tekst, kod = (w.stdout + ("\n" + w.stderr if w.stderr.strip() else "")).strip(), w.returncode
    except (OSError, subprocess.TimeoutExpired) as blad:
        tekst, kod = f"nie udało się uruchomić: {blad}", 127
    (wyj / f"{nazwa}.txt").write_text(tekst + "\n", encoding="utf-8")
    # Narzędzia wtyczki znakują znaleziska różnie: „BŁĄD …” (walidator, reguły, diagnostyka),
    # „[nazwa] BŁĄD: …” (sprawdz_skill, sprawdz_agenta), „[BRAK ] …”/„[UWAGA ] …” (lista kontrolna),
    # „ostrzeżenie: …” (zmienne). Licznik dopuszcza opcjonalny przedrostek „[…] ”, by żadne nie umknęło.
    bledy = len(re.findall(r"(?m)^\s*(?:\[[^\]]*\]\s*)?BŁĄD\b", tekst)) \
        + len(re.findall(r"(?m)^\s*\[BRAK", tekst)) + (1 if kod not in (0, 1) else 0)
    ostrz = len(re.findall(r"(?m)^\s*(?:\[[^\]]*\]\s*)?(?:OSTRZ|ostrzeżenie)\b", tekst)) \
        + len(re.findall(r"(?m)^\s*\[UWAGA", tekst))
    return {"obszar": nazwa, "kod": kod, "bledy": bledy, "ostrzezenia": ostrz, "plik": f"{nazwa}.txt"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projekt", type=Path, default=Path.cwd())
    p.add_argument("--konfiguracja", type=Path,
                   default=Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"))
    p.add_argument("--profil", choices=["stanowisko", "ci", "usluga"], default="stanowisko")
    p.add_argument("--cli", default=os.environ.get("CLAUDE_BIN", ""))
    p.add_argument("--wyjscie", type=Path)
    a = p.parse_args()
    projekt, konf = a.projekt.resolve(), a.konfiguracja.expanduser().resolve()
    wyj = a.wyjscie or Path(os.environ.get("TMPDIR", "/tmp")) / f"audyt-claude-{time.strftime('%Y%m%d-%H%M%S')}"
    wyj.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    wyniki = []

    wyniki.append(uruchom("warstwy", [py, str(S / "ustawienia-i-hierarchia/scripts/warstwy_ustawien.py"),
                                      "--projekt", str(projekt), "--konfiguracja", str(konf)], wyj))
    # projekt w katalogu domowym: .claude projektu = katalog konfiguracji użytkownika — nie licz go podwójnie
    projekt_to_dom = (projekt / ".claude").resolve() == konf
    pliki = [("user", konf / "settings.json")]
    if not projekt_to_dom:
        pliki += [("project", projekt / ".claude/settings.json"), ("local", projekt / ".claude/settings.local.json")]
    istniejace = []
    for rodzaj, plik in pliki:
        if not plik.exists():
            continue
        istniejace.append(plik)
        polecenie = [py, str(KORZEN / "scripts/waliduj_ustawienia.py"), str(plik), "--rodzaj", rodzaj]
        if a.cli:
            polecenie += ["--cli", a.cli]
        wyniki.append(uruchom(f"ustawienia-{rodzaj}", polecenie, wyj))
        wyniki.append(uruchom(f"reguly-{rodzaj}", [py, str(S / "uprawnienia-i-tryby/scripts/sprawdz_reguly.py"),
                                                   "--plik", str(plik)], wyj))
    wyniki.append(uruchom("pamiec", [py, str(S / "instrukcja-systemowa-i-pamiec/scripts/audyt_pamieci.py"),
                                     "--projekt", str(projekt), "--konfiguracja", str(konf)], wyj))
    katalogi_projektu = [] if projekt_to_dom else [("projektu", projekt / ".claude/agents")]
    for opis, katalog in [("uzytkownika", konf / "agents")] + katalogi_projektu:
        if katalog.is_dir() and any(katalog.glob("*.md")):
            wyniki.append(uruchom(f"agenci-{opis}", [py, str(S / "podagenci-i-zespoly/scripts/sprawdz_agenta.py"),
                                                     str(katalog)], wyj))
    skille_projektu = [] if projekt_to_dom else [("projektu", projekt / ".claude/skills")]
    for opis, katalog in [("uzytkownika", konf / "skills")] + skille_projektu:
        if katalog.is_dir():
            for skill in sorted(x for x in katalog.iterdir() if (x / "SKILL.md").exists()):
                wyniki.append(uruchom(f"skille-{opis}-{skill.name}", [py, str(S / "budowa-skilli/scripts/sprawdz_skill.py"),
                                                                       str(skill)], wyj))
    if (projekt / ".mcp.json").exists():
        wyniki.append(uruchom("mcp", [py, str(S / "serwery-mcp/scripts/sprawdz_mcp.py"), str(projekt / ".mcp.json")], wyj))
    zmienne = [py, str(S / "zmienne-srodowiskowe/scripts/sprawdz_zmienne.py")]
    if a.cli:
        zmienne += ["--cli", a.cli]
    wyniki.append(uruchom("zmienne", zmienne, wyj))
    if istniejace:
        wyniki.append(uruchom("lista-kontrolna", [py, str(S / "bezpieczenstwo-wdrozenia/scripts/lista_kontrolna.py"),
                                                  "--profil", a.profil, "--ustawienia", *map(str, istniejace),
                                                  "--markdown", str(wyj / "lista-kontrolna.md")], wyj))
    diag = [py, str(S / "diagnostyka/scripts/zbierz_diagnostyke.py"), "--projekt", str(projekt),
            "--konfiguracja", str(konf), "--wyjscie", str(wyj / "diagnostyka")]
    if a.cli:
        diag += ["--cli", a.cli]
    else:
        diag += ["--bez-doctor"]
    wyniki.append(uruchom("diagnostyka", diag, wyj))

    podsumowanie = {"projekt": str(projekt), "konfiguracja": str(konf), "profil": a.profil,
                    "projekt_w_katalogu_domowym": projekt_to_dom,
                    "czas": time.strftime("%Y-%m-%d %H:%M"), "obszary": wyniki,
                    "bledy": sum(w["bledy"] for w in wyniki), "ostrzezenia": sum(w["ostrzezenia"] for w in wyniki)}
    (wyj / "podsumowanie.json").write_text(json.dumps(podsumowanie, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Audyt: {wyj}")
    print(f"  obszarów {len(wyniki)}, błędów {podsumowanie['bledy']}, ostrzeżeń {podsumowanie['ostrzezenia']}")
    for w in wyniki:
        if w["bledy"] or w["ostrzezenia"]:
            print(f"  {w['obszar']:<34} błędy {w['bledy']:>2}  ostrzeżenia {w['ostrzezenia']:>2}  ({w['plik']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
