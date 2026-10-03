#!/usr/bin/env python3
"""Hook obowiązku opisu danaco-plugin: program z katalogu Danaco wolno użyć dopiero po
przeczytaniu w tej sesji jego opisu szczegółowego i skilla (narzędzie MCP `opis` serwera
danaco-programy), a na maszynę wirtualną (strefę środowisk) wolno wejść dopiero po przeczytaniu
w tej sesji skilla tej maszyny (narzędzie `maszyna` albo `opis <skill maszyny>`).

Tryby (argument):
  po     PostToolUse na `opis` i `maszyna`: zapisuje w stanie sesji przeczytany program i jego
         skill. Program jest zaliczony tylko ze skillem: przeczytanym w tym wywołaniu albo
         wcześniej w sesji (wspólny skill kilku programów wystarczy przeczytać raz, potem `opis`
         z pelny=false). `opis` samego skilla i `maszyna` ze skillem zaliczają skill.
  przed  PreToolUse na Bash, Monitor, `uruchom` i narzędziach zapisu plików: odmawia, gdy
         polecenie używa programu z katalogu, którego opisu w tej sesji nie przeczytano, gdy
         wchodzi na maszynę (polecenie stref albo nakładka maszyny z operacją inną niż stan),
         której skilla w tej sesji nie przeczytano, oraz gdy polecenie albo zapisywany plik sięga
         do katalogu stanu (znacznik ustawia wyłącznie ten hook).

Treść heredoców (`<<EOF … EOF`) to dane, nie polecenia — nie jest rozbierana na programy.
Katalog programów: rejestr `<DANACO_KATALOG>/rejestr/*.json` (domyślnie /danaco/programy/katalog);
maszyny: `<DANACO_KATALOG>/maszyny.json` (generuje zbuduj_indeks.py). Bez rejestru (serwer bez
katalogu) hook niczego nie blokuje; bez wykazu maszyn nie egzekwuje skilli maszyn. Stan: katalog danych wtyczki
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
# Operacje polecenia stref, które nie wchodzą na maszynę (podgląd stanu i pomoc).
OPERACJE_BEZ_WEJSCIA = {"", "stan", "kolejka", "strefy", "-h", "--help", "pomoc"}
OPCJE_Z_WARTOSCIA = {"--zadanie"}


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


def maszyny_katalogu() -> dict:
    """Wykaz maszyn z maszyny.json: {"polecenie": …, "maszyny": {strefa: {"skill", "nakladka", "system"}}};
    pusty słownik, gdy katalog go nie ma albo jest nieczytelny."""
    try:
        with open(os.path.join(KATALOG, "maszyny.json"), encoding="utf-8") as f:
            dane = json.load(f)
    except (OSError, ValueError):
        return {}
    return dane if isinstance(dane, dict) and isinstance(dane.get("maszyny"), dict) else {}


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


def wywolania(tekst: str) -> list[tuple[str, list[str]]]:
    """Wywołania w poleceniu powłoki: (program, argumenty) dla pierwszego słowa każdego segmentu potoku
    i listy; opakowania (sudo, timeout…) są osobnymi wywołaniami bez argumentów."""
    wynik: list[tuple[str, list[str]]] = []
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
                wynik.append((nazwa, []))
                i += 1
                while i < len(slowa) and (slowa[i].startswith("-") or (nazwa == "timeout" and re.fullmatch(r"[\d.]+[smhd]?", slowa[i]))):
                    i += 1
                continue
            wynik.append((nazwa, slowa[i + 1:]))
            break
    return wynik


def programy_polecenia(tekst: str) -> set[str]:
    """Programy wywołane w poleceniu powłoki."""
    return {nazwa for nazwa, _ in wywolania(tekst)}


def wejscia_na_maszyny(tekst: str, dane: dict) -> tuple[set[str], bool]:
    """Strefy, na które polecenie wchodzi (operacja inna niż stan, kolejka, pomoc), i czy któreś wywołanie
    podaje strefę niedosłownie (zmienna, podstawienie) — wtedy nie da się sprawdzić, na którą maszynę wchodzi."""
    polecenie = dane.get("polecenie") or "danaco-srodowisko"
    maszyny = dane.get("maszyny") or {}
    nakladki = {m.get("nakladka"): s for s, m in maszyny.items() if m.get("nakladka")}
    strefy: set[str] = set()
    niedoslowna = False
    for nazwa, argumenty in wywolania(tekst):
        if nazwa in nakladki:
            operacja = argumenty[0] if argumenty else "stan"
            if operacja not in OPERACJE_BEZ_WEJSCIA:
                strefy.add(nakladki[nazwa])
            continue
        if nazwa != polecenie:
            continue
        i = 0
        while i < len(argumenty) and argumenty[i].startswith("-"):
            i += 2 if argumenty[i] in OPCJE_Z_WARTOSCIA else 1
        strefa = argumenty[i] if i < len(argumenty) else ""
        operacja = argumenty[i + 1] if i + 1 < len(argumenty) else ""
        if strefa in OPERACJE_BEZ_WEJSCIA or operacja in OPERACJE_BEZ_WEJSCIA:
            continue
        if strefa in maszyny:
            strefy.add(strefa)
        elif "$" in strefa or "`" in strefa:
            niedoslowna = True
    return strefy, niedoslowna


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


def zalicz_skill(sesja: str, skill: str) -> int:
    programy, przeczytane_skille = stan(sesja)
    zapisz(sesja, programy, przeczytane_skille | {skill})
    return 0


def tryb_po(zdarzenie: dict) -> int:
    wejscie = zdarzenie.get("tool_input") or {}
    odpowiedz = json.dumps(zdarzenie.get("tool_response"), ensure_ascii=False)
    sesja = zdarzenie.get("session_id", "")
    pelny = wejscie.get("pelny", True) is not False and "--- SKILL:" in odpowiedz
    if str(zdarzenie.get("tool_name", "")).endswith("__maszyna"):
        m = (maszyny_katalogu().get("maszyny") or {}).get(str(wejscie.get("strefa", "")).strip().lower()) or {}
        return zalicz_skill(sesja, m["skill"]) if pelny and m.get("skill") else 0
    nazwa = str(wejscie.get("nazwa", "")).strip()
    skille = skille_katalogu()
    if not nazwa or "Nie znam" in odpowiedz[:200]:
        return 0
    if nazwa not in skille:
        # `opis` samego skilla (np. skilla maszyny, który nie jest programem) zalicza ten skill
        if pelny and os.path.isfile(os.path.join(KATALOG, "skille", nazwa, "SKILL.md")):
            return zalicz_skill(sesja, nazwa)
        return 0
    programy, przeczytane_skille = stan(sesja)
    skill = skille[nazwa]
    if pelny:
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
        return obowiazek_skilla_maszyny(tekst, przeczytane_skille)
    ze_skillem = [n for n in brak if skille[n] and skille[n] not in przeczytane_skille]
    bez_skilla = [n for n in brak if n not in ze_skillem]
    czesci = []
    if ze_skillem:
        czesci.append("`opis` (pełny, ze skillem) dla: " + ", ".join(ze_skillem))
    if bez_skilla:
        czesci.append("`opis` z pelny=false (ich skill już przeczytany w tej sesji) dla: " + ", ".join(bez_skilla))
    return odmowa("Przed pierwszym użyciem programu w sesji obowiązkowo przeczytaj jego opis szczegółowy i skill "
                  "narzędziem serwera danaco-programy: " + "; ".join(czesci) + ". Potem ponów polecenie.")


def obowiazek_skilla_maszyny(tekst: str, przeczytane_skille: set[str]) -> int:
    dane = maszyny_katalogu()
    if not dane:
        return 0
    strefy, niedoslowna = wejscia_na_maszyny(tekst, dane)
    maszyny = dane["maszyny"]
    brak = sorted(s for s in strefy if maszyny[s].get("skill") and maszyny[s]["skill"] not in przeczytane_skille)
    if brak:
        wykaz = "; ".join(f"{s} ({maszyny[s].get('system', '')}): narzędzie `maszyna` ze strefą {s} albo "
                          f"`opis` {maszyny[s]['skill']}" for s in brak)
        return odmowa("Przed wejściem na maszynę obowiązkowo przeczytaj w tej sesji skill tej maszyny (start, "
                      "przesyłanie, polecenia, pobieranie wyników przed stop, pułapki) narzędziem serwera "
                      f"danaco-programy — {wykaz}. Potem ponów polecenie.")
    if niedoslowna:
        return odmowa("Podaj strefę w poleceniu stref dosłownie (np. `danaco-srodowisko linux start`), nie zmienną "
                      "— obowiązek skilla maszyny sprawdza się po nazwie strefy.")
    return 0


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
