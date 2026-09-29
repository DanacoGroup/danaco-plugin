# Warsztat pisarski dokumentacji technicznej

Karta zbiera warsztat pisania technicznego klasy zawodowej: od architektury informacji dokumentu,
przez konstrukcję akapitu i wybór formy, po redakcję własnego tekstu i pułapki polszczyzny
technicznej. Stosuj ją przy pisaniu każdego dokumentu — układy poszczególnych rodzajów dokumentów
podaje SKILL.md, a metodę pakietu dokumentacji karta
`references/dokumentacja-techniczna/pakiet-dokumentacji-systemu.md`.

## 1. Architektura informacji dokumentu

Strukturę dokumentu wyprowadzaj z decyzji czytelnika, nie z chronologii pracy
autora ani z budowy systemu. Przed napisaniem spisu treści odpowiedz pisemnie
na trzy pytania:

1. **Kto czyta** — jedna konkretna rola (deweloper przejmujący projekt,
   administrator wdrażający, decydent zatwierdzający). Dokument „dla wszystkich”
   jest dokumentem dla nikogo; przy dwóch odbiorcach rozważ dwa dokumenty
   albo wyraźny podział na części.
2. **Co czytelnik rozstrzyga lub wykonuje po lekturze** — decyzja
   („zatwierdzam architekturę”), czynność („wdrażam system”), rozumienie
   („wiem, gdzie dopisać moduł”). To rozstrzygnięcie steruje selekcją treści:
   wchodzi to, co służy decyzji lub czynności; reszta odpada niezależnie od
   tego, ile pracy kosztowało jej poznanie.
3. **W jakiej kolejności czytelnik potrzebuje treści** — rozdziały układaj od
   pytań, które czytelnik zada najpierw, do tych, które zada, gdy już rozumie
   całość. Kolejność „jak system powstawał” i „jak kod jest ułożony
   w katalogach” to dwie najczęstsze złe kolejności.

Dokument dłuższy niż kilka stron wymaga warstw dostępu: spis treści dla
nawigacji, streszczenie lub tabela zbiorcza na początku dla czytelnika
pobieżnego, rozdziały dla czytelnika dokładnego, załączniki dla czytelnika
wykonującego. Czytelnik ma prawo przerwać lekturę po każdej warstwie
z poprawnym, choć mniej szczegółowym obrazem.

## 2. Zasada piramidy: wniosek przed uzasadnieniem

Podawaj rozstrzygnięcie najpierw, uzasadnienie po nim. Obowiązuje na każdym
poziomie: dokument otwiera streszczenie z głównymi rozstrzygnięciami; rozdział
otwiera zdanie z tezą rozdziału; akapit otwiera zdanie z tezą akapitu.
Kolejność odwrotna — przesłanki, rozważania, na końcu wniosek — jest kolejnością
dochodzenia do wyniku, nie jego komunikowania; zmusza czytelnika do trzymania
w pamięci przesłanek niewiadomo czego.

Źle: „Rozważono trzy warianty przechowywania danych. Wariant pierwszy…
Wariant drugi… Wariant trzeci… W związku z powyższym wybrano wariant drugi.”
Dobrze: „Dane przechowuje SQLite (wariant drugi z trzech rozważonych) —
rozstrzygnęła trwałość transakcyjna bez osobnego serwera. Porównanie wariantów
zawiera tabela poniżej.”

Uzasadnienie po wniosku nie jest ozdobą — czytelnik, który zna wniosek,
czyta uzasadnienie po to, by ocenić, czy nadal obowiązuje, gdy zmienią się
warunki. Dlatego uzasadnienie podaje kryteria i fakty, nie retorykę.

## 3. Akapit jako jednostka

Akapit niesie **jedną tezę**. Test: akapit da się streścić jednym zdaniem,
a tym zdaniem jest — lub powinno być — jego pierwsze zdanie. Zdania kolejne
tezę rozwijają, uzasadniają lub ograniczają; zdanie wnoszące nową tezę otwiera
nowy akapit.

