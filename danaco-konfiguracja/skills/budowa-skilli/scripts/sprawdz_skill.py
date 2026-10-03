#!/usr/bin/env python3
"""Lint skilla (katalog z SKILL.md) według Claude Code i praktyk Agent Skills.

Sprawdza: frontmatter od pierwszego wiersza, pola znane Claude Code (nieznane są pomijane po
cichu), `name` (≤64 znaki, małe litery/cyfry/myślniki, bez „anthropic” i „claude”, nie
`synced`), `description` (≤1024 znaki wg specyfikacji Agent Skills; opis + `when_to_use`
ucinane w liście do 1536), opis w trzeciej osobie i z frazami wyzwalającymi, długość
treści (zalecane < 500 wierszy), odwołania do plików (czy istnieją, czy nie są zagnieżdżone
głębiej niż jeden poziom), wstrzykiwanie poleceń `!` i `allowed-tools`, `context: fork`
bez zadania, pola niedozwolone przy publikacji na claude.ai/Skills API (opcja --spec).
Szacuje koszt wpisu w liście skilli (znaki/4 ≈ tokeny).

Użycie:
  sprawdz_skill.py KATALOG_SKILLA|KATALOG_SKILLI [--spec] [--cli /sciezka/claude]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

POLA = {"name", "description", "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
        "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort", "context", "agent", "background",
        "hooks", "paths", "shell", "metadata", "license", "compatibility"}
SPEC = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
BOOL = {"true", "false", "yes", "no", "on", "off", "1", "0"}


def frontmatter(tekst: str) -> tuple[dict, str] | None:
    if not tekst.startswith("---\n"):
        return None
    koniec = tekst.find("\n---", 4)
    if koniec < 0:
        return None
    blok = tekst[4:koniec]
    dane: dict = {}
    klucz = None
    for linia in blok.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", linia)
        if m and not linia.startswith((" ", "\t")):
            klucz = m.group(1)
            wartosc = m.group(2).strip()
            dane[klucz] = "" if wartosc in (">", "|", ">-", "|-") else wartosc.strip("'\"")
        elif klucz and linia.strip():
            dane[klucz] = (dane[klucz] + " " + linia.strip()).strip()
    return dane, tekst[koniec + 4:]


def sprawdz(katalog: Path, spec: bool) -> list[str]:
    plik = katalog / "SKILL.md"
    if not plik.is_file():
        return [f"BŁĄD: brak {plik}"]
    tekst = plik.read_text(encoding="utf-8")
    wynik = frontmatter(tekst)
    if wynik is None:
        return ["BŁĄD: frontmatter nie zaczyna się w pierwszym wierszu — cały plik zostanie potraktowany jako treść"]
    d, cialo = wynik
    uwagi: list[str] = []
    for pole in d:
        if pole not in POLA:
            uwagi.append(f"BŁĄD: pole `{pole}` nieznane Claude Code — pomijane bez komunikatu")
        if spec and pole not in SPEC:
            uwagi.append(f"uwaga: `{pole}` spoza specyfikacji Agent Skills — publikacja na claude.ai/Skills API się nie powiedzie")
    nazwa = d.get("name") or katalog.name
    if len(nazwa) > 64 or not re.fullmatch(r"[a-z0-9-]+", nazwa):
        uwagi.append(f"BŁĄD: name {nazwa!r} — do 64 znaków, małe litery, cyfry, myślniki")
    if re.search(r"anthropic|claude", nazwa):
        uwagi.append(f"BŁĄD: name {nazwa!r} zawiera słowo zastrzeżone (anthropic/claude)")
    if nazwa.lower() == "synced":
        uwagi.append("BŁĄD: nazwa `synced` zastrzeżona dla skilli z claude.ai")
    opis = d.get("description", "")
    kiedy = d.get("when_to_use", "")
    if not opis:
        uwagi.append("BŁĄD: brak description — Claude użyje pierwszego wiersza treści; skill trudno dopasować")
    if len(opis) > 1024:
        uwagi.append(f"uwaga: description {len(opis)} znaków > 1024 (limit specyfikacji Agent Skills; Claude Code przyjmie)")
    if len(opis) + len(kiedy) > 1536:
        uwagi.append(f"BŁĄD: description + when_to_use = {len(opis) + len(kiedy)} znaków > 1536 — lista utnie koniec")
    if re.match(r"^\s*(I |I'm |You |Ja |Pomogę|Mogę )", opis):
        uwagi.append("uwaga: opis w 1./2. osobie — pisz w trzeciej osobie (opis trafia do instrukcji)")
    if opis and not re.search(r"(Stosuj|Use when|Używaj|gdy |when )", opis):
        uwagi.append("uwaga: opis bez „kiedy używać” — dodaj frazy wyzwalające")
    if "<" in opis and re.search(r"<[a-zA-Z/]", opis):
        uwagi.append("BŁĄD: znaczniki XML w opisie (niedozwolone w specyfikacji)")
    for pole in ("disable-model-invocation", "user-invocable", "background"):
        if pole in d and d[pole].lower() not in BOOL:
            uwagi.append(f"BŁĄD: {pole}={d[pole]!r} nie jest wartością logiczną")
    if d.get("context") and d["context"] != "fork":
        uwagi.append("BŁĄD: context przyjmuje tylko `fork`")
    if d.get("context") == "fork" and not re.search(r"(^\d+\.|\$ARGUMENTS|Zadanie|Task|##\s*(Zadanie|Procedura|Kroki))", cialo, re.M):
        uwagi.append("uwaga: context: fork bez wyraźnego zadania — podagent dostanie wytyczne bez polecenia")
    if d.get("effort") and d["effort"] not in ("low", "medium", "high", "xhigh", "max"):
        uwagi.append(f"BŁĄD: effort={d['effort']!r}")
    linie = cialo.count("\n")
    if linie > 500:
        uwagi.append(f"uwaga: treść {linie} wierszy > 500 — przenieś szczegóły do references/ (ładowane na żądanie)")
    if re.search(r"(^|\s)!`[^`]+`", cialo) or "```!" in cialo:
        uwagi.append("info: skill wstrzykuje wynik poleceń (`!`) — nie zadziała przy disableSkillShellExecution; "
                     "polecenie z niezatwierdzonym uprawnieniem przerywa wywołanie")
    for link in re.findall(r"`((?:references|scripts|examples|assets)/[^`\s]+)`|\]\(((?:references|scripts|examples|assets)/[^)]+)\)", cialo):
        sciezka = link[0] or link[1]
        if "<" in sciezka or "*" in sciezka:
            continue
        if not (katalog / sciezka).exists():
            uwagi.append(f"BŁĄD: odwołanie do nieistniejącego pliku {sciezka}")
    for ref in (katalog / "references").glob("**/*.md") if (katalog / "references").is_dir() else []:
        tresc = ref.read_text(encoding="utf-8", errors="replace")
        if len(tresc.splitlines()) > 300 and not re.search(r"^##?\s*(Spis treści|Contents)", tresc, re.M):
            uwagi.append(f"uwaga: {ref.relative_to(katalog)} > 300 wierszy bez spisu treści — Claude może czytać go częściowo")
    koszt = (len(nazwa) + len(opis[:1536]) + len(kiedy)) // 4
    uwagi.append(f"info: wpis w liście skilli ≈ {koszt} tokenów; treść SKILL.md ≈ {len(cialo) // 4} tokenów po wywołaniu")
    return uwagi


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("katalog", type=Path)
    parser.add_argument("--spec", action="store_true", help="sprawdź zgodność ze specyfikacją Agent Skills")
    parser.add_argument("--cli", default="")
    a = parser.parse_args()
    katalogi = [a.katalog] if (a.katalog / "SKILL.md").is_file() else sorted(p.parent for p in a.katalog.glob("*/SKILL.md"))
    bledy = 0
    for k in katalogi:
        for u in sprawdz(k, a.spec):
            print(f"[{k.name}] {u}")
            bledy += u.startswith("BŁĄD")
    if a.cli:
        # `claude plugin validate` rozpoznaje katalog skilli po nazwie `skills` — kopiujemy do takiego
        import shutil
        import tempfile
        tymczasowy = Path(tempfile.mkdtemp(prefix="walidacja-skilli-")) / "skills"
        tymczasowy.mkdir()
        for k in katalogi:
            shutil.copytree(k, tymczasowy / k.name)
        wynik = subprocess.run([a.cli, "plugin", "validate", str(tymczasowy)], capture_output=True, text=True)
        shutil.rmtree(tymczasowy.parent, ignore_errors=True)
        ostatnia = (wynik.stdout.strip().splitlines() or [wynik.stderr.strip()])[-1]
        print(f"claude plugin validate: kod {wynik.returncode}; {ostatnia}")
        bledy += wynik.returncode != 0
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
