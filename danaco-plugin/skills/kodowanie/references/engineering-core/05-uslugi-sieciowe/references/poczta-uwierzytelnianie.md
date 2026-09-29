# Uwierzytelnianie poczty: SPF, DKIM, DMARC, ARC, MTA-STS, TLS-RPT, BIMI

Stan zweryfikowany na sierpień 2026.

## Wymagania dostawców — stan faktyczny

### Google (Gmail)

Zasady z 1 lutego 2024 obowiązują nadal, ale **egzekucja się zaostrzyła**:

- Od listopada 2025 Gmail przeszedł z tymczasowych odroczeń (`421`) na **trwałe odrzucenia
  (`550`)** dla wiadomości, które nie przechodzą uwierzytelniania albo przekraczają próg skarg.
- W październiku 2025 wyłączono stare Postmaster Tools; wersja 2 pokazuje **binarny status
  zgodności** (przechodzisz / nie przechodzisz), bez półcieni.

| Wymóg | Każdy nadawca | Nadawca masowy (≥5000 wiad./dobę na adresy `@gmail.com`) |
|---|---|---|
| SPF **albo** DKIM | tak | — |
| SPF **i** DKIM | — | tak, oba |
| DMARC z rekordem (min. `p=none`) | nie | tak |
| Wyrównanie `From:` ze SPF **albo** DKIM | nie | tak |
| PTR (forward-confirmed reverse DNS) | tak | tak |
| TLS na połączeniu wychodzącym | tak | tak |
| Zgodność z RFC 5322 | tak | tak |
| Wskaźnik spamu w Postmaster Tools | < 0,30 % | **cel < 0,10 %**, twardy próg 0,30 % |
| Jednoklikowa rezygnacja (RFC 8058) | nie | tak, dla marketingu i subskrypcji; realizacja **≤ 2 dni** |

Liczenie „5000 dziennie”: raz przekroczony próg oznacza status nadawcy masowego **na stałe**.

ARC nie jest wymagany od nadawców. Jest wymagany od **pośredników** (listy dyskusyjne, bramki
przekazujące) — patrz sekcja ARC.

### Yahoo

Wymagania równoległe do Google, ta sama data startu (luty 2024), te same trzy filary:
uwierzytelnianie, jednoklikowa rezygnacja, wskaźnik skarg < 0,30 % (cel < 0,10 %). Yahoo
prowadzi klasyczną pętlę zwrotną (Complaint Feedback Loop) i wysyła raporty ARF — zarejestruj się.

### Microsoft (Outlook.com, Hotmail.com, Live.com)

Wymagania dla nadawców wysokowolumenowych obowiązują **od 5 maja 2025** i w 2026 są w pełni
egzekwowane. Próg: ≥5000 wiadomości na dobę na adresy w domenach konsumenckich Microsoftu.
Wymagane: SPF, DKIM, DMARC (min. `p=none`) z wyrównaniem, funkcjonalna rezygnacja, poprawny PTR,
niskie wskaźniki skarg.

Zapowiedź z 29 kwietnia 2025 zmieniła sankcję: zamiast odrzucenia niezgodne wiadomości trafiają
do folderu Junk. `[niepotwierdzone: czy Microsoft przeszedł już z kierowania do Junk na twarde
odrzucanie — sprawdź aktualny wpis na blogu Microsoft Defender for Office 365]`

### Apple (iCloud Mail)

Apple nie opublikował własnego progu wolumenowego analogicznego do Google/Yahoo/Microsoft.
Wymaga SPF/DKIM, respektuje DMARC, wyświetla BIMI. `[niepotwierdzone: formalne wymagania Apple
dla nadawców masowych — brak oficjalnego dokumentu odpowiadającego wytycznym Google]`

### Wniosek operacyjny

Jedna konfiguracja spełnia wszystkich: **SPF + DKIM + DMARC z wyrównaniem, PTR, TLS,
`List-Unsubscribe` z jednym kliknięciem, wskaźnik skarg poniżej 0,1 %.**

## SPF

Rekord `TXT` w korzeniu domeny, która występuje w **kopercie** (`MAIL FROM`).

```dns
przyklad.pl.  IN TXT "v=spf1 include:_spf.google.com include:amazonses.com ip4:203.0.113.7 -all"
```

### Mechanizmy

