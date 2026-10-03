#!/usr/bin/env python3
"""Analiza statyczna migracji SQL: wypisuje flagi ryzyka z plikiem i wierszem.

Użycie: analizuj_migracje.py KATALOG
Kod wyjścia 0 zawsze (to raport, nie bramka); flagi opisuje references/ryzyka.md.
"""
import re
import sys
from pathlib import Path

WZORCE = {
    "DROP_COLUMN": re.compile(r"\bDROP\s+COLUMN\b", re.I),
    "NOT_NULL_BEZ_DOMYSLNEJ": re.compile(r"\bADD\s+COLUMN\b(?!.*\bDEFAULT\b).*\bNOT\s+NULL\b", re.I),
    "RENAME": re.compile(r"\bRENAME\s+(COLUMN|TO)\b", re.I),
    "INDEX_BEZ_CONCURRENTLY": re.compile(r"\bCREATE\s+(UNIQUE\s+)?INDEX\b(?!\s+CONCURRENTLY)", re.I),
}

katalog = Path(sys.argv[1] if len(sys.argv) > 1 else "migrations")
pliki = sorted(katalog.rglob("*.sql"))
if not pliki:
    print(f"Brak plików .sql w {katalog}")
for plik in pliki:
    tekst = plik.read_text(encoding="utf-8", errors="replace")
    for numer, linia in enumerate(tekst.splitlines(), 1):
        for flaga, wzorzec in WZORCE.items():
            if wzorzec.search(linia):
                print(f"{plik}:{numer}: {flaga}: {linia.strip()[:100]}")
    if not re.search(r"--\s*down|\bdown\b", tekst, re.I):
        print(f"{plik}:1: BRAK_DOWN")
