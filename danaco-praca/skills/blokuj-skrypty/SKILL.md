---
name: blokuj-skrypty
description: "Blokada „pisanie ręczne”: włącza blokadę (zwalnia /odblokuj-skrypty). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: pisanie ręczne

Właściciel włączył blokadę: odrzucane są generowanie treści plików poleceniami i skryptami: przekierowania i `tee` do plików (poza dziennikami `.log`/`.out`/`.err`, `/tmp` i `$TMPDIR`), edytory w miejscu, `patch`, `truncate`, `dd of=`, kod podany wprost i skrypty, które zapisują pliki. Pliki zmieniasz wyłącznie narzędziami Edit i Write.

Blokadę zwalnia wyłącznie właściciel poleceniem `/odblokuj-skrypty`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
