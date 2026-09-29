# Konwencje nazewnicze — część trzecia standardu

Plik niesie rozdział 7 standardu redakcyjnego: zakaz kodów wymyślonych, zakaz określeń
abstrakcyjnych, nazewnictwo bytów kodu, regułę jednego źródła prawdy, regułę zamkniętego
zbioru oraz tryb postępowania przy braku ustalenia. Rozdział zachowuje numerację wspólną
dla całego standardu. Spis rozdziałów i podział na pliki:
`references/standard-redakcyjny-i-jezykowy.md`. Nazewnictwo w samym kodzie rozstrzyga
paczka `standardy-nazewnictwa`.

---

## 7. Konwencje budowy obowiązujące na przyszłość

Rozdział wiąże nie tylko dokumentację, lecz także dalszą budowę produktu. Jego celem jest
zamknięcie źródła problemu, a nie tylko jego skutków.

### 7.1 Zakaz kodów wymyślonych

**Żadnych oznaczeń typu `ADL`, `D-01`, `P-3`, `L-P-7`, rejestrów decyzji ani numeracji
ustaleń.** Odwołujemy się nazwą rzeczy, nie kodem.

| Zapis zakazany | Zapis wiążący |
|---|---|
| „zgodnie z ADL-14” | „zgodnie z zasadą jednego źródła prawdy” |
| „patrz P-3” | „patrz ``[Model konfiguracji](architektura/model-konfiguracji.md)``” |
| „decyzja D-07 przesądza” | „warstwowość konfiguracji przesądza” |
| „rejestr decyzji, poz. 22” | nazwa rozstrzygnięcia i miejsce jego opisu |

Numeracja dopuszczalna jest **wyłącznie** jako numeracja rozdziałów wewnątrz jednego
dokumentu. Kod, który istnieje tylko w głowie autora i wymaga tabeli rozwinięć, nie jest
oznaczeniem — jest szyfrem.

### 7.2 Zakaz określeń abstrakcyjnych

Nazwa opisuje rzecz, a nie jej rolę w narracji autora.

| Określenie ogólnikowe | Czego brakuje | Zapis wiążący |
|---|---|---|
| „mechanizm” | co to jest | „silnik kolejek zadań” |
| „warstwa pomocnicza” | czemu służy | „warstwa adapterów dostawcy modelu” |
| „element” | który | „kafel modułu na stronie głównej” |
| „odpowiedni komponent” | który | „`.dn-btn--sygnal`” |
| „system” bez dopowiedzenia | który | „rdzeń platformy” albo „powłoka kliencka” |

### 7.3 Nazewnictwo bytów kodu

Reguły spisane z tego, co w repozytorium już obowiązuje. Nowy byt otrzymuje nazwę zgodną
z rodziną, do której należy.

> **Zapis kluczy nastaw.** Nazwy w postaci `obszar.grupa.nastawa` użyte w tym rozdziale są
> **kluczami konfiguracji**, nie komendami kontraktu. Klucz wskazuje miejsce wartości w modelu
> konfiguracji; komendy kontraktu, którymi się go odczytuje i zapisuje, to `config.get` i
> `config.set` (obszar `config` w `budowa/shared/contract.json`).


| Rodzina | Reguła zapisu | Przykład wzorcowy |
|---|---|---|
| Pliki i katalogi dokumentacji | małe litery, myślnik jako separator, bez polskich znaków, nazwa rzeczownikowa | `model-konfiguracji.md` |
| Pliki źródłowe powłoki | jak wyżej, nazwa po polsku | `budowa/client/src/powloka/pasek-gorny.ts` |
| Żetony projektowe | `--dn-{rodzina}-{wariant}`; rodziny istniejące: `wym`, `sygnal`, `cien`, `szary`, `tekst`, `ostrzezenie`, `informacja`, `z`, `sukces`, `od`, `blad`, `obrys`, `fs`, `lh`, `ff`, `fw`, `atrament`, `czas`, `rama`, `wstazka`, `r`, `powierzchnia`, `fokus`, `tlo`, `nakladka`, `kropka`, `bp` | `--dn-sygnal-obrys`, `--dn-fs-base`, `--dn-bp-w2` |
| Klasy komponentów | `.dn-{komponent}` · element `.dn-{komponent}-{element}` · modyfikator `.dn-{komponent}--{wariant}` | `.dn-btn`, `.dn-btn--sygnal`, `.dn-awatar-stan` |
| Komendy kontraktu | `{obszar}.{czynność}` albo `{obszar}.{podobszar}.{czynność}`, notacja wielbłądzia w członach złożonych; nazwa obszaru wyłącznie z wykazu 68 obszarów w `budowa/shared/contract.json` — dziesięć z nich: `connection`, `home`, `environment`, `module`, `workspace`, `session`, `window`, `message`, `config`, `settings` | `environment.enter`, `speech.availability.get` |
| Pola ładunku kontraktu | notacja wielbłądzia, angielski, nazwa rzeczownikowa | `focusedSessionId`, `protocolVersion` |
| Kolumny bazy danych | małe litery, podkreślenie jako separator, bez polskich znaków | `srodowisko_id`, `zrodlo_typ` |
| Zdarzenia | `{obszar}.{rzecz}.{co się stało}` w czasie przeszłym | `session.message.appended` |

