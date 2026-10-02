#!/usr/bin/env python3
"""Hook PostToolUse danaco-plugin: po zapisie pliku uruchamia walidator dyscypliny
(`style_guard`) i nazewnictwa (`nazwy_guard`).

Wejście: zdarzenie PostToolUse jako JSON na stdin. Naruszenia trafiają na standardowe
wyjście błędów, a hook kończy się kodem 2 — w tym zdarzeniu Claude Code przekazuje raport
do kontekstu tury, nie blokując narzędzia (plik już został zapisany). Plik bez naruszeń i
plik spoza zakresu kontroli kończą się kodem 0 bez wyjścia.

Fail-open: każdy błąd hooka (zły JSON, brak modułów, zła konfiguracja) kończy się kodem 0 —
usterka kontroli nie może przeszkadzać w pracy. Walidatory lokalizujemy po `CLAUDE_PLUGIN_ROOT`,
a przy jego braku po położeniu tego pliku, więc hook działa też bez tej zmiennej.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path


def _zaladuj(nazwa: str, sciezka: Path):
    spec = importlib.util.spec_from_file_location(nazwa, sciezka)
    if spec is None or spec.loader is None:
        raise ImportError(nazwa)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[nazwa] = modul
    spec.loader.exec_module(modul)
    return modul


def main() -> int:
    try:
        zdarzenie = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(zdarzenie, dict):
        return 0
    wejscie = zdarzenie.get("tool_input")
    if not isinstance(wejscie, dict):
        return 0
    sciezka = wejscie.get("file_path") or wejscie.get("notebook_path") or wejscie.get("path")
    if not isinstance(sciezka, str) or not sciezka:
        return 0
    plik = Path(sciezka)

    korzen = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
    sys.path.insert(0, str(korzen / "scripts"))
    try:
        style = _zaladuj("style_guard", korzen / "skills" / "weryfikatory-dyscypliny" / "scripts" / "style_guard.py")
        nazwy = _zaladuj("nazwy_guard", korzen / "skills" / "standardy-nazewnictwa" / "scripts" / "nazwy_guard.py")
        import konfiguracja_kontroli
    except BaseException:  # noqa: BLE001 — niepełna instalacja nie może wywrócić hooka
        return 0

    if plik.suffix not in (set(style.ROZSZERZENIA_KODU) | set(nazwy.ROZSZERZENIA)):
        return 0

    wiersze: list[str] = []
    try:
        cfg = konfiguracja_kontroli.wczytaj(None, [str(plik)])
        naruszenia = [(n.regula, n.plik, n.linia, n.tresc, n.blokujace) for n in style.sprawdz_plik(plik, cfg)]
        naruszenia += [(n["regula"], n["plik"], n["linia"], n["tresc"], n["blokujace"])
                       for n in nazwy.sprawdz_plik(plik, cfg)]
    except BaseException:  # noqa: BLE001 — także SystemExit z błędu konfiguracji (kod 4)
        return 0

    for regula, p, linia, tresc, blokujace in naruszenia:
        waga = "BLOKUJACE" if blokujace else "ostrzezenie"
        wiersze.append(f"[{waga}] {p}:{linia}: {regula}: {tresc}")
    if not wiersze:
        return 0
    print("\n".join(wiersze), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
