#!/usr/bin/env python3
"""Testy hooka kontroli dyscypliny po zapisie (hooks/po_zapisie.sh) oraz kontraktu
pliku hooks.json wobec plików pluginu.

Uruchomienie (biblioteka standardowa, bez zależności):
    python3 tests/test_po_zapisie.py
    sh tests/uruchom_testy.sh

Każdy test woła PRAWDZIWY wrapper `hooks/po_zapisie.sh` przez `sh` z JSON-em zdarzenia
na stdin, w tymczasowym katalogu projektu - tak jak robi to Claude Code. Sprawdzane są
kody wyjścia (0 = brak naruszeń, 2 = raport do kontekstu tury) i treść wyjścia.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

KORZEN_PLUGINU = Path(__file__).resolve().parent.parent
SH = shutil.which("sh") or "/bin/sh"


class BazaTestow(unittest.TestCase):
    def setUp(self) -> None:
        self.tymczasowy = tempfile.TemporaryDirectory(prefix="po-zapisie-test-")
        self.projekt = Path(self.tymczasowy.name) / "projekt"
        self.projekt.mkdir()
        # Katalog .git czyni z katalogu tymczasowego korzeń projektu, tak jak w repozytorium
        # użytkownika: kontrola po zapisie działa na ścieżkach wewnątrz projektu.
        (self.projekt / ".git").mkdir()

    def tearDown(self) -> None:
        self.tymczasowy.cleanup()

    def srodowisko(self, **nadpisania: str | None) -> dict:
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(KORZEN_PLUGINU)
        env.pop("CLAUDE_PROJECT_DIR", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for klucz, wartosc in nadpisania.items():
            if wartosc is None:
                env.pop(klucz, None)
            else:
                env[klucz] = wartosc
        return env


class TestPoZapisie(BazaTestow):
    """Hook PostToolUse: naruszenia muszą dojść do modelu, a hook nie może padać
    (zamówienie U1 z ustaleń A1-01, A1-02, A1-04)."""

    def po_zapisie(self, zdarzenie, env: dict | None = None) -> subprocess.CompletedProcess:
        wejscie = zdarzenie if isinstance(zdarzenie, str) else json.dumps(zdarzenie, ensure_ascii=False)
        return subprocess.run(
            [SH, str(KORZEN_PLUGINU / "hooks" / "po_zapisie.sh")],
            input=wejscie, cwd=str(self.projekt), env=env or self.srodowisko(),
            capture_output=True, text=True, encoding="utf-8",
        )

    def zdarzenie_zapisu(self, sciezka: Path, tresc: str = "") -> dict:
        return {"hook_event_name": "PostToolUse", "tool_name": "Write",
                "cwd": str(self.projekt),
                "tool_input": {"file_path": str(sciezka), "content": tresc}}

    def test_plik_czysty_nie_zaklada_kontekstu(self):
        plik = self.projekt / "czysty.py"
        plik.write_text("wartosc = 1\n", encoding="utf-8")
        wynik = self.po_zapisie(self.zdarzenie_zapisu(plik))
        self.assertEqual(wynik.returncode, 0)
        self.assertEqual(wynik.stdout, "")
        self.assertEqual(wynik.stderr, "")

    def test_plik_z_naruszeniem_raportuje_na_stderr(self):
        plik = self.projekt / "dlugi.py"
        plik.write_text("# " + "a" * 400 + "\n", encoding="utf-8")
        wynik = self.po_zapisie(self.zdarzenie_zapisu(plik))
        self.assertEqual(wynik.returncode, 2)
        self.assertIn("limit-dlugosci-komentarza", wynik.stderr)
        self.assertEqual(wynik.stdout, "")

    def test_brak_zmiennej_korzenia_pluginu(self):
        plik = self.projekt / "dlugi.py"
        plik.write_text("# " + "a" * 400 + "\n", encoding="utf-8")
        wynik = self.po_zapisie(self.zdarzenie_zapisu(plik),
                                env=self.srodowisko(CLAUDE_PLUGIN_ROOT=None))
        self.assertEqual(wynik.returncode, 2)
        self.assertNotIn("unbound variable", wynik.stderr)
        self.assertIn("limit-dlugosci-komentarza", wynik.stderr)

    def test_bardzo_duze_zdarzenie(self):
        """Regresja A1-04: zdarzenie z dużym polem content nie może być pomijane."""
        plik = self.projekt / "duzy.py"
        plik.write_text("# " + "a" * 400 + "\n", encoding="utf-8")
        wynik = self.po_zapisie(self.zdarzenie_zapisu(plik, tresc="x" * 200_000))
        self.assertEqual(wynik.returncode, 2)
        self.assertIn("limit-dlugosci-komentarza", wynik.stderr)

    def test_zdarzenia_bez_sciezki_nie_blokuja(self):
        for zdarzenie in ("{}", '{"cos":"innego"}', "to nie jest json", "", "[1,2,3]"):
            with self.subTest(zdarzenie=zdarzenie):
                wynik = self.po_zapisie(zdarzenie)
                self.assertEqual(wynik.returncode, 0, zdarzenie)

    def test_plik_poza_zakresem_kontroli(self):
        plik = self.projekt / "notatka.md"
        plik.write_text("# " + "a" * 400 + "\n", encoding="utf-8")
        wynik = self.po_zapisie(self.zdarzenie_zapisu(plik))
        self.assertEqual(wynik.returncode, 0)
        self.assertEqual(wynik.stderr, "")


class TestKonfiguracjaHookow(unittest.TestCase):
    """Kontrakt hooks.json wobec plików pluginu (zamówienie U1 z A1-20)."""

    NAZWY_ZDARZEN = {"PostToolUse", "PreToolUse"}

    def setUp(self) -> None:
        self.dane = json.loads((KORZEN_PLUGINU / "hooks" / "hooks.json").read_text(encoding="utf-8"))

    def test_klucze_najwyzszego_poziomu(self):
        self.assertIn("hooks", self.dane)
        self.assertTrue(set(self.dane) <= {"hooks", "description"})

    def test_nazwy_zdarzen_ze_zbioru(self):
        self.assertTrue(set(self.dane["hooks"]) <= self.NAZWY_ZDARZEN,
                        f"nieznane zdarzenie: {set(self.dane['hooks']) - self.NAZWY_ZDARZEN}")

    def test_polecenia_wskazuja_istniejace_pliki(self):
        import re as wyrazenia
        for zdarzenie, wpisy in self.dane["hooks"].items():
            for wpis in wpisy:
                for hook in wpis.get("hooks", []):
                    polecenie = hook.get("command", "")
                    with self.subTest(zdarzenie=zdarzenie, polecenie=polecenie):
                        podstawione = polecenie.replace("${CLAUDE_PLUGIN_ROOT}", str(KORZEN_PLUGINU))
                        znalezione = wyrazenia.findall(r'"([^"]+)"', podstawione)
                        self.assertTrue(znalezione, polecenie)
                        self.assertTrue(Path(znalezione[0]).is_file(), znalezione[0])

    def test_matchery_kompiluja_sie(self):
        import re as wyrazenia
        for wpisy in self.dane["hooks"].values():
            for wpis in wpisy:
                matcher = wpis.get("matcher")
                if matcher is None:
                    continue
                with self.subTest(matcher=matcher):
                    wyrazenia.compile(matcher)


if __name__ == "__main__":
    unittest.main()
