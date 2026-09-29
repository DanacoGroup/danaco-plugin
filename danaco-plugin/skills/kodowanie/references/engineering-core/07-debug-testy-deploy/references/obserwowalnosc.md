# Obserwowalność — logi, metryki, ślady, alarmy

Wersje odniesienia (sierpień 2026): OpenTelemetry JS `@opentelemetry/api` **1.9.1**,
`@opentelemetry/sdk-node` **0.221.0**; OpenTelemetry Python `opentelemetry-sdk` **1.44.0**;
semantic conventions **1.43.0** (konwencje GenAI wydzielone do osobnego repozytorium
`semantic-conventions-genai`); Sentry `@sentry/node` **10.69.0**, `sentry-sdk` (Python)
**2.66.1**.

Trzy pytania, na które musi odpowiadać system obserwowalny:

1. **Czy działa?** — metryki i alarmy.
2. **Co się właśnie stało w tym jednym żądaniu?** — logi z korelacją.
3. **Gdzie poszedł czas / gdzie się urwało?** — ślady rozproszone.

Brak któregokolwiek oznacza debugowanie produkcji przez zgadywanie. Dokładanie obserwowalności
**po** awarii jest normalne i właściwe — patrz
`references/engineering-core/07-debug-testy-deploy/references/awaria.md`, punkt o pierwszym
wystąpieniu błędu nieodtwarzalnego.

---

## Logi strukturalne

Log to zdarzenie z polami, nie zdanie. Zdanie da się przeczytać oczami; pola da się
filtrować, agregować i korelować.

```ts
// ŹLE — nie da się z tego zbudować zapytania
console.log(`Nie udało się wystawić faktury dla ${email}: ${err.message}`);

// DOBRZE — pino 9 / dowolny logger strukturalny
log.error({
  zdarzenie: 'faktura.wystawienie.niepowodzenie',
  requestId,
  uzytkownikId,             // identyfikator, NIE e-mail
  kontrahentId,
  kwotaGroszy,
  powod: 'walidacja_nip',
  err,                      // logger serializuje stos
}, 'nie udało się wystawić faktury');
```

Zapytanie „ile razy w tym tygodniu wystawienie padło z powodu `walidacja_nip`” jest
wykonalne w drugim przypadku i niewykonalne w pierwszym.

### Co logować

| Zdarzenie | Poziom | Pola obowiązkowe |
| --- | --- | --- |
| Wejście/wyjście żądania | `info` | metoda, ścieżka (wzorzec, nie z ID!), status, czas ms, `requestId` |
| Operacja biznesowa zakończona | `info` | typ operacji, identyfikatory encji, wynik |
| Odrzucenie z powodu reguły | `warn` | reguła, identyfikatory, wartość naruszająca |
| Wywołanie systemu zewnętrznego | `info`/`debug` | usługa, operacja, czas, status, liczba ponowień |
| Wyjątek nieobsłużony | `error` | pełny stos, kontekst, `requestId` |
| Uruchomienie/zamknięcie procesu | `info` | wersja aplikacji, commit, konfiguracja bez sekretów |
| Zmiana stanu wpływająca na dostępność | `warn` | wyczerpanie puli połączeń, przerwanie obwodu, degradacja |

Ścieżka w logu ma być **wzorcem**: `/faktury/:id`, nie `/faktury/8341`. Inaczej każde
żądanie tworzy osobną serię i agregacja jest bezużyteczna (a w systemie metryk —
kardynalność wybucha i rachunek rośnie).

### Czego NIGDY nie logować

Bezwzględny zakaz. Naruszenie oznacza wyciek danych osobowych do systemu logów, do którego
dostęp ma szerszy krąg osób niż do bazy, i którego retencja wynosi miesiące.

