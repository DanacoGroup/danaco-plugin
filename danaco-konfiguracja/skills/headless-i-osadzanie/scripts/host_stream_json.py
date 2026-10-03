#!/usr/bin/env python3
"""Wzorcowy host produktu: steruje `claude -p` przez stream-json (wejście i wyjście).

Pokazuje wzorce osadzania CLI w usłudze:
  - wejście `--input-format stream-json`: wiadomości `{"type":"user","message":{…}}` na stdin,
  - odczyt `system/init` (bramka: serwery MCP connected, brak plugin_errors),
  - `system/api_retry` (stan „ponawiam”), wynik `result` z `usage` i polami cache,
  - przerwanie tury żądaniem sterującym `interrupt` (zamiast SIGTERM, który gubi turę),
  - osobny CLAUDE_CONFIG_DIR i CLAUDE_CODE_PROJECT_DIR_NAME na dzierżawcę.

Użycie (próba na atrapie: ANTHROPIC_BASE_URL i token atrapy w środowisku):
  host_stream_json.py --cli claude --konfiguracja DIR --dzierzawca k123 --cwd DIR
                      --prompt "…" [--przerwij-po 1.5] [-- dodatkowe flagi CLI]
Kod wyjścia: 0 sukces, 2 bramka init nie przeszła, 3 przerwano, 1 inny błąd.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid


def main() -> int:
    if "--" in sys.argv:
        i = sys.argv.index("--")
        wlasne, dodatkowe = sys.argv[1:i], sys.argv[i + 1:]
    else:
        wlasne, dodatkowe = sys.argv[1:], []
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cli", default="claude")
    p.add_argument("--konfiguracja", required=True, help="CLAUDE_CONFIG_DIR dzierżawcy")
    p.add_argument("--dzierzawca", required=True, help="CLAUDE_CODE_PROJECT_DIR_NAME (1–64 znaki [A-Za-z0-9_-])")
    p.add_argument("--cwd", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--sesja", default=str(uuid.uuid4()))
    p.add_argument("--wznow", action="store_true", help="--resume zamiast --session-id")
    p.add_argument("--przerwij-po", type=float, default=0.0, help="wyślij interrupt po N sekundach")
    p.add_argument("--wymagane-mcp", action="append", default=[])
    a = p.parse_args(wlasne)

    srodowisko = dict(os.environ, CLAUDE_CONFIG_DIR=a.konfiguracja, CLAUDE_CODE_PROJECT_DIR_NAME=a.dzierzawca,
                      CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", DISABLE_AUTOUPDATER="1")
    polecenie = [a.cli, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                 "--replay-user-messages", "--permission-prompts", "none",
                 ("--resume" if a.wznow else "--session-id"), a.sesja] + dodatkowe
    proces = subprocess.Popen(polecenie, cwd=a.cwd, env=srodowisko, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, bufsize=1)

    def wyslij(obiekt: dict) -> None:
        proces.stdin.write(json.dumps(obiekt, ensure_ascii=False) + "\n")
        proces.stdin.flush()

    wyslij({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": a.prompt}]}})
    przerwano = False
    if a.przerwij_po:
        def przerwij() -> None:
            nonlocal przerwano
            time.sleep(a.przerwij_po)
            if proces.poll() is None:
                przerwano = True
                wyslij({"type": "control_request", "request_id": f"przerwij-{uuid.uuid4().hex[:8]}",
                        "request": {"subtype": "interrupt"}})
        threading.Thread(target=przerwij, daemon=True).start()

    kod = 1
    for linia in proces.stdout:
        try:
            z = json.loads(linia)
        except json.JSONDecodeError:
            continue
        typ, podtyp = z.get("type"), z.get("subtype")
        if typ == "system" and podtyp == "init":
            serwery = {s["name"]: s["status"] for s in z.get("mcp_servers", [])}
            brakujace = [n for n in a.wymagane_mcp if serwery.get(n) != "connected"]
            print(f"init: tryb={z.get('permissionMode')} model={z.get('model')} mcp={serwery} "
                  f"możliwości={z.get('capabilities')}")
            if brakujace or z.get("plugin_errors") or z.get("mcp_server_errors"):
                print(f"BRAMKA: brak serwerów {brakujace} lub błędy wtyczek/MCP — przerywam przebieg")
                proces.kill()
                return 2
        elif typ == "system" and podtyp == "api_retry":
            print(f"ponawiam: próba {z.get('attempt')}/{z.get('max_retries')} za {z.get('retry_delay_ms')} ms ({z.get('error')})")
        elif typ == "control_response":
            print(f"odpowiedź sterująca: {json.dumps(z.get('response'), ensure_ascii=False)[:200]}")
        elif typ == "result":
            u = z.get("usage") or {}
            print(f"wynik: {podtyp} is_error={z.get('is_error')} tury={z.get('num_turns')} "
                  f"koszt_usd={z.get('total_cost_usd')} cache_odczyt={u.get('cache_read_input_tokens')} "
                  f"cache_zapis={u.get('cache_creation_input_tokens')}")
            kod = 3 if przerwano else (0 if not z.get("is_error") else 1)
            proces.stdin.close()  # koniec wejścia = koniec sesji po turze
    proces.wait(timeout=30)
    bledy = proces.stderr.read().strip()
    if bledy:
        print(f"stderr: {bledy[:300]}")
    print(f"sesja: {a.sesja} (wznowienie: --wznow --sesja {a.sesja}); kod procesu {proces.returncode}")
    return kod


if __name__ == "__main__":
    sys.exit(main())
