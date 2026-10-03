#!/usr/bin/env python3
"""Walidator pliku ustawień Claude Code: ścisły JSON, schemat schemastore i reguły dokumentacji.

Trzy warstwy sprawdzeń:
  1. JSON w trybie ścisłym (komentarz i przecinek końcowy to błąd, jak w Claude Code).
  2. Schemat `https://json.schemastore.org/claude-code-settings.json` (kopia w
     `scripts/schematy/`, odświeżana opcją --odswiez-schemat). Schemat bywa starszy niż
     dokumentacja: klucz albo zdarzenie hooka znane dokumentacji, a nieznane schematowi,
     jest raportowane jako ostrzeżenie „schemat nieaktualny”, nie jako błąd.
  3. Reguły z dokumentacji (indeks 243 kluczy settings-reference): nieznane klucze
     (literówki), zasięg klucza względem rodzaju pliku, minimalne wersje CLI, klucze
     przestarzałe, składnia reguł uprawnień, hooki (zdarzenia, matcher, `if`, `mcp_tool`),
     blok `env` (zmienne ignorowane w projekcie, sekrety wpisane w plik), piaskownica.

Użycie:
  waliduj_ustawienia.py PLIK [PLIK…] [--rodzaj user|project|local|managed|flaga]
                        [--wersja 2.1.286] [--cli ŚCIEŻKA] [--scisle] [--json] [--odswiez-schemat]

  --cli dokłada czwartą warstwę: `claude doctor` w odizolowanym profilu, czyli walidację
  własnym schematem binarki (sekcja „Invalid settings”). To najpewniejsza próba bez modelu.

Rodzaj pliku (domyślnie zgadywany z nazwy): `user` = ~/.claude/settings.json,
`project` = .claude/settings.json, `local` = .claude/settings.local.json,
`managed` = managed-settings.json lub managed-settings.d/*.json, `flaga` = plik dla
`--settings`. Kod wyjścia: 0 bez błędów, 1 są błędy (z --scisle także ostrzeżenia), 2 użycie.
Wartości zmiennych i sekretów nigdy nie są wypisywane.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_wspolne as cc  # noqa: E402

URL_SCHEMATU = "https://json.schemastore.org/claude-code-settings.json"

# settings-reference, „Variables Claude Code ignores in env” (stan 01.10.2026)
ZMIENNE_IGNOROWANE_ZAWSZE = {"CLAUDE_CODE_REMOTE", "CLAUDE_CODE_ACCOUNT_UUID", "CLAUDE_CODE_MESSAGING_SOCKET",
                             "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_PROJECT_DIR_NAME", "CLAUDE_CODE_RESTRICTED",
                             "CLAUDE_CODE_DISABLE_POWERSHELL_CMD_RM_DENY", "CLAUDE_CODE_DISABLE_DANGEROUS_RM_TIMEOUT",
                             "CLAUDE_CODE_DISABLE_SUBSTITUTION_RM_PROMPT"}
ZMIENNE_IGNOROWANE_W_PROJEKCIE = {"CLAUDE_CONFIG_DIR", "CLAUDE_CODE_TMPDIR", "HOME", "TMPDIR", "TMP", "TEMP",
                                  "OTEL_LOG_RAW_API_BODIES", "ENABLE_BETA_TRACING_DETAILED", "BETA_TRACING_ENDPOINT",
                                  "CLAUDE_CODE_ENABLE_TELEMETRY", "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA",
                                  "ENABLE_ENHANCED_TELEMETRY_BETA", "CLAUDE_CODE_PROCESS_WRAPPER",
                                  "CLAUDE_CODE_SYNC_SKILLS", "CLAUDE_CODE_SYNC_PLUGINS", "CLAUDE_CODE_PLUGIN_CACHE_DIR",
                                  "CLAUDE_CODE_PLUGIN_SEED_DIR"}
OTEL_PREFIKSY = ("OTEL_EXPORTER_", "OTEL_LOG_", "OTEL_LOGS_EXPORTER", "OTEL_METRICS_EXPORTER", "OTEL_TRACES_EXPORTER",
                 "XDG_")
PRZESTARZALE = {
    "includeCoAuthoredBy": "użyj `attribution` (≥2.1.281 przyjmuje także `attribution: false`)",
    "disableArtifact": "użyj `enableArtifact: false`",
    "taskOutputMaxChars": "klucz usunięty w 2.1.277",
    "permissionExplainerEnabled": "klucz usunięty w 2.1.257",
    "teammateDefaultModel": "klucz usunięty w 2.1.234",
    "keybindingFlavor": "klucz bez skutku",
    "voiceEnabled": "starsza forma klucza `voice`",
}
GLOWNE_POLA_NARZEDZI = {"Bash": "command", "PowerShell": "command", "Read": "file_path", "Edit": "file_path",
                        "Write": "file_path", "Grep": "path", "Glob": "path", "NotebookEdit": "notebook_path",
                        "WebFetch": "url"}
ZDARZENIA_NARZEDZIOWE = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"}
ZDARZENIA_BEZ_MATCHERA = {"UserPromptSubmit", "PostToolBatch", "Stop", "TeammateIdle", "TaskCreated", "TaskCompleted",
                          "WorktreeCreate", "WorktreeRemove", "MessageDisplay", "CwdChanged"}
TYPY_HOOKOW = {"command", "http", "mcp_tool", "prompt", "agent"}
# Rozbieżności typu, w których schemastore jest starszy niż dokumentacja (ścieżka → wyjaśnienie).
SCHEMAT_ZALEGLY = {
    r"^/attribution$": "dokumentacja dopuszcza `attribution: false` od 2.1.281 (schemat zna tylko obiekt)",
    r"^/sandbox/credentials/(envVars|files)/\d+/(mode|injectHosts|extract|onExtractNoMatch|decode|maskClaims|maskDuplicates)$":
        "tryb `mask` i jego pola są w dokumentacji od 2.1.199–2.1.224 (schemat zna tylko `deny`)",
    r"^/managedMcpServers$": "dokumentacja: obiekt kluczowany nazwą serwera (≥2.1.259); schemat oczekuje tablicy",
    r"^/deniedMcpServers/\d+(/serverName)?$":
        "dokumentacja: `serverName` w deniedMcpServers przyjmuje dowolny niepusty napis (np. nazwy konektorów claude.ai)",
}


class Raport:
    def __init__(self, plik: str):
        self.plik = plik
        self.bledy: list[str] = []
        self.ostrzezenia: list[str] = []
        self.uwagi: list[str] = []
        self.silnik = ""

    def blad(self, tekst: str) -> None:
        self.bledy.append(tekst)

    def ostrzez(self, tekst: str) -> None:
        self.ostrzezenia.append(tekst)

    def uwaga(self, tekst: str) -> None:
        self.uwagi.append(tekst)


def zgadnij_rodzaj(sciezka: Path) -> str:
    nazwa = sciezka.name
    if "managed" in nazwa or sciezka.parent.name == "managed-settings.d":
        return "managed"
    if nazwa == "settings.local.json":
        return "local"
    if nazwa == "settings.json" and sciezka.parent.name == ".claude":
        return "user" if sciezka.parent.parent == Path.home() else "project"
    return "flaga"


def odswiez_schemat() -> None:
    with urllib.request.urlopen(URL_SCHEMATU, timeout=30) as odpowiedz:  # noqa: S310 — stały adres https
        dane = json.loads(odpowiedz.read())
    cc.SCHEMAT.write_text(json.dumps(dane, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Schemat odświeżony: {cc.SCHEMAT}")


def sprawdz_schemat(dokument: dict, raport: Raport) -> None:
    schemat = json.loads(cc.SCHEMAT.read_text(encoding="utf-8"))
    silnik, bledy = cc.bledy_schematu(dokument, schemat)
    raport.silnik = silnik
    znane_zdarzenia = set(cc.zdarzenia_hookow())
    for sciezka, opis in bledy:
        czesci = [c for c in sciezka.split("/") if c]
        if opis.startswith("Additional properties are not allowed"):  # silnik jsonschema: nazwy w treści
            import re
            nazwy = re.findall(r"'([^']+)'", opis.split("(", 1)[-1])
            if czesci == ["hooks"] and nazwy and all(n in znane_zdarzenia for n in nazwy):
                raport.ostrzez(f"schemat nieaktualny: zdarzenia hooków {', '.join(nazwy)} są w dokumentacji, "
                               f"a schemastore ich nie zna (walidacja schematem w edytorze pokaże błąd)")
                continue
            pelne = [".".join(czesci + [n]) for n in nazwy]
            if nazwy and all(p in cc.klucze_ustawien() for p in pelne):
                raport.ostrzez(f"schemat nieaktualny: {', '.join(pelne)} są w dokumentacji, schemastore ich nie zna")
                continue
        if len(czesci) == 2 and czesci[0] == "hooks" and czesci[1] in znane_zdarzenia:
            raport.ostrzez(f"schemat nieaktualny: zdarzenie hooka {czesci[1]} jest w dokumentacji, "
                           f"a schemastore go nie zna (walidacja schematem w edytorze pokaże błąd)")
            continue
        if "additionalProperties" in opis and czesci and ".".join(czesci) in cc.klucze_ustawien():
            raport.ostrzez(f"schemat nieaktualny: {'.'.join(czesci)} jest w dokumentacji, schemastore go nie zna")
            continue
        import re
        zalegly = next((opis_z for wzor, opis_z in SCHEMAT_ZALEGLY.items() if re.match(wzor, sciezka)), None)
        if zalegly:
            raport.ostrzez(f"schemat nieaktualny: {sciezka}: {zalegly}")
            continue
        raport.blad(f"schemat: {sciezka}: {opis}")


def sprawdz_klucze(dokument: dict, rodzaj: str, wersja_cli: str, raport: Raport) -> None:
    indeks = cc.klucze_ustawien()
    schemat_top = set(json.loads(cc.SCHEMAT.read_text(encoding="utf-8")).get("properties", {}))
    znane = {k.split(".")[0] for k in indeks} | schemat_top

    def odwiedz(prefiks: str, wartosc: object) -> None:
        if not isinstance(wartosc, dict):
            return
        for klucz, pod in wartosc.items():
            pelny = f"{prefiks}.{klucz}" if prefiks else klucz
            wpis = indeks.get(pelny)
            if wpis:
                ocen_wpis(pelny, wpis, pod)
            if pelny in ("env", "hooks", "enabledPlugins", "extraKnownMarketplaces", "modelSettings",
                         "skillOverrides", "pluginConfigs", "modelOverrides", "autoMode", "statusLine"):
                continue
            if isinstance(pod, dict) and any(k.startswith(pelny + ".") for k in indeks):
                odwiedz(pelny, pod)

    def ocen_wpis(pelny: str, wpis: dict, wartosc: object) -> None:
        zasieg = wpis["zasieg"]
        if zasieg in cc.ZASIEGI_TYLKO_ZARZADZANE and rodzaj != "managed":
            raport.blad(f"{pelny}: klucz działa tylko w ustawieniach zarządzanych (zasięg {zasieg}); "
                        f"w pliku rodzaju „{rodzaj}” zostanie zignorowany")
        elif zasieg == "Global config":
            raport.blad(f"{pelny}: klucz globalnej konfiguracji — należy do ~/.claude.json, nie do settings.json")
        elif zasieg in cc.ZASIEGI_BEZ_PROJEKTU and rodzaj in ("project", "local"):
            raport.ostrzez(f"{pelny}: zasięg „{zasieg}” — z pliku projektu klucz jest ignorowany")
        elif zasieg in cc.ZASIEGI_BEZ_WSPOLNEGO_PROJEKTU and rodzaj == "project":
            raport.ostrzez(f"{pelny}: zasięg „{zasieg}” — ze wspólnego .claude/settings.json klucz jest ignorowany")
        elif zasieg == "User, local, or managed" and rodzaj == "flaga":
            raport.ostrzez(f"{pelny}: zasięg „{zasieg}” — sprawdź, czy klucz przyjmuje --settings")
        if wpis["min_wersja"] and wersja_cli and cc.wersja_mniejsza(wersja_cli, wpis["min_wersja"]):
            raport.ostrzez(f"{pelny}: opis klucza wymienia wymóg v{wpis['min_wersja']} (cel: v{wersja_cli})")
        if pelny in PRZESTARZALE:
            raport.ostrzez(f"{pelny}: {PRZESTARZALE[pelny]}")

    for klucz in dokument:
        if klucz not in znane:
            podobne = difflib.get_close_matches(klucz, sorted(znane), n=3, cutoff=0.75)
            raport.ostrzez(f"{klucz}: klucz nieznany dokumentacji i schematowi"
                           + (f" — może chodziło o: {', '.join(podobne)}" if podobne else ""))
    odwiedz("", dokument)

    if "$schema" not in dokument and rodzaj != "managed":
        raport.uwaga(f"brak \"$schema\": \"{URL_SCHEMATU}\" — edytor nie podpowie ani nie sprawdzi kluczy")

    tryb = (dokument.get("permissions") or {}).get("defaultMode")
    if tryb in ("auto", "bypassPermissions") and rodzaj in ("project", "local"):
        raport.blad(f"permissions.defaultMode={tryb}: z plików projektu i local ta wartość nie działa "
                    f"(tylko user, managed albo --permission-mode)")
    if tryb == "bypassPermissions":
        raport.ostrzez("permissions.defaultMode=bypassPermissions: tylko w odizolowanym kontenerze lub VM")
    if dokument.get("attribution") is False and wersja_cli and cc.wersja_mniejsza(wersja_cli, "2.1.281"):
        raport.blad("attribution: false wymaga ≥2.1.281 — starsze CLI odrzucają cały plik")


def sprawdz_regule(lista: str, regula: object, raport: Raport) -> None:
    if not isinstance(regula, str):
        raport.blad(f"permissions.{lista}: reguła nie jest tekstem")
        return
    rozbior = cc.rozbierz_regule(regula)
    if not rozbior:
        raport.blad(f"permissions.{lista}: „{regula}” — niepoprawna składnia (Narzędzie albo Narzędzie(specyfikator))")
        return
    narzedzie, argument = rozbior
    znane = cc.narzedzia()
    if narzedzie.startswith("mcp__"):
        if argument is not None:
            raport.blad(f"permissions.{lista}: „{regula}” — reguła mcp__ z nawiasami jest pomijana przy wczytywaniu "
                        f"pliku ustawień; parametr narzędzia MCP blokuj flagą --disallowed-tools")
        serwer = narzedzie.split("__")[1] if narzedzie.count("__") >= 1 else ""
        if lista == "allow" and ("*" in serwer or narzedzie in ("mcp__*", "mcp__")):
            raport.blad(f"permissions.allow: „{regula}” — glob bez nazwy serwera jest pomijany i nic nie zatwierdza")
        return
    if "*" in narzedzie:
        if lista == "allow":
            raport.blad(f"permissions.allow: „{regula}” — glob w nazwie narzędzia działa tylko w deny/ask "
                        f"(w allow tylko po prefiksie mcp__<serwer>__)")
        return
    if narzedzie not in znane and narzedzie not in ("Task", "Cd", "MultiEdit", "TaskOutput", "LS") \
            and "_" not in narzedzie:
        podobne = difflib.get_close_matches(narzedzie, sorted(znane), n=2, cutoff=0.7)
        raport.ostrzez(f"permissions.{lista}: „{narzedzie}” — nieznana nazwa narzędzia"
                       + (f" (może: {', '.join(podobne)})" if podobne else ""))
    if narzedzie in ("Write", "NotebookEdit", "Glob", "MultiEdit") and argument:
        raport.ostrzez(f"permissions.{lista}: „{regula}” — reguły ścieżek sprawdzane są tylko dla Read i Edit; "
                       f"użyj Edit(...)")
    if argument is None:
        return
    if ":" in argument and not argument.endswith(":*") and narzedzie in GLOWNE_POLA_NARZEDZI:
        parametr = argument.split(":", 1)[0].strip()
        if parametr == GLOWNE_POLA_NARZEDZI[narzedzie]:
            raport.blad(f"permissions.{lista}: „{regula}” — dopasowanie po głównym polu ({parametr}) jest ignorowane")
    if narzedzie in ("Bash", "PowerShell"):
        if ":*" in argument and not argument.endswith(":*"):
            raport.blad(f"permissions.{lista}: „{regula}” — „:*” działa tylko na końcu wzorca")
        slowa = argument.split()
        if lista == "allow" and len(slowa) >= 3 and slowa[0] != "*" and slowa[1] == "*":
            raport.ostrzez(f"permissions.allow: „{regula}” — gwiazdka przed podpoleceniem dopasowuje każde "
                           f"podpolecenie i opcje (np. git -c …); CLI ostrzega o tym przy starcie — "
                           f"stawiaj * po podpoleceniu (np. Bash(git log *))")
        elif lista == "allow" and len(slowa) == 2 and slowa[1] == "*" and slowa[0] != "*" and ":" not in slowa[0]:
            raport.uwaga(f"permissions.allow: „{regula}” — zatwierdza wszystkie podpolecenia programu {slowa[0]}")
        if lista == "allow" and argument.strip() in ("*", ""):
            raport.ostrzez(f"permissions.allow: „{regula}” — zatwierdza każde polecenie powłoki")
    if narzedzie == "WebFetch" and not (argument.startswith("domain:") or ":" in argument):
        raport.blad(f"permissions.{lista}: „{regula}” — WebFetch przyjmuje specyfikator domain:<host>")
    if narzedzie in ("Read", "Edit") and argument.startswith("/") and not argument.startswith("//"):
        raport.uwaga(f"permissions.{lista}: „{regula}” — pojedynczy „/” kotwiczy w źródle ustawień "
                     f"(projekt: katalog roboczy; user: ~/.claude; --settings: katalog pliku), nie w korzeniu; "
                     f"ścieżka bezwzględna to „//…”")


def sprawdz_uprawnienia(dokument: dict, raport: Raport) -> None:
    uprawnienia = dokument.get("permissions")
    if not isinstance(uprawnienia, dict):
        return
    for lista in ("allow", "ask", "deny"):
        for regula in uprawnienia.get(lista, []) or []:
            sprawdz_regule(lista, regula, raport)
    allow = set(uprawnienia.get("allow", []) or [])
    for regula in uprawnienia.get("deny", []) or []:
        if regula in allow:
            raport.ostrzez(f"permissions: „{regula}” jest w allow i w deny — wygrywa deny (kolejność deny > ask > allow)")
    for lista in ("allow", "deny", "ask"):
        reguly = set(uprawnienia.get(lista, []) or [])
        if "Edit" in reguly and "Write" not in reguly:
            raport.ostrzez(f"permissions.{lista}: goła nazwa „Edit” dotyczy tylko narzędzia Edit — „Write” nie jest nią "
                           f"{'blokowany' if lista == 'deny' else 'zatwierdzany'} (próba 2.1.286); dodaj „Write” "
                           f"albo użyj „Edit(./**)”")


def sprawdz_hooki(dokument: dict, raport: Raport) -> None:
    hooki = dokument.get("hooks")
    if not isinstance(hooki, dict):
        return
    znane = cc.zdarzenia_hookow()
    for zdarzenie, grupy in hooki.items():
        if zdarzenie not in znane:
            podobne = difflib.get_close_matches(zdarzenie, sorted(znane), n=2, cutoff=0.6)
            raport.blad(f"hooks.{zdarzenie}: nieznane zdarzenie" + (f" (może: {', '.join(podobne)})" if podobne else ""))
            continue
        for grupa in grupy if isinstance(grupy, list) else []:
            if not isinstance(grupa, dict):
                continue
            matcher = grupa.get("matcher")
            if matcher not in (None, "", "*") and zdarzenie in ZDARZENIA_BEZ_MATCHERA:
                raport.ostrzez(f"hooks.{zdarzenie}: zdarzenie nie obsługuje matchera — „{matcher}” jest ignorowany")
            if isinstance(matcher, str) and matcher.startswith("mcp__") and all(c.isalnum() or c in "_-" for c in matcher) \
                    and matcher.count("__") == 1:
                raport.blad(f"hooks.{zdarzenie}: matcher „{matcher}” porówna się dosłownie i nie trafi w żadne "
                            f"narzędzie — dla całego serwera pisz „{matcher}__.*”")
            for handler in grupa.get("hooks", []) or []:
                if not isinstance(handler, dict):
                    continue
                typ = handler.get("type")
                if typ not in TYPY_HOOKOW:
                    raport.blad(f"hooks.{zdarzenie}: typ „{typ}” spoza {sorted(TYPY_HOOKOW)}")
                    continue
                if "if" in handler and zdarzenie not in ZDARZENIA_NARZEDZIOWE:
                    raport.blad(f"hooks.{zdarzenie}: pole `if` działa tylko na zdarzeniach narzędzi — "
                                f"na tym zdarzeniu hook z `if` nie uruchomi się nigdy")
                if typ == "mcp_tool" and zdarzenie in ("SessionStart", "Setup"):
                    raport.blad(f"hooks.{zdarzenie}: hook mcp_tool jest pomijany przy starcie i wznowieniu "
                                f"(serwery MCP nie są jeszcze dostępne) — użyj command lub http")
                if typ in ("prompt", "agent") and zdarzenie == "PreModelSwitch":
                    raport.blad("hooks.PreModelSwitch: obsługuje tylko command, http i mcp_tool")
                if handler.get("once") is not None:
                    raport.uwaga(f"hooks.{zdarzenie}: `once` działa tylko w hookach z frontmattera skilla")
                if typ == "http" and handler.get("headers") and not handler.get("allowedEnvVars"):
                    if any("$" in str(v) for v in handler["headers"].values()):
                        raport.blad(f"hooks.{zdarzenie}: nagłówki z $ZMIENNA bez allowedEnvVars — zmienne zostaną puste")
                if typ == "command":
                    polecenie = str(handler.get("command", ""))
                    if "${CLAUDE_PLUGIN_ROOT}" in polecenie and "args" not in handler and '"${CLAUDE_PLUGIN_ROOT}"' not in polecenie:
                        raport.ostrzez(f"hooks.{zdarzenie}: ${{CLAUDE_PLUGIN_ROOT}} w formie powłoki bez cudzysłowu — "
                                       f"użyj formy exec (`args`) albo cudzysłowów")
                    if zdarzenie == "PermissionRequest" and "exit 2" in polecenie:
                        raport.ostrzez("hooks.PermissionRequest: exit 2 jest ignorowany — odmawiaj obiektem decision")


def sprawdz_env(dokument: dict, rodzaj: str, raport: Raport) -> None:
    env = dokument.get("env") if isinstance(dokument.get("env"), dict) else {}
    tryb = (dokument.get("permissions") or {}).get("defaultMode") if isinstance(dokument.get("permissions"), dict) else None
    if str(env.get("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "")).lower() in ("1", "true") and tryb not in (None, "default"):
        raport.ostrzez(f"env.CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 wymusza tryb „default” — defaultMode „{tryb}” "
                       f"zostanie pominięty (próba 2.1.286)")
    srodowisko = dokument.get("env")
    if not isinstance(srodowisko, dict):
        return
    znane = cc.zmienne()
    for nazwa, wartosc in srodowisko.items():
        if not isinstance(wartosc, str):
            raport.blad(f"env.{nazwa}: wartość musi być tekstem (np. \"1\", nie 1)")
        if nazwa in ZMIENNE_IGNOROWANE_ZAWSZE:
            raport.blad(f"env.{nazwa}: zmienna ignorowana w bloku env każdego pliku — ustaw ją w środowisku procesu")
        elif rodzaj in ("project", "local") and (nazwa in ZMIENNE_IGNOROWANE_W_PROJEKCIE or nazwa.startswith(OTEL_PREFIKSY)):
            raport.ostrzez(f"env.{nazwa}: w ustawieniach projektu/local zmienna jest ignorowana (poza wartościami "
                           f"wyłączającymi telemetrię) — ustaw ją w user, managed, --settings albo w środowisku")
        if cc.wygladaja_na_sekret(nazwa) and isinstance(wartosc, str) and wartosc and not wartosc.startswith("${"):
            raport.blad(f"env.{nazwa}: wygląda na sekret wpisany w plik ustawień (wartość nie jest wypisywana) — "
                        f"użyj apiKeyHelper, menedżera sekretów albo zmiennej procesu")
        if nazwa not in znane and nazwa.startswith(("CLAUDE_", "ANTHROPIC_", "DISABLE_", "MCP_")):
            podobne = difflib.get_close_matches(nazwa, sorted(znane), n=2, cutoff=0.85)
            raport.ostrzez(f"env.{nazwa}: zmiennej nie ma w dokumentacji env-vars"
                           + (f" (może: {', '.join(podobne)})" if podobne else ""))


def sprawdz_piaskownice(dokument: dict, raport: Raport) -> None:
    piaskownica = dokument.get("sandbox")
    if not isinstance(piaskownica, dict) or not piaskownica.get("enabled"):
        return
    if not piaskownica.get("failIfUnavailable"):
        raport.uwaga("sandbox.failIfUnavailable nie jest true — gdy bwrap/socat zawiodą, polecenia pójdą bez piaskownicy")
    if piaskownica.get("allowUnsandboxedCommands", True):
        raport.uwaga("sandbox.allowUnsandboxedCommands nie jest false — model może poprosić o dangerouslyDisableSandbox")
    siec = piaskownica.get("network") or {}
    if siec.get("allowAllUnixSockets"):
        raport.ostrzez("sandbox.network.allowAllUnixSockets: true otwiera każde gniazdo (np. docker.sock)")
    if piaskownica.get("enableWeakerNestedSandbox"):
        raport.ostrzez("sandbox.enableWeakerNestedSandbox: tylko gdy zewnętrzna warstwa (kontener/bwrap) izoluje proces")


def sprawdz_binarka(sciezka: Path, rodzaj: str, cli: str, raport: Raport) -> None:
    """Warstwa 4: walidacja własnym schematem CLI — `claude doctor` w odizolowanym profilu."""
    import os
    import shutil
    import subprocess
    import tempfile

    if rodzaj == "managed":
        raport.uwaga("CLI: plik zarządzany sprawdzany jest jako plik użytkownika (klucze Managed CLI tam pomija)")
    baza = Path(tempfile.mkdtemp(prefix="walidacja-cc-"))
    try:
        (baza / "profil").mkdir()
        (baza / "dom").mkdir()
        (baza / "cwd" / ".claude").mkdir(parents=True)
        cel = {"project": baza / "cwd" / ".claude" / "settings.json",
               "local": baza / "cwd" / ".claude" / "settings.local.json"}.get(rodzaj, baza / "profil" / "settings.json")
        shutil.copy(sciezka, cel)
        srodowisko = {"HOME": str(baza / "dom"), "PATH": "/usr/bin:/bin", "TERM": "dumb",
                      "CLAUDE_CONFIG_DIR": str(baza / "profil"), "DISABLE_AUTOUPDATER": "1",
                      "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "TMPDIR": str(baza)}
        try:
            wynik = subprocess.run([cli, "doctor"], cwd=baza / "cwd", env=srodowisko, capture_output=True,
                                   text=True, timeout=90, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired) as blad:
            raport.ostrzez(f"CLI: nie udało się uruchomić `claude doctor`: {blad}")
            return
        wersja_cli = cc.wersja(wynik.stdout)
        w_sekcji = False
        znalezione = 0
        for linia in wynik.stdout.splitlines():
            if linia.strip() == "Invalid settings":
                w_sekcji = True
                continue
            if w_sekcji:
                if not linia.startswith("- "):
                    break
                opis = linia[2:].split(" › ", 1)[-1]
                if rodzaj == "managed" and "only honored from managed settings" in opis:
                    continue  # plik zarządzany sprawdzany w profilu użytkownika — to oczekiwane
                raport.blad(f"CLI {'.'.join(map(str, wersja_cli))} (claude doctor): {opis}")
                znalezione += 1
        if not znalezione:
            raport.uwaga(f"CLI {'.'.join(map(str, wersja_cli))} (claude doctor): plik przyjęty bez uwag")
            schematowe = [b for b in raport.bledy if b.startswith("schemat: ")]
            for b in schematowe:
                raport.bledy.remove(b)
                raport.ostrzez(f"schemat nieaktualny wobec CLI {'.'.join(map(str, wersja_cli))}: {b[len('schemat: '):]}")
    finally:
        shutil.rmtree(baza, ignore_errors=True)


def waliduj(sciezka: Path, rodzaj: str | None, wersja_cli: str, cli: str = "") -> Raport:
    raport = Raport(str(sciezka))
    try:
        dokument = cc.czytaj_json(sciezka)
    except (cc.BladJson, OSError) as blad:
        raport.blad(f"JSON: {blad}")
        return raport
    if not isinstance(dokument, dict):
        raport.blad("JSON: korzeń pliku ustawień musi być obiektem")
        return raport
    if sciezka.stat().st_size > 2 * 1024 * 1024:
        raport.blad("plik większy niż 2 MiB — --settings go odrzuci")
    rodzaj = rodzaj or zgadnij_rodzaj(sciezka)
    sprawdz_schemat(dokument, raport)
    sprawdz_klucze(dokument, rodzaj, wersja_cli, raport)
    sprawdz_uprawnienia(dokument, raport)
    sprawdz_hooki(dokument, raport)
    sprawdz_env(dokument, rodzaj, raport)
    sprawdz_piaskownice(dokument, raport)
    if cli:
        sprawdz_binarka(sciezka, rodzaj, cli, raport)
    raport.uwaga(f"rodzaj pliku: {rodzaj}")
    return raport


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pliki", nargs="*", type=Path)
    parser.add_argument("--rodzaj", choices=["user", "project", "local", "managed", "flaga"])
    parser.add_argument("--wersja", default="", help="docelowa wersja CLI, np. 2.1.286")
    parser.add_argument("--scisle", action="store_true", help="ostrzeżenia traktuj jak błędy")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--odswiez-schemat", action="store_true")
    parser.add_argument("--cli", default="", help="binarka claude: dodatkowo walidacja `claude doctor` "
                        "w odizolowanym profilu (własny schemat CLI)")
    argumenty = parser.parse_args()
    if argumenty.odswiez_schemat:
        odswiez_schemat()
        if not argumenty.pliki:
            return 0
    if not argumenty.pliki:
        parser.print_usage()
        return 2
    raporty = [waliduj(p, argumenty.rodzaj, argumenty.wersja, argumenty.cli) for p in argumenty.pliki]
    if argumenty.json:
        print(json.dumps([r.__dict__ for r in raporty], ensure_ascii=False, indent=1))
    else:
        for r in raporty:
            stan = "BŁĘDY" if r.bledy else ("OSTRZEŻENIA" if r.ostrzezenia else "OK")
            print(f"== {r.plik}: {stan} (schemat: {r.silnik or '—'})")
            for b in r.bledy:
                print(f"  BŁĄD  {b}")
            for o in r.ostrzezenia:
                print(f"  OSTRZ {o}")
            for u in r.uwagi:
                print(f"  uwaga {u}")
    zle = any(r.bledy or (argumenty.scisle and r.ostrzezenia) for r in raporty)
    return 1 if zle else 0


if __name__ == "__main__":
    sys.exit(main())
