---
name: bash-blokuj
description: "Blokada „Bash”: włącza blokadę (zwalnia /bash-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: Bash

Właściciel włączył blokadę: odrzucane są narzędzie Bash, a także PowerShell, Monitor i narzędzia MCP wykonujące polecenia powłoki.

Blokadę zwalnia wyłącznie właściciel poleceniem `/bash-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
