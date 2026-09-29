# Miary relacji i badania systemów agentowych

Karta rozwija procedurę z `references/agentic-ux/agentic-ux.md`. Miary relacji definiuj operacyjnie
przy projekcie, nie po wdrożeniu — miara dodana post factum mierzy to, co
akurat da się zmierzyć, a nie to, co miało być sukcesem. Każda miara poniżej
ma definicję liczbową, interpretację i tryb błędnego użycia; wszystkie razem
tworzą tablicę relacji, którą przegląda się okresowo (patrz koniec karty).

## Definicje operacyjne miar

**Wskaźnik przyjęć propozycji bez poprawek.** Odsetek propozycji systemu
przyjętych bez edycji, liczony osobno na obszar działania i stadium zaufania.
Licznik: propozycje przyjęte działaniem „przyjmij”. Mianownik: wszystkie
propozycje rozstrzygnięte (przyjęte + poprawione + odrzucone); propozycje
zignorowane licz osobno — ignorowanie jest sygnałem samym w sobie, nie szumem.
Interpretuj łącznie z poziomem trudności propozycji (patrz pułapki miar):
sam wskaźnik rośnie także wtedy, gdy system proponuje banały. Rozkład ma
znaczenie diagnostyczne: wysoki odsetek „popraw” przy niskim „odrzuć” oznacza
system bliski, ale niedokalibrowany — najlepsze możliwe miejsce do nauki;
wysoki „odrzuć” oznacza niezrozumienie potrzeb, nie problem kalibracji.

**Głębokość kontynuacji.** Odsetek sesji, które podejmują wątek poprzedniej
sesji (przez nawiązanie powitania lub samodzielny powrót użytkownika do
artefaktu wspólnego), względem sesji, w których istniał wątek możliwy do
podjęcia. Mianownik jest kluczowy: sesje bez otwartego wątku wyklucz
z rachunku, inaczej miara karze użytkowników, którzy domykają sprawy. Niska
głębokość przy istniejących wątkach oznacza, że relacja nie niesie wartości
między sesjami — system jest używany jak narzędzie jednorazowe mimo
architektury relacyjnej.

**Tempo wzrostu autonomii.** Mediana czasu (w dniach aktywnych, nie
kalendarzowych) od pierwszego użycia obszaru do przejścia w stadium 2 (asysta
nadzorowana) i stadium 3 (autonomia zarobiona), liczona per obszar. Median,
nie średniej — rozkład jest skośny, a ogon użytkowników, którzy nigdy nie
delegują, jest informacją, nie zakłóceniem: raportuj obok mediany odsetek
relacji, które w ogóle osiągają stadium 3. Tempo zbyt szybkie bywa gorsze niż
zbyt wolne — sprawdź, czy awanse nie wynikają z projektowej presji (nagabywanie
o zgodę), zamiast z rzeczywistych podstaw.

**Wskaźnik degradacji zaufania po błędzie i czas odbudowy.** Po incydencie
mierz dwie rzeczy: głębokość reakcji użytkownika (czy ograniczył autonomię
ręcznie poniżej degradacji automatycznej; czy porzucił obszar; czy porzucił
system) oraz czas powrotu do poziomu zaufania sprzed incydentu (dni aktywne do
ponownego osiągnięcia stadium sprzed błędu). Porównuj czas odbudowy między
incydentami obsłużonymi pełną sekwencją odbudowy (karta
`references/agentic-ux/biblioteka-wzorcow.md`, wzorzec 7) a obsłużonymi częściowo — to empiryczny
test wartości wzorca. Incydent bez śladu w miarach nie oznacza braku szkody:
część użytkowników nie degraduje autonomii, tylko cicho przestaje delegować —
dlatego patrz też na spadek liczby delegacji po incydencie.

**Wskaźnik korekt pamięci.** Częstość, z jaką użytkownik poprawia lub wymazuje
to, co system zapamiętał, w przeliczeniu na sto wpisów pamięci, rozbita na
klasy taksonomii (karta `references/agentic-ux/pamiec-i-prywatnosc.md`) i na źródła. Wysoki wskaźnik
dla wzorców wywnioskowanych = pamięć zgaduje: wnioskowanie jest zbyt śmiałe
względem dowodów. Wysoki wskaźnik dla faktów podanych = błąd rozumienia lub
zapisu, poważniejszy. Wskaźnik bliski zeru przy zapełnionym panelu pamięci nie
jest sukcesem automatycznie — sprawdź, czy użytkownicy w ogóle zaglądają do
panelu (odsetek relacji z co najmniej jedną wizytą w panelu); korekt nie ma
także wtedy, gdy nikt nie patrzy.

