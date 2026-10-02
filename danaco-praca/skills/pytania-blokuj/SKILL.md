---
name: pytania-blokuj
description: "Blokada „pytania do właściciela”: włącza blokadę (zwalnia /pytania-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: pytania do właściciela

Właściciel włączył blokadę: odrzucane są narzędzia AskUserQuestion i ExitPlanMode. Przy niejednoznaczności przyjmujesz najrozsądniejsze założenie, zapisujesz je i pracujesz dalej.

Blokadę zwalnia wyłącznie właściciel poleceniem `/pytania-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
