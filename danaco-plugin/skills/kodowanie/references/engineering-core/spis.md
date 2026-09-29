# Spis modułów engineering-core

Katalog `references/engineering-core/` niesie pięć modułów pogłębionych paczki `kodowanie`:
backend Pythona i dane, bazy danych z wyszukiwaniem znaczeniowym, usługi sieciowe,
integracje z platformami PL i UE oraz debugowanie z testami i wdrożeniami. Ten plik jest
jedyną drogą wejścia do 45 plików tych modułów — poza nim żaden indeks paczki ich nie
wymienia. Karty ogólne (języki programowania, frameworki, bazy danych, narzędzia budowy)
leżą w pozostałych katalogach `references/` paczki `kodowanie` i tu nie są powtarzane.

Kolejność wczytywania: najpierw przegląd modułu, potem wyłącznie te karty pogłębione,
których wymaga zadanie. Wczytanie wszystkich pięciu przeglądów naraz to około 115 kB
kontekstu i jest błędem metody.

Wersje narzędzi i bibliotek przywołane w tych plikach traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

---

## 1. Przeglądy modułów

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/02-python-backend-dane/przeglad.md` | Wskazuje wersje odniesienia Pythona i bibliotek, zasady wyboru między nimi oraz kartę pogłębioną właściwą dla zadania. |
| `references/engineering-core/04-bazy-i-rag/przeglad.md` | Rozstrzyga, kiedy wystarczy baza relacyjna, a kiedy potrzebny jest potok wyszukiwania znaczeniowego, i wskazuje kartę właściwą. |
| `references/engineering-core/05-uslugi-sieciowe/przeglad.md` | Prowadzi po warstwie serwerowej: poczta, telefonia, kanały czasu rzeczywistego, eksploatacja usługi. |
| `references/engineering-core/06-integracje-pl-eu/przeglad.md` | Ostrzega o zmienności obszaru, podaje daty stanu i wskazuje kartę właściwą dla instytucji, z którą trzeba się zintegrować. |
| `references/engineering-core/07-debug-testy-deploy/przeglad.md` | Porządkuje drabinę weryfikacji: diagnoza, testy, obserwowalność, wdrożenie, reakcja na awarię. |

---

## 2. Python w produkcji — `02-python-backend-dane`

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/02-python-backend-dane/references/python-nowoczesny.md` | Składnia i idiomy współczesnego Pythona: typowanie, generyki, `match`, wybór między dataclass, Pydantic i msgspec. |
| `references/engineering-core/02-python-backend-dane/references/uv-i-projekt.md` | Zakładanie i utrzymanie projektu narzędziem `uv`: `pyproject.toml`, `ruff`, kontrola typów, pre-commit, układ katalogów. |
| `references/engineering-core/02-python-backend-dane/references/fastapi.md` | FastAPI w wydaniu bieżącym z wersjami przypiętymi i wykazem API usuniętych w Starlette; routery, zależności, uwierzytelnianie, błędy, streaming. |
| `references/engineering-core/02-python-backend-dane/references/async-i-zadania.md` | Praca asynchroniczna i zadania w tle: `TaskGroup`, anulowanie, limity czasu, wybór między Celery, arq, RQ i APScheduler. |
| `references/engineering-core/02-python-backend-dane/references/bazy-i-orm.md` | SQLAlchemy 2.0, Alembic i psycopg3: sesje, relacje, transakcje, migracje, pule połączeń, surowy SQL. |
| `references/engineering-core/02-python-backend-dane/references/dane.md` | Przetwarzanie danych: polars i pandas, leniwa ewaluacja, Parquet, dane większe od pamięci, walidacja zbioru. |
| `references/engineering-core/02-python-backend-dane/references/testy-pytest.md` | Zestaw testów w pytest: struktura, fixtures, parametryzacja, testy asynchroniczne, testcontainers, pokrycie, szybkość. |
| `references/engineering-core/02-python-backend-dane/references/wdrozenie-python.md` | Pakowanie i wdrożenie usługi Pythona: obraz wielostopniowy, sekrety, health, logowanie strukturalne, zamykanie na sygnał. |
| `references/engineering-core/02-python-backend-dane/references/cli-i-narzedzia.md` | Narzędzia z linii poleceń: Typer i Click, wyjście dla człowieka i dla maszyny, kody wyjścia, skrypty jednoplikowe. |

---

