"""Reguły blokad danaco-praca: rozbiór poleceń powłoki i rozstrzygnięcia dla każdej blokady.

Każda funkcja `blokada_*` zwraca powód odmowy (tekst dla modelu) albo None. To filtr
heurystyczny: rozstrzyga po kształcie polecenia, po treści kodu podanego wprost i po
treści uruchamianego pliku skryptu, przed wykonaniem. Rozbiór słów i fragmentów
wykonywanych przez powłokę (`bash -c '…'`, `ssh host '…'`, `$(…)`) dzieli ze strażą
sekretów (`straz_sekretow.py`).
"""

from __future__ import annotations

import os
import re

from straz_sekretow import bez_heredoc, fragmenty, odcinki

# --- rozbiór poleceń ----------------------------------------------------------------------------

SLOWA_KLUCZOWE = {"do", "then", "else", "elif", "if", "while", "until", "!", "{", "}", "time", "coproc"}
NAGLOWKI = {"for", "select", "case", "function", "esac", "fi", "done", "in"}
PRZEDROSTKI = {
    "sudo", "doas", "pkexec", "run0", "nice", "ionice", "nohup", "time", "command", "exec", "stdbuf",
    "setsid", "timeout", "env", "chrt", "taskset", "unbuffer", "builtin",
}
SUDO = {"sudo", "doas", "pkexec", "run0"}
OPCJE_PRZEDROSTKOW = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "--user", "--group", "--chdir"},
    "doas": {"-u", "-C"},
    "pkexec": {"--user"},
    "run0": {"-u", "--user", "-D", "--chdir"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-t", "--class", "--classdata"},
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "stdbuf": {"-i", "-o", "-e"},
}
POWLOKI = {"bash", "sh", "dash", "zsh", "ksh", "fish", "busybox"}
INTERPRETERY = re.compile(r"^(python[0-9.]*|pypy[0-9.]*|node|nodejs|deno|bun|perl[0-9.]*|ruby|php[0-9.]*|lua[0-9.]*|Rscript|tclsh|osascript)$")


def nazwa(slowa: list[str]) -> str:
    return slowa[0].strip("'\"").rsplit("/", 1)[-1] if slowa else ""


def rdzen(slowa: list[str]) -> tuple[list[str], list[str]]:
    """Właściwe polecenie odcinka i lista przedrostków (sudo, timeout, env …), które je poprzedzają."""
    przedrostki: list[str] = []
    i = 0
    while i < len(slowa):
        slowo = slowa[i]
        n = slowo.strip("'\"").rsplit("/", 1)[-1]
        if slowo in SLOWA_KLUCZOWE or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", slowo):
            i += 1
            continue
        if n in PRZEDROSTKI:
            przedrostki.append(n)
            i += 1
            z_wartoscia = OPCJE_PRZEDROSTKOW.get(n, set())
            while i < len(slowa):
                s = slowa[i]
                if s in z_wartoscia and i + 1 < len(slowa):
                    i += 2
                elif s.startswith("-") and s != "-":
                    i += 1
                elif n in ("timeout", "nice", "chrt", "taskset") and re.match(r"^[\d.x]+[smhd]?$", s):
                    i += 1
                elif n == "env" and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", s):
                    i += 1
                else:
                    break
            continue
        break
    return slowa[i:], przedrostki


def _normalizuj(tekst: str) -> str:
    """Usuwa zdublowania deskryptorów (2>&1, >&2), które rozbiór czytałby jako operator `&`."""
    tekst = re.sub(r"\d*>&(\d+|-)", " ", tekst)
    tekst = re.sub(r"&>>", " >>", tekst)
    return re.sub(r"&>", " >", tekst)


def podpolecenia(r: list[str]) -> list[list[str]]:
    """Polecenia uruchamiane przez find -exec, xargs i parallel."""
    n = nazwa(r)
    wynik: list[list[str]] = []
    if n == "find":
        i = 0
        while i < len(r):
            if r[i] in ("-exec", "-execdir", "-ok", "-okdir"):
                j = i + 1
                while j < len(r) and r[j].strip("'\"") not in (";", "\\;", "+"):
                    j += 1
                wynik.append(r[i + 1 : j])
                i = j
            i += 1
    elif n in ("xargs", "parallel"):
        z_wartoscia = {"-I", "-n", "-P", "-L", "-l", "-d", "-E", "-s", "-a", "-j", "--jobs", "--arg-file",
                       "--delimiter", "--max-args", "--max-procs", "--replace"}
        i = 1
        while i < len(r) and r[i].startswith("-"):
            i += 2 if r[i] in z_wartoscia else 1
        reszta = r[i:]
        if ":::" in reszta:
            reszta = reszta[: reszta.index(":::")]
        if reszta:
            wynik.append(reszta)
    return [p for p in wynik if p]


