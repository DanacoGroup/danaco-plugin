#!/usr/bin/env python3
"""Testy narzędzi wtyczki danaco-konfiguracja (unittest, bez sieci).

Testy z CLI (atrapa API, `claude doctor`) uruchamiają się, gdy zmienna CLAUDE_BIN wskazuje binarkę.
Wszystkie pliki tymczasowe powstają w $TMPDIR.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[1]
S = KORZEN / "skills"
PY = sys.executable
CLI = os.environ.get("CLAUDE_BIN", "")
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402


def uruchom(*argumenty: str, wejscie: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *argumenty], capture_output=True, text=True, input=wejscie, timeout=300)


def plik_json(dane: dict | str, przyrostek: str = ".json") -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=przyrostek, delete=False, encoding="utf-8")
    f.write(dane if isinstance(dane, str) else json.dumps(dane))
    f.close()
    return Path(f.name)


class Indeksy(unittest.TestCase):
    def test_liczebnosc(self):
        self.assertGreaterEqual(len(cc.klucze_ustawien()), 240)
        self.assertGreaterEqual(len(cc.zmienne()), 370)
        self.assertGreaterEqual(len(cc.flagi()), 75)
        self.assertGreaterEqual(len(cc.narzedzia()), 40)
        self.assertGreaterEqual(len(cc.zdarzenia_hookow()), 30)

    def test_kolumny_pl_zachowane(self):
        z_opisem = [k for k, w in cc.klucze_ustawien().items() if w.get("co_robi_pl")]
        self.assertGreater(len(z_opisem), 200)

    def test_sekret(self):
        self.assertTrue(cc.wygladaja_na_sekret("DANACO_MCP_TOKEN"))
        self.assertFalse(cc.wygladaja_na_sekret("MAX_THINKING_TOKENS"))
        self.assertFalse(cc.wygladaja_na_sekret("CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR"))


class Walidator(unittest.TestCase):
    W = str(KORZEN / "scripts" / "waliduj_ustawienia.py")

    def test_poprawny(self):
        p = plik_json({"permissions": {"allow": ["Bash(npm test *)"], "deny": ["Read(./.env)"]}})
        self.assertEqual(uruchom(self.W, str(p), "--rodzaj", "project").returncode, 0)

    def test_niepoprawny_json(self):
        p = plik_json('{"permissions": {"allow": ["Read",]}}')
        self.assertEqual(uruchom(self.W, str(p)).returncode, 1)

    def test_sekret_nie_wypisany(self):
        p = plik_json({"env": {"MOJ_API_KEY": "wartosc-tajna-123"}})
        w = uruchom(self.W, str(p))
        self.assertEqual(w.returncode, 1)
        self.assertNotIn("wartosc-tajna-123", w.stdout + w.stderr)

    def test_gola_edit_i_scrub(self):
        p = plik_json({"permissions": {"defaultMode": "acceptEdits", "allow": ["Edit"]},
                       "env": {"CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1"}})
        w = uruchom(self.W, str(p))
        self.assertIn("goła nazwa „Edit”", w.stdout)
        self.assertIn("wymusza tryb „default”", w.stdout)

    def test_zasieg(self):
        p = plik_json({"allowManagedPermissionRulesOnly": True})
        w = uruchom(self.W, str(p), "--rodzaj", "project")
        self.assertIn("allowManagedPermissionRulesOnly", w.stdout)


class Generator(unittest.TestCase):
    def test_profile(self):
        for profil in ("czat", "kod", "ci", "tylko-odczyt"):
            with self.subTest(profil=profil):
                wyj = Path(tempfile.mkdtemp(prefix=f"gen-{profil}-"))
                w = uruchom(str(KORZEN / "scripts/generuj_ustawienia.py"), "--profil", profil, "--nazwa", "t",
                            "--wyjscie", str(wyj))
                self.assertEqual(w.returncode, 0, w.stdout + w.stderr)
                flagi = (wyj / f"t-{profil}.flagi.txt").read_text()
                self.assertIn("--strict-mcp-config", flagi)
                self.assertIn("--permission-mode", flagi)
                lk = uruchom(str(S / "bezpieczenstwo-wdrozenia/scripts/lista_kontrolna.py"), "--profil", "usluga",
                             "--ustawienia", str(wyj / f"t-{profil}.settings.json"), "--flagi", str(wyj / f"t-{profil}.flagi.txt"),
                             "--zmienne", str(wyj / f"t-{profil}.zmienne.txt"))
                self.assertEqual(lk.returncode, 0, lk.stdout)

    def test_ci_bez_golego_edit(self):
        wyj = Path(tempfile.mkdtemp(prefix="gen-ci2-"))
        uruchom(str(KORZEN / "scripts/generuj_ustawienia.py"), "--profil", "ci", "--nazwa", "t", "--wyjscie", str(wyj))
        allow = json.loads((wyj / "t-ci.settings.json").read_text())["permissions"]["allow"]
        self.assertNotIn("Edit", allow)
        self.assertIn("Edit(./**)", allow)


class ListaKontrolna(unittest.TestCase):
    def test_slaba_konfiguracja(self):
        p = plik_json({"permissions": {"defaultMode": "bypassPermissions", "allow": ["Bash"]},
                       "skipDangerousModePermissionPrompt": True})
        w = uruchom(str(S / "bezpieczenstwo-wdrozenia/scripts/lista_kontrolna.py"), "--profil", "stanowisko", "--ustawienia", str(p))
        self.assertEqual(w.returncode, 1)
        for ident in ("U01", "U04", "U07"):
            self.assertRegex(w.stdout, rf"\[BRAK\s*\] {ident}")


class Zarzadzane(unittest.TestCase):
    def test_scalanie_i_first_wins(self):
        a = plik_json({"permissions": {"deny": ["Bash(curl *)"]}, "fallbackModel": ["sonnet", "haiku"], "model": "opus"})
        b = plik_json({"permissions": {"deny": ["Bash(wget *)"]}, "fallbackModel": ["haiku"], "model": "sonnet"})
        z = plik_json({"permissions": {"deny": ["Read(./.env)"]}})
        wyj = Path(tempfile.mkdtemp()) / "scalona.json"
        w = uruchom(str(S / "zarzadzanie-flota/scripts/sprawdz_zarzadzane.py"), "--glowny", str(a), "--dodatki", str(b),
                    "--zdalne", str(z), "--wyjscie", str(wyj))
        scalona = json.loads(wyj.read_text())
        self.assertEqual(scalona["permissions"]["deny"], ["Bash(curl *)", "Bash(wget *)"])
        self.assertEqual(scalona["fallbackModel"], ["haiku"])
        self.assertEqual(scalona["model"], "sonnet")
        self.assertIn("POMINIĘTE", w.stdout)

    def test_niepoprawny_json_blokuje_start(self):
        a = plik_json('{"model": "opus",}')
        w = uruchom(str(S / "zarzadzanie-flota/scripts/sprawdz_zarzadzane.py"), "--glowny", str(a))
        self.assertEqual(w.returncode, 1)
        self.assertIn("ODMÓWI STARTU", w.stdout)


class Zmienne(unittest.TestCase):
    def test_literowka_i_bledy(self):
        p = plik_json("CLAUDE_CODE_DISABLE_AUTOMEMORY=1\nCLAUDE_CODE_PROJECT_DIR_NAME=a/b\nTOKEN_X=tajne\n", ".env")
        w = uruchom(str(S / "zmienne-srodowiskowe/scripts/sprawdz_zmienne.py"), "--plik", str(p))
        self.assertEqual(w.returncode, 1)
        self.assertIn("CLAUDE_CODE_DISABLE_AUTO_MEMORY", w.stdout)
        self.assertIn("tylko razem z CLAUDE_CONFIG_DIR", w.stdout)
        self.assertNotIn("tajne", w.stdout)


class Cache(unittest.TestCase):
    def test_analiza_transkryptu(self):
        wpisy = [
            {"type": "assistant", "sessionId": "s1", "timestamp": "2026-10-02T10:00:00Z",
             "message": {"id": "m1", "model": "claude-opus-5-5", "usage": {"input_tokens": 5, "cache_read_input_tokens": 0,
                         "cache_creation_input_tokens": 50000, "output_tokens": 10,
                         "cache_creation": {"ephemeral_1h_input_tokens": 50000, "ephemeral_5m_input_tokens": 0}}}},
            {"type": "assistant", "sessionId": "s1", "timestamp": "2026-10-02T10:01:00Z",
             "message": {"id": "m2", "model": "claude-opus-5-5", "usage": {"input_tokens": 5, "cache_read_input_tokens": 50000,
                         "cache_creation_input_tokens": 1000, "output_tokens": 10}}},
            {"type": "assistant", "sessionId": "s1", "timestamp": "2026-10-02T10:02:00Z",
             "message": {"id": "m3", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 5, "cache_read_input_tokens": 0,
                         "cache_creation_input_tokens": 52000, "output_tokens": 10}}},
        ]
        p = plik_json("\n".join(json.dumps(w) for w in wpisy), ".jsonl")
        w = uruchom(str(S / "model-cache-i-koszty/scripts/analiza_cache.py"), str(p), "--json")
        r = json.loads(w.stdout)["s1"]
        self.assertEqual(r["zadania"], 3)
        self.assertEqual(len(r["chybienia"]), 1)
        self.assertTrue(r["chybienia"][0]["zmiana_modelu"])

    def test_zadania_cache(self):
        katalog = Path(tempfile.mkdtemp())
        zadanie = {"model": "m", "output_config": {"effort": "medium"}, "system": [
            {"type": "text", "text": "a"}, {"type": "text", "text": "b", "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
            "messages": [], "tools": []}
        (katalog / "001-POST-v1_messages.json").write_text(json.dumps({"headers": {"anthropic-beta": "extended-cache-ttl-2025-04-11"}})
                                                           + "\n" + json.dumps(zadanie))
        w = uruchom(str(S / "model-cache-i-koszty/scripts/zadania_cache.py"), str(katalog), "--json")
        z = json.loads(w.stdout)["a"][0]
        self.assertEqual(z["znaczniki"][0]["ttl"], "1h")
        self.assertTrue(z["beta_ttl_1h"])


class Przyklady(unittest.TestCase):
    def test_wszystkie_przyklady(self):
        argumenty = [str(KORZEN / "scripts/sprawdz_przyklady.py")] + (["--cli", CLI] if CLI else [])
        w = uruchom(*argumenty)
        self.assertEqual(w.returncode, 0, w.stdout[-3000:])


@unittest.skipUnless(CLI, "ustaw CLAUDE_BIN, by uruchomić próby z CLI")
class ProbyCLI(unittest.TestCase):
    def test_atrapa_i_tryb(self):
        w = uruchom(str(KORZEN / "scripts/proba_cli.py"), "--json", "--", "--permission-mode", "dontAsk")
        r = json.loads(w.stdout)
        self.assertEqual((r.get("init") or {}).get("permissionMode"), "dontAsk")
        self.assertEqual((r.get("wynik") or {}).get("subtype"), "success")

    def test_wtyczka_laduje_sie(self):
        w = uruchom(str(KORZEN / "scripts/proba_cli.py"), "--json", "--", "--permission-mode", "dontAsk",
                    "--plugin-dir", str(KORZEN))
        init = json.loads(w.stdout).get("init") or {}
        skille = [s for s in init.get("skills", []) if s.startswith("danaco-konfiguracja:")]
        self.assertEqual(len(skille), 15)
        self.assertFalse(init.get("plugin_errors"))

    def test_plugin_validate(self):
        # Katalog zawiera też marketplace.json, który przy gołym `validate <katalog>` ma
        # pierwszeństwo — manifest wtyczki sprawdzamy więc po jawnej ścieżce.
        manifest = KORZEN / ".claude-plugin/plugin.json"
        w = subprocess.run([CLI, "plugin", "validate", "--strict", str(manifest)], capture_output=True, text=True, timeout=120)
        self.assertEqual(w.returncode, 0, w.stdout + w.stderr)

    def test_marketplace_validate(self):
        rynek = KORZEN / ".claude-plugin/marketplace.json"
        w = subprocess.run([CLI, "plugin", "validate", str(rynek)], capture_output=True, text=True, timeout=120)
        self.assertEqual(w.returncode, 0, w.stdout + w.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
