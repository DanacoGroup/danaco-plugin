# ADR — zapis decyzji architektonicznej

ADR (Architecture Decision Record) to jednostronicowy zapis: jaka była sytuacja, co
zdecydowano, czego nie wybrano i dlaczego, oraz co z tego wynika. Powstaje **w momencie
decyzji**, nie po fakcie, i nie jest później zmieniany — decyzję unieważnia się nowym
ADR-em, który zastępuje stary.

Wartość ADR-a ujawnia się dopiero za 6–18 miesięcy, gdy ktoś (najczęściej autor) patrzy
na dziwną konstrukcję w kodzie i nie wie, czy to przemyślany kompromis, czy pomyłka.
Bez ADR-a odpowiedź brzmi „nie ruszaj, bo się zepsuje” — i system zamarza.

## Kiedy piszesz ADR

Piszesz, gdy decyzja spełnia **co najmniej jeden** warunek:

| Warunek | Przykład |
| --- | --- |
| Odwrócenie kosztuje >1 tydzień pracy | Wybór bazy danych, model uwierzytelniania |
| Decyzja wiąże inne decyzje | Wybór runtime'u przesądza o bibliotekach |
| Wybrano opcję nieoczywistą wbrew domyślnej | Osobna usługa zamiast modułu; NoSQL zamiast Postgresa |
| Konsekwencje ponosi ktoś inny niż decydujący | Kontrakt API, format danych, SLA |
| Decyzja wynika z ograniczenia, które zniknie | „Na razie synchronicznie, bo brak czasu na outbox” |
| Rozstrzygnięto spór w zespole | Cokolwiek, o czym dyskutowano dłużej niż 30 minut |

**Nie piszesz ADR-a** dla: wyboru formattera, nazwy zmiennej, biblioteki do dat
podmienialnej w godzinę, struktury pojedynczego komponentu, decyzji wewnątrz jednego
pliku. ADR na wszystko to biurokracja, która sprawia, że nikt nie czyta żadnego.

Praktyczna miara: projekt roczny generuje 8–25 ADR-ów. Jeśli masz 3, nie zapisujesz
decyzji. Jeśli masz 80, zapisujesz preferencje zamiast decyzji.

## Szablon

Plik `docs/adr/NNNN-krotki-tytul.md`, numeracja czterocyfrowa, nigdy nie recyklowana.

```markdown
# ADR-0007: Kolejkowanie zadań w tabeli Postgresa zamiast brokera

- Status: Zaakceptowana
- Data: 2026-08-04
- Decydujący: <imię/rola>
- Konsultowani: <kto>
- Dotyczy: moduł powiadomień, moduł rozliczeń
- Zastępuje: —
- Zastąpiona przez: —

## Kontekst

<Fakty, nie oceny. Co jest dziś, jakie liczby, jakie ograniczenia, co wymusza decyzję
teraz. Ktoś czytający za rok ma z tego zrozumieć sytuację bez pytania nikogo.
3-8 zdań. Podaj konkretne wielkości.>

## Rozważane opcje

### A. <Nazwa> — WYBRANA
<2-4 zdania: na czym polega.>
- Za: <konkretnie, z liczbą jeśli się da>
- Przeciw: <konkretnie>
- Koszt wyjścia: <ile pracy, gdyby trzeba było zmienić>

### B. <Nazwa> — odrzucona
<To samo. Odrzucenie z jednozdaniowym uzasadnieniem na końcu.>

### C. <Nazwa> — odrzucona
<To samo.>

## Decyzja

<Jedno zdanie w trybie oznajmującym: "Używamy X do Y." Bez "rozważamy", "prawdopodobnie".>

## Uzasadnienie

<Dlaczego A wygrało z B i C. Odnieś się do kryteriów z Kontekstu, nie do ogólnych zalet.>

## Konsekwencje

Ułatwia:
- <co teraz jest prostsze>

Utrudnia:
- <co teraz jest trudniejsze — ta lista NIE MOŻE być pusta>

Wymaga:
- <co trzeba zrobić, żeby decyzja zadziałała>

## Warunki rewizji

<Mierzalny próg, po przekroczeniu którego wracamy do tej decyzji.
"Gdy X przekroczy N" — nie "gdy będzie za wolno".>
```

