# Wdrożenie — karta

Karta obejmuje drogę od zielonego CI do działającej produkcji, niezależnie od języka:
listę kontrolną wydania, migracje bez przestoju, przełączniki funkcji, wdrożenie
kroczące i wycofanie. Pakowanie i wdrożenie usługi Pythona opisuje
`references/engineering-core/02-python-backend-dane/references/wdrozenie-python.md`.

Reguła nadrzędna: **wdrożenie ma być nudne.** Każdy element, który czyni je ekscytującym
(ręczne kroki, migracja bez planu wycofania, „wdrażamy i patrzymy”), jest usterką procesu,
nie cechą charakteru zespołu.

---

## Lista kontrolna przed wydaniem

Przechodzisz ją **przed** naciśnięciem czegokolwiek. Pozycje oznaczone **[blokujące]**
zatrzymują wdrożenie.

### Kod i testy

- [ ] **[blokujące]** CI zielone na commicie, który idzie na produkcję — nie na innym.
- [ ] **[blokujące]** Zestaw e2e ścieżek krytycznych przeszedł na środowisku staging.
- [ ] Przegląd kodu zakończony; uwagi blokujące rozwiązane.
- [ ] Brak `TODO`, `FIXME`, `console.log`, `debugger`, `.only` w zmienionych plikach.
- [ ] Brak zakomentowanego kodu „na wszelki wypadek”.
- [ ] Zależności: brak podatności krytycznych (`npm audit --audit-level=high`,
      `pip-audit`); nowe zależności mają znany właściciela i licencję.

### Dane i zgodność wsteczna

- [ ] **[blokujące]** Migracje przetestowane na kopii danych produkcyjnych, z pomiarem czasu.
- [ ] **[blokujące]** Stary kod działa na nowym schemacie (warunek wdrożenia stopniowego).
- [ ] Migracje nieodwracalne oznaczone jawnie; kopia zapasowa wykonana i **odtworzona
      próbnie** (kopia niesprawdzona to nie kopia).
- [ ] Zmiany API wstecznie zgodne albo wersjonowane; konsumenci powiadomieni.

### Konfiguracja i sekrety

- [ ] **[blokujące]** Nowe zmienne środowiskowe ustawione **na wszystkich** środowiskach.
- [ ] Aplikacja waliduje konfigurację przy starcie i pada natychmiast przy braku
      wymaganej zmiennej (nie po 20 minutach przy pierwszym użyciu).
- [ ] Żaden sekret nie trafił do repozytorium ani do obrazu (skan `gitleaks`/`trufflehog`).
- [ ] Certyfikaty i klucze nie wygasają w ciągu najbliższych 30 dni.

### Obserwowalność i wycofanie

- [ ] **[blokujące]** Procedura wycofania zapisana i wykonalna w < 10 minut.
- [ ] **[blokujące]** Progi wycofania ustalone **liczbowo przed** wdrożeniem.
- [ ] Nowe metryki/logi/alarmy istnieją i były sprawdzone na staging.
- [ ] Ktoś konkretny obserwuje przez 30 minut po wdrożeniu — nazwisko, nie „zespół”.

### Komunikacja

- [ ] Dziennik zmian zaktualizowany.
- [ ] Zainteresowani powiadomieni, jeśli zmiana jest widoczna dla użytkownika.
- [ ] Wdrożenie nie zbiega się ze szczytem ruchu ani z zamknięciem okresu księgowego.

---

## Wersjonowanie i dziennik zmian

**SemVer** dla wszystkiego, co ma konsumenta (biblioteki, API): `MAJOR.MINOR.PATCH`.
Zmiana łamiąca → MAJOR. Nowa funkcja wstecznie zgodna → MINOR. Poprawka → PATCH.

Dla aplikacji wdrażanych ciągle SemVer nie niesie informacji — użyj `RRRR.MM.DD-<numer>`
albo skrótu commita. Ważne, żeby **wersja była widoczna w działającej aplikacji**:

```ts
// endpoint /wersja lub /healthz zwracający to samo, co jest w metrykach i logach
app.get('/wersja', (_req, res) => res.json({
  wersja: process.env.APP_VERSION,
  commit: process.env.COMMIT_SHA,
  zbudowano: process.env.BUILD_TIME,
}));
```

Bez tego pierwsze pytanie każdej awarii — „która wersja tam działa” — nie ma szybkiej
odpowiedzi.

Dziennik zmian pisany **dla użytkownika, nie z `git log`**. Lista 40 commitów
`fix: poprawka` nie jest dziennikiem zmian. Format:

```markdown
## [2026.08.04] – 2026-08-04
### Dodane
- Eksport faktur do formatu KSeF XML (menu Faktury → Eksport).
### Zmienione
- Domyślny termin płatności to 14 dni zamiast 7. Istniejące faktury bez zmian.
### Naprawione
- Korekta z ujemną kwotą zwracała 500 zamiast komunikatu walidacji.
### Łamiące zgodność
- `GET /api/faktury` zwraca `kwotaGroszy` (liczba całkowita) zamiast `kwota` (tekst).
  Stare pole dostępne do 2026-11-01, po tej dacie usunięte.
```

Sekcja „Łamiące zgodność” zawsze z **datą usunięcia starej ścieżki**. Bez daty stare pole
zostanie na zawsze.

---

## Migracje bezpieczne dla wdrożenia stopniowego

W trakcie wdrożenia stopniowego (kanarkowego, kroczącego, niebiesko-zielonego) **stara
i nowa wersja kodu działają jednocześnie na tej samej bazie**. Każda migracja musi być
zgodna z obiema.

### Wzorzec rozszerz – przenieś – usuń

Trzy oddzielne wdrożenia. Skrócenie do jednego jest przyczyną większości awarii
migracyjnych.

**Przykład: zmiana `kwota TEXT` na `kwota_groszy BIGINT`.**

```sql
-- WDROŻENIE 1 (rozszerz): dodaj nowe, nie ruszaj starego
ALTER TABLE faktury ADD COLUMN kwota_groszy BIGINT;
CREATE INDEX CONCURRENTLY idx_faktury_kwota_groszy ON faktury (kwota_groszy);
```
Kod wersji 1: **zapisuje do obu kolumn**, czyta ze starej. Stary kod nadal działa —
nowa kolumna jest `NULL`owalna i ignorowana.

```sql
-- WDROŻENIE 2 (przenieś): uzupełnij dane wsadowo, poza godzinami szczytu
UPDATE faktury SET kwota_groszy = ROUND(replace(kwota, ',', '.')::numeric * 100)
WHERE kwota_groszy IS NULL AND id BETWEEN $1 AND $2;   -- partiami po 10 tys.
```
Kod wersji 2: zapisuje do obu, **czyta z nowej** z awaryjnym powrotem do starej.
Weryfikacja: `SELECT count(*) FROM faktury WHERE kwota_groszy IS NULL` musi dać 0.

```sql
-- WDROŻENIE 3 (usuń): dopiero gdy nic już nie czyta ze starej
ALTER TABLE faktury ALTER COLUMN kwota_groszy SET NOT NULL;
ALTER TABLE faktury DROP COLUMN kwota;
```
Kod wersji 3: tylko nowa kolumna. Odczekaj co najmniej jeden pełny cykl wdrożeniowy
między krokiem 2 a 3 — musisz mieć pewność, że żadna instancja starego kodu nie żyje.

### Operacje blokujące w PostgreSQL

