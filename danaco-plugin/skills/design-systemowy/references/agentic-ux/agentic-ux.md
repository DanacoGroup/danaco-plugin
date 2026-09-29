# Agentic UX — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`);
dokumentację powstałą w tej pracy prowadź według
`references/dokumentacja-designu/dokumentacja-designu.md`. Procedura stosuje się do projektowania
doświadczenia, nie implementacji — implementację prowadzi paczka `../ui-ux-pro/SKILL.md` dla klienta
Danaco Console albo `../kodowanie/SKILL.md` dla pozostałego kodu.

Zmiana paradygmatu: UX tradycyjny optymalizuje pojedyncze ekrany i odosobnione
interakcje; UX agentowy projektuje relację, w której system z każdą sesją
rozumie użytkownika lepiej. Jednostką projektowania jest relacja w czasie,
nie ekran.

## Pięć filarów projektu relacyjnego

### 1. Pamięć jako inteligencja kontekstowa
Nie projektuj pamięci jako statycznych ustawień (motyw, język), lecz jako
ewoluujący model relacji: wzorce zachowań, kontekst sytuacyjny (pośpiech,
eksploracja, decyzja), zmiany preferencji w czasie, ciągłość między sesjami
i urządzeniami. Pytanie kontrolne projektu: jak wyglądałoby to doświadczenie,
gdyby system pamiętał wszystko i z każdym użyciem był lepszy?

### 2. Zaufanie jako materiał projektowy
Autonomię systemu stopniuje się, a nie zakłada. Trzy stadia, projektowane jawnie:
- **przejrzystość** — system pokazuje rozumowanie, pewność i podstawy propozycji;
- **asysta nadzorowana** — system proponuje i wykonuje za potwierdzeniem;
- **autonomia zarobiona** — system działa sam w zakresie, w którym się sprawdził,
  z możliwością wglądu i cofnięcia.
Projekt określa, co przenosi system między stadiami (liczba udanych działań,
jawna zgoda) oraz ścieżkę odbudowy zaufania po błędzie — degradację do stadium
niższego z wyjaśnieniem, nigdy udawanie, że błędu nie było.

### 3. Architektura zorientowana na relację
Struktura informacji porządkuje się wokół wspólnej historii i celów użytkownika
z systemem, nie wokół mapy funkcji. Stan relacji (co system wie, czego się
nauczył, do czego ma uprawnienia) jest dla użytkownika widoczny i edytowalny —
z prawem wglądu, poprawienia i wymazania pamięci włącznie; prywatność jest
elementem projektu relacji, nie regulaminem obok.

### 4. Wspólne planowanie
Człowiek i system współtworzą plan działania: system proponuje ścieżkę, pokazuje
założenia i punkty decyzyjne, użytkownik koryguje zakres i priorytety przed
wykonaniem. Projektuj artefakt planu (edytowalna lista kroków ze statusem),
nie dialog, który znika.

### 5. Miary relacji zamiast miar konwersji
Sukces mierzy się jakością relacji: głębokość kontynuacji między sesjami,
odsetek propozycji przyjętych bez poprawek, tempo przechodzenia do wyższych
stadiów zaufania, utrzymanie w czasie — zamiast klikalności pojedynczych ekranów.
Miary zdefiniuj przy projekcie, nie po wdrożeniu.

## Przebieg pracy projektowej

1. **Kontekst relacji** — kto wraca, po co, w jakich odstępach; co system powinien
   pamiętać, a czego pamiętać mu nie wolno.
2. **Mapa zaufania** — działania systemu rozpisane na trzy stadia z warunkami
   przejść i ścieżką odbudowy.
3. **Architektura pamięci** — co jest zapisywane, gdzie jest widoczne dla
   użytkownika, jak się poprawia i wymazuje.
4. **Wzorce współpracy** — plan wspólny, propozycje z uzasadnieniem, potwierdzenia
   działań nieodwracalnych.
5. **Miary** — wskaźniki relacyjne z wartościami docelowymi.

Wynik dokumentuj w opracowaniu UX projektu (karta
`references/dokumentacja-designu/opracowania-ui-ux.md` w
`references/dokumentacja-designu/dokumentacja-designu.md`) — jednym, kanonicznym.

## Kiedy tego podejścia nie stosować

Transakcje jednorazowe bez konta, treści statyczne bez personalizacji, systemy,
w których pamięć tworzy ryzyko prywatności przewyższające korzyść, oraz
interfejsy wymagające niezmienności zachowania (np. urządzenia krytyczne) —
tam spójność jest ważniejsza niż adaptacja i klasyczny UX pozostaje właściwy.

## Typowe błędy projektowe

Pamięć sprowadzona do ustawień; zaufanie zero-jedynkowe (wszystko albo nic);
miary klikalności do oceny relacji; brak kontroli użytkownika nad pamięcią;
projektowanie ekranów zamiast relacji; brak ścieżki odbudowy zaufania po błędzie
systemu.

## Karty referencyjne

Karty wczytuj z katalogu `references/agentic-ux/` w momencie, gdy praca wchodzi w ich
zakres — nie wszystkie naraz.

| Karta | Zakres | Kiedy wczytać |
|---|---|---|
| `references/agentic-ux/biblioteka-wzorcow.md` | Dziewięć wzorców interfejsów agentowych — od panelu pamięci i propozycji z uzasadnieniem po odbudowę po błędzie i granice proaktywności — każdy z anatomią, stanami i błędami projektowymi | Przy projektowaniu konkretnych komponentów i przepływów (kroki 3–4 przebiegu pracy) |
| `references/agentic-ux/pamiec-i-prywatnosc.md` | Taksonomia pamięci, reguły zapisu i stosowania, zapominanie, przejrzystość źródła, pamięć jako dane niewykonywalne, wiele urządzeń, privacy by design | Przy architekturze pamięci (krok 3) oraz zawsze, gdy projekt dotyka danych osobowych lub kategorii wrażliwych |
| `references/agentic-ux/miary-i-badania.md` | Definicje operacyjne miar relacji, instrumentacja wzorców, badania jakościowe (wywiad o zaufaniu, test dziennikowy, pierwsza delegacja nieodwracalna), pułapki miar, progi alarmowe i przeglądy | Przy definiowaniu miar (krok 5) oraz przy planowaniu badań i przeglądów okresowych |
