"""Testy serwera MCP danaco-programy (mcp/danaco-programy.py): wykaz maszyn w instrukcjach serwera
i narzędzia `maszyny`, `maszyna` na tymczasowym katalogu (tryb lokalny, bez synchronizacji)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SERWER = Path(__file__).resolve().parent.parent / "mcp" / "danaco-programy.py"
LIMITY_ROL = {"nexus": {"priorytet": 0, "gniazda_maks": 2, "sesja_maks_s": 7200, "bezczynnosc_s": 900},
              "agent": {"priorytet": 2, "gniazda_maks": 1, "sesja_maks_s": 7200, "bezczynnosc_s": 1200}}
MASZYNY = {
    "polecenie": "danaco-srodowisko", "skill_ogolny": "maszyny-wirtualne", "kolejka": ["nexus", "agent"],
    "maszyny": {
        "linux": {"system": "Debian 13", "opis": "Debian bez grafiki z sudo.", "skill": "maszyna-linux",
                  "nakladka": None, "gniazda": 2, "zasoby": {"cpu": "wszystkie", "ram": "16G"},
                  "limity": {"polecenie_maks_s": 7200, "przeslanie_maks_mb": 2048, "wyniki_maks_mb": 2048,
                             "program_maks_mb": 4096, "rezerwa": 1},
                  "limity_rol": LIMITY_ROL, "uprawnienia": "konto `danaco` w grupie `sudo`",
                  "wzorzec": {"naglowek": "Linux (wzorzec)", "narzedzia": "| gcc | jest |\n| Go | **brak** |"}},
        "windows": {"system": "Windows 11", "opis": "Windows do budowy .NET.", "skill": "maszyna-windows",
                    "nakladka": "maszyna-windows", "gniazda": 2, "zasoby": {}, "limity": {}, "limity_rol": {},
                    "wzorzec": {}},
    },
}


class SerwerMaszyny(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        katalog = Path(self.tmp.name)
        (katalog / "rejestr").mkdir()
        (katalog / "rejestr" / "danaco.json").write_text(json.dumps({"dzial": "danaco", "narzedzia": [
            {"polecenie": "danaco-srodowisko", "sciezka": "/bin/sh", "do_czego": "strefy",
             "skill": "maszyny-wirtualne"}]}), encoding="utf-8")
        (katalog / "maszyny.json").write_text(json.dumps(MASZYNY), encoding="utf-8")
        skill = katalog / "skille" / "maszyna-linux"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: maszyna-linux\ndescription: \"x\"\n---\n# instrukcja linux\n",
                                        encoding="utf-8")
        self.katalog = katalog
        self.env = dict(os.environ, DANACO_KATALOG=str(katalog), DANACO_PROGRAMY_TRYB="lokalny",
                        PYTHONDONTWRITEBYTECODE="1")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def rozmowa(self, *komunikaty: dict) -> list[dict]:
        wejscie = "".join(json.dumps(dict(k, jsonrpc="2.0", id=i)) + "\n" for i, k in enumerate(komunikaty, 1))
        wynik = subprocess.run([sys.executable, str(SERWER)], input=wejscie, text=True, capture_output=True,
                               env=self.env, check=True, timeout=60)
        return [json.loads(w) for w in wynik.stdout.splitlines() if w.strip()]

    def wywolaj(self, narzedzie: str, argumenty: dict) -> str:
        odp = self.rozmowa({"method": "tools/call", "params": {"name": narzedzie, "arguments": argumenty}})[0]
        return odp["result"]["content"][0]["text"]

    def test_instrukcje_wymieniaja_wszystkie_maszyny(self):
        instrukcje = self.rozmowa({"method": "initialize", "params": {}})[0]["result"]["instructions"]
        self.assertIn("Maszyny (2):", instrukcje)
        self.assertIn("- linux — Debian 13, 2 gniazda, skill `maszyna-linux`: Debian bez grafiki z sudo.", instrukcje)
        self.assertIn("nakładka `maszyna-windows`", instrukcje)
        self.assertIn("obowiązkowo przeczytaj", instrukcje)

    def test_lista_narzedzi_zawiera_maszyny(self):
        nazwy = {n["name"] for n in self.rozmowa({"method": "tools/list"})[0]["result"]["tools"]}
        self.assertTrue({"maszyny", "maszyna", "opis"} <= nazwy)

    def test_maszyna_daje_wykaz_i_skill(self):
        tekst = self.wywolaj("maszyna", {"strefa": "Linux"})
        self.assertIn("Maszyna linux — Debian 13", tekst)
        self.assertIn("Go | **brak**", tekst)
        self.assertIn("- nexus: 2 gn., 2 h / 15 min", tekst)
        self.assertIn("Uprawnienia w maszynie (administrator, kończą się na granicy maszyny): konto `danaco`", tekst)
        self.assertIn("--- SKILL:", tekst)
        self.assertIn("# instrukcja linux", tekst)

    def test_maszyna_bez_skilla_na_zadanie(self):
        tekst = self.wywolaj("maszyna", {"strefa": "linux", "pelny": False})
        self.assertNotIn("--- SKILL:", tekst)
        self.assertIn("przeslanie", tekst.replace("przesłanie", "przeslanie"))

    def test_maszyna_nieznana_i_brak_skilla_w_katalogu(self):
        self.assertIn("Dostępne: linux, windows", self.wywolaj("maszyna", {"strefa": "macos"}))
        self.assertIn("niedostępny w katalogu", self.wywolaj("maszyna", {"strefa": "windows"}))

    def test_bez_wykazu_maszyn_instrukcje_bez_sekcji(self):
        (self.katalog / "maszyny.json").unlink()
        instrukcje = self.rozmowa({"method": "initialize", "params": {}})[0]["result"]["instructions"]
        self.assertNotIn("Maszyny (", instrukcje)
        self.assertIn("nie ma wykazu maszyn", self.wywolaj("maszyny", {}))


if __name__ == "__main__":
    unittest.main()
