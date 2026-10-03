---
paths:
  - "src/api/**/*.ts"
---
# Reguły API
- Każdy handler waliduje wejście schematem z `src/api/schemas/`.
- Błędy zwracaj formatem `{ "kod": string, "opis": string }` i kodem HTTP 4xx/5xx.
- Nie loguj treści żądań z danymi osobowymi.
