# Piaskownica Bash — klucze, zachowanie, organizacja, problemy

Źródła: `cc:sandboxing`, `cc:settings-reference` („Sandbox settings”), `cc:env-vars`,
`anthropic.com/engineering/claude-code-sandboxing`. Próby: CLI 2.1.286 na danaco-nexus,
02.10.2026 (atrapa API, `proba_piaskownicy.py`).

## 1. Klucze `sandbox.*` (38) — co ustawiać

| Klucz | Zasięg | Zalecenie produkcyjne |
|---|---|---|
| `enabled` | Any file | `true` |
| `failIfUnavailable` | Any file | `true` — brak zależności blokuje start zamiast cichej pracy bez izolacji |
| `allowUnsandboxedCommands` | Any file | `false` — model nie ponowi poza piaskownicą (`dangerouslyDisableSandbox` ignorowany) |
| `autoAllowBashIfSandboxed` | Any file | `true` (domyślne) przy ścisłym trybie; `false`, gdy każde polecenie ma przejść przez reguły |
| `excludedCommands` | Any file | `[]`; wyjątki tylko świadome (`docker *`), brak blokady managed |
| `ignoreViolations` | Any file | nie ustawiać (wycisza raporty naruszeń) |
| `enableWeakerNestedSandbox` | Any file | tylko w kontenerze bez uprawnień, gdy zewnętrzna warstwa izoluje |
| `enableWeakerNetworkIsolation` | Any file | macOS + proxy MITM z własnym CA |
| `allowAppleEvents` | User or managed | macOS; zdejmuje izolację wykonania kodu |
| `bwrapPath`, `socatPath` | Managed | ścieżki binarek |
| `ripgrep` | User or managed | własny `rg` |
| `filesystem.allowWrite` | Any file | konkretne katalogi narzędzi (`~/.kube`, `/tmp/build`) |
| `filesystem.denyWrite` | Any file | dodatkowe blokady zapisu |
| `filesystem.denyRead` | Any file | `~/.ssh`, `~/.aws`, `~/.config/gcloud`, katalogi z danymi |
| `filesystem.allowRead` | Any file | ponowne otwarcie fragmentu `denyRead` (węższa reguła wygrywa) |
| `filesystem.allowManagedReadPathsOnly` | Managed | `true` w organizacji |
| `filesystem.disabled` | User or managed (+ `--settings`) | tylko dla zaufanych obciążeń; ≥2.1.216 |
| `network.allowedDomains` | Any file | lista minimalna; `*.domena`, `:port`, IPv6 w nawiasach (≥2.1.229) |
| `network.deniedDomains` | Any file | wyjątki od szerokich wzorców, serwisy wklejek |
| `network.strictAllowlist` | User or managed | `true` — odmowa zamiast pytania (≥2.1.219) |
| `network.allowManagedDomainsOnly` | Managed | `true` w organizacji |
| `network.allowAllUnixSockets` | Any file | `false` (patrz znany problem w SKILL.md) |
| `network.allowUnixSockets` | Any file | macOS: lista gniazd |
| `network.allowLocalBinding`, `allowMachLookup` | Any file | macOS |
| `network.httpProxyPort`, `socksProxyPort` | Any file | własne proxy (inspekcja TLS, dzienniki) |
| `network.tlsTerminate` | User or managed | `{}` albo `caCertPath`/`caKeyPath`; wymagane przez `mask` (≥2.1.199, eksperymentalne) |
| `credentials.envVars[]` | Any file (`mask` tylko user/managed/`--settings`) | `{"name","mode":"deny"\|"mask","injectHosts","extract","onExtractNoMatch","decode","maskClaims"}` |
| `credentials.files[]` | Any file (`mask` j.w.) | `{"path","mode","extract","decode","injectHosts","onExtractNoMatch","maskDuplicates"}` |
| `credentials.awsPairs`, `credentials.sigv4` | User or managed | AWS SigV4 (≥2.1.224) |
| `credentials.allowPlaintextInject` | User or managed | wstrzykiwanie do HTTP bez TLS — nie |

## 2. Prefiksy ścieżek piaskownicy

`/` = korzeń (także `//`), `~/` = dom, `./` lub brak = korzeń projektu (plik projektu) albo
`~/.claude` (plik użytkownika). **Inaczej niż w regułach Read/Edit**, gdzie `/` to źródło
ustawień. Ukośnik końcowy i końcowe `/**` są zdejmowane. Globy: w listach zapisu na Linuksie
pomijane; w listach odczytu rozwijane do ścieżek.

Reguły uprawnień zasilają piaskownicę: `Edit` allow → `allowWrite`; `Read`/`Edit` deny →
`denyRead`/`denyWrite`; `WebFetch(domain:…)` allow/deny → listy domen (honorowane `*.x`
i gołe `*` ≥2.1.186). Wszystko scalane ze wszystkich zakresów.

