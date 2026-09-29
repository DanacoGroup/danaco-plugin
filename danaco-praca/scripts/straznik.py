#!/usr/bin/env python3
"""Strażnik trybu ciągłej pracy — logika hooków Stop, UserPromptSubmit, PreToolUse
i PreCompact (hook SessionStart obsługuje sam wrapper `hooks/straznik.sh`).

Wywołanie (z wrappera `hooks/straznik.sh`, który najpierw znajduje interpreter Pythona):

    straznik.py stop     < JSON zdarzenia Stop
    straznik.py prompt   < JSON zdarzenia UserPromptSubmit
    straznik.py pretool  < JSON zdarzenia PreToolUse
    straznik.py kompakt  < JSON zdarzenia PreCompact
    straznik.py kontrola < JSON zdarzenia PostToolUse (Bash, PowerShell)

Kody wyjścia: 0 = przepuść, 2 = blokuj (Claude Code pokazuje wtedy modelowi treść
stderr jako powód). Innych kodów skrypt nie zwraca; wrapper traktuje każdy inny kod
jako awarię interpretera i sam blokuje (fail-closed).

Zasada nadrzędna: gdy znacznik zadania w toku istnieje, model NIE MA technicznej
możliwości (a) zakończenia tury, (b) zadania pytania użytkownikowi, (c) zdjęcia
blokady. Blokadę zdejmuje wyłącznie polecenie `/stop` wpisane przez użytkownika na
czacie oraz upływ terminu ważności znacznika. Nie ma limitu prób, zmiennej
środowiskowej ani flagi zwalniającej i nie należy ich dodawać. Znacznik obowiązuje
tylko w sesji, która go założyła; skasowany poleceniem powłoki wraca z kopii spoza
katalogu projektu w trybie `kontrola`.

Fail-closed: wszędzie tam, gdzie strażnik nie potrafi ocenić sytuacji (zepsuty JSON
zdarzenia, brak pola, nieczytelna transkrypcja albo znacznik), blokuje. Tryb włącza
`/pracuj` w tym samym zdarzeniu, czyli hook, a nie model: pominięty krok
`zadanie.py start` wyłączał dotąd cały mechanizm bez żadnego śladu.

UserPromptSubmit jako jedyne NIGDY nie blokuje wiadomości użytkownika — powstaje
z wpisu człowieka, więc jest drogą zwolnienia sterowaną wyłącznie przez człowieka.
Polecenie liczy się tylko przy polu `source` równym `user`, `sdk` albo przy braku
tego pola: wybudzenia z harmonogramu i wstrzyknięcia systemowe blokady nie zwalniają.

Bez znacznika wszystkie podpolecenia zwracają 0 i nic nie robią. Zestaw reguł
PreToolUse (lista przepustek, narzędzia plikowe, powłoka, harmonogram, odbiór wyniku
zadania tłowego, wymóg pracy w tle) opisuje README.md; tu prowadzą go stałe i funkcje
niżej, każda z własnym uzasadnieniem.

Wyjście stderr przy blokadzie CELOWO nie zawiera polecenia kończącego: tekst trafia
do transkrypcji, którą przeszukuje hook Stop, więc sam zwalniałby blokadę.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import znacznik  # noqa: E402

for _strumien in (sys.stdout, sys.stderr):
    # Claude Code czyta wyjście hooka jako UTF-8; na Windows domyślne kodowanie potoku
    # to strona kodowa systemu, co psułoby polskie znaki w komunikatach.
    try:
        _strumien.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

KOD_ZEZWOL = 0
KOD_BLOKUJ = 2

KORZEN_PLUGINU = Path(__file__).resolve().parent.parent

# Ile końcowych bajtów transkrypcji jest przeszukiwane w hooku Stop.
LIMIT_ODCZYTU_TRANSKRYPCJI_B = 8 * 1024 * 1024

NARZEDZIE_PYTANIA = "AskUserQuestion"
NARZEDZIA_PLIKOWE = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
NARZEDZIA_POWLOKI = {"Bash", "PowerShell"}
# Narzędzia dostarczające do sesji wiadomość wyglądającą jak wpis użytkownika - model
# mógłby nimi wstrzyknąć polecenie kończące. Odrzucane w całości.
NARZEDZIA_HARMONOGRAMU = re.compile(
    r"^(CronCreate|ScheduleWakeup|Monitor)$|^mcp__.*(send_later|create_trigger|fire_trigger|update_trigger|schedule|wakeup|cron)",
    re.I,
)
# Narzędzia zatrzymujące zadanie tłowe (`TaskStop`, `KillShell` i pokrewne). Bieg
# puszczony w tło ma dobiec do końca - zatrzymanie kasuje wynik, na który zlecenie czeka.
NARZEDZIA_ZATRZYMANIA = re.compile(
    r"^(?:mcp__[\w.-]+__)?(?:(?:kill|stop|cancel|terminate|abort)[_-]?"
    r"(?:task|tasks|shell|shells|bash|agent|agents|job|jobs|process|background)"
    r"|(?:task|shell|bash|agent|job)[_-]?(?:kill|stop|cancel|terminate|abort))s?$",
    re.I,
)
# Narzędzia wysyłające wiadomość poza turę modelu. Taka wiadomość wraca do sesji wpisem
# nieodróżnialnym od wpisu użytkownika, czyli drogą wstrzyknięcia polecenia kończącego.
NARZEDZIA_WIADOMOSCI = re.compile(
    r"^(?:SendMessage|PushNotification|SlashCommand)$"
    r"|^mcp__[\w.-]+__(?:send_message|send_user_message|notify|push|message)",
    re.I,
)
KOMUNIKAT_WIADOMOSC = (
    "Narzędzie {narzedzie} wysyła wiadomość poza Twoją turę, a taka wiadomość wraca do "
    "sesji wpisem nieodróżnialnym od wpisu użytkownika - to droga do wstrzyknięcia "
    "polecenia kończącego, więc w trybie ciągłej pracy jest zamknięta. Do użytkownika "
    "odzywasz się wyłącznie tekstem na czacie, krótko i tylko wtedy, gdy sam napisał "
    "albo gdy dalsza praca jest niemożliwa."
)

KOMUNIKAT_ZATRZYMANIE = (
    "Narzędzie {narzedzie} zatrzymuje pracę uruchomioną w tle, a w trybie ciągłej pracy "
    "nie przerywasz i nie zabijasz tego, co sam odpaliłeś - bieg w tle ma dobiec do "
    "końca, bo po to poszedł w tło. Zostaw go i zajmij się kolejną częścią zlecenia; "
    "wynik odbierz krótkim sprawdzeniem, gdy będzie gotowy. Jeżeli bieg jest ewidentnie "
    "błędny, odnotuj to w katalogu zlecenia i uruchom poprawiony obok, zamiast kasować "
    "poprzedni."
)
# Pole `source` zdarzenia UserPromptSubmit (opcjonalne): `user` = wpisane w kliencie,
# `sdk` = klienci desktop/remote. Reszta to wstrzyknięcia maszynowe - nie zwalniają
# blokady.
ZRODLA_LUDZKIE = {"user", "sdk"}
# To samo dla wpisów transkrypcji (`origin.kind`, `promptSource`): wybudzenia
# i wiadomości od innych agentów nie liczą się jako wiadomość człowieka.
POCHODZENIA_LUDZKIE = {"human", "user", "unclassified", "sdk"}
ZRODLA_MASZYNOWE = {"system", "loop_wakeup", "schedule_wakeup", "poll_event"}

PLIKI_MECHANIZMU = (
    "scripts/zadanie.py",
    "scripts/straznik.py",
    "scripts/znacznik.py",
    ".claude-plugin/plugin.json",
    "skills/pracuj/SKILL.md",
)
KATALOGI_MECHANIZMU = ("hooks", "skills")

KOMUNIKAT_STOP = (
    "Zlecenie w toku: {opis}. Nie kończ tury i nie pytaj o zakończenie - decyduje o nim "
    "wyłącznie użytkownik swoim poleceniem kończącym. Pracuj dalej narzędziami i NIE pisz do "
    "czatu: w tym trybie użytkownik nie czyta relacji z postępów, a każdy akapit zjada "
    "kontekst, który jest potrzebny na pracę. Żadnych zapowiedzi, streszczeń kroków ani "
    "podsumowań etapów - raport, krótki i w punktach, składasz dopiero po poleceniu użytkownika. "
    "Znacznik leży w: {katalog} (ścieżka dla człowieka).{uwaga}"
)

KOMUNIKAT_PYTANIE = (
    "Narzędzie AskUserQuestion jest zablokowane: w trybie ciągłej pracy model nie ma "
    "prawa zadawać użytkownikowi żadnych pytań - ani o zakres, ani o wybór opcji, ani "
    "o zakończenie. Przyjmij najbardziej rozsądne założenie, zapisz je w dzienniku "
    "(python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/zadanie.py\" krok \"założenie: ...\") "
    "i pracuj dalej nad zleceniem."
)

KOMUNIKAT_PLIK = (
    "Zapis do {sciezka} zablokowany ({powod}). W trakcie aktywnego znacznika trybu "
    "ciągłej pracy nie wolno zmieniać znacznika (.danaco), plików mechanizmu w "
    "katalogu pluginu ani konfiguracji hooków/pluginów Claude Code - nawet pozornie "
    "drobna poprawka jest równoznaczna z samodzielnym zakończeniem zadania. Zostaw "
    "ten plik bez zmian i wróć do właściwego zlecenia."
)

KOMUNIKAT_POLECENIE = (
    "Polecenie zablokowane przez strażnika trybu ciągłej pracy (reguła: {regula}): "
    "dotyka mechanizmu blokady (.danaco, hooki i skrypty strażnika, konfiguracja "
    "hooków/pluginów Claude Code, proces sesji) albo kasuje cały katalog roboczy. "
    "Nie próbuj tego obejść inną formą polecenia - wróć do właściwego zlecenia; jeśli "
    "operacja była potrzebna do zlecenia, wykonaj ją w węższej, precyzyjnej postaci, "
    "która nie dotyka tych plików."
)

KOMUNIKAT_HARMONOGRAM = (
    "Narzędzie {narzedzie} jest zablokowane w trybie ciągłej pracy: wybudzenia z "
    "harmonogramu, monitory i wiadomości „wyślij później\" dostarczają do sesji tekst "
    "wyglądający jak wiadomość użytkownika, a o zakończeniu zlecenia decyduje "
    "wyłącznie prawdziwa wiadomość użytkownika. Pracuj dalej bez tego narzędzia "
    "(np. czekaj na proces poleceniem w Bash zamiast planować wybudzenie)."
)

KOMUNIKAT_ZDARZENIE = (
    "Strażnik trybu ciągłej pracy nie potrafi ocenić tego zdarzenia ({powod}) i "
    "blokuje je (fail-closed). Znacznik zadania w toku jest aktywny - kontynuuj "
    "pracę nad zleceniem innymi narzędziami i nie próbuj obchodzić blokady."
)


NARZEDZIA_PODAGENTA = {"Task", "Agent", "Workflow", "Explore", "Plan", "Orchestrate",
                       "SpawnAgent", "RunAgent", "Delegate"}
# Nazwa narzędzia bywa inna w każdym kliencie i serwerze MCP, więc podagenta
# rozpoznajemy DODATKOWO po kształcie wywołania. Rozstrzyganie po samej nazwie
# przepuszczało wywołania odcinające użytkownika na cały czas pracy podagenta.
POLA_PODAGENTA = ("subagent_type", "agent_type", "agentType", "subagentType")
NAZWA_PODAGENTA = re.compile(
    r"^(?:mcp__[\w.-]+__)?(?:[a-z]+_)*(?:agent|subagent|orchestrator|workflow|delegate)"
    r"(?:_[a-z]+)*$", re.I)
# Odczyt stanu pracy wieloagentowej to nie zlecenie jej: `workflow_status`,
# `agent_list` i pokrewne wracają natychmiast i niczego nie uruchamiają.
KONCOWKI_ODCZYTU = ("_status", "_state", "_list", "_get", "_info", "_result", "_results",
                    "_output", "_progress")
# Pola, które ma narzędzie robocze, a nie zlecenie dla podagenta. Sama para
# „prompt + description" bez nich bywa zwykłym wywołaniem (`WebFetch`, narzędzia MCP).
POLA_NARZEDZIOWE = ("url", "file_path", "path", "query", "command", "script", "cmd",
                    "pattern", "id", "notebook_path", "urls")


def wywolanie_podagenta(narzedzie: str, wejscie: dict) -> bool:
    """Czy wywołanie zleca pracę podagentowi (dowolna nazwa narzędzia)."""
    if narzedzie in NARZEDZIA_ODBIORU_WYNIKU:
        return False
    if narzedzie in NARZEDZIA_PODAGENTA:
        return True
    if any(pole in wejscie for pole in POLA_PODAGENTA):
        return True
    if NAZWA_PODAGENTA.match(narzedzie) and not narzedzie.lower().endswith(KONCOWKI_ODCZYTU):
        return True
    if any(pole in wejscie for pole in POLA_NARZEDZIOWE):
        return False
    return isinstance(wejscie.get("prompt"), str) and isinstance(wejscie.get("description"), str)
KOMUNIKAT_PODAGENT_SYNCHRONICZNY = (
    "Wywołanie {narzedzie} czekające na wynik na pierwszym planie jest odrzucone. Praca "
    "wieloagentowa jest dozwolona, ale musi iść w tle: dopóki czekasz, nie odpala się "
    "żaden hook i użytkownik nie ma jak się do Ciebie odezwać. Uruchom podagenta w "
    "wariancie tłowym (pole oznaczające pracę w tle, workflow zwracający identyfikator "
    "zadania) i odbierz wynik powiadomieniem, albo - gdy klient takiego wariantu nie ma "
    "- wykonaj tę pracę sam serią krótkich wywołań. Niczego nie przerywaj i nie zabijaj."
)
# Reguła nadrzędna: model nigdy nie czeka na wynik procesu na pierwszym planie. Podczas
# trwającego wywołania nie odpala się żaden hook, więc czekanie odcina użytkownika.
# Proces ma działać dalej, tylko w tle - nie jest zabijany ani skracany. Polecenia
# nieskończone (serwery, obserwatory) idą w tło bezwarunkowo: limit czasu ich nie skróci.
POLECENIA_NIESKONCZONE = re.compile(
    r"(?:^|[;&|]\s*)(?:"
    r"npm\s+(?:run\s+)?(?:dev|start)"
    r"|(?:yarn|pnpm)\s+(?:dev|start)"
    r"|docker\s+compose(?:\s+[^;|&\n]*)?\s+up"
    r"|tail\s[^;|&\n]*(?:-{1,2}[fF](?![\w])|--follow)|watch\s|journalctl\s[^;|&]*-f"
    r"|less\s+\+F|(?<![\w./-])nc\s[^;|&\n]*-l|(?<![\w./-])(?:socat|ncat)(?![\w-])"
    r"|(?<![\w./-])tcpdump(?![\w-])|strace\s[^;|&\n]*-p"
    r"|vite(?:\s|$)|next\s+dev|serve(?:\s|$)"
    r"|python3?\s+-m\s+http\.server|uvicorn|gunicorn|nodemon"
    r")",
    re.IGNORECASE,
)
# Ile sekund wolno czekać na wynik na pierwszym planie w jednym wywołaniu. Próg równy
# domyślnemu limitowi narzędzia Bash w kliencie: wywołanie bez własnej deklaracji limitu
# i tak zostanie przerwane po tym czasie. Dłuższe idzie w tło.
LIMIT_PIERWSZEGO_PLANU_S = 120
# Polecenia powłoki, których jedyną funkcją jest czekanie na cudzy proces albo na plik.
# Limit czasu ich nie ratuje: dopóki trwają, tura stoi.
POLECENIA_OCZEKIWANIA = re.compile(
    r"(?:^|[;&|(]\s*|\b(?:then|do|else)\s+)wait(?:\s|$|;)"
    r"|\bxargs\s+(?:-\S+\s+)*wait\b"
    r"|\b(?:while|until)\b[^\n]*?(?:\bsleep\b|\btest\s+-[ef]\b|\[\s*-[ef]\s)"
    r"|\bfor\b[^\n]*?;\s*do\b[^\n]*?\bsleep\b"
    r"|\btail\b[^\n]*--pid"
    r"|\bflock\b(?![^\n]*(?:-n|--nonblock))"
    r"|\bwait-for(?:-it)?\b|\bwaitpid\b",
    re.IGNORECASE,
)

# --- Cisza w trakcie zlecenia ---------------------------------------------------------
# Zlecenie ma JEDEN raport - końcowy, po poleceniu kończącym użytkownika. Sama
# instrukcja tekstowa okazała się za słaba, więc reguła ma bramkę: pierwsze wywołanie
# narzędzia po zbyt długiej wypowiedzi jest odrzucane.

# Odrzucenie jest jednorazowe dla danej wypowiedzi - tekst już poszedł na czat, więc
# druga blokada tylko zatrzymywałaby pracę. Próg dotyczy wyłącznie odpowiedzi na
# wiadomość użytkownika; MIĘDZY wywołaniami obowiązuje cisza bez progu, bo mierzenie
# długości krótkich meldunków przepuszczało je wszystkie.
PROG_ODPOWIEDZI_UZYTKOWNIKOWI = 350
NAZWA_PLIKU_NAPOMNIENIA = "napomnienie-ciszy.json"
LIMIT_OGONA_TRANSKRYPCJI_B = 256 * 1024
KOMUNIKAT_CISZA_MIEDZY_WYWOLANIAMI = (
    "Przed tym wywołaniem napisałeś na czacie {znaki} znaków, a między wywołaniami "
    "narzędzi obowiązuje cisza - bez progu i bez wyjątku dla krótkich zdań. Meldunki "
    "w rodzaju „gotowe 59 ze 137\", „test dalej liczy\", „przechodzę do kolejnej "
    "pozycji\" są dokładnie tym, czego ten tryb zabrania: użytkownik widzi postęp po "
    "wywołaniach narzędzi, a każde takie zdanie zjada kontekst i czas. Zlecenie ma "
    "JEDEN raport - końcowy, po poleceniu kończącym użytkownika. Wolno Ci napisać "
    "tylko dwie rzeczy: krótką odpowiedź na wiadomość, którą użytkownik napisał w "
    "trakcie pracy, oraz uprzedzenie o przeszkodzie uniemożliwiającej dalszą pracę. "
    "To wywołanie jest odrzucone jeden raz, jako przypomnienie - powtórz je bez "
    "żadnego tekstu na czacie. Postęp, który chcesz zachować, zapisz w katalogu "
    "zlecenia (`zadanie.py krok \"…\"`), nie na czacie."
)
KOMUNIKAT_CISZA_DLUGA_ODPOWIEDZ = (
    "Odpowiedź na wiadomość użytkownika ma {znaki} znaków, czyli powyżej progu {prog}. "
    "W trakcie zlecenia odpowiadasz krótko i wracasz do pracy - pełny obraz idzie w "
    "raporcie końcowym po poleceniu kończącym. To wywołanie jest odrzucone jeden raz; "
    "powtórz je bez tekstu na czacie."
)


def _wpis_jest_wypowiedzia_czlowieka(wpis: dict) -> bool:
    return any(tekst.strip() for tekst in _teksty_uzytkownika(wpis))


def _ostatnia_wypowiedz_modelu(sciezka: str | None) -> tuple[str, int, bool, str] | None:
    """Ostatnia wypowiedź modelu na czacie: (identyfikator wpisu, liczba znaków, czy
    była odpowiedzią na wiadomość użytkownika, czas wpisu).

    Liczą się wyłącznie bloki `text` - rozumowanie i wywołania narzędzi nie trafiają na
    czat. O tym, czy wypowiedź jest odpowiedzią człowiekowi, rozstrzyga najbliższy
    wcześniejszy wpis. Nieczytelna transkrypcja nie blokuje pracy."""
    if not sciezka:
        return None
    try:
        linie = _linie_ogona(sciezka, LIMIT_OGONA_TRANSKRYPCJI_B)
    except OSError:
        return None
    for pozycja in range(len(linie) - 1, -1, -1):
        try:
            wpis = json.loads(linie[pozycja])
        except (ValueError, TypeError):
            continue
        if not isinstance(wpis, dict) or wpis.get("type") != "assistant":
            continue
        if wpis.get("isSidechain") or wpis.get("isMeta"):
            continue
        wiadomosc = wpis.get("message")
        if not isinstance(wiadomosc, dict) or not isinstance(wiadomosc.get("content"), list):
            continue
        znaki = sum(len(str(k.get("text") or "")) for k in wiadomosc["content"]
                    if isinstance(k, dict) and k.get("type") == "text")
        identyfikator = str(wpis.get("uuid") or wpis.get("timestamp") or "")
        if not identyfikator:
            return None
        odpowiedz = False
        for wczesniejsza in range(pozycja - 1, -1, -1):
            try:
                poprzedni = json.loads(linie[wczesniejsza])
            except (ValueError, TypeError):
                continue
            if not isinstance(poprzedni, dict) or poprzedni.get("type") == "assistant":
                continue
            odpowiedz = _wpis_jest_wypowiedzia_czlowieka(poprzedni)
            break
        return identyfikator, znaki, odpowiedz, str(wpis.get("timestamp") or "")
    return None


def _napomnienie_juz_wydane(katalog, identyfikator: str) -> bool:
    """Czy za tę wypowiedź model dostał już odrzucenie. Zapis idzie przy pierwszym
    odrzuceniu, żeby kolejne wywołanie po niej przeszło i praca ruszyła dalej."""
    sciezka = katalog / NAZWA_PLIKU_NAPOMNIENIA
    try:
        zapisane = json.loads(sciezka.read_text(encoding="utf-8")).get("wpis")
    except (OSError, ValueError, AttributeError):
        zapisane = None
    if zapisane == identyfikator:
        return True
    try:
        znacznik.zapisz_atomowo(sciezka, json.dumps({"wpis": identyfikator, "czas": znacznik.teraz()},
                                                    ensure_ascii=False))
    except OSError:
        pass
    return False


def _wypowiedz_sprzed_zlecenia(wpis_czas: str | None, dane: dict | None) -> bool:
    """Czy wypowiedź jest starsza niż początek zlecenia."""
    czas = znacznik.parsuj_czas(wpis_czas)
    poczatek = znacznik.parsuj_czas((dane or {}).get("rozpoczeto"))
    return czas is not None and poczatek is not None and czas < poczatek


def bramka_ciszy(katalog, zdarzenie: dict) -> int | None:
    """Kod blokady, gdy model pisał na czacie zamiast milczeć."""
    ostatnia = _ostatnia_wypowiedz_modelu(transkrypcja_ze_zdarzenia(zdarzenie))
    if ostatnia is None:
        return None
    identyfikator, znaki, odpowiedz_uzytkownikowi, czas_wpisu = ostatnia
    if znaki == 0:
        return None
    if _wypowiedz_sprzed_zlecenia(czas_wpisu,
                                  znacznik.wczytaj_znacznik(katalog, sesja_ze_zdarzenia(zdarzenie))):
        return None
    if odpowiedz_uzytkownikowi and znaki <= PROG_ODPOWIEDZI_UZYTKOWNIKOWI:
        return None
    if _napomnienie_juz_wydane(katalog, identyfikator):
        return None
    if odpowiedz_uzytkownikowi:
        return blokuj(KOMUNIKAT_CISZA_DLUGA_ODPOWIEDZ.format(
            znaki=znaki, prog=PROG_ODPOWIEDZI_UZYTKOWNIKOWI))
    return blokuj(KOMUNIKAT_CISZA_MIEDZY_WYWOLANIAMI.format(znaki=znaki))


# --- Bramka sprawdzeń stanu -----------------------------------------------------------
# Zakaz czekania na pierwszym planie zostawił drugą drogę do przerwy: model puszczał
# pracę w tło i wielokrotnie sprawdzał ten sam bieg zamiast wykonywać kolejną część
# zlecenia. Każde takie wywołanie z osobna jest krótkie i legalne.
LIMIT_KOLEJNYCH_SPRAWDZEN = 3
# Wyjście awaryjne: gdy została już tylko praca w tle, licznik przestaje obowiązywać
# po tym odstępie od ostatniego sprawdzenia.
ODSTEP_SPRAWDZENIA_S = 300
PRZEDROSTEK_LICZNIKA = "sprawdzenia"
ROZSZERZENIE_LICZNIKA = ".licznik"
# Polecenia, których jedynym wynikiem jest odpowiedź na pytanie „czy to już koniec".
_SPRAWDZENIA_STANU = frozenset({
    "ps", "pgrep", "pidof", "jobs", "top", "htop", "uptime", "date", "sleep", "true",
    "echo", "printf", "pwd", "get-process", "get-date",
})
# Polecenia odczytu, które są sprawdzeniem biegu wtedy, gdy czytają jego log.
_ODCZYTY_LOGU = frozenset({
    "tail", "head", "cat", "less", "tac", "nl", "wc", "stat", "ls", "test", "[", "du",
    "file", "get-content", "get-childitem",
})
# Filtry przycinające wynik sprawdzenia (`ps aux | grep serwer`). Liczą się wyłącznie
# za pierwszym segmentem - `cat src/main.go | grep TODO` to praca.
_FILTRY_WYNIKU = frozenset({
    "grep", "egrep", "fgrep", "rg", "sed", "awk", "sort", "uniq", "cut", "tr", "head",
    "tail", "wc", "jq", "select-string", "measure-object", "where-object",
})
# Narzędzia klienta, których wywołanie jest zajrzeniem do cudzego biegu.
NARZEDZIA_PRZEGLADU_ZADAN = {"TaskList", "TaskGet", "ListTasks"}
# Narzędzia sterujące, które nie są ani pracą, ani sprawdzeniem: nie zerują licznika
# i nie zwiększają go.
NARZEDZIA_NEUTRALNE = {"TodoWrite", "ToolSearch", "Skill", "ListMcpResources"}
# Przekierowanie w poleceniu: zapis to praca, choćby polecenie zaczynało się od `echo`.
# `2>&1` i zapis do `/dev/null` przekierowaniem w tym sensie nie są.
_PRZEKIEROWANIE_ZAPISU = re.compile(r">>?\s*(?!&\d|/dev/null|\$null)[^\s;|&]")

KOMUNIKAT_SPRAWDZENIE_BEZ_PRACY = (
    "To już {licznik}. sprawdzenie stanu z rzędu ({powod}), bez ani jednej wykonanej "
    "pracy pomiędzy. Bieg w tle nie jest Twoją pracą - jest pracą maszyny, przy której "
    "masz nie stać. Wróć do zlecenia i wykonaj następną niezależną część, a po wynik "
    "biegu sięgnij po jej zakończeniu. Biegu nie przerywaj i nie zabijaj. Jeżeli "
    "naprawdę nie ma czego robić poza czekaniem, wolno sprawdzić ponownie po {odstep} "
    "minutach od poprzedniego sprawdzenia."
)


def _nazwa_polecenia(token: str) -> str:
    return os.path.basename(token.strip("\"'")).lower()


def _segment_jest_sprawdzeniem(tokeny: list[str], logi: tuple[str, ...] = ()) -> bool:
    """Czy segment polecenia jest wyłącznie zajrzeniem do stanu biegu."""
    tokeny = [t for t in tokeny if t]
    while tokeny and (_nazwa_polecenia(tokeny[0]) in _PREFIKSY_URUCHOMIENIA
                      or _PRZYPISANIE_ZMIENNEJ.match(tokeny[0])
                      or _ARGUMENT_CZASU.match(tokeny[0])):
        tokeny = tokeny[1:]
    if not tokeny:
        return False
    nazwa = _nazwa_polecenia(tokeny[0])
    if nazwa in _SPRAWDZENIA_STANU:
        return True
    if nazwa not in _ODCZYTY_LOGU:
        return False
    cele = [t for t in tokeny[1:] if not t.startswith("-") and not _ARGUMENT_CZASU.match(t)]
    return bool(cele) and all(_jest_logiem_biegu(cel, logi) for cel in cele)


def _segment_jest_filtrem(tokeny: list[str]) -> bool:
    tokeny = [t for t in tokeny if t]
    return bool(tokeny) and _nazwa_polecenia(tokeny[0]) in _FILTRY_WYNIKU


def _jest_logiem_biegu(cel: str, logi: tuple[str, ...]) -> bool:
    """Czy ścieżka jest logiem biegu uruchomionego w tym zleceniu.

    Rozstrzyga rejestr celów przekierowania, a nie nazwa pliku: po nazwie logiem był
    każdy plik z ciągiem „log" (`blog.md`, `CHANGELOG.md`)."""
    cel = cel.strip("\"'")
    nazwa = os.path.basename(cel)
    if nazwa == "nohup.out":
        return True
    return any(cel == log or nazwa == os.path.basename(log) for log in logi)


