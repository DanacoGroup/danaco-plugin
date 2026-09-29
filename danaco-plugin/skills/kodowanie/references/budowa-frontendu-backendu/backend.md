# Backend — karta

Przeczytaj tę kartę w całości przed napisaniem pierwszej trasy. Zasady poniżej obowiązują w każdym
projekcie backendowym Danaco, niezależnie od frameworka i języka. Szczegóły dotyczące konkretnych
frameworków znajdują się w osobnym skillu — tu obowiązują reguły uniwersalne.

## Warstwy i granice

Utrzymuj trzy warstwy o jasno rozdzielonych rolach:

- **Trasy/kontrolery** — przyjmują żądanie, walidują wejście na granicy, wywołują usługę, mapują
  wynik na odpowiedź HTTP. Zero logiki biznesowej.
- **Usługi/logika domenowa** — reguły biznesowe, orkiestracja operacji, decyzje. Nie znają HTTP: nie
  przyjmują obiektu żądania, nie zwracają kodów statusu.
- **Repozytoria/dostęp do danych** — zapytania i utrwalanie. Nie zawierają reguł biznesowych; usługa
  decyduje „co”, repozytorium wykonuje „jak”.

Zależności biegną w jedną stronę: kontroler → usługa → repozytorium. Repozytorium nigdy nie wywołuje
usługi, usługa nigdy nie sięga po obiekt HTTP. Cykl zależności między warstwami traktuj jako błąd
projektowy do natychmiastowej naprawy.

Na granicy systemu wymieniaj DTO, nie encje bazy danych. Encja to wewnętrzny model utrwalania;
odpowiedź API to kontrakt z klientem. Zwracanie encji wprost wycieka schemat bazy, pola wrażliwe i
wiąże klientów z wewnętrzną strukturą:

```python
# ŹLE: encja bazy trafia wprost do odpowiedzi API
return user_entity

# DOBRZE: jawne DTO definiuje kontrakt i nic ponad kontrakt
return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
```

Ta sama zasada dotyczy wejścia: żądanie mapuj na DTO wejściowe z jawną listą pól. Nigdy nie
przypisuj masowo ciała żądania na encję — to prosta droga do nadpisania pól, których klient nie miał
prawa ustawić (mass assignment).

## Kontrakt API

Projektuj kontrakt świadomie i jednolicie w całym serwisie:

- **Ścieżki**: rzeczowniki w liczbie mnogiej, zasoby zagnieżdżone tylko przy realnej zależności
  (`/invoices/{id}/items`), bez czasowników w ścieżce dla operacji CRUD.
- **Metody HTTP zgodnie z semantyką**: GET nie zmienia stanu, POST tworzy lub wykonuje operację, PUT
  zastępuje, PATCH zmienia częściowo, DELETE usuwa. GET z efektem ubocznym jest błędem.
- **Kody odpowiedzi**: 200 dla odczytu, 201 z lokalizacją dla utworzenia, 204 dla operacji bez
  treści, 400 dla wadliwego żądania, 401 dla braku uwierzytelnienia, 403 dla braku uprawnień, 404
  dla braku zasobu, 409 dla konfliktu stanu, 422 dla błędów walidacji treści (jeżeli projekt tak
  rozróżnia — stosuj konsekwentnie), 500 wyłącznie dla awarii serwera.

