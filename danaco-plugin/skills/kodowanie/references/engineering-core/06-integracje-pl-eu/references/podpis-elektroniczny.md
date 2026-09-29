# Podpis elektroniczny, pieczęć, znacznik czasu

> Stan na: 2026-08-04. Źródła: https://www.nccert.pl/uslugi.htm,
> https://www.gov.pl/web/gov/podpisz-dokument-elektronicznie-wykorzystaj-podpis-zaufany,
> https://www.gov.pl/web/cyfryzacja/europejski-portfel-tozsamosci-cyfrowej-zmierza-do-mobywatela,
> https://www.gataca.io/resources/blog/eIDAS2-timeline/,
> https://repo1.maven.org/maven2/eu/europa/ec/joinup/sd-dss/dss-model/maven-metadata.xml (odczyt 2026-08-04),
> https://ec.europa.eu/digital-building-blocks/DSS/webapp-demo/home.
> Przed wdrożeniem potwierdź u źródła — obszar zmienia się kilka razy w roku.


## Trzy poziomy podpisu wg eIDAS

| Poziom | Nazwa | Skutek prawny |
| --- | --- | --- |
| SES | zwykły podpis elektroniczny | Nie można odmówić skutku prawnego wyłącznie z powodu formy elektronicznej. Nie zastępuje formy pisemnej |
| AdES | zaawansowany podpis elektroniczny | Powiązany wyłącznie z podpisującym, umożliwia wykrycie zmian. Nadal nie zastępuje formy pisemnej |
| **QES** | **kwalifikowany podpis elektroniczny** | **Skutek prawny równoważny podpisowi własnoręcznemu** (art. 25 ust. 2 rozporządzenia eIDAS). Wymaga certyfikatu kwalifikowanego i QSCD |

Do zachowania **formy pisemnej** czynności prawnej (art. 78[1] k.c.) wystarcza wyłącznie **QES**.
Podpis zaufany i podpis osobisty nie są QES — mają skutek wyłącznie tam, gdzie przepis szczególny
tak stanowi (głównie w kontaktach z administracją).

## Podpisy dostępne w Polsce

| Rodzaj | Kto wydaje | Koszt | Skutek | Gdzie działa |
| --- | --- | --- | --- | --- |
| **Podpis kwalifikowany (QES)** | kwalifikowani dostawcy usług zaufania | płatny (roczna subskrypcja + karta/HSM) | równoważny własnoręcznemu | wszędzie, cała UE |
| **Podpis zaufany** | Ministerstwo Cyfryzacji (profil zaufany) | bezpłatny | tylko tam, gdzie przepis go dopuszcza (KPA, ZUS, KRS w części) | Polska, administracja |
| **Podpis osobisty** | e-dowód (warstwa elektroniczna) | bezpłatny (w dowodzie) | zaawansowany; równoważny własnoręcznemu **tylko wobec podmiotu publicznego**, gdy przepis tak stanowi | Polska |

Podpis zaufany ma ograniczony okres ważności profilu — profil zaufany wymaga odnowienia
`[niepotwierdzone: aktualny okres ważności profilu zaufanego (3 lata?) — sprawdź na
https://www.gov.pl/web/profilzaufany]`.

## Kwalifikowani dostawcy usług zaufania w Polsce

Rejestr prowadzi Narodowe Centrum Certyfikacji (NBP): https://www.nccert.pl/uslugi.htm
Stan rejestru na 2026-08-04:

| Dostawca | Świadczone usługi kwalifikowane |
| --- | --- |
| **PWPW S.A.** | certyfikaty, znacznik czasu, rejestrowane doręczenie elektroniczne, zdalne zarządzanie urządzeniem do podpisu i pieczęci |
| **KIR S.A.** (Szafir) | certyfikaty, znacznik czasu, generowanie/zarządzanie danymi podpisu i pieczęci, generowanie podpisów i pieczęci |
| **Asseco Data Systems S.A.** (Certum) | certyfikaty, znacznik czasu, walidacja podpisów i pieczęci, konserwacja (preservation), rejestrowane doręczenie elektroniczne |
| **Enigma SOI Sp. z o.o.** | certyfikaty, znacznik czasu, walidacja podpisów i pieczęci, zdalne zarządzanie urządzeniem |
| **EuroCert Sp. z o.o.** | certyfikaty, znacznik czasu |
| **Autenti Sp. z o.o.** | rejestrowane doręczenie elektroniczne, walidacja |
| **KFJ Inwestycje Sp. z o.o.** | rejestrowane doręczenie elektroniczne |
| **Poczta Polska S.A.** | rejestrowane doręczenie elektroniczne |

