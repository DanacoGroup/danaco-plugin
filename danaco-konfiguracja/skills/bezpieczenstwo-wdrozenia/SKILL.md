---
name: bezpieczenstwo-wdrozenia
description: >
  Bezpieczeństwo wdrożenia Claude Code na produkcję: model zagrożeń (prompt injection, błąd
  modelu, „lethal trifecta”), granice (uprawnienia vs piaskownica vs kontener/VM), zasada
  najmniejszych uprawnień, poświadczenia poza zasięgiem agenta (proxy, apiKeyHelper, SCRUB),
  izolacja dzierżawców, sieć i wyjście, rozszerzenia (MCP, wtyczki, hooki), dane i telemetria,
  aktualizacje, audyt; automatyczna lista kontrolna dla profili stanowisko, ci, usługa.
  Stosuj przed uruchomieniem produkcyjnym, przy przeglądzie bezpieczeństwa, „czy to bezpieczne”,
  „hardening”, „lista kontrolna wdrożenia”, „wielu użytkowników na jednym serwerze”.
---

# Bezpieczeństwo wdrożenia

## Kiedy stosować

Przed każdym wdrożeniem, w którym Claude Code działa **bez człowieka zatwierdzającego każdy
krok** (CI, usługa, agent w tle) albo obsługuje treści niezaufane (repozytoria obce, strony,
dokumenty klientów, wiele dzierżawców).

## Model zagrożeń w jednym zdaniu

Treść, którą agent czyta (plik, strona, wynik MCP, issue), może zawierać instrukcje; gdy agent
ma jednocześnie **dostęp do danych prywatnych**, **kontakt z treścią niezaufaną** i **kanał
wyjścia** (sieć, push, publikacja), atak może wyprowadzić dane. Każda warstwa poniżej usuwa
jeden z tych trzech elementów albo ogranicza szkody.

## Warstwy (od najsłabszej do najsilniejszej)

| Warstwa | Co daje | Czego NIE daje |
|---|---|---|
| CLAUDE.md / instrukcja | wskazówki | żadnej gwarancji |
| reguły uprawnień | bramka narzędzi; deny > ask > allow; Bash analizowany jako AST | nie jest piaskownicą; dopasowuje tekst polecenia (`/bin/rm`, `sh -c` omijają `Bash(rm *)`) |
| hooki `PreToolUse` | dowolna logika decyzji, także w `bypassPermissions` | tylko tam, gdzie hook się uruchomi |
| piaskownica Bash (bwrap/Seatbelt) | pliki i sieć na poziomie systemu dla Bash i podprocesów | nie obejmuje narzędzi Read/Edit/WebFetch (te — uprawnieniami), brak inspekcji TLS (domain fronting) |
| kontener / gVisor / VM | granica jądra lub sprzętu, `--network none` + proxy | konfiguracja zależna od wdrożenia |
| proxy poza granicą | lista domen, wstrzykiwanie poświadczeń, logi | — |

## Procedura

1. Określ profil: `stanowisko`, `ci`, `usluga` (osadzanie CLI, wielu użytkowników).
2. Wygeneruj konfigurację: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generuj_ustawienia.py" --profil czat|kod|ci|tylko-odczyt …`
   albo złóż własną z pakietów `uprawnienia-i-tryby`, `piaskownica-i-izolacja`, `headless-i-osadzanie`.
3. Uruchom listę kontrolną:
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/bezpieczenstwo-wdrozenia/scripts/lista_kontrolna.py" --profil usluga --ustawienia u.json --flagi flagi.txt --zmienne env.txt --markdown raport.md`
   — 28 punktów (uprawnienia, piaskownica i sieć, sekrety i hooki, rozszerzenia, izolacja
   dzierżawców i wersje, koszty i prywatność); kod 1 przy brakach wymaganych.
4. Sprawdź zachowanie bez modelu: `proba_regul.py` (uprawnienia), `proba_piaskownicy.py`
   (pliki, sieć, poświadczenia), `proba_cli.py` (init: narzędzia, tryb, MCP, polecenia).
5. Uzupełnij warstwy poza CLI wg `references/lista-kontrolna-produkcji.md` (kontener, proxy,
   prawa plików, retencja, audyt) i zapisz decyzje w dokumentacji wdrożenia.
6. Po każdej aktualizacji CLI: ponów kroki 3–4 (zachowanie zmienia się między wersjami).

## Najważniejsze zasady

- Tryb zawsze jawny; `bypassPermissions` tylko w odizolowanym kontenerze/VM bez sieci i sekretów,
  na stanowiskach zablokowany (`disableBypassPermissionsMode`).
- Sieć ograniczaj piaskownicą lub kontenerem, nie regułami `Bash(curl *)`.
- Sekrety nigdy w `env` ustawień ani w repozytorium; `apiKeyHelper`, `otelHeadersHelper`,
  `headersHelper` MCP, proxy wstrzykujące, `sandbox.credentials` (deny/mask).
- Usługa: `--setting-sources ""`, `--strict-mcp-config`, `--disable-slash-commands`, katalogi
  dzierżawcy (`CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_PROJECT_DIR_NAME`), pamięć wyłączona,
  przypięta wersja, limity tur/budżetu, brak publikacji i zdalnego dostępu.
- Rozszerzenia tylko z zaufanych źródeł: `strictKnownMarketplaces`, `allowedMcpServers`,
  `allowManagedHooksOnly`, `allowedHttpHookUrls`; serwery MCP pisane samodzielnie lub sprawdzone.

## Pułapki (próby 2.1.286)

- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` wymusza tryb `default` i zostawia puste zaślepki w katalogu
  roboczym — planuj listę allow zamiast `acceptEdits` i sprzątanie katalogu.
- Goła reguła `Edit` nie obejmuje `Write` (ani w allow, ani w deny) — `Edit(./**)`.
- `-p` w niezaufanym folderze **uruchamia hooki projektu** i ładuje jego `env` — dla repozytoriów
  obcych `--setting-sources ""` lub `--bare`.
- Polecenia z `$ZMIENNA` nie pasują do reguł allow („Contains simple_expansion”).
- `-p` bez `--permission-mode` startuje w `auto`, gdy flagi funkcji nie są pobierane (≥2.1.285).
- Wbudowane wtyczki (`cc-plugin-sec-default`, `agents-md`) ładują się nawet przy
  `--setting-sources ""` (nie przy `--bare`) — uwzględnij je w przeglądzie.

## Szablony

- `examples/kontener-agenta.sh` — uruchomienie CLI w utwardzonym kontenerze (bez sieci, proxy przez gniazdo, kod tylko do odczytu).
- `examples/raport-listy-kontrolnej.md` — przykładowy raport `--markdown` dla profilu usługi (wygenerowany).

## Referencje

- `references/lista-kontrolna-produkcji.md` — pełna lista kontrolna (CLI + infrastruktura), z odniesieniem do punktów skryptu.
- `references/model-zagrozen-i-izolacja.md` — zagrożenia, technologie izolacji, wzorzec proxy, pliki z poświadczeniami, dane i retencja.
