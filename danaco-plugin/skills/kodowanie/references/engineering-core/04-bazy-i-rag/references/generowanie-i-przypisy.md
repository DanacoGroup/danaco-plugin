# Generowanie odpowiedzi i przypisy

Wymaganie klienta prawniczego brzmi: **każde twierdzenie w odpowiedzi ma wskazywać
fragment i stronę, a cytat dosłowny ma dać się porównać ze źródłem znak po znaku.**
Odpowiedź, której nie da się sprawdzić, jest gorsza niż brak odpowiedzi, bo tworzy
pozór podstawy.

## Konstrukcja promptu z materiałem

Kolejność bloków jest istotna i wynika z tego, jak modele przetwarzają długie wejście.

```
1. Instrukcja systemowa (rola, reguły cytowania, reguła odmowy)   ← stabilna, cache
2. MATERIAŁ (fragmenty z identyfikatorami i metadanymi)           ← zmienny
3. Powtórzenie kluczowych reguł w skrócie
4. Pytanie użytkownika                                            ← na końcu
```

Trzy powody dla tej kolejności:
- Materiał **przed** pytaniem — model czyta materiał wiedząc, po co, dopiero gdy widzi
  pytanie na końcu; dodatkowo pozwala buforować wszystko poza pytaniem.
- Reguły powtórzone **po** materiale — długi blok tekstu między instrukcją a pytaniem
  osłabia instrukcję. Trzy zdania przypomnienia kosztują nic i mierzalnie pomagają.
- Pytanie na końcu — pozycja końcowa jest przetwarzana najuważniej.

### Format fragmentu

```xml
<materialy>
<fragment id="f_10432" dokument="Umowa najmu z 12.03.2024" strona="4"
          sciezka="§ 7 Kaucja > ust. 3" data="2024-03-12" wersja="2">
Najemca wpłaci kaucję w wysokości trzykrotności czynszu w terminie 7 dni od
zawarcia umowy. Kaucja podlega zwrotowi w terminie 30 dni od zwrotu lokalu.
</fragment>

<fragment id="f_10433" dokument="Aneks nr 1 z 04.09.2024" strona="1"
          sciezka="§ 2" data="2024-09-04" wersja="1">
Strony zmieniają § 7 ust. 3 umowy w ten sposób, że kaucja podlega zwrotowi
w terminie 14 dni od zwrotu lokalu.
</fragment>
</materialy>
```

Znaczniki XML-owe, nie markdown ani JSON. Modele rodziny Claude są trenowane na
strukturze XML-owej i konsekwentniej odwołują się do atrybutów. JSON kusi model
do odpowiadania JSON-em, markdown gubi granice fragmentów przy treściach zawierających
markdown.

Atrybut `id` musi być **stabilnym identyfikatorem z bazy**, nie numerem porządkowym
w tej odpowiedzi. Numer porządkowy uniemożliwia weryfikację przypisu po fakcie
i rozjeżdża się przy przewijaniu rozmowy.

Data w atrybucie jest niezbędna: bez niej model nie rozstrzygnie, że aneks z września
zmienia umowę z marca.

## Kolejność fragmentów w kontekście

| Kryterium | Zastosowanie |
|---|---|
| Malejąca trafność (wynik rerankera) | domyślne, gdy fragmenty są niezależne |
| Kolejność w dokumencie (`dokument_id`, `nr`) | gdy fragmenty pochodzą z jednego dokumentu i tworzą ciąg wywodu |
| Chronologicznie po dacie dokumentu | gdy pytanie dotyczy stanu prawnego lub zmian w czasie |
| Najtrafniejszy na końcu | gdy fragmentów jest > 15 i widać efekt „zgubionego środka” |

Grupuj fragmenty z tego samego dokumentu razem, nawet kosztem globalnej kolejności
trafności. Przeplatanie fragmentów z pięciu dokumentów utrudnia modelowi ustalenie,
co z czym się łączy.

Zjawisko, o którym trzeba pamiętać: badanie „context rot” (Chroma, 14.07.2025, 18 modeli
od Anthropica, OpenAI, Google i Alibaby) pokazuje, że jakość spada wraz z długością
wejścia **nierównomiernie i nawet na trywialnych zadaniach**, a rozpraszacze
(fragmenty powierzchownie podobne, ale nieodpowiadające na pytanie) obniżają wynik
nieproporcjonalnie. Wniosek praktyczny: **10 trafnych fragmentów bije 50 przeciętnych.**
Reranker służy przede wszystkim do usuwania rozpraszaczy, nie do podnoszenia recall.

