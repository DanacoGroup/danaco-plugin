# Pułapki rozumowania — błędy poznawcze diagnosty i kontrtechniki

Najkosztowniejsze błędy diagnozy nie wynikają z braku wiedzy o narzędziach,
lecz z wadliwego rozumowania: diagnosta widzi to, co spodziewa się zobaczyć,
i przestaje szukać po znalezieniu wyjaśnienia wygodnego. Modele LLM podlegają tym
pułapkom co najmniej na równi z ludźmi, a dodatkowo płynnie uzasadniają błędne
wnioski. Gdy diagnoza trwa dłużej niż jedno podejście albo wniosek „wydaje się
oczywisty” — przejdź ten katalog i sprawdź, w której pułapce właśnie tkwisz.
Każda pułapka ma kontrtechnikę: czynność, nie postanowienie.

## 1. Kotwiczenie na miejscu ujawnienia

Mechanizm: ślad stosu i komunikat błędu wskazują miejsce, w którym błąd się
ujawnił — a uwaga diagnosty kotwiczy się na tym miejscu i tam szuka winy.
Tymczasem ślad wskazuje ofiarę, nie sprawcę: funkcja, która padła na wartości
NULL, jest zwykle ostatnim ogniwem łańcucha rozpoczętego wiele warstw
wcześniej. Sygnał ostrzegawczy: poprawka polega na dodaniu warunku ochronnego
dokładnie w linii z komunikatu błędu.

Kontrtechnika — **wędrówka w górę przepływu danych**: weź wartość wadliwą
z miejsca awarii i cofaj się po jej historii, zadając na każdym kroku pytanie
„skąd ta wartość tu przyszła” — przez parametry, pola, kolumny, komunikaty —
aż do miejsca, w którym wartość po raz pierwszy stała się wadliwa. Dopiero to
miejsce jest kandydatem na przyczynę źródłową; miejsce awarii — co najwyżej
na dodatkowe zabezpieczenie. Praktycznie: przeszukaj kod po punktach zapisu
pola, sprawdź dane w spoczynku (od kiedy i ile wierszy wadliwych), skoreluj
czas ich powstania z historią wdrożeń.

## 2. Racjonalizacja zastanego stanu jako celowego

Mechanizm: diagnosta napotyka w kodzie lub danych stan dziwny — wiersz-widmo,
wyciszony wyjątek, uśpienie na 500 ms, wyłączony test — i dopisuje mu
uzasadnienie: „widocznie tak ma być, pewnie dla audytu / kompatybilności /
wydajności”. Wymyślone uzasadnienie brzmi rozsądnie, więc zostaje przyjęte za
fakt, a diagnoza schodzi na poprawkę objawową omijającą „celowy” stan.
Pułapka szczególnie częsta u modeli LLM: model generuje wiarygodne wyjaśnienie
z tą samą płynnością, z jaką relacjonuje fakty.

Kontrtechnika — **żądanie dowodu intencji**: intencję wolno przypisać wyłącznie
na podstawie dowodu — komentarza projektowego, dokumentacji, testu
utrwalającego zachowanie jako oczekiwane, albo słowa właściciela projektu.
Przeprowadź kwerendę dowodową jawnie: przeszukaj kod i dokumentację po nazwach
związanych z podejrzanym stanem, sprawdź testy, w razie potrzeby zapytaj
właściciela. Brak dowodu = usterka do naprawy u źródła, nie decyzja projektowa.
W raporcie zapisz rozstrzygnięcie wprost: „dowód intencji: <przytoczony> /
nie znaleziono — traktuję jako usterkę”. Zakaz formułowań „prawdopodobnie
celowe”, „wygląda na zamierzone” bez przytoczonego dowodu.

## 3. Potwierdzanie hipotezy

Mechanizm: po postawieniu hipotezy diagnosta szuka obserwacji „za” — i zawsze
je znajduje, bo w złożonym systemie każda hipoteza ma poszlaki; złudzenie
pewności rośnie, choć żadna hipoteza konkurencyjna nie została wykluczona.
Sygnał ostrzegawczy: kolejne sprawdzenia tylko „potwierdzają” i żadne nie
mogło zakończyć się inaczej.

Kontrtechnika — **zaprojektuj obserwację, która hipotezę OBALI**: zanim
wykonasz sprawdzenie, zapisz w rozmowie przewidywanie warunkowe: „jeżeli
hipoteza H prawdziwa, obserwacja O da wynik X; jeżeli fałszywa — inny”.
Sprawdzenie, którego oba możliwe wyniki są zgodne z hipotezą, jest
bezwartościowe — zastąp je takim, które rozróżnia H od najsilniejszej hipotezy
konkurencyjnej. Utrzymuj co najmniej dwie hipotezy naraz; jeżeli masz tylko
jedną, pierwszym zadaniem jest wygenerowanie drugiej, nie potwierdzanie
pierwszej.

