# Redakcja dokumentu — część pierwsza standardu

Plik niesie rozdziały 2, 3, 4, 6 i 10 standardu redakcyjnego: budowę opracowania, wymóg
form wizualnych, wymóg normatywnej szczegółowości, zasady odsyłaczy oraz wzorzec w pełni
wypełniony. Rozdziały zachowują numerację wspólną dla całego standardu. Spis rozdziałów
i podział na pliki: `references/standard-redakcyjny-i-jezykowy.md`. Język i typografię
normuje `references/jezyk-i-typografia.md`, nazewnictwo bytów kodu —
`references/konwencje-nazewnicze.md`.

---

## 2. Budowa opracowania

Każde opracowanie zbioru składa się z sześciu części w stałej kolejności:

```
┌───────────────────────────┐
│  1 · Tytuł (nagłówek H1)  │
├───────────────────────────┤
│  2 · Metryka produktowa   │  tabela stała, osiem wierszy
├───────────────────────────┤
│  3 · Metryka dokumentu    │  tabela zmienna, jedenaście wierszy
├───────────────────────────┤
│  4 · Spis treści          │  odsyłacze do wszystkich rozdziałów
├───────────────────────────┤
│  5 · Korpus               │  rozdziały numerowane, oddzielane ───
├───────────────────────────┤
│  6 · Stopka               │  trzy bloki, treść dosłowna
└───────────────────────────┘
```

### 2.1 Nagłówek i metryka

Tytuł dokumentu zapisujemy jako `# Danaco Console — {Tytuł opracowania}`. Bezpośrednio pod
nim stoją dwie tabele.

**Metryka produktowa** — wartości stałe dla całego zbioru, zmienia się wyłącznie data:

```markdown
| | |
|---|---|
| **Produkt** | Danaco Console |
| **Rodzaj** | Platforma AI Workspace OS |
| **Opis** | Platforma jest wielośrodowiskowym systemem operacyjnym dla sztucznej inteligencji, integrującym komunikację, zarządzanie wiedzą, tworzenie treści, projektowanie, automatyzacje procesów oraz rozwój oprogramowania. |
| **Producent** | Danaco Holding Group Sp. z o.o. |
| **Twórca** | Dariusz Naharnowicz |
| **Wersja** | v2.0 |
| **Status** | Deweloperski |
| **Data** | {RRRR-MM-DD} |
```

Wiersz **Opis** niesie brzmienie dosłowne podane wyżej i jest jednakowy w całym zbiorze —
jak pozostałe wiersze tej tabeli, nie podlega przeredagowaniu w pojedynczym opracowaniu.

**Metryka dokumentu** — wartości zmienne, poprzedzona wierszem
`**Informacje szczegółowe dokumentu:**`:

| Pole | Obowiązkowe | Treść |
|---|---|---|
| **Tytuł** | tak | pełny tytuł opracowania, bez przedrostka nazwy produktu |
| **Klasa dokumentu** | tak | jedna z czterech wartości z rozdz. 2.2 |
| **Odbiorcy** | tak | wskazani imiennie: deweloper, projektant, Operator — nie „wszyscy zainteresowani” |
| **Przeznaczenie** | tak | jedno zdanie: do czego dokument służy i co na jego podstawie powstaje |
| **Zakres** | tak | co dokument obejmuje |
| **Poza zakresem** | tak | co świadomie pominięto i gdzie tego szukać |
| **Dokument nadrzędny** | tak | odsyłacz do opracowania wyżej w hierarchii |
| **Dokumenty powiązane** | tak | odsyłacze rozdzielone `·`, powiązanie dwukierunkowe |
| **Prototypy odniesienia** | gdy dotyczy | ścieżki do plików w `design/05-okna/` |
| **Źródła normatywne** | tak | ścieżki źródeł, z których pochodzą wartości w dokumencie |
| **Zasada nadrzędna** | tak | jedno zdanie rozstrzygające, gdy treść dopuszcza dwie lektury |

Pole „Poza zakresem” nie jest ozdobnikiem: bez niego czytelnik nie wie, czy czegoś nie ma,
bo tego nie przewidziano, czy dlatego, że opisano to gdzie indziej.

### 2.2 Klasy dokumentów

