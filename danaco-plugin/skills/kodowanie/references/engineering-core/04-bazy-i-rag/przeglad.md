# Bazy danych i wyszukiwanie znaczeniowe — przegląd modułu

Moduł obejmuje Postgresa jako bazę domyślną oraz potok wyszukiwania znaczeniowego po
dokumentach. Karty pogłębione wymienia tabela „Mapa plików referencyjnych” poniżej,
a wszystkie moduły `references/engineering-core/` —
`references/engineering-core/spis.md`. Poza modułem: podstawy pracy z bazą i migracje
w `references/bazy-danych/bazy-danych.md`.

Wersje narzędzi i bibliotek przywołane w tym module traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Dwie rzeczy naraz: (1) Postgres jako domyślna baza dla wszystkiego, co ma stan;
(2) potok od dokumentu do odpowiedzi z przypisem, który da się sprawdzić.
Klient buduje systemy na dużych zbiorach dokumentów prawniczych — **przypis, którego
nie da się zweryfikować co do słowa i strony, jest wadą krytyczną**, nie kosmetyczną.

## Kiedy wczytać ten moduł

- Trzeba zaprojektować schemat, dobrać typy, dołożyć indeks albo zdiagnozować wolne zapytanie.
- Zapytanie SQL działa wolno, blokuje się, zakleszcza albo baza „padła pod obciążeniem”.
- Trzeba włączyć wyszukiwanie pełnotekstowe, w szczególności po polsku (odmiana, diakrytyki).
- Ktoś mówi „chcemy przeszukiwać nasze dokumenty”, „zbuduj RAG”, „czat z PDF-ami”.
- Trzeba wybrać bazę wektorową albo ocenić, czy pgvector wystarczy.
- Trzeba dobrać model embeddingowy, rozmiar fragmentu, reranker; albo poprawić jakość istniejącego
  RAG.
- Odpowiedzi z dokumentów są nietrafne, zmyślone albo mają przypisy prowadzące donikąd.
- Trzeba zmierzyć jakość wyszukiwania i generowania oraz pilnować jej przy zmianach.

**Nie używaj, gdy:**
- Pytanie brzmi „jaka architektura”, „monolit czy usługi”, „gdzie postawić granicę modułu”, „jak
  modelować domenę na poziomie decyzji” →
  `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`.
- Chodzi o kod Pythona, SQLAlchemy, Alembic, Pydantic, FastAPI, pandas →
  `references/engineering-core/02-python-backend-dane/przeglad.md`. Tam jest ORM i migracje; tutaj
  jest to, co robi silnik bazy.
- Chodzi o wystawienie wyszukiwarki jako serwera MCP, definicje narzędzi, protokół →
  `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md`.
- Chodzi o hosting bazy, backup jako element CI/CD, monitoring produkcyjny →
  `references/engineering-core/07-debug-testy-deploy/przeglad.md` (tu jest tylko to, co ustawia się
  w samym Postgresie).

## Mapa plików referencyjnych

