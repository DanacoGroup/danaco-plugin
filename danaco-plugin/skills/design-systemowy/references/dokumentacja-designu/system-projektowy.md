# System projektowy — karta

Stosuj niniejszą kartę przy tworzeniu i utrzymywaniu systemu projektowego
(design system) oraz jego dokumentacji. Karta reguluje zawartość księgi
projektowej, sposób zapisu zasad i komponentów oraz egzekwowanie spójności.
Szczegóły dotyczące tokenów i CSS zawierają karty „Tokeny projektowe” i
„Standard CSS”.

## Zawartość księgi projektowej (design book)

Utrzymuj dokładnie jedną kanoniczną księgę projektową na produkt. Każdy inny
dokument o designie ma odsyłać do księgi, nie powielać jej treści — dwie
równoległe księgi nieuchronnie się rozjeżdżają.

Zawrzyj w księdze następujące części, w tej kolejności:

1. **Zasady i pryncypia projektowe** — kilka nadrzędnych reguł kierunkowych
   (np. „czytelność przed gęstością informacji”), każda z krótkim
   uzasadnieniem i przykładem zastosowania.
2. **Tokeny** — pełny wykaz tokenów projektu wraz z zasadami ich użycia
   (zob. karta „Tokeny projektowe”).
3. **Biblioteka komponentów** — każdy komponent udokumentowany według wzorca z
   sekcji „Dokumentacja komponentu”, zawsze łącznie ze stanami.
4. **Wzorce układów** — powtarzalne szablony stron i sekcji: strona listy,
   strona szczegółów, formularz, pusty stan, stany ładowania i błędu.
5. **Ton komunikatów** — zasady języka interfejsu: forma zwrotu do
   użytkownika, konstrukcja komunikatów o błędach, etykiety przycisków,
   terminologia produktu z listą pojęć zakazanych i preferowanych.

Aktualizuj księgę w tym samym zakresie prac, w którym zmienia się produkt.
Księga opisująca stan nieistniejący jest gorsza niż brak księgi, ponieważ
wprowadza w błąd.

## Zasady i polityka designu (design rules)

Zapisuj zasady designu jako reguły rozstrzygające — takie, które kończą spór,
zamiast go otwierać. Reguła ma wskazywać decyzję w konkretnej sytuacji, np.:

- **Modal czy strona:** stosuj modal dla krótkiej, przerywalnej decyzji w
  kontekście bieżącego widoku (potwierdzenie usunięcia); stosuj osobną stronę
  dla zadania wieloetapowego lub wymagającego własnego adresu URL (edycja
  profilu).
- **Hierarchia przycisków:** jeden przycisk podstawowy (primary) na widok;
  działania drugorzędne jako przyciski wtórne (secondary); działania
  destrukcyjne wyróżnione odrębnym stylem i potwierdzeniem.

Do każdej reguły dołącz dokładnie jedną parę przykładów: jeden przykład
poprawny („tak”) i jeden niepoprawny („nie”), oba osadzone w realiach produktu.
Reguła bez pary przykładów pozostaje interpretowalna dowolnie; reguła z
kilkunastoma przykładami rozmywa się w kazuistykę.

Formułuj reguły w trybie rozkazującym i dołączaj uzasadnienie jednym zdaniem —
zespół przestrzega reguł, które rozumie, i obchodzi te, które wyglądają na
arbitralne.

## Dokumentacja komponentu

Dokumentuj każdy komponent biblioteki według stałego wzorca:

1. **Anatomia** — nazwane części składowe (np. dla `Button`: container, icon,
   label) wraz ze wskazaniem części opcjonalnych.
2. **Warianty** — wyczerpująca lista wariantów z kryterium wyboru każdego z
   nich (np. `primary`, `secondary`, `danger`), nie sam wykaz nazw.
3. **Stany** — komplet: default, hover, focus-visible, active, disabled oraz —
   gdy dotyczy — loading, error, selected. Komponent opisany bez stanów
   traktuj jako nieudokumentowany.
4. **Zasady użycia i nadużycia** — kiedy komponent stosować i kiedy go nie
   stosować, ze wskazaniem właściwej alternatywy (np. „do nawigacji między
   widokami stosuj `Link`, nie `Button`”).
5. **Dostępność** — wymagane role i atrybuty ARIA, obsługa klawiatury,
   zachowanie fokusa, wymagania kontrastu wg WCAG 2.2 AA.
6. **Powiązane tokeny** — wykaz tokenów, z których komponent korzysta, aby
   skutki zmiany tokenu były możliwe do prześledzenia.

Nadawaj komponentom dokładnie jedną nazwę kanoniczną i stosuj ją wszędzie: w
księdze, w kodzie i w rozmowach. Zanim opiszesz „nowy” komponent, sprawdź, czy
nie jest wariantem komponentu istniejącego — w razie wątpliwości rozszerz
istniejący.

## Spójność i egzekwowanie

Włącz przegląd zgodności z systemem projektowym do standardowego przeglądu
kodu. Sprawdzaj przy każdej zmianie dotykającej interfejsu co najmniej:

- czy wartości wizualne pochodzą z tokenów, a nie są wpisane wprost;
- czy użyto komponentów z biblioteki zamiast konstrukcji doraźnych;
- czy nowy komponent lub wariant został dodany do księgi wraz ze stanami;
- czy nazwy klas i komponentów są zgodne z konwencją projektu;
- czy stany interaktywne i wymagania dostępności zostały zrealizowane.

Traktuj odstępstwo od systemu jako decyzję, nie zdarzenie: wymaga zgłoszenia,
uzasadnienia i akceptacji w przeglądzie, a zaakceptowane — odnotowania w
księdze (jako świadomy wyjątek albo jako zmiana reguły). Odstępstwo
niezgłoszone traktuj jak usterkę i cofaj.

Gdy ta sama potrzeba obchodzi system po raz kolejny, nie mnóż wyjątków —
rozbuduj system tak, aby potrzebę obsługiwał wprost.

## Typowe błędy modeli LLM przy systemach projektowych

Unikaj poniższych błędów, regularnie obserwowanych w dokumentacji generowanej
przez modele językowe:

1. Tworzenie dokumentu-wydmuszki — poprawna struktura nagłówków bez
   konkretnych wartości, przykładów i par „tak/nie”, czyli dokument, który
   niczego nie rozstrzyga.
2. Opisywanie komponentów bez stanów — sam wygląd domyślny, z pominięciem
   hover, focus-visible, disabled, loading i error.
3. Wprowadzanie synonimów nazw komponentów — `Dialog` obok `Modal`, `Chip`
   obok `Tag` — zamiast jednej nazwy kanonicznej na pojęcie.
4. Zapisywanie zasad bez uzasadnień — reguły brzmiące arbitralnie, których
   zespół nie rozumie i dlatego nie przestrzega.
5. Budowanie nowego systemu obok istniejącego zamiast rozbudowy tego, który
   już funkcjonuje w produkcie — najpierw zinwentaryzuj stan zastany.
6. Wymyślanie treści zastępczych przedstawianych jako fakty: fikcyjnych
   historii zmian, numerów wersji i nazwisk decydentów; braki oznaczaj jawnie
   jako do uzupełnienia.
7. Pomijanie sekcji dostępności lub zbywanie jej ogólnikiem, bez wskazania
   konkretnych wymagań WCAG 2.2, ról ARIA i obsługi klawiatury.
