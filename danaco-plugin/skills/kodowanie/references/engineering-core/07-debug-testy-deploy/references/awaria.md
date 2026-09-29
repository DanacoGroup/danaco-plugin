# Awaria — reakcja, komunikacja, wnioski

Jedna zasada porządkuje wszystko poniżej: **przywrócenie działania jest ważniejsze niż
ustalenie przyczyny.** Diagnoza z ruchem produkcyjnym na zepsutym systemie kosztuje
użytkowników. Przyczynę ustalisz po przywróceniu, na podstawie zapisanych danych.

Kolejność: **wykryj → oceń wagę → obsadź role → przywróć → komunikuj → zapisz oś czasu →
przeanalizuj bez szukania winnego → wdróż wnioski.**

---

## Ocena wagi

Waga awarii ma nazwę, nie kod — w komunikacji podawaj nazwę wprost.

Wagę ustala się w pierwszych 5 minutach, na podstawie **wpływu na użytkownika**, nie
na podstawie tego, jak trudna wydaje się naprawa.

| Waga | Kryterium | Reakcja | Powiadomienie |
| --- | --- | --- | --- |
| **krytyczna** | Usługa niedostępna dla wszystkich; utrata lub uszkodzenie danych; wyciek danych osobowych | natychmiast, budzenie, wszystkie ręce | kierownictwo od razu; użytkownicy w 30 min |
| **poważna** | Kluczowa funkcja niedostępna dla wielu (logowanie, płatność, zapis); silna degradacja wydajności | do 15 min, dyżurny + właściciel obszaru | użytkownicy przy > 30 min trwania |
| **umiarkowana** | Funkcja poboczna niedostępna; część użytkowników; istnieje obejście | w godzinach pracy, tego samego dnia | wsparcie dostaje treść odpowiedzi |
| **drobna** | Usterka kosmetyczna, wpływ minimalny | w normalnej kolejce zadań | brak |

Zasady stosowania:

1. **Przy wątpliwości podnieś wagę.** Obniżenie wagi z krytycznej na poważną po 10 minutach nic nie
   kosztuje. Podniesienie z umiarkowanej na krytyczną po godzinie kosztuje godzinę.
2. **Wyciek danych osobowych to zawsze waga krytyczna**, niezależnie od liczby rekordów. RODO:
   zgłoszenie do organu nadzorczego w ciągu **72 godzin** od stwierdzenia naruszenia — zegar rusza w
   momencie stwierdzenia, nie w momencie zakończenia analizy. Włącz osobę odpowiedzialną za ochronę
   danych od razu.
3. **Uszkodzenie danych to waga krytyczna, nawet gdy system działa.** Im dłużej działa, tym więcej
   danych psuje. Rozważ zatrzymanie zapisu.

---

## Kto co robi

Przy wadze krytycznej i poważnej role muszą być **nazwane głośno**, także w zespole dwuosobowym. Bez
tego wszyscy diagnozują to samo i nikt nie odpowiada użytkownikom.

| Rola | Odpowiada za | Nie robi |
| --- | --- | --- |
| **Dowodzący** | decyzje, priorytety, przydział zadań, ogłoszenie końca | nie debuguje — to najczęstszy błąd |
| **Operacyjny** | faktyczna diagnoza i naprawa | nie pisze komunikatów |
| **Komunikujący** | strona statusu, użytkownicy, kierownictwo, wsparcie | nie diagnozuje |
| **Protokolant** | oś czasu ze znacznikami, zbieranie dowodów | nie naprawia |

W zespole dwuosobowym: jedna osoba dowodzi i komunikuje, druga naprawia. Oś czasu pisze
dowodzący.

Dowodzący, który wchodzi w konsolę, przestaje dowodzić. Jeśli nie da się inaczej —
przekaż dowodzenie jawnym zdaniem: „przejmuję konsolę, dowodzenie przejmuje Marek”.

---

## Przywrócenie działania

