# e-Doręczenia

> Stan na: 2026-08-04. Źródła: https://www.gov.pl/web/e-doreczenia/harmonogram,
> https://www.gov.pl/web/e-doreczenia/interfejsy-api,
> https://www.gov.pl/web/e-doreczenia/integracja-uslugi-e-doreczen-z-systemami-klasy-ezd,
> https://www.gov.pl/web/e-doreczenia/pytania-i-odpowiedzi,
> https://www.gov.pl/web/e-doreczenia/nowe-funkcjonalnosci-w-e-doreczeniach2,
> https://edoreczenia.poczta-polska.pl/wp-content/uploads/2025/09/COI-Projekt-Techniczny-UA-API_5.27-1.pdf,
> https://www.sukcescr.pl/blog/wygaszanie-epuap-do-2028-r-harmonogram-i-co-przygotowac-juz-teraz/.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Model pojęciowy — co jest czym

| Skrót | Rozwinięcie | Znaczenie praktyczne |
| --- | --- | --- |
| PURDE | Publiczna usługa rejestrowanego doręczenia elektronicznego | Doręczenie „cyfrowe za cyfrowe”. Wysyłający i odbierający mają ADE. Państwowa, świadczy operator wyznaczony |
| KURDE | Kwalifikowana usługa rejestrowanego doręczenia elektronicznego | To samo skutkiem prawnym, ale świadczona komercyjnie przez kwalifikowanego dostawcę usług zaufania z listy krajowej |
| PUH | Publiczna usługa hybrydowa | Nadawca wysyła elektronicznie, operator drukuje i doręcza papierowo. Tylko dla podmiotów publicznych jako nadawców |
| ADE | Adres do doręczeń elektronicznych | Identyfikator w postaci `AE:PL-XXXXX-XXXXX-YYYYY-ZZ`. **To nie jest adres e-mail** i nie da się na niego wysłać SMTP |
| BAE | Baza Adresów Elektronicznych | Rejestr publiczny wszystkich ADE. Odpytywany przez SE API |
| ADE + skrzynka | Skrzynka do doręczeń elektronicznych | ADE jest adresem, skrzynka jest miejscem przechowywania. Aktywacja skrzynki jest odrębną czynnością od uzyskania ADE |

Operator wyznaczony: **Poczta Polska S.A.** (źródło: gov.pl/web/e-doreczenia/pytania-i-odpowiedzi).

Dowody: przy przyjęciu wiadomości do wysłania system generuje **dowód wysłania**, przy doręczeniu
**dowód otrzymania**. Oba są opatrzone kwalifikowaną pieczęcią elektroniczną, co czyni je dowodem
w rozumieniu przepisów. W obiegu praktycznym i w starszej dokumentacji funkcjonują skróty EPO/EPD
(elektroniczne potwierdzenie odbioru / doręczenia) — `[niepotwierdzone: czy obecna dokumentacja MC
nadal używa oznaczeń EPO/EPD, czy wyłącznie „dowód wysłania”/„dowód otrzymania”; sprawdź w Projekcie
Technicznym UA API]`.

## PURDE vs KURDE — kiedy która

PURDE jest bezpłatna dla podmiotu niepublicznego w zakresie odbierania i wysyłania do podmiotów
publicznych; wysyłka do innych podmiotów niepublicznych jest płatna według cennika operatora
wyznaczonego. KURDE kupujesz u kwalifikowanego dostawcy (patrz
`references/engineering-core/06-integracje-pl-eu/references/podpis-elektroniczny.md`, lista NCCert)
— sens ma wtedy, gdy potrzebujesz SLA, integracji z własnym systemem na warunkach umownych albo
obsługi dużego wolumenu. Skutek doręczenia jest w obu przypadkach ten sam.

Dostawcy z listy NCCert świadczący kwalifikowaną usługę rejestrowanego doręczenia elektronicznego
(stan z rejestru NCCert): PWPW S.A., Asseco Data Systems S.A., KFJ Inwestycje Sp. z o.o.,
Poczta Polska S.A., Autenti Sp. z o.o.

## Harmonogram obowiązku

