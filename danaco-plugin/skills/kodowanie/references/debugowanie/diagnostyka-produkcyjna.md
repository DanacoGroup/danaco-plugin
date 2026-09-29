# Diagnostyka produkcyjna — diagnoza bez debuggera

Na środowisku produkcyjnym nie ma debuggera ani swobodnego restartu.
Materiałem dowodowym są dzienniki, metryki, zrzuty stanu i różnice między
środowiskami; karta opisuje, jak z tego materiału prowadzić diagnozę o rygorze
etapów 1–3 procedury głównej.

## Czytanie dzienników jak dowodów

Dziennik to zeznanie świadka: bywa niepełny, przesunięty w czasie i mylący
bez metody czytania.

- **Korelacja żądań.** Pojedynczy wpis o błędzie jest bez wartości, dopóki nie
  zbierzesz wszystkich wpisów tego samego żądania. Ustal, czy system nadaje
  identyfikator korelacyjny (nagłówek `X-Request-ID`, `traceparent` W3C, pole
  `request_id` w logu strukturalnym) i filtruj po nim przez wszystkie usługi
  na ścieżce żądania. Jeżeli identyfikatora nie ma, koreluj po krotce
  (znacznik czasu ± tolerancja, adres klienta, ścieżka żądania), odnotuj
  w raporcie, że korelacja jest przybliżona, a brak identyfikatora zgłoś
  właścicielowi jako usterkę obserwowalności.
- **Oś czasu zdarzeń z wielu źródeł.** Zbuduj jedną chronologię: wpisy z
  aplikacji, serwera WWW, bazy danych, systemu operacyjnego (`journalctl`,
  `dmesg`), równoważnika obciążenia i harmonogramu zadań — scalone po czasie
  w jednej liście, prowadzonej w rozmowie. Dopiero na scalonej osi widać
  przyczynowość: restart bazy o 14:02:31 poprzedza falę błędów aplikacji
  o 14:02:33, a nie odwrotnie.
- **Strefa czasowa jako pierwszy podejrzany.** Zanim porównasz znaczniki czasu
  z dwóch źródeł, ustal strefę każdego z nich — dzienniki aplikacji bywają w
  UTC, systemowe w czasie lokalnym, baza w strefie sesji, a przeglądarka
  klienta w jeszcze innej. Przesunięcie o równą godzinę w pozornie niespójnej
  chronologii to niemal zawsze strefa, nie magia. Sprawdź też dryf zegarów
  między maszynami (`timedatectl`, status NTP) — dryf rzędu sekund unieważnia
  wnioskowanie o kolejności zdarzeń między hostami.
- **Pierwszy błąd, nie ostatni.** W kaskadzie awarii dziennik zapełnia się
  błędami wtórnymi (odmowy połączeń, timeouty). Przewiń do początku incydentu
  i znajdź pierwszy wpis odbiegający od normy — często nie jest to błąd, lecz
  ostrzeżenie albo nagła zmiana wolumenu wpisów.

## Diagnoza „działa u mnie” — protokół różnicowy środowisk

Zdanie „działa u mnie, nie działa tam” to twierdzenie o istnieniu różnicy
między środowiskami; diagnoza polega na metodycznym znalezieniu tej różnicy.
Prowadź tabelę porównawczą wypełnianą faktami — każda komórka pochodzi z
wykonanego polecenia, nie z pamięci ani z dokumentacji:

| Oś porównania | Jak ustalić stan faktyczny |
| --- | --- |
| Wersja aplikacji (rewizja) | `git rev-parse HEAD` na obu; na produkcji — znacznik wersji z punktu diagnostycznego |
| Środowisko uruchomieniowe | `python --version`, `node --version`, wersja obrazu kontenera (skrót, nie etykieta `latest`) |
| Zależności | zrzut faktycznie zainstalowanych: `pip freeze`, `npm ls --all`; porównuj z plikiem blokady |
| Zmienne środowiskowe | zrzut z procesu, nie z pliku: `cat /proc/<pid>/environ | tr '\0' '\n'` — `.env` mówi, co miało być, proces mówi, co jest |
| Konfiguracja | faktycznie wczytane wartości wypisane przez aplikację; precedencja źródeł |
| Dane | wolumen i kształt: liczność tabel, obecność NULL, duplikatów, znaków spoza ASCII |
| Uprawnienia | użytkownik procesu (`ps -o user= -p <pid>`), prawa do plików, uprawnienia roli bazodanowej (`\du`, `GRANT`) |
| Locale i kodowanie | `locale`, kodowanie bazy i połączenia, `LANG`/`LC_ALL` procesu — sortowanie i parsowanie liczb zależą od locale |
| Sieć i zasoby | dostępność usług zależnych z tej maszyny, limity (`ulimit -n`), pamięć, serwer pośredniczący |

