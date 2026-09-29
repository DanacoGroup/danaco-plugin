# Audyt projektu web — karta

Karta rozszerza wymiary 2, 3 i 6 procedury audytu o metodykę właściwą projektom
webowym: Core Web Vitals, dostępność WCAG 2.2 AA, bezpieczeństwo warstwy HTTP
według OWASP Top 10:2025, techniczne SEO i higienę zasobów. Wszystkie próby opisane
niżej są bezpieczne — odczytują stan, nie modyfikują danych i nie obciążają
systemu ponad zwykły ruch. Prób inwazyjnych (skanowanie agresywne, testy
penetracyjne) audyt jakości nie obejmuje; wymagają odrębnej, pisemnej zgody
właściciela.

## 1. Wydajność — Core Web Vitals

### 1.1 Co mierzy każdy wskaźnik i progi według Google

| Wskaźnik | Co mierzy | Dobry | Wymaga poprawy | Zły |
|---|---|---|---|---|
| LCP (Largest Contentful Paint) | Czas do wyrenderowania największego elementu treści w oknie — moment, w którym strona wygląda na załadowaną | ≤ 2,5 s | 2,5–4,0 s | > 4,0 s |
| INP (Interaction to Next Paint) | Opóźnienie od interakcji użytkownika (klik, dotknięcie, klawisz) do następnego odmalowania — responsywność przez cały czas życia strony | ≤ 200 ms | 200–500 ms | > 500 ms |
| CLS (Cumulative Layout Shift) | Sumę nieoczekiwanych przesunięć układu — stabilność wizualną (wynik bezwymiarowy) | ≤ 0,1 | 0,1–0,25 | > 0,25 |

Progi ocenia się na 75. percentylu wizyt — strona jest „dobra”, gdy 75% wczytań
mieści się w progu, nie gdy mieści się średnia. INP zastąpił FID jako wskaźnik
Core Web Vitals w marcu 2024; raport odwołujący się do FID jest metodycznie
przestarzały.

### 1.2 Pomiar laboratoryjny a polowy — oba, nigdy jeden

- **Pomiar laboratoryjny (Lighthouse):** warunki kontrolowane, powtarzalny,
  dostępny dla środowisk nieprodukcyjnych. Uruchamiaj z wiersza poleceń, żeby
  wynik był odtwarzalny:

  ```
  npx lighthouse https://adres --output=json --output=html \
    --form-factor=mobile --throttling-method=simulate
  ```

  Wykonaj co najmniej 3 przebiegi i raportuj medianę — pojedynczy przebieg
  potrafi różnić się o kilkanaście punktów. Podaj w raporcie konfigurację
  (urządzenie, dławienie) — wynik bez niej jest nieporównywalny. Lighthouse nie
  mierzy INP (wymaga realnej interakcji) — posłuż się TBT (Total Blocking Time)
  jako przybliżeniem i powiedz to wprost.
- **Pomiar polowy (CrUX — Chrome UX Report):** dane rzeczywistych użytkowników
  Chrome z ostatnich 28 dni; to na nich Google ocenia stronę. Sprawdź
  w PageSpeed Insights lub przez CrUX API. Witryny o małym ruchu nie mają
  danych CrUX — odnotuj to jako ograniczenie badania, nie pomijaj milczeniem.
- **Rozbieżność między pomiarami jest ustaleniem:** dobry wynik laboratoryjny
  przy złym polowym wskazuje na warunki niereprezentowane w laboratorium
  (wolne urządzenia, dalekie sieci, stan zalogowania, personalizacja).

### 1.3 Typowe przyczyny i naprawy

- **Obrazy bez wymiarów** → CLS. Wyszukaj `<img>` bez atrybutów
  `width`/`height` ani zarezerwowanego miejsca w CSS (`aspect-ratio`).
  Naprawa: zawsze deklaruj wymiary; przeglądarki rezerwują miejsce przed
  pobraniem. To samo dotyczy reklam, osadzeń i czcionek (podmiana czcionki
  przesuwająca tekst — `font-display: optional` lub dopasowanie metryk fontu
  zapasowego).
