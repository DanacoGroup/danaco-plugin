# Asembler x86-64 — karta

## Standard stylu i nazewnictwa

Dla asemblera nie istnieje jeden branżowy standard stylu — obowiązuje więc zasada nadrzędna: jeden
asembler, jedna składnia i jedna konwencja wywołań na moduł, zadeklarowane w komentarzu nagłówkowym
pliku. Wybór narzędzia i składni:

- NASM: składnia Intel, Linux i Windows; GAS: domyślnie składnia AT&T (przełączalna dyrektywą
  `.intel_syntax noprefix`); MASM: składnia Intel, wyłącznie Windows;
- nie mieszaj składni Intel i AT&T w jednym pliku ani nie przenoś dyrektyw między asemblerami
  (`section .text` w NASM, `.text` w GAS, `.code` w MASM);
- formaterów automatycznych brak w powszechnym użyciu zawodowym — wyrównuj mnemoniki i operandy
  stałą kolumną, jedna instrukcja na wiersz.

Konwencje nazewnicze i dokumentacyjne:

- etykiety eksportowane w `snake_case`, zgodne z ABI języka C (na Linuksie symbol `sum_array`; w x64
  na Windows bez dekoracji nazw);
- etykiety lokalne z prefiksem kropki (NASM: `.loop`) lub numeryczne (GAS: `1:` oraz odwołania
  `1b`/`1f`);
- stałe przez `equ`/`%define` w `UPPER_SNAKE_CASE`;
- komentuj kontrakt każdej procedury: konwencję wywołań, rejestry wejściowe i wyjściowe, rejestry
  niszczone (clobbered), wymagania wyrównania stosu — bez tego kod asemblerowy jest nieodbieralny w
  przeglądzie.

## Struktura projektu

Asembler w projektach zawodowych występuje jako niewielkie moduły przy kodzie C/C++ — utrzymuj go
tak, nie jako samodzielne drzewo źródeł:

```
projekt/
├── CMakeLists.txt          # lub Makefile
├── src/
│   ├── main.c              # uprząż w C wywołująca procedury
│   ├── sum_sysv.asm        # wariant System V (Linux/macOS)
│   └── sum_win64.asm       # wariant Microsoft x64 (Windows)
├── include/danaco/
│   └── sum.h               # deklaracje procedur dla C/C++
└── tests/
    └── test_sum.c
```

Zasady i zakazy:

- warianty dla różnych ABI trzymaj w osobnych plikach wybieranych przez system budowania — nie w
  jednym pliku pełnym warunkowej kompilacji makrami;
- nie twórz plików asemblerowych dla kodu, który kompilator generuje równie dobrze; asembler
  rezerwuj dla udokumentowanej potrzeby: intrinsics niewystarczające, kod startowy, ścieżki
  krytyczne wskazane przez profiler.

## Budowa i zależności

Polecenia asemblacji dla poszczególnych narzędzi:

- NASM: `nasm -f elf64 -g -F dwarf src/sum_sysv.asm -o sum.o` (Linux) oraz `nasm -f win64
  src/sum_win64.asm -o sum.obj` (Windows);
- GAS: asembluj przez sterownik kompilatora `gcc -c src/sum.S` — rozszerzenie `.S` (wielka litera)
  włącza preprocesor C;
- MASM: `ml64 /c /Fo sum.obj src\sum_win64.asm`.

Zasady konsolidacji i integracji:

- konsoliduj przez sterownik kompilatora (`gcc`/`clang`/`cl`), nie przez surowe `ld` — sterownik
  dołącza pliki startowe i biblioteki systemowe we właściwej kolejności;
- w CMake włączaj język jawnie: `enable_language(ASM_NASM)` lub `enable_language(ASM)`; pliki
  `.asm`/`.S` dodawaj do celu jak zwykłe źródła;
- zależności zewnętrzne w sensie menedżera pakietów nie występują; wiąż wersję wymaganego asemblera
  w dokumentacji budowania, a rozszerzenia zestawu instrukcji (np. AVX2) sprawdzaj w czasie
  wykonania przez `cpuid` — nie zakładaj ich milcząco;
- na Linuksie oznaczaj stos jako niewykonywalny (NASM: `section .note.GNU-stack noalloc noexec
  nowrite progbits`), aby uniknąć ostrzeżeń konsolidatora i degradacji zabezpieczeń.

## Testy

Testuj procedury asemblerowe wyłącznie przez uprząż w C/C++: deklaracja `extern` w nagłówku,
wywołania z frameworka testowego (Unity, CMocka lub GoogleTest), rejestracja w CTest, uruchamianie
`ctest --output-on-failure`. Praktyki:

- pokrywaj testami przypadki brzegowe ABI: długość 0, długość 1, dane niewyrównane, wartości
  wymuszające przeniesienia i przepełnienia;
- porównuj wynik procedury asemblerowej z implementacją referencyjną w C na losowych danych (test
  różnicowy);
- weryfikuj zachowanie rejestrów zachowywanych: testy dynamiczne wychwytują zniszczone rejestry
  tylko przypadkiem, dlatego dodatkowo przeglądaj prolog i epilog względem kontraktu ABI.

## Diagnostyka

Debuguj przez `gdb` z widokami `layout asm` i `layout regs`: krok po instrukcji `si`, po wywołaniu
`ni`, rejestry `info registers`, pamięć `x/8gx $rsp`; w lldb odpowiednio `register read` i
`disassemble`. Narzędzia statyczne i dynamiczne:

- deasemblacja i inspekcja: `objdump -d -M intel plik.o`, symbole `nm`, nagłówki `readelf -h` —
  porównuj wygenerowany kod z zamierzonym po każdej zmianie;
- Valgrind działa na binariach z modułami asemblerowymi i wykrywa błędne dostępy do pamięci;
  sanitizery obejmują tylko kod instrumentowany kompilatorem — nie licz na nie wewnątrz procedur
  asemblerowych;
- profilowanie: `perf record`/`perf report` oraz `perf annotate` z kosztem na poziomie pojedynczych
  instrukcji.

Czytanie typowych awarii: `segmentation fault` w okolicy `call` do biblioteki standardowej
(szczególnie w `printf`, na instrukcji typu `movaps`) wskazuje najczęściej złamane 16-bajtowe
wyrównanie stosu. Błędy konsolidatora: `undefined reference` — brak `global` (NASM)/`.globl` (GAS)
przy etykiecie albo niezgodność nazwy z deklaracją w C; `relocation truncated to fit: R_X86_64_PC32`
— adresowanie bezwzględne zamiast względnego względem RIP w kodzie budowanym jako PIE.

## Typowe błędy modeli LLM w tym języku

1. **Mieszanie konwencji System V AMD64 i Microsoft x64**: argumenty całkowite w System V idą w
   `rdi, rsi, rdx, rcx, r8, r9`, w Microsoft x64 w `rcx, rdx, r8, r9`. Model pisze prolog pod
   Linuksa i wywołuje WinAPI albo odwrotnie. Zadeklaruj ABI w komentarzu nagłówkowym procedury i
   konsekwentnie go przestrzegaj.
2. **Brak 32-bajtowego shadow space w Microsoft x64**: przed każdym `call` wywołujący musi
   zarezerwować 32 bajty na stosie (`sub rsp, 32`) ponad ewentualne argumenty stosowe. System V nie
   ma shadow space — model błędnie przenosi ten wzorzec w obie strony.
3. **Złamane wyrównanie stosu przed `call`**: oba ABI wymagają, aby w chwili wykonania `call`
   wskaźnik `rsp` był wyrównany do 16 bajtów (po wejściu do procedury jest przesunięty o 8 przez
   adres powrotu). Modele odejmują od `rsp` dowolne wielokrotności 8, co kończy się awarią na
   `movaps` wewnątrz bibliotek.
4. **Niszczenie rejestrów zachowywanych bez ich zapisania**: w System V rejestry `rbx, rbp, r12–r15`
   (w Microsoft x64 dodatkowo `rdi, rsi` i `xmm6–xmm15`) muszą zostać odtworzone przez procedurę.
   Model używa `rbx` jako licznika pętli bez pary `push`/`pop`.
5. **Wywołania systemowe 32-bitowe w kodzie 64-bitowym**: `int 0x80` z numerami z tabeli 32-bitowej
   zamiast instrukcji `syscall` z numerami 64-bitowymi (na Linux x86-64: `write` = 1, `exit` = 60) i
   argumentami w `rdi, rsi, rdx, r10, r8, r9` — czwarty argument w `r10`, nie w `rcx`, ponieważ
   `syscall` niszczy `rcx` i `r11`.
6. **Pominięcie rejestru `al` przy wywołaniu wariadycznym w System V**: przed `call printf` ustaw w
   `al` liczbę użytych rejestrów wektorowych. Poprawny wzorzec:

```nasm
        lea     rdi, [rel fmt]   ; format
        mov     esi, dword [num] ; argument całkowity
        xor     eax, eax         ; zero rejestrów wektorowych w użyciu
        call    printf wrt ..plt
```

7. **Błędne rozumienie zapisu do rejestrów częściowych**: zapis do rejestru 32-bitowego (`mov eax,
   1`) zeruje górne 32 bity `rax`; zapis 8- lub 16-bitowy (`mov al, 1`) pozostawia resztę bez zmian
   i tworzy zależność od poprzedniej wartości. Modele zakładają zerowanie w obu przypadkach albo w
   żadnym.
8. **Mylenie kierunku operandów między składniami**: Intel — `mov rax, rbx` (cel po lewej); AT&T —
   `movq %rbx, %rax` (cel po prawej, sufiksy rozmiaru, prefiksy `%` i `$`). Model generuje składnię
   Intel z kolejnością AT&T lub odwrotnie — kod się asembluje, ale robi coś przeciwnego.
9. **Adresowanie bezwzględne zamiast względnego względem RIP**: `mov rax, [label]` bez `rel` w NASM
   (lub bez `(%rip)` w GAS) nie konsoliduje się w domyślnych binariach PIE. Stosuj dyrektywę
   `default rel` na początku pliku NASM albo jawnie `lea rax, [rel label]`.
10. **Nadmiarowe „optymalizacje” bez pomiaru i bez dbałości o poprawność**: rozwijanie pętli i
    wstawianie instrukcji AVX bez sprawdzenia `cpuid` oraz bez `vzeroupper` przed powrotem do kodu
    SSE degraduje wydajność lub łamie zgodność. Napisz najpierw wariant poprawny i zmierz
    profilerem, zanim zaczniesz optymalizować.
