---
name: bez-masowych
description: "Blokada pracy masowej: włącza blokadę (zwalnia /z-masowymi). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Blokada pracy masowej

Właściciel włączył blokadę: odrzucana jest hurtowa, maszynowa zmiana plików: `sed -i`, `perl -pi` i inne edytory w miejscu na więcej niż jednym pliku (albo z maską, rekurencyjnie), `find -exec`/`-delete`, `xargs` i `parallel` z poleceniem zmieniającym pliki, pętle po plikach z zapisem, kod i skrypty zapisujące pliki w pętli, `patch`, `git apply`, `git reset --hard`, `git checkout .`, hurtowy `UPDATE`/`DELETE` w bazie. Pliki edytujesz pojedynczo narzędziami Edit i Write. Powód: hurtowa podmiana treści na setkach tysięcy plików zniszczyła kiedyś bazę danych.

Blokadę zwalnia wyłącznie właściciel poleceniem `/z-masowymi`.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
