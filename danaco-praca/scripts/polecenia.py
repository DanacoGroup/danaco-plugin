"""Polecenia właściciela: rozpoznanie w treści wiadomości i zmiana stanu.

Polecenie liczy się wyłącznie na początku wiersza wiadomości (po odstępach), w postaci
`/nazwa` albo `/danaco-praca:nazwa`. Wzmianka w środku zdania, w ścieżce
(`skills/praca/SKILL.md`) czy w cytacie z odstępem przed ukośnikiem w środku wiersza nie
zmienia niczego. Rozpoznawana jest też postać rozwinięta przez klienta
(`<command-name>/praca</command-name>` z `<command-args>`).
"""

from __future__ import annotations

import re

#: polecenie -> (klucz stanu, wartość); `tryb` tylko pokazuje stan.
POLECENIA: dict[str, tuple[str, bool] | None] = {
    "praca": ("praca", True),
    "koniec-pracy": ("praca", False),
    "bez-bash": ("bash", True),
    "z-bash": ("bash", False),
    "bez-python": ("python", True),
    "z-python": ("python", False),
    "bez-masowych": ("masowe", True),
    "z-masowymi": ("masowe", False),
    "reczne-pisanie": ("reczne", True),
    "z-skryptami": ("reczne", False),
    "bez-sleep": ("sleep", True),
    "z-sleep": ("sleep", False),
    "bez-podagentow": ("podagenci", True),
    "z-podagentami": ("podagenci", False),
    "sudo-nie": ("sudo", True),
    "sudo-tak": ("sudo", False),
    "tryb": None,
}

_NAZWY = "|".join(sorted((re.escape(n) for n in POLECENIA), key=len, reverse=True))
#: Polecenie na początku wiersza; po nazwie koniec wiersza albo odstęp.
WIERSZ = re.compile(rf"^\s*/(?:danaco-praca:)?({_NAZWY})(?:[ \t]+(.*))?\s*$")
ROZWINIETE = re.compile(rf"<command-name>\s*/?(?:danaco-praca:)?({_NAZWY})\s*</command-name>")
ARGUMENTY = re.compile(r"<command-args>(.*?)</command-args>", re.S)
#: Wystąpienie polecenia jako tokenu w dowolnym tekście (do straży przed wstrzyknięciem).
TOKEN = re.compile(rf"(?:^|[\s\"'`(=\\])/(?:danaco-praca:)?({_NAZWY})(?=$|[\s\"'`)\\.,;:!?])", re.M)


def rozpoznaj(tekst: str) -> tuple[list[str], str]:
    """Lista poleceń (w kolejności) i reszta wiadomości bez wierszy-poleceń.

    Argumenty `/praca` (treść w tym samym wierszu) trafiają na początek reszty, bo są
    zleceniem.
    """
    tekst = tekst or ""
    polecenia: list[str] = []
    reszta: list[str] = []
    rozwiniete = ROZWINIETE.findall(tekst)
    if rozwiniete:
        polecenia.extend(rozwiniete)
        argumenty = ARGUMENTY.search(tekst)
        if argumenty and argumenty.group(1).strip():
            reszta.append(argumenty.group(1).strip())
        tekst = ARGUMENTY.sub("", ROZWINIETE.sub("", tekst))
        tekst = re.sub(r"<command-message>.*?</command-message>", "", tekst, flags=re.S)
    for wiersz in tekst.splitlines():
        dopasowanie = WIERSZ.match(wiersz)
        if dopasowanie:
            polecenia.append(dopasowanie.group(1))
            if dopasowanie.group(2):
                reszta.append(dopasowanie.group(2).strip())
        else:
            reszta.append(wiersz)
    return polecenia, "\n".join(reszta).strip()