def polecenia(tekst: str) -> list[tuple[list[str], list[str], list[str]]]:
    """(rdzeń, przedrostki, surowe słowa) każdego polecenia, łącznie z wykonywanymi w cudzysłowie po
    bash -c / ssh, w $(…) oraz przez find -exec i xargs."""
    wynik = []
    for fragment in fragmenty(_normalizuj(bez_heredoc(tekst))):
        for slowa in odcinki(fragment):
            if slowa[0] in NAGLOWKI or slowa[0].endswith("()"):
                continue
            r, p = rdzen(slowa)
            if not r and not p:
                continue
            wynik.append((r, p, slowa))
            for pod in podpolecenia(r):
                rp, pp = rdzen(pod)
                wynik.append((rp, pp, pod))
    return wynik


def przekierowania(slowa: list[str]) -> list[str]:
    """Cele przekierowań wyjścia (>, >>, >|) z pominięciem duplikacji deskryptorów."""
    cele = []
    for i, slowo in enumerate(slowa):
        m = re.match(r"^(\d*)(>>?|>\|)(.*)$", slowo)
        if not m:
            continue
        cel = m.group(3) or (slowa[i + 1] if i + 1 < len(slowa) else "")
        cel = cel.strip("'\"")
        if cel and not cel.startswith("&"):
            cele.append(cel)
    return cele


def argumenty_pozycyjne(slowa: list[str], z_wartoscia: set[str] = frozenset()) -> list[str]:
    wynik, i = [], 0
    while i < len(slowa):
        s = slowa[i]
        if s in z_wartoscia:
            i += 2
            continue
        if s == "--":
            wynik.extend(slowa[i + 1 :])
            break
        if not s.startswith("-") or s == "-":
            if not re.match(r"^\d*(>>?|<)", s):
                wynik.append(s)
        i += 1
    return wynik


def w_tle(tekst: str, wejscie: dict) -> bool:
    if wejscie.get("run_in_background") is True:
        return True
    return bool(re.search(r"(?<![&>|])&\s*($|\n|\))", _normalizuj(bez_heredoc(tekst))))


PETLA = re.compile(r"(?<![\w-])(for|while|until|select)\b(.*?)(?<![\w-])do\b(.*?)(?<![\w-])done\b", re.S)


def petle(tekst: str) -> list[tuple[str, str, str]]:
    """(rodzaj, warunek, ciało) pętli powłoki w tekście polecenia (z wnętrzem bash -c '…')."""
    wynik = []
    for fragment in fragmenty(_normalizuj(bez_heredoc(tekst))):
        for m in PETLA.finditer(fragment):
            wynik.append((m.group(1), m.group(2), m.group(3)))
    return wynik


# --- kod podany wprost i pliki skryptów ------------------------------------------------------------

def heredoki(tekst: str) -> list[tuple[str, str]]:
    """(wiersz z <<, treść) dokumentów „here”."""
    wynik = []
    wiersze = tekst.split("\n")
    i = 0
    while i < len(wiersze):
        m = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", wiersze[i])
        if m:
            znacznik, glowa, tresc = m.group(1), wiersze[i], []
            i += 1
            while i < len(wiersze) and wiersze[i].strip() != znacznik:
                tresc.append(wiersze[i])
                i += 1
            wynik.append((glowa, "\n".join(tresc)))
        i += 1
    return wynik


def kod_wbudowany(tekst: str) -> tuple[list[str], list[str]]:
    """Kod podany interpreterowi wprost (-c, -e, heredoc) oraz kod powłoki z heredoca do powłoki."""
    kody: list[str] = []
    powloka: list[str] = []
    for r, _, _ in polecenia(tekst):
        n = nazwa(r)
        if INTERPRETERY.match(n):
            for i, s in enumerate(r[1:], 1):
                perl_e = n.startswith(("perl", "ruby")) and re.match(r"^-[a-zA-Z]*[eE]$", s)
                if (s in ("-c", "-e", "-E", "-r", "--eval", "-p", "--print") or perl_e) and i + 1 < len(r):
                    kody.append(r[i + 1].strip("'\""))
    for glowa, tresc in heredoki(tekst):
        glowa_czysta = glowa.split("<<")[0]
        slowa = [nazwa([s]) for s in glowa_czysta.replace("|", " ").split()]
        if any(INTERPRETERY.match(s) for s in slowa):
            kody.append(tresc)
        elif any(s in POWLOKI or s in ("ssh", "eval") for s in slowa):
            powloka.append(tresc)
    return kody, powloka


