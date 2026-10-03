#!/usr/bin/env python3
"""Wzorcowy serwer MCP (stdio, biblioteka standardowa) pokazujący praktyki dla Claude Code.

Co pokazuje:
  - `instructions` w odpowiedzi `initialize` (z tool search ładują się na starcie zamiast
    definicji narzędzi; domyślny limit 2048 znaków, CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH),
  - mało narzędzi o szerokim działaniu z parametrem `akcja` zamiast wielu podobnych,
  - przestrzeń nazw w nazwach narzędzi (`polityka_…`), szczegółowe opisy (3–4 zdania),
  - `_meta["anthropic/alwaysLoad"]` dla narzędzia rdzenia (bez kroku ToolSearch),
  - `_meta["anthropic/maxResultSizeChars"]` dla narzędzia zwracającego długi tekst,
  - narzędzie zgody dla `--permission-prompt-tool` (odpowiedź jak SDK `PermissionResult`),
  - zasób (`resources/list`, `resources/read`) i deklarację `listChanged`.

Zmienna WZOR_INSTRUKCJE podmienia instrukcje serwera (do prób limitu długości).

Uruchomienie przez Claude Code (plik --mcp-config albo .mcp.json):
  {"mcpServers": {"wzor": {"type": "stdio", "command": "python3",
                           "args": ["<ścieżka>/serwer_wzorcowy.py"],
                           "env": {"WZOR_DZIENNIK": "/tmp/wzor.log"}}}}

Polityka zgody (narzędzie `polityka_zgoda`): pozwala na polecenia Bash, których pierwszy
wyraz jest na liście WZOR_DOZWOLONE (po przecinku, domyślnie „touch,mkdir,ls”), i które
nie są złożone (`;`, `&&`, `|`, `$(`), resztę odrzuca z powodem.
Każde wywołanie zapisuje do pliku WZOR_DZIENNIK (jeśli ustawiony), co pozwala sprawdzić,
jakie wejście CLI przekazuje narzędziu zgody.
"""
from __future__ import annotations

import json
import os
import sys

