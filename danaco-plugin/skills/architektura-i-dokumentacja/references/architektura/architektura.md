# Architektura programistyczna — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`).
Architektura w rozumieniu tej procedury to zbiór decyzji, które trudno później odwrócić: granice
modułów, model danych, sposób komunikacji, dobór technologii. Wszystko, co łatwo zmienić, nie wymaga
decyzji architektonicznej — wymaga po prostu porządnego kodu.

## Przebieg projektowania

### Etap 1 — Wymagania i ograniczenia
- Zbierz wymagania funkcjonalne jako scenariusze („system przyjmuje X i zwraca Y”),
  a niefunkcjonalne jako liczby (ilu użytkowników równocześnie, ile danych, jaki
  dopuszczalny czas odpowiedzi, jaka dostępność) — „ma być szybko” nie jest wymaganiem.
- Spisz ograniczenia zastane: istniejące systemy, zespół i jego kompetencje,
  środowisko wdrożenia (on-premise, chmura, pulpit), budżet utrzymania.
- Rozstrzygnij niejasności pytaniem do właściciela projektu przed projektowaniem.

### Etap 2 — Granice i moduły
- Podziel system według odpowiedzialności biznesowej, nie według technologii:
  moduł „faktury”, nie moduł „funkcje pomocnicze”.
- Dla każdego modułu określ: za co odpowiada, co udostępnia innym (interfejs),
  czego wymaga od innych. Zależności płyną w jedną stronę; cykl zależności
  między modułami to błąd projektu, nie szczegół implementacji.
- Zacznij od najmniejszej liczby modułów, która oddziela odpowiedzialności.
  Monolit modułowy jest właściwym punktem wyjścia dla systemów klasy Danaco;
  podział na osobne usługi wymaga uzasadnienia liczbami z etapu 1.

### Etap 3 — Dane
- Zaprojektuj model danych wcześnie: encje, relacje, właścicielstwo danych
  (który moduł jest źródłem prawdy dla której encji).
- Formaty wymiany i schematy zapisu projektuj według standardów rzeczywistych
  (ISO 8601 dla czasu, UTF-8, SemVer dla wersji interfejsów).

### Etap 4 — Dobór technologii
- Domyślnie: technologie już używane w projektach organizacji. Nowa technologia
  wymaga uzasadnienia, którego nie spełnia „jest nowsza” — to wprost ochrona
  przed dryfem technologicznym (`references/praktyki-produktowe/praktyki-produktowe.md`).
- Porównanie wariantów rób uczciwie: dla każdego wariantu zalety, wady i ryzyka
  względem wymagań z etapu 1 — nie uzasadnienie z góry wybranej opcji.

### Etap 5 — Zapis decyzji (ADR)
Każdą decyzję trudno odwracalną zapisz jako zwięzły zapis decyzji architektonicznej
w jednym kanonicznym dokumencie architektury projektu (nie w osobnych plikach-notatkach),
w układzie:

1. **Kontekst** — jaki problem i jakie ograniczenia.
2. **Rozważone warianty** — co najmniej dwa, z rzeczową oceną każdego.
3. **Decyzja** — co wybrano i dlaczego.
4. **Konsekwencje** — co decyzja ułatwia, co utrudnia, co trzeba monitorować.

## Zasady nadrzędne

- **Architektura ma odpowiadać temu, co działa.** Rozjazd między dokumentem architektury a
  rzeczywistym kodem to usterka dokumentu albo kodu — audytuj i uzgadniaj
  (`../kontrola-jakosci/references/audyt-jakosci/audyt-jakosci.md`), zamiast utrzymywać dwie prawdy.
- **Nazewnictwo architektury jest wiążące.** Nazwy modułów i pojęć przyjęte w architekturze
  obowiązują w kodzie, dokumentacji i komunikatach — zgodnie z zasadą 3 standardów zawodowych
  (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`); wprowadzenie synonimu to usterka.
- **Nie projektuj na zapas.** Warstwa abstrakcji, kolejka, mikroserwis „bo kiedyś
  się przyda” to koszt pewny przy korzyści hipotetycznej. Projektuj punkty
  rozszerzeń tam, gdzie wymagania z etapu 1 ich dowodzą.
- **Weryfikuj architekturę najtańszym eksperymentem.** Decyzję obarczoną
  niepewnością sprawdź prototypem przepływu krytycznego, zanim zwiąże projekt.

## Karty referencyjne

Karty w katalogu `references/architektura/` rozwijają procedurę do poziomu opracowania
zawodowego. Wczytuj kartę, gdy zadanie dotyka jej zakresu — nie wszystkie
naraz.

| Karta | Zakres | Kiedy wczytać |
|---|---|---|
| `references/architektura/granice-i-wzorce.md` | Rodzaje sprzężeń i heurystyki podziału, monolit modułowy i maszynowe egzekwowanie granic (import-linter, ESLint boundaries), porty i adaptery bez ceremonii, warstwa antykorupcyjna, wywołanie a zdarzenie a kolejka, kryteria wydzielenia usługi, ewolucja bez wielkiego przepisania (dusiciel, równoległe działanie, czytelnicy-najpierw) | Etap 2 procedury; każda propozycja nowej granicy, mechanizmu komunikacji lub wydzielenia usługi; planowanie przebudowy systemu zastanego |
| `references/architektura/dane-i-kontrakty.md` | Właścicielstwo danych i źródło prawdy, projektowanie i wersjonowanie kontraktów (tolerancyjny czytelnik, wygaszanie v1), granica transakcji a granica agregatu, skrzynka nadawcza i kompensacje, modelowanie czasu (fakty niezmienne, czas zdarzenia a zapisu, UTC), migracje rozszerz-przenieś-zwęź, architektura on-premise i desktopowa | Etap 3 procedury; projektowanie schematu bazy, API lub formatu wymiany; każda migracja danych; wdrożenia u klienta |
| `references/architektura/ocena-architektury.md` | Scenariusze jakościowe (bodziec, środowisko, odpowiedź mierzalna), uproszczony przegląd metodą kompromisów z tabelą roboczą, funkcje sprawności w CI, wykrywanie i naprawa erozji, rejestr ADR jako żywy dokument, dokument architektury jako kontrakt dla modeli wykonawczych | Etapy 1, 4 i 5 procedury; ocena cudzej lub własnej propozycji; przegląd okresowy; konfiguracja strażników w CI; ustalanie zakresu swobody modeli AI |
