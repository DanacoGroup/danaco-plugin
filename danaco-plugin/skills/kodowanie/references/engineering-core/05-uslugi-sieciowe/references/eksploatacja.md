# Eksploatacja: TLS, DNS, odwrotne proxy, kontenery, kopie, monitorowanie

Wersje zweryfikowane sierpień 2026: nginx 1.30.0 stabilne (2.05.2026), Caddy 2.x,
Traefik v3.x, coturn 4.14.0.

## TLS i certyfikaty

### Let's Encrypt — co zmieniło się w 2026

| Zmiana | Data | Konsekwencja |
|---|---|---|
| Certyfikaty **6-dniowe** i **na adres IP** — dostępność ogólna | 15.01.2026 | możliwe zabezpieczenie usług bez nazwy domenowej; wymaga w pełni sprawnej automatyzacji |
| Certbot wspiera certyfikaty na adres IP | marzec 2026 | `certbot certonly --standalone -d 203.0.113.5` (tylko walidacja HTTP-01/TLS-ALPN-01) |
| Zmiana certyfikatów głównych | 13.05.2026 | sprawdź magazyny zaufania na starych systemach i urządzeniach |
| Koniec profilu `tlsclient` (uwierzytelnianie klienta) | 8.07.2026 | certyfikaty do mTLS z Let's Encrypt **przestały być wydawane** — użyj własnego CA |
| Koniec wysyłania powiadomień o wygaśnięciu e-mailem | 2025 | **monitoruj wygaśnięcia sam** — nikt cię nie ostrzeże |

Profile certyfikatów (parametr `--preferred-profile` w klientach ACME):

| Profil | Ważność | Maks. nazw | Uwagi |
|---|---|---|---|
| `classic` | 90 dni | 100 | domyślny; zawiera Common Name |
| `tlsserver` | 45 dni | 25 | mniejszy certyfikat, bez CN i SKID |
| `shortlived` | 160 h (~6,7 dnia) | 25 | dla w pełni zaufanej automatyzacji; brak potrzeby odwoływania |
| `tlsclient` | — | — | **wycofany 8.07.2026** |

Odnawiaj przy **1/3 pozostałego czasu życia**: 30 dni dla `classic`, 15 dni dla `tlsserver`,
~2 dni dla `shortlived`.

### ACME — wybór metody walidacji

| Metoda | Wymaga | Certyfikat wieloznaczny | Kiedy |
|---|---|---|---|
| HTTP-01 | port 80 osiągalny z internetu, plik pod `/.well-known/acme-challenge/` | **nie** | domyślnie dla usług WWW |
| TLS-ALPN-01 | port 443, wsparcie w serwerze | nie | gdy port 80 zamknięty |
| DNS-01 | dostęp API do strefy DNS | **tak** | wieloznaczne, usługi bez publicznego HTTP (poczta, TURN, SIP), serwery wewnętrzne |

Certyfikat wieloznaczny `*.przyklad.pl` **wymaga DNS-01**. Nie ma innej drogi.
`*.przyklad.pl` **nie obejmuje** `przyklad.pl` ani `a.b.przyklad.pl` — potrzebujesz obu nazw
w jednym certyfikacie: `-d przyklad.pl -d '*.przyklad.pl'`.

DNS-01 z dostawcą polskim (przykład: `home.pl`, `nazwa.pl`, `OVH`) — użyj wtyczki certbota
albo `lego`/`acme.sh` z odpowiednim dostawcą. Gdy dostawca nie ma API, użyj **delegacji
`_acme-challenge`** przez CNAME do strefy, którą kontrolujesz:

```dns
_acme-challenge.przyklad.pl.  IN CNAME _acme-challenge.przyklad.pl.acme.mojastrefa.pl.
```

Wtedy klient ACME modyfikuje tylko `acme.mojastrefa.pl` i nie ma dostępu do głównej strefy —
to również właściwe rozwiązanie z punktu widzenia bezpieczeństwa.

