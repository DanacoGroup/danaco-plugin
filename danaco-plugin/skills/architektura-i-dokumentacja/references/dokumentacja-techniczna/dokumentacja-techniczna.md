# Dokumentacja techniczna — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`), w
szczególności zasada 4 (dyscyplina plików) i zasada 7 (profesjonalny język). Dokumentacja podlega
tym samym rygorom co kod: jedno źródło prawdy, żadnych kopii, żadnych plików-narośli.

## Zasady nadrzędne

1. **Jeden temat — jeden dokument kanoniczny.** Nową treść wprowadza się edycją
   właściwego dokumentu, nigdy utworzeniem pliku obok (`ANALIZA_v2.md`,
   `NOTATKI.md`). Zbiór dokumentów projektu jest zamknięty i uzgodniony
   z właścicielem; nowy dokument wymaga jego zgody.
2. **Dokumentacja opisuje stan obecny.** Historia zmian należy do Git
   i CHANGELOG.md. W treści dokumentu nie ma sekcji „historia wersji”,
   dat aktualizacji akapitów ani przekreśleń „wcześniej było”.
3. **Prawda przed kompletnością.** Każde twierdzenie o systemie sprawdź w kodzie,
   konfiguracji lub przez uruchomienie — dokumentacja pisana z pamięci
   o cudzym kodzie to fabulacja. Czego nie zweryfikowano, oznacz wprost.
4. **Terminologia jak w kodzie.** Pojęcia noszą dokładnie te nazwy, które mają
   w kodzie i architekturze (zasada 3 standardów). Dokument nie wprowadza
   własnych synonimów ani wymyślonych oznaczeń.
5. **Pisz dla wskazanego czytelnika.** Przed pisaniem ustal, kto będzie czytać
   (programista przejmujący projekt, administrator, decydent) i co ma umieć
   po lekturze — to rozstrzyga o doborze treści lepiej niż objętość.

## Układy dokumentów

**README.md** — przeznaczenie projektu (2–3 zdania), wymagania, instalacja
i uruchomienie (polecenia dosłowne, sprawdzone na czystym środowisku),
konfiguracja, sposób uruchomienia testów. Bez historii projektu i planów.

**Dokumentacja API** — dla API w FastAPI źródłem prawdy jest specyfikacja
OpenAPI generowana z kodu; dokument ręczny opisuje tylko to, czego schemat
nie niesie: scenariusze użycia, kolejność wywołań, zasady uwierzytelnienia,
obsługę błędów. Przykłady żądań i odpowiedzi — wykonane naprawdę, nie ułożone.

**Dokument architektury** — układ i zawartość według `references/architektura/architektura.md`
(granice modułów, model danych, zapisy decyzji ADR). Jeden na projekt.

**Runbook (procedura eksploatacyjna)** — po jednej procedurze na scenariusz:
cel, warunki wstępne, kroki z dosłownymi poleceniami i oczekiwanym wynikiem
każdego kroku, postępowanie przy niepowodzeniu, sposób wycofania. Procedurę
przetestuj wykonując ją krok po kroku — runbook niesprawdzony jest groźniejszy
niż jego brak.

**Opracowanie technologiczne / analiza** — pytanie badawcze, kryteria oceny
ustalone przed badaniem, badane warianty, wyniki z dowodami (pomiary, próby,
źródła), wnioski i rekomendacja. Rekomendacja wynika z kryteriów, nie odwrotnie.
Źródła przywołuj rzeczywiste (dokumentacja producenta, normy, pomiary własne).

## Styl

Formalna polszczyzna według zasady 7 standardów. Zdania oznajmujące, strona
czynna, polecenia w blokach kodu dosłownie. Bez zdrobnień, żartów i emotikonów.
Skróty tylko powszechnie uznane. Rysunki i diagramy tylko tam, gdzie niosą
informację, której tekst nie odda zwięźlej — diagram wymaga tych samych nazw
pojęć co kod i tekst.

## Utrzymanie

Dokumentacja zmienia się w tej samej rewizji co kod, który opisuje — rozjazd dokumentacji z kodem to
usterka wykrywana w przeglądzie kodu
(`../kontrola-jakosci/references/przeglad-kodu/przeglad-kodu.md`, wymiar utrzymywalności). Przy
przejęciu projektu z dokumentacją rozproszoną: najpierw inwentaryzacja i uzgodnienie z właścicielem
zbioru kanonicznego, potem scalenie treści i usunięcie plików zbędnych — historia pozostaje w Git.

## Karty referencyjne

Karty w katalogu `references/dokumentacja-techniczna/` pogłębiają procedurę. Wczytaj kartę przed
rozpoczęciem pracy objętej jej zakresem.

| Karta | Zakres | Kiedy wczytać |
|---|---|---|
| `references/dokumentacja-techniczna/pakiet-dokumentacji-systemu.md` | Metoda wytworzenia kompletnego pakietu dokumentacji architektury systemu: skład kanoniczny opracowań i kolejność powstawania, standard redakcyjny (nagłówek redakcyjny, spis treści, załączniki scenariuszowe, stopka), README-indeks jako dokument zarządzający, procedura wytwarzania od inwentaryzacji po kontrolę kompletności, kryteria jakości dokumentu 30–110 tys. znaków, utrzymanie pakietu. | Zawsze, gdy powstaje lub jest porządkowany zbiór opracowań projektowych systemu — od koncepcji, przez architekturę i model danych, po system wizualny — albo pojedynczy dokument tego zbioru. |
| `references/dokumentacja-techniczna/warsztat-pisarski.md` | Warsztat pisania technicznego: architektura informacji dokumentu, zasada piramidy, akapit jako jednostka, kryteria wyboru tabela/proza/diagram, pisanie procedur, pary źle→dobrze, pułapki polszczyzny technicznej, redakcja własnego tekstu (przejście skracające −20%, czytanie na głos, kontrola terminologii grepem). | Przy pisaniu każdego dokumentu dłuższego niż strona oraz przy redakcji lub ocenie cudzego tekstu technicznego. |
| `references/dokumentacja-techniczna/dokumentacja-api-i-runbook.md` | Dokumentacja API ponad schemat (scenariusze wielokrokowe, idempotentność i ponawianie, paginacja, wersjonowanie i wygaszanie, przykłady wykonane naprawdę, błędy jako kontrakt), runbook klasy operacyjnej (struktura, diagnoza niepowodzeń, wycofanie, eskalacja, test przez wykonanie, awaria vs rutyna), przewodnik wdrożeniowy on-premise z listą kontrolną odbioru. | Przy dokumentowaniu interfejsu API, pisaniu lub testowaniu procedury eksploatacyjnej albo przygotowaniu przewodnika wdrożeniowego. |
