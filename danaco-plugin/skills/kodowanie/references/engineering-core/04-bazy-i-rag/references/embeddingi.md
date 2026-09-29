# Embeddingi

Wektor liczb, w którym bliskość odpowiada podobieństwu znaczenia — na tyle, na ile model
nauczył się, co to znaczy „podobne”. To nie jest reprezentacja prawdy o tekście, tylko
reprezentacja tego, co model uznał za istotne przy trenowaniu. Dlatego model trenowany
na angielskich stronach WWW nie oddaje różnicy między „odstąpienie” a „wypowiedzenie”.

Ceny, wymiary i wersje sprawdzone 04.08.2026.

## Aktualne modele

### Chmura

| Model | Wymiary | Maks. wejście | Cena / 1 mln tok. | Uwagi |
|---|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | 1536 (Matryoshka) | 8191 | 0,02 USD | najtańszy sensowny; słabszy po polsku |
| `text-embedding-3-large` (OpenAI) | 3072 (Matryoshka) | 8191 | 0,13 USD | 3072 wymiary **nie zmieszczą się** w indeksie `vector` (limit 2000) |
| `voyage-4-lite` | 256/512/1024/2048 | 32 000 | 0,02 USD | |
| `voyage-4` | 256/512/1024/2048 | 32 000 | 0,06 USD | dobry stosunek jakości do ceny |
| `voyage-4-large` | 256/512/1024/2048 | 32 000 | 0,12 USD | |
| `voyage-3.5` | 256/512/1024/2048 | 32 000 | 0,06 USD | nadal dostępny, sprawdzony |
| `voyage-context-4` | 256/512/1024/2048 | **120 000** | 0,12 USD | osadza fragment ze świadomością całego dokumentu |
| **`voyage-law-2`** | 1024 | 16 000 | 0,12 USD | trenowany na korpusie prawniczym |
| `embed-v4.0` (Cohere) | 256/512/1024/1536 | **128 000** | `[niepotwierdzone: cena za 1 mln tokenów — cennik Cohere podaje obecnie tylko wdrożenia dedykowane]` | wielojęzyczny, obsługuje też obrazy |
| `jina-embeddings-v5-text-small` | 1024 | 32 000 | wg cennika Jina | 677 mln parametrów, dostępny też do hostingu |

Uwaga o OpenAI: **na sierpień 2026 nadal nie ma następcy `text-embedding-3`**.
Modele z początku 2024 są wciąż aktualną ofertą. Nie zakładaj, że pojawił się nowy.

Uwaga o `voyage-law-2`: to jedyny szeroko dostępny model komercyjny trenowany specjalnie
pod teksty prawnicze. Jest anglocentryczny — na polskim korpusie **zweryfikuj go na własnym
zbiorze testowym przed wyborem**, bo specjalizacja dziedzinowa nie musi przenosić się
przez język.

### Do hostingu własnego

| Model | Parametry | Wymiary | Maks. wejście | Języki | Uwagi |
|---|---|---|---|---|---|
| `Qwen3-Embedding-0.6B` | 0,6 mld | 32–1024 (elastyczne) | długie | 100+ | najlepszy stosunek jakości do rozmiaru |
| `Qwen3-Embedding-4B` / `-8B` | 4 / 8 mld | do 4096 | długie | 100+ | **najlepsze wyniki na PL-MTEB** |
| `EmbeddingGemma-300M` | 300 mln | 768 (MRL do 128) | 2048 | 100+ | działa na CPU, dobre do wdrożeń brzegowych |
| `BGE-M3` | ~570 mln | 1024 | **8192** | 100+ | zwraca naraz gęsty, rzadki i wielowektorowy — hybryda z jednego modelu |
| `gte-multilingual-base` | 305 mln | elastyczne | długie | 70+ | lekki, szybki |
| `Nomic Embed Text V2` | 475 mln (305 mln aktywnych, MoE) | 768 (do 256) | 512 | ~100 | krótkie wejście ogranicza użycie |
| `jina-embeddings-v5-text-nano` | 239 mln | 768 | 8000 | wielojęzyczny | |
| `stella-pl-retrieval-8k` | — | — | 8000 | PL/EN | **najlepszy wynik wyszukiwania na PL-MTEB** |
| `mmlw-roberta-*` | 124 mln – 1,4 mld | — | 512 | PL/EN | polski, destylacja dwujęzyczna |
| `silver-retriever` | — | — | 512 | PL | polski, trenowany na MAUPQA |