| Operacja | Blokada | Bezpieczny wariant |
| --- | --- | --- |
| `ADD COLUMN` bez `DEFAULT` | krótka `ACCESS EXCLUSIVE` | bezpieczne |
| `ADD COLUMN ... DEFAULT <stała>` | krótka (PG ≥ 11 nie przepisuje tabeli) | bezpieczne |
| `ADD COLUMN ... DEFAULT <funkcja>` | przepisanie całej tabeli | dodaj kolumnę, potem `UPDATE` partiami, potem `SET DEFAULT` |
| `CREATE INDEX` | blokuje zapisy na czas budowy | `CREATE INDEX CONCURRENTLY` (poza transakcją) |
| `ALTER COLUMN SET NOT NULL` | skan całej tabeli pod `ACCESS EXCLUSIVE` | `ADD CONSTRAINT ... NOT VALID`, `VALIDATE CONSTRAINT`, potem `SET NOT NULL` |
| `ADD FOREIGN KEY` | blokuje obie tabele | `NOT VALID`, potem `VALIDATE CONSTRAINT` |
| `ALTER COLUMN TYPE` | przepisanie tabeli | nowa kolumna + rozszerz-przenieś-usuń |
| `DROP COLUMN` | krótka | bezpieczne, ale nieodwracalne — dopiero w kroku 3 |

Ustaw limit czasu oczekiwania na blokadę, żeby migracja nie zatrzymała całej aplikacji:

```sql
SET lock_timeout = '3s';
SET statement_timeout = '30s';
```

Bez `lock_timeout` `ALTER TABLE` czekający na długą transakcję ustawia się w kolejce
i **blokuje wszystkie kolejne zapytania do tej tabeli** — awaria całkowita z powodu
migracji, która sama w sobie trwałaby 20 ms.

### Migracja w potoku CI/CD

Migracje uruchamiaj **jako osobny krok przed wdrożeniem kodu**, nie przy starcie
aplikacji. Start aplikacji z migracją oznacza: N instancji uruchamia migrację
równolegle, wyścig o blokadę, a przy padnięciu migracji kontener wpada w pętlę restartów.

Jeśli framework wymusza migracje przy starcie, wymuś pojedynczego wykonawcę
(zadanie `job` w Kubernetes, `release phase` na platformie, blokada doradcza
`pg_advisory_lock`).

---

## Przełączniki funkcji

Rozdzielenie wdrożenia (kod na produkcji) od wydania (funkcja widoczna) to najtańsze
narzędzie ograniczania ryzyka, jakie istnieje.

```ts
if (await flagi.wlaczona('ksef-eksport', { uzytkownikId, najemcaId })) {
  return eksportKsef(faktura);
}
return eksportPdf(faktura);
```

Zasady:

1. **Domyślna wartość to stare zachowanie.** Awaria systemu flag nie może włączyć
   niedokończonej funkcji.
2. **Flaga ma właściciela i datę usunięcia** zapisane w miejscu jej definicji.
3. **Testuj obie gałęzie.** Flaga podwaja liczbę stanów; kod za wyłączoną flagą,
   nietestowany przez trzy miesiące, przy włączeniu nie zadziała.
4. **Usuwaj flagi po ustabilizowaniu.** 40 martwych flag to 2^40 teoretycznych
   konfiguracji i kod, którego nikt nie rozumie. Kwartalny przegląd, obowiązkowy.
5. **Flaga to nie przełącznik konfiguracji.** Rozróżniaj: flagi wydaniowe (krótkożyjące,
   do usunięcia) od konfiguracji produktowej (długożyjąca, np. plan abonamentowy).

Flagi zabijające (kill switch) dla integracji zewnętrznych są osobną, trwałą kategorią:
możliwość wyłączenia wywołań do padającego dostawcy bez wdrożenia jest warta swojej ceny.

---

## Wdrożenia bez przestoju

### Kroczące (rolling)

Domyślne w Kubernetes i większości platform. Instancje wymieniane po kolei.

Warunki poprawności: aplikacja obsługuje `SIGTERM` (kończy bieżące żądania, przestaje
przyjmować nowe), ma sondę gotowości odróżnioną od sondy życia, a stara i nowa wersja
są zgodne (patrz migracje).

