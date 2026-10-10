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

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]
