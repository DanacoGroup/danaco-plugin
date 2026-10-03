#!/usr/bin/env python3
"""Składa i sprawdza politykę zarządzaną tak, jak zrobi to Claude Code — przed wdrożeniem na flotę.

Wejście:
  --glowny PLIK         treść przyszłego pliku zarządzanego głównego (dowolna nazwa pliku roboczego),
  --dodatki PLIK…       przyszłe pliki katalogu drop-in (scalane alfabetycznie po nazwie),
  --zdalne PLIK         ładunek ustawień serwerowych (konsola claude.ai) — do symulacji pierwszeństwa,
  --wersja X.Y.Z        wersja CLI floty (klucze wymagające nowszej wersji → ostrzeżenie),
  --cli BINARKA         dodatkowo `claude doctor` na wyniku scalenia (przez waliduj_ustawienia.py),
  --wyjscie PLIK        zapisz scaloną politykę plików.

Zasady scalania plików (cc:managed-settings „Split a file-based policy across teams”):
skalar — późniejszy zastępuje; lista — suma bez duplikatów; obiekt (env, sandbox…) — scalanie
po kluczu; `fallbackModel`, `modelPicker` — w całości; `extraKnownMarketplaces`,
`managedMcpServers` — wpis o tej samej nazwie w całości.

Przy --zdalne: domyślne `first-wins` — wybrane jest źródło zdalne, z plików liczą się tylko
klucze czytane ze wszystkich źródeł administracyjnych (blokady piaskownicy,
allowManagedMcpServersOnly, deniedMcpServers, env per zmienna…); skrypt wypisuje klucze plików,
które zostaną POMINIĘTE.

Wykrywa też ryzyka „fail closed”: niepoprawny JSON (CLI odmówi startu), wartości logiczne
w cudzysłowie, puste listy dozwolonych (allowedProviders [] = CLI nie wystartuje), flagi
odrzucane przez disableSideloadFlags, klucze wymagające nowszej wersji.
Kod wyjścia: 1 przy błędach.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402

W_CALOSCI = {"fallbackModel", "modelPicker"}
PO_NAZWIE = {"extraKnownMarketplaces", "managedMcpServers"}
# cc:managed-settings „Keys read from every admin source” (stan 01.10.2026)
ZE_WSZYSTKICH = {"allowAllClaudeAiMcps", "allowManagedMcpServersOnly", "deniedMcpServers", "disableClaudeAiConnectors",
                 "useAutoModeDuringPlan", "syncClaudeAiSkills", "syncClaudeAiPlugins", "enableArtifact",
                 "maxEffortLevel", "attribution", "includeCoAuthoredBy", "forceRemoteSettingsRefresh", "env",
                 "allowedProviders"}
ZE_WSZYSTKICH_SANDBOX = {"network.allowManagedDomainsOnly", "filesystem.allowManagedReadPathsOnly", "bwrapPath",
                         "socatPath", "ripgrep", "filesystem.disabled", "network.strictAllowlist"}
LOGOWANIE_BRAMY = {"forceLoginGatewayUrl", "gatewayInternalNetworks"}
PUSTE_BLOKUJA = {"allowedProviders": "CLI odmówi każdego dostawcy i nie wystartuje",
                 "availableModels": "dostępny tylko model Default",
                 "strictKnownMarketplaces": "żaden marketplace nie zostanie dopuszczony",
                 "allowedMcpServers": "żaden serwer MCP użytkownika nie zostanie dopuszczony"}
STERUJACE = {"managedSourcesBehavior", "wslInheritsWindowsSettings"}


def scal(a, b, klucz: str = ""):
    if klucz in W_CALOSCI:
        return b
    if klucz in PO_NAZWIE and isinstance(a, dict) and isinstance(b, dict):
        return {**a, **b}
    if isinstance(a, dict) and isinstance(b, dict):
        wynik = dict(a)
        for k, v in b.items():
            wynik[k] = scal(a[k], v, k) if k in a else v
        return wynik
    if isinstance(a, list) and isinstance(b, list):
        wynik = list(a)
        for x in b:
            if x not in wynik:
                wynik.append(x)
        return wynik
    return b


def plaskie(obiekt, przedrostek=""):
    for k, v in (obiekt or {}).items():
        sciezka = f"{przedrostek}.{k}" if przedrostek else k
        if isinstance(v, dict):
            yield from plaskie(v, sciezka)
        else:
            yield sciezka, v


def czytaj(sciezka: Path, bledy: list[str]) -> dict | None:
    try:
        dane = cc.czytaj_json(sciezka)
    except cc.BladJson as blad:
        bledy.append(f"{sciezka.name}: niepoprawny JSON — CLI ODMÓWI STARTU na każdej maszynie ({blad})")
        return None
    if not isinstance(dane, dict):
        bledy.append(f"{sciezka.name}: najwyższy poziom nie jest obiektem — CLI odmówi startu")
        return None
    return dane


def ryzyka(dane: dict, wersja, ostrz: list[str], bledy: list[str]) -> None:
    for sciezka, wartosc in plaskie(dane):
        if wartosc in ("true", "false") and not sciezka.startswith("env."):
            ostrz.append(f"{sciezka}: wartość logiczna w cudzysłowie — CLI przyjmie, ale /status poprosi o poprawkę")
    for k, skutek in PUSTE_BLOKUJA.items():
        if dane.get(k) == []:
            (bledy if k == "allowedProviders" else ostrz).append(f"{k}: pusta lista — {skutek}")
    if dane.get("forceRemoteSettingsRefresh") is True:
        ostrz.append("forceRemoteSettingsRefresh: bez dostępu do api.anthropic.com CLI nie wystartuje (poza `claude auth`)")
    if dane.get("allowManagedPermissionRulesOnly") is True and not (dane.get("permissions") or {}).get("allow"):
        ostrz.append("allowManagedPermissionRulesOnly bez permissions.allow — reguły allow użytkowników, projektów, "
                     "--allowedTools i hostów (np. Cowork) przestaną działać")
    if dane.get("disableSideloadFlags") is True:
        ostrz.append("disableSideloadFlags: odrzuci --plugin-dir, --plugin-url, --agents, --mcp-config — usługi "
                     "osadzające CLI z tymi flagami przestaną startować na tej maszynie")
    if dane.get("strictPluginOnlyCustomization"):
        ostrz.append("strictPluginOnlyCustomization: skille/agenci/hooki/MCP tylko z wtyczek i zarządzanych — "
                     "konfiguracje użytkowników i projektów przestaną działać")
    klucze = cc.klucze_ustawien()
    for k in dane:
        w = klucze.get(k)
        if w and wersja and w.get("min_wersja") and cc.wersja(w["min_wersja"]) > wersja:
            ostrz.append(f"{k}: wymaga ≥{w['min_wersja']}, flota ma {'.'.join(map(str, wersja))} — klucz zostanie "
                         f"zignorowany (dodaj requiredMinimumVersion)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--glowny", type=Path)
    p.add_argument("--dodatki", type=Path, nargs="*", default=[])
    p.add_argument("--zdalne", type=Path)
    p.add_argument("--wersja", default="")
    p.add_argument("--cli", default="")
    p.add_argument("--wyjscie", type=Path)
    a = p.parse_args()
    if not a.glowny and not a.dodatki and not a.zdalne:
        p.error("podaj --glowny, --dodatki lub --zdalne")
    wersja = cc.wersja(a.wersja) if a.wersja else None
    bledy: list[str] = []
    ostrz: list[str] = []
    uwagi: list[str] = []

    pliki = ([a.glowny] if a.glowny else []) + sorted(a.dodatki, key=lambda x: x.name)
    polityka: dict = {}
    for plik in pliki:
        dane = czytaj(plik, bledy)
        if dane is None:
            continue
        for k in dane:
            if k in polityka and not isinstance(dane[k], (dict, list)) and polityka[k] != dane[k]:
                uwagi.append(f"{plik.name}: „{k}” zastępuje wcześniejszą wartość {polityka[k]!r} → {dane[k]!r}")
        polityka = scal(polityka, dane)
    if pliki:
        print(f"== Polityka plików ({', '.join(x.name for x in pliki)}): {len(polityka)} kluczy")
        ryzyka(polityka, wersja, ostrz, bledy)
        if polityka and set(polityka) <= STERUJACE:
            ostrz.append("pliki zawierają tylko klucze sterujące — źródło nie liczy się jako polityka (CLI przejdzie dalej)")

    if a.zdalne:
        zdalne = czytaj(a.zdalne, bledy) or {}
        print(f"== Ładunek serwerowy {a.zdalne.name}: {len(zdalne)} kluczy")
        ryzyka(zdalne, wersja, ostrz, bledy)
        tryb = zdalne.get("managedSourcesBehavior", "first-wins")
        if pliki and zdalne:
            if tryb == "first-wins":
                pominiete = []
                for k in polityka:
                    if k in ZE_WSZYSTKICH or k in LOGOWANIE_BRAMY or k in STERUJACE or k == "$schema":
                        continue
                    if k == "sandbox":
                        sb = polityka["sandbox"] or {}
                        sumowane = set()
                        if (sb.get("network") or {}).get("allowManagedDomainsOnly") is True:
                            sumowane.add("network.allowedDomains")  # blokada włączona → lista sumowana ze wszystkich źródeł
                        if (sb.get("filesystem") or {}).get("allowManagedReadPathsOnly") is True:
                            sumowane.add("filesystem.allowRead")
                        pominiete += [f"sandbox.{s}" for s, _ in plaskie(sb)
                                      if s not in ZE_WSZYSTKICH_SANDBOX and s not in sumowane]
                        continue
                    pominiete.append(k)
                if {"forceLoginMethod", "forceLoginOrgUUID"} & set(pominiete):
                    ostrz.append("forceLoginMethod/forceLoginOrgUUID: utrzymuj je W OBU miejscach (plik i konsola) — "
                                 "ustawienia serwerowe nie przekierują pierwszego logowania")
                if pominiete:
                    ostrz.append("first-wins: wybrane będą ustawienia serwerowe, z plików POMINIĘTE zostaną: "
                                 + ", ".join(sorted(pominiete)))
                env_plikow = set(polityka.get("env") or {}) - set(zdalne.get("env") or {})
                if env_plikow:
                    uwagi.append(f"env scalany per zmienna (≥2.1.223): z plików dojdą {sorted(env_plikow)}")
            else:
                uwagi.append("managedSourcesBehavior=merge: listy sumowane, blokady najsurowsze, listy dozwolonych "
                             "z najwyższego źródła (≥2.1.242)")
        uwagi.append("ustawienia serwerowe nie dotrą do sesji z CLAUDE_CODE_USE_* lub własnym ANTHROPIC_BASE_URL, "
                     "ani przy kluczu z apiKeyHelper / WIF")

    if a.wyjscie and pliki:
        a.wyjscie.write_text(json.dumps(polityka, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Zapisano scaloną politykę: {a.wyjscie}")

    for etykieta, lista in (("BŁĄD", bledy), ("OSTRZ", ostrz), ("uwaga", uwagi)):
        for t in lista:
            print(f"  {etykieta} {t}")

    if pliki and polityka:
        with tempfile.NamedTemporaryFile("w", suffix=".polityka.json", delete=False) as f:
            json.dump(polityka, f)
        polecenie = [sys.executable, str(KORZEN / "scripts" / "waliduj_ustawienia.py"), f.name, "--rodzaj", "managed"]
        if a.wersja:
            polecenie += ["--wersja", a.wersja]
        if a.cli:
            polecenie += ["--cli", a.cli]
        wynik = subprocess.run(polecenie, capture_output=True, text=True)
        print("== Walidacja scalonej polityki (waliduj_ustawienia.py --rodzaj managed)")
        print("\n".join("  " + w for w in wynik.stdout.strip().splitlines()[1:]) or "  OK")
        Path(f.name).unlink(missing_ok=True)
        if wynik.returncode:
            bledy.append("walidacja scalonej polityki zgłosiła błędy")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
