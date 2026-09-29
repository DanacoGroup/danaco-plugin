# Frameworki — indeks modułu

Obowiązują standardy zawodowe (`../../wspolne/standardy-zawodowe/standardy-zawodowe.md`). Karty
frameworków stosuj łącznie z kartą języka ze
`references/jezyki-programowania/jezyki-programowania.md` (FastAPI →
`references/jezyki-programowania/python.md`; Node.js, Next.js, Electron →
`references/jezyki-programowania/javascript-typescript.md`).

## Karty referencyjne

| Framework | Karta | Wczytaj gdy |
| --- | --- | --- |
| FastAPI | `references/frameworki/fastapi.md` | budowa lub naprawa API HTTP w Pythonie: trasy, walidacja Pydantic, zależności, OpenAPI |
| Node.js | `references/frameworki/nodejs.md` | kod serwerowy JavaScript/TypeScript poza przeglądarką: procesy, moduły, asynchroniczność |
| Next.js | `references/frameworki/nextjs.md` | aplikacja internetowa Next.js: routing, komponenty serwerowe i klienckie, budowa i wdrożenie |
| Electron | `references/frameworki/electron.md` | aplikacja desktopowa Electron: proces główny i renderujący, komunikacja IPC, pakowanie |

Wczytaj wyłącznie kartę frameworka, z którym prowadzona jest praca.

## Zasady nadrzędne dla wszystkich frameworków

1. **Wersja frameworka ze źródła.** Przed użyciem mechanizmu sprawdź w plikach
   projektu (`requirements.txt`, `package.json`), która wersja frameworka jest
   zainstalowana — interfejsy różnią się między wersjami głównymi, a model LLM
   z pamięci miesza składnię wersji.
2. **Struktura zgodna z konwencją frameworka.** Każdy framework ma przyjęty układ
   katalogów i nazw — stosuj go zamiast układu własnego pomysłu; odstępstwa tylko
   za zgodą właściciela projektu.
3. **Granice warstw bez skrótów.** Logika domenowa nie należy do warstwy tras ani
   komponentów interfejsu; dostęp do bazy nie należy do warstwy prezentacji.
   Szczegóły podziału podaje karta frameworka.
