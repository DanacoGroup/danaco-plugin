# Ewaluacja RAG

Bez pomiaru każda zmiana w potoku jest zakładem. „Dodaliśmy reranker, jest lepiej”
to nie jest wynik — to wrażenie. Ten plik opisuje, jak zbudować pomiar, który pozwala
podejmować decyzje.

Wersje narzędzi sprawdzone 04.08.2026: `ragas` 0.4.3 (13.01.2026), `deepeval` 4.1.5,
`arize-phoenix` 19.15.0, `trulens-eval` 2.11.0.

## Zbiór testowy

### Ile pytań

| Cel | Liczba pytań |
|---|---|
| Wykrycie rażących błędów podczas budowy | 20–30 |
| Porównanie wariantów (model, fragmentacja, reranker) | **50–100** |
| Testy regresyjne w CI | 100–200 |
| Rozstrzyganie różnic rzędu 1–2 pp | 300+ |

Poniżej 50 pytań różnice do 10 pp mieszczą się w szumie i nie wolno na ich podstawie
podejmować decyzji. 100 dobrze dobranych pytań jest warte więcej niż 1000 wygenerowanych
automatycznie.

### Skąd wziąć pytania

W kolejności wartości:

1. **Realne pytania użytkowników** z dzienników wyszukiwania albo z rozmowy z klientem.
   Jedna godzina z prawnikiem, który spisze 40 pytań, jakie faktycznie zadaje aktom,
   jest najlepszą inwestycją w cały projekt.
2. Pytania odtworzone z historycznych zadań (o co pytano przy poprzednich sprawach).
3. Generowane przez LLM z fragmentów korpusu — tylko jako uzupełnienie i **po przeglądzie
   ręcznym**. Pytania generowane z fragmentu mają wbudowaną odpowiedź w sformułowaniu
   i mierzą łatwiejsze zadanie niż rzeczywiste.

Zbiór musi zawierać, w proporcjach zbliżonych do realnych:

| Rodzaj | Udział | Przykład |
|---|---|---|
| Faktograficzne, jedno źródło | ~40% | „Jaka jest wysokość kaucji w umowie z ACME?” |
| Wielodokumentowe | ~20% | „Czy kaucja została zmieniona aneksem?” |
| Z sygnaturą / numerem / nazwiskiem | ~15% | „Co wynika z wyroku II CSK 123/19?” |
| Czasowe | ~10% | „Jaki termin obowiązywał w marcu 2024?” |
| **Bez odpowiedzi w korpusie** | **~15%** | „Jaka jest wysokość kary umownej?” (nie ma takiego postanowienia) |

Ostatnia kategoria jest najczęściej pomijana i najważniejsza. System, który nie umie
powiedzieć „nie wiem”, jest w kancelarii niebezpieczny.

### Format

```json
{
  "id": "q_017",
  "pytanie": "W jakim terminie podlega zwrotowi kaucja po zmianie aneksem?",
  "kategoria": "wielodokumentowe",
  "zlote_zrodla": [
    {"dokument_id": 412, "offset_od": 8210, "offset_do": 8390, "strona": 4},
    {"dokument_id": 519, "offset_od": 1100, "offset_do": 1250, "strona": 1}
  ],
  "oczekiwana_odpowiedz": "14 dni od zwrotu lokalu, zgodnie z aneksem nr 1 z 4.09.2024, który zmienił pierwotny termin 30-dniowy.",
  "musi_zawierac": ["14 dni", "aneks"],
  "nie_moze_zawierac": ["30 dni od zwrotu lokalu"],
  "dopuszczalna_odmowa": false
}
```

**Złote źródło zapisuj jako zakres znakowy w dokumencie, nigdy jako identyfikator
fragmentu.** Identyfikator fragmentu unieważnia cały zbiór testowy przy pierwszej zmianie
fragmentacji — czyli dokładnie wtedy, gdy zbiór jest najbardziej potrzebny.

Budowa zbioru dla 100 pytań to realnie 1–2 dni pracy z osobą znającą dziedzinę.
To jest koszt, który zwraca się przy pierwszej decyzji o zmianie modelu.

## Metryki wyszukiwania

Liczone przed generowaniem, na samych wynikach wyszukiwarki. Tanie (bez wywołań LLM),
deterministyczne, powtarzalne. **To jest podstawowy pomiar w RAG.**

| Metryka | Co mierzy | Kiedy używać |
|---|---|---|
| **recall@k** | czy właściwy fragment znalazł się w top-k | główna metryka; k = liczba fragmentów podawanych modelowi |
| precision@k | jaka część zwróconych jest trafna | gdy rozpraszacze psują generowanie |
| **MRR** | odwrotność pozycji pierwszego trafienia | gdy liczy się, żeby trafny był wysoko |
| **nDCG@k** | jakość uporządkowania z uwzględnieniem stopnia trafności | do porównywania rerankerów |
| Hit@1 | czy pierwszy wynik jest trafny | interfejs pokazujący jeden wynik |

