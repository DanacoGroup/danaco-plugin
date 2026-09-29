# Fragmentacja

Fragment jest jednostką, którą wyszukiwarka zwraca, model czyta, a użytkownik weryfikuje.
Zbyt duży — rozmywa sygnał w wektorze i zapycha kontekst. Zbyt mały — traci sens
i nie da się z niego odpowiedzieć.

Wartość startowa, gdy nikt nie podał inaczej: **400–600 tokenów, nakładka 10–15%,
granice na akapitach, nagłówek sekcji powtórzony na początku.** Dokumenty prawnicze
bliżej 600, dokumentacja techniczna bliżej 400.

## Strategie

| Strategia | Jak działa | Kiedy | Koszt |
|---|---|---|---|
| Stały rozmiar znakowy | tnij co N znaków | nigdy jako docelowe; tylko do szybkiego prototypu | zerowy |
| Stały rozmiar tokenowy | tnij co N tokenów tokenizatorem modelu | prosty punkt odniesienia | zerowy |
| Zdaniowe | granice na końcach zdań, sklejaj do limitu | krótkie, gęste teksty | znikomy |
| Akapitowe | granice na pustych liniach, sklejaj do limitu | **domyślne** dla prozy i pism | znikomy |
| Według struktury dokumentu | granice na nagłówkach, §, ust., pkt | **domyślne** dla aktów prawnych, umów, regulaminów | wymaga parsera zachowującego strukturę |
| Semantyczne | osadź zdania, tnij tam, gdzie podobieństwo sąsiadów spada poniżej progu | teksty bez struktury (transkrypcje, notatki) | osadzenie każdego zdania przy indeksacji |
| Hierarchiczne (rodzic–dziecko) | szukaj po małych, podawaj duże | **domyślne, gdy zależy na jakości odpowiedzi** | podwójne przechowywanie |
| Late chunking | osadź cały dokument modelem długokontekstowym, uśrednij tokeny per fragment | dokumenty ≤ okno modelu, dużo zaimków i odwołań | tylko model z długim kontekstem |
| Kontekstualizacja fragmentu | LLM dopisuje 1–2 zdania kontekstu przed osadzeniem | **największy zmierzony zysk**, gdy budżet pozwala | ~1 USD za 1 mln tokenów dokumentów |

### Stały rozmiar — dlaczego nie

Cięcie co N znaków rozcina zdania i jednostki redakcyjne. Fragment kończący się w połowie
przesłanki („...jeżeli dłużnik nie”) osadza się w miejscu, które nie odpowiada niczemu.
Dodatkowo w wynikach użytkownik widzi urwane zdanie i traci zaufanie do systemu.
Jedyne uzasadnione użycie: pierwsze 30 minut prototypu.

### Według struktury — właściwy wybór dla prawa

Akty prawne, umowy i regulaminy mają gotową, jawną hierarchię: część → dział → rozdział →
artykuł/paragraf → ustęp → punkt → litera. To są naturalne granice fragmentów i naturalne
jednostki cytowania. Fragment odpowiadający jednemu ustępowi jest przypisem sam w sobie.

```python
import re

WZORCE = [
    (0, re.compile(r"^\s*(DZIAŁ|Dział)\s+[IVXLC]+", re.M)),
    (1, re.compile(r"^\s*(Rozdział|ROZDZIAŁ)\s+[IVXLC0-9]+", re.M)),
    (2, re.compile(r"^\s*(Art\.|§)\s*\d+", re.M)),
    (3, re.compile(r"^\s*\d+\.\s", re.M)),        # ustęp
    (4, re.compile(r"^\s*\d+\)\s", re.M)),        # punkt
]
```

Reguła składania: fragmentem jest najmniejsza jednostka, która mieści się w limicie.
Jeśli artykuł ma 200 tokenów — fragmentem jest artykuł. Jeśli 2000 — fragmentami są ustępy,
każdy poprzedzony nagłówkiem artykułu. Jeśli pojedynczy ustęp ma 1500 tokenów — dziel
zdaniowo z nakładką, ale zachowaj oznaczenie jednostki w każdej części.

### Semantyczne — mniej warte, niż się reklamuje

Metoda: osadź kolejne zdania, licz podobieństwo sąsiadów, tnij w dolinach. Brzmi dobrze,
w pomiarach na korpusach z jasną strukturą przegrywa z fragmentacją strukturalną,
a kosztuje osadzenie każdego zdania przy indeksacji. Sensowne tylko tam, gdzie struktury
nie ma: transkrypcje rozpraw, notatki ze spotkań, długie maile.

### Hierarchiczne (rodzic–dziecko)

Rozdziela dwa sprzeczne wymagania: do wyszukiwania chcesz małych, precyzyjnych fragmentów
(wektor 200 tokenów jest ostrzejszy niż wektor 1500 tokenów), do odpowiedzi chcesz
dużego kontekstu.

```
dziecko: 200-300 tokenów  → osadzane i indeksowane
rodzic:  1000-1500 tokenów → podawane modelowi po trafieniu dziecka
```

