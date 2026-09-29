# Kiedy nie RAG

RAG to najbardziej przereklamowany element stosu AI. Ma sens, ale zakres tego sensu
jest węższy, niż wynika z popularnych opracowań. Ten plik podaje alternatywy i progi,
przy których każda z nich wygrywa.

Kolejność czytania: ten plik **przed** budową potoku, nie po.

## Test wstępny

Cztery pytania. Jeśli mniej niż dwie odpowiedzi wypadają po stronie „RAG”,
zbuduj coś prostszego.

| Pytanie | Bez RAG | RAG |
|---|---|---|
| Ile tekstu musi być potencjalnie dostępne? | ≤ 200 tys. tokenów | setki MB / GB |
| Jak często korpus się zmienia? | rzadko | codziennie, przyrostowo |
| Czy odpowiedź musi wskazać źródło co do strony? | nie | tak |
| Czy są uprawnienia per dokument? | nie | tak |

Dodatkowe sygnały, że RAG jest niepotrzebny:
- pytania dotyczą **danych, nie tekstu** („ile spraw zakończyliśmy w Q2”) — to jest SQL;
- korpus to jeden dokument, który wszyscy czytają w całości;
- zapytania to zawsze wyszukiwanie po nazwie, numerze, sygnaturze — to jest indeks
  pełnotekstowy, ewentualnie `LIKE` z trigramami;
- system i tak wymaga, żeby człowiek przeczytał źródło — wtedy potrzebna jest dobra
  wyszukiwarka, a nie generowanie odpowiedzi.

## Alternatywa 1: długie okno kontekstu

Wrzucasz cały korpus do promptu. Modele klasy Claude i Gemini przyjmują setki tysięcy
tokenów; niektóre miliony.

**Kiedy wygrywa:** korpus ≤ ~200 tys. tokenów (ok. 400–600 stron), stabilny w obrębie
sesji lub dnia, pytania wymagające zrozumienia całości („czy w tych aktach są sprzeczne
zeznania”, „streść przebieg sprawy”). To jest dokładnie sytuacja analizy pojedynczej
sprawy — i tam długi kontekst bije RAG bezdyskusyjnie.

**Kiedy przegrywa:**
- Powyżej ~200 tys. tokenów jakość i koszt przestają się bronić.
- „Context rot”: badanie Chroma z 14.07.2025 na 18 modelach (Claude Opus 4/Sonnet 4/3.7/3.5,
  o3, GPT-4.1, Gemini 2.5 Pro/Flash, Qwen3) pokazuje, że jakość spada wraz z długością
  wejścia **nierównomiernie i nawet na zadaniach trywialnych**. Na LongMemEval różnica
  między promptem skupionym (~300 tokenów) a pełnym (~113 tys.) była wyraźna dla wszystkich
  badanych modeli. Rozpraszacze — treści powierzchownie podobne — obniżają wynik silniej,
  niż sugerowałby ich udział.
- Test „igła w stogu siana” mierzy dopasowanie leksykalne i **przecenia** realne zdolności;
  gdy podobieństwo pytania do szukanej treści maleje, jakość spada znacznie szybciej.

**Koszt.** Korpus 200 tys. tokenów przy 3 USD/M za wejście to 0,60 USD za zapytanie
bez buforowania. Z buforowaniem (odczyt 0,1×) to 0,06 USD — porównywalnie z potokiem RAG,
przy zerowej infrastrukturze i lepszej jakości na pytaniach całościowych.

**Wniosek:** to jest realna, często lepsza alternatywa dla „czatu z aktami jednej sprawy”.
RAG zaczyna wygrywać dopiero przy korpusie obejmującym wiele spraw.

## Alternatywa 2: buforowanie promptu

Nie jest osobną architekturą, tylko tym, co czyni długi kontekst opłacalnym.

Anthropic: zapis 5 min = **1,25×** ceny wejścia, zapis 1 h = **2×**, odczyt = **0,1×**.
Maksymalnie 4 punkty cache. Minimum do buforowania: 512 tokenów (Opus 5),
1024 (Sonnet 4.5/5), 4096 (Haiku 4.5). Prefiks musi być identyczny co do znaku.