def pliki_skryptow(tekst: str, cwd: str) -> list[tuple[str, str, bool]]:
    """(ścieżka, treść, czy powłoka) plików uruchamianych jako program (do 512 kB)."""
    wynik = []
    for r, _, _ in polecenia(tekst):
        if not r:
            continue
        n = nazwa(r)
        kandydat = None
        powloka = n in POWLOKI
        if INTERPRETERY.match(n) or powloka:
            argumenty = r[1:]
            if any(a in ("-c", "-e", "-m", "-E", "--eval") for a in argumenty):
                continue
            pozycyjne = [a for a in argumenty if not a.startswith("-")]
            kandydat = pozycyjne[0] if pozycyjne else None
        elif "/" in r[0]:
            kandydat = r[0]
        if not kandydat:
            continue
        sciezka = os.path.expanduser(kandydat.strip("'\""))
        if not os.path.isabs(sciezka) and cwd:
            sciezka = os.path.join(cwd, sciezka)
        try:
            if not os.path.isfile(sciezka) or os.path.getsize(sciezka) > 512 * 1024:
                continue
            with open(sciezka, encoding="utf-8", errors="replace") as plik:
                tresc = plik.read()
        except OSError:
            continue
        pierwszy = tresc.split("\n", 1)[0]
        if not powloka and not INTERPRETERY.match(n):
            powloka = pierwszy.startswith("#!") and bool(re.search(r"\b(ba|da|z|k)?sh\b", pierwszy))
            if not pierwszy.startswith("#!") and kandydat.endswith(".sh"):
                powloka = True
        wynik.append((sciezka, tresc, powloka))
    return wynik


ZAPIS_KODU = re.compile(
    r"""open\s*\([^)]*?,\s*(mode\s*=\s*)?['"][^'"]*[wax+]|\.write_(text|bytes)\s*\(|\.writelines\s*\(|"""
    r"""writeFileSync|writeFile\s*\(|appendFile|createWriteStream|os\.(replace|rename|remove|unlink)\s*\(|"""
    r"""shutil\.(move|copy\w*|rmtree)\s*\(|fs\.(rm|rmSync|unlink\w*|rename\w*)\s*\(|json\.dump\s*\(|"""
    r"""\.to_(csv|json|parquet|excel)\s*\(|\bprint\s*\([^)]*\bfile\s*=|File\.(write|open\([^)]*['"]w)|"""
    r"""IO\.write|file_put_contents|fopen\s*\([^)]*['"][wa]|\bsed\s+-i|\bperl\s+-p?i|\$\^I"""
)
PETLA_KODU = re.compile(
    r"\bfor\b[^\n]*\bin\b|\bfor\s*\(|\bwhile\b|\.forEach\s*\(|\bos\.walk\b|\.r?glob\s*\(|\bglob\.i?glob\s*\(|"
    r"\bmap\s*\(|\.each\b|\bforeach\b|readdirSync|readdir\s*\(|\$\^I|-p?i\b"
)
SEN_KODU = re.compile(r"\b(time\.sleep|asyncio\.sleep|sleep|usleep|setTimeout|setInterval|Thread\.sleep)\s*\(")


# --- zapis w powłoce -------------------------------------------------------------------------------

WYMIANA = {"rm", "mv", "cp", "tee", "truncate", "dd", "shred", "unlink", "install", "ln", "patch", "rsync"}


def edycja_w_miejscu(r: list[str]) -> tuple[str, list[str], bool] | None:
    """Edytor w miejscu: (nazwa, pliki, rekurencyjnie) albo None."""
    n = nazwa(r)
    argumenty = [a for a in r[1:] if not re.match(r"^\d*(>>?|<)", a)]

    def klaster(a: str, litera: str) -> bool:
        return a.startswith("-") and not a.startswith("--") and litera in re.match(r"^-([A-Za-z0-9]*)", a).group(1)

    rekurencyjnie = any(a in ("-r", "-R", "--recursive") for a in argumenty)
    if n in ("sed", "gsed"):
        if not any(a == "--in-place" or a.startswith("--in-place=") or klaster(a, "i") for a in argumenty):
            return None
        skrypt_w_opcji = any(a in ("-e", "-f", "--expression", "--file") or a.startswith("--expression=") for a in argumenty)
        pozycyjne = argumenty_pozycyjne(argumenty, {"-e", "-f", "--expression", "--file", "-l", "--line-length"})
        return n, (pozycyjne if skrypt_w_opcji else pozycyjne[1:]), rekurencyjnie
    if n.startswith("perl") or n == "ruby":
        if not any(klaster(a, "i") for a in argumenty):
            return None
        ma_e = any(re.match(r"^-[a-zA-Z0-9]*[eE]$", a) for a in argumenty)
        pozycyjne, i = [], 0
        while i < len(argumenty):
            a = argumenty[i]
            if re.match(r"^-[a-zA-Z0-9]*[eE]$", a):
                i += 2
                continue
            if not a.startswith("-"):
                pozycyjne.append(a)
            i += 1
        return n, (pozycyjne if ma_e else pozycyjne[1:]), rekurencyjnie
    if n in ("awk", "gawk") and ("inplace" in argumenty or "--include=inplace" in argumenty):
        pozycyjne = [a for a in argumenty_pozycyjne(argumenty, {"-i", "-v", "-f", "-F"}) if a != "inplace"]
        return n, pozycyjne[1:], rekurencyjnie
    if n == "sd":
        pozycyjne = argumenty_pozycyjne(argumenty)
        return (n, pozycyjne[2:], rekurencyjnie) if len(pozycyjne) > 2 else None
    if n == "rpl":
        pozycyjne = argumenty_pozycyjne(argumenty)
        return n, pozycyjne[2:], rekurencyjnie
    if n in ("dos2unix", "unix2dos", "mac2unix"):
        return n, argumenty_pozycyjne(argumenty), rekurencyjnie
    if n in ("rename", "prename", "perl-rename", "file-rename", "mmv"):
        return n, argumenty_pozycyjne(argumenty)[1:], rekurencyjnie
    if n in ("ed", "ex") or (n in ("vim", "vi", "nvim") and any(a in ("-es", "-e", "-s", "-Es") for a in argumenty)):
        return n, argumenty_pozycyjne(argumenty), rekurencyjnie
    return None


