# COBOL — karta

Karta dotyczy języka COBOL według normy ISO/IEC 1989. W praktyce niemal cała praca
w COBOL-u to praca z kodem zastanym (IBM Enterprise COBOL, Micro Focus, Fujitsu);
nowy kod pisz zachowawczo, w stylu zgodnym z otaczającym programem. Do lokalnych
prób i kompilacji poza mainframe stosuj GnuCOBOL.

## Standard stylu i nazewnictwa

- Zachowuj kanoniczny podział programu na cztery działy, w tej kolejności:
  `IDENTIFICATION DIVISION`, `ENVIRONMENT DIVISION`, `DATA DIVISION`,
  `PROCEDURE DIVISION`. Nie pomijaj nagłówków działów obecnych w kodzie zastanym.
- Rozpoznaj format źródła zanim napiszesz pierwszy wiersz. Format stały: kolumny 1–6
  na numerację, kolumna 7 na wskaźnik (`*` komentarz, `-` kontynuacja), Area A od
  kolumny 8 (nagłówki działów, sekcji, akapitów, numery poziomów 01/77), Area B od
  kolumny 12 (instrukcje), granica w kolumnie 72. Format swobodny wymaga dyrektywy
  `>>SOURCE FORMAT FREE` lub odpowiedniej opcji kompilatora. Nie mieszaj formatów.
- Nazwy danych pisz wielkimi literami z myślnikami: `WS-CUSTOMER-NAME`,
  `IN-INVOICE-TOTAL`. Stosuj przedrostki wskazujące pochodzenie (`WS-` dla
  WORKING-STORAGE, `LS-` dla LINKAGE), jeśli program zastany tak robi.
- Definiuj warunki nazwami poziomu 88 zamiast porównań literałowych rozsianych po kodzie:

```cobol
       01  WS-RECORD-STATUS        PIC X.
           88  RECORD-VALID        VALUE "V".
           88  RECORD-REJECTED     VALUE "R".
      *    Warunek czytelny w logice zamiast porownania z literalem
           IF RECORD-VALID
               PERFORM 2100-PROCESS-RECORD
           END-IF
```

- Zamykaj instrukcje jawnymi terminatorami zakresu (`END-IF`, `END-READ`,
  `END-PERFORM`, `END-EVALUATE`) zamiast polegać na kropkach; kropkę stawiaj na końcu
  akapitu. Kropka w środku zagnieżdżenia ucina wszystkie otwarte zakresy naraz.
- Preferuj `EVALUATE` zamiast kaskad `IF`; unikaj `GO TO` i `ALTER` w nowym kodzie.

## Struktura projektu

- Jeden program (`PROGRAM-ID`) na plik; podprogramy wywołuj przez `CALL` z przekazaniem
  danych w `LINKAGE SECTION` przez `USING`.
- Wspólne definicje rekordów trzymaj w copybookach włączanych instrukcją `COPY`;
  katalog copybooków wskazuj kompilatorowi, nie duplikuj definicji rekordów.
- Numeruj akapity `PROCEDURE DIVISION` hierarchicznie (`1000-MAIN`, `2100-READ-INPUT`),
  jeśli taka konwencja panuje w systemie zastanym — spójność ułatwia nawigację.
- Zmiany w kodzie zastanym rób minimalne i miejscowe: nie przeformatowuj całych plików,
  nie zmieniaj formatu źródła, nie „modernizuj” działającej logiki przy okazji poprawki.

## Budowa i zależności

- Do prób lokalnych stosuj GnuCOBOL: `cobc -x program.cob` buduje program wykonywalny,
  `cobc -m` moduł ładowany dynamicznie (uruchamiany przez `cobcrun`).
- Wybieraj dialekt świadomie opcją `-std=` (m.in. `ibm`, `mf`, `cobol2014`, `default`);
  program przenoszony z mainframe kompiluj z `-std=ibm`, aby wychwycić rozjazdy składni.
- Ścieżki copybooków przekazuj opcją `-I` lub zmienną środowiskową `COB_COPY_DIR`.
- Pamiętaj, że kompilacja w GnuCOBOL nie dowodzi zgodności z Enterprise COBOL:
  różnice obejmują funkcje wewnętrzne, zachowania graniczne i integrację z CICS/DB2.
  Ostateczna weryfikacja należy do środowiska docelowego.

## Testy

- COBOL nie ma jednego dominującego frameworka testowego. Podstawowa technika to testy
  charakteryzujące: utrwal pliki wejściowe i wyjściowe działającego programu przed
  zmianą, po zmianie porównaj wyjścia bajt po bajcie (np. `diff`/`cmp`).
