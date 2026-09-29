# Techniki przyrostowe — karta

Karta pogłębia zasadę budowy przyrostowej ze `SKILL.md` o techniki uznane
w zawodzie. Każda technika ma warunki stosowalności — dobieraj do zadania,
nie stosuj wszystkich naraz.

## Szkielet kroczący (walking skeleton)

Zanim zbudujesz pierwszą pełną funkcję, zbuduj kompletny przepływ przez
wszystkie warstwy systemu z minimalną treścią. Szkielet kroczący to najmniejsza
możliwa implementacja, która przechodzi od wejścia do wyjścia przez każdą
warstwę, jaka wystąpi w wersji docelowej: przyjęcie żądania, uwierzytelnienie
(choćby zaślepkowe, ale w docelowym miejscu), logika, zapis do prawdziwej bazy,
odpowiedź, wpis w dzienniku, uruchomienie w docelowym mechanizmie wdrożenia.

Postępuj tak:

1. Wybierz jeden przepływ o znikomej logice, ale pełnej głębokości — np.
   utworzenie i odczyt jednego rekordu przez API, z zapisem w docelowej bazie
   i wdrożeniem na docelowe środowisko.
2. Zbuduj go do końca, łącznie z potokiem budowania, testem automatycznym
   i wdrożeniem. Szkielet, którego nie da się wdrożyć, nie jest szkieletem.
3. Dopiero potem dokładaj mięso: kolejne przepływy rozbudowują istniejące
   warstwy zamiast tworzyć nowe.

Wartość szkieletu: najdroższe ryzyka projektu — integracja warstw, wdrożenie,
dostęp do bazy, uwierzytelnienie — ujawniają się pierwszego dnia, gdy koszt
zmiany decyzji jest najniższy. Kolejność odwrotna (cała logika, integracja
„na końcu”) odkłada te ryzyka na moment, w którym przebudowa jest najdroższa.

Sygnał ostrzegawczy: jeżeli po tygodniu budowy nadal nie istnieje ani jeden
przepływ uruchamialny od wejścia do wyjścia, budowa przestała być przyrostowa.

## Plastry pionowe i poziome — kiedy który

Plaster pionowy przecina wszystkie warstwy dla jednej funkcji (formularz →
walidacja → zapis → odczyt). Plaster poziomy buduje jedną warstwę dla wielu
funkcji (wszystkie modele danych, potem wszystkie usługi).

Reguła domyślna: **pionowo**. Plaster pionowy daje po każdym kroku system
działający i weryfikowalny, a błędne założenia projektowe ujawnia natychmiast.

Plaster poziomy dopuszczaj wyjątkowo, gdy zachodzi co najmniej jedno:

- Warstwa jest kontraktem dla innego zespołu lub systemu — np. schemat API
  albo schemat bazy, na który ktoś inny czeka, musi powstać w całości wcześniej
  (patrz „Budowa pod kontraktem” niżej).
- Warstwa jest mechaniczna i jednorodna — np. wygenerowanie klientów dla
  trzydziestu końcówek z jednego schematu; dzielenie tego na plastry pionowe
  tworzy sztuczny narzut.
- Zmiana przekrojowa z natury jest pozioma — podniesienie wersji frameworka,
  wymiana biblioteki dziennika, ujednolicenie obsługi dat.

Nawet wtedy zamykaj plaster poziomy weryfikacją całości (kompilacja, testy),
zanim przejdziesz dalej. Najgroźniejsza postać budowy poziomej to „najpierw
wszystkie abstrakcje” — warstwy interfejsów pisane przed jakimkolwiek użyciem;
tego nie rób nigdy.

## Przełączniki funkcji (feature flags)

Przełącznik funkcji pozwala scalać pracę niedokończoną do gałęzi głównej bez
udostępniania jej użytkownikom. To narzędzie przeciw gałęziom długożyciowym:
gałąź rozwijana tygodniami rozjeżdża się z główną i kończy bolesnym scaleniem;
kod za przełącznikiem scala się codziennie małymi rewizjami.

Zasady stosowania:

- Kod za wyłączonym przełącznikiem musi być martwy dla użytkownika, ale żywy
  dla kompilatora i testów: kompiluje się, przechodzi analizę statyczną, ma
  własne testy uruchamiane z przełącznikiem włączonym.
- Rozgałęzienie umieszczaj możliwie wysoko (punkt wejścia funkcji, trasa,
  rejestracja obsługi), nie rozsiewaj `if flaga` po dziesięciu miejscach
  w głębi logiki. Jeden przełącznik — możliwie jeden punkt rozgałęzienia.
- Rozróżniaj przeznaczenie: przełącznik wydaniowy (ukrywa pracę w toku, żyje
  tygodnie), operacyjny (wyłącznik bezpieczeństwa kosztownej funkcji, żyje
  długo z założenia), eksperymentalny (test A/B). Nie mieszaj ich w jednym
  mechanizmie bez oznaczenia.
