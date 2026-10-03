#!/usr/bin/env python3
"""Automatyczna lista kontrolna bezpieczeństwa wdrożenia Claude Code.

Ocenia komplet konfiguracji: pliki ustawień (scalane w podanej kolejności, listy sumowane),
flagi uruchomienia (plik tekstowy, np. `<nazwa>.flagi.txt` z generatora) i środowisko procesu
(plik KLUCZ=WARTOŚĆ, np. `<nazwa>.zmienne.txt`). Każdy punkt dostaje wynik:
  OK — spełniony, BRAK — niespełniony (wymagany dla profilu), UWAGA — zalecany, nie dotyczy (n/d).

Profile:
  stanowisko  — praca człowieka przy terminalu (zespół),
  ci          — potok CI/CD bez człowieka,
  usluga      — produkt osadzający CLI dla wielu użytkowników (np. Danaco Nexus).

Użycie:
  lista_kontrolna.py --profil usluga --ustawienia a.json [b.json…] [--flagi flagi.txt] [--zmienne env.txt]
                     [--json] [--markdown RAPORT.md]
Kod wyjścia: 1, gdy którykolwiek punkt wymagany ma wynik BRAK.
Nie wypisuje wartości sekretów.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402

PRAWDA = {"1", "true", "yes", "on"}


def scal(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        w = dict(a)
        for k, v in b.items():
            w[k] = scal(a[k], v) if k in a else v
        return w
    if isinstance(a, list) and isinstance(b, list):
        return a + [x for x in b if x not in a]
    return b


def czytaj_flagi(sciezka: Path | None) -> list[str]:
    if not sciezka:
        return []
    tekst = " ".join(w.split("#")[0] for w in sciezka.read_text(encoding="utf-8").splitlines())
    try:
        return shlex.split(tekst)
    except ValueError:
        return tekst.split()


def czytaj_env(sciezka: Path | None) -> dict[str, str]:
    wynik = {}
    if sciezka:
        for w in sciezka.read_text(encoding="utf-8").splitlines():
            w = w.strip().removeprefix("export ")
            if w and not w.startswith("#") and "=" in w:
                k, v = w.split("=", 1)
                wynik[k.strip()] = v.strip().strip('"').strip("'")
    return wynik


def wartosc_flagi(flagi: list[str], nazwa: str) -> str | None:
    for i, f in enumerate(flagi):
        if f == nazwa:
            return flagi[i + 1] if i + 1 < len(flagi) else ""
        if f.startswith(nazwa + "="):
            return f.split("=", 1)[1]
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profil", choices=["stanowisko", "ci", "usluga"], required=True)
    p.add_argument("--ustawienia", type=Path, nargs="+", required=True)
    p.add_argument("--flagi", type=Path)
    p.add_argument("--zmienne", type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--markdown", type=Path)
    a = p.parse_args()

    u: dict = {}
    for plik in a.ustawienia:
        u = scal(u, cc.czytaj_json(plik))
    flagi = czytaj_flagi(a.flagi)
    env = {**{k: str(v) for k, v in (u.get("env") or {}).items()}, **czytaj_env(a.zmienne)}
    perm = u.get("permissions") or {}
    allow, deny = perm.get("allow") or [], perm.get("deny") or []
    sb = u.get("sandbox") or {}
    siec = sb.get("network") or {}
    tryb = wartosc_flagi(flagi, "--permission-mode") or perm.get("defaultMode")
    narzedzia_flaga = wartosc_flagi(flagi, "--tools")
    narzedzia = None if narzedzia_flaga is None else {t.strip() for t in re.split(r"[ ,]", narzedzia_flaga) if t.strip()}
    bez_bash = narzedzia is not None and not ({"Bash", "PowerShell"} & narzedzia)
    bez_plikow = narzedzia is not None and not ({"Read", "Grep", "Glob", "Bash", "PowerShell"} & narzedzia)
    bezobslugowy = a.profil in ("ci", "usluga")
    wyniki: list[dict] = []

    def punkt(ident, opis, spelniony, wymagany_dla=("stanowisko", "ci", "usluga"), zalecany_dla=(), uwaga="", zrodlo=""):
        if a.profil in wymagany_dla:
            stan = "OK" if spelniony else "BRAK"
        elif a.profil in zalecany_dla:
            stan = "OK" if spelniony else "UWAGA"
        else:
            stan = "n/d"
        wyniki.append({"id": ident, "opis": opis, "stan": stan, "uwaga": "" if spelniony else uwaga, "zrodlo": zrodlo})

    # Uprawnienia
    punkt("U01", "tryb omijania zablokowany (disableBypassPermissionsMode)",
          perm.get("disableBypassPermissionsMode") == "disable" or u.get("permissions", {}).get("disableBypassPermissionsMode") == "disable",
          uwaga="permissions.disableBypassPermissionsMode: \"disable\"", zrodlo="cc:permissions")
    punkt("U02", "jawny tryb uprawnień przy starcie, nie bypass/auto", tryb in ("default", "dontAsk", "acceptEdits", "plan"),
          wymagany_dla=("ci", "usluga"), zalecany_dla=("stanowisko",),
          uwaga=f"tryb={tryb!r}; podaj --permission-mode (bez niego -p startuje w auto ≥2.1.285)", zrodlo="cc:permission-modes")
    punkt("U03", "tryb auto wyłączony lub świadomie skonfigurowany", u.get("disableAutoMode") == "disable" or bool(u.get("autoMode")),
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="disableAutoMode: \"disable\"", zrodlo="cc:auto-mode-config")
    szerokie = [r for r in allow if r in ("Bash", "Bash(*)", "*", "Edit", "Write") or re.fullmatch(r"Bash\((sh|bash|python3?|node|env|xargs|sudo) \*\)", r)]
    punkt("U04", "brak szerokich zgód (Bash, Bash(*), interpretery z *)", not szerokie,
          uwaga=f"szerokie reguły allow: {szerokie}", zrodlo="cc:permissions")
    sekrety = [r for r in deny if r.startswith("Read(") and (".env" in r or "secret" in r.lower() or ".ssh" in r)]
    piaskownica_odczyt = sb.get("filesystem", {}).get("denyRead") if isinstance(sb.get("filesystem"), dict) else None
    punkt("U05", "odczyt sekretów zablokowany (Read(./.env*), sekrety, klucze)", bool(sekrety) or bool(piaskownica_odczyt) or bez_plikow,
          uwaga="deny Read(./.env), Read(./.env.*), Read(./secrets/**) lub sandbox.filesystem.denyRead", zrodlo="cc:permissions")
    punkt("U06", "sudo zablokowane", any(r.startswith("Bash(sudo") for r in deny) or tryb in ("dontAsk",) and not any("sudo" in r for r in allow),
          zalecany_dla=("stanowisko", "ci", "usluga"), uwaga="deny Bash(sudo *)", zrodlo="cc:permissions")
    punkt("U07", "skipDangerousModePermissionPrompt nie jest włączony", u.get("skipDangerousModePermissionPrompt") is not True,
          uwaga="usuń skipDangerousModePermissionPrompt", zrodlo="cc:settings-reference")
    dodatkowe = perm.get("additionalDirectories") or []
    punkt("U08", "additionalDirectories bez katalogu głównego i domowego",
          not any(d in ("/", "~", "~/", "$HOME") for d in dodatkowe), uwaga=f"additionalDirectories={dodatkowe}", zrodlo="cc:permissions")
    punkt("U09", "goła reguła Edit nie udaje pokrycia Write",
          not (("Edit" in allow and "Write" not in allow) or ("Edit" in deny and "Write" not in deny)),
          zalecany_dla=("stanowisko", "ci", "usluga"), wymagany_dla=(),
          uwaga="użyj Edit(./**) lub par Edit/Write (próba 2.1.286)", zrodlo="próba wtyczki")

    # Piaskownica i sieć
    sieciowe_zakazy = {"Bash(curl *)", "Bash(wget *)"} <= set(deny)
    punkt("S01", "ograniczenie sieci (piaskownica z listą domen albo zakazy curl/wget + WebFetch)",
          bool(sb.get("enabled")) and bool(siec.get("allowedDomains") is not None) or (sieciowe_zakazy and ("WebFetch" in deny or any(r.startswith("WebFetch(domain:") for r in allow)))
          or (bez_bash and "WebFetch(domain:*)" not in allow),
          wymagany_dla=("ci", "usluga"), zalecany_dla=("stanowisko",),
          uwaga="sandbox.enabled + network.allowedDomains (reguły Bash nie są granicą sieci)", zrodlo="cc:sandboxing")
    punkt("S02", "piaskownica nie degraduje się po cichu (failIfUnavailable)", not sb.get("enabled") or sb.get("failIfUnavailable") is True,
          wymagany_dla=("ci", "usluga"), zalecany_dla=("stanowisko",), uwaga="sandbox.failIfUnavailable: true", zrodlo="cc:sandboxing")
    punkt("S03", "brak ucieczki z piaskownicy na prośbę modelu", not sb.get("enabled") or sb.get("allowUnsandboxedCommands") is False,
          wymagany_dla=("ci", "usluga"), zalecany_dla=("stanowisko",), uwaga="sandbox.allowUnsandboxedCommands: false", zrodlo="cc:sandboxing")
    punkt("S04", "poświadczenia poza zasięgiem podprocesów (SCRUB lub sandbox.credentials)",
          env.get("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "").lower() in PRAWDA or bool(sb.get("credentials")) or bez_bash,
          wymagany_dla=("usluga",), zalecany_dla=("ci",),
          uwaga="CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 (wymusza tryb default!) lub sandbox.credentials deny/mask", zrodlo="cc:env-vars")

    # Sekrety i hooki
    jawne = [k for k, v in (u.get("env") or {}).items() if cc.wygladaja_na_sekret(k) and str(v)]
    punkt("K01", "brak sekretów jawnym tekstem w env ustawień", not jawne,
          uwaga=f"zmienne wyglądające na sekret: {jawne} (wartości nie pokazano) — apiKeyHelper/otelHeadersHelper/headersHelper",
          zrodlo="cc:settings-reference#env")
    http = [h.get("url") for grupy in (u.get("hooks") or {}).values() for g in (grupy or []) for h in (g.get("hooks") or [])
            if isinstance(h, dict) and h.get("type") == "http"]
    punkt("K02", "hooki http tylko na dozwolone adresy (allowedHttpHookUrls)", not http or bool(u.get("allowedHttpHookUrls")),
          uwaga=f"hooki http: {http}", zrodlo="cc:hooks")

    # Rozszerzenia
    punkt("R01", "MCP tylko z jawnej konfiguracji (--strict-mcp-config)", "--strict-mcp-config" in flagi,
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="dodaj --strict-mcp-config", zrodlo="cc:mcp")
    punkt("R02", "brak automatycznej zgody na serwery projektu", u.get("enableAllProjectMcpServers") is not True,
          uwaga="enableAllProjectMcpServers: false", zrodlo="cc:mcp")
    punkt("R03", "izolacja od plików konfiguracji maszyny/repozytorium (--setting-sources \"\" lub --bare)",
          wartosc_flagi(flagi, "--setting-sources") == "" or "--bare" in flagi,
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="--setting-sources \"\"", zrodlo="cc:headless")
    punkt("R04", "klient nie steruje sesją poleceniami / (--disable-slash-commands)", "--disable-slash-commands" in flagi,
          wymagany_dla=("usluga",), uwaga="--disable-slash-commands", zrodlo="analiza CLI Nexusa")
    punkt("R05", "publikacja i zdalny dostęp wyłączone (artefakty, Remote Control, wiadomości między sesjami)",
          u.get("enableArtifact") is False and u.get("disableRemoteControl") is True and u.get("crossSessionInbound") == "refuse",
          wymagany_dla=("usluga",), zalecany_dla=("ci",),
          uwaga="enableArtifact: false, disableRemoteControl: true, crossSessionInbound: \"refuse\"", zrodlo="cc:settings-reference")
    punkt("R06", "konektory i synchronizacja z claude.ai wyłączone",
          u.get("disableClaudeAiConnectors") is True and u.get("syncClaudeAiSkills") is False and u.get("syncClaudeAiPlugins") is False,
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="disableClaudeAiConnectors, syncClaudeAi*: false", zrodlo="cc:settings-reference")

    # Izolacja dzierżawców i wersje
    punkt("D01", "osobny katalog konfiguracji i projektu na dzierżawcę",
          bool(env.get("CLAUDE_CONFIG_DIR")) and bool(env.get("CLAUDE_CODE_PROJECT_DIR_NAME")),
          wymagany_dla=("usluga",), uwaga="CLAUDE_CONFIG_DIR + CLAUDE_CODE_PROJECT_DIR_NAME w środowisku procesu", zrodlo="cc:sessions")
    punkt("D02", "pamięć automatyczna wyłączona", env.get("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "").lower() in PRAWDA or u.get("autoMemoryEnabled") is False,
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="CLAUDE_CODE_DISABLE_AUTO_MEMORY=1", zrodlo="cc:memory")
    punkt("D03", "przypięta wersja CLI (bez automatycznych aktualizacji)",
          env.get("DISABLE_AUTOUPDATER", "").lower() in PRAWDA or env.get("DISABLE_UPDATES", "").lower() in PRAWDA,
          wymagany_dla=("ci", "usluga"), uwaga="DISABLE_AUTOUPDATER=1 + ścieżka do konkretnej wersji", zrodlo="cc:setup")
    punkt("D04", "retencja transkryptów ustawiona", isinstance(u.get("cleanupPeriodDays"), int),
          zalecany_dla=("stanowisko", "ci", "usluga"), wymagany_dla=(), uwaga="cleanupPeriodDays (domyślnie 30)", zrodlo="cc:settings-reference")

    # Koszty i prywatność
    punkt("C01", "limit tur lub budżetu przebiegu", wartosc_flagi(flagi, "--max-turns") is not None or wartosc_flagi(flagi, "--max-budget-usd") is not None,
          wymagany_dla=("usluga",), zalecany_dla=("ci",), uwaga="--max-turns / --max-budget-usd", zrodlo="cc:headless")
    punkt("C02", "kontrola modeli (availableModels lub deny Agent(model:*)) i sufit effortu",
          (bool(u.get("availableModels")) or "Agent(model:*)" in deny) and bool(u.get("maxEffortLevel")),
          wymagany_dla=("usluga",), zalecany_dla=("ci", "stanowisko"), uwaga="availableModels / deny Agent(model:*) + maxEffortLevel", zrodlo="cc:model-config")
    tresci = [k for k in ("OTEL_LOG_USER_PROMPTS", "OTEL_LOG_ASSISTANT_RESPONSES", "OTEL_LOG_TOOL_DETAILS", "OTEL_LOG_TOOL_CONTENT",
                          "OTEL_LOG_RAW_API_BODIES") if env.get(k, "").lower() in PRAWDA]
    punkt("P01", "telemetria bez treści rozmów", not tresci, uwaga=f"włączone: {tresci}", zrodlo="cc:monitoring-usage")

    braki = [w for w in wyniki if w["stan"] == "BRAK"]
    if a.json:
        print(json.dumps({"profil": a.profil, "wyniki": wyniki, "braki": len(braki)}, ensure_ascii=False, indent=1))
    else:
        print(f"Lista kontrolna — profil {a.profil}: {sum(w['stan'] == 'OK' for w in wyniki)} OK, {len(braki)} BRAK, "
              f"{sum(w['stan'] == 'UWAGA' for w in wyniki)} UWAGA, {sum(w['stan'] == 'n/d' for w in wyniki)} n/d")
        for w in wyniki:
            if w["stan"] != "n/d":
                print(f"  [{w['stan']:<5}] {w['id']} {w['opis']}" + (f" — {w['uwaga']}" if w["uwaga"] and w["stan"] != "OK" else ""))
    if a.markdown:
        linie = [f"# Lista kontrolna bezpieczeństwa — profil `{a.profil}`", "",
                 f"Pliki: {', '.join(f'`{x}`' for x in a.ustawienia)}; flagi: `{a.flagi}`; zmienne: `{a.zmienne}`", "",
                 "| Id | Punkt | Wynik | Do zrobienia | Źródło |", "|---|---|---|---|---|"]
        linie += [f"| {w['id']} | {w['opis']} | {w['stan']} | {w['uwaga'] if w['stan'] in ('BRAK', 'UWAGA') else ''} | {w['zrodlo']} |"
                  for w in wyniki]
        a.markdown.write_text("\n".join(linie) + "\n", encoding="utf-8")
    return 1 if braki else 0


if __name__ == "__main__":
    sys.exit(main())