| Plik | Co zawiera | Kiedy wczytać |
|---|---|---|
| `references/engineering-core/04-bazy-i-rag/references/postgres.md` | typy (jsonb, tablice, zakresy, enum, identyfikatory), indeksy (btree, GIN, GiST, BRIN, częściowe, pokrywające), czytanie `EXPLAIN (ANALYZE, BUFFERS)`, transakcje i poziomy izolacji, blokady i zakleszczenia, FTS z konfiguracją polską (`unaccent`, stemmer PG19, hunspell na PG≤18), partycjonowanie, replikacja, kopie, pgbouncer, katalog błędów wydajnościowych | zawsze przy schemacie, wolnym zapytaniu, blokadach, FTS, skalowaniu Postgresa |
| `references/engineering-core/04-bazy-i-rag/references/pgvector.md` | wersje i instalacja, `vector`/`halfvec`/`bit`/`sparsevec` z limitami, operatory odległości, HNSW vs IVFFlat z parametrami budowy i zapytania, kwantyzacja, filtrowanie i `iterative_scan`, przechowywanie wektorów obok danych relacyjnych, limity skali, pgvectorscale i VectorChord | gdy wektory mają leżeć w Postgresie: projekt tabeli, dobór indeksu, wolne zapytanie wektorowe, filtr + wektor |
| `references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md` | Qdrant, Weaviate, Milvus, Chroma, LanceDB, Turbopuffer, Vespa, Elasticsearch/OpenSearch, Pinecone — model danych, filtrowanie, wielodostępność, replikacja, ceny, koszt przy 10 tys./1 mln/100 mln wektorów, hosting własny vs usługa, migracja | gdy pgvector przestaje wystarczać albo ktoś pyta „którą bazę wektorową” |
| `references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md` | pozyskanie (PDF z warstwą i bez, OCR, DOCX, HTML, e-mail), zachowanie struktury i tabel, normalizacja, wykrywanie języka, deduplikacja, model metadanych z uprawnieniami, aktualizacja przyrostowa i usuwanie | przy budowie indeksacji, przy „skąd brać te dokumenty”, przy skanach i OCR |
| `references/engineering-core/04-bazy-i-rag/references/fragmentacja.md` | strategie dzielenia z rozmiarami, nakładanie, hierarchia rodzic-dziecko, „late chunking”, kontekstualizacja fragmentu (Contextual Retrieval z liczbami), dobór do typu treści, pomiar wpływu | gdy trzeba wybrać rozmiar fragmentu albo poprawić trafność wyszukiwania |
| `references/engineering-core/04-bazy-i-rag/references/embeddingi.md` | dobór modelu, tabela aktualnych modeli z wymiarami i cenami, jakość dla polszczyzny (PL-MTEB), normalizacja, wsadowe osadzanie, wersjonowanie i koszt ponownego osadzenia, asymetria zapytanie/dokument, Matryoshka | przy wyborze modelu, przy planowaniu kosztu, przy migracji modelu |
| `references/engineering-core/04-bazy-i-rag/references/wyszukiwanie-hybrydowe.md` | BM25 i dlaczego samo wektorowe przegrywa na sygnaturach i cytatach, RRF i ważona suma, przepisywanie i rozszerzanie zapytania, HyDE, filtry, reranking z liczbami i kosztem, dobór k na każdym etapie | gdy trafność jest za niska, gdy w zapytaniach są numery spraw, nazwiska, sygnatury |
| `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md` | konstrukcja promptu, kolejność fragmentów, budżet kontekstu, wymuszenie przypisu do fragmentu i strony, Citations API i weryfikacja dosłowności, odmowa przy braku podstaw, sprzeczne źródła, strumieniowanie, buforowanie promptu | przy pisaniu warstwy generowania, przy halucynacjach, przy wymaganiu sprawdzalnych cytatów |
| `references/engineering-core/04-bazy-i-rag/references/ewaluacja.md` | budowa zbioru testowego, metryki wyszukiwania (recall@k, MRR, nDCG) i generowania, sędzia-model i jego pułapki, testy regresyjne, obserwowalność, koszt na zapytanie | zanim zmienisz cokolwiek w istniejącym RAG i zanim ogłosisz, że jest lepiej |
| `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` | długie okno kontekstu, buforowanie promptu, dostrajanie, zwykły FTS, agent z narzędziami, GraphRAG — progi opłacalności i uczciwe koszty | **zanim** zaczniesz budować RAG; przy pytaniu „czy długi kontekst nie wystarczy” |

## Objaw → plik

