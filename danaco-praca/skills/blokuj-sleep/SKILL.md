---
name: blokuj-sleep
description: "Blokada „uśpienie”: włącza blokadę (zwalnia /odblokuj-sleep). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: uśpienie

Właściciel włączył blokadę: odrzucane są `sleep`, `timeout … sleep`, `wait`, `tail -f`, `watch`, pętle oczekiwania i odpytywania, uśpienie w kodzie, `ScheduleWakeup`, `Monitor`, `CronCreate` i blokujący odbiór wyniku — także w tle (poza pętlą monitoringu zapisującą do dziennika `>>`). Ściślej niż sam tryb `/praca`, który dopuszcza czekanie w tle.

Blokadę zwalnia wyłącznie właściciel poleceniem `/odblokuj-sleep`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
