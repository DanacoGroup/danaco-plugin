# Potok dokumentów: od pliku do fragmentu

Tu leży większość jakości całego systemu. Model embeddingowy poprawi wynik o kilka punktów;
źle wyciągnięty tekst z PDF-a odbiera kilkadziesiąt. Kolejność diagnozy przy złym RAG
zawsze zaczyna się od pytania „czy ten fragment w ogóle jest w indeksie i czy jest czytelny”.

Wersje bibliotek sprawdzone 04.08.2026: `docling` 2.118.0, `unstructured` 0.25.2,
`chonkie` 1.7.0.

## Etapy

```
plik → identyfikacja → wyciągnięcie tekstu + struktury → normalizacja →
wykrycie języka → deduplikacja → metadane → fragmentacja → osadzenie → indeks
```

Każdy etap zapisuje wynik trwale (nie tylko w pamięci procesu). Powód: przy zmianie modelu
embeddingowego chcesz osadzić ponownie, nie parsować ponownie. Parsowanie 100 tys.
PDF-ów z OCR to dni pracy; osadzenie tych samych fragmentów to godziny.

Tabela pośrednia, którą warto mieć:

```sql
CREATE TABLE dokumenty_tekst (
  dokument_id   bigint PRIMARY KEY REFERENCES dokumenty(id) ON DELETE CASCADE,
  wersja_dok    int    NOT NULL,
  tekst         text   NOT NULL,          -- markdown ze strukturą
  strony        jsonb  NOT NULL,          -- [{nr, offset_od, offset_do}, ...]
  parser        text   NOT NULL,          -- 'pdfium' | 'docling' | 'ocr-tesseract' | ...
  parser_wersja text   NOT NULL,
  ocr           bool   NOT NULL DEFAULT false,
  ocr_pewnosc   real,
  jezyk         text,
  przetworzono  timestamptz NOT NULL DEFAULT now()
);
```

Mapa `strony` (offsety znakowe → numer strony) jest tym, co pozwala później zamienić
fragment na przypis „str. 14”. Bez niej przypis do strony jest nie do odtworzenia.

## Pozyskanie według formatu

### PDF z warstwą tekstową

Najprostszy przypadek i najczęstsze źródło cichych błędów.

| Narzędzie | Zalety | Wady |
|---|---|---|
| `pypdfium2` / `pdfium` | bardzo szybkie, dobra kolejność czytania | brak analizy układu, tabele jako tekst płaski |
| `pdfplumber` | pozycje znaków, wykrywanie tabel, ramki | wolne (rzędy sekund na stronę przy dużych plikach) |
| `PyMuPDF` (fitz) | szybkie, eksport do markdown, obrazy | licencja AGPL — przy produkcie zamkniętym trzeba licencji komercyjnej |
| `docling` | analiza układu modelem, tabele, nagłówki, wyjście markdown/JSON | wymaga modeli, wolniejsze, potrzebuje GPU przy skali |

Kontrole, które trzeba wykonać na każdym pliku:

- **Ile znaków na stronę.** Poniżej ~50 znaków przy stronie A4 to skan albo pusta strona.
  Kieruj do OCR, nie indeksuj jako pustkę.
- **Udział znaków niedrukowalnych i zastępczych** (`U+FFFD`, `U+0000`). Wysoki oznacza
  uszkodzone kodowanie czcionki — tekst wygląda poprawnie w czytniku, a wyciągnięty
  jest śmieciem. Częste w starszych plikach z polskimi diakrytykami.
- **Czy tekst jest po polsku.** Jeśli wykryty język to np. `hr` albo `sl` przy polskim
  dokumencie, prawie zawsze oznacza to zgubione diakrytyki.
- **Wielokolumnowość.** Naiwne wyciągnięcie z układu dwukolumnowego przeplata zdania
  z lewej i prawej kolumny. Wynik jest gramatycznie bezsensowny i osadza się w losowe
  miejsce przestrzeni. Wykrycie: udział zdań bez czasownika, albo po prostu użycie
  parsera z analizą układu.

