---
name: praca
description: "Praca ciągła: agent nie kończy tury ani nie czeka, dopóki właściciel nie wyda /koniec-pracy. Przełącza wyłącznie właściciel."
disable-model-invocation: true
argument-hint: "[zlecenie]"
---

# Praca ciągła

Właściciel włączył tryb pracy ciągłej. Zlecenie: $ARGUMENTS

Zasady, których pilnują hooki (do polecenia `/koniec-pracy`):

1. **Nie kończysz tury z własnej woli.** Hook `Stop` odrzuca próbę zakończenia i przypomina
   zlecenie. Gdy uznasz część pracy za skończoną, weź następną: sprawdź wyniki procesów w tle,
   zweryfikuj i przetestuj zrobione części, popraw błędy, uzupełnij dokumentację.
2. **Nie czekasz i nie śpisz.** Odrzucane są `sleep`, `timeout … sleep`, `wait`, `tail -f`
   i pętle oczekiwania na pierwszym planie, `ScheduleWakeup`, `CronCreate` oraz blokujący
   odbiór wyniku (`TaskOutput` bez `block: false`).
3. **Pracujesz aktywnie cały czas.** Wolno uruchamiać procesy i agentów w tle oraz stawiać
   monitoring (także narzędziem `Monitor`), ale sam w tym czasie robisz dalej kolejne
   części zadania. Podagenci, których powołasz, oddają wynik normalnie.
4. **Bez innych ograniczeń.** Narzędzia i miejsca zapisu nie są ograniczone. Obowiązują tylko
   zasady serwera (kosz zamiast kasowania, straż pakietów i dysku, sekrety) oraz blokady,
   które właściciel dołożył osobno.

Tryb **wyłącza** wyłącznie właściciel poleceniem `/koniec-pracy`. Nie proś o nie i nie pytaj,
czy kończyć. Co pewien czas hook `Stop` sam oddaje turę, żeby właściciel mógł wpisać wiadomość
(jego wiadomość zostaje odczytana od razu) — to **nie koniec trybu**: `/praca` pozostaje włączone,
a Ty masz pracować dalej. Gdy właściciel przyśle wiadomość, najpierw ją obsłuż, a potem wróć do
zlecenia; samo „kontynuuj” też wznawia pracę. Nie traktuj oddania tury jako pozwolenia na
zakończenie pracy.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
