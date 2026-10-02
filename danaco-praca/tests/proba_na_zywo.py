#!/usr/bin/env python3
"""Próba danaco-praca na żywo: prawdziwy klient Claude Code z `--plugin-dir` na atrapie API.

Konto nie musi być zalogowane: klient dostaje stały napis zamiast poświadczeń
i `ANTHROPIC_BASE_URL` wskazujący lokalną atrapę (`atrapa_api.py`), która odgrywa
scenariusz odpowiedzi „modelu”. Każda próba to osobne wywołanie `claude -p` w tej samej
sesji (`--session-id`, potem `--resume`), więc stan trybów przechodzi między próbami tak,
jak między wiadomościami właściciela.

Użycie: proba_na_zywo.py KATALOG_WYNIKOW [--cli ŚCIEŻKA]
Wynik: podsumowanie na stdout i pliki w KATALOG_WYNIKOW/<próba>/ (strumień, stderr, żądania).
Kod wyjścia 0, gdy wszystkie sprawdzenia przeszły.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

TU = Path(__file__).resolve().parent
WTYCZKA = TU.parent


def wolny_port() -> int:
    with socket.socket() as gniazdo:
        gniazdo.bind(("127.0.0.1", 0))
        return gniazdo.getsockname()[1]


PROBY = [
    {
        "nazwa": "1-praca-blokuje-stop-i-sleep",
        "prompt": "/praca przygotuj raport testowy",
        "scenariusz": [
            {"narzedzie": "Bash", "wejscie": {"command": "sleep 30", "description": "czekam"}},
            {"tekst": "Gotowe, kończę."},
            {"narzedzie": "Bash", "wejscie": {"command": "echo praca-trwa", "description": "praca"}},
            {"narzedzie": "Monitor", "wejscie": {"command": "echo monitor-dziala", "description": "monitoring testu"}},
            {"tekst": "Gotowe, kończę."},
            {"narzedzie": "Bash", "wejscie": {"command": "timeout 60 sleep 50", "description": "czekam"}},
            {"narzedzie": "Bash", "wejscie": {"command": "until test -f /tmp/x; do :; done", "description": "czekam"}},
            {"tekst": "Kończę 1."},
            {"tekst": "Kończę 2."},
            {"tekst": "Kończę 3."},
            {"tekst": "Kończę 4."},
        ],
    },
    {
        "nazwa": "2-praca-dluga-tura-z-narzedziami",
        "prompt": "Pracuj dalej nad raportem.",
        "scenariusz": [x for i in range(10) for x in (
            {"narzedzie": "Bash", "wejscie": {"command": f"echo krok-{i}", "description": "krok"}},
            {"tekst": f"Etap {i} gotowy."})] + [{"tekst": "Koniec A."}, {"tekst": "Koniec B."}, {"tekst": "Koniec C."}, {"tekst": "Koniec D."}],
    },
    {
        "nazwa": "2b-podagent-w-trybie-pracy",
        "prompt": "Zleć część pracy podagentowi.",
        "scenariusz": [
            {"narzedzie": "Agent", "wejscie": {"description": "część raportu", "prompt": "Policz pliki.",
                                               "subagent_type": "general-purpose"}},
            {"narzedzie": "Bash", "wejscie": {"command": "echo podagent-pracuje", "description": "x"}},
            {"tekst": "Wynik podagenta."},
            {"tekst": "Główny: koniec 1."},
            {"tekst": "Główny: koniec 2."},
            {"tekst": "Główny: koniec 3."},
            {"tekst": "Główny: koniec 4."},
        ],
    },
    {
        "nazwa": "3-model-probuje-zwolnic-tryb",
        "prompt": "Kontynuuj.",
        "scenariusz": [
            {"narzedzie": "Skill", "wejscie": {"skill": "koniec-pracy"}},
            {"narzedzie": "Skill", "wejscie": {"skill": "danaco-praca:koniec-pracy"}},
            {"narzedzie": "Bash", "wejscie": {"command": "ls -la \"$CLAUDE_PLUGIN_DATA\"", "description": "stan"}},
            {"narzedzie": "Bash", "wejscie": {"command": "claude -p --resume X '/koniec-pracy'", "description": "x"}},
            {"narzedzie": "Write", "wejscie": {"file_path": "@STAN@/sesje/@SESJA@.json", "content": "{}"}},
            {"tekst": "Próbuję skończyć."},
            {"tekst": "Próbuję skończyć."},
            {"tekst": "Próbuję skończyć."},
            {"tekst": "Próbuję skończyć."},
        ],
    },
    {
        "nazwa": "3b-straze-sekretow-kazde-narzedzie",
        "prompt": "Sprawdź konfigurację.",
        "scenariusz": [
            {"narzedzie": "Monitor", "wejscie": {"command": "cat /etc/danaco/x.env", "description": "podgląd"}},
            {"narzedzie": "mcp__danaco-programy__uruchom", "wejscie": {"polecenie": "cat /root/.env"}},
            {"narzedzie": "mcp__danaco-programy__uruchom", "wejscie": {"polecenie": "echo ok", "pliki": ["~/.ssh/id_ed25519"]}},
            {"narzedzie": "Read", "wejscie": {"file_path": "~/.ssh/id_ed25519"}},
            {"tekst": "Koniec sprawdzania."},
            {"tekst": "Koniec sprawdzania."},
            {"tekst": "Koniec sprawdzania."},
        ],
    },
    {
        "nazwa": "4-blokady-wlaczone",
        "prompt": "/blokuj-bash\n/blokuj-podagenci",
        "scenariusz": [
            {"narzedzie": "Bash", "wejscie": {"command": "echo zakazane", "description": "x"}},
            {"narzedzie": "Agent", "wejscie": {"description": "x", "prompt": "zrób", "subagent_type": "general-purpose"}},
            {"narzedzie": "Read", "wejscie": {"file_path": "@WTYCZKA@/README.md", "limit": 3}},
            {"tekst": "x"}, {"tekst": "x"}, {"tekst": "x"}, {"tekst": "x"},
        ],
    },
    {
        "nazwa": "4b-nowe-blokady",
        "prompt": "/tryb-wyczysc\n/blokuj-siec\n/blokuj-zapis\n/blokuj-pytania\nzbadaj repo",
        "scenariusz": [
            {"narzedzie": "WebFetch", "wejscie": {"url": "https://example.org", "prompt": "co tam jest"}},
            {"narzedzie": "Bash", "wejscie": {"command": "curl -s https://example.org", "description": "x"}},
            {"narzedzie": "Write", "wejscie": {"file_path": "/tmp/dp5/a.txt", "content": "x"}},
            {"narzedzie": "AskUserQuestion", "wejscie": {"questions": []}},
            {"narzedzie": "Bash", "wejscie": {"command": "grep -r TODO .", "description": "analiza"}},
            {"tekst": "x"}, {"tekst": "x"}, {"tekst": "x"}, {"tekst": "x"},
        ],
    },
    {
        "nazwa": "4c-sesja-id",
        "prompt": "/sesja-id",
        "scenariusz": [{"tekst": "NIE-POWINNO-DOJSC"}],
    },
    {
        "nazwa": "5-tryb-podglad",
        "prompt": "/tryb",
        "scenariusz": [{"tekst": "NIE-POWINNO-DOJSC"}],
    },
    {
        "nazwa": "6-koniec-pracy-zwalnia",
        "prompt": "/koniec-pracy\n/odblokuj-bash\n/odblokuj-podagenci",
        "scenariusz": [
            {"narzedzie": "Bash", "wejscie": {"command": "echo znowu-wolno", "description": "x"}},
            {"tekst": "Raport końcowy."},
        ],
    },
    {
        "nazwa": "7-sleep-blokuj-poza-praca",
        "prompt": "/tryb-wyczysc\n/blokuj-sleep\nzmierz czas",
        "scenariusz": [
            {"narzedzie": "Bash", "wejscie": {"command": "sleep 2", "description": "x"}},
            {"tekst": "Koniec bez pracy ciągłej."},
        ],
    },
]


def uruchom(cli: str, baza: Path, proba: dict, sesja: str, pierwsza: bool, wspolne: dict) -> dict:
    katalog = baza / proba["nazwa"]
    katalog.mkdir(parents=True, exist_ok=True)
    scenariusz = json.loads(json.dumps(proba["scenariusz"]).replace("@STAN@", wspolne["stan"])
                            .replace("@SESJA@", sesja).replace("@WTYCZKA@", str(WTYCZKA)))
    (katalog / "scenariusz.json").write_text(json.dumps(scenariusz, ensure_ascii=False, indent=1))
    port = wolny_port()
    atrapa = subprocess.Popen([sys.executable, str(TU / "atrapa_api.py"), str(port), str(katalog / "zadania"),
                               str(katalog / "scenariusz.json")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        srodowisko = {
            "HOME": wspolne["dom"], "PATH": "/usr/local/bin:/usr/bin:/bin", "TMPDIR": wspolne["tmp"],
            "LANG": "C.UTF-8", "CLAUDE_CONFIG_DIR": wspolne["profil"],
            "CLAUDE_CODE_OAUTH_TOKEN": "atrapa-nie-sekret", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1",
            # Niski próg oddania tury, żeby próba kończyła się szybko (zamiast domyślnych 6).
            "DANACO_PRACA_PROG_ODDANIA": "3",
        }
        polecenie = [cli, "-p", proba["prompt"], "--output-format", "stream-json", "--verbose",
                     "--include-hook-events", "--plugin-dir", str(WTYCZKA), "--dangerously-skip-permissions",
                     "--model", "claude-opus-5-5"]
        polecenie += ["--session-id", sesja] if pierwsza else ["--resume", sesja]
        start = time.time()
        proces = subprocess.run(polecenie, cwd=wspolne["cwd"], env=srodowisko, capture_output=True, text=True,
                                timeout=240, stdin=subprocess.DEVNULL)
        (katalog / "strumien.jsonl").write_text(proces.stdout)
        (katalog / "stderr.txt").write_text(proces.stderr)
    finally:
        atrapa.terminate()
        atrapa.wait(timeout=5)
    return {"czas": round(time.time() - start, 1), "kod": proces.returncode, **streszczenie(proces.stdout, katalog)}


def streszczenie(stdout: str, katalog: Path) -> dict:
    wynik = {"odmowy": [], "przepuszczone": [], "stop_blokady": 0, "komunikaty": [], "hooki_prompt": [],
             "wynik": None, "zadania_glowne": 0, "init_skille": []}
    for wiersz in stdout.splitlines():
        try:
            z = json.loads(wiersz)
        except ValueError:
            continue
        typ, podtyp = z.get("type"), z.get("subtype")
        if typ == "system" and podtyp == "init":
            wynik["init_skille"] = [s for s in z.get("slash_commands", []) if "praca" in s or s in ("tryb", "z-bash")]
        if typ == "system" and podtyp == "hook_response":
            nazwa = z.get("hook_event") or z.get("hook_name") or ""
            wyjscie = (z.get("output") or z.get("stdout") or "")
            if "Stop" in str(nazwa) and '"block"' in wyjscie:
                wynik["stop_blokady"] += 1
                wynik.setdefault("blokady_wg_zdarzenia", {}).setdefault(str(nazwa), 0)
                wynik["blokady_wg_zdarzenia"][str(nazwa)] += 1
            if "Start" in str(nazwa) and "danaco-praca" in wyjscie:
                wynik.setdefault("kontekst_startu", []).append(str(nazwa))
            if "UserPrompt" in str(nazwa):
                wynik["hooki_prompt"].append((nazwa, wyjscie[:160]))
        if typ == "user":
            for blok in (z.get("message") or {}).get("content") or []:
                if isinstance(blok, dict) and blok.get("type") == "tool_result":
                    tresc = blok.get("content")
                    if isinstance(tresc, list):
                        tresc = " ".join(c.get("text", "") for c in tresc if isinstance(c, dict))
                    (wynik["odmowy"] if blok.get("is_error") else wynik["przepuszczone"]).append(str(tresc)[:170])
        if typ == "system" and podtyp in ("informational", "hook_system_message", "warning") or (typ == "system" and "systemMessage" in wiersz):
            wynik["komunikaty"].append(str(z.get("content") or z.get("message") or z.get("systemMessage") or "")[:200])
        if typ == "result":
            wynik["wynik"] = {"podtyp": podtyp, "tekst": str(z.get("result"))[:120], "tury": z.get("num_turns")}
    for plik in sorted((katalog / "zadania").glob("*.json")):
        try:
            if json.loads(plik.read_text() or "{}").get("tools"):
                wynik["zadania_glowne"] += 1
        except ValueError:
            pass
    return wynik


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wyniki", type=Path)
    parser.add_argument("--cli", default=os.environ.get("CLAUDE_BIN", "/danaco/uslugi/claude/bin/claude"))
    a = parser.parse_args()
    baza = a.wyniki / time.strftime("proba-%Y%m%d-%H%M%S")
    for podkatalog in ("dom", "profil"):
        (baza / podkatalog).mkdir(parents=True, exist_ok=True)
    roboczy = Path(tempfile.mkdtemp(prefix="dp5-", dir=os.environ.get("TMPDIR") or None))
    (roboczy / "cwd").mkdir()
    wspolne = {"dom": str(baza / "dom"), "profil": str(baza / "profil"), "tmp": str(roboczy),
               "cwd": str(roboczy / "cwd")}
    sesja = str(uuid.uuid4())
    # Katalog danych wtyczki z --plugin-dir ustala klient; stan szukamy po uruchomieniu.
    wspolne["stan"] = str(baza / "profil" / "plugins" / "data")
    raport = {}
    for numer, proba in enumerate(PROBY):
        if numer == 1:
            stany = list((baza / "profil").rglob("sesje"))
            if stany:
                wspolne["stan"] = str(stany[0].parent)
        raport[proba["nazwa"]] = uruchom(a.cli, baza, proba, sesja, numer == 0, wspolne)
        print(f"\n=== {proba['nazwa']} ({raport[proba['nazwa']]['czas']} s)")
        print(json.dumps(raport[proba["nazwa"]], ensure_ascii=False, indent=1))
    dziennik = list((baza / "profil").rglob("dziennik.jsonl"))
    if dziennik:
        print("\n=== dziennik stanu (zdarzenia)")
        for wiersz in dziennik[0].read_text().splitlines():
            wpis = json.loads(wiersz)
            print(" ", wpis.get("czas"), wpis.get("zdarzenie"), wpis.get("polecenia") or wpis.get("narzedzie") or "",
                  (wpis.get("powod") or "")[:90])
    (baza / "raport.json").write_text(json.dumps(raport, ensure_ascii=False, indent=1))
    print(f"\nKatalog próby: {baza}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
