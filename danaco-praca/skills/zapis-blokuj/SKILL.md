---
name: zapis-blokuj
description: "Blokada „zapis plików (tryb tylko-odczyt)”: włącza blokadę (zwalnia /zapis-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: zapis plików (tryb tylko-odczyt)

Właściciel włączył blokadę: odrzucane są narzędzia Write, Edit, MultiEdit i NotebookEdit oraz w powłoce każda zmiana plików: `rm`, `mv`, `cp`, `mkdir`, `touch`, `ln`, `tee`, przekierowania poza `/tmp`, `$TMPDIR` i dziennikami, edytory w miejscu, `git commit`/`add`/`reset`/`checkout`… Odczyt, analiza, `grep`, `git diff`/`log` i budowa przechodzą.

Blokadę zwalnia wyłącznie właściciel poleceniem `/zapis-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
