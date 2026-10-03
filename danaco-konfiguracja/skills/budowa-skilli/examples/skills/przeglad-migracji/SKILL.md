---
name: przeglad-migracji
description: >
  Przegląd migracji bazy danych przed scaleniem: odwracalność, blokady tabel, utrata
  danych, kolejność wdrożenia z kodem. Stosuj, gdy pada „sprawdź migrację”, „czy ta
  migracja jest bezpieczna”, „review migracji”, albo gdy zmiana zawiera pliki w
  migrations/. Nie pisze migracji — tylko je ocenia i raportuje ryzyka.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/analizuj_migracje.py *)
---

# Przegląd migracji

## Kiedy stosować

Przed scaleniem zmiany z plikami w `migrations/` albo na prośbę o ocenę migracji.
Nie poprawiaj migracji sam — raportuj ryzyka i proponuj poprawki.

## Procedura

1. Uruchom analizę statyczną:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/analizuj_migracje.py <katalog migracji>`
2. Dla każdej flagi skryptu oceń ryzyko według `references/ryzyka.md`.
3. Sprawdź, czy kod aplikacji działa przed i po migracji (wdrożenie dwufazowe).
4. Raport według `examples/raport.md`: ryzyko, waga, dowód (plik:wiersz), poprawka.

## Pułapki

- `ALTER TABLE … ADD COLUMN … NOT NULL` bez wartości domyślnej blokuje i zawodzi na danych.
- Usunięcie kolumny w tej samej wersji co kod, który jej używa, psuje wdrożenie stopniowe.
- Migracja bez kroku `down` jest nieodwracalna — to nie zawsze błąd, ale musi być jawne.
