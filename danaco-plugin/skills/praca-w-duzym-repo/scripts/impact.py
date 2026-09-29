#!/usr/bin/env python3
"""Zasięg zmiany w repozytorium Danaco Console.

Odpowiada na pytanie: "zmieniłem te pliki - co jeszcze może przestać działać
i co trzeba przetestować?". Liczy domknięcie zwrotne grafu zależności
pakietów Go i modułów TypeScriptu, po czym wypisuje gotowe polecenia.

Użycie:
    python3 impact.py --root . --base main
    python3 impact.py --root . --staged
    python3 impact.py --root . --changed server/internal/session/store.go client/src/shell.ts

Zależności: biblioteka standardowa Pythona 3.9+ oraz git (tylko dla --base/--staged).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "target", "dist", "build", "vendor", ".venv", "venv",
    "__pycache__", ".next", ".turbo", "coverage",
}

GO_IMPORT_BLOCK = re.compile(r"^import\s*\(([^)]*)\)", re.M | re.S)
GO_IMPORT_ONE = re.compile(r'^import\s+(?:\w+\s+)?"([^"]+)"', re.M)
GO_IMPORT_LINE = re.compile(r'^\s*(?:[\w.]+\s+)?"([^"]+)"', re.M)
TS_IMPORT = re.compile(r'(?:^|\n)\s*(?:import|export)[^;\n]*?from\s+["\']([^"\']+)["\']')
TS_DYNAMIC = re.compile(r'import\(\s*["\']([^"\']+)["\']\s*\)')


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def iter_files(root: Path, suffixes):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if Path(name).suffix in suffixes:
                yield Path(dirpath) / name


def go_module_path(root: Path) -> str:
    gomod = root / "go.mod"
    if gomod.exists():
        m = re.search(r"^module\s+(\S+)", read(gomod), re.M)
        if m:
            return m.group(1)
    return ""


def go_imports(src: str):
    out = []
    for block in GO_IMPORT_BLOCK.findall(src):
        out.extend(GO_IMPORT_LINE.findall(block))
    out.extend(GO_IMPORT_ONE.findall(src))
    return out


def ts_resolve(importer: Path, spec: str, root: Path):
    if not spec.startswith("."):
        return None
    base = (importer.parent / spec).resolve()
    # `.js` w imporcie wskazuje plik `.ts` - tak wymaga NodeNext, a tak pisze się w tym repozytorium.
    bez_js = Path(str(base)[:-3]) if str(base).endswith(".js") else base
    for cand in (base, Path(str(bez_js) + ".ts"), Path(str(bez_js) + ".tsx"),
                 base / "index.ts", base / "index.tsx"):
        if cand.is_file():
            try:
                return cand.relative_to(root).as_posix()
            except ValueError:
                return None
    return None


def build_graphs(root: Path):
    modpath = go_module_path(root)
    go_rev = defaultdict(set)   # pakiet -> pakiety, które go importują
    go_pkgs = set()
    for path in iter_files(root, {".go"}):
        rel = path.relative_to(root)
        pkg = rel.parent.as_posix()
        go_pkgs.add(pkg)
        if not modpath:
            continue
        for imp in go_imports(read(path)):
            if imp.startswith(modpath):
                dep = imp[len(modpath):].lstrip("/") or "."
                go_rev[dep].add(pkg)

    ts_rev = defaultdict(set)   # moduł -> moduły, które go importują
    for path in iter_files(root, {".ts", ".tsx"}):
        rel = path.relative_to(root).as_posix()
        src = read(path)
        for spec in list(TS_IMPORT.findall(src)) + list(TS_DYNAMIC.findall(src)):
            target = ts_resolve(path, spec, root)
            if target:
                ts_rev[target].add(rel)
    return modpath, go_pkgs, go_rev, ts_rev


def closure(seeds, reverse):
    seen = set(seeds)
    queue = deque(seeds)
    while queue:
        cur = queue.popleft()
        for user in reverse.get(cur, ()):
            if user not in seen:
                seen.add(user)
                queue.append(user)
    return seen


def changed_from_git(root: Path, base: str, staged: bool):
    # core.quotepath=false: bez tego git oddaje nazwy z polskimi znakami w postaci
    # ósemkowych sekwencji ucieczki, których nie da się dopasować do ścieżek na dysku.
    wspolne = ["git", "-C", str(root), "-c", "core.quotepath=false"]
    if staged:
        cmd = wspolne + ["diff", "--cached", "--name-only"]
    else:
        cmd = wspolne + ["diff", "--name-only", "{}...HEAD".format(base)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print("BŁĄD: nie udało się odczytać zmian z gita: {}".format(exc), file=sys.stderr)
        sys.exit(4)
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Liczy zasięg zmiany w repozytorium")
    ap.add_argument("--root", default=".")
    ap.add_argument("--base", help="gałąź odniesienia, np. main")
    ap.add_argument("--staged", action="store_true", help="użyj zmian przygotowanych do commita")
    ap.add_argument("--changed", nargs="*", default=[], help="lista zmienionych plików")
    ap.add_argument("--exit-code", action="store_true",
                    help="kończy kodem 3, gdy zmiana dotyka pliku generowanego bez zmiany kontraktu")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if args.base or args.staged:
        changed = changed_from_git(root, args.base or "main", args.staged)
    else:
        changed = args.changed
    if not changed:
        print("Brak zmienionych plików do analizy.")
        return 0

    modpath, go_pkgs, go_rev, ts_rev = build_graphs(root)

    go_seeds = sorted({Path(c).parent.as_posix() for c in changed
                       if c.endswith(".go") and Path(c).parent.as_posix() in go_pkgs})
    ts_seeds = sorted({c for c in changed if c.endswith((".ts", ".tsx"))})

    print("Zmienione pliki: {}".format(len(changed)))
    for c in changed:
        print("  - {}".format(c))
    print()

    contract_touched = [c for c in changed if c.endswith("contract.json")]
    generated_touched = [c for c in changed
                         if c.endswith(("contract.go", "contract.ts", "scopes.go", "scopes.ts",
                                        "dispatch_gen.go", "dispatch_gen.ts"))]

    if contract_touched:
        print("!! Zmieniono kontrakt: {}".format(", ".join(contract_touched)))
        print("   Zanim cokolwiek zbudujesz, zregeneruj kod: task contract")
        print("   Zasięg takiej zmiany to w praktyce całe repozytorium - kompilator wskaże miejsca.")
        print()
    reczna_edycja_generowanego = bool(generated_touched and not contract_touched)
    if reczna_edycja_generowanego:
        print("!! Zmieniono plik generowany bez zmiany kontraktu: {}".format(", ".join(generated_touched)))
        print("   Te poprawki znikną przy najbliższej regeneracji. Źródłem prawdy jest shared/contract.json.")
        print()

    if go_seeds:
        affected = sorted(closure(go_seeds, go_rev))
        print("Pakiety Go dotknięte zmianą ({}):".format(len(affected)))
        for pkg in affected:
            marker = " <- zmieniony" if pkg in go_seeds else ""
            print("  {}{}".format(pkg, marker))
        print()
        print("Weryfikacja:")
        print("  go build ./...")
        print("  go test {}".format(" ".join("./{}/".format(p) for p in affected[:20])))
        if len(affected) > 20:
            print("  (dotkniętych pakietów jest {}, powyżej pierwsze 20 - rozważ 'go test ./...')".format(len(affected)))
        print()

    if ts_seeds:
        affected = sorted(closure(ts_seeds, ts_rev))
        print("Moduły TypeScript dotknięte zmianą ({}):".format(len(affected)))
        for mod in affected[:40]:
            marker = " <- zmieniony" if mod in ts_seeds else ""
            print("  {}{}".format(mod, marker))
        if len(affected) > 40:
            print("  ... i {} dalszych".format(len(affected) - 40))
        print()
        tests = [m for m in affected if ".test." in m or ".spec." in m]
        print("Weryfikacja:")
        print("  npx tsc --noEmit")
        if tests:
            print("  npx vitest run {}".format(" ".join(tests[:20])))
        else:
            print("  npx vitest run   # żaden z dotkniętych modułów nie ma własnego testu -")
            print("                   # to sam w sobie jest ustaleniem wartym odnotowania")
        print()

    if not go_seeds and not ts_seeds:
        print("Zmiana nie dotyka kodu Go ani TypeScriptu - brak grafu zależności do policzenia.")

    if args.exit_code and reczna_edycja_generowanego:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
