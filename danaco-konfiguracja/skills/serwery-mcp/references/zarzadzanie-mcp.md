# MCP w organizacji: `managed-mcp.json`, `managedMcpServers`, listy dozwolone i zakazane

Źródło: `cc:managed-mcp` (stan 01.10.2026).

## 1. Trzy wzorce

| Wzorzec | Mechanizm | Skutek |
|---|---|---|
| wyłączna kontrola | `managed-mcp.json` w ścieżce systemowej (Linux `/etc/claude-code/managed-mcp.json`, macOS `/Library/Application Support/ClaudeCode/`, Windows `C:\Program Files\ClaudeCode\`) | ładują się tylko serwery z pliku (+ `managedMcpServers`, serwery w procesie hosta, Chrome po zgodzie); użytkownik nie doda żadnego, wtyczki i `--mcp-config` wyłączone, konektory claude.ai wyłączone |
| dodatek | `managedMcpServers` w ustawieniach zarządzanych (≥2.1.259) | serwery HTTP/SSE dla każdego obok własnych użytkownika; pierwszeństwo nad duplikatami; omija listę dozwolonych |
| polityka | `allowedMcpServers`, `deniedMcpServers` (+ `allowManagedMcpServersOnly`) | filtr na serwery z każdego źródła |

`managed-mcp.json` nie przechodzi przez ustawienia serwerowe (to osobny plik); do
dostarczania przez konsolę służy `managedMcpServers`. Plik czyta każdy użytkownik —
żadnych sekretów w `env`; poświadczenia przez `${VAR}`, OAuth, `headersHelper`.
Pusta mapa `{"mcpServers": {}}` = MCP wyłączony (poza `managedMcpServers` i dopuszczonymi).

## 2. Konflikty z flagami

Przy czytelnym `managed-mcp.json`: `--mcp-config` na stacji roboczej → błąd startu
(„You cannot dynamically configure MCP servers when an enterprise MCP config is present”);
`--strict-mcp-config` → błąd startu wszędzie. **Na hoście produktu osadzającego CLI,
który używa `--mcp-config`, nie wdrażaj `managed-mcp.json`** — użyj list i
`managedMcpServers` albo własnego pliku zarządzanego w izolacji procesu.

## 3. Wpisy list

| Klucz | Dopasowuje | Uwagi |
|---|---|---|
| `serverUrl` | adres serwera zdalnego, `*` w dowolnym miejscu (także schemat) | host bez wielkości liter; wzorzec bez ścieżki = każda ścieżka |
| `serverCommand` | dokładne polecenie i argumenty serwera stdio | kolejność i liczba argumentów muszą się zgadzać |
| `serverName` | etykieta nadana przez użytkownika | **nie jest kontrolą bezpieczeństwa**; w allow tylko `[A-Za-z0-9_-]` |

Stany `allowedMcpServers`: brak = wszystko; `[]` = nic (poza pomijającymi sprawdzenie);
lista = tylko pasujące. `deniedMcpServers`: brak lub `[]` = nic nie zablokowane.

## 4. Ocena serwera (przed każdym ładowaniem i ponownym połączeniem)

1. scalenie list ze wszystkich zakresów (`allowManagedMcpServersOnly` → tylko lista
   zarządzana dozwolonych; zakazy zawsze ze wszystkich);
2. zakaz wygrywa zawsze;
3. lista dozwolonych: serwer zdalny musi pasować do `serverUrl` (nazwa liczy się tylko,
   gdy lista nie ma żadnego `serverUrl`), stdio do `serverCommand` (analogicznie);
   sprawdzenie pomijają: `managedMcpServers`, wpisy `managed-mcp.json` bez `${VAR}`,
   serwery wbudowane (Chrome, `ide`), narzędzia Slack sesji Claude Tag, serwery `type: "sdk"`.

Wpisy polityki rozwijają `${VAR}` ze środowiska startowego (plus `env` z managed); rozwinięcie
zmieniające schemat/host/ścieżkę wpisu dozwolonych — wpis ignorowany (≥2.1.219). Do
egzekucji używaj dosłownych adresów i poleceń.

## 5. Dodatkowe przełączniki (tylko managed)

`allowAllClaudeAiMcps` — konektory claude.ai obok `managed-mcp.json`;
`allowClaudeInChromeWithManagedMcp` (≥2.1.282, tylko urządzenie: plik/MDM/HKLM) — Chrome obok.

## 6. Sprawdzenie wdrożenia

1. `claude mcp list` pokazuje tylko serwery zarządzane (+ `managedMcpServers`); sekcja
   „MCP config diagnostics” zgłasza błąd parsowania pliku.
2. `claude mcp add --transport http test https://example.com/mcp` kończy się „Cannot add MCP
   server: enterprise MCP configuration is active…”.
3. Użytkownik widzi blokady w `/mcp`; użycie można monitorować przez OpenTelemetry
   (nazwy serwerów i narzędzi w zdarzeniach `tool_result` przy `OTEL_LOG_TOOL_DETAILS=1`).
