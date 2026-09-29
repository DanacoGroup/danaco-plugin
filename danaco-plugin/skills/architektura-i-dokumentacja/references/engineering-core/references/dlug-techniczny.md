# Dług techniczny i refaktoryzacja

Dług techniczny to różnica między kształtem, jaki kod ma, a kształtem, jaki powinien
mieć, żeby dzisiejsze zmiany były tanie. Metafora finansowa jest trafna w jednym
punkcie: dług ma **odsetki** — koszt płacony przy każdej zmianie — i te odsetki, nie
kwota główna, decydują o kolejności spłaty.

Nie każdy brzydki kod jest długiem. Kod, którego nikt nie zmienia i który działa, ma
odsetki bliskie zeru — przepisywanie go to strata. Dług liczy się tylko tam, gdzie
system żyje.

## Klasyfikacja

### Po intencji

| Rodzaj | Powstaje gdy | Jak traktować |
| --- | --- | --- |
| **Celowy rozważny** | „Wiemy, że to uproszczenie; wybraliśmy je świadomie dla terminu” | Zapisz w kodzie komentarzem z odnośnikiem do zadania i warunkiem spłaty. To jest zdrowe |
| **Celowy nierozważny** | „Nie mamy czasu na projektowanie, piszemy jak wyjdzie” | Najdroższy rodzaj. Nie ma planu spłaty, bo nie ma zapisu, co jest długiem |
| **Przypadkowy rozważny** | „Teraz, po zbudowaniu, wiemy, jak to powinno wyglądać” | Naturalny i nieunikniony. Spłacaj przy najbliższym dotknięciu obszaru |
| **Przypadkowy nierozważny** | „Nie wiedzieliśmy, że tak się nie robi” | Wymaga nauki, nie tylko refaktoryzacji — inaczej wróci |

Praktyczna konsekwencja: dług celowy rozważny zapisuj **w kodzie**, w miejscu jego
wystąpienia, w jednym formacie:

```typescript
// DŁUG(ZGL-412, do 2026-Q4): synchroniczne wywołanie API fakturowania.
// Powód: brak czasu na outbox przed terminem wdrożenia.
// Koszt: awaria API fakturowania = błąd 500 przy zamykaniu zgłoszenia.
// Spłata: przenieść do outboxu (ADR-0007), ~2 dni.
```

Komentarz `// TODO: poprawić` bez terminu, kosztu i sposobu jest szumem — po roku
nikt nie wie, czy nadal jest aktualny.

### Po obszarze

| Obszar | Objawy | Odsetki | Ryzyko |
| --- | --- | --- | --- |
| **Kod** | Duplikacja, funkcje >100 linii, warunki zagnieżdżone na 5 poziomów, magiczne liczby | Średnie — spowalnia każdą zmianę w obszarze | Niskie — błędy widoczne |
| **Architektura** | Przecieki warstw, cykle modułów, wspólna tabela dwóch modułów, brak granic | **Najwyższe** — rośnie wykładniczo, blokuje wszystkie zmiany | Wysokie — trudne do naprawienia inkrementalnie |
| **Dane** | Schemat niepasujący do domeny, brak ograniczeń, dane niespójne w produkcji | Wysokie | **Najwyższe** — dane uszkodzone są nieodwracalne |
| **Testy** | Brak testów krytycznych ścieżek, testy niedeterministyczne, testy implementacji | Wysokie — blokuje refaktoryzację czegokolwiek | Wysokie — regresje trafiają na produkcję |
| **Zależności** | Wersje bez wsparcia, porzucone paczki, znane podatności | Niskie do momentu, gdy staje się blokadą | **Wysokie** — podatności, blokada aktualizacji runtime'u |
| **Infrastruktura** | Ręczne wdrożenia, brak IaC, brak monitoringu, brak odtwarzalnego środowiska | Wysokie — każde wdrożenie kosztuje czas i nerwy | Wysokie — długi czas odtworzenia po awarii |
| **Wiedza** | Jedna osoba rozumie moduł, brak dokumentacji decyzji, brak ADR | Niewidoczne do odejścia tej osoby | **Skrajne** — nagła utrata zdolności do zmiany |