Nie przerywaj na pierwszej różnicy jakiejkolwiek — środowiska różnią się
zawsze i tuzinami szczegółów; różnica jest podejrzana dopiero wtedy, gdy
istnieje mechanizm łączący ją z objawem. Gdy kandydatów jest wielu, przenoś
różnice połówkami do środowiska działającego (bisekcja konfiguracji — karta
technik zaawansowanych). Kierunek odwrotny — „upodobnić produkcję do
dewelopera” — jest zakazany jako działanie na ślepo na produkcji.

## Diagnoza po awarii — zrzuty i sekwencja pytań

Gdy proces padł, materiałem jest to, co po nim zostało.

- **Core dump (Linux).** Sprawdź, czy zrzuty są włączone: `ulimit -c`,
  `kernel.core_pattern` (na systemach z systemd: `coredumpctl list`,
  `coredumpctl debug <pid>`). Analiza: `gdb <binarka> <core>`, następnie
  `bt full` (ślad z wartościami zmiennych lokalnych), `info threads`,
  `thread apply all bt` — awaria bywa w innym wątku, niż sugeruje sygnał.
  Potrzebne są symbole debugowania zgodne z dokładnie tą binarką, która
  padła — zachowaj binarkę wraz ze zrzutem.
- **Minidump (Windows / Crashpad / Breakpad).** Mały zrzut ze stosami wątków
  i wybranymi fragmentami pamięci; analiza w WinDbg (`!analyze -v`) albo
  narzędziem `minidump-stackwalk` z plikami symboli danego wydania.
- **Zrzut sterty (języki zarządzane).** Java: `jmap -dump:live,file=heap.hprof
  <pid>` lub `-XX:+HeapDumpOnOutOfMemoryError` zawczasu; analiza w Eclipse MAT
  — raport podejrzanych o wyciek i ścieżki do korzeni GC. Node.js: zrzut przez
  inspektora (`node --inspect`, zakładka Memory) albo `process.report`.
  Python: `tracemalloc` wymaga włączenia przed zdarzeniem — na procesach
  podatnych włączaj instrumentację zapobiegawczo.

Sekwencja pytań post-mortem — w tej kolejności, z notowaniem odpowiedzi:

1. Co dokładnie padło — proces, wątek, żądanie, host? Jeden egzemplarz czy
   wszystkie?
2. Kiedy — pierwszy moment odchylenia na scalonej osi czasu, nie moment
   zauważenia przez ludzi?
3. Co się zmieniło bezpośrednio przedtem — wdrożenie, konfiguracja, dane,
   ruch, infrastruktura, certyfikaty, zadanie cykliczne?
4. Jaki był stan zasobów w chwili awarii — pamięć, dysk, deskryptory, pula
   połączeń (z metryk historycznych)?
5. Czy sygnał zgonu coś mówi — SIGKILL bez śladu w aplikacji wskazuje zabójcę
   zewnętrznego (OOM killer: `Killed process` w `dmesg`; nadzorca kontenerów:
   limit pamięci, sonda żywotności), SIGSEGV — błąd pamięci, kod wyjścia
   własny — ścieżkę zakończenia w kodzie?
6. Czy to pierwszy raz — przeszukaj dzienniki wstecz; awaria „pierwsza”
   zwykle okazuje się trzecią, tylko wcześniejsze przeszły niezauważone.

## Regresja wdrożeniowa — co naprawdę weszło w wydaniu

Po zdaniu „zepsuło się po wdrożeniu” ustal pełny ładunek wydania — kod to
jedna z czterech osi:

- **Kod**: `git log --oneline poprzednie..obecne` oraz diff; szukaj zmian w
  ścieżce objawu, ale też pozornie odległych (wspólne biblioteki, middleware,
  serializacja).
- **Zależności**: diff plików blokady (`package-lock.json`, `poetry.lock`,
  `requirements.txt`) między wydaniami — aktualizacja zależności przechodniej
  wchodzi bez zmiany pliku deklaracji; porównuj wersje rozstrzygnięte, nie
  deklarowane zakresy.
- **Migracje**: które wykonały się przy wdrożeniu, czy wszystkie z
  powodzeniem, czy któraś zmieniła typ kolumny, wartość domyślną, indeks.
  Częsty przypadek: regresja wydajnościowa po migracji — nowy indeks
  nieużywany, stary usunięty, statystyki nieodświeżone.
- **Konfiguracja i infrastruktura**: zmienne środowiskowe wydania, wersja
  obrazu bazowego i środowiska uruchomieniowego, zmiany zarządzane równolegle
  (równoważnik, TLS, DNS, limity).

Dopiero suma czterech diffów wyznacza obszar podejrzany; gdy pozostaje
szeroki, bisekcja rewizji na środowisku przejściowym zawęża go szybciej niż
czytanie diffów w całości. Wycofanie wydania (rollback) jest legalnym
narzędziem diagnostycznym: gasi objaw — hipoteza „regresja wdrożeniowa”
potwierdzona; nie gasi — obszar podejrzany przesuwa się na dane, ruch lub
infrastrukturę, co oszczędza dni czytania kodu.

