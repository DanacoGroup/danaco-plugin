# WebSocket, WebRTC, TURN, serwery mediów

Wersje zweryfikowane sierpień 2026: coturn 4.14.0 (21.06.2026), LiveKit server 1.12.x
(maj 2026 — zmiany w uwierzytelnianiu i uprawnieniach TURN), Janus 1.x, mediasoup 3.x.

## Wybór warstwy — pierwsza decyzja

| Potrzeba | Rozwiązanie | Dlaczego nie inne |
|---|---|---|
| Serwer → przeglądarka, jednokierunkowo (powiadomienia, postęp zadania, dziennik na żywo) | **SSE** (Server-Sent Events) | WebSocket to nadmiar: SSE idzie po zwykłym HTTP, ma wbudowane ponowne łączenie i `Last-Event-ID`, przechodzi przez każde proxy |
| Dwukierunkowo, tekst/JSON, opóźnienie < 100 ms (czat, edycja współbieżna, tablica) | **WebSocket** | SSE nie ma kanału powrotnego; long polling ma większe opóźnienie i koszt |
| Audio/wideo między użytkownikami | **WebRTC** | WebSocket przez TCP powoduje kaskadowe opóźnienia przy utracie pakietu |
| Strumień jednokierunkowy do wielu widzów, opóźnienie 2-5 s akceptowalne | **HLS/LL-HLS** | WebRTC do 10 tys. widzów wymaga drogiej infrastruktury |
| Dane binarne P2P (przesyłanie plików, sygnał sterujący gry) | **WebRTC DataChannel** | omija serwer, ma tryb nieuporządkowany/nierzetelny |

Nie buduj WebSocketa tam, gdzie wystarczy SSE. SSE nie wymaga zmian w reverse proxy poza
wyłączeniem buforowania i jest odporny na zerwania z natury.

## WebSocket

### Uścisk dłoni

```
GET /ws HTTP/1.1
Host: app.przyklad.pl
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: danaco.v1
Origin: https://app.przyklad.pl
```
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: danaco.v1
```

Po `101` to już nie HTTP — ramkowany protokół binarny nad tym samym TCP.

**`Origin` musi być sprawdzany po stronie serwera.** WebSocket **nie podlega CORS**.
Przeglądarka wyśle uścisk dłoni z dowolnej strony, a ciasteczka sesji polecą razem z nim.
Bez sprawdzenia `Origin` masz Cross-Site WebSocket Hijacking:

```python
from fastapi import WebSocket, WebSocketException, status

DOZWOLONE = {"https://app.przyklad.pl", "https://panel.przyklad.pl"}

async def sprawdz_pochodzenie(ws: WebSocket) -> None:
    if ws.headers.get("origin") not in DOZWOLONE:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
```

Uwierzytelnianie: **nie polegaj na ciasteczku sesji**. Przeglądarkowe API `WebSocket` nie
pozwala ustawić nagłówka `Authorization`. Poprawny wzorzec: krótkotrwały token pobrany
zwykłym żądaniem HTTP i przesłany jako **pierwsza wiadomość** po otwarciu (nie w URL —
adresy trafiają do logów proxy).

```python
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await sprawdz_pochodzenie(ws)
    await ws.accept(subprotocol="danaco.v1")
    try:
        pierwsza = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
    except (asyncio.TimeoutError, ValueError):
        await ws.close(code=1008); return
    uzytkownik = zweryfikuj_token(pierwsza.get("token"))
    if uzytkownik is None:
        await ws.close(code=1008); return
    ...
