# Indeks 243 kluczy ustawień według kategorii

Źródło: `https://code.claude.com/docs/en/settings-reference` (kopia z 01.10.2026), opisy po polsku z macierzy pełnej CLI. Kolumna „Zasięg” mówi, z jakich plików klucz działa: `Any file` — każdy plik i `--settings`; `User or managed` — tylko `~/.claude/settings.json`, ustawienia zarządzane i `--settings`; `User, local, or managed` — dodatkowo `.claude/settings.local.json`, bez wspólnego pliku projektu; `Managed` — wyłącznie ustawienia zarządzane; `Global config` — wyłącznie `~/.claude.json` (zapisuje `/config`). „Min. wersja” to wymóg z pierwszego akapitu opisu klucza; wymagania dotyczące pojedynczych wartości (np. `attribution: false` ≥2.1.281) opisuje skill.

## Spis treści

- Model i odpowiedzi (23)
- Uprawnienia (15)
- Piaskownica (38)
- Pamięć i kontekst (13)
- Interfejs i terminal (39)
- Git i atrybucja (7)
- Hooki i automatyzacja (9)
- Wtyczki i skille (22)
- Serwery MCP (10)
- Agenci, sesje i worktree (11)
- Zdalne, desktop i powiadomienia (13)
- Uwierzytelnianie i dostawcy (10)
- Aktualizacje i wersje (4)
- Narzędzia (3)
- Prywatność i telemetria (5)
- Organizacja i ustawienia zarządzane (9)
- Konfiguracja globalna (~/.claude.json) (12)

Szybkie wyszukiwanie: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/szukaj.py" <fraza> --typ klucz --pelny`.

## Model i odpowiedzi (23)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `advisorModel` | Any file | — | O4 | model doradcy (narzędzie advisor) |
| `alwaysThinkingEnabled` | Any file | — | O4 | wyłącza myślenie rozszerzone |
| `availableModels` | Any file | — | O4 | ogranicza modele (także `/model`, `--model`, `model` podagentów, fallback) |
| `availableModelsMatch` | Managed | 2.1.283 | O4 | dokładne wersje w `availableModels` |
| `deniedModels` | Managed | 2.1.283 | O4 | blokada modeli |
| `effortLevel` | Any file | — | O4 | domyślny effort |
| `enforceAvailableModels` | Any file | 2.1.175 | O4 | pilnuje modelu Default w allowliście |
| `fallbackModel` | Any file | — | O4 | łańcuch modeli zapasowych przy przeciążeniu |
| `fastMode` | Any file | — | O4 | tryb szybki (droższy) |
| `fastModePerSessionOptIn` | Any file | — | O4 | wymaga włączania fast per sesja |
| `language` | Any file | — | O1 | język odpowiedzi |
| `maxEffortLevel` | Any file | 2.1.267 | O4 | sufit effortu (≥2.1.267) |
| `model` | Any file | — | O4 | model startowy |
| `modelOverrides` | Any file | — | O4 | mapowanie ID na dostawcę |
| `modelPicker` | User or managed | 2.1.242 | O4 | lista pickera `/model` |
| `modelPricing` | Managed | 2.1.242 | O15 | stawki do raportów kosztów |
| `modelSettings` | Any file | 2.1.251 | O4 | effort i sufit per model (≥2.1.251) |
| `outputStyle` | Any file | — | O3 | styl wyjścia |
| `promptCacheTtl` | Any file | 2.1.242 | O4 | TTL cache głównej rozmowy (≥2.1.242) |
| `showThinkingSummaries` | Any file | — | O4 | podsumowania myślenia w TUI |
| `subagentPromptCacheTtl` | Any file | 2.1.242 | O4 | TTL cache podagentów (≥2.1.242) |
| `switchModelsOnFlag` | Any file | — | O4 | co robić, gdy klasyfikator oznaczy prośbę |
| `ultracode` | Any file | — | O9 | planowanie workflow przy każdym zadaniu |