```python
def dopasowanie(wynik, zlote) -> bool:
    return any(
        wynik["dokument_id"] == z["dokument_id"]
        and wynik["offset_od"] < z["offset_do"]
        and wynik["offset_do"] > z["offset_od"]
        for z in zlote
    )

def recall_at_k(wyniki, zlote, k) -> float:
    trafione = {
        (z["dokument_id"], z["offset_od"])
        for z in zlote
        for w in wyniki[:k]
        if dopasowanie(w, [z])
    }
    return len(trafione) / len(zlote)

def mrr(wyniki, zlote) -> float:
    for i, w in enumerate(wyniki, start=1):
        if dopasowanie(w, zlote):
            return 1.0 / i
    return 0.0

def ndcg_at_k(wyniki, zlote, k) -> float:
    import math
    dcg = sum(1 / math.log2(i + 1)
              for i, w in enumerate(wyniki[:k], start=1) if dopasowanie(w, zlote))
    idcg = sum(1 / math.log2(i + 1) for i in range(1, min(len(zlote), k) + 1))
    return dcg / idcg if idcg else 0.0
```

Progi akceptacji dla systemu produkcyjnego:

| Metryka | Próg | Uwaga |
|---|---|---|
| recall@10 (po reranku) | **≥ 0,90** | poniżej 0,85 generowanie nie ma z czego odpowiadać |
| recall@50 (przed rerankiem) | ≥ 0,95 | reranker nie naprawi tego, czego nie dostał |
| recall indeksu ANN vs wyszukiwanie dokładne | ≥ 0,95 | osobny pomiar, patrz `references/engineering-core/04-bazy-i-rag/references/pgvector.md` |
| MRR@10 | ≥ 0,7 | |

Rozdziel te trzy pomiary. Niski recall@10 przy wysokim recall@50 to problem rerankera.
Niski recall@50 przy wysokim recall ANN to problem modelu embeddingowego albo hybrydy.
Niski recall ANN to problem strojenia indeksu.

## Metryki generowania

Droższe (wymagają LLM jako sędziego) i mniej stabilne. Liczysz je **dopiero** gdy
metryki wyszukiwania są na poziomie.

| Metryka | Pytanie, na które odpowiada |
|---|---|
| **Wierność** (faithfulness / groundedness) | czy każde twierdzenie w odpowiedzi wynika z podanego materiału |
| **Trafność odpowiedzi** (answer relevancy) | czy odpowiedź odnosi się do zadanego pytania |
| **Kompletność** | czy odpowiedź zawiera wszystkie istotne elementy oczekiwanej |
| **Poprawność cytowań** | czy przypisy wskazują fragmenty faktycznie zawierające twierdzenie |
| Trafność kontekstu | czy podane fragmenty były potrzebne |
| Odsetek poprawnych odmów | ile pytań bez odpowiedzi zakończyło się prawidłową odmową |

Dwie ostatnie są w systemie prawniczym równie ważne jak wierność.

Część z tych rzeczy da się zmierzyć **bez LLM**, deterministycznie — i wtedy pomiar jest
darmowy, powtarzalny i wiarygodny:

```python
def metryki_deterministyczne(odpowiedz, przypadek, fragmenty):
    return {
        "zawiera_wymagane": all(f.casefold() in odpowiedz.casefold()
                                for f in przypadek["musi_zawierac"]),
        "brak_zakazanych": not any(f.casefold() in odpowiedz.casefold()
                                   for f in przypadek["nie_moze_zawierac"]),
        "odmowa": "nie ma podstawy do odpowiedzi" in odpowiedz.casefold(),
        # kontrole z generowanie-i-przypisy.md:
        "cytaty_doslowne": sprawdz_odpowiedz(odpowiedz, fragmenty)["niezweryfikowane_cytaty"] == [],
        "przypisy_istnieja": sprawdz_odpowiedz(odpowiedz, fragmenty)["nieistniejace_id"] == [],
    }
```

Zaczynaj od tych. `musi_zawierac` / `nie_moze_zawierac` na 100 pytaniach wyłapuje
większość regresji taniej i pewniej niż sędzia-model.

## Sędzia-model i jego pułapki

