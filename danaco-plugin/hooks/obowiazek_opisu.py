#!/usr/bin/env python3
"""Hook obowiązku opisu danaco-plugin: program z katalogu Danaco wolno użyć dopiero po
przeczytaniu w tej sesji jego opisu szczegółowego i skilla (narzędzie MCP `opis` serwera
danaco-programy).

Tryby (argument):
  po     PostToolUse na `opis`: zapisuje w stanie sesji, że opis programu został przeczytany.
  przed  PreToolUse na Bash, Monitor, `uruchom` i narzędziach zapisu plików: odmawia, gdy
         polecenie używa programu z katalogu, którego opisu w tej sesji nie przeczytano,
         oraz gdy narzędzie sięga do katalogu stanu (znacznik ustawia wyłącznie ten hook).

Katalog programów: rejestr `<DANACO_KATALOG>/rejestr/*.json` (domyślnie /danaco/programy/katalog);
bez rejestru (serwer bez katalogu) hook niczego nie blokuje. Stan: `~/.claude/plugins/data/danaco-plugin/
obowiazek-opisu/<sesja>.json`. Usterka hooka (zły JSON zdarzenia, nieczytelny rejestr) kończy się kodem 0
bez decyzji, żeby błąd kontroli nie zatrzymał pracy.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shlex
import sys
import tempfile

KATALOG = os.environ.get("DANACO_KATALOG", "/danaco/programy/katalog")
NAZWA_STANU = "obowiazek-opisu"
# Słowa, po których w segmencie polecenia stoi właściwy program.
OPAKOWANIA = {"sudo", "env", "time", "nohup", "nice", "exec", "command", "builtin", "xargs", "stdbuf", "ionice", "timeout"}
SLOWA_POWLOKI = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "in", "case", "esac",
                 "!", "{", "}", "[[", "]]", "function", "select"}
PRZYPISANIE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORY = re.compile(r"\|\||&&|\$\(|[|;&\n()`]")


def katalog_stanu() -> str:
    konfiguracja = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.realpath(os.path.join(konfiguracja, "plugins", "data", "danaco-plugin", NAZWA_STANU))


def sesja_pliku(sesja: str) -> str:
    bezpieczna = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sesja or ""))[:120].strip(".") or "bez-sesji"
    return os.path.join(katalog_stanu(), bezpieczna + ".json")


def polecenia_katalogu() -> set[str]:
    nazwy: set[str] = set()
    for plik in glob.glob(os.path.join(KATALOG, "rejestr", "*.json")):
        with open(plik, encoding="utf-8") as f:
            for wpis in json.load(f).get("narzedzia", []):
                if wpis.get("polecenie"):
                    nazwy.add(wpis["polecenie"])
    return nazwy


def przeczytane(sesja: str) -> set[str]:
    try:
        with open(sesja_pliku(sesja), encoding="utf-8") as f:
            return set(json.load(f).get("przeczytane", []))
    except (OSError, ValueError):
        return set()


def zapisz(sesja: str, nazwy: set[str]) -> None:
    cel = sesja_pliku(sesja)
    os.makedirs(os.path.dirname(cel), mode=0o700, exist_ok=True)
    fd, tymczasowy = tempfile.mkstemp(dir=os.path.dirname(cel), prefix=".zapis-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"sesja": sesja, "przeczytane": sorted(nazwy)}, f, ensure_ascii=False)
    os.replace(tymczasowy, cel)


def programy_polecenia(tekst: str) -> set[str]:
    """Programy wywołane w poleceniu powłoki: pierwsze słowo każdego segmentu potoku i listy."""
    wynik: set[str] = set()
    for segment in SEPARATORY.split(tekst):
        try:
            slowa = shlex.split(segment, comments=True)
        except ValueError:
            slowa = segment.split()
        i = 0
        while i < len(slowa):
            slowo = slowa[i]
            if PRZYPISANIE.match(slowo) or slowo in SLOWA_POWLOKI:
                i += 1
                continue
            nazwa = os.path.basename(slowo)
            if nazwa in OPAKOWANIA:
                wynik.add(nazwa)
                i += 1
                while i < len(slowa) and (slowa[i].startswith("-") or (nazwa == "timeout" and re.fullmatch(r"[\d.]+[smhd]?", slowa[i]))):
                    i += 1
                continue
            wynik.add(nazwa)
            break
    return wynik


def odmowa(powod: str) -> int:
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": powod}}, sys.stdout, ensure_ascii=False)
    return 0


def tryb_po(zdarzenie: dict) -> int:
    nazwa = str((zdarzenie.get("tool_input") or {}).get("nazwa", "")).strip()
    odpowiedz = json.dumps(zdarzenie.get("tool_response"), ensure_ascii=False)
    if not nazwa or "Nie znam" in odpowiedz[:200] or nazwa not in polecenia_katalogu():
        return 0
    sesja = zdarzenie.get("session_id", "")
    zapisz(sesja, przeczytane(sesja) | {nazwa})
    return 0


def tryb_przed(zdarzenie: dict) -> int:
    wejscie = zdarzenie.get("tool_input") or {}
    surowe = json.dumps(wejscie, ensure_ascii=False)
    if katalog_stanu() in surowe or NAZWA_STANU in surowe:
        return odmowa("Stan obowiązku opisu programów ustawia wyłącznie hook po przeczytaniu `opis`; "
                      "nie zapisujesz go ani nie zmieniasz.")
    tekst = wejscie.get("command") or wejscie.get("polecenie") or ""
    if not isinstance(tekst, str) or not tekst.strip():
        return 0
    katalog = polecenia_katalogu()
    if not katalog:
        return 0
    brak = sorted((programy_polecenia(tekst) & katalog) - przeczytane(zdarzenie.get("session_id", "")))
    if not brak:
        return 0
    return odmowa("Przed pierwszym użyciem programu w sesji obowiązkowo przeczytaj jego opis szczegółowy i skill: "
                  "narzędzie `opis` serwera danaco-programy dla: " + ", ".join(brak) + ". Potem ponów polecenie.")


def main() -> int:
    tryb = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        zdarzenie = json.load(sys.stdin)
        if not isinstance(zdarzenie, dict):
            return 0
        if tryb == "po":
            return tryb_po(zdarzenie)
        if tryb == "przed":
            return tryb_przed(zdarzenie)
    except (ValueError, OSError) as blad:
        print(f"danaco-plugin obowiazek_opisu: {blad}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