- **Łańcuchy żądań krytycznych** → LCP. W panelu Network prześledź łańcuch
  HTML → CSS → font → obraz LCP; każde ogniwo dodaje podróż sieciową. Naprawa:
  `<link rel="preload">` dla zasobu LCP, `preconnect` dla domen trzecich na
  ścieżce krytycznej, inline krytycznego CSS, eliminacja `@import` w CSS.
- **JavaScript blokujący** → LCP i INP. Skrypty synchroniczne w `<head>` blokują
  parsowanie; długie zadania (> 50 ms) blokują odpowiedź na interakcję.
  Naprawa: `defer` dla skryptów, podział długich zadań, przeniesienie pracy
  poza wątek główny, usunięcie nieużywanego JS (pokrycie zbada panel Coverage
  w DevTools).
- **Brak nagłówków cache** → wolne kolejne wizyty. Sprawdź `Cache-Control`:
  zasoby z hashem w nazwie — `max-age=31536000, immutable`; HTML — krótki
  cache lub `no-cache` z walidacją ETag. Naprawa konfiguracyjna o niskim
  koszcie i wymiernym skutku.
- **Element LCP wczytywany leniwie** — `loading="lazy"` na obrazie hero opóźnia
  LCP o cały cykl; leniwe wczytywanie stosuj wyłącznie poniżej linii zanurzenia.

## 2. Dostępność — audyt WCAG 2.2 AA warstwami

Automat wykrywa około 30–40% naruszeń WCAG — wynik axe/Lighthouse bez badania
ręcznego nie jest audytem dostępności i nie wolno go tak nazywać w raporcie.
Badaj trzema warstwami i każdą raportuj osobno.

### Warstwa 1 — automat

Uruchom axe (axe DevTools lub `@axe-core/cli`) oraz Lighthouse (kategoria
Accessibility) na reprezentatywnym zestawie stron: główna, formularz, tabela
danych, strona z mediami. Wyniki przytocz liczbowo z podziałem na reguły.
Automat wykrywa niezawodnie: brak `alt`, kontrast tekstu statycznego, brak
etykiet pól, błędy struktury nagłówków, brak `lang`, duplikaty `id`, wadliwe
atrybuty ARIA.

### Warstwa 2 — klawiatura od początku do końca

Odłóż mysz i przejdź pełny przepływ krytyczny (np. wejście → wyszukanie →
formularz → wysłanie) wyłącznie klawiaturą:

- **Osiągalność:** każdy element interaktywny osiągalny Tabem; klikalne
  `div`/`span` bez `tabindex` i obsługi klawisza są nieosiągalne — ustalenie.
- **Widoczność fokusa:** wskaźnik widoczny na każdym elemencie; globalne
  `outline: none` bez stylu zastępczego to naruszenie WCAG 2.4.7.
- **Kolejność:** porządek Tab zgodny z wizualnym; `tabindex` > 0 to sygnał
  ostrzegawczy.
- **Pułapki fokusa:** wejdź w każde okno modalne i wyjdź (Escape, przycisk);
  fokus ma wracać do elementu wywołującego. Fokus uwięziony w widżecie
  osadzonym bez drogi wyjścia to naruszenie WCAG 2.1.2 — ustalenie poważne,
  bo blokuje resztę strony.
- **Treść ruchoma:** karuzele i autoodtwarzanie — możliwość zatrzymania
  (WCAG 2.2.2).

### Warstwa 3 — czytnik ekranu na przepływie krytycznym

Przejdź przepływ krytyczny czytnikiem ekranu (NVDA z Firefoksem na Windows,
VoiceOver z Safari na macOS — podaj w raporcie użytą parę, wyniki bywają różne).
Sprawdź: czy każdy element ogłasza nazwę, rolę i stan (przycisk „Menu,
zwinięte”, nie „grupa, pusty”); czy komunikaty dynamiczne (błędy walidacji,
potwierdzenia, wyniki wyszukiwania) są ogłaszane — wymagają `aria-live` lub
przeniesienia fokusa; czy obrazy informacyjne mają sensowny opis, a dekoracyjne
`alt=""`; czy tabele danych mają nagłówki programowe (`th`, `scope`).