| Co mówi człowiek | Najpierw otwórz |
|---|---|
| „chcemy przeszukiwać nasze dokumenty”, „czat z PDF-ami” | `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md`, potem drzewo decyzyjne niżej |
| „zbuduj RAG” | `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` — sprawdź, czy na pewno |
| „odpowiedzi są zmyślone”, „powołuje nieistniejące wyroki” | `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md`, ale najpierw diagnoza ze Ścieżki B |
| „nie znajduje dokumentu, o którym wiem, że jest” | `references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md` (czy w ogóle jest w indeksie?) |
| „nie znajduje po sygnaturze / numerze faktury / nazwisku” | `references/engineering-core/04-bazy-i-rag/references/wyszukiwanie-hybrydowe.md` (brak BM25) |
| „przypis prowadzi do złego miejsca / nie ma numeru strony” | `references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md` (metadane), `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md` |
| „skany się nie indeksują”, „PDF wychodzi pusty” | `references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md` (OCR, warstwa tekstowa) |
| „polskie znaki psują wyszukiwanie”, „nie znajduje odmienionego słowa” | `references/engineering-core/04-bazy-i-rag/references/postgres.md` (konfiguracja FTS, `unaccent`) |
| „jaki model embeddingowy”, „ile to kosztuje” | `references/engineering-core/04-bazy-i-rag/references/embeddingi.md` |
| „ile tokenów ma mieć fragment” | `references/engineering-core/04-bazy-i-rag/references/fragmentacja.md` |
| „którą bazę wektorową wybrać” | `references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md` — ale najpierw drzewo decyzyjne |
| „pgvector nam nie wystarcza” | `references/engineering-core/04-bazy-i-rag/references/pgvector.md` (progi eskalacji), dopiero potem `references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md` |
| „HNSW czy IVFFlat”, „jak ustawić `ef_search`” | `references/engineering-core/04-bazy-i-rag/references/pgvector.md` |
| „po dodaniu filtra dostajemy mniej wyników” | `references/engineering-core/04-bazy-i-rag/references/pgvector.md` (`iterative_scan`) — to jest cichy błąd poprawności |
| „zapytanie SQL działa wolno” | `references/engineering-core/04-bazy-i-rag/references/postgres.md` (EXPLAIN, katalog błędów) |
| „baza się zakleszcza”, „migracja wisi” | `references/engineering-core/04-bazy-i-rag/references/postgres.md` (blokady, `lock_timeout`) |
| „za dużo połączeń do bazy” | `references/engineering-core/04-bazy-i-rag/references/postgres.md` (pgbouncer) |
| „skąd wiemy, że jest lepiej” | `references/engineering-core/04-bazy-i-rag/references/ewaluacja.md` |
| „czy długi kontekst nie wystarczy zamiast RAG” | `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` |
| „a może dostroimy model na naszych aktach” | `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` (to nie wprowadza faktów) |
| „zróbmy GraphRAG” | `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` (progi opłacalności) |

## Drzewo decyzyjne

### Krok 1 — czy w ogóle potrzebujesz RAG

Odpowiedz na cztery pytania. RAG jest uzasadniony, gdy **co najmniej dwie** odpowiedzi
są po prawej stronie.

| Pytanie | Bez RAG | Z RAG |
|---|---|---|
| Ile tekstu musi być dostępne, żeby odpowiedzieć? | ≤ 200 tys. tokenów łącznie | setki MB, GB, „wszystkie akta” |
| Jak często korpus się zmienia? | rzadko, wersjonowany ręcznie | codziennie, przyrostowo |
| Czy odpowiedź musi wskazać źródło co do strony? | nie, wystarczy sens | tak, przypis podlega weryfikacji |
| Czy istnieją uprawnienia per dokument? | nie | tak, użytkownik widzi podzbiór |

Skróty, które wygrywają zaskakująco często:

- **Korpus ≤ 200 tys. tokenów i stały** → wrzuć całość do promptu z buforowaniem.
  Odczyt z cache kosztuje 0,1× ceny wejścia u Anthropica; miesięczny korpus statutów
  firmy zmieści się i będzie tańszy oraz dokładniejszy niż potok RAG.
- **Zapytania to nazwy własne, sygnatury, numery** → samo BM25 / `tsvector`. Wektory
  tu przeszkadzają, nie pomagają.
- **Model ma narzędzia i może iterować** → agent z narzędziem `szukaj(fraza)` +
  `czytaj(dokument, strony)` bywa lepszy od jednorazowego pobrania top-k.
- **Wiedza jest w bazie relacyjnej, nie w tekście** → to jest zadanie dla SQL, nie dla RAG.

Pełna analiza kosztów każdej alternatywy:
`references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md`. **Przeczytaj ten plik,
zanim zbudujesz cokolwiek** — połowa projektów RAG to projekty, które nie powinny powstać.

### Krok 2 — jaka baza