## Budżet kontekstu

Policz przed uruchomieniem, nie po przekroczeniu limitu:

```
instrukcja systemowa       ~600 tok.
fragmenty  10 × 600 tok.  ~6 000 tok.
historia rozmowy           ~2 000 tok.  (przycinana)
pytanie                      ~50 tok.
------------------------------------------
wejście                    ~8 650 tok.
odpowiedź                  ~800 tok.
```

Zasady:
- Twardy limit liczby fragmentów **i** sumy tokenów. Jeden fragment będący tabelą na
  50 stron potrafi wysadzić budżet mimo poprawnej liczby fragmentów.
- Przy przekroczeniu odcinaj **fragmenty o najniższej trafności**, nigdy nie przycinaj
  fragmentu w środku — okrojony fragment daje przypis do treści, której nie było.
- Historia rozmowy przycinana z zachowaniem pierwszej tury (zwykle zawiera ustalenia
  o sprawie) i ostatnich N tur.
- Nie wypełniaj okna „bo się mieści”. Każdy dodatkowy nietrafny fragment to koszt
  i rozpraszacz.

## Wymuszenie przypisów

Prompt systemowy — konkret, nie ogólniki:

```
Jesteś asystentem analizującym materiały procesowe. Odpowiadasz WYŁĄCZNIE na podstawie
fragmentów w bloku <materialy>.

ZASADY CYTOWANIA
1. Po każdym zdaniu zawierającym twierdzenie o faktach lub o treści dokumentu podaj
   przypis w postaci [id_fragmentu], np. [f_10432].
2. Jeśli zdanie opiera się na kilku fragmentach, podaj wszystkie: [f_10432][f_10433].
3. Cytat dosłowny umieść w cudzysłowie i przepisz DOKŁADNIE, znak po znaku, ze źródła.
   Nie poprawiaj interpunkcji, ortografii ani odmiany. Jeśli skracasz, użyj [...].
4. Zdania wprowadzające, podsumowujące i pytania nie wymagają przypisu.

ZASADA ODMOWY
Jeśli w materiałach nie ma podstawy do odpowiedzi, napisz dokładnie:
"W dostarczonych materiałach nie ma podstawy do odpowiedzi na to pytanie."
i wskaż, jakiego dokumentu brakuje. NIE uzupełniaj z wiedzy własnej.
Odpowiedź częściowa jest dopuszczalna: odpowiedz na to, co jest pokryte,
i wyraźnie zaznacz, czego brakuje.

SPRZECZNE ŹRÓDŁA
Jeśli fragmenty są ze sobą sprzeczne, przedstaw obie wersje z przypisami i wskaż,
który dokument jest późniejszy (atrybut data) lub wyższego rzędu. Nie wybieraj
w milczeniu jednej wersji.

ZAKAZY
- Nie powołuj przepisów, wyroków ani dokumentów spoza <materialy>.
- Nie podawaj sygnatur ani numerów, których nie ma w materiałach.
- Nie oceniaj szans procesowych, jeśli nie jesteś o to wprost zapytany.
```

Trzy elementy, których brak najbardziej boli w praktyce:
- **Zakaz poprawiania cytatu.** Bez niego model „naprawia” archaiczną ortografię wyroku
  i cytat przestaje się zgadzać ze źródłem.
- **Zakaz podawania sygnatur spoza materiałów.** To jest miejsce, w którym modele
  halucynują najczęściej i najbardziej przekonująco.
- **Dopuszczenie odpowiedzi częściowej.** Bez tego model wybiera między halucynacją
  a bezużyteczną pełną odmową.

## Weryfikacja programowa — obowiązkowa

Instrukcja w prompcie to nie jest zabezpieczenie. Każda odpowiedź przechodzi kontrolę
w kodzie, zanim trafi do użytkownika.

