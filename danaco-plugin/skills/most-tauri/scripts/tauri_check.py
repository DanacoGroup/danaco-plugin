#!/usr/bin/env python3
"""Kontrola granicy Tauri w Danaco Console.

Sprawdza zgodność trzech miejsc, które muszą mówić to samo, a nie mają wspólnego kompilatora:
  - sekcja `commands` w shared/contract.json
  - funkcje `#[tauri::command]` w desktop/src-tauri/src/**/*.rs
  - lista w `tauri::generate_handler![...]`

oraz przegląda konfigurację powłoki pod kątem ustawień, które otwierają powierzchnię ataku.

Użycie:
    python3 tauri_check.py --root .
    python3 tauri_check.py --root . --tauri-dir desktop/src-tauri

Kody wyjścia: 0 w porządku, 2 znalezione niezgodności, 4 błąd wejścia/wyjścia.
Zależności: wyłącznie biblioteka standardowa Pythona 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_OK, EXIT_INVALID, EXIT_IO = 0, 2, 4

KOMENDA = re.compile(
    r"#\[tauri::command[^\]]*\]\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)", re.S)
HANDLER = re.compile(r"generate_handler!\s*\[([^\]]*)\]", re.S)
# Zakres z symbolem wieloznacznym obejmujący całe poddrzewo albo dowolną ścieżkę.
# Wąskie wzorce w rodzaju "*.pdf" nie są tu problemem, więc ich nie zgłaszamy.
SZEROKI_ZAKRES = re.compile(r'"(?:\*\*?|\*\*/\*|/\*\*(?:/\*)?|\$[A-Z]+/\*\*(?:/\*)?)"')
# Linie zakomentowane pomijamy - komenda w komentarzu nie istnieje dla kompilatora,
# a bez tego narzędzie zgłasza rozjazd, którego nie ma.
KOMENTARZ_LINIOWY = re.compile(r"^\s*//.*$", re.M)
KOMENTARZ_BLOKOWY = re.compile(r"/\*.*?\*/", re.S)
# Literał Rusta (zwykły i surowy). Bez wycięcia go wystąpienie "/*" w łańcuchu
# zjadało kod do najbliższego "*/", więc komendy za nim przestawały być widoczne.
LANCUCH_RUST = re.compile(r'r#*"(?:[^"]|"(?!#))*"#*|"(?:\\.|[^"\\])*"', re.S)

DYREKTYWY_SKRYPTOWE = ("script-src", "script-src-elem", "default-src", "worker-src")


def bez_komentarzy(tresc: str) -> str:
    bez_lancuchow = LANCUCH_RUST.sub('""', tresc)
    return KOMENTARZ_LINIOWY.sub("", KOMENTARZ_BLOKOWY.sub("", bez_lancuchow))


def dyrektywy_csp(tekst: str) -> dict:
    """Polityka CSP rozbita na dyrektywy. Kolejność dyrektyw w CSP jest dowolna,
    więc szukanie 'unsafe-inline' w tekście przed pierwszym `style-src`
    przepuszczało `script-src 'unsafe-inline'` postawione dalej."""
    wynik = {}
    for fragment in tekst.split(";"):
        czesci = fragment.split()
        if czesci:
            wynik[czesci[0].lower()] = " ".join(czesci[1:])
    return wynik


def wczytaj_json(sciezka: Path, wymagany=True):
    if not sciezka.exists():
        if wymagany:
            print("BŁĄD: nie znaleziono {}".format(sciezka), file=sys.stderr)
            sys.exit(EXIT_IO)
        return None
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


def zbierz_rust(katalog: Path):
    komendy, handlery, pliki = {}, set(), []
    src = katalog / "src"
    if not src.is_dir():
        return komendy, handlery, pliki
    for plik in sorted(src.rglob("*.rs")):
        tresc = bez_komentarzy(plik.read_text(encoding="utf-8", errors="replace"))
        pliki.append(plik)
        for nazwa in KOMENDA.findall(tresc):
            komendy[nazwa] = plik
        for blok in HANDLER.findall(tresc):
            for wpis in blok.split(","):
                wpis = wpis.strip().split("::")[-1]
                if wpis:
                    handlery.add(wpis)
    return komendy, handlery, pliki


def main() -> int:
    ap = argparse.ArgumentParser(description="Kontrola granicy Tauri wobec kontraktu")
    ap.add_argument("--root", default=".")
    ap.add_argument("--contract", default="shared/contract.json")
    ap.add_argument("--tauri-dir", default="desktop/src-tauri")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    kontrakt = wczytaj_json(root / args.contract)
    tauri_dir = root / args.tauri_dir

    if not tauri_dir.is_dir():
        print("BŁĄD: nie znaleziono katalogu powłoki {}".format(tauri_dir), file=sys.stderr)
        return EXIT_IO

    bledy, uwagi = [], []

    komendy_kontraktu = kontrakt.get("commands", [])
    if not isinstance(komendy_kontraktu, list):
        komendy_kontraktu = []
    z_kontraktu = {c["name"]: c for c in komendy_kontraktu
                   if isinstance(c, dict) and str(c.get("name", "")).strip()}
    if len(z_kontraktu) != len(komendy_kontraktu):
        bledy.append("kontrakt zawiera pozycje w commands bez pola name - nie da się ich "
                     "porównać z powłoką")
    komendy, handlery, pliki = zbierz_rust(tauri_dir)

    if not pliki:
        uwagi.append("w {}/src nie ma plików Rust - powłoka jeszcze nie istnieje".format(args.tauri_dir))

    if komendy and not handlery:
        bledy.append("w powłoce są funkcje #[tauri::command], ale nigdzie nie ma "
                     "generate_handler! - żadna z nich nie jest widoczna z interfejsu")

    for nazwa in sorted(z_kontraktu):
        if nazwa not in komendy:
            bledy.append("komenda {!r} jest w kontrakcie, ale nie ma dla niej funkcji "
                         "#[tauri::command] w powłoce".format(nazwa))
        elif handlery and nazwa not in handlery:
            bledy.append("komenda {!r} istnieje w Rust, ale nie jest wymieniona w generate_handler! "
                         "- z interfejsu będzie niewidoczna".format(nazwa))

    for nazwa in sorted(handlery - set(komendy)):
        uwagi.append("generate_handler! wymienia {!r}, dla którego nie widać funkcji "
                     "#[tauri::command] - sprawdź, czy nazwa nie została zmieniona".format(nazwa))
    for nazwa, plik in sorted(komendy.items()):
        if nazwa not in z_kontraktu:
            bledy.append("komenda {!r} ({}) nie jest zadeklarowana w kontrakcie - interfejs nie ma "
                         "z niej typowanego wywołania".format(nazwa, plik.relative_to(root)))

    conf = wczytaj_json(tauri_dir / "tauri.conf.json", wymagany=False)
    if conf is None:
        uwagi.append("brak {}/tauri.conf.json - pomijam przegląd konfiguracji".format(args.tauri_dir))
    else:
        app = conf.get("app", {})
        security = app.get("security", {})
        csp = security.get("csp")
        if not csp:
            bledy.append("app.security.csp jest puste - powłoka ładuje treść bez polityki "
                         "bezpieczeństwa; przy renderowaniu treści pism to realne ryzyko")
        else:
            # CSP bywa obiektem (dyrektywa -> wartość) albo jednym łańcuchem znaków.
            tekst_csp = csp if isinstance(csp, str) else " ".join(
                "{} {}".format(k, v if isinstance(v, str) else " ".join(v)) for k, v in csp.items())
            dyrektywy = dyrektywy_csp(tekst_csp)
            niebezpieczne = [nazwa for nazwa in DYREKTYWY_SKRYPTOWE
                             if "'unsafe-inline'" in dyrektywy.get(nazwa, "")
                             or "'unsafe-eval'" in dyrektywy.get(nazwa, "")]
            if niebezpieczne:
                bledy.append("app.security.csp dopuszcza 'unsafe-eval' albo 'unsafe-inline' w {} "
                             "- to znosi ochronę, dla której CSP tu jest".format(", ".join(niebezpieczne)))
            if "ipc:" not in tekst_csp and "ipc.localhost" not in tekst_csp:
                uwagi.append("app.security.csp nie wymienia origin IPC (ipc: http://ipc.localhost) "
                             "w connect-src - wywołania komend mogą zostać zablokowane")
            if "default-src" not in tekst_csp:
                uwagi.append("app.security.csp nie ma dyrektywy default-src - reszta polityki "
                             "nie ma domyślnego oparcia")
        if app.get("withGlobalTauri"):
            bledy.append("app.withGlobalTauri jest włączone - udostępnia most każdemu skryptowi "
                         "w oknie; wyłącz i wołaj przez import")
        if security.get("dangerousDisableAssetCspModification"):
            bledy.append("włączone dangerousDisableAssetCspModification - Tauri przestaje dokładać "
                         "do CSP własne nonce i skróty")
        bundle = conf.get("bundle", {})
        if not bundle.get("externalBin"):
            uwagi.append("bundle.externalBin jest puste - jeśli rdzeń Go ma jechać w instalatorze "
                         "jako proces poboczny, musi być tu wymieniony")

    kat_cap = tauri_dir / "capabilities"
    if not kat_cap.is_dir():
        uwagi.append("brak katalogu {}/capabilities".format(args.tauri_dir))
    else:
        pliki_cap = sorted(kat_cap.glob("*.json"))
        if not pliki_cap:
            uwagi.append("katalog capabilities jest pusty")
        for plik in pliki_cap:
            tresc = plik.read_text(encoding="utf-8", errors="replace")
            if SZEROKI_ZAKRES.search(tresc):
                bledy.append("{}: zakres z symbolem wieloznacznym - uprawnienie obejmuje więcej, "
                             "niż ktokolwiek zamierzał".format(plik.relative_to(root)))
            dane = wczytaj_json(plik, wymagany=False) or {}
            if not dane.get("windows") and not dane.get("webviews"):
                uwagi.append("{}: brak listy windows - uprawnienie obejmuje wtedy wszystkie okna".format(
                    plik.relative_to(root)))
            for uprawnienie in dane.get("permissions", []):
                nazwa = uprawnienie if isinstance(uprawnienie, str) else uprawnienie.get("identifier", "")
                if nazwa.startswith(("shell:allow-execute", "shell:allow-spawn")) or nazwa == "shell:default":
                    bledy.append("{}: uprawnienie {!r} pozwala uruchamiać programy z okna; "
                                 "rdzeń Go uruchamiaj z warstwy Rust, nie z interfejsu".format(
                                     plik.relative_to(root), nazwa))
                if nazwa in ("fs:default", "fs:allow-read-recursive", "fs:allow-write-recursive",
                             "fs:allow-full-access"):
                    bledy.append("{}: uprawnienie {!r} daje szeroki dostęp do plików; "
                                 "wypisz konkretne katalogi w zakresie".format(
                                     plik.relative_to(root), nazwa))
                ma_zakres = isinstance(uprawnienie, dict) and uprawnienie.get("scope")
                if nazwa.startswith("fs:allow") and not ma_zakres:
                    uwagi.append("{}: uprawnienie {!r} bez widocznego zakresu".format(
                        plik.relative_to(root), nazwa))

    if uwagi:
        print("Uwagi ({}):".format(len(uwagi)))
        for u in uwagi:
            print("  ~ {}".format(u))
        print()
    if bledy:
        print("Granica Tauri: {} niezgodności".format(len(bledy)), file=sys.stderr)
        for b in bledy:
            print("  - {}".format(b), file=sys.stderr)
        return EXIT_INVALID

    print("Granica Tauri w porządku: {} komend w kontrakcie, {} w powłoce, {} w generate_handler!.".format(
        len(z_kontraktu), len(komendy), len(handlery)))
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_IO)
    except Exception as blad:  # noqa: BLE001 - kod 1 nie występuje w kontrakcie narzędzia
        print("BŁĄD: awaria narzędzia: {!r}".format(blad), file=sys.stderr)
        sys.exit(EXIT_IO)
