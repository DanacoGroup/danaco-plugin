# Standardy zawodowe Danaco Code — standard współdzielony

Plik obowiązuje wszystkie paczki pluginu i leży w jednej kanonicznej kopii w
`wspolne/standardy-zawodowe/`. Paczki odsyłają do niego ścieżką
`../../wspolne/standardy-zawodowe/<plik>.md`, liczoną od katalogu paczki; kopii lokalnych nie ma i
nie wolno ich zakładać. Karty pogłębione tego standardu wskazuje rozdział „Karty referencyjne” na
końcu pliku.

Standard definiuje dyscyplinę zawodową obowiązującą we wszystkich pracach nad kodem
w projektach Danaco. Paczki `kodowanie`, `architektura-i-dokumentacja`, `kontrola-jakosci`
i `design-systemowy` zakładają, że zasady opisane tutaj są zawsze spełnione. W razie
konfliktu wskazówek — te zasady mają pierwszeństwo.

Powód istnienia tego standardu: modele LLM mają utrwalone nawyki, które w krótkiej sesji
wyglądają na pomocne, a w wielomiesięcznym projekcie niszczą spójność kodu i dokumentacji.
Poprzednie przebudowy systemów Danaco upadały właśnie przez niespójne nazewnictwo
i rozproszoną, samorodną dokumentację. Każda z poniższych zasad usuwa jeden taki nawyk.

## 1. Kod nie jest kroniką — zakaz historii w komentarzach

Historię zmian przechowuje system kontroli wersji (Git) oraz plik CHANGELOG.md.
Komentarz w kodzie opisuje wyłącznie stan obecny i uzasadnienie („dlaczego tak”),
nigdy przebieg prac.

Zabronione w komentarzach i kodzie:
- adnotacje o przebiegu zmian: `// zmieniono 2026-08-01`, `// poprawka po awarii`, `// wcześniej
  było X`
- kod wykomentowany „na zapas” — usuń go; Git pamięta
- sekcje typu „Historia wersji”, „Changelog”, „Dziennik zmian” wewnątrz plików źródłowych
- odwołania do rozmów, sesji, poleceń: `// zgodnie z ustaleniami`, `// na prośbę użytkownika`

Poprawny komentarz uzasadnia decyzję nieoczywistą dla czytelnika kodu:

```python
# Limit 5 MB wynika z ograniczenia bramki SMS operatora (dokumentacja API, rozdz. 4.2).
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
```

Zapis o tym, ŻE coś zmieniono i KIEDY, trafia wyłącznie do komunikatu rewizji Git
oraz — dla zmian istotnych dla użytkowników — do CHANGELOG.md.

## 2. Zakaz wymyślonych kodów, sygnatur i systemów numeracji

Nie twórz własnych kodów, skrótów ani numeracji w rodzaju `ADL27/P-1`, `FIX-3b`,
`[T4/K2]`, `ETAP-A.2`. Takie oznaczenia nic nie znaczą poza sesją, w której powstały;
po tygodniu są nieczytelne nawet dla autora, a w projekcie tworzą pozór systematyki,
za którym nie stoi żaden rejestr.

Stosuj wyłącznie identyfikatory zakotwiczone w rzeczywistych systemach:
- numer zgłoszenia z rzeczywistego systemu śledzenia (np. `#142` w repozytorium projektu),
- oznaczenia standardów branżowych: PEP 8, RFC 5321, ISO 8601, CWE-89, SemVer,
- rzeczywiste kody błędów platformy: `ECONNREFUSED`, `HTTP 422`, `SQLSTATE 23505`.

Jeżeli pojęcie wymaga oznaczenia, a żaden istniejący system go nie obejmuje —
użyj pełnej, opisowej nazwy słownej zamiast kodu.

## 3. Nazewnictwo: terminologia zawodowa zamiast etykiet własnych

Nie nadawaj pojęciom abstrakcyjnych, autorskich określeń („rdzeń”, „sonda”, „strażnik”,
„kapsuła”) i nie rozsiewaj ich po plikach oraz komentarzach. Nazywaj rzeczy terminami
przyjętymi w zawodzie: walidator, bufor, kolejka, migracja, repozytorium, moduł uwierzytelniania.

Przed wprowadzeniem nowej nazwy sprawdź, jak to pojęcie jest już nazwane w projekcie
(przeszukaj kod i dokumentację) — jedno pojęcie ma dokładnie jedną nazwę w całym
projekcie: w kodzie, dokumentacji, komunikatach i testach. Synonimy traktuj jak usterkę.

Identyfikatory w kodzie (nazwy zmiennych, funkcji, klas, tabel) pisz po angielsku,
zgodnie z konwencją danego języka, chyba że zastany projekt konsekwentnie stosuje
inną konwencję — wtedy podporządkuj się zastanej. Komentarze i dokumentację pisz
w języku przyjętym w projekcie, konsekwentnie w całym pliku.

## 4. Dyscyplina plików: żadnych plików-narośli

W projekcie istnieje zamknięty zbiór opracowań kanonicznych — zwykle README.md,
CHANGELOG.md oraz dokumenty jawnie uzgodnione z właścicielem projektu. Wszystko inne
to narośl.

Zabronione:
- tworzenie plików typu `NOTATKI.md`, `PODSUMOWANIE.md`, `PLAN.md`, `FIXES.md`,
  `ANALIZA_v2.md` obok istniejących opracowań — nową treść wprowadza się edycją
  właściwego dokumentu kanonicznego,
- kopie plików w rodzaju `main_v2.py`, `app_final.js`, `stary_index.html` —
  wersjonowanie zapewnia Git; plik ma jedną, właściwą nazwę i edytuje się go w miejscu,
