---
name: orkiestracja-agentow
description: >
  Autonomiczna orkiestracja czterech modeli AI w Danaco Console: role (koordynator, badacz,
  wykonawca, kontroler), kolejka zadań, protokół międzymodelowy, pętla działająca dobami bez
  człowieka, warunki stopu, budżety na rolę, bramki akceptacji sprawdzalne maszynowo,
  trwałość na Temporalu, dziennik audytowy i wyłącznik awaryjny. Stosuj, gdy projektowany
  jest przepływ z udziałem wielu modeli, gdy powstaje definicja pętli, gdy przydzielane są
  role i budżety, a także gdy pada „pętla się kręci i nic nie robi”, „modele zgadzają się ze
  sobą, a wynik jest zły”, „skąd wiadomo, że skończyła”, „ile to będzie kosztować”, „jak to
  zatrzymać” albo „praca 24/7 bez człowieka”. Widoczność danych dla toru AI rozstrzyga
  `macierz-trybow-sesji`; ciągła praca jednego modelu na czacie to polecenie `/praca` pluginu
  `danaco-praca`, jeśli jest zainstalowany, nie ta paczka.
---

# Orkiestracja czterech modeli

## Kiedy stosować

Stosuj, gdy projektujesz albo zmieniasz przepływ z udziałem wielu modeli w produkcie:
definicję pętli w `workflows/*.json`, przydział ról, budżety, warunki stopu, bramkę
akceptacji. Stosuj też przy diagnozie pętli, która utknęła albo przepaliła budżet.

Nie stosuj tej paczki do włączenia trybu ciągłej pracy jednego modelu w bieżącej sesji
czatu — to paczka `pracuj` pluginu `danaco-praca`, jeśli jest zainstalowany. Tego, co dany
tor AI widzi i gdzie zapisuje, nie rozstrzyga ta paczka,
lecz `macierz-trybow-sesji`; przepływu zdarzeń toru przez kanał — `kanal-websocket`.

Zasada nadrzędna: uruchomienie czterech modeli, które przekazują sobie zadania, jest łatwe.
Trudne jest to, że pętla ma pracować dobami bez człowieka, więc **każdy sposób, w jaki pętla
może zawieść, musi mieć odpowiadający mu warunek zatrzymania**. Pętla krążąca od trzech
godzin, modele uzgadniające niedziałające rozwiązanie, źle postawione zadanie i koordynator
uznający pracę za skończoną wyglądają od środka jak normalna praca.

## Cztery role

| Rola | Zadanie | Izolacja | Uwaga |
|---|---|---|---|
| `coordinator` | dzieli cel na zadania, prowadzi kolejkę, pilnuje warunków stopu | `hybrid` | nie wykonuje pracy i nie ocenia jej jakości |
| `researcher` | zbiera kontekst: mapa repozytorium, kontrakt, sąsiednie moduły | `hybrid` | oddaje materiał, nie wnioski |
| `builder` | wytwarza kod i testy | `hybrid` | pisze do własnej przestrzeni roboczej |
| `reviewer` | ocenia wynik | **`isolated`** | dostaje sam wynik, bez uzasadnienia wykonawcy |

Dwie reguły dotyczące kontrolera są jedynymi bez wyjątku — walidator odrzuca przepływ, który
je łamie:

**Kontroler musi być izolowany.** Model, który widzi rozumowanie wykonawcy, potwierdza je
znacznie chętniej, niż gdy dostaje sam wynik. Cztery modele zgadzające się ze sobą, bo widzą
nawzajem swoje uzasadnienia, dają złudzenie kontroli przy jej faktycznym braku.

**Kontroler musi być innym modelem niż wykonawca.** Model oceniający własną pracę nie jest
kontrolą, niezależnie od tego, jak jest o to poproszony.

## Procedura: definicja przepływu i jej kontrola

Pętla jest opisana danymi w `workflows/*.json`, a nie kodem. Przed uruchomieniem przechodzi
przez walidator, który **odmawia** startu, gdy brakuje zabezpieczenia.

