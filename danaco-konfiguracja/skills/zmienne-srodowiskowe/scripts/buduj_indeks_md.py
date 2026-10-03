#!/usr/bin/env python3
"""Generuje references/indeks-zmiennych.md z wspolne/indeksy/zmienne.tsv (kategorie po polsku,
opis — pierwsze zdanie dokumentacji w oryginale). Uruchamiaj po odświeżeniu indeksu.

Użycie: buduj_indeks_md.py [--wyjscie PLIK]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
from cc_wspolne import zmienne  # noqa: E402

NAZWY = {
    "uwierzytelnianie-i-dostawcy": "Uwierzytelnianie i dostawcy",
    "model-effort-i-myslenie": "Model, effort i myślenie",
    "cache-promptu": "Cache promptu",
    "kontekst-kompakcja-i-wyjscie": "Kontekst, kompakcja i wyjście",
    "sesje-headless-i-osadzanie": "Sesje, headless i osadzanie",
    "podagenci-zespoly-i-zadania-w-tle": "Podagenci, zespoły i zadania w tle",
    "narzedzia-wbudowane": "Narzędzia wbudowane",
    "mcp": "MCP",
    "skille-wtyczki-i-polecenia": "Skille, wtyczki i polecenia",
    "uprawnienia-i-tryby": "Uprawnienia i tryby",
    "bezpieczenstwo-i-izolacja": "Bezpieczeństwo i izolacja",
    "pamiec-i-claude-md": "Pamięć i CLAUDE.md",
    "instrukcja-i-tozsamosc": "Instrukcja i tożsamość",
    "hooki": "Hooki",
    "telemetria-i-prywatnosc": "Telemetria i prywatność",
    "siec-proxy-i-niezawodnosc": "Sieć, proxy i niezawodność",
    "aktualizacje-i-instalacja": "Aktualizacje i instalacja",
    "ustawienia-i-zarzadzanie": "Ustawienia i zarządzanie",
    "diagnostyka-i-logi": "Diagnostyka i logi",
    "interfejs-terminala-i-ide": "Interfejs terminala i IDE",
}


def pierwsze_zdanie(tekst: str, limit: int = 240) -> str:
    tekst = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", tekst).replace("|", "\\|")
    m = re.match(r"(.+?[.!?])(\s|$)", tekst)
    zdanie = m.group(1) if m else tekst
    return zdanie if len(zdanie) <= limit else zdanie[: limit - 1].rstrip() + "…"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wyjscie", type=Path, default=Path(__file__).resolve().parents[1] / "references" / "indeks-zmiennych.md")
    a = p.parse_args()
    grupy: dict[str, list[dict]] = defaultdict(list)
    for w in zmienne().values():
        grupy[w["kategoria"]].append(w)
    kolejnosc = [k for k in NAZWY if k in grupy] + sorted(k for k in grupy if k not in NAZWY)
    linie = ["# Indeks zmiennych środowiskowych Claude Code", "",
             f"Wygenerowano z `wspolne/indeksy/zmienne.tsv` ({sum(len(v) for v in grupy.values())} zmiennych, "
             "strona `cc:env-vars`, stan 01.10.2026) skryptem `scripts/buduj_indeks_md.py`. Opis — pierwsze "
             "zdanie dokumentacji (oryginał); pełny opis: `scripts/szukaj.py --typ zmienna NAZWA --pelny`.", "",
             "## Spis treści", ""]
    for k in kolejnosc:
        kotwica = NAZWY.get(k, k).lower().replace(" ", "-").replace(",", "").replace(".", "")
        linie.append(f"- [{NAZWY.get(k, k)}](#{kotwica}) — {len(grupy[k])}")
    for k in kolejnosc:
        linie += ["", f"## {NAZWY.get(k, k)}", "", "| Zmienna | Wersja | Opis (dokumentacja) |", "|---|---|---|"]
        for w in sorted(grupy[k], key=lambda x: x["zmienna"]):
            linie.append(f"| `{w['zmienna']}` | {w.get('wersja_w_opisie') or ''} | {pierwsze_zdanie(w.get('opis_en', ''))} |")
    a.wyjscie.write_text("\n".join(linie) + "\n", encoding="utf-8")
    print(f"Zapisano {a.wyjscie} ({len(linie)} wierszy)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
