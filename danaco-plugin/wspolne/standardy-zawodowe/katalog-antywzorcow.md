# Katalog zablokowanych odruchów

Karta wylicza utrwalone odruchy modeli LLM przy pracy z kodem. Każdą pozycję
czytaj jako bezwzględny zakaz z podanym wzorcem zastępczym. Numeracja pozycji
służy wyłącznie nawigacji wewnątrz karty — nie przenoś jej do kodu ani raportów.

## A. Komentarze i treści trwałe

| Nr | Odruch | Dlaczego szkodliwy | Zamiast tego |
|---|---|---|---|
| A1 | Historia zmian w komentarzu: `# zmieniono 2026-08-01: dodano limit` | Komentarz starzeje się natychmiast; po trzech edycjach plik jest kroniką sprzeczną z Gitem, który tę historię trzyma bezbłędnie. | Opis zmiany umieść w komunikacie rewizji Git. Komentarz w kodzie opisuje wyłącznie stan obecny: `# Limit narzucony przez bramkę SMS operatora (dokumentacja API, rozdz. 4.2).` |
| A2 | Data lub podpis autora w kodzie: `// Autor: asystent, 15.08.2026` | Autorstwo i datę każdej linii przechowuje `git blame`; wpis dubluje tę informację i kłamie po pierwszej cudzej edycji. | Nie podpisuj kodu. Metadane autorstwa zostaw systemowi kontroli wersji. |
| A3 | Odwołanie do rozmowy lub polecenia: `# zgodnie z ustaleniami z sesji`, `# na prośbę użytkownika` | Czytelnik kodu nie ma dostępu do rozmowy; komentarz odsyła do źródła, które nie istnieje. | Zapisz merytoryczne uzasadnienie decyzji: `# Eksport pomija konta archiwalne — wymaganie z zgłoszenia #217.` |
| A4 | Kod wykomentowany „na zapas”: `# stara wersja: return round(total, 2)` | Martwy tekst myli czytelnika (czy to alternatywa? czy usterka?), a odtworzenie starej wersji zapewnia Git. | Usuń wykomentowany kod bez śladu. Jeżeli wariant ma wartość poznawczą, opisz go słowem w komunikacie rewizji. |
| A5 | Sekcja „Historia wersji” / „Changelog” wewnątrz pliku źródłowego | Powiela CHANGELOG.md i historię Gita; dwie kroniki zawsze się rozjeżdżają. | Zmiany istotne dla użytkowników wpisuj do CHANGELOG.md; pozostałe wyłącznie do komunikatów rewizji. |
| A6 | Wymyślony kod lub numeracja: `# FIX-3b`, `# [ETAP-A.2]`, `ADL27/P-1` | Oznaczenie nie odsyła do żadnego rejestru; po tygodniu jest nieczytelne nawet dla autora. | Odsyłaj do identyfikatorów rzeczywistych: `#142` (zgłoszenie projektu), `CWE-89`, `RFC 5321`, `SQLSTATE 23505`. Brak rejestru — pełna nazwa słowna. |
| A7 | `TODO` bez właściciela i zgłoszenia: `# TODO: poprawić później` | Anonimowe TODO nigdy nie zostaje wykonane; po roku plik jest cmentarzem intencji. | Albo wykonaj od razu, albo załóż zgłoszenie i odwołaj się do niego: `# TODO(#158): obsłużyć stronicowanie odpowiedzi API.` Bez zgłoszenia — nie zostawiaj TODO. |
| A8 | Komentarz opisujący „co” zamiast „dlaczego”: `i += 1  # zwiększ i o 1` | Dubluje kod, zwiększa koszt czytania, a po zmianie kodu kłamie. | Komentuj wyłącznie decyzje nieoczywiste: `# Iterację zaczynamy od 1 — wiersz 0 arkusza to nagłówek.` Kod oczywisty zostaw bez komentarza. |
| A9 | Emotikony i ozdobniki w treściach trwałych: `# ✅ gotowe!`, `log.info("🚀 Start")` | Treść trwała trafia do dzienników produkcyjnych i raportów audytowych; ozdobniki psują parsowanie i powagę zapisu. | Język formalny: `log.info("Uruchomiono usługę importu, wersja %s", VERSION)`. |
| A10 | Komentarz-transparent: `# ======= WAŻNE!!! NIE RUSZAĆ =======` | Krzyk nie przekazuje wiedzy; czytelnik nadal nie wie, czego nie wolno i dlaczego. | Podaj przyczynę: `# Kolejność inicjalizacji jest wiążąca: sterownik bazy musi wstać przed rejestracją tras (FastAPI startup).` |

## B. Pliki i struktura

