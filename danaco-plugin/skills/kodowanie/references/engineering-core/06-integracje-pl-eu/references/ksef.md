# KSeF 2.0 — Krajowy System e-Faktur

> Stan na: 2026-08-04. Źródła: https://ksef.podatki.gov.pl/etapy-wdrozenia-ksef/,
> https://ksef.podatki.gov.pl/informacje-ogolne-ksef-20/struktura-logiczna-fa-3/,
> https://github.com/CIRFMF/ksef-docs, https://github.com/CIRFMF/ksef-api/blob/main/srodowiska.md,
> https://ksef.podatki.gov.pl/media/p4mpdzx1/opis-elementow-numeru_ksef.pdf,
> https://www.insert.com.pl/aktualnosci/prawne/ksef_przepisy_przejsciowe_do_konca_2026_r.html,
> https://ksiegowosc.infor.pl/ksef/7603120 (kary, art. 106ni ustawy o VAT),
> https://www.infakt.pl/blog/wdrozenie-ksef-harmonogram-2026-r/.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Harmonogram obowiązku (stan po przesunięciach)

Termin był przesuwany trzykrotnie (pierwotnie 2023, potem 1.07.2024, potem 1.02.2026).
**Obowiązujący harmonogram:**

| Data | Kto | Zakres |
| --- | --- | --- |
| **1.02.2026** | Podatnicy, u których wartość sprzedaży wraz z podatkiem przekroczyła w **2024 r. 200 mln zł** | Wystawianie **i** odbieranie. Od tego dnia **wszyscy** podatnicy muszą odbierać faktury przez KSeF |
| **1.04.2026** | Pozostali podatnicy | Wystawianie i odbieranie |
| **1.01.2027** | Podatnicy „wykluczeni cyfrowo”: faktury ≤ 450 zł brutto pojedynczo i ≤ 10 000 zł miesięcznie łącznie | Wystawianie |

Kluczowa asymetria, którą łatwo przeoczyć: **obowiązek odbierania faktur przez KSeF objął
wszystkich już 1.02.2026**, niezależnie od tego, kiedy dany podatnik zaczyna wystawiać. System
klienta musi umieć **pobierać** faktury z KSeF od lutego 2026, nawet jeśli jego obowiązek
wystawiania zaczął się w kwietniu.

Okno serwisowe 26–31.01.2026 wyłączyło KSeF 1.0; od 1.02.2026 KSeF 2.0 jest jedynym systemem.
KSeF 1.0 i jego API nie są już wspierane — kod pisany pod `/online/Session/*` z KSeF 1.0 jest
martwy.

## Przepisy przejściowe do 31.12.2026

| Rozwiązanie | Do kiedy |
| --- | --- |
| Faktury z kas rejestrujących (w tym paragony z NIP jako faktury uproszczone) poza KSeF | 31.12.2026 |
| Brak kar za naruszenia obowiązków KSeF | 31.12.2026 |
| Faktury konsumenckie poza KSeF przy limicie 450 zł / 10 000 zł miesięcznie | patrz harmonogram — do 31.12.2026 |
| Obowiązek podawania numeru KSeF w tytule przelewu za e-fakturę | odroczony do **1.01.2027** |

## Kary

Podstawa: **art. 106ni ust. 1–3 ustawy z 11.03.2004 o podatku od towarów i usług**. Stosowanie
od **1.01.2027**.

| Naruszenie | Sankcja |
| --- | --- |
| Wystawienie faktury poza KSeF wbrew obowiązkowi | do **100%** kwoty podatku wykazanego na fakturze |
| Faktura bez wykazanego podatku | do **18,7%** kwoty należności ogółem |
| Nieprzesłanie faktury wystawionej offline w terminie | j.w. |

Naczelnik urzędu skarbowego może miarkować karę na podstawie art. 189d k.p.a. (waga naruszenia,
uprzednie naruszenia, dobrowolne działania naprawcze, korzyść finansowa).

## Środowiska i adresy API

Źródło: https://github.com/CIRFMF/ksef-api/blob/main/srodowiska.md

| Środowisko | Adres bazowy API | Dokumentacja OpenAPI |
| --- | --- | --- |
| TEST (release candidate) | `https://api-test.ksef.mf.gov.pl` | `https://api-test.ksef.mf.gov.pl/docs/v2` |
| DEMO (przedprodukcyjne) | `https://api-demo.ksef.mf.gov.pl` | `https://api-demo.ksef.mf.gov.pl/docs/v2` |
| PROD | `https://api.ksef.mf.gov.pl` | `https://api.ksef.mf.gov.pl/docs/v2` |

Aplikacja Podatnika (webowa, dla użytkownika końcowego): `ap.ksef.mf.gov.pl`.
Infolinia KSeF: 22 330 03 30.

Ścieżki API są wersjonowane pod `/v2`. Gdy API zwraca URL do pobrania lub wysłania zasobu, host
w tym URL odpowiada środowisku, do którego kierowano wywołanie — **nie podmieniaj hosta ręcznie**.

