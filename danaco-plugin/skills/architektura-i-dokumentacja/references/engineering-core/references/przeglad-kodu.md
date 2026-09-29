# Przegląd kodu — karta

Karta obejmuje przegląd w ujęciu architektonicznym: granice modułów, kontrakty, dług
techniczny. Procedurę przeglądu zmiany przed scaleniem prowadzi
`../kontrola-jakosci/references/przeglad-kodu/przeglad-kodu.md`.

Przegląd ma jeden cel: wyłapać to, czego nie wyłapią kompilator, linter i testy.
Wszystko, co da się zautomatyzować, ma być zautomatyzowane — uwaga o formatowaniu
w przeglądzie oznacza, że w repozytorium brakuje formattera.

## Kolejność ważności

Przechodź warstwy w tej kolejności i **nie schodź niżej, dopóki wyższa nie jest czysta**.
Uwaga o nazewnictwie zmiennej w kodzie, który ma warunek wyścigu, marnuje uwagę
recenzenta i autora.

| Priorytet | Warstwa | Pytanie |
| --- | --- | --- |
| 1 | Poprawność | Czy robi to, co miało robić — także dla wejść nietypowych? |
| 2 | Bezpieczeństwo | Czy da się tego użyć do uzyskania czegoś, do czego się nie ma prawa? |
| 3 | Zachowanie przy awarii | Co się dzieje, gdy zewnętrzna zależność nie odpowie albo proces padnie w połowie? |
| 4 | Wydajność | Czy koszt rośnie liniowo z danymi, czy szybciej? |
| 5 | Granice i struktura | Czy zmiana jest w warstwie, do której należy? |
| 6 | Czytelność | Czy zrozumie to ktoś, kto tego nie pisał, za pół roku? |
| 7 | Testy | Czy test faktycznie sprawdza zachowanie, czy tylko implementację? |

## Procedura przeglądu

1. **Przeczytaj opis zmiany i powiąż go z diffem.** Zmiany niewymienione w opisie są
   podejrzane: albo opis jest niepełny, albo zmiana jest przypadkowa.
2. **Sprawdź rozmiar.** Powyżej ~400 zmienionych linii jakość przeglądu gwałtownie
   spada. Poproś o podział — to uzasadniona uwaga, nie unik.
3. **Przejdź diff pod kątem warstwy 1–2** (poprawność, bezpieczeństwo). Nic innego.
4. **Wyjdź poza diff.** Znajdź wszystkie wywołania zmienionych funkcji. Najgroźniejsze
   błędy nie są w diffie, tylko w miejscach, które diff cicho zmienił.
5. **Sprawdź testy.** Czy istnieje test, który **nie przechodziłby** przed tą zmianą?
   Jeśli nie, zmiana nie jest przetestowana, choćby pokrycie rosło.
6. **Dopiero teraz warstwy 3–7.**
7. **Sformułuj werdykt.** Jasny: zatwierdzam / zatwierdzam z uwagami / wymaga zmian.

## Katalog usterek

Kolejność odpowiada częstości występowania w realnym kodzie pisanym szybko.

### 1. Warunek wyścigu przy sprawdź-i-działaj

Najczęstsza usterka współbieżności. Sprawdzenie i działanie w dwóch operacjach.

```typescript
// USTERKA
const istnieje = await db.uzytkownik.findUnique({ where: { email } });
if (istnieje) throw new EmailZajety();
await db.uzytkownik.create({ data: { email, hasloHash } });
```

Dwa równoległe żądania z tym samym e-mailem przechodzą oba sprawdzenie i tworzą dwa
konta. Testy tego nie wykryją — wymaga jednoczesności.

```typescript
// POPRAWKA: ograniczenie w bazie jest jedynym prawdziwym sprawdzeniem
try {
  await db.uzytkownik.create({ data: { email, hasloHash } });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === 'P2002') {
    throw new EmailZajety();
  }
  throw e;
}
```