| Klasa | Co opisuje | Przykłady |
|---|---|---|
| **Specyfikacja docelowa** | stan, który ma powstać — zakres budowy | opracowania w `architektura/`, `moduly/`, `interfejs-uzytkownika/`, `srodowiska/`, `specyfikacje/`, `funkcje-globalne/` |
| **Stan wdrożenia** | stan faktyczny kodu w bieżącym wydaniu | `README.md`, `INSTRUKCJA-UZYTKOWANIA.md`, `INSTALACJA-I-KONFIGURACJA.md` |
| **Akt prawny** | warunki korzystania z produktu | `LICENSE.md` |
| **Nawigacja** | porządek zbioru | `SPIS-OPRACOWAN.md`, niniejszy standard |

Klasa rozstrzyga o dwóch rzeczach: czy w dokumencie występują oznaczenia stanu wdrożenia
(rozdz. 2.6) oraz jaki repertuar form wizualnych obowiązuje (rozdz. 3.2).

### 2.3 Spis treści

```markdown
## Spis treści

1. [{Rozdział}](#1-rozdział)
   - [1.1 {Podrozdział}](#11-podrozdział)
   - [1.2 {Podrozdział}](#12-podrozdział)
2. [{Rozdział}](#2-rozdział)
```

| Zasada | Postać wiążąca |
|---|---|
| Nagłówek sekcji | zawsze `## Spis treści` |
| Poziom pierwszy | numeracja `1.`, `2.`, bez wcięcia |
| Poziom drugi | wcięcie trzema spacjami, myślnik `- `, numer `1.1` |
| Poziom trzeci | dopuszczalny w opracowaniach powyżej 1500 wierszy |
| Położenie numeru | wewnątrz odsyłacza: `[1.1 Tytuł](#…)`, nigdy `1.1 [Tytuł](#…)` |
| Kotwice | małe litery, polskie znaki zachowane, spacja → `-`, kropki i backticki usunięte, półpauza `—` daje podwójny `--` |
| Kompletność | spis obejmuje wszystkie nagłówki `##` i `###` korpusu |

Spisu treści nie umieszczamy w spisie treści. Rozdziałów „Stopka” i „Metryka” również.

### 2.4 Korpus dokumentu

Rozdziały numerujemy `## 1.`, podrozdziały `### 1.1`. Numeracja jest ciągła i nie ma luk.
Rozdziały oddzielamy poziomą linią `---`. Rozdział pierwszy zawsze odpowiada na pytanie
„czym jest opisywany byt”; rozdział ostatni zawsze zawiera kryteria odbioru (rozdz. 4.2).

Zakaz numeracji innej niż numeracja rozdziałów — patrz rozdz. 7.1.

### 2.5 Stopka

Trzy ostatnie bloki każdego pliku, treść dosłowna:

```markdown
---

*Koniec dokumentu. {Tytuł opracowania} — {klasa dokumentu}, wersja 2.0, {RRRR-MM-DD}.*

---
*Danaco Console — Platforma AI Workspace OS · v2.0 · status Deweloperski*
*© 2026 Danaco Holding Group Sp. z o.o. Wszelkie prawa zastrzeżone — Dariusz Naharnowicz.*
*Warunki korzystania: [Licencja produktu]({ścieżka}). Kontakt: support@danaco-group.pl*
```

Ścieżka do licencji jest względna wobec położenia pliku:

| Położenie pliku | Ścieżka w stopce |
|---|---|
| korzeń `docs/` | `LICENSE.md` |
| podkatalog `docs/{katalog}/` | `../LICENSE.md` |

Zapis `[Licencja produktu](../LICENSE.md)` w pliku leżącym w korzeniu `docs/` jest błędny —
wskazuje poza katalog zbioru, gdzie nie ma żadnego pliku licencji. Tak samo błędny jest
zapis `[Licencja produktu](LICENSE.md)` w pliku podkatalogu.

### 2.6 Oznaczenia stanu wdrożenia

Oznaczenia stanu **nie występują w opracowaniach klasy Specyfikacja docelowa**. Opracowanie
projektowe opisuje to, co ma powstać; znakowanie w nim, co już działa, myli zakres budowy
z postępem budowy i dezaktualizuje dokument przy każdym wydaniu. Postęp prac jest
przedmiotem raportu wykonawczego.

W opracowaniach klasy **Stan wdrożenia** obowiązuje jeden zestaw sześcioelementowy:

| Oznaczenie | Znaczenie |
|---|---|
| **[DZIAŁA]** | Funkcja domknięta od interfejsu albo od komendy kontraktu do skutku; potwierdzona audytem. |
| **[DZIAŁA CZĘŚCIOWO]** | Mechanizm działa w ograniczonym zakresie albo z udokumentowanym zastrzeżeniem. |
| **[NIEZINTEGROWANE]** | Kod istnieje i jest poprawny, lecz nie ma konsumenta — funkcja nie jest osiągalna dla Operatora. |
| **[ATRAPA]** | Element widoczny w interfejsie, za którym nie stoi realizacja. |
| **[BRAK]** | Przewidziane koncepcją, w bieżącej wersji niezaimplementowane. |
| **[DO DECYZJI OPERATORA]** | Kwestia nierozstrzygnięta; dokument jej nie przesądza. |

