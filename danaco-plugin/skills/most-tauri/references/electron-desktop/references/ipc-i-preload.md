# IPC i preload

Odniesienie: Electron 43.2.0. `contextIsolation: true` i `sandbox: true` przyjęte jako
domyślne — cały ten plik zakłada ten tryb.

## Trzy kierunki komunikacji i kiedy który

| Wzorzec | API | Kiedy |
| --- | --- | --- |
| renderer → main, z odpowiedzią | `ipcRenderer.invoke` / `ipcMain.handle` | 90 % przypadków: „zapisz plik”, „daj listę”, „otwórz dialog” |
| renderer → main, bez odpowiedzi | `ipcRenderer.send` / `ipcMain.on` | telemetria, zdarzenia UI, „zamknij okno” |
| main → renderer | `webContents.send` / `ipcRenderer.on` | postęp operacji, zmiana motywu systemu, powiadomienie o aktualizacji |
| renderer ↔ renderer / utility | `MessageChannelMain` + `postMessage` | duże strumienie danych, pominięcie procesu głównego |

**Nie używaj `ipcRenderer.sendSync`.** Blokuje renderer do czasu odpowiedzi procesu
głównego; przy jednoczesnym `dialog.showMessageBox` w mainie masz zakleszczenie. Jedyny
uzasadniony przypadek: odczyt jednej wartości konfiguracyjnej przed pierwszym renderem,
i nawet wtedy lepiej wstrzyknąć ją przez `additionalArguments` w `webPreferences`.

## Preload — poprawny kształt

```ts
// src/preload.ts  (budowany do CJS!)
import { contextBridge, ipcRenderer } from 'electron';

// Kontrakt jest wąski i konkretny. Żadnych generycznych "invoke(kanal, ...args)".
const api = {
  dokument: {
    otworz: (): Promise<{ sciezka: string; tresc: string } | null> =>
      ipcRenderer.invoke('dokument:otworz'),
    zapisz: (sciezka: string, tresc: string): Promise<void> =>
      ipcRenderer.invoke('dokument:zapisz', { sciezka, tresc }),
    ostatnie: (): Promise<string[]> => ipcRenderer.invoke('dokument:ostatnie'),
  },
  aplikacja: {
    wersja: (): Promise<string> => ipcRenderer.invoke('aplikacja:wersja'),
    otworzZewnetrznie: (url: string): Promise<void> =>
      ipcRenderer.invoke('aplikacja:otworz-zewnetrznie', url),
  },
  // subskrypcja zdarzeń z main: zwracamy funkcję odsubskrybowania
  naPostep: (cb: (procent: number) => void): (() => void) => {
    const handler = (_e: Electron.IpcRendererEvent, procent: number) => cb(procent);
    ipcRenderer.on('operacja:postep', handler);
    return () => ipcRenderer.removeListener('operacja:postep', handler);
  },
} as const;

contextBridge.exposeInMainWorld('danaco', api);

export type DanacoApi = typeof api;
```

Cztery rzeczy, które ten kod robi dobrze:

1. **Nie wystawia `ipcRenderer`.** Wystawia funkcje o ustalonych nazwach kanałów.
2. **Zdarzenie z main nie przekazuje obiektu `event` do renderera.** Obiekt `IpcRendererEvent`
   zawiera `sender` — wyciek przez `contextBridge` byłby dziurą.
3. **Zwraca funkcję odsubskrybowania.** Bez tego React w `useEffect` nabija listenery przy
   każdym renderze i po minucie masz ostrzeżenie `MaxListenersExceededWarning`.
4. **Eksportuje typ**, którego użyje renderer.

```ts
// src/renderer/global.d.ts
import type { DanacoApi } from '../preload';
declare global { interface Window { danaco: DanacoApi } }
export {};
```

## Wzorce błędne — z konsekwencją

```ts
// BŁĄD 1: generyczny most
contextBridge.exposeInMainWorld('api', {
  invoke: (kanal: string, ...args: unknown[]) => ipcRenderer.invoke(kanal, ...args),
});
```
Konsekwencja: dowolny skrypt na stronie (wstrzyknięty przez XSS, reklamę, rozszerzenie)
woła `api.invoke('plik:usun', '/')`. Cała lista twoich kanałów staje się publicznym API.

```ts
// BŁĄD 2: wystawienie modułu Node
import fs from 'node:fs';
contextBridge.exposeInMainWorld('fs', fs);
```
Konsekwencja: `contextBridge` i tak nie przeniesie tego poprawnie (funkcje z prototypami
gubią kontekst), a to, co przeniesie, daje stronie odczyt i zapis całego dysku z prawami
użytkownika. Przy `sandbox: true` `node:fs` w ogóle nie jest dostępny w preloadzie —
i to jest dobra wiadomość.

