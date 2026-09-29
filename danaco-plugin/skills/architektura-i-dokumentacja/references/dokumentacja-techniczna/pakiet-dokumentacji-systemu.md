# Pakiet dokumentacji architektury systemu — metoda wytworzenia

Karta opisuje metodę wytworzenia kompletnego pakietu dokumentacji architektury
systemu: zbioru kilkunastu opracowań kanonicznych, które razem stanowią jedyne
źródło prawdy projektowej produktu — od koncepcji po system wizualny. Pakiet
tej klasy czyta deweloper, zanim napisze pierwszą linię kodu; czyta go audytor,
zanim oceni bezpieczeństwo; czyta go nowy członek zespołu, zanim zada pierwsze
pytanie. Metoda jest niezależna od dziedziny produktu — obowiązuje dla platformy,
usługi, aplikacji i systemu wbudowanego.

## 1. Skład kanoniczny pakietu

Pakiet składa się z README-indeksu oraz opracowań tematycznych. Każde opracowanie
ma **jednego właściciela tematu**: temat należy w całości do jednego dokumentu,
a pozostałe dokumenty odsyłają do niego zamiast powtarzać treść. Dublowanie
tematu między dokumentami jest usterką pakietu — dwa opisy tego samego mechanizmu
nieuchronnie się rozjadą.

### 1.1. Opracowania i ich zakresy

| Opracowanie | Właściciel tematu — zakres wyłączny | Kolejność |
|---|---|---|
| README-indeks | Metryka produktu, zasady katalogu, spis opracowań ze statusami. Nie zawiera treści merytorycznej systemu. | 0 (powstaje pierwszy, aktualizowany do końca) |
| Koncepcja produktu / platformy | Czym produkt jest i dla kogo; pojęcia podstawowe i słownik; warstwy logiczne; zasady nadrzędne funkcjonalności; rozstrzygnięcia kwestii otwartych. Dokument autorytatywny — pozostałe realizują jego postanowienia. | 1 |
| Architektura techniczna | Model wdrożenia, stos technologiczny z uzasadnieniami, warstwy techniczne, model procesów i sesji, widok wdrożeniowy. Realizuje koncepcję; wskazuje, który rozdział którą zasadę koncepcji odzwierciedla. | 2 |
| Model danych | Encje, relacje, klucze, ograniczenia, cykl życia danych, migracje, kopie zapasowe. Jedyne miejsce definicji schematu — inne dokumenty przywołują encje po nazwie. | 3 |
| Kontrakty komunikacji | Protokoły, formaty komunikatów, kierunki przepływu, kolejność wymian, zachowanie przy zerwaniu i wznowieniu, wersjonowanie kontraktu. | 4 |
| Specyfikacje funkcjonalne | Po jednym opracowaniu na obszar funkcjonalny (moduły, agenci, okna robocze, orkiestracja): zachowanie obserwowalne, stany, przypadki brzegowe, scenariusze. | 5 |
| Bezpieczeństwo i uwierzytelnianie | Model zagrożeń, tożsamość, sesje uwierzytelnienia, uprawnienia, ochrona danych, sekrety. Jedyne miejsce decyzji bezpieczeństwa — specyfikacje funkcjonalne odsyłają tu przy każdym punkcie styku. | 6 |
| Model konfiguracji | Struktura konfiguracji, źródła wartości i pierwszeństwo, wartości domyślne, walidacja, zachowanie przy braku ustawienia. | 7 |
| Izolacja i zależności | Granice izolacji (procesy, konteksty, dane), zależności między częściami systemu, punkty konfigurowalne izolacji. | 7 |
| Integracja usług zewnętrznych / modeli | Adaptery, kontrakty z dostawcami zewnętrznymi, obsługa niedostępności, limity, koszty. | 7 |
| Rozszerzenia | Mechanizm rozszerzania systemu: punkty rozszerzeń, kontrakt rozszerzenia, cykl życia, izolacja rozszerzenia od rdzenia. | 7 |
| Nawigacja i struktura interfejsu | Punkt wejścia, hierarchia nawigacji, model przejść, stany interfejsu. | 8 |
| System wizualny | Tokeny projektowe, typografia, kolorystyka, komponenty, ikonografia, zasady kompozycji. | 8 |

### 1.2. Kolejność powstawania i zależności

Kolejność w tabeli nie jest umowna — odzwierciedla zależności treściowe.
Dokument późniejszy przywołuje pojęcia zdefiniowane wcześniej; pisanie w odwrotnej
kolejności wymusza definiowanie pojęć „na kredyt” i kończy się niespójnością.

