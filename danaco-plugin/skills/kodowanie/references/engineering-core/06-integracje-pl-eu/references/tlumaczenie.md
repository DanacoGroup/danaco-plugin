# Tłumaczenie maszynowe jako funkcja aplikacji

> Stan na: 2026-08-04. Źródła: https://developers.deepl.com/docs/api-reference/translate,
> https://support.deepl.com/hc/en-us/articles/360021200939-DeepL-API-plans,
> https://support.deepl.com/hc/en-us/articles/26380849099932-DeepL-infrastructure-and-data-protection,
> https://cloud.google.com/translate/pricing, https://docs.cloud.google.com/translate/docs/overview,
> https://www.deepl.com/pl/features/glossary.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Wybór dostawcy

| Kryterium | DeepL | Google Cloud Translation | Model językowy (LLM) | Model lokalny |
| --- | --- | --- | --- | --- |
| Jakość PL↔EN/DE | bardzo dobra, naturalna składnia | dobra, bywa dosłowna | dobra do bardzo dobrej, zależna od promptu | od słabej do dobrej |
| Terminologia prawnicza | glosariusz wymuszający | glosariusz w modelach custom | sterowalna promptem, **niestabilna między wywołaniami** | zależna od modelu |
| Powtarzalność | wysoka | wysoka | **niska** — ten sam tekst może dać inny wynik | wysoka |
| Zachowanie formatowania | tłumaczenie dokumentów zachowuje układ | tłumaczenie dokumentów per strona | trzeba samemu | trzeba samemu |
| Dane opuszczają organizację | tak (serwery w UE dla planów Pro/API) | tak | tak | **nie** |
| Koszt jednostkowy | za znaki | za znaki / strony | za tokeny | koszt sprzętu |

Reguła doboru dla tekstów prawniczych: **DeepL z glosariuszem** do tłumaczeń, które mają być
powtarzalne i terminologicznie spójne. **LLM** tam, gdzie potrzebne jest rozumienie kontekstu
(streszczenie, przeformułowanie, tłumaczenie z komentarzem) i gdzie nikt nie porówna dwóch
wywołań. Nie odwrotnie — LLM jako silnik tłumaczeń produkcyjnych daje za każdym razem inny
wybór terminu, co w dokumencie prawnym jest wadą, nie zaletą.

## DeepL API

Adresy bazowe:

| Plan | Adres |
| --- | --- |
| Pro / płatne | `https://api.deepl.com` |
| Free (wycofany dla nowych) | `https://api-free.deepl.com` |

Uwierzytelnienie: nagłówek `Authorization: DeepL-Auth-Key <klucz>`.

Limity techniczne:
- **maksymalny rozmiar żądania: 128 KiB**;
- parametr `text` może wystąpić wielokrotnie w jednym żądaniu (w ramach 128 KiB); tłumaczenia
  wracają **w tej samej kolejności**, w jakiej je wysłano.

Konsekwencja: batchuj krótkie teksty (etykiety UI, rekordy) — jedno żądanie z 50 tekstami jest
wielokrotnie tańsze czasowo niż 50 żądań. Ale pilnuj 128 KiB, bo przekroczenie odrzuca całą paczkę.

### Parametry, które mają znaczenie

| Parametr | Wartości | Do czego |
| --- | --- | --- |
| `formality` | `default`, `more`, `less`, `prefer_more`, `prefer_less` | Forma grzecznościowa. Dla polskiego istotne: `more` wymusza formę „Pan/Pani” zamiast „ty” |
| `glossary_id` | UUID | Wymusza tłumaczenie terminów. **Wymaga ustawienia `source_lang`** |
| `glossary_ids` | tablica, **max 5** | Kilka glosariuszy naraz |
| `tag_handling` | `xml`, `html` | Ochrona znaczników przed tłumaczeniem |
| `model_type` | `quality_optimized`, `prefer_quality_optimized`, `latency_optimized` | Kompromis jakość/opóźnienie |

`glossary_id` bez `source_lang` jest **cicho ignorowany** — to najczęstszy powód „glosariusz nie
działa”. Zawsze podawaj język źródłowy przy glosariuszu.