| Pułapka | Objaw | Przeciwdziałanie |
|---|---|---|
| Preferencja własnych wyjść | ten sam model ocenia wyżej odpowiedzi swojej rodziny | sędzia z innej rodziny niż generator |
| Preferencja długości | dłuższe odpowiedzi dostają wyższe oceny | w kryteriach jawny zakaz nagradzania długości; kontrola korelacji ocena–długość |
| Efekt kolejności | pierwsza z porównywanych opcji wygrywa | losuj kolejność; oceniaj obie kolejności i uśredniaj |
| Niestabilność | ta sama para dostaje różne oceny | `temperature=0`, 3 przebiegi, mediana |
| Skala ciągła 1–10 | model używa 7 i 8, reszta martwa | skala binarna albo trójstopniowa z jawnymi definicjami |
| Ocena bez rozbicia | jedna liczba „jakość” nic nie mówi | osobno: wierność, trafność, kompletność |
| Brak kalibracji | nie wiadomo, czy sędzia się myli | **50 przypadków ocenionych ręcznie**, porównanie zgodności |

**Kalibracja jest obowiązkowa.** Oceń ręcznie 50 przypadków, policz zgodność z sędzią.
Poniżej ~80% zgodności ocen sędzia jest nieużyteczny — popraw kryteria albo zmień model.
Bez tego kroku optymalizujesz pod preferencje sędziego, a nie pod jakość.

Prompt sędziego, który działa lepiej niż ogólny:

```
Oceń, czy ODPOWIEDŹ jest w pełni oparta na MATERIALE.

Procedura:
1. Wypisz każde twierdzenie o faktach zawarte w odpowiedzi.
2. Dla każdego wskaż fragment materiału, który je potwierdza, albo napisz BRAK.
3. Werdykt: PEŁNA (wszystkie potwierdzone) / CZĘŚCIOWA (co najmniej jedno BRAK,
   ale bez sprzeczności) / NARUSZONA (co najmniej jedno twierdzenie sprzeczne
   z materiałem lub całkowicie spoza niego).

Nie oceniaj stylu, długości ani przydatności. Oceniasz wyłącznie oparcie w materiale.
```

Wymuszenie wypisania twierdzeń przed werdyktem daje wyraźnie stabilniejsze oceny niż
prośba o samą liczbę — i pozwala sprawdzić rozumowanie sędziego przy kalibracji.

## Narzędzia

| Narzędzie | Wersja | Mocna strona | Uwaga |
|---|---|---|---|
| **RAGAS** | 0.4.3 (13.01.2026) | gotowe metryki RAG (wierność, trafność, precyzja i recall kontekstu), generowanie zbiorów syntetycznych | **API zmienione względem 0.1/0.2** — przykłady z sieci sprzed 2025 nie zadziałają |
| **DeepEval** | 4.1.5 | metryki jako testy `pytest`, dobrze wchodzi do CI | |
| **Arize Phoenix** | 19.15.0 | śledzenie i obserwowalność (OpenTelemetry), przegląd realnych zapytań | najlepsze do produkcji, nie do CI |
| **TruLens** | 2.11.0 | „triada RAG”: kontekst–odpowiedź–pytanie | |
| **MLflow** | — | ewaluacja agentów i wersjonowanie przebiegów | gdy już używasz MLflow |
| własny skrypt | — | pełna kontrola, zero zależności | **wystarcza w 80% przypadków** |

Rekomendacja: metryki wyszukiwania i kontrole deterministyczne pisz sam (30 linii,
powyżej), a narzędzie zewnętrzne dokładaj dopiero na metryki generowania oparte o LLM.
Framework nie zastąpi zbioru testowego, a bez zbioru testowego jest bezużyteczny.

## Testy regresyjne

Każda z tych zmian wymaga pełnego przebiegu ewaluacji, bo każda potrafi zepsuć
system w sposób niewidoczny na oko:

- model embeddingowy (także zmiana wersji tego samego modelu),
- strategia lub rozmiar fragmentacji,
- parametry indeksu (`m`, `ef_construction`, `ef_search`, `lists`, `probes`),
- reranker albo jego brak,
- liczby k na dowolnym etapie,
- prompt generowania (nawet zmiana jednego zdania),
- model generujący (także „drobna” zmiana wersji),
- konfiguracja FTS, słownik, lista stop-słów,
- parser dokumentów i jego wersja.

```yaml
# ci: uruchamiane przy zmianie w potoku
- uruchom ewaluację na 100 pytaniach
- porównaj z zapisaną wartością odniesienia
- BLOKUJ, gdy:
    recall@10               spadł o > 2 pp
    odsetek poprawnych odmów spadł o > 5 pp
    cytaty niedosłowne       pojawiły się w ogóle
    przypisy do nieistniejących fragmentów  pojawiły się w ogóle
- OSTRZEŻ, gdy:
    koszt na zapytanie wzrósł o > 20%
    opóźnienie p95 wzrosło o > 30%
```

