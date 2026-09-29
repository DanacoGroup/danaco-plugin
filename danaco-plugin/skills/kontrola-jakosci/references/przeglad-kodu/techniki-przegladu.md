# Techniki przeglądu — warsztat przeglądającego

Karta rozwija procedurę z `references/przeglad-kodu/przeglad-kodu.md`. Opisuje sposób prowadzenia
przeglądu: od czego zacząć czytanie, jak śledzić dane nieufne, jak dobrać głębokość przeglądu do
ryzyka i jak komunikować ustalenia. Techniki stosuj łącznie z katalogiem usterek
(`references/przeglad-kodu/katalog-usterek.md`) i kartą językową
(`references/przeglad-kodu/przeglad-wg-jezykow.md`).

## 1. Kolejność czytania zmiany — strategia według rodzaju zmiany

Nie czytaj diffu plik po pliku w kolejności alfabetycznej — dobierz punkt
wejścia do rodzaju zmiany:

- **Nowa funkcjonalność:** zacznij od kontraktu — sygnatury publicznych
  funkcji, definicji punktów końcowych API, schematu danych. Oceń, czy kontrakt
  jest właściwy, zanim ocenisz implementację; zła implementacja dobrego
  kontraktu to poprawka, dobry kod na złym kontrakcie to przebudowa. Następnie
  przeczytaj testy — mówią, co autor uważa za zachowanie obiecane. Dopiero
  potem implementację, śledząc jeden pełny przepływ od wejścia do wyjścia.
- **Poprawka błędu:** zacznij od testu odtwarzającego błąd. Jeżeli go nie ma —
  to pierwsze ustalenie przeglądu. Sprawdź, czy poprawka usuwa przyczynę, czy
  objaw: poprawka warunku w jednym miejscu przy przyczynie leżącej w danych
  wróci w innym miejscu. Wyszukaj inne wystąpienia tego samego wzorca w kodzie —
  błąd rzadko występuje raz.
- **Refaktoryzacja:** najpierw upewnij się, że zmiana deklarowana jako
  refaktoryzacja rzeczywiście nie zmienia zachowania — porównaj testy przed
  i po (powinny przejść bez modyfikacji; zmodyfikowane testy w „czystej
  refaktoryzacji” to sygnał ostrzegawczy). Czytaj parami stare–nowe, szukając
  różnic w obsłudze przypadków brzegowych.
- **Zmiana konfiguracji lub zależności:** przeczytaj dziennik zmian
  podnoszonej zależności (zmiany łamiące, poprawki bezpieczeństwa), sprawdź
  wpływ nowych wartości domyślnych. Mała objętość diffu nie znaczy małego
  ryzyka — jedna linia w konfiguracji potrafi wyłączyć uwierzytelnianie.
- **Migracja bazy danych:** czytaj według sekcji 7 tej karty, przed kodem
  aplikacji, który z niej korzysta.

Niezależnie od rodzaju zmiany: przeczytaj opis zmiany i porównaj z diffem.
Kod obecny w diffie, a nieobjęty opisem, wymaga wyjaśnienia — to częste
miejsce przemyconych zmian ubocznych.

## 2. Śledzenie przepływu danych nieufnych

Technika podstawowa dla sprawdzeń bezpieczeństwa. Wykonaj dla każdego nowego
lub zmienionego punktu wejścia:

1. **Zidentyfikuj źródła:** parametry żądania HTTP (ścieżka, zapytanie, treść,
   nagłówki, ciasteczka), pliki od użytkownika, komunikaty z kolejek, odpowiedzi
   zewnętrznych API, dane z bazy zapisane wcześniej przez użytkowników
   (nieufne w drugim obiegu — stored XSS), zmienne środowiskowe w kodzie
   uruchamianym u klienta.
2. **Zidentyfikuj ujścia:** zapytanie SQL, polecenie powłoki, ścieżka pliku,
   treść HTML, nagłówek odpowiedzi, adres żądania wychodzącego, deserializator,
   log, `eval`/refleksja.
