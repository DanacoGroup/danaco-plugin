---
name: kanal-websocket
description: >
  Kanał komunikacyjny Danaco Console między rdzeniem Go a interfejsem TypeScript: jedna
  koperta komunikatu, korelacja żądanie–odpowiedź, numeracja sekwencyjna, wznowienie po
  zerwaniu połączenia, heartbeat, przeciwciśnienie oraz równoległe strumienie czterech torów
  AI w jednej sesji. Stosuj, gdy powstaje obsługa komunikatu po stronie rdzenia lub klienta,
  a także gdy pada „połączenie się rwie”, „klient gubi zdarzenia”, „komunikat nie dochodzi”,
  „zdarzenia przychodzą w złej kolejności”, „aplikacja nie wraca po uśpieniu laptopa”,
  „strumień AI się urywa” albo „jak wznowić sesję”. Sięgaj po nią też przy projektowaniu
  przeciwciśnienia i diagnozie wyścigów po ponownym połączeniu. Sam kształt komunikatu
  deklaruje się najpierw w `kontrakt-zrodlo-prawdy` — ta paczka odpowiada za transport,
  kolejność i wznowienie.
---

# Kanał komunikacyjny

## Kiedy stosować

Stosuj, gdy powstaje albo zmienia się obsługa komunikatu po stronie rdzenia lub klienta, przy
diagnozie zerwanych połączeń, gubionych zdarzeń, złej kolejności i urwanych strumieni AI oraz
przy projektowaniu przeciwciśnienia.

Nie stosuj tej paczki do zadeklarowania nowego komunikatu — kształt koperty i lista
komunikatów mieszkają w `shared/contract.json`, którym zajmuje się `kontrakt-zrodlo-prawdy`.
Kolejność jest ustalona: najpierw kontrakt, potem ta paczka. Tego, co dany tryb widzi
i gdzie zapisuje, nie rozstrzyga ta paczka, lecz `macierz-trybow-sesji`; ról, budżetów
i warunków stopu toru AI — `orkiestracja-agentow`; komend IPC powłoki — `most-tauri`.

Zasada nadrzędna: kanał ma **jeden kształt koperty, jeden licznik i jeden mechanizm
wznowienia** — wspólne dla wszystkich komunikatów i wszystkich torów. Uśpiony laptop zrywa
połączenie, restart rdzenia gubi stan, wolny odbiorca zapycha bufor, a cztery tory AI
produkują zdarzenia szybciej, niż interfejs je rysuje — i ponieważ dzieje się to rzadko, kod
obsługi tych przypadków bywa pisany raz i nigdy nie sprawdzany.

## Koperta

Wszystko podróżuje w jednej kopercie generowanej z kontraktu:

| Pole | Rola |
|---|---|
| `id` | identyfikator koperty, unikalny w sesji |
| `correlation_id` | wiąże odpowiedź z żądaniem; puste w komunikatach rozgłoszeniowych |
| `session_id` | sesja, do której należy komunikat |
| `mode_id` | tryb sesyjny — wyznacza zakres widoczności po stronie rdzenia |
| `channel` | grupa komunikatów (`session`, `ai`, …) |
| `seq` | numer w globalnym strumieniu sesji |
| `type` | nazwa komunikatu z kontraktu |
| `payload` | ładunek, którego typ wyznacza `type` |
| `error_code`, `error_message` | kod z kontraktu i ogólna treść; nigdy dane sprawy |

Jeden licznik `seq` na sesję, nie na kanał ani na tor. To decyduje o odtwarzalności: przeplot
zdarzeń z czterech torów AI jest przy każdym wznowieniu identyczny. Osobne liczniki dawałyby
przy każdym odtworzeniu inną kolejność, a przy diagnozie usterki w pętli autonomicznej nie
byłoby czego się chwycić.

## Procedura: dodanie obsługi komunikatu

1. Upewnij się, że komunikat jest już w `shared/contract.json` (paczka
   `kontrakt-zrodlo-prawdy`). Jeśli nie jest, zacznij tam.
