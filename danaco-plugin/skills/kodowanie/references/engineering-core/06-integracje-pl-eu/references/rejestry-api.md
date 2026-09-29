# Rejestry i usługi państwowe — API

> Stan na: 2026-08-04. Źródła: https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat,
> https://prs.ms.gov.pl/krs/openApi (+ weryfikacja wywołaniem `api-krs.ms.gov.pl` 2026-08-04),
> https://pliki.biznes.gov.pl/akademia/Hurtownia_danych/HD CEIDG - API v3 HD - Dokumentacja dla integratorów v1.0.pdf,
> https://api.stat.gov.pl/Home/RegonApi (+ weryfikacja wywołaniem SOAP 2026-08-04),
> https://ec.europa.eu/taxation_customs/vies/ (+ weryfikacja wywołaniem REST 2026-08-04),
> https://www.kujawsko-pomorskie.kas.gov.pl/documents/3319704/10482277/ApiPrzegladoweCRBR_Specyfikacja_We-Wy_2_0_Pub.pdf.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Tabela zbiorcza

| Rejestr | Adres | Auth | Format | Limit |
| --- | --- | --- | --- | --- |
| KRS | `https://api-krs.ms.gov.pl/api/krs/...` | brak | JSON / XML | patrz niżej |
| CEIDG v3 | `https://dane.biznes.gov.pl/api/ceidg/v3/` | JWT (Bearer) | JSON | 50 / 3 min, 1000 / 60 min |
| Biała lista VAT | `https://wl-api.mf.gov.pl` | brak | JSON | 100 zapytań `search`/dobę, 5000 podmiotów `check`/dobę |
| VIES | `https://ec.europa.eu/taxation_customs/vies/rest-api/` | brak | JSON | brak udokumentowanego |
| GUS BIR (REGON) | `https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc` | klucz → sesja (SOAP) | XML | 3–4/s, 120–200/min, 6000–10000/h zależnie od pory |
| CRBR | `https://bramkacrbr.mf.gov.pl:5058/...` | brak | SOAP 1.2 / XML | brak udokumentowanego |
| e-Urząd Skarbowy | — | — | — | brak publicznego API dla integratorów |
| S24 / PRS | — | — | — | brak publicznego API |

## KRS — Otwarte API Ministerstwa Sprawiedliwości

Adres bazowy: **`https://api-krs.ms.gov.pl/api/krs/`**
Dokumentacja: https://prs.ms.gov.pl/krs/openApi

Wzorzec wywołania (**zweryfikowany wywołaniem 2026-08-04, HTTP 200**):

```
GET https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{numerKRS}?rejestr=P&format=json
GET https://api-krs.ms.gov.pl/api/krs/OdpisPelny/{numerKRS}?rejestr=P&format=json
```

| Parametr | Wartości |
| --- | --- |
| `{numerKRS}` | 10 cyfr **z wiodącymi zerami**, np. `0000026438` |
| `rejestr` | `P` — rejestr przedsiębiorców; `S` — rejestr stowarzyszeń i innych organizacji |
| `format` | `json` lub `xml` |

Brak klucza, brak rejestracji, odpowiedź z nagłówkiem CORS. Podmiot spoza wskazanego rejestru
zwraca **404** — jeśli nie wiesz, czy podmiot jest w `P` czy `S`, odpytaj oba.

Struktura odpowiedzi (`odpis`):
- `naglowekA` — `rejestr`, `numerKRS`, `dataCzasOdpisu`, `stanZDnia`, `dataRejestracjiWKRS`,
  `numerOstatniegoWpisu`, `dataOstatniegoWpisu`
- `dane` — działy 1–6 odpisu

Uwaga na `stanZDnia`: dane nie są odświeżane w czasie rzeczywistym. W przykładzie z 2026-08-04
`dataCzasOdpisu` = 04.08.2026, ale `stanZDnia` = 09.07.2026 — prawie miesiąc opóźnienia.
**Nie używaj tego API jako źródła prawdy o reprezentacji do czynności prawnej.** Do tego służy
odpis z PRS opatrzony pieczęcią.

`[niepotwierdzone: limity zapytań otwartego API KRS — MS nie publikuje ich wprost; przyjmij
ostrożne tempo (≤ 1 zapytanie/s) i obsłuż 429]`

