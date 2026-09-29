# Własny serwer pocztowy: kiedy, z czego, jak

Wersje zweryfikowane sierpień 2026: Postfix 3.11.5 (6.07.2026), Dovecot CE 2.4.4 (12.05.2026,
gałąź 2.3 tylko krytyczne poprawki bezpieczeństwa), Rspamd 4.1.x, mailcow wydanie 2026-07a,
Mailu gałąź `2024.06` (najnowszy `2024.06.57`, 26.07.2026), Stalwart 0.16.11 (25.06.2026),
docker-mailserver `[niepotwierdzone: ostatnie potwierdzone v15.1.x]`.

## Decyzja: własny serwer czy nie

### Kiedy własny serwer ma sens

| Sytuacja | Dlaczego |
|---|---|
| Wymóg przechowywania poczty na własnej infrastrukturze (umowa, tajemnica zawodowa, zamówienie publiczne) | dostawca chmurowy nie przejdzie audytu |
| Kilkadziesiąt/kilkaset skrzynek i twardy budżet | Workspace/365 przy 100 skrzynkach to ~30-60 tys. PLN/rok; VPS z mailcow ~1,5-3 tys. PLN/rok + czas administratora |
| Poczta **przychodząca** do przetworzenia przez własną aplikację (parsowanie zgłoszeń, faktur, dokumentów) | pełna kontrola nad routingiem i przetwarzaniem |
| Aliasy, catch-all, reguły routingu, których dostawca nie oferuje | np. `sprawa-<id>@kancelaria.pl` z dynamicznym dopasowaniem |
| Bardzo duże skrzynki archiwalne | koszt przestrzeni u dostawcy rośnie liniowo |

### Kiedy własny serwer jest błędem — zawsze

**Nie stawiaj własnego serwera pocztowego do wysyłki marketingowej ani do wysyłki
transakcyjnej z aplikacji.** Powody, po kolei:

1. **Reputacja IP buduje się miesiącami i ginie w godzinę.** Jeden zainfekowany skrypt na
   tym samym VPS-ie, jedno źle skonfigurowane przekazywanie i twój adres jest w Spamhaus.
   Wyjście z listy to formularz, oczekiwanie i uzasadnienie — od kilku dni do kilku tygodni.
   Przez ten czas nie wychodzi ani jedno powiadomienie o zamówieniu.
2. **Adresy VPS-ów są z góry podejrzane.** Pule Hetznera, OVH, DigitalOcean i Contabo są
   masowo używane przez spamerów. Microsoft i Gmail stosują wobec nich ostrzejsze progi.
   Adres z „czystej” puli kosztuje więcej i nie zawsze da się kupić.
3. **Port 25 wyjściowy jest domyślnie zablokowany** u AWS, GCP, Azure, DigitalOcean, Hetznera,
   Oracle Cloud. Odblokowanie na wniosek, czasem odmowa, czasem tylko dla klientów
   z historią płatności.
4. **Nie masz pętli zwrotnych ani telemetrii.** Dostawca transakcyjny zwraca webhookiem
   „odbite / oznaczone jako spam / otwarte”. Własny Postfix zwraca linijkę w `/var/log/mail.log`,
   którą ktoś musi czytać.
5. **Ciągłość działania.** Wysyłka transakcyjna to ścieżka krytyczna (reset hasła, potwierdzenie
   płatności). Jeden serwer bez zapasowego = pojedynczy punkt awarii dla całego produktu.
6. **Koszt czasu.** Realistyczny nakład na utrzymanie: 2-4 h miesięcznie przy spokoju,
   pełen dzień przy każdym incydencie z listą blokującą. Amazon SES przy 100 tys. wiadomości
   miesięcznie kosztuje ~10 USD.

**Reguła:** poczta **przychodząca i skrzynki** — możesz u siebie. Poczta **wychodząca z aplikacji**
— przez dostawcę
(`references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md`). Nawet mając
własny serwer, skonfiguruj go jako `relayhost` do dostawcy dla wysyłki wychodzącej.

