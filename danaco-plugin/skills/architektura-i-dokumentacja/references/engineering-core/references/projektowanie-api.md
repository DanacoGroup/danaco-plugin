# Projektowanie API

API jest zobowiązaniem. Kod zmienisz wdrożeniem; API zmienisz dopiero wtedy, gdy każdy
konsument zdąży się dostosować — a przy publicznym API nigdy nie wiesz, kto jeszcze go
używa. Dlatego kontrakt projektuje się przed implementacją i traktuje jak umowę.

## REST, RPC czy GraphQL

| | REST (zasoby) | RPC (operacje) | GraphQL |
| --- | --- | --- | --- |
| Model | Zasoby + metody HTTP | Nazwane operacje | Graf typów + zapytanie klienta |
| Naturalne dla | CRUD nad encjami, API publiczne | Operacje biznesowe, komunikacja wewnętrzna | Wielu klientów o różnych potrzebach danych |
| Cache HTTP | Działa (GET + ETag) | Nie działa (POST) | Nie działa bez dodatkowej warstwy |
| Odkrywalność | Wysoka, konwencja znana | Niska, trzeba czytać dokumentację | Wysoka (introspekcja) |
| Koszt wejścia | Niski | Najniższy | Wysoki (serwer, N+1, limity złożoności) |
| Typowa pułapka | Wciskanie operacji w CRUD | Brak konwencji, chaos nazw | Nieograniczone zapytania kładą bazę |

**Domyślnie REST + OpenAPI.** Dla operacji, które nie są CRUD-em (`/zgloszenia/{id}/zamknij`),
nie próbuj ich modelować jako aktualizacji zasobu — dopuść zasób-akcję. `PATCH` ze
zmianą `status` na `zamkniete` gubi to, że zamknięcie ma reguły, których zwykła zmiana
pola nie ma, i nie pozwala przekazać powodu zamknięcia bez zaśmiecania encji.

**RPC (gRPC / tRPC)** wybieraj do komunikacji wewnętrznej między własnymi komponentami,
gdzie liczy się typowany kontrakt i nie potrzebujesz cache'u HTTP ani przeglądarki.

**GraphQL** wybieraj, gdy masz **wielu różnych konsumentów o rozbieżnych potrzebach**
i jeden zespół utrzymujący graf. Przy jednym kliencie GraphQL to koszt bez zysku:
dochodzi problem N+1 (rozwiązywany dataloaderami), limity głębokości i złożoności,
brak cache'u HTTP, a zysk „klient bierze tylko to, czego chce” osiąga się w REST
parametrem `fields` albo dwoma wariantami reprezentacji.

## Zasoby, nazwy, metody

```
GET    /zgloszenia                 lista
POST   /zgloszenia                 utworzenie
GET    /zgloszenia/{id}            pobranie
PATCH  /zgloszenia/{id}            częściowa aktualizacja
DELETE /zgloszenia/{id}            usunięcie
POST   /zgloszenia/{id}/zamkniecia zamknięcie (operacja z regułami)
GET    /zgloszenia/{id}/wiadomosci podzasób
```

| Reguła | Powód |
| --- | --- |
| Rzeczowniki w liczbie mnogiej, małe litery, myślnik jako separator | Konwencja; `/zgloszenia-serwisowe`, nie `/zgloszenieSerwisowe` |
| Zagnieżdżenie maksymalnie 2 poziomy | `/a/{id}/b/{id}/c/{id}/d` jest nieużywalne; od trzeciego poziomu zasób ma własną ścieżkę |
| `GET` nigdy nie zmienia stanu | Cache, prefetch przeglądarki i ponowienia wykonają go wielokrotnie |
| `PUT` zastępuje całość, `PATCH` zmienia część | `PUT` z połową pól wyczyści resztę — jeśli tego nie chcesz, to `PATCH` |
| `DELETE` idempotentny: drugie wywołanie zwraca 204 albo 404, nigdy 500 | Ponowienie po timeoutcie jest normalne |
| Bez czasowników w ścieżce zasobu | `/pobierzZgloszenia` — nie. Wyjątek: zasoby-akcje jak `/zamkniecia` |

