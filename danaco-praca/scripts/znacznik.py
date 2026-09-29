#!/usr/bin/env python3
"""Wspólny moduł znacznika zadania w toku (`zadanie.py`, `straznik.py`): pliki
zlecenia w `.danaco`, korzeń projektu, zapis atomowy, odnajdywanie znacznika, termin
ważności, wiązanie z sesją, rozpoznawanie poleceń `/stop` i `/blokada`.

Korzeń projektu: `CLAUDE_PROJECT_DIR`, najbliższy katalog z `.git`, katalog roboczy.
Znacznik szukany jest też w katalogach nadrzędnych, bo hook działa po `cd`. Katalog
domowy i korzeń systemu są wyłączone. Moduł uruchomiony wprost kończy się kodem 2.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

NAZWA_KATALOGU = ".danaco"
# Pliki zniesionej skrzynki poleceń - do sprzątania starszych instalacji.
NAZWA_PLIKU_SKRZYNKI = "skrzynka.txt"
NAZWA_PLIKU_POZYCJI = "skrzynka.pozycja"
NAZWA_ZNACZNIKA = "zadanie-w-toku.json"
# Znacznik jest sesyjny: `/stop` zdejmuje wyłącznie zlecenie tej rozmowy. Plik
# w korzeniu `.danaco` to układ sprzed 4.0.0 - czytany dalej, żeby dawne zlecenie
# nie przepadło.
NAZWA_KATALOGU_ZADAN = "zadania"
# Stan zapisywany przed kompresją: bez niego model po kompresji nie wie, co miał robić.
NAZWA_STANU = "stan-zlecenia.md"
# Blokada podagentów: niezależna od zlecenia, do `LIMIT_GODZIN_BLOKADY` godzin.
NAZWA_BLOKADY = "blokada-subagentow.json"
LIMIT_GODZIN_BLOKADY = 12

# Blokada pracy maszynowej (masowa podmiana treści w plikach i w bazie): zakłada ją
# `/stop-skrypt`, zdejmuje `/skrypt`. Bez terminu ważności - termin zdejmowałby ją
# w środku pracy.
NAZWA_BLOKADY_SKRYPTOW = "blokada-skryptow.json"

# Dziennik pracy zlecenia: po jednym wierszu na wywołanie narzędzia. Zostaje po
# zakończeniu zlecenia - jest jedynym zapisem tego, co model faktycznie robił.
PRZEDROSTEK_DZIENNIKA_PRACY = "praca"
DNI_WAZNOSCI_DZIENNIKA_PRACY = 7


# Prefiksy komend: własny oraz stary `danaco-plugin` - użytkownik ma otwarte sesje
# z tamtą postacią komendy.
PREFIKSY_KOMEND = "(?:danaco-praca|danaco-plugin)"


def wzorzec_komendy(nazwa: str) -> re.Pattern:
    """Komenda tylko na początku wiadomości albo linii: cytat, ścieżka i log nie
    zdejmują blokady, kropka na końcu zdania - owszem."""
    return re.compile(rf"^[ \t]*/(?:{PREFIKSY_KOMEND}:)?{nazwa}(?!\w|[/:-]|\.\w)",
                      re.IGNORECASE | re.MULTILINE)


WZORZEC_BLOKADY = wzorzec_komendy("blokada")
WZORZEC_BLOKADY_STOP = wzorzec_komendy("blokada-stop")
# `/stop-skrypt` nie jest wariantem `/stop`: rozdziela je negatywny wgląd na `-`
# w `wzorzec_komendy`.
WZORZEC_BLOKADY_SKRYPTOW = wzorzec_komendy("stop-skrypt")
WZORZEC_ZWOLNIENIA_SKRYPTOW = wzorzec_komendy("skrypt")
# Znacznik zakłada hook `UserPromptSubmit`, nie model: gdy zakładał go model
# poleceniem `zadanie.py start`, pominięcie kroku cicho wyłączało cały mechanizm.
POLECENIE_ROZPOCZECIA = "/pracuj"
WZORZEC_ROZPOCZECIA = wzorzec_komendy("pracuj")
OPIS_ZASTEPCZY = "(zlecenie opisane w rozmowie)"
# Zniesiony plik klucza podpisu - do sprzątania po starszych instalacjach.
NAZWA_KLUCZA = ".klucz"
# Jedyne polecenie kończące tryb. Komenda, nie fraza: nie da się jej wypowiedzieć
# przypadkiem, a model nie ma jak jej podać.
POLECENIE_ZAKONCZENIA = "/stop"
WZORZEC_ZAKONCZENIA = wzorzec_komendy("stop")
NAZWA_KATALOGU_GIT = ".git"
ZMIENNA_KATALOGU_PROJEKTU = "CLAUDE_PROJECT_DIR"
LIMIT_POZIOMOW_W_GORE = 64
# Termin ważności: zapomniany znacznik blokowałby kolejne sesje w poddrzewie.
# Pola `wygasa` model nie skróci - zapisy do `.danaco` są odrzucane.
DOMYSLNY_LIMIT_GODZIN = 24
LIMIT_WPISOW_DZIENNIKA = 500
# Ponowienia usuwania: na Windows plik otwarty przez inny hook zwalnia się po chwili.
LICZBA_PONOWIEN_USUNIECIA = 6
PRZERWA_MIEDZY_PONOWIENIAMI_S = 0.05
# Kopia poza projektem: hook PostToolUse odtwarza z niej skasowany znacznik. Legalne
# zdjęcie kasuje kopię i zostawia nagrobek, żeby znacznik nie wracał.
NAZWA_KATALOGU_KOPII = ".danaco-kopie"
ROZSZERZENIE_NAGROBKA = ".nagrobek"
LIMIT_ODCZYTU_TOKENU_B = 8 * 1024 * 1024


def teraz() -> str:
    return datetime.now(timezone.utc).isoformat()


def parsuj_czas(tekst: str | None, wymagaj_strefy: bool = False) -> datetime | None:
    """Czas ISO 8601 jako datetime ze strefą albo None; `wymagaj_strefy` odrzuca wpis
    bez strefy."""
    if not isinstance(tekst, str) or not tekst.strip():
        return None
    surowy = tekst.strip()
    if surowy.endswith("Z") or surowy.endswith("z"):
        surowy = surowy[:-1] + "+00:00"
    try:
        wynik = datetime.fromisoformat(surowy)
    except ValueError:
        return None
    if wynik.tzinfo is None:
        if wymagaj_strefy:
            return None
        wynik = wynik.replace(tzinfo=timezone.utc)
    return wynik


def zapisz_atomowo(sciezka: Path, tresc: str, uprawnienia: int | None = None) -> None:
    """Zapis atomowy: widać starą albo nową pełną treść, nigdy pół-zapisanego JSON-a."""
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    fd, tymczasowa = tempfile.mkstemp(dir=str(sciezka.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as plik:
            plik.write(tresc)
        if uprawnienia is not None:
            os.chmod(tymczasowa, uprawnienia)
        os.replace(tymczasowa, sciezka)
    except BaseException:
        try:
            os.unlink(tymczasowa)
        except OSError:
            pass
        raise


# --- korzeń projektu i granica wyszukiwania

def _absolutna(start: str | os.PathLike | None) -> Path | None:
    if not start:
        return None
    try:
        return Path(os.path.abspath(os.fspath(start)))
    except (OSError, ValueError, TypeError):
        return None


def katalog_roboczy() -> Path:
    try:
        return Path(os.getcwd())
    except OSError:
        return Path(os.path.abspath(os.sep))


def katalog_domowy() -> Path | None:
    try:
        dom = Path(os.path.expanduser("~"))
    except (OSError, RuntimeError):
        return None
    return dom if dom.is_absolute() else None


def w_poddrzewie(katalog: Path, korzen: Path) -> bool:
    try:
        katalog.relative_to(korzen)
        return True
    except ValueError:
        return False


def _fizyczna(katalog: Path) -> Path:
    """Ścieżka po rozwinięciu dowiązań. Granice liczone tak samo jak zakres zapisu -
    inaczej dowiązanie do katalogu domowego omija kontrolę."""
    try:
        return Path(os.path.realpath(katalog))
    except OSError:
        return katalog


def poza_granica(katalog: Path) -> bool:
    """Czy to korzeń systemu plików, katalog domowy albo katalog nad nim."""
    if str(katalog) == katalog.anchor:
        return True
    fizyczny = _fizyczna(katalog)
    if str(fizyczny) == fizyczny.anchor:
        return True
    dom = katalog_domowy()
    if dom is None:
        return False
    return w_poddrzewie(dom, katalog) or w_poddrzewie(_fizyczna(dom), fizyczny)


def katalog_projektu_ze_srodowiska() -> Path | None:
    kandydat = _absolutna(os.environ.get(ZMIENNA_KATALOGU_PROJEKTU))
    if kandydat is None:
        return None
    try:
        return kandydat if kandydat.is_dir() else None
    except OSError:
        return None


def _lancuch_w_gore(start: Path, limit: int = LIMIT_POZIOMOW_W_GORE) -> list[Path]:
    """Katalog i przodkowie w granicach wyszukiwania (limit poziomów, bez `~`)."""
    wynik: list[Path] = []
    for katalog in [start, *list(start.parents)[:limit]]:
        if poza_granica(katalog):
            break
        wynik.append(katalog)
    return wynik


LIMIT_POZIOMOW_KORZENIA = 64


def korzen_projektu(start: str | os.PathLike | None = None) -> Path:
    """Deterministyczny korzeń projektu. `CLAUDE_PROJECT_DIR` porównywany jest też po
    ścieżce fizycznej (przy dowiązaniu znacznik lądował w podkatalogu), a `.git`
    szukany bez limitu ośmiu poziomów (w monorepo limit kończył wędrówkę wcześniej)."""
    biezacy = _absolutna(start) or katalog_roboczy()
    ze_srodowiska = katalog_projektu_ze_srodowiska()
    if ze_srodowiska is not None and (w_poddrzewie(biezacy, ze_srodowiska)
                                      or w_poddrzewie(_fizyczna(biezacy), _fizyczna(ze_srodowiska))):
        return ze_srodowiska
    for katalog in _lancuch_w_gore(biezacy, LIMIT_POZIOMOW_KORZENIA):
        if poza_granica(katalog):
            break
        try:
            if (katalog / NAZWA_KATALOGU_GIT).exists():
                return katalog
        except OSError:
            continue
    return biezacy


def korzen_wyznaczony_deterministycznie(start: str | os.PathLike | None = None) -> bool:
    """Czy korzeń wynika ze zmiennej środowiskowej albo z `.git`."""
    biezacy = _absolutna(start) or katalog_roboczy()
    korzen = korzen_projektu(biezacy)
    if korzen != biezacy:
        return True
    ze_srodowiska = katalog_projektu_ze_srodowiska()
    if ze_srodowiska is not None and korzen == ze_srodowiska:
        return True
    try:
        return (korzen / NAZWA_KATALOGU_GIT).exists()
    except OSError:
        return False


def _lancuch_do_korzenia(start: Path) -> list[Path]:
    """Katalogi do sprawdzenia: do korzenia, a bez niego do limitu poziomów."""
    lancuch = _lancuch_w_gore(start)
    if not korzen_wyznaczony_deterministycznie(start):
        return lancuch
    korzen = korzen_projektu(start)
    if korzen in lancuch:
        return lancuch[: lancuch.index(korzen) + 1]
    return lancuch


def kandydaci_katalogow(*starty: str | os.PathLike | None) -> list[Path]:
    """Katalogi, w których może leżeć `.danaco` (starty, cwd z przodkami, zmienna)."""
    widziane: set[str] = set()
    wynik: list[Path] = []

    def dolacz(katalog: Path) -> None:
        klucz = os.path.normcase(str(katalog))
        if klucz not in widziane:
            widziane.add(klucz)
            wynik.append(katalog)

    for zrodlo in [*starty, katalog_roboczy()]:
        poczatek = _absolutna(zrodlo)
        if poczatek is None:
            continue
        for katalog in _lancuch_do_korzenia(poczatek):
            dolacz(katalog)
    ze_srodowiska = katalog_projektu_ze_srodowiska()
    if ze_srodowiska is not None and not poza_granica(ze_srodowiska):
        dolacz(ze_srodowiska)
    return wynik


def nazwa_pliku_sesji(sesja: str) -> str:
    """Nazwa pliku znacznika dla sesji; znaki spoza bezpiecznego zakresu zastępuje
    skrót, bo identyfikator bywa dowolnym łańcuchem klienta."""
    czysta = re.sub(r"[^A-Za-z0-9._-]", "", sesja or "")
    if not czysta or czysta in (".", "..") or len(czysta) > 64 or czysta != (sesja or ""):
        import hashlib
        czysta = hashlib.sha256((sesja or "").encode("utf-8")).hexdigest()[:32]
    return f"{czysta}.json"


def katalog_zadan(katalog: Path) -> Path:
    return katalog / NAZWA_KATALOGU_ZADAN


def sciezka_znacznika(katalog: Path, sesja: str) -> Path:
    """Plik znacznika tej sesji (bez sesji - plik w układzie sprzed 4.0.0)."""
    if not sesja:
        return katalog / NAZWA_ZNACZNIKA
    return katalog_zadan(katalog) / nazwa_pliku_sesji(sesja)


def _sciezka_dawnego_znacznika(katalog: Path) -> Path:
    return katalog / NAZWA_ZNACZNIKA


def _dawny_znacznik_tej_sesji(katalog: Path, sesja: str) -> dict | None:
    """Znacznik w układzie sprzed 4.0.0, o ile należy do tej sesji albo jest niezwiązany."""
    try:
        dane = json.loads(_sciezka_dawnego_znacznika(katalog).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dane, dict):
        return None
    wlasciciel = sesja_znacznika(dane)
    if not sesja or not wlasciciel or wlasciciel == sesja:
        return dane
    return None


def sesje_zlecen(katalog: Path) -> list[str]:
    """Nazwy plików zleceń w tym katalogu (do `status` i `diagnoza`)."""
    wynik: list[str] = []
    try:
        if _sciezka_dawnego_znacznika(katalog).is_file():
            wynik.append(NAZWA_ZNACZNIKA)
        wynik += sorted(p.name for p in katalog_zadan(katalog).glob("*.json"))
    except OSError:
        pass
    return wynik


def istnieje_znacznik(katalog: Path, sesja: str = "") -> bool:
    """Czy w tym katalogu jest zlecenie tej sesji (bez sesji: jakiekolwiek). Rozstrzyga
    OBECNOŚĆ pliku, nie czytelność - uszkodzony znacznik ma dalej blokować."""
    try:
        if not sesja:
            return bool(sesje_zlecen(katalog))
        if sciezka_znacznika(katalog, sesja).is_file():
            return True
        if not _sciezka_dawnego_znacznika(katalog).is_file():
            return False
        try:
            dane = json.loads(_sciezka_dawnego_znacznika(katalog).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return True
        if not isinstance(dane, dict):
            return True
        wlasciciel = sesja_znacznika(dane)
        return not wlasciciel or wlasciciel == sesja
    except OSError:
        return False


def znajdz_katalog_znacznika(*starty: str | os.PathLike | None, sesja: str = "") -> Path | None:
    """Katalog `.danaco` ze zleceniem TEJ sesji albo None; zlecenie innej rozmowy nie
    jest tu widoczne."""
    for katalog in kandydaci_katalogow(*starty):
        kandydat = katalog / NAZWA_KATALOGU
        try:
            if istnieje_znacznik(kandydat, sesja):
                return kandydat
        except OSError:
            continue
    for zrodlo in [*starty, katalog_roboczy()]:
        poczatek = _absolutna(zrodlo)
        if poczatek is None:
            continue
        for katalog in _lancuch_w_gore(poczatek):
            kandydat = katalog / NAZWA_KATALOGU
            try:
                if not istnieje_znacznik(kandydat, sesja):
                    continue
            except OSError:
                continue
            zakres = _absolutna(str((wczytaj_znacznik(kandydat, sesja) or {}).get("katalogProjektu") or ""))
            if zakres is not None and w_poddrzewie(poczatek, zakres):
                return kandydat
    return None


# --- treść znacznika

def wczytaj_znacznik(katalog: Path, sesja: str = "") -> dict | None:
    """Treść zlecenia TEJ sesji albo None (o istnieniu decyduje obecność pliku). Bez
    sesji zwracane jest zlecenie sprzed 4.0.0 - tak wołają narzędzia człowieka."""
    if sesja:
        try:
            dane = json.loads(sciezka_znacznika(katalog, sesja).read_text(encoding="utf-8"))
            return dane if isinstance(dane, dict) else None
        except (OSError, ValueError):
            dawne = _dawny_znacznik_tej_sesji(katalog, sesja)
            if dawne is not None and not sesja_znacznika(dawne):
                # Zlecenie sprzed 4.0.0 nie ma właściciela: bierze je pierwsza sesja,
                # która po nie sięgnie. Inaczej blokowałoby WSZYSTKIE rozmowy.
                dawne["sesjaId"] = sesja
                dawne["ostatnioWidziano"] = teraz()
                try:
                    # Kopia też jest sesyjna: bez przeniesienia nie da się odtworzyć
                    # skasowanego znacznika.
                    zapisz_kopie(katalog, dawne, sesja)
                    zapisz_znacznik(katalog, dawne, sesja)
                    dawna_kopia = sciezka_kopii(katalog)
                    if dawna_kopia is not None and dawna_kopia.is_file():
                        os.remove(dawna_kopia)
                except (OSError, ValueError, TypeError):
                    pass
            return dawne
    try:
        dane = json.loads(_sciezka_dawnego_znacznika(katalog).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dane if isinstance(dane, dict) else None


def zapisz_znacznik(katalog: Path, dane: dict, sesja: str = "") -> None:
    """Zapisuje zlecenie tej sesji i odświeża ISTNIEJĄCĄ kopię. Kopii nie tworzymy tu
    od zera - nagrobek po zakończonym zleceniu musi zostać nagrobkiem."""
    kopia_kontrolna = sciezka_kopii(katalog, sesja)
    if kopia_kontrolna is not None:
        try:
            if kopia_kontrolna.with_suffix(ROZSZERZENIE_NAGROBKA).exists():
                # Zapis, który dobiegł po `/stop` (obecność z równoległego hooka),
                # wskrzeszał zlecenie mimo polecenia użytkownika.
                return
        except OSError:
            pass
    cel = sciezka_znacznika(katalog, sesja)
    try:
        cel.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    zapisz_atomowo(cel, json.dumps(dane, ensure_ascii=False, indent=2))
    if sesja and _sciezka_dawnego_znacznika(katalog).is_file():
        wlasciciel = sesja_znacznika(_dawny_znacznik_tej_sesji(katalog, sesja) or {})
        if not wlasciciel or wlasciciel == sesja:
            try:
                os.remove(_sciezka_dawnego_znacznika(katalog))
            except OSError:
                pass
    kopia = sciezka_kopii(katalog, sesja)
    if kopia is None or not kopia.is_file():
        return
    try:
        tresc = dict(dane)
        tresc["katalogZnacznika"] = str(katalog)
        tresc["sesjaZnacznika"] = sesja
        zapisz_atomowo(kopia, json.dumps(tresc, ensure_ascii=False, indent=2), uprawnienia=0o600)
    except OSError:
        pass


def ogranicz_dziennik(dane: dict, limit: int = LIMIT_WPISOW_DZIENNIKA) -> dict:
    """Ostatnie `limit` kroków (pominięte są zliczane) - inaczej plik rośnie bez końca."""
    kroki = dane.get("kroki")
    if not isinstance(kroki, list):
        dane["kroki"] = []
        return dane
    nadmiar = len(kroki) - limit
    if nadmiar > 0:
        dane["kroki"] = kroki[-limit:]
        try:
            pominiete = int(dane.get("krokowPominietych", 0))
        except (TypeError, ValueError):
            pominiete = 0
        dane["krokowPominietych"] = pominiete + nadmiar
    return dane


_BIALE_W_LINII = re.compile(r"[^\S\n]+")


def normalizuj_fraze(tekst: str) -> str:
    """Normalizacja NFC z zachowaniem linii - komenda liczy się na początku linii."""
    znormalizowany = unicodedata.normalize("NFC", tekst).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(_BIALE_W_LINII.sub(" ", linia).strip() for linia in znormalizowany.split("\n"))


def zawiera_polecenie_stop(tekst: str) -> bool:
    """Czy tekst zawiera polecenie kończące tryb."""
    if not isinstance(tekst, str) or not tekst:
        return False
    return WZORZEC_ZAKONCZENIA.search(normalizuj_fraze(tekst)) is not None


# --- termin ważności i zakres zlecenia

def wygasl(dane: dict | None, teraz_dt: datetime | None = None) -> bool:
    """Czy termin ważności minął. Brak pola `wygasa` = zlecenie bezterminowe."""
    if not dane:
        return False
    termin = parsuj_czas(dane.get("wygasa"))
    if termin is None:
        return False
    return (teraz_dt or datetime.now(timezone.utc)) >= termin


def poza_zakresem_zlecenia(dane: dict | None, sciezka: str) -> bool:
    """Czy zapis leży poza katalogiem projektu (katalog obok bywa cudzym repo)."""
    if not dane:
        return False
    korzen = _absolutna(str(dane.get("katalogProjektu") or ""))
    if korzen is None:
        return False
    cel = _absolutna(sciezka)
    if cel is None:
        return False
    try:
        cel = Path(os.path.realpath(cel))
        korzen = Path(os.path.realpath(korzen))
    except OSError:
        pass
    return not w_poddrzewie(cel, korzen)


def sesja_znacznika(dane: dict | None) -> str:
    """Sesja, do której znacznik należy (pusty, gdy niezwiązany)."""
    if not dane:
        return ""
    wartosc = dane.get("sesjaId")
    return wartosc.strip() if isinstance(wartosc, str) else ""


def token_znacznika(dane: dict | None) -> str:
    if not dane:
        return ""
    wartosc = dane.get("token")
    return wartosc.strip() if isinstance(wartosc, str) else ""


def token_w_transkrypcji(sciezka: str | None, token: str) -> bool | None:
    """Czy token z `start` pada w transkrypcji. None = nie dało się sprawdzić."""
    if not token or not isinstance(sciezka, str) or not sciezka.strip():
        return None
    pelna = os.path.expanduser(sciezka.strip())
    try:
        with open(pelna, "rb") as plik:
            plik.seek(0, os.SEEK_END)
            rozmiar = plik.tell()
            plik.seek(max(0, rozmiar - LIMIT_ODCZYTU_TOKENU_B))
            tresc = plik.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    return token in tresc


# DECYZJA (przejmowanie własności): token z `start` bywa widoczny w transkrypcji obcej
# sesji, więc sam token NIE przepisuje własności - obca sesja zamykałaby cudze zlecenie.
OKNO_PRZEJECIA_S = 30 * 60
# Obecność zapisujemy raz na tyle sekund - inaczej każdy hook przepisywałby plik.
ODSTEP_ZAPISU_OBECNOSCI_S = 60


def _zapisz_sesje(katalog: Path, dane: dict | None, sesja: str) -> None:
    if dane is None:
        return
    try:
        dane["sesjaId"] = sesja
        dane["ostatnioWidziano"] = teraz()
        zapisz_znacznik(katalog, ogranicz_dziennik(dane))
    except (OSError, ValueError, TypeError):
        pass


def odnotuj_obecnosc(katalog: Path, dane: dict | None, sesja: str = "") -> None:
    """Odświeża czas ostatniej obecności właściciela zlecenia (raz na minutę)."""
    if dane is None:
        return
    ostatnio = parsuj_czas(dane.get("ostatnioWidziano"))
    if ostatnio is not None:
        wiek = (datetime.now(timezone.utc) - ostatnio).total_seconds()
        if wiek < ODSTEP_ZAPISU_OBECNOSCI_S:
            return
    try:
        dane["ostatnioWidziano"] = teraz()
        zapisz_znacznik(katalog, ogranicz_dziennik(dane), sesja)
    except (OSError, ValueError, TypeError):
        pass


def wlasciciel_niewidoczny(dane: dict | None) -> bool:
    """Czy właściciel milczy dłużej niż OKNO_PRZEJECIA_S (brak czasu = tak). Czas
    z przyszłości liczy się jak brak zapisu: po cofniętym zegarze znacznik nigdy nie
    dałby się przejąć."""
    ostatnio = parsuj_czas((dane or {}).get("ostatnioWidziano"))
    if ostatnio is None:
        return True
    wiek = (datetime.now(timezone.utc) - ostatnio).total_seconds()
    if wiek < 0:
        return True
    return wiek > OKNO_PRZEJECIA_S


def mozna_zdjac(dane: dict | None, sesja: str, transkrypcja: str | None = None) -> bool:
    """Czy ta sesja może zdjąć znacznik: przy pustym `session_id` wymaga tokenu."""
    if sesja:
        return True
    return token_w_transkrypcji(transkrypcja, token_znacznika(dane)) is True


def zawiera_polecenie_pracuj(tekst: str) -> bool:
    """Czy tekst zawiera polecenie włączające tryb ciągłej pracy."""
    if not isinstance(tekst, str) or not tekst:
        return False
    return WZORZEC_ROZPOCZECIA.search(normalizuj_fraze(tekst)) is not None


def opis_ze_zlecenia(tekst: str) -> str:
    """Treść wiadomości po odjęciu samej komendy - to jest opis zlecenia."""
    if not isinstance(tekst, str):
        return OPIS_ZASTEPCZY
    znormalizowany = normalizuj_fraze(tekst)
    bez_komendy = WZORZEC_ROZPOCZECIA.sub("", znormalizowany, count=1).strip()
    return bez_komendy or OPIS_ZASTEPCZY


def utworz_dane_zlecenia(korzen: Path, opis: str, sesja: str = "",
                         limit_godzin: float = DOMYSLNY_LIMIT_GODZIN) -> dict:
    """Treść nowego znacznika - wspólna dla hooka i `zadanie.py start`, żeby obie drogi
    zakładały identyczny plik."""
    import secrets
    from datetime import timedelta
    if limit_godzin and limit_godzin > 0:
        wygasa = (datetime.now(timezone.utc) + timedelta(hours=limit_godzin)).isoformat()
    else:
        wygasa = ""
    return {
        "opis": opis,
        "rozpoczeto": teraz(),
        "katalogProjektu": str(korzen),
        "sesjaId": sesja,
        "ostatnioWidziano": teraz() if sesja else "",
        "token": secrets.token_hex(8),
        "wygasa": wygasa,
        "prob": 0,
        "kroki": [],
        "krokowPominietych": 0,
    }


def zawiera_polecenie_blokady(tekst: str) -> bool:
    return isinstance(tekst, str) and WZORZEC_BLOKADY.search(normalizuj_fraze(tekst)) is not None


def zawiera_polecenie_blokada_stop(tekst: str) -> bool:
    return isinstance(tekst, str) and WZORZEC_BLOKADY_STOP.search(normalizuj_fraze(tekst)) is not None


def zawiera_polecenie_blokady_skryptow(tekst: str) -> bool:
    return isinstance(tekst, str) and WZORZEC_BLOKADY_SKRYPTOW.search(normalizuj_fraze(tekst)) is not None


def zawiera_polecenie_zwolnienia_skryptow(tekst: str) -> bool:
    return isinstance(tekst, str) and WZORZEC_ZWOLNIENIA_SKRYPTOW.search(normalizuj_fraze(tekst)) is not None


def sciezka_stanu(katalog: Path, sesja: str = "") -> Path:
    """Plik stanu zlecenia zapisywany przed kompresją kontekstu (osobny dla sesji)."""
    if not sesja:
        return katalog / NAZWA_STANU
    return katalog_zadan(katalog) / f"stan-{nazwa_pliku_sesji(sesja)[:-5]}.md"


def sciezka_dziennika_pracy(katalog: Path, sesja: str = "") -> Path:
    """Dziennik pracy tej rozmowy."""
    if not sesja:
        return katalog_zadan(katalog) / f"{PRZEDROSTEK_DZIENNIKA_PRACY}.jsonl"
    return katalog_zadan(katalog) / f"{PRZEDROSTEK_DZIENNIKA_PRACY}-{nazwa_pliku_sesji(sesja)[:-5]}.jsonl"


def posprzataj_dzienniki_pracy(katalog: Path, dni: int = DNI_WAZNOSCI_DZIENNIKA_PRACY) -> int:
    """Kasuje dzienniki pracy starsze niż podana liczba dni."""
    granica = datetime.now(timezone.utc).timestamp() - dni * 86400
    usuniete = 0
    try:
        pliki = list(katalog_zadan(katalog).glob(f"{PRZEDROSTEK_DZIENNIKA_PRACY}-*.jsonl"))
    except OSError:
        return 0
    for plik in pliki:
        try:
            if plik.stat().st_mtime < granica:
                os.remove(plik)
                usuniete += 1
        except OSError:
            continue
    return usuniete


def podsumowanie_pracy(katalog: Path, sesja: str = "") -> list[str]:
    """Raport z dziennika pracy: co model faktycznie wywołał w tym zleceniu."""
    sciezka = sciezka_dziennika_pracy(katalog, sesja)
    try:
        with open(sciezka, "r", encoding="utf-8") as plik:
            wpisy = [json.loads(linia) for linia in plik if linia.strip()]
    except (OSError, ValueError):
        return []
    wpisy = [w for w in wpisy if isinstance(w, dict)]
    if not wpisy:
        return []
    odrzucone = sum(1 for w in wpisy if w.get("odrzucone"))
    w_tle = sum(1 for w in wpisy if w.get("wTle"))
    narzedzia: dict[str, int] = {}
    pliki: list[str] = []
    for wpis in wpisy:
        nazwa = str(wpis.get("narzedzie") or "?")
        narzedzia[nazwa] = narzedzia.get(nazwa, 0) + 1
        if nazwa in ("Write", "Edit", "MultiEdit", "NotebookEdit") and not wpis.get("odrzucone"):
            cel = str(wpis.get("co") or "")
            if cel and cel not in pliki:
                pliki.append(cel)
    poczatek = parsuj_czas(wpisy[0].get("czas"))
    koniec = parsuj_czas(wpisy[-1].get("czas"))
    trwanie = ""
    if poczatek is not None and koniec is not None:
        minuty = int((koniec - poczatek).total_seconds() // 60)
        trwanie = f", czas pracy {minuty // 60} h {minuty % 60} min" if minuty >= 60 else f", czas pracy {minuty} min"
    kolejnosc = sorted(narzedzia.items(), key=lambda para: -para[1])[:6]
    wiersze = [
        f"Dziennik pracy: {len(wpisy)} wywołań ({odrzucone} odrzuconych, {w_tle} w tle){trwanie}.",
        "Najczęstsze narzędzia: " + ", ".join(f"{nazwa} {ile}x" for nazwa, ile in kolejnosc) + ".",
    ]
    if pliki:
        wiersze.append(f"Zapisane pliki ({len(pliki)}): " + ", ".join(pliki[:10])
                       + (" …" if len(pliki) > 10 else ""))
    wiersze.append(f"Pełny zapis: {sciezka}")
    return wiersze


def katalog_blokady(*starty) -> Path:
    """Katalog `.danaco` z plikiem blokady podagentów."""
    istniejacy = znajdz_katalog_znacznika(*starty)
    if istniejacy is not None:
        return istniejacy
    return korzen_projektu() / NAZWA_KATALOGU


def wlacz_blokade(katalog: Path, sesja: str, godziny: float = LIMIT_GODZIN_BLOKADY) -> str:
    from datetime import timedelta
    wygasa = (datetime.now(timezone.utc) + timedelta(hours=godziny)).isoformat()
    zapisz_atomowo(katalog / NAZWA_BLOKADY, json.dumps(
        {"wlaczono": teraz(), "wygasa": wygasa, "sesjaId": sesja}, ensure_ascii=False, indent=2))
    return wygasa


def wylacz_blokade(katalog: Path) -> None:
    try:
        os.remove(katalog / NAZWA_BLOKADY)
    except OSError:
        pass


def wczytaj_blokade(katalog: Path) -> dict | None:
    """Treść pliku blokady (bez sprawdzania terminu) albo None."""
    try:
        dane = json.loads((katalog / NAZWA_BLOKADY).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dane if isinstance(dane, dict) else None


def blokada_aktywna(katalog: Path, sesja: str) -> dict | None:
    """Aktywna blokada podagentów tej sesji albo None (wygasła jest kasowana)."""
    plik = katalog / NAZWA_BLOKADY
    try:
        dane = json.loads(plik.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dane, dict):
        return None
    if wygasl(dane):
        wylacz_blokade(katalog)
        return None
    wlasciciel = str(dane.get("sesjaId") or "")
    if wlasciciel and sesja and wlasciciel != sesja:
        return None
    return dane


def wlacz_blokade_skryptow(katalog: Path, sesja: str) -> None:
    """Zakłada blokadę pracy maszynowej dla tej sesji (bez terminu ważności)."""
    zapisz_atomowo(katalog / NAZWA_BLOKADY_SKRYPTOW, json.dumps(
        {"wlaczono": teraz(), "sesjaId": sesja}, ensure_ascii=False, indent=2))


def wylacz_blokade_skryptow(katalog: Path) -> None:
    try:
        os.remove(katalog / NAZWA_BLOKADY_SKRYPTOW)
    except OSError:
        pass


def wczytaj_blokade_skryptow(katalog: Path) -> dict | None:
    try:
        dane = json.loads((katalog / NAZWA_BLOKADY_SKRYPTOW).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dane if isinstance(dane, dict) else None


def blokada_skryptow_aktywna(katalog: Path, sesja: str) -> dict | None:
    """Aktywna blokada pracy maszynowej tej sesji albo None; zdejmuje ją wyłącznie
    polecenie użytkownika."""
    dane = wczytaj_blokade_skryptow(katalog)
    if dane is None:
        return None
    wlasciciel = str(dane.get("sesjaId") or "")
    if wlasciciel and sesja and wlasciciel != sesja:
        return None
    return dane


def _skrot_sciezki(katalog: Path) -> str:
    import hashlib
    return hashlib.sha256(os.path.normcase(str(katalog)).encode("utf-8")).hexdigest()[:16]


def sciezka_kopii(katalog: Path, sesja: str = "") -> Path | None:
    """Plik kopii dla zlecenia tej sesji albo None bez katalogu domowego. Osobny dla
    sesji: równoległe zlecenia nie mogą kasować sobie nagrobków."""
    dom = katalog_domowy()
    if dom is None:
        return None
    nazwa = _skrot_sciezki(katalog if not sesja else Path(f"{katalog}\n{sesja}"))
    return dom / NAZWA_KATALOGU_KOPII / f"{nazwa}.json"


DNI_WAZNOSCI_KOPII = 7


def posprzataj_kopie(dni: int = DNI_WAZNOSCI_KOPII) -> int:
    """Kasuje kopie i nagrobki starsze niż `dni`."""
    dom = katalog_domowy()
    if dom is None:
        return 0
    katalog = dom / NAZWA_KATALOGU_KOPII
    granica = time.time() - dni * 86400
    usuniete = 0
    try:
        wpisy = list(katalog.iterdir())
    except OSError:
        return 0
    for wpis in wpisy:
        if wpis.suffix not in (".json", ROZSZERZENIE_NAGROBKA):
            continue
        try:
            if wpis.stat().st_mtime >= granica:
                continue
            os.remove(wpis)
            usuniete += 1
        except OSError:
            continue
    return usuniete


def zapisz_kopie(katalog: Path, dane: dict, sesja: str = "") -> bool:
    """True, gdy kopia trafiła na dysk (False = znacznika nie da się odtworzyć)."""
    kopia = sciezka_kopii(katalog, sesja)
    if kopia is None:
        return False
    try:
        kopia.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(kopia.parent, 0o700)
        nagrobek = kopia.with_suffix(ROZSZERZENIE_NAGROBKA)
        if nagrobek.exists():
            os.remove(nagrobek)
        tresc = dict(dane)
        tresc["katalogZnacznika"] = str(katalog)
        tresc["sesjaZnacznika"] = sesja
        zapisz_atomowo(kopia, json.dumps(tresc, ensure_ascii=False, indent=2), uprawnienia=0o600)
    except OSError:
        return False
    return True


def wczytaj_kopie(katalog: Path, sesja: str = "") -> dict | None:
    """Ważna kopia (nie wygasła, bez nagrobka) albo None. Bez kopii sesyjnej sięgamy
    po kopię bez sesji: zlecenie z `zadanie.py start` nie zna identyfikatora sesji."""
    kandydaci = [sciezka_kopii(katalog, sesja)]
    if sesja:
        kandydaci.append(sciezka_kopii(katalog))
    for kopia in kandydaci:
        if kopia is None:
            continue
        try:
            if kopia.with_suffix(ROZSZERZENIE_NAGROBKA).exists():
                continue
            dane = json.loads(kopia.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(dane, dict) and not wygasl(dane):
            return dane
    return None


def usun_kopie(katalog: Path, sesja: str = "") -> None:
    """Kasuje kopię i zostawia nagrobek."""
    kopia = sciezka_kopii(katalog, sesja)
    if kopia is None:
        return
    try:
        kopia.parent.mkdir(parents=True, exist_ok=True)
        zapisz_atomowo(kopia.with_suffix(ROZSZERZENIE_NAGROBKA), teraz(), uprawnienia=0o600)
    except OSError:
        pass
    try:
        os.remove(kopia)
    except OSError:
        pass


def odtworz_znacznik(katalog: Path, sesja: str = "") -> bool:
    """Odtwarza zlecenie tej sesji z ważnej kopii."""
    dane = wczytaj_kopie(katalog, sesja)
    if dane is None:
        return False
    dane.pop("katalogZnacznika", None)
    dane.pop("sesjaZnacznika", None)
    dane["ostatnioWidziano"] = teraz()
    try:
        zapisz_znacznik(katalog, dane, sesja)
    except (OSError, ValueError, TypeError):
        return False
    return sciezka_znacznika(katalog, sesja).is_file()


def usun_znacznik(katalog: Path, sesja: str = "") -> bool:
    """Usuwa zlecenie TEJ sesji; zlecenia innych rozmów w projekcie zostają."""
    usun_kopie(katalog, sesja)
    # Licznik sprawdzeń znika razem ze zleceniem; dziennik pracy zostaje, bo jest
    # zapisem tego, co model robił, i człowiek czyta go po zakończeniu.
    do_usuniecia = [sciezka_znacznika(katalog, sesja), sciezka_stanu(katalog, sesja),
                    katalog_zadan(katalog) / f"sprawdzenia-{nazwa_pliku_sesji(sesja)[:-5]}.licznik"
                    if sesja else katalog / "sprawdzenia.licznik"]
    if sesja:
        # Zlecenie przeniesione z układu sprzed 4.0.0 mogło zostawić dawny plik.
        if _dawny_znacznik_tej_sesji(katalog, sesja) is not None:
            do_usuniecia.append(_sciezka_dawnego_znacznika(katalog))
    else:
        do_usuniecia += [katalog / NAZWA_KLUCZA, katalog / NAZWA_PLIKU_SKRZYNKI,
                         katalog / NAZWA_PLIKU_POZYCJI, katalog / NAZWA_STANU]
    for sciezka in do_usuniecia:
        # Plik blokady podagentów celowo NIE jest kasowany ze zleceniem: `/blokada`
        # jest niezależna od trybu ciągłej pracy.
        for proba in range(LICZBA_PONOWIEN_USUNIECIA):
            try:
                os.remove(sciezka)
                break
            except FileNotFoundError:
                break
            except OSError:
                if proba == LICZBA_PONOWIEN_USUNIECIA - 1:
                    break
                time.sleep(PRZERWA_MIEDZY_PONOWIENIAMI_S)
    try:
        for resztka in katalog.glob(".tmp-*"):
            try:
                os.remove(resztka)
            except OSError:
                pass
    except OSError:
        pass
    if not sesje_zlecen(katalog):
        try:
            os.rmdir(katalog_zadan(katalog))
        except OSError:
            pass
        try:
            os.rmdir(katalog)
        except OSError:
            pass
    return not istnieje_znacznik(katalog, sesja)


def posprzataj_wygasle(katalog: Path) -> int:
    """Kasuje zlecenia z minionym terminem - inaczej pliki po zamkniętych rozmowach
    zostają w projekcie na stałe."""
    usuniete = 0
    try:
        pliki = list(katalog_zadan(katalog).glob("*.json"))
    except OSError:
        return 0
    for plik in pliki:
        try:
            dane = json.loads(plik.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(dane, dict) and wygasl(dane):
            try:
                os.remove(plik)
                usuniete += 1
            except OSError:
                continue
    return usuniete


if __name__ == "__main__":
    print(
        "znacznik.py to moduł wspólny skryptów zadanie.py i straznik.py - nie ma "
        "własnych poleceń. Znacznik zakłada: zadanie.py start \"opis\"; stan "
        "pokazuje: zadanie.py status.",
        file=sys.stderr,
    )
    sys.exit(2)
