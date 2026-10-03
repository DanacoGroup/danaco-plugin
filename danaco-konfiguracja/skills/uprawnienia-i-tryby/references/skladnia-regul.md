# Składnia i dopasowanie reguł uprawnień

Źródła: `cc:permissions`, `cc:permission-modes` („Protected paths”, „Critical paths”),
`cc:settings-reference` (`permissions.*`), `cc:errors`. Stan: 01.10.2026.

## 1. Postać reguły

`Narzędzie` albo `Narzędzie(specyfikator)`. Nawiasy wewnątrz specyfikatora są dosłowne
(`Edit(./Finance (2024)/**)` działa bez ucieczek). `Bash(*)` = `Bash`. Reguły trafiają do
`permissions.allow|ask|deny` (pliki, `--settings`) albo do flag `--allowed-tools`
i `--disallowed-tools` (reguły sesji).

Kolejność oceny: **deny → ask → allow**; pierwsze trafienie wygrywa. Allow nie tworzy
wyjątku od deny, ask wygrywa z allow. Reguły z wszystkich warstw się sumują, chyba że
managed ma `allowManagedPermissionRulesOnly: true`.

## 2. Bash i PowerShell

| Wzorzec | Pasuje | Nie pasuje |
|---|---|---|
| `Bash(npm run build)` | `npm run build` | `npm run build --watch` |
| `Bash(npm run *)` | `npm run build`, `npm run test --watch`, `npm run` | `npm install` |
| `Bash(git log * main)` | `git log --oneline main` | `git log main` |
| `Bash(git * main)` | `git merge main`, `git push origin main`, `git -c core.fsmonitor=<skrypt> diff main` | `git log` |
| `Bash(* --version)` | `node --version` (każdy program) | `node -v` |
| `Bash(ls *)` | `ls -la`, `ls` | `lsof` |
| `Bash(ls*)` | `ls -la`, `lsof` | — |
| `Bash(ls:*)` | jak `Bash(ls *)`; `:*` tylko na końcu (`Bash(git:* push)` — dwukropek dosłowny) | — |

Zasady:
- `*` zastępuje dowolny tekst (także spacje); końcowe ` *` łapie też gołe polecenie, jeśli
  to jedyna gwiazdka.
- **`*` stawiaj po podpoleceniu.** Gwiazdka przed podpoleceniem w allow (`Bash(git * main)`)
  daje ostrzeżenie przy starcie („has a wildcard before the rest of the command”).
- Polecenia złożone dzielone są po `&&`, `||`, `;`, `|`, `|&`, `&`, nowej linii — allow
  musi pasować do **każdego** podpolecenia; deny/ask pasuje, gdy pasuje **którekolwiek**
  (także w `$(…)`, w podpowłoce, w ciele pętli).
- `npm test &&` (pusty człon) = nieparsowalne → allow nie pasuje.
- Zdejmowane opakowania: `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`,
  `noglob`, gołe `xargs` (bez flag). **Nie** zdejmowane: `direnv exec`, `devbox run`,
  `mise exec`, `npx`, `docker exec` — `Bash(devbox run *)` zatwierdza wszystko po `run`.
- Zdejmowane przypisania znanych bezpiecznych zmiennych (`NODE_ENV=test npm test`); allow
  nie pasuje za przypisaniem innej zmiennej; deny/ask — pasuje za każdym.
- Opakowania wykonawcze `watch`, `setsid`, `ionice`, `flock` i `find -exec/-delete` nie dają
  się zatwierdzić prefiksem — tylko dokładnym poleceniem.
- Granice: `/usr/bin/curl`, `sh -c '…'`, `git -C . push`, `git 'push'` omijają regułę
  napisaną dla typowej postaci. Twarda granica = piaskownica.
- PowerShell: ta sama postać, aliasy kanonizowane (`Get-ChildItem` = `gci`, `ls`, `dir`),
  wielkość liter bez znaczenia, AST dzieli polecenia.

### Polecenia tylko do odczytu

Bez pytania w każdym trybie (poza `blockReadsOutsideWorkingDirectories` dla ścieżek spoza
katalogów roboczych): `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`,
`diff`, `stat`, `du`, `cd` (w katalogach roboczych), odczytowe `git`. Zbiór nie jest
konfigurowalny. Pytają mimo to: glob przy poleceniach z flagami zapisu (`find`, `sort`,
`sed`, `git`), `docker` z innym demonem (`-H`, `--context`), `file -m/-f`, ścieżki UNC,
zapis zmiennych specjalnych (`PATH`, `IFS`), polecenia nieparsowalne i dłuższe niż
10 000 znaków, `cd` + `git` do innego katalogu, `cd` + przekierowanie o nieustalonym celu.

### Przekierowania