```python
import pypdfium2 as pdfium

def wyciagnij_pdf(sciezka: str) -> tuple[str, list[dict], bool]:
    doc = pdfium.PdfDocument(sciezka)
    czesci, strony, pozycja = [], [], 0
    for nr, strona in enumerate(doc, start=1):
        tekst = strona.get_textpage().get_text_range()
        strony.append({"nr": nr, "offset_od": pozycja, "offset_do": pozycja + len(tekst)})
        czesci.append(tekst)
        pozycja += len(tekst) + 1
    pelny = "\n".join(czesci)
    znakow_na_strone = len(pelny) / max(len(strony), 1)
    wymaga_ocr = znakow_na_strone < 50
    return pelny, strony, wymaga_ocr
```

### PDF bez warstwy tekstowej (skany)

Trzy drogi, rosnąco pod względem kosztu i jakości:

| Droga | Koszt | Jakość na polskim | Uwagi |
|---|---|---|---|
| Tesseract 5 z `-l pol` | ~0 (CPU) | przyzwoita na czystych skanach, słaba na złych | wymaga prostowania i binaryzacji przed |
| Silnik OCR w chmurze (Azure Document Intelligence, Google Document AI, Mistral OCR) | grosze za stronę | dobra, także tabele i układ | dane opuszczają infrastrukturę — sprawdź podstawę prawną |
| Model wielomodalny (Claude, Gemini) na obrazach stron | najdroższa | najlepsza na trudnych układach i pismach ręcznych | ryzyko halucynacji — model może „poprawić” tekst |

Ostatnia opcja ma cechę dyskwalifikującą w kontekście prawniczym: model wielomodalny
**może zmienić treść**, uzupełniając to, czego nie widzi. Jeśli używasz go do OCR akt,
musisz zachować obraz strony i traktować transkrypcję jako wtórną, a nie jako oryginał.

Przygotowanie obrazu przed OCR ma większy wpływ niż wybór silnika: rozdzielczość ≥ 300 dpi,
prostowanie (deskew), usunięcie szumu, binaryzacja adaptacyjna, wykrycie i obrót stron
do góry nogami. Skan 150 dpi po prostowaniu bije skan 300 dpi krzywy.

Zapisuj **pewność OCR** per strona. Fragmenty ze średnią pewnością poniżej progu
(np. 0,80) oznaczaj i pokazuj przy przypisie ostrzeżenie „tekst rozpoznany automatycznie,
zweryfikuj z oryginałem”. W dokumentach prawniczych to nie jest ozdobnik.

Skanów bez warstwy tekstowej **nie da się cytować przez Citations API Anthropica** —
ta funkcja wymaga tekstu wyekstrahowanego. Cytat musi więc pochodzić z twojej własnej
transkrypcji, z zachowanym odsyłaczem do obrazu strony.

### DOCX

`python-docx` daje akapity ze stylami — z tego odtwarzasz hierarchię nagłówków. Trzy rzeczy,
które trzeba wyciągnąć osobno, bo są poza głównym strumieniem:

- **przypisy dolne i końcowe** (`word/footnotes.xml`) — w dokumentach prawniczych niosą
  odesłania do orzecznictwa, czyli najcenniejszą treść;
- **komentarze** (`word/comments.xml`) — zwykle NIE indeksować, to notatki wewnętrzne;
- **zmiany śledzone** — zdecyduj i zapisz decyzję: wersja z przyjętymi zmianami czy
  z odrzuconymi. Indeksowanie surowego XML-a daje tekst zawierający obie wersje naraz.

DOCX nie ma stron — numeracja powstaje dopiero przy renderowaniu. Jeśli przypis ma
wskazywać stronę, konwertuj do PDF-a i z niego bierz mapę stron.

### HTML i e-mail

HTML: usuń nawigację, stopkę, skrypty, style; zachowaj `h1`–`h6`, listy, tabele.
`trafilatura` albo `readability` do wydzielenia treści głównej, potem konwersja do markdown.

