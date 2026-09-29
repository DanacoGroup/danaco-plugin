---
name: kontrola-jakosci
description: >
  Ocena cudzego lub wygenerowanego kodu: przegląd zmiany (diff, rewizja, plik przed
  scaleniem) oraz audyt całego projektu lub witryny zakończony raportem ustaleń z wagami
  i planem naprawy (WCAG, Core Web Vitals, OWASP). Stosuj, gdy pada „przejrzyj ten kod”,
  „zrób code review”, „czy to jest bezpieczne”, „oceń jakość”, „audyt projektu”, „audyt
  strony”, „sprawdź przed scaleniem”, „raport ustaleń”. Ta paczka ocenia i raportuje, nie
  pisze poprawek — samo pisanie kodu należy do `kodowanie`. Maszynowe bramki dyscypliny
  uruchamia `weryfikatory-dyscypliny`, a wizualną kontrolę ekranu przed scaleniem —
  `ui-ux-pro`.
---

# Kontrola jakości

## Kiedy stosować

Stosuj, gdy przedmiotem pracy jest ocena, nie wytwarzanie: przegląd pojedynczej zmiany przed
scaleniem albo audyt całości projektu, repozytorium lub witryny, kończony raportem ustaleń
z wagami i planem naprawy.

Nie stosuj tej paczki do pisania poprawek — to `kodowanie`. Maszynowych bramek dyscypliny nie
uruchamia ta paczka, lecz `weryfikatory-dyscypliny`; wizualnej kontroli ekranu przed
scaleniem — `ui-ux-pro`; kolejności i kosztu weryfikacji w dużym repozytorium —
`praca-w-duzym-repo`.

Rozróżnienie zakresu: przegląd ocenia zmianę, audyt ocenia całość. Przy audycie fragmenty
kodu badaj technikami z modułu przeglądu.

## Procedura

1. **Zawsze najpierw** wczytaj `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` —
   zasady dyscypliny zawodowej, względem których prowadzona jest ocena (historia
   w komentarzach, wymyślone kody, pliki-narośle, język to usterki do wykrywania).
2. Ustal zakres oceny i wczytaj właściwy moduł z tabeli niżej.
3. Uruchom bramki maszynowe, żeby nie wypisywać ręcznie tego, co narzędzie znajdzie samo:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <ścieżki>
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/kontrola-jakosci/scripts/audyt_smieci.py" <katalog>
   ```
4. Wczytaj karty pogłębione według tabeli w pliku głównym modułu.
5. Zapisz ustalenia z wagą (blokująca, poważna, drobna), plikiem i linią oraz z planem
   naprawy. Ustalenie bez ścieżki i bez wagi nie jest ustaleniem.

## Moduły

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Standardy zawodowe | `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` | zawsze — wzorzec, względem którego ocenia się kod |
| Przegląd kodu | `references/przeglad-kodu/przeglad-kodu.md` | ocena ZMIANY: diff, rewizja, plik lub moduł przed scaleniem |
| Audyt jakości | `references/audyt-jakosci/audyt-jakosci.md` | ocena CAŁOŚCI: projekt, repozytorium, witryna — z raportem i planem naprawy |

## Kryteria zakończenia

Ocena jest skończona, gdy zachodzą wszystkie cztery warunki:

- każde ustalenie ma wagę, ścieżkę pliku, numer linii i sprawdzalne uzasadnienie;
- każde ustalenie ma przypisany krok naprawy albo jawne stwierdzenie, że naprawa nie jest
  potrzebna;
- bramki maszynowe zostały uruchomione, a ich wynik jest w raporcie (nie zastępuje oceny,
  ale ją poprzedza);
- zakres oceny jest wypisany wraz z tym, czego nie objęto.

## Narzędzie: audyt_smieci.py

`audyt_smieci.py` znajduje śmieci w repozytorium (cache kompilatorów, pliki tymczasowe, pliki
systemowe, puste katalogi) i zbiera znaczniki TODO/FIXME/XXX/HACK. Domyślnie tryb suchego
przebiegu — tylko listuje.

```bash
AS="${CLAUDE_PLUGIN_ROOT}/skills/kontrola-jakosci/scripts/audyt_smieci.py"

python3 "$AS" <katalog>                 # tylko raport
python3 "$AS" <katalog> --usun          # usuwa znalezione śmieci
python3 "$AS" <katalog> --usun-puste    # usuwa także puste katalogi
python3 "$AS" <katalog> --json          # do wpięcia w CI lub skrypt
```

Nigdy nie rusza zawartości `.git`. Używaj `--usun` świadomie — usunięcie jest nieodwracalne
w tym repozytorium, poza historią git, jeśli plik był śledzony.

## Odwołania między modułami

W treściach modułów odwołania do „skilla X” oznaczają moduł `X` tej paczki. Moduły
`jezyki-programowania`, `budowa-kodu`, `debugowanie` i `bazy-danych` należą do paczki
`kodowanie`; `praktyki-produktowe` i `architektura` — do paczki
`architektura-i-dokumentacja`. Gdy ocena wymaga ich treści, stosuj zasady ogólne ze
standardów zawodowych oraz sygnatury językowe z karty
`references/przeglad-kodu/przeglad-wg-jezykow.md`, a właścicielowi projektu wskaż właściwą
paczkę dla prac naprawczych.

## Materiały

- `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` — wzorzec oceny
- `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` — kontrola końcowa pracy
- `../../wspolne/standardy-zawodowe/katalog-antywzorcow.md` — antywzorce do wykrywania
- `references/przeglad-kodu/przeglad-kodu.md` — technika przeglądu zmiany
- `references/audyt-jakosci/audyt-jakosci.md` — technika audytu całości i kształt raportu
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrola-jakosci/scripts/audyt_smieci.py` — audyt porządku
  repozytorium

## Rozgraniczenie z paczkami sąsiednimi

- `kodowanie` — pisanie poprawek wynikających z ustaleń.
- `weryfikatory-dyscypliny` — uruchamianie i strojenie bramek maszynowych.
- `ui-ux-pro` — dostępność i wygląd budowanego komponentu, kontrola wizualna zrzutem ekranu.
- `praca-w-duzym-repo` — kolejność i koszt weryfikacji.
- `architektura-i-dokumentacja` — ocena struktury i architektury projektu.