Nazwa nowego bytu nie powstaje w oderwaniu od tych rodzin. Jeśli byt nie mieści się
w żadnej, jest to sygnał, że rodzina wymaga rozszerzenia — rozszerzenie odnotowujemy tutaj,
a nie zakładamy własnej konwencji obok.

### 7.4 Reguła jednego źródła prawdy

Wartość istnieje w jednym miejscu i jest przywoływana, nigdy powielana.

```
                    ┌──────────────────────────┐
                    │   ŹRÓDŁO NORMATYWNE      │
                    │  contract.json           │
                    │  zetony.css              │
                    │  komponenty.css          │
                    └────────────┬─────────────┘
                                 │  przywołanie
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌────────────┐     ┌────────────┐     ┌────────────┐
       │ opracowanie│     │  prototyp  │     │    kod     │
       └────────────┘     └────────────┘     └────────────┘

       Zakazane: powielenie wartości w którymkolwiek z trzech miejsc.
```

| Zakazane | Wiążące |
|---|---|
| wartość szesnastkowa koloru w opisie wyglądu | nazwa żetonu `--dn-*` |
| wartość pikselowa wymiaru | nazwa żetonu z rodziny `wym` albo `od` |
| nazwa komendy przepisana z pamięci | nazwa odczytana z `contract.json` |
| własna lista pól ładunku | lista z `contract.json` |

### 7.5 Reguła zamkniętego zbioru

Nowa funkcja wchodzi do produktu **razem z opracowaniem**, które niesie komplet:

```
┌─────────────────────────────────────────────────────────────┐
│  Funkcja gotowa do budowy — warunki łączne                  │
├─────────────────────────────────────────────────────────────┤
│  ✓ nazwa komendy kontraktu i pola ładunku                   │
│  ✓ dosłowne brzmienie wszystkich etykiet i komunikatów      │
│  ✓ żetony i klasy komponentów użyte w widoku                │
│  ✓ komplet stanów kontrolek                                 │
│  ✓ zachowanie na wszystkich punktach łamania                │
│  ✓ skróty klawiszowe i ich kolizje                          │
│  ✓ kryteria odbioru — warunki sprawdzalne                   │
└─────────────────────────────────────────────────────────────┘
```

Brak któregokolwiek z siedmiu warunków oznacza, że funkcja nie jest gotowa do budowy.
Rozpoczęcie budowy mimo braku jest odstępstwem od standardu, a nie decyzją wykonawcy.

### 7.6 Tryb postępowania przy braku ustalenia

```
        czy wartość jest w źródle normatywnym?
                        │
            ┌───────────┴───────────┐
           tak                     nie
            │                       │
            ▼                       ▼
     przywołaj ją        czy Właściciel ją rozstrzygnął?
                                    │
                        ┌───────────┴───────────┐
                       tak                     nie
                        │                       │
                        ▼                       ▼
              zapisz i wskaż        [DO DECYZJI OPERATORA]
              podstawę              + pytanie postawione wprost
```

Zakazane jest przemycenie własnej propozycji wykonawcy jako faktu. Propozycja jest
dopuszczalna wyłącznie jako propozycja: oznaczona, opatrzona uzasadnieniem i skierowana
do rozstrzygnięcia.

---

