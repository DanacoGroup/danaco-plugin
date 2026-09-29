# Protokoły poczty: SMTP, IMAP, POP3, MIME, odbicia

Stan na sierpień 2026. Wersje: Postfix 3.11.5 (6.07.2026), Dovecot CE 2.4.4 (12.05.2026).

## Model: trzy warstwy, które model myli

| Warstwa | Kto ją widzi | Gdzie żyje | Przykład |
|---|---|---|---|
| Koperta (envelope) | serwery SMTP | polecenia `MAIL FROM` / `RCPT TO` | `MAIL FROM:<bounce+abc@mail.firma.pl>` |
| Nagłówki | użytkownik i filtry | pierwsza część treści wiadomości | `From: Biuro <biuro@firma.pl>` |
| Treść MIME | użytkownik | po pustej linii za nagłówkami | `text/html`, załączniki |

Konsekwencje, które psują wdrożenia:

- **Koperta i nagłówek `From:` to dwa różne adresy i tak ma być.** SPF sprawdza kopertę
  (`MAIL FROM`, zwane też Return-Path / RFC5321.MailFrom). DMARC sprawdza nagłówek `From:`
  (RFC5322.From). Wyrównanie (alignment) DMARC polega właśnie na porównaniu tych dwóch.
- **Odbicia (bounce) wracają na adres z koperty, nie na `From:`.** Jeśli w kopercie
  wstawisz `noreply@`, do której nikt nie zagląda, stracisz całą informację o twardych
  odbiciach i po miesiącu wysyłki twoja reputacja będzie w ruinie.
- `Return-Path:` w odebranej wiadomości jest dopisywany przez serwer docelowy z koperty.
  Nadawca go nie ustawia — ustawia kopertę.

## SMTP: przebieg sesji

```
S: 220 mx.przyklad.pl ESMTP Postfix
C: EHLO mail.firma.pl
S: 250-mx.przyklad.pl
S: 250-PIPELINING
S: 250-SIZE 52428800
S: 250-STARTTLS
S: 250-ENHANCEDSTATUSCODES
S: 250-8BITMIME
S: 250-DSN
S: 250 CHUNKING
C: STARTTLS
S: 220 2.0.0 Ready to start TLS
   [handshake TLS, sesja zaczyna się od nowa — po STARTTLS trzeba powtórzyć EHLO]
C: EHLO mail.firma.pl
C: MAIL FROM:<bounce+7f3a@mail.firma.pl> SIZE=4820
S: 250 2.1.0 Ok
C: RCPT TO:<jan.kowalski@przyklad.pl>
S: 250 2.1.5 Ok
C: DATA
S: 354 End data with <CR><LF>.<CR><LF>
C: [nagłówki, pusta linia, treść]
C: .
S: 250 2.0.0 Ok: queued as 4bHk2P1yFzz3xN
C: QUIT
```

`EHLO` zamiast `HELO` to ESMTP. Rozszerzenia, które mają znaczenie praktyczne:

| Rozszerzenie | Do czego |
|---|---|
| `STARTTLS` | podniesienie połączenia jawnego do TLS na porcie 25/587 |
| `SIZE` | serwer deklaruje limit; klient może zadeklarować rozmiar i dostać odmowę przed wysłaniem 40 MB |
| `8BITMIME` | wolno przesyłać oktety >127 bez kodowania — bez tego polskie znaki muszą iść przez QP/base64 |
| `SMTPUTF8` | adresy e-mail z UTF-8 w części lokalnej i domenie (IDN). Wsparcie po stronie odbiorców nadal niepełne — nie opieraj na tym adresacji produkcyjnej |
| `DSN` | żądanie powiadomienia o statusie doręczenia (`NOTIFY=SUCCESS,FAILURE,DELAY`) |
| `PIPELINING` | wysyłanie kilku poleceń bez czekania na odpowiedź; skraca sesję |
| `CHUNKING` / `BDAT` | alternatywa dla `DATA` bez kropki-terminatora |
| `AUTH` | uwierzytelnianie klienta (`PLAIN`, `LOGIN`, `CRAM-MD5`, `XOAUTH2`) |

### Porty — reguła bez wyjątków

| Port | Nazwa | Kto używa | TLS |
|---|---|---|---|
| 25 | SMTP relay (MX) | serwer → serwer | oportunistyczny STARTTLS; **nigdy nie wymagaj AUTH** |
| 465 | SMTPS / submissions | aplikacja → serwer | implicit TLS od pierwszego bajtu (RFC 8314) |
| 587 | submission | aplikacja/klient → serwer | STARTTLS obowiązkowy + AUTH obowiązkowy |
| 2525 | brak standardu | obejście blokad portu 25 u dostawców chmury | jak 587, zależnie od dostawcy |

