# Dedykowane bazy wektorowe

Ten plik otwierasz dopiero wtedy, gdy pgvector został zmierzony i nie wystarcza (progi eskalacji w
`references/engineering-core/04-bazy-i-rag/references/pgvector.md`). Domyślną odpowiedzią na „jaką
bazę wektorową” jest „żadną, użyj Postgresa”.

Ceny i wersje sprawdzone 04.08.2026. Cenniki zmieniają się co kilka miesięcy —
**przy realnej ofercie sprawdź je ponownie**, nie cytuj tej tabeli jako wiążącej.

## Przegląd

| System | Model wdrożenia | Silnik / indeks | Mocna strona | Słaba strona |
|---|---|---|---|---|
| **pgvector** | rozszerzenie Postgresa | HNSW, IVFFlat | spójność transakcyjna z danymi, jeden system, zero dodatkowej infrastruktury | RAM na indeks, brak shardingu, wolniejsza budowa |
| **Qdrant** 1.19 | OSS (Apache 2.0), Cloud, Hybrid, Private | HNSW w Rust, kwantyzacja skalarna/binarna/TurboQuant | najlepsze filtrowanie i wielodostępność, dobry stosunek jakości do kosztu, tryb na dysku | osobny system do utrzymania i backupu |
| **Weaviate** | OSS, Cloud | HNSW + BM25 natywnie | hybryda w jednym zapytaniu, wbudowane moduły wektoryzacji | zasobożerne, cennik złożony (za wymiary) |
| **Milvus / Zilliz** 3.0 | OSS, Zilliz Cloud | wiele indeksów, GPU, tabele zewnętrzne (Parquet/Lance/Iceberg) | skala 100 mld+, sharding, indeksy rzadkie (SINDI, Block-Max WAND) | najbardziej złożony operacyjnie z całej listy |
| **Chroma** | osadzona lub serwer, Cloud | HNSW | najniższy próg wejścia, świetna do prototypu | ograniczenia przy produkcji i wielu użytkownikach |
| **LanceDB** | osadzona, na S3/GCS, Cloud | format kolumnowy Lance, IVF-PQ, HNSW | bezserwerowa nad magazynem obiektowym, multimodalna, wersjonowanie danych | młodszy ekosystem zarządzany |
| **Turbopuffer** | tylko usługa | indeks na magazynie obiektowym z warstwą cache | koszt idzie za ruchem, nie za RAM; setki tysięcy małych przestrzeni | brak wersji do samodzielnego hostingu, opóźnienie zimnego startu |
| **Vespa** | OSS, Cloud | HNSW + tensory + ranking wielofazowy | najbogatszy język rankingu, ranking ML w silniku | najostrzejsza krzywa uczenia |
| **Elasticsearch / OpenSearch** | OSS/licencja, Cloud | Lucene HNSW, BBQ (ES 9), FAISS (OpenSearch) | masz to już wdrożone, BM25 klasy produkcyjnej, agregacje | wektory to funkcja dołożona, nie rdzeń |
| **Pinecone** | tylko usługa | zamknięty, bezserwerowy | zero utrzymania | zamknięcie u dostawcy, koszt trudny do przewidzenia przy skali |

## Model danych i metadane

Wszystkie te systemy mają ten sam kształt rekordu: `id` + wektor(y) + ładunek metadanych
(JSON-podobny) + opcjonalnie tekst. Różnice, które realnie bolą:

| Cecha | Qdrant | Weaviate | Milvus | Chroma | LanceDB | Turbopuffer | Elastic |
|---|---|---|---|---|---|---|---|
| Wiele wektorów nazwanych na rekord | tak | tak | tak | nie | tak | tak | tak (wiele pól) |
| Wektory rzadkie (BM25/SPLADE jako wektor) | tak | tak | tak (SINDI) | nie | ograniczone | tak | tak (`sparse_vector`) |
| Filtrowanie z indeksem na ładunku | tak, bogate | tak | tak | proste | tak (predykaty SQL) | tak | tak |
| Schemat wymuszony | opcjonalny | tak | tak | nie | tak | luźny | tak (mapping) |
| Aktualizacja pojedynczego pola metadanych bez ponownego zapisu wektora | tak | tak | tak | nie | tak | tak | tak |

