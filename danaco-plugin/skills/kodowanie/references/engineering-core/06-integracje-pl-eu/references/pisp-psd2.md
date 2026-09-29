# PSD2 / open banking / inicjowanie płatności

> Stan na: 2026-08-04. Źródła: https://polishapi.org/en/,
> https://www.knf.gov.pl/dla_rynku/procesy_licencyjne/platniczy/MIP/Informacje_Ogolne,
> https://legalgeek.pl/blog/instytucje-platnicze-mip-vs-kip/,
> https://dudkowiak.pl/blog/psd3-i-psr-uzgodnione-finalne-teksty-nowe-obowiazki-dla-instytucji-platniczych,
> https://legalgeek.pl/en/blog/psd3-psr-harmonogram-i-najwazniejsze-zmiany/,
> https://www.nccert.pl/uslugi.htm, https://www.certum.eu/en/psd2-certificates/,
> https://eurocert.pl/en/certyfikaty-kwalifikowane-zgodne-z-psd2/.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Role TPP

| Rola | Pełna nazwa | Co wolno |
| --- | --- | --- |
| **AISP** | Account Information Service Provider | Odczyt historii i sald rachunków płatniczych za zgodą użytkownika |
| **PISP** | Payment Initiation Service Provider | Zlecenie przelewu z rachunku użytkownika w jego banku, bez posiadania środków |
| **CAF** / PIISP | Confirmation of Availability of Funds | Zapytanie „czy na rachunku jest kwota X” — odpowiedź TAK/NIE, bez salda |

PISP **nie przyjmuje środków**. Pieniądze idą z rachunku płatnika bezpośrednio na rachunek
odbiorcy. To odróżnia PISP od bramki płatniczej działającej jako acquirer — i dlatego PISP nie
potrzebuje licencji na przyjmowanie środków ani rachunku powierniczego dla nich.

## Licencja KNF

| Forma | Kapitał założycielski | Limit obrotu | Zasięg | Realny czas postępowania |
| --- | --- | --- | --- | --- |
| **MIP** (mała instytucja płatnicza) | brak progu ustawowego | średniomiesięcznie **1 500 000 EUR** z 12 miesięcy (art. 117f ust. 3 UUP) | **tylko Polska**, bez paszportu | 4–6 mies. (termin ustawowy 3 mies.) |
| **KIP** (krajowa instytucja płatnicza) | **20 000 – 125 000 EUR** zależnie od zakresu usług (art. 64 ust. 1 pkt 1 UUP) | brak | paszport UE | **18–36 mies.** (termin ustawowy 3 mies.) |

Dodatkowo:
- Usługa **AIS wyłącznie** (bez PIS) prowadzona jest w reżimie wpisu do rejestru jako
  „dostawca świadczący wyłącznie usługę dostępu do informacji o rachunku” (AISP) — łagodniejszym
  niż zezwolenie KIP. `[niepotwierdzone: aktualne wymogi kapitałowe i proceduralne dla samego
  AISP — sprawdź https://www.knf.gov.pl/dla_rynku/procesy_licencyjne/platniczy]`
- Dla PIS i AIS wymagane jest **ubezpieczenie OC lub gwarancja** (art. 61b UUP).
- **MIP nie może paszportować** — jeśli produkt ma działać poza Polską, MIP nie wystarczy.

Realna liczba do zapamiętania: **18–36 miesięcy** na zezwolenie KIP. To dłużej niż życie
większości projektów. Dlatego domyślną odpowiedzią na „chcemy inicjować płatności” jest
**pośrednik**, nie własna licencja.

## Kiedy własna licencja, kiedy pośrednik

Własna licencja opłaca się, gdy spełnione są łącznie:
- inicjowanie płatności jest **produktem**, nie funkcją pomocniczą;
- wolumen jest na tyle duży, że marża pośrednika przewyższa koszt compliance (compliance officer,
  audyt, sprawozdawczość do KNF, OC, kapitał);
- potrzebujesz kontroli nad UX autoryzacji i danymi, których pośrednik nie odda;
- masz horyzont ≥ 3 lat.

Pośrednik (agregator TPP) opłaca się, gdy:
- płatność jest jednym z kilku sposobów zapłaty w aplikacji;
- nie chcesz utrzymywać integracji z kilkudziesięcioma bankami osobno (każdy bank ma własną
  implementację PolishAPI, własny sandbox i własne odstępstwa od standardu);
- nie chcesz kupować i rotować QWAC/QSealC.

Agregator odsprzedaje dostęp „pod swoją licencją” — z punktu widzenia banku to on jest TPP.
Modele: agregator z własną licencją KIP/AISP (najczęstszy w PL) albo agregator techniczny
(„technical service provider”), który dostarcza tylko warstwę API, a licencję musisz mieć ty.
**Zawsze pytaj, który to model** — od tego zależy, czy potrzebujesz zezwolenia.