- pliki-atrapy i szkielety „na przyszłość” (puste moduły, nieużywane klasy) —
  kod powstaje wtedy, gdy jest potrzebny.

Jeżeli zadanie wymaga dokumentu, którego nie ma w zbiorze kanonicznym — zapytaj
właściciela projektu przed utworzeniem pliku, wskazując dokładnie jeden proponowany
plik i jego przeznaczenie. Wyniki pośrednie i brudnopisy trzymaj poza katalogiem
projektu (katalog tymczasowy), nigdy w repozytorium.

## 5. Przyczyna źródłowa zamiast poprawki objawowej

Usterkę naprawia się u źródła, po zrozumieniu mechanizmu powstania — nie przez
zamaskowanie objawu. Szczegółową procedurę diagnostyczną zawiera
`skills/kodowanie/references/debugowanie/debugowanie.md`;
na poziomie standardu obowiązuje minimum:

- nie wyciszaj błędów pustym `try/except` ani `catch` — obsłuż albo propaguj,
- nie usuwaj i nie wyłączaj testu, który nie przechodzi — test to informacja o usterce,
- nie dopisuj warunków specjalnych maskujących pojedynczy przypadek, gdy zawodzi reguła ogólna,
- zanim ogłosisz naprawę, odtwórz pierwotny błąd i wykaż, że po zmianie nie występuje.

## 6. Weryfikacja zamiast deklaracji

Nie deklaruj, że kod działa — wykaż to. Przed przekazaniem pracy:
- uruchom kod lub testy i przytocz rzeczywisty wynik uruchomienia,
- interfejsy zewnętrzne (funkcje bibliotek, punkty końcowe API, kolumny tabel)
  sprawdzaj w rzeczywistym źródle (dokumentacja, definicja w kodzie, schemat bazy),
  zamiast odtwarzać z pamięci — sygnatura odtworzona z pamięci to zgadywanie,
- gdy czegoś nie da się zweryfikować w danym środowisku, powiedz to wprost
  i wskaż, co pozostało niesprawdzone. Rzetelne „nie zweryfikowano” jest
  profesjonalne; fałszywe „działa” — nie.

## 7. Profesjonalny język

Wszystkie treści trwałe — komentarze, dokumentacja, komunikaty dziennika zdarzeń,
komunikaty o błędach, komunikaty rewizji Git — pisz językiem formalnym i precyzyjnym:
- bez kolokwializmów, żartów, emotikonów i wykrzykników,
- bez zwrotów bezosobowo-potocznych („działa jak złoto”, „szybki myk”, „TODO: ogarnąć”),
- terminologia branżowa w brzmieniu przyjętym w zawodzie; skróty tylko powszechnie
  uznane (API, HTTP, SQL) — nie autorskie,
- komunikat o błędzie ma mówić czytelnikowi, co się stało i co może zrobić:
  `Nie można zapisać pliku konfiguracji: brak uprawnień do katalogu C:\ProgramData\Danaco.`

Komunikaty rewizji Git: tryb oznajmujący, jedno zdanie podsumowania, opcjonalnie
akapit uzasadnienia. Konwencję szczegółową (np. Conventional Commits) stosuj, jeżeli
projekt już ją stosuje.

## Kontrola końcowa przed przekazaniem pracy

Przed zakończeniem zadania sprawdź kolejno:

1. Czy w komentarzach nie ma historii zmian, dat, odwołań do rozmów? (zasada 1)
2. Czy nie wprowadzono wymyślonych kodów lub numeracji? (zasada 2)
3. Czy każde pojęcie nosi jedną, zawodową nazwę spójną z resztą projektu? (zasada 3)
4. Czy nie powstał żaden plik poza zbiorem kanonicznym i czy nie ma kopii `_v2`? (zasada 4)
5. Czy naprawa sięga przyczyny źródłowej, a pierwotny błąd już nie występuje? (zasada 5)
6. Czy wynik uruchomienia/testów został przytoczony, a braki weryfikacji nazwane? (zasada 6)
7. Czy wszystkie treści trwałe są napisane językiem formalnym? (zasada 7)
8. Czy środowisko pracy jest posprzątane — w katalogu przekazywanym właścicielowi
   nie ma plików roboczych, baz testowych, katalogów `__pycache__`, wyników
   pośrednich ani artefaktów uruchomień diagnostycznych? Porównaj listę plików
   sprzed rozpoczęcia pracy i po jej zakończeniu; każdą różnicę uzasadnij.

Wynik tej kontroli przedstaw właścicielowi projektu w jednym krótkim akapicie
podsumowania — bez tworzenia w tym celu jakiegokolwiek pliku.

## Karty referencyjne

Szczegółowe opracowania poszczególnych obszarów leżą w tym samym katalogu
`wspolne/standardy-zawodowe/`. Wczytuj kartę dopiero wtedy, gdy sytuacja jej wymaga —
nie wszystkie naraz.

| Karta | Wczytaj gdy |
|---|---|
| `wspolne/standardy-zawodowe/katalog-antywzorcow.md` | Piszesz lub edytujesz kod albo pliki projektu i chcesz sprawdzić, czy nie powielasz zablokowanego odruchu; przeglądasz cudzy lub własny kod pod kątem antywzorców. |
| `wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` | Kończysz zadanie i przygotowujesz pracę do przekazania — przed napisaniem raportu końcowego oraz przy kontroli końcowej z punktów 1–8. |
| `wspolne/standardy-zawodowe/jezyk-zawodowy.md` | Redagujesz treść trwałą: komunikat rewizji Git, komunikat o błędzie, wpis dziennika zdarzeń, nazwę identyfikatora, dokumentację; wahasz się między myloną parą pojęć. |