3. **Prześledź każdą ścieżkę źródło→ujście** i zaznacz punkty kontroli:
   gdzie dane są walidowane (kształt), sanityzowane (treść), ucieczkowane
   (kontekst ujścia). Kontrola musi być dobrana do ujścia — ucieczkowanie HTML
   nie chroni przed wstrzyknięciem SQL i odwrotnie.
4. **Sprawdź obejścia:** czy każda ścieżka przechodzi przez punkt kontroli,
   czy istnieje ścieżka boczna (drugi punkt końcowy, zadanie w tle, import CSV)
   omijająca walidację; czy kontrola biegnie po stronie serwera (kontrola tylko
   w przeglądarce nie jest kontrolą); czy dane po walidacji nie są ponownie
   modyfikowane przed ujściem.

Ustalenie z tej techniki formułuj jako ścieżkę: „dane z X trafiają do Y bez
kontroli Z w punkcie W” — z plikami i wierszami dla każdego ogniwa.

## 3. Przegląd granic zaufania

Wypisz, co w zmianie przekracza granicę procesu, sieci lub uprawnień:
nowy punkt końcowy, nowe wywołanie zewnętrznej usługi, nowy odczyt pliku,
nowy parametr istniejącego API, poszerzenie uprawnień konta usługowego.
Dla każdego przekroczenia sprawdź:

- **Do środka:** uwierzytelnienie (kto), autoryzacja do zasobu (czy wolno mu do tego konkretnego
  rekordu — patrz IDOR, `references/przeglad-kodu/katalog-usterek.md` A7), walidacja kształtu i
  zakresu, limity rozmiaru i częstości.
- **Na zewnątrz:** co ujawniamy (czy odpowiedź nie zawiera pól nadmiarowych —
  serializacja całej encji zamiast widoku), co się dzieje przy awarii drugiej
  strony (limit czasu, ponowienia, degradacja), czy wywołanie jest idempotentne
  przy ponowieniach.
- **Uprawnienia:** czy kod działa z najmniejszymi uprawnieniami wystarczającymi
  do zadania; poszerzenie uprawnień w konfiguracji wdrożeniowej podlega
  przeglądowi tak samo jak kod.

Zmiana, która nie przekracza żadnej granicy zaufania, z reguły uzasadnia
płytszy przegląd bezpieczeństwa — odnotuj to i przenieś uwagę na poprawność.

## 4. Pytania do autora zamiast zgadywania intencji

Gdy nie rozumiesz, po co fragment istnieje — nie zgaduj i nie zgłaszaj usterki
na podstawie domysłu. Sformułuj pytanie, które rozstrzyga między konkretnymi
hipotezami:

- Zamiast „ten warunek wygląda podejrzanie”: „Warunek w wierszu 42 pomija
  rekordy ze statusem `draft`. Czy to zamierzone dla tego raportu, czy warunek
  przeniesiony z widoku publicznego?”.
- Zamiast „po co ta blokada?”: „Czy `lock` w wierszu 80 chroni przed
  równoległym wywołaniem z zadania cyklicznego, czy przed czymś innym? Jeśli
  to pierwsze — zadanie biegnie w osobnym procesie i blokada w pamięci go nie
  obejmie”.

Dobre pytanie zawiera obserwację (fakt z kodu) i hipotezy do wyboru — autor
odpowiada w minutę, a odpowiedź często ujawnia usterkę precyzyjniej niż
zgadywanie. Pytania odnotuj w raporcie w osobnej sekcji „do wyjaśnienia”,
nie mieszaj ich z usterkami potwierdzonymi.

## 5. Przegląd zmian szerokich — oddzielanie szumu od treści

Zmiany wygenerowane (kod z generatorów, migracje automatyczne, pliki blokady
zależności), masowe formatowanie i masowe zmiany nazw zalewają diff tysiącami
wierszy mechanicznych. Nie czytaj ich wiersz po wierszu — i nie zatwierdzaj
w ciemno. Procedura:

1. **Rozdziel warstwy.** Zażądaj (lub wykonaj lokalnie) rozdzielenia zmiany
   mechanicznej od merytorycznej na osobne rewizje. Jeżeli są zmieszane —
   to samo w sobie jest ustaleniem: zmiana merytoryczna ukryta w formatującej
   jest nieprzeglądalna.
2. **Zweryfikuj skryptem, że reszta jest mechaniczna.** Dla formatowania:
   uruchom formater na wersji bazowej i porównaj wynik z wersją zgłoszoną
   (`diff` powinien być pusty). Dla zmiany nazw: `git diff --word-diff` albo
   wyszukiwanie potwierdzające, że różnice ograniczają się do zamienianego
   symbolu. Dla plików generowanych: wygeneruj ponownie ze źródła i porównaj.
   Diff niezerowy wskazuje dokładnie miejsca wymagające ludzkiego oka.
3. **Przegląd wybiórczy z próbkowaniem.** Gdy weryfikacja skryptem jest
   niewykonalna, przejrzyj próbkę losową (np. 10% plików, minimum 5) w pełnej
   głębokości plus wszystkie pliki z obszarów krytycznych (uwierzytelnianie,
   płatności, migracje). Znalezienie w próbce choć jednej zmiany
   niemechanicznej unieważnia założenie mechaniczności — wróć do punktu 1.
4. **W raporcie napisz wprost**, którą część przejrzano w pełni, którą
   zweryfikowano skryptem, a którą próbkowano — czytelnik raportu musi znać
   pokrycie przeglądu.

## 6. Przegląd kodu wygenerowanego przez model LLM

Kod z modelu przeglądaj według tych samych kryteriów co ludzki — plus
sygnatury typowe dla generacji, które kieruj do sprawdzenia w pierwszej
kolejności:

- **API z innej wersji biblioteki:** wywołania metod nieistniejących
  w wersji z pliku zależności projektu, mieszanie składni dwóch wersji
  frameworka, importy z pakietów o zmienionej strukturze. Sprawdź każde
  wywołanie zewnętrznego API, którego nie rozpoznajesz, z dokumentacją wersji
  zadeklarowanej w projekcie — kod mógł nigdy nie zostać uruchomiony.
- **Nadmiarowa obrona:** sprawdzanie `None`/typów wartości, które w tym miejscu
  nie mogą być puste, `try` wokół kodu, który nie rzuca, walidacja powtórzona
  z warstwy wyżej. Zaciemnia przepływ i maskuje prawdziwe błędy (szeroki
  `except` połyka usterkę logiczną). Żądaj usunięcia obrony bez scenariusza,
  który przed czymś chroni.
- **Komentarze-parafrazy:** komentarz powtarzający treść wiersza
  („zwiększ licznik o 1”). Usuwać; sprawdź przy okazji, czy pod parafrazami
  nie zniknęły komentarze „dlaczego” z kodu zastanego.
- **Styl niespójny z projektem:** inna konwencja nazw, inna biblioteka do
  zadania już rozwiązanego w projekcie (druga biblioteka HTTP, własny parser
  zamiast istniejącego), wzorce z innego ekosystemu. Egzekwuj konwencję
  projektu.
- **Testy pozorne:** wygenerowane testy często mockują testowaną logikę albo
  assertują to, co wpisano w mock — stosuj sekcję 8 tej karty ze zdwojoną
  uwagą.
- **Pewny ton bez pokrycia:** opis zmiany i komentarze generowane brzmią
  pewnie niezależnie od poprawności — nie skracaj przeglądu dlatego, że kod
  „wygląda profesjonalnie”.

## 7. Przegląd migracji bazy danych

Migracje przeglądaj surowiej niż kod aplikacji — błędna migracja na produkcji
jest trudno odwracalna i psuje dane trwale. Sprawdź:

