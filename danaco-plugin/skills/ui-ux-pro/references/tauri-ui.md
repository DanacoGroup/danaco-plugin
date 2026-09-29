# UI aplikacji Tauri — karta

Karta obejmuje różnice między interfejsem aplikacji desktopowej Tauri a stroną WWW:
gęstość układu, zachowania okna, obsługę klawiatury i różnice silnika WebView. Granicę
powłoki i rdzenia opisuje paczka `../most-tauri/SKILL.md`; komponenty i styl —
`references/design-interfejsu.md`.

Sprawdź środowisko, zanim zaczniesz, i nie zakładaj jego stanu:

```bash
cargo tauri --version       # wersja tauri-cli
rustc --version             # wersja kompilatora
pkg-config --modversion webkit2gtk-4.1   # zależności WebView na Linuksie
sccache --version           # pamięć podręczna kompilacji, jeśli używana
```

Frontem buduje Vite. Przyspieszacze kompilacji (sccache, mold, clang) są zalecane, ale
nie są dane z góry — jeśli powyższe polecenia nie odpowiadają, skonfiguruj je albo licz
się z dłuższą kompilacją. Wersje traktuj jako orientacyjne.

## Desktop to nie strona WWW

1. Gęstość natywna: mniejsze fonty bazowe (13–14px), zwarty spacing, brak sekcji hero i
   marketingowych paddingów.
2. Layout aplikacyjny: sidebar/toolbar/statusbar zamiast nagłówka strony; panele z możliwością
   zmiany rozmiaru tam, gdzie użytkownik pracuje długo.
3. Skróty klawiaturowe od pierwszego dnia (paleta komend Ctrl+K jako wzorzec domyślny); pełna
   obsługa focus-visible.
4. Wyłącz zachowania „strony”: `user-select: none` na chrome UI (nie na treści!),
   `overscroll-behavior: none`, brak kontekstowego menu przeglądarki na elementach UI (`contextmenu`
   przechwycony tam, gdzie dajesz własne).
5. Okno: pamiętaj rozmiar/pozycję (plugin `tauri-plugin-window-state`), sensowne
   `minWidth/minHeight` w `tauri.conf.json`, tytuł okna odzwierciedla kontekst (np. nazwę otwartego
   pliku).

## Silnik: webkit2gtk (WebKit, nie Chromium)

1. Sprawdź wersję przed użyciem nowinek CSS: `pkg-config --modversion webkit2gtk-4.1`.
2. Bezpieczny rdzeń: grid, flex, custom properties, `:has()`, container queries (nowsze webkit2gtk);
   ostrożnie z `backdrop-filter` (koszt na GTK) i eksperymentami spoza Baseline.
3. Testuj front w firefox z Playwright jako proxy różnic silników
   (`references/weryfikacja-wizualna.md`) + finalnie realne okno `cargo tauri dev`.

## Wydajność

1. Duże listy (logi, tabele danych) — zawsze wirtualizacja (np. `@tanstack/virtual`).
2. Dane z backendu: paginacja/stream przez komendy Tauri, nie jednorazowy transfer megabajtów przez
   IPC; do dużych transferów użyj kanałów (`tauri::ipc::Channel`).
3. SQLite (3.46 na maszynie) po stronie Rust — front dostaje gotowe, przycięte widoki danych, nie
   surowe tabele.
4. Animacje tylko transform/opacity — WebKitGTK renderuje je na GPU, reszta potrafi klatkować.

## Struktura projektu

```
src/            # front (Vite + TS)
  tokens.css    # wspólny system projektowy
src-tauri/      # Rust: komendy, stan, SQLite
Taskfile.yml    # task dev / task build / task check
```

- `task dev` → `cargo tauri dev`; `task check` → `tsc --noEmit && vitest run && cargo clippy`.
- Ikony aplikacji generuj z jednego SVG: `cargo tauri icon icon.svg` (ImageMagick dostępny do korekt
  rastrów).
- Build produkcyjny: `cargo tauri build` — mold i sccache już skracają kompilację; nie wyłączaj ich.

## Weryfikacja

Po zmianach UI: pętla z `references/weryfikacja-wizualna.md` na dev-serverze Vite (viewporty =
realne rozmiary okna: 1024×700 min, 1440×900 typowe), potem kontrola w realnym oknie Tauri. Czysta
konsola WebView i brak błędów `cargo clippy` to warunek ukończenia.