```yaml
readinessProbe:                 # czy mogę dostawać ruch
  httpGet: { path: /gotowosc, port: 8080 }
  periodSeconds: 5
livenessProbe:                  # czy mam być zrestartowany
  httpGet: { path: /zycie, port: 8080 }
  periodSeconds: 10
  failureThreshold: 3
terminationGracePeriodSeconds: 45
```

Sonda gotowości sprawdza zależności (baza, cache). Sonda życia **nie może** ich sprawdzać:
chwilowa niedostępność bazy zrestartuje wtedy wszystkie instancje jednocześnie i zamieni
awarię częściową w całkowitą.

### Niebiesko-zielone

Dwa pełne środowiska; przełączenie ruchu jednym ruchem, wycofanie w sekundach.

Koszt: podwójna infrastruktura na czas wdrożenia. Pułapka: **wspólna baza danych** —
niebiesko-zielone nie chroni przed złą migracją, chroni tylko przed złym kodem.

### Kanarkowe

Nowa wersja dostaje 1% → 5% → 25% → 100% ruchu, z automatyczną oceną między krokami.

```
1%  przez 10 min → sprawdź: 5xx, p95, błędy biznesowe → 5%
5%  przez 15 min → sprawdź → 25%
25% przez 30 min → sprawdź → 100%
```

Warunek działania: **porównujesz kanarka z bazą w tym samym oknie czasowym**, nie
z historią. Porównanie z wczoraj myli efekt wdrożenia z porą dnia.

Kanarek nie wykryje: błędów dotyczących 0,1% użytkowników, problemów widocznych dopiero
przy pełnym obciążeniu, ani awarii migracji. To nie jest zastępstwo dla testów.

### Wybór

| Sytuacja | Strategia |
| --- | --- |
| Zmiana bez migracji, niskie ryzyko | krocząca |
| Zmiana ryzykowna, ruch pozwala na próbkowanie | kanarkowa |
| Zmiana infrastruktury, potrzeba natychmiastowego wycofania | niebiesko-zielona |
| Zmiana zachowania widoczna dla użytkownika | krocząca + przełącznik funkcji |
| Migracja danych | rozszerz-przenieś-usuń, niezależnie od strategii wdrożenia |

---

## Wycofanie

### Progi ustalane przed wdrożeniem

Zapisz je **liczbowo** przed startem. Decyzja podjęta w trakcie awarii, pod presją, jest
zwykle „poczekajmy jeszcze 10 minut” — i awaria trwa godzinę zamiast pięciu minut.

```markdown
## Progi wycofania — wydanie 2026.08.04
Wycofujemy natychmiast, bez dyskusji, gdy w oknie 5 minut po wdrożeniu:
- odsetek 5xx na /api/* > 1% (baza: 0,05%)
- p95 /api/faktury > 1500 ms (baza: 340 ms)
- wskaźnik powodzenia logowania < 98% (baza: 99,7%)
- pojawi się jakikolwiek błąd zapisu do bazy
Obserwacja przez 30 min: Anna K. Decyzja o wycofaniu: bez konsultacji.
```

### Procedura

1. **Wycofaj najpierw, diagnozuj potem.** Przywrócenie działania jest ważniejsze niż
   ustalenie przyczyny. Diagnoza z ruchem produkcyjnym na zepsutej wersji kosztuje
   użytkowników.
2. Preferowana kolejność: wyłącz przełącznik funkcji (sekundy) → przełącz ruch na
   poprzednią wersję (minuta) → wdróż poprzedni obraz (minuty). Cofanie commita i
   przebudowa to **ostateczność**, bo trwa tyle co pełne CI.
3. Sprawdź, że wycofanie faktycznie zadziałało — metryki wróciły do bazy.
4. Zapisz oś czasu, dopóki pamiętasz
   (`references/engineering-core/07-debug-testy-deploy/references/awaria.md`).

### Kiedy wycofanie nie jest możliwe

Po migracji nieodwracalnej i po wysłaniu wiadomości/płatności. Dlatego:

- Migracje nieodwracalne wdrażaj **osobno**, po co najmniej jednym stabilnym cyklu
  z kodem, który już jest na produkcji.
- Operacje o skutkach zewnętrznych (wysyłka, płatność) chroń przełącznikiem i
  idempotencją — powtórzenie nie może wysłać drugiej faktury.

---

## Sekrety i konfiguracja per środowisko

| Rodzaj | Gdzie trzymać | Czego nie robić |
| --- | --- | --- |
| Sekrety (hasła, klucze, tokeny) | menedżer sekretów platformy / Vault, wstrzykiwane jako zmienne albo pliki | nigdy w repozytorium, w obrazie, w `NEXT_PUBLIC_*`, w logach |
| Konfiguracja per środowisko | zmienne środowiskowe | nie w kodzie z `if (env === 'prod')` rozsianym po całym projekcie |
| Konfiguracja produktowa | baza danych / system flag | nie wymaga wdrożenia do zmiany |
| Stałe techniczne | kod | nie w zmiennych środowiskowych „na wszelki wypadek” |

Walidacja przy starcie — nienegocjowalne:

```ts
import { z } from 'zod';
const Srodowisko = z.object({
  DATABASE_URL: z.string().url(),
  SESSION_SECRET: z.string().min(32),
  SENTRY_DSN: z.string().url().optional(),
  NODE_ENV: z.enum(['development', 'test', 'production']),
});
export const env = Srodowisko.parse(process.env);   // pada przy starcie, nie w produkcji
```

Zmienna z prefiksem `NEXT_PUBLIC_`/`VITE_` **trafia do przeglądarki**. Klucz API dostawcy
umieszczony tam jest publiczny od chwili wdrożenia — i pozostaje publiczny w cache CDN
także po naprawie. Rotacja klucza obowiązkowa, nie samo usunięcie.

Rotacja sekretów: obsługuj **dwa ważne sekrety naraz** (stary i nowy) na czas przejścia,
inaczej rotacja wymaga przestoju.

---

## CI/CD

### Etapy i bramki

```
push → [1] szybka bramka (2-4 min)     lint, typy, testy jednostkowe, skan sekretów
     → [2] budowanie (3-8 min)          jeden artefakt/obraz, tagowany skrótem commita
     → [3] testy integracyjne (5-10 min) z kontenerami usług
     → [4] wdrożenie staging (auto)
     → [5] e2e na staging (5-15 min)
     → [6] wdrożenie produkcja          auto albo za zatwierdzeniem
     → [7] testy dymne na produkcji     ścieżki krytyczne, 1-2 min
```

Zasady, których złamanie kosztuje najwięcej:

1. **Buduj raz, wdrażaj wszędzie.** Ten sam artefakt na staging i produkcję. Osobne
   budowanie dla produkcji oznacza, że testowałeś inny artefakt niż wdrażasz.
2. **Etap 1 poniżej 5 minut.** Powyżej tego ludzie przestają czekać na wynik i pchają
   dalej, co niweczy sens bramki.
3. **Bramki blokują, nie ostrzegają.** Bramka, którą można pominąć jednym kliknięciem
   bez uzasadnienia, jest ozdobą.
4. **Testy dymne po wdrożeniu na produkcję.** Zielone CI nie dowodzi, że produkcja
   wstała — dowodzi tylko, że kod jest poprawny.

### Bramki jakości — sensowny zestaw

| Bramka | Próg | Blokuje |
| --- | --- | --- |
| Typy | zero błędów | tak |
| Lint | zero błędów, ostrzeżenia dozwolone | tak |
| Testy jednostkowe + integracyjne | wszystkie zielone | tak |
| Pokrycie różnicy | ≥ 70% nowego kodu | tak |
| Skan sekretów | zero trafień | tak |
| Podatności zależności | zero krytycznych i wysokich z dostępną łatką | tak |
| e2e ścieżek krytycznych | wszystkie zielone | tak |
| Rozmiar pakietu klienckiego | wzrost > 10% wymaga uzasadnienia | ostrzega |
| Testy wizualne | różnice do zaakceptowania ręcznie | ostrzega |

