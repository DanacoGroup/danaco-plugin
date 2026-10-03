# Przepisy hooków — gotowe rozwiązania z uzasadnieniem

Każdy przepis: potrzeba → zdarzenie i typ → konfiguracja → na co uważać. Skrypty
w `../examples/`. Przepisy oznaczone „próba” sprawdzono w CLI 2.1.286 na atrapie API.

## 1. Blokada poleceń niszczących (próba)

`PreToolUse`, matcher `Bash`, `command` w formie exec → `examples/blokuj_niebezpieczne.py`.
Deny z powodem trafia do modelu jako błąd narzędzia („PreToolUse:Bash hook error: …”);
działa także w `bypassPermissions`. Granica nie jest szczelna (reguły tekstowe) — łącz
z piaskownicą. Wąskie `if: "Bash(rm *)"` oszczędza uruchomień.

## 2. Formatowanie po edycji

`PostToolUse`, matcher `Edit|Write`, `if: "Edit(**/*.py)"`, polecenie formatera
z `jq -r .tool_input.file_path`. Długie zadania (testy) → `"async": true` (wynik w następnej
turze; w `-p` zabijane na końcu) albo `asyncRewake` (budzi model przy exit 2).

## 3. Ochrona plików przed edycją

`PreToolUse`, matcher `Edit|Write`, skrypt odrzucający ścieżki z listy (np. `migrations/`,
`.env`). Prościej i pewniej: reguła `deny` `Edit(./migrations/**)` — hook tylko wtedy,
gdy potrzebna logika (np. wyjątek dla właściciela zmiany).

## 4. Kontekst na starcie i po kompakcji (próba)

`SessionStart`, matcher `startup|resume|compact`, skrypt `examples/kontekst_sesji.sh`:
stdout (fakty: gałąź, zmiany, polecenie testów) trafia do kontekstu; `export` dopisywane
do `$CLAUDE_ENV_FILE` obowiązują w każdym poleceniu Bash sesji (próba: `printenv NODE_ENV`
→ `development`). Podagenci nie dziedziczą `SessionStart` → osobny hook `SubagentStart`
z `additionalContext`. Limit 10 000 znaków na łańcuch — większy kontekst podziel na kilka
hooków albo przenieś do `--append-system-prompt-file`.

## 5. Weryfikacja przed końcem tury (próba)

`Stop`, `command` → `examples/weryfikacja_stop.py`: jeśli istnieje `.do-zrobienia`,
`decision: block` z listą punktów; przy `stop_hook_active: true` przepuszcza. Próba: model
dostał powód w kolejnym żądaniu, druga odpowiedź zakończyła turę. Wersja „modelem”:
`examples/ocena-modelem.user.settings.json` (`type: prompt`, `ok/reason/impossible`) —
kosztuje dodatkowe wywołanie przy każdym zakończeniu.

## 6. Polityka zgód w kodzie (próba)

`PermissionRequest`, matcher `Bash` → `uprawnienia-i-tryby/examples/zgoda.py`
(`decision.behavior` allow/deny). Exit 2 ignorowany. W próbie działa w czystym `-p`, choć
dokumentacja zaleca tam `PreToolUse` — dla przenośności polityk używaj `PreToolUse`.

## 7. Dziennik produktu przez HTTP

`http` na `PermissionDenied`, `PostModelSwitch`, `StopFailure`, `PostCompact` do lokalnej
usługi; `allowedHttpHookUrls` zawęża adresy, `allowedEnvVars` pozwala wstawić token do
nagłówka. Status HTTP nie blokuje — przy błędzie usługi praca idzie dalej.
Szablon: `examples/produkt-hooki.flaga.settings.json`; generator `generuj_ustawienia.py
--hook-dziennik`.

## 8. Strażnik podagentów w serwerze MCP

`PreToolUse`, matcher `Agent`, `mcp_tool` → narzędzie serwera produktu z
`input: {"typ": "${tool_input.subagent_type}"}`. Logika i dziennik poza procesem modelu.
Nie dla `SessionStart`/`Setup` (pomijane). Narzędzia hooków ukrywaj przed modelem
(np. regułą deny w `--disallowed-tools` — działanie z hookiem `mcp_tool` sprawdź próbą
w swojej wersji).

## 9. Blokada `/skill` wpisanego przez użytkownika

`UserPromptExpansion` (matcher = nazwa polecenia) z `decision: block` — wpisanie
`/nazwa` omija `PreToolUse`. W produkcie prościej: `--disable-slash-commands`.

## 10. Audyt zmian ustawień

`ConfigChange`, matcher `project_settings|local_settings`, zapis do dziennika i ewentualnie
`decision: block` (zmian `policy_settings` nie zablokujesz).

## 11. Kontrola zmiany modelu

`PreModelSwitch` z `permissionDecision: deny` dla modeli spoza polityki (timeout też
blokuje; `ask` poza `/model` = odmowa). Twardszą kontrolę daje `availableModels`.
`PostModelSwitch` rejestruje także automatyczny fallback (oznaczenie przez klasyfikator).

## 12. Powiadomienie o czekaniu na człowieka (interaktywnie)

`Notification`, matcher `permission_prompt|idle_prompt`, skrypt zwracający
`{"terminalSequence": "\u001b]777;notify;Claude Code;Czekam\u0007"}` (OSC 777/9/99).
W `-p` pole jest ignorowane.

## 13. Wyłączenie wszystkich hooków na jedno uruchomienie

`claude -p … --settings '{"disableAllHooks": true}'` — samo ustawienie w pliku
użytkownika nie wystarczy (projekt może je przestawić); hooków zarządzanych nie wyłącza.

## 14. Hooki we wtyczce

`hooks/hooks.json` (szablon `examples/hooks.json`): forma exec z
`${CLAUDE_PLUGIN_ROOT}`, trwałe dane w `${CLAUDE_PLUGIN_DATA}`, opcje użytkownika
`${user_config.klucz}` tylko w formie exec. Sprawdzenie: `claude plugin validate`.

## 15. Wtyczka wbudowana a hooki (obserwacja z próby)

W CLI 2.1.286 wbudowana wtyczka `cc-plugin-sec-default` rejestruje hook `PreToolUse:Bash`
także przy `--setting-sources ""` (widać go z `--include-hook-events`); `--bare` jej nie
ładuje. Licz się z tym przy pomiarze czasu i przy porządku decyzji wielu hooków.