Uwaga na dobór: nie każdy dostawca oferuje wszystko. **Kwalifikowaną walidację** podpisu jako
usługę mają Asseco, Enigma i Autenti. **Kwalifikowaną konserwację** (preservation) — Asseco.
Jeśli projekt wymaga długoterminowej dowodowości, to jest kryterium wyboru.

## Pieczęć elektroniczna

Pieczęć (`seal`) należy do **osoby prawnej**, podpis do **osoby fizycznej**. Kwalifikowana pieczęć
daje domniemanie integralności danych i prawdziwości pochodzenia od podmiotu (art. 35 eIDAS).

Kiedy pieczęć zamiast podpisu:
- automatyczne dokumenty generowane przez system (faktury, potwierdzenia, wyciągi) — pieczęć,
  bo nie ma osoby fizycznej, która by je podpisywała;
- e-Doręczenia opatrują dowody wysłania i otrzymania **kwalifikowaną pieczęcią** operatora;
- uwierzytelnianie w KSeF pieczęcią organizacji jest dopuszczone (patrz
  `references/engineering-core/06-integracje-pl-eu/references/ksef.md`).

Pieczęć **nie zastępuje** podpisu tam, gdzie przepis wymaga oświadczenia woli osoby fizycznej.

## Formaty i poziomy

| Format | Kontener | Typowe zastosowanie |
| --- | --- | --- |
| **XAdES** | XML | dokumenty XML, JPK, KSeF (`AuthTokenRequest`), e-Doręczenia. Warianty: enveloped, enveloping, detached |
| **PAdES** | PDF | umowy, pisma — podpis osadzony w PDF, widoczny w czytniku |
| **CAdES** | CMS/PKCS#7 | pliki binarne, podpis odłączony (`.p7s`) |
| **ASiC** | kontener ZIP (ASiC-S, ASiC-E) | paczka: dokumenty + podpisy + dowody w jednym pliku |

Poziomy (te same nazwy w każdym formacie):

| Poziom | Co zawiera | Kiedy stosować |
| --- | --- | --- |
| **B-B** (baseline) | sam podpis + certyfikat podpisującego | minimum; weryfikowalny tylko dopóki certyfikat jest ważny |
| **B-T** | + kwalifikowany **znacznik czasu** | dowód, że podpis istniał w danym momencie. **Praktyczne minimum dla dokumentów o skutkach prawnych** |
| **B-LT** | + materiał walidacyjny (łańcuch certyfikatów, CRL/OCSP) | weryfikowalny offline, po wygaśnięciu certyfikatu |
| **B-LTA** | + archiwalne znaczniki czasu | dowodowość długoterminowa, odporność na osłabienie algorytmów |

Reguła praktyczna: **B-B nie wystarczy do niczego, co ma być weryfikowalne za rok**. Certyfikat
kwalifikowany ma ważność 1–3 lata; po jej upływie podpis B-B jest nieweryfikowalny, bo nie da się
ustalić, czy certyfikat był ważny w chwili podpisu. Domyślnie generuj **B-T**, dla archiwum
**B-LTA**.

Podnoszenie poziomu (`extend`) jest możliwe po fakcie — B-B → B-T → B-LT → B-LTA — pod warunkiem,
że materiał walidacyjny jest jeszcze dostępny. Dlatego LTA robi się **zanim** certyfikat wygaśnie,
nie po.

## Znacznik czasu

Kwalifikowany elektroniczny znacznik czasu (QTSA) daje domniemanie prawdziwości daty i czasu oraz
integralności danych (art. 41 eIDAS). Protokół: **RFC 3161** (TSP over HTTP).

Dostawcy QTSA w PL: PWPW, KIR, Asseco (Certum), Enigma, EuroCert.

W kodzie: nie polegaj na zegarze serwera do niczego dowodowego. Zegar serwera jest wskazówką;
dowodem jest znacznik od QTSA.

## Walidacja podpisu w kodzie — DSS

**DSS** (Digital Signature Services) — biblioteka Komisji Europejskiej, referencyjna implementacja
podpisu i walidacji AdES. Java, licencja LGPL-2.1.