def _polecenie_jest_sprawdzeniem(tresc: str, logi: tuple[str, ...] = ()) -> bool:
    if _PRZEKIEROWANIE_ZAPISU.search(tresc):
        return False
    segmenty = _segmenty_polecenia(tresc)
    if not segmenty or not _segment_jest_sprawdzeniem(segmenty[0], logi):
        return False
    return all(_segment_jest_sprawdzeniem(s, logi) or _segment_jest_filtrem(s)
               for s in segmenty[1:])


def _odbior_natychmiastowy(wejscie: dict) -> bool:
    """Czy odbiór wyniku zadania tłowego wraca od razu, zamiast czekać na koniec."""
    if wejscie.get(POLE_BLOKOWANIA_ODBIORU) is False:
        return True
    limit = limit_wywolania_s(wejscie)
    return limit is not None and limit <= LIMIT_ODBIORU_WYNIKU_S


def tresc_polecenia(narzedzie: str, wejscie: dict) -> str | None:
    """Treść polecenia powłoki w wywołaniu - także w narzędziu MCP, które jest powłoką
    pod inną nazwą (pole `command`, `script` albo `cmd`)."""
    for pole in ("command", "script", "cmd"):
        wartosc = wejscie.get(pole)
        if isinstance(wartosc, str) and wartosc.strip():
            return wartosc
    return None


def _wywolanie_jest_sprawdzeniem(narzedzie: str, wejscie: dict,
                                 logi: tuple[str, ...] = ()) -> str | None:
    """Krótki opis powodu, gdy wywołanie jest wyłącznie sprawdzeniem stanu cudzego
    biegu, albo None, gdy wykonuje jakąkolwiek pracę."""
    if narzedzie in NARZEDZIA_ODBIORU_WYNIKU:
        return f"{narzedzie}: odbiór wyniku zadania tłowego"
    if narzedzie in NARZEDZIA_PRZEGLADU_ZADAN:
        return f"{narzedzie}: przegląd zadań tłowych"
    if narzedzie in {"Read", "NotebookRead"}:
        sciezka = wejscie.get("file_path") or wejscie.get("notebook_path")
        if isinstance(sciezka, str) and _jest_logiem_biegu(sciezka, logi):
            return "odczyt logu biegu"
        return None
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is not None and _polecenie_jest_sprawdzeniem(tresc, logi):
        return f"polecenie sprawdzające ({tresc.strip().splitlines()[0][:60]})"
    return None


def _sciezka_licznika_sprawdzen(katalog, sesja: str):
    """Plik licznika sprawdzeń tej sesji.

    Rozszerzenie nie może być `.json`: każdy plik `.json` w katalogu `zadania` liczy się
    jako zlecenie osobnej rozmowy."""
    if sesja:
        nazwa = f"{PRZEDROSTEK_LICZNIKA}-{znacznik.nazwa_pliku_sesji(sesja)[:-5]}{ROZSZERZENIE_LICZNIKA}"
        return znacznik.katalog_zadan(katalog) / nazwa
    return katalog / f"{PRZEDROSTEK_LICZNIKA}{ROZSZERZENIE_LICZNIKA}"