```

### Podtrzymanie połączenia

Protokół ma ramki `PING`/`PONG` na poziomie WebSocketa. Problem: **API przeglądarki ich nie
udostępnia** — nie zainicjujesz PING-a z JavaScriptu. Serwer inicjuje PING, przeglądarka
odpowiada PONG automatycznie.

Dlatego dwa mechanizmy:

1. **Serwer → klient: ramki PING** co 20-30 s. To wykrywa martwe połączenia po stronie serwera
   i utrzymuje wpisy NAT/proxy.
2. **Klient → serwer: własna wiadomość aplikacyjna** (`{"typ":"ping"}`) co 25 s, jeśli
   pośrednik wymaga ruchu od klienta. Serwer odpowiada `{"typ":"pong"}`.

Typowe limity bezczynności: nginx `proxy_read_timeout` domyślnie **60 s**, Cloudflare
100 s, AWS ALB 60 s, Azure App Service 230 s. Interwał podtrzymania musi być
**wyraźnie krótszy niż najkrótszy limit na ścieżce** — 25 s to bezpieczna wartość.

Nagłówek `Sec-WebSocket-Extensions: permessage-deflate` włącza kompresję. Zysk przy JSON-ie
duży, ale kosztuje ~300 kB pamięci na połączenie (okno zlib). Przy 10 tys. połączeń to 3 GB.
Przy dużej liczbie połączeń **wyłącz** albo ustaw `server_max_window_bits=10`.

### Ponowne łączenie

Kod klienta, który obsługuje realne warunki:

```javascript
class TrwalyWebSocket {
  constructor(url, { maxOpoznienie = 30000, przyPolaczeniu, przyWiadomosci } = {}) {
    this.url = url;
    this.maxOpoznienie = maxOpoznienie;
    this.przyPolaczeniu = przyPolaczeniu;
    this.przyWiadomosci = przyWiadomosci;
    this.proba = 0;
    this.zamkniete = false;
    this.kolejka = [];
    this.polacz();
  }

  polacz() {
    this.ws = new WebSocket(this.url, "danaco.v1");

    this.ws.onopen = async () => {
      this.proba = 0;
      await this.przyPolaczeniu?.(this.ws);        // wyślij token, odtwórz subskrypcje
      for (const w of this.kolejka.splice(0)) this.ws.send(w);
    };

    this.ws.onmessage = (e) => this.przyWiadomosci?.(JSON.parse(e.data));

    this.ws.onclose = (e) => {
      if (this.zamkniete || e.code === 1008) return;   // 1008 = odrzucenie polityką
      // wykładnicze wycofanie z rozrzutem (jitter) — bez rozrzutu wszyscy wracają naraz
      const bazowe = Math.min(1000 * 2 ** this.proba++, this.maxOpoznienie);
      const opoznienie = bazowe * (0.5 + Math.random() * 0.5);
      setTimeout(() => this.polacz(), opoznienie);
    };

    this.ws.onerror = () => this.ws.close();
  }

  wyslij(obiekt) {
    const dane = JSON.stringify(obiekt);
    if (this.ws.readyState === WebSocket.OPEN) this.ws.send(dane);
    else this.kolejka.push(dane);                 // ogranicz długość kolejki w produkcji
  }

  zamknij() { this.zamkniete = true; this.ws.close(1000); }
}
```

Elementy, których brak w typowej implementacji:

- **Rozrzut (jitter)** w wycofaniu. Bez niego restart serwera powoduje, że 5000 klientów
  próbuje się połączyć w tej samej milisekundzie i kładzie serwer ponownie.
- **Odtworzenie stanu po `onopen`** — token, subskrypcje kanałów, pozycja w strumieniu
  zdarzeń. Ponowne połączenie zaczyna od zera; serwer o niczym nie pamięta.
- **Nie ponawiaj po `1008`/`1003`** — to odmowa polityki, ponawianie tylko generuje ruch.
- **Odtworzenie luki w zdarzeniach.** Klient przechowuje identyfikator ostatniego zdarzenia
  i po połączeniu prosi o różnicę. Bez tego zerwanie na 3 s = trwała rozbieżność stanu.

Kody zamknięcia: `1000` normalne, `1001` odejście, `1006` **nienormalne (brak ramki close —
najczęstsze w praktyce, oznacza zerwanie TCP)**, `1008` naruszenie polityki, `1011` błąd
serwera, `1012` restart, `1013` spróbuj później, `4000-4999` własne.

### Skalowanie

Jeden proces utrzyma 10-50 tys. połączeń WebSocket (pamięć ~10-40 kB/połączenie plus bufory).
Ograniczeniem jest zwykle pamięć i liczba deskryptorów, nie CPU.

```bash
# limity systemowe — bez tego zatrzymasz się na 1024 połączeniach
ulimit -n 200000
sysctl -w fs.file-max=500000
sysctl -w net.core.somaxconn=8192
sysctl -w net.ipv4.tcp_max_syn_backlog=8192
```

**Przyleganie sesji (sticky sessions) — czy jest potrzebne**

WebSocket to jedno długie połączenie TCP: po nawiązaniu i tak trafia zawsze do tego samego
procesu. Przyleganie potrzebne jest tylko wtedy, gdy:

- używasz transportu awaryjnego z długim odpytywaniem (Socket.IO z `polling`) — **wtedy tak,
  obowiązkowo**, bo kolejne żądania HTTP muszą trafiać do tego samego procesu;
- stan sesji trzymasz w pamięci procesu.

Rozwiązanie skalowalne: **stan poza procesem** (Redis) + rozgłaszanie między procesami.

```
Klient A ──┐                        ┌── proces 1 ──┐
Klient B ──┼── reverse proxy ───────┼── proces 2 ──┼── Redis Pub/Sub
Klient C ──┘                        └── proces 3 ──┘
```

Każdy proces subskrybuje kanały Redis dla pokojów, w których ma klientów. Publikacja
wiadomości trafia do wszystkich procesów; każdy wysyła tylko do swoich połączeń.
Biblioteki: `socket.io-redis-adapter` (Node), `broadcaster`/`redis.asyncio` (Python),
Django Channels z `channels_redis`.

Ograniczenie Redis Pub/Sub: **brak trwałości**. Wiadomość opublikowana, gdy proces był
odłączony, przepada. Do gwarancji dostarczenia użyj Redis Streams z grupami konsumentów albo
NATS JetStream.

Wdrożenie nowej wersji zrywa wszystkie połączenia naraz. Łagodzenie: `1012 Service Restart`
przed zamknięciem, rozłożone wyłączanie procesów (drain), po stronie klienta wycofanie
z rozrzutem.

### SSE jako alternatywa

```python
from fastapi.responses import StreamingResponse