Reguły:

- **Aplikacja nigdy nie wysyła przez port 25.** Port 25 służy wyłącznie do przyjmowania
  poczty przychodzącej i do przekazywania między serwerami. Jeśli wpiszesz 25 w konfiguracji
  aplikacji, u większości dostawców chmury (AWS, GCP, Azure, DigitalOcean, Hetzner) połączenie
  po prostu zawiśnie — port jest zablokowany wyjściowo i odblokowywany na wniosek.
- **Domyślnie wybieraj 465.** RFC 8314 od 2018 rekomenduje implicit TLS. 587 ze STARTTLS jest
  podatne na atak downgrade, jeśli klient nie ma ustawionego trybu „wymagaj TLS”.
- Nie mieszaj: `SMTP_PORT=587` z `SMTP_SSL=true` w bibliotekach Pythona to najczęstszy błąd
  konfiguracji — połączenie zawiesza się do timeoutu, bo serwer czeka na `EHLO` w jawnym tekście,
  a klient wysyła ClientHello.

### Kody odpowiedzi — co naprawdę znaczą

Trzy cyfry: `2xx` sukces, `3xx` kontynuuj, `4xx` błąd tymczasowy (**ponów**), `5xx` błąd trwały
(**nie ponawiaj nigdy**). Do tego rozszerzony kod `X.Y.Z` (RFC 3463), gdy serwer ogłosił
`ENHANCEDSTATUSCODES`.

| Kod | Znaczenie praktyczne | Co robić |
|---|---|---|
| `250 2.0.0 Ok: queued as ...` | przyjęte do kolejki odbiorcy. **Nie znaczy, że doręczone** | zapisz identyfikator z odpowiedzi do korelacji z logami |
| `421 4.7.0` | serwer chwilowo zamyka połączenie, zwykle throttling | wolniej, mniejsza równoległość; kolejka ponowi |
| `450 4.2.1` | skrzynka chwilowo niedostępna / greylisting | ponów po ≥5 min; greylisting przepuszcza drugą próbę |
| `451 4.3.0` | błąd lokalny odbiorcy | ponów |
| `452 4.2.2` | skrzynka pełna | ponów, ale po 3 dniach traktuj jako miękkie odbicie i zawieś adres |
| `550 5.1.1` | **adres nie istnieje** | twarde odbicie — usuń z listy natychmiast |
| `550 5.7.1` | odrzucone przez politykę (SPF/DMARC/blocklist/reputacja) | nie ponawiaj; diagnozuj uwierzytelnianie |
| `550 5.7.26` | Gmail: brak uwierzytelnienia dla nadawcy masowego | dołóż SPF+DKIM i wyrównanie |
| `552 5.2.3` / `552 5.3.4` | wiadomość za duża | zmniejsz załącznik lub podaj link |
| `554 5.7.1` | odrzucone jako spam albo IP na czarnej liście | sprawdź listy blokujące, nie ponawiaj |

Reguła: **`4xx` ponawiaj, `5xx` nie ponawiaj i wypisz adres**. Aplikacja, która ponawia `5xx`,
zbiera skargi i po kilkuset próbach dostaje trwałą blokadę u dostawcy.

### Kolejka i ponawianie (Postfix)

```
# main.cf — sensowne wartości dla serwera firmowego
maximal_queue_lifetime = 3d          # po 3 dniach zwrot do nadawcy (domyślnie 5d)
bounce_queue_lifetime  = 1d          # kolejka odbić żyje krócej
minimal_backoff_time   = 300s        # pierwsza ponowna próba po 5 min
maximal_backoff_time   = 4000s       # maksymalny odstęp ~66 min
queue_run_delay        = 300s        # co ile skaner przegląda kolejkę deferred
```

Postfix ma cztery kolejki: `maildrop` (wrzucone lokalnie), `incoming`, `active` (aktualnie
obsługiwane, ograniczona przez `qmgr_message_active_limit`), `deferred` (czeka na ponowienie),
`hold` (zamrożone ręcznie). Diagnostyka:

```bash
postqueue -p                 # lista kolejki, powód odroczenia przy każdym wpisie
postqueue -p | tail -1       # "-- 148 Kbytes in 12 Requests." — szybki licznik
postqueue -f                 # wymuś natychmiastowe przebiegnięcie kolejki
postcat -vq 4bHk2P1yFzz3xN   # podejrzyj konkretną wiadomość z kolejki
postsuper -d ALL deferred    # skasuj całą kolejkę odroczonych (ostrożnie)
postsuper -h ALL             # zamroź wszystko (przy incydencie z pętlą)
mailq                        # alias na postqueue -p
```

