# Architektura systemu — przegląd modułu

Moduł obejmuje projektowanie systemu przed napisaniem kodu: ograniczenia, granice modułów,
wybór technologii, zapis decyzji, model danych, projekt API i dług techniczny. Karty
pogłębione wymienia tabela poniżej. Poza modułem: procedura architektoniczna paczki
w `references/architektura/architektura.md` oraz dokumentacja techniczna
w `references/dokumentacja-techniczna/dokumentacja-techniczna.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Domyślne zachowanie modelu przy zadaniu „zbuduj X” to natychmiastowe pisanie plików.
Powstaje kod, który działa na happy path i którego po tygodniu nie da się zmienić, bo
warstwa HTTP zna schemat bazy, a logika biznesowa importuje SDK dostawcy płatności.

Ten moduł wymusza kolejność: **ograniczenia → granice → interfejsy → implementacja**.
Każdy krok wstecz w tej kolejności kosztuje więcej niż krok naprzód.

## Kiedy wczytać ten moduł

- Zadanie brzmi „zbuduj aplikację / usługę / system do X” i nie istnieje jeszcze kod.
- Trzeba rozstrzygnąć wybór: baza, kolejka, framework, monolit vs usługi, sposób auth.
- Wchodzisz w istniejące repozytorium i masz dodać funkcję, nie łamiąc tego, co jest.
- Trzeba zaprojektować schemat danych albo kontrakt API przed implementacją.
- Przegląd kodu, audyt jakości, wycena i uporządkowanie długu, plan refaktoryzacji.
- Ktoś proponuje przepisanie systemu od zera.

**Nie używaj gdy:** pytanie dotyczy konkretnego API biblioteki, składni, albo „dlaczego
ten test nie przechodzi”. To nie jest architektura, to implementacja lub debugowanie.

## Granice

| Temat | Materiał właściwy |
| --- | --- |
| Konkretne API Next.js i TypeScriptu, warstwa stylu | `../kodowanie/references/frameworki/nextjs.md` · `../kodowanie/references/jezyki-programowania/javascript-typescript.md` · `../ui-ux-pro/SKILL.md` (API React 19 i Prisma nie są w tym pluginie opisane) |
| Python, FastAPI, pandas, ETL, SQLAlchemy, warstwa danych w Pythonie | `../kodowanie/references/engineering-core/02-python-backend-dane/przeglad.md` |
| Debugowanie, testy, CI/CD, wdrożenia, obserwowalność | `../kodowanie/references/engineering-core/07-debug-testy-deploy/przeglad.md` |
| Bazy wektorowe, embeddingi, RAG, wyszukiwanie semantyczne | `../kodowanie/references/engineering-core/04-bazy-i-rag/przeglad.md` |

Podział jest prosty: tutaj **decydujesz i zapisujesz decyzję**, tam **wykonujesz**.
„Jakiej bazy użyć i dlaczego” — tutaj. „Jak napisać migrację w Prisma 7” — tam.
„Jak zaprojektować kontrakt API” — tutaj. „Jak obsłużyć błąd w route handlerze” — tam.

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
| --- | --- | --- |
| `references/engineering-core/references/dekompozycja.md` | Od problemu do modułów: domeny, granice transakcyjne, rdzeń vs peryferia, monolit modularny vs usługi, osie zmian, skalowanie jako decyzja odroczona | Zaczynasz nowy system albo dzielisz istniejący |
| `references/engineering-core/references/granice-i-warstwy.md` | Warstwy, zależności do środka, porty i adaptery, co nie może przeciekać, struktury katalogów TS i Python, wykrywanie naruszeń | Ustalasz strukturę repozytorium albo widzisz przeciek warstw |
| `references/engineering-core/references/wybor-technologii.md` | Ramy oceny (zespół, dojrzałość, koszt wyjścia, licencja, ekosystem), nudna technologia jako domyślna, katalog kosztownych błędnych wyborów | Wybierasz bazę, framework, kolejkę, hosting, bibliotekę |
| `references/engineering-core/references/adr.md` | Szablon ADR, kiedy pisać, jak formułować alternatywy i konsekwencje, 5 pełnych przykładów, rewizja decyzji | Podjąłeś nieodwracalną decyzję i trzeba ją zapisać |
| `references/engineering-core/references/modelowanie-danych.md` | Model domenowy vs schemat, normalizacja, klucze, migracje bez przestoju, usuwanie miękkie, audyt, czas, pieniądze, identyfikatory | Projektujesz schemat, zmieniasz schemat, planujesz migrację |
| `references/engineering-core/references/projektowanie-api.md` | REST/RPC/GraphQL, wersjonowanie, paginacja, filtrowanie, błędy RFC 9457, idempotencja, limity, authn/authz, OpenAPI, zdarzenia i webhooki | Projektujesz kontrakt między systemami |
| `references/engineering-core/references/przeglad-kodu.md` | Kolejność ważności, katalog realnych usterek z przykładami, jak formułować uwagi, co nie jest przedmiotem przeglądu | Recenzujesz diff, PR albo cudzy moduł |
| `references/engineering-core/references/dlug-techniczny.md` | Klasyfikacja, pomiar, priorytetyzacja, refaktoryzacja krok po kroku, wzorzec duszącego figowca, kiedy przepisać od zera | Kod spowalnia zespół, ktoś proponuje przepisanie |

Wczytuj **jeden do dwóch** plików na zadanie. Wczytanie wszystkich ośmiu oznacza,
że nie zrozumiałeś zadania.

## Procedura: od wymagania do architektury

Nie pomijaj kroków 1–3, nawet gdy zadanie wygląda na trywialne. Zajmują łącznie kilka
minut, a ich pominięcie kosztuje dni.

### 1. Ustal, co system ma robić — w zdaniach, nie w technologiach

Zapisz maksymalnie pięć zdań w formie „aktor robi X, żeby Y”. Jeśli nie potrafisz ich
napisać, nie masz wymagań, masz życzenie. Zadaj pytania, zamiast zgadywać.

Wymagane odpowiedzi przed jakąkolwiek decyzją techniczną:

| Pytanie | Dlaczego przesądza |
| --- | --- |
| Kto jest użytkownikiem i ilu ich jest? | 50 użytkowników wewnętrznych to inny system niż 50 000 anonimowych |
| Jaka jest **rzeczywista** skala? (rps, GB, liczba rekordów) | Skala projektowana to fantazja; skala rzeczywista to ograniczenie |
| Kto to utrzymuje po wdrożeniu i ilu ich jest? | Jednoosobowy zespół nie utrzyma sześciu usług |
| Co jest nieodwracalne? (dane osobowe, pieniądze, integracje zewnętrzne) | Tam kładziesz największą staranność |
| Jaki jest termin i co się stanie po jego przekroczeniu? | Rozstrzyga wybór między „poprawnie” a „szybko” |
| Jakie są wymagania prawne? (RODO, retencja, KSeF, archiwizacja) | Nie da się ich dokleić po fakcie |

Gdy użytkownik nie zna odpowiedzi na pytanie o skalę — przyjmij najniższą sensowną
i **zapisz to jako założenie**. Nie projektuj pod skalę, której nikt nie potwierdził.

### 2. Wypisz ograniczenia, zanim wypiszesz rozwiązania

Ograniczenie to coś, czego nie wolno albo nie da się zmienić: istniejąca baza, znany
zespołowi język, budżet hostingu, wymóg działania offline, umowa SLA, integracja z
systemem, którego nie kontrolujesz. Ograniczenia zawężają przestrzeń rozwiązań szybciej
niż jakikolwiek argument techniczny.

Rozróżnij twarde od miękkich. „Musimy hostować w UE” jest twarde. „Zespół woli Vue”
jest miękkie, ale ma realny koszt. Zapisz oba, oznacz które jest które.

### 3. Nazwij domeny i narysuj granice

Rozbij problem na 3–7 obszarów odpowiedzialności o odrębnym słowniku. Dla każdego
zapisz: co należy do środka, czego nie wolno wpuścić, jak inne obszary go używają.
Szczegóły — `references/engineering-core/references/dekompozycja.md`.

Test poprawności granicy: **czy zmiana reguły biznesowej wewnątrz obszaru wymaga
dotknięcia plików w innym obszarze?** Jeśli tak, granica jest w złym miejscu.

Domyślnie: **monolit modularny**, jedno wdrożenie, moduły jako katalogi z jawnym
interfejsem publicznym. Podział na usługi wymaga uzasadnienia zapisanego w ADR.

### 4. Zdecyduj o technologiach i zapisz uzasadnienie

Dla każdej decyzji nieodwracalnej albo kosztownej w odwróceniu napisz ADR
(`references/engineering-core/references/adr.md`). Kryteria wyboru —
`references/engineering-core/references/wybor-technologii.md`.

Nieodwracalne albo kosztowne: baza danych, model uwierzytelniania, granice usług,
format identyfikatorów, dostawca chmury, język. Odwracalne tanio: biblioteka do
walidacji, formatter, biblioteka UI, narzędzie testowe. Nad odwracalnymi nie debatuj.

### 5. Zaprojektuj dane przed kodem

Schemat przetrwa trzy przepisania warstwy aplikacyjnej. Model danych ustala, co da się
policzyć, czego nie da się cofnąć i ile będzie kosztować migracja.
Reguły — `references/engineering-core/references/modelowanie-danych.md`.

Minimum przed pierwszą linią kodu: encje, klucze, relacje, co jest niemutowalne,
gdzie jest czas i w jakiej strefie, gdzie są pieniądze i w jakim typie.

### 6. Zaprojektuj kontrakty, zanim napiszesz implementację

Kontrakt to publiczne API modułu, endpoint HTTP, schemat zdarzenia albo sygnatura
portu. Napisz go jako typy/OpenAPI/schemat — nie jako opis prozą.
Reguły — `references/engineering-core/references/projektowanie-api.md`.

Kontrakt pisany po implementacji zawsze odzwierciedla implementację, a nie potrzebę
konsumenta. To jest przyczyna większości nieprzyjemnych API.

### 7. Dopiero teraz kod

Kolejność wewnątrz kroku: model domenowy (czyste funkcje i typy, zero I/O) → przypadki
użycia (orkiestracja) → adaptery (baza, HTTP, kolejka) → prezentacja.
Jeśli zaczynasz od kontrolera, kończysz z logiką w kontrolerze.

### 8. Zapisz to, czego nie widać w kodzie

Do repozytorium: `docs/adr/NNNN-*.md` z decyzjami, `docs/architektura.md` z mapą modułów
i przepływem danych (10–40 linii, nie 10 stron), `README.md` z uruchomieniem.
Cała reszta niech mieszka w kodzie i testach.

## Procedura: wejście w cudzy kod

Gdy repozytorium już istnieje, zmienia się wszystko poza zasadą kolejności.

1. **Nie czytaj wszystkiego.** Przeczytaj: `README`, pliki konfiguracji zależności,
   schemat bazy/migracje, drzewo katalogów na 2 poziomy, punkt wejścia aplikacji.
   To daje 80% obrazu w 10 minut.
2. **Zrekonstruuj mapę modułów** i narysuj ją w odpowiedzi, zanim cokolwiek zmienisz.
   Jeśli nie umiesz jej narysować, nie wiesz, co zepsujesz.
3. **Znajdź konwencje panujące w repozytorium** — nazewnictwo, obsługa błędów, sposób
   dostępu do bazy, sposób walidacji. Nowy kod ma wyglądać jak stary kod, nawet gdy
   stary kod jest gorszy od twojego domyślnego stylu. Spójność bije lokalną jakość.
4. **Ustal, czy twoja zmiana mieści się w istniejącej granicy.** Jeśli tak — wpisz się
   w nią. Jeśli nie — zapytaj, zanim zaczniesz przesuwać granice.
5. **Zmieniaj minimalnie.** Zmiana funkcjonalna i refaktoryzacja to dwa osobne commity.
   Zmieszane, są nierecenzowalne i nie da się ich cofnąć osobno.
6. **Sprawdź, co się zepsuje.** Wyszukaj wszystkie użycia funkcji, którą zmieniasz.
   Sprawdź testy, które ją pokrywają. Brak testów jest informacją, nie zaproszeniem.

## Szkic domyślny — z czego zaczynasz, gdy nic nie przeczy

```
                   ┌──────────────────────────────────────────┐
   we/wy           │  prezentacja: HTTP, CLI, cron, kolejka    │
   (adaptery       │  parsuje wejście, formatuje wyjście       │
    napędzające)   └───────────────────┬──────────────────────┘
                                       │ wywołuje
                   ┌───────────────────▼──────────────────────┐
                   │  aplikacja: przypadki użycia             │
                   │  orkiestracja, transakcja, autoryzacja   │
                   └───────────────────┬──────────────────────┘
                          używa portów │  (interfejsy zdefiniowane TU)
                   ┌───────────────────▼──────────────────────┐
                   │  domena: encje, reguły, niezmienniki     │
                   │  zero I/O, zero frameworka, zero SDK     │
                   └──────────────────────────────────────────┘
                                       ▲ implementuje porty
   (adaptery       ┌───────────────────┴──────────────────────┐
    napędzane)     │  infrastruktura: baza, HTTP, S3, SMTP    │
                   └──────────────────────────────────────────┘