### Kolejność działań

1. **Zatrzymaj powiększanie szkody.** Wyłącz przełącznik funkcji, zablokuj ścieżkę
   zapisu, ogranicz ruch. Zanim zaczniesz diagnozować.
2. **Sprawdź, co się zmieniło w ostatnich 24 h.** W kolejności: wdrożenie kodu, zmiana
   konfiguracji lub flagi, migracja, aktualizacja infrastruktury, zmiana u dostawcy,
   nietypowy wzrost ruchu. To pokrywa większość awarii.
3. **Jeśli była zmiana — cofnij ją**, nie diagnozuj. Wycofanie jest odwracalne, więc
   nawet błędna decyzja o wycofaniu jest tania.
4. **Jeśli nie było zmiany** — sprawdź zasoby (dysk, pamięć, połączenia, limity API,
   certyfikaty) i zależności zewnętrzne (strony statusu dostawców).
5. **Zbierz dowody, zanim je zniszczysz.** Przed restartem: zrzut logów, wartości metryk,
   zrzut pamięci/wątków, `SELECT` z tabel diagnostycznych. Restart czyści stan i razem
   z nim jedyny ślad przyczyny.

```bash
# przed restartem — 30 sekund, które ratują analizę po incydencie
kubectl logs <pod> --since=30m > /tmp/awaria-logi.txt
kubectl describe pod <pod> > /tmp/awaria-pod.txt
kubectl top pods > /tmp/awaria-zasoby.txt
psql -c "SELECT pid,state,wait_event,query_start,query FROM pg_stat_activity
         WHERE state<>'idle' ORDER BY query_start" > /tmp/awaria-baza.txt
```

### Obejścia dopuszczalne w trakcie awarii

Poprawka objawowa jest w trakcie awarii **właściwym** narzędziem — pod warunkiem, że
towarzyszy jej zapisane zadanie naprawy właściwej:

- Restart usługi (kupuje czas, nie naprawia).
- Zwiększenie limitu zasobów.
- Wyłączenie funkcji przełącznikiem.
- Ograniczenie ruchu, kolejkowanie, tryb tylko do odczytu.
- Ręczna poprawka danych — **z zapisem, co dokładnie zmieniono** (`SELECT` przed i po,
  do pliku).

Czego nie robić nigdy, także pod presją: wdrożenie niesprawdzonej poprawki prosto na
produkcję z pominięciem CI; `DELETE`/`UPDATE` bez wcześniejszego `SELECT` tego samego
warunku; zmiana kilku rzeczy naraz (nie będziesz wiedział, co pomogło).

### Gdy przyczyna jest nieznana, a system działa

To nie koniec incydentu, tylko koniec fazy pilnej. Obniż wagę, ale **zostaw incydent otwarty** i
wzmocnij obserwowalność w podejrzanym obszarze, żeby następne wystąpienie dało dane zamiast kolejnej
zagadki (`references/engineering-core/07-debug-testy-deploy/references/obserwowalnosc.md`).

---

## Komunikacja w trakcie

### Zasady

1. **Pierwszy komunikat w ciągu 15 minut od potwierdzenia wagi krytycznej albo poważnej**, nawet
   jeśli nie wiesz nic poza tym, że coś nie działa. Cisza jest interpretowana jako „nie wiedzą, że
   jest problem” — a to gorsze niż problem.
2. **Podaj termin następnej aktualizacji i dotrzymaj go.** „Kolejna informacja o 14:30”
   jest zobowiązaniem. Jeśli o 14:30 nie ma postępu, napisz, że nie ma postępu.
3. **Fakty, bez spekulacji o przyczynie.** „Badamy przyczynę” jest lepsze niż „to
   prawdopodobnie problem z dostawcą” — bo za godzinę okaże się, że to twój kod, i
   stracisz wiarygodność.
