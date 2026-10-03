#!/usr/bin/env python3
"""Analiza skuteczności prompt cache z transkryptów sesji lub wyjścia stream-json.

Wejście (dowolna liczba plików lub katalogów):
  - transkrypty `<CLAUDE_CONFIG_DIR>/projects/<projekt>/<sesja>.jsonl` (wpisy `assistant`
    z `message.usage`; podagenci w `<sesja>/subagents/*.jsonl` albo `isSidechain: true`),
  - wyjście `claude -p --output-format stream-json --verbose` (zdarzenia `assistant`
    i `result`).
Dla każdej sesji: liczba żądań, tokeny wejścia/odczytu/zapisu cache (zapisy 1h i 5m),
udział wejścia z cache, „chybienia” (żądanie, które zapisało ponad --prog tokenów, choć
poprzednie żądanie było w czasie życia cache), przerwy dłuższe niż TTL (chybienia
oczekiwane), modele i poziomy effort. Z --ceny PLIK (format `modelPricing.overrides`:
{"model": {"input":…, "output":…, "cacheRead":…, "cacheWrite":…}} w USD/1M tokenów)
liczy koszt i oszczędność cache.

Użycie:
  analiza_cache.py ŚCIEŻKA… [--prog 20000] [--ttl-s 300|3600] [--ceny ceny.json] [--json]
Nie wypisuje treści rozmów — tylko liczby, modele i znaczniki czasu.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def pliki(sciezki: list[Path]):
    for s in sciezki:
        if s.is_dir():
            yield from sorted(s.rglob("*.jsonl"))
        elif s.exists():
            yield s


def czas(napis: str | None):
    if not napis:
        return None
    try:
        return datetime.fromisoformat(napis.replace("Z", "+00:00"))
    except ValueError:
        return None


def zbierz(plik: Path) -> dict[str, list[dict]]:
    """Zwraca {klucz_sesji: [żądania]}; żądanie = usage jednej odpowiedzi API."""
    sesje: dict[str, list[dict]] = defaultdict(list)
    widziane: set[str] = set()
    with plik.open(encoding="utf-8", errors="replace") as f:
        for linia in f:
            try:
                w = json.loads(linia)
            except json.JSONDecodeError:
                continue
            if w.get("type") != "assistant":
                continue
            m = w.get("message") or {}
            u = m.get("usage")
            if not isinstance(u, dict) or m.get("model") == "<synthetic>":  # wpisy lokalne, bez żądania API
                continue
            ident = m.get("id") or w.get("requestId") or w.get("uuid")
            if ident in widziane:  # kilka bloków treści jednej odpowiedzi ma to samo usage
                continue
            widziane.add(ident)
            podagent = bool(w.get("isSidechain")) or "subagents" in plik.parts or bool(w.get("parent_tool_use_id"))
            sesja = (w.get("sessionId") or w.get("session_id") or plik.stem) + (" [podagent]" if podagent else "")
            cc = u.get("cache_creation") or {}
            sesje[sesja].append({
                "czas": czas(w.get("timestamp")),
                "model": m.get("model") or "?",
                "effort": w.get("effort"),
                "wejscie": u.get("input_tokens") or 0,
                "odczyt": u.get("cache_read_input_tokens") or 0,
                "zapis": u.get("cache_creation_input_tokens") or 0,
                "zapis_1h": cc.get("ephemeral_1h_input_tokens") or 0,
                "zapis_5m": cc.get("ephemeral_5m_input_tokens") or 0,
                "wyjscie": u.get("output_tokens") or 0,
            })
    return sesje


def koszt(z: dict, ceny: dict) -> tuple[float, float] | None:
    c = ceny.get(z["model"])
    if not c:
        for klucz, wartosc in ceny.items():
            if z["model"].startswith(klucz):
                c = wartosc
                break
    if not c:
        return None
    rzeczywisty = (z["wejscie"] * c["input"] + z["odczyt"] * c["cacheRead"] + z["zapis"] * c["cacheWrite"]
                   + z["wyjscie"] * c["output"]) / 1e6
    bez_cache = ((z["wejscie"] + z["odczyt"] + z["zapis"]) * c["input"] + z["wyjscie"] * c["output"]) / 1e6
    return rzeczywisty, bez_cache


def analizuj(zadania: list[dict], prog: int, ttl_s: int, ceny: dict | None) -> dict:
    zadania = sorted(zadania, key=lambda z: z["czas"].timestamp() if z["czas"] else 0.0)
    suma = defaultdict(int)
    chybienia, przerwy = [], []
    poprzedni = None
    koszt_r = koszt_b = 0.0
    bez_ceny = set()
    for i, z in enumerate(zadania):
        for k in ("wejscie", "odczyt", "zapis", "zapis_1h", "zapis_5m", "wyjscie"):
            suma[k] += z[k]
        if poprzedni is not None and z["czas"] and poprzedni["czas"]:
            odstep = (z["czas"] - poprzedni["czas"]).total_seconds()
            if odstep > ttl_s:
                przerwy.append({"nr": i + 1, "odstep_s": int(odstep), "zapis": z["zapis"]})
            elif z["zapis"] > prog and z["odczyt"] < z["zapis"]:
                chybienia.append({"nr": i + 1, "czas": z["czas"].isoformat(timespec="seconds"),
                                  "zapis": z["zapis"], "odczyt": z["odczyt"], "model": z["model"],
                                  "zmiana_modelu": z["model"] != poprzedni["model"],
                                  "zmiana_effort": z["effort"] != poprzedni["effort"]})
        poprzedni = z
        if ceny is not None:
            k = koszt(z, ceny)
            if k:
                koszt_r += k[0]
                koszt_b += k[1]
            else:
                bez_ceny.add(z["model"])
    caly = suma["wejscie"] + suma["odczyt"] + suma["zapis"]
    wynik = {
        "zadania": len(zadania),
        "modele": sorted({z["model"] for z in zadania}),
        "effort": sorted({str(z["effort"]) for z in zadania if z["effort"]}),
        **dict(suma),
        "udzial_z_cache": round(suma["odczyt"] / caly, 3) if caly else None,
        "ttl_zapisow": ("1h" if suma["zapis_1h"] and not suma["zapis_5m"] else
                        "5m" if suma["zapis_5m"] and not suma["zapis_1h"] else
                        "mieszane" if suma["zapis_1h"] else "brak danych"),
        "chybienia": chybienia,
        "przerwy_ponad_ttl": przerwy,
    }
    if ceny is not None:
        wynik["koszt_usd"] = round(koszt_r, 4)
        wynik["koszt_bez_cache_usd"] = round(koszt_b, 4)
        if bez_ceny:
            wynik["modele_bez_ceny"] = sorted(bez_ceny)
    return wynik


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sciezki", nargs="+", type=Path)
    p.add_argument("--prog", type=int, default=20000, help="zapis cache uznawany za chybienie (tokeny)")
    p.add_argument("--ttl-s", type=int, default=300, help="czas życia cache w s (300 lub 3600)")
    p.add_argument("--ceny", type=Path, help="JSON w formacie modelPricing.overrides")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    ceny = None
    if a.ceny:
        dane = json.loads(a.ceny.read_text(encoding="utf-8"))
        ceny = dane.get("overrides", dane)
    wszystkie: dict[str, list[dict]] = defaultdict(list)
    for plik in pliki(a.sciezki):
        for sesja, zadania in zbierz(plik).items():
            wszystkie[sesja].extend(zadania)
    if not wszystkie:
        print("Brak wpisów z usage (transkrypt lub stream-json).")
        return 1
    raport = {s: analizuj(z, a.prog, a.ttl_s, ceny) for s, z in wszystkie.items()}
    if a.json:
        print(json.dumps(raport, ensure_ascii=False, indent=1, default=str))
        return 0
    for sesja, r in raport.items():
        print(f"== {sesja}: żądań {r['zadania']}, modele {r['modele']}, effort {r['effort'] or '-'}")
        udzial = f"{r['udzial_z_cache'] * 100:.1f}%" if r["udzial_z_cache"] is not None else "-"
        print(f"   wejście {r['wejscie']:,} | odczyt cache {r['odczyt']:,} | zapis cache {r['zapis']:,} "
              f"(1h {r['zapis_1h']:,}, 5m {r['zapis_5m']:,}) | wyjście {r['wyjscie']:,}")
        print(f"   udział wejścia z cache: {udzial}; TTL zapisów: {r['ttl_zapisow']}")
        if "koszt_usd" in r:
            print(f"   koszt: {r['koszt_usd']} USD (bez cache byłoby {r['koszt_bez_cache_usd']} USD)"
                  + (f"; brak cen dla {r['modele_bez_ceny']}" if r.get("modele_bez_ceny") else ""))
        for c in r["chybienia"][:10]:
            powod = "zmiana modelu" if c["zmiana_modelu"] else "zmiana effort" if c["zmiana_effort"] else \
                "zmiana prefiksu (narzędzia/MCP/instrukcja, kompakcja, obrazy, wersja CLI)"
            print(f"   chybienie #{c['nr']} {c['czas']}: zapis {c['zapis']:,}, odczyt {c['odczyt']:,} — {powod}")
        if len(r["chybienia"]) > 10:
            print(f"   … i {len(r['chybienia']) - 10} kolejnych chybień")
        if r["przerwy_ponad_ttl"]:
            print(f"   przerwy dłuższe niż TTL ({a.ttl_s} s): {len(r['przerwy_ponad_ttl'])} "
                  f"(zapis po przerwach łącznie {sum(x['zapis'] for x in r['przerwy_ponad_ttl']):,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
