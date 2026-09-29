# Strategia testów — co testować, czego nie, i dlaczego zestaw jest wolny

Wersje odniesienia (sierpień 2026): Vitest **4.1.10** (Vitest 5 w beta),
pytest **9.1.1**, `pytest-asyncio` **1.4.0**, Hypothesis **6.165**, `msw` **2.15**,
`testcontainers` (Node) **12.1**, `freezegun` **1.5.5**.

---

## Zasada doboru: test ma zapobiegać awarii, nie podnosić liczbę

Przed napisaniem testu odpowiedz: **jaka awaria u użytkownika nie wystąpi dzięki temu
testowi?** Jeśli odpowiedź brzmi „żadna” albo „że getter przestanie zwracać pole” — nie
pisz go. Test bez tej odpowiedzi to koszt utrzymania bez zysku: będzie padał przy każdej
refaktoryzacji i nie wyłapie żadnego błędu.

### Co testować — w kolejności wartości

| Priorytet | Obszar | Dlaczego |
| --- | --- | --- |
| 1 | Reguły biznesowe z pieniędzmi, terminami, uprawnieniami | Awaria kosztuje bezpośrednio; reguły są złożone i zmienne |
| 2 | Granice ufności: walidacja wejścia, authz, dane od użytkownika | Tu powstają luki bezpieczeństwa |
| 3 | Obsługa błędów i przypadki brzegowe (`null`, puste, ujemne, ogromne) | Happy path działa zawsze; padają brzegi |
| 4 | Integralność danych: migracje, transakcje, idempotencja | Skutki są nieodwracalne |
| 5 | Ścieżki krytyczne end-to-end (logowanie, zakup, wystawienie dokumentu) | Awaria = usługa nieużywalna |
| 6 | Kontrakty między usługami i z konsumentami API | Awaria jest cudza i zauważona późno |
| 7 | Regresje: każdy naprawiony błąd dostaje test | Ten sam błąd wraca statystycznie najczęściej |

### Czego nie testować

- Getterów, setterów, prostych mapowań pole-w-pole bez logiki.
- Frameworka i bibliotek zewnętrznych (`że Prisma zapisuje do bazy`, `że React renderuje`).
- Konfiguracji jako takiej (`że plik ma 3 klucze`) — sprawdź typem/schematem przy starcie.
- Prywatnych metod. Test prywatnej metody przypina cię do implementacji; testuj przez
  publiczne wejście, a jeśli się nie da, prywatna metoda chce być osobną jednostką.
- Kodu jednorazowego: skryptów migracyjnych uruchamianych raz, prototypów.
- UI na poziomie „czy `div` ma klasę `flex`”. To test CSS-a, a nie zachowania.

Konsekwencja testowania powyższych: zestaw rośnie, czas rośnie, każda refaktoryzacja
wymaga poprawienia 40 testów, zespół przestaje refaktoryzować.

---

## Piramida i jej krytyka

Klasyczna piramida (dużo jednostkowych, mniej integracyjnych, kilka e2e) jest domyślnie
poprawna, ale ma dwie znane wady:

1. **Testy jednostkowe z ciężkim atrapowaniem nie dowodzą, że system działa.** Jeśli
   każda zależność jest atrapą, test sprawdza zgodność kodu z twoim wyobrażeniem o
   zależności, a nie z zależnością. Klasyczny przypadek: wszystkie testy zielone,
   aplikacja nie startuje, bo zmieniła się sygnatura repozytorium — atrapa jej nie znała.
2. **Granica „jednostki” jest umowna.** Testowanie każdej klasy osobno produkuje testy
   przypięte do struktury, a nie do zachowania.

Praktyczny kompromis — **trofeum testowe**: najwięcej testów integracyjnych (moduł
z prawdziwą bazą w kontenerze, bez sieci zewnętrznej), sporo jednostkowych dla logiki
czystej, mało e2e, dużo analizy statycznej (typy, lint) jako podstawa.

Reguła rozstrzygająca: **jednostka to fragment, który ma sens biznesowy i którego
kontrakt nie zmieni się przy refaktoryzacji wnętrza.** Zwykle to przypadek użycia albo
moduł, nie pojedyncza klasa.

### Proporcje, od których warto zacząć

