# Biblioteka wzorców interfejsów agentowych

Karta rozwija procedurę z `references/agentic-ux/agentic-ux.md`. Każdy wzorzec opisano w układzie:
problem → rozwiązanie → anatomia (elementy interfejsu) → stany → błędy
projektowe. Wzorce projektuj jako komplet — wzorzec wyrwany z systemu (np.
pasek autonomii bez raportu z pracy autonomicznej) daje obietnicę kontroli bez
pokrycia. Nazwy elementów traktuj jako słownik projektu i stosuj konsekwentnie
w opracowaniu UX i makietach.

## 1. Panel pamięci („co system o mnie wie”)

**Problem.** Użytkownik nie wie, co system o nim zapamiętał, więc nie ufa ani
personalizacji („skąd on to wie?”), ani jej brakowi („dlaczego on tego nie
wie?”). Relacja bez przejrzystości pamięci nie przechodzi do stadium autonomii.

**Rozwiązanie.** Zaprojektuj stały, łatwo osiągalny panel z całą pamięcią
o użytkowniku jako edytowalną listą faktów. Każdy fakt jest osobnym,
adresowalnym obiektem: do wglądu, poprawienia i wymazania pojedynczo, bez
kasowania całej pamięci. Panel jest miejscem sprawowania władzy nad relacją,
nie stroną informacyjną.

**Anatomia.**
- Lista faktów pogrupowana według taksonomii pamięci (karta
  `references/agentic-ux/pamiec-i-prywatnosc.md`).
- Oznaczenie pochodzenia rozróżnialne wizualnie, nie tylko tekstowo: **fakt
  podany** (użytkownik powiedział wprost) i **fakt wywnioskowany** (system
  wydedukował z zachowania). Rozróżnienie jest twardym wymogiem — fakt
  wywnioskowany ma niższy status dowodowy i musi to być widoczne od razu,
  np. przez odmienny znacznik i przycisk „skąd to wiesz?”.
- Działania na fakcie: edytuj, wymaż, oznacz jako nieaktualny; dla
  wywnioskowanych także: potwierdź (awans do rangi podanego).
- Wejście globalne: wymaż wszystko i zacznij od nowa, z opisem skutków.

**Stany.** *Pusty* — panel mówi wprost, że system nic jeszcze nie wie, i
wyjaśnia zasady zapisu. *Fakt świeżo dodany* — wyróżnienie wpisów od ostatniej
wizyty. *Fakt przeterminowany* — system proponuje potwierdzenie lub wymazanie.
*Po wymazaniu* — potwierdzenie obejmuje także pochodne (wnioski wyprowadzone
z wymazanego faktu), nie tylko sam wpis.

**Błędy projektowe.** Panel ukryty głęboko w ustawieniach; pamięć jako
nieedytowalny opis; brak rozróżnienia podane/wywnioskowane; wymazanie
działające na wpis, ale nie na wnioski z niego; surowe rekordy zamiast zdań
zrozumiałych dla człowieka.

## 2. Propozycja z uzasadnieniem

**Problem.** Rekomendacja bez podstawy zmusza do ślepego zaufania albo ślepego
odrzucenia — pierwsze pęka przy pierwszym błędzie, drugie blokuje wzrost
autonomii.

**Rozwiązanie.** Każdą propozycję wydawaj w kompletnej jednostce: rekomendacja
+ podstawa + pewność + działania. Odrzucenie projektuj jako sygnał uczący, nie
porażkę interfejsu — system pyta (opcjonalnie, nie natarczywie) o powód
i zapisuje korektę.

**Anatomia.**
- Treść propozycji — jedno działanie lub jedna decyzja, nie pakiet.
- Podstawa — wskazanie konkretnych faktów pamięci lub danych („proponuję X, bo
  w poprzednich trzech raportach wybrano Y”).
- Pewność — skala co najwyżej trójstopniowa, wyrażona operacyjnie („na
  podstawie 12 podobnych przypadków”), nie procentem — procent sugeruje
  precyzję, której system nie ma.
