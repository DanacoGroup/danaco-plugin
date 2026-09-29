# Język, ton i terminologia

## Podział języków

- Komentarze, dokumentacja, komunikaty w interfejsie: język polski.
- Identyfikatory w kodzie (nazwy zmiennych, funkcji, typów, pakietów, plików kodu):
  język angielski, zgodnie z konwencją danego języka programowania.
- Nie mieszasz: brak polskich nazw funkcji, brak angielskich komentarzy wyjaśniających.

## Ton

Ton formalny i rzeczowy, jak w dokumentacji technicznej. Unikasz:

- markerów nieformalnych: „btw”, „fyi”, „hack”, „hacky”, „magia”, „na szybko”, „chyba”,
  „raczej”, „jakoś”, „sorry”, „ups”,
- znaczników prowizorki w kodzie produkcyjnym: „todo”, „fixme”, „xxx” — otwarta praca
  należy do rejestru zadań, nie do komentarza,
- emocji i ocen w komentarzach („brzydkie, ale działa”, „nie pytaj dlaczego”).

## Terminologia

Używasz terminów przyjętych w projekcie i w normach, nie ukutych na miejscu:

- protokoły i formaty po nazwach standardów: IMAP, SMTP, MIME, TLS, WebSocket, JSON;
- pojęcia domenowe zgodnie z dokumentacją Danaco (np. `sprawa`, `dokument`, `kancelaria`);
- warstwy i komponenty zgodnie z istniejącą architekturą (kontrakt, most Tauri, kanał,
  rdzeń), a nie własnymi synonimami.

Gdy dla pojęcia istnieje termin w dokumentacji lub w normie — używasz go. Nie tworzysz
synonimu, bo brzmi lepiej.

## Dane wrażliwe

Pracujesz na danych prawnych objętych tajemnicą zawodową. W kodzie, komentarzach,
przykładach, testach i komunikatach błędów:

- nie umieszczasz nazwisk, treści pism, danych kontaktowych, sygnatur powiązanych z osobą;
- używasz identyfikatorów technicznych i danych syntetycznych o tym samym kształcie;
- sekrety (hasła, klucze, tokeny) trzymasz poza kodem.