## Jak formułować poszczególne sekcje

### Kontekst — fakty z liczbami

| Źle | Dobrze |
| --- | --- |
| „Potrzebujemy skalowalnego rozwiązania” | „Dziś 200 zdarzeń dziennie, prognoza handlowa 2 000 dziennie w 2027” |
| „Zespół jest mały” | „Jedna osoba utrzymuje, 20% etatu na utrzymanie” |
| „Baza jest wolna” | „p95 zapytania listy zgłoszeń: 1,4 s przy 400 tys. wierszy” |
| „Wymagana wysoka dostępność” | „SLA w umowie: 99,5% miesięcznie, kara 5% wynagrodzenia” |

Kontekst bez liczb jest bezużyteczny przy rewizji, bo nie da się sprawdzić, czy sytuacja
się zmieniła.

### Alternatywy — muszą być prawdziwe

Najczęstsza patologia ADR-ów: dwie alternatywy dopisane po fakcie, żeby wybrana wyglądała
lepiej („Opcja B: napisać własną bazę danych”). To fałszowanie zapisu.

Zasady:

- Minimum dwie realne alternatywy plus **zawsze rozważ „nie robić nic”**. Zaskakująco
  często jest to najlepsza opcja i jej brak w zestawieniu jest sygnałem ostrzegawczym.
- Alternatywa musi mieć zapisaną **zaletę, która faktycznie przemawia** na jej korzyść.
  Jeśli nie potrafisz jej znaleźć, to nie jest alternatywa.
- Odrzucenie musi być uzasadnione **kryterium z kontekstu**, nie ogólną wadą.
  „Kafka odrzucona, bo złożona” — słabe. „Kafka odrzucona, bo dodaje usługę do
  utrzymania przy 20% etatu na utrzymanie i 200 zdarzeniach dziennie” — mocne.
- Podaj **koszt wyjścia** dla każdej opcji. To najczęściej pomijana i najważniejsza
  informacja przy rewizji.

### Konsekwencje — sekcja „Utrudnia” nie może być pusta

ADR bez wad wybranego rozwiązania jest reklamą, nie zapisem decyzji. Każdy wybór coś
zamyka. Jeśli nie potrafisz wskazać czego, nie rozumiesz jeszcze wyboru.

Konsekwencje pisz w czasie przyszłym dokonanym: „każdy nowy konsument będzie musiał
obsłużyć duplikaty”, a nie „może pojawić się problem z duplikatami”.

### Warunki rewizji — próg, nie przeczucie

| Źle | Dobrze |
| --- | --- |
| „Wrócimy do tego, gdy urośniemy” | „Gdy przetwarzanie kolejki przekroczy 500 zdarzeń/min przez 3 dni z rzędu” |
| „Jeśli okaże się za wolne” | „Gdy p95 czasu od zapisu do wysyłki przekroczy 60 s” |
| „Przy większym zespole” | „Gdy nad tym modułem pracują 2 zespoły z osobnymi cyklami wydawniczymi” |

## Status i cykl życia

| Status | Znaczenie |
| --- | --- |
| `Proponowana` | Napisana, czeka na akceptację. Kod jej jeszcze nie realizuje |
| `Zaakceptowana` | Obowiązuje. Kod ma być z nią zgodny |
| `Odrzucona` | Rozważona i odrzucona. **Zostaje w repozytorium** — chroni przed powtórnym rozważaniem |
| `Wycofana` | Przestała obowiązywać, nic jej nie zastąpiło (funkcja usunięta) |
| `Zastąpiona przez ADR-NNNN` | Decyzja zmieniona. Stary plik zostaje, dopisujesz odnośnik |

**Nigdy nie edytuj treści zaakceptowanego ADR-a.** Wyjątek: literówka, dopisanie pola
`Zastąpiona przez`. Zmiana decyzji = nowy plik. Historia decyzji jest wartością samą
w sobie — pokazuje, jak myślenie zespołu ewoluowało i czego już próbowano.

