# Płatności krajowe

> Stan na: 2026-08-04. Źródła: https://developers.przelewy24.pl/yaml/pl_documentation_1.0.yaml
> (OpenAPI 3.0.0, `info.version: 1.0.17`, pobrane 2026-08-04),
> https://docs-api.tpay.com/pl/webhooks/, https://developers.payu.com/europe/api/,
> https://developers.payu.com/europe/docs/payment-flows/lifecycle/,
> https://www.kir.pl/nasza-oferta/klient-indywidualny/rozliczenia/express-elixir,
> https://openapi.tpay.com/, https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/uslugi-platnicze-17734563.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Wybór operatora — co realnie różnicuje

| Operator | Model | BLIK | Wyróżnik |
| --- | --- | --- | --- |
| **Przelewy24** | agent rozliczeniowy PL | tak, z aliasami | Najszersze pokrycie pay-by-link w PL, OpenAPI publiczne bez rejestracji |
| **PayU** | agent rozliczeniowy (grupa Prosus) | tak | Rozbudowany REST, OAuth2, obecność w regionie CEE |
| **Tpay** | agent rozliczeniowy PL | tak | Webhooki podpisywane **JWS** (RFC 7515) — najmocniejsza weryfikacja spośród trójki |
| **Autopay** (d. Blue Media) | agent rozliczeniowy + open banking | tak | Łączy bramkę z usługami PSD2 |
| **Stripe** | międzynarodowy PSP | tak (jako metoda) | Obsługuje BLIK i Przelewy24 jako metody płatności; sens przy sprzedaży międzynarodowej |

Reguła: **do sprzedaży wyłącznie w PL** bierz operatora krajowego — Stripe dokłada warstwę
przewalutowania i rozliczeń, której nie potrzebujesz. **Do sprzedaży międzynarodowej z PL** Stripe
z włączonym BLIK i P24 jest jedną integracją zamiast dwóch.
`[niepotwierdzone: aktualne stawki prowizji każdego z operatorów — zmieniają się i są negocjowane
indywidualnie; nie podawaj liczb bez sprawdzenia w umowie]`

## BLIK

Operator: **Polski Standard Płatności sp. z o.o.** Merchant nie integruje się z PSP bezpośrednio
w typowym przypadku — BLIK dostajesz jako metodę u agenta rozliczeniowego (P24, PayU, Tpay,
Autopay, Stripe).

Dwa warianty w API bramek:
1. **Kod jednorazowy (6 cyfr)** — użytkownik podaje kod z aplikacji bankowej, merchant przekazuje
   go w żądaniu obciążenia. Kod ma krótką ważność (rzędu 2 minut), po czym wygasa.
2. **Alias (BLIK one-click)** — po pierwszej płatności bank zwraca alias przypisany do użytkownika;
   kolejne płatności bez wpisywania kodu, z potwierdzeniem w aplikacji.

W Przelewy24 odpowiadają temu endpointy:
- `POST /api/v1/paymentMethod/blik/chargeByCode`
- `POST /api/v1/paymentMethod/blik/chargeByAlias`
- `GET /api/v1/paymentMethod/blik/getAliasesByEmail/{email}`

Konsekwencja UX: przy kodzie jednorazowym masz ~2 minuty na całą rundę. Formularz nie może
przeładowywać strony po wpisaniu kodu ani czekać na wolny backend — inaczej kod wygaśnie w połowie.

## Przelewy24 — integracja

Specyfikacja OpenAPI: https://developers.przelewy24.pl/yaml/pl_documentation_1.0.yaml
(wersja `1.0.17`, odczyt 2026-08-04). Generuj klienta z tego pliku.

Serwery:

| Środowisko | Adres |
| --- | --- |
| Sandbox | `https://sandbox.przelewy24.pl` |
| Produkcja | `https://secure.przelewy24.pl` |

Kluczowe endpointy:

| Endpoint | Rola |
| --- | --- |
| `POST /api/v1/testAccess` | Sprawdzenie poświadczeń — zrób to jako pierwszy krok wdrożenia |
| `POST /api/v1/transaction/register` | Rejestracja transakcji, zwraca `token` do przekierowania |
| `POST /api/v1/transaction/verify` | **Weryfikacja** transakcji po notyfikacji — bez tego transakcja nie jest zamknięta |
| `POST /api/v1/transaction/refund` | Zwrot |
| `POST /api/v1/transaction/registerOffline` | Rejestracja offline |
| `POST /api/v1/transaction/register/splitpayment` | Split payment |
| `GET /api/v1/payment/methods/{lang}` | Lista metod płatności |
| `GET /api/v1/report/history`, `/api/v1/report/batch/details` | Raporty rozliczeniowe |

### Suma kontrolna `sign` — SHA-384

`sign` liczy się jako **SHA-384** z ciągu JSON zbudowanego z określonego zestawu pól.
**Zestaw pól jest inny dla każdego żądania** — to najczęstsze źródło błędów.

Rejestracja transakcji (`/transaction/register`) — pola w kolejności:

```python
import hashlib, json

params = {
    "sessionId": session_id,      # str, unikalne ID sesji
    "merchantId": merchant_id,    # int, z panelu P24
    "amount": amount_grosze,      # int, w groszach: 1234 == 12,34 PLN
    "currency": "PLN",            # str
    "crc": crc_key,               # str, klucz CRC z panelu P24
}
combined = json.dumps(params, ensure_ascii=False, separators=(",", ":"))
sign = hashlib.sha384(combined.encode("utf-8")).hexdigest()
```

Weryfikacja transakcji (`/transaction/verify`) — **inny zestaw**: `sessionId`, `orderId` (int,
z notyfikacji), `amount`, `currency`, `crc`.

Pułapki serializacji, wprost wskazane w dokumentacji P24:
- **Kolejność kluczy musi być zachowana** — użyj słownika uporządkowanego, nie sortuj.
- Bez escape'owania Unicode i slashy. W PHP: `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES`.
  W Pythonie: `ensure_ascii=False` (slashe i tak nie są escapowane).
- **Typy mają znaczenie**: `merchantId` i `amount` to `int`, reszta `str`. Wysłanie `amount`
  jako stringa zmienia JSON i psuje hash.
- `separators=(",", ":")` — bez spacji, inaczej hash się nie zgodzi z tym, co liczy P24.

### Notyfikacja

P24 wysyła notyfikację POST na `urlStatus`. Jeśli merchant **nie wykona poprawnej weryfikacji**,
P24 ponawia powiadomienie po **3, 5, 15, 30, 60, 150 i 450 minutach** (±5 min).

Odrębna notyfikacja o zwrocie (`RefundNotification`) idzie na `urlStatus` podany w żądaniu
`/transaction/refund`, a przy jego braku — na domyślny adres z panelu.

Poprawny przebieg:
1. `register` → `token`
2. redirect użytkownika na `https://secure.przelewy24.pl/trnRequest/{token}`
3. notyfikacja POST na `urlStatus`
4. **`verify`** z sumą kontrolną liczoną z `orderId`
5. dopiero po `verify` uznaj płatność za rozliczoną

Krok 4 nie jest opcjonalny. Bez `verify` P24 traktuje transakcję jako niepotwierdzoną i będzie
ponawiać notyfikacje przez 450 minut.

## Tpay — integracja i weryfikacja JWS

Dokumentacja: https://docs-api.tpay.com/pl/ , OpenAPI: https://openapi.tpay.com/

Webhook Tpay jest podpisany w nagłówku **`X-JWS-Signature`** (RFC 7515, JSON Web Signature),
algorytm **RSA z SHA-256**.

Procedura weryfikacji (obowiązkowa wg dokumentacji):
1. Odczytaj `X-JWS-Signature` — trzy segmenty base64url rozdzielone kropkami.
2. Zdekoduj nagłówek JWS, wyciągnij URL certyfikatu (`x5u`).
3. Zwaliduj łańcuch certyfikatu względem root CA Tpay.
4. Zweryfikuj podpis nad **oryginalnym, surowym ciałem żądania** (nie nad ponownie
   zserializowanym JSON-em).

