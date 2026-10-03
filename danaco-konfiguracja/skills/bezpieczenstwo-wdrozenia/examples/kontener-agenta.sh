#!/usr/bin/env bash
# Uruchomienie Claude Code w utwardzonym kontenerze (wzorzec z cc:agent-sdk/secure-deployment).
# Kod tylko do odczytu, brak sieci — ruch wyłącznie przez gniazdo proxy działającego NA HOŚCIE,
# które pilnuje listy domen i dokłada poświadczenie (agent go nie widzi).
# Wymaga: obraz z CLI (np. agent-image), proxy na hoście nasłuchujące na $GNIAZDO_PROXY,
# w obrazie most gniazdo→localhost:8080 (np. socat) uruchamiany przed `claude`.
# Użycie: ./kontener-agenta.sh /ścieżka/do/kodu "polecenie dla agenta"
set -euo pipefail

KOD="${1:?ścieżka do kodu}"
PROMPT="${2:?polecenie}"
OBRAZ="${OBRAZ:-agent-image}"
GNIAZDO_PROXY="${GNIAZDO_PROXY:-/var/run/proxy-agenta.sock}"
PROFIL="${PROFIL:-/srv/agent/seccomp.json}"

exec docker run --rm -i \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --security-opt "seccomp=${PROFIL}" \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /home/agent:rw,noexec,nosuid,size=500m \
  --network none \
  --memory 2g --cpus 2 --pids-limit 100 \
  --user 1000:1000 \
  -v "${KOD}:/workspace:ro" \
  -v "${GNIAZDO_PROXY}:/var/run/proxy.sock:ro" \
  -e ANTHROPIC_BASE_URL=http://localhost:8080 \
  -e HTTPS_PROXY=http://localhost:8080 \
  -e CLAUDE_CONFIG_DIR=/home/agent/.claude \
  -e DISABLE_AUTOUPDATER=1 \
  -e CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
  -w /workspace \
  "${OBRAZ}" \
  claude -p "${PROMPT}" \
    --setting-sources "" --strict-mcp-config --disable-slash-commands \
    --tools "Read,Grep,Glob" --permission-mode dontAsk --permission-prompts none \
    --max-turns 50 --output-format json < /dev/null