E-mail: parsuj `.eml`/`.msg`, oddziel treść od cytowanego wątku (linie zaczynające się od
`>`, bloki „Od: ... Wysłano: ...”). **Cytowany wątek indeksowany osobno tworzy dziesiątki
niemal identycznych fragmentów**, które wypychają z wyników wszystko inne. Załączniki
przetwarzaj jako osobne dokumenty z relacją „załącznik do wiadomości X”.

## Zachowanie struktury

Wyjściem parsera powinien być markdown, nie płaski tekst. Powody są praktyczne:

- Nagłówki dają granice fragmentacji i pozwalają zbudować ścieżkę kontekstową
  („Umowa najmu > § 7 Kaucja > ust. 3”).
- Tabela w markdownie jest czytelna dla modelu; ta sama tabela jako ciąg liczb
  rozdzielonych spacjami jest bezużyteczna.
- Listy numerowane zachowują numerację ustępów i punktów, co w tekstach prawnych
  jest częścią treści, a nie formatowania.

Reguły:

- **Tabela nigdy nie jest dzielona między fragmenty.** Jeśli nie mieści się w limicie,
  fragmentem jest tabela w całości (nawet dużym), z nagłówkiem kolumn powtórzonym.
- Nagłówek sekcji jest **powtarzany na początku każdego fragmentu z tej sekcji**.
  To najtańsza możliwa kontekstualizacja i działa zaskakująco dobrze.
- Przypisy dolne dołączane na końcu fragmentu, w którym jest odsyłacz, a nie na końcu
  strony i nie osobno.
- Numeracja jednostek redakcyjnych (§, ust., pkt, lit., art.) jest częścią treści —
  nie usuwaj jej jako „formatowania”. Bez niej model nie może zacytować podstawy.

## Normalizacja

Robisz dokładnie tyle, ile trzeba, i zapisujesz, co zrobiłeś. Nadmierna normalizacja
niszczy możliwość weryfikacji cytatu.

Obowiązkowe:
- Unicode NFC (polskie diakrytyki bywają w PDF-ach jako litera + znak łączący; bez NFC
  „ą” złożone i „ą” pojedyncze to dla wyszukiwarki dwa różne słowa).
- Ujednolicenie końców linii do `\n`.
- Usunięcie twardych spacji ` `, myślników miękkich `­`, znaków zerowej
  szerokości.
- Sklejenie wyrazów przenoszonych na końcu linii (`prze-\nnoszenie` → `przenoszenie`),
  ale **tylko** gdy druga część zaczyna się małą literą i połączenie daje słowo
  ze słownika — inaczej niszczysz łączniki w nazwiskach i terminach.
- Usunięcie powtarzalnych nagłówków i stopek stron (wykrycie: ten sam ciąg na ≥ 60% stron).
  Bez tego numer sprawy w stopce trafia do każdego fragmentu i psuje statystyki BM25.

Czego NIE robić:
- Nie zmieniaj wielkości liter w tekście przechowywanym (małe litery stosuj tylko
  w indeksie wyszukiwania, nie w tym, co pokazujesz i cytujesz).
- Nie usuwaj diakrytyków z treści (usuwanie diakrytyków należy do konfiguracji FTS
  przez `unaccent`, nie do danych).
- Nie usuwaj interpunkcji ani cyfr. „art. 415 k.c.” bez kropek i cyfr przestaje istnieć.
- Nie zwijaj wszystkich białych znaków w pojedynczą spację, jeśli chcesz zachować offsety
  do oryginału. Jeśli musisz — zapisz mapowanie offsetów przed i po.

## Wykrywanie języka

Korpus prawniczy w Polsce zawiera dokumenty polskie, angielskie umowy, wyroki TSUE,
niemieckie akty spółek. To ma dwa skutki:

1. Konfiguracja FTS musi być dobrana per dokument (`to_tsvector('polski', ...)`
   vs `('english', ...)`). Jedna kolumna `tsvector` z wybraną dynamicznie konfiguracją
   plus kolumna `jezyk` do filtrowania.
2. Model embeddingowy musi być **wielojęzyczny**, żeby polskie zapytanie znalazło
   angielski dokument o tej samej treści. Modele jednojęzyczne osadzają języki w rozłącznych
   obszarach przestrzeni.

Wykrywanie: `lingua-py` (wolniejsze, dokładniejsze na krótkich tekstach) albo `fasttext`
`lid.176`. Wykrywaj na całym dokumencie i na fragmencie — dokument może być mieszany
(polska umowa z angielskim załącznikiem).

Pułapka: teksty prawnicze z dużą liczbą łacińskich zwrotów bywają klasyfikowane jako
łacina lub włoski. Ustaw próg pewności i przy niepewności przyjmij język dokumentu
nadrzędnego.

## Deduplikacja

Trzy poziomy, każdy łapie co innego:

| Poziom | Metoda | Co łapie |
|---|---|---|
| Plik | SHA-256 zawartości | ten sam plik wgrany dwa razy |
| Tekst | SHA-256 tekstu po normalizacji | ten sam dokument w PDF i DOCX; ten sam skan z innym OCR |
| Fragment | MinHash / SimHash, próg Jaccarda ~0,9 | wzorce umów, powtarzane pouczenia, cytowany wątek maila |

Trzeci poziom jest w korpusie prawniczym niezbędny. Bez niego zapytanie o klauzulę
z wzorca umowy zwraca dziesięć razy tę samą klauzulę z dziesięciu umów i wypycha z top-k
wszystko, co mogłoby być użyteczne.

Ważne: **duplikaty oznaczasz, a nie usuwasz.** Fakt, że identyczna klauzula występuje
w 40 umowach, jest informacją. Właściwa obsługa to zwinięcie w wynikach wyszukiwania
(„ten fragment występuje w 40 dokumentach — pokaż listę”), nie usunięcie z indeksu.

```python
from datasketch import MinHash, MinHashLSH

lsh = MinHashLSH(threshold=0.9, num_perm=128)

def podpis(tekst: str) -> MinHash:
    m = MinHash(num_perm=128)
    tokeny = tekst.lower().split()
    for i in range(len(tokeny) - 4):
        m.update(" ".join(tokeny[i:i+5]).encode("utf-8"))
    return m
```

## Metadane

Minimalny zestaw przy każdym fragmencie. Brak któregokolwiek pola oznacza konkretną
niemożność później:

| Pole | Bez niego nie da się |
|---|---|
| `dokument_id` | wskazać źródła |
| `wersja_dok` | odróżnić aktualnej treści od poprzedniej wersji |
| `strona_od`, `strona_do` | podać przypisu do strony |
| `offset_od`, `offset_do` | zweryfikować cytatu ani podświetlić go w oryginale |
| `nr` (kolejność) | pokazać sąsiednich fragmentów ani odtworzyć kolejności |
| `sciezka_naglowkow` | pokazać kontekstu („§ 7 ust. 3”) |
| `data_dokumentu` | filtrować po czasie ani rozstrzygać, która wersja przepisu obowiązuje |
| `zrodlo` (system, ścieżka) | odtworzyć indeksu ani udowodnić pochodzenia |
| `klucz_dostepu` | filtrować uprawnień |
| `model_emb`, `wymiar` | zmigrować modelu |
| `parser`, `ocr`, `ocr_pewnosc` | ocenić wiarygodności tekstu |

**Uprawnienia** zasługują na osobne zdanie. Trzy sposoby, w kolejności bezpieczeństwa:

1. `JOIN` do tabeli uprawnień w tej samej bazie, w tym samym zapytaniu — jedyny sposób,
   który jest zawsze aktualny. To główny argument za pgvector.
2. Denormalizowana lista uprawnionych ról w metadanych fragmentu — działa, ale wymaga
   propagacji zmian ACL do indeksu; zaplanuj opóźnienie i procedurę wymuszonego odświeżenia.