Wartość odniesienia trzymaj w repozytorium (plik JSON z wynikami), nie w pamięci zespołu.

## Obserwowalność w produkcji

Zbiór testowy mierzy to, co przewidziałeś. Produkcja pokazuje to, czego nie.

Loguj przy każdym zapytaniu:

| Pole | Po co |
|---|---|
| zapytanie oryginalne i przepisane | analiza, czy przepisywanie nie psuje |
| identyfikatory zwróconych fragmentów, wyniki przed i po reranku | odtworzenie przypadku |
| identyfikator wersji indeksu, modelu, promptu | bez tego nie porównasz okresów |
| liczba tokenów wejścia/wyjścia, trafienia cache | koszt |
| opóźnienie na etap (osadzenie, wyszukiwanie, rerank, generowanie) | gdzie jest wąskie gardło |
| wynik kontroli programowej (cytaty, przypisy, pokrycie) | jakość bez sędziego |
| czy nastąpiła odmowa | wzrost odsetka odmów = coś się zepsuło w indeksacji |
| sygnał od użytkownika (kciuk, kliknięcie w przypis, kopiowanie) | najcenniejszy sygnał |

Sygnały alarmowe:
- **wzrost odsetka odmów** — najczęściej indeksacja przestała działać;
- **spadek klikalności przypisów** — użytkownicy przestali ufać odpowiedziom;
- wzrost udziału zapytań z zerową liczbą wyników z gałęzi BM25 — coś zepsuło konfigurację FTS;
- spadek średniego wyniku rerankera — korpus lub rozkład pytań się zmienił.

Cotygodniowy przegląd 20 losowych rozmów przez osobę z dziedziny wykrywa więcej niż
dowolny automat. Wpisz to do harmonogramu, nie do dobrych chęci.

## Koszt na zapytanie

Policz i pokaż klientowi. Przykład dla typowej konfiguracji (fragmenty 600 tokenów,
10 podanych do modelu, model klasy Sonnet):

| Składnik | Tokeny | Koszt |
|---|---|---|
| Osadzenie zapytania (`voyage-4`, 0,06/M) | 30 | 0,000002 USD |
| Wyszukiwanie w pgvector | — | ~0 (własna infrastruktura) |
| Reranking 50 × 600 tok. (`rerank-2.5-lite`, 0,02/M) | 30 000 | 0,0006 USD |
| Generowanie: wejście 7 000 tok. (bez cache, 3 USD/M) | 7 000 | 0,021 USD |
| Generowanie: wyjście 800 tok. (15 USD/M) | 800 | 0,012 USD |
| **Razem** | | **~0,034 USD** |

Wnioski, które warto powiedzieć wprost:
- **Generowanie to ~97% kosztu.** Optymalizowanie bazy wektorowej i embeddingów pod kątem
  ceny jest stratą czasu.
- Największa dostępna oszczędność to buforowanie promptu (odczyt 0,1× wejścia) i podawanie
  mniejszej liczby fragmentów — a to drugie zwykle podnosi też jakość.
- Przy 10 tys. zapytań miesięcznie to ~340 USD. Przy 1 mln — 34 tys. USD. Próg, przy którym
  warto rozważyć mniejszy model do prostych pytań, leży gdzieś w okolicy 100 tys. zapytań
  miesięcznie.

Koszt jednorazowy indeksacji policz osobno: parsowanie z OCR + osadzenie + ewentualna
kontekstualizacja (~1 USD za 1 mln tokenów dokumentów). Dla 1 mln stron to rząd
kilkuset dolarów za osadzenie i kontekstualizację, plus koszt OCR, który zwykle dominuje.

## Antywzorce

| Antywzorzec | Konsekwencja |
|---|---|
| Ocena „na oko” na 5 pytaniach | każda zmiana wygląda na poprawę |
| Złote źródło jako identyfikator fragmentu | zbiór testowy unieważniony przy zmianie fragmentacji |
| Brak pytań bez odpowiedzi w zbiorze | nie wiesz, czy system halucynuje |
| Sędzia z tej samej rodziny co generator | zawyżone oceny |
| Sędzia bez kalibracji ręcznej | optymalizujesz pod preferencje sędziego |
| Metryki generowania przed naprawą wyszukiwania | mierzysz szum |
| Jedna metryka „jakość” | nie wiadomo, co poprawiać |
| Ewaluacja tylko przed wdrożeniem | rozkład pytań w produkcji jest inny niż w zbiorze |
| Bufor włączony podczas ewaluacji | mierzysz bufor, nie system |
| Brak zapisanej wartości odniesienia w repozytorium | nie ma z czym porównać po trzech miesiącach |