```ts
// BŁĄD 3: nodeIntegration zamiast preloadu
new BrowserWindow({ webPreferences: { nodeIntegration: true, contextIsolation: false } });
```
Konsekwencja: `require('child_process').exec` dostępne z konsoli DevTools i z każdego
skryptu na stronie. To jest domyślna konfiguracja z tutoriali sprzed 2020 i główne
źródło CVE w aplikacjach Electronowych.

```ts
// BŁĄD 4: @electron/remote
import { getCurrentWindow } from '@electron/remote';
getCurrentWindow().setTitle('x');
```
Konsekwencja: renderer trzyma proxy do obiektów procesu głównego; każdy string, który
przejdzie do tego proxy, jest wykonywany w kontekście uprzywilejowanym. Moduł został
wyjęty z rdzenia w E14 właśnie z tego powodu. Dodatkowo każde wywołanie to synchroniczny
round-trip — przy 60 fps animacji tytułu masz 60 blokad procesu głównego na sekundę.

```ts
// BŁĄD 5: przekazywanie funkcji przez contextBridge w drugą stronę bez sprzątania
contextBridge.exposeInMainWorld('api', {
  naZmiane: (cb: Function) => ipcRenderer.on('zmiana', (_e, v) => cb(v)),
});
```
Konsekwencja: brak `removeListener` = wyciek pamięci i wielokrotne wywołania po
przeładowaniu renderera. Zawsze zwracaj funkcję odsubskrybowania (patrz wzorzec wyżej).

## `ipcMain.handle` — walidacja i błędy

```ts
// src/main/ipc.ts
import { ipcMain, BrowserWindow, shell, dialog } from 'electron';
import { z } from 'zod';
import fs from 'node:fs/promises';
import path from 'node:path';

const DOZWOLONY_ORIGIN = 'file://';   // albo 'app://' przy własnym protokole

/** Każdy handler przechodzi przez to opakowanie. */
function bezpiecznyHandler<W, O>(
  kanal: string,
  schema: z.ZodType<W>,
  fn: (dane: W, okno: BrowserWindow) => Promise<O>,
) {
  ipcMain.handle(kanal, async (event, surowe) => {
    // 1. skąd przyszło
    const ramka = event.senderFrame;
    if (!ramka || !ramka.url.startsWith(DOZWOLONY_ORIGIN)) {
      throw new Error(`IPC ${kanal}: odrzucone źródło ${ramka?.url}`);
    }
    // 2. tylko główna ramka, nie osadzone iframe
    if (ramka !== event.sender.mainFrame) {
      throw new Error(`IPC ${kanal}: wywołanie z podramki`);
    }
    // 3. kształt danych
    const wynik = schema.safeParse(surowe);
    if (!wynik.success) throw new Error(`IPC ${kanal}: złe argumenty`);
    // 4. kontekst okna
    const okno = BrowserWindow.fromWebContents(event.sender);
    if (!okno) throw new Error(`IPC ${kanal}: brak okna`);
    return fn(wynik.data, okno);
  });
}

const ZapisSchema = z.object({
  sciezka: z.string().min(1).max(4096),
  tresc: z.string().max(50 * 1024 * 1024),
});

bezpiecznyHandler('dokument:zapisz', ZapisSchema, async ({ sciezka, tresc }) => {
  // 5. ścieżka MUSI być zwalidowana wobec katalogu bazowego
  const bazowy = await fs.realpath(katalogDokumentow);
  const docelowy = path.resolve(bazowy, sciezka);
  if (!docelowy.startsWith(bazowy + path.sep)) {
    throw new Error('Ścieżka poza katalogiem roboczym');
  }
  await fs.writeFile(docelowy, tresc, 'utf8');
});
```

**Dlaczego `senderFrame`, a nie `sender`:** `event.sender` to `WebContents` całego okna.
Jeśli w oknie jest `<iframe>` z obcą domeną, wywołanie z tego iframe ma ten sam `sender`,
ale inne `senderFrame`. Bez sprawdzenia ramki reklama w osadzonej stronie woła twoje API.

**Dlaczego `realpath` przed `resolve`:** bez tego dowiązanie symboliczne w katalogu
roboczym wyprowadza poza sprawdzany prefiks. Klasyczne obejście walidacji ścieżki.

