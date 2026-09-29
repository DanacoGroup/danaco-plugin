#!/usr/bin/env python3
"""Progi i słowniki kontroli dyscypliny oraz nazewnictwa — jedno miejsce.

Wartości domyślne odpowiadają standardowi z paczki `dyscyplina-inzynierska`
(limit 350 znaków na komentarz, udział komentarzy poniżej 20%). Repozytorium
może je nadpisać plikiem `konfiguracja-dyscypliny.json` — podanym przez
`--config` albo znalezionym w korzeniu sprawdzanego repozytorium.

Kształt pliku konfiguracyjnego:

    {
      "limitKomentarza": 350,
      "progUdzialu": 0.2,
      "minZnakowDoUdzialu": 600,
      "allowlistaKodow": ["MOD-A7"],
      "slowaMetaforyczne": ["silnik"],
      "allowlistaNazw": ["Tauri2"]
    }

Błąd konfiguracji (brak pliku, zepsuty JSON, zła wartość) kończy walidator kodem
`KOD_BLEDU_KONFIGURACJI`, a nie tracebackiem: kod 1 nie występuje w kontrakcie
walidatorów (0/2/3), więc CI nie odróżniłby awarii narzędzia od naruszenia.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DOMYSLNY_LIMIT_KOMENTARZA = 350
DOMYSLNY_PROG_UDZIALU = 0.20
# Poniżej tej objętości pliku reguła udziału komentarzy jest wyłączona: na krótkim
# pliku nawet jeden zdawkowy komentarz przekracza każdy procentowy próg, bo
# mianownik jest za mały, żeby proporcja cokolwiek mówiła o esejowości kodu.
DOMYSLNY_MIN_ZNAKOW_DO_UDZIALU = 600

KOD_BLEDU_KONFIGURACJI = 4
NAZWA_PLIKU_KONFIGURACJI = "konfiguracja-dyscypliny.json"
LIMIT_POZIOMOW_KONFIGURACJI = 6

# Standardy, normy, wersje protokołów i jednostki pasują do wzorca wymyślonego
# kodu, ale wymyślonymi kodami nie są.
WYJATKI_STANDARDOW = re.compile(
    r"^(UTF|ISO|RFC|SHA|MD|AES|RSA|HTTP|HTTPS|TLS|SSL|WCAG|IEEE|ANSI|EN|PN|DIN|IPv"
    r"|GPT|CVE|CWE|OWASP|SQL|CSS|API|URL|URI|JSON|YAML|XML|UUID|CRC|GPU|CPU)[-_]",
    re.I,
)

DOMYSLNE_SLOWA_METAFORYCZNE = {
    "magia", "magiczny", "silnik", "mozg", "serce", "dusza", "moc", "czarodziej",
    "guru", "ninja", "rakieta", "smart", "genialny",
}

# Identyfikatory pasujące do wzorca oznaczenia literowo-numerycznego, które są
# uzasadnione technicznie (wersje standardów i bibliotek stosu Danaco).
DOMYSLNE_WYJATKI_OZNACZEN = {
    "UTF8", "SHA256", "SHA512", "AES256", "HTTP2", "HTTP3", "IPv4", "IPv6",
    "Base64", "OAuth2", "Tauri2", "Vite5", "React18", "Go1", "ES2022",
    "PostgreSQL16", "SQLite3", "Python3", "Node20", "Radix3",
}


@dataclass
class Konfiguracja:
    limit_komentarza: int = DOMYSLNY_LIMIT_KOMENTARZA
    prog_udzialu: float = DOMYSLNY_PROG_UDZIALU
    min_znakow_do_udzialu: int = DOMYSLNY_MIN_ZNAKOW_DO_UDZIALU
    allowlista_kodow: set[str] = field(default_factory=set)
    slowa_metaforyczne: set[str] = field(default_factory=lambda: set(DOMYSLNE_SLOWA_METAFORYCZNE))
    allowlista_nazw: set[str] = field(default_factory=set)

    def oznaczenie_dozwolone(self, oznaczenie: str) -> bool:
        maly = oznaczenie.lower()
        dozwolone = {w.lower() for w in self.allowlista_nazw | DOMYSLNE_WYJATKI_OZNACZEN}
        return maly in dozwolone

    def kod_dozwolony(self, kod: str) -> bool:
        if kod in self.allowlista_kodow:
            return True
        return bool(WYJATKI_STANDARDOW.match(kod))


def _zbior(dane: dict, klucz: str) -> set[str]:
    wartosc = dane.get(klucz)
    if wartosc is None:
        return set()
    if not isinstance(wartosc, list) or any(not isinstance(w, str) for w in wartosc):
        raise ValueError(f"pole {klucz} musi być listą łańcuchów")
    return set(wartosc)


def z_pliku(sciezka: Path) -> Konfiguracja:
    """Konfiguracja z pliku JSON. Każdy błąd kończy proces kodem konfiguracji."""
    try:
        dane = json.loads(sciezka.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as blad:
        print(f"BŁĄD: nie da się odczytać konfiguracji {sciezka}: {blad}", file=sys.stderr)
        raise SystemExit(KOD_BLEDU_KONFIGURACJI)
    if not isinstance(dane, dict):
        print(f"BŁĄD: {sciezka} musi zawierać obiekt JSON", file=sys.stderr)
        raise SystemExit(KOD_BLEDU_KONFIGURACJI)
    try:
        return Konfiguracja(
            limit_komentarza=int(dane.get("limitKomentarza", DOMYSLNY_LIMIT_KOMENTARZA)),
            prog_udzialu=float(dane.get("progUdzialu", DOMYSLNY_PROG_UDZIALU)),
            min_znakow_do_udzialu=int(dane.get("minZnakowDoUdzialu", DOMYSLNY_MIN_ZNAKOW_DO_UDZIALU)),
            allowlista_kodow=_zbior(dane, "allowlistaKodow"),
            slowa_metaforyczne=set(DOMYSLNE_SLOWA_METAFORYCZNE) | _zbior(dane, "slowaMetaforyczne"),
            allowlista_nazw=_zbior(dane, "allowlistaNazw"),
        )
    except (TypeError, ValueError) as blad:
        print(f"BŁĄD: nieprawidłowa wartość w {sciezka}: {blad}", file=sys.stderr)
        raise SystemExit(KOD_BLEDU_KONFIGURACJI)


def znajdz_domyslny(sciezki: list[str]) -> Path | None:
    """Plik konfiguracyjny sprawdzanego repozytorium albo None.

    Szukany jest w katalogu wskazanej ścieżki i w katalogach nadrzędnych, do
    korzenia repozytorium (katalog z `.git`) albo `LIMIT_POZIOMOW_KONFIGURACJI`
    poziomów. Hook `PostToolUse` woła walidator z pojedynczym plikiem gdzieś
    w głębi drzewa, a konfiguracja leży w korzeniu.
    """
    for wpis in sciezki:
        p = Path(wpis).resolve()
        start = p if p.is_dir() else p.parent
        for katalog in [start, *list(start.parents)[:LIMIT_POZIOMOW_KONFIGURACJI]]:
            try:
                kandydat = katalog / NAZWA_PLIKU_KONFIGURACJI
                if kandydat.is_file():
                    return kandydat
                if (katalog / ".git").exists():
                    break
            except OSError:
                break
    return None


def wczytaj(sciezka: Path | None, sciezki_kontroli: list[str] | None = None) -> Konfiguracja:
    if sciezka is not None:
        return z_pliku(sciezka)
    domyslny = znajdz_domyslny(sciezki_kontroli or [])
    return z_pliku(domyslny) if domyslny is not None else Konfiguracja()


if __name__ == "__main__":
    print("konfiguracja_kontroli.py to moduł wspólny walidatorów - nie ma własnych "
          "poleceń.", file=sys.stderr)
    sys.exit(2)