### Rachunek kosztów, który należy przedstawić klientowi

| Pozycja | Własny (mailcow, 50 skrzynek) | Google Workspace Business Standard |
|---|---|---|
| Infrastruktura | VPS 4 vCPU / 8 GB / 200 GB SSD: ~150 PLN/mies. | — |
| Licencje | 0 | ~55 PLN/użytkownik/mies. → 2 750 PLN/mies. |
| Kopie zapasowe | ~30 PLN/mies. (przestrzeń) | w cenie |
| Administracja | 3 h/mies. × stawka | ~0,5 h/mies. |
| Ryzyko przestoju | na tobie | SLA dostawcy |
| **Razem/rok** | ~2 200 PLN + ~36 h pracy | ~33 000 PLN + ~6 h pracy |

Przy 5-10 skrzynkach ten rachunek wychodzi odwrotnie — własny serwer nie ma ekonomicznego sensu.

## Wybór stosu

| Rozwiązanie | Postać | Dla kogo | Wady |
|---|---|---|---|
| **mailcow: dockerized** | ~15 kontenerów, `docker compose` | domyślny wybór dla firmy; panel WWW, SOGo (kalendarz/kontakty), ACME wbudowany, DKIM z panelu, 2FA, kwoty | najcięższy (min. 6 GB RAM), aktualizacje wymagają uwagi, brak łatwej konfiguracji „poza panelem” |
| **Mailu** | kontenery, konfiguracja z pliku `mailu.env` + `docker compose` | mniejsze instalacje, ludzie preferujący konfigurację w repozytorium (GitOps) | mniejsza społeczność, panel skromniejszy, brak kalendarza w podstawie |
| **docker-mailserver** | **jeden** kontener, konfiguracja plikami w `docker-data/dms/config/` | serwer bez panelu WWW, dodatek do istniejącej aplikacji, minimalne zużycie (~1,5 GB RAM) | zarządzanie kontami z wiersza poleceń (`setup email add`), brak webmaila w podstawie |
| **Stalwart Mail Server** | jeden proces w Rust; SMTP+IMAP+JMAP+POP3+CalDAV+CardDAV+WebDAV | instalacje nowe, gdzie ceni się prostotę i JMAP; natywne DANE, MTA-STS, ARC, sieve | młody projekt (0.16.x, przed 1.0), mniej materiałów, migracja z Dovecota nietrywialna |
| **Postfix + Dovecot + Rspamd ręcznie** | pakiety systemowe | gdy trzeba dokładnie zrozumieć albo zintegrować z nietypową aplikacją | najwięcej pracy; łatwo pominąć element (np. ARC, kwoty, sieve) |

**Domyślna rekomendacja:** mailcow dla firmy z pocztą użytkowników; docker-mailserver, gdy
serwer ma tylko przyjmować pocztę dla aplikacji; Stalwart, gdy budujesz od zera i chcesz JMAP.

## Wymagania przed instalacją — bez tego nie zaczynaj

1. **Statyczny adres IPv4** z możliwością ustawienia PTR. Zapytaj operatora *przed* zakupem.
2. **Port 25 wyjściowy odblokowany** — sprawdź: `nc -vz gmail-smtp-in.l.google.com 25`.
3. **IP niebędące na listach blokujących** — sprawdź *przed* wdrożeniem:
   `dig +short 7.113.0.203.zen.spamhaus.org` (odwrócone oktety).
4. **FQDN serwera** = nazwa w PTR = nazwa w `myhostname` = nazwa w certyfikacie = nazwa
   w `EHLO`. Cztery miejsca, jedna wartość, np. `mail.przyklad.pl`.
5. Co najmniej **6 GB RAM** dla mailcow, 2 GB dla docker-mailserver, 4 GB dla Stalwart
   z ClamAV. ClamAV sam zjada ~1,5 GB.