Do rejestracji spółki i składania wniosków służą **Portal Rejestrów Sądowych** (prs.ms.gov.pl)
i **S24** (ekrs.ms.gov.pl/s24) — są to aplikacje webowe. **Brak publicznego API do składania
wniosków**; automatyzacja rejestracji spółki nie jest możliwa legalnie przez interfejs
programistyczny. `[niepotwierdzone: czy MS udostępnia jakikolwiek interfejs maszynowy dla S24 —
sprawdź https://www.gov.pl/web/sprawiedliwosc]`

## CEIDG — API v3 hurtowni danych

| Środowisko | Adres |
| --- | --- |
| Produkcja | `https://dane.biznes.gov.pl/api/ceidg/v3/` |
| Test | `https://test-dane.biznes.gov.pl/api/ceidg/v3/` |

Uwierzytelnienie: **token JWT** w nagłówku `Authorization: Bearer <token>`. Token uzyskuje się
przez rejestrację w portalu biznes.gov.pl.

| Endpoint | Rola |
| --- | --- |
| `GET /firmy` | Wyszukiwanie firm wg kryteriów (NIP, REGON, nazwa, miejscowość) |
| `GET /firma` | Szczegółowe dane pojedynczej firmy |
| `GET /zmiana` | Identyfikatory wpisów zmienionych w okresie — **do synchronizacji przyrostowej** |
| `GET /raporty` | Lista dostępnych raportów zbiorczych |
| `GET /raport/{id}` | Pobranie pliku raportu |

Limity (dwa jednocześnie):
- **50 żądań w 3 minuty**
- **1000 żądań w 60 minut**

Przekroczenie → **180-sekundowa blokada**. Optymalny odstęp między zapytaniami: **3,6 s**.

Format: JSON. Kody: 200, 204 (brak danych), 400, 401, 403, 404, 429, 500.
Zwróć uwagę na **204** — to nie błąd, to „nie znaleziono”, i trzeba go obsłużyć osobno od 404.

Wzorzec: do budowy własnej kopii bazy używaj `/raporty` + `/zmiana`, nie odpytywania `/firmy`
w pętli. Przy limicie 1000/h pełny przemiał CEIDG trwałby lata.

## Biała lista podatników VAT (wykaz podatników VAT)

| Środowisko | Adres |
| --- | --- |
| Produkcja | `https://wl-api.mf.gov.pl` |
| Test | `https://wl-test.mf.gov.pl/` |

Bez uwierzytelnienia. Dokumentacja: https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat
(specyfikacja `WykazPodatnikowOpisAPI_v1_6_0.pdf`, stan 01.01.2025; do tego `SwaggerAPI.yml`
i plik z kodami błędów).

Dwie rodziny metod:

| Metoda | Co robi | Limit dobowy |
| --- | --- | --- |
| `search` | Pełne dane podmiotu wg NIP / REGON / numeru rachunku na wskazany dzień | **100 zapytań/dobę**, max **30 podmiotów** w jednym zapytaniu |
| `check` | Uproszczona weryfikacja: czy rachunek jest przypisany do podmiotu na dany dzień | **5000 podmiotów/dobę** |

Po wyczerpaniu limitu dostęp może zostać zablokowany **do godziny 0:00**.

Odpowiedź `check` zawiera potwierdzenie TAK/NIE oraz **klucz weryfikacyjny** (`requestId`),
który potwierdza treść zapytania i moment. Ten klucz jest materiałem dowodowym przy dochowaniu
należytej staranności — **zapisuj go razem z wynikiem**, nie tylko boolean.

Kiedy używać czego: do masowej walidacji rachunków kontrahentów przed przelewem — `check`
(5000/dobę). Do pobrania pełnych danych podmiotu — `search`, ale 100 zapytań na dobę to bardzo
mało; nie buduj na tym funkcji „pokaż dane firmy” w interfejsie użytkownika.

Znaczenie prawne: zapłata na rachunek spoza wykazu przy transakcji ≥ 15 000 zł skutkuje brakiem
możliwości zaliczenia wydatku do kosztów uzyskania przychodu i odpowiedzialnością solidarną za VAT
(chyba że zgłoszenie ZAW-NR). Dlatego weryfikacja musi być zapisana z datą i kluczem.

## VIES — walidacja numerów VAT UE

**REST API (zweryfikowane wywołaniem 2026-08-04, HTTP 200):**

