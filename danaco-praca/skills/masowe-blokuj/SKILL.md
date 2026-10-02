---
name: masowe-blokuj
description: "Blokada „praca masowa”: włącza blokadę (zwalnia /masowe-odblokuj). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: praca masowa

Właściciel włączył blokadę: odrzucane są hurtowa, maszynowa zmiana plików: `sed -i`/`perl -pi` na więcej niż jednym pliku, z maską albo rekurencyjnie, `find -exec`/`-delete`, `xargs`/`parallel` z zapisem, pętle po plikach z zapisem, kod i skrypty zapisujące pliki w pętli, `patch`, `git apply`, `git reset --hard`, `git checkout .`, hurtowy `UPDATE`/`DELETE` bez `WHERE`. Pliki edytujesz pojedynczo narzędziami Edit i Write. Przyczyna: hurtowa podmiana treści na setkach tysięcy plików zniszczyła kiedyś bazę danych.

Blokadę zwalnia wyłącznie właściciel poleceniem `/masowe-odblokuj`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
