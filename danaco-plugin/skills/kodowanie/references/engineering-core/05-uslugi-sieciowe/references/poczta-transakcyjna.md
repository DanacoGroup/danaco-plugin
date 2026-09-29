# Poczta transakcyjna: wysyłka z aplikacji

Ceny i stan dostawców zweryfikowane lipiec/sierpień 2026.

## Podział, od którego wszystko zależy

| Rodzaj | Przykłady | Podstawa prawna wysyłki | Subdomena |
|---|---|---|---|
| Transakcyjna | reset hasła, potwierdzenie zamówienia, faktura, kod jednorazowy, powiadomienie o statusie sprawy | wykonanie umowy / obowiązek prawny — **zgoda niepotrzebna** | `powiadomienia.przyklad.pl` |
| Marketingowa | newsletter, promocja, „wróć do koszyka”, ankieta NPS, zaproszenie na webinar | **zgoda wymagana** (PKE art. 398) | `wiadomosci.przyklad.pl` |

Rozdzielenie subdomen to nie kosmetyka. Reputacja liczy się per domena nadawcza. Jedna kampania
marketingowa z wysokim wskaźnikiem skarg, wysłana z tej samej domeny co resety haseł, zabiera
ze sobą resety haseł. **Zawsze dwie subdomeny, dwa klucze DKIM, dwa konta u dostawcy** (albo dwa
różne konta subusera / dwie różne pule IP).

Wiadomość transakcyjna z doklejonym banerem promocyjnym staje się marketingową w rozumieniu
PKE. Nie doklejaj.

## Dostawcy — porównanie

| Dostawca | Model | Koszt orientacyjny | Mocne strony | Ryzyka |
|---|---|---|---|---|
| **Amazon SES** | pay-as-you-go | ~0,10 USD / 1000; 50 tys./mies. za ~4,70 USD | najtaniej przy skali; regiony UE (`eu-central-1`, `eu-west-1`); pełna kontrola | konto startuje w piaskownicy (tylko zweryfikowane adresy) — wyjście na wniosek; brak szablonów wizualnych; webhooki przez SNS wymagają montażu; wsparcie płatne |
| **Resend** | free + pay-as-you-go | 3 000/mies. bezpłatnie; ~0,0004 USD/wiad.; 50 tys. ≈ 18,80 USD | najlepsze API dla zespołów JS/TS; React Email; szybkie wdrożenie | młodszy dostawca, mniej narzędzi analitycznych |
| **Postmark** | abonament | od ~15 USD/mies.; +1,80 USD / 1000 ponad limit; 50 tys. ≈ 84,82 USD | **najlepsza dostarczalność transakcyjna**; osobne strumienie transakcyjny/masowy wymuszone przez dostawcę; szczegółowe zdarzenia | najdroższy; polityka twardo zabrania marketingu na strumieniu transakcyjnym |
| **SendGrid** | abonament + nadwyżki | plany od ~20 USD | dojrzały; subusers; pule IP | zbiorcza reputacja niższych planów bywa słaba; wsparcie oceniane słabo |
| **Mailgun** | abonament + nadwyżki | plany od ~15 USD | dobre API do odbioru poczty przychodzącej (routes) i parsowania | dostarczalność zmienna między planami |
| **Brevo** (dawniej Sendinblue) | limity dobowe/abonament | plan bezpłatny 300/dobę | **spółka z UE (Francja)** — prostsza dokumentacja RODO; łączy transakcyjne i marketing | narzuca własne stopki na planach bezpłatnych |
| **Mailjet** | abonament | plan bezpłatny 200/dobę | UE (Francja), polskie wsparcie przez partnerów | interfejs szablonów przeciętny |

Wybór dla typowego projektu DANACO:

- Aplikacja w Pythonie/Node, ≤ 50 tys. wiad./mies., klient wrażliwy na RODO → **Brevo** albo
  **Mailjet** (podmioty z UE) lub **SES w `eu-central-1`** z SCC.
- Aplikacja, gdzie kluczowa jest dostarczalność krytycznych powiadomień (kancelaria, finanse) →
  **Postmark**.
- Skala > 200 tys. wiad./mies. i zespół umiejący obsłużyć SNS → **SES**.
- Prototyp / MVP w TypeScripcie → **Resend**.

Niezależnie od wyboru: **własna domena zwrotna (custom MAIL FROM / custom return-path)**
i DKIM podpisany twoją domeną. Bez tego nie masz wyrównania DMARC (patrz
`references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md`).