```
KONCEPCJA ──► ARCHITEKTURA ──► MODEL DANYCH ──► KONTRAKTY KOMUNIKACJI
                                     │                  │
                                     ▼                  ▼
                        SPECYFIKACJE FUNKCJONALNE (po jednej na obszar)
                                     │
                                     ▼
                    BEZPIECZEŃSTWO I UWIERZYTELNIANIE
                                     │
                                     ▼
        KONFIGURACJA · IZOLACJA · INTEGRACJE · ROZSZERZENIA (równolegle)
                                     │
                                     ▼
                    NAWIGACJA ──► SYSTEM WIZUALNY
```

Reguły kolejności:

1. Koncepcja rozstrzyga **co** system robi; architektura — **jak** technicznie;
   nie odwracaj tej zależności ani nie łącz obu w jednym dokumencie.
2. Specyfikacje funkcjonalne piszą się dopiero po modelu danych i kontraktach:
   każdy opis zachowania przywołuje encje i komunikaty po nazwie, więc nazwy
   muszą już istnieć.
3. Bezpieczeństwo powstaje po specyfikacjach funkcjonalnych — model zagrożeń
   wymaga znajomości pełnej powierzchni systemu, nie jej wyobrażenia.
4. Dokumenty grupy „konfiguracja / izolacja / integracje / rozszerzenia” są
   względem siebie niezależne i mogą powstawać równolegle, lecz każdy z nich
   zależy od architektury i modelu danych.
5. System wizualny powstaje ostatni — dokumentuje decyzje projektowe
   dla struktury interfejsu, która musi być wcześniej ustalona.

### 1.3. Reguła jednego właściciela i odsyłaczy

- Każdy temat ma dokładnie jeden dokument-właściciela; przypisanie tematów
  wykonaj przed pisaniem (rozdz. 4, krok 2) i utrzymuj do końca życia pakietu.
- Gdy dokument potrzebuje treści cudzego tematu, wstawia **odsyłacz** do
  dokumentu-właściciela z numerem rozdziału — nigdy kopię ani streszczenie
  własnymi słowami. Streszczenie to druga wersja prawdy.
- Dopuszczalny wyjątek: jedno zdanie kontekstu przy odsyłaczu, aby czytelnik
  wiedział, po co ma przejść do innego dokumentu.
- Gdy temat nie mieści się w żadnym istniejącym dokumencie, decyzja brzmi:
  rozszerzyć zakres istniejącego właściciela albo powołać nowe opracowanie
  w README-indeksie — nigdy dopisać temat „gdzie akurat wygodnie”.

## 2. Standard redakcyjny pakietu

Standard obowiązuje każdy dokument pakietu bez wyjątku. Jednolitość nie jest
estetyką — pozwala czytelnikowi przenieść nawyki lektury między dokumentami
i odróżnić dokument kanoniczny od przypadkowego pliku.

### 2.1. Nagłówek redakcyjny (metryka produktu)

Każdy dokument otwiera tytuł oraz tabela metryki o stałym układzie pól:

| Pole | Treść |
|---|---|
| Produkt | Nazwa własna produktu. |
| Rodzaj | Klasa produktu jednym określeniem. |
| Opis | Jedno–dwa zdania: czym produkt jest. Identyczne we wszystkich dokumentach pakietu. |
| Producent | Podmiot odpowiedzialny. |
| Twórca | Autor koncepcji lub opracowania. |
| Wersja | Wersja opracowania (nie produktu). |
| Status | Stan pakietu, np. deweloperski / zatwierdzony. |
| Data | Data wydania bieżącej wersji dokumentu. |

Po metryce produktu może następować druga, krótka tabela informacji
szczegółowych dokumentu (źródło, przeznaczenie, adresat) — różna między
dokumentami, w odróżnieniu od metryki, która jest wspólna.

### 2.2. Elementy obowiązkowe korpusu

1. **Akapit przeznaczenia** bezpośrednio po metryce: jedno–trzy zdania — co
   dokument opisuje, co realizuje, dla kogo jest podstawą.
2. **Spis treści** z numeracją rozdziałów i wykazem załączników.
3. **Numeracja rozdziałów** ciągła (1., 1.1., 1.2.); załączniki literowane
   (Załącznik A, B, …). Odsyłacze wewnętrzne i międzydokumentowe podają numer
   rozdziału, nie numer strony.
4. **Załączniki scenariuszowe**: scenariusze użycia, wdrożenia lub eksploatacji
   przenoszące mechanizmy rozdziałów w konkretne przebiegi krok po kroku.
   Scenariusz przywołuje rozdziały, których mechanizmy ilustruje.
5. **Stopka praw**: linia z nazwą produktu i wersją oraz linia praw autorskich
   z odesłaniem do licencji i kontaktem.

