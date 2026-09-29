#!/usr/bin/env python3
"""Walidator dyscypliny Danaco (style_guard.py).

Sprawdza pliki źródłowe pod kątem standardu z paczki `dyscyplina-inzynierska`:
- limit długości pojedynczego komentarza (domyślnie 350 znaków),
- udział komentarzy w pliku poniżej progu (domyślnie 20%, reguła wyłączona na plikach
  krótszych niż 600 znaków); dla plików `.py` do udziału wliczane są docstringi
  funkcji i klas, bo w tym języku proza mieszka głównie w nich,
- wymyślone kody literowo-numeryczne komponentów (kody pochodzą z kontraktu),
- ton nieformalny (emoji, wielokrotniki wykrzykników/kropek),
- pliki, których nie da się odczytać jako UTF-8 (kontrola nie została wykonana).

Komentarze `.py` wyodrębnia `tokenize` z biblioteki standardowej, a w językach
`//` skaner znający literały i znaki ucieczki. Liczenie cudzysłowów przed
prefiksem myliło się w obie strony: apostrof w literale (`print("it's")`) ukrywał
komentarz, a nagłówek Markdown w literale potrójnym udawał komentarz.

Progi, allowlisty i słowniki: `scripts/konfiguracja_kontroli.py` oraz opcjonalny
plik `konfiguracja-dyscypliny.json` w korzeniu sprawdzanego repozytorium.

Użycie:
    python3 style_guard.py <plik-lub-katalog> [<plik-lub-katalog> ...]
    python3 style_guard.py --config konfiguracja-dyscypliny.json src/

Kody wyjścia:
    0 - brak naruszeń
    2 - tylko ostrzeżenia (nie blokujące)
    3 - co najmniej jedno naruszenie blokujące
    4 - awaria kontroli (zła konfiguracja, brak modułów wspólnych pluginu)
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

try:
    import konfiguracja_kontroli
    import przechodzenie_repozytorium
except ImportError as _blad:  # pragma: no cover - niepełna instalacja pluginu
    print(f"BŁĄD: brak modułów wspólnych pluginu (scripts/): {_blad}", file=sys.stderr)
    sys.exit(4)

Konfiguracja = konfiguracja_kontroli.Konfiguracja
KOD_AWARII = konfiguracja_kontroli.KOD_BLEDU_KONFIGURACJI

ROZSZERZENIA_KODU = {
    ".go": ("//", None),
    ".ts": ("//", ("/*", "*/")),
    ".tsx": ("//", ("/*", "*/")),
    ".js": ("//", ("/*", "*/")),
    ".jsx": ("//", ("/*", "*/")),
    ".rs": ("//", ("/*", "*/")),
    ".py": ("#", None),
}

# Wzorzec wymyślonych kodów literowo-numerycznych: 1-4 wielkie litery, myślnik albo
# podkreślnik, 1-4 znaki alfanumeryczne. Kody o takim kształcie muszą pochodzić
# z kontraktu; przykłady naruszeń są w dokumentacji paczki, nie w tym komentarzu.
WZORZEC_WYMYSLONEGO_KODU = re.compile(r"\b[A-Z]{1,4}[-_][A-Z0-9]{1,4}\b")

WZORCE_NIEFORMALNE = [
    # `??` to operator TypeScriptu, więc seria musi być jednorodna i dłuższa.
    re.compile(r"!{2,}|\?{3,}"),
    re.compile(r"\.{4,}"),
    re.compile(r"[\U0001F300-\U0001FAFF☀-➿]"),
]

REGULA_KODOWANIA = "kodowanie-pliku"


@dataclass
class Naruszenie:
    plik: str
    linia: int
    regula: str
    tresc: str
    blokujace: bool


def komentarze_python(tresc: str) -> list[tuple[int, str]]:
    """Komentarze `#` wyodrębnione tokenizerem Pythona."""
    wynik: list[tuple[int, str]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(tresc).readline):
            if token.type == tokenize.COMMENT:
                wynik.append((token.start[0], token.string))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return skanuj_komentarze(tresc, "#", None)
    return wynik


def docstringi_python(tresc: str) -> list[tuple[int, str]]:
    """Docstringi klas i funkcji — w Pythonie to główne miejsce prozy w kodzie.

    Docstring MODUŁU nie jest wliczany: to dokumentacja pliku (przeznaczenie,
    użycie, kody wyjścia, kontrakt wejścia), czyli dokładnie to miejsce, do
    którego standard każe przenosić dłuższe wyjaśnienia z komentarzy.
    """
    try:
        drzewo = ast.parse(tresc)
    except (SyntaxError, ValueError):
        return []
    wynik: list[tuple[int, str]] = []
    for wezel in ast.walk(drzewo):
        if not isinstance(wezel, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        tekst = ast.get_docstring(wezel, clean=False)
        if not tekst:
            continue
        linia = getattr(wezel.body[0], "lineno", 1) if getattr(wezel, "body", None) else 1
        wynik.append((linia, tekst))
    return wynik


def _pomin_literal(tresc: str, start: int) -> int:
    """Indeks pierwszego znaku za literałem rozpoczynającym się na `start`."""
    znak = tresc[start]
    dlugosc = len(tresc)
    potrojny = tresc[start:start + 3] if tresc[start:start + 3] in ('"""', "'''") else ""
    if potrojny:
        koniec = tresc.find(potrojny, start + 3)
        return dlugosc if koniec == -1 else koniec + 3
    i = start + 1
    while i < dlugosc:
        if tresc[i] == "\\":
            i += 2
            continue
        if tresc[i] == znak:
            return i + 1
        if tresc[i] == "\n" and znak != "`":
            return i
        i += 1
    return dlugosc


