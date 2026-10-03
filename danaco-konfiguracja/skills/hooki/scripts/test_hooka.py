#!/usr/bin/env python3
"""Test hooka Claude Code bez sesji: podaje wejście zdarzenia, ocenia wyjście jak CLI.

Buduje przykładowe wejście JSON dla zdarzenia (pola wspólne + pola zdarzenia), uruchamia
polecenie hooka ze stdin, a potem tłumaczy wynik według reguł dokumentacji:
kod wyjścia (0 / 2 / inny), czy stdout będzie parsowany jako JSON czy tekst, czy pola
decyzji są na właściwym poziomie i mają dozwolone wartości, czy hook zablokuje akcję.

Użycie:
  test_hooka.py --zdarzenie PreToolUse --narzedzie Bash --wejscie '{"command":"rm -rf /"}' -- python3 hook.py
  test_hooka.py --zdarzenie Stop --pole stop_hook_active=true -- ./weryfikacja_stop.py
  test_hooka.py --zdarzenie SessionStart --pole source=resume -- sh kontekst.sh
Opcje: --cwd KATALOG (CLAUDE_PROJECT_DIR i cwd), --tryb (permission_mode), --timeout S.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KORZEN / "scripts"))
import cc_wspolne as cc  # noqa: E402

KONTEKST_ZE_STDOUT = {"SessionStart", "UserPromptSubmit", "UserPromptExpansion", "PostModelSwitch"}
NARZEDZIOWE = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"}
DECYZJA_GORNA = {"UserPromptSubmit", "UserPromptExpansion", "PostToolUse", "PostToolUseFailure", "PostToolBatch",
                 "Stop", "SubagentStop", "ConfigChange", "PreCompact", "TaskCreated", "PreModelSwitch"}
POLA_SZCZEGOLOWE = {
    "PreToolUse": {"permissionDecision", "permissionDecisionReason", "updatedInput", "additionalContext"},
    "PermissionRequest": {"decision"},
    "PermissionDenied": {"retry"},
    "PostToolUse": {"additionalContext", "updatedToolOutput", "updatedMCPToolOutput", "classifierContext"},
    "PostToolUseFailure": {"additionalContext"},
    "PostToolBatch": {"additionalContext"},
    "SessionStart": {"additionalContext", "initialUserMessage", "sessionTitle", "watchPaths", "reloadSkills"},
    "SubagentStart": {"additionalContext"},
    "PostModelSwitch": {"additionalContext"},
    "PreModelSwitch": {"permissionDecision", "permissionDecisionReason"},
    "UserPromptSubmit": {"additionalContext", "sessionTitle", "suppressOriginalPrompt"},
    "UserPromptExpansion": {"additionalContext"},
    "Stop": {"additionalContext"},
    "SubagentStop": {"additionalContext"},
    "Elicitation": {"action", "content"},
    "ElicitationResult": {"action", "content"},
    "MessageDisplay": {"displayContent"},
    "CwdChanged": {"watchPaths"},
    "FileChanged": {"watchPaths"},
    "WorktreeCreate": {"worktreePath"},
}
UNIWERSALNE = {"continue", "stopReason", "suppressOutput", "systemMessage", "terminalSequence", "hookSpecificOutput",
               "decision", "reason"}


def wejscie_zdarzenia(a: argparse.Namespace) -> dict:
    dane = {"session_id": "test-sesja", "prompt_id": "00000000-0000-4000-8000-000000000000",
            "transcript_path": "/tmp/test.jsonl", "cwd": a.cwd, "permission_mode": a.tryb,
            "hook_event_name": a.zdarzenie, "effort": {"level": "high"}}
    if a.zdarzenie in NARZEDZIOWE:
        dane.update(tool_name=a.narzedzie, tool_input=json.loads(a.wejscie), tool_use_id="toolu_test")
        if a.zdarzenie == "PostToolUse":
            dane["tool_response"] = {"stdout": "", "stderr": "", "interrupted": False, "isImage": False}
    if a.zdarzenie == "SessionStart":
        dane["source"] = "startup"
    if a.zdarzenie in ("Stop", "SubagentStop"):
        dane.update(stop_hook_active=False, last_assistant_message="Gotowe.")
    if a.zdarzenie == "UserPromptSubmit":
        dane["prompt"] = "przykładowy prompt"
    if a.zdarzenie in ("PreModelSwitch", "PostModelSwitch"):
        dane.update(from_model="claude-opus-5-5", to_model="claude-sonnet-5")
    for para in a.pole:
        klucz, _, wartosc = para.partition("=")
        try:
            dane[klucz] = json.loads(wartosc)
        except json.JSONDecodeError:
            dane[klucz] = wartosc
    return dane


def ocen(zdarzenie: str, kod: int, stdout: str, stderr: str) -> list[str]:
    uwagi = []
    wpis = cc.zdarzenia_hookow().get(zdarzenie, {})
    blokujace = str(wpis.get("blokuje_exit2", "")).startswith("tak")
    tekst = stdout.strip()
    jest_json = tekst.startswith("{") and tekst.endswith("}")
    if kod == 2:
        uwagi.append("exit 2: " + ("BLOKADA — powód ze stderr lub z JSON" if blokujace
                                   else "to zdarzenie nie blokuje; stderr pokazany według reguł zdarzenia"))
        if zdarzenie == "PermissionRequest":
            uwagi.append("UWAGA: PermissionRequest ignoruje exit 2 — odmawiaj obiektem decision")
    elif kod != 0:
        uwagi.append(f"exit {kod}: błąd NIEBLOKUJĄCY — akcja przejdzie (polityka wymaga exit 2 lub JSON-a)")
    if not tekst:
        uwagi.append("brak stdout: brak decyzji, zwykły przepływ")
        return uwagi
    if not jest_json:
        if zdarzenie in KONTEKST_ZE_STDOUT and kod == 0:
            uwagi.append("stdout to tekst — trafi do kontekstu modelu (≤10 000 znaków)")
        else:
            uwagi.append("stdout to tekst — tylko do dziennika debug (dla tego zdarzenia nie trafia do modelu)")
        if tekst.lstrip().startswith("{"):
            uwagi.append("UWAGA: stdout zaczyna się od '{', ale nie kończy '}' — traktowany jak tekst")
        return uwagi
    try:
        wynik = json.loads(tekst)
    except json.JSONDecodeError as blad:
        return uwagi + [f"BŁĄD: stdout wygląda na JSON, ale się nie parsuje ({blad}) — błąd nieblokujący"]
    nieznane = set(wynik) - UNIWERSALNE
    if nieznane:
        uwagi.append(f"BŁĄD: pola na złym poziomie lub nieznane: {sorted(nieznane)} "
                     f"(np. permissionDecision należy do hookSpecificOutput)")
    if "decision" in wynik:
        if zdarzenie not in DECYZJA_GORNA:
            uwagi.append(f"BŁĄD: górne `decision` nie działa dla {zdarzenie}"
                         + (" — użyj hookSpecificOutput.permissionDecision" if zdarzenie == "PreToolUse" else ""))
        elif wynik["decision"] != "block":
            uwagi.append("BŁĄD: jedyna wartość `decision` to \"block\"")
        else:
            uwagi.append(f"decision: block — {'powód: ' + str(wynik.get('reason', 'BRAK reason!'))[:120]}")
    szczegoly = wynik.get("hookSpecificOutput")
    if isinstance(szczegoly, dict):
        if szczegoly.get("hookEventName") != zdarzenie:
            uwagi.append(f"BŁĄD: hookSpecificOutput.hookEventName = {szczegoly.get('hookEventName')!r}, oczekiwane {zdarzenie!r}")
        dozwolone = POLA_SZCZEGOLOWE.get(zdarzenie, set()) | {"hookEventName"}
        zle = set(szczegoly) - dozwolone
        if zle:
            uwagi.append(f"BŁĄD: pola nieobsługiwane w {zdarzenie}: {sorted(zle)}")
        decyzja = szczegoly.get("permissionDecision")
        if decyzja is not None:
            dopuszczalne = {"allow", "deny", "ask"} | ({"defer"} if zdarzenie == "PreToolUse" else set())
            uwagi.append(f"permissionDecision: {decyzja}" + ("" if decyzja in dopuszczalne else " — BŁĄD: wartość spoza "
                                                                                                f"{sorted(dopuszczalne)}"))
        if zdarzenie == "PermissionRequest":
            d = szczegoly.get("decision") or {}
            if d.get("behavior") not in ("allow", "deny"):
                uwagi.append("BŁĄD: decision.behavior musi być allow albo deny")
            else:
                uwagi.append(f"decision.behavior: {d['behavior']}")
        for pole in ("additionalContext", "systemMessage", "initialUserMessage"):
            wartosc = szczegoly.get(pole, wynik.get(pole))
            if isinstance(wartosc, str) and len(wartosc) > 10000:
                uwagi.append(f"UWAGA: {pole} ma {len(wartosc)} znaków > 10 000 — trafi do pliku z podglądem 2 000")
    if wynik.get("continue") is False:
        uwagi.append(f"continue: false — praca zatrzymana ({wynik.get('stopReason', 'bez stopReason')})")
    return uwagi or ["JSON poprawny, bez decyzji"]


def main() -> int:
    if "--" not in sys.argv:
        print(__doc__)
        return 2
    i = sys.argv.index("--")
    parser = argparse.ArgumentParser()
    parser.add_argument("--zdarzenie", required=True)
    parser.add_argument("--narzedzie", default="Bash")
    parser.add_argument("--wejscie", default='{"command": "ls"}')
    parser.add_argument("--pole", action="append", default=[])
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--tryb", default="default")
    parser.add_argument("--timeout", type=int, default=30)
    a = parser.parse_args(sys.argv[1:i])
    polecenie = sys.argv[i + 1:]
    if a.zdarzenie not in cc.zdarzenia_hookow():
        print(f"Nieznane zdarzenie {a.zdarzenie}. Znane: {', '.join(cc.zdarzenia_hookow())}")
        return 2
    dane = wejscie_zdarzenia(a)
    srodowisko = dict(os.environ, CLAUDE_PROJECT_DIR=a.cwd)
    plik_env = None
    if a.zdarzenie == "SessionStart":
        plik_env = tempfile.NamedTemporaryFile(prefix="claude-env-", delete=False)
        srodowisko["CLAUDE_ENV_FILE"] = plik_env.name
    try:
        proces = subprocess.run(polecenie, input=json.dumps(dane), capture_output=True, text=True, cwd=a.cwd,
                                env=srodowisko, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT po {a.timeout} s — na PreToolUse wywołanie przeszłoby dalej, na PreModelSwitch zmiana zablokowana")
        return 1
    print(f"Zdarzenie: {a.zdarzenie}   kod wyjścia: {proces.returncode}")
    if proces.stdout.strip():
        print(f"stdout: {proces.stdout.strip()[:600]}")
    if proces.stderr.strip():
        print(f"stderr: {proces.stderr.strip()[:300]}")
    if plik_env:
        tresc = Path(plik_env.name).read_text()
        if tresc:
            print("CLAUDE_ENV_FILE: " + ", ".join(l.split("=")[0].replace("export ", "") for l in tresc.splitlines() if l))
        os.unlink(plik_env.name)
    for uwaga in ocen(a.zdarzenie, proces.returncode, proces.stdout, proces.stderr):
        print(f"  - {uwaga}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