- Działania: **przyjmij** (wykonaj), **popraw** (edytuj przed wykonaniem —
  najcenniejsze źródło sygnału uczącego), **odrzuć** (powód opcjonalny).
- Kanał zwrotny: po korekcie system komunikuje jednym zdaniem, czego się
  nauczył — i wpis pojawia się w panelu pamięci.

**Stany.** *Wysoka pewność* — przyjęcie jednym działaniem. *Niska pewność* —
system otwiera od pytania; forma „nie wiem, czy…” jest projektowo pożądana.
*Po poprawce* — różnica widoczna, korekta potwierdzona. *Po odrzuceniu* — bez
ponawiania w tej samej sesji; ponowienie wymaga zmiany podstawy. *Konflikt
z pamięcią* — propozycja sprzeczna z zapamiętaną preferencją jawnie nazywa
konflikt i uzasadnia odstępstwo.

**Błędy projektowe.** Uzasadnienie generyczne („na podstawie Twojej
aktywności”); pewność jako ozdobny procent; brak trybu „popraw” (traci się
najlepszy sygnał uczący); ponawianie odrzuconej propozycji bez nowej podstawy;
wymuszanie powodu odrzucenia jako warunku zamknięcia.

## 3. Plan współtworzony

**Problem.** Plan przedstawiony w dialogu znika z przewinięciem rozmowy; plan
wykonany bez akceptacji odbiera sprawczość; plan zamrożony po akceptacji nie
wytrzymuje zderzenia z rzeczywistością.

**Rozwiązanie.** Projektuj plan jako trwały artefakt: edytowalną listę kroków
ze statusami, istniejącą obok rozmowy, nie w jej strumieniu — edytowalną przed
startem i w trakcie, z obowiązkowym punktem zatrzymania przed każdą operacją
nieodwracalną.

**Anatomia.**
- Kroki jako obiekty: treść, status (oczekuje / w toku / wykonany / pominięty /
  zablokowany), przewidywany skutek, oznaczenie odwracalności.
- Edycja: dodanie, usunięcie, zmiana kolejności i zakresu — w trakcie działa
  od najbliższego niewykonanego kroku.
- Punkt zatrzymania: krok nieodwracalny (wysyłka, płatność, usunięcie danych,
  publikacja) wymaga osobnego potwierdzenia w momencie dojścia do niego —
  akceptacja całego planu nie konsumuje tej zgody.
- Założenia planu wypisane jawnie, każde do zakwestionowania.
- Widok postępu: co wykonano, co się zmieniło względem wersji zaakceptowanej.

**Stany.** *Szkic* — nic się nie wykonuje. *Zaakceptowany* — ruszają kroki
odwracalne. *W wykonaniu* — statusy na żywo, edycja dalszych kroków otwarta.
*Zatrzymany na punkcie nieodwracalnym* — system czeka; odróżnij od awarii.
*Rozjazd* — rzeczywistość unieważniła założenie; system zatrzymuje się
i proponuje rewizję zamiast brnąć.

**Błędy projektowe.** Plan tylko w treści rozmowy; akceptacja hurtowa
konsumująca zgody na kroki nieodwracalne; plan nieedytowalny po starcie;
statusy aktualizowane dopiero po zakończeniu całości; ukrywanie kroków
technicznych o widocznych skutkach.

## 4. Pasek autonomii

**Problem.** Użytkownik nie wie, co system zrobi sam, a o co zapyta — więc
albo nadzoruje wszystko (autonomia bez wartości), albo jest zaskakiwany
działaniami (zaufanie pęka). Poziom uprawnień istniejący tylko w konfiguracji
jest projektowo niewidzialny.

**Rozwiązanie.** Uczyń poziom autonomii widocznym elementem interfejsu, osobno
dla każdego obszaru działania (autonomia jest zawsze zakresowa, nigdy
globalna), wraz z historią jego zdobycia. Ręczna regulacja w dół jest dostępna
zawsze i działa natychmiast; podwyższenie — wyłącznie za jawną zgodą, nigdy
samoczynnie.

