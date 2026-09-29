# Raportowanie audytu — karta

Karta rozszerza sekcje „Zasady dowodowe” i „Raport z audytu” procedury.
Raport jest produktem audytu — audyt przeprowadzony wzorowo, lecz zraportowany
niechlujnie, nie zadziała: decydent nie podejmie decyzji, zespół nie naprawi
we właściwej kolejności, a audytor nie obroni ustaleń przy sporze. Stosuj
poniższe zasady do każdego raportu, także przekazywanego wyłącznie w rozmowie.

## 1. Kalibracja wagi ustaleń

### 1.1 Macierz prawdopodobieństwo × skutek

Wagę każdego ustalenia wyznacz z dwóch osi, ocenianych osobno i jawnie:

- **Skutek** — co się stanie, gdy ryzyko się zmaterializuje: strata danych,
  włamanie, przestój, błędne wyniki, koszt utrzymania, niewygoda.
- **Prawdopodobieństwo** — jak łatwo o materializację: wymagane warunki
  (dostęp sieciowy, konto, zbieg okoliczności), czy ścieżka jest wykonywana
  często, czy istnieje obejście.

| | Skutek poważny | Skutek umiarkowany | Skutek drobny |
|---|---|---|---|
| **Prawdopodobieństwo wysokie** | Krytyczne | Istotne | Drobne |
| **Prawdopodobieństwo średnie** | Istotne | Istotne | Drobne |
| **Prawdopodobieństwo niskie** | Istotne | Drobne | Drobne |

Macierz jest punktem wyjścia, nie automatem — od wyniku macierzy wolno odstąpić,
ale odstępstwo uzasadnij w treści ustalenia.

### 1.2 Zakaz inflacji „krytyczne” — kryteria twarde

Waga „krytyczne” jest zarezerwowana dla ustaleń spełniających co najmniej jedno
kryterium twarde:

1. udokumentowana możliwość **straty lub uszkodzenia danych**;
2. udokumentowana możliwość **włamania lub eskalacji uprawnień** (przejęcie
   sesji, odczyt cudzych danych, wykonanie kodu);
3. **przestój lub blokada funkcji krytycznej bez obejścia** — system nie działa
   albo przestanie działać w przewidywalnym terminie (wygasający certyfikat,
   kończące się miejsce), a użytkownik nie ma drogi zastępczej.

Wszystko inne jest co najwyżej istotne. Inflacja wag niszczy raport podwójnie:
decydent przestaje odróżniać pożar od bałaganu, a przy kolejnym audycie nikt
nie traktuje „krytycznego” poważnie. Regułą praktyczną: jeśli ustalenie może
poczekać do przyszłego tygodnia bez rosnącej szkody — nie jest krytyczne.
Odwrotna inflacja też jest błędem: nie obniżaj wagi dlatego, że naprawa jest
trudna albo niewygodna politycznie — waga opisuje ryzyko, nie koszt naprawy.

## 2. Pisanie ustaleń — metoda fakt → dowód → skutek → naprawa

Każde ustalenie ma cztery obowiązkowe elementy w stałej kolejności:

1. **Fakt** — jedno zdanie oznajmujące, co stwierdzono, z miejscem (plik,
   moduł, adres). Bez ocen, bez przymiotników.
2. **Dowód** — wynik polecenia, fragment odpowiedzi, zrzut wyniku narzędzia —
   z poleceniem i datą, tak by inna osoba mogła powtórzyć próbę.
3. **Skutek** — co z tego faktu wynika praktycznie, w warunkach tego projektu
   (nie podręcznikowo).
4. **Naprawa** — konkretny, wykonalny pierwszy krok; jeśli napraw jest kilka
   wariantów, wskaż zalecany i powiedz dlaczego.

### Pary przykładowe: źle → dobrze

**Para 1 — bezpieczeństwo.**

Źle: „Aplikacja ma poważne problemy z bezpieczeństwem ciasteczek, co jest
bardzo ryzykowne i wymaga pilnej naprawy.”

