# Ocena i utrzymanie architektury — karta

Karta rozwija etap 5 procedury oraz zasadę „architektura ma odpowiadać temu,
co działa”. Stosuj ją przy ocenie propozycji architektury, przeglądach
okresowych, budowie strażników w CI i prowadzeniu rejestru decyzji.

## 1. Scenariusze jakościowe jako narzędzie oceny

Wymagań niefunkcjonalnych nie ocenia się przymiotnikami. „System ma być
wydajny i łatwy w utrzymaniu” nie podlega ocenie; scenariusz jakościowy —
podlega. Zapisuj każdy istotny atrybut jakościowy w układzie:

**bodziec → środowisko → odpowiedź mierzalna**

- *Bodziec* — co się dzieje: żądanie, awaria, zlecenie zmiany, wzrost danych.
- *Środowisko* — w jakich warunkach: praca normalna, szczyt, awaria częściowa,
  system po dwóch latach eksploatacji.
- *Odpowiedź mierzalna* — co system robi i jak to zmierzyć liczbą.

Przykłady wzorcowe:

- **Wydajność:** „Użytkownik zatwierdza fakturę (bodziec) przy pracy
  normalnej, 50 użytkowników równocześnie, baza z 5 lat danych (środowisko);
  system zapisuje i potwierdza w czasie poniżej 2 s dla 99% operacji
  (odpowiedź).” Środowisko z danymi z lat jest tu istotą: system szybki na
  pustej bazie to żaden dowód.
- **Dostępność:** „Serwer poczty klienta przestaje odpowiadać (bodziec)
  w godzinach pracy (środowisko); wystawianie faktur działa bez zakłóceń,
  wiadomości czekają w skrzynce nadawczej i wychodzą po przywróceniu
  łączności, administrator widzi zaległość w panelu (odpowiedź).”
- **Modyfikowalność:** „Właściciel zleca dodanie nowej metody płatności
  (bodziec) w systemie rozwijanym od 3 lat (środowisko); zmiana obejmuje
  wyłącznie moduł płatności i konfigurację, bez zmian w kontraktach innych
  modułów, i mieści się w 3 dniach pracy (odpowiedź).” Scenariusze
  modyfikowalności pisz dla zmian *spodziewanych* — ich lista to zarazem
  jawna deklaracja, na co architektura jest gotowa, a na co świadomie nie.
- **Odtwarzalność:** „Dysk serwera ulega awarii (bodziec) w środku dnia
  pracy (środowisko); system zostaje odtworzony z kopii na nowej maszynie
  w czasie do 4 godzin, z utratą danych nie większą niż 15 minut (odpowiedź).”

Zbiór scenariuszy powstaje w etapie 1 procedury i służy dwa razy: przy
projektowaniu (warianty ocenia się względem scenariuszy) i przy odbiorze
(scenariusz wydajności staje się testem obciążeniowym, dostępności — próbą
kontrolowanej awarii). Scenariusz niesprawdzalny przeredaguj, aż się da.

## 2. Przegląd architektury metodą kompromisów (uproszczone ATAM)

Pełna metoda ATAM wymaga warsztatów i wielu ról; do skali Danaco stosuj
wersję uproszczoną, wykonalną w pół dnia, także jednoosobowo:

1. Zbierz 5–10 najważniejszych scenariuszy jakościowych (sekcja 1) i nadaj
   im wagi wspólnie z właścicielem projektu.
2. Wypisz rozważane warianty architektury (z etapu 4 procedury).
3. Zbuduj tabelę roboczą: wiersze — scenariusze, kolumny — warianty.
   W komórce zapisz, jak wariant obsługuje scenariusz, oceną trójstopniową
   (wspiera / obojętny / utrudnia) plus jedno zdanie uzasadnienia. Zdanie
   jest obowiązkowe — ocena bez uzasadnienia nie podlega późniejszej rewizji.