Ostatni wiersz jest ważniejszy, niż wygląda: w systemie prawniczym uprawnienia zmieniają
się częściej niż treść. Jeśli zmiana ACL wymusza ponowny zapis wektora, każda zmiana
dostępu do sprawy to ponowny zapis tysięcy rekordów.

## Filtrowanie: pre vs post

Trzy strategie, które silniki stosują:

1. **Post-filtering** — pobierz `k` z indeksu, odrzuć niepasujące. Cichy błąd przy
   selektywnym filtrze (zwrócisz mniej niż `k`). Naiwny pgvector bez `iterative_scan`
   i część prostszych bibliotek.
2. **Pre-filtering z listą dozwolonych** — wyznacz zbiór id spełniających filtr, przeszukuj
   graf tylko w nim. Poprawne, ale przy dużym zbiorze kosztowne.
3. **Filtrowalne przechodzenie grafu** — filtr sprawdzany w trakcie chodzenia po HNSW,
   z automatycznym przełączeniem na skan pełny, gdy filtr jest bardzo selektywny.
   To robi Qdrant (dlatego jest wskazywany przy złożonych filtrach) i, w innej formie,
   Milvus.

Pytanie kontrolne do każdego dostawcy: **„co się dzieje, gdy filtr przepuszcza 0,1%
kolekcji — dostanę pełne k wyników?”** Jeśli odpowiedź brzmi „to zależy”, masz post-filtering.

Filtry wymagają własnych indeksów na polach ładunku. Bez nich silnik iteruje po ładunkach
liniowo i filtrowanie staje się wolniejsze od samego wyszukiwania wektorowego:

```python
# Qdrant: indeks na polu ładunku jest obowiązkowy dla często filtrowanych pól
klient.create_payload_index(
    collection_name="fragmenty",
    field_name="kancelaria_id",
    field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True),
)
klient.create_payload_index(
    collection_name="fragmenty",
    field_name="data_dokumentu",
    field_schema="datetime",
)
```

`is_tenant=True` mówi silnikowi, żeby fizycznie grupował dane po tym polu — to jest
różnica między „filtrowanie działa” a „filtrowanie jest szybkie przy 500 najemcach”.

## Przechowywanie: pamięć czy dysk

Rozstrzygnięcie, które decyduje o rachunku bardziej niż wybór dostawcy.

| Tryb | Gdzie graf, gdzie wektory | Opóźnienie | Koszt |
|---|---|---|---|
| Wszystko w RAM | oba w pamięci | najniższe (jednostki ms) | najwyższy |
| Wektory na dysku, graf w RAM | mmap wektorów | +kilka ms na NVMe | średni |
| Wszystko na dysku / obiektach | graf i wektory czytane leniwie | dziesiątki–setki ms, zimny start sekundy | najniższy |

Kto co oferuje: Qdrant ma `on_disk` osobno dla wektorów, ładunku i indeksu HNSW;
Milvus rozdziela przechowywanie od obliczeń z danymi w S3/MinIO; LanceDB i Turbopuffer
są z założenia nad magazynem obiektowym; pgvector trzyma indeks w `shared_buffers`
i cache systemu, a pgvectorscale/VectorChord dokładają wariant dyskowy.

Reguła: przy korpusie dokumentowym odpytywanym kilkanaście razy na minutę tryb dyskowy
z kwantyzacją w RAM daje opóźnienie w pełni akceptowalne przy kilkukrotnie niższym koszcie.
Tryb „wszystko w RAM” ma sens przy setkach zapytań na sekundę, a nie przy kancelarii.

```python
# Qdrant: wektory na dysku, skwantyzowane kopie w RAM do przesiewania
klient.create_collection(
    collection_name="fragmenty",
    vectors_config=models.VectorParams(
        size=1024, distance=models.Distance.COSINE, on_disk=True,
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8, always_ram=True,
        )
    ),
    hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100, on_disk=False),
)
```

## Kwantyzacja w bazach dedykowanych

