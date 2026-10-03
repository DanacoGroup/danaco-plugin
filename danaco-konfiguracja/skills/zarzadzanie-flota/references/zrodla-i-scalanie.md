# Źródła zarządzane i ich scalanie

Źródła: `cc:managed-settings`, `cc:server-managed-settings`, `cc:settings` (wyjątki od
pierwszeństwa), `cc:settings-reference` (managedSourcesBehavior, parentSettingsBehavior,
policyHelper, Scope), `cc:admin-setup`, `cc:managed-mcp`.

## 1. Gdzie leży polityka

| Mechanizm | Postać |
|---|---|
| serwerowe | JSON w konsoli; cache `~/.claude/remote-settings.json` (pod `CLAUDE_CONFIG_DIR`) |
| macOS | profil konfiguracji, domena `com.anthropic.claudecode` (zagnieżdżenia jako słowniki, listy jako tablice plist) |
| Windows HKLM / HKCU | wartość `Settings` (`REG_SZ`/`REG_EXPAND_SZ`) z JSON w `…\SOFTWARE\Policies\ClaudeCode` |
| pliki | `managed-settings.json`, katalog `managed-settings.d/` (`*.json`, alfabetycznie, bez ukrytych), `managed-mcp.json`, zarządzany `CLAUDE.md`; Linux/WSL `/etc/claude-code/` |

Scalanie plików (główny, potem drop-iny): skalar — późniejszy; lista — suma bez duplikatów;
obiekt (`env`, `sandbox`) — po kluczu; `fallbackModel`, `modelPicker` — w całości;
`extraKnownMarketplaces`, `managedMcpServers` — wpis o tej samej nazwie w całości.

## 2. Ranking i tryby

1. serwerowe (konsola lub brama; tylko przy bezpośrednim API Anthropic i kwalifikującym poświadczeniu),
2. MDM/HKLM,
3. pliki (główny + drop-iny),
4. HKCU — tylko gdy nad nim nie ma żadnego dokumentu administracyjnego.

„Klucz polityki” = każdy poza `managedSourcesBehavior` i `wslInheritsWindowsSettings`.
Dokument jest „obecny”, gdy ustawia jakikolwiek klucz polityki na wartość różną od `null`
(także nieczytelną).

**first-wins** (domyślnie): pierwsze źródło z kluczem polityki; inne pomijane, poza kluczami:

| Klucz | Zasada |
|---|---|
| `sandbox.network.allowManagedDomainsOnly`, `sandbox.filesystem.allowManagedReadPathsOnly` | `true` gdziekolwiek włącza blokadę; przy blokadzie listy (`allowedDomains` + `WebFetch(domain:)`, `allowRead`) sumowane ze wszystkich źródeł |
| `allowManagedMcpServersOnly` | `true` gdziekolwiek; lista `allowedMcpServers` z najwyższego źródła, które ją ma (≥2.1.273) |
| `deniedMcpServers`, `disableClaudeAiConnectors` | wpis/`true` z dowolnego źródła (≥2.1.273) |
| `sandbox.bwrapPath`, `socatPath`, `ripgrep`, `filesystem.disabled`, `network.strictAllowlist`, `allowAllClaudeAiMcps` | z każdego źródła |
| `useAutoModeDuringPlan`, `syncClaudeAiSkills`, `syncClaudeAiPlugins`, `enableArtifact` | `false` z dowolnego źródła (także użytkownika) wyłącza |
| `maxEffortLevel` | najniższy sufit (≥2.1.267) |
| `attribution` (rezygnacja z trailera) | z każdego poziomu |
| `forceRemoteSettingsRefresh` | z każdego źródła |
| `env` | per zmienna: najwyższe źródło, które ją definiuje (≥2.1.223); wyjątki: jednostka telemetrii (`OTEL_EXPORTER_OTLP_*`, `OTEL_LOG_*`, `OTEL_LOGS_EXPORTER`, tracing beta) z jednego źródła; routing sparowany z `apiKeyHelper`/`otelHeadersHelper` tylko ze źródła wybranego |
| `allowedProviders` | lista maszyny i lista serwerowa — część wspólna (≥2.1.285) |
| klucze logowania przez bramę | nigdy z serwerowych — z najwyższego źródła administracyjnego maszyny |

**merge** (`managedSourcesBehavior: "merge"` w najwyższym źródle, ≥2.1.242):

| Rodzaj | Zasada | Przykłady |
|---|---|---|
| listy | suma | `permissions.allow`, `hooks`, `allowedDomains`, `deniedMcpServers`, `deniedModels` |
| blokady | najsurowsza | `allowManagedHooksOnly`, `disableBypassPermissionsMode`, `crossSessionInbound`, `availableModelsMatch` |
| listy dozwolonych | w całości z najwyższego | `availableModels`, `allowedMcpServers`, `strictKnownMarketplaces`, `allowedChannelPlugins`, `fallbackModel` |
| wartości w całości | z najwyższego | `sandbox.credentials.awsPairs`, `sandbox.ripgrep` |
| `managedMcpServers` | suma nazw, przy kolizji wpis wyższego | |
| tylko najwyższe źródło | ignorowane niżej | `apiKeyHelper`, `forceLoginOrgUUID`, `modelPicker`, `permissions.defaultMode` |
| pozostałe | z najwyższego, które ustawia | `model`, `cleanupPeriodDays` |

