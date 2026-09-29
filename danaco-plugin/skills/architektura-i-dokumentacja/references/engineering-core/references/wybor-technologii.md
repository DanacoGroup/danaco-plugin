# Wybór technologii

Wybór technologii jest decyzją o **kosztach przez najbliższe lata**, a nie o zaletach
w dniu wyboru. Ocena „czy to jest dobre” jest bezużyteczna. Użyteczna jest ocena
„ile będzie kosztować utrzymanie tego przy naszym zespole i naszej skali, i ile
kosztowałoby wyjście”.

## Ramy oceny

Sześć wymiarów, w kolejności ważności. Wymiar 1 unieważnia wszystkie pozostałe.

### 1. Ograniczenia zespołu

| Pytanie | Waga |
| --- | --- |
| Ile osób to zna dziś? | Rozstrzygające |
| Ile osób będzie utrzymywać po wdrożeniu i przy jakim udziale etatu? | Rozstrzygające |
| Ile trwa doprowadzenie zespołu do samodzielności? | Wysoka |
| Da się zatrudnić kogoś z tą technologią na naszym rynku? | Wysoka przy dłuższej perspektywie |
| Kto podejmie decyzję o wersji, gdy autor odejdzie? | Wysoka |

Technologia lepsza o 30%, której nikt w zespole nie zna, jest gorsza. Ten rachunek
przegrywa tylko wtedy, gdy znana technologia **nie potrafi** spełnić twardego wymagania.

Kryterium liczbowe: jeżeli utrzymanie ma być prowadzone przy udziale poniżej 30% etatu,
liczba istotnych technologii w systemie nie powinna przekraczać sześciu (język, baza,
framework, hosting, CI, monitoring). Każda dodatkowa to nowe wersje, nowe podatności,
nowa dokumentacja do śledzenia.

### 2. Dojrzałość

| Sygnał | Dobry | Ostrzegawczy |
| --- | --- | --- |
| Wiek | ≥3 lata w produkcji u innych | <1 rok, wersja 0.x |
| Tempo zmian łamiących | Major raz na 1–2 lata z opisem migracji | Zmiany łamiące w wydaniach minor |
| Rozmiar zespołu utrzymującego | Fundacja albo firma z modelem przychodu | Jeden autor, brak sponsora |
| Częstość wydań poprawek | Regularne, z opisem | Cisza >6 miesięcy albo wysyp bez opisu |
| Zgłoszenia | Odpowiedzi w dniach, stary dług zamykany | Setki otwartych bez odpowiedzi |
| Odpowiedzi na trudne pytania | Istnieją poza dokumentacją autora | Tylko materiały marketingowe autora |

Test praktyczny: wyszukaj problem, który na pewno napotkasz (np. „connection pool
exhausted”, „migration lock timeout”). Jeśli znajdujesz opisy z rozwiązaniami — narzędzie
jest używane w produkcji. Jeśli tylko dokumentację i posty startowe — będziesz pierwszy.

### 3. Koszt wyjścia

Najważniejszy wymiar przy decyzjach nieodwracalnych i najczęściej pomijany.

| Poziom | Charakterystyka | Przykłady |
| --- | --- | --- |
| Niski (godziny–dni) | Zamknięte za własnym interfejsem, standardowy format danych | Biblioteka walidacji, logger, klient HTTP, formatter |
| Średni (tygodnie) | Przenika warstwę, ale za portem | ORM, framework HTTP, dostawca poczty, magazyn plików |
| Wysoki (miesiące) | Przenika model danych albo kontrakty | Baza danych, model uwierzytelniania, format identyfikatorów |
| Praktycznie nieodwracalny | Wpisany w dane i integracje osób trzecich | Dostawca płatności, publiczne API, schemat danych historycznych |

Trzy pytania obniżające koszt wyjścia, zadane **przed** wyborem:

1. Czy da się to zamknąć za własnym interfejsem (portem), którego kształt wynika z
   naszej domeny, a nie z API dostawcy?
2. Czy da się wyeksportować dane w formacie czytelnym bez tego narzędzia?
3. Czy istnieje co najmniej jedna realna alternatywa o zbliżonym modelu?

„Nie” na dwa z trzech oznacza, że decyzja jest nieodwracalna — i wymaga ADR-a oraz
większej staranności niż zwykle.

