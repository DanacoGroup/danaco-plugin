# Przegląd kodu — procedura

Procedura obejmuje przegląd zmiany przed scaleniem: co sprawdzać, w jakiej kolejności
i jak zapisać uwagę. Przegląd w ujęciu architektonicznym — granice modułów, kontrakty,
dług — prowadzi
`../architektura-i-dokumentacja/references/engineering-core/references/przeglad-kodu.md`.

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Przegląd
sprawdza kod, nie autora; wynik przeglądu to lista konkretnych ustaleń z dowodami, nie ogólna
opinia.

## Zakres przeglądu

Ustal najpierw, co dokładnie podlega przeglądowi: zakres zmian (`git diff`,
`git show`), pojedynczy plik czy moduł. Przeglądaj zmianę w kontekście — otwórz
także kod otaczający, wywołujący i wywoływany; większość poważnych usterek leży
na styku zmiany z resztą systemu.

## Kolejność sprawdzeń — od najpoważniejszych

Sprawdzaj w tej kolejności, aby czas przeglądu trafiał najpierw w usterki najdroższe:

### 1. Poprawność
- Czy kod robi to, co deklaruje nazwa i zadanie? Prześledź co najmniej jeden
  przepływ danych od wejścia do wyjścia.
- Przypadki brzegowe: wartość pusta, zero, ujemna, bardzo duża, kolekcja pusta,
  tekst z polskimi znakami, strefa czasowa, współbieżny dostęp.
- Obsługa niepowodzeń każdego styku z zewnętrzem (plik, sieć, baza, proces):
  co się dzieje, gdy operacja zawiedzie w połowie?

### 2. Bezpieczeństwo
- Wstrzyknięcia: SQL budowany doklejaniem tekstu (CWE-89), polecenia powłoki
  z danymi użytkownika (CWE-78), XSS w treści HTML (CWE-79).
- Sekrety w kodzie lub w repozytorium; dane osobowe w dziennikach zdarzeń.
- Walidacja danych wejściowych po stronie serwera; uprawnienia sprawdzane przy
  każdej operacji, nie tylko w interfejsie.
- Deserializacja niezaufanych danych, ścieżki plików sklejane z danych użytkownika.

### 3. Wydajność
- Zapytania w pętli (problem N+1), pobieranie całej tabeli dla jednego wiersza,
  brak indeksu pod często filtrowaną kolumną.
- Operacje blokujące w kodzie asynchronicznym; wczytywanie dużych plików w całości
  do pamięci bez potrzeby.
- Oceniaj wydajność na poziomie mechanizmu (złożoność, liczba zapytań, liczba
  odczytów), nie mikrooptymalizacji stylistycznych.

### 4. Utrzymywalność i zgodność ze standardami Danaco
- Kontrola końcowa z `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` zastosowana do
  przeglądanego kodu: historia w komentarzach, wymyślone kody, etykiety własne zamiast terminologii
  zawodowej, pliki-narośle i kopie `_v2`, kod martwy i wykomentowany, język nieprofesjonalny w
  treściach trwałych.
- Nazewnictwo i styl zgodne z konwencją języka — sprawdź według karty języka w
  `../kodowanie/references/jezyki-programowania/jezyki-programowania.md` oraz konwencji zastanej w
  projekcie.
- Duplikacja logiki już istniejącej w projekcie; funkcje o mylących nazwach;
  komentarze opisujące „co” zamiast „dlaczego”.

### 5. Testy
- Czy zmiana jest objęta testem, który wykryłby jej cofnięcie?
- Czy testy sprawdzają zachowanie (wynik), a nie implementację (kolejność wywołań)?
- Czy nie usunięto ani nie wyłączono istniejących testów?

## Weryfikacja ustaleń przed zgłoszeniem

Każde ustalenie przeglądu potwierdź przed zgłoszeniem: wskaż plik i wiersz, opisz
scenariusz niepowodzenia (konkretne dane → konkretny błędny skutek), a gdy to możliwe —
wykonaj kod lub minimalny przykład potwierdzający. Ustalenie, którego nie potrafisz
poprzeć scenariuszem, oznacz wprost jako przypuszczenie. Zgłaszanie domysłów jako
usterek podważa zaufanie do całego przeglądu.

## Raport z przeglądu

Raport przekaż w rozmowie (bez tworzenia pliku), w kolejności od usterek
najpoważniejszych. Dla każdego ustalenia podaj:

1. miejsce (plik, wiersz),
2. kategorię (poprawność / bezpieczeństwo / wydajność / utrzymywalność / testy),
3. scenariusz niepowodzenia lub uzasadnienie,
4. proponowaną poprawkę — konkretną, najmniejszą usuwającą problem.

Rozdziel wyraźnie: usterki wymagające naprawy przed scaleniem, zalecenia oraz
uwagi drobne. Jeżeli kod jest poprawny — napisz to wprost; przegląd bez ustaleń
też jest wynikiem. Nie zgłaszaj uwag czysto stylistycznych tam, gdzie styl jest
zgodny z konwencją projektu.

## Karty referencyjne

Karty wczytuj według potrzeby przeglądu — nie wszystkie naraz:

| Karta | Zawartość | Kiedy wczytać |
|---|---|---|
| `references/przeglad-kodu/katalog-usterek.md` | Katalog usterek do wykrywania: bezpieczeństwo (wstrzyknięcia, deserializacja, SSRF, IDOR, sekrety, losowość), poprawność (TOCTOU, strefy czasowe, pieniądze, Unicode), współbieżność, wydajność, utrzymywalność — każda pozycja z sygnaturą, scenariuszem niepowodzenia i poprawką wzorcową | Przy każdym przeglądzie merytorycznym — jako lista kontrolna sprawdzeń 1–4 |
| `references/przeglad-kodu/techniki-przegladu.md` | Warsztat przeglądającego: kolejność czytania zmiany wg jej rodzaju, śledzenie danych nieufnych, granice zaufania, pytania do autora, zmiany szerokie i wygenerowane (w tym kod z modeli LLM), migracje bazy, przegląd testów, kalibracja głębokości wg ryzyka, higiena komunikacji ustaleń | Przy planowaniu przeglądu oraz przy zmianach nietypowych: szerokich, wygenerowanych, migracjach |
| `references/przeglad-kodu/przeglad-wg-jezykow.md` | Sygnatury usterek specyficzne językowo: Python, JavaScript/TypeScript, SQL, C/C++, Go, C#/Java, PowerShell/bash — każda pozycja: sygnatura → skutek → poprawka | Po ustaleniu języka przeglądanej zmiany — jako lista kontrolna dla tego języka |