6. Osobny wolumen na dane poczty — łatwiejsze powiększanie i kopie zapasowe.

## mailcow — wdrożenie

```bash
# Debian 12/13, jako root
apt update && apt install -y curl git apt-transport-https ca-certificates
# Docker Engine + compose plugin z repozytorium Dockera (nie z Debiana)
curl -fsSL https://get.docker.com | sh

umask 0022
git clone https://github.com/mailcow/mailcow-dockerized /opt/mailcow-dockerized
cd /opt/mailcow-dockerized
./generate_config.sh
# pyta o MAILCOW_HOSTNAME -> mail.przyklad.pl  oraz strefę czasową -> Europe/Warsaw
```

Po wygenerowaniu, w `mailcow.conf`:

```bash
MAILCOW_HOSTNAME=mail.przyklad.pl
MAILCOW_TZ=Europe/Warsaw

# Jeśli przed mailcow stoi własne reverse proxy (patrz eksploatacja.md):
HTTP_PORT=8080
HTTP_BIND=127.0.0.1
HTTPS_PORT=8443
HTTPS_BIND=127.0.0.1
SKIP_LETS_ENCRYPT=y          # certyfikaty dostarcza proxy

# Wyłączenia zmniejszające zużycie pamięci przy małych instalacjach:
SKIP_CLAMD=n                 # zostaw ClamAV, jeśli masz RAM; przy 4 GB ustaw y
SKIP_SOLR=y                  # wyszukiwanie pełnotekstowe w Dovecot; zjada 1-2 GB
SKIP_SOGO=n                  # kalendarz i kontakty; wyłącz, jeśli niepotrzebne

# Ograniczenie kolejek i limitów wysyłki na konto ustawiasz w panelu, nie tu.
```

```bash
docker compose pull
docker compose up -d
docker compose logs -f postfix-mailcow    # obserwuj start
```

Panel: `https://mail.przyklad.pl/`, login `admin`, hasło `moohoo` — **zmień natychmiast**.

Kolejność w panelu:
1. Konfiguracja → domeny → dodaj `przyklad.pl`, ustaw kwotę domeny i limit skrzynek.
2. W wierszu domeny ikona klucza → wygeneruj DKIM 2048 bit → skopiuj rekord do DNS.
3. Konfiguracja → skrzynki → dodaj konta, każde z własną kwotą.
4. Konfiguracja → opcje → włącz `Rspamd` UI (`/rspamd/`), ustaw wskaźniki progowe.
5. Ustaw kopię zapasową (niżej) **przed** przeniesieniem prawdziwej poczty.

Aktualizacja:

```bash
cd /opt/mailcow-dockerized
./update.sh --check      # co się zmieni
./update.sh              # aktualizacja (robi kopię konfiguracji)
```

Uwaga do wydania 2026-07: podniesienie Rspamda z 3.x na 4.1.x to zmiana wersji głównej,
kontener Postfiksa przeszedł na Debiana 13. Poprawka 2026-07a łata CVE-2026-42533 w nginx
i podbija Rspamda do 4.1.4. **Wykonaj pełną kopię przed aktualizacją** — powrót po nieudanym
przejściu na Rspamd 4 wymaga odtworzenia wolumenu.

## Postfix — konfiguracja ręczna, elementy, które model myli

`/etc/postfix/main.cf`:

```
# --- tożsamość ---
myhostname = mail.przyklad.pl
mydomain = przyklad.pl
myorigin = $mydomain
mydestination =                       # PUSTE przy skrzynkach wirtualnych!
inet_interfaces = all
inet_protocols = all

# --- domeny i skrzynki wirtualne (Dovecot jako LDA/LMTP) ---
virtual_mailbox_domains = mysql:/etc/postfix/sql/domains.cf
virtual_mailbox_maps    = mysql:/etc/postfix/sql/mailboxes.cf
virtual_alias_maps      = mysql:/etc/postfix/sql/aliases.cf
virtual_transport       = lmtp:unix:private/dovecot-lmtp

# --- TLS przychodzące (rola serwera) ---
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.przyklad.pl/fullchain.pem
smtpd_tls_key_file  = /etc/letsencrypt/live/mail.przyklad.pl/privkey.pem
smtpd_tls_security_level = may            # port 25: oportunistyczne, NIGDY encrypt
smtpd_tls_mandatory_protocols = >=TLSv1.2
smtpd_tls_protocols = >=TLSv1.2
smtpd_tls_loglevel = 1

# --- TLS wychodzące (rola klienta) ---
smtp_tls_security_level = dane           # wymaga DNSSEC; bez DNSSEC ustaw: may
smtp_tls_mandatory_protocols = >=TLSv1.2
smtp_tls_CApath = /etc/ssl/certs
smtp_tls_loglevel = 1

# --- ograniczenia na przyjmowanie poczty ---
smtpd_helo_required = yes
smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_unknown_recipient_domain,
    reject_non_fqdn_recipient,
    reject_rbl_client zen.spamhaus.org,
    permit
smtpd_helo_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname
smtpd_sender_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unknown_sender_domain

# --- milter: Rspamd (podpis DKIM/ARC + antyspam) ---
milter_protocol = 6
milter_default_action = accept          # przy awarii Rspamda przyjmuj, nie odrzucaj
smtpd_milters = inet:127.0.0.1:11332
non_smtpd_milters = $smtpd_milters

# --- limity ---
message_size_limit = 52428800           # 50 MB; MIME base64 zwiększa o ~33%, więc
mailbox_size_limit = 0                  #   załącznik 35 MB to praktyczne maksimum
smtpd_client_connection_count_limit = 20
smtpd_client_message_rate_limit = 100
anvil_rate_time_unit = 60s

# --- kolejka ---
maximal_queue_lifetime = 3d
bounce_queue_lifetime = 1d
minimal_backoff_time = 300s
maximal_backoff_time = 4000s
```

Pułapki:

- **`mydestination` musi być puste**, gdy używasz `virtual_mailbox_domains`. Domena w obu
  miejscach daje `User unknown in local recipient table` przy poprawnie istniejącej skrzynce.
- **`smtpd_tls_security_level = encrypt` na porcie 25 to sabotaż** — odrzucasz pocztę od
  serwerów bez STARTTLS. `encrypt` należy do portów 465/587 w `master.cf`, nie do `main.cf`.
- **`reject_unauth_destination` musi być w `smtpd_recipient_restrictions`.** Bez tego masz
  otwarty relay i w ciągu doby twój serwer rozsyła spam całego świata.
- **`milter_default_action = accept`** — przy `reject` awaria Rspamda zatrzymuje całą pocztę
  przychodzącą. Wybierasz między „przepuszczę spam przy awarii” a „stracę pocztę przy awarii”.
- Kolejność milterów: podpisujący DKIM musi być ostatni, po wszystkim, co zmienia treść.

`/etc/postfix/master.cf` — submission:

```
submission     inet  n  -  y  -  -  smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_sasl_type=dovecot
  -o smtpd_sasl_path=private/auth
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o smtpd_sender_restrictions=reject_sender_login_mismatch
  -o smtpd_sender_login_maps=mysql:/etc/postfix/sql/sender_login.cf
  -o milter_macro_daemon_name=ORIGINATING

smtps          inet  n  -  y  -  -  smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_sasl_type=dovecot
  -o smtpd_sasl_path=private/auth
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o smtpd_sender_restrictions=reject_sender_login_mismatch
  -o smtpd_sender_login_maps=mysql:/etc/postfix/sql/sender_login.cf
  -o milter_macro_daemon_name=ORIGINATING
```

