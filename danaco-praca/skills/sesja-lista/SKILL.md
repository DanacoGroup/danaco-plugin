---
name: sesja-lista
description: "Wypisuje listę ostatnich sesji obu kont właściciela, gotowych do przejęcia (danaco-przejmij-sesje --lista). Wyłącznie dla właściciela."
disable-model-invocation: true
---

# Lista sesji

Hook uruchamia `danaco-przejmij-sesje --lista` i pokazuje właścicielowi spis ostatnich sesji obu kont (id, konto, stan, katalog). Z niego właściciel bierze identyfikator do `/sesja-przejmij <id>`. Polecenie nie trafia do modelu.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
