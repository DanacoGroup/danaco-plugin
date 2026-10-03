#!/usr/bin/env python3
"""Przeszukiwanie referencji Claude Code: klucze ustawień, zmienne, flagi, narzędzia, zdarzenia hooków.

Źródło: indeksy `wspolne/indeksy/*.tsv` zbudowane z lokalnej kopii dokumentacji
(settings-reference, env-vars, cli-reference, tools-reference, hooks) z 01.10.2026.

Użycie:
  szukaj.py FRAZA [--typ klucz|zmienna|flaga|narzedzie|hook|wszystko]
                  [--zasieg "Managed"] [--kategoria NAZWA] [--od-wersji 2.1.280] [--pelny]

Przykłady:
  szukaj.py cache                         # wszystko o cache
  szukaj.py "" --typ klucz --zasieg Managed   # klucze działające tylko w ustawieniach zarządzanych
  szukaj.py "" --typ zmienna --kategoria mcp  # zmienne z kategorii mcp
  szukaj.py "" --typ klucz --od-wersji 2.1.260  # klucze dodane od wersji 2.1.260
  szukaj.py sandbox.network --pelny       # pełne wpisy (typ, domyślna wartość, nadpisania)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_wspolne as cc  # noqa: E402


def pasuje(fraza: str, *pola: str) -> bool:
    fraza = fraza.lower()
    return not fraza or any(fraza in (p or "").lower() for p in pola)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fraza")
    parser.add_argument("--typ", default="wszystko", choices=["klucz", "zmienna", "flaga", "narzedzie", "hook", "wszystko"])
    parser.add_argument("--zasieg", default="")
    parser.add_argument("--kategoria", default="")
    parser.add_argument("--od-wersji", default="")
    parser.add_argument("--pelny", action="store_true")
    a = parser.parse_args()
    trafienia = 0

    if a.typ in ("klucz", "wszystko"):
        for klucz, w in cc.klucze_ustawien().items():
            if not pasuje(a.fraza, klucz, w["co_robi_pl"], w["opis_en"], w["kategoria"]):
                continue
            if a.zasieg and a.zasieg.lower() not in w["zasieg"].lower():
                continue
            if a.kategoria and a.kategoria.lower() not in w["kategoria"].lower():
                continue
            if a.od_wersji and not (w["min_wersja"] and not cc.wersja_mniejsza(w["min_wersja"], a.od_wersji)):
                continue
            trafienia += 1
            wersja = f" ≥{w['min_wersja']}" if w["min_wersja"] else ""
            print(f"[klucz] {klucz}  ({w['zasieg']}{wersja}; {w['obszar'] or '—'}) — {w['co_robi_pl']}")
            if a.pelny:
                for etykieta, pole in (("typ", "typ"), ("domyślnie", "domyslnie"), ("nadpisania", "nadpisania"),
                                       ("uwaga", "uwaga_pl"), ("opis (dokumentacja)", "opis_en"), ("źródło", "zrodlo")):
                    if w.get(pole):
                        print(f"        {etykieta}: {w[pole]}")
    if a.typ in ("zmienna", "wszystko"):
        for nazwa, w in cc.zmienne().items():
            if not pasuje(a.fraza, nazwa, w["opis_en"], w["kategoria"]):
                continue
            if a.kategoria and a.kategoria.lower() not in w["kategoria"].lower():
                continue
            if a.od_wersji and not (w["wersja_w_opisie"] and not cc.wersja_mniejsza(w["wersja_w_opisie"], a.od_wersji)):
                continue
            trafienia += 1
            opis = w["opis_en"] if a.pelny else w["opis_en"][:160] + ("…" if len(w["opis_en"]) > 160 else "")
            print(f"[zmienna] {nazwa}  ({w['kategoria']}) — {opis}")
    if a.typ in ("flaga", "wszystko"):
        for w in cc.flagi():
            if not pasuje(a.fraza, w["flaga"], w["opis_en"]):
                continue
            trafienia += 1
            dopiski = ", ".join(x for x in (f"≥{w['wersja_w_opisie']}" if w["wersja_w_opisie"] else "",
                                            "tylko -p" if w["tylko_p"] else "") if x)
            opis = w["opis_en"] if a.pelny else w["opis_en"][:160] + ("…" if len(w["opis_en"]) > 160 else "")
            print(f"[flaga] {w['flaga']}{f'  ({dopiski})' if dopiski else ''} — {opis}")
    if a.typ in ("narzedzie", "wszystko"):
        for nazwa, w in cc.narzedzia().items():
            if pasuje(a.fraza, nazwa, w["opis_en"]):
                trafienia += 1
                print(f"[narzędzie] {nazwa}  (wymaga zgody: {w['wymaga_zgody']}) — {w['opis_en'][:160]}")
    if a.typ in ("hook", "wszystko"):
        for nazwa, w in cc.zdarzenia_hookow().items():
            if pasuje(a.fraza, nazwa, w["kiedy"], w["uwagi"], w["wzorzec_decyzji"]):
                trafienia += 1
                print(f"[hook] {nazwa} — {w['kiedy']}; matcher: {w['matcher_filtruje']}; blokuje: {w['blokuje_exit2']}; "
                      f"decyzja: {w['wzorzec_decyzji']}" + (f"; uwagi: {w['uwagi']}" if a.pelny else ""))
    print(f"— trafień: {trafienia}", file=sys.stderr)
    return 0 if trafienia else 1


if __name__ == "__main__":
    sys.exit(main())
