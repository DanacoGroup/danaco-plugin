# Wyszukiwanie hybrydowe

Samo wyszukiwanie wektorowe jest gorszym rozwiązaniem niż wyszukiwanie hybrydowe
w niemal każdym realnym zastosowaniu, a w korpusie prawniczym jest po prostu wadliwe.
Ten plik opisuje, dlaczego i co z tym zrobić.

## Dlaczego samo wektorowe przegrywa

Embedding koduje znaczenie, a nie ciąg znaków. Konsekwencje:

| Zapytanie | Co robi wyszukiwanie wektorowe |
|---|---|
| `II CSK 123/19` | znajduje „jakieś sygnatury”, niekoniecznie tę; wektor sygnatury jest prawie identyczny z wektorem każdej innej sygnatury |
| `art. 415 k.c.` | mieszają się z art. 405, 445, 471 — dla modelu to podobne obiekty |
| `Kowalski-Nowakowa` | nazwisko spoza słownika trafia w okolicę „polskich nazwisk”, nie w konkretne |
| `"opóźnienie w spełnieniu świadczenia pieniężnego"` (cytat dosłowny) | zwraca parafrazy, nie dosłowne wystąpienie |
| `faktura FV/2024/08/1731` | numer jest dla modelu szumem |
| `KRS 0000123456` | jak wyżej |

BM25 (albo `tsvector` z `ts_rank_cd`) robi dokładnie odwrotnie: doskonale trafia w rzadkie
ciągi znaków, a nie rozumie, że „wypowiedzenie umowy” i „rozwiązanie stosunku najmu”
to bliskie sobie pojęcia.

Te dwa mechanizmy zawodzą na rozłącznych zbiorach zapytań. Dlatego działają razem,
a nie zamiast siebie. W korpusie prawniczym udział zapytań zawierających sygnaturę,
numer, datę albo nazwisko jest wysoki — hybryda nie jest tam ulepszeniem, tylko warunkiem
poprawności.

Potwierdzenie liczbowe (Contextual Retrieval, Anthropic): dodanie kontekstowego BM25
do kontekstowych embeddingów zbiło odsetek nietrafionych zapytań z 3,7% do 2,9% —
czyli sam BM25 odpowiadał za jedną piątą całej poprawy.

## Architektura

```
zapytanie
   ├─ (opcjonalnie) przepisanie / rozszerzenie
   ├─→ wektorowo  → top 50   ─┐
   ├─→ BM25/FTS   → top 50   ─┼→ RRF → top 50 → reranker → top 5-10 → model
   └─ filtry metadanych (uprawnienia, data, typ) stosowane w OBU gałęziach
```

Liczby na każdym etapie:

| Etap | Wartość | Dlaczego |
|---|---|---|
| k wektorowe | 50 | poniżej 30 reranker nie ma z czego wybierać |
| k BM25 | 50 | jw. |
| po RRF | 50 | wejście rerankera |
| po reranku | 5–10 | tyle model realnie wykorzystuje; 20 przy Contextual Retrieval |
| `hnsw.ef_search` | ≥ k, praktycznie 100 | inaczej indeks zwraca mniej niż `LIMIT` |

Anthropic mierzył najlepszy wynik przy podawaniu **20** fragmentów po reranku (testowali
5, 10 i 20). Przy dłuższych fragmentach i droższym modelu 5–10 bywa lepszym kompromisem
kosztowym. Zmierz na swoim zbiorze.

## Łączenie wyników

### RRF (Reciprocal Rank Fusion) — domyślne

```
score(d) = Σ  1 / (k + pozycja_d_w_liście_i)      k = 60
```

Zalety: nie wymaga porównywalności wyników (odległość cosinusowa i `ts_rank_cd` są
w zupełnie różnych skalach i nie da się ich sensownie znormalizować), odporny na wartości
odstające, nie ma czego stroić poza `k`.

Stała `k = 60` pochodzi z oryginalnej pracy i jest dobrym domyślnym wyborem. Mniejsze `k`
mocniej faworyzuje pierwsze pozycje; większe wyrównuje wpływ dalszych.

W jednym zapytaniu SQL:

```sql
WITH wekt AS (
  SELECT f.id, row_number() OVER (ORDER BY f.emb <=> $1) AS poz
  FROM fragmenty f
  JOIN dokumenty d ON d.id = f.dokument_id
  WHERE d.kancelaria_id = $3 AND f.obowiazuje_do IS NULL
  ORDER BY f.emb <=> $1
  LIMIT 50
),
pelno AS (
  SELECT f.id, row_number() OVER (ORDER BY ts_rank_cd(f.tsv, q) DESC) AS poz
  FROM fragmenty f
  JOIN dokumenty d ON d.id = f.dokument_id,
       websearch_to_tsquery('public.polski', $2) AS q
  WHERE f.tsv @@ q AND d.kancelaria_id = $3 AND f.obowiazuje_do IS NULL
  ORDER BY ts_rank_cd(f.tsv, q) DESC
  LIMIT 50
)
SELECT f.id, f.tresc, f.dokument_id, f.strona_od,
       coalesce(1.0 / (60 + w.poz), 0) + coalesce(1.0 / (60 + p.poz), 0) AS rrf
FROM fragmenty f
LEFT JOIN wekt  w ON w.id = f.id
LEFT JOIN pelno p ON p.id = f.id
WHERE w.id IS NOT NULL OR p.id IS NOT NULL
ORDER BY rrf DESC
LIMIT 50;
```

Zwróć uwagę: filtr `kancelaria_id` jest w **obu** podzapytaniach. Filtr zastosowany tylko na końcu
jest równoważny post-filteringowi i cicho gubi wyniki. Do gałęzi wektorowej potrzebny jest jeszcze
`hnsw.iterative_scan` (patrz `references/engineering-core/04-bazy-i-rag/references/pgvector.md`).

### Ważona suma

```
score = α · norm(podobieństwo_wektorowe) + (1-α) · norm(bm25)
```

Wymaga normalizacji obu wyników do wspólnej skali (min-max po zbiorze wyników albo
z-score). Wrażliwa na wartości odstające, wymaga strojenia `α` per korpus.
Bierz ją tylko, gdy: (a) masz zbiór testowy do strojenia `α`, (b) chcesz sterować wagą
zależnie od zapytania (np. `α = 0,3`, gdy w zapytaniu wykryto sygnaturę; `α = 0,8`
przy pytaniu opisowym). Poza tym RRF jest prostszy i wystarczający.

## Przepisywanie i rozszerzanie zapytania

| Technika | Na czym polega | Zysk | Koszt |
|---|---|---|---|
| Rozwinięcie skrótów | `k.c.` → „kodeks cywilny”, `KPC` → „kodeks postępowania cywilnego” | duży w polskim korpusie prawniczym | słownik, zero opóźnienia |
| Normalizacja sygnatur | `IICSK123/19` → `II CSK 123/19` i odwrotnie, oba warianty do zapytania BM25 | duży | wyrażenie regularne |
| Rozbicie pytania złożonego | „czy X i jakie są skutki Y” → dwa zapytania | duży przy pytaniach wielowątkowych | jedno wywołanie LLM |
| Przepisanie kontekstowe | „a co z jego terminem?” → „jaki jest termin przedawnienia roszczenia z art. 118 k.c.” | **niezbędne w rozmowie wieloturowej** | jedno wywołanie LLM (~200 ms) |
| Rozszerzenie o synonimy | dopisanie terminów bliskoznacznych do gałęzi BM25 | umiarkowany | słownik dziedzinowy albo LLM |
| HyDE | LLM pisze hipotetyczną odpowiedź, tę odpowiedź osadzasz zamiast pytania | zmienny | wywołanie LLM + ryzyko dryfu |

Przepisanie kontekstowe w rozmowie jest obowiązkowe, nie opcjonalne. Bez niego drugie
pytanie użytkownika („a jeśli minęły trzy lata?”) jest osadzane jako samodzielny tekst
i nie znajduje niczego sensownego.

```python
PRZEPISZ = """Historia rozmowy:
{historia}

Ostatnie pytanie użytkownika: {pytanie}

Przepisz je jako samodzielne zapytanie wyszukiwania, rozwijając zaimki i odwołania
do wcześniejszych tur. Zachowaj wszystkie sygnatury, numery i nazwy własne dosłownie.
Zwróć wyłącznie przepisane zapytanie."""
```

