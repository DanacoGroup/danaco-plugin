---
name: macierz-trybow-sesji
description: >
  Macierz trybów sesyjnych Danaco Console: 4 środowiska po 8–10 modułów (32–40 trybów),
  poziomy izolacji `shared`/`hybrid`/`isolated`, macierz widoczności danych, mosty między
  środowiskami oraz reguły podłączania równoległych torów AI do jednej sesji. Stosuj, gdy
  zmienia się to, co dany tryb widzi lub gdzie zapisuje, gdy podłączany jest model AI do
  sesji, a także gdy pada „czy ten moduł powinien widzieć dane tamtego”, „sesja wspólna czy
  izolowana”, „ile modeli może pracować w jednej sesji”, „dane wyciekają między sprawami”
  albo „jak zaprojektować nowe środowisko”. Sięgaj po nią przy audycie izolacji. Rejestr
  trybów mieszka w kontrakcie (`kontrakt-zrodlo-prawdy`); pętlę modeli, budżety i warunki
  stopu prowadzi `orkiestracja-agentow`.
---

# Macierz trybów sesyjnych

## Kiedy stosować

Stosuj, gdy zmienia się to, co dany tryb widzi lub gdzie zapisuje, gdy podłączany jest model
AI do sesji, przy projektowaniu nowego środowiska, przy audycie izolacji oraz przy podejrzeniu
wycieku danych między sprawami.

Nie stosuj tej paczki do samego wpisania trybu do rejestru — rejestr trybów mieszka
w `shared/contract.json`, którym zajmuje się `kontrakt-zrodlo-prawdy`. Ról, kolejki, budżetów
i warunków stopu pętli modeli nie prowadzi ta paczka, lecz `orkiestracja-agentow`; przepływu
zdarzeń toru przez kanał — `kanal-websocket`.

Cztery środowiska po 8–10 modułów dają od 32 do 40 trybów sesyjnych (kontrakt startowy ma
32). Liczba możliwych par „kto widzi kogo” przekracza tysiąc, a pomyłka nie objawia się
awarią — objawia się tym, że w module rozliczeń widać treść pisma z cudzej sprawy. To
najcięższa możliwa usterka w systemie z danymi objętymi tajemnicą zawodową i jedyna, której
kompilator nigdy nie wykryje. Dlatego macierz musi być **danymi w kontrakcie**, sprawdzanymi
maszynowo, a nie ustaleniem w dokumentacji.

## Zasada nadrzędna

> Widoczność jest deklarowana, wąska domyślnie i egzekwowana w rdzeniu.
> Kontrola po stronie interfejsu chroni przed pomyłką, nie przed obejściem.

## Trzy poziomy izolacji

| Poziom | Czyta | Pisze | Kiedy |
|---|---|---|---|
| `shared` | wszystkie tryby współdzielone swojego środowiska | własną przestrzeń | moduły składające się na jeden obraz pracy: sprawy, dokumenty, terminarz |
| `hybrid` | jak wyżej | wyłącznie własną przestrzeń | moduły korzystające z kontekstu, ale nieuprawnione do jego zmiany: kolejka zadań, konfiguracja agentów |
| `isolated` | wyłącznie siebie | wyłącznie siebie | moduły o podwyższonej wrażliwości: pisma, klienci, sekrety, rozliczenia |

Tryb izolowany nie tylko niczego nie widzi — **nikt nie widzi jego**. Walidator odrzuca odczyt
z trybu izolowanego, bo inaczej słowo „izolowany” przestaje cokolwiek znaczyć.

Wyboru dokonuj po stronie ostrożniejszej. Rozszerzenie widoczności później jest zmianą
dodającą; zawężenie jej po tym, jak moduły zdążyły się przyzwyczaić, jest zmianą łamiącą
i zwykle nie zostaje wykonane.

## Deklaracja w kontrakcie

Macierz mieszka w `shared/contract.json`, w sekcji `modes`. Pola `reads`, `writes` i `ai` są
opcjonalne — pominięte przyjmują wąskie wartości domyślne wynikające z poziomu izolacji.

```json
{
  "id": "studio.agenci",
  "environment": "studio",
  "module": "agenci",
  "isolation": "hybrid",
  "doc": "Konfiguracja modeli AI i ról",
  "ai": { "allowed": true, "maxChannels": 4, "isolation": "hybrid" }
}
```