Warianty tej samej usterki: sprawdzenie salda przed pobraniem, sprawdzenie limitu przed
zapisem, sprawdzenie dostępności przed rezerwacją. **Reguła: unikalność i limity
egzekwuje baza (`UNIQUE`, `CHECK`, `SELECT ... FOR UPDATE`), nie odczyt w aplikacji.**

### 2. Utracona aktualizacja przy odczyt-modyfikuj-zapis

```python
# USTERKA
konto = await repo.pobierz(konto_id)
konto.saldo_grosze -= kwota
await repo.zapisz(konto)
```

Dwie równoległe operacje odczytują to samo saldo; druga nadpisuje wynik pierwszej.
Pieniądze znikają.

```sql
-- POPRAWKA A: operacja atomowa w bazie
UPDATE konta
SET saldo_grosze = saldo_grosze - $2
WHERE id = $1 AND saldo_grosze >= $2
RETURNING saldo_grosze;
-- 0 wierszy = niewystarczające środki
```

```python
# POPRAWKA B: blokada optymistyczna z kolumną wersji
UPDATE konta SET saldo_grosze = $2, wersja = wersja + 1
WHERE id = $1 AND wersja = $3
# 0 wierszy = ktoś zmienił w międzyczasie → ponów lub zgłoś konflikt
```

Szukaj wzorca: odczyt encji → zmiana pola → zapis całej encji. W kodzie z ORM-em
występuje domyślnie i prawie nikt nie dodaje kolumny wersji.

### 3. N+1 zapytań

```typescript
// USTERKA
const zgloszenia = await db.zgloszenie.findMany({ where: { klientId } });
for (const z of zgloszenia) {
  z.klient = await db.klient.findUnique({ where: { id: z.klientId } });
}
```

50 zgłoszeń = 51 zapytań. Na środowisku deweloperskim z 5 rekordami niewidoczne.

```typescript
// POPRAWKA
const zgloszenia = await db.zgloszenie.findMany({
  where: { klientId },
  include: { klient: true },
});
```

Postacie ukryte, których szuka się trudniej:
- Leniwe ładowanie relacji w pętli renderującej (widoczne dopiero w logu SQL).
- `await` wewnątrz `for` tam, gdzie operacje są niezależne → `Promise.all` z limitem
  współbieżności.
- Resolver GraphQL bez dataloadera.
- Serializacja, która dotyka relacji nieza ładowanych wcześniej.

**Metoda wykrywania w przeglądzie**: znajdź każdą pętlę i sprawdź, czy w jej ciele jest
`await` albo dostęp do relacji. Jeśli tak, policz, ile zapytań to daje przy 1000 elementach.

### 4. Zapytanie bez ograniczenia

```python
# USTERKA
zgloszenia = await repo.wszystkie_dla_klienta(klient_id)
return [do_dto(z) for z in zgloszenia]
```

Działa dwa lata, aż jeden klient uzbiera 300 tys. zgłoszeń i proces zabija OOM.

Reguła: **każde zapytanie zwracające zbiór ma `LIMIT`.** Brak limitu jest dopuszczalny
tylko dla tabel o wiadomym, ograniczonym rozmiarze (słowniki, konfiguracja) — i wtedy
warto to zaznaczyć komentarzem.

Ten sam błąd w innych postaciach: `readFile` na pliku o nieznanym rozmiarze, `JSON.parse`
odpowiedzi zewnętrznego API bez limitu, wczytanie całego CSV do pamięci zamiast
strumieniowania.

### 5. Nieobsłużony błąd i błąd połknięty

```typescript
// USTERKA A: połknięcie
try {
  await wyslijPowiadomienie(uzytkownik);
} catch (e) {
  console.log('nie udało się');   // nic nie wiadomo, nic nie ponowione
}

// USTERKA B: opakowanie gubiące przyczynę
catch (e) {
  throw new Error('Błąd zapisu');  // stos i przyczyna przepadły
}

// USTERKA C: obietnica bez await
zapiszAudyt(zdarzenie);            // odrzucenie ląduje w unhandledRejection
```