- **Odwracalność:** czy istnieje ścieżka powrotu (migracja w dół albo
  udokumentowana procedura); operacje tracące dane (`DROP COLUMN`, zwężenie
  typu, `DELETE`) wymagają jawnego potwierdzenia, że dane są zbędne lub
  zarchiwizowane. Wycofanie kodu bez wycofania migracji musi pozostawiać
  działający system — stara wersja aplikacji ma działać na nowym schemacie
  (zgodność w obie strony przez jedno wydanie).
- **Blokady:** które operacje biorą blokadę wyłączną na tabeli i na jak długo
  przy produkcyjnym rozmiarze danych. Typowe pułapki: `ALTER TABLE` przepisujące
  tabelę, `CREATE INDEX` bez `CONCURRENTLY` (PostgreSQL), dodanie kolumny
  z domyślną wartością nieustaloną (starsze wersje silników przepisują tabelę),
  zmiana typu kolumny. Długa blokada na gorącej tabeli to przestój usługi.
- **Dane zastane:** czy migracja obsługuje dane już obecne — `NOT NULL` na
  kolumnie z istniejącymi NULL padnie w trakcie; ograniczenie unikalności na
  danych z duplikatami wymaga wcześniejszego czyszczenia; aktualizacja masowa
  (backfill) milionów wierszy w jednej transakcji rozdyma dziennik transakcji
  i blokuje replikację — żądaj partii.
- **Kolejność wdrożenia:** czy kod i migracja mogą wjechać w dowolnej
  kolejności; wzorzec bezpieczny dla zmian łamiących: dodaj nowe → pisz w oba →
  przenieś odczyt → przestań pisać w stare → usuń stare (każdy krok osobnym
  wydaniem).

## 8. Przegląd testów — czy test czegokolwiek dowodzi

Test podlega przeglądowi jak kod produkcyjny, według innego pytania:
co ten test udowadnia i czy wykryje regresję?

- **Asercje:** test bez asercji (albo z asercją zawsze prawdziwą,
  `assert result is not None` wobec funkcji, która nie zwraca None) dowodzi
  tylko braku wyjątku. Sprawdź, czy asercja porównuje z wartością oczekiwaną
  wyliczoną niezależnie, a nie z wynikiem tej samej logiki (test tautologiczny:
  oczekiwana wartość liczona tą samą funkcją, którą testujemy).
- **Mocki:** czy mock nie zastępuje testowanej logiki — test, który mockuje
  repozytorium i asserta, że kontroler zwraca to, co zwrócił mock, testuje
  framework, nie kod. Mockuj granice (sieć, zegar, losowość), nie środek.
- **Niezależność:** test zależny od kolejności wykonania, stanu z poprzedniego
  testu, bieżącej daty, strefy czasowej maszyny lub sieci będzie migotał —
  a testy migoczące zespół nauczy się ignorować, co unieważnia całą sieć
  bezpieczeństwa. Szukaj: współdzielonych fixture'ów modyfikowanych w testach,
  `sleep` jako synchronizacji, zapisów do wspólnej bazy bez izolacji.
- **Dane brzegowe:** czy przypadki brzegowe z sekcji „Poprawność” procedury
  `references/przeglad-kodu/przeglad-kodu.md` mają odzwierciedlenie w testach — pusta kolekcja,
  zero, wartość ujemna, tekst z polskimi znakami, granice zakresów. Test wyłącznie „ścieżki
  szczęśliwej” pokrywa najmniej ryzykowną część kodu.
- **Zmiany w testach istniejących:** każda modyfikacja lub usunięcie asercji
  w istniejącym teście wymaga uzasadnienia w opisie zmiany — osłabienie testu,
  by przechodził, to antywzorzec, który przegląd musi wychwycić.

## 9. Kalibracja głębokości przeglądu według ryzyka

