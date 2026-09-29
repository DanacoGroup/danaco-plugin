# Git — karta

## Procedury podstawowe

Pracuj według stałej sekwencji: stan → gałąź → zmiany → rewizja → scalanie. Nie pomijaj żadnego
etapu.

1. **Stan.** Przed każdą operacją ustal, w jakim punkcie znajduje się repozytorium:
   ```
   git status
   git log --oneline -10
   git branch --show-current
   ```
2. **Gałąź.** Nową pracę rozpoczynaj wyłącznie na dedykowanej gałęzi utworzonej z aktualnej gałęzi
   głównej:
   ```
   git fetch origin
   git switch -c feature/nazwa-zadania origin/main
   ```
3. **Zmiany.** Dodawaj do indeksu wyłącznie pliki, które świadomie zmodyfikowano. Przed dodaniem
   obejrzyj różnice:
   ```
   git diff
   git add sciezka/do/pliku
   git diff --staged
   ```
4. **Rewizja.** Twórz rewizje małe i jednotematyczne. Komunikat formułuj w trybie oznajmującym, w
   pierwszym wierszu do około 50 znaków, bez kropki na końcu; szczegóły umieszczaj po pustym
   wierszu:
   ```
   git commit -m "Dodaje walidację numeru NIP w formularzu klienta"
   ```
   Dla zmian wymagających uzasadnienia stosuj komunikat wielowierszowy:
   ```
   Zastępuje sekwencyjne zapytania jednym zapytaniem zbiorczym

   Poprzednia implementacja wykonywala N zapytań w pętli, co przy
   dużych zbiorach danych powodowało przekroczenie limitu czasu.
   ```
5. **Scalanie.** Przed scaleniem zaktualizuj gałąź względem gałęzi docelowej i rozwiąż konflikty
   lokalnie. Scalaj przez żądanie zmian (pull request / merge request), nie bezpośrednio na gałęzi
   głównej:
   ```
   git fetch origin
   git rebase origin/main
   git push -u origin feature/nazwa-zadania
   ```

W środowisku Windows skonfiguruj obsługę końców wierszy, aby uniknąć fałszywych różnic w plikach:
```
git config core.autocrlf true
```

## Bezpieczne wzorce

- Na wspólnych gałęziach (`main`, `develop`, gałęzie wydań) nie wykonuj operacji przepisujących
  historię: `rebase`, `commit --amend`, `reset` na opublikowanych rewizjach. Historia wypchnięta do
  zdalnego repozytorium jest umową z zespołem.
- Stosuj `rebase` wyłącznie na własnych, niewypchniętych lub jednoosobowych gałęziach roboczych, aby
  uporządkować historię przed przeglądem. Stosuj `merge` wszędzie tam, gdzie gałąź jest
  współdzielona lub historia ma pozostać wiernym zapisem przebiegu prac.
- Utrzymuj plik `.gitignore` dopasowany do ekosystemu projektu. Nigdy nie zatwierdzaj danych
  uwierzytelniających; wpis w `.gitignore` nie usuwa pliku już zatwierdzonego. Przykładowy zestaw
  wpisów dla projektu mieszanego (Node, Python, Windows):
  ```
  node_modules/
  dist/
  __pycache__/
  *.pyc
  .venv/
  .env
  .env.*
  *.pem
  .idea/
  .vs/
  Thumbs.db
  ```
- Przed wypchnięciem wykonaj `git pull --rebase` lub `git pull` (zgodnie z konwencją projektu) i
  upewnij się, że testy przechodzą lokalnie.
- Sekrety omyłkowo zatwierdzone traktuj jako ujawnione: zgłoś właścicielowi projektu i doprowadź do
  rotacji poświadczeń; samo usunięcie pliku w kolejnej rewizji nie usuwa go z historii.

## Diagnostyka

- **Odzyskiwanie utraconych rewizji.** `git reflog` przechowuje lokalną historię przesunięć
  wskaźnika HEAD. Po omyłkowym `reset` lub usunięciu gałęzi odszukaj skrót rewizji i przywróć stan:
  ```
  git reflog
  git branch odzyskana <skrot-rewizji>
  ```
- **Lokalizowanie regresji.** Użyj wyszukiwania połówkowego, wskazując rewizję sprawną i wadliwą:
  ```
  git bisect start
  git bisect bad
  git bisect good <skrot-rewizji-sprawnej>
  git bisect reset
  ```
