# Przeciwciśnienie, wznowienie i wyścigi

## Bufor wznowienia

Gotowa implementacja z testami: `assets/resume_buffer.go` i `assets/resume_buffer_test.go`.

```go
bufor := transport.NewResumeBuffer(2048)

// Wysylka: bufor nadaje numer i zapamietuje koperte.
env = bufor.Append(env)
_ = conn.WriteJSON(env)

// Po ponownym polaczeniu:
ogon, err := bufor.Since(req.ResumeFrom)
if errors.Is(err, transport.ErrResumeGap) {
    // Dziura w strumieniu. Pelne przeladowanie stanu jest jedyna uczciwa odpowiedzia.
    return odesliPelnyStan(sesja)
}
for _, e := range ogon {
    _ = conn.WriteJSON(e)
}
```

Dobór pojemności: tyle zdarzeń, ile sesja produkuje przez kilka minut normalnej pracy. Przy
czterech torach AI pracujących strumieniowo to rząd tysięcy, a nie dziesiątek. Zbyt mały bufor
oznacza pełne przeładowanie przy każdym uśpieniu laptopa — technicznie poprawne, w odbiorze
uciążliwe.

Bufor jest **na sesję**, nie na połączenie. Bufor związany z połączeniem znika dokładnie wtedy,
gdy jest potrzebny.

## Limity kolejki wychodzącej

Kolejka bez limitu rośnie do wyczerpania pamięci. W instalacji on-premise nie ma nic, co by to
zamaskowało — proces po prostu padnie, zwykle w środku pracy.

Limit ma być twardy, a jego przekroczenie **decyzją zależną od rodzaju komunikatu**:

| Rodzaj | Decyzja przy przepełnieniu | Dlaczego |
|---|---|---|
| komunikat sesyjny (otwarcie, zamknięcie, zmiana stanu) | nigdy nie odrzucaj; zwolnij nadawcę | od nich zależy poprawność stanu |
| zdarzenie stanu (postęp, licznik) | odrzuć starsze, zachowaj ostatnie | liczy się wyłącznie wartość bieżąca |
| fragment odpowiedzi modelu (`AiDelta`) | scal kilka fragmentów w jeden | użytkownik i tak nie czyta szybciej niż model pisze |
| zdarzenie audytowe | nigdy nie odrzucaj; zapisz na dysk | dziennik z dziurami nie jest dziennikiem |

Kluczowe: **przeciwciśnienie dotyczy toru, nie kanału**. Wstrzymanie całego kanału, bo jeden tor
AI produkuje szybciej, niż interfejs rysuje, zatrzymuje też komunikaty sesyjne — i użytkownik
traci możliwość przerwania tego, co go zalewa.

## Heartbeat

```
ping co 5 s  ->  brak dwóch odpowiedzi  ->  zamknij połączenie  ->  wznów
```

Zerwane połączenie TCP potrafi milczeć minutami. Bez heartbeatu interfejs pokazuje „połączono”,
gdy połączenia dawno nie ma, a użytkownik klika w martwy ekran i uznaje, że aplikacja zamarła.

Heartbeat wysyłają obie strony. Sam ping od klienta nie wykryje sytuacji, w której to rdzeń
przestał odbierać.

## Wyścigi przy ponownym połączeniu

Trzy sytuacje, które w praktyce występują, i które trzeba obsłużyć jawnie:

**Podwójne otwarcie.** Klient wykrywa zerwanie i otwiera nowe połączenie, zanim stare zdąży się
domknąć po stronie rdzenia. Rdzeń widzi dwie sesje o tym samym identyfikatorze. Rozwiązanie:
otwarcie sesji, która jest już otwarta, zamyka poprzednie połączenie — ostatni wygrywa.

**Wznowienie w trakcie strumienia.** Tor AI był w połowie odpowiedzi. Po wznowieniu albo
dokończ strumień od numeru wewnętrznego, albo wyślij fragment z `final: true` i kodem przerwania.
Ciche porzucenie zostawia interfejs z połową odpowiedzi bez informacji, że to koniec.

**Zdarzenia z okresu rozłączenia.** Rdzeń pracował dalej — pętla autonomiczna nie zatrzymuje się
dlatego, że ktoś zamknął laptopa. Po wznowieniu klient dostaje ogon strumienia, który może liczyć
tysiące zdarzeń. Wysyłaj go paczkami i pozwól interfejsowi rysować w międzyczasie, zamiast blokować
go jednym wielkim ładunkiem.

## Diagnoza

Objawy i pierwszy trop:

| Objaw | Pierwszy trop |
|---|---|
| klient gubi pojedyncze zdarzenia | limit kolejki odrzuca komunikaty, których odrzucać nie wolno |
| zdarzenia w złej kolejności | osobne liczniki `seq` zamiast jednego na sesję |
| interfejs pokazuje „połączono”, nic nie przychodzi | brak heartbeatu; połączenie martwe od minut |
| po wznowieniu podwójne zdarzenia | ogon wysłany od `seq`, a nie od `seq+1` |
| po wznowieniu brakujące zdarzenia | `E_RESUME_GAP` obsłużone jako ostrzeżenie zamiast przeładowania |
| pamięć rdzenia rośnie w czasie | kolejka wychodząca bez limitu albo bufor wznowienia bez ograniczenia |
| komunikat nie wywołuje żadnej reakcji | obsługa dopisana z pominięciem generowanego rozdzielacza |

Ostatni wiersz jest najczęstszy przy pracy zespołowej i najtrudniejszy do zauważenia, bo nic nie
zawodzi — po prostu nic się nie dzieje. `task channel:check` w haku pre-commit wyklucza tę
możliwość, zanim zamieni się w godzinę szukania.