4. **Bez żargonu wewnętrznego.** Użytkownika nie interesuje, że „pody wpadły w
   CrashLoopBackOff”. Interesuje go, czy jego faktura się zapisała.
5. **Napisz, co użytkownik ma robić** — czekać, ponowić za godzinę, czy skorzystać
   z obejścia.

### Szablon aktualizacji

```markdown
**[Badamy | Zidentyfikowano | Obserwujemy | Rozwiązane]** — 2026-08-04 13:05

Od 12:40 część użytkowników nie może wystawiać faktur. Przeglądanie i pobieranie
istniejących dokumentów działa bez zakłóceń.

Co robimy: zidentyfikowaliśmy przyczynę i wdrażamy poprawkę.
Co możesz zrobić: dane wprowadzone w formularzu nie zostały utracone — po przywróceniu
działania wystarczy ponowić zapis.

Następna informacja: 13:30 lub wcześniej, jeśli sytuacja się zmieni.
```

Stany: **Badamy** (nie wiemy, co się dzieje) → **Zidentyfikowano** (wiemy, naprawiamy) →
**Obserwujemy** (naprawione, sprawdzamy stabilność) → **Rozwiązane**. Nie ogłaszaj
„Rozwiązane” przed co najmniej 30 minutami stabilnych metryk — ogłoszenie i powrót awarii
kosztuje więcej wiarygodności niż dłuższa awaria.

### Komunikacja wewnętrzna

Jeden kanał na incydent. Wszystko istotne trafia tam, nie na prywatne rozmowy — inaczej
oś czasu jest niemożliwa do odtworzenia, a nowa osoba dołączająca do akcji nie ma jak
się zorientować.

Zmiana stanu ogłaszana głośno: „wycofuję wydanie 2026.08.04 — teraz”, „baza wróciła do
normy o 13:12”. Zmiana zrobiona po cichu prowadzi do tego, że dwie osoby naprawiają to
samo w sprzeczny sposób.

---

## Oś czasu

Zapisuj **w trakcie**, nie po. Rekonstrukcja z pamięci po dwóch dniach jest niedokładna
i pomija właśnie te momenty, które mają znaczenie.

| Godzina | Kto | Co się stało / co zrobiono | Skąd wiemy |
| --- | --- | --- | --- |
| 12:38 | — | Wdrożenie 2026.08.04 (commit `a3f9c21`) | dziennik wdrożeń |
| 12:41 | alarm | 5xx na `/api/faktury` wzrosło z 0,05% do 34% | Grafana, alarm `faktury-5xx` |
| 12:44 | AK | Potwierdzono wagę poważną, objęcie dowodzenia | kanał `#awaria-0804` |
| 12:47 | MW | `pg_stat_activity`: 98/100 połączeń zajętych | zrzut `/tmp/awaria-baza.txt` |
| 12:51 | AK | Decyzja o wycofaniu do 2026.08.01 | kanał |
| 12:54 | MW | Wycofanie zakończone | dziennik wdrożeń |
| 12:58 | — | 5xx wróciło do 0,06% | Grafana |
| 13:30 | AK | Ogłoszono rozwiązanie po 30 min stabilności | strona statusu |

Kolumna „skąd wiemy” jest tym, co odróżnia oś czasu od anegdoty. Bez niej analiza po
incydencie opiera się na wspomnieniach.

Notuj także **rzeczy, które okazały się nieprawdą** („12:46 — podejrzenie awarii
dostawcy płatności, wykluczone o 12:49”). To najcenniejszy materiał do wniosków: pokazuje,
gdzie brakowało informacji.

---

## Analiza po incydencie bez szukania winnego

Termin: **do 5 dni roboczych** od zakończenia. Później pamięć zanika i sprawa traci
priorytet.

### Dlaczego bez winnego

Nie z uprzejmości, tylko z rachunku: w kulturze szukania winnych ludzie przestają
zgłaszać własne pomyłki, a wtedy tracisz dostęp do informacji o rzeczywistych przyczynach.
System, w którym pojedyncza pomyłka człowieka wywołuje awarię, jest źle zaprojektowany —
i to jest przyczyna, nie ta pomyłka.

