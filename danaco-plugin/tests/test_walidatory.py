#!/usr/bin/env python3
"""Testy walidatorów dyscypliny i nazewnictwa (style_guard.py, nazwy_guard.py).

Uruchomienie:
    python3 tests/test_walidatory.py
    python3 -m pytest tests/test_walidatory.py

Każdy test tworzy pliki w katalogu tymczasowym i uruchamia walidator jako proces
(tak jak robi to hook, pre-commit i CI), więc sprawdzane są kody wyjścia i treść
raportu, nie wewnętrzne struktury. Pliki pluginu nie są nigdy modyfikowane.
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
STYL = KORZEN_PLUGINU / "skills" / "weryfikatory-dyscypliny" / "scripts" / "style_guard.py"
NAZWY = KORZEN_PLUGINU / "skills" / "standardy-nazewnictwa" / "scripts" / "nazwy_guard.py"
PYTHON = sys.executable

KOD_CZYSTO = 0
KOD_OSTRZEZENIA = 2
KOD_BLOKUJACE = 3
KOD_AWARII = 4


class BazaWalidatorow(unittest.TestCase):
    def setUp(self) -> None:
        self.tymczasowy = tempfile.TemporaryDirectory(prefix="walidatory-test-")
        self.katalog = Path(self.tymczasowy.name)

    def tearDown(self) -> None:
        self.tymczasowy.cleanup()

    def plik(self, nazwa: str, tresc: str, kodowanie: str = "utf-8") -> Path:
        cel = self.katalog / nazwa
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_bytes(tresc.encode(kodowanie))
        return cel

    def uruchom(self, walidator: Path, *argumenty: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([PYTHON, str(walidator), *argumenty],
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def styl(self, *argumenty: str) -> subprocess.CompletedProcess:
        return self.uruchom(STYL, *argumenty)

    def nazwy(self, *argumenty: str) -> subprocess.CompletedProcess:
        return self.uruchom(NAZWY, *argumenty)


class TestKomentarzePython(BazaWalidatorow):
    def test_dlugi_komentarz_w_linii_z_apostrofem_w_literale(self):
        """Regresja A2-09: apostrof w literale ukrywał komentarz przed kontrolą."""
        plik = self.plik("a.py", 'print("it\'s")  # ' + "x" * 400 + "\n")
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("limit-dlugosci-komentarza", wynik.stdout)

    def test_krotka_w_literale_potrojnym_nie_jest_komentarzem(self):
        """Regresja A2-09: nagłówek Markdown w szablonie to nie komentarz."""
        plik = self.plik("b.py", 'SZABLON = """\n# ' + "y" * 400 + '\n"""\n')
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_adres_w_literale_nie_ukrywa_komentarza(self):
        plik = self.plik("c.py", 'URL = "https://przyklad.test/x"  # ' + "z" * 400 + "\n")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_BLOKUJACE)

    def test_komentarz_w_typescript_za_literalem(self):
        plik = self.plik("d.ts", 'const s = "a // b";\n// ' + "q" * 400 + "\n")
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)

    def test_literal_szablonowy_typescript_nie_jest_komentarzem(self):
        plik = self.plik("e.ts", "const s = `\n// " + "q" * 400 + "\n`;\n")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_CZYSTO)

    def test_docstring_wlicza_sie_do_udzialu(self):
        proza = "Wyjaśnienie działania funkcji. " * 30
        tresc = f'def f():\n    """{proza}"""\n    return 1\n' + "x = 1\n" * 5
        plik = self.plik("f.py", tresc)
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("udzial-komentarzy", wynik.stdout)

    def test_docstring_modulu_nie_wlicza_sie_do_udzialu(self):
        proza = "Dokumentacja pliku i jego kontraktu wejścia. " * 20
        tresc = f'"""{proza}"""\n' + "wartosc = 1\n" * 10
        plik = self.plik("g.py", tresc)
        self.assertEqual(self.styl(str(plik)).returncode, KOD_CZYSTO)

    def test_plik_niepoprawny_skladniowo_nie_przewraca_kontroli(self):
        plik = self.plik("h.py", "def f(:\n  # " + "x" * 400 + "\n")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_BLOKUJACE)