`reject_sender_login_mismatch` + `smtpd_sender_login_maps` to zabezpieczenie, o którym większość
poradników zapomina: bez niego uwierzytelniony użytkownik `stazysta@przyklad.pl` może wysłać
wiadomość jako `prezes@przyklad.pl` — z prawidłowym SPF, DKIM i DMARC.

### Przekazywanie wysyłki do dostawcy (relayhost)

```
relayhost = [email-smtp.eu-central-1.amazonaws.com]:465
smtp_tls_wrappermode = yes
smtp_tls_security_level = encrypt
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = static:AKIAXXXXXXXX:BLpQ...
smtp_sasl_security_options = noanonymous
smtp_sasl_mechanism_filter = plain, login
```

Nawiasy kwadratowe wokół nazwy hosta wyłączają szukanie rekordu MX. Ich brak to klasyczny błąd
— Postfix pyta o MX dla `email-smtp...amazonaws.com`, nie znajduje i odracza wszystko.

## Dovecot 2.4

Gałąź 2.4 (od 24.01.2025) **zmieniła składnię konfiguracji** względem 2.3 — pliki z poradników
sprzed 2025 nie zadziałają. Kluczowe różnice: nowy format bloków, `ssl_server_*` zamiast
`ssl_*`, zmiany w `auth`. Przy migracji użyj oficjalnego przewodnika 2.3→2.4, nie przepisuj
ręcznie.

`/etc/dovecot/conf.d/10-mail.conf` — Maildir vs mdbox:

```
# Maildir: jeden plik = jedna wiadomość. Prosty, odporny, łatwy w kopii, wolny przy 100k+ maili
mail_location = maildir:/var/vmail/%d/%n/Maildir

# mdbox: wiadomości w plikach zbiorczych. Szybszy, mniej i-węzłów, wymaga doveadm purge
# mail_location = mdbox:/var/vmail/%d/%n/mdbox
```

Przy skrzynkach > 50 tys. wiadomości Maildir zaczyna męczyć system plików (liczba i-węzłów,
czas listowania katalogu). Wtedy mdbox — ale pamiętaj o `doveadm purge` w cronie, bo skasowane
wiadomości nie zwalniają miejsca same.

### Kwoty

```
# 10-mail.conf
mail_plugins = $mail_plugins quota

# 20-imap.conf
protocol imap { mail_plugins = $mail_plugins imap_quota }

# 90-quota.conf
plugin {
  quota = maildir:User quota
  quota_rule  = *:storage=5G
  quota_rule2 = Trash:storage=+500M      # kosz ponad limit
  quota_rule3 = Junk:storage=+200M
  quota_grace = 10%%
  quota_status_success = DUNNO
  quota_status_nouser  = DUNNO
  quota_status_overquota = "552 5.2.2 Mailbox is full"
  quota_warning  = storage=90%% quota-warning 90 %u
  quota_warning2 = storage=80%% quota-warning 80 %u
}

service quota-warning {
  executable = script /usr/local/bin/quota-warning.sh
  unix_listener quota-warning { user = vmail }
}
```

Postfix musi znać kwotę **przed** przyjęciem wiadomości, inaczej przyjmie 40 MB i dopiero LMTP
odbije — generując odbicie z twojego serwera (backscatter). Dołóż w `main.cf`:

```
smtpd_recipient_restrictions = ... check_policy_service unix:private/quota-status ...
```

### Sieve

```
# 90-sieve.conf
plugin {
  sieve = file:/var/vmail/%d/%n/sieve;active=/var/vmail/%d/%n/.dovecot.sieve
  sieve_before = /var/vmail/sieve-before.d      # reguły globalne PRZED regułami użytkownika
  sieve_after  = /var/vmail/sieve-after.d
  sieve_extensions = +vnd.dovecot.duplicate +editheader
}
```

`/var/vmail/sieve-before.d/10-spam.sieve`:

```sieve
require ["fileinto", "mailbox", "imap4flags"];

if header :contains "X-Spam-Flag" "YES" {
  fileinto :create "Junk";
  stop;
}
if header :contains "X-Spam-Level" "*****" {
  fileinto :create "Junk";
  stop;
}
```

Przykład reguły użytkownika — automatyczna odpowiedź urlopowa z zabezpieczeniem przed pętlą:

```sieve
require ["vacation", "variables", "date"];

if allof(
     currentdate :value "ge" "date" "2026-08-10",
     currentdate :value "le" "date" "2026-08-24",
     not header :matches "Auto-Submitted" "*",
     not header :contains "Precedence" ["bulk", "list", "junk"]
   ) {
  vacation
    :days 7
    :subject "Nieobecność do 24 sierpnia"
    :addresses ["jan@przyklad.pl", "j.kowalski@przyklad.pl"]
    "Dzień dobry, wracam 24 sierpnia. W pilnych sprawach: biuro@przyklad.pl.";
}
```

Warunki `Auto-Submitted` i `Precedence` są obowiązkowe. Bez nich dwa autorespondery
odpowiadają sobie nawzajem w nieskończoność i zapychają obie kolejki.

## Rspamd

Rspamd zastępuje SpamAssassina i OpenDKIM naraz: filtruje, podpisuje DKIM, podpisuje ARC,
robi greylisting, ratelimit i uczenie bayesowskie. W mailcow jest domyślnie.

`/etc/rspamd/local.d/dkim_signing.conf`:

```
selector = "selektor2026a";
path = "/var/lib/rspamd/dkim/$domain.$selector.key";
allow_username_mismatch = true;
use_domain = "header";      # podpisuj domeną z From:, nie z koperty
sign_authenticated = true;
sign_local = true;
```

`/etc/rspamd/local.d/arc.conf` — analogicznie (`selector`, `path`), włącz **tylko** jeśli serwer
przekazuje cudzą pocztę dalej.

`/etc/rspamd/local.d/actions.conf` — progi:

```
reject = 15;
add_header = 6;          # dopisz X-Spam i skieruj sievem do Junk
greylist = 4;
```

Domyślne progi Rspamda (`reject=15`) są konserwatywne i to dobrze. Obniżenie `reject` poniżej
12 zaczyna kasować legalną pocztę, o czym dowiesz się od klientów, a nie z logów.

`/etc/rspamd/local.d/worker-controller.inc`:

```
password = "$2$xxxxx";        # rspamadm pw
enable_password = "$2$yyyyy"; # osobne hasło do zmian
bind_socket = "127.0.0.1:11334";
```

Uczenie:

```bash
rspamc learn_spam < /var/vmail/przyklad.pl/jan/Maildir/.Junk/cur/*
rspamc learn_ham  < /var/vmail/przyklad.pl/jan/Maildir/cur/*
rspamc stat                    # sprawdź, ile próbek w bazie bayesowskiej
```

Klasyfikator bayesowski zaczyna działać sensownie od ~200 próbek każdej klasy. Automatyzuj:
przeniesienie wiadomości do `Junk` przez użytkownika powinno wywołać `learn_spam` (mailcow ma
to wbudowane przez `imapsieve`).

## Antywirus

ClamAV przez `clamav-milter` albo przez Rspamd (`local.d/antivirus.conf`):

```
clamav {
  action = "reject";
  symbol = "CLAM_VIRUS";
  type = "clamav";
  servers = "127.0.0.1:3310";
  scan_mime_parts = true;
  max_size = 20000000;
}
```

ClamAV zajmuje ~1,5 GB RAM i sam w sobie łapie niewiele nowoczesnych zagrożeń. Sensowniejsze
uzupełnienie: blokada rozszerzeń wykonywalnych w załącznikach (`.exe`, `.scr`, `.js`, `.vbs`,
`.jar`, `.iso`, `.lnk`, także wewnątrz archiwów) — Rspamd moduł `mime_types`. Blokada
makrowirusów w `.docm`/`.xlsm` również.

