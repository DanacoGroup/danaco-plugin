# Debugowanie — procedura

Procedura obejmuje przebieg diagnozy w codziennej pracy nad kodem. Rozszerzoną metodę
pomiarową — minimalizację przypadku, połowienie ścieżki, narzędzia systemowe — niesie
`references/engineering-core/07-debug-testy-deploy/references/metoda-debugowania.md`;
sięgaj po nią, gdy ta procedura nie doprowadziła do przyczyny.

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`: przyczyna
źródłowa, weryfikacja zamiast deklaracji, zakaz historii w komentarzach, dyscyplina plików). Ta
procedura opisuje samą procedurę diagnostyczną.

Powód istnienia procedury: naturalny odruch modelu LLM wobec błędu to natychmiastowa
edycja kodu w miejscu wskazanym przez komunikat. To odruch zawodny — komunikat wskazuje
miejsce ujawnienia się błędu, nie miejsce jego powstania. Poprawka wykonana przed
zrozumieniem mechanizmu zwykle maskuje objaw i pozostawia usterkę w kodzie.

## Przebieg: pięć etapów, zawsze w tej kolejności

### Etap 1 — Odtworzenie

Nie naprawiaj błędu, którego nie potrafisz wywołać na żądanie.

- Ustal dokładne warunki wystąpienia: dane wejściowe, środowisko, wersje, kolejność działań.
- Doprowadź do wystąpienia błędu i zachowaj pełny, dosłowny komunikat wraz ze śladem stosu.
- Jeżeli odtworzenie w danym środowisku jest niemożliwe (np. błąd wyłącznie produkcyjny),
  powiedz to wprost i oprzyj diagnozę na dziennikach zdarzeń oraz różnicach między
  środowiskami — nigdy na domysłach przedstawianych jako fakty.

### Etap 2 — Izolacja

Zawęź obszar poszukiwań, zanim postawisz hipotezę.

- Czytaj ślad stosu od miejsca awarii w górę, aż do pierwszej ramki w kodzie projektu.
- Zmniejszaj przypadek testowy: usuwaj dane i kroki tak długo, jak błąd nadal występuje;
  najmniejszy przypadek wywołujący błąd to najcenniejszy materiał diagnostyczny.
- Przy regresji ustal ostatnią rewizję działającą poprawnie (w Git: `git bisect`
  lub przegląd historii zmian) — różnica między rewizjami wyznacza obszar podejrzany.
- Sprawdzaj stan faktyczny, nie wyobrażony: wypisz rzeczywiste wartości zmiennych,
  wykonaj zapytanie na rzeczywistej bazie, obejrzyj rzeczywistą odpowiedź API.

### Etap 3 — Przyczyna źródłowa

Sformułuj hipotezę mechanizmu: „błąd powstaje, ponieważ X prowadzi do Y”.

- Hipotezę potwierdź obserwacją, która może ją obalić (wartość zmiennej, wynik
  zapytania, zawartość dziennika). Hipoteza niepotwierdzona pozostaje domysłem —
  wróć do etapu 2.
- Zadawaj pytanie „dlaczego” aż do warstwy, na którą projekt ma wpływ: pusta wartość
  w polu to objaw; brak walidacji przy zapisie to przyczyna.
- Rozróżniaj: miejsce ujawnienia błędu, miejsce powstania błędu i brakujące
  zabezpieczenie, które pozwoliło błędowi przejść niezauważonym. Naprawa może
  wymagać zmiany w dwóch ostatnich, nigdy tylko w pierwszym.

#### Przykład wzorcowy — wraz z ostrzeżeniem

Objaw: program wyliczający wartość magazynu pada z błędem NULL podczas sumowania
kolumny ilości. Poprawka objawowa, narzucająca się jako pierwsza: pominąć wiersze
z wartością NULL przy liczeniu. Diagnoza prowadzona w górę przepływu danych
ujawnia jednak, skąd NULL się bierze: funkcja usuwania pozycji magazynowej
„zwalnia” wiersz poleceniem `UPDATE ... SET quantity = NULL` zamiast wykonać
`DELETE`. Przyczyna źródłowa: operacja usuwania pozostawia w tabeli wiersz-widmo,
który zatruwa każde kolejne obliczenie — sumowanie jest tylko pierwszą ofiarą.
Naprawa u źródła: poprawić operację usuwania i uporządkować dane zastane;
pominięcie NULL w jednym zapytaniu zostawiłoby usterkę czynną dla wszystkich
pozostałych odbiorców tabeli.

PUŁAPKA — zapamiętaj ją, bo dotyczy wprost sposobu rozumowania modelu: na tym
etapie diagnozy pojawia się pokusa, aby zastany stan danych zracjonalizować jako
celowy — „widocznie wiersz z NULL zachowywany jest dla celów audytu” — i na tej
podstawie uznać poprawkę objawową za właściwą. Taka racjonalizacja bez dowodu
jest błędem diagnostycznym. ZAKAZ: intencję wolno przypisać wyłącznie na
podstawie dowodu — komentarza projektowego, dokumentacji, testu utrwalającego to
zachowanie albo słowa właściciela projektu. Brak dowodu oznacza, że zastany stan
jest usterką do naprawy u źródła, a nie decyzją projektową do respektowania.
Jeżeli dowód istnieje — wskaż go w raporcie; jeżeli nie istnieje — nie wolno go
domniemywać.

### Etap 4 — Naprawa

- Zmień możliwie najmniejszy zakres kodu usuwający przyczynę źródłową.
- Nie dodawaj przy okazji ulepszeń, refaktoryzacji ani „drobnych porządków” —
  to osobne zadania; mieszanie ich z naprawą utrudnia przegląd i ewentualne wycofanie.
- Zakazy z zasady 5 standardów zawodowych (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`)
  obowiązują bezwzględnie: żadnego wyciszania wyjątków, usuwania testów, warunków specjalnych
  maskujących przypadek.
