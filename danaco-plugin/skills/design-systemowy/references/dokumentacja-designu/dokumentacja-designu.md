# Dokumentacja designu — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`: jedno źródło
prawdy, zamknięty zbiór dokumentów, profesjonalny język) i `praktyki-produktowe` (style wyłącznie we
właściwych plikach). Opracowania projektowe podlegają tej samej dyscyplinie co kod: jeden dokument
kanoniczny na temat, spójna terminologia, wersjonowanie w Git.

## Karty referencyjne

| Obszar | Karta | Wczytaj gdy |
| --- | --- | --- |
| Tokeny projektowe | `references/dokumentacja-designu/design-tokens.md` | definiowanie kolorów, typografii, odstępów, cieni; plik tokenów jako źródło prawdy; powiązanie tokenów z CSS |
| Standard stylów CSS | `references/dokumentacja-designu/standard-css.md` | organizacja arkuszy, konwencje nazw klas, architektura CSS, zmienne, tryby jasny/ciemny |
| System projektowy i zasady | `references/dokumentacja-designu/system-projektowy.md` | księga projektowa (design book), zasady i polityka designu, biblioteka komponentów, stany interakcji, dostępność |
| Identyfikacja wizualna | `references/dokumentacja-designu/identyfikacja-wizualna.md` | księga znaku, logo i pole ochronne, paleta marki, typografia firmowa, zastosowania CI |
| Opracowania UI/UX | `references/dokumentacja-designu/opracowania-ui-ux.md` | dokumentowanie przepływów użytkownika, makiet, badań, decyzji projektowych UX |
| Projektowanie banerów | `references/dokumentacja-designu/banner-design.md` | banery reklamowe i firmowe: formaty, hierarchia, typografia, wezwanie do działania, eksport |

Wczytaj kartę obszaru, którego dotyczy praca; przy budowie pełnego systemu
projektowego zacznij od tokenów, potem standard CSS, potem system projektowy.

## Zasady nadrzędne

1. **Hierarchia źródeł prawdy:** identyfikacja wizualna (marka) → tokeny projektowe → standard CSS →
   komponenty. Wartość niższego szczebla zawsze wynika z wyższego; kolor wpisany wprost w
   komponencie z pominięciem tokenu to usterka (zasada stylów ze
   `../architektura-i-dokumentacja/references/praktyki-produktowe/praktyki-produktowe.md`).
2. **Nazwy tokenów i komponentów są terminologią projektu** — obowiązują
   w plikach projektowych, kodzie i dokumentacji jednakowo (zasada 3 standardów);
   wprowadzenie synonimu („primary” tu, „brand” tam) to dryf.
3. **Opracowanie projektowe opisuje decyzje i reguły, nie historię prac.**
   Warianty odrzucone dokumentuje się tylko jako uzasadnienie decyzji (jak ADR
   w `../architektura-i-dokumentacja/references/architektura/architektura.md`), nie jako kronikę.
4. **Każda reguła z przykładem poprawnym i błędnym.** Zasada bez pary
   „tak / nie” jest niewykonalna dla kolejnego wykonawcy.
5. **Dostępność jest częścią standardu, nie dodatkiem:** kontrasty według
   WCAG 2.2 AA sprawdzone narzędziowo na parach kolorów z tokenów, rozmiary
   dotykowe, widoczne stany fokusu — zapisane w systemie projektowym.