**Próg alarmowy:** kolejka `deferred` > 200 pozycji albo najstarsza pozycja > 6 h = alarm.
Rosnąca kolejka `active` przy stałej `deferred` oznacza, że nie nadążasz z wysyłką, nie że
odbiorcy odrzucają.

## IMAP

Stan trwa po stronie serwera: foldery, flagi, przeczytane/nieprzeczytane są wspólne dla
wszystkich urządzeń. To odróżnia IMAP od POP3.

Porty: **993 (implicit TLS, używaj)**, 143 (STARTTLS, tylko dla kompatybilności).

### Foldery specjalne (RFC 6154, SPECIAL-USE)

Klient nie zgaduje po nazwie — serwer ogłasza atrybuty. Dovecot 2.4:

```
# /etc/dovecot/conf.d/15-mailboxes.conf
namespace inbox {
  mailbox Drafts  { special_use = \Drafts;  auto = subscribe }
  mailbox Junk    { special_use = \Junk;    auto = subscribe }
  mailbox Trash   { special_use = \Trash;   auto = subscribe }
  mailbox Sent    { special_use = \Sent;    auto = subscribe }
  mailbox Archive { special_use = \Archive; auto = subscribe }
}
```

Bez `special_use` klienty pocztowe tworzą własne foldery („Wysłane”, „Sent Items”,
„Elementy wysłane”) i użytkownik dostaje trzy foldery wysłanych. To najczęstsza skarga
po migracji poczty.

### Flagi

Systemowe: `\Seen`, `\Answered`, `\Flagged`, `\Deleted`, `\Draft`, `\Recent`.
Własne (keywords): dowolny ciąg, np. `$Forwarded`, `$MDNSent`, `NonJunk`. Serwer ogłasza
`PERMANENTFLAGS` z `\*`, jeśli pozwala tworzyć własne.

`\Deleted` **nie kasuje** — oznacza do skasowania. Faktyczne usunięcie następuje przy
`EXPUNGE`. Klienty w trybie „Trash folder” zamiast tego przenoszą wiadomość do `Trash`.

### IDLE

`IDLE` (RFC 2177) to push: klient wysyła `IDLE`, serwer trzyma połączenie i wysyła
`* 4 EXISTS`, gdy przyjdzie nowa poczta. Bez IDLE klient odpytuje co N minut.

Pułapka: sesja IDLE musi być odnawiana **co najwyżej co 29 minut** (limit z RFC to 30 min,
NAT-y i firewalle zrywają wcześniej). Klient, który tego nie robi, „nie widzi nowej poczty”,
dopóki użytkownik ręcznie nie odświeży.

Każde IDLE trzyma osobne połączenie TCP i osobny proces `imap` w Dovecot. 200 użytkowników
× 3 urządzenia × 5 folderów w IDLE = 3000 połączeń. Ustaw `mail_max_userip_connections = 20`
i licz się z limitem deskryptorów.

### Synchronizacja: UIDVALIDITY i MODSEQ

- `UID` jest niezmienny w obrębie folderu i rosnący.
- `UIDVALIDITY` to znacznik folderu. **Jeśli się zmienił, wszystkie UID-y są nieważne i klient
  musi przeładować folder od zera.** Zmienia się przy odtworzeniu skrzynki z kopii albo migracji
  między formatami. Migracja, która nie zachowuje UIDVALIDITY, powoduje, że każdemu
  użytkownikowi klient pobiera całą skrzynkę od nowa.
- `CONDSTORE`/`QRESYNC` (RFC 7162) dodają `MODSEQ` — pozwalają dociągnąć tylko zmiany flag od
  ostatniej synchronizacji. Dovecot wspiera; włącz w kliencie, jeśli skrzynki są duże.

Migracja skrzynek: `doveadm backup` / `doveadm sync` (Dovecot 2.4) zachowuje UID-y i flagi.
`imapsync` jest wolniejszy, ale działa między różnymi serwerami.

## POP3

Porty: **995 (implicit TLS)**, 110 (jawny). Pobiera i (domyślnie) kasuje. Brak folderów,
brak flag, brak synchronizacji między urządzeniami.

Kiedy POP3 ma sens w 2026: urządzenia, które nie mają IMAP (stare skanery, drukarki
wielofunkcyjne, terminale płatnicze), oraz archiwizacja jednokierunkowa do lokalnego magazynu.
Poza tym — nie używaj. Włączony POP3 z opcją „zostaw na serwerze” u kilku użytkowników
prowadzi do skrzynek, w których „maile znikają” losowo.