Instrukcja „zachowaj sygnatury dosłownie” jest istotna — model chętnie „poprawia”
numery i sygnatury, co niszczy gałąź BM25.

### HyDE — ostrożnie

Pomysł: pytanie i dokument to różne rodzaje tekstu, więc zamiast osadzać pytanie,
niech LLM napisze prawdopodobną odpowiedź i osadź ją. Wektor odpowiedzi jest bliżej
wektorów fragmentów niż wektor pytania.

Działa na korpusach ogólnych. W dziedzinie specjalistycznej model zmyśla treść
o powierzchownie prawidłowym brzmieniu i **oddala** zapytanie od właściwego fragmentu.
W prawie polskim model potrafi wygenerować hipotetyczną odpowiedź z nieistniejącym
przepisem — i wtedy szukasz czegoś, czego nie ma.

Jeśli mimo to stosujesz: łącz wektor HyDE z wektorem oryginalnego pytania (średnia
albo dwie osobne gałęzie w RRF), nigdy nie zastępuj. I zmierz — HyDE bywa regresją.

## Filtry metadanych

Filtry, które w korpusie dokumentowym są potrzebne prawie zawsze:

| Filtr | Powód |
|---|---|
| uprawnienia (kancelaria, sprawa, rola) | bezpieczeństwo; **nigdy po pobraniu** |
| aktualna wersja dokumentu | inaczej odpowiadasz z nieaktualnej treści |
| zakres dat | „co obowiązywało w marcu 2024” |
| typ dokumentu | „tylko wyroki”, „tylko umowy” |
| język | gdy trzeba ograniczyć do polskich źródeł |

Zasady:
- Filtr aplikowany w bazie, wewnątrz obu gałęzi wyszukiwania.
- Filtr niskoselektywny wymaga `hnsw.iterative_scan` — inaczej dostajesz mniej wyników
  niż `LIMIT`, bez żadnego błędu.
- Filtr bardzo selektywny (< ~1000 wierszy) — wyłącz indeks ANN, przeszukanie dokładne
  jest szybsze i bezbłędne.
- Filtry wywnioskowane z zapytania przez LLM (np. wykrycie daty w pytaniu) traktuj jako
  podpowiedź, nie jako twardy warunek. Model wykrywający „2024” w pytaniu o coś innego
  wytnie właściwą odpowiedź.

## Reranking

Reranker to model, który dostaje parę (zapytanie, fragment) i ocenia trafność, patrząc
na oba naraz. Cross-encoder widzi interakcję słów, czego bi-encoder (embedding) z zasady
nie może — dlatego jest wyraźnie dokładniejszy i nieporównanie wolniejszy. Stąd użycie
wyłącznie do przeszeregowania kandydatów, nigdy do przeszukiwania korpusu.

### Ile to daje

Jedyna dobrze udokumentowana liczba na realnym potoku: w badaniu Contextual Retrieval
dodanie rerankingu do hybrydy z kontekstualizacją zbiło odsetek zapytań bez trafnego
fragmentu w top-20 z **2,9% do 1,9%** — czyli o jedną trzecią tego, co jeszcze zostało.
W typowych potokach bez kontekstualizacji zysk jest większy (rzędu kilku–kilkunastu
punktów nDCG@10), bo jest więcej do naprawienia.

Reranker dziedzinowy dokłada jeszcze trochę: warianty Voyage dla prawa i kodu dają
ok. **+2–4 nDCG@10** względem rerankera ogólnego na odpowiadającym im korpusie
(pomiar Voyage, maj 2026).

### Modele

| Model | Typ | Kontekst | Cena / opóźnienie |
|---|---|---|---|
| `rerank-v4.0-pro` (Cohere) | API | 32k | wg cennika; ~600 ms na wywołanie z siecią |
| `rerank-v4.0-fast` (Cohere) | API | 32k | tańszy, szybszy |
| `rerank-2.5` (Voyage) | API | 32k | **0,05 USD / 1 mln tokenów** |
| `rerank-2.5-lite` (Voyage) | API | 32k | **0,02 USD / 1 mln tokenów** |
| `jina-reranker-v3` / `v3.5` | własny hosting (0,6 mld par.) | — | ~190 ms na partię przy własnym GPU |
| `bge-reranker-v2-m3` | własny hosting | 8k | wielojęzyczny, sprawdzony, darmowy |