Źródło: https://www.gov.pl/web/e-doreczenia/harmonogram (odczyt 2026-08-04).

| Data | Grupa |
| --- | --- |
| 1.01.2025 | Organy administracji rządowej i obsługujące je jednostki budżetowe; pozostałe podmioty publiczne niewymienione osobno |
| 1.01.2025 | **Zawody zaufania publicznego**: adwokat, radca prawny, doradca podatkowy, rzecznik patentowy, notariusz |
| 1.01.2025 | Podmioty **rejestrujące się w KRS** od tego dnia (obowiązek powstaje z chwilą wpisu) |
| 1.04.2025 | Podmioty **wpisane do KRS przed 1.01.2025** (spółki istniejące) |
| 1.07.2025 | Podmioty CEIDG dokonujące zmiany wpisu po 30.06.2025 |
| **1.10.2026** | **Wszystkie pozostałe podmioty CEIDG** (zarejestrowane do 31.12.2024) |
| 31.12.2026 | Służby bezpieczeństwa wewnętrznego i obrony, w tym CBA |
| 1.10.2029 | JST w zakresie publicznej usługi hybrydowej (PUH) |

Konsekwencja dla kancelarii: adwokat/radca prawny miał obowiązek od **1.01.2025** — to jest już
stan zastany, nie plan. Konsekwencja dla spółek KRS: nowe od **1.01.2025**, istniejące od
**1.04.2025**. Jednoosobowe działalności „stare” wchodzą **1.10.2026** — to najbliższy termin,
który realnie dotyczy klientów budowanego systemu.

## ePUAP — wygaszanie

- Od **1.01.2026** e-Doręczenia zastąpiły ePUAP jako podstawowy kanał komunikacji podmiotów
  publicznych z podmiotami niepublicznymi; ustaje fikcja doręczenia przez ePUAP wobec obywateli
  i firm.
- Komunikacja **między podmiotami publicznymi** przez ePUAP ma zostać wyłączona **1.01.2028** —
  to wynika z **projektu** nowelizacji ustawy o doręczeniach elektronicznych opublikowanego przez
  Ministerstwo Cyfryzacji **8.07.2026**. `[niepotwierdzone: czy projekt stał się ustawą; sprawdź
  https://legislacja.rcl.gov.pl oraz gov.pl/web/e-doreczenia/akty-prawne przed powołaniem się na
  datę 1.01.2028]`
- Przepis przejściowy w zakresie PUH dla JST sięga **30.09.2029**.

Wniosek projektowy: **nie buduj nowych integracji na ePUAP/SkrytkaESP**. Jeśli istniejący system
korzysta z ePUAP, planuj migrację na UA API, nie rozbudowę adaptera ePUAP.

## Architektura systemu

Trzy warstwy, które trzeba rozróżnić przy projektowaniu integracji:

1. **BAE** — rejestr adresów. Odpytywany przez **SE API** (Search Engine API). Nie przechowuje
   wiadomości, tylko odpowiada „czy ten NIP/PESEL/KRS ma ADE i jaki”.
2. **Skrzynka/UA** — magazyn wiadomości i operacje na nich. Obsługiwana przez **UA API**
   (User Agent API): tworzenie roboczych, wysyłka, listowanie, odczyt, pobieranie załączników,
   usuwanie.
3. **Operator** — realizuje doręczenie i wystawia dowody. Dla integratora jest przezroczysty:
   dowody pojawiają się jako obiekty powiązane z wiadomością.

## Interfejsy API — wersje obowiązujące

Źródło: https://www.gov.pl/web/e-doreczenia/interfejsy-api (odczyt 2026-08-04).

| API | Wersja obowiązująca na INT i PROD | Do czego |
| --- | --- | --- |
| UA API 3 | `3.0.8` (paczka `uaapi_3.0.8.2.zip`) | Przygotowanie, wysyłanie, odbieranie, magazynowanie wiadomości |
| SE API 4 | `4.0.0.1` | Wyszukiwanie ADE w BAE |
| SE API 3 | `3.0.6` | j.w., wersja starsza, nadal wspierana |
| SE API 2 | `2.0.4` | j.w., wersja najstarsza, nadal wspierana |

