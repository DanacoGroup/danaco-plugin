# Sesje i równoległe tory AI

## Cykl życia sesji

```
opening --> ready --> suspended --> ready --> closing --> closed
```

- **opening** — uzgodniony skrót kontraktu, ustalony tryb, przydzielona przestrzeń danych;
  jeszcze żadnych zdarzeń dziedzinowych
- **ready** — sesja przyjmuje komunikaty
- **suspended** — połączenie zerwane, stan zachowany; wznowienie od numeru sekwencyjnego
- **closing** — tory AI domykane, bufory opróżniane, zapis stanu
- **closed** — zwolnione zasoby, wpis w dzienniku audytowym

Rozdzielenie `suspended` od `closed` jest istotne w aplikacji desktopowej: zerwane połączenie
(uśpiony laptop, restart rdzenia) nie jest tym samym co zamknięcie sesji przez użytkownika.
Traktowanie ich jednakowo oznacza utratę pracy przy każdym uśpieniu.

## Sesja wspólna a izolowana

**Sesja izolowana** to jeden tryb, własna przestrzeń, brak zdarzeń na zewnątrz. Prosta i domyślna.

**Sesja wspólna** obejmuje kilka trybów jednocześnie — użytkownik prowadzi sprawę, ma otwarte
dokumenty i terminarz, a zdarzenia z jednego modułu widać w drugim. Sesja wspólna nie znosi
macierzy: tryby wewnątrz niej nadal widzą tylko to, na co pozwala `CanRead`. Wspólna jest
**oś czasu zdarzeń**, nie dostęp do danych.

To rozróżnienie jest źródłem najczęstszego nieporozumienia przy projektowaniu. „Wspólna sesja”
brzmi jak „wspólny dostęp”, a oznacza wyłącznie „wspólny strumień zdarzeń, każdy filtrowany
zakresem odbiorcy”.

## Cztery tory AI

Do jednej sesji wolno podłączyć do czterech torów AI. Każdy to `AiChannel` z rolą
(`coordinator`, `builder`, `reviewer`, `researcher`), modelem, poziomem izolacji i budżetem.

### Stopnie izolacji toru

| Izolacja toru | Co widzi model | Zastosowanie |
|---|---|---|
| `shared` | zdarzenia sesji w zakresie trybu | koordynator, który musi wiedzieć, co robią pozostałe tory |
| `hybrid` | zdarzenia sesji, ale zapisuje do własnej przestrzeni | wykonawca — proponuje, nie zatwierdza |
| `isolated` | wyłącznie własny kontekst i to, co mu jawnie podano | kontroler, który ma ocenić wynik bez sugestii; praca na treści wrażliwej |

Izolacja toru **nigdy nie jest słabsza od izolacji trybu** — pilnuje tego walidator.

Tor `isolated` dla kontrolera nie jest ostrożnością, tylko warunkiem sensowności kontroli. Model,
który widzi rozumowanie wykonawcy, potwierdza je znacznie chętniej, niż gdy dostaje sam wynik.
Cztery modele zgadzające się ze sobą, bo widzą nawzajem swoje uzasadnienia, dają złudzenie
kontroli przy jej faktycznym braku.

### Budżety

`tokenBudget` jest twardy. Po wyczerpaniu tor kończy się `E_BUDGET_EXCEEDED` — bez prośby
o zwiększenie, bez cichego kontynuowania. W pętli działającej całą dobę bez człowieka budżet jest
jedynym mechanizmem, który zatrzymuje pracę, gdy zadanie okazało się źle postawione.

Budżet ustawiaj na tor, nie na sesję. Budżet sesyjny pozwala jednemu torowi zjeść cały przydział
i zagłodzić pozostałe trzy.

### Kolejność zdarzeń

Cztery tory produkują zdarzenia równolegle. Wspólna oś czasu sesji ma jeden licznik `seq`, więc
kolejność jest globalna i odtwarzalna. Bez tego wznowienie po zerwaniu połączenia dałoby przy
każdym odtworzeniu inny przeplot — a przy diagnozie usterki w pętli autonomicznej odtwarzalność
przeplotu jest jedynym punktem zaczepienia.

### Zapis

Zapis przez tor AI przechodzi przez `CanWrite` dokładnie tak samo jak zapis przez człowieka.
Model nie ma osobnej ścieżki do danych. Ma natomiast dwa dodatkowe ograniczenia:

- **tor `hybrid` i `isolated` pisze wyłącznie do własnej przestrzeni** — jego wynik trafia do
  przestrzeni roboczej, a przeniesienie go do przestrzeni trybu jest osobną, jawną operacją
- **każdy zapis jest odnotowany** z identyfikatorem toru, roli i modelu

Druga reguła jest tania, a bez niej po tygodniu pracy pętli nie da się odpowiedzieć na pytanie,
który model wprowadził daną zmianę.

## Wznowienie sesji z torami

Przy wznowieniu (`resumeFrom`) sesja odtwarza zdarzenia od podanego numeru. Tory AI **nie są
odtwarzane automatycznie** — zostają zamknięte przy przejściu w `suspended`, a po wznowieniu
podłącza się je na nowo, z tym samym budżetem pomniejszonym o zużycie.

Automatyczne wznawianie torów kusi, ale oznacza, że zerwane połączenie w środku pętli
autonomicznej pozostawia model pracujący nad kontekstem, którego już nikt nie ogląda.
Świadome ponowne podłączenie jest tańsze niż tydzień pracy w próżni.