| Kategoria | Przykłady | Co zamiast tego |
| --- | --- | --- |
| Poświadczenia | hasła (także błędne!), tokeny, klucze API, ciasteczka sesyjne, `Authorization` | fakt uwierzytelnienia + identyfikator użytkownika |
| Dane osobowe | PESEL, dowód osobisty, adres, pełne imię i nazwisko, e-mail, telefon, IP (RODO: dana osobowa) | identyfikator wewnętrzny; e-mail zredagowany `j***@example.com` gdy naprawdę konieczny |
| Dane finansowe | pełny numer karty, CVV, numer rachunku, pełne dane transakcji | ostatnie 4 cyfry, identyfikator płatności u dostawcy |
| Dane wrażliwe | zdrowie, wyznanie, orientacja, dane biometryczne, treść korespondencji | wyłącznie identyfikator zasobu |
| Zawartość dokumentów | treść pliku, treść wiadomości, załączniki | identyfikator, rozmiar, typ MIME, suma kontrolna |
| Całe obiekty żądania/odpowiedzi | `log.info({ req })`, `log.debug(body)` | wybrane pola z jawnej listy dozwolonej |

Ostatni wiersz jest najczęstszym mechanizmem wycieku: `log.info({ req })` wypisuje
nagłówki razem z `Authorization` i `Cookie`. Loguj po **liście dozwolonej**, nigdy po
liście zakazanej — nowe pole w obiekcie automatycznie trafiłoby do logu.

Redakcja na poziomie loggera jako druga linia obrony, nie pierwsza:

```ts
import pino from 'pino';
export const log = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: {
    paths: [
      'req.headers.authorization', 'req.headers.cookie', '*.password', '*.haslo',
      '*.token', '*.apiKey', '*.pesel', '*.nrRachunku', 'res.headers["set-cookie"]',
    ],
    censor: '[usunięte]',
  },
});
```

Test w CI, że sekret nie wycieka — tani i skuteczny:

```ts
it('log nie zawiera tokenu', () => {
  const linie = przechwycLogi(() => obsluzZadanie({ headers: { authorization: 'Bearer sekret123' } }));
  expect(linie.join('\n')).not.toContain('sekret123');
});
```

### Poziomy

| Poziom | Znaczenie operacyjne | Czy budzi kogoś |
| --- | --- | --- |
| `error` | Operacja użytkownika nie powiodła się i wymaga działania | Nie sam z siebie — dopiero wzrost tempa |
| `warn` | Coś jest nie tak, ale system poradził sobie (ponowienie, degradacja) | Nie |
| `info` | Zdarzenia biznesowe i cykl życia; domyślny poziom na produkcji | Nie |
| `debug` | Szczegóły diagnostyczne; wyłączony na produkcji, włączany punktowo | Nie |
| `trace` | Bardzo szczegółowe; tylko lokalnie | Nie |

Dwa najczęstsze błędy: (a) błąd walidacji użytkownika logowany jako `error` — po tygodniu
`error` znaczy „nic”, bo jest ich 50 000 dziennie; (b) awaria bazy logowana jako `warn` —
alarm nie zadziała. Reguła: `error` znaczy „ktoś musi coś zrobić z kodem albo
z infrastrukturą”. Zły NIP wpisany przez użytkownika to `info` albo `warn`.

Poziom przez zmienną środowiskową, przełączalny bez wdrożenia. Możliwość podniesienia
poziomu dla jednego użytkownika/najemcy na godzinę jest warta swojej ceny w trakcie awarii.

---

## Korelacja żądań

Bez identyfikatora korelacji log rozproszony jest zbiorem zdań bez związku.

```ts
import { AsyncLocalStorage } from 'node:async_hooks';
import { randomUUID } from 'node:crypto';

const kontekst = new AsyncLocalStorage<{ requestId: string }>();

export function middlewareKorelacji(req, res, next) {
  // uszanuj identyfikator od klienta/bramy, jeśli przyszedł
  const requestId = req.headers['x-request-id'] ?? randomUUID();
  res.setHeader('x-request-id', requestId);
  kontekst.run({ requestId }, next);
}

export const log = pino({ mixin: () => ({ requestId: kontekst.getStore()?.requestId }) });
```

Trzy warunki, żeby korelacja była użyteczna:

1. **Identyfikator wędruje dalej** — do każdego wywołania HTTP w dół (`x-request-id`
   albo standardowy nagłówek `traceparent`) i do komunikatów w kolejce (w nagłówkach
   komunikatu, nie w treści).
2. **Identyfikator wraca do użytkownika** — w nagłówku odpowiedzi i na stronie błędu.
   „Podaj kod błędu z ekranu” skraca diagnozę zgłoszenia z godzin do minut.