## 4. Naprawianie testu zamiast kodu

Mechanizm: test przestał przechodzić, a najkrótsza droga do zieleni prowadzi
przez edycję testu — aktualizację wartości oczekiwanej na tę, którą kod
faktycznie zwraca, poszerzenie tolerancji, oznaczenie testu jako pomijanego.
Każda z tych operacji jest legalna wyłącznie przy zamierzonej zmianie
zachowania; wykonana odruchowo — zamienia zabezpieczenie w atrapę.

Kontrtechnika — **rozstrzygnięcie przed edycją**: zanim dotkniesz testu,
odpowiedz na piśmie: czy specyfikacja zachowania zmieniła się zamierzenie?
Dowodem zamierzenia jest zadanie, opis zmiany lub słowo właściciela — nie
fakt, że kod teraz zwraca inną wartość. Zamierzona zmiana: zaktualizuj test
i wskaż dowód. Brak dowodu: test ma rację, kod jest wadliwy — wróć do etapu 2
procedury. Bezwzględny zakaz: aktualizacja wartości oczekiwanej przez
skopiowanie wartości bieżącej z wyniku uruchomienia bez tego rozstrzygnięcia.

## 5. „To niemożliwe”

Mechanizm: obserwacja przeczy przekonaniu diagnosty o tym, jak kod działa —
i diagnosta odrzuca obserwację zamiast przekonania: „ta funkcja nie mogła
zwrócić NULL”, „ten warunek zawsze jest prawdziwy”. Komputer tymczasem
wykonuje kod rzeczywisty, nie wyobrażony; „to niemożliwe” znaczy tyle, że
model kodu w głowie diagnosty różni się od kodu w maszynie — a ta różnica
jest właśnie poszukiwanym błędem.

Kontrtechnika — **minimalna reprodukcja przeczącego zjawiska**: wyodrębnij
„niemożliwy” fragment do samodzielnego programu kilkuliniowego i uruchom.
Dwa możliwe wyniki, oba wartościowe: zjawisko występuje w izolacji — masz
reprodukcję i dowód, że przekonanie było fałszywe; nie występuje — różnica
między izolacją a systemem pełnym wskazuje brakujący składnik mechanizmu
(stan współdzielony, kolejność inicjalizacji, inna wersja zależności).
Zweryfikuj też tożsamość kodu wykonywanego: czy proces wykonuje tę wersję
pliku, którą czytasz (ścieżka modułu, pamięć podręczna bajtkodu, niedokonane
wdrożenie) — znaczna część „niemożliwości” to wykonywanie starego kodu.

## 6. Wiara w komunikat błędu

Mechanizm: komunikat błędu traktowany jest jak diagnoza, a bywa jedynie
ostatnim słowem procesu — nieraz mylącym. Typowe zafałszowania: wyjątek
wtórny przesłania pierwotny (błąd w procedurze obsługi błędu), komunikat
opisuje skutek odległy („connection reset” — bo serwer padł z zupełnie innego
powodu), warstwa pośrednia opakowuje błąd we własny, ogólniejszy
(„500 Internal Server Error” jako opakowanie czegokolwiek), komunikat
formułowany jest z perspektywy biblioteki, nie problemu („No such file” o
pliku, którego nazwa powstała z błędnego sklejenia ścieżki).

Kontrtechnika — **pierwszy błąd w dzienniku, nie ostatni**: przewiń dziennik
do początku okna zdarzenia i czytaj chronologicznie w przód; diagnozuj
pierwszy wpis odbiegający od normy, późniejsze traktuj jako podejrzane o
wtórność do czasu wykluczenia. W śladach wyjątków czytaj łańcuch przyczyn do
końca (`Caused by:` w Javie, `__cause__` w Pythonie, `cause` w JS) — diagnozie
podlega wyjątek najgłębszy. Komunikat traktuj jak zeznanie świadka: punkt
wyjścia do sprawdzeń, nigdy rozstrzygnięcie.

## 7. Poprawka, która „pomogła”, bez zrozumienia dlaczego

Mechanizm: po którejś z prób objaw znika — i pojawia się pokusa zamknięcia
sprawy. Jeżeli nie potrafisz wskazać mechanizmu łączącego zmianę z objawem,
prawdopodobne pozostają scenariusze gorsze: objaw zniknął przypadkiem (błąd
niedeterministyczny się przyczaił), poprawka zamaskowała objaw przesuwając
usterkę w miejsce trudniejsze do wykrycia, albo pomogło coś ubocznego
(restart, świeży stan pamięci podręcznej), a nie sama zmiana.

