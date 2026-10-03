---
name: budowa-skilli
description: >
  Skille Claude Code: budowa pakietu (SKILL.md, references/, scripts/, examples/),
  frontmatter (description, when_to_use, disable-model-invocation, user-invocable,
  allowed-tools, context: fork, agent, paths, hooks, model, effort), miejsca ładowania
  i pierwszeństwo nazw, podstawienia ($ARGUMENTS, ${CLAUDE_SKILL_DIR}), wstrzykiwanie
  wyniku poleceń (!`…`), budżet listy skilli (skillListingBudgetFraction, 1536 znaków),
  skillOverrides, disableBundledSkills, skille wbudowane, cykl życia treści po kompakcji,
  pisanie skilli uczących umiejętności i ich ewaluacja (claude plugin eval). Stosuj, gdy
  pada „napisz skill”, „skill się nie uruchamia”, „skill odpala się za często”, „ukryj
  skill”, „wyłącz skille wbudowane”, „opis skilla jest ucinany”.
---

# Budowa skilli

## Kiedy stosować

Gdy wiedza, procedura albo zestaw skryptów ma być ładowany **na żądanie** (opis w kontekście
zawsze, treść po wywołaniu, pliki dodatkowe dopiero gdy potrzebne). Nie do zasad, które
muszą obowiązywać zawsze — to hook (gwarancja) albo CLAUDE.md (stały kontekst).

| Potrzeba | Mechanizm |
|---|---|
| wiedza i procedura używana czasem | skill |
| stała konwencja projektu | CLAUDE.md / `.claude/rules/` |
| reguła obowiązująca zawsze | hook |
| zadanie w osobnym kontekście | skill z `context: fork` albo podagent ze `skills:` |
| polecenie uruchamiane tylko przez człowieka (`/deploy`) | skill z `disable-model-invocation: true` |
| wiedza tła, nie polecenie | skill z `user-invocable: false` |

## Anatomia pakietu (progresywne ujawnianie)

```
nazwa-skilla/
├── SKILL.md          rdzeń: kiedy, decyzje, procedura, pułapki, odsyłacze (< 500 wierszy)
├── references/       wiedza szczegółowa — czytana na żądanie; jeden poziom odwołań
├── scripts/          kod wykonywany (nie ładowany): walidatory, generatory, próby
└── examples/         szablony gotowe do skopiowania, sprawdzone walidacją
```

- Wpis w liście skilli (nazwa + `description` + `when_to_use`, ucinany do 1536 znaków)
  jest w kontekście **w każdej turze** — to koszt stały. Specyfikacja Agent Skills
  ogranicza `description` do 1024 znaków.
- Lista ma budżet 1% okna kontekstu; przy nadmiarze CLI wycina opisy (zostają nazwy).
  Podnieś: `skillListingBudgetFraction` (np. `0.02`) albo `SLASH_COMMAND_TOOL_CHAR_BUDGET`;
  zwolnij: `skillOverrides` → `"name-only"`. Diagnoza: `/doctor`, `/context`, `/skill-doctor` (≥2.1.252).
- Treść po wywołaniu zostaje w rozmowie na stałe; po kompakcji wraca pierwsze 5 000 tokenów
  każdego skilla (łącznie 25 000) — najważniejsze instrukcje na początku.

## Frontmatter — decyzje

| Pole | Kiedy |
|---|---|
| `description` | zawsze: co robi + kiedy (frazy użytkownika), w 3. osobie, kluczowe słowa na początku |
| `when_to_use` | dodatkowe frazy wyzwalające (liczą się do 1536) |
| `disable-model-invocation: true` | efekty uboczne (wdrożenie, wysyłka) — tylko człowiek; opis znika z kontekstu |
| `user-invocable: false` | wiedza tła — tylko model |
| `allowed-tools` | narzędzia bez pytania **w turze wywołania** (nie ogranicza zestawu; zaufanie folderu tego nie blokuje — przeglądaj skille z repozytoriów) |
| `disallowed-tools` | odebranie narzędzi na czas skilla |
| `context: fork` + `agent` | zadanie w osobnym podagencie (treść skilla = zlecenie; bez historii rozmowy); `background: false` czeka na wynik (≥2.1.218) |
| `paths` | auto-ładowanie tylko przy pracy na pasujących plikach |
| `model`, `effort` | do końca bieżącej tury |
| `hooks` | od wywołania do końca sesji; `once: true` |
| `arguments`, `argument-hint` | argumenty pozycyjne `$0`, nazwane `$nazwa` |
| `shell` | `bash` / `powershell` dla wstrzykiwania |

