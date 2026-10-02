---
name: sudo-blokuj
description: "Blokada sudo: odrzuca podnoszenie uprawnień w powłoce (zwalnia /sudo-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada sudo

Właściciel włączył blokadę: odrzucane są `sudo`, `doas`, `pkexec`, `run0` i `su -c` w poleceniach powłoki, także w `ssh host '…'`, `bash -c '…'` i `find -exec`. Polecenia wykonujesz bez podnoszenia uprawnień.

Blokadę zwalnia wyłącznie właściciel poleceniem `/sudo-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