## 3. Bazy danych i wyszukiwanie znaczeniowe — `04-bazy-i-rag`

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/04-bazy-i-rag/references/postgres.md` | Postgres jako baza domyślna: typy, indeksy, czytanie planu zapytania, transakcje, blokady, wyszukiwanie pełnotekstowe po polsku, partycjonowanie. |
| `references/engineering-core/04-bazy-i-rag/references/pgvector.md` | Wektory w Postgresie: typy i limity, operatory odległości, wybór między HNSW i IVFFlat, kwantyzacja, filtrowanie, granice skali. |
| `references/engineering-core/04-bazy-i-rag/references/bazy-wektorowe.md` | Dedykowane bazy wektorowe: model danych, filtrowanie, wielodostępność, replikacja, koszt — z porównaniem dziewięciu rozwiązań. |
| `references/engineering-core/04-bazy-i-rag/references/potok-dokumentow.md` | Droga od pliku do fragmentu: pozyskanie z PDF, OCR, zachowanie tabel, normalizacja, deduplikacja, metadane z uprawnieniami. |
| `references/engineering-core/04-bazy-i-rag/references/fragmentacja.md` | Dzielenie dokumentu na fragmenty: rozmiary, nakładanie, hierarchia rodzic–dziecko, kontekstualizacja fragmentu. |
| `references/engineering-core/04-bazy-i-rag/references/embeddingi.md` | Dobór modelu osadzeń, jakość dla polszczyzny, normalizacja, osadzanie wsadowe, koszt ponownego osadzenia zbioru. |
| `references/engineering-core/04-bazy-i-rag/references/wyszukiwanie-hybrydowe.md` | Łączenie wyszukiwania leksykalnego z wektorowym: BM25, scalanie wyników, przepisywanie zapytania, reranking. |
| `references/engineering-core/04-bazy-i-rag/references/generowanie-i-przypisy.md` | Generowanie odpowiedzi z przypisem sprawdzalnym co do fragmentu i strony oraz odmowa przy braku podstawy w źródle. |
| `references/engineering-core/04-bazy-i-rag/references/ewaluacja.md` | Pomiar jakości wyszukiwania i generowania: zbiór testowy, metryki, sędzia-model i jego pułapki, testy regresyjne. |
| `references/engineering-core/04-bazy-i-rag/references/kiedy-nie-rag.md` | Progi opłacalności rozwiązań tańszych od RAG: długie okno kontekstu, buforowanie promptu, zwykłe wyszukiwanie pełnotekstowe. |

---

## 4. Usługi sieciowe — `05-uslugi-sieciowe`

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-protokoly.md` | Protokoły poczty: sesja SMTP i jej kody odpowiedzi, porty i STARTTLS, IMAP i POP3, budowa MIME, obsługa odbić. |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-uwierzytelnianie.md` | Rekordy uwierzytelniające nadawcę: SPF, DKIM, DMARC, ARC, MTA-STS, TLS-RPT, BIMI — z wymaganiami dużych operatorów. |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-serwer.md` | Własny serwer pocztowy: rachunek kosztów, porównanie zestawów gotowych, wdrożenie krok po kroku, konfiguracja Postfiksa i Dovecota. |
| `references/engineering-core/05-uslugi-sieciowe/references/poczta-transakcyjna.md` | Wysyłka poczty z aplikacji: rozdzielenie ruchu transakcyjnego od marketingowego, porównanie dostawców, warstwa abstrakcji w kodzie. |
| `references/engineering-core/05-uslugi-sieciowe/references/sip-i-telefonia.md` | Telefonia SIP i Asterisk: rejestracja i sygnalizacja, przechodzenie przez NAT, kodeki i pasmo, kolejki, nagrywanie, jakość rozmowy. |
| `references/engineering-core/05-uslugi-sieciowe/references/czas-rzeczywisty.md` | Kanały czasu rzeczywistego: wybór między WebSocket, SSE i WebRTC, podtrzymanie połączenia, ponowne łączenie, skalowanie, TURN. |
| `references/engineering-core/05-uslugi-sieciowe/references/eksploatacja.md` | Eksploatacja usługi sieciowej: TLS i ACME, DNS, odwrotne proxy, kontenery, kopie zapasowe, monitorowanie. |

---

## 5. Integracje PL i UE — `06-integracje-pl-eu`

