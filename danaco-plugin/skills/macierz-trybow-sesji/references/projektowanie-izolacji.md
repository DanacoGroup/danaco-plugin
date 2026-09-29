# Projektowanie izolacji trybu

## Spis treści

1. [Pytanie rozstrzygające](#pytanie-rozstrzygające)
2. [Wzorce](#wzorce)
3. [Przypadki graniczne](#przypadki-graniczne)
4. [Mosty między środowiskami](#mosty-między-środowiskami)
5. [Egzekwowanie w kodzie](#egzekwowanie-w-kodzie)

## Pytanie rozstrzygające

Przy wyborze poziomu izolacji nie pytaj „czy ten moduł potrzebuje tych danych”. Prawie zawsze
odpowiedź brzmi „przydałyby się”. Pytaj:

> **Co się stanie, jeśli te dane pojawią się tutaj przez pomyłkę?**

Dla modułu terminarza odpowiedź brzmi: użytkownik zobaczy termin z innej swojej sprawy —
niewygodne, ale nie szkodliwe. Dla modułu pism: użytkownik zobaczy treść pisma z cudzej sprawy —
to naruszenie tajemnicy zawodowej.

Ta asymetria decyduje. Terminarz może być `shared`, pisma muszą być `isolated`.

## Wzorce

**Rdzeń pracy — `shared`.** Moduły, które razem składają się na jeden obraz sprawy: rejestr spraw,
dokumenty, terminarz, wyszukiwarka. Rozdzielenie ich zamieniłoby aplikację w zestaw niepowiązanych
narzędzi, a użytkownik i tak ma dostęp do wszystkich.

**Konsument kontekstu — `hybrid`.** Moduł, który potrzebuje wiedzieć, co się dzieje, ale nie ma
prawa niczego zmieniać w cudzej przestrzeni: kolejka zadań, konfiguracja agentów, przepływy.
`hybrid` jest właściwą odpowiedzią wszędzie tam, gdzie kusi „shared, ale tylko do odczytu” —
i jest dokładnie tym mechanizmem.

**Wrażliwa treść — `isolated`.** Pisma, kartoteka klientów, rozliczenia, sekrety, archiwum.
Zasada: jeśli moduł przechowuje treść, a nie metadane, domyślnie jest izolowany.

**Rozróżnienie treść–metadane** jest w tym systemie najbardziej użytecznym narzędziem
projektowym. `kancelaria.sprawy` trzyma sygnatury, statusy i terminy — metadane, więc `shared`.
`kancelaria.pisma` trzyma treść — więc `isolated`. Ten sam podział pozwala budować mosty:
przez most przechodzą liczniki i identyfikatory, nigdy treść.

## Przypadki graniczne

**„Moduł raportów potrzebuje danych ze wszystkich modułów”.** Nie potrzebuje danych — potrzebuje
liczb. Raport buduj na agregatach publikowanych przez moduły źródłowe, nie na dostępie do ich
stanu. Moduł raportów zostaje `shared` w obrębie środowiska i czyta agregaty.

**„Wyszukiwarka musi przeszukiwać wszystko, także pisma”.** To najtrudniejszy przypadek w tym
systemie. Właściwe rozwiązanie: indeks buduje moduł izolowany, a wyszukiwarka dostaje wyniki
w postaci identyfikatorów, po których użytkownik przechodzi do modułu izolowanego — gdzie
obowiązuje normalna kontrola dostępu. Wyszukiwarka nigdy nie trzyma treści.

**„Dwa moduły ciągle wymieniają dane, izolacja przeszkadza”.** Jeśli wymiana jest stała i
dwukierunkowa, prawdopodobnie to jeden moduł podzielony na dwa. Scal je albo zaakceptuj wspólną
przestrzeń — utrzymywanie fikcyjnej granicy z dziesiątkiem wyjątków jest gorsze niż jej brak.

**„Tryb ma być izolowany, ale musi widzieć konfigurację”.** Konfiguracja nie jest danymi sprawy.
Trzymaj ją poza macierzą trybów — w warstwie, do której odwołuje się rdzeń, a nie tryb.

## Mosty między środowiskami

Cztery środowiska są niezależne z założenia. Most jest wyjątkiem, więc:

- ma kierunek — `from` czyta `to`, nie odwrotnie; **most nigdy nie uprawnia do zapisu**
- ma uzasadnienie, w którym stoi **co dokładnie przez most przechodzi**
- prowadzi wyłącznie do trybu `shared` po drugiej stronie; do trybu izolowanego most nie prowadzi
  nigdy, bo to zaprzeczenie izolacji
- łączy dwa **różne** środowiska; w obrębie jednego środowiska widoczność opisuje pole `reads`

Wszystkie cztery reguły egzekwuje `modes_tool.py validate` — most łamiący którąkolwiek z nich
zatrzymuje bramkę, a nie trafia do przeglądu przy najbliższym wydaniu.

Przeglądaj listę mostów przy każdym większym wydaniu. Rosnąca liczba mostów oznacza, że podział
na środowiska przestaje odpowiadać temu, jak system jest naprawdę używany — i lepiej zmienić
podział świadomie, niż zszywać go wyjątkami.

## Egzekwowanie w kodzie

`modes_tool.py gen` wytwarza `CanRead`, `CanWrite` i `AIChannelAllowed`. Wywołuj je w jednym
miejscu — na wejściu do warstwy danych:

```go
// server/internal/store/guard.go

// Read wydaje stan trybu target sesji działającej w trybie mode.
// Kontrola siedzi tutaj, a nie w handlerach, bo handlerów jest kilkadziesiąt
// i pominięcie kontroli w jednym z nich nie zostawia śladu.
func (s *Store) Read(mode, target shared.ModeID, klucz string) ([]byte, error) {
    if !shared.CanRead(mode, target) {
        return nil, shared.ErrIsolationViolation
    }
    return s.read(target, klucz)
}
```

Dwie rzeczy są tu istotne. Po pierwsze, kontrola jest **jedna** — rozproszona po handlerach
zamienia się w kontrolę, której gdzieś brakuje. Po drugie, błąd zwraca kod z kontraktu i nie
zawiera nazwy ani treści — komunikat o naruszeniu izolacji nie może sam być wyciekiem.

Do tego test, który pilnuje, żeby macierz nie miała dziur: `assets/scopes_test.go`.
