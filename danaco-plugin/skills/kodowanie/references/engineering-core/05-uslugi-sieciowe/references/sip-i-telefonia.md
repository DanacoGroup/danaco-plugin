# SIP, VoIP, Asterisk

Wersje zweryfikowane sierpień 2026: Asterisk **22.x — bieżący LTS** (22.10.1), Asterisk 23.x
— bieżące wydanie standardowe (23.4.1), Asterisk 20 — LTS w podtrzymaniu, Asterisk 21 — tylko
poprawki bezpieczeństwa, Asterisk 18 — koniec życia. Kamailio 6.1.3 (27.05.2026).
FreeSWITCH 1.11.x `[niepotwierdzone: dokładna data wydania 1.11.x]`. coturn 4.14.0 (21.06.2026).

**Do nowych wdrożeń: Asterisk 22 LTS.** LTS ma 4 lata pełnego wsparcia + rok poprawek
bezpieczeństwa; wydanie standardowe rok + rok. Do produkcji u klienta nie bierz wydania
standardowego.

### Który silnik

| | Asterisk | FreeSWITCH | Kamailio |
|---|---|---|---|
| Czym jest | **centrala (B2BUA)** z pełną obsługą mediów | centrala/softswitch z mocniejszym stosem mediów | **proxy SIP** — nie dotyka mediów |
| Skala | do ~500-1000 równoczesnych rozmów na maszynie | wyżej niż Asterisk przy transkodowaniu i konferencjach | dziesiątki tysięcy rejestracji; routing, nie media |
| Konfiguracja | pliki `.conf` + plan wybierania; najniższy próg wejścia | XML; bardziej rozwlekła | własny język skryptowy `kamailio.cfg`; najwyższy próg |
| Integracja z aplikacją | AMI, ARI, AGI | ESL (Event Socket) | moduły, `http_client`, baza |
| Kiedy | **domyślnie**: centrala firmowa, IVR, kolejki, nagrywanie, integracja z CRM | duże konferencje, ciężkie transkodowanie, platforma operatorska | warstwa brzegowa/SBC, równoważenie ruchu przed farmą Asterisków |

Dla typowego wdrożenia DANACO (centrala firmowa do 100 użytkowników, integracja z aplikacją)
**Asterisk jest jedynym sensownym wyborem**. Kamailio dokłada się dopiero, gdy jeden Asterisk
przestaje wystarczać i trzeba rozłożyć rejestracje na kilka węzłów.

**`chan_sip` nie istnieje.** Usunięty w Asterisku 21, zdeprecjonowany od 17. Każda konfiguracja
z `sip.conf`, `type=friend`, `context=` w `sip.conf` jest nieaktualna. Obowiązuje `chan_pjsip`
i `pjsip.conf`.

## SIP w praktyce

SIP to protokół sygnalizacyjny — negocjuje połączenie. **Dźwięk nim nie płynie**; dźwięk płynie
RTP-em po osobnych portach UDP. To rozdzielenie jest przyczyną ~80 % problemów z VoIP.

### Rejestracja

```
UA -> PBX:  REGISTER sip:pbx.przyklad.pl   Contact: <sip:101@192.168.1.42:5060>  Expires: 3600
PBX -> UA:  401 Unauthorized               WWW-Authenticate: Digest realm="asterisk", nonce=...
UA -> PBX:  REGISTER ...                   Authorization: Digest username="101", response=...
PBX -> UA:  200 OK                         Contact: <sip:101@192.168.1.42:5060>;expires=3600
```

Rejestracja mówi centrali „gdzie mnie znaleźć”. Wygasa — telefon musi ją odnawiać przed
`Expires`. Za NAT-em ustaw `Expires` krótko (60-180 s), żeby wpis w tablicy NAT nie wygasł
i połączenia przychodzące nadal docierały.

### Przebieg połączenia

```
A -> PBX:  INVITE sip:600123456@pbx SIP/2.0        [SDP oferta: kodeki A, adres/port RTP A]
PBX -> A:  100 Trying
PBX -> B:  INVITE ...                              [SDP oferta]
B -> PBX:  180 Ringing
PBX -> A:  180 Ringing                             (albo 183 Session Progress z wczesnym audio)
B -> PBX:  200 OK                                  [SDP odpowiedź: wybrany kodek, adres/port RTP B]
PBX -> A:  200 OK
A -> PBX:  ACK
           <<<<<<<<<< strumienie RTP w obie strony >>>>>>>>>>
A -> PBX:  BYE
PBX -> A:  200 OK
```

Kluczowe metody: `INVITE` (nawiąż/zmień), `ACK`, `BYE`, `CANCEL` (przerwij niezakończony
INVITE), `REGISTER`, `OPTIONS` (ping/qualify), `REFER` (przekazanie), `NOTIFY`/`SUBSCRIBE`
(BLF, poczta głosowa), `MESSAGE` (SIP SMS), `INFO` (DTMF poza pasmem, przestarzałe).