def wiele_plikow(pliki: list[str], limit: int) -> bool:
    if len(pliki) > limit:
        return True
    return any(re.search(r"[*?\[]|\{\}|\$\(|`|\$[A-Za-z_{]", p) for p in pliki)


def zapisuje(r: list[str], slowa: list[str]) -> bool:
    n = nazwa(r)
    if edycja_w_miejscu(r) or n in WYMIANA:
        return True
    if n == "find" and "-delete" in r:
        return True
    return any(not c.startswith("/dev/") for c in przekierowania(slowa))


def tekst_zapisuje(tekst: str) -> bool:
    return any(zapisuje(r, s) for r, _, s in polecenia(tekst))


# --- blokady ---------------------------------------------------------------------------------------

def polecenie_powloki(narzedzie: str, wejscie: dict) -> str | None:
    """Tekst polecenia narzędzia wykonującego powłokę (Bash, PowerShell, Monitor, MCP z polem command)."""
    if narzedzie in ("Bash", "PowerShell", "Monitor"):
        return str(wejscie.get("command") or "")
    if narzedzie.startswith("mcp__"):
        for pole in ("command", "cmd", "script"):
            if isinstance(wejscie.get(pole), str):
                return wejscie[pole]
    return None


def blokada_sudo(tekst: str) -> str | None:
    for r, p, _ in polecenia(tekst):
        n = nazwa(r)
        if SUDO & set(p) or n in SUDO:
            return "`sudo` (i doas, pkexec, run0) jest zablokowane poleceniem właściciela /sudo-blokuj. Wykonaj polecenie bez podnoszenia uprawnień albo pomiń ten krok"
        if n == "su" and (any(a in ("-c", "--command", "-", "-l", "--login", "root") for a in r[1:]) or len(r) == 1):
            return "`su` jest zablokowane poleceniem właściciela /sudo-blokuj"
    return None


PYTHON = re.compile(r"^(python[0-9.]*(-config)?|pypy[0-9.]*|ipython[0-9]*|pip[0-9.]*|pipx|uvx|pytest|py\.test|tox|nox|jupyter(-\w+)?|pdm|hatch|pipenv|poetry|rye)$")
UV_PYTHON = {"run", "pip", "tool", "sync", "add", "x", "venv", "python", "init"}


def blokada_python(tekst: str, cwd: str) -> str | None:
    powod = "Python jest zablokowany poleceniem właściciela /python-blokuj ({}). Wykonaj zadanie bez Pythona: innym narzędziem, poleceniem powłoki albo ręcznie"
    for r, _, slowa in polecenia(tekst):
        n = nazwa(r)
        if not r:
            continue
        if PYTHON.match(n):
            return powod.format(f"`{n}`")
        if n == "uv" and len(r) > 1 and r[1] in UV_PYTHON:
            return powod.format(f"`uv {r[1]}`")
        if n in ("conda", "mamba", "micromamba") and len(r) > 1 and r[1] in ("run", "install"):
            return powod.format(f"`{n} {r[1]}`")
        if n.endswith((".py", ".pyw")):
            return powod.format(f"skrypt `{n}`")
        if "/" in r[0]:
            sciezka = os.path.expanduser(r[0].strip("'\""))
            if not os.path.isabs(sciezka) and cwd:
                sciezka = os.path.join(cwd, sciezka)
            try:
                with open(sciezka, encoding="utf-8", errors="replace") as plik:
                    pierwszy = plik.readline(200)
                if pierwszy.startswith("#!") and "python" in pierwszy:
                    return powod.format(f"skrypt Pythona `{r[0]}`")
            except OSError:
                pass
        cele = przekierowania(slowa) + (argumenty_pozycyjne(r[1:]) if n == "tee" else [])
        for cel in cele:
            if cel.endswith((".py", ".pyw")):
                return powod.format(f"tworzenie pliku `{cel}`")
    for glowa, _ in heredoki(tekst):
        if re.search(r"\bpython[0-9.]*\b", glowa.split("<<")[0]):
            return powod.format("kod Pythona w dokumencie here")
    return None