Certyfikaty:
- podpisujący: `https://secure.tpay.com/x509/notifications-jws.pem`
- root CA: `https://secure.tpay.com/x509/tpay-jws-root.pem`

Odpowiedź: HTTP **200** z ciałem dokładnie `TRUE`. Każda inna odpowiedź uruchamia ponowienia.

To jest mocniejszy model niż hash z sekretem: nawet ujawnienie klucza merchanta nie pozwala
sfałszować notyfikacji, bo podpis jest asymetryczny.

## PayU — integracja i weryfikacja

Dokumentacja: https://developers.payu.com/europe/api/

Notyfikacja idzie na `notifyUrl`, oczekiwana odpowiedź HTTP **200**. Ponowienia: próby 1–5
natychmiast oraz po 1, 2, 5 i 10 minutach; próby 6–20 z rosnącymi odstępami **do 72 godzin**.

Adresy IP, z których PayU wysyła notyfikacje (dodatkowa, nie zastępcza kontrola):

| Środowisko | IP |
| --- | --- |
| Produkcja | 185.68.12.10, .11, .12, .26, .27, .28 |
| Sandbox | 185.68.14.10, .11, .12, .26, .27, .28 |

Podpis w nagłówku **`OpenPayu-Signature`**, zawiera pola: `sender=checkout`, `algorithm`
(MD5 albo SHA), `signature`, `content=DOCUMENT`.

Weryfikacja:
1. Wyciągnij `signature` i `algorithm` z nagłówka.
2. Sklej **surowe ciało JSON** notyfikacji z **second key** (drugi klucz z panelu PayU).
3. Policz hash wskazanym algorytmem.
4. Porównaj z `signature`.

Uwaga: MD5 jako algorytm podpisu jest słaby kryptograficznie. Jeśli konfiguracja pozwala, wymuś
SHA. Filtrowanie po IP traktuj jako warstwę dodatkową — samo IP nie zastępuje weryfikacji podpisu.

## Reguły wspólne dla wszystkich webhooków płatniczych

1. **Weryfikuj podpis przed parsowaniem treści.** Odwrotna kolejność otwiera na ataki przez
   spreparowany payload.
2. **Podpisuj/haszuj surowe bajty ciała żądania**, nie obiekt po deserializacji. Frameworki
   (FastAPI, Express) domyślnie oddają zdeserializowany obiekt — trzeba jawnie sięgnąć po `raw
   body`.
3. **Idempotencja.** Wszystkie trzy bramki ponawiają notyfikacje. Ta sama transakcja przyjdzie
   wielokrotnie. Klucz idempotencji: identyfikator transakcji operatora + status.
4. **Nie ufaj kwocie z notyfikacji.** Porównaj z kwotą zapisaną przy rejestracji transakcji.
   Notyfikacja z inną kwotą to sygnał manipulacji albo częściowej płatności.
5. **Odpowiadaj szybko.** Ciężką pracę (wysyłka maila, generowanie faktury, KSeF) wrzuć do
   kolejki. Timeout po stronie operatora liczy się jako niepowodzenie i uruchamia ponowienia.
6. **Loguj surowe żądanie z nagłówkami.** Przy sporze o płatność to jedyny materiał dowodowy.

## Express Elixir

Operator: **KIR S.A.** Przelew natychmiastowy w PLN.

| Parametr | Wartość |
| --- | --- |
| Dostępność | 24/7/365, także weekendy i święta (dostępność zależy od banku) |
| Czas realizacji | kilka sekund |
| Limit pojedynczego przelewu | do **100 000 zł** (standardowo) |
| Limit dla organów celno-skarbowych | do **250 000 zł** |
| Uczestnicy | ponad 25 banków komercyjnych i ok. 450 banków spółdzielczych |
| Wolumen 2025 | 636 mln transakcji, 321 mld zł |