`> plik`, `>> plik`, `2> plik` — sprawdzane jak `Edit` celu (reguły, ścieżki chronione,
katalogi robocze); cel z `~` lub globem wymaga zgody. `< plik` — jak `Read` (≥2.1.257).
Cele `tee` — jak `Edit` (≥2.1.269). Bez sprawdzenia: `/dev/null`, `2>&1`, here-doc.

## 3. Read i Edit (ścieżki)

Składnia gitignore. `Edit` obejmuje wszystkie narzędzia edytujące; `Read` — w miarę
możliwości Grep, Glob, wzmianki `@plik`, kontekst IDE. Reguły ścieżek dla `Write`,
`NotebookEdit`, `Glob`, `MultiEdit` są przyjmowane, ale **nigdy nie sprawdzane** (ostrzeżenie).
Deny `Read` blokuje też Edit (≥2.1.208) i Write (≥2.1.228) tej ścieżki; NotebookEdit nie.

**Próba 2.1.286 — goła nazwa `Edit` dotyczy tylko narzędzia Edit**: allow `"Edit"` nie zatwierdza
`Write`, a deny `"Edit"` go nie blokuje (Write przeszedł w `acceptEdits` i `bypassPermissions`).
Reguła ze ścieżką obejmuje wszystkie narzędzia edytujące: allow/deny `"Edit(./**)"` lub
`"Edit(**)"` działa na `Write` (`Edit(*)` — nie). Gołe nazwy wymieniaj parami (`"Edit", "Write"`)
albo używaj `Edit(./**)`.

| Wzorzec | Znaczenie | Przykład |
|---|---|---|
| `//ścieżka` | od korzenia systemu | `Read(//etc/**)` |
| `~/ścieżka` | od katalogu domowego | `Read(~/.ssh/**)` |
| `/ścieżka` | od **źródła ustawień** | projekt: katalog roboczy; `~/.claude/settings.json`: `~/.claude`; plik `--settings`: jego katalog; flagi: katalog roboczy |
| `ścieżka`, `./ścieżka` | od katalogu bieżącego | `Read(*.env)` |

- Nazwa pliku bez katalogu pasuje na każdej głębokości: `Read(.env)` = `Read(**/.env)`.
- Jeden segment katalogu (`src/**`): w allow tylko `<cwd>/src`, w deny/ask — `src` na każdej
  głębokości. `**/src/**` — wszędzie w każdym typie.
- `!wzorzec` w deny/ask (gitignore) wycina wyjątek z wcześniejszych reguł **tego samego
  źródła**, nie sięga reguł z `/`, `~/`, `//`, nie otwiera pliku w zablokowanym katalogu.
- Dowiązania: allow — muszą pasować ścieżka i cel; deny — wystarczy jedno; zapis przez
  dowiązanie odrzucany i kierowany na cel.
- Windows: ścieżki normalizowane do `/c/Users/...`; `//c/**/.env`, `//**/.env`.

Deny `Read`/`Edit` działa na narzędzia plikowe i rozpoznane polecenia Bash (`cat`, `head`,
`tail`, `sed`, `tee`, przekierowania), **nie** na `grep -r .` z katalogu nadrzędnego ani
dowolne podprocesy — tę lukę zamyka piaskownica (dodaje ścieżki `Read` deny do `denyRead`).

## 4. WebFetch

`WebFetch(domain:example.com)`; `domain:*.example.com` = subdomeny dowolnej głębokości
(bez samej domeny); `domain:example.*` — `*` w środku obejmuje tylko jeden segment
(nie `example.evil.com`); wielkość liter i kropka końcowa bez znaczenia; gwiazdki ≥2.1.172.

| Reguła | W allow | W deny |
|---|---|---|
| `WebFetch` | pobiera bez pytania; lista piaskownicy bez zmian | usuwa narzędzie |
| `WebFetch(domain:*)` | pobiera bez pytania **i** otwiera piaskownicę na każdy host | zostawia narzędzie, odrzuca każde pobranie i blokuje sieć piaskownicy |

WebFetch nie zastępuje blokady sieci: przy dozwolonym Bash model użyje `curl`.

## 5. MCP

`mcp__serwer` = `mcp__serwer__*` = wszystkie narzędzia serwera; `mcp__serwer__narzedzie`.
W allow glob tylko po dosłownym `mcp__<serwer>__` (`mcp__github__get_*`); `mcp__*` w allow
jest pomijane. **Reguła `mcp__…` z nawiasami w pliku ustawień jest pomijana** („MCP rules do
not support patterns in parentheses” — `claude doctor`); parametr narzędzia MCP blokuj
flagą `--disallowed-tools`. Narzędzia serwera z wtyczki: `mcp__plugin_<wtyczka>_<serwer>__…`.
Konektor claude.ai ustawiony przez organizację na `ask` — allow nie działa, `dontAsk` odrzuca.

## 6. Agent, Skill, Cd i parametry narzędzi

