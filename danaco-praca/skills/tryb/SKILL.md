---
name: tryb
description: "Pokazuje bieżący stan trybu pracy i wszystkich blokad tej sesji. Przełącza i ogląda wyłącznie właściciel."
disable-model-invocation: true
---

# Stan trybów

Stan trybu pracy i blokad hook `UserPromptSubmit` pokazuje właścicielowi (samo `/tryb` nie trafia do modelu). Jeśli mimo to czytasz tę instrukcję, przepisz właścicielowi tabelę stanu z kontekstu dodanego przez hook — bez komentarza.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