WERSJE = ["2026-07-28", "2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]
INSTRUKCJE = (
    "Serwer „wzor” udostępnia politykę pracy projektu. Szukaj jego narzędzi, gdy zadanie "
    "dotyczy zasad projektu, dozwolonych poleceń albo raportu zgodności. Narzędzie "
    "polityka_opis zwraca zasady (akcja: krotko|pelny); polityka_raport tworzy długi raport. "
    "Narzędzie polityka_zgoda służy wyłącznie hostowi uprawnień — nie wywołuj go samodzielnie."
)
NARZEDZIA = [
    {
        "name": "polityka_opis",
        "description": (
            "Zwraca zasady pracy w projekcie. Używaj przed pierwszą zmianą w repozytorium "
            "i gdy nie wiesz, czy działanie jest dozwolone. Parametr akcja=krotko daje listę "
            "zasad w punktach, akcja=pelny — pełny tekst z uzasadnieniami. Nie zmienia stanu."
        ),
        "inputSchema": {"type": "object", "properties": {
            "akcja": {"type": "string", "enum": ["krotko", "pelny"], "description": "zakres opisu"}},
            "required": ["akcja"]},
        "annotations": {"readOnlyHint": True},
        "_meta": {"anthropic/alwaysLoad": True},
    },
    {
        "name": "polityka_raport",
        "description": (
            "Tworzy długi raport zgodności projektu z polityką (kilkadziesiąt tysięcy znaków). "
            "Używaj na wyraźne polecenie audytu. Wynik jest tekstem gotowym do zapisania. "
            "Narzędzie nie wykonuje zmian w plikach."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True},
        "_meta": {"anthropic/maxResultSizeChars": 200000},
    },
    {
        "name": "polityka_zgoda",
        "description": (
            "Narzędzie hosta uprawnień (--permission-prompt-tool). Przyjmuje nazwę narzędzia "
            "i jego wejście, zwraca decyzję allow albo deny w formacie PermissionResult. "
            "Model nie powinien go wywoływać."
        ),
        "inputSchema": {"type": "object", "properties": {
            "tool_name": {"type": "string"}, "input": {"type": "object"}, "tool_use_id": {"type": "string"}},
            "required": ["tool_name", "input"]},
    },
]
ZASOBY = [{"uri": "wzor://polityka/zasady", "name": "zasady", "mimeType": "text/markdown",
           "description": "Zasady pracy w projekcie"}]
ZASADY = "# Zasady\n1. Zmiany tylko w katalogu roboczym.\n2. Bez publikacji i push.\n3. Testy przed commitem.\n"


def dziennik(wpis: dict) -> None:
    sciezka = os.environ.get("WZOR_DZIENNIK")
    if sciezka:
        with open(sciezka, "a", encoding="utf-8") as plik:
            plik.write(json.dumps(wpis, ensure_ascii=False) + "\n")


def decyzja(argumenty: dict) -> dict:
    narzedzie = argumenty.get("tool_name", "")
    wejscie = argumenty.get("input") or {}
    dozwolone = {p.strip() for p in os.environ.get("WZOR_DOZWOLONE", "touch,mkdir,ls").split(",") if p.strip()}
    polecenie = str(wejscie.get("command", ""))
    zlozone = any(z in polecenie for z in (";", "&&", "||", "|", "$(", "`", "\n"))
    if narzedzie == "Bash" and not zlozone and polecenie.split()[:1] and polecenie.split()[0] in dozwolone:
        return {"behavior": "allow", "updatedInput": wejscie}
    return {"behavior": "deny", "message": f"Polityka projektu nie pozwala na {narzedzie}: "
                                           f"{json.dumps(wejscie, ensure_ascii=False)[:120]}"}


def obsluz(zadanie: dict) -> dict | None:
    metoda, ident, params = zadanie.get("method"), zadanie.get("id"), zadanie.get("params") or {}
    if ident is None:  # powiadomienie, np. notifications/initialized
        return None
    if metoda == "initialize":
        wersja = params.get("protocolVersion")
        wynik = {"protocolVersion": wersja if wersja in WERSJE else WERSJE[2],
                 "capabilities": {"tools": {"listChanged": True}, "resources": {"listChanged": True}},
                 "serverInfo": {"name": "wzor", "version": "1.0.0"},
                 "instructions": os.environ.get("WZOR_INSTRUKCJE", INSTRUKCJE)}
    elif metoda == "ping":
        wynik = {}
    elif metoda == "tools/list":
        wynik = {"tools": NARZEDZIA}
    elif metoda == "tools/call":
        nazwa, argumenty = params.get("name"), params.get("arguments") or {}
        dziennik({"narzedzie": nazwa, "argumenty": argumenty})
        if nazwa == "polityka_opis":
            tekst = ZASADY if argumenty.get("akcja") == "pelny" else "zmiany w katalogu; bez push; testy"
        elif nazwa == "polityka_raport":
            tekst = "Raport zgodności\n" + ("— wiersz raportu —\n" * 3000)
        elif nazwa == "polityka_zgoda":
            tekst = json.dumps(decyzja(argumenty), ensure_ascii=False)
        else:
            return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": f"nieznane narzędzie {nazwa}"}}
        wynik = {"content": [{"type": "text", "text": tekst}], "isError": False}
    elif metoda == "resources/list":
        wynik = {"resources": ZASOBY}
    elif metoda == "resources/read":
        wynik = {"contents": [{"uri": params.get("uri"), "mimeType": "text/markdown", "text": ZASADY}]}
    elif metoda in ("prompts/list", "resources/templates/list"):
        wynik = {"prompts": []} if metoda == "prompts/list" else {"resourceTemplates": []}
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": f"brak metody {metoda}"}}
    return {"jsonrpc": "2.0", "id": ident, "result": wynik}


def main() -> None:
    for linia in sys.stdin:
        linia = linia.strip()
        if not linia:
            continue
        try:
            odpowiedz = obsluz(json.loads(linia))
        except json.JSONDecodeError:
            odpowiedz = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "błąd parsowania"}}
        if odpowiedz is not None:
            sys.stdout.write(json.dumps(odpowiedz, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
