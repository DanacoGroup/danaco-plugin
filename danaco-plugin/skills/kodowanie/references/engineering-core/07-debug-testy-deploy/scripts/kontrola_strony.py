#!/usr/bin/env python3
"""Samokontrola agenta: przejdź własną stroną i zgłoś wszystko, co się zepsuło.

Po co: model deklaruje "gotowe" o interfejsie, którego nie otworzył. Ten skrypt
otwiera stronę w Chromium (headless), wykonuje podane kroki, zbiera błędy konsoli,
nieprzechwycone wyjątki i odpowiedzi HTTP >= 400, robi zrzuty ekranu i kończy się
kodem 1, jeśli cokolwiek jest nie tak.

Kroki wykonują się W KOLEJNOŚCI PODANIA argumentów.

Przykład:
    python kontrola_strony.py \
        --url http://localhost:3000/faktury \
        --klik "role=button[name=Nowa faktura]" \
        --wpisz "label=Kwota netto=1500,00" \
        --klik "role=button[name=Zapisz]" \
        --oczekuj-tekst "Faktura zapisana" \
        --zrzuty /tmp/kontrola --a11y

Składnia selektorów:
    role=button[name=Zapisz]   -> get_by_role("button", name="Zapisz")
    label=Kwota netto          -> get_by_label("Kwota netto")
    text=Faktura zapisana      -> get_by_text("Faktura zapisana")
    testid=wykres-przychodow   -> get_by_test_id("wykres-przychodow")
    placeholder=Szukaj         -> get_by_placeholder("Szukaj")
    dowolny inny ciąg          -> traktowany jako selektor CSS (ostateczność)

--wpisz przyjmuje "SELEKTOR=WARTOSC" (dzielone na ostatnim znaku '=').

Wymaga: pip install playwright && python -m playwright install chromium --with-deps
Do testów dostępności dodatkowo: pip install axe-playwright-python
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

# Katalog zrzutów w katalogu tymczasowym SYSTEMU: "/tmp/kontrola" na Windows
# tworzyło "C:\\tmp\\kontrola" na dysku systemowym.
KATALOG_ZRZUTOW_DOMYSLNY = Path(tempfile.gettempdir()) / "kontrola-strony"

try:
    from playwright.sync_api import Error as PwError, sync_playwright
except ImportError:
    print("BŁĄD: brak playwrighta. Uruchom:\n"
          "  pip install playwright && python -m playwright install chromium --with-deps",
          file=sys.stderr)
    sys.exit(2)


class _Krok(argparse.Action):
    """Zapisuje kroki w kolejności podania na wspólnej liście."""

    def __call__(self, parser, ns, wartosc, option_string=None):
        ns.kroki = getattr(ns, "kroki", None) or []
        ns.kroki.append((self.dest, wartosc))


def lokator(strona, selektor: str):
    if m := re.fullmatch(r"role=([a-z]+)\[name=(.+)\]", selektor):
        return strona.get_by_role(m.group(1), name=m.group(2))
    if selektor.startswith("role="):
        return strona.get_by_role(selektor[5:])
    if selektor.startswith("label="):
        return strona.get_by_label(selektor[6:])
    if selektor.startswith("text="):
        return strona.get_by_text(selektor[5:])
    if selektor.startswith("testid="):
        return strona.get_by_test_id(selektor[7:])
    if selektor.startswith("placeholder="):
        return strona.get_by_placeholder(selektor[12:])
    return strona.locator(selektor)


IGNOROWANE_KONSOLA = (
    "Download the React DevTools",
    "[vite] connected",
    "[HMR]",
)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Samokontrola strony: kliknij, wpisz, sprawdź konsolę i sieć.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--url", action=_Krok, required=True, help="adres do otwarcia")
    p.add_argument("--klik", action=_Krok, help="kliknij element (patrz składnia)")
    p.add_argument("--wpisz", action=_Krok, metavar="SELEKTOR=WARTOSC",
                   help="wpisz wartość w pole")
    p.add_argument("--oczekuj-tekst", action=_Krok, dest="oczekuj_tekst",
                   help="poczekaj, aż tekst będzie widoczny (do 10 s)")
    p.add_argument("--oczekuj-brak", action=_Krok, dest="oczekuj_brak",
                   help="poczekaj, aż element zniknie")
    p.add_argument("--zrzut", action=_Krok, help="zrób zrzut o tej nazwie")
    p.add_argument("--zrzuty", type=Path, default=KATALOG_ZRZUTOW_DOMYSLNY,
                   help="katalog na zrzuty (domyślnie {} w katalogu tymczasowym "
                        "systemu)".format(KATALOG_ZRZUTOW_DOMYSLNY.name))
    p.add_argument("--szerokosc", type=int, default=1440, help="szerokość okna")
    p.add_argument("--wysokosc", type=int, default=900, help="wysokość okna")
    p.add_argument("--a11y", action="store_true",
                   help="sprawdź dostępność (axe) po każdym otwarciu adresu")
    p.add_argument("--dozwolone-4xx", action="store_true",
                   help="nie traktuj odpowiedzi 4xx jako błędu (tylko 5xx)")
    p.add_argument("--json", action="store_true", help="raport w formacie JSON")

    a = p.parse_args()
    kroki: list[tuple[str, str]] = getattr(a, "kroki", []) or []
    a.zrzuty.mkdir(parents=True, exist_ok=True)
    # Katalog zrzutów jest wspólny między przebiegami, więc listowanie *.png
    # wciągałoby do raportu zrzuty z poprzednich uruchomień.
    zrobione_zrzuty: list[str] = []

    def zrzut(strona, nazwa: str, **dodatkowe) -> None:
        cel = a.zrzuty / f"{nazwa}.png"
        strona.screenshot(path=str(cel), **dodatkowe)
        zrobione_zrzuty.append(str(cel))

    bledy_konsoli: list[str] = []
    wyjatki: list[str] = []
    zle_odpowiedzi: list[str] = []
    padle_zadania: list[str] = []
    niepowodzenia: list[str] = []
    naruszenia_a11y: list[dict] = []
    prog_statusu = 500 if a.dozwolone_4xx else 400

    with sync_playwright() as pw:
        przegladarka = pw.chromium.launch(headless=True)
        kontekst = przegladarka.new_context(
            viewport={"width": a.szerokosc, "height": a.wysokosc},
            locale="pl-PL", timezone_id="Europe/Warsaw",
        )
        strona = kontekst.new_page()

        strona.on("console", lambda m: (
            bledy_konsoli.append(f"{m.type}: {m.text}")
            if m.type == "error" and not any(i in m.text for i in IGNOROWANE_KONSOLA)
            else None))
        strona.on("pageerror", lambda e: wyjatki.append(str(e)))
        strona.on("response", lambda r: (
            zle_odpowiedzi.append(f"{r.status} {r.request.method} {r.url}")
            if r.status >= prog_statusu else None))
        strona.on("requestfailed", lambda r: (
            padle_zadania.append(f"{r.url} :: {(r.failure or '')}")
            if not (r.failure or "").startswith("net::ERR_ABORTED") else None))

        licznik = 0
        for nazwa, wartosc in kroki:
            licznik += 1
            etykieta = f"{licznik:02d}-{nazwa}"
            try:
                if nazwa == "url":
                    strona.goto(wartosc, wait_until="domcontentloaded", timeout=30_000)
                    try:
                        strona.wait_for_load_state("networkidle", timeout=10_000)
                    except PwError:
                        pass                      # aplikacje z pollingiem/WS nigdy nie ucichną
                    zrzut(strona, etykieta, full_page=True)
                    if a.a11y:
                        naruszenia_a11y += _sprawdz_a11y(strona, wartosc, niepowodzenia)

                elif nazwa == "klik":
                    lokator(strona, wartosc).first.click(timeout=10_000)
                    strona.wait_for_timeout(300)

                elif nazwa == "wpisz":
                    sel, _, wart = wartosc.rpartition("=")
                    if not sel:
                        raise ValueError("format: SELEKTOR=WARTOSC")
                    lokator(strona, sel).first.fill(wart, timeout=10_000)

                elif nazwa == "oczekuj_tekst":
                    strona.get_by_text(wartosc).first.wait_for(
                        state="visible", timeout=10_000)

                elif nazwa == "oczekuj_brak":
                    lokator(strona, wartosc).first.wait_for(
                        state="hidden", timeout=10_000)

                elif nazwa == "zrzut":
                    zrzut(strona, f"{etykieta}-{wartosc}", full_page=True)

            except Exception as e:
                komunikat = str(e).splitlines()[0]
                niepowodzenia.append(f"[{etykieta}] {wartosc!r}: {komunikat}")
                try:
                    zrzut(strona, f"{etykieta}-BLAD", full_page=True)
                except Exception:
                    pass
                break                     # dalsze kroki na zepsutym stanie nie mają sensu

        przegladarka.close()

    raport = {
        "niepowodzenia_krokow": niepowodzenia,
        "bledy_konsoli": bledy_konsoli,
        "wyjatki_strony": wyjatki,
        "odpowiedzi_bledne": zle_odpowiedzi,
        "zadania_padle": padle_zadania,
        "naruszenia_dostepnosci": naruszenia_a11y,
        "zrzuty": sorted(zrobione_zrzuty),
    }
    problemy = sum(len(raport[k]) for k in
                   ("niepowodzenia_krokow", "bledy_konsoli", "wyjatki_strony",
                    "odpowiedzi_bledne", "zadania_padle", "naruszenia_dostepnosci"))

    if a.json:
        print(json.dumps(raport, ensure_ascii=False, indent=2))
    else:
        for klucz, pozycje in raport.items():
            if klucz == "zrzuty" or not pozycje:
                continue
            print(f"\n### {klucz.replace('_', ' ').upper()} ({len(pozycje)})",
                  file=sys.stderr)
            for pozycja in pozycje[:25]:
                print(f"  - {pozycja if not isinstance(pozycja, dict) else pozycja['id']}",
                      file=sys.stderr)
        print(f"\nZrzuty: {a.zrzuty}", file=sys.stderr)
        print("SAMOKONTROLA: OK" if problemy == 0
              else f"SAMOKONTROLA: {problemy} problem(ów) — NIE deklaruj gotowości",
              file=sys.stderr)

    return 0 if problemy == 0 else 1


def _sprawdz_a11y(strona, url: str, niepowodzenia: list[str]) -> list[dict]:
    try:
        from axe_playwright_python.sync_playwright import Axe
    except ImportError:
        niepowodzenia.append("--a11y wymaga: pip install axe-playwright-python")
        return []
    wynik = Axe().run(strona)
    return [{"id": f"{v['id']} ({len(v['nodes'])}x) @ {url}", "opis": v["description"]}
            for v in wynik.response["violations"]
            if v["impact"] in ("serious", "critical")]


if __name__ == "__main__":
    sys.exit(main())
