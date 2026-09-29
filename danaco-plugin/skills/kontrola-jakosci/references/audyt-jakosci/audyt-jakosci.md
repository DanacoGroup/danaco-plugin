# Audyt jakości — procedura

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Audyt różni
się od przeglądu kodu zakresem: przegląd ocenia zmianę, audyt ocenia całość — kod, strukturę
projektu, proces budowy i zgodność ze standardami. Wynikiem audytu jest raport z ustaleniami
uporządkowanymi według wagi, z dowodami i planem naprawy.

## Przebieg audytu

### Etap 1 — Inwentaryzacja
- Ustal z właścicielem zakres i cel audytu (całość czy wskazane obszary; decyzja
  o wdrożeniu, przejęcie projektu, kontrola okresowa).
- Zbadaj stan faktyczny: drzewo katalogów, języki i frameworki (z plików projektu,
  nie z deklaracji), zależności i ich wersje, obecność testów, dokumentację, historię Git.
- Uruchom projekt i testy — audyt projektu, którego nie próbowano uruchomić,
  jest niekompletny; niepowodzenie uruchomienia to pierwsze ustalenie audytu.

### Etap 2 — Analiza narzędziowa
Uruchom narzędzia przyjęte zawodowo dla danego ekosystemu (wskazuje je karta języka
w `jezyki-programowania`): linter, analiza statyczna, audyt zależności
(`npm audit`, `pip-audit`), pomiar pokrycia testami. Wyniki przytaczaj liczbowo.

### Etap 3 — Badanie próbek
Nie czytaj wszystkiego — dobierz próbki celowane: moduły największe, najczęściej
zmieniane (`git log --stat`), krytyczne dla bezpieczeństwa (uwierzytelnianie,
płatności, dostęp do danych) oraz 2–3 losowe dla kalibracji. Każdą próbkę oceń
według wymiarów z etapu 4.

### Etap 4 — Wymiary oceny
1. **Poprawność i niezawodność** — obsługa błędów na stykach z zewnętrzem,
   przypadki brzegowe, spójność transakcyjna.
2. **Bezpieczeństwo** — według kategorii OWASP Top 10:2025 dla aplikacji web
   (w tym A03 Software Supply Chain Failures i A10 Mishandling of Exceptional
   Conditions, dodane w tej edycji); sekrety w repozytorium; walidacja na granicach
   systemu.
3. **Wydajność** — zapytania N+1, brak indeksów, operacje blokujące; w projektach
   web dodatkowo wskaźniki Core Web Vitals (LCP, INP, CLS) mierzone narzędziem
   (np. Lighthouse), nie szacowane.
4. **Struktura i praktyki produktowe** — zgodność drzewa katalogów z konwencją ekosystemu, podział
   odpowiedzialności, dryf technologiczny (szczegółowe kryteria:
   `../architektura-i-dokumentacja/references/praktyki-produktowe/praktyki-produktowe.md`).
5. **Zgodność ze standardami zawodowymi** — kontrola końcowa z
   `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` zastosowana do całości: historia w
   komentarzach, wymyślone kody, pliki-narośle, kopie `_v2`, martwy kod, język nieprofesjonalny.
6. **Dostępność (projekty web)** — zgodność z WCAG 2.2 AA w zakresie badanym
   narzędziowo (kontrast, atrybuty alternatywne, nawigacja klawiaturą) plus próba ręczna.
7. **Testy i dokumentacja** — czy istnieją, czy przechodzą, czy odpowiadają stanowi
   faktycznemu projektu.

## Zasady dowodowe

Każde ustalenie audytu ma trzy elementy: miejsce (plik, moduł, adres), dowód
(wynik narzędzia, fragment kodu, wynik uruchomienia) i skutek praktyczny.
Ustalenie bez dowodu oznacz jako przypuszczenie. Nie zgłaszaj naruszeń stylu
tam, gdzie projekt konsekwentnie stosuje własną, spójną konwencję.

## Raport z audytu

Raport przekaż w rozmowie; jako plik — wyłącznie na wyraźne życzenie właściciela
projektu, w jednym uzgodnionym dokumencie. Układ raportu:

1. **Streszczenie** — stan ogólny w 3–5 zdaniach, najpoważniejsze ryzyko, ocena
   zdatności do celu audytu.
2. **Ustalenia** — od najpoważniejszych, każde z miejscem, dowodem i skutkiem;
   podział: krytyczne / istotne / drobne.
3. **Plan naprawy** — kolejność usuwania ustaleń wynikająca z ryzyka i zależności
   między poprawkami; przy każdej pozycji przybliżony nakład (mały/średni/duży).
4. **Czego nie zbadano** — obszary poza zakresem lub niedostępne, wymienione wprost.

Nie zaokrąglaj oceny w górę dla uprzejmości: audyt, który przemilcza problem,
jest gorszy niż brak audytu.

## Karty referencyjne

Wczytuj kartę, gdy audyt wchodzi w jej obszar — karty zawierają polecenia,
progi i metodykę szczegółową, których nie powiela ta procedura.

| Karta | Plik | Kiedy wczytać |
|---|---|---|
| Audyt repozytorium | `references/audyt-jakosci/audyt-repozytorium.md` | Etapy 1–3 każdego audytu kodu: analiza historii Git (churn, hotspoty, bus factor, poprawki wielokrotne), zależności i licencje, kod martwy, metryki złożoności z progami, pliki-narośle, ocena testów ponad pokrycie, próba README na czysto. |
| Audyt projektu web | `references/audyt-jakosci/audyt-web.md` | Wymiary 2, 3 i 6 dla projektów web: Core Web Vitals z progami i metodyką pomiaru, dostępność WCAG 2.2 AA warstwami (automat + klawiatura + czytnik ekranu), bezpieczeństwo HTTP według OWASP Top 10:2025 próbami bezpiecznymi, SEO techniczne, higiena zasobów. |
| Raportowanie audytu | `references/audyt-jakosci/raportowanie-audytu.md` | Przy pisaniu każdego raportu: kalibracja wag (macierz, kryteria twarde „krytycznego”), metoda fakt–dowód–skutek–naprawa z parami źle/dobrze, plan naprawy jako harmonogram zależności, streszczenie dla decydenta, rozmowa z zespołem, audyt powtórny, granice odpowiedzialności audytora. |