## Instrumentacja

Zdarzenia projektuj razem ze wzorcami interfejsu — każdy wzorzec z biblioteki
ma swój zestaw zdarzeń, definiowany w opracowaniu UX przy wzorcu, nie
w osobnym dokumencie analitycznym po fakcie.

Minimalny zestaw zdarzeń na wzorzec: propozycja — wyświetlona, przyjęta,
poprawiona (z rozmiarem poprawki jako kategorią: drobna/istotna), odrzucona
(z powodem, jeśli podany), zignorowana; plan — utworzony, edytowany przed
startem, edytowany w trakcie, zatrzymany na punkcie nieodwracalnym,
potwierdzony, rozjazd; pasek autonomii — propozycja awansu wyświetlona,
przyjęta, odrzucona, obniżenie ręczne, degradacja automatyczna; przerwanie —
wstrzymanie, przejęcie, anulowanie, wznowienie po przejęciu; skrzynka
przeglądowa — otwarta, pozycja rozstrzygnięta, czas zalegania decyzji;
panel pamięci — wizyta, fakt obejrzany ze źródłem, poprawiony, wymazany,
potwierdzony; proaktywność — odezwanie wysłane (klasa, kanał), obsłużone,
zignorowane, klasa zablokowana.

Twarde reguły instrumentacji:
- Rejestruj zdarzenia i kategorie, nigdy treści: fakt „użytkownik poprawił
  wpis pamięci klasy wywnioskowanej” — tak; treść wpisu — nie. Analityka nie
  jest wyjątkiem od reguł prywatności z karty `references/agentic-ux/pamiec-i-prywatnosc.md`.
- Każde zdarzenie niesie kontekst stadium zaufania i obszaru — bez tego miary
  relacji nie da się policzyć wstecz.
- Znaczniki czasu pozwalają liczyć dni aktywne i odstępy między sesjami;
  odstęp jest wymiarem każdej analizy relacji.
- Zdarzeń nie dodawaj „na zapas”: każde ma odbiorcę w postaci konkretnej
  miary lub progu alarmowego. Zdarzenie bez odbiorcy to koszt i ryzyko bez
  zwrotu.

## Badania jakościowe systemów agentowych

Relacji nie zbada się testem godzinnym. Klasyczny test użyteczności mierzy
pierwsze zderzenie z interfejsem — a pierwsze zderzenie to najmniej
reprezentatywny moment relacji, która ma dojrzewać tygodniami. Metody dobieraj
do osi czasu.

**Wywiad o zaufaniu.** Pytania nie mogą podpowiadać odpowiedzi ani tezy.
Zamiast „czy ufasz systemowi?” (deklaratywne, sugeruje, że zaufanie jest
oczekiwane) pytaj o zachowania i zdarzenia: „opowiedz o ostatnim razie, gdy
system zrobił coś za Ciebie — co sprawdziłeś po nim?”; „co robisz z jego
propozycjami, zanim je zatwierdzisz?”; „czego byś mu nie powierzył i co
musiałoby się stać, żeby to się zmieniło?”; „czy kiedyś Cię zaskoczył — czym?”.
Zaufanie odczytuj z praktyk weryfikacji, nie z deklaracji: użytkownik, który
mówi „ufam”, ale sprawdza każdy wynik, nie ufa — i odwrotnie, milczące
zatwierdzanie bez czytania to sygnał zaufania albo rezygnacji; rozstrzyga
dopiero pytanie o skutki błędu.

**Test dziennikowy wielotygodniowy.** Minimum cztery–sześć tygodni, bo dopiero
wtedy zachodzą zjawiska relacyjne: pierwsze wnioskowania systemu, pierwszy
awans autonomii, zwykle też pierwszy błąd. Uczestnik prowadzi krótkie wpisy po
sesjach (co delegował, co sprawdzał, co go zaskoczyło) uzupełnione wywiadami
co dwa tygodnie. Wpisy dziennika zestawiaj z telemetrią tego samego
uczestnika — rozjazd między relacją opowiedzianą a zarejestrowaną jest
najcenniejszym materiałem badania, nie błędem metody.