```
Czy dane wektorowe muszą być spójne transakcyjnie z danymi relacyjnymi
(uprawnienia, wersje dokumentu, stan sprawy)?
├─ TAK → Postgres + pgvector.  To jest domyślna odpowiedź.
│         Przy > ~5 mln fragmentów rozważ pgvectorscale lub VectorChord
│         (indeks na dysku zamiast w RAM), zanim wyjdziesz z Postgresa.
└─ NIE
   ├─ < 1 mln wektorów, jeden proces, prototyp
   │     → pgvector i tak. Ewentualnie LanceDB/Chroma osadzone lokalnie.
   ├─ 1–50 mln wektorów, potrzebne bogate filtrowanie i wielodostępność
   │     → Qdrant (self-host lub cloud) albo dalej pgvector z pgvectorscale.
   ├─ > 100 mln wektorów, wiele węzłów, GPU, dane w jeziorze
   │     → Milvus / Zilliz.
   ├─ Bardzo dużo małych, rzadko odpytywanych przestrzeni (per klient, per sprawa)
   │     → Turbopuffer (koszt idzie za ruchem, nie za RAM-em) albo LanceDB na S3.
   └─ Już masz Elasticsearch/OpenSearch i BM25 jest sercem systemu
         → dołóż tam wektory (BBQ), nie stawiaj drugiego systemu.
```

Twarda reguła: **nie wprowadzaj drugiego systemu przechowywania, dopóki nie masz
zmierzonego problemu z pierwszym.** Dwa źródła prawdy o tym samym dokumencie to
gwarantowana niespójność między treścią, uprawnieniami i indeksem.

### Krok 3 — jaki potok

Kolejność, w której to się buduje. Nie przeskakuj etapów — każdy następny mierzy się
na wyniku poprzedniego.

```
0. Zbiór testowy: 50-100 realnych pytań z oczekiwanym dokumentem/stroną.
   Bez tego nie wiesz, czy cokolwiek poprawiasz.        → ewaluacja.md
1. Pozyskanie i normalizacja: plik → tekst + struktura + metadane.
   Tu leży 60% jakości całego systemu.                  → potok-dokumentow.md
2. Fragmentacja: 300-800 tokenów, granice strukturalne, metadane w każdym fragmencie.
                                                        → fragmentacja.md
3. Osadzenie: model wielojęzyczny, wersja zapisana przy każdym wektorze.
                                                        → embeddingi.md
4. Indeks: pgvector HNSW + GIN na tsvector (albo pg_search/BM25).
                                                        → pgvector.md, postgres.md
5. Wyszukiwanie: hybrydowe (wektor + BM25) → RRF → reranker → top 5-10.
                                                        → wyszukiwanie-hybrydowe.md
6. Generowanie: prompt z materiałem, wymuszony przypis, odmowa przy braku podstaw.
                                                        → generowanie-i-przypisy.md
7. Pomiar: recall@k przed generowaniem, wierność i trafność po.
                                                        → ewaluacja.md
```

Minimalna konfiguracja, od której startujesz, jeśli nikt nie podał inaczej:

| Decyzja | Wartość startowa | Uzasadnienie |
|---|---|---|
| Rozmiar fragmentu | 400–600 tokenów, nakładka 10–15% | kompromis potwierdzony na wielu korpusach; dokumenty prawnicze bliżej 600 |
| Model embeddingowy | `voyage-3.5` lub `embed-v4.0` (chmura), `Qwen3-Embedding-0.6B` (własny hosting) | wielojęzyczne, dobre po polsku |
| Wymiar | 1024 | mieści się w indeksie HNSW `vector` (limit 2000) i nie marnuje pamięci |
| Indeks | HNSW, `m=16`, `ef_construction=64` | domyślne pgvector; strojenie dopiero po pomiarze |
| Pobranie | 50 wektorowo + 50 BM25 → RRF → rerank → 10 | liczby z badań Contextual Retrieval i praktyki rerankerów |
| Generowanie | przypis do `chunk_id` + strony, obowiązkowa odmowa przy braku pokrycia | wymóg klienta prawniczego |

## Stan faktyczny na sierpień 2026

