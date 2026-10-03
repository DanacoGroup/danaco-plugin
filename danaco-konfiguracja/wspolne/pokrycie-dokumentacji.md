# Pokrycie dokumentacji — która strona, który skill

Stan: dokumentacja z 01–02.10.2026 (281 stron z listy macierzy pełnej CLI: 230 `code.claude.com`, 51 `platform.claude.com`).
Kolumna „Obszar” — oznaczenie z macierzy (O1–O15, P — platformy, SDK, OŚ — oś pojęć, — — strona ogólna).
„cytowana” — strona jest źródłem w SKILL.md, referencji lub skrypcie wskazanego skilla; „tematycznie” —
temat strony należy do skilla, ale treść nie jest cytowana wprost; „poza zakresem” — powierzchnie inne niż
CLI/SDK lub strony wprowadzające.

| Strona | Obszar | Skill | Rodzaj |
|---|---|---|---|
| `cc:overview` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:quickstart` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:changelog` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:how-claude-code-works` | O13 | ustawienia-i-hierarchia | tematycznie — kontekst ogólny |
| `cc:features-overview` | OŚ | ustawienia-i-hierarchia | tematycznie — kontekst ogólny |
| `cc:claude-directory` | O14 | headless-i-osadzanie | cytowana |
| `cc:context-window` | O13 | instrukcja-systemowa-i-pamiec | cytowana |
| `cc:prompt-caching` | O4 | instrukcja-systemowa-i-pamiec, model-cache-i-koszty | cytowana |
| `cc:memory` | O2 | bezpieczenstwo-wdrozenia, instrukcja-systemowa-i-pamiec | cytowana |
| `cc:sessions` | O13 | bezpieczenstwo-wdrozenia, headless-i-osadzanie | cytowana |
| `cc:common-workflows` | — | scripts | cytowana |
| `cc:prompt-library` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:best-practices` | O11 | ustawienia-i-hierarchia | tematycznie — kontekst ogólny |
| `cc:platforms` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:remote-control` | P | scripts | cytowana |
| `cc:claude-projects` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:mobile` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:chrome` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:computer-use` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:vs-code` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:jetbrains` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:slack` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:claude-tag` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:web-quickstart` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:claude-code-on-the-web` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:routines` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:ultrareview` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:desktop-quickstart` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:desktop` | P | scripts | cytowana |
| `cc:desktop-linux` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:desktop-wsl` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:desktop-scheduled-tasks` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:desktop-ios-simulator` | P | scripts | cytowana |
| `cc:security-guidance` | O12 | bezpieczenstwo-wdrozenia | tematycznie |
| `cc:claude-security` | O12 | bezpieczenstwo-wdrozenia | tematycznie |
| `cc:code-review` | P | bezpieczenstwo-wdrozenia | tematycznie — profil ci (tylko zasady; integracje CI poza zakresem) |
| `cc:github-actions` | P | bezpieczenstwo-wdrozenia | tematycznie — profil ci (tylko zasady; integracje CI poza zakresem) |
| `cc:github-actions-cloud-providers` | P | bezpieczenstwo-wdrozenia | tematycznie — profil ci (tylko zasady; integracje CI poza zakresem) |
| `cc:github-enterprise-server` | P | bezpieczenstwo-wdrozenia | tematycznie — profil ci (tylko zasady; integracje CI poza zakresem) |
| `cc:gitlab-ci-cd` | P | bezpieczenstwo-wdrozenia | tematycznie — profil ci (tylko zasady; integracje CI poza zakresem) |
| `cc:agents` | O9 | podagenci-i-zespoly | tematycznie |
| `cc:sub-agents` | O9 | podagenci-i-zespoly | cytowana |
| `cc:agent-view` | O9 | podagenci-i-zespoly | cytowana |
| `cc:agent-teams` | O9 | model-cache-i-koszty, podagenci-i-zespoly | cytowana |
| `cc:cross-session-messaging` | O9 | podagenci-i-zespoly | cytowana |
| `cc:workflows` | O9 | podagenci-i-zespoly | cytowana |
| `cc:worktrees` | O9 | podagenci-i-zespoly | tematycznie |
| `cc:mcp-quickstart` | O8 | serwery-mcp | cytowana |
| `cc:mcp` | O8 | bezpieczenstwo-wdrozenia, serwery-mcp, uprawnienia-i-tryby | cytowana |
| `cc:skills` | O10 | budowa-skilli | cytowana |
| `cc:artifacts` | P | scripts | cytowana |
| `cc:hooks-guide` | O11 | hooki | cytowana |
| `cc:channels` | O9 | scripts | cytowana |
| `cc:scheduled-tasks` | O9 | podagenci-i-zespoly | tematycznie |
| `cc:goal` | O13 | headless-i-osadzanie | tematycznie |
| `cc:headless` | O13 | bezpieczenstwo-wdrozenia, headless-i-osadzanie, uprawnienia-i-tryby | cytowana |
| `cc:deep-links` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:large-codebases` | O2 | instrukcja-systemowa-i-pamiec | cytowana |
| `cc:troubleshoot-install` | O14 | diagnostyka | cytowana |
| `cc:troubleshooting` | O14 | diagnostyka | cytowana |
| `cc:debug-your-config` | O14 | diagnostyka | cytowana |
| `cc:errors` | O14 | diagnostyka, uprawnienia-i-tryby | cytowana |
| `cc:plugins/overview` | O12 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/install` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/anthropic-marketplaces` | O12 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/code-intelligence` | O5 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/security` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/create` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/components` | O12 | hooki, wtyczki-i-marketplace | cytowana |
| `cc:plugins/dependencies` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugin-evals` | O12 | budowa-skilli | cytowana |
| `cc:plugins/publish` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/measure` | O15 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/cli-hints` | O12 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/mods/overview` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/create` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/reference` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/interface` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/events` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/api` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/test` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/mods/troubleshoot` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/create-marketplace` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/host-marketplace` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/relevance` | O12 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/org` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/mods/admin` | P | — | poza zakresem: modyfikacje interfejsu (mods) |
| `cc:plugins/troubleshooting` | O12 | wtyczki-i-marketplace | tematycznie |
| `cc:plugins/loading` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/manifest-reference` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/marketplace-reference` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:plugins/cli-reference` | O12 | wtyczki-i-marketplace | cytowana |
| `cc:admin-setup` | O14 | zarzadzanie-flota | cytowana |
| `cc:setup` | O14 | bezpieczenstwo-wdrozenia, zarzadzanie-flota | cytowana |
| `cc:authentication` | O14 | zarzadzanie-flota, zmienne-srodowiskowe | cytowana |
| `cc:managed-settings` | O14 | bezpieczenstwo-wdrozenia, ustawienia-i-hierarchia, zarzadzanie-flota | cytowana |
| `cc:server-managed-settings` | O14 | zarzadzanie-flota | cytowana |
| `cc:managed-mcp` | O8 | serwery-mcp, zarzadzanie-flota | cytowana |
| `cc:auto-mode-config` | O6 | bezpieczenstwo-wdrozenia, uprawnienia-i-tryby | cytowana |
| `cc:third-party-integrations` | O14 | zarzadzanie-flota | tematycznie |
| `cc:feature-availability` | O14 | zarzadzanie-flota | tematycznie |
| `cc:amazon-bedrock` | O14 | scripts | cytowana |
| `cc:claude-platform-on-aws` | O14 | scripts | cytowana |
| `cc:google-vertex-ai` | O14 | scripts | cytowana |
| `cc:microsoft-foundry` | O14 | scripts | cytowana |
| `cc:network-config` | O14 | diagnostyka | cytowana |
| `cc:corporate-launcher` | O14 | zarzadzanie-flota | cytowana |
| `cc:devcontainer` | O7 | piaskownica-i-izolacja | cytowana |
| `cc:gateways` | O14 | zarzadzanie-flota | tematycznie |
| `cc:claude-apps-gateway` | O14 | scripts | cytowana |
| `cc:claude-apps-gateway-config` | O14 | zarzadzanie-flota | tematycznie |
| `cc:claude-apps-gateway-spend-limits` | O14 | zarzadzanie-flota | tematycznie |
| `cc:claude-apps-gateway-deploy` | O14 | zarzadzanie-flota | tematycznie |
| `cc:claude-apps-gateway-on-aws` | O14 | zarzadzanie-flota | tematycznie |
| `cc:claude-apps-gateway-on-gcp` | O14 | zarzadzanie-flota | tematycznie |
| `cc:llm-gateway` | O14 | zarzadzanie-flota | tematycznie |
| `cc:llm-gateway-connect` | O14 | zarzadzanie-flota | tematycznie |
| `cc:llm-gateway-rollout` | O14 | zarzadzanie-flota | tematycznie |
| `cc:llm-gateway-protocol` | O14 | model-cache-i-koszty | cytowana |
| `cc:monitoring-usage` | O15 | bezpieczenstwo-wdrozenia, diagnostyka, model-cache-i-koszty, zmienne-srodowiskowe | cytowana |
| `cc:costs` | O15 | model-cache-i-koszty | cytowana |
| `cc:analytics` | O15 | model-cache-i-koszty | tematycznie |
| `cc:security` | O7 | bezpieczenstwo-wdrozenia | cytowana |
| `cc:data-usage` | O15 | bezpieczenstwo-wdrozenia, zarzadzanie-flota | cytowana |
| `cc:zero-data-retention` | O15 | bezpieczenstwo-wdrozenia | cytowana |
| `cc:communications-kit` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:champion-kit` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:settings` | O14 | ustawienia-i-hierarchia, zarzadzanie-flota | cytowana |
| `cc:settings-reference` | OŚ | bezpieczenstwo-wdrozenia, budowa-skilli, hooki, instrukcja-systemowa-i-pamiec, model-cache-i-koszty, piaskownica-i-izolacja, serwery-mcp, uprawnienia-i-tryby, ustawienia-i-hierarchia, zarzadzanie-flota | cytowana |
| `cc:settings-example` | O14 | zarzadzanie-flota | tematycznie |
| `cc:permissions` | O6 | bezpieczenstwo-wdrozenia, serwery-mcp, uprawnienia-i-tryby, ustawienia-i-hierarchia | cytowana |
| `cc:permission-modes` | O6 | bezpieczenstwo-wdrozenia, uprawnienia-i-tryby | cytowana |
| `cc:sandboxing` | O7 | bezpieczenstwo-wdrozenia, piaskownica-i-izolacja | cytowana |
| `cc:sandbox-environments` | O7 | piaskownica-i-izolacja | cytowana |
| `cc:cloud-environments` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-quickstart` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-deploy` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-configuration` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-testing` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-reference` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:self-hosted-environments-identity` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:model-config` | O4 | bezpieczenstwo-wdrozenia, model-cache-i-koszty | cytowana |
| `cc:fast-mode` | O4 | model-cache-i-koszty | cytowana |
| `cc:advisor` | O4 | model-cache-i-koszty | cytowana |
| `cc:output-styles` | O3 | instrukcja-systemowa-i-pamiec | cytowana |
| `cc:terminal-config` | P | scripts | cytowana |
| `cc:fullscreen` | P | scripts | cytowana |
| `cc:accessibility` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:voice-dictation` | P | scripts | cytowana |
| `cc:statusline` | P | model-cache-i-koszty | cytowana |
| `cc:keybindings` | P | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:cli-reference` | OŚ | diagnostyka, headless-i-osadzanie, instrukcja-systemowa-i-pamiec, podagenci-i-zespoly, uprawnienia-i-tryby | cytowana |
| `cc:commands` | O10 | budowa-skilli | cytowana |
| `cc:env-vars` | O14 | bezpieczenstwo-wdrozenia, diagnostyka, headless-i-osadzanie, instrukcja-systemowa-i-pamiec, model-cache-i-koszty, piaskownica-i-izolacja, podagenci-i-zespoly, serwery-mcp, ustawienia-i-hierarchia, zmienne-srodowiskowe | cytowana |
| `cc:tools-reference` | O5 | scripts | cytowana |
| `cc:interactive-mode` | P | scripts | cytowana |
| `cc:checkpointing` | O13 | scripts | cytowana |
| `cc:hooks` | O11 | bezpieczenstwo-wdrozenia, diagnostyka, hooki, uprawnienia-i-tryby | cytowana |
| `cc:channels-reference` | O9 | podagenci-i-zespoly | tematycznie |
| `cc:glossary` | — | — | poza zakresem: powierzchnia inna niż CLI/SDK (IDE, desktop, web, mobile, Slack, środowiska chmurowe) lub strona wprowadzająca |
| `cc:agent-sdk/overview` | SDK | headless-i-osadzanie | cytowana |
| `cc:agent-sdk/quickstart` | SDK | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/migration-guide` | SDK | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/troubleshooting` | SDK | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/configuration` | OŚ | headless-i-osadzanie | cytowana |
| `cc:agent-sdk/examples` | SDK | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/agent-loop` | O13 | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/claude-code-features` | O14 | headless-i-osadzanie, ustawienia-i-hierarchia | cytowana |
| `cc:agent-sdk/sessions` | O13 | headless-i-osadzanie | cytowana |
| `cc:agent-sdk/session-storage` | O13 | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/streaming-vs-single-mode` | O13 | headless-i-osadzanie | cytowana |
| `cc:agent-sdk/user-input` | O6 | uprawnienia-i-tryby | tematycznie |
| `cc:agent-sdk/streaming-output` | O13 | headless-i-osadzanie | cytowana |
| `cc:agent-sdk/structured-outputs` | O13 | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/custom-tools` | O8 | serwery-mcp | tematycznie |
| `cc:agent-sdk/mcp` | O8 | serwery-mcp | cytowana |
| `cc:agent-sdk/tool-search` | O8 | serwery-mcp | tematycznie |
| `cc:agent-sdk/subagents` | O9 | podagenci-i-zespoly | cytowana |
| `cc:agent-sdk/modifying-system-prompts` | O1 | instrukcja-systemowa-i-pamiec, model-cache-i-koszty | cytowana |
| `cc:agent-sdk/skills` | O10 | budowa-skilli | tematycznie |
| `cc:agent-sdk/plugins` | O12 | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/permissions` | O6 | uprawnienia-i-tryby | tematycznie |
| `cc:agent-sdk/hooks` | O11 | hooki | tematycznie |
| `cc:agent-sdk/file-checkpointing` | O13 | scripts | cytowana |
| `cc:agent-sdk/cost-tracking` | O15 | model-cache-i-koszty | tematycznie |
| `cc:agent-sdk/observability` | O15 | model-cache-i-koszty | tematycznie |
| `cc:agent-sdk/todo-tracking` | O5 | podagenci-i-zespoly | tematycznie |
| `cc:agent-sdk/hosting` | O14 | bezpieczenstwo-wdrozenia, headless-i-osadzanie, piaskownica-i-izolacja | cytowana |
| `cc:agent-sdk/secure-deployment` | O7 | bezpieczenstwo-wdrozenia, headless-i-osadzanie, piaskownica-i-izolacja | cytowana |
| `cc:agent-sdk/typescript` | SDK | headless-i-osadzanie, uprawnienia-i-tryby | cytowana |
| `cc:agent-sdk/typescript-v2-preview` | SDK | headless-i-osadzanie | tematycznie — odpowiedniki SDK ↔ CLI |
| `cc:agent-sdk/python` | SDK | headless-i-osadzanie | cytowana |
| `cc:whats-new/index` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w37` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w36` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w35` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w34` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w33` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w32` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w30` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w29` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w28` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w27` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w26` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w25` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w24` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w23` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w22` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w21` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w20` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w19` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w18` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w17` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w16` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w15` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w14` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:whats-new/2026-w13` | O14 | zarzadzanie-flota | tematycznie — wersje — źródło minimalnych wersji w indeksach |
| `cc:legal-and-compliance` | — | bezpieczenstwo-wdrozenia | cytowana |
| `https://code.claude.com/docs/_llms/fr` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/de` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/it` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/jp` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/es` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/ko` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/zh-cn` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/zh-tw` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/ru` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/id` | — | — | indeks tłumaczeń (nie dotyczy) |
| `https://code.claude.com/docs/_llms/pt-br` | — | — | indeks tłumaczeń (nie dotyczy) |
| `pl:agents-and-tools/agent-skills/best-practices` | przeczytana; kontekst mapy pojęć i zaleceń | budowa-skilli | cytowana |
| `pl:agents-and-tools/agent-skills/overview` | przeczytana; kontekst mapy pojęć i zaleceń | budowa-skilli | cytowana |
| `pl:agents-and-tools/mcp-connector` | przeczytana; kontekst mapy pojęć i zaleceń | serwery-mcp | tematycznie |
| `pl:agents-and-tools/remote-mcp-servers` | przeczytana; kontekst mapy pojęć i zaleceń | serwery-mcp | tematycznie |
| `pl:agents-and-tools/tool-use/overview` | przeczytana; kontekst mapy pojęć i zaleceń | serwery-mcp | tematycznie |
| `pl:agents-and-tools/tool-use/tool-search-tool` | tool search (O8) | serwery-mcp | cytowana |
| `pl:build-with-claude/compaction` | przeczytana; kontekst mapy pojęć i zaleceń | model-cache-i-koszty | tematycznie |
| `pl:build-with-claude/context-editing` | przeczytana; kontekst mapy pojęć i zaleceń | model-cache-i-koszty | tematycznie |
| `pl:build-with-claude/effort` | przeczytana; kontekst mapy pojęć i zaleceń | model-cache-i-koszty | tematycznie |
| `pl:build-with-claude/overview` | przeczytana; kontekst mapy pojęć i zaleceń | — | poza zakresem: platforma API (kontekst) |
| `pl:build-with-claude/prompt-caching` | izolacja cache organizacji/workspace (rozdz. 3A) | model-cache-i-koszty | tematycznie |
| `pl:build-with-claude/prompt-engineering/claude-prompting-best-practices` | przeczytana; kontekst mapy pojęć i zaleceń | instrukcja-systemowa-i-pamiec | tematycznie |
| `pl:build-with-claude/prompt-engineering/prompting-claude-opus-5-5` | przeczytana; kontekst mapy pojęć i zaleceń | instrukcja-systemowa-i-pamiec | tematycznie |
| `pl:cli-sdks-libraries/cli/apply` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/cli/authentication` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/cli/quickstart` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/cli/scripting` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/cli/sessions-connect` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/cli/using` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:cli-sdks-libraries/overview` | strona zbiorcza SDK/CLI (rozdz. 0) | zarzadzanie-flota | tematycznie — CLI `ant` (profile, uwierzytelnienie) |
| `pl:home` | przeczytana; kontekst mapy pojęć i zaleceń | — | poza zakresem: platforma API (kontekst) |
| `pl:manage-claude/claude-code-analytics-api` | przeczytana; kontekst mapy pojęć i zaleceń | zarzadzanie-flota | tematycznie |
| `pl:managed-agents/agent-setup` | pola agenta — oś obszarów (rozdz. 0) | headless-i-osadzanie | cytowana |
| `pl:managed-agents/budgets` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/cloud-sandboxes-reference` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/define-outcomes` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/dreams` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/environments` | mapa pojęć (networking) | headless-i-osadzanie | cytowana |
| `pl:managed-agents/events-and-streaming` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/files` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/github` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/mcp-connector` | mapa pojęć (MCP, limit 100 000 znaków) | headless-i-osadzanie | cytowana |
| `pl:managed-agents/memory` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/migration` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/multiagent-orchestration` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie, podagenci-i-zespoly | cytowana |
| `pl:managed-agents/onboarding` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/overview` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/permission-policies` | mapa pojęć (permission_policy) | headless-i-osadzanie | cytowana |
| `pl:managed-agents/quickstart` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/reference` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/scheduled-deployments` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/self-hosted-sandboxes-security` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/self-hosted-sandboxes` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie, piaskownica-i-izolacja | cytowana |
| `pl:managed-agents/session-operations` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/sessions` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/skills` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/tools` | mapa pojęć + praktyki narzędzi (rozdz. 2) | headless-i-osadzanie, serwery-mcp | cytowana |
| `pl:managed-agents/vaults` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:managed-agents/webhooks` | przeczytana; kontekst mapy pojęć i zaleceń | headless-i-osadzanie | cytowana |
| `pl:test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks` | przeczytana; kontekst mapy pojęć i zaleceń | — | poza zakresem: platforma API (kontekst) |
| `pl:test-and-evaluate/strengthen-guardrails/reduce-prompt-leak` | przeczytana; kontekst mapy pojęć i zaleceń | — | poza zakresem: platforma API (kontekst) |