### Uzupełnienia ręczne poza przepływem

- **Kontrast także stanów:** automat mierzy stan spoczynkowy; ręcznie sprawdź
  stany hover, focus, disabled tam gdzie niosą informację, teksty na obrazach
  i gradientach oraz elementy nietekstowe (ikony, obramowania pól — 3:1 według
  WCAG 1.4.11). Progi tekstu: 4,5:1 zwykły, 3:1 duży (≥ 24 px lub ≥ 18,5 px
  pogrubiony).
- **Formularze z etykietami programowymi:** każda kontrolka powiązana przez
  `label for`/`id` lub `aria-labelledby` — placeholder nie jest etykietą.
  Błędy walidacji powiązane z polem programowo (`aria-describedby`), nie tylko
  kolorem (WCAG 1.4.1).
- **Powiększenie:** strona używalna przy powiększeniu 200% i w oknie 320 px
  szerokości bez przewijania poziomego (WCAG 1.4.10).

### Warstwa 4 — dziewięć kryteriów dodanych w WCAG 2.2

WCAG 2.2 jest rekomendacją W3C od 5 października 2023 (aktualizacja 12 grudnia 2024)
i normą, względem której prowadzi się dziś audyty. Dodała dziewięć kryteriów sukcesu
i wycofała kryterium 4.1.1 Parsowanie — raport odwołujący się do 4.1.1 jako naruszenia
jest metodycznie wadliwy. Automat nie wykrywa żadnego z dziewięciu w pełni, więc każde
badaj ręcznie i raportuj osobno.

| Kryterium | Poziom | Co sprawdzić ręcznie |
|---|---|---|
| 2.4.11 Fokus niezasłonięty (minimum) | AA | Przejdź Tabem przy przyklejonym nagłówku, przyklejonej stopce i otwartym panelu ciasteczek — element z fokusem nie może być zasłonięty ani częściowo, ani całkowicie |
| 2.4.12 Fokus niezasłonięty (rozszerzony) | AAA | Jak wyżej, ale wskaźnik fokusa musi być widoczny w całości; raportuj tylko przy zadeklarowanym poziomie AAA |
| 2.4.13 Wygląd fokusa | AAA | Wskaźnik obejmuje kontur elementu, ma grubość co najmniej 2 px i kontrast 3:1 wobec stanu bez fokusa; poziom AAA |
| 2.5.7 Ruchy przeciągania | AA | Każda czynność wymagająca przeciągania (suwak, zmiana kolejności listy, mapa) ma odpowiednik na jedno wskazanie — sprawdź, czy da się ją wykonać samym kliknięciem albo klawiaturą |
| 2.5.8 Rozmiar celu (minimum) | AA | Cel dotykowy co najmniej 24×24 px albo odstęp gwarantujący brak nakładania okręgów 24 px; mierz ikony w paskach narzędzi, przyciski zamknięcia, pozycje paginacji i przełączniki w tabelach |
| 3.2.6 Spójna pomoc | A | Mechanizm pomocy (kontakt, czat, instrukcja) występuje w tej samej relacji do treści na każdej stronie, na której jest dostępny |
| 3.3.7 Powtórne wprowadzanie | A | W przepływie wieloetapowym dane raz podane są wypełniane automatycznie albo dostępne do wyboru; wyjątek dotyczy haseł i danych, których powtórzenie jest wymogiem bezpieczeństwa |
| 3.3.8 Dostępne uwierzytelnianie (minimum) | AA | Logowanie nie wymaga testu poznawczego: zapamiętania hasła bez wklejenia, rozwiązania zagadki, przepisania obrazka. Sprawdź, czy menedżer haseł może wkleić wartość i czy istnieje alternatywa dla CAPTCHA |
| 3.3.9 Dostępne uwierzytelnianie (rozszerzone) | AAA | Jak wyżej, bez wyjątku rozpoznawania obiektów; poziom AAA |

Kryteria 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7 i 3.3.8 są na poziomie A albo AA, więc wchodzą
do audytu deklarującego zgodność AA. Trzy pozostałe raportuj wyłącznie tam, gdzie
zadeklarowano poziom AAA.

