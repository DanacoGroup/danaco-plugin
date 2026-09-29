---
name: kodowanie
description: >
  Pisanie, budowa i debugowanie kodu według standardów zawodowych Danaco: karty 20 języków,
  frameworki (FastAPI, Node.js, Next.js, Electron), PostgreSQL/SQLite, Git, Docker,
  PowerShell, serwery MCP. Stosuj, gdy trzeba napisać, poprawić lub zrefaktoryzować kod,
  zbudować projekt, aplikację, API, bazę danych albo serwer MCP, oraz przy błędzie, śladzie
  stosu, awarii i regresji — gdy pada „nie działa”, „napraw to”, „dlaczego wyrzuca wyjątek”,
  „jak to zbudować”. Ta paczka daje rzemiosło języka i frameworka. Reguły komentarzy, tonu
  i zakresu zmiany prowadzi `dyscyplina-inzynierska`, nazwy `standardy-nazewnictwa`, ocenę
  gotowego kodu `kontrola-jakosci`, a orientację w repozytorium Danaco Console
  `praca-w-duzym-repo` — w tym repozytorium stosuj je razem z tą paczką, nie zamiast niej.
---

# Kodowanie

## Kiedy stosować

Stosuj, gdy trzeba napisać, poprawić lub zrefaktoryzować kod, zbudować projekt, aplikację,
API, bazę danych albo serwer MCP, a także przy błędzie, śladzie stosu, awarii i regresji.

Nie stosuj tej paczki do oceny gotowego kodu raportem ustaleń — to `kontrola-jakosci`. Reguł
komentarzy, tonu i zakresu zmiany nie ustala ta paczka, lecz `dyscyplina-inzynierska`; nazw —
`standardy-nazewnictwa`; orientacji i zasięgu zmiany w repozytorium Danaco Console —
`praca-w-duzym-repo`; kształtu danych przechodzących granicę Go↔TypeScript —
`kontrakt-zrodlo-prawdy`. W repozytorium Danaco Console te paczki stosuje się razem z tą,
nie zamiast niej.

## Procedura wczytywania modułów

Moduły mieszkają w katalogu `references/` — wczytuj wyłącznie te potrzebne bieżącemu
zadaniu, według tabel poniżej.

1. **Zawsze najpierw** wczytaj `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` —
   siedem zasad dyscypliny zawodowej i kontrola końcowa. Obowiązują przy każdej pracy
   z kodem; pozostałe moduły je zakładają.
2. Następnie wczytaj moduł procedury właściwy dla rodzaju zadania (tabela A).
3. Następnie wczytaj kartę technologii, w której prowadzona jest praca (tabela B).
4. Karty pogłębione danego modułu wczytuj według tabeli „Karty referencyjne” wewnątrz pliku
   głównego modułu — nie wczytuj wszystkich kart modułu naraz.

## Tabela A — procedury pracy

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Standardy zawodowe | `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` | zawsze, przy każdej pracy z kodem |
| Budowa kodu | `references/budowa-kodu/budowa-kodu.md` | nowy kod, funkcja, moduł, projekt od zera, refaktoryzacja |
| Debugowanie | `references/debugowanie/debugowanie.md` | komunikat błędu, ślad stosu, awaria, regresja, „nie działa” |
| Frontend i backend | `references/budowa-frontendu-backendu/budowa-frontendu-backendu.md` | budowa interfejsu użytkownika, warstwy serwerowej z API albo pełnej aplikacji |
| Serwery MCP | `references/budowa-serwerow-mcp/budowa-serwerow-mcp.md` | budowa lub naprawa serwera MCP, projektowanie narzędzi dla modelu LLM |

## Tabela B — karty technologii

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Języki programowania | `references/jezyki-programowania/jezyki-programowania.md` | przed pierwszą linią kodu w danym języku — spis 20 kart języków ze ścieżkami |
| Frameworki | `references/frameworki/frameworki.md` | praca z FastAPI, Node.js, Next.js lub Electron |
| Bazy danych | `references/bazy-danych/bazy-danych.md` | schematy, zapytania, migracje, wydajność i eksploatacja PostgreSQL lub SQLite |
| Narzędzia budowy | `references/narzedzia-budowy/narzedzia-budowy.md` | Git, Docker, PowerShell/CMD, menedżery pakietów |

## Tabela C — rozszerzenie engineering-core

Spis wszystkich plików tego rozszerzenia wraz z regułą wczytania:
**`references/engineering-core/spis.md`**. Zacznij od niego, a nie od listowania katalogów.