Dobrze: „Ciasteczko sesyjne nie ma flag HttpOnly i Secure. Dowód: nagłówek
`Set-Cookie: session=…; Path=/` w odpowiedzi logowania (curl -sI, 2026-08-14).
Skutek: dowolny XSS w aplikacji pozwala odczytać token i przejąć sesję;
token wychodzi również w ruchu HTTP. Naprawa: ustawić `HttpOnly; Secure;
SameSite=Lax` w konfiguracji sesji — jedna zmiana konfiguracyjna; sprawdzić,
czy frontend nie czyta ciasteczka z JS (grep po `document.cookie`).”

Błędy wersji złej: brak miejsca, brak dowodu, ocena zamiast faktu
(„poważne”, „bardzo ryzykowne”), brak wykonalnej naprawy.

**Para 2 — jakość kodu.**

Źle: „Kod w module raportów jest napisany fatalnie i nieczytelnie, trzeba go
przepisać.”

Dobrze: „Funkcja `generuj_raport` w `raporty/generator.py` ma złożoność
cyklomatyczną 34 i 210 linii; moduł jest trzecim najgorętszym hotspotem
repozytorium (41 zmian × 1840 linii) i nie ma żadnego testu. Dowód: `radon cc
-s raporty/generator.py` → F (34); tabela hotspotów, sekcja 2 raportu. Skutek:
każda zmiana w raportach niesie wysokie ryzyko regresji bez sygnału
ostrzegawczego; historia pokazuje 6 rewizji naprawczych tego pliku w pół roku.
Naprawa: najpierw test charakteryzujący obecne zachowanie na 3 raportach
wzorcowych, potem wydzielenie etapów potoku (pobranie, agregacja, format) —
w tej kolejności, bo refaktoryzacja bez testu powiela dotychczasowy wzorzec
napraw naprawianych.”

Błędy wersji złej: ocena emocjonalna, brak liczb, „przepisać” nie jest planem.

**Para 3 — waga skalibrowana w dół.**

Źle: „KRYTYCZNE: brak nagłówka X-Content-Type-Options naraża użytkowników na
ataki.”

Dobrze: „Drobne: odpowiedzi nie zawierają nagłówka `X-Content-Type-Options:
nosniff` (dowód: curl -sI, pełna lista nagłówków w załączniku). Skutek:
przeglądarka może zgadywać typ MIME zasobów, co w połączeniu z możliwością
wgrywania plików podniosłoby ryzyko — w tym projekcie użytkownicy nie wgrywają
plików, więc skutek jest ograniczony. Naprawa: jedna linia w konfiguracji
serwera; wykonać przy najbliższym wdrożeniu.”

Zasada z tej pary: waga wynika z warunków projektu, a obniżenie wagi
uzasadnia się tak samo starannie jak podwyższenie.

### Zasady redakcyjne ustaleń

- Jedno ustalenie — jedna sprawa; nie łącz pięciu problemów w jedno „stan
  modułu X jest zły”.
- Grupuj wystąpienia tego samego wzorca w jedno ustalenie z listą miejsc
  („zapytania budowane konkatenacją w 7 miejscach — lista poniżej”), zamiast
  siedmiu ustaleń; wagę nadaj według najgorszego wystąpienia.
- Ustalenia bez dowodu oznaczaj wprost jako przypuszczenia i umieszczaj
  w osobnej podsekcji — pomieszanie faktów z przypuszczeniami podważa całość.
- Odnotuj także to, co działa dobrze, w krótkiej sekcji pozytywów: kalibruje
  odbiór i chroni dobre praktyki przed przypadkowym zaoraniem podczas napraw.

## 3. Plan naprawy jako harmonogram zależności

Plan naprawy nie jest listą ustaleń posortowaną po wadze — jest harmonogramem,
w którym o kolejności decydują trzy czynniki: ryzyko, zależności techniczne
i stosunek skutku do nakładu.

- **Co odblokowuje co:** wypisz zależności jawnie. Przykłady typowych
  zależności: test charakteryzujący odblokowuje refaktoryzację hotspotu;
  naprawa uruchamiania na czysto odblokowuje pipeline CI; podbicie wersji
  frameworka odblokowuje łatki bezpieczeństwa zależności, które wymagają
  nowszej wersji. Pozycję planu, która niczego nie odblokowuje i niczego nie
  wymaga, wolno szeregować czysto po wadze.