## Uprawnienia (15)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `allowManagedPermissionRulesOnly` | Managed | — | O6 | tylko reguły zarządzane |
| `autoMode` | User or managed | — | O6 | reguły klasyfikatora auto |
| `autoMode.classifyAllShell` | User or managed | 2.1.193 | O6 | każde polecenie do klasyfikatora |
| `disableAutoMode` | Any file | — | O6 | usuwa tryb auto |
| `permissions` | Any file | — | O6 | reguły allow/ask/deny i tryb startowy |
| `useAutoModeDuringPlan` | User, local, or managed | — | O6 | klasyfikator w trybie plan |
| `permissions.allow` | Any file | — | O6 | pre-akceptowane narzędzia |
| `permissions.ask` | Any file | — | O6 | zawsze pytaj |
| `permissions.deny` | Any file | — | O6 | blokady narzędzi |
| `permissions.additionalDirectories` | Any file | — | O6 | dodatkowe katalogi robocze |
| `permissions.blockReadsOutsideWorkingDirectories` | Any file | 2.1.257 | O6 | plikowe narzędzia nie czytają poza katalogami roboczymi (≥2.1.257) |
| `permissions.defaultMode` | Any file | — | O6 | tryb startowy |
| `permissions.disableBypassPermissionsMode` | Any file | — | O6 | zakaz bypassPermissions |
| `skipAutoPermissionPrompt` | User or managed | — | O6 | pomija komunikat auto |
| `skipDangerousModePermissionPrompt` | User, local, or managed | — | O6 | pomija dialog bypass |

## Piaskownica (38)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `sandbox` | Any file | — | O7 | piaskownica Bash CLI |
| `sandbox.enabled` | Any file | — | O7 | włącza piaskownicę Bash |
| `sandbox.failIfUnavailable` | Any file | — | O7 | twardy błąd, gdy piaskownica nie startuje |
| `sandbox.autoAllowBashIfSandboxed` | Any file | — | O7 | auto-akceptacja Bash w piaskownicy |
| `sandbox.excludedCommands` | Any file | — | O7 | polecenia poza piaskownicą |
| `sandbox.allowUnsandboxedCommands` | Any file | — | O7 | furtka `dangerouslyDisableSandbox` |
| `sandbox.filesystem` | Any file | — | O7 | reguły plików |
| `sandbox.filesystem.allowWrite` | Any file | — | O7 | dodatkowe ścieżki zapisu |
| `sandbox.filesystem.denyWrite` | Any file | — | O7 | blokada zapisu |
| `sandbox.filesystem.denyRead` | Any file | — | O7 | blokada odczytu |
| `sandbox.filesystem.allowRead` | Any file | — | O7 | otwiera odczyt w obszarze denyRead |
| `sandbox.filesystem.allowManagedReadPathsOnly` | Managed | — | O7 | blokada allowRead |
| `sandbox.filesystem.disabled` | User or managed | 2.1.216 | O7 | wyłącza warstwę plików |
| `sandbox.ignoreViolations` | Any file | — | O7 | wycisza raporty naruszeń |
| `sandbox.enableWeakerNestedSandbox` | Any file | — | O7 | bwrap wewnątrz kontenera bez nowego /proc |
| `sandbox.enableWeakerNetworkIsolation` | Any file | — | O7 | TLS za MITM na macOS |
| `sandbox.allowAppleEvents` | User or managed | — | O7 | Apple Events |
| `sandbox.ripgrep` | User or managed | — | O7 | własny ripgrep |
| `sandbox.bwrapPath` | Managed | — | O7 | ścieżka bwrap |
| `sandbox.socatPath` | Managed | — | O7 | ścieżka socat |
| `sandbox.credentials` | Any file | — | O7 | ochrona sekretów |
| `sandbox.credentials.files` | Any file | 2.1.221 | O7 | deny/mask plików |
| `sandbox.credentials.envVars` | Any file | 2.1.199 | O7 | deny/mask zmiennych |
| `sandbox.credentials.allowPlaintextInject` | User or managed | 2.1.199 | O7 | wstrzyknięcie do HTTP |
| `sandbox.credentials.awsPairs` | User or managed | 2.1.224 | O7 | pary AWS |
| `sandbox.credentials.sigv4` | User or managed | 2.1.224 | O7 | SigV4 |
| `sandbox.network` | Any file | — | O7 | reguły sieci |
| `sandbox.network.allowUnixSockets` | Any file | — | O7 | lista gniazd |
| `sandbox.network.allowAllUnixSockets` | Any file | — | O7 | wszystkie gniazda uniksowe |
| `sandbox.network.allowLocalBinding` | Any file | — | O7 | bind na localhost |
| `sandbox.network.allowMachLookup` | Any file | — | O7 | XPC |
| `sandbox.network.allowedDomains` | Any file | — | O7 | lista domen dla Bash |
| `sandbox.network.deniedDomains` | Any file | — | O7 | zakazane domeny |
| `sandbox.network.strictAllowlist` | User or managed | 2.1.219 | O7 | odmowa zamiast pytania poza listą |
| `sandbox.network.allowManagedDomainsOnly` | Managed | — | O7 | blokada domen do zarządzanych |
| `sandbox.network.httpProxyPort` | Any file | — | O7 | własny proxy HTTP |
| `sandbox.network.socksProxyPort` | Any file | — | O7 | własny SOCKS |
| `sandbox.network.tlsTerminate` | User or managed | — | O7 | proxy kończy TLS (eksperymentalne) |