## Błędy wyłącznie pod obciążeniem

Klasa błędów niewidocznych w testach: mechanizm wymaga wolumenu. Naucz się
ich sygnatur w dziennikach:

- **Wyczerpanie puli połączeń**: czasy odpowiedzi rosną schodkowo, w logach
  `connection pool exhausted`, `TimeoutError: QueuePool limit`, a baza
  pokazuje połączenia `idle in transaction` (PostgreSQL: `SELECT state,
  count(*) FROM pg_stat_activity GROUP BY state`). Typowa przyczyna źródłowa:
  połączenie trzymane przez czas operacji zewnętrznej albo niezwracane w
  ścieżce błędu — powiększenie puli leczy objaw, naprawy wymaga cykl życia
  połączenia.
- **Limity deskryptorów plików**: `EMFILE`/`Too many open files`; sprawdź
  limit (`cat /proc/<pid>/limits`) i zużycie (`ls /proc/<pid>/fd | wc -l`,
  rozkład przez `lsof -p <pid>`). Rosnąca liczba gniazd w stanie `CLOSE_WAIT`
  oznacza niezamykane połączenia — wyciek zasobu, nie za niski limit.
- **Timeouty kaskadowe**: usługa A czeka na B, B na C; timeout A krótszy niż
  suma prób B wywołuje falę przerwanych żądań, które ponawiane pogłębiają
  obciążenie C. Sygnatura: błędy timeout pojawiają się w kolejności odwrotnej
  do zależności, a wolumen żądań do usługi najgłębszej rośnie zamiast maleć.
  Szukaj ogniska pierwotnego — usługi, której opóźnienie wzrosło pierwsze.

Odtworzenie: błędu obciążeniowego nie reprodukuje się pojedynczym żądaniem —
przygotuj generator obciążenia odzwierciedlający produkcyjny profil ruchu, na
środowisku przejściowym o produkcyjnych limitach zasobów; wynik na środowisku
o innych limitach nie jest dowodem.

## Zasada: dowody PRZED restartem

Restart przywraca usługę i jednocześnie niszczy cały ulotny materiał dowodowy.
Zawodowa odpowiedź na presję natychmiastowego restartu: zbierz dowody najpierw
— to kwestia minut, a bez nich diagnoza po incydencie sprowadza się do
spekulacji i incydent wróci. Kolejność zbierania, od najulotniejszych:

1. Stan procesów: `ps aux`, dla podejrzanego `cat /proc/<pid>/status`,
   `/proc/<pid>/limits`, lista deskryptorów; ślad stosu żywego procesu bez
   zabijania go (`py-spy dump --pid`, `jstack <pid>`,
   `gdb -p <pid> -batch -ex 'thread apply all bt'`).
2. Połączenia sieciowe: `ss -tanp` (stany gniazd, kolejki), liczność per stan.
3. Pamięć i zasoby: `free -h`, `df -h` (pełny dysk to klasyczny cichy
   sprawca), `dmesg | tail -100` (OOM, błędy IO).
4. Stan aplikacyjny: zrzut sterty lub core żywego procesu (`gcore <pid>`).
5. Kolejki: głębokości kolejek komunikatów, opóźnienie konsumentów (lag),
   zaległości zadań cyklicznych.
6. Dzienniki: skopiuj pliki z okna incydentu poza maszynę — rotacja po
   restarcie potrafi je zmieść.

Przygotuj z tej listy skrypt zawczasu — podczas incydentu nie ma czasu na
przypominanie sobie flag.

## Raport z incydentu bez teatru winy

Raport pisz tak, aby za rok obcy inżynier zrozumiał mechanizm i sprawdził
zabezpieczenia. Struktura:

1. **Skutek**: kto i jak długo był dotknięty, w liczbach.
2. **Oś czasu**: fakty ze znacznikami czasu i strefą, od pierwszego
   odchylenia do pełnego przywrócenia; każdy wpis poparty źródłem.
3. **Mechanizm**: pełny łańcuch przyczynowy od przyczyny źródłowej do skutku,
   bez ogniw „a potem stało się coś dziwnego”.
4. **Co pozwoliło usterce przejść**: brakujące zabezpieczenia — walidacja,
   test, alert, limit; właściwe miejsce pytania „dlaczego”.
5. **Działania**: naprawcze (wykonane, z dowodem) i zapobiegawcze
   (z właścicielem i terminem).

Zasady języka: opisuj systemy i procesy, nie osoby — zamiast „inżynier
pominął przegląd” pisz „zmiana tej klasy nie wymagała drugiego przeglądu”.
Zakaz „błędu ludzkiego” jako przyczyny źródłowej — jeżeli pojedyncze ludzkie
potknięcie wywołało incydent, przyczyną źródłową jest system, który na nie
pozwolił. Rozróżniaj fakty od hipotez niepotwierdzonych; hipotezy oznaczaj
wprost wraz z planem weryfikacji.
