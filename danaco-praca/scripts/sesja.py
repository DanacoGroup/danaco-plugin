"""SessionStart trybu ciągłej pracy: opis trwającego zlecenia i stan sprzed kompresji.

Wywołuje go hooks/straznik.sh (tryb ``sesja``); scripts/straznik.py nie ma tego trybu.
Nigdy nie blokuje: każdy błąd kończy się kodem 0 bez wyjścia. Nie wypisuje komendy
kończącej tryb (tę zna tylko użytkownik).

Argument opcjonalny: katalog pluginu (zgodność z wrapperem sprzed 4.7.0, który podawał
go jawnie); domyślnie moduły są brane z katalogu tego pliku.
"""

import json
import os
import sys


def main() -> int:
    katalog_skryptow = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1 and sys.argv[1]:
        katalog_skryptow = os.path.join(sys.argv[1], "scripts")
    sys.path.insert(0, katalog_skryptow)
    import znacznik  # noqa: PLC0415 - ścieżka modułu znana dopiero tutaj

    try:
        zdarzenie = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        zdarzenie = {}
    if not isinstance(zdarzenie, dict):
        zdarzenie = {}
    sesja = str(zdarzenie.get("session_id") or "")
    cwd = str(zdarzenie.get("cwd") or "")
    katalog = znacznik.znajdz_katalog_znacznika(cwd or None, sesja=sesja)
    if katalog is None:
        return 0
    dane = znacznik.wczytaj_znacznik(katalog, sesja) or {}
    if znacznik.wygasl(dane):
        return 0
    wiersze = [
        "Trwa zlecenie trybu ciągłej pracy (danaco-praca).",
        f"Opis zlecenia: {dane.get('opis') or '(brak opisu)'}",
        f"Katalog zlecenia: {katalog.parent}",
        "Pracuj dalej bez kończenia tury i bez pytań; o zakończeniu decyduje wyłącznie użytkownik.",
    ]
    stan = znacznik.sciezka_stanu(katalog, sesja)
    if stan.is_file():
        tresc = stan.read_text(encoding="utf-8", errors="replace").strip()
        if tresc:
            wiersze += ["", "Stan zapisany przed ostatnią kompresją:", tresc[:4000]]
    print("\n".join(w for w in wiersze if znacznik.POLECENIE_ZAKONCZENIA not in w))
    return 0


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # noqa: BLE001 - SessionStart nie może zatrzymać sesji
        pass
    sys.exit(0)
