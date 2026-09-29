#!/usr/bin/env python3
"""Walidator standardu nazewnictwa Danaco (nazwy_guard.py).

Sprawdza pliki źródłowe i etykiety UI pod kątem standardu z paczki
`standardy-nazewnictwa`:
- wymyślone oznaczenia literowo-numeryczne komponentów — tylko tam, gdzie
  identyfikator jest DEKLAROWANY (`const`, `class`, `type`, `func`, `struct`…);
  dowolny token „słowo + liczba” w treści pliku (`Col2`, `Row1`, wersja stosu)
  nie jest naruszeniem,
- etykiety UI będące zdaniami opisowymi zamiast krótkich nazw funkcji
  (`label`, `aria-label`, `placeholder`, `buttonText`; `title` jest pominięty,
  bo w Go, Rust i w komunikatach oznacza tytuł, nie etykietę),
- identyfikatory zbudowane z metafory zamiast funkcji (słownik konfigurowalny),
- pliki, których nie da się odczytać jako UTF-8 (kontrola nie została wykonana).

Reguła `etykieta-jako-zdanie` jest ostrzeżeniem, nie naruszeniem blokującym:
kryterium jest heurystyczne i trafia także poprawne komunikaty błędów.

Progi i słowniki: `scripts/konfiguracja_kontroli.py` oraz opcjonalny plik
`konfiguracja-dyscypliny.json` w korzeniu sprawdzanego repozytorium.

Użycie:
    python3 nazwy_guard.py <plik-lub-katalog> [...]
    python3 nazwy_guard.py --config konfiguracja-dyscypliny.json src/

Kody wyjścia: 0 brak naruszeń, 2 tylko ostrzeżenia, 3 co najmniej jedno
blokujące, 4 awaria kontroli (zła konfiguracja, brak modułów wspólnych).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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

ROZSZERZENIA = {".go", ".ts", ".tsx", ".js", ".jsx", ".rs", ".py"}
MAKSIMUM_SLOW_ETYKIETY = 6

SLOWA_DEKLARACJI = r"const|let|var|function|func|class|type|interface|struct|enum|fn|def"

WZORZEC_OZNACZENIA = re.compile(
    rf"(?<![\w-])(?:{SLOWA_DEKLARACJI})\s+([A-Z][a-zA-Z]{{1,20}})[_-]?([A-Z]\d{{1,3}}|\d{{1,3}}[A-Z]?)(?![\w])"
)

WZORZEC_ETYKIETY = re.compile(
    r'(?<![\w.])(label|aria-label|placeholder|buttonText)\s*[:=]\s*'
    r'(?:"((?:[^"\\]|\\.){1,200})"|\'((?:[^\'\\]|\\.){1,200})\'|`((?:[^`\\]|\\.){1,200})`)'
)


def _naruszenie(sciezka: Path, nr: int, regula: str, tresc: str, blokujace: bool) -> dict:
    return {"plik": str(sciezka), "linia": nr, "regula": regula, "tresc": tresc,
            "blokujace": blokujace}


def sprawdz_oznaczenia(sciezka: Path, nr: int, linia: str, cfg: Konfiguracja) -> list[dict]:
    naruszenia = []
    for dopasowanie in WZORZEC_OZNACZENIA.finditer(linia):
        pelne = dopasowanie.group(1) + dopasowanie.group(2)
        if cfg.oznaczenie_dozwolone(pelne):
            continue
        naruszenia.append(_naruszenie(
            sciezka, nr, "oznaczenie-literowo-numeryczne",
            f"możliwe wymyślone oznaczenie komponentu: {pelne!r}", False,
        ))
    return naruszenia


def sprawdz_etykiety(sciezka: Path, nr: int, linia: str) -> list[dict]:
    naruszenia = []
    for dopasowanie in WZORZEC_ETYKIETY.finditer(linia):
        tekst = next((g for g in dopasowanie.groups()[1:] if g is not None), "")
        if len(tekst.split()) <= MAKSIMUM_SLOW_ETYKIETY:
            continue
        naruszenia.append(_naruszenie(
            sciezka, nr, "etykieta-jako-zdanie",
            f"etykieta wygląda na opis zdaniowy, nie krótką nazwę funkcji: {tekst!r}", False,
        ))
    return naruszenia


_LITERALY = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`')
_KOMENTARZ_LINIOWY = re.compile(r"(#|//).*$")
_IDENTYFIKATOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CZLONY_IDENTYFIKATORA = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")


def czlony_identyfikatorow(linia: str) -> set[str]:
    """Człony nazw z linii kodu, bez literałów i komentarzy.

    Reguła dotyczy NAZW, nie prozy: metafora w komunikacie dla użytkownika albo
    w słowniku reguły nie jest naruszeniem nazewnictwa. Nazwa jest rozbijana na
    człony, więc dłuższy rzeczownik techniczny nie trafia na krótszy wpis
    słownika, którym się zaczyna.
    """
    kod = _KOMENTARZ_LINIOWY.sub("", _LITERALY.sub(" ", linia))
    czlony: set[str] = set()
    for identyfikator in _IDENTYFIKATOR.findall(kod):
        for czlon in _CZLONY_IDENTYFIKATORA.findall(identyfikator):
            czlony.add(czlon.lower())
    return czlony


def sprawdz_metafory(sciezka: Path, nr: int, linia: str, slowa: set[str]) -> list[dict]:
    naruszenia = []
    czlony = czlony_identyfikatorow(linia)
    for slowo in sorted(slowa):
        if slowo.lower() in czlony:
            naruszenia.append(_naruszenie(
                sciezka, nr, "nazwa-metaforyczna",
                f"identyfikator zawiera słowo metaforyczne {slowo!r} zamiast opisu funkcji",
                False,
            ))
    return naruszenia


def sprawdz_plik(sciezka: Path, cfg: Konfiguracja) -> list[dict]:
    tresc, blad = przechodzenie_repozytorium.wczytaj_tekst(sciezka)
    if tresc is None:
        regula = "kodowanie-pliku" if "UTF-8" in (blad or "") else "plik-nieczytelny"
        return [_naruszenie(sciezka, 0, regula, blad or "", True)]

    naruszenia: list[dict] = []
    for nr, linia in enumerate(tresc.splitlines(), start=1):
        naruszenia.extend(sprawdz_oznaczenia(sciezka, nr, linia, cfg))
        naruszenia.extend(sprawdz_etykiety(sciezka, nr, linia))
        naruszenia.extend(sprawdz_metafory(sciezka, nr, linia, cfg.slowa_metaforyczne))
    return naruszenia


def raportuj(blokujace: list[dict], ostrzezenia: list[dict], jako_json: bool,
             cicho: bool = False) -> None:
    if jako_json:
        print(json.dumps({"blokujace": blokujace, "ostrzezenia": ostrzezenia},
                         ensure_ascii=False, indent=2))
        return
    if cicho and not blokujace and not ostrzezenia:
        return
    for n in blokujace + ostrzezenia:
        waga = "BLOKUJACE" if n["blokujace"] else "ostrzezenie"
        print(f"[{waga}] {n['plik']}:{n['linia']}: {n['regula']}: {n['tresc']}")
    print(f"\nRazem: {len(blokujace)} blokujących, {len(ostrzezenia)} ostrzeżeń.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sciezki", nargs="+")
    parser.add_argument("--config", type=Path,
                        help="JSON: slowaMetaforyczne, allowlistaNazw, progi kontroli")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--cicho", action="store_true",
                        help="bez wiersza podsumowania, gdy nie ma naruszeń (do użycia w hooku)")
    args = parser.parse_args(argv)

    cfg = konfiguracja_kontroli.wczytaj(args.config, args.sciezki)

    pliki, byly_braki = przechodzenie_repozytorium.zbierz_pliki(args.sciezki, ROZSZERZENIA)
    wszystkie: list[dict] = []
    for plik in pliki:
        wszystkie.extend(sprawdz_plik(plik, cfg))

    blokujace = [n for n in wszystkie if n["blokujace"]]
    ostrzezenia = [n for n in wszystkie if not n["blokujace"]]
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
