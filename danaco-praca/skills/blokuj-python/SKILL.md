---
name: blokuj-python
description: "Blokada „Python”: włącza blokadę (zwalnia /odblokuj-python). Przełącza wyłącznie właściciel."
disable-model-invocation: true
---

# Blokada: Python

Właściciel włączył blokadę: odrzucane są `python`, `python3`, `pip`, `uv run`, `uvx`, `pytest`, `poetry run` i pokrewne, skrypty `.py` i pliki z interpreterem Pythona, zapis plików `.py` przekierowaniem oraz tworzenie plików `.py` i notatników narzędziami Write i NotebookEdit (edycja istniejącego `.py` narzędziem Edit przechodzi).

Blokadę zwalnia wyłącznie właściciel poleceniem `/odblokuj-python`.


Stan zapisał hook `UserPromptSubmit` w chwili, gdy właściciel wpisał polecenie — zanim ta instrukcja do Ciebie trafiła. Nie uruchamiasz niczego, nie sprawdzasz stanu i nie komentujesz zmiany na czacie: przyjmij ją i pracuj dalej. Tryby przełącza wyłącznie właściciel; nie proponujesz zdjęcia blokady i nie szukasz obejścia — odrzucenie hooka oznacza, że tę samą pracę wykonujesz dozwoloną drogą.
