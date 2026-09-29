# Dokumentacja API, runbook i przewodnik wdrożeniowy

Karta podaje warsztat trzech rodzajów dokumentów wykonawczych: dokumentacji API
ponad schematem, runbooka klasy operacyjnej oraz przewodnika wdrożeniowego
on-premise. Wspólny mianownik: te dokumenty są wykonywane, nie tylko czytane —
każde twierdzenie musi przejść próbę wykonania.

## 1. Dokumentacja API ponad schemat

Schemat (OpenAPI generowany z kodu) jest źródłem prawdy o kształcie żądań
i odpowiedzi — nie powtarzaj go ręcznie, bo kopia się zestarzeje. Dokument
ręczny opisuje wyłącznie to, czego schemat nie niesie; poniższe sekcje
wyczerpują tę listę.

### 1.1. Scenariusze wielokrokowe i kolejność wywołań

Klient API nie wywołuje pojedynczych endpointów — realizuje zadania złożone
z sekwencji wywołań. Dla każdego zadania, które klient wykonuje naprawdę
(rejestracja zasobu, przetworzenie zlecenia od utworzenia po odbiór wyniku),
opisz scenariusz: kolejność wywołań, dane przenoszone z odpowiedzi jednego
wywołania do żądania następnego, punkty, w których klient czeka lub odpytuje.
Scenariusz podaje, które kroki są obowiązkowe, a które warunkowe, oraz co
scala stan po stronie serwera między krokami (identyfikator sesji, token
kontynuacji). Endpoint nieobecny w żadnym scenariuszu jest podejrzany —
albo brakuje scenariusza, albo endpointu nie potrzeba.

### 1.2. Idempotentność i ponawianie

Udokumentuj kontrakt ponawiania — bez niego każdy klient wymyśla własny
i część z nich duplikuje operacje:

- dla każdej operacji zmieniającej stan: czy powtórzenie tego samego żądania
  jest bezpieczne; jeśli tak — co to gwarantuje (klucz idempotentności
  w nagłówku, naturalna idempotentność operacji), jeśli nie — jak klient
  wykrywa, czy pierwotne żądanie doszło do skutku;
- okno ważności klucza idempotentności i zachowanie serwera przy powtórzeniu
  z tym samym kluczem, lecz inną treścią żądania;
- zalecana strategia ponawiania: które kody odpowiedzi ponawiać, z jakim
  odstępem (rosnącym, z losowym rozrzutem), po ilu próbach się poddać;
- których kodów **nie** ponawiać nigdy (błędy walidacji, brak uprawnień) —
  ponawianie ich obciąża serwer bez szans powodzenia.

### 1.3. Paginacja

Podaj model paginacji (strony numerowane albo kursor/token kontynuacji),
parametry i ich limity, oraz gwarancje spójności: co widzi klient, gdy zbiór
zmienia się między pobraniem stron — czy elementy mogą się powtórzyć lub
zniknąć. Opisz warunek końca (pusta strona, brak tokenu kontynuacji, pole
łącznej liczby) i termin ważności kursora. Przykład przejścia pełnej kolekcji
umieść w scenariuszu (1.1), nie w opisie parametru.

### 1.4. Wersjonowanie i wygaszanie

Kontrakt wersjonowania obejmuje: sposób wskazania wersji przez klienta
(segment ścieżki, nagłówek), definicję zmiany zgodnej (dodanie pola
odpowiedzi, nowy endpoint) i niezgodnej (usunięcie lub zmiana znaczenia
pola, zmiana kodu odpowiedzi), oraz procedurę wygaszania: kanał zapowiedzi,
minimalny okres równoległego działania wersji, sposób sygnalizowania
wygaszania w odpowiedziach, zachowanie po wyłączeniu wersji. Zobowiązanie
dla klientów zapisz wprost: klient ma tolerować pola nieznane — to warunek,
by dodanie pola było zmianą zgodną.

### 1.5. Przykłady wykonane naprawdę

Każdy przykład żądania i odpowiedzi w dokumencie pochodzi z rzeczywistego
wykonania przeciw działającej instancji — nigdy z ręcznego ułożenia „jak to
powinno wyglądać”. Ułożony przykład rozmija się z rzeczywistością w polach,
których autor nie pamiętał, i uczy klientów błędnego kontraktu. Procedura:
wykonaj wywołanie, wklej odpowiedź dosłownie, zanonimizuj wyłącznie wartości
wrażliwe (tokeny, dane osobowe) — zachowując format i długość pól. Przy
aktualizacji dokumentu wykonaj przykłady ponownie; przykład, którego nie da
się odtworzyć, oznacz i wyjaśnij albo usuń.

### 1.6. Błędy jako kontrakt

Odpowiedzi błędne są częścią kontraktu równie wiążącą jak poprawne — klient
programuje obsługę błędów na podstawie tej tabeli, nie na podstawie zgadywania.
Dla każdego kodu podaj trzy kolumny: przyczynę (co po stronie żądania lub stanu
serwera wywołuje błąd), zawartość odpowiedzi (format ciała błędu — jednolity
dla całego API) oraz **działanie klienta** — kolumnę najczęściej pomijaną,
a najcenniejszą:

