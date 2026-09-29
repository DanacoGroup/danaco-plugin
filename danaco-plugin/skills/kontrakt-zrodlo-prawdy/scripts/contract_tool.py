#!/usr/bin/env python3
"""Narzędzie kontraktu Danaco Console.

Jedno źródło prawdy: shared/contract.json.
Z niego generowane są:
  - shared/contract.go        (typy, stałe, rejestr komunikatów dla rdzenia Go)
  - client/src/contract.ts    (typy, unie, strażnicy typów dla interfejsu TypeScript)

Podkomendy:
  install   - kopiuje narzędzie do repozytorium (tools/contract_tool.py)
  validate  - sprawdza poprawność contract.json bez zapisu czegokolwiek
  gen       - generuje pliki docelowe (nadpisuje)
  check     - regeneruje do pamięci i porównuje z dyskiem; błąd przy rozjeździe

Kody wyjścia: 0 OK, 2 błąd walidacji (także ścieżka docelowa poza korzeniem
repozytorium), 3 rozjazd, 4 błąd wejścia/wyjścia albo awaria narzędzia. Kod 1
nie występuje: niepoprawny kontrakt jest raportowany, nie zgłaszany wyjątkiem.

Zależności: wyłącznie biblioteka standardowa Pythona 3.9+.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

LIMIT_CZASU_GOFMT_S = 60

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_DRIFT = 3
EXIT_IO = 4

# ---------------------------------------------------------------- typy proste

PRIMITIVES = {
    "string": ("string", "string"),
    "uuid": ("string", "string"),
    "int": ("int", "number"),
    "int64": ("int64", "number"),
    "float": ("float64", "number"),
    "bool": ("bool", "boolean"),
    "timestamp": ("time.Time", "string"),
    "bytes": ("[]byte", "string"),
    "json": ("json.RawMessage", "unknown"),
}

# Nazwy, które generator wytwarza sam. Typ albo enum o takiej nazwie w kontrakcie
# dałby w Go i TypeScripcie podwójną deklarację, więc walidator go odrzuca.
RESERVED_NAMES = {
    "ContractVersion", "ContractHash", "ModeID", "ModeId", "ModeInfo", "Modes", "LookupMode",
    "MessageType", "MessageDirection", "MessageResponse", "MessagePayloads", "NewPayload",
    "Envelope", "CommandName", "Commands", "ErrorCode", "ErrorMessages", "Environment",
    "ModeScope", "ModeScopes",
}

DOC_COMMENTS = True


def dok(tekst, prefiks="  // "):
    """Zwraca komentarz z pola doc albo pusty łańcuch, gdy komentarze są wyłączone.

    Reguła udzial-komentarzy liczy udział znaków komentarza w znakach pliku. Wygenerowany
    kontrakt przekracza ten limit wielokrotnie, bo komentuje każdy tryb i każde pole.
    Zwykle właściwą odpowiedzią jest wyłączenie plików generowanych spod bramki, ale
    gdy to niemożliwe, ten przełącznik pozwala wygenerować kod bez komentarzy.
    """
    if not DOC_COMMENTS or not tekst:
        return ""
    return prefiks + " ".join(str(tekst).split())


def lit(tekst) -> str:
    """Literał łańcuchowy poprawny jednocześnie w Go i w TypeScripcie.

    json.dumps ucieka cudzysłowy, odwrotne ukośniki i znaki sterujące dokładnie tak,
    jak wymagają tego oba języki; podmiana cudzysłowu na apostrof zmieniałaby treść.
    """
    return json.dumps(str(tekst or ""), ensure_ascii=False)


PASCAL = re.compile(r"^[A-Z][A-Za-z0-9]*$")
CAMEL = re.compile(r"^[a-z][A-Za-z0-9]*$")
SNAKE_LOWER = re.compile(r"^[a-z][a-z0-9_]*$")
SCREAM = re.compile(r"^[A-Z][A-Z0-9_]*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
MODE_ID = re.compile(r"^[a-z][a-z0-9]*\.[a-z][a-z0-9_]*$")


# ------------------------------------------------------------------ pomocnicze

def snake(name: str) -> str:
    """AiPrompt -> ai_prompt, AIPrompt -> ai_prompt.

    Granica jest wstawiana po małej literze/cyfrze przed wielką oraz przed ostatnią
    wielką literą akronimu; inaczej `AIPrompt` dawało `a_i_prompt`, a w nazwie na
    drucie `ai.a.i.prompt`.
    """
    out = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    return out.lower()


def pascal(name: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-.\s]+", name) if p)


def go_field_name(name: str) -> str:
    out = pascal(name)
    for acronym in ("Id", "Url", "Api", "Ai", "Ts", "Http", "Json", "Uuid"):
        if out.endswith(acronym):
            out = out[: -len(acronym)] + acronym.upper()
    return out


def error_const(code: str) -> str:
    """E_SESSION_UNKNOWN -> SessionUnknown (prefiks E_ jest szumem w nazwie stałej)."""
    body = code[2:] if code.startswith("E_") else code
    return pascal(body.lower())


def parse_type(expr: str):
    expr = expr.strip()
    if expr.endswith("[]"):
        return ("list", parse_type(expr[:-2]))
    if expr.startswith("map<") and expr.endswith(">"):
        return ("map", parse_type(expr[4:-1]))
    return ("named", expr)


def named_refs(expr: str):
    kind, inner = parse_type(expr)
    if kind == "named":
        yield inner
    else:
        yield from named_refs_node(inner)


def named_refs_node(node):
    kind, inner = node
    if kind == "named":
        yield inner
    else:
        yield from named_refs_node(inner)


def go_type(expr: str) -> str:
    return go_type_node(parse_type(expr))


def go_type_node(node) -> str:
    kind, inner = node
    if kind == "list":
        return "[]" + go_type_node(inner)
    if kind == "map":
        return "map[string]" + go_type_node(inner)
    return go_named(inner)


def go_named(name: str) -> str:
    if name in PRIMITIVES:
        return PRIMITIVES[name][0]
    return name


def ts_type(expr: str) -> str:
    return ts_type_node(parse_type(expr))


def ts_type_node(node) -> str:
    kind, inner = node
    if kind == "list":
        return ts_type_node(inner) + "[]"
    if kind == "map":
        return "Record<string, " + ts_type_node(inner) + ">"
    return ts_named(inner)


def ts_named(name: str) -> str:
    if name in PRIMITIVES:
        return PRIMITIVES[name][1]
    return name


def uses_time(contract) -> bool:
    for typ in contract.get("types", []):
        if not isinstance(typ, dict):
            continue
        for pole in typ.get("fields", []) or []:
            if not isinstance(pole, dict):
                continue
            if "timestamp" in list(named_refs(pole.get("type", ""))):
                return True
    return False


# Koperta (Envelope) jest emitowana zawsze i nosi ładunek jako json.RawMessage,
# więc pakiet encoding/json jest potrzebny w każdym wygenerowanym pliku Go.
WYMAGA_JSON = True


def canonical_bytes(contract) -> bytes:
    return json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def contract_hash(contract) -> str:
    return hashlib.sha256(canonical_bytes(contract)).hexdigest()[:16]


def wire_name(msg) -> str:
    """Nazwa komunikatu na drucie: `AiPrompt` w kanale `ai` -> `ai.prompt`.

    Nazwa komunikatu zwykle zaczyna się od nazwy kanału, więc ten wspólny przedrostek
    jest odcinany - inaczej powstawałoby `ai.ai.prompt`. Komunikat, którego nazwa nie
    zaczyna się od kanału (`Ping` w kanale `session`), dostaje `session.ping`.
    Pole `wire` w kontrakcie nadpisuje tę regułę w całości.
    """
    if msg.get("wire"):
        return str(msg["wire"])
    channel = str(msg.get("channel", ""))
    parts = snake(str(msg.get("name", ""))).split("_")
    channel_parts = channel.split("_")
    if parts[: len(channel_parts)] == channel_parts and len(parts) > len(channel_parts):
        parts = parts[len(channel_parts):]
    return "{}.{}".format(channel, ".".join(parts))


# ------------------------------------------------------------------- walidacja

def _kolekcja(contract, klucz: str, errs: list) -> list:
    """Lista pozycji spod klucza. Sekcja obecna, ale niebędąca listą, jest błędem
    walidacji - ciche pominięcie dawałoby „kontrakt poprawny” dla kontraktu,
    z którego nic nie zostało wygenerowane."""
    wartosc = contract.get(klucz, [])
    if isinstance(wartosc, list):
        return wartosc
    errs.append("sekcja {} musi być listą, jest: {}".format(klucz, type(wartosc).__name__))
    return []


def _nazwane(kolekcja: list, grupa: str, errs: list) -> dict:
    """Słownik nazwa -> pozycja. Pozycja bez pola `name` jest błędem walidacji,
    nie wyjątkiem: narzędzie ma zgłaszać niepoprawny kontrakt, nie przewracać się
    na nim kodem 1 spoza kontraktu."""
    wynik = {}
    for indeks, pozycja in enumerate(kolekcja):
        if not isinstance(pozycja, dict) or not str(pozycja.get("name", "")).strip():
            errs.append("{} #{}: brak pola name".format(grupa, indeks))
            continue
        wynik[pozycja["name"]] = pozycja
    return wynik


def validate(contract) -> list:
    errs = []

    def err(msg):
        errs.append(msg)

    if not isinstance(contract, dict):
        return ["kontrakt musi być obiektem JSON, jest: {}".format(type(contract).__name__)]

    if not SEMVER.match(str(contract.get("contractVersion", ""))):
        err("contractVersion musi być w formacie semver (np. 1.0.0), jest: {!r}".format(contract.get("contractVersion")))

    enums = _nazwane(_kolekcja(contract, "enums", errs), "enum", errs)
    types = _nazwane(_kolekcja(contract, "types", errs), "typ", errs)

    seen = {}
    for group, coll in (("enum", enums.values()), ("type", types.values())):
        for item in coll:
            name = item.get("name", "")
            if not PASCAL.match(name):
                err("{} {!r}: nazwa musi być w PascalCase".format(group, name))
            if name in seen:
                err("nazwa {!r} zadeklarowana dwa razy ({} i {})".format(name, seen[name], group))
            if name in RESERVED_NAMES:
                err("{} {!r}: nazwa zarezerwowana przez generator - w wygenerowanym kodzie "
                    "powstałaby podwójna deklaracja".format(group, name))
            seen[name] = group

    for e in enums.values():
        vals = set()
        vnames = set()
        if not e.get("values"):
            err("enum {!r}: brak wartości".format(e.get("name")))
        for v in e.get("values", []) or []:
            if not isinstance(v, dict):
                err("enum {}: wartość musi być obiektem JSON".format(e["name"]))
                continue
            vname = v.get("name", "")
            if not PASCAL.match(vname):
                err("enum {}: nazwa wartości {!r} musi być w PascalCase".format(e["name"], vname))
            if vname in vnames:
                err("enum {}: nazwa wartości {!r} powtarza się".format(e["name"], vname))
            vnames.add(vname)
            wire = v.get("value", "")
            if not wire:
                err("enum {}: wartość {!r} nie ma pola value".format(e["name"], vname))
            if wire in vals:
                err("enum {}: wartość {!r} powtarza się".format(e["name"], wire))
            vals.add(wire)

    for t in types.values():
        fseen = set()
        jseen = set()
        gseen = set()
        for f in t.get("fields", []) or []:
            if not isinstance(f, dict):
                err("typ {}: pole musi być obiektem JSON".format(t["name"]))
                continue
            fname = f.get("name", "")
            if not CAMEL.match(fname):
                err("typ {}: pole {!r} musi być w camelCase".format(t["name"], fname))
            if fname in fseen:
                err("typ {}: pole {!r} powtarza się".format(t["name"], fname))
            fseen.add(fname)
            gname = go_field_name(fname)
            if gname in gseen:
                err("typ {}: pola {!r} i inne dają tę samą nazwę pola Go {!r}".format(t["name"], fname, gname))
            gseen.add(gname)
            jkey = f.get("json") or snake(fname)
            if jkey in jseen:
                err("typ {}: klucz JSON {!r} powtarza się".format(t["name"], jkey))
            jseen.add(jkey)
            expr = f.get("type", "")
            if not expr:
                err("typ {}: pole {!r} nie ma typu".format(t["name"], fname))
                continue
            for ref in named_refs(expr):
                if ref not in PRIMITIVES and ref not in enums and ref not in types:
                    err("typ {}: pole {} odwołuje się do nieznanego typu {!r}".format(t["name"], fname, ref))

    isolation_enum = enums.get("IsolationLevel")
    allowed_isolation = None
    if isolation_enum:
        allowed_isolation = {v.get("value") for v in isolation_enum.get("values", []) or []
                             if isinstance(v, dict) and v.get("value")}

    mode_ids = set()
    for m in _kolekcja(contract, "modes", errs):
        if not isinstance(m, dict):
            err("tryb: pozycja musi być obiektem JSON")
            continue
        mid = m.get("id", "")
        if not MODE_ID.match(mid):
            err("tryb {!r}: identyfikator musi mieć postać środowisko.moduł (małe litery)".format(mid))
            continue
        if mid in mode_ids:
            err("tryb {!r}: identyfikator powtarza się".format(mid))
        mode_ids.add(mid)
        env, mod = mid.split(".", 1)
        if m.get("environment") != env:
            err("tryb {}: pole environment ({!r}) nie zgadza się z identyfikatorem".format(mid, m.get("environment")))
        if m.get("module") != mod:
            err("tryb {}: pole module ({!r}) nie zgadza się z identyfikatorem".format(mid, m.get("module")))
        iso = m.get("isolation")
        if not iso:
            err("tryb {}: brak pola isolation - każdy tryb musi jawnie deklarować poziom izolacji".format(mid))
        elif allowed_isolation is not None and iso not in allowed_isolation:
            err("tryb {}: isolation {!r} spoza enumu IsolationLevel".format(mid, iso))

    wires = set()
    wszystkie_komunikaty = _kolekcja(contract, "messages", errs)
    komunikaty = [m for m in wszystkie_komunikaty if isinstance(m, dict)]
    if len(komunikaty) != len(wszystkie_komunikaty):
        err("komunikat: pozycja musi być obiektem JSON")
    msg_names = {msg.get("name", "") for msg in komunikaty}
    seen_msg = set()
    for msg in komunikaty:
        name = msg.get("name", "")
        if not PASCAL.match(name):
            err("komunikat {!r}: nazwa musi być w PascalCase".format(name))
        if name in seen_msg:
            err("komunikat {!r}: nazwa powtarza się".format(name))
        seen_msg.add(name)
        if not SNAKE_LOWER.match(msg.get("channel", "")):
            err("komunikat {}: channel {!r} musi być w snake_case".format(name, msg.get("channel")))
            continue
        direction = msg.get("direction")
        if direction not in ("clientToServer", "serverToClient", "bidirectional"):
            err("komunikat {}: direction musi być clientToServer, serverToClient albo bidirectional".format(name))
        w = wire_name(msg)
        if w in wires:
            err("komunikat {}: nazwa na drucie {!r} powtarza się".format(name, w))
        wires.add(w)
        payload = msg.get("payload")
        if payload and payload not in types:
            err("komunikat {}: payload odwołuje się do nieznanego typu {!r}".format(name, payload))
        response = msg.get("response")
        if response:
            if response not in msg_names:
                err("komunikat {}: response {!r} nie jest nazwą komunikatu - response wskazuje "
                    "komunikat odpowiedzi, nie typ ładunku".format(name, response))
            elif response == name:
                err("komunikat {}: response wskazuje sam siebie".format(name))
            if direction == "serverToClient":
                err("komunikat {}: response ma sens tylko dla komunikatu wysyłanego przez klienta".format(name))

    cmd_names = set()
    for c in _kolekcja(contract, "commands", errs):
        if not isinstance(c, dict):
            err("komenda: pozycja musi być obiektem JSON")
            continue
        name = c.get("name", "")
        if not SNAKE_LOWER.match(name):
            err("komenda {!r}: nazwa musi być w snake_case (tak wymaga Tauri)".format(name))
        if name in cmd_names:
            err("komenda {!r}: nazwa powtarza się".format(name))
        cmd_names.add(name)
        for key in ("request", "response"):
            ref = c.get(key)
            if ref and ref not in types:
                err("komenda {}: {} odwołuje się do nieznanego typu {!r}".format(name, key, ref))

    codes = set()
    for e in _kolekcja(contract, "errors", errs):
        if not isinstance(e, dict):
            err("błąd: pozycja musi być obiektem JSON")
            continue
        code = e.get("code", "")
        if not SCREAM.match(code):
            err("błąd {!r}: kod musi być W_STYLU_WIELKICH_LITER".format(code))
        if code in codes:
            err("błąd {!r}: kod powtarza się".format(code))
        codes.add(code)
        if not str(e.get("message", "")).strip():
            err("błąd {}: brak pola message - każdy kod musi mieć ogólną, bezpieczną treść".format(code))

    # typy nieużywane są tylko ostrzeżeniem, więc nie zgłaszamy ich jako błędów
    return errs


# ------------------------------------------------------------------ render Go

def render_go(contract) -> str:
    pkg = contract.get("generated", {}).get("go", {}).get("package", "shared")
    out = []
    w = out.append

    w("// Kod generowany automatycznie przez scripts/contract_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json. Zmiany wprowadzaj tam i uruchom ponownie generator.")
    w("")
    w("package {}".format(pkg))
    w("")

    imports = []
    if WYMAGA_JSON:
        imports.append('"encoding/json"')
    if uses_time(contract):
        imports.append('"time"')
    if imports:
        w("import (")
        for imp in imports:
            w("\t{}".format(imp))
        w(")")
        w("")

    w("// ContractVersion to wersja kontraktu, z której wygenerowano ten plik.")
    w('const ContractVersion = "{}"'.format(contract["contractVersion"]))
    w("")
    w("// ContractHash pozwala przy uścisku dłoni sprawdzić, czy klient i rdzeń mają ten sam kontrakt.")
    w('const ContractHash = "{}"'.format(contract_hash(contract)))
    w("")

    for e in contract.get("enums", []):
        if e.get("doc") and DOC_COMMENTS:
            w("// {} {}".format(e["name"], e["doc"]))
        w("type {} string".format(e["name"]))
        w("")
        w("const (")
        for v in e["values"]:
            line = '\t{}{} {} = "{}"'.format(e["name"], v["name"], e["name"], v["value"])
            w(line + dok(v.get("doc")))
        w(")")
        w("")
        w("// All{}s wylicza wszystkie dopuszczalne wartości.".format(e["name"]))
        w("var All{}s = []{}{{{}}}".format(
            e["name"], e["name"],
            ", ".join("{}{}".format(e["name"], v["name"]) for v in e["values"])))
        w("")
        w("// Valid mówi, czy wartość należy do kontraktu.")
        w("func (v {}) Valid() bool {{".format(e["name"]))
        w("\tfor _, c := range All{}s {{".format(e["name"]))
        w("\t\tif c == v {")
        w("\t\t\treturn true")
        w("\t\t}")
        w("\t}")
        w("\treturn false")
        w("}")
        w("")

    for t in contract.get("types", []):
        if t.get("doc") and DOC_COMMENTS:
            w("// {} {}".format(t["name"], t["doc"]))
        w("type {} struct {{".format(t["name"]))
        for f in t.get("fields", []):
            gtype = go_type(f.get("type", ""))
            jkey = f.get("json") or snake(f["name"])
            optional = bool(f.get("optional"))
            if optional and not gtype.startswith(("[]", "map[")) and gtype != "json.RawMessage":
                gtype = "*" + gtype
            tag = jkey + (",omitempty" if optional else "")
            line = '\t{} {} `json:"{}"`'.format(go_field_name(f["name"]), gtype, tag)
            w(line + dok(f.get("doc")))
        w("}")
        w("")

    # Rejestry trybów, komunikatów i błędów są emitowane zawsze - także puste.
    # Envelope odwołuje się do ModeID i ErrorCode, a testy z assets/ do Modes,
    # MessageDirection i ErrorMessages; kontrakt bez którejś sekcji musi się nadal kompilować.
    modes = contract.get("modes", [])
    w("// ModeID identyfikuje tryb sesyjny w postaci środowisko.moduł.")
    w("type ModeID string")
    w("")
    if modes:
        w("const (")
        for m in modes:
            const = "Mode" + pascal(m["id"])
            line = '\t{} ModeID = "{}"'.format(const, m["id"])
            w(line + dok(m.get("doc")))
        w(")")
        w("")
    w("// ModeInfo opisuje tryb: do jakiego środowiska i modułu należy oraz jak jest izolowany.")
    w("type ModeInfo struct {")
    w('\tID          ModeID `json:"id"`')
    w('\tEnvironment string `json:"environment"`')
    w('\tModule      string `json:"module"`')
    w('\tIsolation   string `json:"isolation"`')
    w('\tDoc         string `json:"doc,omitempty"`')
    w("}")
    w("")
    w("// Modes to rejestr wszystkich trybów sesyjnych zadeklarowanych w kontrakcie.")
    w("var Modes = map[ModeID]ModeInfo{")
    for m in modes:
        const = "Mode" + pascal(m["id"])
        w('\t{}: {{ID: {}, Environment: "{}", Module: "{}", Isolation: "{}", Doc: {}}},'.format(
            const, const, m["environment"], m["module"], m["isolation"], lit(m.get("doc"))))
    w("}")
    w("")
    w("// LookupMode zwraca opis trybu i informację, czy tryb istnieje w kontrakcie.")
    w("func LookupMode(id ModeID) (ModeInfo, bool) {")
    w("\tinfo, ok := Modes[id]")
    w("\treturn info, ok")
    w("}")
    w("")

    messages = contract.get("messages", [])
    w("// MessageType to nazwa komunikatu na drucie.")
    w("type MessageType string")
    w("")
    if messages:
        w("const (")
        for msg in messages:
            line = '\tMsg{} MessageType = "{}"'.format(msg["name"], wire_name(msg))
            w(line + dok(msg.get("doc")))
        w(")")
        w("")
    w("// MessageDirection mówi, kto może wysłać dany komunikat.")
    w("var MessageDirection = map[MessageType]string{")
    for msg in messages:
        w('\tMsg{}: "{}",'.format(msg["name"], msg["direction"]))
    w("}")
    w("")
    w("// MessageResponse wiąże komunikat żądania z komunikatem odpowiedzi (pole response w kontrakcie).")
    w("var MessageResponse = map[MessageType]MessageType{")
    for msg in messages:
        if msg.get("response"):
            w("\tMsg{}: Msg{},".format(msg["name"], msg["response"]))
    w("}")
    w("")
    w("// NewPayload zwraca pustą strukturę ładunku dla danego typu komunikatu.")
    w("// Dzięki temu dekoder nie musi znać mapowania - kontrakt trzyma je w jednym miejscu.")
    w("func NewPayload(t MessageType) (any, bool) {")
    with_payload = [msg for msg in messages if msg.get("payload")]
    if with_payload:
        w("\tswitch t {")
        for msg in with_payload:
            w("\tcase Msg{}:".format(msg["name"]))
            w("\t\treturn &{}{{}}, true".format(msg["payload"]))
        w("\t}")
    w("\treturn nil, false")
    w("}")
    w("")
    w("// Envelope to jedyna koperta, w której podróżują wszystkie komunikaty kanału.")
    w("type Envelope struct {")
    w('\tID            string          `json:"id"`')
    w('\tCorrelationID string          `json:"correlation_id,omitempty"`')
    w('\tSessionID     string          `json:"session_id,omitempty"`')
    w('\tModeID        ModeID          `json:"mode_id,omitempty"`')
    w('\tChannel       string          `json:"channel"`')
    w('\tSeq           uint64          `json:"seq"`')
    w('\tType          MessageType     `json:"type"`')
    w('\tPayload       json.RawMessage `json:"payload,omitempty"`')
    w('\tErrorCode     ErrorCode       `json:"error_code,omitempty"`')
    w('\tErrorMessage  string          `json:"error_message,omitempty"`')
    w("}")
    w("")

    if contract.get("commands"):
        w("// CommandName to nazwa komendy Tauri wołanej z interfejsu.")
        w("type CommandName string")
        w("")
        w("const (")
        for c in contract["commands"]:
            line = '\tCmd{} CommandName = "{}"'.format(pascal(c["name"]), c["name"])
            w(line + dok(c.get("doc")))
        w(")")
        w("")

    errors = contract.get("errors", [])
    w("// ErrorCode to ustalony w kontrakcie kod błędu. Treść komunikatu nigdy nie zawiera danych sprawy.")
    w("type ErrorCode string")
    w("")
    if errors:
        w("const (")
        for e in errors:
            line = '\tErr{} ErrorCode = "{}"'.format(error_const(e["code"]), e["code"])
            w(line + dok(e.get("doc")))
        w(")")
        w("")
    w("// ErrorMessages trzyma bezpieczne, ogólne treści komunikatów dla każdego kodu.")
    w("var ErrorMessages = map[ErrorCode]string{")
    for e in errors:
        w("\tErr{}: {},".format(error_const(e["code"]), lit(e.get("message"))))
    w("}")
    w("")

    return "\n".join(out).rstrip() + "\n"


# ------------------------------------------------------------------ render TS

def render_ts(contract) -> str:
    out = []
    w = out.append

    w("// Kod generowany automatycznie przez scripts/contract_tool.py - NIE EDYTOWAĆ RĘCZNIE.")
    w("// Źródło prawdy: shared/contract.json. Zmiany wprowadzaj tam i uruchom ponownie generator.")
    w("")
    w("/** Wersja kontraktu, z której wygenerowano ten plik. */")
    w('export const CONTRACT_VERSION = "{}" as const;'.format(contract["contractVersion"]))
    w("")
    w("/** Skrót kontraktu - porównywany z rdzeniem Go przy uścisku dłoni. */")
    w('export const CONTRACT_HASH = "{}" as const;'.format(contract_hash(contract)))
    w("")

    for e in contract.get("enums", []):
        if e.get("doc") and DOC_COMMENTS:
            w("/** {} */".format(e["doc"]))
        w("export const {} = [".format(snake(e["name"]).upper()))
        for v in e["values"]:
            comment = dok(v.get("doc"))
            w('  "{}",{}'.format(v["value"], comment))
        w("] as const;")
        w("export type {} = (typeof {})[number];".format(e["name"], snake(e["name"]).upper()))
        w("export function is{}(v: unknown): v is {} {{".format(e["name"], e["name"]))
        w("  return typeof v === \"string\" && ({} as readonly string[]).includes(v);".format(snake(e["name"]).upper()))
        w("}")
        w("")

    for t in contract.get("types", []):
        if t.get("doc") and DOC_COMMENTS:
            w("/** {} */".format(t["doc"]))
        w("export interface {} {{".format(t["name"]))
        for f in t.get("fields", []):
            jkey = f.get("json") or snake(f["name"])
            opt = "?" if f.get("optional") else ""
            comment = dok(f.get("doc"))
            w("  {}{}: {};{}".format(jkey, opt, ts_type(f.get("type", "")), comment))
        w("}")
        w("")

    # Rejestry emitowane zawsze - Envelope odwołuje się do ModeId i ErrorCode,
    # a test contract.test.ts do MODES, MESSAGE_DIRECTION i MODULES_BY_ENVIRONMENT.
    modes = contract.get("modes", [])
    w("/** Identyfikator trybu sesyjnego: środowisko.moduł. */")
    w("export const MODE_IDS = [")
    for m in modes:
        w('  "{}",'.format(m["id"]))
    w("] as const;")
    w("export type ModeId = (typeof MODE_IDS)[number];")
    w("")
    w("export interface ModeInfo {")
    w("  id: ModeId;")
    w("  environment: string;")
    w("  module: string;")
    w("  isolation: string;")
    w("  doc?: string;")
    w("}")
    w("")
    w("/** Rejestr wszystkich trybów sesyjnych zadeklarowanych w kontrakcie. */")
    w("export const MODES: Record<ModeId, ModeInfo> = {")
    for m in modes:
        doc = ", doc: {}".format(lit(m.get("doc"))) if m.get("doc") else ""
        w('  "{}": {{ id: "{}", environment: "{}", module: "{}", isolation: "{}"{} }},'.format(
            m["id"], m["id"], m["environment"], m["module"], m["isolation"], doc))
    w("};")
    w("")
    w("export function isModeId(v: unknown): v is ModeId {")
    w('  return typeof v === "string" && (MODE_IDS as readonly string[]).includes(v);')
    w("}")
    w("")
    envs = []
    for m in modes:
        if m["environment"] not in envs:
            envs.append(m["environment"])
    w("/** Środowiska pracy - wyprowadzone z rejestru trybów. */")
    w("export const ENVIRONMENTS = [{}] as const;".format(", ".join('"{}"'.format(e) for e in envs)))
    w("export type Environment = (typeof ENVIRONMENTS)[number];")
    w("")
    w("/** Moduły dostępne w danym środowisku. */")
    w("export const MODULES_BY_ENVIRONMENT: Record<Environment, ModeId[]> = {")
    for env in envs:
        ids = [m["id"] for m in modes if m["environment"] == env]
        w('  "{}": [{}],'.format(env, ", ".join('"{}"'.format(i) for i in ids)))
    w("};")
    w("")

    messages = contract.get("messages", [])
    w("/** Nazwy komunikatów na drucie. */")
    w("export const MESSAGE_TYPES = [")
    for msg in messages:
        comment = dok(msg.get("doc"))
        w('  "{}",{}'.format(wire_name(msg), comment))
    w("] as const;")
    w("export type MessageType = (typeof MESSAGE_TYPES)[number];")
    w("")
    w("/** Mapowanie komunikat -> typ ładunku. Pozwala napisać typowanego klienta bez rzutowania. */")
    w("export interface MessagePayloads {")
    for msg in messages:
        payload = msg.get("payload")
        w('  "{}": {};'.format(wire_name(msg), payload if payload else "undefined"))
    w("}")
    w("")
    w("/** Kto może wysłać dany komunikat. */")
    w("export const MESSAGE_DIRECTION: Record<MessageType, \"clientToServer\" | \"serverToClient\" | \"bidirectional\"> = {")
    for msg in messages:
        w('  "{}": "{}",'.format(wire_name(msg), msg["direction"]))
    w("};")
    w("")
    by_name = {msg["name"]: msg for msg in messages}
    w("/** Komunikat żądania -> komunikat odpowiedzi (pole response w kontrakcie). */")
    w("export const MESSAGE_RESPONSE: Partial<Record<MessageType, MessageType>> = {")
    for msg in messages:
        if msg.get("response") and msg["response"] in by_name:
            w('  "{}": "{}",'.format(wire_name(msg), wire_name(by_name[msg["response"]])))
    w("};")
    w("")
    w("/** Jedyna koperta, w której podróżują wszystkie komunikaty kanału. */")
    w("export interface Envelope<T extends MessageType = MessageType> {")
    w("  id: string;")
    w("  correlation_id?: string;")
    w("  session_id?: string;")
    w("  mode_id?: ModeId;")
    w("  channel: string;")
    w("  seq: number;")
    w("  type: T;")
    w("  payload?: MessagePayloads[T];")
    w("  error_code?: ErrorCode;")
    w("  error_message?: string;")
    w("}")
    w("")

    if contract.get("commands"):
        w("/** Komendy Tauri wołane z interfejsu. */")
        w("export interface Commands {")
        for c in contract["commands"]:
            req = c.get("request") or "void"
            res = c.get("response") or "void"
            comment = dok(c.get("doc"))
            w('  "{}": {{ request: {}; response: {} }};{}'.format(c["name"], req, res, comment))
        w("}")
        w("export type CommandName = keyof Commands;")
        w("")

    errors = contract.get("errors", [])
    w("/** Kody błędów. Treść komunikatu nigdy nie zawiera danych sprawy. */")
    w("export const ERROR_CODES = [")
    for e in errors:
        comment = dok(e.get("doc"))
        w('  "{}",{}'.format(e["code"], comment))
    w("] as const;")
    w("export type ErrorCode = (typeof ERROR_CODES)[number];")
    w("")
    w("export const ERROR_MESSAGES: Record<ErrorCode, string> = {")
    for e in errors:
        w("  {}: {},".format(json.dumps(e["code"]), lit(e.get("message"))))
    w("};")
    w("")

    return "\n".join(out).rstrip() + "\n"


# ------------------------------------------------------------- formatowanie Go

def gofmt(src: str, tool: str = "gofmt"):
    """Przepuszcza wygenerowany kod przez gofmt.

    Własne wyrównanie kolumn byłoby powielaniem reguł, które i tak należą do gofmt
    i mogą się zmienić między wersjami Go. Wolimy zawołać narzędzie i mieć pewność,
    że wynik przechodzi `gofmt -l` bez zastrzeżeń.

    Zwraca (kod, ostrzeżenie_albo_None). Przy braku gofmt oddaje kod bez zmian.
    """
    exe = shutil.which(tool)
    if not exe:
        return src, ("nie znaleziono {} w PATH - kod Go nie został sformatowany; "
                     "na maszynie z Go wynik będzie inny, co da fałszywy rozjazd".format(tool))
    try:
        done = subprocess.run([exe], input=src, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=LIMIT_CZASU_GOFMT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return src, "gofmt nie wystartował ({}) - kod Go bez formatowania".format(exc)
    if done.returncode != 0:
        return src, "gofmt zgłosił błąd: {}".format(done.stderr.strip()[:400])
    return done.stdout, None


# ---------------------------------------------------------------- podkomendy

def w_korzeniu(root: Path, wzgledna, opis: str) -> Path:
    """Ścieżka docelowa ograniczona do korzenia repozytorium.

    Ścieżka pochodzi z DANYCH (contract.json, argument --dest), a nie z kodu:
    `root / "/abs"` daje w pathlib ścieżkę absolutną, a `..` nie jest odcinane,
    więc plik danych rozstrzygałby, gdzie narzędzie zapisze wygenerowany kod.
    """
    if not isinstance(wzgledna, str) or not wzgledna.strip():
        print("BŁĄD: {} musi być niepustym łańcuchem".format(opis), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    if Path(wzgledna).is_absolute():
        print("BŁĄD: {} ({}) jest ścieżką absolutną - podawaj ścieżkę względną "
              "wobec korzenia repozytorium".format(opis, wzgledna), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    cel = (root / wzgledna).resolve()
    if cel != root and root not in cel.parents:
        print("BŁĄD: {} ({}) wskazuje poza korzeń repozytorium {}".format(opis, wzgledna, root),
              file=sys.stderr)
        sys.exit(EXIT_INVALID)
    return cel


def resolve_targets(contract, root: Path):
    gen = contract.get("generated", {})
    if not isinstance(gen, dict):
        gen = {}
    go = gen.get("go") if isinstance(gen.get("go"), dict) else {}
    ts = gen.get("ts") if isinstance(gen.get("ts"), dict) else {}
    return (w_korzeniu(root, go.get("path", "shared/contract.go"), "generated.go.path"),
            w_korzeniu(root, ts.get("path", "client/src/contract.ts"), "generated.ts.path"))


def load(path: Path):
    try:
        dane = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("BŁĄD: nie znaleziono {}".format(path), file=sys.stderr)
        sys.exit(EXIT_IO)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print("BŁĄD: {} nie da się odczytać jako JSON UTF-8: {}".format(path, exc), file=sys.stderr)
        sys.exit(EXIT_INVALID)
    except OSError as exc:
        print("BŁĄD: {} nie da się odczytać: {}".format(path, exc), file=sys.stderr)
        sys.exit(EXIT_IO)
    if not isinstance(dane, dict):
        print("BŁĄD: {} musi zawierać obiekt JSON, zawiera: {}".format(path, type(dane).__name__),
              file=sys.stderr)
        sys.exit(EXIT_INVALID)
    return dane


def wczytaj_wygenerowany(path: Path) -> str:
    """Treść pliku wygenerowanego wcześniej. Pliku nieczytelnego jako UTF-8 nie
    da się porównać z kontraktem, więc jest zgłaszany jako rozjazd, nie traceback."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as blad:
        print("ROZJAZD: {} nie da się odczytać jako UTF-8 ({}) - traktuję jako rozjazd"
              .format(path, blad), file=sys.stderr)
        return "\0"