Prosta matematyka progu opłacalności przy TTL 5 minut:

```
bez cache:  n × K
z cache:    1,25 × K + (n-1) × 0,1 × K
próg:       opłaca się od n ≥ 2 zapytań na ten sam prefiks w oknie TTL
```

Przy TTL 1 h (zapis 2×) próg to n ≥ 2 również, tylko okno jest dłuższe.

Zastosowanie wzorcowe: użytkownik pracuje nad jedną sprawą i zadaje 15 pytań do tego
samego kompletu akt. Pierwsze zapytanie płaci 1,25× (albo 2× przy TTL godzinnym),
czternaście kolejnych po 0,1×. Łącznie ok. 2,6 zamiast 15 jednostek — **oszczędność ~83%**
przy zerowym potoku RAG.

Najczęstszy błąd: znacznik czasu, identyfikator sesji albo licznik w prompcie systemowym.
Prefiks zmienia się przy każdym żądaniu, cache nigdy nie trafia, płacisz 1,25× za nic.

## Alternatywa 3: dostrajanie modelu (fine-tuning)

**Do czego służy:** nadanie stylu, formatu, terminologii, sposobu rozumowania.
Nauczenie modelu, jak ma pisać pismo procesowe w konwencji kancelarii.

**Do czego NIE służy:** wprowadzenie faktów. Dostrajanie na korpusie akt nie sprawi,
że model będzie umiał zacytować konkretny ustęp konkretnej umowy. Da model, który
brzmi jak akta i pewnie zmyśla ich treść — czyli najgorszy możliwy wynik w kontekście
prawniczym.

| | Dostrajanie | RAG |
|---|---|---|
| Nowe fakty | nie | tak |
| Aktualizacja wiedzy | ponowne trenowanie | wstawienie do bazy |
| Przypisy do źródeł | niemożliwe | naturalne |
| Styl i format | tak, najlepsza metoda | częściowo, przez prompt |
| Koszt startu | wysoki (dane + trenowanie) | średni |
| Koszt zapytania | niższy (krótszy prompt) | wyższy |

Te dwa podejścia się nie wykluczają: dostrojony model piszący w konwencji kancelarii,
zasilany faktami przez RAG, jest sensowną kombinacją. Ale dostrajanie **jako zamiennik**
RAG do wiedzy faktograficznej jest błędem kategorii.

Zanim zaproponujesz dostrajanie, sprawdź, czy problemu nie rozwiązuje: lepszy prompt
systemowy, kilka przykładów w prompcie (few-shot), albo prompt z przykładami w cache.
Kolejność prób: prompt → przykłady w prompcie → dostrajanie.

## Alternatywa 4: zwykłe wyszukiwanie pełnotekstowe

Najbardziej niedoceniana opcja.

**Kiedy wystarcza:** użytkownik wie, czego szuka, i chce to znaleźć, a nie dostać
odpowiedź. Wyszukiwanie po sygnaturze, numerze faktury, nazwisku, dacie, frazie dosłownej.
Prawnik przeszukujący akta w 80% przypadków szuka konkretnego dokumentu, a nie odpowiedzi
na pytanie otwarte.

**Koszt:** `tsvector` + GIN w Postgresie, który już masz. Zero kosztu zmiennego,
opóźnienie w milisekundach, wynik w 100% weryfikowalny, brak halucynacji z definicji.

Nie sprzedawaj klientowi RAG tam, gdzie potrzebuje dobrej wyszukiwarki. Częsty i uczciwy wynik
rozmowy z klientem: „potrzebujecie wyszukiwarki pełnotekstowej z filtrami i dobrym podglądem, a nie
systemu generującego odpowiedzi”. Konfigurację polską opisuje
`references/engineering-core/04-bazy-i-rag/references/postgres.md`.

Wersja pośrednia, która często wystarcza: wyszukiwanie pełnotekstowe + model streszczający
znalezione dokumenty na żądanie użytkownika. Bez potoku osadzania, bez bazy wektorowej,
z pełną weryfikowalnością.

## Alternatywa 5: agent z narzędziami

Zamiast raz pobrać top-k i wygenerować odpowiedź, model dostaje narzędzia i sam decyduje,
czego szukać i kiedy skończyć:

```
szukaj(fraza, filtry)      → lista dokumentów z fragmentami
czytaj(dokument_id, strony) → pełny tekst wskazanego zakresu
lista_dokumentow(sprawa_id) → spis akt sprawy
zapytanie_sql(...)          → dane strukturalne (terminy, kwoty, strony)
```

**Przewaga nad klasycznym RAG:**
- Model może iterować: znaleźć umowę, przeczytać § 7, zauważyć odesłanie do aneksu,
  poszukać aneksu, przeczytać go. Jednorazowe pobranie top-10 tego nie zrobi.
- Model może przeczytać dokument w całości, gdy uzna to za potrzebne.
- Naturalnie obsługuje pytania wielokrokowe („czy termin z aneksu został dochowany”).
- Przypis jest dokładny, bo model przeczytał wskazane strony, a nie fragment wyrwany
  z kontekstu.

**Koszt:** więcej wywołań modelu na jedno pytanie (typowo 3–8), wyższe opóźnienie
(rzędu 10–40 s), trudniejsza kontrola kosztu. Wymaga limitu kroków i budżetu tokenów.

**Kiedy wybrać:** pytania złożone, wymagające wielu kroków, gdzie jakość odpowiedzi
jest ważniejsza od czasu i kosztu. To jest opis analizy prawniczej.

Uwaga: narzędzie `szukaj` w takim agencie i tak jest zbudowane na hybrydzie z tego modułu.
Agent nie zastępuje wyszukiwarki, tylko sposób jej użycia. Definicje narzędzi i protokół
MCP → `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md`; konstrukcja pętli agenta,
role i budżety → paczka `../orkiestracja-agentow/SKILL.md`.

## Alternatywa 6: GraphRAG i grafy wiedzy

Zamiast (albo obok) indeksu wektorowego budujesz graf encji i relacji, a odpowiedź
składasz, chodząc po grafie.

**Kiedy naprawdę pomaga:**
- Pytania wielokrokowe po relacjach: „którzy członkowie zarządu spółek powiązanych
  z pozwanym występowali też w sprawach naszego klienta”.
- Pytania całościowe o korpus: „jakie są główne tematy w tych 4000 dokumentach”
  (na to klasyczny RAG jest z zasady bezradny — top-10 fragmentów nie opisze całości).
- Domeny z gęstą, jawną siecią relacji: powiązania kapitałowe, łańcuchy cesji,
  sieć podmiotów w sprawie gospodarczej.

**Kiedy nie pomaga (czyli zwykle):**
- Pytania faktograficzne z jednego dokumentu — klasyczny RAG jest tańszy i równie dobry.
- Korpus bez wyraźnych, powtarzalnych typów encji i relacji.

**Koszt, który przesądza:** budowa grafu wymaga przepuszczenia **całego korpusu** przez LLM w celu
ekstrakcji encji i relacji, a przy podejściu Microsoft GraphRAG także generowania streszczeń
społeczności. To jest rząd wielkości drożej niż osadzenie (które kosztuje dziesiątki dolarów za
korpus — patrz `references/engineering-core/04-bazy-i-rag/references/embeddingi.md`) i musi być
powtarzane przy każdej istotnej zmianie korpusu. Do tego dochodzi utrzymanie bazy grafowej i jakość
ekstrakcji, która na polskich tekstach prawniczych wymaga własnej ewaluacji. `[niepotwierdzone:
aktualne liczbowe porównania kosztu indeksacji GraphRAG vs klasyczny RAG na sierpień 2026 — dostępne
opracowania są niespójne co do metodologii]`

**Uczciwa rekomendacja:** zbuduj najpierw hybrydowy RAG. Zmierz, jaki odsetek pytań ze zbioru
testowego wymaga chodzenia po relacjach. Jeśli poniżej ~15% — nie buduj grafu, tylko
dodaj narzędzia agentowi (alternatywa 5), który wykona te kroki sam. Graf ma sens,
gdy pytania relacyjne dominują, a nie gdy się zdarzają.

