#!/usr/bin/env python3
"""Próba konfiguracji Claude Code bez modelu: CLI kierowane do lokalnej atrapy API.

Uruchamia `atrapa_api.py`, tworzy odizolowany katalog konfiguracji (CLAUDE_CONFIG_DIR)
i katalog roboczy, uruchamia CLI w czystym środowisku i streszcza wynik: zdarzenie
`system/init` (tryb uprawnień, narzędzia, serwery MCP, polecenia, skille, agenci,
wtyczki), zdarzenia hooków, wynik tury oraz treść żądań wysłanych do „API”.

Użycie:
  python3 proba_cli.py [opcje] -- <argumenty CLI po `claude -p`>

Przykłady:
  python3 proba_cli.py --nazwa tryb -- --permission-mode dontAsk --settings ustawienia.json
  python3 proba_cli.py --scenariusz bash.json --szukaj "Co-Authored-By" -- --settings u.json --tools Bash

Opcje:
  --cli PATH          binarka CLI (domyślnie $CLAUDE_BIN, potem `claude` z PATH)
  --katalog DIR       katalog próby (domyślnie $TMPDIR/proby-claude/<nazwa>; gdy istnieje — nowy
                      z przyrostkiem czasu, nic nie jest usuwane)
  --nazwa NAZWA       nazwa próby (podkatalog)
  --scenariusz PLIK   kroki atrapy (patrz atrapa_api.py)
  --prompt TEKST      treść wiadomości (domyślnie „próba”)
  --cwd DIR           katalog roboczy CLI (domyślnie <katalog>/cwd)
  --srodowisko K=V    dodatkowa zmienna procesu CLI (wielokrotnie)
  --szukaj TEKST      sprawdź, czy tekst wystąpił w żądaniach do API (wielokrotnie)
  --timeout S         limit czasu (domyślnie 120 s)
  --plik-w-domu R=T   utwórz plik R (względem katalogu domowego próby) z treścią T
  --json              wypisz streszczenie jako JSON

Bezpieczeństwo: CLI dostaje stały napis `atrapa-nie-sekret` zamiast poświadczeń,
`ANTHROPIC_BASE_URL` na 127.0.0.1 i `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`.
Zmienna ta wyłącza pobieranie flag funkcji, więc bez jawnego `--permission-mode`
sesja `-p` startuje w trybie `auto` (≥2.1.285) — podawaj tryb jawnie.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TU = Path(__file__).resolve().parent


def wolny_port() -> int:
    with socket.socket() as gniazdo:
        gniazdo.bind(("127.0.0.1", 0))
        return gniazdo.getsockname()[1]


def znajdz_cli(wskazane: str | None) -> str:
    for kandydat in (wskazane, os.environ.get("CLAUDE_BIN"), shutil.which("claude")):
        if kandydat and Path(kandydat).exists():
            return kandydat
    sys.exit("Nie znaleziono binarki claude: podaj --cli albo ustaw CLAUDE_BIN")


def streszczenie_wyjscia(linie: list[str]) -> dict:
    wynik: dict = {"init": None, "hooki": [], "wynik": None, "teksty": [], "inne_systemowe": []}
    for linia in linie:
        try:
            zdarzenie = json.loads(linia)
        except json.JSONDecodeError:
            continue
        typ, podtyp = zdarzenie.get("type"), zdarzenie.get("subtype")
        if typ == "system" and podtyp == "init":
            wynik["init"] = {k: zdarzenie.get(k) for k in (
                "claude_code_version", "model", "permissionMode", "tools", "mcp_servers", "slash_commands",
                "skills", "agents", "plugins", "plugin_errors", "mcp_server_errors", "output_style")}
        elif typ == "system" and str(podtyp).startswith("hook_"):
            wynik["hooki"].append({k: zdarzenie.get(k) for k in ("subtype", "hook_event", "hook_name", "outcome",
                                                                    "exit_code", "output", "stdout", "stderr")
                                   if zdarzenie.get(k) not in (None, "")})
        elif typ == "system":
            wynik["inne_systemowe"].append(podtyp)
        elif typ == "result":
            wynik["wynik"] = {k: zdarzenie.get(k) for k in ("subtype", "is_error", "num_turns", "result",
                                                             "permission_denials", "stop_reason")}
        elif typ == "assistant":
            for blok in zdarzenie.get("message", {}).get("content", []):
                if blok.get("type") == "text":
                    wynik["teksty"].append(blok.get("text", "")[:200])
                elif blok.get("type") == "tool_use":
                    wynik["teksty"].append(f"[tool_use {blok.get('name')}]")
        elif typ == "user":
            for blok in zdarzenie.get("message", {}).get("content", []) or []:
                if isinstance(blok, dict) and blok.get("type") == "tool_result":
                    tresc = blok.get("content")
                    if isinstance(tresc, list):
                        tresc = " ".join(c.get("text", "") for c in tresc if isinstance(c, dict))
                    wynik["teksty"].append(f"[tool_result{' BŁĄD' if blok.get('is_error') else ''}] {str(tresc)[:200]}")
    return wynik


def streszczenie_zadan(katalog: Path, szukane: list[str]) -> dict:
    glowne, pomocnicze, trafienia = [], 0, {s: False for s in szukane}
    for plik in sorted(katalog.glob("*-POST-v1_messages*.json")):
        surowe = plik.read_text(errors="replace")
        for s in szukane:
            if s in surowe:
                trafienia[s] = True
        try:
            cialo = json.loads(surowe.split("\n", 1)[1] or "{}")
        except (IndexError, json.JSONDecodeError):
            continue
        if not cialo.get("tools"):
            pomocnicze += 1
            continue
        system = cialo.get("system")
        bloki = [len(b.get("text", "")) for b in system] if isinstance(system, list) else [len(system or "")]
        glowne.append({"plik": plik.name, "model": cialo.get("model"),
                       "effort": (cialo.get("output_config") or {}).get("effort"),
                       "system_bloki_znaki": bloki,
                       "narzedzia": [t.get("name") for t in cialo.get("tools", [])],
                       "wiadomosci": len(cialo.get("messages", []))})
    return {"glowne": glowne, "pomocnicze": pomocnicze, "szukane": trafienia}


def main() -> None:
    if "--" in sys.argv:
        podzial = sys.argv.index("--")
        wlasne, cli_args = sys.argv[1:podzial], sys.argv[podzial + 1:]
    else:
        wlasne, cli_args = sys.argv[1:], []
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli")
    parser.add_argument("--katalog", type=Path)
    parser.add_argument("--nazwa", default="proba")
    parser.add_argument("--scenariusz", type=Path)
    parser.add_argument("--prompt", default="próba")
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--srodowisko", action="append", default=[])
    parser.add_argument("--szukaj", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--plik-w-domu", action="append", default=[],
                        help="utwórz plik w katalogu domowym próby: ŚCIEŻKA_WZGLĘDNA=TREŚĆ (wielokrotnie)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--bez-strumienia", action="store_true",
                        help="nie dodawaj --output-format stream-json --verbose")
    a = parser.parse_args(wlasne)

    cli = znajdz_cli(a.cli)
    baza = a.katalog or Path(os.environ.get("TMPDIR", "/tmp")) / "proby-claude" / a.nazwa
    if "/.claude/" in str(baza.resolve()) + "/":
        print("UWAGA: katalog próby leży pod .claude/ — każdy zapis będzie zapisem do ścieżki chronionej "
              "(w dontAsk odmowa). Ustaw TMPDIR albo --katalog poza .claude.", file=sys.stderr)
    if baza.exists():
        # nigdy nie usuwamy istniejącego katalogu (mógłby zawierać dane) — nowa próba dostaje przyrostek
        baza = baza.with_name(f"{baza.name}-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}")
        print(f"Katalog próby istnieje — używam {baza}", file=sys.stderr)
    for podkatalog in ("profil", "dom", "zadania", "tmp"):
        (baza / podkatalog).mkdir(parents=True, exist_ok=True)
    for wpis in a.plik_w_domu:
        sciezka, _, tresc = wpis.partition("=")
        cel = baza / "dom" / sciezka
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_text(tresc)
    cwd = a.cwd or baza / "cwd"
    cwd.mkdir(parents=True, exist_ok=True)

    port = wolny_port()
    atrapa_cmd = [sys.executable, str(TU / "atrapa_api.py"), "--port", str(port), "--zapis", str(baza / "zadania")]
    if a.scenariusz:
        atrapa_cmd += ["--scenariusz", str(a.scenariusz.resolve())]
    atrapa = subprocess.Popen(atrapa_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        # Krótki TMPDIR dla CLI: piaskownica tworzy w nim gniazda uniksowe, a ścieżka gniazda
        # ma limit ok. 107 znaków („Failed to create bridge sockets after 5 attempts”).
        tmp_cli = baza / "tmp"
        if len(str(tmp_cli)) > 60:
            tmp_cli = Path(tempfile.mkdtemp(prefix="cc", dir=os.environ.get("TMPDIR") or None))
        srodowisko = {
            "HOME": str(baza / "dom"), "PATH": "/usr/local/bin:/usr/bin:/bin", "TMPDIR": str(tmp_cli),
            "LANG": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(baza / "profil"),
            "CLAUDE_CODE_OAUTH_TOKEN": "atrapa-nie-sekret", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1",
        }
        for para in a.srodowisko:
            klucz, _, wartosc = para.partition("=")
            srodowisko[klucz] = wartosc
        # Prompt stoi zaraz po -p: flagi wieloargumentowe (--allowed-tools, --disallowed-tools,
        # --mcp-config, --add-dir) połknęłyby prompt podany na końcu jako kolejną wartość.
        polecenie = [cli, "-p"]
        if "--input-format" not in cli_args:
            polecenie.append(a.prompt)
        if not a.bez_strumienia:
            polecenie += ["--output-format", "stream-json", "--verbose"]
        polecenie += cli_args
        start = time.time()
        try:
            proces = subprocess.run(polecenie, cwd=cwd, env=srodowisko, capture_output=True, text=True,
                                    timeout=a.timeout, stdin=subprocess.DEVNULL)
            kod, stdout, stderr = proces.returncode, proces.stdout, proces.stderr
        except subprocess.TimeoutExpired as wyjatek:
            kod, stdout, stderr = "timeout", wyjatek.stdout or "", wyjatek.stderr or ""
            stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
            stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
        (baza / "wyjscie.jsonl").write_text(stdout)
        (baza / "stderr.txt").write_text(stderr)
        (baza / "polecenie.json").write_text(json.dumps(polecenie, ensure_ascii=False, indent=1))
    finally:
        atrapa.terminate()
        atrapa.wait(timeout=5)

    raport = {"katalog": str(baza), "kod_wyjscia": kod, "czas_s": round(time.time() - start, 1),
              "stderr": stderr.strip()[:800], **streszczenie_wyjscia(stdout.splitlines()),
              "zadania": streszczenie_zadan(baza / "zadania", a.szukaj)}
    if a.json:
        print(json.dumps(raport, ensure_ascii=False, indent=1))
        return
    init = raport["init"] or {}
    print(f"Próba: {baza}\nKod wyjścia: {kod}  czas: {raport['czas_s']} s")
    if raport["stderr"]:
        print(f"stderr: {raport['stderr']}")
    if init:
        print(f"CLI {init.get('claude_code_version')}  model {init.get('model')}  tryb {init.get('permissionMode')}")
        print(f"narzędzia ({len(init.get('tools') or [])}): {', '.join(init.get('tools') or [])}")
        print("MCP: " + ", ".join(f"{s.get('name')}={s.get('status')}" for s in init.get("mcp_servers") or []))
        print(f"polecenia: {len(init.get('slash_commands') or [])}  skille: {len(init.get('skills') or [])}  "
              f"agenci: {', '.join(init.get('agents') or [])}")
        print("wtyczki: " + ", ".join(p.get("name", "?") for p in init.get("plugins") or []))
        if init.get("plugin_errors"):
            print(f"błędy wtyczek: {init['plugin_errors']}")
    for hook in raport["hooki"]:
        print(f"hook: {hook}")
    for tekst in raport["teksty"]:
        print(f"  {tekst}")
    if raport["wynik"]:
        print(f"wynik: {raport['wynik']}")
    zadania = raport["zadania"]
    print(f"żądania główne: {len(zadania['glowne'])}, pomocnicze: {zadania['pomocnicze']}")
    for z in zadania["glowne"][:3]:
        print(f"  {z['plik']}: model={z['model']} effort={z['effort']} system={z['system_bloki_znaki']} "
              f"narzędzia={len(z['narzedzia'])}")
    for tekst, jest in zadania["szukane"].items():
        print(f"szukane „{tekst}”: {'JEST' if jest else 'brak'}")


if __name__ == "__main__":
    main()
