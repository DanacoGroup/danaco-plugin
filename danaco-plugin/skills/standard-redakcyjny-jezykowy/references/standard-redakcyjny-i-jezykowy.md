# Standard redakcyjny i językowy Danaco — spis standardu

Standard obowiązuje opracowania wchodzące do zbioru dokumentacji `docs/` produktu
Danaco Console: README, opracowania architektury, specyfikacje, standardy, dokumenty
produktowe. Dla plików referencyjnych paczek tego pluginu obowiązuje osobna, węższa
klasa dokumentu opisana w `references/plik-referencyjny-skilla.md` — nie wymaga ona
metryki produktowej, metryki dokumentu ani stopki produktowej.

Standard jest podzielony na cztery pliki, żeby wczytywać wyłącznie potrzebną część.
Numeracja rozdziałów jest wspólna dla całego standardu; odsyłacz „rozdz. 5.1” wskazuje
zawsze ten sam rozdział, niezależnie od pliku, w którym się pojawia. Ta tabela rozstrzyga,
w którym pliku leży dany rozdział.

| Rozdziały | Plik | Przedmiot |
|---|---|---|
| 1 · 8 · 9 · 11 · 12 | `references/standard-redakcyjny-i-jezykowy.md` (ten plik) | przeznaczenie standardu, kontrola zgodności, progi objętości, katalog usterek redakcyjnych, polecenia kontrolne |
| 2 · 3 · 4 · 6 · 10 | `references/redakcja-dokumentu.md` | budowa opracowania, formy wizualne, normatywna szczegółowość, odsyłacze, wzorzec w pełni wypełniony |
| 5 | `references/jezyk-i-typografia.md` | słownik wiążący, terminy zachowane, zasady polszczyzny, typografia |
| 7 | `references/konwencje-nazewnicze.md` | zakaz kodów wymyślonych, zakaz określeń abstrakcyjnych, nazewnictwo bytów kodu, jedno źródło prawdy, zamknięty zbiór, tryb przy braku ustalenia |
| — | `references/plik-referencyjny-skilla.md` | kształt wiążący pliku referencyjnego paczki pluginu |

**Zasada nadrzędna.** Opracowanie niesie zamknięty zbiór informacji. Jeśli dokument
czegoś nie rozstrzyga, wykonawca nie rozstrzyga tego sam — dokument oznacza brak
i stawia pytanie.

---

## Spis treści

Rozdziały niesione przez ten plik, w numeracji wspólnej dla całego standardu:

- rozdz. 1 — [Do czego służy ten standard](#1-do-czego-służy-ten-standard)
- rozdz. 8 — [Kontrola zgodności](#8-kontrola-zgodności)
- rozdz. 9 — [Progi objętości](#9-progi-objętości)
- rozdz. 11 — [Najczęstsze usterki redakcyjne](#11-najczęstsze-usterki-redakcyjne)
- rozdz. 12 — [Polecenia kontrolne dla redaktora](#12-polecenia-kontrolne-dla-redaktora)

Rozdziały 2, 3, 4, 6 i 10 leżą w `references/redakcja-dokumentu.md`, rozdział 5
w `references/jezyk-i-typografia.md`, rozdział 7 w `references/konwencje-nazewnicze.md`.

---

## 1. Do czego służy ten standard

Zbiór dokumentacji Danaco Console liczy kilkadziesiąt opracowań pisanych w różnym czasie
i przez różne ręce. Bez jednego wzorca każde kolejne przejście redakcyjne poprawia to samo
od nowa: raz metrykę, raz stopkę, raz termin zapisany na trzy sposoby. Standard zamyka tę
pętlę — ustala kształt dokumentu, słownik i konwencje nazewnicze raz, wiążąco i sprawdzalnie.

### 1.1 Trzy części standardu

```
┌─────────────────────────────────────────────────────────────────────┐
│  STANDARD REDAKCYJNY I JĘZYKOWY                                     │
├──────────────────┬──────────────────────┬───────────────────────────┤
│  CZĘŚĆ PIERWSZA  │  CZĘŚĆ DRUGA         │  CZĘŚĆ TRZECIA            │
│  Redakcja        │  Język               │  Konwencje budowy         │
├──────────────────┼──────────────────────┼───────────────────────────┤
│  rozdz. 2 · 3    │  rozdz. 5            │  rozdz. 7                 │
│  rozdz. 4 · 6    │                      │                           │
├──────────────────┼──────────────────────┼───────────────────────────┤
│  jak dokument    │  jakimi słowami      │  jak nazywać byty,        │
│  ma być zbudowany│  ma być napisany     │  które dopiero powstaną   │
└──────────────────┴──────────────────────┴───────────────────────────┘
```

Legenda: część pierwsza dotyczy formy opracowania, druga jego języka, trzecia — tego, co
z opracowania przechodzi do kodu i do przyszłych dokumentów.

### 1.2 Moc obowiązująca

| Adresat | Zakres związania |
|---|---|
| Redaktor dokumentacji | całość standardu; opracowanie niezgodne ze standardem nie jest przyjmowane |
| Projektant | rozdziały 2–6 przy opisie interfejsu; rozdział 7 przy nazywaniu komponentów i żetonów |
| Deweloper | rozdział 7 w całości; rozdziały 4 i 5 przy nazywaniu komend, zdarzeń i etykiet |

---

## 8. Kontrola zgodności

Opracowanie jest przyjmowane, gdy wszystkie poniższe kontrole zwracają zero uchybień.

| Kontrola | Sprawdzany warunek |
|---|---|
| **Metryka** | obie tabele obecne, komplet pól obowiązkowych wypełniony; metryka produktowa liczy osiem wierszy, metryka dokumentu jedenaście pól |
| **Spis treści** | obecny, pozycje zgodne z rzeczywistymi nagłówkami, kotwice rozwiązywalne |
| **Stopka** | trzy bloki, treść dosłowna, ścieżka do licencji rozwiązywalna |
| **Odsyłacze** | wszystkie rozwiązywalne, wszystkie w postaci markdown, powiązania dwukierunkowe |
| **Formy wizualne** | udział nie mniejszy niż 30 % |
| **Wykazy obowiązkowe** | komplet z rozdz. 4.2 obecny albo opatrzony uzasadnioną adnotacją „nie dotyczy” |
| **Normatywność** | każda nazwa komendy obecna w `contract.json`; każdy żeton w `zetony.css`; każda klasa w arkuszach `design/zasoby/` |
| **Luki wykończeniowe** | zero sformułowań z rozdz. 4.3 bez towarzyszącego oznaczenia braku |
| **Terminologia** | zero terminów porzuconych z rozdz. 5.1 w prozie |
| **Typografia** | zero cudzysłowów prostych poza kodem, zero podwójnych spacji, zero dywizów w funkcji myślnika |
| **Kody wymyślone** | zero oznaczeń zakazanych rozdz. 7.1 |
| **Objętość** | patrz progi znakowe rozdz. 9 |

---

## 9. Progi objętości

Objętość jest miarą pomocniczą — świadczy, że wykazy z rozdz. 4.2 i formy wizualne
z rozdz. 3 rzeczywiście wypełniono, a nie że dokument jest długi dla samej długości.
Miarą jest liczba znaków pliku źródłowego, licząc znaki znaczników Markdown.

| Klasa pliku | Próg | Uzasadnienie |
|---|---|---|
| Cztery opracowania Właściciela w korzeniu (`README.md`, `INSTRUKCJA-UZYTKOWANIA.md`, `INSTALACJA-I-KONFIGURACJA.md`, `LICENSE.md`) | **objętość nie może ulec zmniejszeniu** względem stanu zastanego | dokumenty niosą opis stanu faktycznego kodu i akt prawny — redakcja poprawia formę, nie skraca treści |
| Opracowania merytoryczne bardziej rozbudowane — katalogi `architektura/`, `moduly/`, `interfejs-uzytkownika/`, `srodowiska/`, `specyfikacje/`, `funkcje-globalne/` | **co najmniej 85 000 znaków** | katalogi niosące pełny ciąg budowy (rozdz. 4) — komplet wykazów przy tej objętości merytorycznej osiąga tę wielkość naturalnie, bez dopełniaczy |
| Pozostałe opracowania własne zbioru (nawigacja, standard) | **co najmniej 45 000 znaków** | dokumenty porządkujące zbiór, nie opisujące pojedynczego bytu platformy w pełnym wykazie |

**Zakaz osiągania progu przez dopełniacz.** Wiersz powtórzony, akapit rozwodniony,
zdanie bez nowej informacji nie podnoszą jakości dokumentu, nawet jeśli podnoszą
licznik znaków. Objętość jest skutkiem kompletności wykazów i diagramów (rozdz. 3–4),
nie odwrotnie. Kontrola przyjęcia dokumentu sprawdza oba warunki niezależnie: próg
znakowy **i** komplet wykazów obowiązkowych — spełnienie jednego bez drugiego nie
domyka pracy redakcyjnej.

---

## 11. Najczęstsze usterki redakcyjne

Wykaz zebrany z audytu zbioru poprzedzającego niniejszy standard — każda pozycja
wystąpiła co najmniej kilkanaście razy w zbiorze przed redakcją. Wykaz służy jako
lista kontrolna przy przeglądzie każdego opracowania. Trzy ostatnie pozycje pochodzą
z fali redakcyjnej katalogu `specyfikacje/` — metryka zredukowana do jednego pola,
nagłówek sekcji zmieniony w tabeli zbiorczej bez zmiany w każdym z jego wystąpień
korpusu oraz opracowanie bez odsyłacza przychodzącego — i dokumentują usterki
odnalezione dopiero przy przeglądzie obejmującym cały zbiór naraz, nie pojedynczy plik.

| Usterka | Zapis błędny | Zapis wiążący |
|---|---|---|
| Cudzysłów niesparowany | `„Deweloperski"` | `„Deweloperski”` |
| Odsyłacz w backtickach zamiast markdown | `` `architektura/model-danych.md` `` | ``[Model danych](../architektura/model-danych.md)`` |
| Termin glosowany wariantowo w jednym pliku | „Hover (najechanie)” w jednym akapicie, „najechanie (hover)” w drugim | jedna postać w całym pliku: „wskazanie kursorem” |
| Numer rozdziału poza odsyłaczem | `1.1 [Tytuł](#…)` | `[1.1 Tytuł](#…)` |
| Odsyłacz do rozdziału, którego nie ma | `rozdz. 4.5` w pliku mającym rozdziały 4.1–4.4 | wskazanie rzeczywistego rozdziału po weryfikacji w pliku docelowym |
| Kod wymyślony jako odwołanie | „zgodnie z ADL-14” | nazwa rozstrzygnięcia wprost, bez kodu |
| Odmiana anglicyzmu po polsku | „checkboxa”, „toastu”, „mockupów” | „pola wyboru”, „dymka powiadomienia”, „makiet” |
| Wartość wpisana na sztywno zamiast żetonu | „przycisk w kolorze `#2F6FED`” | „przycisk w kolorze `--dn-sygnal`” |
| Sformułowanie otwierające interpretację | „ustawia odpowiedni znacznik” | „ustawia znacznik `sesja_aktywna`” albo `[DO DECYZJI OPERATORA]` |
| Pierwsza osoba liczby pojedynczej | „dodałem konto, a dalej odmawia” | forma bezosobowa: „po dodaniu konta system nadal odmawia” |
| Stopka niepełna albo brak stopki | plik kończy się ostatnim zdaniem korpusu | trzy bloki stopki z rozdz. 2.5 |
| Odsyłacz do nieistniejącego pliku | `budowa/docs/kontrakt.md` (katalog nieistniejący) | odsyłacz do rzeczywistego źródła `budowa/shared/contract.json` albo liczba podana wprost |
| Powielenie wykazu zamiast odsyłacza do źródła | własna kopia listy 68 obszarów kontraktu w kilku plikach | odsyłacz do `[Architektura techniczna](../architektura/architektura.md)` rozdz. 18, jedynego miejsca wykazu pełnego |
| Nazwa pliku kolidująca wielkością liter | `Instrukcja.md` obok `instrukcja.md` | jedna z dwóch nazw zmieniona na rzeczowo odrębną |
| Metryka niepełna — jedno pole zamiast jedenastu | `**Informacje szczegółowe dokumentu:**` z samym polem „Źródło” | komplet jedenastu pól rozdz. 2.1: Tytuł, Klasa dokumentu, Odbiorcy, Przeznaczenie, Zakres, Poza zakresem, Dokument nadrzędny, Dokumenty powiązane, Prototypy odniesienia (gdy dotyczy), Źródła normatywne, Zasada nadrzędna |
| Nagłówek sekcji przemianowany niespójnie w obrębie pliku | „Przebieg pracy modułu” w spisie wykazów rozdz. 4.2, „Workflow modułu” w każdym z piętnastu wystąpień korpusu | zamiana wszystkich wystąpień jednocześnie — jedna nazwa sekcji w całym pliku, nie tylko w tabeli zbiorczej |
| Opracowanie osierocone — bez odsyłacza przychodzącego | plik istnieje w katalogu tematycznym, lecz żadne inne opracowanie ani Spis opracowań do niego nie odsyła | dodanie odsyłacza z opracowania nadrzędnego wskazanego w polu „Dokument nadrzędny” własnej metryki pliku |

**Przykład: naprawa metryki niepełnej.** Poniższy fragment pokazuje usterkę spotykaną
najczęściej w opracowaniach redagowanych przed ustanowieniem niniejszego standardu —
drugą tabelę metryki zredukowaną do jednego, niewiążącego pola — oraz jej naprawę do
kompletu jedenastu pól rozdziału 2.1.

Zapis błędny:

```markdown
**Informacje szczegółowe dokumentu:**

| | |
|---|---|
| **Źródło** | Koncepcja platformy i architektura |
```

Zapis naprawiony — komplet pól, każde wypełnione treścią właściwą opisywanemu opracowaniu,
nie przepisaną z sąsiedniego pliku:

```markdown
**Informacje szczegółowe dokumentu:**

| | |
|---|---|
| **Tytuł** | {pełny tytuł opracowania} |
| **Klasa dokumentu** | Specyfikacja docelowa |
| **Odbiorcy** | deweloper · projektant |
| **Przeznaczenie** | {jedno zdanie: do czego dokument służy} |
| **Zakres** | {co dokument obejmuje} |
| **Poza zakresem** | {co świadomie pominięto i gdzie tego szukać} |
| **Dokument nadrzędny** | [Koncepcja platformy](../architektura/koncepcja-platformy.md) |
| **Dokumenty powiązane** | {odsyłacze rozdzielone `·`} |
| **Źródła normatywne** | {ścieżki źródeł} |
| **Zasada nadrzędna** | {jedno zdanie rozstrzygające} |
```

Naprawa nie ogranicza się do dopisania brakujących wierszy pustą treścią — pole
wypełnione frazą „do uzupełnienia” albo pozostawione puste jest tą samą usterką w innej
postaci. Każde z jedenastu pól niesie treść rzeczywiście prawdziwą dla redagowanego
pliku, ustaloną lekturą jego korpusu, nie skopiowaną z wzorca ani z sąsiedniego
opracowania tego samego katalogu.

---

## 12. Polecenia kontrolne dla redaktora

Rozdział podaje gotowe polecenia powłoki sprawdzające zgodność jednego pliku albo
całego zbioru z rozdziałami 2–8, bez potrzeby ręcznego przeglądu. Polecenia uruchamia
się z katalogu `docs/`.

**Cudzysłów prosty poza kodem** — zero wyników oznacza zgodność:

```bash
awk '!/^```/{f=!f} f{next} /"/{print FILENAME":"FNR}' **/*.md
```

**Odsyłacz w backtickach zamiast markdown** — każdy wynik wymaga zamiany na `[Tytuł](ścieżka)`:

```bash
grep -rnoE '`[a-z0-9/_-]+\.md`' --include='*.md' .
```

**Termin porzucony w prozie** (rozdz. 5.1) — dopasowanie poza blokiem kodu:

```bash
grep -rniE '\b(hover|preview|workflow|toast|placeholder|checkbox|tooltip|toggle|mockup|dashboard)\b' \
  --include='*.md' . | grep -v '^\s*```'
```

Wynik dla `dashboard` wymaga odsiania trzech dopuszczalnych wystąpień: nazwy własnej okna
„Project Dashboard” (rozdz. 5.2), nazwy komendy `workspace.dashboard.get` oraz pola
`dashboard:WorkspaceDashboard` — identyfikatory techniczne zamianie nie podlegają.

```bash
grep -rniE '\bdashboard\b' --include='*.md' . | grep -vE 'Project Dashboard|workspace\.dashboard|WorkspaceDashboard'
```

**Kod wymyślony** (rozdz. 7.1) — musi zwrócić zero:

```bash
grep -rnE '\bADL[- ]?[0-9]|\b[DPL]-[0-9]+\b' --include='*.md' .
```

**Brak stopki** — pliki, których trzy ostatnie niepuste wiersze nie zaczynają się
od `*Danaco Console`:

```bash
for f in $(find . -name '*.md'); do
  tail -5 "$f" | grep -q '^\*Danaco Console' || echo "brak stopki: $f"
done
```

**Objętość poniżej progu** (rozdz. 9):

```bash
for f in $(find . -name '*.md'); do
  n=$(wc -c < "$f"); echo "$n $f"
done | sort -n | head -20
```

**Odsyłacz martwy** — ścieżka niewskazująca istniejącego pliku:

```python
import re, glob, os
links = re.compile(r'\[([^\]]*)\]\(([^)#\s]+)(#[^)]*)?\)')
for f in glob.glob('**/*.md', recursive=True):
    txt = re.sub(r'```.*?```', '', open(f, encoding='utf-8').read(), flags=re.S)
    for m in links.finditer(txt):
        u = m.group(2)
        if u.startswith(('http', 'mailto:')):
            continue
        p = os.path.normpath(os.path.join(os.path.dirname(f), u))
        if not os.path.exists(p):
            print(f, u)
```

**Opracowanie osierocone** — plik `.md` katalogu `docs/`, do którego nie odsyła żaden
odsyłacz markdown z żadnego innego pliku zbioru poza Spisem opracowań; wynik jest listą
kandydatów do sprawdzenia, nie automatycznym wyrokiem — plik wskazany jako `[Spis
opracowań](../SPIS-OPRACOWAN.md)` w polu „Dokument nadrzędny” własnej metryki, lecz bez
odsyłacza przychodzącego z żadnego opracowania tematycznego, wymaga dodania takiego
odsyłacza w opracowaniu nadrzędnym:

```python
import re, glob, os

files = glob.glob('**/*.md', recursive=True)
incoming = {f: 0 for f in files}
link = re.compile(r'\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)')
for f in files:
    body = re.sub(r'```.*?```', '', open(f, encoding='utf-8').read(), flags=re.S)
    for m in link.finditer(body):
        u = m.group(1)
        if u.startswith(('http', 'mailto:')):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(f), u))
        if target in incoming and target != f:
            incoming[target] += 1
for f, n in sorted(incoming.items()):
    if n == 0 and f not in ('SPIS-OPRACOWAN.md',):
        print('osierocone:', f)
```

Trzy pliki są wyłączone spod tej kontroli z natury swojej roli, nie przez wyjątek
zapisany w skrypcie: `README.md` jest punktem wejścia czytelnika z zewnątrz zbioru i nie
wymaga odsyłacza przychodzącego z wnętrza `docs/`; `SPIS-OPRACOWAN.md` jest korzeniem
nawigacyjnym całego zbioru z definicji rozdziału 2.2; `LICENSE.md` jest aktem prawnym
przywoływanym ze stopki każdego pliku, co dla skryptu liczy się jako odsyłacz
przychodzący i w praktyce nigdy nie oznacza go jako osieroconego. Wynik dla pozostałych
czterdziestu ośmiu plików jest rozstrzygający — zero wystąpień oznacza zgodność, każde
inne oznacza plik do naprawy przez dodanie odsyłacza w opracowaniu nadrzędnym.

Żadne z powyższych poleceń nie zastępuje przeglądu merytorycznego — wykrywają wyłącznie
usterki mechaniczne. Kompletność wykazów normatywnych (rozdz. 4.2) i jakość diagramów
(rozdz. 3.3) sprawdza się wyłącznie lekturą.

**Kolejność stosowania.** Polecenia mechaniczne uruchamia się przed przeglądem
merytorycznym, nie po nim — usterka typograficzna albo odsyłacz martwy odwraca uwagę
recenzenta od treści i utrudnia ocenę kompletności wykazów. Redaktor przechodzący
opracowanie stosuje kolejność: odsyłacze i cudzysłowy (mechaniczne) → rama redakcyjna
(rozdz. 2) → terminologia (rozdz. 5) → normatywność (rozdz. 4) → formy wizualne
(rozdz. 3) → objętość (rozdz. 9). Odwrócenie kolejności — dociąganie objętości
przed uzupełnieniem wykazów — grozi dopełniaczem zakazanym w rozdz. 9.

Polecenia mechaniczne uruchamia się ponownie po każdej turze redakcji, aż do zerowego
wyniku wszystkich ośmiu kontroli — dopiero wtedy opracowanie jest gotowe do przeglądu
merytorycznego przez drugą osobę. Kontrola opracowania osieroconego różni się od
pozostałych siedmiu tym, że nie sprawdza pojedynczego pliku, lecz cały zbiór naraz —
uruchamiana jest po zakończeniu fali redakcyjnej obejmującej wiele opracowań, nie przy
każdym pojedynczym pliku z osobna.

**Moc wiążąca standardu.** Niniejszy standard jest wiążący dla wszystkich opracowań
katalogu `docs/` powstałych po dniu 2026-08-20 oraz dla redakcji opracowań powstałych
wcześniej, bez wyjątku co do klasy dokumentu.

---

*Koniec spisu standardu. Części standardu: `references/redakcja-dokumentu.md`,
`references/jezyk-i-typografia.md`, `references/konwencje-nazewnicze.md`,
`references/plik-referencyjny-skilla.md`.*
