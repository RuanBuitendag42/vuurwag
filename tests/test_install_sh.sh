#!/usr/bin/env bash
# Tests for install.sh's pure helpers: bash tests/test_install_sh.sh  (no root, no network, changes nothing)
# Sources install.sh with VUURWAG_INSTALL_SOURCED=1 so main() does not run.
# shellcheck source-path=SCRIPTDIR
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../install.sh
VUURWAG_INSTALL_SOURCED=1 source "${HERE}/../install.sh"
set +e   # install.sh turned errexit on; the asserts below count failures themselves

PASS=0 FAIL=0
ok()  { PASS=$((PASS + 1)); printf 'ok   %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf 'FAIL %s\n' "$1"; }
expect_eq() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1: expected [$3], got [$2]"; fi; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── --public-url ─────────────────────────────────────────────────────────────
for u in http://192.168.1.10:8787 http://tv.example.lan:8787 https://x.ts.net 'http://[::1]:8787' http://pve:8787/ https://node.tailnet.ts.net/vuurwag; do
    if valid_public_url "$u" && (parse_args --public-url "$u") >/dev/null 2>&1; then ok "url accepted: $u"; else bad "url rejected: $u"; fi
done
# shellcheck disable=SC2016  # the $(id) is meant literally: it must be rejected, not expanded
for u in 'http://x-]' 'http://[::1' 'ftp://x' 'http://' 'http://a b' 'http://x:8787"' 'http://x/$(id)' 'http://x:123456'; do
    if valid_public_url "$u" || (parse_args --public-url "$u") >/dev/null 2>&1; then bad "url accepted: $u"; else ok "url rejected: $u"; fi
done

# ── pve-firewall host.fw ─────────────────────────────────────────────────────
RULE="$(fw_rule 198.51.100.0/24 8787)"

printf '[OPTIONS]\n\nenable: 1\n\n[RULES]\n\nIN SSH(ACCEPT) -source 198.51.100.0/24 -log nolog\n' >"$TMP/plain.fw"
expect_eq "plan: no rule -> add" "$(fw_plan "$RULE" 8787 <"$TMP/plain.fw")" "add"
fw_merge "$RULE" <"$TMP/plain.fw" >"$TMP/merged.fw"
expect_eq "merge: rule right under [RULES]" "$(sed -n '/^\[RULES\]/{n;p;}' "$TMP/merged.fw")" "$RULE"
expect_eq "merge: other rules kept" "$(grep -c 'SSH(ACCEPT)' "$TMP/merged.fw")" "1"
expect_eq "plan: after merge -> present" "$(fw_plan "$RULE" 8787 <"$TMP/merged.fw")" "present"
fw_merge "$RULE" <"$TMP/merged.fw" >"$TMP/merged2.fw"
expect_eq "merge: idempotent" "$(cmp -s "$TMP/merged.fw" "$TMP/merged2.fw" && echo same)" "same"

HAND='IN ACCEPT -p tcp -dport 8787 -source 198.51.100.0/24 -log nolog'
printf '[RULES]\n\n%s\n' "$HAND" >"$TMP/hand.fw"
expect_eq "plan: hand-made rule for the port -> covered" "$(fw_plan "$RULE" 8787 <"$TMP/hand.fw")" "covered ${HAND}"
expect_eq "plan: hand-made rule, other port -> add" "$(fw_plan "$(fw_rule 198.51.100.0/24 9090)" 9090 <"$TMP/hand.fw")" "add"
printf '[RULES]\n|IN ACCEPT -p tcp -dport 8787 -log nolog\n# IN ACCEPT -p tcp -dport 8787\nIN DROP -p tcp -dport 8787\nIN ACCEPT -p tcp -dport 87870\n' >"$TMP/near.fw"
expect_eq "plan: disabled/commented/DROP/longer port do not cover" "$(fw_plan "$RULE" 8787 <"$TMP/near.fw")" "add"

printf '[RULES]\n%s\nIN ACCEPT -p tcp -dport 22\n' "$(fw_rule 198.51.100.0/24 8080)" >"$TMP/oldport.fw"
expect_eq "plan: tagged rule for an old port -> add" "$(fw_plan "$RULE" 8787 <"$TMP/oldport.fw")" "add"
fw_merge "$RULE" <"$TMP/oldport.fw" >"$TMP/oldport2.fw"
expect_eq "merge: old tagged rule replaced, one left" "$(grep -c "$FW_TAG" "$TMP/oldport2.fw")" "1"
expect_eq "merge: the one left is the new one" "$(grep -F "$FW_TAG" "$TMP/oldport2.fw")" "$RULE"

printf '[OPTIONS]\nenable: 1\n' >"$TMP/norules.fw"
fw_merge "$RULE" <"$TMP/norules.fw" >"$TMP/norules2.fw"
expect_eq "merge: [RULES] created when missing" "$(grep -c '^\[RULES\]' "$TMP/norules2.fw")" "1"
expect_eq "merge: empty file gets the rule" "$(fw_merge "$RULE" </dev/null | grep -cF "$RULE")" "1"

# ── authorized_keys on a cluster ─────────────────────────────────────────────
{
    echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIadmin admin@laptop'
    echo 'from="127.0.0.1,::1",command="python3 -",restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIpve1 vuurwag-kiosk@pve1'
    echo 'from="127.0.0.1,::1",command="python3 -",restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIpve2 vuurwag-kiosk@pve2'
    echo 'from="127.0.0.1,::1",command="python3 -",restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIpve1x vuurwag-kiosk@pve1x'
    echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIother not-restricted vuurwag-kiosk@pve1'
} >"$TMP/ak"
ak_without_node_key pve1 <"$TMP/ak" >"$TMP/ak2"
expect_eq "authorized_keys: this node's line removed" "$(grep -c 'AAAAIpve1 ' "$TMP/ak2")" "0"
expect_eq "authorized_keys: other nodes, look-alikes and unrestricted keys kept" "$(wc -l <"$TMP/ak2" | tr -d ' ')" "4"

# ── legacy layout (the hand deployment's flat /opt/vuurwag) ───────────────────
PREFIX="$TMP/opt"
mkdir -p "$PREFIX/vuurwag" "$PREFIX/deploy" "$PREFIX/tests" "$PREFIX/src" "$PREFIX/.venv/bin"
touch "$PREFIX/pyproject.toml" "$PREFIX/uv.lock" "$PREFIX/README.md" "$PREFIX/vuurwag/__init__.py" "$PREFIX/src/keep" "$PREFIX/.venv/bin/python"
if legacy_layout; then ok "legacy: flat layout detected"; else bad "legacy: flat layout not detected"; fi
clean_legacy >/dev/null
expect_eq "legacy: old files removed" "$(find "$PREFIX" -mindepth 1 -maxdepth 1 -printf '%f ' | tr ' ' '\n' | LC_ALL=C sort | tr '\n' ' ')" ".venv src "
if legacy_layout; then bad "legacy: still detected after cleanup"; else ok "legacy: clean after cleanup"; fi

# ── a failed download must not cost the old install ───────────────────────────
# do_install with the system-touching steps stubbed out and the real fetch_source pointed at nothing
PREFIX="$TMP/opt2" SRC_DIR="$TMP/opt2/src" VENV="$TMP/opt2/.venv"
mkdir -p "$PREFIX/vuurwag" "$PREFIX/deploy" "$VENV/bin"
touch "$PREFIX/pyproject.toml" "$PREFIX/uv.lock" "$PREFIX/vuurwag/__init__.py"
before="$(cd "$PREFIX" && find . | LC_ALL=C sort)"
(
    apt_install() { :; }
    python_ok() { :; }
    detect_network() { :; }
    OPT_NO_PVE=1 OPT_LOCAL_SRC="$TMP/nonexistent"
    do_install
) >/dev/null 2>&1
rc=$?
expect_eq "failed download: do_install fails" "$([ "$rc" != 0 ] && echo failed)" "failed"
expect_eq "failed download: the legacy layout is untouched" "$(cd "$PREFIX" && find . | LC_ALL=C sort)" "$before"
if legacy_layout; then ok "failed download: still a legacy layout (nothing half-removed)"; else bad "failed download: legacy layout gone"; fi

# ── the font check (a real node "lost" an installed font to pipefail + grep -q) ─────
set -o pipefail
# like fc-list: the font early in a long listing, so grep -q quits while the writer is still writing
big_listing() { echo "/usr/share/fonts/x.ttf: DejaVu Sans Mono:style=Book"; seq 1 200000 | sed 's/$/: Some Font:style=Book/'; }
if contains "$(big_listing)" "DejaVu Sans Mono"; then ok "contains: finds the font in a 200k-line listing under pipefail"; else bad "contains: missed it"; fi
if big_listing | grep -q 'DejaVu Sans Mono'; then
    bad "the old 'cmd | grep -q' pattern passed: the regression check below proves nothing"
else
    ok "the old 'cmd | grep -q' pattern reports 'not found' under pipefail (rc ${PIPESTATUS[0]}): the live bug, reproduced"
fi
dpkg-query() { seq 1 100000 >/dev/null; printf 'install ok installed'; }
if pkg_installed fonts-dejavu-core; then ok "pkg_installed: true for an installed package"; else bad "pkg_installed: false for an installed package"; fi
dpkg-query() { printf 'deinstall ok config-files'; }
if pkg_installed fonts-dejavu-core; then bad "pkg_installed: true for a removed package"; else ok "pkg_installed: false for a removed package"; fi

DEJAVU_TTF="$TMP/DejaVuSansMono.ttf"
fc-match() { printf 'DejaVu Sans Mono'; }
if font_check; then ok "font: fc-match names DejaVu Sans Mono"; else bad "font: fc-match hit not accepted"; fi
fc-match() { printf 'DejaVu Sans Mono,DejaVu Sans Mono Book'; }
if font_check; then ok "font: fc-match with several family names"; else bad "font: several family names not accepted"; fi
fc-match() { printf 'Noto Sans'; }
pkg_installed() { return 1; }
if font_check; then bad "font: accepted a fallback font"; else ok "font: fc-match falls back to another font, no file, no package -> missing"; fi
touch "$DEJAVU_TTF"
if font_check; then ok "font: the .ttf file is enough when fontconfig disagrees"; else bad "font: file not accepted"; fi
rm -f "$DEJAVU_TTF"
pkg_installed() { [ "$1" = fonts-dejavu-core ]; }
if font_check; then ok "font: the fonts-dejavu-core package is enough"; else bad "font: package not accepted"; fi
unset -f fc-match dpkg-query
# shellcheck disable=SC2016  # ${Status} is dpkg-query's format field, not a shell variable
pkg_installed() { contains "$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)" 'install ok installed'; }
expect_eq "font: diagnose prints something either way" "$(font_diagnose 2>&1 | grep -c 'fc-match')" "1"
set +o pipefail

# ── --place placeholder, --bind ───────────────────────────────────────────────
for p in "Your Town, South Africa" "Your Town" "  your town , ZA"; do
    if (parse_args --place "$p") >/dev/null 2>&1; then bad "place accepted: '$p'"; else ok "place rejected: '$p'"; fi
done
for p in "Bloemfontein, South Africa" "Yourtown, ZA" "Lyon, FR"; do
    if (parse_args --place "$p") >/dev/null 2>&1; then ok "place accepted: '$p'"; else bad "place rejected: '$p'"; fi
done
for b in 192.0.2.10 0.0.0.0 :: fd00::10; do
    if (parse_args --bind "$b") >/dev/null 2>&1; then ok "bind accepted: $b"; else bad "bind rejected: $b"; fi
done
for b in pve.example.lan 192.0.2.10:8787 '[::1]' 'x;id'; do
    if (parse_args --bind "$b") >/dev/null 2>&1; then bad "bind accepted: '$b'"; else ok "bind rejected: '$b'"; fi
done

# default 0.0.0.0 (Tailscale, DHCP); --bind is opt-in
NODE_IP=192.0.2.10 OPT_BIND=""
expect_eq "bind: default is every address even with a primary IPv4" "$(default_bind 2>/dev/null)" "0.0.0.0"
OPT_BIND=192.0.2.10
expect_eq "bind: --bind IP is used as given" "$(default_bind 2>/dev/null)" "192.0.2.10"
OPT_BIND=""

# the unguarded-page warning: no pve-firewall vs a disabled one
ENV_FILE="$TMP/none.env"
if command -v pve-firewall >/dev/null 2>&1; then
    ok "warning: no pve-firewall found (skipped: this host has a real pve-firewall)"
else
    expect_eq "warning: no pve-firewall found" "$(fw_unguarded_warning 8787 2>&1 | grep -c '^!! no pve-firewall found')" "1"
fi
# shellcheck disable=SC2329  # found by fw_unguarded_warning's 'command -v pve-firewall'
pve-firewall() { echo "Status: disabled/running"; }
expect_eq "warning: pve-firewall disabled" "$(fw_unguarded_warning 8787 2>&1 | grep -c 'pve-firewall is DISABLED')" "1"
expect_eq "warning: names 0.0.0.0 when nothing is configured" "$(fw_unguarded_warning 8787 2>&1 | grep -c '0.0.0.0:8787')" "1"
unset -f pve-firewall

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]