@app.get("/zdarzenia")
async def zdarzenia(request: Request, last_event_id: str | None = Header(None)):
    async def generator():
        async for zd in strumien_od(last_event_id):
            yield f"id: {zd.id}\nevent: {zd.typ}\ndata: {json.dumps(zd.dane)}\n\n"
            if await request.is_disconnected():
                break
    return StreamingResponse(generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",          # WYMAGANE przy nginx, inaczej bufor zjada strumień
        "Connection": "keep-alive",
    })
```

Zalety SSE: automatyczne ponowne łączenie w przeglądarce, `Last-Event-ID` odtwarzający lukę
bez kodu, zwykły HTTP (proxy, HTTP/2, cache — wszystko działa), prostota.

Wady: jednokierunkowo; **przy HTTP/1.1 limit 6 połączeń na domenę w przeglądarce**
(przy HTTP/2 problem znika — multipleksowanie); tylko tekst.

`X-Accel-Buffering: no` jest obowiązkowy przy nginx. Bez niego nginx buforuje odpowiedź
i klient nie dostaje nic aż do zapełnienia bufora — objaw „SSE nie działa, choć na localhost
działało”.

## WebRTC

Trzy elementy: **sygnalizacja** (twoja, poza WebRTC), **ICE/STUN/TURN** (znalezienie ścieżki),
**media** (SRTP, szyfrowanie obowiązkowe).

### Sygnalizacja

WebRTC nie definiuje sygnalizacji. Musisz przenieść między stronami: SDP oferty, SDP
odpowiedzi i kandydatów ICE. Zwykle WebSocketem.

```javascript
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: "stun:stun.przyklad.pl:3478" },
    {
      urls: ["turn:turn.przyklad.pl:3478?transport=udp",
             "turn:turn.przyklad.pl:3478?transport=tcp",
             "turns:turn.przyklad.pl:5349?transport=tcp"],
      username: poswiadczenia.username,     // z serwera, krótkotrwałe!
      credential: poswiadczenia.credential,
    },
  ],
  iceTransportPolicy: "all",       // "relay" wymusza TURN — do testów
  bundlePolicy: "max-bundle",
  rtcpMuxPolicy: "require",
});

// kandydaci ICE pojawiają się asynchronicznie — wysyłaj je na bieżąco (trickle ICE)
pc.onicecandidate = ({ candidate }) => {
  if (candidate) sygnalizacja.wyslij({ typ: "candidate", candidate });
};

pc.onconnectionstatechange = () => {
  if (pc.connectionState === "failed") pc.restartIce();   // nie twórz nowego RTCPeerConnection
};

// strona inicjująca
const oferta = await pc.createOffer();
await pc.setLocalDescription(oferta);
sygnalizacja.wyslij({ typ: "oferta", sdp: pc.localDescription });

