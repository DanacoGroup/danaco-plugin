# Przegląd migracji — <gałąź>

| Ryzyko | Waga | Dowód | Poprawka |
|---|---|---|---|
| Usunięcie kolumny `email` używanej w `user_service.py` | krytyczna | `migrations/0042.sql:3` | wycofać użycie w tym wydaniu, usunąć kolumnę w następnym |

Werdykt: **nie scalać** / **scalić po poprawkach** / **scalić**.