### 4. Licencja

| Licencja | Do użytku komercyjnego | Uwaga |
| --- | --- | --- |
| MIT, Apache-2.0, BSD | Bez ograniczeń | Apache-2.0 dodatkowo obejmuje patenty — bezpieczniejsza |
| MPL-2.0, LGPL | Zwykle tak | Zmiany w samej bibliotece muszą być udostępnione |
| GPL / AGPL | **Uważaj** | AGPL obejmuje udostępnianie przez sieć — użycie w SaaS może wymagać otwarcia kodu |
| BSL / SSPL / „source available” | Sprawdź warunki | Nie są otwartym oprogramowaniem; ograniczają hosting jako usługę; bywają zmieniane wstecz |
| Własnościowa z limitem | Sprawdź progi | Limit przychodu/użytkowników, po którym cena rośnie skokowo |

Ryzyko realne, nie teoretyczne: kilku dostawców infrastruktury zmieniło w ostatnich
latach licencję z otwartej na ograniczoną, wymuszając na użytkownikach migrację lub
zakup. Przy komponencie infrastrukturalnym sprawdź **historię zmian licencji** i model
przychodu właściciela — jeśli nie widać, z czego się utrzymuje, zmiana licencji jest
kwestią czasu.

### 5. Utrzymanie i eksploatacja

| Pytanie | Dlaczego istotne |
| --- | --- |
| Czy to komponent stanowy? | Stan = kopie zapasowe, odtwarzanie, migracje wersji, monitoring. Bezstanowe komponenty są wielokrotnie tańsze |
| Ile pamięci/CPU w spoczynku? | Trzy komponenty po 512 MB zmieniają klasę maszyny |
| Jak wygląda aktualizacja wersji major? | Niektóre wymagają przestoju i przepisania danych |
| Jak to postawić lokalnie? | Komponent bez sensownego środowiska lokalnego spowalnia każdą pracę |
| Co się dzieje, gdy padnie? | Czy system degraduje się łagodnie, czy przestaje działać |
| Czy istnieje wariant zarządzany w UE? | Samodzielne utrzymanie bazy to etat, nie zadanie |

Reguła kosztu operacyjnego: **każdy dodatkowy komponent stanowy to około pół dnia pracy
miesięcznie** (aktualizacje, monitoring, kopie, incydenty). Przy zespole dwuosobowym
cztery takie komponenty zjadają tydzień w miesiącu.

### 6. Ekosystem i integracja

- Czy istnieją biblioteki do rzeczy, których na pewno będziesz potrzebować (typy dla
  twojego języka, integracja z twoim frameworkiem, sterownik dla twojej bazy)?
- Czy narzędzia, których używasz (CI, monitoring, IDE), to obsługują?
- Czy da się to sensownie testować — czy istnieje atrapa, kontener testowy, tryb offline?
- Czy dokumentacja opisuje przypadki błędne, czy tylko happy path?

Brak sensownego sposobu testowania jest wystarczającym powodem odrzucenia. Zależność,
której nie da się zasymulować w testach, wymusza albo testy zależne od sieci
(niedeterministyczne), albo brak testów.

## Nudna technologia jako wartość domyślna

Zasada budżetu innowacji: masz ograniczoną liczbę „żetonów” na technologie, które
zaskoczą cię czymś, o czym nie wiedziałeś. Zespół dwuosobowy ma ich mniej więcej
**jeden**. Wydaj go tam, gdzie decyduje o wartości produktu, a wszystko pozostałe
buduj z rzeczy nudnych, o dobrze znanych trybach awarii.

„Nudne” nie znaczy „stare” ani „gorsze”. Znaczy: **znane tryby awarii**. Wiesz, jak
Postgres się psuje, co pokazuje w logach, jak go odtworzyć i gdzie szukać odpowiedzi.
Nowego narzędzia nie wiesz — i dowiesz się w środku incydentu.

