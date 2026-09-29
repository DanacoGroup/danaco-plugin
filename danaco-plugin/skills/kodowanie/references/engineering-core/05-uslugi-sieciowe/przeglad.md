# Usługi sieciowe — przegląd modułu

Moduł obejmuje serwery i protokoły uruchamiane przez firmę: pocztę, telefonię SIP,
kanały czasu rzeczywistego oraz eksploatację usługi. Karty pogłębione wymienia tabela
„Mapa plików referencyjnych” poniżej, a wszystkie moduły `references/engineering-core/` —
`references/engineering-core/spis.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Warstwa, w której model gubi się w szczegółach konfiguracji i rekordach DNS. Moduł zawiera
liczby, składnię i kolejność kroków, których nie da się odtworzyć z pamięci bez pomyłki.

Stan zweryfikowany: sierpień 2026.

## Kiedy wczytać ten moduł

- Poczta nie dochodzi, trafia do spamu, odbija się, albo trzeba zbudować wysyłkę z aplikacji.
- Trzeba postawić, przejąć albo naprawić serwer pocztowy (Postfix/Dovecot/Rspamd, mailcow).
- Trzeba napisać albo naprawić rekordy SPF, DKIM, DMARC, MTA-STS, BIMI, PTR.
- Trzeba uruchomić albo zintegrować centralę telefoniczną: Asterisk, trunk SIP, IVR, kolejki,
  nagrywanie, click-to-call z aplikacji.
- Trzeba zbudować kanał czasu rzeczywistego: czat, powiadomienia, wideorozmowa, softphone
  w przeglądarce, udostępnianie ekranu.
- Trzeba postawić TLS, DNS, odwrotne proxy, zaporę albo `docker compose` dla usługi sieciowej.

**Nie używaj, gdy:**
- Pytanie dotyczy podziału systemu na moduły, granic usług, wyboru architektury, kolejek zadań jako
  wzorca → `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`.
- Trzeba napisać kod aplikacji w Pythonie, model danych, ORM, API, zadania w tle
  → `references/engineering-core/02-python-backend-dane/przeglad.md`.
- Chodzi o eDoręczenia, KSeF, płatności (Przelewy24/PayU/Stripe), Profil Zaufany, ePUAP, BIR/REGON,
  integracje z platformami PL/UE → `references/engineering-core/06-integracje-pl-eu/przeglad.md`.
- Chodzi o front interfejsu i wydajność w przeglądarce →
  `../ui-ux-pro/references/wydajnosc-frontu.md`; audyt gotowej witryny →
  `../kontrola-jakosci/references/audyt-jakosci/audyt-web.md`.
- Chodzi o CI/CD, testy, wdrożenie aplikacji →
  `references/engineering-core/07-debug-testy-deploy/przeglad.md`.

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
|---|---|---|
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md` | koperta vs nagłówki, sesja SMTP i ESMTP, porty 25/465/587, STARTTLS, **kody odpowiedzi i co znaczą**, kolejka Postfiksa i ponawianie, IMAP (foldery specjalne, flagi, IDLE, UIDVALIDITY, QRESYNC), POP3, MIME (struktura, kodowania, `cid:`), **polskie znaki w nagłówkach i nazwach plików**, `Message-ID`/`References` i wątkowanie, odbicia twarde vs miękkie, VERP, DSN, ARF | przy diagnostyce „nie doszło / odbiło się”, przy budowie parsera poczty, przy pytaniu o port albo kod SMTP, przy krzakach w temacie |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` | **wymagania Google/Yahoo/Microsoft z aktualnym stanem egzekucji**, SPF (limit 10 odwołań, `~all` vs `-all`, błędy), DKIM (klucze, selektory, rotacja, `h=`, co psuje podpis), DMARC (wyrównanie, raporty, wdrożenie etapowe), ARC, MTA-STS, TLS-RPT, DANE, BIMI (VMC vs CMC), **komplet rekordów DNS do wklejenia**, kolejność wdrażania domeny, rozgrzewanie IP, procedura diagnostyki „trafiamy do spamu” | **zawsze przy „maile idą do spamu”**, przy zakładaniu domeny nadawczej, przy każdym pytaniu o SPF/DKIM/DMARC |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md` | **kiedy własny serwer jest błędem** (z rachunkiem kosztów), porównanie mailcow/Mailu/docker-mailserver/Stalwart, wdrożenie mailcow krok po kroku, `main.cf` i `master.cf` z pułapkami, Dovecot 2.4 (kwoty, sieve, Maildir vs mdbox), Rspamd (DKIM, ARC, progi), antywirus, kopie zapasowe, monitorowanie kolejki, listy blokujące i procedura wypisu, RODO a poczta | gdy pada „postaw serwer pocztowy”, przy przejmowaniu cudzej instalacji, przy awarii kolejki, przy wpisie na listę blokującą |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` | **rozdzielenie transakcyjnej od marketingowej**, porównanie dostawców z cenami (SES/Resend/Postmark/SendGrid/Brevo), API vs SMTP relay, warstwa abstrakcji w kodzie, szablony, załączniki, **dlaczego śledzenie otwarć jest zepsute**, webhooki odbić i skarg, lista wykluczeń, `List-Unsubscribe` RFC 8058, **zgody marketingowe wg PKE art. 398**, HTML e-maila (tabele, inline, tryb ciemny, dostępność), procedura testu dostarczalności | przy budowie wysyłki z aplikacji, przy wyborze dostawcy, przy pisaniu szablonu e-maila, przy pytaniu o zgody i newsletter |
| `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` | SIP (rejestracja, INVITE, SDP, kody odpowiedzi), **NAT i dlaczego psuje dźwięk**, kodeki i pasmo, jakość (jitter, MOS), **Asterisk 22 LTS z `chan_pjsip` — dosłowne `pjsip.conf`**, plan wybierania, kolejki, IVR, nagrywanie **z obowiązkami prawnymi w PL**, AMI i ARI, trunk SIP w Polsce z cenami, numeracja i UKE, połączenia alarmowe, fail2ban, **oszustwo taryfowe z realnym kosztem** | przy każdym pytaniu o telefonię, centralę, Asteriska, „nie ma dźwięku”, click-to-call, integrację CRM z telefonią |
| `references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md` | wybór WebSocket vs SSE vs WebRTC, uścisk dłoni WS i **sprawdzanie `Origin`**, podtrzymanie i limity proxy, ponowne łączenie z rozrzutem, skalowanie i przyleganie sesji, SSE, WebRTC (sygnalizacja, trickle ICE, perfect negotiation), **coturn — pełna konfiguracja z `denied-peer-ip`**, poświadczenia krótkotrwałe, `getUserMedia`, udostępnianie ekranu, kodeki, mesh/SFU/MCU, LiveKit vs mediasoup vs Janus, nagrywanie, **WebRTC jako softphone do Asteriska** | przy czacie, powiadomieniach na żywo, wideorozmowie, „nie ma obrazu/dźwięku w przeglądarce”, softphonie |
| `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` | Let's Encrypt — **co zmieniło się w 2026** (profile, 6 dni, IP, koniec `tlsclient`, koniec powiadomień), ACME i DNS-01 dla certyfikatów wieloznacznych, konfiguracja TLS, typy rekordów DNS, **TTL i sekwencja migracji**, DNSSEC, propagacja, nginx/Caddy/Traefik z **WebSocketem i SSE przez proxy**, limity, zapora i SSH, `docker compose` dla usług sieciowych, kopie zapasowe (co się pomija), monitorowanie z progami, dzienniki i retencja | przy stawianiu czegokolwiek na serwerze, przy „certyfikat wygasł”, „zmieniam serwer”, „WebSocket nie działa przez nginx” |

## Objaw → plik

| Co mówi człowiek | Otwórz najpierw |
|---|---|
| „maile trafiają do spamu” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` (procedura diagnostyki na końcu) |
| „klient nie dostał faktury / powiadomienia” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md` (kody, odbicia) → `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` (webhooki) |
| „postaw nam serwer pocztowy” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md` (najpierw sekcja „kiedy jest błędem”) |
| „chcemy wysyłać newsletter” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` (dostawcy + zgody PKE) — **nie własny serwer** |
| „potrzebujemy resetu hasła mailem” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` (API, subdomena transakcyjna) |
| „Gmail odrzuca nasze maile”, „550 5.7.26” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` (wymagania Google) |
| „jaki rekord DNS wkleić” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` (komplet rekordów) |
| „przenosimy pocztę do innego dostawcy” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` (kolejność) + `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (TTL) |
| „polskie znaki w temacie się psują” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md` (RFC 2047, kodowania) |
| „mail wygląda inaczej w Outlooku” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` (HTML e-maila) |
| „kolejka poczty rośnie” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md` (monitorowanie) + `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md` (kolejka) |
| „jesteśmy na czarnej liście” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md` (listy blokujące, procedura wypisu) |
| „chcemy logo przy mailach w Gmailu” | `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` (BIMI) |
| „potrzebujemy centrali telefonicznej” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` |
| „słyszę ich, oni mnie nie”, „dźwięk urywa się po 30 s” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` (NAT) |
| „IVR nie reaguje na klawisze” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` (DTMF `rfc4733`) |
| „chcemy dzwonić z CRM-a jednym kliknięciem” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` (AMI `Originate`) |
| „chcemy nagrywać rozmowy” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` (MixMonitor + obowiązki prawne) |
| „dostaliśmy rachunek na 400 tys. za połączenia” | `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` (oszustwo taryfowe) |
| „chcemy dzwonić z przeglądarki” | `references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md` (WebRTC ↔ SIP) + `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` |
| „potrzebujemy czatu / powiadomień na żywo” | `references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md` (najpierw: czy nie wystarczy SSE) |
| „WebSocket rozłącza się co minutę” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (`proxy_read_timeout`) |
| „SSE nie działa na produkcji, na localhost działało” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (`proxy_buffering off`, `X-Accel-Buffering`) |
| „wideorozmowa nie działa u części użytkowników” | `references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md` (TURN, kandydaci `relay`) |
| „certyfikat wygasł” / „przeglądarka pokazuje stary certyfikat” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (ACME, `--deploy-hook`) |
| „potrzebujemy certyfikatu na `*.przyklad.pl`” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (DNS-01) |
| „zmieniamy adres IP serwera” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (TTL, sekwencja migracji) |
| „dodałem rekord, a nie widać” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (propagacja, negatywny TTL) |
| „postaw to w Dockerze” | `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` (`docker compose`, publikacja portów a `ufw`) |

## Szybkie decyzje — bez otwierania plików

Rozstrzygnięcia, które padają na początku rozmowy i determinują całą resztę pracy.

| Pytanie | Odpowiedź domyślna | Wyjątek |
|---|---|---|
| Własny serwer pocztowy czy dostawca? | **skrzynki** — można u siebie; **wysyłka z aplikacji** — nigdy u siebie | brak: wysyłka z aplikacji zawsze przez dostawcę |
| Który port SMTP w aplikacji? | **465** (implicit TLS) | 587, gdy dostawca nie wystawia 465; **nigdy 25** |
| API czy SMTP relay do dostawcy? | **API** | SMTP, gdy wysyła gotowe oprogramowanie (WordPress, ERP, drukarka) |
| Jeden zestaw rekordów czy subdomeny? | **osobna subdomena dla transakcyjnej i osobna dla marketingu** | brak |
| Od jakiej polityki DMARC zacząć? | `p=none` + `sp=reject` + `rua` | `p=reject` od razu tylko na domenach, z których nikt nie nadaje |
| `~all` czy `-all` w SPF? | zacznij `~all`, po 2-4 tyg. raportów `-all` | brak |
| MTA-STS czy DANE? | **MTA-STS** | DANE tylko, gdy masz DNSSEC **i** automat aktualizujący TLSA |
| Dedykowane IP do wysyłki? | **nie** poniżej ~100 tys. wiad./mies. | powyżej — tak, z rozgrzewaniem |
| Która wersja Asteriska? | **22 LTS** | 23 tylko w laboratorium |
| `chan_sip` czy `chan_pjsip`? | **`chan_pjsip`** | brak — `chan_sip` nie istnieje od wersji 21 |
| Który kodek na trunk operatorski? | **G.711 a-law** (`alaw`) | Opus tylko między własnymi punktami końcowymi |
| Media przez Asteriska czy bezpośrednio? | `direct_media=no` (przez Asteriska) | `yes` tylko w jednej sieci LAN bez NAT |
| WebSocket czy SSE? | **SSE**, jeśli komunikacja jest jednokierunkowa serwer→klient | WebSocket przy dwukierunkowej |
| Mesh czy SFU dla wideo? | **SFU powyżej 4 uczestników** | mesh do 4, gdy nie chcesz serwera |
| Który serwer mediów? | **LiveKit** | mediasoup przy potrzebie pełnej kontroli; Janus przy bramce SIP↔WebRTC |
| Własny STUN/TURN czy publiczny? | **własny coturn** | publiczny STUN Google tylko w prototypie |
| nginx, Caddy czy Traefik? | **Caddy** na pojedynczym serwerze; **Traefik** przy wielu kontenerach; **nginx** przy dużym ruchu i strojeniu | brak |
| HTTP-01 czy DNS-01 w ACME? | HTTP-01 | **DNS-01 obowiązkowo** przy certyfikacie wieloznacznym i przy usługach bez publicznego HTTP (poczta, TURN, SIP) |
| Profil certyfikatu Let's Encrypt? | `tlsserver` (45 dni) | `classic` przy starych klientach ACME; `shortlived` przy w pełni zaufanej automatyzacji |

## Pierwsze 15 minut przy zgłoszeniu

Zanim otworzysz plik referencyjny, zbierz to, bez czego diagnoza jest zgadywaniem.

**Poczta nie dochodzi / trafia do spamu**
1. Do kogo konkretnie nie dochodzi (Gmail, Outlook, WP, klient korporacyjny) — filtry różnią się
   diametralnie i „nie dochodzi nigdzie” prawie nigdy nie jest prawdą.
2. Surowa treść odbicia albo nagłówki `Authentication-Results` z wiadomości, która **doszła**.
3. Kto wysyła: własny serwer, dostawca, obydwa naraz.
4. Od kiedy i co się zmieniło (nowa domena, nowy dostawca, nowe IP, migracja, kampania).

**Nie ma dźwięku / rozmowa się urywa**
1. Kierunek ciszy: w jedną stronę czy w obie.
2. Kiedy: od początku, po N sekundach, po przekazaniu połączenia.
3. Kto: wszyscy, jeden użytkownik, tylko zdalni, tylko na komórce.
4. Czy na routerze jest włączone SIP ALG.

**Wideorozmowa nie działa u części użytkowników**
1. `chrome://webrtc-internals` — czy jest wybrana para kandydatów i jakiego typu.
2. Czy w teście trickle-ICE pojawia się kandydat `relay` (czyli czy TURN żyje).
3. Czy strona jest na HTTPS (bez tego `getUserMedia` nie istnieje).

