# Frontend — karta

Przeczytaj tę kartę w całości przed napisaniem pierwszego komponentu. Zasady poniżej obowiązują w
każdym projekcie frontendowym Danaco, niezależnie od frameworka. Szczegóły dotyczące konkretnych
frameworków znajdują się w osobnym skillu — tu obowiązują reguły uniwersalne.

## Struktura i komponenty

Dziel interfejs na komponenty według odpowiedzialności, nie według wyglądu. Jeden komponent — jedna
odpowiedzialność: albo pobiera i orkiestruje dane (kontener), albo renderuje przekazane dane
(komponent prezentacyjny). Nie łącz obu ról w jednym pliku, gdy komponent przekracza trywialny
rozmiar.

Stosuj kompozycję zamiast dziedziczenia. Warianty komponentu wyrażaj przez właściwości i sloty
(children), nie przez rozbudowę klasy bazowej ani kopiowanie kodu z drobnymi zmianami.

Utrzymuj granice wiedzy. Komponent prezentacyjny nie zna schematu bazy danych, kształtu odpowiedzi
API ani biblioteki, którą pobrano dane. Przyjmuje zmapowany model widoku i funkcje zwrotne:

```tsx
// ŹLE: komponent zna surowy rekord z bazy
function UserRow({ dbRecord }) {
  return <td>{dbRecord.usr_fst_nm} {dbRecord.usr_lst_nm}</td>;
}

// DOBRZE: komponent przyjmuje model widoku zmapowany w warstwie API
function UserRow({ user }: { user: { fullName: string } }) {
  return <td>{user.fullName}</td>;
}
```

Mapowanie odpowiedzi API na modele widoku wykonuj w jednym miejscu — w warstwie API/adapterach,
nigdy rozproszenie po komponentach. Zmiana kontraktu backendu ma dotykać jednego pliku, nie
dwudziestu.

Ogranicz głębokość przekazywania właściwości. Jeżeli właściwość przechodzi przez więcej niż dwa
poziomy wyłącznie „tranzytem”, zastosuj kompozycję (przekazanie gotowego elementu) lub kontekst —
nie rozbudowuj łańcucha.

## Stan aplikacji

Rozróżniaj trzy rodzaje stanu i traktuj każdy inaczej:

- **Stan lokalny** — otwarcie menu, wartość pola przed wysłaniem, aktywna zakładka. Trzymaj w
  komponencie. Nie wynoś go wyżej, dopóki drugi komponent go realnie nie potrzebuje.
- **Stan współdzielony klienta** — zalogowany użytkownik, motyw, zawartość koszyka. Trzymaj w
  jednym, jawnie wskazanym mechanizmie stanu.
- **Stan serwerowy** — dane pobrane z API. Traktuj jako pamięć podręczną cudzych danych: ma
  właściciela po stronie serwera, wygasa, wymaga odświeżania i inwalidacji.

Jedna biblioteka stanu na projekt. Wybór zapisano w konfiguracji projektu — nie wprowadzaj drugiego
rozwiązania „bo akurat pasuje”. Jeżeli projekt nie ma jeszcze wyboru, zaproponuj jeden mechanizm i
stosuj go konsekwentnie.

Zakaz duplikowania stanu serwera w stanie globalnym bez udokumentowanej potrzeby. Kopiowanie
odpowiedzi API do magazynu globalnego tworzy drugie źródło prawdy, które natychmiast się rozjeżdża.
Dane serwerowe pobieraj i buforuj przez warstwę danych; do magazynu globalnego trafiają wyłącznie
dane, które klient realnie posiada (np. niesynchronizowane ustawienia UI).

Nie przechowuj w stanie wartości wyprowadzalnych. Sumę, filtr, flagę `isValid` licz przy
renderowaniu z danych źródłowych — stan przechowuje fakty, nie wnioski.

## Formularze i walidacja