```
POST https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number
Content-Type: application/json

{"countryCode": "PL", "vatNumber": "5250008014"}
```

Odpowiedź (JSON): `countryCode`, `vatNumber`, `requestDate`, `valid` (bool), `requestIdentifier`,
`name`, `address`, oraz pola `trader*` i `trader*Match` przy weryfikacji z danymi kontrahenta.

Dostępność krajów:
```
GET https://ec.europa.eu/taxation_customs/vies/rest-api/check-status
```
Zwraca `vow.available` oraz listę krajów z `availability` (`Available` / `Unavailable`).
**Odpytuj to przed masową weryfikacją** — VIES jest proxy do baz krajowych i pojedyncze kraje
bywają niedostępne godzinami. Wynik „niedostępne” ≠ „numer nieprawidłowy”.

Starszy interfejs SOAP nadal istnieje:
`https://ec.europa.eu/taxation_customs/vies/services/checkVatService.wsdl` — do nowego kodu
używaj REST.

`requestIdentifier` (zwracany przy weryfikacji z nazwą i adresem) jest dowodem sprawdzenia —
zapisz go. Przy pustym zapytaniu (bez danych tradera) pole jest puste.

Brak udokumentowanego limitu zapytań, ale VIES stosuje throttling. Buforuj wyniki — numer VAT
kontrahenta nie zmienia się co godzinę.

## GUS BIR — rejestr REGON

Usługa SOAP (WCF). **Zweryfikowane wywołaniem 2026-08-04.**

| Środowisko | Adres |
| --- | --- |
| Produkcja | `https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc` |
| Test | `https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc` |

Wersje usługi: **BIR 1.1** (od maja 2019) i **BIR 1.2** (od grudnia 2024).
Klucz produkcyjny: wniosek do GUS (regon_bir@stat.gov.pl, tel. 22 608-36-39 / 22 608-33-74).
Klucz testowy: **`abcde12345abcde12345`**.

Przebieg: `Zaloguj` → zwraca identyfikator sesji (`sid`) → kolejne wywołania przekazują `sid`
w nagłówku HTTP `sid` → `Wyloguj`.

Minimalne żądanie logowania (potwierdzone, zwraca `<ZalogujResult>`):

```xml
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:ns="http://CIS/BIR/PUBL/2014/07">
  <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
    <wsa:To>https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc</wsa:To>
    <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj</wsa:Action>
  </soap:Header>
  <soap:Body>
    <ns:Zaloguj><ns:pKluczUzytkownika>abcde12345abcde12345</ns:pKluczUzytkownika></ns:Zaloguj>
  </soap:Body>
</soap:Envelope>
```

`Content-Type: application/soap+xml;charset=UTF-8` (SOAP 1.2). Nagłówek `wsa:To` i `wsa:Action`
są **wymagane** — WCF odrzuca żądanie bez WS-Addressing (HTTP 400). Odpowiedź przychodzi jako
**MTOM/multipart** (`application/xop+xml`) — parser musi to obsłużyć albo trzeba wyciąć kopertę
z multipartu.

Główne operacje: `Zaloguj`, `Wyloguj`, `DaneSzukajPodmioty` (wyszukiwanie po NIP/REGON/KRS),
`DanePobierzPelnyRaport` (raport szczegółowy wg typu podmiotu), `GetValue` (parametry sesji,
m.in. `StatusUslugi`, `KomunikatKod`).
`[niepotwierdzone: pełna lista nazw raportów w BIR 1.2 — pobierz instrukcję ZIP z
https://api.stat.gov.pl/Home/RegonApi]`

Limity zapytań (z portalu API GUS), zależne od pory doby:

| Godziny | /godz. | /min | /s |
| --- | --- | --- | --- |
| 8:00–16:59 | 6 000 | 120 | 3 |
| 6:00–7:59 i 17:00–21:59 | 8 000 | 150 | 3 |
| 22:00–5:59 | 10 000 | 200 | 4 |

Wnioski: masowe zaciąganie danych planuj na noc. Sesja ma ograniczony czas życia — odnawiaj `sid`,
nie loguj się przy każdym zapytaniu (logowanie też liczy się do limitu).

Biblioteki: `gusregon` (Python, PyPI), `bir1` (Node), `gus_bir1` (Ruby), `regonapi` (Python).
`[niepotwierdzone: czy te biblioteki obsługują BIR 1.2; większość powstała dla 1.1]`