**Usługa przestała odpowiadać**
1. Data ważności certyfikatu na **każdym** punkcie końcowym, nie tylko 443.
2. Zajętość dysku (dzienniki kontenerów bez limitu to najczęstsza przyczyna).
3. Czy zmieniał się DNS w ostatnich 48 h i jaki był TTL.

## Polecenia diagnostyczne — jedna strona

```bash
# --- poczta: uwierzytelnianie i reputacja ---
dig +short TXT przyklad.pl                          # SPF (musi być dokładnie jeden spf1)
dig +short TXT sel._domainkey.przyklad.pl           # DKIM
dig +short TXT _dmarc.przyklad.pl                   # DMARC
dig +short MX przyklad.pl
dig +short -x 203.0.113.7                           # PTR
dig +short 7.113.0.203.zen.spamhaus.org             # lista blokująca (oktety odwrócone)
swaks --to test@gmail.com --from a@przyklad.pl --server localhost --tls
openssl s_client -starttls smtp -connect mx.przyklad.pl:25 -servername mx.przyklad.pl

# --- poczta: serwer ---
postqueue -p | tail -1                              # rozmiar kolejki
postconf -n                                         # konfiguracja bez domyślnych
postfix check
doveadm quota get -A                                # wykorzystanie kwot
rspamc stat                                         # stan klasyfikatora

# --- SIP / Asterisk ---
asterisk -rvvv
  pjsip show endpoints
  pjsip show registrations                          # trunk musi być Registered
  pjsip show aors
  pjsip set logger on                               # pełny podgląd sygnalizacji
  core show channels
  queue show
  sip show settings                                 # (nie istnieje przy chan_pjsip — kontrola wersji)
sngrep -d any port 5060                             # przechwytywanie SIP z drzewem połączeń

# --- WebRTC / TURN ---
turnutils_uclient -T -u <expires:user> -w <haslo> turn.przyklad.pl
# przeglądarka: chrome://webrtc-internals, https://icetest.info/

# --- TLS / DNS ---
echo | openssl s_client -connect app.przyklad.pl:443 -servername app.przyklad.pl 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
dig +trace przyklad.pl
delv przyklad.pl                                    # walidacja DNSSEC
certbot certificates

# --- proxy / kontenery ---
nginx -t && nginx -s reload
curl -isN -H "Accept: text/event-stream" https://app.przyklad.pl/zdarzenia | head -20
curl -i -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Version: 13" \
     https://app.przyklad.pl/ws                     # ma zwrócić 101
docker compose ps
docker compose logs -f --tail=200 aplikacja
```

