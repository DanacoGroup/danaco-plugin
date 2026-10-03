"""Wspólne funkcje skryptów wtyczki danaco-konfiguracja (biblioteka standardowa Pythona).

Moduł ładuje indeksy z `wspolne/indeksy/` (klucze ustawień, zmienne, flagi, narzędzia,
zdarzenia hooków), porównuje wersje CLI, czyta JSON w trybie ścisłym i waliduje dokument
względem schematu JSON (podzbiór draft-07 wystarczający dla schematu ustawień
`https://json.schemastore.org/claude-code-settings.json`). Gdy w środowisku jest pakiet
`jsonschema`, walidacja schematem korzysta z niego.
"""
from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
INDEKSY = KORZEN / "wspolne" / "indeksy"
SCHEMAT = KORZEN / "scripts" / "schematy" / "claude-code-settings.schema.json"

ZASIEGI_TYLKO_ZARZADZANE = {"Managed", "Managed (tylko z urządzenia)"}
ZASIEGI_BEZ_PROJEKTU = {"User or managed"}
ZASIEGI_BEZ_WSPOLNEGO_PROJEKTU = {"User, local, or managed", "User, local, managed or --settings"}


# --------------------------------------------------------------------------- indeksy

def _tsv(nazwa: str) -> list[dict]:
    with open(INDEKSY / nazwa, newline="", encoding="utf-8") as plik:
        return list(csv.DictReader(plik, delimiter="\t"))


@lru_cache(maxsize=None)
def klucze_ustawien() -> dict[str, dict]:
    return {wiersz["klucz"]: wiersz for wiersz in _tsv("ustawienia.tsv")}


@lru_cache(maxsize=None)
def zmienne() -> dict[str, dict]:
    return {wiersz["zmienna"]: wiersz for wiersz in _tsv("zmienne.tsv")}


@lru_cache(maxsize=None)
def flagi() -> list[dict]:
    return _tsv("flagi-cli.tsv")


@lru_cache(maxsize=None)
def narzedzia() -> dict[str, dict]:
    return {wiersz["narzedzie"]: wiersz for wiersz in _tsv("narzedzia.tsv")}


@lru_cache(maxsize=None)
def zdarzenia_hookow() -> dict[str, dict]:
    return {wiersz["zdarzenie"]: wiersz for wiersz in _tsv("hooki-zdarzenia.tsv")}


# --------------------------------------------------------------------------- wersje

def wersja(tekst: str) -> tuple[int, ...]:
    znalezione = re.search(r"(\d+)\.(\d+)\.(\d+)", tekst or "")
    return tuple(int(x) for x in znalezione.groups()) if znalezione else ()


def wersja_mniejsza(a: str, b: str) -> bool:
    """Czy wersja `a` jest starsza niż `b` (puste wersje nie są porównywane)."""
    wa, wb = wersja(a), wersja(b)
    return bool(wa and wb and wa < wb)


# --------------------------------------------------------------------------- JSON

class BladJson(Exception):
    pass


def czytaj_json(sciezka: Path | str) -> object:
    """Czyta JSON ściśle jak Claude Code: komentarz `//` i przecinek końcowy to błąd."""
    tekst = Path(sciezka).read_text(encoding="utf-8")
    try:
        return json.loads(tekst)
    except json.JSONDecodeError as blad:
        podpowiedz = ""
        if re.search(r"^\s*//", tekst, re.M) or "/*" in tekst:
            podpowiedz = " (plik ma komentarz — ustawienia Claude Code to ścisły JSON)"
        elif re.search(r",\s*[}\]]", tekst):
            podpowiedz = " (przecinek przed nawiasem zamykającym — ścisły JSON go nie dopuszcza)"
        raise BladJson(f"{blad.msg} w wierszu {blad.lineno}, kolumna {blad.colno}{podpowiedz}") from None


# --------------------------------------------------------------------------- schemat

