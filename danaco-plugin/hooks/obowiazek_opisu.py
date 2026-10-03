#!/usr/bin/env python3
"""Hook obowiązku opisu danaco-plugin: program z katalogu Danaco wolno użyć dopiero po
przeczytaniu w tej sesji jego opisu szczegółowego i skilla (narzędzie MCP `opis` serwera
danaco-programy).

Tryby (argument):
  po     PostToolUse na `opis`: zapisuje w stanie sesji przeczytany program i jego skill. Program
         jest zaliczony tylko ze skillem: przeczytanym w tym wywołaniu albo wcześniej w sesji
         (wspólny skill kilku programów wystarczy przeczytać raz, potem `opis` z pelny=false).
  przed  PreToolUse na Bash, Monitor, `uruchom` i narzędziach zapisu plików: odmawia, gdy
         polecenie używa programu z katalogu, którego opisu w tej sesji nie przeczytano,
         oraz gdy polecenie albo zapisywany plik sięga do katalogu stanu (znacznik ustawia
         wyłącznie ten hook).

Treść heredoców (`<<EOF … EOF`) to dane, nie polecenia — nie jest rozbierana na programy.
Katalog programów: rejestr `<DANACO_KATALOG>/rejestr/*.json` (domyślnie /danaco/programy/katalog);
bez rejestru (serwer bez katalogu) hook niczego nie blokuje. Stan: katalog danych wtyczki
`~/.claude/plugins/data/danaco-plugin/` (podkatalog NAZWA_STANU, plik na sesję). Usterka hooka (zły JSON
zdarzenia, nieczytelny rejestr) kończy się kodem 0 bez decyzji, żeby błąd kontroli nie zatrzymał pracy.
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
NAZWA_STANU = "przeczytane-opisy"
NARZEDZIA_ZAPISU = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
# Słowa, po których w segmencie polecenia stoi właściwy program.
OPAKOWANIA = {"sudo", "env", "time", "nohup", "nice", "exec", "command", "builtin", "xargs", "stdbuf", "ionice", "timeout"}
SLOWA_POWLOKI = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "in", "case", "esac",
                 "!", "{", "}", "[[", "]]", "function", "select"}
PRZYPISANIE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORY = re.compile(r"\|\||&&|\$\(|[|;&\n()`]")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def katalog_stanu() -> str:
    konfiguracja = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.realpath(os.path.join(konfiguracja, "plugins", "data", "danaco-plugin", NAZWA_STANU))


def sesja_pliku(sesja: str) -> str:
    bezpieczna = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sesja or ""))[:120].strip(".") or "bez-sesji"
    return os.path.join(katalog_stanu(), bezpieczna + ".json")


def skille_katalogu() -> dict[str, str]:
    """Polecenie katalogu → nazwa jego skilla (pusty napis, gdy wpis skilla nie podaje)."""
    wynik: dict[str, str] = {}
    for plik in glob.glob(os.path.join(KATALOG, "rejestr", "*.json")):
        with open(plik, encoding="utf-8") as f:
            for wpis in json.load(f).get("narzedzia", []):
                if wpis.get("polecenie"):
                    wynik[wpis["polecenie"]] = wpis.get("skill") or ""
    return wynik


def stan(sesja: str) -> tuple[set[str], set[str]]:
    """Przeczytane w sesji: (programy, skille)."""
    try:
        with open(sesja_pliku(sesja), encoding="utf-8") as f:
            dane = json.load(f)
        return set(dane.get("przeczytane", [])), set(dane.get("skille", []))
    except (OSError, ValueError):
        return set(), set()


def zapisz(sesja: str, programy: set[str], skille: set[str]) -> None:
    cel = sesja_pliku(sesja)
    os.makedirs(os.path.dirname(cel), mode=0o700, exist_ok=True)
    fd, tymczasowy = tempfile.mkstemp(dir=os.path.dirname(cel), prefix=".zapis-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"sesja": sesja, "przeczytane": sorted(programy), "skille": sorted(skille)}, f, ensure_ascii=False)
    os.replace(tymczasowy, cel)


def bez_heredocow(tekst: str) -> str:
    """Usuwa treść heredoców: wiersze po `<<ZNACZNIK` do wiersza z samym znacznikiem."""
    wynik, znaczniki = [], []
    for wiersz in tekst.split("\n"):
        if znaczniki:
            if wiersz.strip() == znaczniki[0]:
                znaczniki.pop(0)
            continue
        wynik.append(wiersz)
        znaczniki.extend(m.group(2) for m in HEREDOC.finditer(wiersz))
    return "\n".join(wynik)


def programy_polecenia(tekst: str) -> set[str]:
    """Programy wywołane w poleceniu powłoki: pierwsze słowo każdego segmentu potoku i listy."""
    wynik: set[str] = set()
    for segment in SEPARATORY.split(bez_heredocow(tekst)):
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


def siega_do_stanu(narzedzie: str, wejscie: dict, tekst: str) -> bool:
    """Polecenie z rzeczywistą ścieżką katalogu stanu albo zapis pliku w tym katalogu."""
    katalog = katalog_stanu()
    if narzedzie in NARZEDZIA_ZAPISU:
        sciezka = str(wejscie.get("file_path") or wejscie.get("notebook_path") or "")
        return bool(sciezka) and os.path.realpath(sciezka).startswith(katalog + os.sep)
    return katalog in tekst or ("data/danaco-plugin/" + NAZWA_STANU) in tekst


def odmowa(powod: str) -> int:
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": powod}}, sys.stdout, ensure_ascii=False)
    return 0


def tryb_po(zdarzenie: dict) -> int:
    wejscie = zdarzenie.get("tool_input") or {}
    nazwa = str(wejscie.get("nazwa", "")).strip()
    odpowiedz = json.dumps(zdarzenie.get("tool_response"), ensure_ascii=False)
    skille = skille_katalogu()
    if not nazwa or "Nie znam" in odpowiedz[:200] or nazwa not in skille:
        return 0
    sesja = zdarzenie.get("session_id", "")
    programy, przeczytane_skille = stan(sesja)
    skill = skille[nazwa]
    if wejscie.get("pelny", True) is not False and "--- SKILL:" in odpowiedz:
        if skill:
            przeczytane_skille.add(skill)
    elif skill and skill not in przeczytane_skille:
        return 0  # opis bez skilla, a skilla w sesji jeszcze nie przeczytano — program niezaliczony
    zapisz(sesja, programy | {nazwa}, przeczytane_skille)
    return 0


def tryb_przed(zdarzenie: dict) -> int:
    wejscie = zdarzenie.get("tool_input") or {}
    tekst = wejscie.get("command") or wejscie.get("polecenie") or ""
    tekst = tekst if isinstance(tekst, str) else ""
    if siega_do_stanu(str(zdarzenie.get("tool_name", "")), wejscie, tekst):
        return odmowa("Stan obowiązku opisu programów ustawia wyłącznie hook po przeczytaniu `opis`; "
                      "nie zapisujesz go ani nie zmieniasz.")
    if not tekst.strip():
        return 0
    skille = skille_katalogu()
    if not skille:
        return 0
    programy, przeczytane_skille = stan(zdarzenie.get("session_id", ""))
    brak = sorted((programy_polecenia(tekst) & set(skille)) - programy)
    if not brak:
        return 0
    ze_skillem = [n for n in brak if skille[n] and skille[n] not in przeczytane_skille]
    bez_skilla = [n for n in brak if n not in ze_skillem]
    czesci = []
    if ze_skillem:
        czesci.append("`opis` (pełny, ze skillem) dla: " + ", ".join(ze_skillem))
    if bez_skilla:
        czesci.append("`opis` z pelny=false (ich skill już przeczytany w tej sesji) dla: " + ", ".join(bez_skilla))
    return odmowa("Przed pierwszym użyciem programu w sesji obowiązkowo przeczytaj jego opis szczegółowy i skill "
                  "narzędziem serwera danaco-programy: " + "; ".join(czesci) + ". Potem ponów polecenie.")


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
