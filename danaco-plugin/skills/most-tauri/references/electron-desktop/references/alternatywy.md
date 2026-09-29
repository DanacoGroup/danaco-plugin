# Alternatywy dla Electrona — karta

Karta zestawia Electron z pozostałymi drogami zbudowania aplikacji desktopowej i podaje
kryteria wyboru. Powłokę produktu Danaco Console (Tauri 2) opisuje
`SKILL.md` tej paczki; pozostałe karty modułu wymienia
`references/electron-desktop/electron-desktop.md`.

Wersje narzędzi i bibliotek przywołane w tej karcie traktuj jako orientacyjne — stan
faktyczny sprawdzaj w środowisku projektu i w dokumentacji oficjalnej.

Cała tabela porównawcza wygasa razem z wersjami — przed decyzją sprawdź bieżące wydania
u dostawców, a nie w tej karcie.

Stan na sierpień 2026. Wersje sprawdzone: `tauri` 2.11.5 / `@tauri-apps/cli` 2.11.4
(2026-06/07), Wails v2 stabilny + **v3 w becie** (wymaga Go 1.25+), `@neutralinojs/neu`
11.7.2 (2026-06), Electron 43.2.0.

## Tabela porównawcza

| Kryterium | Electron 43 | Tauri 2.11 | Wails v2 / v3-beta | Neutralino 11.7 | PWA | .NET MAUI |
| --- | --- | --- | --- | --- | --- | --- |
| Silnik renderujący | własny Chromium 150 | systemowy: WebView2 / WKWebView / WebKitGTK | jw. | jw. | przeglądarka użytkownika | natywne kontrolki (Blazor Hybrid = WebView) |
| Język warstwy systemowej | JS/TS (Node 24) | Rust | Go | C++ (mały rdzeń), logika w JS | brak | C# |
| Instalator (hello world) | ~90-110 MB | ~3-10 MB | ~8-15 MB | ~2-3 MB | 0 | ~30-60 MB |
| Instalator realnej aplikacji | 120-250 MB | 10-30 MB | 15-40 MB | 5-15 MB | 0 | 60-120 MB |
| RAM, 1 okno, spoczynek | 150-250 MB | 60-120 MB | 70-130 MB | 50-100 MB | jak karta przeglądarki | 80-150 MB |
| RAM, 6 okien | ~409 MB (pomiar publiczny) | ~172 MB (ten sam pomiar) | zbliżony do Tauri | niższy | — | — |
| Spójność renderowania między systemami | **pełna** | **brak** — trzy różne silniki | brak | brak | brak | n/d |
| Czas budowania (przyrostowy) | ~15 s | ~80 s pierwszy raz, potem szybciej | średni | szybki | 0 | średni |
| Dostęp natywny gotowy | bardzo szeroki (menu, tray, dialogi, protokoły, `webRequest`, rozszerzenia) | szeroki, ale węższy; brak `webRequest`, brak rozszerzeń | średni | wąski | znikomy | pełny (to jest natywny stack) |
| Auto-update | dojrzały (`electron-updater`) | wbudowany plugin, dojrzały | v2: podstawowy; v3: w rozwoju | ręczny | automatyczny (serwer) | ClickOnce/MSIX |
| Podpis kodu | udokumentowany, wiele ścieżek | udokumentowany | podstawowy | ręczny | n/d | dojrzały |
| Dojrzałość ekosystemu | bardzo wysoka (VS Code, Slack, Figma, Discord, Notion) | wysoka i rosnąca | średnia | niska | wysoka | wysoka w świecie .NET |
| Koszt wejścia zespołu JS | zerowy | wysoki (Rust) — dla prostych aplikacji można prawie bez Rusta | wysoki (Go) | niski | zerowy | bardzo wysoki |
| Rekrutacja | łatwa | trudniejsza | trudniejsza | trudna | łatwa | inny rynek |
| Zdalne treści, przeglądarka, kiosk | **jedyny sensowny wybór** | nie nadaje się | nie nadaje się | nie | n/d | nie |

Liczby RAM i rozmiaru pochodzą z publicznych porównań (Tauri 8,6 MiB vs Electron 244 MiB
dla przykładowej aplikacji; 172 MB vs 409 MB przy sześciu oknach) — traktuj jako rząd
wielkości, nie jako gwarancję dla twojego przypadku.

## Kiedy Tauri 2 bije Electrona

Tauri 2 to dziś jedyna alternatywa, którą warto rozważać na serio dla projektu
komercyjnego w miejsce Electrona.

**Wybierz Tauri, gdy:**

- Aplikacja jest **rezydentna** — siedzi w tray, ma stać godzinami. 60 MB vs 200 MB
  ma znaczenie, gdy użytkownik ma otwarte piętnaście innych programów.