## Pamięć i kontekst (13)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `autoCompactEnabled` | Any file | — | O13 | włącza autokompakcję |
| `autoCompactWindow` | Any file | — | O13 | próg kompakcji |
| `autoMemoryDirectory` | Any file | — | O2 | katalog pamięci automatycznej |
| `autoMemoryEnabled` | Any file | — | O2 | pamięć automatyczna |
| `bashOutputMaxChars` | Any file | 2.1.261 | O5 | wyjście Bash inline (≥2.1.261) |
| `claudeMd` | Managed | — | O2 | CLAUDE.md organizacji |
| `claudeMdExcludes` | Any file | — | O2 | pomija pliki CLAUDE.md |
| `env` | Any file | — | O14 | zmienne dla sesji i podprocesów |
| `fileCheckpointingEnabled` | Any file | — | O13 | punkty kontrolne plików |
| `plansDirectory` | Any file | — | O13 | katalog planów |
| `skillListingBudgetFraction` | Any file | — | O10 | budżet listy skilli |
| `skillListingMaxDescChars` | Any file | — | O10 | limit opisu skilla |
| `taskOutputMaxChars` | usunięty | — | O13 | usunięte w 2.1.277 |

## Interfejs i terminal (39)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `askUserQuestionTimeout` | User or managed | 2.1.200 | O5 | timeout AskUserQuestion |
| `autoContinueAtUsageLimit` | User or managed | 2.1.234 | P | kontynuacja po odnowieniu limitu w otwartej sesji |
| `autoScrollEnabled` | Any file | — | P | przewijanie w trybie pełnoekranowym |
| `axScreenReader` | Any file | — | P | tryb czytnika ekranu |
| `bashEditDiffEnabled` | User or managed | — | O5 | zapis zmian plików przez Bash |
| `companyAnnouncements` | Any file | — | P | komunikaty organizacji przy starcie |
| `defaultShell` | Any file | — | P | powłoka poleceń `!` |
| `dialogExpiry` | User or managed | 2.1.224 | O6 | czas na odpowiedź hosta SDK na dialog |
| `editorMode` | Any file | — | P | tryb vim w polu wpisywania |
| `emojiCompletionEnabled` | Any file | — | P | podpowiedzi emoji |
| `fileSuggestion` | Any file | — | P | własne podpowiedzi plików `@` |
| `footerLinksRegexes` | User or managed | — | P | linki w stopce |
| `keybindingFlavor` | Any file | — | P | przestarzałe (bez skutku) |
| `maxProseWidth` | Any file | 2.1.282 | P | szerokość tekstu w terminalu |
| `prefersReducedMotion` | Any file | — | P | ograniczenie animacji |
| `promptSuggestionEnabled` | Any file | — | P | podpowiedzi w polu wpisywania |
| `respectGitignore` | Any file | — | P | `@` bez plików z .gitignore |
| `respondToBashCommands` | Any file | — | P | odpowiedź po poleceniu `!` |
| `showClearContextOnPlanAccept` | Any file | — | P | opcja czyszczenia kontekstu po planie |
| `showTurnDuration` | Any file | — | P | czas tury |
| `spellcheck` | User or managed | 2.1.235 | P | sprawdzanie pisowni w polu wpisywania |
| `spinnerTipsEnabled` | Any file | — | P | podpowiedzi w spinnerze |
| `spinnerTipsOverride` | Any file | — | P | własne podpowiedzi spinnera |
| `spinnerVerbs` | Any file | — | P | czasowniki spinnera |
| `statusLine` | Any file | — | P | pasek stanu z polecenia |
| `subagentStatusLine` | Any file | — | P | wiersze podagentów w TUI |
| `syntaxHighlightingDisabled` | Any file | — | P | kolorowanie składni |
| `terminalProgressBarEnabled` | Any file | — | P | pasek postępu terminala |
| `terminalTitleFromRename` | Any file | — | P | tytuł karty terminala |
| `theme` | Any file | — | P | motyw |
| `timeFormat` | Any file | 2.1.257 | P | format czasu w interfejsie |
| `timeZone` | Any file | 2.1.257 | P | strefa czasu w interfejsie |
| `tui` | Any file | — | P | renderer pełnoekranowy/klasyczny |
| `verbose` | Any file | — | P | pełne wyjście narzędzi w TUI |
| `viewMode` | Any file | — | P | widok startowy TUI |
| `vimInsertModeRemaps` | User or managed | 2.1.208 | P | mapowanie klawiszy vim |
| `voice` | Any file | — | P | dyktowanie głosowe |
| `voiceEnabled` | Any file | — | P | dyktowanie (starsza forma) |
| `wheelScrollAccelerationEnabled` | Any file | — | P | przyspieszenie kółka myszy |