Przejście między środowiskami wymaga jawnego wpisu w `modeBridges` **wraz z uzasadnieniem**:

```json
"modeBridges": [
  {
    "from": "crm.kontrahenci",
    "to": "kancelaria.sprawy",
    "reason": "Kartoteka kontrahenta pokazuje liczbę spraw prowadzonych dla podmiotu; przez most przechodzą wyłącznie identyfikatory i liczniki, nigdy treść akt."
  }
]
```

Wymóg uzasadnienia nie jest biurokracją. Cztery środowiska są niezależne z założenia, więc
każdy most jest wyjątkiem od tego założenia — a wyjątek bez zapisanego powodu po pół roku
wygląda jak reguła i zostaje rozszerzony.

## Procedura: zakładanie lub zmiana trybu

1. Ustal środowisko i sprawdź, czy nie przekroczy limitu modułów.
2. Wybierz izolację — po stronie ostrożniejszej.
3. Dopisz tryb do `modes` w kontrakcie. Zakresy zostaw domyślne, dopóki nie okażą się za
   wąskie.
4. Jeśli tryb potrzebuje danych z innego środowiska, dopisz most z uzasadnieniem; nie
   rozszerzaj zakresu po cichu.
5. Uruchom łańcuch: `task contract` (kod z kontraktu) → `task modes` (tablice zakresów) →
   `task modes:check` → `task modes:report`.
6. Obejrzyj diagram widoczności: sprawdź, czy nowy tryb ma strzałki, których się nie
   spodziewałeś.

## Narzędzie

```bash
MT="${CLAUDE_PLUGIN_ROOT}/skills/macierz-trybow-sesji/scripts/modes_tool.py"

python3 "$MT" validate --root .                   # czy macierz jest sensowna
python3 "$MT" gen      --root .                   # shared/scopes.go i client/src/scopes.ts
python3 "$MT" check    --root .                   # czy kod odwzorowuje macierz
python3 "$MT" report   --root . --out MACIERZ.md  # macierz i diagram widoczności
```

Skopiuj narzędzie do `tools/` obok `contract_tool.py` i wołaj stamtąd — z tego samego powodu,
dla którego wersjonuje się generator kontraktu.

`validate` i `check` pilnują dwóch różnych rzeczy i żadne nie zastępuje drugiego. `validate`
mówi, czy macierz jest sensowna; `check` — czy wygenerowane tablice ją odwzorowują. Sama
walidacja przepuściłaby poprawiony kontrakt z niezregenerowanymi tablicami widoczności, a to
znaczy izolację, która wygląda na wprowadzoną i nie działa. Oba wchodzą do haka pre-commit
i do bramki akceptacji pętli AI.

`gen` wytwarza tablicę `ModeScopes` oraz funkcje `CanRead`, `CanWrite` i `AIChannelAllowed`
po obu stronach. To one są egzekucją macierzy: **wołaj je przy wejściu do warstwy danych**,
nie tylko przy budowaniu interfejsu.

## Kryteria zakończenia

Zmiana macierzy jest gotowa, gdy zachodzą wszystkie pięć warunków:

- `modes_tool.py validate` zwraca `0`;
- `modes_tool.py check` zwraca `0` po regeneracji tablic (`task modes`);
- `task modes:report` wygenerował diagram, a diagram został obejrzany i nie zawiera strzałek
  niezamierzonych;
- każdy nowy most ma wpis w `modeBridges` z uzasadnieniem, prowadzi wyłącznie do trybu
  `shared` i pozwala tylko czytać;
- izolacja każdego toru AI nie jest słabsza od izolacji trybu, w którym tor pracuje.

## Niezmienniki, których pilnuje walidator

- każde środowisko ma 8–10 modułów (`--min-modules`, `--max-modules`)
- każdy tryb ma jawnie zadeklarowaną izolację o wartości z enumu `IsolationLevel`
- `reads` i `writes` wskazują wyłącznie istniejące tryby
- każdy tryb czyta i zapisuje własną przestrzeń — brak tego jest zawsze błędem macierzy
- tryb `isolated` i `hybrid` pisze wyłącznie do własnej przestrzeni
- tryb `shared` zapisuje poza siebie tylko do innych trybów `shared` tego samego środowiska
- nikt nie czyta z trybu izolowanego
- każde przejście między środowiskami ma wpis w `modeBridges` z uzasadnieniem; most prowadzi
  wyłącznie do trybu `shared`, łączy dwa różne środowiska i nie powtarza się
