# Next.js — karta

Przeczytaj tę kartę w całości przed rozpoczęciem pracy z kodem Next.js. Karta opisuje App Router
jako standard przyjęty w Danaco. Istnieje również starszy Pages Router (`pages/`) — zastane projekty
mogą go używać i wówczas pracuj w jego konwencjach; nigdy nie mieszaj obu wzorców w jednej
funkcjonalności.

## Struktura projektu

Przyjmij układ z App Routerem i kodem aplikacyjnym poza katalogiem tras:

```
projekt/
├── app/                    # wyłącznie trasy i pliki specjalne
│   ├── layout.tsx          # układ główny (html, body)
│   ├── page.tsx
│   ├── error.tsx           # granica błędów (komponent kliencki)
│   ├── not-found.tsx
│   ├── orders/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx   # segment dynamiczny
│   └── api/.../route.js    # procedury obsługi tras (route handlers)
├── components/             # komponenty wielokrotnego użytku
├── lib/                    # logika domenowa, dostęp do danych, klienci usług
├── public/                 # zasoby statyczne
└── next.config.js
```

Przestrzegaj granic: `app/` zawiera trasy i kompozycję, `components/` — interfejs, `lib/` — logikę i
dostęp do danych. Zapytania do bazy i wywołania usług umieszczaj w `lib/`, importowanym przez
komponenty serwerowe — nie w plikach `page.tsx`. Rozpoznaj router przed pracą: obecność `app/`
oznacza App Router, `pages/` — Pages Router. Nie twórz katalogu `pages/` w projekcie z App Routerem
ani odwrotnie; nie twórz tras API tylko po to, aby komponent serwerowy pobrał dane, które może
pobrać bezpośrednio.

## Konwencje frameworka

- Komponenty serwerowe są domyślne: renderują na serwerze, mogą być `async`, mają dostęp do bazy i
  sekretów, nie mają stanu ani zdarzeń przeglądarki. Dyrektywę `"use client"` dodawaj wyłącznie tam,
  gdzie potrzebne są haki (`useState`, `useEffect`), obsługa zdarzeń lub API przeglądarki.
- Umieszczaj granicę kliencką jak najniżej w drzewie: interaktywny przycisk wydziel jako mały
  komponent kliencki zamiast oznaczać dyrektywą całą stronę. Komponenty serwerowe przekazuj do
  klienckich jako `children` lub właściwości.
- Pobieraj dane w komponentach serwerowych przez `async`/`await` (bezpośrednio z `lib/` lub przez
  `fetch`). Nie stosuj wzorca `useEffect` + `fetch` + stan ładowania tam, gdzie dane może dostarczyć
  serwer.
- Mutacje realizuj przez akcje serwerowe (`"use server"`) z rewalidacją
  (`revalidatePath`/`revalidateTag`) lub przez procedury obsługi w `route.js`. Waliduj wejście
  każdej akcji serwerowej — jest ona publicznym punktem końcowym HTTP.
- Świadomie steruj buforowaniem: określaj zachowanie `fetch` (opcja `cache`, `next.revalidate`,
  znaczniki) i tryb renderowania segmentu (statyczny lub dynamiczny). Nie pozostawiaj strategii
  buforowania przypadkowi.
- Stany ładowania i błędów wyrażaj plikami specjalnymi `loading.tsx` i `error.tsx` oraz granicami
  `Suspense`.
- Używaj `next/link` do nawigacji, `next/image` do obrazów i `next/font` do krojów pisma zamiast
  surowych odpowiedników HTML.
- W Pages Routerze obowiązują inne idiomy: `getServerSideProps`/`getStaticProps`, `pages/api/`, brak
  komponentów serwerowych i dyrektywy `"use client"`. Stosuj je wyłącznie w zastanym kodzie Pages
  Routera.

Wzorzec podziału serwer–klient:

```tsx
// app/orders/page.tsx — komponent serwerowy: dane pobrane bezpośrednio
import { getOrders } from "@/lib/orders";
import { OrderFilter } from "@/components/order-filter";

export default async function OrdersPage() {
  const orders = await getOrders(); // bez trasy API, bez useEffect
  return <OrderFilter orders={orders} />;
}
```

```tsx
// components/order-filter.tsx — wąski komponent kliencki: tylko interakcja
"use client";
import { useState } from "react";

export function OrderFilter({ orders }: { orders: Order[] }) {
  const [query, setQuery] = useState("");
  const visible = orders.filter((order) => order.name.includes(query));
  return (
    <>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      <OrderList orders={visible} />
    </>
  );
}
```

## Konfiguracja i sekrety

- Zmienne środowiskowe bez prefiksu `NEXT_PUBLIC_` są dostępne wyłącznie po stronie serwera. Prefiks
  `NEXT_PUBLIC_` powoduje trwałe wkompilowanie wartości w pakiet kliencki — nigdy nie nadawaj go
  sekretom.
- Sekretów (klucze API, dane dostępowe do bazy) używaj wyłącznie w komponentach serwerowych, akcjach
  serwerowych, procedurach obsługi tras i `lib/`. Nie przekazuj ich przez właściwości do komponentów
  klienckich — właściwości komponentów klienckich są serializowane do przeglądarki.
- Lokalne wartości trzymaj w `.env.local` (nieobecnym w repozytorium); commituj `.env.example` z
  nazwami zmiennych. Nie commituj `.env.local`, katalogów `.next/` i `node_modules/`.
- Konfigurację buduj w `next.config.js`; nie wpisuj tam sekretów, ponieważ plik podlega commitowi.

## Testy

- Testy jednostkowe i komponentów pisz w Vitest (lub Jest, jeżeli projekt już go używa) z React
  Testing Library; konfiguracja wymaga środowiska DOM (jsdom).
- Asynchroniczne komponenty serwerowe testuj przede wszystkim przez wydzieloną logikę: funkcje z
  `lib/` testuj jednostkowo, a pełne strony — testami end-to-end w Playwright na uruchomionej
  aplikacji, ponieważ wsparcie bibliotek komponentowych dla komponentów `async` jest ograniczone.
- Akcje serwerowe i procedury obsługi tras testuj jak funkcje: wywołaj z przygotowanym wejściem i
  sprawdź wynik oraz efekty uboczne na testowej bazie.
- W testach end-to-end pokrywaj krytyczne przepływy (logowanie, formularze mutujące dane) na
  buildzie produkcyjnym (`next build` + `next start`), ponieważ tryb deweloperski maskuje błędy
  buforowania i renderowania statycznego.

Wzorzec akcji serwerowej z walidacją i rewalidacją (do testowania jak zwykłej funkcji):

```tsx
// lib/actions/create-order.ts — akcja serwerowa jest publicznym endpointem
"use server";

export async function createOrder(formData: FormData) {
  const parsed = orderSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { error: "Niepoprawne dane formularza" };
  }
  const user = await requireUser(); // autoryzacja wewnątrz akcji, zawsze
  await insertOrder(user.id, parsed.data);
  revalidatePath("/orders"); // bez rewalidacji lista pozostanie przestarzała
  return { ok: true };
}
```

## Diagnostyka

- Błąd hydratacji („hydration failed”, „text content does not match”) oznacza rozbieżność między
  HTML z serwera a pierwszym renderem klienta. Typowe przyczyny: `Date.now()`/`Math.random()` w
  renderze, formatowanie zależne od ustawień regionalnych, odczyt `window`/`localStorage` podczas
  renderu, niepoprawne zagnieżdżenie HTML, ingerencja rozszerzeń przeglądarki. Porównaj nakładkę
  błędu z komponentem i usuń źródło niedeterminizmu; wartości wyłącznie klienckie renderuj po
  montażu.
- Rozróżniaj miejsca wykonania: dziennik komponentów serwerowych trafia do terminala procesu Next,
  dziennik komponentów klienckich — do konsoli przeglądarki. Szukaj komunikatu tam, gdzie kod
  faktycznie działa.