| Rodzaj | Udział | Czas jednego | Co dowodzą |
| --- | --- | --- | --- |
| Jednostkowe (logika czysta) | 50–60% | < 10 ms | reguła liczy poprawnie |
| Integracyjne (moduł + baza/HTTP) | 30–40% | 50–500 ms | części się składają |
| Kontraktowe | kilka–kilkanaście | < 100 ms | konsument i dostawca się rozumieją |
| End-to-end | 5–15 przypadków | 2–20 s | ścieżka krytyczna przechodzi w całości |

15 testów e2e to nie jest za mało. 150 to za dużo — zestaw będzie trwał 40 minut,
migotał i nikt nie będzie czekał na jego wynik.

---

## Testy jednostkowe

### Struktura: układ – działanie – sprawdzenie

```ts
import { describe, it, expect } from 'vitest';
import { obliczOdsetkiUstawowe } from '../src/odsetki';

describe('obliczOdsetkiUstawowe', () => {
  it('nalicza od dnia następnego po terminie płatności', () => {
    // układ
    const kwota = 10_000_00;                     // grosze
    const termin = new Date('2026-01-31');
    const zaplata = new Date('2026-03-02');

    // działanie
    const wynik = obliczOdsetkiUstawowe({ kwota, termin, zaplata, stawka: 0.1125 });

    // sprawdzenie — 30 dni: 1..2 marca liczone, 31 stycznia nie
    expect(wynik.dni).toBe(30);
    expect(wynik.kwotaGroszy).toBe(92_47);
  });

  it('zwraca zero, gdy zapłacono w terminie', () => {
    const wynik = obliczOdsetkiUstawowe({
      kwota: 10_000_00, termin: new Date('2026-01-31'),
      zaplata: new Date('2026-01-31'), stawka: 0.1125,
    });
    expect(wynik.kwotaGroszy).toBe(0);
  });
});
```

Nazwa testu opisuje **zachowanie i warunek**, nie nazwę metody. `it('nalicza od dnia
następnego po terminie płatności')` mówi, co jest regułą; `it('test1')` i `it('działa
poprawnie')` nie mówią nic i przy padnięciu wymagają czytania kodu.

Jedna asercja logiczna na test. Trzy asercje sprawdzające ten sam fakt są w porządku;
trzy sprawdzające trzy różne reguły ukrywają dwie z nich — przy padnięciu pierwszej
pozostałe się nie wykonają.

### Testy oparte na własnościach (property-based)

Tam, gdzie reguła ma dać się wyrazić niezmiennikiem, jeden test właściwości zastępuje
dwadzieścia przykładów i znajduje przypadki brzegowe, których nie wymyśliłbyś.

```python
from hypothesis import given, strategies as st
from decimal import Decimal
from faktury import brutto, netto

@given(
    kwota=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000000"), places=2),
    stawka=st.sampled_from([Decimal("0"), Decimal("0.05"), Decimal("0.08"), Decimal("0.23")]),
)
def test_netto_brutto_sa_odwrotne(kwota, stawka):
    assert netto(brutto(kwota, stawka), stawka) == kwota
```

Typowe niezmienniki: kodowanie/dekodowanie są odwrotne, sortowanie zachowuje długość,
operacja idempotentna daje ten sam wynik przy powtórzeniu, suma części równa się całości.

### Atrapy i ich nadużywanie

Trzy różne rzeczy, których model używa zamiennie:

| Rodzaj | Co robi | Kiedy właściwe |
| --- | --- | --- |
| **stub** | zwraca ustaloną wartość | podstawienie danych wejściowych |
| **fake** | działająca uproszczona implementacja (repozytorium w pamięci) | najczęściej najlepsze: szybkie i realistyczne |
| **mock** | weryfikuje, że wywołano go w określony sposób | tylko gdy sam fakt wywołania jest regułą biznesową (wysłano e-mail, pobrano opłatę) |

Reguła: **atrapuj granice procesu (sieć, zegar, losowość, system plików, płatności), nie
własne moduły.** Atrapa własnego modułu przypina test do struktury kodu, a nie do
zachowania — po refaktoryzacji trzeba przepisać test, choć zachowanie się nie zmieniło.

```ts
// ŹLE — atrapa własnego repozytorium sprawdzająca sposób wywołania
const repo = { zapisz: vi.fn() };
await wystawFakture(dane, repo);
expect(repo.zapisz).toHaveBeenCalledWith(expect.objectContaining({ numer: 'FV/1' }));
// przy zmianie kolejności pól albo dodaniu argumentu test pada, choć wszystko działa

// LEPIEJ — fake i asercja na obserwowalnym skutku
const repo = new RepozytoriumWPamieci();
await wystawFakture(dane, repo);
expect(await repo.znajdzPoNumerze('FV/1')).toMatchObject({ kwotaGroszy: 184_500 });
```

