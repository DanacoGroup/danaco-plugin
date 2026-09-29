# Język zawodowy treści trwałych

Karta normuje język wszystkich treści trwałych projektu: komunikatów rewizji Git,
komunikatów o błędach, wpisów dziennika zdarzeń, nazw identyfikatorów oraz
dokumentacji. Treść trwała to każdy tekst, który przeżyje sesję pracy — stosuj
wobec niego rygor języka formalnego bez wyjątków.

## 1. Komunikat rewizji Git — anatomia

Budowa komunikatu:

1. **Wiersz podsumowania** — tryb oznajmujący, do ~72 znaków, bez kropki na końcu;
   nazywa skutek zmiany, nie czynność autora. Test poprawności: wiersz musi sensownie
   dopełniać zdanie „Po przyjęciu tej rewizji system…” / „Ta rewizja…”.
2. **Wiersz pusty.**
3. **Uzasadnienie** — akapit odpowiadający na pytania: dlaczego zmiana była potrzebna,
   dlaczego wybrano to rozwiązanie, jakie warianty odrzucono i czemu. Diff pokazuje
   „co”; komunikat ma przekazać „dlaczego”. Uzasadnienie pomiń tylko przy zmianach
   samoobjaśniających się (literówka, aktualizacja wersji zależności).
4. **Odwołania** — numer zgłoszenia w składni przyjętej w projekcie (np. `Zamyka #142`).

Konwencję szczegółową (Conventional Commits: `fix:`, `feat:`) stosuj wtedy i tylko
wtedy, gdy projekt już ją stosuje — sprawdź w `git log --oneline -20` przed
pierwszą rewizją.

Przykłady na realnych scenariuszach:

| Źle | Dlaczego źle | Dobrze |
|---|---|---|
| `poprawki` | Nie nazywa żadnej zmiany; historia staje się nieprzeszukiwalna. | `Napraw zaokrąglanie kwoty VAT przy pozycjach z rabatem` |
| `Naprawiłem błąd o którym rozmawialiśmy` | Odwołanie do rozmowy nieistniejącej dla czytelnika; brak treści merytorycznej. | `Napraw utratę rabatu przy scalaniu pozycji faktury` + akapit z mechanizmem błędu i `Zamyka #142` |
| `WIP / dalsze zmiany w module raportów 15.08` | Data dubluje metadane Gita; „dalsze zmiany” nie znaczy nic. | `Dodaj filtrowanie raportu sprzedaży po oddziale` |
| `fix: różne poprawki + refaktoryzacja + nowy endpoint` | Trzy niezależne zmiany w jednej rewizji — nieprzeglądalne, niecofalne osobno. | Trzy rewizje: `Napraw…`, `Uporządkuj…`, `Dodaj punkt końcowy…` |
| `Zaktualizowano plik utils.py` | Opisuje czynność na pliku, nie skutek dla systemu; to widać w diffie. | `Ujednolić strefę czasową znaczników eksportu do UTC` |

Uzasadnienie wzorcowe (treść po wierszu pustym):

```
Napraw utratę rabatu przy scalaniu pozycji faktury

Funkcja scalająca duplikaty pozycji sumowała kwoty brutto, pomijając
pole rabatu — scalona pozycja przyjmowała rabat pierwszej z pozycji
źródłowych. Scalanie operuje teraz na kwotach po rabacie, a test
odtwarza przypadek z dwoma różnymi rabatami.

Zamyka #142
```

## 2. Komunikat o błędzie — anatomia

Komunikat o błędzie ma dwóch różnych odbiorców i dwie różne wersje.

**Dla użytkownika końcowego** — trzy człony: co się stało (językiem dziedziny,
nie techniki), w jakim kontekście, co użytkownik może zrobić. Bez śladów stosu,
bez nazw wyjątków, bez obwiniania użytkownika.

**Dla operatora (dziennik zdarzeń)** — pełen kontekst techniczny: operacja,
identyfikatory obiektów, przyczyna pierwotna, parametry istotne dla diagnozy.

Pary złe → dobre:

| Źle | Dobrze (użytkownik) | Dobrze (dziennik) |
|---|---|---|
| `Błąd!` / `Coś poszło nie tak :(` | `Nie można zapisać faktury: numer FV/2026/08/031 już istnieje. Odśwież listę faktur — dokument mógł zostać zapisany w innej sesji.` | `Zapis faktury odrzucony: naruszenie unikalności numeru (SQLSTATE 23505), numer=FV/2026/08/031, uzytkownik_id=84, oddzial=WRO` |
| `Exception: [Errno 13] Permission denied: 'C:\\ProgramData\\Danaco\\config.json'` (pokazane użytkownikowi) | `Nie można zapisać ustawień: program nie ma uprawnień do katalogu C:\ProgramData\Danaco. Uruchom program jako administrator albo zgłoś się do działu IT.` | `Zapis konfiguracji nieudany: PermissionError (Errno 13), sciezka=C:\ProgramData\Danaco\config.json, uzytkownik systemowy=biuro03` |
| `Nieprawidłowe dane.` | `Nie można wysłać formularza: numer NIP 5261040567 ma nieprawidłową sumę kontrolną. Sprawdź, czy wszystkie cyfry przepisano poprawnie.` | `Walidacja formularza kontrahenta odrzucona: pole=nip, wartosc_dlugosc=10, przyczyna=suma kontrolna` |
| `Wystąpił błąd połączenia. Spróbuj ponownie.` (przy każdej awarii) | `Nie można pobrać kursów walut: serwis NBP nie odpowiada. Faktura zostanie zapisana jako robocza; kurs uzupełnij po przywróceniu połączenia.` | `Pobranie kursu NBP nieudane: timeout po 10 s, url=https://api.nbp.pl/api/exchangerates/..., proba=3/3` |

Zasady przekrojowe: komunikat pisz w trybie oznajmującym lub rozkazującym, bez
wykrzykników; wskazuj obiekt po identyfikatorze dziedzinowym (numer faktury,
login), nie po kluczu technicznym, chyba że odbiorcą jest operator; nigdy nie
sugeruj czynności niemożliwej dla odbiorcy („skontaktuj się z administratorem”
tylko wtedy, gdy istnieje ścieżka takiego kontaktu).

## 3. Wpisy dziennika zdarzeń

**Poziomy** — stosuj rozłącznie:

- `ERROR` — operacja zakończona niepowodzeniem, wymagana reakcja lub wiedza operatora.
- `WARNING` — operacja wykonana, lecz w warunkach nietypowych (ponowienie, wartość
  domyślna zamiast brakującej, zbliżanie się do limitu).
- `INFO` — zdarzenia cyklu życia i operacje dziedzinowe istotne dla audytu
  (uruchomienie usługi, zakończenie importu z bilansem, zmiana konfiguracji).
- `DEBUG` — szczegóły diagnostyczne; nigdy nie wymagane do zrozumienia przebiegu
  na poziomie INFO.

Nadużycia zakazane: `ERROR` dla stanów obsłużonych poprawnie (walidacja odrzucająca
błędny formularz to `INFO`/`WARNING`, nie `ERROR`), `INFO` w pętli po każdym rekordzie
(zaleje dziennik; loguj bilans po zakończeniu partii).

**Struktura wpisu**: czasownik dziedzinowy + obiekt + identyfikatory + parametry
diagnostyczne w formie klucz=wartość. Wartości zmienne przekazuj przez parametry
mechanizmu logowania, nie przez sklejanie napisów:

```python
log.info("Zakończono import wyciągu: plik=%s, pozycje=%d, odrzucone=%d",
         path.name, imported, rejected)
```

**Zakaz danych osobowych i sekretów.** Do dziennika nie trafiają: imiona i nazwiska,
adresy e-mail, numery PESEL, numery kart, hasła, tokeny, pełne treści dokumentów.
Obiekt wskazuj identyfikatorem technicznym lub dziedzinowym (`klient_id=1204`,
`faktura=FV/2026/08/031`). Jeżeli identyfikator dziedzinowy sam jest daną osobową
(login będący adresem e-mail) — loguj identyfikator techniczny. Wyjątki od tej
zasady wymagają jawnej decyzji właściciela projektu, odnotowanej w dokumentacji.

