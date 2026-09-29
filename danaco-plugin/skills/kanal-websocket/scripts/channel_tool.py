#!/usr/bin/env python3
"""Generator rozdzielacza komunikatów kanału Danaco Console.

Z sekcji `messages` w shared/contract.json wytwarza:
  - server/internal/transport/dispatch_gen.go - interfejs Handler i wyczerpujący rozdzielacz
  - client/src/channel/dispatch_gen.ts        - interfejs ServerEvents i rozdzielacz po stronie klienta

Sens tego generowania: dodanie komunikatu do kontraktu ma **zepsuć kompilację** dopóki
ktoś go nie obsłuży. Rozdzielacz pisany ręcznie po prostu milczy na nieznany komunikat,
a milczenie w kanale jest najtrudniejszą do zdiagnozowania klasą usterek.

Podkomendy:
  gen    - generuje oba pliki
  check  - porównuje z dyskiem, błąd przy rozjeździe

Ścieżki wyjściowe: --go-out, --ts-out (domyślne jak wyżej). Import pakietu kontraktu
w Go i ścieżka importu contract.ts w TypeScripcie są wyliczane z sekcji `generated`
kontraktu, więc przeniesienie plików jest zmianą w JSON-ie, nie w narzędziu.

Kody wyjścia: 0 w porządku, 2 błąd kontraktu, 3 rozjazd, 4 błąd wejścia/wyjścia.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXIT_OK, EXIT_INVALID, EXIT_DRIFT, EXIT_IO = 0, 2, 3, 4
LIMIT_CZASU_GOFMT_S = 60

DO_SERWERA = ("clientToServer", "bidirectional")
DO_KLIENTA = ("serverToClient", "bidirectional")


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


def snake(nazwa: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nazwa).lower()


def drut(msg) -> str:
    """Nazwa na drucie - ta sama reguła co w contract_tool.py (`AiPrompt` w `ai` -> `ai.prompt`).

    Wspólny przedrostek nazwy i kanału jest odcinany; pole `wire` nadpisuje regułę.
    Obie kopie tej funkcji muszą dawać identyczny wynik, inaczej rozdzielacz nie
    rozpozna komunikatów wygenerowanych przez contract_tool.py.
    """
    if msg.get("wire"):
        return msg["wire"]
    kanal = msg["channel"]
    czesci = snake(msg["name"]).split("_")
    czesci_kanalu = kanal.split("_")
    if czesci[: len(czesci_kanalu)] == czesci_kanalu and len(czesci) > len(czesci_kanalu):
        czesci = czesci[len(czesci_kanalu):]
    return "{}.{}".format(kanal, ".".join(czesci))


def modul_go(root: Path) -> str:
    gomod = root / "go.mod"
    if gomod.exists():
        m = re.search(r"^module\s+(\S+)", gomod.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    print("UWAGA: brak go.mod w {} - przyjmuję moduł 'danacoconsole'".format(root), file=sys.stderr)
    return "danacoconsole"


def sciezka_importu_shared(kontrakt, modul: str) -> str:
    """Ścieżka importu pakietu kontraktu wyprowadzona z generated.go.path (np. shared/contract.go)."""
    go_path = kontrakt.get("generated", {}).get("go", {}).get("path", "shared/contract.go")
    katalog = Path(go_path).parent.as_posix()
    return modul if katalog in ("", ".") else "{}/{}".format(modul, katalog)


def sciezka_importu_ts(ts_out: str, kontrakt) -> str:
    """Względny import contract.ts z pliku rozdzielacza, wyliczony z obu ścieżek w kontrakcie."""
    ts_path = Path(kontrakt.get("generated", {}).get("ts", {}).get("path", "client/src/contract.ts"))
    rel = Path(os.path.relpath(ts_path.with_suffix(""), Path(ts_out).parent)).as_posix()
    return rel if rel.startswith(".") else "./" + rel


def render_go(kontrakt, import_shared: str, pakiet: str, pakiet_shared: str) -> str:
    do_serwera = [m for m in kontrakt.get("messages", []) if m["direction"] in DO_SERWERA]
    out = []
    w = out.append
    w("// Kod generowany automatycznie przez tools/channel_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json, sekcja messages.")
    w("")
    w("package {}".format(pakiet))
    w("")
    w("import (")
    w('\t"context"')
    w('\t"encoding/json"')
    w('\t"errors"')
    w('\t"fmt"')
    w("")
    w('\t"{}"'.format(import_shared))
    w(")")
    w("")
    w("// ErrUnknownMessage oznacza komunikat spoza kontraktu.")
    w('var ErrUnknownMessage = errors.New("komunikat spoza kontraktu")')
    w("")
    w("// ErrWrongDirection oznacza komunikat wysłany w stronę, w którą wysyłać go nie wolno.")
    w('var ErrWrongDirection = errors.New("komunikat wysłany w niedozwoloną stronę")')
    w("")
    w("// Handler obsługuje komunikaty przychodzące od klienta.")
    w("// Interfejs jest generowany, więc dopisanie komunikatu do kontraktu psuje kompilację")
    w("// każdej implementacji, dopóki nowy komunikat nie zostanie obsłużony. O to chodzi.")
    w("type Handler interface {")
    for msg in do_serwera:
        if msg.get("payload"):
            w("\tHandle{}(ctx context.Context, env {}.Envelope, p *{}.{}) error".format(
                msg["name"], pakiet_shared, pakiet_shared, msg["payload"]))
        else:
            w("\tHandle{}(ctx context.Context, env {}.Envelope) error".format(msg["name"], pakiet_shared))
    w("}")
    w("")
    w("// Dispatch rozdziela kopertę do właściwej metody obsługi.")
    w("// Sprawdza też kierunek: klient nie może podszyć się pod komunikat serwera.")
    w("func Dispatch(ctx context.Context, env {}.Envelope, h Handler) error {{".format(pakiet_shared))
    w("\tif dir, ok := {}.MessageDirection[env.Type]; !ok {{".format(pakiet_shared))
    w("\t\treturn fmt.Errorf(\"%w: %s\", ErrUnknownMessage, env.Type)")
    w('\t} else if dir == "serverToClient" {')
    w("\t\treturn fmt.Errorf(\"%w: %s\", ErrWrongDirection, env.Type)")
    w("\t}")
    w("")
    w("\tswitch env.Type {")
    for msg in do_serwera:
        w("\tcase {}.Msg{}:".format(pakiet_shared, msg["name"]))
        if msg.get("payload"):
            w("\t\tvar p {}.{}".format(pakiet_shared, msg["payload"]))
            w("\t\tif len(env.Payload) > 0 {")
            w("\t\t\tif err := json.Unmarshal(env.Payload, &p); err != nil {")
            w("\t\t\t\treturn fmt.Errorf(\"ładunek %s: %w\", env.Type, err)")
            w("\t\t\t}")
            w("\t\t}")
            w("\t\treturn h.Handle{}(ctx, env, &p)".format(msg["name"]))
        else:
            w("\t\treturn h.Handle{}(ctx, env)".format(msg["name"]))
    w("\t}")
    w("\treturn fmt.Errorf(\"%w: %s\", ErrUnknownMessage, env.Type)")
    w("}")
    w("")
    return "\n".join(out).rstrip() + "\n"


def render_ts(kontrakt, import_contract: str) -> str:
    do_klienta = [m for m in kontrakt.get("messages", []) if m["direction"] in DO_KLIENTA]
    typy = sorted({m["payload"] for m in do_klienta if m.get("payload")})
    out = []
    w = out.append
    w("// Kod generowany automatycznie przez tools/channel_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json, sekcja messages.")
    w("")
    w('import type {{ Envelope, MessageType }} from "{}";'.format(import_contract))
    if typy:
        w('import type {')
        for t in typy:
            w("  {},".format(t))
        w('}} from "{}";'.format(import_contract))
    w("")
    w("/** Zdarzenia przychodzące z rdzenia. Interfejs jest generowany, więc nowy komunikat")
    w(" *  w kontrakcie psuje kompilację, dopóki klient go nie obsłuży. */")
    w("export interface ServerEvents {")
    for msg in do_klienta:
        nazwa = "on" + msg["name"]
        if msg.get("payload"):
            w('  {}(env: Envelope, payload: {}): void;'.format(nazwa, msg["payload"]))
        else:
            w('  {}(env: Envelope): void;'.format(nazwa))
    w("}")
    w("")
    w("/** Rozdziela kopertę do właściwej metody. Nieznany komunikat trafia do onUnknown,")
    w(" *  bo starszy klient musi przeżyć nowszy rdzeń - milczące zignorowanie ukryłoby to. */")
    w("export function dispatchEnvelope(")
    w("  env: Envelope,")
    w("  handlers: ServerEvents,")
    w("  onUnknown?: (type: MessageType | string) => void,")
    w("): void {")
    w("  switch (env.type) {")
    for msg in do_klienta:
        w('    case "{}":'.format(drut(msg)))
        if msg.get("payload"):
            w('      handlers.on{}(env, env.payload as {});'.format(msg["name"], msg["payload"]))
        else:
            w('      handlers.on{}(env);'.format(msg["name"]))
        w("      return;")
    w("    default:")
    w("      onUnknown?.(env.type);")
    w("      return;")
    w("  }")
    w("}")
    w("")
    return "\n".join(out).rstrip() + "\n"


def gofmt(src: str):
    exe = shutil.which("gofmt")
    if not exe:
        return src, ("nie znaleziono gofmt w PATH - kod Go nie został sformatowany; "
                     "na maszynie z Go wynik będzie inny, co da fałszywy rozjazd")
    try:
        done = subprocess.run([exe], input=src, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=LIMIT_CZASU_GOFMT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return src, "gofmt nie wystartował ({}) - kod Go bez formatowania".format(exc)
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
    ap = argparse.ArgumentParser(description="Generator rozdzielacza komunikatów kanału")
    ap.add_argument("command", choices=["gen", "check"])
    ap.add_argument("--contract", default="shared/contract.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--go-out", default="server/internal/transport/dispatch_gen.go")
    ap.add_argument("--go-package", default="transport")
    ap.add_argument("--ts-out", default="client/src/channel/dispatch_gen.ts")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    sciezka = Path(args.contract)
    if not sciezka.is_absolute():
        sciezka = root / sciezka
    kontrakt = wczytaj(sciezka)
    if not kontrakt.get("messages"):
        print("BŁĄD: kontrakt nie deklaruje komunikatów - nie ma czego rozdzielać", file=sys.stderr)
        return EXIT_INVALID

    pakiet_shared = kontrakt.get("generated", {}).get("go", {}).get("package", "shared")
    go_src = render_go(kontrakt, sciezka_importu_shared(kontrakt, modul_go(root)), args.go_package, pakiet_shared)
    go_src, ostrzezenie = gofmt(go_src)
    if ostrzezenie:
        print("UWAGA: {}".format(ostrzezenie), file=sys.stderr)
    ts_src = render_ts(kontrakt, sciezka_importu_ts(args.ts_out, kontrakt))

    cele = ((w_korzeniu(root, args.go_out, "--go-out"), go_src),
            (w_korzeniu(root, args.ts_out, "--ts-out"), ts_src))

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
            print("ROZJAZD: {} nie odpowiada kontraktowi".format(sciezka_wy), file=sys.stderr)
            for i, linia in enumerate(difflib.unified_diff(
                    obecne.splitlines(), tresc.splitlines(),
                    fromfile="na dysku", tofile="z kontraktu", lineterm="", n=2)):
                if i > 40:
                    print("  ... (dalsze różnice pominięte)", file=sys.stderr)
                    break
                print("  {}".format(linia), file=sys.stderr)
    if rozjazd:
        print("\nUruchom: task channel", file=sys.stderr)
        return EXIT_DRIFT
    print("Bez rozjazdu: rozdzielacze zgodne z kontraktem.")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_IO)
    except Exception as blad:  # noqa: BLE001 - kod 1 nie występuje w kontrakcie narzędzia
        print("BŁĄD: awaria narzędzia: {!r}".format(blad), file=sys.stderr)
        sys.exit(EXIT_IO)