Odpowiedzi: `1xx` w toku, `2xx` sukces, `3xx` przekierowanie, `4xx` błąd klienta,
`5xx` błąd serwera, `6xx` odmowa globalna.

| Kod | Znaczenie | Typowa przyczyna |
|---|---|---|
| `401` / `407` | wymagane uwierzytelnienie | normalne w przebiegu; jeśli w pętli — złe hasło |
| `403 Forbidden` | odmowa | zły `context`, brak uprawnień do wybieranego numeru, ACL |
| `404 Not Found` | numer nieznany | brak `exten` w planie wybierania |
| `408 Request Timeout` | brak odpowiedzi | druga strona nieosiągalna sieciowo |
| `480 Temporarily Unavailable` | punkt końcowy niezarejestrowany | telefon nie utrzymuje rejestracji |
| `486 Busy Here` | zajęte | |
| `487 Request Terminated` | anulowane przez `CANCEL` | dzwoniący się rozłączył |
| `488 Not Acceptable Here` | **brak wspólnego kodeka** | rozjazd `allow`/`disallow` |
| `503 Service Unavailable` | trunk niedostępny | operator odrzuca, brak środków, blokada |

### SDP

Ciało `INVITE`/`200 OK`. Opisuje, gdzie i czym przesyłać media:

```
v=0
o=- 3901234567 1 IN IP4 203.0.113.10
c=IN IP4 203.0.113.10          <- adres, na który wysyłać RTP
m=audio 14002 RTP/AVP 8 0 101   <- port RTP i lista kodeków (payload types)
a=rtpmap:8 PCMA/8000            <- G.711 a-law
a=rtpmap:0 PCMU/8000            <- G.711 µ-law
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16                 <- DTMF RFC 2833
a=sendrecv
```

**Jeśli w `c=` albo `o=` jest adres prywatny (192.168.x.x, 10.x.x.x), a rozmowa idzie przez
internet — dźwięk nie dojdzie.** To najczęstsza przyczyna „słyszę, ale mnie nie słychać”.

## NAT — dlaczego psuje dźwięk

SIP wkłada adresy IP **do treści komunikatów** (nagłówek `Contact`, `Via`, oraz `c=`/`o=`
w SDP). NAT tłumaczy adresy w nagłówkach IP/UDP, ale nie zagląda do treści SIP. Efekt:
zdalna strona wysyła RTP na adres prywatny, który u niej nie istnieje.

Objawy i przyczyny:

| Objaw | Przyczyna |
|---|---|
| Cisza w jedną stronę | jedna strona wysyła RTP na adres prywatny; brak `rtp_symmetric` |
| Cisza w obie strony | oba SDP z adresami prywatnymi albo blokada portów RTP na zaporze |
| Dźwięk urywa się po 30 s | wpis NAT wygasł, bo nie ma ruchu utrzymującego; brak `qualify` / za długie `Expires` |
| Połączenia wychodzą, przychodzące nie | rejestracja wygasła w tablicy NAT; skróć `Expires` |
| Dźwięk tylko w pierwszych sekundach | RTP idzie inną ścieżką niż sygnalizacja, brak symetrii |

### Rozwiązania, w kolejności skuteczności

| # | Środek | Co robi / ograniczenie |
|---|---|---|
| 1 | `rtp_symmetric` + `force_rport` + `rewrite_contact` | Asterisk uczy się prawdziwego adresu z pakietów przychodzących i tam odsyła. Rozwiązuje większość przypadków |
| 2 | `external_media_address` / `external_signaling_address` | Asterisk za NAT-em wpisuje w SDP swój adres publiczny zamiast prywatnego |
| 3 | STUN | klient sam poznaje adres publiczny; działa przy NAT stożkowym, zawodzi przy symetrycznym |
| 4 | TURN | przekaźnik mediów; działa zawsze, kosztuje pasmo (`references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md`) |
| 5 | `direct_media=no` / SBC | cały RTP przez Asteriska; kosztuje pasmo i CPU, eliminuje całą klasę problemów |

Odpowiednik dawnego `nat=force_rport,comedia` z `sip.conf` w `chan_pjsip`:

```ini
[101]
type=endpoint
force_rport=yes          ; odsyłaj na port źródłowy, nie na port z Via
rtp_symmetric=yes        ; odpowiednik comedia — ucz się adresu RTP z ruchu przychodzącego
rewrite_contact=yes      ; nadpisz Contact prawdziwym adresem
direct_media=no          ; media przez Asteriska, nie bezpośrednio między telefonami
```

Zapora — otwórz dokładnie to:

```
5060/udp, 5060/tcp    SIP (jeśli używany jawnie)
5061/tcp              SIPS (TLS)
10000-20000/udp       RTP (zakres z rtp.conf; zawęź do faktycznej liczby rozmów × 2)
```

Nigdy nie polegaj na module `nf_conntrack_sip` (SIP ALG) w routerze — **wyłącz go**. SIP ALG
w tanich routerach przepisuje pakiety niepoprawnie i jest źródłem najbardziej niezrozumiałych
awarii VoIP. To pierwsza rzecz do sprawdzenia przy zgłoszeniu „u jednego klienta nie działa”.

