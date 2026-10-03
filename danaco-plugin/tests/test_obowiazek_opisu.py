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
SKILL = "opis\n\n--- SKILL: /skille/x/SKILL.md ---\ntreść skilla"


class ObowiazekOpisu(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        katalog = Path(self.tmp.name) / "katalog"
        (katalog / "rejestr").mkdir(parents=True)
        (katalog / "rejestr" / "dane.json").write_text(json.dumps({"narzedzia": [
            {"polecenie": "jq", "skill": "jq"}, {"polecenie": "grep", "skill": "tekst"},
            {"polecenie": "sed", "skill": "tekst"}, {"polecenie": "ffmpeg9", "skill": "ffmpeg"},
            {"polecenie": "global", "skill": "global"}]}), encoding="utf-8")
        self.konf = Path(self.tmp.name) / "konf"
        self.env = dict(os.environ, DANACO_KATALOG=str(katalog), CLAUDE_CONFIG_DIR=str(self.konf))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def hak(self, tryb: str, zdarzenie: dict) -> str:
        wynik = subprocess.run([sys.executable, str(HOOK), tryb], input=json.dumps(zdarzenie), text=True,
                               capture_output=True, env=self.env, check=True)
        return wynik.stdout

    def bash(self, polecenie: str, sesja: str = "s1") -> str:
        return self.hak("przed", {"session_id": sesja, "tool_name": "Bash", "tool_input": {"command": polecenie}})

    def opis(self, nazwa: str, pelny: bool = True, sesja: str = "s1") -> None:
        self.hak("po", {"session_id": sesja, "tool_input": {"nazwa": nazwa, "pelny": pelny},
                        "tool_response": SKILL if pelny else "sam opis"})

    def stan(self) -> Path:
        return self.konf / "plugins" / "data" / "danaco-plugin" / "przeczytane-opisy"

    def test_program_bez_opisu_odrzucony(self):
        wynik = json.loads(self.bash("cat x | jq ."))
        self.assertEqual(wynik["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("jq", wynik["hookSpecificOutput"]["permissionDecisionReason"])

    def test_po_pelnym_opisie_przepuszczony(self):
        self.opis("jq")
        self.assertEqual(self.bash("cat x | jq ."), "")

    def test_opis_bez_skilla_nie_zalicza_programu(self):
        self.opis("jq", pelny=False)
        self.assertNotEqual(self.bash("jq ."), "")

    def test_wspolny_skill_czytany_raz(self):
        self.opis("grep")
        self.opis("sed", pelny=False)
        self.assertEqual(self.bash("grep x f | sed s/a/b/"), "")

    def test_odmowa_wskazuje_opis_bez_skilla_dla_przeczytanego_skilla(self):
        self.opis("grep")
        powod = json.loads(self.bash("sed s/a/b/ f"))["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("pelny=false", powod)

    def test_polecenia_spoza_katalogu_przechodza(self):
        self.assertEqual(self.bash("cd /tmp && echo ok"), "")

    def test_programy_za_opakowaniami_i_w_podstawieniu(self):
        powod = json.loads(self.bash("A=1 sudo timeout 30 ffmpeg9 -i a b; echo $(grep x f)"))
        tekst = powod["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("ffmpeg9", tekst)
        self.assertIn("grep", tekst)

    def test_tresc_heredoca_nie_jest_poleceniem(self):
        self.assertEqual(self.bash("cat > plik.py <<'PY'\nglobal s\njq = 1\nPY\necho ok"), "")

    def test_sesje_rozdzielone(self):
        self.opis("jq", sesja="s1")
        self.assertNotEqual(self.bash("jq .", "s2"), "")

    def test_nieznana_nazwa_nie_zapisuje(self):
        self.opis("nieistnieje")
        self.assertFalse((self.stan() / "s1.json").exists())

    def test_zapis_stanu_przez_bash_odrzucony(self):
        wynik = json.loads(self.bash(f"echo [] > {self.stan()}/s1.json"))
        self.assertEqual(wynik["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_zapis_pliku_w_katalogu_stanu_odrzucony(self):
        wynik = self.hak("przed", {"session_id": "s1", "tool_name": "Write",
                                   "tool_input": {"file_path": str(self.stan() / "s1.json"), "content": "{}"}})
        self.assertIn("deny", wynik)

    def test_edycja_kodu_z_nazwa_stanu_przepuszczona(self):
        wynik = self.hak("przed", {"session_id": "s1", "tool_name": "Write",
                                   "tool_input": {"file_path": "/tmp/hak.py", "content": "NAZWA = 'przeczytane-opisy'"}})
        self.assertEqual(wynik, "")

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