Repozytoria referencyjne Ministerstwa Finansów (CIRF MF):
- `https://github.com/CIRFMF/ksef-docs` — dokumentacja funkcjonalna, changelog
- `https://github.com/CIRFMF/ksef-api` — specyfikacja OpenAPI, opis środowisk
- Struktura FA(3) w CRWDE: `http://crd.gov.pl/wzor/2025/06/25/13775/`

## Struktura logiczna FA(3)

- Obowiązuje **od 1.02.2026**, zastąpiła FA(2).
- Opublikowana w Centralnym Repozytorium Wzorów Dokumentów Elektronicznych **25.06.2025**
  pod `http://crd.gov.pl/wzor/2025/06/25/13775/`.
- FA(3) wprowadza m.in. obsługę **załączników do faktury** (wcześniej niemożliwych) oraz
  rozszerzenia pól tekstowych. `[niepotwierdzone: pełna lista różnic FA(2) → FA(3); strona MF nie
  wylicza zmian — pobierz XSD z CRWDE i zrób diff, albo sprawdź changelog w CIRFMF/ksef-docs]`

Walidacja: faktura musi przejść walidację względem XSD **przed** wysłaniem. Odrzucenie po stronie
KSeF nie jest tanie — sesja zwraca błąd, a fakturę trzeba wystawić od nowa. Waliduj lokalnie
(`lxml.etree.XMLSchema` w Pythonie) przy każdym budowaniu dokumentu, nie tylko w testach.

## Numer KSeF

Format (źródło: opis-elementow-numeru_ksef.pdf, MF):

```
9999999999-RRRRMMDD-FFFFFFFFFFFF-FF
```

| Segment | Długość | Znaczenie |
| --- | --- | --- |
| `9999999999` | 10 | NIP sprzedawcy |
| `RRRRMMDD` | 8 | data wystawienia faktury |
| `FFFFFFFFFFFF` | 12 | część techniczna, generowana przez system |
| `FF` | 2 | suma kontrolna |

Łącznie **35 znaków** z myślnikami. Kolumna w bazie: `CHAR(35)` albo `VARCHAR(35)`, nigdy krótsza.
Numer KSeF nadaje **system**, nie wystawca — do momentu nadania faktura nie istnieje w obrocie
prawnym w trybie online. Data nadania numeru KSeF jest datą otrzymania faktury przez nabywcę.

## Uwierzytelnianie

Źródło: `CIRFMF/ksef-docs`, `uwierzytelnianie.md`.

Trzy metody:

1. **Podpis XAdES** — podpisanie dokumentu XML `AuthTokenRequest`. Akceptowane: kwalifikowany
   certyfikat osoby fizycznej (z PESEL/NIP), kwalifikowana pieczęć organizacji, **profil zaufany**,
   certyfikat KSeF, certyfikaty dostawców Peppol. Na środowisku testowym dopuszczone certyfikaty
   samodzielnie wygenerowane.
2. **Token KSeF** — szyfrujesz ciąg `{tokenKSeF}|{timestampMs}` kluczem publicznym KSeF algorytmem
   **RSA-OAEP z SHA-256**, wynik kodujesz Base64.
3. **Certyfikat KSeF** — wydawany przez sam KSeF, nie jest certyfikatem kwalifikowanym, ale jest
   honorowany przy uwierzytelnianiu.

Przebieg (challenge–response, asynchroniczny):

| Krok | Wywołanie |
| --- | --- |
| 1. Pobranie wyzwania (ważne 10 minut) | `POST /auth/challenge` |
| 2a. Uwierzytelnienie podpisem | `POST /auth/xades-signature` |
| 2b. Uwierzytelnienie tokenem | `POST /auth/ksef-token` |
| 3. Sprawdzenie statusu | `GET /auth/{referenceNumber}` |
| 4. Odbiór tokenów | `POST /auth/token/redeem` |
| 5. Odświeżenie dostępu | `POST /auth/token/refresh` |

Zwracana jest para `accessToken` / `refreshToken`. `accessToken` ważny do czasu z pola `exp`.
Kroki 2 i 3 są asynchroniczne — odpowiedź z kroku 2 zawiera `referenceNumber`, status trzeba
odpytać. Nie zakładaj natychmiastowego sukcesu.

Uwaga na semantykę: **certyfikat nie niesie uprawnień**. Certyfikat identyfikuje podmiot (PESEL,
NIP albo fingerprint), a uprawnienia w KSeF są zarządzane osobno (`/permissions/*`). Nadanie
komuś certyfikatu nie daje mu dostępu do faktur.

## Certyfikaty KSeF

Dwa typy, każdy certyfikat ma dokładnie jeden:

| Typ | keyUsage | Do czego |
| --- | --- | --- |
| `Authentication` | Digital Signature (80) | Logowanie do KSeF |
| `Offline` | (40) | Wyłącznie fakturowanie offline — potwierdzenie autentyczności i integralności w kodzie QR II. **Nie** pozwala się uwierzytelnić |

Procedura pozyskania:

| Krok | Wywołanie |
| --- | --- |
| 1. Sprawdzenie limitów | `GET /certificates/limits` |
| 2. Pobranie danych do wniosku (wymaga uwierzytelnienia XAdES) | `GET /certificates/enrollments/data` |
| 3. Przygotowanie CSR (PKCS#10, RSA 2048 lub EC NIST P-256) | — lokalnie |
| 4. Złożenie wniosku | `POST /certificates/enrollments` |
| 5. Status wniosku | `GET /certificates/enrollments/{referenceNumber}` |
| 6. Pobranie certyfikatu | `POST /certificates/retrieve` |

Wniosek można złożyć **wyłącznie we własnym imieniu** — dane muszą się zgadzać z certyfikatem użytym
do uwierzytelnienia. Można podać `validFrom`; bez tego certyfikat obowiązuje od wystawienia.
`[niepotwierdzone: standardowy okres ważności certyfikatu KSeF i maksymalna liczba aktywnych
certyfikatów na podmiot — dokumentacja odsyła do `/certificates/limits`, wartości sprawdź
wywołaniem]`

## Tryby offline

| Tryb | Kiedy | Termin przesłania do KSeF |
| --- | --- | --- |
| `offline24` | Zawsze dostępny, bez warunków, decyzja podatnika | **następny dzień roboczy** |
| Tryb niedostępności (`offline`) | Automatycznie, gdy MF ogłosi niedostępność systemu | następny dzień roboczy po przywróceniu dostępu |
| Tryb awaryjny | Awaria systemu ogłoszona przez MF | **do 7 dni roboczych** od zakończenia awarii |

Faktura wystawiona offline wymaga **dwóch kodów QR**:
- **KOD I** — umożliwia weryfikację faktury w KSeF,
- **KOD II** — potwierdza tożsamość wystawcy (podpisany certyfikatem KSeF typu `Offline`).

Konsekwencja projektowa: `offline24` nie jest trybem awaryjnym, tylko **normalną ścieżką**.
System musi umieć wystawić fakturę bez połączenia z KSeF, wygenerować oba kody i dosłać dokument
najpóźniej następnego dnia roboczego. Kolejka wysyłkowa z retry i kontrolą terminu jest
obowiązkowym elementem, nie opcją.

## Sesje i wysyłka

Dokumentacja `CIRFMF/ksef-docs` opisuje dwa tryby:
- **sesja interaktywna** — wysyłka pojedynczych faktur w czasie rzeczywistym,
- **sesja wsadowa (batch)** — paczka faktur, przetwarzana asynchronicznie.

Pobieranie faktur ma wariant **przyrostowy** (incremental) — używaj go do synchronizacji, nie
pobieraj pełnej listy przy każdym cyklu.

`[niepotwierdzone: dokładne limity API (żądania/minutę per endpoint, maksymalny rozmiar paczki
wsadowej, maksymalna liczba faktur w sesji) — plik z limitami jest w CIRFMF/ksef-docs, ale nie
udało się go odczytać pod nazwą `limity-api.md`; sprawdź spis plików w repozytorium]`

## Szyfrowanie

KSeF 2.0 używa klucza publicznego systemu do szyfrowania (m.in. tokenu przy uwierzytelnianiu
RSA-OAEP/SHA-256, oraz treści w sesjach). Klucze publiczne są publikowane per środowisko —
**klucz z DEMO nie zadziała na PROD**. Pobieraj klucz z tego samego środowiska, do którego wysyłasz.

## Typowe błędy integracyjne

| Błąd | Konsekwencja |
| --- | --- |
| Kod pod KSeF 1.0 (`/online/Session/*`) | API nie istnieje od 1.02.2026 — całkowity brak łączności |
| Założenie, że obowiązek odbierania zaczyna się razem z obowiązkiem wystawiania | Nieodebrane faktury zakupowe od 1.02.2026 |
| Brak lokalnej walidacji XSD przed wysyłką | Odrzucenia w sesji, konieczność ponownego wystawienia |
| Traktowanie `offline24` jako trybu awaryjnego | Brak kolejki dosyłkowej → przekroczenie terminu D+1 → kara od 1.01.2027 |
| Numer KSeF w kolumnie krótszej niż 35 znaków | Ucięcie sumy kontrolnej, nieweryfikowalny numer |
| Mieszanie kluczy publicznych między środowiskami | Błąd deszyfracji, brak uwierzytelnienia |
| Certyfikat typu `Offline` użyty do logowania | Odrzucenie uwierzytelnienia — ten typ nie ma tego keyUsage |
| Synchroniczne oczekiwanie na wynik `POST /auth/xades-signature` | Proces jest asynchroniczny; trzeba odpytywać `GET /auth/{referenceNumber}` |

## Co potwierdzić przed wdrożeniem

1. Changelog w `CIRFMF/ksef-docs` — MF publikuje zmiany API bez wersjonowania semantycznego.
2. Aktualny XSD FA(3) z CRWDE (mógł być poprawiany po publikacji 25.06.2025).
3. Limity API dla planowanego wolumenu — przy wysyłce masowej to jest ograniczenie projektowe.
4. Czy klient mieści się w przepisie przejściowym dla kas rejestrujących (do 31.12.2026).