```sql
ALTER TABLE fragmenty ADD COLUMN rodzic_id bigint REFERENCES fragmenty(id);

-- wyszukaj po dzieciach, zwróć unikalnych rodziców
WITH trafienia AS (
  SELECT id, rodzic_id, emb <=> $1 AS dystans
  FROM fragmenty
  WHERE rodzic_id IS NOT NULL
  ORDER BY emb <=> $1
  LIMIT 50
)
SELECT DISTINCT ON (r.id) r.id, r.tresc, min(t.dystans) AS dystans
FROM trafienia t
JOIN fragmenty r ON r.id = t.rodzic_id
GROUP BY r.id, r.tresc
ORDER BY r.id, dystans
LIMIT 10;
```

Wariant tańszy i prawie tak samo skuteczny: **rozszerzanie sąsiadami**. Indeksujesz tylko
małe fragmenty, a po trafieniu dołączasz fragment poprzedni i następny po `nr`.
Zero dodatkowego przechowywania.

```sql
SELECT f.*
FROM fragmenty f
JOIN trafienia t ON f.dokument_id = t.dokument_id
                AND f.nr BETWEEN t.nr - 1 AND t.nr + 1;
```

### Late chunking

Pomysł (Jina, arXiv:2409.04701): zamiast osadzać fragmenty osobno, przepuść cały dokument
przez model z długim kontekstem, a dopiero na wyjściu uśrednij wektory tokenów należące
do każdego fragmentu. Każdy fragment „wie” wtedy, co było wcześniej — zaimki i odwołania
przestają być bezkontekstowe.

Wymagania: model z oknem ≥ długość dokumentu i dostępem do wektorów tokenów
(modele własne, `jina-embeddings-v3/v5`, `voyage-context-4` realizuje pokrewny pomysł
przez API na 120 tys. tokenów kontekstu).

Stan dowodów jest mieszany. Praca „Reconstructing Context” (arXiv:2504.19754) mierzy
na NFCorpus i MSMarco: late chunking wygrywa z klasycznym raz (NDCG@5 0,380 vs 0,374
z jina-v3), a przegrywa wyraźnie w innych zestawieniach (0,070 vs 0,246 z BGE-M3;
0,503 vs 0,630 ze stella-v5). Wniosek: **działa tylko z modelem, który był na to trenowany**,
a użyty z dowolnym modelem długokontekstowym potrafi zaszkodzić. Zmierz na swoim korpusie
albo nie stosuj.

### Kontekstualizacja fragmentu (Contextual Retrieval)

Najlepiej udokumentowana pojedyncza poprawka jakości wyszukiwania. Metoda Anthropica
(wrzesień 2024): przed osadzeniem dopisz do fragmentu 50–100 tokenów kontekstu
wygenerowanego przez model, który widzi cały dokument.

Zmierzone na fragmentach ~800 tokenów, przy pobieraniu top-20:

| Konfiguracja | Odsetek zapytań bez trafnego fragmentu w top-20 |
|---|---|
| baza (osadzenia + BM25) | 5,7% |
| + kontekst przed osadzeniem | 3,7% (−35%) |
| + kontekstowy BM25 | 2,9% (−49%) |
| + reranking | **1,9% (−67%)** |

Koszt: **1,02 USD za 1 mln tokenów dokumentów** przy użyciu buforowania promptu
(dokument w cache, generowany jest tylko kontekst per fragment). Dla korpusu 100 mln
tokenów to ok. 100 USD jednorazowo — mniej niż tydzień pracy inżyniera nad strojeniem.

```python
PROMPT = """<dokument>
{dokument}
</dokument>

Oto fragment tego dokumentu:
<fragment>
{fragment}
</fragment>

Napisz 1-2 zdania osadzające ten fragment w całości dokumentu: czego dotyczy dokument,
w której jego części znajduje się fragment, do czego się odnosi. Odpowiedz wyłącznie
tym opisem, bez wstępu."""
```

Osadzasz `kontekst + "\n\n" + tresc`, a użytkownikowi pokazujesz i cytujesz **wyłącznie
`tresc`**. Kontekst jest wygenerowany przez model i nie wolno go traktować jako treści
dokumentu — to jest wymóg weryfikowalności, nie kosmetyka.

Wersja tania, bez LLM, dająca sporą część zysku: dopisz ścieżkę nagłówków i metadane.

```
Umowa najmu lokalu z 12.03.2024, strony: Kowalski / ACME sp. z o.o.
§ 7 Kaucja > ust. 3

[treść fragmentu]
```

Dla korpusu ze zdyscyplinowaną strukturą (a akty prawne taki mają) różnica między wersją
z LLM a wersją ze ścieżką nagłówków jest niewielka. Zmierz obie, zanim wydasz pieniądze.

## Nakładanie się fragmentów

Nakładka chroni przed rozcięciem sensu na granicy. Kosztuje miejsce i tworzy duplikaty
w wynikach.

