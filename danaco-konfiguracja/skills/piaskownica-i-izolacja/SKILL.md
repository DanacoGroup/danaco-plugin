---
name: piaskownica-i-izolacja
description: >
  Piaskownica Claude Code i izolacja środowiska: piaskownica Bash (bubblewrap/Seatbelt +
  proxy), sandbox.filesystem (allowWrite, denyRead, allowRead, disabled), sandbox.network
  (allowedDomains, deniedDomains, strictAllowlist, proxy), sandbox.credentials (deny i mask
  zmiennych i plików, tlsTerminate), tryb ścisły (allowUnsandboxedCommands, failIfUnavailable),
  zagnieżdżanie w kontenerze, CLAUDE_CODE_SUBPROCESS_ENV_SCRUB, sandbox runtime, dev
  container, VM, chmura. Stosuj, gdy pada „piaskownica”, „sandbox”, „odetnij sieć”, „lista
  domen”, „chroń sekrety”, „uruchom bez pytań bezpiecznie”, „bwrap nie działa”, „izolacja
  usługi”. Reguły uprawnień prowadzi `uprawnienia-i-tryby`.
---

# Piaskownica i środowiska izolowane

## Kiedy stosować

Gdy trzeba **twardej granicy** dla poleceń agenta: reguły uprawnień dopasowują tekst
polecenia, a piaskownica egzekwuje dostęp do plików i sieci w jądrze systemu, niezależnie
od tego, co model uruchomi. Także gdy agent ma pracować bez pytań (`dontAsk`, `auto`,
`bypassPermissions`) — wtedy granica izolacji jest jedyną ochroną.

## Wybór podejścia

| Cel | Podejście | Co izoluje |
|---|---|---|
| mniej pytań przy codziennej pracy | piaskownica Bash (`/sandbox`, `sandbox.enabled`) | tylko Bash, PowerShell, Monitor i ich procesy potomne |
| izolacja także narzędzi plikowych, MCP i hooków bez Dockera | sandbox runtime (`@anthropic-ai/sandbox-runtime`, beta) albo własny `bwrap` całego procesu | cały proces Claude Code |
| praca bez nadzoru (`--dangerously-skip-permissions`, `auto`) | dev container z zaporą, kontener, VM, sandbox runtime | całe środowisko |
| cudze, niezaufane repozytorium | osobna VM albo sesja w chmurze | system |
| usługa wielodzierżawna (produkt osadzający CLI) | osobny proces w izolacji systemowej na dzierżawcę + piaskownica Bash jako druga warstwa | warstwowo |

Piaskownica Bash **nie obejmuje** Read/Edit/WebFetch (te pilnują reguły uprawnień), serwerów
MCP ani hooków `command` (działają na hoście bez ograniczeń). Warstwy wolno łączyć:
piaskownica Bash wewnątrz kontenera lub `bwrap` produktu daje ograniczenia per polecenie
ponad zewnętrzną granicą.

## Model działania piaskownicy Bash

- **Pliki**: zapis domyślnie tylko w katalogu roboczym, katalogach dodatkowych i
  osobnym `$TMPDIR` piaskownicy; **odczyt domyślnie całego komputera** (także `~/.ssh`,
  `~/.aws`) — zawężaj `denyRead`, `sandbox.credentials` albo
  `permissions.blockReadsOutsideWorkingDirectories`.
- **Ścieżki chronione piaskownicy** (bez wyjątków przez `allowWrite`): pliki ustawień
  i katalogi `.claude/skills|agents|commands|hooks`, `.mcp.json`, pliki startowe powłoki,
  `.gitconfig`, `.git/hooks`, `.git/config`, zawartość `~/.claude` i `~/.claude.json`.
- **Sieć**: proxy poza piaskownicą; domyślnie **żadna domena nie jest dozwolona**; nowa
  domena → pytanie (w `-p` bez hosta → odmowa); `strictAllowlist: true` → odmowa zamiast
  pytania. Proxy decyduje po nazwie hosta bez inspekcji TLS (ryzyko domain fronting przy
  szerokich domenach typu `github.com`).
- **Tryby**: auto-allow (`autoAllowBashIfSandboxed: true`, domyślne) — polecenie w
  piaskownicy wykonuje się bez pytania; deny, ask z treścią polecenia i ścieżki krytyczne
  nadal działają. Regular — piaskownica plus zwykłe pytania.