## Procedura

1. **Ustal, o którą z czterech dziedzin chodzi**: poczta / telefonia / czas rzeczywisty /
   eksploatacja. Zgłoszenia mieszają dziedziny („maile nie dochodzą, bo certyfikat wygasł”).
2. **Sprawdź granice modułu.** Jeśli pytanie dotyczy architektury, kodu Pythona albo integracji
   PL/UE — odeślij do sąsiada i nie duplikuj.
3. **Przy poczcie: zawsze najpierw uwierzytelnianie, potem treść.** 90 % zgłoszeń „idziemy do spamu”
   to SPF/DKIM/DMARC albo PTR, nie słowa w tytule. Wykonaj procedurę diagnostyczną z końca
   `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md`, zanim
   zaproponujesz cokolwiek innego.
4. **Przy prośbie o własny serwer pocztowy: najpierw zakwalifikuj.** Przeczytaj klientowi rachunek
   kosztów z `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md`. Wysyłka z
   aplikacji — nigdy własny serwer.
5. **Przy telefonii: sprawdź wersję Asteriska i czy konfiguracja nie jest z `chan_sip`.**
   `chan_sip` nie istnieje od Asteriska 21. Konfiguracja z `sip.conf` wymaga przepisania na
   `pjsip.conf`, nie łatania.