- **Szybkie wygrane a inwestycje:** podziel plan na dwie ścieżki prowadzone
  równolegle. Szybkie wygrane — nakład mały, skutek natychmiastowy, ryzyko
  zerowe (nagłówki, flagi ciasteczek, kompresja, usunięcie plików-narośli):
  wykonać w pierwszym tygodniu, budują zaufanie do procesu naprawy. Inwestycje —
  nakład duży, skutek strukturalny (pokrycie hotspotów testami, likwidacja
  duplikatów bibliotek, refaktoryzacja modułu naprawianego wielokrotnie):
  wymagają decyzji o priorytecie względem rozwoju produktu — tę decyzję
  podejmuje właściciel, audytor dostarcza danych.
- **Szacunki nakładu z jawną niepewnością:** podawaj rzędy wielkości
  (godziny / dni / tygodnie), nie liczby udające precyzję. Przy pozycjach
  o dużej niepewności powiedz, skąd ona płynie i co ją zmniejszy („nakład:
  dni–tygodnie; niepewność wynika z nieznanej liczby miejsc zależnych od
  starego API — zmniejszy ją półdniowa analiza wywołań”). Szacunek dotyczy
  nakładu wykonania naprawy przez osobę znającą projekt; zaznacz to założenie.
- Każdej pozycji planu przypisz ustalenia, które zamyka (odwołaniem do ich
  numerów) — plan bez tego wiązania nie pozwala potem sprawdzić kompletności
  napraw.

## 4. Streszczenie dla decydenta

Streszczenie czyta osoba, która nie przeczyta reszty — musi wystarczyć do
decyzji. Zasady: bez żargonu (nie „XSS przez brak CSP”, lecz „możliwość
przejęcia kont użytkowników”), ryzyka wyrażone biznesowo (przestój, strata
danych klientów, koszt utrzymania, ryzyko prawne), długość 5 zdań.

Wzorzec pięciu zdań:

1. Co zbadano i w jakim celu (zakres jednym zdaniem).
2. Ocena ogólna względem celu audytu (zdatny / zdatny warunkowo / niezdatny —
   ze wskazaniem warunku).
3. Najpoważniejsze ryzyko wyrażone skutkiem biznesowym.
4. Co trzeba zrobić najpierw i jakim rzędem nakładu.
5. Czego audyt nie obejmował (jedno zdanie o granicach — patrz sekcja 7).

Streszczenie piszesz na końcu pracy, ale stoi na początku raportu. Test
jakości streszczenia: osoba nietechniczna po jego przeczytaniu potrafi
powiedzieć, czy sprawa jest pilna i ile z grubsza będzie kosztować — jeśli
nie potrafi, przepisz.

## 5. Rozmowa o wynikach z zespołem — bez teatru winy

Wyniki audytu omawia się z zespołem przed lub równocześnie z przekazaniem
decydentowi — zespół, który poznaje ustalenia z raportu wysłanego ponad jego
głową, będzie ich bronić zamiast naprawiać. Zasady rozmowy:

- **Ustalenia są o kodzie, nie o ludziach.** W raporcie i rozmowie nie
  wskazuje się autorów ustaleń — `git blame` służył doborowi próbek, nie
  przypisaniu winy. Wyjątek: analiza bus factor z konieczności mówi o osobach;
  formułuj ją jako ryzyko ciągłości („wiedza o module X jest skupiona w jednej
  osobie”), nigdy jako zarzut wobec tej osoby — skupienie wiedzy jest zwykle
  skutkiem decyzji organizacyjnych, nie zaborczości.
- **Zacznij od metody, nie od wyników:** pokaż, jak zbierano dowody i jakie
  progi przyjęto — zespół, który rozumie metodę, spiera się o fakty, a nie
  o intencje.
- **Dopuść kontekst zespołu przed finalizacją:** część ustaleń ma wyjaśnienia
  (świadome kompromisy, ograniczenia zastane, prace w toku). Wyjaśnienie nie
  kasuje ustalenia, ale zmienia jego opis — dopisz kontekst do treści
  ustalenia i, gdy to zasadne, skoryguj wagę. Ustalenie, przy którym zespół
  powiedział „wiemy, to świadoma decyzja z powodu Y”, raportuj jako ryzyko
  zaakceptowane ze wskazaniem, kto je zaakceptował.
