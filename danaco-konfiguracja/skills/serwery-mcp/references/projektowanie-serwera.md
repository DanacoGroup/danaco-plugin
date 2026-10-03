# Projektowanie serwera MCP i narzędzi według praktyk Anthropic

Źródła: `pl:managed-agents/tools` („Best practices for custom tool definitions”),
`anthropic.com/engineering/writing-tools-for-agents`, `…/code-execution-with-mcp`,
`cc:mcp` („For MCP server authors”, limity, `_meta`), `pl:agents-and-tools/tool-use/tool-search-tool`,
macierz pełna CLI (projekt `danaco-programy`). Wzorzec: `../examples/serwer_wzorcowy.py`.

## 1. Zasady

| Zasada | Treść | Jak sprawdzić |
|---|---|---|
| bardzo szczegółowe opisy | „najważniejszy czynnik”: co robi, kiedy używać i kiedy nie, znaczenie każdego parametru, ograniczenia; 3–4 zdania, więcej przy złożonych | `sprawdz_mcp.py --polacz` (krótkie opisy) |
| mniej, mocniejszych narzędzi | łącz operacje w jedno narzędzie z parametrem `action`/`akcja` zamiast `create_x`, `review_x`, `merge_x` | liczba narzędzi, podobne nazwy |
| przestrzenie nazw | przedrostek zasobu: `db_query`, `storage_read`, `programy_uruchom` | wspólny przedrostek |
| wynik o wysokim sygnale | stabilne identyfikatory (slug, UUID), tylko pola potrzebne do następnego kroku; długie logi do pliku, ścieżka w wyniku | rozmiar wyniku |
| paginacja i filtry | parametry zawężające zamiast zwracania wszystkiego; domyślne limity | — |
| komunikaty błędów prowadzące | błąd mówi, co poprawić w wywołaniu | — |
| instrukcje serwera | przy tool search ładują się zamiast definicji: kategoria zadań, kiedy szukać narzędzi serwera, kluczowe możliwości; najważniejsze na początku (limit 2048) | długość, `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` |

## 2. Tool search a liczba narzędzi

Przy tool search na starcie są tylko nazwy i instrukcje; każde użycie odroczonego narzędzia
to krok `ToolSearch` (dodatkowa tura). Setki podobnych narzędzi zwiększają niejednoznaczność
wyboru. Dla katalogów (np. 1190 programów) lepsze są 2–3 narzędzia z parametrem nazwy
(`programy_opis(nazwa, zakres)`, `programy_uruchom(nazwa, argumenty, pliki)`) oznaczone
`alwaysLoad`, a lista nazw w kontekście z hooka lub instrukcji. Zmiana definicji narzędzi
ładowanych od startu zmienia prefiks żądania → unieważnia cache rozmów; stałe narzędzia +
zmienny katalog w zasobach lub wyniku narzędzia — nie.

## 3. Adnotacje Claude Code w `_meta` narzędzia

| Klucz | Wartość | Skutek |
|---|---|---|
| `anthropic/alwaysLoad` | `true` | narzędzie od startu, bez kroku wyszukiwania |
| `anthropic/maxResultSizeChars` | liczba ≤ 500 000 | wynik tekstowy do tego progu bez zapisu do pliku (niezależnie od `MAX_MCP_OUTPUT_TOKENS`) |
| `anthropic/requiresUserInteraction` | JSON `true` | każde wywołanie wymaga człowieka; w `dontAsk` i przez prompt tool odmowa; hook „allow” nie pomija (≥2.1.199) |

Adnotacje MCP (`annotations.readOnlyHint` itd.) opisują narzędzie zgodnie z protokołem.

## 4. Schematy wejścia

- właściwości najwyższego poziomu: 1–64 znaki `[A-Za-z0-9_.-]`;
- schemat zgodny z JSON Schema draft 2020-12 (lub z innym `$schema` — wtedy tylko test nazw);
- `anyOf/oneOf/allOf` w korzeniu → CLI scala gałęzie i dopisuje do opisu, które parametry
  idą razem; walidację kombinacji rób po stronie serwera;
- wymagane pola w `required`, opisy każdego pola, `enum` dla wartości zamkniętych.

## 5. Zasoby, prompty, elicitation, `list_changed`

- Zasoby (`resources/list`, `resources/read`) — dane czytane na żądanie (`@serwer:uri`,
  narzędzia `ListMcpResourcesTool`/`ReadMcpResourceTool`); dobre dla dokumentacji programów.
  URI `ui://` i typ `text/html;profile=mcp-app` to UI dla hosta, nie dla modelu.
- Prompty → polecenia `/mcp__serwer__prompt` (w produkcie zwykle blokowane
  `--disable-slash-commands`).
- Elicitation (formularz/URL) — w `-p` bez hosta anulowana; hook `Elicitation` może odpowiedzieć.
- `list_changed` w `capabilities.tools/resources/prompts` — wysyłaj po zmianie katalogu.

## 6. Narzędzie zgody dla produktu (`--permission-prompt-tool`)

Kontrakt sprawdzony próbą (CLI 2.1.286): wejście `{tool_name, input, tool_use_id}`,
wynik tekstem JSON `{"behavior":"allow","updatedInput":…}` albo `{"behavior":"deny","message":…}`.
Implementacja: `examples/serwer_wzorcowy.py`, narzędzie `polityka_zgoda` (polityka:
pierwszy wyraz polecenia z listy, bez poleceń złożonych). CLI ukrywa narzędzie przed modelem.

## 7. Serwer stdio — rzemiosło

- stdout wyłącznie JSON-RPC (jedna wiadomość w wierszu), dzienniki na stderr;
- odpowiadaj na `initialize` wersją protokołu klienta, jeśli ją obsługujesz;
- `notifications/initialized` bez odpowiedzi; `ping` → `{}`;
- nieznana metoda → błąd `-32601`; wynik narzędzia `{"content":[{"type":"text",…}], "isError": false}`;
  błąd wykonania jako `isError: true` z treścią prowadzącą;
- `CLAUDE_PROJECT_DIR` w środowisku serwera; katalogi robocze sesji przez `roots/list`.

## 8. Lista kontrolna serwera produktu

1. Instrukcje ≤ limit, najważniejsze zasady na początku.
2. ≤ 10–15 narzędzi rdzenia z `alwaysLoad`, reszta odroczona.
3. Opisy 3–4 zdania, parametry opisane, `enum` gdzie się da.
4. Wyniki zwięzłe, identyfikatory stabilne, długie treści przez zasób lub plik;
   `maxResultSizeChars` tam, gdzie wynik musi być długi.
5. Narzędzia hooków (`mcp_tool`) i zgody — niewidoczne dla modelu lub odrzucane regułą.
6. `list_changed` przy zmianie katalogu.
7. Próba: `sprawdz_mcp.py --polacz`, potem `proba_cli.py` z `--mcp-config`.