---

# Pięć pełnych przykładów

## ADR-0001: PostgreSQL jako podstawowa baza danych

- Status: Zaakceptowana
- Data: 2026-08-04
- Decydujący: architekt prowadzący
- Dotyczy: cały system

### Kontekst

System obsługi zgłoszeń serwisowych: 40 klientów B2B, ~200 zgłoszeń miesięcznie,
prognoza 3-letnia do 1 000 miesięcznie. Dane silnie relacyjne (zgłoszenie → klient →
umowa → pozycje rozliczenia), wymagana spójność przy rozliczeniach finansowych.
Wymóg raportowania ad-hoc przez dział finansowy. Wymóg hostingu w UE (RODO).
Utrzymanie: jeden programista, ~20% etatu. Zespół zna SQL, nie zna żadnej bazy
dokumentowej.

### Rozważane opcje

**A. PostgreSQL 18 — WYBRANA.**
Relacyjna baza z transakcjami ACID, `JSONB` dla danych półstrukturalnych,
`tsvector` dla wyszukiwania pełnotekstowego, wbudowany `uuidv7()`.
- Za: transakcje wielotabelowe bez ceremonii; raportowanie SQL bez dodatkowej warstwy;
  `JSONB` obsługuje pola zmienne per klient bez migracji schematu; jedna baza pokrywa
  też kolejkę (`SKIP LOCKED`) i wyszukiwanie; hosting zarządzany w UE u każdego dostawcy.
- Przeciw: schemat wymaga migracji przy zmianach; skalowanie zapisu ograniczone do
  jednej instancji (nieistotne przy tej skali).
- Koszt wyjścia: wysoki — SQL i typy przenikają warstwę infrastruktury. Ograniczony
  przez wzorzec repozytorium: ~2 tygodnie na wymianę adapterów.

**B. MongoDB — odrzucona.**
- Za: brak migracji schematu przy zmiennych polach; szybki start.
- Przeciw: rozliczenia wymagają spójności wielodokumentowej — transakcje istnieją, ale
  są droższe i mniej naturalne; raportowanie ad-hoc wymaga agregacji, których dział
  finansowy nie napisze; zespół nie zna.
- Odrzucona, bo rdzeniem systemu są rozliczenia wymagające spójności, a nie elastyczność
  schematu.

**C. SQLite — odrzucona.**
- Za: zero administracji, plik, najprostsze wdrożenie i kopie zapasowe.
- Przeciw: jeden zapisujący; brak dostępu sieciowego dla przyszłych procesów w tle;
  brak natywnych typów `TIMESTAMPTZ`, co przy pracy w wielu strefach jest ryzykiem.
- Odrzucona, bo planujemy proces roboczy poza aplikacją webową (outbox).

**D. Nie decydować teraz, użyć ORM-a abstrahującego bazę — odrzucona.**
- Za: odroczenie decyzji.
- Przeciw: abstrakcja sprowadza się do części wspólnej możliwości baz, czyli tracimy
  `JSONB`, `SKIP LOCKED`, wyszukiwanie pełnotekstowe; decyzja i tak zapada implicite.
- Odrzucona: odroczenie decyzji o bazie kosztuje więcej niż decyzja.

### Decyzja

Używamy PostgreSQL 18 jako jedynej bazy danych systemu.

### Uzasadnienie

Rdzeniem systemu są rozliczenia wymagające spójności transakcyjnej, a nie elastyczność
schematu. Skala (setki zgłoszeń miesięcznie) mieści się w jednej instancji z ogromnym
zapasem. Jedna baza pokrywa cztery potrzeby (dane, kolejka, wyszukiwanie, raporty),
co przy 20% etatu na utrzymanie jest decydujące.

### Konsekwencje

Ułatwia: transakcje między modułami; raportowanie bez ETL; kolejkę bez brokera;
wyszukiwanie bez Elasticsearcha; kopie zapasowe (jeden zasób).