### 2.3. Jednolita terminologia i słownik pojęć

- Pakiet ma **jeden słownik pojęć**, umieszczony w dokumencie koncepcji jako
  rozdział; pozostałe dokumenty używają pojęć w brzmieniu słownika i nie
  definiują ich ponownie.
- Pojęcie ma jedną nazwę w całym pakiecie. Synonimy stosowane wymiennie
  („moduł” raz jako „komponent”, raz jako „plugin”) są usterką wykrywaną
  w przejściu spójnościowym (rozdz. 4, krok 4).
- Nazwy pojęć w pakiecie są tymi samymi nazwami, które nosi kod; rozjazd
  nazewnictwa dokument–kod usuwaj po stronie, która jest młodsza.
- Zakaz skrótów odsyłających i oznaczeń literowo-cyfrowych bez rzeczywistego
  znaczenia w projekcie — każde określenie w dokumencie ma pełne brzmienie.

## 3. README-indeks jako dokument zarządzający

README-indeks katalogu pakietu jest dokumentem zarządzającym, nie merytorycznym.
Zawiera cztery bloki:

1. **Metryka produktu** — identyczna jak w dokumentach merytorycznych; README
   jest wzorcem, z którego pozostałe dokumenty kopiują metrykę.
2. **Zasady katalogu** — wyliczone i ponumerowane, co najmniej: katalog jest
   źródłem prawdy dokumentacyjnej; zakaz gromadzenia szkiców, kopii roboczych
   i starych wersji (poprzednia wersja jest zastępowana, nie odkładana obok);
   standard redakcyjny obowiązuje każdy plik bez wyjątku; rozstrzygnięcie,
   czy katalog podlega kontroli wersji repozytorium kodu, oraz zasady
   postępowania, jeśli katalog może zawierać informacje wrażliwe.
3. **Tabela grup opracowań** — grupa, zawartość, lokalizacja; przy strukturze
   z podkatalogami każda grupa ma własny README z indeksem szczegółowym.
4. **Wykaz opracowań ze statusami** — tabela: nazwa dokumentu, zakres jednym
   zdaniem, status (planowany / w opracowaniu / kompletny / do uzgodnienia
   z kodem). Wykaz jest narzędziem kontroli kompletności — dokument nieobecny
   w wykazie nie istnieje dla pakietu, a plik w katalogu nieobecny w wykazie
   podlega usunięciu albo wpisaniu.

README opisuje także procedurę dodania nowego dokumentu: przypisanie do grupy,
konwencja nazwy pliku, obowiązek metryki i stopki, zakaz wersji roboczej obok
dokumentu docelowego, aktualizacja indeksu.

## 4. Procedura wytwarzania pakietu

### Krok 1. Inwentaryzacja wiedzy źródłowej

Zbierz wszystko, co o systemie wiadomo: kod, konfiguracje, istniejące notatki,
decyzje ustne właściciela, protokoły rozmów. Dla każdego przyszłego dokumentu
zanotuj, skąd pochodzi jego treść i co pozostaje nieustalone. Rzeczy
nieustalonych nie wymyślaj — załóż listę kwestii otwartych i doprowadź do ich
rozstrzygnięcia u właściciela; rozstrzygnięcia zapisz w dedykowanym rozdziale
koncepcji.

### Krok 2. Szkielety wszystkich dokumentów

Zanim napiszesz pierwszy dokument w całości, utwórz szkielety **wszystkich**:
tytuł, metryka, akapit przeznaczenia, spis treści z tytułami rozdziałów, po
jednym zdaniu zakresu na rozdział. Szkielety pełnią dwie funkcje kontrolne:

- **kontrola pokrycia** — porównaj sumę zakresów rozdziałów z inwentaryzacją;
  temat bez rozdziału to luka pakietu;
- **kontrola rozłączności** — ten sam temat w dwóch szkieletach to konflikt
  własności; rozstrzygnij go teraz, przenosząc temat do jednego właściciela
  i wpisując odsyłacz w drugim.

Szkielety zatwierdź z właścicielem — zmiana składu pakietu po wypełnieniu
dokumentów kosztuje wielokrotnie więcej.

### Krok 3. Wypełnianie w kolejności zależności

Wypełniaj dokumenty w kolejności z rozdziału 1.2. W trakcie pisania dokumentu
późniejszego nie „poprawiaj przy okazji” wcześniejszego — potrzebną zmianę
zanotuj i wykonaj jako świadomą edycję z ponownym przejściem odsyłaczy do
zmienionego rozdziału.

### Krok 4. Przejście spójnościowe całego pakietu

