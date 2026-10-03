#!/usr/bin/env python3
"""Odświeża indeksy wtyczki z dokumentacji Claude Code i pokazuje różnice.

Źródła (strony Markdown dokumentacji, `https://code.claude.com/docs/en/<strona>.md`):
  settings-reference → wspolne/indeksy/ustawienia.tsv (klucze, zasięg, typ, domyślne, min. wersja),
  env-vars           → wspolne/indeksy/zmienne.tsv (zmienne, kategoria, wersja),
  cli-reference      → wspolne/indeksy/flagi-cli.tsv (flagi, wersja, tylko -p),
  tools-reference    → wspolne/indeksy/narzedzia.tsv (narzędzia, czy wymagają zgody).
Kolumny opracowane ręcznie po polsku (ustawienia: obszar, co_robi_pl, uwaga_pl; zmienne: kategoria
nowych zmiennych wg reguł) są zachowywane z bieżących indeksów. `hooki-zdarzenia.tsv` jest
opracowany ręcznie — skrypt tylko zgłasza zdarzenia z `hooks` nieobecne w indeksie.

Użycie:
  odswiez_indeksy.py --pobierz [--katalog DIR]     pobierz strony do DIR (domyślnie $TMPDIR/docs-cc)
  odswiez_indeksy.py --katalog DIR [--zapisz]      zbuduj indeksy z pobranych stron; bez --zapisz
                                                   tylko raport różnic (nowe/usunięte/zmienione wersje)
Po zapisie: przebuduj referencje generowane (`skills/ustawienia-i-hierarchia/references/indeks-kluczy.md`,
`skills/zmienne-srodowiskowe/scripts/buduj_indeks_md.py`) i uruchom testy wtyczki.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import urllib.request
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[2]
INDEKSY = KORZEN / "wspolne" / "indeksy"
STRONY = ["settings-reference", "env-vars", "cli-reference", "tools-reference", "hooks"]
ADRES = "https://code.claude.com/docs/en/{}.md"

KATEGORIE_ZMIENNYCH = [
    ("instrukcja-i-tozsamosc", r"ATTRIBUTION_HEADER|SIMPLE_SYSTEM_PROMPT|GIT_INSTRUCTIONS|APPEND_SUBAGENT_PROMPT"),
    ("uprawnienia-i-tryby", r"AUTO_MODE|DANGEROUS_RM|SUBSTITUTION_RM|PERMISSION_PROMPT|USER_DIALOG_TIMEOUT|CFC_PROMPT"),
    ("hooki", r"HOOK"),
    ("ustawienia-i-zarzadzanie", r"ADMIN_ENV_UNION|MANAGED_SETTINGS|POLICY_HELPER"),
    ("telemetria-i-prywatnosc", r"^(OTEL_|BETA_TRACING|ENABLE_BETA_TRACING)|TELEMETRY|ERROR_REPORTING|NONESSENTIAL|GROWTHBOOK|DO_NOT_TRACK|FEEDBACK|SURVEY|_TRACEPARENT|COST_WARNINGS"),
    ("uwierzytelnianie-i-dostawcy", r"^ANTHROPIC_(API_KEY|AUTH_TOKEN|AWS|BEDROCK|VERTEX|FOUNDRY|BASE_URL|WORKSPACE|CUSTOM_HEADERS|BETAS|FEDERATION|ORGANIZATION|PROFILE)|^AWS_|^VERTEX_REGION|_USE_(BEDROCK|VERTEX|FOUNDRY|MANTLE|ANTHROPIC_AWS)|SKIP_.*AUTH|AUTH_REFRESH|OAUTH|API_KEY_HELPER|GATEWAY|LOGIN|LOGOUT"),
    ("cache-promptu", r"PROMPT_CACHING|CACHE_TTL"),
    ("model-effort-i-myslenie", r"MODEL|EFFORT|THINKING|FAST_MODE|ADVISOR|1M_CONTEXT|EXTRA_BODY|EXPERIMENTAL_BETAS"),
    ("mcp", r"MCP"),
    ("podagenci-zespoly-i-zadania-w-tle", r"SUBAGENT|AGENT_SDK_DISABLE_BUILTIN|EXPLORE_PLAN|AGENT_TEAMS|TEAM|WORKFLOW|BACKGROUND|_BG_|FORK|TASK|ASYNC_AGENT|AGENT_VIEW|CRON|CHILD_SESSION|AFK|MESSAGING_|CLAUDE_JOB_DIR"),
    ("skille-wtyczki-i-polecenia", r"SKILL|PLUGIN|MARKETPLACE|_COMMAND$|SLASH|ADOPT"),
    ("pamiec-i-claude-md", r"MEMORY|CLAUDE_MDS|ADDITIONAL_DIRECTORIES"),
    ("kontekst-kompakcja-i-wyjscie", r"COMPACT|MAX_OUTPUT|CONTEXT_TOKENS|FILE_READ_MAX|STRUCTURED_OUTPUT|ATTACHMENTS"),
    ("narzedzia-wbudowane", r"^BASH_|GLOB|WEBFETCH|WEB_FETCH|WEB_SEARCH|TOOL|POWERSHELL|RIPGREP|SHELL|NATIVE_FILE_SEARCH|CHECKPOINT|ARTIFACT|GIT_BASH|PERFORCE|SCRIPT_CAPS"),
    ("sesje-headless-i-osadzanie", r"RESUME|SESSION|PRINT_|EXIT_AFTER|PROMPT_HISTORY|STARTUP_FAILURE|PROJECT_DIR|CONFIG_DIR|TMPDIR|SIMPLE|CLAUDECODE|CLAUDE_PID|CLAUDE_ENV_FILE|PROMPT_SUGGESTION|MAX_TURNS|REMOTE|BRIDGE|CCR_|IS_DEMO|AWAY_SUMMARY|GOAL_|NONBLOCKING_STDOUT"),
    ("siec-proxy-i-niezawodnosc", r"PROXY|CERT|CLIENT_KEY|API_TIMEOUT|RETR|STREAM|WATCHDOG|IDLE_TIMEOUT|NONSTREAMING|CONNECT"),
    ("bezpieczenstwo-i-izolacja", r"SUBPROCESS_ENV_SCRUB|RESTRICTED|SAFE_MODE|SANDBOX|PROCESS_WRAPPER"),
    ("aktualizacje-i-instalacja", r"UPDATE|INSTALL|UPGRADE"),
    ("diagnostyka-i-logi", r"DEBUG|DIAG"),
    ("interfejs-terminala-i-ide", r"."),
]


def czysc(tekst: str) -> str:
    return re.sub(r"\]\([^)]*\)", "]", tekst).replace("[", "").replace("]", "").replace("<br />", " ").strip()


def normalizuj_zasieg(tekst: str) -> str:
    """Sprowadza opis zasięgu do kategorii używanych przez walidator (cc_wspolne.ZASIEGI_*)."""
    z = tekst.split(".")[0].replace("`", "").strip()
    if z.startswith("Any file"):
        return "Any file"
    if z.startswith("Managed, from the device"):
        return "Managed (tylko z urządzenia)"
    if z.startswith("Managed"):
        return "Managed"
    if z.startswith("User, local, or managed, and files passed with --settings"):
        return "User, local, managed or --settings"
    return z


def tsv(sciezka: Path) -> list[dict]:
    if not sciezka.exists():
        return []
    with sciezka.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def zapisz(sciezka: Path, wiersze: list[dict]) -> None:
    with sciezka.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(wiersze[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in wiersze:
            w.writerow({k: str(v).replace("\t", " ").replace("\n", " ") for k, v in r.items()})


def pobierz(katalog: Path) -> None:
    katalog.mkdir(parents=True, exist_ok=True)
    for strona in STRONY:
        zadanie = urllib.request.Request(ADRES.format(strona), headers={"User-Agent": "curl/8 (danaco-konfiguracja)"})
        with urllib.request.urlopen(zadanie, timeout=60) as odp:  # noqa: S310 — stały adres dokumentacji
            (katalog / f"{strona}.md").write_bytes(odp.read())
        print(f"pobrano {strona}.md")


def ustawienia(tekst: str, stare: dict[str, dict]) -> list[dict]:
    wiersze, kategoria = [], ""
    linie = tekst.splitlines()
    i = 0
    while i < len(linie):
        m2 = re.match(r"^## (.*)", linie[i])
        if m2:
            kategoria = m2.group(1).strip()
        m = re.match(r"^### `([^`]+)`\s*$", linie[i])
        if not m:
            i += 1
            continue
        klucz, cialo, j = m.group(1), [], i + 1
        while j < len(linie) and not re.match(r"^##(#)? ", linie[j]):
            cialo.append(linie[j])
            j += 1
        tresc = "\n".join(cialo)
        akapit = []
        for w in cialo:
            if not w.strip():
                if akapit:
                    break
                continue
            if w.startswith(("*", "```", "<")):
                if akapit:
                    break
                continue
            akapit.append(w.strip())
        pierwszy = " ".join(akapit)

        def pole(nazwa: str) -> str:
            mm = re.search(r"^\* \*\*" + re.escape(nazwa) + r"\*\*: (.*)$", tresc, re.M)
            return czysc(mm.group(1)) if mm else ""
        wersja = (re.search(r"[Rr]equires Claude Code v(\d+\.\d+\.\d+)", pierwszy)
                  or re.search(r"^\* \*\*Scope\*\*.*?[Rr]equires Claude Code v(\d+\.\d+\.\d+)", tresc, re.M))
        usuniety = re.search(r"[Rr]emoved in (?:Claude Code )?v(\d+\.\d+\.\d+)", tresc)
        s = stare.get(klucz, {})
        wiersze.append({
            "klucz": klucz, "kategoria": kategoria, "zasieg": normalizuj_zasieg(pole("Scope")),
            "min_wersja": wersja.group(1) if wersja else "",
            "wersje_w_opisie": " ".join(sorted(set(re.findall(r"v(\d+\.\d+\.\d+)", tresc)),
                                               key=lambda v: tuple(map(int, v.split("."))))),
            "usuniety_w": usuniety.group(1) if usuniety else "", "typ": pole("Type")[:300],
            "domyslnie": pole("Default")[:300], "nadpisania": pole("Per-session overrides")[:400],
            "obszar": s.get("obszar", ""), "co_robi_pl": s.get("co_robi_pl", ""), "uwaga_pl": s.get("uwaga_pl", ""),
            "opis_en": czysc(pierwszy)[:600],
            "zrodlo": "https://code.claude.com/docs/en/settings-reference#" + klucz.lower().replace(".", "-"),
        })
        i = j
    return wiersze


def zmienne(tekst: str, stare: dict[str, dict]) -> list[dict]:
    sekcja = tekst.split("## Variables", 1)[1].split("## Features that need", 1)[0]
    wiersze = []
    for w in sekcja.splitlines():
        m = re.match(r"^\| `([A-Z0-9_]+)`(?:, `[A-Z0-9_]+`)* +\| (.*) \|\s*$", w)
        if not m:
            continue
        nazwa, opis = m.group(1), czysc(m.group(2))
        wersje = re.findall(r"v(\d+\.\d+\.\d+)", opis)
        kat = stare.get(nazwa, {}).get("kategoria") or next(k for k, rx in KATEGORIE_ZMIENNYCH if re.search(rx, nazwa))
        wiersze.append({"zmienna": nazwa, "kategoria": kat, "wersja_w_opisie": wersje[0] if wersje else "", "opis_en": opis})
    return wiersze


def flagi(tekst: str) -> list[dict]:
    sekcja = tekst.split("## CLI flags", 1)[1].split("### System prompt flags", 1)[0]
    wiersze = []
    for w in sekcja.splitlines():
        m = re.match(r"^\| (`--?[^|]+`(?:, `[^`]+`)*) +\| (.*) \| (.*) \|\s*$", w)
        if not m:
            continue
        nazwy, opis = re.findall(r"`([^`]+)`", m.group(1)), czysc(m.group(2))
        wersje = re.findall(r"v(\d+\.\d+\.\d+)", opis)
        tylko_p = "tak" if re.search(r"print mode only|Only applies in non-interactive|Requires `--print`|With `--print`|requires `-p`|\(print mode", opis, re.I) else ""
        wiersze.append({"flaga": ", ".join(nazwy), "wersja_w_opisie": wersje[0] if wersje else "", "tylko_p": tylko_p, "opis_en": opis})
    return wiersze


def narzedzia(tekst: str) -> list[dict]:
    wiersze = []
    for w in tekst.splitlines():
        m = re.match(r"^\| `([A-Za-z]+)` +\| (.*) \| (Yes|No) \|\s*$", w)
        if m:
            wiersze.append({"narzedzie": m.group(1), "wymaga_zgody": "tak" if m.group(3) == "Yes" else "nie",
                            "opis_en": czysc(m.group(2))[:400]})
    return wiersze


def roznice(nazwa: str, klucz: str, stare: list[dict], nowe: list[dict], pole_wersji: str) -> None:
    s, n = {r[klucz]: r for r in stare}, {r[klucz]: r for r in nowe}
    dodane, usuniete = sorted(set(n) - set(s)), sorted(set(s) - set(n))
    zmienione = sorted(k for k in set(s) & set(n) if s[k].get(pole_wersji, "") != n[k].get(pole_wersji, ""))
    print(f"== {nazwa}: było {len(s)}, jest {len(n)}; nowe {len(dodane)}, usunięte {len(usuniete)}, zmiana wersji {len(zmienione)}")
    for etykieta, lista in (("nowe", dodane), ("usunięte", usuniete), ("wersja", zmienione)):
        if lista:
            print(f"   {etykieta}: {', '.join(lista[:25])}{' …' if len(lista) > 25 else ''}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pobierz", action="store_true")
    p.add_argument("--katalog", type=Path, default=Path(os.environ.get("TMPDIR", "/tmp")) / "docs-cc")
    p.add_argument("--zapisz", action="store_true")
    a = p.parse_args()
    if a.pobierz:
        pobierz(a.katalog)
    strona = lambda n: (a.katalog / f"{n}.md").read_text(encoding="utf-8")  # noqa: E731
    stare_u, stare_z = tsv(INDEKSY / "ustawienia.tsv"), tsv(INDEKSY / "zmienne.tsv")
    stare_f, stare_n = tsv(INDEKSY / "flagi-cli.tsv"), tsv(INDEKSY / "narzedzia.tsv")
    nowe_u = ustawienia(strona("settings-reference"), {r["klucz"]: r for r in stare_u})
    nowe_z = zmienne(strona("env-vars"), {r["zmienna"]: r for r in stare_z})
    nowe_f, nowe_n = flagi(strona("cli-reference")), narzedzia(strona("tools-reference"))
    roznice("ustawienia", "klucz", stare_u, nowe_u, "min_wersja")
    roznice("zmienne", "zmienna", stare_z, nowe_z, "wersja_w_opisie")
    roznice("flagi", "flaga", stare_f, nowe_f, "wersja_w_opisie")
    roznice("narzędzia", "narzedzie", stare_n, nowe_n, "wymaga_zgody")
    znane = {r["zdarzenie"] for r in tsv(INDEKSY / "hooki-zdarzenia.tsv")}
    zdarzenia = set(re.findall(r"^### (\w+)\s*$", strona("hooks"), re.M)) & set(re.findall(r"`(\w+)`", strona("hooks")))
    brak = sorted(z for z in zdarzenia if z[0].isupper() and z not in znane and re.match(r"^(Pre|Post|Session|User|Stop|Subagent|Notification|Permission|Config|Instructions|Setup|Task|Teammate|Worktree|Elicitation|File|Cwd|Compact|Model|Tool)", z))
    if brak:
        print(f"== hooki: zdarzenia spoza indeksu (dopisz ręcznie): {', '.join(brak)}")
    if not nowe_u or not nowe_z or not nowe_f:
        print("BŁĄD: parser nie znalazł danych — struktura strony mogła się zmienić; indeksy nie zostaną zapisane")
        return 1
    if a.zapisz:
        zapisz(INDEKSY / "ustawienia.tsv", nowe_u)
        zapisz(INDEKSY / "zmienne.tsv", nowe_z)
        zapisz(INDEKSY / "flagi-cli.tsv", nowe_f)
        if nowe_n:
            zapisz(INDEKSY / "narzedzia.tsv", nowe_n)
        print("Zapisano indeksy. Nowe klucze nie mają opisu PL (co_robi_pl, uwaga_pl) — uzupełnij ręcznie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
