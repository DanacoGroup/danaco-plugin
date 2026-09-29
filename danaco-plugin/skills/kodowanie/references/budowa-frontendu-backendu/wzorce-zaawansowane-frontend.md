# Frontend, wzorce zaawansowane — karta ekspercka Danaco Code

Karta rozszerza `references/budowa-frontendu-backendu/frontend.md` o wzorce poziomu zawodowego.
Wczytaj ją, gdy budujesz aplikację z danymi zmiennymi w czasie, formularzami złożonymi, komunikacją
w czasie rzeczywistym albo gdy interfejs ma działać pod realnym obciążeniem i realnymi awariami.
Podstawy z `references/budowa-frontendu-backendu/frontend.md` obowiązują nadal.

## Zarządzanie stanem serwera

Stan serwerowy to pamięć podręczna cudzych danych (patrz
`references/budowa-frontendu-backendu/frontend.md`, sekcja „Stan aplikacji”). Z tej definicji
wynikają obowiązki, które realizuj niezależnie od wybranej biblioteki — biblioteka je ułatwia, nie
zastępuje decyzji:

**Stale-while-revalidate jako wzorzec domyślny.** Pokaż natychmiast dane z pamięci podręcznej,
równolegle odśwież je w tle i podmień po nadejściu świeżych. Pełny ekran ładowania rezerwuj dla
pierwszego wejścia, gdy pamięć podręczna jest pusta. Rozróżniaj w interfejsie „ładuję po raz
pierwszy” (szkielet) od „odświeżam w tle” (dyskretny wskaźnik lub nic) — mylenie ich powoduje
migotanie ekranu przy każdym odświeżeniu.

**Jawna polityka świeżości.** Dla każdego rodzaju danych ustal czas, przez który wynik uznaje się za
świeży i nie ponawia żądania: kursy walut — sekundy; lista faktur — dziesiątki sekund; słownik
krajów — godziny. Politykę zapisz w konfiguracji warstwy danych, nie rozproszoną po komponentach.

**Odświeżanie sterowane zdarzeniami.** Odświeżaj przy powrocie fokusu do okna, przy odzyskaniu
połączenia i po każdej mutacji dotykającej danych. Odpytywanie interwałowe stosuj tylko dla danych
zmieniających się bez udziału użytkownika — i zatrzymuj je, gdy karta przeglądarki jest nieaktywna.

**Deduplikacja żądań.** Dwa komponenty proszące o te same dane w tym samym oknie czasowym generują
jedno żądanie sieciowe. Warunkiem jest wspólny, deterministyczny klucz zapytania budowany z zasobu i
wszystkich parametrów wpływających na wynik: `['invoices', { status: 'overdue', page: 2 }]`. Klucz
niepełny (bez parametru filtru) powoduje serwowanie cudzych wyników z pamięci podręcznej — to
najczęstszy błąd tej warstwy.

**Unieważnianie po mutacji.** Po każdym zapisie unieważnij wszystkie zapytania, których wynik mógł
się zmienić: utworzenie faktury unieważnia listę faktur (we wszystkich wariantach filtrów), licznik
na pulpicie i agregaty raportowe. Unieważniaj po prefiksie klucza (`['invoices']` obejmuje każdy
wariant listy), a mapę „mutacja → unieważniane klucze” trzymaj przy definicji mutacji. Ręczne
dopisywanie rekordu do buforowanej listy zamiast unieważnienia pomija sortowanie, filtry i agregaty
liczone serwerowo — stosuj wyłącznie z uzasadnieniem wydajnościowym.

## Aktualizacje optymistyczne

Aktualizacja optymistyczna pokazuje skutek operacji przed potwierdzeniem serwera. Stosuj ją dla
operacji o wysokim prawdopodobieństwie powodzenia i natychmiastowym oczekiwaniu zwrotnym —
przełączenie flagi, zmiana statusu, dodanie do listy. Nie stosuj jej, gdy wynik zależy od serwera
(cena wyliczana serwerowo, numer nadawany sekwencyjnie) ani dla operacji nieodwracalnych w skutkach.

Przepis obowiązkowy:

1. **Anuluj trwające odświeżenia** zapytań, które zaraz nadpiszesz — inaczej spóźniona odpowiedź
   odczytu przywróci stary stan w trakcie mutacji.
