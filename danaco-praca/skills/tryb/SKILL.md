---
name: tryb
description: "Pokazuje bieżący stan trybu pracy i wszystkich blokad tej sesji. Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Stan trybów

Stan trybu pracy i blokad pokazuje właścicielowi hook `UserPromptSubmit` (samo `/tryb` nie trafia do modelu). Jeżeli czytasz tę instrukcję, przepisz właścicielowi tabelę stanu z kontekstu dodanego przez hook — bez komentarza.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
