"""Testy hooka obowiązku opisu (hooks/obowiazek_opisu.py) na tymczasowym rejestrze i stanie."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "obowiazek_opisu.py"


class ObowiazekOpisu(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        katalog = Path(self.tmp.name) / "katalog"
        (katalog / "rejestr").mkdir(parents=True)
        (katalog / "rejestr" / "dane.json").write_text(json.dumps({"narzedzia": [
            {"polecenie": "jq"}, {"polecenie": "grep"}, {"polecenie": "ffmpeg9"}]}), encoding="utf-8")
        self.env = dict(os.environ, DANACO_KATALOG=str(katalog), CLAUDE_CONFIG_DIR=str(Path(self.tmp.name) / "konf"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def hak(self, tryb: str, zdarzenie: dict) -> str:
        wynik = subprocess.run([sys.executable, str(HOOK), tryb], input=json.dumps(zdarzenie), text=True,
                               capture_output=True, env=self.env, check=True)
        return wynik.stdout

    def bash(self, polecenie: str, sesja: str = "s1") -> str:
        return self.hak("przed", {"session_id": sesja, "tool_name": "Bash", "tool_input": {"command": polecenie}})

    def przeczytaj(self, nazwa: str, sesja: str = "s1") -> None:
        self.hak("po", {"session_id": sesja, "tool_input": {"nazwa": nazwa}, "tool_response": "opis"})

    def test_program_bez_opisu_odrzucony(self):
        wynik = json.loads(self.bash("cat x | jq ."))
        self.assertEqual(wynik["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("jq", wynik["hookSpecificOutput"]["permissionDecisionReason"])

    def test_po_opisie_przepuszczony(self):
        self.przeczytaj("jq")
        self.assertEqual(self.bash("cat x | jq ."), "")

    def test_polecenia_spoza_katalogu_przechodza(self):
        self.assertEqual(self.bash("cd /tmp && echo ok"), "")

    def test_programy_za_opakowaniami_i_w_podstawieniu(self):
        powod = json.loads(self.bash("A=1 sudo timeout 30 ffmpeg9 -i a b; echo $(grep x f)"))
        tekst = powod["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("ffmpeg9", tekst)
        self.assertIn("grep", tekst)

    def test_sesje_rozdzielone(self):
        self.przeczytaj("jq", "s1")
        self.assertNotEqual(self.bash("jq .", "s2"), "")

    def test_nieznana_nazwa_nie_zapisuje(self):
        self.przeczytaj("nieistnieje")
        stan = Path(self.env["CLAUDE_CONFIG_DIR"]) / "plugins" / "data" / "danaco-plugin" / "obowiazek-opisu" / "s1.json"
        self.assertFalse(stan.exists())

    def test_zapis_stanu_przez_model_odrzucony(self):
        wynik = json.loads(self.bash("echo [] > ~/.claude/plugins/data/danaco-plugin/obowiazek-opisu/s1.json"))
        self.assertEqual(wynik["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_uruchom_mcp_objety(self):
        wynik = self.hak("przed", {"session_id": "s1", "tool_name": "mcp__x__uruchom",
                                   "tool_input": {"polecenie": "ffmpeg9 -i a b"}})
        self.assertIn("ffmpeg9", wynik)

    def test_zly_json_nie_blokuje(self):
        wynik = subprocess.run([sys.executable, str(HOOK), "przed"], input="nie json", text=True,
                               capture_output=True, env=self.env)
        self.assertEqual((wynik.returncode, wynik.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
