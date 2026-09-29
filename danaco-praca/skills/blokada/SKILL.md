---
name: blokada
description: >
  Blokada podagentów: po poleceniu `/blokada` model pracuje wyłącznie samodzielnie,
  bez zlecania czegokolwiek podagentom ani workflow — także w tle. Blokada trwa
  najwyżej 12 godzin albo do polecenia `/blokada-stop`. Stosuj, gdy użytkownik wywoła
  `/blokada`, `/danaco-praca:blokada` albo starą postać `/danaco-plugin:blokada`. Model nie włącza ani nie zdejmuje jej sam.
---

# Blokada podagentów

Blokadę włącza i zdejmuje wyłącznie użytkownik, wpisując `/blokada` albo
`/blokada-stop` na początku wiadomości albo w osobnej linii — wzmianka w prozie
(„opisz polecenie /blokada”) niczego nie uruchamia. Hook `UserPromptSubmit` zapisuje wtedy plik
`.danaco/blokada-subagentow.json` (albo go kasuje) — model nie ma na to wpływu,
bo to zdarzenie powstaje tylko z wpisu człowieka.

Dopóki blokada trwa, hook `PreToolUse` odrzuca `Task`, `Agent` i `Workflow`, również
uruchamiane w tle. Odrzucenie nie jest usterką ani zaproszeniem do szukania obejścia:
pracę, którą chciałeś zlecić podagentowi, wykonaj sam — czytając pliki, uruchamiając
polecenia i weryfikując wyniki krok po kroku. Nie proponuj użytkownikowi zniesienia
blokady i nie pytaj, czy może ją zdjąć.

Blokada jest niezależna od trybu ciągłej pracy: działa tak samo w zwykłej sesji, wiąże
się z sesją, w której ją włączono (polecenie `/blokada-stop` z innej rozmowy jej nie
zdejmuje), i wygasa sama po dwunastu godzinach. Zakończenie
zlecenia (`/stop`) jej nie zdejmuje.

Procesy w tle, zwykłe polecenia powłoki i wszystkie pozostałe narzędzia działają bez
zmian — blokada dotyczy wyłącznie zlecania pracy podagentom.