Limity kwotowe są **ustalane przez banki** i mogą być niższe niż limit systemowy. Nie zakładaj
100 000 zł jako pewnika — sprawdź w banku odbiorcy i nadawcy.

Znaczenie dla integracji: potwierdzenie z bramki płatniczej (pay-by-link) nie oznacza, że środki
przyszły Express Elixirem. Rozliczenie merchanta następuje w cyklu ustalonym w umowie
z agentem rozliczeniowym, nie natychmiast.

## Wymogi prawne

**Regulamin.** Sprzedaż online wymaga regulaminu ze wskazaniem dostępnych metod płatności,
terminu płatności i podmiotu obsługującego płatności. Podstawa: ustawa o świadczeniu usług drogą
elektroniczną + ustawa o prawach konsumenta.

**Zwroty.** Odstąpienie od umowy zawartej na odległość: **14 dni** dla konsumenta; przedsiębiorca
zwraca środki **w ciągu 14 dni** od otrzymania oświadczenia, tym samym sposobem, którym otrzymał
zapłatę, chyba że konsument zgodził się na inny bez kosztów. Zwrot przez API bramki
(`/transaction/refund` w P24) realizuje ten obowiązek technicznie — ale termin biegnie od
oświadczenia, nie od wywołania API.

**Reklamacje.** Podmioty rynku finansowego (w tym agenci rozliczeniowi, instytucje płatnicze)
podlegają ustawie o rozpatrywaniu reklamacji przez podmioty rynku finansowego i o Rzeczniku
Finansowym — termin odpowiedzi to **30 dni**, w sprawach szczególnie skomplikowanych do 60 dni.
Merchant nie jest podmiotem rynku finansowego, ale reklamacja dotycząca samej płatności trafia
do operatora. `[niepotwierdzone: aktualne brzmienie terminów w ustawie o rozpatrywaniu reklamacji
po nowelizacjach — sprawdź tekst jednolity]`

**Nieautoryzowana transakcja płatnicza.** Dostawca zwraca kwotę **do końca następnego dnia
roboczego** po zgłoszeniu (zasada D+1, art. 46 ustawy o usługach płatniczych), chyba że ma
uzasadnione podejrzenie oszustwa i powiadomi organy ścigania. To obowiązek dostawcy usług
płatniczych, nie merchanta — ale merchant musi wiedzieć, że chargeback w tym trybie jest szybki.

## Typowe błędy

| Błąd | Konsekwencja |
| --- | --- |
| Ten sam zestaw pól `sign` dla `register` i `verify` w P24 | Odrzucenie weryfikacji, transakcja niezamknięta, notyfikacje przez 450 minut |
| Liczenie hasha z ponownie zserializowanego JSON-a | Hash się nie zgadza (kolejność kluczy, spacje, escape) |
| Pominięcie `verify` w P24 | Transakcja nigdy nie zostaje potwierdzona po stronie operatora |
| Brak idempotencji obsługi webhooka | Podwójne wydanie towaru, podwójna faktura |
| Zaufanie kwocie z notyfikacji bez porównania | Zaniżona płatność uznana za pełną |
| Ciężka praca synchronicznie w handlerze webhooka | Timeout → ponowienia → duplikaty |
| Weryfikacja tylko po IP (PayU) | IP można sfałszować za proxy; potrzebny podpis |
| Formularz BLIK przeładowujący stronę | Kod 6-cyfrowy wygasa w trakcie |

## Co potwierdzić przed wdrożeniem

1. Wersję OpenAPI operatora (P24 publikuje `info.version`, sprawdź czy nie podbito).
2. Aktualne prowizje i warunki rozliczeń w umowie — nie z artykułów porównawczych.
3. Adresy IP notyfikacji PayU (bywają rozszerzane).
4. Czy metoda BLIK jest włączona na koncie — u wszystkich operatorów wymaga aktywacji.