| Scenariusz (waga) | Wariant A: monolit + skrzynka | Wariant B: osobna usługa wysyłki |
|---|---|---|
| Wydajność zatwierdzania (wys.) | wspiera — zapis lokalny, jedna transakcja | obojętny — zapis lokalny, wysyłka i tak poza ścieżką |
| Dostępność przy awarii poczty (wys.) | wspiera — zaległość w tabeli | wspiera — zaległość w usłudze |
| Prostota wdrożenia on-premise (wys.) | wspiera — jeden proces | utrudnia — drugi proces u każdego klienta |
| Skalowanie wysyłki (nis.) | utrudnia — wspólne zasoby procesu | wspiera — skalowanie osobne |

4. Odczytaj z tabeli dwie rzeczy:
   - **Punkty wrażliwości** — miejsca, gdzie drobna zmiana parametru
     przestawia ocenę (np. wariant A wspiera wydajność, dopóki wysyłka nie
     przekracza pewnego wolumenu — zapisz próg liczbą i monitoruj go).
   - **Kompromisy** — komórki, gdzie wariant wygrywa scenariusz kosztem
     innego. Rozstrzygają wagi, nie preferencja technologiczna: przewaga B
     w skalowaniu (waga niska) nie równoważy przegranej w prostocie
     on-premise (waga wysoka).
5. Wynik przenieś do ADR: tabela do sekcji wariantów, punkty wrażliwości
   do „co monitorować” w konsekwencjach. Przegląd powtarzaj, gdy zmieniają
   się wagi (nowy duży klient, zmiana modelu wdrożenia) — uzasadnienia w
   komórkach pozwalają ocenić na nowo bez odtwarzania rozumowania z pamięci.

## 3. Funkcje sprawności — automatyczni strażnicy architektury

Funkcja sprawności (fitness function) to automatyczny test reguły
architektury, uruchamiany w CI jak każdy inny test. Reguła architektury bez
strażnika obowiązuje tylko do pierwszego pośpiechu. Utrzymuj co najmniej
trzy klasy strażników:

- **Testy zależności między modułami.** Egzekwują graf zależności zapisany
  w dokumencie architektury: `import-linter` (Python, kontrakty warstw,
  zakazów i niezależności), `dependency-cruiser` albo `eslint-plugin-boundaries`
  (JavaScript/TypeScript). Konfiguracja strażnika jest maszynową kopią
  rozdziału „granice” dokumentu architektury — zmieniaj oba w jednej rewizji;
  rozjazd między nimi to usterka (karta `granice-i-wzorce`, sekcja 2).
- **Budżety wydajności.** Progi liczbowe ze scenariuszy jakościowych
  zamienione na testy: czas odpowiedzi ścieżek krytycznych na danych
  o realistycznym rozmiarze, liczba zapytań SQL na operację (próg wykrywa
  regresje N+1 — licz zapytania w teście integracyjnym i porównuj z limitem),
  czas zimnego startu aplikacji pulpitowej. Budżet przekroczony blokuje
  scalenie tak samo jak test czerwony.
- **Limity rozmiaru i złożoności.** Górne progi na rozmiar modułu, pliku
  i funkcji oraz na liczbę zależności modułu. Ich zadaniem nie jest
  wymuszanie elegancji, lecz wczesne ujawnianie modułu, który rozrasta się
  ponad swoją odpowiedzialność — przekroczenie progu ma wywołać rozmowę
  o granicy, nie mechaniczne cięcie pliku na dwa.

Zasady prowadzenia strażników:
- Strażnik ma być szybki i jednoznaczny; strażnik chwiejny (raz czerwony,
  raz zielony bez zmiany kodu) psuje zaufanie do zestawu — napraw go albo usuń.
- Wyjątek od reguły zapisuj w konfiguracji z komentarzem wskazującym ADR,
  który go uzasadnia; wyjątek bez ADR to erozja w trakcie stawania się
  (sekcja 4).