Sprawdzone przez WebSearch/WebFetch 4 sierpnia 2026. To liczby, których model nie zgaduje.

| Fakt | Wartość | Źródło / data |
|---|---|---|
| PostgreSQL stabilny | **18** (18.0 wydane 25.09.2025, poprawkowe 18.6) | postgresql.org/support/versioning, 2026-09-03 |
| PostgreSQL 19 | **wciąż w becie** (Beta 3 z 13.08.2026) — nie na produkcję | postgresql.org/about/news, 2026-09-03 |
| PG19: stemmer dla polskiego | **dodany do Snowball** („Add full text stemmers for Polish and Esperanto”, Tom Lane) | Release Notes PG19 |
| PostgreSQL 14 | koniec wsparcia **12.11.2026** | postgresql.org |
| pgvector | **0.8.6** (29.07.2026); 0.8.0 wprowadził `iterative_scan` | CHANGELOG pgvector |
| pgvector: limity wymiarów | `vector` 16 000 (indeks 2 000), `halfvec` 16 000 (indeks 4 000), `bit` 64 000, `sparsevec` 16 000 (indeks 1 000 niezerowych) | README pgvector |
| pg_search (ParadeDB, BM25 w Postgresie) | **0.25.0** (28.07.2026), oparty na Tantivy | pgxn.org |
| Qdrant | **1.19.0** (sierpień 2026); 1.18 (11.05.2026) wprowadził TurboQuant | Docker Hub, blog Qdrant |
| Milvus | **3.0.0** (29.07.2026): tabele zewnętrzne (Parquet/Lance/Iceberg), pola TEXT, indeks SINDI | milvus.io/docs/release_notes |
| Weaviate Cloud | darmowe 100 tys. obiektów; Flex od **45 USD/mies.**; Premium od **400 USD/mies.**; dysk od 0,12 USD/GiB | weaviate.io/pricing |
| Turbopuffer | dane do **0,33 USD/GB-mies.**, zapis do **2 USD/GB**, zapytania **1 USD/PB** skanu (obniżka z 5 USD/PB w II 2026), minimum 1,28 GB na zapytanie; plany 16 / 256 / ≥4096 USD/mies. | turbopuffer.com/pricing |
| OpenAI embeddingi | wciąż tylko `text-embedding-3-small` (0,02 USD/M), `-3-large` (0,13 USD/M), `ada-002`. **Brak następcy** | pricing OpenAI |
| Voyage | `voyage-4-large` 0,12 / `voyage-4` 0,06 / `voyage-4-lite` 0,02 USD/M, 32k kontekstu, wymiary 256/512/1024/2048; `voyage-context-4` 0,12 USD/M, 120k; **`voyage-law-2`** 0,12 USD/M | docs Voyage / MongoDB |
| Voyage rerank | `rerank-2.5` 0,05 USD/M, `rerank-2.5-lite` 0,02 USD/M, 32k kontekstu | jw. |
| Cohere | `embed-v4.0`: 128k kontekstu, wymiary 256/512/1024/1536; `rerank-v4.0-pro` i `-fast`: 32k | docs.cohere.com |
| Jina | `jina-embeddings-v5-text-small` (1024 wym., 32k, 677M param., 18.02.2026); `jina-reranker-v3.5` | jina.ai/models |
| Najlepsze po polsku (PL-MTEB) | ogólnie `Qwen3-Embedding-8B` 70,47 i `-4B` 69,37; **wyszukiwanie**: `stella-pl-retrieval-8k` 61,59, `stella-pl` 60,82 | PL-MTEB, wersja ACL 2026 |
| Contextual Retrieval (Anthropic) | odsetek nietrafionych top-20: 5,7% → 3,7% (kontekst przed osadzeniem) → 2,9% (+ kontekstowy BM25) → **1,9% (+ reranking)**; koszt 1,02 USD za 1 mln tokenów dokumentów | anthropic.com/news/contextual-retrieval |
| Citations API (Anthropic) | `char_location` / `page_location` / `content_block_location`; `cited_text` **nie liczy się do tokenów wyjściowych**; nie działa z wymuszonym formatem strukturalnym; nie cytuje skanów bez warstwy tekstowej | platform.claude.com/docs |
| Buforowanie promptu (Anthropic) | zapis 5 min = 1,25× ceny wejścia, zapis 1 h = 2×, **odczyt = 0,1×**; maks. 4 punkty cache; minimum 1024 tokeny (Sonnet 4.5/5), 512 (Opus 5) | jw. |
| „Context rot” | badanie Chroma z 14.07.2025 na 18 modelach: jakość spada nierównomiernie wraz z długością wejścia nawet na trywialnych zadaniach | trychroma.com/research/context-rot |
| RAGAS | **0.4.3** (13.01.2026) — API zmienione względem 0.1/0.2 | PyPI |
| Inne biblioteki | deepeval 4.1.5, arize-phoenix 19.15.0, trulens-eval 2.11.0, llama-index 0.14.23, langchain 1.3.14, unstructured 0.25.2, docling 2.118.0, chonkie 1.7.0, sentence-transformers 5.6.1 | PyPI, 4.08.2026 |