```typescript
// POPRAWKA
try {
  await wyslijPowiadomienie(uzytkownik);
} catch (e) {
  log.error({ err: e, uzytkownikId: uzytkownik.id }, 'wysyłka powiadomienia nieudana');
  await outbox.zaplanujPonowienie('powiadomienie', uzytkownik.id);
}
```

Sprawdzaj w przeglądzie:
- Czy każdy `catch` albo obsługuje, albo przekazuje dalej z zachowaniem przyczyny
  (`new Error(msg, { cause: e })`, `raise X from e`)?
- Czy `catch` nie łapie zbyt szeroko (`except Exception`, `catch (e)`) tam, gdzie
  spodziewany jest jeden konkretny błąd? Szeroki `catch` maskuje literówki i `TypeError`.
- Czy błąd trafia do logu z kontekstem (identyfikatory), a nie z samym komunikatem?
- Czy jest jakikolwiek `await` bez obsługi na ścieżce, gdzie odrzucenie jest możliwe?

### 6. Wyciek zasobu

```python
# USTERKA
conn = await pool.acquire()
wynik = await conn.fetch(zapytanie)   # wyjątek tutaj = połączenie nie wraca do puli
await pool.release(conn)
return wynik
```

Po kilkudziesięciu błędach pula jest wyczerpana i cała aplikacja przestaje odpowiadać.

```python
# POPRAWKA
async with pool.acquire() as conn:
    return await conn.fetch(zapytanie)
```

Szukaj: uchwytów plików, połączeń, blokad, `setInterval` bez `clearInterval`,
subskrypcji bez odsubskrybowania, `AbortController` bez wywołania, transakcji bez
`ROLLBACK` na ścieżce błędu, obserwatorów zdarzeń dodawanych w pętli.

Test w przeglądzie: **dla każdego zasobu — czy istnieje ścieżka wyjątku, na której nie
zostanie zwolniony?**

### 7. Wstrzyknięcie

```python
# USTERKA: SQL
zapytanie = f"SELECT * FROM zgloszenia WHERE status = '{status}' ORDER BY {sort}"
```

Parametry rozwiązują wartości, ale **nie** identyfikatory (nazwy kolumn, kierunek
sortowania) — te wymagają białej listy:

```python
# POPRAWKA
DOZWOLONE_SORT = {"utworzono": "utworzono", "numer": "numer"}
kolumna = DOZWOLONE_SORT.get(sort)
if kolumna is None:
    raise BladWalidacji("sort", "nieznane pole")
zapytanie = f"SELECT * FROM zgloszenia WHERE status = $1 ORDER BY {kolumna} DESC"
rows = await conn.fetch(zapytanie, status)
```

Pozostałe rodzaje do sprawdzenia w diffie:

| Rodzaj | Sygnał w kodzie | Poprawka |
| --- | --- | --- |
| Wstrzyknięcie poleceń | `exec`, `spawn` z konkatenacją, `shell=True` | Tablica argumentów, `shell=False` |
| Przechodzenie ścieżek | `path.join(katalog, nazwaOdUzytkownika)` | Normalizacja + sprawdzenie, że wynik zaczyna się od katalogu bazowego |
| SSRF | `fetch(urlOdUzytkownika)` | Biała lista domen; blokada adresów prywatnych i metadanych chmury |
| XSS | `innerHTML`, `dangerouslySetInnerHTML`, `\|safe` w szablonie | Escapowanie domyślne; sanityzacja dla HTML od użytkownika |
| Deserializacja | `pickle.loads`, `yaml.load` bez `SafeLoader` | `json`, `yaml.safe_load` |
| Wstrzyknięcie logów | Dane użytkownika w komunikacie logu bez escapowania | Logowanie strukturalne (pola, nie interpolacja) |

### 8. Kontrola dostępu na poziomie obiektu (IDOR)