Po wypełnieniu wszystkich dokumentów wykonaj przejście spójnościowe — osobny
etap, nie „czytanie przy okazji”:

1. **Terminologia**: dla każdego pojęcia słownika przeszukaj cały pakiet
   (grep po nazwie i podejrzewanych synonimach); ujednolić brzmienie.
2. **Odsyłacze**: sprawdź każdy odsyłacz — czy dokument i rozdział docelowy
   istnieją i czy treść docelowa nadal odpowiada obietnicy odsyłacza.
3. **Zgodność międzydokumentowa**: wartości i rozstrzygnięcia występujące
   w kilku dokumentach (nazwy encji, protokoły, limity, listy elementów)
   porównaj parami; różnica to usterka — popraw u właściciela tematu
   i skoryguj odsyłacze.
4. **Metryki i stopki**: identyczność metryki produktu, obecność stopki,
   zgodność dat i wersji ze stanem faktycznym.

### Krok 5. Kontrola kompletności według listy

Zamknięcie pakietu następuje po kontroli listowej: każdy dokument z wykazu
README ma status „kompletny”; każdy rozdział szkieletu jest wypełniony albo
świadomie usunięty z aktualizacją spisu treści; lista kwestii otwartych jest
pusta albo każda pozycja ma rozstrzygnięcie zapisane w koncepcji; przejście
spójnościowe wykonano po ostatniej edycji merytorycznej. Wynik kontroli
odnotuj w statusach wykazu — nie w treści dokumentów.

## 5. Kryteria jakości dokumentu

Dokument pakietu klasy zawodowej liczy zwykle 30–110 tysięcy znaków. Objętość
jest skutkiem głębokości, nie celem — dokument krótszy, który wyczerpuje temat,
jest lepszy od dłuższego z watą.

**Głębokość sekcji.** Każdy mechanizm opisany w dokumencie ma komplet:
**cel** (po co istnieje), **przebieg** (jak działa krok po kroku lub stan po
stanie), **przypadki brzegowe** (zerwanie, brak danych, konflikt, limit,
restart) oraz **scenariusz** (co najmniej jeden przebieg konkretny, własny
lub w załączniku scenariuszowym). Mechanizm opisany samym celem to deklaracja,
nie specyfikacja.

**Tabele decyzyjne.** Każdą decyzję projektową o więcej niż jednym wariancie
przedstaw tabelą: wymiar porównania w wierszach, warianty w kolumnach, wybór
z uzasadnieniem pod tabelą. Wyliczenia właściwości, przypisania
odpowiedzialności i macierze dostępności również prowadź tabelami — proza
o trzech równoległych cechach czterech elementów jest nieczytelna.

**Schematy tekstowe.** Przepływy, cykle życia i hierarchie przedstawiaj
schematem tekstowym w bloku kodu (ASCII), z tymi samymi nazwami pojęć co
w tekście. Schemat uzupełnia tabelę lub akapit — nie zastępuje definicji.

**Zakaz waty.** Usuń zdania, których zniknięcie nie zubaża treści: powtórzenia
tego, co niesie tabela obok; zapowiedzi („w tym rozdziale opiszemy…”);
ogólniki bez rozstrzygnięcia („system powinien być wydajny”); przymiotniki
oceniające własny projekt. Test: streszczenie rozdziału w jednym zdaniu musi
być trudne, bo każdy akapit niesie odrębną treść.

## 6. Utrzymanie pakietu

1. **Zastępowanie wersji.** Nową wersję dokumentu zapisuj w miejscu starej,
   pod tą samą nazwą pliku; podnieś wersję i datę w metryce. Zakaz plików
   `-v2`, `-final`, `-kopia` — historia wersji należy do mechanizmu kontroli
   wersji albo do archiwum poza katalogiem pakietu, nigdy do katalogu.
2. **Zakaz kopii.** Treść pakietu nie jest kopiowana do innych katalogów ani
   dokumentów pochodnych; potrzebujący treści odsyłają do pakietu.
3. **Uzgodnienie z kodem.** Zmiana systemu, która unieważnia treść dokumentu,
   obejmuje edycję dokumentu-właściciela tematu w tym samym zakresie prac;
   rozjazd pakiet–kod traktuj jak usterkę i wykrywaj w przeglądzie kodu.
   Po każdej edycji merytorycznej wykonaj lokalne przejście spójnościowe:
   odsyłacze do zmienionego rozdziału oraz wystąpienia zmienionych nazw
   w całym pakiecie.
4. **Jeden redaktor przejścia.** Przejście spójnościowe całego pakietu
   powierzaj jednej osobie na raz — spójność jest własnością całości i nie
   powstaje z sumy lokalnych starań.