2. Skopiuj narzędzie do repozytorium (raz, obok `contract_tool.py`):
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/kanal-websocket/scripts/channel_tool.py" \
     tools/channel_tool.py
   ```
3. Wygeneruj rozdzielacze i sprawdź rozjazd wobec kontraktu:
   ```bash
   python3 tools/channel_tool.py gen   --root .   # rozdzielacze Go i TypeScript
   python3 tools/channel_tool.py check --root .   # rozjazd wobec kontraktu
   ```
   Ścieżki wyjściowe zmienisz przez `--go-out` i `--ts-out`. Import pakietu kontraktu w Go
   i ścieżka do `contract.ts` są wyliczane z sekcji `generated` kontraktu oraz z `go.mod`,
   więc przeniesienie plików jest zmianą w kontrakcie, nie w narzędziu.
4. Zaimplementuj metodę interfejsu `Handler` w rdzeniu i wpis w `ServerEvents` w kliencie —
   dopóki tego nie zrobisz, kompilacja ma być zepsuta.
5. Uruchom `task channel:check` oraz kompilację obu światów.

Generowane pliki: `server/internal/transport/dispatch_gen.go` (interfejs `Handler`
i `Dispatch`) oraz `client/src/channel/dispatch_gen.ts` (interfejs `ServerEvents`
i `dispatchEnvelope`).

Sens tego generowania: **dopisanie komunikatu do kontraktu ma zepsuć kompilację**, dopóki
nikt go nie obsłuży. Rozdzielacz pisany ręcznie milczy na nieznany komunikat, a milczenie
w kanale jest najtrudniejszą do zdiagnozowania klasą usterek — nic nie zawodzi, po prostu nic
się nie dzieje.

`Dispatch` sprawdza również kierunek: klient nie może podszyć się pod komunikat serwerowy. Po
stronie klienta jest odwrotnie — nieznany komunikat trafia do `onUnknown`, bo starszy
interfejs musi przeżyć nowszy rdzeń.

## Kryteria zakończenia

Zmiana w kanale jest gotowa, gdy zachodzą wszystkie pięć warunków:

- `task contract:check` i `task channel:check` zwracają `0`;
- oba światy się kompilują (`go build ./...`, `npx tsc --noEmit`) i żadna metoda `Handler`
  ani wpis `ServerEvents` nie został pominięty;
- ścieżka wznowienia jest sprawdzona: przy `E_RESUME_GAP` klient przeładowuje stan w całości,
  nie wznawia od czegokolwiek;
- limit kolejki wychodzącej jest ustawiony, a decyzja przy jego przekroczeniu jest
  zadeklarowana osobno dla fragmentów odpowiedzi modelu, zdarzeń stanu i komunikatów
  sesyjnych;
- `error_message` nie zawiera danych sprawy.

## Wznowienie po zerwaniu

Gotowa, przetestowana implementacja leży w `assets/resume_buffer.go` wraz z testami
w `assets/resume_buffer_test.go`. Skopiuj oba pliki do `server/internal/transport/`.

Mechanika:

1. Rdzeń numeruje każdą wychodzącą kopertę i trzyma ostatnie N w buforze.
2. Klient zapamiętuje numer ostatniej odebranej koperty.
3. Po ponownym połączeniu wysyła `resumeFrom` w `SessionOpenRequest`.
4. Rdzeń odsyła ogon strumienia (od `resumeFrom + 1`) albo `E_RESUME_GAP`, jeśli żądany numer
   wypadł już z bufora — albo jeśli klient podaje numer **wyższy** niż ostatni nadany, co
   oznacza rozjazd sesji, a nie stan przejściowy.

**`E_RESUME_GAP` musi prowadzić do pełnego przeładowania stanu, nie do cichego wznowienia od
czegokolwiek.** Dziura w strumieniu zdarzeń jest gorsza od przeładowania, bo przeładowanie
widać, a dziurę odkrywa się dwie godziny później po niezgodnym stanie ekranu.

Pojemność bufora to kompromis: za mała oznacza częste przeładowania przy każdym uśpieniu
laptopa, za duża trzyma w pamięci zdarzenia, po które nikt nie wróci. Punkt wyjścia: tyle
zdarzeń, ile sesja produkuje przez kilka minut normalnej pracy.

## Cztery tory AI w jednym kanale

Tory AI nie dostają osobnych połączeń. Dzielą kanał sesji, a rozróżnia je `channelId`
w ładunku.

- **Jeden wolny tor nie może zagłodzić pozostałych.** Przy przeciwciśnieniu odrzucaj lub
  scalaj fragmenty `AiDelta` konkretnego toru, nie wstrzymuj całego kanału.
- **Fragmenty jednego toru muszą zachować kolejność względem siebie**, ale nie muszą jej
  zachować względem innych torów. Globalny `seq` daje odtwarzalność; wewnętrzny `seq`
  w `AiDelta` daje kolejność w obrębie toru.
- **Zamknięcie toru jest zdarzeniem**, nie ciszą. Interfejs, który rozpoznaje koniec
  strumienia po braku kolejnych fragmentów, będzie się mylił przy każdym zerwaniu połączenia.

## Przeciwciśnienie

Cztery modele piszące strumieniowo potrafią wyprodukować więcej zdarzeń, niż interfejs zdąży
narysować. Kolejka bez ograniczenia rośnie do wyczerpania pamięci, a w instalacji on-premise
nie ma autoskalowania, które to zamaskuje.

Reguła: **kolejka wychodząca ma twardy limit, a jego przekroczenie jest decyzją, nie
awarią.** Dla fragmentów odpowiedzi modelu właściwą decyzją jest scalenie kilku fragmentów
w jeden; dla zdarzeń stanu — odrzucenie starszych, bo liczy się ostatni; dla komunikatów
sesyjnych — nigdy odrzucenie, bo od nich zależy poprawność.

Rozwinięcie wraz z wzorcami: `references/przeciwcisnienie-i-wznowienie.md`.

## Heartbeat

Zerwane połączenie TCP potrafi nie zgłosić się przez wiele minut. Bez heartbeatu interfejs
pokazuje „połączono”, gdy od dawna nie ma połączenia. Obie strony wysyłają ping w stałym
odstępie i zamykają połączenie po dwóch nieodebranych. Wartości dobierz tak, żeby wykrycie
zajmowało kilkanaście sekund — dłużej znaczy, że użytkownik zdąży kliknąć w martwy interfejs.

## Częste pułapki

- **Wyścig przy ponownym połączeniu.** Klient wysyła `SessionOpen` z `resumeFrom`, zanim
  domknie poprzednie połączenie; rdzeń widzi dwie sesje. Domykaj poprzednie połączenie przed
  otwarciem nowego i odrzucaj drugie otwarcie tej samej sesji.
- **Numer sekwencyjny nadawany przez klienta.** Numeruje wyłącznie strona wysyłająca,
  a strumień do klienta numeruje wyłącznie rdzeń. Dwa źródła numeracji to gwarantowany
  rozjazd.
- **Korelacja po `id` zamiast po `correlation_id`.** `id` jest unikalne dla koperty;
  odpowiedź ma własne `id` i wskazuje żądanie przez `correlation_id`.
- **Obsługa komunikatu dopisana z pominięciem rozdzielacza.** Wtedy `check` przestaje
  cokolwiek gwarantować, bo generowany plik już nie opisuje rzeczywistości.
- **Dane sprawy w `error_message`.** Komunikat błędu bywa logowany i pokazywany — kod
  z kontraktu plus identyfikator techniczny, nigdy treść.
- **Zamykanie sesji przy zerwaniu połączenia.** `suspended` i `closed` to różne stany;
  zlanie ich w jeden oznacza utratę pracy przy każdym uśpieniu laptopa.

## Materiały

- `references/koperta-i-korelacja.md` — pola koperty, wzorce żądanie–odpowiedź, rozgłoszenia,
  błędy
- `references/przeciwcisnienie-i-wznowienie.md` — bufor wznowienia, limity kolejki,
  heartbeat, wyścigi
- `assets/resume_buffer.go`, `assets/resume_buffer_test.go` — gotowy bufor wznowienia
  z testami
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — cele `channel` i `channel:check`

## Rozgraniczenie z paczkami sąsiednimi

- `kontrakt-zrodlo-prawdy` — deklaracja koperty, komunikatów i kodów błędów. Krok pierwszy.
- `macierz-trybow-sesji` — co tryb i tor AI widzi oraz gdzie zapisuje.
- `orkiestracja-agentow` — role, kolejka, budżety i warunki stopu torów AI.
- `most-tauri` — co idzie komendą IPC, a co kanałem.
