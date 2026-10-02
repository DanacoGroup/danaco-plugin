---
name: blokuj-podagenci
description: "Blokada „podagenci”: włącza blokadę (zwalnia /odblokuj-podagenci). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: podagenci

Właściciel włączył blokadę: odrzucane są narzędzia Agent, Task, Workflow i TeamCreate oraz `claude -p` i `codex exec` w powłoce. Całą pracę wykonujesz sam.

Blokadę zwalnia wyłącznie właściciel poleceniem `/odblokuj-podagenci`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
