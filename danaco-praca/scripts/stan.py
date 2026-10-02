"""Stan trybów pracy danaco-praca: osobny dla każdej sesji, podpisany, z dziennikiem.

Stan zapisuje wyłącznie hook (`UserPromptSubmit` na polecenie właściciela, a liczniki pętli
`PreToolUse`, `Stop` i `SubagentStop`). Leży w katalogu danych wtyczki
(`${CLAUDE_PLUGIN_DATA}/stan`), do którego model nie ma dostępu: każde wywołanie narzędzia,
które wskazuje ten katalog, odrzuca `PreToolUse` (patrz `reguly.dotyka_stanu`).

Układ katalogu:
  klucz                 klucz HMAC (0600), zakładany przy pierwszym użyciu
  sesje/<sesja>.json    stan sesji z podpisem HMAC-SHA256
  dziennik.jsonl        każda zmiana stanu (z pełną migawką i podpisem), odmowy, pętle Stop
  blokada               plik blokady fcntl dla zapisów współbieżnych

Odczyt: podpisany plik sesji; gdy go brak albo podpis się nie zgadza (ktoś go zmienił),
stan odtwarza się z ostatniej podpisanej migawki tej sesji w dzienniku. Skasowanie pliku
sesji nie zwalnia więc żadnej blokady.
"""

from __future__ import annotations

import contextlib
import copy
import datetime as _dt
import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets

#: Blokady przełączane parami poleceń (klucz stanu -> opis dla /tryb).
BLOKADY = {
    "bash": "Bash",
    "python": "Python",
    "masowe": "praca masowa",
    "reczne": "pisanie ręczne",
    "sleep": "uśpienie",
    "podagenci": "podagenci",
    "sudo": "sudo",
    "siec": "sieć",
    "zapis": "zapis plików",
    "pytania": "pytania",
}

#: Para poleceń włączających/zwalniających każdą blokadę (temat -> klucz stanu).
#: Nazwy wg jednej zasady: `/<temat>-blokuj` włącza, `/<temat>-odblokuj` zwalnia.
TEMATY = {
    "bash": "bash",
    "python": "python",
    "masowe": "masowe",
    "skrypty": "reczne",
    "sleep": "sleep",
    "podagenci": "podagenci",
    "sudo": "sudo",
    "siec": "siec",
    "zapis": "zapis",
    "pytania": "pytania",
}

LIMIT_DZIENNIKA = 5 * 1024 * 1024


def teraz() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def katalog_stanu() -> str:
    """Katalog stanu: zmienna testowa, dane wtyczki albo zapasowo ~/.claude/plugins/data."""
    jawny = os.environ.get("DANACO_PRACA_STAN")
    if jawny:
        return os.path.realpath(jawny)
    dane = os.environ.get("CLAUDE_PLUGIN_DATA")
    if dane:
        return os.path.realpath(os.path.join(dane, "stan"))
    konfiguracja = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.realpath(os.path.join(konfiguracja, "plugins", "data", "danaco-praca", "stan"))


def bezpieczna_sesja(sesja: str) -> str:
    sesja = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sesja or ""))[:120].strip(".")
    return sesja or "bez-sesji"


def pusty(sesja: str) -> dict:
    return {
        "wersja": 1,
        "sesja": sesja,
        "praca": {"wlaczona": False, "zlecenie": "", "od": None, "oddania": 0},
        "blokady": {k: False for k in BLOKADY},
        "zmieniono": None,
    }


def bezpieczny(sesja: str) -> dict:
    """Stan maksymalnie ograniczający — fallback, gdy stanu nie da się zweryfikować.

    Utrata albo uszkodzenie klucza lub podpisu nie może zdjąć blokad, więc przy braku
    zweryfikowanej i braku odczytywalnej migawki utrzymujemy tryb pracy i wszystkie
    blokady. Właściciel zwalnia je poleceniem /koniec-pracy i /odblokuj-… albo /tryb-wyczysc.
    """
    stan = pusty(sesja)
    stan["praca"]["wlaczona"] = True
    stan["praca"]["od"] = teraz()
    for klucz in BLOKADY:
        stan["blokady"][klucz] = True
    return stan


