---
name: polecenie-wdrozenia
description: Wdrożenie wersji na środowisko testowe z kontrolą stanu repozytorium. Stosuj, gdy człowiek wywoła /polecenie-wdrozenia; model nie uruchamia go sam.
disable-model-invocation: true
argument-hint: "[środowisko]"
arguments: [srodowisko]
allowed-tools: Bash(git status *) Bash(./scripts/wdroz.sh *)
---

## Stan repozytorium
!`git status --short || true`

## Zadanie
Wdróż bieżącą wersję na środowisko `$srodowisko` (domyślnie `test`):
1. Jeśli powyżej są niezatwierdzone zmiany — przerwij i wypisz je.
2. Uruchom `./scripts/wdroz.sh $srodowisko`.
3. Zgłoś wynik i adres wdrożenia z wyjścia skryptu.