class TestReguly(BazaWalidatorow):
    def test_wymyslony_kod_trafiony_i_nietrafiony(self):
        """Regresja A2-10: normy i standardy nie są wymyślonymi kodami."""
        czysty = self.plik("norm.py", "# kodowanie UTF-8, podpis SHA-1, norma ISO-8601, RFC-3339\n")
        self.assertEqual(self.styl(str(czysty)).returncode, KOD_CZYSTO)
        brudny = self.plik("kod.py", "# panel MOD-A7 zgodnie z ustaleniem\n")
        wynik = self.styl(str(brudny))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)
        self.assertIn("wymyslony-kod", wynik.stdout)

    def test_allowlista_kodow_z_konfiguracji(self):
        plik = self.plik("kod2.py", "# panel MOD-A7\n")
        cfg = self.katalog / "konfiguracja-dyscypliny.json"
        cfg.write_text(json.dumps({"allowlistaKodow": ["MOD-A7"]}), encoding="utf-8")
        self.assertEqual(self.styl("--config", str(cfg), str(plik)).returncode, KOD_CZYSTO)

    def test_ton_nieformalny_trafiony_i_nietrafiony(self):
        """Regresja A2-11: `??` to operator TypeScriptu, nie ton nieformalny."""
        czysty = self.plik("ts.ts", "// uzyj a ?? b gdy null\n")
        self.assertEqual(self.styl(str(czysty)).returncode, KOD_CZYSTO)
        for tekst in ("// gotowe!!!\n", "// no i co teraz???\n", "// czekamy.....\n"):
            with self.subTest(tekst=tekst):
                brudny = self.plik("ton.ts", tekst)
                wynik = self.styl(str(brudny))
                self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, tekst)
                self.assertIn("ton-nieformalny", wynik.stdout)

    def test_limit_dlugosci_komentarza_granica(self):
        rowno = self.plik("r1.py", "# " + "a" * 348 + "\n")
        self.assertEqual(self.styl(str(rowno)).returncode, KOD_CZYSTO)
        ponad = self.plik("r2.py", "# " + "a" * 349 + "\n")
        self.assertEqual(self.styl(str(ponad)).returncode, KOD_BLOKUJACE)

    def test_udzial_komentarzy_wylaczony_na_krotkim_pliku(self):
        tresc = "# " + "k" * 300 + "\nx = 1\n"
        plik = self.plik("krotki.py", tresc)
        self.assertLess(len(tresc), 600)
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_udzial_komentarzy_zglaszany_na_duzym_pliku(self):
        tresc = ("# " + "k" * 300 + "\n") * 3 + "x = 1\n" * 20
        plik = self.plik("duzy.py", tresc)
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("udzial-komentarzy", wynik.stdout)