**Anatomia.**
- Wskaźnik stadium na obszar: przejrzystość / asysta nadzorowana / autonomia
  zarobiona (stadia z `references/agentic-ux/agentic-ux.md`), z opisem znaczenia w praktyce obszaru.
- Historia zdobycia: zdarzenia uzasadniające obecny poziom (wykonane
  działania, zgody, korekty) — zaufanie ma być audytowalne.
- Regulacja: wybór stadium w dół działający od razu; propozycja podwyższenia
  jako osobne, odrzucalne zaproszenie z uzasadnieniem.
- Zapowiedź konsekwencji: co konkretnie zmieni się po zmianie stadium.

**Stany.** *Stadium początkowe* — nowy obszar startuje od przejrzystości.
*Propozycja awansu* — brak reakcji oznacza brak zgody. *Degradacja po
błędzie* — obniżenie automatyczne z wyjaśnieniem (wzorzec 7); wskaźnik
pokazuje powód i ścieżkę powrotu. *Obniżenie ręczne* — bez dopytywania
„dlaczego” jako warunku; pytanie opcjonalne, po fakcie.

**Błędy projektowe.** Jedna globalna autonomia dla całego systemu; samoczynne
podwyższanie poziomu; historia zdobycia niedostępna; regulacja w dół schowana
lub opóźniona; opisy stadiów żargonem zamiast językiem skutków.

## 5. Przerwanie i przejęcie

**Problem.** Praca agenta, której nie można bezpiecznie przerwać, zmusza do
wyboru: czekać do końca albo zabić proces i stracić wszystko. Oba warianty
uczą, żeby nie delegować niczego długiego.

**Rozwiązanie.** Projektuj przerwanie jako operację pierwszej klasy:
zatrzymanie bez utraty stanu, podgląd pracy częściowej, przejęcie ręczne od
miejsca zatrzymania. Przerwanie nie jest anulowaniem — rozdziel te operacje.

**Anatomia.**
- Element zatrzymania widoczny przez cały czas pracy agenta; odrębne
  działania: **wstrzymaj** (stan zachowany, można wznowić), **przejmij**
  (użytkownik kontynuuje ręcznie od stanu bieżącego), **anuluj** (wycofanie
  z opisem, co da się cofnąć, a co już nie).
- Podgląd pracy częściowej w formie nadającej się do oceny (artefakty, nie
  logi).
- Punkt przejęcia: stan przekazywany do edycji ręcznej jest kompletny —
  użytkownik nie zaczyna od zera.
- Powrót delegacji: po interwencji użytkownik może oddać dalszą pracę
  systemowi wraz ze swoimi zmianami.

**Stany.** *W pracy* — postęp komunikowany etapami, nie samym paskiem
procentów. *Wstrzymany* — stan zamrożony; wznów / przejmij / anuluj.
*Przejęty* — system w roli obserwatora, nie nadpisuje zmian użytkownika.
*Wznowiony po przejęciu* — system jawnie uwzględnia ręczne zmiany.

**Błędy projektowe.** Jedno działanie „stop” o niejasnych skutkach; przerwanie
gubiące pracę częściową; podgląd w formie surowego logu; brak drogi powrotnej
do delegacji po przejęciu; blokowanie przerwania „bo krok się nie skończył”.

## 6. Raport z pracy autonomicznej

**Problem.** Agent działający pod nieobecność użytkownika tworzy dług
informacyjny: użytkownik albo nie wie, co się działo (zaufanie ślepe), albo
rekonstruuje przebieg z rozproszonych śladów (koszt nadzoru zjada zysk
z delegacji).

**Rozwiązanie.** Projektuj skrzynkę przeglądową: jedno miejsce, w którym praca
autonomiczna czeka na przegląd w stałym, trójdzielnym układzie — **co
zrobiłem / czego nie zrobiłem / co wymaga Twojej decyzji**. Pozycje decyzyjne
zawsze na górze.

**Anatomia.**
- Sekcja decyzji: sprawy zablokowane na użytkowniku, każda z działaniami
  (zatwierdź / popraw / odrzuć) i kontekstem wystarczającym do decyzji bez
  opuszczania skrzynki.