- **Nie negocjuj faktów.** Wagę i opis wolno korygować na podstawie kontekstu;
  dowodu się nie wycofuje, bo jest niewygodny. Spór o fakt rozstrzyga
  powtórzenie próby przy wszystkich zainteresowanych.

## 6. Audyt powtórny — weryfikacja napraw

Audyt powtórny nie jest nowym audytem — jest weryfikacją zamknięcia ustaleń
z audytu pierwotnego. Metodyka:

- **Powtórz dokładnie te same próby**, którymi zebrano dowody pierwotne: te
  same polecenia, te same adresy, ta sama konfiguracja narzędzi. Zmiana
  narzędzia lub konfiguracji między pomiarami unieważnia porównanie — jeśli
  zmiana była konieczna (nowa wersja narzędzia), odnotuj ją i w miarę
  możliwości wykonaj pomiar oboma wariantami.
- **Przytocz wyniki przed/po** przy każdym ustaleniu, obok siebie: „przed:
  `npm audit` — 3 krytyczne, 11 wysokich (2026-05-10); po: 0 krytycznych,
  2 wysokie (2026-08-14); pozostałe 2 dotyczą pakietu X, poprawka
  nieopublikowana — ryzyko zaakceptowane przez właściciela do czasu wydania”.
- **Status każdego ustalenia** — jeden z czterech: naprawione (dowód po),
  naprawione częściowo (co zostało), nienaprawione, ryzyko zaakceptowane
  (przez kogo i na jakich warunkach). Ustalenie „naprawione” bez powtórzonej
  próby nie istnieje — deklaracja zespołu nie jest dowodem.
- **Regresje i nowe obserwacje:** jeśli przy powtarzaniu prób wyjdą nowe
  problemy, raportuj je w osobnej sekcji, wyraźnie oddzielonej od weryfikacji —
  nie mieszaj zamykania starych ustaleń z otwieraniem nowych.
- Audyt powtórny planuj już w raporcie pierwotnym: podaj, które próby będą
  powtórzone i co uznaje się za zamknięcie — to usuwa późniejsze spory
  o kryteria.

## 7. Granice odpowiedzialności audytora

Raport ma jawnie wytyczać granice tego, co stwierdza — audyt bez granic
obiecuje więcej, niż jakikolwiek audyt może dostarczyć.

- **Czego audyt nie stwierdza:** audyt jest badaniem próbek w punkcie czasu.
  Nie stwierdza poprawności całego kodu (badano próbki), stanu przyszłego
  (dowody mają daty), ani nieobecności problemów w obszarach niebadanych.
  Sekcja „Czego nie zbadano” jest obowiązkowa i konkretna: wymień obszary
  z powodem pominięcia (poza zakresem umówionym, brak dostępu, brak środowiska,
  brak czasu — każdy powód jest legalny, przemilczenie żadnego nie jest).
- **Zakaz gwarancji „brak podatności”:** nigdy nie formułuj wyników jako
  „aplikacja jest bezpieczna”, „nie ma podatności”, „kod jest wolny od błędów”.
  Poprawna forma: „w zbadanym zakresie, wymienionymi metodami, w dniu badania
  nie stwierdzono…” — z odesłaniem do listy prób. Brak ustaleń jest wynikiem
  prób, nie właściwością systemu.
- **Rozdzielaj fakty, wnioski i zalecenia:** fakt (nagłówek nieobecny),
  wniosek (ochrona nie działa), zalecenie (ustawić tak). Czytelnik musi umieć
  odrzucić zalecenie, nie odrzucając faktu.
- **Kwestie prawne i licencyjne:** audyt techniczny stwierdza stan (licencja
  GPL obecna w zależnościach, dane osobowe w logach), lecz nie wydaje opinii
  prawnej — zalecaj konsultację właściwą, nie zastępuj jej.
- **Konflikt ról:** jeśli audytor ma następnie wykonywać naprawy, powiedz to
  w raporcie — czytelnik ma prawo wiedzieć, że autor zaleceń będzie ich
  wykonawcą, i ocenić zalecenia z tą wiedzą.