Utrudnia: każda zmiana kształtu danych wymaga migracji; nie ma poziomego skalowania
zapisu; pola zmienne per klient w `JSONB` nie są sprawdzane przez schemat i wymagają
walidacji w aplikacji.

Wymaga: narzędzia migracji z wersjonowaniem od pierwszego dnia; monitoringu rozmiaru
tabel i czasu zapytań; kopii zapasowych z odtworzeniem punktowym (PITR).

### Warunki rewizji

Gdy pojedyncza tabela przekroczy 200 mln wierszy albo obciążenie zapisem przekroczy
50% czasu CPU instancji przez tydzień.

---

## ADR-0007: Kolejka zadań w tabeli Postgresa zamiast brokera

- Status: Zaakceptowana
- Data: 2026-08-04
- Dotyczy: powiadomienia, integracja z fakturowaniem

### Kontekst

Trzy rodzaje pracy asynchronicznej: e-maile do klientów (~30/dzień), synchronizacja
z systemem fakturowania (~50 wywołań/dzień, API zewnętrzne z historią niedostępności
kilka razy w miesiącu), generowanie raportów PDF (~5/dzień, do 20 s każdy). Łącznie
poniżej 100 zadań dziennie, szczyt ~20 zadań w ciągu godziny. Jedna osoba utrzymuje.
Baza to PostgreSQL 18 (ADR-0001). Wymóg: żadne zdarzenie nie może zginąć, bo
niewysłana synchronizacja z fakturowaniem oznacza niewystawioną fakturę.

### Rozważane opcje

**A. Tabela `outbox` w Postgresie + proces roboczy z `SELECT ... FOR UPDATE SKIP LOCKED` —
WYBRANA.**
- Za: zdarzenie i zmiana danych w jednej transakcji — brak scenariusza „wysłane, ale
  nie zapisane”; zero dodatkowych usług; podgląd stanu kolejki zwykłym `SELECT`;
  ponowienie przez `UPDATE`; kopia zapasowa obejmuje kolejkę.
- Przeciw: odpytywanie (polling) zamiast zdarzeń — opóźnienie rzędu sekund; przepustowość
  ograniczona do kilkuset zadań/s; trzeba samodzielnie napisać ponowienia i wykładnicze
  wycofywanie (~120 linii).
- Koszt wyjścia: niski — interfejs `KolejkaZadan` w warstwie aplikacji, wymiana adaptera
  to ~2 dni.

**B. RabbitMQ — odrzucona.**
- Za: właściwe narzędzie do kolejkowania; ponowienia, DLQ, priorytety w standardzie;
  natychmiastowe dostarczenie bez odpytywania.
- Przeciw: druga usługa stanowa do utrzymania, monitorowania i kopiowania; zdarzenie
  poza transakcją bazy, więc i tak potrzebny outbox, żeby nie zgubić; lokalne
  środowisko rośnie o kontener.
- Odrzucona: przy <100 zadaniach dziennie i 20% etatu na utrzymanie koszt operacyjny
  przewyższa zysk. Outbox i tak byłby potrzebny.

**C. Kolejka zarządzana u dostawcy chmury — odrzucona.**
- Za: brak administracji; ponowienia i DLQ w standardzie.
- Przeciw: przywiązanie do dostawcy; ten sam problem transakcyjności co B; koszt
  środowiska lokalnego (emulator albo atrapa).
- Odrzucona z tego samego powodu co B, dodatkowo koszt wyjścia.

**D. Wywołania synchroniczne bez kolejki — odrzucona.**
- Za: najprostsze; zero infrastruktury.
- Przeciw: niedostępność API fakturowania kończy się utratą zdarzenia albo błędem
  widocznym dla użytkownika przy operacji, która go nie dotyczy; generowanie PDF
  blokuje żądanie na 20 s.
- Odrzucona: wymóg „żadne zdarzenie nie może zginąć” wprost tego zabrania.

### Decyzja

Zdarzenia asynchroniczne zapisujemy do tabeli `outbox` w tej samej transakcji co zmianę
danych. Osobny proces roboczy pobiera je przez `FOR UPDATE SKIP LOCKED`.

