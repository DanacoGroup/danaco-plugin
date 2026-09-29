# Plik referencyjny paczki — kształt wiążący

Plik ustala kształt obowiązujący pliki w katalogach `references/` paczek tego pluginu.
Standard redakcyjny zbioru `docs/` (`references/standard-redakcyjny-i-jezykowy.md`
i jego części) opisuje opracowania produktowe i wymaga metryki produktowej, metryki
dokumentu, spisu treści oraz stopki — wymogów, których czterokilobajtowa karta
referencyjna nie spełni i spełniać nie ma. Ten plik zamyka tę lukę: karta referencyjna
ma własną, węższą klasę dokumentu.

Zakres: pliki `skills/<paczka>/references/**` oraz `shared/**`. Poza zakresem: pliki
`skills/<paczka>/SKILL.md` — te mają frontmatter i własne wymagania systemu paczek.

---

## 1. Kształt minimalny

| Element | Postać wiążąca |
|---|---|
| Nagłówek H1 | `# {Przedmiot} — {rodzaj}`, gdzie rodzaj należy do zamkniętego zbioru: `procedura`, `karta`, `indeks modułu`, `przegląd modułu`, `spis`, `standard współdzielony`. Rodzaj wolno pominąć, gdy przedmiot sam go nazywa (`# Spis modułów engineering-core`) |
| Zdanie granicy | pierwszy akapit, jedno do trzech zdań: co plik obejmuje, czego nie obejmuje i gdzie leży materiał sąsiedni — wskazany ścieżką pliku, nie nazwą paczki |
| Frontmatter YAML | zakazany; pole `name:` w pliku referencyjnym stwarza pozór drugiego punktu wejścia paczki |
| Numeracja rozdziałów | dowolna, ale jednolita w obrębie jednego katalogu modułu; numeracja poza numeracją rozdziałów jest zakazana (rozdz. 7.1 standardu) |
| Sekcja końcowa | „Kontrola przed oddaniem” albo „Typowe błędy modeli LLM” — wykaz sprawdzalny, nie podsumowanie prozą |
| Łamanie wiersza | twarde, 78–100 znaków, poza tabelami i blokami kodu |
| Metryka produktowa, metryka dokumentu, stopka produktowa | zakazane |
| Emoji i ozdobniki | zakazane |

Wzorcem do naśladowania są karty języków w `skills/kodowanie/references/jezyki-programowania/`
— dwadzieścia plików o jednym kształcie i sześciu zapowiedzianych sekcjach.

---

## 2. Odsyłacze

| Zasada | Wymóg |
|---|---|
| Punkt odniesienia | ścieżka liczona od katalogu paczki (`skills/<paczka>/`), niezależnie od tego, jak głęboko leży plik odsyłający |
| Wyjście poza paczkę | przedrostek `../` na każdy poziom: standard współdzielony to `../../wspolne/standardy-zawodowe/<plik>.md`, inna paczka to `../<paczka>/SKILL.md` |
| Katalog jako cel | zakazany — odsyłacz wskazuje plik, żeby czytający nie musiał wykonywać listowania |
| Nazwa paczki bez ścieżki | zakazana jako jedyna wskazówka; nazwa paczki wolno podać razem ze ścieżką pliku |
| Cel istniejący | odsyłacz do pliku nieistniejącego jest usterką; dotyczy to również nazw paczek z rodziny sprzed konsolidacji |
| Nazwa pliku bez katalogu | dopuszczalna wyłącznie w tabeli, której nagłówek podaje katalog wspólny dla całej kolumny |

---

## 3. Osiągalność

Każdy plik w `references/` musi mieć ścieżkę wejścia: z `SKILL.md` swojej paczki, z pliku
spisu albo z innego pliku referencyjnego przywołanego wcześniej w tym łańcuchu. Plik
nieosiągalny nie jest materiałem rezerwowym — jest balastem, bo nic go nie wczyta,
a jego objętość i tak wchodzi do dystrybucji.

Kontrola: prześledzić odnośniki od `skills/*/SKILL.md` w głąb i porównać zbiór osiągnięty
ze zbiorem plików w drzewie. Różnica musi być pusta.

---

## 4. Kontrola przed oddaniem

1. Nagłówek H1 z rodzajem ze zbioru zamkniętego, zdanie granicy w pierwszym akapicie.
2. Brak frontmatteru, brak metryk, brak stopki produktowej, brak emoji.
3. Każdy odnośnik wskazuje istniejący plik, ścieżką od katalogu paczki.
4. Plik jest osiągalny z `SKILL.md` swojej paczki albo z pliku spisu.
5. Wiersze poza tabelami i blokami kodu nie przekraczają 100 znaków.
6. Nazwa pliku w kebab-case, opisująca zawartość; żadnych oznaczeń literowo-numerycznych.
7. Kodowanie UTF-8 bez BOM, końce linii LF, brak bajtów sterujących.