- Jeżeli pełna naprawa wykracza poza zakres zadania, powiedz to właścicielowi projektu
  i zaproponuj zakres — nie wprowadzaj po cichu rozwiązania połowicznego.

### Etap 5 — Weryfikacja

- Wykonaj ponownie dokładnie ten scenariusz, który w etapie 1 wywoływał błąd,
  i przytocz wynik: błąd nie występuje.
- Uruchom istniejące testy projektu; żaden nie może przestać przechodzić.
- Jeżeli projekt ma zestaw testów, dopisz test odtwarzający naprawiony błąd —
  to zabezpieczenie, którego brak pozwolił usterce powstać.
- Usuń wszystkie ślady diagnozy: tymczasowe wypisy, pliki robocze, pomocnicze skrypty.
  W kodzie nie zostaje żaden komentarz opisujący przebieg naprawy.

## Raport końcowy

Diagnozę zakończ zwięzłym raportem w rozmowie (nie w pliku), zawierającym kolejno:
objaw, przyczynę źródłową z mechanizmem powstania, wykonaną zmianę, dowód weryfikacji
(przytoczony wynik uruchomienia), oraz — jeżeli występują — elementy niezweryfikowane
wraz z powodem.

## Narzędzia diagnostyczne właściwe dla technologii

Doboru narzędzi (debugger, profilowanie, analiza dzienników) dokonuj według karty danego języka w
`references/jezyki-programowania/jezyki-programowania.md`, karty bazy w
`references/bazy-danych/bazy-danych.md` lub karty frameworka w `references/frameworki/frameworki.md`
— każda karta zawiera sekcję „Diagnostyka” z narzędziami przyjętymi zawodowo w danym ekosystemie.

## Spis kart referencyjnych

Karty poniżej rozwijają procedurę o warsztat klasy zawodowej. Sięgaj po kartę,
gdy diagnoza wykracza poza prosty przypadek pięciu etapów — nie wczytuj wszystkich
naraz.

| Karta | Plik | Kiedy sięgnąć |
| --- | --- | --- |
| Techniki zaawansowane | `references/debugowanie/techniki-zaawansowane.md` | Regresja o nieznanym pochodzeniu, błąd niedeterministyczny, wyścig, wyciek pamięci, problem wydajnościowy, przypadek zbyt duży do analizy — bisekcja, minimalizacja, narzędzia detekcji |
| Diagnostyka produkcyjna | `references/debugowanie/diagnostyka-produkcyjna.md` | Błąd wyłącznie na środowisku produkcyjnym lub „działa u mnie”, awaria po wdrożeniu, błąd tylko pod obciążeniem, analiza po awarii, praca na dziennikach i zrzutach bez debuggera |
| Pułapki rozumowania | `references/debugowanie/pulapki-rozumowania.md` | Zawsze, gdy diagnoza trwa dłużej niż jedno podejście albo gdy hipoteza „wydaje się oczywista” — katalog błędów poznawczych diagnosty wraz z kontrtechnikami |