def blokada_python_plik(narzedzie: str, wejscie: dict) -> str | None:
    """Tworzenie plików Pythona narzędziami plikowymi."""
    powod = "Python jest zablokowany poleceniem właściciela /python-blokuj: nie twórz plików Pythona do uruchomienia ({})"
    if narzedzie == "NotebookEdit":
        return powod.format("notatnik Jupyter")
    if narzedzie == "Write":
        sciezka = str(wejscie.get("file_path") or "")
        tresc = str(wejscie.get("content") or "")
        if sciezka.endswith((".py", ".pyw")):
            return powod.format(sciezka)
        pierwszy = tresc.split("\n", 1)[0]
        if pierwszy.startswith("#!") and "python" in pierwszy:
            return powod.format(f"{sciezka} z interpreterem Pythona")
    return None


def _monitoring(tekst: str, wejscie: dict) -> bool:
    """Pętla w tle zapisująca do dziennika (>>) — monitoring, nie czekanie modelu."""
    if not w_tle(tekst, wejscie):
        return False
    return any(">>" in cialo or re.search(r"done\s*>>", tekst) for _, _, cialo in petle(tekst))


ODPYTANIE = re.compile(
    r"\b(pgrep|pidof|kill\s+-0|test\s+!?\s*-[efsdpS]|\[\[?\s*!?\s*-[efsdpS]|curl|wget|nc|ps|ss|lsof|"
    r"systemctl\s+is-\w+|docker\s+(inspect|ps)|kubectl\s+get|ls|grep\s+-q|true|:)\b|^\s*:\s*$|!\s"
)


def blokada_czekania(tekst: str, wejscie: dict, scisle: bool = True) -> str | None:
    """sleep, wait, pętle oczekiwania i odpytywanie.

    `scisle` (/sleep-blokuj): także w tle, poza monitoringiem z dziennikiem. Bez niego (sam tryb
    /praca): tylko na pierwszym planie — polecenie w tle to proces albo monitoring, a agent
    pracuje dalej.
    """
    powod = ("Czekanie jest zablokowane ({}): pracuj dalej zamiast czekać — sięgnij po kolejną część "
             "zadania i wróć do wyniku później. Procesy, agenci i monitoring w tle są dozwolone")
    tlo = w_tle(tekst, wejscie)
    if tlo and not scisle:
        return None
    monitoring = _monitoring(tekst, wejscie)
    for r, _, _ in polecenia(tekst):
        n = nazwa(r)
        if n in ("sleep", "usleep") and not monitoring:
            return powod.format(f"`{' '.join(r[:2])}`")
        if n == "wait" or n in ("inotifywait", "inotifywatch") or (n == "watch" and not monitoring):
            return powod.format(f"`{n}`")
        if n == "tail" and not tlo and any(
            a in ("-f", "-F", "--follow", "--retry") or a.startswith(("--follow", "--pid"))
            or re.match(r"^-[a-zA-Z0-9]*[fF][a-zA-Z0-9]*$", a) for a in r[1:]
        ):
            return powod.format("`tail -f`")
        if n in ("docker", "podman", "kubectl") and "wait" in r[1:3]:
            return powod.format(f"`{n} wait`")
        if n == "gh" and ("watch" in r[1:3] or "--watch" in r):
            return powod.format("`gh … watch`")
        if n == "systemd-run" and "--wait" in r:
            return powod.format("`systemd-run --wait`")
    for rodzaj, warunek, cialo in petle(tekst):
        if monitoring:
            break
        if rodzaj == "until":
            return powod.format("pętla `until`")
        if rodzaj == "while" and not re.search(r"\bread\b", warunek) and ODPYTANIE.search(warunek):
            return powod.format("pętla `while` odpytująca stan")
    kody, powloki = kod_wbudowany(tekst)
    for kod in kody:
        if SEN_KODU.search(kod) and not monitoring:
            return powod.format("uśpienie w kodzie podanym wprost")
    for kod in powloki:
        wynik = blokada_czekania(kod, {}, scisle)
        if wynik:
            return wynik
    return None


#: Narzędzia, których funkcją jest odłożenie pracy albo czekanie.
NARZEDZIA_CZEKANIA = {"ScheduleWakeup", "Monitor", "CronCreate", "Sleep", "Wait"}
ODBIOR_WYNIKU = {"TaskOutput", "BashOutput", "AgentOutputTool", "BashOutputTool"}