Format błędów jest jednolity dla całego API — jeden kształt niezależnie od tego, która warstwa
zgłosiła problem:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Żądanie zawiera nieprawidłowe pola.",
    "details": [{ "field": "email", "message": "Podaj poprawny adres e-mail." }]
  }
}
```

Wersjonuj API od pierwszego wydania (np. prefiks `/v1`) i traktuj zmiany łamiące — usunięcie pola,
zmianę typu, zmianę semantyki — jako wymagające nowej wersji lub uzgodnionej ścieżki migracji.
Dodawanie pól opcjonalnych jest zmianą bezpieczną.

Każdą listę stronicuj od początku. Punkt końcowy zwracający kolekcję bez limitu działa do dnia, w
którym tabela urośnie. Zwracaj metadane stronicowania (rozmiar strony, wskaźnik następnej strony lub
liczbę całkowitą) w stałym kształcie; dla dużych, zmiennych zbiorów preferuj stronicowanie kursorem
nad offsetem.

## Walidacja i bezpieczeństwo

Waliduj na granicy systemu — w warstwie tras, zanim dane dotkną logiki. Walidacja frontendowa nie
istnieje z punktu widzenia backendu: każde wejście (ciało, parametry ścieżki i zapytania, nagłówki)
traktuj jako niezaufane. Waliduj typ, zakres, format i reguły biznesowe; odrzucaj pola nieznane
zamiast je ignorować po cichu, jeżeli konwencja projektu na to pozwala.

Rozróżniaj uwierzytelnianie od autoryzacji i egzekwuj oba przy każdej operacji:

- **Uwierzytelnianie** odpowiada na pytanie „kto wywołuje” — sprawdzane na każdym chronionym punkcie
  końcowym.
- **Autoryzacja** odpowiada na pytanie „czy wolno mu wykonać tę operację na tym zasobie” —
  sprawdzana przy każdej operacji, na poziomie zasobu. Samo posiadanie ważnej sesji nie uprawnia do
  cudzej faktury; pominięcie kontroli własności zasobu to podatność klasy IDOR/BOLA — pozycja API1
  „Broken Object Level Authorization” w OWASP API Security Top 10, wydanie 2023 (najnowsze wydanie
  listy dla API; lista ogólna ma wydanie 2025).

Zapytania SQL wyłącznie parametryzowane — przez parametry sterownika lub warstwę ORM. Sklejanie
zapytania z danych wejściowych jest zakazane bez wyjątków:

```python
# ŹLE: wstrzyknięcie SQL
db.execute(f"SELECT * FROM users WHERE email = '{email}'")

