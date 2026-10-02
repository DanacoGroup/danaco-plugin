---
name: bez-bash
description: "Blokada narzędzia Bash: włącza blokadę (zwalnia /z-bash). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Blokada narzędzia Bash

Właściciel włączył blokadę: narzędzie Bash (a także PowerShell, Monitor i narzędzia MCP wykonujące polecenia powłoki) jest odrzucane. Pracujesz narzędziami Read, Grep, Glob, Edit i Write.

Blokadę zwalnia wyłącznie właściciel poleceniem `/z-bash`.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
