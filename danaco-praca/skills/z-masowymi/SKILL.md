---
name: z-masowymi
description: "Zdejmuje blokadę włączoną poleceniem /bez-masowych. Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Zdjęcie blokady /bez-masowych

Właściciel zdjął blokadę `/bez-masowych`. Pozostałe tryby sesji obowiązują bez zmian.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