## 3. Odczyt przy `blockReadsOutsideWorkingDirectories`

Polecenia w piaskownicy tracą odczyt katalogu domowego i katalogów z plikami użytkownika
(poza wyjątkami z settings-reference „Sandboxed commands under the block”) — prostszy sposób
niż ręczne `denyRead: ["~/"]` + `allowRead`.

## 4. Maskowanie poświadczeń

- Zmienna: polecenie widzi sentinel; proxy podmienia go na wartość prawdziwą w nagłówkach
  i ciele żądań do `injectHosts` (bez `injectHosts` — do wszystkich `allowedDomains`).
  Wymaga `tlsTerminate`; host musi być na liście domen; `deny` wygrywa z `mask`.
- Plik (Linux/WSL2): kopia z sentinelem + podmiana na wyjściu; `extract` (grupa 1 wyrażenia)
  zostawia resztę pliku czytelną; macOS — plik niedostępny (jak `deny`, ale odporne na
  `filesystem.disabled`).
- Fallback do `deny`: katalog, glob, plik >8 MiB, nie-UTF-8.
- AWS: maskuj klucz i sekret razem (proxy ponownie podpisuje SigV4); `awsPairs` dla
  niestandardowych nazw; `sigv4` dla form niepodpisywalnych (strumieniowe, presigned, SigV4A).
- `claude doctor` ostrzega o nieosiągalnych `injectHosts` (≥2.1.229).

## 5. Organizacja

```json
{
  "sandbox": {
    "enabled": true, "failIfUnavailable": true, "allowUnsandboxedCommands": false,
    "filesystem": {"allowManagedReadPathsOnly": true, "denyRead": ["~/.ssh", "~/.aws"]},
    "network": {"allowManagedDomainsOnly": true, "allowedDomains": ["registry.npmjs.org", "github.com"]}
  }
}
```
Klucze logiczne z managed wygrywają; listy się sumują — dlatego blokady
`allowManaged*Only`. Gdy managed konfiguruje `sandbox.filesystem` lub ma `credentials.files`
z `deny`, tylko managed może ustawić `filesystem.disabled`. Natywny Windows nie ma
piaskownicy — tam WSL2 lub kontener.

## 6. Rozwiązywanie problemów

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| tylko zakładka Dependencies w `/sandbox` | brak `bwrap`/`socat` | instalacja (pakiety systemowe zatwierdza właściciel serwera) |
| `Can't mount proc on /newroot/proc` | kontener bez uprawnień | `enableWeakerNestedSandbox: true` przy zewnętrznej izolacji |
| `apply-seccomp: write /proc/self/setgroups (nested userns is capability-restricted…)` | jądro ogranicza zagnieżdżone przestrzenie użytkownika dla pomocnika seccomp (danaco-nexus, jądro 7.0) | `allowAllUnixSockets: true` (bez filtra gniazd); `enableWeakerNestedSandbox` nie pomaga |
| `CONNECT tunnel failed, response 403` + `<sandbox_violations> deny network-outbound host:443 (host is not on the allow list)` | domena spoza listy przy `strictAllowlist` | dopisz do `allowedDomains` albo zostaw blokadę |
| `Read-only file system` przy zapisie | ścieżka poza katalogami zapisu | `allowWrite` dla konkretnego katalogu |
| `unable to unlink old` w gicie | zapis do ścieżki chronionej piaskownicy | wykonaj poza piaskownicą (człowiek) |
| 0-bajtowe pliki tylko do odczytu w `.claude/` | przerwana sesja nie posprzątała zaślepek | `claude doctor` je wymienia, usuń ręcznie (≥2.1.257 sprząta sam) |
| Go CLI (`gh`, `terraform`) nie weryfikują TLS na macOS | Seatbelt | `excludedCommands` lub `enableWeakerNetworkIsolation` przy MITM |
| `--dangerously-skip-permissions` jako root | blokada bezpieczeństwa | użytkownik nie-root (dev container) |

## 7. Ograniczenia bezpieczeństwa

- Proxy nie inspekcjonuje TLS (poza `tlsTerminate`) — domain fronting przy szerokich
  domenach; dla wysokiego ryzyka własne proxy z inspekcją.
- Gniazda uniksowe (`docker.sock`) = obejście piaskownicy.
- Szeroki `allowWrite` (katalogi z `$PATH`, `.bashrc`) = wykonanie kodu w innym kontekście.
- `enableWeakerNestedSandbox` znacząco osłabia izolację.
- Zmienne środowiska są dziedziczone przez polecenia, dopóki ich nie odbierzesz
  (`credentials.envVars`, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`).
- Podagenci dzielą konfigurację piaskownicy z sesją główną.
