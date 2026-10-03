#!/bin/sh
# Sprawdza warunki piaskownicy Bash Claude Code na Linuksie/WSL2 (tylko odczyt, bez sudo).
# Użycie: sh sprawdz_srodowisko.sh
# Wynik: lista warunków z oceną OK/BRAK/UWAGA. Kod wyjścia 1, gdy brakuje zależności wymaganej.
set -u
blad=0
ocena() { printf '%-7s %s\n' "$1" "$2"; }

case "$(uname -s)" in
  Linux) ;;
  Darwin) ocena OK "macOS: Seatbelt wbudowany, brak zależności"; exit 0 ;;
  *) ocena BRAK "system $(uname -s) — piaskownica działa tylko na macOS, Linux i WSL2"; exit 1 ;;
esac
if grep -qi microsoft /proc/version 2>/dev/null; then
  ocena UWAGA "WSL: piaskownica wymaga WSL2 (WSL1 nieobsługiwany)"
fi
for program in bwrap socat; do
  if command -v "$program" >/dev/null 2>&1; then
    ocena OK "$program: $(command -v "$program")"
  else
    ocena BRAK "$program — wymagany (pakiet bubblewrap/socat; pakiety systemowe zatwierdza właściciel serwera)"
    blad=1
  fi
done
klucz=/proc/sys/kernel/apparmor_restrict_unprivileged_userns
if [ -r "$klucz" ]; then
  wartosc=$(cat "$klucz")
  if [ "$wartosc" = "0" ]; then ocena OK "apparmor_restrict_unprivileged_userns = 0"
  else ocena UWAGA "apparmor_restrict_unprivileged_userns = $wartosc — potrzebny profil AppArmor dla bwrap (userns)"; fi
else
  ocena OK "brak klucza apparmor_restrict_unprivileged_userns (ograniczenie nie występuje)"
fi
if [ -r /proc/sys/user/max_user_namespaces ]; then
  ocena OK "max_user_namespaces = $(cat /proc/sys/user/max_user_namespaces)"
fi
if command -v bwrap >/dev/null 2>&1; then
  if bwrap --ro-bind / / --dev /dev --proc /proc --unshare-all true 2>/dev/null; then
    ocena OK "bwrap tworzy przestrzenie nazw i montuje /proc"
  elif bwrap --ro-bind / / --dev /dev --unshare-all true 2>/dev/null; then
    ocena UWAGA "bwrap działa bez nowego /proc — kontener bez uprawnień: enableWeakerNestedSandbox przy zewnętrznej izolacji"
  else
    ocena BRAK "bwrap nie tworzy przestrzeni nazw (userns zablokowane)"; blad=1
  fi
  if bwrap --ro-bind / / --dev /dev --proc /proc --unshare-all -- bwrap --ro-bind / / --dev /dev --proc /proc --unshare-all true 2>/dev/null; then
    ocena OK "zagnieżdżony bwrap działa"
  else
    ocena UWAGA "zagnieżdżony bwrap nie działa — jeśli CLI zgłasza 'apply-seccomp: write /proc/self/setgroups', ustaw network.allowAllUnixSockets: true (bez filtra seccomp gniazd)"
  fi
fi
if [ -f /.dockerenv ] || grep -qE '(docker|containerd|kubepods)' /proc/1/cgroup 2>/dev/null; then
  ocena UWAGA "wykryto kontener — sprawdź montowanie /proc w bwrap (enableWeakerNestedSandbox)"
fi
if [ "$(id -u)" = "0" ]; then
  ocena UWAGA "uruchomiono jako root — --dangerously-skip-permissions odmówi startu poza rozpoznaną piaskownicą"
fi
exit $blad