Walidacja po stronie klienta służy wygodzie użytkownika — nigdy bezpieczeństwu. Serwer waliduje
wszystko niezależnie; frontend jedynie skraca pętlę informacji zwrotnej. Nie pisz komunikatów
sugerujących, że kontrola kliencka jest ostateczna.

Komunikaty o błędach umieszczaj przy polach, których dotyczą, i wiąż je programowo z polem
(etykieta, opis błędu dostępny dla czytnika ekranu). Zbiorczy komunikat na górze formularza stosuj
wyłącznie jako uzupełnienie i dla błędów niedotyczących pojedynczego pola. Pisz, co poprawić, nie
tylko że jest źle: „Podaj datę w formacie DD.MM.RRRR”, nie „Nieprawidłowa wartość”.

Waliduj w momencie sprzyjającym użytkownikowi: pokaż błąd po opuszczeniu pola lub przy wysyłce, a po
pierwszym błędzie waliduj na bieżąco, aby użytkownik widział, kiedy poprawił wartość. Nie krzycz
błędami w polu, którego użytkownik jeszcze nie dotknął.

Każdy widok danych projektuj od razu w czterech stanach: **ładowanie, błąd, pusty, sukces**.
Zaprojektowanie wyłącznie ścieżki sukcesu jest błędem blokującym przegląd kodu w Danaco:

```tsx
if (query.isLoading) return <ListSkeleton />;        // stan ładowania
if (query.isError)   return <ErrorPanel onRetry={query.refetch} />; // błąd z akcją
if (query.data.length === 0) return <EmptyState />;  // stan pusty z podpowiedzią
return <InvoiceList items={query.data} />;           // sukces
```

Podczas wysyłki formularza blokuj powtórne wysłanie i sygnalizuj trwanie operacji. Po błędzie
zachowaj wpisane dane — utrata treści formularza po nieudanej wysyłce jest niedopuszczalna.

## Style

Zasada bezwzględna Danaco: style wyłącznie w plikach i mechanizmach do tego przeznaczonych —
arkuszach, modułach stylów lub warstwie klas narzędziowych przyjętej w projekcie. Zakaz stylów
inline (`style="..."`, obiektowe `style={{...}}`) poza jedynym uzasadnionym wyjątkiem: wartościami
wyliczanymi w czasie działania (np. pozycja elementu przeciąganego, szerokość paska postępu).

Tokeny projektowe są jedynym źródłem prawdy. Kolory, odstępy, promienie, cienie, typografia —
wyłącznie przez zmienne/tokeny, nigdy jako wartości dosłowne w komponencie:

```css
/* ŹLE: magiczne wartości rozproszone po komponentach */
.card { padding: 13px; color: #3b6ef5; }

/* DOBRZE: tokeny jako źródło prawdy */
.card { padding: var(--space-md); color: var(--color-primary); }
```

Warianty wyglądu realizuj przez przełączanie klas, nie przez budowanie CSS w logice komponentu.
Logika decyduje „który stan”, arkusz decyduje „jak ten stan wygląda”:

```tsx
// DOBRZE: logika wybiera klasę, wygląd definiuje arkusz
<span className={isOverdue ? "badge badge--danger" : "badge"}>...</span>
```

Nie nadpisuj stylów cudzych komponentów selektorami sięgającymi w ich wnętrze. Jeżeli komponent
współdzielony nie obsługuje potrzebnego wariantu, rozszerz jego API o wariant — nie obchodź go
selektorem.

## Dostępność i wydajność

Dostępność na poziomie WCAG 2.2 AA jest wymaganiem, nie opcją:

- **Kontrast**: minimum 4,5:1 dla tekstu zwykłego, 3:1 dla dużego tekstu i elementów interfejsu.
- **Fokus**: widoczny wskaźnik fokusu na każdym elemencie interaktywnym; nie usuwaj obrysu bez
  pełnowartościowego zamiennika. Zarządzaj fokusem przy otwieraniu i zamykaniu dialogów.