### Uzasadnienie

Twardym wymaganiem jest brak utraty zdarzeń, a nie przepustowość ani opóźnienie.
Outbox rozwiązuje wymaganie twarde przy zerowym koszcie operacyjnym. Broker rozwiązuje
przepustowość, której nie potrzebujemy, i **nie** rozwiązuje utraty zdarzeń bez outboxu.

### Konsekwencje

Ułatwia: atomowość zmiany i zdarzenia; diagnostykę (stan kolejki widoczny w SQL);
odtworzenie po awarii; środowisko lokalne bez dodatkowych kontenerów.

Utrudnia: opóźnienie dostarczenia rzędu 1–5 s (interwał odpytywania); trzeba
samodzielnie zaimplementować ponowienia, wycofywanie wykładnicze i limit prób;
proces roboczy trzeba osobno wdrażać i monitorować; przy wielu procesach roboczych
odpytywanie obciąża bazę.

Wymaga: kolumn `proby`, `nastepna_proba`, `ostatni_blad`, `przetworzono` w tabeli;
indeksu częściowego na niewysłanych; alertu, gdy najstarsze nieprzetworzone zdarzenie
ma >5 minut; limitu prób z przeniesieniem do `outbox_martwe` po 10 nieudanych.

### Warunki rewizji

Gdy liczba zadań przekroczy 500/min przez godzinę, gdy opóźnienie p95 przekroczy 60 s,
albo gdy pojawi się drugi konsument o istotnie innym tempie przetwarzania.

---

## ADR-0012: Monolit modularny zamiast mikrousług

- Status: Zaakceptowana
- Data: 2026-08-04
- Dotyczy: cały system

### Kontekst

Zespół: 2 programistów, jeden wspólny cykl wydawniczy. Cztery domeny: zgłoszenia,
klienci, komunikacja, rozliczenia. Ruch: szczyt ~5 żądań/s. Rozliczenia wymagają
spójności ze zgłoszeniami (czas pracy zarejestrowany przy zgłoszeniu wchodzi na
fakturę). Wymóg wdrożenia produkcyjnego w 6 tygodni. Wcześniejszy projekt zespołu
został podzielony na 5 usług i spędzono ~30% czasu na koordynacji wersji kontraktów.

### Rozważane opcje

**A. Monolit modularny, jedno wdrożenie, moduły jako katalogi z jawnym API — WYBRANA.**
- Za: transakcja obejmująca zgłoszenie i rozliczenie bez sagi; jeden artefakt; jedno
  środowisko lokalne; refaktoryzacja granic modułów z pomocą kompilatora; wdrożenie
  w 6 tygodni realne.
- Przeciw: całość skaluje się razem; awaria jednego modułu może położyć proces;
  ryzyko erozji granic, jeśli nie egzekwowane narzędziami.
- Koszt wyjścia: średni — wydzielenie modułu do usługi to ~2–3 tygodnie na moduł,
  pod warunkiem że granice były pilnowane.

**B. Mikrousługi per domena (4 usługi) — odrzucona.**
- Za: niezależne wdrożenia; izolacja awarii; niezależne skalowanie.
- Przeciw: rozliczenia + zgłoszenia wymagają sagi z kompensacją; 2 osoby na 4 usługi to
  brak właściciela; środowisko lokalne z 4 usługami + bazą; termin 6 tygodni nierealny.
- Odrzucona: przy 2 osobach nie ma organizacyjnego powodu do niezależnych wdrożeń, a
  spójność rozliczeń przemawia przeciw granicy sieciowej w tym miejscu.

**C. Monolit bez podziału na moduły — odrzucona.**
- Za: najszybszy start.
- Przeciw: bez granic kod splata się w 3–6 miesięcy; późniejsze wydzielenie czegokolwiek
  staje się przepisaniem.
- Odrzucona: koszt granic jest dziś niski (konfiguracja lintera), a zysk realny.

### Decyzja

