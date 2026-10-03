#!/usr/bin/env python3
"""Generator szablonów `--settings` dla produktu osadzającego Claude Code CLI.

Tworzy komplet trzech plików dla jednego profilu przebiegu:
  <nazwa>-<profil>.settings.json  — plik dla `--settings` (zasięg „Any file”, bez kluczy Managed)
  <nazwa>-<profil>.flagi.txt      — zalecane flagi uruchomienia `claude -p` (po jednej w wierszu)
  <nazwa>-<profil>.zmienne.txt    — zmienne środowiska procesu CLI (bez sekretów)
i sprawdza wynik walidatorem (`waliduj_ustawienia.py`; z --cli także `claude doctor`).

Profile:
  czat          rozmowa bez narzędzi kodu: tylko MCP produktu i sieć (WebSearch/WebFetch),
                tryb dontAsk, bez skilli wbudowanych, workflowów, artefaktów, Remote Control
  kod           praca na repozytorium: acceptEdits, piaskownica Bash z listą domen,
                odczyt tylko w katalogach roboczych, twarde limity podagentów
  ci            przebieg nienadzorowany w CI: dontAsk + dokładna lista dozwolonych poleceń
  tylko-odczyt  analiza bez zmian: dontAsk, bez Edit/Write/Bash poza poleceniami tylko do odczytu

Użycie:
  generuj_ustawienia.py --profil czat --nazwa nexus --serwer-mcp nexus --wyjscie DIR
                        [--model claude-opus-5-5] [--modele a,b] [--max-effort xhigh]
                        [--ttl 1h] [--jezyk polski] [--domeny d1,d2] [--retencja-dni 30]
                        [--hook-dziennik http://127.0.0.1:8787/hook] [--wersja 2.1.286]
                        [--cli /sciezka/claude]

Klucz wymagający nowszego CLI niż --wersja jest pomijany z komunikatem (starsze CLI
odrzucają cały plik przy nieznanej wartości, np. `attribution: false` przed 2.1.281).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_wspolne as cc  # noqa: E402

SCHEMAT_URL = "https://json.schemastore.org/claude-code-settings.json"
SPECJALNE_WERSJE = {"attribution": "2.1.281", "disableAutoMode": "2.1.111"}

DOMENY_KOD = ["registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "github.com",
              "codeload.github.com", "objects.githubusercontent.com", "proxy.golang.org", "sum.golang.org",
              "crates.io", "index.crates.io", "static.crates.io", "repo1.maven.org"]
DOMENY_ZAKAZANE = ["pastebin.com", "transfer.sh", "*.ngrok-free.app", "*.ngrok.io"]
NARZEDZIA = {
    "czat": "ToolSearch,Agent,WebSearch,WebFetch",
    "kod": "ToolSearch,Agent,WebSearch,WebFetch,Read,Edit,Write,Glob,Grep,Bash",
    "ci": "Read,Edit,Write,Glob,Grep,Bash",
    "tylko-odczyt": "Read,Glob,Grep,Bash",
}


def wspolne_ustawienia(a: argparse.Namespace) -> dict:
    """Klucze wspólne dla każdego profilu usługi: tożsamość, wyłączenia powierzchni, koszty."""
    u: dict = {
        "$schema": SCHEMAT_URL,
        "attribution": False,
        "includeGitInstructions": a.profil in ("kod", "ci"),
        "language": a.jezyk,
        "disableAutoMode": "disable",
        "autoMemoryEnabled": False,
        "disableBundledSkills": True,
        "syncClaudeAiSkills": False,
        "syncClaudeAiPlugins": False,
        "disableClaudeAiConnectors": True,
        "disableWorkflows": True,
        "workflowKeywordTriggerEnabled": False,
        "disableAgentView": True,
        "crossSessionInbound": "refuse",
        "enableArtifact": False,
        "disableRemoteControl": True,
        "fastMode": False,
        "maxEffortLevel": a.max_effort,
        "cleanupPeriodDays": a.retencja_dni,
    }
    if a.ttl:
        u["promptCacheTtl"] = a.ttl
    if a.model:
        u["model"] = a.model
    if a.modele:
        u["availableModels"] = [m.strip() for m in a.modele.split(",") if m.strip()]
    if a.serwer_mcp:
        u["allowedMcpServers"] = [{"serverName": s} for s in a.serwer_mcp]
    if a.hook_dziennik:
        u["allowedHttpHookUrls"] = [a.hook_dziennik.rsplit("/", 1)[0] + "/*"]
        u["httpHookAllowedEnvVars"] = []
        u["hooks"] = {zdarzenie: [{"hooks": [{"type": "http", "url": a.hook_dziennik, "timeout": 10}]}]
                      for zdarzenie in ("PermissionDenied", "PostModelSwitch", "StopFailure", "PostCompact")}
    return u


def uprawnienia(a: argparse.Namespace) -> dict:
    mcp = [f"mcp__{s}" for s in a.serwer_mcp]
    deny_agent = ["Agent(model:*)", "Agent(isolation:*)"]
    if a.profil == "czat":
        return {"defaultMode": "dontAsk", "disableBypassPermissionsMode": "disable",
                "allow": mcp + ["ToolSearch", "Agent", "WebSearch"] + [f"WebFetch(domain:{d})" for d in a.domeny_web],
                "deny": deny_agent + [f"WebFetch(domain:{d})" for d in DOMENY_ZAKAZANE]}
    if a.profil == "kod":
        return {"defaultMode": "acceptEdits", "disableBypassPermissionsMode": "disable",
                "blockReadsOutsideWorkingDirectories": True,
                "allow": mcp + ["ToolSearch", "Agent", "WebSearch", "Bash(npm run *)", "Bash(npm test *)",
                                "Bash(git status)", "Bash(git diff *)", "Bash(git log *)", "Bash(git add *)",
                                "Bash(git commit *)", "Bash(pytest *)", "Bash(go test *)"],
                "ask": ["Bash(git push *)"],
                "deny": deny_agent + ["Bash(run_in_background:true)", "Bash(sudo *)", "Bash(git remote *)",
                                      "Bash(npm publish *)", "Read(./.env)", "Read(./.env.*)", "Read(**/secrets/**)"]}
    if a.profil == "ci":
        return {"defaultMode": "dontAsk", "disableBypassPermissionsMode": "disable",
                "blockReadsOutsideWorkingDirectories": True,
                "allow": mcp + ["Edit(./**)", "Bash(npm ci)", "Bash(npm run lint)", "Bash(npm test *)",
                                "Bash(git diff *)", "Bash(git status)"],
                "deny": deny_agent + ["Agent", "WebFetch", "WebSearch", "Bash(git push *)", "Bash(curl *)",
                                      "Bash(wget *)", "Read(./.env)", "Read(./.env.*)"]}
    return {"defaultMode": "dontAsk", "disableBypassPermissionsMode": "disable",
            "blockReadsOutsideWorkingDirectories": True,
            "allow": mcp,
            "deny": deny_agent + ["Edit", "Write", "NotebookEdit", "WebFetch", "Read(./.env)", "Read(./.env.*)"]}


def piaskownica(a: argparse.Namespace) -> dict:
    return {"enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": a.profil == "kod", "excludedCommands": [],
            "filesystem": {"denyRead": ["~/.ssh", "~/.aws", "~/.config/gcloud"]},
            "network": {"strictAllowlist": True, "allowAllUnixSockets": False,
                        "allowedDomains": a.domeny or (DOMENY_KOD if a.profil == "kod" else []),
                        "deniedDomains": DOMENY_ZAKAZANE},
            "credentials": {"envVars": [{"name": n, "mode": "deny"} for n in
                                        ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "GITHUB_TOKEN")]}}


def zbuduj(a: argparse.Namespace) -> tuple[dict, list[str], list[str], list[str]]:
    u = wspolne_ustawienia(a)
    u["permissions"] = uprawnienia(a)
    if a.profil in ("kod", "ci", "tylko-odczyt"):
        u["sandbox"] = piaskownica(a)
        u["bashOutputMaxChars"] = 60000
    pominiete = []
    if a.wersja:
        indeks = cc.klucze_ustawien()

        def przytnij(slownik: dict, prefiks: str = "") -> None:
            for klucz in list(slownik):
                pelny = f"{prefiks}.{klucz}" if prefiks else klucz
                wymog = SPECJALNE_WERSJE.get(pelny) or (indeks.get(pelny) or {}).get("min_wersja", "")
                if wymog and cc.wersja_mniejsza(a.wersja, wymog):
                    pominiete.append(f"{pelny} (wymaga ≥{wymog})")
                    del slownik[klucz]
                elif isinstance(slownik[klucz], dict) and pelny in ("permissions", "sandbox", "sandbox.network",
                                                                     "sandbox.filesystem", "sandbox.credentials"):
                    przytnij(slownik[klucz], pelny)
        przytnij(u)
        if "attribution" not in u:
            u["attribution"] = {"commit": "", "pr": ""}
            pominiete.append("attribution: false → {commit: \"\", pr: \"\"} (forma dla CLI < 2.1.281)")

    flagi = ["-p", "--input-format stream-json", "--output-format stream-json", "--verbose",
             "--include-partial-messages", "--include-hook-events", "--replay-user-messages",
             '--setting-sources ""', f"--settings <katalog>/{a.nazwa}-{a.profil}.settings.json",
             f'--tools "{NARZEDZIA[a.profil]}"', f"--permission-mode {u['permissions']['defaultMode']}",
             "--permission-prompts none", "--disable-slash-commands",
             "--system-prompt-file <katalog>/instrukcja.txt", "--system-prompt-snapshot off",
             "--max-turns 200"]
    if a.serwer_mcp:
        flagi.append("--mcp-config <katalog>/mcp.json")
    # zawsze: bez serwerów z ~/.claude.json, konektorów claude.ai i .mcp.json (próba: --setting-sources "" sam
    # odcina .mcp.json projektu, ale --strict-mcp-config obejmuje wszystkie inne źródła MCP)
    flagi.append("--strict-mcp-config")
    if a.profil in ("czat", "kod"):
        flagi += ["--agents <katalog>/agenci.json", "--forward-subagent-text"]
    flagi.append("(--session-id <uuid> | --resume <uuid>)")

    srodowisko = [
        "CLAUDE_CONFIG_DIR=<katalog-konfiguracji-dzierżawcy>",
        "CLAUDE_CODE_PROJECT_DIR_NAME=<identyfikator-dzierżawcy>",
        "DISABLE_AUTOUPDATER=1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1",
        "CLAUDE_CODE_DISABLE_POLICY_SKILLS=1",
        "CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1",
        "CLAUDE_CODE_DISABLE_WORKFLOWS=1",
        "CLAUDE_CODE_DISABLE_FAST_MODE=1",
        "CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1",
        "CLAUDE_CODE_DISABLE_ARTIFACT=1",
        "CLAUDE_CODE_DISABLE_CRON=1",
        "CLAUDE_CODE_STARTUP_FAILURE_RESULTS=1",
        "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=10",
        "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1",
        "MCP_TIMEOUT=60000",
    ]
    if a.profil == "czat":
        srodowisko.append("CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1")
    if a.profil in ("kod", "ci"):
        srodowisko.append("CLAUDE_CODE_TOOL_MEMORY_LIMIT=4G")
    if a.profil == "ci":
        # SCRUB=1 wymusza tryb `default` (próba 2.1.286) — zgodne z dontAsk + jawną listą allow w `-p`,
        # ale niezgodne z acceptEdits profilu `kod` (edycje byłyby odrzucane).
        srodowisko.append("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1")
    if a.ttl:
        srodowisko.append(f"CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL={a.ttl}")
    znane = cc.zmienne()
    nieznane = [w.split("=")[0] for w in srodowisko if w.split("=")[0] not in znane]
    if nieznane:
        raise SystemExit(f"Generator zawiera zmienne spoza dokumentacji: {nieznane}")
    return u, flagi, srodowisko, pominiete


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profil", required=True, choices=sorted(NARZEDZIA))
    parser.add_argument("--nazwa", default="produkt")
    parser.add_argument("--wyjscie", type=Path, default=Path("."))
    parser.add_argument("--serwer-mcp", action="append", default=[])
    parser.add_argument("--model", default="")
    parser.add_argument("--modele", default="")
    parser.add_argument("--max-effort", default="xhigh", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--ttl", default="1h", choices=["1h", "5m", ""])
    parser.add_argument("--jezyk", default="polski")
    parser.add_argument("--domeny", default="", help="lista domen piaskownicy Bash (po przecinku)")
    parser.add_argument("--domeny-web", default="", help="domeny dozwolone dla WebFetch w profilu czat")
    parser.add_argument("--retencja-dni", type=int, default=30)
    parser.add_argument("--hook-dziennik", default="", help="adres hooka http rejestrującego zdarzenia")
    parser.add_argument("--wersja", default="", help="docelowa wersja CLI (pomija nowsze klucze)")
    parser.add_argument("--cli", default="", help="binarka do walidacji `claude doctor`")
    a = parser.parse_args()
    a.domeny = [d for d in a.domeny.split(",") if d]
    a.domeny_web = [d for d in a.domeny_web.split(",") if d]
    if a.retencja_dni < 1:
        parser.error("--retencja-dni musi być ≥ 1 (cleanupPeriodDays: 0 jest niedozwolone)")

    ustawienia, flagi, srodowisko, pominiete = zbuduj(a)
    a.wyjscie.mkdir(parents=True, exist_ok=True)
    rdzen = a.wyjscie / f"{a.nazwa}-{a.profil}"
    plik = rdzen.with_suffix(".settings.json")
    plik.write_text(json.dumps(ustawienia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rdzen.with_suffix(".flagi.txt").write_text("\n".join(flagi) + "\n", encoding="utf-8")
    rdzen.with_suffix(".zmienne.txt").write_text("\n".join(srodowisko) + "\n", encoding="utf-8")
    print(f"Zapisano: {plik}, {rdzen.with_suffix('.flagi.txt')}, {rdzen.with_suffix('.zmienne.txt')}", flush=True)
    for p in pominiete:
        print(f"Pominięto dla v{a.wersja}: {p}", flush=True)
    walidacja = [sys.executable, str(Path(__file__).with_name("waliduj_ustawienia.py")), str(plik), "--rodzaj", "flaga"]
    if a.wersja:
        walidacja += ["--wersja", a.wersja]
    if a.cli:
        walidacja += ["--cli", a.cli]
    return subprocess.call(walidacja)


if __name__ == "__main__":
    sys.exit(main())