## Kodeki i pasmo

| Kodek | Przepływność | Pasmo z narzutem IP/UDP/RTP (20 ms ramki) | MOS | Uwagi |
|---|---|---|---|---|
| G.711 a-law (PCMA) | 64 kb/s | ~87 kb/s | 4,4 | **standard w Polsce i Europie**; brak kompresji, brak opłat |
| G.711 µ-law (PCMU) | 64 kb/s | ~87 kb/s | 4,4 | standard w Ameryce Płn. i Japonii |
| G.722 | 64 kb/s | ~87 kb/s | 4,5 | szerokopasmowy (HD voice), 7 kHz; wymaga wsparcia po obu stronach |
| Opus | 6-510 kb/s (typ. 24-32) | ~40-56 kb/s | 4,5+ | najlepszy stosunek jakości do pasma; adaptacyjny; **domyślny w WebRTC** |
| G.729 | 8 kb/s | ~31 kb/s | 3,9 | oszczędza pasmo kosztem jakości; **transkodowanie kosztuje CPU**; patenty wygasły |
| G.726 | 16-40 kb/s | ~55 kb/s | 4,0 | rzadki, spotykany w starszych bramkach |
| iLBC | 15,2 kb/s | ~38 kb/s | 4,1 | odporny na utratę pakietów; wypierany przez Opusa |

Zasady doboru:

- **Sieć lokalna i łącze symetryczne → G.711 a-law.** Brak transkodowania = brak obciążenia CPU
  i zero degradacji.
- **Łącze wąskie albo komórkowe → Opus**, jeśli obie strony go mają; G.729 tylko dla starych
  urządzeń.
- **Nie ustawiaj listy `allow` z dziesięcioma kodekami.** Każde transkodowanie na centrali
  zjada CPU (G.711↔G.729 to ~30× więcej niż przekazanie bez zmiany). Trzy pozycje wystarczą:
  `allow=!all,opus,alaw,ulaw`.
- **Kolejność w `allow` ma znaczenie** — pierwszy z listy jest preferowany.
- **Trunk operatorski w PL prawie zawsze mówi G.711 a-law.** Ustawienie na trunku wyłącznie
  Opusa daje `488 Not Acceptable Here`.
- DTMF: `dtmf_mode=rfc4733` (dawniej RFC 2833) — w paśmie, jako zdarzenia RTP. `inband`
  psuje się przy kompresji, `info` jest przestarzałe. Rozjazd trybu DTMF = „IVR nie reaguje
  na wciskanie klawiszy”.

### Jakość: jitter, utrata pakietów, MOS

| Parametr | Dobrze | Do przyjęcia | Źle |
|---|---|---|---|
| Utrata pakietów | < 0,5 % | < 1 % | > 2 % (słyszalne przerwy) |
| Jitter | < 20 ms | < 30 ms | > 50 ms (zniekształcenia) |
| Opóźnienie w jedną stronę | < 100 ms | < 150 ms | > 200 ms (wchodzenie w słowo) |
| MOS | > 4,3 | > 4,0 | < 3,6 |

MOS (Mean Opinion Score) 1-5 liczy się z modelu E (ITU-T G.107) na podstawie opóźnienia,
jittera i utraty pakietów.

Bufor jitteru w Asterisku (`jitterbuffer` w `pjsip.conf`): adaptacyjny, 60-200 ms. Za duży
bufor = opóźnienie; za mały = ucinanie. Zakres portów RTP w `rtp.conf` (`rtpstart=10000`,
`rtpend=20000`). QoS: DSCP CS3 (24) dla sygnalizacji, EF (46) dla mediów — bez tego na łączu
współdzielonym z ruchem WWW dowolne pobieranie pliku psuje rozmowę.

## Asterisk z `chan_pjsip` — konfiguracja dosłowna

### `pjsip.conf` — transporty

```ini
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
; jeśli Asterisk stoi za NAT-em:
external_media_address=203.0.113.50
external_signaling_address=203.0.113.50
local_net=192.168.1.0/24
local_net=10.0.0.0/8

[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
cert_file=/etc/letsencrypt/live/pbx.przyklad.pl/fullchain.pem
priv_key_file=/etc/letsencrypt/live/pbx.przyklad.pl/privkey.pem
method=tlsv1_2
external_media_address=203.0.113.50
external_signaling_address=203.0.113.50

[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
```

`local_net` musi obejmować **wszystkie** sieci lokalne. Adres spoza `local_net` jest traktowany
jako zdalny i Asterisk podstawia `external_*`. Pominięcie sieci VPN w `local_net` powoduje, że
telefony w VPN dostają w SDP adres publiczny i tracą dźwięk.

### Punkt końcowy (telefon wewnętrzny)

Trzy sekcje na jeden telefon — to konstrukcja `chan_pjsip`, której model często nie zna:

```ini
; ---- 1. Punkt końcowy: co potrafi i jak się zachowuje ----
[101]
type=endpoint
context=wewnetrzne
disallow=all
allow=alaw,ulaw,opus
auth=101-auth
aors=101
direct_media=no
force_rport=yes
rtp_symmetric=yes
rewrite_contact=yes
dtmf_mode=rfc4733
callerid=Jan Kowalski <101>
transport=transport-udp
device_state_busy_at=1
call_group=1
pickup_group=1
language=pl
media_encryption=no          ; sdes przy SRTP, dtls przy WebRTC

; ---- 2. Uwierzytelnianie: jak się loguje ----
[101-auth]
type=auth
auth_type=userpass
username=101
password=Xy7#kP2rQm9wLt4v      ; min. 16 znaków losowych — patrz sekcja bezpieczeństwa

; ---- 3. AOR (Address of Record): gdzie go szukać ----
[101]
type=aor
max_contacts=2                 ; telefon biurkowy + softphone
remove_existing=yes
qualify_frequency=30           ; OPTIONS co 30 s: utrzymuje NAT i wykrywa awarię
qualify_timeout=3
```

Punkt końcowy i AOR mogą nazywać się tak samo (różne `type=`). Sekcja `auth` musi mieć inną
nazwę, bo `auth=` odwołuje się do niej po nazwie.

`max_contacts=1` z `remove_existing=yes` to typowe ustawienie „jeden telefon = jedna
rejestracja”. `max_contacts` większe niż 1 pozwala dzwonić na wszystkie urządzenia naraz.

### Trunk do operatora

```ini
; ---- rejestracja u operatora (jeśli trunk rejestrowany) ----
[trunk-operator]
type=registration
transport=transport-udp
outbound_auth=trunk-operator-auth
server_uri=sip:sip.operator.pl
client_uri=sip:48221234567@sip.operator.pl
contact_user=48221234567
retry_interval=60
forbidden_retry_interval=600     ; po 403 czekaj dłużej, żeby nie zablokować konta
expiration=300
line=yes
endpoint=trunk-operator

[trunk-operator-auth]
type=auth
auth_type=userpass
username=48221234567
password=HasloOdOperatora

[trunk-operator]
type=aor
contact=sip:sip.operator.pl:5060
qualify_frequency=60

[trunk-operator]
type=endpoint
context=z-zewnatrz              ; KRYTYCZNE: własny kontekst, nigdy nie 'wewnetrzne'
transport=transport-udp
disallow=all
allow=alaw,ulaw
outbound_auth=trunk-operator-auth
aors=trunk-operator
from_user=48221234567
from_domain=sip.operator.pl
direct_media=no
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
dtmf_mode=rfc4733
send_rpid=yes                   ; prezentacja numeru — zależnie od wymagań operatora
trust_id_outbound=yes

; ---- identyfikacja przychodzących po IP (trunk bez rejestracji) ----
[trunk-operator]
type=identify
endpoint=trunk-operator
match=91.185.0.0/16             ; sieć operatora — POBIERZ Z DOKUMENTACJI OPERATORA
```

**`context=z-zewnatrz` na trunku jest wymogiem bezpieczeństwa.** Trunk z `context=wewnetrzne`
pozwala każdemu, kto dodzwoni się z zewnątrz, wybrać dowolny numer międzynarodowy na twój
koszt. To najkosztowniejszy pojedynczy błąd konfiguracyjny w Asterisku.

### Plan wybierania (`extensions.conf`)

```ini
[globals]
TRUNK=PJSIP/trunk-operator
NUMER_GLOWNY=48221234567

[wewnetrzne]
; --- numery wewnętrzne 100-199 ---
exten => _1XX,1,Dial(PJSIP/${EXTEN},25,tT)
 same => n,GotoIf($["${DIALSTATUS}" = "BUSY"]?zajete:nieodebrane)
 same => n(zajete),Playback(pl/zajete)
 same => n,Hangup()
 same => n(nieodebrane),VoiceMail(${EXTEN}@domyslne,u)
 same => n,Hangup()

exten => *97,1,VoiceMailMain(${CALLERID(num)}@domyslne)   ; poczta głosowa

; --- wyjście na miasto: numery krajowe 9-cyfrowe ---
exten => _XXXXXXXXX,1,Set(CALLERID(num)=${NUMER_GLOWNY})
 same => n,Dial(${TRUNK}/sip:48${EXTEN}@sip.operator.pl,60)
 same => n,Hangup()

exten => _0XXXXXXXXX,1,Goto(wewnetrzne,${EXTEN:1},1)      ; prefiks 0 z nawyku

; --- międzynarodowe: 00 + kraj; ograniczone do wybranych grup ---
exten => _00.,1,GotoIf($["${CHANNEL(endpoint)}" =~ "^(101|102)$"]?dalej:odmowa)
 same => n(dalej),Dial(${TRUNK}/sip:${EXTEN}@sip.operator.pl,60)
 same => n,Hangup()
 same => n(odmowa),Playback(pl/brak-uprawnien)
 same => n,Hangup()

; --- ALARMOWE: bez ograniczeń, najwyższy priorytet ---
exten => 112,1,NoOp(POŁĄCZENIE ALARMOWE z ${CALLERID(num)})
 same => n,Set(CALLERID(num)=${NUMER_GLOWNY})
 same => n,Dial(${TRUNK}/sip:112@sip.operator.pl,120)
 same => n,Hangup()
exten => _99[789],1,Goto(112,1)     ; 997, 998, 999

[z-zewnatrz]
; --- ruch przychodzący z trunku: TYLKO dozwolone cele ---
exten => ${NUMER_GLOWNY},1,Goto(ivr-glowne,s,1)
exten => _48221234XXX,1,Goto(wewnetrzne-docelowe,${EXTEN:-3},1)
exten => _.,1,NoOp(Nieznany numer docelowy: ${EXTEN})
 same => n,Hangup()

[wewnetrzne-docelowe]
exten => _XXX,1,Dial(PJSIP/${EXTEN},30)
 same => n,VoiceMail(${EXTEN}@domyslne,u)
 same => n,Hangup()
```

