#!/usr/bin/env python3
"""Zbiera diagnostykę konfiguracji Claude Code dla konta i projektu — tylko odczyt, bez sekretów.

Co sprawdza:
  1. wersję CLI i `claude doctor` (sekcje: Invalid settings, Managed settings (remote),
     Organization policy, Auto-updates, ostrzeżenia), uruchomione w katalogu projektu,
  2. pliki ustawień każdej warstwy (user, project, local) — walidator wtyczki,
  3. `.mcp.json` projektu — lint (bez uruchamiania serwerów),
  4. środowisko procesu — nazwy zmiennych Claude Code (bez wartości), literówki, konflikty,
  5. CLAUDE.md i reguły (rozmiary), skille i agenci projektu/użytkownika (liczby),
  6. piaskownicę (bwrap, socat, userns) i długość TMPDIR (gniazda),
  7. pozostawione zaślepki (0-bajtowe `.env*`, `.npmrc`, `package.json`…, pusty
     `.claude/settings.local.json`) — ślady izolacji/piaskownicy,
  8. najnowsze logi debug w `<konfiguracja>/debug/` (nazwy i rozmiary).

Użycie:
  zbierz_diagnostyke.py [--projekt DIR] [--konfiguracja DIR] [--cli claude] [--wyjscie DIR] [--bez-doctor]
Wynik: streszczenie na ekranie i raport `diagnostyka.md` + surowe wyniki w katalogu --wyjscie
(domyślnie $TMPDIR/diagnostyka-claude-<czas>). Kod wyjścia 1, gdy są błędy.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
WALIDATOR = KORZEN / "scripts" / "waliduj_ustawienia.py"
MCP = KORZEN / "skills" / "serwery-mcp" / "scripts" / "sprawdz_mcp.py"
ZMIENNE = KORZEN / "skills" / "zmienne-srodowiskowe" / "scripts" / "sprawdz_zmienne.py"
PIASKOWNICA = KORZEN / "skills" / "piaskownica-i-izolacja" / "scripts" / "sprawdz_srodowisko.sh"
ZASLEPKI = [".env", ".env.local", ".env.development", ".env.production", ".env.test", ".npmrc", ".yarnrc",
            ".yarnrc.yml", "bunfig.toml", "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            ".gitmodules"]
SEKCJE_DOCTOR = ("Invalid", "Managed settings", "Organization policy", "Auto-updates", "Setting", "Stale", "Warning",
                 "⚠", "✗", "Error", "Skipped")


def uruchom(polecenie: list[str], **kw) -> tuple[int, str]:
    try:
        w = subprocess.run(polecenie, capture_output=True, text=True, timeout=kw.pop("timeout", 120),
                           stdin=subprocess.DEVNULL, **kw)
        return w.returncode, (w.stdout + w.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as blad:
        return 127, f"nie udało się uruchomić: {blad}"


def maskuj(tekst: str) -> str:
    tekst = re.sub(r"(sk-ant-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]+", r"\1…", tekst)
    return re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1…", tekst)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projekt", type=Path, default=Path.cwd())
    p.add_argument("--konfiguracja", type=Path,
                   default=Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"))
    p.add_argument("--cli", default=os.environ.get("CLAUDE_BIN", "claude"))
    p.add_argument("--wyjscie", type=Path)
    p.add_argument("--bez-doctor", action="store_true")
    a = p.parse_args()
    wyj = a.wyjscie or Path(os.environ.get("TMPDIR", "/tmp")) / f"diagnostyka-claude-{time.strftime('%Y%m%d-%H%M%S')}"
    wyj.mkdir(parents=True, exist_ok=True)
    projekt, konf = a.projekt.resolve(), a.konfiguracja.expanduser()
    bledy, ostrz, info = [], [], []
    raport = [f"# Diagnostyka Claude Code — {time.strftime('%Y-%m-%d %H:%M')}", "",
              f"- projekt: `{projekt}`", f"- konfiguracja: `{konf}`", ""]

    # 1. CLI i doctor
    cli = shutil.which(a.cli) or a.cli
    kod, wersja = uruchom([cli, "--version"], timeout=30)
    info.append(f"CLI: {wersja.splitlines()[0] if wersja else '?'} ({cli})")
    if not a.bez_doctor:
        srodowisko = dict(os.environ, CLAUDE_CONFIG_DIR=str(konf), DISABLE_AUTOUPDATER="1")
        kod, wynik = uruchom([cli, "doctor"], cwd=projekt, env=srodowisko, timeout=120)
        wynik = maskuj(wynik)
        (wyj / "doctor.txt").write_text(wynik + "\n", encoding="utf-8")
        wazne = [w.strip() for w in wynik.splitlines() if any(s in w for s in SEKCJE_DOCTOR)]
        raport += ["## claude doctor", "", "```", *wazne[:40], "```", ""]
        if any("Invalid" in w for w in wazne):
            bledy.append("claude doctor: nieprawidłowe ustawienia (szczegóły w doctor.txt)")
        info.append(f"claude doctor: {len(wazne)} istotnych wierszy (doctor.txt)")

    # 2. Pliki ustawień
    raport += ["## Pliki ustawień", ""]
    warstwy = [("user", konf / "settings.json")]
    if (projekt / ".claude").resolve() != konf.resolve():  # projekt w katalogu domowym = ten sam katalog .claude
        warstwy += [("project", projekt / ".claude" / "settings.json"), ("local", projekt / ".claude" / "settings.local.json")]
    for rodzaj, plik in warstwy:
        if not plik.exists():
            raport.append(f"- {rodzaj}: brak (`{plik}`)")
            continue
        if plik.stat().st_size == 0:
            ostrz.append(f"{plik}: pusty plik (0 B) — możliwa zaślepka po przerwanej sesji z piaskownicą")
        kod, wynik = uruchom([sys.executable, str(WALIDATOR), str(plik), "--rodzaj", rodzaj])
        (wyj / f"ustawienia-{rodzaj}.txt").write_text(wynik + "\n", encoding="utf-8")
        pierwszy = wynik.splitlines()[0] if wynik else "?"
        raport.append(f"- {rodzaj}: {pierwszy}")
        if kod:
            bledy.append(f"ustawienia {rodzaj}: błędy walidacji (ustawienia-{rodzaj}.txt)")
        elif "OSTRZ" in wynik:
            ostrz.append(f"ustawienia {rodzaj}: ostrzeżenia walidatora (ustawienia-{rodzaj}.txt)")
    if (konf.parent / ".claude.json").exists() or (konf / ".claude.json").exists():
        info.append(".claude.json obecny (stan aplikacji, nie ustawienia — permissions/hooks/env tam nie działają)")
    raport.append("")

    # 3. MCP
    mcp = projekt / ".mcp.json"
    if mcp.exists():
        kod, wynik = uruchom([sys.executable, str(MCP), str(mcp)])
        (wyj / "mcp.txt").write_text(wynik + "\n", encoding="utf-8")
        raport += ["## .mcp.json", "", "```", *wynik.splitlines()[:20], "```", ""]
        if kod:
            bledy.append(".mcp.json: błędy (mcp.txt)")
    if (projekt / ".claude" / ".mcp.json").exists() or (projekt / ".claude" / "mcp.json").exists():
        bledy.append(".mcp.json w katalogu .claude/ — CLI go nie czyta (ma być w korzeniu repozytorium)")

    # 4. Środowisko (tylko nazwy)
    kod, wynik = uruchom([sys.executable, str(ZMIENNE), "--cli", cli])
    (wyj / "zmienne.txt").write_text(wynik + "\n", encoding="utf-8")
    problemy = [w.strip() for w in wynik.splitlines() if re.match(r"\s*(BŁĄD|ostrzeżenie|NIEZNANA|NIEUDOKUMENTOWANA)", w)]
    raport += ["## Zmienne środowiskowe (nazwy, bez wartości)", "", *([f"- {w}" for w in problemy] or ["- bez uwag"]), ""]
    if kod:
        bledy.append("zmienne środowiskowe: błędy (zmienne.txt)")

    # 5. Pamięć, skille, agenci
    raport += ["## Pamięć, skille, agenci", ""]
    for opis, sciezka in (("CLAUDE.md projektu", projekt / "CLAUDE.md"), ("CLAUDE.md w .claude", projekt / ".claude" / "CLAUDE.md"),
                          ("CLAUDE.local.md", projekt / "CLAUDE.local.md"), ("CLAUDE.md użytkownika", konf / "CLAUDE.md")):
        if sciezka.exists():
            rozmiar = sciezka.stat().st_size
            raport.append(f"- {opis}: {rozmiar} B")
            if rozmiar > 40_000:
                ostrz.append(f"{opis}: {rozmiar} B — długi plik obniża stosowanie instrukcji (przenieś części do skilli/reguł)")
    for opis, katalog in (("skille projektu", projekt / ".claude" / "skills"), ("skille użytkownika", konf / "skills"),
                          ("agenci projektu", projekt / ".claude" / "agents"), ("agenci użytkownika", konf / "agents"),
                          ("reguły projektu", projekt / ".claude" / "rules")):
        if katalog.is_dir():
            liczba = len(list(katalog.glob("*/SKILL.md"))) if "skille" in opis else len(list(katalog.glob("*.md")))
            raport.append(f"- {opis}: {liczba}")
            if "skille" in opis:
                luzne = list(katalog.glob("*.md"))
                if luzne:
                    bledy.append(f"{opis}: pliki .md bez katalogu ({', '.join(x.name for x in luzne[:3])}) — skill to katalog z SKILL.md")
    raport.append("")

    # 6. Piaskownica i TMPDIR
    if PIASKOWNICA.exists():
        kod, wynik = uruchom(["sh", str(PIASKOWNICA)])
        (wyj / "piaskownica.txt").write_text(wynik + "\n", encoding="utf-8")
        raport += ["## Piaskownica", "", "```", *wynik.splitlines()[:15], "```", ""]
    tmp = os.environ.get("TMPDIR", "/tmp")
    if len(tmp) > 60:
        ostrz.append(f"TMPDIR ma {len(tmp)} znaków — piaskownica może nie utworzyć gniazd („Failed to create bridge sockets”)")

    # 7. Zaślepki
    zaslepki = [n for n in ZASLEPKI if (projekt / n).is_file() and (projekt / n).stat().st_size == 0]
    if len(zaslepki) >= 3:
        ostrz.append(f"projekt zawiera {len(zaslepki)} pustych plików typowych dla zaślepek izolacji ({', '.join(zaslepki[:6])}…) — "
                     "ślad CLAUDE_CODE_SUBPROCESS_ENV_SCRUB lub przerwanej piaskownicy; usuń przy zamkniętych sesjach")

    # 8. Logi debug
    debug = konf / "debug"
    if debug.is_dir():
        logi = sorted(debug.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        raport += ["## Najnowsze logi debug", "", *[f"- `{x.name}` {x.stat().st_size} B" for x in logi], ""]

    raport += ["## Wnioski", "", *[f"- **BŁĄD** {t}" for t in bledy], *[f"- ostrzeżenie: {t}" for t in ostrz],
               *[f"- {t}" for t in info], ""]
    (wyj / "diagnostyka.md").write_text("\n".join(raport), encoding="utf-8")
    print(f"Raport: {wyj / 'diagnostyka.md'}")
    for t in bledy:
        print(f"  BŁĄD {t}")
    for t in ostrz:
        print(f"  OSTRZ {t}")
    for t in info:
        print(f"  info {t}")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