Licencje: sprawdź przed produkcją. `jina-embeddings-v4` jest na CC-BY-NC-4.0 (zakaz użycia
komercyjnego bez licencji) — to wyklucza go z produktu klienta. Rodzina Qwen3-Embedding i BGE są na
licencjach dopuszczających użycie komercyjne `[niepotwierdzone: dokładny wariant licencji
Qwen3-Embedding na sierpień 2026 — sprawdź kartę modelu]`.

## Jakość dla polszczyzny

PL-MTEB (Polish Massive Text Embedding Benchmark, wersja ACL 2026) — wyniki, na których
warto opierać decyzję zamiast na ogólnym MTEB:

| Model | Wynik ogólny | Wyszukiwanie |
|---|---|---|
| `Qwen3-Embedding-8B` | **70,47** | — |
| `Qwen3-Embedding-4B` | 69,37 | — |
| `stella-pl-retrieval-8k` | — | **61,59** |
| `stella-pl` | — | 60,82 |

Cztery wnioski praktyczne:

1. **Model najlepszy ogólnie i model najlepszy do wyszukiwania to nie ten sam model.**
   Do RAG interesuje cię wyłącznie kolumna „wyszukiwanie”.
2. Duże modele wielojęzyczne (Qwen3) biją małe modele polskie na zadaniach ogólnych,
   ale wyspecjalizowane modele dwujęzyczne PL/EN (stella-pl) wygrywają na wyszukiwaniu.
3. `mmlw-roberta-base` (124 mln parametrów) wyprzedza modele z wyższej kategorii
   rozmiarowej — mały model dobrze dopasowany do języka bije duży model ogólny.
4. Modele wyłącznie angielskie (`text-embedding-3-small`, `embed-english-v3.0`)
   są dla polskiego korpusu wykluczone. Nie chodzi o gorsze wyniki, tylko o to,
   że polskie i angielskie odpowiedniki lądują w rozłącznych obszarach przestrzeni.

**Zawsze zweryfikuj na własnym korpusie.** Benchmark ogólny na Wikipedii nie przewiduje
zachowania na uzasadnieniach wyroków. 100 pytań testowych i pomiar recall@10 kosztuje
pół dnia i rozstrzyga więcej niż każdy ranking.

## Dobór modelu — kolejność pytań

```
1. Czy korpus i zapytania są po polsku?
   → tak: tylko modele wielojęzyczne albo PL. To wyklucza połowę listy.

2. Czy dane mogą opuścić infrastrukturę?
   → nie: hosting własny. Qwen3-Embedding-0.6B na jednym GPU obsłuży
     miliony fragmentów; EmbeddingGemma-300M zadziała nawet na CPU.
   → tak: API. Sprawdź podstawę transferu i umowę powierzenia.

3. Jak długie są fragmenty?
   → do 512 tokenów: wystarczy każdy model
   → do 8000: BGE-M3, jina, modele OpenAI
   → dłuższe albo kontekstualizacja: voyage-context-4 (120k), embed-v4.0 (128k)

4. Ile fragmentów?
   → < 1 mln: wymiar 1024 bez zastanowienia
   → > 5 mln: policz pamięć. 1024 wym. × 4 B × 5 mln = 20 GB samych wektorów.
     Rozważ 512 wym. (Matryoshka) albo halfvec.

5. Jaki budżet?
   → policz: (tokeny korpusu / 1 mln) × cena. Potem pomnóż przez 2-3,
     bo będziesz osadzać ponownie przy zmianie fragmentacji.
```

## Wymiar

| Wymiar | Pamięć na 1 mln wektorów (float32) | Kiedy |
|---|---|---|
| 256 | 1,0 GB | ogromne korpusy, wstępne przesiewanie |
| 512 | 2,0 GB | dobry kompromis przy > 5 mln fragmentów |
| **1024** | 4,1 GB | **domyślny** |
| 1536 | 6,1 GB | gdy pomiar pokazuje realny zysk |
| 3072 | 12,3 GB | wymaga `halfvec` w pgvector (limit indeksu `vector` to 2000) |

Zysk z podwojenia wymiaru jest zwykle rzędu 1–2 pp recall. Koszt pamięci i czasu
wyszukiwania jest dwukrotny. Przy korpusie powyżej miliona fragmentów to zwykle zły
interes — pieniądze lepiej wydać na reranker.

### Matryoshka

Modele trenowane techniką Matryoshka Representation Learning układają informację
tak, że **pierwsze N wymiarów jest samodzielnie użyteczne**. Można obciąć wektor
bez ponownego osadzania i stracić bardzo mało.

