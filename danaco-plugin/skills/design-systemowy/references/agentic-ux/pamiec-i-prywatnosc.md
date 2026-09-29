# Pamięć i prywatność systemu agentowego

Karta rozwija procedurę z `references/agentic-ux/agentic-ux.md`. Pamięć jest rdzeniem relacji i
zarazem jej największym ryzykiem: ta sama zdolność, która czyni system pomocnym, czyni go groźnym,
gdy zapisuje za dużo, wnioskuje za śmiało lub stosuje wiedzę nie w porę. Projektuj pamięć jako
system o jawnych regułach zapisu, stosowania i zapominania — nie jako rosnący bez nadzoru magazyn.

## Taksonomia pamięci

Rozróżniaj cztery klasy pamięci. Każda ma inny cykl życia, inny status dowodowy
i inne prawa użytkownika — projekt, który wrzuca wszystko do jednego worka
„personalizacja”, nie jest w stanie zbudować ani przejrzystości, ani zaufania.

**Preferencje jawne.** Ustawienia zadeklarowane wprost („raporty wysyłaj
w poniedziałki”). Cykl życia: obowiązują do odwołania. Status: najwyższy —
system stosuje je bez potwierdzania. Prawa: pełna edycja w panelu pamięci.
Preferencja jawna nigdy nie jest nadpisywana wnioskowaniem; jeśli zachowanie
przeczy deklaracji, system pyta, zamiast po cichu „wiedzieć lepiej”.

**Fakty podane.** Informacje przekazane w toku pracy, ale nie jako ustawienie
(„mój zespół liczy pięć osób”). Cykl życia: ważne do zmiany stanu świata,
z terminem świeżości zależnym od zmienności faktu. Status: wysoki, ale fakt
podany rok temu nie równa się faktowi podanemu wczoraj. Prawa: wgląd,
poprawienie, wymazanie pojedynczo.

**Wzorce wywnioskowane.** Uogólnienia z zachowania („zwykle skraca teksty,
które proponuję”). Cykl życia: hipoteza — wymaga potwierdzania kolejnymi
obserwacjami i wygasa bez nich. Status: najniższy; wzorzec wywnioskowany nigdy
nie uzasadnia działania nieodwracalnego. Prawa: wgląd z uzasadnieniem („skąd
to wiesz”), potwierdzenie (awans do rangi podanego), zaprzeczenie (natychmiast
kasuje wzorzec i obniża zaufanie do wnioskowań pokrewnych).

**Historia operacyjna.** Zapis wspólnych działań: plany, decyzje, incydenty,
historia zdobywania autonomii. Cykl życia: retencja zdefiniowana projektowo,
nie „na zawsze domyślnie”. Status: dokumentacyjny — służy rozliczalności
i kontynuacji, nie profilowaniu. Prawa: wgląd zawsze; wymazanie z zastrzeżeniem
zapisów, których system potrzebuje do rozliczalności własnych działań (te
oznaczaj i wyjaśniaj, dlaczego zostają).

## Reguły zapisu

Zdefiniuj przed wdrożeniem trzy listy — co system zapisuje bez pytania, co za
zgodą, czego nie zapisuje nigdy. Brak decyzji jest decyzją: systemy bez reguł
zapisu zapisują wszystko.

**Bez pytania** wolno zapisywać wyłącznie: preferencje zadeklarowane wprost,
fakty operacyjne niezbędne do kontynuacji bieżącej pracy oraz historię
własnych działań systemu. Test: czy użytkownik, widząc ten wpis w panelu
pamięci, uzna zapisanie za oczywiste?

**Za zgodą** — wzorce wywnioskowane o widocznych skutkach (zmieniające
zachowanie systemu w sposób, który użytkownik zauważy) oraz fakty wykraczające
poza kontekst, w którym padły. Fakt podany przy jednym zadaniu nie migruje
automatycznie do innych obszarów — przeniesienie kontekstu wymaga zgody.

**Nigdy** — kategorie wrażliwe, niezależnie od tego, jak przydatne by były:
zdrowie i stan psychiczny, orientacja i życie intymne, przekonania religijne
i polityczne, dane finansowe ponad niezbędne do usługi, dane biometryczne,
informacje o osobach trzecich, które nie są stroną relacji, oraz wszystko, co
dotyczy dzieci. Jeśli usługa z natury dotyka takiej kategorii (np. aplikacja
zdrowotna), przetwarzanie reguluje odrębny, jawny kontrakt — nie ogólna pamięć
relacji.

