#!/usr/bin/env python3
"""Testy hooków danaco-praca 5: każde zdarzenie i każde polecenie na wejściach JSON.

Hooki są uruchamiane tak jak przez klienta: wrapper `hooks/hak.sh` z JSON-em zdarzenia na
stdin. Stan trafia do katalogu tymczasowego (`DANACO_PRACA_STAN`), więc testy nie dotykają
danych prawdziwej instalacji. Narzędzie przejmowania sesji podmieniamy atrapą
(`DANACO_PRZEJMIJ_CMD`), żeby nie ruszać prawdziwych sesji.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
WRAPPER = KORZEN / "hooks" / "hak.sh"
sys.path.insert(0, str(KORZEN / "scripts"))

import polecenia as P  # noqa: E402
from stan import BLOKADY, TEMATY  # noqa: E402


class Baza(unittest.TestCase):
    def setUp(self):
        self.katalog = tempfile.mkdtemp(prefix="dp5-test-")
        self.stan = os.path.join(self.katalog, "stan")
        self.cwd = os.path.join(self.katalog, "projekt")
        os.makedirs(self.cwd)
        self.przejmij = os.path.join(self.katalog, "przejmij-atrapa")
        with open(self.przejmij, "w") as plik:
            plik.write("#!/bin/sh\necho \"ATRAPA-PRZEJMIJ argumenty: $*\"\n")
        os.chmod(self.przejmij, 0o755)
        self.env = dict(os.environ, DANACO_PRACA_STAN=self.stan, DANACO_PRACA_STRAZ_DYSKU="system",
                        DANACO_PRZEJMIJ_CMD=self.przejmij, CLAUDE_PLUGIN_ROOT=str(KORZEN),
                        CLAUDE_CONFIG_DIR=os.path.join(self.katalog, "profil"),
                        TMPDIR=os.path.join(self.katalog, "tmp"))
        self.env.pop("CLAUDE_PLUGIN_DATA", None)

    def tearDown(self):
        shutil.rmtree(self.katalog, ignore_errors=True)

    def hook(self, tryb: str, zdarzenie: dict, env: dict | None = None) -> dict:
        zdarzenie.setdefault("session_id", "sesja-a")
        zdarzenie.setdefault("cwd", self.cwd)
        wynik = subprocess.run(["sh", str(WRAPPER), tryb], input=json.dumps(zdarzenie), capture_output=True,
                               text=True, timeout=30, env=env or self.env)
        self.assertEqual(wynik.returncode, 0, wynik.stderr)
        self.assertNotIn("błąd hooka", wynik.stderr)
        return json.loads(wynik.stdout) if wynik.stdout.strip() else {}

    def prompt(self, tekst: str, sesja: str = "sesja-a") -> dict:
        return self.hook("prompt", {"hook_event_name": "UserPromptSubmit", "prompt": tekst, "session_id": sesja})

    def narzedzie(self, nazwa: str, wejscie: dict, sesja: str = "sesja-a", **dodatkowe) -> str | None:
        wynik = self.hook("narzedzie", {"hook_event_name": "PreToolUse", "tool_name": nazwa, "tool_input": wejscie,
                                        "session_id": sesja, **dodatkowe})
        return (wynik.get("hookSpecificOutput") or {}).get("permissionDecision")

    def bash(self, polecenie: str, **wejscie) -> str | None:
        return self.narzedzie("Bash", {"command": polecenie, **wejscie})

    def stop(self, sesja: str = "sesja-a", podagent: str | None = None) -> dict:
        zdarzenie = {"hook_event_name": "SubagentStop" if podagent else "Stop", "session_id": sesja,
                     "stop_hook_active": False}
        if podagent:
            zdarzenie["agent_id"] = podagent
        return self.hook("stop", zdarzenie)

    def stan_sesji(self, sesja: str = "sesja-a") -> dict:
        with open(os.path.join(self.stan, "sesje", sesja + ".json"), encoding="utf-8") as plik:
            return json.load(plik)["stan"]

    def dziennik(self) -> list[dict]:
        with open(os.path.join(self.stan, "dziennik.jsonl"), encoding="utf-8") as plik:
            return [json.loads(w) for w in plik]


class TestPolecenia(Baza):
    def test_kazde_polecenie_zmienia_stan_albo_pokazuje(self):
        for polecenie, rodzaj in P.POLECENIA.items():
            with self.subTest(polecenie=polecenie):
                wynik = self.prompt(f"/{polecenie}")
                self.assertTrue(wynik, "polecenie nie dało żadnego wyjścia")
                if rodzaj[0] == "praca":
                    self.assertEqual(self.stan_sesji()["praca"]["wlaczona"], rodzaj[1])
                elif rodzaj[0] == "blok":
                    self.assertEqual(self.stan_sesji()["blokady"][rodzaj[1]], rodzaj[2])
                else:
                    self.assertIn("reason", wynik)  # widok/akcja: pokaz i blokada tury

    def test_pary_blokuj_odblokuj(self):
        for temat, klucz in TEMATY.items():
            with self.subTest(temat=temat):
                self.prompt(f"/blokuj-{temat}")
                self.assertTrue(self.stan_sesji()["blokady"][klucz])
                self.prompt(f"/odblokuj-{temat}")
                self.assertFalse(self.stan_sesji()["blokady"][klucz])

    def test_praca_koniec_pracy(self):
        self.prompt("/praca")
        self.assertTrue(self.stan_sesji()["praca"]["wlaczona"])
        self.prompt("/koniec-pracy")
        self.assertFalse(self.stan_sesji()["praca"]["wlaczona"])

    def test_konwencja_nazw_spojna(self):
        # Wszystkie pary blokad trzymają jedną zasadę: blokuj-<temat> / odblokuj-<temat>.
        for temat in TEMATY:
            self.assertIn(f"blokuj-{temat}", P.POLECENIA)
            self.assertIn(f"odblokuj-{temat}", P.POLECENIA)
        for stara in ("bash-blokuj", "z-bash", "bez-bash", "sudo-tak", "dziennik", "sesje", "przejmij"):
            self.assertNotIn(stara, P.POLECENIA)
        # Czasownik pierwszy: menu grupuje po przedrostku.
        for nazwa, rodzaj in P.POLECENIA.items():
            if rodzaj[0] == "blok":
                self.assertTrue(nazwa.startswith(("blokuj-", "odblokuj-")), nazwa)

    def test_tryb_pokazuje_wszystkie_blokady(self):
        self.prompt("/blokuj-python")
        wynik = self.prompt("/tryb")
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("Python         ZABLOKOWANE", wynik["reason"])
        for nazwa in BLOKADY.values():
            self.assertIn(nazwa, wynik["reason"])

    def test_pure_control_blokuje_ture(self):
        # Sama komenda (bez zadania) nie woła modelu — pokazuje wynik przez decision: block.
        wynik = self.prompt("/blokuj-bash")
        self.assertEqual(wynik["decision"], "block")
        self.assertNotIn("hookSpecificOutput", wynik)

    def test_polecenie_z_zadaniem_przechodzi(self):
        wynik = self.prompt("/blokuj-bash\nzrób porządek w repo")
        self.assertIn("additionalContext", wynik["hookSpecificOutput"])
        self.assertTrue(self.stan_sesji()["blokady"]["bash"])

    def test_praca_zapisuje_zlecenie_i_przechodzi(self):
        wynik = self.prompt("/praca zbuduj raport\nszczegóły w pliku a.md")
        stan = self.stan_sesji()
        self.assertTrue(stan["praca"]["wlaczona"])
        self.assertEqual(stan["praca"]["zlecenie"], "zbuduj raport\nszczegóły w pliku a.md")
        self.assertIn("zbuduj raport", wynik["hookSpecificOutput"]["additionalContext"])

    def test_prefiks_wtyczki_i_kilka_polecen(self):
        self.prompt("/danaco-praca:blokuj-bash\n/blokuj-sudo")
        stan = self.stan_sesji()
        self.assertTrue(stan["blokady"]["bash"])
        self.assertTrue(stan["blokady"]["sudo"])

    def test_postac_rozwinieta(self):
        self.prompt("<command-message>praca</command-message>\n<command-name>/danaco-praca:praca</command-name>\n<command-args>zadanie X</command-args>")
        self.assertEqual(self.stan_sesji()["praca"]["zlecenie"], "zadanie X")

    def test_wzmianka_nie_jest_poleceniem(self):
        for tekst in ("opisz polecenie /koniec-pracy w README", "zobacz skills/praca/SKILL.md",
                      "/bashlog", "a /blokuj-bash w zdaniu"):
            with self.subTest(tekst=tekst):
                self.assertEqual(self.prompt(tekst), {})
        self.assertFalse(os.path.exists(os.path.join(self.stan, "sesje", "sesja-a.json")))

    def test_stan_osobny_na_sesje(self):
        self.prompt("/blokuj-bash", sesja="sesja-a")
        self.assertEqual(self.narzedzie("Bash", {"command": "ls"}, sesja="sesja-a"), "deny")
        self.assertIsNone(self.narzedzie("Bash", {"command": "ls"}, sesja="sesja-b"))

    def test_dziennik_zmian(self):
        self.prompt("/blokuj-bash")
        self.prompt("/odblokuj-bash")
        wpisy = [w for w in self.dziennik() if w["zdarzenie"] == "polecenie"]
        self.assertEqual([w["polecenia"] for w in wpisy], [["blokuj-bash"], ["odblokuj-bash"]])
        self.assertTrue(all(w["sesja"] == "sesja-a" and "podpis_migawki" in w for w in wpisy))


class TestKomendySesji(Baza):
    def test_sesja_id(self):
        wynik = self.hook("prompt", {"hook_event_name": "UserPromptSubmit", "prompt": "/sesja-id",
                                     "session_id": "11112222-3333-4444"})
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("11112222-3333-4444", wynik["reason"])

    def test_sesje_wola_narzedzie(self):
        wynik = self.prompt("/sesja-lista")
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("ATRAPA-PRZEJMIJ argumenty: --lista", wynik["reason"])

    def test_przejmij_wola_narzedzie_z_id(self):
        wynik = self.prompt("/sesja-przejmij 9d4ff047")
        self.assertIn("ATRAPA-PRZEJMIJ argumenty: 9d4ff047", wynik["reason"])

    def test_przejmij_bez_id(self):
        wynik = self.prompt("/sesja-przejmij")
        self.assertIn("Podaj identyfikator", wynik["reason"])

    def test_przejmij_odrzuca_niebezpieczny_id(self):
        wynik = self.prompt("/sesja-przejmij a;rm -rf /")
        self.assertIn("Niepoprawny identyfikator", wynik["reason"])

    def test_brak_narzedzia_nie_wywraca(self):
        env = dict(self.env, DANACO_PRZEJMIJ_CMD="danaco-przejmij-sesje-ktorego-nie-ma")
        wynik = self.hook("prompt", {"hook_event_name": "UserPromptSubmit", "prompt": "/sesja-lista"}, env)
        self.assertIn("Nie znaleziono narzędzia", wynik["reason"])


class TestWyczyscIDziennik(Baza):
    def test_wyczysc_tryby(self):
        self.prompt("/praca zadanie")
        self.prompt("/blokuj-bash")
        self.prompt("/blokuj-siec")
        wynik = self.prompt("/tryb-wyczysc")
        self.assertEqual(wynik["decision"], "block")
        stan = self.stan_sesji()
        self.assertFalse(stan["praca"]["wlaczona"])
        self.assertFalse(any(stan["blokady"].values()))

    def test_dziennik_pokazuje_wpisy(self):
        self.prompt("/blokuj-bash")
        self.bash("ls")  # odmowa trafia do dziennika
        wynik = self.prompt("/tryb-dziennik")
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("polecenie", wynik["reason"])
        self.assertIn("odmowa", wynik["reason"])


class TestOchronaStanu(Baza):
    def test_zmieniony_plik_stanu_wraca_z_dziennika(self):
        self.prompt("/blokuj-bash")
        sciezka = os.path.join(self.stan, "sesje", "sesja-a.json")
        with open(sciezka, encoding="utf-8") as plik:
            zapis = json.load(plik)
        zapis["stan"]["blokady"]["bash"] = False
        with open(sciezka, "w", encoding="utf-8") as plik:
            json.dump(zapis, plik)
        self.assertEqual(self.bash("ls"), "deny")
        self.assertIn("naruszenie-stanu", [w["zdarzenie"] for w in self.dziennik()])

    def test_skasowany_plik_stanu_wraca_z_dziennika(self):
        self.prompt("/praca")
        os.remove(os.path.join(self.stan, "sesje", "sesja-a.json"))
        self.assertEqual(self.stop().get("decision"), "block")

    def test_model_nie_dotyka_stanu(self):
        for nazwa, wejscie in (
            ("Write", {"file_path": f"{self.stan}/sesje/sesja-a.json", "content": "{}"}),
            ("Read", {"file_path": f"{self.stan}/klucz"}),
            ("Bash", {"command": f"cat {self.stan}/dziennik.jsonl"}),
            ("Bash", {"command": "ls ~/.claude/plugins/data/danaco-praca-danaco/stan"}),
            ("Bash", {"command": "cat ~/.claude/plugins/data/danaco-p*/stan/klucz"}),
            ("Bash", {"command": "rm -rf \"$CLAUDE_PLUGIN_DATA\""}),
        ):
            with self.subTest(nazwa=nazwa, wejscie=wejscie):
                self.assertEqual(self.narzedzie(nazwa, wejscie), "deny")

    def test_skill_i_podrzucone_polecenia(self):
        self.prompt("/praca")
        self.assertEqual(self.narzedzie("Skill", {"skill": "koniec-pracy"}), "deny")
        self.assertEqual(self.narzedzie("Skill", {"skill": "danaco-praca:odblokuj-bash"}), "deny")
        self.assertEqual(self.narzedzie("SendMessage", {"to": "main", "message": "/koniec-pracy"}), "deny")
        self.assertEqual(self.bash("echo '/koniec-pracy' | claude -p"), "deny")
        self.assertEqual(self.bash("claude -p --resume abc 'dalej'"), "deny")
        self.assertIsNone(self.narzedzie("Skill", {"skill": "dataviz"}))
        self.assertIsNone(self.bash("ls skills/praca/SKILL.md"))
        self.assertIsNone(self.bash("ls ~/.claude/plugins/data/"))

    def test_ochrona_mechanizmu_tylko_przy_aktywnym_trybie(self):
        ustawienia = os.path.join(self.katalog, "profil", "settings.json")
        self.assertIsNone(self.narzedzie("Edit", {"file_path": ustawienia, "old_string": "a", "new_string": "b"}))
        self.prompt("/blokuj-python")
        self.assertEqual(self.narzedzie("Edit", {"file_path": ustawienia, "old_string": "a", "new_string": "b"}), "deny")
        self.assertEqual(self.narzedzie("Write", {"file_path": str(KORZEN / "hooks" / "hooks.json"), "content": "{}"}), "deny")
        self.assertEqual(self.bash("claude plugin disable danaco-praca"), "deny")
        self.assertEqual(self.bash("jq '.disableAllHooks=true' a > b"), "deny")
        self.assertEqual(self.bash(f"echo x >> {ustawienia}"), "deny")


class TestPracaCiagla(Baza):
    def test_bez_trybu_stop_przechodzi(self):
        self.assertEqual(self.stop(), {})

    def test_stop_zablokowany_z_przypomnieniem(self):
        self.prompt("/praca napisz raport")
        wynik = self.stop()
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("napisz raport", wynik["reason"])
        self.assertIn("/koniec-pracy", wynik["reason"])

    def test_bezpiecznik_petli_i_reset_przez_narzedzie(self):
        self.prompt("/praca")
        for _ in range(3):
            self.assertEqual(self.stop().get("decision"), "block")
        wynik = self.stop()
        self.assertNotIn("decision", wynik)
        self.assertIn("bezpiecznik", wynik["systemMessage"])
        self.assertTrue(self.stan_sesji()["praca"]["wlaczona"])
        self.assertEqual(self.stop().get("decision"), "block")
        self.assertEqual(self.stop().get("decision"), "block")
        self.bash("echo praca")
        for _ in range(3):
            self.assertEqual(self.stop().get("decision"), "block")
        self.assertIn("bezpiecznik-petli", [w["zdarzenie"] for w in self.dziennik()])

    def test_wiadomosc_wlasciciela_zeruje_licznik(self):
        self.prompt("/praca")
        self.stop()
        self.stop()
        self.prompt("dalej, popraw testy")
        self.assertEqual(self.stan_sesji()["praca"]["bez_narzedzi"], {})

    def test_podagent_oddaje_wynik_od_razu(self):
        self.prompt("/praca")
        self.assertEqual(self.stop(podagent="ag1"), {})
        self.assertEqual(self.stop(podagent="ag1"), {})
        self.assertEqual(self.stop().get("decision"), "block")
        self.narzedzie("Bash", {"command": "ls"}, agent_id="ag1")
        self.assertEqual(self.stan_sesji()["praca"]["bez_narzedzi"], {"glowny": 1})
        wynik = self.hook("sesja", {"hook_event_name": "SubagentStart", "agent_id": "ag1"})
        self.assertIn("oddajesz wynik normalnie", wynik["hookSpecificOutput"]["additionalContext"])

    def test_koniec_pracy_zwalnia(self):
        self.prompt("/praca")
        self.assertEqual(self.stop().get("decision"), "block")
        wynik = self.prompt("/koniec-pracy")
        self.assertIn("wolno zakończyć turę", wynik["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.stop(), {})

    def test_praca_bez_ograniczen_narzedzi_i_miejsc(self):
        self.prompt("/praca")
        for nazwa, wejscie in (
            ("Bash", {"command": "cp -r /danaco/x /srv/y && python3 skrypt.py"}),
            ("Write", {"file_path": "/danaco/inny-projekt/a.md", "content": "x"}),
            ("Agent", {"prompt": "zbadaj", "run_in_background": True}),
            ("Bash", {"command": "npm test > test.log 2>&1", "run_in_background": True}),
            ("TaskOutput", {"task_id": "x", "block": False}),
            ("Monitor", {"command": "tail -f app.log | grep ERROR"}),
        ):
            with self.subTest(nazwa=nazwa):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))

    def test_praca_blokuje_czekanie_ale_nie_tlo(self):
        self.prompt("/praca")
        for polecenie in ("sleep 30", "timeout 100 sleep 90", "wait", "until [ -f x ]; do :; done",
                          "while ! curl -s localhost:8000; do sleep 1; done"):
            with self.subTest(polecenie=polecenie):
                self.assertEqual(self.bash(polecenie), "deny")
        for nazwa, wejscie in (("ScheduleWakeup", {"delaySeconds": 600}), ("TaskOutput", {"task_id": "x"}),
                               ("CronCreate", {"cron": "* * * * *"})):
            with self.subTest(nazwa=nazwa):
                self.assertEqual(self.narzedzie(nazwa, wejscie), "deny")
        for nazwa, wejscie in (("Bash", {"command": "sleep 600 && make raport", "run_in_background": True}),
                               ("Bash", {"command": "nohup sh -c 'until test -f x; do sleep 5; done; echo ok' > w.log 2>&1 &"})):
            with self.subTest(dozwolone=nazwa):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))


class TestBlokady(Baza):
    def przypadki(self, temat: str, odrzucane: list, przepuszczane: list):
        self.prompt(f"/blokuj-{temat}")
        for przypadek in odrzucane:
            nazwa, wejscie = przypadek if isinstance(przypadek, tuple) else ("Bash", {"command": przypadek})
            with self.subTest(odrzucane=wejscie):
                self.assertEqual(self.narzedzie(nazwa, wejscie), "deny")
        for przypadek in przepuszczane:
            nazwa, wejscie = przypadek if isinstance(przypadek, tuple) else ("Bash", {"command": przypadek})
            with self.subTest(przepuszczane=wejscie):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))

    def test_bash(self):
        self.przypadki("bash", ["ls", ("PowerShell", {"command": "dir"}), ("Monitor", {"command": "x"}),
                                ("mcp__terminal__run_in_terminal", {"command": "ls"})],
                       [("Read", {"file_path": "/etc/hostname"}), ("Grep", {"pattern": "x"}),
                        ("Write", {"file_path": f"{self.cwd}/a.md", "content": "x"})])

    def test_python(self):
        skrypt = os.path.join(self.cwd, "narzedzie")
        with open(skrypt, "w") as plik:
            plik.write("#!/usr/bin/env python3\nprint(1)\n")
        self.przypadki("python",
                       ["python3 a.py", "python -c 'print(1)'", "/usr/bin/python3.12 -m http.server", "pip install x",
                        "uv run x.py", "uvx ruff", "./skrypt.py", "bash -c 'python3 x'", "env python3 x",
                        "pytest -q", "poetry run x", f"{skrypt} --opcja", "cat > a.py <<'EOF'\nprint(1)\nEOF",
                        "echo 'print(1)' | tee b.py", "sudo -u x python3 y", "find . -exec python3 {} \\;",
                        ("Write", {"file_path": f"{self.cwd}/nowy.py", "content": "print(1)"}),
                        ("NotebookEdit", {"notebook_path": "a.ipynb", "new_source": "x"})],
                       ["ls", "node a.js", "grep -rn python README.md", "echo python", "git log --grep=python",
                        ("Edit", {"file_path": f"{self.cwd}/istniejacy.py", "old_string": "a", "new_string": "b"}),
                        ("Write", {"file_path": f"{self.cwd}/notatka.md", "content": "python3 a.py"})])

    def test_masowe(self):
        petla = os.path.join(self.cwd, "napraw.py")
        with open(petla, "w") as plik:
            plik.write("from pathlib import Path\nfor p in Path('.').rglob('*.md'):\n    p.write_text(p.read_text().replace('a','b'))\n")
        self.przypadki("masowe",
                       ["sed -i 's/a/b/' *.md", "sed -i 's/a/b/' a.txt b.txt", "perl -pi -e 's/a/b/' a b",
                        "find . -name '*.md' -exec sed -i 's/a/b/' {} +", "find . -type f -delete",
                        "grep -rl foo . | xargs sed -i 's/foo/bar/'", "for f in *.txt; do sed 's/a/b/' $f > $f.new; done",
                        "python3 -c \"from pathlib import Path\nfor p in Path('.').rglob('*'): p.write_text('x')\"",
                        f"python3 {petla}", "git checkout -- .", "git reset --hard HEAD", "patch -p1 < z.diff",
                        "sqlite3 b.db \"UPDATE t SET a = REPLACE(a,'x','y')\"", "psql -c 'DELETE FROM t'"],
                       ["sed -i 's/a/b/' jeden.txt", "for f in *.py; do wc -l $f; done",
                        "psql -c 'UPDATE t SET a=1 WHERE id=3'", "git checkout -b nowa", "cp a b",
                        ("Edit", {"file_path": "a.md", "old_string": "x", "new_string": "y", "replace_all": True})])

    def test_skrypty_pisanie_reczne(self):
        self.przypadki("skrypty",
                       ["echo x > plik.txt", "printf 'a' >> notatki.md", "cat > a.md <<'EOF'\nt\nEOF",
                        "sed -i 's/a/b/' jeden.txt", "echo x | tee plik.md", "python3 -c \"open('a','w').write('x')\"",
                        "truncate -s 0 a", "git apply z.diff"],
                       ["ls -la", "npm test > /tmp/test.log 2>&1", "grep x a > /dev/null", "cp a b", "rm a",
                        "echo x >> $TMPDIR/n.txt", "git commit -m x",
                        ("Write", {"file_path": f"{self.cwd}/a.md", "content": "x"})])

    def test_sleep(self):
        self.przypadki("sleep",
                       ["sleep 5", "timeout 30 sleep 10", "sleep 1 && make", "wait $PID", "tail -f app.log",
                        "watch -n 5 ls", "until curl -s x; do sleep 2; done", "python3 -c 'import time; time.sleep(3)'",
                        "ssh serwer 'sleep 100'", ("ScheduleWakeup", {"delaySeconds": 60}),
                        ("Monitor", {"command": "tail -f x"}), ("TaskOutput", {"task_id": "x", "block": True}),
                        ("BashOutput", {"bash_id": "x"}),
                        ("Bash", {"command": "sleep 600 && make", "run_in_background": True})],
                       ["ls", "echo sleep", "git commit -m 'usuń sleep'", "grep -rn sleep src/", "npm test",
                        "tail -n 20 app.log", ("TaskOutput", {"task_id": "x", "block": False}),
                        ("Bash", {"command": "while true; do date >> /tmp/m.log; sleep 60; done", "run_in_background": True})])

    def test_podagenci(self):
        self.przypadki("podagenci",
                       [("Agent", {"prompt": "x"}), ("Task", {"prompt": "x"}), ("Workflow", {"script": "x"}),
                        ("TeamCreate", {"name": "x"}), "claude -p 'zrób x'", "claude --print x"],
                       [("Read", {"file_path": "a"}), "claude --version", "ls"])

    def test_sudo(self):
        self.przypadki("sudo",
                       ["sudo ls", "sudo -u postgres psql", "ssh serwer 'sudo systemctl restart x'", "su -c 'ls'",
                        "doas ls", "pkexec ls", "nohup sudo make &", "find . -exec sudo rm {} \\;"],
                       ["ls", "echo sudo", "grep sudo /etc/group", "git commit -m 'bez sudo'"])
        self.prompt("/odblokuj-sudo")
        self.assertIsNone(self.bash("sudo ls"))

    def test_siec(self):
        self.przypadki("siec",
                       [("WebFetch", {"url": "http://x"}), ("WebSearch", {"query": "x"}), "curl http://x",
                        "wget http://x/a", "ssh serwer ls", "scp a serwer:/b", "git clone https://x/y.git",
                        "git pull", "pip install req", "npm install", "uv add req", "hf download org/model",
                        "rsync -a a serwer:/b"],
                       ["ls", "git status", "git diff", "git log", "npm test", "rsync -a a b", "cat plik",
                        ("Read", {"file_path": "a"})])

    def test_zapis_tylko_odczyt(self):
        self.przypadki("zapis",
                       [("Write", {"file_path": "a", "content": "x"}),
                        ("Edit", {"file_path": "a", "old_string": "x", "new_string": "y"}),
                        ("NotebookEdit", {"notebook_path": "a.ipynb", "new_source": "x"}),
                        "rm a", "mv a b", "cp a b", "mkdir nowy", "touch a", "echo x > a.txt",
                        "sed -i s/a/b/ a", "git commit -m x", "git add .", "truncate -s0 a"],
                       ["ls -la", "cat plik", "grep x a", "git diff", "git log --oneline", "git status",
                        "echo x > /tmp/a", "npm test > /tmp/t.log 2>&1", ("Read", {"file_path": "a"}),
                        ("Grep", {"pattern": "x"})])

    def test_pytania(self):
        self.przypadki("pytania",
                       [("AskUserQuestion", {"questions": []}), ("ExitPlanMode", {"plan": "x"})],
                       [("Read", {"file_path": "a"}), "ls", ("Write", {"file_path": f"{self.cwd}/a", "content": "x"})])


class TestTwardeZasady(Baza):
    def test_straz_sekretow_zawsze(self):
        self.assertEqual(self.bash("cat ~/.ssh/id_ed25519"), "deny")
        self.assertEqual(self.bash("git push --force origin main"), "ask")
        self.assertIsNone(self.bash("git status"))

    def test_straz_dysku_bez_dublowania(self):
        env = dict(self.env, DANACO_PRACA_STRAZ_DYSKU="wtyczka")
        mountinfo = Path("/proc/self/mountinfo").read_text()
        osobny_danaco = re.search(r" /danaco ", mountinfo) is not None
        wynik = self.hook("narzedzie", {"tool_name": "Bash", "tool_input": {"command": "sudo git clone https://x/y.git /opt/y"}}, env)
        self.assertEqual((wynik.get("hookSpecificOutput") or {}).get("permissionDecision"),
                         "deny" if osobny_danaco else None)
        os.makedirs(os.path.join(self.katalog, "profil"), exist_ok=True)
        with open(os.path.join(self.katalog, "profil", "settings.json"), "w") as plik:
            plik.write('{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"/usr/local/sbin/danaco-straz-dysku-hook"}]}]}}')
        env = dict(self.env)
        env.pop("DANACO_PRACA_STRAZ_DYSKU")
        wynik = self.hook("narzedzie", {"tool_name": "Bash", "tool_input": {"command": "sudo git clone https://x/y.git /opt/y"}}, env)
        self.assertEqual(wynik, {})

    def test_wbudowane_przypadki_strazy(self):
        for skrypt in ("straz_sekretow.py", "straz_dysku.py"):
            with self.subTest(skrypt=skrypt):
                wynik = subprocess.run([sys.executable, str(KORZEN / "scripts" / skrypt), "--test"],
                                       capture_output=True, text=True, timeout=60)
                self.assertEqual(wynik.returncode, 0, wynik.stdout + wynik.stderr)
                self.assertIn("błędy: 0", wynik.stdout)


class TestSesjaIWrapper(Baza):
    def test_sesja_przypomina_aktywne_tryby(self):
        self.assertEqual(self.hook("sesja", {"hook_event_name": "SessionStart", "source": "compact"}), {})
        self.prompt("/praca zadanie A\n/blokuj-python")
        wynik = self.hook("sesja", {"hook_event_name": "SessionStart", "source": "compact"})
        kontekst = wynik["hookSpecificOutput"]["additionalContext"]
        self.assertIn("zadanie A", kontekst)
        self.assertIn("Python         ZABLOKOWANE", kontekst)
        wynik = self.hook("sesja", {"hook_event_name": "SubagentStart", "agent_id": "ag1"})
        self.assertEqual(wynik["hookSpecificOutput"]["hookEventName"], "SubagentStart")

    def test_wrapper_fail_open(self):
        pusty = tempfile.mkdtemp(prefix="dp5-pusty-")
        try:
            os.makedirs(os.path.join(pusty, "hooks"))
            shutil.copy(WRAPPER, os.path.join(pusty, "hooks", "hak.sh"))
            env = dict(self.env, CLAUDE_PLUGIN_ROOT=pusty)
            wynik = subprocess.run(["sh", os.path.join(pusty, "hooks", "hak.sh"), "stop"], input="{}",
                                   capture_output=True, text=True, env=env, timeout=10)
            self.assertEqual(wynik.returncode, 0)
            self.assertEqual(wynik.stdout, "")
        finally:
            shutil.rmtree(pusty, ignore_errors=True)

    def test_zle_wejscie_nie_blokuje(self):
        for tryb in ("prompt", "narzedzie", "stop", "sesja"):
            wynik = subprocess.run(["sh", str(WRAPPER), tryb], input="to nie JSON", capture_output=True,
                                   text=True, env=self.env, timeout=10)
            self.assertEqual((wynik.returncode, wynik.stdout), (0, ""))


class TestRejestracja(unittest.TestCase):
    def test_hooks_json(self):
        dane = json.loads((KORZEN / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(dane), {"UserPromptSubmit", "PreToolUse", "Stop", "SessionStart", "SubagentStart"})
        for zdarzenie, wpisy in dane.items():
            for wpis in wpisy:
                for hook in wpis["hooks"]:
                    tryb = hook["command"].rsplit(" ", 1)[-1]
                    self.assertIn(tryb, ("prompt", "narzedzie", "stop", "sesja"), zdarzenie)

    def test_skille_polecen(self):
        katalogi = {p.name for p in (KORZEN / "skills").iterdir() if p.is_dir()}
        self.assertEqual(katalogi, set(P.POLECENIA))
        for nazwa in katalogi:
            tresc = (KORZEN / "skills" / nazwa / "SKILL.md").read_text()
            with self.subTest(skill=nazwa):
                self.assertRegex(tresc, r"(?m)^disable-model-invocation: true$")
                self.assertRegex(tresc, rf"(?m)^name: {re.escape(nazwa)}$")

    def test_wersja(self):
        self.assertEqual(json.loads((KORZEN / ".claude-plugin" / "plugin.json").read_text())["version"], "5.2.0")


if __name__ == "__main__":
    unittest.main()