| Moduł | Plik główny | Wczytaj gdy |
|---|---|---|
| Python w produkcji | `references/engineering-core/02-python-backend-dane/przeglad.md` | FastAPI/Starlette, asyncio, Pydantic v2, SQLAlchemy 2.x, polars/pandas, pytest, uv |
| Bazy i RAG | `references/engineering-core/04-bazy-i-rag/przeglad.md` | schemat i wydajność Postgresa, pgvector, potok RAG, fragmentacja, reranking, przypisy |
| Usługi sieciowe | `references/engineering-core/05-uslugi-sieciowe/przeglad.md` | serwer pocztowy, SPF/DKIM/DMARC, SIP/Asterisk, WebSocket/WebRTC/TURN, TLS/DNS/proxy |
| Integracje PL/EU | `references/engineering-core/06-integracje-pl-eu/przeglad.md` | e-Doręczenia, KSeF, PSD2, podpis kwalifikowany, bramki płatnicze, rejestry publiczne |
| Debug, testy, wdrożenia | `references/engineering-core/07-debug-testy-deploy/przeglad.md` | metoda debugowania, strategia testów, obserwowalność, wdrożenie, reakcja na awarię |

To rozszerzenie niesie najświeższy materiał wersyjny w tej paczce (przypięte wersje
bibliotek, API usunięte w bieżących wydaniach). Traktuj je jako uzupełnienie kart języków
i frameworków, nie ich zamiennik.

## Odwołania między modułami

W treściach modułów odwołania do „skilla X” oznaczają moduł `X` tej paczki. Siedem modułów
należy do innych paczek pluginu i wymaga wybrania tamtej paczki: `przeglad-kodu`
i `audyt-jakosci` (paczka `kontrola-jakosci`), `architektura`, `dokumentacja-techniczna`
i `praktyki-produktowe` (paczka `architektura-i-dokumentacja`), `dokumentacja-designu`
i `agentic-ux` (paczka `design-systemowy`). Gdy zadanie wchodzi w ich zakres, zastosuj zasady
ogólne ze standardów zawodowych i wskaż właścicielowi projektu właściwą paczkę.

## Narzędzie: quality_gate.sh

`quality_gate.sh` wykrywa rodzaj projektu po plikach znacznikowych (`go.mod`, `package.json`,
`Cargo.toml`, `requirements.txt`/`pyproject.toml`) i uruchamia dla każdego odpowiednie
budowanie, lint i testy — pomijając z ostrzeżeniem narzędzia, których nie ma na maszynie,
zamiast przerywać całość.

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/kodowanie/scripts/quality_gate.sh" <katalog>
```

Kod wyjścia `0` gdy wszystkie uruchomione kroki przeszły, `1` gdy którykolwiek zawiódł.
Wpinaj w bramkę akceptacji obok kontroli kontraktu i dyscypliny.

## Kryteria zakończenia

Kod jest gotowy, gdy zachodzą wszystkie cztery warunki:

- projekt się buduje, a `quality_gate.sh` na dotkniętym katalogu zwraca `0`;
- testy dotyczące zmienionego obszaru przechodzą, a przy naprawie błędu istnieje test, który
  bez poprawki zawodzi;
- kontrola dyscypliny i nazewnictwa zwraca `0` albo `2`
  (`${CLAUDE_PLUGIN_ROOT}/scripts/mass_actions.py verify <ścieżki>`);
- zakres zmiany odpowiada zadaniu — bez refaktoryzacji przy okazji i kodu „na przyszłość”.

## Materiały

- `../../wspolne/standardy-zawodowe/standardy-zawodowe.md` — siedem zasad dyscypliny
  zawodowej, obowiązkowa kolejność
- `../../wspolne/standardy-zawodowe/katalog-antywzorcow.md` — antywzorce pracy z kodem
- `../../wspolne/standardy-zawodowe/jezyk-zawodowy.md` — język i ton opracowań zawodowych
- `../../wspolne/standardy-zawodowe/kontrola-jakosci-pracy.md` — kontrola końcowa
- `references/engineering-core/spis.md` — spis rozszerzenia engineering-core
- `${CLAUDE_PLUGIN_ROOT}/skills/kodowanie/scripts/quality_gate.sh` — bramka budowy, lintu
  i testów

## Rozgraniczenie z paczkami sąsiednimi

- `dyscyplina-inzynierska` — reguły prowadzenia pliku: komentarze, ton, zakres zmiany.
- `standardy-nazewnictwa` — nazwy plików, zmiennych, typów, komponentów i etykiet.
- `kontrola-jakosci` — ocena gotowego kodu i raport ustaleń.
- `praca-w-duzym-repo` — gdzie zmiana należy i jaki ma zasięg w Danaco Console.
- `kontrakt-zrodlo-prawdy` — kształt danych przechodzących granicę procesu lub języka.
- `ui-ux-pro` — wykonanie interfejsu klienta Danaco Console.