## Kopie zapasowe

Kopia poczty musi obejmować **cztery** rzeczy; pominięcie którejkolwiek oznacza brak odtworzenia:

1. Maildir/mdbox (dane wiadomości),
2. bazę danych kont/aliasów/haseł (MySQL/PostgreSQL),
3. **klucze prywatne DKIM** — bez nich po odtworzeniu musisz rotować selektor i przez czas
   propagacji część poczty nie ma podpisu,
4. konfigurację (`mailcow.conf`, `main.cf`, `master.cf`, `conf.d/`).

mailcow ma własny skrypt:

```bash
BACKUP_LOCATION=/backup /opt/mailcow-dockerized/helper-scripts/backup_and_restore.sh backup all --delete-days 14
```

Wpis do crona plus wysyłka poza serwer (restic/borg do S3 albo do innego hosta):

```bash
0 3 * * * BACKUP_LOCATION=/backup /opt/mailcow-dockerized/helper-scripts/backup_and_restore.sh backup all --delete-days 14 >> /var/log/mailcow-backup.log 2>&1
0 5 * * * restic -r s3:s3.eu-central-1.amazonaws.com/kopie-danaco backup /backup --tag mailcow
```

**Test odtworzenia raz na kwartał, na osobnej maszynie.** Kopia, której nigdy nie odtwarzano,
nie jest kopią. Typowy problem wychodzi dopiero przy odtwarzaniu: uprawnienia `vmail`, brak
kluczy DKIM, niezgodna wersja bazy.

Odtworzenie na innym serwerze zmienia UIDVALIDITY tylko wtedy, gdy kopiujesz „na piechotę” —
kopia całego katalogu Maildir z plikami `dovecot-uidlist` zachowuje UID-y (patrz
`references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md`).

## Monitorowanie

| Metryka | Próg alarmu | Źródło |
|---|---|---|
| Długość kolejki `deferred` | > 200 | `postqueue -p \| tail -1` |
| Wiek najstarszej pozycji | > 6 h | `mailq` |
| Zajętość dysku wolumenu poczty | > 80 % | `df` |
| Wolne miejsce dla ClamAV/bazy | > 85 % | `df` |
| Nieudane logowania SASL / min | > 30 | `journalctl -u postfix \| grep 'SASL.*authentication failed'` |
| Obecność IP na `zen.spamhaus.org` | dowolna | cron z `dig` |
| Ważność certyfikatu | < 14 dni | `openssl s_client -connect mail.przyklad.pl:993` |
| Wskaźnik odbić `5.x.x` w dobie | > 2 % wysyłki | parsowanie logu |
| Wskaźnik spamu w Postmaster Tools | > 0,1 % | panel Google |

Prosty test end-to-end w cronie (ważniejszy niż wszystkie metryki naraz):

```bash
#!/bin/bash
# wyślij wiadomość testową przez własny serwer na zewnętrzną skrzynkę kontrolną
# i sprawdź IMAP-em, czy dotarła w ciągu 5 minut i czy nie w Junk
ID="probe-$(date +%s)"
swaks --to kontrola@zewnetrzny-dostawca.pl --from monitoring@przyklad.pl \
      --server localhost --header "Subject: $ID" --body "ping" || exit 1
sleep 120
python3 /usr/local/bin/sprawdz_skrzynke.py "$ID" || exit 2
```

Logi: `journalctl -u postfix -f`, w kontenerach `docker compose logs -f postfix-mailcow`.
Analiza zbiorcza: `pflogsumm` na dobowym logu daje raport doręczeń, odbić i najczęstszych
błędów — wyślij go sobie codziennie o 6:00.

## Reputacja IP i listy blokujące