- most pozwala **czytać**, nigdy pisać
- tryb z pustą listą `writes` jest odrzucany — jest albo martwy, albo niedopowiedziany
- `ai.maxChannels` mieści się między 1 a projektowym limitem czterech torów
  (`--max-ai-channels`)
- **izolacja toru AI nigdy nie jest słabsza od izolacji trybu**

Ostatni punkt jest najważniejszy. Gdyby tor AI w trybie izolowanym mógł działać w trybie
współdzielonym, podłączenie modelu byłoby obejściem granicy, którą tryb miał wyznaczać — i to
obejściem wyglądającym na funkcję, a nie na usterkę.

## Cztery tory AI w jednej sesji

Sesja współdzielona może mieć do czterech równoległych torów AI. Każdy tor to osobny
`AiChannel` z własną rolą, modelem, poziomem izolacji i budżetem.

1. **Tor widzi tyle, ile jego poziom izolacji, nie tyle, ile sesja.** Tor `isolated` w sesji
   współdzielonej nie widzi tego, co widzą pozostałe tory — nawet jeśli technicznie siedzą
   w tej samej sesji.
2. **Tor ma budżet i budżet jest twardy.** `tokenBudget` w kontrakcie to nie sugestia; po
   jego wyczerpaniu tor kończy się kodem `E_BUDGET_EXCEEDED`.
3. **Zapis przez tor AI przechodzi przez `CanWrite` tak samo jak zapis przez człowieka.**
   Model nie ma osobnej, szerszej ścieżki do danych. Naruszenie kończy się
   `E_ISOLATION_VIOLATION`.

Rozwinięcie mechaniki torów i sesji: `references/sesje-i-tory-ai.md`.

## Częste pułapki

- **Domyślnie szeroki zakres „na wszelki wypadek”.** Zakres, którego nikt nie potrzebuje, i
  tak zostanie kiedyś użyty — a zawężenie go później nie jest już zmianą dodającą.
- **Tryb izolowany, który „tylko podgląda” cudzy stan.** To nie jest tryb izolowany. Jeśli
  podgląd jest potrzebny, właściwą odpowiedzią jest `hybrid` albo most z uzasadnieniem.
- **Kontrola widoczności wyłącznie w interfejsie.** Interfejs można ominąć — kanałem
  WebSocket, komendą Tauri, restartem z innym stanem. Granicę wyznacza rdzeń.
- **Tor AI dziedziczący izolację sesji zamiast własnej.** Sesja współdzielona nie oznacza, że
  wszystkie tory widzą to samo.
- **Most bez uzasadnienia.** Po pół roku nikt nie pamięta, czy to była decyzja, czy obejście.
- **Tryb dodany w kodzie, nie w kontrakcie.** Rejestr przestaje być kompletny, a wraz z nim
  routing, uprawnienia i cała macierz.
- **Poprawiony kontrakt bez regeneracji tablic.** Macierz mówi jedno, `CanRead` robi drugie.
  `validate` tego nie wykryje — od tego jest `check`, i dlatego oba muszą być w haku
  pre-commit.

## Materiały

- `references/projektowanie-izolacji.md` — jak wybierać poziom izolacji, wzorce i przypadki
  graniczne
- `references/sesje-i-tory-ai.md` — cykl życia sesji, sesje wspólne i izolowane, cztery tory
  AI
- `assets/scopes_test.go` — test Go sprawdzający, że macierz nie ma dziur: każdy tryb czyta
  i zapisuje siebie, nikt nie czyta z izolowanego, tryb spoza kontraktu nie ma żadnych praw
- `${CLAUDE_PLUGIN_ROOT}/skills/kontrakt-zrodlo-prawdy/assets/Taskfile.yml` — cele `modes`, `modes:check`
  i `modes:report`

## Rozgraniczenie z paczkami sąsiednimi

- `kontrakt-zrodlo-prawdy` — rejestr trybów i wpisanie nowego trybu do kontraktu.
- `orkiestracja-agentow` — jak tor pracuje: role, kolejka, budżety, warunki stopu.
- `kanal-websocket` — jak przepływają zdarzenia toru: przeplot, `seq`, przeciwciśnienie.
- `architektura-i-dokumentacja` — projekt nowego środowiska na poziomie architektury.
