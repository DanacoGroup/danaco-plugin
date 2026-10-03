#!/usr/bin/env python3
"""Audyt instrukcji i pamięci projektu Claude Code (tylko odczyt).

Znajduje i ocenia: CLAUDE.md / .claude/CLAUDE.md / CLAUDE.local.md / AGENTS.md w katalogu
projektu i katalogach nadrzędnych, ~/.claude/CLAUDE.md, reguły .claude/rules/*.md (z `paths`
lub bez), importy `@ścieżka` (czy istnieją, głębokość ≤4), rozmiary (zalecane < 200 wierszy,
limit 4 MiB), komentarze HTML (usuwane przed wstrzyknięciem), MEMORY.md pamięci
automatycznej (limit 200 wierszy / 25 KB), wyłączenia (claudeMdExcludes, autoMemoryEnabled).

Użycie:
  audyt_pamieci.py [--projekt KATALOG] [--konfiguracja ~/.claude]
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

IMPORT = re.compile(r"(?<![`\w])@((?:\\ |[^\s`])+)")


def importy(plik: Path, glebokosc: int = 1, odwiedzone: set | None = None) -> list[str]:
    odwiedzone = odwiedzone or set()
    uwagi = []
    tekst = re.sub(r"```.*?```", "", plik.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    tekst = re.sub(r"`[^`]*`", "", tekst)
    for surowa in IMPORT.findall(tekst):
        sciezka = surowa.replace("\\ ", " ").rstrip(".,;:)")
        if "/" not in sciezka and "." not in sciezka:
            continue  # wzmianka @uzytkownik, nie import
        cel = (plik.parent / os.path.expanduser(sciezka)).resolve() if not sciezka.startswith("/") else Path(sciezka)
        if not cel.exists():
            uwagi.append(f"  BŁĄD import @{sciezka} w {plik.name}: plik nie istnieje")
        elif glebokosc >= 4:
            uwagi.append(f"  uwaga import @{sciezka}: głębokość > 4 — nie zostanie wczytany")
        elif cel not in odwiedzone and cel.is_file():
            odwiedzone.add(cel)
            uwagi += importy(cel, glebokosc + 1, odwiedzone)
    return uwagi


def ocen(plik: Path) -> list[str]:
    tekst = plik.read_text(encoding="utf-8", errors="replace")
    wiersze = tekst.count("\n") + 1
    uwagi = [f"{plik}: {wiersze} wierszy, {len(tekst.encode())} B"]
    if len(tekst.encode()) > 4 * 1024 * 1024:
        uwagi.append("  BŁĄD > 4 MiB — plik zostanie pominięty")
    elif wiersze > 200:
        uwagi.append("  uwaga > 200 wierszy — gorsze przestrzeganie; przenieś części do .claude/rules z paths")
    if re.search(r"<!--.*?-->", tekst, re.S):
        uwagi.append("  info: komentarze HTML zostaną usunięte przed wstrzyknięciem")
    if re.search(r"\b(zawsze|nigdy|always|never)\b", tekst, re.I) and re.search(r"\b(rm -rf|push|deploy|sekret|secret)\b", tekst, re.I):
        uwagi.append("  uwaga: zakazy operacji w CLAUDE.md to prośba — egzekwuj regułą deny lub hookiem")
    return uwagi + importy(plik)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projekt", type=Path, default=Path.cwd())
    p.add_argument("--konfiguracja", type=Path, default=Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")))
    a = p.parse_args()
    projekt = a.projekt.resolve()
    znalezione = []
    for kat in [projekt, *projekt.parents]:
        for nazwa in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
            if (kat / nazwa).is_file():
                znalezione.append(kat / nazwa)
        if (kat / ".git").exists():
            break
    uzytkownik = a.konfiguracja / "CLAUDE.md"
    print("== Pliki instrukcji (od najogólniejszego)")
    if uzytkownik.is_file():
        print("\n".join(ocen(uzytkownik)))
    for plik in reversed(znalezione):
        print("\n".join(ocen(plik)))
    if not znalezione and not uzytkownik.is_file():
        print("brak CLAUDE.md / AGENTS.md")
    if any(p.name == "AGENTS.md" for p in znalezione) and any(p.name == "CLAUDE.md" for p in znalezione):
        print("uwaga: CLAUDE.md i AGENTS.md razem — domyślnie wczytywany tylko CLAUDE.md "
              "(tryb: pluginConfigs['agents-md@builtin'].options.instructionFiles)")
    print("== Reguły .claude/rules")
    for katalog in (projekt / ".claude" / "rules", a.konfiguracja / "rules"):
        for regula in sorted(katalog.rglob("*.md")) if katalog.is_dir() else []:
            tekst = regula.read_text(encoding="utf-8", errors="replace")
            warunkowa = tekst.startswith("---") and "paths:" in tekst.split("---", 2)[1] if tekst.startswith("---") else False
            print(f"{regula}: {'warunkowa (paths)' if warunkowa else 'zawsze ładowana'}, {tekst.count(chr(10)) + 1} wierszy")
    print("== Ustawienia pamięci")
    for plik in (a.konfiguracja / "settings.json", projekt / ".claude" / "settings.json", projekt / ".claude" / "settings.local.json"):
        if plik.is_file():
            try:
                dane = json.loads(plik.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"{plik}: błędny JSON")
                continue
            for klucz in ("autoMemoryEnabled", "autoMemoryDirectory", "claudeMdExcludes", "outputStyle"):
                if klucz in dane:
                    print(f"{plik.name}: {klucz} = {json.dumps(dane[klucz], ensure_ascii=False)}")
    if os.environ.get("CLAUDE_CODE_DISABLE_AUTO_MEMORY") == "1":
        print("CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 — pamięć automatyczna wyłączona")
    print("== Pamięć automatyczna (MEMORY.md)")
    projekty = a.konfiguracja / "projects"
    for memory in sorted(projekty.glob("*/memory/MEMORY.md")) if projekty.is_dir() else []:
        tekst = memory.read_text(encoding="utf-8", errors="replace")
        wiersze = tekst.count("\n") + 1
        ostrzezenie = " — POWYŻEJ limitu wczytywania (200 wierszy / 25 KB)" if wiersze > 200 or len(tekst.encode()) > 25 * 1024 else ""
        print(f"{memory.parent.parent.name}: {wiersze} wierszy, {len(tekst.encode())} B, plików tematów: "
              f"{len(list(memory.parent.glob('*.md'))) - 1}{ostrzezenie}")


if __name__ == "__main__":
    main()
