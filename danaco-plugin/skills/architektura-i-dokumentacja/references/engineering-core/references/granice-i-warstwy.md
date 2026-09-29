# Granice i warstwy

Warstwa to odpowiedź na pytanie „co ten kod wie o świecie”. Domena nie wie nic —
nie wie, że istnieje HTTP, baza danych ani framework. Infrastruktura wie o wszystkim.
Zależności biegną **do środka**: infrastruktura zależy od domeny, nigdy odwrotnie.

Naruszenie tej jednej reguły jest przyczyną większości sytuacji „nie da się tego
przetestować bez postawienia bazy” i „zmiana dostawcy wymaga przepisania logiki”.

## Cztery warstwy

| Warstwa | Zawiera | Wolno importować | Zabronione |
| --- | --- | --- | --- |
| **Domena** | Encje, obiekty wartości, reguły, niezmienniki, zdarzenia domenowe, typy błędów domenowych | Bibliotekę standardową i własne typy domenowe. Nic więcej | ORM, klient HTTP, SDK, logger frameworka, `process.env`, `datetime.now()` |
| **Aplikacja** | Przypadki użycia, orkiestracja, granica transakcji, autoryzacja operacji, definicje portów | Domenę, porty (własne interfejsy) | Konkretne implementacje, typy frameworka (`Request`, `Response`) |
| **Infrastruktura** | Repozytoria, adaptery do usług zewnętrznych, mapowanie encja↔wiersz, zegar, generator UUID | Domenę, aplikację, biblioteki zewnętrzne | Warstwę prezentacji |
| **Prezentacja** | Kontrolery HTTP, komendy CLI, konsumenci kolejki, harmonogram, GraphQL resolvery | Aplikację, typy DTO | Domenę bezpośrednio, repozytoria bezpośrednio |

Trzecia kolumna jest ważniejsza od pierwszej. Warstwa jest zdefiniowana przez to, czego
**nie wolno** w niej użyć.

## Czego nie wolno przepuścić przez granicę

Wyciek przez granicę zwykle nie wygląda groźnie w momencie popełnienia. Poniżej lista
konkretnych rzeczy, których obecność po złej stronie oznacza, że granica już nie działa.

### Do domeny nie wchodzi

| Wyciek | Jak wygląda | Konsekwencja | Poprawka |
| --- | --- | --- | --- |
| Typ ORM-a | `class Zgloszenie extends Model` / dekorator `@Entity` | Nie da się przetestować reguły bez bazy; zmiana ORM-a = przepisanie domeny | Czysta klasa/typ + osobny mapper w infrastrukturze |
| Zegar systemowy | `new Date()` / `datetime.now()` wewnątrz reguły | Testy niedeterministyczne; nie da się przetestować „co po terminie” | Port `Zegar` wstrzykiwany; w testach zegar ustawiony |
| Losowość | `crypto.randomUUID()` w konstruktorze encji | Ten sam problem co zegar | Port `GeneratorId` |
| Typ HTTP | `Request`, `Response` w sygnaturze reguły | Reguła użyteczna tylko z HTTP; cron jej nie wywoła | DTO wejściowe, zwykły typ |
| Konfiguracja | `process.env.STAWKA_VAT` w kalkulacji | Reguła zależy od środowiska; niepowtarzalna w teście | Parametr przekazany z warstwy aplikacji |
| Logger frameworka | `logger.info` z biblioteki | Domena zależy od infrastruktury logowania | Zwracaj zdarzenia domenowe; loguj w warstwie wyżej |

### Do prezentacji nie wychodzi

| Wyciek | Konsekwencja | Poprawka |
| --- | --- | --- |
| Encja domenowa serializowana wprost do JSON | Zmiana wewnętrznego pola łamie API konsumenta; wyciekają pola wewnętrzne (`wersja`, `usunieteDnia`, hash hasła) | Jawny DTO odpowiedzi z jawnym mapowaniem |
| Wyjątek bazy danych (`UniqueViolation`, `SQLSTATE 23505`) | Klient dostaje 500 zamiast 409; komunikat zdradza nazwy tabel | Mapowanie na błąd domenowy w repozytorium |
| Typy ORM w odpowiedzi (`Decimal` z biblioteki, `Prisma.JsonValue`) | Serializacja niedeterministyczna, klient dostaje `{"s":1,"e":2,"d":[...]}` | Konwersja w mapperze |
| Stos wywołań w treści błędu | Wyciek ścieżek i wersji bibliotek — informacja dla atakującego | Identyfikator korelacji w odpowiedzi, stos wyłącznie do logu |