- Do testów jednostkowych logiki wydzielonej w podprogramy pisz programy sterujące
  (driver): `CALL` testowanego modułu ze spreparowanymi rekordami w LINKAGE
  i porównanie wyników z oczekiwaniami; niezgodność zgłaszaj niezerowym `RETURN-CODE`.
- Rozważ COBOL Check (projekt Open Mainframe Project) do testów jednostkowych na
  poziomie akapitów, jeśli organizacja go dopuszcza.
- Testuj granice pól: przepełnienie `PIC 9(n)`, obcięcie łańcuchów, wartości ujemne
  w polach bez znaku, rekordy o złej długości.

## Diagnostyka

- Kompiluj wersje diagnostyczne GnuCOBOL z `-Wall -debug -g -fsource-location`;
  `-debug` włącza kontrole wykonania (m.in. indeksy poza zakresem), a program zgłasza
  wtedy błąd z numerem wiersza zamiast cicho psuć dane.
- Program skompilowany przez GnuCOBOL (translacja do C) można debugować w gdb;
  do wglądu doraźnego stosuj `DISPLAY` pól pośrednich, usuwany po diagnozie.
- Czytaj komunikaty o niezgodności danych: nieprawidłowa zawartość pola numerycznego
  (np. spacje w `PIC 9`) to klasyczna przyczyna błędów — sprawdzaj `IF field IS NUMERIC`
  przed arytmetyką na danych z zewnątrz.
- W arytmetyce obsługuj przepełnienia frazą `ON SIZE ERROR`; bez niej wynik zostaje
  obcięty do rozmiaru pola bez żadnego sygnału.

## Typowe błędy modeli LLM w tym języku

1. Mieszanie formatu stałego ze swobodnym: kod zaczynający się w kolumnie 1 wklejony
   do programu w formacie stałym nie skompiluje się lub zmieni znaczenie (kolumna 7).
   Ustal format istniejącego pliku i pisz dokładnie w nim.
2. Przekroczenie kolumny 72 w formacie stałym — kompilator ucina resztę wiersza, co
   bywa błędem cichym (ucięty literał). Łam wiersze wcześniej; literały kontynuuj
   zgodnie z zasadami kontynuacji lub buduj przez `STRING`.
3. Mieszanie dialektów: używanie rozszerzeń Micro Focus lub GnuCOBOL w kodzie dla IBM
   Enterprise COBOL i odwrotnie (odmienne zestawy funkcji `FUNCTION`, klauzul i opcji).
   Trzymaj się konstrukcji obecnych w otaczającym kodzie; nowość weryfikuj kompilacją
   z właściwym `-std=`.
4. Błędne kropki: kropka postawiona wewnątrz `IF` kończy wszystkie otwarte konstrukcje
   i zmienia przepływ sterowania bez błędu kompilacji. Stosuj `END-IF`/`END-EVALUATE`
   i ogranicz kropki do końców akapitów.
5. Traktowanie `PIC` jak typów z języków nowszych: przypisanie dłuższego łańcucha do
   krótszego pola obcina bez ostrzeżenia, a liczba niemieszcząca się w polu traci
   cyfry wiodące. Dobieraj rozmiary pól do danych i używaj `ON SIZE ERROR`.
6. Halucynowane funkcje wewnętrzne lub składnia z innych języków (operatory `==`,
   nawiasy klamrowe, `RETURN` jako zwrot wartości z akapitu). Zwrot z podprogramu
   odbywa się przez pola LINKAGE i `GOBACK`; listę funkcji `FUNCTION` weryfikuj
   w dokumentacji docelowego kompilatora.
7. Użycie słowa zastrzeżonego jako nazwy danych (`DATA`, `COUNT`, `LENGTH`, `STATUS`).
   Lista słów zastrzeżonych jest długa i zależna od dialektu — przy błędzie składni
   w deklaracji podejrzewaj kolizję nazwy i dodaj przedrostek (`WS-COUNT`).
8. Porównywanie pól znakowych bez świadomości dopełnienia spacjami: porównanie
   uzupełnia krótszy operand spacjami, więc `"ABC"` równa się `"ABC   "`. Nie dopisuj
   zbędnego przycinania tam, gdzie logika zastana na tym polega — i odwrotnie.
9. „Ulepszanie” kodu zastanego przy okazji poprawki: przeformatowanie, zmiana nazw,
   zastąpienie `GO TO` strukturą. Każda taka zmiana bez testów charakteryzujących
   to ryzyko regresji w systemie produkcyjnym; ograniczaj diff do istoty zadania.