# DOBRZE: parametryzacja
db.execute("SELECT * FROM users WHERE email = :email", {"email": email})
```

Sekrety — hasła, klucze API, łańcuchy połączeń — wyłącznie w zmiennych środowiskowych lub magazynie
sekretów. Nigdy w kodzie, plikach konfiguracyjnych w repozytorium ani w dzienniku zdarzeń. W
repozytorium trzymaj wyłącznie przykładowy plik z nazwami zmiennych bez wartości.

Stosuj zasadę najmniejszych uprawnień na każdym poziomie: konto bazodanowe aplikacji bez uprawnień
administracyjnych, tokeny o minimalnym zakresie i ograniczonym czasie życia, dostęp procesów tylko
do zasobów, których wymagają.

## Obsługa błędów i dzienniki

Rozróżniaj wyjątki domenowe od technicznych. Wyjątek domenowy (`InsufficientFundsError`,
`OrderAlreadyShippedError`) to przewidziany rezultat reguły biznesowej — mapuje się na odpowiedź 4xx
ze zrozumiałym komunikatem. Wyjątek techniczny (utrata połączenia, przekroczenie czasu) to awaria —
mapuje się na 5xx bez ujawniania szczegółów wewnętrznych klientowi.

Mapowanie wyjątków na odpowiedzi HTTP wykonuj w jednej warstwie — centralnym module obsługi błędów.
Kontrolery nie zawierają bloków try/catch tłumaczących wyjątki na kody statusu; usługi zgłaszają
wyjątki domenowe i nie wiedzą, co się z nimi dzieje dalej. Jedno miejsce gwarantuje jednolity format
błędów z sekcji „Kontrakt API”.

Nie przechwytuj wyjątku, którego nie obsługujesz. Pusty blok catch oraz catch z samym wpisem do
dziennika i połknięciem błędu ukrywają awarie i produkują ciche uszkodzenia danych. Przechwytuj, gdy
potrafisz zareagować; w przeciwnym razie pozwól wyjątkowi dotrzeć do warstwy mapującej.

Prowadź dziennik zdarzeń strukturalny — pary klucz–wartość zamiast zdań sklejanych z danych — aby
wpisy dały się filtrować i agregować. Loguj na właściwych poziomach: błędy techniczne jako error z
pełnym śladem, odrzucenia domenowe jako warning lub info, przebieg jako debug. Nie zapisuj w
dzienniku danych osobowych, sekretów ani pełnych treści żądań — obowiązek minimalizacji danych
wynika wprost z RODO; identyfikuj rekordy przez identyfikatory, nie przez adresy e-mail czy
nazwiska.

Koreluj żądania: nadaj każdemu żądaniu identyfikator korelacyjny na wejściu (lub przyjmij
przekazany), dołączaj go do każdego wpisu dziennika w obrębie żądania i propaguj w wywołaniach usług
zależnych. Zwracaj go w odpowiedziach błędów, aby zgłoszenie klienta dało się połączyć z zapisem w
dzienniku.

## Dane i transakcje

Każdą operację wielokrokową zmieniającą dane wykonuj w transakcji. Zapis zamówienia, pomniejszenie
stanu magazynowego i wpis rozliczeniowy to jedna jednostka: wszystko albo nic. Sekwencja osobnych
zapisów bez transakcji zostawia dane w stanie niespójnym przy pierwszej awarii w środku sekwencji.

Utrzymuj transakcje krótkie i wolne od operacji zewnętrznych. Wywołanie zdalnego API lub wysyłka
wiadomości wewnątrz otwartej transakcji przetrzymuje blokady i wiąże spójność bazy z dostępnością
cudzego systemu — operacje zewnętrzne wykonuj po zatwierdzeniu, z mechanizmem kompensacji lub
kolejką na wypadek niepowodzenia.

Schemat bazy zmieniaj wyłącznie przez wersjonowane migracje w repozytorium — nigdy ręcznie na
środowisku. Każda migracja jest uporządkowana, powtarzalna i w miarę możliwości odwracalna; migracje
danych oddzielaj od migracji schematu, a zmiany łamiące rozkładaj na kroki bezpieczne dla
działającej aplikacji (najpierw dodaj nowe, przełącz, potem usuń stare).

Dobieraj typy kolumn świadomie: kwoty pieniężne w typie dziesiętnym o stałej precyzji, nigdy
zmiennoprzecinkowym; znaczniki czasu ze strefą lub konsekwentnie w UTC; identyfikatory zewnętrzne
nieodgadywalne, jeżeli trafiają do adresów URL.

Operacje powtarzalne projektuj idempotentnie. Klient ponowi żądanie po przekroczeniu czasu —
obciążenie płatności lub utworzenie zamówienia nie może wykonać się podwójnie. Przyjmuj klucz
idempotentności dla operacji tworzących, wykrywaj powtórzenie i zwracaj wynik pierwotnego wykonania;
wykorzystuj ograniczenia unikalności bazy jako ostateczną zaporę przed duplikatami.

## Typowe błędy modeli LLM w backendzie

Poniższe wzorce generuj modele językowe nagminnie. Sprawdź własny kod pod ich kątem przed oddaniem:

1. **Logika biznesowa w kontrolerach** — reguły, obliczenia i dostęp do danych wprost w funkcji
   trasy; niesprawdzalne jednostkowo i niereużywalne. Kontroler deleguje, usługa decyduje.
2. **Zwracanie encji bazy wprost do API** — wyciek schematu i pól wrażliwych; patrz sekcja „Warstwy
   i granice”.
3. **Catch bez obsługi** — pusty blok lub samo zalogowanie i kontynuacja, jakby błąd nie zaszedł;
   awarie stają się niewidzialne.
4. **Walidacja tylko na froncie** — zaufanie, że klient przysłał dane poprawne; każde pole waliduj
   na granicy backendu.
5. **Zapytania N+1** — pobranie listy, a następnie osobne zapytanie dla każdego elementu w pętli;
   ładuj relacje zapytaniem zbiorczym lub złączeniem.
6. **Brak transakcji dla operacji wielokrokowych** — sekwencja zapisów, z których każdy może się nie
   powieść osobno, bez jednostki atomowej.
7. **Sekrety w kodzie** — klucz API lub hasło bazy wpisane dosłownie „na razie, do testów”; trafiają
   do historii repozytorium na zawsze.
8. **Kody 200 z błędem w treści** — odpowiedź `200 OK` z polem `"success": false`; łamie klientów,
   monitoring i pamięci podręczne. Status HTTP niesie wynik operacji.
9. **Brak kontroli własności zasobu** — sprawdzenie tylko, czy użytkownik jest zalogowany, bez
   sprawdzenia, czy zasób należy do niego.
10. **Brak stronicowania kolekcji** — punkt końcowy zwracający całą tabelę; działa w środowisku
    testowym, zabija produkcyjne.
