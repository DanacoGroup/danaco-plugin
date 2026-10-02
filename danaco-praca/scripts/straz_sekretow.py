#!/usr/bin/env python3
"""Straż sekretów i operacji nieodwracalnych — hook PreToolUse (Danaco).

Zasady właściciela: sekrety leżą wyłącznie w plikach 600 i nigdy nie trafiają na ekran ani
do rozmowy; operacje, których nie da się cofnąć (wymuszony push, przepisanie historii,
skasowanie bazy albo repozytorium), wymagają potwierdzenia człowieka.

Wejście: zdarzenie PreToolUse jako JSON na stdin. Wyjście: JSON z decyzją ``deny`` albo
``ask`` i powodem po polsku; brak wyjścia przepuszcza polecenie. Strażnik działa
zachowawczo: każdy własny błąd przepuszcza polecenie, bo usterka strażnika nie może
zatrzymać pracy. Rozpoznaje typowe drogi wypisania sekretu, nie wszystkie — to siatka
bezpieczeństwa, nie szczelna granica.

``--test`` uruchamia wbudowane przypadki (polecenia z codziennej pracy muszą przejść).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# Polecenia, które wypisują zawartość pliku podanego w argumencie.
PODGLADY = {
    "cat", "tac", "less", "more", "head", "tail", "bat", "batcat", "nl", "strings",
    "xxd", "hexdump", "od", "base64", "zcat", "zless", "column", "jq", "yq",
}
# Wyszukiwarki: wypisują pasujące wiersze, więc sekret wycieka, gdy wzorzec go dotyczy.
SZUKAJACE = {"grep", "egrep", "fgrep", "rg", "ag"}
# Przełączniki wyszukiwarek, przy których nie wypisuje się treści wierszy.
BEZ_TRESCI = {"-c", "--count", "-l", "--files-with-matches", "-L", "--files-without-match", "-q", "--quiet", "--silent"}
# Przedrostki, po których dopiero stoi właściwe polecenie.
PRZEDROSTKI = {"sudo", "doas", "nice", "ionice", "nohup", "time", "command", "exec", "stdbuf", "setsid", "timeout"}

NAZWA_SEKRETU_SUROWA = re.compile(r"(TOKEN|SECRET|SEKRET|KLUCZ|HASLO|HASŁO|PASSWORD|PASSWD|PASS\b|API_?KEY|PRIVATE)", re.I)
# Zmienna ze ścieżką do sekretu (NEXUS_PLATNOSCI_STRIPE_KLUCZ_PLIK, NEXUS_CHMURA_TOKEN_FILE) sama sekretem nie jest.
ZMIENNA_ZE_SCIEZKA = re.compile(r"(TOKEN|SECRETS?|SEKRETY?|KLUCZE?|HASLO|PASSWORD)_(FILE|PLIK|DIR|PATH|SCIEZKA|KATALOG)", re.I)


class _NazwaSekretu:
    """Dopasowanie nazwy sekretu z pominięciem nazw zmiennych wskazujących ścieżkę."""

    @staticmethod
    def search(tekst: str):  # noqa: ANN205
        return NAZWA_SEKRETU_SUROWA.search(ZMIENNA_ZE_SCIEZKA.sub("", tekst))


NAZWA_SEKRETU = _NazwaSekretu()
WZORY_JAWNE = re.compile(r"\.(example|szablon|template|wzor|wzór|sample|dist)$", re.I)
PLIKI_KODU = re.compile(r"\.(py|ts|tsx|js|mjs|cjs|md|sh|go|rs|java|kt|html|css|lock)$", re.I)
# Słowo-sekret jako osobny człon nazwy: „huggingface-token”, „db-haslo”, „sekrety.log”, ale nie
# „tokeny-pl.log” (tokeny modelu) ani „tokens.json” (tokeny projektowe).
NAZWA_PLIKU_SEKRETU = re.compile(
    r"(^|[-_.])(klucz|haslo|hasło|sekret|sekrety|secret|secrets|token|credential|credentials|password|passwd)([-_.]|$)", re.I
)
#: Katalog roboczy zdarzenia — do rozstrzygania ścieżek względnych.
KATALOG = {"cwd": ""}
SSH_JAWNE = {"config", "known_hosts", "known_hosts.old", "authorized_keys"}


def sciezka_sekretu(argument: str) -> bool:
    """Czy argument wskazuje plik z sekretem (klucz, hasło, plik środowiska, poświadczenia)."""
    arg = argument.strip().strip("'\"")
    if not arg or arg.startswith("-"):
        return False
    if WZORY_JAWNE.search(arg):
        return False
    nazwa = arg.rstrip("/").rsplit("/", 1)[-1]
    if arg.startswith("/etc/danaco/") or arg in ("/etc/shadow", "/etc/gshadow") or arg.startswith("/etc/ssl/private/"):
        return True
    if arg in ("/etc/passwd", "/etc/group") or arg.startswith("/etc/pam.d/"):
        return False
    if re.search(r"(^|/)\.ssh/", arg):
        return not (nazwa in SSH_JAWNE or nazwa.endswith(".pub"))
    if re.search(r"(^|/)(\.env|[^/]+\.env)$", arg):
        return not sledzony_w_gicie(arg)
    if re.search(r"\.(pem|key|p12|pfx|jks|keystore)$", arg, re.I):
        return True
    if re.search(r"(^|/)\.claude/settings(\.local)?\.json$|(^|/)\.claude\.json$", arg):
        return True
    if re.search(r"(^|/)(\.netrc|\.pgpass|\.git-credentials|\.npmrc)$|/\.config/gh/hosts\.yml$|/\.docker/config\.json$", arg):
        return True
    if re.search(r"^/proc/[^/]+/environ$", arg):
        return True
    if not PLIKI_KODU.search(nazwa) and NAZWA_PLIKU_SEKRETU.search(nazwa):
        return not sledzony_w_gicie(arg)
    return False


def sledzony_w_gicie(arg: str) -> bool:
    """Plik śledzony przez gita to konfiguracja repozytorium, nie sekret (np. deploy/…/produkcja.env)."""
    sciezka = os.path.expanduser(arg)
    if not os.path.isabs(sciezka) and KATALOG["cwd"]:
        sciezka = os.path.join(KATALOG["cwd"], sciezka)
    if not os.path.isfile(sciezka):
        return False
    try:
        wynik = subprocess.run(
            ["git", "-C", os.path.dirname(sciezka) or ".", "ls-files", "--error-unmatch", os.path.basename(sciezka)],
            capture_output=True, timeout=3,
        )
    except Exception:  # noqa: BLE001
        return False
    return wynik.returncode == 0


def bez_heredoc(tekst: str) -> str:
    """Usuwa treść dokumentów „here” (to, co idzie do pliku, nie jest wykonywane)."""
    wynik: list[str] = []
    wiersze = tekst.split("\n")
    i = 0
    while i < len(wiersze):
        wiersz = wiersze[i]
        wynik.append(wiersz)
        znaczniki = re.findall(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", wiersz)
        for znacznik in znaczniki:
            i += 1
            while i < len(wiersze) and wiersze[i].strip() != znacznik:
                i += 1
        i += 1
    return "\n".join(wynik)


#: Polecenia, które wykonują swój argument jako kod powłoki (ssh host '…', bash -c "…").
WYKONAWCY = re.compile(r"(^|[\s/])(ssh|bash|sh|zsh|dash|ksh|su|runuser|eval|watch|parallel)(\s|$)")


def fragmenty(tekst: str, glebokosc: int = 0) -> list[str]:
    """Tekst polecenia i fragmenty, które powłoka naprawdę wykona.

    Zawartość cudzysłowu liczy się tylko po wykonawcy (ssh, bash -c, eval …): tekst podany
    do echo, git commit -m czy do pliku to dane, nie polecenie. Podstawienia $(…) i `…`
    wykonują się zawsze, także wewnątrz cudzysłowu.
    """
    wynik = [tekst]
    if glebokosc >= 3:
        return wynik
    for dopasowanie in re.finditer(r"\$\(([^()]*)\)|`([^`]*)`", tekst):
        wnetrze = dopasowanie.group(1) if dopasowanie.group(1) is not None else dopasowanie.group(2)
        if wnetrze and wnetrze.strip():
            wynik.extend(fragmenty(wnetrze, glebokosc + 1))
    for dopasowanie in re.finditer(r"'([^']*)'|\"((?:[^\"\\]|\\.)*)\"", tekst):
        przed = tekst[: dopasowanie.start()]
        poczatek = max(przed.rfind(znak) for znak in ("|", ";", "&", "\n", "(")) + 1
        if not WYKONAWCY.search(przed[poczatek:]):
            continue
        # W apostrofach powłoka niczego nie rozwija; w cudzysłowie \" znaczy zwykły cudzysłów.
        if dopasowanie.group(1) is not None:
            wnetrze = dopasowanie.group(1)
        else:
            wnetrze = dopasowanie.group(2).replace('\\"', '"')
        if wnetrze and len(wnetrze.strip()) > 1:
            wynik.extend(fragmenty(wnetrze, glebokosc + 1))
    return wynik


def odcinki(tekst: str) -> list[list[str]]:
    """Pojedyncze polecenia (po operatorach powłoki) jako listy słów."""
    # Spacje i operatory wewnątrz cudzysłowów nie dzielą polecenia (tr ";" "\n", grep "a|b").
    ukryj = str.maketrans({" ": "\x00", "|": "\x01", ";": "\x02", "&": "\x03", "(": "\x04", ")": "\x05", "\n": "\x06", "`": "\x07", "$": "\x08"})
    odkryj = str.maketrans({"\x00": " ", "\x01": "|", "\x02": ";", "\x03": "&", "\x04": "(", "\x05": ")", "\x06": "\n", "\x07": "`", "\x08": "$"})
    bez_cudzyslowow = re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", lambda m: m.group(0).translate(ukryj), tekst)
    wynik = []
    for czesc in re.split(r"\|\||&&|[|;&\n()`]|\$\(", bez_cudzyslowow):
        slowa = [s.translate(odkryj) for s in czesc.split()]
        if slowa:
            wynik.append(slowa)
    return wynik


def wlasciwe_polecenie(slowa: list[str]) -> list[str]:
    """Pomija przypisania zmiennych i przedrostki (sudo, timeout, env X=1 …)."""
    i = 0
    while i < len(slowa):
        slowo = slowa[i]
        nazwa = slowo.rsplit("/", 1)[-1]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", slowo):
            i += 1
        elif nazwa in PRZEDROSTKI:
            i += 1
            # opcje przedrostka i ich wartości (sudo -u konto, timeout 30)
            while i < len(slowa) and (slowa[i].startswith("-") or re.match(r"^\d+[smhd]?$", slowa[i])):
                if slowa[i] in ("-u", "-g", "-k", "-s", "--signal", "-n") and i + 1 < len(slowa) and not slowa[i + 1].startswith("-"):
                    i += 1
                i += 1
        elif nazwa == "env" and i + 1 < len(slowa) and (
            re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", slowa[i + 1]) or slowa[i + 1] in ("-i", "-u")
        ):
            i += 1
        else:
            break
    return slowa[i:]


OPCJE_Z_WARTOSCIA = {"-A", "-B", "-C", "-m", "--max-count", "--include", "--exclude", "--exclude-dir", "-g", "--glob", "-t", "--type", "-T", "--type-not", "--color", "--colour", "-d", "-D"}


def rozbierz_wyszukiwanie(argumenty: list[str]) -> tuple[list[str], list[str], set[str]]:
    """grep/rg: wzorce (pierwszy argument albo -e), pliki (reszta) i flagi (-c, -v, --count …)."""
    wzorce: list[str] = []
    pozycyjne: list[str] = []
    flagi: set[str] = set()
    z_opcji = False
    i = 0
    while i < len(argumenty):
        a = argumenty[i]
        if a == "--":
            pozycyjne.extend(argumenty[i + 1 :])
            break
        if a in ("-e", "--regexp") and i + 1 < len(argumenty):
            wzorce.append(argumenty[i + 1])
            z_opcji = True
            i += 2
            continue
        if a in ("-f", "--file"):
            z_opcji = True  # wzorce z pliku — nieznane, więc traktowane jak dowolne
            i += 2
            continue
        if a.startswith("--regexp="):
            wzorce.append(a.split("=", 1)[1])
            z_opcji = True
        elif a in OPCJE_Z_WARTOSCIA:
            i += 2
            continue
        elif a.startswith("--"):
            flagi.add(a.split("=", 1)[0])
        elif a.startswith("-") and len(a) > 1:
            flagi.update(a[1:])
        else:
            pozycyjne.append(a)
        i += 1
    if not z_opcji and pozycyjne:
        wzorce.append(pozycyjne.pop(0))
    return wzorce, pozycyjne, flagi


def ocen_odcinek(slowa: list[str]) -> tuple[str, str] | None:
    polecenie = wlasciwe_polecenie(slowa)
    if not polecenie:
        return None
    nazwa = polecenie[0].rsplit("/", 1)[-1]
    argumenty = [a.strip("'\"") for a in polecenie[1:]]

    # --- sekrety w plikach ---
    if nazwa in ("jq", "yq"):
        filtry = [a for a in argumenty if not a.startswith("-") and not sciezka_sekretu(a)]
        filtr = filtry[0] if filtry else "."
        if filtr.strip() not in (".", "") and not NAZWA_SEKRETU.search(filtr) and "env" not in filtr:
            return None  # wybiórczy filtr (np. .mcpServers) — nie wypisuje sekretów
    do_kosza = any(a in (">/dev/null", "1>/dev/null", "&>/dev/null") for a in argumenty) or any(
        a in (">", "1>", "&>") and nastepny == "/dev/null" for a, nastepny in zip(argumenty, argumenty[1:])
    )
    if (nazwa in PODGLADY or nazwa == "sed") and do_kosza:
        return None  # wynik idzie do /dev/null — sprawdzenie odczytu, nie podgląd
    if nazwa in PODGLADY or (nazwa == "sed" and not any(a.startswith("-i") or a == "--in-place" for a in argumenty)):
        if nazwa == "cat" and any(a.startswith(">") for a in argumenty):
            return None  # cat > plik: zapis, nie podgląd
        for arg in argumenty:
            if sciezka_sekretu(arg):
                return ("deny", f"„{nazwa} {arg}” wypisałoby sekret na ekran. Sekrety zostają w plikach 600; "
                                "sprawdź obecność klucza bez wartości (grep -c, grep -o '^NAZWA=')")
    if nazwa in SZUKAJACE:
        wzorce, pliki, flagi = rozbierz_wyszukiwanie(argumenty)
        sekretne = [p for p in pliki if sciezka_sekretu(p)]
        tylko_liczba = bool(flagi & {"c", "l", "L", "q", "--count", "--files-with-matches", "--files-without-match", "--quiet", "--silent"})
        odwrocone = bool(flagi & {"v", "--invert-match"})
        if sekretne and not tylko_liczba and (odwrocone or not wzorce or any(NAZWA_SEKRETU.search(w) for w in wzorce)):
            return ("deny", f"„{nazwa}” na {sekretne[0]} wypisałoby wiersz z sekretem. Użyj -c albo -l, "
                            "albo szukaj klucza, który nie jest sekretem")

    # --- sekrety w zmiennych środowiska ---
    if nazwa in ("env", "printenv") and not [a for a in argumenty if not a.startswith("-")]:
        return ("deny", "Pełny wydruk środowiska ujawnia tokeny (np. DANACO_MCP_TOKEN). Same nazwy zmiennych: "
                        "compgen -e; obecność jednej: [ -n \"$NAZWA\" ] && echo jest")
    if nazwa == "printenv" and any(NAZWA_SEKRETU.search(a) for a in argumenty):
        return ("deny", "printenv sekretu wypisałoby jego wartość. Sprawdź tylko obecność: [ -n \"$NAZWA\" ] && echo jest")
    bez_nazw = not [a for a in argumenty if not a.startswith("-")]
    if (nazwa == "set" and not argumenty) or (nazwa == "export" and bez_nazw and set(argumenty) <= {"-p"}) or (
        nazwa in ("declare", "typeset") and bez_nazw and set(argumenty) <= {"-p", "-x", "-px", "-xp"}
    ):
        return ("deny", f"„{' '.join(polecenie)}” wypisuje wszystkie zmienne razem z tokenami. Same nazwy: compgen -e")
    if nazwa in ("echo", "printf"):
        for arg in argumenty:
            # [ -n "$TOKEN" ] sprawdza tylko obecność — tak podpowiada też ten strażnik
            arg = re.sub(r"(\[\[?|test)\s+-[nz]\s+\"?\$\{?[A-Za-z_][A-Za-z0-9_]*\}?\"?", "", arg)
            for zmienna in re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", arg):
                if NAZWA_SEKRETU.search(zmienna) and f"${{#{zmienna}" not in arg:
                    return ("deny", f"{nazwa} ${zmienna} wypisałoby sekret. Sprawdź długość albo obecność: echo ${{#{zmienna}}}")

    # --- operacje nieodwracalne: potwierdza człowiek (--version i --help niczego nie zmieniają) ---
    if any(a in ("--version", "--help", "-h", "-V") for a in argumenty):
        return None
    if nazwa == "git" and argumenty:
        podpolecenie = argumenty[0]
        if podpolecenie == "push" and any(
            a in ("--force", "-f", "--force-with-lease", "--mirror") or a.startswith("--force-with-lease=")
            or (a.startswith("+") and len(a) > 1) for a in argumenty[1:]
        ):
            return ("ask", "Wymuszony push nadpisuje historię na zdalnym repozytorium. Potwierdź, że to zamierzone")
        if podpolecenie in ("filter-repo", "filter-branch"):
            return ("ask", "Przepisanie historii gita jest nieodwracalne dla wszystkich klonów. Potwierdź")
    if nazwa in ("git-filter-repo", "bfg"):
        return ("ask", "Przepisanie historii gita jest nieodwracalne dla wszystkich klonów. Potwierdź")
    if nazwa in ("dropdb", "pg_resetwal", "mkfs") or nazwa.startswith("mkfs."):
        return ("ask", f"{nazwa} niszczy dane bez możliwości cofnięcia. Potwierdź")
    if nazwa == "dd" and any(a.startswith("of=/dev/") for a in argumenty):
        return ("ask", "dd na urządzenie blokowe nadpisuje dysk. Potwierdź")
    if nazwa == "gh" and argumenty[:2] == ["repo", "delete"]:
        return ("ask", "Usunięcie repozytorium GitHub jest nieodwracalne. Potwierdź")
    return None


def ocen(polecenie: str) -> tuple[str, str] | None:
    tekst = bez_heredoc(polecenie)
    if re.search(r"\bDROP\s+(DATABASE|SCHEMA)\b", tekst, re.I):
        return ("ask", "DROP DATABASE/SCHEMA niszczy dane bez możliwości cofnięcia. Potwierdź")
    najostrzejsza: tuple[str, str] | None = None
    for fragment in fragmenty(tekst):
        for slowa in odcinki(fragment):
            wynik = ocen_odcinek(slowa)
            if wynik and wynik[0] == "deny":
                return wynik
            if wynik and najostrzejsza is None:
                najostrzejsza = wynik
    return najostrzejsza


PRZYPADKI: list[tuple[str, str | None]] = [
    # przechodzą — polecenia z codziennej pracy
    ("ssh -i ~/.ssh/admin -o IdentitiesOnly=yes admin@10.10.0.2 'sudo grep -o \"^NEXUS_PLATNOSCI_CENY=\\\"[^\\\"]*\\\"\" /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env | tr \";\" \"\\n\" | sed \"s/=price_.*//\"'", None),
    ("ssh -i ~/.ssh/admin -o IdentitiesOnly=yes admin@10.10.0.2 'sudo env NEXUS_APLIKACJA_DIR=/danaco/nexus/aplikacja deploy/wydania/wypchnij.sh przedsionek 20260928-135957-15e0b05'", None),
    ("sudo -u danaco-nexus bash -c \"set -a; . /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env; . /danaco/nexus/aplikacja/produkcja/konfiguracja/produkcja.env; set +a; python3 deploy/stripe-zaloz-produkty.py --na-sucho\"", None),
    ("bash -n /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", None),
    ("sudo sed -i 's/^NEXUS_X=.*/NEXUS_X=\"1\"/' /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", None),
    ("git push -q -u origin cennik/teksty", None),
    ("git push origin --delete stara-galaz", None),
    (". ~/tmp/env.sh && cd ~/tmp/wt && python3 seed.py", None),
    ("scp -q -i ~/.ssh/admin -o IdentitiesOnly=yes plik admin@10.10.0.2:tmp/", None),
    ("ls -la ~/.ssh/ && cat ~/.ssh/id_ed25519.pub && cat ~/.ssh/config", None),
    ("gh auth status 2>&1 | head -5", None),
    ("echo \"PATH=$PATH\" | tr ':' '\\n' | head", None),
    ("printenv PATH HOME", None),
    ("env NEXUS_DATA_DIR=/tmp/x python3 -m uvicorn nexus.api.app:app", None),
    ("set -euo pipefail; export NEXUS_X=1", None),
    ("grep -c KLUCZ /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", None),
    ("cat > /tmp/skrypt.sh <<'EOF'\ncat /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env\nEOF\nbash -n /tmp/skrypt.sh", None),
    ("tail -5 ~/tmp/wydanie-8.log; cat backend/tests/test_tokens.py | head", None),
    ("git log --oneline -3 && git diff --stat", None),
    ("echo ${#DANACO_MCP_TOKEN}", None),
    ("cat /danaco/uzytkownik/admin/tmp/danaco-lex-biegi/tlumaczenia/tokeny-pl.log | tail -3", None),
    ("git filter-repo --version >/dev/null 2>&1 && echo jest", None),
    ("cat design/tokens.json", None),
    ("set -x; head -1 /etc/passwd; grep -Ev '^#' /etc/pam.d/common-password", None),
    ("jq -r '.mcpServers | keys' /danaco/uzytkownik/admin/.claude.json", None),
    ("sudo grep -h \"^NEXUS_CHMURA_TOKEN_FILE=\" /x/nexus.env", None),
    ("declare -f moja_funkcja", None),
    ("echo '{\"tool_input\":{\"command\":\"cat /etc/danaco/x.env\"}}' | python3 hook.py", None),
    ("git commit -q -m \"Poprawka: cat nexus.env w dokumentacji\"", None),
    ("echo \"TOKEN_SET=$([ -n \"$DANACO_MCP_TOKEN\" ] && echo yes || echo no)\"", None),
    ("head -c 1 /etc/danaco/instytucje-api.env >/dev/null 2>&1 && echo czytelny", None),
    ("grep -n -i \"klucz przeprowadzki\\|nexus_migracja\" /danaco/uzytkownik/admin/.claude/plans/plan-token.md", None),
    ("sudo awk '/x/,0' /etc/caddy/a.caddy | grep -v -i \"haslo\\|token\\|secret\\|key\"", None),
    ("grep -o 'x' wynik.jsonl | grep -i \"sudo\\|KLUCZ_PLIK\"", None),
    ("grep -ci haslo /etc/danaco/ovh.env", None),
    # odrzucane — wypisanie sekretu
    ("cat /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", "deny"),
    ("ssh -i ~/.ssh/admin admin@10.10.0.2 'sudo cat /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env'", "deny"),
    ("tail -3 /etc/danaco/ovh.env", "deny"),
    ("cat /etc/danaco/nie-istnieje.env", "deny"),
    ("env | grep NEXUS", "deny"),
    ("printenv", "deny"),
    ("printenv DANACO_MCP_TOKEN", "deny"),
    ("echo $DANACO_MCP_TOKEN", "deny"),
    ("cat ~/.claude/settings.json", "deny"),
    ("less /danaco/uzytkownik/admin/.claude.json", "deny"),
    ("cat ~/.ssh/id_ed25519", "deny"),
    ("head -1 ~/.config/gh/hosts.yml", "deny"),
    ("grep STRIPE_KLUCZ /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", "deny"),
    ("sudo cat /proc/1234/environ", "deny"),
    ("cat ~/.sekrety/huggingface-token", "deny"),
    ("cat bazy-danych/sekrety/lex_odczyt.haslo 2>/dev/null", "deny"),
    ("sudo cat /danaco/projekty/danaco-nexus/dane/nextcloud/db-haslo", "deny"),
    ("cat \"$NEXUS_PLATNOSCI_STRIPE_KLUCZ_PLIK\"", "deny"),
    ("sudo -u danaco-serwis env", "deny"),
    ("cat service-account-credentials.json", "deny"),
    ("jq . ~/.claude/settings.json", "deny"),
    ("jq '.env' ~/.claude/settings.json", "deny"),
    ("sudo cat /etc/shadow", "deny"),
    ("echo \"$(cat /etc/danaco/x.env)\"", "deny"),
    ("sudo -u danaco-nexus bash -c 'cat /x/nexus.env'", "deny"),
    ("ssh -i ~/.ssh/admin admin@10.10.0.2 \"sudo -u danaco-nexus bash -c 'env'\"", "deny"),
    ("declare -px", "deny"),
    ("set", "deny"),
    ("grep -v '^#' /danaco/nexus/aplikacja/produkcja/konfiguracja/nexus.env", "deny"),
    ("grep -e HASLO -e KLUCZ /etc/danaco/ovh.env", "deny"),
    ("rg -i token ~/.config/gh/hosts.yml", "deny"),
    ("export -p", "deny"),
    # potwierdza człowiek — operacje nieodwracalne
    ("git push --force origin main", "ask"),
    ("git push origin main --force-with-lease", "ask"),
    ("git push origin +main", "ask"),
    ("git filter-repo --path sekret.txt --invert-paths", "ask"),
    ("sudo -u postgres dropdb nexus", "ask"),
    ("psql -c 'DROP DATABASE nexus'", "ask"),
    ("gh repo delete DanacoGroup/danaco-nexus --yes", "ask"),
]


def test_gita() -> int:
    """Plik .env śledzony w gicie przechodzi, nieśledzony — nie."""
    import tempfile

    katalog = tempfile.mkdtemp(prefix="straz-")
    subprocess.run(["git", "init", "-q", katalog], check=True)
    for nazwa, tresc in (("produkcja.env", "SCIEZKA=/danaco\n"), ("lokalny.env", "KLUCZ=x\n")):
        with open(os.path.join(katalog, nazwa), "w", encoding="utf-8") as plik:
            plik.write(tresc)
    subprocess.run(["git", "-C", katalog, "add", "produkcja.env"], check=True)
    KATALOG["cwd"] = katalog
    bledy = 0
    for polecenie, oczekiwane in (("cat produkcja.env", None), ("cat lokalny.env", "deny")):
        wynik = ocen(polecenie)
        if (wynik[0] if wynik else None) != oczekiwane:
            bledy += 1
            print(f"BŁĄD (git): oczekiwano {oczekiwane}: {polecenie}")
    KATALOG["cwd"] = ""
    import shutil

    shutil.rmtree(katalog, ignore_errors=True)
    return bledy


def test() -> int:
    bledy = test_gita()
    for polecenie, oczekiwane in PRZYPADKI:
        wynik = ocen(polecenie)
        decyzja = wynik[0] if wynik else None
        if decyzja != oczekiwane:
            bledy += 1
            print(f"BŁĄD: oczekiwano {oczekiwane}, jest {decyzja}: {polecenie[:110]!r}")
    print(f"przypadki: {len(PRZYPADKI)}, błędy: {bledy}")
    return 1 if bledy else 0


def main() -> int:
    if "--test" in sys.argv:
        return test()
    try:
        zdarzenie = json.load(sys.stdin)
        narzedzie = str(zdarzenie.get("tool_name") or "")
        wejscie = zdarzenie.get("tool_input") or {}
        if not isinstance(wejscie, dict):
            wejscie = {}
        KATALOG["cwd"] = str(zdarzenie.get("cwd") or "")
        polecenie = None
        if narzedzie in ("Bash", "PowerShell", "Monitor"):
            polecenie = str(wejscie.get("command") or "")
        elif narzedzie.startswith("mcp__"):
            for pole in ("command", "cmd", "script", "polecenie"):
                if isinstance(wejscie.get(pole), str):
                    polecenie = wejscie[pole]
                    break
        if polecenie is not None:
            wynik = ocen(polecenie)
        elif narzedzie in ("Read", "NotebookRead"):
            sciezka = str(wejscie.get("file_path") or wejscie.get("notebook_path") or wejscie.get("path") or "")
            wynik = (("deny", f"„{narzedzie} {sciezka}” wypisałoby sekret do rozmowy. Sekrety zostają "
                      "w plikach 600; sprawdź obecność klucza bez wartości")
                     if sciezka and sciezka_sekretu(sciezka) else None)
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
                    "permissionDecisionReason": f"Straż sekretów Danaco: {powod}.",
                }
            },
            sys.stdout,
            ensure_ascii=False,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