| Mechanizm | Znaczenie | Kosztuje odwołanie DNS |
|---|---|---|
| `ip4:` / `ip6:` | dosłowny adres lub sieć CIDR | nie |
| `a` | rekordy A/AAAA domeny | tak (1) |
| `mx` | adresy serwerów MX domeny | tak (1 + po jednym na każdy MX) |
| `include:` | dołącz politykę innej domeny | tak (1 + wszystko wewnątrz) |
| `exists:` | test istnienia rekordu A | tak (1) |
| `redirect=` | zastąp całą politykę inną | tak (1) |
| `ptr` | **zdeprecjonowany, nie używaj** | tak, drogo |
| `all` | dopasowuje wszystko; zawsze ostatni | nie |

Kwalifikatory: `+` przepuść (domyślny), `~` softfail, `-` fail, `?` neutral.

### Limit 10 odwołań DNS — najczęstsza przyczyna awarii

RFC 7208 §4.6.4: przetwarzanie rekordu SPF nie może wywołać **więcej niż 10 zapytań DNS**.
Przekroczenie daje wynik `permerror`, który dla DMARC liczy się jak brak SPF.

`include:_spf.google.com` sam zużywa 4 odwołania (rozwija się na trzy podrekordy).
`include:spf.protection.outlook.com` — 2. `include:amazonses.com` — 1. `include:sendgrid.net` — 3.
Trzech dostawców i `mx` i już jesteś na granicy.

Sprawdzenie:

```bash
dig +short TXT przyklad.pl | grep spf1
# licznik odwołań — usługa online albo:
python3 -c "import spf,sys; print(spf.check2(i='203.0.113.7', s='a@przyklad.pl', h='mail.przyklad.pl'))"
```

Naprawa, w kolejności:

1. Usuń `include:` dostawców, z których już nie korzystasz. Zwykle to wystarcza.
2. Zamień `mx` i `a` na dosłowne `ip4:` — poczta przychodząca (MX) prawie nigdy nie jest
   nadawcą, więc `mx` w SPF jest zwykle zbędny.
3. Dopiero potem sięgaj po „spłaszczanie” (flattening) — rozwinięcie `include:` na listę `ip4:`.
   **Spłaszczanie jest pułapką:** dostawca zmienia swoje adresy bez uprzedzenia i twój SPF
   przestaje obejmować jego serwery. Jeśli spłaszczasz, rób to automatem odświeżanym codziennie,
   nigdy ręcznie raz.

### `~all` czy `-all`

- `~all` (softfail) — niedopasowane źródła oznaczone, ale nie odrzucane.
- `-all` (fail, hardfail) — niedopasowane źródła do odrzucenia.

**Zaczynaj od `~all`, kończ na `-all`.** Przejście na `-all` dopiero gdy raporty DMARC przez
2-4 tygodnie nie pokazują legalnych źródeł spoza rekordu. Przy DMARC w trybie `p=reject`
różnica między `~all` a `-all` jest w praktyce niewielka — DMARC i tak zdecyduje — ale `-all`
pomaga przy odbiorcach, którzy patrzą tylko na SPF.

### Typowe błędy

| Błąd | Skutek |
|---|---|
| Dwa rekordy `TXT` ze `spf1` na jednej nazwie | `permerror`, SPF nie działa w ogóle. Musi być dokładnie jeden |
| Rekord typu `SPF` (99) zamiast `TXT` | ignorowany; typ `SPF` wycofano w RFC 7208 |
| SPF na subdomenie odziedziczony „z domeny nadrzędnej” | SPF **nie dziedziczy**. Każda nadająca subdomena potrzebuje własnego rekordu |
| Brak SPF na subdomenach, z których nikt nie nadaje | podszywanie się. Dodaj `"v=spf1 -all"` na `*.przyklad.pl` oraz na domenach zaparkowanych |
| Poleganie na SPF przy przekierowaniu poczty | SPF **zawsze** się psuje przy forwardzie — dlatego DKIM jest ważniejszy |
| `+all` | otwierasz domenę dla dowolnego nadawcy. Nigdy |

## DKIM

Podpis kryptograficzny nagłówków i treści, wstawiany przez serwer nadający, weryfikowany
kluczem publicznym z DNS. Odporny na przekierowanie (dopóki treść i podpisane nagłówki się
nie zmienią).

### Rekord

```dns
selektor2026a._domainkey.przyklad.pl.  IN TXT ( "v=DKIM1; k=rsa; t=s; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy8..." 
                                                "...reszta_klucza_publicznego_base64IDAQAB" )
```