### Kody odpowiedzi

| Kod | Kiedy | Częsty błąd |
| --- | --- | --- |
| 200 | Sukces z ciałem | — |
| 201 | Utworzono; nagłówek `Location` z URI nowego zasobu | Brak `Location` |
| 202 | Przyjęto do przetwarzania asynchronicznego | Zwracanie 200 przy operacji, która jeszcze się nie wykonała |
| 204 | Sukces bez ciała | Zwracanie 200 z pustym ciałem `{}` |
| 400 | Żądanie źle sformułowane, walidacja | Używanie 400 do błędów biznesowych |
| 401 | Brak lub nieważne uwierzytelnienie | Mylone z 403 |
| 403 | Uwierzytelniony, ale bez uprawnień | Mylone z 401 |
| 404 | Zasób nie istnieje **lub** nie masz prawa wiedzieć, że istnieje | Zwracanie 403 dla cudzego zasobu — ujawnia jego istnienie |
| 409 | Konflikt stanu (zamknięcie zamkniętego, duplikat) | Zwracanie 400 |
| 410 | Zasób istniał i został trwale usunięty | — |
| 422 | Składnia poprawna, treść semantycznie niepoprawna | Nadużywane zamiast 400; wybierz jedno i trzymaj się |
| 429 | Przekroczony limit; wymagany `Retry-After` | Brak `Retry-After` |
| 500 | Błąd po naszej stronie | Zwracanie 500 przy błędzie walidacji |
| 503 | Chwilowo niedostępne; `Retry-After` | — |

Rozstrzygnięcie 401 vs 403: 401 znaczy „nie wiem, kim jesteś”, 403 znaczy „wiem i nie
wolno ci”. Jeśli samo istnienie zasobu jest informacją poufną, zwracaj 404.

## Format błędu — RFC 9457

Ustandaryzowany format problemu (`application/problem+json`). Zastąpił RFC 7807,
struktura pozostała zgodna.

```json
{
  "type": "https://api.example.com/problemy/limit-czasu-pracy",
  "title": "Przekroczono limit czasu pracy w miesiącu",
  "status": 409,
  "detail": "Umowa UM-2026-14 dopuszcza 40 h miesięcznie; zarejestrowano 38 h, próba dodania 5 h.",
  "instance": "/zgloszenia/018f.../wpisy-czasu",
  "limitGodzin": 40,
  "wykorzystano": 38,
  "korelacja": "01J8XK2M9P"
}
```

| Pole | Rola |
| --- | --- |
| `type` | URI identyfikujące **rodzaj** problemu. Stabilne — klienci na nim polegają. `about:blank` gdy typ = kod HTTP |
| `title` | Krótki, stały opis rodzaju. Nie zmienia się między wystąpieniami |
| `status` | Powtórzenie kodu HTTP (przydatne, gdy odpowiedź przechodzi przez pośredników) |
| `detail` | Opis **tego** wystąpienia. Może zawierać dane |
| `instance` | URI tego konkretnego wystąpienia |
| pola własne | Dane maszynowo przetwarzalne (limity, identyfikatory) |

Reguły:

- `Content-Type: application/problem+json`.
- Klient rozgałęzia logikę po `type`, nigdy po `title` ani `detail` (te są dla ludzi
  i mogą być tłumaczone).
- Błędy walidacji jako lista w polu własnym:

```json
{
  "type": "https://api.example.com/problemy/walidacja",
  "title": "Nieprawidłowe dane wejściowe",
  "status": 400,
  "bledy": [
    { "pole": "email", "kod": "format", "komunikat": "Nieprawidłowy adres e-mail" },
    { "pole": "kwotaGrosze", "kod": "min", "komunikat": "Wartość musi być dodatnia" }
  ]
}
```

- **Nigdy** w odpowiedzi: stos wywołań, nazwy tabel, treść zapytania SQL, wersje
  bibliotek, ścieżki plików. To materiał wywiadowczy dla atakującego. Zwróć
  identyfikator korelacji, a szczegóły zapisz w logu.