**Błędy przechodzą przez IPC jako `Error` z zachowanym `message`, ale bez `stack`
i bez własnych pól.** Jeśli renderer ma rozróżniać przyczyny, koduj je w `message`
albo zwracaj wynik dyskryminowany:

```ts
type Wynik<T> = { ok: true; dane: T } | { ok: false; kod: 'BRAK_PLIKU' | 'BRAK_PRAW' | 'INNE'; opis: string };
```

To jest lepsze niż rzucanie wyjątków przez IPC, bo typ błędu przeżywa serializację.

## Serializacja — co przechodzi przez IPC

IPC używa **Structured Clone Algorithm**, nie JSON. Konsekwencje:

| Typ | Przechodzi | Uwaga |
| --- | --- | --- |
| `string`, `number`, `boolean`, `null`, `undefined` | tak | |
| `Date`, `RegExp`, `Map`, `Set` | tak | |
| `ArrayBuffer`, `TypedArray`, `Blob` | tak | kopiowane, nie transferowane (poza `MessagePort`) |
| zwykły obiekt, tablica | tak | cykle są obsługiwane |
| funkcja | **nie** | `Error: An object could not be cloned` |
| klasa z metodami | **częściowo** | przechodzą tylko własne pola, prototyp ginie |
| `Symbol` | **nie** | |
| `Error` | tak, ale | tylko `name` i `message`; własne pola giną |
| `Buffer` (Node) | tak | dociera jako `Uint8Array`, nie `Buffer` |

Najczęstsza awaria: przekazanie obiektu z Prisma/ORM-a, który ma gettery i metody —
zserializuje się jako pusty obiekt albo rzuci. Zawsze konwertuj do zwykłego obiektu
(`structuredClone` po `JSON.parse(JSON.stringify(x))` nie wystarczy dla `Date` — zrób
jawne mapowanie DTO).

## Duże dane i strumienie

Trzy progi:

**< 1 MB — zwykły `invoke`.** Kopiowanie jest szybsze niż jakikolwiek sprytny mechanizm.

**1-100 MB — `invoke` zwracający `Uint8Array`.** Structured clone kopiuje bufor raz.
Nie zamieniaj na base64 — rośnie o 33 % i kosztuje CPU po obu stronach.

**> 100 MB albo strumień — `MessagePort` z transferem albo ścieżka do pliku.**

```ts
// main: przekazujemy port do renderera, dane płyną z utility process
import { MessageChannelMain } from 'electron';

ipcMain.handle('eksport:start', async (event, { format }: { format: 'csv' | 'pdf' }) => {
  const { port1, port2 } = new MessageChannelMain();
  const worker = utilityProcess.fork(sciezkaEksportera);
  worker.postMessage({ typ: 'start', format }, [port1]);
  event.sender.postMessage('eksport:port', null, [port2]);
});
```

```ts
// preload: odbieramy port i wystawiamy strumień jako async iterator
ipcRenderer.on('eksport:port', (event) => {
  const [port] = event.ports;
  port.start();
  port.onmessage = (e) => { /* e.data to Uint8Array kawałka */ };
});
```

Transfer przez `MessagePort` z listą transferowalnych obiektów przenosi bufor **bez
kopiowania** — po transferze bufor po stronie nadawcy jest odłączony (`byteLength === 0`).

**Alternatywa, często lepsza:** zapisz wynik do pliku w `app.getPath('temp')` i przekaż
ścieżkę. Renderer czyta przez `fetch('file://...')` (jeśli nie wyłączyłeś fuse
`grantFileProtocolExtraPrivileges`) albo przez własny protokół `app://`. Dla eksportu
100 MB CSV to jest szybsze niż jakikolwiek IPC i nie obciąża pamięci procesu głównego.

## Typowanie kanałów w TypeScript

Jedna mapa kanałów, z niej wyprowadzone typy dla obu stron. Plik współdzielony przez
main i preload:

```ts
// src/shared/kanaly.ts
export type Kanaly = {
  'dokument:otworz': { arg: void; wynik: { sciezka: string; tresc: string } | null };
  'dokument:zapisz': { arg: { sciezka: string; tresc: string }; wynik: void };
  'dokument:ostatnie': { arg: void; wynik: string[] };
  'aplikacja:wersja': { arg: void; wynik: string };
  'aplikacja:otworz-zewnetrznie': { arg: string; wynik: void };
};

export type Zdarzenia = {
  'operacja:postep': number;
  'aktualizacja:gotowa': { wersja: string };
  'motyw:zmiana': 'jasny' | 'ciemny';
};

export type NazwaKanalu = keyof Kanaly;
export type Arg<K extends NazwaKanalu> = Kanaly[K]['arg'];
export type Wynik<K extends NazwaKanalu> = Kanaly[K]['wynik'];
```