def _wczytaj_licznik(sciezka) -> dict:
    try:
        dane = json.loads(sciezka.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dane if isinstance(dane, dict) else {}


def _zapisz_licznik(sciezka, dane: dict) -> None:
    try:
        sciezka.parent.mkdir(parents=True, exist_ok=True)
        znacznik.zapisz_atomowo(sciezka, json.dumps(dane, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError):
        pass


def _odstep_od(czas: str | None) -> float | None:
    """Ile sekund minęło od podanego znacznika czasu (None, gdy nie da się ustalić)."""
    poprzednio = znacznik.parsuj_czas(czas)
    teraz_dt = znacznik.parsuj_czas(znacznik.teraz())
    if poprzednio is None or teraz_dt is None:
        return None
    return (teraz_dt - poprzednio).total_seconds()


LIMIT_ZAPAMIETANYCH_LOGOW = 20
_CEL_PRZEKIEROWANIA = re.compile(r">>?\s*(?!&\d|/dev/null|\$null)([^\s;|&]+)")


def _logi_z_polecenia(tresc: str) -> list[str]:
    """Pliki, do których bieg puszczony w tle kieruje swoje wyjście."""
    cele = [c.strip("\"'") for c in _CEL_PRZEKIEROWANIA.findall(tresc)]
    if not cele and _NOHUP_NA_POZYCJI_POLECENIA.search(tresc):
        cele = ["nohup.out"]
    return cele


def zapamietaj_log_biegu(katalog, sesja: str, narzedzie: str, wejscie: dict) -> None:
    """Zapamiętuje cele przekierowania biegu uruchomionego w tle. Rejestr rozstrzyga
    później, czy odczyt pliku jest zaglądaniem do biegu, czy pracą nad projektem."""
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is None or not (uruchomione_w_tle(wejscie) or polecenie_w_tle(tresc)):
        return
    nowe = _logi_z_polecenia(tresc)
    if not nowe:
        return
    sciezka = _sciezka_licznika_sprawdzen(katalog, sesja)
    stan = _wczytaj_licznik(sciezka)
    logi = [l for l in stan.get("logi", []) if isinstance(l, str)]
    for cel in nowe:
        if cel not in logi:
            logi.append(cel)
    stan["logi"] = logi[-LIMIT_ZAPAMIETANYCH_LOGOW:]
    _zapisz_licznik(sciezka, stan)


# Powtórzenie tego samego wywołania. Bramka sprawdzeń stanu liczy tylko wywołania
# rozpoznane jako zaglądanie do biegu, więc odpytywanie pliku `.rc` w kółko przez pół
# godziny przechodziło jako zwykłe polecenie.
LIMIT_POWTORZEN = 3
# Przeplot dwóch wywołań w kółko omija licznik powtórzeń, a jest tym samym staniem:
# sześć wywołań bez zmiany stanu i najwyżej dwa różne odciski to pętla.
DLUGOSC_HISTORII_WYWOLAN = 6
LIMIT_ROZNYCH_W_PETLI = 2
KOMUNIKAT_PETLA_WYWOLAN = (
    "To {ile} wywołań z rzędu, w których nic nie zmieniłeś, a padły w nich tylko dwa "
    "różne polecenia na przemian - to pętla, nie praca. Wykonaj następną część zlecenia "
    "albo zapisz wynik; po stan biegu wróć po jej zakończeniu."
)
KOMUNIKAT_POWTORZENIE = (
    "To {ile}. identyczne wywołanie z rzędu ({fragment}) - między powtórzeniami nic nie "
    "zmieniłeś, więc każde następne da ten sam wynik. Odpytywanie tego samego stanu "
    "w kółko jest staniem, nawet gdy polecenie wygląda na pracę. Zrób następną "
    "niezależną część zlecenia i wróć tu po jej zakończeniu; jeżeli czekasz na cudzy "
    "proces, wróć po pięciu minutach albo po zrobieniu czegoś innego."
)


def _wywolanie_zmienia_stan(narzedzie: str, wejscie: dict) -> bool:
    """Czy wywołanie zapisuje cokolwiek. Powtórzony zapis jest normalną pracą -
    poprawka po poprawce w tym samym pliku nie jest staniem."""
    if narzedzie in NARZEDZIA_PLIKOWE:
        return True
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is None:
        return False
    return bool(_PRZEKIEROWANIE_ZAPISU.search(tresc) or _POLECENIE_ZMIENIAJACE.search(tresc))


# Odcisk odporny na kosmetyczne warianty: model zmieniał w odpytaniu format wydruku
# (`%.1fG` na `%.2fG`), więc liczy się to, co polecenie uruchamia i czego dotyka.
PROG_PODOBIENSTWA = 0.8
MIN_TOKENOW_DO_PODOBIENSTWA = 4
_TOKEN_SCIEZKI = re.compile(r"^[~./]?[\w./~-]*[/.][\w./~-]*$")
# Argument będący zwykłym słowem albo ścieżką. Program `awk` i format wydruku odciskiem
# nie są - to w nich model zmieniał znak.
_TOKEN_PROSTY = re.compile(r"^[\w.@:+-]{1,60}$")


def _zbior_tokenow(narzedzie: str, wejscie: dict) -> frozenset:
    """Nazwy uruchamianych poleceń i dotykane ścieżki - bez liczb i formatów wydruku."""
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is None:
        wartosc = _odcisk_wywolania(narzedzie, wejscie)
        return frozenset({narzedzie, os.path.basename(wartosc.split(":", 1)[-1])[:60]})
    tokeny = set()
    for segment in _segmenty_polecenia(tresc):
        czysty = [token for token in segment if not _PRZYPISANIE_ZMIENNEJ.match(token)]
        if czysty:
            tokeny.add(_nazwa_polecenia(czysty[0]))
        pierwszy_argument = True
        for token in czysty[1:]:
            goly = token.strip("\"'$")
            if not goly or goly.startswith("-") or _ARGUMENT_CZASU.match(goly):
                continue
            # Pierwszy argument to zwykle podpolecenie (`npm test`, `git log`) i musi
            # rozróżniać wywołania; dalsze liczą się, gdy wskazują plik.
            if (pierwszy_argument and _TOKEN_PROSTY.match(goly)) or _TOKEN_SCIEZKI.match(goly):
                tokeny.add(os.path.basename(goly.rstrip("/"))[:60])
            pierwszy_argument = False
    return frozenset(token for token in tokeny if token)


def _podobne(pierwszy: frozenset, drugi: frozenset) -> bool:
    """Czy dwa wywołania robią to samo. Przy krótkich zbiorach wymagana jest równość."""
    if not pierwszy or not drugi:
        return False
    if pierwszy == drugi:
        return True
    if min(len(pierwszy), len(drugi)) < MIN_TOKENOW_DO_PODOBIENSTWA:
        return False
    wspolne = len(pierwszy & drugi)
    return wspolne / len(pierwszy | drugi) >= PROG_PODOBIENSTWA


def _odcisk_wywolania(narzedzie: str, wejscie: dict) -> str:
    """Nazwa narzędzia z głównym argumentem - do rozpoznania, czy kolejne wywołanie jest
    powtórzeniem poprzedniego."""
    for pole in ("command", "script", "cmd", "file_path", "notebook_path", "pattern",
                 "url", "path", "query"):
        wartosc = wejscie.get(pole)
        if isinstance(wartosc, str) and wartosc.strip():
            return f"{narzedzie}:{wartosc.strip()[:200]}"
    return narzedzie


def _licznik_biezacy(stan: dict) -> int:
    """Liczba sprawdzeń pod rząd, z uwzględnieniem wyjścia awaryjnego po odstępie."""
    odstep = _odstep_od(stan.get("ostatnie"))
    if odstep is not None and odstep >= ODSTEP_SPRAWDZENIA_S:
        return 0
    return int(stan.get("podRzad") or 0)


def odnotuj_wywolanie(katalog, sesja: str, narzedzie: str, wejscie: dict) -> None:
    """Dopisuje do licznika wywołanie, które strażnik DOPUŚCIŁ.

    Powtórzenie tego samego odczytu nie zeruje licznika - inaczej jedno wywołanie
    wplecione między sprawdzenia wystarczyłoby, by sprawdzać bieg bez końca."""
    if narzedzie in NARZEDZIA_NEUTRALNE:
        return
    sciezka = _sciezka_licznika_sprawdzen(katalog, sesja)
    stan = _wczytaj_licznik(sciezka)
    powod = _wywolanie_jest_sprawdzeniem(narzedzie, wejscie, tuple(stan.get("logi", [])))
    if powod is not None:
        stan.update({"podRzad": _licznik_biezacy(stan) + 1, "ostatnie": znacznik.teraz(),
                     "powod": powod})
        _zapisz_licznik(sciezka, stan)
        return
    odcisk = _odcisk_wywolania(narzedzie, wejscie)
    if odcisk == stan.get("ostatniaPraca") and narzedzie not in NARZEDZIA_PLIKOWE:
        return
    stan["podRzad"] = 0
    stan["ostatniaPraca"] = odcisk
    _zapisz_licznik(sciezka, stan)


def _historia_zbiorow(stan: dict) -> list:
    return [frozenset(w) for w in stan.get("historia", []) if isinstance(w, list)]


def odnotuj_powtorzenie(katalog, sesja: str, narzedzie: str, wejscie: dict) -> None:
    """Prowadzi licznik powtórzeń tego samego wywołania i historię ostatnich."""
    sciezka = _sciezka_licznika_sprawdzen(katalog, sesja)
    stan = _wczytaj_licznik(sciezka)
    if _wywolanie_zmienia_stan(narzedzie, wejscie):
        # Zapis przerywa pętlę: od niego historia liczy się od nowa.
        stan.update({"historia": [], "powtorzen": 0, "powtarzane": []})
        _zapisz_licznik(sciezka, stan)
        return
    tokeny = _zbior_tokenow(narzedzie, wejscie)
    poprzednie = frozenset(stan.get("powtarzane") or [])
    stan["powtarzane"] = sorted(tokeny)
    stan["powtorzen"] = (int(stan.get("powtorzen") or 0) + 1
                         if _podobne(tokeny, poprzednie) else 1)
    stan["ostatniePowtorzenie"] = znacznik.teraz()
    historia = [sorted(z) for z in _historia_zbiorow(stan)]
    historia.append(sorted(tokeny))
    stan["historia"] = historia[-DLUGOSC_HISTORII_WYWOLAN:]
    _zapisz_licznik(sciezka, stan)


def bramka_powtorzen(katalog, zdarzenie: dict, narzedzie: str, wejscie: dict) -> int | None:
    """Kod blokady, gdy model powtarza to samo wywołanie, nic między nimi nie zmieniając."""
    if narzedzie in NARZEDZIA_NEUTRALNE or _wywolanie_zmienia_stan(narzedzie, wejscie):
        return None
    stan = _wczytaj_licznik(_sciezka_licznika_sprawdzen(katalog, sesja_ze_zdarzenia(zdarzenie)))
    if not _podobne(_zbior_tokenow(narzedzie, wejscie),
                    frozenset(stan.get("powtarzane") or [])):
        return None
    ile = int(stan.get("powtorzen") or 0) + 1
    if ile <= LIMIT_POWTORZEN:
        return None
    odstep = _odstep_od(stan.get("ostatniePowtorzenie"))
    if odstep is not None and odstep >= ODSTEP_SPRAWDZENIA_S:
        return None
    zapisz_dziennik_ciszy(katalog, narzedzie, f"powtórzenie odrzucone ({ile}. raz)")
    return blokuj(KOMUNIKAT_POWTORZENIE.format(
        ile=ile, fragment=_odcisk_wywolania(narzedzie, wejscie)[:80]))


def bramka_petli_wywolan(katalog, zdarzenie: dict, narzedzie: str,
                         wejscie: dict) -> int | None:
    """Kod blokady, gdy model krąży między dwoma wywołaniami, nic nie zmieniając."""
    if narzedzie in NARZEDZIA_NEUTRALNE or _wywolanie_zmienia_stan(narzedzie, wejscie):
        return None
    stan = _wczytaj_licznik(_sciezka_licznika_sprawdzen(katalog, sesja_ze_zdarzenia(zdarzenie)))
    przyszla = (_historia_zbiorow(stan)
                + [_zbior_tokenow(narzedzie, wejscie)])[-DLUGOSC_HISTORII_WYWOLAN:]
    if len(przyszla) < DLUGOSC_HISTORII_WYWOLAN:
        return None
    rozne: list = []
    for zbior in przyszla:
        if not any(_podobne(zbior, znane) for znane in rozne):
            rozne.append(zbior)
    if len(rozne) > LIMIT_ROZNYCH_W_PETLI:
        return None
    odstep = _odstep_od(stan.get("ostatniePowtorzenie"))
    if odstep is not None and odstep >= ODSTEP_SPRAWDZENIA_S:
        return None
    zapisz_dziennik_ciszy(katalog, narzedzie, "pętla wywołań odrzucona")
    return blokuj(KOMUNIKAT_PETLA_WYWOLAN.format(ile=DLUGOSC_HISTORII_WYWOLAN))


def bramka_sprawdzen_stanu(katalog, zdarzenie: dict, narzedzie: str,
                           wejscie: dict) -> int | None:
    """Kod blokady, gdy model zamiast pracować odpytuje w kółko własny bieg w tle."""
    if narzedzie in NARZEDZIA_NEUTRALNE:
        return None
    if narzedzie in NARZEDZIA_ODBIORU_WYNIKU and not _odbior_natychmiastowy(wejscie):
        # Odbiór w wariancie czekającym odrzuca osobna reguła i to jej komunikat jest
        # tu właściwy.
        return None
    stan = _wczytaj_licznik(_sciezka_licznika_sprawdzen(katalog, sesja_ze_zdarzenia(zdarzenie)))
    powod = _wywolanie_jest_sprawdzeniem(narzedzie, wejscie, tuple(stan.get("logi", [])))
    if powod is None:
        return None
    licznik = _licznik_biezacy(stan) + 1
    if licznik > LIMIT_KOLEJNYCH_SPRAWDZEN:
        zapisz_dziennik_ciszy(katalog, narzedzie, f"sprawdzenie bez pracy odrzucone: {powod}")
        return blokuj(KOMUNIKAT_SPRAWDZENIE_BEZ_PRACY.format(
            licznik=licznik, powod=powod, odstep=int(ODSTEP_SPRAWDZENIA_S // 60)))
    return None




# --- Wymóg pracy w tle dla poleceń powłoki --------------------------------------------
# Na pierwszym planie zostaje wyłącznie WGLĄD - polecenia wracające natychmiast. Reszta
# idzie w tło, także z krótkim limitem: limit mówi, kiedy polecenie zostanie przerwane,
# a nie kiedy się skończy. Lista wglądu jest zamknięta - czego tu nie ma, idzie w tło.
POLECENIA_WGLADU = frozenset({
    "ls", "cat", "head", "tail", "grep", "egrep", "fgrep", "rg", "find", "wc", "stat",
    "file", "du", "df", "sed", "git", "echo", "printf", "pwd", "cd", "basename",
    "dirname", "realpath", "readlink", "sort", "uniq", "cut", "tr", "jq", "diff",
    "cmp", "which", "true", "test", "[", "nl", "tree", "ps", "env", "date", "uname",
    "hostname", "whoami", "id",
    # `kill` nie odczytuje stanu, ale wraca natychmiast: wysłanie sygnału nie jest
    # pracą, przy której model mógłby stać. Ograniczenia sygnałów i celów rozstrzyga
    # osobna reguła ochrony sesji.
    "kill",
})
# Odpowiednik listy wglądu dla PowerShella: te same odczyty, inne nazwy. Porównanie
# idzie po nazwie zapisanej małymi literami, bo PowerShell nie rozróżnia wielkości.
POLECENIA_WGLADU_POWERSHELL = frozenset({
    "get-childitem", "gci", "dir", "ls", "get-content", "gc", "type", "cat",
    "select-string", "sls", "get-item", "gi", "get-itemproperty", "test-path",
    "get-location", "pwd", "measure-object", "write-output", "echo", "out-string",
    "sort-object", "select-object", "where-object", "format-table", "format-list",
    "get-date", "resolve-path", "get-process", "compare-object", "convertfrom-json",
})
# Podpolecenia `git`, które wyłącznie czytają. Reszta (`clone`, `pull`, `push`, `commit`,
# `checkout`, `merge`) sięga po sieć albo zmienia repozytorium - to praca, nie wgląd.
PODPOLECENIA_GIT_WGLADU = frozenset({
    "status", "log", "diff", "show", "branch", "tag", "remote", "ls-files", "rev-parse",
    "blame", "describe", "shortlog", "config", "cat-file", "grep",
})
# Przełączniki, które z polecenia wglądu robią pracę: `sed -i` zapisuje w miejscu,
# `find -exec`/`-delete` uruchamia cudze polecenia i kasuje pliki.
PRZELACZNIKI_POZA_WGLADEM = {
    "sed": ("-i", "--in-place"),
    "find": ("-exec", "-execdir", "-ok", "-okdir", "-delete"),
}
KOMUNIKAT_TLO_WYMAGANE = (
    "To wywołanie ({fragment}) wykonuje pracę, a w trybie ciągłej pracy praca idzie "
    "w tle - na pierwszym planie zostaje wyłącznie wgląd, który wraca natychmiast "
    "(`ls`, `cat`, `head`, `tail -n`, `grep`, `find`, `wc`, `stat`, `sed -n`, `diff`, "
    "`git status|log|diff|show`, `echo`, `pwd`). Powód: dopóki wywołanie trwa, nie "
    "odpala się żaden hook i użytkownik nie ma jak się do Ciebie odezwać, a "
    "zadeklarowany limit czasu tego nie zmienia - mówi tylko, kiedy polecenie zostanie "
    "przerwane. Uruchom to samo w tle: `run_in_background` narzędzia Bash albo "
    "`nohup <polecenie> > <plik-logu> 2>&1 &`, pracuj dalej nad kolejną częścią "
    "zlecenia, a wynik odbierz krótkim wywołaniem (`BashOutput` z `block: false`, "
    "`tail -n 20 <plik-logu>`). Nic nie przerywaj i niczego nie zabijaj."
)
# Zamiana podstawień poleceń i separatorów na jeden separator segmentów: `$(...)`,
# odwrotne apostrofy i `<(...)` uruchamiają własne polecenia, więc ich zawartość musi
# przejść tę samą kontrolę co reszta.
_OTWARCIA_PODSTAWIEN = re.compile(r"\$\(|<\(|>\(|`|\)|\{|\}|\(")
_SEPARATORY_SEGMENTOW = re.compile(r"\|\||&&|[;|\n&]")
# Słowa kluczowe powłoki na pozycji polecenia: rozgałęzienia i pętle nie są wglądem,
# bo ich treść może uruchomić dowolną pracę.
_SLOWA_KLUCZOWE_POWLOKI = frozenset({
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done", "case",
    "esac", "function", "select", "time", "exec", "eval", "source", ".",
})
_PRZYPISANIE_ZMIENNEJ = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PRZYPISANIE_ZMIENNEJ_TOKEN = _PRZYPISANIE_ZMIENNEJ
_ARGUMENT_CZASU = re.compile(r"^\d+(?:\.\d+)?[smhd]?$")
_PREFIKSY_URUCHOMIENIA = frozenset({"env", "nice", "ionice", "stdbuf", "nohup", "command",
                                    "time", "timeout", "setsid", "unbuffer"})
_OPCJE_GIT_Z_ARGUMENTEM = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                                     "--exec-path"})


def _segmenty_polecenia(tresc: str) -> list[list[str]]:
    """Polecenie rozbite na segmenty (potok, `;`, `&&`, podstawienie) w postaci list
    tokenów. Komentarze i przekierowania są pomijane - o tym, czy segment jest wglądem,
    decyduje nazwa polecenia i jego przełączniki."""
    bez_komentarza = re.sub(r"#[^\n]*", " ", tresc)
    ujednolicone = _OTWARCIA_PODSTAWIEN.sub(";", bez_komentarza)
    segmenty = []
    for fragment in _SEPARATORY_SEGMENTOW.split(ujednolicone):
        tokeny = [token for token in fragment.split() if token]
        if tokeny:
            segmenty.append(tokeny)
    return segmenty


# Wgląd, który potrafi nie wrócić: polecenie z listy wraca natychmiast tylko wtedy, gdy
# ma co czytać i wie, gdzie skończyć. `cat` bez pliku czeka na standardowe wejście,
# a `find /` chodzi po całym dysku.
_POLECENIA_ZE_STANDARDOWEGO_WEJSCIA = frozenset({
    "cat", "sort", "head", "tail", "wc", "nl", "tac", "cut", "tr", "jq", "uniq",
})
_POLECENIA_WZORCA = frozenset({"grep", "egrep", "fgrep", "sed"})
_POLECENIA_PRZESZUKUJACE = frozenset({"find", "grep", "egrep", "fgrep", "rg", "du", "tree"})
_PRZELACZNIKI_REKURENCJI = frozenset({"-r", "-R", "--recursive", "-rn", "-rl", "-ri", "-rni"})
_KORZEN_SYSTEMOWY = re.compile(
    r"^(?:/|~|\$HOME)$|^/(?:home|Users|var|usr|etc|opt|proc|sys|mnt|media|Volumes)(?:/[^/]*)?$"
    r"|^~/?$",
)
_URZADZENIE_BLOKUJACE = re.compile(r"^/dev/(?!null$|stdout$|stderr$)")


def _wglad_wraca_natychmiast(polecenie: str, argumenty: list[str], pierwszy: bool) -> bool:
    """Czy polecenie wglądu ma z czego czytać i gdzie skończyć."""
    cele = [a.strip("\"'") for a in argumenty if not a.startswith("-")]
    if any(_URZADZENIE_BLOKUJACE.match(cel) for cel in cele):
        return False
    if pierwszy and polecenie in _POLECENIA_ZE_STANDARDOWEGO_WEJSCIA and not cele:
        return False
    if pierwszy and polecenie in _POLECENIA_WZORCA and len(cele) < 2:
        return False
    if polecenie in _POLECENIA_PRZESZUKUJACE:
        rekurencja = polecenie in ("find", "rg", "du", "tree") or any(
            a in _PRZELACZNIKI_REKURENCJI for a in argumenty)
        if rekurencja and any(_KORZEN_SYSTEMOWY.match(cel) for cel in cele):
            return False
    return True


def _segment_jest_wgladem(tokeny: list[str], powloka: str = "Bash",
                          pierwszy: bool = True) -> bool:
    pozycja = 0
    while pozycja < len(tokeny) and _PRZYPISANIE_ZMIENNEJ.match(tokeny[pozycja]):
        pozycja += 1
    if pozycja >= len(tokeny):
        return True
    # Prefiksy uruchamiające cudze polecenie: liczy się to, co po nich stoi. `env`
    # był na liście wglądu, więc `env ./budowanie.sh` przechodził jako odczyt.
    while pozycja < len(tokeny) and tokeny[pozycja].strip('"\'').rsplit("/", 1)[-1] in _PREFIKSY_URUCHOMIENIA:
        pozycja += 1
        while pozycja < len(tokeny) and (_PRZYPISANIE_ZMIENNEJ_TOKEN.match(tokeny[pozycja])
                                         or tokeny[pozycja].startswith("-")
                                         or _ARGUMENT_CZASU.match(tokeny[pozycja])):
            pozycja += 1
    if pozycja >= len(tokeny):
        return False
    polecenie = tokeny[pozycja].strip('"\'')
    polecenie = polecenie.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if powloka == "PowerShell":
        return polecenie.lower() in POLECENIA_WGLADU_POWERSHELL
    if polecenie in _SLOWA_KLUCZOWE_POWLOKI:
        return False
    if polecenie not in POLECENIA_WGLADU:
        return False
    argumenty = tokeny[pozycja + 1:]
    for przelacznik in PRZELACZNIKI_POZA_WGLADEM.get(polecenie, ()):  # sed -i, find -exec
        if any(argument == przelacznik or argument.startswith(przelacznik) for argument in argumenty):
            return False
    if polecenie == "git":
        # Opcje globalne `git` biorą argument (`-C <kat>`, `-c <klucz=wartość>`), więc
        # pierwszy token bez myślnika bywa wartością opcji, nie podpoleceniem:
        # `git -C /repo status` był klasyfikowany jako praca i blokowany.
        podpolecenia = []
        pomin = False
        for argument in argumenty:
            if pomin:
                pomin = False
                continue
            if argument in _OPCJE_GIT_Z_ARGUMENTEM:
                pomin = True
                continue
            if argument.startswith("-"):
                continue
            podpolecenia.append(argument)
        if not podpolecenia or podpolecenia[0] not in PODPOLECENIA_GIT_WGLADU:
            return False
    return _wglad_wraca_natychmiast(polecenie, argumenty, pierwszy)


def wylacznie_wglad(tresc: str, powloka: str = "Bash") -> bool:
    """Czy całe polecenie jest odczytem stanu, który wraca natychmiast."""
    segmenty = _segmenty_polecenia(tresc)
    return bool(segmenty) and all(
        _segment_jest_wgladem(s, powloka, pierwszy=(numer == 0))
        for numer, s in enumerate(segmenty))


# Lista przepustek: narzędzia kończące się od razu, które nie odcinają użytkownika.
# Matcher PreToolUse obejmuje wszystkie narzędzia, więc rozstrzygnięcie „to przechodzi
# bez sprawdzania" należy do tej listy.
NARZEDZIA_PRZEPUSTKI = {
    "Read", "Glob", "Grep", "TodoWrite", "ToolSearch",
    "Skill", "NotebookRead", "ListMcpResources", "ReadMcpResource",
}
# Narzędzia odbioru wyniku zadania tłowego. `block` ma domyślnie `true`, a `timeout`
# domyślnie 30 s - wywołanie bez tych pól CZEKA na zakończenie zadania i przez ten czas
# odcina użytkownika. Przechodzi więc wyłącznie wariant natychmiastowy.
NARZEDZIA_ODBIORU_WYNIKU = {
    "TaskOutput", "BashOutput", "AgentOutputTool", "BashOutputTool", "TaskGet",
}
POLE_BLOKOWANIA_ODBIORU = "block"
# Ile sekund wolno czekać na wynik zadania tłowego w jednym wywołaniu odbioru.
LIMIT_ODBIORU_WYNIKU_S = 5
# Narzędzia, których nazwa zapowiada czekanie. Limit czasu ich nie ratuje - czekanie
# jest ich jedyną funkcją.
NARZEDZIA_OCZEKIWANIA = re.compile(r".*(wait|sleep|poll|await|idle_until).*", re.I)
# Pola, którymi wywołanie deklaruje własny limit czasu. Wartości poniżej progu
# milisekundowego liczymy jako sekundy, powyżej - jako milisekundy.
POLA_LIMITU_CZASU = ("timeout", "timeout_ms", "timeoutMs", "max_duration", "deadline_s")
PROG_MILISEKUND = 1000
NAZWA_DZIENNIKA_CISZY = "dziennik-ciszy.jsonl"
LIMIT_WPISOW_DZIENNIKA_CISZY = 1000


def limit_wywolania_s(wejscie: dict) -> float | None:
    """Limit czasu zadeklarowany w wywołaniu narzędzia albo None, gdy nie ma żadnego
    pola limitu."""
    for pole in POLA_LIMITU_CZASU:
        wartosc = wejscie.get(pole)
        if isinstance(wartosc, bool) or not isinstance(wartosc, (int, float)):
            continue
        wartosc = float(wartosc)
        if pole.lower().endswith(("_ms", "ms")) or wartosc > PROG_MILISEKUND:
            return wartosc / 1000
        return wartosc
    return None


def deklaruje_limit(wejscie: dict) -> bool:
    return any(pole in wejscie for pole in POLA_LIMITU_CZASU)


def zapisz_dziennik_ciszy(katalog, narzedzie: str, powod: str) -> None:
    """Dopisuje wpis o wywołaniu, które mogło odciąć użytkownika, a nie dało się go
    ocenić. Dziennik jest wyłącznie informacyjny - niczego nie blokuje."""
    try:
        sciezka = katalog / NAZWA_DZIENNIKA_CISZY
        wpis = json.dumps({"czas": znacznik.teraz(), "narzedzie": narzedzie,
                           "powod": powod}, ensure_ascii=False)
        with open(sciezka, "a", encoding="utf-8") as plik:
            plik.write(wpis + "\n")
        _przytnij_dziennik_ciszy(sciezka)
    except (OSError, ValueError, TypeError):
        pass


def _przytnij_dziennik_ciszy(sciezka) -> None:
    try:
        with open(sciezka, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except OSError:
        return
    if len(linie) <= LIMIT_WPISOW_DZIENNIKA_CISZY:
        return
    try:
        znacznik.zapisz_atomowo(sciezka, "".join(linie[-LIMIT_WPISOW_DZIENNIKA_CISZY:]))
    except OSError:
        pass


KOMUNIKAT_OCZEKIWANIE = (
    "Narzędzie {narzedzie} jest zablokowane w trybie ciągłej pracy: jego jedyną funkcją "
    "jest czekanie, a w czasie trwania wywołania nie odpala się żaden hook i użytkownik "
    "nie ma jak się odezwać. Zamiast czekać, wykonaj następny krok zlecenia i sprawdź "
    "stan krótkim wywołaniem później."
)

KOMUNIKAT_ODBIOR_BLOKUJACY = (
    "Wywołanie {narzedzie} czeka na zakończenie zadania tłowego (pole `block` domyślnie "
    "`true`, limit domyślnie 30 s, maksymalnie 600 s). Nie czekaj na zadanie tłowe; wróć "
    "do innej części zlecenia, a wynik sprawdź krótkim wywołaniem, gdy będzie gotowy: "
    "podaj `block: false` albo `timeout` najwyżej {prog} s."
)

KOMUNIKAT_OCZEKIWANIE_POWLOKI = (
    "Polecenie ({fragment}) czeka na zakończenie zadania tłowego na pierwszym planie, a "
    "przez ten czas nie odpala się żaden hook i użytkownik nie ma jak się do Ciebie "
    "odezwać. Nie czekaj na zadanie tłowe; wróć do innej części zlecenia, a wynik sprawdź "
    "krótkim wywołaniem, gdy będzie gotowy (`BashOutput` z `block: false`, `tail -n 20 "
    "<plik-logu>`). Procesu nie przerywaj i nie zabijaj."
)

KOMUNIKAT_LIMIT_POLECENIA = (
    "To wywołanie deklaruje limit czasu {limit:.0f} s, czyli powyżej progu pierwszego "
    "planu ({prog:.0f} s). Dopóki ono trwa, nie odpala się żaden hook i użytkownik nie ma "
    "jak się do Ciebie odezwać - widzi wyłącznie „running tools\". Proces ma działać "
    "dalej; masz tylko przestać na niego czekać. Uruchom to samo w tle (`run_in_background` "
    "narzędzia Bash albo `nohup <polecenie> > <plik-logu> 2>&1 &`) i pracuj dalej, a wynik "
    "odbierz krótkim wywołaniem (`BashOutput` z `block: false`, `tail -n 20 <plik-logu>`). "
    "Nic nie przerywaj i niczego nie zabijaj."
)

KOMUNIKAT_LIMIT_NARZEDZIA = (
    "Wywołanie {narzedzie} deklaruje limit czasu {limit:.0f} s, czyli powyżej progu "
    "pierwszego planu ({prog} s). Dopóki ono trwa, użytkownik nie ma jak się do Ciebie "
    "odezwać. Uruchom to w tle albo zejdź z limitem poniżej progu i sprawdzaj wynik "
    "krótkimi wywołaniami."
)

# `sleep` na pierwszym planie jest przerwą, nie pracą. Próg jest krótki z rozmysłem:
# `sleep 2` między dwiema próbami to normalna praca, `sleep 90` przed odczytem logu to
# czekanie. Próg pierwszego planu dotyczy poleceń, które COŚ robią - tu byłby za wysoki.
PROG_SLEEP_PIERWSZEGO_PLANU_S = 5
_SLEEP_Z_CZASEM = re.compile(r"(?:^|[;&|]\s*)sleep\s+(\d+(?:\.\d+)?)([smhd]?)(?![\w])", re.I)
_MNOZNIKI_CZASU = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}


def _sleep_ponad_prog(tresc: str) -> str | None:
    """Odliczanie ponad próg - pojedyncze albo w sumie. Tło go nie usprawiedliwia:
    `sleep 100` wszyty w polecenie sprawdzające zamienia zadanie tłowe w minutnik."""
    razem = 0.0
    for dopasowanie in _SLEEP_Z_CZASEM.finditer(tresc):
        sekundy = float(dopasowanie.group(1)) * _MNOZNIKI_CZASU[dopasowanie.group(2).lower()]
        if sekundy > PROG_SLEEP_PIERWSZEGO_PLANU_S:
            return dopasowanie.group(0).strip()
        razem += sekundy
    if razem > PROG_SLEEP_PIERWSZEGO_PLANU_S:
        return f"sleep łącznie {razem:.0f} s"
    return None
_PREFIKS_TIMEOUT = re.compile(r"^\s*timeout\s+(?:-\S+\s+)*(\d+(?:\.\d+)?)([smh]?)(?![\w])", re.I)


def _zadeklarowany_limit_s(tresc: str, wejscie: dict, powloka: bool = True) -> float | None:
    """Limit czasu zadeklarowany w wywołaniu: pole `timeout` narzędzia (sekundy albo
    milisekundy) albo prefiks `timeout N` w poleceniu."""
    dopasowanie = _PREFIKS_TIMEOUT.search(tresc)
    if dopasowanie:
        mnoznik = {"": 1, "s": 1, "m": 60, "h": 3600}[dopasowanie.group(2).lower()]
        return float(dopasowanie.group(1)) * mnoznik
    wartosc = wejscie.get("timeout")
    if isinstance(wartosc, bool) or not isinstance(wartosc, (int, float)):
        return None
    # Narzędzie powłoki klienta podaje `timeout` w MILISEKUNDACH. Czytanie tego pola
    # jako sekund odrzucało `timeout: 1000` (jedna sekunda) jako limit tysiąca sekund.
    if powloka:
        return float(wartosc) / 1000
    return float(wartosc) / 1000 if wartosc > PROG_MILISEKUND else float(wartosc)
# Czekanie przeniesione w tło. Tło jest miejscem na PRACĘ, nie na czekanie: zadanie
# tłowe, którego całą treścią jest `sleep` albo pętla odpytująca, niczego nie liczy -
# daje tylko pozór zajętości, bo w interfejsie widać „running task", a zlecenie stoi.
# Model zamieniał w ten sposób zakaz czekania na pierwszym planie na zadanie tłowe
# o nazwie „Wait for the dump to finish" i znikał na kilkanaście minut.
_POLECENIA_CZEKANIA = frozenset({"sleep", "wait", "true", ":"})
# Treść, która odpytuje albo odlicza - sprawdzana razem z opisem wywołania.
_ODPYTYWANIE_W_TRESCI = re.compile(
    r"\bsleep\s+\d|(?<![\w-])wait(?![\w-])|\bpgrep\b|\bpidof\b|\btest\s+-[ef]\b"
    r"|\[\s*-[ef]\s|\buntil\b|\bwhile\b|\bseq\b",
    re.I,
)
# Opis wywołania zapowiadający czekanie. Sam opis niczego nie przesądza - liczy się
# dopiero razem z odpytywaniem w treści polecenia.
_OPIS_CZEKANIA = re.compile(
    r"(?<![\w-])(wait|waiting|await|poll|polling|czeka|czekaj|czekam|oczekiw|dopóki|aż\s)",
    re.I,
)
POLA_OPISU_WYWOLANIA = ("description", "name", "title", "label")
KOMUNIKAT_CZEKANIE_W_TLE = (
    "To wywołanie nie wykonuje pracy - czeka ({powod}). Tło jest miejscem na pracę, nie "
    "na czekanie: zadanie tłowe, które wyłącznie odlicza albo odpytuje, niczego nie "
    "liczy, a w interfejsie wygląda jak zajętość - użytkownik widzi „running task\", "
    "za którym nie stoi żadna praca. Proces, na który czekasz, już działa i nikt go nie "
    "przerywa. Wróć do zlecenia i wykonaj następną niezależną część, a stan sprawdź "
    "jednym krótkim wywołaniem, gdy ta część będzie gotowa."
)


def _polecenie_tylko_czeka(tresc: str) -> bool:
    """Czy całe polecenie sprowadza się do odliczania albo czekania na cudzy proces."""
    segmenty = _segmenty_polecenia(tresc)
    if not segmenty:
        return False
    for tokeny in segmenty:
        tokeny = [token for token in tokeny if token]
        while tokeny and (_nazwa_polecenia(tokeny[0]) in _PREFIKSY_URUCHOMIENIA
                          or _PRZYPISANIE_ZMIENNEJ.match(tokeny[0])):
            tokeny = tokeny[1:]
        if not tokeny or _nazwa_polecenia(tokeny[0]) not in _POLECENIA_CZEKANIA:
            return False
    return True


def powod_czekania(tresc: str, wejscie: dict) -> str | None:
    """Powód odrzucenia wywołania, którego jedyną treścią jest czekanie - także w tle."""
    if _polecenie_tylko_czeka(tresc):
        return "całą treścią polecenia jest odliczanie czasu"
    opisy = " ".join(str(wejscie.get(pole, "")) for pole in POLA_OPISU_WYWOLANIA)
    if _OPIS_CZEKANIA.search(opisy) and _ODPYTYWANIE_W_TRESCI.search(tresc):
        return "opis wywołania zapowiada czekanie, a polecenie odpytuje stan w pętli"
    return None


KOMUNIKAT_PIERWSZY_PLAN = (
    "To wywołanie ({fragment}) czeka na wynik na pierwszym planie, a w trybie ciągłej "
    "pracy jest to jedyna rzecz zakazana: dopóki ono trwa, nie odpala się żaden hook, "
    "więc użytkownik nie ma jak się do Ciebie odezwać. Proces ma działać - masz tylko "
    "przestać na niego czekać. Uruchom to samo w tle: parametrem `run_in_background` "
    "narzędzia Bash albo jako `nohup <polecenie> > <plik-logu> 2>&1 &`, a potem pracuj "
    "dalej i zaglądaj do wyniku krótkimi wywołaniami (`BashOutput`, `tail -n 20 "
    "<plik-logu>`). Nic nie przerywaj i niczego nie zabijaj."
)
# Pola, którymi klient oznacza uruchomienie w tle. Nazwa bywa różna w kolejnych wersjach,
# więc rozpoznajemy rodzinę nazw zamiast jednej sztywnej.
POLE_PRACY_W_TLE_KLIENTA = "run_in_background"
# Nazwy zapasowe na wypadek zmiany nazwy pola. Nie są dowodem, że klient w ogóle ma
# wariant tłowy.
POLA_PRACY_W_TLE_ZAPAS = ("background", "is_background", "run_in_bg", "async", "detached")
POLA_PRACY_W_TLE = (POLE_PRACY_W_TLE_KLIENTA,) + POLA_PRACY_W_TLE_ZAPAS


def uruchomione_w_tle(wejscie: dict) -> bool:
    return any(bool(wejscie.get(pole)) for pole in POLA_PRACY_W_TLE)


# `&` liczy się jako tło tylko na końcu polecenia albo segmentu: `npm run build && npm
# test` zawiera " &", a jest pracą na pierwszym planie. `nohup` musi stać na pozycji
# polecenia.
_AMPERSAND_NA_KONCU = re.compile(r"&\s*(?:$|[;\n])")
_NOHUP_NA_POZYCJI_POLECENIA = re.compile(r"(?:^|[;&|]\s*|\b(?:then|do|else)\s+)nohup\b")


_SEGMENT_TLOWY = re.compile(r"[^&\n]*(?<!&)&(?!&)")


def _czesc_pierwszoplanowa(tresc: str) -> str:
    """Polecenie po usunięciu segmentów zakończonych `&`. Segment puszczony w tło nie
    zatrzymuje tury; zatrzymuje ją to, co zostaje na pierwszym planie."""
    bez_komentarza = re.sub(r"#[^\n]*", " ", tresc)
    return "\n".join(_SEGMENT_TLOWY.sub(" ", linia) for linia in bez_komentarza.split("\n"))


def polecenie_w_tle(tresc: str) -> bool:
    bez_komentarza = re.sub(r"#[^\n]*", "", tresc)
    if _AMPERSAND_NA_KONCU.search(bez_komentarza.replace("&&", "  ")):
        return True
    return _NOHUP_NA_POZYCJI_POLECENIA.search(bez_komentarza) is not None


def diagnostyka(tekst: str) -> None:
    """Notatka do stderr przy kodzie 0 — Claude Code zapisuje ją tylko w logu debug."""
    print(f"[straznik] {tekst}", file=sys.stderr)


def blokuj(komunikat: str) -> int:
    print(komunikat, file=sys.stderr)
    return KOD_BLOKUJ


def wczytaj_zdarzenie() -> tuple[dict | None, str | None]:
    """JSON zdarzenia ze stdin. Zwraca (zdarzenie, powód_błędu)."""
    try:
        surowe = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    except (OSError, ValueError) as blad:
        return None, f"nie udało się odczytać stdin: {blad}"
    if not surowe.strip():
        return None, "puste wejście zamiast JSON zdarzenia"
    try:
        zdarzenie = json.loads(surowe)
    except ValueError as blad:
        return None, f"uszkodzony JSON zdarzenia: {blad}"
    if not isinstance(zdarzenie, dict):
        return None, "JSON zdarzenia nie jest obiektem"
    return zdarzenie, None


def sesja_ze_zdarzenia(zdarzenie: dict | None) -> str:
    if not zdarzenie:
        return ""
    wartosc = zdarzenie.get("session_id")
    return wartosc.strip() if isinstance(wartosc, str) else ""


def transkrypcja_ze_zdarzenia(zdarzenie: dict | None) -> str | None:
    if not zdarzenie:
        return None
    sciezka = zdarzenie.get("transcript_path")
    return sciezka if isinstance(sciezka, str) and sciezka.strip() else None


def cwd_ze_zdarzenia(zdarzenie: dict | None) -> str | None:
    if zdarzenie is None:
        return None
    cwd = zdarzenie.get("cwd")
    return cwd if isinstance(cwd, str) and cwd.strip() else None


# --- Stop

_NAZWY_TAGOW_SYSTEMOWYCH = (
    r"system-reminder|important-info|local-command-[a-z]+|command-[a-z]+|[a-z-]+-hook"
    r"|[a-z-]+-reminder|[a-z-]+-instructions"
)
_TAGI_SYSTEMOWE = re.compile(rf"<({_NAZWY_TAGOW_SYSTEMOWYCH})(\s[^>]*)?>.*?</\1\s*>", re.S | re.I)
# Tag otwarty bez domknięcia: reszty wpisu nie da się przypisać człowiekowi, więc
# nie liczy się jako jego tekst. Brak dopasowania musi znaczyć „blokada zostaje”,
# nie „polecenie uznane” - to jedyne miejsce mechanizmu, gdzie pomyłka zwalnia blokadę.
_TAG_SYSTEMOWY_OTWARTY = re.compile(
    rf"(?:\A|(?<=\n))[^\S\n]*<({_NAZWY_TAGOW_SYSTEMOWYCH})(\s[^>]*)?>.*\Z", re.S | re.I)


def _bez_blokow_systemowych(tekst: str) -> str:
    return _TAG_SYSTEMOWY_OTWARTY.sub(" ", _TAGI_SYSTEMOWE.sub(" ", tekst))


def _teksty_uzytkownika(wpis: dict) -> list[str]:
    """Tekst faktycznie napisany przez człowieka w jednym wpisie transkrypcji.

    Pomija wpisy niebędące wiadomością `user`, wpisy meta, streszczenia po
    kompaktowaniu, wątki subagentów, wyniki narzędzi i bloki systemowe."""
    if wpis.get("type") not in (None, "user"):
        return []
    if wpis.get("isMeta") or wpis.get("isCompactSummary") or wpis.get("isSidechain"):
        return []
    if "toolUseResult" in wpis:
        return []
    if "wakeupSource" in wpis or str(wpis.get("promptSource") or "") in ZRODLA_MASZYNOWE:
        return []
    pochodzenie = wpis.get("origin")
    if pochodzenie is not None:
        if not isinstance(pochodzenie, dict) or pochodzenie.get("kind") not in POCHODZENIA_LUDZKIE:
            return []
    wiadomosc = wpis.get("message")
    if not isinstance(wiadomosc, dict) or wiadomosc.get("role") != "user":
        return []
    tresc = wiadomosc.get("content")
    teksty: list[str] = []
    if isinstance(tresc, str):
        teksty.append(tresc)
    elif isinstance(tresc, list):
        for kawalek in tresc:
            if isinstance(kawalek, dict) and kawalek.get("type") == "text":
                teksty.append(str(kawalek.get("text") or ""))
    return [_bez_blokow_systemowych(t) for t in teksty]


def _linie_ogona(sciezka: str, limit_bajtow: int) -> list[str]:
    """Końcowy fragment transkrypcji jako linie: liczą się tylko wpisy późniejsze od
    znacznika, a czytanie megabajtów przy każdej próbie Stop jest zbędne. Pierwsza,
    ucięta w połowie linia ogona jest odrzucana."""
    with open(sciezka, "rb") as plik:
        plik.seek(0, os.SEEK_END)
        rozmiar = plik.tell()
        start = max(0, rozmiar - limit_bajtow)
        plik.seek(start)
        surowe = plik.read()
    if start > 0:
        _, _, surowe = surowe.partition(b"\n")
    return surowe.decode("utf-8", errors="replace").splitlines()


def transkrypcja_zawiera_potwierdzenie(sciezka: str, od_kiedy: datetime | None) -> bool | None:
    """True/False = wynik przeszukania; None = pliku nie dało się przeczytać.

    Liczą się wyłącznie wiadomości wysłane PO założeniu znacznika: wiadomość zlecająca
    pracę może zawierać to polecenie w cytacie. Wpis bez wiarygodnego czasu ze strefą
    nie liczy się (fail-closed)."""
    if od_kiedy is None:
        return False
    try:
        linie = _linie_ogona(sciezka, LIMIT_ODCZYTU_TRANSKRYPCJI_B)
    except OSError:
        return None
    for surowa in linie:
        linia = surowa.strip()
        if not linia:
            continue
        try:
            wpis = json.loads(linia)
        except ValueError:
            continue
        if not isinstance(wpis, dict):
            continue
        teksty = _teksty_uzytkownika(wpis)
        if not teksty:
            continue
        czas = znacznik.parsuj_czas(wpis.get("timestamp"), wymagaj_strefy=True)
        if czas is None or czas < od_kiedy:
            continue
        if znacznik.zawiera_polecenie_stop(" ".join(teksty)):
            return True
    return False


def _odnotuj_probe(katalog: Path, dane: dict | None, sesja: str = "") -> None:
    """Licznik blokad jest wyłącznie informacyjny (`zadanie.py status`) — nie
    steruje żadnym zwolnieniem."""
    if not dane:
        return
    try:
        dane["prob"] = int(dane.get("prob", 0)) + 1
        znacznik.zapisz_znacznik(katalog, znacznik.ogranicz_dziennik(dane), sesja)
    except (OSError, ValueError, TypeError):
        pass


def polecenie_stop(zdarzenie: dict | None, blad: str | None) -> int:
    # Zlecenie jest sesyjne: szukamy WYŁĄCZNIE pliku tej rozmowy. Zlecenie innej sesji
    # w tym samym projekcie nie blokuje tu niczego i nie jest tu widoczne.
    sesja = sesja_ze_zdarzenia(zdarzenie)
    katalog = znacznik.znajdz_katalog_znacznika(cwd_ze_zdarzenia(zdarzenie), sesja=sesja)
    if katalog is None:
        return KOD_ZEZWOL

    dane = znacznik.wczytaj_znacznik(katalog, sesja)
    opis = str((dane or {}).get("opis") or "(brak opisu - znacznik nieczytelny)")
    od_kiedy = znacznik.parsuj_czas((dane or {}).get("rozpoczeto"))

    # Termin ważności. Zapomniany znacznik bez terminu blokowałby zakończenie tury
    # w każdej późniejszej sesji otwartej w tym poddrzewie.
    if znacznik.wygasl(dane):
        if znacznik.usun_znacznik(katalog, sesja):
            diagnostyka(
                f"Termin ważności znacznika minął ({(dane or {}).get('wygasa')}) - tryb ciągłej "
                "pracy wygasł sam i został zdjęty. Podsumuj stan zlecenia użytkownikowi."
            )
            return KOD_ZEZWOL
        diagnostyka("znacznik wygasł, ale nie udało się usunąć pliku")

    # Zwolnienie na podstawie transkrypcji: hook Stop nie widzi wpisu użytkownika, więc
    # szuka w niej wiadomości `user` z poleceniem `/stop` wysłanej po założeniu
    # znacznika. Sytuacja, której nie umie ocenić, kończy się blokadą.
    uwaga = ""
    if blad:
        uwaga = f" (uwaga techniczna: {blad})"
    else:
        sciezka = zdarzenie.get("transcript_path") if zdarzenie else None
        if not isinstance(sciezka, str) or not sciezka.strip():
            uwaga = " (uwaga techniczna: klient nie przekazał hookowi transcript_path - zwolnienie nastąpi przez wiadomość użytkownika)"
        else:
            sciezka = os.path.expanduser(sciezka.strip())
            if not os.path.isfile(sciezka):
                uwaga = " (uwaga techniczna: transcript_path nie wskazuje istniejącego pliku)"
            else:
                wynik = transkrypcja_zawiera_potwierdzenie(sciezka, od_kiedy)
                if wynik is None:
                    uwaga = " (uwaga techniczna: nie udało się odczytać pliku transkrypcji)"
                elif wynik:
                    if znacznik.usun_znacznik(katalog, sesja):
                        return KOD_ZEZWOL
                    uwaga = " (uwaga techniczna: nie udało się usunąć pliku znacznika)"

    _odnotuj_probe(katalog, dane, sesja)
    return blokuj(KOMUNIKAT_STOP.format(opis=opis, katalog=katalog, uwaga=uwaga))


# --- UserPromptSubmit

def obsluz_polecenia_blokady(zdarzenie: dict | None) -> bool:
    """Włącza albo wyłącza blokadę podagentów na polecenie użytkownika. Działa
    niezależnie od trybu ciągłej pracy. True, gdy polecenie obsłużono."""
    if not zdarzenie:
        return False
    tresc = zdarzenie.get("prompt")
    if not isinstance(tresc, str):
        return False
    zrodlo = zdarzenie.get("source")
    if not (zrodlo is None or (isinstance(zrodlo, str) and zrodlo in ZRODLA_LUDZKIE)):
        return False

    katalog = znacznik.katalog_blokady(cwd_ze_zdarzenia(zdarzenie))
    sesja = sesja_ze_zdarzenia(zdarzenie)
    if znacznik.zawiera_polecenie_blokada_stop(tresc):
        # Blokadę zdejmuje ta sama sesja, która ją założyła: wpis w obcej rozmowie
        # zwalniał dotąd cudzą blokadę podagentów.
        istniejaca = znacznik.wczytaj_blokade(katalog)
        wlasciciel = str((istniejaca or {}).get("sesjaId") or "")
        if istniejaca is not None and wlasciciel and sesja and wlasciciel != sesja:
            print("Blokada podagentów należy do innej sesji - zdejmie ją polecenie "
                  "użytkownika w tamtej rozmowie.")
            return True
        znacznik.wylacz_blokade(katalog)
        print("Blokada podagentów zdjęta poleceniem użytkownika. Możesz znowu zlecać "
              "pracę podagentom.")
        return True
    if znacznik.zawiera_polecenie_blokady(tresc):
        wygasa = znacznik.wlacz_blokade(katalog, sesja)
        print(
            "Blokada podagentów WŁĄCZONA przez użytkownika (do "
            f"{wygasa}, najwyżej 12 godzin, albo do polecenia /blokada-stop). Do tego "
            "czasu pracujesz wyłącznie samodzielnie: narzędzia podagentów i workflow są "
            "odrzucane, także uruchamiane w tle. Nie proponuj ich i nie proś o zdjęcie "
            "blokady."
        )
        return True
    return False


def obsluz_polecenia_skryptow(zdarzenie: dict | None) -> bool:
    """Zakłada albo zdejmuje blokadę pracy maszynowej na polecenie użytkownika; działa
    niezależnie od zlecenia i od blokady podagentów. True, gdy polecenie obsłużono."""
    if not zdarzenie:
        return False
    tresc = zdarzenie.get("prompt")
    if not isinstance(tresc, str):
        return False
    zrodlo = zdarzenie.get("source")
    if not (zrodlo is None or (isinstance(zrodlo, str) and zrodlo in ZRODLA_LUDZKIE)):
        return False

    katalog = znacznik.katalog_blokady(cwd_ze_zdarzenia(zdarzenie))
    sesja = sesja_ze_zdarzenia(zdarzenie)
    if znacznik.zawiera_polecenie_zwolnienia_skryptow(tresc):
        istniejaca = znacznik.wczytaj_blokade_skryptow(katalog)
        wlasciciel = str((istniejaca or {}).get("sesjaId") or "")
        if istniejaca is not None and wlasciciel and sesja and wlasciciel != sesja:
            print("Blokada pracy maszynowej należy do innej sesji - zdejmie ją "
                  "polecenie użytkownika w tamtej rozmowie.")
            return True
        znacznik.wylacz_blokade_skryptow(katalog)
        print("Blokada pracy maszynowej ZDJĘTA poleceniem użytkownika. Wolno znowu "
              "podmieniać treść maszynowo - pętlą, `sed -i`, `find -exec`, `xargs` "
              "i zapisem hurtowym do bazy. Rób to ostrożnie: przed każdą taką operacją "
              "sprawdź na jednej pozycji, co dokładnie zmieni.")
        return True
    if znacznik.zawiera_polecenie_blokady_skryptow(tresc):
        try:
            katalog.mkdir(parents=True, exist_ok=True)
            znacznik.wlacz_blokade_skryptow(katalog, sesja)
        except (OSError, ValueError, TypeError) as awaria:
            print(f"Nie udało się założyć blokady pracy maszynowej: {awaria}.",
                  file=sys.stderr)
            return True
        print(
            "Blokada pracy maszynowej WŁĄCZONA przez użytkownika poleceniem "
            "/stop-skrypt (bezterminowo, do polecenia /skrypt). Do tego czasu treść "
            "zmieniasz pojedynczo i pod kontrolą: odrzucane są podmiany w miejscu "
            "(`sed -i`, `perl -i`, `rename`), `find -exec` i `xargs` zmieniające pliki, "
            "pętle powłoki z zapisem, kod w linii i skrypty przepisujące treść w pętli, "
            "zapis hurtowy do bazy danych (UPDATE/DELETE/DROP, import `.sql`) oraz "
            "zamiana wszystkich wystąpień w pliku naraz. Zakaz obowiązuje także w tle. "
            "Nie szukaj obejść i nie proponuj zdjęcia blokady."
        )
        return True
    return False


KOMUNIKAT_WLACZENIA = (
    "TRYB CIĄGŁEJ PRACY WŁĄCZONY przez użytkownika (znacznik założył hook, nie Ty).\n"
    "Katalog zlecenia: {katalog}\n"
    "Zlecenie: {opis}\n"
    "Reguły do końca zlecenia: nie kończysz tury; nie zadajesz pytań ani nie prosisz "
    "o potwierdzenia (przy niejednoznaczności przyjmij założenie i pracuj dalej); nie "
    "czekasz na pierwszym planie - to, co trwa, uruchamiasz w tle i idziesz dalej; "
    "milczysz na czacie - zlecenie ma JEDEN raport, końcowy, więc żadnych zapowiedzi, "
    "raportów cząstkowych ani podsumowań etapów (wywołanie narzędzia po wypowiedzi "
    "dłuższej niż 350 znaków jest odrzucane); zapisy trzymasz w katalogu "
    "zlecenia. Zlecenie zamyka wyłącznie polecenie użytkownika {stop} na czacie albo "
    "termin ważności znacznika ({wygasa}). Nie uruchamiaj `zadanie.py start` - "
    "znacznik już jest."
)

KOMUNIKAT_JUZ_AKTYWNY = (
    "Tryb ciągłej pracy JEST JUŻ AKTYWNY (znacznik: {katalog}, zlecenie: {opis}). "
    "Znacznik zostaje bez zmian - nowa treść wiadomości to doprecyzowanie tego samego "
    "zlecenia, nie nowe. Pracuj dalej: nie kończysz tury, nie pytasz, nie czekasz na "
    "pierwszym planie."
)


def obsluz_polecenie_pracuj(zdarzenie: dict | None) -> bool:
    """Zakłada znacznik zlecenia na polecenie `/pracuj`; True, gdy polecenie obsłużono.

    Każda awaria idzie na stderr - to zdarzenie nie ma prawa zakończyć się wyjątkiem."""
    if not zdarzenie:
        return False
    tresc = zdarzenie.get("prompt")
    if not isinstance(tresc, str):
        return False
    zrodlo = zdarzenie.get("source")
    if not (zrodlo is None or (isinstance(zrodlo, str) and zrodlo in ZRODLA_LUDZKIE)):
        return False
    if not znacznik.zawiera_polecenie_pracuj(tresc):
        return False

    try:
        sesja = sesja_ze_zdarzenia(zdarzenie)
        # Zlecenie tej rozmowy. Zlecenia innych sesji w tym samym projekcie są tu
        # niewidoczne: `/pracuj` w drugiej rozmowie zakłada WŁASNY znacznik, zamiast
        # przejmować cudzy.
        istniejacy = znacznik.znajdz_katalog_znacznika(cwd_ze_zdarzenia(zdarzenie), sesja=sesja)
        if istniejacy is not None:
            dane = znacznik.wczytaj_znacznik(istniejacy, sesja) or {}
            if znacznik.wygasl(dane):
                # Wygasłe zlecenie nie jest aktywne: bez tego komenda kończyła się
                # komunikatem „tryb JEST JUŻ AKTYWNY", a pierwszy hook kasował znacznik
                # jako przeterminowany i tryb w ogóle nie ruszał.
                znacznik.usun_znacznik(istniejacy, sesja)
                dane = None
                istniejacy = None
            elif sesja and dane.get("sesjaId") != sesja:
                # Zlecenie przeniesione z układu sprzed 4.0.0: dopisujemy właściciela.
                dane["sesjaId"] = sesja
                dane["ostatnioWidziano"] = znacznik.teraz()
                znacznik.zapisz_znacznik(istniejacy, dane, sesja)
                znacznik.zapisz_kopie(istniejacy, dane, sesja)
            if istniejacy is not None:
                print(KOMUNIKAT_JUZ_AKTYWNY.format(
                    katalog=istniejacy, opis=dane.get("opis") or "(bez opisu)"))
                return True

        korzen = znacznik.korzen_projektu(cwd_ze_zdarzenia(zdarzenie))
        if znacznik.poza_granica(korzen):
            print(f"Nie zakładam znacznika w {korzen}: znacznik obowiązuje w całym "
                  "poddrzewie, więc w katalogu domowym lub w korzeniu systemu plików "
                  "zablokowałby wszystkie projekty. Otwórz sesję w katalogu projektu i "
                  "powtórz polecenie. Tryb ciągłej pracy NIE jest włączony.")
            return True

        katalog = korzen / znacznik.NAZWA_KATALOGU
        znacznik.posprzataj_wygasle(katalog)
        dane = znacznik.utworz_dane_zlecenia(
            korzen, znacznik.opis_ze_zlecenia(tresc), sesja)
        znacznik.zapisz_kopie(katalog, dane, sesja)
        znacznik.zapisz_znacznik(katalog, dane, sesja)
        znacznik.posprzataj_kopie()
    except (OSError, ValueError, TypeError) as awaria:
        print(f"Nie udało się założyć znacznika zlecenia: {awaria}. Tryb ciągłej pracy "
              "NIE jest włączony - sprawdź `zadanie.py diagnoza`.", file=sys.stderr)
        return True

    print(KOMUNIKAT_WLACZENIA.format(
        katalog=korzen, opis=dane["opis"],
        stop=znacznik.POLECENIE_ZAKONCZENIA, wygasa=dane["wygasa"] or "bezterminowo"))
    return True


def polecenie_prompt(zdarzenie: dict | None, blad: str | None) -> int:
    """Nigdy nie blokuje wiadomości użytkownika. Zdejmuje znacznik, gdy użytkownik
    wpisał polecenie kończące; w przeciwnym razie dokłada krótkie przypomnienie
    o aktywnym trybie (stdout przy kodzie 0 trafia do kontekstu modelu)."""
    # Blokada podagentów obsługiwana jest niezależnie i NIE przerywa dalszej obsługi:
    # wiadomość „/stop i /blokada" musi zadziałać w obie strony.
    if not blad and zdarzenie is not None:
        obsluz_polecenia_blokady(zdarzenie)
        obsluz_polecenia_skryptow(zdarzenie)
        # Włączenie trybu: hook zakłada znacznik SAM, bez udziału modelu.
        if obsluz_polecenie_pracuj(zdarzenie):
            return KOD_ZEZWOL

    sesja = sesja_ze_zdarzenia(zdarzenie)
    katalog = znacznik.znajdz_katalog_znacznika(cwd_ze_zdarzenia(zdarzenie), sesja=sesja)
    if katalog is None:
        return KOD_ZEZWOL
    if _znacznik_wygasl_i_zdjety(katalog, zdarzenie, glosno=True):
        return KOD_ZEZWOL
    if blad or zdarzenie is None:
        diagnostyka(f"UserPromptSubmit pominięte: {blad}")
        return KOD_ZEZWOL
    tresc = zdarzenie.get("prompt")
    if not isinstance(tresc, str):
        diagnostyka("UserPromptSubmit bez pola prompt - pominięte")
        return KOD_ZEZWOL

    dane = znacznik.wczytaj_znacznik(katalog, sesja)
    opis = str((dane or {}).get("opis") or "(brak opisu)")

    zrodlo = zdarzenie.get("source")
    od_czlowieka = zrodlo is None or (isinstance(zrodlo, str) and zrodlo in ZRODLA_LUDZKIE)
    if not od_czlowieka:
        diagnostyka(f"UserPromptSubmit ze źródłem {zrodlo!r} - nie liczy się jako wiadomość użytkownika")

    transkrypcja = transkrypcja_ze_zdarzenia(zdarzenie)
    if od_czlowieka and znacznik.zawiera_polecenie_stop(tresc):
        # Polecenie kończące zdejmuje WYŁĄCZNIE zlecenie tej rozmowy. Zlecenia
        # równoległych sesji w tym samym projekcie zostają nietknięte.
        if not znacznik.mozna_zdjac(dane, sesja, transkrypcja):
            print("Zdarzenie nie ma identyfikatora sesji, a w transkrypcji nie ma tokenu "
                  "tego zlecenia - znacznik zostaje. Zdejmie go polecenie użytkownika w "
                  "sesji, która zlecenie założyła.")
            return KOD_ZEZWOL
        if znacznik.usun_znacznik(katalog, sesja):
            pozostale = len(znacznik.sesje_zlecen(katalog))
            dopisek = (f" W tym projekcie trwa jeszcze {pozostale} zlecenie innych sesji."
                       if pozostale else "")
            podsumowanie = znacznik.podsumowanie_pracy(katalog, sesja)
            print(
                "Użytkownik zakończył zlecenie TEJ rozmowy - blokada trybu ciągłej pracy "
                f"została tu zdjęta.{dopisek} Złóż krótki raport w punktach i zakończ turę."
            )
            if podsumowanie:
                print("Zapis z dziennika pracy (użyj go w raporcie zamiast pamięci):")
                for wiersz in podsumowanie:
                    print(f"  {wiersz}")
        else:
            diagnostyka("polecenie rozpoznane, ale nie udało się usunąć znacznika")
        return KOD_ZEZWOL

    print(
        f"Tryb ciągłej pracy jest aktywny (zlecenie: {opis}). Nie zadawaj pytań, nie "
        "proś o potwierdzenia i nie kończ pracy - po odpowiedzi na tę wiadomość wróć "
        "do realizacji zlecenia."
    )
    return KOD_ZEZWOL


# --- PreToolUse: ścieżki

def _znormalizuj(sciezka: str) -> str:
    """Absolutna, z rozwiązanymi dowiązaniami, z `/` jako separatorem; na Windows
    dodatkowo małe litery (normcase), żeby porównania nie zależały od wielkości."""
    pelna = os.path.abspath(os.path.expanduser(sciezka))
    try:
        pelna = os.path.realpath(pelna)
    except OSError:
        pass
    return os.path.normcase(pelna).replace("\\", "/")


def _korzenie_pluginu() -> list[str]:
    korzenie = [str(KORZEN_PLUGINU)]
    z_srodowiska = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if z_srodowiska:
        korzenie.append(z_srodowiska)
    return [_znormalizuj(k).rstrip("/") for k in korzenie]


def powod_ochrony_sciezki(sciezka: str) -> str | None:
    """Dlaczego zapis do tej ścieżki jest zabroniony przy aktywnym znaczniku — albo None."""
    try:
        pelna = _znormalizuj(sciezka)
    except (OSError, ValueError):
        return "ścieżki nie da się znormalizować"
    segmenty = [s.lower() for s in pelna.split("/")]
    nazwa = segmenty[-1] if segmenty else ""

    if znacznik.NAZWA_KATALOGU in segmenty:
        return "katalog znacznika .danaco"
    if znacznik.NAZWA_KATALOGU_KOPII in segmenty or nazwa.endswith(znacznik.ROZSZERZENIE_NAGROBKA):
        return "kopia znacznika poza katalogiem projektu (.danaco-kopie)"

    for korzen in _korzenie_pluginu():
        if not pelna.startswith(korzen + "/"):
            continue
        wzgledna = pelna[len(korzen) + 1:].lower()
        if any(wzgledna == p.lower() for p in PLIKI_MECHANIZMU):
            return "plik mechanizmu trybu ciągłej pracy w katalogu pluginu"
        if any(wzgledna.startswith(k.lower() + "/") for k in KATALOGI_MECHANIZMU):
            return "katalog hooków albo paczek pluginu"
        # Sam katalog jako cel operacji (`mv <plugin>/scripts /tmp`): pojedyncze pliki
        # w `scripts/` i `.claude-plugin/` chroni lista PLIKI_MECHANIZMU.
        if wzgledna in ("hooks", "scripts", "skills", ".claude-plugin"):
            return "katalog mechanizmu w katalogu pluginu"

    if "projects" in segmenty and ".claude" in segmenty:
        return "plik transkrypcji rozmowy (tam da się podłożyć fałszywe polecenie użytkownika)"
    if ".claude" in segmenty:
        if nazwa in ("settings.json", "settings.local.json") or nazwa.startswith("managed-settings"):
            return "konfiguracja Claude Code (settings) - tam da się wyłączyć hooki lub plugin"
        indeks = segmenty.index(".claude")
        if len(segmenty) > indeks + 1 and segmenty[indeks + 1] == "plugins":
            return "rejestr pluginów Claude Code"
    if nazwa == ".claude.json" or "managed-settings.d" in segmenty or nazwa.startswith("managed-settings"):
        return "konfiguracja Claude Code"
    return None


# Ścieżka w zagnieżdżonym polu wywołania MCP omijała kontrolę pól pierwszego poziomu.
LIMIT_GLEBOKOSCI_WEJSCIA = 6
LIMIT_SPRAWDZANYCH_WARTOSCI = 200
_WYGLADA_NA_SCIEZKE = re.compile(r"^[~/.]?[\w./~$-]{2,300}$")


def _wartosci_tekstowe(wejscie, glebokosc: int = 0) -> list[str]:
    """Wszystkie łańcuchy z wywołania narzędzia, także z list i słowników w środku."""
    if glebokosc > LIMIT_GLEBOKOSCI_WEJSCIA:
        return []
    if isinstance(wejscie, str):
        return [wejscie]
    if isinstance(wejscie, dict):
        wejscie = list(wejscie.values())
    if not isinstance(wejscie, list):
        return []
    wynik: list[str] = []
    for element in wejscie:
        wynik.extend(_wartosci_tekstowe(element, glebokosc + 1))
        if len(wynik) > LIMIT_SPRAWDZANYCH_WARTOSCI:
            break
    return wynik[:LIMIT_SPRAWDZANYCH_WARTOSCI]


def sciezka_chroniona_w_wywolaniu(wejscie: dict) -> tuple[str, str] | None:
    """Para (ścieżka, powód) dla pierwszej chronionej ścieżki w całym wywołaniu."""
    for wartosc in _wartosci_tekstowe(wejscie):
        if "/" not in wartosc or not _WYGLADA_NA_SCIEZKE.match(wartosc.strip()):
            continue
        powod = powod_ochrony_sciezki(wartosc.strip())
        if powod:
            return wartosc.strip(), powod
    return None


def _powod_transkrypcji(sciezka: str, zdarzenie: dict | None) -> str | None:
    """Czy ścieżka wskazuje transkrypcję TEJ rozmowy - jedyny plik, w którym da się
    podłożyć fałszywe polecenie użytkownika."""
    biezaca = transkrypcja_ze_zdarzenia(zdarzenie)
    if not biezaca or not isinstance(sciezka, str):
        return None
    try:
        if _znormalizuj(sciezka) == _znormalizuj(biezaca):
            return "plik transkrypcji tej rozmowy"
    except (OSError, ValueError):
        return None
    return None


def _tresc_zapisu(narzedzie: str, wejscie: dict) -> str:
    """Nowa treść, jaką narzędzie plikowe zapisze (Write/Edit/MultiEdit/NotebookEdit)."""
    czesci: list[str] = []
    for klucz in ("content", "new_string", "new_source"):
        wartosc = wejscie.get(klucz)
        if isinstance(wartosc, str):
            czesci.append(wartosc)
    edycje = wejscie.get("edits")
    if isinstance(edycje, list):
        for edycja in edycje:
            if isinstance(edycja, dict) and isinstance(edycja.get("new_string"), str):
                czesci.append(edycja["new_string"])
    return "\n".join(czesci)


# Kontrola treści dotyczy plików, które da się URUCHOMIĆ albo wczytać jako
# konfigurację. Dokumentacja polecenia wyłącznie OPISUJE - README i CHANGELOG muszą
# móc zacytować `rm -rf .danaco`.
ROZSZERZENIA_WYKONYWALNE = (".sh", ".ps1", ".py", ".bat", ".cmd", ".json", ".yaml",
                            ".yml", ".toml")


def tresc_podlega_kontroli(sciezka: str) -> bool:
    return os.path.splitext(str(sciezka).strip().lower())[1] in ROZSZERZENIA_WYKONYWALNE


def powod_ochrony_tresci(tresc: str, sciezka: str = "") -> str | None:
    """Zapisywana treść, która sama jest narzędziem obejścia: skrypt zmieniający
    `.danaco` albo konfiguracja wyłączająca hooki. Heurystyka jak dla poleceń powłoki,
    ale wyłącznie dla plików skryptowych i konfiguracyjnych."""
    if not tresc or (sciezka and not tresc_podlega_kontroli(sciezka)):
        return None
    if _WZMIANKA_WYLACZANIA_HOOKOW.search(tresc):
        return "treść wyłącza hooki lub pluginy Claude Code"
    # Wzmianka o znaczniku i czasownik destrukcyjny muszą stać w TEJ SAMEJ linii.
    # Warunek liczony na całym pliku blokował zapis każdego dłuższego skryptu, który
    # gdziekolwiek wspomina `.danaco`, a gdzie indziej ma `rm` - w tym testów pluginu.
    for linia in _NIESZKODLIWE_PRZEKIEROWANIA.sub(" ", tresc).split("\n"):
        if _WZMIANKA_ZNACZNIKA.search(linia) and _CZASOWNIKI_DESTRUKCYJNE_DOWOLNE.search(linia):
            return "treść zawiera operację zapisu/usuwania na znaczniku .danaco"
    return None


# --- PreToolUse: polecenia powłoki (heurystyka)

_NIESZKODLIWE_PRZEKIEROWANIA = re.compile(r"(\d*>{1,2}|&>)\s*(/dev/null|&\d|\$null|nul(?![\w]))", re.I)

_CZASOWNIKI_DESTRUKCYJNE_POSIX = re.compile(
    r"""
      (?<![\w./-])(rm|rmdir|unlink|shred|truncate|mv|cp|tee|dd|chmod|chown|chattr|patch|ln|rsync)(?![\w-])
    | (?<![\w./-])(sed|perl)\s+(-\S*\s+)*-[a-zA-Z]*i
    | (?<![\w./-])git\s+(checkout|restore|clean|stash|reset|rm|mv|filter-branch)(?![\w-])
    | >{1,2}
    | \bopen\([^)]*['"][wax]
    | write_text|write_bytes|rmtree|os\.(remove|unlink|rename|replace|rmdir|truncate|chmod)|shutil\.
    | (?<![\w-])(Remove-Item|Move-Item|Copy-Item|Rename-Item|Set-Content|Add-Content|Clear-Content|Out-File|New-Item|Set-ItemProperty|Clear-Item|Set-Acl)(?![\w-])
    | \[(System\.)?IO\.
    """,
    re.I | re.X,
)

# Aliasy PowerShell są dwuliterowe i w Bashu padają jako zwykły tekst argumentu
# (np. wzorzec `grep -n "sc"`), dlatego obowiązują tylko w powłoce PowerShell.
_CZASOWNIKI_DESTRUKCYJNE_PS = re.compile(
    r"""
      (?<![\w./-])(Remove-Item|Move-Item|Copy-Item|Rename-Item|Set-Content|Add-Content
        |Clear-Content|Out-File|New-Item|Set-ItemProperty|Clear-Item|Set-Acl)(?![\w-])
    | (?<![\w./-])(rd|ri|mi|ni|rni|sc|ac|cpi|cli|clc|del|erase|icacls|attrib|takeown)(?![\w-])
    | \[(System\.)?IO\.
    | >{1,2}
    """,
    re.I | re.X,
)

_CZASOWNIKI_DESTRUKCYJNE_DOWOLNE = re.compile(
    rf"{_CZASOWNIKI_DESTRUKCYJNE_POSIX.pattern}|{_CZASOWNIKI_DESTRUKCYJNE_PS.pattern}",
    re.I | re.X,
)

# Nazwa katalogu znacznika, także z symbolem wieloznacznym w środku (`rm -rf .dan*co`
# kasuje znacznik tak samo), oraz katalog kopii poza projektem - `rm -rf ~/.danaco-kopie`
# był drogą do samozwolnienia w dwóch krokach.
_WZMIANKA_ZNACZNIKA = re.compile(
    r"\.danaco-kopie|\.dan[\w*?\[\]!-]{0,6}co(?![\w-])",
    re.I,
)

# Pliki zlecenia (znacznik, stan, blokada, nagrobki). Sama nazwa nie wystarcza:
# `rg zadanie-w-toku` to praca - liczy się dopiero czasownik destrukcyjny w tym
# samym poleceniu.
_WZMIANKA_PLIKOW_ZLECENIA = re.compile(
    r"zadanie[-*?\[\]]*w[-*?\[\]]*toku|blokada-subagentow|blokada-skryptow|stan-zlecenia"
    r"|[/\\]zadania[/\\]|dziennik-ciszy|napomnienie-ciszy"
    r"|\.licznik(?![\w-])|\.nagrobek(?![\w-])",
    re.I,
)

# Luźniejszy wzorzec nazwy znacznika - stosowany tylko w argumentach `find` z
# kasowaniem, gdzie fałszywe trafienie kosztuje mniej niż usunięty znacznik.
_NAZWA_ZNACZNIKA_W_FILTRZE = re.compile(r"anaco|dan[\w*?\[\]!-]{0,6}co|zadanie.{0,3}w.{0,3}toku|klucz", re.I)

_NAZWY_MECHANIZMU = re.compile(
    r"straznik\.(py|sh|ps1)|znacznik\.py|zadanie\.py|pracuj/SKILL",
    re.I,
)

# Gołe `hooks`, `scripts`, `.claude-plugin` to nazwy katalogów spotykane w każdym
# repozytorium - liczą się wyłącznie wtedy, gdy wskazują wnętrze katalogu pluginu.
_KATALOGI_PLUGINU = re.compile(r"(?<![\w./-])(hooks|scripts|\.claude-plugin)(?![\w.-])", re.I)


def _katalog_pluginu_w_poleceniu(polecenie: str) -> bool:
    korzenie = _korzenie_pluginu()
    for dopasowanie in _KATALOGI_PLUGINU.finditer(polecenie):
        try:
            pelna = _znormalizuj(dopasowanie.group(0))
        except (OSError, ValueError):
            continue
        if any(pelna == korzen + "/" + dopasowanie.group(1).lower() or pelna.startswith(korzen + "/")
               for korzen in korzenie):
            return True
    return False

_WZMIANKA_WYLACZANIA_HOOKOW = re.compile(r"disableAllHooks|enabledPlugins|installed_plugins|known_marketplaces", re.I)

_WYWOLANIE_CLI_CLAUDE = re.compile(
    r"(^|[;&|(`\n]\s*|\b(sudo|exec|nohup|command|env|time)\s+(\w+=\S*\s+)*)"
    r"(\S*[\\/])?(claude|claude-code)(\.exe|\.cmd)?(\s|$)"
    r"|npx\s+(-y\s+)?@anthropic-ai/claude-code",
    re.I,
)

_SCIEZKA_KONFIGURACJI = re.compile(
    r"\.claude[\\/]+settings|managed-settings|\.claude\.json(?![\w])|\.claude[\\/]+plugins|plugins[\\/]+cache",
    re.I,
)

# `-1` liczy się tylko jako CEL (wszystkie procesy użytkownika), nie jako numer
# sygnału: `kill -1 <pid>` to zwykłe przeładowanie własnego serwera.
_ZABIJANIE_SESJI = re.compile(
    r"(?<![\w-])(pkill|killall|taskkill|Stop-Process)(?![\w-]).*(?<![\w-])claude(?![\w-])"
    r"|(?<![\w-])kill(?![\w-])[^;&|\n]*(\$PPID|\$\$)"
    r"|(?<![\w-])kill\s+(-[\w]+\s+)?-1\s*(;|&|\||$)",
    re.I | re.S,
)

_ZMIENNE_KORZENIA = re.compile(r"\$\{?env:CLAUDE_PLUGIN_ROOT\}?|\$\{CLAUDE_PLUGIN_ROOT\}|\$CLAUDE_PLUGIN_ROOT|%CLAUDE_PLUGIN_ROOT%", re.I)

_TOKEN = re.compile(r"[^\s\"'`;&|<>()]+")

_CELE_CALEGO_KATALOGU = {
    ".", "./", ".\\", "*", ".*", "./*", "./.*", ".\\*", "..", "../", "~", "~/", "/",
    "$home", "${home}", "$pwd", "${pwd}", "$(pwd)", "`pwd`", "$cwd", "%cd%", "$pwd.path",
    "(get-location)", "(pwd)",
}


def _bez_tekstu_dziennika(polecenie: str) -> str:
    """Usuwa cytowany argument `zadanie.py krok "…"`, żeby prozy z dziennika nie brać
    za czasownik destrukcyjny. Argument ze składnią powłoki zostaje."""
    def _zamien(dopasowanie: re.Match) -> str:
        argument = dopasowanie.group(2)
        if re.search(r"[$`;|&<>\n]", argument):
            return dopasowanie.group(0)
        return dopasowanie.group(1) + '""'
    return re.sub(r'(zadanie\.py"?\s+(?:krok|start)\s+)("[^"]*"|\'[^\']*\')', _zamien, polecenie)


def _sciezki_chronione_w_poleceniu(polecenie: str) -> bool:
    """Czy któryś token wyglądający na ścieżkę wskazuje na plik chroniony."""
    rozwiniete = _ZMIENNE_KORZENIA.sub(str(KORZEN_PLUGINU).replace("\\", "/"), polecenie)
    for token in _TOKEN.findall(rozwiniete):
        if ("/" not in token and "\\" not in token) or token.startswith(("http://", "https://")):
            continue
        if powod_ochrony_sciezki(token):
            return True
    return False


def _tokeny(fragment: str) -> list[str]:
    return [t.strip("\"'") for t in fragment.split()]


def _cel_calego_katalogu(token: str) -> bool:
    t = token.lower()
    return t in _CELE_CALEGO_KATALOGU or t.startswith(".[") or t.startswith("./.[")


def _rm_calego_katalogu(polecenie: str) -> bool:
    for dopasowanie in re.finditer(r"(?<![\w./-])rm\s+([^;&|\n]*)", polecenie, re.I):
        tokeny = _tokeny(dopasowanie.group(1))
        rekurencyjnie = any(
            (t.startswith("-") and not t.startswith("--") and "r" in t.lower())
            or t.lower() in ("--recursive", "-recurse")
            for t in tokeny
        )
        cele = [t for t in tokeny if not t.startswith("-")]
        if rekurencyjnie and any(_cel_calego_katalogu(t) for t in cele):
            return True
    return False


def _powershell_calego_katalogu(polecenie: str) -> bool:
    if re.search(r"(?<![\w-])(Get-ChildItem|gci|ls|dir)(?![\w-])[^|\n]*\|\s*(Remove-Item|ri|rm|del|erase|rd|rmdir)(?![\w-])", polecenie, re.I):
        return True
    for dopasowanie in re.finditer(r"(?<![\w./-])(Remove-Item|ri|del|erase|rd|rmdir)\s+([^;&|\n]*)", polecenie, re.I):
        tokeny = _tokeny(dopasowanie.group(2))
        rekurencyjnie = any(t.lower() in ("-recurse", "-r", "/s", "-rec") for t in tokeny)
        cele = [t for t in tokeny if not t.startswith("-") and not t.startswith("/")]
        if rekurencyjnie and any(_cel_calego_katalogu(t) for t in cele):
            return True
    return False


def _argumenty_find_z_kasowaniem(polecenie: str) -> list[str]:
    wynik = []
    for dopasowanie in re.finditer(r"(?<![\w./-])find\s+([^;&|\n]*)", polecenie, re.I):
        argumenty = dopasowanie.group(1)
        if re.search(r"-delete(?![\w-])|-exec\s+rm(?![\w-])", argumenty, re.I):
            wynik.append(argumenty)
    return wynik


def _find_kasuje_wszystko(polecenie: str) -> bool:
    for argumenty in _argumenty_find_z_kasowaniem(polecenie):
        if not re.search(r"-i?(name|path|regex|wholename)(?![\w-])", argumenty, re.I):
            return True
    return False


_FILTR_NAZWY_FIND = re.compile(r"-i?(?:name|path|wholename)\s+(\"[^\"]*\"|'[^']*'|\S+)", re.I)


def _find_kasuje_znacznik(polecenie: str) -> bool:
    """Kasowanie przez `find` z filtrem nazwy, który mógłby objąć pliki zlecenia —
    także filtrem ogólnym w rodzaju `-name "*.json"`."""
    cele = (znacznik.NAZWA_KATALOGU, znacznik.NAZWA_ZNACZNIKA, znacznik.NAZWA_KLUCZA,
            znacznik.NAZWA_STANU)
    for argumenty in _argumenty_find_z_kasowaniem(polecenie):
        if _NAZWA_ZNACZNIKA_W_FILTRZE.search(argumenty):
            return True
        for wzorzec in _FILTR_NAZWY_FIND.findall(argumenty):
            wzorzec = wzorzec.strip("\"'")
            nazwa = wzorzec.rsplit("/", 1)[-1]
            if _wzorzec_trafia(nazwa, cele):
                return True
    return False


# Wywołanie API mechanizmu wprost z Pythona omija filtr nazw plików: nie pada tu ani
# `.danaco`, ani czasownik destrukcyjny, a efekt jest ten sam co `rm -rf .danaco`.
# Liczy się wyłącznie nazwa funkcji - sam `import znacznik` niczego nie kasuje.
_API_MECHANIZMU = re.compile(
    r"\b(?:usun_znacznik|zapisz_znacznik|wlacz_blokade|wylacz_blokade|zwiaz_z_sesja"
    r"|znajdz_katalog_znacznika|katalog_blokady|zapisz_atomowo|odtworz_znacznik"
    r"|usun_kopie|zapisz_kopie)\b",
    re.IGNORECASE,
)


# Kontekst wykonania Pythona: `-c`, `-m`, czytanie skryptu ze standardowego wejścia
# oraz heredoc. Poza nim nazwy funkcji mechanizmu są zwykłym tekstem (grep, git log).
_KONTEKST_PYTHONA = re.compile(
    r"(?<![\w./-])(python[\d.]*|py)(\.exe)?\s+(-\S+\s+)*(-c|-m|-)(?![\w-])"
    r"|(?<![\w./-])(python[\d.]*|py)(\.exe)?[^\n;|&]*<<-?\s*[\"']?\w+",
    re.I,
)

_DEKODOWANIE_DO_POWLOKI = re.compile(
    r"base64\s+(-d|-D|--decode)[^\n]*\|\s*(sudo\s+)?(sh|bash|zsh|python[\d.]*|py|perl|node)(?![\w-])"
    r"|(?<![\w./-])(sh|bash|python[\d.]*)\s+[^\n]*<<<[^\n]*base64",
    re.I,
)

_PRZYPISANIE_ZMIENNEJ = re.compile(r"(?<![\w./-])([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;|&]*)")

_START_ZLECENIA = re.compile(r"zadanie(?:\.py)?[\"'\s]+start(?![\w-])", re.I)


_CYTOWANIE_LUB_ESCAPE = re.compile(r"""(?<!\\)["']|\\(?=[A-Za-z0-9._/-])""")


def _bez_cytowania(polecenie: str) -> str:
    """Polecenie po zdjęciu cudzysłowów i ukośników odwrotnych rozbijających nazwy."""
    return _CYTOWANIE_LUB_ESCAPE.sub("", polecenie)


def _rozwin_zmienne(polecenie: str) -> str:
    """Podstawia wartości przypisań powłoki w dalszej części polecenia — nazwa
    znacznika składana ze zmiennych (`A=.dana; B=co; rm -rf $A$B`) ma być widoczna."""
    wartosci = {n: w.strip("\"'") for n, w in _PRZYPISANIE_ZMIENNEJ.findall(polecenie)}
    if not wartosci:
        return polecenie
    wynik = polecenie
    for _ in range(2):
        for nazwa, wartosc in wartosci.items():
            wynik = re.sub(rf"\$\{{{nazwa}\}}|\${nazwa}(?![\w])", wartosc.replace("\\", "\\\\"), wynik)
    return wynik


def _wzorzec_trafia(nazwa: str, cele: tuple[str, ...]) -> bool:
    import fnmatch
    if "*" not in nazwa and "?" not in nazwa and "[" not in nazwa:
        return False
    return any(fnmatch.fnmatch(cel, nazwa) for cel in cele)


# Nazwy katalogów, w których leży mechanizm: katalog zlecenia w projekcie, katalog
# kopii poza projektem i plik klucza.
_KATALOGI_MECHANIZMU_NA_DYSKU = (znacznik.NAZWA_KATALOGU, znacznik.NAZWA_KATALOGU_KOPII,
                                 znacznik.NAZWA_KLUCZA)


def _glob_trafia_w_zlecenie(polecenie: str) -> bool:
    """Czy wzorzec wieloznaczny rozwija się do katalogu mechanizmu (`.dana*`, `.d*o`).

    Sprawdzany jest KAŻDY człon ścieżki: w `rm -f .*/zadania/*.json` człon `.*` trafia
    w `.danaco`. Wzorce bez wiodącej kropki zostawiamy `find` - inaczej padałoby
    `rm build/*.json`."""
    for token in re.findall(r"[^\s\"'`;&|<>()]+", polecenie):
        for czlon in token.strip("\"'").split("/"):
            czlon = czlon.strip("\"'")
            if czlon.startswith(".") and _wzorzec_trafia(czlon, _KATALOGI_MECHANIZMU_NA_DYSKU):
                return True
    return False


# Cel operacji pochodzący z podstawienia polecenia `$( )` albo z backticków: wartości
# nie da się rozwinąć statycznie, więc pod nią może stać nazwa katalogu znacznika.
_PODSTAWIENIE_POLECENIA = re.compile(r"\$\(|`")
_KASOWANIE_Z_CELEM = re.compile(
    r"(?<![\w./-])(rm|rmdir|unlink|shred|mv|Remove-Item|Move-Item|rmtree"
    r"|shutil\.rmtree|os\.remove|os\.unlink|os\.rename)(?![\w-])([^;&|\n]*)",
    re.I,
)


# Nazwa pliku zlecenia liczy się dopiero jako CEL operacji: `rg zadanie-w-toku` i
# `echo zadanie-w-toku >> lista.txt` to praca, a nie obejście.
_OPERACJA_Z_CELEM = re.compile(
    r"(?<![\w./-])(?:rm|rmdir|unlink|shred|truncate|mv|cp|dd|chmod|chown|tee|rsync"
    r"|Remove-Item|Move-Item|Copy-Item|Rename-Item|Set-Content|Add-Content|Out-File"
    r"|Clear-Content)(?![\w-])([^;&|\n]*)"
    r"|(?<![\w./-])(?:sed|perl)\s+(?:-\S*\s+)*-[a-zA-Z]*i(?![\w-])([^;&|\n]*)"
    r"|>{1,2}\|?\s*([^\s;|&]+)",
    re.I,
)


def _operacja_na_plikach_zlecenia(polecenie: str) -> bool:
    for dopasowanie in _OPERACJA_Z_CELEM.finditer(polecenie):
        fragment = next((g for g in dopasowanie.groups() if g), "")
        if _WZMIANKA_PLIKOW_ZLECENIA.search(fragment) or _glob_trafia_w_zlecenie(fragment):
            return True
    return False


def _cel_z_podstawienia_polecenia(polecenie: str) -> bool:
    for dopasowanie in _KASOWANIE_Z_CELEM.finditer(polecenie):
        if _PODSTAWIENIE_POLECENIA.search(dopasowanie.group(2)):
            return True
    return False


# Zatrzymywanie własnych biegów tłowych z powłoki. Reguła stoi obok blokady narzędzi
# zatrzymujących - inaczej wystarczyłoby zejść z narzędzia do powłoki.
_ZATRZYMANIE_BIEGU = re.compile(
    r"(?<![\w-])kill(?:all)?\s+(?:-\S+\s+)*%\d+"
    r"|(?<![\w-])(?:pkill|killall|taskkill|Stop-Process)(?![\w-])"
    r"|(?<![\w-])jobs\b[^;&|\n]*\|[^;&|\n]*(?:kill|xargs\s+kill)",
    re.I,
)


def regula_blokady_polecenia(polecenie: str, powloka: str = "Bash",
                             tylko_mechanizm: bool = False) -> str | None:
    """Nazwa dopasowanej reguły heurystycznej albo None, gdy polecenie może przejść."""
    tekst = _rozwin_zmienne(polecenie.strip())
    if not tekst:
        return None
    # Nazwy mechanizmu sprawdzamy DODATKOWO na tekście bez cudzysłowów i `\`-escapes:
    # powłoka i tak je usunie, a bez tego `rm -rf .dan""aco` mijało się z wzorcem.
    # Reszta heurystyk pracuje na tekście oryginalnym - odcytowanie skleja treść
    # argumentów i rodzi fałszywe trafienia.
    tekst_nagi = _bez_cytowania(tekst)
    if not tylko_mechanizm and _START_ZLECENIA.search(tekst):
        return ("próba założenia nowego znacznika przy już aktywnym zleceniu "
                "(tryb ciągłej pracy włącza wyłącznie komenda użytkownika)")
    if _DEKODOWANIE_DO_POWLOKI.search(tekst):
        return "polecenie odkodowywane i podawane wprost do powłoki (base64 | sh)"
    if _WZMIANKA_ZNACZNIKA.search(tekst) or (
            tekst_nagi != tekst and _WZMIANKA_ZNACZNIKA.search(tekst_nagi)):
        return "wzmianka o znaczniku .danaco albo o katalogu kopii .danaco-kopie"
    if _WZMIANKA_WYLACZANIA_HOOKOW.search(tekst):
        return "wyłączanie hooków lub pluginów Claude Code"
    if _WYWOLANIE_CLI_CLAUDE.search(tekst):
        return "wywołanie CLI claude z wnętrza sesji"
    if _ZABIJANIE_SESJI.search(tekst):
        return "zabijanie procesu sesji"
    if not tylko_mechanizm and _ZATRZYMANIE_BIEGU.search(tekst):
        return ("zatrzymywanie pracy uruchomionej w tle (bieg w tle ma dobiec do końca; "
                "poprawiony uruchom obok, zamiast kasować poprzedni)")

    czasowniki = (_CZASOWNIKI_DESTRUKCYJNE_PS if powloka == "PowerShell"
                  else _CZASOWNIKI_DESTRUKCYJNE_POSIX)
    do_analizy = _NIESZKODLIWE_PRZEKIEROWANIA.sub(" ", _bez_tekstu_dziennika(tekst))
    destrukcyjne = bool(czasowniki.search(do_analizy))
    if _operacja_na_plikach_zlecenia(do_analizy):
        return "operacja zapisu/usuwania na plikach zlecenia (znacznik, stan, blokada, kopie)"
    if _cel_z_podstawienia_polecenia(do_analizy):
        return ("cel kasowania lub przenoszenia pochodzi z podstawienia polecenia "
                "$( ) albo backticków - nazwy nie da się sprawdzić przed wykonaniem")
    if destrukcyjne and _glob_trafia_w_zlecenie(do_analizy):
        return "wzorzec wieloznaczny obejmujący katalog zlecenia"
    if destrukcyjne and (_NAZWY_MECHANIZMU.search(do_analizy)
                         or _katalog_pluginu_w_poleceniu(do_analizy)
                         or _sciezki_chronione_w_poleceniu(do_analizy)):
        return "operacja zapisu/usuwania na plikach mechanizmu pluginu lub konfiguracji Claude Code"
    if destrukcyjne and _SCIEZKA_KONFIGURACJI.search(do_analizy):
        return "operacja zapisu/usuwania na konfiguracji Claude Code"
    if _rm_calego_katalogu(do_analizy) or _powershell_calego_katalogu(do_analizy):
        return "rekurencyjne kasowanie całego katalogu roboczego"
    for dopasowanie in re.finditer(r"(?<![\w./-])git\s+clean(?![\w-])([^;&|\n]*)", do_analizy, re.I):
        # `-n`/`--dry-run` niczego nie kasuje, tylko wypisuje listę - to zwykłe
        # rozpoznanie stanu repozytorium, nie droga do skasowania znacznika.
        argumenty = dopasowanie.group(1)
        if re.search(r"--dry-run(?![\w-])|(?<![\w-])-[a-zA-Z]*n[a-zA-Z]*(?![\w-])", argumenty):
            continue
        return "git clean (kasuje pliki nieśledzone, w tym .danaco)"
    if re.search(r"(?<![\w./-])git\s+stash\b[^;&|\n]*(\s-[a-zA-Z]*[ua][a-zA-Z]*(\s|$)|--include-untracked|--all)", do_analizy, re.I):
        return "git stash z plikami nieśledzonymi (zabiera .danaco)"
    if _KONTEKST_PYTHONA.search(do_analizy) and _API_MECHANIZMU.search(do_analizy):
        return "wywołanie API mechanizmu znacznika wprost z kodu (omija filtr nazw plików)"
    if re.search(r"zadanie(?:\.py)?[\"'\s]+zakoncz", do_analizy, re.IGNORECASE):
        return "próba zdjęcia znacznika poleceniem zadanie.py zakoncz (to polecenie jest dla człowieka, uruchamiane poza sesją)"
    if _find_kasuje_wszystko(do_analizy):
        return "find z kasowaniem bez filtra nazwy"
    if _find_kasuje_znacznik(do_analizy):
        return "find z kasowaniem i filtrem nazwy pasującym do znacznika"
    return None


# --- Blokada pracy maszynowej (/stop-skrypt) ------------------------------------------
# Zbiory danych giną nie od pomyłki w jednym rekordzie, tylko od pętli, która ją powiela
# po całym zbiorze. Blokadę zakłada i zdejmuje wyłącznie użytkownik. Reguły rozstrzygają
# przed wykonaniem - po kształcie polecenia i po treści uruchamianego pliku.

# Podmiana treści w miejscu: jedno wywołanie przepisuje pliki, których nikt nie czytał.
_PODMIANA_W_MIEJSCU = re.compile(
    r"(?<![\w./-])sed\s+(?:-\S+\s+)*-\w*i\w*(?![\w])"
    r"|(?<![\w./-])sed\s[^;|&\n]*--in-place"
    r"|(?<![\w./-])perl\s+(?:-\S+\s+)*-\w*i\w*"
    r"|(?<![\w./-])(?:gawk|awk)\s[^;|&\n]*-i\s*inplace"
    r"|(?<![\w./-])(?:rename|prename|rpl|sponge|mmv|sd|dos2unix|unix2dos|recode)(?![\w-])"
    r"|(?<![\w./-])iconv\s[^;|&\n]*-o(?![\w-])"
    r"|(?<![\w./-])(?:yq|crudini|xmlstarlet)\s[^;|&\n]*(?:-i|--inplace|ed\s)"
    r"|fileinput\.\w+\s*\([^)]*inplace",
    re.I,
)
# Narzędzia łatania i odtwarzania: jedno wywołanie zmienia dowolnie wiele plików wprost
# z pliku różnicowego albo z historii repozytorium.
_LATANIE_I_ODTWARZANIE = re.compile(
    r"(?<![\w./-])patch(?![\w-])"
    r"|(?<![\w./-])git\s+(?:-\S+\s+)*(?:apply|restore|filter-branch|filter-repo)(?![\w-])"
    r"|(?<![\w./-])git\s+(?:-\S+\s+)*checkout\s[^;|&\n]*(?:--(?:\s|$)|HEAD|[\w/]+\.\w)"
    r"|(?<![\w./-])git\s+(?:-\S+\s+)*stash\s+(?:pop|apply)(?![\w-])"
    r"|(?<![\w./-])git\s+(?:-\S+\s+)*reset\s[^;|&\n]*--hard"
    r"|(?<![\w./-])rsync(?![\w-])",
    re.I,
)
# Edytory wsadowe: skrypt edycji podany w wywołaniu albo w pliku.
_EDYTOR_WSADOWY = re.compile(
    r"(?<![\w./-])ed\s+(?:-\S+\s+)*\S"
    r"|(?<![\w./-])(?:ex|vim|vi|nvim)\s+(?:-\S+\s+)*-\w*[sc]\w*(?![\w])",
    re.I,
)
# Polecenia zmieniające treść albo pliki - sprawdzane w ciele pętli, w argumencie
# `find -exec` i za `xargs`. Sam interpreter tu nie wystarcza: `for f in *.py; do
# python3 -m py_compile $f; done` niczego nie zmienia.
_POLECENIE_ZMIENIAJACE = re.compile(
    r"(?<![\w./-])(?:mv|cp|rm|tee|truncate|dd|install|shred|ln|rsync|unlink|chmod|chown"
    r"|set-content|add-content|remove-item|rename-item|out-file)(?![\w./-])"
    r"|>>?\s*[^\s;|&>]",
    re.I,
)
_PETLA_POWLOKI = re.compile(r"\b(?:for|while|until)\b[\s\S]*?\bdo\b([\s\S]*?)(?:\bdone\b|$)", re.I)
_ROZDZIELACZ_ARGUMENTOW = re.compile(r"(?<![\w./-])(?:xargs|parallel)\b([^\n]*)", re.I)
_FIND_Z_WYKONANIEM = re.compile(
    r"(?<![\w./-])find\s[^\n]*?(-exec(?:dir)?|-ok(?:dir)?)\s+([^\n]*?)(?:\;|;|\+)", re.I)
_FIND_Z_KASOWANIEM = re.compile(r"(?<![\w./-])find\s[^\n]*?-delete(?![\w-])", re.I)

# Klienci baz danych i zapis w ich języku. Odczyt (`SELECT`, `.schema`, `EXPLAIN`)
# przechodzi - blokada dotyczy podmiany treści, nie zaglądania do niej.
_KLIENT_BAZY = re.compile(
    r"(?<![\w./-])(?:sqlite3|psql|pgcli|mysql|mycli|mariadb|mongosh|mongo|redis-cli"
    r"|duckdb|clickhouse-client|cqlsh|surreal|prisma|sequelize|alembic|flyway)(?![\w-])",
    re.I,
)
_ZAPIS_W_BAZIE = re.compile(
    r"(?<![\w])(?:update\s+[\w.\"'`\[\]]+\s+set|delete\s+from|insert\s+into"
    r"|replace\s+into|merge\s+into|upsert\s+into"
    r"|drop\s+(?:table|database|schema|index|view|column)"
    r"|truncate(?:\s+table)?(?![\w])|alter\s+table|create\s+or\s+replace"
    r"|update_many|updatemany|update_one|updateone|delete_many|deletemany|bulk_write"
    r"|bulkwrite|remove\s*\(\s*\{|flushall|flushdb)",
    re.I,
)
# Wczytanie pliku `.sql` do klienta bazy. O tym, czy plik zmienia treść, rozstrzyga
# jego zawartość - `psql -f raport.sql` z samym `SELECT` jest odczytem.
_WCZYTANIE_SQL = re.compile(
    r"<\s*([^\s;|&]+\.sql)(?![\w])|(?<![\w-])-f\s+([^\s;|&]+\.sql)(?![\w])"
    r"|(?<![\w])source\s+([^\s;|&]+\.sql)|\.read\s+([^\s;|&]+\.sql)",
    re.I,
)
_IMPORT_DO_BAZY = re.compile(r"(?<![\w])\.import\b|(?<![\w])load\s+data(?![\w])"
                             r"|(?<![\w])copy\s+[\w.\"]+\s+from(?![\w])", re.I)

# Kod podany wprost w wywołaniu (`python -c`, `node -e`, heredoc do interpretera).
_KONTEKST_KODU_W_LINII = re.compile(
    r"(?<![\w./-])(?:python3?|node|deno|bun|ruby|perl|php|pwsh|powershell)\s+"
    r"(?:-\S+\s+)*-(?:c|e|eval|E|Command|command)(?![\w])",
    re.I,
)
_PETLA_W_KODZIE = re.compile(
    r"(?:^|\n|;)\s*(?:for|while|foreach)\b|\.forEach\s*\(|\.map\s*\(|\bmap\s*\("
    r"|os\.walk\s*\(|glob\.glob\s*\(|\.rglob\s*\(|\.iterdir\s*\(|\bglob\s*\("
    r"|get-childitem|\bfetchall\s*\(|\bcursor\b",
    re.I,
)
_ZAPIS_W_KODZIE = re.compile(
    r"open\s*\([^)]*['\"][rab+]*[wa][rab+]*['\"]"
    r"|\.write_text\s*\(|\.write_bytes\s*\(|\.writelines\s*\(|\.write\s*\("
    r"|os\.(?:remove|unlink|rename|replace|rmdir|truncate)\s*\("
    r"|shutil\.(?:move|copy\w*|rmtree)\s*\("
    r"|\.(?:unlink|rename|replace)\s*\(\s*\)"
    r"|fs\.(?:writeFile|writeFileSync|appendFile\w*|renameSync|unlinkSync|rmSync|rmdirSync)"
    r"|File\.(?:write|delete|rename)|\.save\s*\(|\.commit\s*\(\s*\)|executemany\s*\("
    r"|set-content|add-content|remove-item|rename-item|out-file"
    r"|(?<![\w./-])(?:mv|cp|rm|tee|truncate|shred)(?![\w./-])"
    r"|>>?\s*[^\s;|&>]",
    re.I,
)
LIMIT_ODCZYTU_SKRYPTU_B = 512 * 1024
# Ile zmian w jednym wywołaniu narzędzia plikowego jest jeszcze zmianą pojedynczą.
LIMIT_ZMIAN_W_WYWOLANIU = 20

# Polecenia, które wykonują to, co dostaną na wejściu albo w argumencie: za nimi treść
# przestaje być tekstem, a staje się kodem.
_ODBIORCA_KODU = re.compile(
    r"^\s*(?:sudo\s+)?(?:sh|bash|zsh|dash|ksh|python3?|node|deno|bun|perl|ruby|php"
    r"|pwsh|powershell|sqlite3|psql|mysql|mariadb|mongosh|mongo|redis-cli|duckdb"
    r"|clickhouse-client|patch|ed)(?![\w-])",
    re.I,
)
_TEKST_CYTOWANY = re.compile(r"\"([^\"]*)\"|'([^']*)'")
_TEKST_ECHO = re.compile(r"(?<![\w./-])(echo|printf)\s+(\"[^\"]*\"|'[^']*')", re.I)
_ODCZYT_PLIKU = re.compile(r"(?<![\w./-])cat\s+([^\s;|&<>]+)", re.I)
# Argument-wzorzec wyszukiwania: `grep -rn 'sed -i' docs/` szuka frazy w dokumentacji,
# a nie podmienia treści.
_WZORZEC_WYSZUKIWANIA = re.compile(
    r"(?<![\w./-])(?:grep|egrep|fgrep|rg|ag|ack|findstr|select-string)\s+(?:-\S+\s+)*"
    r"(\"[^\"]*\"|'[^']*')|--grep=(\"[^\"]*\"|'[^']*'|\S+)",
    re.I,
)
# Treść heredoca skierowanego do PLIKU jest tekstem dokumentu, nie kodem do wykonania.
_HEREDOC_DO_PLIKU = re.compile(
    r"(?:>|>>)\s*[^\s;|&]+\s*<<-?\s*['\"]?(\w+)['\"]?(.*?)^\1$",
    re.S | re.M,
)


def _bez_tekstu_echo(polecenie: str) -> str:
    return _TEKST_ECHO.sub(lambda dopasowanie: dopasowanie.group(1) + ' ""', polecenie)


def _bez_wzorca_wyszukiwania(polecenie: str) -> str:
    return _WZORZEC_WYSZUKIWANIA.sub(
        lambda dopasowanie: dopasowanie.group(0).replace(
            dopasowanie.group(1) or dopasowanie.group(2) or "", ""), polecenie)


def _bez_tresci_dokumentu(polecenie: str) -> str:
    return _HEREDOC_DO_PLIKU.sub(lambda dopasowanie: dopasowanie.group(0).replace(
        dopasowanie.group(2), "\n"), polecenie)


def _segmenty_potoku(tresc: str) -> list[str]:
    return [czesc for czesc in re.split(r"\|(?!\|)", tresc)]


def _tresci_podane_do_wykonania(tresc: str, cwd: str | None) -> list[str]:
    """Treści, które w tym poleceniu trafiają do wykonania, choć wyglądają na tekst.

    `echo "UPDATE …" | sqlite3 baza` mijało się z każdą regułą: sam segment `echo`
    niczego nie zmienia, a wykonuje się to, co jest w nim zapisane."""
    zebrane: list[str] = []
    segmenty = _segmenty_potoku(tresc)
    for numer, segment in enumerate(segmenty[:-1]):
        if not _ODBIORCA_KODU.match(segmenty[numer + 1]):
            continue
        for dopasowanie in _TEKST_CYTOWANY.finditer(segment):
            zebrane.append(dopasowanie.group(1) or dopasowanie.group(2) or "")
        for nazwa in _ODCZYT_PLIKU.findall(segment):
            zebrane.append(_tresc_pliku(nazwa, cwd))
    for dopasowanie in re.finditer(r"\$\(\s*cat\s+([^\s)]+)\s*\)|`\s*cat\s+([^\s`]+)\s*`", tresc):
        zebrane.append(_tresc_pliku(dopasowanie.group(1) or dopasowanie.group(2), cwd))
    return [z for z in zebrane if z]


def _tresc_pliku(nazwa: str, cwd: str | None) -> str:
    """Treść pliku wskazanego w poleceniu albo pusty ciąg, gdy nie da się go odczytać."""
    try:
        kandydat = Path(os.path.expanduser(nazwa.strip("\"'")))
        if not kandydat.is_absolute():
            kandydat = (Path(cwd) if cwd else Path.cwd()) / kandydat
        if not kandydat.is_file():
            return ""
        with open(kandydat, "r", encoding="utf-8", errors="replace") as plik:
            return plik.read(LIMIT_ODCZYTU_SKRYPTU_B)
    except (OSError, ValueError):
        return ""


# Plik uruchamiany jako program: na pozycji polecenia albo jako argument interpretera.
# Odczyt tego samego pliku (`cat napraw.py`, `grep def napraw.py`) pracą maszynową nie
# jest - blokada dotyczy uruchomienia, nie czytania.
_URUCHOMIENIE_PLIKU = re.compile(
    r"(?:^|[;&|]\s*|\b(?:then|do|else)\s+)(?:sudo\s+)?(?:env\s+\S+=\S+\s+)*"
    r"(?:(?:python3?|node|deno|bun|ruby|perl|php|sh|bash|zsh|pwsh|powershell|go\s+run)"
    r"\s+(?:-\S+\s+)*([^\s;|&<>]+)|(\.{0,2}/[^\s;|&<>]+))",
    re.I,
)


def _uruchamiane_pliki(polecenie: str, cwd: str | None) -> list[tuple[str, str]]:
    """Pary (nazwa, treść) plików, które to polecenie URUCHAMIA."""
    wynik = []
    for dopasowanie in _URUCHOMIENIE_PLIKU.finditer(polecenie):
        nazwa = (dopasowanie.group(1) or dopasowanie.group(2) or "").strip("\"'")
        if not nazwa or nazwa.startswith("-"):
            continue
        tresc = _tresc_pliku(nazwa, cwd)
        if tresc:
            wynik.append((os.path.basename(nazwa), tresc))
    return wynik


KOMUNIKAT_BLOKADA_SKRYPTOW = (
    "Odrzucone: użytkownik włączył blokadę pracy maszynowej poleceniem /stop-skrypt. "
    "Dopasowana reguła: {powod}. W tym trybie treść zmieniasz POJEDYNCZO i pod kontrolą "
    "- pozycja po pozycji, czytając każdą przed zmianą i po zmianie - zamiast puszczać "
    "jedną podmianę po całym zbiorze. Pętla, `sed -i`, `find -exec`, `xargs`, hurtowy "
    "`UPDATE`, łatka i skrypt przelatujący kolejne rekordy powielają błąd, zanim "
    "ktokolwiek go zobaczy, i tak właśnie została zniszczona baza. Wykonaj tę pracę "
    "ręcznie, choćby była długa; jeżeli zakres jest za duży na jedną turę, zrób tyle, "
    "ile się da, i odnotuj resztę. Nie szukaj obejścia (inna powłoka, skrypt pomocniczy, "
    "podagent, narzędzie MCP) i nie proś o zdjęcie blokady - zdejmuje ją wyłącznie "
    "użytkownik poleceniem /skrypt."
)


def powod_pracy_maszynowej_w_tresci(tekst: str, zrodlo: str = "") -> str | None:
    """Powód blokady rozpoznany w TREŚCI kodu (plik uruchamiany albo kod w linii)."""
    if not tekst:
        return None
    skad = f" ({zrodlo})" if zrodlo else ""
    if _PODMIANA_W_MIEJSCU.search(tekst):
        return f"podmiana treści w miejscu{skad}"
    if _ZAPIS_W_BAZIE.search(tekst) or _IMPORT_DO_BAZY.search(tekst):
        return f"zapis hurtowy do bazy danych{skad}"
    if _PETLA_W_KODZIE.search(tekst) and _ZAPIS_W_KODZIE.search(tekst):
        return f"pętla przepisująca treść{skad}"
    return None


def _zapis_z_pliku_sql(tekst: str, cwd: str | None) -> bool:
    """Czy wczytywany plik `.sql` zmienia treść bazy. Plik nieczytelny liczy się jako
    zmieniający: nie da się sprawdzić, co zrobi."""
    for dopasowanie in _WCZYTANIE_SQL.finditer(tekst):
        nazwa = next((g for g in dopasowanie.groups() if g), "")
        tresc = _tresc_pliku(nazwa, cwd)
        if not tresc or _ZAPIS_W_BAZIE.search(tresc) or _IMPORT_DO_BAZY.search(tresc):
            return True
    return False


def powod_pracy_maszynowej(polecenie: str, powloka: str = "Bash",
                           cwd: str | None = None) -> str | None:
    """Powód blokady pracy maszynowej albo None, gdy polecenie może przejść."""
    if not isinstance(polecenie, str) or not polecenie.strip():
        return None
    surowe = _rozwin_zmienne(re.sub(r"#[^\n]*", " ", polecenie))
    tekst = _bez_tresci_dokumentu(_bez_wzorca_wyszukiwania(_bez_tekstu_echo(surowe)))

    if _PODMIANA_W_MIEJSCU.search(tekst):
        return "podmiana treści w miejscu (sed -i, perl -i, rename i pokrewne)"
    if _LATANIE_I_ODTWARZANIE.search(tekst):
        return "hurtowe nadpisanie plików (patch, git apply/checkout/restore, rsync)"
    if _EDYTOR_WSADOWY.search(tekst):
        return "edytor wsadowy wykonujący skrypt edycji (ed, ex, vim -es)"
    if _FIND_Z_KASOWANIEM.search(tekst):
        return "find z kasowaniem (-delete) - hurtowe usunięcie plików"
    for dopasowanie in _FIND_Z_WYKONANIEM.finditer(tekst):
        if _POLECENIE_ZMIENIAJACE.search(dopasowanie.group(2) or ""):
            return "find -exec uruchamiający polecenie zmieniające pliki"
    for dopasowanie in _ROZDZIELACZ_ARGUMENTOW.finditer(tekst):
        if _POLECENIE_ZMIENIAJACE.search(dopasowanie.group(1) or ""):
            return "xargs albo parallel uruchamiający polecenie zmieniające pliki"
    for dopasowanie in _PETLA_POWLOKI.finditer(tekst):
        if _POLECENIE_ZMIENIAJACE.search(dopasowanie.group(1) or ""):
            return "pętla powłoki z zapisem (for/while ... do ... done)"
    for segment in re.split(r"\|\||&&|[;|\n]", tekst):
        if not _KLIENT_BAZY.search(segment):
            continue
        if _ZAPIS_W_BAZIE.search(segment) or _IMPORT_DO_BAZY.search(segment):
            return "zapis hurtowy do bazy danych (UPDATE/DELETE/DROP)"
        if _zapis_z_pliku_sql(segment, cwd):
            return "wczytanie do bazy pliku .sql, który zmienia jej treść"
    if _KONTEKST_KODU_W_LINII.search(tekst) or "<<" in tekst:
        powod = powod_pracy_maszynowej_w_tresci(tekst, "kod podany wprost w poleceniu")
        if powod:
            return powod
    for tresc in _tresci_podane_do_wykonania(surowe, cwd):
        powod = powod_pracy_maszynowej_w_tresci(tresc, "treść podana do wykonania")
        if powod:
            return powod
    for nazwa, tresc in _uruchamiane_pliki(tekst, cwd):
        powod = powod_pracy_maszynowej_w_tresci(tresc, f"skrypt {nazwa}")
        if powod:
            return powod
    return None


def _liczba_zmian_w_wywolaniu(wejscie: dict) -> int:
    zmiany = wejscie.get("edits")
    return len(zmiany) if isinstance(zmiany, list) else 1


def _replace_all_w_wejsciu(wejscie: dict) -> bool:
    """Czy wywołanie narzędzia plikowego zamienia WSZYSTKIE wystąpienia wzorca."""
    if wejscie.get("replace_all") is True:
        return True
    zmiany = wejscie.get("edits")
    if isinstance(zmiany, list):
        return any(isinstance(z, dict) and z.get("replace_all") is True for z in zmiany)
    return False


def _tekst_zlecenia_podagenta(wejscie: dict) -> str:
    czesci = [wejscie.get(pole) for pole in ("prompt", "description", "task", "instructions")]
    return "\n".join(c for c in czesci if isinstance(c, str))


def kontrola_pracy_maszynowej(narzedzie: str, wejscie: dict, cwd: str | None) -> int | None:
    """Kod blokady, gdy przy włączonym /stop-skrypt wywołanie podmienia treść maszynowo.

    Blokada obowiązuje tak samo na pierwszym planie i w tle: przeniesienie podmiany
    w tło nie czyni jej bardziej odwracalną."""
    if narzedzie in NARZEDZIA_PLIKOWE:
        if _replace_all_w_wejsciu(wejscie):
            return blokuj(KOMUNIKAT_BLOKADA_SKRYPTOW.format(
                powod="zamiana wszystkich wystąpień w pliku naraz (replace_all)"))
        liczba = _liczba_zmian_w_wywolaniu(wejscie)
        if liczba > LIMIT_ZMIAN_W_WYWOLANIU:
            return blokuj(KOMUNIKAT_BLOKADA_SKRYPTOW.format(
                powod=f"{liczba} zmian w jednym wywołaniu (próg: {LIMIT_ZMIAN_W_WYWOLANIU})"))
        return None
    if wywolanie_podagenta(narzedzie, wejscie):
        powod = powod_pracy_maszynowej_w_tresci(_tekst_zlecenia_podagenta(wejscie),
                                                "zlecenie dla podagenta")
        if powod:
            return blokuj(KOMUNIKAT_BLOKADA_SKRYPTOW.format(powod=powod))
        return None
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is None:
        return None
    powloka = narzedzie if narzedzie in NARZEDZIA_POWLOKI else "Bash"
    powod = powod_pracy_maszynowej(tresc, powloka=powloka, cwd=cwd)
    if powod:
        return blokuj(KOMUNIKAT_BLOKADA_SKRYPTOW.format(powod=powod))
    return None



KOMUNIKAT_BLOKADA_PODAGENTOW = (
    "Narzędzie {narzedzie} jest odrzucone: użytkownik włączył blokadę podagentów "
    "poleceniem /blokada (obowiązuje do {wygasa} albo do /blokada-stop). Wykonaj tę "
    "pracę samodzielnie. Nie proponuj zlecenia jej podagentom i nie proś o zdjęcie "
    "blokady - zdejmuje ją wyłącznie użytkownik."
)


KOMUNIKAT_WYGASNIECIE = (
    "Tryb ciągłej pracy WYGASŁ (termin ważności znacznika: {wygasa}) i został zdjęty. "
    "Zlecenie: {opis}. Od tej chwili nic nie blokuje kończenia tury, pytań ani pracy na "
    "pierwszym planie. Jeżeli zlecenie ma być kontynuowane w tym trybie, użytkownik "
    "włącza je ponownie poleceniem /pracuj."
)


def _znacznik_wygasl_i_zdjety(katalog, zdarzenie, glosno: bool = False) -> bool:
    """Termin ważności obowiązuje w KAŻDYM hooku, nie tylko przy próbie zakończenia
    tury: inaczej po upływie terminu model nadal nie mógł zadać pytania ani zapisać
    pliku. `glosno` włącza komunikat w kontekście tury, bo wygaśnięcie było dotąd
    ciche - tryb znikał w trakcie pracy bez śladu."""
    sesja = sesja_ze_zdarzenia(zdarzenie)
    dane = znacznik.wczytaj_znacznik(katalog, sesja)
    if dane is None and znacznik.istnieje_znacznik(katalog, sesja):
        # Plik jest, ale nie da się go odczytać. `wygasl(None)` zwracało False, więc
        # taka blokada trwała wiecznie: `/stop` też potrzebuje odczytu. Najpierw kopia,
        # a gdy jej nie ma - znacznik znika jak wygasły.
        if znacznik.odtworz_znacznik(katalog, sesja):
            dane = znacznik.wczytaj_znacznik(katalog, sesja)
        if dane is None:
            znacznik.usun_znacznik(katalog, sesja)
            if glosno:
                print("Znacznik zlecenia był nieczytelny (uszkodzony plik) i nie dało się "
                      "go odtworzyć z kopii - został zdjęty. Tryb ciągłej pracy NIE "
                      "obowiązuje; użytkownik włącza go ponownie poleceniem /pracuj.")
            return True
    if not znacznik.wygasl(dane):
        return False
    znacznik.usun_znacznik(katalog, sesja)
    if glosno:
        print(KOMUNIKAT_WYGASNIECIE.format(
            wygasa=(dane or {}).get("wygasa") or "brak daty",
            opis=(dane or {}).get("opis") or "(bez opisu)"))
    return True


# Cele zapisu w poleceniu powłoki: przekierowania oraz `-C <katalog>` gita. Zakres
# zlecenia obejmował dotąd tylko narzędzia plikowe, więc `cat > /inne/repo/plik`
# wychodził poza katalog zlecenia bez przeszkód.
_CELE_ZAPISU = re.compile(
    r">{1,2}\|?\s*([^\s;|&]+)"
    r"|\bgit\s+-C\s+([^\s;|&]+)"
    r"|(?<![\w./-])tee\s+((?:-\S+\s+)*)([^\s;|&]+)"
    r"|\s-o\s+([^\s;|&]+)|--output[=\s]([^\s;|&]+)"
)
# Polecenia kopiujące: celem jest ostatni argument niebędący opcją.
_POLECENIA_KOPIUJACE = re.compile(r"(?<![\w./-])(cp|mv|install|rsync)\s+([^;&|\n]+)", re.I)
# Miejsca poza zleceniem, w których zapis jest normalną częścią pracy.
_DOZWOLONE_POZA_ZAKRESEM = ("/tmp/", "/var/tmp/", "/dev/", "/private/tmp/")
_PREFIKS_CD = re.compile(r"^\s*cd\s+(\"[^\"]+\"|'[^']+'|\S+)\s*&&")


def _dozwolony_cel(cel: str, korzen_zlecenia: str = "") -> bool:
    """Czy cel leży w miejscu roboczym dozwolonym mimo wyjścia poza zlecenie. Katalog
    tymczasowy przestaje być neutralny, gdy samo zlecenie w nim leży."""
    pelna = os.path.abspath(os.path.expanduser(cel)).replace("\\", "/")
    korzen = (korzen_zlecenia or "").replace("\\", "/")
    dozwolone = [d for d in _DOZWOLONE_POZA_ZAKRESEM if not korzen.startswith(d)]
    if any(pelna == d.rstrip("/") or pelna.startswith(d) for d in dozwolone):
        return True
    cache = os.path.expanduser(os.environ.get("XDG_CACHE_HOME") or "~/.cache").replace("\\", "/").rstrip("/")
    return bool(cache) and not korzen.startswith(cache + "/") and pelna.startswith(cache + "/")


_GIT_Z_KATALOGIEM = re.compile(r"(?<![\w./-])git\s+-C\s+([^\s;|&]+)([^;|&\n]*)")


def _git_tylko_odczyt(fragment: str) -> bool:
    """Czy `git -C <katalog> …` jest odczytem (status, log, diff, show…)."""
    for argument in fragment.split():
        if argument.startswith("-"):
            continue
        return argument in PODPOLECENIA_GIT_WGLADU
    return False


def _cele_zapisu_w_poleceniu(polecenie: str) -> list[str]:
    cele: list[str] = []
    # Odczytowe `git -C` usuwamy z tekstu przed szukaniem celów zapisu.
    polecenie = _GIT_Z_KATALOGIEM.sub(
        lambda m: " " if _git_tylko_odczyt(m.group(2)) else m.group(0), polecenie)
    for dopasowanie in _CELE_ZAPISU.finditer(polecenie):
        cele.append(dopasowanie.group(1) or dopasowanie.group(2) or dopasowanie.group(4)
                    or dopasowanie.group(5) or dopasowanie.group(6) or "")
    for dopasowanie in _POLECENIA_KOPIUJACE.finditer(polecenie):
        argumenty = [t for t in _tokeny(dopasowanie.group(2)) if t and not t.startswith("-")]
        if len(argumenty) >= 2:
            cele.append(argumenty[-1])
    return [c.strip("\"'") for c in cele if c]


def _cel_zapisu_poza_zakresem(polecenie: str, dane: dict | None,
                              cwd: str | None = None) -> str | None:
    """Cel zapisu leżący poza katalogiem zlecenia albo None. Ścieżki względne liczone
    są od prefiksu `cd <ścieżka bezwzględna> &&`, a bez niego od katalogu roboczego
    zdarzenia - `echo x > ../poza.txt` wychodziło dotąd poza zlecenie bez przeszkód."""
    if not dane or not dane.get("katalogProjektu"):
        return None
    prefiks = _PREFIKS_CD.search(polecenie)
    baza = prefiks.group(1).strip("\"'") if prefiks else ""
    baza = baza if baza and os.path.isabs(os.path.expanduser(baza)) else ""
    if not baza and cwd and os.path.isabs(os.path.expanduser(cwd)):
        baza = cwd
    korzen_zlecenia = str(dane.get("katalogProjektu") or "")
    for cel in _cele_zapisu_w_poleceniu(polecenie):
        if cel.startswith("&") or _dozwolony_cel(cel, korzen_zlecenia):
            continue
        pelna = os.path.expanduser(cel)
        if not os.path.isabs(pelna):
            if not baza:
                continue
            pelna = os.path.join(os.path.expanduser(baza), pelna)
        if znacznik.poza_zakresem_zlecenia(dane, pelna):
            return cel
    return None


def _ochrona_bez_zlecenia(zdarzenie: dict) -> int:
    """Kontrola poleceń przy samej blokadzie podagentów (bez aktywnego zlecenia).

    Bez tego `/blokada` była kasowalna zwykłym `rm -rf .danaco`: strażnik wychodził
    wcześniej przy braku znacznika. Sprawdzany jest wyłącznie mechanizm.
    """
    narzedzie = zdarzenie.get("tool_name")
    wejscie = zdarzenie.get("tool_input")
    if not isinstance(wejscie, dict):
        wejscie = {}
    if narzedzie in NARZEDZIA_PLIKOWE:
        sciezka = wejscie.get("file_path") or wejscie.get("notebook_path")
        if isinstance(sciezka, str) and sciezka.strip():
            powod = powod_ochrony_sciezki(sciezka)
            if powod:
                return blokuj(KOMUNIKAT_PLIK.format(sciezka=sciezka, powod=powod))
        return KOD_ZEZWOL
    if narzedzie in NARZEDZIA_POWLOKI:
        tresc = wejscie.get("command")
        if not isinstance(tresc, str):
            return KOD_ZEZWOL
        regula = regula_blokady_polecenia(tresc, powloka=narzedzie, tylko_mechanizm=True)
        if regula:
            return blokuj(KOMUNIKAT_POLECENIE.format(regula=regula))
    return KOD_ZEZWOL


# Katalog zlecenia ustalony w tej turze hooka: wyszukiwanie chodzi po dysku, więc krok
# drugi (odnotowanie pracy) bierze wynik pierwszego zamiast szukać jeszcze raz.
_KATALOG_TEJ_TURY: dict = {}


LIMIT_WPISOW_DZIENNIKA_PRACY = 2000


def _opis_wywolania(narzedzie: str, wejscie: dict) -> str:
    """Krótki opis wywołania do dziennika pracy."""
    tresc = tresc_polecenia(narzedzie, wejscie)
    if tresc is not None:
        return tresc.strip().splitlines()[0][:160]
    for pole in ("file_path", "notebook_path", "pattern", "url", "path", "description"):
        wartosc = wejscie.get(pole)
        if isinstance(wartosc, str) and wartosc.strip():
            return wartosc.strip()[:160]
    return ""


def zapisz_dziennik_pracy(katalog, sesja: str, narzedzie: str, wejscie: dict,
                          kod: int) -> None:
    """Dopisuje wywołanie do dziennika pracy - jedynego zapisu tego, co model robił."""
    try:
        sciezka = znacznik.sciezka_dziennika_pracy(katalog, sesja)
        sciezka.parent.mkdir(parents=True, exist_ok=True)
        wpis = {"czas": znacznik.teraz(), "narzedzie": narzedzie,
                "co": _opis_wywolania(narzedzie, wejscie)}
        if kod == KOD_BLOKUJ:
            wpis["odrzucone"] = True
        if uruchomione_w_tle(wejscie):
            wpis["wTle"] = True
        with open(sciezka, "a", encoding="utf-8") as plik:
            plik.write(json.dumps(wpis, ensure_ascii=False) + "\n")
        _przytnij_dziennik(sciezka, LIMIT_WPISOW_DZIENNIKA_PRACY)
    except (OSError, ValueError, TypeError):
        pass


def _przytnij_dziennik(sciezka, limit: int) -> None:
    try:
        with open(sciezka, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except OSError:
        return
    if len(linie) <= limit:
        return
    try:
        znacznik.zapisz_atomowo(sciezka, "".join(linie[-limit:]))
    except OSError:
        pass


def polecenie_pretool(zdarzenie: dict | None, blad: str | None) -> int:
    """Rozstrzyga wywołanie, a po DOPUSZCZENIU odnotowuje je jako pracę.

    Kolejność jest istotna: odrzucone wywołanie nigdy się nie wykonuje, więc nie jest
    pracą - liczenie go jako pracy zamieniało odrzucenie w zerowanie licznika."""
    _KATALOG_TEJ_TURY.clear()
    kod = _rozstrzygniecie_pretool(zdarzenie, blad)
    katalog = _KATALOG_TEJ_TURY.get("katalog")
    if katalog is None or not isinstance(zdarzenie, dict):
        return kod
    narzedzie = zdarzenie.get("tool_name")
    wejscie = zdarzenie.get("tool_input")
    if isinstance(narzedzie, str) and isinstance(wejscie, dict):
        sesja = sesja_ze_zdarzenia(zdarzenie)
        zapisz_dziennik_pracy(katalog, sesja, narzedzie, wejscie, kod)
    if kod != KOD_ZEZWOL:
        return kod
    if isinstance(narzedzie, str) and isinstance(wejscie, dict):
        sesja = sesja_ze_zdarzenia(zdarzenie)
        zapamietaj_log_biegu(katalog, sesja, narzedzie, wejscie)
        odnotuj_wywolanie(katalog, sesja, narzedzie, wejscie)
        odnotuj_powtorzenie(katalog, sesja, narzedzie, wejscie)
    return kod


def _rozstrzygniecie_pretool(zdarzenie: dict | None, blad: str | None) -> int:
    # Blokada podagentów działa niezależnie od trybu ciągłej pracy i sprawdzana jest
    # przed nim - użytkownik może jej użyć w zwykłej sesji.
    blokada = None
    blokada_skryptow = None
    if zdarzenie is not None:
        katalog_bl = znacznik.katalog_blokady(cwd_ze_zdarzenia(zdarzenie))
        blokada = znacznik.blokada_aktywna(katalog_bl, sesja_ze_zdarzenia(zdarzenie))
        narzedzie_wstepne = zdarzenie.get("tool_name")
        wejscie_wstepne = zdarzenie.get("tool_input")
        wejscie_wstepne = wejscie_wstepne if isinstance(wejscie_wstepne, dict) else {}
        if (blokada and isinstance(narzedzie_wstepne, str)
                and wywolanie_podagenta(narzedzie_wstepne, wejscie_wstepne)):
            return blokuj(KOMUNIKAT_BLOKADA_PODAGENTOW.format(
                narzedzie=narzedzie_wstepne, wygasa=blokada.get("wygasa", "?")))
        # Blokada pracy maszynowej działa niezależnie od zlecenia i od blokady
        # podagentów, więc sprawdzana jest tu, przed odnalezieniem znacznika.
        blokada_skryptow = znacznik.blokada_skryptow_aktywna(
            katalog_bl, sesja_ze_zdarzenia(zdarzenie))
        if blokada_skryptow and isinstance(narzedzie_wstepne, str) and not blad:
            kod = kontrola_pracy_maszynowej(narzedzie_wstepne, wejscie_wstepne,
                                            cwd_ze_zdarzenia(zdarzenie))
            if kod is not None:
                return kod

    sesja = sesja_ze_zdarzenia(zdarzenie)
    katalog = znacznik.znajdz_katalog_znacznika(cwd_ze_zdarzenia(zdarzenie), sesja=sesja)
    if katalog is None:
        if (blokada or blokada_skryptow) and zdarzenie is not None and not blad:
            return _ochrona_bez_zlecenia(zdarzenie)
        return KOD_ZEZWOL
    if _znacznik_wygasl_i_zdjety(katalog, zdarzenie):
        return KOD_ZEZWOL
    if blad or zdarzenie is None:
        return blokuj(KOMUNIKAT_ZDARZENIE.format(powod=blad or "brak zdarzenia"))
    znacznik.odnotuj_obecnosc(katalog, znacznik.wczytaj_znacznik(katalog, sesja), sesja)
    _KATALOG_TEJ_TURY["katalog"] = katalog

    narzedzie = zdarzenie.get("tool_name")
    if not isinstance(narzedzie, str) or not narzedzie:
        return blokuj(KOMUNIKAT_ZDARZENIE.format(powod="brak pola tool_name"))
    wejscie = zdarzenie.get("tool_input")
    if not isinstance(wejscie, dict):
        wejscie = {}

    kod_ciszy = bramka_ciszy(katalog, zdarzenie)
    if kod_ciszy is not None:
        return kod_ciszy

    # Sprawdzanie stanu własnego biegu w kółko, bez pracy pomiędzy, jest przerwą
    # schowaną za cudzym procesem.
    kod_sprawdzenia = bramka_sprawdzen_stanu(katalog, zdarzenie, narzedzie, wejscie)
    if kod_sprawdzenia is not None:
        return kod_sprawdzenia

    kod_powtorzenia = bramka_powtorzen(katalog, zdarzenie, narzedzie, wejscie)
    if kod_powtorzenia is not None:
        return kod_powtorzenia

    kod_petli = bramka_petli_wywolan(katalog, zdarzenie, narzedzie, wejscie)
    if kod_petli is not None:
        return kod_petli

    if narzedzie in NARZEDZIA_PRZEPUSTKI:
        return KOD_ZEZWOL

    if narzedzie in NARZEDZIA_ODBIORU_WYNIKU:
        # Samo pobranie wyniku jest dozwolone i pożądane - blokujemy tylko wariant, w
        # którym wywołanie czeka na zakończenie zadania.
        if wejscie.get(POLE_BLOKOWANIA_ODBIORU) is False:
            return KOD_ZEZWOL
        limit = limit_wywolania_s(wejscie)
        if limit is not None and limit <= LIMIT_ODBIORU_WYNIKU_S:
            return KOD_ZEZWOL
        return blokuj(KOMUNIKAT_ODBIOR_BLOKUJACY.format(
            narzedzie=narzedzie, prog=LIMIT_ODBIORU_WYNIKU_S))

    if NARZEDZIA_OCZEKIWANIA.match(narzedzie):
        return blokuj(KOMUNIKAT_OCZEKIWANIE.format(narzedzie=narzedzie))

    if narzedzie == NARZEDZIE_PYTANIA:
        return blokuj(KOMUNIKAT_PYTANIE)

    if wywolanie_podagenta(narzedzie, wejscie) and not uruchomione_w_tle(wejscie):
        # Praca wieloagentowa jest dozwolona wyłącznie w tle: wariant synchroniczny
        # zabiera użytkownikowi kontakt na cały czas pracy podagenta. Brak pola tła
        # w schemacie narzędzia NIE jest przepustką - wywołanie bez niego czeka tak
        # samo, a przepuszczanie go było obejściem.
        return blokuj(KOMUNIKAT_PODAGENT_SYNCHRONICZNY.format(narzedzie=narzedzie))

    if NARZEDZIA_ZATRZYMANIA.match(narzedzie):
        return blokuj(KOMUNIKAT_ZATRZYMANIE.format(narzedzie=narzedzie))

    if NARZEDZIA_HARMONOGRAMU.search(narzedzie):
        return blokuj(KOMUNIKAT_HARMONOGRAM.format(narzedzie=narzedzie))

    if NARZEDZIA_WIADOMOSCI.search(narzedzie):
        return blokuj(KOMUNIKAT_WIADOMOSC.format(narzedzie=narzedzie))

    if narzedzie in NARZEDZIA_PLIKOWE:
        sciezka = wejscie.get("file_path") or wejscie.get("notebook_path")
        if not isinstance(sciezka, str) or not sciezka.strip():
            return blokuj(KOMUNIKAT_ZDARZENIE.format(powod=f"{narzedzie} bez ścieżki pliku"))
        dane_znacznika = znacznik.wczytaj_znacznik(katalog, sesja)
        if znacznik.poza_zakresem_zlecenia(dane_znacznika, sciezka):
            return blokuj(
                f"Zapis do {sciezka} leży poza katalogiem zlecenia "
                f"({(dane_znacznika or {}).get('katalogProjektu')}). W trybie ciągłej pracy "
                "pracujesz wyłącznie nad tym zleceniem i wyłącznie w jego katalogu - "
                "cudze repozytoria i inne produkty są poza zakresem. Wróć do zlecenia."
            )
        powod = (powod_ochrony_sciezki(sciezka)
                 or _powod_transkrypcji(sciezka, zdarzenie)
                 or powod_ochrony_tresci(_tresc_zapisu(narzedzie, wejscie), sciezka))
        if powod:
            return blokuj(KOMUNIKAT_PLIK.format(sciezka=sciezka, powod=powod))
        return KOD_ZEZWOL

    if narzedzie not in NARZEDZIA_PLIKOWE:
        trafienie = sciezka_chroniona_w_wywolaniu(wejscie)
        if trafienie is not None:
            return blokuj(KOMUNIKAT_PLIK.format(sciezka=trafienie[0], powod=trafienie[1]))
        for wartosc in _wartosci_tekstowe(wejscie):
            powod = _powod_transkrypcji(wartosc.strip(), zdarzenie)
            if powod:
                return blokuj(KOMUNIKAT_PLIK.format(sciezka=wartosc.strip(), powod=powod))

    # Narzędzie MCP z polem `command`, `script` albo `cmd` to powłoka pod inną nazwą
    # i podlega temu samemu reżimowi co `Bash`: przy samym filtrze nazw plików
    # `sleep 3000` i `npm run dev` przechodziły narzędziem MCP.
    tresc = tresc_polecenia(narzedzie, wejscie)
    if narzedzie in NARZEDZIA_POWLOKI and tresc is None:
        return blokuj(KOMUNIKAT_ZDARZENIE.format(powod=f"{narzedzie} bez pola command"))
    if tresc is not None:
        powloka = narzedzie if narzedzie in NARZEDZIA_POWLOKI else "Bash"
        narzedzie_powloki = narzedzie
        narzedzie = powloka
        regula = regula_blokady_polecenia(tresc, powloka=powloka)
        if regula:
            return blokuj(KOMUNIKAT_POLECENIE.format(regula=regula))
        sciezka_transkrypcji = transkrypcja_ze_zdarzenia(zdarzenie)
        if sciezka_transkrypcji and sciezka_transkrypcji in tresc:
            return blokuj(KOMUNIKAT_POLECENIE.format(
                regula="operacja na pliku transkrypcji tej rozmowy (tam da się podłożyć "
                       "fałszywe polecenie użytkownika)"))
        cel = _cel_zapisu_poza_zakresem(tresc, znacznik.wczytaj_znacznik(katalog, sesja),
                                        cwd_ze_zdarzenia(zdarzenie))
        if cel:
            return blokuj(
                f"Polecenie zapisuje poza katalogiem zlecenia ({cel}). W trybie ciągłej "
                "pracy pracujesz wyłącznie w katalogu tego zlecenia - cudze repozytoria "
                "i inne produkty są poza zakresem."
            )
        w_tle = uruchomione_w_tle(wejscie) or polecenie_w_tle(tresc)
        # Czekanie jest zakazane także w poleceniu z `&`: to, co stoi PO ampersandzie,
        # wykonuje się na pierwszym planie mimo tła sąsiada.
        for linia in _czesc_pierwszoplanowa(tresc).split("\n"):
            fragment = _PREFIKS_TIMEOUT.sub("", linia).strip()
            if not fragment:
                continue
            oczekiwanie_zawsze = POLECENIA_OCZEKIWANIA.search(fragment)
            if oczekiwanie_zawsze:
                return blokuj(KOMUNIKAT_OCZEKIWANIE_POWLOKI.format(
                    fragment=oczekiwanie_zawsze.group(0).strip()))
        czekanie = powod_czekania(tresc, wejscie)
        if czekanie:
            return blokuj(KOMUNIKAT_CZEKANIE_W_TLE.format(powod=czekanie))
        odliczanie = _sleep_ponad_prog(_PREFIKS_TIMEOUT.sub("", tresc))
        if odliczanie:
            return blokuj(KOMUNIKAT_CZEKANIE_W_TLE.format(
                powod=f"odliczanie w treści polecenia ({odliczanie})"))
        if not w_tle:
            # Prefiks `timeout N` odcinamy przed dopasowaniem: sam limit czasu nie
            # zmienia tego, że polecenie jest długie, a przesuwa je z pozycji polecenia.
            bez_prefiksu = _PREFIKS_TIMEOUT.sub("", tresc).lstrip()
            nieskonczone = POLECENIA_NIESKONCZONE.search(bez_prefiksu)
            if nieskonczone:
                return blokuj(KOMUNIKAT_PIERWSZY_PLAN.format(fragment=nieskonczone.group(0).strip()))
            oczekiwanie = POLECENIA_OCZEKIWANIA.search(bez_prefiksu)
            if oczekiwanie:
                return blokuj(KOMUNIKAT_OCZEKIWANIE_POWLOKI.format(
                    fragment=oczekiwanie.group(0).strip()))
            # Limit POWYŻEJ progu pierwszego planu blokuje bez względu na to, jakim
            # poleceniem jest wywołanie: rozpoznawanie po nazwach przepuszczało
            # wszystko, czego na liście nie było (`ssh`, `scp`, `rsync`). Wywołanie
            # bez zadeklarowanego limitu przechodzi - przerwie je klient po limicie
            # domyślnym, równym progowi.
            limit = _zadeklarowany_limit_s(tresc, wejscie)
            if limit is None:
                limit = limit_wywolania_s(wejscie)
            if limit is not None and limit > LIMIT_PIERWSZEGO_PLANU_S:
                return blokuj(KOMUNIKAT_LIMIT_POLECENIA.format(
                    limit=limit, prog=LIMIT_PIERWSZEGO_PLANU_S))
            if not wylacznie_wglad(bez_prefiksu, powloka):
                return blokuj(KOMUNIKAT_TLO_WYMAGANE.format(
                    fragment=tresc.strip().splitlines()[0][:120]))
        diagnostyka(f"PreToolUse: {narzedzie_powloki} sprawdzone jako powłoka")
        return KOD_ZEZWOL

    # Wszystkie pozostałe narzędzia (w tym `mcp__*`, `WebFetch`, `WebSearch`): przechodzą
    # tylko z deklaracją pracy w tle albo z limitem czasu w granicach pierwszego planu.
    if uruchomione_w_tle(wejscie):
        return KOD_ZEZWOL
    limit = limit_wywolania_s(wejscie)
    if limit is not None:
        if limit > LIMIT_PIERWSZEGO_PLANU_S:
            return blokuj(KOMUNIKAT_LIMIT_NARZEDZIA.format(
                narzedzie=narzedzie, limit=limit, prog=LIMIT_PIERWSZEGO_PLANU_S))
        return KOD_ZEZWOL
    # Narzędzie bez pola limitu i bez pola tła: trwałe odrzucenie odebrałoby modelowi
    # całą tę rodzinę narzędzi, więc wywołanie przechodzi, a ślad zostaje w dzienniku.
    zapisz_dziennik_ciszy(katalog, narzedzie, "brak pola limitu czasu i pola pracy w tle")
    diagnostyka(f"PreToolUse: {narzedzie} bez deklarowanego limitu czasu - przepuszczone "
                f"i odnotowane w {katalog / NAZWA_DZIENNIKA_CISZY}")
    return KOD_ZEZWOL


# --- PreCompact

def polecenie_kompakt(zdarzenie: dict | None, blad: str | None) -> int:
    """Kompresja kontekstu przebiega normalnie - hook jej nie wstrzymuje. Zapisuje stan
    zlecenia do pliku i przypomina na stdout, że tryb obowiązuje dalej. Zawsze 0:
    zatrzymana kompresja zabiłaby sesję przepełnionym kontekstem."""
    sesja = sesja_ze_zdarzenia(zdarzenie)
    katalog = znacznik.znajdz_katalog_znacznika(cwd_ze_zdarzenia(zdarzenie), sesja=sesja)
    if katalog is None:
        return KOD_ZEZWOL
    if _znacznik_wygasl_i_zdjety(katalog, zdarzenie, glosno=True):
        return KOD_ZEZWOL
    dane = znacznik.wczytaj_znacznik(katalog, sesja) or {}

    opis = str(dane.get("opis") or "(bez opisu)")
    kroki = dane.get("kroki") if isinstance(dane.get("kroki"), list) else []
    wiersze = [
        "# Stan zlecenia (tryb ciągłej pracy Danaco)",
        "",
        f"- Zlecenie: {opis}",
        f"- Rozpoczęto: {dane.get('rozpoczeto', '?')}",
        f"- Katalog zlecenia: {dane.get('katalogProjektu', '?')}",
        f"- Termin ważności znacznika: {dane.get('wygasa') or 'bezterminowo'}",
        f"- Zapisano przed kompresją kontekstu: {znacznik.teraz()}",
        "",
        "## Odnotowane kroki",
        "",
    ]
    wiersze += [f"- {k.get('czas', '?')}: {k.get('tekst', '')}" for k in kroki[-50:]] or ["- (brak)"]
    try:
        sciezka_stanu = znacznik.sciezka_stanu(katalog, sesja)
        sciezka_stanu.parent.mkdir(parents=True, exist_ok=True)
        znacznik.zapisz_atomowo(sciezka_stanu, "\n".join(wiersze) + "\n")
    except OSError:
        pass

    print(
        "Kompresja kontekstu w trakcie trybu ciągłej pracy Danaco. Tryb obowiązuje "
        f"dalej po kompresji: zlecenie brzmi „{opis}”, katalog zlecenia to "
        f"{dane.get('katalogProjektu', '?')}, a stan zapisano w "
        f"{znacznik.sciezka_stanu(katalog, sesja)}. Po kompresji wróć do tego zlecenia bez "
        "pytania użytkownika, bez kończenia tury i bez raportu na czacie - zlecenie ma "
        "jeden raport, końcowy; blokadę zdejmuje wyłącznie jego polecenie kończące."
    )
    return KOD_ZEZWOL


# --- PostToolUse: kontrola po poleceniu powłoki

KOMUNIKAT_ODTWORZENIE = (
    "Plik znacznika zniknął po tym poleceniu i został ODTWORZONY z kopii leżącej poza "
    "katalogiem projektu ({katalog}). Usunięcie znacznika nie jest drogą zakończenia "
    "zlecenia - kończy je wyłącznie polecenie użytkownika na czacie albo termin "
    "ważności. Wróć do zlecenia i nie próbuj kasować mechanizmu."
)


def polecenie_kontrola(zdarzenie: dict | None, blad: str | None) -> int:
    """Po poleceniu powłoki sprawdza, czy znacznik nadal jest na miejscu, i odtwarza go
    z kopii spoza katalogu projektu. Bez tego `rm -rf .danaco` kończył zlecenie."""
    if blad or zdarzenie is None:
        return KOD_ZEZWOL
    start = cwd_ze_zdarzenia(zdarzenie)
    kandydaci = []
    # Kandydaci muszą pokrywać się z wyszukiwaniem z pozostałych hooków: znacznik bywa
    # w katalogu nadrzędnym, a `korzen_projektu` zwracał wtedy katalog bieżący
    # i skasowany znacznik nie był odtwarzany.
    sesja = sesja_ze_zdarzenia(zdarzenie)
    for kandydat in znacznik.kandydaci_katalogow(start):
        if kandydat not in kandydaci:
            kandydaci.append(kandydat)
    for korzen in (znacznik.korzen_projektu(start), znacznik.korzen_projektu()):
        katalog = korzen / znacznik.NAZWA_KATALOGU
        if katalog not in kandydaci:
            kandydaci.append(katalog)
    for katalog in kandydaci:
        try:
            if znacznik.istnieje_znacznik(katalog, sesja):
                continue
        except OSError:
            continue
        if znacznik.odtworz_znacznik(katalog, sesja):
            return blokuj(KOMUNIKAT_ODTWORZENIE.format(katalog=katalog))
    return KOD_ZEZWOL


# --- wejście

def _znacznik_aktywny_bezpiecznie() -> bool:
    """Używane tylko w ścieżkach awaryjnych: gdy nawet sprawdzenie znacznika
    zawodzi, zakładamy, że jest aktywny (fail-closed)."""
    try:
        return znacznik.znajdz_katalog_znacznika() is not None
    except BaseException:  # noqa: BLE001
        return True


def _potwierdz_wykonanie() -> None:
    """Zostawia ślad, że kod strażnika faktycznie się wykonał.

    Wrapper czyta ten plik: interpreter kończący się kodem 0 bez potwierdzenia jest
    atrapą podłożoną w PATH, a nie Pythonem."""
    sciezka = os.environ.get("DANACO_POTWIERDZENIE")
    if not sciezka:
        return
    try:
        with open(sciezka, "w", encoding="utf-8") as plik:
            plik.write("straznik\n")
    except OSError:
        pass


def main(argv: list[str]) -> int:
    _potwierdz_wykonanie()
    if len(argv) != 2 or argv[1] not in ("stop", "prompt", "pretool", "kompakt", "kontrola"):
        print("Użycie: straznik.py stop|prompt|pretool|kompakt|kontrola  (JSON zdarzenia na stdin)",
              file=sys.stderr)
        return KOD_BLOKUJ if _znacznik_aktywny_bezpiecznie() else KOD_ZEZWOL

    tryb = argv[1]
    zdarzenie, blad = wczytaj_zdarzenie()
    if tryb == "stop":
        return polecenie_stop(zdarzenie, blad)
    if tryb == "prompt":
        return polecenie_prompt(zdarzenie, blad)
    if tryb == "kompakt":
        return polecenie_kompakt(zdarzenie, blad)
    if tryb == "kontrola":
        return polecenie_kontrola(zdarzenie, blad)
    return polecenie_pretool(zdarzenie, blad)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException as blad:  # noqa: BLE001 - każdy nieprzewidziany błąd = fail-closed
        tryb = sys.argv[1] if len(sys.argv) > 1 else "?"
        if tryb in ("prompt", "kompakt", "kontrola") or not _znacznik_aktywny_bezpiecznie():
            print(f"[straznik] nieoczekiwany błąd ({tryb}, pominięty): {blad!r}", file=sys.stderr)
            sys.exit(KOD_ZEZWOL)
        print(
            "Strażnik trybu ciągłej pracy napotkał nieoczekiwany błąd i blokuje "
            f"(fail-closed): {blad!r}. Kontynuuj pracę nad zleceniem.",
            file=sys.stderr,
        )
        sys.exit(KOD_BLOKUJ)
