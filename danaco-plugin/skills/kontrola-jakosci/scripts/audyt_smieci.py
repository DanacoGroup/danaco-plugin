#!/usr/bin/env python3
"""Audyt śmieci i porządku repozytorium (audyt_smieci.py).

Znajduje w repozytorium pliki i katalogi pasujące do JAWNIE wymienionych wzorców
śmieci (cache kompilatorów, pliki tymczasowe, pliki systemu operacyjnego) oraz
zbiera prosty raport porządku: znaczniki TODO/FIXME i puste katalogi.

Zakres jest ograniczony trzema regułami, bo usunięcie pliku z repozytorium
użytkownika jest nieodwracalne:

1. Domyślnie działa TRYB PODGLĄDU — nic nie jest usuwane; usuwanie włącza `--usun`,
   a przed usunięciem wypisywane jest podsumowanie tego, co zostanie usunięte.
2. Usuwane są wyłącznie pozycje pasujące do `WZORCE_SMIECI_PLIKOW` i
   `KATALOGI_SMIECI`, w drzewie podanego katalogu. Katalogi zależności i wytworów
   (`node_modules`, `.venv`, `.git`, `dist`, `build`, `target`…) nie są ani
   przechodzone, ani czyszczone: ich zawartość nie należy do repozytorium.
3. PUSTE KATALOGI są tylko raportowane. Pusty katalog bywa wymaganym katalogiem
   roboczym aplikacji (`logi/`, `migracje/`), więc jego usunięcie stoi za osobnym
   przełącznikiem `--usun-puste`.

Użycie:
    python3 audyt_smieci.py <katalog>
    python3 audyt_smieci.py <katalog> --usun [--usun-puste]
    python3 audyt_smieci.py <katalog> --json

Kody wyjścia: 0 wynik zebrany (także gdy coś znaleziono - to raport, nie bramka),
3 co najmniej jedno usunięcie zawiodło, 4 zły katalog wejściowy.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

try:
    import przechodzenie_repozytorium
except ImportError as _blad:  # pragma: no cover - niepełna instalacja pluginu
    print(f"BŁĄD: brak modułów wspólnych pluginu (scripts/): {_blad}", file=sys.stderr)
    sys.exit(4)

WZORCE_SMIECI_PLIKOW = [
    "*.pyc", "*.pyo", "*.orig", "*.rej", "*.bak", "*.tmp", "*.swp",
    ".DS_Store", "Thumbs.db",
]
# *.log celowo NIE jest tu domyślnie: w wielu projektach to legalne dzienniki
# aplikacji, nie śmieci budowy - usuwanie ich bez pytania byłoby niebezpieczne.
KATALOGI_SMIECI = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

ROZSZERZENIA_KODU = {".go", ".ts", ".tsx", ".py", ".rs", ".js", ".jsx"}
LIMIT_WYPISANYCH_TODO = 50

WZORZEC_TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")

KOD_NIEUDANEGO_USUNIECIA = 3
KOD_ZLEGO_WEJSCIA = 4


def _znaczniki_todo(sciezka: Path) -> list[str]:
    tresc, _blad = przechodzenie_repozytorium.wczytaj_tekst(sciezka)
    if tresc is None:
        return []
    return [f"{sciezka}:{nr}: {linia.strip()[:100]}"
            for nr, linia in enumerate(tresc.splitlines(), start=1)
            if WZORZEC_TODO.search(linia)]


def znajdz_smieci(root: Path) -> dict:
    """Pozycje pasujące do wzorców śmieci oraz raport porządku."""
    pliki_do_usuniecia: list[str] = []
    katalogi_do_usuniecia: list[str] = []
    puste_katalogi: list[str] = []
    todo_fixme: list[str] = []

    for katalog in przechodzenie_repozytorium.iteruj_katalogi(root, zwracaj_przyciete=True):
        if katalog.name in KATALOGI_SMIECI:
            katalogi_do_usuniecia.append(str(katalog))
            continue
        if katalog.name in przechodzenie_repozytorium.KATALOGI_POMIJANE:
            continue
        try:
            if not any(katalog.iterdir()):
                puste_katalogi.append(str(katalog))
        except OSError:
            continue

    for sciezka in przechodzenie_repozytorium.iteruj_pliki(root):
        if any(sciezka.match(wzorzec) for wzorzec in WZORCE_SMIECI_PLIKOW):
            pliki_do_usuniecia.append(str(sciezka))
        elif sciezka.suffix in ROZSZERZENIA_KODU:
            todo_fixme.extend(_znaczniki_todo(sciezka))

    return {
        "plikiDoUsuniecia": sorted(pliki_do_usuniecia),
        "katalogiDoUsuniecia": sorted(katalogi_do_usuniecia),
        "pusteKatalogi": sorted(puste_katalogi),
        "todoFixme": sorted(todo_fixme),
    }


def _pozycje_do_usuniecia(wynik: dict, usuwaj_puste: bool) -> list[str]:
    pozycje = list(wynik["plikiDoUsuniecia"]) + list(wynik["katalogiDoUsuniecia"])
    if usuwaj_puste:
        pozycje += list(wynik["pusteKatalogi"])
    return pozycje


def usun(wynik: dict, usuwaj_puste: bool = False) -> tuple[int, int]:
    """Usuwa znalezione śmieci. Zwraca (usunięte, nieudane)."""
    usuniete = 0
    nieudane = 0

    for plik in wynik["plikiDoUsuniecia"]:
        try:
            Path(plik).unlink()
            usuniete += 1
        except OSError as blad:
            nieudane += 1
            print(f"nie udało się usunąć {plik}: {blad}", file=sys.stderr)

    for katalog in wynik["katalogiDoUsuniecia"]:
        try:
            shutil.rmtree(katalog)
            usuniete += 1
        except OSError as blad:
            nieudane += 1
            print(f"nie udało się usunąć {katalog}: {blad}", file=sys.stderr)

    if usuwaj_puste:
        # Od najgłębszych, bo usunięcie plików wyżej mogło dopiero co osierocić
        # katalog nadrzędny.
        for katalog in sorted(wynik["pusteKatalogi"], key=len, reverse=True):
            try:
                Path(katalog).rmdir()
                usuniete += 1
            except OSError as blad:
                nieudane += 1
                print(f"nie udało się usunąć {katalog}: {blad}", file=sys.stderr)

    return usuniete, nieudane


def wypisz_raport(wynik: dict, args: argparse.Namespace) -> None:
    print(f"Pliki-śmieci: {len(wynik['plikiDoUsuniecia'])}")
    for plik in wynik["plikiDoUsuniecia"]:
        print(f"  {plik}")
    print(f"Katalogi-śmieci (cache): {len(wynik['katalogiDoUsuniecia'])}")
    for katalog in wynik["katalogiDoUsuniecia"]:
        print(f"  {katalog}")
    print(f"Puste katalogi (nie usuwane bez --usun-puste): {len(wynik['pusteKatalogi'])}")
    for katalog in wynik["pusteKatalogi"]:
        print(f"  {katalog}")
    print(f"Znaczniki TODO/FIXME/XXX/HACK: {len(wynik['todoFixme'])}")
    for znacznik in wynik["todoFixme"][:LIMIT_WYPISANYCH_TODO]:
        print(f"  {znacznik}")
    if args.usun:
        print(f"\nUsunięto pozycji: {wynik['usunieto']}, nieudanych: {wynik['nieudane']}")
    else:
        print("\nTryb podglądu - nic nie usunięto. Użyj --usun, żeby usunąć wymienione "
              "pozycje; puste katalogi dodatkowo wymagają --usun-puste.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("katalog", type=Path, help="katalog do przejrzenia")
    parser.add_argument("--usun", action="store_true",
                        help="usuwa pozycje pasujące do wzorców śmieci (domyślnie tryb podglądu)")
    parser.add_argument("--usun-puste", dest="usun_puste", action="store_true",
                        help="razem z --usun usuwa też puste katalogi (bywają wymagane przez aplikację)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.katalog.is_dir():
        print(f"nie ma takiego katalogu: {args.katalog}", file=sys.stderr)
        return KOD_ZLEGO_WEJSCIA

    wynik = znajdz_smieci(args.katalog)
    nieudane = 0

    if args.usun:
        pozycje = _pozycje_do_usuniecia(wynik, args.usun_puste)
        print(f"Do usunięcia w {args.katalog}: {len(pozycje)} pozycji "
              f"(pliki: {len(wynik['plikiDoUsuniecia'])}, katalogi-cache: "
              f"{len(wynik['katalogiDoUsuniecia'])}, puste katalogi: "
              f"{len(wynik['pusteKatalogi']) if args.usun_puste else 0}).")
        usuniete, nieudane = usun(wynik, args.usun_puste)
        wynik["usunieto"] = usuniete
        wynik["nieudane"] = nieudane
    elif args.usun_puste:
        print("--usun-puste działa tylko razem z --usun; nic nie usunięto.", file=sys.stderr)

    if args.json:
        print(json.dumps(wynik, ensure_ascii=False, indent=2))
    else:
        wypisz_raport(wynik, args)

    return KOD_NIEUDANEGO_USUNIECIA if nieudane else 0


if __name__ == "__main__":
    sys.exit(main())