- `Agent(Explore)`, `Agent(nazwa-agenta)` — w deny wyłącza typ podagenta.
- `Tool(param:wartość)` — tylko deny/ask, każde wbudowane narzędzie, parametr najwyższego
  poziomu, jeden parametr na regułę, `*` w wartości, parametr pominięty nie pasuje,
  porównanie przed normalizacją (`Agent(model:opus)` nie złapie pełnego ID). Przykłady:
  `Agent(model:*)`, `Agent(isolation:worktree)`, `Bash(run_in_background:true)`.
  Główne pola są wykluczone (`command`, `file_path`, `path`, `notebook_path`, `url`).
- `Skill(skill:nazwa)` — deny skilla pod każdą jego nazwą (alias, nazwa wyświetlana).
- `Cd` — goły deny wyłącza `/cd`; dowolny allow włącza tryb listy dozwolonej.
- Glob nazwy narzędzia (`*`, `mcp__*`) — w deny/ask usuwa narzędzia z kontekstu; deny/ask
  z nieznaną nazwą daje ostrzeżenie (poza nazwami z `_` lub `*`). Reguły i matchery hooków
  używają nazw kanonicznych (`TaskStop`, nie etykiety „Stop Task”).

## 7. Ścieżki chronione

Katalogi: `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`,
`.yarn`, `.mvn`, `.claude` (poza `.claude/worktrees`), katalog z `--plugin-dir`.
Pliki: `.gitconfig`, `.gitmodules`, `.bashrc`, `.bash_profile`, `.bash_login`,
`.bash_aliases`, `.bash_logout`, `.zshrc`, `.zprofile`, `.zshenv`, `.zlogin`, `.zlogout`,
`.profile`, `.envrc`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `.pnp.cjs`, `.pnp.loader.mjs`,
`.pnpmfile.cjs`, `bunfig.toml`, `.bunfig.toml`, `.bazelrc`, `.bazelversion`, `.bazeliskrc`,
`.pre-commit-config.yaml`, `lefthook.yml`, `lefthook.yaml`, `.lefthook.yml`, `.lefthook.yaml`,
`gradle-wrapper.properties`, `maven-wrapper.properties`, `.devcontainer.json`, `.ripgreprc`,
`pyrightconfig.json`, `.mcp.json`, `.claude.json`.

| Tryb | Zapis do ścieżki chronionej |
|---|---|
| `default`, `acceptEdits` | pytanie |
| `plan` | pytanie (albo klasyfikator przy dostępnym auto) |
| `auto` | klasyfikator (w `--restricted` nie zatwierdzi) |
| `dontAsk` | odmowa |
| `bypassPermissions` | dozwolone |

Allow z plików nie zatwierdza ścieżek chronionych (sprawdzenie bezpieczeństwa jest przed
regułami).

## 8. Ścieżki krytyczne (`rm`, `rmdir`)

Korzeń, katalogi najwyższego poziomu (`/usr`, `/etc`…), katalog domowy, katalog roboczy
i jego rodzice, glob pod katalogiem dodatkowym, glob pod pustą zmienną (`rm -rf "$DIR"/*`),
`rm -rf "$(pwd)"`, zmienna z `$(pwd)`/`$(git rev-parse --show-toplevel)`. Żaden allow ani
hook „allow” ich nie zatwierdzi. `default`/`acceptEdits`/`plan` pytają, `auto` pyta
w terminalu (2 min), gdzie indziej odmawia, `dontAsk` odmawia, `bypassPermissions` pyta.
Przepisanie: `rm -rf "${DIR:?}"/*` albo ścieżka dosłowna.

## 9. Katalogi robocze

Katalog startu (główny), `--add-dir`, `/add-dir`, `permissions.additionalDirectories`.
Pliki w nich: odczyt bez pytania, edycja wg trybu. `blockReadsOutsideWorkingDirectories`
(≥2.1.257) każe narzędziom plikowym odmawiać poza nimi w każdym trybie, a rozpoznane
polecenia czytające — pytać nawet w `auto`/`bypassPermissions`.
`--add-dir` wczytuje z dodanego katalogu tylko: skille (`.claude/skills`), polecenia,
podagentów, z ustawień `enabledPlugins` i `extraKnownMarketplaces`; CLAUDE.md tylko przy
`CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`. Katalogi z `additionalDirectories`
w pliku dają tylko dostęp do plików. `/cd` przenosi sesję i wczytuje konfigurację nowego
katalogu (≥2.1.246).

## 10. Hooki a reguły

`PreToolUse` uruchamia się przed pytaniem; jego „allow” nie przebija deny i ask. Mod
(`plugins/mods`) z `tool.check` może zmienić wynik po regułach — na maszynie z ustawieniami
zarządzanymi lub w planie Team/Enterprise deny trzyma się wobec moda domyślnie.
