#!/usr/bin/env python3
"""Testy audytu porządku repozytorium (skills/kontrola-jakosci/scripts/audyt_smieci.py).

Uruchomienie:
    python3 tests/test_audyt_smieci.py
    python3 -m pytest tests/test_audyt_smieci.py

Narzędzie usuwa pliki nieodwracalnie, więc testy sprawdzają przede wszystkim to,
czego usunąć NIE WOLNO: katalogów roboczych aplikacji, zawartości zależności
i katalogu `.git`. Wszystko dzieje się w katalogu tymczasowym.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KORZEN_PLUGINU = Path(__file__).resolve().parent.parent
AUDYT = KORZEN_PLUGINU / "skills" / "kontrola-jakosci" / "scripts" / "audyt_smieci.py"
PYTHON = sys.executable

KOD_CZYSTO = 0
KOD_NIEUDANEGO_USUNIECIA = 3
KOD_ZLEGO_WEJSCIA = 4


class TestAudytSmieci(unittest.TestCase):
    def setUp(self) -> None:
        self.tymczasowy = tempfile.TemporaryDirectory(prefix="audyt-smieci-test-")
        self.repo = Path(self.tymczasowy.name) / "repo"
        for katalog in ("logi", "migracje", "src", "node_modules/pakiet/__pycache__",
                        ".venv/lib", ".git/objects", "src/__pycache__"):
            (self.repo / katalog).mkdir(parents=True, exist_ok=True)
        (self.repo / "src" / "a.bak").write_text("x", encoding="utf-8")
        (self.repo / "src" / "__pycache__" / "m.pyc").write_text("x", encoding="utf-8")
        (self.repo / "node_modules" / "pakiet" / "x.bak").write_text("x", encoding="utf-8")
        (self.repo / ".venv" / "lib" / "y.tmp").write_text("x", encoding="utf-8")
        (self.repo / ".git" / "objects" / "z.tmp").write_text("x", encoding="utf-8")
        (self.repo / "src" / "kod.py").write_text("# TODO: dokończyć\nwartosc = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tymczasowy.cleanup()

    def audyt(self, *argumenty: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([PYTHON, str(AUDYT), *argumenty],
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def stan(self) -> set[str]:
        return {str(p.relative_to(self.repo)) for p in self.repo.rglob("*")}

    def test_tryb_podgladu_nic_nie_zmienia(self):
        przed = self.stan()
        wynik = self.audyt(str(self.repo))
        self.assertEqual(wynik.returncode, KOD_CZYSTO)
        self.assertIn("Tryb podglądu", wynik.stdout)
        self.assertEqual(przed, self.stan())

    def test_usun_zostawia_katalogi_robocze(self):
        """Regresja A2-04: pusty katalog bywa wymaganym katalogiem aplikacji."""
        wynik = self.audyt(str(self.repo), "--usun")
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stderr)
        self.assertTrue((self.repo / "logi").is_dir())
        self.assertTrue((self.repo / "migracje").is_dir())

    def test_usun_nie_wchodzi_do_zaleznosci(self):
        """Regresja A2-04: zawartość node_modules i .venv nie należy do repozytorium."""
        self.audyt(str(self.repo), "--usun")
        self.assertTrue((self.repo / "node_modules" / "pakiet" / "x.bak").is_file())
        self.assertTrue((self.repo / ".venv" / "lib" / "y.tmp").is_file())
        self.assertTrue((self.repo / "node_modules" / "pakiet" / "__pycache__").is_dir())

    def test_usun_nie_rusza_katalogu_git(self):
        self.audyt(str(self.repo), "--usun")
        self.assertTrue((self.repo / ".git" / "objects" / "z.tmp").is_file())

    def test_usun_usuwa_wskazane_smieci(self):
        self.audyt(str(self.repo), "--usun")
        self.assertFalse((self.repo / "src" / "a.bak").exists())
        self.assertFalse((self.repo / "src" / "__pycache__").exists())
        self.assertTrue((self.repo / "src" / "kod.py").is_file())

    def test_usun_puste_za_osobnym_przelacznikiem(self):
        wynik = self.audyt(str(self.repo), "--usun", "--usun-puste")
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stderr)
        self.assertFalse((self.repo / "logi").exists())
        self.assertFalse((self.repo / "migracje").exists())

    def test_usun_puste_bez_usun_nic_nie_robi(self):
        przed = self.stan()
        wynik = self.audyt(str(self.repo), "--usun-puste")
        self.assertEqual(wynik.returncode, KOD_CZYSTO)
        self.assertIn("tylko razem z --usun", wynik.stderr)
        self.assertEqual(przed, self.stan())

    def test_nieudane_usuniecie_daje_kod_trzy(self):
        if os.name != "posix" or os.geteuid() == 0:
            self.skipTest("test wymaga uprawnień innych niż root")
        katalog = self.repo / "chroniony"
        katalog.mkdir()
        (katalog / "x.bak").write_text("x", encoding="utf-8")
        katalog.chmod(0o500)
        try:
            wynik = self.audyt(str(self.repo), "--usun")
            self.assertEqual(wynik.returncode, KOD_NIEUDANEGO_USUNIECIA, wynik.stdout)
            self.assertIn("nie udało się usunąć", wynik.stderr)
        finally:
            katalog.chmod(0o700)

    def test_zly_katalog(self):
        wynik = self.audyt(str(self.repo / "nie-ma"))
        self.assertEqual(wynik.returncode, KOD_ZLEGO_WEJSCIA)
        self.assertIn("nie ma takiego katalogu", wynik.stderr)

    def test_raport_json_wymienia_znaczniki_todo(self):
        wynik = self.audyt(str(self.repo), "--json")
        dane = json.loads(wynik.stdout)
        self.assertEqual(len(dane["todoFixme"]), 1)
        self.assertIn("kod.py", dane["todoFixme"][0])
        self.assertTrue(any("a.bak" in p for p in dane["plikiDoUsuniecia"]))
        self.assertEqual(len([p for p in dane["plikiDoUsuniecia"] if "node_modules" in p]), 0)

    def test_podsumowanie_przed_usunieciem(self):
        wynik = self.audyt(str(self.repo), "--usun")
        self.assertIn("Do usunięcia w", wynik.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