2. **Zachowaj migawkę** obecnych danych z pamięci podręcznej.
3. **Zapisz przewidywany wynik** do pamięci podręcznej; interfejs odzwierciedla zmianę natychmiast.
4. **Wyślij mutację.**
5. **Przy błędzie przywróć migawkę** i pokaż komunikat z możliwością ponowienia. Wycofanie bez
   komunikatu jest zakazane — użytkownik widział skutek i musi wiedzieć, że nie zaszedł.
6. **Po rozstrzygnięciu (sukces i błąd jednakowo) unieważnij** dotknięte zapytania — również po
   sukcesie, bo przewidywany wynik mógł odbiegać od faktycznego.

Pułapki sprawdzane w przeglądzie kodu:

- **Mutacje współbieżne na tych samych danych.** Druga mutacja startująca przed rozstrzygnięciem
  pierwszej robi migawkę zawierającą już optymistyczną zmianę — wycofanie pierwszej przywraca stan
  fałszywy. Kolejkuj mutacje na tym samym zasobie albo przy wycofaniu przelicz stan z ostatniej
  prawdy serwera.
- **Identyfikatory tymczasowe.** Rekord dodany optymistycznie nie ma identyfikatora serwerowego.
  Nadaj tymczasowy i podmień po odpowiedzi; operacje wymagające identyfikatora prawdziwego (edycja,
  usunięcie, nawigacja do szczegółu) blokuj do potwierdzenia.
- **Skutki pochodne.** Optymistyczna zmiana statusu zmienia też liczniki, sumy i pozycję na listach
  filtrowanych. Zwykle słuszniej nie aktualizować ich optymistycznie i pozwolić unieważnieniu je
  poprawić — sekundowa niespójność jest lepsza niż błędna arytmetyka na stałe.

## Formularze złożone

**Walidacja synchroniczna i asynchroniczna to dwie warstwy.** Format, obecność, zakres — sprawdzaj
synchronicznie przy każdej zmianie wartości. Unikalność adresu e-mail czy poprawność numeru
kontrahenta w systemie zewnętrznym — asynchronicznie, po przejściu walidacji synchronicznej (nie
odpytuj serwera o wartość w złym formacie), z debounce 300–500 ms od ostatniego naciśnięcia
klawisza. Sprawdzenie asynchroniczne ma trzy stany widoczne dla użytkownika: trwa, przeszło, nie
przeszło; po przekroczeniu czasu potraktuj wynik jako nieznany i pozostaw rozstrzygnięcie serwerowi
przy wysyłce — „sprawdzam...” nie może zablokować wysyłki na zawsze. Wynik przypisuj do wartości,
której dotyczył: odpowiedź o starej wartości pola odrzuć, inaczej spóźnione „zajęte” przykleja się
do nowej, poprawnej wartości.

**Stan dotknięcia pól.** Prowadź znacznik „dotknięte” (użytkownik wszedł i opuścił pole) i pokazuj
błąd tylko dla pól dotkniętych — zgodnie z `references/budowa-frontendu-backendu/frontend.md`. Przy
próbie wysyłki oznacz wszystkie pola jako dotknięte, pokaż komplet błędów i przenieś fokus na
pierwsze pole z błędem. W formularzach wielokrokowych waliduj krok przy próbie przejścia dalej; przy
powrocie zachowaj wartości i stan dotknięcia.

**Zapis roboczy.** Formularz, którego wypełnienie kosztuje więcej niż minutę, chroni pracę
użytkownika: zapisuj kopię roboczą automatycznie z debounce 1–2 s, sygnalizuj dyskretnie „zapisano
szkic”, a przy powrocie zaproponuj przywrócenie — decyzję podejmuje użytkownik, nie aplikacja po
cichu. Kopię usuwaj po pomyślnej wysyłce. Do kopii lokalnej nie zapisuj pól wrażliwych (hasła,
numery kart) — przechowanie ich w magazynie przeglądarki jest błędem bezpieczeństwa.

**Brudny formularz.** Śledź, czy formularz różni się od stanu początkowego, i ostrzegaj przed
opuszczeniem widoku z niezapisanymi zmianami. Porównuj z wartościami początkowymi, nie flagą
ustawianą przy pierwszym naciśnięciu klawisza: ręczne cofnięcie zmian ma gasić ostrzeżenie.

## Praca w czasie rzeczywistym