| Lista | Waga | Wypis |
|---|---|---|
| Spamhaus ZEN (SBL/XBL/PBL) | **decydująca** — używa jej większość świata | formularz na spamhaus.org, zwykle automatyczny przy PBL, ręczny przy SBL |
| Spamhaus DBL (domeny) | wysoka | jw. |
| SpamCop | średnia, wygasa sama po 24 h bez zgłoszeń | automatyczny |
| Barracuda | średnia, ważna przy odbiorcach korporacyjnych | formularz |
| UCEPROTECT L2/L3 | **niska, ignoruj** — blokuje całe pule /24 i /16 i pobiera opłaty za wypis | nie płać |
| SORBS | malejąca | formularz |

Procedura po wpisaniu na listę:
1. **Znajdź i usuń przyczynę.** Wypis bez usunięcia przyczyny kończy się ponownym wpisem
   i trudniejszym kolejnym wypisem. Typowe przyczyny: otwarty relay, zainfekowany skrypt PHP
   na tym samym hoście, przejęte konto pocztowe (sprawdź `grep 'sasl_username' /var/log/mail.log
   | awk '{print $NF}' | sort | uniq -c | sort -rn`), formularz kontaktowy bez limitu.
2. Zatrzymaj wysyłkę.
3. Złóż wniosek o wypis z opisem przyczyny i podjętych działań.
4. Po wypisie wznów wysyłkę na obniżonym wolumenie (patrz rozgrzewanie w
   `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md`).

Postmaster Tools Google (v2) i Microsoft SNDS to jedyne wglądy w reputację, jakie masz.
Zarejestruj się w obu **zanim** będzie potrzebne.

## RODO a przechowywanie poczty

Serwer pocztowy to zbiór danych osobowych i jeden z najbardziej wrażliwych w firmie.

| Obowiązek | Realizacja techniczna |
|---|---|
| Ograniczenie przechowywania (art. 5 ust. 1 lit. e) | polityka retencji: automatyczne kasowanie z `Trash` po 30 dniach, z `Junk` po 30 dniach, archiwum wg polityki firmy. `doveadm expunge -A mailbox Trash savedbefore 30d` w cronie |
| Bezpieczeństwo przetwarzania (art. 32) | TLS wymuszony na 465/587/993, szyfrowanie wolumenu (LUKS), kopie zapasowe szyfrowane (restic/borg mają to wbudowane), 2FA do panelu |
| Rejestr czynności przetwarzania | wpisz „obsługa poczty elektronicznej” z kategoriami danych, odbiorcami, okresem |
| Powierzenie przetwarzania (art. 28) | umowa powierzenia z **każdym** dostawcą: hostingiem VPS, dostawcą poczty transakcyjnej, usługą antyspamową w chmurze, dostawcą kopii zapasowych |
| Transfer poza EOG | Amazon SES w regionie `eu-central-1`/`eu-west-1`, ale spółka amerykańska — potrzebne SCC i ocena skutków. Dostawcy z UE (Brevo/FR, Mailjet/FR) upraszczają dokumentację |
| Prawo do usunięcia | procedura: kasowanie skrzynki + usunięcie z kopii zapasowych po upływie cyklu retencji kopii (udokumentuj ten cykl — nie musisz grzebać w taśmach, musisz mieć politykę) |
| Zgłoszenie naruszenia (art. 33) | 72 h. Przejęcie konta pocztowego pracownika **jest** naruszeniem, jeśli w skrzynce były dane osobowe. Miej gotowy szablon zgłoszenia do UODO |
| Monitoring poczty pracownika | dopuszczalny na warunkach z Kodeksu pracy art. 22[3]: cel, zakres i sposób w regulaminie/układzie, poinformowanie z 2-tygodniowym wyprzedzeniem, zakaz naruszania tajemnicy korespondencji |

Skanowanie antyspamowe i antywirusowe własnej poczty mieści się w prawnie uzasadnionym
interesie. Przekazanie treści do zewnętrznej usługi analitycznej (np. chmurowej piaskownicy)
to powierzenie przetwarzania — potrzebna umowa i wpis do rejestru.