| Warstwa | Nudny domyślny wybór | Kiedy warto wydać żeton |
| --- | --- | --- |
| Baza | PostgreSQL | Skala poza jedną maszyną; dane grafowe; szeregi czasowe w skali TB |
| Język backendu | Ten, który zespół zna | Wymóg wydajnościowy niemożliwy do spełnienia inaczej |
| Kolejka | Tabela w bazie | Przepustowość >1000 zdarzeń/s |
| Wyszukiwanie | Pełnotekstowe w bazie | Rankowanie semantyczne, wielojęzyczność, fasety |
| Wdrożenie | Kontener na maszynie albo PaaS | Wiele środowisk, autoskalowanie, wiele usług |
| Uwierzytelnianie | Gotowy dostawca albo sesje | Nigdy własna kryptografia |
| Frontend | Framework, który zespół zna | Wymóg, którego obecny nie spełnia |

Test przed sięgnięciem po coś nowego: **czy potrafisz wymienić trzy sposoby, w jakie
to zawiedzie na produkcji, i co wtedy zrobisz?** Jeśli nie, nie znasz tego narzędzia
wystarczająco, żeby na nim oprzeć system.

## Katalog kosztownych błędnych wyborów

Wzorce powtarzalne, z faktycznym kosztem.

| Wybór | Uzasadnienie w momencie wyboru | Rzeczywisty koszt |
| --- | --- | --- |
| Baza dokumentowa do danych relacyjnych | „Schemat będzie się zmieniał” | Spójność w aplikacji zamiast w bazie; raportowanie wymaga eksportu; po roku i tak powstaje sztywny schemat, tylko niepilnowany |
| Mikrousługi przy jednym zespole | „Będziemy skalować” | 30–40% czasu na koordynację kontraktów i infrastrukturę; sagi zamiast transakcji; środowisko lokalne przestaje działać |
| Kubernetes do jednej aplikacji | „Standard branżowy” | Manifesty, sieć, uprawnienia, aktualizacje klastra — praca operacyjna bez zysku przy jednym kontenerze |
| Własny system wtyczek | „Będą rozszerzenia” | Wtyczki pisane wyłącznie przez ten sam zespół; API wtyczek ogranicza rdzeń; wersjonowanie dwóch rzeczy zamiast jednej |
| Własna warstwa uwierzytelniania | „Nasze wymagania są nietypowe” | Podatności, których nie wykryjesz; brak MFA, rotacji, blokad; koszt audytu |
| GraphQL przy jednym kliencie | „Elastyczność zapytań” | N+1 w resolverach; limity złożoności; brak cache HTTP; dwie warstwy typów zamiast jednej |
| Rzadka baza (grafowa/kolumnowa) do zwykłej aplikacji | „Pasuje do modelu danych” | Brak ludzi, brak narzędzi, brak odpowiedzi na problemy operacyjne |
| Wielochmurowość od pierwszego dnia | „Uniknięcie przywiązania” | Część wspólna możliwości = brak usług zarządzanych; podwójna konfiguracja; przywiązanie i tak następuje |
| Framework 0.x w rdzeniu | „Nowoczesny, szybki” | Zmiany łamiące w wydaniach minor; przepisanie przy każdej aktualizacji |
| ORM abstrahujący wiele baz | „Odroczenie decyzji o bazie” | Tracisz możliwości konkretnej bazy; decyzja i tak zapada, tylko nieświadomie |
| Monorepo z narzędziem budowania nieznanym zespołowi | „Skalowalna struktura” | Konfiguracja budowania staje się osobnym projektem |
| Serverless do długotrwałych zadań | „Płacimy za użycie” | Limity czasu wykonania, zimne starty, wyczerpanie puli połączeń do bazy |

Wspólny mianownik: uzasadnienie odnosi się do **przyszłej, niepotwierdzonej potrzeby**,
a koszt jest **natychmiastowy i pewny**.

## Jak nie ulec modzie

Sygnały, że oceniasz technologię modą, a nie kryteriami:

| Sygnał | Kontrola |
| --- | --- |
| Uzasadnienie brzmi „tak się teraz robi” | Kto tak robi i przy jakiej skali? Skala źródła zwykle różni się o 3 rzędy wielkości |
| Argument z benchmarku | Jaki profil miał benchmark i czy przypomina nasz? Różnica 3× w mikrobenchmarku bywa 0% w systemie z bazą |
| Argument z popularności repozytorium | Gwiazdki mierzą marketing, nie przydatność ani utrzymanie |
| „Wszyscy odchodzą od X” | Kto konkretnie i dokąd? Zwykle to głośna mniejszość |
| Nie potrafisz wymienić wad wybranej opcji | Nie przeczytałeś o niej wystarczająco |
| Nie potrafisz wymienić zalet odrzuconej | Nie rozważyłeś jej, tylko odrzuciłeś |
| Wybór wygląda dobrze w opisie stanowiska | To jest inżynieria próżności: koszt ponosi firma, korzyść osoba |