`tag_handling` używaj zawsze, gdy tekst zawiera znaczniki. Bez tego DeepL przetłumaczy nazwy
tagów albo je pogubi.

### Plany (stan 2026-08-04)

| Plan | Zakres |
| --- | --- |
| **API Developer** | Do **1 000 000 znaków łącznie** (bez odnowienia miesięcznego). Bez speech-to-text. Po wyczerpaniu — przejście na Growth |
| **API Growth** | Stała opłata miesięczna/roczna; **50 mln znaków** i **300 h** speech-to-text miesięcznie. Maksymalny poziom ochrony danych, API Write, limity per klucz, wtyczki CAT |
| **API Enterprise** | Indywidualne zobowiązania wolumenowe, kontakt z działem sprzedaży |
| **API Free** | **Wycofany** — nie można już kupić (dawniej 500 000 znaków/mies.) |
| **API Pro** | **Wycofany** — nie można już kupić (dawniej opłata stała + koszt za znak) |

`[niepotwierdzone: aktualne stawki cenowe planów Growth i Enterprise w EUR/PLN — DeepL nie
publikuje ich w dokumentacji pomocy; sprawdź https://www.deepl.com/pro#api]`

Istotne dla kosztorysu: **plan Developer nie odnawia się co miesiąc** — to jednorazowy milion
znaków. Nie planuj na nim produkcji.

### Tłumaczenie dokumentów

DeepL ma osobny przepływ dla plików (`/v2/document`): upload → polling statusu → download.
Zachowuje układ dokumentu. Obsługiwane formaty obejmują .docx, .pptx, .xlsx, .pdf, .html, .txt.
`[niepotwierdzone: pełna lista formatów i limity rozmiaru pliku per plan — sprawdź
https://developers.deepl.com/docs/api-reference/document]`

Przy PDF: tłumaczenie zachowuje układ tylko dla PDF-ów tekstowych. **Skan wymaga OCR wcześniej** —
DeepL nie zrobi tego za ciebie i zwróci pusty albo szczątkowy wynik.

### Glosariusze — spójność terminologii

Glosariusz to zbiór par „termin źródłowy → termin docelowy” dla konkretnej pary językowej.
Wymuszany jest przy tłumaczeniu, niezależnie od kontekstu.

Dlaczego to jest kluczowe dla tekstów prawniczych: bez glosariusza „zażalenie”, „skarga”,
„odwołanie” i „środek zaskarżenia” trafią na częściowo pokrywające się angielskie odpowiedniki,
zmienne między akapitami. W dokumencie procesowym to jest błąd merytoryczny, nie stylistyczny.

Zasady budowy glosariusza prawniczego:
1. Wpisuj **tylko terminy, dla których istnieje jedno poprawne tłumaczenie w danym kontekście**.
   Glosariusz nie rozumie kontekstu — wymusza zawsze.
2. Nie wpisuj słów wieloznacznych ogólnych („strona”, „sprawa”) — zepsujesz zdania, w których
   występują w innym sensie.
3. Prowadź osobne glosariusze per dziedzina (cywilny, karny, administracyjny) i wybieraj
   `glossary_id` na podstawie klasyfikacji dokumentu, nie mieszaj wszystkiego w jeden.
4. Wersjonuj glosariusz razem z kodem. Zmiana glosariusza zmienia wyniki historycznych tłumaczeń
   — jeśli to ma znaczenie dowodowe, zapisuj `glossary_id` razem z wynikiem.

Ograniczenie: max **5** glosariuszy w jednym żądaniu.

## Google Cloud Translation