Polscy i obecni w PL dostawcy warstwy open banking: **KIR** (Krajowa Izba Rozliczeniowa,
usługi płatnicze i open banking), **Kontomatik**, **Blue Media / Autopay**, **Savangard**
(agregator API). Z zagranicznych obecnych w PL: Tink, Nordigen/GoCardless.
`[niepotwierdzone: aktualny status licencyjny każdego z tych podmiotów i zakres wspieranych banków
w PL — sprawdź w rejestrze KNF https://www.knf.gov.pl/podmioty/wyszukiwarka_podmiotow oraz
w rejestrze EBA]`

## Certyfikaty QWAC i QSealC

| Certyfikat | Do czego | Warstwa |
| --- | --- | --- |
| **QWAC** (Qualified Website Authentication Certificate) | Uwierzytelnienie TPP wobec banku w kanale — mTLS | transport |
| **QSealC** (Qualified Seal Certificate) | Pieczętowanie treści żądania/odpowiedzi — niezaprzeczalność | aplikacja |

Oba muszą zawierać rozszerzenie PSD2 z numerem autoryzacji TPP i rolami (PSP_AI, PSP_PI, PSP_IC)
oraz oznaczeniem organu nadzoru (dla Polski: PL-PFSA).

Wydawcy w Polsce (kwalifikowani dostawcy usług zaufania, rejestr NCCert):
- **Certum / Asseco Data Systems S.A.** — pakiet PSD2 (QWAC + QSealC)
- **EuroCert Sp. z o.o.** — zestaw certyfikatów PSD2, QWAC i QSealC osobno
- **KIR S.A.** i **PWPW S.A.** są w rejestrze jako kwalifikowani dostawcy — `[niepotwierdzone: czy
  oferują certyfikaty z rozszerzeniem PSD2; sprawdź bezpośrednio w ofercie]`

Certyfikat wydaje się **dopiero po uzyskaniu wpisu/zezwolenia** — numer autoryzacji jest polem
w certyfikacie. Nie da się kupić QWAC „na zapas”.

Rotacja: certyfikaty mają ograniczoną ważność (typowo 1–2 lata). Zaplanuj wymianę **z
wyprzedzeniem** — po wygaśnięciu QWAC wszystkie integracje bankowe padają jednocześnie, bo mTLS
przestaje działać.

## PolishAPI

Standard krajowy Związku Banków Polskich.

| Wersja | Status | Data publikacji |
| --- | --- | --- |
| **3.0.1** | wspierana, najnowsza | 17.06.2025 |
| **2.1.4** | wspierana, najnowsza w linii 2.x | 17.06.2025 |
| 3.0 | wspierana | 12.12.2019 |
| 2.1.3 | wspierana | 12.07.2019 |

Zakres: **PIS**, **AIS**, **CAF**. Specyfikacja: PDF (część biznesowa) + YAML (OpenAPI) +
interfejsy na SwaggerHub, https://polishapi.org/en/documentation/

Rzeczywistość wdrożeniowa: PolishAPI to **standard**, nie wspólny endpoint. Każdy bank hostuje
własną implementację, z własnym adresem bazowym, własnym sandboxem, własnym procesem rejestracji
TPP i własnymi odstępstwami (pola opcjonalne, kolejność kroków, obsługa błędów). Część banków
w PL implementuje **Berlin Group NextGenPSD2** zamiast PolishAPI albo obok niego.
Planuj adapter per bank, nie jeden klient „PolishAPI”.

## Przebieg inicjowania płatności (PIS)

1. **Rejestracja TPP w banku** — jednorazowo, na podstawie QWAC. Część banków wymaga dodatkowo
   konta w portalu deweloperskim.
2. **Utworzenie zlecenia** — TPP wysyła do banku dane przelewu (rachunek płatnika opcjonalnie,
   odbiorca, kwota, tytuł). Bank zwraca identyfikator zlecenia i URL do autoryzacji.
3. **Przekierowanie (redirect)** — użytkownik ląduje w bankowości elektronicznej swojego banku.
   To jest **kanał banku**, TPP nie widzi poświadczeń.
4. **SCA** — silne uwierzytelnianie w banku (dwa niezależne elementy: wiedza / posiadanie /
   cecha). Realizowane po stronie banku.
5. **Powrót** — bank przekierowuje na `redirectUri` TPP.
6. **Sprawdzenie statusu** — TPP odpytuje status zlecenia. **Nie ufaj powrotowi z redirectu jako
   potwierdzeniu** — użytkownik może zamknąć okno, a przelew i tak zostanie zlecony (albo
   odwrotnie). Status pochodzi wyłącznie z odpytania API.
7. **Rozliczenie** — środki idą z rachunku płatnika na rachunek odbiorcy w normalnym trybie
   (Elixir sesyjny albo Express Elixir, zależnie od banku i kwoty). PISP **nie gwarantuje**
   natychmiastowego wpływu.

Kluczowa różnica względem bramki płatniczej: PISP potwierdza **zlecenie**, nie **wpływ środków**.
Jeśli logika biznesowa wymaga „towar wydajemy po zaksięgowaniu”, potwierdzenie od PISP nie
wystarczy — trzeba dodatkowo obserwować rachunek (AIS albo wyciąg bankowy).

## SCA — wyjątki