## 4. Nazewnictwo — jak wybrać nazwę

**Test odwrotny**: nazwa jest dobra, jeżeli czytelnik znający dziedzinę potrafi
z samej nazwy odtworzyć odpowiedzialność elementu — bez zaglądania do wnętrza.
`retry_failed_exports` przechodzi test; `process_data2`, `handle_stuff`, `do_export`
— nie. Wykonuj test przy każdej nowej nazwie funkcji, klasy, modułu i tabeli.

Reguły wyboru:

- **Funkcja** — czasownik + dopełnienie: `calculate_gross_amount`, `send_reminder`.
  Funkcja zwracająca wartość logiczną — predykat: `is_overdue`, `has_active_contract`.
- **Klasa, moduł, tabela** — rzeczownik dziedzinowy: `InvoiceMerger`, `exchange_rates`.
- **Zmienna** — nazwa treści, nie typu: `overdue_invoices`, nie `invoice_list`;
  `retry_limit`, nie `number`. Skróty jednoliterowe wyłącznie jako konwencjonalne
  liczniki pętli o zasięgu kilku linii.
- **Symetria par**: `open/close`, `acquire/release`, `create/delete` — nie
  `open/destroy`. Złamanie symetrii sugeruje asymetrię zachowania, której nie ma.
- **Jednostki i układy w nazwie**, gdy typ ich nie niesie: `timeout_seconds`,
  `attachment_max_bytes`, `issued_at_utc`.
- **Zakres znaczeniowy zgodny z zawartością**: funkcja `validate_invoice`, która
  dodatkowo zapisuje fakturę, ma nazwę kłamiącą — rozdziel albo przemianuj na
  nazwę pełną (`validate_and_store_invoice`), a docelowo rozdziel.
- **Negacje**: unikaj nazw przeczących w flagach (`disable_checks=False` zmusza
  do podwójnej negacji); nazywaj stan pozytywny: `checks_enabled=True`.

## 5. Słownik par pojęć mylonych

Rozstrzygnięcia stosuj konsekwentnie w kodzie, dokumentacji i komunikatach:

| Para | Rozstrzygnięcie |
|---|---|
| walidacja / weryfikacja | **Walidacja** — sprawdzenie zgodności danych z regułami formalnymi (format NIP, zakres daty, wymagalność pola). **Weryfikacja** — potwierdzenie zgodności ze stanem faktycznym lub wymaganiem (weryfikacja konta w rejestrze VAT, weryfikacja poprawki uruchomieniem testów). Formularz się waliduje; kontrahenta w białej liście się weryfikuje. |
| uwierzytelnianie / autoryzacja | **Uwierzytelnianie** (authentication) — ustalenie tożsamości: kto się łączy (hasło, token, certyfikat). **Autoryzacja** (authorization) — ustalenie uprawnień: co wolno już ustalonej tożsamości. HTTP 401 dotyczy uwierzytelnienia, HTTP 403 — autoryzacji. „Autoryzacja logowania” to błąd terminologiczny. |
| parametr / argument | **Parametr** — nazwa w definicji funkcji. **Argument** — wartość przekazana w wywołaniu. Komunikat „nieprawidłowy argument `limit=-5`” jest poprawny; „funkcja przyjmuje trzy argumenty” w opisie definicji — niepoprawny (przyjmuje trzy parametry). |
| błąd / usterka / awaria | **Usterka** (defect/bug) — wada w kodzie. **Błąd** (error) — nieprawidłowy stan w działaniu, zwykle skutek usterki lub złych danych. **Awaria** (failure/outage) — niezdolność systemu do świadczenia usługi. Usterkę się naprawia, błąd obsługuje, awarię usuwa się i opisuje w raporcie poincydentalnym. |
| wydajność / skalowalność | **Wydajność** — zachowanie przy bieżącym obciążeniu (czas odpowiedzi, przepustowość). **Skalowalność** — zmiana wydajności wraz ze wzrostem obciążenia lub zasobów. System może być wydajny i nieskalowalny. |
| współbieżność / równoległość | **Współbieżność** — struktura programu obsługująca wiele zadań w przeplocie (async, wątki). **Równoległość** — jednoczesne wykonanie na wielu jednostkach obliczeniowych. Serwer FastAPI jest współbieżny na jednym procesie; równoległość dają dopiero procesy robocze. |
| migracja / aktualizacja | **Migracja** — kontrolowana zmiana schematu lub przeniesienie danych między strukturami (skrypt migracyjny bazy). **Aktualizacja** — podniesienie wersji oprogramowania lub zależności. Aktualizacja bywa przyczyną migracji; nie są synonimami. |
| idempotentny / deterministyczny | **Idempotentna** operacja — wielokrotne wykonanie daje ten sam skutek co jednokrotne (ponowienie bezpieczne). **Deterministyczna** — ten sam wynik dla tych samych danych wejściowych. `DELETE` po identyfikatorze jest idempotentny; losowanie nie jest deterministyczne, choć bywa idempotentne w skutkach. |
| szyfrowanie / haszowanie | **Szyfrowanie** — odwracalne, z kluczem (dane w spoczynku, transmisja). **Haszowanie** — nieodwracalne (hasła, sumy kontrolne). „Szyfrowanie haseł” w dokumentacji to błąd — hasła się haszuje z solą. |

