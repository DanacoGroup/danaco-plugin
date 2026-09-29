# Integracje z platformami PL i UE — przegląd modułu

Moduł obejmuje integracje z polskimi i unijnymi platformami państwowymi oraz finansowymi
i tłumaczenie maszynowe w aplikacji. Karty pogłębione wymienia tabela
„Mapa plików referencyjnych” poniżej, a wszystkie moduły `references/engineering-core/` —
`references/engineering-core/spis.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Obszar, w którym model **najczęściej zmyśla**: daty wejścia obowiązków, adresy endpointów,
wersje schem, nazwy metod API. Dokumentacja jest rozproszona po gov.pl, GitHubie ministerstw
i portalach operatorów, a terminy były wielokrotnie przesuwane.

## Zastrzeżenie — obszar szybko zmienny

Wszystkie fakty w tym module mają **datę stanu 2026-08-04** i URL źródła. Przed jakimkolwiek
wdrożeniem produkcyjnym **potwierdź u źródła**:

- Terminy KSeF przesuwano trzykrotnie (2023 → 1.07.2024 → 1.02.2026).
- Ministerstwo Cyfryzacji podbija wersje UA API i SE API e-Doręczeń bez zapowiedzi.
- Ministerstwo Finansów zmienia dokumentację KSeF w repozytorium GitHub bez wersjonowania
  semantycznego.
- PSD3/PSR nie zostały jeszcze opublikowane w Dz.Urz. UE — daty stosowania są liczone
  od zdarzenia, które jeszcze nie nastąpiło.
- Plany cenowe DeepL zostały przebudowane (Free i Pro wycofane).

**Nigdy nie podawaj klientowi daty obowiązku prawnego bez sprawdzenia jej w dniu odpowiedzi.**
Błąd o kwartał w dacie obowiązku KSeF albo e-Doręczeń to błąd kosztujący kary.

## Kiedy wczytać ten moduł

- „Podłącz system do e-Doręczeń”, „zintegruj z KSeF”, „chcemy inicjować przelewy z aplikacji”.
- Trzeba ustalić, **od kiedy** dany podmiot ma obowiązek (KSeF, e-Doręczenia) i co z tego wynika
  technicznie.
- Trzeba dobrać sposób uwierzytelnienia wobec instytucji: certyfikat kwalifikowany, pieczęć,
  token, profil zaufany, mTLS.
- Trzeba pobrać dane z rejestru publicznego (KRS, CEIDG, REGON, biała lista, VIES, CRBR).
- Trzeba przyjąć płatność online i **poprawnie zweryfikować webhook**.
- Trzeba dodać tłumaczenie maszynowe i rozstrzygnąć kwestię poufności danych.

**Nie używaj gdy:** pytanie dotyczy ogólnej architektury integracji (retry, kolejki, idempotencja
jako wzorzec) — to `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`. Ani gdy
chodzi o konfigurację serwera pocztowego albo SMTP — to
`references/engineering-core/05-uslugi-sieciowe/przeglad.md` (uwaga: **e-Doręczenia to nie poczta
e-mail**, ADE nie jest adresem SMTP).

## Granice

| Temat | Materiał właściwy |
| --- | --- |
| Serwery pocztowe, SMTP, DNS, TLS dla poczty | `references/engineering-core/05-uslugi-sieciowe/przeglad.md` |
| Wzorce integracji, granice modułów, kontrakt API, ADR | `../architektura-i-dokumentacja/references/engineering-core/przeglad.md` |
| Kod Pythona: klienci HTTP, walidacja XML, kolejki, SQLAlchemy | `references/engineering-core/02-python-backend-dane/przeglad.md` |
| Testy integracyjne, CI, wdrożenia, obserwowalność | `references/engineering-core/07-debug-testy-deploy/przeglad.md` |

Podział: tutaj **co jest po drugiej stronie i jakie ma reguły**, tam **jak to napisać**. „Jak
zbudować kolejkę ponowień” —
`../architektura-i-dokumentacja/references/engineering-core/przeglad.md`. „Ile dni roboczych ma
podatnik na dosłanie faktury z trybu offline24” — tutaj.

## Mapa platform

| Platforma | Status obowiązku (stan 2026-08-04) | Plik referencyjny | Weryfikacja |
| --- | --- | --- | --- |
| **e-Doręczenia** | Obowiązek czynny: zawody zaufania publicznego i nowe KRS od 1.01.2025, istniejące KRS od 1.04.2025. **CEIDG „stare” od 1.10.2026** | `references/engineering-core/06-integracje-pl-eu/references/edoreczenia.md` | 2026-08-04 |
| **ePUAP** | Wygaszany. Od 1.01.2026 zastąpiony przez e-Doręczenia w kontakcie z podmiotami niepublicznymi | `references/engineering-core/06-integracje-pl-eu/references/edoreczenia.md` | 2026-08-04 |
| **KSeF** | Obowiązek czynny: > 200 mln zł obrotu 2024 → 1.02.2026; pozostali → 1.04.2026; najmniejsi → 1.01.2027. **Odbieranie faktur — wszyscy od 1.02.2026**. Kary od 1.01.2027 | `references/engineering-core/06-integracje-pl-eu/references/ksef.md` | 2026-08-04 |
| **PSD2 / PolishAPI** | Obowiązuje. PolishAPI 3.0.1 / 2.1.4 (17.06.2025) | `references/engineering-core/06-integracje-pl-eu/references/pisp-psd2.md` | 2026-08-04 |
| **PSD3 / PSR** | Teksty uzgodnione 23.04.2026, **przed publikacją w Dz.Urz. UE**. Stosowanie +21 mies., VoP +27 mies. Realnie 2028 | `references/engineering-core/06-integracje-pl-eu/references/pisp-psd2.md` | 2026-08-04 |
| **eIDAS 2 / EUDI Wallet** | Rozporządzenie 2024/1183 w mocy od 20.05.2024. Portfele: **koniec 2026**. Obowiązek akceptacji: **koniec 2027**. PL: pilotaż w mObywatelu koniec 2026 | `references/engineering-core/06-integracje-pl-eu/references/podpis-elektroniczny.md` | 2026-08-04 |
| **Podpis kwalifikowany, pieczęć, QTSA** | Obowiązuje. 8 dostawców w rejestrze NCCert | `references/engineering-core/06-integracje-pl-eu/references/podpis-elektroniczny.md` | 2026-08-04 |
| **Bramki płatnicze (P24, PayU, Tpay, BLIK)** | Bez obowiązku prawnego; obowiązki po stronie regulaminu, zwrotów i reklamacji | `references/engineering-core/06-integracje-pl-eu/references/platnosci.md` | 2026-08-04 |
| **Express Elixir** | Usługa KIR, 24/7, limit standardowy 100 000 zł | `references/engineering-core/06-integracje-pl-eu/references/platnosci.md` | 2026-08-04 |
| **Rejestry (KRS, CEIDG, biała lista, VIES, REGON, CRBR)** | Dostępne; biała lista rodzi obowiązek należytej staranności przy ≥ 15 000 zł | `references/engineering-core/06-integracje-pl-eu/references/rejestry-api.md` | 2026-08-04 |
| **e-Urząd Skarbowy, S24/PRS** | **Brak publicznego API dla integratorów** | `references/engineering-core/06-integracje-pl-eu/references/rejestry-api.md` | 2026-08-04 |
| **Tłumaczenie maszynowe** | Bez obowiązku; ograniczenia z RODO i tajemnicy zawodowej | `references/engineering-core/06-integracje-pl-eu/references/tlumaczenie.md` | 2026-08-04 |

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
| --- | --- | --- |
| `references/engineering-core/06-integracje-pl-eu/references/edoreczenia.md` | PURDE/KURDE/PUH/ADE/BAE, dowody wysłania i otrzymania, pełny harmonogram obowiązku, wygaszanie ePUAP, UA API 3.0.8 i SE API 4.0.0.1, uwierzytelnianie (Węzeł Krajowy SAML, mTLS, OAuth2+UMA), procedura dostępu do INT, limity 500 MB / 1000 adresatów / 180 dni | Zadanie dotyczy korespondencji urzędowej, doręczeń, terminów procesowych, migracji z ePUAP |
| `references/engineering-core/06-integracje-pl-eu/references/ksef.md` | Harmonogram z progami, przepisy przejściowe do 31.12.2026, kary z art. 106ni ustawy o VAT, adresy środowisk API v2, FA(3), format numeru KSeF, uwierzytelnianie challenge–response, certyfikaty KSeF, tryby offline24/awaryjny | Zadanie dotyczy faktur, e-fakturowania, integracji księgowej |
| `references/engineering-core/06-integracje-pl-eu/references/pisp-psd2.md` | Role AISP/PISP/CAF, MIP vs KIP (kwoty, limity, czasy postępowania KNF), QWAC/QSealC i wydawcy w PL, PolishAPI, przebieg PIS z SCA, agregator vs własna licencja, stan PSD3/PSR | Zadanie dotyczy inicjowania płatności z rachunku, dostępu do danych bankowych, licencji |
| `references/engineering-core/06-integracje-pl-eu/references/podpis-elektroniczny.md` | SES/AdES/QES, podpis zaufany vs osobisty vs kwalifikowany, rejestr NCCert, pieczęć, XAdES/PAdES/CAdES/ASiC, poziomy B-B/B-T/B-LT/B-LTA, DSS 6.4, znacznik czasu RFC 3161, harmonogram EUDI Wallet | Zadanie dotyczy podpisywania, walidacji podpisu, formy pisemnej, tożsamości |
| `references/engineering-core/06-integracje-pl-eu/references/platnosci.md` | P24 (OpenAPI 1.0.17, sign SHA-384, harmonogram ponowień), Tpay (JWS, X-JWS-Signature), PayU (OpenPayu-Signature, IP), BLIK, Stripe w PL, Express Elixir, obowiązki prawne (regulamin, zwroty, reklamacje, D+1) | Zadanie dotyczy przyjmowania płatności, webhooków, zwrotów |
| `references/engineering-core/06-integracje-pl-eu/references/rejestry-api.md` | Adresy, uwierzytelnienie, limity i formaty dla KRS, CEIDG v3, białej listy VAT, VIES REST, GUS BIR (SOAP), CRBR; wzorce weryfikacji kontrahenta i buforowania | Zadanie dotyczy pobierania danych o podmiotach, weryfikacji kontrahenta, KYC/AML |
| `references/engineering-core/06-integracje-pl-eu/references/tlumaczenie.md` | DeepL API (adresy, limity, glosariusze, plany), Google Cloud Translation (cennik), LLM vs silnik MT, tłumaczenie dokumentów, RODO i tajemnica zawodowa, modele lokalne | Zadanie dotyczy tłumaczenia w aplikacji, wielojęzyczności, poufności tekstów |

## Skróty, które trzeba rozwijać poprawnie

Model regularnie myli te pojęcia. Pomyłka zmienia odpowiedź merytorycznie.

| Skrót | Rozwinięcie | Czym NIE jest |
| --- | --- | --- |
| **ADE** | Adres do doręczeń elektronicznych, format `AE:PL-XXXXX-XXXXX-YYYYY-ZZ` | Nie jest adresem e-mail ani skrytką ePUAP |
| **PURDE** | Publiczna usługa rejestrowanego doręczenia elektronicznego | Nie jest usługą komercyjną; świadczy operator wyznaczony |
| **KURDE** | Kwalifikowana usługa rejestrowanego doręczenia elektronicznego | Nie jest „lepszą” wersją PURDE — skutek prawny ten sam, inny dostawca |
| **PUH** | Publiczna usługa hybrydowa (elektronicznie → papierowo) | Nie jest dostępna dla podmiotu niepublicznego jako nadawcy |
| **BAE** | Baza Adresów Elektronicznych | Nie przechowuje wiadomości, tylko adresy |
| **FA(3)** | Struktura logiczna e-faktury obowiązująca od 1.02.2026 | Nie jest wersją API — API ma osobne wersjonowanie (`/v2`) |
| **Numer KSeF** | 35 znaków, `NIP-RRRRMMDD-12znaków-suma` | Nie jest numerem faktury nadanym przez wystawcę |
| **AISP** | Dostawca usługi dostępu do informacji o rachunku | Nie może inicjować płatności |
| **PISP** | Dostawca usługi inicjowania płatności | Nie przyjmuje środków; pieniądze idą płatnik → odbiorca |
| **QWAC** | Kwalifikowany certyfikat uwierzytelniania witryny (mTLS) | Nie służy do pieczętowania treści — do tego jest QSealC |
| **QSealC** | Kwalifikowany certyfikat pieczęci (niezaprzeczalność treści) | Nie zestawia kanału TLS |
| **QES** | Kwalifikowany podpis elektroniczny | Podpis zaufany i podpis osobisty **nie są** QES |
| **QTSA** | Kwalifikowany dostawca znacznika czasu | Nie jest tym samym co urząd certyfikacji |
| **B-LTA** | Poziom podpisu z archiwalnymi znacznikami czasu | Nie da się go dodać po wygaśnięciu materiału walidacyjnego |
| **BIR** | Baza Internetowa REGON (usługa GUS) | Nie jest REST-em; to SOAP 1.2 z WS-Addressing |
| **CRBR** | Centralny Rejestr Beneficjentów Rzeczywistych | Nie jest częścią KRS |

## Kalendarz terminów 2026–2029

Uporządkowany chronologicznie, bo w rozmowie z klientem liczy się „co nas czeka”, nie „co jest
w którym rejestrze”.

| Data | Zdarzenie | Kogo dotyczy |
| --- | --- | --- |
| 1.01.2026 | e-Doręczenia zastępują ePUAP w kontakcie z podmiotami niepublicznymi | wszyscy |
| 1.02.2026 | KSeF: obowiązek **wystawiania** dla podatników > 200 mln zł obrotu 2024 | duzi podatnicy |
| 1.02.2026 | KSeF: obowiązek **odbierania** faktur | **wszyscy podatnicy** |
| 1.02.2026 | FA(3) zastępuje FA(2) | wszyscy w KSeF |
| 1.04.2026 | KSeF: obowiązek wystawiania dla pozostałych | większość firm |
| **1.10.2026** | e-Doręczenia: obowiązek dla podmiotów CEIDG zarejestrowanych do 31.12.2024 | JDG „stare” |
| koniec 2026 | eIDAS 2: państwa muszą udostępnić portfel EUDI; PL — pilotaż w mObywatelu | państwa UE |
| 31.12.2026 | e-Doręczenia: obowiązek dla służb bezpieczeństwa i obrony (w tym CBA) | służby |
| 31.12.2026 | Koniec przepisów przejściowych KSeF: kasy rejestrujące, brak kar | wszyscy |
| **1.01.2027** | KSeF: początek stosowania kar (art. 106ni ustawy o VAT) | wszyscy |
| 1.01.2027 | KSeF: obowiązek podawania numeru KSeF w tytule przelewu | wszyscy |
| 1.01.2027 | KSeF: obowiązek wystawiania dla najmniejszych (≤ 450 zł / 10 000 zł mies.) | mikro |
| koniec 2027 | eIDAS 2: obowiązek akceptacji portfela EUDI przez podmioty zobowiązane | banki, telekomy, VLOP |
| 1.01.2028 | ePUAP: planowane wyłączenie komunikacji między podmiotami publicznymi | podmioty publiczne |
| ~2028 | PSD3: termin transpozycji (21 mies. od publikacji w Dz.Urz. UE) | instytucje płatnicze |
| 1.10.2029 | e-Doręczenia: JST w zakresie PUH | JST |

Daty po 2026 r. są **planami**, nie stanem zastanym — sprawdzaj przed powołaniem się na nie.

## Trzy najczęstsze zadania — ścieżka skrócona

### „Podłącz nas do e-Doręczeń”

1. Ustal, czy klient jest podmiotem publicznym (to determinuje PUH i limit 1000 adresatów).
2. Sprawdź, czy klient ma już ADE i **aktywowaną skrzynkę** — to dwie różne rzeczy.
3. Zdecyduj: integracja przez UA API (własny system) czy korzystanie z gotowej skrzynki
   (przeglądarka). API ma sens dopiero przy wolumenie albo przy potrzebie archiwizacji w systemie.
4. Złóż wniosek o dostęp do INT (`test.edoreczenia@cyfra.gov.pl`) — to jest **ścieżka krytyczna
   harmonogramu**, liczona w tygodniach.
5. Zaprojektuj: pobieranie wiadomości + **pobieranie i trwałe zapisywanie dowodów**, bo skrzynka
   trzyma przesyłkę tylko 180 dni.
6. Zaprojektuj rejestrowanie daty doręczenia z dowodu otrzymania jako źródła biegu terminów —
   nie daty odczytania w interfejsie.

Szczegóły: `references/engineering-core/06-integracje-pl-eu/references/edoreczenia.md`.

### „Zintegruj nas z KSeF”

1. Ustal, od kiedy klient ma obowiązek **wystawiania**. Obowiązek **odbierania** ma już od
   1.02.2026 niezależnie od odpowiedzi.
2. Wybierz metodę uwierzytelnienia: pieczęć kwalifikowana organizacji (najtrwalsze dla systemu),
   token KSeF (najprostsze) albo certyfikat KSeF.
3. Uruchom na `api-test.ksef.mf.gov.pl`, potem `api-demo`, potem produkcja. Klucze publiczne są
   **per środowisko**.
4. Zbuduj walidację XSD FA(3) lokalnie, przed wysyłką.
5. Zbuduj kolejkę dosyłkową dla `offline24` z kontrolą terminu D+1 — to nie jest opcja.
6. Zaplanuj przechowywanie numeru KSeF (35 znaków) i UPO.

Szczegóły: `references/engineering-core/06-integracje-pl-eu/references/ksef.md`.

### „Weryfikuj kontrahentów przed przelewem”

1. GUS BIR (SOAP) — dane podstawowe. Limit hojny, można odpytywać szeroko.
2. Biała lista VAT, metoda `check` — rachunek bankowy. 5000 podmiotów/dobę.
   **Zapisz klucz weryfikacyjny**, nie tylko wynik TAK/NIE.
3. KRS `OdpisAktualny` — reprezentacja, jeśli w KRS. Uwaga na `stanZDnia` (bywa sprzed tygodni).
4. VIES — tylko przy WDT/WNT. Wcześniej sprawdź `check-status` dla kraju.
5. CRBR — tylko gdy wymaga tego AML.

Nie odpytuj wszystkiego zawsze. Biała lista `search` ma **100 zapytań na dobę** — wyczerpie się
na kilkudziesięciu kontrahentach.

Szczegóły: `references/engineering-core/06-integracje-pl-eu/references/rejestry-api.md`.

## Czego w tym obszarze nie ma

Odpowiedź „tego nie da się zintegrować” jest poprawną odpowiedzią i trzeba ją umieć dać.

| Chciane | Stan faktyczny |
| --- | --- |
| API do składania wniosków w S24 / PRS | Brak. Rejestracja spółki wyłącznie przez aplikację webową |
| API e-Urzędu Skarbowego dla integratorów | Brak. Kanały maszynowe to bramka JPK i KSeF, osobno |
| API do podpisywania profilem zaufanym w dowolnej aplikacji | Brak udokumentowanego interfejsu; usługa podpis.gov.pl jest webowa |
| Jeden wspólny endpoint „PolishAPI” dla wszystkich banków | Nie istnieje. PolishAPI to standard, każdy bank hostuje własną implementację |
| Natychmiastowe rozliczenie merchanta po płatności | Nie. Potwierdzenie transakcji ≠ wpływ środków na rachunek merchanta |
| PISP gwarantujący wpływ środków | Nie. PISP potwierdza zlecenie, nie zaksięgowanie |
| Zaświadczenie o reprezentacji z otwartego API KRS | Nie. `stanZDnia` bywa sprzed tygodni; do czynności prawnej służy odpis z PRS |

## Procedura

1. **Ustal, czy w grę wchodzi obowiązek prawny.** Jeśli tak, wczytaj właściwy plik referencyjny
   i sprawdź datę w tabeli mapy platform. Nie odpowiadaj z pamięci — te daty się zmieniały.
2. **Ustal status podmiotu klienta.** Podmiot publiczny czy niepubliczny; KRS czy CEIDG; próg
   obrotu; zawód zaufania publicznego. Od tego zależy data obowiązku i dostępność usług
   (np. PUH tylko dla podmiotów publicznych jako nadawców).
3. **Sprawdź, czy istnieje publiczne API.** Nie każda usługa państwowa je ma — e-Urząd Skarbowy
   i S24 nie mają. Jeśli nie ma, powiedz to wprost zamiast projektować integrację, która nie
   może powstać.
4. **Ustal sposób uwierzytelnienia** przed projektowaniem czegokolwiek innego. Certyfikat
   kwalifikowany, pieczęć, token, mTLS, klucz API, brak — to determinuje architekturę i czas
   uruchomienia (uzyskanie certyfikatu to tygodnie, licencja KNF to lata).
5. **Ustal środowisko testowe i procedurę dostępu do niego.** KSeF ma TEST i DEMO otwarte;
   e-Doręczenia wymagają wniosku mailowego; banki PSD2 mają sandbox per bank. Czas uzyskania
   dostępu jest elementem harmonogramu projektu.
6. **Sprawdź limity** i porównaj z zakładanym wolumenem. Biała lista `search`: 100 zapytań/dobę.
   CEIDG: 50 / 3 min. GUS: zależne od pory doby. To bywa ograniczeniem projektowym, nie
   szczegółem implementacyjnym.
7. **Zaprojektuj obsługę dowodów i terminów.** Doręczenie, numer KSeF, klucz weryfikacyjny białej
   listy, `requestIdentifier` VIES — to materiał dowodowy. Zapisz go, nie tylko wynik logiczny.
8. **Oznacz każdy fakt normatywny źródłem i datą.** W odpowiedzi dla użytkownika podaj URL
   i datę stanu. Czego nie potwierdziłeś — oznacz `[niepotwierdzone: co sprawdzić i gdzie]`.

## Twarde reguły

1. **Nie podawaj daty wejścia obowiązku z pamięci.** Wczytaj plik referencyjny albo sprawdź
   u źródła. Terminy KSeF i e-Doręczeń były przesuwane.
2. **ADE nie jest adresem e-mail.** Nie proponuj SMTP do e-Doręczeń w żadnej formie.
3. **Nie buduj nowych integracji na ePUAP.** Jest wygaszany; migruj na UA API.
4. **KSeF 1.0 nie istnieje** od 1.02.2026 — kod pod `/online/Session/*` jest martwy.
5. **Weryfikuj podpis webhooka przed parsowaniem treści**, na surowych bajtach ciała żądania.
   Bez tego przyjmiesz spreparowane powiadomienie o płatności.
6. **Przekierowanie z bramki płatniczej ani z banku nie jest potwierdzeniem.** Potwierdzeniem
   jest odpytanie statusu przez API (P24: `verify`; PISP: status zlecenia).
7. **Podpis na poziomie B-B nie nadaje się do archiwum.** Domyślnie generuj B-T, dla dowodowości
   długoterminowej B-LTA — i podnieś poziom, zanim certyfikat wygaśnie.
8. **Nie implementuj walidacji podpisu kwalifikowanego samodzielnie.** Bez sprawdzenia Trusted
   List przepuścisz podpis niekwalifikowany jako kwalifikowany. Użyj DSS.
9. **`offline24` w KSeF to normalna ścieżka, nie awaria.** System musi umieć wystawić fakturę bez
   łączności i dosłać ją do następnego dnia roboczego.
10. **Nie wysyłaj do zewnętrznego API tłumaczenia tekstu, którego klasyfikacja poufności nie
    została sprawdzona programowo.** Tajemnica zawodowa to reżim surowszy niż RODO.
11. **Zapisuj materiał dowodowy, nie tylko wynik.** Klucz weryfikacyjny białej listy, dowód
    otrzymania z e-Doręczeń, numer KSeF, `requestIdentifier` VIES.
12. **Nie zakładaj 100% pokrycia.** Nie każdy NIP ma ADE (CEIDG dopiero od 1.10.2026), nie każdy
    agregator PSD2 obsługuje wszystkie banki, nie każdy podmiot jest w rejestrze `P` KRS.

## Adresy dokumentacji urzędowej

**e-Doręczenia**
- https://www.gov.pl/web/e-doreczenia/harmonogram — terminy obowiązku
- https://www.gov.pl/web/e-doreczenia/interfejsy-api — wersje UA API i SE API
- https://www.gov.pl/web/e-doreczenia/integracja-uslugi-e-doreczen-z-systemami-klasy-ezd — procedura
  INT
- https://int.edoreczenia.gov.pl/dokumentacja — dokumentacja po nadaniu dostępu
- https://pomoc.coi.gov.pl/ — zgłoszenia incydentów (ITSM)
- test.edoreczenia@cyfra.gov.pl — wniosek o dostęp do INT

**KSeF**
- https://ksef.podatki.gov.pl/ — portal główny
- https://ksef.podatki.gov.pl/etapy-wdrozenia-ksef/ — harmonogram
- https://github.com/CIRFMF/ksef-docs — dokumentacja funkcjonalna i changelog
- https://github.com/CIRFMF/ksef-api — OpenAPI i opis środowisk
- http://crd.gov.pl/wzor/2025/06/25/13775/ — struktura FA(3) w CRWDE
- https://api-test.ksef.mf.gov.pl/docs/v2 — dokumentacja API środowiska TEST

**PSD2 / płatności**
- https://polishapi.org/en/documentation/ — standard PolishAPI
- https://www.knf.gov.pl/dla_rynku/procesy_licencyjne/platniczy — licencje KIP/MIP
- https://developers.przelewy24.pl/yaml/pl_documentation_1.0.yaml — OpenAPI P24
- https://docs-api.tpay.com/pl/ — dokumentacja Tpay
- https://developers.payu.com/europe/api/ — dokumentacja PayU
- https://www.kir.pl/ — Express Elixir, usługi open banking

**Podpis i tożsamość**
- https://www.nccert.pl/uslugi.htm — rejestr kwalifikowanych dostawców usług zaufania
- https://podpis.gov.pl/podpisz-dokument-elektronicznie/ — podpis zaufany
- https://ec.europa.eu/digital-building-blocks/DSS/webapp-demo/home — walidator KE
- https://github.com/esig/dss — biblioteka DSS

**Rejestry**
- https://prs.ms.gov.pl/krs/openApi — Otwarte API KRS
- https://dane.biznes.gov.pl/api/ceidg/v3/ — API CEIDG v3
- https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat — biała lista VAT
- https://ec.europa.eu/taxation_customs/vies/ — VIES
- https://api.stat.gov.pl/Home/RegonApi — GUS BIR
- https://www.podatki.gov.pl/pozostale/crbr — CRBR

## Kontrola przed oddaniem

- [ ] Każdy fakt normatywny (data obowiązku, próg kwotowy, sankcja) ma podany **URL źródła
      i datę stanu**.
- [ ] Sprawdziłem, czy termin nie zmienił się po 2026-08-04 — albo jawnie napisałem, że treść
      pochodzi ze stanu na tę datę i wymaga potwierdzenia.
- [ ] Rozróżniłem obowiązek **wystawiania** i **odbierania** (KSeF) oraz obowiązek **posiadania
      ADE** i **aktywacji skrzynki** (e-Doręczenia).
- [ ] Podałem środowisko testowe i procedurę uzyskania do niego dostępu.
- [ ] Podałem sposób uwierzytelnienia i czas potrzebny na jego uzyskanie.
- [ ] Podałem limity API i skonfrontowałem je z zakładanym wolumenem.
- [ ] Wskazałem, co trzeba zapisać jako materiał dowodowy.
- [ ] Wszystko, czego nie potwierdziłem u źródła, jest oznaczone
      `[niepotwierdzone: <co sprawdzić i gdzie>]`.
- [ ] Nie zaproponowałem integracji z usługą, która nie ma publicznego API (e-Urząd Skarbowy, S24).
- [ ] Weryfikacja webhooka (jeśli dotyczy) jest na surowych bajtach, przed parsowaniem, z obsługą
      idempotencji.
