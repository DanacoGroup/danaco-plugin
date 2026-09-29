#!/usr/bin/env python3
"""Instalator komponentów shadcn/ui (shadcn_add.py).

Dodaje komponenty shadcn/ui do projektu, obsługując zależności przez CLI shadcn.
Wersja narzędzia jest brana z `package.json` projektu, ale przyjmowany jest
WYŁĄCZNIE czysty numer semver: `npx pakiet@specyfikator` uruchamia także pakiet
wskazany tagiem, adresem URL albo skrótem repozytorium, więc plik danych w
repozytorium mógłby zdecydować, jaki obcy kod zostanie pobrany i wykonany.

Użycie:
    python3 shadcn_add.py button card
    python3 shadcn_add.py --all --overwrite
    python3 shadcn_add.py --list

Kody wyjścia: 0 powodzenie, 1 niepowodzenie.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

WERSJA_DOMYSLNA = "2.3.0"
WZORZEC_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
LIMIT_CZASU_NPX_S = 600


class ShadcnInstaller:
    """Instalacja komponentów shadcn/ui w projekcie."""

    def __init__(self, project_root: Optional[Path] = None, dry_run: bool = False):
        self.project_root = project_root or Path.cwd()
        self.dry_run = dry_run
        self.components_json = self.project_root / "components.json"

    def check_shadcn_config(self) -> bool:
        """Czy shadcn jest zainicjowany w projekcie (istnieje components.json)."""
        return self.components_json.exists()

    def get_installed_components(self) -> List[str]:
        """Nazwy komponentów już obecnych w katalogu `ui`."""
        if not self.check_shadcn_config():
            return []

        try:
            config = json.loads(self.components_json.read_text(encoding="utf-8"))
            components_dir = self.project_root / config.get("aliases", {}).get(
                "components", "components"
            ).replace("@/", "")
            ui_dir = components_dir / "ui"
            if not ui_dir.exists():
                return []
            return [f.stem for f in ui_dir.glob("*.tsx") if f.is_file()]
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, KeyError, OSError):
            return []

    def _get_shadcn_version(self) -> str:
        """Wersja shadcn z package.json; przyjmowany jest wyłącznie czysty semver."""
        pkg_json = self.project_root / "package.json"
        if not pkg_json.exists():
            return WERSJA_DOMYSLNA
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            return WERSJA_DOMYSLNA
        if not isinstance(pkg, dict):
            return WERSJA_DOMYSLNA
        for section in ("dependencies", "devDependencies"):
            sekcja = pkg.get(section)
            wartosc = sekcja.get("shadcn") if isinstance(sekcja, dict) else None
            if not isinstance(wartosc, str) or not wartosc.strip():
                continue
            kandydat = wartosc.lstrip("^~>=< ").split()[0]
            if WZORZEC_SEMVER.match(kandydat):
                return kandydat
            print(f"Pomijam nieznany specyfikator wersji shadcn {wartosc!r} z {section} "
                  f"- używam {WERSJA_DOMYSLNA}", file=sys.stderr)
        return WERSJA_DOMYSLNA

    def _npx(self) -> Optional[str]:
        """Ścieżka do npx. Na Windows to plik `npx.cmd`, którego CreateProcess nie
        uruchomi bez rozszerzenia."""
        nazwy = ("npx.cmd", "npx") if sys.platform.startswith("win") else ("npx",)
        for nazwa in nazwy:
            sciezka = shutil.which(nazwa)
            if sciezka:
                return sciezka
        return None

    def _uruchom(self, argumenty: List[str], opis: str) -> tuple[bool, str]:
        exe = self._npx()
        if not exe:
            return False, "nie znaleziono npx - upewnij się, że Node.js jest zainstalowany"
        try:
            wynik = subprocess.run(
                [exe, *argumenty],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=LIMIT_CZASU_NPX_S,
            )
        except subprocess.CalledProcessError as blad:
            return False, f"nie udało się {opis}: {blad.stderr or blad.stdout or blad}"
        except subprocess.TimeoutExpired:
            return False, (f"nie udało się {opis}: npx przekroczył limit czasu "
                           f"{LIMIT_CZASU_NPX_S} s (prawdopodobnie czeka na pytanie interaktywne)")
        except OSError as blad:
            return False, f"nie udało się uruchomić npx: {blad}"
        komunikat = f"gotowe: {opis}"
        if wynik.stdout:
            komunikat += f"\n\nWyjście:\n{wynik.stdout}"
        return True, komunikat

    def _polecenie(self, komponenty: List[str], overwrite: bool, wszystkie: bool) -> List[str]:
        wersja = self._get_shadcn_version()
        polecenie = [f"shadcn@{wersja}", "add"]
        polecenie += ["--all"] if wszystkie else list(komponenty)
        if overwrite:
            polecenie.append("--overwrite")
        return polecenie

    def add_components(self, components: List[str], overwrite: bool = False) -> tuple[bool, str]:
        """Dodaje wymienione komponenty. Zwraca (powodzenie, komunikat)."""
        if not components:
            return False, "nie podano komponentów"

        if not self.check_shadcn_config():
            return False, "shadcn nie jest zainicjowany - uruchom najpierw 'npx shadcn@latest init'"

        installed = self.get_installed_components()
        already_installed = [c for c in components if c in installed]
        if already_installed and not overwrite:
            return False, (f"komponenty już zainstalowane: {', '.join(already_installed)}. "
                           "Użyj --overwrite, żeby zainstalować ponownie")

        polecenie = self._polecenie(components, overwrite, wszystkie=False)
        if self.dry_run:
            return True, f"uruchomiłbym: npx {' '.join(polecenie)}"
        return self._uruchom(polecenie, f"dodać komponenty: {', '.join(components)}")

    def add_all_components(self, overwrite: bool = False) -> tuple[bool, str]:
        """Dodaje wszystkie dostępne komponenty. Zwraca (powodzenie, komunikat)."""
        if not self.check_shadcn_config():
            return False, "shadcn nie jest zainicjowany - uruchom najpierw 'npx shadcn@latest init'"

        polecenie = self._polecenie([], overwrite, wszystkie=True)
        if self.dry_run:
            return True, f"uruchomiłbym: npx {' '.join(polecenie)}"
        return self._uruchom(polecenie, "dodać wszystkie komponenty")

    def list_installed(self) -> tuple[bool, str]:
        """Lista zainstalowanych komponentów."""
        if not self.check_shadcn_config():
            return False, "shadcn nie jest zainicjowany"
        installed = self.get_installed_components()
        if not installed:
            return True, "brak zainstalowanych komponentów"
        return True, "zainstalowane komponenty:\n" + "\n".join(f"  - {c}" for c in sorted(installed))


def zbuduj_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dodaje komponenty shadcn/ui do projektu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  python3 shadcn_add.py button
  python3 shadcn_add.py button card dialog
  python3 shadcn_add.py --all
  python3 shadcn_add.py button --overwrite
  python3 shadcn_add.py button card --dry-run
  python3 shadcn_add.py --list
        """,
    )
    parser.add_argument("components", nargs="*", help="nazwy komponentów do dodania")
    parser.add_argument("--all", action="store_true", help="dodaj wszystkie dostępne komponenty")
    parser.add_argument("--overwrite", action="store_true", help="nadpisz istniejące komponenty")
    parser.add_argument("--dry-run", action="store_true", help="pokaż polecenie bez uruchamiania")
    parser.add_argument("--list", action="store_true", help="wypisz zainstalowane komponenty")
    parser.add_argument("--project-root", type=Path,
                        help="korzeń projektu (domyślnie katalog bieżący)")
    return parser


def main() -> int:
    args = zbuduj_parser().parse_args()

    installer = ShadcnInstaller(project_root=args.project_root, dry_run=args.dry_run)

    if args.list:
        powodzenie, komunikat = installer.list_installed()
    elif args.all:
        powodzenie, komunikat = installer.add_all_components(overwrite=args.overwrite)
    elif not args.components:
        zbuduj_parser().print_help()
        return 1
    else:
        powodzenie, komunikat = installer.add_components(args.components, overwrite=args.overwrite)

    print(komunikat)
    return 0 if powodzenie else 1


if __name__ == "__main__":
    sys.exit(main())
