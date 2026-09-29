# Standardy kodu Danaco

## Komentarze

Komentarz istnieje po to, by wyjaśnić decyzję nieoczywistą z kodu — „dlaczego tak”,
nie „co robi ta linia”. Kod czytelny dzięki nazwom nie wymaga opisu.

Limity egzekwowane przez walidator:

- pojedynczy komentarz ciągły: najwyżej 350 znaków (blok kolejnych linii liczony łącznie),
- udział komentarzy: najwyżej 20% wierszy pliku (liczony od 40 wierszy kodu),
- najwyżej cztery zdania w jednym komentarzu (ostrzeżenie o eseju),
- rozbicie eseju pustą linią nie omija limitu — sąsiadujące obszerne bloki liczą się razem.

Źle — esej z historią decyzji:

```go
// Ta funkcja przeszła długą ewolucję. Początkowo używaliśmy innego podejścia,
// ale okazało się ono problematyczne, więc po wielu dyskusjach w zespole
// zdecydowaliśmy się przepisać ją tak, jak wygląda teraz, co moim zdaniem jest
// znacznie lepsze, choć nadal nie idealne i pewnie kiedyś to jeszcze zmienimy.
func parseHeader(raw []byte) (Header, error) { ... }
```

Dobrze — rzeczowa nota „dlaczego”:

```go
// Nagłówek IMAP bywa kodowany MIME (RFC 2047); dekodujemy przed parsowaniem.
func parseHeader(raw []byte) (Header, error) { ... }
```

## Logowanie

W środowisku on-premise log serwera jest podstawowym źródłem prawdy. Nie zostawiaj
`print`, `console.log`, `fmt.Println` diagnostycznych — używaj loggera projektu.

- Loguj zdarzenie i kontekst techniczny (`sprawa_id`, `dokument_id`, typ operacji, wynik),
  nigdy treść danych sprawy.
- Poziomy: `DEBUG` diagnostyka, `INFO` zdarzenia biznesowe, `WARNING` sytuacja podejrzana,
  `ERROR` awaria ze śladem.
- Loguj strukturalnie z identyfikatorem korelacji, by powiązać wpisy jednego żądania.
- Logowanie tymczasowe przy diagnozie usuwaj po naprawie.

## Struktura pliku

- Jeden plik to jedna odpowiedzialność. Duży plik dzielisz wzdłuż granic funkcji, nie
  wzdłuż wygody.
- Zakomentowany kod nie wchodzi do repozytorium — od tego jest historia gita.
- Import i formatowanie zostawiasz narzędziom (`goimports`, `cargo fmt`, formater klienta),
  nie ręcznie.

## Obsługa błędów

- Diagnozujesz przyczynę źródłową, nie maskujesz objawu.
- Komunikat błędu zawiera identyfikatory techniczne, nie treść rekordu.
- Każda zmiana logiki dostaje test regresyjny odtwarzający dokładny scenariusz.