W opracowaniach klasy Specyfikacja docelowa z całego repertuaru zostaje **wyłącznie**
oznaczenie `[DO DECYZJI OPERATORA]` — jest niezbędne, bo rozdz. 4 zakazuje zgadywania.

---

## 3. Wymóg form wizualnych

### 3.1 Miara i próg

Każde opracowanie ma **co najmniej 30 % wierszy w formach innych niż ciągła proza**.

```
Objętość dokumentu
├── proza ciągła ............................ najwyżej 70 %
└── formy wizualne .......................... co najmniej 30 %
    ├── tabele
    ├── diagramy ASCII
    ├── bloki kodu i konfiguracji
    ├── listy definicyjne i wyliczeniowe
    ├── drzewa katalogów
    ├── maszyny stanów
    └── przebiegi decyzyjne i sekwencje
```

Miarą jest udział wierszy należących do form wizualnych w sumie wierszy pliku, liczony
z pominięciem metryki, spisu treści i stopki.

### 3.2 Repertuar form obowiązkowych

| Katalog | Formy wymagane w każdym opracowaniu |
|---|---|
| `architektura/` | diagram warstw · diagram sekwencji dla każdego przebiegu · schemat encji i relacji · drzewo katalogów · tabela kontraktów |
| `specyfikacje/` | tabela pełnego wykazu · maszyna stanów · macierz uprawnień |
| `interfejs-uzytkownika/` | szkic układu okna · mapa stref · tabela stanów kontrolki · przebieg nawigacji · tabela punktów łamania |
| `moduly/` | szkic okna głównego · mapa okien operacyjnych · tabela komend kontraktu · przepływ pracy jako diagram · tabela danych wykorzystywanych przez model |
| `srodowiska/` | mapa modułów środowiska · szkic przedsionka · przebieg wejścia do środowiska |
| `funkcje-globalne/` | szkic widoku · maszyna stanów · tabela wyzwalaczy |

### 3.3 Jakość diagramów

| Zasada | Wymóg |
|---|---|
| Znaki ramek | `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ► ▼ ◄ ▲` |
| Szerokość | do 100 znaków |
| Podpis | jedno zdanie nad diagramem, mówiące co diagram pokazuje |
| Legenda | pod diagramem, gdy diagram używa skrótów albo znaków o umownym znaczeniu |
| Nazewnictwo | każdy element nazwany dokładnie tak jak w prozie i w kodzie |
| Kompletność | diagram nie wprowadza nazwy, której nie ma w treści |
| Celowość | diagram objaśnia to, czego proza nie oddaje równie zwięźle; diagramy ozdobne są zakazane |

Przykład diagramu spełniającego wymogi — przebieg wejścia do środowiska:

```
Operator                Powłoka                           Rdzeń
   │                       │                                 │
   │  wybór środowiska     │                                 │
   ├──────────────────────►│                                 │
   │                       │  environment.enter              │
   │                       ├────────────────────────────────►│
   │                       │                                 │
   │                       │  environment · modules          │
   │                       │  sessions · focusedSessionId    │
   │                       │◄────────────────────────────────┤
   │  przedsionek          │                                 │
   │◄──────────────────────┤                                 │
   │                       │                                 │
```

Legenda: `environment.enter` — nazwa komendy kontraktu; `environment`, `modules`,
`sessions`, `focusedSessionId` — pola wyniku tej komendy.

---

## 4. Wymóg normatywnej szczegółowości

Opracowanie niesie **pełny ciąg budowy**. Deweloper nie ma prawa niczego dopowiadać.
Jeśli dokument nie podaje nazwy komendy, brzmienia etykiety, wartości żetonu albo kodu
błędu — jest to usterka opracowania, nie swoboda wykonawcy.

### 4.1 Źródła normatywne

Wartości pochodzą wyłącznie z poniższych źródeł. Wymyślanie wartości jest zakazane.