Sygnał nadużycia: w teście jest więcej linii konfiguracji atrap niż linii sprawdzenia.
Wtedy problem jest w projekcie — moduł ma za dużo zależności. Rozdziel go zamiast
rozbudowywać atrapy.

Atrapowanie sieci na poziomie HTTP zamiast poziomu klienta:

```ts
// msw 2.15 — przechwytuje na poziomie żądania, więc test przechodzi przez prawdziwy
// kod klienta HTTP (nagłówki, serializacja, obsługa błędów)
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const serwer = setupServer(
  http.get('https://api.nbp.pl/api/exchangerates/rates/a/eur', () =>
    HttpResponse.json({ rates: [{ mid: 4.3125, effectiveDate: '2026-08-04' }] })),
);
beforeAll(() => serwer.listen({ onUnhandledRequest: 'error' }));
afterEach(() => serwer.resetHandlers());
afterAll(() => serwer.close());
```

`onUnhandledRequest: 'error'` jest istotne: bez tego test po cichu strzela do prawdziwego
API, działa u ciebie i pada w CI bez sieci.

---

## Testy integracyjne

Definicja robocza: kod działa z **prawdziwą** zależnością infrastrukturalną (baza,
kolejka, cache), a atrapowane są tylko systemy trzecie, których nie kontrolujesz.

```ts
// testcontainers 12 — prawdziwy PostgreSQL na czas zestawu
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';

let kontener: StartedPostgreSqlContainer;

beforeAll(async () => {
  kontener = await new PostgreSqlContainer('postgres:17-alpine').start();
  process.env.DATABASE_URL = kontener.getConnectionUri();
  await migruj();                       // ten sam mechanizm migracji co na produkcji
}, 60_000);

afterAll(async () => { await kontener.stop(); });

beforeEach(async () => {
  await db.$executeRawUnsafe('TRUNCATE faktury, kontrahenci RESTART IDENTITY CASCADE');
});
```

Dlaczego prawdziwa baza, a nie SQLite w pamięci: różnice w typach (`TIMESTAMPTZ`,
`NUMERIC`, tablice, JSONB), w zachowaniu transakcji, w ograniczeniach unikalności i
w składni. Test na SQLite przechodzi, produkcja na PostgreSQL pada — i odwrotnie, co
gorsze: nie wykryjesz błędu, który wystąpi.

Alternatywa dla `TRUNCATE`: każdy test w transakcji wycofywanej na końcu. Szybsze, ale
nie działa, gdy testowany kod sam zarządza transakcjami.

Izolacja przy zrównolegleniu: osobny **schemat** na worker (`SET search_path`), nie osobna
baza — tworzenie bazy jest wolne, schematu nie.

---

## Testy kontraktowe

Problem: usługa A woła usługę B. Testy A używają atrapy B. B zmienia format odpowiedzi.
Testy obu przechodzą, produkcja pada. Testy kontraktowe zamykają tę dziurę.

Wariant lekki, wystarczający dla większości zespołów — **wspólny schemat jako źródło
prawdy**:

```ts
// kontrakt w jednym miejscu, importowany przez obie strony
export const OdpowiedzKursu = z.object({
  kod: z.string().length(3),
  kurs: z.number().positive(),
  data: z.string().date(),
});

// po stronie dostawcy: test, że prawdziwa odpowiedź pasuje do schematu
it('odpowiedź /kurs zgodna z kontraktem', async () => {
  const odp = await request(app).get('/kurs/EUR');
  expect(() => OdpowiedzKursu.parse(odp.body)).not.toThrow();
});

// po stronie konsumenta: atrapy budowane z tego samego schematu
const atrapa = OdpowiedzKursu.parse({ kod: 'EUR', kurs: 4.31, data: '2026-08-04' });
```

Zmiana schematu psuje typy po obu stronach w czasie kompilacji. To tańsze niż pełny
Pact i wyłapuje większość realnych rozjazdów. Pełne narzędzie kontraktowe ma sens, gdy
konsument i dostawca należą do różnych zespołów z osobnymi cyklami wydań.