def blokada_czekania_narzedzie(narzedzie: str, wejscie: dict, scisle: bool = True) -> str | None:
    """Narzędzia odkładające pracę. `Monitor` odrzuca tylko /sleep-blokuj; w /praca monitoring wolno stawiać."""
    powod = "Czekanie jest zablokowane ({}): pracuj dalej zamiast czekać na wybudzenie albo wynik"
    if narzedzie == "Monitor" and not scisle:
        return None
    if narzedzie in NARZEDZIA_CZEKANIA:
        return powod.format(f"narzędzie {narzedzie}")
    if narzedzie in ODBIOR_WYNIKU and wejscie.get("block") is not False:
        return powod.format(f"{narzedzie} czeka na zakończenie zadania; odbierz wynik bez czekania: block: false")
    if re.search(r"(?i)(^|[_-])(wait|sleep|await)([_-]|$)", narzedzie.split("__")[-1]):
        return powod.format(f"narzędzie {narzedzie}")
    return None


def blokada_masowa(tekst: str, cwd: str, limit: int, glebokosc: int = 0) -> str | None:
    powod = ("Praca masowa jest zablokowana poleceniem właściciela /masowe-blokuj ({}). Edytuj pliki "
             "pojedynczo narzędziami Edit/Write, plik po pliku, sprawdzając każdą zmianę")
    for r, _, _ in polecenia(tekst):
        n = nazwa(r)
        edycja = edycja_w_miejscu(r)
        if edycja and (edycja[2] or wiele_plikow(edycja[1], limit)):
            return powod.format(f"`{edycja[0]}` w miejscu na wielu plikach")
        if n == "find":
            if "-delete" in r:
                return powod.format("`find -delete`")
            for pod in podpolecenia(r):
                if zapisuje(pod, pod) or nazwa(pod) in POWLOKI:
                    return powod.format(f"`find -exec {nazwa(pod)}`")
        if n in ("xargs", "parallel"):
            for pod in podpolecenia(r):
                if zapisuje(pod, pod) or nazwa(pod) in POWLOKI:
                    return powod.format(f"`{n} {nazwa(pod)}`")
        if n in ("patch",) or (n == "git" and len(r) > 1 and r[1] in ("apply", "am")):
            return powod.format(f"`{' '.join(r[:2])}` nanosi zmiany hurtem")
        if n == "git" and len(r) > 1:
            if r[1] == "reset" and "--hard" in r:
                return powod.format("`git reset --hard`")
            if r[1] == "clean" and any(a.startswith("-") and "f" in a for a in r[2:]):
                return powod.format("`git clean -f`")
            if r[1] in ("checkout", "restore") and any(a in (".", "*", ":/") or re.search(r"[*?]", a) for a in r[2:]):
                return powod.format(f"`git {r[1]}` na wielu plikach")
        if n in ("rsync",) and any(a.startswith("--delete") for a in r):
            return powod.format("`rsync --delete`")
    for _, _, cialo in petle(tekst):
        if tekst_zapisuje(cialo):
            return powod.format("pętla po plikach z zapisem")
    kody, powloki = kod_wbudowany(tekst)
    for kod in kody:
        if PETLA_KODU.search(kod) and ZAPIS_KODU.search(kod):
            return powod.format("kod podany wprost zapisuje pliki w pętli")
    for kod in powloki:
        wynik = blokada_masowa(kod, cwd, limit, glebokosc + 1)
        if wynik:
            return wynik
    if glebokosc < 2:
        for sciezka, tresc, powloka in pliki_skryptow(tekst, cwd):
            if powloka:
                wynik = blokada_masowa(tresc, cwd, limit, glebokosc + 1)
                if wynik:
                    return powod.format(f"skrypt {sciezka}: " + wynik.split("(", 1)[-1].split(")")[0])
            elif PETLA_KODU.search(tresc) and ZAPIS_KODU.search(tresc):
                return powod.format(f"skrypt {sciezka} zapisuje pliki w pętli")
    if any(nazwa(r) in ("sqlite3", "psql", "mysql", "mariadb", "duckdb", "clickhouse-client", "mongosh") for r, _, _ in polecenia(tekst)):
        for zdanie in re.split(r";", tekst):
            if re.search(r"\bUPDATE\b[\s\S]*\bSET\b", zdanie, re.I) and (
                not re.search(r"\bWHERE\b", zdanie, re.I) or re.search(r"\bREPLACE\s*\(", zdanie, re.I)
            ):
                return powod.format("hurtowy UPDATE w bazie danych")
            if re.search(r"\bDELETE\s+FROM\b", zdanie, re.I) and not re.search(r"\bWHERE\b", zdanie, re.I):
                return powod.format("DELETE bez WHERE w bazie danych")
    return None


