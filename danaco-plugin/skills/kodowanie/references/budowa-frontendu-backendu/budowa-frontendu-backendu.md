# Budowa frontendu i backendu — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`) oraz
`references/budowa-kodu/budowa-kodu.md` (budowa przyrostowa) i `praktyki-produktowe` (granice
odpowiedzialności, zakaz stylów w logice, zakaz dryfu technologicznego). Ten indeks dodaje standard
wykonania właściwy dla obu warstw aplikacji.

## Karty referencyjne

| Warstwa | Karta | Wczytaj gdy |
| --- | --- | --- |
| Frontend | `references/budowa-frontendu-backendu/frontend.md` | interfejs użytkownika: komponenty, stan, formularze, style, dostępność, wydajność |
| Backend | `references/budowa-frontendu-backendu/backend.md` | warstwa serwerowa: API, logika domenowa, dostęp do danych, uwierzytelnianie, dzienniki |
| Frontend pro | `references/budowa-frontendu-backendu/wzorce-zaawansowane-frontend.md` | stan serwera (odświeżanie, unieważnianie, deduplikacja), aktualizacje optymistyczne, formularze złożone, WebSocket/SSE, wydajność renderowania, granice błędów, i18n, telemetria |
| Backend pro | `references/budowa-frontendu-backendu/wzorce-zaawansowane-backend.md` | pamięć podręczna, zadania w tle i kolejki, odporność na zewnętrzne API, rate limiting, wielodostęp i izolacja klientów, migracje bez przestoju, metryki RED, bezpieczeństwo operacyjne |

Przy budowie pełnej aplikacji wczytaj obie karty podstawowe; łącz z kartą frameworka (`frameworki`:
FastAPI, Node.js, Next.js, Electron) i kartą języka. Karty zaawansowane wczytuj dodatkowo, gdy
zakres zadania wykracza poza podstawy opisane w kartach
`references/budowa-frontendu-backendu/frontend.md` i
`references/budowa-frontendu-backendu/backend.md` — zawsze po wczytaniu karty podstawowej danej
warstwy, nigdy zamiast niej.

## Zasady wspólne obu warstw

1. **Kontrakt najpierw.** Kształt danych wymienianych między frontendem
   a backendem (pola, typy, formaty, błędy) ustala się przed budową którejkolwiek
   warstwy i zapisuje w jednym miejscu (schemat OpenAPI, typy współdzielone).
   Zmiana kontraktu to zmiana jawna, nie skutek uboczny.
2. **Walidacja po obu stronach, prawda po stronie serwera.** Frontend waliduje
   dla wygody użytkownika, backend — dla bezpieczeństwa i spójności danych;
   walidacja frontendowa nigdy nie jest jedyną.
3. **Błędy jako część kontraktu.** Każda operacja ma określone odpowiedzi błędne
   (kody, komunikaty) i frontend je obsługuje — stan ładowania, stan błędu
   i stan pusty projektuje się razem ze stanem szczęśliwym, nie „potem”.
4. **Granica warstw bez przecieków.** Frontend nie zna schematu bazy; backend
   nie formatuje treści pod widok. Wymiana wyłącznie przez kontrakt.
