#!/usr/bin/env python3
"""Uruchom serwer(y), poczekaj na gotowość, wykonaj polecenie, posprzątaj.

Po co: modele notorycznie uruchamiają `npm run dev &` i od razu strzelają do portu,
dostają ECONNREFUSED i zaczynają diagnozować nieistniejący problem. Ten skrypt czeka
na REALNĄ gotowość (odpowiedź HTTP, nie samo otwarcie portu) i przy niepowodzeniu
wypisuje wyjście serwera — czyli to, co zawiera przyczynę.

Przykłady:
    python z_serwerem.py --serwer "npm run dev" --url http://localhost:3000 \
        -- python kontrola_strony.py --url http://localhost:3000

    python z_serwerem.py \
        --serwer "cd backend && uvicorn app:app --port 8000" --url http://localhost:8000/zycie \
        --serwer "cd frontend && npm run dev" --url http://localhost:5173 \
        -- npx playwright test

    python z_serwerem.py --serwer "npm start" --port 3000 -- curl -sS localhost:3000

Kod wyjścia: kod wyjścia uruchomionego polecenia, albo 1 gdy serwer nie wstał.
"""

from __future__ import annotations

import argparse
import collections
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

JEST_WINDOWS = sys.platform.startswith("win")
# Własna grupa procesów daje pewne sprzątanie całego drzewa serwera. Na Windows
# `start_new_session` zgłasza ValueError, więc grupę zakłada flaga CreationFlags.
DODATKOWE_POPEN = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if JEST_WINDOWS
                   else {"start_new_session": True})
LIMIT_LINII_WYJSCIA = 200


class Wyjscie:
    """Czyta strumień serwera od chwili uruchomienia i trzyma jego ogon.

    Potok o rozmiarze 64 KiB zapełnia się przy starcie każdego większego projektu;
    serwer blokuje się wtedy na zapisie i nigdy nie odpowie na sondę, a skrypt
    raportuje „serwer nie wstał”. Dlatego strumień jest opróżniany w wątku.
    """

    def __init__(self, strumien, limit_linii: int = LIMIT_LINII_WYJSCIA) -> None:
        self.linie: collections.deque = collections.deque(maxlen=limit_linii)
        self._watek = threading.Thread(target=self._czytaj, args=(strumien,), daemon=True)
        self._watek.start()

    def _czytaj(self, strumien) -> None:
        if strumien is None:
            return
        try:
            for surowa in iter(strumien.readline, b""):
                self.linie.append(surowa.decode("utf-8", "replace").rstrip("\n"))
        except (OSError, ValueError):
            return


class _Sonda(argparse.Action):
    """Zbiera --url i --port w JEDNEJ liście, w kolejności podania w wierszu
    poleceń. Osobne listy parowane potem przez zip() mieszały serwery ze
    sondami, gdy oba rodzaje wystąpiły naprzemiennie."""

    def __call__(self, parser, przestrzen, wartosc, option_string=None):
        sondy = getattr(przestrzen, "sondy", None) or []
        sondy.append((self.dest, wartosc))
        setattr(przestrzen, "sondy", sondy)


def _czekaj_na_port(host: str, port: int, limit_s: float) -> bool:
    koniec = time.time() + limit_s
    while time.time() < koniec:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def _czekaj_na_url(url: str, limit_s: float) -> bool:
    koniec = time.time() + limit_s
    while time.time() < koniec:
        try:
            with urllib.request.urlopen(url, timeout=2) as odp:
                if odp.status < 500:
                    return True
        except urllib.error.HTTPError as e:
            if e.code < 500:            # 401/404 też znaczy, że serwer żyje
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def _wypisz_wyjscie(wyjscie: Wyjscie | None, etykieta: str, limit_linii: int = 60) -> None:
    """Wypisz to, co serwer zdążył napisać. Tu zwykle jest przyczyna niewstania."""
    if wyjscie is None:
        return
    linie = list(wyjscie.linie)[-limit_linii:]
    if not linie:
        return
    print(f"\n--- {etykieta} (ostatnie {len(linie)} linii) ---", file=sys.stderr)
    print("\n".join(linie), file=sys.stderr)


def _zabij(proces: subprocess.Popen) -> None:
    if proces.poll() is not None:
        return
    try:
        if JEST_WINDOWS:
            proces.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(proces.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, AttributeError, OSError, ValueError):
        proces.terminate()
    try:
        proces.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            if JEST_WINDOWS:
                proces.kill()
            else:
                os.killpg(os.getpgid(proces.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, AttributeError, OSError, ValueError):
            proces.kill()
        proces.wait(timeout=5)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Uruchom serwer(y), poczekaj na gotowość, wykonaj polecenie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--serwer", action="append", dest="serwery", required=True,
                   help="polecenie uruchamiające serwer (można powtórzyć)")
    p.add_argument("--url", action=_Sonda, dest="url",
                   help="adres sprawdzany do skutku (zalecane); po jednym na --serwer")
    p.add_argument("--port", action=_Sonda, dest="port", type=int,
                   help="alternatywa dla --url: czekaj tylko na otwarcie portu TCP")
    p.add_argument("--limit", type=float, default=90.0,
                   help="ile sekund czekać na jeden serwer (domyślnie 90)")
    p.add_argument("polecenie", nargs=argparse.REMAINDER,
                   help="po ' -- ': polecenie do wykonania przy działających serwerach")

    a = p.parse_args()
    polecenie = a.polecenie[1:] if a.polecenie and a.polecenie[0] == "--" else a.polecenie
    if not polecenie:
        p.error("brak polecenia do wykonania (po ' -- ')")

    sondy: list[tuple[str, object]] = getattr(a, "sondy", None) or []
    if len(sondy) != len(a.serwery):
        p.error(f"liczba --url/--port ({len(sondy)}) musi równać się liczbie "
                f"--serwer ({len(a.serwery)})")

    procesy: list[tuple[str, subprocess.Popen]] = []
    wyjscia: dict[int, Wyjscie] = {}
    try:
        for polecenie_serwera, (rodzaj, sonda) in zip(a.serwery, sondy):
            print(f"[z_serwerem] uruchamiam: {polecenie_serwera}", file=sys.stderr)
            proc = subprocess.Popen(
                polecenie_serwera, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                **DODATKOWE_POPEN,
            )
            procesy.append((polecenie_serwera, proc))
            wyjscia[proc.pid] = Wyjscie(proc.stdout)

            if rodzaj == "url":
                gotowy = _czekaj_na_url(str(sonda), a.limit)
                opis = str(sonda)
            else:
                gotowy = _czekaj_na_port("127.0.0.1", int(sonda), a.limit)
                opis = f"port {sonda}"

            if not gotowy:
                print(f"[z_serwerem] BŁĄD: serwer nie odpowiedział na {opis} "
                      f"w {a.limit:.0f} s", file=sys.stderr)
                _wypisz_wyjscie(wyjscia.get(proc.pid), polecenie_serwera)
                return 1
            print(f"[z_serwerem] gotowy: {opis}", file=sys.stderr)

        print(f"[z_serwerem] wykonuję: {' '.join(polecenie)}\n", file=sys.stderr)
        wynik = subprocess.run(polecenie)
        if wynik.returncode != 0:
            for etykieta, proc in procesy:
                _wypisz_wyjscie(wyjscia.get(proc.pid), etykieta, limit_linii=40)
        return wynik.returncode

    finally:
        for etykieta, proc in reversed(procesy):
            _zabij(proc)
        if procesy:
            print(f"\n[z_serwerem] zatrzymano {len(procesy)} serwer(ów)", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