def dozwolony_cel_reczny(cel: str) -> bool:
    """Wyjście programów do dzienników i plików tymczasowych nie jest pisaniem treści."""
    tmpdir = os.environ.get("TMPDIR", "/tmp").rstrip("/")
    return (
        cel.startswith(("/dev/", "/tmp/", "/proc/self/", "$TMPDIR", "${TMPDIR}", tmpdir + "/"))
        or cel.endswith((".log", ".out", ".err"))
    )


def blokada_reczna(tekst: str, cwd: str, glebokosc: int = 0) -> str | None:
    powod = ("Pisanie ręczne: właściciel poleceniem /skrypty-blokuj dopuścił zmiany plików wyłącznie "
             "narzędziami Edit i Write ({}). Wpisz treść sam tymi narzędziami, bez generowania jej skryptem")
    for r, _, slowa in polecenia(tekst):
        n = nazwa(r)
        edycja = edycja_w_miejscu(r)
        if edycja:
            return powod.format(f"`{edycja[0]}` w miejscu")
        if n in ("truncate", "patch", "sponge") or (n == "dd" and any(a.startswith("of=") for a in r)):
            return powod.format(f"`{n}`")
        if n == "git" and len(r) > 1 and r[1] in ("apply", "am"):
            return powod.format(f"`git {r[1]}`")
        cele = przekierowania(slowa) + (argumenty_pozycyjne(r[1:], {"-p"}) if n == "tee" else [])
        for cel in cele:
            if not dozwolony_cel_reczny(cel):
                return powod.format(f"zapis do `{cel}` przekierowaniem albo tee")
    kody, powloki = kod_wbudowany(tekst)
    for kod in kody:
        if ZAPIS_KODU.search(kod):
            return powod.format("kod podany wprost zapisuje pliki")
    for kod in powloki:
        wynik = blokada_reczna(kod, cwd, glebokosc + 1)
        if wynik:
            return wynik
    if glebokosc < 2:
        for sciezka, tresc, powloka in pliki_skryptow(tekst, cwd):
            if powloka:
                if blokada_reczna(tresc, cwd, glebokosc + 1):
                    return powod.format(f"skrypt {sciezka} zapisuje pliki")
            elif ZAPIS_KODU.search(tresc):
                return powod.format(f"skrypt {sciezka} zapisuje pliki")
    return None


NARZEDZIA_PODAGENTOW = {"Agent", "Task", "Workflow", "TeamCreate", "Team", "SpawnAgent", "SpawnTeam"}
CLAUDE = {"claude", "claude-uslugi", "claude-code"}


def blokada_podagentow_narzedzie(narzedzie: str) -> str | None:
    if narzedzie in NARZEDZIA_PODAGENTOW:
        return (f"Podagenci są zablokowani poleceniem właściciela /podagenci-blokuj (narzędzie {narzedzie}). "
                "Wykonaj tę pracę sam, krok po kroku")
    return None


def blokada_podagentow_powloka(tekst: str) -> str | None:
    for r, _, _ in polecenia(tekst):
        n = nazwa(r)
        if n in CLAUDE and any(a in ("-p", "--print", "--agent", "--agents") or a.startswith("--print") for a in r[1:]):
            return "Podagenci są zablokowani poleceniem właściciela /podagenci-blokuj (`claude -p` w powłoce). Wykonaj tę pracę sam"
        if n == "codex" and "exec" in r[1:]:
            return "Podagenci są zablokowani poleceniem właściciela /podagenci-blokuj (`codex exec`). Wykonaj tę pracę sam"
    return None


def wznowienie_sesji(tekst: str) -> str | None:
    """`claude --resume` z wnętrza sesji: droga do podrzucenia polecenia właściciela tej sesji."""
    for r, _, _ in polecenia(tekst):
        if nazwa(r) in CLAUDE and any(
            a in ("-r", "--resume", "-c", "--continue", "--session-id", "--fork-session", "--from-pr")
            or a.startswith(("--resume=", "--session-id=")) for a in r[1:]
        ):
            return ("Wznowienie sesji Claude z wnętrza sesji jest zablokowane, dopóki działa tryb lub blokada "
                    "danaco-praca: przełączać je może wyłącznie właściciel")
    return None


# --- blokada sieci (/siec-blokuj) -----------------------------------------------------------------

#: Klienty, których jedyną funkcją jest połączenie sieciowe.
SIEC_KLIENCI = {"curl", "wget", "nc", "ncat", "netcat", "telnet", "ssh", "sftp", "ftp", "lftp",
                "aria2c", "httpie", "http", "xh", "yt-dlp", "youtube-dl", "svn"}