- **Klawiatura**: każda operacja wykonalna myszą musi być wykonalna klawiaturą, w logicznej
  kolejności tabulacji, bez pułapek fokusu.
- **Alternatywy**: tekst alternatywny obrazów niosących treść (`alt=""` dla dekoracyjnych), etykiety
  wszystkich pól formularza, nazwy dostępne przycisków-ikon.

Używaj elementów semantycznych: `button` dla akcji, `a` dla nawigacji, `nav`, `main`, `table`,
nagłówki w hierarchii bez przeskoków. Atrybuty ARIA stosuj dopiero tam, gdzie semantyka HTML nie
wystarcza — pierwszą regułą ARIA jest jej nieużywanie, gdy istnieje element natywny.

Wydajność mierz metrykami Core Web Vitals i projektuj pod nie od początku:

- **LCP** (Largest Contentful Paint): nie opóźniaj głównej treści; ładuj krytyczne zasoby
  priorytetowo, nie stosuj leniwego ładowania dla obrazu widocznego na starcie.
- **INP** (Interaction to Next Paint): nie blokuj wątku głównego długimi obliczeniami; dziel ciężkie
  operacje, odraczaj pracę niekrytyczną.
- **CLS** (Cumulative Layout Shift): rezerwuj miejsce na treść ładowaną asynchronicznie; każdemu
  obrazowi deklaruj wymiary (`width`/`height` lub `aspect-ratio`), aby układ nie skakał.

Obrazy serwuj w rozmiarze zbliżonym do wyświetlanego (obrazy responsywne), w nowoczesnych formatach,
z leniwym ładowaniem poza pierwszym ekranem. Kod dziel per trasa; nie ładuj całej aplikacji na
stronie logowania.

## Typowe błędy modeli LLM we frontendzie

Poniższe wzorce generuj modele językowe nagminnie. Sprawdź własny kod pod ich kątem przed oddaniem:

1. **Style inline rozsiane po komponentach** — wartości dosłowne w `style={{...}}` zamiast tokenów i
   klas; patrz sekcja „Style”, zasada bezwzględna.
2. **`div` z obsługą kliknięcia zamiast elementów semantycznych** — `div onClick` zamiast `button`,
   `div` zamiast `nav`/`main`/`table`; łamie klawiaturę i czytniki ekranu.
3. **Brak stanów błędu i ładowania** — wygenerowana wyłącznie ścieżka sukcesu; użytkownik przy
   awarii widzi pusty lub zamrożony ekran.
4. **Stan globalny do wszystkiego** — otwarcie modala i wartość pola lądują w magazynie globalnym;
   lokalne trzymaj lokalnie.
5. **Klucze indeksowe w listach** — `key={index}` przy listach modyfikowalnych powoduje błędne
   przypięcie stanu elementów po sortowaniu lub usunięciu; używaj stabilnych identyfikatorów.
6. **Pobieranie danych bezpośrednio w komponencie bez warstwy API** — adresy, nagłówki i mapowanie
   odpowiedzi wklejone w komponent; zmiana kontraktu wymaga edycji wielu plików.
7. **Brak obsługi odmontowania** — aktualizacja stanu po zakończeniu żądania, gdy komponent już nie
   istnieje; anuluj żądania lub ignoruj wynik po odmontowaniu, czyść subskrypcje, interwały i
   nasłuchy zdarzeń.
8. **Duplikowanie danych serwera w stanie klienckim** — ręczna kopia odpowiedzi API w magazynie
   globalnym rozjeżdża się ze źródłem; patrz sekcja „Stan aplikacji”.
9. **Komunikaty walidacji oderwane od pól** — jeden zbiorczy alert zamiast komunikatów przy polach
   powiązanych programowo.
10. **Fałszywa dostępność** — `alt="obrazek"`, puste `aria-label`, `tabindex` większy od zera;
    atrybuty obecne, lecz bezwartościowe. Dostępność weryfikuj klawiaturą i czytnikiem, nie
    obecnością atrybutów.