- Nowy strażnik wprowadzaj najpierw w trybie ostrzeżenia na zastanym kodzie,
  z jawną listą odstępstw; dopiero potem w trybie blokującym.

## 4. Wykrywanie erozji architektury

Erozja to rozjazd między architekturą zapisaną a rzeczywistym kodem,
narastający drobnymi krokami, z których każdy z osobna wyglądał niewinnie.
Wykrywaj ją sygnałami, nie przeczuciem:

Sygnały twarde (wykrywalne maszynowo):
- import przekraczający zadeklarowaną granicę modułów albo nowy cykl
  zależności — łapane przez strażników z sekcji 3, o ile ich konfiguracja
  nadąża za dokumentem;
- rosnąca liczba wyjątków w konfiguracji strażników — każdy wyjątek to
  udokumentowana dziura w granicy; trend rosnący jest ważniejszy niż stan;
- zapytania SQL jednego modułu do tabel innego modułu (wykrywalne
  przeszukaniem kodu po nazwach schematów bazy);
- pliki z różnych modułów wielokrotnie zmieniane w tych samych rewizjach —
  analiza współzmienności wskazuje granicę przebiegającą w poprzek
  rzeczywistej osi zmian.

Sygnały miękkie (wykrywalne w przeglądzie):
- to samo pojęcie biznesowe zamodelowane niezależnie w dwóch modułach
  (dwie klasy „Kontrahent” o rozbieżnych polach) — właścicielstwo encji
  nierozstrzygnięte albo nierespektowane;
- synonimy w nazewnictwie (kod mówi „klient”, dokument „kontrahent”) —
  wprost usterka wobec zasady wiążącego nazewnictwa;
- sekcje dokumentu opisujące składniki nieobecne w kodzie albo milczące
  o składnikach, które są.

Procedura naprawy:
1. Ustal, która strona ma rację: czy kod zdryfował od słusznej decyzji, czy
   decyzja przestała przystawać do wymagań. Karanie kodu za mądrzejszą od
   dokumentu adaptację jest równie szkodliwe jak legalizowanie dryfu bez
   namysłu.
2. Jeśli rację ma dokument — zaplanuj powrót kodu do zgodności jako zwykłą
   pracę z terminem, strategiami z karty `granice-i-wzorce` (sekcja 7).
3. Jeśli rację ma kod — zapisz nowy ADR zastępujący stary (sekcja 5)
   i uaktualnij strażników.
4. W obu przypadkach domknij pętlę: dodaj lub zaostrz strażnika, który
   wykryłby ten rozjazd wcześniej.

Przegląd erozji wykonuj w rytmie kwartalnym, w ramach audytu jakości
(`../kontrola-jakosci/references/audyt-jakosci/audyt-jakosci.md`).

## 5. Rejestr decyzji jako żywy dokument

Rejestr ADR w kanonicznym dokumencie architektury (etap 5 procedury) jest
żywy: czyta się go przed zmianami i zmienia wraz z systemem.

- **Przeglądaj ADR przy każdej zmianie dotykającej jego obszaru.** Przed
  pracą w obszarze objętym decyzją przeczytaj jej zapis; jeśli kontekst
  decyzji się zdezaktualizował (zmienione liczby, nowe ograniczenia),
  zgłoś to właścicielowi projektu, zamiast w milczeniu projektować obok.
- **Decyzja zastąpiona ma następcę, nie kasowanie.** Nieaktualnego ADR nie
  usuwaj ani nie przepisuj po cichu. Nadaj mu stan „zastąpiona przez ADR-nn”
  z datą, a w następcy wskaż poprzednika i powód. Łańcuch decyzji to jedyne
  trwałe źródło odpowiedzi na pytanie „czemu to tak działa” — po dwóch
  latach i przy pracy z modelami AI (sekcja 6) ta pamięć jest bezcenna.