## Procedura

### Ścieżka A — „chcemy przeszukiwać nasze dokumenty” (nowy system)

1. **Zapytaj o pięć rzeczy, zanim zaproponujesz cokolwiek**: ile dokumentów i ile MB;
   jakie formaty i czy są skany; kto może widzieć co; jak często się zmieniają;
   czy odpowiedź musi wskazywać stronę. Bez tych odpowiedzi każdy projekt jest zgadywaniem.
2. Przejdź krok 1 drzewa decyzyjnego. Jeśli RAG nie jest uzasadniony — powiedz to i podaj tańszą
   alternatywę z `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md`. To jest
   właściwa odpowiedź, nie unik.
3. Zbuduj zbiór testowy (50–100 pytań) **przed** kodem.
   `references/engineering-core/04-bazy-i-rag/references/ewaluacja.md`.
4. Zbuduj potok w kolejności z kroku 3. Po każdym etapie zmierz recall@10 na zbiorze testowym.
5. Warstwa generowania dopiero na końcu, gdy recall@10 ≥ 0,85. Generowanie nie naprawi
   wyszukiwania — model nie zacytuje fragmentu, którego nie dostał.
6. Zanim oddasz: przejdź „Kontrolę przed oddaniem”.

### Ścieżka B — „nasz RAG odpowiada źle” (istniejący system)

Rozdziel winę, zanim zaczniesz naprawiać. Kolejność diagnozy jest sztywna:

1. **Czy właściwy fragment w ogóle trafił do modelu?** Weź 20 złych odpowiedzi, ręcznie
   znajdź prawidłowy fragment w korpusie, sprawdź, czy był w kontekście.
   - Nie było → problem wyszukiwania. Idź do punktu 2.
   - Było → problem generowania. Idź do punktu 4.
2. **Czy fragment w ogóle istnieje w indeksie?** Wyszukaj go po dosłownym cytacie
   (`LIKE`/`tsvector`). Jeśli nie ma — problem jest w pozyskaniu lub fragmentacji
   (`references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md`,
   `references/engineering-core/04-bazy-i-rag/references/fragmentacja.md`), nie w embeddingach. To
   najczęstsza przyczyna i najczęściej pomijana.
3. Jest w indeksie, ale nie wychodzi w top-k →
   `references/engineering-core/04-bazy-i-rag/references/wyszukiwanie-hybrydowe.md`. Kolejność
   poprawek według stosunku zysku do kosztu: dołóż BM25 → dołóż reranker → podnieś k pierwszego
   etapu → dopiero potem zmieniaj model embeddingowy.
4. Fragment był, a odpowiedź zła →
   `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md`: kolejność
   fragmentów, wymuszenie przypisu, jawna instrukcja odmowy, weryfikacja dosłowności cytatu.
5. Każdą zmianę zmierz na zbiorze testowym. Zmiana bez pomiaru to nie poprawka.

### Ścieżka C — problem z samym Postgresem (schemat, wolne zapytanie, blokady)