6. **Przy czasie rzeczywistym: zapytaj o kierunek komunikacji.** Jednokierunkowo serwer→klient
   to SSE, nie WebSocket. Wideo to WebRTC, nie WebSocket.
7. **Zweryfikuj wersje i wymagania, które mogły się zmienić.** Wymagania nadawców masowych,
   wersje serwerów, zasady Let's Encrypt zmieniają się co kwartał. Daty w tym module są
   podane jawnie — jeśli minęło pół roku, sprawdź.
8. **Podaj konfigurację dosłownie, gotową do wklejenia**, z komentarzem przy każdej nieoczywistej
   linii. Nie opisuj konfiguracji prozą.
9. **Do każdej zmiany dopisz sposób weryfikacji** (`dig`, `openssl s_client`, `postqueue -p`,
   `asterisk -rx`, `chrome://webrtc-internals`) i **sposób wycofania**.

## Twarde reguły

**Poczta**

1. **Nie stawiaj własnego serwera pocztowego do wysyłki marketingowej ani transakcyjnej.** Powody z
   liczbami w `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md`. Jeśli
   mimo to postawisz: pierwsza kampania z 2 % odbić wpisze IP na Spamhaus i przez tydzień nie
   wyjdzie ani jeden reset hasła.
2. **Koperta ≠ nagłówek `From:`.** SPF sprawdza kopertę, DMARC nagłówek. Mylenie ich to
   przyczyna większości nieudanych wdrożeń DMARC.
