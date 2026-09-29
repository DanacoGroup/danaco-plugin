# Opracowania UI/UX — karta

Stosuj niniejszą kartę przy tworzeniu i aktualizowaniu opracowań projektowych: przepływów,
specyfikacji widoków, zapisów badań i decyzji projektowych. Opracowanie ma umożliwić wdrożenie i
weryfikację rozwiązania bez dopytywania autora. Pisz zwięźle, jednoznacznie i w formie
umożliwiającej utrzymanie dokumentu w czasie.

## Rodzaje opracowań

Rozróżniaj cztery podstawowe rodzaje opracowań i nie mieszaj ich w jednym dokumencie:

- **Mapa przepływów użytkownika.**
  Opisuje drogę użytkownika przez produkt: stany, decyzje, przejścia między ekranami.
  Odpowiada na pytanie, jak użytkownik osiąga cel i co się dzieje, gdy zbacza ze ścieżki.
- **Specyfikacja ekranu/widoku.**
  Opisuje pojedynczy ekran lub widok: układ, komponenty, stany, treści, zachowania brzegowe.
  Stanowi podstawę implementacji i odbioru.
- **Zapis badania z użytkownikami.**
  Dokumentuje cel, metodę, uczestników, obserwacje i wnioski z badania.
  Oddziela fakty od interpretacji.
- **Zapis decyzji projektowej.** Utrwala rozstrzygnięcie: kontekst, rozważane warianty, wybrany
  wariant, uzasadnienie i konsekwencje. Zapobiega ponownemu otwieraniu zamkniętych dyskusji bez
  nowych przesłanek.

Utrzymuj jedno opracowanie kanoniczne na temat:

- Zanim utworzysz nowy dokument, sprawdź, czy opracowanie danego tematu już istnieje.
- Jeżeli istnieje — edytuj je i aktualizuj, zamiast tworzyć dokument równoległy.
- Wersje robocze i warianty oznaczaj jednoznacznie i usuwaj po scaleniu do dokumentu kanonicznego.

## Dokumentowanie przepływów

- Zapisuj przepływ jako sekwencję stanów i decyzji użytkownika, nie jako listę ekranów.
- Dla każdego kroku określ:
  - stan początkowy (co użytkownik widzi i wie),
  - działanie użytkownika lub zdarzenie systemowe,
  - wynik (nowy stan, komunikat, przejście).
- Punkty decyzyjne zapisuj jawnie, wraz ze wszystkimi gałęziami; nie pozostawiaj gałęzi
  „oczywistych” bez opisu.
- Ścieżki błędów dokumentuj obowiązkowo:
  - błędy walidacji i błędy systemowe,
  - brak uprawnień,
  - przerwanie procesu i powrót do niego,
  - utrata połączenia lub przeterminowanie sesji, jeżeli dotyczy.
- Puste stany dokumentuj obowiązkowo: pierwszy kontakt z funkcją, brak danych, brak wyników
  wyszukiwania.
- Stosuj nazwy ekranów spójne z kodem:
  - używaj identyfikatorów ekranów obowiązujących w repozytorium (nazwy tras, komponentów lub
    widoków),
  - przy pierwszym użyciu nazwy podaj jej odpowiednik w kodzie, jeżeli nazwa opisowa różni się od
    technicznej,
  - po zmianie nazwy w kodzie zaktualizuj opracowanie w tym samym zakresie prac.

## Specyfikacja widoku

Kompletna specyfikacja widoku zawiera następujące elementy:

- **Układ.** Opisz strukturę widoku: strefy, siatkę, kolejność elementów, zachowanie przy różnych
  szerokościach ekranu.
- **Komponenty z systemu projektowego.** Wskazuj komponenty po ich nazwach z systemu projektowego,
  wraz z wariantem i rozmiarem. Nowy komponent lub odstępstwo od systemu opisuj jawnie i uzasadniaj;
  nie wprowadzaj odstępstw milcząco.
- **Stany.** Opisz wszystkie stany widoku i jego kluczowych elementów: domyślny, ładowania, pusty,
  błędu, wyłączony, tylko do odczytu — w zakresie, w jakim dotyczą widoku.