Przeformułowanie, które trzeba stosować mechanicznie:

| Sformułowanie oskarżające | Sformułowanie systemowe |
| --- | --- |
| „Marek wdrożył bez testów” | „Proces pozwalał wdrożyć przy czerwonym CI — brak bramki blokującej” |
| „Anna źle napisała zapytanie” | „Zapytanie bez indeksu przeszło przegląd; brak automatycznego wykrywania pełnych skanów w CI” |
| „Zapomnieliśmy o zmiennej środowiskowej” | „Aplikacja startowała bez wymaganej zmiennej zamiast paść natychmiast” |
| „Nie zauważyliśmy alarmu” | „Alarm trafiał do kanału z 200 wiadomościami dziennie” |

### Pięć „dlaczego” — poprawnie

Technika działa tylko wtedy, gdy nie zatrzymasz się na pierwszej odpowiedzi
satysfakcjonującej i gdy każde „dlaczego” ma dowód.

```
Objaw: 34% żądań /api/faktury zwracało 500 przez 17 minut.
1. Dlaczego? → Pula połączeń do bazy była wyczerpana.
2. Dlaczego? → Nowy endpoint eksportu otwierał połączenie na rekord w pętli
   (200 rekordów = 200 połączeń) i nie zwalniał ich przed końcem żądania.
3. Dlaczego przeszło przegląd? → Przegląd nie obejmuje wzorców zarządzania zasobami;
   nie ma listy kontrolnej ani reguły lintera.
4. Dlaczego testy nie wykryły? → Testy integracyjne działały na 3 rekordach, gdzie limit
   puli nie był osiągany; brak testu z danymi produkcyjnej wielkości.
5. Dlaczego wykryto dopiero z alarmu, 3 minuty po wdrożeniu? → Wdrożenie było
   natychmiastowe na 100% ruchu; brak etapu kanarkowego dla zmian dotykających bazy.
```

Wnioski wychodzą z poziomów 3–5, nie z poziomu 1. Analiza kończąca się na „naprawiliśmy
wyciek połączeń” nie zapobiegnie następnemu incydentowi tej klasy.

Uwaga: rzadko istnieje jedna przyczyna. Zwykle jest ich kilka i dopiero ich zbieg dał
awarię — zapisz wszystkie, nie wybieraj najwygodniejszej.

### Wnioski, które faktycznie zostaną wdrożone

Wniosek bez tych trzech elementów nie zostanie wykonany: **właściciel imienny**,
**termin**, **priorytet uzgodniony z planem prac**.

| Cecha wniosku | Zły | Dobry |
| --- | --- | --- |
| Konkretność | „poprawić monitoring” | „dodać alarm na wykorzystanie puli połączeń > 80% przez 2 min” |
| Wykonalność | „nigdy nie wdrażać bez testów” | „bramka CI blokująca merge przy czerwonym zestawie — GitHub required checks” |
| Właściciel | „zespół” | „Marek W.” |
| Termin | „wkrótce” | „do 2026-08-18” |
| Weryfikowalność | „lepiej testować” | „test integracyjny eksportu na 5000 rekordów w zestawie CI” |

Ogranicz się do **3–5 wniosków**. Lista dwudziestu nie zostanie zrealizowana i uczy
zespół, że analiza po incydencie jest rytuałem bez skutków.

Podział wniosków, który warto zrobić jawnie:

- **Zapobieganie** — żeby ta przyczyna nie wystąpiła ponownie.
- **Wykrywanie** — żeby następnym razem wiedzieć wcześniej (skrócenie czasu do wykrycia).
- **Ograniczanie skutków** — żeby ta sama przyczyna dawała mniejszą awarię.