3. **Aplikacja nigdy nie wysyła przez port 25.** Port 25 to relay między serwerami; u dostawców
   chmury jest zablokowany wyjściowo. Aplikacja: 465 (implicit TLS) albo 587 (STARTTLS+AUTH).
4. **`5xx` = nie ponawiaj i wyklucz adres. `4xx` = ponów.** Ponawianie `5xx` niszczy reputację.
5. **DMARC wdrażaj etapami: `p=none` → `p=quarantine` → `p=reject`, min. 2 tygodnie w etapie 1.**
   Od razu `p=reject` odcina pocztę z drukarki, CRM-u i systemu kadrowego.
6. **Poczta transakcyjna i marketingowa na osobnych subdomenach z osobnymi kluczami DKIM.**
   Wspólna subdomena oznacza, że jedna zła kampania zabiera ze sobą resety haseł.
7. **Każda skarga („to jest spam”) i każde twarde odbicie = natychmiastowe, trwałe wykluczenie
   adresu.** Bez wyjątków i bez automatycznego przywracania.
8. **Marketing e-mailowy w Polsce wymaga uprzedniej zgody (PKE art. 398), także B2B.**
   Kara: do 3 % przychodu albo 1 mln PLN. Zgoda musi być udokumentowana z treścią klauzuli.