### Między modułami nie przechodzi

- Encja domenowa innego modułu. Przechodzą DTO i identyfikatory.
- Zapytanie SQL z JOIN-em do tabel cudzego modułu.
- Repozytorium cudzego modułu.
- Import z głębi cudzego modułu z pominięciem `index.ts`.

## Porty i adaptery

Port to interfejs zdefiniowany **w warstwie aplikacji**, wyrażony w słowniku domeny.
Adapter to implementacja tego interfejsu, żyjąca w infrastrukturze.

Kluczowe i najczęściej mylone: port należy do wnętrza, nie do zewnętrza. Nazwa portu
mówi, czego domena potrzebuje, a nie czego używa dostawca.

```
Dobrze:  interface WysylkaPowiadomien { powiadomOZamknieciu(...): Promise<void> }
Źle:     interface KlientSendgrid { sendMail(opts: SendgridOptions): Promise<Response> }
```

Drugi wariant to nie port, tylko przepisany SDK. Zmiana dostawcy wymusi zmianę
interfejsu, czyli zmianę warstwy aplikacji — czyli port nie spełnił swojego zadania.

### Kompletny przykład — TypeScript

```typescript
// ── src/modules/zgloszenia/domain/Zgloszenie.ts ──────────────────────────
export type StatusZgloszenia = 'nowe' | 'w_toku' | 'zamkniete';

export class BlednePrzejscieStatusu extends Error {
  constructor(z: StatusZgloszenia, na: StatusZgloszenia) {
    super(`Nie można przejść ze statusu ${z} na ${na}`);
    this.name = 'BlednePrzejscieStatusu';
  }
}

export interface Zgloszenie {
  readonly id: string;
  readonly klientId: string;
  readonly status: StatusZgloszenia;
  readonly utworzono: Date;
  readonly zamknieto: Date | null;
}

const DOZWOLONE: Record<StatusZgloszenia, StatusZgloszenia[]> = {
  nowe: ['w_toku', 'zamkniete'],
  w_toku: ['zamkniete'],
  zamkniete: [],
};

export function zamknij(z: Zgloszenie, teraz: Date): Zgloszenie {
  if (!DOZWOLONE[z.status].includes('zamkniete')) {
    throw new BlednePrzejscieStatusu(z.status, 'zamkniete');
  }
  return { ...z, status: 'zamkniete', zamknieto: teraz };
}
```

Ten plik nie importuje niczego. Da się go przetestować w mikrosekundach i nie zmieni
się, gdy zmienisz bazę, framework albo dostawcę poczty.

```typescript
// ── src/modules/zgloszenia/application/porty.ts ──────────────────────────
import type { Zgloszenie } from '../domain/Zgloszenie';

export interface RepozytoriumZgloszen {
  pobierz(id: string): Promise<Zgloszenie | null>;
  zapisz(z: Zgloszenie): Promise<void>;
}

export interface Zegar {
  teraz(): Date;
}

export interface Powiadomienia {
  powiadomOZamknieciu(zgloszenieId: string, klientId: string): Promise<void>;
}

// ── src/modules/zgloszenia/application/zamknijZgloszenie.ts ──────────────
import { zamknij } from '../domain/Zgloszenie';
import type { Powiadomienia, RepozytoriumZgloszen, Zegar } from './porty';

export class ZgloszenieNieIstnieje extends Error {
  constructor(public readonly id: string) {
    super(`Zgłoszenie ${id} nie istnieje`);
    this.name = 'ZgloszenieNieIstnieje';
  }
}

export interface ZaleznosciZamkniecia {
  repozytorium: RepozytoriumZgloszen;
  zegar: Zegar;
  powiadomienia: Powiadomienia;
}

export async function zamknijZgloszenie(
  dep: ZaleznosciZamkniecia,
  zgloszenieId: string,
): Promise<void> {
  const zgloszenie = await dep.repozytorium.pobierz(zgloszenieId);
  if (zgloszenie === null) throw new ZgloszenieNieIstnieje(zgloszenieId);

  const zamkniete = zamknij(zgloszenie, dep.zegar.teraz());
  await dep.repozytorium.zapisz(zamkniete);
  await dep.powiadomienia.powiadomOZamknieciu(zamkniete.id, zamkniete.klientId);
}
```

