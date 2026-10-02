#!/usr/bin/env python3
"""Straż dysku systemowego — hook PreToolUse dla narzędzi Bash i Write (Danaco).

Zasada właściciela (2026-10-02): na dysku systemowym `/` (30 GB) powstaje wyłącznie system —
jednostki i timery systemd, konfiguracja w `/etc`, skrypty w `/usr/local/sbin` i `/usr/local/bin`,
stan pakietów i dzienniki w limicie. Pobrania, klony, rozpakowania, budowy, instalacje
i wyniki prób idą na `/danaco`. Zasada: /etc/danaco/zasady/serwer.md, sekcja „Dysk systemowy (/)”.

Strażnik odrzuca polecenie, gdy jego cel zapisu leży na tym samym urządzeniu co `/`
i poza ścieżkami dozwolonymi. O położeniu rozstrzyga tablica montowań
(`/proc/self/mountinfo`), nie sama ścieżka: `/var/tmp`, `/root/.cache` czy `/var/crash`
są bind mountami z `/danaco` i zapis do nich przechodzi.

Wejście: zdarzenie PreToolUse jako JSON na stdin. Wyjście: JSON z decyzją ``deny`` i powodem
po polsku z podpowiedzią właściwego miejsca; brak wyjścia przepuszcza polecenie.
Strażnik działa tylko na serwerze, na którym `/danaco` jest osobnym systemem plików;
gdzie indziej (inne serwery, Windows) milczy. Każdy własny błąd przepuszcza polecenie —
to siatka bezpieczeństwa dla typowych dróg zapisu, nie szczelna granica.

``--test`` uruchamia wbudowane przypadki na sztucznej tablicy montowań.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from straz_sekretow import bez_heredoc, odcinki, wlasciwe_polecenie  # noqa: E402

#: Na dysku systemowym wolno zapisywać tylko tutaj (każdym sposobem).
DOZWOLONE = ("/etc", "/usr/local/sbin", "/usr/local/bin")
#: Drobny tekst (przekierowanie, tee, narzędzie Write) wolno też zapisać w konfiguracji roota.
DOZWOLONE_TEKST = DOZWOLONE + ("/root/.ssh", "/root/.config", "/root/.bashrc", "/root/.profile", "/var/spool/cron")

#: Zbiór montowań do testów; None = /proc/self/mountinfo.
MONTOWANIA: dict[str, list[tuple[str, str]] | None] = {"tablica": None}
KATALOG = {"cwd": ""}


# --- tablica montowań ---------------------------------------------------------------------------


def _wczytaj_montowania() -> list[tuple[str, str]]:
    """Lista (punkt montowania, urządzenie major:minor) z /proc/self/mountinfo."""
    if MONTOWANIA["tablica"] is not None:
        return MONTOWANIA["tablica"]
    wynik = []
    with open("/proc/self/mountinfo", encoding="utf-8", errors="replace") as plik:
        for wiersz in plik:
            pola = wiersz.split()
            if len(pola) < 5:
                continue
            punkt = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), pola[4])
            wynik.append((punkt, pola[2]))
    MONTOWANIA["tablica"] = wynik
    return wynik


def _urzadzenie(sciezka: str) -> str | None:
    """Urządzenie najgłębszego montowania obejmującego ścieżkę (ostatnie wygrywa przy przesłonięciu)."""
    najlepszy, dlugosc = None, -1
    for punkt, urzadzenie in _wczytaj_montowania():
        if sciezka == punkt or punkt == "/" or sciezka.startswith(punkt.rstrip("/") + "/"):
            if len(punkt) >= dlugosc:
                najlepszy, dlugosc = urzadzenie, len(punkt)
    return najlepszy


def straz_aktywna() -> bool:
    """Tylko tam, gdzie /danaco jest osobnym dyskiem — inaczej każdy zapis byłby „na /”."""
    korzen = _urzadzenie("/")
    danaco = [u for p, u in _wczytaj_montowania() if p == "/danaco"]
    return bool(korzen and danaco and danaco[-1] != korzen)


def na_dysku_systemowym(sciezka: str) -> bool:
    return _urzadzenie(sciezka) == _urzadzenie("/")


def pod(sciezka: str, przedrostki: tuple[str, ...]) -> bool:
    return any(sciezka == p or sciezka.startswith(p + "/") for p in przedrostki)


# --- ścieżki ------------------------------------------------------------------------------------


def rozwin(argument: str, cwd: str) -> str | None:
    """Ścieżka bezwzględna argumentu albo None, gdy nie da się jej ustalić bez wykonania."""
    arg = argument.strip().strip("'\"")
    if not arg or arg.startswith("-") or "://" in arg or re.match(r"^[\w.-]+@[\w.-]+:", arg):
        return None
    if arg == "~" or arg.startswith("~/"):
        arg = os.environ.get("HOME", "") + arg[1:]

    def _zmienna(m: re.Match) -> str:
        nazwa = m.group(1) or m.group(2)
        return os.environ.get(nazwa, "\x00")

    arg = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", _zmienna, arg)
    if "\x00" in arg or "$" in arg or "`" in arg or "*" in arg:
        return None
    if not arg.startswith("/"):
        if not cwd:
            return None
        arg = posixpath.join(cwd, arg)
    return posixpath.normpath(arg)


def podpowiedz(sciezka: str) -> str:
    konto = os.environ.get("USER") or os.environ.get("LOGNAME") or "<konto>"
    if pod(sciezka, ("/opt", "/usr")):
        return "programy i narzędzia — /danaco/programy/<dziedzina>/<program> (nakładka w /danaco/programy/bin, wpis w katalog/rejestr); narzędzia produktu — /danaco/uslugi/<usługa>"
    if pod(sciezka, ("/var/lib", "/var/www", "/srv", "/var/opt")):
        return "dane usług — /danaco/uslugi/<usługa> (w jednostce systemd: ReadWritePaths/StateDirectory wskazujące tam)"
    if pod(sciezka, ("/var/cache",)):
        return "pamięci podręczne — /danaco/cache (wspólne) albo /danaco/cache/konta/<konto>"
    if pod(sciezka, ("/var/log",)):
        return "dzienniki — journald (limit 1 GB) albo katalog usługi w /danaco/uslugi/<usługa>"
    return f"próby, pobrania i wyniki — katalog projektu na /danaco albo $TMPDIR (/danaco/cache/konta/{konto}/tmp, czyszczony po 2 dniach)"


def werdykt(cel: str, opis: str, tekst: bool = False) -> tuple[str, str] | None:
    dozwolone = DOZWOLONE_TEKST if tekst else DOZWOLONE
    if pod(cel, dozwolone) or not na_dysku_systemowym(cel):
        return None
    return (
        "deny",
        f"{opis} zapisałoby dane na dysku systemowym / (30 GB): {cel}. Na / wolno pisać tylko do "
        f"{', '.join(DOZWOLONE)} (w tym /etc/systemd/system); reszta idzie na /danaco. Właściwe miejsce: "
        f"{podpowiedz(cel)}. Zasada: /etc/danaco/zasady/serwer.md, sekcja „Dysk systemowy (/)”",
    )


# --- polecenia ----------------------------------------------------------------------------------

PIP = {"pip", "pip3"}
MENEDZERY_JS = {"npm", "pnpm", "yarn", "bun"}
INSTALACJE_JS = {"install", "i", "ci", "add"}
BUDOWY = {"make", "cmake", "ninja", "meson"}


def _opcja(slowa: list[str], nazwy: tuple[str, ...]) -> str | None:
    """Wartość opcji w postaci `-o X`, `--opcja X`, `--opcja=X` albo `-oX` (krótkie)."""
    for i, s in enumerate(slowa):
        for n in nazwy:
            if s == n and i + 1 < len(slowa):
                return slowa[i + 1]
            if n.startswith("--") and s.startswith(n + "="):
                return s[len(n) + 1 :]
            if not n.startswith("--") and len(n) == 2 and s.startswith(n) and len(s) > 2 and not s.startswith("--"):
                return s[2:]
    return None


def _pozycyjne(slowa: list[str], z_wartoscia: tuple[str, ...] = ()) -> list[str]:
    wynik, i = [], 0
    while i < len(slowa):
        s = slowa[i]
        if s in z_wartoscia:
            i += 2
            continue
        if not s.startswith("-"):
            wynik.append(s)
        i += 1
    return wynik


def cele_zapisu(slowa: list[str], cwd: str) -> list[tuple[str, str, bool]]:
    """Cele zapisu odcinka: (ścieżka, opis, czy to drobny tekst)."""
    cele: list[tuple[str, str, bool]] = []
    # Przekierowania wyjścia (nie: >&2, 2>&1, >/dev/null rozstrzyga tablica montowań).
    oczyszczone = []
    i = 0
    while i < len(slowa):
        s = slowa[i]
        m = re.match(r"^(\d*|&)>>?(.*)$", s)
        if m and not m.group(2).startswith("&"):
            cel = m.group(2) or (slowa[i + 1] if i + 1 < len(slowa) else "")
            if not m.group(2):
                i += 1
            sciezka = rozwin(cel, cwd)
            if sciezka:
                cele.append((sciezka, "przekierowanie wyjścia", True))
            i += 1
            continue
        oczyszczone.append(s)
        i += 1
    slowa = wlasciwe_polecenie(oczyszczone)
    if not slowa:
        return cele
    nazwa = slowa[0].rsplit("/", 1)[-1]
    reszta = slowa[1:]

    def dodaj(argument: str | None, opis: str, tekst: bool = False) -> None:
        if argument is None:
            return
        sciezka = rozwin(argument, cwd)
        if sciezka:
            cele.append((sciezka, opis, tekst))

    # python -m pip …
    if re.match(r"^python[0-9.]*$", nazwa) and len(reszta) >= 2 and reszta[0] == "-m" and reszta[1] in PIP:
        nazwa, reszta = "pip", reszta[2:]
    # uv pip …
    if nazwa == "uv" and reszta[:1] == ["pip"]:
        nazwa, reszta = "pip", reszta[1:]

    if nazwa == "tee":
        for arg in _pozycyjne(reszta):
            dodaj(arg, "tee", True)
    elif nazwa in ("cp", "mv", "rsync", "install", "scp"):
        cel = _opcja(reszta, ("-t", "--target-directory"))
        poz = _pozycyjne(reszta, ("-t", "--target-directory", "-m", "--mode", "-o", "--owner", "-g", "--group", "-e", "--exclude", "--include"))
        if cel is None and len(poz) >= 2:
            cel = poz[-1]
        dodaj(cel, nazwa)
    elif nazwa == "dd":
        for arg in reszta:
            if arg.startswith("of="):
                dodaj(arg[3:], "dd")
    elif nazwa == "curl":
        wyjscie = _opcja(reszta, ("-o", "--output"))
        katalog = _opcja(reszta, ("--output-dir",))
        if wyjscie:
            dodaj(wyjscie, "pobranie (curl)")
        elif katalog:
            dodaj(katalog, "pobranie (curl)")
        elif any(s in ("-O", "--remote-name", "--remote-name-all", "-J") or re.match(r"^-[a-zA-Z]*O[a-zA-Z]*$", s) for s in reszta):
            dodaj(".", "pobranie (curl -O)")
    elif nazwa == "wget":
        wyjscie = _opcja(reszta, ("-O", "--output-document"))
        katalog = _opcja(reszta, ("-P", "--directory-prefix"))
        dodaj(wyjscie or katalog or ".", "pobranie (wget)")
    elif nazwa == "git" and "clone" in reszta:
        poz = _pozycyjne(reszta[reszta.index("clone") + 1 :], ("-b", "--branch", "--depth", "-o", "--origin", "-c", "--config", "--reference", "--filter", "-j", "--jobs"))
        dodaj(poz[1] if len(poz) >= 2 else ".", "klon repozytorium (git clone)")
    elif nazwa in ("tar", "bsdtar"):
        tryb = (reszta[0] if reszta and not reszta[0].startswith("-") else "") + "".join(s[1:] for s in reszta if re.match(r"^-[A-Za-z]+$", s))
        if "x" in tryb or "--extract" in reszta or "--get" in reszta:
            dodaj(_opcja(reszta, ("-C", "--directory")) or ".", "rozpakowanie (tar)")
        elif "c" in tryb or "--create" in reszta:
            plik = _opcja(reszta, ("-f", "--file"))
            if plik is None and reszta and not reszta[0].startswith("-") and "f" in reszta[0]:
                poz = _pozycyjne(reszta[1:])
                plik = poz[0] if poz else None
            if plik and plik != "-":
                dodaj(plik, "archiwum (tar)")
    elif nazwa == "unzip":
        dodaj(_opcja(reszta, ("-d",)) or ".", "rozpakowanie (unzip)")
    elif nazwa in ("7z", "7za", "7zz") and reszta[:1] in (["x"], ["e"]):
        dodaj(_opcja(reszta, ("-o",)) or ".", "rozpakowanie (7z)")
    elif nazwa == "pip":
        polecenie = reszta[0] if reszta else ""
        if polecenie == "install":
            if "--break-system-packages" in reszta:
                cele.append(("/usr/local/lib/python3", "pip install --break-system-packages (systemowy Python)", False))
            for opcja in (("-t", "--target"), ("--prefix",), ("--root",)):
                dodaj(_opcja(reszta, opcja), "instalacja pakietów Pythona")
        elif polecenie in ("download", "wheel"):
            dodaj(_opcja(reszta, ("-d", "--dest", "-w", "--wheel-dir")) or ".", f"pip {polecenie}")
    elif nazwa in MENEDZERY_JS and reszta[:1] and reszta[0] in INSTALACJE_JS:
        if not any(s in ("-g", "--global", "--location=global") for s in reszta):
            dodaj(_opcja(reszta, ("--prefix", "--dir", "-C")) or ".", f"instalacja zależności ({nazwa} {reszta[0]})")
    elif nazwa == "cargo" and reszta[:1] and reszta[0] in ("build", "install", "new", "init", "test", "run"):
        dodaj(_opcja(reszta, ("--root",)) if reszta[0] == "install" else _opcja(reszta, ("--target-dir",)) or ".", f"cargo {reszta[0]}")
    elif nazwa in ("hf", "huggingface-cli") and "download" in reszta:
        dodaj(_opcja(reszta, ("--local-dir",)), "pobranie modelu (hf)")
        dodaj(_opcja(reszta, ("--cache-dir",)), "pobranie modelu (hf)")
    elif nazwa == "docker" and reszta[:1] == ["save"]:
        dodaj(_opcja(reszta, ("-o", "--output")), "docker save")
    elif nazwa == "go" and reszta[:1] == ["build"]:
        dodaj(_opcja(reszta, ("-o",)), "go build")
    elif nazwa in BUDOWY:
        dodaj(_opcja(reszta, ("-C", "-B")) or ".", f"budowa ({nazwa})")
    return cele


def ocen(polecenie: str) -> tuple[str, str] | None:
    if not straz_aktywna():
        return None
    cwd = KATALOG["cwd"]
    for slowa in odcinki(bez_heredoc(polecenie)):
        wlasciwe = wlasciwe_polecenie([s for s in slowa if not re.match(r"^(\d*|&)>", s)])
        if wlasciwe[:1] == ["cd"]:
            cel = wlasciwe[1] if len(wlasciwe) > 1 else os.environ.get("HOME", "")
            nowy = rozwin(cel, cwd)
            cwd = nowy or ""
            continue
        for sciezka, opis, tekst in cele_zapisu(slowa, cwd):
            wynik = werdykt(sciezka, opis, tekst)
            if wynik:
                return wynik
    return None


def ocen_zapis_pliku(sciezka: str) -> tuple[str, str] | None:
    if not straz_aktywna():
        return None
    cel = rozwin(sciezka, KATALOG["cwd"])
    return werdykt(cel, "Zapis pliku (Write)", True) if cel else None


# --- testy --------------------------------------------------------------------------------------

#: Układ jak na danaco-nexus: / = 9:3, /danaco = 9:5, /tmp = tmpfs, bind mounty z /danaco.
TABLICA_TESTOWA = [
    ("/", "9:3"), ("/danaco", "9:5"), ("/tmp", "0:40"), ("/var/tmp", "9:5"), ("/dev", "0:5"),
    ("/root/.cache", "9:5"), ("/root/tmp", "9:5"), ("/var/crash", "9:5"), ("/proc", "0:22"),
]

PRZYPADKI: list[tuple[str, str, str | None]] = [
    # (katalog roboczy, polecenie, oczekiwana decyzja)
    ("/danaco/projekty/x", "git clone https://github.com/a/b.git", None),
    ("/danaco/projekty/x", "sudo git clone https://github.com/a/b.git /opt/b", "deny"),
    ("/root", "sudo git clone https://github.com/a/b.git", "deny"),
    ("/danaco/x", "cd /root && wget https://x/model.bin", "deny"),
    ("/danaco/x", "cd /root/tmp && wget https://x/model.bin", None),
    ("/danaco/x", "wget -P /var/tmp https://x/a.iso", None),
    ("/danaco/x", "curl -L -o /root/a.tar.gz https://x/a", "deny"),
    ("/danaco/x", "curl -sS https://x/api | jq .", None),
    ("/danaco/x", "curl -fsSLO https://x/a.tgz", None),
    ("/opt", "curl -fsSLO https://x/a.tgz", "deny"),
    ("/danaco/x", "sudo tar xzf a.tgz -C /opt", "deny"),
    ("/danaco/x", "tar xzf a.tgz", None),
    ("/danaco/x", "tar czf /root/kopia.tgz /danaco/x", "deny"),
    ("/danaco/x", "unzip a.zip -d /srv/a", "deny"),
    ("/danaco/x", "sudo pip install --break-system-packages requests", "deny"),
    ("/danaco/x", "sudo pip install --target /usr/lib/python3/dist-packages x", "deny"),
    ("/danaco/x", "pip install --target /danaco/programy/x/lib x", None),
    ("/danaco/x", "sudo uv pip install --prefix /usr/local x", "deny"),
    ("/root", "sudo npm install", "deny"),
    ("/danaco/x", "sudo npm install --prefix /danaco/x/proba lodash", None),
    ("/danaco/x", "sudo npm install -g pakiet", None),
    ("/danaco/x", "sudo cargo install --root /usr/local/lib/cargo ripgrep", "deny"),
    ("/danaco/x", "cargo build --release", None),
    ("/danaco/x", "hf download org/model --local-dir /root/modele", "deny"),
    ("/danaco/x", "hf download org/model --local-dir /danaco/cache/huggingface/x", None),
    ("/danaco/x", "sudo cp -r wyniki /root/", "deny"),
    ("/danaco/x", "sudo cp skrypt.sh /usr/local/sbin/", None),
    ("/danaco/x", "sudo install -m 0755 skrypt.sh /usr/local/bin/skrypt", None),
    ("/danaco/x", "sudo cp jednostka.service /etc/systemd/system/", None),
    ("/danaco/x", "sudo rsync -a /danaco/x/ /var/lib/dane/", "deny"),
    ("/danaco/x", "sudo dd if=/dev/zero of=/var/obraz.img bs=1M count=100", "deny"),
    ("/danaco/x", "pg_dump nexus > /root/nexus.sql", "deny"),
    ("/danaco/x", "pg_dump nexus > wynik.sql 2>/dev/null", None),
    ("/danaco/x", "echo 'x' | sudo tee /etc/danaco/x.conf >/dev/null", None),
    ("/danaco/x", "echo 'ssh-ed25519 AAA' | sudo tee -a /root/.ssh/authorized_keys", None),
    ("/danaco/x", "find / -xdev -newer z > /tmp/lista.txt", None),
    ("/danaco/x", "find / -xdev -newer z > /var/log/lista.txt", "deny"),
    ("/danaco/x", "ls -la /root 2>&1 | head", None),
    ("/danaco/x", "sudo docker save -o /root/obraz.tar nexus", "deny"),
    ("/danaco/x", "cat <<'EOF' > /danaco/x/a.md\ncurl -o /root/a https://x\nEOF", None),
    ("/danaco/x", "make -C /usr/src/linux", "deny"),
    ("/danaco/x", "sudo mv /var/crash/a.crash /danaco/kosz/", None),
    ("/danaco/x", "sudo systemctl daemon-reload && sudo mount /root/.cache", None),
]


def test() -> int:
    MONTOWANIA["tablica"] = TABLICA_TESTOWA
    bledy = 0
    for cwd, polecenie, oczekiwane in PRZYPADKI:
        KATALOG["cwd"] = cwd
        wynik = ocen(polecenie)
        decyzja = wynik[0] if wynik else None
        if decyzja != oczekiwane:
            bledy += 1
            print(f"BŁĄD: oczekiwano {oczekiwane}, jest {decyzja}: [{cwd}] {polecenie[:100]!r}")
    for sciezka, oczekiwane in (("/root/raport.md", "deny"), ("/etc/danaco/x.json", None), ("/danaco/x/a.py", None), ("/opt/a/b.py", "deny")):
        KATALOG["cwd"] = "/danaco/x"
        wynik = ocen_zapis_pliku(sciezka)
        if (wynik[0] if wynik else None) != oczekiwane:
            bledy += 1
            print(f"BŁĄD (Write): oczekiwano {oczekiwane}: {sciezka}")
    # Bez osobnego /danaco straż milczy (inne serwery, Windows).
    MONTOWANIA["tablica"] = [("/", "9:3")]
    KATALOG["cwd"] = "/root"
    if ocen("git clone https://x/y.git") is not None:
        bledy += 1
        print("BŁĄD: straż działa bez osobnego /danaco")
    print(f"przypadki: {len(PRZYPADKI) + 5}, błędy: {bledy}")
    return 1 if bledy else 0


def main() -> int:
    if "--test" in sys.argv:
        return test()
    try:
        zdarzenie = json.load(sys.stdin)
        narzedzie = zdarzenie.get("tool_name")
        wejscie = zdarzenie.get("tool_input") or {}
        KATALOG["cwd"] = str(zdarzenie.get("cwd") or "")
        if narzedzie == "Bash":
            wynik = ocen(str(wejscie.get("command") or ""))
        elif narzedzie == "Write":
            wynik = ocen_zapis_pliku(str(wejscie.get("file_path") or ""))
        else:
            return 0
    except Exception:  # noqa: BLE001 — usterka strażnika przepuszcza polecenie
        return 0
    if wynik:
        decyzja, powod = wynik
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decyzja,
                    "permissionDecisionReason": f"Straż dysku systemowego Danaco: {powod}.",
                }
            },
            sys.stdout,
            ensure_ascii=False,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