Reguły konstrukcji:

- **Pierwsze zdanie niesie treść.** Czytelnik skanujący dokument po pierwszych
  zdaniach akapitów ma otrzymać kompletny szkielet wywodu. Pierwsze zdania
  typu „Warto w tym miejscu zauważyć, że…”, „Kolejnym aspektem jest…” wyrzuć —
  zacznij od tego, co następuje po nich.
- **Jeden akapit — jeden adresat zaimka.** Gdy „on”, „ten”, „to” może wskazywać
  dwa rzeczowniki poprzedniego zdania, powtórz rzeczownik. Powtórzenie nazwy
  w tekście technicznym nie jest usterką stylu; wieloznaczność jest.
- **Długość**: 3–6 zdań. Akapit jednozdaniowy sygnalizuje tezę niedorozwiniętą
  (rozwiń albo dołącz do sąsiada); akapit ośmiozdaniowy — dwie tezy sklejone
  (podziel).

## 4. Tabela, proza, diagram — kryteria wyboru

Formę dobieraj do struktury treści, nie do przyzwyczajenia.

| Struktura treści | Forma | Uzasadnienie |
|---|---|---|
| N elementów porównywanych w M wymiarach | Tabela | Proza o trzech cechach czterech wariantów wymaga od czytelnika budowy tabeli w głowie — zbuduj ją za niego. |
| Przypisanie: element → odpowiedzialność / wartość / zachowanie | Tabela dwukolumnowa | Wyliczenie w prozie gubi równoległość; tabela ją wymusza. |
| Decyzja z wariantami i kryteriami | Tabela decyzyjna + akapit wyboru | Kryteria w wierszach, warianty w kolumnach, wybór z uzasadnieniem pod tabelą — nigdy wybór ukryty w komórce. |
| Wywód przyczynowy, uzasadnienie, definicja niuansu | Proza | Tabela nie niesie „ponieważ”, „chyba że”, „pod warunkiem”; upychanie zdań podrzędnych w komórki daje tabelę-prozę, najgorszą z form. |
| Przepływ, cykl życia, hierarchia, topologia | Diagram (schemat tekstowy ASCII w bloku kodu) | Relacje przestrzenne i sekwencyjne oko czyta szybciej niż opis; diagram w ASCII wersjonuje się razem z tekstem. |
| Sekwencja czynności do wykonania | Lista numerowana (procedura, rozdz. 5) | Numer daje punkt odniesienia przy wykonaniu i przy zgłaszaniu problemu. |

Reguły łączenia form: diagram i tabela nie zastępują definicji — pierwsze
wystąpienie pojęcia definiuje proza, formy strukturalne je zestawiają. Diagram
używa dokładnie tych nazw, które nosi tekst i kod; diagram z własnymi skrótami
podwaja słownik. Nie dubluj treści tabeli akapitem, który ją „omawia” — akapit
przy tabeli mówi to, czego w tabeli nie ma: wybór, wzorzec, wyjątek.

## 5. Pisanie procedur

Procedura to tekst wykonywany, nie czytany — pisz ją tak, by wykonawca w żadnym
kroku nie musiał niczego się domyślać.

1. **Tryb rozkazujący**, jedno polecenie na krok: „Uruchom…”, „Sprawdź…”,
   „Wpisz…”. Nie „należy uruchomić”, nie „uruchamiamy”, nie „zostanie
   uruchomione”.
2. **Krok atomowy**: jedna czynność, którą wykonawca kończy, zanim spojrzy na
   następny krok. Zdanie z „a następnie”, „po czym” w kroku to dwa kroki.
3. **Wynik oczekiwany po każdym kroku**: co wykonawca ma zobaczyć, żeby wiedzieć,
   że krok się powiódł — dosłowny komunikat, stan, wartość. Krok bez wyniku
   oczekiwanego odbiera wykonawcy możliwość wykrycia niepowodzenia we właściwym
   miejscu; błąd ujawni się trzy kroki dalej, w mylącej postaci.
