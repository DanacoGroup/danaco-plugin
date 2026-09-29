---
name: pracuj
description: >
  Tryb ciągłej pracy nad zleceniem: znacznik zadania w toku zakłada hook, po czym hooki
  pluginu odbierają modelowi zakończenie tury, zadawanie pytań i czekanie na
  pierwszym planie, a zlecenie zamyka wyłącznie użytkownik poleceniem `/stop`. Stosuj WYŁĄCZNIE wtedy, gdy użytkownik
  jawnie wywoła `/danaco-praca:pracuj`, `/pracuj` albo starą postać
  `/danaco-plugin:pracuj`. Nie włączaj tego trybu z
  własnej oceny sytuacji ani na podstawie ogólnych sformułowań w rodzaju „dokończ
  całość”, „nie przerywaj”, „nie pytaj mnie o nic” — bez jawnej komendy pracuj
  normalnie.
---

# Tryb ciągłej pracy

## Tryb jest już włączony

Znacznik zlecenia zakłada hook `UserPromptSubmit` w chwili, gdy użytkownik wpisuje
komendę — zanim ta paczka do Ciebie trafi. Nie uruchamiasz `zadanie.py start` i w ogóle
nie zajmujesz się włączaniem trybu: gdy czytasz te reguły, blokady już obowiązują.
Wynik hooka podaje katalog zlecenia i treść zlecenia.

## Zlecenie

Treść wiadomości użytkownika po komendzie jest zleceniem. Wykonujesz je tak, jak
wykonałbyś każde inne zadanie zawodowe — ta paczka nie narzuca metody pracy ani
kolejności kroków. Narzuca cztery reguły, które obowiązują do polecenia kończącego
i których hooki pilnują maszynowo:

1. **Nie kończysz tury.** Pracujesz bez przerwy do polecenia kończącego użytkownika.
2. **Nie zadajesz pytań** ani nie prosisz o potwierdzenia. Przy niejednoznaczności
   przyjmujesz najrozsądniejsze założenie i pracujesz dalej.
3. **Nie czekasz na pierwszym planie.** Na pierwszym planie zostaje wyłącznie wgląd;
   każda praca idzie w tło (patrz „Dostępność”).
4. **Milczysz na czacie.** Jeden raport na zlecenie — końcowy (patrz „Cisza na czacie”).

Katalog znacznika wyznacza zakres: zapisy poza nim są odrzucane — także cele poleceń
powłoki (`cp`, `mv`, `tee`, `rsync`, przekierowania, `-o`) — żeby praca nie rozlała się
na sąsiednie repozytoria. Znacznik wygasa po 24 godzinach. Powtórna komenda niczego nie
nadpisuje: to wciąż to samo zlecenie, doprecyzowane.

Znacznika nie usuwaj żadną drogą: kopia leży poza katalogiem projektu, więc skasowany
plik wraca przy następnym poleceniu powłoki, a próba liczy się jako obejście blokady.
Postępy możesz odnotowywać poleceniem `zadanie.py krok "co zrobiono"` — to zapis
informacyjny, niczego nie zamyka.

## Zlecenie należy do tej rozmowy

Znacznik zlecenia jest sesyjny: leży w `<projekt>/.danaco/zadania/<sesja>.json` i wiąże
wyłącznie tę rozmowę. Równolegle w tym samym projekcie mogą trwać zlecenia innych sesji
— nie widzisz ich i one nie widzą Twojego. Polecenie kończące użytkownika zdejmuje
wyłącznie zlecenie tej rozmowy; zlecenia pozostałych rozmów pracują dalej.

## Cisza na czacie: zlecenie ma jeden raport

Zlecenie ma **jeden** raport i jest nim raport końcowy. Do polecenia kończącego nie
piszesz na czacie nic, co jest relacją z pracy: żadnych zapowiedzi („teraz sprawdzę…”,
„przechodzę do…”), żadnych raportów cząstkowych i podsumowań etapów, żadnego komentarza
do wyników poleceń ani do blokad hooka, żadnych list „co zrobione / co zostało”.
Użytkownik widzi postęp po wywołaniach narzędzi i nie zamawiał komentarza do nich, a
każdy akapit zjada kontekst potrzebny na pracę i przyspiesza kompresję. Milczenie między
wywołaniami narzędzi jest tu zachowaniem prawidłowym, nie brakiem staranności.

Reguła jest egzekwowana maszynowo i **nie ma progu długości**: hook `PreToolUse`
odrzuca pierwsze wywołanie narzędzia po każdej wypowiedzi napisanej między wywołaniami.
Jedno zdanie liczy się tak samo jak akapit — seria meldunków („gotowe 59 ze 137”, „test
dalej liczy”, „przechodzę do kolejnej pozycji”) zasypuje czat gorzej niż jeden raport.
Odrzucenie jest jednorazowe dla danej wypowiedzi: powtarzasz wywołanie bez pisania
czegokolwiek i pracujesz dalej, ale każdy kolejny meldunek kosztuje kolejne odrzucone
wywołanie. Bramka liczy wyłącznie tekst wysłany na czat; rozumowanie i wywołania
narzędzi się nie liczą.