Zespoły skupiają się prawie wyłącznie na zapobieganiu. Wykrywanie i ograniczanie skutków
mają zwykle lepszy stosunek kosztu do efektu, bo działają także dla przyczyn, których
nie przewidziałeś.

---

## Szablon raportu po incydencie

```markdown
# Incydent 2026-08-04: niedostępność wystawiania faktur

**Waga:** poważna   **Czas trwania:** 12:40–12:58 (18 min)
**Wykryto:** alarm automatyczny, 12:41 (1 min od początku)
**Autorzy:** Anna K. (dowodząca), Marek W.   **Status:** wnioski w realizacji

## Streszczenie
Wdrożenie 2026.08.04 wprowadziło endpoint eksportu otwierający połączenie do bazy na
każdy rekord. Pula 100 połączeń wyczerpała się w 2 minuty, przez co 34% żądań do
`/api/faktury` zwracało 500. Przywrócono działanie przez wycofanie wydania.

## Wpływ
- Około 340 użytkowników nie mogło wystawić faktury przez 18 minut.
- 12 faktur zapisało się częściowo — naprawione ręcznie 04.08 o 15:20, lista w zadaniu #4471.
- Brak utraty danych. Brak naruszenia ochrony danych osobowych.

## Oś czasu
| Godzina | Zdarzenie | Źródło |
|---|---|---|
| 12:38 | wdrożenie `a3f9c21` | dziennik wdrożeń |
| 12:41 | alarm `faktury-5xx` | Grafana |
| … | … | … |

## Przyczyny
Bezpośrednia: wyczerpanie puli połączeń przez pętlę otwierającą połączenie na rekord.
Współprzyczyny:
1. Testy integracyjne na 3 rekordach nie osiągały limitu puli.
2. Brak alarmu na wykorzystanie puli — dowiedzieliśmy się dopiero z 5xx.
3. Wdrożenie od razu na 100% ruchu, bez etapu kanarkowego.

## Co zadziałało dobrze
- Alarm zadziałał w 1 minutę.
- Wycofanie trwało 3 minuty i było przećwiczone.
- Komunikat na stronie statusu ukazał się o 12:49.

## Co zawiodło
- Diagnoza zajęła 6 minut, bo brakowało metryki puli połączeń.
- Nie wiedzieliśmy od razu, że 12 faktur zapisało się częściowo — ustalono po godzinie.

## Wnioski
| # | Rodzaj | Działanie | Właściciel | Termin |
|---|---|---|---|---|
| 1 | wykrywanie | Metryka i alarm: wykorzystanie puli > 80% przez 2 min | Marek W. | 2026-08-11 |
| 2 | zapobieganie | Test integracyjny eksportu na 5000 rekordów w CI | Anna K. | 2026-08-18 |
| 3 | ograniczanie | Etap kanarkowy 5% / 10 min dla zmian dotykających bazy | Marek W. | 2026-08-25 |
```

---

## Miary, które warto śledzić między incydentami

| Miara | Co mówi | Kierunek |
| --- | --- | --- |
| Czas do wykrycia | jakość monitoringu | niżej |
| Czas do przywrócenia | jakość procedur i narzędzi wycofania | niżej |
| Udział incydentów wykrytych przez alarm, nie przez użytkownika | pokrycie monitoringu | wyżej, cel > 90% |
| Udział wniosków zrealizowanych w terminie | czy analiza cokolwiek zmienia | wyżej, cel > 80% |
| Udział incydentów powtarzających przyczynę | skuteczność wniosków | niżej |

Ostatnia miara jest najważniejsza. Powtarzająca się przyczyna oznacza, że poprzednia
analiza po incydencie była rytuałem. To sygnał do zmiany sposobu prowadzenia analiz,
a nie do napisania kolejnego raportu.

Nie mierz „liczby incydentów” jako celu do obniżenia. Nagradza to zaniżanie wagi
i nieformalne naprawianie po cichu — czyli utratę danych o rzeczywistym stanie systemu.