## API czy SMTP relay

| | API (HTTPS) | SMTP relay |
|---|---|---|
| Zależność | biblioteka lub `httpx` | biblioteka SMTP w każdym języku |
| Wydajność | jedno żądanie na wiadomość lub wsad; brak handshake'u SMTP | 3 rundy TCP + TLS na wiadomość, chyba że trzymasz połączenie |
| Zwrot identyfikatora | natychmiast, `message_id` do korelacji z webhookiem | tylko w treści odpowiedzi `250`, trzeba parsować |
| Szablony po stronie dostawcy | tak | nie |
| Porty | 443 — nigdy blokowany | 587/465 — blokowane w części sieci firmowych |
| Migracja do innego dostawcy | trzeba przepisać warstwę | zmiana hosta i danych logowania |
| Diagnostyka | kody HTTP + JSON z powodem | kody SMTP |

**Domyślnie API.** SMTP relay wybierz, gdy wysyła gotowe oprogramowanie, którego nie
przepiszesz (WordPress, ERP, drukarka), albo gdy chcesz zachować możliwość natychmiastowej
zmiany dostawcy bez zmiany kodu.

Warstwa abstrakcji w aplikacji jest tania i opłaca się zawsze:

```python
# poczta/nadawca.py
from dataclasses import dataclass, field
from typing import Protocol

@dataclass(slots=True)
class Wiadomosc:
    do: str
    temat: str
    html: str
    tekst: str
    szablon: str | None = None
    dane: dict = field(default_factory=dict)
    zalaczniki: list[tuple[str, bytes, str]] = field(default_factory=list)
    naglowki: dict[str, str] = field(default_factory=dict)
    tag: str = "transakcyjna"

class Nadawca(Protocol):
    def wyslij(self, w: Wiadomosc) -> str:  # zwraca message_id dostawcy
        ...
```

Implementacje: `NadawcaResend`, `NadawcaSES`, `NadawcaSMTP`, `NadawcaLog` (środowisko
deweloperskie — zapis do pliku zamiast wysyłki). Testy jednostkowe wpinają `NadawcaLog`.

### SES przez API, z obsługą własnej domeny zwrotnej

```python
import boto3
from botocore.config import Config

_ses = boto3.client(
    "sesv2",
    region_name="eu-central-1",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)

def wyslij_ses(w: Wiadomosc) -> str:
    odp = _ses.send_email(
        FromEmailAddress="DANACO <powiadomienia@powiadomienia.przyklad.pl>",
        Destination={"ToAddresses": [w.do]},
        FeedbackForwardingEmailAddress="bounce@powiadomienia.przyklad.pl",
        ConfigurationSetName="transakcyjne",   # spina zdarzenia z SNS/EventBridge
        EmailTags=[{"Name": "typ", "Value": w.tag}],
        Content={
            "Simple": {
                "Subject": {"Data": w.temat, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": w.tekst, "Charset": "UTF-8"},
                    "Html": {"Data": w.html, "Charset": "UTF-8"},
                },
                "Headers": [
                    {"Name": k, "Value": v} for k, v in w.naglowki.items()
                ],
            }
        },
    )
    return odp["MessageId"]
```

`Charset: "UTF-8"` przy każdym polu — bez tego SES koduje jako US-ASCII i polskie znaki
w temacie zamieniają się w znaki zapytania. To najczęstszy błąd w integracjach SES z Polski.

Piaskownica SES: nowe konto może wysyłać wyłącznie na zweryfikowane adresy, limit 200/dobę
i 1 wiad./s. Wyjście z piaskownicy to wniosek w konsoli z opisem, co wysyłasz i jak obsługujesz
odbicia — rozpatrywany zwykle w 24 h, ale **złóż go tydzień przed startem produkcji**.

## Szablony i personalizacja

Trzy podejścia:

1. **Szablony po stronie dostawcy** (SES templates, Postmark templates, SendGrid dynamic
   templates). Zaleta: zmiana treści bez wdrożenia aplikacji, marketing edytuje sam.
   Wada: przywiązanie do dostawcy, trudne wersjonowanie i przegląd zmian, brak testów.
2. **Szablony w repozytorium**, renderowane w aplikacji (Jinja2, MJML, React Email).
   Zaleta: wersjonowanie w Gicie, przegląd kodu, testy migawkowe. Wada: każda literówka
   wymaga wdrożenia.
