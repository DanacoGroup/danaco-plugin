# Role, protokół międzymodelowy i kolejka

## Spis treści

1. [Zakresy ról](#zakresy-ról)
2. [Protokół międzymodelowy](#protokół-międzymodelowy)
3. [Rozmiar zadania](#rozmiar-zadania)
4. [Kolejka](#kolejka)
5. [Przestrzeń robocza i przenoszenie wyniku](#przestrzeń-robocza-i-przenoszenie-wyniku)

## Zakresy ról

Podział ról działa tylko wtedy, gdy każda rola ma **wąski zakres i wyraźny zakaz**. Rola bez
zakazu rozlewa się na sąsiednie i po kilku rundach cztery modele robią to samo, tylko drożej.

**Koordynator.** Dzieli cel na zadania, prowadzi kolejkę, pilnuje warunków stopu, prowadzi
bramkę akceptacji. *Nie wykonuje pracy i nie ocenia jej jakości.* Koordynator, który zaczyna
poprawiać kod, przestaje pilnować pętli — a to jedyna rola, która ma widok całości.

**Badacz.** Zbiera materiał: mapa repozytorium, kontrakt, sąsiednie moduły, istniejące wzorce.
*Oddaje materiał, nie wnioski.* Badacz formułujący rekomendacje wyręcza koordynatora, a jego
wnioski nie przechodzą przez żadną kontrolę.

**Wykonawca.** Wytwarza kod i testy dla jednego zadania. *Pisze wyłącznie do własnej przestrzeni
roboczej.* Nie decyduje, czy zadanie było dobrze postawione — to zadanie koordynatora.

**Kontroler.** Ocenia wynik jednego zadania. *Dostaje sam wynik, bez uzasadnienia wykonawcy.*
Nie proponuje poprawki — zwraca werdykt i uwagi. Kontroler proponujący własne rozwiązanie
staje się drugim wykonawcą, a jego kontrola znika.

## Protokół międzymodelowy

Modele nie rozmawiają ze sobą swobodnie. Wymieniają się **komunikatami o ustalonym kształcie**,
przechodzącymi przez koordynatora i przez kolejkę.

Rozmowa swobodna między modelami wygląda atrakcyjnie i ma dwie wady, które w pętli całodobowej
są rozstrzygające: nie da się jej ograniczyć budżetem (bo nie wiadomo, kiedy się kończy) i nie da
się jej odtworzyć przy diagnozie.

Kształt komunikatu zadania:

```json
{
  "id": "zad-0142",
  "rola": "builder",
  "opis": "Dodaj walidację terminu przedawnienia w kancelaria.egzekucje",
  "kontekst": ["shared/contract.json", "server/internal/sprawy/"],
  "kryteriaPrzyjecia": ["test regresyjny odtwarza scenariusz", "task go:test przechodzi"],
  "budzetTokenow": 300000,
  "proba": 1
}
```

Kształt werdyktu kontroli:

```json
{
  "zadanie": "zad-0142",
  "przyjete": false,
  "uwagi": "Brak przypadku brzegowego: termin przypadający na dzień wolny.",
  "zuzyteTokeny": 41200
}
```

Dwie rzeczy warte podkreślenia. Po pierwsze, `kontekst` to **lista odwołań**, nie treść —
identyfikatory i ścieżki, nie zawartość akt. Po drugie, `kryteriaPrzyjecia` są formułowane
przy tworzeniu zadania, a nie po jego wykonaniu. Kryteria dopisane po fakcie zawsze pasują
do tego, co powstało.

## Rozmiar zadania

Najwyżej jeden pakiet, jedna zmiana, jeden test. Zadanie większe:

- nie da się skontrolować — kontroler dostaje diff, którego nie obejmie oceną
- nie da się cofnąć — odrzucenie oznacza wyrzucenie kilku godzin pracy
- nie da się rozliczyć z budżetu — nie wiadomo, która część go zjadła

Sygnał, że zadanie jest za duże: opis zawiera „oraz” albo „a następnie”. Wtedy są to dwa zadania.

## Kolejka

Kolejka ma twarde ograniczenia, bo koordynator, który przy każdym niepowodzeniu dokłada zadania,
potrafi rozbudowywać ją szybciej, niż wykonawca ją opróżnia.

| Ograniczenie | Po co |
|---|---|
| `maxDepth` | kolejka bez ograniczenia rośnie do wyczerpania pamięci, a rosnąca kolejka wygląda jak postęp |
| `maxRetries` | zadanie zawodzące zawsze będzie ponawiane zawsze |
| budżet na zadanie | jedno źle postawione zadanie nie może zjeść budżetu roli |

Zadanie, które wyczerpało `maxRetries`, **nie znika** — trafia do listy zadań odłożonych,
a licznik braku postępu rośnie. Ciche porzucanie zadań sprawia, że pętla kończy pracę „bez
zadań w kolejce” mimo niewykonanego celu.

## Przestrzeń robocza i przenoszenie wyniku

Wykonawca pisze do własnej przestrzeni roboczej — nie do przestrzeni trybu. Przeniesienie wyniku
dalej jest osobną, jawną operacją, wykonywaną dopiero po przyjęciu przez kontrolera.

Wynikają z tego trzy rzeczy:

- odrzucona zmiana nie zostawia śladu w stanie właściwym
- kontroler ocenia dokładnie to, co ma zostać przeniesione
- przeniesienie przechodzi przez `CanWrite` z macierzy trybów, tak samo jak zapis przez człowieka

W praktyce oznacza to gałąź git na zadanie albo katalog roboczy na zadanie. Przy pętli
całodobowej gałąź jest wygodniejsza: daje historię, cofnięcie i naturalny punkt scalenia.