Kontrtechnika — **zakaz zamknięcia diagnozy bez mechanizmu**: diagnoza jest
zakończona dopiero, gdy raport zawiera zdanie „błąd powstawał, ponieważ X
prowadziło do Y, a zmiana Z przerywa ten łańcuch, ponieważ...”, a każde ogniwo
ma obserwację na poparcie. Jeżeli koszt pozwala, wykonaj próbę odwrotną:
wycofaj poprawkę i potwierdź, że objaw wraca — poprawka, po której wycofaniu
objaw nie wraca, niczego nie naprawiła. Przy błędach niedeterministycznych
zastąp pojedyncze uruchomienie pętlą z licznikiem częstotliwości (karta
technik zaawansowanych). Sformułowania „wygląda, że pomogło”, „powinno już
działać” są zakazane — zastępuje je przytoczony wynik weryfikacji.

## 8. Efekt świeżej zmiany

Mechanizm: pułapka o dwóch ostrzach. Ostrze pierwsze — „to na pewno moja
ostatnia zmiana”: uwaga skupia się na świeżym kodzie, choć zmiana mogła jedynie
odsłonić usterkę leżącą w kodzie od dawna. Ostrze drugie — „to na pewno nie
moja zmiana”: autor przekonany o niewinności własnego kodu szuka winy w
środowisku i cudzych modułach, odwlekając sprawdzenie najbardziej
prawdopodobnego podejrzanego. Oba ostrza łączy to samo: przekonanie zastępuje
pomiar.

Kontrtechnika — **bisekcja zamiast przekonań**: związek zmiany z objawem
rozstrzygaj doświadczalnie. Krok najtańszy: uruchom scenariusz błędu na
rewizji sprzed zmiany (`git stash` dla zmian roboczych, `git checkout
<rewizja>` dla zatwierdzonych). Objaw występuje przed zmianą — zmiana niewinna
albo współwinna; nie występuje — zmiana jest sprawcą lub wyzwalaczem. Przy
wielu kandydatach: `git bisect` z automatem (karta technik zaawansowanych).
Rozróżniaj sprawcę od wyzwalacza: zmiana, która odsłoniła starą usterkę, nie
jest miejscem naprawy — naprawie podlega usterka odsłonięta, a wynik bisekcji
wskazuje jedynie, gdzie zacząć wędrówkę w górę przepływu danych.

## 9. Dług hipotez

Mechanizm: w długiej diagnozie hipotezy mnożą się i giną — diagnosta wraca do
hipotez już obalonych, „sprawdza” to samo trzeci raz, a po godzinach nie umie
powiedzieć, co zostało wykluczone. U modeli LLM pułapka zaostrza się wraz z
długością rozmowy: wcześniejsze ustalenia wypadają z uwagi i rozumowanie
dryfuje po kole.

Kontrtechnika — **notatnik diagnozy prowadzony w rozmowie**: gdy diagnoza przekracza dwie hipotezy
albo trzy sprawdzenia, prowadź jawny rejestr i przytaczaj go w całości po każdej rundzie obserwacji
— w treści rozmowy, nie w pliku (dyscyplina plików ze standardów zawodowych,
`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`; rejestr w rozmowie dodatkowo utrzymuje
ustalenia w polu uwagi modelu). Format:

```
H1: pula połączeń wyczerpana przez ścieżkę błędu — OBALONA
    (licznik puli stabilny podczas reprodukcji, obserwacja z 14:12)
H2: timeout klienta krótszy niż czas zapytania — POSTAWIONA
    następne sprawdzenie: zmierzyć rozkład czasów zapytania pod obciążeniem
H3: regresja planu zapytania po migracji — POTWIERDZONA CZĘŚCIOWO
    (plan zmienił się na skan sekwencyjny; brak dowodu związku z objawem)
```

Reguły prowadzenia: status wyłącznie z listy postawiona / obalona /
potwierdzona — zmienia go tylko przytoczona obserwacja, nigdy „upływ czasu”
ani „wrażenie”; hipoteza obalona nie wraca do gry bez nowej obserwacji
podważającej obalenie; w każdej chwili dokładnie jedno sprawdzenie jest
„następne”. Rejestr wchodzi w skład raportu końcowego: pokazuje właścicielowi
projektu nie tylko wynik, lecz także co wykluczono i jakim dowodem.

## Użycie katalogu w praktyce

Katalog stosuj w dwóch trybach. Tryb bieżący: gdy pojawia się sygnał
ostrzegawczy którejkolwiek pułapki — zatrzymaj się i wykonaj kontrtechnikę,
zanim wykonasz kolejną edycję kodu. Tryb kontrolny: przed raportem końcowym
przejdź wszystkie dziewięć pozycji i sprawdź, czy żadna nie opisuje właśnie
zakończonej diagnozy; szczególnie pozycje 2, 4 i 7, bo ich skutki wyglądają
jak sukces — diagnoza „domknięta” tymi pułapkami wraca jako incydent.