Budujemy monolit modularny: jeden proces, cztery moduły w `src/modules/`, komunikacja
wyłącznie przez `index.ts` modułu lub zdarzenia outbox.

### Uzasadnienie

Powodem do wydzielania usług jest niezależność organizacyjna albo skrajnie różny profil
zasobowy. Nie zachodzi żaden z nich. Granica sieciowa między zgłoszeniami a
rozliczeniami kosztowałaby sagę tam, gdzie wystarczy `COMMIT`.

### Konsekwencje

Ułatwia: transakcje; debugowanie (jeden stos); wdrożenie; onboarding.

Utrudnia: nie da się skalować pojedynczego modułu; długie generowanie raportu obciąża
ten sam proces co API (mitygowane osobnym procesem roboczym); granice trzeba egzekwować
narzędziami, bo kompilator sam ich nie pilnuje.

Wymaga: `dependency-cruiser` w CI blokujący import z wnętrza cudzego modułu; osobne
tabele per moduł bez JOIN-ów międzymodułowych; przegląd granic co kwartał.

### Warunki rewizji

Gdy nad systemem pracują ≥2 zespoły o osobnych cyklach wydawniczych, gdy któryś moduł
wymaga profilu zasobowego różnego o rząd wielkości, albo gdy czas budowania i testów
przekroczy 15 minut.

---

## ADR-0015: Sesje po stronie serwera zamiast JWT

- Status: Zaakceptowana
- Data: 2026-08-04
- Dotyczy: dostęp, cały system

### Kontekst

Konsumenci: przeglądarka (panel klienta i panel serwisu). Brak aplikacji mobilnej,
brak API dla stron trzecich w planie 12-miesięcznym. Wymóg biznesowy: administrator
musi móc **natychmiast** odciąć dostęp zwolnionemu pracownikowi klienta. Dane osobowe
zgłaszających — RODO. Jedna aplikacja, jedna baza (ADR-0001).

### Rozważane opcje

**A. Sesja po stronie serwera, identyfikator w cookie `HttpOnly; Secure; SameSite=Lax` — WYBRANA.**
- Za: natychmiastowe unieważnienie (`DELETE FROM sesje`); token niedostępny dla
  JavaScriptu, więc XSS nie wykrada sesji; brak danych w tokenie, więc brak wycieku
  przy przechwyceniu; rotacja i wygaszanie w jednym miejscu.
- Przeciw: odczyt sesji z bazy przy każdym żądaniu (~0,3 ms z indeksem); stan po stronie
  serwera utrudnia rozdzielenie na wiele niezależnych usług.
- Koszt wyjścia: niski — warstwa uwierzytelnienia jest jednym middleware.

**B. JWT w localStorage — odrzucona.**
- Za: bezstanowo; łatwe skalowanie poziome; standard w wielu poradnikach.
- Przeciw: brak unieważnienia bez listy odwołań (czyli i tak stan po stronie serwera —
  cały zysk znika); `localStorage` dostępny dla JS, więc XSS = kradzież tokenu;
  token z rolami dezaktualizuje się do wygaśnięcia.
- Odrzucona: wymóg natychmiastowego odcięcia dostępu jest z nią wprost sprzeczny.

**C. JWT w cookie HttpOnly z krótkim czasem życia + token odświeżający — odrzucona.**
- Za: bezpieczniejszy magazyn niż B; okno nadużycia ograniczone do czasu życia tokenu.
- Przeciw: dwa tokeny, rotacja, wykrywanie ponownego użycia tokenu odświeżającego —
  istotnie więcej kodu do napisania i przetestowania; okno unieważnienia nadal >0.
- Odrzucona: złożoność nieuzasadniona przy jednym kliencie przeglądarkowym.

**D. Zewnętrzny dostawca tożsamości (OIDC) — odrzucona na teraz.**
- Za: MFA, reset hasła, audyt logowań poza naszym kodem; zgodność.
- Przeciw: koszt miesięczny; przywiązanie do dostawcy; nadmiar przy 40 klientach B2B
  bez wymogu SSO.
