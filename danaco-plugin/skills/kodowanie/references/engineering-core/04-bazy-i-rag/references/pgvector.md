# pgvector

Stan: **0.8.6** (29.07.2026). Sprawdzone w CHANGELOG projektu 04.08.2026.

Istotne wydania:

| Wersja | Data | Co wniosło |
|---|---|---|
| 0.8.0 | 30.10.2024 | **iteracyjne skanowanie indeksu** (`iterative_scan`), lepsze szacowanie kosztu przy filtrowaniu, koniec wsparcia PG 12 |
| 0.8.1 | 04.09.2025 | wsparcie PG 18, szybszy `binary_quantize` |
| 0.8.2 | 25.02.2026 | poprawka przepełnienia bufora przy równoległej budowie HNSW |
| 0.8.3 | 17.06.2026 | poprawka możliwego **uszkodzenia indeksu HNSW przy vacuum** |
| 0.8.4 | 30.06.2026 | poprawka błędu `hnsw graph not repaired`, kontrola `maintenance_work_mem` przy IVFFlat |
| 0.8.5–0.8.6 | 08.07 / 29.07.2026 | zużycie pamięci przy IVFFlat, przepełnienie bufora na systemach 32-bitowych |

Jeśli klient ma 0.8.0–0.8.2 z indeksami HNSW i intensywnymi usunięciami — **aktualizacja
do ≥ 0.8.4 jest pilna**, bo 0.8.3 naprawia realne uszkodzenie indeksu przy vacuum.

## Instalacja

```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extversion FROM pg_extension WHERE extname = 'vector';
-- po podmianie plików rozszerzenia:
ALTER EXTENSION vector UPDATE;
```

Dostępne w RDS/Aurora, Cloud SQL, Azure Database for PostgreSQL, Neon, Supabase — ale
**wersja w usłudze zarządzanej bywa o kilka miesięcy w tyle**. Sprawdź `extversion`
przed obiecaniem klientowi funkcji z 0.8.x. Bez 0.8.0 nie ma `iterative_scan`, czyli
filtrowanie z wektorami działa źle i nie da się tego obejść parametrem.

## Typy i limity

| Typ | Maks. wymiarów | Maks. w indeksie | Rozmiar | Do czego |
|---|---|---|---|---|
| `vector` | 16 000 | **2 000** | 4·d + 8 B | domyślny, float32 |
| `halfvec` | 16 000 | **4 000** | 2·d + 8 B | float16 — połowa pamięci, strata jakości zwykle poniżej progu istotności |
| `bit` | 64 000 | 64 000 | d/8 + 8 B | kwantyzacja binarna, wstępne przesiewanie |
| `sparsevec` | 16 000 niezerowych | **1 000 niezerowych** | 8·nnz + 16 B | wektory rzadkie (SPLADE, BM25 jako wektor) |

**Limit 2000 wymiarów w indeksie dla `vector` jest twardy.** `text-embedding-3-large`
ma 3072 wymiary — nie zaindeksujesz go jako `vector`. Trzy wyjścia:
1. `halfvec(3072)` z indeksem HNSW (limit 4000) — najprostsze, strata recall rzędu 0,5–1 pp.
2. Skrócenie wymiaru przez Matryoshka do 1024/1536 na etapie API (`dimensions=1024`).
3. Model o mniejszym wymiarze. Zwykle najlepsze — patrz
   `references/engineering-core/04-bazy-i-rag/references/embeddingi.md`.

Rozmiar tabeli to nie tylko wektory: przy 1 mln fragmentów i 1024 wymiarach same wektory
to ~4,1 GB, indeks HNSW dokłada mniej więcej tyle samo, a `m=32` prawie dwa razy tyle.

## Operatory odległości

| Operator | Miara | Klasa operatora indeksu |
|---|---|---|
| `<->` | L2 (euklidesowa) | `vector_l2_ops`, `halfvec_l2_ops` |
| `<=>` | cosinusowa | `vector_cosine_ops`, `halfvec_cosine_ops` |
| `<#>` | ujemny iloczyn skalarny | `vector_ip_ops` |
| `<+>` | L1 (taksówkowa) | `vector_l1_ops` |
| `<~>` | Hamminga | `bit_hamming_ops` |
| `<%>` | Jaccarda | `bit_jaccard_ops` |