3. **Hybryda**: struktura (layout, nagłówek, stopka) w repozytorium, treść zmienna w bazie
   z panelem administracyjnym.

Domyślnie **2** dla powiadomień transakcyjnych, **1 lub 3** dla marketingu.

MJML kompiluje deklaratywny znacznik do tabelowego HTML-a zgodnego z Outlookiem — oszczędza
tygodnie walki z klientami pocztowymi. `mjml szablon.mjml -o szablon.html` w kroku budowania.

Personalizacja:

- Zawsze przygotuj wartość zapasową: `{{ imie|default("Dzień dobry") }}`. Wysłanie
  „Dzień dobry, {{imie}}” z niewypełnionym polem to najgorszy możliwy pierwszy kontakt.
- Odmiana imion po polsku: nie próbuj. „Dzień dobry, Anno” wygenerowane automatycznie
  wywróci się na „Dzień dobry, Xawery”. Używaj mianownika po przecinku albo formy neutralnej.
- Nie personalizuj tematu wartościami, których nie kontrolujesz (nazwa produktu z importu CSV
  potrafi zawierać znaki, które łamią kodowanie nagłówka).

## Załączniki

- Twardy limit u większości dostawców i odbiorców: **10-25 MB po zakodowaniu base64**
  (czyli ~7-18 MB pliku). Gmail przyjmuje 25 MB, Outlook 20 MB, wiele serwerów firmowych 10 MB.
- **Faktura PDF w załączniku: tak.** Wszystko powyżej 5 MB: **link do pobrania z tokenem
  czasowym**, nie załącznik.
- Nigdy nie załączaj `.zip`, `.html`, `.exe`, `.js` — filtry korporacyjne kasują takie
  wiadomości bez powiadomienia nadawcy ani odbiorcy.
- Nazwa pliku bez polskich znaków i bez spacji (patrz
  `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md`, RFC 2231).
- Załącznik zwiększa wagę wiadomości w ocenie antyspamowej. Wysyłka masowa z załącznikiem
  do listy = pewny spam.

## Śledzenie otwarć i kliknięć

**Otwarcia** mierzy się przezroczystym pikselem `<img src=".../open?id=...">`.

Dlaczego to jest zepsute w 2026:

- Apple Mail Privacy Protection (od iOS 15) pobiera **wszystkie** obrazy przez pośrednika
  z góry, niezależnie od tego, czy użytkownik otworzył wiadomość. Wskaźnik otwarć dla
  odbiorców Apple to fikcja — a to 40-55 % rynku poczty mobilnej.
- Gmail buforuje obrazy przez własne proxy — dostajesz otwarcie, ale bez adresu IP ani
  informacji o urządzeniu.
- Klienty domyślnie blokujące obrazy (Outlook desktop, część korporacyjnych) nigdy nie
  zgłoszą otwarcia mimo przeczytania.

Konsekwencja praktyczna: **nie podejmuj decyzji biznesowych na wskaźniku otwarć.** Nadaje się
tylko do porównania dwóch wariantów tej samej wysyłki w tym samym czasie (test A/B), i tylko
jako wskaźnik zastępczy. Do segmentacji „aktywni odbiorcy” używaj kliknięć i konwersji.

**Kliknięcia** mierzy się przez przepisanie linków na `https://sledzenie.przyklad.pl/c/<token>`.
Konsekwencje, o których trzeba wiedzieć:

- Domena śledząca **musi być twoja subdomena** z ważnym certyfikatem. Współdzielona domena
  dostawcy (`sendgrid.net`, `click.mailgun.net`) bywa na listach blokujących i obniża
  dostarczalność.
- Przepisany link ukrywa cel — użytkownicy i filtry to widzą. W wiadomościach dotyczących
  bezpieczeństwa (reset hasła, potwierdzenie logowania) **wyłącz przepisywanie linków**.
- Skanery bezpieczeństwa w firmach klikają wszystkie linki w wiadomości — generują fałszywe
  kliknięcia i mogą zużyć jednorazowy token. Tokeny resetu hasła muszą wytrzymać przedwczesne
  kliknięcie skanera (użycie dopiero po `POST`, nie po `GET`).

