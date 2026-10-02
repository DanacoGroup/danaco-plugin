#!/usr/bin/env python3
"""Atrapa Messages API do prób danaco-praca na żywo (bez modelu, bez konta, bez sieci).

Każde żądanie głównej pętli (z niepustą listą `tools`) zużywa kolejny krok scenariusza:
  {"narzedzie": "Bash", "wejscie": {"command": "sleep 30"}}  -> blok tool_use
  {"tekst": "Gotowe."}                                      -> odpowiedź tekstowa (end_turn)
Po wyczerpaniu scenariusza i dla żądań pomocniczych atrapa odpowiada tekstem `ATRAPA-KONIEC`.
Treść każdego żądania trafia do katalogu zapisu (nagłówki uwierzytelnienia zamaskowane).

Użycie: atrapa_api.py PORT KATALOG_ZAPISU SCENARIUSZ.json
"""
from __future__ import annotations

import itertools
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

port, katalog, scenariusz = int(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
katalog.mkdir(parents=True, exist_ok=True)
kroki = json.loads(scenariusz.read_text())
licznik = itertools.count(1)
blokada = threading.Lock()


class Obsluga(BaseHTTPRequestHandler):
    def log_message(self, *argumenty):
        pass

    def _json(self, kod, dane):
        surowe = json.dumps(dane).encode()
        self.send_response(kod)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(surowe)))
        self.end_headers()
        self.wfile.write(surowe)

    def do_GET(self):  # noqa: N802
        self._json(404, {"type": "error", "error": {"type": "not_found_error", "message": "atrapa"}})

    def do_POST(self):  # noqa: N802
        tresc = self.rfile.read(int(self.headers.get("content-length", 0) or 0))
        numer = next(licznik)
        (katalog / f"{numer:03d}.json").write_bytes(tresc)
        if not self.path.startswith("/v1/messages") or "count_tokens" in self.path:
            self._json(404, {"type": "error", "error": {"type": "not_found_error", "message": "atrapa"}})
            return
        zadanie = json.loads(tresc or b"{}")
        krok = None
        if zadanie.get("tools"):
            with blokada:
                if kroki:
                    krok = kroki.pop(0)
        if krok and "narzedzie" in krok:
            blok = {"type": "tool_use", "id": f"toolu_atrapa_{numer:04d}", "name": krok["narzedzie"],
                    "input": krok.get("wejscie", {})}
            powod = "tool_use"
        else:
            blok = {"type": "text", "text": (krok or {}).get("tekst", "ATRAPA-KONIEC")}
            powod = "end_turn"
        wiadomosc = {"id": f"msg_atrapa_{numer}", "type": "message", "role": "assistant",
                     "model": zadanie.get("model", "atrapa"), "content": [], "stop_reason": None,
                     "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}
        if not zadanie.get("stream"):
            wiadomosc["content"], wiadomosc["stop_reason"] = [blok], powod
            self._json(200, wiadomosc)
            return
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()

        def zdarzenie(typ, dane):
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
        zdarzenie("message_delta", {"type": "message_delta", "delta": {"stop_reason": powod, "stop_sequence": None},
                                    "usage": {"output_tokens": 1}})
        zdarzenie("message_stop", {"type": "message_stop"})


ThreadingHTTPServer(("127.0.0.1", port), Obsluga).serve_forever()