**Obserwacja momentu pierwszej delegacji nieodwracalnej.** Pierwsze
powierzenie systemowi działania, którego nie da się cofnąć, to najgęstszy
moment relacji — zaprojektuj badanie tak, by go uchwycić: telemetria
wyzwalająca krótki wywiad w ciągu doby od zdarzenia. Pytaj o wahanie (co
rozważał tuż przed), o zabezpieczenia własne (czy zrobił kopię, czy sprawdził
po fakcie) i o to, co przekonało go właśnie teraz. Analogicznie badaj moment
odwrotny: pierwsze ręczne obniżenie autonomii.

## Pułapki miar

**Optymalizacja przyjęć prowadzi do propozycji zachowawczych.** System karany
za odrzucenia nauczy się proponować tylko pewniaki — wskaźnik rośnie, wartość
maleje, bo najcenniejsze propozycje to te nieoczywiste. Zabezpieczenie:
raportuj wskaźnik przyjęć zawsze w parze z miarą śmiałości propozycji (np.
odsetkiem propozycji wykraczających poza dotychczasowe wybory użytkownika)
i pilnuj obu naraz. Spadek odrzuceń przy jednoczesnym spadku śmiałości to
regres udający postęp.

**Miara zaangażowania nagradza uzależnianie.** Czas w aplikacji, liczba sesji
i liczba interakcji rosną także wtedy, gdy system działa źle: wymusza
poprawki, dopytuje bez potrzeby, przerywa dla błahostek. W systemie agentowym
dobrze zaprojektowana autonomia skraca interakcje — sukcesem bywa sesja,
której nie było, bo skrzynka przeglądowa załatwiła sprawę w minutę. Miary
relacji mają mierzyć wartość dla użytkownika, nie przywiązanie: zamiast czasu
w aplikacji mierz odsetek spraw domkniętych bez eskalacji, czas użytkownika
oszczędzony względem ścieżki ręcznej i utrzymanie liczone decyzją powrotu przy
realnej alternatywie, nie siłą przyzwyczajenia.

**Miary stadiów mierzone bez kontekstu obszaru.** Uśrednienie autonomii po
całym systemie zamazuje obraz: relacja dojrzała w jednym obszarze i martwa
w innym to inny stan niż przeciętność wszędzie — a agregat pokaże to samo.
Każdą miarę relacji licz per obszar i dopiero potem, świadomie, agreguj.

**Wskaźnik jako cel.** Każda z miar tej karty przestaje działać, gdy staje się
celem zespołu (premiowanym progiem) zamiast instrumentem diagnozy. Miary
relacji trzymaj jako tablicę diagnostyczną z progami alarmowymi — nie jako
cele sprzedażowe.

## Progi alarmowe i przeglądy okresowe

Dla każdej miary zdefiniuj przy projekcie próg alarmowy — wartość, której
przekroczenie uruchamia analizę, nie panikę. Progi początkowe ustaw
zachowawczo i kalibruj po pierwszym kwartale danych; brak progu oznacza, że
miara jest ozdobą. Przykładowe konstrukcje progów (wartości liczbowe ustala
projekt na własnych danych): wskaźnik korekt pamięci dla wnioskowań rosnący
między przeglądami; odsetek relacji cofających autonomię ręcznie w obszarze;
czas zalegania decyzji w skrzynce przeglądowej przekraczający rytm pracy
użytkownika; odsetek odezwań proaktywnych zignorowanych lub zablokowanych;
spadek głębokości kontynuacji po zmianie wersji.

Przegląd projektu relacji prowadź w stałym rytmie (kwartalnym lub po każdej
istotnej zmianie zachowania systemu) i w stałym układzie: tablica miar
względem progów → incydenty i przebieg odbudowy → wnioski z korekt pamięci
(czego system nauczył się źle) → decyzje projektowe z właścicielem i terminem.
Do przeglądu wchodzą też dane jakościowe z bieżących badań — miara mówi, że
coś się dzieje; badanie mówi, dlaczego. Wynik przeglądu zapisuj w opracowaniu
UX projektu jako aktualizację stanu, zgodnie z zasadami dokumentacji
kanonicznej pluginu.