- Błąd „Functions cannot be passed directly to Client Components” oznacza przekazanie niedozwolonej
  wartości przez granicę serwer–klient; przekazuj wyłącznie dane serializowalne lub akcje serwerowe.
- Przestarzałe dane po mutacji to niemal zawsze brak rewalidacji (`revalidatePath`/`revalidateTag`)
  lub niezamierzone buforowanie `fetch` — sprawdź strategię buforowania, zanim podejrzewasz bazę.
- Zachowanie różniące się między `next dev` a buildem produkcyjnym diagnozuj na buildzie (`next
  build && next start`); wynik `next build` wskazuje, które trasy są statyczne, a które dynamiczne.

## Typowe błędy modeli LLM w tym frameworku

1. **`"use client"` wszędzie.** Dyrektywa dodawana odruchowo do każdego pliku niweczy renderowanie
   serwerowe, powiększa pakiet kliencki i odcina komponent od danych serwerowych. Dodawaj ją tylko
   przy rzeczywistej potrzebie (stan, zdarzenia, API przeglądarki) i możliwie nisko w drzewie.
2. **Mieszanie wzorców Pages i App Routera.** `getServerSideProps` lub `getStaticProps` w plikach
   `app/`, `next/router` zamiast `next/navigation`, `pages/api/` obok `app/api/*/route.js`. Przed
   pracą ustal router obowiązujący w projekcie i używaj wyłącznie jego API.
3. **`useEffect` + `fetch` do danych dostępnych na serwerze.** Odtwarza wzorzec klasycznego SPA:
   dodatkowe żądanie, migotanie stanu ładowania, ekspozycja punktu końcowego. Pobierz dane w
   komponencie serwerowym przez `await` i przekaż w dół.
4. **Sekrety w kodzie klienckim.** Użycie klucza API w komponencie z `"use client"` lub nadanie
   sekretowi prefiksu `NEXT_PUBLIC_` publikuje go w przeglądarce. Sekrety pozostają w kodzie
   serwerowym; klient komunikuje się przez akcje serwerowe lub procedury obsługi tras.
5. **Halucynowane API.** Nieistniejące eksporty `next/*`, zmyślone opcje `next.config.js`, haki
   serwerowe wywoływane w komponentach klienckich (`cookies()`, `headers()`), API z innych
   metaframeworków. W razie niepewności zweryfikuj istnienie API w dokumentacji lub w kodzie
   projektu.
6. **Niewalidowane akcje serwerowe.** Akcja serwerowa przyjmująca dane formularza bez walidacji i
   autoryzacji to otwarty punkt końcowy mutujący dane. Waliduj wejście (np. schematem) i sprawdzaj
   uprawnienia wewnątrz każdej akcji.
7. **Ignorowanie semantyki buforowania.** Założenie, że każde żądanie wykona kod od nowa, podczas
   gdy segmenty statyczne i buforowane `fetch` serwują dane zapisane podczas builda. Po mutacji
   rewaliduj; dla danych na żądanie jawnie wymuś tryb dynamiczny lub wyłącz buforowanie.
8. **Niedeterministyczny render powodujący błędy hydratacji.** Bieżący czas, wartości losowe lub
   odczyt `window` w ciele komponentu współdzielonego przez serwer i klienta. Wartości zależne od
   przeglądarki wyznaczaj w `useEffect` po montażu.
9. **Trasa API jako pośrednik dla własnego serwera.** Tworzenie `route.js`, które komponent
   serwerowy odpytuje przez `fetch` na własny adres, zamiast bezpośredniego wywołania funkcji z
   `lib/`. Warstwa HTTP między dwoma fragmentami kodu serwerowego jest zbędna.
10. **Znaczniki `<a>`, `<img>` i ręczne `<head>` zamiast mechanizmów frameworka.** Utrata nawigacji
    klienckiej, optymalizacji obrazów i poprawnych metadanych. Używaj `next/link`, `next/image` oraz
    eksportu `metadata`/`generateMetadata`.
