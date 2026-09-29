# Projektowanie banerów — karta

Stosuj niniejszą kartę przy projektowaniu banerów reklamowych, nagłówków profili społecznościowych i
grafik kampanijnych. Baner ma przekazać jeden komunikat i skłonić do jednego działania; wszystkie
decyzje projektowe podporządkuj temu celowi.

## Wymagania wstępne

Przed rozpoczęciem projektu ustal i zapisz następujące dane; nie rozpoczynaj projektowania bez nich:

- **Cel i wezwanie do działania.**
  - Określ, co odbiorca ma zrobić po zobaczeniu banera (np. przejść na stronę, zapisać się, pobrać
    materiał).
  - Ustal dokładne brzmienie wezwania do działania; jedno wezwanie na baner.
- **Format i medium docelowe.**
  - Ustal, gdzie baner będzie wyświetlany: sieć reklamowa, serwis społecznościowy, strona firmowa,
    druk.
  - Ustal wymagane wymiary w pikselach (lub milimetrach dla druku) oraz liczbę wymaganych wariantów
    rozmiaru.
- **Obowiązujące elementy identyfikacji.**
  - Pobierz plik znaku we właściwej wersji (podstawowa, monochromatyczna, kontra) z zasobów
    firmowych.
  - Pobierz wartości palety i nazwy krojów z księgi znaku lub pliku palety; nie przyjmuj ich z
    pamięci.
  - Zastosuj zasady pola ochronnego i rozmiarów minimalnych znaku.
- **Tekst dosłowny.**
  - Uzyskaj ostateczne brzmienie nagłówka, tekstu towarzyszącego i wezwania do działania.
  - Nie projektuj na tekstach zastępczych; zmiana tekstu po zakończeniu projektu wymusza zmianę
    kompozycji.

Jeżeli którejkolwiek z powyższych informacji brakuje, zadaj pytanie zamawiającemu, zamiast
przyjmować założenia.

## Formaty

- Dla banerów reklamowych w sieciach display stosuj standardowe formaty IAB. Najczęściej
  wykorzystywane:
  - 300x250 px — medium rectangle; format uniwersalny, osadzany w treści stron,
  - 728x90 px — leaderboard; górny pas na stronach na ekrany komputerów,
  - 160x600 px — wide skyscraper; pionowy format w kolumnach bocznych,
  - 320x50 px — poziomy pas na urządzenia przenośne,
  - 970x250 px — billboard; duży format ekspozycyjny nad treścią strony.
- Dla serwisów społecznościowych stosuj wymiary wymagane aktualnie przez daną platformę (grafiki w
  publikacjach, nagłówki profili, formaty pionowe relacji). Wymiary platform społecznościowych
  zmieniają się; przed projektem zweryfikuj aktualne wartości w oficjalnej specyfikacji platformy,
  zamiast polegać na wartościach zapamiętanych.
- Dobieraj format do medium i miejsca ekspozycji:
  - formaty poziome i billboardy — ekrany komputerów,
  - formaty drobne poziome (np. 320x50 px) — urządzenia przenośne,
  - formaty pionowe — kolumny boczne stron oraz relacje w serwisach społecznościowych.
- Przestrzegaj limitów wagi pliku:
  - sieci reklamowe ograniczają wagę kreacji; zależnie od sieci i formatu limity wynoszą zwykle od
    kilkudziesięciu do ok. 150 kB dla standardowych banerów display,
  - przed publikacją zweryfikuj limit obowiązujący w docelowej sieci i skompresuj plik poniżej tego
    limitu,
  - dla materiałów na strony własne firmy stosuj wagę możliwie najniższą przy zachowaniu jakości.

## Kompozycja i hierarchia

- Buduj baner wokół jednego przekazu głównego; usuń wszystko, co temu przekazowi nie służy.
- Zachowuj hierarchię elementów w kolejności: nagłówek → korzyść → wezwanie do działania → logo.
  - Nagłówek: największy element tekstowy, komunikuje sedno.
  - Korzyść: krótkie rozwinięcie, jeżeli format daje na nie miejsce; w formatach drobnych pomiń.
  - Wezwanie do działania: wyróżnione wizualnie, jednoznaczne, z czasownikiem w formie rozkazującej.
  - Logo: obecne, lecz podporządkowane przekazowi; zwykle w narożniku, z zachowaniem pola
    ochronnego.
- Prowadź wzrok zgodnie z kierunkiem czytania (w układzie polskim: od lewej do prawej, z góry na
  dół); nie zmuszaj odbiorcy do powrotów.
- Pozostawiaj przestrzeń negatywną wokół elementów kluczowych; nie zapełniaj całej powierzchni.
- Utrzymuj elementy krytyczne (tekst, wezwanie, logo) z dala od krawędzi formatu, w środkowej
  strefie kompozycji.
- Zapewnij elementowi głównemu najwyższy kontrast w kompozycji — względem tła i względem elementów
  drugorzędnych.