## MIME

Wiadomość bez MIME to `Content-Type: text/plain; charset=us-ascii`. Wszystko poza tym wymaga
nagłówków MIME.

### Struktura typowej wiadomości handlowej

```
multipart/mixed
├── multipart/alternative
│   ├── text/plain        (wersja tekstowa — WYMAGANA)
│   └── multipart/related
│       ├── text/html     (wersja HTML)
│       └── image/png     (logo, Content-ID: <logo>)
└── application/pdf       (załącznik: faktura)
```

`multipart/alternative` — klient wybiera **ostatnią** część, którą umie wyświetlić. Dlatego
`text/plain` idzie zawsze pierwsza, HTML druga. Odwrócenie kolejności = wszyscy widzą tekst.

`multipart/related` — części powiązane z HTML-em przez `cid:`. Obraz osadzony:

```
Content-Type: image/png
Content-ID: <logo@firma.pl>
Content-Disposition: inline; filename="logo.png"
Content-Transfer-Encoding: base64
```
w HTML: `<img src="cid:logo@firma.pl" alt="DANACO">`.

### Kodowania treści

| `Content-Transfer-Encoding` | Kiedy | Narzut |
|---|---|---|
| `7bit` | czysty ASCII | 0% |
| `8bit` | UTF-8 przy `8BITMIME`; bezpieczne w praktyce w 2026 | 0% |
| `quoted-printable` | tekst z nielicznymi znakami spoza ASCII (polski) | ~3-6% dla polskiego |
| `base64` | binaria, załączniki, oraz tekst gęsty w znakach spoza ASCII | +33% |

Dla polskiego tekstu **`quoted-printable` z `charset=utf-8`** jest właściwym wyborem: `ą`
staje się `=C4=85`, reszta zdania zostaje czytelna także w surowym źródle.

### Polskie znaki — gdzie się psują

1. **Nagłówki muszą być ASCII.** Wszystko poza tym idzie w kodowaniu RFC 2047:
   `Subject: =?utf-8?Q?Faktura_za_lipiec_=E2=80=93_p=C5=82atno=C5=9B=C4=87?=`
   Biblioteki (`email.headerregistry` w Pythonie, Nodemailer) robią to same. Ręczne sklejanie
   nagłówka z polskimi znakami daje krzaki albo odrzucenie przez serwer.
2. **Nazwa pliku w załączniku** — `Content-Disposition: attachment; filename="..."` nie przyjmuje
   RFC 2047 w niektórych klientach. Poprawnie jest RFC 2231:
   `filename*=UTF-8''Faktura%20lipiec%20%C5%82%C4%85czna.pdf`
   Najbezpieczniej: **nazwy plików bez polskich znaków i bez spacji** (`faktura-2026-07.pdf`).
3. **`charset=iso-8859-2`** — nie używaj. Zostaw dla odczytu archiwów. Wysyłaj wyłącznie UTF-8.
4. Deklaracja `charset` musi zgadzać się z faktycznym bajtami. Rozjazd (`charset=utf-8`, treść
   w cp1250) daje „Å¼” zamiast „ż” u wszystkich odbiorców.

### Nagłówki, których nie wolno pominąć

| Nagłówek | Uwagi |
|---|---|
| `Message-ID` | globalnie unikalny, `<uuid@domena-nadawcy>`. Brak = punkty spamowe u większości filtrów. Domena po `@` musi być twoja |
| `Date` | zgodny z RFC 5322, ze strefą. Data w przyszłości albo sprzed tygodnia = punkty spamowe |
| `From` | jeden adres; domena musi wspierać wyrównanie DMARC |
| `To` | prawdziwy odbiorca. Wysyłka masowa z `To: undisclosed-recipients` = spam |
| `Subject` | ≤ 78 znaków przed kodowaniem, żeby nie łamać linii |
| `MIME-Version: 1.0` | wymagany, gdy jest cokolwiek poza `text/plain` ASCII |
| `List-Unsubscribe` | dla masówki obowiązkowy (patrz `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md`) |
| `List-Unsubscribe-Post` | `List-Unsubscribe=One-Click` — RFC 8058 |
| `Auto-Submitted: auto-generated` | dla powiadomień automatycznych; blokuje pętle autoresponderów |
| `Precedence: bulk` | historyczne, ale niektóre autorespondery nadal to honorują |

### Wątkowanie