4. **Polecenia dosłowne** w blokach kodu, gotowe do wklejenia. Fragmenty do
   podstawienia oznacz jednolitą konwencją i wypisz przed procedurą, z opisem
   skąd wziąć wartość.
5. **Warunki wstępne przed krokiem 1**: uprawnienia, narzędzia, stan systemu.
   Warunek odkrywany w kroku 7 unieważnia pracę z kroków 1–6.
6. **Rozgałęzienia jawnie**: „Jeśli komunikat zawiera…, przejdź do kroku 12;
   w przeciwnym razie kontynuuj.” Procedura z ukrytymi założeniami o przebiegu
   szczęśliwym zawodzi dokładnie wtedy, gdy jest potrzebna.

## 6. Pary źle → dobrze

Sześć par ilustruje najczęstsze przekształcenia redakcyjne. Wzorce, nie cytaty —
stosuj przekształcenie, nie brzmienie.

**Para 1 — zdanie mgliste → precyzyjne.**
Źle: „System w odpowiednich sytuacjach podejmuje stosowne działania w celu
zapewnienia poprawnego funkcjonowania synchronizacji.”
Dobrze: „Po zerwaniu połączenia klient ponawia próbę co 5 sekund; po ponownym
połączeniu serwer przesyła komunikaty pominięte w czasie rozłączenia.”

**Para 2 — strona bierna → czynna.**
Źle: „Po zatwierdzeniu formularza dane zostają zwalidowane, a w przypadku
wykrycia błędów użytkownik zostaje o nich poinformowany.”
Dobrze: „Po zatwierdzeniu formularza serwer waliduje dane; przy błędzie zwraca
listę pól z opisem usterki, a klient wyświetla ją przy polach.”
(Strona bierna ukrywa wykonawcę — a rozstrzygnięcie, czy waliduje klient, czy
serwer, jest właśnie treścią, którą czytelnik ma otrzymać.)

**Para 3 — ogólnik → liczba.**
Źle: „Operacja eksportu może przy większych zbiorach danych trwać stosunkowo
długo i zużywać znaczną ilość pamięci.”
Dobrze: „Eksport 100 tysięcy rekordów trwa około 40 sekund i zużywa do 1,5 GB
pamięci; powyżej 500 tysięcy rekordów stosuj eksport partiami.”
(Liczbę zmierz albo napisz wprost, że pomiaru nie wykonano — nie zmyślaj.)

**Para 4 — zapowiedź → treść.**
Źle: „W niniejszym rozdziale przedstawione zostaną zagadnienia związane
z problematyką konfiguracji połączenia z bazą danych.”
Dobrze: „Połączenie z bazą danych konfigurują trzy parametry: adres, nazwa bazy
i limit puli połączeń. Brak parametru oznacza wartość domyślną z tabeli poniżej.”

**Para 5 — asekuracja → rozstrzygnięcie.**
Źle: „W zależności od potrzeb można rozważyć zastosowanie mechanizmu kolejki,
co w niektórych przypadkach może przynieść pewne korzyści wydajnościowe.”
Dobrze: „Przy więcej niż 10 żądaniach na sekundę zastosuj kolejkę; poniżej tego
progu kolejka dodaje opóźnienie bez zysku.”

**Para 6 — łańcuch dopełniaczy → zdanie z czasownikiem.**
Źle: „Proces weryfikacji poprawności konfiguracji parametrów połączenia
serwera synchronizacji danych obejmuje…”
Dobrze: „Serwer synchronizacji sprawdza przy starcie, czy parametry połączenia
są poprawne. Sprawdzenie obejmuje…”

## 7. Pułapki polszczyzny technicznej