## Git i atrybucja (7)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `attribution` | Any file | — | O1 | podpis commitów/PR |
| `includeCoAuthoredBy` | Any file | — | O1 | przestarzałe |
| `includeGitInstructions` | Any file | — | O1 | wbudowane instrukcje git + migawka git status |
| `prUrlTemplate` | Any file | — | O1 | linki PR |
| `attribution.commit` | Any file | — | O1 | podpis commitów |
| `attribution.pr` | Any file | — | O1 | podpis PR |
| `attribution.sessionUrl` | Any file | — | O1 | link sesji w commitach |

## Hooki i automatyzacja (9)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `allowedHttpHookUrls` | Any file | — | O11 | dozwolone adresy hooków http |
| `allowManagedHooksOnly` | Managed | — | O11 | tylko hooki zarządzane |
| `disableAllHooks` | Any file | — | O11 | wyłącza hooki |
| `disableWorkflows` | Any file | — | O9 | wyłącza dynamic workflows |
| `enableWorkflows` | Any file | — | O9 | osobisty przełącznik |
| `hooks` | Any file | — | O11 | hooki |
| `httpHookAllowedEnvVars` | Any file | — | O11 | zmienne w nagłówkach hooków HTTP |
| `workflowKeywordTriggerEnabled` | Any file | — | O9 | słowo `ultracode` uruchamia workflow |
| `workflowSizeGuideline` | Any file | 2.1.219 | O9 | rozmiar workflow |

## Wtyczki i skille (22)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `disableBundledSkills` | Any file | — | O10 | wyłącza skille wbudowane |
| `disableSkillShellExecution` | Any file | — | O10 | zakaz powłoki w skillach |
| `skillOverrides` | Any file | — | O10 | ukrywa/zwija skille |
| `syncClaudeAiSkills` | User, local, managed or --settings | — | O10 | skille z konta claude.ai |
| `syncClaudeAiPlugins` | User, local, managed or --settings | 2.1.273 | O12 | wtyczki z konta claude.ai |
| `allowedChannelPlugins` | Managed | — | O9 | lista kanałów |
| `blockedMarketplaces` | Managed | — | O12 | blokada marketplace |
| `channelsEnabled` | Managed | — | O9 | kanały |
| `disableCommandPluginSources` | Managed | 2.1.229 | O12 | blokada źródeł command |
| `pluginSuggestionMarketplaces` | Managed | — | O12 | sugestie wtyczek |
| `pluginTrustMessage` | Managed | — | O12 | komunikat zaufania |
| `strictKnownMarketplaces` | Managed | — | O12 | lista marketplace |
| `strictPluginOnlyCustomization` | Managed | — | O12 | tylko wtyczki i zarządzane |
| `strictPluginOnlyCustomization.skills` | Managed | — | O12 | j.w. skille |
| `strictPluginOnlyCustomization.agents` | Managed | — | O12 | j.w. agenci |
| `strictPluginOnlyCustomization.hooks` | Managed | — | O12 | j.w. hooki |
| `strictPluginOnlyCustomization.mcp` | Managed | — | O12 | j.w. MCP |
| `enabledPlugins` | Any file | — | O12 | włączone wtyczki |
| `extraKnownMarketplaces` | Any file | — | O12 | marketplace repo |
| `pluginConfigs` | User or managed | — | O12 | odpowiedzi konfiguracji wtyczek |
| `prependPlugins` | User or managed | — | O12 | mody organizacji |
| `appendPlugins` | User or managed | — | O12 | mody organizacji |