## Paginacja

| Rodzaj | Kiedy | Wada |
| --- | --- | --- |
| **Kursorowa** (`?limit=50&po=<kursor>`) | Domyślnie; listy zmieniające się w czasie | Brak skoku na stronę N |
| Offsetowa (`?limit=50&offset=200`) | Małe zbiory (<10 tys.), gdy potrzebny numer strony | `OFFSET 100000` skanuje 100 tys. wierszy; wstawienie rekordu przesuwa stronę i gubi wiersze |
| Zakresowa (`?od=2026-01-01&do=2026-02-01`) | Dane naturalnie czasowe, eksporty | Nierówne strony |

Kursor to nieprzezroczysty ciąg kodujący pozycję sortowania. **Zawsze sortuj po parze
(pole, id)**, inaczej rekordy o identycznej wartości pola będą się gubić lub dublować.

```sql
SELECT id, numer, utworzono
FROM zgloszenia
WHERE klient_id = $1
  AND (utworzono, id) < ($2, $3)     -- kursor rozpakowany
ORDER BY utworzono DESC, id DESC
LIMIT $4;
```

```json
{
  "dane": [ ... ],
  "strona": {
    "nastepny": "eyJ1IjoiMjAyNi0wOC0wNFQxMDowMDowMFoiLCJpIjoiMDE4Zi4uLiJ9",
    "limit": 50
  }
}
```

Reguły: `limit` z wartością domyślną (20–50) i twardym maksimum (100–200); brak limitu
w żądaniu **nie** oznacza „wszystko”. Nie zwracaj `total` przy każdej stronie —
`COUNT(*)` na dużej tabeli kosztuje tyle co całe zapytanie. Jeśli klient go potrzebuje,
osobny endpoint albo `?zLiczba=true` z jawnym kosztem.

## Filtrowanie i sortowanie

```
GET /zgloszenia?status=nowe,w_toku&klientId=018f...&utworzonoOd=2026-01-01&sort=-utworzono
```

| Reguła | Powód |
| --- | --- |
| Płaskie parametry zapytania, wartości wielokrotne po przecinku | Prosto po obu stronach, cache'owalne |
| **Biała lista** pól filtrowania i sortowania | Bez niej dostajesz sortowanie po niezaindeksowanej kolumnie i skan całej tabeli |
| Prefiks `-` dla kierunku malejącego | `sort=-utworzono,numer` |
| Nieznany parametr → 400, nie ciche ignorowanie | Literówka w nazwie filtru cicho zwraca wszystko; przy usuwaniu to katastrofa |
| Bez własnego języka zapytań w URL | `?filter=status:eq:nowe;AND;kwota:gt:100` — piszesz parser i sam go utrzymujesz |

Gdy filtrowanie naprawdę wymaga wyrażeń złożonych, użyj `POST /zgloszenia/wyszukiwania`
z ciałem JSON. Świadomie tracisz cache HTTP, ale zyskujesz strukturę.

## Idempotencja

Sieć zawodzi. Klient, który nie dostał odpowiedzi, nie wie, czy operacja się wykonała,
i ponowi. Bez idempotencji dostaniesz podwójne zgłoszenia, podwójne obciążenia.

| Metoda | Idempotentna z definicji |
| --- | --- |
| `GET`, `HEAD`, `OPTIONS` | Tak |
| `PUT`, `DELETE` | Tak (jeśli zaimplementowane poprawnie) |
| `POST`, `PATCH` | **Nie** — wymagają mechanizmu |

Wzorzec `Idempotency-Key`: klient generuje UUID na operację (nie na żądanie — ponowienie
używa **tego samego** klucza).

```
POST /zgloszenia
Idempotency-Key: 018f2a4b-6c8d-7e1f-9a2b-3c4d5e6f7a8b
```

```sql
CREATE TABLE klucze_idempotencji (
  klucz         uuid PRIMARY KEY,
  odcisk_zadania text NOT NULL,          -- hash metody + ścieżki + ciała
  status_odp    smallint,
  cialo_odp     jsonb,
  utworzono     timestamptz NOT NULL DEFAULT now(),
  wygasa        timestamptz NOT NULL DEFAULT now() + interval '24 hours'
);
```