Klucz 2048-bitowy nie mieści się w jednym łańcuchu TXT (limit 255 znaków) — musi być rozbity
na kilka łańcuchów w cudzysłowach w jednym rekordzie. Panel DNS, który tego nie umie (część
tanich hostingów), wymaga wklejenia klucza 1024-bitowego albo zmiany dostawcy DNS.

Nagłówek w wysłanej wiadomości:

```
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=przyklad.pl;
 s=selektor2026a; t=1754300000; bh=...; 
 h=From:To:Subject:Date:Message-ID:MIME-Version:Content-Type;
 b=...
```

### Parametry, które mają znaczenie

| Parametr | Wartość zalecana | Uzasadnienie |
|---|---|---|
| Długość klucza | **2048 bit RSA** | 1024 to minimum akceptowane przez Gmaila, ale odbiorcy zaczynają je oznaczać jako słabe. 4096 nie mieści się wygodnie w DNS i nie daje realnej korzyści |
| `a=` | `rsa-sha256` | `ed25519-sha256` (RFC 8463) jest krótszy i szybszy, ale weryfikacja u odbiorców nadal niepełna — publikuj **równolegle** z RSA, nie zamiast |
| `c=` (kanonikalizacja) | `relaxed/relaxed` | `simple/simple` łamie się przy najmniejszej zmianie białych znaków po drodze |
| `h=` | `From` obowiązkowo, dalej `To`, `Subject`, `Date`, `Message-ID`, `MIME-Version`, `Content-Type` | **nie podpisuj** `Received`, `Return-Path`, `List-*` — pośrednicy je zmieniają i podpis pęka |
| `l=` (długość treści) | **nie używaj** | pozwala doklejać treść za podpisaną częścią; atak „DKIM body length” |
| `t=s` w rekordzie | tak, jeśli nie podpisujesz subdomen tym kluczem | zabrania używania klucza dla subdomen |

Podpisywanie `From` jest obowiązkowe (RFC 6376). Podpis bez `From` w `h=` jest nieważny.

### Selektory i rotacja

Selektor to nazwa klucza. Pozwala mieć wiele kluczy naraz — jeden na dostawcę, jeden na
środowisko.

Konwencja: `<rok><litera>` albo `<usluga><rok>`, np. `ses2026a`, `postfix2026b`.
Nie używaj `default` ani `mail` — utrudnia rotację i kolejny dostawca zażąda tej samej nazwy.

Procedura rotacji (bez przerwy w podpisach):

1. Wygeneruj nową parę, opublikuj `selektor2026b._domainkey` w DNS.
2. Odczekaj **co najmniej 2× TTL** rekordu (przy TTL 3600 s → 2 h), żeby rekord się rozszedł.
3. Przełącz podpisywanie na nowy selektor.
4. Zostaw stary rekord w DNS przez **co najmniej 7 dni** — wiadomości w kolejkach odbiorców
   i raporty DMARC nadal się do niego odwołują.
5. Usuń stary rekord. Jeśli chcesz zaznaczyć unieważnienie, opublikuj `v=DKIM1; p=` (pusty `p`)
   zamiast kasować.

Rotuj co 6-12 miesięcy. Rotuj natychmiast po podejrzeniu wycieku klucza prywatnego.

### Generowanie klucza

```bash
# Rspamd / dowolny stos
openssl genrsa -out /var/lib/rspamd/dkim/przyklad.pl.selektor2026a.key 2048
chmod 600 /var/lib/rspamd/dkim/przyklad.pl.selektor2026a.key
chown _rspamd:_rspamd /var/lib/rspamd/dkim/przyklad.pl.selektor2026a.key

openssl rsa -in /var/lib/rspamd/dkim/przyklad.pl.selektor2026a.key -pubout -outform PEM \
  | sed '1d;$d' | tr -d '\n'
# wynik wklej jako p= w rekordzie TXT

# weryfikacja po publikacji
dig +short TXT selektor2026a._domainkey.przyklad.pl
```

### Co psuje DKIM

| Przyczyna | Mechanizm |
|---|---|
| Lista dyskusyjna dokleja stopkę | zmienia treść → `bh=` nie pasuje → podpis nieważny |
| Lista zmienia `Subject` na `[lista] Temat` | podpisany nagłówek się zmienił |
| Brama antyspamowa dopisuje `[SPAM]` albo skanuje i przepakowuje załączniki | zmiana treści |
| Serwer po drodze konwertuje kodowanie (8bit → QP) | zmiana bajtów treści |
| Autoresponder cytuje i przesyła dalej | to nowa wiadomość, stary podpis nieistotny |