Źródła: https://www.w3.org/WAI/standards-guidelines/wcag/ oraz
https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/ (stan na 2026-09-03).

W raporcie mapuj ustalenia na numery kryteriów sukcesu WCAG (np. „1.4.3
Kontrast (minimum)”) — to umożliwia weryfikację i rozmowę o zgodności. Podaj też
wersję normy, względem której prowadzono audyt: „WCAG 2.2, poziom AA”.

## 3. Bezpieczeństwo web — przegląd według OWASP Top 10:2025, próby bezpieczne

Przegląd audytowy opiera się na obserwacji odpowiedzi serwera i konfiguracji —
bez wstrzykiwania, bez zgadywania haseł, bez obciążania.

### 3.1 Nagłówki odpowiedzi — jak czytać

Pobierz nagłówki strony głównej i jednej odpowiedzi API:

```
curl -sI https://adres | sed -n '1,40p'
```

Oceń:

- **CSP (Content-Security-Policy):** brak nagłówka = brak ochrony przed
  wstrzyknięciem treści. Obecny przeczytaj krytycznie: `default-src *`,
  `script-src` z `'unsafe-inline'` lub `'unsafe-eval'` neutralizuje ochronę
  przed XSS — polityka fasadowa to ustalenie, nie zaliczenie. Stan docelowy:
  polityka nonce/hash bez `unsafe-inline`.
- **HSTS (Strict-Transport-Security):** wymagany na serwisie HTTPS; sprawdź
  `max-age` (docelowo ≥ 31536000) i czy HTTP przekierowuje na HTTPS.
- **X-Content-Type-Options: nosniff** — blokuje zgadywanie typów MIME; brak
  to ustalenie drobne, naprawa jednolinijkowa.
- **X-Frame-Options / CSP frame-ancestors** — ochrona przed clickjackingiem;
  sprawdź na stronach z akcjami (formularze, panel).
- **Nagłówki gadatliwe:** `Server`, `X-Powered-By` z numerami wersji ułatwiają
  dobór exploita — zalecenie usunięcia, waga drobna.

### 3.2 Ciasteczka

W DevTools (Application → Cookies) lub z nagłówków `Set-Cookie` sprawdź każde
ciasteczko sesyjne:

- **Secure** — bez tej flagi ciasteczko wychodzi także po HTTP; na serwisie
  HTTPS brak flagi to ustalenie istotne.
- **HttpOnly** — bez niej ciasteczko czyta JavaScript, więc każdy XSS staje się
  przejęciem sesji.
- **SameSite** — `Lax` lub `Strict` jako ochrona CSRF; `SameSite=None` wymaga
  uzasadnienia (rzeczywista integracja cross-site) i zawsze flagi Secure.
- Token sesyjny w localStorage zamiast ciasteczka HttpOnly odnotuj jako decyzję
  architektoniczną zwiększającą skutki XSS.

### 3.3 CORS — sygnatury błędnych konfiguracji

Odczytaj nagłówki odpowiedzi API na żądanie z nagłówkiem `Origin`:

```
curl -sI -H 'Origin: https://przyklad-obcy.pl' https://api.adres/zasob
```

Sygnatury błędów: `Access-Control-Allow-Origin` odbijający dowolny nadesłany
Origin łącznie z `Access-Control-Allow-Credentials: true` (obca strona może
wykonywać uwierzytelnione żądania — ustalenie poważne); `Allow-Origin: *` na
API wymagającym uwierzytelnienia; akceptowanie `Origin: null`. Samo `*` na
publicznym API bez poświadczeń jest poprawne — nie zgłaszaj go odruchowo.

### 3.4 Ujawnienia

- **Source mapy na produkcji:** sprawdź, czy obok bundli istnieją pliki `.map`
  (`curl -sI https://adres/assets/app.js.map`) lub dyrektywy
  `sourceMappingURL` na końcu bundla. Mapa ujawnia pełny kod źródłowy frontendu
  z komentarzami — ustalenie istotne w aplikacjach z logiką własnościową.