| Klasa odpowiedzi | Przyczyna | Działanie klienta |
|---|---|---|
| Błąd walidacji | Żądanie niezgodne z kontraktem — usterka klienta. | Popraw żądanie; nie ponawiaj bez zmiany. Wyświetl użytkownikowi wskazane pola. |
| Brak uwierzytelnienia | Token nieobecny lub wygasły. | Odśwież token i powtórz raz; przy ponownym niepowodzeniu — przejdź do logowania. |
| Brak uprawnień | Tożsamość poprawna, operacja niedozwolona. | Nie ponawiaj; pokaż odmowę. Ponawianie nie zmieni uprawnień. |
| Konflikt stanu | Zasób zmieniony równolegle albo operacja już wykonana. | Pobierz stan bieżący, rozstrzygnij, czy operacja nadal potrzebna. |
| Przekroczenie limitu | Zbyt wiele żądań. | Odczekaj czas wskazany w odpowiedzi; ponów z rosnącym odstępem. |
| Błąd serwera | Usterka lub niedostępność po stronie serwera. | Ponów według strategii z 1.2; po wyczerpaniu prób zgłoś niedostępność. |

Tabelę wypełnij rzeczywistymi kodami i formatami swojego API; klasy powyżej są
szkieletem, nie gotową treścią. Błędy specyficzne dla pojedynczych endpointów
dokumentuj przy endpointach, błędy wspólne — raz, w rozdziale ogólnym,
z odsyłaczami.

## 2. Runbook klasy operacyjnej

Runbook jest procedurą pisaną dla wykonawcy działającego pod presją — często
w nocy, w awarii, bez autora pod ręką. Kryterium jakości: osoba znająca system
powierzchownie wykonuje procedurę od początku do końca bez zadawania pytań.

### 2.1. Struktura obowiązkowa

1. **Cel** — jedno zdanie: co procedura osiąga i po czym poznać, że jest
   potrzebna (objawy, alarm, wpis monitoringu).
2. **Warunki wstępne** — uprawnienia i dostępy (z nazwami systemów, do których
   trzeba się zalogować), narzędzia, stan systemu wymagany przed startem,
   szacowany czas wykonania i okno, w którym wykonanie jest bezpieczne.
   Osobno: czy procedura przerywa działanie usługi i na jak długo.
3. **Kroki** — według warsztatu procedur (karta
   `references/dokumentacja-techniczna/warsztat-pisarski.md`, rozdz. 5): tryb rozkazujący, kroki
   atomowe, polecenia dosłowne w blokach kodu, **wynik oczekiwany po każdym kroku** (dosłowny
   komunikat lub stan).
4. **Diagnoza niepowodzenia każdego kroku** — przy każdym kroku albo w tabeli
   zbiorczej: co oznacza brak wyniku oczekiwanego, jak to sprawdzić, czy
   kontynuować, powtórzyć krok, przejść do wycofania, czy eskalować. Krok bez
   ścieżki niepowodzenia zostawia wykonawcę z systemem w stanie pośrednim
   i bez instrukcji — to najgroźniejsza luka runbooka.
5. **Wycofanie** — kompletna procedura powrotu do stanu sprzed startu, ze
   wskazaniem **punktu bez powrotu**: kroku, po którym wycofanie przestaje być
   możliwe i pozostaje wyłącznie droga naprzód lub odtworzenie z kopii.
   Wykonawca musi znać ten punkt przed startem, nie odkryć go w trakcie.
6. **Eskalacja** — kiedy przerwać samodzielne próby (po jakim czasie, po jakim
   objawie), do jakiej roli eskalować i jakim kanałem, jakie informacje
   przekazać (wykonane kroki, wyniki, stan bieżący). Eskalacja wskazuje role,
   nie nazwiska — nazwiska się starzeją.

### 2.2. Test runbooka przez wykonanie

Runbook niesprawdzony jest groźniejszy niż jego brak — daje fałszywą pewność
i zawodzi w najgorszym momencie. Przed dopuszczeniem do użytku:

1. Wykonaj procedurę krok po kroku na środowisku możliwie bliskim
   produkcyjnemu, wklejając polecenia dosłownie z dokumentu — nie z pamięci.
2. Każdą rozbieżność między wynikiem oczekiwanym a rzeczywistym popraw
   w dokumencie natychmiast, nie „po przejściu całości”.
3. Wykonaj także procedurę wycofania — wycofanie nietestowane to dekoracja.
4. Docelowo zleć wykonanie osobie innej niż autor: autor nieświadomie uzupełnia
   luki własną wiedzą, wykonawca obcy je ujawnia.
5. Po każdym użyciu bojowym odnotuj rozbieżności i nanieś poprawki — runbook,
   który zawiódł w awarii i nie został poprawiony, zawiedzie ponownie.

### 2.3. Runbook awarii a runbook rutyny

Oba rodzaje dzielą strukturę z 2.1, lecz różnią się rozkładem akcentów:

| Cecha | Runbook rutyny (kopia zapasowa, rotacja sekretów, aktualizacja) | Runbook awarii (niedostępność, utrata danych, incydent) |
|---|---|---|
| Punkt wejścia | Harmonogram lub decyzja planowa. | Objaw — dokument zaczyna się od rozpoznania: tabela „objaw → prawdopodobna przyczyna → właściwa sekcja”. |
| Struktura kroków | Liniowa, przewidywalna. | Rozgałęziona: diagnoza zawęża przyczynę, potem właściwa ścieżka naprawy. |
| Priorytet | Powtarzalność i kompletność. | Czas do przywrócenia usługi: najpierw działania przywracające, potem naprawa przyczyny źródłowej. Rozdziel te fazy wprost. |
| Ton i objętość kroków | Może odsyłać do dokumentacji. | Samowystarczalny — w awarii nie ma czasu na lekturę odsyłaczy; wszystko potrzebne stoi w kroku. |
| Zbieranie śladów | Zbędne poza logiem wykonania. | Obowiązkowy krok zabezpieczenia śladów (logi, zrzuty stanu) **przed** działaniami, które je nadpiszą. |

## 3. Przewodnik wdrożeniowy on-premise

Przewodnik wdrożeniowy prowadzi administratora klienta przez instalację systemu
w środowisku, którego autor nie zna i nie kontroluje. Stąd dwie zasady
nadrzędne: żadnych założeń niewypowiedzianych o środowisku oraz weryfikacja
po każdym etapie — błąd wykryty dwa etapy później jest niediagnozowalny
u klienta zdalnie.

### 3.1. Wymagania środowiska

Wypisz wymagania kompletnie i mierzalnie, w tabelach:

- **Sprzęt i zasoby**: procesor, pamięć, dysk (z zapasem na przyrost danych —
  podaj regułę szacowania), przepustowość sieci; wartości minimalne
  i zalecane osobno.
- **System operacyjny i oprogramowanie**: nazwy i wersje — jako przedziały
  wersji przetestowanych, nie „najnowsza”; biblioteki i usługi wymagane
  wcześniej (baza danych, środowisko uruchomieniowe).
- **Sieć**: porty nasłuchu i połączeń wychodzących z przeznaczeniem każdego,
  wymagane wpisy DNS, certyfikaty; zachowanie systemu w środowisku bez dostępu
  do internetu — dla on-premise to przypadek główny, nie brzegowy.
- **Uprawnienia i konta**: konta systemowe do utworzenia, wymagane uprawnienia
  administracyjne z uzasadnieniem każdego — administrator klienta ma prawo
  zapytać, po co proces potrzebuje danego uprawnienia.

Zamknij rozdział procedurą sprawdzenia wymagań: poleceniami, którymi
administrator potwierdza każde wymaganie przed rozpoczęciem instalacji.

### 3.2. Kolejność instalacji z weryfikacją etapów

Instalację podziel na etapy zamknięte weryfikacją; typowa kolejność: przygotowanie
środowiska → składniki wymagane (baza, usługi) → instalacja aplikacji →
konfiguracja → inicjalizacja danych → uruchomienie usług → włączenie do
monitoringu i kopii zapasowych. Dla każdego etapu:

1. Kroki instalacyjne według warsztatu procedur (polecenia dosłowne, wyniki
   oczekiwane).
2. **Weryfikacja etapu** — polecenia potwierdzające, że etap się powiódł,
   z dosłownym wynikiem poprawnym; instrukcja brzmi: nie przechodź do
   następnego etapu przed pomyślną weryfikacją bieżącego.
3. Postępowanie przy niepowodzeniu weryfikacji: najczęstsze przyczyny
   i sposób cofnięcia etapu do stanu powtarzalnego.

Konfigurację prowadź przez wypisany komplet parametrów: nazwa, znaczenie,
wartość domyślna, kiedy zmienić. Parametr nieudokumentowany zostanie ustawiony
źle albo wcale.

### 3.3. Lista kontrolna odbioru

Przewodnik zamyka lista kontrolna odbioru — jednoznaczne kryterium, że
wdrożenie jest ukończone i system nadaje się do przekazania do eksploatacji.
Każda pozycja jest sprawdzalna poleceniem lub obserwacją, z wynikiem tak/nie:

- wszystkie usługi systemu uruchomione i uruchamiają się ponownie po restarcie
  maszyny;
- scenariusz przejścia głównego wykonany od początku do końca na danych
  próbnych (logowanie, operacja główna systemu, odczyt wyniku);
- kopia zapasowa wykonana i **odtworzona próbnie** — kopia nieodtworzona nie
  jest kopią;
- monitoring zbiera metryki, a alarm próbny dociera do właściwego kanału;
- dane dostępowe zmienione z wartości instalacyjnych na docelowe, sekrety
  przechowane zgodnie z polityką klienta;
- dokumenty przekazane: parametry instalacji (wypełnione wartości środowiska),
  runbooki eksploatacyjne, kontakt eskalacyjny.

Wynik odbioru odnotowuje protokół z datą i wykonawcą — poza treścią przewodnika,
który pozostaje bezosobowy i wielokrotnego użytku.