| Metoda | Kompresja | Strata jakości | Gdzie |
|---|---|---|---|
| Skalarna int8 | 4× | mała, zwykle < 1 pp | Qdrant, Milvus, Weaviate |
| Binarna (1 bit) | 32× | duża bez ponownego rankingu | wszędzie; w pgvector `binary_quantize` |
| Produktowa (PQ) | 4–64× | zmienna, wymaga trenowania | Milvus, FAISS, OpenSearch |
| BBQ (Better Binary Quantization) | ~32× | mała dzięki korekcie i ponownemu rankingowi | Elasticsearch 9 / Lucene |
| TurboQuant | ~8× | zbliżona do skalarnej przy dwukrotnie większej kompresji | Qdrant od 1.18 (11.05.2026) |
| RaBitQ | ~32× | mała z ponownym rankingiem | VectorChord |

Wzorzec, który powtarza się we wszystkich tych systemach: **skwantyzowane wektory
przesiewają, pełne szeregują.** Jeśli dostawca oferuje kwantyzację bez etapu ponownego
rankingu, spodziewaj się spadku recall o kilkanaście punktów i zmierz go, zanim wdrożysz.

## Wielodostępność

Trzy wzorce, w kolejności rosnącej izolacji i kosztu:

| Wzorzec | Jak | Kiedy | Ryzyko |
|---|---|---|---|
| Jedna kolekcja + pole `tenant_id` | filtr przy każdym zapytaniu | wielu małych najemców | pomyłka w filtrze = wyciek między najemcami |
| Partycjonowanie po najemcy w jednej kolekcji | Qdrant: indeks ładunku z `is_tenant`; Milvus: partycje | dziesiątki–tysiące najemców | |
| Osobna kolekcja / przestrzeń per najemca | | wymóg prawny izolacji, duzi najemcy | koszt stały per kolekcja rośnie |

Qdrant 1.16 wprowadził wielodostępność warstwową (aktywni najemcy w pamięci, nieaktywni
na dysku) — to jest właściwy model dla „500 kancelarii, z których 20 pracuje jednocześnie”.
Turbopuffer jest zaprojektowany wokół dokładnie tego przypadku: przestrzenie leżą na
magazynie obiektowym i kosztują prawie nic, dopóki nikt do nich nie pyta.

Twarda reguła niezależnie od bazy: **filtr najemcy wstrzykiwany w warstwie dostępu do
danych, nie w kodzie wywołującym.** Jeden zapomniany filtr w jednym miejscu = wyciek akt
między kancelariami.

## Replikacja, trwałość, kopie

| System | Replikacja | Kopie | Uwaga |
|---|---|---|---|
| pgvector | fizyczna/logiczna Postgresa, PITR | jak baza | najlepsza sytuacja z całej listy |
| Qdrant | shardy z replikami, konsensus Raft | migawki kolekcji (`snapshot`) | migawki trzeba wywozić samodzielnie |
| Weaviate | replikacja z konfigurowalną spójnością | backup do S3/GCS/Azure | |
| Milvus | rozdzielone przechowywanie i obliczenia, obiekty w S3/MinIO | wbudowane | dane i tak leżą w magazynie obiektowym |
| Chroma | ograniczona | kopiowanie katalogu | nie traktuj jako źródła prawdy |
| LanceDB | wersjonowanie w formacie Lance | kopia magazynu obiektowego | wersjonowanie jest wbudowaną cechą formatu |
| Turbopuffer | odpowiedzialność dostawcy | eksport przez API | |

Reguła, która ratuje projekty: **żadna baza wektorowa nie jest źródłem prawdy.**
Źródłem prawdy są pliki i Postgres. Indeks wektorowy musi dać się odtworzyć od zera
skryptem. Jeśli nie da się — masz w systemie stan, którego nie umiesz odbudować.
Zmierz czas pełnej reindeksacji i zapisz go; to jest twoje realne RTO dla wyszukiwarki.

## Koszt: 10 tys. / 1 mln / 100 mln wektorów

Założenia: wektory 1024-wymiarowe, `float32` (4 KB/wektor przed kompresją), metadane ~1 KB,
umiarkowany ruch (10 zapytań/s). Liczby są rzędem wielkości do rozmowy z klientem,
nie ofertą.

