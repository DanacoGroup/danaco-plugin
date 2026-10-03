# Projekt Przykład — instrukcje dla Claude Code

<!-- Notatka dla opiekunów: plik < 200 wierszy; szczegóły w .claude/rules/ (ładowane według ścieżek). -->

## Polecenia
- Testy: `npm test` (pojedynczy plik: `npm test -- <ścieżka>`); uruchamiaj przed każdym commitem.
- Lint: `npm run lint`; formatowanie: `npm run format`.

## Architektura
- Obsługa API: `src/api/handlers/`; logika domenowa: `src/domain/` (bez importów z `src/api/`).
- Migracje bazy w `migrations/` — tylko nowe pliki, istniejących nie zmieniaj.

## Konwencje
- TypeScript strict; wcięcia 2 spacje; nazwy plików w kebab-case.
- Komunikaty commitów: `<obszar>: <co>` po polsku, bez stopki.

Szczegóły procesu wydań: @docs/wydania.md