Mają to: `text-embedding-3-*` (parametr `dimensions`), rodzina Voyage
(256/512/1024/2048), Cohere `embed-v4.0` (256/512/1024/1536), EmbeddingGemma (768→128),
Qwen3-Embedding (32–1024).

```python
# obcięcie po stronie klienta wymaga PONOWNEJ normalizacji
import numpy as np
def obetnij(v: np.ndarray, d: int) -> np.ndarray:
    v = v[:d]
    return v / np.linalg.norm(v)
```

Zastosowanie wzorcowe — dwuetapowe wyszukiwanie: indeks na 256 wymiarach przesiewa
top-500 (mały indeks, mieści się w RAM), pełne 1024 wymiary ze składowanego wektora
szeregują top-50. Efekt zbliżony do kwantyzacji binarnej z ponownym rankingiem.

Pułapka: obcięcie działa tylko dla modeli trenowanych pod MRL. Obcięcie zwykłego
embeddingu daje wektor, który wygląda poprawnie i szereguje przypadkowo.

## Normalizacja

Większość nowoczesnych modeli zwraca wektory o normie 1. Sprawdź, nie zakładaj:

```python
import numpy as np
print(np.linalg.norm(wektor))   # ~1.0 → znormalizowany
```

Konsekwencje:
- Znormalizowane: `<=>` (cosinus), `<->` (L2) i `<#>` (iloczyn) dają ten sam ranking.
  `<#>` jest najszybszy, `<=>` najbardziej jednoznaczny.
- Nieznormalizowane: `<->` będzie mierzył także długość wektora, czyli częściowo długość
  tekstu. Ranking wyjdzie zniekształcony. Normalizuj przed zapisem.

**Nigdy nie mieszaj w jednej kolumnie wektorów znormalizowanych i nie.** Objaw:
najkrótsze fragmenty systematycznie wypadają wysoko albo nisko, niezależnie od treści.

## Asymetria zapytania i dokumentu

Zapytanie („czy można wypowiedzieć umowę bez zachowania terminu”) i dokument
(fragment kodeksu) nie są tym samym rodzajem tekstu. Modele trenowane pod wyszukiwanie
mają dla nich osobne tryby.

```python
# Voyage
voyage.embed(teksty, model="voyage-3.5", input_type="document")   # przy indeksacji
voyage.embed([pytanie], model="voyage-3.5", input_type="query")   # przy wyszukiwaniu

# Cohere
co.embed(texts=..., input_type="search_document")
co.embed(texts=..., input_type="search_query")

# E5 / BGE / Qwen3 — prefiksy tekstowe
"passage: " + fragment
"query: " + pytanie
```

Pominięcie tego rozróżnienia kosztuje kilka punktów recall i jest błędem, którego nie widać
— wyniki są „w miarę sensowne”, po prostu gorsze. Modele OpenAI nie mają trybów;
tam pytanie nie powstaje.

Zapisz w kodzie, którego trybu użyto przy indeksacji, i użyj tego samego przy każdym
ponownym osadzaniu. Korpus osadzony częściowo jako `document`, częściowo jako `query`
jest niespójny i objawia się losowo.

## Osadzanie wsadowe

```python
import time, itertools

def wsadami(iterable, n):
    it = iter(iterable)
    while (partia := list(itertools.islice(it, n))):
        yield partia

def osadz_korpus(fragmenty, klient, model, rozmiar=128):
    wynik = []
    for partia in wsadami(fragmenty, rozmiar):
        for proba in range(5):
            try:
                odp = klient.embed(
                    [f["tresc"] for f in partia],
                    model=model, input_type="document",
                )
                wynik.extend(odp.embeddings)
                break
            except RateLimitError:
                time.sleep(2 ** proba)
        else:
            raise RuntimeError("nie udało się po 5 próbach")
    return wynik
```

Zasady:
- Rozmiar partii dobierz do **limitu tokenów na żądanie**, nie do liczby tekstów.
  128 fragmentów po 600 tokenów to 77 tys. tokenów — sprawdź, czy dostawca to przyjmie.
- Wykładnicze wycofanie przy 429. Bez tego przy 100 tys. fragmentów zadanie padnie w połowie.
- **Zapisuj wektory do bazy na bieżąco, partia po partii, z commitem.** Trzymanie 500 tys.
  wektorów w pamięci do końca przetwarzania to gwarantowana strata wielogodzinnej pracy.
- Wznawianie: zadanie musi umieć ruszyć od miejsca, w którym padło
  (`WHERE emb IS NULL`).