Kontrola najprostsza i najskuteczniejsza: **napisz ADR z trzema alternatywami**
(`references/engineering-core/references/adr.md`). Wymóg wypisania prawdziwych zalet odrzucanych
opcji i prawdziwych wad wybranej ujawnia decyzję modową szybciej niż jakakolwiek dyskusja.

Druga kontrola: **odwróć obowiązek dowodu**. Domyślnie zostajemy przy tym, co znamy.
Nowa technologia musi udowodnić przewagę, nie odwrotnie. Sformułuj to jako pytanie:
„jakiego twardego wymagania nie spełnia to, co już mamy?”. Brak odpowiedzi kończy temat.

## Procedura decyzyjna

1. **Sformułuj wymaganie, nie rozwiązanie.** Nie „potrzebujemy Redisa”, tylko
   „odczyt listy zgłoszeń ma się mieścić w 200 ms przy 50 tys. rekordów”.
2. **Sprawdź, czy istniejący stos tego nie spełnia.** W ~70% przypadków spełnia —
   po dodaniu indeksu, poprawieniu zapytania albo użyciu funkcji, o której nie wiedziałeś.
3. **Wypisz 2–4 kandydatów**, w tym zawsze „zostajemy przy tym, co mamy”.
4. **Oceń wg sześciu wymiarów.** Wymiar 1 (zespół) może zamknąć sprawę od razu.
5. **Sprawdź koszt wyjścia** i zaprojektuj port, który go obniża.
6. **Zbuduj kolec** — najmniejszy działający fragment realnego przypadku użycia,
   z połączeniem do bazy i obsługą błędu. Nie „hello world” z dokumentacji.
   Ogranicz do 1–2 dni i wyrzuć kod po ocenie.
7. **Napisz ADR** (`references/engineering-core/references/adr.md`), jeśli koszt wyjścia jest średni
   lub wyższy.
8. **Zapisz warunek rewizji** — próg, przy którym wracasz do decyzji.

Krok 6 wykrywa większość problemów, których nie widać z dokumentacji: brak typów,
niejasną obsługę błędów, brak sposobu testowania, złe zachowanie przy zerwaniu
połączenia, konieczność obejść.

## Ocena zależności przed dodaniem

Przed każdym `npm install` / `pip install` czterech odpowiedzi:

1. **Co to robi i czy potrzebuję całości?** Paczka do jednej funkcji, którą napiszesz
   w 20 linijkach, to zależność z ryzykiem podmiany za darmo.
2. **Kto to utrzymuje?** Data ostatniego wydania, liczba osób z prawem publikacji,
   czy istnieje sponsor.
3. **Ile ciągnie za sobą?** Sprawdź drzewo zależności przechodnich. Paczka z 60
   zależnościami to 60 punktów ryzyka i 60 rzeczy do aktualizowania.
4. **Jaka licencja?** Sprawdź także zależności przechodnie — AGPL kilka poziomów w dół
   dotyczy ciebie tak samo.

Sygnały ostrzegawcze: brak repozytorium źródłowego, brak historii wydań, ostatnie
wydanie sprzed >2 lat przy aktywnym ekosystemie, nazwa łudząco podobna do popularnej
paczki (podszywanie się), skrypt instalacyjny wykonujący kod (`postinstall`).

Blokada w CI zamiast dyscypliny: `npm audit --audit-level=high`, `pip-audit`,
`osv-scanner`, plus przypięte wersje (lockfile w repozytorium, zawsze `npm ci`).

## Podsumowanie w jednym akapicie

Wybieraj to, co zespół zna, chyba że to nie spełnia twardego wymagania. Ograniczaj
liczbę komponentów stanowych. Zamykaj wszystko, co da się zamknąć, za własnym
interfejsem. Zapisuj decyzje nieodwracalne w ADR z prawdziwymi alternatywami. Nowość
uzasadniaj wymaganiem, nie ciekawością. Koszt wyjścia licz przed wejściem.
