#!/usr/bin/python3
"""Serwer MCP (stdio) katalogu programów Danaco: /danaco/programy na danaco-nexus.

Źródła: rejestr/<dział>.json (wpisy narzędzi) i skille/<nazwa>/SKILL.md (pełne instrukcje).
Model dostaje krótką listę przy wyszukiwaniu, a pełny opis dopiero przez `opis`.

Tryby (DANACO_PROGRAMY_TRYB albo samoczynnie po nazwie hosta):
- lokalny (danaco-nexus): katalog z dysku, programy w PATH, `uruchom` liczy lokalnie;
- zdalny (pozostałe serwery): katalog kopiowany z nexusa (rsync), `uruchom` wysyła pliki na nexusa,
  liczy TAM jako to samo konto (klucz techniczny, Host danaco-nexus w ~/.ssh/config) i ściąga wyniki.
Tylko biblioteka standardowa - działa na każdym serwerze z /usr/bin/python3.
"""
import json
import os
import pathlib
import re
import secrets
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import unicodedata

NEXUS = os.environ.get("DANACO_NEXUS_HOST", "danaco-nexus")
TRYB = os.environ.get("DANACO_PROGRAMY_TRYB") or ("lokalny" if socket.gethostname() == NEXUS else "zdalny")
KATALOG_NEXUS = "/danaco/programy/katalog"
if TRYB == "lokalny":
    KATALOG = pathlib.Path(os.environ.get("DANACO_KATALOG", KATALOG_NEXUS))