1. Skopiuj narzędzie do repozytorium (raz):
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/orkiestracja-agentow/scripts/workflow_tool.py" tools/
   ```
2. Zbuduj definicję na wzorze `assets/przeplyw-przykladowy.json`.
3. Zwaliduj i wygeneruj opis:
   ```bash
   python3 tools/workflow_tool.py validate workflows/budowa-modulu.json --root .
   python3 tools/workflow_tool.py report   workflows/budowa-modulu.json --root . \
     --out PRZEPLYW.md
   ```
4. Uzupełnij braki wskazane przez walidator i powtórz krok 3, dopóki nie zwróci zera.

Walidator odrzuca przepływ, w którym:

- **jakikolwiek cykl kroków nie zawiera bramki kontroli** (`gate: true`) — pętla bez bramki
  krąży w nieskończoność, a przy pracy bez człowieka nie ma kto tego zauważyć
- krok końcowy nie ma listy `acceptance` — pętla kończąca się na opinii koordynatora nie ma
  warunku końca, tylko opinię
- kontroler nie jest izolowany albo używa tego samego modelu co wykonawca
- brakuje warunku stopu na wyczerpanie budżetu albo brak postępu
- brakuje ograniczenia czasu (`wallClockHours`) — praca bez człowieka potrzebuje twardego
  końca także w czasie, nie tylko w tokenach
- kolejka nie ma dodatniego `maxDepth` albo `maxRetries`
- brakuje budżetu na zadanie (`budget.perTaskTokens`) albo przekracza on budżet którejś roli
- `audit.appendOnly` nie jest ustawione
- rola ma słabszą izolację niż tryb sesyjny albo przepływ używa więcej torów, niż tryb
  dopuszcza
- któryś krok jest nieosiągalny, nie jest końcowy i nigdzie nie prowadzi, albo jest końcowy
  i jednocześnie prowadzi dalej
- `onReject` stoi przy kroku, który nie jest bramką — nie ma kto odrzucać

Gdy pierwszy krok leży w cyklu (zawrót po odrzuceniu prowadzi do niego z powrotem), wskaż
początek jawnie polem `start` — inaczej każdy krok ma poprzednika i nie da się wyznaczyć
wejścia.

## Bramka akceptacji

To jedyne miejsce, które kończy pętlę sukcesem. Zawiera **polecenia sprawdzalne maszynowo**,
nie ocenę:

```json
"acceptance": [
  "task gen:check",
  "task tauri:check",
  "task go:build",
  "task go:vet",
  "task go:test",
  "task client:types",
  "task client:test",
  "task standard"
]
```

Wszystkie osiem celów istnieje we wspólnym pliku
`${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml`. `task gen:check` obejmuje
`contract:check`, `modes:check` (wraz z `modes:validate`) i `channel:check` — jedno polecenie
zamiast czterech, które łatwo rozjeżdżają się z Taskfile'em. `task standard` jest wrapperem
na `${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py verify`, czyli na bramki dyscypliny i nazewnictwa.

Tu jest sedno konstrukcji: **drabina weryfikacji jest wyrocznią pętli**. Modele mogą się
mylić, przekonywać nawzajem i być bardzo pewne swojego — kompilator, testy i bramki domowe
nie. Pętla, która nie ma takiej wyroczni, nie jest autonomiczna, tylko niepilnowana. Dlatego
rozbudowa testów i bramek to warunek działania orkiestracji, nie praca poboczna.

## Warunki stopu

Cztery, i wszystkie cztery walidator wymaga jawnie — każdy odpowiada innemu sposobowi,
w jaki pętla zawodzi:

| Warunek | Kiedy | Działanie |
|---|---|---|
| `acceptancePassed` | bramka akceptacji przeszła w całości | `finish` (jedyne zakończenie powodzeniem) |
| `budgetExhausted` | zużycie tokenów sięgnęło limitu | `halt` albo `escalate`, nigdy `finish` |
| `wallClockExceeded` | minął zadeklarowany czas | `halt` albo `escalate`, nigdy `finish` |
| `noProgress` | N rund bez przyjętego zadania (`threshold`) | `escalate` do człowieka |

`finish` przy wyczerpanym budżecie albo przekroczonym czasie udaje powodzenie — pętla zgłasza
sukces, mimo że celu nie osiągnęła. Walidator to odrzuca.

`noProgress` jest najważniejszy i najczęściej pomijany. Wyczerpanie budżetu zauważy każdy;
pętla, która przez sześć godzin poprawia to samo miejsce, mieszcząc się w budżecie, jest
w praktyce niewidoczna. Eskalacja musi mieć adresata (`escalation`) — eskalacja donikąd jest
tym samym co jej brak.

## Budżety

Budżet ustawiaj **na rolę**, nie na przepływ. Budżet wspólny pozwala jednemu torowi zjeść
cały przydział i zagłodzić pozostałe trzy; zwykle robi to wykonawca, bo produkuje najwięcej
tekstu. Budżet jest twardy: po wyczerpaniu tor kończy się `E_BUDGET_EXCEEDED`, bez prośby
o zwiększenie i bez cichego kontynuowania.

### Budżet czasu jednego zlecenia podagenta

Budżet liczony w tokenach nie chroni kanału rozmowy z człowiekiem. Wiadomość użytkownika
wpisana w trakcie tury dochodzi wraz z wynikiem najbliższego wywołania narzędzia, więc
zlecenie podagenta trwające kilkadziesiąt minut zamyka ten kanał na cały swój czas.
Dlatego każde zlecenie ma osobny budżet czasu, niezależny od budżetu tokenów, a blok
zleceń równoległych dzieli się na partie tak, żeby przerwa między kolejnymi wywołaniami
koordynatora nie przekraczała kilku minut. Zlecenie, które przekroczy budżet czasu,
przerywa się i wraca z tym, co ma — częściowy wynik oddany w terminie jest wart więcej niż
pełny wynik oddany po godzinie ciszy. Reguła prowadzenia rozmowy w trakcie długiej tury
leży w paczce `pracuj` pluginu `danaco-praca`, jeśli jest zainstalowany, rozdział
„Wiadomość użytkownika w trakcie tury”.

## Trwałość: Temporal

Pętla ma pracować dobami, więc restart rdzenia, awaria zasilania albo wdrożenie nowej wersji
nie mogą oznaczać zaczynania od początku. Temporal daje to bez pisania własnego mechanizmu
wznowień, a jego historia przepływu jest jednocześnie dziennikiem audytowym.

Szkielet pętli, skompilowany i gotowy do rozbudowy: `assets/execution_loop.go`. `Spec.Validate`
w tym pliku powtarza progi sprawdzane przez walidator — przepływ bywa uruchamiany
z pominięciem `workflow_tool.py`, a brakujący próg to nie „brak ograniczenia”, tylko próg
zero.

Trzy rzeczy do zrobienia dobrze od początku:

- **`ContinueAsNew` co N rund.** Historia przepływu rośnie z każdą rundą; pętla działająca
  dobami bez tego przewraca się o własny rozmiar.
- **Kanał sygnału jako wyłącznik awaryjny**, sprawdzany na początku każdej rundy i po każdym
  zadaniu — zatrzymuje wtedy po bieżącym zadaniu, nie w jego środku. Przed `ContinueAsNew`
  kanał trzeba opróżnić: sygnał, który nadszedł tuż przed przejściem, przepadłby razem
  z historią.
- **Determinizm przepływu.** Czas bierz z `workflow.Now`, losowość z `workflow.SideEffect`.
  Zwykłe `time.Now()` psuje odtwarzalność, a odtwarzalność jest jedynym punktem zaczepienia
  przy diagnozie tego, co pętla zrobiła w nocy.

## Dziennik audytowy

Dopisywany, nigdy nadpisywany. Dla każdego zadania: rola, model, zużycie tokenów, wynik
bramki, zmienione pliki. Bez tego po tygodniu pracy pętli nie da się odpowiedzieć na pytanie
„który model wprowadził tę zmianę i dlaczego została przyjęta”. W systemie pracującym na
danych objętych tajemnicą zawodową odpowiedź „nie wiadomo” nie jest dopuszczalna. Dziennik
nie zawiera treści danych sprawy — identyfikatory techniczne, nazwy plików, liczby.

## Kryteria zakończenia

Przepływ jest gotowy do uruchomienia, gdy zachodzą wszystkie cztery warunki:

- `workflow_tool.py validate` zwraca zero na docelowej definicji;
- lista `acceptance` kroku końcowego składa się wyłącznie z poleceń sprawdzalnych maszynowo,
  a każde z nich istnieje w Taskfile'u repozytorium;
- wszystkie cztery warunki stopu są zadeklarowane, a `escalate` ma adresata;
- wyłącznik awaryjny jest podłączony i sprawdzany na początku każdej rundy.

Pętla kończy się powodzeniem wyłącznie przez `acceptancePassed`. Żadna ocena modelu nie jest
zakończeniem.

## Częste pułapki

- **Pętla bez bramki kontroli.** Krąży, aż skończy się budżet, i wygląda przy tym na zajętą.
- **Kontroler widzący rozumowanie wykonawcy.** Przyjmuje prawie wszystko; kontrola jest
  pozorna.
- **Kontroler tym samym modelem co wykonawca.** To samo, tylko trudniej zauważyć.
- **Koniec na opinii koordynatora.** „Uważam, że zadanie wykonane” nie jest warunkiem końca.
- **Zadania zbyt duże.** Zadanie obejmujące kilka pakietów naraz nie da się ani
  skontrolować, ani cofnąć. Rozmiar zadania: najwyżej jeden pakiet, jedna zmiana, jeden test.
- **Brak licznika braku postępu.** Najdroższy sposób na zmarnowanie doby pracy.
- **Kolejka bez ograniczenia.** Koordynator, który przy każdym niepowodzeniu dokłada zadania,
  potrafi rozbudować kolejkę szybciej, niż wykonawca ją opróżnia.
- **Ponawianie bez limitu.** Zadanie, które wyczerpało `maxRetries`, trafia do listy
  odłożonych (`State.Deferred` w szkielecie pętli), a nie znika po cichu.
- **`finish` przy wyczerpanym budżecie.** Pętla zgłasza wtedy sukces, którego nie osiągnęła.
- **Pętla bez wyłącznika.** Jedynym sposobem zatrzymania zostaje zabicie procesu, razem
  z całym stanem, którego potem brakuje przy diagnozie.
- **Modele piszące bezpośrednio do przestrzeni trybu.** Wynik wykonawcy trafia do przestrzeni
  roboczej; przeniesienie go dalej jest osobną, jawną operacją po przejściu kontroli.

## Materiały

- `references/role-i-protokol.md` — zakresy ról, protokół międzymodelowy, kolejka, rozmiar
  zadania
- `references/petla-i-zabezpieczenia.md` — warunki stopu, eskalacja, budżety, wyłącznik,
  diagnoza
- `assets/przeplyw-przykladowy.json` — kompletna definicja przepływu przechodząca walidację
- `assets/execution_loop.go` — szkielet pętli w Temporalu, skompilowany
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — wspólne cele, w tym `flow:check`
  i `standard`

## Rozgraniczenie z paczkami sąsiednimi

- `macierz-trybow-sesji` — co tor AI widzi i gdzie zapisuje, izolacja toru wobec trybu.
- `kanal-websocket` — jak przepływają zdarzenia toru: przeplot, `seq`, przeciwciśnienie.
- paczka `pracuj` pluginu `danaco-praca`, jeśli jest zainstalowany — ciągła praca jednego
  modelu na czacie w bieżącej sesji.
- `kontrakt-zrodlo-prawdy` — deklaracja typów i kodów błędów używanych przez pętlę.
