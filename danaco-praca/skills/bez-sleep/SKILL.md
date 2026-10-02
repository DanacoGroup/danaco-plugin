---
name: bez-sleep
description: "Blokada uśpienia: włącza blokadę (zwalnia /z-sleep). Polecenie wyłącznie dla właściciela."
disable-model-invocation: true
---

# Blokada uśpienia

Właściciel włączył blokadę: odrzucane są `sleep`, `timeout … sleep`, `wait`, `tail -f`, `watch`, pętle oczekiwania i odpytywania, uśpienie w kodzie podanym wprost, `ScheduleWakeup`, `Monitor`, `CronCreate` i blokujący odbiór wyniku — także poza trybem pracy ciągłej. Monitoring w tle zapisujący do dziennika jest dozwolony.

Blokadę zwalnia wyłącznie właściciel poleceniem `/z-sleep`.

Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