### Buforowanie

```yaml
# GitHub Actions — klucze cache oparte na plikach blokad
- uses: actions/setup-node@v4
  with: { node-version: 22, cache: npm }
- uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
- uses: actions/cache@v4
  with:
    path: |
      .next/cache
      node_modules/.cache
    key: build-${{ runner.os }}-${{ hashFiles('package-lock.json') }}-${{ github.sha }}
    restore-keys: build-${{ runner.os }}-${{ hashFiles('package-lock.json') }}-
```

Reguły: klucz cache **musi zawierać skrót pliku blokad** (inaczej dostaniesz stare
zależności i będziesz debugował duchy); cache przeglądarek Playwrighta oszczędza ok. 60 s
na uruchomienie; nigdy nie buforuj artefaktów wdrożeniowych (obraz ma być budowany
z czystego stanu).

Warstwy obrazu Docker: kopiuj `package*.json` i instaluj zależności **przed** kopiowaniem
źródeł. Odwrotna kolejność unieważnia cache przy każdej zmianie kodu i wydłuża budowanie
o minuty.

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
USER node
CMD ["node", "dist/serwer.js"]
```

`USER node` nie jest ozdobą: kontener działający jako `root` zamienia dowolne wykonanie
kodu w przejęcie hosta w części konfiguracji.

---

## Wdrożenie w piątek

Zakaz wdrożeń w piątek to obejście problemu, nie rozwiązanie. Jeśli boisz się wdrożyć
w piątek, twój proces jest zły — i jest tak samo zły we wtorek, tylko masz więcej czasu
na sprzątanie.

**Wdrażaj, gdy** spełnione są łącznie: wycofanie działa i było przećwiczone; alarmy
działają; ktoś jest dostępny przez najbliższe 2 godziny; zmiana nie zawiera migracji
nieodwracalnej ani zmiany łamiącej zgodność.

**Nie wdrażaj, gdy** zachodzi cokolwiek z poniższych — niezależnie od dnia tygodnia:

- Nie ma nikogo, kto zareaguje przez najbliższe 2 godziny.
- Wycofanie jest niemożliwe albo nieprzećwiczone.
- Zmiana zawiera migrację nieodwracalną, a nie ma na to okna.
- Zaczyna się okres szczytowy (zamknięcie miesiąca, kampania, termin ustawowy).
- Autor zmiany kończy pracę za 20 minut.
- Jesteś zmęczony i wdrażasz „żeby zamknąć temat”.

Ostatni punkt jest realną przyczyną znacznej części awarii. Zmiana poczeka do poniedziałku;
awaria nie poczeka.

---

## Testy dymne po wdrożeniu

Minimalny zestaw, uruchamiany automatycznie po każdym wdrożeniu produkcyjnym, do 2 minut:

```bash
#!/usr/bin/env bash
set -euo pipefail
BASE="${1:?podaj adres bazowy}"

test -n "$(curl -fsS "$BASE/zycie")"
[ "$(curl -fsS "$BASE/wersja" | jq -r .commit)" = "$COMMIT_SHA" ] \
  || { echo "wdrożona inna wersja niż oczekiwana"; exit 1; }
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")" = "200" ]
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/faktury")" = "401" ]  # authz działa
curl -fsS "$BASE/api/gotowosc" | jq -e '.baza == "ok" and .cache == "ok"' >/dev/null
echo "Testy dymne: OK"
```

Sprawdzenie zgodności wdrożonego commita z oczekiwanym wyłapuje najczęstszą cichą
usterkę wdrożenia: wdrożył się poprzedni obraz, bo tag nie został zaktualizowany.

Do pełniejszych ścieżek na produkcji użyj Playwrighta z kontem testowym i danymi oznaczonymi jako
testowe — patrz
`references/engineering-core/07-debug-testy-deploy/references/testowanie-w-przegladarce.md`.
