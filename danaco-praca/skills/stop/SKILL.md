---
name: stop
description: >
  Kończy tryb ciągłej pracy Danaco: zdejmuje znacznik zadania w toku i przywraca
  normalne zachowanie sesji. Stosuj, gdy użytkownik wywoła `/stop`,
  `/danaco-praca:stop` albo starą postać `/danaco-plugin:stop`. Samo zdjęcie blokady wykonuje hook `UserPromptSubmit`
  w chwili, gdy użytkownik wpisze tę komendę — model nie zdejmuje jej sam i nie
  wywołuje tej paczki z własnej inicjatywy.
---

# Zakończenie trybu ciągłej pracy

Wpisanie `/stop` przez użytkownika jest zdarzeniem `UserPromptSubmit`, a hook
`hooks/straznik.sh prompt` usuwa wtedy znacznik `.danaco/zadanie-w-toku.json` oraz jego
kopię poza katalogiem projektu. Dzieje się to zanim ta paczka trafi do Ciebie, więc
blokady już nie ma i turę wolno zakończyć. Komenda liczy się wyłącznie na początku
wiadomości albo w osobnej linii — jej wystąpienie w cytacie, w ścieżce czy we wklejonym
logu blokady nie zdejmuje.

Twoje jedyne zadanie po tej komendzie: krótki raport w punktach — zakres wykonanych
prac, rezultat, nierozwiązane problemy, rekomendowane kolejne kroki — i zakończenie
tury. Bez wstępu, bez eseju, bez opisywania własnego procesu pracy. Nie zakładaj nowego znacznika, nie
kontynuuj poprzedniego zlecenia i nie pytaj, czy na pewno kończyć.

Procesy uruchomione w tle działają dalej — `/stop` kończy tryb pracy, nie zabija
niczego. Jeśli któryś proces nadal pracuje, wymień go w raporcie wraz z plikiem
logu, żeby użytkownik wiedział, gdzie sprawdzić wynik.

Gdyby po tej komendzie hook `Stop` mimo wszystko zgłosił blokadę (na przykład brak
interpretera Pythona w środowisku hooków), powiedz o tym użytkownikowi i wskaż mu
awaryjne wyjście: usunięcie katalogu `.danaco` w katalogu projektu albo polecenie
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zadanie.py" zakoncz` uruchomione z osobnego
terminala.
