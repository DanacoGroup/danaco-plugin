#!/usr/bin/env python3
"""Kontrola definicji pętli orkiestracji Danaco Console.

Pętla autonomiczna z czterema modelami pracuje bez człowieka, więc nie ma nikogo, kto
zauważy, że kręci się w kółko, przepala budżet albo kończy pracę na podstawie własnej opinii.
To narzędzie odmawia uruchomienia definicji, w której brakuje któregokolwiek z zabezpieczeń.

Podkomendy:
  validate  - kontrola niezmienników definicji przepływu
  report    - opis przepływu i diagram pętli (Markdown + Mermaid)

Kody wyjścia: 0 w porządku, 2 naruszenie niezmiennika, 4 błąd wejścia/wyjścia.
Zależności: wyłącznie biblioteka standardowa Pythona 3.9+.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXIT_OK, EXIT_INVALID, EXIT_IO = 0, 2, 4

ROLE = ("coordinator", "builder", "reviewer", "researcher")
MAX_ROL = 4  # projekt przewiduje najwyżej cztery tory AI w jednej sesji
# Cztery warunki stopu, każdy odpowiada innemu sposobowi, w jaki pętla zawodzi:
# fałszywe zakończenie, przepalony budżet, przekroczony czas, krążenie w kółko.
WYMAGANE_STOPY = ("acceptancePassed", "budgetExhausted", "wallClockExceeded", "noProgress")
STOPY_Z_PROGIEM = ("noProgress", "repeatedFailure")
DZIALANIA = ("finish", "halt", "escalate")
SILA = {"shared": 0, "hybrid": 1, "isolated": 2}


def w_korzeniu(root: Path, wzgledna, opis: str) -> Path:
    """Ścieżka docelowa ograniczona do korzenia repozytorium.

    Ścieżka bierze się z argumentu albo z pliku danych, więc bez tej kontroli
    `..` albo ścieżka absolutna kierowałyby zapis poza repozytorium.
    """
    if not isinstance(wzgledna, str) or not wzgledna.strip():
        print("BŁĄD: {} musi być niepustym łańcuchem".format(opis), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    if Path(wzgledna).is_absolute():
        print("BŁĄD: {} ({}) jest ścieżką absolutną - podawaj ścieżkę względną wobec "
              "korzenia repozytorium".format(opis, wzgledna), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    cel = (root / wzgledna).resolve()
    if cel != root and root not in cel.parents:
        print("BŁĄD: {} ({}) wskazuje poza korzeń repozytorium {}".format(opis, wzgledna, root),
              file=sys.stderr)
        sys.exit(EXIT_INVALID)
    return cel


def wczytaj(sciezka: Path, wymagany: bool = True):
    """Obiekt JSON z pliku albo wyjście z kodem z kontraktu narzędzia.

    Kontrakt bywa modyfikowany ręcznie albo przychodzi z gałęzi zewnętrznej;
    plik, który nie jest obiektem JSON, musi dać kod walidacji, nie traceback.
    """
    if not sciezka.exists():
        if not wymagany:
            return None
        print("BŁĄD: nie znaleziono {}".format(sciezka), file=sys.stderr)
        sys.exit(EXIT_IO)
    try:
        dane = json.loads(sciezka.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print("BŁĄD: {} nie da się odczytać jako JSON UTF-8: {}".format(sciezka, exc), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    except OSError as exc:
        print("BŁĄD: {} nie da się odczytać: {}".format(sciezka, exc), file=sys.stderr)
        sys.exit(EXIT_IO)
    if not isinstance(dane, dict):
        print("BŁĄD: {} musi zawierać obiekt JSON, zawiera: {}".format(sciezka, type(dane).__name__),
              file=sys.stderr)
        sys.exit(EXIT_INVALID)
    return dane


def skladowe_silnie_spojne(wierzcholki, krawedzie):
    """Algorytm Tarjana. Każda składowa z cyklem musi zawierać bramkę kontroli."""
    indeks, nisko, na_stosie, stos, wynik = {}, {}, set(), [], []
    licznik = [0]

    def odwiedz(v):
        indeks[v] = nisko[v] = licznik[0]
        licznik[0] += 1
        stos.append(v)
        na_stosie.add(v)
        for w in krawedzie.get(v, ()):
            if w not in indeks:
                odwiedz(w)
                nisko[v] = min(nisko[v], nisko[w])
            elif w in na_stosie:
                nisko[v] = min(nisko[v], indeks[w])
        if nisko[v] == indeks[v]:
            skladowa = []
            while True:
                w = stos.pop()
                na_stosie.discard(w)
                skladowa.append(w)
                if w == v:
                    break
            wynik.append(skladowa)

    sys.setrecursionlimit(10000)
    for v in wierzcholki:
        if v not in indeks:
            odwiedz(v)
    return wynik


def sprawdz(przeplyw, kontrakt):
    bledy = []

    if not przeplyw.get("id"):
        bledy.append("przepływ nie ma identyfikatora")
    if not przeplyw.get("goal"):
        bledy.append("przepływ nie ma pola goal - pętla bez zapisanego celu nie da się ocenić "
                     "ani zatrzymać na jego osiągnięciu")

    # --- role
    role = przeplyw.get("roles", [])
    if not role:
        bledy.append("przepływ nie deklaruje ról")
    widziane = {}
    for r in role:
        nazwa = r.get("role")
        if nazwa not in ROLE:
            bledy.append("nieznana rola {!r}; dopuszczalne: {}".format(nazwa, ", ".join(ROLE)))
            continue
        if nazwa in widziane:
            bledy.append("rola {!r} zadeklarowana dwa razy".format(nazwa))
        widziane[nazwa] = r
        if int(r.get("tokenBudget", 0)) <= 0:
            bledy.append("rola {}: brak budżetu tokenów - budżet na rolę jest jedynym "
                         "mechanizmem, który zatrzyma źle postawione zadanie".format(nazwa))
    if len(role) > MAX_ROL:
        bledy.append("zadeklarowano {} ról; projekt przewiduje najwyżej {} tory".format(len(role), MAX_ROL))

    kontroler = widziane.get("reviewer")
    wykonawca = widziane.get("builder")
    if kontroler:
        if kontroler.get("isolation") != "isolated":
            bledy.append("rola reviewer musi mieć izolację isolated; kontroler, który widzi "
                         "rozumowanie wykonawcy, potwierdza je znacznie chętniej niż ocenia")
        if wykonawca and kontroler.get("model") and kontroler["model"] == wykonawca.get("model"):
            bledy.append("reviewer i builder używają tego samego modelu {!r}; model kontrolujący "
                         "własną pracę nie jest kontrolą".format(kontroler["model"]))

    # --- kroki
    lista_krokow = przeplyw.get("steps", [])
    for k in lista_krokow:
        if not k.get("id"):
            bledy.append("krok bez identyfikatora")
    kroki = {}
    for k in lista_krokow:
        if k.get("id") in kroki:
            bledy.append("krok {!r}: identyfikator powtarza się".format(k["id"]))
        if k.get("id"):
            kroki[k["id"]] = k
    if not kroki:
        bledy.append("przepływ nie ma kroków")
    krawedzie = {}
    for kid, k in kroki.items():
        if k.get("role") not in widziane:
            bledy.append("krok {}: rola {!r} nie jest zadeklarowana".format(kid, k.get("role")))
        nastepne = list(k.get("next", []))
        if k.get("onReject"):
            nastepne.append(k["onReject"])
        for n in nastepne:
            if n not in kroki:
                bledy.append("krok {}: prowadzi do nieistniejącego kroku {!r}".format(kid, n))
        krawedzie[kid] = [n for n in nastepne if n in kroki]
        if not k.get("terminal") and not nastepne:
            bledy.append("krok {}: nie jest końcowy i nigdzie nie prowadzi - pętla utknie "
                         "na nim bez warunku stopu".format(kid))
        if k.get("terminal") and k.get("next"):
            bledy.append("krok {}: jest końcowy, a ma pole next - albo kończy, albo prowadzi dalej".format(kid))
        if k.get("onReject") and not k.get("gate"):
            bledy.append("krok {}: ma onReject, ale nie jest bramką (gate: true) - kto miałby odrzucać?".format(kid))

    koncowe = [kid for kid, k in kroki.items() if k.get("terminal")]
    if not koncowe:
        bledy.append("żaden krok nie jest oznaczony jako terminal - pętla nie ma jak się skończyć")
    for kid in koncowe:
        akceptacja = kroki[kid].get("acceptance", [])
        if not akceptacja:
            bledy.append("krok końcowy {}: brak listy acceptance. Pętla, która kończy się na "
                         "opinii koordynatora, nie jest zweryfikowana - potrzebne są polecenia "
                         "sprawdzalne maszynowo".format(kid))

    # --- osiągalność
    # Początek: jawne pole `start` albo kroki bez poprzednika. Pole `start` jest potrzebne,
    # gdy zawrót po odrzuceniu prowadzi do pierwszego kroku i każdy krok ma poprzednika.
    start = przeplyw.get("start")
    if start and start not in kroki:
        bledy.append("start wskazuje nieistniejący krok {!r}".format(start))
        start = None
    if start:
        wejsciowe = [start]
    else:
        wejsciowe = [kid for kid in kroki if not any(kid in v for v in krawedzie.values())]
    if kroki and not wejsciowe:
        bledy.append("każdy krok ma poprzednika - wskaż początek przepływu polem start")
    osiagalne = set()
    do_odwiedzenia = list(wejsciowe)
    while do_odwiedzenia:
        kid = do_odwiedzenia.pop()
        if kid in osiagalne:
            continue
        osiagalne.add(kid)
        do_odwiedzenia.extend(krawedzie.get(kid, ()))
    nieosiagalne = sorted(set(kroki) - osiagalne)
    for kid in nieosiagalne:
        bledy.append("krok {} jest nieosiągalny z kroku wejściowego ({})".format(kid, ", ".join(wejsciowe)))
    if nieosiagalne and not start:
        bledy.append("jeśli początek przepływu leży w cyklu (zawrót po odrzuceniu prowadzi do "
                     "pierwszego kroku), wskaż go jawnie polem start")

    # --- każdy cykl musi mieć bramkę kontroli
    for skladowa in skladowe_silnie_spojne(list(kroki), krawedzie):
        cykl = len(skladowa) > 1 or (skladowa and skladowa[0] in krawedzie.get(skladowa[0], ()))
        if not cykl:
            continue
        if not any(kroki[k].get("gate") for k in skladowa):
            bledy.append("pętla {} nie zawiera kroku z gate: true. Pętla bez bramki kontroli "
                         "potrafi krążyć w nieskończoność, a przy pracy bez człowieka nie ma "
                         "kto tego zauważyć".format(" -> ".join(sorted(skladowa))))

    # --- warunki stopu
    stopy = {}
    for s in przeplyw.get("stop", []):
        when = s.get("when")
        if when in stopy:
            bledy.append("warunek stopu {!r} zadeklarowany dwa razy".format(when))
        stopy[when] = s
        if when in STOPY_Z_PROGIEM and int(s.get("threshold") or 0) < 1:
            bledy.append("warunek stopu {!r} bez dodatniego progu".format(when))
        if s.get("action") not in DZIALANIA:
            bledy.append("warunek stopu {!r}: nieznane działanie {!r}; dopuszczalne: {}".format(
                when, s.get("action"), ", ".join(DZIALANIA)))
    for wymagany in WYMAGANE_STOPY:
        if wymagany not in stopy:
            bledy.append("brak warunku stopu {!r} - wszystkie cztery muszą być zadeklarowane".format(wymagany))
    if stopy.get("acceptancePassed", {}).get("action") not in (None, "finish"):
        bledy.append("acceptancePassed musi kończyć pętlę działaniem finish - to jedyny sposób "
                     "zakończenia powodzeniem")
    for when in ("budgetExhausted", "wallClockExceeded"):
        if stopy.get(when, {}).get("action") == "finish":
            bledy.append("warunek stopu {!r} z działaniem finish udaje powodzenie - użyj halt "
                         "albo escalate".format(when))
    if any(s.get("action") == "escalate" for s in przeplyw.get("stop", [])) and not przeplyw.get("escalation"):
        bledy.append("przepływ eskaluje, ale nie ma sekcji escalation - eskalacja donikąd "
                     "jest tym samym co jej brak")

    # --- budżet
    budzet = przeplyw.get("budget", {})
    calkowity = int(budzet.get("totalTokens") or 0)
    if calkowity <= 0:
        bledy.append("brak budżetu całkowitego (budget.totalTokens)")
    if int(budzet.get("wallClockHours") or 0) <= 0:
        bledy.append("brak ograniczenia czasu (budget.wallClockHours) - praca bez człowieka "
                     "wymaga twardego końca także w czasie, nie tylko w tokenach")
    na_zadanie = int(budzet.get("perTaskTokens") or 0)
    if na_zadanie <= 0:
        bledy.append("brak budżetu na zadanie (budget.perTaskTokens) - jedno źle postawione "
                     "zadanie nie może zjeść budżetu roli")
    suma = sum(int(r.get("tokenBudget") or 0) for r in role)
    if calkowity and suma > calkowity:
        bledy.append("suma budżetów ról ({}) przekracza budżet całkowity ({})".format(suma, calkowity))
    for r in role:
        if na_zadanie and int(r.get("tokenBudget") or 0) and na_zadanie > int(r["tokenBudget"]):
            bledy.append("budżet na zadanie ({}) przekracza budżet roli {} ({})".format(
                na_zadanie, r.get("role"), r["tokenBudget"]))

    # --- kolejka i audyt
    kolejka = przeplyw.get("queue", {})
    if int(kolejka.get("maxDepth") or 0) < 1:
        bledy.append("kolejka bez maxDepth - kolejka bez ograniczenia rośnie do wyczerpania pamięci")
    if int(kolejka.get("maxRetries") or 0) < 1:
        bledy.append("kolejka bez maxRetries - zadanie, które zawodzi zawsze, będzie ponawiane zawsze")
    audyt = przeplyw.get("audit", {})
    if not audyt.get("appendOnly"):
        bledy.append("audit.appendOnly nie jest ustawione. Dziennik, który da się nadpisać, "
                     "nie odpowie na pytanie, który model wprowadził daną zmianę")

    # --- zgodność z macierzą trybów
    tryb = przeplyw.get("mode")
    if not tryb:
        bledy.append("przepływ nie ma pola mode - bez trybu sesyjnego nie ma macierzy widoczności")
    if kontrakt is None:
        for r in role:
            if r.get("isolation") not in SILA:
                bledy.append("rola {}: nieznany poziom izolacji {!r}".format(r.get("role"), r.get("isolation")))
    elif tryb:
        tryby = {m["id"]: m for m in kontrakt.get("modes", [])}
        if tryb not in tryby:
            bledy.append("tryb {!r} nie istnieje w kontrakcie".format(tryb))
        else:
            ai = tryby[tryb].get("ai") or {}
            if not ai.get("allowed"):
                bledy.append("tryb {} nie dopuszcza torów AI".format(tryb))
            elif len(role) > int(ai.get("maxChannels", 0)):
                bledy.append("przepływ używa {} ról, a tryb {} dopuszcza {} torów".format(
                    len(role), tryb, ai.get("maxChannels")))
            izolacja_trybu = tryby[tryb].get("isolation", "isolated")
            if izolacja_trybu not in SILA:
                bledy.append("tryb {} ma nieznany poziom izolacji {!r} w kontrakcie".format(tryb, izolacja_trybu))
                izolacja_trybu = "isolated"
            for r in role:
                iz = r.get("isolation")
                if iz not in SILA:
                    bledy.append("rola {}: nieznany poziom izolacji {!r}".format(r.get("role"), iz))
                elif SILA[iz] < SILA[izolacja_trybu]:
                    bledy.append("rola {}: izolacja {} słabsza niż izolacja trybu {} ({})".format(
                        r.get("role"), iz, tryb, izolacja_trybu))

    return bledy


def raport(przeplyw) -> str:
    out = []
    w = out.append
    kroki = {k["id"]: k for k in przeplyw.get("steps", [])}
    w("# Przepływ: {}".format(przeplyw.get("id", "?")))
    w("")
    w("**Cel.** {}".format(przeplyw.get("goal", "—")))
    w("")
    w("Tryb sesyjny: `{}`. Budżet: {} tokenów, {} godzin.".format(
        przeplyw.get("mode", "—"),
        przeplyw.get("budget", {}).get("totalTokens", "—"),
        przeplyw.get("budget", {}).get("wallClockHours", "—")))
    w("")
    w("## Role")
    w("")
    w("| Rola | Model | Izolacja | Budżet tokenów |")
    w("|---|---|---|---:|")
    for r in przeplyw.get("roles", []):
        w("| {} | `{}` | {} | {} |".format(r.get("role"), r.get("model", "—"),
                                           r.get("isolation", "—"), r.get("tokenBudget", "—")))
    w("")
    w("## Pętla")
    w("")
    w("```mermaid")
    w("graph TD")
    for kid, k in kroki.items():
        etykieta = "{}<br/>{}".format(kid, k.get("role", ""))
        if k.get("gate"):
            w('  {}{{"{}"}}'.format(kid, etykieta))
        elif k.get("terminal"):
            w('  {}(["{}"])'.format(kid, etykieta))
        else:
            w('  {}["{}"]'.format(kid, etykieta))
    for kid, k in kroki.items():
        for n in k.get("next", []):
            w("  {} --> {}".format(kid, n))
        if k.get("onReject"):
            w("  {} -.odrzucone.-> {}".format(kid, k["onReject"]))
    w("```")
    w("")
    w("Romb oznacza bramkę kontroli, zaokrąglenie - krok końcowy, linia przerywana - zawrót "
      "po odrzuceniu wyniku.")
    w("")
    w("## Warunki stopu")
    w("")
    w("| Warunek | Próg | Działanie |")
    w("|---|---|---|")
    for s in przeplyw.get("stop", []):
        w("| `{}` | {} | {} |".format(s.get("when"), s.get("threshold", "—"), s.get("action")))
    w("")
    for kid, k in kroki.items():
        if k.get("acceptance"):
            w("## Bramka akceptacji: {}".format(kid))
            w("")
            w("Pętla kończy się dopiero, gdy wszystkie poniższe polecenia zakończą się powodzeniem.")
            w("Ocena koordynatora nie zastępuje żadnego z nich.")
            w("")
            for polecenie in k["acceptance"]:
                w("- `{}`".format(polecenie))
            w("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Kontrola definicji pętli orkiestracji")
    ap.add_argument("command", choices=["validate", "report"])
    ap.add_argument("workflow", help="ścieżka do definicji przepływu (JSON)")
    ap.add_argument("--contract", default="shared/contract.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", help="plik wyjściowy dla report, względem --root")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    sciezka_przeplywu = Path(args.workflow)
    if not sciezka_przeplywu.is_absolute() and not sciezka_przeplywu.exists():
        sciezka_przeplywu = root / sciezka_przeplywu
    przeplyw = wczytaj(sciezka_przeplywu)
    sciezka_kontraktu = Path(args.contract)
    if not sciezka_kontraktu.is_absolute():
        sciezka_kontraktu = root / sciezka_kontraktu
    kontrakt = wczytaj(sciezka_kontraktu, wymagany=False)
    if kontrakt is None:
        print("UWAGA: nie znaleziono {} - pomijam kontrolę zgodności z macierzą trybów".format(
            sciezka_kontraktu), file=sys.stderr)

    bledy = sprawdz(przeplyw, kontrakt)
    if bledy:
        print("Przepływ narusza {} niezmienników:".format(len(bledy)), file=sys.stderr)
        for b in bledy:
            print("  - {}".format(b), file=sys.stderr)
        return EXIT_INVALID

    if args.command == "validate":
        print("Przepływ {!r} poprawny: {} ról, {} kroków, {} warunków stopu.".format(
            przeplyw.get("id"), len(przeplyw.get("roles", [])),
            len(przeplyw.get("steps", [])), len(przeplyw.get("stop", []))))
        return EXIT_OK

    md = raport(przeplyw)
    if args.out:
        cel = w_korzeniu(root, args.out, "--out")
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_text(md, encoding="utf-8")
        print("zapisano {}".format(cel), file=sys.stderr)
    else:
        sys.stdout.write(md)
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_IO)
    except Exception as blad:  # noqa: BLE001 - kod 1 nie występuje w kontrakcie narzędzia
        print("BŁĄD: awaria narzędzia: {!r}".format(blad), file=sys.stderr)
        sys.exit(EXIT_IO)