Aspekty prawne: piksel śledzący i przepisany link to **dostęp do informacji na urządzeniu
końcowym** — PKE art. 371 (dawny art. 173 Prawa telekomunikacyjnego) wymaga zgody analogicznej
do ciasteczkowej. Praktyka rynkowa jest luźniejsza, ale przy wysyłce do konsumentów w PL
bezpieczniej: informacja w polityce prywatności + zgoda w formularzu zapisu, a w wiadomościach
transakcyjnych **śledzenie wyłączone**.

## Odbicia i skargi przez webhooki

Bez obsługi zwrotnej twoja lista gnije, a reputacja z nią.

Zdarzenia, które musisz obsłużyć:

| Zdarzenie | Reakcja |
|---|---|
| `bounce` typu `Permanent` | wpis na listę wykluczeń **na stałe**, natychmiast |
| `bounce` typu `Transient` | licznik; po 5 w 7 dni → wykluczenie |
| `complaint` (kliknięcie „to spam”) | wykluczenie **globalne**, natychmiast, bez wyjątków |
| `reject` (dostawca odrzucił przed wysyłką, np. wirus) | alarm dla zespołu |
| `delivery` | zapis do dziennika, ewentualnie potwierdzenie w interfejsie |
| `rendering_failure` | błąd szablonu — alarm |

Odbiornik webhooka (FastAPI, SES przez SNS):

```python
import json, hmac, hashlib
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/webhooks/ses")
async def ses_webhook(request: Request):
    surowe = await request.body()
    koperta = json.loads(surowe)

    # SNS: potwierdzenie subskrypcji przy pierwszym podpięciu
    if koperta.get("Type") == "SubscriptionConfirmation":
        # zweryfikuj podpis SNS przed odwiedzeniem SubscribeURL
        await potwierdz_subskrypcje(koperta["SubscribeURL"])
        return {"ok": True}

    if not zweryfikuj_podpis_sns(koperta):
        raise HTTPException(status_code=403, detail="zły podpis")

    zdarzenie = json.loads(koperta["Message"])
    typ = zdarzenie["eventType"]

    if typ == "Bounce":
        b = zdarzenie["bounce"]
        trwale = b["bounceType"] == "Permanent"
        for odbiorca in b["bouncedRecipients"]:
            await zapisz_odbicie(
                adres=odbiorca["emailAddress"],
                trwale=trwale,
                kod=odbiorca.get("status"),
                diagnoza=odbiorca.get("diagnosticCode"),
            )
    elif typ == "Complaint":
        for odbiorca in zdarzenie["complaint"]["complainedRecipients"]:
            await wyklucz_na_stale(odbiorca["emailAddress"], powod="skarga")
    elif typ == "Delivery":
        await oznacz_doreczona(zdarzenie["mail"]["messageId"])

    return {"ok": True}
```

Reguły implementacji webhooka:

1. **Weryfikuj podpis.** Publiczny endpoint bez weryfikacji pozwala każdemu wykluczyć dowolny
   adres z twojej listy albo zafałszować statystyki. SES/SNS podpisuje certyfikatem, Resend
   i Postmark używają HMAC z sekretu, Mailgun HMAC-SHA256 z `timestamp` i `token`.
2. **Idempotencja.** Dostawcy powtarzają dostarczenie webhooka. Klucz: identyfikator zdarzenia
   dostawcy, `UNIQUE` w bazie.
3. **Odpowiadaj `200` szybko.** Ciężką pracę wrzuć do kolejki. Timeout webhooka u dostawcy to
   zwykle 5-10 s; przekroczenie = ponowienie = duplikaty.
4. **Zapisz surowe zdarzenie** przed przetworzeniem. Przy niejasnej diagnostyce dostarczalności
   będziesz chciał zobaczyć oryginał.

## Lista wykluczeń (suppression list)

Osobna tabela, sprawdzana **przed każdą wysyłką**, także transakcyjną:

```sql
CREATE TABLE wykluczenia (
  adres        citext PRIMARY KEY,
  powod        text   NOT NULL CHECK (powod IN ('twarde_odbicie','skarga','rezygnacja','reczne','miekkie_powtarzalne')),
  zrodlo       text,
  utworzono    timestamptz NOT NULL DEFAULT now(),
  wygasa       timestamptz              -- NULL = na zawsze
);
CREATE INDEX ON wykluczenia (utworzono);
```

Zasady:

- Twarde odbicie i skarga → `wygasa IS NULL`. Nigdy nie zdejmuj automatycznie.
- Rezygnacja z marketingu **nie blokuje** wiadomości transakcyjnych — trzymaj to jako osobny
  wymiar (`kanal`), inaczej po wypisaniu z newslettera klient nie dostanie faktury.