// strona odbierająca
await pc.setRemoteDescription(otrzymanaOferta);
const odpowiedz = await pc.createAnswer();
await pc.setLocalDescription(odpowiedz);
sygnalizacja.wyslij({ typ: "odpowiedz", sdp: pc.localDescription });
```

Pułapki sygnalizacji:

- **Trickle ICE**: nie czekaj na `icegatheringstate === "complete"` przed wysłaniem oferty.
  Czekanie dodaje 2-10 s do czasu nawiązania (a przy niedostępnym STUN — pełny timeout).
- **Kolizja ofert (glare)**: obie strony wysyłają ofertę jednocześnie. Rozwiązanie — wzorzec
  „perfect negotiation” z rolami `polite`/`impolite` (strona uprzejma wycofuje swoją ofertę).
- Kandydaci przychodzące przed `setRemoteDescription` trzeba **kolejkować**, inaczej
  `addIceCandidate` rzuca wyjątek.
- `restartIce()` przy `failed` zamiast tworzenia nowego połączenia — zachowuje strumienie
  i jest o rząd wielkości szybszy.

### ICE, STUN, TURN

| | STUN | TURN |
|---|---|---|
| Rola | „jaki mam adres publiczny?” | przekaźnik mediów |
| Ruch przez serwer | nie | **cały ruch audio/wideo** |
| Koszt pasma | znikomy | pełny: ~1,5 Mb/s na uczestnika wideo HD, w obie strony |
| Kiedy potrzebny | prawie zawsze | ~10-20 % połączeń (NAT symetryczny, sieci korporacyjne, mobilne CGNAT) |
| Port | 3478/udp | 3478/udp+tcp, 5349/tls |

Typy kandydatów w kolejności preferencji ICE: `host` (adres lokalny) → `srflx`
(server-reflexive, z STUN) → `prf` (peer-reflexive) → `relay` (TURN).

**Publiczny STUN Google (`stun:stun.l.google.com:19302`) nadaje się do prototypu, nie do
produkcji** — brak SLA, ograniczenia szybkości, i to przekazywanie informacji o twoich
użytkownikach do Google (kwestia RODO). Postaw własny coturn: pełni obie role naraz.

### coturn — konfiguracja produkcyjna

coturn 4.14.0 (21.06.2026) dodał HTTPS dla Prometheusa, TLS do Redisa i eksperymentalne
ograniczanie odpowiedzi `401` (obrona przed atakami odbiciowymi).

`/etc/turnserver.conf`:

```
listening-port=3478
tls-listening-port=5349

# adres publiczny; przy serwerze za NAT: listening-ip=adres prywatny, external-ip=publiczny
listening-ip=0.0.0.0
external-ip=203.0.113.60
relay-ip=203.0.113.60

realm=turn.przyklad.pl
server-name=turn.przyklad.pl

# --- uwierzytelnianie krótkotrwałe (REST API) — JEDYNE poprawne dla produkcji ---
use-auth-secret
static-auth-secret=DlugiLosowySekret64ZnakiZmienGoOkresowo0123456789abcdef
# NIE używaj: lt-cred-mech + user=jan:haslo  (poświadczenia trafiają do kodu front-endu)

# --- TLS ---
cert=/etc/letsencrypt/live/turn.przyklad.pl/fullchain.pem
pkey=/etc/letsencrypt/live/turn.przyklad.pl/privkey.pem
no-tlsv1
no-tlsv1_1

# --- zakres portów przekaźnika (otwórz na zaporze!) ---
min-port=49160
max-port=49200

# --- bezpieczeństwo: TURN bez tego jest otwartym proxy ---
no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
denied-peer-ip=::1
denied-peer-ip=fc00::-fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff
no-cli
no-tcp-relay

# --- limity ---
user-quota=12
total-quota=1200
max-bps=1500000            # 1,5 Mb/s na sesję
stale-nonce=600

# --- dzienniki ---
log-file=/var/log/turnserver.log
simple-log
verbose
```

**Bez `denied-peer-ip` dla sieci prywatnych TURN staje się bramą do twojej sieci wewnętrznej.**
Atakujący z poświadczeniami TURN może przez niego dosięgnąć `10.0.0.0/8` i skanować bazy danych.
To realny, wielokrotnie wykorzystywany wektor.

Poświadczenia krótkotrwałe generowane przez backend:

```python
import hmac, hashlib, base64, time

SEKRET = b"DlugiLosowySekret64ZnakiZmienGoOkresowo0123456789abcdef"

