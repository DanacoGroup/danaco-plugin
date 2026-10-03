# Prompt cache w Claude Code

Źródła: `cc:prompt-caching`, `cc:costs` (Prompt cache statistics), `cc:statusline`
(`prompt_cache`), `cc:agent-sdk/modifying-system-prompts` (cache między użytkownikami),
`cc:llm-gateway-protocol`, próby 2.1.286 na atrapie (`zadania_cache.py`).

## 1. Mechanizm

API dopasowuje **prefiks** żądania dokładnie; zmiana w dowolnym miejscu przelicza wszystko
dalej. Kolejność warstw w żądaniu Claude Code:

| Warstwa | Zawartość | Zmienia się, gdy |
|---|---|---|
| instrukcja systemowa | instrukcje, definicje narzędzi, ścieżka pamięci automatycznej | zmienia się zestaw narzędzi, wersja CLI, instrukcja |
| kontekst projektu | CLAUDE.md, pamięć, reguły bez `paths` | start, `/clear`, `/compact` |
| rozmowa | wiadomości, wyniki narzędzi | każda tura |

Poza tabelą: **model** (osobny cache) i **effort** (na większości modeli osobny cache).

Próba (zrzut żądania): 3 bloki `system`, znaczniki `cache_control` na blokach 2 i 3 instrukcji
oraz na ostatniej wiadomości; beta `prompt-caching-scope-…`, przy 1h — `extended-cache-ttl-…`.

## 2. Co unieważnia, co zachowuje

| Unieważnia (jednorazowo droższa tura) | Zachowuje |
|---|---|
| zmiana modelu (`/model`, `opusplan` przy wejściu/wyjściu z planu, `model` skilla, przełączenie po klasyfikatorze) | edycja plików (przypomnienie w rozmowie) |
| zmiana effortu (poza Opus 5.5, Sonnet 5.5, Fable 5.1 na API/subskrypcji, ≥2.1.260 dla Fable) | edycja CLAUDE.md w trakcie (zadziała po `/clear`/`/compact`) |
| pierwsze włączenie fast mode (nagłówek) | zmiana trybu uprawnień (poza `opusplan`) |
| podłączenie/usunięcie serwera MCP, gdy narzędzia ładowane z góry (bez tool search, np. z `ANTHROPIC_BASE_URL`) | zmiana stylu wyjścia (≥2.1.251 — jako wiadomość) |
| wyłączenie/włączenie wtyczki z serwerami MCP | skille, polecenia, agenci, hooki wtyczek (dopisywane) |
| odmowa całego narzędzia (`Bash`, `Bash(*)`, `"*"`, `mcp__*`) bez tool search | `/recap`, `/rewind`, podagent (osobny cache), `/advisor` |
| kompakcja (warstwa rozmowy) | wznowienie (część niezmieniona i ciepła) |
| usuwanie najstarszych obrazów przy limicie | edycja konfiguracji MCP (do restartu) |
| nowa wersja CLI | |

## 3. Czas życia (TTL)

| Kubełek | Subskrypcja w limicie | Kredyty, klucz API, chmura |
|---|---|---|
| główna rozmowa (`-p` i SDK też) | 1h | 5m |
| reszta (podagenci, workflowy, kompakcja, tytuły) | 5m (wybrane pomocnicze 1h) | 5m |

Kolejność: `FORCE_PROMPT_CACHING_5M=1` → `CLAUDE_CODE_PROMPT_CACHE_TTL` /
`CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` → `promptCacheTtl` / `subagentPromptCacheTtl` →
`experimental.cacheTtl` podagenta → `ENABLE_PROMPT_CACHING_1H=1` → domyślne. Wartości `5m`/`1h`,
inne ignorowane; ≥2.1.242.

Próby 2.1.286 (atrapa, znaczniki w żądaniu):