9. **`List-Unsubscribe` z `List-Unsubscribe-Post: List-Unsubscribe=One-Click` obowiązkowy**
   dla masówki; endpoint musi przyjmować `POST`, bez potwierdzania, realizacja ≤ 2 dni.
10. **Nie podejmuj decyzji na wskaźniku otwarć.** Apple Mail Privacy Protection go fałszuje.
11. **Nowy adres IP rozgrzewaj: maksymalnie ×2 wolumenu na dobę**, zaczynając od 50/dobę.
12. **`mode: enforce` w MTA-STS włączaj dopiero po tygodniu czystych raportów TLS-RPT.**
    Wygasły certyfikat na `mta-sts.` przy `enforce` odbija całą pocztę przychodzącą.

**Telefonia**

13. **Nie używaj `chan_sip`.** Usunięty w Asterisku 21. Do nowych wdrożeń: Asterisk 22 LTS
    z `chan_pjsip`.
14. **Trunk operatorski zawsze we własnym kontekście** (`context=z-zewnatrz`), nigdy
    w kontekście z wyjściem na miasto. Inaczej każdy dzwoniący z zewnątrz może wybrać dowolny
    numer premium na twój koszt.
15. **Limit kwotowy u operatora + blokada kierunków premium — obowiązkowo, przy podpisywaniu
    umowy.** To jedyne zabezpieczenie działające, gdy śpisz. Weekendowe włamanie bez limitu
    to rachunek rzędu setek tysięcy złotych.
16. **Hasła SIP: losowe, ≥ 16 znaków.** Hasło równe numerowi wewnętrznemu to gwarantowane
    włamanie w ciągu doby.
17. **Numery alarmowe (112, 997, 998, 999) dostępne z każdego kontekstu, bez uprawnień,
    bez limitów.** Adres instalacji u operatora musi być aktualny.
18. **Nagrywanie rozmów: poinformowanie przed rozpoczęciem, podstawa prawna, retencja,
    szyfrowanie.** Nagrywanie pracowników to monitoring z Kodeksu pracy art. 22[3] —
    regulamin i 2 tygodnie uprzedzenia.
19. **Wyłącz SIP ALG na routerze.** Zawsze. To pierwsza rzecz do sprawdzenia przy
    niewytłumaczalnych problemach z dźwiękiem.

**Czas rzeczywisty**

20. **Sprawdzaj nagłówek `Origin` przy uścisku dłoni WebSocket.** WebSocket nie podlega CORS;
    bez sprawdzenia masz Cross-Site WebSocket Hijacking z ciasteczkiem sesji.