- Dostawcy prowadzą własne listy wykluczeń. **Twoja lista jest nadrzędna** — sprawdzaj u siebie,
  zanim wyślesz żądanie do API. Wysłanie do adresu na liście dostawcy zwykle nie kosztuje,
  ale liczy się do statystyk jakości.
- Ręczne zdjęcie z listy tylko na pisemny wniosek odbiorcy, z odnotowaniem.

## Rezygnacja z subskrypcji

Dla wiadomości marketingowych i subskrypcyjnych **obowiązkowe** (Google, Yahoo, Microsoft):

```
List-Unsubscribe: <https://przyklad.pl/rezygnacja?t=eyJhbGciOi...>, <mailto:rezygnacja+eyJhbGciOi@przyklad.pl>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

Wymagania RFC 8058:

- Adres HTTPS musi obsługiwać **`POST`**, nie tylko `GET`. Klient pocztowy wykonuje `POST`
  z ciałem `List-Unsubscribe=One-Click`.
- **Bez potwierdzania, bez logowania, bez „czy na pewno”.** Jedno żądanie = rezygnacja.
- Realizacja w **maksymalnie 2 dni** (wymóg Google). W praktyce: natychmiast.
- Nagłówek musi być podpisany DKIM-em, inaczej filtry mogą go zignorować.
- Widoczny link „Zrezygnuj” w treści wiadomości nadal obowiązkowy — nagłówek go nie zastępuje.

Endpoint:

```python
@router.post("/rezygnacja")
async def rezygnacja(t: str):
    try:
        dane = odczytaj_token(t, max_wiek_dni=365)   # podpisany token, nie identyfikator!
    except TokenNiewazny:
        return PlainTextResponse("OK", status_code=200)  # nie ujawniaj niczego
    await wyklucz(dane["adres"], kanal=dane["kanal"], powod="rezygnacja")
    return PlainTextResponse("OK", status_code=200)