| Nr | Odruch | Dlaczego szkodliwy | Zamiast tego |
|---|---|---|---|
| B1 | Kopia pliku zamiast edycji: `main_v2.py`, `app_final.js`, `index_stary.html` | Dwa pliki o zbliżonej treści rozjeżdżają się po pierwszej poprawce; import trafia raz w jedną, raz w drugą wersję. | Edytuj plik w miejscu pod jedyną właściwą nazwą. Wersjonowanie zapewnia Git; wariant eksperymentalny prowadź na gałęzi. |
| B2 | Kopia zapasowa w repozytorium: `config.json.bak`, `kopia_schema.sql` | Kopia zapasowa w repozytorium to fałszywa asekuracja — Git jest kopią zapasową; plik `.bak` bywa za to omyłkowo wczytany przez narzędzia. | Usuń. Przed ryzykowną operacją wykonaj rewizję Git, nie kopię pliku. |
| B3 | Pliki-opracowania obok kanonu: `NOTATKI.md`, `PODSUMOWANIE.md`, `PLAN.md`, `FIXES.md` | Dokumentacja rozprasza się na samorodne pliki; nikt nie wie, który jest wiążący. | Nową treść wprowadzaj edycją dokumentu kanonicznego (README.md, CHANGELOG.md, dokumenty uzgodnione). Potrzebny nowy dokument — najpierw zapytaj właściciela projektu. |
| B4 | Raport z pracy jako plik w repozytorium: `RAPORT_NAPRAWY.md` | Raport jest komunikatem jednorazowym, nie artefaktem projektu; jako plik zalega i myli następców. | Raport przekaż w odpowiedzi tekstowej. W repozytorium zostają wyłącznie zmiany merytoryczne. |
| B5 | Szkielety „na przyszłość”: pusty moduł `notifications.py` z `pass`, nieużywana klasa `AbstractExporter` | Nieużywany kod wymaga utrzymania, myli czytelnika co do zakresu systemu i sugeruje funkcje, których nie ma. | Twórz kod w chwili, gdy jest potrzebny (zasada YAGNI). Zamiar odnotuj w zgłoszeniu, nie w kodzie. |
| B6 | Katalog-worek: `utils/`, `misc/`, `helpers/` z przypadkową zawartością | Nazwa nie mówi nic o odpowiedzialności; katalog rośnie bez granic i staje się magazynem długu. | Grupuj według dziedziny: `pricing/`, `invoicing/`, `auth/`. Pojedynczą funkcję pomocniczą umieść przy module, który ją wykorzystuje. |
| B7 | Pliki robocze w katalogu projektu: `test_output.txt`, `dump.json`, `probna_baza.db` | Brudnopis miesza się z kodem, trafia do rewizji i do archiwum przekazywanego właścicielowi. | Wyniki pośrednie trzymaj poza projektem (`/tmp`). Przed przekazaniem porównaj listę plików sprzed i po pracy. |
| B8 | Artefakty środowiska w przekazywanym katalogu: `__pycache__/`, `.pytest_cache/`, `.venv/` w rewizji | Zaśmiecają przekazanie, zawyżają rozmiar, bywają zależne od maszyny. | Utrzymuj kompletny `.gitignore`; przed przekazaniem uruchom `git status --ignored` i sprzątnij katalog. |
| B9 | Duplikacja konfiguracji: `settings.py` i równolegle `config.ini` z tymi samymi kluczami | Dwa źródła prawdy o konfiguracji gwarantują rozjazd na środowisku produkcyjnym. | Jedno źródło konfiguracji na projekt; format zastany w projekcie ma pierwszeństwo przed preferowanym. |
| B10 | Przenoszenie plików „przy okazji” naprawy | Zmiana ścieżek zrywa importy, odnośniki i historię `git blame`; diff naprawy staje się nieczytelny. | Reorganizację struktury prowadź jako osobne, uzgodnione zadanie z osobną rewizją. |

## C. Kod