21. **Nie przekazuj tokenu w URL WebSocketa** — trafia do logów proxy. Pierwsza wiadomość
    po otwarciu.
22. **coturn bez `denied-peer-ip` dla sieci prywatnych to brama do twojej sieci wewnętrznej.**
23. **Poświadczenia TURN krótkotrwałe (HMAC, 1-4 h), generowane przez backend.** Statyczne
    w kodzie front-endu = darmowy przekaźnik dla internetu na twój rachunek.
24. **Powyżej 4 uczestników wideo — SFU, nie mesh.** Mesh przy 5 osobach to ~6 Mb/s wysyłania
    na uczestnika, powyżej możliwości typowego łącza.
25. **Ponowne łączenie zawsze z wykładniczym wycofaniem i rozrzutem.** Bez rozrzutu restart
    serwera powoduje, że wszyscy klienci wracają w tej samej milisekundzie.

**Eksploatacja**

26. **Let's Encrypt nie wysyła już powiadomień o wygaśnięciu.** Monitoruj sam, wszystkie
    punkty końcowe: 443, 993, 465, 5349, 5061, `mta-sts.`.
27. **`--deploy-hook` przeładowujący usługi jest obowiązkowy.** Bez niego certyfikat jest
    odnowiony na dysku, a serwer podaje stary z pamięci.
28. **Obniż TTL na 300 s co najmniej 2× stary TTL przed planowaną zmianą DNS.**
29. **WebSocket przez nginx wymaga: `proxy_http_version 1.1`, mapy `$connection_upgrade`,
    `proxy_read_timeout` > interwału podtrzymania.** SSE dodatkowo `proxy_buffering off`
    i `X-Accel-Buffering: no`.
30. **`ports: "8000:8000"` w Dockerze omija `ufw`.** Publikuj na `127.0.0.1:8000:8000`,
    a na zewnątrz wystawiaj przez proxy.
31. **Każda usługa w `compose.yaml` musi mieć limit rozmiaru dziennika.** Domyślny `json-file`
    bez limitu zapełnia dysk i kładzie serwer w nocy.
32. **Kopia bez przetestowanego odtworzenia nie jest kopią.** Test raz na kwartał, na czystej
    maszynie, z pomiarem RTO i RPO. W kopii muszą być klucze DKIM, `/etc/letsencrypt`, sekrety.

## Kontrola przed oddaniem

- [ ] Każdy podany rekord DNS ma komentarz wyjaśniający, co robi i co się stanie bez niego.
- [ ] Przy każdej wersji oprogramowania podana jest data, na którą została sprawdzona.
- [ ] Fakty, których nie udało się potwierdzić, oznaczono `[niepotwierdzone: ...]`.
- [ ] Podana konfiguracja jest kompletna — bez `...` i „resztę uzupełnij”.
- [ ] Do każdej zmiany dodano polecenie weryfikujące (`dig`, `openssl`, `postqueue`,
      `asterisk -rx`, `curl`) i sposób wycofania.
- [ ] Przy poczcie: sprawdzono uwierzytelnianie **przed** proponowaniem zmian w treści.
- [ ] Przy prośbie o serwer pocztowy: przedstawiono rachunek kosztów i alternatywę.
- [ ] Przy wysyłce marketingowej: sprawdzono podstawę prawną (zgoda PKE) i `List-Unsubscribe`.
- [ ] Przy telefonii: sprawdzono kontekst trunku, limity kosztowe i numery alarmowe.
- [ ] Przy nagrywaniu rozmów: wskazano obowiązek informacyjny i retencję.
- [ ] Przy WebSocket/WebRTC: wskazano sprawdzanie `Origin`, TURN i sposób diagnostyki.
- [ ] Przy certyfikatach: wskazano `--deploy-hook` i monitorowanie wygaśnięcia.
- [ ] Nie powielono treści należącej do
  `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`,
  `references/engineering-core/02-python-backend-dane/przeglad.md` ani
  `references/engineering-core/06-integracje-pl-eu/przeglad.md` — zamiast tego odsyłacz.

