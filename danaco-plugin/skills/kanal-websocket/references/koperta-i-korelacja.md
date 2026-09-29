# Koperta, korelacja i wzorce wymiany

## Spis treści

1. [Trzy wzorce wymiany](#trzy-wzorce-wymiany)
2. [Korelacja](#korelacja)
3. [Błędy w kanale](#błędy-w-kanale)
4. [Strumienie](#strumienie)
5. [Wersjonowanie komunikatów](#wersjonowanie-komunikatów)

## Trzy wzorce wymiany

Wszystko, co przechodzi przez kanał, mieści się w trzech wzorcach. Warto nazwać je wprost, bo
mieszanie ich jest źródłem większości nieporozumień przy projektowaniu nowego komunikatu.

**Żądanie–odpowiedź.** Klient wysyła `SessionOpen`, rdzeń odpowiada `SessionOpened` z tym samym
`correlation_id`. Klient czeka. W kontrakcie komunikat żądania ma pole `response`.

**Rozgłoszenie.** Rdzeń wysyła `SessionStateChanged` do wszystkich obserwatorów sesji.
Bez `correlation_id`, bez oczekiwania, bez gwarancji, że kogokolwiek to obchodzi.

**Strumień.** Rdzeń wysyła ciąg `AiDelta` z rosnącym numerem wewnętrznym, zakończony fragmentem
z `final: true`. Strumień jest powiązany z żądaniem przez `correlation_id`, ale nie jest
odpowiedzią w sensie żądanie–odpowiedź: nie ma jednego momentu, w którym „przychodzi”.

Pytanie, które rozstrzyga przy projektowaniu nowego komunikatu: **czy nadawca czeka?**
Jeśli tak — żądanie–odpowiedź. Jeśli nie i jest jeden komunikat — rozgłoszenie. Jeśli nie i jest
ich wiele — strumień, i wtedy trzeba od razu zaprojektować zakończenie oraz przerwanie.

## Korelacja

- `id` — nowe dla każdej koperty, także dla odpowiedzi
- `correlation_id` — w odpowiedzi i w każdym fragmencie strumienia równe `id` żądania

Korelowanie po `id` zamiast po `correlation_id` działa dopóty, dopóki nie pojawi się strumień: wtedy
wszystkie fragmenty musiałyby mieć to samo `id`, co psuje jednoznaczność koperty i uniemożliwia
odróżnienie duplikatu od kolejnego fragmentu.

Klient trzyma mapę `correlation_id` → oczekujące żądanie, z **czasem wygaśnięcia**. Wpis bez
wygaśnięcia oznacza, że zerwane połączenie w środku żądania zostawia obietnicę, która nigdy się
nie rozstrzygnie — i element interfejsu, który kręci się w nieskończoność.

## Błędy w kanale

Błąd nie jest osobnym komunikatem, tylko kopertą z wypełnionym `error_code`:

```json
{
  "id": "…",
  "correlation_id": "…",
  "type": "session.opened",
  "error_code": "E_MODE_UNKNOWN",
  "error_message": "Nieznany tryb sesyjny."
}
```

Dzięki temu klient obsługuje błąd w tym samym miejscu, w którym czeka na odpowiedź, zamiast
w osobnej gałęzi obsługi błędów, którą łatwo pominąć.

Trzy reguły dotyczące treści:

- `error_code` pochodzi z kontraktu, nigdy z łańcucha znaków w kodzie
- `error_message` jest ogólne i nie zawiera nazwisk, sygnatur powiązanych z osobą ani treści pism
- szczegóły potrzebne do diagnozy przekazuj identyfikatorem technicznym, po którym da się je
  odnaleźć w dzienniku serwera — dziennik ma węższy krąg odbiorców niż ekran użytkownika

## Strumienie

Strumień musi mieć zaprojektowane trzy rzeczy, i wszystkie trzy bywają pomijane:

**Zakończenie.** Fragment z `final: true`. Rozpoznawanie końca po ciszy zawodzi przy każdym
zerwaniu połączenia.

**Przerwanie.** Użytkownik zamyka panel, przełącza tryb, przerywa generowanie. Bez komunikatu
przerwania model po drugiej stronie pracuje dalej i zużywa budżet na wynik, którego nikt nie
zobaczy — a przy czterech torach i pętli całodobowej to nie jest strata teoretyczna.

**Wznowienie.** Po ponownym połączeniu strumień albo jest kontynuowany od numeru wewnętrznego,
albo jawnie unieważniony. Trzeciej możliwości — cichego porzucenia — nie ma, bo interfejs
zostaje z połową odpowiedzi i bez informacji, że to już wszystko.

## Wersjonowanie komunikatów

Komunikat jest częścią kontraktu, więc obowiązują te same zasady co przy typach (patrz
umiejętność `kontrakt-zrodlo-prawdy`). Trzy przypadki specyficzne dla kanału:

- **Nowe pole opcjonalne w ładunku** — zmiana dodająca; starsza strona zignoruje nieznany klucz.
- **Nowy komunikat serwerowy** — zmiana dodająca **pod warunkiem**, że klient ma gałąź
  `onUnknown`. Bez niej starszy klient wywróci się na nieznanym typie. Dlatego generowany
  rozdzielacz TypeScriptu ma tę gałąź od początku.
- **Zmiana kierunku komunikatu** — zawsze zmiana łamiąca; `Dispatch` po stronie rdzenia odrzuci
  komunikat wysłany w niedozwoloną stronę, więc starszy klient przestanie działać natychmiast.
  To dobrze: cichy przypadek byłby gorszy.
