#!/usr/bin/env python3
"""Sprawdza zmienne środowiskowe, z którymi startuje Claude Code (proces, plik lub działający proces).

Źródła (jedno):
  (domyślnie)        środowisko bieżącego procesu,
  --plik PLIK        plik KLUCZ=WARTOŚĆ (EnvironmentFile systemd, .zmienne.txt generatora, docker --env-file),
  --pid PID          /proc/PID/environ działającego procesu (np. usługi uruchamiającej `claude`),
  --ustawienia PLIK  blok `env` pliku ustawień (+ --rodzaj user|project|local|managed|flaga).

Wypisuje: rozpoznane zmienne Claude Code z kategorią (wartości tylko z --wartosci, sekrety zawsze
zamaskowane — tylko długość), nazwy podobne do znanych (literówki), zmienne usunięte/przestarzałe, zmienne ignorowane
w danym rodzaju pliku oraz konflikty i pułapki (dwa sposoby uwierzytelnienia, kilku dostawców,
CLAUDE_CODE_PROJECT_DIR_NAME bez CLAUDE_CONFIG_DIR, wyłączony cache, flagi funkcji, treści w OTel).
Kod wyjścia: 1 gdy są błędy, 0 w pozostałych przypadkach.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
from cc_wspolne import wygladaja_na_sekret, zmienne  # noqa: E402

PRZEDROSTKI = ("CLAUDE", "ANTHROPIC_", "OTEL_", "MCP_", "DISABLE_", "ENABLE_", "BASH_", "API_", "MAX_",
               "VERTEX_REGION_", "AWS_BEARER", "FORCE_", "CCR_", "SLASH_COMMAND", "USE_BUILTIN", "TASK_",
               "FALLBACK_", "BETA_TRACING", "DO_NOT_TRACK", "IS_DEMO")
OGOLNE = {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "DEBUG", "OTEL_RESOURCE_ATTRIBUTES", "OTEL_METRICS_EXPORTER",
          "OTEL_LOGS_EXPORTER", "OTEL_TRACES_EXPORTER", "OTEL_METRIC_EXPORT_INTERVAL", "OTEL_LOGS_EXPORT_INTERVAL",
          "OTEL_TRACES_EXPORT_INTERVAL", "OTEL_SERVICE_NAME"}
OGOLNE_PRZEDROSTKI = ("OTEL_EXPORTER_OTLP_",)  # standard OpenTelemetry (cc:monitoring-usage)
USUNIETE = re.compile(r"Removed in v?([\d.]+)|^Deprecated")
# settings-reference, „Variables Claude Code ignores in env”
IGNOROWANE_ZAWSZE = {"CLAUDE_CODE_REMOTE", "CLAUDE_CODE_ACCOUNT_UUID", "CLAUDE_CODE_MESSAGING_SOCKET",
                     "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_PROJECT_DIR_NAME", "CLAUDE_CODE_RESTRICTED",
                     "CLAUDE_CODE_DISABLE_POWERSHELL_CMD_RM_DENY", "CLAUDE_CODE_DISABLE_DANGEROUS_RM_TIMEOUT",
                     "CLAUDE_CODE_DISABLE_SUBSTITUTION_RM_PROMPT"}
IGNOROWANE_W_PROJEKCIE = {"CLAUDE_CONFIG_DIR", "CLAUDE_CODE_TMPDIR", "HOME", "TMPDIR", "TMP", "TEMP",
                          "OTEL_LOG_RAW_API_BODIES", "ENABLE_BETA_TRACING_DETAILED", "BETA_TRACING_ENDPOINT",
                          "CLAUDE_CODE_ENABLE_TELEMETRY", "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA",
                          "ENABLE_ENHANCED_TELEMETRY_BETA", "OTEL_LOGS_EXPORTER", "OTEL_METRICS_EXPORTER",
                          "OTEL_TRACES_EXPORTER", "OTEL_LOG_USER_PROMPTS", "OTEL_LOG_ASSISTANT_RESPONSES",
                          "OTEL_LOG_TOOL_CONTENT", "OTEL_LOG_TOOL_DETAILS", "CLAUDE_CODE_PROCESS_WRAPPER",
                          "CLAUDE_CODE_SYNC_SKILLS", "CLAUDE_CODE_SYNC_PLUGINS", "CLAUDE_CODE_PLUGIN_CACHE_DIR",
                          "CLAUDE_CODE_PLUGIN_SEED_DIR"}
DOSTAWCY = ["CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
            "CLAUDE_CODE_USE_ANTHROPIC_AWS", "CLAUDE_CODE_USE_MANTLE"]
PRAWDA = {"1", "true", "yes", "on"}


def wczytaj(a) -> tuple[dict[str, str], str]:
    if a.plik:
        srodowisko = {}
        for linia in a.plik.read_text(encoding="utf-8").splitlines():
            linia = linia.strip()
            if not linia or linia.startswith("#"):
                continue
            linia = linia.removeprefix("export ")
            if "=" in linia:
                k, v = linia.split("=", 1)
                srodowisko[k.strip()] = v.strip().strip('"').strip("'")
        return srodowisko, f"plik {a.plik}"
    if a.pid:
        surowe = Path(f"/proc/{a.pid}/environ").read_bytes()
        return dict(x.split("=", 1) for x in surowe.decode(errors="replace").split("\0") if "=" in x), f"proces {a.pid}"
    if a.ustawienia:
        dane = json.loads(a.ustawienia.read_text(encoding="utf-8"))
        return {k: str(v) for k, v in (dane.get("env") or {}).items()}, f"env w {a.ustawienia} ({a.rodzaj})"
    return dict(os.environ), "środowisko bieżącego procesu"


def pokaz(nazwa: str, wartosc: str, jawnie: bool) -> str:
    if not jawnie:
        return f"<ustawiona, {len(wartosc)} zn.>"
    if wygladaja_na_sekret(nazwa) or "Bearer" in wartosc or re.search(r"(?i)authorization=", wartosc):
        return f"<ukryte, {len(wartosc)} zn.>"
    return wartosc if len(wartosc) <= 60 else wartosc[:57] + "…"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    zrodlo = p.add_mutually_exclusive_group()
    zrodlo.add_argument("--plik", type=Path)
    zrodlo.add_argument("--pid", type=int)
    zrodlo.add_argument("--ustawienia", type=Path)
    p.add_argument("--rodzaj", choices=["user", "project", "local", "managed", "flaga"], default="user")
    p.add_argument("--usluga", action="store_true", help="dodatkowe zalecenia dla usługi osadzającej CLI")
    p.add_argument("--cli", help="binarka CLI: nazwy spoza dokumentacji sprawdzane w jej napisach")
    p.add_argument("--wartosci", action="store_true",
                   help="pokaż wartości (sekrety i tak zamaskowane); domyślnie tylko długości")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    srodowisko, opis = wczytaj(a)
    znane = zmienne()
    z_binarki: set[str] = set()
    if a.cli:
        import shutil
        sciezka = shutil.which(a.cli) or a.cli
        dane = Path(os.path.realpath(sciezka)).read_bytes()
        z_binarki = {m.decode() for m in re.findall(rb"\b(?:CLAUDE|ANTHROPIC|OTEL|MCP|DISABLE|ENABLE)_[A-Z0-9_]{3,}\b", dane)}
    wynik = {"zrodlo": opis, "rozpoznane": [], "nieznane": [], "bledy": [], "ostrzezenia": [], "uwagi": []}
    for nazwa in sorted(srodowisko):
        wartosc = srodowisko[nazwa]
        if nazwa in znane:
            w = znane[nazwa]
            wynik["rozpoznane"].append({"zmienna": nazwa, "kategoria": w["kategoria"], "wartosc": pokaz(nazwa, wartosc, a.wartosci)})
            m = USUNIETE.search(w.get("opis_en", ""))
            if m:
                wynik["ostrzezenia"].append(f"{nazwa}: {'usunięta w ' + m.group(1) + ' — nie działa' if m.group(1) else 'przestarzała'} "
                                            f"({w['opis_en'][:120]})")
        elif nazwa in OGOLNE or nazwa.startswith(OGOLNE_PRZEDROSTKI):
            wynik["rozpoznane"].append({"zmienna": nazwa, "kategoria": "ogólna", "wartosc": pokaz(nazwa, wartosc, a.wartosci)})
        elif nazwa.startswith(PRZEDROSTKI) and not nazwa.startswith(("CLAUDE_PLUGIN_", "CLAUDE_PROJECT_DIR")):
            podobne = difflib.get_close_matches(nazwa, list(znane), n=2, cutoff=0.85)
            wynik["nieznane"].append({"zmienna": nazwa, "podobne": podobne, "w_binarce": nazwa in z_binarki})
        if a.ustawienia:
            if nazwa in IGNOROWANE_ZAWSZE:
                wynik["bledy"].append(f"{nazwa}: ignorowana w każdym pliku ustawień — tylko środowisko procesu")
            elif a.rodzaj in ("project", "local") and (nazwa in IGNOROWANE_W_PROJEKCIE or nazwa.startswith(("XDG_", "OTEL_EXPORTER_"))):
                wynik["bledy"].append(f"{nazwa}: ignorowana w ustawieniach {a.rodzaj} (≥2.1.251/2.1.282) — ustaw w powłoce, user lub managed")
            if wygladaja_na_sekret(nazwa) and wartosc:
                wynik["ostrzezenia"].append(f"{nazwa}: sekret jawnym tekstem w pliku ustawień — użyj apiKeyHelper/otelHeadersHelper/headersHelper")

    def ustawiona(n: str) -> bool:
        return srodowisko.get(n, "") != ""

    def wlaczona(n: str) -> bool:
        return srodowisko.get(n, "").lower() in PRAWDA

    dostawcy = [d for d in DOSTAWCY if wlaczona(d)]
    if len(dostawcy) > 1:
        wynik["bledy"].append(f"kilku dostawców naraz: {dostawcy}")
    # cc:authentication „Authentication precedence”: USE_* > AUTH_TOKEN > API_KEY > apiKeyHelper > OAUTH_TOKEN > profil > /login
    zrodla = [n for n in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN") if ustawiona(n)]
    if dostawcy and zrodla:
        wynik["ostrzezenia"].append(f"{dostawcy[0]} ma pierwszeństwo przed {zrodla} (poświadczenia dostawcy chmurowego)")
    elif len(zrodla) > 1:
        wynik["ostrzezenia"].append(f"kilka poświadczeń naraz {zrodla} — użyte zostanie {zrodla[0]} (kolejność: "
                                    "AUTH_TOKEN > API_KEY > apiKeyHelper > OAUTH_TOKEN); przy kluczu API domyślny "
                                    "TTL cache to 5m (próba)")
    if ustawiona("CLAUDE_CODE_PROJECT_DIR_NAME"):
        if not ustawiona("CLAUDE_CONFIG_DIR"):
            wynik["bledy"].append("CLAUDE_CODE_PROJECT_DIR_NAME działa tylko razem z CLAUDE_CONFIG_DIR")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", srodowisko["CLAUDE_CODE_PROJECT_DIR_NAME"]):
            wynik["bledy"].append("CLAUDE_CODE_PROJECT_DIR_NAME: dozwolone 1–64 znaki [A-Za-z0-9_-]")
    if wlaczona("DISABLE_PROMPT_CACHING"):
        wynik["ostrzezenia"].append("DISABLE_PROMPT_CACHING=1 — żądania bez znaczników cache (próba); tylko do diagnozy")
    if wlaczona("FORCE_PROMPT_CACHING_5M") and (ustawiona("CLAUDE_CODE_PROMPT_CACHE_TTL") or wlaczona("ENABLE_PROMPT_CACHING_1H")):
        wynik["ostrzezenia"].append("FORCE_PROMPT_CACHING_5M wygrywa z ustawieniami TTL 1h")
    v = srodowisko.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "")
    if v and not v.isdigit():
        wynik["bledy"].append("CLAUDE_CODE_AUTO_COMPACT_WINDOW przyjmuje tylko liczbę tokenów (np. 500000, nie 500k)")
    if any(wlaczona(n) for n in ("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "DISABLE_GROWTHBOOK", "DISABLE_TELEMETRY", "DO_NOT_TRACK")):
        wynik["uwagi"].append("flagi funkcji nie są pobierane: bez /auto-mode-setup, Remote Control, synchronizacji "
                              "skilli/wtyczek, doradcy; `-p` bez jawnego --permission-mode startuje w `auto` (≥2.1.285, próba)")
    if ustawiona("ANTHROPIC_BASE_URL"):
        wynik["uwagi"].append("ANTHROPIC_BASE_URL — tool search wyłączony (wszystkie narzędzia MCP z góry; zmiana MCP "
                              "unieważnia cache); brama musi przekazywać cache_control i anthropic-beta")
    tresci = [n for n in ("OTEL_LOG_USER_PROMPTS", "OTEL_LOG_ASSISTANT_RESPONSES", "OTEL_LOG_TOOL_DETAILS",
                          "OTEL_LOG_TOOL_CONTENT", "OTEL_LOG_RAW_API_BODIES") if wlaczona(n)]
    if tresci:
        wynik["ostrzezenia"].append(f"telemetria eksportuje treści: {tresci}")
    if a.usluga:
        for n, powod in (("DISABLE_AUTOUPDATER", "przypięta wersja CLI"),
                         ("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "pamięć dzierżawcy i wspólny cache instrukcji"),
                         ("CLAUDE_CONFIG_DIR", "izolacja konfiguracji i transkryptów"),
                         ("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "poświadczenia poza podprocesami")):
            if not ustawiona(n):
                wynik["uwagi"].append(f"usługa: brak {n} ({powod})")

    if a.json:
        print(json.dumps(wynik, ensure_ascii=False, indent=1))
    else:
        print(f"Źródło: {opis}; zmiennych Claude Code: {len(wynik['rozpoznane'])}")
        for r in wynik["rozpoznane"]:
            print(f"  {r['zmienna']} = {r['wartosc']}  [{r['kategoria']}]")
        for n in wynik["nieznane"]:
            if n["w_binarce"]:
                print(f"  NIEUDOKUMENTOWANA {n['zmienna']} — obecna w binarce CLI, brak w cc:env-vars (zachowanie może się zmienić)")
            else:
                print(f"  NIEZNANA {n['zmienna']}" + (f" — może {', '.join(n['podobne'])}?" if n["podobne"] else ""))
        for etykieta, klucz in (("BŁĄD", "bledy"), ("ostrzeżenie", "ostrzezenia"), ("uwaga", "uwagi")):
            for t in wynik[klucz]:
                print(f"  {etykieta}: {t}")
    return 1 if wynik["bledy"] else 0


if __name__ == "__main__":
    sys.exit(main())