- **Rozmiar pobrania jest argumentem sprzedażowym** albo klient ma wolne łącze.
  10 MB vs 150 MB to różnica między „pobierz i uruchom” a „poczekaj”.
- Masz **Rusta w zespole** albo backend już jest w Ruście.
- Potrzebujesz **wysokiej wydajności obliczeniowej** po stronie systemowej — Rust bije
  Node w przetwarzaniu danych, kryptografii, parsowaniu.
- Aplikacja ma iść **także na mobile** — Tauri 2 wspiera iOS i Android z tego samego kodu.
  To jest przewaga, której Electron nie ma w ogóle.
- Bezpieczeństwo jest argumentem przetargowym: model uprawnień Tauri (capabilities,
  jawna lista dozwolonych komend) jest ciaśniejszy niż domyślny Electron.

**Nie wybieraj Tauri, gdy:**

- **Renderowanie musi być identyczne na trzech systemach.** WebKitGTK na Linuksie jest
  wersję lub dwie za resztą, WKWebView ma własne dziwactwa CSS, WebView2 jest Chromium,
  ale w wersji zainstalowanej u użytkownika. Trzy silniki = trzy zestawy błędów
  wizualnych i trzy matryce testów.
- Aplikacja **pokazuje obce strony** — brak odpowiednika `webRequest`, brak kontroli
  nad siecią na poziomie Chromium, brak rozszerzeń.
- Używasz **API dostępnych tylko w Chromium** — WebGPU, wybrane części WebRTC,
  File System Access API, natywny podgląd PDF.
- Masz **duży istniejący kod Node** w warstwie systemowej (przetwarzanie plików,
  integracje) — przepisanie na Rust to miesiące.
- Zespół **nie ma i nie będzie miał Rusta**, a aplikacja potrzebuje nietrywialnych
  funkcji systemowych. Prosty most JS↔Rust da się napisać bez znajomości Rusta;
  własny plugin systemowy już nie.

**Realna ścieżka pośrednia:** Tauri z minimalną warstwą Rust (tylko gotowe pluginy:
`fs`, `dialog`, `notification`, `store`, `updater`, `shell`) i całą logiką w TS.
Wtedy koszt Rusta jest bliski zeru, a zyskujesz rozmiar i pamięć. To działa dla
większości aplikacji CRUD-owych.

### Jak wygląda ten sam kod w obu

```ts
// ELECTRON — main.ts
import { ipcMain, dialog } from 'electron';
ipcMain.handle('plik:wczytaj', async (event, sciezka: string) => {
  if (typeof sciezka !== 'string') throw new Error('zły argument');
  return fs.readFile(waliduj(sciezka), 'utf8');
});

// ELECTRON — preload.ts
contextBridge.exposeInMainWorld('api', {
  wczytaj: (s: string) => ipcRenderer.invoke('plik:wczytaj', s),
});
```

```rust
// TAURI — src-tauri/src/lib.rs
#[tauri::command]
fn plik_wczytaj(sciezka: String) -> Result<String, String> {
    let p = waliduj(&sciezka).map_err(|e| e.to_string())?;
    std::fs::read_to_string(p).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![plik_wczytaj])
        .run(tauri::generate_context!())
        .expect("błąd startu");
}
```

```ts
// TAURI — renderer, bez preloadu i bez contextBridge
import { invoke } from '@tauri-apps/api/core';
const tresc = await invoke<string>('plik_wczytaj', { sciezka: '/tmp/a.txt' });
```

Różnice widoczne w tych trzech fragmentach:
- **Tauri nie ma preloadu ani `contextBridge`** — `invoke` jest wstrzykiwane przez rdzeń.
  Mniej kodu, ale też mniej kontroli nad tym, co widzi strona.
- **Lista dozwolonych komend jest jawna** (`generate_handler!`) — nie da się przypadkiem
  wystawić kanału, o którym zapomniałeś. W Electronie to twoja dyscyplina.
- **Uprawnienia w Tauri są deklaratywne** (`capabilities/*.json`: które okna mogą wołać
  które komendy i pluginy). Electron nie ma odpowiednika — wszystko, co zarejestrujesz
  w `ipcMain`, jest dostępne dla każdego okna, chyba że sam sprawdzisz `senderFrame`.
- **Walidacja typu jest w Ruście darmowa** — `sciezka: String` odrzuci liczbę na poziomie
  deserializacji. W Electronie potrzebujesz Zoda.

## Wails

Go zamiast Rusta. Ta sama architektura co Tauri: systemowy WebView + skompilowany
backend.