- Odrzucona na teraz. Wróci, gdy klient korporacyjny zażąda SSO — patrz warunki rewizji.

### Decyzja

Uwierzytelnianie sesjami po stronie serwera. Identyfikator sesji (128 bitów z CSPRNG)
w cookie `HttpOnly; Secure; SameSite=Lax; Path=/`. Sesje w tabeli `sesje` z kolumnami
`wygasa`, `ostatnia_aktywnosc`, `user_agent_hash`.

### Uzasadnienie

Twardym wymaganiem jest natychmiastowe unieważnienie. JWT jest z nim strukturalnie
sprzeczny; obejścia sprowadzają JWT do sesji z dodatkowymi krokami. Jedyna przewaga
JWT — bezstanowość — nie ma tu wartości, bo i tak mamy jedną bazę i jeden proces.

### Konsekwencje

Ułatwia: wylogowanie ze wszystkich urządzeń; zmianę uprawnień działającą natychmiast;
audyt aktywnych sesji; brak wrażliwych danych po stronie klienta.

Utrudnia: każde żądanie to dodatkowe zapytanie do bazy; przyszłe wydzielenie usług
wymaga współdzielonego magazynu sesji; API dla klientów nieprzeglądarkowych wymaga
osobnego mechanizmu (tokeny API) — nie sesji.

Wymaga: ochrony CSRF (`SameSite=Lax` pokrywa większość, dodatkowo token dla żądań
zmieniających stan wysyłanych spoza formularzy); indeksu na `sesje(wygasa)` i zadania
czyszczącego; rotacji identyfikatora sesji przy logowaniu (ochrona przed utrwaleniem
sesji); haszowania haseł Argon2id.

### Warunki rewizji

Gdy pojawi się klient wymagający SSO/SAML, gdy powstanie aplikacja mobilna, albo gdy
system zostanie rozdzielony na niezależnie wdrażane usługi.

---

## ADR-0019: Fastify zamiast NestJS i Express

- Status: Zaakceptowana
- Data: 2026-08-04
- Dotyczy: warstwa HTTP

### Kontekst

Backend w TypeScript na Node 22. Architektura: monolit modularny z portami i adapterami
(ADR-0012), przypadki użycia jako zwykłe funkcje. ~35 endpointów. Wymóg: kontrakt
OpenAPI generowany z kodu, walidacja wejścia zgodna z tym kontraktem. Zespół zna
Express. Termin 6 tygodni.

### Rozważane opcje

**A. Fastify + `@fastify/swagger` + walidacja schematami JSON Schema — WYBRANA.**
- Za: schemat trasy pełni jednocześnie rolę walidacji, dokumentacji OpenAPI i typów
  (`fastify-type-provider-typebox`) — jedno źródło; wbudowana serializacja odpowiedzi
  według schematu zapobiega wyciekowi pól; obsługa błędów asynchronicznych domyślnie;
  wydajność ~2× Express na tym profilu.
- Przeciw: mniejszy ekosystem wtyczek niż Express; zespół musi poznać system wtyczek
  i enkapsulację kontekstu (~1 dzień).
- Koszt wyjścia: niski — warstwa HTTP to cienkie handlery wywołujące przypadki użycia.

**B. Express 5 — odrzucona.**
- Za: zespół zna; największy ekosystem; najwięcej materiałów.
- Przeciw: brak wbudowanej walidacji i schematów, więc OpenAPI trzeba utrzymywać ręcznie
  albo dokładać dwie biblioteki; łatwo wyciec polami encji przy `res.json(encja)`.
- Odrzucona: wymóg „kontrakt generowany z kodu” wymagałby zbudowania w Expressie tego,
  co Fastify ma wbudowane.

**C. NestJS — odrzucona.**
- Za: struktura narzucona z góry; dekoratory; generowanie OpenAPI; duży ekosystem.
- Przeciw: narzuca własny model DI i moduły, który dubluje nasz podział na moduły i
  porty — dwie konkurujące struktury; dekoratory i metadane przenoszą błędy z czasu
  kompilacji do czasu wykonania; istotny narzut nauki przy 6-tygodniowym terminie.