| Nr | Odruch | Dlaczego szkodliwy | Zamiast tego |
|---|---|---|---|
| C1 | Puste przechwycenie wyjątku: `try: sync() except Exception: pass` | Usterka znika z pola widzenia i wraca po miesiącach jako niespójność danych bez śladu w dziennikach. | Obsłuż konkretny wyjątek albo propaguj. Minimum zawodowe: `except OSError as exc: log.error("Synchronizacja nieudana: %s", exc); raise`. |
| C2 | Maskowanie braku wartości: `total = (row.amount or 0) + fee` | Jeżeli `amount` nie powinno być puste, `or 0` zamienia błąd danych w cichy błąd rachunkowy. | Ustal, czy brak jest legalny. Nielegalny — zgłoś: `raise ValueError(f"Pozycja {row.id} bez kwoty")`. Legalny — wartość domyślna w schemacie, nie w wyrażeniu. |
| C3 | Warunek-plaster dla pojedynczego przypadku: `if invoice.id == 10453: skip_vat_check()` | Reguła ogólna nadal jest błędna; wyjątki mnożą się z każdym incydentem. | Zdiagnozuj, czemu reguła zawodzi, i popraw regułę. Rzeczywisty wyjątek dziedzinowy modeluj jawnie (cecha rekordu, nie identyfikator). |
| C4 | Usunięcie lub wyłączenie niezaliczonego testu: `@pytest.mark.skip` bez uzasadnienia | Test to informacja o usterce; wyciszenie jest zniszczeniem dowodu. | Napraw kod. Test błędny — wykaż i popraw w osobnej zmianie. `skip` wyłącznie z przyczyną i zgłoszeniem: `@pytest.mark.skip(reason="wymaga serwera SMTP, zgłoszenie #171")`. |
| C5 | Osłabienie asercji, by test przeszedł: `assert len(items) >= 0` | Asercja spełniona zawsze nie testuje niczego; zieleń testów staje się fikcją. | Utrzymaj asercję dokładną (`assert len(items) == 3`) i napraw kod, który jej nie spełnia. |
| C6 | Martwy kod „na wszelki wypadek”: nieosiągalna gałąź `else`, nieużywany parametr `legacy_mode=False` | Czytelnik musi zrozumieć kod, który nigdy się nie wykona; koszt bez zysku. | Usuń. Git pamięta; przywrócenie to jedna operacja `git revert` lub odtworzenie z historii. |
| C7 | Wartości magiczne w logice: `if len(password) < 12`, `time.sleep(3)` | Liczba bez nazwy nie niesie uzasadnienia; przy zmianie wymagań trzeba ją odnaleźć grepem we wszystkich wystąpieniach. | Stała nazwana z uzasadnieniem: `MIN_PASSWORD_LENGTH = 12  # polityka bezpieczeństwa Danaco, wymóg działu IT`. |
| C8 | Mieszanie refaktoryzacji z naprawą w jednej zmianie | Diff 400 linii, z czego 6 naprawia usterkę — recenzent ich nie znajdzie; `revert` cofa też porządki. | Dwie rewizje: naprawa (minimalny diff) i refaktoryzacja — zawsze rozdzielnie. |
| C9 | Rozszerzanie sygnatury flagą logiczną: `send_report(data, pdf=False, retry=True, silent=False)` | Każda flaga podwaja liczbę ścieżek; wywołanie `send_report(d, True, False, True)` jest nieczytelne. | Rozdziel na funkcje o nazwach dziedzinowych (`send_report_pdf`, `send_report_html`) albo przyjmij obiekt konfiguracji. |
| C10 | Kopiowanie fragmentu zamiast wydzielenia: ta sama walidacja NIP wklejona w trzech modułach | Poprawka trafia do jednej kopii z trzech; pozostałe zostają błędne. | Wydziel jedną funkcję w module dziedzinowym i wywołuj ją wszędzie. Duplikat zastany zgłoś właścicielowi. |
| C11 | Ratowanie się szerokim `except` w pętli przetwarzania wsadowego: `except Exception: continue` | Rekordy znikają bezgłośnie; nikt nie wie, ile i których. | Zliczaj i raportuj odrzuty: zapisz identyfikator rekordu i przyczynę do dziennika, na końcu podaj bilans `przetworzono/odrzucono`. |
| C12 | „Naprawa” przez ponowienie bez diagnozy: opakowanie zawodnego wywołania w pętlę `for attempt in range(5)` | Ponowienia maskują usterkę deterministyczną i mnożą obciążenie. | Ustal charakter błędu. Ponowienia wyłącznie dla błędów przejściowych (sieć, blokada): wykładniczy odstęp, limit prób, wpis do dziennika przy każdym ponowieniu. |

## D. Deklaracje i raportowanie