```ts
// src/main/typowane-ipc.ts
import { ipcMain, type IpcMainInvokeEvent, type WebContents } from 'electron';
import type { Kanaly, NazwaKanalu, Arg, Wynik, Zdarzenia } from '../shared/kanaly';

export function obsluz<K extends NazwaKanalu>(
  kanal: K,
  fn: (event: IpcMainInvokeEvent, arg: Arg<K>) => Promise<Wynik<K>> | Wynik<K>,
): void {
  ipcMain.handle(kanal, fn as never);
}

export function wyslij<K extends keyof Zdarzenia>(
  wc: WebContents, kanal: K, dane: Zdarzenia[K],
): void {
  wc.send(kanal, dane);
}
```

```ts
// src/preload.ts
import { ipcRenderer, contextBridge } from 'electron';
import type { NazwaKanalu, Arg, Wynik, Zdarzenia } from './shared/kanaly';

function wolaj<K extends NazwaKanalu>(kanal: K, arg: Arg<K>): Promise<Wynik<K>> {
  return ipcRenderer.invoke(kanal, arg);
}

const api = {
  otworzDokument: () => wolaj('dokument:otworz', undefined),
  zapiszDokument: (sciezka: string, tresc: string) =>
    wolaj('dokument:zapisz', { sciezka, tresc }),
  naZdarzenie: <K extends keyof Zdarzenia>(kanal: K, cb: (d: Zdarzenia[K]) => void) => {
    const h = (_e: unknown, d: Zdarzenia[K]) => cb(d);
    ipcRenderer.on(kanal, h);
    return () => { ipcRenderer.removeListener(kanal, h); };
  },
};
contextBridge.exposeInMainWorld('danaco', api);
export type DanacoApi = typeof api;
```

Efekt: literówka w nazwie kanału to błąd kompilacji, a nie cicha `Promise`, która nigdy
się nie rozwiązuje (`invoke` na nieobsłużony kanał odrzuca dopiero z komunikatem
„No handler registered”, i to tylko wtedy, gdy ktoś ten komunikat czyta).

**Uwaga o typie zwracanym przez `contextBridge`:** most **nie przenosi typów**. Typ
w `window.danaco` jest deklaracją, której nikt nie sprawdza w runtime. Dlatego walidacja
po stronie main jest obowiązkowa mimo typowania.

## Zdarzenia main → renderer

```ts
// main: postęp długiej operacji
async function przetworzPliki(wc: WebContents, pliki: string[]) {
  for (let i = 0; i < pliki.length; i++) {
    await przetworzJeden(pliki[i]);
    if (!wc.isDestroyed()) {
      wc.send('operacja:postep', Math.round(((i + 1) / pliki.length) * 100));
    }
  }
}
```

`wc.isDestroyed()` przed każdym `send` — bez tego zamknięcie okna w trakcie operacji
rzuca `Object has been destroyed` w procesie głównym i wywala aplikację.

**Rozgłoszenie do wszystkich okien:**

```ts
import { webContents } from 'electron';
function rozglos<K extends keyof Zdarzenia>(kanal: K, dane: Zdarzenia[K]) {
  for (const wc of webContents.getAllWebContents()) {
    if (!wc.isDestroyed() && wc.getType() === 'window') wc.send(kanal, dane);
  }
}
```

Filtr `getType() === 'window'` pomija `WebContentsView` osadzające obce strony — nie chcesz
wysyłać wewnętrznych zdarzeń do cudzych witryn.

## Testowanie IPC

Handlery pisz jako czyste funkcje, `ipcMain.handle` tylko je podpina:

```ts
// src/main/uslugi/dokumenty.ts — testowalne bez Electrona
export async function zapiszDokument(dane: { sciezka: string; tresc: string }, bazowy: string) { /* ... */ }

// src/main/ipc.ts — cienka warstwa
bezpiecznyHandler('dokument:zapisz', ZapisSchema, (d) => zapiszDokument(d, katalogDokumentow));
```

Do testów end-to-end: Playwright ma wsparcie dla Electrona (`_electron.launch`),
`app.evaluate()` daje dostęp do procesu głównego z testu. Szczegóły uruchamiania testów —
`../kodowanie/references/engineering-core/07-debug-testy-deploy/przeglad.md`.