def poswiadczenia_turn(id_uzytkownika: str, waznosc_s: int = 3600) -> dict:
    wygasa = int(time.time()) + waznosc_s
    username = f"{wygasa}:{id_uzytkownika}"
    haslo = base64.b64encode(
        hmac.new(SEKRET, username.encode(), hashlib.sha1).digest()
    ).decode()
    return {
        "username": username,
        "credential": haslo,
        "ttl": waznosc_s,
        "uris": [
            "turn:turn.przyklad.pl:3478?transport=udp",
            "turn:turn.przyklad.pl:3478?transport=tcp",
            "turns:turn.przyklad.pl:5349?transport=tcp",
        ],
    }
```

Statyczne poświadczenia w kodzie front-endu = darmowy przekaźnik dla całego internetu na twoim
rachunku za transfer. Ważność 1-4 h wystarcza.

Test:

```bash
# sprawdzenie, czy TURN w ogóle działa (i czy zwraca kandydatów relay)
turnutils_uclient -T -u 1754300000:test -w <haslo> turn.przyklad.pl
# w przeglądarce: https://icetest.info/ albo webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
```

W teście trickle-ICE musisz zobaczyć kandydata typu **`relay`**. Jeśli widzisz tylko `host`
i `srflx`, TURN nie działa — i dowiesz się o tym dopiero od użytkownika w sieci korporacyjnej.

### Media

```javascript
const strumien = await navigator.mediaDevices.getUserMedia({
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    channelCount: 1,
    sampleRate: 48000,
  },
  video: {
    width:  { ideal: 1280, max: 1920 },
    height: { ideal: 720,  max: 1080 },
    frameRate: { ideal: 30, max: 30 },
    facingMode: "user",
  },
});
strumien.getTracks().forEach((t) => pc.addTrack(t, strumien));
```

`getUserMedia` wymaga **bezpiecznego kontekstu**: HTTPS albo `localhost`. Na `http://192.168.1.5`
API nie istnieje — to najczęstsze „u mnie działa, na testowym nie”.

Uprawnienia: pierwsze wywołanie pokazuje pytanie przeglądarki. Odmowa daje
`NotAllowedError`; brak urządzenia `NotFoundError`; urządzenie zajęte przez inną aplikację
`NotReadableError`. Obsłuż wszystkie trzy osobnym komunikatem — „nie działa kamera” bez
diagnozy generuje zgłoszenia.

Udostępnianie ekranu:

```javascript
const ekran = await navigator.mediaDevices.getDisplayMedia({
  video: { frameRate: { ideal: 15, max: 30 }, displaySurface: "monitor" },
  audio: { suppressLocalAudioPlayback: false },   // dźwięk karty/zakładki, gdzie wspierane
  selfBrowserSurface: "exclude",                  // nie proponuj bieżącej karty (efekt lustra)
  systemAudio: "include",
});
// użytkownik może zatrzymać z paska przeglądarki — obsłuż to
ekran.getVideoTracks()[0].onended = () => zatrzymajUdostepnianie();

// podmiana ścieżki bez renegocjacji SDP:
const nadajnik = pc.getSenders().find((s) => s.track?.kind === "video");
await nadajnik.replaceTrack(ekran.getVideoTracks()[0]);
```

`replaceTrack` zamiast `removeTrack` + `addTrack` — brak renegocjacji, brak przerwy w obrazie.

Kodeki 2026:

| Kodek | Stan |
|---|---|
| **Opus** | audio, uniwersalny, obowiązkowy w każdej przeglądarce. Domyślny wybór |
| **VP8** | wideo, obowiązkowy, uniwersalny, sprzętowe dekodowanie powszechne |
| **H.264** (baseline) | obowiązkowy, sprzętowe kodowanie/dekodowanie na urządzeniach mobilnych — mniejsze zużycie baterii |
| **VP9** | lepsza kompresja niż VP8, wsparcie szerokie, wyższy koszt CPU; SVC |
| **AV1** | ~30 % lepsza kompresja niż VP9; wsparcie w Chrome/Edge/Firefox; kodowanie kosztowne bez sprzętu, sprzętowe dopiero w nowszych GPU. Sensowne przy niskich przepływnościach i udostępnianiu ekranu |
| **H.265/HEVC** | wprowadzany do WebRTC (draft IETF `avtcore-hevc-webrtc`, wdrożenia w Chrome i produktach strumieniowych). `[niepotwierdzone: pełny zakres wsparcia H.265 w przeglądarkach na sierpień 2026]` |
| `audio/red` | redundancja Opusa — znacząco poprawia jakość przy utracie pakietów. Włącz przy złych łączach |