**Za:** Go jest łatwiejszy niż Rust dla zespołu bez doświadczenia z systemami; szybka
kompilacja; dobra biblioteka standardowa do sieci i I/O; jeden binarny plik wyjściowy.

**Przeciw:** ekosystem mniejszy niż Tauri; **v3 jest w becie** (wymaga Go 1.25+),
więc nowy projekt stoi przed wyborem „stabilne v2, które jest zamrażane” albo
„v3 beta z zapowiedzianymi zmianami API”; te same problemy z niespójnością WebView
co Tauri; mniejsza społeczność = wolniejsze odpowiedzi na problemy.

**Wybierz Wails, gdy** masz Go w zespole i backend w Go. W innym przypadku Tauri ma
większy ekosystem przy tych samych zaletach.

## Neutralino

Mały rdzeń C++ serwujący aplikację przez lokalny serwer HTTP do systemowego WebView.
Instalator 2-3 MB.

**Za:** najmniejszy rozmiar; brak Rusta i Go; prosty model.

**Przeciw:** najwęższy dostęp natywny z całej stawki (podstawowe pliki, okna, tray,
`os.execCommand` do reszty); mała społeczność; **architektura z lokalnym serwerem HTTP
oznacza otwarty port na localhost** — to jest powierzchnia ataku, której nie ma
w Electronie ani Tauri; brak dojrzałego auto-update i podpisu.

**Wybierz Neutralino, gdy:** narzędzie wewnętrzne, prototyp, aplikacja demonstracyjna,
gdzie rozmiar to jedyne kryterium. **Nie do produktu komercyjnego.**

## PWA

Zainstalowana aplikacja webowa. Zero MB pobrania, aktualizacja natychmiastowa,
jeden kod na wszystko.

**Wystarcza, gdy** aplikacja to w istocie strona: praca na danych z serwera, formularze,
tabele, wykresy, komunikator, panel administracyjny.

**Nie wystarcza, gdy** potrzebujesz: swobodnego dostępu do systemu plików bez dialogu,
uruchamiania innych programów, tray, autostartu, menu systemowego, protokołów własnych
z pełną kontrolą, pracy w tle bez otwartej przeglądarki, integracji z urządzeniami
poza WebUSB/WebHID/WebSerial.

**Pułapka wyboru:** File System Access API (do katalogów z uprawnieniem trwałym)
**nie działa w Safari** i ma ograniczenia w Firefoksie. Jeśli aplikacja musi działać
na macOS z Safari — PWA odpada dla scenariuszy plikowych.

**Zasada:** zanim wybierzesz Electron, sprawdź, czy PWA nie wystarcza. To jest
najtańsza opcja w utrzymaniu i najczęściej odrzucana bez sprawdzenia.

## .NET MAUI

Inny świat: natywne kontrolki, C#, ekosystem Microsoftu. Blazor Hybrid pozwala pisać
UI w webowych technologiach osadzonych w natywnej powłoce.

**Wybierz, gdy** zespół jest .NET-owy, aplikacja integruje się z ekosystemem Microsoftu
(Office, Dynamics, Azure AD), a wygląd ma być natywny.

**Nie wybieraj**, jeśli zespół jest webowy — koszt przekwalifikowania jest wyższy niż
przy Tauri, a wsparcie dla Linuksa jest nieoficjalne (społecznościowe GTK).

## Koszt zespołu — liczby, nie wrażenia

Najczęściej pomijana pozycja w porównaniu. Framework wybiera się na 3-5 lat.

| Pozycja | Electron | Tauri | Wails | .NET MAUI |
| --- | --- | --- | --- | --- |
| Czas do pierwszej działającej funkcji dla dewelopera JS | godziny | 1-3 dni (gotowe pluginy) do 2 tygodni (własne komendy) | podobnie | 4-8 tygodni |
| Czas do samodzielności w warstwie systemowej | dni | **2-6 miesięcy** (Rust) | 1-3 miesiące (Go) | 3-6 miesięcy |
| Dostępność odpowiedzi na Stack Overflow / w LLM-ach | bardzo wysoka | średnia, rosnąca | niska | wysoka |
| Ryzyko „jedyna osoba, która to rozumie, odeszła” | niskie | **wysokie**, jeśli Rusta zna jedna osoba | wysokie | średnie |
| Czas budowania w CI (wpływ na tempo pracy) | 5-15 min | 15-40 min (kompilacja Rusta na trzy platformy) | 10-20 min | 10-25 min |
| Debugowanie warstwy systemowej | DevTools + Node inspector, znane | `gdb`/`lldb` + `println!`, obce dla zespołu JS | podobnie | Visual Studio, dojrzałe |

