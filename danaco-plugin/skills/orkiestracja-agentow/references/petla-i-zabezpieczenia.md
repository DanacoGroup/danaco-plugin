# Pętla wykonawcza i jej zabezpieczenia

## Bieg jednej rundy

```
koordynator planuje  ->  kolejka zadań
   -> dla każdego zadania:  wykonawca wytwarza  ->  kontroler ocenia
   -> zadania przyjęte przenoszone do przestrzeni trybu
   -> kolejka pusta?  ->  bramka akceptacji  ->  koniec albo kolejna runda
```

Runda kończy się zawsze jednym z dwóch: przyjęciem przynajmniej jednego zadania (postęp)
albo brakiem takiego przyjęcia (licznik braku postępu rośnie). Trzeciej możliwości nie ma —
i to jest cała mechanika wykrywania krążenia.

## Cztery sposoby, w jakie pętla zawodzi

| Sposób | Jak wygląda od środka | Co go wykrywa |
|---|---|---|
| krążenie | normalna praca, kolejne rundy | licznik `noProgress` |
| uzgodniona pomyłka | wszyscy się zgadzają, wynik jest zły | izolowany kontroler + bramka akceptacji |
| źle postawione zadanie | wykonawca pracuje pilnie w złą stronę | budżet roli i budżet całkowity |
| fałszywe zakończenie | koordynator uznaje pracę za skończoną | bramka akceptacji sprawdzalna maszynowo |

Warto zauważyć, że **żaden z tych czterech przypadków nie jest awarią**. Nic się nie wywraca,
nic nie zgłasza błędu. Dlatego zabezpieczenia muszą być czynne — liczniki i bramki — a nie
polegać na obsłudze wyjątków.

## Bramka akceptacji jako wyrocznia

```bash
task gen:check     # contract:check + modes:check (z modes:validate) + channel:check
task tauri:check
task go:build
task go:vet
task go:test
task client:types
task client:test
task standard
```

Wszystkie muszą przejść. Częściowe przejście nie jest przejściem.

To jest miejsce, w którym cała reszta warsztatu opłaca się najbardziej: strażnik kontraktu,
macierz trybów, testy i bramki domowe stają się wyrocznią, której model nie przekona.
Rozbudowa testów nie jest pracą poboczną względem orkiestracji — jest warunkiem tego, żeby
orkiestracja mogła w ogóle działać bez człowieka.

Odwrotnie: pętla puszczona na repozytorium bez testów nie jest autonomiczna, tylko niepilnowana.
Jeśli bramka akceptacji sprowadza się do „kompiluje się”, pętla wyprodukuje kod, który się
kompiluje — i nic ponadto.

## Eskalacja

Eskalacja to nie zatrzymanie. To przekazanie decyzji człowiekowi wraz z materiałem, który
pozwoli ją podjąć:

- ostatnie zadanie i jego historia prób
- próg, który został przekroczony
- wynik ostatniej bramki akceptacji wraz z tym, co dokładnie zawiodło
- zużycie budżetu w rozbiciu na role

Eskalacja bez tego materiału zamienia się w powiadomienie „coś poszło nie tak”, po którym i tak
trzeba odtworzyć całą sytuację od zera.

## Wyłącznik awaryjny

Sygnał sprawdzany na początku każdej rundy. Trzy wymagania:

- **działa bez konsoli** — pętla pracuje w nocy, a osoba zatrzymująca może mieć tylko telefon
- **zatrzymuje po bieżącym zadaniu**, nie w jego środku — przerwanie w połowie zapisu zostawia
  przestrzeń roboczą w stanie pośrednim
- **zapisuje stan** — zatrzymana pętla ma dać się wznowić, a nie zacząć od nowa

Zabicie procesu nie jest wyłącznikiem: zabiera cały stan, którego potem brakuje przy diagnozie.

## Diagnoza pętli

| Objaw | Pierwszy trop |
|---|---|
| pętla działa, nic nie przybywa | brak bramki kontroli w cyklu; sprawdź `workflow_tool.py validate` |
| kontroler przyjmuje wszystko | kontroler nie jest izolowany albo widzi uzasadnienie wykonawcy |
| budżet znika szybciej, niż powinien | zadania za duże; sprawdź rozkład zużycia na role |
| pętla kończy „bez zadań”, cel niewykonany | zadania po `maxRetries` porzucane cicho zamiast odkładane |
| pamięć rośnie, pętla zwalnia | brak `ContinueAsNew`; historia przepływu przerosła rozsądny rozmiar |
| nie da się odtworzyć, co się stało | użyto `time.Now()` zamiast `workflow.Now`; przepływ przestał być deterministyczny |
| nie wiadomo, który model wprowadził zmianę | dziennik nie jest dopisywany albo nie zapisuje roli i modelu |

## Uruchamianie pierwszej pętli

Nie zaczynaj od celu na trzy dni. Kolejność, która pozwala zobaczyć problemy, zanim staną się
drogie:

1. **Jedna runda, jedno zadanie, człowiek patrzy.** Sprawdź, czy kontroler faktycznie odrzuca
   złą pracę — podrzuć mu celowo wadliwy wynik.
2. **Kilka rund z niskim budżetem.** Sprawdź, czy licznik braku postępu zadziała; ustaw próg
   na 2 i zobacz eskalację.
3. **Pełna bramka akceptacji na małym zadaniu.** Sprawdź, czy pętla naprawdę kończy się dopiero
   po przejściu wszystkich poleceń.
4. **Dopiero teraz doba pracy.**

Pominięcie kroku pierwszego jest najczęstszym błędem: pętla z kontrolerem, który przyjmuje
wszystko, wygląda przez pierwsze godziny znakomicie.