- **Katalogi z listingiem:** odpowiedź typu „Index of /” na katalogach zasobów.
- **Endpointy debug:** sprawdź obecność (samym GET, bez eksploatacji) ścieżek
  typowych dla frameworków: `/actuator` (Spring), `/__debug__` (Django),
  `/docs` i `/openapi.json` (FastAPI — publiczna dokumentacja bywa zamierzona;
  ustal z właścicielem). Wymuś 404/500 i przeczytaj treść — pełny traceback na
  produkcji to ustalenie istotne.
- **Pliki przypadkowe:** `/.env`, `/.git/HEAD`, `/backup.zip` — status 200 na
  `/.git/HEAD` oznacza możliwość pobrania całego repozytorium; ustalenie
  krytyczne, dalszych prób nie wykonuj.
- **Sekrety w bundlu:** przeszukaj pobrany bundel JS wzorcami kluczy (`AKIA`,
  `sk_live_`, `AIza`); klucz w kodzie frontendu jest publiczny z definicji.

### 3.5 Dwie kategorie dodane w edycji 2025

Edycja OWASP Top 10:2025 wprowadziła dwie kategorie, których nie obejmują próby
z punktów 3.1–3.4. Audyt pomijający je wygląda na kompletny, a nie jest.

**A03:2025 Software Supply Chain Failures** — ryzyko wnoszone przez zależności, obrazy
bazowe, wtyczki i potok budowy. Próby audytowe:

- wykaz zależności z wersjami i znanymi podatnościami (`npm audit --omit=dev`,
  `pip-audit`, `osv-scanner`) — raportuj liczby, nie wrażenie;
- obecność wykazu składników (SBOM w formacie CycloneDX albo SPDX) i tego, czy powstaje
  automatycznie w potoku budowy, czy został wygenerowany raz do audytu;
- przypięcie wersji: plik blokady w repozytorium, obrazy bazowe wskazane sumą skrótu,
  a nie ruchomym znacznikiem `latest`;
- zależności zewnętrzne wciągane z sieci w czasie budowy (skrypt `curl | sh`,
  biblioteka z CDN bez `integrity`) — każda to punkt wejścia;
- uprawnienia potoku: czy budowa ma dostęp do sekretów wydania, czy krok podpisania
  jest oddzielony od kroku budowy.

**A10:2025 Mishandling of Exceptional Conditions** — obsługa warunków wyjątkowych:
błąd wyciszony, błąd ujawniający wnętrze systemu, awaria kończąca się stanem otwartym.
Próby audytowe:

- wymuś błąd (żądanie do nieistniejącego zasobu, wadliwy dokument JSON, przekroczenie
  limitu długości) i przeczytaj odpowiedź: ślad stosu, nazwa biblioteki, ścieżka pliku
  i fragment zapytania SQL w treści to ustalenie istotne;
- sprawdź, czy niepowodzenie kontroli kończy się odmową, a nie przejściem dalej —
  zwłaszcza w uwierzytelnianiu i w kontroli uprawnień;
- sprawdź, czy odpowiedź po błędzie jest jednolita (jeden format błędu, jeden kod), bo
  różnice ujawniają istnienie zasobów;
- w kodzie: puste `try/except`, `catch` bez obsługi i logowanie wyjątku jako jedyna
  reakcja — pozycja A7 katalogu w `../../wspolne/standardy-zawodowe/katalog-antywzorcow.md`.

Źródło: https://owasp.org/Top10/2025/ (stan na 2026-09-03). Kategorie edycji 2025:
A01 Broken Access Control, A02 Security Misconfiguration, A03 Software Supply Chain
Failures, A04 Cryptographic Failures, A05 Injection, A06 Insecure Design,
A07 Authentication Failures, A08 Software or Data Integrity Failures, A09 Security
Logging and Alerting Failures, A10 Mishandling of Exceptional Conditions.

## 4. SEO techniczne jako element audytu

Audyt stwierdza wyłącznie fakty sprawdzalne technicznie — nie prognozuje pozycji
w wynikach ani ruchu; takie prognozy leżą poza kompetencją audytu jakości.