```typescript
// USTERKA: sprawdzona rola, nie własność
app.get('/zgloszenia/:id', wymagaRoli('klient'), async (req, res) => {
  const z = await repo.pobierz(req.params.id);   // czyjekolwiek zgłoszenie
  res.json(doDto(z));
});
```

```typescript
// POPRAWKA: filtr w zapytaniu
const z = await repo.pobierzDlaKlienta(req.params.id, req.aktor.klientId);
if (z === null) { res.status(404).json(problem404()); return; }
```

To najczęstsza realna podatność w API biznesowych. W przeglądzie: **dla każdego
endpointu przyjmującego identyfikator — gdzie sprawdzana jest przynależność?**
Odpowiedź „sprawdzamy rolę” jest niewystarczająca.

### 9. Błędy graniczne

Konkretne przypadki, które trzeba świadomie przejść, bo model i człowiek pomijają je
tak samo:

| Wejście | Typowa usterka |
| --- | --- |
| Pusta kolekcja | Dzielenie przez `len(x)`; `max()` na pustej; `reduce` bez wartości początkowej |
| Jeden element | Logika zakładająca parę (porównania sąsiadów) |
| `null` / `undefined` / `None` | `undefined` odróżnione od braku klucza; `?? 0` a `\|\| 0` (drugie łyka `0` i `''`) |
| Wartości ujemne, zero | Brak `CHECK > 0`; kwota ujemna jako zwrot środków |
| Bardzo duże liczby | `Number.MAX_SAFE_INTEGER` przy identyfikatorach z bazy jako liczby |
| Ciąg z emoji / znakami spoza BMP | `length` liczy jednostki kodowe, nie znaki; ucinanie tekstu rozcina parę zastępczą |
| Polskie znaki, `İ`/`ı` | `toLowerCase()` zależne od locale w porównaniach |
| Data 29 lutego, zmiana czasu | Arytmetyka „+1 rok”, „+24 h” |
| Ta sama sekunda, ten sam klucz | Sortowanie niestabilne bez pola rozstrzygającego |
| Ciąg o długości limitu | `<` zamiast `<=`, ucięcie w bazie bez błędu |

Pytanie w przeglądzie: **czy istnieje test dla pustego wejścia i dla wejścia
granicznego?** Jeśli nie ma, poproś o niego zamiast dyskutować, czy kod jest poprawny.

### 10. Transakcja o złym zasięgu

```typescript
// USTERKA A: efekt zewnętrzny wewnątrz transakcji
await db.$transaction(async (tx) => {
  await tx.zgloszenie.update({ where: { id }, data: { status: 'zamkniete' } });
  await wyslijEmail(klient.email);        // 800 ms z blokadą wiersza; rollback nie cofnie e-maila
});

// USTERKA B: brak transakcji tam, gdzie potrzebna
await db.zgloszenie.update({ ... });
await db.wpisCzasu.create({ ... });        // padnie tutaj → stan niespójny
```

Reguły: transakcja obejmuje **wyłącznie** operacje na bazie; wywołania sieciowe,
wysyłka poczty i zapis plików idą przez outbox. Transakcja ma być krótka — długa
transakcja trzyma blokady i blokuje `VACUUM`.

### 11. Niebezpieczne domyślne wartości

| Wzorzec | Problem |
| --- | --- |
| `def f(lista=[])` w Pythonie | Domyślny argument mutowalny współdzielony między wywołaniami |
| `SELECT *` | Dodanie kolumny zmienia wynik; pobierasz `haslo_hash` i logujesz go |
| `cors({ origin: '*' })` z `credentials: true` | Nieprawidłowa i niebezpieczna kombinacja |
| `JSON.parse` bez walidacji kształtu | Ufasz strukturze danych z zewnątrz |
| Sekret jako wartość domyślna w kodzie | Trafia na produkcję, gdy zmienna nie ustawiona |
| `catch` bez ponownego rzucenia w middleware | Żądanie wisi do timeoutu |

### 12. Zmiana łamiąca niewidoczna w diffie

Najgroźniejsza kategoria, bo diff wygląda niewinnie:

- Zmiana wartości domyślnej parametru — wszyscy dotychczasowi wywołujący zmieniają
  zachowanie.
- Zmiana kolejności parametrów tego samego typu — kompilator nie pomoże.
- Rozszerzenie typu zwracanego o `null` — wywołujący nie sprawdzają.
- Zmiana znaczenia pola przy zachowanej nazwie (`kwota` z brutto na netto).
- Zmiana domyślnego sortowania — paginacja u konsumenta zaczyna gubić rekordy.
- Dodanie `NOT NULL` do kolumny bez wartości domyślnej — stara wersja aplikacji przestaje
  wstawiać.
- Zmiana strefy czasowej w interpretacji daty.

Metoda: dla każdej zmienionej sygnatury publicznej wyszukaj wszystkie użycia i sprawdź
je jedno po drugim. To jedyna metoda, która działa.

## Przegląd testów

Test też podlega przeglądowi — zły test jest gorszy od jego braku, bo daje fałszywe
poczucie bezpieczeństwa.

| Usterka testu | Objaw | Poprawka |
| --- | --- | --- |
| Test sprawdza implementację, nie zachowanie | Weryfikacja, że wywołano metodę atrapy | Sprawdzaj wynik i stan po operacji |
| Brak testu ścieżki błędu | Tylko happy path | Test na każdą gałąź `catch` i każdy błąd domenowy |
| Test niedeterministyczny | `new Date()`, `random`, `sleep`, kolejność zależna od hasza | Wstrzyknięty zegar, ustalone ziarno, sortowanie |
| Współdzielony stan między testami | Test przechodzi sam, pada w zestawie | Izolacja: transakcja z wycofaniem albo świeży schemat |
| Asercja na całym obiekcie z datami | Pada przy każdej zmianie pola | Asercje na istotnych polach |
| Test tautologiczny | Ta sama logika w teście i w kodzie | Oczekiwana wartość wpisana wprost |
| Atrapa zwracająca strukturę niezgodną z prawdziwą | Test zielony, produkcja pada | Test kontraktowy atrapy albo test integracyjny |

Kluczowe pytanie: **czy ten test padłby, gdyby usterkę wprowadzono z powrotem?**

## Jak formułować uwagi

Uwaga ma zawierać trzy rzeczy: **co**, **dlaczego to problem**, **co zrobić**.
Brak trzeciego elementu zamienia przegląd w wymianę zdań.

| Zamiast | Napisz |
| --- | --- |
| „To jest źle” | „Ten `catch` łapie też `TypeError` z literówki w nazwie pola i zamienia go w 404. Zawęź do `NotFoundError`.” |
| „Nieoptymalne” | „Przy 500 pozycjach to 501 zapytań (~2 s). `include: { klient: true }` załatwia to jednym.” |
| „Dodaj testy” | „Brakuje testu dla pustej listy pozycji — `reduce` bez wartości początkowej rzuci `TypeError`.” |
| „Nie podoba mi się ta nazwa” | „`dane` w tym module oznacza już DTO wejściowe (linia 12). Proponuję `pozycjeDoRozliczenia`.” |

### Oznaczanie wagi

Prefiksuj każdą uwagę, żeby autor wiedział, co blokuje scalenie:

- **[blokujące]** — usterka poprawności, bezpieczeństwa lub utraty danych. Bez poprawki
  nie ma zgody.
- **[istotne]** — powinno być poprawione, ale można w osobnej zmianie z zapisanym zadaniem.
- **[drobne]** — sugestia; autor decyduje.
- **[pytanie]** — nie rozumiem intencji, wyjaśnij. **Nie** jest to zawoalowana krytyka.
- **[pochwała]** — konkretnie, za co. Nie ozdobnik: wskazuje, jaki wzorzec ma się utrwalić.

Proporcja zdrowego przeglądu: kilka uwag blokujących **lub** kilkanaście drobnych,
nigdy trzydzieści mieszanych. Trzydzieści uwag oznacza, że zmiana jest za duża albo
brakuje uzgodnionego stylu.