Cennik (https://cloud.google.com/translate/pricing, odczyt 2026-08-04, USD):

| Usługa | Cena |
| --- | --- |
| NMT (Basic v2 i Advanced v3), tekst | **20 USD / mln znaków** (pierwsze 500 000 znaków/mies. w ramach kredytu 10 USD) |
| NMT, tłumaczenie dokumentów (DOCX, PPT, PDF) | **0,08 USD / stronę** |
| Modele własne (AutoML), tekst | **80 USD / mln znaków** (progi malejące do 30 USD powyżej 4 mld) |
| Modele własne, dokumenty | **0,25 USD / stronę** |
| Translation LLM — text translation | **10 USD / mln znaków** wejścia i **10 USD / mln** wyjścia |
| Adaptive Translation | **25 USD / mln znaków** wejścia i wyjścia |
| Custom text translation (LLM) | **20 USD / mln znaków** wejścia i wyjścia |
| Trenowanie modelu własnego | **45 USD/h**, max 300 USD na zadanie |

Zwróć uwagę: **Translation LLM** (10 USD/mln) jest tańszy niż klasyczny NMT (20 USD/mln), a
**Adaptive Translation** pozwala dostroić wynik przykładami bez trenowania modelu — to jest
najbliższy odpowiednik glosariusza DeepL po stronie Google, ale działa przez przykłady, nie
przez twarde reguły.

Uwaga na jednostkę rozliczeniową w LLM: liczone są **znaki wejścia i wyjścia osobno**.
Tłumaczenie 1 mln znaków to realnie ~2 mln znaków rozliczeniowych.

## Modele językowe jako tłumacz

Kiedy mają przewagę:
- tekst wymaga zrozumienia, nie odwzorowania (streszczenie w innym języku, tłumaczenie z
  wyjaśnieniem instytucji prawnej nieistniejącej w systemie docelowym);
- potrzebna jest kontrola stylu wykraczająca poza `formality`;
- tłumaczenie ma być połączone z inną operacją (ekstrakcja + tłumaczenie w jednym przebiegu).

Kiedy przegrywają:
- **powtarzalność** — dwa wywołania na tym samym tekście dają różne wyniki nawet przy
  `temperature=0`;
- **koszt przy wolumenie** — rozliczenie za tokeny wychodzi drożej niż 10–20 USD/mln znaków przy
  prostym tłumaczeniu;
- **opóźnienie** — nieakceptowalne dla tłumaczenia w czasie rzeczywistym w interfejsie.

Jeśli używasz LLM, wymuś powtarzalność przez: `temperature=0`, stały prompt systemowy, glosariusz
wstrzyknięty do promptu jako tabela, cache wyników po hashu tekstu.

## Tłumaczenie w czasie rzeczywistym

Wymagania: opóźnienie < 300 ms na segment, żeby interakcja była płynna.

- DeepL: `model_type=latency_optimized`, batchowanie po zdaniu, nie po akapicie.
- Debounce na wejściu użytkownika — nie wysyłaj przy każdym znaku. 300–500 ms bezczynności.
- Cache po hashu tekstu źródłowego + para językowa + `glossary_id`. W interfejsach powtarzalność
  tekstów jest bardzo wysoka; cache zbija koszt o rząd wielkości.
- Nie tłumacz w czasie rzeczywistym dokumentów. Tłumacz je asynchronicznie z paskiem postępu.

## Poufność i RODO

**DeepL** (plany Pro/API), stan wg dokumentacji pomocy:
- infrastruktura hybrydowa: własne serwery DeepL w centrach danych **w Europie** + AWS;
  regiony: Europa, USA, Azja-Pacyfik;
- teksty **nie są przechowywane**: „the text you enter or upload is processed instantly to
  provide the services and is not stored”;
- przechowywane są tylko dane zapisane celowo (glosariusze, zapisane tłumaczenia) do czasu
  usunięcia;
- certyfikaty: **ISO 27001** i **SOC 2 Type II**;
- dane płacących użytkowników **nie są używane do trenowania modeli** poza kontem;
- szyfrowanie w tranzycie i w spoczynku, klucze kontroluje DeepL, nie AWS.

Co z tego wynika dla RODO:
1. Wysłanie tekstu do DeepL to **powierzenie przetwarzania** — potrzebna umowa powierzenia (DPA).
   DeepL udostępnia wzór.
2. Trzeba wskazać region przetwarzania. Domyślny region konta nie musi być europejski — **ustaw go
   jawnie**, jeśli dane mają nie opuszczać EOG.
3. DeepL jest podprocesorem — wpisz go do rejestru czynności i do informacji dla klienta.
4. Dla danych szczególnych kategorii (art. 9 RODO: zdrowie, wyroki, dane wrażliwe w aktach
   sprawy) ocena ryzyka jest osobna. Sam fakt, że dostawca ma ISO 27001, nie jest podstawą
   przetwarzania.
5. **Tajemnica zawodowa** (adwokacka, radcowska, notarialna) jest reżimem odrębnym od RODO
   i surowszym. Powierzenie danych objętych tajemnicą zewnętrznemu dostawcy wymaga odrębnej
   analizy — `[niepotwierdzone: aktualne stanowiska NRA/KIRP w sprawie dopuszczalności korzystania
   z chmurowych usług tłumaczenia dla materiałów objętych tajemnicą; sprawdź uchwały samorządów]`

**Google Cloud Translation**: dane klienta nie są używane do ulepszania modeli w Cloud;
region przetwarzania konfigurowalny (`europe-west*`). DPA w ramach Google Cloud Terms.
`[niepotwierdzone: aktualne brzmienie zobowiązań Google co do niewykorzystywania danych Cloud
Translation do trenowania — sprawdź Google Cloud Data Processing Addendum]`

## Modele lokalne jako alternatywa

Kiedy to jedyna dopuszczalna droga: materiał objęty tajemnicą zawodową, dane objęte zakazem
transferu, wymóg klienta „nic nie wychodzi z naszej infrastruktury”.

| Model | Charakterystyka |
| --- | --- |
| **NLLB-200** (Meta) | 200 języków, warianty od 600M do 54B parametrów. Polski wspierany. Jakość poniżej DeepL, ale użyteczna |
| **MADLAD-400** (Google) | Warianty 3B, 7B, 10B. Szeroki zakres językowy, T5-owy |
| **Opus-MT** (Helsinki-NLP) | Modele per para językowa, bardzo małe (dziesiątki MB), szybkie na CPU. Jakość niższa, ale dla pary PL-EN akceptowalna w zastosowaniach pomocniczych |
| **Ogólne LLM lokalne** (Gemma, Llama, Qwen w wariantach instruct) | Jakość zależna od rozmiaru; wymagają GPU dla rozsądnego opóźnienia |

`[niepotwierdzone: porównawcze wyniki jakości (COMET/BLEU) dla pary PL↔EN dla wymienionych modeli
w 2026 r. — nie znaleziono wiarygodnego, aktualnego benchmarku; przed wyborem przetestuj na
własnym korpusie]`

Realistyczna ocena: model lokalny **nie dorówna DeepL na tekstach prawniczych**. Sensowny wzorzec
hybrydowy: dokumenty jawne → DeepL z glosariuszem; dokumenty objęte tajemnicą → model lokalny
z wyraźnym oznaczeniem w interfejsie, że jakość jest niższa i wymaga weryfikacji człowieka.

## Twarde reguły dla funkcji tłumaczenia w aplikacji

1. Tłumaczenie maszynowe dokumentu o skutkach prawnych **musi być oznaczone jako maszynowe**
   i nie może zastępować tłumaczenia przysięgłego.
2. Przechowuj razem z wynikiem: dostawcę, model, `glossary_id`, datę. Bez tego nie odtworzysz,
   dlaczego termin przetłumaczono tak, a nie inaczej.
3. Cache po hashu (tekst + para językowa + glosariusz). Bez tego płacisz wielokrotnie za to samo.
4. Nigdy nie wysyłaj do zewnętrznego API tekstu, którego klasyfikacja poufności nie została
   sprawdzona przez kod, a nie przez użytkownika.
5. Batchuj, ale pilnuj limitu 128 KiB (DeepL) — przekroczenie odrzuca całą paczkę, nie jej część.
6. `source_lang` jest obowiązkowy przy glosariuszu; bez niego glosariusz nie działa i nie ma o tym
   komunikatu.

## Co potwierdzić przed wdrożeniem

1. Aktualny cennik i limity planów DeepL (plany są przebudowywane — Free i Pro już wycofano).
2. Region przetwarzania ustawiony na koncie DeepL.
3. Podpisaną umowę powierzenia z dostawcą.
4. Stanowisko samorządu zawodowego, jeśli materiał objęty tajemnicą.