Na to jest ARC. Nadawca nic tu nie naprawi — może tylko nie podpisywać nagłówków zmienianych
przez listy i pilnować, żeby jego własna infrastruktura nie modyfikowała treści po podpisaniu
(kolejność w Postfiksie: `milter` podpisujący musi działać **jako ostatni**, po wszystkich
modyfikatorach treści).

## DMARC

Wiąże `From:` z wynikiem SPF/DKIM, mówi odbiorcy co robić przy niepowodzeniu i żąda raportów.

```dns
_dmarc.przyklad.pl.  IN TXT "v=DMARC1; p=none; rua=mailto:dmarc-agg@przyklad.pl; ruf=mailto:dmarc-forensic@przyklad.pl; fo=1; adkim=r; aspf=r; pct=100"
```

### Znaczniki

| Znacznik | Wartości | Uwagi |
|---|---|---|
| `v` | `DMARC1` | obowiązkowy, pierwszy |
| `p` | `none` / `quarantine` / `reject` | polityka dla domeny organizacyjnej |
| `sp` | jw. | polityka dla subdomen; **bez `sp` subdomeny dziedziczą `p`** |
| `rua` | `mailto:` | raporty zbiorcze (agregowane), codziennie, XML w gzip |
| `ruf` | `mailto:` | raporty szczegółowe (forensic); **większość dużych dostawców ich nie wysyła** ze względu na RODO |
| `fo` | `0`/`1`/`d`/`s` | `1` = raportuj, gdy zawiedzie SPF **lub** DKIM (nie tylko oba) |
| `adkim` / `aspf` | `r` (relaxed) / `s` (strict) | `r` pozwala na zgodność na poziomie domeny organizacyjnej (subdomena pasuje do domeny) |
| `pct` | 1-100 | procent wiadomości objętych polityką; użyteczne przy stopniowaniu |
| `rf`, `ri` | — | format i interwał raportów; zostaw domyślne |

### Wyrównanie (alignment) — sedno DMARC

DMARC przechodzi, gdy **przynajmniej jedno** jest prawdą:

- SPF przeszedł **i** domena z koperty jest wyrównana z domeną z `From:`, albo
- DKIM przeszedł **i** `d=` podpisu jest wyrównane z domeną z `From:`.

Wyrównanie `relaxed`: wystarczy zgodność domeny organizacyjnej.
`From: biuro@przyklad.pl` + `d=mail.przyklad.pl` → **przechodzi** przy `adkim=r`, **nie
przechodzi** przy `adkim=s`.

To dlatego wysyłka przez dostawcę z jego domeny w kopercie (`bounces.sendgrid.net`) nie daje
wyrównania SPF — i cała nadzieja jest w DKIM podpisanym twoją domeną. Skonfiguruj u dostawcy
**własną domenę zwrotną** (custom return-path / custom MAIL FROM, zwykle `bounce.przyklad.pl`
z rekordem CNAME albo MX u dostawcy), żeby mieć oba filary.

### Raporty zbiorcze — jak je czytać

XML w załączniku, jedna sekcja `<record>` na źródłowy adres IP:

```xml
<record>
  <row>
    <source_ip>203.0.113.7</source_ip>
    <count>412</count>
    <policy_evaluated>
      <disposition>none</disposition>
      <dkim>pass</dkim>
      <spf>fail</spf>
    </policy_evaluated>
  </row>
  <identifiers><header_from>przyklad.pl</header_from></identifiers>
  <auth_results>
    <dkim><domain>przyklad.pl</domain><selector>ses2026a</selector><result>pass</result></dkim>
    <spf><domain>amazonses.com</domain><result>pass</result></spf>
  </auth_results>
</record>
```

Uwaga na pułapkę czytania: `<spf><result>pass</result>` w `auth_results` znaczy „SPF technicznie
przeszedł dla domeny `amazonses.com`”, ale `policy_evaluated/spf = fail` znaczy „nie było
wyrównania z `From:`”. **Liczy się `policy_evaluated`.**

Nie parsuj tego ręcznie na produkcji — kieruj `rua` do usługi analitycznej (Postmark DMARC
Digests jest bezpłatny, dmarcian/Red Sift/Valimail płatne) albo do własnego parsera
(`parsedmarc` w Pythonie).

