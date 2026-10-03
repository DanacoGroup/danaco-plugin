---
name: zasady-commitow
description: Zasady komunikatów commitów zespołu (format, zakres, język). Stosuj, gdy pada „napisz commit”, „komunikat commita”, „zatwierdź zmiany”. Nie wykonuje push.
allowed-tools: Bash(git diff *) Bash(git status *)
---

# Zasady commitów

1. Pierwszy wiersz: `<obszar>: <czasownik w trybie rozkazującym> <co>` — do 72 znaków, po polsku.
2. Pusty wiersz, potem uzasadnienie „dlaczego”, nie „co” (to widać w diffie).
3. Jeden commit = jedna zmiana logiczna; nie łącz refaktoryzacji z poprawką.
4. Przed commitem: `git diff --staged` i testy obszaru.
