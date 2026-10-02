---
name: reczne-pisanie
description: "Pisanie ręczne: włącza blokadę (zwalnia /z-skryptami). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Pisanie ręczne

Właściciel włączył blokadę: pliki zmieniasz wyłącznie narzędziami Edit i Write. Odrzucane jest generowanie treści poleceniem lub skryptem: przekierowania i `tee` do plików (poza dziennikami `.log`/`.out`/`.err`, `/tmp` i `$TMPDIR`), edytory w miejscu, `patch`, `truncate`, `dd of=`, kod podany wprost i skrypty, które zapisują pliki. Kopiowanie, przenoszenie i kasowanie do kosza przechodzą.

Blokadę zwalnia wyłącznie właściciel poleceniem `/z-skryptami`.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
