---
name: sesja-przejmij
description: "Przejmuje wskazaną sesję: przygotowuje przejęcie (danaco-przejmij-sesje) i podaje gotowe polecenie wznowienia. Argument: identyfikator sesji. Wyłącznie dla właściciela."
disable-model-invocation: true
argument-hint: "[id-sesji]"
---

# Przejęcie sesji

Hook uruchamia `danaco-przejmij-sesje <id>` dla identyfikatora podanego przez właściciela, a następnie pokazuje mu gotowe polecenie `claude --resume` do wklejenia w terminalu (tej sesji Claude nie może wznowić sam, bez terminala). Polecenie nie trafia do modelu i nie wymaga od Ciebie działania.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