- **Rozwiązywanie konfliktów.** Po komunikacie o konflikcie wykonaj `git status`, aby zobaczyć listę
  plików w konflikcie. W każdym pliku odszukaj znaczniki `<<<<<<<`, `=======`, `>>>>>>>`, świadomie
  wybierz lub połącz treść obu stron, następnie `git add` i kontynuuj (`git merge --continue` albo
  `git rebase --continue`). Nie wybieraj mechanicznie „swojej” wersji — przeanalizuj intencję obu
  zmian. W razie wątpliwości przerwij operację poleceniem `git merge --abort` lub `git rebase
  --abort` i skonsultuj się z autorem drugiej zmiany.
- **Inspekcja historii pliku.** `git log --follow -p -- sciezka/do/pliku` pokazuje pełną historię
  zmian pliku wraz z różnicami; `git blame sciezka/do/pliku` wskazuje autora każdego wiersza.

## Operacje nieodwracalne — wymagają zgody właściciela projektu

Nie wykonuj poniższych poleceń bez wyraźnej, jednoznacznej zgody właściciela projektu udzielonej dla
konkretnego przypadku:

- `git push --force` — nadpisuje historię w zdalnym repozytorium; bezpowrotnie usuwa rewizje innych
  osób wypchnięte w międzyczasie i unieważnia lokalne kopie całego zespołu. Jeżeli nadpisanie jest
  uzasadnione, stosuj wyłącznie `git push --force-with-lease` i wyłącznie na własnej gałęzi.
- `git reset --hard` — odrzuca wszystkie niezatwierdzone zmiany w katalogu roboczym i indeksie;
  zmian niezatwierdzonych nie da się odzyskać.
- `git clean -fd` — trwale usuwa nieśledzone pliki i katalogi, w tym konfiguracje lokalne i wyniki
  pracy nieobjęte repozytorium. Przed rozważeniem użycia wykonaj `git clean -nd` (przebieg próbny).
- `git branch -D` oraz `git push origin --delete <galaz>` — usuwają gałąź bez sprawdzenia, czy
  została scalona.
- `git stash drop` / `git stash clear` — trwale usuwają odłożone zmiany.

## Typowe błędy modeli LLM przy tym narzędziu

1. **Zatwierdzanie bez uprzedniego `git status` i `git diff`.** Model zatwierdza pliki, których
   stanu nie zna, w tym artefakty budowy lub sekrety. Zawsze najpierw obejrzyj stan i różnice,
   dodawaj pliki imiennie.
2. **Użycie `git add .` lub `git add -A` odruchowo.** Do rewizji trafiają pliki przypadkowe. Dodawaj
   wyłącznie pliki związane z zadaniem, po obejrzeniu `git status`.
3. **Dopisywanie się do cudzych zmian.** Model modyfikuje pliki, które w katalogu roboczym zawierają
   niezatwierdzone zmiany użytkownika, i zatwierdza je łącznie ze swoimi. Jeżeli `git status`
   pokazuje obce modyfikacje, zapytaj, zanim je uwzględnisz lub odłożysz.
4. **`git push --force` jako „rozwiązanie” rozjazdu gałęzi.** Rozjazd z gałęzią zdalną rozwiązuj
   przez `git pull --rebase` lub scalenie, nigdy przez nadpisanie historii — nadpisanie niszczy
   pracę innych.
5. **Komunikaty rewizji opisujące proces zamiast zmiany.** Komunikaty typu „poprawki”, „zmiany po
   uwagach”, „fix” nie niosą informacji. Opisuj, co rewizja robi, w trybie oznajmującym: „Usuwa
   zdublowaną walidację adresu e-mail”.
6. **`commit --amend` lub `rebase` na rewizjach już wypchniętych.** Prowadzi to do rozjazdu, który
   następnie „naprawia się” wymuszeniem — patrz punkt 4. Historię przepisuj wyłącznie lokalnie,
   przed publikacją.
7. **Praca bezpośrednio na `main` zamiast na gałęzi zadaniowej.** Utrudnia przegląd i wycofanie
   zmian. Zawsze twórz gałąź roboczą.
8. **Ignorowanie konfliktów przez wybór jednej strony w całości.** Mechaniczne `checkout
   --ours`/`--theirs` gubi cudzą logikę. Konflikty rozwiązuj merytorycznie, plik po pliku.
9. **Tworzenie jednej wielkiej rewizji na koniec pracy.** Utrudnia przegląd, `bisect` i selektywne
   wycofywanie. Zatwierdzaj przyrostowo, po każdej spójnej zmianie.
10. **Zakładanie stanu repozytorium zamiast jego sprawdzenia.** Model „pamięta”, że gałąź istnieje
    albo że zmiany są zatwierdzone, choć stan mógł się zmienić. Każdą sesję pracy rozpoczynaj od
    `git status`, `git branch` i `git log --oneline`.