Adres w `rua` w innej domenie niż raportowana wymaga rekordu autoryzacji po stronie odbiorcy
raportów:
```dns
przyklad.pl._report._dmarc.raporty.pl.  IN TXT "v=DMARC1"
```
Bez tego dostawcy nie wyślą raportów. To najczęstsza przyczyna „mamy DMARC, ale nie dostajemy
raportów”.

### Wdrożenie etapowe

| Etap | Rekord | Czas trwania | Kryterium przejścia dalej |
|---|---|---|---|
| 1. Nasłuch | `p=none; rua=...; fo=1` | 2-4 tygodnie | znasz wszystkie źródła wysyłki z raportów |
| 2. Naprawa | bez zmian w `p` | do skutku | każde legalne źródło ma DKIM podpisany twoją domeną i wyrównanie |
| 3. Kwarantanna cząstkowa | `p=quarantine; pct=25` | 1 tydzień | brak zgłoszeń od użytkowników, wolumen `fail` bez zmian |
| 4. Kwarantanna pełna | `p=quarantine; pct=100` | 2 tygodnie | jw. |
| 5. Odrzucanie | `p=reject` | docelowo | — |

Nie skracaj etapu 1. Przejście od razu na `p=reject` przy nieznanych źródłach kasuje pocztę
z systemu kadrowego, z drukarki, z CRM-u i z newslettera — i dowiesz się o tym od prezesa.

Osobno: **subdomeny**. Jeśli nadajesz tylko z `przyklad.pl`, ustaw `sp=reject` od razu, nawet
przy `p=none` — nikt legalnie nie nadaje z twoich subdomen, więc nie masz co psuć.

### Kiedy DMARC szkodzi

`p=reject` na domenie, z której pracownicy piszą na listy dyskusyjne, powoduje odrzucanie ich
wiadomości u wszystkich subskrybentów listy. Rozwiązanie: osobna domena/subdomena do takich
zastosowań albo lista przepisująca `From:` na własny adres (większość Mailmanów 3 robi to
automatycznie przy wykryciu `p=reject`).

## ARC (RFC 8617)

Pośrednik (lista dyskusyjna, brama przekazująca, filtr antyspamowy w chmurze), który modyfikuje
wiadomość, dołącza trzy nagłówki:

```
ARC-Seal: i=1; a=rsa-sha256; d=lista.przyklad.pl; s=arc2026; cv=none; b=...
ARC-Message-Signature: i=1; a=rsa-sha256; d=lista.przyklad.pl; s=arc2026; h=From:To:Subject...; b=...
ARC-Authentication-Results: i=1; lista.przyklad.pl; spf=pass smtp.mailfrom=przyklad.pl; dkim=pass header.d=przyklad.pl; dmarc=pass
```

Odbiorca końcowy widzi zepsuty DKIM oryginału, ale może odczytać z łańcucha ARC, że **przed**
modyfikacją wiadomość była uwierzytelniona — i zaufać temu, jeśli ufa pośrednikowi.

Konsekwencje praktyczne:

- Jesteś nadawcą → ARC cię nie dotyczy, nic nie konfigurujesz.
- Prowadzisz listę dyskusyjną, bramę `@absolwenci.uczelnia.pl` przekazującą pocztę dalej albo
  usługę przesyłania → **musisz** podpisywać ARC, inaczej przekazywana poczta ginie u odbiorców
  z `p=reject`.
- Rspamd podpisuje ARC modułem `arc` (konfiguracja bliźniacza do `dkim_signing`).
  Postfix samodzielnie tego nie robi; potrzebny milter (Rspamd albo OpenARC).
- ARC to **zaufanie do pośrednika**, nie dowód. Gmail honoruje ARC od znanych pośredników;
  nowy, nieznany podpisujący nie zyska od razu nic.

## MTA-STS (RFC 8461) i TLS-RPT (RFC 8460)

SMTP domyślnie używa TLS oportunistycznie: jeśli STARTTLS zawiedzie, wysyła jawnym tekstem.
MTA-STS to deklaracja „do mnie zawsze przez TLS, z ważnym certyfikatem, na te MX-y”.

Trzy elementy — wszystkie muszą istnieć:

1. Rekord DNS:
```dns
_mta-sts.przyklad.pl.  IN TXT "v=STSv1; id=20260804120000"
```
`id` zmieniasz **przy każdej zmianie polityki** — po nim odbiorcy poznają, że mają pobrać
plik na nowo.

2. Plik pod HTTPS na `https://mta-sts.przyklad.pl/.well-known/mta-sts.txt`, serwowany jako
`text/plain`, z **ważnym certyfikatem dla `mta-sts.przyklad.pl`**:
```
version: STSv1
mode: enforce
mx: mx1.przyklad.pl
mx: mx2.przyklad.pl
max_age: 604800
```