Do polskiego korpusu: `bge-reranker-v2-m3` (własny hosting) albo `rerank-v4.0-pro`
(wielojęzyczny). `[niepotwierdzone: publiczne wyniki rerankerów na polskim korpusie
prawniczym — brak benchmarku; zmierz na własnym zbiorze]`

### Koszt

Reranking 50 fragmentów po 600 tokenów to ok. 30 tys. tokenów na zapytanie.

| Model | Koszt 1 zapytania | 100 tys. zapytań |
|---|---|---|
| `rerank-2.5-lite` (0,02/M) | 0,0006 USD | 60 USD |
| `rerank-2.5` (0,05/M) | 0,0015 USD | 150 USD |
| własny hosting na GPU | koszt maszyny | maszyna T4/L4 obsłuży to bez problemu |

To jest tanie względem kosztu generowania odpowiedzi. Główny koszt rerankera to
**opóźnienie**: 200–600 ms dodane do każdego zapytania. Przy interfejsie czatowym
mieści się w akceptowalnym budżecie, przy autouzupełnianiu — nie.

### Kiedy nie stosować rerankera

- Gdy pierwszy etap ma recall@50 poniżej ~0,8. Reranker nie znajdzie fragmentu, którego
  mu nie podano. Najpierw napraw wyszukiwanie.
- Gdy budżet opóźnienia jest poniżej 300 ms.
- Gdy podajesz modelowi 20+ fragmentów i tak — przy dużym k zysk z przeszeregowania
  maleje, bo właściwy fragment i tak jest w kontekście.

## Kolejność napraw przy niskiej trafności

Sprawdzona kolejność według stosunku zysku do nakładu. Nie przeskakuj do końca listy.

```
1. Czy fragment w ogóle jest w indeksie i jest czytelny?  → potok-dokumentow.md
2. Czy filtr nie wycina wyników po cichu (iterative_scan)? → pgvector.md
3. Dołóż BM25 / tsvector, jeśli jest tylko wektorowe.
4. Dołóż reranker.
5. Podnieś k pierwszego etapu (50 → 100) i ef_search.
6. Dołóż kontekstualizację fragmentów.                    → fragmentacja.md
7. Przepisywanie zapytania (obowiązkowe w rozmowie).
8. Zmień model embeddingowy.                              → embeddingi.md
9. Zmień strategię fragmentacji.                          → fragmentacja.md
```

Punkty 8 i 9 wymagają ponownego osadzenia całego korpusu i są najdroższe, a rzadko dają
najwięcej. Typowy błąd zespołu: zaczyna od punktu 8.

## Diagnostyka: która gałąź zawodzi

Dla każdego pytania ze zbioru testowego policz pozycję prawidłowego fragmentu osobno
w gałęzi wektorowej, osobno w BM25, i po połączeniu.

```python
def diagnoza(pytania, szukaj_wekt, szukaj_bm25, szukaj_hybryda):
    stat = {"tylko_wekt": 0, "tylko_bm25": 0, "oba": 0, "zadne": 0}
    for p in pytania:
        w = p["zloty_id"] in [x["id"] for x in szukaj_wekt(p["pytanie"], k=20)]
        b = p["zloty_id"] in [x["id"] for x in szukaj_bm25(p["pytanie"], k=20)]
        stat["oba" if w and b else "tylko_wekt" if w else "tylko_bm25" if b else "zadne"] += 1
    return stat
```

Interpretacja:

| Wynik | Co oznacza |
|---|---|
| wysokie `tylko_bm25` | model embeddingowy słabo radzi sobie z językiem lub dziedziną → zmień model |
| wysokie `tylko_wekt` | konfiguracja FTS jest zła (brak polskiego słownika, brak `unaccent`) |
| wysokie `zadne` | problem jest przed wyszukiwaniem: parsowanie albo fragmentacja |
| `oba` blisko 100%, a odpowiedzi wciąż złe | problem jest w generowaniu → `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md` |

Ta jedna tabelka rozstrzyga więcej niż tydzień strojenia na wyczucie.