## Stan faktyczny na sierpień 2026 — liczby, których model nie zgaduje

Zweryfikowane przez WebSearch/WebFetch. Szczegóły i źródła w plikach referencyjnych.

| Fakt | Wartość | Data weryfikacji |
|---|---|---|
| Gmail: przejście z odroczeń `421` na trwałe odrzucenia `550` | listopad 2025 | 08.2026 |
| Gmail: wyłączenie starych Postmaster Tools, v2 z binarnym statusem zgodności | październik 2025 | 08.2026 |
| Gmail/Yahoo: próg nadawcy masowego | 5 000 wiad./dobę; skarg cel < 0,10 %, twardy próg 0,30 % | 08.2026 |
| Microsoft Outlook: wymagania dla nadawców wysokowolumenowych | od 5.05.2025, egzekwowane; niezgodne do Junk (zmiana z 29.04.2025) | 08.2026 |
| BIMI: CMC bez znaku towarowego (wymaga logo publicznie od ≥12 mies.) | opcja Gmaila od początku 2025 | 08.2026 |
| Postfix stabilny | 3.11.5 (6.07.2026) | 08.2026 |
| Dovecot CE | 2.4.4 (12.05.2026); gałąź 2.3 tylko krytyczne poprawki, **inna składnia konfiguracji** | 08.2026 |
| mailcow | wydanie 2026-07a: Postfix 3.10.12 (Debian 13), Rspamd 4.1.4, nginx 1.30.3, CVE-2026-42533 | 08.2026 |
| Mailu | gałąź `2024.06`, najnowszy `2024.06.57` (26.07.2026) | 08.2026 |
| Stalwart Mail Server | 0.16.11 (25.06.2026) — SMTP/IMAP/JMAP/POP3/CalDAV/CardDAV/WebDAV | 08.2026 |
| Asterisk LTS / standardowy | **22.10.1 (LTS)** / 23.4.1; 21 tylko bezpieczeństwo; 18 EOL | 08.2026 |
| `chan_sip` | **usunięty w Asterisku 21** — obowiązuje `chan_pjsip` | 08.2026 |
| Kamailio | 6.1.3 (27.05.2026) | 08.2026 |
| coturn | 4.14.0 (21.06.2026) — HTTPS dla Prometheusa, TLS do Redisa, limit `401` | 08.2026 |
| LiveKit server | 1.12.x (maj 2026) — **zmiany w uwierzytelnianiu i uprawnieniach TURN** | 08.2026 |
| nginx stabilny | 1.30.0 (2.05.2026) — Early Hints, HTTP/2 do zaplecza, ECH, sticky upstream, **domyślnie HTTP/1.1 z keep-alive do zaplecza** | 08.2026 |
| Let's Encrypt: certyfikaty 6-dniowe i na adres IP | dostępność ogólna od 15.01.2026 | 08.2026 |
| Let's Encrypt: profil `tlsclient` | **wycofany 8.07.2026** — brak certyfikatów do mTLS | 08.2026 |
| Let's Encrypt: powiadomienia o wygaśnięciu e-mailem | **zakończone (2025)** — monitoruj sam | 08.2026 |
| Let's Encrypt: zmiana certyfikatów głównych | 13.05.2026 | 08.2026 |
| PKE (Prawo komunikacji elektronicznej), zgody marketingowe | obowiązuje od 10.11.2024, art. 398; kara do 3 % przychodu albo 1 mln PLN | 08.2026 |
| Amazon SES | ~0,10 USD/1000; regiony UE `eu-central-1`, `eu-west-1` | 07.2026 |
| Postmark | od ~15 USD/mies. + 1,80 USD/1000 ponad limit | 07.2026 |
| Resend | 3 000/mies. bezpłatnie; ~0,0004 USD/wiad. | 07.2026 |
| SIP trunk PL (ACTIO, Platan, Datera, EasyCall, SuperVoIP) | od ~4 PLN/kanał; wszyscy z MNP i numeracją UKE | 06.2026 |