3. Rekord TLS-RPT (raporty o niepowodzeniach TLS):
```dns
_smtp._tls.przyklad.pl.  IN TXT "v=TLSRPTv1; rua=mailto:tlsrpt@przyklad.pl"
```

Tryby: `none` (wyłączone), `testing` (raportuj, nie blokuj), `enforce` (blokuj przy
niepowodzeniu). **Zawsze zaczynaj od `testing`** i przejdź na `enforce` po tygodniu czystych
raportów TLS-RPT.

Pułapki:
- Wygaśnięcie certyfikatu na `mta-sts.przyklad.pl` przy `mode: enforce` = **cała poczta
  przychodząca odbita** u nadawców respektujących MTA-STS (Google, Microsoft, Yahoo). To realny
  sposób na wyłączenie sobie firmy.
- Zmiana MX bez aktualizacji pliku i `id` = to samo.
- `max_age` 604800 (7 dni) to rozsądny start; docelowo 1209600 (14 dni). Krótszy = szybsza
  reakcja na zmiany, dłuższy = lepsza ochrona przed atakiem na DNS.

## DANE (RFC 7672)

Alternatywa dla MTA-STS: rekord `TLSA` w DNS przypina certyfikat serwera MX. **Wymaga DNSSEC
na całej ścieżce delegacji.**

```dns
_25._tcp.mx1.przyklad.pl.  IN TLSA 3 1 1 <sha256-klucza-publicznego>
```

Pola: użycie (3 = DANE-EE, przypnij certyfikat serwera), selektor (1 = klucz publiczny),
typ dopasowania (1 = SHA-256). Kombinacja `3 1 1` jest standardem dla SMTP.

| | MTA-STS | DANE |
|---|---|---|
| Wymaga DNSSEC | nie | **tak, bezwzględnie** |
| Wymaga HTTPS i certyfikatu WWW | tak | nie |
| Wsparcie u dużych dostawców | Google, Microsoft, Yahoo | Microsoft (od 2024), część europejskich; Google **nie** wysyła z DANE |
| Ryzyko przy odnowieniu certyfikatu | niskie | wysokie — trzeba aktualizować TLSA przed zmianą klucza |
| Popularność w Polsce | rosnąca | niszowa poza operatorami |

Praktyka 2026: **wdrażaj MTA-STS**. DANE dokładaj tylko, gdy i tak masz DNSSEC i automat
aktualizujący TLSA z odnawianiem certyfikatu (np. `dehydrated` + hook, albo Stalwart, który
obsługuje DANE natywnie). Zrobienie DANE ręcznie prawie na pewno skończy się awarią przy
kolejnym odnowieniu Let's Encrypt (co 60 dni albo częściej).

## BIMI

Logo nadawcy w interfejsie skrzynki. Stan 2026:

Wymagania łącznie:
1. DMARC **na poziomie egzekucji**: `p=quarantine` lub `p=reject` (przy `pct=100`). `p=none`
   nie kwalifikuje.
2. SPF lub DKIM przechodzące z wyrównaniem.
3. Logo w formacie **SVG Tiny 1.2 Portable/Secure (SVG Tiny PS)** — kwadratowe, bez skryptów,
   bez zewnętrznych odwołań, z `<title>`, tło jednolite, plik zwykle < 32 kB.
4. Certyfikat: **VMC** (Verified Mark Certificate) albo **CMC** (Common Mark Certificate).
5. Rekord DNS:
```dns
default._bimi.przyklad.pl.  IN TXT "v=BIMI1; l=https://przyklad.pl/bimi/logo.svg; a=https://przyklad.pl/bimi/vmc.pem"
```

VMC vs CMC:

| | VMC | CMC |
|---|---|---|
| Wymaga zarejestrowanego znaku towarowego | tak | **nie** |
| Warunek zastępczy | — | logo publicznie widoczne na twojej domenie od **≥12 miesięcy**, weryfikowane przez archiwum internetu |
| Niebieski znacznik weryfikacji w Gmailu | tak | nie |
| Wsparcie | Gmail, Yahoo, Apple Mail | Gmail (opcja wprowadzona na początku 2025), zakres u pozostałych węższy |
| Wydawcy | DigiCert, Entrust | ci sami |
| Koszt roczny | rząd kilku tysięcy PLN | niższy, ale nadal płatny |