```

Strzałki zależności wskazują do środka. Warstwa infrastruktury zależy od domeny, nigdy odwrotnie. To
jedyna reguła strukturalna, której nie wolno naginać —
`references/engineering-core/references/granice-i-warstwy.md` opisuje, jak ją utrzymać w TypeScript
i w Pythonie.

Domyślny zestaw dla nowego projektu wewnętrznego, dopóki wymagania nie przeczą:

| Warstwa | Domyślny wybór | Zmieniasz, gdy |
| --- | --- | --- |
| Wdrożenie | Jeden proces, jeden artefakt | Zespoły muszą wdrażać niezależnie |
| Baza | PostgreSQL 18 | Dane naprawdę nierelacyjne albo skala poza jedną maszyną |
| Kolejka | Tabela w Postgresie + `SELECT ... FOR UPDATE SKIP LOCKED` | >1000 zdarzeń/s albo wielu konsumentów o różnym tempie |
| Cache | Brak | Zmierzone zapytanie >200 ms po dodaniu indeksu |
| Wyszukiwanie | `tsvector` w Postgresie | Wymagane rankowanie semantyczne → `../kodowanie/references/engineering-core/04-bazy-i-rag/przeglad.md` |
| Pliki | S3-kompatybilne, referencja w bazie | Nigdy blob w bazie powyżej kilkuset kB |
| Identyfikatory | UUIDv7 (`uuidv7()` w PG 18) | Klucz musi być krótki i czytelny dla człowieka |
| Auth | Gotowy dostawca (OIDC) albo sesja w cookie HttpOnly | Nigdy własna kryptografia haseł |
| Konfiguracja | Zmienne środowiskowe walidowane przy starcie | — |

Każde odstępstwo od tej tabeli wymaga zdania uzasadnienia. Trzy odstępstwa wymagają ADR.

## Szybkie rozstrzygnięcia

Odpowiedzi na pytania, przy których model najczęściej odpowiada „to zależy” i zostawia
użytkownika bez decyzji. Podawaj rekomendację **plus warunek jej odwrócenia**.

| Pytanie | Domyślna odpowiedź | Odwraca ją |
| --- | --- | --- |
| Monolit czy mikrousługi? | Monolit modularny | >2 zespoły wdrażające niezależnie, albo jeden komponent skaluje się o rząd wielkości inaczej |
| REST czy GraphQL? | REST + OpenAPI | Wielu różnych konsumentów o rozbieżnych potrzebach danych i jeden zespół utrzymuje graf |
| ORM czy surowy SQL? | ORM do CRUD, SQL do raportów i agregacji | Zapytanie, którego ORM nie wyraża czytelnie — pisz SQL i otestuj |
| Jedna baza czy baza na moduł? | Jedna baza, schematy per moduł | Rozdzielenie usług (a wtedy i tak masz problem transakcji) |
| Zdarzenia czy wywołanie synchroniczne? | Synchronicznie | Odbiorca nie musi odpowiedzieć teraz, a nadawca nie potrzebuje wyniku |
| Sesja czy JWT? | Sesja po stronie serwera (cookie HttpOnly, SameSite=Lax) | Klienci bez cookies albo prawdziwie bezstanowe usługi — i akceptujesz brak natychmiastowego unieważnienia |
| Miękkie usuwanie czy twarde? | Twarde + tabela audytu | Wymóg prawny odtworzenia stanu albo funkcja „kosz” |
| Warstwa repozytoriów w małej aplikacji? | Tak, ale cienka: jeden moduł na agregat | Prototyp jednorazowy |
| Monorepo czy wiele repo? | Monorepo | Osobne cykle wydawnicze i osobni właściciele |
| TypeScript czy Python na backend? | Ten, który zespół zna lepiej | Domena to dane/ML (Python) albo współdzielone typy z frontem (TS) |

## Przykład przejścia procedury

Zadanie użytkownika: „zbuduj system do obsługi zgłoszeń serwisowych dla naszych klientów”.

**Krok 1–2 (wymagania i ograniczenia).** Pytania zadane, odpowiedzi: 40 klientów B2B,
~200 zgłoszeń miesięcznie, 3 osoby serwisu, jeden programista utrzymujący, dane osobowe
zgłaszających, wymóg hostingu w UE, termin 6 tygodni, istniejący system fakturowania z
API REST. Skala rzeczywista: kilka zgłoszeń na godzinę w szczycie.

**Krok 3 (domeny).** `zgloszenia` (cykl życia zgłoszenia, priorytet, SLA),
`klienci` (kontrahent, umowa, uprawnienia zgłaszających), `komunikacja` (wiadomości,
załączniki, powiadomienia), `rozliczenia` (godziny, integracja z fakturowaniem).
Granica transakcyjna: zmiana statusu zgłoszenia + wpis do historii = jedna transakcja.
Powiadomienie e-mail — poza transakcją, przez outbox.

**Krok 4 (technologie).** Monolit modularny, Postgres, wysyłka poczty przez dostawcę,
pliki w S3-kompatybilnym magazynie w UE. ADR-y: wybór bazy (jeden akapit, oczywisty),
sposób uwierzytelniania (istotny — sesje vs OIDC klienta), integracja z fakturowaniem
(istotny — synchroniczna vs kolejka zdarzeń, bo API zewnętrzne bywa niedostępne).

**Krok 5 (dane).** Encje: `Zgloszenie`, `ZdarzenieZgloszenia` (niemutowalne),
`Klient`, `Uzytkownik`, `Zalacznik`, `WpisCzasu`. Klucze UUIDv7. Czas `TIMESTAMPTZ`.
Kwoty w groszach jako `BIGINT` + kod waluty. Historia zgłoszenia jako append-only —
to daje audyt za darmo i usuwa potrzebę miękkiego usuwania.

**Krok 6 (kontrakty).** OpenAPI dla API klienta (7 endpointów), format błędu wg
RFC 9457, paginacja kursorowa po `(utworzono, id)`, idempotencja na tworzeniu zgłoszenia
przez nagłówek `Idempotency-Key`. Port `KsiegowanieCzasu` z jedną metodą — implementacja
adaptera do systemu fakturowania i implementacja atrapy do testów.

**Krok 7.** Dopiero teraz pliki.

Czego **nie** ma w tym projekcie i dlaczego: kolejki brokerowej (200 zgłoszeń/miesiąc —
wystarczy tabela outbox), cache (nie zmierzono problemu), osobnej usługi powiadomień
(jeden moduł w monolicie), warstwy GraphQL (jeden konsument), Kubernetes (jeden proces).

## Twarde reguły

1. **Nie piszesz kodu przed nazwaniem granic.** Minimum: lista modułów i ich
   odpowiedzialności w jednym zdaniu każdy.
2. **Domyślną odpowiedzią na „mikrousługi?” jest „nie”.** Monolit modularny, dopóki
   nie masz pisemnego powodu (zespoły, izolacja skali, izolacja awarii, zgodność).
3. **Domena nie importuje infrastruktury.** Żadnego ORM-a, klienta HTTP, SDK dostawcy
   ani typu frameworka w warstwie domenowej. Naruszenie: za pół roku zmiana dostawcy
   płatności wymaga przepisania reguł biznesowych.
4. **Pieniądze nigdy jako `float`/`double`.** Liczba całkowita w najmniejszej jednostce
   albo `DECIMAL(19,4)` plus jawny kod waluty. Naruszenie: rozjazd sald przy sumowaniu.
5. **Czas zawsze w UTC w bazie, strefa jawnie tam, gdzie ma znaczenie prawne.**
   `TIMESTAMPTZ`, nie `TIMESTAMP`. Naruszenie: podwójne godziny przy zmianie czasu.
6. **Każda decyzja nieodwracalna ma ADR.** Bez ADR za pół roku nikt nie wie, dlaczego
   tak jest, więc nikt nie odważy się tego zmienić — albo zmieni bez zrozumienia.
7. **Kontrakt przed implementacją.** Typy/OpenAPI/schemat zdarzenia najpierw.
8. **Nie wprowadzasz abstrakcji dla jednej implementacji.** Interfejs z jedną klasą to
   nie architektura, to dodatkowy plik. Wyjątek: granica portu do systemu zewnętrznego
   albo rzecz podmieniana w testach.
9. **Nie przepisujesz systemu od zera.** Domyślnie: dławienie starego przez nowy
   (`references/engineering-core/references/dlug-techniczny.md`). Warunki wyjątku są tam wypisane.
10. **Zmiana funkcjonalna i refaktoryzacja nie mieszają się w jednym commicie.**
11. **Nie dodajesz zależności bez odpowiedzi na: kto to utrzymuje, jaka licencja,
    ile kosztuje wyjście.** Naruszenie: porzucona paczka blokuje aktualizację runtime'u.
12. **Nie optymalizujesz bez pomiaru.** Optymalizacja bez profilu to zgadywanie,
    które kosztuje czytelność i zwykle trafia w niewłaściwe miejsce.

## Antywzorce, które model popełnia najczęściej

| Antywzorzec | Co się dzieje | Zamiast tego |
| --- | --- | --- |
| Zaczyna od `app/api/...` i wpisuje logikę w handler | Logika nietestowalna bez HTTP; duplikacja przy drugim wejściu (cron, CLI) | Przypadek użycia jako funkcja, handler tylko go wywołuje |
| Tworzy `services/`, `utils/`, `helpers/` jako główny podział | Podział techniczny zamiast domenowego; każda zmiana biznesowa dotyka pięciu katalogów | Podział po domenach, warstwy wewnątrz domeny |
| Projektuje pod skalę, której nie ma | Kolejki, cache, sharding przy 3 rps; koszt utrzymania bez zysku | Najprostsza rzecz, która działa; skalowanie jako odroczona decyzja z progiem |
| Kopiuje strukturę z tutoriala mikroserwisowego | Granice sieciowe wewnątrz jednej domeny transakcyjnej; utrata transakcji | Monolit modularny, moduły z jawnym API |
| Modeluje dane pod ekran, nie pod domenę | Schemat zmienia się przy każdej zmianie UI | Model domenowy niezależny, DTO osobno |
| Wprowadza cache przy pierwszym „wolno” | Niespójność danych, trudne błędy | Najpierw indeks i zapytanie, cache jako ostatnie |
| Odpowiada „to zależy” bez rozstrzygnięcia | Użytkownik nie ma decyzji | Podaj rekomendację + warunek, przy którym byłaby inna |

## Kontrola przed oddaniem

Zanim uznasz zadanie architektoniczne za skończone, sprawdź:

- [ ] Wymagania zapisane w ≤5 zdaniach; założenia oznaczone jako założenia.
- [ ] Ograniczenia wypisane, twarde odróżnione od miękkich.
- [ ] Moduły nazwane, każdy z jednozdaniową odpowiedzialnością i jawnym API.
- [ ] Kierunek zależności sprawdzony: nic z zewnątrz nie wchodzi do domeny.
- [ ] Granice transakcyjne wskazane — co musi być atomowe, a co może być spójne później.
- [ ] Każda decyzja nieodwracalna ma ADR z co najmniej dwiema odrzuconymi alternatywami.
- [ ] Schemat danych: klucze, typy czasu i pieniędzy, strategia migracji.
- [ ] Kontrakty API zapisane jako typy/OpenAPI, z formatem błędu i paginacją.
- [ ] Wskazane, co jest najbardziej prawdopodobną osią zmiany i jak system to znosi.
- [ ] Wskazany najsłabszy punkt projektu i jego koszt — jawnie, nie w domyśle.
- [ ] Nic nie zostało zaprojektowane „na zapas” bez potwierdzonej potrzeby.

Ostatnie pytanie do samego siebie przed oddaniem: **czy usunięcie któregokolwiek
elementu tego projektu odebrałoby użytkownikowi coś, na czym mu zależy?** Jeśli nie —
usuń ten element.
