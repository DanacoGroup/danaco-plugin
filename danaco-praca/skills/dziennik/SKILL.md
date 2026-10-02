---
name: dziennik
description: "Pokazuje ostatnie wpisy dziennika tej sesji: polecenia właściciela, odmowy hooka, zadziałania bezpiecznika. Wyłącznie dla właściciela."
disable-model-invocation: true
---

# Dziennik trybów

Hook wypisuje właścicielowi ostatnie wpisy dziennika tej sesji (zmiany trybów, odmowy, bezpiecznik pętli). Polecenie nie trafia do modelu i nie wymaga od Ciebie żadnego działania.


To polecenie wydaje wyłącznie właściciel; model go nie wywołuje (ma `disable-model-invocation: true`). Wynik hook pokazuje właścicielowi — nie komentujesz go i nie podejmujesz na jego podstawie działań z własnej inicjatywy.