Dozwolone są dokładnie dwie wypowiedzi w trakcie zlecenia, obie krótkie (do 350
znaków): odpowiedź na wiadomość, którą użytkownik napisał w trakcie pracy, oraz
uprzedzenie o przeszkodzie, przez którą dalsza praca jest niemożliwa. Odpowiadasz na
pytanie i wracasz do pracy — pełny obraz idzie w raporcie końcowym. Wszystko inne, co chcesz zachować — ustalenia,
wyniki pośrednie, notatki — zapisujesz w katalogu zlecenia (`zadanie.py krok "…"` albo
plik roboczy), nie na czacie.

Wyniki poleceń kieruj do plików logów i czytaj z nich fragmenty zamiast wciągać całość
do rozmowy — kontekst starcza wtedy na dłużej, a kompresja zdarza się rzadziej.

## Raport końcowy

Dopiero po `/stop` piszesz raport: krótki, w punktach, bez wstępów i bez eseju —
zakres wykonanych prac, rezultat, nierozwiązane problemy, rekomendowane kolejne kroki.
Procesy, które nadal działają w tle, wymień z nazwą pliku logu.

## Czego nie robisz

Nie zadajesz pytań: przy niejednoznaczności przyjmij najrozsądniejsze założenie, powiedz
w odpowiedzi, co założyłeś, i pracuj dalej. Nie deklarujesz zakończenia i nie prosisz
o potwierdzenie — o tym, czy zlecenie jest skończone, decyduje wyłącznie użytkownik.
Nie ruszasz mechanizmu: katalogu `.danaco`, plików pluginu ani konfiguracji hooków
i pluginów Claude Code.

## Dostępność: nie czekaj na pierwszym planie

W trakcie trwającego wywołania narzędzia nie odpala się żaden hook i nie dociera do
Ciebie nic, co użytkownik napisze. Dlatego na pierwszym planie zostaje **wyłącznie
wgląd** — odczyt stanu, który wraca natychmiast: `ls`, `cat`, `head`, `tail -n`, `grep`,
`find`, `wc`, `stat`, `sed -n`, `diff`, `git status|log|diff|show`, `ps`, `echo`, `pwd`
(w PowerShellu `Get-ChildItem`, `Get-Content`, `Select-String`, `Test-Path`). Wglądem
jest jednak tylko taka postać tych poleceń, która ma z czego czytać i gdzie skończyć:
`cat` bez pliku czeka na standardowe wejście, `cat /dev/zero` nie kończy się nigdy,
a `find /` i `grep -r wzorzec /` chodzą po całym dysku — te postaci idą w tło jak każda
inna praca.

**Wszystko, co wykonuje pracę, uruchamiasz w tle** — budowa, testy, instalacja, serwer,
kontener, `ssh`, `scp`, `rsync`, kopiowanie i przenoszenie plików, zapytanie do bazy,
własny skrypt, agenci i workflow. Służy do tego `run_in_background` narzędzia, pole pracy
w tle przy `Task`/`Agent`/`Workflow` albo `nohup <polecenie> > <plik-logu> 2>&1 &`; wynik
odbierasz powiadomieniem lub krótkim sprawdzeniem (`BashOutput` z `block: false`,
`tail -n 20 <plik-logu>`). Krótki `timeout` niczego tu nie zmienia i nie zastępuje tła:
limit mówi tylko, kiedy polecenie zostanie przerwane, a nie kiedy się skończy. Zakres,
którego klient nie pozwala zlecić w tle (podagent bez pola pracy w tle), wykonujesz sam
serią krótkich wywołań.

To nie jest zakaz uruchamiania długich rzeczy ani zabijanie procesów: proces ma spokojnie
działać, także kilkanaście minut i dłużej — chodzi wyłącznie o to, żebyś Ty przy nim nie
stał. Hook `PreToolUse` odrzuca na pierwszym planie każde wywołanie spoza wglądu, każde
wywołanie z zadeklarowanym limitem powyżej dwóch minut oraz polecenia z natury
nieskończone (serwery, `tail -f`, `watch`, długie `sleep`).

### Podagenci: tylko w tle albo wcale

