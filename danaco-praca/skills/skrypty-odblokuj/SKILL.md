---
name: skrypty-odblokuj
description: "Zdejmuje blokadę „pisanie ręczne” (włączoną przez /skrypty-blokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Zdjęcie blokady: pisanie ręczne

Właściciel zdjął blokadę `/skrypty-blokuj`: generowanie treści skryptami znów dozwolone. Pozostałe tryby sesji obowiązują bez zmian.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