## CRBR — Centralny Rejestr Beneficjentów Rzeczywistych

Adres:
```
https://bramkacrbr.mf.gov.pl:5058/uslugiBiznesowe/uslugiESB/AP/ApiPrzegladoweCRBR/2020/05/01
```

Protokół: **SOAP 1.2**, namespace `http://www.mf.gov.pl/schematy/AP/ApiPrzegladoweCRBR/2020/05/01`.
Jedna operacja: **`PobierzInformacjeOSpolkachIBeneficjentach`**.

Usługa **publiczna, bez klucza**. Zwracane statusy: `IstniejaInformacje`, `BrakInformacji`,
`BladFormalny`, plus SOAP Fault.

Uwaga na port **5058** — bywa blokowany przez firewalle korporacyjne. Sprawdź łączność przed
zaplanowaniem integracji.

Specyfikacja nie podaje limitów, SLA ani czasów odpowiedzi. Traktuj usługę jako best-effort:
buforuj wyniki, obsłuż timeout, nie stawiaj na niej ścieżki krytycznej.

## e-Urząd Skarbowy

**Brak publicznego API dla integratorów.** e-Urząd Skarbowy (`urzadskarbowy.gov.pl`) i
e-Mikrofirma (`e-mikrofirma.mf.gov.pl`) są aplikacjami webowymi dla użytkownika końcowego.

Maszynowa komunikacja z KAS przebiega przez odrębne kanały:
- **JPK_V7** — bramka JPK (e-Bramka), wysyłka pliku podpisanego kwalifikowanym podpisem,
  profilem zaufanym albo danymi autoryzującymi;
- **KSeF** — patrz `references/engineering-core/06-integracje-pl-eu/references/ksef.md`;
- **Wykaz podatników VAT** — patrz wyżej.

`[niepotwierdzone: aktualne adresy bramek JPK (produkcyjnej i testowej) oraz schemy JPK_V7
obowiązujące w 2026 r. — sprawdź https://www.podatki.gov.pl/jednolity-plik-kontrolny/]`

## Wzorce użycia

**Weryfikacja kontrahenta przed transakcją** — kolejność, która wykorzystuje limity sensownie:
1. GUS BIR — dane podstawowe i PKD (limit hojny).
2. Biała lista `check` — rachunek bankowy (5000/dobę, wystarczy).
3. KRS `OdpisAktualny` — reprezentacja, jeśli podmiot jest w KRS (pamiętaj o `stanZDnia`).
4. VIES — tylko przy transakcjach wewnątrzwspólnotowych.
5. CRBR — tylko gdy wymaga tego AML.

Nie odpytuj wszystkiego zawsze. Biała lista `search` (100/dobę) wyczerpie się na kilkudziesięciu
kontrahentach.

**Buforowanie.** Dane rejestrowe zmieniają się rzadko. Rozsądne TTL: GUS/KRS/CEIDG — dni;
biała lista — **zero, dla celów dowodowych zawsze świeże zapytanie z zapisem klucza**; VIES —
godziny.

**Zapis dowodowy.** Dla białej listy i VIES zapisuj: identyfikator zapytania zwrócony przez API,
datę i godzinę, pełną odpowiedź. Sam wynik boolean nie jest dowodem należytej staranności.

## Typowe błędy

| Błąd | Konsekwencja |
| --- | --- |
| Numer KRS bez wiodących zer | 404 z API KRS |
| Traktowanie KRS API jako źródła prawdy o reprezentacji | `stanZDnia` bywa sprzed tygodni |
| Odpytywanie CEIDG `/firmy` w pętli | Blokada po 50 żądaniach w 3 minuty |
| Zapisywanie tylko `true/false` z białej listy | Brak dowodu należytej staranności |
| Żądanie SOAP do GUS bez WS-Addressing | HTTP 400 |
| Logowanie do GUS przy każdym zapytaniu | Wyczerpanie limitu na samych logowaniach |
| Nieobsłużenie MTOM w odpowiedzi GUS | Parser XML nie widzi koperty |
| Mylenie `check-status` VIES z wynikiem walidacji | Niedostępność kraju uznana za nieprawidłowy VAT |
| Zależność od CRBR na ścieżce krytycznej | Port 5058 blokowany, brak SLA |