3. **Identyfikator jest w każdym logu**, także w logach zadań w tle wykonujących pracę
   zleconą przez to żądanie.

Gdy używasz OpenTelemetry, nie wymyślaj własnego: `traceId` i `spanId` z kontekstu śladu
są tym identyfikatorem i przechodzą przez `traceparent` (W3C Trace Context) automatycznie.

---

## Metryki

### Cztery złote sygnały (usługa obsługująca żądania)

| Sygnał | Co mierzy | Metryka |
| --- | --- | --- |
| Opóźnienie | jak długo trwa żądanie | histogram czasu, osobno dla udanych i nieudanych |
| Ruch | ile żądań | licznik żądań na sekundę |
| Błędy | jaka część zawodzi | odsetek odpowiedzi 5xx i błędów biznesowych |
| Nasycenie | jak blisko limitu | zajętość puli połączeń, kolejki, pamięci, CPU |

Opóźnienie mierz **osobno dla żądań udanych i nieudanych**. Szybkie 500-tki potrafią
poprawić medianę i ukryć awarię: p50 spada, bo połowa żądań pada w 5 ms.

### RED (usługi) i USE (zasoby)

- **RED** — Rate, Errors, Duration. Dla każdego endpointu i każdej usługi. To jest to,
  co widzi użytkownik.
- **USE** — Utilization, Saturation, Errors. Dla każdego zasobu (CPU, dysk, pula
  połączeń, wątki). To jest to, co ogranicza system.

Alarmuj na RED, diagnozuj przez USE. Alarm na USE (np. „CPU > 80%”) budzi ludzi wtedy,
gdy nic złego się nie dzieje, i milczy wtedy, gdy usługa jest niedostępna z powodu
niezwiązanego z zasobami.

### Percentyle, nie średnie

Średni czas odpowiedzi jest bezużyteczny: przy 99 żądaniach po 10 ms i jednym po 30 s
średnia wynosi 310 ms i wygląda dobrze. Publikuj p50, p95, p99. Cel definiuj na p95 albo
p99, nigdy na średniej.

Uwaga na agregację: **percentyle nie sumują się.** Nie da się policzyć p99 dla całości
ze średniej p99 z pięciu instancji. Używaj histogramów (OTel `Histogram`, Prometheus
`histogram_quantile`), które agregują poprawnie.

### Kardynalność — najczęstsza przyczyna rachunku za monitoring

Etykieta metryki o wysokiej liczbie unikalnych wartości mnoży liczbę serii czasowych.
Kilka takich etykiet i masz miliony serii oraz rachunek większy niż za serwery.

| Nie jako etykieta | Dlaczego | Gdzie umieścić |
| --- | --- | --- |
| ID użytkownika, ID zamówienia, e-mail | miliony wartości | log albo atrybut śladu |
| Pełny URL z parametrami | nieograniczone | wzorzec ścieżki jako etykieta |
| Znacznik czasu | z definicji unikalny | to jest oś, nie etykieta |
| Komunikat błędu | swobodny tekst | kod błędu jako etykieta, treść do logu |

Bezpieczne etykiety: wzorzec ścieżki, metoda, klasa statusu (`2xx`/`4xx`/`5xx`), nazwa
usługi, wersja, środowisko, region. Łącznie ich iloczyn powinien się liczyć w setkach,
nie w setkach tysięcy.

---

## Ślady rozproszone i OpenTelemetry

Ślad odpowiada na pytanie „gdzie poszedł czas i w którym miejscu łańcucha się urwało”.
Pojedynczy ślad = jedno żądanie przez wszystkie usługi; przęsło (`span`) = jedna operacja.

### Minimalna konfiguracja, Node (SDK 0.221)

```ts
// telemetria.ts — musi być importowane PRZED kodem aplikacji
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: resourceFromAttributes({
    [ATTR_SERVICE_NAME]: 'faktury-api',
    [ATTR_SERVICE_VERSION]: process.env.COMMIT_SHA ?? 'dev',
    'deployment.environment.name': process.env.NODE_ENV ?? 'development',
  }),
  traceExporter: new OTLPTraceExporter({ url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT }),
  instrumentations: [getNodeAutoInstrumentations({
    '@opentelemetry/instrumentation-fs': { enabled: false },   // ogromny szum
  })],
});
sdk.start();
process.on('SIGTERM', () => { void sdk.shutdown(); });
```

