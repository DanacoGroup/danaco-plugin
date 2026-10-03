#!/usr/bin/env python3
"""Składa instrukcję systemową produktu z części stałej i zmiennej ze znacznikiem granicy cache.

Część stała (tożsamość, zasady, opisy narzędzi, katalogi — identyczna dla wszystkich
rozmów) trafia nad wiersz `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__`, część zmienna (klient,
plan, data, strefa, fragment aplikacji) pod niego. CLI ≥2.1.275 dzieli instrukcję na dwa
bloki z osobnymi punktami cache (tylko przy bezpośrednim API Anthropic / Claude Platform
on AWS; przez bramę LLM, Bedrock, Vertex, Foundry — jeden blok, znacznik usunięty).

Użycie:
  buduj_instrukcje.py --stala stala.md [--zmienna zmienna.md] --wyjscie instrukcja.txt
                      [--podstaw KLUCZ=WARTOSC]…   (podstawia {{KLUCZ}} w części zmiennej)
Wypisuje rozmiary, ostrzeżenia i zalecane flagi uruchomienia.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ZNACZNIK = "__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stala", type=Path, required=True)
    p.add_argument("--zmienna", type=Path)
    p.add_argument("--wyjscie", type=Path, required=True)
    p.add_argument("--podstaw", action="append", default=[])
    a = p.parse_args()
    stala = a.stala.read_text(encoding="utf-8").rstrip("\n")
    zmienna = a.zmienna.read_text(encoding="utf-8").strip("\n") if a.zmienna else ""
    for para in a.podstaw:
        klucz, _, wartosc = para.partition("=")
        zmienna = zmienna.replace("{{" + klucz + "}}", wartosc)
    uwagi = []
    if ZNACZNIK in stala or ZNACZNIK in zmienna:
        uwagi.append("BŁĄD: znacznik wpisany ręcznie w części — skrypt dodaje go sam (pierwsze wystąpienie dzieli)")
    if re.search(r"\{\{[A-Z_]+\}\}", zmienna):
        uwagi.append(f"BŁĄD: niepodstawione pola: {sorted(set(re.findall(r'{{[A-Z_]+}}', zmienna)))}")
    if re.search(r"\d{4}-\d{2}-\d{2}|\b\d{1,2}:\d{2}\b", stala):
        uwagi.append("uwaga: część stała zawiera datę lub godzinę — każda zmiana unieważni cache wszystkich rozmów")
    tekst = stala + ("\n" + ZNACZNIK + "\n" + zmienna if zmienna else "") + "\n"
    a.wyjscie.write_text(tekst, encoding="utf-8")
    skrot = hashlib.sha256(stala.encode()).hexdigest()[:12]
    print(f"Zapisano {a.wyjscie}: część stała {len(stala)} znaków (skrót {skrot}), zmienna {len(zmienna)} znaków")
    if len(tekst) > 100_000:
        uwagi.append("uwaga: instrukcja > 100 000 znaków — sprawdź koszt każdego zapisu cache")
    for u in uwagi:
        print(u)
    print("Zalecane flagi:")
    print(f"  --system-prompt-file {a.wyjscie} --system-prompt-snapshot off   # ≥2.1.257; znacznik ≥2.1.275")
    print("Skrót części stałej pozwala sprawdzić, czy kolejne wydania zmieniają prefiks cache.")
    return 1 if any(u.startswith("BŁĄD") for u in uwagi) else 0


if __name__ == "__main__":
    sys.exit(main())