```typescript
// ── src/modules/zgloszenia/infrastructure/RepozytoriumZgloszenPg.ts ──────
import type { Pool } from 'pg';
import type { Zgloszenie, StatusZgloszenia } from '../domain/Zgloszenie';
import type { RepozytoriumZgloszen } from '../application/porty';

interface WierszZgloszenia {
  id: string;
  klient_id: string;
  status: StatusZgloszenia;
  utworzono: Date;
  zamknieto: Date | null;
}

function naDomene(w: WierszZgloszenia): Zgloszenie {
  return {
    id: w.id,
    klientId: w.klient_id,
    status: w.status,
    utworzono: w.utworzono,
    zamknieto: w.zamknieto,
  };
}

export class RepozytoriumZgloszenPg implements RepozytoriumZgloszen {
  constructor(private readonly pool: Pool) {}

  async pobierz(id: string): Promise<Zgloszenie | null> {
    const { rows } = await this.pool.query<WierszZgloszenia>(
      'SELECT id, klient_id, status, utworzono, zamknieto FROM zgloszenia WHERE id = $1',
      [id],
    );
    return rows.length === 0 ? null : naDomene(rows[0]);
  }

  async zapisz(z: Zgloszenie): Promise<void> {
    await this.pool.query(
      `INSERT INTO zgloszenia (id, klient_id, status, utworzono, zamknieto)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status,
                                      zamknieto = EXCLUDED.zamknieto`,
      [z.id, z.klientId, z.status, z.utworzono, z.zamknieto],
    );
  }
}
```

```typescript
// ── src/modules/zgloszenia/http/zamknijHandler.ts ────────────────────────
import type { Request, Response } from 'express';
import { zamknijZgloszenie, ZgloszenieNieIstnieje } from '../application/zamknijZgloszenie';
import { BlednePrzejscieStatusu } from '../domain/Zgloszenie';
import type { ZaleznosciZamkniecia } from '../application/zamknijZgloszenie';

export function zamknijHandler(dep: ZaleznosciZamkniecia) {
  return async (req: Request, res: Response): Promise<void> => {
    try {
      await zamknijZgloszenie(dep, req.params.id);
      res.status(204).end();
    } catch (e) {
      if (e instanceof ZgloszenieNieIstnieje) {
        res.status(404).json({ type: 'about:blank', title: 'Nie znaleziono', status: 404 });
        return;
      }
      if (e instanceof BlednePrzejscieStatusu) {
        res.status(409).json({ type: 'about:blank', title: 'Konflikt stanu', status: 409, detail: e.message });
        return;
      }
      throw e;
    }
  };
}
```

Test przypadku użycia nie potrzebuje bazy ani serwera:

```typescript
import { zamknijZgloszenie } from '../application/zamknijZgloszenie';
import type { Zgloszenie } from '../domain/Zgloszenie';

test('zamknięcie ustawia datę i powiadamia klienta', async () => {
  const teraz = new Date('2026-08-04T10:00:00Z');
  let zapisane: Zgloszenie | null = null;
  const powiadomienia: string[] = [];

  await zamknijZgloszenie(
    {
      repozytorium: {
        pobierz: async () => ({
          id: 'z1', klientId: 'k1', status: 'w_toku',
          utworzono: new Date('2026-08-01T10:00:00Z'), zamknieto: null,
        }),
        zapisz: async (z) => { zapisane = z; },
      },
      zegar: { teraz: () => teraz },
      powiadomienia: { powiadomOZamknieciu: async (id) => { powiadomienia.push(id); } },
    },
    'z1',
  );

  expect(zapisane?.status).toBe('zamkniete');
  expect(zapisane?.zamknieto).toEqual(teraz);
  expect(powiadomienia).toEqual(['z1']);
});
```

### Ten sam wzorzec w Pythonie

```python
# ── src/zgloszenia/domain/zgloszenie.py ─────────────────────────────────
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal

Status = Literal["nowe", "w_toku", "zamkniete"]

DOZWOLONE: dict[Status, frozenset[Status]] = {
    "nowe": frozenset({"w_toku", "zamkniete"}),
    "w_toku": frozenset({"zamkniete"}),
    "zamkniete": frozenset(),
}


class BlednePrzejscieStatusu(Exception):
    def __init__(self, z: Status, na: Status) -> None:
        super().__init__(f"Nie można przejść ze statusu {z} na {na}")


@dataclass(frozen=True, slots=True)
class Zgloszenie:
    id: str
    klient_id: str
    status: Status
    utworzono: datetime
    zamknieto: datetime | None


def zamknij(z: Zgloszenie, teraz: datetime) -> Zgloszenie:
    if "zamkniete" not in DOZWOLONE[z.status]:
        raise BlednePrzejscieStatusu(z.status, "zamkniete")
    return replace(z, status="zamkniete", zamknieto=teraz)
```

