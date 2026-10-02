#!/usr/bin/env python3
"""Hooki danaco-praca 5: jedno wejście dla wszystkich zdarzeń wtyczki.

Użycie (z hooks/hak.sh): hak.py <tryb> < zdarzenie.json
  prompt      UserPromptSubmit — polecenia właściciela, zapis stanu
  narzedzie   PreToolUse — ochrona stanu, blokady sesji, straż sekretów i dysku
  stop        Stop — tryb pracy ciągłej (tylko agent główny)
  sesja       SessionStart i SubagentStart — przypomnienie aktywnych blokad

Zasada bezpieczeństwa: usterka hooka nie może zamknąć sesji (każdy wyjątek kończy się
kodem 0 bez decyzji), a decyzje idą wyłącznie przez JSON na stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import polecenia as P  # noqa: E402
import reguly as R  # noqa: E402
import stan as S  # noqa: E402

#: Po tylu kolejnych próbach zakończenia tury (bez wiadomości właściciela) hook Stop oddaje
#: turę, żeby właściciel mógł wpisać wiadomość i żeby została od razu odczytana. Tryb /praca
#: zostaje włączony i wznawia pracę na następnej turze. Zmienia DANACO_PRACA_PROG_ODDANIA.
PROG_ODDANIA = max(1, int(os.environ.get("DANACO_PRACA_PROG_ODDANIA", "6") or 6))
LIMIT_PLIKOW = int(os.environ.get("DANACO_PRACA_LIMIT_PLIKOW", "1") or 1)
NAZWA_WTYCZKI = "danaco-praca"


def wypisz(dane: dict) -> None:
    json.dump(dane, sys.stdout, ensure_ascii=False)


def wartosci_tekstowe(obj) -> list[str]:
    """Wszystkie łańcuchy w strukturze wejścia narzędzia (do wykrycia podrzuconego polecenia)."""
    wynik: list[str] = []
    if isinstance(obj, str):
        wynik.append(obj)
    elif isinstance(obj, dict):
        for wartosc in obj.values():
            wynik.extend(wartosci_tekstowe(wartosc))
    elif isinstance(obj, (list, tuple)):
        for wartosc in obj:
            wynik.extend(wartosci_tekstowe(wartosc))
    return wynik


# --- UserPromptSubmit -----------------------------------------------------------------------------

ZASADY_PRACY = (
    "Tryb pracy ciągłej włączył właściciel. Do jego polecenia /koniec-pracy nie kończysz tury z "
    "własnej woli: hook Stop odrzuca zakończenie i przypomina zlecenie. Nie czekasz i nie śpisz "
    "(sleep, pętle oczekiwania, ScheduleWakeup, CronCreate, blokujący odbiór wyniku są odrzucane). "
    "Wolno Ci uruchamiać procesy i agentów w tle oraz stawiać monitoring (także narzędziem Monitor), "
    "ale sam cały czas pracujesz dalej: weryfikujesz, testujesz, poprawiasz, dokumentujesz i bierzesz "
    "kolejne części zlecenia. Co pewien czas hook Stop sam odda turę, żeby właściciel mógł się wtrącić "
    "— to nie koniec trybu: /praca zostaje włączone i masz pracować dalej. Gdy właściciel przyśle "
    "wiadomość, najpierw ją obsłuż, a potem wracaj do zlecenia. Narzędzia i miejsca zapisu nie są "
    "ograniczone; obowiązują tylko zasady serwera (kosz zamiast kasowania, straż pakietów i dysku, "
    "sekrety). Trybu nie zmieniasz sam — przełącza go wyłącznie właściciel."
)


def obsluz_polecenia(zdarzenie: dict) -> int:
    tekst = str(zdarzenie.get("prompt") or "")
    pary, reszta = P.rozpoznaj(tekst)
    sesja = S.bezpieczna_sesja(zdarzenie.get("session_id"))
    magazyn = S.Magazyn()
    if not pary:
        # Zwykła wiadomość właściciela zaczyna nową turę. Przy włączonej pracy ciągłej:
        # zeruje licznik oddań tury i przypomina modelowi, że tryb trwa (re-aktywacja).
        stan = magazyn.wczytaj(sesja)
        if stan["praca"]["wlaczona"]:
            if stan["praca"].get("oddania"):
                with magazyn.blokada():
                    stan = magazyn.wczytaj(sesja)
                    stan["praca"]["oddania"] = 0
                    magazyn.zapisz(stan)
            kontekst = [f"[{NAZWA_WTYCZKI}] Tryb pracy ciągłej (/praca) jest nadal włączony. "
                        "Obsłuż tę wiadomość właściciela, a potem pracuj dalej nad zleceniem; "
                        "turę kończysz dopiero na /koniec-pracy albo gdy hook sam odda głos."]
            if stan["praca"].get("zlecenie"):
                kontekst.append("Zlecenie: " + stan["praca"]["zlecenie"])
            wypisz({"hookSpecificOutput": {"hookEventName": zdarzenie.get("hook_event_name") or "UserPromptSubmit",
                                           "additionalContext": "\n".join(kontekst)}})
        return 0

    nazwy = [p for p, _ in pary]
    zlecenie_pracy = ""
    for polecenie, arg in pary:
        if P.POLECENIA[polecenie] == ("praca", True) and arg:
            zlecenie_pracy = arg
    zmiany: list[str] = []
    widoki: list[str] = []
    wlaczono_prace = False

    with magazyn.blokada():
        stan = magazyn.wczytaj(sesja)
        for polecenie, arg in pary:
            rodzaj = P.POLECENIA[polecenie]
            if rodzaj[0] == "praca":
                stan["praca"]["wlaczona"] = rodzaj[1]
                stan["praca"]["oddania"] = 0
                if rodzaj[1]:
                    tresc = "\n".join(x for x in (zlecenie_pracy, reszta) if x)
                    if tresc or not stan["praca"].get("od"):
                        stan["praca"]["zlecenie"] = tresc[:4000]
                    stan["praca"]["od"] = stan["praca"].get("od") or S.teraz()
                    wlaczono_prace = True
                else:
                    stan["praca"]["od"] = None
                    stan["praca"]["zlecenie"] = ""
                zmiany.append(polecenie)
            elif rodzaj[0] == "blok":
                stan["blokady"][rodzaj[1]] = rodzaj[2]
                zmiany.append(polecenie)
            elif rodzaj == ("akcja", "wyczysc"):
                stan["praca"] = S.pusty(sesja)["praca"]
                for k in S.BLOKADY:
                    stan["blokady"][k] = False
                zmiany.append(polecenie)
                widoki.append("Wszystkie blokady i tryb pracy zdjęte.")
        if zmiany:
            magazyn.zapisz(stan, {"zdarzenie": "polecenie", "polecenia": zmiany,
                                  "zrodlo": zdarzenie.get("hook_event_name") or "UserPromptSubmit",
                                  "cwd": zdarzenie.get("cwd")})

    # Widoki i akcje pokazujące coś właścicielowi (po zapisie stanu).
    for polecenie, arg in pary:
        rodzaj = P.POLECENIA[polecenie]
        if rodzaj == ("widok", "tryb"):
            widoki.append(S.opis_stanu(stan))
        elif rodzaj == ("widok", "dziennik"):
            widoki.append("Ostatnie wpisy dziennika tej sesji:\n" + "\n".join(S.ogon_dziennika(magazyn, sesja)))
        elif rodzaj == ("widok", "sesja-id"):
            widoki.append(f"Identyfikator tej sesji: {zdarzenie.get('session_id') or '(nieznany)'}\n"
                          f"Przejmij ją z innego konta: /sesja-przejmij {zdarzenie.get('session_id') or '<id>'}")
        elif rodzaj == ("widok", "sesje"):
            widoki.append(wywolaj_przejmij(["--lista"]))
        elif rodzaj == ("akcja", "przejmij"):
            widoki.append(przejmij_sesje(arg))

    opis = S.opis_stanu(stan)
    etykieta = ", ".join("/" + p for p in nazwy)
    # Czysta wiadomość sterująca (same polecenia, bez zadania) — pokaż wynik i nie wołaj modelu.
    if not reszta and not wlaczono_prace and "koniec-pracy" not in nazwy:
        czesci = [f"{NAZWA_WTYCZKI}: {etykieta}"]
        if zmiany:
            czesci.append("")
            czesci.append(opis)
        if widoki:
            czesci.append("")
            czesci.append("\n\n".join(widoki))
        wypisz({"decision": "block", "reason": "\n".join(czesci)})
        return 0

    # Wiadomość ma też zadanie dla modelu: zapisz stan, podaj kontekst, pozwól pracować.
    kontekst = [f"[{NAZWA_WTYCZKI}] Właściciel wydał polecenia: {etykieta}. Stan:", opis]
    if wlaczono_prace:
        kontekst += ["", ZASADY_PRACY]
        if stan["praca"]["zlecenie"]:
            kontekst += ["", "Zlecenie: " + stan["praca"]["zlecenie"]]
    if widoki:
        kontekst += ["", "\n\n".join(widoki)]
    if "koniec-pracy" in nazwy:
        kontekst += ["", "Tryb pracy ciągłej jest wyłączony: wolno zakończyć turę krótkim raportem. Pozostałe blokady obowiązują bez zmian."]
    else:
        kontekst += ["", "Stanu nie zmieniasz i nie komentujesz go: przyjmij go i pracuj dalej."]
    wypisz({
        "systemMessage": f"{NAZWA_WTYCZKI}: {etykieta} — zapisano.\n" + opis,
        "hookSpecificOutput": {"hookEventName": zdarzenie.get("hook_event_name") or "UserPromptSubmit",
                               "additionalContext": "\n".join(kontekst)},
    })
    return 0


# --- przejmowanie sesji (wrapper na danaco-przejmij-sesje) ----------------------------------------

import shutil  # noqa: E402
import subprocess  # noqa: E402

#: Narzędzie systemowe; nadpisywalne w testach.
PRZEJMIJ_CMD = os.environ.get("DANACO_PRZEJMIJ_CMD", "danaco-przejmij-sesje")
BEZPIECZNY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,120}$")


def wywolaj_przejmij(argumenty: list[str]) -> str:
    sciezka = shutil.which(PRZEJMIJ_CMD) or (PRZEJMIJ_CMD if os.path.isabs(PRZEJMIJ_CMD) and os.path.exists(PRZEJMIJ_CMD) else None)
    if not sciezka:
        return (f"Nie znaleziono narzędzia `{PRZEJMIJ_CMD}` (działa tylko na danaco-nexus). "
                "Spis sesji wypiszesz w terminalu poleceniem `danaco-przejmij-sesje --lista`.")
    try:
        wynik = subprocess.run([sciezka, *argumenty], capture_output=True, text=True, timeout=25)
    except Exception as blad:  # noqa: BLE001
        return f"Nie udało się uruchomić `{PRZEJMIJ_CMD}`: {blad}"
    tekst = (wynik.stdout + ("\n" + wynik.stderr if wynik.stderr.strip() else "")).strip()
    return tekst[:6000] or "(brak wyniku)"


def przejmij_sesje(identyfikator: str) -> str:
    identyfikator = (identyfikator or "").strip()
    if not identyfikator:
        return ("Podaj identyfikator sesji: `/sesja-przejmij <id>` (ID bieżącej sesji pokaże `/sesja-id`, "
                "spis sesji — `/sesja-lista`).")
    if not BEZPIECZNY_ID.match(identyfikator):
        return f"Niepoprawny identyfikator sesji: {identyfikator!r}."
    wynik = wywolaj_przejmij([identyfikator])
    return ("Przejęcie sesji przygotowane. Dokończ je w terminalu poleceniem `wznowienie` poniżej "
            "(tej sesji Claude nie może wznowić sam):\n" + wynik)


# --- PreToolUse -----------------------------------------------------------------------------------

def zwiazane_ze_stanem(tekst: str, katalog: str) -> bool:
    if not tekst:
        return False
    dane = os.path.dirname(katalog)
    znaczniki = [katalog, "CLAUDE_PLUGIN_DATA", "DANACO_PRACA_STAN"]
    if os.path.basename(dane).startswith(NAZWA_WTYCZKI):
        znaczniki.append(dane)
    if any(z and z in tekst for z in znaczniki):
        return True
    # Katalog danych tej wtyczki pod dowolną nazwą instalacji, także maską (danaco-p*).
    return bool(re.search(r"plugins/data/(danaco-praca|[^/\s\"']*[*?\[])", tekst))


SCIEZKI_PLIKOWE = ("file_path", "notebook_path", "path")
NARZEDZIA_PLIKOWE = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def chroni_mechanizm(narzedzie: str, wejscie: dict, powloka: str | None, surowe: str, cwd: str = "") -> str | None:
    """Przy aktywnym trybie lub blokadzie: zakaz wyłączania wtyczki i hooków."""
    korzen = os.path.realpath(os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    konfiguracja = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    powod = ("Dopóki działa tryb lub blokada danaco-praca, nie zmieniasz wtyczki, jej hooków ani "
             "ustawień Claude Code ({}). Tryby przełącza wyłącznie właściciel")
    if "disableAllHooks" in surowe:
        return powod.format("disableAllHooks")
    chronione = re.compile(r"(^|/)\.claude/(settings(\.local)?\.json|plugins/)|managed-settings|/etc/claude-code")
    if narzedzie in NARZEDZIA_PLIKOWE:
        for pole in SCIEZKI_PLIKOWE:
            sciezka = str(wejscie.get(pole) or "")
            if not sciezka:
                continue
            pelna = os.path.realpath(os.path.join(cwd or "/", os.path.expanduser(sciezka)))
            konf = os.path.realpath(konfiguracja)
            if (pelna.startswith(korzen + os.sep) or chronione.search(pelna) or pelna.startswith(konf + "/plugins/")
                    or pelna in (konf + "/settings.json", konf + "/settings.local.json")):
                return powod.format(sciezka)
    if powloka:
        for r, _, _ in R.polecenia(powloka):
            if R.nazwa(r) in R.CLAUDE and len(r) > 2 and r[1] in ("plugin", "plugins") and r[2] in ("disable", "uninstall", "remove", "rm", "marketplace"):
                return powod.format(" ".join(r[:3]))
        if (korzen in powloka or chronione.search(powloka) or os.path.realpath(konfiguracja) + "/settings" in powloka) and R.tekst_zapisuje(powloka):
            return powod.format("zapis w plikach wtyczki lub ustawień")
    return None


def ocen_narzedzie(zdarzenie: dict, stan: dict, katalog: str) -> tuple[str, str] | None:
    """Decyzja wtyczki dla wywołania narzędzia: ('deny'|'ask', powód) albo None."""
    narzedzie = str(zdarzenie.get("tool_name") or "")
    wejscie = zdarzenie.get("tool_input") or {}
    if not isinstance(wejscie, dict):
        wejscie = {}
    cwd = str(zdarzenie.get("cwd") or "")
    surowe = json.dumps(wejscie, ensure_ascii=False)
    powloka = R.polecenie_powloki(narzedzie, wejscie)
    blokady = stan["blokady"]
    praca = stan["praca"]["wlaczona"]

    # 1. Stan trybów jest poza zasięgiem modelu — zawsze.
    if zwiazane_ze_stanem(surowe, katalog):
        return ("deny", "Stan trybów danaco-praca jest poza zasięgiem modelu: nie czytasz go i nie zmieniasz. "
                        "Stan pokazuje właścicielowi polecenie /tryb")
    # 2. Polecenia właściciela przełącza tylko właściciel: ani narzędzie Skill, ani podrzucony prompt.
    if narzedzie in ("Skill", "SlashCommand"):
        kanoniczna = P.kanon(str(wejscie.get("skill") or wejscie.get("command") or wejscie.get("name") or ""))
        if kanoniczna:
            return ("deny", f"/{kanoniczna} przełącza wyłącznie właściciel, wpisując polecenie na czacie")
    # Podrzucenie polecenia przez narzędzie wysyłające tekst albo w poleceniu powłoki — ale tylko
    # jako SAMODZIELNE polecenie (cały wiersz), a w powłoce dodatkowo gdy polecenie podaje token
    # agentowi (claude/codex). Zwykła wzmianka w ścieżce (`ls /praca`) czy w komunikacie commita
    # nie jest samodzielnym poleceniem i przechodzi. Z powłoki pomijamy treść dokumentów here.
    podrzucone = False
    if powloka is not None:
        oczyszczone = R.bez_heredoc(powloka)
        podrzucone = bool(P.rozpoznaj(oczyszczone)[0]) or (R.uruchamia_agenta(oczyszczone) and P.zawiera_token(oczyszczone))
    elif re.search(r"(?i)send|message|notif|terminal|prompt|slash|push", narzedzie):
        podrzucone = any(P.rozpoznaj(t)[0] for t in wartosci_tekstowe(wejscie))
    if podrzucone:
        return ("deny", "Polecenia trybów danaco-praca (/praca, /koniec-pracy, /blokuj-…, /odblokuj-…, /tryb, "
                        "/sesja-przejmij) wpisuje wyłącznie właściciel; nie przekazuj ich narzędziem ani poleceniem")
    # Polecenie powłoki zbyt duże, by je bezpiecznie przeanalizować: blokujemy, zamiast przepuścić
    # (dotyczy też straży sekretów i dysku, które muszą móc rozebrać polecenie).
    if powloka is not None and R.za_duze_do_analizy(powloka):
        return ("deny", "Polecenie jest zbyt duże, by je bezpiecznie sprawdzić pod kątem straży sekretów, "
                        "dysku i blokad danaco-praca. Podziel je na mniejsze kroki")
    if S.aktywne(stan):
        wynik = chroni_mechanizm(narzedzie, wejscie, powloka, surowe, cwd)
        if wynik:
            return ("deny", wynik)
        if powloka:
            wynik = R.wznowienie_sesji(powloka)
            if wynik:
                return ("deny", wynik)
    # 3. Blokady sesji.
    if blokady["bash"] and (narzedzie in ("Bash", "PowerShell", "Monitor") or (powloka is not None and narzedzie.startswith("mcp__"))):
        return ("deny", f"Narzędzie {narzedzie} jest zablokowane poleceniem właściciela /blokuj-bash. "
                        "Pracuj narzędziami Read, Grep, Glob, Edit i Write")
    if blokady["podagenci"]:
        wynik = R.blokada_podagentow_narzedzie(narzedzie) or (R.blokada_podagentow_powloka(powloka) if powloka else None)
        if wynik:
            return ("deny", wynik)
    if praca or blokady["sleep"]:
        scisle = blokady["sleep"]
        wynik = (R.blokada_czekania_narzedzie(narzedzie, wejscie, scisle)
                 or (R.blokada_czekania(powloka, wejscie, scisle) if powloka and narzedzie != "Monitor" else None))
        if wynik:
            zrodlo = "/praca" if praca and not blokady["sleep"] else "/blokuj-sleep"
            return ("deny", f"{wynik} [{zrodlo}]")
    if blokady["python"]:
        wynik = R.blokada_python_plik(narzedzie, wejscie) or (R.blokada_python(powloka, cwd) if powloka else None)
        if wynik:
            return ("deny", wynik)
    if blokady["pytania"] and narzedzie in ("AskUserQuestion", "ExitPlanMode"):
        return ("deny", "Pytania do właściciela są wstrzymane poleceniem /blokuj-pytania: przyjmij "
                        "najrozsądniejsze założenie, zanotuj je i pracuj dalej")
    if blokady["siec"]:
        if narzedzie in ("WebFetch", "WebSearch"):
            return ("deny", f"Sieć jest zablokowana poleceniem właściciela /blokuj-siec (narzędzie {narzedzie}). "
                            "Pracuj na danych lokalnych; dostęp do sieci wróci po /odblokuj-siec")
        if powloka:
            wynik = R.blokada_sieci(powloka)
            if wynik:
                return ("deny", wynik)
    if blokady["zapis"]:
        if narzedzie in NARZEDZIA_PLIKOWE:
            return ("deny", "Tryb tylko-odczyt jest włączony poleceniem właściciela /blokuj-zapis "
                            f"(narzędzie {narzedzie}). Oglądaj i analizuj; pliki zmienisz po /odblokuj-zapis")
        if powloka:
            wynik = R.blokada_zapisu(powloka)
            if wynik:
                return ("deny", wynik)
    if powloka:
        if blokady["sudo"]:
            wynik = R.blokada_sudo(powloka)
            if wynik:
                return ("deny", wynik)
        if blokady["masowe"]:
            wynik = R.blokada_masowa(powloka, cwd, LIMIT_PLIKOW)
            if wynik:
                return ("deny", wynik)
        if blokady["reczne"]:
            wynik = R.blokada_reczna(powloka, cwd)
            if wynik:
                return ("deny", wynik)
    # 4. Twarde zasady serwera: sekrety i dysk systemowy — dla KAŻDEGO narzędzia, zawsze.
    return twarde_zasady(narzedzie, wejscie, cwd, powloka)


#: Narzędzia odczytu, przez które model mógłby wypisać zawartość pliku z sekretem.
NARZEDZIA_ODCZYTU = {"Read", "NotebookRead"}
#: Pola narzędzi MCP, które wskazują pliki wejściowe (wysyłane do programu) — np. danaco-programy.
MCP_POLA_PLIKOW = ("pliki", "files", "paths", "input_files")


def cele_zapisu_narzedzia(narzedzie: str, wejscie: dict) -> list[str]:
    """Ścieżki, do których narzędzie zapisuje: pliki narzędzi plikowych i wyniki programów MCP."""
    cele: list[str] = []
    if narzedzie in NARZEDZIA_PLIKOWE:
        cele += [str(wejscie.get(p)) for p in SCIEZKI_PLIKOWE if wejscie.get(p)]
    if narzedzie.startswith("mcp__"):
        for pole in ("wyniki_do", "output", "out", "plik", "sciezka", "path", "file_path"):
            if isinstance(wejscie.get(pole), str) and wejscie[pole]:
                cele.append(wejscie[pole])
    return cele


def twarde_zasady(narzedzie: str, wejscie: dict, cwd: str, powloka: str | None) -> tuple[str, str] | None:
    """Zasady serwera egzekwowane dla KAŻDEGO narzędzia: sekrety i dysk systemowy.

    Nie ograniczają się do Bash i Write — polecenie powłoki dowolnego narzędzia (Monitor,
    PowerShell, MCP `uruchom` z polem `polecenie`) przechodzi przez straż sekretów i dysku,
    odczyt pliku z sekretem (Read) jest odrzucany, a pliki wejściowe programów MCP nie mogą
    wynieść sekretu poza plik 600.
    """
    import straz_dysku
    import straz_sekretow

    straz_sekretow.KATALOG["cwd"] = cwd
    straz_dysku.KATALOG["cwd"] = cwd
    najostrzejsza = None

    # Sekrety w poleceniu powłoki dowolnego narzędzia.
    if powloka is not None:
        wynik = straz_sekretow.ocen(powloka)
        if wynik:
            if wynik[0] == "deny":
                return ("deny", f"Straż sekretów Danaco: {wynik[1]}")
            najostrzejsza = ("ask", f"Straż sekretów Danaco: {wynik[1]}")

    # Odczyt pliku z sekretem narzędziem odczytu (Read, NotebookRead).
    if narzedzie in NARZEDZIA_ODCZYTU:
        for pole in SCIEZKI_PLIKOWE:
            sciezka = str(wejscie.get(pole) or "")
            if sciezka and straz_sekretow.sciezka_sekretu(sciezka):
                return ("deny", f"Straż sekretów Danaco: odczyt {sciezka} wypisałby sekret do rozmowy. "
                                "Sekrety zostają w plikach 600; sprawdź obecność klucza bez wartości")

    # Pliki wejściowe programów MCP: nie wynoś sekretu poza plik 600.
    if narzedzie.startswith("mcp__"):
        for pole in MCP_POLA_PLIKOW:
            for sciezka in (wejscie.get(pole) or []):
                if isinstance(sciezka, str) and sciezka and straz_sekretow.sciezka_sekretu(sciezka):
                    return ("deny", f"Straż sekretów Danaco: przez {narzedzie} wysyłasz plik z sekretem "
                                    f"({sciezka}) poza plik 600. Nie przekazuj sekretów do programów")

    # Dysk systemowy: polecenie powłoki dowolnego narzędzia.
    if powloka is not None:
        wynik = straz_dysku.ocen(powloka)
        if wynik:
            return (wynik[0], f"Straż dysku systemowego Danaco: {wynik[1]}")

    # Dysk systemowy: cele zapisu narzędzi plikowych i MCP.
    for sciezka in cele_zapisu_narzedzia(narzedzie, wejscie):
        wynik = straz_dysku.ocen_zapis_pliku(sciezka)
        if wynik:
            return (wynik[0], f"Straż dysku systemowego Danaco: {wynik[1]}")
    return najostrzejsza


def obsluz_narzedzie(zdarzenie: dict) -> int:
    sesja = S.bezpieczna_sesja(zdarzenie.get("session_id"))
    magazyn = S.Magazyn()
    stan = magazyn.wczytaj(sesja)
    wynik = ocen_narzedzie(zdarzenie, stan, magazyn.katalog)
    if not wynik:
        return 0
    decyzja, powod = wynik
    if S.aktywne(stan) or decyzja == "deny":
        try:
            magazyn.dopisz({"zdarzenie": "odmowa" if decyzja == "deny" else "pytanie", "sesja": sesja,
                            "narzedzie": zdarzenie.get("tool_name"), "agent": zdarzenie.get("agent_id"),
                            "powod": powod[:300]})
        except OSError:
            pass
    wypisz({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decyzja,
                                   "permissionDecisionReason": powod + "."}})
    return 0


# --- Stop -----------------------------------------------------------------------------------------

#: Pola, którymi klient mógłby zasygnalizować nieobsłużone wejście właściciela w hooku Stop.
#: Klient 2.1.287 ich nie przekazuje — honorujemy je, gdy się pojawią (zgodność w przód).
POLA_WEJSCIA_WLASCICIELA = ("pending_user_input", "has_queued_input", "queued_messages",
                            "user_input_pending", "pending_input")


def _wejscie_wlasciciela(zdarzenie: dict) -> bool:
    for klucz in POLA_WEJSCIA_WLASCICIELA:
        wartosc = zdarzenie.get(klucz)
        if isinstance(wartosc, bool) and wartosc:
            return True
        if isinstance(wartosc, (list, str, int)) and not isinstance(wartosc, bool) and wartosc:
            return True
    return False


def _oddaj_ture(magazyn, sesja: str, stan: dict, powod_dziennika: str) -> int:
    """Kończy turę (brak decyzji), zerując licznik oddań. Tryb /praca zostaje włączony."""
    stan["praca"]["oddania"] = 0
    magazyn.zapisz(stan, None)
    magazyn.dopisz({"zdarzenie": "oddanie-tury", "sesja": sesja, "powod": powod_dziennika})
    wypisz({"systemMessage": (
        f"{NAZWA_WTYCZKI}: tryb /praca oddaje turę, żeby właściciel mógł wpisać wiadomość — zostanie "
        "odczytana od razu. Tryb jest nadal WŁĄCZONY i wznowi pracę ciągłą na następnej turze (po "
        "wiadomości właściciela; samo „kontynuuj” wystarczy). Wyłącza go tylko /koniec-pracy.")})
    return 0


def obsluz_stop(zdarzenie: dict) -> int:
    """Praca ciągła: hook Stop nie pozwala agentowi skończyć tury z własnej woli, ale okresowo
    sam oddaje turę, żeby właściciel zawsze mógł wysłać wiadomość i mieć ją odczytaną natychmiast.

    Jedynym wyłączeniem trybu jest /koniec-pracy; oddanie tury trybu nie wyłącza — tryb wznawia
    się na następnej turze (UserPromptSubmit/SessionStart). Gdy klient zasygnalizuje nieobsłużone
    wejście właściciela, oddajemy turę od razu; w przeciwnym razie co PROG_ODDANIA prób zakończenia.
    Tryb wiąże wyłącznie agenta głównego — podagent oddaje wynik normalnie (SubagentStop nie jest
    rejestrowany, decyzja właściciela z 2026-10-02)."""
    if zdarzenie.get("hook_event_name") == "SubagentStop" or zdarzenie.get("agent_id"):
        return 0
    sesja = S.bezpieczna_sesja(zdarzenie.get("session_id"))
    magazyn = S.Magazyn()
    if not magazyn.wczytaj(sesja)["praca"]["wlaczona"]:
        return 0
    with magazyn.blokada():
        stan = magazyn.wczytaj(sesja)
        if not stan["praca"]["wlaczona"]:
            return 0
        if _wejscie_wlasciciela(zdarzenie):
            # Klient wie o wiadomości właściciela: oddaj turę od razu, żeby została odczytana.
            return _oddaj_ture(magazyn, sesja, stan, "wejscie-wlasciciela")
        oddania = int(stan["praca"].get("oddania", 0)) + 1
        if oddania >= PROG_ODDANIA:
            # Okresowe oddanie tury: hook nie widzi kolejki wejścia, więc gwarantuje właścicielowi
            # okno na wiadomość, zamiast trzymać turę w nieskończoność.
            return _oddaj_ture(magazyn, sesja, stan, f"prog-{oddania}")
        stan["praca"]["oddania"] = oddania
        magazyn.zapisz(stan, None)
    zlecenie = (stan["praca"].get("zlecenie") or "").strip()
    powod = ("Tryb pracy ciągłej (/praca) jest włączony przez właściciela — nie kończ tury. Kontynuuj zadanie"
             + (f": {zlecenie[:1500]}" if zlecenie else "")
             + ". Weź następny krok: sprawdź wyniki procesów w tle, zweryfikuj i przetestuj zrobione części, "
             "popraw błędy, uzupełnij dokumentację albo podejmij kolejną część zlecenia. Nie czekaj i nie "
             "pytaj; tryb zwalnia wyłącznie właściciel poleceniem /koniec-pracy.")
    wypisz({"decision": "block", "reason": powod})
    return 0


# --- SessionStart / SubagentStart -----------------------------------------------------------------

def obsluz_sesje(zdarzenie: dict) -> int:
    sesja = S.bezpieczna_sesja(zdarzenie.get("session_id"))
    stan = S.Magazyn().wczytaj(sesja)
    if not S.aktywne(stan):
        return 0
    tekst = [f"[{NAZWA_WTYCZKI}] W tej sesji obowiązują tryby ustawione przez właściciela:", S.opis_stanu(stan)]
    if stan["praca"]["wlaczona"] and zdarzenie.get("hook_event_name") == "SubagentStart":
        tekst += ["", "Tryb pracy ciągłej wiąże agenta głównego. Ty jako podagent wykonujesz zlecone zadanie "
                      "i oddajesz wynik normalnie; nie czekasz i nie usypiasz (sleep, wait, ScheduleWakeup)."]
    elif stan["praca"]["wlaczona"]:
        tekst += ["", ZASADY_PRACY]
        if stan["praca"]["zlecenie"]:
            tekst += ["Zlecenie: " + stan["praca"]["zlecenie"]]
    wypisz({"hookSpecificOutput": {"hookEventName": zdarzenie.get("hook_event_name") or "SessionStart",
                                   "additionalContext": "\n".join(tekst)}})
    return 0


TRYBY = {"prompt": obsluz_polecenia, "narzedzie": obsluz_narzedzie, "stop": obsluz_stop, "sesja": obsluz_sesje}


def main(argv: list[str]) -> int:
    tryb = argv[1] if len(argv) > 1 else ""
    obsluga = TRYBY.get(tryb)
    if obsluga is None:
        print(f"[{NAZWA_WTYCZKI}] nieznany tryb hooka: {tryb!r}", file=sys.stderr)
        return 0
    try:
        zdarzenie = json.load(sys.stdin)
        if not isinstance(zdarzenie, dict):
            return 0
        return obsluga(zdarzenie)
    except Exception:  # noqa: BLE001 — usterka hooka nie może zamknąć sesji
        if os.environ.get("DANACO_PRACA_DEBUG"):
            traceback.print_exc()
        else:
            print(f"[{NAZWA_WTYCZKI}] błąd hooka {tryb}: {sys.exc_info()[1]!r}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