- Sekcja wykonanych: zwięzła lista z odnośnikami do artefaktów i oznaczeniem
  odwracalności; działania odwracalne mają widoczne „cofnij”.
- Sekcja niewykonanych: co planowano, czego zaniechano i dlaczego —
  zaniechanie z powodem buduje zaufanie mocniej niż sukces bez kontekstu.
- Podsumowanie kosztu: czas, zasoby, liczba operacji.

**Stany.** *Nic do przeglądu* — komunikat pusty jest wartościowy:
„działałem, wszystko w zakresie uprawnień, nic nie czeka”. *Decyzje zaległe*
— widoczność rośnie z wiekiem sprawy, zgodnie z budżetem przerwań
(wzorzec 9). *Przegląd częściowy* — stan zapamiętany, nic nie znika przez
przewinięcie. *Po odrzuceniu pozycji* — korekta staje się sygnałem uczącym.

**Błędy projektowe.** Raport jako chronologiczny log zdarzeń; ukrywanie
zaniechań; mieszanie spraw decyzyjnych z informacyjnymi w jednym strumieniu;
raport rozproszony po powiadomieniach zamiast jednej skrzynki; brak „cofnij”
przy działaniach odwracalnych.

## 7. Odbudowa po błędzie agenta

**Problem.** Błąd systemu autonomicznego niszczy zaufanie nieproporcjonalnie
do szkody, bo podważa samą zasadność delegacji; zaprzeczanie lub milczenie
zamienia incydent w koniec relacji.

**Rozwiązanie.** Projektuj sekwencję odbudowy jako stały scenariusz:
przyznanie błędu wprost → pokazanie skutków → propozycja naprawy →
automatyczna degradacja autonomii w dotkniętym obszarze z wyjaśnieniem.
Kolejność jest częścią wzorca: naprawa proponowana przed przyznaniem błędu
brzmi jak unik.

**Anatomia.**
- Komunikat przyznania: co system zrobił źle, nazwane wprost, bez strony
  biernej („usunąłem niewłaściwy plik”, nie „plik został usunięty omyłkowo”).
- Mapa skutków: co dotknięte, co odwracalne, co nie; skutki niepewne oznaczone
  jako niepewne.
- Propozycja naprawy: konkretne kroki, wykonywane w stadium asysty
  nadzorowanej niezależnie od dotychczasowego poziomu autonomii.
- Zapis degradacji: obszar błędu wraca do niższego stadium; pasek autonomii
  (wzorzec 4) pokazuje powód i warunki powrotu.
- Incydent pozostaje widoczny w historii zdobywania autonomii — nie znika po
  naprawie.

**Stany.** *Błąd wykryty przez system* — sekwencja rusza, zanim użytkownik
sam zauważy; wyprzedzenie jest miarą dojrzałości wzorca. *Błąd zgłoszony
przez użytkownika* — najpierw weryfikacja i przyznanie, potem ewentualne
wyjaśnienie. *Naprawa w toku / zakończona* — status widoczny jak w planie
współtworzonym. *Fałszywy alarm* — system pokazuje dowód braku błędu, nie
samo zapewnienie.

**Błędy projektowe.** Przeprosiny bez treści („przepraszamy za
niedogodności”); naprawa bez pokazania skutków; zachowanie pełnej autonomii po
błędzie w tym samym obszarze; degradacja bez wyjaśnienia (odbierana jako
awaria); usuwanie incydentu z historii po odbudowie.

## 8. Przekazanie kontekstu między sesjami

**Problem.** Sesja zaczynana od zera unieważnia relację: użytkownik powtarza
kontekst, system marnuje zdobytą wiedzę. Powitanie przeciążone podsumowaniami
jest równie złe — zamienia otwarcie w raport do przeczytania.

**Rozwiązanie.** Projektuj powitanie kontynuujące o dwóch częściach: **gdzie
skończyliśmy** (stan ostatniego wątku, jedno–dwa zdania) i **co się zmieniło
od tamtej pory** (zdarzenia istotne dla wspólnych spraw, zaszłe bez
użytkownika). Powitanie jest ofertą podjęcia wątku, nie przymusem — nowy
temat musi być równie łatwy do rozpoczęcia.