- **Treści komunikatów.**
  Podawaj dosłowne brzmienie nagłówków, etykiet, komunikatów błędów i potwierdzeń.
  Nie zostawiaj w specyfikacji tekstów zastępczych typu „komunikat błędu” bez treści.
- **Zachowania brzegowe.** Opisz zachowanie przy skrajnych danych: bardzo długie teksty, wartości
  zerowe i maksymalne, duża liczba pozycji, brak uprawnień do części danych.
- **Kryteria ukończenia.** Zakończ specyfikację listą sprawdzalnych warunków odbioru, sformułowanych
  tak, aby osoba testująca mogła jednoznacznie orzec: spełnione albo niespełnione.

## Zapis badań i wniosków

- Rozpocznij od metryki badania:
  - cel (na jakie pytanie badanie ma odpowiedzieć),
  - metoda (np. wywiad, test użyteczności, ankieta) wraz z krótkim uzasadnieniem doboru,
  - uczestnicy: liczba, sposób rekrutacji, istotne cechy grupy — bez danych osobowych.
- Nie umieszczaj w opracowaniu danych osobowych uczestników: imion i nazwisk, adresów e-mail, nazw
  pracodawców ani innych informacji umożliwiających identyfikację.
- Oznaczaj uczestników kodami (np. U1, U2) spójnymi w całym dokumencie.
- Oddzielaj obserwacje od interpretacji:
  - obserwacja: co uczestnik zrobił lub powiedział — zapis faktograficzny,
  - interpretacja: co to może oznaczać — zapis oznaczony jako wniosek autora.
- Nie formułuj wniosków niepopartych obserwacją; przy każdym wniosku wskaż obserwacje, z których
  wynika.
- Nadawaj wnioskom priorytety (np. krytyczny, istotny, drobny) według wpływu na cel użytkownika i
  częstości wystąpienia.
- Odróżniaj wnioski od rekomendacji: wniosek opisuje problem, rekomendacja proponuje działanie;
  rekomendacje oznaczaj jako propozycje do decyzji zespołu.

## Typowe błędy modeli LLM w opracowaniach UX

Unikaj następujących błędów, charakterystycznych dla pracy modeli językowych:

1. **Dokumentowanie wyłącznie ścieżki szczęśliwej.**
   Nie kończ pracy nad przepływem po opisaniu wariantu, w którym wszystko się udaje.
   Ścieżki błędów, przerwania i puste stany są obowiązkową częścią opracowania.
2. **Makiety i specyfikacje bez stanów błędów.**
   Nie przekazuj specyfikacji widoku, która opisuje wyłącznie stan domyślny z poprawnymi danymi.
3. **Wnioski niepoparte obserwacją.** Nie dopisuj do zapisu badania wniosków ogólnych,
   prawdopodobnych „z doświadczenia” lub wynikających z wiedzy modelu, a nie z materiału badawczego.
4. **Mnożenie plików opracowań zamiast edycji kanonicznego.**
   Nie twórz plików typu „wersja-2”, „final”, „poprawione” obok istniejącego dokumentu.
   Edytuj dokument kanoniczny i pozostaw historię zmian systemowi kontroli wersji.
5. **Nazwy ekranów rozjechane z kodem.**
   Nie wymyślaj własnych nazw ekranów, gdy repozytorium definiuje już nazewnictwo tras i widoków.
   Przed napisaniem opracowania sprawdź nazwy w kodzie.
6. **Uzupełnianie luk zmyśleniami.** Nie wypełniaj brakujących informacji (treści komunikatów, reguł
   biznesowych, limitów) własnymi założeniami przedstawianymi jako ustalenia. Braki oznaczaj jawnie
   jako pytania otwarte i kieruj do właściciela tematu.
7. **Specyfikacja oderwana od systemu projektowego.** Nie opisuj elementów interfejsu ogólnikami
   („przycisk”, „okno”), gdy system projektowy definiuje konkretne komponenty i ich warianty.
8. **Kryteria ukończenia niesprawdzalne.**
   Nie formułuj kryteriów typu „widok ma być czytelny i intuicyjny”.
   Formułuj warunki, których spełnienie można jednoznacznie zweryfikować.