```python
import re, unicodedata

def normalizuj(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = t.replace(" ", " ").replace("­", "")
    t = t.replace("„", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t).strip().casefold()

def sprawdz_odpowiedz(odpowiedz: str, fragmenty: dict[str, str]) -> dict:
    uzyte = set(re.findall(r"\[(f_\d+)\]", odpowiedz))
    nieistniejace = uzyte - set(fragmenty)

    korpus = normalizuj(" ".join(fragmenty.values()))
    cytaty = re.findall(r'"([^"]{20,})"', odpowiedz)
    niezweryfikowane = [
        c for c in cytaty
        if not all(normalizuj(cz) in korpus
                   for cz in re.split(r"\s*\[\.\.\.\]\s*", c) if len(cz.strip()) > 10)
    ]

    zdania = [z for z in re.split(r"(?<=[.!?])\s+", odpowiedz) if len(z) > 40]
    bez_przypisu = [z for z in zdania if not re.search(r"\[f_\d+\]", z)]

    return {
        "nieistniejace_id": sorted(nieistniejace),
        "niezweryfikowane_cytaty": niezweryfikowane,
        "zdania_bez_przypisu": bez_przypisu,
        "pokrycie": 1 - len(bez_przypisu) / max(len(zdania), 1),
    }
```

Reakcja na wynik kontroli:

| Wykryto | Reakcja |
|---|---|
| Identyfikator fragmentu, którego nie było w materiałach | **blokuj odpowiedź**, ponów generowanie; jeśli powtórnie — komunikat o błędzie |
| Cytat niedosłowny | oznacz w interfejsie jako parafrazę albo poproś model o poprawkę z jawnym wskazaniem rozbieżności |
| Pokrycie przypisami < 0,7 | ostrzeżenie w interfejsie, wpis do dziennika, próbka do przeglądu ręcznego |
| Sygnatura/numer w odpowiedzi, którego nie ma w materiałach | flaga do przeglądu; to najczęstsza halucynacja w tekstach prawniczych |

Warto dopisać regułę wyłapującą wzorce sygnatur i numerów:

```python
WZORCE_SYGNATUR = [
    re.compile(r"\b[IVX]{1,4}\s+[A-ZŁŚŻ]{1,4}\s+\d+/\d{2,4}\b"),   # II CSK 123/19
    re.compile(r"\bart\.\s*\d+[a-z]?\b", re.I),
    re.compile(r"\bDz\.\s*U\.\s*z?\s*\d{4}"),
    re.compile(r"\bKRS\s*\d{10}\b"),
]

def sygnatury_spoza_zrodel(odpowiedz: str, korpus: str) -> list[str]:
    znalezione = {m for w in WZORCE_SYGNATUR for m in w.findall(odpowiedz)}
    kn = normalizuj(korpus)
    return sorted(s for s in znalezione if normalizuj(s) not in kn)
```

## Citations API zamiast promptu

Anthropic udostępnia mechanizm cytowania wbudowany w API, dostępny we wszystkich aktywnych
modelach. Zamiast prosić model o `[f_10432]`, przekazujesz materiał jako bloki `document`
z `citations: {enabled: true}` i dostajesz w odpowiedzi obiekty cytowań z **gwarantowanymi**
wskaźnikami do przekazanego tekstu.

Rodzaje cytowań: `char_location` (tekst zwykły, indeksy znakowe od 0),
`page_location` (PDF, numery stron od 1), `content_block_location` (treść własna,
indeksy bloków od 0).

```python
odp = klient.messages.create(
    model="claude-opus-5",
    max_tokens=1500,
    messages=[{"role": "user", "content": [
        {
            "type": "document",
            "source": {"type": "content", "content": [
                {"type": "text", "text": f["tresc"]} for f in fragmenty
            ]},
            "title": "Materiały sprawy",
            "citations": {"enabled": True},
        },
        {"type": "text", "text": pytanie},
    ]}],
)

for blok in odp.content:
    if blok.type == "text" and getattr(blok, "citations", None):
        for c in blok.citations:
            # c.cited_text jest DOSŁOWNYM fragmentem z dokumentu
            # c.start_block_index / c.end_block_index wskazują nasze fragmenty
            ...
```

Zalety względem podejścia promptowego:
- `cited_text` **nie liczy się do tokenów wyjściowych** ani do wejściowych przy zwrocie
  w kolejnej turze — cytowanie długich fragmentów jest darmowe;
- wskaźniki są z definicji poprawne, więc znika cała klasa błędów „przypis do nieistniejącego
  fragmentu”;
- mierzalnie częstsze cytowanie trafnych fragmentów niż przy instrukcji w prompcie.