| Źródło | Zawartość | Co z niego bierzemy |
|---|---|---|
| `budowa/shared/contract.json` | 1119 komend · 68 obszarów · 552 struktury · 377 wyliczeń · 78 zdarzeń · 8 kodów błędów | nazwy komend i zdarzeń, pola żądania i wyniku, typy, wymagalność, wartości wyliczeń, kody błędów |
| `design/zasoby/zetony/zetony.css` | 184 żetony `--dn-*` | kolory, wymiary, odstępy, typografia, cienie, czasy, warstwy, punkty łamania |
| `design/zasoby/css/komponenty.css`, `rama.css`, `prototyp.css` | 199 klas `.dn-*` | nazwy komponentów, modyfikatorów i stanów |
| `design/zasoby/ikony/manifest.json` | wykaz ikon | nazwy ikon przypisane do kontrolek |
| `budowa/shared/kontrasty-progi.json` | progi kontrastu | wymagania dostępności |
| `design/05-okna/` | 38 prototypów | dosłowne brzmienia etykiet, przycisków, komunikatów |
| `budowa/client/src/` | kod powłoki | rzeczywiste identyfikatory i etykiety |

**Reguła weryfikowalności.** Każda wartość liczbowa, nazwa i etykieta w opracowaniu musi
dać się wskazać w jednym z powyższych źródeł. Wartość bez pokrycia oznaczamy jawnie
`[DO DECYZJI OPERATORA]`.

### 4.2 Wykazy obowiązkowe

Każde opracowanie klasy Specyfikacja docelowa zawiera komplet poniższych wykazów. Wykaz
niedotyczący opisywanego bytu zapisujemy z adnotacją „nie dotyczy” i uzasadnieniem — nie
pomijamy go milczeniem.

| Wykaz | Zawartość kolumn |
|---|---|
| **Komendy kontraktu** | nazwa komendy · obszar · pola żądania (nazwa, typ, wymagalność) · pola wyniku · zdarzenia zwrotne · kody błędów |
| **Etykiety interfejsu** | element · dosłowne brzmienie · miejsce wystąpienia |
| **Komunikaty** | sytuacja · dosłowna treść · rodzaj (potwierdzenie, ostrzeżenie, błąd, stan pusty) |
| **Żetony** | miejsce zastosowania · żeton `--dn-*` · czego dotyczy |
| **Komponenty** | klasa `.dn-*` · rola · modyfikatory · stany |
| **Skróty klawiszowe** | kombinacja · działanie · zasięg · kolizje |
| **Stany kontrolek** | kontrolka · spoczynek · wskazanie kursorem · wciśnięcie · ognisko · nieaktywny · ładowanie · pusty · błąd |
| **Punkty łamania** | próg szerokości · zachowanie układu |
| **Kryteria odbioru** | warunek sprawdzalny · sposób sprawdzenia |

**Fragmenty kodu jako wartość wymuszona.** Tam, gdzie konwencja projektowa nie dopuszcza
wariantu — struktura ładunku, sygnatura komendy, deklaracja żetonu, znacznik dostępności —
podajemy gotowy fragment, nie opis. Przykład zapisu komendy w postaci wymuszonej:

```json
{
  "typ": "environment.enter",
  "zadanie": {
    "environmentId": "string   — wymagane",
    "clientId":      "string   — wymagane",
    "sessionId":     "string   — opcjonalne; puste otwiera kartę pustą"
  }
}
```

### 4.3 Wykluczenie luk wykończeniowych

Sformułowania zakazane, ponieważ otwierają interpretację wykonawcy:

| Zakazane | Dlaczego | Czym zastąpić |
|---|---|---|
| „odpowiedni”, „stosowny”, „właściwy” | nie mówi, który | wskazać wartość |
| „w razie potrzeby”, „opcjonalnie” | nie mówi, kiedy | podać warunek |
| „na przykład”, „i tym podobne”, „między innymi” | zbiór otwarty | wyliczyć komplet |
| „można”, „powinno się rozważyć”, „warto” | nie zobowiązuje | rozstrzygnąć wprost |
| „typowo”, „zwykle”, „zazwyczaj” | opisuje zwyczaj, nie regułę | podać regułę |
| „i inne”, „itd.”, „itp.” | ukrywa braki | wyliczyć komplet |

Każde takie miejsce zastępujemy wartością rozstrzygniętą albo oznaczeniem
`[DO DECYZJI OPERATORA]` z pytaniem postawionym wprost.

---

## 6. Odsyłacze i nawigacja

| Zasada | Wymóg |
|---|---|
| Postać | odsyłacz markdown ``[Tytuł](../katalog/plik.md)``; zapis w backtickach nie jest odsyłaczem |
| Ścieżka | zawsze z katalogiem, także przy plikach o nazwie powtórzonej w zbiorze |
| Kotwica rozdziału | `[…](model-danych.md#…)` |
| Dwukierunkowość | jeśli opracowanie A wskazuje B, opracowanie B wymienia A w polu „Dokumenty powiązane” |
| Cel istniejący | odsyłacz do pliku nieistniejącego jest usterką; zakaz przywoływania opracowań planowanych |
| Liczby | zamiast odsyłać do wykazu, podajemy liczbę i wykaz wprost ze źródła normatywnego |

