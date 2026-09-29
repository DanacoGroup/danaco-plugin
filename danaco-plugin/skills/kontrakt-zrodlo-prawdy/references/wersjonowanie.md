# Wersjonowanie kontraktu i zmiany łamiące

## Dlaczego to jest trudniejsze niż w usłudze webowej

W aplikacji webowej klient i serwer aktualizują się razem — użytkownik odświeża stronę i ma nowy
kod. Danaco Console jest aplikacją desktopową (Tauri 2) w środowisku on-premise. Rdzeń Go,
interfejs TypeScript i powłoka Rust są pakowane razem, ale w praktyce rozjeżdżają się:
użytkownik odkłada aktualizację, instalacja przerywa się w połowie, na jednej stacji jest
wersja z zeszłego miesiąca.

Kontrakt musi więc znieść sytuację, w której obie strony mają różne wersje.

## Skala zmian

| Rodzaj zmiany | Wersja | Czy starsza strona przeżyje |
|---|---|---|
| nowe pole `optional` | MINOR | tak — zignoruje nieznany klucz |
| nowy typ | MINOR | tak |
| nowy komunikat | MINOR | tak, o ile nie jest wymagany do działania |
| nowy tryb | MINOR | tak — starszy interfejs go nie pokaże |
| nowa wartość enumu | **MAJOR** | nie — starszy strażnik `isX` ją odrzuci |
| nowe pole wymagane | **MAJOR** | nie — starsza strona go nie wyśle |
| usunięcie / zmiana nazwy pola | **MAJOR** | nie |
| zmiana typu pola | **MAJOR** | nie |
| zmiana kierunku komunikatu | **MAJOR** | nie |
| usunięcie trybu | **MAJOR** | nie — sesje w tym trybie osierocone |

Nowa wartość enumu jest w tej tabeli najczęściej niedocenianą pozycją. Wygenerowany strażnik
`isIsolationLevel` w starszym kliencie zwróci `false` dla nowej wartości i komunikat zostanie
odrzucony. Jeśli enum ma się rozrastać, zaprojektuj go od razu z gałęzią „nieznane”: po stronie
TypeScriptu obsłuż `default` w `switch`, po stronie Go nie polegaj wyłącznie na `Valid()`.

## Wycofywanie pola — wzorzec trzech wydań

1. **Wydanie N.** Dodaj nowe pole jako `optional`. Rdzeń wypełnia oba: stare i nowe. Interfejs
   czyta nowe, jeśli jest, w przeciwnym razie stare. W kontrakcie dopisz do `doc` starego pola
   `PRZESTARZAŁE od 1.4.0, użyj deadlineAt`.
2. **Wydanie N+1.** Interfejs przestaje czytać stare pole. Rdzeń nadal je wypełnia — bo w terenie
   są jeszcze klienci z wydania N-1.
3. **Wydanie N+2.** Usuń stare pole z kontraktu i podnieś `MAJOR`.

Skrócenie tego cyklu jest kuszące i regularnie kończy się awarią u klienta, który pominął jedną
aktualizację.

## Bramka skrótu kontraktu

Generator umieszcza w obu plikach `ContractHash` — skrót kanonicznej postaci `contract.json`.
Wykorzystaj go przy otwarciu połączenia:

```go
// server/internal/transport/handshake.go
if req.ContractHash != shared.ContractHash {
    // Rozjazd wersji wykrywamy natychmiast, zamiast pozwolić mu objawić się
    // jako brakujące pole trzy ekrany dalej.
    return shared.ErrContractMismatch
}
```

Po stronie interfejsu przechwyć `E_CONTRACT_MISMATCH` i pokaż komunikat o konieczności
aktualizacji zamiast ogólnego błędu połączenia.

**Ograniczenie, o którym trzeba pamiętać.** Skrót liczy się z `contract.json`, nie z plików
wygenerowanych. Ręczna edycja `contract.go` albo `contract.ts` nie zmienia skrótu, więc bramka
ją przepuści — obie strony zgłoszą zgodność mimo rozjechanego kodu. Tę klasę usterek wykrywa
wyłącznie `task contract:check`, i dlatego musi on być podpięty pod pre-commit oraz pod wydanie.
Bramka skrótu chroni przed rozjazdem **wersji**, strażnik przed rozjazdem **kodu**; to dwie
różne rzeczy.

**Kiedy poluzować bramkę.** Ścisłe porównanie skrótu odrzuca też zmiany czysto dodające, które
starszy klient przeżyłby bez szkody. Jeśli to zbyt ostre, porównuj `MAJOR` z `contractVersion`
zamiast skrótu, a skrót loguj. Zacznij jednak od ostrej bramki — poluzowanie na podstawie
zaobserwowanych problemów jest bezpieczniejsze niż odwrotna kolejność.

## Migracja danych utrwalonych

Kontrakt opisuje dane w ruchu, ale jego kształty bywają utrwalane: zapis stanu sesji, kolejka
zadań, dziennik audytowy. Zmiana łamiąca w kontrakcie dotyka wtedy również danych na dysku.

Przed zmianą łamiącą sprawdź, czy zmieniany typ jest gdzieś serializowany do trwałego magazynu.
Jeśli tak, zmiana potrzebuje kroku migracyjnego i wersji zapisu — zwykle pola `schemaVersion`
w utrwalanym rekordzie, niezależnego od `contractVersion`.

## Zapis historii zmian

Prowadź `shared/CHANGELOG.md` z jedną pozycją na wersję kontraktu:

```markdown
## 1.4.0 — 2026-08-22
- Dodano `SprawaRef.deadlineAt` (opcjonalne). Wycofuje `SprawaRef.termin` — usunięcie w 2.0.0.
- Dodano tryb `kancelaria.egzekucje` (isolation: isolated).
```

Przy 40 trybach sesyjnych i wielu wydaniach to jedyny praktyczny sposób, żeby odpowiedzieć na
pytanie „od kiedy to pole istnieje”, bez przekopywania historii git.