TYPY = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _pasuje_typ(wartosc: object, typ: str) -> bool:
    if typ == "integer":
        return isinstance(wartosc, int) and not isinstance(wartosc, bool)
    if typ == "number":
        return isinstance(wartosc, (int, float)) and not isinstance(wartosc, bool)
    return isinstance(wartosc, TYPY.get(typ, object))


class MiniWalidator:
    """Podzbiór draft-07: type, enum, const, properties, additionalProperties, required,
    items, minItems, maxItems, uniqueItems, minLength, pattern, minimum, maximum,
    exclusiveMinimum, propertyNames, anyOf, oneOf, allOf, not, if/then/else, $ref (#/…)."""

    def __init__(self, schemat: dict):
        self.korzen = schemat

    def _ref(self, ref: str) -> dict:
        wezel: object = self.korzen
        for czesc in ref.lstrip("#/").split("/"):
            wezel = wezel[czesc.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
        return wezel  # type: ignore[return-value]

    def bledy(self, wartosc: object, schemat: dict | bool | None = None, sciezka: str = "") -> list[tuple[str, str]]:
        schemat = self.korzen if schemat is None else schemat
        if schemat is True or schemat == {}:
            return []
        if schemat is False:
            return [(sciezka or "/", "wartość niedozwolona przez schemat")]
        wynik: list[tuple[str, str]] = []
        if "$ref" in schemat:
            wynik += self.bledy(wartosc, self._ref(schemat["$ref"]), sciezka)
        typ = schemat.get("type")
        if typ:
            typy = typ if isinstance(typ, list) else [typ]
            if not any(_pasuje_typ(wartosc, t) for t in typy):
                return wynik + [(sciezka or "/", f"oczekiwany typ {'/'.join(typy)}, jest {type(wartosc).__name__}")]
        if "enum" in schemat and wartosc not in schemat["enum"]:
            wynik.append((sciezka or "/", f"wartość {json.dumps(wartosc, ensure_ascii=False)[:60]} spoza listy "
                                         f"{json.dumps(schemat['enum'], ensure_ascii=False)[:160]}"))
        if "const" in schemat and wartosc != schemat["const"]:
            wynik.append((sciezka or "/", f"oczekiwana stała {json.dumps(schemat['const'])}"))
        if isinstance(wartosc, str):
            if len(wartosc) < schemat.get("minLength", 0):
                wynik.append((sciezka, f"tekst krótszy niż {schemat['minLength']}"))
            if "pattern" in schemat and not re.search(schemat["pattern"], wartosc):
                wynik.append((sciezka, f"tekst nie pasuje do wzorca {schemat['pattern']}"))
        if _pasuje_typ(wartosc, "number"):
            if "minimum" in schemat and wartosc < schemat["minimum"]:  # type: ignore[operator]
                wynik.append((sciezka, f"wartość mniejsza niż {schemat['minimum']}"))
            if "maximum" in schemat and wartosc > schemat["maximum"]:  # type: ignore[operator]
                wynik.append((sciezka, f"wartość większa niż {schemat['maximum']}"))
            if "exclusiveMinimum" in schemat and wartosc <= schemat["exclusiveMinimum"]:  # type: ignore[operator]
                wynik.append((sciezka, f"wartość musi być większa niż {schemat['exclusiveMinimum']}"))
        if isinstance(wartosc, list):
            if len(wartosc) < schemat.get("minItems", 0):
                wynik.append((sciezka, f"lista krótsza niż {schemat['minItems']}"))
            if "maxItems" in schemat and len(wartosc) > schemat["maxItems"]:
                wynik.append((sciezka, f"lista dłuższa niż {schemat['maxItems']}"))
            if schemat.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in wartosc}) != len(wartosc):
                wynik.append((sciezka, "powtórzone elementy listy"))
            if isinstance(schemat.get("items"), dict):
                for indeks, element in enumerate(wartosc):
                    wynik += self.bledy(element, schemat["items"], f"{sciezka}/{indeks}")
        if isinstance(wartosc, dict):
            for wymagane in schemat.get("required", []):
                if wymagane not in wartosc:
                    wynik.append((sciezka or "/", f"brak wymaganego pola „{wymagane}”"))
            wlasciwosci = schemat.get("properties", {})
            dodatkowe = schemat.get("additionalProperties", True)
            for klucz, element in wartosc.items():
                if "propertyNames" in schemat:
                    wynik += [(f"{sciezka}/{klucz}", f"nazwa klucza: {opis}")
                              for _, opis in self.bledy(klucz, schemat["propertyNames"], "")]
                if klucz in wlasciwosci:
                    wynik += self.bledy(element, wlasciwosci[klucz], f"{sciezka}/{klucz}")
                elif dodatkowe is False:
                    wynik.append((f"{sciezka}/{klucz}", "klucz nieznany schematowi (additionalProperties: false)"))
                elif isinstance(dodatkowe, dict):
                    wynik += self.bledy(element, dodatkowe, f"{sciezka}/{klucz}")
        if "allOf" in schemat:
            for podschemat in schemat["allOf"]:
                wynik += self.bledy(wartosc, podschemat, sciezka)
        for slowo in ("anyOf", "oneOf"):
            if slowo in schemat:
                wyniki = [self.bledy(wartosc, podschemat, sciezka) for podschemat in schemat[slowo]]
                pasujace = sum(1 for w in wyniki if not w)
                if pasujace == 0:
                    najblizszy = min(wyniki, key=len)
                    wynik.append((sciezka or "/", f"żaden wariant {slowo} nie pasuje; najbliższy: "
                                                  + "; ".join(f"{s or '/'}: {o}" for s, o in najblizszy[:2])))
                elif slowo == "oneOf" and pasujace > 1:
                    wynik.append((sciezka or "/", "pasuje więcej niż jeden wariant oneOf"))
        if "not" in schemat and not self.bledy(wartosc, schemat["not"], sciezka):
            wynik.append((sciezka or "/", "wartość pasuje do schematu zakazanego (not)"))
        if "if" in schemat:
            if not self.bledy(wartosc, schemat["if"], sciezka):
                if "then" in schemat:
                    wynik += self.bledy(wartosc, schemat["then"], sciezka)
            elif "else" in schemat:
                wynik += self.bledy(wartosc, schemat["else"], sciezka)
        return wynik