- **Każdy przełącznik wydaniowy jest długiem od chwili powstania.** Zakładając
  go, zapisz w zgłoszeniu lub rejestrze projektu termin i warunek usunięcia.
  Po pełnym włączeniu funkcji usuń przełącznik i martwą gałąź kodu w osobnej
  rewizji — system z dziesiątkami zapomnianych przełączników ma 2^n stanów
  konfiguracji, z których testowane są dwa.

W małym projekcie przełącznikiem może być zwykła wartość konfiguracji —
nie wprowadzaj platformy do zarządzania flagami tam, gdzie wystarcza jedno pole.

## Wzorzec dusiciela (strangler fig)

Do przejmowania i wymiany systemu zastanego. Zamiast przepisywać system w całości
(„wielki przełącznik”, który zawodzi statystycznie najczęściej ze wszystkich
strategii), buduj nowy system wokół starego i przejmuj ruch fragmentami:

1. **Postaw fasadę przechwytującą.** Umieść przed systemem zastanym warstwę,
   przez którą przechodzi cały ruch: odwrotne proxy, router API, wspólny punkt
   wejścia modułu. Dopóki fasada tylko przekazuje ruch dalej, nic się nie zmienia —
   to krok o zerowym ryzyku funkcjonalnym, a daje punkt sterowania.
2. **Wybierz pierwszy fragment do przejęcia.** Kryteria dobrego kandydata:
   wyraźna granica (własne dane, mało powiązań), umiarkowana wartość (nie zaczynaj
   od najkrytyczniejszego przepływu), istniejąca wiedza o zachowaniu (albo
   możliwość zbudowania testów charakteryzujących — patrz niżej).
3. **Zbuduj nowe obok, przełącz ruch na fasadzie.** Przez pewien czas prowadź
   równolegle: nowy komponent obsługuje ruch, a wyniki porównujesz z zastanym
   (tzw. równoległy bieg z porównaniem odpowiedzi) albo przełączasz najpierw
   odczyty, potem zapisy.
4. **Uśmiercaj przejęte.** Po ustabilizowaniu przejętego fragmentu usuń jego
   odpowiednik w systemie zastanym. Pominięcie tego kroku to najczęstsza porażka
   wzorca: dwa systemy utrzymywane bez końca.

Największa trudność to wspólne dane. Dopóki oba systemy piszą do tych samych
tabel, ustal jednoznacznie, który jest właścicielem których danych; podwójny
zapis (nowy pisze do obu miejsc) traktuj jako stan przejściowy z terminem końca,
bo każdy podwójny zapis to źródło rozjazdów.

## Testy charakteryzujące — siatka przed zmianą

Kod zastany bez testów wolno zmieniać dopiero po zbudowaniu siatki zachowań.
Test charakteryzujący nie sprawdza, czy kod działa *poprawnie* — utrwala, jak
działa *obecnie*, łącznie z dziwactwami:

1. Wywołaj badany fragment z reprezentatywnym wejściem i zapisz w asercji
   faktyczny wynik — także wtedy, gdy wynik wygląda na błędny. Jeżeli podejrzewasz
   błąd, odnotuj go w komentarzu testu i zgłoś właścicielowi; nie „naprawiaj”
   przy okazji, bo ktoś może zależeć od obecnego zachowania.
2. Pokryj przypadki brzegowe: wejście puste, wartości skrajne, ścieżki błędów,
   wyjątki. Miarą wystarczalności siatki jest pokrycie gałęzi zmienianego
   fragmentu, nie całego pliku.
3. Dla wyników złożonych (dokumenty, duże struktury) stosuj testy zatwierdzeniowe
   (approval/golden master): zrzuć pełny wynik do pliku wzorcowego i porównuj
   z nim w kolejnych uruchomieniach.
4. Dopiero na zielonej siatce prowadź zmianę. Po zmianie funkcjonalnej świadomie
   zaktualizuj te testy charakteryzujące, których zachowanie miało się zmienić —
   każdą taką aktualizację umiej uzasadnić.

Jeżeli kodu nie da się wywołać w teście (zależności od sieci, zegara, globalnego
stanu), najpierw wprowadź szew — technika opisana w karcie
`references/budowa-kodu/rzemioslo-refaktoryzacji.md`.

## Budowa pod kontraktem (contract-first)

Gdy budujesz punkt styku między systemami lub zespołami, ustal kontrakt przed
implementacją: schemat OpenAPI dla API HTTP, plik `.proto` dla gRPC, schemat
JSON/Avro dla komunikatów, DDL dla współdzielonych tabel.

- Kontrakt jest artefaktem pierwszym: wersjonowany w repozytorium, przeglądany
  jak kod, zmieniany świadomie. Implementacja podąża za kontraktem, nie odwrotnie —
  unikaj generowania schematu z kodu jako źródła prawdy, bo wtedy przypadkowa
  zmiana kodu po cichu zmienia kontrakt.
- Z kontraktu generuj, co się da: typy, klientów, walidatory, atrapy serwera.
  Wygenerowanego kodu nie edytuj ręcznie; regeneruj przy zmianie schematu.
- Dzięki atrapie z kontraktu obie strony budują równolegle: konsument pracuje
  na atrapie, dostawca na testach zgodności ze schematem. To jedyny układ,
  w którym plaster poziomy „najpierw cały schemat” jest wprost pożądany.