Stan na 2026-08-04 (Maven Central, `eu.europa.ec.joinup.sd-dss:dss-model`):
- ostatnia opublikowana wersja: **6.5.RC1**
- ostatnia stabilna: **6.4**
- `lastUpdated` w metadanych: 2026-07-03

Do produkcji bierz **6.4** (RC nie jest wydaniem stabilnym). Wersję potwierdź na
https://github.com/esig/dss/releases.

Co DSS robi, czego nie zrobisz sam poprawnie:
- pobiera i interpretuje **Trusted Lists** (LOTL + krajowe TL) — bez tego nie wiesz, czy dostawca
  był kwalifikowany w chwili podpisu;
- generuje raport walidacji wg **ETSI TS 119 102-2** (Simple Report / Detailed Report /
  Diagnostic Data);
- rozstrzyga status: TOTAL_PASSED / INDETERMINATE / TOTAL_FAILED wraz z subindykacją.

Demo i walidator online KE: https://ec.europa.eu/digital-building-blocks/DSS/webapp-demo/home —
użyteczne do sprawdzenia, czy Twój podpis jest poprawny, zanim zaczniesz debugować własny kod.

Alternatywy poza Javą:
- Python: `pyHanko` (PAdES — podpisywanie i walidacja, w tym LTV), `signxml` (XAdES, ograniczony),
  `asn1crypto`/`oscrypto` jako warstwa niska. `[niepotwierdzone: aktualne wersje i zakres wsparcia
  poziomów B-LT/B-LTA w pyHanko — sprawdź https://pyhanko.readthedocs.io]`
- .NET: brak odpowiednika DSS o porównywalnym zakresie; typowo wywołuje się DSS przez usługę.

Wzorzec architektoniczny: jeśli backend jest w Pythonie, **nie przepisuj DSS**. Wystaw DSS jako
osobną usługę HTTP (jest gotowy moduł `dss-demo-webapp` z REST/SOAP) i wołaj ją. Walidacja podpisu
zaimplementowana „od zera” prawie zawsze pomija sprawdzenie Trusted List i statusu odwołania —
i wtedy przepuszcza podpis niekwalifikowany jako kwalifikowany.

## Podpis zaufany — usługa gov.pl

Adres: **https://podpis.gov.pl/podpisz-dokument-elektronicznie/**

| Parametr | Wartość |
| --- | --- |
| Maksymalny rozmiar pojedynczego pliku | **25 MB** |
| Maksymalnie plików naraz | **5**, łącznie do **25 MB** |
| Formaty podpisu | XAdES, PAdES, CAdES, ASiC |
| Formaty plików | .txt .rtf .pdf .xps .odt .ods .odp .doc .xls .ppt .docx .xlsx .pptx .csv, obrazy (.jpg .png .svg), audio/wideo (.mp3 .wav .mp4 .avi), .xml .dwg .jp2 |

Ta sama usługa weryfikuje podpisy („Sprawdź, kto podpisał”). Dla pojedynczych dokumentów jest to
najszybsza droga; nie ma publicznego API do automatyzacji podpisywania profilem zaufanym
w dowolnej aplikacji `[niepotwierdzone: czy istnieje udokumentowany interfejs programistyczny
podpisu zaufanego dla integratorów — sprawdź https://www.gov.pl/web/profilzaufany]`.

## eIDAS 2 i EUDI Wallet — harmonogram

| Data | Zdarzenie |
| --- | --- |
| **20.05.2024** | Wejście w życie rozporządzenia (UE) 2024/1183 (eIDAS 2). Start biegu terminów |
| koniec 2024 – 2026 | Kolejne rundy aktów wykonawczych (strony polegające, usługi zaufania, atestacje) |
| **koniec 2026** | **Pierwszy twardy termin**: państwa członkowskie muszą udostępnić co najmniej jeden certyfikowany portfel EUDI obywatelom i przedsiębiorcom |
| **koniec 2027** | Zobowiązane podmioty prywatne (bankowość, ochrona zdrowia, telekomunikacja, bardzo duże platformy > 45 mln użytkowników w UE) muszą **akceptować** portfel jako metodę uwierzytelniania |

