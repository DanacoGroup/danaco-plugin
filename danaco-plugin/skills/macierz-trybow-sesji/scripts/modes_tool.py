#!/usr/bin/env python3
"""Narzędzie macierzy trybów sesyjnych Danaco Console.

Czyta shared/contract.json i pilnuje niezmienników, których sam kontrakt nie sprawdza:
kto co widzi, kto do czego pisze i ile torów AI wolno podłączyć w danym trybie.

Podkomendy:
  validate  - kontrola niezmienników macierzy, nic nie zapisuje
  report    - macierz środowisko x moduł oraz diagram widoczności (Markdown + Mermaid)
  gen       - generuje shared/scopes.go i client/src/scopes.ts z tablicami zakresów
  check     - porównuje wygenerowane tablice z macierzą; błąd przy rozjeździe

Kody wyjścia: 0 w porządku, 2 naruszenie niezmiennika, 3 rozjazd, 4 błąd wejścia/wyjścia.

Podkomendy `validate` i `check` pilnują dwóch różnych rzeczy i żadna nie zastępuje drugiej:
`validate` mówi, czy macierz jest sensowna, `check` - czy kod ją odwzorowuje. Sama walidacja
przepuściłaby poprawiony kontrakt z niezregenerowanymi tablicami widoczności, a to znaczy
izolację, która wygląda na wprowadzoną i nie działa.

Zależności: wyłącznie biblioteka standardowa Pythona 3.9+.
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

EXIT_OK, EXIT_INVALID, EXIT_DRIFT, EXIT_IO = 0, 2, 3, 4
LIMIT_CZASU_GOFMT_S = 60

# Siła izolacji rośnie w prawo. Tor AI nie może być słabiej izolowany niż tryb,
# w którym działa - inaczej podłączenie modelu obchodziłoby izolację trybu.
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


def pascal(nazwa: str) -> str:
    import re
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-.\s]+", nazwa) if p)


def rozwiaz_zakresy(kontrakt):
    """Uzupełnia domyślne zakresy widoczności.

    Domyślne wartości są celowo wąskie. Tryb, który potrzebuje szerszego widoku,
    musi go zadeklarować - w systemie z danymi objętymi tajemnicą zawodową milcząco
    szeroki domyślny zakres jest najkrótszą drogą do wycieku między sprawami.
    """
    tryby = {m["id"]: m for m in kontrakt.get("modes", [])}
    wg_srodowiska = defaultdict(list)
    for m in tryby.values():
        wg_srodowiska[m["environment"]].append(m["id"])

    zakresy = {}
    for mid, m in tryby.items():
        izolacja = m.get("isolation", "isolated")
        wspolne_w_srodowisku = [i for i in wg_srodowiska[m["environment"]]
                                if tryby[i].get("isolation") == "shared"]
        if izolacja == "shared":
            domyslne_czyta = sorted(set(wspolne_w_srodowisku) | {mid})
        elif izolacja == "hybrid":
            domyslne_czyta = sorted(set(wspolne_w_srodowisku) | {mid})
        else:
            domyslne_czyta = [mid]
        ai = m.get("ai") or {}
        zakresy[mid] = {
            "id": mid,
            "environment": m["environment"],
            "module": m["module"],
            "isolation": izolacja,
            "reads": sorted(set(m.get("reads", domyslne_czyta))),
            "writes": sorted(set(m.get("writes", [mid]))),
            "aiAllowed": bool(ai.get("allowed", False)),
            "aiMaxChannels": int(ai.get("maxChannels") or 0),
            "aiIsolation": ai.get("isolation", izolacja),
        }
    return tryby, zakresy


def sprawdz(kontrakt, min_modulow, max_modulow, max_torow):
    bledy = []
    tryby, zakresy = rozwiaz_zakresy(kontrakt)
    if not tryby:
        return ["kontrakt nie zawiera sekcji modes - macierz trybów nie istnieje"], zakresy

    # Nieznany poziom izolacji unieważnia resztę kontroli tego trybu (i wywracałby raport),
    # więc jest zgłaszany od razu, a tryb dostaje na czas kontroli najostrzejszy poziom.
    for mid, z in sorted(zakresy.items()):
        if z["isolation"] not in SILA:
            bledy.append("tryb {}: nieznany poziom izolacji {!r}; dopuszczalne: {}".format(
                mid, z["isolation"], ", ".join(SILA)))
            z["isolation"] = "isolated"
        if z["aiIsolation"] not in SILA:
            bledy.append("tryb {}: nieznany poziom izolacji toru AI {!r}; dopuszczalne: {}".format(
                mid, z["aiIsolation"], ", ".join(SILA)))
            z["aiIsolation"] = "isolated"

    wg_srodowiska = defaultdict(list)
    for m in tryby.values():
        wg_srodowiska[m["environment"]].append(m["id"])

    for srodowisko, lista in sorted(wg_srodowiska.items()):
        if not min_modulow <= len(lista) <= max_modulow:
            bledy.append("środowisko {}: {} modułów, a umowa projektowa mówi o {}-{}".format(
                srodowisko, len(lista), min_modulow, max_modulow))

    # Most jest wyjątkiem od niezależności środowisk: ma kierunek (from czyta to),
    # uzasadnienie i prowadzi wyłącznie do trybu współdzielonego po drugiej stronie.
    mosty = set()
    for most in kontrakt.get("modeBridges", []):
        skad, dokad = most.get("from"), most.get("to")
        if not most.get("reason"):
            bledy.append("most {} -> {}: brak pola reason; przejście między środowiskami "
                         "wymaga uzasadnienia".format(skad, dokad))
        if skad not in tryby or dokad not in tryby:
            bledy.append("most {} -> {}: wskazuje nieistniejący tryb".format(skad, dokad))
            continue
        if tryby[skad]["environment"] == tryby[dokad]["environment"]:
            bledy.append("most {} -> {}: oba tryby są w tym samym środowisku - most jest zbędny, "
                         "użyj pola reads".format(skad, dokad))
        if zakresy[dokad]["isolation"] != "shared":
            bledy.append("most {} -> {}: most może prowadzić wyłącznie do trybu shared, "
                         "a {} jest {}".format(skad, dokad, dokad, zakresy[dokad]["isolation"]))
        if (skad, dokad) in mosty:
            bledy.append("most {} -> {}: zadeklarowany dwa razy".format(skad, dokad))
        mosty.add((skad, dokad))

    for mid, z in sorted(zakresy.items()):
        if mid not in z["reads"]:
            bledy.append("tryb {}: nie czyta własnego stanu - to zawsze jest błąd macierzy".format(mid))
        for cel in z["reads"]:
            if cel not in tryby:
                bledy.append("tryb {}: czyta z nieistniejącego trybu {!r}".format(mid, cel))
                continue
            if tryby[cel]["environment"] != z["environment"] and (mid, cel) not in mosty:
                bledy.append("tryb {}: czyta z {} w innym środowisku bez wpisu w modeBridges".format(mid, cel))
            if cel != mid and zakresy[cel]["isolation"] == "isolated":
                bledy.append("tryb {}: czyta z trybu izolowanego {} - izolacja przestaje "
                             "cokolwiek znaczyć".format(mid, cel))
        for cel in z["writes"]:
            if cel not in tryby:
                bledy.append("tryb {}: pisze do nieistniejącego trybu {!r}".format(mid, cel))
                continue
            if cel == mid:
                continue
            if z["isolation"] in ("isolated", "hybrid"):
                bledy.append("tryb {} ({}): pisze do {} poza własną przestrzenią".format(
                    mid, z["isolation"], cel))
            elif tryby[cel]["environment"] != z["environment"]:
                bledy.append("tryb {}: pisze do {} w innym środowisku - most pozwala czytać, "
                             "nigdy pisać".format(mid, cel))
            elif zakresy[cel]["isolation"] != "shared":
                bledy.append("tryb {}: pisze do {} o izolacji {} - zapis poza własną przestrzenią "
                             "jest dozwolony tylko między trybami shared".format(
                                 mid, cel, zakresy[cel]["isolation"]))
        if not z["writes"]:
            bledy.append("tryb {}: pusta lista writes - tryb, który do niczego nie pisze, "
                         "jest albo martwy, albo niedopowiedziany".format(mid))
        elif mid not in z["writes"]:
            bledy.append("tryb {}: nie pisze do własnej przestrzeni".format(mid))

        if z["aiAllowed"]:
            if z["aiMaxChannels"] < 1:
                bledy.append("tryb {}: AI dozwolone, ale maxChannels wynosi {}".format(mid, z["aiMaxChannels"]))
            if z["aiMaxChannels"] > max_torow:
                bledy.append("tryb {}: maxChannels {} przekracza projektowy limit {}".format(
                    mid, z["aiMaxChannels"], max_torow))
            if SILA[z["aiIsolation"]] < SILA[z["isolation"]]:
                bledy.append("tryb {}: tor AI ({}) jest słabiej izolowany niż tryb ({}) - "
                             "podłączenie modelu obchodziłoby izolację".format(
                                 mid, z["aiIsolation"], z["isolation"]))
        elif z["aiMaxChannels"]:
            bledy.append("tryb {}: maxChannels ustawione, ale AI nie jest dozwolone".format(mid))

    return bledy, zakresy


def raport(kontrakt, zakresy) -> str:
    out = []
    w = out.append
    wg = defaultdict(dict)
    for mid, z in zakresy.items():
        wg[z["environment"]][z["module"]] = z

    w("# Macierz trybów sesyjnych")
    w("")
    w("Plik generowany przez `modes_tool.py`. Nie edytuj ręcznie.")
    w("")
    w("Środowisk: **{}**, trybów: **{}**.".format(len(wg), len(zakresy)))
    w("")
    for srodowisko in sorted(wg):
        w("## {}".format(srodowisko))
        w("")
        w("| Moduł | Izolacja | Czyta z | Pisze do | Tory AI |")
        w("|---|---|---:|---:|---|")
        for modul in sorted(wg[srodowisko]):
            z = wg[srodowisko][modul]
            ai = "{} x {}".format(z["aiMaxChannels"], z["aiIsolation"]) if z["aiAllowed"] else "—"
            w("| `{}` | {} | {} | {} | {} |".format(
                modul, z["isolation"], len(z["reads"]), len(z["writes"]), ai))
        w("")

    w("## Widoczność między trybami")
    w("")
    w("Strzałka prowadzi od trybu czytającego do trybu, z którego czyta. Tryb bez strzałek "
      "przychodzących jest w pełni izolowany.")
    w("")
    w("```mermaid")
    w("graph LR")
    skroty = {mid: "m{}".format(i) for i, mid in enumerate(sorted(zakresy))}
    for srodowisko in sorted(wg):
        w('  subgraph {}["{}"]'.format(srodowisko, srodowisko))
        for modul in sorted(wg[srodowisko]):
            z = wg[srodowisko][modul]
            znak = {"shared": "", "hybrid": "~", "isolated": "!"}.get(z["isolation"], "?")
            w('    {}["{}{}"]'.format(skroty[z["id"]], znak, modul))
        w("  end")
    for mid, z in sorted(zakresy.items()):
        for cel in z["reads"]:
            if cel != mid and cel in skroty:
                w("  {} --> {}".format(skroty[mid], skroty[cel]))
    w("```")
    w("")
    w("Oznaczenia: `!` tryb izolowany, `~` hybrydowy, bez znaku - współdzielony.")
    w("")

    z_ai = [z for z in zakresy.values() if z["aiAllowed"]]
    if z_ai:
        w("## Tryby dopuszczające tory AI")
        w("")
        w("| Tryb | Izolacja trybu | Izolacja toru AI | Maksymalnie torów |")
        w("|---|---|---|---:|")
        for z in sorted(z_ai, key=lambda x: x["id"]):
            w("| `{}` | {} | {} | {} |".format(z["id"], z["isolation"], z["aiIsolation"], z["aiMaxChannels"]))
        w("")
        w("Izolacja toru AI nigdy nie jest słabsza od izolacji trybu. Gdyby była, podłączenie "
          "modelu byłoby obejściem granicy, którą tryb miał wyznaczać.")
        w("")
    return "\n".join(out) + "\n"


def render_go(kontrakt, zakresy, pakiet: str) -> str:
    out = []
    w = out.append
    w("// Kod generowany automatycznie przez tools/modes_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json, sekcje modes i modeBridges.")
    w("")
    w("package {}".format(pakiet))
    w("")
    w("// ModeScope opisuje, co dany tryb widzi i do czego pisze.")
    w("type ModeScope struct {")
    w("\tReads         []ModeID")
    w("\tWrites        []ModeID")
    w("\tAIAllowed     bool")
    w("\tAIMaxChannels int")
    w("\tAIIsolation   IsolationLevel")
    w("}")
    w("")
    w("// ModeScopes to macierz widoczności wyprowadzona z kontraktu.")
    w("var ModeScopes = map[ModeID]ModeScope{")
    for mid, z in sorted(zakresy.items()):
        czyta = ", ".join('"{}"'.format(x) for x in z["reads"])
        pisze = ", ".join('"{}"'.format(x) for x in z["writes"])
        w('\t"{}": {{Reads: []ModeID{{{}}}, Writes: []ModeID{{{}}}, AIAllowed: {}, '
          'AIMaxChannels: {}, AIIsolation: "{}"}},'.format(
              mid, czyta, pisze, "true" if z["aiAllowed"] else "false",
              z["aiMaxChannels"], z["aiIsolation"]))
    w("}")
    w("")
    w("// CanRead mówi, czy tryb from ma prawo czytać stan trybu to.")
    w("// Wołaj to przy każdym wejściu do warstwy danych, nie tylko w interfejsie -")
    w("// kontrola po stronie interfejsu chroni przed pomyłką, nie przed obejściem.")
    w("func CanRead(from, to ModeID) bool {")
    w("\tscope, ok := ModeScopes[from]")
    w("\tif !ok {")
    w("\t\treturn false")
    w("\t}")
    w("\tfor _, id := range scope.Reads {")
    w("\t\tif id == to {")
    w("\t\t\treturn true")
    w("\t\t}")
    w("\t}")
    w("\treturn false")
    w("}")
    w("")
    w("// CanWrite mówi, czy tryb mode ma prawo zapisywać w przestrzeni trybu target.")
    w("func CanWrite(mode, target ModeID) bool {")
    w("\tscope, ok := ModeScopes[mode]")
    w("\tif !ok {")
    w("\t\treturn false")
    w("\t}")
    w("\tfor _, id := range scope.Writes {")
    w("\t\tif id == target {")
    w("\t\t\treturn true")
    w("\t\t}")
    w("\t}")
    w("\treturn false")
    w("}")
    w("")
    w("// AIChannelAllowed mówi, czy w danym trybie wolno otworzyć kolejny tor AI.")
    w("// Argument open to liczba torów już otwartych w tej sesji.")
    w("func AIChannelAllowed(mode ModeID, open int) bool {")
    w("\tscope, ok := ModeScopes[mode]")
    w("\tif !ok || !scope.AIAllowed {")
    w("\t\treturn false")
    w("\t}")
    w("\treturn open < scope.AIMaxChannels")
    w("}")
    w("")
    return "\n".join(out).rstrip() + "\n"


def render_ts(zakresy) -> str:
    out = []
    w = out.append
    w("// Kod generowany automatycznie przez tools/modes_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json, sekcje modes i modeBridges.")
    w("")
    w('import type { ModeId } from "./contract";')
    w("")
    w("export interface ModeScope {")
    w("  reads: ModeId[];")
    w("  writes: ModeId[];")
    w("  aiAllowed: boolean;")
    w("  aiMaxChannels: number;")
    w("  aiIsolation: string;")
    w("}")
    w("")
    w("/** Macierz widoczności wyprowadzona z kontraktu. */")
    w("export const MODE_SCOPES: Record<ModeId, ModeScope> = {")
    for mid, z in sorted(zakresy.items()):
        czyta = ", ".join('"{}"'.format(x) for x in z["reads"])
        pisze = ", ".join('"{}"'.format(x) for x in z["writes"])
        w('  "{}": {{ reads: [{}], writes: [{}], aiAllowed: {}, aiMaxChannels: {}, '
          'aiIsolation: "{}" }},'.format(mid, czyta, pisze,
                                         "true" if z["aiAllowed"] else "false",
                                         z["aiMaxChannels"], z["aiIsolation"]))
    w("};")
    w("")
    w("/** Czy tryb `from` widzi stan trybu `to`. Kontrola w interfejsie chroni przed pomyłką;")
    w(" *  właściwą granicę wyznacza ta sama kontrola po stronie rdzenia. */")
    w("export function canRead(from: ModeId, to: ModeId): boolean {")
    w("  return MODE_SCOPES[from]?.reads.includes(to) ?? false;")
    w("}")
    w("")
    w("export function canWrite(mode: ModeId, target: ModeId): boolean {")
    w("  return MODE_SCOPES[mode]?.writes.includes(target) ?? false;")
    w("}")
    w("")
    w("export function aiChannelAllowed(mode: ModeId, open: number): boolean {")
    w("  const s = MODE_SCOPES[mode];")
    w("  return !!s && s.aiAllowed && open < s.aiMaxChannels;")
    w("}")
    w("")
    return "\n".join(out).rstrip() + "\n"


def gofmt(src: str, narzedzie: str = "gofmt"):
    exe = shutil.which(narzedzie)
    if not exe:
        return src, "nie znaleziono {} w PATH - kod Go nie został sformatowany".format(narzedzie)
    try:
        done = subprocess.run([exe], input=src, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=LIMIT_CZASU_GOFMT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return src, "gofmt nie wystartował ({})".format(exc)
    if done.returncode != 0:
        return src, "gofmt zgłosił błąd: {}".format(done.stderr.strip()[:400])
    return done.stdout, None


def wczytaj_wygenerowany(sciezka: Path) -> str:
    """Treść pliku wygenerowanego wcześniej; pliku nieczytelnego jako UTF-8 nie da
    się porównać, więc jest zgłaszany jako rozjazd, nie traceback."""
    if not sciezka.exists():
        return ""
    try:
        return sciezka.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as blad:
        print("ROZJAZD: {} nie da się odczytać jako UTF-8 ({})".format(sciezka, blad), file=sys.stderr)
        return "\0"


def main() -> int:
    ap = argparse.ArgumentParser(description="Kontrola i generowanie macierzy trybów sesyjnych")
    ap.add_argument("command", choices=["validate", "report", "gen", "check"])
    ap.add_argument("--contract", default="shared/contract.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", help="plik wyjściowy dla report, względem --root (domyślnie standardowe wyjście)")
    ap.add_argument("--min-modules", type=int, default=8)
    ap.add_argument("--max-modules", type=int, default=10)
    ap.add_argument("--max-ai-channels", type=int, default=4)
    ap.add_argument("--go-out", default="shared/scopes.go")
    ap.add_argument("--ts-out", default="client/src/scopes.ts")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    sciezka = Path(args.contract)
    if not sciezka.is_absolute():
        sciezka = root / sciezka
    kontrakt = wczytaj(sciezka)

    bledy, zakresy = sprawdz(kontrakt, args.min_modules, args.max_modules, args.max_ai_channels)
    if bledy:
        print("Macierz trybów narusza {} niezmienników:".format(len(bledy)), file=sys.stderr)
        for b in bledy:
            print("  - {}".format(b), file=sys.stderr)
        return EXIT_INVALID

    if args.command == "validate":
        srodowiska = {z["environment"] for z in zakresy.values()}
        z_ai = sum(1 for z in zakresy.values() if z["aiAllowed"])
        print("Macierz poprawna: {} środowisk, {} trybów, {} z torami AI.".format(
            len(srodowiska), len(zakresy), z_ai))
        return EXIT_OK

    if args.command == "report":
        md = raport(kontrakt, zakresy)
        if args.out:
            cel = w_korzeniu(root, args.out, "--out")
            cel.parent.mkdir(parents=True, exist_ok=True)
            cel.write_text(md, encoding="utf-8")
            print("zapisano {}".format(cel), file=sys.stderr)
        else:
            sys.stdout.write(md)
        return EXIT_OK

    pakiet = kontrakt.get("generated", {}).get("go", {}).get("package", "shared")
    go_src, ostrzezenie = gofmt(render_go(kontrakt, zakresy, pakiet))
    if ostrzezenie:
        print("UWAGA: {}".format(ostrzezenie), file=sys.stderr)
    cele = ((w_korzeniu(root, args.go_out, "--go-out"), go_src),
            (w_korzeniu(root, args.ts_out, "--ts-out"), render_ts(zakresy)))

    if args.command == "gen":
        for sciezka_wy, tresc in cele:
            sciezka_wy.parent.mkdir(parents=True, exist_ok=True)
            sciezka_wy.write_text(tresc, encoding="utf-8")
            print("zapisano {}".format(sciezka_wy))
        return EXIT_OK

    rozjazd = False
    for sciezka_wy, tresc in cele:
        obecne = wczytaj_wygenerowany(sciezka_wy)
        if obecne != tresc:
            rozjazd = True
            print("ROZJAZD: {} nie odpowiada macierzy trybów".format(sciezka_wy), file=sys.stderr)
            for i, linia in enumerate(difflib.unified_diff(
                    obecne.splitlines(), tresc.splitlines(),
                    fromfile="na dysku", tofile="z kontraktu", lineterm="", n=2)):
                if i > 40:
                    print("  ... (dalsze różnice pominięte)", file=sys.stderr)
                    break
                print("  {}".format(linia), file=sys.stderr)
    if rozjazd:
        print("\nUruchom: task modes", file=sys.stderr)
        return EXIT_DRIFT
    print("Bez rozjazdu: tablice widoczności zgodne z macierzą trybów.")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_IO)
    except Exception as blad:  # noqa: BLE001 - kod 1 nie występuje w kontrakcie narzędzia
        print("BŁĄD: awaria narzędzia: {!r}".format(blad), file=sys.stderr)
        sys.exit(EXIT_IO)
