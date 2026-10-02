---
name: odblokuj-siec
description: "Zdejmuje blokadę „sieć” (włączoną przez /blokuj-siec). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Zdjęcie blokady: sieć

Właściciel zdjął blokadę `/blokuj-siec`: dostęp do sieci wrócił. Pozostałe tryby sesji obowiązują bez zmian.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