Dokument źródłowy: „COI — Projekt Techniczny UA API” (wersja 5.27, wrzesień 2025), publikowany na
https://edoreczenia.poczta-polska.pl/wp-content/uploads/2025/09/COI-Projekt-Techniczny-UA-API_5.27-1.pdf

Specyfikacja UA API jest wydawana jako **OpenAPI (YAML)** — generuj klienta z YAML-a, nie pisz
ręcznie.

## Operacje UA API

Wzorzec ścieżek (z Projektu Technicznego UA API 5.27):

| Operacja | Metoda i ścieżka |
| --- | --- |
| Wysłanie wiadomości roboczej | `POST /{eDeliveryAddress}/drafts/send` |
| Wysłanie wiadomości | `POST /{eDeliveryAddress}/messages` |
| Lista wiadomości | `GET /{eDeliveryAddress}/messages` |
| Odczyt wiadomości | `GET /{eDeliveryAddress}/messages/{messageId}` |
| Usunięcie wiadomości | `DELETE /{eDeliveryAddress}/messages/{messageId}` |
| Pobranie załącznika | `GET /{eDeliveryAddress}/messages/{messageId}/attachments/{attachmentId}` |

`{eDeliveryAddress}` w ścieżce to ADE skrzynki, w której kontekście działasz — to nie jest
identyfikator techniczny nadawany przez API, tylko adres z BAE.

`[niepotwierdzone: pełne adresy bazowe (host) środowisk INT i PROD dla UA API — Projekt Techniczny
ich nie publikuje, są przekazywane po nadaniu dostępu do INT; potwierdź w
https://int.edoreczenia.gov.pl/dokumentacja po uzyskaniu dostępu]`

## Uwierzytelnianie

Projekt Techniczny UA API 5.27 wskazuje trzy warstwy:

- **Osoby fizyczne** — uwierzytelnianie przez **Węzeł Krajowy, protokół SAML** (login.gov.pl:
  profil zaufany, e-dowód, bankowość, aplikacja mObywatel).
- **Systemy klasy EZD / systemy zewnętrzne** — uwierzytelnianie **certyfikatem uwierzytelnienia
  witryny internetowej** (mTLS certyfikatem po stronie klienta).
- **Autoryzacja na poziomie API i zasobów** — **OAuth 2.0 + UMA 2.0**. UMA jest tu istotne: ten
  sam podmiot może mieć wiele skrzynek i wielu pełnomocników, a UMA modeluje „kto ma dostęp do
  której skrzynki” niezależnie od tego, kto się zalogował.

Praktycznie: aplikacja serwerowa nie loguje się „jako użytkownik”. Rejestruje system zewnętrzny
przy skrzynce (Załącznik 1c „Instrukcja dodania systemu zewnętrznego”), dostaje poświadczenia
i działa w trybie machine-to-machine.

## Środowisko integracyjne INT

Procedura dostępu (gov.pl/web/e-doreczenia/integracja-uslugi-e-doreczen-z-systemami-klasy-ezd):

1. Zapoznaj się z dokumentacją publikowaną na stronie MC.
2. Wypełnij formularz zgłoszenia integratora.
3. Wyślij na **test.edoreczenia@cyfra.gov.pl**.
4. Po nadaniu dostępu dokumentacja pod **https://int.edoreczenia.gov.pl/dokumentacja**.

Dokumenty, które faktycznie są potrzebne (nazwy z portalu):
- Załącznik 1a — Instrukcja integracji dla podmiotów i integratorów EZD ze środowiskiem INT
- Załącznik 1c — Instrukcja dodania systemu zewnętrznego (rozszerzona)
- Instrukcja integracji EZD ze środowiskiem PROD dla podmiotów zewnętrznych

Zgłaszanie incydentów: **https://pomoc.coi.gov.pl/** (ITSM Atmosfera). Nie mailem do MC — zgłoszenia
mailowe nie mają numeru i giną.

## Limity i parametry operacyjne

Zmiany wprowadzone przez operatora wyznaczonego (komunikat MC z 14.08.2024):

