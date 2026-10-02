---
name: siec-blokuj
description: "Blokada „sieć”: włącza blokadę (zwalnia /siec-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: sieć

Właściciel włączył blokadę: odrzucane są narzędzia WebFetch i WebSearch oraz w powłoce `curl`, `wget`, `nc`, `ssh`, `scp`, `sftp`, `git clone`/`fetch`/`pull`/`push` i pobieranie menedżerami pakietów (`pip`/`npm`/`uv`/`cargo`/`hf` install/download). Pracujesz na danych lokalnych.

Blokadę zwalnia wyłącznie właściciel poleceniem `/siec-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
