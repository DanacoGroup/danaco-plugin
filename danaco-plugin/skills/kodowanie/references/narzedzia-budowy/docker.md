# Docker — karta

## Procedury podstawowe

W środowisku Windows Docker Desktop uruchamia kontenery linuksowe poprzez zaplecze WSL 2. Przed
rozpoczęciem pracy sprawdź, czy demon działa:
```
docker version
docker info
```

**Dockerfile wielostopniowy.** Buduj obrazy produkcyjne w co najmniej dwóch etapach: etap budowy
zawiera kompilatory i zależności deweloperskie, etap końcowy — wyłącznie artefakty uruchomieniowe.
Przykład dla aplikacji Node:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
USER node
CMD ["node", "dist/main.js"]
```
Porządkuj instrukcje od najrzadziej do najczęściej zmienianych, aby maksymalnie wykorzystać pamięć
podręczną warstw: najpierw pliki manifestów zależności i ich instalacja, dopiero potem kod źródłowy.

**Obrazy.** Buduj, oznaczaj i przeglądaj obrazy jawnie:
```
docker build -t rejestr.example.com/projekt/api:1.4.2 .
docker image ls
docker image history rejestr.example.com/projekt/api:1.4.2
```

**Compose.** Środowisko wielousługowe definiuj w pliku `compose.yaml` (akceptowana jest również
nazwa `docker-compose.yml`). Przykład szkieletu:
```yaml
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: ${DATABASE_URL}
    depends_on:
      - db
  db:
    image: postgres:16
    volumes:
      - dane-db:/var/lib/postgresql/data
volumes:
  dane-db:
```
Steruj środowiskiem poleceniami:
```
docker compose up -d
docker compose ps
docker compose logs -f nazwa-uslugi
docker compose down
```
Konfigurację zależną od środowiska przekazuj przez plik `.env` odczytywany przez Compose; pliku
`.env` nie zatwierdzaj w repozytorium.

## Bezpieczne wzorce

- **Użytkownik nieuprzywilejowany.** Nie uruchamiaj procesu aplikacji jako root. W obrazach Node
  użyj istniejącego użytkownika `node`; w innych utwórz własnego:
  ```dockerfile
  RUN adduser --system --no-create-home appuser
  USER appuser
  ```
- **`.dockerignore`.** Utwórz plik `.dockerignore` w katalogu kontekstu budowy i wyklucz co
  najmniej: `.git`, `node_modules`, `.venv`, `.env`, pliki kluczy i certyfikatów, katalogi wyników
  budowy. Bez tego pliku cały katalog — łącznie z sekretami — trafia do kontekstu budowy i
  potencjalnie do warstw obrazu.
- **Sekrety poza obrazem.** Nie umieszczaj sekretów w instrukcjach `ENV`, `ARG` ani w kopiowanych
  plikach — pozostają w historii warstw. Przekazuj je w czasie uruchomienia (zmienne środowiskowe z
  bezpiecznego magazynu, sekcja `secrets` w Compose) albo w czasie budowy przez `RUN
  --mount=type=secret`, który nie zapisuje treści w warstwie.
- **Przypinanie wersji.** W instrukcji `FROM` wskazuj konkretną wersję obrazu bazowego (np.
  `python:3.12-slim`), nigdy `latest`. Dla obrazów o podwyższonych wymaganiach powtarzalności
  przypinaj skrót: `FROM python:3.12-slim@sha256:<skrot>` — skrót pobierz poleceniem `docker image
  inspect`, nie wpisuj go z pamięci.
- **Woluminy do danych trwałych.** Dane, które mają przetrwać usunięcie kontenera (bazy danych,
  przesłane pliki), przechowuj w nazwanych woluminach zadeklarowanych w Compose, nie w warstwie
  zapisu kontenera.

## Diagnostyka

- **Dzienniki.** `docker logs nazwa-kontenera` wyświetla strumienie wyjścia procesu głównego;
  `docker logs -f --tail 100 nazwa-kontenera` śledzi na bieżąco ostatnie wpisy. W Compose: `docker
  compose logs -f`.
- **Wejście do działającego kontenera.** `docker exec -it nazwa-kontenera sh` (lub `bash`, jeżeli
  jest dostępny). Używaj do inspekcji; zmian konfiguracyjnych wykonanych wewnątrz kontenera nie
  traktuj jako trwałych — wprowadzaj je w Dockerfile lub Compose.
- **Inspekcja.** `docker inspect nazwa-kontenera` zwraca pełną konfigurację (sieci, woluminy,
  zmienne środowiskowe, kod wyjścia). `docker ps -a` pokazuje również kontenery zatrzymane wraz z
  kodami wyjścia — kod `137` oznacza zabicie procesu (często brak pamięci), `126`/`127` — problem z
  poleceniem startowym.
- **Niepowodzenia budowy.** Czytaj komunikat błędu przy konkretnym kroku, nie zgaduj. Najczęstsze
  przyczyny: plik nieobecny w kontekście budowy (wykluczony w `.dockerignore` albo błędna ścieżka
  względem kontekstu), brak dostępu do sieci przy pobieraniu zależności, niezgodność architektury
  obrazu bazowego, przestarzała warstwa z pamięci podręcznej — w ostatnim przypadku przebuduj z
  `docker build --no-cache`, ale dopiero po wykluczeniu innych przyczyn.
- **Sieć i porty.** Konflikt portu na hoście zgłaszany jest przy starcie kontenera; sprawdź zajętość portu na Windows poleceniem `netstat -ano | findstr :8080` i zmień mapowanie `-p host:kontener` zamiast zabijać cudze procesy.

## Operacje nieodwracalne — wymagają zgody właściciela projektu

Nie wykonuj poniższych poleceń bez wyraźnej zgody właściciela projektu udzielonej dla konkretnego
przypadku:

- `docker system prune` (a zwłaszcza `docker system prune -a --volumes`) — usuwa zatrzymane
  kontenery, nieużywane sieci, obrazy i opcjonalnie woluminy w całym środowisku, także te należące
  do innych projektów na tej samej maszynie. Utrata woluminów oznacza utratę danych.
- `docker volume rm` oraz `docker volume prune` — trwale usuwają dane trwałe (bazy danych, pliki
  użytkowników). Danych z usuniętego woluminu nie da się odzyskać.
- `docker compose down -v` — poza zatrzymaniem usług usuwa woluminy zadeklarowane w projekcie;
  skutek jak wyżej.
- `docker rm -f` na kontenerze z danymi w warstwie zapisu — usuwa kontener wraz z niezapisanymi
  danymi.
- `docker rmi` na obrazie oznaczonym jako wdrożony — może uniemożliwić odtworzenie działającej
  wersji, jeżeli obraz nie istnieje w rejestrze.
- `docker push` do rejestru produkcyjnego nadpisujący istniejący znacznik wersji — odbiorcy tego
  samego znacznika otrzymają inną treść niż dotychczas.

## Typowe błędy modeli LLM przy tym narzędziu

1. **`FROM obraz:latest` zamiast przypiętej wersji.** Budowa przestaje być powtarzalna — ten sam
   Dockerfile daje różne obrazy w różnych dniach. Zawsze wskazuj konkretną wersję obrazu bazowego.
2. **`COPY . .` bez `.dockerignore`.** Do obrazu trafiają `.git`, `node_modules`, pliki `.env` i
   klucze. Najpierw utwórz `.dockerignore`, potem kopiuj; kopiuj wąsko (konkretne katalogi), gdy to
   możliwe.
3. **Sekrety w `ENV`, `ARG` lub wklejone do Dockerfile.** Wartości pozostają w historii warstw i
   metadanych obrazu; każdy z dostępem do obrazu je odczyta. Przekazuj sekrety w czasie
   uruchomienia.
4. **Instalacja zależności po skopiowaniu całego kodu.** Każda zmiana kodu unieważnia warstwę
   instalacji zależności i wydłuża budowę. Kopiuj manifesty i instaluj zależności przed skopiowaniem
   źródeł.
5. **Proces aplikacji uruchamiany jako root.** Zbędne rozszerzenie skutków ewentualnego przejęcia
   kontenera. Dodawaj instrukcję `USER` z użytkownikiem nieuprzywilejowanym w etapie końcowym.
6. **„Naprawianie” środowiska przez `docker system prune` lub `--no-cache`.** Model sięga po
   kasowanie zasobów zamiast diagnozy. Najpierw ustal przyczynę (`logs`, `inspect`, komunikat kroku
   budowy); czyszczenie globalne wymaga zgody właściciela projektu.
7. **Mylenie czasu budowy z czasem uruchomienia.** Próby łączenia się z bazą danych w `RUN`,
   oczekiwanie, że zmienne z `docker run -e` będą widoczne podczas budowy. Rozdzielaj: `RUN`
   wykonuje się przy budowie, `CMD`/`ENTRYPOINT` przy starcie kontenera.
8. **Adres `localhost` wewnątrz kontenera wskazujący hosta.** Wewnątrz kontenera `localhost` to sam
   kontener. Między usługami Compose używaj nazw usług; do hosta z Docker Desktop na Windows — nazwy
   `host.docker.internal`.
9. **Dane trwałe w warstwie kontenera.** Usunięcie kontenera usuwa dane. Deklaruj nazwane woluminy
   dla wszystkiego, co ma przetrwać ponowne utworzenie kontenera.
10. **Wymyślanie skrótów `sha256` i nieistniejących znaczników obrazów.** Skróty i znaczniki
    weryfikuj poleceniami (`docker image inspect`, zapytanie do rejestru); nigdy nie wpisuj ich „z
    pamięci”.