Kontekst `z-zewnatrz` **nie zawiera** reguł wyjścia na miasto. Ostatni wzorzec `_.` z `Hangup()`
zamyka wszystko, co nie pasuje — bez tego nierozpoznany numer wpada w kolejne konteksty.

### IVR

```ini
[ivr-glowne]
exten => s,1,Answer()
 same => n,Wait(1)
 same => n,Set(TIMEOUT(digit)=3)
 same => n,Set(TIMEOUT(response)=8)
 same => n(menu),Background(custom/powitanie)   ; "Sekretariat 1, księgowość 2, ..."
 same => n,WaitExten(8)
 same => n,Goto(powtorz,1)

exten => 1,1,Goto(kolejki,sekretariat,1)
exten => 2,1,Goto(kolejki,ksiegowosc,1)
exten => 9,1,Goto(wewnetrzne-docelowe,100,1)
exten => 0,1,Goto(kolejki,sekretariat,1)        ; 0 = człowiek, ZAWSZE dostępne

exten => i,1,Playback(custom/zly-wybor)          ; niepoprawny klawisz
 same => n,Goto(ivr-glowne,s,menu)
exten => t,1,Playback(custom/brak-wyboru)        ; brak reakcji
 same => n,Goto(kolejki,sekretariat,1)

[powtorz]
exten => 1,1,Set(PROBA=$[${PROBA:-0} + 1])
 same => n,GotoIf($[${PROBA} > 2]?koniec:ivr-glowne^s^menu)
 same => n(koniec),Playback(custom/do-uslyszenia)
 same => n,Hangup()
```

Reguły IVR, które decydują o tym, czy klienci go znoszą:

- **Maksymalnie 5 opcji na poziomie, maksymalnie 2 poziomy zagłębienia.**
- **`0` zawsze prowadzi do człowieka** i jest o tym mowa w zapowiedzi.
- Rozszerzenia `i` (invalid) i `t` (timeout) muszą istnieć — bez nich rozmówca dostaje ciszę.
- Licznik prób — po trzeciej nieudanej próbie przekaż do człowieka albo zakończ grzecznie.
  Bez licznika `Goto` do menu tworzy pętlę bez końca.
- Zapowiedzi nagraj jako 8 kHz mono WAV (`sox nagranie.wav -r 8000 -c 1 -e signed-integer -b 16
  custom/powitanie.wav`) albo `.gsm`; format musi pasować do kodeka, inaczej Asterisk
  transkoduje przy każdym odtworzeniu.

### Kolejki (`queues.conf`)

```ini
[sekretariat]
strategy=rrmemory              ; round-robin z pamięcią, kto ostatnio odebrał
timeout=20                     ; ile dzwoni u jednego agenta
retry=3
wrapuptime=10                  ; przerwa agenta po rozmowie
maxlen=10                      ; maks. oczekujących; 0 = bez limitu
announce-frequency=45
announce-position=yes
announce-holdtime=no
periodic-announce=custom/prosimy-czekac
periodic-announce-frequency=60
joinempty=no                   ; nie wpuszczaj, gdy nie ma agentów
leavewhenempty=yes
ringinuse=no                   ; nie dzwoń do agenta w trakcie rozmowy
musicclass=default
member => PJSIP/101,0,Jan Kowalski
member => PJSIP/102,1,Anna Nowak      ; wyższa liczba = niższy priorytet
```

Strategie: `ringall` (wszyscy naraz — hałaśliwe), `leastrecent`, `fewestcalls`, `random`,
`rrmemory` (domyślny wybór dla równego obciążenia), `linear` (kolejność z pliku, dla eskalacji).

`joinempty=no` + `leavewhenempty=yes` zapobiega sytuacji, w której klient czeka 15 minut
w kolejce, w której nikogo nie ma.

### Nagrywanie rozmów

```ini
exten => _1XX,1,NoOp(Nagrywanie ${EXTEN})
 same => n,Set(NAZWA=${STRFTIME(${EPOCH},Europe/Warsaw,%Y%m%d-%H%M%S)}-${CALLERID(num)}-${EXTEN}-${UNIQUEID})
 same => n,Set(CDR(nagranie)=${NAZWA}.wav)
 same => n,MixMonitor(${NAZWA}.wav,b,/usr/local/bin/po-nagraniu.sh "${NAZWA}")
 same => n,Dial(PJSIP/${EXTEN},25)
 same => n,Hangup()
```