```bash
# certbot, DNS-01, Cloudflare, certyfikat wieloznaczny
certbot certonly \
  --dns-cloudflare --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 30 \
  -d przyklad.pl -d '*.przyklad.pl' \
  --preferred-profile tlsserver \
  --key-type ecdsa --elliptic-curve secp384r1 \
  --deploy-hook '/usr/local/bin/przeladuj-uslugi.sh'
```

`/usr/local/bin/przeladuj-uslugi.sh`:

```bash
#!/bin/bash
set -euo pipefail
systemctl reload nginx
systemctl reload postfix
doveadm reload
systemctl restart coturn        # coturn nie umie przeładować certyfikatu bez restartu
asterisk -rx "module reload res_pjsip"
```

`--deploy-hook` uruchamia się **tylko po faktycznym odnowieniu**, nie przy każdym sprawdzeniu.
Brak przeładowania usług to najczęstsza przyczyna „certyfikat odnowiony, a przeglądarka
pokazuje stary/wygasły” — serwer trzyma stary w pamięci.

Odnawianie w cronie/timerze **dwa razy dziennie w losowej minucie**:

```
17 3,15 * * * certbot renew --quiet --deploy-hook /usr/local/bin/przeladuj-uslugi.sh
```

Monitorowanie wygaśnięcia (obowiązkowe, odkąd Let's Encrypt nie wysyła powiadomień):

```bash
#!/bin/bash
for cel in przyklad.pl:443 mail.przyklad.pl:993 turn.przyklad.pl:5349 pbx.przyklad.pl:5061 mta-sts.przyklad.pl:443; do
  host=${cel%%:*}; port=${cel##*:}
  koniec=$(echo | openssl s_client -connect "$cel" -servername "$host" 2>/dev/null \
           | openssl x509 -noout -enddate | cut -d= -f2)
  dni=$(( ($(date -d "$koniec" +%s) - $(date +%s)) / 86400 ))
  [ "$dni" -lt 14 ] && echo "ALARM: $cel wygasa za $dni dni"
done
```

Uwzględnij **wszystkie** punkty końcowe, nie tylko WWW: IMAP, submission, TURN, SIP-TLS, MTA-STS.
Wygasły certyfikat na `mta-sts.przyklad.pl` przy `mode: enforce` odbija całą pocztę przychodzącą
(patrz `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md`).

### Konfiguracja TLS

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;              # przy TLS 1.3 kolejność klienta jest lepsza
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;                    # bilety psują forward secrecy bez rotacji kluczy
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
```

`ssl_stapling` przestaje mieć znaczenie — Let's Encrypt wygasił OCSP; nowoczesne przeglądarki
używają list CRLite/OneCRL. Zostawienie `ssl_stapling on;` bez działającego respondera daje
opóźnienie przy pierwszym połączeniu.

HSTS: `max-age` 2 lata dopiero po pewności, że **wszystkie** subdomeny mają HTTPS.
`includeSubDomains` z jedną subdomeną bez certyfikatu wyłącza ją dla wszystkich, którzy raz
odwiedzili domenę główną — i nie da się tego cofnąć przed upływem `max-age`.

## DNS

### Typy rekordów w praktyce

| Typ | Do czego | Uwaga |
|---|---|---|
| `A` / `AAAA` | nazwa → IPv4 / IPv6 | brak AAAA przy działającym IPv6 u odbiorcy = opóźnienie Happy Eyeballs |
| `CNAME` | alias nazwy | **nie może współistnieć z innymi rekordami tej samej nazwy** i nie może być w korzeniu strefy |
| `ALIAS`/`ANAME`/`CNAME flattening` | CNAME w korzeniu | rozszerzenie dostawcy (Cloudflare, Route 53), nie standard |
| `MX` | serwery poczty; niższy priorytet = wyższy wybór | wartość musi być nazwą, **nigdy adresem IP** |
| `TXT` | SPF, DKIM, DMARC, weryfikacje | jeden łańcuch ≤ 255 znaków; dłuższe dzielone na kilka w jednym rekordzie |
| `SRV` | usługa+protokół → host:port | `_sip._udp.przyklad.pl. 3600 IN SRV 10 50 5060 pbx.przyklad.pl.` |
| `CAA` | które CA mogą wydać certyfikat | `przyklad.pl. IN CAA 0 issue "letsencrypt.org"` — postaw, blokuje wydanie przez inne CA |
| `PTR` | IP → nazwa (odwrotny) | **w strefie operatora IP**, nie w twojej; ustawia się w panelu VPS |
| `NS` | delegacja strefy | |
| `TLSA` | DANE (przypięcie certyfikatu) | wymaga DNSSEC |
| `SVCB`/`HTTPS` | parametry usługi (ALPN, ECH, port) | wsparcie rośnie; `HTTPS` pozwala pominąć przekierowanie z HTTP |

### TTL

| Sytuacja | TTL |
|---|---|
| Stan ustalony | 3600 s (1 h) — kompromis |
| Rekordy rzadko zmieniane (MX, DKIM, SPF) | 3600-86400 s |
| **Przed planowaną zmianą** | obniż do **300 s co najmniej 2× stary TTL wcześniej** |
| Po zmianie, gdy wszystko działa | podnieś z powrotem |

Sekwencja migracji serwera bez przerwy:

```
T-48 h  obniż TTL rekordu A z 3600 na 300
T-24 h  (stary TTL już wygasł u wszystkich — teraz zmiany propagują się w 5 min)
T-0     przełącz A na nowy adres; stary serwer pracuje dalej
T+2 h   sprawdź logi starego serwera — jeśli pusto, wyłącz
T+24 h  podnieś TTL z powrotem na 3600
```

Pominięcie kroku T-48 h oznacza, że przez godzinę część ruchu idzie na wyłączony serwer.

**Negatywny TTL** (parametr `minimum` w rekordzie SOA) określa, jak długo buforowana jest
odpowiedź „nie ma takiego rekordu”. Jeśli sprawdzałeś nazwę **przed** jej utworzeniem, twój
resolver trzyma NXDOMAIN przez ten czas — stąd „dodałem rekord, a `dig` nadal nic nie widzi”.
Ustaw SOA `minimum` na 300-900 s.

### Delegacja i DNSSEC

Delegacja: rekordy `NS` u rejestratora (w strefie nadrzędnej) muszą wskazywać na te same
serwery, które są autorytatywne. Rozjazd między `NS` u rejestratora a `NS` w samej strefie
daje sporadyczne, nieodtwarzalne błędy rozwiązywania.

DNSSEC: podpisuje odpowiedzi; chroni przed zatruciem bufora i **jest warunkiem DANE**.

```bash
# czy strefa jest podpisana i łańcuch zaufania działa
dig +dnssec +multi przyklad.pl SOA
delv przyklad.pl                       # "fully validated" = OK
dig +short DS przyklad.pl @a.dns.pl    # rekord DS musi być w strefie nadrzędnej (.pl)
```

Ryzyko: rekord `DS` u rejestratora niezgodny z kluczem `DNSKEY` w strefie = **cała domena
znika** dla walidujących resolverów (a to Google DNS, Cloudflare i większość operatorów).
Przy zmianie dostawcy DNS z DNSSEC: najpierw wyłącz DNSSEC (usuń DS, odczekaj TTL), przenieś,
włącz ponownie. Nie przenoś „na żywo”.

W domenie `.pl` DNSSEC włącza się przez rejestratora (NASK wymaga przekazania DS przez
partnera). Nie wszyscy rejestratorzy to obsługują.

### Propagacja — czego model nie rozumie

„Propagacja DNS” nie istnieje jako proces. Serwery autorytatywne mają nowy rekord
**natychmiast**. To, co trwa, to **wygasanie buforów** resolverów — dokładnie tyle, ile
wynosił stary TTL.

```bash
dig +short A przyklad.pl @8.8.8.8          # Google — sprawdź co widzi
dig +short A przyklad.pl @1.1.1.1          # Cloudflare
dig +short A przyklad.pl @ns1.dostawca.pl  # autorytatywny — prawda źródłowa
dig +trace przyklad.pl                     # cała ścieżka od korzenia
```

Jeśli autorytatywny zwraca nowy adres, a Google stary — czekasz na TTL. Nic więcej nie da się
zrobić (poza tym, że niektóre publiczne resolvery mają formularz czyszczenia bufora).

## Odwrotne proxy

### Wybór

| | nginx | Caddy | Traefik |
|---|---|---|---|
| Konfiguracja | własny język, jawna | `Caddyfile`, zwięzła | etykiety kontenerów / plik dynamiczny |
| HTTPS | ręcznie + certbot | **automatycznie, domyślnie** | automatycznie (ACME wbudowane) |
| HTTP/3 | od 1.25 (moduł `quic`) | domyślnie | tak |
| Odkrywanie usług | brak | brak | **Docker, Kubernetes, Consul** |
| Przeładowanie bez przerwy | `nginx -s reload` | `caddy reload` | automatyczne |
| Kiedy wybrać | statyka, precyzyjne strojenie, duży ruch, istniejąca wiedza | pojedynczy serwer, chcesz skończyć w 10 minut | wiele kontenerów o zmiennym składzie |

nginx 1.30.0 (2.05.2026) przyniósł: Early Hints, HTTP/2 do serwera zaplecza, Encrypted
ClientHello, trwałe sesje w `upstream`, Multipath TCP, oraz **zmianę domyślnej wersji
protokołu do zaplecza na HTTP/1.1 z keep-alive**. Ta ostatnia zmiana wpływa na zachowanie
starych konfiguracji, które polegały na HTTP/1.0.

### nginx — aplikacja + WebSocket + SSE

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream aplikacja {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name app.przyklad.pl;

    ssl_certificate     /etc/letsencrypt/live/app.przyklad.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.przyklad.pl/privkey.pem;

    client_max_body_size 25m;

    location / {
        proxy_pass http://aplikacja;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host  $host;
        proxy_set_header Connection "";          # keepalive do zaplecza
    }

    location /ws {
        proxy_pass http://aplikacja;
        proxy_http_version 1.1;                  # WYMAGANE — HTTP/1.0 nie umie Upgrade
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host       $host;
        proxy_set_header X-Real-IP  $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout  3600s;               # domyślne 60 s zrywa WebSocket co minutę
        proxy_send_timeout  3600s;
        proxy_buffering off;
    }

    location /zdarzenia {
        proxy_pass http://aplikacja;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;                     # bez tego SSE nie dociera
        proxy_cache off;
        proxy_read_timeout 3600s;
        chunked_transfer_encoding off;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name app.przyklad.pl;
    location /.well-known/acme-challenge/ { root /var/www/acme; }
    location / { return 301 https://$host$request_uri; }
}
```

Cztery błędy, które psują WebSocket przez proxy:

1. Brak `proxy_http_version 1.1` — nagłówek `Upgrade` nie przechodzi (HTTP/1.0 go nie zna).
2. `proxy_set_header Connection "upgrade"` na stałe zamiast mapy — łamie zwykłe żądania HTTP
   w tej samej lokalizacji.
3. Domyślny `proxy_read_timeout 60s` — połączenie zrywane co minutę mimo aktywności
   podtrzymania rzadszej niż 60 s.
4. `proxy_buffering on` przy SSE — strumień zatrzymuje się w buforze nginx.

Ograniczenia szybkości i połączeń:

```nginx
limit_req_zone  $binary_remote_addr zone=api:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=polaczenia:10m;

location /api/ {
    limit_req  zone=api burst=20 nodelay;
    limit_conn polaczenia 20;
    limit_req_status 429;
    proxy_pass http://aplikacja;
}
```

`$binary_remote_addr` za innym proxy (Cloudflare) to adres Cloudflare, nie użytkownika.
Wtedy konieczny `real_ip_header CF-Connecting-IP` + `set_real_ip_from` z sieciami dostawcy —
inaczej limitujesz cały ruch jako jednego klienta.

### Caddy — to samo w kilkunastu liniach

```caddyfile
app.przyklad.pl {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8000 {
        header_up X-Real-IP {remote_host}
        flush_interval -1           # wyłącza buforowanie: wymagane dla SSE
    }
}
```

Caddy sam pobiera i odnawia certyfikat, sam przekierowuje HTTP→HTTPS, sam obsługuje
`Upgrade` dla WebSocketa. `flush_interval -1` to odpowiednik `proxy_buffering off`.

### Traefik — dla wielu kontenerów

```yaml
services:
  traefik:
    image: traefik:v3.6
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.web.http.redirections.entrypoint.to=websecure
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.le.acme.email=admin@przyklad.pl
      - --certificatesresolvers.le.acme.storage=/acme/acme.json
      - --certificatesresolvers.le.acme.tlschallenge=true
    ports: ["80:80", "443:443"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - acme:/acme

  aplikacja:
    image: rejestr.przyklad.pl/aplikacja:1.4.2
    labels:
      - traefik.enable=true
      - traefik.http.routers.app.rule=Host(`app.przyklad.pl`)
      - traefik.http.routers.app.entrypoints=websecure
      - traefik.http.routers.app.tls.certresolver=le
      - traefik.http.services.app.loadbalancer.server.port=8000
```

Montowanie `docker.sock` do kontenera Traefika daje mu **pełną kontrolę nad hostem**.
Montuj `:ro` i rozważ pośrednik (`tecnativa/docker-socket-proxy`) ograniczający API
do odczytu kontenerów.

## Zapora i dostęp SSH

```bash
# nftables / ufw — domyślnie wszystko zamknięte
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp                 # albo lepiej: tylko z konkretnych adresów
ufw allow 80,443/tcp
ufw allow 25,465,587,993/tcp     # tylko na serwerze poczty
ufw allow 3478/udp
ufw allow 49160:49200/udp        # przekaźnik TURN
ufw limit 22/tcp                 # ogranicza tempo prób
ufw enable
```

SSH — `/etc/ssh/sshd_config.d/10-hardening.conf`:

```
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
X11Forwarding no
AllowUsers admin wdrozenie
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
```

Kolejność, która ratuje przed zablokowaniem sobie dostępu:
1. Wgraj klucz publiczny.
2. **Zaloguj się kluczem w drugim oknie terminala** i nie zamykaj go.
3. Dopiero wtedy wyłącz `PasswordAuthentication` i `systemctl reload sshd`.
4. Sprawdź logowanie z trzeciego okna.

Zmiana portu SSH z 22 na wysoki eliminuje ~99 % automatycznych prób w logach — nie jest
zabezpieczeniem, ale oczyszcza dziennik na tyle, że widać prawdziwe zdarzenia.

fail2ban dla SSH (`bantime = 1d`, `maxretry = 3`) plus dla usług z
`references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` i
`references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md`.

## Kontenery i `docker compose`

```yaml
# compose.yaml — usługa sieciowa z zapleczem
name: danaco-uslugi

services:
  aplikacja:
    image: rejestr.przyklad.pl/aplikacja:1.4.2      # NIGDY :latest w produkcji
    restart: unless-stopped
    depends_on:
      baza:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://app@baza:5432/app
      REDIS_URL: redis://redis:6379/0
    env_file: [.env]                                 # sekrety poza compose.yaml
    ports: ["127.0.0.1:8000:8000"]                   # NIE 0.0.0.0 — proxy jest na hoście
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/zdrowie"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    logging:
      driver: json-file
      options: { max-size: "20m", max-file: "5" }
    deploy:
      resources:
        limits: { cpus: "2.0", memory: 2G }
    security_opt: ["no-new-privileges:true"]
    read_only: true
    tmpfs: ["/tmp"]

  baza:
    image: postgres:17.6-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_haslo
    secrets: [postgres_haslo]
    volumes:
      - dane-bazy:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: json-file
      options: { max-size: "20m", max-file: "3" }

  redis:
    image: redis:8-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
    volumes: [dane-redis:/data]

volumes:
  dane-bazy:
  dane-redis:

secrets:
  postgres_haslo:
    file: ./sekrety/postgres_haslo.txt
```

Reguły, których pominięcie boli:

- **`logging` z limitem rozmiaru na każdej usłudze.** Domyślnie `json-file` rośnie bez końca
  i zapełnia dysk — najczęstsza przyczyna nocnej awarii serwera z kontenerami.
- **`ports: "127.0.0.1:8000:8000"`.** Zapis `"8000:8000"` publikuje na wszystkich interfejsach
  **i omija `ufw`** (Docker wpina reguły przed łańcuchem `ufw`). Usługa, którą „zablokowałeś
  zaporą”, jest dostępna z internetu.
- **Przypięta wersja obrazu.** `:latest` powoduje, że `docker compose pull` na produkcji
  wprowadza nieprzetestowaną wersję.
- **`healthcheck` + `depends_on: condition: service_healthy`.** Bez tego aplikacja startuje
  przed bazą, wywala się i restartuje w pętli.
- **Nazwane wolumeny, nie montowania z hosta**, dla danych — łatwiejsze kopie i uprawnienia.
- `restart: unless-stopped`, nie `always` — `always` wznawia także po ręcznym zatrzymaniu.

Sieci usług sieciowych (poczta, SIP, TURN) potrzebują `network_mode: host` albo jawnego
mapowania **całego zakresu portów RTP** — NAT Dockera dla tysięcy portów UDP jest wolny i
zawodny. Dla Asteriska i coturn: `network_mode: host` jest zwykle jedynym praktycznym wyborem.

## Kopie zapasowe i odtwarzanie

Reguła 3-2-1: **3** kopie danych, na **2** różnych nośnikach, **1** poza lokalizacją.

```bash
# restic — deduplikacja, szyfrowanie, przyrost
export RESTIC_REPOSITORY="s3:s3.eu-central-1.amazonaws.com/kopie-danaco"
export RESTIC_PASSWORD_FILE=/root/.restic-haslo

# zrzut bazy przed kopią plików
docker compose exec -T baza pg_dump -U app -Fc app > /var/kopie/app-$(date +%F).dump

restic backup /var/kopie /var/lib/docker/volumes /etc/nginx /etc/letsencrypt \
       --exclude-caches --tag noc
restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 12 --prune
restic check --read-data-subset=5%       # weryfikacja losowej próbki co noc
```

Co musi być w kopii, a bywa pominięte:

- **Klucze prywatne DKIM** (bez nich rotacja selektora po odtworzeniu).
- **Klucze i certyfikaty ACME** (`/etc/letsencrypt` — konta, nie tylko certyfikaty).
- **Sekrety TURN i AMI/ARI**.
- **Konfiguracja Asteriska** (`/etc/asterisk`) i nagrania, jeśli podlegają retencji.
- **Pliki `.env` i `secrets/`** — zaszyfrowane osobno (SOPS/age), nie w tym samym repozytorium
  co kod.
- **Zrzut bazy zrobiony narzędziem bazy**, nie kopia katalogu danych na żywo. Kopia
  `/var/lib/postgresql/data` bez zatrzymania bazy jest w połowie przypadków nieodtwarzalna.

**Test odtworzenia raz na kwartał, na czystej maszynie, z mierzeniem czasu.** Zapisz RTO
(ile trwa odtworzenie) i RPO (ile danych tracisz). Te dwie liczby są jedynym sensownym
opisem jakości kopii. Kopia bez testu odtworzenia to nadzieja, nie kopia.

## Monitorowanie i alarmy

Minimalny zestaw dla usług sieciowych — bez Prometheusa, w cronie, jeśli trzeba szybko:

| Co | Jak | Próg |
|---|---|---|
| Usługa odpowiada | `curl -fsS https://app.przyklad.pl/zdrowie` | błąd lub > 3 s |
| Certyfikat | skrypt z sekcji TLS | < 14 dni |
| Miejsce na dysku | `df -h --output=pcent /` | > 80 % |
| Pamięć | `free -m` | < 10 % wolnej + swap w użyciu |
| Kolejka poczty | `postqueue -p \| tail -1` | > 200 pozycji |
| Rejestracja trunku SIP | `asterisk -rx "pjsip show registrations"` | stan inny niż `Registered` |
| Kandydaci TURN | `turnutils_uclient` | brak kandydata `relay` |
| Domena na liście blokującej | `dig` w `zen.spamhaus.org` | dowolne trafienie |
| Wygasające domeny | WHOIS albo kalendarz | < 30 dni |
| Restart kontenera | `docker compose ps` + licznik restartów | > 3 w godzinę |

Zasada alarmowania: **alarm musi wymagać działania.** Alarm, który przychodzi codziennie
i jest ignorowany, jest gorszy niż jego brak — uczy zespół ignorować powiadomienia.

Rozdziel: `krytyczne` (SMS/telefon, budzi w nocy: usługa nie działa, certyfikat wygasa jutro,
dysk 95 %) od `ostrzeżeń` (e-mail rano: dysk 80 %, kolejka rośnie, kontener się restartuje).

Docelowo: Prometheus + node_exporter + blackbox_exporter (sonda HTTP/TCP/TLS z zewnątrz)
+ Alertmanager, Grafana do wykresów, Uptime Kuma jako lekka alternatywa dla małych wdrożeń.

**Sonda z zewnątrz jest ważniejsza niż wszystkie metryki wewnętrzne.** Serwer może raportować
pełne zdrowie, gdy zapora, DNS albo certyfikat blokują dostęp z internetu.

## Dzienniki

```bash
journalctl -u nginx -f                            # na żywo
journalctl -u postfix --since "2026-08-04 08:00" --until "2026-08-04 09:00"
journalctl -p err -b                              # błędy od startu systemu
journalctl --disk-usage
docker compose logs -f --tail=200 aplikacja
```

Rotacja — bez niej dysk się zapełni:

```
# /etc/logrotate.d/aplikacja
/var/log/aplikacja/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 app app
    sharedscripts
    postrotate
        systemctl reload aplikacja > /dev/null 2>&1 || true
    endscript
}
```

`journald` ograniczaj w `/etc/systemd/journald.conf`: `SystemMaxUse=2G`, `MaxRetentionSec=30day`.

Co logować w aplikacji sieciowej:

- identyfikator korelacji żądania (`X-Request-ID` przekazywany przez proxy),
- adres IP klienta **po** `X-Forwarded-For` (i tylko z zaufanych proxy),
- czas obsługi, kod odpowiedzi, rozmiar,
- przy poczcie: identyfikator kolejki + `Message-ID` + adres odbiorcy,
- przy SIP: `UNIQUEID` kanału i `Call-ID`,
- przy WebRTC: identyfikator sesji i typ wybranej pary kandydatów.

Czego **nie** logować: haseł, tokenów, całych ciał żądań z danymi osobowymi, treści
wiadomości, numerów kart. Dziennik z danymi osobowymi podlega RODO tak samo jak baza —
z retencją, dostępem na role i obowiązkiem usunięcia.

Retencja dzienników: 30 dni na serwerze, dłużej tylko dla dzienników bezpieczeństwa
(logowania, zmiany uprawnień) — tam 12 miesięcy jest typowe. Ustal to jawnie w rejestrze
czynności przetwarzania, a nie „zostawmy, może się przyda”.
