# Instrukcja systemowa — flagi, utrwalanie, znacznik granicy, kontekst dokładany przez CLI

Źródła: `cc:cli-reference` („System prompt flags”), `cc:agent-sdk/modifying-system-prompts`,
`cc:prompt-caching`, `cc:env-vars`, analiza CLI Nexusa (przechwycone żądania 2.1.284),
próby 2.1.286 (atrapa API).

## 1. Flagi

| Flaga | Działanie | Uwagi |
|---|---|---|
| `--system-prompt <tekst>` | zastępuje całą instrukcję domyślną | widoczna w `ps`; wyklucza się z `-file` |
| `--system-prompt-file <plik>` | to samo z pliku | dla długich tekstów |
| `--append-system-prompt <tekst>` | dopisuje na końcu (do domyślnej lub zastępczej) | — |
| `--append-system-prompt-file <plik>` | dopisek z pliku | — |
| `--system-prompt-snapshot on|off` | `on` (domyślne): instrukcja z 1. żądania utrwalona do kompakcji; `off`: przebudowa przy każdym żądaniu | ≥2.1.257; w `--bare` zapis wyłączony, chyba że `on` |
| `--append-subagent-system-prompt <tekst>` | dopisek do instrukcji każdego podagenta (z zagnieżdżonymi; nie fork) | tylko `-p`; ≥2.1.205 |
| `--append-subagent-system-prompt-file <plik>` | to samo z pliku | ≥2.1.261; nie łączy się z wersją tekstową |
| `--exclude-dynamic-system-prompt-sections` | sekcje per użytkownik (np. ścieżka pamięci) do 1. wiadomości | tylko instrukcja domyślna; ignorowana przy `--system-prompt*` |

Zastąpienie, gdy powierzchnia (czat, nie terminal), tożsamość (inny agent), model uprawnień
(bez człowieka) albo zadania (nie kod) różnią się od Claude Code — przejmujesz wtedy
odpowiedzialność za zasady narzędzi i bezpieczeństwa. Dopisek, gdy agent nadal jest
asystentem kodującym.

## 2. Znacznik `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` (≥2.1.275)

Wiersz zawierający tylko znacznik dzieli instrukcję z `--system-prompt(-file)`: część nad
nim — blok stały z punktem cache (od 2.1.275 „cachowany globalnie”), część pod nim — blok
zmienny. Pierwsze wystąpienie dzieli, kolejne są usuwane. Podział tylko przy połączeniu
bezpośrednio z API Anthropic lub Claude Platform on AWS; na Bedrock, Vertex, Foundry i przez
bramę LLM — jeden blok. Próba 2.1.286 przez `ANTHROPIC_BASE_URL` (atrapa): znacznik
usunięty, w żądaniu jeden blok `system[2]` z `cache_control` (TTL 1h). W SDK TypeScript:
tablica `[stała, SYSTEM_PROMPT_DYNAMIC_BOUNDARY, zmienna]`.

`--append-system-prompt` dokleja się na końcu, czyli w części zmiennej.

## 3. Utrwalanie a wznawianie

| Sytuacja | Instrukcja w żądaniu |
|---|---|
| nowa sesja | z flag tego uruchomienia |
| `--resume`, snapshot `on`, inne flagi | **utrwalona z 1. żądania** (nowe flagi działają po kompakcji) |
| `--resume`, snapshot `off` | z flag tego uruchomienia (identyczna treść → trafienie w cache) |
| sesja bez pobierania flag funkcji przed 2.1.268 | zapis wyłączony |
| przed 2.1.265 | każda flaga instrukcji wyłączała zapis, chyba że `on` |

## 4. Struktura żądania (próby)

```
system[0]  x-anthropic-billing-header: cc_version=…; cc_entrypoint=sdk-…   (bez cache)
system[1]  "You are a Claude agent, built on Anthropic's Claude Agent SDK."  (cache)
system[2]  instrukcja z flag (lub domyślna Claude Code)                       (cache)
tools      definicje narzędzi wbudowanych i MCP (przy tool search — odroczone)
messages[0] pierwsza wiadomość: przypomnienia (CLAUDE.md, skille, agenci, instrukcje MCP, # Environment)
```
`CLAUDE_CODE_ATTRIBUTION_HEADER=0` usuwa `system[0]`. Wiersza tożsamości `system[1]` nie da się
usunąć flagami — tożsamość rozstrzyga treść Twojej instrukcji.

## 5. Kontekst dokładany poza instrukcją i jak go wyłączyć

| Kontekst | Wyłączenie |
|---|---|
| CLAUDE.md (wszystkie poziomy) | `--setting-sources` bez źródeł, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` (próba: oba działają) |
| zasady commitów/PR w opisie Bash, migawka git | `includeGitInstructions: false`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` |
| stopka `Co-Authored-By`, stopka PR | `attribution.commit/pr: ""` lub `attribution: false` (≥2.1.281) |
| lista skilli, przypomnienia o zadaniach, zmiany plików | `CLAUDE_CODE_DISABLE_ATTACHMENTS=1` (wyłącza też rozwijanie `@plik`) |
| skille wbudowane i polecenia | `disableBundledSkills`, `--disable-slash-commands` |
| lista agentów wbudowanych | `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` (`-p`) |
| pamięć automatyczna | `autoMemoryEnabled: false`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` |
| styl wyjścia | `outputStyle` |
| krótsza instrukcja i opisy narzędzi | `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1` (eksperyment) |

Podgląd tego, co dostał model: `OTEL_LOG_RAW_API_BODIES=file:<katalog>`, własna brama
(`ANTHROPIC_BASE_URL`), atrapa `scripts/atrapa_api.py`.

## 6. Odpowiedniki Agent SDK

| SDK | CLI |
|---|---|
| `systemPrompt: "tekst"` / `{type:"custom", …, snapshot}` | `--system-prompt(-file)`, `--system-prompt-snapshot` |
| `{type:"preset", preset:"claude_code", append}` | domyślna + `--append-system-prompt(-file)` |
| `excludeDynamicSections: true` | `--exclude-dynamic-system-prompt-sections` |
| tablica z `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` | wiersz `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` |
| `settings: {includeGitInstructions:false, attribution:{…}}` | `--settings` |
| Managed Agents `system` | `--system-prompt-file` w wersjonowanym pliku wydania |