```python
# ── src/zgloszenia/application/porty.py ─────────────────────────────────
from datetime import datetime
from typing import Protocol

from ..domain.zgloszenie import Zgloszenie


class RepozytoriumZgloszen(Protocol):
    async def pobierz(self, id: str) -> Zgloszenie | None: ...
    async def zapisz(self, z: Zgloszenie) -> None: ...


class Zegar(Protocol):
    def teraz(self) -> datetime: ...


class Powiadomienia(Protocol):
    async def powiadom_o_zamknieciu(self, zgloszenie_id: str, klient_id: str) -> None: ...
```

```python
# ── src/zgloszenia/application/zamknij_zgloszenie.py ────────────────────
from dataclasses import dataclass

from ..domain.zgloszenie import zamknij
from .porty import Powiadomienia, RepozytoriumZgloszen, Zegar


class ZgloszenieNieIstnieje(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ZaleznosciZamkniecia:
    repozytorium: RepozytoriumZgloszen
    zegar: Zegar
    powiadomienia: Powiadomienia


async def zamknij_zgloszenie(dep: ZaleznosciZamkniecia, zgloszenie_id: str) -> None:
    zgloszenie = await dep.repozytorium.pobierz(zgloszenie_id)
    if zgloszenie is None:
        raise ZgloszenieNieIstnieje(zgloszenie_id)

    zamkniete = zamknij(zgloszenie, dep.zegar.teraz())
    await dep.repozytorium.zapisz(zamkniete)
    await dep.powiadomienia.powiadom_o_zamknieciu(zamkniete.id, zamkniete.klient_id)
```

`Protocol` zamiast `ABC` — nie wymaga dziedziczenia po stronie adaptera, więc adapter
nie musi importować portu. Zależność biegnie tylko w jedną stronę, statycznie
sprawdzana przez mypy/pyright.

## Struktura katalogów

### TypeScript — monolit modularny

```
src/
  modules/
    zgloszenia/
      index.ts                 ← publiczne API modułu; jedyny punkt wejścia
      domain/
        Zgloszenie.ts
        regulySla.ts
      application/
        porty.ts
        zamknijZgloszenie.ts
        przyjmijZgloszenie.ts
      infrastructure/
        RepozytoriumZgloszenPg.ts
        PowiadomieniaOutbox.ts
      http/
        router.ts
        dto.ts
      __tests__/
    klienci/
      ...
    rozliczenia/
      ...
  platform/                    ← wspólne, BEZ logiki domenowej
    db.ts                      ← pula połączeń
    config.ts                  ← walidacja env przy starcie
    errors.ts                  ← bazowe typy błędów
    id.ts                      ← generator UUIDv7
    zegar.ts
  main.ts                      ← montaż zależności; JEDYNE miejsce z `new`
```

`main.ts` jest jedynym miejscem, w którym konkretne implementacje spotykają się z
portami. Nie potrzebujesz kontenera DI — potrzebujesz jednej funkcji montującej:

```typescript
// src/main.ts
import express from 'express';
import { Pool } from 'pg';
import { RepozytoriumZgloszenPg } from './modules/zgloszenia/infrastructure/RepozytoriumZgloszenPg';
import { PowiadomieniaOutbox } from './modules/zgloszenia/infrastructure/PowiadomieniaOutbox';
import { routerZgloszen } from './modules/zgloszenia/http/router';
import { config } from './platform/config';

const pool = new Pool({ connectionString: config.DATABASE_URL });

const zgloszenia = {
  repozytorium: new RepozytoriumZgloszenPg(pool),
  powiadomienia: new PowiadomieniaOutbox(pool),
  zegar: { teraz: () => new Date() },
};

const app = express();
app.use(express.json());
app.use('/api/zgloszenia', routerZgloszen(zgloszenia));
app.listen(config.PORT);
```

Kontener DI wprowadzaj dopiero wtedy, gdy montaż przekracza ~150 linii. Wcześniej jest
kosztem bez zysku: dodaje dekoratory, metadane i błędy wykrywane dopiero w runtime.

### Python — ten sam podział

```
src/
  zgloszenia/
    __init__.py                ← publiczne API modułu (jawne `__all__`)
    domain/
      zgloszenie.py
      reguly_sla.py
    application/
      porty.py
      zamknij_zgloszenie.py
    infrastructure/
      repozytorium_pg.py
      powiadomienia_outbox.py
    api/
      router.py                ← FastAPI APIRouter
      schematy.py              ← modele Pydantic (DTO, nie encje)
  platform/
    db.py
    config.py                  ← pydantic-settings
    errors.py
  main.py
tests/
  zgloszenia/
    test_domain.py             ← bez I/O
    test_zamkniecie.py         ← z atrapami portów
    test_repozytorium_pg.py    ← z prawdziwą bazą (testcontainers)
```

