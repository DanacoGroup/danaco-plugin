# Tryby uprawnień szczegółowo, tryb auto i klasyfikator, `--restricted`

Źródła: `cc:permission-modes`, `cc:auto-mode-config`, `cc:cli-reference`,
`anthropic.com/engineering/claude-code-auto-mode`. Stan: 01.10.2026.

## 1. Tryby

| Tryb | Bez pytania | Uwagi |
|---|---|---|
| `default` (Manual; `manual` ≥2.1.200) | odczyty | wartość w hookach i SDK zawsze `default` |
| `acceptEdits` | odczyty, edycje i `mkdir`, `touch`, `mv`, `cp`, `rm`… w katalogach roboczych | ścieżki chronione nadal pytają |
| `plan` | odczyty (+ polecenia zatwierdzone klasyfikatorem, gdy auto dostępne) | w `-p` i SDK blokady planu obowiązują zawsze |
| `auto` | wszystko z kontrolą klasyfikatora | wymagania niżej |
| `dontAsk` | odczyty, polecenia tylko do odczytu, allow, zgody hooków | `AskUserQuestion`, MCP z `requiresUserInteraction`, ask-reguły → odmowa |
| `bypassPermissions` | wszystko poza akcjami, których żaden tryb nie zatwierdza | nie jako root/`sudo` (poza rozpoznaną piaskownicą); w chmurze z plików ignorowany |

Akcje, których **żaden** tryb nie zatwierdza: reguły ask, konektory organizacji ustawione
na `ask`, `AskUserQuestion` i MCP z `requiresUserInteraction`, `rm`/`rmdir` na ścieżkach
krytycznych, zabezpieczenia wiadomości między sesjami, odczyty poza katalogami roboczymi
przy `blockReadsOutsideWorkingDirectories`.

## 2. Tryb startowy

1. `--permission-mode` / `--dangerously-skip-permissions`;
2. `permissions.defaultMode` (z projektu i local nie działają `auto` i `bypassPermissions`);
3. wbudowany:

| Uruchomienie | Wbudowany tryb |
|---|---|
| dowolny plik ma `disableAutoMode: "disable"` | `default` |
| `-p` lub Agent SDK, sesja pobiera flagi funkcji | `default` |
| `-p` lub Agent SDK, sesja **nie** pobiera flag (inny dostawca, wyłączona telemetria lub ruch) | `auto` od **2.1.285** (wcześniej `default`) |
| terminal, VS Code | `auto` od 2.1.283 |

Pierwsza sesja po instalacji lub aktualizacji może wystartować w innym trybie (flagi
jeszcze nie pobrane). Gdy wybrane `auto` jest niedostępne (model, polityka, wyłączone po
stronie serwera) — sesja startuje w Manual.

Wznowienie `-p --resume`: tryb ustalany jak dla nowego `-p` (plan tylko z hostem uprawnień)
— dlatego jawny `--permission-mode` w każdym przebiegu.

## 3. Tryb auto

**Dostępność**: wszystkie plany (Team/Enterprise — można wyłączyć w managed); modele na
API: Opus 4.6+, Sonnet 4.6+, Fable; na Bedrock/Vertex/Foundry/bramie: Sonnet 5+, Opus 4.7+,
Fable. `CLAUDE_CODE_ENABLE_AUTO_MODE` nie ma skutku od 2.1.207.

**Kolejność decyzji**: (1) reguły allow/ask/deny — z wyjątkami: zapis do ścieżki chronionej
idzie do klasyfikatora mimo allow, ścieżki krytyczne nigdy przez allow, MCP
`requiresUserInteraction` pyta, polecenie z domenami per polecenie idzie do klasyfikatora,
ask z treścią polecenia pyta; (2) odczyty i edycje w katalogu roboczym zatwierdzone
(pierwszy odczyt spoza katalogów pyta); (3) reszta do klasyfikatora; (4) blokada → model
dostaje nazwę reguły (np. `[Data Exfiltration]`).

**Reguły szerokie wyłączane w auto**: `Bash(*)`, `PowerShell(*)`, `Bash(python*)`,
uruchamianie menedżerów pakietów, allow `Agent`, allow `Monitor` (≥2.1.236). Wracają po
wyjściu z auto.

**Klasyfikator widzi**: wiadomości użytkownika, wywołania narzędzi (poza odczytami),
CLAUDE.md; **nie widzi** wyników narzędzi (odporność na wstrzyknięcia). Hook `PostToolUse`
może dodać `classifierContext` (≥2.1.236). Podagenci: ocena zadania przy starcie, każdej
akcji i raportu końcowego; `permissionMode` z frontmattera podagenta ignorowany.

