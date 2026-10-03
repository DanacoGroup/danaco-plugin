#!/usr/bin/env python3
"""Sprawdzenie konfiguracji MCP (.mcp.json, --mcp-config, managed-mcp.json) i serwerów stdio.

Część 1 — plik konfiguracji: struktura `mcpServers`, typy (`stdio`, `http`, `sse`, `ws`),
wymagane pola, nazwy zastrzeżone, ukryte białe znaki, `${VAR}` bez wartości domyślnej,
zmienne poświadczeń w `url`/`headers` serwera zdalnego (CLI czyta je jako puste), sekrety
wpisane dosłownie, względny `headersHelper`, `alwaysLoad`.

Część 2 — z opcją --polacz: uruchamia każdy serwer stdio, wykonuje `initialize`
i `tools/list` (oraz `resources/list`, gdy serwer je deklaruje) i ocenia projekt narzędzi
według praktyk Anthropic: długość instrukcji serwera i opisów (domyślny limit 2048 znaków,
CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH), opisy zbyt krótkie (zalecane 3–4 zdania), nazwy
właściwości schematu (1–64 znaki [A-Za-z0-9_.-]), kombinatory w korzeniu schematu,
adnotacje `_meta` (`anthropic/alwaysLoad`, `anthropic/maxResultSizeChars` ≤ 500 000,
`anthropic/requiresUserInteraction`), przestrzeń nazw i liczba narzędzi.

Użycie:
  sprawdz_mcp.py PLIK.json [--polacz] [--limit-opisu 2048]
Wartości sekretów nie są wypisywane.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

ZASTRZEZONE = {"workspace", "claude-in-chrome", "computer-use", "Claude Preview", "Claude Browser", "anthropic-skills"}
POSWIADCZENIA = {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "AWS_BEARER_TOKEN_BEDROCK", "HTTPS_PROXY", "NPM_TOKEN",
                 "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_FOUNDRY_API_KEY", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN"}
SEKRET = re.compile(r"(^|_)(TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|CREDENTIALS?)($|_)", re.I)
NAZWA_WLASCIWOSCI = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def sprawdz_plik(dane: dict) -> list[str]:
    uwagi = []
    serwery = dane.get("mcpServers")
    if not isinstance(serwery, dict):
        return ["BŁĄD: brak obiektu mcpServers"]
    if not serwery:
        uwagi.append("uwaga: pusta mapa mcpServers (w managed-mcp.json = wyłączenie MCP poza serwerami zarządzanymi)")
    for nazwa, s in serwery.items():
        p = f"[{nazwa}]"
        if nazwa in ZASTRZEZONE:
            uwagi.append(f"BŁĄD {p}: nazwa zastrzeżona — CLI pominie serwer")
        if not isinstance(s, dict):
            uwagi.append(f"BŁĄD {p}: wpis nie jest obiektem")
            continue
        typ = s.get("type", "stdio" if "command" in s else None)
        if typ not in ("stdio", "http", "sse", "ws"):
            uwagi.append(f"BŁĄD {p}: type={typ!r} — dozwolone stdio, http, sse, ws")
            continue
        if typ == "stdio" and not s.get("command"):
            uwagi.append(f"BŁĄD {p}: stdio wymaga `command`")
        if typ != "stdio" and "url" not in s:
            uwagi.append(f"BŁĄD {p}: {typ} wymaga `url` (pusty `url` = „not configured”)")
        for pole in ("command", "url"):
            if isinstance(s.get(pole), str) and s[pole] != s[pole].strip():
                uwagi.append(f"BŁĄD {p}: białe znaki na początku/końcu `{pole}`")
        for pole in ("args",):
            for arg in s.get(pole, []) or []:
                if isinstance(arg, str) and arg != arg.strip():
                    uwagi.append(f"BŁĄD {p}: białe znaki w elemencie `args`")
        for blok in ("env", "headers"):
            for k, v in (s.get(blok) or {}).items():
                if not isinstance(v, str):
                    uwagi.append(f"BŁĄD {p}: {blok}.{k} musi być tekstem")
                    continue
                if v != v.strip() or k != k.strip():
                    uwagi.append(f"BŁĄD {p}: ukryte białe znaki w {blok}.{k} (często wklejony token z nową linią)")
                if (SEKRET.search(k) or k.lower() == "authorization") and v and "${" not in v:
                    uwagi.append(f"BŁĄD {p}: {blok}.{k} — wartość dosłowna wygląda na sekret; użyj ${{ZMIENNA}}, "
                                 f"headersHelper albo OAuth (wartość nie jest wypisywana)")
        tekst = json.dumps(s)
        for zmienna, domyslna in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-[^}]*)?\}", tekst):
            if not domyslna and zmienna not in os.environ and zmienna != "CLAUDE_PLUGIN_ROOT":
                uwagi.append(f"uwaga {p}: ${{{zmienna}}} bez wartości domyślnej i nieustawiona teraz — "
                             f"CLI użyje dosłownego tekstu i ostrzeże")
            if typ != "stdio" and zmienna in POSWIADCZENIA:
                uwagi.append(f"BŁĄD {p}: ${{{zmienna}}} w url/headers serwera zdalnego CLI czyta jako PUSTE — "
                             f"skopiuj wartość do zmiennej o własnej nazwie")
            if zmienna == "CLAUDE_PROJECT_DIR" and not domyslna:
                uwagi.append(f"uwaga {p}: ${{CLAUDE_PROJECT_DIR}} poza wtyczką wymaga wartości domyślnej "
                             f"(${{CLAUDE_PROJECT_DIR:-.}}) — zmienna jest w środowisku serwera, nie CLI")
        if s.get("headersHelper") and not str(s["headersHelper"]).startswith(("/", "${", "echo")):
            uwagi.append(f"uwaga {p}: headersHelper ze ścieżką względną — katalog roboczy zależy od zakresu; podaj ścieżkę bezwzględną")
        if s.get("alwaysLoad"):
            uwagi.append(f"uwaga {p}: alwaysLoad — wszystkie narzędzia serwera w kontekście od startu i start czeka "
                         f"na serwer (do 5 s); tylko dla małych serwerów rdzenia")
        if typ == "ws" and s.get("oauth"):
            uwagi.append(f"BŁĄD {p}: ws nie obsługuje OAuth (tylko nagłówki/headersHelper)")
    return uwagi


def rozmowa(polecenie: list[str], env: dict, limit_s: float = 15.0) -> dict:
    proces = subprocess.Popen(polecenie, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              env=env, text=True)
    odpowiedzi: dict = {}

    def wyslij(obiekt: dict) -> None:
        proces.stdin.write(json.dumps(obiekt) + "\n")
        proces.stdin.flush()

    def czekaj(ident: int) -> dict | None:
        koniec = time.time() + limit_s
        while time.time() < koniec:
            gotowe, _, _ = select.select([proces.stdout], [], [], 0.2)
            if gotowe:
                linia = proces.stdout.readline()
                if not linia:
                    return None
                try:
                    wiadomosc = json.loads(linia)
                except json.JSONDecodeError:
                    continue
                if wiadomosc.get("id") == ident:
                    return wiadomosc
        return None

    try:
        wyslij({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "sprawdz_mcp", "version": "1"}}})
        odpowiedzi["initialize"] = czekaj(1)
        wyslij({"jsonrpc": "2.0", "method": "notifications/initialized"})
        wyslij({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        odpowiedzi["tools"] = czekaj(2)
        mozliwosci = ((odpowiedzi.get("initialize") or {}).get("result") or {}).get("capabilities") or {}
        if "resources" in mozliwosci:
            wyslij({"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}})
            odpowiedzi["resources"] = czekaj(3)
    finally:
        proces.kill()
    return odpowiedzi


def ocen_serwer(nazwa: str, odp: dict, limit: int) -> list[str]:
    p = f"[{nazwa}]"
    init = (odp.get("initialize") or {}).get("result")
    if not init:
        return [f"BŁĄD {p}: brak odpowiedzi na initialize (serwer nie startuje albo pisze na stdout coś poza JSON-RPC)"]
    uwagi = [f"{p} protokół {init.get('protocolVersion')}, serwer {init.get('serverInfo', {}).get('name')}"]
    instrukcje = init.get("instructions") or ""
    if not instrukcje:
        uwagi.append(f"uwaga {p}: brak `instructions` — przy tool search to jedyny opis serwera ładowany na starcie")
    elif len(instrukcje) > limit:
        uwagi.append(f"BŁĄD {p}: instrukcje {len(instrukcje)} znaków > {limit} — reszta ucięta "
                     f"(CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH ≥2.1.280)")
    mozliwosci = init.get("capabilities") or {}
    if not (mozliwosci.get("tools") or {}).get("listChanged"):
        uwagi.append(f"uwaga {p}: brak tools.listChanged — zmiana listy narzędzi wymaga ponownego połączenia")
    narzedzia = ((odp.get("tools") or {}).get("result") or {}).get("tools") or []
    uwagi.append(f"{p} narzędzi: {len(narzedzia)}")
    if len(narzedzia) > 40:
        uwagi.append(f"uwaga {p}: dużo narzędzi — rozważ łączenie operacji parametrem `action` (mniej niejednoznaczności)")
    przedrostki = {n.get("name", "").split("_")[0] for n in narzedzia}
    if len(narzedzia) > 3 and len(przedrostki) == len(narzedzia):
        uwagi.append(f"uwaga {p}: nazwy bez wspólnej przestrzeni nazw (np. `zasob_akcja`)")
    for n in narzedzia:
        nazwa_n = n.get("name", "?")
        opis = n.get("description") or ""
        zdania = len(re.findall(r"[.!?](\s|$)", opis))
        if len(opis) > limit:
            uwagi.append(f"BŁĄD {p}.{nazwa_n}: opis {len(opis)} znaków > {limit} — ucięty")
        elif zdania < 2:
            uwagi.append(f"uwaga {p}.{nazwa_n}: opis krótki ({zdania} zd.) — zalecane 3–4 zdania: co robi, kiedy (nie) używać, parametry, ograniczenia")
        schemat = n.get("inputSchema") or {}
        for slowo in ("anyOf", "oneOf", "allOf"):
            if slowo in schemat:
                uwagi.append(f"uwaga {p}.{nazwa_n}: `{slowo}` w korzeniu schematu — CLI spłaszczy schemat i dopisze opis")
        for wl in (schemat.get("properties") or {}):
            if not NAZWA_WLASCIWOSCI.match(wl):
                uwagi.append(f"BŁĄD {p}.{nazwa_n}: właściwość {wl!r} poza [A-Za-z0-9_.-]{{1,64}} — API odrzuci narzędzie")
        meta = n.get("_meta") or {}
        if "anthropic/maxResultSizeChars" in meta and int(meta["anthropic/maxResultSizeChars"]) > 500000:
            uwagi.append(f"BŁĄD {p}.{nazwa_n}: maxResultSizeChars > 500 000 (twardy limit)")
        if meta.get("anthropic/requiresUserInteraction") not in (None, True):
            uwagi.append(f"BŁĄD {p}.{nazwa_n}: requiresUserInteraction musi być JSON-owym true")
        oznaczenia = [k.split("/")[1] for k in meta if k.startswith("anthropic/")]
        if oznaczenia:
            uwagi.append(f"{p}.{nazwa_n}: _meta {', '.join(oznaczenia)}")
    zasoby = ((odp.get("resources") or {}).get("result") or {}).get("resources")
    if zasoby is not None:
        uwagi.append(f"{p} zasobów: {len(zasoby)}")
    return uwagi


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plik", type=Path)
    parser.add_argument("--polacz", action="store_true")
    parser.add_argument("--limit-opisu", type=int,
                        default=int(os.environ.get("CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH", "2048")))
    a = parser.parse_args()
    try:
        dane = json.loads(a.plik.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as blad:
        print(f"BŁĄD: {blad}")
        return 1
    uwagi = sprawdz_plik(dane)
    if a.polacz:
        for nazwa, s in (dane.get("mcpServers") or {}).items():
            if isinstance(s, dict) and s.get("type", "stdio") == "stdio" and s.get("command"):
                env = dict(os.environ, **{k: os.path.expandvars(v) for k, v in (s.get("env") or {}).items()})
                polecenie = [os.path.expandvars(s["command"])] + [os.path.expandvars(x) for x in s.get("args", [])]
                uwagi += ocen_serwer(nazwa, rozmowa(polecenie, env), a.limit_opisu)
            else:
                uwagi.append(f"[{nazwa}]: serwer zdalny — sprawdź `claude mcp list` / `claude mcp get {nazwa}`")
    for u in uwagi or ["bez uwag"]:
        print(u)
    return 1 if any(u.startswith("BŁĄD") for u in uwagi) else 0


if __name__ == "__main__":
    sys.exit(main())
