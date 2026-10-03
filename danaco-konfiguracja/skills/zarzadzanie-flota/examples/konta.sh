#!/usr/bin/env bash
# Kilka kont Claude Code na jednym serwerze/stanowisku: osobny CLAUDE_CONFIG_DIR na konto
# (ustawienia, historia sesji, logowanie lub klucz, zgody na ustawienia serwerowe, cache wtyczek).
# Wczytaj w ~/.bashrc:  . /ścieżka/konta.sh   — potem: claude-praca, claude-test, claude-konta
# Uwaga: keyless sign-in do Console (profil Anthropic) jest trzymany POZA katalogiem konfiguracji
# (~/.config/anthropic) — osobne katalogi go nie rozdzielą; użyj ANTHROPIC_PROFILE na konto.

KONTA_BAZA="${KONTA_BAZA:-${XDG_CONFIG_HOME:-$HOME/.config}/claude-konta}"

_claude_konto() {
  local konto="$1"; shift
  mkdir -p "$KONTA_BAZA/$konto"
  CLAUDE_CONFIG_DIR="$KONTA_BAZA/$konto" claude "$@"
}

claude-praca() { _claude_konto praca "$@"; }
claude-test()  { _claude_konto test "$@"; }

# Stan kont bez wypisywania sekretów: czy jest logowanie, ostatnia aktywność, rozmiar transkryptów.
claude-konta() {
  local d
  for d in "$KONTA_BAZA"/*/; do
    [ -d "$d" ] || continue
    printf '%-12s logowanie:%-4s sesje:%-6s ostatnio:%s\n' "$(basename "$d")" \
      "$([ -s "$d/.credentials.json" ] && echo tak || echo nie)" \
      "$(du -sh "$d/projects" 2>/dev/null | cut -f1)" \
      "$(find "$d/projects" -name '*.jsonl' -printf '%TY-%Tm-%Td\n' 2>/dev/null | sort | tail -1)"
  done
}