def report(errs) -> None:
    print("Kontrakt niepoprawny - błędów: {}".format(len(errs)), file=sys.stderr)
    for e in errs:
        print("  - {}".format(e), file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generator i strażnik kontraktu Danaco Console")
    ap.add_argument("command", choices=["validate", "gen", "check", "install"])
    ap.add_argument("--contract", default="shared/contract.json", help="ścieżka do contract.json")
    ap.add_argument("--root", default=".", help="korzeń repozytorium (domyślnie bieżący katalog)")
    ap.add_argument("--doc-comments", choices=["all", "none"], default="all",
                    help="czy przenosić pola doc z kontraktu do komentarzy w kodzie")
    ap.add_argument("--gofmt", default="gofmt", help="nazwa albo ścieżka narzędzia formatującego Go")
    ap.add_argument("--no-gofmt", action="store_true",
                    help="pomija formatowanie kodu Go (używaj tylko bez zainstalowanego Go)")
    ap.add_argument("--dest", default="tools/contract_tool.py",
                    help="dla podkomendy install: docelowa ścieżka w repozytorium")
    args = ap.parse_args()

    global DOC_COMMENTS
    DOC_COMMENTS = args.doc_comments == "all"

    root = Path(args.root).resolve()
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = root / contract_path

    if args.command == "install":
        dest = w_korzeniu(root, args.dest, "--dest")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
        dest.chmod(0o755)
        print("Zainstalowano narzędzie kontraktu w {}".format(dest))
        print("Wersjonuj je razem z kontraktem - inaczej dwie osoby wygenerują różny kod")
        print("z tego samego JSON-a. Uruchamiaj przez: python3 {} gen --root .".format(args.dest))
        return EXIT_OK

    contract = load(contract_path)
    errs = validate(contract)
    if errs:
        report(errs)
        return EXIT_INVALID

    if args.command == "validate":
        print("Kontrakt poprawny: wersja {}, skrót {}, typów {}, trybów {}, komunikatów {}.".format(
            contract["contractVersion"], contract_hash(contract),
            len(contract.get("types", [])), len(contract.get("modes", [])),
            len(contract.get("messages", []))))
        return EXIT_OK

    go_path, ts_path = resolve_targets(contract, root)
    go_src = render_go(contract)
    if not args.no_gofmt:
        go_src, ostrzezenie = gofmt(go_src, args.gofmt)
        if ostrzezenie:
            print("UWAGA: {}".format(ostrzezenie), file=sys.stderr)
    ts_src = render_ts(contract)

    if args.command == "gen":
        for path, src in ((go_path, go_src), (ts_path, ts_src)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(src, encoding="utf-8")
            print("zapisano {}".format(path.relative_to(root) if path.is_relative_to(root) else path))
        print("Kontrakt {} (skrót {}) rozprowadzony do Go i TypeScriptu.".format(
            contract["contractVersion"], contract_hash(contract)))
        return EXIT_OK

    drift = False
    for path, src in ((go_path, go_src), (ts_path, ts_src)):
        current = wczytaj_wygenerowany(path)
        if current != src:
            drift = True
            print("ROZJAZD: {} nie odpowiada kontraktowi".format(path), file=sys.stderr)
            diff = difflib.unified_diff(
                current.splitlines(), src.splitlines(),
                fromfile="{} (na dysku)".format(path.name),
                tofile="{} (z kontraktu)".format(path.name), lineterm="", n=2)
            for i, line in enumerate(diff):
                if i > 60:
                    print("  ... (dalsze różnice pominięte)", file=sys.stderr)
                    break
                print("  {}".format(line), file=sys.stderr)
    if drift:
        print("\nUruchom: python3 contract_tool.py gen --root {}".format(root), file=sys.stderr)
        return EXIT_DRIFT

    print("Bez rozjazdu: Go i TypeScript zgodne z kontraktem {}.".format(contract["contractVersion"]))
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_IO)
    except Exception as blad:  # noqa: BLE001 - kod 1 nie występuje w kontrakcie narzędzia
        print("BŁĄD: awaria narzędzia kontraktu: {!r}".format(blad), file=sys.stderr)
        sys.exit(EXIT_IO)