## 3. policyHelper i ustawienia hosta

- `policyHelper` (`path`, `timeoutMs`, `refreshIntervalMs`; tylko MDM/plik) — program wyliczający
  politykę przy starcie; jego `managedSettings` jest **jedyną** polityką sesji (poza
  `forceRemoteSettingsRefresh`); naruszenie schematu po naprawach = odmowa startu.
- Ustawienia hosta (SDK `managedSettings`, Desktop, IDE): domyślnie ignorowane, gdy istnieje
  źródło administracyjne; `parentSettingsBehavior: "merge"` — host może tylko zaostrzać, ale jego
  allow i listy piaskownicy przechodzą, jeśli nie ma blokad `allowManaged*Only`.

## 4. Błędy w polityce

- Nieparsowalny JSON pliku/drop-inu/plist/HKLM → **odmowa startu** (nawet przy innym poprawnym
  źródle). Pusty plik = `{}`. Brak pliku — bez skutków. Brak prawa odczytu → sesja bez polityki
  (komunikat w `/status`, `doctor`, stderr `-p`); inny błąd odczytu → wyjście.
- Błędy schematu: wpisy naprawialne pomijane, reszta odrzucana z ostrzeżeniem (dialog,
  stderr `-p`, `claude doctor`).
- Fail closed (≥2.1.282): klucze z jedną wartością restrykcyjną (`allowManagedPermissionRulesOnly`,
  `disableAutoMode`, `skipDangerousModePermissionPrompt`…) przy błędnej wartości działają
  restrykcyjnie; `"true"`/`"false"` w cudzysłowie = wartość logiczna z uwagą w `/status`;
  `disableAllHooks` błędne — pominięte. Bloki `permissions`, `autoMode`, `worktree`,
  `attribution` naprawiane per pole; nieczytelne `deny`/`ask` wstrzymują `allow`.
- Tabela kluczy z własnym zachowaniem: `allowedMcpServers`, `allowedProviders`,
  `allowedHttpHookUrls`, `httpHookAllowedEnvVars`, `allowedChannelPlugins`,
  `strictKnownMarketplaces`, `availableModels` → pusta lista; `availableModelsMatch` → `exact`;
  `forceLoginOrgUUID` → nikt; `crossSessionInbound` → `refuse`; `deniedMcpServers`,
  `deniedModels`, `blockedMarketplaces` → odrzucone w całości z ostrzeżeniem;
  `strictPluginOnlyCustomization` → `true`; piaskownica — per pole, najsurowiej (≥2.1.283).

## 5. Klucze tylko zarządzane (wybór)

`allowAllClaudeAiMcps`, `allowedChannelPlugins`, `allowManagedHooksOnly`,
`allowManagedMcpServersOnly`, `allowManagedPermissionRulesOnly`, `blockedMarketplaces`,
`channelsEnabled`, `disableCommandPluginSources`, `disableSideloadFlags`,
`forceRemoteSettingsRefresh`, `managedMcpServers`, `managedSourcesBehavior`,
`parentSettingsBehavior`, `pluginSuggestionMarketplaces`, `pluginTrustMessage`, `policyHelper`,
`sandbox.filesystem.allowManagedReadPathsOnly`, `sandbox.network.allowManagedDomainsOnly`,
`strictKnownMarketplaces`, `strictPluginOnlyCustomization`, `wslInheritsWindowsSettings`,
a także `requiredMinimumVersion`, `requiredMaximumVersion`, `deniedModels`, `availableModelsMatch`,
`modelPricing`, `allowedProviders`, `claudeMd`. Pełna lista: `scripts/szukaj.py --zasieg Managed`.

## 6. Weryfikacja

| Narzędzie | Co pokazuje |
|---|---|
| `/status` | `Setting sources: Enterprise managed settings (remote|plist|HKLM|file|drop-ins|file + drop-ins|…, merged|HKCU|parent process|helper)`, `Skipped sources` (≥2.1.242) |
| `claude doctor` | odrzucone wpisy ze źródłem i polem, `Managed settings (remote)` (≥2.1.248), `Organization policy` (≥2.1.261), `Auto-updates` |
| `/permissions` | efektywne reguły |
| `claude --debug-file <plik>` | `Remote settings` w logu |
| hook `ConfigChange` | audyt zmian plików lokalnych (nie serwerowych, nie MDM) |
| OTel `managed_settings_resolved` | rozstrzygnięta polityka (z `OTEL_LOG_MANAGED_SETTINGS` — zredagowana treść i skrót) |