- **Furtka**: polecenie, które nie działa w piaskownicy, model może ponowić z
  `dangerouslyDisableSandbox` — wtedy idzie zwykłą ścieżką uprawnień. `allowUnsandboxedCommands: false`
  zamyka furtkę (tryb ścisły).

## Konfiguracja produkcyjna — kolejność kroków

1. **Zależności** (Linux/WSL2): `bwrap`, `socat`; Ubuntu ≥24.04 —
   `sysctl kernel.apparmor_restrict_unprivileged_userns` musi dawać `0` albo profil AppArmor
   dla `bwrap`. Sprawdź: `bash "${CLAUDE_PLUGIN_ROOT}/skills/piaskownica-i-izolacja/scripts/sprawdz_srodowisko.sh"`.
2. **Tryb ścisły**: `enabled: true`, `failIfUnavailable: true` (brak piaskownicy = błąd,
   nie cichy brak izolacji), `allowUnsandboxedCommands: false`, `excludedCommands: []`.
3. **Sieć**: `strictAllowlist: true` (zasięg User or managed — działa z `--settings`),
   `allowedDomains` tylko potrzebne rejestry i hosty, `deniedDomains` na wyjątki od
   szerokich wzorców, `allowAllUnixSockets: false`.
4. **Pliki**: `denyRead` dla katalogów z sekretami, `allowWrite` tylko dla konkretnych
   katalogów narzędzi (np. `~/.kube`), zamiast `excludedCommands`.
5. **Sekrety**: `credentials.envVars`/`files` z `deny`; gdy narzędzie musi się
   uwierzytelnić — `mask` z `injectHosts` i `network.tlsTerminate` (tylko user, managed,
   `--settings`; z plików projektu ignorowane). Dodatkowo `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`
   w środowisku procesu (czyści poświadczenia ze wszystkich podprocesów, na Linuksie Bash
   w osobnej przestrzeni PID, wymusza izolację plików).
6. **W organizacji**: te klucze w managed + `allowManagedDomainsOnly`,
   `allowManagedReadPathsOnly`; `excludedCommands` nie ma blokady zarządzanej — trzymaj
   listę krótką.
7. **Sprawdź próbą**: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/piaskownica-i-izolacja/scripts/proba_piaskownicy.py" --settings <plik>`
   — zestaw poleceń (zapis w/poza katalogiem, domena dozwolona/niedozwolona, odczyt
   sekretu, zmienna z poświadczeniem) uruchomiony przez CLI na atrapie API.

## Zagnieżdżanie (piaskownica w kontenerze lub w `bwrap` produktu)

- Kontener nieuprzywilejowany: `bwrap` nie zamontuje nowego `/proc` („Can't mount proc on
  /newroot/proc”) → `enableWeakerNestedSandbox: true` — **tylko** gdy zewnętrzna warstwa
  izoluje proces.
- **Znany problem tego serwera** (danaco-nexus, jądro 7.0.0, Ubuntu 26.04, CLI 2.1.286,
  próba 02.10.2026): każde polecenie w piaskownicy kończy się błędem
  `apply-seccomp: write /proc/self/setgroups (nested userns is capability-restricted…)`;
  `enableWeakerNestedSandbox` nie pomaga. Piaskownica działa po
  `network.allowAllUnixSockets: true` (CLI pomija wtedy filtr seccomp gniazd uniksowych) —
  koszt: brak blokady gniazd uniksowych w piaskownicy. Przy tej obejściu nie montuj
  w zasięgu piaskownicy gniazd usług (`docker.sock` itp.).

## Pułapki

