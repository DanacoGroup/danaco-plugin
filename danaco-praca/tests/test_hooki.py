#!/usr/bin/env python3
"""Testy hooków danaco-praca 5: każde zdarzenie i każde polecenie na wejściach JSON.

Hooki są uruchamiane tak jak przez klienta: wrapper `hooks/hak.sh` z JSON-em zdarzenia na
stdin. Stan trafia do katalogu tymczasowego (`DANACO_PRACA_STAN`), więc testy nie dotykają
danych prawdziwej instalacji.
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


class Baza(unittest.TestCase):
    def setUp(self):
        self.katalog = tempfile.mkdtemp(prefix="dp5-test-")
        self.stan = os.path.join(self.katalog, "stan")
        self.cwd = os.path.join(self.katalog, "projekt")
        os.makedirs(self.cwd)
        self.env = dict(os.environ, DANACO_PRACA_STAN=self.stan, DANACO_PRACA_STRAZ_DYSKU="system",
                        CLAUDE_PLUGIN_ROOT=str(KORZEN), CLAUDE_CONFIG_DIR=os.path.join(self.katalog, "profil"),
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
    def test_kazde_polecenie_zmienia_stan(self):
        for polecenie, cel in P.POLECENIA.items():
            if cel is None:
                continue
            klucz, wartosc = cel
            with self.subTest(polecenie=polecenie):
                wynik = self.prompt(f"/{polecenie}")
                self.assertIn("additionalContext", wynik["hookSpecificOutput"])
                self.assertIn("zapisano", wynik["systemMessage"])
                stan = self.stan_sesji()
                aktualna = stan["praca"]["wlaczona"] if klucz == "praca" else stan["blokady"][klucz]
                self.assertEqual(aktualna, wartosc)

    def test_pary_wlacz_wylacz(self):
        for wlacz, wylacz in (("bez-bash", "z-bash"), ("bez-python", "z-python"), ("bez-masowych", "z-masowymi"),
                              ("reczne-pisanie", "z-skryptami"), ("bez-sleep", "z-sleep"),
                              ("bez-podagentow", "z-podagentami"), ("sudo-nie", "sudo-tak"), ("praca", "koniec-pracy")):
            klucz = P.POLECENIA[wlacz][0]
            with self.subTest(para=wlacz):
                self.prompt(f"/{wlacz}")
                stan = self.stan_sesji()
                self.assertTrue(stan["praca"]["wlaczona"] if klucz == "praca" else stan["blokady"][klucz])
                self.prompt(f"/{wylacz}")
                stan = self.stan_sesji()
                self.assertFalse(stan["praca"]["wlaczona"] if klucz == "praca" else stan["blokady"][klucz])

    def test_tryb_pokazuje_stan_bez_modelu(self):
        self.prompt("/bez-python")
        wynik = self.prompt("/tryb")
        self.assertEqual(wynik["decision"], "block")
        self.assertIn("Python         ZABLOKOWANE", wynik["reason"])
        for nazwa in ("praca ciągła", "Bash", "praca masowa", "pisanie ręczne", "uśpienie", "podagenci", "sudo"):
            self.assertIn(nazwa, wynik["reason"])

    def test_praca_zapisuje_zlecenie(self):
        wynik = self.prompt("/praca zbuduj raport\nszczegóły w pliku a.md")
        stan = self.stan_sesji()
        self.assertTrue(stan["praca"]["wlaczona"])
        self.assertEqual(stan["praca"]["zlecenie"], "zbuduj raport\nszczegóły w pliku a.md")
        self.assertIn("zbuduj raport", wynik["hookSpecificOutput"]["additionalContext"])

    def test_prefiks_wtyczki_i_kilka_polecen(self):
        self.prompt("/danaco-praca:bez-bash\n/sudo-nie")
        stan = self.stan_sesji()
        self.assertTrue(stan["blokady"]["bash"])
        self.assertTrue(stan["blokady"]["sudo"])

    def test_postac_rozwinieta(self):
        self.prompt("<command-message>praca</command-message>\n<command-name>/danaco-praca:praca</command-name>\n<command-args>zadanie X</command-args>")
        self.assertEqual(self.stan_sesji()["praca"]["zlecenie"], "zadanie X")

    def test_wzmianka_nie_jest_poleceniem(self):
        for tekst in ("opisz polecenie /koniec-pracy w README", "zobacz skills/praca/SKILL.md", "/pracak", "a /bez-bash"):
            with self.subTest(tekst=tekst):
                self.assertEqual(self.prompt(tekst), {})
        self.assertFalse(os.path.exists(os.path.join(self.stan, "sesje", "sesja-a.json")))

    def test_stan_osobny_na_sesje(self):
        self.prompt("/bez-bash", sesja="sesja-a")
        self.assertEqual(self.narzedzie("Bash", {"command": "ls"}, sesja="sesja-a"), "deny")
        self.assertIsNone(self.narzedzie("Bash", {"command": "ls"}, sesja="sesja-b"))

    def test_dziennik_zmian(self):
        self.prompt("/bez-bash")
        self.prompt("/z-bash")
        wpisy = [w for w in self.dziennik() if w["zdarzenie"] == "polecenie"]
        self.assertEqual([w["polecenia"] for w in wpisy], [["bez-bash"], ["z-bash"]])
        self.assertTrue(all(w["sesja"] == "sesja-a" and "podpis_migawki" in w for w in wpisy))


class TestOchronaStanu(Baza):
    def test_zmieniony_plik_stanu_wraca_z_dziennika(self):
        self.prompt("/bez-bash")
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
        self.assertEqual(self.narzedzie("Skill", {"skill": "danaco-praca:z-bash"}), "deny")
        self.assertEqual(self.narzedzie("SendMessage", {"to": "main", "message": "/koniec-pracy"}), "deny")
        self.assertEqual(self.bash("echo '/koniec-pracy' | claude -p"), "deny")
        self.assertEqual(self.bash("claude -p --resume abc 'dalej'"), "deny")
        self.assertIsNone(self.narzedzie("Skill", {"skill": "dataviz"}))
        self.assertIsNone(self.bash("ls skills/praca/SKILL.md"))
        self.assertIsNone(self.bash("ls ~/.claude/plugins/data/"))

    def test_ochrona_mechanizmu_tylko_przy_aktywnym_trybie(self):
        ustawienia = os.path.join(self.katalog, "profil", "settings.json")
        self.assertIsNone(self.narzedzie("Edit", {"file_path": ustawienia, "old_string": "a", "new_string": "b"}))
        self.prompt("/bez-python")
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
        # Po interwencji licznik od zera; wywołanie narzędzia też go zeruje.
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
        # Wywołanie narzędzia przez podagenta nie zeruje licznika agenta głównego.
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
        ):
            with self.subTest(nazwa=nazwa):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))

    def test_praca_blokuje_czekanie(self):
        self.prompt("/praca")
        for polecenie in ("sleep 30", "timeout 100 sleep 90", "wait", "until [ -f x ]; do :; done",
                          "while ! curl -s localhost:8000; do sleep 1; done"):
            with self.subTest(polecenie=polecenie):
                self.assertEqual(self.bash(polecenie), "deny")
        for nazwa, wejscie in (("ScheduleWakeup", {"delaySeconds": 600}), ("TaskOutput", {"task_id": "x"}),
                               ("CronCreate", {"cron": "* * * * *"})):
            with self.subTest(nazwa=nazwa):
                self.assertEqual(self.narzedzie(nazwa, wejscie), "deny")
        # Monitoring wolno stawiać (narzędzie Monitor i procesy w tle); agent pracuje dalej.
        for nazwa, wejscie in (("Monitor", {"command": "tail -f app.log | grep --line-buffered ERROR"}),
                               ("Bash", {"command": "sleep 600 && make raport", "run_in_background": True}),
                               ("Bash", {"command": "nohup sh -c 'until test -f x; do sleep 5; done; echo ok' > w.log 2>&1 &"})):
            with self.subTest(dozwolone=nazwa):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))


class TestBlokady(Baza):
    def przypadki(self, polecenie_wl: str, odrzucane: list, przepuszczane: list):
        self.prompt(f"/{polecenie_wl}")
        for przypadek in odrzucane:
            nazwa, wejscie = przypadek if isinstance(przypadek, tuple) else ("Bash", {"command": przypadek})
            with self.subTest(odrzucane=wejscie):
                self.assertEqual(self.narzedzie(nazwa, wejscie), "deny")
        for przypadek in przepuszczane:
            nazwa, wejscie = przypadek if isinstance(przypadek, tuple) else ("Bash", {"command": przypadek})
            with self.subTest(przepuszczane=wejscie):
                self.assertIsNone(self.narzedzie(nazwa, wejscie))

    def test_bez_bash(self):
        self.przypadki("bez-bash", ["ls", ("PowerShell", {"command": "dir"}), ("Monitor", {"command": "x"}),
                                    ("mcp__terminal__run_in_terminal", {"command": "ls"})],
                       [("Read", {"file_path": "/etc/hostname"}), ("Grep", {"pattern": "x"}),
                        ("Write", {"file_path": f"{self.cwd}/a.md", "content": "x"})])

    def test_bez_python(self):
        skrypt = os.path.join(self.cwd, "narzedzie")
        with open(skrypt, "w") as plik:
            plik.write("#!/usr/bin/env python3\nprint(1)\n")
        self.przypadki("bez-python",
                       ["python3 a.py", "python -c 'print(1)'", "/usr/bin/python3.12 -m http.server", "pip install x",
                        "uv run x.py", "uvx ruff", "./skrypt.py", "bash -c 'python3 x'", "env python3 x",
                        "pytest -q", "poetry run x", f"{skrypt} --opcja", "cat > a.py <<'EOF'\nprint(1)\nEOF",
                        "echo 'print(1)' | tee b.py", "sudo -u x python3 y", "find . -exec python3 {} \\;",
                        ("Write", {"file_path": f"{self.cwd}/nowy.py", "content": "print(1)"}),
                        ("Write", {"file_path": f"{self.cwd}/narzedzie2", "content": "#!/usr/bin/python3\nx"}),
                        ("NotebookEdit", {"notebook_path": "a.ipynb", "new_source": "x"})],
                       ["ls", "node a.js", "grep -rn python README.md", "echo python", "git log --grep=python",
                        ("Edit", {"file_path": f"{self.cwd}/istniejacy.py", "old_string": "a", "new_string": "b"}),
                        ("Write", {"file_path": f"{self.cwd}/notatka.md", "content": "python3 a.py"})])

    def test_bez_masowych(self):
        petla = os.path.join(self.cwd, "napraw.py")
        with open(petla, "w") as plik:
            plik.write("from pathlib import Path\nfor p in Path('.').rglob('*.md'):\n    p.write_text(p.read_text().replace('a','b'))\n")
        powloka = os.path.join(self.cwd, "napraw.sh")
        with open(powloka, "w") as plik:
            plik.write("#!/bin/bash\nfor f in *.txt; do sed -i 's/a/b/' \"$f\"; done\n")
        self.przypadki("bez-masowych",
                       ["sed -i 's/a/b/' *.md", "sed -i 's/a/b/' a.txt b.txt", "sed -i.bak -e 's/a/b/' -r src/",
                        "perl -pi -e 's/a/b/' a b", "find . -name '*.md' -exec sed -i 's/a/b/' {} +",
                        "find . -type f -delete", "grep -rl foo . | xargs sed -i 's/foo/bar/'",
                        "for f in *.txt; do sed 's/a/b/' $f > $f.new; done",
                        "for f in $(ls); do mv \"$f\" \"x$f\"; done",
                        "python3 -c \"from pathlib import Path\nfor p in Path('.').rglob('*'): p.write_text('x')\"",
                        f"python3 {petla}", f"bash {powloka}", "git checkout -- .", "git reset --hard HEAD",
                        "patch -p1 < zmiana.diff", "rename 's/a/b/' *.txt",
                        "sqlite3 baza.db \"UPDATE wpisy SET tresc = REPLACE(tresc, 'a', 'b')\"",
                        "psql -c 'DELETE FROM wpisy'"],
                       ["sed -i 's/a/b/' jeden.txt", "sed -n '1,5p' a b c", "for f in *.py; do wc -l $f; done",
                        "find . -name '*.md' -exec grep -l x {} +", "grep -rl foo . | xargs wc -l",
                        "psql -c 'UPDATE wpisy SET a=1 WHERE id=3'", "git checkout -b nowa", "cp a b",
                        ("Edit", {"file_path": "a.md", "old_string": "x", "new_string": "y", "replace_all": True}),
                        ("Write", {"file_path": f"{self.cwd}/a.md", "content": "x"})])

    def test_reczne_pisanie(self):
        skrypt = os.path.join(self.cwd, "gen.js")
        with open(skrypt, "w") as plik:
            plik.write("require('fs').writeFileSync('a.txt', 'x')\n")
        self.przypadki("reczne-pisanie",
                       ["echo x > plik.txt", "printf 'a' >> notatki.md", "cat > a.md <<'EOF'\ntekst\nEOF",
                        "sed -i 's/a/b/' jeden.txt", "echo x | tee plik.md", "python3 -c \"open('a','w').write('x')\"",
                        f"node {skrypt}", "truncate -s 0 a", "dd if=/dev/zero of=plik bs=1 count=1",
                        "git apply zmiana.diff"],
                       ["ls -la", "npm test > /tmp/test.log 2>&1", "make > build.log 2>&1", "grep x a > /dev/null",
                        "cp a b", "mv a b", "rm a", "mkdir -p x", "echo x >> $TMPDIR/n.txt", "git commit -m x",
                        ("Write", {"file_path": f"{self.cwd}/a.md", "content": "x"}),
                        ("Edit", {"file_path": f"{self.cwd}/a.md", "old_string": "x", "new_string": "y"})])

    def test_bez_sleep(self):
        self.przypadki("bez-sleep",
                       ["sleep 5", "timeout 30 sleep 10", "sleep 1 && make", "wait $PID", "tail -f app.log",
                        "watch -n 5 ls", "until curl -s x; do sleep 2; done", "while pgrep make; do :; done",
                        "python3 -c 'import time; time.sleep(3)'", "ssh serwer 'sleep 100'",
                        "bash -c \"while true; do sleep 5; done\"", "inotifywait -e modify a",
                        "docker wait kontener", "gh run watch 123",
                        ("ScheduleWakeup", {"delaySeconds": 60}), ("Monitor", {"command": "tail -f x"}),
                        ("TaskOutput", {"task_id": "x", "block": True}), ("BashOutput", {"bash_id": "x"}),
                        ("mcp__computer-use__wait", {"duration": 3}),
                        ("mcp__playwright__browser_wait_for", {"time": 5}),
                        ("Bash", {"command": "sleep 600 && make raport", "run_in_background": True})],
                       ["ls", "echo sleep", "git commit -m 'usuń sleep'", "grep -rn sleep src/", "npm test",
                        "while read l; do echo $l; done < plik", "tail -n 20 app.log",
                        ("Bash", {"command": "while true; do date >> /tmp/monitor.log; sleep 60; done",
                                  "run_in_background": True}),
                        ("Bash", {"command": "nohup sh -c 'while true; do df -h >> dysk.log; sleep 300; done' &"}),
                        ("TaskOutput", {"task_id": "x", "block": False})])

    def test_bez_podagentow(self):
        self.przypadki("bez-podagentow",
                       [("Agent", {"prompt": "x"}), ("Task", {"prompt": "x"}), ("Workflow", {"script": "x"}),
                        ("TeamCreate", {"name": "x"}), "claude -p 'zrób x'", "claude --print x"],
                       [("Read", {"file_path": "a"}), "claude --version", "ls"])

    def test_sudo_nie_i_tak(self):
        self.przypadki("sudo-nie",
                       ["sudo ls", "sudo -u postgres psql", "ssh serwer 'sudo systemctl restart x'", "su -c 'ls'",
                        "doas ls", "pkexec ls", "nohup sudo make &", "find . -exec sudo rm {} \\;"],
                       ["ls", "echo sudo", "grep sudo /etc/group", "git commit -m 'bez sudo'"])
        self.prompt("/sudo-tak")
        self.assertIsNone(self.bash("sudo ls"))


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
        # Hook konta (danaco-straz-dysku-hook) już pilnuje dysku: wtyczka milczy.
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
        self.prompt("/praca zadanie A\n/bez-python")
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
        self.assertEqual(json.loads((KORZEN / ".claude-plugin" / "plugin.json").read_text())["version"], "5.0.0")


if __name__ == "__main__":
    unittest.main()
