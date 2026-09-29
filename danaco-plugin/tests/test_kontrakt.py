#!/usr/bin/env python3
"""Testy narzędzi kontraktu i granic (contract_tool, modes_tool, channel_tool,
workflow_tool, tauri_check).

Uruchomienie:
    python3 tests/test_kontrakt.py
    python3 -m pytest tests/test_kontrakt.py

Sprawdzane są przede wszystkim dwie rzeczy: że niepoprawny plik danych daje kod
z kontraktu narzędzia (0/2/3/4) i komunikat, nigdy traceback z kodem 1, oraz że
ścieżka zapisu pochodząca z danych nie wyprowadza poza korzeń repozytorium.
Wszystko dzieje się w katalogu tymczasowym.
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
SKRYPTY = KORZEN_PLUGINU / "skills"
CONTRACT_TOOL = SKRYPTY / "kontrakt-zrodlo-prawdy" / "scripts" / "contract_tool.py"
MODES_TOOL = SKRYPTY / "macierz-trybow-sesji" / "scripts" / "modes_tool.py"
CHANNEL_TOOL = SKRYPTY / "kanal-websocket" / "scripts" / "channel_tool.py"
WORKFLOW_TOOL = SKRYPTY / "orkiestracja-agentow" / "scripts" / "workflow_tool.py"
TAURI_CHECK = SKRYPTY / "most-tauri" / "scripts" / "tauri_check.py"
PYTHON = sys.executable

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_DRIFT = 3
EXIT_IO = 4

KONTRAKT_MINIMALNY = {
    "contractVersion": "1.0.0",
    "enums": [],
    "types": [{"name": "Ping", "fields": [{"name": "sesja", "type": "string"}]}],
    "modes": [],
    "messages": [{"name": "SessionPing", "channel": "session", "direction": "clientToServer",
                  "payload": "Ping"}],
    "commands": [],
    "errors": [{"code": "E_SESSION_UNKNOWN", "message": "Nieznana sesja."}],
}


class BazaKontraktu(unittest.TestCase):
    def setUp(self) -> None:
        self.tymczasowy = tempfile.TemporaryDirectory(prefix="kontrakt-test-")
        self.repo = Path(self.tymczasowy.name) / "repo"
        (self.repo / "shared").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tymczasowy.cleanup()

    def zapisz_kontrakt(self, dane, nazwa: str = "shared/contract.json") -> Path:
        cel = self.repo / nazwa
        cel.parent.mkdir(parents=True, exist_ok=True)
        tresc = dane if isinstance(dane, str) else json.dumps(dane, ensure_ascii=False)
        cel.write_text(tresc, encoding="utf-8")
        return cel

    def uruchom(self, skrypt: Path, *argumenty: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([PYTHON, str(skrypt), *argumenty],
                              capture_output=True, text=True, encoding="utf-8", env=env,
                              cwd=str(self.repo))

    def sprawdz_bez_tracebacku(self, wynik: subprocess.CompletedProcess) -> None:
        self.assertNotIn("Traceback", wynik.stderr)
        self.assertIn(wynik.returncode, (EXIT_OK, EXIT_INVALID, EXIT_DRIFT, EXIT_IO),
                      f"kod {wynik.returncode} poza kontraktem narzędzia")


class TestWalidacjaKontraktu(BazaKontraktu):
    def test_kontrakt_minimalny_jest_poprawny(self):
        self.zapisz_kontrakt(KONTRAKT_MINIMALNY)
        wynik = self.uruchom(CONTRACT_TOOL, "validate", "--root", str(self.repo))
        self.assertEqual(wynik.returncode, EXIT_OK, wynik.stderr)

    def test_zepsute_kontrakty_daja_kod_walidacji(self):
        """Regresja A2-06: walidator nie może przewracać się na tym, co ma zgłaszać."""
        przypadki = (
            {"enums": [{"values": [{"name": "Full", "value": "full"}]}]},
            {"types": [{"fields": [{"name": "a", "type": "string"}]}]},
            {"contractVersion": "1.0.0", "enums": [{"name": "IsolationLevel",
                                                    "values": [{"name": "Full"}]}]},
            [],
            {"contractVersion": "1.0.0", "messages": [{"channel": "ai"}]},
            {"contractVersion": "1.0.0", "types": "nie lista"},
            {"contractVersion": "1.0.0", "commands": [{"request": "Brak"}]},
            {"contractVersion": "1.0.0", "errors": ["nie obiekt"]},
            {"contractVersion": "1.0.0", "modes": ["nie obiekt"]},
        )
        for indeks, kontrakt in enumerate(przypadki):
            with self.subTest(indeks=indeks):
                self.zapisz_kontrakt(kontrakt)
                wynik = self.uruchom(CONTRACT_TOOL, "validate", "--root", str(self.repo))
                self.sprawdz_bez_tracebacku(wynik)
                self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)

    def test_kontrakt_nie_jest_json(self):
        self.zapisz_kontrakt("{to nie json")
        wynik = self.uruchom(CONTRACT_TOOL, "validate", "--root", str(self.repo))
        self.assertEqual(wynik.returncode, EXIT_INVALID)
        self.sprawdz_bez_tracebacku(wynik)

    def test_brak_pliku_kontraktu(self):
        wynik = self.uruchom(CONTRACT_TOOL, "validate", "--root", str(self.repo))
        self.assertEqual(wynik.returncode, EXIT_IO)


class TestSciezkiZapisu(BazaKontraktu):
    """Regresja A2-05: ścieżka z danych nie może wyprowadzać poza korzeń."""

    def _kontrakt_ze_sciezka(self, go: str, ts: str) -> None:
        kontrakt = dict(KONTRAKT_MINIMALNY)
        kontrakt["generated"] = {"go": {"path": go}, "ts": {"path": ts}}
        self.zapisz_kontrakt(kontrakt)

    def test_sciezka_wychodzaca_przez_dwie_kropki(self):
        self._kontrakt_ze_sciezka("../poza/x.go", "client/src/contract.ts")
        wynik = self.uruchom(CONTRACT_TOOL, "gen", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)
        self.assertIn("poza korzeń", wynik.stderr)
        self.assertFalse((self.repo.parent / "poza").exists())

    def test_sciezka_absolutna(self):
        cel = Path(self.tymczasowy.name) / "poza" / "x.ts"
        self._kontrakt_ze_sciezka("shared/contract.go", str(cel))
        wynik = self.uruchom(CONTRACT_TOOL, "gen", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)
        self.assertFalse(cel.exists())

    def test_sciezka_w_korzeniu_dziala(self):
        self._kontrakt_ze_sciezka("shared/contract.go", "client/src/contract.ts")
        wynik = self.uruchom(CONTRACT_TOOL, "gen", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_OK, wynik.stderr)
        self.assertTrue((self.repo / "shared" / "contract.go").is_file())
        self.assertTrue((self.repo / "client" / "src" / "contract.ts").is_file())

    def test_install_dest_poza_korzeniem(self):
        self.zapisz_kontrakt(KONTRAKT_MINIMALNY)
        wynik = self.uruchom(CONTRACT_TOOL, "install", "--root", str(self.repo),
                             "--dest", "../tools/contract_tool.py")
        self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)
        self.assertFalse((self.repo.parent / "tools").exists())


class TestRozjazd(BazaKontraktu):
    def test_check_pliku_w_cp1250_daje_rozjazd(self):
        """Regresja A2-25: pliku nieczytelnego jako UTF-8 nie da się porównać."""
        self.zapisz_kontrakt(KONTRAKT_MINIMALNY)
        wynik = self.uruchom(CONTRACT_TOOL, "gen", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_OK, wynik.stderr)
        cel = self.repo / "shared" / "contract.go"
        cel.write_bytes("// zażółć gęślą jaźń\n".encode("cp1250"))
        wynik = self.uruchom(CONTRACT_TOOL, "check", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_DRIFT, wynik.stderr)
        self.sprawdz_bez_tracebacku(wynik)

    def test_check_bez_rozjazdu(self):
        self.zapisz_kontrakt(KONTRAKT_MINIMALNY)
        self.uruchom(CONTRACT_TOOL, "gen", "--root", str(self.repo), "--no-gofmt")
        wynik = self.uruchom(CONTRACT_TOOL, "check", "--root", str(self.repo), "--no-gofmt")
        self.assertEqual(wynik.returncode, EXIT_OK, wynik.stderr)


class TestNazwaNaDrucie(unittest.TestCase):
    """Regresja A2-35: akronim w nazwie komunikatu nie może się rozpadać."""

    def setUp(self) -> None:
        sys.path.insert(0, str(CONTRACT_TOOL.parent))
        import contract_tool
        self.narzedzie = contract_tool

    def test_akronim_na_poczatku_nazwy(self):
        self.assertEqual(self.narzedzie.wire_name({"name": "AIPrompt", "channel": "ai"}), "ai.prompt")
        self.assertEqual(self.narzedzie.wire_name({"name": "AiPrompt", "channel": "ai"}), "ai.prompt")

    def test_nazwa_bez_przedrostka_kanalu(self):
        self.assertEqual(self.narzedzie.wire_name({"name": "Ping", "channel": "session"}),
                         "session.ping")

    def test_pole_wire_nadpisuje_regule(self):
        self.assertEqual(self.narzedzie.wire_name({"name": "X", "channel": "y", "wire": "a.b"}), "a.b")

    def test_komunikat_bez_nazwy_nie_przewraca(self):
        self.assertEqual(self.narzedzie.wire_name({"channel": "ai"}), "ai.")


class TestPozostaleNarzedzia(BazaKontraktu):
    """Regresja A2-07: kontrakt niebędący obiektem JSON w każdym narzędziu."""

    def test_kontrakt_lista_albo_zepsuty_json(self):
        przypadki = (
            (MODES_TOOL, ("validate", "--contract", "zly.json", "--root", str(self.repo))),
            (CHANNEL_TOOL, ("gen", "--contract", "zly.json", "--root", str(self.repo))),
            (TAURI_CHECK, ("--contract", "zly.json", "--root", str(self.repo))),
        )
        for tresc in ("[]", "{to nie json"):
            self.zapisz_kontrakt(tresc, "zly.json")
            for skrypt, argumenty in przypadki:
                with self.subTest(skrypt=skrypt.name, tresc=tresc):
                    wynik = self.uruchom(skrypt, *argumenty)
                    self.sprawdz_bez_tracebacku(wynik)
                    self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)

    def test_workflow_tool_zepsuty_kontrakt(self):
        przeplyw = {"nazwa": "x", "wersja": "1.0.0", "role": [], "zadania": [], "bramki": []}
        self.zapisz_kontrakt(przeplyw, "przeplyw.json")
        self.zapisz_kontrakt("{to nie json", "zly.json")
        wynik = self.uruchom(WORKFLOW_TOOL, "validate", "przeplyw.json",
                             "--contract", "zly.json", "--root", str(self.repo))
        self.sprawdz_bez_tracebacku(wynik)
        self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stderr)

    def test_modes_tool_out_poza_korzeniem(self):
        kontrakt = dict(KONTRAKT_MINIMALNY)
        self.zapisz_kontrakt(kontrakt, "zly-out.json")
        wynik = self.uruchom(MODES_TOOL, "report", "--contract", "zly-out.json",
                             "--root", str(self.repo), "--out", "../poza/raport.md")
        self.sprawdz_bez_tracebacku(wynik)
        self.assertIn(wynik.returncode, (EXIT_INVALID,), wynik.stderr)
        self.assertFalse((self.repo.parent / "poza").exists())


class TestTauriCheck(BazaKontraktu):
    def _przygotuj_powloke(self, kod_rust: str, csp: str) -> None:
        tauri = self.repo / "desktop" / "src-tauri"
        (tauri / "src").mkdir(parents=True)
        (tauri / "src" / "main.rs").write_text(kod_rust, encoding="utf-8")
        (tauri / "tauri.conf.json").write_text(json.dumps({
            "app": {"security": {"csp": csp}, "windows": [{"label": "glowne"}]},
        }), encoding="utf-8")
        (tauri / "capabilities").mkdir()
        (tauri / "capabilities" / "domyslne.json").write_text(json.dumps({
            "identifier": "domyslne", "windows": ["glowne"],
            "permissions": ["fs:allow-read-text-file"],
        }), encoding="utf-8")

    def test_unsafe_inline_za_style_src_jest_zglaszane(self):
        """Regresja A2-23: kolejność dyrektyw CSP jest dowolna."""
        self._przygotuj_powloke(
            '#[tauri::command]\nfn ping() {}\nfn main() { tauri::generate_handler![ping]; }\n',
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
        self.zapisz_kontrakt({"commands": [{"name": "ping"}]}, "shared/contract.json")
        wynik = self.uruchom(TAURI_CHECK, "--root", str(self.repo))
        self.assertEqual(wynik.returncode, EXIT_INVALID, wynik.stdout)
        self.assertIn("script-src", wynik.stderr)

    def test_lancuch_rust_nie_zjada_komendy(self):
        """Regresja A2-24: "/*" w łańcuchu ukrywało dalszy kod przed kontrolą."""
        self._przygotuj_powloke(
            'fn zakres() -> &\'static str { "script-src \'self\' /*" }\n'
            '#[tauri::command]\nfn ping() {}\n'
            'fn main() { tauri::generate_handler![ping]; }\n',
            "default-src 'self'; script-src 'self'; connect-src ipc: http://ipc.localhost")
        self.zapisz_kontrakt({"commands": [{"name": "ping"}]}, "shared/contract.json")
        wynik = self.uruchom(TAURI_CHECK, "--root", str(self.repo))
        self.assertEqual(wynik.returncode, EXIT_OK, wynik.stdout + wynik.stderr)

    def test_komenda_bez_nazwy_w_kontrakcie(self):
        self._przygotuj_powloke(
            '#[tauri::command]\nfn ping() {}\nfn main() { tauri::generate_handler![ping]; }\n',
            "default-src 'self'; script-src 'self'; connect-src ipc: http://ipc.localhost")
        self.zapisz_kontrakt({"commands": [{"request": "Brak"}]}, "shared/contract.json")
        wynik = self.uruchom(TAURI_CHECK, "--root", str(self.repo))
        self.sprawdz_bez_tracebacku(wynik)
        self.assertEqual(wynik.returncode, EXIT_INVALID)
        self.assertIn("bez pola name", wynik.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