| Nakładka | Kiedy |
|---|---|
| 0% | granice strukturalne (§, ust.) — nakładka jest wtedy szkodliwa, bo rozmywa jednostkę cytowania |
| 10–15% | domyślnie dla prozy i cięcia akapitowego |
| 20–25% | teksty gęste, dużo odwołań, brak wyraźnej struktury |
| > 25% | nigdy — płacisz za osadzenie i przechowywanie tej samej treści wielokrotnie |

Przy nakładce trzeba deduplikować wyniki: dwa sąsiednie fragmenty z 20% nakładką trafiają
razem w top-k i podają modelowi ten sam tekst dwa razy. Scalaj sąsiadujące fragmenty
z tego samego dokumentu przed przekazaniem do generowania.

## Dobór rozmiaru do typu treści

| Typ | Rozmiar | Granice | Uwagi |
|---|---|---|---|
| Ustawa, rozporządzenie | 300–600 tok. | artykuł / ustęp | jednostka redakcyjna = jednostka cytowania |
| Umowa, regulamin | 400–700 tok. | § / ust. | zachowaj definicje z początku jako kontekst |
| Wyrok, uzasadnienie | 500–800 tok. | akapit / sekcja (stan faktyczny, ocena prawna) | tezy oddzielnie, są najczęściej cytowane |
| Pismo procesowe | 400–600 tok. | punkt uzasadnienia | |
| Korespondencja | wiadomość | cała wiadomość | odetnij cytowany wątek |
| Dokumentacja techniczna | 300–500 tok. | nagłówek | bloki kodu nierozdzielane |
| Transkrypcja | 300–500 tok. | zmiana mówcy / temat semantyczny | zachowaj znacznik czasu |
| Tabela | cała tabela | — | nigdy nie dziel; powtórz nagłówek kolumn |
| FAQ, baza wiedzy | wpis | cały wpis | pytanie + odpowiedź razem |

Nie dobieraj rozmiaru „bo w tutorialu było 1000”. Rozmiar zależy od tego, ile tekstu
potrzeba, żeby fragment był samodzielnie zrozumiały — i to jest kryterium, które można
sprawdzić ręcznie na 20 losowych fragmentach.

## Pomiar wpływu

Fragmentacja jest parametrem, nie decyzją estetyczną. Mierzysz ją tak samo jak wszystko inne.

Procedura:
1. Zbiór testowy: pytanie → identyfikator dokumentu i zakres znaków, w którym jest odpowiedź
   (`references/engineering-core/04-bazy-i-rag/references/ewaluacja.md`). Zakres znakowy, nie
   identyfikator fragmentu — inaczej zbiór testowy przestaje być ważny przy każdej zmianie
   fragmentacji.
2. Dla każdego wariantu fragmentacji zbuduj indeks od nowa.
3. Trafienie liczysz jako „zwrócony fragment przecina się z zakresem odpowiedzi”.
4. Porównaj recall@5, recall@10, recall@20 i **średnią liczbę tokenów przekazanych
   do modelu** przy tej samej jakości. Wariant o tym samym recall i o 40% mniejszym
   zużyciu kontekstu jest wariantem lepszym.

```python
def trafienie(fragment, zlota_odpowiedz) -> bool:
    return (fragment["dokument_id"] == zlota_odpowiedz["dokument_id"]
            and fragment["offset_od"] < zlota_odpowiedz["offset_do"]
            and fragment["offset_do"] > zlota_odpowiedz["offset_od"])
```

Warianty warte sprawdzenia, w kolejności prawdopodobnego zysku:
1. strukturalna vs akapitowa,
2. 400 vs 600 vs 800 tokenów,
3. z kontekstualizacją vs bez,
4. hierarchiczna vs płaska,
5. nakładka 0 vs 15%.

Zwykle 1 i 3 dają zauważalną różnicę, a 2 i 5 mieszczą się w szumie. Nie strój
parametrów, które nie zmieniają wyniku — to jest czas, który lepiej wydać na reranker.

## Antywzorce

| Antywzorzec | Konsekwencja |
|---|---|
| Cięcie co N znaków na dokumentach prawnych | fragment kończy się w środku przesłanki; nie da się z niego cytować |
| Fragment bez oznaczenia jednostki redakcyjnej | model odpowiada bez podstawy prawnej albo ją zmyśla |
| Tabela pocięta na fragmenty | wiersze bez nagłówków kolumn; liczby bez znaczenia |
| Nakładka 50% „dla pewności” | podwojony koszt osadzenia i przechowywania, duplikaty w każdym wyniku |
| Osadzanie fragmentu razem z wygenerowanym kontekstem i pokazywanie obu użytkownikowi | cytat zawiera tekst, którego nie ma w dokumencie — dyskwalifikujące |
| Fragmentacja zmieniona bez ponownego osadzenia całości | indeks zawiera dwie niekompatybilne granulacje |
| Identyfikator fragmentu jako klucz w zbiorze testowym | zbiór traci ważność przy każdej zmianie fragmentacji |
| Fragmenty bez `offset_od`/`offset_do` | cytatu nie da się zweryfikować ani podświetlić w oryginale |