Kolejność, w której model zwykle się myli: skupia się na długu kodowym (widocznym
w diffie) i pomija dług wiedzy i dług danych — dwa najgroźniejsze.

## Pomiar

Bez liczb priorytetyzacja jest opinią. Mierzalne sygnały, dostępne bez dodatkowych
narzędzi:

| Miara | Skąd | Co oznacza wysoka wartość |
| --- | --- | --- |
| Częstość zmian pliku | `git log --format=%n --name-only \| sort \| uniq -c \| sort -rn` | Obszar żyje; dług tutaj ma realne odsetki |
| Zmiany z poprawką błędu w pliku | `git log --grep='fix\|popraw' --name-only` | Obszar generuje błędy; kandydat na refaktoryzację |
| Liczba autorów pliku | `git shortlog -sn -- <plik>` | Jeden autor = dług wiedzy |
| Wiek ostatniej zmiany | `git log -1 --format=%ar` | Stary i niezmieniany = niski priorytet, choćby brzydki |
| Czas budowania i testów | CI | >10 min oznacza, że ludzie przestają uruchamiać testy lokalnie |
| Udział testów niedeterministycznych | Historia CI | >2% = zespół przestaje ufać czerwonemu wynikowi |
| Zależności bez wsparcia | `npm audit`, `pip-audit`, `osv-scanner` | Ryzyko bezpieczeństwa z terminem |
| Czas wdrożenia zmiany jednoliniowej | Pomiar | Miara całkowitego tarcia |

Najsilniejszy sygnał to **przecięcie częstości zmian z częstością poprawek**. Plik
zmieniany 40 razy w kwartale, z czego 15 razy poprawką błędu, jest pierwszym kandydatem
niezależnie od tego, jak wygląda.

```bash
# pliki najczęściej zmieniane w ostatnim półroczu
git log --since='6 months ago' --format='' --name-only \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

Czego **nie** mierzyć jako długu: pokrycia testami jako celu (100% pokrycia z testami
tautologicznymi to dług, nie jego brak), złożoności cyklomatycznej w oderwaniu od
częstości zmian, liczby ostrzeżeń lintera (to zadanie dla lintera, nie dla planu).

## Priorytetyzacja

Kolejność wyznacza iloczyn kosztu utrzymania i ryzyka, podzielony przez nakład:

```
priorytet = (odsetki_miesieczne × prawdopodobieństwo_zmiany) + ryzyko
            ────────────────────────────────────────────────────────
                              nakład
```

W praktyce wystarczy tabela z trzema kolumnami ocenianymi w skali 1–5:

| Element | Odsetki | Ryzyko | Nakład | Wynik | Decyzja |
| --- | --- | --- | --- | --- | --- |
| Brak testów modułu rozliczeń | 4 | 5 | 3 | 3,0 | Najpierw |
| Sterownik bazy bez wsparcia (podatność) | 1 | 5 | 1 | 6,0 | Natychmiast |
| Duplikacja walidacji w 3 miejscach | 3 | 2 | 2 | 2,5 | Przy okazji |
| Moduł raportów pisany przez jedną osobę | 2 | 4 | 4 | 1,5 | Sparuj przy najbliższej zmianie |
| Brzydki, stabilny kod importu CSV | 1 | 1 | 3 | 0,7 | Nie ruszać |

Wzór: `(odsetki + ryzyko) / nakład`. Nie chodzi o dokładność liczby, tylko o zmuszenie
do porównania. Element z niskim wynikiem i wysoką atrakcyjnością techniczną („przepiszmy
to na nowy wzorzec”) jest dokładnie tym, czego nie robić.

### Zasada budżetu

Spłata długu w osobnym „sprincie technicznym” nie działa: jest odkładana przy pierwszym
naciskiem biznesowym i tworzy podział na pracę „biznesową” i „techniczną”. Działa:

- **Stały udział** ~15–20% każdego okresu na dług, wpisany w plan jak każde zadanie.
- **Zasada harcerza**: obszar dotknięty przy zadaniu funkcjonalnym zostaje odrobinę
  lepszy — z ograniczeniem do rzeczy mieszczących się w tym samym commicie.
- **Sprzątanie wyprzedzające**: przed dużą zmianą funkcjonalną najpierw refaktoryzacja
  przygotowawcza w osobnym commicie, potem zmiana. Kolejność odwrotna miesza dwie
  rzeczy w jednym diffie i uniemożliwia przegląd.

## Refaktoryzacja krok po kroku

Definicja robocza: zmiana struktury kodu **bez zmiany jego obserwowalnego zachowania**.
Jeśli zachowanie się zmienia, to nie jest refaktoryzacja — to zmiana funkcjonalna
udająca refaktoryzację, najgroźniejszy rodzaj commita.

### Warunek wstępny: siatka bezpieczeństwa

**Nie refaktoryzuj kodu bez testów.** Kolejność jest zawsze taka:

1. Napisz testy charakteryzujące — sprawdzające, co kod **robi teraz**, nie co powinien.
   Także zachowania, które wyglądają na błędy (ktoś może na nich polegać).
2. Uruchom, potwierdź zieloność.
3. Dopiero refaktoryzuj.

```python
# Test charakteryzujący: dokumentuje stan faktyczny, w tym dziwny
def test_ujemna_kwota_daje_zero_a_nie_blad():
    # UWAGA: prawdopodobnie błąd, ale raport miesięczny na tym polega (ZGL-388)
    assert oblicz_rabat(-100, 0.1) == 0
