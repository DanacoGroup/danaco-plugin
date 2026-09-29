# Narzędzia budowy — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`) — w
szczególności zakaz kopii plików `_v2` (wersjonowanie zapewnia Git) oraz wymóg przypinania
zależności do wersji.

## Karty referencyjne

| Narzędzie | Karta | Wczytaj gdy |
| --- | --- | --- |
| Git | `references/narzedzia-budowy/git.md` | rewizje, gałęzie, scalanie, konflikty, historia, `.gitignore`, komunikaty rewizji |
| Docker | `references/narzedzia-budowy/docker.md` | Dockerfile, obrazy, kontenery, docker compose, konteneryzacja aplikacji |
| PowerShell i CMD | `references/narzedzia-budowy/powershell.md` | skrypty administracyjne Windows, automatyzacja, praca w konsoli Windows |
| Menedżery pakietów | `references/narzedzia-budowy/menedzery-pakietow.md` | npm i package.json, pip i requirements, środowiska wirtualne venv, aktualizacja zależności |

Wczytaj wyłącznie kartę narzędzia, którego dotyczy praca.

## Zasady nadrzędne

1. **Polecenia nieodwracalne za zgodą.** Operacje niszczące dane lub historię
   (`git push --force`, `git reset --hard`, `docker system prune`, usuwanie
   wolumenów, `Remove-Item -Recurse`) wykonuj wyłącznie po jawnym potwierdzeniu
   właściciela projektu, z podaniem skutków.
2. **Stan przed działaniem.** Przed operacją na repozytorium sprawdź `git status`
   i bieżącą gałąź; przed operacją na kontenerach — co faktycznie działa
   (`docker ps`). Działanie na stanie wyobrażonym to główne źródło szkód.
3. **Skrypty idempotentne i jawne.** Skrypt budowy lub administracyjny ma dawać
   ten sam skutek przy ponownym uruchomieniu, jawnie zgłaszać błędy (bez połykania
   kodów wyjścia) i nie zależeć od stanu pozostałego po poprzednich uruchomieniach.