class TestPrzypadkiBrzegowe(BazaWalidatorow):
    def test_plik_cp1250_jest_naruszeniem_blokujacym(self):
        """Regresja A2-08: pliku nie da się sprawdzić, więc nie jest „czysty”."""
        plik = self.plik("cp1250.py", "# zażółć gęślą jaźń " + "x" * 400 + "\n", kodowanie="cp1250")
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("kodowanie-pliku", wynik.stdout)
        wynik_nazwy = self.nazwy(str(plik))
        self.assertEqual(wynik_nazwy.returncode, KOD_BLOKUJACE, wynik_nazwy.stdout)
        self.assertIn("kodowanie-pliku", wynik_nazwy.stdout)

    def test_plik_pusty(self):
        plik = self.plik("pusty.py", "")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_CZYSTO)
        self.assertEqual(self.nazwy(str(plik)).returncode, KOD_CZYSTO)

    def test_plik_binarny_z_rozszerzeniem_py(self):
        plik = self.katalog / "binarny.py"
        plik.write_bytes(bytes(range(256)) * 8)
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("kodowanie-pliku", wynik.stdout)

    def test_plik_z_crlf(self):
        plik = self.katalog / "crlf.py"
        plik.write_bytes(("# " + "a" * 400 + "\r\n" + "x = 1\r\n").encode("utf-8"))
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_BLOKUJACE, wynik.stdout)
        self.assertIn("limit-dlugosci-komentarza", wynik.stdout)

    def test_plik_bez_znaku_konca_linii(self):
        plik = self.plik("bez_konca.py", "x = 1  # komentarz bez znaku końca linii")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_CZYSTO)

    def test_bardzo_duzy_plik(self):
        plik = self.plik("wielki.py", "wartosc = 1\n" * 60_000)
        wynik = self.styl(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_brak_pliku_zglaszany_i_konczy_awaria(self):
        wynik = self.styl(str(self.katalog / "nie-ma.py"))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertIn("nie istnieje", wynik.stderr)
        wynik_nazwy = self.nazwy(str(self.katalog / "nie-ma.py"))
        self.assertEqual(wynik_nazwy.returncode, KOD_AWARII)

    def test_brak_jednej_ze_sciezek_nie_maskuje_wyniku(self):
        plik = self.plik("ok.py", "x = 1\n")
        wynik = self.styl(str(plik), str(self.katalog / "nie-ma.py"))
        self.assertEqual(wynik.returncode, KOD_CZYSTO)
        self.assertIn("nie istnieje", wynik.stderr)

    def test_katalogi_zaleznosci_nie_sa_przeszukiwane(self):
        """Regresja A2-26: naruszenie w node_modules nie należy do repozytorium."""
        for katalog in ("node_modules/pakiet", ".venv/lib", "dist", "__pycache__"):
            self.plik(f"{katalog}/x.py", "# " + "a" * 400 + "\n")
        self.plik("src/czysty.py", "x = 1\n")
        self.assertEqual(self.styl(str(self.katalog)).returncode, KOD_CZYSTO)
        self.assertEqual(self.nazwy(str(self.katalog)).returncode, KOD_CZYSTO)


class TestKonfiguracja(BazaWalidatorow):
    def test_config_nieistniejacy(self):
        plik = self.plik("a.py", "x = 1\n")
        for walidator in (self.styl, self.nazwy):
            with self.subTest(walidator=walidator.__name__):
                wynik = walidator("--config", str(self.katalog / "nie-ma.json"), str(plik))
                self.assertEqual(wynik.returncode, KOD_AWARII)
                self.assertIn("nie da się odczytać konfiguracji", wynik.stderr)

    def test_config_zepsuty_json(self):
        plik = self.plik("a.py", "x = 1\n")
        cfg = self.plik("cfg.json", "{to nie json")
        wynik = self.styl("--config", str(cfg), str(plik))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertNotIn("Traceback", wynik.stderr)

    def test_config_zla_wartosc(self):
        plik = self.plik("a.py", "x = 1\n")
        cfg = self.plik("cfg2.json", json.dumps({"limitKomentarza": "wiele"}))
        wynik = self.styl("--config", str(cfg), str(plik))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertIn("nieprawidłowa wartość", wynik.stderr)

    def test_config_nie_jest_obiektem(self):
        plik = self.plik("a.py", "x = 1\n")
        cfg = self.plik("cfg3.json", "[]")
        wynik = self.styl("--config", str(cfg), str(plik))
        self.assertEqual(wynik.returncode, KOD_AWARII)
        self.assertIn("obiekt JSON", wynik.stderr)

    def test_konfiguracja_znajdowana_z_glebi_drzewa(self):
        """Hook woła walidator z jednym plikiem, konfiguracja leży w korzeniu."""
        (self.katalog / ".git").mkdir()
        plik = self.plik("src/glebiej/kod.py", "# panel MOD-A7\n")
        (self.katalog / "konfiguracja-dyscypliny.json").write_text(
            json.dumps({"allowlistaKodow": ["MOD-A7"]}), encoding="utf-8")
        self.assertEqual(self.styl(str(plik)).returncode, KOD_CZYSTO)

    def test_konfiguracja_z_korzenia_repozytorium(self):
        self.plik("src/kod.py", "# panel MOD-A7\n")
        (self.katalog / "konfiguracja-dyscypliny.json").write_text(
            json.dumps({"allowlistaKodow": ["MOD-A7"]}), encoding="utf-8")
        self.assertEqual(self.styl(str(self.katalog)).returncode, KOD_CZYSTO)


class TestNazewnictwo(BazaWalidatorow):
    def test_etykieta_zdaniowa_jest_ostrzezeniem(self):
        """Regresja A2-12: reguła jest heurystyczna, więc nie blokuje bramki."""
        opis = "Kliknij tutaj, aby zapisać zmiany w dokumencie"
        plik = self.plik("a.ts", 'const x = { label: "' + opis + '" };\n')
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)
        self.assertIn("etykieta-jako-zdanie", wynik.stdout)

    def test_komunikat_bledu_nie_jest_etykieta(self):
        plik = self.plik("b.ts", 'const e = { title: "Nie udało się połączyć z rdzeniem." };\n')
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_etykieta_z_apostrofem_jest_sprawdzana(self):
        """Regresja A2-12: łańcuch w apostrofach był pomijany w całości."""
        plik = self.plik("c.ts", "const x = { label: 'Don\\'t save this document right now please' };\n")
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)
        self.assertIn("etykieta-jako-zdanie", wynik.stdout)

    def test_krotka_etykieta_przepuszczana(self):
        plik = self.plik("d.ts", 'const x = { label: "Zapisz", placeholder: "Numer sprawy" };\n')
        self.assertEqual(self.nazwy(str(plik)).returncode, KOD_CZYSTO)

    def test_oznaczenia_techniczne_nie_sa_zglaszane(self):
        """Regresja A2-13: token „słowo + liczba” to nie wymyślone oznaczenie."""
        plik = self.plik("e.ts", "const kolumny = [Col2, Row1];\nconst h = Sha256(x);\n"
                                 "type Klient = Tauri2Config;\n")
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_oznaczenie_w_deklaracji_jest_zglaszane(self):
        plik = self.plik("f.ts", "const Panel" + "X3 = () => null;\n")
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)
        self.assertIn("oznaczenie-literowo-numeryczne", wynik.stdout)

    def test_wyjatki_bez_rozroznienia_wielkosci_liter(self):
        plik = self.plik("g.ts", "const Sha256 = 1;\nconst Tauri2 = 2;\nconst Utf8 = 3;\n")
        wynik = self.nazwy(str(plik))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)

    def test_nazwa_metaforyczna_trafiona_i_nietrafiona(self):
        czysty = self.plik("h.ts", "const smartfon = 1;\nconst mocy = 2;\nconst mock = 3;\n"
                                   'const opis = "silnik parowy w opisie";\n')
        wynik = self.nazwy(str(czysty))
        self.assertEqual(wynik.returncode, KOD_CZYSTO, wynik.stdout)
        brudny = self.plik("i.ts", "const silnikSesji = 1;\n")
        wynik = self.nazwy(str(brudny))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)
        self.assertIn("nazwa-metaforyczna", wynik.stdout)

    def test_slowa_metaforyczne_z_konfiguracji(self):
        plik = self.plik("j.ts", "const kotwicaSesji = 1;\n")
        cfg = self.plik("cfg.json", json.dumps({"slowaMetaforyczne": ["kotwica"]}))
        wynik = self.nazwy("--config", str(cfg), str(plik))
        self.assertEqual(wynik.returncode, KOD_OSTRZEZENIA, wynik.stdout)

    def test_wynik_json(self):
        plik = self.plik("k.ts", "const Panel" + "X3 = 1;\n")
        wynik = self.nazwy("--json", str(plik))
        dane = json.loads(wynik.stdout)
        self.assertEqual(dane["blokujace"], [])
        self.assertEqual(dane["ostrzezenia"][0]["regula"], "oznaczenie-literowo-numeryczne")


if __name__ == "__main__":
    unittest.main(verbosity=2)