```

Token musi być podpisany (HMAC/JWT), nie może być samym identyfikatorem odbiorcy — inaczej
zgadywanie identyfikatorów pozwala wypisać całą bazę.

## Zgody marketingowe — polskie PKE

Ustawa Prawo komunikacji elektronicznej obowiązuje **od 10 listopada 2024** i zastąpiła
rozproszone przepisy (art. 10 UŚUDE, art. 172 Prawa telekomunikacyjnego).

**Art. 398 PKE:** zakaz używania automatycznych systemów wywołujących i telekomunikacyjnych
urządzeń końcowych do marketingu bezpośredniego **bez uprzedniej zgody** abonenta lub
użytkownika końcowego. Dotyczy e-maila, SMS-a, połączenia telefonicznego i komunikatorów.

Konsekwencje praktyczne:

1. **Jedna zgoda PKE może pokryć to, co dawniej wymagało dwóch** (UŚUDE + Prawo tele.).
   W praktyce nadal zbieraj **osobno per kanał** (e-mail / SMS / telefon) — bo tak buduje się
   dowód i bo odbiorca może chcieć tylko jednego.
2. Zgoda musi być: uprzednia, dobrowolna, konkretna, świadoma, wyrażona **czynnym działaniem**.
   Domyślnie zaznaczony checkbox jest nieważny. Zgoda „przy okazji” regulaminu jest nieważna
   (brak dobrowolności — nie można jej uzależniać od świadczenia usługi).
3. **Ciężar dowodu jest po twojej stronie.** Zapisuj: adres, data i godzina (ze strefą),
   adres IP, treść klauzuli w brzmieniu z momentu zebrania (nie odsyłacz — pełny tekst),
   źródło (formularz, nazwa strony), sposób (single/double opt-in).
4. **Double opt-in** nie jest wymogiem ustawowym, ale to jedyny praktyczny dowód, że adres
   należy do osoby, która wyraziła zgodę. Stosuj zawsze.
5. Zgody zebrane przed 10.11.2024 pozostają ważne, jeśli spełniały ówczesne wymogi
   i są udokumentowane. Zrób audyt — brak dokumentacji = brak zgody.
6. **Kary:** Prezes UKE może nałożyć do **3 % przychodu z poprzedniego roku** albo
   **1 000 000 PLN** — zależnie od tego, co wyższe. Osobno RODO (do 20 mln EUR / 4 %) za
   przetwarzanie bez podstawy.
7. Rezygnacja musi być tak łatwa jak zgoda i realizowana niezwłocznie. Odnotuj ją w tym samym
   rejestrze co zgodę.

Model tabeli zgód:

```sql
CREATE TABLE zgody (
  id            bigserial PRIMARY KEY,
  adres         citext NOT NULL,
  kanal         text   NOT NULL CHECK (kanal IN ('email','sms','telefon')),
  tresc_klauzuli text  NOT NULL,           -- pełne brzmienie, nie odsyłacz
  wersja_klauzuli text NOT NULL,
  udzielona     timestamptz NOT NULL,
  ip            inet,
  user_agent    text,
  zrodlo        text NOT NULL,             -- "formularz newsletter, /kontakt"
  potwierdzona  timestamptz,               -- double opt-in
  wycofana      timestamptz,
  wycofana_jak  text
);
CREATE INDEX ON zgody (adres, kanal) WHERE wycofana IS NULL;
```

Marketing do adresów firmowych (`biuro@`, `kontakt@`) też wymaga zgody — PKE nie odróżnia
B2B od B2C w art. 398. Powszechne przekonanie, że „do firm można bez zgody”, jest błędne.

## HTML wiadomości e-mail

Klienty pocztowe renderują HTML jak przeglądarki z 2003 roku. Outlook na Windows do dziś
używa silnika Worda do renderowania (`mso`), a nie WebView.

### Reguły twarde

| Reguła | Co się stanie, jeśli złamiesz |
|---|---|
| Układ **tabelami**, nie `flex`/`grid` | Outlook rozłoży wszystko w pionową kolumnę |
| Style **inline** (`style="..."`) na każdym elemencie | Gmail usuwa `<style>` w wersji mobilnej i w części widoków; wiadomość traci całe formatowanie |
| Szerokość maksymalna **600 px** | szersze wiadomości ucinają się w panelu podglądu |
| Obrazy z `width`, `height` i `alt` jako atrybutami HTML | bez wymiarów układ skacze; bez `alt` przy blokowanych obrazach zostaje pustka |
| Brak `position`, `float` w Outlooku | ignorowane |
| Brak `background-image` bez zapasu | Outlook nie renderuje; użyj VML jako zapasu albo koloru tła |
| Brak zewnętrznych CSS i webfontów | nie ładują się; użyj stosu systemowego |
| Zawsze wersja `text/plain` | brak części tekstowej to punkty spamowe u każdego filtru |
| Zawsze `lang="pl"` i `<meta charset="utf-8">` | polskie znaki i czytniki ekranu |

### Szkielet, który działa

```html
<!DOCTYPE html>
<html lang="pl" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>Potwierdzenie zamówienia</title>
  <!--[if mso]>
  <xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
  <![endif]-->
  <style>
    /* wyłącznie jako uzupełnienie inline; Gmail może to usunąć */
    @media (prefers-color-scheme: dark) {
      .tlo   { background-color: #16181c !important; }
      .karta { background-color: #202329 !important; }
      .tekst { color: #e8eaed !important; }
    }
    @media only screen and (max-width: 600px) {
      .kolumna { display: block !important; width: 100% !important; }
    }
  </style>
</head>
<body class="tlo" style="margin:0;padding:0;background-color:#f4f5f7;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
    Zamówienie 2026/08/117 przyjęte do realizacji.
    &#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f5f7;">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" class="karta" width="600" cellpadding="0" cellspacing="0" border="0"
               style="width:600px;max-width:600px;background-color:#ffffff;border-radius:8px;">
          <tr>
            <td style="padding:32px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:16px;line-height:1.5;color:#1f2328;" class="tekst">
              <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;color:#1f2328;">Zamówienie przyjęte</h1>
              <p style="margin:0 0 16px;">Dzień dobry,</p>
              <p style="margin:0 0 24px;">przyjęliśmy zamówienie nr <strong>2026/08/117</strong>.</p>
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="background-color:#1f5fd0;border-radius:6px;">
                    <a href="https://przyklad.pl/zamowienia/117"
                       style="display:inline-block;padding:12px 24px;font-family:Arial,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;">
                      Zobacz zamówienie
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;font-size:12px;color:#5b636d;">
          DANACO sp. z o.o., ul. Przykładowa 1, 00-001 Warszawa, NIP 000-000-00-00
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
```

Elementy, których model zwykle nie pamięta:

- **Preheader** — ukryty tekst na początku `<body>`, wyświetlany w skrzynce po temacie.
  Ciąg `&#847;&zwnj;&nbsp;` powtórzony kilkanaście razy zapobiega dociąganiu treści z dalszej
  części wiadomości do podglądu.
- **`x-apple-disable-message-reformatting`** — bez tego Apple Mail sam skaluje wiadomość.
- **`<o:PixelsPerInch>96`** — bez tego Outlook przy skalowaniu 125 % rozjeżdża szerokości.
- **Przyciski budowane tabelą + `<a>` z `padding`**, nie `<button>`. `<button>` w e-mailu
  nie działa.
- `role="presentation"` na każdej tabeli układu — inaczej czytniki ekranu ogłaszają
  „tabela, 3 kolumny” przy każdym elemencie dekoracyjnym.

### Tryb ciemny

Trzy zachowania klientów:

1. **Nie robią nic** (Gmail web w części przypadków) — twoje kolory zostają.
2. **Respektują `prefers-color-scheme`** (Apple Mail, iOS Mail, Outlook macOS) — działa
   `@media`, ale tylko jeśli `<style>` przetrwał.
3. **Wymuszają własną inwersję** (Gmail Android, Outlook Windows) — zamieniają jasne tła
   na ciemne i tekst na jasny **wybiórczo**, często psując logo i przyciski.

Obrona:
- Logo w formacie PNG z przezroczystym tłem i jasną obwódką, żeby było czytelne na obu tłach.
- Nie polegaj na tekście czarnym na białym — używaj kontrastów, które działają po inwersji.
- Testuj w Gmailu na Androidzie; to najbardziej agresywny klient.
- `<meta name="color-scheme" content="light dark">` sygnalizuje, że sam obsługujesz tryb —
  część klientów wtedy nie wymusza inwersji.

### Dostępność

- Stosunek kontrastu tekstu do tła **≥ 4,5:1**.
- `alt` na każdym obrazie; obrazy dekoracyjne `alt=""`.
- Nie umieszczaj treści krytycznej **wyłącznie** w obrazie — Outlook domyślnie blokuje obrazy.
- Rozmiar tekstu podstawowego **≥ 14 px**, treści prawnych w stopce ≥ 12 px.
- Obszar klikalny przycisku **≥ 44 × 44 px**.
- Sensowna kolejność czytania — czytnik ekranu idzie po strukturze tabel od lewej do prawej,
  wiersz po wierszu.

## Testowanie dostarczalności

Przed pierwszą wysyłką produkcyjną, w tej kolejności:

1. **`mail-tester.com`** — wyślij na wygenerowany adres, sprawdź punktację (cel: 10/10)
   i rozpiskę: SPF, DKIM, DMARC, PTR, listy blokujące, reguły SpamAssassina, kompletność MIME.
2. **Własne skrzynki testowe** na: Gmail, Outlook.com, WP.pl, o2.pl, Onet, Interia, iCloud.
   Polscy dostawcy (Wirtualna Polska, Onet, Interia) mają własne filtry i bywają surowsi niż
   Gmail — nie pomijaj ich, jeśli klient działa w PL.
3. **„Pokaż oryginał” w Gmailu** — trzy `pass` w `Authentication-Results` i **zgodność domen**
   z `From:`.
4. **Renderowanie**: Litmus/Email on Acid (płatne, kompletne) albo ręcznie: Gmail web,
   Gmail Android, Outlook Windows (najgorszy), Apple Mail iOS, Thunderbird.
5. **Wersja tekstowa** — sprawdź, czy nie jest pusta i czy zawiera link do rezygnacji.
6. **`List-Unsubscribe`** — wyślij `POST` `curl`em na adres z nagłówka i sprawdź, czy adres
   trafia na listę wykluczeń.
7. **Odbicie** — wyślij na `nieistniejacy@gmail.com` i sprawdź, czy webhook zapisał twarde
   odbicie i czy adres trafił na listę wykluczeń.
8. **Symulacja skargi** — u dostawców jest zwykle adres testowy (SES: `complaint@simulator.
   amazonses.com`, `bounce@simulator.amazonses.com`, `suppressionlist@simulator.amazonses.com`).
   Użyj go, nie czekaj na prawdziwą skargę.

Adresy symulatora SES działają w piaskownicy i nie wliczają się do reputacji — to jedyny
bezpieczny sposób przetestowania całej ścieżki zwrotnej przed produkcją.