Wybieraj kanał świadomie: **SSE** wystarcza, gdy dane płyną wyłącznie z serwera do klienta
(powiadomienia, postęp zadania) — jest prostsze i ma wbudowane wznawianie. **WebSocket** stosuj, gdy
klient wysyła dane tym samym kanałem z niskim opóźnieniem (czat, edycja wspólna). Nie otwieraj
WebSocketu tam, gdzie wystarczy SSE albo odświeżanie po mutacji.

**Ponowne łączenie z odczekaniem wykładniczym.** Po zerwaniu wznawiaj z rosnącym odstępem (1 s, 2 s,
4 s... do pułapu 30 s) i losowym rozrzutem (jitter) — bez rozrzutu wszyscy klienci odłączeni awarią
serwera wrócą w tej samej sekundzie i położą go ponownie. Licznik prób zeruj po połączeniu
utrzymanym stabilnie, nie po samym nawiązaniu. Po zdarzeniu online przeglądarki łącz natychmiast,
bez odsiadywania bieżącego odstępu.

**Kolejkowanie w rozłączeniu.** Działania wykonane bez połączenia kolejkuj lokalnie i oznaczaj w
interfejsie jako oczekujące — użytkownik musi widzieć różnicę między „wysłane” a „wyśle się po
powrocie sieci”. Ustal górny limit kolejki i zachowanie po przekroczeniu (blokada akcji z
komunikatem, nie ciche porzucanie). Każdemu komunikatowi nadaj identyfikator klienta, aby serwer
rozpoznał duplikat wysłany tuż przed zerwaniem i ponownie po wznowieniu.

**Uzgadnianie stanu po powrocie.** Zdarzenia z czasu rozłączenia przepadły — samo wznowienie kanału
ich nie odtwarza. Po połączeniu wykonaj pełne odświeżenie danych widoku (unieważnij zapytania stanu
serwerowego) albo pobierz zaległości od ostatniego potwierdzonego znacznika, jeżeli serwer to
wspiera. Kolejność obowiązkowa: najpierw uzgodnij stan, potem wyślij kolejkę lokalną, na końcu wznów
przetwarzanie zdarzeń bieżących.

## Wydajność renderowania

**Memoizacja z umiarem i pomiarem.** Memoizuj po stwierdzeniu problemu profilerem, nie prewencyjnie
— memoizacja ma koszt (pamięć, porównania) i zaciemnia kod. Kolejność: zmierz, zawęź stan (przenieś
go w dół drzewa, aby zmiana nie renderowała całej gałęzi), dopiero potem memoizuj komponenty
faktycznie drogie. Memoizacja nie działa, gdy właściwości tworzone są od nowa przy każdym renderze
rodzica (świeży literał obiektu, świeża funkcja) — ustabilizuj wejścia albo odpuść.

**Wirtualizacja długich list.** Listę powyżej kilkuset wierszy renderuj oknem: elementy widoczne
plus margines. Wirtualizacja wyklucza wyszukiwanie przeglądarki w treści listy i wymaga poprawnej
obsługi klawiatury oraz ról ARIA — koszt akceptuj świadomie, gdy rozmiar listy realnie dławi render;
dla krótszych list paginacja bywa lepsza i prostsza.

**Podział paczek po trasach.** Dziel kod per trasa (patrz
`references/budowa-frontendu-backendu/frontend.md`); dodatkowo wydzielaj ciężkie zależności używane
w jednym miejscu — edytor tekstu, bibliotekę wykresów, podgląd PDF — i ładuj przy użyciu, z
widocznym stanem ładowania. Ustal budżet rozmiaru paczki wejściowej i pilnuj go w CI; przekroczenie
blokuje scalenie jak czerwony test.

**Obrazy.** Serwuj w rozmiarze zbliżonym do wyświetlanego (`srcset`/`sizes`), w formatach
nowoczesnych (AVIF/WebP z awaryjnym JPEG/PNG), z zadeklarowanymi wymiarami przeciw skokom układu.
Priorytety jawnie: obraz LCP z priorytetem wysokim i bez leniwego ładowania; wszystko poza pierwszym
ekranem — leniwie. Logotypy i ikony jako SVG, nie rastry.

## Obsługa błędów warstwowo

Buduj trzy niezależne linie obrony:

1. **Granice błędów wokół fragmentów widoku.** Otaczaj granicą błędu każdy niezależny region
   interfejsu (panel, widget, sekcję), nie tylko całą aplikację. Awaria renderowania wykresu nie
   może zdjąć całego pulpitu — region pokazuje komunikat z akcją ponowienia, reszta działa. Granica
   najwyższego poziomu jest ostatnią deską ratunku, nie podstawowym mechanizmem.
2. **Degradacja łagodna przy braku danych.** Gdy fragment danych jest niedostępny, pokaż to, co
   masz: lista główna z informacją „nie udało się wczytać podsumowania — ponów”, nie pusty ekran.
   Rozróżniaj dane krytyczne dla widoku (bez nich pokaż stan błędu całego widoku) od uzupełniających
   (pokaż widok bez nich, z oznaczeniem braku). Klasyfikację przeprowadź projektując widok, nie w
   trakcie awarii.
3. **Rozróżnienie rodzajów błędów w komunikatach.** Błąd walidacji — komunikat przy polu; brak
   uprawnień — wyjaśnienie bez sugerowania ponowienia; błąd sieci — ponowienie (automatyczne z
   odczekaniem dla odczytów, ręczne dla mutacji); awaria serwera — komunikat z identyfikatorem
   korelacyjnym z odpowiedzi błędu (patrz karta backendowa), który użytkownik poda w zgłoszeniu.

## Internacjonalizacja i formatowanie

Formatuj daty, liczby i waluty wyłącznie przez `Intl` — `Intl.DateTimeFormat`, `Intl.NumberFormat`
(z `style: 'currency'`), `Intl.RelativeTimeFormat` — nigdy przez ręczne sklejanie łańcuchów. Ręczne
wstawianie separatora tysięcy czy porządku daty jest zawsze błędne dla części ustawień regionalnych:

```ts
// ŹLE: format przyklejony do jednego rynku
const label = `${amount.toFixed(2)} zł`;

// DOBRZE: Intl formatuje według ustawień regionalnych
const label = new Intl.NumberFormat(locale, { style: "currency", currency: "PLN" }).format(amount);
```

Teksty interfejsu trzymaj poza kodem komponentów — w plikach zasobów z kluczami — nawet w projekcie
jednojęzycznym: wymusza to spójność terminologii i umożliwia korektę bez dotykania logiki. Nie
składaj zdań z fragmentów (`"Usunięto " + n + " plików"`) — odmiana liczebników różni się między
językami; używaj mechanizmu form liczby mnogiej (`Intl.PluralRules` lub odpowiednik biblioteki i18n)
i interpolacji nazwanych parametrów. Daty przesyłaj przez kontrakt API w ISO 8601 z jawną strefą
(zwykle UTC), formatuj dopiero na brzegu widoku i nigdy nie przechowuj w stanie dat już
sformatowanych.

## Telemetria frontendu

Frontend bez telemetrii to system, o którego awariach wiedzą tylko użytkownicy. Minimum zawodowe:

- **Błędy nieprzechwycone**: nasłuch zdarzenia `error` okna oraz — osobno, bo to inny kanał —
  `unhandledrejection` dla odrzuconych obietnic bez obsługi. Wysyłaj komunikat, ślad stosu, adres
  widoku, wersję aplikacji i identyfikator sesji; bez wersji nie odróżnisz błędów naprawionych od
  nowych.
- **Błędy przechwycone przez granice błędów**: raportuj je również — granica, która pokazała
  komunikat i nic nie zaraportowała, ukrywa awarie przed zespołem.
- **Web Vitals w polu**: zbieraj LCP, INP i CLS od rzeczywistych użytkowników i analizuj percentyl
  75., nie średnią — pomiar laboratoryjny nie widzi realnych urządzeń i sieci.
- **Higiena danych**: nie wysyłaj danych osobowych ani treści wprowadzanych przez użytkownika
  (minimalizacja danych — jak w dziennikach backendu); próbkuj i deduplikuj powtarzający się błąd,
  aby awaria masowa nie zalała punktu zbiorczego; wysyłaj przez `navigator.sendBeacon` lub `fetch` z
  `keepalive`, aby raporty nie ginęły przy zamknięciu strony.

Telemetria jest częścią definicji ukończenia: funkcja bez raportowania błędów i pomiaru w polu nie
jest gotowa do wydania.