```
Wiadomość 1: Message-ID: <a@firma.pl>
Wiadomość 2: Message-ID: <b@firma.pl>
             In-Reply-To: <a@firma.pl>
             References: <a@firma.pl>
Wiadomość 3: Message-ID: <c@firma.pl>
             In-Reply-To: <b@firma.pl>
             References: <a@firma.pl> <b@firma.pl>
```

`References` to pełna ścieżka od korzenia, `In-Reply-To` to bezpośredni rodzic. Gmail dodatkowo
grupuje po temacie — dlatego wątek widoczny w Gmailu może być poprawny mimo błędnych nagłówków,
a w Thunderbirdzie rozsypany. **Testuj wątkowanie w Thunderbirdzie albo `mutt`, nie w Gmailu.**

Aplikacja obsługująca zgłoszenia (helpdesk): zapisz `Message-ID` każdej wysłanej wiadomości,
przy odpowiedzi klienta odczytaj `In-Reply-To`/`References` i po nich znajdź zgłoszenie.
Doklejanie identyfikatora do tematu (`[#12345]`) jest zapasowe, bo klienci go kasują.

## Odbicia (bounce) i ich klasyfikacja

### Twarde vs miękkie

| Typ | Kody | Znaczenie | Reakcja |
|---|---|---|---|
| Twarde (hard) | `5.1.1`, `5.1.10`, `5.4.4` | adres nie istnieje, domena nie istnieje | **natychmiast na listę wykluczeń, na zawsze** |
| Miękkie (soft) | `4.2.2`, `4.2.1`, `4.3.x` | skrzynka pełna, chwilowa awaria | ponawiaj; po 5 kolejnych soft w 7 dni → wyklucz |
| Polityczne (block) | `5.7.1`, `5.7.26`, `554` | odrzucone przez filtr/reputację | **nie wyklucza adresu — wyklucza ciebie**; napraw uwierzytelnianie i reputację |

Twarde odbicia > 2% wysyłki to sygnał, że lista jest kupiona albo stara. Gmail i Microsoft
liczą to do reputacji nadawcy.

### VERP i adresy zwrotne

Żeby wiedzieć, **który** adres odbił, koperta musi być unikalna dla odbiorcy:

```
MAIL FROM:<bounce+jan.kowalski=przyklad.pl@mail.firma.pl>
```

To VERP (Variable Envelope Return Path). Alternatywa: `bounce+<uuid_wysylki>@mail.firma.pl` i tabela
mapująca uuid → adres. Dostawcy transakcyjni robią to za ciebie i zwracają wynik webhookiem — patrz
`references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md`.

### DSN (RFC 3464)

Raport o statusie doręczenia generowany przez serwer. `Content-Type: multipart/report;
report-type=delivery-status`, trzy części:

1. `text/plain` — opis dla człowieka,
2. `message/delivery-status` — pola maszynowe: `Final-Recipient`, `Action` (`failed`,
   `delayed`, `delivered`, `relayed`, `expanded`), `Status` (`5.1.1`), `Diagnostic-Code`,
3. `message/rfc822` lub `text/rfc822-headers` — oryginał albo jego nagłówki.

Parsuj część drugą, nie pierwszą. Treść dla człowieka jest w kilkunastu językach i zmienia się
między serwerami; pole `Status` jest ustandaryzowane.

W Pythonie: `email.message_from_bytes(raw, policy=policy.default)`, potem
`msg.get_payload()[1]` i odczyt pól nagłówkowych tej części.

### ARF (RFC 5965) — skargi

Gdy użytkownik kliknie „to jest spam”, dostawca (Yahoo, Microsoft, Comcast, ale **nie Gmail**)
wysyła raport ARF na adres z pętli zwrotnej (feedback loop). `Content-Type: multipart/report;
report-type=feedback-report`, pole `Feedback-Type: abuse`.

Reguła: **każda skarga = natychmiastowe i bezwarunkowe wykluczenie adresu.** Nie „wypisz
z tej jednej kampanii” — wykluczenie globalne.

Gmail nie wysyła ARF pojedynczych skarg. Agregat widać w Postmaster Tools (wersja 2, po
wyłączeniu starej w październiku 2025 — pokazuje binarny status zgodności). Wskaźnik skarg
utrzymuj **poniżej 0,10%**; 0,30% to próg twardej egzekucji.

### Adresy obowiązkowe

`abuse@twoja-domena.pl` i `postmaster@twoja-domena.pl` muszą działać i być czytane (RFC 2142).
Rejestracja w pętlach zwrotnych, wpisy do list blokujących i zgłoszenia nadużyć idą właśnie tam.
Brak działającego `abuse@` bywa powodem odmowy wypisania z listy blokującej.
