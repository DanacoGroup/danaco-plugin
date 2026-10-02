"""Polecenia właściciela: rozpoznanie w treści wiadomości i opis ich działania.

Konwencja nazw (czasownik pierwszy, żeby menu kontekstowe grupowało po przedrostku):
blokady to `/blokuj-<temat>` ↔ `/odblokuj-<temat>` (wszystkie `/blokuj-*` i wszystkie
`/odblokuj-*` stoją w menu razem). Stan ma przedrostek `/tryb` (`/tryb`, `/tryb-dziennik`,
`/tryb-wyczysc`), sesje przedrostek `/sesja-` (`/sesja-id`, `/sesja-lista`,
`/sesja-przejmij`). Tryb pracy ciągłej ma własną, naturalną nazwę (`/praca` ↔
`/koniec-pracy`), bo jest trybem, nie blokadą.

Polecenie liczy się wyłącznie na początku wiersza wiadomości (po odstępach), w postaci
`/nazwa` albo `/danaco-praca:nazwa`. Wzmianka w środku zdania, w ścieżce
(`skills/praca/SKILL.md`) czy w cytacie nie przełącza niczego. Rozpoznawana jest też
postać rozwinięta przez klienta (`<command-name>/praca</command-name>` + `<command-args>`).
"""

from __future__ import annotations

import re

from stan import TEMATY

#: polecenie -> akcja:
#:   ("praca", bool)          tryb pracy ciągłej (wł./wył.)
#:   ("blok", klucz, bool)    blokada (wł./wył.)
#:   ("widok", nazwa)         pokazuje stan/sesję, nie zmienia niczego
#:   ("akcja", nazwa)         wykonuje czynność (reset trybów, przejęcie sesji)
POLECENIA: dict[str, tuple] = {
    "praca": ("praca", True),
    "koniec-pracy": ("praca", False),
    "tryb": ("widok", "tryb"),
    "tryb-dziennik": ("widok", "dziennik"),
    "tryb-wyczysc": ("akcja", "wyczysc"),
    "sesja-id": ("widok", "sesja-id"),
    "sesja-lista": ("widok", "sesje"),
    "sesja-przejmij": ("akcja", "przejmij"),
}
for _temat, _klucz in TEMATY.items():
    POLECENIA[f"blokuj-{_temat}"] = ("blok", _klucz, True)
    POLECENIA[f"odblokuj-{_temat}"] = ("blok", _klucz, False)

_NAZWY = "|".join(sorted((re.escape(n) for n in POLECENIA), key=len, reverse=True))
#: Polecenie na początku wiersza; po nazwie koniec wiersza albo odstęp i argument.
WIERSZ = re.compile(rf"^\s*/(?:danaco-praca:)?({_NAZWY})(?:[ \t]+(.*))?\s*$")
ROZWINIETE = re.compile(rf"<command-name>\s*/?(?:danaco-praca:)?({_NAZWY})\s*</command-name>")
ARGUMENTY = re.compile(r"<command-args>(.*?)</command-args>", re.S)
#: Wystąpienie polecenia jako tokenu w dowolnym tekście (do straży przed wstrzyknięciem).
TOKEN = re.compile(rf"(?:^|[\s\"'`(=\\])/(?:danaco-praca:)?({_NAZWY})(?=$|[\s\"'`)\\.,;:!?])", re.M)


def rozpoznaj(tekst: str) -> tuple[list[tuple[str, str]], str]:
    """Lista (polecenie, argument) w kolejności oraz reszta wiadomości bez wierszy-poleceń.

    Argument to tekst w tym samym wierszu po nazwie polecenia (zlecenie dla `/praca`,
    identyfikator dla `/sesja-przejmij`). Reszta to wiersze, które poleceniami nie są.
    """
    tekst = tekst or ""
    pary: list[tuple[str, str]] = []
    reszta: list[str] = []
    rozwiniete = ROZWINIETE.findall(tekst)
    if rozwiniete:
        argumenty = ARGUMENTY.search(tekst)
        arg = argumenty.group(1).strip() if argumenty else ""
        for i, nazwa in enumerate(rozwiniete):
            pary.append((nazwa, arg if i == 0 else ""))
        tekst = ARGUMENTY.sub("", ROZWINIETE.sub("", tekst))
        tekst = re.sub(r"<command-message>.*?</command-message>", "", tekst, flags=re.S)
    for wiersz in tekst.splitlines():
        dopasowanie = WIERSZ.match(wiersz)
        if dopasowanie:
            pary.append((dopasowanie.group(1), (dopasowanie.group(2) or "").strip()))
        else:
            reszta.append(wiersz)
    return pary, "\n".join(reszta).strip()