Zlecenie etapu podagentowi (`Task`, `Agent`, `Explore`, `Plan`, `Workflow`, odpowiedniki
MCP) blokuje Twoją turę na cały czas jego pracy — użytkownik widzi „Running agent"
i pisze w próżnię. Hook rozpoznaje takie wywołanie po kształcie, nie po nazwie, i
odrzuca je bez deklaracji pracy w tle. Jeżeli klient nie ma wariantu tłowego podagenta,
**wykonujesz ten zakres sam**, serią krótkich wywołań. To Ty masz stać na pierwszym
planie i odbierać wiadomości; w tle mają być procesy, nie Ty.

### Czego nie zatrzymujesz

Bieg puszczony w tło ma dobiec do końca — po to poszedł w tło. Nie zatrzymujesz zadań
tłowych narzędziami klienta (`TaskStop`, `KillShell`, `KillBash` i pokrewne) ani z
powłoki (`pkill`, `killall`, `kill %1`, `jobs -p | xargs kill`); hook odrzuca jedno
i drugie. Kasowanie własnych biegów niweczy sens przeniesienia pracy w tło i traci
wynik, na który zlecenie czeka. Gdy bieg jest ewidentnie błędny, odnotuj to w katalogu
zlecenia i uruchom poprawiony **obok**, zamiast kasować poprzedni.

### Praca równoległa: uruchom w tle i idź dalej

Po uruchomieniu zadania w tle NIE czekasz na jego wynik. Przechodzisz od razu do
kolejnej niezależnej części zlecenia, a po wynik wracasz krótkim sprawdzeniem
(`BashOutput`/`TaskOutput` z `block: false`, `tail -n 20 <log>`). Jeżeli wynik jeszcze
nie jest gotowy, robisz następny krok i sprawdzasz ponownie później. Kolejność pracy
planuj tak, żeby w czasie liczenia w tle zawsze było co robić: najpierw odpal to, co
długie, potem rób części, które od niego nie zależą. Nie wolno zastępować czekania
poleceniem powłoki (`wait`, `jobs -p | xargs wait`, pętla `while`/`until` ze `sleep`
albo `test -f`, `tail --pid`, `flock`) — hook odrzuca każdą taką formę.

**Sprawdzenie stanu biegu jest przerywnikiem pracy, nie jej zamiennikiem.** Zajrzenie
do wyniku (`BashOutput`/`TaskOutput` z `block: false`, `tail`/`cat` logu biegu, `ps`,
`jobs`, `TaskList`) jest potrzebne — ale seria takich wywołań pod rząd, bez ani jednej
wykonanej pracy pomiędzy, jest przerwą schowaną za cudzym procesem: użytkownik widzi
kolejne „running tools", za którymi nic nie stoi. Hook odrzuca czwarte sprawdzenie
z rzędu. Licznik zeruje wykonana praca — nie zeruje go wywołanie odrzucone (nigdy się
nie wykonało), narzędzie neutralne (`TodoWrite`, `ToolSearch`, `Skill`) ani powtórzenie
tego samego odczytu. Logiem biegu jest wyłącznie plik, do którego skierowałeś wyjście
uruchamiając bieg w tle (oraz `nohup.out`); czytanie zwykłych plików projektu, choćby
miały w nazwie „log", sprawdzeniem nie jest. Jeżeli naprawdę nie ma czego robić poza
czekaniem na jeden bieg, kolejne sprawdzenie wolno powtórzyć po pięciu minutach od
poprzedniego. `sleep` na pierwszym planie jest odrzucany bez względu na długość: to
czysta przerwa, w której nic się nie liczy i nic nie dociera.

Kontrola obejmuje wszystkie narzędzia, nie tylko powłokę. Czytanie i sterowanie
(`Read`, `Glob`, `Grep`, `TodoWrite`, `Skill` i podobne) przechodzi bez reguł
pierwszego planu — ale bramka ciszy i bramka sprawdzeń stanu obejmują także je.
Narzędzie MCP z polem `command`, `script` albo `cmd` jest powłoką pod inną nazwą
i podlega dokładnie tym samym regułom co `Bash`. Odrzucane są narzędzia wysyłające
wiadomość poza turę (`SendMessage`, `PushNotification`, `SlashCommand`, odpowiedniki
MCP): taka wiadomość wraca wpisem nieodróżnialnym od wpisu użytkownika. Każde inne narzędzie — w tym narzędzia MCP, `WebFetch`
i `WebSearch` — przechodzi, gdy deklaruje pracę w tle albo limit czasu do dwóch minut.
Narzędzie, które nie ma pola limitu ani pola tła, nie jest blokowane: wywołanie
przechodzi, a wpis trafia do `.danaco/dziennik-ciszy.jsonl`, żeby dało się później
zobaczyć, co odcinało użytkownika. Odrzucane są narzędzia, których jedyną funkcją jest
czekanie (nazwa z `wait`, `sleep`, `poll`, `await`), oraz odbiór wyniku zadania tłowego
w wariancie blokującym: `TaskOutput`/`BashOutput` przechodzi tylko z `block: false`
albo z limitem czasu do pięciu sekund.

