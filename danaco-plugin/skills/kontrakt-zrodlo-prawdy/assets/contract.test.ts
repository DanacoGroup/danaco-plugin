// Test Vitest pilnujący, że wygenerowany kontrakt TypeScriptu odpowiada źródłu prawdy.
// Umieść w client/src/contract.test.ts.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import {
  CONTRACT_HASH,
  CONTRACT_VERSION,
  ENVIRONMENTS,
  ERROR_CODES,
  ERROR_MESSAGES,
  MESSAGE_DIRECTION,
  MESSAGE_RESPONSE,
  MESSAGE_TYPES,
  MODE_IDS,
  MODES,
  MODULES_BY_ENVIRONMENT,
} from "./contract";

// Ścieżka względem client/src - dostosuj, jeśli układ katalogów jest inny.
const CONTRACT_PATH = new URL("../../shared/contract.json", import.meta.url);

function stableStringify(value: unknown): string {
  // Ta sama postać kanoniczna co w contract_tool.py: klucze posortowane, bez zbędnych spacji.
  if (Array.isArray(value)) return "[" + value.map(stableStringify).join(",") + "]";
  if (value && typeof value === "object") {
    const entries = Object.keys(value as object)
      .sort()
      .map((k) => JSON.stringify(k) + ":" + stableStringify((value as Record<string, unknown>)[k]));
    return "{" + entries.join(",") + "}";
  }
  return JSON.stringify(value);
}

function canonicalHash(contract: unknown): string {
  return createHash("sha256").update(stableStringify(contract)).digest("hex").slice(0, 16);
}

describe("kontrakt", () => {
  const raw = JSON.parse(readFileSync(CONTRACT_PATH, "utf-8"));

  it("skrót klienta zgadza się ze źródłem prawdy", () => {
    // Łapie sytuację, w której ktoś zregenerował tylko stronę Go.
    expect(CONTRACT_HASH).toBe(canonicalHash(raw));
    expect(CONTRACT_VERSION).toBe(raw.contractVersion);
  });

  it("rejestr trybów jest spójny", () => {
    expect(MODE_IDS.length).toBeGreaterThan(0);
    for (const id of MODE_IDS) {
      expect(MODES[id]).toBeDefined();
      expect(MODES[id].id).toBe(id);
      expect(MODES[id].isolation).not.toBe("");
    }
    expect(Object.keys(MODES).length).toBe(MODE_IDS.length);
  });

  it("każdy tryb należy do dokładnie jednego środowiska", () => {
    const zRejestru = ENVIRONMENTS.flatMap((env) => MODULES_BY_ENVIRONMENT[env]);
    expect([...zRejestru].sort()).toEqual([...MODE_IDS].sort());
    expect(new Set(zRejestru).size).toBe(zRejestru.length);
  });

  it("każdy komunikat ma zadeklarowany kierunek", () => {
    for (const typ of MESSAGE_TYPES) {
      expect(MESSAGE_DIRECTION[typ]).toBeDefined();
    }
  });

  it("odpowiedź wskazuje komunikat z rejestru", () => {
    for (const [zadanie, odpowiedz] of Object.entries(MESSAGE_RESPONSE)) {
      expect(MESSAGE_DIRECTION[zadanie as keyof typeof MESSAGE_DIRECTION]).not.toBe("serverToClient");
      expect(MESSAGE_TYPES).toContain(odpowiedz);
    }
  });

  it("każdy kod błędu ma ogólną treść", () => {
    for (const kod of ERROR_CODES) {
      expect(ERROR_MESSAGES[kod]).toBeTruthy();
      // Treść pokazywana użytkownikowi nie może zawierać samego kodu - pilnuje tego też Semgrep.
      expect(ERROR_MESSAGES[kod]).not.toContain(kod);
    }
  });
});