Kolejność: znak towarowy (jeśli w ogóle, procedura w UPRP/EUIPO trwa miesiącami) → DMARC na
egzekucji → certyfikat (wydanie 7-10 dni roboczych po spełnieniu DMARC) → rekord BIMI.

BIMI to marketing, nie bezpieczeństwo. Nie zaczynaj od niego. Jest natomiast **dobrym pretekstem
biznesowym**, żeby dokończyć DMARC do `p=reject`.

## Rekordy do wklejenia — komplet dla nowej domeny nadawczej

Domena: `przyklad.pl`. Poczta firmowa u dostawcy (tu: Google Workspace), transakcyjna z aplikacji
przez Amazon SES z subdomeny `powiadomienia.przyklad.pl`, marketing przez osobną subdomenę
`wiadomosci.przyklad.pl`.

```dns
; ---- MX poczty firmowej ----
przyklad.pl.                     3600 IN MX 1 smtp.google.com.

; ---- SPF domeny głównej (koperta poczty firmowej) ----
przyklad.pl.                     3600 IN TXT "v=spf1 include:_spf.google.com -all"
;   4 odwołania DNS z include Google; zostaje 6 zapasu

; ---- DKIM poczty firmowej (klucz z panelu Workspace) ----
google._domainkey.przyklad.pl.   3600 IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBg...IDAQAB"

; ---- DMARC: start w trybie nasłuchu, subdomeny od razu twardo ----
_dmarc.przyklad.pl.              3600 IN TXT "v=DMARC1; p=none; sp=reject; rua=mailto:dmarc@przyklad.pl; fo=1; adkim=r; aspf=r; pct=100"
;   po 2-4 tygodniach czystych raportów: p=quarantine; potem p=reject

; ---- Subdomena transakcyjna ----
powiadomienia.przyklad.pl.       3600 IN TXT "v=spf1 include:amazonses.com -all"
ses2026a._domainkey.powiadomienia.przyklad.pl. 3600 IN CNAME ses2026a.dkim.amazonses.com.
_dmarc.powiadomienia.przyklad.pl. 3600 IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc@przyklad.pl"
;   custom MAIL FROM u dostawcy — daje wyrównanie SPF:
bounce.powiadomienia.przyklad.pl. 3600 IN MX 10 feedback-smtp.eu-central-1.amazonses.com.
bounce.powiadomienia.przyklad.pl. 3600 IN TXT "v=spf1 include:amazonses.com -all"

; ---- Subdomena marketingowa (osobna reputacja!) ----
wiadomosci.przyklad.pl.          3600 IN TXT "v=spf1 include:sendgrid.net -all"
s1._domainkey.wiadomosci.przyklad.pl. 3600 IN CNAME s1.domainkey.uXXXXXX.wl.sendgrid.net.
s2._domainkey.wiadomosci.przyklad.pl. 3600 IN CNAME s2.domainkey.uXXXXXX.wl.sendgrid.net.
_dmarc.wiadomosci.przyklad.pl.   3600 IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc@przyklad.pl"

; ---- MTA-STS + TLS-RPT (dla poczty PRZYCHODZĄCEJ) ----
_mta-sts.przyklad.pl.            3600 IN TXT "v=STSv1; id=20260804120000"
mta-sts.przyklad.pl.             3600 IN A    203.0.113.20
_smtp._tls.przyklad.pl.          3600 IN TXT "v=TLSRPTv1; rua=mailto:tlsrpt@przyklad.pl"

; ---- Domeny i subdomeny, z których NIKT nie nadaje ----
*.przyklad.pl.                   3600 IN TXT "v=spf1 -all"
_dmarc.stara-domena.pl.          3600 IN TXT "v=DMARC1; p=reject; sp=reject; rua=mailto:dmarc@przyklad.pl"
stara-domena.pl.                 3600 IN TXT "v=spf1 -all"
```

Rekord odwrotny (PTR) ustawia się u operatora adresu IP, nie w swoim DNS. Musi być zgodność
w obie strony (FCrDNS): `PTR 203.0.113.7 → mail.przyklad.pl` **oraz** `A mail.przyklad.pl →
203.0.113.7`.

## Kolejność wdrażania nowej domeny nadawczej

1. Kup domenę **z wyprzedzeniem**. Domena młodsza niż 30 dni jest traktowana podejrzliwie przez
   wszystkie filtry. Miesiąc odstoju to minimum.