3. Odsiew po pobraniu wyników — **niedopuszczalne**. Nie tylko dlatego, że gubi wyniki (patrz
   `references/engineering-core/04-bazy-i-rag/references/pgvector.md`), ale dlatego, że dokument już
   przeszedł przez pamięć procesu i wystarczy jeden błąd w kodzie, żeby wyciekł.

Nigdy nie realizuj uprawnień instrukcją w prompcie („nie pokazuj dokumentów oznaczonych
jako poufne”). Model to zignoruje przy odpowiednio sformułowanym pytaniu.

## Aktualizacja przyrostowa i usuwanie

To jest najczęściej pomijana część potoku i najczęstsza przyczyna tego, że po pół roku
indeks nie odpowiada rzeczywistości.

### Wykrywanie zmian

```sql
-- dokument jest do przetworzenia, gdy:
--   nie ma go w indeksie, albo
--   suma kontrolna pliku się zmieniła, albo
--   zmienił się parser/model (wersje zapisane przy fragmentach)
SELECT d.id
FROM dokumenty d
LEFT JOIN dokumenty_tekst t ON t.dokument_id = d.id
WHERE t.dokument_id IS NULL
   OR t.parser_wersja <> $1
   OR EXISTS (
        SELECT 1 FROM fragmenty f
        WHERE f.dokument_id = d.id AND f.model_emb <> $2
      );
```

### Aktualizacja dokumentu

Właściwa procedura, w jednej transakcji:

```sql
BEGIN;
UPDATE dokumenty SET wersja = wersja + 1, suma = $2 WHERE id = $1 RETURNING wersja;
DELETE FROM fragmenty WHERE dokument_id = $1 AND wersja_dok < $nowa;
INSERT INTO fragmenty (...) VALUES (...);   -- nowe fragmenty z nową wersja_dok
COMMIT;
```

Częsty błąd: wstawienie nowych fragmentów bez usunięcia starych. W indeksie zostają dwa
pokolenia, wyszukiwanie zwraca oba, a użytkownik dostaje przypis do treści, której już
nie ma w dokumencie. W kontekście prawniczym to jest błąd dyskwalifikujący system.

Wariant z zachowaniem historii (potrzebny, gdy trzeba odpowiedzieć „co było w umowie
w marcu”): nie usuwaj starych fragmentów, tylko oznacz je `obowiazuje_do = now()`
i dodaj do filtra zapytania `WHERE obowiazuje_do IS NULL`. Kosztuje miejsce, daje
możliwość zapytań na dowolny moment.

### Usuwanie

- `ON DELETE CASCADE` z dokumentu na fragmenty — usunięcie musi być atomowe.
- Jeśli indeks wektorowy jest w osobnym systemie: usuwanie **przed** potwierdzeniem
  usunięcia użytkownikowi, z kolejką ponowień. Rozjazd w drugą stronę (dokument usunięty
  z bazy, obecny w indeksie) oznacza pokazywanie treści, której nie wolno pokazywać.
- Po masowym usunięciu: `VACUUM` na tabeli fragmentów, inaczej indeks HNSW nadal
  przechodzi przez martwe węzły.

### Kolejkowanie

Indeksacja musi być odporna na przerwanie w połowie. Wzorzec: tabela zadań w Postgresie z `FOR
UPDATE SKIP LOCKED` (patrz `references/engineering-core/04-bazy-i-rag/references/postgres.md`), stan
per dokument (`oczekuje`, `w_toku`, `gotowe`, `blad`), licznik prób i zapisany komunikat błędu.

Dokumenty, które padły, muszą być widoczne. Cichy `try/except: pass` przy parsowaniu
oznacza korpus, w którym brakuje 8% dokumentów i nikt o tym nie wie. Raport
„przetworzono 9 812 z 10 000, 188 błędów, najczęstszy: brak warstwy tekstowej” jest
obowiązkowym wynikiem indeksacji.