Wariant tańszy, który zwykle wystarcza: **encje jako metadane, nie jako graf.** Wyciągnij
z dokumentów strony, sygnatury, daty, kwoty i zapisz jako kolumny/`jsonb` w Postgresie.
Wtedy „wszystkie dokumenty, w których występuje X” to zapytanie SQL, a nie przechodzenie
po grafie. Pokrywa większość realnych pytań relacyjnych za ułamek kosztu.

## Tabela decyzyjna

| Sytuacja | Rozwiązanie | Uzasadnienie |
|---|---|---|
| Jedna sprawa, ≤ 500 stron, wiele pytań w sesji | długi kontekst + cache | tańsze i dokładniejsze niż RAG |
| Kilkaset spraw, pytania w obrębie jednej | RAG z filtrem sprawy, ale rozważ długi kontekst na wybraną sprawę | filtr redukuje korpus do rozmiaru okna |
| Dziesiątki tysięcy dokumentów, pytania przekrojowe | **RAG hybrydowy** | to jest właściwy przypadek użycia |
| Szukanie konkretnego dokumentu po numerze/nazwisku | FTS + filtry | zero halucynacji, milisekundy |
| Pytania o liczby, terminy, statystyki | SQL | RAG na danych strukturalnych to błąd kategorii |
| Pytania wielokrokowe po relacjach | agent z narzędziami; graf dopiero gdy dominują | graf jest drogi w budowie i utrzymaniu |
| Pytania całościowe o cały korpus | GraphRAG albo hierarchiczne streszczenia | klasyczny RAG tego nie umie |
| Model ma pisać w konwencji kancelarii | dostrajanie albo przykłady w prompcie | RAG nie zmienia stylu |
| Model ma znać wewnętrzne procedury firmy (stały tekst) | prompt systemowy + cache | RAG dla 20 stron to przerost formy |

## Uczciwe koszty — zestawienie

Założenie: 10 tys. zapytań miesięcznie, model klasy Sonnet (3 USD/M wejście, 15 USD/M wyjście).

| Rozwiązanie | Koszt startu | Koszt miesięczny | Opóźnienie | Weryfikowalność |
|---|---|---|---|---|
| FTS w Postgresie | dni (konfiguracja polska) | ~0 | < 50 ms | pełna |
| Długi kontekst 200 tys. tok. bez cache | godziny | ~6 000 USD | 10–30 s | pełna (materiał w prompcie) |
| Długi kontekst 200 tys. tok. z cache | godziny | ~600–900 USD | 10–30 s | pełna |
| RAG hybrydowy (ten moduł) | tygodnie | ~340 USD | 2–5 s | wysoka, wymaga dyscypliny przypisów |
| Agent z narzędziami | tygodnie | ~1 000–2 500 USD | 10–40 s | najwyższa (model czyta źródło) |
| GraphRAG | miesiące + kosztowna indeksacja | RAG + utrzymanie grafu | 3–10 s | średnia (relacje wywnioskowane przez LLM) |
| Dostrajanie | tygodnie + dane | niższy koszt zapytania | 1–3 s | **brak** |

Liczby są rzędem wielkości do rozmowy, nie ofertą. Zmienne, które przesuwają je najbardziej:
liczba fragmentów podawanych modelowi, długość odpowiedzi, trafienia w cache.

## Reguły

- Zawsze sprawdź, czy korpus mieści się w oknie kontekstu. Jeśli tak i jest stabilny —
  długi kontekst z buforowaniem jest domyślną odpowiedzią, nie RAG.
- Nie buduj RAG dla korpusu, który nie rośnie i mieści się w 200 tys. tokenów.
- Nie buduj RAG dla pytań, które są zapytaniami SQL.
- Nie buduj GraphRAG, zanim nie zmierzysz, jaki odsetek pytań rzeczywiście wymaga relacji.
- Nie proponuj dostrajania jako sposobu na wprowadzenie faktów.
- Powiedz klientowi wprost, gdy potrzebuje wyszukiwarki, a nie generatora odpowiedzi.
  To jest uczciwa i zwykle tańsza rekomendacja.
- Rozwiązanie mieszane jest normą: FTS do szukania dokumentu, długi kontekst do analizy
  jednej sprawy, RAG do pytań przekrojowych. Jeden system nie musi obsługiwać wszystkiego
  tym samym mechanizmem.