Zasada: **zostaw negocjację kodeków przeglądarce**, chyba że masz konkretny powód. Wymuszanie
kodeka przez modyfikację SDP jest kruche i psuje się przy każdej aktualizacji przeglądarki.

### Topologie

| Topologia | Jak działa | Pasmo nadawania na klienta (N uczestników) | Sensowne dla |
|---|---|---|---|
| **Mesh** (P2P) | każdy z każdym | (N−1) × przepływność | **2-4 uczestników**, maks. 5 |
| **SFU** | serwer rozsyła strumienie bez dekodowania | 1 × przepływność (odbiór N−1) | **5-200**; standard branżowy |
| **MCU** | serwer miksuje w jeden strumień | 1 × (odbiór 1 ×) | urządzenia słabe, nagrywanie, integracja z SIP; kosztowne CPU, dodaje opóźnienie |

Mesh przy 5 uczestnikach wideo HD to ~6 Mb/s wysyłania na każdego — powyżej możliwości
większości łączy asymetrycznych w Polsce. **Powyżej 4 uczestników zawsze SFU.**

### Gotowe serwery mediów

| | LiveKit | mediasoup | Janus |
|---|---|---|---|
| Język / postać | Go, gotowy serwer | C++ z warstwą Node — **biblioteka, nie serwer** | C z modułami |
| Model użycia | wdrażasz i używasz SDK | budujesz własny serwer sygnalizacyjny wokół API | wybierasz moduły (videoroom, sip, streaming, record) |
| SDK klienckie | JS, React, Swift, Kotlin, Flutter, Unity, Python, Go | JS (mediasoup-client) | JS (janus.js), społecznościowe |
| Nakład wdrożenia | najmniejszy | największy | średni |
| Kontrola szczegółów | średnia | pełna | duża |
| Wbudowane: nagrywanie, SIP, agenci AI | tak (Egress/Ingress/SIP/Agents) | nie | moduły `record`, `sip` |
| Skalowanie | wielowęzłowe z Redisem | budujesz sam | kaskada modułów |
| Licencja | Apache-2.0 | ISC | GPLv3 (uwaga przy produkcie zamkniętym) |
| Kiedy wybrać | **domyślnie** — wideokonferencja, agent głosowy, transmisja | gdy potrzebujesz pełnej kontroli i masz zespół | gdy potrzebujesz bramki SIP↔WebRTC albo nietypowego modułu |

LiveKit 1.12 (maj 2026) zmienił obsługę uwierzytelniania i uprawnień TURN — przy aktualizacji
z wcześniejszych wersji sprawdź konfigurację TURN, bo stare ustawienia mogą przestać działać.

Minimalne wdrożenie LiveKit:

```yaml
# livekit.yaml
port: 7880
rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: true
turn:
  enabled: true
  domain: turn.przyklad.pl
  tls_port: 5349
  cert_file: /etc/letsencrypt/live/turn.przyklad.pl/fullchain.pem
  key_file: /etc/letsencrypt/live/turn.przyklad.pl/privkey.pem
keys:
  APIklucz: sekretDlugiNaConajmniej32Znaki
redis:
  address: redis:6379
```

Token dostępu generuje backend (nigdy front-end):

```python
from livekit import api

def token_pokoju(pokoj: str, tozsamosc: str, nazwa: str) -> str:
    return (
        api.AccessToken("APIklucz", "sekretDlugiNaConajmniej32Znaki")
        .with_identity(tozsamosc)
        .with_name(nazwa)
        .with_grants(api.VideoGrants(
            room_join=True, room=pokoj,
            can_publish=True, can_subscribe=True, can_publish_data=True,
        ))
        .with_ttl(timedelta(hours=2))
        .to_jwt()
    )
```

### Nagrywanie

Trzy miejsca, trzy kompromisy:

1. **W przeglądarce** (`MediaRecorder`) — najprostsze, ale nagrywa tylko lokalny strumień,
   ginie przy zamknięciu karty, obciąża urządzenie użytkownika.
