# Pisanie skilli, które uczą umiejętności — metoda

Źródła: `pl:agents-and-tools/agent-skills/best-practices`, `pl:agents-and-tools/agent-skills/overview`,
`anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills`,
`cc:skills` („Evaluate and iterate”), `cc:plugin-evals`. Wzorzec w tej wtyczce:
każdy z 15 pakietów `skills/*` ma rdzeń, referencje, skrypty i szablony.

## 1. Zasady

1. **Zwięzłość** — model jest już kompetentny; każdy akapit musi uzasadnić swój koszt.
   Pomijaj wyjaśnienia rzeczy oczywistych, zostaw to, czego model nie wie (fakty tego
   środowiska, wersje, pułapki, decyzje).
2. **Stopień swobody dopasowany do kruchości zadania**:
   - wysoka swoboda (tekst, heurystyki) — gdy wiele dróg jest poprawnych;
   - średnia (pseudokod, szablon z parametrami) — gdy jest wzorzec preferowany;
   - niska (konkretny skrypt, dokładne polecenie) — gdy operacja jest krucha
     (migracja, wdrożenie, format pliku).
3. **Uczenie decyzji, nie wyliczeń** — tabele „sytuacja → wybór → dlaczego”, kolejność
   pierwszeństwa, warunki brzegowe. Pełne listy kluczy i opcji do referencji lub indeksów
   przeszukiwanych skryptem.
4. **Progresywne ujawnianie** — SKILL.md jako spis i ścieżka decyzji; szczegóły w
   `references/` z jasnym „kiedy czytać”; jeden poziom odwołań (unikaj łańcuchów
   plik → plik → plik — model może czytać tylko fragmenty).
5. **Skrypty rozwiązują, nie odsyłają** — obsługują błędy, mają czytelne komunikaty,
   kody wyjścia, opis użycia w docstringu; „magiczne liczby” z uzasadnieniem.
6. **Pętle sprawdzeń** — krok „waliduj → popraw → waliduj” z narzędziem (walidator,
   próba), nie „sprawdź uważnie”.
7. **Weryfikowalne produkty pośrednie** — plan w pliku, walidowany przed wykonaniem
   (np. plik ustawień przed wdrożeniem).
8. **Spójna terminologia** — jedno słowo na jedno pojęcie w całym pakiecie.
9. **Bez informacji z datą ważności** w rdzeniu; zmiany wersji w sekcji „Minimalne
   wersje” lub „Stare wzorce” z numerem wersji.
10. **Nie zakładaj zainstalowanych narzędzi** — podaj, czego skrypt wymaga, i sprawdzaj to.

## 2. Szablon rdzenia SKILL.md (stosowany w tej wtyczce)

```
---
name: <rzeczownik-lub-czynność>
description: >
  <Co obejmuje — kluczowe pojęcia i identyfikatory>. Stosuj, gdy pada „…”, „…”.
  <Czego nie obejmuje — odesłanie do sąsiedniego skilla>.
---
# Tytuł
## Kiedy stosować            — 2–4 zdania, granice z innymi skillami
## Decyzja / wybór           — tabela sytuacja → mechanizm → uwagi
## Model działania / kolejność nadpisywania
## Procedura                 — kroki z poleceniami skryptów
## Pułapki                   — konkretne, z objawem i obejściem; wyniki prób
## Minimalne wersje          — tabela funkcja → wersja
## Szablony                  — pliki examples/ i jak je sprawdzono
## Referencje                — pliki references/ z opisem zawartości
```

## 3. Opis (description) — jak pisać

- trzecia osoba, kluczowe słowa i identyfikatory na początku (lista może uciąć koniec);
- frazy, którymi użytkownik naprawdę prosi („skill się nie uruchamia”, „dodaj serwer MCP”);
- granica: czego skill nie robi i który skill to robi;
- ≤1024 znaki (specyfikacja), łącznie z `when_to_use` ≤1536 (lista Claude Code).

## 4. Szablony w examples/ — reguła jakości

Każdy szablon musi przejść co najmniej jedno sprawdzenie maszynowe, a najlepiej próbę:

| Rodzaj | Sprawdzenie |
|---|---|
| plik ustawień | `waliduj_ustawienia.py --cli` (schemat, dokumentacja, `claude doctor`) |
| `.mcp.json` | `sprawdz_mcp.py --polacz` |
| agent `.md` / `agents.json` | `sprawdz_agenta.py --cli` (`claude plugin validate`) |
| skill | `sprawdz_skill.py --cli` |
| wtyczka, marketplace | `claude plugin validate --strict` |
| hook | `test_hooka.py`, próba w CLI (`proba_cli.py --scenariusz`) |
| flagi i zachowanie | `proba_cli.py` na atrapie API |

Zbiorczo: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sprawdz_przyklady.py"`.

## 5. Ewaluacja

Bez ewaluacji wiesz tylko, że skill się wyzwolił, nie że działa.
1. 3–5 realnych próśb + 2 prośby, które **nie** powinny go wyzwolić.
2. `claude plugin eval init` (Claude pisze przypadki) albo ręcznie `evals/<przypadek>/prompt.md`
   + `graders/*.md` (`tool_used: Skill` z `input_match`, `llm` z kryteriami PASS/FAIL,
   `regex`, `file_exists`, `tool_order`).
3. `claude plugin eval .` — każdy przypadek 3× z wtyczką i 3× bez; Δ > 0 = wtyczka pomaga.
   Pojedyncza próba: `--case <nazwa> --runs 1 --ablation none`; koszt: `--max-cost-usd`.
4. Δ ≈ 0 i niezaliczony `tool_used: Skill` = opis nie trafia w naturalne sformułowania.
5. Iteruj z drugą instancją Claude (pisze/poprawia skill) i trzecią (używa go w świeżej sesji).
   Obserwuj, które pliki czyta, czego nie znajduje, co ignoruje.

Wymaga modelu i ≥2.1.269; przypadki przykładowe: `examples/evals/`.

## 6. Lista kontrolna przed wydaniem

- [ ] opis konkretny, 3. osoba, wyzwalacze, granice;
- [ ] SKILL.md < 500 wierszy, najważniejsze na początku;
- [ ] referencje jednopoziomowe, długie ze spisem treści;
- [ ] skrypty z obsługą błędów i opisem użycia, bez zależności spoza biblioteki standardowej
      (albo z jawnym wymogiem);
- [ ] szablony sprawdzone maszynowo;
- [ ] `sprawdz_skill.py --cli` i `claude plugin validate` bez błędów;
- [ ] ewaluacja na 3+ przypadkach (jeśli dostępny model).
