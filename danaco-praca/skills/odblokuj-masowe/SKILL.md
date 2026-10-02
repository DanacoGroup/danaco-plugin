---
name: odblokuj-masowe
description: "Zdejmuje blokadę „praca masowa” (włączoną przez /blokuj-masowe). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Zdjęcie blokady: praca masowa

Właściciel zdjął blokadę `/blokuj-masowe`: praca masowa znów dozwolona. Pozostałe tryby sesji obowiązują bez zmian.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