**Kalki z angielskiego.** Tłumacz konstrukcję, nie słowa: „dedykowany serwer”
(ang. *dedicated*) → „wydzielony serwer” lub „serwer przeznaczony do…”;
„adresować problem” → „rozwiązywać problem”; „wspierać format” (*support*) →
„obsługiwać format”; „w ramach modułu” nadużywane jako kalka *within* →
najczęściej wystarcza „w module”. Utrwalone terminy fachowe (interfejs,
serwer, sesja, token) zostawiaj — kalką jest przenoszenie składni
i frazeologii, nie zapożyczenie terminu, dla którego polszczyzna nie ma
odpowiednika.

**Łańcuchy dopełniaczy.** Ciąg trzech i więcej rzeczowników w dopełniaczu
(„proces obsługi żądań aktualizacji konfiguracji użytkownika”) jest
nieprzetwarzalny przy czytaniu. Rozbijaj czasownikiem lub przyimkiem: „proces,
który obsługuje żądania aktualizujące konfigurację użytkownika”. Granica
praktyczna: dwa dopełniacze pod rząd.

**Nominalizacje.** Rzeczownik odczasownikowy w miejscu czasownika rozdyma
zdanie i usuwa wykonawcę: „dokonywanie zapisywania danych następuje po
wykonaniu walidacji” → „serwer zapisuje dane po walidacji”. Sygnały ostrzegawcze:
„dokonywać”, „następuje”, „ma miejsce”, „ulega”, „w celu zapewnienia”,
„realizacja procesu”. Każde takie wyrażenie sprawdź, czy nie ukrywa prostego
czasownika.

**Fałszywa uprzejmość i wata grzecznościowa.** „Warto zwrócić uwagę”, „należy
podkreślić”, „jak łatwo zauważyć”, „oczywiście” — usuń; jeśli rzecz jest warta
uwagi, samo jej napisanie tego dowodzi.

## 8. Redakcja własnego tekstu

Redakcja jest osobnym etapem po napisaniu całości — nie poprawianiem zdań
w trakcie pisania. Wykonaj trzy przejścia, każde z innym celem:

1. **Przejście skracające: −20% objętości bez utraty treści.** Załóż z góry, że
   pierwsza wersja zawiera jedną piątą waty — to norma, nie zarzut. Usuwaj
   w kolejności: zapowiedzi i podsumowania powtarzające sąsiedztwo; zdania
   omawiające tabelę, która stoi obok; przymiotniki oceniające („zaawansowany”,
   „elastyczny”, „kompleksowy” — zostają tylko poparte treścią); nominalizacje
   (rozdz. 7); zdania, po których usunięciu czytelnik niczego nie traci. Licz
   znaki przed i po — cel 20% jest mierzalny; jeśli po uczciwym przejściu
   ubyło mniej, tekst był pisany dyscyplinowanie, jeśli więcej — powtórz
   przejście.
2. **Czytanie na głos.** Zdanie, na którym łapiesz oddech w połowie albo
   gubisz podmiot, jest za długie lub źle zbudowane — podziel je albo przestaw
   tak, by podmiot i orzeczenie stały blisko początku. Czytanie na głos
   wykrywa także mimowolne rymy, powtórzenia słów w sąsiednich zdaniach
   i zdania, których nie da się wypowiedzieć z sensowną intonacją.
3. **Kontrola terminologii grepem.** Dla każdego kluczowego pojęcia dokumentu
   przeszukaj plik po nazwie pojęcia i po podejrzewanych synonimach
   (`grep -in 'moduł\|komponent\|wtyczka' plik.md`) — każde wystąpienie synonimu
   ujednolić do brzmienia słownika. Sprawdź też pisownię wariantową tego samego
   terminu (wielkość liter, łącznik, odmiana nazw własnych). Kontrola ręczna
   „na oko” nie wykrywa synonimów — oko czyta znaczenie, nie brzmienie.

Po trzech przejściach wykonaj kontrolę zgodności z rzeczywistością: każde
polecenie z dokumentu uruchom, każdą wartość liczbową porównaj ze źródłem,
każdy odsyłacz otwórz. Redakcja językowa nie zastępuje weryfikacji — zdanie
piękne i fałszywe jest gorsze od niezgrabnego i prawdziwego.