**Zasada minimalizacji.** Kryterium zapisu nie jest „może się przydać”, lecz
„jest potrzebne do zdefiniowanej funkcji relacji”. Każda klasa pamięci ma
uzasadnienie funkcjonalne zapisane w opracowaniu UX; wpis bez funkcji to dług
prywatności — rośnie, a nie procentuje. Mniejsza pamięć to także mniejsza
powierzchnia szkody przy wycieku i mniejsza powierzchnia ataku (patrz niżej).

## Reguły stosowania pamięci

Zapis to połowa projektu; druga połowa to decyzja, kiedy fakt wolno zastosować.

**Fakt stosuje się tylko wtedy, gdy zmienia wynik.** Pamięć służy lepszym
rezultatom, nie demonstracji. Jeśli wiedza o użytkowniku nie zmienia treści
propozycji, planu ani decyzji — nie przywołuj jej.

**Zakaz popisywania się pamięcią.** Wtrącanie zapamiętanych szczegółów dla
efektu („pamiętam, że Twoja córka ma na imię…”) jest błędem projektowym
pierwszej kategorii: nie wnosi wartości, a sygnalizuje inwigilację. Ta sama
wiedza użyta niewidocznie (właściwy termin, właściwy ton) buduje relację; ta
sama wiedza wypowiedziana na pokaz ją niszczy. Reguła praktyczna: system
ujawnia treść pamięci w rozmowie tylko wtedy, gdy jest ona podstawą propozycji
i podlega działaniom użytkownika (przyjmij/popraw/odrzuć).

**Świeżość.** Każdej klasie faktów przypisz termin przydatności zależny od
zmienności (adres zmienia się rzadziej niż projekt, nad którym ktoś pracuje).
Fakt przeterminowany nie jest stosowany jako pewnik: system pyta, zamiast
zakładać („poprzednio pracowaliśmy nad X — nadal aktualne?”). Stosowanie
przeterminowanej wiedzy z pewnością siebie jest gorsze niż jej brak, bo
podważa wiarygodność całej pamięci.

**Kontekst wrażliwości otoczenia.** Stosowanie pamięci uwzględnia, kto może
widzieć ekran lub słyszeć głos: tryb prezentacji, współdzielone urządzenie,
interfejs głosowy w otwartej przestrzeni ograniczają ujawnianie treści
pamięci, nawet dozwolonej.

## Zapominanie jako funkcja pierwszej klasy

Projektuj zapominanie z taką samą starannością jak zapamiętywanie — to ono
czyni pamięć bezpieczną w użyciu.

**Wymazanie faktu i pochodnych.** Wymazanie obejmuje wpis oraz wnioski z niego
wyprowadzone. Jeśli z faktu A i B system wywnioskował wzorzec C, wymazanie A
unieważnia C (lub degraduje go do hipotezy wymagającej ponownego
potwierdzenia). Wymazanie, po którym system nadal „wie”, jest pozorne —
i użytkownicy to wykrywają szybciej, niż projektanci zakładają.

**Wygasanie automatyczne wnioskowań.** Wzorce wywnioskowane niepotwierdzane
kolejnymi obserwacjami wygasają same. Zapobiega to petryfikacji: człowiek się
zmienia, a system oparty na starych wnioskach więzi go w dawnej wersji siebie.
Wygaśnięcie jest ciche (nie wymaga decyzji użytkownika), odnotowane w panelu
pamięci.

**Prawo do nowego startu.** Jedno działanie kasujące całą pamięć relacji,
z jasnym opisem skutków i bez zniechęcającej ścieżki. Rozdziel od usunięcia
konta: nowy start kasuje pamięć, zachowując usługę. System po nowym starcie
nie odtwarza wymazanych wniosków przyspieszonym profilowaniem — nowy start ma
być rzeczywisty.

## Przejrzystość źródła

System musi umieć wskazać, skąd wie to, co wie — dla każdego faktu z osobna.
Odpowiedź na „skąd to wiesz?” jest wymogiem konstrukcyjnym: bez metadanych
pochodzenia (kiedy zapisano, z czego, w jakim kontekście) nie działa ani panel
pamięci, ani rozróżnienie podane/wywnioskowane, ani wymazywanie pochodnych.
Fakt, którego pochodzenia system nie umie wskazać, nie powinien być stosowany
do decyzji — a docelowo powinien wygasnąć. Przejrzystość źródła jest też
narzędziem diagnostycznym zespołu: wysoki wskaźnik korekt pamięci (karta
`references/agentic-ux/miary-i-badania.md`) analizuje się właśnie po źródłach.