def skanuj_komentarze(tresc: str, prefiks: str, blok: tuple[str, str] | None) -> list[tuple[int, str]]:
    """Komentarze liniowe i blokowe poza literałami łańcuchowymi."""
    wyniki: list[tuple[int, str]] = []
    dlugosc = len(tresc)
    i = 0
    nr = 1
    while i < dlugosc:
        znak = tresc[i]
        if znak == "\n":
            nr += 1
            i += 1
            continue
        if znak in "\"'`":
            koniec = _pomin_literal(tresc, i)
            nr += tresc.count("\n", i, koniec)
            i = koniec
            continue
        if blok is not None and tresc.startswith(blok[0], i):
            znaleziony = tresc.find(blok[1], i + len(blok[0]))
            koniec = dlugosc if znaleziony == -1 else znaleziony + len(blok[1])
            wyniki.append((nr, tresc[i:koniec]))
            nr += tresc.count("\n", i, koniec)
            i = koniec
            continue
        if tresc.startswith(prefiks, i):
            znaleziony = tresc.find("\n", i)
            koniec = dlugosc if znaleziony == -1 else znaleziony
            wyniki.append((nr, tresc[i:koniec]))
            i = koniec
            continue
        i += 1
    return wyniki


def komentarze_pliku(sciezka: Path, tresc: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Para: komentarze podlegające limitowi długości oraz proza wliczana do udziału."""
    prefiks, blok = ROZSZERZENIA_KODU[sciezka.suffix]
    if sciezka.suffix == ".py":
        komentarze = komentarze_python(tresc)
        return komentarze, komentarze + docstringi_python(tresc)
    komentarze = skanuj_komentarze(tresc, prefiks, blok)
    return komentarze, komentarze


def sprawdz_komentarz(sciezka: Path, nr: int, tekst: str, cfg: Konfiguracja) -> list[Naruszenie]:
    naruszenia: list[Naruszenie] = []
    if len(tekst) > cfg.limit_komentarza:
        naruszenia.append(Naruszenie(
            str(sciezka), nr, "limit-dlugosci-komentarza",
            f"komentarz ma {len(tekst)} znaków (limit {cfg.limit_komentarza})",
            blokujace=True,
        ))
    for wzorzec in WZORCE_NIEFORMALNE:
        if wzorzec.search(tekst):
            naruszenia.append(Naruszenie(
                str(sciezka), nr, "ton-nieformalny",
                f"nieformalny ton w komentarzu: {tekst.strip()[:80]!r}",
                blokujace=False,
            ))
            break
    for dopasowanie in WZORZEC_WYMYSLONEGO_KODU.finditer(tekst):
        kod = dopasowanie.group(0)
        if cfg.kod_dozwolony(kod):
            continue
        naruszenia.append(Naruszenie(
            str(sciezka), nr, "wymyslony-kod",
            f"możliwy wymyślony kod {kod!r} - kody muszą pochodzić z kontraktu",
            blokujace=False,
        ))
    return naruszenia


def sprawdz_plik(sciezka: Path, cfg: Konfiguracja) -> list[Naruszenie]:
    if sciezka.suffix not in ROZSZERZENIA_KODU:
        return []

    tresc, blad = przechodzenie_repozytorium.wczytaj_tekst(sciezka)
    if tresc is None:
        regula = REGULA_KODOWANIA if "UTF-8" in (blad or "") else "plik-nieczytelny"
        return [Naruszenie(str(sciezka), 0, regula, blad or "", blokujace=True)]

    komentarze, proza = komentarze_pliku(sciezka, tresc)
    naruszenia: list[Naruszenie] = []
    for nr, tekst in komentarze:
        naruszenia.extend(sprawdz_komentarz(sciezka, nr, tekst, cfg))

    znakow_calosc = max(len(tresc), 1)
    udzial = sum(len(t) for _, t in proza) / znakow_calosc
    if znakow_calosc >= cfg.min_znakow_do_udzialu and udzial > cfg.prog_udzialu:
        naruszenia.append(Naruszenie(
            str(sciezka), 0, "udzial-komentarzy",
            f"komentarze zajmują {udzial:.1%} pliku (próg {cfg.prog_udzialu:.0%})",
            blokujace=True,
        ))
    return naruszenia


def raportuj(blokujace: list[Naruszenie], ostrzezenia: list[Naruszenie], jako_json: bool,
             cicho: bool = False) -> None:
    if jako_json:
        print(json.dumps(
            {
                "blokujace": [n.__dict__ for n in blokujace],
                "ostrzezenia": [n.__dict__ for n in ostrzezenia],
            },
            ensure_ascii=False, indent=2,
        ))
        return
    if cicho and not blokujace and not ostrzezenia:
        return
    for n in blokujace + ostrzezenia:
        waga = "BLOKUJACE" if n.blokujace else "ostrzezenie"
        print(f"[{waga}] {n.plik}:{n.linia}: {n.regula}: {n.tresc}")
    print(f"\nRazem: {len(blokujace)} blokujących, {len(ostrzezenia)} ostrzeżeń.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sciezki", nargs="+", help="pliki lub katalogi do sprawdzenia")
    parser.add_argument("--config", type=Path, help="plik JSON z konfiguracją progów i allowlisty")
    parser.add_argument("--json", action="store_true", help="wypisz wynik jako JSON zamiast tekstu")
    parser.add_argument("--cicho", action="store_true",
                        help="bez wiersza podsumowania, gdy nie ma naruszeń (do użycia w hooku)")
    args = parser.parse_args(argv)

    cfg = konfiguracja_kontroli.wczytaj(args.config, args.sciezki)

    pliki, byly_braki = przechodzenie_repozytorium.zbierz_pliki(args.sciezki, set(ROZSZERZENIA_KODU))
    wszystkie: list[Naruszenie] = []
    for plik in pliki:
        wszystkie.extend(sprawdz_plik(plik, cfg))

    blokujace = [n for n in wszystkie if n.blokujace]
    ostrzezenia = [n for n in wszystkie if not n.blokujace]
    raportuj(blokujace, ostrzezenia, args.json, args.cicho)

    if byly_braki and not pliki:
        print("BŁĄD: żadna ze wskazanych ścieżek nie istnieje - nic nie zostało "
              "sprawdzone", file=sys.stderr)
        return KOD_AWARII
    if blokujace:
        return 3
    if ostrzezenia:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