Obszar zmienia się kilka razy w roku. Każda karta niesie datę stanu i adresy źródeł —
przed wdrożeniem potwierdź stan u źródła, nie w karcie.

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/06-integracje-pl-eu/references/edoreczenia.md` | e-Doręczenia: role uczestników, dowody wysłania i otrzymania, harmonogram obowiązku, wygaszanie ePUAP, interfejsy API i uwierzytelnianie. |
| `references/engineering-core/06-integracje-pl-eu/references/ksef.md` | KSeF: harmonogram z progami, przepisy przejściowe, kary, adresy środowisk, struktura faktury, uwierzytelnianie. |
| `references/engineering-core/06-integracje-pl-eu/references/pisp-psd2.md` | Inicjowanie płatności i dostęp do rachunku: role licencyjne, certyfikaty kwalifikowane, PolishAPI, przebieg z silnym uwierzytelnieniem. |
| `references/engineering-core/06-integracje-pl-eu/references/podpis-elektroniczny.md` | Podpis, pieczęć i znacznik czasu: poziomy zaawansowania, formaty XAdES, PAdES, CAdES i ASiC, walidacja, obowiązki dowodowe. |
| `references/engineering-core/06-integracje-pl-eu/references/platnosci.md` | Bramki płatnicze krajowe: podpisywanie żądań, powiadomienia zwrotne, ponowienia, obowiązki regulaminowe. |
| `references/engineering-core/06-integracje-pl-eu/references/rejestry-api.md` | Rejestry publiczne: adresy, uwierzytelnienie, limity i formaty odpowiedzi oraz wzorzec weryfikacji kontrahenta z buforowaniem. |
| `references/engineering-core/06-integracje-pl-eu/references/tlumaczenie.md` | Tłumaczenie maszynowe w aplikacji: dobór silnika, glosariusze, limity i ceny, ochrona danych i tajemnicy zawodowej. |

---

## 6. Debugowanie, testy, wdrożenia — `07-debug-testy-deploy`

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/07-debug-testy-deploy/references/metoda-debugowania.md` | Droga od objawu do przyczyny przez pomiar: minimalizacja przypadku, połowienie ścieżki, hipotezy falsyfikowalne, narzędzia diagnostyczne. |
| `references/engineering-core/07-debug-testy-deploy/references/testowanie-w-przegladarce.md` | Weryfikacja interfejsu w przeglądarce: procedura samokontroli, Playwright, oczekiwanie na stan zamiast uśpienia, przechwytywanie sieci i konsoli. |
| `references/engineering-core/07-debug-testy-deploy/references/strategia-testow.md` | Zakres i kształt zestawu testów: co testować i czego nie, atrapy i ich nadużycia, testy integracyjne, kontraktowe i migracji. |
| `references/engineering-core/07-debug-testy-deploy/references/obserwowalnosc.md` | Logi, metryki, ślady i alarmy: dane zakazane w logach, korelacja żądań, sygnały złote, kardynalność, OpenTelemetry. |
| `references/engineering-core/07-debug-testy-deploy/references/wdrozenie.md` | Droga od zielonego CI do działającej produkcji: lista kontrolna wydania, migracje bez przestoju, przełączniki funkcji, wdrożenie kroczące i wycofanie. |
| `references/engineering-core/07-debug-testy-deploy/references/awaria.md` | Reakcja na awarię: ocena wagi, podział ról, kolejność przywracania, zbieranie dowodów przed restartem, komunikacja i wnioski. |
| `references/engineering-core/07-debug-testy-deploy/references/wydajnosc-i-profilowanie.md` | Szukanie wąskiego gardła pomiarem: kolejność sprawdzania warstw, profilowanie Node i Pythona, statystyki zapytań, budżety. |

Moduł niesie też dwa narzędzia wykonywalne, przywołane w kartach powyżej:

| Ścieżka | Przeznaczenie |
|---|---|
| `references/engineering-core/07-debug-testy-deploy/scripts/z_serwerem.py` | Uruchamia serwer, czeka na rzeczywistą gotowość HTTP, wykonuje polecenie i sprząta; zastępuje uruchamianie serwera w tle. |
| `references/engineering-core/07-debug-testy-deploy/scripts/kontrola_strony.py` | Przechodzi podane kroki w przeglądarce i zbiera błędy konsoli, wyjątki strony, odpowiedzi o kodzie 400 i wyższym oraz naruszenia dostępności. |

---

## 7. Kontrola przed oddaniem

1. Wczytany został przegląd modułu, nie wszystkie pięć naraz.
2. Karta pogłębiona wczytana wyłącznie wtedy, gdy zadanie jej wymaga.
3. Wersje przywołane w karcie sprawdzone w środowisku projektu, nie przyjęte na słowo.
4. Przy integracjach PL i UE stan potwierdzony u źródła wskazanego w karcie.
