#!/usr/bin/env python3
"""Znacznik zadania w toku (zadanie.py) — zamknięcie decyduje CZŁOWIEK, nie model.

Polecenia: `start`, `krok`, `status`, `diagnoza`, `zakoncz`. Tryb ciągłej pracy włącza
jawna komenda użytkownika `/pracuj` (albo `/danaco-praca:pracuj`, albo stare
`/danaco-plugin:pracuj`), a znacznik zakłada wtedy HOOK `UserPromptSubmit`, nie model:
dopóki robił to model poleceniem `start`, pominięcie tego kroku albo uruchomienie go
w innym katalogu cicho wyłączało cały mechanizm. `start` zostaje jako droga dla
człowieka uruchamiana z terminala. Zakończenie należy do CZŁOWIEKA: hooki pluginu (`scripts/straznik.py`
wołany przez `hooks/straznik.sh`) zdejmują znacznik na podstawie danych, których
model nie kontroluje - polecenia `/stop` (albo `/danaco-praca:stop`, albo starego `/danaco-plugin:stop`) we wpisie
użytkownika na czacie. `zakoncz` to awaryjne wyjście dla człowieka poza sesją
(zapomniany znacznik blokowałby każdą późniejszą sesję w tym poddrzewie); hook
`PreToolUse` odrzuca jego uruchomienie z wnętrza sesji, więc dla modelu jest
niedostępne. Trzecia droga to termin ważności znacznika (`--limit-godzin`,
domyślnie 24 h), po którym blokada zdejmuje się sama.

Warstwy blokady technicznej, gdy znacznik istnieje (szczegóły w
`scripts/straznik.py` i `hooks/hooks.json`):

    UserPromptSubmit  — jedyna zwykła droga zwolnienia. Gdy wiadomość użytkownika
                        (pole `prompt` zdarzenia) zawiera polecenie `/stop`, hook
                        usuwa znacznik. Tego zdarzenia model nie może wywołać —
                        powstaje wyłącznie z wpisu człowieka na czacie.
    Stop              — blokuje zakończenie tury (kod 2). Zwalnia tylko wtedy, gdy
                        w prawdziwej transkrypcji (`transcript_path`) znajdzie
                        wiadomość o roli `user` (nie wynik narzędzia, nie wpis
                        modelu) z poleceniem `/stop`, wysłaną PO założeniu
                        znacznika. Sprawdza też termin ważności. Każda sytuacja,
                        której nie umie ocenić (brak pola, nieczytelny plik,
                        zepsute zdarzenie, brak interpretera) = blokada.
    PreToolUse        — blokuje `AskUserQuestion` (model nie ma prawa pytać),
                        narzędzia harmonogramu i wybudzania, zapisy do `.danaco/`,
                        plików mechanizmu w katalogu pluginu i konfiguracji Claude
                        Code (`.claude/settings*.json`, `.claude/plugins/`), zapisy
                        poza katalogiem zlecenia oraz — heurystycznie — polecenia
                        Bash/PowerShell, które dotykają tych plików, wyłączają
                        hooki/plugin albo kasują cały katalog roboczy. Odrzuca też
                        polecenia długotrwałe uruchamiane na pierwszym planie.
    PreCompact        — nie blokuje kompresji: zapisuje stan zlecenia do
                        `.danaco/stan-zlecenia.md` i przypomina, że tryb trwa.
    SessionStart      — nie blokuje niczego: podaje opis zlecenia i zapisany stan
                        po kompresji oraz przy wznowieniu sesji.

Plik znacznika (`.danaco/zadanie-w-toku.json`) pamięta OPIS zlecenia, czas
rozpoczęcia, katalog zlecenia, identyfikator sesji, token wiążący, termin ważności
i dziennik kroków. Własność rozstrzyga token wypisywany przez `start` na stdout: trafia
do transkrypcji tej sesji, która polecenie uruchomiła, więc inne sesje otwarte w tym
samym katalogu tryb pomijają. Kopia znacznika trafia do `~/.danaco-kopie/` (uprawnienia
600), skąd hook PostToolUse odtwarza go po skasowaniu. Zapisy są atomowe.

Polecenia:
    zadanie.py start "opis zlecenia" [--limit-godzin N]
        Zakłada znacznik w `.danaco/` KORZENIA PROJEKTU, nie bieżącego katalogu:
        korzeń wyznacza kolejno `CLAUDE_PROJECT_DIR`, najbliższy katalog z `.git`,
        a w ostatniej kolejności katalog roboczy. Znacznik założony w podkatalogu
        byłby niewidoczny dla hooka wołanego z korzenia, więc blokada cicho
        przestawałaby działać. Katalog domowy i korzeń systemu plików są odrzucane
        — znacznik obowiązuje w całym poddrzewie, więc w `~` blokowałby wszystkie
        projekty. Katalog znacznika wyznacza zarazem zakres zlecenia: zapisy poza
        nim są odrzucane. `--limit-godzin` ustawia termin ważności w przedziale 1-24 h
        (domyślnie 24); `0` (bezterminowo) wolno wyłącznie poza sesją modelu, z flagą
        `--poza-sesja`.

    zadanie.py krok "co zrobiono"
        Dopisuje krok do dziennika (informacyjne, tylko do wglądu, niczego nie
        zamyka). Tu model zapisuje też przyjęte założenia — zamiast pytać.

    zadanie.py status
        Czytelny stan trybu: czy aktywny w tym katalogu, gdzie leży znacznik, do jakiej
        sesji należy, kiedy wygasa, ile było blokad zakończenia tury.

    zadanie.py diagnoza
        Czy mechanizm w tym katalogu w ogóle zadziała: widoczność pluginu w konfiguracji
        Claude Code, interpreter Pythona osiągalny dla powłoki hooków, miejsce
        poszukiwania znacznika i wynik, jaki zwróciłby tu hook `Stop` (0 albo 2).

Celowo NIE ma tu bezpiecznika w postaci limitu prób ani zmiennej środowiskowej
zdejmującej blokadę — użytkownik wyzwala pracę (komendą `/pracuj`) i użytkownik ją
kończy (poleceniem `/stop` na czacie), nie automat i nie model. Jedynym wyjątkiem
jest termin ważności znacznika.

Osobnym, niezależnym mechanizmem jest blokada podagentów: polecenie użytkownika
`/blokada` wyłącza narzędzia `Task`, `Agent` i `Workflow` (także w tle) najwyżej na
12 godzin albo do `/blokada-stop`; stan leży w `.danaco/blokada-subagentow.json`,
a opis w paczce `skills/blokada`.

Ograniczenia, których ten skrypt nie usuwa (opisane uczciwie w README): znacznik i
pliki pluginu leżą na dysku zapisywalnym dla procesu modelu; hook PreToolUse
zatrzymuje typowe próby ich usunięcia lub edycji, ale to filtr heurystyczny —
pełną barierę dają dopiero uprawnienia systemowe poza zasięgiem pluginu. Awaryjne
zdjęcie blokady przez CZŁOWIEKA poza sesją: usuń katalog `.danaco` w katalogu
projektu (np. z innego terminala).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import znacznik  # noqa: E402

for _strumien in (sys.stdout, sys.stderr):
    # Komunikaty mają polskie znaki; na Windows domyślne kodowanie potoku (cp1250)
    # psułoby je w wyjściu narzędzia Bash.
    try:
        _strumien.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _zglos_istniejacy(katalog: Path) -> int:
    dane = znacznik.wczytaj_znacznik(katalog) or {}
    print(
        f"Znacznik już istnieje w {katalog} (opis: {dane.get('opis', '?')!r}). "
        "To zadanie zamyka wyłącznie Twoje polecenie "
        f"{znacznik.POLECENIE_ZAKONCZENIA} na czacie - jeśli to nowe, niezwiązane "
        "zlecenie, zakończ najpierw poprzednie.",
        file=sys.stderr,
    )
    return 1


def _korzen_dla_znacznika() -> Path | None:
    """Korzeń projektu albo None, gdy znacznika nie wolno tam zakładać."""
    korzen = znacznik.korzen_projektu()
    if znacznik.poza_granica(korzen):
        print(
            f"Odmowa założenia znacznika w {korzen}: znacznik obowiązuje w całym "
            "poddrzewie, więc w katalogu domowym lub w korzeniu systemu plików "
            "zablokowałby wszystkie projekty. Uruchom polecenie w katalogu projektu.",
            file=sys.stderr,
        )
        return None
    if not znacznik.korzen_wyznaczony_deterministycznie():
        print(
            f"Korzeń projektu nie jest wyznaczony ani przez {znacznik.ZMIENNA_KATALOGU_PROJEKTU}, "
            f"ani przez katalog {znacznik.NAZWA_KATALOGU_GIT} - znacznik trafia do katalogu "
            f"roboczego ({korzen}).",
            file=sys.stderr,
        )
    elif korzen != znacznik.katalog_roboczy():
        print(f"Znacznik zakładany w korzeniu projektu ({korzen}), nie w {znacznik.katalog_roboczy()}.",
              file=sys.stderr)
    return korzen


MIN_LIMIT_GODZIN = 1
MAX_LIMIT_GODZIN = 24


def poza_sesja_modelu() -> bool:
    """Czy polecenie działa poza sesją modelu — oceniane po czymś, czego model nie
    ustawia: braku zmiennych wstrzykiwanych przez klienta (CLAUDE_PLUGIN_ROOT,
    CLAUDE_PROJECT_DIR) albo interaktywnym terminalu na standardowym wejściu.
    Sama flaga --poza-sesja jest deklaracją wywołującego, więc nie wystarcza."""
    if os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get(znacznik.ZMIENNA_KATALOGU_PROJEKTU):
        try:
            return bool(sys.stdin.isatty())
        except (OSError, ValueError):
            return False
    return True


def _limit_dozwolony(limit_godzin: float, poza_sesja: bool) -> str | None:
    """Komunikat odmowy albo None. Model nie może skrócić terminu do sekund ani
    założyć znacznika bezterminowego: `0` wymaga zarówno flagi --poza-sesja, jak i
    dowodu spoza sesji (patrz `poza_sesja_modelu`)."""
    if limit_godzin == 0:
        if poza_sesja and poza_sesja_modelu():
            return None
        return ("Znacznik bezterminowy (--limit-godzin 0) zakłada wyłącznie człowiek poza "
                "sesją modelu: uruchom polecenie z flagą --poza-sesja we własnym terminalu "
                "(bez zmiennych CLAUDE_PLUGIN_ROOT i CLAUDE_PROJECT_DIR albo z terminalem "
                "interaktywnym).")
    if not MIN_LIMIT_GODZIN <= limit_godzin <= MAX_LIMIT_GODZIN:
        return (f"Wartość --limit-godzin poza dozwolonym przedziałem "
                f"{MIN_LIMIT_GODZIN}-{MAX_LIMIT_GODZIN} h: {limit_godzin}.")
    return None


def polecenie_start(opis: str, limit_godzin: float, poza_sesja: bool = False) -> int:
    odmowa = _limit_dozwolony(limit_godzin, poza_sesja)
    if odmowa:
        print(odmowa, file=sys.stderr)
        return 1
    if not opis.strip():
        print("Opis zlecenia jest wymagany: bez niego komunikat blokady nie mówi, "
              "nad czym model ma pracować.", file=sys.stderr)
        return 1

    istniejacy = znacznik.znajdz_katalog_znacznika()
    if istniejacy is not None:
        return _zglos_istniejacy(istniejacy)

    korzen = _korzen_dla_znacznika()
    if korzen is None:
        return 1

    katalog = korzen / znacznik.NAZWA_KATALOGU
    # Token wiążący: wypisany na stdout trafia do transkrypcji tej sesji, która
    # uruchomiła `start`, i to on rozstrzyga własność znacznika. Zmienna
    # CLAUDE_SESSION_ID zwykle nie istnieje, więc wiązanie po niej nie działało.
    dane = znacznik.utworz_dane_zlecenia(korzen, opis, "", limit_godzin)
    token = dane["token"]
    wygasa = dane["wygasa"]
    kopia_zapisana = znacznik.zapisz_kopie(katalog, dane)
    znacznik.zapisz_znacznik(katalog, dane)
    posprzatane = znacznik.posprzataj_kopie()

    print(f"Znacznik założony: {opis!r} (katalog: {katalog}).")
    if not kopia_zapisana:
        print("Uwaga: nie udało się zapisać kopii znacznika poza katalogiem projektu - "
              "skasowanie pliku znacznika poleceniem powłoki nie zostanie odtworzone.")
    if posprzatane:
        print(f"Sprzątnięto stare kopie zleceń: {posprzatane} "
              f"(starsze niż {znacznik.DNI_WAZNOSCI_KOPII} dni).")
    print(f"Token zlecenia: {token}")
    print(
        f"Tura nie zakończy się, dopóki Ty (nie model) nie wpiszesz na czacie "
        f"{znacznik.POLECENIE_ZAKONCZENIA!r}. Model nie może zamknąć tego sam."
    )
    print(
        "Wiadomości pisz normalnie na czacie - klient dostarcza je modelowi na granicy "
        "najbliższego wywołania narzędzia, a tryb wymusza, żeby model nie czekał na "
        "pierwszym planie, więc te granice są częste."
    )
    if wygasa:
        print(f"Termin ważności znacznika: {wygasa} (za {limit_godzin} h). Po tym czasie blokada zdejmuje się sama.")
    else:
        print(f"Znacznik bez terminu ważności (--limit-godzin 0): zdejmie go wyłącznie polecenie "
              f"{znacznik.POLECENIE_ZAKONCZENIA} na czacie albo `zadanie.py zakoncz` uruchomione "
              "przez Ciebie poza sesją.")
    return 0


def polecenie_zakoncz() -> int:
    """Awaryjne zdjęcie znacznika przez CZŁOWIEKA, uruchamiane poza sesją modelu.

    Pierwsza wersja pluginu nie miała tego polecenia z obawy, że model sam się nim
    zwolni. Praktyka pokazała odwrotny problem: zapomniany znacznik blokuje wszystkie
    późniejsze sesje w tym poddrzewie, a jedyną drogą wyjścia jest ręczne kasowanie
    plików. Polecenie zostaje więc dodane, ale hook `PreToolUse` odrzuca jego
    uruchomienie z wnętrza sesji - dla modelu jest niedostępne."""
    katalog = znacznik.znajdz_katalog_znacznika()
    if katalog is None:
        print("Brak aktywnego znacznika - nie ma czego zdejmować.")
        return 0
    if znacznik.usun_znacznik(katalog):
        print(f"Znacznik zdjęty ({katalog}). Tryb ciągłej pracy jest wyłączony.")
        return 0
    print(f"Nie udało się usunąć znacznika w {katalog} - skasuj ten katalog ręcznie.", file=sys.stderr)
    return 1


def polecenie_krok(tekst: str) -> int:
    katalog = znacznik.znajdz_katalog_znacznika()
    dane = znacznik.wczytaj_znacznik(katalog) if katalog is not None else None
    if katalog is None or dane is None:
        print("Brak aktywnego znacznika — nie ma czego uzupełniać krokiem.", file=sys.stderr)
        return 1
    kroki = dane.get("kroki")
    if not isinstance(kroki, list):
        kroki = []
    kroki.append({"czas": znacznik.teraz(), "tekst": tekst})
    dane["kroki"] = kroki
    znacznik.zapisz_znacznik(katalog, znacznik.ogranicz_dziennik(dane))
    print("Krok odnotowany.")
    return 0


def _pozostalo(wygasa: str) -> str:
    """Ile czasu zostało do terminu ważności, po ludzku."""
    termin = znacznik.parsuj_czas(wygasa)
    if termin is None:
        return "bezterminowo (brak pola `wygasa`)"
    sekundy = (termin - datetime.now(timezone.utc)).total_seconds()
    if sekundy <= 0:
        return f"{wygasa} - termin już minął, blokada zdejmie się przy najbliższym hooku"
    godziny = int(sekundy // 3600)
    minuty = int((sekundy % 3600) // 60)
    return f"{wygasa} (za {godziny} h {minuty} min)"


def _wypisz_blokady() -> None:
    """Stan blokad niezależnych od zlecenia: podagentów i pracy maszynowej.

    Obie zakłada i zdejmuje wyłącznie użytkownik komendą na czacie, ale z terminala
    nie widać identyfikatora rozmowy, więc pokazujemy sam plik."""
    katalog = znacznik.katalog_blokady()
    podagenci = znacznik.wczytaj_blokade(katalog)
    skrypty = znacznik.wczytaj_blokade_skryptow(katalog)
    if podagenci:
        print(f"Blokada podagentów: WŁĄCZONA (sesja: {podagenci.get('sesjaId') or '?'}, "
              f"wygasa: {podagenci.get('wygasa') or 'bezterminowo'}). Zdejmuje /blokada-stop.")
    else:
        print("Blokada podagentów: wyłączona (włącza /blokada).")
    if skrypty:
        print(f"Blokada pracy maszynowej: WŁĄCZONA (sesja: {skrypty.get('sesjaId') or '?'}, "
              f"od: {skrypty.get('wlaczono') or '?'}). Zdejmuje /skrypt.")
    else:
        print("Blokada pracy maszynowej: wyłączona (włącza /stop-skrypt).")


def polecenie_raport() -> int:
    """Raport z dziennika pracy: co model wywołał w zleceniach tego katalogu."""
    katalog = znacznik.znajdz_katalog_znacznika() or (
        znacznik.korzen_projektu() / znacznik.NAZWA_KATALOGU)
    try:
        dzienniki = sorted(znacznik.katalog_zadan(katalog).glob(
            f"{znacznik.PRZEDROSTEK_DZIENNIKA_PRACY}-*.jsonl"))
    except OSError:
        dzienniki = []
    if not dzienniki:
        print(f"Brak dziennika pracy w {katalog}. Dziennik powstaje przy pierwszym "
              "wywołaniu narzędzia w trybie ciągłej pracy.")
        return 1
    for plik in dzienniki:
        sesja = plik.stem[len(znacznik.PRZEDROSTEK_DZIENNIKA_PRACY) + 1:]
        print(f"--- rozmowa {sesja} ---")
        wiersze = znacznik.podsumowanie_pracy(katalog, sesja)
        for wiersz in wiersze or ["(dziennik pusty albo nieczytelny)"]:
            print(wiersz)
    return 0


def polecenie_status() -> int:
    """Czytelny stan trybu dla CZŁOWIEKA: czy działa tu i teraz, czyj jest znacznik,
    kiedy wygasa. Surowy JSON niczego użytkownikowi nie mówił."""
    katalog = znacznik.znajdz_katalog_znacznika()
    dane = znacznik.wczytaj_znacznik(katalog) if katalog is not None else None
    if katalog is None or dane is None:
        katalog_sesyjny = katalog or (znacznik.korzen_projektu() / znacznik.NAZWA_KATALOGU)
        if znacznik.sesje_zlecen(katalog_sesyjny):
            # Od 4.0.0 zlecenia są sesyjne. Z terminala nie widać identyfikatora
            # bieżącej rozmowy, więc pokazujemy wszystkie zlecenia tego katalogu.
            print(f"Tryb ciągłej pracy: AKTYWNY w tym katalogu dla wymienionych rozmów "
                  f"({katalog_sesyjny}).")
            _wypisz_zlecenia_sesyjne(katalog_sesyjny)
            print("Każde zlecenie obowiązuje wyłącznie swoją rozmowę; kończy je polecenie "
                  f"{znacznik.POLECENIE_ZAKONCZENIA} napisane w TEJ rozmowie.")
            _wypisz_blokady()
            return 0
        print("Tryb ciągłej pracy: NIEAKTYWNY w tym katalogu.")
        print(f"Katalog roboczy: {znacznik.katalog_roboczy()}")
        print(f"Korzeń projektu: {znacznik.korzen_projektu()}")
        print(f"Znacznik zakładałby się w: "
              f"{znacznik.korzen_projektu() / znacznik.NAZWA_KATALOGU / znacznik.NAZWA_ZNACZNIKA}")
        print(f"Włącza go polecenie {znacznik.POLECENIE_ROZPOCZECIA} napisane na czacie "
              "(znacznik zakłada hook, nie model).")
        _wypisz_blokady()
        return 1

    kroki = dane.get("kroki") if isinstance(dane.get("kroki"), list) else []
    sesja = znacznik.sesja_znacznika(dane) or "(jeszcze niezwiązany z sesją)"
    print("Tryb ciągłej pracy: AKTYWNY.")
    print(f"Zlecenie: {dane.get('opis') or '(bez opisu)'}")
    print(f"Znacznik: {katalog / znacznik.NAZWA_ZNACZNIKA}")
    print(f"Zakres zapisów: {dane.get('katalogProjektu') or '(nieznany)'}")
    print(f"Sesja właściciela: {sesja}")
    print(f"Założone: {dane.get('rozpoczeto') or '(bez daty)'}")
    print(f"Wygasa: {_pozostalo(str(dane.get('wygasa') or ''))}")
    print(f"Blokad zakończenia tury: {dane.get('prob', 0)}")
    print(f"Zapisanych kroków: {len(kroki)} (pominiętych: {dane.get('krokowPominietych', 0)})")
    for krok in kroki[-5:]:
        if isinstance(krok, dict):
            print(f"  - {krok.get('czas', '?')}: {krok.get('tekst', '')}")
    print(f"Zamyka wyłącznie Twoje polecenie {znacznik.POLECENIE_ZAKONCZENIA} na czacie.")
    _wypisz_blokady()
    return 0


def _wypisz_zlecenia_sesyjne(katalog) -> None:
    """Lista zleceń sesyjnych w tym katalogu (od 4.0.0 może ich być kilka naraz)."""
    pliki = [n for n in znacznik.sesje_zlecen(katalog) if n != znacznik.NAZWA_ZNACZNIKA]
    if not pliki:
        return
    print(f"Zleceń sesyjnych w tym katalogu: {len(pliki)}")
    for nazwa in pliki:
        dane = None
        try:
            dane = json.loads((znacznik.katalog_zadan(katalog) / nazwa).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if not isinstance(dane, dict):
            print(f"  - {nazwa}: plik nieczytelny")
            continue
        print(f"  - {nazwa}: {dane.get('opis') or '(bez opisu)'} "
              f"(sesja: {dane.get('sesjaId') or 'nieprzypisana'}, wygasa: {dane.get('wygasa') or 'bezterminowo'})")


def _konfiguracje_klienta() -> list[Path]:
    """Pliki, w których widać zainstalowany plugin. Poza konfiguracją Claude Code
    w terminalu (`settings.json`, `~/.claude.json`) obejmują rejestr pluginów
    synchronizowanych z konta - w Cowork i w aplikacji desktopowej plugin nie ma
    wpisu w żadnym pliku ustawień, a jedynie w `plugins/**/manifest.json`; bez tego
    diagnoza zgłaszała brak wpisu przy działającym pluginie."""
    dom = znacznik.katalog_domowy()
    kandydaci = [znacznik.korzen_projektu() / ".claude" / "settings.json",
                 znacznik.korzen_projektu() / ".claude" / "settings.local.json"]
    if dom is None:
        return kandydaci
    kandydaci += [dom / ".claude.json", dom / ".claude" / "settings.json"]
    katalog_pluginow = dom / ".claude" / "plugins"
    try:
        for wzorzec in ("config.json", "manifest.json", "*/manifest.json",
                        "*/*/manifest.json"):
            kandydaci += sorted(katalog_pluginow.glob(wzorzec))
    except OSError:
        pass
    return kandydaci


NAZWA_PLUGINU = "danaco-praca"


def _wpis_pluginu_wlaczony(dane, notatki: list[str], plik) -> bool:
    """Czy struktura konfiguracji włącza ten plugin. Wartość `false` znaczy WYŁĄCZONY."""
    znalezione = False
    if isinstance(dane, dict):
        # Rejestr pluginów synchronizowanych z konta: {"plugins": [{"name": "…"}]}.
        if dane.get("name") == NAZWA_PLUGINU:
            notatki.append(f"wpis pluginu {NAZWA_PLUGINU} w rejestrze {plik}")
            znalezione = True
        for klucz, wartosc in dane.items():
            if isinstance(klucz, str) and klucz.split("@")[0] == NAZWA_PLUGINU:
                if wartosc is False or (isinstance(wartosc, dict)
                                        and wartosc.get("enabled") is False):
                    notatki.append(f"UWAGA: {plik} WYŁĄCZA wpis {klucz}")
                    continue
                znalezione = True
                notatki.append(f"wpis pluginu {klucz} włączony w {plik}")
            elif isinstance(wartosc, (dict, list)):
                znalezione = _wpis_pluginu_wlaczony(wartosc, notatki, plik) or znalezione
        if dane.get("disableAllHooks") is True:
            notatki.append(f"UWAGA: {plik} wyłącza wszystkie hooki (disableAllHooks)")
    elif isinstance(dane, list):
        for element in dane:
            if isinstance(element, str) and element.split("@")[0] == NAZWA_PLUGINU:
                znalezione = True
                notatki.append(f"wpis pluginu {element} w {plik}")
            elif isinstance(element, (dict, list)):
                znalezione = _wpis_pluginu_wlaczony(element, notatki, plik) or znalezione
    return znalezione


def _hooki_widoczne() -> tuple[bool, list[str]]:
    """Czy plugin jest włączony w konfiguracji klienta. Zwraca (widoczne, notatki).

    Pliki są PARSOWANE jako JSON: wyszukiwanie podciągu meldowało plugin jako widoczny
    przy wpisie `"danaco-praca": false` i nie zauważało `"disableAllHooks":true`
    zapisanego bez spacji."""
    notatki: list[str] = []
    widoczne = False
    for plik in _konfiguracje_klienta():
        try:
            tresc = plik.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            dane = json.loads(tresc)
        except ValueError:
            notatki.append(f"UWAGA: {plik} nie jest poprawnym JSON-em - pominięty")
            continue
        widoczne = _wpis_pluginu_wlaczony(dane, notatki, plik) or widoczne
    return widoczne, notatki


def _interpreter_z_powloki() -> str | None:
    """Pierwszy interpreter Pythona 3 osiągalny tak, jak szuka go wrapper hooków."""
    import shutil
    import subprocess
    for polecenie in (["python3"], ["python"], ["py", "-3"]):
        if shutil.which(polecenie[0]) is None:
            continue
        try:
            wynik = subprocess.run([*polecenie, "-c", "import sys; print(sys.version.split()[0])"],
                                   capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        if wynik.returncode == 0 and wynik.stdout.strip().startswith("3"):
            return f"{' '.join(polecenie)} -> Python {wynik.stdout.strip()}"
    return None


def polecenie_diagnoza() -> int:
    """Jednym poleceniem: czy mechanizm w TYM katalogu w ogóle zadziała."""
    korzen_pluginu = Path(__file__).resolve().parent.parent
    print("Diagnoza trybu ciągłej pracy Danaco")
    print(f"Katalog roboczy: {znacznik.katalog_roboczy()}")
    print(f"Korzeń projektu: {znacznik.korzen_projektu()} "
          f"(deterministyczny: {'tak' if znacznik.korzen_wyznaczony_deterministycznie() else 'nie'})")
    print(f"Katalog pluginu: {korzen_pluginu}")

    plik_hookow = korzen_pluginu / "hooks" / "hooks.json"
    print(f"Definicja hooków ({plik_hookow}): {'jest' if plik_hookow.is_file() else 'BRAK'}")
    wrapper = korzen_pluginu / "hooks" / "straznik.sh"
    print(f"Wrapper hooków ({wrapper}): {'jest' if wrapper.is_file() else 'BRAK'}")

    widoczne, notatki = _hooki_widoczne()
    print(f"Plugin w konfiguracji Claude Code: {'widoczny' if widoczne else 'NIE ZNALEZIONO WPISU'}")
    for notatka in notatki:
        print(f"  - {notatka}")
    if not widoczne:
        print("  - sprawdź `/plugin` w kliencie; bez wpisu hooki się nie uruchamiają")

    interpreter = _interpreter_z_powloki()
    print(f"Interpreter Pythona dla hooków: {interpreter or 'BRAK - hooki blokują awaryjnie'}")

    katalog = znacznik.znajdz_katalog_znacznika()
    oczekiwany = znacznik.korzen_projektu() / znacznik.NAZWA_KATALOGU / znacznik.NAZWA_ZNACZNIKA
    print(f"Znacznik szukany w: {oczekiwany} oraz w katalogach nadrzędnych")
    dane = znacznik.wczytaj_znacznik(katalog) if katalog is not None else None
    if katalog is not None and dane is None and (katalog / znacznik.NAZWA_ZNACZNIKA).is_file():
        print(f"Znacznik: {katalog / znacznik.NAZWA_ZNACZNIKA} — PLIK NIECZYTELNY")
        print("Tryb: pierwszy hook spróbuje odtworzyć znacznik z kopii, a gdy się nie "
              "uda, zdejmie go jak wygasły i tryb przestanie obowiązywać.")
        print("Naprawa ręczna: skasuj ten plik albo popraw jego treść (poprawny JSON).")
        return 0
    if katalog is None or dane is None:
        katalog_sesyjny = katalog or (znacznik.korzen_projektu() / znacznik.NAZWA_KATALOGU)
        if znacznik.sesje_zlecen(katalog_sesyjny):
            print(f"Zlecenia w tym katalogu: {katalog_sesyjny}")
            _wypisz_zlecenia_sesyjne(katalog_sesyjny)
            print("Każde zlecenie obowiązuje WYŁĄCZNIE swoją rozmowę. Z terminala nie da "
                  "się rozstrzygnąć, która sesja jest która - identyfikator sesji zna "
                  "tylko klient.")
            print("Wynik hooka Stop tutaj: 2 dla rozmowy, do której należy zlecenie; "
                  "0 dla pozostałych.")
            return 0
        print("Znacznik: BRAK - tryb nieaktywny w tym katalogu")
        print("Wynik hooka Stop tutaj: 0 (tura kończy się normalnie)")
        print(f"Włącz tryb: napisz {znacznik.POLECENIE_ROZPOCZECIA} na czacie - "
              "znacznik zakłada hook UserPromptSubmit, model nie musi nic uruchamiać.")
        return 0
    print(f"Znacznik: {katalog / znacznik.NAZWA_ZNACZNIKA}")
    print(f"Zlecenie: {dane.get('opis') or '(bez opisu)'}")
    _wypisz_zlecenia_sesyjne(katalog)
    wlasciciel = str(dane.get("sesjaId") or "")
    widziano = dane.get("ostatnioWidziano") or "brak zapisu"
    print(f"Właściciel znacznika (sesjaId): {wlasciciel or 'brak - przypisze się pierwszej sesji'}")
    print(f"Właściciel ostatnio widziany: {widziano}")
    if not wlasciciel:
        print("Tryb w nowej sesji: OBOWIĄZUJE (znacznik przypisze się jej przy pierwszym zdarzeniu)")
    elif znacznik.wlasciciel_niewidoczny(dane):
        print("Tryb w nowej sesji: OBOWIĄZUJE (właściciel milczy dłużej niż pół godziny, "
              "więc nowa sesja przejmuje znacznik)")
    else:
        print("Tryb w nowej sesji: NIE OBOWIĄZUJE - znacznik należy do innej, czynnej sesji. "
              f"W tamtej rozmowie reguły działają; tutaj przejmiesz je poleceniem {znacznik.POLECENIE_ROZPOCZECIA}.")
    if znacznik.wygasl(dane):
        print("Wynik hooka Stop tutaj: 0 (termin ważności znacznika minął)")
    else:
        print("Wynik hooka Stop tutaj: 2 dla sesji-właściciela "
              "(tura nie zakończy się bez polecenia użytkownika)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    podpolecenia = parser.add_subparsers(dest="polecenie", required=True)

    p = podpolecenia.add_parser("start")
    p.add_argument("opis")
    p.add_argument("--limit-godzin", type=float, default=znacznik.DOMYSLNY_LIMIT_GODZIN,
                   help="po ilu godzinach znacznik wygasa sam (1-24, domyślnie 24); 0 = "
                        "bezterminowo, dozwolone wyłącznie poza sesją modelu")
    p.add_argument("--poza-sesja", action="store_true",
                   help="polecenie uruchamia człowiek poza sesją modelu (zezwala na 0)")

    podpolecenia.add_parser("zakoncz", help="zdejmuje znacznik (dla człowieka, poza sesją modelu)")

    p = podpolecenia.add_parser("krok")
    p.add_argument("tekst")

    podpolecenia.add_parser("status", help="czytelny stan trybu w tym katalogu")
    podpolecenia.add_parser("raport", help="co model wywołał w zleceniach tego katalogu")
    podpolecenia.add_parser("diagnoza", help="czy mechanizm w tym katalogu w ogóle zadziała")

    args = parser.parse_args()

    if args.polecenie == "start":
        return polecenie_start(args.opis, args.limit_godzin, args.poza_sesja)
    if args.polecenie == "krok":
        return polecenie_krok(args.tekst)
    if args.polecenie == "zakoncz":
        return polecenie_zakoncz()
    if args.polecenie == "status":
        return polecenie_status()
    if args.polecenie == "raport":
        return polecenie_raport()
    if args.polecenie == "diagnoza":
        return polecenie_diagnoza()
    return 1


if __name__ == "__main__":
    sys.exit(main())