**Anatomia.**
- Nawiązanie: ostatni niedomknięty wątek ze statusem i jednym działaniem
  podjęcia („wróć do…”).
- Delta: zmiany od ostatniej sesji uporządkowane malejąco według wpływu na
  sprawy użytkownika, nie chronologicznie; rzeczy bez wpływu — pominięte.
- Wyjście awaryjne: czysta karta jednym działaniem, bez kasowania pamięci.
- Kalibracja do przerwy: po dniu — kontynuacja niemal bezszwowa; po miesiącach
  — więcej rekonstrukcji kontekstu i ostrożniejsze założenia o aktualności
  preferencji (świeżość faktów — karta `references/agentic-ux/pamiec-i-prywatnosc.md`).

**Stany.** *Krótka przerwa* — delta zwykle pusta; nie wymyślaj zmian, by
powitanie wyglądało na mądre. *Długa przerwa* — system zaznacza, które
założenia mogły się zdezaktualizować, i pyta zamiast zakładać. *Zmiana
urządzenia* — kontynuacja stanu relacji z poszanowaniem różnic kontekstu
(inne wejście, inna prywatność otoczenia). *Wątek domknięty pod nieobecność*
— nawiązanie zamienia się w odnośnik do raportu (wzorzec 6).

**Błędy projektowe.** Streszczanie całej historii zamiast ostatniego stanu;
delta chronologiczna zamiast ważonej wpływem; przymus starego wątku;
identyczne powitanie po godzinie i po pół roku; nawiązywanie do spraw
wymazanych z pamięci.

## 9. Granice proaktywności

**Problem.** System, który odzywa się sam, operuje na cudzej uwadze — zasobie
nieodnawialnym. Nietrafione odezwanie obniża wiarygodność wszystkich
następnych; system zbyt cichy nie realizuje wartości agentowości.

**Rozwiązanie.** Zaprojektuj jawny kontrakt proaktywności: reguły ciszy,
kanały przypisane do pilności i budżet przerwań (górny limit odezwań w oknie
czasu). Kontrakt jest widoczny i edytowalny — proaktywność jest uprawnieniem
nadanym, nie cechą wrodzoną.

**Anatomia.**
- Klasy pilności z twardymi definicjami: *krytyczne* (szkoda nieodwracalna bez
  reakcji teraz), *ważne* (decyzja potrzebna w znanym terminie), *przydatne*
  (wartość bez terminu). Klasę definiuje skutek braku reakcji, nigdy
  entuzjazm systemu wobec własnej propozycji.
- Mapa kanałów: krytyczne — kanał przerywający; ważne — skrzynka przeglądowa
  z terminem; przydatne — wyłącznie pasywnie.
- Reguły ciszy: godziny, konteksty (spotkanie, jazda, skupienie) i tematy;
  cisza domyślnie obejmuje wszystko poza klasą krytyczną.
- Budżet przerwań: limit odezwań aktywnych na dobę lub tydzień; po wyczerpaniu
  wszystko poniżej klasy krytycznej czeka w skrzynce.
- Rozliczalność: każde aktywne odezwanie niesie powód i działanie „nie
  odzywaj się w takich sprawach” — blokada działa na klasę, nie na sztukę.

**Stany.** *Cisza* — sprawy buforowane; licznik oczekujących widoczny
pasywnie. *Budżet wyczerpany* — degradacja klasy ważnej do skrzynki z jawną
informacją w raporcie. *Eskalacja* — sprawa ważna przy terminie może
awansować do krytycznej; warunek awansu zapisany w kontrakcie, nie uznaniowy.
*Po zablokowaniu klasy* — system potwierdza zakres blokady i respektuje ją
bez prób obejścia innym kanałem.

**Błędy projektowe.** Pilność definiowana ważnością dla systemu, nie skutkiem
dla użytkownika; obchodzenie ciszy „wyjątkowo ważną” sprawą klasy przydatnej;
brak budżetu; powiadomienie bez działania blokującego klasę; traktowanie
braku reakcji jako zgody na więcej odezwań.