`MixMonitor` z opcją `b` nie zapisuje niczego, dopóki połączenie nie zostanie odebrane —
bez tego masz pliki z samym sygnałem dzwonienia. Trzeci parametr to polecenie uruchamiane po
zakończeniu (konwersja do MP3/OPUS, przeniesienie do magazynu, wpis do bazy).

**Obowiązki prawne w Polsce (nie pomijaj):**

1. **Poinformowanie przed rozpoczęciem nagrywania** — komunikat na początku połączenia,
   w obie strony (także przy połączeniach wychodzących do klienta). „Rozmowa może być
   nagrywana” **nie wystarcza** — musi być jasne, że jest nagrywana, w jakim celu i przez kogo.
2. **Podstawa prawna z RODO.** Zgoda (art. 6 ust. 1 lit. a) jest słaba, bo rozmówca musi mieć
   realną możliwość odmowy — trzeba wtedy zapewnić ścieżkę bez nagrywania. Prawnie uzasadniony
   interes (lit. f) wymaga testu równowagi i udokumentowania. Wykonanie umowy (lit. b) działa
   w telesprzedaży.
3. **Obowiązek informacyjny (art. 13 RODO)** — pełna klauzula musi być dostępna; w zapowiedzi
   odsyłacz do niej („szczegóły na przyklad.pl/prywatnosc”).
4. **Nagrywanie rozmów pracowników** = monitoring w rozumieniu Kodeksu pracy art. 22[3]:
   cel, zakres i sposób w regulaminie pracy lub układzie zbiorowym, poinformowanie pracowników
   **2 tygodnie przed** uruchomieniem, oznaczenie stanowisk.
5. **Retencja** — określ okres (typowo 3-12 miesięcy, w telesprzedaży do przedawnienia
   roszczeń) i **kasuj automatycznie**. Nagrania „na zawsze” to naruszenie zasady ograniczenia
   przechowywania.
6. **Zabezpieczenie** — szyfrowanie wolumenu z nagraniami, dostęp na role, dziennik dostępu.
   Nagranie rozmowy zawiera dane osobowe, często szczególnej kategorii (zdrowie, finanse).
7. Zakaz nagrywania rozmów, w których pada informacja objęta tajemnicą zawodową bez podstawy.

### AMI i ARI — integracja z aplikacją

**AMI** (Asterisk Manager Interface) — protokół tekstowy nad TCP (port 5038), zdarzenia
i polecenia. Starszy, ale niezastąpiony do nasłuchu zdarzeń i prostych akcji.

```ini
; /etc/asterisk/manager.conf
[general]
enabled = yes
port = 5038
bindaddr = 127.0.0.1          ; NIGDY 0.0.0.0 bez zapory
tlsenable = yes
tlsbindaddr = 127.0.0.1:5039
tlscertfile = /etc/asterisk/keys/ami.pem

[aplikacja]
secret = DlugieLosoweHaslo32Znaki!!
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.255
read = system,call,agent,user,cdr,dialplan
write = system,call,agent,originate
```

```python
# Nasłuch zdarzeń AMI + click-to-call (biblioteka panoramisk)
import asyncio
from panoramisk import Manager

async def main():
    manager = Manager(host="127.0.0.1", port=5038,
                      username="aplikacja", secret="DlugieLosoweHaslo32Znaki!!")
    await manager.connect()

    @manager.register_event("Newchannel")
    def nowe_polaczenie(mgr, msg):
        print(f"kanał {msg.Channel} od {msg.CallerIDNum} do {msg.Exten}")

    @manager.register_event("Hangup")
    def rozlaczenie(mgr, msg):
        print(f"koniec {msg.Channel}, przyczyna {msg.Cause}: {msg.get('Cause-txt')}")

    await manager.send_action({
        "Action": "Originate", "Channel": "PJSIP/101", "Context": "wewnetrzne",
        "Exten": "600123456", "Priority": "1", "CallerID": "Klik <101>", "Async": "true",
    })
    await manager.close()

asyncio.run(main())
```

**ARI** (Asterisk REST Interface) — REST + WebSocket. Aplikacja przejmuje **sterowanie
połączeniem**: własne IVR w Pythonie, mostkowanie, kolejkowanie według własnej logiki.

```ini
; /etc/asterisk/ari.conf
[general]
enabled = yes
pretty = yes
allowed_origins = https://panel.przyklad.pl

[aplikacja]
type = user
read_only = no
password = InneDlugieHaslo32Znaki!!
password_format = plain

; /etc/asterisk/http.conf
[general]
enabled = yes
bindaddr = 127.0.0.1
bindport = 8088
tlsenable = yes
tlsbindaddr = 127.0.0.1:8089
tlscertfile = /etc/asterisk/keys/ari.pem
```