Rozporządzenie delegowane 2018/389 (RTS) przewiduje m.in.: płatności niskokwotowe, zaufani
odbiorcy, transakcje powtarzalne o stałej kwocie, TRA (transaction risk analysis). Wyjątki stosuje
**bank**, nie TPP — TPP może o nie wnioskować, ale decyzja należy do ASPSP.
Dla AIS: SCA wymagane przy pierwszym dostępie, potem odnawiane — w praktyce banki wymagają
ponowienia zgody nie rzadziej niż raz na **180 dni**. `[niepotwierdzone: czy po zmianach RTS
z 2022 r. limit 90 dni został ostatecznie zastąpiony 180 dniami we wszystkich bankach w PL —
sprawdź w dokumentacji konkretnego ASPSP]`

## Terminy odpowiedzi i sandbox

RTS wymaga od ASPSP interfejsu dedykowanego o wydajności nie gorszej niż interfejs klienta oraz
udostępnienia **sandboxa** i dokumentacji **6 miesięcy przed** uruchomieniem produkcyjnym. Banki
publikują SLA w swoich portalach deweloperskich (np. developer.pekao.com.pl). `[niepotwierdzone:
konkretne wartości SLA (ms) — są ustalane per bank, brak wartości ogólnokrajowej]`

Sandbox: każdy bank ma własny. Nie zakładaj, że dane testowe z jednego działają w drugim.
Czas uzyskania dostępu do sandboxa liczy się w tygodniach, nie dniach — uwzględnij to w planie.

## PSD3 / PSR — stan legislacyjny w połowie 2026

| Zdarzenie | Data |
| --- | --- |
| Wstępne porozumienie polityczne | 27.11.2025 |
| Zatwierdzenie przez COREPER | 22.04.2026 |
| Publikacja finalnych tekstów przez Radę UE | 23.04.2026 |
| Publikacja w Dz.Urz. UE | oczekiwana w **drugiej połowie 2026** (jeszcze nie nastąpiła) |
| Rozpoczęcie stosowania PSR | **21 miesięcy** od wejścia w życie |
| Weryfikacja odbiorcy (art. 50, 57 PSR) | **27 miesięcy** od wejścia w życie |
| Termin transpozycji PSD3 | **21 miesięcy** — realnie **2028 r.** |

Stan na 2026-08-04: **treść przepisów jest ustalona, procedura formalna nie jest zamknięta**.
Dla projektu startującego dziś oznacza to: buduj na PSD2, ale nie na założeniach, które PSD3
wprost odwraca.

Zmiany, które mają znaczenie architektoniczne:
1. **Interfejs dedykowany staje się obowiązkowy** — „customer interface” (screen scraping jako
   fallback) przestaje być dopuszczalną alternatywą. Kod oparty na scrapingu ma datę ważności.
2. **Weryfikacja odbiorcy (VoP)** dla wszystkich przelewów, niezależnie od waluty — nie tylko
   SEPA Instant.
3. **Połączenie licencji** — emisja pieniądza elektronicznego wchodzi w zakres zezwolenia
   instytucji płatniczej.
4. **Egzekwowalny dostęp do rachunku** — instytucja płatnicza dostaje formalną ścieżkę odwoławczą
   do nadzoru, gdy bank odmawia rachunku.
5. **Ochrona przed oszustwem „na pracownika banku” (impersonation)** — zwrot dla konsumenta
   w **15 dni roboczych**.
6. **Doprecyzowanie SCA** — transakcje MOTO wyraźnie wyłączone.
7. **Rozszerzenie zakresu podmiotowego** na dostawców usług technicznych, operatorów telekom
   i duże platformy.

## Typowe błędy

| Błąd | Konsekwencja |
| --- | --- |
| Traktowanie powrotu z redirectu jako potwierdzenia płatności | Fałszywe potwierdzenia i fałszywe odrzucenia; obowiązkowe odpytanie statusu |
| Jeden klient „PolishAPI” dla wszystkich banków | Nie działa — każdy bank ma odstępstwa; potrzebny adapter per ASPSP |
| Założenie, że PISP gwarantuje wpływ środków | Wydanie towaru przed zaksięgowaniem |
| Brak monitoringu wygaśnięcia QWAC | Jednoczesna awaria wszystkich integracji bankowych |
| Planowanie na własną licencję KIP w harmonogramie kwartalnym | 18–36 miesięcy postępowania |
| Budowanie na screen scrapingu | PSD3 zamyka tę ścieżkę |
| MIP przy produkcie na rynki UE | Brak paszportu, konieczność ponownego licencjonowania |

## Co potwierdzić przed wdrożeniem

1. Status licencyjny wybranego agregatora w rejestrze KNF i EBA.
2. Czy agregator działa „pod swoją licencją”, czy jako dostawca techniczny.
3. Listę banków realnie obsługiwanych przez agregatora w PL — pokrycie rzadko jest pełne.
4. Wersję standardu implementowaną przez każdy docelowy bank (PolishAPI 3.0.1 vs Berlin Group).
5. Publikację PSD3/PSR w Dz.Urz. UE — od niej biegnie 21/27 miesięcy.