## Typografia i czytelność

- Ograniczaj liczbę krojów do dwóch na baner; preferuj kroje firmowe, a różnicowanie uzyskuj
  odmianami grubości.
- Przestrzegaj rozmiarów minimalnych dla czytelności:
  - w formatach drobnych (np. 320x50 px) skracaj tekst zamiast zmniejszać stopień pisma poniżej
    progu czytelności,
  - traktuj ok. 16 px jako dolną granicę dla tekstu towarzyszącego na ekranie, a nagłówek składaj
    wyraźnie większym stopniem,
  - oceniaj czytelność w skali 100% na docelowym rozmiarze, nie w powiększeniu roboczym.
- Zapewniaj kontrast tekstu zgodny z WCAG 2.2:
  - co najmniej 4,5:1 dla tekstu w rozmiarze zwykłym,
  - co najmniej 3:1 dla tekstu dużego (co najmniej 18 pkt lub 14 pkt pogrubionego).
- Nie umieszczaj tekstu na ruchliwym tle: na wzorzystych fragmentach fotografii, na obszarach o
  dużej zmienności jasności ani na animowanych partiach kreacji. W razie potrzeby stosuj aplę,
  przyciemnienie lub jednolity obszar pod tekstem.
- Nie składaj dłuższych partii tekstu wersalikami; wersaliki rezerwuj dla krótkich haseł i wezwania
  do działania.

## Produkcja i eksport

- Projektuj w HTML/CSS albo w narzędziu graficznym, zależnie od formatu docelowego i wymagań sieci:
  - HTML/CSS ułatwia utrzymanie wielu wariantów rozmiaru z jednego źródła i precyzyjne odwzorowanie
    typografii,
  - narzędzie graficzne stosuj, gdy wymagany jest wyłącznie plik rastrowy lub materiał do druku.
- Eksportuj do formatów i rozmiarów wymaganych przez medium docelowe:
  - dla sieci reklamowych: pliki rastrowe (PNG lub JPG) albo kreacje HTML5, zgodnie ze specyfikacją
    sieci,
  - dla druku: pliki w CMYK, w rozdzielczości produkcyjnej wymaganej przez drukarnię, ze spadami.
- Kompresuj pliki eksportowane na ekran do wagi poniżej limitu medium; sprawdzaj jakość po kompresji
  na docelowym rozmiarze.
- Przygotowuj komplet wariantów rozmiarów ustalony w wymaganiach wstępnych; nie kończ pracy po
  wyeksportowaniu jednego rozmiaru.
- Stosuj nazewnictwo plików według formatu i wariantu, spójne i opisowe:
  - zawrzyj w nazwie kampanię lub temat, wariant kreacji oraz wymiary, np.
    `kampania-jesien_wariant-a_300x250.png`,
  - używaj małych liter, bez spacji i polskich znaków diakrytycznych w nazwach plików,
  - stosuj identyczny schemat nazw dla wszystkich plików jednej kampanii,
  - grupuj pliki jednej kampanii w jednym katalogu.

## Typowe błędy modeli LLM przy banerach

Unikaj następujących błędów, charakterystycznych dla pracy modeli językowych:

1. **Przeładowanie treścią.**
   Nie umieszczaj na banerze kilku komunikatów, list zalet ani rozbudowanych opisów.
   Jeden przekaz, jedno wezwanie do działania.
2. **Wezwanie do działania niewidoczne.** Nie traktuj wezwania jako zwykłego tekstu; wyróżnij je
   kontrastem, wielkością lub formą przycisku i nie zasłaniaj go innymi elementami.
3. **Wymyślanie kolorów marki.**
   Nie stosuj wartości kolorów przyjętych z pamięci ani „podobnych” do firmowych.
   Pobieraj wartości z księgi znaku lub pliku palety; w razie braku źródła — zapytaj.
4. **Tekst poniżej progu czytelności.**
   Nie zmniejszaj stopnia pisma, aby zmieścić całą treść w małym formacie.
   Skracaj treść i sprawdzaj czytelność w skali 100%.
5. **Brak wariantów rozmiarów.**
   Nie kończ zadania po przygotowaniu jednego formatu, jeżeli kampania wymaga kompletu rozmiarów.
   Dostosuj kompozycję do każdego formatu; nie skaluj mechanicznie jednej kreacji.
6. **Niespójne nazwy plików eksportu.**
   Nie nadawaj plikom nazw przypadkowych ani różniących się schematem w obrębie kampanii.
   Stosuj jeden ustalony schemat: kampania, wariant, wymiary.
7. **Ignorowanie limitów wagi.** Nie przekazuj plików bez sprawdzenia wagi względem limitu sieci
   reklamowej; kreacja przekraczająca limit zostanie odrzucona.
8. **Tekst na ruchliwym tle.** Nie kładź tekstu bezpośrednio na wzorzystych fotografiach ani
   gradientach o zmiennej jasności bez apli lub przyciemnienia.