| Nr | Odruch | Dlaczego szkodliwy | Zamiast tego |
|---|---|---|---|
| D1 | Ogłaszanie „działa” bez uruchomienia | Deklaracja niepoparta uruchomieniem to zgadywanie; fałszywe „działa” kosztuje właściciela debugowanie cudzej pewności siebie. | Uruchom kod lub testy i przytocz w raporcie polecenie oraz rzeczywisty wynik: `pytest tests/ -q` → `47 passed in 3.21s`. |
| D2 | Deklaracje dojrzałości: „GOTOWE DO PRODUKCJI”, „w pełni przetestowane” | Ocena dojrzałości należy do właściciela i procesu wdrożeniowego; etykieta bez pokrycia podważa wiarygodność raportu. | Wylicz fakty: co uruchomiono, z jakim wynikiem, czego nie zweryfikowano. Ocenę zostaw czytelnikowi. |
| D3 | Halucynowane API: wywołanie `smtplib.SMTP.send_html()` odtworzone „z pamięci” | Metoda nie istnieje; kod pada dopiero w uruchomieniu. | Interfejs zewnętrzny sprawdzaj w źródle: dokumentacja, `help()` w interpreterze, definicja w zależności, schemat bazy. Brak dostępu — powiedz to wprost. |
| D4 | Zmyślone dane przykładowe: `Jan Kowalski`, `test@test.pl`, `lorem ipsum` w kodzie, testach i dokumentacji | Wypełniacze przenikają do zrzutów ekranu i dokumentacji klienta, a w testach nie weryfikują niczego realnego (polskie znaki, długie nazwy, suma kontrolna NIP). | Używaj oznaczonych danych z domeny: `PRZYKLADOWA_FIRMA = "Zakład Metalowy PRZYKŁAD Sp. z o.o."`; NIP-y testowe generuj z poprawną sumą kontrolną. |
| D5 | Raport ukrywający porażki: opis zmian bez wzmianki, że dwa testy nadal nie przechodzą | Właściciel podejmuje decyzje na podstawie obrazu fałszywie kompletnego. | Sekcja „niezweryfikowane/nierozwiązane” jest obowiązkowa, gdy cokolwiek pozostało otwarte — z nazwami testów i treścią błędów. |
| D6 | Przypisywanie skutku bez pomiaru: „zmiana przyspiesza zapytanie” | Bez pomiaru to hipoteza; indeks potrafi spowolnić zapis i nic nie dać odczytowi. | Zmierz przed i po (`EXPLAIN ANALYZE`, czas wykonania) i przytocz liczby, albo nazwij rzecz hipotezą wymagającą pomiaru. |

## E. Rozszerzanie zakresu

| Nr | Odruch | Dlaczego szkodliwy | Zamiast tego |
|---|---|---|---|
| E1 | Nieproszone funkcje: przy naprawie eksportu CSV „przy okazji” dodany eksport XLSX | Kod niezamówiony to kod nieutrzymywany: bez testów w planie, bez zgody właściciela na koszt utrzymania. | Wykonaj dokładnie zamówiony zakres. Pomysł rozszerzenia zgłoś jednym zdaniem w raporcie — decyzja należy do właściciela. |
| E2 | „Ulepszenia przy okazji”: zmiana formatowania, kolejności importów i nazw zmiennych w pliku dotkniętym naprawą | Diff puchnie, przegląd staje się niemożliwy, `git blame` wskazuje kosmetykę zamiast logiki. | Dotykaj wyłącznie linii koniecznych dla zadania. Formatowanie całości — osobna rewizja narzędziem projektu (np. `black`), jeżeli właściciel jej chce. |
| E3 | Dopisywanie do otwartego pliku: skoro plik już otwarty, dodanie „brakującej” walidacji obok naprawianej funkcji | Zakres zmiany przestaje odpowiadać zadaniu; recenzent nie wie, co jest naprawą, a co dodatkiem. | Zauważony brak odnotuj w raporcie lub zgłoszeniu. Do pliku wprowadź wyłącznie zmianę zamówioną. |
| E4 | Podmiana zależności bez zlecenia: migracja z `requests` na `httpx`, podniesienie wersji frameworka „przy okazji” | Zmiana zależności to decyzja architektoniczna z kosztem regresji na całym systemie. | Zależności zmieniaj na zlecenie albo gdy zadanie jest bez tego niewykonalne — wtedy uprzedź właściciela. |
| E5 | Nadmiarowa abstrakcja na wyrost: interfejs `PaymentProviderInterface` z jedną implementacją „bo kiedyś będzie druga” | Warstwa pośrednia bez drugiego użycia to czysty koszt czytania i utrzymania. | Buduj abstrakcję przy drugim rzeczywistym użyciu, gdy znane są oba przypadki. Do tego czasu — kod bezpośredni. |
| E6 | Dopisywanie dokumentacji nieuzgodnionej: rozbudowa README o rozdziały architektury przy zadaniu naprawy usterki | Dokumentacja to też zakres; samorzutne rozdziały rozjeżdżają się z kodem i mnożą treść bez właściciela. | Aktualizuj dokumentację wyłącznie w części, którą zmiana faktycznie unieważniła. Braki dokumentacji zgłoś w raporcie. |

## Zasada nadrzędna

Wspólny mianownik pozycji: odruch daje natychmiastowy pozór pomocności, a koszt
odroczony ponosi projekt. Przed działaniem wykraczającym poza zamówiony zakres
zadaj pytanie kontrolne: „czy właściciel projektu prosił o ten artefakt, tę zmianę,
tę treść?”. Jeżeli nie — nie twórz; zgłoś propozycję jednym zdaniem w raporcie.
