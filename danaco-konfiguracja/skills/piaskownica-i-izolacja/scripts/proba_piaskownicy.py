#!/usr/bin/env python3
"""Próba piaskownicy Bash: zestaw poleceń wykonanych przez CLI według pliku ustawień.

Dla każdego testu atrapa API zleca jedno polecenie Bash, CLI uruchamia je w piaskownicy
z podanego pliku, a skrypt ocenia wynik względem oczekiwania:
  zapis-w-katalogu     zapis w katalogu roboczym              oczekiwane: dozwolone
  zapis-poza           zapis w katalogu domowym próby         oczekiwane: zablokowane
  domena-dozwolona     curl do pierwszej domeny z allowedDomains  oczekiwane: dozwolone
  domena-obca          curl do example.org (spoza listy)      oczekiwane: zablokowane
  odczyt-sekretu       cat ~/.ssh/klucz_proby (plik atrapy)   oczekiwane: zablokowane, gdy ~/.ssh w denyRead/credentials
  zmienna-poswiadczen  długość zmiennej z credentials.envVars oczekiwane: 0 przy deny
Wynik: tabela OK / NIEZGODNE / BŁĄD PIASKOWNICY oraz komunikaty CLI.

Użycie:
  proba_piaskownicy.py --settings plik.json [--tryb dontAsk] [--cli /sciezka/claude] [--bez-sieci]

Wymaga: CLI Claude Code, bwrap i socat na Linuksie. Nie używa modelu ani konta; `curl`
łączy się naprawdę z domeną dozwoloną (pomiń opcją --bez-sieci).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]


def uruchom(cli: str, ustawienia: Path, tryb: str, polecenie: str, katalog: Path, nazwa: str,
            srodowisko: list[str]) -> dict:
    scenariusz = katalog / f"{nazwa}.json"
    scenariusz.write_text(json.dumps([{"narzedzie": "Bash", "wejscie": {"command": polecenie, "description": nazwa}},
                                      {"tekst": "koniec"}]))
    argv = [sys.executable, str(KORZEN / "scripts" / "proba_cli.py"), "--json", "--katalog", str(katalog / nazwa),
            "--scenariusz", str(scenariusz), "--plik-w-domu", ".ssh/klucz_proby=ATRAPA-KLUCZA"]
    for para in srodowisko:
        argv += ["--srodowisko", para]
    if cli:
        argv += ["--cli", cli]
    argv += ["--", "--permission-mode", tryb, "--settings", str(ustawienia)]
    wynik = subprocess.run(argv, capture_output=True, text=True)
    try:
        return json.loads(wynik.stdout)
    except json.JSONDecodeError:
        return {"blad": wynik.stdout[-400:] + wynik.stderr[-400:]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--tryb", default="dontAsk")
    parser.add_argument("--cli", default=os.environ.get("CLAUDE_BIN", ""))
    parser.add_argument("--bez-sieci", action="store_true")
    a = parser.parse_args()
    ustawienia = json.loads(a.settings.read_text())
    piaskownica = ustawienia.get("sandbox") or {}
    if not piaskownica.get("enabled"):
        print("Plik nie włącza piaskownicy (sandbox.enabled) — próba nie ma sensu.")
        return 2
    siec = piaskownica.get("network") or {}
    domeny = [d for d in siec.get("allowedDomains", []) if "*" not in d and ":" not in d]
    odmowy_odczytu = (piaskownica.get("filesystem") or {}).get("denyRead", []) + \
        [f.get("path", "") for f in (piaskownica.get("credentials") or {}).get("files", []) if f.get("mode") == "deny"]
    ssh_chronione = any(p.rstrip("/").endswith(".ssh") or p in ("~", "~/") for p in odmowy_odczytu)
    zmienne = [z["name"] for z in (piaskownica.get("credentials") or {}).get("envVars", []) if z.get("mode") == "deny"]

    testy = [("zapis-w-katalogu", "touch plik_proby && echo ZAPIS-OK", "dozwolone"),
             ("zapis-poza", "touch ~/poza_proby && echo ZAPIS-POZA-OK", "zablokowane")]
    if not a.bez_sieci:
        if domeny:
            testy.append(("domena-dozwolona", f"curl -sS -m 15 -o /dev/null -w '%{{http_code}}' https://{domeny[0]}/",
                          "dozwolone"))
        testy.append(("domena-obca", "curl -sS -m 15 -o /dev/null -w '%{http_code}' https://example.org/", "zablokowane"))
    testy.append(("odczyt-sekretu", "cat ~/.ssh/klucz_proby", "zablokowane" if ssh_chronione else "dozwolone"))
    srodowisko = []
    if zmienne:
        srodowisko = [f"{zmienne[0]}=atrapa-wartosci"]
        testy.append(("zmienna-poswiadczen", f"echo DLUGOSC=${{#{zmienne[0]}}}", "zablokowane"))

    katalog = Path(tempfile.mkdtemp(prefix="pp-"))
    print(f"Plik: {a.settings}  tryb: {a.tryb}  katalog: {katalog}")
    niezgodne = 0
    for numer, (nazwa, polecenie, oczekiwane) in enumerate(testy, 1):
        raport = uruchom(a.cli, a.settings.resolve(), a.tryb, polecenie, katalog, f"t{numer}",
                         srodowisko if nazwa == "zmienna-poswiadczen" else [])
        wyniki = [t for t in raport.get("teksty", []) if t.startswith("[tool_result")]
        tekst = " ".join(wyniki)
        if any(z in tekst for z in ("apply-seccomp", "bwrap:", "failed to initialize")) or raport.get("blad"):
            stan, faktyczne = "BŁĄD PIASKOWNICY", "—"
        else:
            if nazwa == "zmienna-poswiadczen":
                faktyczne = "zablokowane" if "DLUGOSC=0" in tekst else "dozwolone"
            elif nazwa.startswith("domena"):
                faktyczne = "dozwolone" if "BŁĄD" not in tekst and "000" not in tekst else "zablokowane"
            else:
                faktyczne = "zablokowane" if "BŁĄD" in tekst else "dozwolone"
            stan = "OK" if faktyczne == oczekiwane else "NIEZGODNE"
        niezgodne += stan != "OK"
        print(f"{stan:<17} {nazwa:<20} oczekiwane: {oczekiwane:<12} faktyczne: {faktyczne}")
        for w in wyniki:
            print(f"    {w[:220]}")
    return 1 if niezgodne else 0


if __name__ == "__main__":
    sys.exit(main())