**Koszt i opóźnienie**: klasyfikator działa domyślnie na Sonnet 5 (albo modelu sesji, gdy
`availableModels` wyklucza Sonnet 5); na Enterprise, API i chmurach wywołania liczą się do
zużycia; każda kontrola to dodatkowa runda przed akcją. Sieć w piaskownicy nie dodaje
wywołań per połączenie.

**Ocena po stronie serwera** (≥2.1.271/2.1.278): w żądaniu modelu zamiast osobnego
klasyfikatora; brak werdyktu = odmowa; brama/proxy LLM ucinająca odpowiedzi daje odmowy.
`CLAUDE_CODE_AUTO_MODE_SERVER=0` wymusza własny klasyfikator.

**Progi**: 3 blokady z rzędu lub 20 łącznie → powrót do pytań (nie konfigurowalne);
w `-p` bez hosta akcja nie wykonuje się, praca trwa.

**Domyślnie blokowane**: pobieranie i wykonywanie kodu (`curl | bash`), wysyłanie danych
wrażliwych na zewnątrz, wdrożenia produkcyjne i migracje, masowe kasowanie w chmurze,
nadawanie uprawnień IAM/repozytoriów, zmiany wspólnej infrastruktury. Zaufane: katalog
roboczy i zdalne repozytoria skonfigurowane przed startem (dodane w trakcie — nie, ≥2.1.200).

Skuteczność (artykuł inżynieryjny Anthropic): fałszywe blokady ok. 0,4%, przepuszczenia
akcji „nadgorliwych” ok. 17% — klasyfikator jest kontrolą per akcja, **nie granicą izolacji**.

## 4. Konfiguracja klasyfikatora (`autoMode`)

Czytana z `~/.claude/settings.json`, managed i `--settings`/SDK; **nie** z plików projektu.
Wpisy z zakresów się sumują (deweloper nie usunie wpisów organizacji, ale jego `allow` może
przebić `soft_deny` organizacji — to nie jest twarda polityka; twarde zakazy = `permissions.deny`
w managed).

| Pole | Rola |
|---|---|
| `environment` | proza: organizacja, kontrola wersji, chmury, zaufane kubełki i domeny, usługi, rejestr pakietów, dane wrażliwe, cele produkcyjne, chronione IaC; `"$defaults"` wstawia wpisy wbudowane |
| `hard_deny` | blokady bezwarunkowe |
| `soft_deny` | blokady, które może zdjąć intencja użytkownika lub `allow` |
| `allow` | wyjątki od `soft_deny` |
| `classifyAllShell` (≥2.1.193) | każde polecenie powłoki do klasyfikatora |

Polecenia: `claude auto-mode defaults [--label <prefiks>]` (≥2.1.208) — reguły wbudowane
jako JSON (2.1.286: 17 allow, 72 soft_deny, 1 hard_deny, 21 environment);
`claude auto-mode config` — reguły efektywne; `claude auto-mode reset [-y]` (≥2.1.212);
`/auto-mode-setup` (≥2.1.228, wymaga flag funkcji) szkicuje `environment`;
wyłączenie: `skillOverrides: {"auto-mode-setup": "off"}`.

Wpisy to proza, nie wzorce. Kolejność wdrażania: `$defaults` + kontrola wersji i kluczowe
usługi → zaufane domeny i kubełki → reszta w miarę blokad.

## 5. `--restricted` (≥2.1.248)

Dla harnessu ewaluacyjnego na współdzielonej maszynie: usuwa wbudowane narzędzia
uruchamiające kod i WebFetch, **chyba że wymienisz je w `--tools`** (nie przez `default`),
zamyka narzędzia plikowe w katalogach roboczych, wczytuje tylko managed i `--settings`,
odmawia `bypassPermissions` i sesji chmurowych, klasyfikator nie zatwierdzi ścieżek
chronionych. `CLAUDE_CODE_RESTRICTED=1` tylko w środowisku procesu (z `env` ignorowane).

## 6. Wyłączanie trybów

- `permissions.disableBypassPermissionsMode: "disable"` — bypass niedostępny;
- `disableAutoMode: "disable"` (klucz główny; dokumentacja wspomina także
  `permissions.disableAutoMode`) — auto znika z cyklu, `--permission-mode auto` startuje
  w Manual, wbudowany start `-p` = `default`;
- w managed — nie do zdjęcia przez użytkownika; sesja w auto wychodzi z niego, gdy
  ustawienie dotrze ze źródła administracyjnego (≥2.1.251).
