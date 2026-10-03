# Host uprawnień: kto odpowiada na pytanie o zgodę

Źródła: `cc:cli-reference` (`--permission-prompt-tool`, `--permission-prompts`),
`cc:headless` („Turn off permission prompts in unattended runs”), `cc:hooks`
(`PermissionRequest`), `cc:agent-sdk/typescript` (`canUseTool`, `PermissionResult`),
`cc:mcp` („Require approval for a specific tool”). Kontrakt narzędzia zgody sprawdzony
próbą na CLI 2.1.286 (atrapa API + `examples/serwer_wzorcowy.py` z pakietu `serwery-mcp`).

## 1. Cztery mechanizmy

| Mechanizm | Gdzie | Kolejność |
|---|---|---|
| reguły i tryb | wszędzie | najpierw: deny/ask/allow, potem tryb |
| hook `PermissionRequest` | pliki ustawień, wtyczki | gdy CLI ma pytać — przed hostem |
| host: `--permission-prompt-tool` (narzędzie MCP) albo SDK `canUseTool` | `-p`, SDK | gdy nic wcześniej nie rozstrzygnęło |
| człowiek | interaktywnie | ostatni |

`--permission-prompts host` (domyślne) kieruje pytania do hosta; `none` (≥2.1.259) odmawia
bez czekania, usuwa `AskUserQuestion`, anuluje elicitation bez hooka `Elicitation`; odmowy
trafiają do `permission_denied` (stream-json) i `permission_denials` w wyniku.

## 2. Narzędzie zgody MCP (`--permission-prompt-tool mcp__serwer__narzedzie`)

Kontrakt (próba 2.1.286):

- **Wejście** (argumenty `tools/call`):
  `{"tool_name": "Bash", "input": {"command": "touch zapis.txt", "description": "…"}, "tool_use_id": "toolu_…"}`
- **Wyjście**: treść tekstowa z JSON-em w kształcie `PermissionResult`:
  - `{"behavior": "allow", "updatedInput": {…}}` — wykonaj (z wejściem, które zwróciłeś;
    wejście jest ponownie oceniane wobec deny/ask),
  - `{"behavior": "deny", "message": "…"}` — odmów; `message` dostaje model jako błąd narzędzia
    (opcjonalnie `"interrupt": true` — zatrzymaj pracę).
- CLI **ukrywa narzędzie zgody przed modelem** (w `system/init.tools` go nie ma).
- CLI czeka na połączenie serwera do `MCP_TIMEOUT` (domyślnie 30 s) przed pierwszą turą.
- Narzędzie z `_meta["anthropic/requiresUserInteraction"]: true` — allow z narzędzia zgody
  zamieniany jest na deny („MCP tool requires user interaction; not supported via
  --permission-prompt-tool”, ≥2.1.199). Takie zgody obsłuży tylko SDK `canUseTool`.
- Hook `PermissionRequest` rozstrzyga wcześniej — host dostaje tylko resztę.

Zastosowanie w produkcie: narzędzie zgody pokazuje kartę w interfejsie produktu (np.
„Agent chce wysłać pocztę”), czeka na decyzję użytkownika i zwraca allow/deny. Dla długich
decyzji ustaw `dialogExpiry` (≥2.1.224, zasięg User or managed — w `--settings` działa)
oraz `MCP_TOOL_TIMEOUT`.

## 3. Hook `PermissionRequest`

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {"command": "npm run lint"},
      "updatedPermissions": [
        {"type": "addRules", "rules": [{"toolName": "Bash", "ruleContent": "npm run lint"}],
         "behavior": "allow", "destination": "session"}
      ]
    }
  }
}
```

- `behavior: "deny"` + `message` (+ `interrupt`); exit 2 jest **ignorowany** — odmowa tylko
  obiektem `decision`.
- `updatedPermissions`: `addRules`, `replaceRules`, `removeRules`, `setMode`, `addDirectories`,
  `removeDirectories`; `destination`: `session`, `localSettings`, `projectSettings`,
  `userSettings`. `setMode: bypassPermissions` działa tylko, gdy bypass był dostępny od
  startu; nigdy nie zapisuje się jako `defaultMode`.
- Hook typu `prompt`/`agent` nie odmówi tu (`ok: false` bez skutku) — użyj `command`.
- Wejście hooka zawiera `permission_suggestions` — hook może je odesłać jako własne
  `updatedPermissions`.

## 4. SDK `canUseTool`

Callback `(toolName, input, {signal, suggestions, …}) => PermissionResult`. W CLI
odpowiada mu `control_request` typu `can_use_tool` w stream-json (gdy host jest
aplikacją SDK). Callback otrzymuje także narzędzia z `requiresUserInteraction` i może je
zatwierdzić (aplikacja odpowiada za realny kontakt z człowiekiem). Odpowiedź `null` tylko
wtedy, gdy host sam wysłał `control_response` — inaczej wywołanie wisi bez końca.

## 5. Zalecenia dla usług

1. Najpierw reguły i `dontAsk` — host jest dla wyjątków, nie dla każdego wywołania.
2. Bez hosta zawsze `--permission-prompts none`, żeby przebieg nie czekał.
3. Narzędzie zgody trzymaj w serwerze MCP produktu (logika i dziennik decyzji poza procesem
   modelu); zwracaj krótkie, rzeczowe `message` — model dostaje je jako przyczynę.
4. Narzędzi wymagających świadomej zgody człowieka nie oznaczaj `requiresUserInteraction`,
   jeśli host to narzędzie MCP — zostaną zawsze odrzucone; obsłuż je w hoście SDK.
5. Rejestruj `PermissionDenied` (tryb auto) i `permission_denials` (wynik) w dzienniku produktu.