1. Wolne zapytanie: `EXPLAIN (ANALYZE, BUFFERS, SETTINGS)` **przed** dodaniem indeksu.
   Porównaj `rows` szacowane z rzeczywistymi — rozjazd > 10× oznacza problem ze statystykami,
   nie z brakiem indeksu.
2. Zidentyfikuj wzorzec z katalogu błędów w
   `references/engineering-core/04-bazy-i-rag/references/postgres.md` (jest ich kilkanaście i
   pokrywają większość realnych przypadków).
3. Dodaj indeks dopiero gdy wiesz, który predykat jest selektywny. `CREATE INDEX CONCURRENTLY`
   na produkcji, zawsze.
4. Potwierdź, że planer go używa (nie zakładaj), i zmierz ponownie.

### Ścieżka D — konkretne pytanie („jaki wymiar embeddingu”, „HNSW czy IVFFlat”)

Odpowiedz z właściwego pliku, krótko, z liczbą i konsekwencją. Nie rozwijaj do projektu
całego systemu, jeśli nikt o niego nie prosił.

## Twarde reguły

**Postgres**
- Domyślną bazą jest Postgres. Odejście od niej wymaga zapisanego uzasadnienia liczbowego.
- Każde zapytanie wchodzące na produkcję ma sprawdzony plan (`EXPLAIN ANALYZE`), nie
  „powinno być szybkie”. Konsekwencja pominięcia: seq scan na tabeli, która za pół roku
  ma 50 mln wierszy.
- `CREATE INDEX CONCURRENTLY` na tabeli produkcyjnej. Zwykłe `CREATE INDEX` blokuje zapisy
  na cały czas budowy.
- Migracja z `ALTER TABLE ... ADD COLUMN ... DEFAULT` jest bezpieczna od PG11 (bez
  przepisywania tabeli), ale `ALTER COLUMN TYPE` nadal przepisuje całość i blokuje.
- Znak zapytania w aplikacji: parametryzowane zapytania zawsze. Sklejanie SQL-a stringami
  to wstrzyknięcie, nawet gdy „to tylko liczba”.
- Konfiguracja polska do FTS musi być utworzona jawnie (na PG ≤ 18 przez hunspell/ispell,
  na PG 19 przez wbudowany stemmer). Domyślna `english` na polskim tekście gubi odmianę
  i daje ~40% recall.
- `unaccent` przy każdym wyszukiwaniu po nazwiskach i nazwach własnych.

**Wektory**
- Wektory trzymamy w Postgresie, dopóki nie ma zmierzonego powodu, żeby ich tam nie trzymać.
- Wymiar ≤ 2000 przy typie `vector` — powyżej indeks HNSW nie powstanie. Dla 3072
  wymiarów użyj `halfvec` (limit indeksu 4000) albo skróć wymiar (Matryoshka).
- Przy każdym wektorze zapisany identyfikator modelu i jego wersja. Bez tego migracja modelu
  jest niewykonalna, a wynik z dwóch wersji naraz jest po cichu bezsensowny.
- Filtrowanie razem z wyszukiwaniem wektorowym: włącz `hnsw.iterative_scan`, inaczej filtr
  o niskiej selektywności zwróci mniej wyników niż `LIMIT` i nikt tego nie zauważy.
- Nie normalizuj ręcznie, jeśli model już zwraca wektory znormalizowane, i nie mieszaj
  operatorów: `<=>` (cosinus) dla znormalizowanych, `<->` (L2) tylko świadomie.

**RAG**
- Nie ma potoku RAG bez zbioru testowego. Zbiór powstaje pierwszy.
- Wyszukiwanie jest hybrydowe domyślnie. Samo wektorowe przegrywa na sygnaturach
  („II CSK 123/19”), numerach, nazwiskach i cytatach dosłownych — czyli na wszystkim,
  czym żyje korpus prawniczy.
- Każdy fragment przechowuje: identyfikator dokumentu, wersję dokumentu, numer strony
  (lub zakres), pozycję znakową w oryginale, źródło, datę, klucz uprawnień.
  Brak choćby jednego z tych pól = przypisu nie da się zweryfikować.
- Filtr uprawnień stosowany **w bazie, w zapytaniu**, nigdy przez odsiew po pobraniu
  i nigdy przez instrukcję w prompcie. Konsekwencja: wyciek dokumentu do niepowołanej osoby.
