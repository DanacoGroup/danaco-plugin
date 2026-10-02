---
name: sudo-odblokuj
description: "Przywraca sudo zgodnie z uprawnieniami konta (zdejmuje /sudo-blokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Sudo zgodnie z kontem

Właściciel zdjął blokadę `/sudo-blokuj`: sudo znów działa zgodnie z uprawnieniami konta. Pozostałe tryby sesji obowiązują bez zmian.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
