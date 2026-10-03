---
description: Audyt konfiguracji Claude Code konta i projektu względem dobrych praktyk — zbiera dowody narzędziami wtyczki i kończy się raportem z priorytetami poprawek
argument-hint: "[katalog-projektu] [profil: stanowisko|ci|usluga]"
allowed-tools: Bash(python3 *), Read, Grep, Glob
---

# Audyt konfiguracji Claude Code

Przeprowadź audyt konfiguracji Claude Code dla projektu `$1` (gdy pusty — bieżący katalog)
w profilu `$2` (gdy pusty — `stanowisko`). Pracuj **tylko w trybie odczytu**: nie zmieniaj
żadnego pliku konfiguracji, nie wypisuj wartości sekretów (nazwy zmiennych wystarczą).

## Krok 1 — zbierz dowody

Uruchom (jeden raz):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audyt_konfiguracji.py" --projekt "<katalog>" --profil "<profil>" --cli "$(command -v claude)"
```

Skrypt wypisze katalog wyników (`podsumowanie.json` i pliki `*.txt` per obszar,
`lista-kontrolna.md`, `diagnostyka/diagnostyka.md`). Gdy `claude` nie jest w PATH, pomiń `--cli`.

## Krok 2 — przeanalizuj

Gdy dostępny jest podagent `audytor-konfiguracji`, przekaż mu ścieżkę katalogu wyników,
katalog projektu i profil — zwróci gotowy raport. W przeciwnym razie zrób analizę sam:

1. Przeczytaj `podsumowanie.json`, potem pliki obszarów z błędami i ostrzeżeniami.
2. Każde znalezisko odnieś do skilla tej wtyczki, który opisuje poprawne rozwiązanie
   (`ustawienia-i-hierarchia`, `uprawnienia-i-tryby`, `piaskownica-i-izolacja`, `hooki`,
   `serwery-mcp`, `podagenci-i-zespoly`, `budowa-skilli`, `wtyczki-i-marketplace`,
   `instrukcja-systemowa-i-pamiec`, `headless-i-osadzanie`, `model-cache-i-koszty`,
   `zmienne-srodowiskowe`, `zarzadzanie-flota`, `diagnostyka`, `bezpieczenstwo-wdrozenia`)
   i przeczytaj jego sekcję „Pułapki” lub referencję, zanim zaproponujesz poprawkę.
3. Odróżnij błędy pewne (walidator, `claude doctor`, lista kontrolna BRAK) od zaleceń.
4. Dla każdej poprawki podaj gotowy fragment konfiguracji (JSON / flaga / zmienna)
   i sposób sprawdzenia (`waliduj_ustawienia.py … --cli claude`, `proba_cli.py`, `/status`).

## Krok 3 — raport

Zwróć raport w tej strukturze:

```
# Audyt konfiguracji Claude Code — <projekt>, profil <profil>, <data>

## Podsumowanie
<3–5 zdań: stan ogólny, liczba problemów krytycznych/ważnych/drobnych, najważniejsze ryzyko>

## Problemy krytyczne (bezpieczeństwo, utrata danych, konfiguracja odrzucana przez CLI)
| # | Obszar | Problem | Dowód (plik wyników) | Poprawka | Weryfikacja |

## Problemy ważne (działanie niezgodne z intencją, koszty, izolacja)
| … jak wyżej … |

## Zalecenia (dobre praktyki, porządek)
| … jak wyżej … |

## Co jest w porządku
<krótka lista mocnych stron>

## Czego audyt nie sprawdził
<np. polityki zarządzanej na innych maszynach, zachowania modelu, serwerów MCP bez --polacz>

Katalog dowodów: <ścieżka>
```

Priorytety: krytyczne — sekret w pliku ustawień, `bypassPermissions` bez izolacji, brak deny
dla sekretów w CI/usłudze, plik ustawień odrzucany przez CLI, hooki/serwery z niezaufanych
źródeł; ważne — reguły niedziałające (goła `Edit`, `$ZMIENNA`, matcher hooka), tryb wymuszony
przez SCRUB, brak izolacji dzierżawców, cache/koszty; zalecenia — reszta.