Algorytm:

1. `INSERT` klucza w tej samej transakcji co operacja. Konflikt na PK oznacza powtórkę.
2. Powtórka z **tym samym** odciskiem żądania → zwróć zapisaną odpowiedź.
3. Powtórka z **innym** odciskiem → 422: ten sam klucz z innym ciałem to błąd klienta.
4. Klucze starsze niż 24 h czyść zadaniem cyklicznym.

Krok 3 jest kluczowy — bez niego klient, który pomylił klucze, dostanie cudzą odpowiedź.

## Wersjonowanie

| Sposób | Za | Przeciw |
| --- | --- | --- |
| **W ścieżce** (`/v1/zgloszenia`) | Widoczne, trywialne w routingu, łatwe w logach i cache | Wersjonuje całe API, nie zasób |
| Nagłówek `Accept` (`application/vnd.firma.v2+json`) | Czyste URI, wersja per reprezentacja | Niewidoczne w logach, trudne do przetestowania w przeglądarce, mylące dla cache |
| Parametr zapytania (`?v=2`) | Proste | Miesza wersję z filtrami, gubi się w cache |

**Domyślnie: wersja w ścieżce, jedna cyfra major.** Wersji minor nie wprowadzaj —
zmiany zgodne wstecz nie wymagają wersji.

### Co jest zmianą łamiącą

Łamiące (wymagają nowej wersji major):

- Usunięcie pola z odpowiedzi lub endpointu.
- Zmiana typu pola (`string` → `number`, skalar → tablica).
- Nowe **wymagane** pole w żądaniu.
- Zawężenie akceptowanego zakresu wartości.
- Zmiana znaczenia pola przy zachowanej nazwie — **najgorsza**, bo cicha.
- Zmiana kodu odpowiedzi dla istniejącego scenariusza.
- Zmiana domyślnego sortowania lub domyślnego limitu.

Niełamiące:

- Nowe pole opcjonalne w odpowiedzi (**pod warunkiem** że klienci ignorują nieznane pola
  — zapisz to w dokumentacji jako wymóg wobec klienta).
- Nowy endpoint, nowy parametr opcjonalny.
- Nowa wartość w polu typu enum — **łamiąca**, jeśli klient robi wyczerpujący `switch`.
  Zapowiedz to w kontrakcie od początku.

### Wycofywanie wersji

1. Ogłoszenie z datą wyłączenia (minimum 6 miesięcy dla API zewnętrznego).
2. Nagłówki w odpowiedziach starej wersji: `Deprecation: true`,
   `Sunset: Sat, 01 Aug 2026 00:00:00 GMT`, `Link: <...>; rel="successor-version"`.
3. Pomiar użycia per konsument — bez tego nie wiesz, kogo wyłączysz.
4. Kontakt z konsumentami, którzy nadal używają.
5. Wyłączenie: 410 Gone z opisem, jak migrować.

## Uwierzytelnianie i autoryzacja

| Konsument | Mechanizm | Uwagi |
| --- | --- | --- |
| Przeglądarka, ta sama organizacja | Sesja w cookie `HttpOnly; Secure; SameSite=Lax` | Natychmiastowe unieważnienie; CSRF pokryty przez `SameSite` plus token dla żądań poza formularzem |
| Integracja maszynowa | Klucz API w `Authorization: Bearer` | Przechowuj **hash** klucza, nie klucz; prefiks umożliwiający identyfikację (`dnc_live_...`) do wykrywania wycieków |
| Aplikacja stron trzecich | OAuth 2.1 + PKCE | Nie wymyślaj własnego przepływu |
| Usługa ↔ usługa wewnątrz sieci | mTLS albo krótkożyjący token z dostawcy tożsamości | — |

Reguły autoryzacji:

1. **Autoryzacja w warstwie aplikacji, nie w kontrolerze.** Kontroler wie o HTTP;
   reguła „użytkownik widzi tylko zgłoszenia swojego klienta” to reguła domenowa.
