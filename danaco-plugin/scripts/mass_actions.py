#!/usr/bin/env python3
"""Orkiestrator masowych weryfikacji i akcji Danaco (mass_actions.py).

Spina walidatory rozsiane po paczkach skilli tego pluginu w jedno polecenie,
tak żeby jedna komenda na koniec tury albo w pre-commit/CI dawała pełny obraz
stanu repozytorium: dyscyplina kodu i komentarzy, nazewnictwo, porządek
(śmieci, TODO), oraz - jeśli dostępne narzędzia budowy - bramkę jakości.

Świadomie NIE wywołuje tu skryptów specyficznych dla kontraktu Danaco Console
(contract_tool.py, modes_tool.py, channel_tool.py, workflow_tool.py,
tauri_check.py) na sztywno - te żyją w swoich paczkach i mają własne kontrakty
wejścia (ścieżka do `contract.json` itp.), które ten ogólny orkiestrator by
musiał zgadywać. `verify` obejmuje kontrole uniwersalne dla dowolnego
repozytorium Danaco; kontrole specyficzne dla kontraktu uruchamiaj z ich
własnych paczek, tak jak opisano w ich SKILL.md.

Polecenia:
    verify <katalog>                   - style_guard, nazwy_guard i audyt śmieci
                                         (tryb podglądu), jeden raport i jeden kod
    cleanup <katalog> --tak-usun       - audyt_smieci.py --usun; katalog i zgoda są
                                         obowiązkowe, bo usuwanie jest nieodwracalne
    quality-gate <katalog>             - kodowanie/scripts/quality_gate.sh

Kody wyjścia (jednakowe dla wszystkich poleceń): 0 czysto, 2 same ostrzeżenia,
3 co najmniej jedno naruszenie blokujące (dla `quality-gate` także: krok budowy
albo testów zawiódł), 4 AWARIA KONTROLI - brak walidatora, brak powłoki,
przekroczony limit czasu, nierozpoznany projekt albo kod potomny poza
kontraktem. Kod 4 nigdy nie znaczy „czysto”: bramka, która nie wykonała
kontroli, nie ma prawa orzec, że repozytorium jest w porządku.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

KORZEN_PLUGINU = Path(__file__).resolve().parent.parent

KOD_CZYSTO = 0
KOD_OSTRZEZENIA = 2
KOD_BLOKUJACE = 3
KOD_AWARII = 4
KODY_W_KONTRAKCIE = {KOD_CZYSTO, KOD_OSTRZEZENIA, KOD_BLOKUJACE}

LIMIT_CZASU_WALIDATORA_S = 900

SKRYPT_STYLU = "skills/weryfikatory-dyscypliny/scripts/style_guard.py"
SKRYPT_NAZW = "skills/standardy-nazewnictwa/scripts/nazwy_guard.py"
SKRYPT_SMIECI = "skills/kontrola-jakosci/scripts/audyt_smieci.py"
SKRYPT_BRAMKI = "skills/kodowanie/scripts/quality_gate.sh"


def sciezka_skryptu(wzgledna: str) -> Path:
    return KORZEN_PLUGINU / wzgledna


def uruchom_python(skrypt: Path, argumenty: list[str]) -> int:
    """Kod wyjścia walidatora. Brak skryptu i przekroczony limit czasu to AWARIA,
    nie wynik „czysto”: inaczej niepełna instalacja pluginu dawałaby zieloną
    bramkę bez jednej wykonanej kontroli."""
    if not skrypt.exists():
        print(f"BŁĄD: brak walidatora {skrypt} - bramka nie może orzec, że jest czysto",
              file=sys.stderr)
        return KOD_AWARII
    try:
        return subprocess.run([sys.executable, str(skrypt), *argumenty],
                              timeout=LIMIT_CZASU_WALIDATORA_S).returncode
    except subprocess.TimeoutExpired:
        print(f"BŁĄD: {skrypt.name} przekroczył limit czasu {LIMIT_CZASU_WALIDATORA_S} s",
              file=sys.stderr)
        return KOD_AWARII
    except OSError as blad:
        print(f"BŁĄD: nie udało się uruchomić {skrypt.name}: {blad}", file=sys.stderr)
        return KOD_AWARII


def polecenie_verify(katalog: str) -> int:
    kody: list[int] = []

    print("### Dyscyplina kodu i komentarzy (style_guard) ###")
    kody.append(uruchom_python(sciezka_skryptu(SKRYPT_STYLU), [katalog]))

    print("\n### Standard nazewnictwa (nazwy_guard) ###")
    kody.append(uruchom_python(sciezka_skryptu(SKRYPT_NAZW), [katalog]))

    print("\n### Porządek repozytorium (audyt_smieci, tryb podglądu) ###")
    kod_smieci = uruchom_python(sciezka_skryptu(SKRYPT_SMIECI), [katalog])
    # Audyt śmieci jest raportem, nie bramką: znalezione pozycje nie podnoszą
    # poziomu wyniku. Jego awaria (brak skryptu, zły katalog) podnosi.
    if kod_smieci == KOD_AWARII:
        kody.append(KOD_AWARII)

    najgorszy = max(kody) if kody else KOD_CZYSTO
    if najgorszy not in KODY_W_KONTRAKCIE:
        print(f"\n### Wynik zbiorczy: awaria kontroli (kod potomny {najgorszy}) ###")
        return KOD_AWARII
    print(f"\n### Wynik zbiorczy: kod {najgorszy} ###")
    return najgorszy


def polecenie_cleanup(katalog: str, potwierdzone: bool) -> int:
    if not potwierdzone:
        print("cleanup usuwa pliki nieodwracalnie - powtórz polecenie z --tak-usun. "
              "Podgląd tego, co zostanie usunięte: mass_actions.py verify "
              f"{katalog}", file=sys.stderr)
        return KOD_AWARII
    skrypt = sciezka_skryptu(SKRYPT_SMIECI)
    if not skrypt.exists():
        print(f"BŁĄD: brak skryptu {skrypt}", file=sys.stderr)
        return KOD_AWARII
    return uruchom_python(skrypt, [katalog, "--usun"])


def polecenie_quality_gate(katalog: str) -> int:
    skrypt = sciezka_skryptu(SKRYPT_BRAMKI)
    if not skrypt.exists():
        print(f"BŁĄD: brak skryptu {skrypt}", file=sys.stderr)
        return KOD_AWARII
    powloka = shutil.which("bash") or shutil.which("sh")
    if not powloka:
        print("BŁĄD: brak interpretera powłoki (bash, sh) - bramka jakości nie "
              "została uruchomiona", file=sys.stderr)
        return KOD_AWARII
    try:
        kod = subprocess.run([powloka, str(skrypt), katalog],
                             timeout=LIMIT_CZASU_WALIDATORA_S).returncode
    except subprocess.TimeoutExpired:
        print(f"BŁĄD: bramka jakości przekroczyła limit czasu {LIMIT_CZASU_WALIDATORA_S} s",
              file=sys.stderr)
        return KOD_AWARII
    except OSError as blad:
        print(f"BŁĄD: nie udało się uruchomić bramki jakości: {blad}", file=sys.stderr)
        return KOD_AWARII
    # quality_gate.sh ma własny kontrakt: 0 przeszło, 1 krok zawiódł, 4 nie ma
    # czego uruchomić. Kod 1 to naruszenie blokujące bramki, nie awaria narzędzia.
    if kod == 1:
        return KOD_BLOKUJACE
    return kod if kod in KODY_W_KONTRAKCIE or kod == KOD_AWARII else KOD_AWARII


def zbuduj_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    podpolecenia = parser.add_subparsers(dest="polecenie", required=True)

    for nazwa in ("verify", "quality-gate"):
        p = podpolecenia.add_parser(nazwa)
        p.add_argument("katalog", nargs="?", default=".")

    p = podpolecenia.add_parser("cleanup")
    p.add_argument("katalog", help="katalog do wyczyszczenia (obowiązkowy)")
    p.add_argument("--tak-usun", dest="tak_usun", action="store_true",
                   help="zgoda na nieodwracalne usunięcie znalezionych śmieci")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = zbuduj_parser().parse_args(argv)

    if args.polecenie == "verify":
        return polecenie_verify(args.katalog)
    if args.polecenie == "cleanup":
        return polecenie_cleanup(args.katalog, args.tak_usun)
    if args.polecenie == "quality-gate":
        return polecenie_quality_gate(args.katalog)
    return KOD_AWARII


if __name__ == "__main__":
    sys.exit(main())