- **Indeksowalność:** pobierz `robots.txt` — czy nie blokuje zasobów
  renderowania (CSS, JS) ani całych sekcji przez pomyłkę (`Disallow: /`
  pozostawione po wdrożeniu z testów to ustalenie krytyczne dla celu witryny).
  Sprawdź metatag `robots`/`noindex` i nagłówek `X-Robots-Tag` na stronach
  do indeksowania. Zweryfikuj `sitemap.xml` (status 200, adresy kanoniczne,
  bez 404/301).
- **Canonical:** każda strona indeksowalna z jednym `link rel="canonical"`
  wskazującym samą siebie w wariancie docelowym; warianty http/https i z/bez
  `www` mają przekierowywać 301 na kanoniczny. Canonical wskazujący stronę
  nieistniejącą lub sprzeczny między nagłówkiem HTTP a HTML to ustalenie.
- **Dane strukturalne:** zweryfikuj walidatorem (Schema Markup Validator, test
  wyników rozszerzonych Google) — raportuj błędy składni i pól wymaganych jako
  fakt walidacji; nie obiecuj elementów rozszerzonych w wynikach.
- **Podstawy na stronę:** unikalny `title` i `meta description`, jeden `h1`,
  poprawny `hreflang` przy wersjach językowych (błędny `hreflang` jest gorszy
  niż brak — pary muszą być wzajemne).
- **Odpowiedzi serwera:** próbką adresów sprawdź łańcuchy przekierowań
  (`curl -sIL adres` — zgłoś więcej niż jedno w łańcuchu) i miękkie 404
  (strona „nie znaleziono” ze statusem 200).

## 5. Higiena zasobów

- **Wagi bundli z progami orientacyjnymi:** zmierz rozmiar transferowany
  (po kompresji) JS i CSS ścieżki krytycznej (panel Network). Progi orientacyjne
  dla strony publicznej na urządzenia mobilne: JS ścieżki krytycznej > 300 KB
  po kompresji — odnotuj, > 1 MB — ustalenie do przeglądu składu; całkowita
  waga pierwszego wczytania > 3 MB — ustalenie. Aplikacja wewnętrzna za
  logowaniem ma inny budżet niż strona kampanii — przyjęte założenie podaj
  w raporcie.
- **Skład bundla:** zbadaj `npx source-map-explorer` lub
  `npx webpack-bundle-analyzer`: duplikaty bibliotek (dwie wersje tej samej
  zależności), całe biblioteki wciągnięte dla jednej funkcji, brak podziału
  kodu na trasy w aplikacjach wielostronicowych.
- **Obrazy w formatach współczesnych:** WebP/AVIF z fallbackiem (`<picture>`)
  lub negocjacją po `Accept`; obrazy serwowane w rozmiarze wielokrotnie
  większym niż wyświetlany (porównaj wymiary naturalne z wyświetlanymi
  w DevTools); brak `srcset` na stronach responsywnych. PNG użyty do fotografii
  odnotuj z wyliczeniem oszczędności na próbce.
- **Kompresja transferu:** odpowiedzi tekstowe z `Content-Encoding: br` lub
  `gzip`; brak kompresji na dużych zasobach tekstowych to ustalenie o naprawie
  konfiguracyjnej, natychmiastowym skutku i zerowym ryzyku.
- **Czcionki:** format WOFF2, `font-display` ustawione świadomie, subsetting
  przy dużych zestawach znaków; policz ładowane kroje i odmiany — każda odmiana
  to osobny plik.

## Minimalny komplet dowodów z tej karty

Do raportu audytu projektu web dołącz co najmniej: wyniki Lighthouse (mediana
z ≥ 3 przebiegów, z konfiguracją) i dane CrUX albo odnotowany ich brak; tabelę
Core Web Vitals z progami; wynik automatu dostępności plus protokoły przejścia
klawiaturą i czytnikiem ekranu z mapowaniem na kryteria WCAG; tabelę nagłówków
bezpieczeństwa i flag ciasteczek; wynik prób ujawnień; stan indeksowalności
i canonical; wagi bundli ścieżki krytycznej. Każdy pomiar z datą, adresem
i poleceniem — stan witryny zmienia się z każdym wdrożeniem, dowód bez daty
traci wartość.
