#!/usr/bin/env python3
"""Testy orkiestratora bramek jakości (scripts/mass_actions.py).

Uruchomienie:
    python3 tests/test_mass_actions.py
    python3 -m pytest tests/test_mass_actions.py

Testy pracują na KOPII pluginu w katalogu tymczasowym, żeby dało się sprawdzić
zachowanie przy brakującym albo podstawionym walidatorze bez ruszania plików
pluginu. Kontrakt kodów wyjścia: 0 czysto, 2 ostrzeżenia, 3 blokujące,
4 awaria kontroli.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KORZEN_PLUGINU = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

KOD_CZYSTO = 0
KOD_OSTRZEZENIA = 2
KOD_BLOKUJACE = 3
KOD_AWARII = 4

PLIKI_KOPII = (
    "scripts/mass_actions.py",
    "scripts/przechodzenie_repozytorium.py",
    "scripts/konfiguracja_kontroli.py",
    "skills/weryfikatory-dyscypliny/scripts/style_guard.py",
    "skills/standardy-nazewnictwa/scripts/nazwy_guard.py",
    "skills/kontrola-jakosci/scripts/audyt_smieci.py",
    "skills/kodowanie/scripts/quality_gate.sh",
)


class TestMassActions(unittest.TestCase):
    def setUp(self) -> None:
        self.tymczasowy = tempfile.TemporaryDirectory(prefix="mass-actions-test-")
        self.katalog = Path(self.tymczasowy.name)
        self.plugin = self.katalog / "plugin"
        for wzgledna in PLIKI_KOPII:
            cel = self.plugin / wzgledna
            cel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(KORZEN_PLUGINU / wzgledna, cel)
        self.zrodla = self.katalog / "repo"
        self.zrodla.mkdir()

    def tearDown(self) -> None:
        self.tymczasowy.cleanup()

    def orkiestrator(self, *argumenty: str, sciezka_srodowiska: str | None = None) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if sciezka_srodowiska is not None:
            env["PATH"] = sciezka_srodowiska
        return subprocess.run([PYTHON, str(self.plugin / "scripts" / "mass_actions.py"), *argumenty],
                              capture_output=True, text=True, encoding="utf-8", env=env,
                              cwd=str(self.katalog))

    def plik_zrodlowy(self, nazwa: str, tresc: str) -> Path:
        cel = self.zrodla / nazwa
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_text(tresc, encoding="utf-8")
        return cel

    def test_verify_bez_walidatora_nie_daje_zielono(self):
        """Regresja A2-02: brak walidatora to awaria kontroli, nie „czysto”."""
        (self.plugin / "skills/weryfikatory-dyscypliny/scripts/style_guard.py").unlink()
        self.plik_zrodlowy("czysty.py", "wartosc = 1\n")
        wynik = self.orkiestrator("verify", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_AWARII, wynik.stdout)
        self.assertIn("brak walidatora", wynik.stderr)

    def test_verify_katalog_czysty(self):
        self.plik_zrodlowy("czysty.py", "wartosc = 1\n")
        wynik = self.orkiestrator("verify", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout + wynik.stderr)

    def test_verify_z_ostrzezeniem(self):
        self.plik_zrodlowy("kod.py", "# panel MOD-A7\n")
        wynik = self.orkiestrator("verify", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)

    def test_verify_z_naruszeniem_blokujacym(self):
        self.plik_zrodlowy("dlugi.py", "# " + "a" * 400 + "\n")
        wynik = self.orkiestrator("verify", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)

    def test_verify_kod_potomny_poza_kontraktem(self):
        """Regresja A2-17: kod 1 z walidatora to awaria, nie wynik bramki."""
        podstawiony = self.plugin / "skills/weryfikatory-dyscypliny/scripts/style_guard.py"
        podstawiony.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
        self.plik_zrodlowy("czysty.py", "wartosc = 1\n")
        wynik = self.orkiestrator("verify", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_AWARII, wynik.stdout)
        self.assertIn("awaria kontroli", wynik.stdout)

    def test_verify_zly_katalog_audytu_nie_maskuje_wyniku(self):
        wynik = self.orkiestrator("verify", str(self.katalog / "nie-ma"))
        self.assertEqual(wynik.returncode, KOD_AWARII, wynik.stdout)

    def test_quality_gate_bez_powloki(self):
        """Regresja A2-16: brak bash i sh daje komunikat, nie FileNotFoundError."""
        puste = self.katalog / "puste-bin"
        puste.mkdir()
        wynik = self.orkiestrator("quality-gate", str(self.zrodla), sciezka_srodowiska=str(puste))
        self.assertEqual(wynik.returncode, KOD_AWARII, wynik.stdout)
        self.assertIn("brak interpretera powłoki", wynik.stderr)
        self.assertNotIn("Traceback", wynik.stderr)

    def test_quality_gate_bez_skryptu(self):
        (self.plugin / "skills/kodowanie/scripts/quality_gate.sh").unlink()
        wynik = self.orkiestrator("quality-gate", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertIn("brak skryptu", wynik.stderr)

    def test_cleanup_bez_argumentu_nic_nie_usuwa(self):
        """Regresja A2-42: cleanup bez katalogu nie może działać na cwd."""
        smiec = self.plik_zrodlowy("plik.bak", "x")
        wynik = self.orkiestrator("cleanup")
        self.assertNotEqual(wynik.returncode, KOD_CZYSTO)
        self.assertIn("required", wynik.stderr)
        self.assertTrue(smiec.is_file())

    def test_cleanup_bez_zgody_nic_nie_usuwa(self):
        smiec = self.plik_zrodlowy("plik.bak", "x")
        wynik = self.orkiestrator("cleanup", str(self.zrodla))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertIn("--tak-usun", wynik.stderr)
        self.assertTrue(smiec.is_file())

    def test_cleanup_ze_zgoda_usuwa_smieci(self):
        smiec = self.plik_zrodlowy("plik.bak", "x")
        pusty = self.zrodla / "logi"
        pusty.mkdir()
        wynik = self.orkiestrator("cleanup", str(self.zrodla), "--tak-usun")
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout + wynik.stderr)
        self.assertFalse(smiec.exists())
        self.assertTrue(pusty.is_dir(), "pusty katalog roboczy nie może zniknąć bez --usun-puste")


if __name__ == "__main__":
    unittest.main(verbosity=2)