Czas przeglądu jest ograniczony — rozdzielaj go według macierzy
**zasięg × krytyczność obszaru**:

| | Obszar krytyczny (uwierzytelnianie, płatności, uprawnienia, migracje, przetwarzanie danych osobowych) | Obszar standardowy (logika dziedzinowa, API wewnętrzne) | Obszar niskiego ryzyka (narzędzia deweloperskie, teksty, style) |
|---|---|---|---|
| **Zasięg szeroki** (nowy moduł, zmiana kontraktu, >300 wierszy logiki) | Przegląd pełny: śledzenie przepływów danych, granice zaufania, uruchomienie kodu, przegląd testów; rozważ drugiego przeglądającego | Przegląd pełny bez uruchamiania każdej ścieżki; pełne sprawdzenie katalogu usterek | Przegląd strukturalny + próbkowanie |
| **Zasięg średni** (zmiana zachowania w istniejącym module) | Przegląd pełny w obrębie zmiany + styki z resztą obszaru | Standardowa procedura z `references/przeglad-kodu/przeglad-kodu.md` | Szybki przegląd sygnatur z karty językowej |
| **Zasięg wąski** (poprawka lokalna, kilka wierszy) | Pełne sprawdzenie zmiany + pytanie, czemu obszar krytyczny zmieniany jest poprawką wąską | Sprawdzenie poprawności i testu regresji | Przegląd minimalny |

Dwie reguły nadrzędne: krytyczność obszaru wygrywa z rozmiarem diffu (jedna
linia w kodzie uwierzytelniania zasługuje na głęboki przegląd), a deklarowany
rodzaj zmiany trzeba zweryfikować, nie przyjąć na wiarę (patrz sekcja 1 —
„refaktoryzacja” bywa zmianą zachowania).

## 10. Higiena komunikacji ustaleń

Sposób zakomunikowania ustaleń decyduje, czy przegląd poprawi kod, czy
wywoła spór. Zasady:

- **Struktura ustalenia: fakt → skutek → propozycja.** Najpierw obserwacja
  weryfikowalna („zapytanie w wierszu 30 wykonuje się w pętli po zamówieniach”),
  potem skutek ze scenariuszem („przy 200 zamówieniach to 201 zapytań; strona
  listy przekroczy limit czasu”), na końcu propozycja najmniejszej poprawki
  („jedno zapytanie z `WHERE order_id IN (...)`”). Ustalenie bez skutku to
  opinia; ustalenie bez propozycji zrzuca całą pracę na autora.
- **Rozdziel kategorie wagi** i nazwij je wprost: **blokujące** (usterka do
  naprawy przed scaleniem — z uzasadnieniem, czemu blokuje), **zalecenia**
  (warto poprawić, dopuszczalne w osobnej zmianie), **drobne** (oznaczaj
  jawnie, np. „drobiazg:”; autor może pominąć bez dyskusji). Przegląd,
  w którym wszystko jest blokujące, uczy ignorowania wag.
- **Komentuj kod, nie autora:** „ta funkcja nie obsługuje pustej listy”,
  nie „nie obsłużyłeś pustej listy”. Pytania formułuj według sekcji 4.
- **Zakaz uwag smakowych sprzecznych z konwencją projektu:** styl zgodny
  z konwencją zastaną nie podlega uwagom, nawet gdy przeglądający preferuje
  inny. Spory o styl rozstrzyga konfiguracja formatera i lintera — zaproponuj
  regułę zamiast komentować ręcznie ten sam wzorzec po raz trzeci.
- **Uznaj rozwiązania dobre:** krótka wzmianka przy nieoczywistym dobrym
  rozwiązaniu kalibruje wagę pozostałych uwag i utrwala dobre wzorce.
- **Wynik czysty komunikuj wprost:** „przegląd bez ustaleń blokujących” to
  pełnoprawny wynik — nie dopisuj uwag drobnych na siłę, by przegląd
  „coś znalazł”.