- **Stany decyzji ogranicz do czterech:** proponowana, przyjęta, zastąpiona,
  wycofana (decyzja przyjęta, lecz nigdy niezrealizowana — odnotuj czemu).
  Rozbudowane obiegi zatwierdzania to ceremonia bez zysku w małym zespole.
- **Konsekwencje uzupełniaj po fakcie.** Gdy rzeczywistość zweryfikuje
  decyzję (przewidywany koszt okazał się inny, monitorowany próg został
  osiągnięty), dopisz to do sekcji konsekwencji z datą. Rejestr, w którym
  konsekwencje są zawsze tylko przewidywaniami, nie uczy niczego.
- **Wiąż strażników z decyzjami.** Każda reguła w konfiguracji strażników
  (sekcja 3) powinna dać się wywieść z ADR; strażnik bez decyzji to
  przesąd, decyzja bez strażnika — życzenie.

## 6. Architektura a zespół jednoosobowy wspomagany modelami AI

W trybie pracy Danaco jeden architekt-właściciel prowadzi projekt, a znaczną
część kodu wytwarzają modele wykonawcze. To przesuwa rolę dokumentu
architektury: przestaje być notatką dla przyszłego siebie, a staje się
**kontraktem dla modeli wykonawczych** — najważniejszym wejściem każdej
sesji pracy modelu.

Zasady prowadzenia dokumentu jako kontraktu:
- **Rozdziel wprost zakresy swobody.** Dokument architektury musi jawnie wskazywać: co model może
  zmieniać swobodnie (wnętrza modułów w ramach ich interfejsów, testy, kod podległy strażnikom), a
  co wymaga uprzedniej zgody właściciela (granice modułów i ich interfejsy publiczne, schemat bazy i
  migracje, kontrakty zewnętrzne, dobór technologii, konfiguracja strażników, treść ADR). Model,
  który w toku zadania stwierdza potrzebę zmiany z drugiej listy, przerywa i pyta — nie „poprawia
  przy okazji”. To wprost zastosowanie standardów zawodowych
  (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`) o granicach samodzielności.
- **Strażnicy są ważniejsi niż instrukcje.** Model może źle zrozumieć
  akapit; strażnika w CI nie zignoruje niezauważenie. Każdą regułę, której
  naruszenie przez model byłoby kosztowne, wyrażaj podwójnie: zdaniem
  w dokumencie i testem w CI (sekcja 3). W zespole jednoosobowym strażnicy
  zastępują drugą parę oczu przeglądu.
- **Pisz decyzje, nie tylko stan.** Model czytający wyłącznie opis stanu
  („moduły A, B, C”) będzie proponował zmiany łamiące intencje. Zapis ADR
  z wariantami odrzuconymi i powodami odrzucenia powstrzymuje model przed
  ponownym proponowaniem wariantu odrzuconego — odrzucenie bez zapisu wraca
  w co drugiej sesji.
- **Nazewnictwo wiążące działa w obie strony.** Model używa nazw z dokumentu;
  właściciel utrzymuje dokument, w którym te nazwy są jednoznaczne. Słownik
  pojęć w dokumencie jest dla modelu tańszy niż wiedza plemienna, której
  model nie posiada.
- **Po sesji pracy modelu domknij pętlę.** Sprawdź, czy zmiany nie naruszyły
  granic (strażnicy), czy nie powstały synonimy pojęć (sekcja 4) i czy
  decyzje trudno odwracalne podjęte w toku sesji trafiły do rejestru.
  Decyzja architektoniczna podjęta mimochodem przez model wykonawczy
  i nigdzie nie zapisana to najszybsza znana droga erozji.

## Odesłania

Granice i komunikacja — karta `references/architektura/granice-i-wzorce.md`; dane, kontrakty,
migracje — karta `references/architektura/dane-i-kontrakty.md`; procedura i układ ADR — `SKILL.md`.
