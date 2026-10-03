#!/bin/sh
# Hook SessionStart: kontekst projektu dla modelu i zmienne dla poleceń Bash sesji.
# Zwykły stdout trafia do kontekstu (dla SessionStart). Zmienne dopisujemy (>>) do
# $CLAUDE_ENV_FILE, żeby nie nadpisać wpisów innych hooków.
set -u
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
  echo 'export PYTHONDONTWRITEBYTECODE=1' >> "$CLAUDE_ENV_FILE"
fi
galaz=$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "brak repozytorium")
zmiany=$(git -C "${CLAUDE_PROJECT_DIR:-.}" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
echo "Gałąź: ${galaz}. Pliki ze zmianami: ${zmiany}. Testy uruchamia: npm test."
exit 0