- Odrzucona: wnosi opinię architektoniczną, którą już mamy — z ADR-0012.

**D. Sam `node:http` — odrzucona.**
- Za: zero zależności.
- Przeciw: routing, parsowanie ciała, cookies, obsługa błędów — do napisania.
- Odrzucona: to problem rozwiązany, klasyfikacja „ogólne”, nie budujemy własnego.

### Decyzja

Warstwa HTTP oparta na Fastify 5 z TypeBox jako źródłem schematów walidacji, typów
TypeScript i dokumentu OpenAPI.

### Uzasadnienie

Wymóg jednego źródła prawdy dla kontraktu rozstrzyga. Fastify daje to wbudowanie;
Express wymaga złożenia z trzech bibliotek; Nest daje, ale w pakiecie z modelem
architektonicznym konkurującym z naszym.

### Konsekwencje

Ułatwia: utrzymanie zgodności dokumentacji z implementacją; walidację wejścia bez
osobnej warstwy; blokadę wycieku pól przez schemat odpowiedzi.

Utrudnia: część bibliotek middleware wymaga adaptera `@fastify/middie`; system wtyczek
z enkapsulacją bywa mylący na starcie (dekorator zarejestrowany w potomku nie jest
widoczny w rodzicu).

Wymaga: schematu dla każdej trasy, także odpowiedzi; testu porównującego wygenerowany
OpenAPI z zatwierdzonym plikiem (wykrywa niezamierzone zmiany kontraktu).

### Warunki rewizji

Gdy potrzeba biblioteki dostępnej wyłącznie jako middleware Express, której adapter nie
działa, albo gdy zespół urośnie ponad 6 osób i narzucona struktura Nest zacznie mieć
przewagę koordynacyjną.

---

## Rewizja decyzji

Rewizja nie polega na edycji starego pliku. Polega na napisaniu nowego ADR-a, który:

1. W polu `Zastępuje` wskazuje stary numer.
2. W `Kontekście` opisuje **co się zmieniło** względem sytuacji z tamtego ADR-a —
   najlepiej przez porównanie liczb: „ADR-0007 zakładał <100 zadań dziennie; obecnie
   4 200 dziennie, p95 opóźnienia 8 minut”.
3. Ocenia, czy stara decyzja była **błędna wtedy**, czy tylko **przestała pasować**.
   To rozróżnienie jest ważne: pierwsze wymaga poprawy procesu decyzyjnego, drugie jest
   normalnym cyklem życia.

W starym pliku dopisujesz jedną linię: `Zastąpiona przez: ADR-NNNN`. Nic więcej.

### Sygnały, że decyzję trzeba zrewidować

| Sygnał | Co robić |
| --- | --- |
| Przekroczony próg z „Warunków rewizji” | Napisz nowy ADR lub jawnie potwierdź starą decyzję (`Potwierdzona <data>`) |
| Kod systematycznie obchodzi decyzję | Decyzja jest martwa. Zapisz stan faktyczny albo egzekwuj starą |
| Trzy razy w kwartale ktoś pyta „dlaczego tak?” | ADR jest nieczytelny albo nie istnieje |
| Zniknęło ograniczenie z „Kontekstu” | Sprawdź, czy decyzja nadal ma podstawę |
| Autor decyzji odszedł, nikt nie umie jej obronić | Nie zmieniaj pochopnie. Najpierw odtwórz kontekst z ADR-a |

### Czego nie robić przy rewizji

- Nie usuwaj starych ADR-ów. Odrzucona opcja zapisana w ADR-0001 chroni przed
  ponownym rozważaniem MongoDB co pół roku.
- Nie oceniaj starej decyzji wiedzą, której wtedy nie było. Pytanie brzmi: „czy przy
  ówczesnych informacjach ta decyzja była rozsądna?”, nie „czy okazała się optymalna”.
- Nie rewiduj decyzji, której konsekwencje jeszcze nie nastąpiły. Trzy miesiące to
  za mało, by ocenić wybór bazy.