## Serwery MCP (10)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `allowAllClaudeAiMcps` | Managed | — | O8 | konektory przy managed-mcp |
| `allowClaudeInChromeWithManagedMcp` | Managed (tylko z urządzenia) | 2.1.282 | O8 | Chrome przy managed-mcp |
| `allowedMcpServers` | Any file | — | O8 | allowlista MCP |
| `allowManagedMcpServersOnly` | Managed | — | O8 | blokada allowlisty MCP |
| `deniedMcpServers` | Any file | — | O8 | blokada serwerów |
| `disableClaudeAiConnectors` | Any file | — | O8 | wyłącza konektory claude.ai |
| `disabledMcpjsonServers` | Any file | — | O8 | .mcp.json projektu |
| `enableAllProjectMcpServers` | Any file | — | O8 | .mcp.json projektu |
| `enabledMcpjsonServers` | Any file | — | O8 | .mcp.json projektu |
| `managedMcpServers` | Managed | 2.1.259 | O8 | serwery zarządzane |

## Agenci, sesje i worktree (11)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `agent` | Any file | — | O9 | sesja jako nazwany agent |
| `crossSessionInbound` | Any file | 2.1.224 | O9 | wiadomości z innych sesji |
| `disableAgentView` | Any file | — | O9 | agent view / sesje w tle |
| `isolatePeerMachines` | Any file | — | O9 | pytanie przed wiadomością do innej maszyny |
| `processWrapper` | User or managed | 2.1.210 | O9 | launcher procesów w tle |
| `teammateMode` | Any file | — | O9 | zespoły agentów |
| `worktree` | Any file | — | O9 | worktree CLI |
| `worktree.baseRef` | Any file | — | O9 | j.w. |
| `worktree.symlinkDirectories` | Any file | — | O9 | j.w. |
| `worktree.sparsePaths` | Any file | — | O9 | j.w. |
| `worktree.bgIsolation` | Any file | — | O9 | j.w. |

## Zdalne, desktop i powiadomienia (13)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `agentPushNotifEnabled` | Any file | — | P | push |
| `awaySummaryEnabled` | Any file | — | P | podsumowanie po powrocie do terminala |
| `disableArtifact` | Any file | — | P | przestarzałe |
| `disableDeepLinkRegistration` | Any file | — | P | rejestracja `claude-cli://` |
| `disableDesktopLocalSessions` | Managed | — | P | wyłącza lokalne sesje desktop |
| `disableRemoteControl` | Any file | — | P | Remote Control |
| `enableArtifact` | Any file | 2.1.196 | P | narzędzie Artifact |
| `inputNeededNotifEnabled` | Any file | — | P | powiadomienie push o czekaniu |
| `preferredNotifChannel` | Any file | — | P | kanał powiadomień terminala |
| `remote.defaultEnvironmentId` | Any file | — | P | domyślne środowisko chmurowe `--cloud` |
| `remoteControlAtStartup` | Any file | — | P | RC przy starcie |
| `sshConfigs` | User or managed | — | P | połączenia SSH w desktop |
| `sshHostAllowlist` | Managed | — | P | dozwolone hosty SSH desktop |

