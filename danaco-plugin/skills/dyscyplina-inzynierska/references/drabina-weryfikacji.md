# Drabina weryfikacji — stos Danaco

Wyrocznią gotowości zmiany są narzędzia, nie deklaracja. Uruchamiasz właściwy zestaw
i czytasz wynik. Poniżej narzędzia realnie dostępne w środowisku.

## Go (rdzeń)

```bash
goimports -w <pliki>            # formatowanie i import
golangci-lint run ./...         # zbiorczy linter
staticcheck ./...               # analiza statyczna
go vet ./...                    # kontrola poprawności
go build ./...                  # kompilacja
gotestsum -- ./...              # testy z czytelnym raportem
```

Zależnie od zmiany:

```bash
sqlc generate                   # regeneracja warstwy zapytań po zmianie SQL
oapi-codegen ...                # regeneracja klienta/serwera po zmianie OpenAPI
mockery                         # regeneracja atrap interfejsów
dlv debug ...                   # diagnoza pod debuggerem
```

## TypeScript / Vite (interfejs)

```bash
tsc --noEmit                    # kontrola typów
vitest run                      # testy jednostkowe
pnpm build   # lub: bun run build / npm run build — build produkcyjny Vite
npx playwright test             # testy E2E (przeglądarki już pobrane)
```

## Rust / Tauri 2 (powłoka)

```bash
cargo fmt --check               # formatowanie
cargo clippy -- -D warnings     # linter
cargo test                      # testy
cargo tauri build               # build powłoki (sccache + mold + clang przyspieszają)
```

## Repozytorium i dyscyplina

```bash
task flow:check                 # zbiorcza kontrola repozytorium (gdy zdefiniowana)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py" verify <ścieżki>
```

## Kolejność

1. Formatowanie i import (`goimports`, `cargo fmt`, formater klienta).
2. Kontrola typów i lintery (`tsc`, `golangci-lint`, `staticcheck`, `clippy`).
3. Testy (`gotestsum`, `vitest`, `cargo test`, Playwright), w tym nowy test regresyjny.
4. Build całości.
5. Dyscyplina: `style_guard.py` + `nazwy_guard.py` (razem przez `mass_actions.py verify`).

Zmiana bez przejścia właściwych szczebli nie jest gotowa, niezależnie od tego,
jak pewny jesteś wyniku.