Ograniczenia, które trzeba znać przed decyzją:
- **nie działa razem z wymuszonym formatem strukturalnym** (`output_config.format`) —
  jeśli potrzebujesz odpowiedzi w JSON, musisz wybrać jedno;
- cytowanie musi być włączone dla wszystkich dokumentów w żądaniu albo dla żadnego;
- **skany bez warstwy tekstowej nie dają się cytować** — dla akt w formie obrazów musisz
  podać własną transkrypcję jako `content` i sam trzymać odsyłacz do obrazu strony;
- brak cytowań do obrazów.

Zalecenie: przy trybie `content` z blokami odpowiadającymi twoim fragmentom masz
jednocześnie gwarancję dosłowności i mapowanie na własne identyfikatory —
to jest właściwa konfiguracja dla systemu prawniczego.

## Odmowa przy braku podstaw

Test, który trzeba wykonać przed oddaniem systemu: **zadaj 20 pytań, na które w korpusie
nie ma odpowiedzi.** Odsetek poprawnych odmów to metryka jakości równie ważna jak recall.

Pytania testowe: o dokument, którego nie ma; o datę spoza zakresu; o stronę
niewystępującą w sprawie; o przepis, którego nie ma w zaindeksowanych aktach.

Bez tego testu system, który wygląda dobrze na pytaniach z odpowiedzią, na pytaniach
bez odpowiedzi produkuje przekonujące zmyślenia — i to właśnie one trafiają do pisma
procesowego.

Wzmocnienia, gdy odmowa nie działa mimo instrukcji:
1. Próg trafności: jeśli najlepszy fragment po reranku ma wynik poniżej progu,
   **nie wywołuj modelu w ogóle** — odpowiedz odmową w kodzie. Próg dobierz na zbiorze
   testowym (zwykle wychodzi między 0,2 a 0,4 dla rerankerów Cohere/Voyage).
2. Osobne wywołanie sprawdzające przed generowaniem: „czy te fragmenty pozwalają
   odpowiedzieć na to pytanie: tak/nie/częściowo”. Kosztuje jedno tanie wywołanie,
   działa lepiej niż instrukcja w głównym prompcie.
3. Przykłady odmowy w prompcie (2–3 pary pytanie–odmowa). Model naśladuje wzorzec.

## Sprzeczne źródła

W aktach sprzeczność jest normą, nie wyjątkiem: umowa i aneks, wyrok i jego zmiana
w instancji odwoławczej, dwa zeznania, przepis w brzmieniu przed i po nowelizacji.

Model musi to zgłosić, a nie rozstrzygnąć po cichu. Reguła w prompcie (wyżej) plus
przekazanie danych, które pozwalają na rozstrzygnięcie:

- `data` dokumentu przy każdym fragmencie — bez tego „późniejszy” jest nieustalalny;
- `typ` dokumentu (ustawa / rozporządzenie / umowa / aneks / wyrok) — pozwala zastosować
  hierarchię źródeł;
- `wersja` i `obowiazuje_od`/`obowiazuje_do`, gdy korpus zawiera historię.

Oczekiwany kształt odpowiedzi:

> Zgodnie z umową kaucja podlega zwrotowi w terminie 30 dni od zwrotu lokalu [f_10432].
> Aneks nr 1 z 4.09.2024 zmienił ten termin na 14 dni [f_10433]. Ponieważ aneks jest
> późniejszy i wprost zmienia § 7 ust. 3, zastosowanie ma termin 14-dniowy.
> Materiały nie zawierają informacji, czy aneks został podpisany przez obie strony.

Ostatnie zdanie — jawne wskazanie luki — jest tym, co odróżnia użyteczną odpowiedź
od odpowiedzi ładnej.

## Strumieniowanie

Odpowiedź z materiałem trwa kilka–kilkanaście sekund. Bez strumieniowania interfejs
wygląda na zawieszony.

Uwaga specyficzna dla przypisów: przy strumieniowaniu przypisy przychodzą jako zdarzenia
`citations_delta` (Citations API) albo pojawiają się w tekście stopniowo. Nie renderuj
przypisu jako klikalnego, zanim nie masz kompletnego identyfikatora — użytkownik kliknie
w `[f_104` i trafi w nic.