| Skala | Surowe wektory | pgvector | Qdrant Cloud | Weaviate Cloud | Turbopuffer | Pinecone |
|---|---|---|---|---|---|---|
| 10 tys. | 40 MB | w istniejącej bazie: **0 zł dodatkowo** | plan darmowy (1 GB RAM) | plan darmowy (100 tys. obiektów) | minimum planu 16 USD/mies. | plan darmowy |
| 1 mln | 4 GB | maszyna 8 GB RAM: ~50–120 USD/mies. (już ją masz) | ~100–250 USD/mies. | Flex od 45 USD/mies. + wymiary + dysk | ~1,3 GB po kompresji → kilkanaście USD + zapytania | ~50–200 USD/mies. |
| 100 mln | 400 GB | nierealne bez kwantyzacji i sharding; z `halfvec`+DiskANN duża maszyna 1000+ USD/mies. | klaster wielowęzłowy, tysiące USD/mies. | jw. | dane ~100 GB × 0,33 USD = ~33 USD/mies. + koszt skanu | tysiące USD/mies. |

Trzy wnioski, które trzeba powiedzieć klientowi:

1. **Do 1 mln fragmentów koszt bazy wektorowej jest szumem** w porównaniu z kosztem
   osadzania i generowania. Optymalizowanie tego jest stratą czasu.
2. Modele cenowe dzielą się na dwie rodziny: **za zarezerwowaną pamięć** (Pinecone, Qdrant,
   Weaviate, pgvector — płacisz, nawet gdy nikt nie pyta) i **za faktyczny ruch nad
   magazynem obiektowym** (Turbopuffer, LanceDB, częściowo Milvus). Przy korpusie dużym
   i rzadko odpytywanym — a taki jest typowy korpus akt — druga rodzina bywa tańsza
   o rząd wielkości.
3. Turbopuffer, stan na 2026: dane do **0,33 USD/GB-mies.**, zapis do **2 USD/GB**,
   zapytania **1 USD/PB** przeskanowanych danych (obniżka z 5 USD/PB w lutym 2026),
   przy minimum **1,28 GB naliczanego skanu na zapytanie**. Plany: Launch 16 USD/mies.
   (obniżone z 64 w czerwcu 2026), Scale 256, Enterprise ≥ 4096 z narzutem 35% na zużycie.
   To minimum na zapytanie jest istotne: system z bardzo dużą liczbą bardzo małych
   zapytań płaci za skan, którego nie wykonał.

Koszty, o których się zapomina przy porównaniach:
- ruch wychodzący z chmury (egress) przy indeksacji z zewnętrznego magazynu,
- ponowne osadzenie całego korpusu przy zmianie modelu (to zwykle największa pojedyncza
  pozycja — patrz `references/engineering-core/04-bazy-i-rag/references/embeddingi.md`),
- czas inżyniera na utrzymanie drugiego systemu; przy jednym etacie DevOps to jest
  droższe niż różnica w rachunku za którąkolwiek z tych baz.

## Hosting własny vs usługa

| Za własnym hostingiem | Za usługą |
|---|---|
| Dane nie opuszczają infrastruktury (RODO, tajemnica zawodowa) | zero utrzymania, aktualizacje, kopie |
| Brak kosztu zmiennego przy dużym ruchu | szybszy start |
| Pełna kontrola wersji i konfiguracji | SLA na piśmie |
| Możliwe uruchomienie w tej samej sieci co baza | wsparcie przy incydencie |

Dla kancelarii przetwarzającej akta klientów pytanie o miejsce przetwarzania jest zwykle
przesądzające. Wtedy: pgvector w tej samej instancji Postgresa co reszta danych, albo
Qdrant/Weaviate w Hybrid Cloud (płatność za sterowanie, dane u siebie). Zwróć uwagę,
że **model embeddingowy też przetwarza treść** — hosting bazy we własnej serwerowni przy
wysyłaniu wszystkich fragmentów do API w USA nie rozwiązuje niczego. Albo obie warstwy
lokalnie, albo trzeba mieć umowę powierzenia i podstawę transferu.

## Migracja między bazami

Migracja jest łatwiejsza, niż się wydaje, **jeśli** od początku spełniasz dwa warunki:

1. Wektory da się odtworzyć z tekstu (masz tekst i wiesz, jakim modelem i jak fragmentowałeś).
2. Warstwa wyszukiwania jest za interfejsem: jedna funkcja `szukaj(zapytanie, filtry, k)`,
   a nie wywołania klienta SDK rozsiane po kodzie.

Procedura:

```
1. Zaimplementuj drugą implementację interfejsu wyszukiwania.
2. Zbuduj indeks w nowej bazie z tego samego źródła prawdy (nie kopiuj wektorów
   między bazami — odtwórz je; wtedy wykryjesz różnice w normalizacji i metrykach).
3. Uruchom oba systemy równolegle na zbiorze testowym. Porównaj recall@10 i nDCG@10.
   Różnica > 3 pp oznacza błąd konfiguracji (zwykle metryka odległości albo brak
   normalizacji), nie „inna baza inaczej liczy".
4. Cieniowanie: kieruj ruch produkcyjny do obu, porównuj wyniki, loguj rozbieżności.
5. Przełącz odczyt, zostaw stary indeks przez tydzień.
```

Rzeczy, które nie przenoszą się automatycznie i są typowym źródłem regresji:
metryka odległości (cosinus vs iloczyn skalarny vs L2), normalizacja wektorów,
składnia i semantyka filtrów (`null` w metadanych bywa traktowany różnie), sposób
liczenia BM25 i wagi w hybrydzie, tokenizacja przy wyszukiwaniu pełnotekstowym.

## Jak porównać dostawców na własnych danych

Benchmarki dostawców są robione na ich korzyść — inny sprzęt, inny zestaw danych, inne
`ef_search`, często pominięty recall. Porównanie warte decyzji zajmuje dzień i wygląda tak:

1. Weź **swój** korpus (albo reprezentatywne 100 tys. fragmentów) i **swoje** zapytania
   testowe ze zbioru ewaluacyjnego.
2. Wyznacz odniesienie: wyszukiwanie dokładne (brute force) na tych danych. To jest
   prawda, względem której liczysz recall każdego kandydata.
3. Dla każdego kandydata **stroj do tego samego recall**, nie do tego samego parametru.
   Porównywanie QPS przy recall 0,88 i 0,97 jest bez wartości. Ustal cel (np. recall@10
   = 0,95) i mierz, ile każdy system potrzebuje czasu i pamięci, żeby go osiągnąć.
4. Mierz komplet: QPS przy p50 i p95 opóźnienia, czas budowy indeksu, zużycie RAM i dysku,
   zachowanie przy filtrze o selektywności 1% i 0,1%, czas pełnej reindeksacji.
5. Osobno zmierz **koszt operacyjny**: ile trwa wdrożenie, aktualizacja wersji,
   odtworzenie z kopii.

Trzy pomiary, które najczęściej wywracają wstępne preferencje: zachowanie przy filtrze
selektywnym, czas budowy indeksu na pełnym korpusie i zużycie RAM przy docelowej skali.

## Reguły wyboru

- Postgres z pgvector, dopóki nie ma zmierzonego powodu przeciwnego. Powód musi być liczbą.
- Zanim wyjdziesz z Postgresa, wypróbuj pgvectorscale albo VectorChord — zostajesz
  w jednej bazie i zwykle to wystarcza.
- Qdrant, gdy głównym problemem jest filtrowanie i wielu najemców.
- Milvus/Zilliz, gdy naprawdę idziesz w setki milionów wektorów albo potrzebujesz GPU.
- Turbopuffer lub LanceDB, gdy korpus jest duży, a ruch rzadki i nierównomierny.
- Elasticsearch/OpenSearch, gdy już go masz i BM25 jest sercem systemu — dokładanie
  drugiego silnika dla wektorów kosztuje więcej, niż daje.
- Chroma tylko do prototypu. Prototyp, który dojrzewa, przechodzi na coś innego —
  zaplanuj to od razu, nie po fakcie.
- Pinecone, gdy zespół nie ma nikogo do utrzymania infrastruktury i akceptuje zamknięcie
  u dostawcy oraz brak kontroli nad miejscem przetwarzania.
