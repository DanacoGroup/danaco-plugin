---
name: odblokuj-zapis
description: "Zdejmuje blokadę „zapis plików (tryb tylko-odczyt)” (włączoną przez /blokuj-zapis). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Zdjęcie blokady: zapis plików (tryb tylko-odczyt)

Właściciel zdjął blokadę `/blokuj-zapis`: zapis plików znów dozwolony. Pozostałe tryby sesji obowiązują bez zmian.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
