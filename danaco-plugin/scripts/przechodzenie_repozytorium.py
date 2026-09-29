#!/usr/bin/env python3
"""Jedno miejsce przechodzenia drzewa repozytorium dla kontroli pluginu.

Walidatory (`style_guard.py`, `nazwy_guard.py`) i audyt porządku
(`audyt_smieci.py`) miały trzy różne polityki pomijania katalogów i filtrowały
wyniki PO przejściu całego drzewa, więc w repozytorium z `node_modules` każde
uruchomienie hooka PostToolUse przechodziło drzewo zależności. Tutaj lista jest
jedna, a katalogi są przycinane w trakcie przechodzenia.

Moduł jest importowany przez skrypty paczek przez `sys.path` wyliczony z ich
`__file__`, więc działa niezależnie od katalogu roboczego.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

KATALOGI_POMIJANE = {
    ".git", "node_modules", "target", "dist", "build", "vendor", "__pycache__",
    ".venv", "venv", ".next", ".turbo", "coverage", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".idea",
}


def iteruj_pliki(root: Path, rozszerzenia: set[str] | None = None) -> Iterator[Path]:
    """Pliki w drzewie `root` z przycięciem katalogów zależności i wytworów."""
    for katalog, podkatalogi, nazwy in os.walk(str(root)):
        podkatalogi[:] = sorted(d for d in podkatalogi if d not in KATALOGI_POMIJANE)
        for nazwa in sorted(nazwy):
            sciezka = Path(katalog) / nazwa
            if rozszerzenia is None or sciezka.suffix in rozszerzenia:
                yield sciezka


def iteruj_katalogi(root: Path, zwracaj_przyciete: bool = False) -> Iterator[Path]:
    """Katalogi w drzewie `root`. Katalog z listy pomijanych nie jest przechodzony;
    przy `zwracaj_przyciete` jest zwracany (audyt śmieci musi zobaczyć `__pycache__`,
    a nie wchodzić do jego zawartości)."""
    for katalog, podkatalogi, _nazwy in os.walk(str(root)):
        przyciete = [d for d in podkatalogi if d in KATALOGI_POMIJANE]
        podkatalogi[:] = sorted(d for d in podkatalogi if d not in KATALOGI_POMIJANE)
        nazwy = sorted(podkatalogi + przyciete) if zwracaj_przyciete else podkatalogi
        for nazwa in nazwy:
            yield Path(katalog) / nazwa


def zbierz_pliki(sciezki: list[str], rozszerzenia: set[str]) -> tuple[list[Path], bool]:
    """Pliki wskazane wprost i pliki z katalogów. Drugi element mówi, czy któraś
    ścieżka nie istniała — ciche pominięcie dawałoby w CI fałszywe „0 naruszeń”."""
    wynik: list[Path] = []
    byly_braki = False
    for wpis in sciezki:
        p = Path(wpis)
        if p.is_file():
            wynik.append(p)
        elif p.is_dir():
            wynik.extend(iteruj_pliki(p, rozszerzenia))
        else:
            byly_braki = True
            print(f"[ostrzezenie] ścieżka nie istnieje, pomijam: {wpis}", file=sys.stderr)
    return wynik, byly_braki


def wczytaj_tekst(sciezka: Path) -> tuple[str | None, str | None]:
    """Treść pliku jako UTF-8 albo (None, powód). Końce linii są normalizowane
    do `\\n`, więc plik z CRLF jest sprawdzany tak samo jak z LF."""
    try:
        return sciezka.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return None, ("pliku nie da się odczytać jako UTF-8 - kontrola nie została "
                      "wykonana; zapisz plik w UTF-8")
    except OSError as blad:
        return None, f"pliku nie da się odczytać: {blad}"


if __name__ == "__main__":
    print("przechodzenie_repozytorium.py to moduł wspólny walidatorów - nie ma "
          "własnych poleceń.", file=sys.stderr)
    sys.exit(2)