Modele Pydantic są **DTO warstwy prezentacji**, nie encjami domenowymi. Encja to
`@dataclass(frozen=True, slots=True)`. Mieszanie tego jest najczęstszym przeciekiem
warstw w projektach FastAPI: model Pydantic z walidacją, ORM-em i regułą biznesową
w jednym miejscu.

## Wykrywanie naruszeń granic

Reguła, której nie sprawdza narzędzie, zostanie naruszona w ciągu miesiąca.

### TypeScript — ESLint `no-restricted-imports`

```javascript
// eslint.config.js
export default [
  {
    files: ['src/modules/*/domain/**/*.ts'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          { group: ['**/infrastructure/**', '**/http/**'], message: 'Domena nie zależy od infrastruktury ani od HTTP.' },
          { group: ['pg', 'prisma', '@prisma/*', 'express', 'axios', 'node:fs'], message: 'Domena nie importuje bibliotek zewnętrznych.' },
        ],
      }],
    },
  },
  {
    files: ['src/modules/**/*.ts'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          { group: ['**/modules/*/domain/*', '**/modules/*/infrastructure/*', '**/modules/*/application/*'],
            message: 'Import z wnętrza innego modułu. Użyj jego index.ts.' },
        ],
      }],
    },
  },
];
```

Uzupełniająco `dependency-cruiser` wykrywa cykle, których ESLint nie widzi:

```json
{
  "forbidden": [
    { "name": "brak-cykli", "severity": "error", "from": {}, "to": { "circular": true } },
    { "name": "domena-czysta", "severity": "error",
      "from": { "path": "^src/modules/[^/]+/domain" },
      "to": { "pathNot": "^src/modules/[^/]+/domain|^node:" } }
  ]
}
```

### Python — import-linter

```ini
# setup.cfg / .importlinter
[importlinter]
root_package = src

[importlinter:contract:warstwy]
name = Zależności biegną do środka
type = layers
layers =
    src.zgloszenia.api
    src.zgloszenia.infrastructure
    src.zgloszenia.application
    src.zgloszenia.domain

[importlinter:contract:moduly-niezalezne]
name = Moduły nie sięgają do swoich wnętrz
type = independence
modules =
    src.zgloszenia
    src.klienci
    src.rozliczenia
```

`lint-imports` w CI. Kontrakt `layers` egzekwuje kierunek, `independence` blokuje
poziome zależności między modułami — komunikacja tylko przez `__init__.py`.

### Sygnały naruszenia widoczne bez narzędzi

| Objaw | Co naprawdę znaczy |
| --- | --- |
| Test logiki biznesowej wymaga uruchomienia bazy | Domena zależy od infrastruktury |
| `import` z `express`/`fastapi` w pliku z regułami | Prezentacja wciekła do domeny |
| Kontroler ma >40 linii | Logika w kontrolerze zamiast w przypadku użycia |
| Ten sam warunek biznesowy w kontrolerze i w serwisie | Reguła nie ma jednego miejsca |
| Encja ma pole `_dirty`, `_loaded`, `save()` | Encja jest wierszem bazy, nie modelem domeny |
| Zmiana nazwy kolumny łamie API HTTP | Brak DTO; encja serializowana wprost |
| Moduł A importuje z `modules/b/domain/...` | Granica modułu istnieje tylko w katalogu |

## Kiedy warstwy są przesadą

Pełny podział na cztery warstwy z portami kosztuje ~4 pliki na przypadek użycia.
Nie warto tego robić wszędzie:

| Sytuacja | Wystarczy |
| --- | --- |
| CRUD bez reguł (słownik, konfiguracja, kategorie) | Kontroler → repozytorium. Bez warstwy aplikacji |
| Skrypt jednorazowy, migracja danych | Jeden plik |
| Prototyp odrzucany po demonstracji | Cokolwiek, byle oznaczone jako prototyp |
| Moduł ogólny użyty przez bibliotekę (auth) | Konfiguracja biblioteki, nie własna warstwa |

Warstwy zakładaj tam, gdzie jest **reguła biznesowa** — czyli warunek, który da się
naruszyć i który ktoś kiedyś zmieni. Tam, gdzie kod tylko przenosi dane, warstwy dodają
tylko pliki. Kryterium: czy istnieje test, który sprawdza regułę, a nie mapowanie?