| Konfiguracja | TTL znaczników |
|---|---|
| token OAuth, bez ustawień | `1h` |
| klucz API, bez ustawień | `5m` |
| klucz API + `promptCacheTtl: "1h"` | `1h` |
| `promptCacheTtl: "1h"` + `FORCE_PROMPT_CACHING_5M=1` | `5m` (beta 1h zniknęła) |
| `DISABLE_PROMPT_CACHING=1` | brak znaczników |

Kontrola w praktyce: `claude -p "hello" --output-format json` → `usage.cache_creation`
(`ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens`).

## 4. Zakres

- Cache API jest izolowany per organizacja (u części dostawców per workspace); w jej obrębie
  dwa żądania z tym samym modelem i prefiksem dzielą wpis.
- Claude Code: instrukcja zawiera **ścieżkę pamięci automatycznej** (`<config>/projects/<projekt>/memory/`),
  więc sesje w różnych katalogach lub z różnym `CLAUDE_CONFIG_DIR` mają różne instrukcje.
  Próba: dwa profile, ten sam `cwd` → różny 3. blok (ścieżka pamięci); z
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` → identyczne 3/3 bloki.
- Katalog roboczy, platforma, powłoka, wersja systemu i stan git trafiają do pierwszej
  wiadomości — sesje kolejne dzielą prefiks tylko przy tym samym stanie git.
- SDK: `excludeDynamicSections: true` przenosi elementy zmienne do pierwszej wiadomości;
  w CLI — `--exclude-dynamic-system-prompt-sections` (tylko z domyślną instrukcją).
- Własna instrukcja (`--system-prompt-file`) ze znacznikiem `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__`:
  podział na bloki tylko przy bezpośrednim API (próba pakietu `instrukcja-systemowa-i-pamiec`).

## 5. Podagenci, fork, workflow

Podagent — własny prefiks i cache (5m, o ile nie `subagentPromptCacheTtl`); fork i `/fork`
czytają cache rodzica; wznowiony podagent czyta własny; workflow wstrzymuje równoległych
agentów o tym samym prefiksie do 5 s, by odczytali cache pierwszego.

## 6. Bramy i dostawcy

- Brama przekazuje `cache_control` → jak u dostawcy; odrzuca 400 → CLI przenosi znacznik na
  ostatnią wiadomość (blok systemowy bez cache); **usuwa po cichu** → cała rozmowa bez cache.
- 1h przez bramę wymaga przekazania `anthropic-beta`; niedostępne w Claude apps gateway.
- `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` — blok kontekstu w środku rozmowy bez cache;
  zmiana effortu unieważnia cache także na Opus 5.5/Sonnet 5.5.
- Bedrock — obsługa cache, minimalny prefiks i 1h zależne od modelu i regionu.

## 7. Pomiar

| Źródło | Co |
|---|---|
| `/usage` | `Prompt cache (main)`: żądania, % wejścia z cache, chybienia, przebudowy oczekiwane, ciepły/zimny, TTL; przyczyna (≥2.1.260) |
| linia statusu | `current_usage`, obiekt `prompt_cache` |
| `-p` | `result.usage` (`cache_read_input_tokens`, `cache_creation_input_tokens`, `cache_creation.ephemeral_*`), `modelUsage` |
| transkrypty | `message.usage` wpisów `assistant` — `scripts/analiza_cache.py` |
| OTel | `claude_code.token.usage` z `type=cacheRead|cacheCreation`, atrybut `query_source` |

Próba `analiza_cache.py` na sesjach konta: 98,7–99,1% wejścia z cache, chybienia przy zmianie
modelu (Opus 4.8 ↔ Opus 5.5, ok. 0,5 mln tokenów zapisu) i po kompakcji.

## 8. Rotacja kont i usługi

Cache nie przechodzi między organizacjami/kontami. Rotacja per tura = każda tura zimna (pełny
zapis prefiksu). Wzorzec: przypisanie rozmowy do konta na czas życia cache (1h lub 5m od
ostatniego żądania), rotacja tylko nowych rozmów lub po wygaśnięciu; to samo konto dla
rozmów o identycznej instrukcji, by dzieliły blok stały.
