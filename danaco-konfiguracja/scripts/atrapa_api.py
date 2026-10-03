#!/usr/bin/env python3
"""Lokalna atrapa Messages API do prób Claude Code bez modelu i bez konta.

Zapisuje każde żądanie CLI do katalogu (nagłówki uwierzytelnienia zamaskowane)
i odpowiada według scenariusza. Nie łączy się z niczym na zewnątrz.

Użycie:
  python3 atrapa_api.py --port 18500 --zapis KATALOG [--scenariusz PLIK.json]

Scenariusz to lista kroków JSON, zużywanych przez kolejne żądania głównej pętli
(żądania z niepustą listą `tools`):
  [{"narzedzie": "Bash", "wejscie": {"command": "echo ok"}},
   {"tekst": "Gotowe."}]
Krok `narzedzie` zwraca blok `tool_use`; krok `tekst` zwraca zwykłą odpowiedź.
Opcjonalne pole kroku `opoznienie_s` wstrzymuje odpowiedź (próby przerwania tury).
Po wyczerpaniu scenariusza oraz dla żądań pomocniczych (bez narzędzi) atrapa
odpowiada tekstem `ATRAPA-OK`.

Do CLI podłącza się ją zmiennymi procesu:
  ANTHROPIC_BASE_URL=http://127.0.0.1:<port>
  CLAUDE_CODE_OAUTH_TOKEN=atrapa-nie-sekret   (stały napis, nie poświadczenie)
"""
from __future__ import annotations

import argparse
import itertools
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MASKOWANE = {"authorization", "x-api-key", "cookie"}


def zbuduj_handler(katalog: Path, kroki: list[dict]):
    licznik = itertools.count(1)
    blokada = threading.Lock()
    pozostale = list(kroki)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *argumenty):  # cisza w terminalu
            pass

        def _zapisz(self, tresc: bytes) -> None:
            numer = next(licznik)
            naglowki = {k: ("***" if k.lower() in MASKOWANE else v) for k, v in self.headers.items()}
            nazwa = self.path.split("?")[0].strip("/").replace("/", "_") or "root"
            plik = katalog / f"{numer:03d}-{self.command}-{nazwa}.json"
            plik.write_bytes(json.dumps({"path": self.path, "headers": naglowki}, ensure_ascii=False).encode()
                             + b"\n" + tresc)

        def _json(self, kod: int, dane: dict) -> None:
            surowe = json.dumps(dane).encode()
            self.send_response(kod)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(surowe)))
            self.end_headers()
            self.wfile.write(surowe)

        def do_GET(self):  # noqa: N802 — nazwa wymagana przez http.server
            self._zapisz(b"")
            self._json(404, {"type": "error", "error": {"type": "not_found_error", "message": "atrapa"}})

        def do_POST(self):  # noqa: N802
            tresc = self.rfile.read(int(self.headers.get("content-length", 0) or 0))
            self._zapisz(tresc)
            if not self.path.startswith("/v1/messages") or "count_tokens" in self.path:
                self._json(404, {"type": "error", "error": {"type": "not_found_error", "message": "atrapa"}})
                return
            zadanie = json.loads(tresc or b"{}")
            krok = None
            if zadanie.get("tools"):
                with blokada:
                    if pozostale:
                        krok = pozostale.pop(0)
            if krok and krok.get("opoznienie_s"):
                import time
                time.sleep(float(krok["opoznienie_s"]))
            if krok and "narzedzie" in krok:
                blok = {"type": "tool_use", "id": f"toolu_atrapa_{next(licznik):04d}",
                        "name": krok["narzedzie"], "input": krok.get("wejscie", {})}
                powod = "tool_use"
            else:
                blok = {"type": "text", "text": (krok or {}).get("tekst", "ATRAPA-OK")}
                powod = "end_turn"
            wiadomosc = {"id": "msg_atrapa", "type": "message", "role": "assistant",
                         "model": zadanie.get("model", "atrapa"), "content": [], "stop_reason": None,
                         "stop_sequence": None,
                         "usage": {"input_tokens": 1, "output_tokens": 1,
                                   "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}
            if not zadanie.get("stream"):
                wiadomosc["content"] = [blok]
                wiadomosc["stop_reason"] = powod
                self._json(200, wiadomosc)
                return
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()

            def zdarzenie(typ: str, dane: dict) -> None:
                self.wfile.write(f"event: {typ}\ndata: {json.dumps(dane)}\n\n".encode())

            zdarzenie("message_start", {"type": "message_start", "message": wiadomosc})
            if blok["type"] == "text":
                zdarzenie("content_block_start", {"type": "content_block_start", "index": 0,
                                                  "content_block": {"type": "text", "text": ""}})
                zdarzenie("content_block_delta", {"type": "content_block_delta", "index": 0,
                                                  "delta": {"type": "text_delta", "text": blok["text"]}})
            else:
                zdarzenie("content_block_start", {"type": "content_block_start", "index": 0,
                                                  "content_block": {"type": "tool_use", "id": blok["id"],
                                                                    "name": blok["name"], "input": {}}})
                zdarzenie("content_block_delta", {"type": "content_block_delta", "index": 0,
                                                  "delta": {"type": "input_json_delta",
                                                            "partial_json": json.dumps(blok["input"])}})
            zdarzenie("content_block_stop", {"type": "content_block_stop", "index": 0})
            zdarzenie("message_delta", {"type": "message_delta",
                                        "delta": {"stop_reason": powod, "stop_sequence": None},
                                        "usage": {"output_tokens": 1}})
            zdarzenie("message_stop", {"type": "message_stop"})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--zapis", type=Path, required=True, help="katalog na zapis żądań")
    parser.add_argument("--scenariusz", type=Path, help="plik JSON z listą kroków")
    argumenty = parser.parse_args()
    argumenty.zapis.mkdir(parents=True, exist_ok=True)
    kroki = json.loads(argumenty.scenariusz.read_text()) if argumenty.scenariusz else []
    serwer = ThreadingHTTPServer(("127.0.0.1", argumenty.port), zbuduj_handler(argumenty.zapis, kroki))
    serwer.serve_forever()


if __name__ == "__main__":
    main()