- Zmiany kontraktu prowadź zgodnie z zasadą rozszerzania: dodawaj pola opcjonalne,
  nie zmieniaj znaczenia istniejących, usuwaj dopiero po okresie wycofania.
  Zmiana łamiąca wymaga nowej wersji kontraktu i uzgodnienia z konsumentami.

## Sterowanie budową testami — tam, gdzie się opłaca

Pisanie testu przed kodem (TDD) traktuj jako narzędzie, nie dogmat. Opłaca się
wyraźnie, gdy:

- logika ma charakter algorytmiczny lub przekształceniowy (parsowanie, wyliczenia,
  reguły domenowe) — test przed kodem wymusza przemyślenie interfejsu i przypadków
  brzegowych, zanim powstanie implementacja;
- naprawiasz błąd — najpierw test odtwarzający błąd (czerwony), potem poprawka
  (zielony); taki test zostaje jako strażnik przed regresją;
- zachowanie da się opisać własnościami. Testy własnościowe (property-based,
  np. Hypothesis w Pythonie, fast-check w JS) sprawdzają niezmienniki na setkach
  wejść generowanych losowo: „deserializacja(serializacja(x)) == x”, „wynik
  sortowania jest uporządkowany i jest permutacją wejścia”, „suma pozycji równa
  się kwocie faktury”. Jedna dobra własność wykrywa przypadki brzegowe, których
  ręcznie nikt nie wypisze.

Opłaca się słabo przy kodzie sklejającym (przepisywanie pól, wywołania delegujące)
i przy interfejsie użytkownika w fazie szkicowania — tam testuj po ustabilizowaniu
kształtu, na poziomie zachowań, nie piksli. Niezależnie od kolejności pisania
obowiązuje minimum z procedury głównej: każdy przyrost kończy się kodem
sprawdzonym uruchomieniem lub testem.

## Praca z generatorem kodu i modelem AI

Kod z generatora (w tym z modelu językowego) traktuj jak kod od nieznanego
współpracownika o nierównej formie: bywa świetny, bywa przekonująco błędny.

- **Zakaz wklejania niezrozumianego kodu.** Każdy przyjęty fragment musisz umieć
  wyjaśnić linia po linii: co robi, dlaczego tak, co się stanie przy błędzie.
  Fragment, którego nie rozumiesz, odrzuć albo rozłóż na mniejsze i zrozum.
- Weryfikuj wywołania interfejsów w źródle: modele mieszają wersje bibliotek
  i wymyślają nieistniejące funkcje o wiarygodnych nazwach. Sygnatura
  niepotwierdzona w dokumentacji lub kodzie biblioteki nie wchodzi do projektu.
- Generuj małymi porcjami pod istniejącą strukturę — jedna funkcja, jeden test —
  zamiast prosić o cały moduł. Duże porcje przemycają zależności, style
  i abstrakcje sprzeczne z projektem.
- Kod wygenerowany podlega tym samym bramkom co ręczny: analiza statyczna,
  testy, przegląd. Szczególnie sprawdzaj obszary, gdzie generatory statystycznie
  błądzą: obsługa błędów (przemilczana), przypadki brzegowe (puste kolekcje,
  strefy czasowe, kodowanie znaków), współbieżność, bezpieczeństwo (sklejanie
  zapytań SQL, obsługa ścieżek plików).
- Dla powtarzalnych generatorów (klienci z OpenAPI, kod z `.proto`) — patrz
  „Budowa pod kontraktem”: generat regenerowalny nie podlega edycji ręcznej,
  w odróżnieniu od kodu z modelu, który z chwilą przyjęcia staje się zwykłym
  kodem projektu z pełną odpowiedzialnością autora.

## Najmniejszy krok wdrażalny

Zasada nadrzędna spinająca wszystkie powyższe: **każda rewizja pozostawia system
zdatny do wdrożenia**. Nie „skompilowalny”, lecz wdrażalny: testy przechodzą,
migracje są odwracalne lub zgodne wstecznie, funkcja niedokończona jest ukryta
za przełącznikiem, kontrakty nie są złamane.

Praktyczne konsekwencje:

- Zmianę zbyt dużą na jeden krok wdrażalny tnij technikami rozwijania: najpierw
  dodaj nowe obok starego (expand), przełącz użycia, potem usuń stare (contract).
  Dotyczy to kolumn bazy (dodaj kolumnę → podwójny zapis → migracja danych →
  przełącz odczyt → usuń starą), pól API i funkcji.
- Migracja bazy i wdrożenie kodu to osobne kroki: schemat po migracji musi
  działać ze starym kodem (na wypadek wycofania wdrożenia), a nowy kod ze starym
  schematem (na czas trwania wdrożenia kroczącego).
- Jeżeli nie umiesz wskazać, jak wycofać rewizję w razie awarii, krok jest
  za duży — potnij go.

Test końcowy każdej techniki z tej karty jest ten sam: czy w dowolnym momencie
budowy można przerwać pracę i przekazać system w stanie działającym? Jeżeli nie —
wróć do najmniejszego kroku wdrażalnego.