### Zasady prowadzenia rozmowy

- Uwaga dotyczy kodu, nie autora: „ta funkcja pomija X”, nie „pominąłeś X”.
- Nie proponuj przepisania w swoim stylu, jeśli obecny działa i mieści się w konwencji
  repozytorium.
- Jeśli poprawka jest wieloznaczna, napisz, jaki wynik ma zostać osiągnięty, i zostaw
  autorowi sposób.
- Po dwóch rundach niezgody rozmawiajcie głosem i zapiszcie wynik w kodzie lub ADR.
  Trzecia runda komentarzy nie doprowadzi do zgody.
- Odrzucona uwaga z sensownym uzasadnieniem to zamknięty wątek, nie porażka recenzenta.

## Co nie jest przedmiotem przeglądu

Uwagi z tej listy usuń przed wysłaniem — obniżają sygnał całego przeglądu:

| Nie recenzuj | Bo |
| --- | --- |
| Formatowanie, cudzysłowy, przecinki końcowe | Prettier/Black/Ruff w CI |
| Kolejność importów, nieużywane zmienne | Linter |
| Preferencje stylistyczne bez uzasadnienia funkcjonalnego | To gust, nie jakość |
| Nazwa zmiennej lokalnej w krótkiej funkcji | Koszt dyskusji > zysk |
| Architektura całego systemu przy zmianie 30 linii | Za późno; to temat na ADR **przed** zmianą |
| Fakt, że kod nie używa najnowszego wzorca | Spójność z repozytorium bije nowość |
| Kod niezmieniony przez ten diff | Osobne zadanie; inaczej każdy PR rośnie w nieskończoność |
| Domysły o wydajności bez pomiaru | „To będzie wolne” bez liczby to spekulacja |

Wyjątek od przedostatniego: jeśli w niezmienionym kodzie obok widzisz **podatność**
albo **utratę danych** — zgłoś, ale jako osobne zadanie, nie jako blokadę tej zmiany.

## Format wyniku przeglądu

```markdown
## Przegląd: <tytuł zmiany>

**Werdykt:** wymaga zmian / zatwierdzam z uwagami / zatwierdzam

**Zakres:** <co zmiana robi, 1-2 zdania — dowód, że recenzent zrozumiał>

### Blokujące
1. `sciezka/plik.ts:88` — <co, dlaczego, jak poprawić>

### Istotne
1. `sciezka/plik.ts:140` — <...>

### Drobne
- `sciezka/plik.ts:12` — <...>

### Pytania
- <...>

### Dobre
- <konkretnie, co warto powtarzać>
```

## Lista kontrolna recenzenta

- [ ] Rozumiem, co zmiana ma osiągnąć, i widzę to w diffie.
- [ ] Sprawdziłem wejścia graniczne: puste, jednoelementowe, `null`, ujemne, maksymalne.
- [ ] Sprawdziłem współbieżność: sprawdź-i-działaj, odczyt-modyfikuj-zapis, zasięg transakcji.
- [ ] Sprawdziłem uprawnienia na poziomie obiektu, nie tylko roli.
- [ ] Każde zapytanie zwracające zbiór ma limit; żadna pętla nie zawiera zapytania.
- [ ] Każdy zasób zwalniany także na ścieżce wyjątku.
- [ ] Żaden błąd nie jest połknięty; przyczyna zachowana przy opakowaniu.
- [ ] Żadne dane użytkownika nie trafiają do SQL/polecenia/ścieżki/HTML bez obróbki.
- [ ] Sekrety nie występują w kodzie, logach ani w odpowiedziach błędnych.
- [ ] Migracja bazy zgodna z poprzednią wersją aplikacji.
- [ ] Zmiana mieści się w warstwie, do której należy.
- [ ] Istnieje test, który nie przechodziłby przed tą zmianą.
- [ ] Każda uwaga ma wagę i propozycję działania.