Wniosek praktyczny: **oszczędność 150 MB na instalatorze nie zwraca się, jeśli kosztuje
sześć miesięcy dochodzenia zespołu do produktywności.** Ta kalkulacja odwraca się, gdy
Rust jest już w firmie albo gdy rozmiar jest wymogiem kontraktowym.

## Decyzja w pięciu krokach

1. **Czy da się zrobić PWA?** Jeśli tak — zrób PWA. Koniec.
2. **Czy aplikacja pokazuje obce strony, jest przeglądarką albo kioskiem, albo wymaga
   `webRequest`/rozszerzeń?** Jeśli tak — Electron. Koniec.
3. **Czy renderowanie musi być identyczne na trzech systemach?** Jeśli tak i nie umiesz
   zapłacić za testy na trzech silnikach — Electron.
4. **Czy zespół ma Rusta albo Go, albo aplikacja jest prosta (CRUD, gotowe pluginy)?**
   Jeśli tak i zależy ci na rozmiarze/pamięci — Tauri 2 (Go → Wails).
5. **W pozostałych przypadkach — Electron**, bo koszt zespołu i ryzyko ekosystemu
   przeważają nad 100 MB instalatora.

Zapisz tę decyzję w ADR (patrz
`../architektura-i-dokumentacja/references/engineering-core/przeglad.md`). Za rok nikt nie będzie
pamiętał, dlaczego wybrano to, co wybrano, a pytanie wróci.

## Migracja z Electrona do Tauri

Realistyczny podział pracy dla aplikacji średniej wielkości:

| Warstwa | Co się dzieje | Nakład |
| --- | --- | --- |
| Renderer (React/Vue/Svelte) | przenosi się prawie bez zmian | 5 % |
| Wywołania IPC | `ipcRenderer.invoke('kanal', arg)` → `invoke('komenda', { arg })` z `@tauri-apps/api` | 15 % |
| Handlery `ipcMain.handle` | przepisanie na `#[tauri::command]` w Ruście | **40 %** |
| Warstwa natywna (dialogi, tray, menu, powiadomienia) | mapowanie na pluginy Tauri; część funkcji nie ma odpowiednika | 20 % |
| Moduły natywne Node (`better-sqlite3`) | zamiana na crate'y Rusta (`rusqlite`) — logika dostępu do danych do przepisania | 15 % |
| Build, podpis, aktualizacje | konfiguracja od zera; koncepty podobne | 5 % |

Czego **nie da się przenieść wprost**:

- Wszystko, co opiera się na `webRequest`, `session`, `protocol.handle`, `<webview>`,
  rozszerzeniach Chrome.
- Kod procesu głównego zależny od API Node (strumienie, `child_process` w formie
  używanej przez biblioteki npm, moduły natywne).
- Zachowanie renderowania: policz na regresje wizualne na WebKitGTK i WKWebView.
  To jest ukryty koszt, który zjada oszczędność.

**Kiedy migracja się opłaca:** aplikacja jest w większości UI z prostym backendem,
rozmiar/pamięć są realnym problemem biznesowym, i masz Rusta. W innym przypadku
migracja kosztuje kwartał i przynosi 100 MB.

**Kiedy zdecydowanie nie:** aplikacja działa, użytkownicy nie narzekają, a jedynym
powodem jest „Electron jest ciężki”. To nie jest powód biznesowy.

## Częste błędne przekonania

| Przekonanie | Jak jest |
| --- | --- |
| „Tauri jest szybszy” | Start i renderowanie zależą od twojego kodu i silnika systemowego. WebView2 to to samo Chromium. Różnica jest w pamięci i rozmiarze, nie automatycznie w szybkości. |
| „Tauri jest bezpieczniejszy, bo Rust” | Rust chroni przed błędami pamięci w twoim kodzie systemowym. Nie chroni przed XSS w rendererze, złą walidacją komend ani sekretem w binarce. Model uprawnień Tauri jest lepszy — to jest realna przewaga, nie sam język. |
| „Electron zawsze waży 200 MB” | Zbundlowany main + wyczyszczony ASAR + `compression: maximum` daje 90-120 MB. Powyżej tego to twoje zasoby. |
| „PWA nie ma dostępu do plików” | Ma — File System Access API, z uprawnieniem trwałym. Ale nie w Safari. |
| „Systemowy WebView jest aktualizowany, więc bezpieczniejszy” | Na Windows i macOS tak. Na Linuksie WebKitGTK bywa lata za Chromium w konkretnej dystrybucji — tam Electron z własnym Chromium jest **bezpieczniejszy**. |
| „Wails v3 jest gotowy” | Jest w becie. API może się jeszcze zmienić przed 3.0.0. |