Twarda zasada: **klasa operatora indeksu musi zgadzać się z operatorem w zapytaniu.**
Indeks `vector_cosine_ops` nie zostanie użyty przez zapytanie z `<->`. To najczęstszy
powód „mam indeks HNSW, a zapytanie robi seq scan”.

Dla wektorów znormalizowanych (większość modeli zwraca takie) `<=>` i `<->` dają identyczny
ranking, a `<#>` jest najszybszy. Trzymaj się `<=>` — jest jednoznaczny i nie wymaga
zakładania normalizacji.

Uwaga na `<#>`: zwraca **ujemny** iloczyn skalarny, żeby `ORDER BY ... ASC` dawało
najbardziej podobne. Podobieństwo to `-(a <#> b)`.

## Schemat, który się nie zemści

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE dokumenty (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  zewn_id       text NOT NULL UNIQUE,
  tytul         text NOT NULL,
  suma          bytea NOT NULL,                 -- sha256 pliku, do deduplikacji
  wersja        int  NOT NULL DEFAULT 1,
  kancelaria_id bigint NOT NULL,
  poziom_dostepu text NOT NULL,
  utworzono     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE fragmenty (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  dokument_id   bigint NOT NULL REFERENCES dokumenty(id) ON DELETE CASCADE,
  wersja_dok    int    NOT NULL,
  nr            int    NOT NULL,                -- kolejność w dokumencie
  strona_od     int,
  strona_do     int,
  offset_od     int    NOT NULL,                -- pozycja znakowa w tekście źródłowym
  offset_do     int    NOT NULL,
  tresc         text   NOT NULL,
  kontekst      text,                           -- dopisany kontekst (Contextual Retrieval)
  model_emb     text   NOT NULL,                -- np. 'voyage-3.5'
  wymiar        int    NOT NULL,
  emb           vector(1024),
  tsv           tsvector GENERATED ALWAYS AS (to_tsvector('public.polski', tresc)) STORED,
  UNIQUE (dokument_id, wersja_dok, nr)
);

CREATE INDEX CONCURRENTLY idx_fr_dok  ON fragmenty (dokument_id);
CREATE INDEX CONCURRENTLY idx_fr_tsv  ON fragmenty USING gin (tsv);
CREATE INDEX CONCURRENTLY idx_fr_emb  ON fragmenty
  USING hnsw (emb vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

Cztery rzeczy, które muszą tu być i często ich nie ma:
- `model_emb` i `wymiar` przy każdym wierszu — bez nich migracja modelu jest niewykonalna,
  a mieszanka dwóch modeli w jednym indeksie daje wyniki, które wyglądają sensownie
  i są bezwartościowe.
- `offset_od`/`offset_do` — bez nich nie zweryfikujesz cytatu ani nie podświetlisz go w oryginale.
- `wersja_dok` — bez niej po aktualizacji dokumentu masz w indeksie dwa pokolenia fragmentów.
- Klucz obcy z `ON DELETE CASCADE` — usunięcie dokumentu musi usuwać fragmenty w tej samej
  transakcji, inaczej indeks przeżyje dokument.

## HNSW vs IVFFlat

| | HNSW | IVFFlat |
|---|---|---|
| Jakość przy tym samym czasie | wyższa | niższa |
| Czas budowy | wolniejszy (kilka–kilkanaście razy) | szybki |
| Pamięć | duża, graf w RAM | mała |
| Wymaga danych przed budową | nie | **tak** — buduje na podstawie próbki |
| Zachowanie przy dopisywaniu | dobre | degraduje, wymaga przebudowy |
| Kiedy | domyślnie, prawie zawsze | gdy budowa HNSW nie mieści się w oknie serwisowym albo RAM jest twardym limitem |

**Domyślnie HNSW.** IVFFlat wybieraj świadomie, nie z rozpędu.

### HNSW: parametry

Budowa:

| Parametr | Domyślnie | Efekt zwiększenia |
|---|---|---|
| `m` | 16 | więcej krawędzi na węzeł: lepszy recall, większy indeks (~liniowo), wolniejsza budowa |
| `ef_construction` | 64 | lepszy graf: wyższy recall, znacznie wolniejsza budowa, bez wpływu na rozmiar |

Zapytanie:

| Parametr | Domyślnie | Efekt |
|---|---|---|
| `hnsw.ef_search` | 40 | większe = lepszy recall, wolniej. Musi być ≥ `LIMIT` |

Dobór praktyczny:

| Skala | `m` | `ef_construction` | `ef_search` |
|---|---|---|---|
| < 100 tys. | 16 | 64 | 40 |
| 100 tys. – 1 mln | 16 | 128 | 100 |
| 1–10 mln | 24–32 | 200 | 100–200 |
| gdy recall < 0,95 mimo powyższego | 32–48 | 256 | 200–400 |

Zawsze zaczynaj od domyślnych i podnoś dopiero po zmierzeniu recall (patrz niżej).
Podniesienie `m` z 16 na 48 to trzykrotnie większy indeks — na 5 mln wektorów po 1024
wymiary różnica między 20 GB a 60 GB decyduje o tym, czy indeks mieści się w RAM.

Przyspieszenie budowy:

```sql
SET maintenance_work_mem = '8GB';   -- graf musi się zmieścić, inaczej budowa idzie na dysk
SET max_parallel_maintenance_workers = 7;
CREATE INDEX CONCURRENTLY idx_fr_emb ON fragmenty
  USING hnsw (emb vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

Jeśli w logu pojawi się `hnsw graph no longer fits into maintenance_work_mem`, budowa
przechodzi w tryb dyskowy i trwa wielokrotnie dłużej. Reguła: `maintenance_work_mem`
większy niż szacowany rozmiar grafu ≈ liczba_wektorów × (wymiar × 4 B + m × 2 × 8 B).

### IVFFlat: parametry

```sql
-- lists: liczba_wierszy/1000 dla ≤ 1 mln, sqrt(liczba_wierszy) powyżej
CREATE INDEX CONCURRENTLY idx_fr_emb_ivf ON fragmenty
  USING ivfflat (emb vector_cosine_ops) WITH (lists = 1000);

SET ivfflat.probes = 32;   -- start: sqrt(lists); probes = lists daje wyszukiwanie dokładne
```

IVFFlat buduje centroidy na podstawie danych obecnych w tabeli w momencie budowy.
**Budowanie indeksu na pustej tabeli daje bezużyteczny indeks** — to klasyczny błąd
w skryptach migracyjnych, które tworzą indeksy przed załadowaniem danych.

### Pomiar recall — obowiązkowy

Indeks ANN nie jest dokładny. Nikt nie wie, jak bardzo, dopóki nie zmierzy:

```sql
-- 1. wyniki dokładne (wymuś brak indeksu)
SET enable_indexscan = off; SET enable_bitmapscan = off;
CREATE TEMP TABLE dokladne AS
SELECT q.id AS qid, f.id AS fid
FROM zapytania_testowe q
CROSS JOIN LATERAL (
  SELECT id FROM fragmenty ORDER BY emb <=> q.emb LIMIT 10
) f;
RESET enable_indexscan; RESET enable_bitmapscan;

-- 2. wyniki z indeksu
SET hnsw.ef_search = 40;
CREATE TEMP TABLE przybliz AS
SELECT q.id AS qid, f.id AS fid
FROM zapytania_testowe q
CROSS JOIN LATERAL (
  SELECT id FROM fragmenty ORDER BY emb <=> q.emb LIMIT 10
) f;

-- 3. recall@10
SELECT count(*) FILTER (WHERE p.fid IS NOT NULL)::float / count(*) AS recall
FROM dokladne d LEFT JOIN przybliz p USING (qid, fid);
```

Próg akceptacji: **recall@10 ≥ 0,95**. Poniżej — podnieś `ef_search`, potem `m`.
Bez tego pomiaru całe strojenie wyższych warstw (reranker, prompt) mierzy szum.

## Kwantyzacja

Trzy poziomy, od najtańszego w utracie jakości:

### halfvec (float16)

```sql
ALTER TABLE fragmenty ALTER COLUMN emb TYPE halfvec(1024);
CREATE INDEX CONCURRENTLY ON fragmenty USING hnsw (emb halfvec_cosine_ops);
```

Połowa pamięci, spadek recall zwykle < 1 pp. **To jest domyślny wybór przy > 1 mln wektorów.**
Podnosi też limit indeksowanego wymiaru do 4000.

### Indeks na wyrażeniu halfvec (przechowaj float32, indeksuj float16)

```sql
CREATE INDEX CONCURRENTLY ON fragmenty
  USING hnsw ((emb::halfvec(1024)) halfvec_cosine_ops);

SELECT id FROM fragmenty
ORDER BY emb::halfvec(1024) <=> $1::halfvec(1024)
LIMIT 50;
```

Pełna precyzja w tabeli (do ponownego rankingu), oszczędność w indeksie.

### Kwantyzacja binarna + ponowny ranking

```sql
CREATE INDEX CONCURRENTLY ON fragmenty
  USING hnsw ((binary_quantize(emb)::bit(1024)) bit_hamming_ops);

-- dwuetapowo: tanio przesiej 500, dokładnie uszereguj 50
SELECT id, tresc
FROM (
  SELECT id, tresc, emb
  FROM fragmenty
  ORDER BY binary_quantize(emb)::bit(1024) <~> binary_quantize($1::vector)
  LIMIT 500
) s
ORDER BY s.emb <=> $1::vector
LIMIT 50;
```

32× mniejszy indeks. Recall po samym etapie binarnym spada wyraźnie (rząd 10–20 pp
w zależności od modelu), dlatego **drugi etap jest obowiązkowy**. Działa dobrze dla modeli
trenowanych pod kwantyzację (Cohere embed-v4, Voyage z `output_dtype`), źle dla dowolnych.

## Filtrowanie razem z wyszukiwaniem — najgroźniejsza pułapka

Zapytanie:

```sql
SELECT f.id, f.tresc
FROM fragmenty f
JOIN dokumenty d ON d.id = f.dokument_id
WHERE d.kancelaria_id = 42
ORDER BY f.emb <=> $1
LIMIT 10;
```

Co robi Postgres bez `iterative_scan`: indeks HNSW zwraca `ef_search` (40) najbliższych
wektorów **z całej tabeli**, potem filtr odrzuca te, które nie należą do kancelarii 42.
Jeśli ta kancelaria to 1% korpusu, z 40 kandydatów zostanie średnio 0–1.
**Zapytanie zwróci 1 wynik zamiast 10 i nikt nie dostanie błędu.** To jest cichy błąd
poprawności, nie wydajności.

Rozwiązanie od pgvector 0.8.0:

```sql
SET hnsw.iterative_scan = strict_order;   -- albo relaxed_order
SET hnsw.max_scan_tuples = 20000;         -- domyślnie 20000
SET hnsw.scan_mem_multiplier = 2;         -- ile razy work_mem wolno użyć
```

| Tryb | Zachowanie |
|---|---|
| `off` (domyślnie) | jeden przebieg, opisany wyżej problem |
| `strict_order` | dokłada kolejne warstwy skanowania, zachowuje ścisłą kolejność odległości |
| `relaxed_order` | szybszy, kolejność może być lekko naruszona — akceptowalne, gdy i tak jest reranker |

Dla IVFFlat: `SET ivfflat.iterative_scan = relaxed_order;` oraz `ivfflat.max_probes`.

**Ustaw `hnsw.iterative_scan` domyślnie dla roli aplikacyjnej.** Jeżeli w systemie są
uprawnienia per dokument (a w kancelarii są), to bez tego system po cichu gubi wyniki.

```sql
ALTER ROLE app SET hnsw.iterative_scan = 'strict_order';
ALTER ROLE app SET hnsw.ef_search = 100;
```

### Kiedy filtr jest bardzo selektywny

Gdy filtr zostawia mniej niż ~1000 wierszy, indeks wektorowy jest zbędny — dokładne
przeszukanie podzbioru jest szybsze i idealnie dokładne. Pomóż planerowi indeksem
częściowym albo denormalizacją klucza filtrującego do tabeli fragmentów:

```sql
-- denormalizacja: kancelaria_id w fragmentach + indeks częściowy per duży najemca
ALTER TABLE fragmenty ADD COLUMN kancelaria_id bigint NOT NULL;
CREATE INDEX CONCURRENTLY idx_fr_emb_k42 ON fragmenty
  USING hnsw (emb vector_cosine_ops) WHERE kancelaria_id = 42;
```

Indeksy częściowe per najemca mają sens do kilkudziesięciu najemców. Powyżej — jeden indeks +
`iterative_scan`, albo baza z natywną wielodostępnością
(`references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md`).

## Główna zaleta: jedna baza

To nie jest argument estetyczny, tylko lista rzeczy, których nie musisz robić:

- **Jedna transakcja.** Wstawienie dokumentu, jego fragmentów, wektorów i zmiany uprawnień
  są atomowe. Przy osobnej bazie wektorowej masz dwa systemy i zapis, który może się udać
  w połowie — i wtedy indeks pokazuje dokument, którego już nie ma, albo pokazuje go osobie,
  której właśnie odebrano dostęp.
- **Filtr uprawnień w `JOIN`-ie**, na aktualnych danych. Bez kopiowania ACL do metadanych
  wektorów i bez ryzyka, że kopia jest nieświeża.
- **Zapytania mieszane**: „fragmenty podobne do X z pism złożonych po 1.01.2026 w sprawach,
  gdzie stroną jest Y” to jedno zapytanie SQL, a nie trzy wywołania i łączenie w Pythonie.
- **Jedna kopia zapasowa i jedno PITR.** Odtworzenie stanu na 3 marca obejmuje też indeks.
- **Jeden system do monitorowania, aktualizowania i audytu bezpieczeństwa.**

Cena: pgvector nie jest najszybszy w benchmarkach QPS i zjada RAM na indeks HNSW.
To zwykle znacznie tańsze niż utrzymywanie spójności między dwoma systemami.

## Limity skali i moment przejścia dalej

Progi orientacyjne dla wektorów 1024-wymiarowych, maszyna 8 rdzeni / 64 GB:

| Fragmentów | Rozmiar wektorów | Indeks HNSW m=16 | Ocena |
|---|---|---|---|
| 100 tys. | ~0,4 GB | ~0,4 GB | trywialne |
| 1 mln | ~4 GB | ~4 GB | komfortowo, `vector` |
| 5 mln | ~20 GB | ~20 GB | granica RAM; przejdź na `halfvec` |
| 20 mln | ~80 GB (40 GB half) | ~40 GB | wymaga pgvectorscale/VectorChord albo dużej maszyny |
| 100 mln+ | setki GB | | dedykowana baza rozproszona |

Sygnały, że czas coś zmienić — w tej kolejności eskalacji:

1. **Budowa indeksu trwa dłużej niż okno serwisowe** → `maintenance_work_mem`,
   równoległość, budowa na replice.
2. **Indeks nie mieści się w RAM (`shared_buffers` + cache OS)**, opóźnienia skaczą
   → `halfvec`, potem kwantyzacja binarna z ponownym rankingiem.
3. **Nadal nie mieści się** → **pgvectorscale** (rozszerzenie Timescale, indeks
   StreamingDiskANN trzymany na dysku, z kwantyzacją SBQ) albo **VectorChord**
   (następca pgvecto.rs, indeks IVF/RaBitQ na dysku). Oba zostają w Postgresie —
   to jest właściwy krok przed wyjściem na zewnątrz.
   `[niepotwierdzone: bieżące numery wersji pgvectorscale i VectorChord na sierpień 2026]`
4. **Potrzebne > 100 mln wektorów, wiele węzłów, sharding, GPU** → dopiero teraz
   dedykowana baza (`references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md`).

Nie przechodź do punktu 4, mając niezrobiony 1 i 2. Większość „pgvector nie skaluje się”
to niestrojony `ef_search`, `maintenance_work_mem` na 64 MB i brak `halfvec`.

## Utrzymanie

- Po dużym imporcie: `ANALYZE fragmenty;` — planer bez statystyk nie wybierze indeksu
  wektorowego prawidłowo (od 0.8.0 szacowanie kosztu przy filtrowaniu jest lepsze,
  ale nadal potrzebuje statystyk).
- Autovacuum na tabeli z wektorami: obniż `autovacuum_vacuum_scale_factor` do 0,02,
  bo domyślne 0,2 na tabeli 10 mln wierszy oznacza czekanie na 2 mln martwych krotek.
- Masowa aktualizacja wektorów (ponowne osadzenie): buduj do nowej kolumny/tabeli
  i przełącz `ALTER TABLE ... RENAME`, zamiast `UPDATE` in-place. `UPDATE` tworzy nowe
  wersje wszystkich krotek i podwaja rozmiar tabeli przed vacuum.
- Przy usuwaniu dokumentów: `ON DELETE CASCADE` plus okresowy `VACUUM` — HNSW oznacza
  usunięte węzły, ale nie zwalnia miejsca w grafie do momentu vacuum.

```sql
ALTER TABLE fragmenty SET (
  autovacuum_vacuum_scale_factor = 0.02,
  autovacuum_analyze_scale_factor = 0.01
);
```