2. **Filtruj w zapytaniu, nie po pobraniu.** `WHERE klient_id = $aktorKlientId` —
   nie `SELECT *` i sprawdzenie w pętli. Pobranie cudzych danych do pamięci to już
   wyciek, jeśli gdziekolwiek trafi do logu.
3. **Zawsze sprawdzaj przynależność zasobu, nie tylko rolę.** Kontrola dostępu na
   poziomie obiektu (IDOR) jest najczęstszą realną podatnością API: `GET /zgloszenia/{id}`
   z rolą `klient` musi sprawdzić, że zgłoszenie należy do klienta wywołującego.
4. **Domyślna odmowa.** Nowy endpoint bez jawnej reguły ma być niedostępny, nie otwarty.
5. **Nie ujawniaj istnienia cudzego zasobu** — 404 zamiast 403 tam, gdzie samo istnienie
   jest informacją.

## Limity i ochrona zasobów

| Mechanizm | Wartość wyjściowa | Nagłówki |
| --- | --- | --- |
| Limit żądań na klucz | 100/min dla API integracyjnego | `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`; przy 429 obowiązkowo `Retry-After` |
| Maksymalny rozmiar ciała | 1 MB dla JSON, osobny endpoint dla plików | 413 |
| Limit strony | Domyślnie 50, maks. 100 | 400 przy przekroczeniu |
| Limit czasu zapytania | `statement_timeout` w bazie, np. 5 s | 503 |
| Limit głębokości/złożoności (GraphQL) | Głębokość 10, koszt 1000 | 400 |

Algorytm limitowania: token bucket albo okno przesuwne. Limit stały w oknie
kalendarzowym pozwala na podwójną przepustowość na granicy okna.

Ważne: **limit ma być zwracany, zanim żądanie zużyje zasoby**. Sprawdzenie limitu po
wykonaniu zapytania do bazy nie chroni bazy.

## Kontrakt jako źródło prawdy

Dokumentacja pisana ręcznie obok kodu rozjeżdża się w ciągu tygodni. Jedyny działający
układ: kontrakt jest artefaktem, z którego wynikają walidacja i typy — albo jest z kodu
generowany i sprawdzany testem.

Dwa poprawne warianty:

**A. Kontrakt najpierw.** Piszesz OpenAPI 3.1/3.2, generujesz z niego typy i atrapy
serwera; walidacja żądań i odpowiedzi wobec schematu w środowisku testowym. Wybieraj,
gdy konsument jest zewnętrzny albo pisany równolegle przez inny zespół.

**B. Kod najpierw ze schematem jako źródłem.** Definiujesz schematy (TypeBox/Zod dla
Fastify, Pydantic dla FastAPI), OpenAPI generuje się z nich automatycznie. Wybieraj,
gdy API jest wewnętrzne i klient powstaje po serwerze.

Czego **nie** robić: pisać OpenAPI ręcznie **obok** kodu bez powiązania. To gwarantuje
rozjazd, a rozjechana dokumentacja jest gorsza niż jej brak, bo się jej ufa.

Test chroniący kontrakt przed niezamierzoną zmianą — porównanie wygenerowanego dokumentu
z zatwierdzonym plikiem w repozytorium:

```typescript
test('kontrakt OpenAPI nie zmienił się bez zapowiedzi', async () => {
  const app = await zbudujAplikacje();
  const biezacy = app.swagger();
  const zatwierdzony = JSON.parse(
    await readFile('contracts/openapi.json', 'utf8'),
  );
  expect(biezacy).toEqual(zatwierdzony);
});
```

Zmiana kontraktu wymaga wtedy świadomej aktualizacji pliku — czyli pojawia się w diffie
i przechodzi przez przegląd.

OpenAPI 3.2 (wydana 2025) dodała m.in. opis odpowiedzi strumieniowanych (`itemSchema`
dla SSE/NDJSON), pole `additionalOperations` dla metod spoza HTTP-owego standardu i
`$self` dla identyfikacji dokumentu. Wsparcie narzędzi jest częściowe — jeśli twój
generator kodu nie deklaruje 3.2, zostań przy 3.1.