class Magazyn:
    """Dostęp do stanu jednej instalacji (katalog stanu)."""

    def __init__(self, katalog: str | None = None) -> None:
        self.katalog = katalog or katalog_stanu()
        self.sesje = os.path.join(self.katalog, "sesje")
        self.dziennik = os.path.join(self.katalog, "dziennik.jsonl")

    # --- infrastruktura -------------------------------------------------------------------

    def _przygotuj(self) -> None:
        os.makedirs(self.sesje, mode=0o700, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(self.katalog, 0o700)

    @staticmethod
    def _czytaj_klucz(sciezka: str) -> bytes | None:
        """Klucz z pliku, gdy ma pełną długość; None, gdy go brak albo jest obcięty."""
        try:
            with open(sciezka, "rb") as plik:
                klucz = plik.read()
        except FileNotFoundError:
            return None
        return klucz if len(klucz) >= 32 else None

    def _klucz(self) -> bytes:
        """Klucz HMAC stanu. Zakłada go atomowo przy pierwszym użyciu; obcięty naprawia.

        Brak albo obcięcie klucza nie może wysypać zapisu (`FileExistsError`): nowy klucz
        trafia najpierw do pliku tymczasowego, a potem atomowo na miejsce. Przy wyścigu z
        innym procesem używamy tego, co ostatecznie jest na dysku.
        """
        sciezka = os.path.join(self.katalog, "klucz")
        klucz = self._czytaj_klucz(sciezka)
        if klucz is not None:
            return klucz
        self._przygotuj()
        tymczasowy = f"{sciezka}.{secrets.token_hex(8)}.nowy"
        deskryptor = os.open(tymczasowy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(deskryptor, secrets.token_bytes(32))
        finally:
            os.close(deskryptor)
        try:
            os.replace(tymczasowy, sciezka)
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(tymczasowy)
        klucz = self._czytaj_klucz(sciezka)
        if klucz is None:
            raise OSError("nie udało się ustanowić klucza stanu danaco-praca")
        return klucz

    def _podpis(self, dane: dict) -> str:
        tresc = json.dumps(dane, sort_keys=True, ensure_ascii=False).encode()
        return hmac.new(self._klucz(), tresc, hashlib.sha256).hexdigest()

    def _zgodny(self, dane: dict, podpis: str) -> bool:
        return isinstance(podpis, str) and hmac.compare_digest(self._podpis(dane), podpis)

    @contextlib.contextmanager
    def blokada(self):
        self._przygotuj()
        with open(os.path.join(self.katalog, "blokada"), "a") as plik:
            fcntl.flock(plik, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(plik, fcntl.LOCK_UN)

    def _plik(self, sesja: str) -> str:
        return os.path.join(self.sesje, bezpieczna_sesja(sesja) + ".json")

    # --- odczyt ---------------------------------------------------------------------------

    def wczytaj(self, sesja: str) -> dict:
        sesja = bezpieczna_sesja(sesja)
        sciezka = self._plik(sesja)
        istnieje_plik = os.path.exists(sciezka)
        naruszenie = False
        if istnieje_plik:
            try:
                with open(sciezka, encoding="utf-8") as plik:
                    zapis = json.load(plik)
                if self._zgodny(zapis.get("stan"), zapis.get("podpis")):
                    return self._uzupelnij(zapis["stan"], sesja)
                naruszenie = True
            except (OSError, ValueError, AttributeError, TypeError):
                naruszenie = True
        elif not os.path.isdir(self.katalog):
            return pusty(sesja)

        zweryfikowana, dowolna = self._skan_dziennika(sesja)
        if zweryfikowana is not None:
            # Plik sesji skasowany lub zmieniony, ale klucz i dziennik całe: wraca podpisana migawka.
            stan = self._uzupelnij(zweryfikowana, sesja)
            with contextlib.suppress(OSError):
                self.dopisz({"zdarzenie": "naruszenie-stanu", "sesja": sesja,
                             "opis": "plik stanu zmieniony albo usunięty poza hookiem - odtworzono z dziennika"})
                self._zapisz_plik(stan)
            return stan
        if naruszenie or dowolna is not None:
            # Nie da się zweryfikować stanu (utracony/uszkodzony klucz lub podpis), a sesja miała
            # zapisany stan: fail-safe. Bierzemy ostatnią odczytywalną migawkę (niezależnie od
            # podpisu), a gdy jej brak - stan maksymalnie ograniczający. Blokady zostają. Sam wpis
            # w dzienniku bez migawki (np. odmowa) nie liczy się jako stan - sesja bez trybów
            # i bez pliku stanu wraca pusta.
            stan = self._uzupelnij(dowolna, sesja) if dowolna is not None else bezpieczny(sesja)
            with contextlib.suppress(OSError):
                self.dopisz({"zdarzenie": "stan-bezpieczny", "sesja": sesja,
                             "opis": "stanu nie dało się zweryfikować - utrzymano ograniczenia (fail-safe)"})
                self._zapisz_plik(stan)
            return stan
        return pusty(sesja)

    def _skan_dziennika(self, sesja: str) -> tuple[dict | None, dict | None]:
        """(ostatnia zweryfikowana migawka, ostatnia odczytywalna migawka) stanu sesji z dziennika."""
        zweryfikowana: dict | None = None
        dowolna: dict | None = None
        igla, igla_bez = f'"sesja": "{sesja}"', f'"sesja":"{sesja}"'
        for sciezka in (self.dziennik + ".1", self.dziennik):
            try:
                with open(sciezka, encoding="utf-8") as plik:
                    for wiersz in plik:
                        if igla not in wiersz and igla_bez not in wiersz:
                            continue
                        try:
                            wpis = json.loads(wiersz)
                        except ValueError:
                            continue
                        if wpis.get("sesja") != sesja:
                            continue
                        migawka = wpis.get("migawka")
                        if isinstance(migawka, dict):
                            dowolna = migawka
                            if self._zgodny(migawka, wpis.get("podpis_migawki")):
                                zweryfikowana = migawka
            except OSError:
                continue
        return zweryfikowana, dowolna

    @staticmethod
    def _uzupelnij(stan: dict, sesja: str) -> dict:
        wzor = pusty(sesja)
        stan = copy.deepcopy(stan) if isinstance(stan, dict) else wzor
        for klucz, wartosc in wzor.items():
            stan.setdefault(klucz, wartosc)
        for klucz, wartosc in wzor["praca"].items():
            stan["praca"].setdefault(klucz, wartosc)
        for klucz in BLOKADY:
            stan["blokady"].setdefault(klucz, False)
        return stan

    # --- zapis ----------------------------------------------------------------------------

    def _zapisz_plik(self, stan: dict) -> None:
        self._przygotuj()
        sciezka = self._plik(stan["sesja"])
        tymczasowy = f"{sciezka}.{secrets.token_hex(6)}.nowy"
        try:
            with open(tymczasowy, "w", encoding="utf-8") as plik:
                json.dump({"stan": stan, "podpis": self._podpis(stan)}, plik, ensure_ascii=False)
            os.chmod(tymczasowy, 0o600)
            os.replace(tymczasowy, sciezka)
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(tymczasowy)
            raise

    def zapisz(self, stan: dict, wpis: dict | None = None) -> None:
        """Zapis stanu; z `wpis` także wpis do dziennika z podpisaną migawką (zmiana trybu)."""
        stan["zmieniono"] = teraz()
        self._zapisz_plik(stan)
        if wpis is not None:
            wpis = dict(wpis)
            wpis["sesja"] = stan["sesja"]
            wpis["migawka"] = stan
            wpis["podpis_migawki"] = self._podpis(stan)
            self.dopisz(wpis)

    def dopisz(self, wpis: dict) -> None:
        self._przygotuj()
        wpis = {"czas": teraz(), **wpis}
        with contextlib.suppress(OSError):
            if os.path.getsize(self.dziennik) > LIMIT_DZIENNIKA:
                os.replace(self.dziennik, self.dziennik + ".1")
        deskryptor = os.open(self.dziennik, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(deskryptor, (json.dumps(wpis, ensure_ascii=False) + "\n").encode())
        finally:
            os.close(deskryptor)


def aktywne(stan: dict) -> list[str]:
    """Nazwy aktywnych ograniczeń (tryb pracy i blokady)."""
    wynik = ["praca"] if stan["praca"].get("wlaczona") else []
    return wynik + [k for k, v in stan["blokady"].items() if v]


def opis_stanu(stan: dict) -> str:
    """Tabela stanu dla właściciela (/tryb) i dla modelu po kompakcji."""
    praca = stan["praca"]
    wiersze = ["Tryb pracy danaco-praca (sesja " + stan["sesja"][:8] + "):", ""]
    if praca.get("wlaczona"):
        zlecenie = (praca.get("zlecenie") or "").strip().replace("\n", " ")
        wiersze.append(f"  praca ciągła   WŁĄCZONA od {praca.get('od')} (/koniec-pracy zwalnia)")
        if zlecenie:
            wiersze.append(f"                 zlecenie: {zlecenie[:300]}")
    else:
        wiersze.append("  praca ciągła   wyłączona (/praca włącza)")
    # Para poleceń dla każdej blokady z TEMATY (temat -> klucz); odwrotnie: klucz -> temat.
    temat_klucza = {klucz: temat for temat, klucz in TEMATY.items()}
    for klucz, nazwa in BLOKADY.items():
        temat = temat_klucza[klucz]
        wlacz, zwolnij = f"/blokuj-{temat}", f"/odblokuj-{temat}"
        if stan["blokady"].get(klucz):
            wiersze.append(f"  {nazwa:<14} ZABLOKOWANE ({zwolnij} zwalnia)")
        elif klucz == "sudo":
            wiersze.append(f"  {nazwa:<14} zgodnie z kontem ({wlacz} blokuje)")
        elif klucz == "sleep" and praca.get("wlaczona"):
            wiersze.append(f"  {nazwa:<14} zablokowane przez tryb pracy ({wlacz} blokuje ściślej)")
        else:
            wiersze.append(f"  {nazwa:<14} dozwolone ({wlacz} blokuje)")
    return "\n".join(wiersze)


def ogon_dziennika(magazyn, sesja: str, ile: int = 15) -> list[str]:
    """Ostatnie wpisy dziennika tej sesji (dla polecenia /tryb-dziennik) jako wiersze tekstu."""
    wynik: list[str] = []
    for sciezka in (magazyn.dziennik + ".1", magazyn.dziennik):
        try:
            with open(sciezka, encoding="utf-8") as plik:
                for wiersz in plik:
                    if f'"sesja": "{sesja}"' not in wiersz and f'"sesja":"{sesja}"' not in wiersz:
                        continue
                    try:
                        wpis = json.loads(wiersz)
                    except ValueError:
                        continue
                    if wpis.get("sesja") != sesja:
                        continue
                    czas = (wpis.get("czas") or "")[:19]
                    zdarzenie = wpis.get("zdarzenie", "?")
                    szczegol = (wpis.get("polecenia") and " ".join(wpis["polecenia"])) or wpis.get("narzedzie") or ""
                    powod = (wpis.get("powod") or "").split(".")[0][:80]
                    wynik.append(f"  {czas}  {zdarzenie:18} {szczegol} {powod}".rstrip())
        except OSError:
            continue
    return wynik[-ile:] if wynik else ["  (dziennik tej sesji jest pusty)"]
