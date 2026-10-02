---
name: sudo-tak
description: "Przywraca sudo zgodnie z uprawnieniami konta (zdejmuje /sudo-nie). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Sudo zgodnie z kontem

Właściciel zdjął blokadę sudo: `sudo` działa zgodnie z uprawnieniami konta.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