- **Długi `$TMPDIR` psuje piaskownicę**: gniazda mostu sieciowego powstają w `$TMPDIR`,
  a ścieżka gniazda uniksowego ma limit ok. 107 znaków — przy głęboko zagnieżdżonym
  katalogu tymczasowym każde polecenie kończy się „Sandbox is required but failed to
  initialize: Failed to create bridge sockets after 5 attempts” (próba 2.1.286). Usługi:
  krótki `TMPDIR` na przebieg (do ok. 60 znaków).
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` (próba 2.1.286): wymusza tryb `default` i tworzy w katalogu
  roboczym puste zaślepki (`.env*`, `.npmrc`, `package.json`, `*lock*`, `node_modules/.bin`,
  `.claude/commands|agents`…), które zostają po sesji — w czystym katalogu dzierżawcy sprzątaj je.
- `failIfUnavailable` domyślnie `false`: brak `bwrap` = cicha praca **bez** piaskownicy.
- `allowWrite` do katalogu z plikami wykonywalnymi w `$PATH` lub plików startowych powłoki
  = eskalacja przy następnym uruchomieniu.
- `filesystem.disabled: true` wyłącza też `denyRead` i `credentials.files` `deny`; działa
  tylko z user/managed/`--settings`; ignorowane przy `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`.
- Ścieżki w `sandbox.filesystem`: `/` = korzeń (inaczej niż w regułach `Read`/`Edit`!),
  `~/` = dom, `./` lub brak = korzeń projektu (w pliku projektu) albo `~/.claude`
  (w pliku użytkownika).
- `--setting-sources` bez projektu/local pomija ich `sandbox.filesystem`, reguły `Edit`
  i `Read` deny przy budowie piaskownicy (≥2.1.246), ale `deny` z `credentials`
  w `~/.claude/settings.json` działa nawet przy wykluczonym źródle użytkownika.
- `WebFetch(domain:*)` w allow otwiera piaskownicę na każdy host; goły `WebFetch` — nie.
- `mask` bez `tlsTerminate`: sentinel trafia do serwera, uwierzytelnienie zawodzi (CLI
  ostrzega przy starcie). `mask` katalogu, globu, pliku >8 MiB lub nie-UTF-8 → `deny`.
- `allowWrite`/`denyWrite` z `*`, `?`, `[` na Linuksie są **pomijane** (montowane są
  konkretne ścieżki); dotyczy też reguł `Edit` z globem. Listy odczytu globy rozwijają.
- `excludedCommands` wyjmuje wywołanie tylko, gdy pokrywa każde polecenie; `cd … &&`,
  przekierowanie, podpowłoka, `sudo`/`eval`/`xargs` zostawiają je w piaskownicy.
- `docker`, `watchman` (`jest --no-watchman`) nie działają w piaskownicy;
  `docker *` w `excludedCommands` to świadome wyjście poza granicę.
- Polecenia wpisane przez człowieka po `!` idą poza piaskownicą (poza sesjami w tle
  i Linuksem z `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`).
- Piaskownica nie zmienia tego, co trafia do modelu — pliki czytane przez agenta i tak
  wychodzą do API.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `credentials.envVars`, `mask` zmiennych, `tlsTerminate` | 2.1.199 |
| `filesystem.disabled` | 2.1.216 |
| `strictAllowlist` | 2.1.219 |
| `credentials.files` `mask` | 2.1.221 |
| `extract`, `decode: "jwt"`, `awsPairs`, `sigv4` | 2.1.224 |
| adresy IPv6 w nawiasach w listach domen, ostrzeżenie `injectHosts` w doctor | 2.1.229 |
| ukośnik końcowy w `denyRead`/`denyWrite` zdejmowany (wcześniej omijał blokadę) | 2.1.224 |
| wykluczone źródła ignorowane przy budowie piaskownicy | 2.1.246 |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` usuwa `CLAUDE_CONFIG_DIR` | 2.1.251 |

## Szablony (walidator + `claude doctor`; ścisły — także próba)

- `examples/scisla-linux.flaga.settings.json` — tryb ścisły, lista domen, deny sekretów.
- `examples/maskowanie-tokenow.user.settings.json` — `mask` z `injectHosts` i `tlsTerminate`.
- `examples/wymuszenie-organizacji.managed.settings.json` — polityka zarządzana z blokadami poszerzania.
- `examples/tylko-siec.user.settings.json` — sama izolacja sieci (`filesystem.disabled`).
- `examples/obejscie-seccomp-nexus.flaga.settings.json` — wariant dla jądra bez zagnieżdżonych przestrzeni użytkownika.

## Referencje

- `references/piaskownica-bash.md` — wszystkie klucze `sandbox.*`, prefiksy ścieżek, sieć, maskowanie, organizacja, rozwiązywanie problemów.
- `references/srodowiska-izolowane.md` — sandbox runtime, dev container, kontener, VM, chmura, wzorzec usługi wielodzierżawnej.
