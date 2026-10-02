---
name: sesja-id
description: "Wypisuje identyfikator bieżącej sesji — do skopiowania, np. aby przejąć ją z innego konta. Wyłącznie dla właściciela."
disable-model-invocation: true
---

# Identyfikator sesji

Hook wypisuje właścicielowi identyfikator bieżącej sesji (z pola `session_id` zdarzenia). Służy do przejęcia sesji na innym koncie poleceniem `/przejmij <id>`. Polecenie nie trafia do modelu.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