| Parametr | Wartość |
| --- | --- |
| Rozmiar wiadomości z załącznikami | **500 MB** (wcześniej 15 MB) |
| Liczba adresatów jednej wiadomości | **1000** — tylko podmioty publiczne (wcześniej 15) |
| Dostępność przesyłki dla adresata | **180 dni** |

Konsekwencja architektoniczna: 500 MB to za dużo na trzymanie w pamięci. Zaplanuj strumieniowe
pobieranie i zapis załączników do storage, nie `response.content` w całości. Konsekwencja prawna:
180 dni to nie jest archiwum — jeśli system ma stanowić dowód w sprawie, musi pobierać i trwale
przechowywać wiadomość **razem z dowodami**, bo po 180 dniach zniknie ze skrzynki.

`[niepotwierdzone: limit liczby załączników w jednej wiadomości oraz limit pojedynczego pliku —
komunikat MC podaje tylko limit łączny 500 MB; sprawdź w dokumentacji UA API na
int.edoreczenia.gov.pl]`

## Praktyczne konsekwencje dla kancelarii i spółek

**Kancelaria (adwokat, radca prawny, notariusz, doradca podatkowy)** — obowiązek od 1.01.2025.
Skutki, które trzeba obsłużyć w systemie:
- Doręczenie na ADE wywołuje bieg terminów procesowych. System musi rejestrować **datę z dowodu
  otrzymania**, a nie datę odczytania wiadomości przez pracownika.
- Wiadomość i oba dowody trzeba pobrać i zarchiwizować niezależnie od skrzynki (180 dni).
- Trzeba rozdzielić „wpływ do kancelarii” od „doręczenia stronie” — jeśli kancelaria odbiera na
  własne ADE korespondencję w sprawie klienta, dowód dotyczy pełnomocnika.

**Spółka KRS** — obowiązek od 1.01.2025 (nowe) lub 1.04.2025 (istniejące). Skutki:
- ADE spółki jest w BAE i jest publiczne — organy będą go używać domyślnie, niezależnie od tego,
  czy ktoś w spółce zagląda do skrzynki.
- Brak odbioru nie wstrzymuje skutku doręczenia. Monitoring skrzynki musi być procesem, nie
  czynnością.

**Sprawdzanie, czy kontrahent ma ADE** — przed wysyłką zapytaj SE API. Jeśli adresat nie ma ADE,
podmiot publiczny użyje PUH; podmiot niepubliczny musi wysłać papierowo. Nie zakładaj, że każdy
NIP ma ADE — CEIDG „stare” wchodzą dopiero 1.10.2026.

## Typowe błędy integracyjne

| Błąd | Konsekwencja |
| --- | --- |
| Traktowanie ADE jak adresu e-mail i próba SMTP | Nic nie zostanie doręczone; ADE nie jest routowalne pocztowo |
| Poleganie na obecności wiadomości w skrzynce jako archiwum | Po 180 dniach wiadomość znika, dowód doręczenia przepada |
| Liczenie terminu od odczytania wiadomości w UI | Termin biegnie od doręczenia z dowodu otrzymania — błąd o kilka dni |
| Wdrożenie na PROD bez przejścia przez INT | Brak poświadczeń dla systemu zewnętrznego na PROD; procedura PROD jest odrębna od INT |
| Budowanie na SE API 2 dla nowego projektu | Wersja utrzymywana kompatybilnościowo; nowy kod pisz na SE API 4 (4.0.0.1) |
| Wczytywanie 500 MB załącznika do pamięci | OOM przy kilku równoległych pobraniach |

## Co potwierdzić przed wdrożeniem

1. Aktualne wersje UA API i SE API na https://www.gov.pl/web/e-doreczenia/interfejsy-api — MC
   podbija je bez zapowiedzi.
2. Adresy bazowe INT/PROD po uzyskaniu dostępu.
3. Status nowelizacji wygaszającej ePUAP dla podmiotów publicznych (data 1.01.2028).
4. Czy klient jest podmiotem publicznym — od tego zależy dostępność PUH i limit 1000 adresatów.