Napotkawszy w projekcie parę użytą wbrew rozstrzygnięciu, nie mieszaj dwóch
konwencji: w nowym kodzie stosuj rozstrzygnięcie, a rozjazd zastany zgłoś
właścicielowi jako usterkę terminologiczną.

## 6. Pisanie po polsku w kodzie mieszanym

Standard Danaco dla projektów z polską dokumentacją:

- **Identyfikatory** (zmienne, funkcje, klasy, tabele, kolumny, punkty końcowe API)
  — po angielsku, zgodnie z konwencją języka programowania. Wyjątek: projekt zastany
  konsekwentnie stosuje identyfikatory polskie — wtedy podporządkuj się zastanej
  konwencji; nie wprowadzaj drugiej.
- **Terminy dziedzinowe bez ustalonego odpowiednika angielskiego** w identyfikatorach
  zapisuj po polsku bez diakrytyków, konsekwentnie w całym projekcie (np. kolumna
  `nip`, `regon`, `krs` — nie tłumacz na opisowe nazwy angielskie, których nikt
  w dziedzinie nie rozpozna).
- **Komentarze i dokumentacja** — po polsku, z pełnymi znakami diakrytycznymi
  (kodowanie UTF-8 jest standardem; zapis „bez ogonków” jest nieprofesjonalny),
  poprawną interpunkcją i odmianą. Jeden plik = jeden język komentarzy.
- **Komunikaty dla użytkownika** — po polsku; **wpisy dziennika i komunikaty
  wewnętrzne** — w języku przyjętym w projekcie (sprawdź istniejące wpisy zanim
  napiszesz pierwszy własny); nie mieszaj języków w obrębie jednego strumienia.
- **Odmiana terminów angielskich w tekście polskim** — odmieniaj z apostrofem
  wyłącznie tam, gdzie wymaga tego wymowa (`commit` → `commita` bez apostrofu;
  `cache` → `cache'a`); w dokumentacji przedkładaj polski termin zawodowy nad
  zapożyczenie, jeżeli jest przyjęty: rewizja, scalenie, gałąź, wdrożenie —
  z terminem angielskim w nawiasie przy pierwszym użyciu, gdy słownictwo czytelnika
  może być angielskie.
- **Format daty i liczb w treściach trwałych** — daty w ISO 8601 (`2026-08-16`)
  w danych i dziennikach; w tekście dla użytkownika format polski (`16 sierpnia 2026`).
  Separator dziesiętny: kropka w kodzie i danych, przecinek w tekście polskim
  dla użytkownika.

Test końcowy karty: przeczytaj każdą napisaną treść trwałą głosem obcego
inżyniera, który zna dziedzinę, lecz nie zna przebiegu prac. Jeżeli czegoś
nie zrozumie albo poczuje, że czyta notatkę prywatną — treść wymaga poprawy.