- Model dostaje instrukcję odmowy i musi z niej korzystać. Odpowiedź „w dostarczonych
  materiałach nie ma podstawy do odpowiedzi” jest wynikiem poprawnym.
- Cytat dosłowny w odpowiedzi jest weryfikowany programowo względem tekstu źródłowego
  (dopasowanie po normalizacji białych znaków). Niezweryfikowany cytat oznaczamy albo usuwamy.
- Nie podajemy liczbowej poprawy jakości bez pomiaru na zbiorze testowym. „Reranker
  powinien pomóc” nie jest wynikiem.

**Koszty i wersje**
- Przy każdej rekomendacji modelu podajemy cenę za 1 mln tokenów i koszt jednorazowego
  osadzenia całego korpusu. Zmiana modelu = ponowne osadzenie wszystkiego.
- Wersje bibliotek podawane z datą sprawdzenia. Nie zgadujemy numerów wersji.

**Granice modułu**
- Decyzje architektoniczne wyższego rzędu →
  `../architektura-i-dokumentacja/references/engineering-core/przeglad.md`.
- Kod Pythona, SQLAlchemy, Alembic, warstwa dostępu do danych →
  `references/engineering-core/02-python-backend-dane/przeglad.md`.
- Wystawienie wyszukiwarki jako narzędzia MCP →
  `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md`.

## Kontrola przed oddaniem

```
Decyzja
- [ ] Sprawdzone, czy RAG jest w ogóle potrzebny; alternatywa rozważona i odrzucona z podaniem powodu
- [ ] Wybór bazy uzasadniony liczbą (wektorów, QPS, RAM), nie preferencją
- [ ] Nie wprowadzono drugiego systemu przechowywania bez zmierzonego problemu z pierwszym

Postgres
- [ ] Każde zapytanie na ścieżce krytycznej ma plan z EXPLAIN (ANALYZE, BUFFERS)
- [ ] Indeksy powstają przez CREATE INDEX CONCURRENTLY
- [ ] Konfiguracja FTS dla polskiego utworzona jawnie, z unaccent
- [ ] Pula połączeń (pgbouncer) ustawiona, tryb transakcyjny świadomie wybrany
- [ ] Kopia zapasowa ma przetestowane odtworzenie, nie tylko wykonanie

Wektory
- [ ] Wymiar mieści się w limicie indeksu wybranego typu
- [ ] Przy każdym wektorze zapisany model i jego wersja
- [ ] Filtrowanie + wektor przetestowane na filtrze o niskiej selektywności
- [ ] Zmierzony recall indeksu ANN względem wyszukiwania dokładnego (próbka 200 zapytań)

Potok
- [ ] Zbiór testowy istnieje i ma ≥ 50 pytań z oznaczonym prawidłowym źródłem
- [ ] recall@10 zmierzony i zapisany przed etapem generowania
- [ ] Fragment zawiera komplet metadanych: dokument, wersja, strona, offset, uprawnienia
- [ ] Aktualizacja przyrostowa i usuwanie dokumentu przetestowane (nie tylko wstawianie)
- [ ] Skany bez warstwy tekstowej wykryte i skierowane do OCR, nie zaindeksowane jako puste

Odpowiedzi
- [ ] Wyszukiwanie hybrydowe włączone; przetestowane na zapytaniu z sygnaturą i nazwiskiem
- [ ] Przypis wskazuje dokument + stronę i jest klikalny do miejsca w oryginale
- [ ] Cytaty dosłowne weryfikowane programowo względem źródła
- [ ] Odmowa przy braku podstaw działa (przetestowana pytaniem spoza korpusu)
- [ ] Filtr uprawnień działa w zapytaniu do bazy; przetestowany kontem o wąskich prawach

Pomiar
- [ ] Metryki wyszukiwania i generowania policzone przed i po zmianie
- [ ] Koszt na zapytanie policzony (osadzenie + wyszukiwanie + rerank + generowanie)
- [ ] Testy regresyjne uruchamiane przy zmianie modelu, fragmentacji lub promptu
```