2. Postaw stronę WWW pod domeną. Domena bez strony = sygnał spamerski.
3. Rekordy: MX, SPF, DKIM, DMARC `p=none` + `sp=reject`, PTR.
4. Skonfiguruj `abuse@` i `postmaster@` — muszą przyjmować i być czytane.
5. Zarejestruj się w Google Postmaster Tools (v2), Microsoft SNDS/JMRP, Yahoo CFL.
6. Wyślij pierwsze wiadomości **do własnych skrzynek** na Gmailu, Outlooku, WP, Onecie, Interii.
   Sprawdź „Pokaż oryginał” — trzy `pass` w `Authentication-Results`.
7. Rozgrzewanie IP/domeny (niżej).
8. Po 2-4 tygodniach raportów DMARC: `p=quarantine`, potem `p=reject`.
9. MTA-STS w `testing`, po tygodniu `enforce`.
10. BIMI, jeśli w ogóle.

## Rozgrzewanie adresu IP i domeny

Nowy adres IP nie ma reputacji. Wysłanie 50 000 wiadomości pierwszego dnia daje blokadę,
z której wychodzi się tygodniami.

Harmonogram wyjściowy (dobowa liczba wiadomości; skaluj proporcjonalnie do docelowego wolumenu):

| Dzień | Wiadomości/dobę |
|---|---|
| 1-2 | 50 |
| 3-4 | 200 |
| 5-7 | 500 |
| 8-10 | 2 000 |
| 11-14 | 5 000 |
| 15-18 | 15 000 |
| 19-24 | 40 000 |
| 25-30 | 100 000 |

Zasady:
- **Skaluj maksymalnie ×2 na dobę.** Skok ×10 unieważnia rozgrzewanie.
- Zacznij od najaktywniejszych odbiorców (ci, którzy otwierali w ostatnich 30 dniach). Wysoki
  współczynnik otwarć i odpowiedzi buduje reputację najszybciej.
- Rozgrzewaj osobno per dostawcę odbiorcy — Gmail, Microsoft i Yahoo prowadzą niezależne
  reputacje. Rozłóż wolumen proporcjonalnie do udziału w liście.
- Przy skokach wskaźnika odbić > 2 % albo skarg > 0,1 % **cofnij się o dwa dni** i zatrzymaj się
  na tym poziomie na 3 doby.
- Domena i IP rozgrzewają się osobno. Zmiana dostawcy przy zachowaniu domeny = rozgrzewanie IP
  od zera, ale krótsze, bo reputacja domeny zostaje.
- Przy dostawcach z pulą współdzieloną (SES domyślnie, SendGrid w niższych planach) IP jest
  wspólne i rozgrzane — rozgrzewasz tylko domenę. Dedykowane IP ma sens od ~100 tys. wiadomości
  miesięcznie; poniżej tego wolumenu dedykowane IP **szkodzi**, bo nie generuje ruchu
  wystarczającego do utrzymania reputacji.

## Szybka diagnostyka „maile trafiają do spamu”

W tej kolejności, nie inaczej:

```bash
# 1. Czy uwierzytelnianie w ogóle przechodzi?
#    Wyślij na własny Gmail, "Pokaż oryginał", szukaj:
#    spf=pass  dkim=pass  dmarc=pass  — i CZY DOMENY SIĘ ZGADZAJĄ z From:

# 2. Rekordy
dig +short TXT przyklad.pl                       # SPF
dig +short TXT selektor._domainkey.przyklad.pl   # DKIM
dig +short TXT _dmarc.przyklad.pl                # DMARC
dig +short -x 203.0.113.7                        # PTR
dig +short A $(dig +short -x 203.0.113.7 | sed 's/\.$//')  # FCrDNS

# 3. Listy blokujące
for bl in zen.spamhaus.org bl.spamcop.net b.barracudacentral.org dnsbl.sorbs.net; do
  echo -n "$bl: "; dig +short 7.113.0.203.$bl A || echo "czysto"
done

# 4. Postmaster Tools (Gmail) — status zgodności, wskaźnik spamu, reputacja domeny/IP
# 5. mail-tester.com — punktacja SpamAssassin + kompletność nagłówków
# 6. Treść: stosunek tekstu do obrazów, skracacze linków (bit.ly = punkty karne),
#    załączniki .zip/.html, słowa-wyzwalacze, brak wersji text/plain
```

Kolejność ma znaczenie: 90 % przypadków „trafiamy do spamu” to punkty 1-2, a nie treść.
Optymalizowanie treści przy zepsutym DMARC to strata czasu.