Dla API publicznego: test, że wygenerowana specyfikacja OpenAPI nie zmieniła się
w sposób łamiący (`oasdiff --fail-on breaking`) — bramka w CI, nie ręczne oko.

---

## Testy migracji bazy

Najczęściej pomijana kategoria, a skutki awarii są nieodwracalne.

Co sprawdzić dla każdej migracji zmieniającej dane:

1. **Migracja przechodzi na kopii schematu produkcyjnego z danymi**, nie na pustej bazie.
   Pusta baza nie ma rekordów z 2011 roku z `NULL` w polu, które teraz staje się `NOT NULL`.
2. **Wycofanie (`down`) działa** albo jest jawnie zadeklarowane jako niemożliwe.
   Migracja bez wycofania jest dopuszczalna, ale musi być świadoma i odnotowana.
3. **Czas wykonania na produkcyjnej wielkości.** `ALTER TABLE ... ADD COLUMN NOT NULL
   DEFAULT` na 50 mln wierszy blokuje tabelę. Zmierz na kopii.
4. **Stary kod działa na nowym schemacie** — warunek wdrożenia stopniowego.

```python
def test_migracja_nadaje_domyslny_nip_dla_starych_rekordow(baza_z_kopia_prod):
    przed = baza_z_kopia_prod.execute(
        "SELECT count(*) FROM kontrahenci WHERE nip IS NULL").scalar()
    assert przed > 0, "kopia bez rekordów bez NIP nie testuje niczego"

    uruchom_migracje("0042_nip_not_null")

    assert baza_z_kopia_prod.execute(
        "SELECT count(*) FROM kontrahenci WHERE nip IS NULL").scalar() == 0
    assert baza_z_kopia_prod.execute(
        "SELECT count(*) FROM kontrahenci").scalar() == liczba_przed_migracja
```

Ostatnia asercja (liczba rekordów bez zmian) wyłapuje migracje, które „naprawiły” dane przez ich
usunięcie. Procedura bezpiecznej migracji przy wdrożeniu:
`references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.

---

## Dane testowe i fabryki

Trzy stopnie, w kolejności rosnącego kosztu i rosnącej użyteczności:

```ts
// 1. Literał — dobre dla 1-2 testów
const faktura = { numer: 'FV/1', kwotaGroszy: 100_00, kontrahentId: 'k1' };

// 2. Fabryka z sensownymi domyślnymi — standard
export function fakturaTestowa(nadpisz: Partial<Faktura> = {}): Faktura {
  return {
    id: crypto.randomUUID(),
    numer: `FV/2026/08/${licznik++}`,
    kwotaGroszy: 100_00,
    stawkaVat: 23,
    kontrahentId: kontrahentTestowy().id,
    wystawionaDnia: new Date('2026-08-04'),
    ...nadpisz,
  };
}

// w teście widać TYLKO to, co ma znaczenie dla testowanej reguły
const f = fakturaTestowa({ kwotaGroszy: -1 });
```

Kluczowa zaleta fabryki: test pokazuje różnicę istotną dla reguły, a nie 12 pól bez
znaczenia. Czytający od razu wie, że testowana jest ujemna kwota.

Zasady:

- **Domyślne wartości muszą być poprawne** — fabryka produkuje obiekt przechodzący
  walidację. Inaczej połowa testów pada z powodów niezwiązanych z testowaną regułą.
- **Unikalność w polach unikalnych** (licznik albo UUID), inaczej zrównoleglenie pada
  na kluczu unikalnym.
- **Zero zależności między testami**: fabryka nie zapisuje do współdzielonej bazy, chyba
  że test o to jawnie poprosi.
- **Nie wczytuj wielkich zestawów `fixtures` na cały zestaw.** Test zależny od 400
  rekordów, których nie widać w jego kodzie, jest nieczytelny i kruchy.

Dane z produkcji w testach: **tylko anonimizowane**. Nazwiska, NIP-y, adresy e-mail,
numery kont, PESEL — do zamiany przed opuszczeniem produkcji. Wgranie zrzutu produkcyjnego
na maszynę deweloperską to naruszenie RODO, nie wygoda.

---

## Determinizm i izolacja

Test niedeterministyczny jest gorszy niż brak testu: kosztuje uwagę i uczy zespół
ignorowania czerwonego.

### Trzy źródła niedeterminizmu i ich neutralizacja

**Czas.** Zamroź go zawsze, gdy wynik od niego zależy.

```ts
import { vi } from 'vitest';
vi.useFakeTimers();
vi.setSystemTime(new Date('2026-08-04T10:00:00Z'));
// ...
vi.useRealTimers();
```

```python
from freezegun import freeze_time