Kolejność zdarzeń w interfejsie, która działa:
1. „Przeszukuję materiały…” — natychmiast, przed wywołaniem wyszukiwarki.
2. Lista znalezionych dokumentów z tytułami — po wyszukiwaniu, przed generowaniem.
   Użytkownik widzi, na czym system pracuje, i może przerwać, gdy widzi złe źródła.
3. Strumień odpowiedzi.
4. Po zakończeniu: wynik kontroli programowej (ostrzeżenia o niezweryfikowanych cytatach).

Punkt 2 jest tani i buduje zaufanie bardziej niż cokolwiek innego w interfejsie.

## Buforowanie

Dwa poziomy, oba warte wdrożenia.

### Bufor promptu (po stronie modelu)

Anthropic: zapis do cache na 5 minut kosztuje **1,25×** ceny wejścia, na godzinę **2×**,
a odczyt **0,1×**. Maksymalnie 4 punkty cache w żądaniu. Minimum, żeby cokolwiek
buforować: 1024 tokeny (Sonnet 4.5/5), 512 (Opus 5), 4096 (Haiku 4.5, starsze Opus).

Co buforować w RAG:
- instrukcję systemową i definicje narzędzi — zawsze, punkt cache po nich;
- **materiał, gdy jest stały w obrębie sesji** (analiza jednej sprawy, gdzie zestaw
  dokumentów się nie zmienia) — to jest przypadek, w którym cache daje 10× oszczędności;
- historię rozmowy z punktem cache po ostatniej zakończonej turze.

Czego nie buforować: fragmentów zmieniających się przy każdym pytaniu. Zapis
kosztuje 1,25×, a trafienia nie będzie — wychodzi drożej niż bez cache.

Punkt cache stawiaj **po ostatnim bloku, który jest identyczny między żądaniami**.
Znacznik czasu w prompcie systemowym unieważnia cache przy każdym żądaniu; to najczęstsza
przyczyna „włączyliśmy cache i nic się nie zmieniło”.

### Bufor aplikacyjny

| Co | Klucz | Ważność | Zysk |
|---|---|---|---|
| Wektor zapytania | hash zapytania + model | dni | oszczędza wywołanie embeddingu (~50 ms) |
| Wyniki wyszukiwania | hash (zapytanie, filtry, wersja indeksu) | minuty–godziny | oszczędza wyszukiwanie i rerank |
| Cała odpowiedź | hash (zapytanie, zestaw id fragmentów, wersja promptu) | godziny | oszczędza wszystko |

Klucz bufora **musi** zawierać identyfikator wersji indeksu i wersji promptu. Bufor
przeżywający reindeksację zwraca odpowiedzi oparte na fragmentach, których już nie ma —
a przypisy prowadzą donikąd.

Bufor odpowiedzi w systemie z uprawnieniami: klucz musi zawierać także zakres uprawnień
użytkownika. Inaczej pierwszy użytkownik z szerokim dostępem zapełnia bufor odpowiedzią,
którą dostanie użytkownik z wąskim. To jest wyciek danych przez bufor.

## Antywzorce

| Antywzorzec | Konsekwencja |
|---|---|
| Przypis jako numer porządkowy `[1]`, `[2]` | nie da się zweryfikować po fakcie; rozjeżdża się przy przewijaniu rozmowy |
| Brak weryfikacji programowej cytatu | cytat „prawie dosłowny” trafia do pisma procesowego |
| Uprawnienia egzekwowane instrukcją w prompcie | model to zignoruje przy odpowiednio sformułowanym pytaniu |
| Podawanie 50 fragmentów „żeby model miał wybór” | rozpraszacze obniżają jakość; koszt rośnie liniowo |
| Przycinanie fragmentu w środku przy przekroczeniu budżetu | przypis do treści, której nie było |
| Brak `data` w metadanych fragmentu | model nie rozstrzygnie sprzeczności między umową a aneksem |
| Brak testu odmowy | system produkuje przekonujące zmyślenia na pytania spoza korpusu |
| Bufor odpowiedzi bez wersji indeksu w kluczu | przypisy do usuniętych fragmentów |
| Bufor odpowiedzi bez zakresu uprawnień w kluczu | wyciek treści między użytkownikami |
| Punkt cache po bloku zawierającym znacznik czasu | cache nigdy nie trafia, płacisz 1,25× za nic |
| Renderowanie klikalnych przypisów w trakcie strumieniowania | użytkownik klika w niekompletny identyfikator |