Nieznane pole (np. literówka `allowed_tools`) jest **pomijane bez komunikatu**. Frontmatter
musi zaczynać się w pierwszym wierszu; błędny YAML = skill bez metadanych (działa tylko `/nazwa`).

## Podstawienia i wstrzykiwanie

`$ARGUMENTS`, `$N`, `$nazwa`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}` (≥2.1.196),
`${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, we wtyczce `${CLAUDE_PLUGIN_ROOT}`,
`${CLAUDE_PLUGIN_DATA}` — podstawiane w treści i w regułach Bash `allowed-tools` (skrypt
skilla bez pytania: `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/x.sh *)`).
`` !`polecenie` `` i bloki ` ```! ` wykonują się przed wysłaniem treści: błąd (kod ≠ 0, poza
kodem 1 narzędzi wyszukiwania) przerywa całe wywołanie; polecenie bez zgody przerywa
(poza trybem auto); `disableSkillShellExecution: true` zastępuje je komunikatem; skille
z claude.ai nigdy ich nie wykonują.

## Gdzie skill się ładuje (pierwszeństwo przy tej samej nazwie)

organizacja (`.claude/skills` w katalogu zarządzanym) > osobiste (`~/.claude/skills`) >
projektu (`.claude/skills`, także katalogi nadrzędne do korzenia repozytorium; zagnieżdżone
ładują się, gdy model pracuje w ich katalogu) > wbudowane (Twój skill zastępuje polecenie,
nie jego aliasy) > `.claude/commands/*.md` (starszy format). Wtyczka: `/wtyczka:skill`
(osobna przestrzeń nazw). claude.ai: `/anthropic-skills:nazwa`. Nazwy zastrzeżone:
`synced`, `anthropic-skills`. Folder skilla z `.claude-plugin/plugin.json` = wtyczka `@skills-dir`.

## Kontrola skilli w sesji i produkcie

- `disableBundledSkills: true` / `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1` — bez skilli
  wbudowanych Anthropic (`/simplify`, `/batch`, `/code-review`…; nie obejmuje poleceń
  wbudowanych jak `/auto-mode-setup`).
- `skillOverrides: {"nazwa": "on"|"name-only"|"user-invocable-only"|"off"}` — widoczność
  bez edycji SKILL.md (nie dotyczy skilli wtyczek; alias w managed/`--settings` tylko zawęża).
- Uprawnienia: deny `Skill` (żadnych), `Skill(nazwa)`, `Skill(nazwa *)`, `Skill(skill:nazwa)`.
- `--disable-slash-commands` — brak poleceń i skilli w sesji (produkty: klient nie wywoła
  `/…`); `CLAUDE_CODE_DISABLE_POLICY_SKILLS=1` — bez skilli zarządzanych.
- `syncClaudeAiSkills: false` — bez skilli z konta claude.ai.
- Wpisanie `/skill` przez użytkownika omija `PreToolUse` — kontrola hookiem `UserPromptExpansion`.

## Procedura pisania skilla uczącego

1. Zbierz 3–5 realnych próśb, które mają go wyzwolić, i 2 podobne, które nie powinny.
2. Napisz `description` pod te prośby (co + kiedy + czego nie obejmuje, odesłanie do sąsiednich skilli).
3. Rdzeń SKILL.md: kiedy stosować → decyzje (tabele „sytuacja → wybór”) → procedura
   (kroki z poleceniami skryptów) → pułapki → minimalne wersje → szablony → referencje.
   Ucz **rozstrzygania**, nie wyliczania: wyliczenia kluczy idą do `references/` lub indeksów.
4. Szczegóły do `references/` (jeden poziom; plik > 300 wierszy ze spisem treści).
5. Powtarzalne sprawdzenia do `scripts/` (walidator, generator, próba) — skrypt
   „rozwiązuje, nie odsyła” (jasne komunikaty błędów, kody wyjścia).
6. Szablony do `examples/` — każdy sprawdzony (walidator, `claude doctor`, próba).
7. Lint: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/budowa-skilli/scripts/sprawdz_skill.py" <katalog> --cli "$(command -v claude)"`
   (+ `--spec` przed publikacją na claude.ai/Skills API).
8. Ewaluacja (wymaga modelu): `claude plugin eval init`, potem `claude plugin eval .`
   — porównanie z wtyczką i bez (Δ), grader `tool_used: Skill` mierzy wyzwalanie
   (szablon: `examples/evals/`).

## Pułapki

- Narzędzie `Skill` **wymaga zgody**: w `dontAsk` bez `Skill` (lub `Skill(nazwa)`) w allow
  model nie wywoła żadnego skilla (próba 2.1.286: odmowa; po allow — „Launching skill”,
  treść w żądaniu). Skill z `disable-model-invocation` nie trafia do listy, a wywołanie
  przez model kończy się błędem z prośbą, by człowiek wpisał `/nazwa`.
- Opis w 1./2. osobie, ogólnikowy („pomaga z dokumentami”) — skill się nie wyzwala lub
  wyzwala za często.
- Za długi rdzeń — każde wywołanie zjada kontekst na resztę sesji; po kompakcji wraca początek.
- `context: fork` przy skillu z samymi wytycznymi — podagent nie dostaje zadania.
- Forkowany skill w tle edytuje poza punktami kontrolnymi (`/rewind` ich nie cofnie).
- `allowed-tools` z repozytorium działa także w `-p` w folderze niezaufanym.
- Plik `manifest.json` w `~/.claude/skills/` przed 2.1.280 przenosił skille do `.trash`.
- Skille synchronizowane z claude.ai ustępują lokalnym o tej samej nazwie.

## Minimalne wersje

| Funkcja | Wersja |
|---|---|
| `${CLAUDE_PROJECT_DIR}` w skillach, `disable-model-invocation` dla zadań cyklicznych | 2.1.196 |
| łączenie kilku `/skill` w jednej wiadomości, `skillOverrides: off` ukrywa w SDK | 2.1.199 |
| wartości logiczne `yes/no/on/off/1/0`, `background` dla `context: fork` | 2.1.218 |
| `claude plugin validate` dla katalogu skilli | 2.1.233 |
| `/skill-doctor` | 2.1.252 |
| `/add-dir` podkatalogu ładuje jego skille | 2.1.257 |
| `claude plugin eval` | 2.1.269 |
| skille głównego checkoutu w worktree bez `.claude/skills` | 2.1.277 |

## Szablony (sprawdzone `sprawdz_skill.py` i `claude plugin validate`)

- `examples/` — kompletna przykładowa wtyczka `narzedzia-wydania` (`.claude-plugin/plugin.json`,
  `skills/`, `evals/`), gotowa do uruchomienia `claude plugin eval skills/budowa-skilli/examples`.
- `examples/skills/przeglad-migracji/` — pełny pakiet uczący (SKILL.md, references, scripts, examples).
- `examples/skills/polecenie-wdrozenia/SKILL.md` — skill tylko dla człowieka z `allowed-tools` i wstrzykiwaniem.
- `examples/widocznosc-skilli.user.settings.json` — `skillOverrides`, budżet listy, blokady.
- `examples/evals/` — przypadki `claude plugin eval` dla wyzwalania skilla (`wyzwalanie-migracji`,
  `bez-wyzwalania`); na kliencie 2.1.284 obie zaliczone, Δ dodatnia.

## Referencje

- `references/frontmatter-i-ladowanie.md` — wszystkie pola, nazwy poleceń, miejsca, synchronizacja, cykl życia.
- `references/pisanie-skilli-uczacych.md` — metoda: swoboda, przepływy, pętle sprawdzeń, skrypty, ewaluacja.
