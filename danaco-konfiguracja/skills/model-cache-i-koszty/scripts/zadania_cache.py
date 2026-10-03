#!/usr/bin/env python3
"""Pokazuje, jak CLI ustawia cache w żądaniach do API (zrzuty atrapy lub bramy).

Czyta pliki zapisane przez `scripts/atrapa_api.py` (`<katalog>/zadania/*messages*.json`:
pierwszy wiersz — nagłówki z zamaskowanym uwierzytelnieniem, dalej treść żądania)
i dla każdego żądania wypisuje:
  - model, effort (`output_config.effort`), tryb myślenia,
  - znaczniki `cache_control` (miejsce i TTL) oraz beta `extended-cache-ttl-…`,
  - skróty SHA-256 bloków `system` i listy narzędzi — dwa żądania z różnym skrótem
    nie dzielą prefiksu cache (porównuj przebiegi: --porownaj KATALOG2).

Użycie:
  zadania_cache.py KATALOG_ZADAN [--porownaj KATALOG_ZADAN2] [--json]
Kod wyjścia: 0; 1 gdy brak żądań.
Nie wypisuje treści instrukcji ani nagłówków uwierzytelnienia — tylko długości i skróty.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def skrot(obiekt) -> str:
    return hashlib.sha256(json.dumps(obiekt, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def znaczniki(obiekt, sciezka=""):
    if isinstance(obiekt, dict):
        if "cache_control" in obiekt:
            yield sciezka or ".", obiekt["cache_control"]
        for k, v in obiekt.items():
            yield from znaczniki(v, f"{sciezka}.{k}")
    elif isinstance(obiekt, list):
        for i, v in enumerate(obiekt):
            yield from znaczniki(v, f"{sciezka}[{i}]")


def czytaj(katalog: Path) -> list[dict]:
    wyniki = []
    for plik in sorted(katalog.glob("*messages*.json")):
        naglowki_txt, _, tresc = plik.read_text(encoding="utf-8").partition("\n")
        try:
            naglowki = {k.lower(): v for k, v in json.loads(naglowki_txt).get("headers", {}).items()}
            zadanie = json.loads(tresc)
        except json.JSONDecodeError:
            continue
        if "count_tokens" in plik.name:
            continue
        system = zadanie.get("system") or []
        if isinstance(system, str):
            system = [{"type": "text", "text": system}]
        bety = [b for b in naglowki.get("anthropic-beta", "").split(",") if b]
        wyniki.append({
            "plik": plik.name,
            "model": zadanie.get("model"),
            "effort": (zadanie.get("output_config") or {}).get("effort"),
            "myslenie": (zadanie.get("thinking") or {}).get("type"),
            "narzedzia": len(zadanie.get("tools") or []),
            "system_dlugosci": [len(b.get("text", "")) for b in system],
            "system_skroty": [skrot(b.get("text", "")) for b in system],
            "narzedzia_skrot": skrot(zadanie.get("tools") or []),
            "znaczniki": [{"gdzie": g, **(c if isinstance(c, dict) else {"wartosc": c})} for g, c in znaczniki(
                {k: zadanie[k] for k in ("system", "messages", "tools") if k in zadanie})],
            "beta_ttl_1h": any(b.startswith("extended-cache-ttl") for b in bety),
            "beta_zakres_cache": any(b.startswith("prompt-caching-scope") for b in bety),
        })
    return wyniki


def drukuj(nazwa: str, zadania: list[dict]) -> None:
    print(f"== {nazwa}: żądań {len(zadania)}")
    for z in zadania:
        ttl = sorted({m.get("ttl", "5m") for m in z["znaczniki"]}) or ["brak znaczników"]
        print(f"  {z['plik']}: model={z['model']} effort={z['effort']} myślenie={z['myslenie']} "
              f"narzędzia={z['narzedzia']} (skrót {z['narzedzia_skrot']})")
        print(f"    system: długości={z['system_dlugosci']} skróty={z['system_skroty']}")
        print(f"    cache_control: {len(z['znaczniki'])}× TTL={ttl}; beta 1h={z['beta_ttl_1h']} "
              f"zakres={z['beta_zakres_cache']}")
        for m in z["znaczniki"]:
            print(f"      {m['gdzie']}: {({k: v for k, v in m.items() if k != 'gdzie'})}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("katalog", type=Path)
    p.add_argument("--porownaj", type=Path)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    pierwsze = czytaj(a.katalog)
    drugie = czytaj(a.porownaj) if a.porownaj else None
    if a.json:
        print(json.dumps({"a": pierwsze, "b": drugie}, ensure_ascii=False, indent=1))
        return 0 if pierwsze else 1
    if not pierwsze:
        print(f"Brak żądań /v1/messages w {a.katalog}")
        return 1
    drukuj(str(a.katalog), pierwsze)
    if drugie is not None:
        drukuj(str(a.porownaj), drugie)
        x, y = pierwsze[0], drugie[0]
        print("== porównanie pierwszych żądań")
        wspolne = 0
        for s1, s2 in zip(x["system_skroty"], y["system_skroty"]):
            if s1 != s2:
                break
            wspolne += 1
        print(f"  model ten sam: {x['model'] == y['model']}; effort ten sam: {x['effort'] == y['effort']}")
        print(f"  narzędzia te same: {x['narzedzia_skrot'] == y['narzedzia_skrot']}")
        print(f"  wspólny prefiks system: {wspolne}/{max(len(x['system_skroty']), len(y['system_skroty']))} bloków")
        if x["narzedzia_skrot"] != y["narzedzia_skrot"] or wspolne == 0:
            print("  WNIOSEK: prefiks różny od początku — przebiegi nie dzielą cache.")
        elif wspolne < len(x["system_skroty"]):
            print("  WNIOSEK: wspólny początek instrukcji; cache trafia do pierwszego różnego bloku "
                  "(o ile przed nim jest znacznik cache_control).")
        else:
            print("  WNIOSEK: identyczna instrukcja i narzędzia — prefiks wspólny (ten sam model i organizacja).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