```bash
node --import ./telemetria.js ./dist/serwer.js
# albo, gdy budujesz do CJS:
node --require ./telemetria.js ./dist/serwer.js
```

Import przed aplikacją jest konieczny: instrumentacja podmienia moduły przy ładowaniu.
Zaimportowana po `express` nie widzi go i ślady są puste — to najczęstszy błąd wdrożenia
OTel.

### Python (SDK 1.44)

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install          # dobiera instrumentacje do zainstalowanych paczek
OTEL_SERVICE_NAME=faktury-api \
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318 \
opentelemetry-instrument uvicorn app:app --host 0.0.0.0 --port 8000
```

### Przęsła własne — tylko tam, gdzie automat nie sięga

```ts
import { trace, SpanStatusCode } from '@opentelemetry/api';
const tracer = trace.getTracer('faktury');

export async function wystawFakture(dane: DaneFaktury) {
  return tracer.startActiveSpan('faktura.wystaw', async (span) => {
    span.setAttribute('faktura.stawka_vat', dane.stawkaVat);
    span.setAttribute('faktura.pozycji', dane.pozycje.length);
    try {
      const wynik = await zapisz(dane);
      span.setAttribute('faktura.numer', wynik.numer);
      return wynik;
    } catch (err) {
      span.recordException(err as Error);
      span.setStatus({ code: SpanStatusCode.ERROR, message: 'wystawienie nieudane' });
      throw err;
    } finally {
      span.end();          // brak end() = wyciek pamięci i brak przęsła w ślad
    }
  });
}
```

Atrybuty przęsła mogą mieć wysoką kardynalność (identyfikatory są tu w porządku, inaczej
niż w metrykach), ale **nie mogą zawierać danych osobowych ani sekretów** — obowiązuje
ta sama lista zakazów co dla logów.

### Konwencje nazw (semconv 1.43)

Używaj standardowych nazw atrybutów, nie własnych. Zysk: gotowe pulpity i zapytania
w dowolnym backendzie działają bez konfiguracji.

| Zamiast | Użyj |
| --- | --- |
| `http_method`, `method` | `http.request.method` |
| `status`, `http_status` | `http.response.status_code` |
| `url`, `path` | `url.full`, `url.path`, `http.route` |
| `db_query`, `sql` | `db.query.text`, `db.system.name`, `db.collection.name` |
| `env`, `stage` | `deployment.environment.name` |
| `error`, `err_msg` | `error.type` (klasa błędu), wyjątek przez `recordException` |

Stabilne obszary konwencji: HTTP, bazy danych, systemy komunikatów, zasoby, wyjątki.
Konwencje GenAI (`gen_ai.*`) zostały wydzielone do osobnego repozytorium i wciąż
ewoluują — przy instrumentowaniu wywołań LLM sprawdź bieżący stan zamiast zakładać
stabilność nazw.

### Próbkowanie

100% śladów na produkcji o dużym ruchu jest niepotrzebne i drogie. Reguła praktyczna:

```bash
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1        # 10% ruchu normalnego
```

Ale: **próbkuj 100% śladów zakończonych błędem i tych powyżej progu opóźnienia.**
To wymaga próbkowania „po fakcie” (tail sampling) w kolektorze — próbkowanie na kliencie
nie wie jeszcze, czy żądanie padnie. Konfiguracja w OpenTelemetry Collector:
`tail_sampling` z regułami `status_code = ERROR` oraz `latency > 2s` przy podstawowej
stopie 10%.

Bez tego 90% śladów, których naprawdę potrzebujesz przy diagnozie, zostanie odrzuconych.

### Logi w OTel

Sygnał logów w OTel jest stabilny w specyfikacji; dojrzałość SDK różni się między
językami. Praktyczne podejście: pisz logi strukturalne na stdout, zbieraj kolektorem
(`filelog` receiver), wzbogacaj o `trace_id`/`span_id` z kontekstu. Wtedy z przęsła
przechodzisz do logów tego samego żądania jednym kliknięciem — i to jest cała wartość
integracji logów ze śladami.

---

## Sentry

Sentry uzupełnia (nie zastępuje) OTel: grupuje wyjątki w problemy, deduplikuje, wiąże
błąd z wydaniem i commitem, pokazuje pierwsze i ostatnie wystąpienie.

```ts
// instrument.ts — import przed aplikacją, tak samo jak OTel
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.COMMIT_SHA,          // bez tego nie ma „regresja od wydania X"
  tracesSampleRate: 0.1,
  enableLogs: true,                          // w v10 opcja najwyższego poziomu (w v9 była w _experiments)
  sendDefaultPii: false,                     // domyślnie fałsz; true wysyła m.in. adres IP
  beforeSend(zdarzenie) {
    if (zdarzenie.request?.headers) {
      delete zdarzenie.request.headers.authorization;
      delete zdarzenie.request.headers.cookie;
    }
    return zdarzenie;
  },
});
```

Zmiany istotne w v10 (wobec v9): `enableLogs` przeniesione z `_experiments` na najwyższy
poziom; `hasTracingEnabled` → `hasSpansEnabled`; `BaseClient` → `Client`; przestano
raportować FID (zastąpione przez INP) — jeśli masz alarmy na FID, przestaną działać;
od 10.4 zbieranie adresu IP zależy wyłącznie od `sendDefaultPii`.

Warunki, bez których Sentry jest tylko kolejnym strumieniem szumu:

1. **`release` ustawione na skrót commita** i mapy źródeł wgrane przy budowaniu — inaczej
   ślady stosu są zminifikowane i bezużyteczne.
2. **Filtruj błędy, na które nie zareagujesz**: rozszerzenia przeglądarki, boty,
   `ResizeObserver loop limit exceeded`, anulowane żądania. Bez filtrowania problemy
   realne toną w szumie.
3. **Ustal właściciela problemu.** Problem bez właściciela zostaje otwarty na zawsze,
   a licznik „1247 nieprzejrzanych problemów” oznacza, że narzędzie przestało działać.

---

## Alarmy

### Alarmuj na objawy odczuwane przez użytkownika

| Zły alarm (przyczyna/zasób) | Dobry alarm (objaw) |
| --- | --- |
| CPU > 80% przez 5 min | p95 czasu odpowiedzi `/api/*` > 2 s przez 10 min |
| Zajętość dysku > 70% | odsetek 5xx > 1% przez 5 min |
| Liczba restartów poda > 3 | wskaźnik powodzenia logowania < 95% przez 10 min |
| Kolejka > 1000 komunikatów | wiek najstarszego nieprzetworzonego komunikatu > 15 min |
| Instancja nieodpowiada | test sztuczny ścieżki krytycznej pada z dwóch regionów |

CPU 90% przy działającej usłudze to nie awaria, tylko dobre wykorzystanie zasobu.
Alarm na zasób budzi ludzi bez powodu i uczy ich ignorowania powiadomień.

Wyjątek uzasadniony: alarmy na zasoby **wyczerpywalne bez powrotu** — miejsce na dysku,
wygasające certyfikaty (30 i 7 dni przed), limity API, zbliżające się przepełnienie
klucza głównego typu `int4`. Tu przewidywanie ma sens, bo objaw pojawia się dopiero
w momencie awarii całkowitej.

### Budżet błędów zamiast progu absolutnego

Zdefiniuj cel (SLO), np. „99,5% żądań `/api/faktury` kończy się poniżej 1 s w oknie
30 dni”. Budżet błędów to 0,5% — czyli około 3,6 godziny niedotrzymania na miesiąc.

- Alarm **szybkiego wypalania**: 2% budżetu w godzinę → budzi.
- Alarm **wolnego wypalania**: 10% budżetu w 3 dni → zgłoszenie w godzinach pracy.

Ta konstrukcja usuwa alarmy od chwilowych skoków, a wyłapuje powolną degradację, którą
progi absolutne przepuszczają.

### Zmęczenie alarmowe

Objawy: alarm, który był ignorowany 5 razy z rzędu; kanał alarmowy wyciszony; „to zawsze
tak miga”. Alarm ignorowany jest gorszy niż jego brak — daje fałszywe poczucie pokrycia
i zaśmieca uwagę.

Reguły higieny:

1. **Każdy alarm budzący człowieka ma podręcznik postępowania** (co sprawdzić, co zrobić,
   kogo zawołać). Alarm bez podręcznika = ktoś obudzony bez planu.
2. **Każdy alarm ma odpowiedź na pytanie „co człowiek ma zrobić o 3 w nocy”.** Jeśli
   odpowiedź brzmi „nic, samo się naprawi” — to nie jest alarm, tylko metryka na pulpicie.
3. **Co miesiąc przegląd**: alarmy, które nie zadziałały ani razu (czy nadal mają sens),
   i te, które zadziałały bez potrzeby (podnieś próg albo usuń).
4. **Limit**: więcej niż 2 nocne wybudzenia na tydzień na dyżurnego oznaczają, że system
   albo alarmy wymagają naprawy. To liczba, nie odczucie.

---

## Pulpity, które ktoś naprawdę czyta

Trzy warstwy, każda dla innego odbiorcy:

| Pulpit | Odbiorca | Zawartość | Liczba wykresów |
| --- | --- | --- | --- |
| Stan usługi | dyżurny w trakcie alarmu | 4 złote sygnały, stan zależności, ostatnie wdrożenia | 6–8 |
| Diagnostyczny | inżynier szukający przyczyny | rozbicie po endpointach, zasoby, kolejki, baza | 15–25 |
| Biznesowy | zespół produktu | rejestracje, transakcje, przychód, konwersja | 5–10 |

Zasady:

- **Znaczniki wdrożeń na osi czasu.** Pytanie „czy to od wdrożenia” pada w każdej awarii;
  bez znaczników odpowiedź zajmuje 10 minut, z nimi 2 sekundy.
- **Ta sama oś czasu na wszystkich wykresach pulpitu.** Porównywanie wykresów z różnymi
  zakresami produkuje błędne wnioski.
- **Linia celu na wykresie**, żeby odróżnić „wysoko” od „za wysoko”.
- **Pulpit z 40 wykresami nie jest czytany.** Jeśli wykres nie zmienił niczyjej decyzji
  przez kwartał — usuń go.

---

## Retencja i koszt

Koszt obserwowalności potrafi przekroczyć koszt infrastruktury produkcyjnej. Trzy dźwignie
w kolejności skuteczności:

1. **Kardynalność metryk** (patrz wyżej) — największy pojedynczy czynnik.
2. **Objętość logów** — `debug` na produkcji, logowanie całych obiektów, log na każdą
   iterację pętli.
3. **Stopa próbkowania śladów.**

Rozsądne domyślne okresy retencji:

| Dane | Retencja | Uzasadnienie |
| --- | --- | --- |
| Logi `error`/`warn` | 30–90 dni | diagnoza i wzorce; RODO ogranicza dłuższe trzymanie danych z identyfikatorami |
| Logi `info` | 7–14 dni | wystarcza na diagnozę bieżącą |
| Logi `debug` | 24–48 h, włączane punktowo | objętość rośnie o rząd wielkości |
| Metryki, pełna rozdzielczość | 15 dni | analiza incydentu |
| Metryki, agregat godzinowy | 13 miesięcy | porównanie rok do roku, planowanie |
| Ślady | 7–30 dni | diagnoza; starsze nikt nie otwiera |
| Logi audytowe (kto co zmienił) | zgodnie z wymogiem prawnym, zwykle 5 lat | osobny magazyn, niezmienny |

Logi audytowe trzymaj **osobno** od logów diagnostycznych: mają inny cel, inną retencję,
inne uprawnienia i muszą przetrwać czyszczenie logów operacyjnych.

---

## Kontrola obserwowalności przed wdrożeniem funkcji

- [ ] Każda ścieżka błędu ma log z `error.type` i identyfikatorem korelacji.
- [ ] Żaden log nie zawiera hasła, tokenu, PESEL, e-maila ani treści dokumentu (test w CI).
- [ ] Nowe endpointy widoczne w metrykach RED z etykietą będącą wzorcem ścieżki.
- [ ] Operacje długotrwałe mają własne przęsło z sensowną nazwą.
- [ ] Nowe zależności zewnętrzne mają metrykę czasu i odsetka błędów.
- [ ] Jeśli funkcja ma cel dostępnościowy — SLO zdefiniowane, alarm na wypalanie budżetu.
- [ ] Alarm, który powstał razem z funkcją, ma podręcznik postępowania.
