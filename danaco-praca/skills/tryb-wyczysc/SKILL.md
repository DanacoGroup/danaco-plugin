---
name: tryb-wyczysc
description: "Zdejmuje naraz tryb pracy ciągłej i wszystkie blokady tej sesji (powrót do stanu domyślnego). Wyłącznie dla właściciela."
disable-model-invocation: true
---

# Reset trybów

Właściciel zdjął naraz tryb pracy ciągłej i wszystkie blokady tej sesji — sesja wraca do stanu domyślnego. Hook zapisał to w dzienniku. Pracuj dalej zgodnie z nowym (pustym) stanem.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