## Zdarzenia i webhooki

Webhook to twoje API u odbiorcy — obowiązują te same reguły kontraktu, plus specyfika
dostarczania.

### Struktura zdarzenia

```json
{
  "id": "018f2a4b-6c8d-7e1f-9a2b-3c4d5e6f7a8b",
  "typ": "zgloszenie.zamkniete",
  "wersja": 1,
  "utworzono": "2026-08-04T10:15:30.123Z",
  "zasobId": "018f2a4b-...",
  "dane": { "zgloszenieId": "018f...", "klientId": "018f...", "zamknietoPrzez": "018f..." }
}
```

| Reguła | Powód |
| --- | --- |
| `id` unikalne i **stałe między ponowieniami** | Odbiorca odsiewa duplikaty po `id` |
| Nazwa typu `zasob.czynnosc` w czasie przeszłym | Zdarzenie opisuje fakt, nie polecenie |
| `wersja` w ładunku od pierwszego dnia | Dopisanie wersjonowania później jest zmianą łamiącą |
| Ładunek zawiera identyfikatory, nie pełny stan | Pełny stan dezaktualizuje się w locie i puchnie; wyjątek: gdy odbiorca nie ma dostępu do API |
| Bez danych wrażliwych w ładunku | Webhook idzie na cudzy serwer, ląduje w cudzych logach |

### Dostarczanie

- **At-least-once.** Odbiorca **musi** być idempotentny. Zapisz to w dokumentacji
  wielkimi literami — to najczęstsze źródło incydentów u konsumentów.
- **Brak gwarancji kolejności.** Jeśli kolejność ma znaczenie, dodaj monotoniczny
  numer sekwencyjny per zasób i pozwól odbiorcy odrzucać starsze.
- **Podpis HMAC** nagłówkiem, liczony z surowego ciała plus znacznik czasu:

```
X-Sygnatura: t=1754301330,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
```

Odbiorca liczy `HMAC-SHA256(sekret, "{t}.{surowe_cialo}")` i porównuje **w czasie
stałym**. Znacznik czasu w podpisie chroni przed powtórzeniem nagrania (odrzucaj
starsze niż 5 minut). Bez znacznika podpis sam w sobie nie chroni przed replayem.

- **Wycofywanie wykładnicze z rozproszeniem**: 1 s, 5 s, 30 s, 5 min, 30 min, 2 h, 6 h.
  Po ostatniej próbie oznacz punkt końcowy jako niesprawny i powiadom właściciela.
- **Limit czasu odpowiedzi 5 s.** Odbiorca ma potwierdzić przyjęcie (2xx), a nie
  przetworzyć synchronicznie.
- **Panel z historią dostarczeń i przyciskiem ponowienia.** Bez tego każdy problem
  konsumenta jest zgłoszeniem do ciebie.

## Lista kontrolna kontraktu

- [ ] Każdy endpoint ma schemat żądania i schemat odpowiedzi (także błędnej).
- [ ] Błędy w formacie RFC 9457 ze stabilnym `type`.
- [ ] Listy paginowane kursorowo, z limitem domyślnym i maksymalnym.
- [ ] Filtry i sortowanie z białej listy; nieznany parametr → 400.
- [ ] `POST` tworzący zasób obsługuje `Idempotency-Key`.
- [ ] Wersja w ścieżce; polityka zmian łamiących opisana.
- [ ] Autoryzacja sprawdza przynależność zasobu, nie tylko rolę.
- [ ] Limity żądań z nagłówkami `RateLimit-*` i `Retry-After`.
- [ ] Żadna odpowiedź błędna nie zawiera stosu, SQL-a ani nazw tabel.
- [ ] Kontrakt OpenAPI generowany z kodu (lub kod z kontraktu) + test porównawczy.
- [ ] Webhooki: `id` stabilne, podpis HMAC ze znacznikiem czasu, wycofywanie wykładnicze.
- [ ] Nagłówki `Deprecation`/`Sunset` przy wycofywanych endpointach.