W planie wybierania: `same => n,Stasis(moja-aplikacja,${CALLERID(num)})` przekazuje kanał
do aplikacji ARI.

Wybór: **AMI do obserwacji** (dziennik połączeń, wskaźniki, wyskakujące okienko z kartą
klienta), **ARI do sterowania** (własne IVR, integracja z CRM, dynamiczne routowanie).
Nie buduj IVR w `extensions.conf`, jeśli logika zależy od bazy danych — od tego jest ARI.

## SIP trunk od operatora — Polska

Stan rynku 2026: dostępni polscy operatorzy zarejestrowani w UKE z własną numeracją
i przenoszeniem numerów (MNP). Ceny orientacyjne (netto/mies.):

| Operator | Model | Orientacyjnie |
|---|---|---|
| ACTIO | za kanał | od ~4 PLN/kanał; 15 kanałów ~25 PLN |
| Platan | za kanał | 3 kanały ~45 PLN, bez umowy terminowej |
| EasyCall | za kanał | 5 kanałów od ~60 PLN |
| Datera | za kanał | trunk 10 kanałów ~160 PLN |
| SuperVoIP | pakiet | pakiet 20 kanałów ~99 PLN |
| Orange, Netia, Telestrada, PLFON, Spikon | indywidualnie | wycena handlowa |

`[niepotwierdzone: aktualne cenniki — sprawdź u operatora, ceny zmieniają się kwartalnie]`

Kryteria wyboru (ważniejsze od ceny za kanał):

1. **Rozliczanie sekundowe od pierwszej sekundy** vs pierwsza minuta. Przy call center to
   różnica rzędu 20-30 % rachunku.
2. **Limit dobowy/miesięczny kosztu** i alarm po przekroczeniu — ochrona przed oszustwem
   taryfowym.
3. Możliwość **blokady kierunków premium i egzotycznych** po stronie operatora.
4. Obsługa **prezentacji numeru (CLIP)** dla numerów, których nie jesteś abonentem —
   wymaga oświadczenia i zgody.
5. Wsparcie **TLS + SRTP**. Część tanich operatorów oferuje wyłącznie UDP bez szyfrowania.
6. Identyfikacja po IP vs rejestracja. Identyfikacja po IP jest stabilniejsza, ale wymaga
   stałego adresu.

### Numeracja i obowiązki regulacyjne

- Numeracja przydzielana jest **operatorowi** przez Prezesa UKE; jako klient dostajesz numery
  od operatora, nie od UKE.
- **Przeniesienie numeru (MNP)** przysługuje z mocy ustawy. Termin: co do zasady **1 dzień
  roboczy** przy zachowaniu procedury. Wniosek składasz u operatora docelowego (biorcy).
- **Numer musi być używany zgodnie ze strefą numeracyjną.** Numer warszawski (22) używany
  przez abonenta z Gdańska bywa kwestionowany; przy usługach nomadycznych sprawdź warunki
  u operatora.
- **Połączenia alarmowe (112, 997, 998, 999) muszą działać zawsze.** Operator przekazuje
  do CPR informację o lokalizacji abonenta — musisz podać i **aktualizować adres instalacji**.
  Podanie nieaktualnego adresu przy zgłoszeniu alarmowym ma realne konsekwencje.
  W planie wybierania numery alarmowe muszą być dostępne z każdego kontekstu, bez uprawnień,
  bez PIN-u, także gdy skończył się limit środków.
- Prezentacja numeru: podszywanie się pod cudzy numer (CLI spoofing) jest zabronione. PKE
  nakłada na operatorów obowiązek blokowania połączeń z podrobioną prezentacją.
- Świadczenie usług telekomunikacyjnych dla osób trzecich wymaga **wpisu do rejestru
  przedsiębiorców telekomunikacyjnych UKE**. Postawienie centrali dla własnej firmy — nie.
  Odsprzedaż minut klientom — tak. `[niepotwierdzone: aktualny zakres obowiązku wpisu po
  wejściu PKE — zweryfikuj w UKE przed odsprzedażą usług]`

## Bezpieczeństwo

### Skanowanie SIP

Serwer SIP na publicznym adresie jest skanowany w ciągu **minut** od uruchomienia. Narzędzia
(`sipvicious`, `svwar`, `friendly-scanner`) próbują odgadnąć numery wewnętrzne i hasła.

```bash
# to zobaczysz w logu w pierwszej godzinie
grep 'failed for' /var/log/asterisk/messages | wc -l
```

### Minimum obronne

1. **Hasła losowe, ≥ 16 znaków.** Hasło `101` dla numeru `101` albo `1234` to gwarancja
   włamania. Generuj: `openssl rand -base64 24`.
2. **`alwaysauthreject=yes`** (w `pjsip.conf` odpowiednik to domyślne zachowanie
   `chan_pjsip`) — nie ujawniaj, czy numer istnieje. Odpowiedź `403` dla nieistniejącego
   i istniejącego numeru musi być identyczna.
