# Ryzyka migracji — skala ocen

| Flaga skryptu | Ryzyko | Waga | Bezpieczna alternatywa |
|---|---|---|---|
| `DROP_COLUMN` | utrata danych, błąd starego kodu | krytyczna | wycofaj użycie w kodzie, usuń w następnym wydaniu |
| `NOT_NULL_BEZ_DOMYSLNEJ` | błąd na istniejących wierszach | krytyczna | dodaj z wartością domyślną, uzupełnij, potem `NOT NULL` |
| `RENAME` | błąd starego kodu przy wdrożeniu stopniowym | ważna | nowa kolumna + kopiowanie + przełączenie |
| `INDEX_BEZ_CONCURRENTLY` | blokada zapisu na czas budowy | ważna | `CREATE INDEX CONCURRENTLY` |
| `BRAK_DOWN` | brak wycofania | drobna | dopisz `down` albo udokumentuj nieodwracalność |