def bledy_schematu(dokument: object, schemat: dict) -> tuple[str, list[tuple[str, str]]]:
    """Zwraca (silnik, lista (ścieżka, opis)). Korzysta z `jsonschema`, gdy jest dostępny."""
    try:
        import jsonschema  # type: ignore[import-not-found]

        walidator = jsonschema.Draft7Validator(schemat)
        lista = []
        for blad in walidator.iter_errors(dokument):
            sciezka = "/" + "/".join(str(x) for x in blad.absolute_path)
            lista.append((sciezka if sciezka != "/" else "/", blad.message))
        return "jsonschema", lista
    except ImportError:
        return "wbudowany", MiniWalidator(schemat).bledy(dokument)


# --------------------------------------------------------------------------- reguły uprawnień

REGULA = re.compile(r"^(?P<narzedzie>[A-Za-z_][\w\-]*(?:__[\w\-.*]+)*\*?)(?:\((?P<argument>.*)\))?$", re.S)


def rozbierz_regule(regula: str) -> tuple[str, str | None] | None:
    dopasowanie = REGULA.match(regula.strip())
    if not dopasowanie:
        return None
    return dopasowanie.group("narzedzie"), dopasowanie.group("argument")


def wygladaja_na_sekret(nazwa: str) -> bool:
    """Nazwa zmiennej sugerująca sekret (MAX_THINKING_TOKENS czy *_FILE_DESCRIPTOR nim nie są)."""
    duze = nazwa.upper()
    if re.search(r"_(FILE|FILE_DESCRIPTOR|HELPER|TTL_MS|PATH|DIR|SCOPES)$", duze):
        return False
    return bool(re.search(r"(^|_)(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|CREDENTIALS?|PASSPHRASE|AUTH)($|_)", duze))