3. **Ogranicz dostęp po IP.** Jeśli telefony są tylko w biurze i VPN — zablokuj resztę świata
   na zaporze. To skuteczniejsze niż wszystko inne razem.
4. **Osobny kontekst dla trunku** (patrz wyżej).
5. **TLS + SRTP** dla telefonów spoza sieci lokalnej.
6. **Nie używaj portu 5060.** Przeniesienie na 5160 albo 5080 eliminuje 95 % automatycznych
   skanów. To nie jest bezpieczeństwo przez ukrycie zastępujące resztę — to filtr szumu.
7. **Wyłącz `allowguest`** (`chan_pjsip` nie ma anonimowych połączeń domyślnie — nie twórz
   punktu końcowego `anonymous`).
8. **Limity połączeń równoczesnych** na punkt końcowy: `device_state_busy_at`, oraz limit
   globalny w planie wybierania (`GROUP()`/`GROUP_COUNT()`).

### fail2ban

```ini
# /etc/fail2ban/jail.d/asterisk.conf
[asterisk]
enabled  = true
filter   = asterisk
port     = 5060,5061,5160,5080
protocol = all
logpath  = /var/log/asterisk/messages
maxretry = 3
findtime = 600
bantime  = 86400
banaction = iptables-allports
```

```ini
# /etc/fail2ban/filter.d/asterisk.local  (uzupełnienie dla chan_pjsip)
[Definition]
failregex = ^%(__prefix_line)sNOTICE.* .*: Registration from '.*' failed for '<HOST>:\d+' - (Wrong password|No matching endpoint found|Not a local domain)$
            ^%(__prefix_line)sNOTICE.* .*: Request '[A-Z]+' from '.*' failed for '<HOST>:\d+' \(callid: .*\) - (No matching endpoint found|Not a local domain)$
            ^%(__prefix_line)sSECURITY.* .*: SecurityEvent="(FailedACL|InvalidAccountID|ChallengeResponseFailed|InvalidPassword)".*RemoteAddress="IPV[46]/(UDP|TCP|TLS)/<HOST>/\d+"
ignoreregex =
```

Włącz `security` w `/etc/asterisk/logger.conf` (`security => security`), żeby zdarzenia
`SecurityEvent` w ogóle powstawały — to najpewniejsze źródło dla fail2ban.

Konfiguracja bez `bantime` liczonego w dobach nie ma sensu: skanery wracają.

### Oszustwo taryfowe (toll fraud) — realny koszt

Mechanizm: włamywacz zdobywa dane rejestracji albo znajduje otwarty kontekst i przez weekend
generuje tysiące połączeń na numery o podwyższonej opłacie (Kuba, Somalia, Łotwa, Sierra Leone,
numery satelitarne). Zysk dzieli z właścicielem numeru docelowego.

Rachunek: 30 kanałów × 48 godzin × ~4-9 PLN/min na kierunku premium = **od 300 tys. do ponad
700 tys. PLN**. Operator wystawi fakturę i będzie się jej domagał — to twoje połączenia,
wykonane z twojego trunku, po twoim uwierzytelnieniu.

Obowiązkowe zabezpieczenia, w tej kolejności:

1. **Limit kwotowy u operatora** — dobowy i miesięczny, z automatycznym odcięciem.
   To jedyny mechanizm, który zadziała, gdy śpisz. Zażądaj go przy podpisywaniu umowy.
2. **Blokada kierunków premium i egzotycznych** po stronie operatora (nie tylko w planie
   wybierania — atakujący może obejść plan, jeśli zdobędzie dostęp do centrali).
3. Blokada w planie wybierania — biała lista dozwolonych prefiksów zamiast czarnej listy:
   ```ini
   exten => _00[1-9].,1,GotoIf($["${EXTEN:2:2}" =~ "^(49|44|33|39|34|31|32|43|420|421)$"]?ok:blok)
    same => n(blok),NoOp(ZABLOKOWANY KIERUNEK ${EXTEN})
    same => n,Hangup(21)
   ```
4. **Limit równoczesnych połączeń wychodzących** na trunku i na punkt końcowy.
5. **Limit godzinowy** — brak połączeń międzynarodowych poza godzinami pracy:
   ```ini
   exten => _00.,1,GotoIfTime(07:00-19:00,mon-fri,*,*?dalej:blok)
   ```
6. **Alarm przy anomalii** — skrypt sprawdzający CDR co 15 minut: więcej niż N połączeń
   międzynarodowych w oknie albo koszt powyżej progu → SMS do administratora i automatyczne
   `pjsip set endpoint trunk-operator disable`.
7. **Rejestr zmian konfiguracji** — konfiguracja Asteriska w Gicie. Włamywacz często dodaje
   sobie punkt końcowy; różnica w Gicie to pokazuje.

Realna kolejność zdarzeń przy włamaniu: skan → odgadnięcie hasła → rejestracja obcego
urządzenia → połączenia w piątek wieczorem → wykrycie w poniedziałek → faktura. **Alarm
w punkcie 6 skraca to z 60 godzin do 15 minut** i to jest różnica między 500 tys. a 2 tys. PLN.
