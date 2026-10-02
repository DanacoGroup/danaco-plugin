---
name: z-skryptami
description: "Zdejmuje blokadę włączoną poleceniem /reczne-pisanie. Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Zdjęcie blokady /reczne-pisanie

Właściciel zdjął blokadę `/reczne-pisanie`. Pozostałe tryby sesji obowiązują bez zmian.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