- API wsadowe (batch) tam, gdzie jest: Voyage daje **33% zniżki** na Batch API
  (bez naliczania darmowej puli). OpenAI ma Batch API z 50% zniżką przy oknie 24 h.
  Przy pierwszym osadzeniu dużego korpusu to realne oszczędności.
- Darmowe pule: Voyage 200 mln tokenów na większość modeli, 50 mln na specjalistyczne
  (w tym `voyage-law-2`). Do prototypu wystarczy.

Przy hostingu własnym: `sentence-transformers` 5.6.1, wsad 32–256 zależnie od VRAM,
`fp16`, sortowanie tekstów po długości przed wsadem (zmniejsza dopełnianie i przyspiesza
o kilkadziesiąt procent).

## Wersjonowanie modelu i koszt ponownego osadzenia

**Wektory z dwóch różnych modeli są nieporównywalne.** Nie ma migracji częściowej,
nie ma „nowe dokumenty nowym modelem”. Zmiana modelu = ponowne osadzenie całego korpusu.

Dlatego przy każdym wektorze zapisany `model_emb` i `wymiar` (patrz
`references/engineering-core/04-bazy-i-rag/references/pgvector.md`).

Koszt jednorazowego osadzenia korpusu:

| Korpus | Tokenów (ok.) | `voyage-4-lite` (0,02) | `voyage-4` (0,06) | `text-embedding-3-large` (0,13) |
|---|---|---|---|---|
| 10 tys. stron | 5 mln | 0,10 USD | 0,30 USD | 0,65 USD |
| 1 mln stron | 500 mln | 10 USD | 30 USD | 65 USD |
| 10 mln stron | 5 mld | 100 USD | 300 USD | 650 USD |

(Założenie: ok. 500 tokenów na stronę A4 tekstu prawniczego.)

Wniosek, który zaskakuje klientów: **osadzenie jest tanie**. Nawet 10 mln stron to setki
dolarów jednorazowo. Drogie są: parsowanie z OCR, generowanie odpowiedzi i czas inżyniera.
Nie projektuj systemu wokół oszczędzania na embeddingach.

Wniosek dla decyzji: skoro ponowne osadzenie kosztuje setki dolarów i kilka godzin,
**nie warto długo dobierać modelu w teorii**. Osadź korpus dwoma kandydatami, zmierz
recall@10, wybierz. To jest tańsze niż tydzień dyskusji.

### Procedura migracji modelu bez przestoju

```sql
ALTER TABLE fragmenty ADD COLUMN emb_nowy vector(1024);
-- osadzaj partiami w tle:  WHERE emb_nowy IS NULL LIMIT 1000
-- gdy gotowe:
CREATE INDEX CONCURRENTLY idx_fr_emb_nowy ON fragmenty
  USING hnsw (emb_nowy vector_cosine_ops);
-- porównaj recall@10 obu indeksów na zbiorze testowym
BEGIN;
ALTER TABLE fragmenty DROP COLUMN emb;
ALTER TABLE fragmenty RENAME COLUMN emb_nowy TO emb;
UPDATE fragmenty SET model_emb = 'nowy-model';
COMMIT;
```

Nigdy nie usuwaj starego indeksu przed porównaniem wyników. Nowszy model bywa gorszy
na konkretnym korpusie — to zdarza się częściej, niż sugerują karty modeli.

## Antywzorce

| Antywzorzec | Konsekwencja |
|---|---|
| Model wyłącznie angielski na polskim korpusie | polskie zapytanie nie znajduje polskich dokumentów o tej samej treści |
| `text-embedding-3-large` (3072) w kolumnie `vector` | indeks HNSW nie powstanie — limit 2000 wymiarów |
| Brak `input_type` / prefiksu przy modelach asymetrycznych | kilka punktów recall stracone bez żadnego objawu |
| Mieszanie modeli w jednej kolumnie | ranking pozornie sensowny, faktycznie losowy |
| Obcięcie wymiaru modelu bez MRL | wektor wygląda poprawnie, szereguje przypadkowo |
| Brak ponownej normalizacji po obcięciu | zniekształcony ranking przy metryce L2 |
| Osadzanie fragmentów pojedynczo (jedno żądanie na fragment) | 100× wolniej i wielokrotnie drożej w limitach |
| Trzymanie wszystkich wektorów w pamięci do końca zadania | utrata wielogodzinnej pracy przy jednym wyjątku |
| Wybór modelu na podstawie ogólnego MTEB bez pomiaru na własnym korpusie | model najlepszy „ogólnie” bywa gorszy na konkretnej dziedzinie |
| Wysyłanie akt klienta do API bez umowy powierzenia | naruszenie RODO i tajemnicy zawodowej |