2. **Na SFU** (LiveKit Egress, Janus `record`) — nagrywa wszystkie strumienie, niezawodne,
   wymaga miksowania do jednego pliku (kosztowne) albo daje osobne pliki na uczestnika.
3. **Osobny uczestnik-nagrywacz** (headless Chrome dołączający do pokoju) — daje dokładnie to,
   co widzi użytkownik, kosztuje jeden rdzeń + ~1 GB RAM na nagranie.

Prawnie: nagrywanie rozmowy wideo podlega tym samym regułom co nagrywanie rozmowy telefonicznej —
patrz sekcja o nagrywaniu w
`references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md`. Poinformowanie
**przed** rozpoczęciem, widoczny wskaźnik nagrywania w interfejsie przez cały czas trwania, podstawa
prawna, retencja, kasowanie.

## WebRTC ↔ SIP: softphone w przeglądarce

Asterisk obsługuje WebRTC natywnie przez transport `wss` — nie potrzebujesz bramki.

```ini
; pjsip.conf — punkt końcowy dla przeglądarki
[900-webrtc]
type=endpoint
context=wewnetrzne
disallow=all
allow=opus,ulaw,alaw
auth=900-auth
aors=900-webrtc
webrtc=yes                 ; ustawia naraz: dtls_auto_generate_cert, ice_support,
                           ; use_avpf, media_encryption=dtls, rtcp_mux, media_use_received_transport
transport=transport-wss
direct_media=no
dtls_verify=fingerprint
dtls_setup=actpass

[900-auth]
type=auth
auth_type=userpass
username=900
password=LosoweHaslo24ZnakiMinimum

[900-webrtc]
type=aor
max_contacts=1
remove_existing=yes
```

`webrtc=yes` w Asterisku 22 zastępuje sześć osobnych opcji — konfiguracje z poradników
sprzed 2020 ustawiają je ręcznie i często niekompletnie.

Klient przeglądarkowy: **SIP.js** albo **JsSIP** (oba dojrzałe). Nad WebSocketem trzeba
podać podprotokół `sip`:

```javascript
import { UserAgent, Registerer, Inviter } from "sip.js";

const ua = new UserAgent({
  uri: UserAgent.makeURI("sip:900@pbx.przyklad.pl"),
  authorizationUsername: "900",
  authorizationPassword: haslo,             // z backendu, krótkotrwałe
  transportOptions: { server: "wss://pbx.przyklad.pl:8089/ws" },
  sessionDescriptionHandlerFactoryOptions: {
    peerConnectionConfiguration: { iceServers: (await pobierzPoswiadczeniaTurn()).uris },
  },
});
await ua.start();
await new Registerer(ua).register();

const rozmowa = new Inviter(ua, UserAgent.makeURI("sip:600123456@pbx.przyklad.pl"));
await rozmowa.invite();
```

Wymagania, bez których to nie zadziała:

- **HTTPS na stronie** (bezpieczny kontekst dla `getUserMedia`) i **`wss`** (nie `ws`) —
  przeglądarka blokuje niezabezpieczony WebSocket ze strony HTTPS.
- **Ważny certyfikat** na porcie 8089 Asteriska. Certyfikat samopodpisany działa dopiero po
  ręcznej akceptacji w przeglądarce (i nie działa wcale w kontekście `wss` w tle).
- **Opus na trunku operatorskim nie przejdzie** — Asterisk transkoduje Opus↔G.711 przy
  wyjściu na miasto. Policz CPU: ~50-80 równoczesnych transkodowań na rdzeń.
- **TURN jest obowiązkowy** dla użytkowników w sieciach korporacyjnych i mobilnych.
  Bez TURN „u części pracowników nie ma dźwięku” i nie znajdziesz wzoru.
- Hasło SIP nie może być w kodzie front-endu. Generuj krótkotrwałe poświadczenia po stronie
  serwera (Asterisk z bazą realtime i tymczasowymi kontami) albo terminuj SIP w backendzie
  i wystawiaj własne API.

Diagnostyka WebRTC — `chrome://webrtc-internals` w Chrome. Zakładka z wykresami pokazuje
wybraną parę kandydatów, przepływność, utratę pakietów, jitter i zmiany kodeka w czasie.
To jedyne narzędzie, które odpowiada na pytanie „dlaczego u tego jednego użytkownika nie ma
obrazu”: jeśli para kandydatów jest typu `relay`/`relay`, przechodzi przez TURN; jeśli nie ma
pary — ICE zawiódł.