Nazwy plików kolidujące wielkością liter są zakazane: `INSTRUKCJA-UZYTKOWANIA.md`
i `instrukcja-uzytkowania.md` to jeden plik na Windows i na macOS.

---

## 10. Wzorzec w pełni wypełniony

Poniższy szkielet pokazuje minimalny komplet elementów opracowania klasy Specyfikacja
docelowa, z przykładowymi wartościami wziętymi z rzeczywistych źródeł normatywnych —
nie jest to dokument istniejący w zbiorze, wyłącznie ilustracja złożenia elementów
z rozdziałów 2–4 w jedną całość.

```markdown
# Danaco Console — Moduł Automations

| | |
|---|---|
| **Produkt** | Danaco Console |
| **Rodzaj** | Platforma AI Workspace OS |
| **Opis** | Platforma jest wielośrodowiskowym systemem operacyjnym dla sztucznej inteligencji, integrującym komunikację, zarządzanie wiedzą, tworzenie treści, projektowanie, automatyzacje procesów oraz rozwój oprogramowania. |
| **Producent** | Danaco Holding Group Sp. z o.o. |
| **Twórca** | Dariusz Naharnowicz |
| **Wersja** | v2.0 |
| **Status** | Deweloperski |
| **Data** | 2026-08-20 |

**Informacje szczegółowe dokumentu:**

| | |
|---|---|
| **Tytuł** | Moduł Automations |
| **Klasa dokumentu** | Specyfikacja docelowa |
| **Odbiorcy** | deweloper · projektant |
| **Przeznaczenie** | Ustala zakres funkcjonalny i zachowanie modułu Automations — automatyk, harmonogramów i przebiegów |
| **Zakres** | okna operacyjne modułu, komendy obszaru `automation`, żetony i komponenty widoku, stany kontrolek |
| **Poza zakresem** | silnik harmonogramu jako mechanizm rdzenia — [Architektura techniczna](../architektura/architektura.md) rozdz. 7 |
| **Dokument nadrzędny** | [Specyfikacja modułów](../specyfikacje/specyfikacja-modulow.md) |
| **Dokumenty powiązane** | [Model danych](../architektura/model-danych.md) · [Katalog komponentów](../interfejs-uzytkownika/katalog-komponentow.md) |
| **Prototypy odniesienia** | `design/05-okna/moduly/automations.html` |
| **Źródła normatywne** | `budowa/shared/contract.json` (obszar `automation`) · `design/zasoby/zetony/zetony.css` |
| **Zasada nadrzędna** | Automatyka bez właściciela nie uruchamia się — każdy przebieg ma przypisaną odpowiedzialność |

---

## Spis treści

1. [Czym jest moduł Automations](#1-czym-jest-moduł-automations)
2. [Okna operacyjne](#2-okna-operacyjne)
3. [Komendy kontraktu](#3-komendy-kontraktu)

---

## 1. Czym jest moduł Automations

{proza — jeden do trzech akapitów}

---

## 2. Okna operacyjne

┌───────────────────────────────────────────────────┐
│  Automations — okno główne                        │
├──────────────────┬────────────────────────────────┤
│  Harmonogramy    │  Karta harmonogramu            │
│  (lewa kolumna)  │  (prawa kolumna, szczegóły)    │
└──────────────────┴────────────────────────────────┘

## 3. Komendy kontraktu

| Komenda | Pola żądania | Pola wyniku | Zdarzenia |
|---|---|---|---|
| `automation.list` **[DO DECYZJI OPERATORA]** — nazwa nie występuje w `budowa/shared/contract.json`; do rozstrzygnięcia, czy komenda ma powstać | `environmentId?: string` | `automations: Automation[]` | — |
| `automation.run` | `automationId: string` | `runId: string` | `automation.run.started` |
```

Elementy, których w tym szkicu **nie wolno pominąć** w dokumencie docelowym: wykaz
etykiet interfejsu, wykaz żetonów, wykaz komponentów, wykaz skrótów klawiszowych,
wykaz stanów kontrolek, wykaz punktów łamania, kryteria odbioru oraz stopka pełna
(rozdz. 2.5). Szkic je pomija wyłącznie dla zwięzłości ilustracji.

---