## Uwierzytelnianie i dostawcy (10)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `allowedProviders` | Managed | 2.1.285 | O14 | ogranicza dostawców API na maszynie |
| `apiKeyHelper` | Any file | — | O14 | własne polecenie generujące poświadczenie |
| `awsAuthRefresh` | Any file | — | O14 | odświeżanie poświadczeń Bedrock |
| `awsCredentialExport` | Any file | — | O14 | poświadczenia Bedrock z polecenia |
| `forceLoginMethod` | Any file | — | O14 | wymuszona metoda logowania |
| `forceLoginGatewayUrl` | Managed | — | O14 | adres bramy logowania |
| `forceLoginOrgUUID` | Any file | — | O14 | przypięcie logowania do organizacji |
| `gatewayInternalNetworks` | Managed | 2.1.268 | O14 | sieci wewnętrzne bramy |
| `gcpAuthRefresh` | Any file | — | O14 | odświeżanie poświadczeń Google Cloud |
| `otelHeadersHelper` | Any file | — | O14 | rotujące nagłówki OTel z polecenia |

## Aktualizacje i wersje (4)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `autoUpdatesChannel` | Any file | — | O14 | kanał aktualizacji |
| `minimumVersion` | Any file | — | O14 | dolna granica autoaktualizacji |
| `requiredMaximumVersion` | Managed | 2.1.163 | O14 | górna granica wersji |
| `requiredMinimumVersion` | Managed | 2.1.163 | O14 | dolna granica wersji |

## Narzędzia (3)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `browserExternalPageTools` | Managed | — | P | narzędzia na stronach zewnętrznych w panelu przeglądarki desktop |
| `disableBrowserExternalNavigation` | Managed | — | P | panel przeglądarki desktop tylko localhost |
| `disableMobileSimulatorTools` | Managed | — | P | narzędzia w symulatorze iOS |

## Prywatność i telemetria (5)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `cleanupPeriodDays` | Any file | — | O13 | retencja transkryptów (30 dni) |
| `desktopSessionCleanupPeriodDays` | User or managed | 2.1.248 | P | retencja desktop |
| `feedbackDrafts` | User or managed | — | O15 | szkice opinii do Anthropic |
| `feedbackSurveyRate` | Any file | — | O15 | ankiety |
| `skipWebFetchPreflight` | Any file | — | O5 | pomija sprawdzenie domeny WebFetch |

## Organizacja i ustawienia zarządzane (9)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `disableSideloadFlags` | Managed | 2.1.193 | O14 | odrzuca `--agents`, `--mcp-config`, `--plugin-dir` |
| `forceRemoteSettingsRefresh` | Managed | — | O14 | start dopiero po pobraniu ustawień serwerowych |
| `managedSourcesBehavior` | Managed | 2.1.242 | O14 | składanie źródeł zarządzanych |
| `parentSettingsBehavior` | Managed | — | O14 | polityka hosta SDK |
| `policyHelper` | Managed | — | O14 | program liczący politykę |
| `policyHelper.path` | Managed | — | O14 | j.w. |
| `policyHelper.timeoutMs` | Managed | — | O14 | j.w. |
| `policyHelper.refreshIntervalMs` | Managed | — | O14 | j.w. |
| `wslInheritsWindowsSettings` | Managed | — | O14 | WSL |

## Konfiguracja globalna (~/.claude.json) (12)

| Klucz | Zasięg | Min. wersja | Obszar | Co robi |
|---|---|---|---|---|
| `autoConnectIde` | Global config | — | P | automatyczne łączenie z IDE |
| `autoInstallIdeExtension` | Global config | — | P | automatyczna instalacja rozszerzenia IDE |
| `claudeInChromeDefaultEnabled` | Global config | — | P | Chrome w każdej sesji interaktywnej |
| `copyFullResponse` | Global config | — | P | `/copy` całej odpowiedzi |
| `copyOnSelect` | Global config | — | P | kopiowanie zaznaczenia |
| `defaultToAgentsView` | Global config | — | P | start w widoku agentów |
| `diffTool` | Global config | — | P | przeglądarka różnic |
| `externalEditorContext` | Global config | — | P | kontekst w edytorze zewnętrznym (Ctrl+G) |
| `leftArrowOpensAgents` | Global config | — | P | skrót ← do widoku agentów |
| `permissionExplainerEnabled` | Global config | — | P | usunięte w 2.1.257 |
| `prStatusFooterEnabled` | Global config | — | P | status PR w stopce |
| `teammateDefaultModel` | Global config | — | P | usunięte w 2.1.234 |
