---
name: sudo-nie
description: "Blokada sudo: włącza blokadę sudo w poleceniach powłoki (zwalnia /sudo-tak). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Blokada sudo

Właściciel zablokował sudo: odrzucane są `sudo`, `doas`, `pkexec`, `run0` i `su -c` w poleceniach powłoki, także w `ssh host '…'` i `bash -c '…'`. Polecenia wykonujesz bez podnoszenia uprawnień.

Blokadę zwalnia wyłącznie właściciel poleceniem `/sudo-tak`.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