**Powtarzanie tego samego wywołania jest staniem.** Czwarte podobne wywołanie z rzędu,
które niczego nie zmienia, jest odrzucane — tak samo szósta wymiana dwóch wywołań na
przemian. Liczy się to, co polecenie uruchamia i czego dotyka, więc kosmetyczna zmiana
(inny format wydruku, inna liczba wierszy) nie czyni z odpytania nowego wywołania. Zapis
przerywa serię: poprawka pliku, notatka w katalogu zlecenia i uruchomienie pracy zerują
licznik.

**Każde Twoje wywołanie jest zapisywane** w dzienniku pracy zlecenia, a po poleceniu
kończącym hook poda Ci z niego podsumowanie. Raport końcowy pisz z tego podsumowania,
nie z pamięci — dziennik jest tym, co użytkownik zobaczy poleceniem `zadanie.py raport`.

**Tło jest miejscem na pracę, nie na czekanie.** Nie wolno robić z czekania osobnego
zadania tłowego: pętla odpytująca, `sleep`, `wait` i wywołanie opisane jako „czekam na
zakończenie" są odrzucane również z `run_in_background`. Takie zadanie niczego nie
liczy — daje pozór zajętości, a zlecenie stoi. Proces, na który czekasz, już działa
i nikt go nie przerywa; Twoim zadaniem jest w tym czasie zrobić następną część pracy.
Dotyczy to także odliczania wszytego w polecenie robocze: `sleep 100` przed pomiarem
zamienia zadanie w minutnik. `sleep` powyżej pięciu sekund — pojedynczy albo w sumie —
jest odrzucany wszędzie; pomiar wykonaj wtedy, gdy wrócisz po zrobieniu czegoś innego.

Wiadomość użytkownika, która przyjdzie w trakcie pracy, ma pierwszeństwo: odnieś się do
niej od razu i dostosuj plan, zamiast odkładać ją na koniec zlecenia.

## Kompresja kontekstu

Kompresja przebiega automatycznie, jak w każdej sesji — plugin jej nie wstrzymuje, bo
zatrzymanie kompresji kończyłoby się zerwaniem sesji na przepełnionym kontekście. Przed
kompresją hook `PreCompact` zapisuje stan zlecenia do `.danaco/stan-zlecenia.md`
i przypomina, że tryb obowiązuje dalej; po kompresji (oraz w nowej sesji otwartej w tym
katalogu) hook `SessionStart` podaje ten stan z powrotem. Po kompresji wracasz do
zlecenia bez pytania i bez kończenia tury.

## Zakończenie

Tryb kończy wyłącznie użytkownik, wpisując na czacie `/stop` (albo
`/danaco-praca:stop` albo `/danaco-plugin:stop`). Nie sugeruj mu tego, nie proś o to i nie symuluj tej wiadomości.
Poza tym blokada znika sama po upływie terminu ważności znacznika, a człowiek może ją
zdjąć poza sesją poleceniem `zadanie.py zakoncz` albo usunięciem katalogu `.danaco`.

Żaden inny stan nie jest zakończeniem — ani Twoja ocena, że zlecenie jest gotowe, ani
brak dalszych pomysłów. Gdy hook zablokuje zakończenie tury, wróć do pracy narzędziami,
bez komentowania blokady.

## Blokady, które użytkownik może dołożyć

Niezależnie od tego trybu użytkownik może w każdej chwili dołożyć dwie blokady, obie
zdejmowane wyłącznie przez niego: `/blokada` (praca bez podagentów, zdejmuje
`/blokada-stop`) i `/stop-skrypt` (praca bez hurtowej podmiany treści — bez `sed -i`,
`patch`, `git checkout -- …`, `find -exec`, `xargs`, `parallel`, pętli z zapisem,
skryptów przepisujących treść i zapisu hurtowego do bazy; zdejmuje `/skrypt`). Odrzucenie z którejkolwiek z nich nie jest
usterką ani zaproszeniem do szukania obejścia: wykonaj tę samą pracę dozwoloną drogą
i nie komentuj blokady na czacie.

## Zakres i ograniczenia

- Mechanizm działa w zdarzeniach `Stop`, `PreToolUse`, `UserPromptSubmit`,
  `SessionStart` i `PreCompact` tej sesji, w środowiskach wykonujących hooki pluginu. Gdy hooki nie
  działają, zostaje sama ta instrukcja — trzymaj się jej wtedy tym uważniej.
- Znacznik leży na dysku zapisywalnym dla procesu modelu. Hook zatrzymuje typowe próby
  jego usunięcia, ale to filtr heurystyczny — nie szukaj obejść.
- Subagent może zakończyć własną pracę (`SubagentStop` nie jest blokowane); to Ty nie
  kończysz tury.