else:
    KATALOG = pathlib.Path(os.environ.get("DANACO_KATALOG") or
                           pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")) / "danaco-programy" / "katalog")
REJESTR = KATALOG / "rejestr"
SKILLE = KATALOG / "skille"
WYMIANA = "/danaco/wymiana"  # na nexusie: /danaco/wymiana/<konto>/<serwer>/<zadanie>/{we,wy}
MAKS_SKILL = 60000  # znaków SKILL.md zwracanych przez `opis`
MAKS_WYJSCIE = 20000  # znaków stdout/stderr zwracanych przez `uruchom`
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30"]
WERSJA = "1.1.0"

INSTRUKCJE = (
    "Programy Danaco działają WYŁĄCZNIE na danaco-nexus (/danaco/programy, ponad 1000 poleceń: grafika, wideo, "
    "dźwięk, 3D, dokumenty, kod, dane, web, devops, bezpieczeństwo, testy, modele AI). Zanim cokolwiek "
    "zainstalujesz albo uznasz, że narzędzia brak, wyszukaj je tutaj (`szukaj`), a przed pierwszym użyciem "
    "przeczytaj `opis`. "
    + ("Na tym serwerze (nexus) polecenia uruchamiasz po nazwie w Bash albo przez `uruchom`."
       if TRYB == "lokalny" else
       "Ten serwer NIE ma programów: uruchamiaj je narzędziem `uruchom` - pliki wejściowe trafiają na nexusa "
       "do $WE, polecenie liczy się na nexusie w katalogu $WY, a wszystko z $WY wraca do `wyniki_do`.")
)


def synchronizuj_katalog(wymus: bool = False) -> str:
    """Tryb zdalny: kopia katalogu z nexusa (co najwyżej raz na 10 minut)."""
    if TRYB == "lokalny":
        return ""
    znacznik = KATALOG / ".zsynchronizowano"
    try:
        if not wymus and time.time() - znacznik.stat().st_mtime < 600:
            return ""
    except OSError:
        pass
    KATALOG.mkdir(parents=True, exist_ok=True)
    wynik = subprocess.run(
        ["rsync", "-a", "--delete", "-e", " ".join(SSH),
         "--include=/rejestr/***", "--include=/dzialy.json", "--include=/skille/", "--include=/skille/*/",
         "--include=/skille/*/SKILL.md", "--include=/skille/*/references/***", "--exclude=*",
         f"{NEXUS}:{KATALOG_NEXUS}/", f"{KATALOG}/"],
        capture_output=True, text=True, timeout=300)
    if wynik.returncode != 0:
        return f"(uwaga: nie udało się odświeżyć katalogu z {NEXUS}: {wynik.stderr.strip()[-300:]})"
    znacznik.touch()
    return ""


def zloz(tekst: str) -> str:
    """Małe litery bez polskich znaków - „dźwięk” pasuje do „dzwiek”."""
    tekst = tekst.lower().replace("ł", "l")
    return "".join(z for z in unicodedata.normalize("NFKD", tekst) if not unicodedata.combining(z))


def frontmatter(sciezka: pathlib.Path) -> dict:
    try:
        tekst = sciezka.read_text(errors="replace")
    except OSError:
        return {}
    if not tekst.startswith("---"):
        return {}
    koniec = tekst.find("\n---", 3)
    wynik = {}
    for wiersz in tekst[3:koniec].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", wiersz)
        if m:
            wynik[m.group(1)] = m.group(2).strip().strip('"')
    return wynik


class Indeks:
    def __init__(self):
        self.stempel = 0.0
        self.wpisy: dict[str, dict] = {}
        self.skille: dict[str, dict] = {}
        self.dzialy: dict[str, dict] = {}

    def znacznik(self) -> float:
        m = 0.0
        for d in (REJESTR, SKILLE):
            try:
                m = max(m, d.stat().st_mtime)
            except OSError:
                pass
        return m

    def odswiez(self):
        self.uwaga = synchronizuj_katalog()
        if self.wpisy and self.znacznik() <= self.stempel:
            return
        wpisy, dzialy = {}, {}
        for plik in sorted(REJESTR.glob("*.json")):
            try:
                dane = json.loads(plik.read_text())
            except (OSError, ValueError):
                continue
            for w in dane.get("narzedzia", []):
                nazwa = w.get("polecenie")
                if not nazwa:
                    continue
                dzial = w.get("dzial") or w.get("kategoria") or dane.get("dzial") or "inne"
                w = dict(w, dzial=dzial)
                wpisy[nazwa] = w
                d = dzialy.setdefault(dzial, {"opis": dane.get("opis_dzialu", ""), "liczba": 0})
                d["liczba"] += 1
        opisy_dzialow = KATALOG / "dzialy.json"
        if opisy_dzialow.exists():
            try:
                for nazwa, opis in json.loads(opisy_dzialow.read_text()).items():
                    dzialy.setdefault(nazwa, {"liczba": 0})["opis"] = opis
            except ValueError:
                pass
        skille = {}
        if SKILLE.is_dir():
            for d in sorted(SKILLE.iterdir()):
                f = d / "SKILL.md"
                if f.is_file():
                    fm = frontmatter(f)
                    skille[d.name] = {"nazwa": d.name, "opis": fm.get("description", ""), "plik": str(f)}
        self.wpisy, self.skille, self.dzialy = wpisy, skille, dzialy
        self.stempel = self.znacznik()

    def szukaj(self, zapytanie: str, dzial: str | None, limit: int) -> list[tuple[int, str, str, str, str]]:
        self.odswiez()
        slowa = [s for s in re.split(r"\s+", zloz(zapytanie)) if s]
        wyniki = []
        for nazwa, w in self.wpisy.items():
            if dzial and zloz(w["dzial"]) != zloz(dzial):
                continue
            n = zloz(nazwa)
            pola = {
                "kiedy": zloz(" ".join(w.get("kiedy_uzywac") or [])),
                "do": zloz(w.get("do_czego", "")),
                "dz": zloz(w["dzial"]),
                "sk": zloz(self.skille.get(nazwa, {}).get("opis", "")),
            }
            pkt = 0
            for s in slowa:
                if s == n:
                    pkt += 100
                elif n.startswith(s):
                    pkt += 40
                elif s in n:
                    pkt += 20
                pkt += 8 * (s in pola["kiedy"]) + 5 * (s in pola["do"]) + 5 * (s in pola["dz"]) + 3 * (s in pola["sk"])
            if slowa and all(s in n or any(s in v for v in pola.values()) for s in slowa):
                pkt += 15
            if pkt:
                wyniki.append((pkt, nazwa, w["dzial"], w.get("do_czego", ""), "polecenie"))
        if not dzial:
            for nazwa, s in self.skille.items():
                if nazwa in self.wpisy:
                    continue
                n, op = zloz(nazwa), zloz(s["opis"])
                pkt = sum(30 * (x in n) + 4 * (x in op) for x in slowa)
                if pkt:
                    wyniki.append((pkt, nazwa, "skill", s["opis"][:300], "skill"))
        wyniki.sort(key=lambda r: (-r[0], r[1]))
        return wyniki[:limit]


INDEKS = Indeks()


def narzedzie_szukaj(arg: dict) -> str:
    zapytanie = str(arg.get("zapytanie", "")).strip()
    if not zapytanie:
        return "Podaj `zapytanie` (np. „wideo av1”, „pdf ocr”, „sprawdz dostępność wcag”)."
    limit = max(1, min(int(arg.get("limit", 15)), 60))
    wyniki = INDEKS.szukaj(zapytanie, arg.get("dzial"), limit)
    if not wyniki:
        return f"Brak wyników dla „{zapytanie}”. Spróbuj synonimu albo `dzialy` i `lista`."
    wiersze = [f"Wyniki dla „{zapytanie}” ({len(wyniki)}); szczegóły: narzędzie `opis`."]
    for _, nazwa, dz, opis, rodzaj in wyniki:
        if rodzaj == "skill":
            wiersze.append(f"- {nazwa} [skill]: {opis}")
        else:
            znak = " (+skill)" if nazwa in INDEKS.skille else ""
            wiersze.append(f"- {nazwa}{znak} [{dz}]: {opis}")
    return "\n".join(wiersze)


def narzedzie_opis(arg: dict) -> str:
    INDEKS.odswiez()
    nazwa = str(arg.get("nazwa", "")).strip()
    w, s = INDEKS.wpisy.get(nazwa), INDEKS.skille.get(nazwa)
    if not w and not s:
        podobne = [r[1] for r in INDEKS.szukaj(nazwa, None, 8)]
        return f"Nie znam „{nazwa}”. Podobne: {', '.join(podobne) or 'brak'}."
    czesci = []
    if w:
        czesci.append(json.dumps({k: v for k, v in w.items()}, ensure_ascii=False, indent=2))
    if s and arg.get("pelny", True):
        tekst = pathlib.Path(s["plik"]).read_text(errors="replace")
        if len(tekst) > MAKS_SKILL:
            tekst = tekst[:MAKS_SKILL] + f"\n\n[… ucięto; całość: {s['plik']}]"
        czesci.append(f"--- SKILL: {s['plik']} ---\n{tekst}")
        ref = pathlib.Path(s["plik"]).parent / "references"
        if ref.is_dir():
            pliki = sorted(p.name for p in ref.iterdir())
            if pliki:
                czesci.append(f"Materiały dodatkowe ({ref}): " + ", ".join(pliki))
    return "\n\n".join(czesci)


def narzedzie_dzialy(arg: dict) -> str:
    INDEKS.odswiez()
    wiersze = [f"Działy katalogu ({len(INDEKS.wpisy)} poleceń, {len(INDEKS.skille)} skilli):"]
    for nazwa, d in sorted(INDEKS.dzialy.items(), key=lambda x: -x[1]["liczba"]):
        wiersze.append(f"- {nazwa} ({d['liczba']}): {d.get('opis', '')}".rstrip(": "))
    return "\n".join(wiersze)


def ucinaj(tekst: str) -> str:
    return tekst if len(tekst) <= MAKS_WYJSCIE else f"[… ucięto {len(tekst) - MAKS_WYJSCIE} znaków]\n" + tekst[-MAKS_WYJSCIE:]


def narzedzie_uruchom(arg: dict) -> str:
    polecenie = str(arg.get("polecenie", "")).strip()
    if not polecenie:
        return "Podaj `polecenie` (np. „ffmpeg9 -i \"$WE/film.mov\" -c:v libsvtav1 film.mkv”)."
    pliki = [os.path.abspath(os.path.expanduser(p)) for p in (arg.get("pliki") or [])]
    brak = [p for p in pliki if not os.path.exists(p)]
    if brak:
        return "Nie ma plików: " + ", ".join(brak)
    limit = max(10, min(int(arg.get("limit_s", 3600)), 86400))
    konto = os.environ.get("USER") or os.getlogin()
    zadanie = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
    katalog = f"{WYMIANA}/{konto}/{socket.gethostname()}/{zadanie}"
    wyniki_do = os.path.abspath(os.path.expanduser(arg.get("wyniki_do") or os.path.join(os.getcwd(), "wyniki-nexus", zadanie)))
    zdalnie = TRYB != "lokalny"
    start = time.time()

    def na_nexusie(skrypt: str, limit_s: int) -> subprocess.CompletedProcess:
        if zdalnie:
            return subprocess.run(SSH + [NEXUS, "bash -lc " + shlex.quote(skrypt)], capture_output=True, text=True,
                                  timeout=limit_s, errors="replace")
        return subprocess.run(["bash", "-lc", skrypt], capture_output=True, text=True, timeout=limit_s, errors="replace")

    przyg = na_nexusie(f"mkdir -p {shlex.quote(katalog)}/we {shlex.quote(katalog)}/wy", 60)
    if przyg.returncode != 0:
        return f"Nie mogę założyć katalogu zadania na {NEXUS}: {przyg.stderr.strip()[-500:]}"
    if pliki:
        if zdalnie:
            wys = subprocess.run(["rsync", "-a", "-e", " ".join(SSH)] + pliki + [f"{NEXUS}:{katalog}/we/"],
                                 capture_output=True, text=True, timeout=limit)
            if wys.returncode != 0:
                return f"Wysyłanie plików na {NEXUS} nie powiodło się: {wys.stderr.strip()[-800:]}"
        else:  # na nexusie wystarczą dowiązania - bez kopiowania dużych plików
            for p in pliki:
                os.symlink(p, os.path.join(katalog, "we", os.path.basename(p.rstrip("/"))))
    skrypt = (f"cd {shlex.quote(katalog)}/wy && export WE={shlex.quote(katalog)}/we WY={shlex.quote(katalog)}/wy "
              f"&& timeout {limit} bash -c {shlex.quote(polecenie)}")
    try:
        wynik = na_nexusie(skrypt, limit + 120)
        kod, out, err = wynik.returncode, wynik.stdout, wynik.stderr
    except subprocess.TimeoutExpired:
        kod, out, err = 124, "", f"przekroczono limit {limit} s"
    os.makedirs(wyniki_do, exist_ok=True)
    if zdalnie:
        pob = subprocess.run(["rsync", "-a", "-e", " ".join(SSH), f"{NEXUS}:{katalog}/wy/", wyniki_do + "/"],
                             capture_output=True, text=True, timeout=max(600, limit))
        blad_pobierania = pob.stderr.strip()[-500:] if pob.returncode != 0 else ""
    else:
        pob = subprocess.run(["cp", "-a", f"{katalog}/wy/.", wyniki_do + "/"], capture_output=True, text=True)
        blad_pobierania = pob.stderr.strip()[-500:] if pob.returncode != 0 else ""
    if not arg.get("zostaw") and not blad_pobierania:
        na_nexusie(f"/usr/bin/rm -rf -- {shlex.quote(katalog)}", 300)  # /usr/bin/rm: sprzątanie z pominięciem kosza
    pobrane = sorted(p for p in pathlib.Path(wyniki_do).rglob("*") if p.is_file())
    rozmiar = sum(p.stat().st_size for p in pobrane)
    czesci = [f"Zadanie {zadanie} na {NEXUS} ({'lokalnie' if not zdalnie else 'zdalnie'}): kod wyjścia {kod}, "
              f"czas {time.time() - start:.1f} s."]
    if out.strip():
        czesci.append("--- stdout ---\n" + ucinaj(out))
    if err.strip():
        czesci.append("--- stderr ---\n" + ucinaj(err))
    if blad_pobierania:
        czesci.append(f"UWAGA: pobieranie wyników nie powiodło się ({blad_pobierania}); katalog zadania zostaje na {NEXUS}: {katalog}")
    czesci.append(f"Wyniki: {len(pobrane)} plików, {rozmiar / 1e6:.1f} MB w {wyniki_do}" +
                  ("".join(f"\n- {p}" for p in pobrane[:50])) + ("\n- …" if len(pobrane) > 50 else ""))
    return "\n\n".join(czesci)


def narzedzie_lista(arg: dict) -> str:
    INDEKS.odswiez()
    dzial = zloz(str(arg.get("dzial", "")))
    wpisy = sorted((n, w) for n, w in INDEKS.wpisy.items() if zloz(w["dzial"]) == dzial)
    if not wpisy:
        return f"Nie ma działu „{arg.get('dzial')}”. Dostępne: {', '.join(sorted(INDEKS.dzialy))}."
    return "\n".join([f"Dział {arg.get('dzial')} ({len(wpisy)}):"] + [f"- {n}: {w.get('do_czego', '')}" for n, w in wpisy])


NARZEDZIA = {
    "szukaj": (narzedzie_szukaj, "Wyszukuje programy i skille serwera po temacie, zadaniu albo nazwie (np. „usuń tło ze zdjęcia”, „kodowanie av1”, „audyt wcag”). Zwraca krótką listę: polecenie, dział, do czego służy.", {
        "type": "object",
        "properties": {
            "zapytanie": {"type": "string", "description": "Słowa kluczowe po polsku lub angielsku"},
            "dzial": {"type": "string", "description": "Opcjonalnie: zawęź do działu (patrz `dzialy`)"},
            "limit": {"type": "integer", "description": "Liczba wyników (domyślnie 15, maks. 60)"},
        },
        "required": ["zapytanie"],
    }),
    "opis": (narzedzie_opis, "Pełny opis jednego programu albo skilla: ścieżka, do czego, kiedy używać, test działania oraz cała instrukcja SKILL.md z przykładami i pułapkami. Używaj przed pierwszym użyciem programu.", {
        "type": "object",
        "properties": {
            "nazwa": {"type": "string", "description": "Dokładna nazwa polecenia albo skilla"},
            "pelny": {"type": "boolean", "description": "Dołącz SKILL.md (domyślnie tak)"},
        },
        "required": ["nazwa"],
    }),
    "uruchom": (narzedzie_uruchom, "Uruchamia polecenie z programami Danaco NA danaco-nexus (tam jest cała moc obliczeniowa i wszystkie programy). Pliki z `pliki` trafiają do katalogu $WE, polecenie wykonuje się w katalogu $WY, a cała zawartość $WY wraca do `wyniki_do`. Przykład: polecenie „ffmpeg9 -i \"$WE/film.mov\" -c:v libsvtav1 film.mkv”, pliki [\"/sciezka/film.mov\"].", {
        "type": "object",
        "properties": {
            "polecenie": {"type": "string", "description": "Polecenie powłoki (bash) wykonywane na nexusie w $WY; wejście czytaj z $WE"},
            "pliki": {"type": "array", "items": {"type": "string"}, "description": "Lokalne pliki lub katalogi do wysłania do $WE"},
            "wyniki_do": {"type": "string", "description": "Lokalny katalog na wyniki (domyślnie ./wyniki-nexus/<zadanie>)"},
            "limit_s": {"type": "integer", "description": "Limit czasu w sekundach (domyślnie 3600, maks. 86400)"},
            "zostaw": {"type": "boolean", "description": "Nie usuwaj katalogu zadania na nexusie po pobraniu wyników"},
        },
        "required": ["polecenie"],
    }),
    "dzialy": (narzedzie_dzialy, "Lista działów katalogu programów z liczbą poleceń i opisem działu.", {"type": "object", "properties": {}}),
    "lista": (narzedzie_lista, "Wszystkie polecenia jednego działu z jednozdaniowym opisem.", {
        "type": "object",
        "properties": {"dzial": {"type": "string", "description": "Nazwa działu z `dzialy`"}},
        "required": ["dzial"],
    }),
}


def odpowiedz(id_, wynik=None, blad=None):
    kom = {"jsonrpc": "2.0", "id": id_}
    if blad:
        kom["error"] = blad
    else:
        kom["result"] = wynik
    sys.stdout.write(json.dumps(kom, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def obsluz(kom: dict):
    metoda, id_ = kom.get("method"), kom.get("id")
    if id_ is None:
        return  # powiadomienia (notifications/initialized, cancelled) nie mają odpowiedzi
    if metoda == "initialize":
        wersja = (kom.get("params") or {}).get("protocolVersion") or "2025-06-18"
        odpowiedz(id_, {
            "protocolVersion": wersja,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "danaco-programy", "version": WERSJA},
            "instructions": INSTRUKCJE,
        })
    elif metoda == "ping":
        odpowiedz(id_, {})
    elif metoda == "tools/list":
        odpowiedz(id_, {"tools": [
            {"name": n, "description": d, "inputSchema": s} for n, (_, d, s) in NARZEDZIA.items()
        ]})
    elif metoda == "tools/call":
        p = kom.get("params") or {}
        n = p.get("name")
        if n not in NARZEDZIA:
            odpowiedz(id_, blad={"code": -32602, "message": f"Nieznane narzędzie: {n}"})
            return
        try:
            tekst = NARZEDZIA[n][0](p.get("arguments") or {})
            odpowiedz(id_, {"content": [{"type": "text", "text": tekst}], "isError": False})
        except Exception as e:  # błąd narzędzia wraca do modelu, serwer działa dalej
            odpowiedz(id_, {"content": [{"type": "text", "text": f"Błąd: {e}"}], "isError": True})
    else:
        odpowiedz(id_, blad={"code": -32601, "message": f"Nieobsługiwana metoda: {metoda}"})


def main():
    for wiersz in sys.stdin:
        wiersz = wiersz.strip()
        if not wiersz:
            continue
        try:
            kom = json.loads(wiersz)
        except ValueError:
            odpowiedz(None, blad={"code": -32700, "message": "Niepoprawny JSON"})
            continue
        for k in (kom if isinstance(kom, list) else [kom]):
            obsluz(k)


if __name__ == "__main__":
    main()