#: Zdalne z natury (cel to host): scp/sftp.
SIEC_ZDALNE = {"scp", "sftp"}
#: Podpolecenia menedżerów pakietów, które pobierają z sieci.
SIEC_PAKIETY = {
    "pip": {"install", "download", "wheel"}, "pip3": {"install", "download", "wheel"},
    "uv": {"add", "sync"}, "pipx": {"install", "upgrade", "run"},
    "npm": {"install", "i", "ci", "add", "update", "up"}, "pnpm": {"install", "i", "add", "update"},
    "yarn": {"install", "add", "up"}, "bun": {"install", "i", "add", "update"},
    "cargo": {"install", "add", "fetch", "update"}, "go": {"get", "install"},
    "gem": {"install", "update", "fetch"}, "apt": {"install", "update", "upgrade", "download"},
    "apt-get": {"install", "update", "upgrade", "download"}, "dnf": {"install", "update", "upgrade"},
    "yum": {"install", "update", "upgrade"}, "brew": {"install", "upgrade", "update", "fetch"},
    "conda": {"install", "update", "create"}, "mamba": {"install", "update", "create"},
    "hf": {"download", "upload"}, "huggingface-cli": {"download", "upload"},
}
SIEC_GIT = {"clone", "fetch", "pull", "push", "remote", "ls-remote"}
ZDALNY_CEL = re.compile(r"[\w.-]+@[\w.-]+:|^[\w.-]+:")


def blokada_sieci(tekst: str) -> str | None:
    powod = ("Sieć jest zablokowana poleceniem właściciela /siec-blokuj ({}). Pracuj na danych "
             "lokalnych; pobieranie i połączenia zdalne wykonasz po /siec-odblokuj")
    for r, _, _ in polecenia(tekst):
        n = nazwa(r)
        if not r:
            continue
        if n in SIEC_KLIENCI:
            return powod.format(f"`{n}`")
        if n in SIEC_ZDALNE:
            return powod.format(f"`{n}`")
        if n == "rsync" and any(ZDALNY_CEL.search(a) for a in r[1:]):
            return powod.format("zdalny `rsync`")
        if n == "git" and len(r) > 1 and r[1] in SIEC_GIT:
            return powod.format(f"`git {r[1]}`")
        if n in SIEC_PAKIETY and any(a in SIEC_PAKIETY[n] for a in r[1:3]):
            return powod.format(f"pobieranie `{n}`")
        if n == "go" and r[1:3] == ["mod", "download"]:
            return powod.format("`go mod download`")
    return None


# --- blokada zapisu / tryb tylko-odczyt (/zapis-blokuj) -------------------------------------------

#: Polecenia tworzące albo niszczące pliki (poza przenoszeniem treści, które liczy WYMIANA).
ZAPIS_TWORZ = {"mkdir", "mkfifo", "mknod", "touch", "ln", "install"}
#: Podpolecenia gita zmieniające repozytorium albo drzewo robocze.
GIT_ZMIANA = {"commit", "add", "rm", "mv", "reset", "restore", "checkout", "merge", "rebase",
              "cherry-pick", "revert", "stash", "apply", "am", "clean", "init", "gc", "tag", "pull"}


def blokada_zapisu(tekst: str) -> str | None:
    powod = ("Tryb tylko-odczyt jest włączony poleceniem właściciela /zapis-blokuj ({}). Oglądaj "
             "i analizuj; pliki zmienisz po /zapis-odblokuj narzędziami Edit i Write")
    for r, _, slowa in polecenia(tekst):
        n = nazwa(r)
        if not r:
            continue
        if edycja_w_miejscu(r):
            return powod.format(f"`{n}` w miejscu")
        if n in ("rm", "shred", "unlink", "truncate", "dd", "patch"):
            return powod.format(f"`{n}`")
        if n in ZAPIS_TWORZ:
            return powod.format(f"`{n}`")
        if n in ("mv", "cp", "tee") or (n == "rsync"):
            cele = argumenty_pozycyjne(r[1:], {"-t", "--target-directory"}) if n != "tee" else argumenty_pozycyjne(r[1:], {"-p"})
            if n in ("mv", "cp", "rsync"):
                cele = cele[1:] if len(cele) > 1 else cele
            if any(not dozwolony_cel_reczny(c) for c in cele) or not cele:
                return powod.format(f"`{n}`")
        if n == "git" and len(r) > 1 and r[1] in GIT_ZMIANA:
            return powod.format(f"`git {r[1]}`")
        for cel in przekierowania(slowa):
            if not dozwolony_cel_reczny(cel):
                return powod.format(f"zapis do `{cel}`")
    kody, powloki = kod_wbudowany(tekst)
    for kod in kody:
        if ZAPIS_KODU.search(kod):
            return powod.format("kod podany wprost zapisuje pliki")
    for kod in powloki:
        wynik = blokada_zapisu(kod)
        if wynik:
            return wynik
    return None