@freeze_time("2026-08-04 10:00:00", tz_offset=0)
def test_termin_platnosci_14_dni():
    assert termin_platnosci().isoformat() == "2026-08-18"
```

W Playwright: `page.clock.setFixedTime(...)` albo `page.clock.install()` + `fastForward`.

**Losowość.** Wstrzykuj generator, nie wołaj `Math.random()` w środku logiki.
W Pythonie pamiętaj o `PYTHONHASHSEED` — kolejność iteracji `set` jest losowa między
uruchomieniami i test porównujący listę ze zbioru będzie migotał.

**Strefa i locale.** Ustaw je jawnie w konfiguracji zestawu (`TZ=Europe/Warsaw`,
`LC_ALL=pl_PL.UTF-8` albo `C`), a nie polegaj na maszynie. Dodatkowo raz na dobę uruchom
zestaw z `TZ=Pacific/Kiritimati` — wyłapie założenia „lokalny = UTC”.

### Izolacja stanu

```ts
afterEach(() => {
  vi.restoreAllMocks();       // przywraca oryginały wszystkich vi.spyOn
  localStorage.clear();
  serwerMsw.resetHandlers();
});
```

Sprawdzian izolacji — uruchom zestaw w losowej kolejności:

```bash
vitest --sequence.shuffle --sequence.seed=12345
pytest -p randomly                # pytest-randomly, domyślnie losuje
pytest -p no:randomly             # powtórzenie z konkretnym ziarnem: -p randomly --randomly-seed=12345
```

Jeśli po przetasowaniu coś pada, masz wyciek stanu między testami. To usterka testów,
nie „dziwna kolejność”.

---

## Testy migoczące — wykrywanie i eliminacja

### Wykrywanie

```bash
npx playwright test --repeat-each=20 --workers=4       # 20 przebiegów tego samego
vitest --retry=0 --sequence.shuffle                     # bez ponowień maskujących
pytest --count=20 -p repeat tests/test_kolejka.py
```

W CI: zbieraj wynik każdego uruchomienia testu do bazy i licz współczynnik padnięć na
nazwę testu. Test z padnięciem > 1% jest migoczący, nawet jeśli „zwykle przechodzi”.

### Katalog przyczyn

| Przyczyna | Objaw | Naprawa |
| --- | --- | --- |
| Sztywne opóźnienie zamiast oczekiwania | Pada na obciążonym CI | `expect(locator)` / `waitFor`; usuń wszystkie `sleep` |
| Asercja na pobranej wartości zamiast na lokatorze | Pada losowo przy wolniejszym renderowaniu | `await expect(loc).toHaveText(...)`, nie `expect(await loc.textContent())` |
| Współdzielona baza między równoległymi testami | Pada, gdy inny test doda rekord | Unikalne dane na test; asercja po kluczu, nie po liczbie |
| Zależność od czasu rzeczywistego | Pada o północy / na przełomie miesiąca | Zamrożony zegar |
| Zależność od kolejności | Pada w pełnym zestawie, przechodzi solo | Sprzątanie w `afterEach`; sprawdzian przez `--shuffle` |
| Zewnętrzne API | Pada, gdy cudza usługa ma awarię | msw / nagrany HAR; `onUnhandledRequest: 'error'` |
| Animacje i przejścia | Element „porusza się” przy kliknięciu | `animations: 'disabled'`, `prefers-reduced-motion` w konfiguracji testowej |
| Wyciek zasobów | Pada dopiero po N testach | Zamykaj połączenia; `--detectOpenHandles` (Node), `pytest --timeout` |

### Postępowanie z migoczącym testem

1. **Nie dodawaj `retry`.** Ponowienie ukrywa problem, który zwykle jest realnym wyścigiem
   w kodzie produkcyjnym — czyli błędem, który zobaczy użytkownik.
2. Oznacz i odizoluj: `test.fixme()` / `@pytest.mark.flaky` z **datą i właścicielem**.
3. Napraw w ciągu tygodnia albo usuń. Test wyłączony na stałe jest kłamstwem w statystyce
   pokrycia.

---

## Pokrycie jako sygnał, nie cel

Pokrycie mierzy, które linie **zostały wykonane**, a nie które zostały **sprawdzone**.
Test bez ani jednej asercji, który tylko wywołuje funkcję, daje 100% pokrycia tej funkcji.

```js
// vitest.config.ts
coverage: {
  provider: 'v8',
  reporter: ['text', 'lcov'],
  include: ['src/**'],
  exclude: ['src/**/*.d.ts', 'src/**/index.ts', 'src/generated/**'],
  thresholds: {
    lines: 70,
    'src/domena/**': { lines: 90, branches: 85 },    // rdzeń wyżej niż całość
  },
}
```

Jak używać liczby:

- **Próg globalny 70–80%** jako bramka „nie schodzimy niżej”, nie jako cel.
- **Rdzeń domenowy 90%+**, warstwa infrastruktury i UI znacznie niżej — to normalne.
- **Patrz na pokrycie gałęzi (`branches`), nie linii.** `if` z niesprawdzonym `else` daje
  wysokie pokrycie linii i zero wartości.
- **Pokrycie różnicy (diff coverage)** jest użyteczniejsze niż globalne: „nowy kod w tym
  PR ma 85% pokrycia” mówi coś, czego „projekt ma 73%” nie mówi.

Antywzorzec: cel 100%. Osiąga się go pisząc testy na kod trywialny i wyłączając trudny
przez `/* istanbul ignore */`. Efekt: mnóstwo testów, zerowy przyrost bezpieczeństwa,
i wolny zestaw.

Testowanie mutacyjne (Stryker, `mutmut`) mierzy to, co pokrycie mierzyć chciało: czy
testy **wykryją** zmianę w kodzie. Kosztowne — puszczaj nocnie na rdzeniu domenowym,
nie na całości przy każdym PR.

---

## Szybkość zestawu

Budżety, po przekroczeniu których zachowanie zespołu się zmienia (przestaje uruchamiać
testy lokalnie):

| Zestaw | Budżet | Co zrobić po przekroczeniu |
| --- | --- | --- |
| Jednostkowe, lokalnie | < 10 s | Znajdź 10 najwolniejszych i napraw je |
| Jednostkowe + integracyjne, CI | < 5 min | Zrównoleglenie, podział na projekty |
| Pełny e2e | < 15 min | Sharding, mniej testów e2e, więcej integracyjnych |
| Od pushu do wyniku | < 10 min | Bramka szybka (lint+typy+jednostkowe) osobno od reszty |

Techniki w kolejności zwrotu z inwestycji:

```bash
vitest --reporter=verbose --slowTestThreshold=300     # wskaże najwolniejsze
pytest --durations=20                                  # 20 najwolniejszych
npx playwright test --shard=1/4                        # podział między maszyny CI
```

1. **Znajdź 10 najwolniejszych testów.** Zwykle 5% testów zjada 50% czasu; to prawie
   zawsze testy, które podnoszą coś ciężkiego w `beforeEach` zamiast w `beforeAll`.
2. **Przenieś testy w dół piramidy.** Test e2e walidacji pola → test jednostkowy.
3. **Zrównoleglaj**, ale najpierw zapewnij izolację (patrz wyżej), inaczej kupujesz
   migotanie za szybkość.
4. **Cache zależności i przeglądarek w CI** (`~/.cache/ms-playwright`, `node_modules`,
   `~/.cache/pip`) — patrz
   `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md`.
5. **Nie buduj obrazu produkcyjnego dla testów jednostkowych.** Buduj raz, wynik przekaż
   jako artefakt między etapami.

---

## Kiedy testy się nie opłacają

Uczciwe wyjątki, w których pisanie testów jest kosztem bez zwrotu:

- Prototyp z jawnie zadeklarowanym terminem wyrzucenia (i naprawdę wyrzucany).
- Skrypt jednorazowy, uruchamiany raz pod nadzorem.
- Kod, który za tydzień zostanie zastąpiony, a jego awaria nie kosztuje.

Poza tym: brak testu na regułę biznesową dotyczącą pieniędzy, uprawnień albo danych
osobowych to nie oszczędność, tylko odroczony koszt z odsetkami.

Kolejność, gdy dostajesz nietestowany kod i masz go zmienić: **najpierw test
charakteryzujący** (opisujący obecne zachowanie, także błędne), potem zmiana. Bez niego
nie odróżnisz zmiany zamierzonej od przypadkowej.