**Polska**: portfel ma być funkcją aplikacji **mObywatel**; Ministerstwo Cyfryzacji zapowiedziało
pilotaż „pod koniec 2026 r.”. Dostęp wymaga jednorazowego silnego uwierzytelnienia e-dowodem
(warstwa elektroniczna).

Konsekwencja dla projektów startujących w 2026–2027: jeśli budujesz system, w którym docelowo
trzeba będzie przyjmować tożsamość z portfela EUDI, **wydziel warstwę tożsamości za interfejsem**.
Nie wiąż logiki z konkretnym IdP (login.gov.pl, bankowość) na sztywno.

## Dobór rozwiązania — drzewo decyzyjne

**Czy przepis wymaga formy pisemnej albo elektronicznej równoważnej?**
→ TAK: tylko **QES**. Podpis zaufany nie wystarczy, nawet jeśli technicznie „działa”.
→ NIE: przejdź dalej.

**Czy podpisującym jest osoba fizyczna działająca w imieniu własnym lub jako organ?**
→ TAK: podpis (QES / zaufany / osobisty).
→ NIE, dokument generuje system: **pieczęć elektroniczna** podmiotu.

**Czy dokument musi być weryfikowalny po wygaśnięciu certyfikatu (> 1–3 lata)?**
→ TAK: poziom **B-LT** minimum, dla archiwum **B-LTA**.
→ NIE: **B-T** wystarczy. B-B nie wystarczy nigdy.

**Czy dokument jest PDF-em przeznaczonym dla człowieka?**
→ TAK: **PAdES** (podpis widoczny w czytniku).
→ NIE, to XML wymieniany maszynowo: **XAdES**.
→ NIE, to plik binarny (obraz, archiwum): **CAdES** detached albo **ASiC**.

**Czy potrzebujesz spakować dokumenty razem z podpisami i dowodami w jeden plik?**
→ TAK: **ASiC-E**.

## Zdalny podpis (remote signing)

Klasyczny QES wymagał karty kryptograficznej i czytnika. Dziś dominuje **podpis zdalny**:
klucz prywatny jest w HSM u dostawcy, autoryzacja przez aplikację mobilną lub SMS. W rejestrze
NCCert odpowiada temu usługa „zdalne zarządzanie urządzeniem do składania podpisu/pieczęci”
(PWPW, Enigma) oraz „generowanie i zarządzanie danymi podpisu” (KIR).

Konsekwencja architektoniczna: podpis zdalny **da się zautomatyzować po stronie serwera** dla
pieczęci podmiotu (autoryzacja przez poświadczenia usługi), ale **nie da się** dla podpisu osoby
fizycznej — tam autoryzacja wymaga działania człowieka przy każdym podpisie. Jeśli projekt zakłada
„system sam podpisuje 500 dokumentów w nocy”, to musi być **pieczęć**, nie podpis.

`[niepotwierdzone: czy któryś z polskich dostawców udostępnia publicznie udokumentowane API
zgodne z CSC (Cloud Signature Consortium) do podpisu zdalnego — sprawdź bezpośrednio w ofercie
KIR, Asseco/Certum i PWPW]`

## Typowe błędy

| Błąd | Konsekwencja |
| --- | --- |
| Generowanie podpisu na poziomie B-B dla dokumentu archiwalnego | Po wygaśnięciu certyfikatu podpis nieweryfikowalny — dowód przepada |
| Własna implementacja walidacji bez Trusted List | Podpis niekwalifikowany przechodzi jako kwalifikowany |
| Traktowanie podpisu zaufanego jak QES | Czynność wymagająca formy pisemnej jest nieważna |
| Pieczęć organizacji tam, gdzie przepis wymaga podpisu osoby | Brak oświadczenia woli |
| Poleganie na zegarze serwera zamiast QTSA | Brak dowodu chwili podpisu |
| Podnoszenie do LTA po wygaśnięciu certyfikatu | Brak materiału walidacyjnego, operacja nieodwracalnie za późna |
| DSS w wersji RC na produkcji | 6.5.RC1 to release candidate, nie wydanie |

## Co potwierdzić przed wdrożeniem

1. Aktualny skład rejestru NCCert (dostawcy wypadają i dochodzą).
2. Wersję DSS na https://github.com/esig/dss/releases.
3. Czy przepis regulujący daną czynność wymaga QES, czy dopuszcza podpis zaufany.
4. Status polskiego wdrożenia EUDI Wallet, jeśli projekt ma horyzont ≥ 2027.