```

Gdy kod jest tak spleciony, że nie da się go przetestować, użyj kolejności:
najmniejsza możliwa zmiana umożliwiająca test (wydzielenie zależności przez parametr)
→ test → właściwa refaktoryzacja.

### Sekwencja bezpiecznych kroków

Każdy krok osobno, każdy z uruchomieniem testów, każdy jako osobny commit.

| Krok | Operacja | Ryzyko |
| --- | --- | --- |
| 1 | Zmiana nazwy (narzędziem IDE, nie wyszukaj-zamień) | Bardzo niskie |
| 2 | Wydzielenie funkcji z fragmentu | Niskie |
| 3 | Wydzielenie zmiennej wyjaśniającej z wyrażenia | Bardzo niskie |
| 4 | Zamiana warunku zagnieżdżonego na wczesne wyjścia | Niskie |
| 5 | Wydzielenie parametru zamiast zależności globalnej | Średnie |
| 6 | Wydzielenie klasy/modułu z grupy funkcji | Średnie |
| 7 | Zmiana struktury danych | Wysokie — wymaga pełnego pokrycia |
| 8 | Przesunięcie granicy modułu | Najwyższe — traktuj jak zmianę architektury z ADR |

Reguła: **nigdy nie łącz kroku o wysokim ryzyku z jakimkolwiek innym**. Commit
zmieniający nazwy i strukturę danych jednocześnie jest nieprzeglądalny i nie da się go
wycofać częściowo.

### Rozdziel refaktoryzację od zmiany funkcjonalnej

```
commit 1: refaktoryzacja — wydzielenie ObliczanieRabatu, bez zmiany zachowania
commit 2: funkcja — nowa reguła rabatu progowego
```

Recenzent commita 1 sprawdza, czy zachowanie się nie zmieniło (może to zrobić szybko,
bo testy są te same). Recenzent commita 2 patrzy na małą, czytelną zmianę. Zmieszane —
nikt nie sprawdzi ani jednego, ani drugiego.

### Antywzorce refaktoryzacji

| Antywzorzec | Co się dzieje |
| --- | --- |
| Refaktoryzacja „przy okazji” w PR funkcjonalnym | Diff 900 linii; recenzent zatwierdza bez czytania |
| Refaktoryzacja bez testów, „bo przecież widzę, że to to samo” | Regresja w ścieżce, o której zapomniałeś |
| Wprowadzenie abstrakcji na podstawie dwóch przypadków | Abstrakcja nie pasuje do trzeciego; koszt większy niż duplikacja |
| Refaktoryzacja kodu, który za miesiąc się usuwa | Praca wyrzucona |
| Ujednolicanie stylu w całym repozytorium jednym commitem | `git blame` bezużyteczny, konflikty we wszystkich gałęziach |
| „Zrefaktoryzuję, jak skończę funkcję” | Nie skończy się nigdy |

Uwaga o duplikacji: dwie kopie to **nie** jest dług. Przedwczesne wyodrębnienie
wspólnego kodu z dwóch miejsc, które przypadkiem wyglądają podobnie, tworzy sprzężenie
między niepowiązanymi obszarami — a to jest gorsze. Reguła trzech: wyodrębniaj przy
trzecim wystąpieniu, gdy widzisz już, co jest naprawdę wspólne.

## Wzorzec duszącego figowca

Sposób na wymianę dużego komponentu bez zatrzymania systemu. Nazwa od figowca
duszącego, który oplata drzewo i rośnie, aż stare drzewo zanika — a korona stoi
przez cały czas.

### Sekwencja

**1. Postaw przechwytywacz.** Warstwa kierująca ruch, przez którą przechodzi całe
wywołanie do wymienianego obszaru. Na początku przekazuje 100% do starego.

```typescript
export function utworzRozliczenia(
  stare: SilnikRozliczen,
  nowe: SilnikRozliczen,
  flagi: Flagi,
): SilnikRozliczen {
  return {
    async oblicz(zgloszenieId: string) {
      if (!flagi.wlaczona('nowy-silnik-rozliczen', zgloszenieId)) {
        return stare.oblicz(zgloszenieId);
      }
      return nowe.oblicz(zgloszenieId);
    },
  };
}
```

**2. Wybierz pierwszy fragment do przeniesienia.** Najmniejszy z jasną granicą,
najlepiej odczytowy (błąd w odczycie nie uszkadza danych).

**3. Uruchom porównawczo.** Przez pewien czas oba tory liczą, wynik zwraca stary,
różnice są logowane. To jedyny sposób, żeby odkryć nieudokumentowane zachowania,
które ktoś wykorzystuje.

```typescript
async oblicz(zgloszenieId: string) {
  const wynikStary = await stare.oblicz(zgloszenieId);
  if (flagi.wlaczona('porownanie-rozliczen', zgloszenieId)) {
    try {
      const wynikNowy = await nowe.oblicz(zgloszenieId);
      if (wynikNowy.kwotaGrosze !== wynikStary.kwotaGrosze) {
        log.warn({ zgloszenieId, stary: wynikStary, nowy: wynikNowy }, 'rozbieżność');
      }
    } catch (e) {
      log.error({ err: e, zgloszenieId }, 'nowy silnik rzucił wyjątek');
    }
  }
  return wynikStary;   // stary nadal jest źródłem prawdy
}
```

**4. Przełącz stopniowo.** 1% ruchu → 10% → 50% → 100%, z możliwością natychmiastowego
cofnięcia flagą. Na każdym progu odczekaj co najmniej pełen cykl biznesowy (dla
rozliczeń: pełny miesiąc).

**5. Usuń stary kod.** To jest krok, który zespoły pomijają — i wtedy zostają z dwiema
implementacjami na zawsze, czyli z długiem większym niż przed migracją. Usunięcie
starego toru i przechwytywacza jest częścią zadania, nie osobnym pomysłem na później.

### Kiedy figowiec, a kiedy zwykła refaktoryzacja

| Sytuacja | Podejście |
| --- | --- |
| Moduł 500 linii, dobre testy | Refaktoryzacja bezpośrednia, kroki 1–6 |
| Moduł krytyczny, słabe testy, cudze zachowania | Figowiec z porównaniem |
| Zmiana bazy danych | Figowiec: podwójny zapis, porównanie odczytu, przełączenie |
| Zmiana dostawcy zewnętrznego | Figowiec na poziomie adaptera |
| Zmiana frameworka HTTP | Figowiec na poziomie routingu (nowe endpointy w nowym) |

## Kiedy przepisać od zera

Prawie nigdy. Argumenty za przepisaniem są prawie zawsze błędne z tych samych powodów:

| Argument | Dlaczego zawodzi |
| --- | --- |
| „Kod jest nieczytelny” | Nieczytelność zawiera lata poprawek błędów, których nie znasz. Przepisanie odtworzy je wszystkie, po kolei, na produkcji |
| „Nowa technologia będzie lepsza” | Wymiana znanego problemu na nieznany |
| „Szybciej napiszę od nowa niż zrozumiem” | To zdanie znaczy: „nie znam wymagań”. Napiszesz szybko coś innego |
| „Stary system nie skaluje się” | Zmierz, gdzie. Zwykle to jedno zapytanie albo brak indeksu |
| „Nikt już nie zna tej technologii” | Migracja stopniowa uczy zespołu przy działającym systemie |

Koszt przepisania jest systematycznie niedoszacowany, bo szacuje się **funkcje
widoczne**, a nie **zachowania faktyczne**: obsługę przypadków szczególnych klientów,
poprawki wprowadzone po incydentach, integracje, o których nikt nie pamięta, dane
historyczne w formatach z poprzednich wersji. Te zachowania nie są nigdzie zapisane
poza kodem, który chcesz wyrzucić.

Dodatkowo: przez cały czas przepisywania stary system musi być rozwijany (bo biznes nie
staje), więc cel się przesuwa. To główna przyczyna, dla której przepisania nie kończą się.

### Warunki, przy których przepisanie jest uzasadnione

Wszystkie muszą zachodzić jednocześnie:

1. **Technologia bazowa jest martwa i nie da się jej utrzymać** — nie „stara”, tylko
   bez łatek bezpieczeństwa, bez działającego środowiska, bez możliwości zatrudnienia
   kogokolwiek (np. runtime, którego już nie da się uruchomić na wspieranym systemie).
2. **Zakres jest mały i w pełni opisany** — kilka tysięcy linii z kompletną specyfikacją
   lub zestawem testów akceptacyjnych.
3. **Stary system może działać równolegle** przez cały okres przejścia, z możliwością
   powrotu w każdej chwili.
4. **Istnieje sposób weryfikacji równoważności** — porównanie wyników na rzeczywistych
   danych, nie deklaracja „przetestowaliśmy”.
5. **Nikt nie liczy na skrócenie czasu** dzięki przepisaniu. Przepisanie nie przyspiesza
   dostarczania funkcji; w najlepszym razie nie spowalnia.

Jeśli któryś warunek nie zachodzi — figowiec.

### Wariant pośredni, prawie zawsze lepszy

Przepisz **jeden moduł**, nie system. Wybierz moduł o najwyższych odsetkach i najlepiej
określonej granicy, wymień go figowcem, oceń wynik. Jeśli wyszło — powtórz z następnym.
To daje wszystkie korzyści przepisania bez ryzyka „wielkiego przepisania”, które nigdy
się nie kończy.

## Format rejestru długu

Dług nieprzetworzony na zapis nie istnieje. Jedna tabela w repozytorium
(`docs/dlug.md`), aktualizowana przy przeglądach:

```markdown
| Id | Obszar | Opis | Odsetki | Ryzyko | Nakład | Warunek spłaty | Status |
|----|--------|------|---------|--------|--------|----------------|--------|
| D-01 | dane | Brak `CHECK` na kwotach; w produkcji 14 rekordów z ujemną kwotą | 2 | 5 | 1 d | Przed zamknięciem kwartału | otwarty |
| D-02 | architektura | Moduł rozliczeń czyta tabele modułu zgłoszeń | 4 | 3 | 5 d | Przed wydzieleniem raportów | otwarty |
| D-03 | zależności | Sterownik SMTP bez wsparcia od 2024 | 1 | 4 | 0,5 d | Natychmiast | w toku |
| D-04 | wiedza | Moduł importu rozumie tylko jedna osoba | 2 | 4 | 3 d | Przy najbliższej zmianie — parowanie + ADR | otwarty |
```

Wpis bez `Warunku spłaty` jest życzeniem, nie planem. Rejestr powyżej ~30 pozycji
przestaje być czytany — usuwaj pozycje, których nikt nie podejmie, zamiast je hodować.