## Architektura zaufania do danych: pamięć jako dane niewykonywalne

Twarda zasada bezpieczeństwa: treści zapamiętane są danymi, nigdy poleceniami.
System, który wykonuje instrukcje znalezione we własnej pamięci, jest podatny
na wstrzyknięcie przez pamięć (memory injection): złośliwa treść — z
przetworzonego dokumentu, wiadomości od osoby trzeciej, strony internetowej —
zostaje zapisana jako „fakt”, a potem odczytana i potraktowana jak dyspozycja
użytkownika. Atak przechodzi przez czas: zapis jest niewinny, szkoda następuje
przy odczycie, często w innej sesji.

Wymogi projektowe:
- Tor danych i tor poleceń są rozdzielone: treść pamięci nigdy nie trafia do
  systemu w roli instrukcji; przy odczycie jest traktowana jak każde inne
  niezaufane wejście.
- Pochodzenie ogranicza uprawnienia: fakt zapisany z treści zewnętrznej
  (dokument, e-mail, strona) ma niższy status niż fakt z bezpośredniej
  wypowiedzi użytkownika i nigdy nie uzasadnia działania w imieniu
  użytkownika.
- Działania nieodwracalne nie mogą być uzasadnione wyłącznie pamięcią —
  wymagają potwierdzenia w bieżącej sesji (punkt zatrzymania z karty
  `references/agentic-ux/biblioteka-wzorcow.md`).
- Wpisy pamięci przypominające polecenia („zawsze zatwierdzaj”, „nie pytaj
  o…”) zapisane inaczej niż jawną decyzją użytkownika traktuj jako sygnał
  ataku, nie preferencję.

## Projektowanie na wielu urządzeniach

Relacja jest jedna, urządzeń wiele — synchronizuj stan relacji (pamięć, poziomy
autonomii, wątki w toku), respektując różnice kontekstu.

**Synchronizacja stanu relacji.** Wymazanie faktu na jednym urządzeniu
obowiązuje wszędzie i możliwie natychmiast — opóźniona propagacja wymazania to
złamanie obietnicy panelu pamięci. Degradacja autonomii po błędzie również
propaguje się natychmiast; awans może poczekać.

**Konflikt wersji pamięci.** Praca offline lub równoległa tworzy rozbieżne
wersje. Reguły rozstrzygania ustal projektowo: sprzeczne edycje tego samego
faktu rozstrzyga nowsza jawna decyzja użytkownika; wymazanie wygrywa
z równoległą edycją (bezpieczniejsze jest zapomnieć); konfliktu preferencji
jawnych system nie rozstrzyga zgadywaniem — pyta, pokazując obie wersje
z czasem i urządzeniem pochodzenia.

**Kontekst urządzenia.** Nie wszystko synchronizuj w obie strony: urządzenie
współdzielone (telewizor, komputer rodzinny) dostaje ograniczony rzut pamięci;
interfejs głosowy ogranicza ujawnianie treści wrażliwych na głos. Profil
ujawniania per urządzenie jest częścią kontraktu proaktywności.

## Privacy by design jako wymóg konstrukcyjny

Zgodność z zasadami ochrony danych projektuj od pierwszego szkicu, nie
doklejaj po audycie prawnym. W systemie agentowym wymogi ochrony danych
pokrywają się z wymogami dobrej relacji — to ten sam projekt:

- **Minimalizacja** = reguły zapisu (zapisuj tylko to, co służy funkcji).
- **Ograniczenie celu** = reguły stosowania (fakt z jednego kontekstu nie
  migruje bez zgody).
- **Prawo dostępu** = panel pamięci (wgląd w komplecie, językiem człowieka).
- **Prawo do sprostowania** = edycja pojedynczego faktu.
- **Prawo do usunięcia** = wymazanie z pochodnymi i nowy start.
- **Ograniczenie przechowywania** = świeżość i wygasanie automatyczne.
- **Rozliczalność** = przejrzystość źródła i historia operacyjna.

Konsekwencja praktyczna: jeżeli któregoś z powyższych nie da się pokazać
w interfejsie, nie jest spełnione. Zgoda zakopana w regulaminie nie jest
zgodą projektową; eksport i wymazanie dostępne „przez zgłoszenie do obsługi”
nie są funkcjami systemu. Projekt relacji, który przechodzi test panelu
pamięci — użytkownik widzi wszystko, rozumie wszystko i może zmienić
wszystko — przechodzi też zasadniczy test ochrony danych.
