---
name: koniec-pracy
description: "Kończy tryb pracy ciągłej włączony poleceniem /praca. Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Koniec pracy ciągłej

Właściciel wyłączył tryb pracy ciągłej: wolno Ci zakończyć turę. Złóż krótki raport
w punktach — co zrobiono, wynik, co zostało otwarte, procesy nadal działające w tle
(z plikiem dziennika) — i zakończ turę. Pozostałe blokady sesji obowiązują bez zmian.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
