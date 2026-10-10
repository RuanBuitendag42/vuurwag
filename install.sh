#!/usr/bin/env bash
# Vuurwag installer: a braai in ASCII for your Proxmox node.
#
#   # on the Proxmox node, as root
#   curl -fsSL https://raw.githubusercontent.com/RuanBuitendag42/vuurwag/main/install.sh | bash -s -- --tv
#
# Flags (no flags = install the files and the venv, enable nothing, print the next steps):
#   --tv              enable vuurwag-web (the page for the TV's browser) and open its port in pve-firewall
#   --monitor         enable vuurwag-kiosk (cage + foot on tty1) after a preflight; never leaves tty1 dead
#   --place "T, C"    town for the weather (default: the one in vuurwag/weather.py)
#   --port N          web port (default 8787)
#   --lan CIDR        LAN allowed to the web port (default: the network of the node's primary interface)
#   --public-url URL  URL the browser uses (default: http://<node ip>:<port>)
#   --bind IP         address the web page listens on (default 0.0.0.0, every address; opt-in to narrow it)
#   --fps N           frames a second, 1-20 (default 10; 4 for slow TV browsers)
#   --ref REF         git ref to install (default main)
#   --check           preflight and status only; changes nothing
#   --uninstall       remove vuurwag (asks before removing the vuurwag user and /etc/vuurwag)
#   --yes             answer yes to --uninstall's questions
#   --no-pve-check    do not insist on pveversion (testing outside Proxmox)
#   --local-src PATH  install from a directory or a .tar.gz instead of GitHub (testing)
#
# Rerunning the command upgrades in place. Nothing in here deletes guests, storage or config.
set -euo pipefail

REPO="RuanBuitendag42/vuurwag"
PREFIX="/opt/vuurwag"
SRC_DIR="${PREFIX}/src"
VENV="${PREFIX}/.venv"
ETC_DIR="/etc/vuurwag"
ENV_FILE="${ETC_DIR}/vuurwag.env"
UNIT_DIR="/etc/systemd/system"
KIOSK_USER="vuurwag"
KIOSK_HOME="/home/${KIOSK_USER}"
FW_TAG="# vuurwag-web"
KEY_TAG="vuurwag-kiosk@"
RUN_DIR="/var/lib/vuurwag"   # the web unit's WorkingDirectory: nothing importable in it
# What the 2026-10-09 hand deployment rsynced straight into /opt/vuurwag (now under src/).
LEGACY_ITEMS=(vuurwag deploy tests screenshots pyproject.toml uv.lock README.md DESIGN.md .gitignore .python-version .pytest_cache)
BASE_PKGS=(python3 python3-venv smartmontools lm-sensors curl ca-certificates iproute2)
MONITOR_PKGS=(cage foot seatd fonts-dejavu fontconfig openssh-client)

OPT_TV=0 OPT_MONITOR=0 OPT_CHECK=0 OPT_UNINSTALL=0 OPT_YES=0 OPT_NO_PVE=0
OPT_PLACE="" OPT_PORT="" OPT_LAN="" OPT_PUBLIC_URL="" OPT_FPS="" OPT_REF="main" OPT_LOCAL_SRC="" OPT_BIND=""
NODE_IP="" NODE_LAN="" NODE_NAME=""
FAILED=0
KIOSK_STARTING=0

say()  { printf '>> %s\n' "$*"; }
info() { printf '   %s\n' "$*"; }
warn() { printf '!! %s\n' "$*" >&2; }
die()  { printf 'vuurwag install: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Vuurwag installer - run as root on the Proxmox node:
  curl -fsSL https://raw.githubusercontent.com/RuanBuitendag42/vuurwag/main/install.sh | bash -s -- [flags]

  --tv              enable vuurwag-web (the page for the TV) and open its port in pve-firewall
  --monitor         enable vuurwag-kiosk (cage + foot on tty1) after a preflight
  --place "T, C"    town for the weather          --port N        web port (default 8787)
  --lan CIDR        LAN allowed to the web port   --public-url U  URL the browser uses
  --fps N           frames a second, 1-20         --ref REF       git ref (default main)
  --check           status only, changes nothing  --uninstall     remove vuurwag (--yes: no questions)
  --bind IP         web listen address (default 0.0.0.0 = every address, Tailscale included)
  --no-pve-check    allow non-Proxmox hosts       --local-src P   install from a dir or .tar.gz
No flags: install the files and the venv, enable nothing, print the next steps.
EOF
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --tv) OPT_TV=1 ;;
            --monitor) OPT_MONITOR=1 ;;
            --check) OPT_CHECK=1 ;;
            --uninstall) OPT_UNINSTALL=1 ;;
            --yes|-y) OPT_YES=1 ;;
            --no-pve-check) OPT_NO_PVE=1 ;;
            --place) [ $# -ge 2 ] || die "--place needs a value"; OPT_PLACE="$2"; shift ;;
            --port) [ $# -ge 2 ] || die "--port needs a value"; OPT_PORT="$2"; shift ;;
            --lan) [ $# -ge 2 ] || die "--lan needs a value"; OPT_LAN="$2"; shift ;;
            --public-url) [ $# -ge 2 ] || die "--public-url needs a value"; OPT_PUBLIC_URL="$2"; shift ;;
            --bind) [ $# -ge 2 ] || die "--bind needs a value"; OPT_BIND="$2"; shift ;;
            --fps) [ $# -ge 2 ] || die "--fps needs a value"; OPT_FPS="$2"; shift ;;
            --ref) [ $# -ge 2 ] || die "--ref needs a value"; OPT_REF="$2"; shift ;;
            --local-src) [ $# -ge 2 ] || die "--local-src needs a value"; OPT_LOCAL_SRC="$2"; shift ;;
            -h|--help) usage; exit 0 ;;
            *) die "unknown flag: $1 (try --help)" ;;
        esac
        shift
    done
    if [ -n "$OPT_PORT" ]; then
        [[ "$OPT_PORT" =~ ^[0-9]+$ ]] && [ "$OPT_PORT" -ge 1 ] && [ "$OPT_PORT" -le 65535 ] || die "--port must be 1-65535"
    fi
    if [ -n "$OPT_FPS" ]; then
        [[ "$OPT_FPS" =~ ^[0-9]+$ ]] && [ "$OPT_FPS" -ge 1 ] && [ "$OPT_FPS" -le 20 ] || die "--fps must be 1-20"
    fi
    if [ -n "$OPT_BIND" ] && ! valid_bind "$OPT_BIND"; then
        die "--bind must be an IPv4 or IPv6 address of this node (or 0.0.0.0 for every address)"
    fi
    if [ -n "$OPT_PLACE" ] && is_placeholder_place "$OPT_PLACE"; then
        die "--place \"${OPT_PLACE}\" is the README's placeholder: pass your own town, e.g. --place \"Bloemfontein, South Africa\""
    fi
    case "$OPT_PLACE" in
        *[\"\\\$\`]* | *$'\n'* | *$'\r'*) die "--place may not contain quotes, backslashes, \$, backticks or newlines" ;;
    esac
    if [ -n "$OPT_LAN" ] && ! [[ "$OPT_LAN" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}/[0-9]{1,2}$ ]]; then
        die "--lan must be an IPv4 CIDR such as 192.0.2.0/24"
    fi
    if [ -n "$OPT_PUBLIC_URL" ] && ! valid_public_url "$OPT_PUBLIC_URL"; then
        die "--public-url must look like http://host:port"
    fi
    [[ "$OPT_REF" =~ ^[A-Za-z0-9._/-]+$ ]] || die "--ref may only contain letters, digits and . _ / -"
    if [ "$OPT_CHECK" = 1 ] && [ "$OPT_UNINSTALL" = 1 ]; then
        die "--check and --uninstall do not mix"
    fi
}

# ─── helpers ──────────────────────────────────────────────────────────────────

have_systemd() { [ -d /run/systemd/system ] && command -v systemctl >/dev/null 2>&1; }

# systemctl that says so (instead of failing) when systemd is not running, e.g. in a container.
sctl() {
    if have_systemd; then
        systemctl "$@"
    else
        info "systemd is not running here: skipped 'systemctl $*'"
        return 0
    fi
}

unit_state() {  # unit -> "enabled/active" style summary, or "n/a"
    if ! have_systemd; then echo "n/a (systemd not running)"; return 0; fi
    local en ac
    en="$(systemctl is-enabled "$1" 2>/dev/null || true)"
    ac="$(systemctl is-active "$1" 2>/dev/null || true)"
    echo "${en:-unknown}/${ac:-unknown}"
}

# Never 'cmd | grep -q' in this script: with pipefail, grep -q exits at the first match, cmd dies of SIGPIPE
# (141) and the pipeline counts as failed. That is how a long fc-list "lost" an installed font on a real node.
# Capture the output first, then match.
contains() { [[ "$1" == *"$2"* ]]; }

pkg_installed() { contains "$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)" 'install ok installed'; }

DEJAVU_TTF="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# 0 if DejaVu Sans Mono is usable by foot; first hit wins: fontconfig, the file, the package.
font_check() {
    local fam
    if command -v fc-match >/dev/null 2>&1; then
        fam="$(fc-match -f '%{family}' 'DejaVu Sans Mono' 2>/dev/null || true)"
        case ",${fam}," in *",DejaVu Sans Mono,"*) return 0 ;; esac
    fi
    [ -f "$DEJAVU_TTF" ] && return 0
    pkg_installed fonts-dejavu-core && return 0
    return 1
}

font_diagnose() {  # so the next failure can be read from the output
    local out
    if command -v fc-list >/dev/null 2>&1; then
        out="$(fc-list 2>&1 || true)"
        info "  fc-list says (first 5 lines, stderr included):"
        printf '%s\n' "$out" | head -n 5 | sed 's/^/     /' || true
    else
        info "  fc-list is not installed (apt install fontconfig)"
    fi
    info "  fc-match 'DejaVu Sans Mono' -> $(fc-match 'DejaVu Sans Mono' 2>&1 || echo 'n/a'); ${DEJAVU_TTF}: $([ -f "$DEJAVU_TTF" ] && echo present || echo absent)"
}

# The README's example town, pasted literally, must not end up as the weather.
is_placeholder_place() {
    local first="${1%%,*}"
    first="$(printf '%s' "$first" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    [ "$first" = "your town" ]
}

python_ok() { python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; }

env_get() {  # key -> value from the env file (quotes stripped), empty if absent
    [ -f "$ENV_FILE" ] || return 0
    local v
    v="$(sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1)"
    v="${v#\"}"; v="${v%\"}"
    printf '%s' "$v"
}

env_set() {  # key value -> replace or append KEY="value" in the env file
    local key="$1" val="$2" tmp
    tmp="$(mktemp "${ETC_DIR}/.vuurwag.env.XXXXXX")"
    if grep -q "^${key}=" "$ENV_FILE"; then
        awk -v k="$key" -v line="${key}=\"${val}\"" 'index($0, k "=") == 1 { print line; next } { print }' "$ENV_FILE" >"$tmp"
    else
        cat "$ENV_FILE" >"$tmp"
        printf '%s="%s"\n' "$key" "$val" >>"$tmp"
    fi
    chmod 0644 "$tmp"
    mv -f "$tmp" "$ENV_FILE"
}

confirm() {  # question -> 0 for yes. --yes answers yes; no terminal answers no.
    local ans=""
    if [ "$OPT_YES" = 1 ]; then return 0; fi
    if ! { exec 3</dev/tty; } 2>/dev/null; then
        info "no terminal to ask '$1': keeping it (rerun with --yes to remove)"
        return 1
    fi
    printf '?? %s [y/N] ' "$1" >/dev/tty
    read -r ans <&3 || ans=""
    exec 3<&-
    case "$ans" in y|Y|yes|YES|ja|Ja) return 0 ;; *) return 1 ;; esac
}

detect_network() {
    NODE_NAME="$(uname -n)"; NODE_NAME="${NODE_NAME%%.*}"
    command -v ip >/dev/null 2>&1 || { warn "iproute2 (ip) not installed: cannot work out the node's address"; return 0; }
    local dev cidr
    dev="$(ip -4 route show default 2>/dev/null | awk '{ for (i = 1; i < NF; i++) if ($i == "dev") { print $(i + 1); exit } }')"
    [ -n "$dev" ] || { warn "no IPv4 default route: cannot work out the node's address"; return 0; }
    cidr="$(ip -o -4 addr show dev "$dev" scope global 2>/dev/null | awk '{ print $4; exit }')"
    [ -n "$cidr" ] || { warn "no IPv4 address on ${dev}"; return 0; }
    NODE_IP="${cidr%/*}"
    NODE_LAN="$(python3 -c 'import ipaddress, sys; print(ipaddress.ip_interface(sys.argv[1]).network)' "$cidr" 2>/dev/null || true)"
    info "primary interface ${dev}: ${cidr} (LAN ${NODE_LAN:-unknown})"
}

fw_file() { echo "/etc/pve/nodes/${NODE_NAME}/host.fw"; }

# "Status: enabled/running" -> 0; "disabled/..." or no pve-firewall -> 1
fw_enabled() { command -v pve-firewall >/dev/null 2>&1 && contains "$(pve-firewall status 2>/dev/null || true)" 'Status: enabled'; }

fw_rule() { echo "IN ACCEPT -source $1 -p tcp -dport $2 -log nolog ${FW_TAG}"; }

# ip -> 0 if it is a plain IPv4 or IPv6 address (no brackets, no port)
valid_bind() {
    local v4='^([0-9]{1,3}\.){3}[0-9]{1,3}$' v6='^[0-9A-Fa-f:]*:[0-9A-Fa-f:]*$'
    [[ "$1" =~ $v4 || "$1" =~ $v6 ]]
}

# url -> 0 if it is http(s)://host[:port][/path]; host is a name, an IPv4 or a bracketed [IPv6].
# Kept in a variable: inside [[ =~ ]] a literal '\]' in a bracket set ends the set early.
valid_public_url() {
    local re='^https?://(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9._-]+)(:[0-9]{1,5})?(/[A-Za-z0-9._~/-]*)?$'
    [[ "$1" =~ $re ]]
}

# host.fw content on stdin, rule, port -> one word on stdout:
#   present            the exact tagged rule is there
#   covered <line>     an untagged IN ACCEPT rule for this dport is there (a hand-made one): leave it
#   add                neither: fw_merge it
fw_plan() {
    awk -v rule="$1" -v port="$2" -v tag="$FW_TAG" '
        $0 == rule { found = "present" }
        /^[[:space:]]*#/ { next }
        index($0, tag) > 0 { next }
        $0 ~ /^[[:space:]]*IN[[:space:]]+ACCEPT([[:space:]]|$)/ && $0 ~ ("-dport[[:space:]]+" port "([[:space:]]|$)") {
            if (!covered) covered = $0
        }
        END { if (found) print found; else if (covered) print "covered " covered; else print "add" }'
}

# host.fw content on stdin, rule -> the content with any old vuurwag rule replaced by this one,
# placed first under [RULES] (the section is created if missing).
fw_merge() {
    awk -v rule="$1" -v tag="$FW_TAG" '
        index($0, tag) > 0 { next }
        { print }
        toupper($0) ~ /^\[RULES\]/ && !done { print rule; done = 1 }
        END { if (!done) { print ""; print "[RULES]"; print ""; print rule } }'
}

# authorized_keys on stdin, node -> the same without the restricted line whose key comment is exactly
# vuurwag-kiosk@<node>; other nodes' kiosk lines (a cluster shares this file) stay.
ak_without_node_key() {
    awk -v want=" ${KEY_TAG}$1" '
        { line = $0; sub(/[[:space:]]+$/, "", line) }
        index(line, "command=\"python3 -\",restrict ") > 0 && length(line) >= length(want) \
            && substr(line, length(line) - length(want) + 1) == want { next }
        { print }'
}

# 0 if /opt/vuurwag still has the hand deployment's flat layout (package and project files directly in it)
legacy_layout() { [ -d "${PREFIX}/vuurwag" ] || [ -f "${PREFIX}/pyproject.toml" ] || [ -f "${PREFIX}/uv.lock" ]; }

# ─── the source, the venv, the config ─────────────────────────────────────────

fetch_source() {
    say "fetching vuurwag (${OPT_LOCAL_SRC:-github.com/${REPO} @ ${OPT_REF}}) into ${SRC_DIR}"
    install -d -m 0755 "$PREFIX"
    local stage
    stage="$(mktemp -d "${PREFIX}/.src-new.XXXXXX")"
    if [ -n "$OPT_LOCAL_SRC" ] && [ -d "$OPT_LOCAL_SRC" ]; then
        tar -C "$OPT_LOCAL_SRC" --exclude=.git --exclude=.venv --exclude=__pycache__ --exclude=.pytest_cache -cf - . \
            | tar -C "$stage" --no-same-owner -xf -
    else
        local tarball="${stage}.tar.gz"
        if [ -n "$OPT_LOCAL_SRC" ]; then
            [ -f "$OPT_LOCAL_SRC" ] || { rm -rf "$stage"; die "--local-src ${OPT_LOCAL_SRC}: no such file or directory"; }
            cp -f "$OPT_LOCAL_SRC" "$tarball"
        else
            if ! curl -fsSL --retry 3 --connect-timeout 15 -o "$tarball" "https://github.com/${REPO}/archive/${OPT_REF}.tar.gz"; then
                rm -rf "$stage" "$tarball"
                die "could not download https://github.com/${REPO}/archive/${OPT_REF}.tar.gz"
            fi
        fi
        tar -C "$stage" --no-same-owner --strip-components=1 -xzf "$tarball" || { rm -rf "$stage" "$tarball"; die "the tarball would not unpack"; }
        rm -f "$tarball"
    fi
    if [ ! -f "${stage}/pyproject.toml" ] || [ ! -f "${stage}/requirements.txt" ] || [ ! -d "${stage}/deploy" ]; then
        rm -rf "$stage"
        die "the source has no pyproject.toml, requirements.txt or deploy/ - wrong --ref or --local-src?"
    fi
    chmod 0755 "$stage"
    # swap in one rename each way; the old tree goes only once the new one is in place
    local old="${PREFIX}/.src-old.$$"
    if [ -e "$SRC_DIR" ]; then mv "$SRC_DIR" "$old"; fi
    mv "$stage" "$SRC_DIR"
    rm -rf "$old"
}

build_venv() {
    say "python venv in ${VENV} (pinned dependencies from requirements.txt)"
    if [ -x "${VENV}/bin/python" ]; then
        local have want
        have="$("${VENV}/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo broken)"
        want="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        if [ "$have" != "$want" ]; then
            info "venv is python ${have}, system is ${want}: rebuilding it"
            rm -rf "$VENV"
        elif ! "${VENV}/bin/python" -m pip --version >/dev/null 2>&1 </dev/null; then
            # a venv made by 'uv sync' (the hand deployment) has no pip
            info "venv has no pip (made by uv?): rebuilding it"
            rm -rf "$VENV"
        fi
    fi
    [ -x "${VENV}/bin/python" ] || python3 -m venv "$VENV"
    export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1
    "${VENV}/bin/python" -m pip install --quiet --require-hashes -r "${SRC_DIR}/requirements.txt" </dev/null
    "${VENV}/bin/python" -m pip install --quiet --no-deps --force-reinstall "$SRC_DIR" </dev/null
    smoke_test
}

# The units run the venv's entry point (kiosk) and textual-serve runs 'python -P -m vuurwag' per tab
# (web). Try both, from ${PREFIX} on purpose: whatever lies in the cwd must not be what gets imported.
smoke_test() {
    local origin
    origin="$(cd "$PREFIX" && "${VENV}/bin/python" -P -c 'import vuurwag; print(vuurwag.__file__)' 2>/dev/null </dev/null || true)"
    case "$origin" in
        "${VENV}/"*) ;;
        *) die "python -P imports vuurwag from '${origin:-nowhere}', not from ${VENV}" ;;
    esac
    if ! (cd "$PREFIX" && "${VENV}/bin/python" -P -m vuurwag --demo --once >/dev/null 2>&1 </dev/null); then
        die "the new venv does not run: ${VENV}/bin/python -P -m vuurwag --demo --once failed"
    fi
    if ! "${VENV}/bin/vuurwag" --demo --once >/dev/null 2>&1 </dev/null; then
        die "the new venv does not run: ${VENV}/bin/vuurwag --demo --once failed"
    fi
    info "ok: imports from ${origin%/__init__.py}"
    info "ok: $("${VENV}/bin/vuurwag" --demo --once 2>/dev/null </dev/null | head -n 1)"
}

# Remove what the hand deployment rsynced straight into /opt/vuurwag; leaves src/ and .venv alone.
clean_legacy() {
    legacy_layout || return 0
    say "removing the old hand-deployed layout from ${PREFIX}"
    local item
    for item in "${LEGACY_ITEMS[@]}"; do
        if [ -e "${PREFIX}/${item}" ]; then
            rm -rf "${PREFIX:?}/${item}"
            info "removed ${PREFIX}/${item}"
        fi
    done
}

default_place() {
    "${VENV}/bin/python" -c 'from vuurwag.weather import DEFAULT_PLACE; print(DEFAULT_PLACE)' 2>/dev/null || true
}

# the address vuurwag-web listens on: --bind if given, else every address. 0.0.0.0 keeps the page reachable over
# Tailscale and survives a DHCP change of the node's address; --bind IP narrows it (opt-in).
default_bind() {
    if [ -n "$OPT_BIND" ]; then echo "$OPT_BIND"; return 0; fi
    echo "0.0.0.0"
}

# the loud line for a page without login that pve-firewall does not guard
fw_unguarded_warning() {  # port
    local where
    where="$(env_get VUURWAG_BIND)"; where="${where:-0.0.0.0}"
    if command -v pve-firewall >/dev/null 2>&1; then
        warn "pve-firewall is DISABLED on this node: the page (no login) is open to every network that can reach ${where}:$1."
    else
        warn "no pve-firewall found: the page (no login) is open to every network that can reach ${where}:$1."
    fi
    warn "  Keep it on a trusted LAN or Tailscale, or narrow it with --bind IP."
}

warn_place() {  # the place we ended up with -> a loud line when it is the default or the README placeholder
    local place="$1" def
    def="$(default_place)"
    if is_placeholder_place "$place"; then
        warn "weather place is the README placeholder '${place}': rerun with --place \"Town, Country\" (your own town)"
    elif [ -z "$OPT_PLACE" ] && [ "$place" = "$def" ]; then
        warn "weather place not set: using ${place}; rerun with --place \"Town, Country\""
    fi
}

write_env() {
    install -d -m 0755 "$ETC_DIR"
    local port="${OPT_PORT:-8787}"
    local url="${OPT_PUBLIC_URL:-http://${NODE_IP:-127.0.0.1}:${port}}"
    if [ ! -f "$ENV_FILE" ]; then
        say "writing ${ENV_FILE}"
        local place="${OPT_PLACE:-$(default_place)}"
        local bind
        bind="$(default_bind)"
        local tmp
        tmp="$(mktemp "${ETC_DIR}/.vuurwag.env.XXXXXX")"
        cat >"$tmp" <<EOF
# ${ENV_FILE} - read by vuurwag-web and vuurwag-kiosk (systemd EnvironmentFile).
# Edit it, then: systemctl restart vuurwag-web vuurwag-kiosk
# Rerunning the installer only changes the keys you pass as flags.

# Town for the weather (Open-Meteo, no key). Most specific part first; it falls back part by part.
VUURWAG_PLACE="${place}"
# Port of the web page for the TV (vuurwag-web).
VUURWAG_PORT="${port}"
# The address vuurwag-web listens on (0.0.0.0 = every network the node is on; the page has no login).
VUURWAG_BIND="${bind}"
# The LAN allowed to that port through pve-firewall (the installer's host rule).
VUURWAG_LAN="${OPT_LAN:-${NODE_LAN:-}}"
# The URL the browser uses to reach the page; textual-serve builds its websocket URL from it.
VUURWAG_PUBLIC_URL="${url}"
# Frames a second, 1-20. 4 is plenty for a slow TV browser.
VUURWAG_FPS="${OPT_FPS:-10}"
EOF
        chmod 0644 "$tmp"
        mv -f "$tmp" "$ENV_FILE"
    else
        say "keeping ${ENV_FILE} (updating only the keys given as flags)"
        [ -z "$OPT_PLACE" ] || env_set VUURWAG_PLACE "$OPT_PLACE"
        [ -z "$OPT_PORT" ] || env_set VUURWAG_PORT "$OPT_PORT"
        [ -z "$OPT_LAN" ] || env_set VUURWAG_LAN "$OPT_LAN"
        [ -z "$OPT_FPS" ] || env_set VUURWAG_FPS "$OPT_FPS"
        if [ -n "$OPT_PUBLIC_URL" ] || [ -n "$OPT_PORT" ]; then
            env_set VUURWAG_PUBLIC_URL "$url"
        fi
        if [ -z "$(env_get VUURWAG_LAN)" ] && [ -n "$NODE_LAN" ]; then env_set VUURWAG_LAN "$NODE_LAN"; fi
        # keys added since the first release: fill them in once, never overwrite what is there
        if [ -n "$OPT_BIND" ] || ! grep -q '^VUURWAG_BIND=' "$ENV_FILE"; then env_set VUURWAG_BIND "$(default_bind)"; fi
        if [ -z "$(env_get VUURWAG_PLACE)" ]; then env_set VUURWAG_PLACE "$(default_place)"; fi
    fi
    warn_place "$(env_get VUURWAG_PLACE)"
    sed 's/^/   | /' "$ENV_FILE" | grep -v '^   | #' | grep -v '^   | $' || true
}

# the address to test the page on: the bind address, or loopback when it listens everywhere
web_probe_host() {
    local b
    b="$(env_get VUURWAG_BIND)"
    case "$b" in ""|0.0.0.0|::) echo 127.0.0.1 ;; *:*) echo "[$b]" ;; *) echo "$b" ;; esac
}

install_units() {
    say "staging systemd units in ${UNIT_DIR}"
    install -d -m 0755 "$UNIT_DIR"
    install -m 0644 "${SRC_DIR}/deploy/vuurwag-web.service" "${UNIT_DIR}/vuurwag-web.service"
    install -m 0644 "${SRC_DIR}/deploy/vuurwag-kiosk.service" "${UNIT_DIR}/vuurwag-kiosk.service"
    install -d -m 0755 "$RUN_DIR"
    sctl daemon-reload
}

# ─── the TV ───────────────────────────────────────────────────────────────────

firewall_add() {
    local lan port rule file tmp
    lan="$(env_get VUURWAG_LAN)"; port="$(env_get VUURWAG_PORT)"
    if [ -z "$lan" ]; then
        warn "no LAN known (pass --lan CIDR): not touching pve-firewall"
        return 0
    fi
    rule="$(fw_rule "$lan" "$port")"
    file="$(fw_file)"
    if ! fw_enabled; then
        fw_unguarded_warning "$port"
        info "with pve-firewall enabled, this rule under [RULES] in ${file} would admit only the LAN:"
        info "  ${rule}"
        return 0
    fi
    local plan
    plan="$({ [ -f "$file" ] && cat "$file"; true; } | fw_plan "$rule" "$port")"
    case "$plan" in
        present)
            info "pve-firewall: rule already there (${lan} -> ${port}/tcp)"
            return 0 ;;
        covered\ *)
            info "pve-firewall: an existing rule already opens ${port}/tcp, leaving it as it is:"
            info "  ${plan#covered }"
            return 0 ;;
    esac
    if [ ! -d "$(dirname "$file")" ]; then
        warn "no $(dirname "$file") - is ${NODE_NAME} the Proxmox node name? Add this under [RULES] yourself:"
        info "  ${rule}"
        return 0
    fi
    say "pve-firewall: allowing ${lan} to ${port}/tcp in ${file}"
    tmp="$(mktemp)"
    { [ -f "$file" ] && cat "$file"; true; } | fw_merge "$rule" >"$tmp"
    # /etc/pve is pmxcfs: write the file in place, never rename over it
    cat "$tmp" >"$file"
    rm -f "$tmp"
}

firewall_remove() {
    local file tmp
    file="$(fw_file)"
    [ -f "$file" ] && grep -qF "$FW_TAG" "$file" || return 0
    say "pve-firewall: removing the vuurwag rule from ${file}"
    tmp="$(mktemp)"
    grep -vF "$FW_TAG" "$file" >"$tmp" || true
    cat "$tmp" >"$file"
    rm -f "$tmp"
}

enable_web() {
    say "vuurwag-web (the page for the TV)"
    firewall_add
    if ! have_systemd; then
        info "systemd is not running here: vuurwag-web staged but not started; nothing to verify"
        return 0
    fi
    systemctl enable vuurwag-web >/dev/null 2>&1
    systemctl restart vuurwag-web
    local port i host
    port="$(env_get VUURWAG_PORT)"
    host="$(web_probe_host)"
    for i in $(seq 1 20); do
        if curl -fsI --max-time 2 "http://${host}:${port}" >/dev/null 2>&1; then
            info "ok: answering on ${host}:${port} after ${i}s"
            return 0
        fi
        sleep 1
    done
    warn "vuurwag-web did not answer on ${host}:${port} within 20 s; see: journalctl -u vuurwag-web -n 50"
    FAILED=1
}

# ─── the monitor ──────────────────────────────────────────────────────────────

root_authorized_keys() {
    # On Proxmox /root/.ssh/authorized_keys is a symlink into /etc/pve/priv (pmxcfs): edit it in place.
    install -d -m 0700 /root/.ssh
    local f=/root/.ssh/authorized_keys
    [ -e "$f" ] || { : >"$f"; chmod 0600 "$f"; }
    echo "$f"
}

setup_kiosk_user() {
    say "kiosk user '${KIOSK_USER}' and its ssh key"
    local groups="" g
    for g in video input render; do
        getent group "$g" >/dev/null 2>&1 && groups="${groups:+${groups},}${g}"
    done
    if ! id "$KIOSK_USER" >/dev/null 2>&1; then
        useradd -m -d "$KIOSK_HOME" -s /bin/bash ${groups:+-G "$groups"} "$KIOSK_USER"
        info "created user ${KIOSK_USER} (groups: ${groups:-none})"
    elif [ -n "$groups" ]; then
        usermod -a -G "$groups" "$KIOSK_USER"
    fi
    install -d -m 0700 -o "$KIOSK_USER" -g "$KIOSK_USER" "${KIOSK_HOME}/.ssh"
    if [ ! -f "${KIOSK_HOME}/.ssh/id_ed25519" ]; then
        runuser -u "$KIOSK_USER" -- ssh-keygen -q -t ed25519 -N '' -C "${KEY_TAG}${NODE_NAME}" -f "${KIOSK_HOME}/.ssh/id_ed25519" </dev/null
    fi
    local pub blob line ak tmp
    pub="$(cat "${KIOSK_HOME}/.ssh/id_ed25519.pub")"
    blob="$(awk '{ print $2 }' <<<"$pub")"
    line="from=\"127.0.0.1,::1\",command=\"python3 -\",restrict ${pub}"
    ak="$(root_authorized_keys)"
    if grep -qxF "$line" "$ak"; then
        info "root's authorized_keys: restricted line already there"
    else
        tmp="$(mktemp)"
        grep -vF " ${blob}" "$ak" >"$tmp" || true
        printf '%s\n' "$line" >>"$tmp"
        cat "$tmp" >"$ak"
        rm -f "$tmp"
        info "root's authorized_keys: added one line (localhost only, forced to 'python3 -', restrict)"
    fi
    # pre-seed known_hosts so BatchMode ssh to 127.0.0.1 never stops to ask
    local kh="${KIOSK_HOME}/.ssh/known_hosts" scan
    scan="$(ssh-keyscan -T 5 127.0.0.1 2>/dev/null | grep -v '^#' || true)"
    if [ -n "$scan" ]; then
        tmp="$(mktemp)"
        { [ -f "$kh" ] && grep -v -e '^127\.0\.0\.1[ ,]' -e '^# 127\.0\.0\.1:' "$kh"; true; } >"$tmp"
        printf '%s\n' "$scan" >>"$tmp"
        install -m 0644 -o "$KIOSK_USER" -g "$KIOSK_USER" "$tmp" "$kh"
        rm -f "$tmp"
    else
        warn "ssh-keyscan 127.0.0.1 got nothing - is sshd running?"
    fi
    if [ ! -f "${KIOSK_HOME}/.config/foot/foot.ini" ]; then
        install -d -m 0755 -o "$KIOSK_USER" -g "$KIOSK_USER" "${KIOSK_HOME}/.config" "${KIOSK_HOME}/.config/foot"
        install -m 0644 -o "$KIOSK_USER" -g "$KIOSK_USER" "${SRC_DIR}/deploy/foot.ini" "${KIOSK_HOME}/.config/foot/foot.ini"
        info "installed ${KIOSK_HOME}/.config/foot/foot.ini"
    else
        info "keeping your ${KIOSK_HOME}/.config/foot/foot.ini"
    fi
}

# Prints every reason the kiosk cannot start; returns non-zero if there is one.
kiosk_preflight() {
    local bad=0 b
    if ! id "$KIOSK_USER" >/dev/null 2>&1; then
        info "preflight: no user ${KIOSK_USER}"; bad=1
    fi
    for b in cage foot seatd; do
        if ! command -v "$b" >/dev/null 2>&1; then info "preflight: ${b} is not installed"; bad=1; fi
    done
    if ! font_check; then
        info "preflight: DejaVu Sans Mono not found (apt install fonts-dejavu fontconfig; fc-cache -f)"; bad=1
        font_diagnose
    fi
    if [ ! -e /dev/tty1 ]; then info "preflight: there is no /dev/tty1"; bad=1; fi
    if ! have_systemd; then
        info "preflight: systemd is not running"; bad=1
    elif ! systemctl is-active --quiet seatd; then
        info "preflight: seatd is not active (systemctl enable --now seatd)"; bad=1
    fi
    if id "$KIOSK_USER" >/dev/null 2>&1 && command -v ssh >/dev/null 2>&1; then
        if ! runuser -u "$KIOSK_USER" -- ssh -o BatchMode=yes -o ConnectTimeout=5 root@127.0.0.1 true </dev/null >/dev/null 2>&1; then
            info "preflight: '${KIOSK_USER}' cannot ssh to root@127.0.0.1 (key, known_hosts or sshd)"; bad=1
        fi
    else
        info "preflight: cannot test ssh to root@127.0.0.1 (no user or no ssh client)"; bad=1
    fi
    if ! grep -qs pam_systemd /etc/pam.d/common-session /etc/pam.d/login; then
        info "preflight: pam_systemd is not in the login PAM stack (no XDG_RUNTIME_DIR for cage)"; bad=1
    fi
    if [ ! -x "${VENV}/bin/vuurwag" ]; then info "preflight: ${VENV}/bin/vuurwag is missing"; bad=1; fi
    if [ ! -f "${UNIT_DIR}/vuurwag-kiosk.service" ]; then info "preflight: the kiosk unit is not staged"; bad=1; fi
    return "$bad"
}

kiosk_rollback() {
    warn "rolling the kiosk back: tty1 gets its login prompt again"
    if have_systemd; then
        systemctl disable --now vuurwag-kiosk >/dev/null 2>&1 || true
        systemctl reset-failed vuurwag-kiosk >/dev/null 2>&1 || true
        systemctl enable getty@tty1 >/dev/null 2>&1 || true
        systemctl start getty@tty1 >/dev/null 2>&1 || true
    fi
    KIOSK_STARTING=0
}

on_exit() {
    local rc=$?
    if [ "$KIOSK_STARTING" = 1 ]; then kiosk_rollback; fi
    exit "$rc"
}

enable_kiosk() {
    say "vuurwag-kiosk (cage + foot on tty1)"
    if have_systemd && ! systemctl is-active --quiet seatd 2>/dev/null; then
        systemctl enable --now seatd >/dev/null 2>&1 || true
    fi
    if ! kiosk_preflight; then
        warn "preflight failed: vuurwag-kiosk NOT enabled; tty1 keeps its login prompt"
        if have_systemd && { systemctl is-enabled --quiet vuurwag-kiosk 2>/dev/null || systemctl is-active --quiet vuurwag-kiosk 2>/dev/null; }; then
            kiosk_rollback
        fi
        FAILED=1
        return 0
    fi
    info "preflight ok"
    KIOSK_STARTING=1
    # getty@tty1 stays enabled: the kiosk's Conflicts= wins at boot and OnFailure= brings getty back
    systemctl enable getty@tty1 >/dev/null 2>&1 || true
    systemctl enable vuurwag-kiosk >/dev/null 2>&1
    systemctl restart vuurwag-kiosk
    local i up=0 state restarts
    for i in $(seq 1 20); do
        sleep 1
        state="$(systemctl show -p ActiveState --value vuurwag-kiosk)"
        restarts="$(systemctl show -p NRestarts --value vuurwag-kiosk)"
        if [ "$state" = active ] && [ "${restarts:-0}" = 0 ]; then up=$((up + 1)); else up=0; fi
        if [ "$up" -ge 5 ]; then
            info "ok: vuurwag-kiosk active for 5 s (after ${i}s)"
            KIOSK_STARTING=0
            return 0
        fi
    done
    warn "vuurwag-kiosk did not stay up (state ${state}, restarts ${restarts}); see: journalctl -u vuurwag-kiosk -n 50"
    kiosk_rollback
    FAILED=1
}

# ─── check / uninstall ────────────────────────────────────────────────────────

do_check() {
    say "vuurwag --check (changes nothing)"
    if command -v pveversion >/dev/null 2>&1; then info "proxmox: $(pveversion 2>/dev/null | head -n 1)"; else info "proxmox: pveversion not found"; fi
    if command -v python3 >/dev/null 2>&1; then
        info "python3: $(python3 -V 2>&1) ($(python_ok && echo 'ok, >= 3.11' || echo 'TOO OLD, need >= 3.11'))"
    else
        info "python3: not installed"
    fi
    local p missing=""
    for p in "${BASE_PKGS[@]}"; do pkg_installed "$p" || missing="${missing} ${p}"; done
    info "base packages: ${missing:+missing:}${missing:-all installed}"
    missing=""
    for p in "${MONITOR_PKGS[@]}"; do pkg_installed "$p" || missing="${missing} ${p}"; done
    info "monitor packages: ${missing:+missing:}${missing:-all installed}"
    if have_systemd; then info "systemd: running"; else info "systemd: NOT running (container?) - unit states are not available"; fi
    detect_network
    if [ -f "${SRC_DIR}/pyproject.toml" ]; then
        info "source: ${SRC_DIR} ($(sed -n 's/^version = "\(.*\)"/version \1/p' "${SRC_DIR}/pyproject.toml" | head -n 1))"
    else
        info "source: not installed"
    fi
    if legacy_layout; then
        info "legacy: ${PREFIX} still has the hand-deployed flat layout; an install removes:$(for i in "${LEGACY_ITEMS[@]}"; do [ -e "${PREFIX}/${i}" ] && printf ' %s' "$i"; done; true)"
    fi
    local origin
    origin="$(cd / && "${VENV}/bin/python" -P -c 'import vuurwag; print(vuurwag.__file__)' 2>/dev/null </dev/null || true)"
    if [ -x "${VENV}/bin/vuurwag" ] && [ -n "$origin" ]; then
        info "venv: ${VENV} ok ($("${VENV}/bin/python" -V 2>&1), vuurwag from ${origin%/__init__.py})"
        "${VENV}/bin/python" -m pip --version >/dev/null 2>&1 </dev/null || info "venv: has no pip (made by uv?) - an install rebuilds it"
    else
        info "venv: missing or broken"
    fi
    if [ -f "$ENV_FILE" ]; then
        info "config: ${ENV_FILE}"
        grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/     /' || true
    else
        info "config: ${ENV_FILE} not written yet"
    fi
    local u
    for u in vuurwag-web vuurwag-kiosk; do
        if [ -f "${UNIT_DIR}/${u}.service" ]; then info "unit ${u}: staged, $(unit_state "$u")"; else info "unit ${u}: not staged"; fi
    done
    info "unit getty@tty1: $(unit_state getty@tty1)"
    local port lan
    port="$(env_get VUURWAG_PORT)"; port="${port:-8787}"
    lan="$(env_get VUURWAG_LAN)"; lan="${lan:-${NODE_LAN:-<unknown>}}"
    if command -v pve-firewall >/dev/null 2>&1; then
        local st; st="$(pve-firewall status 2>/dev/null | head -n 1 || true)"
        info "pve-firewall: ${st:-unknown}"
        local plan
        plan="$({ [ -f "$(fw_file)" ] && cat "$(fw_file)"; true; } | fw_plan "$(fw_rule "$lan" "$port")" "$port")"
        if [ -f "$(fw_file)" ] && grep -qF "$FW_TAG" "$(fw_file)"; then
            info "firewall rule: present: $(grep -F "$FW_TAG" "$(fw_file)" | head -n 1)"
        elif [ "${plan%% *}" = covered ]; then
            info "firewall rule: ${port}/tcp already opened by an existing rule: ${plan#covered }"
        else
            info "firewall rule: absent (would be: $(fw_rule "$lan" "$port"))"
        fi
        if ! fw_enabled; then fw_unguarded_warning "$port" 2>&1; fi
    else
        info "pve-firewall: not found"
        fw_unguarded_warning "$port" 2>&1
    fi
    local host place
    host="$(web_probe_host)"
    if command -v curl >/dev/null 2>&1 && curl -fsI --max-time 2 "http://${host}:${port}" >/dev/null 2>&1; then
        info "web: answering on ${host}:${port} -> $(env_get VUURWAG_PUBLIC_URL)"
    else
        info "web: nothing answering on ${host}:${port}"
    fi
    place="$(env_get VUURWAG_PLACE)"
    if is_placeholder_place "$place"; then
        info "weather place: '${place}' is the README placeholder - rerun with --place \"Town, Country\""
    elif [ -n "$place" ]; then
        info "weather place: ${place}"
    fi
    if kiosk_preflight; then info "monitor preflight: ok"; else info "monitor preflight: not ready (the reasons above); --monitor would refuse to enable the kiosk"; fi
    return 0
}

do_uninstall() {
    say "uninstalling vuurwag"
    detect_network
    local u
    for u in vuurwag-kiosk vuurwag-web; do
        if have_systemd; then
            systemctl disable --now "$u" >/dev/null 2>&1 || true
            systemctl reset-failed "$u" >/dev/null 2>&1 || true
        fi
        if [ -f "${UNIT_DIR}/${u}.service" ]; then rm -f "${UNIT_DIR}/${u}.service"; info "removed ${UNIT_DIR}/${u}.service"; fi
    done
    sctl daemon-reload
    say "tty1: making sure the login prompt is back"
    sctl enable getty@tty1
    if have_systemd && ! systemctl is-active --quiet getty@tty1; then systemctl start getty@tty1 || true; fi
    local ak=/root/.ssh/authorized_keys tmp
    if [ -f "$ak" ] && grep -qF "${KEY_TAG}${NODE_NAME}" "$ak"; then
        tmp="$(mktemp)"
        ak_without_node_key "$NODE_NAME" <"$ak" >"$tmp"
        # on a cluster this file is shared through /etc/pve/priv: only this node's line goes; write in place
        cat "$tmp" >"$ak"
        rm -f "$tmp"
        info "removed this node's kiosk key (${KEY_TAG}${NODE_NAME}) from ${ak}"
    fi
    firewall_remove
    if [ -d "$PREFIX" ]; then rm -rf "$PREFIX"; info "removed ${PREFIX}"; fi
    if [ -d "$RUN_DIR" ]; then rm -rf "$RUN_DIR"; info "removed ${RUN_DIR}"; fi
    if id "$KIOSK_USER" >/dev/null 2>&1; then
        if confirm "remove the user '${KIOSK_USER}' and ${KIOSK_HOME}?"; then
            pkill -u "$KIOSK_USER" >/dev/null 2>&1 || true
            userdel -r "$KIOSK_USER" >/dev/null 2>&1 || userdel "$KIOSK_USER" || true
            info "removed user ${KIOSK_USER}"
        fi
    fi
    if [ -d "$ETC_DIR" ]; then
        if confirm "remove ${ETC_DIR} (your place, port and fps)?"; then rm -rf "$ETC_DIR"; info "removed ${ETC_DIR}"; fi
    fi
    say "vuurwag is gone. Totsiens."
}

# ─── install ──────────────────────────────────────────────────────────────────

apt_install() {
    local p missing=()
    for p in "$@"; do pkg_installed "$p" || missing+=("$p"); done
    [ "${#missing[@]}" -gt 0 ] || { info "packages already installed: $*"; return 0; }
    say "apt-get install ${missing[*]}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq </dev/null || warn "apt-get update reported errors (an enterprise repo without a subscription?); trying the install anyway"
    apt-get install -y -qq --no-install-recommends "${missing[@]}" </dev/null
}

next_steps() {
    local url port
    port="$(env_get VUURWAG_PORT)"
    url="$(env_get VUURWAG_PUBLIC_URL)"
    cat <<EOF

Vuurwag is installed in ${PREFIX}; config in ${ENV_FILE}.
  try it here:        ${VENV}/bin/vuurwag            (q leaves; --demo for fake data)
  TV / browser:       rerun with --tv       -> ${url:-http://<node ip>:${port:-8787}}
  monitor on the node: rerun with --monitor  (cage + foot on tty1, with a preflight)
  status:             rerun with --check
EOF
}

do_install() {
    if [ "$OPT_NO_PVE" = 0 ]; then
        command -v pveversion >/dev/null 2>&1 || die "pveversion not found: this is not a Proxmox VE node (--no-pve-check to try anyway)"
        say "$(pveversion | head -n 1)"
    fi
    if command -v python3 >/dev/null 2>&1 && ! python_ok; then
        die "python3 is $(python3 -V 2>&1); vuurwag needs >= 3.11 (Proxmox VE 8 ships 3.11, 9 ships 3.13)"
    fi
    local pkgs=("${BASE_PKGS[@]}")
    [ "$OPT_MONITOR" = 0 ] || pkgs+=("${MONITOR_PKGS[@]}")
    apt_install "${pkgs[@]}"
    if [ "$OPT_MONITOR" = 1 ] && command -v fc-cache >/dev/null 2>&1; then
        # a font that was just unpacked is not in fontconfig's cache until this runs
        fc-cache -f >/dev/null 2>&1 || warn "fc-cache -f failed; the font check may not see DejaVu Sans Mono"
    fi
    python_ok || die "python3 >= 3.11 is still not available after apt"
    detect_network
    fetch_source
    build_venv
    # only now that the new install runs (its smoke test uses -P, so the old tree cannot interfere):
    # a failed download or venv build leaves the hand-deployed files where they were
    clean_legacy
    write_env
    install_units
    # an upgrade: restart what is already running so it picks up the new code and config
    if have_systemd; then
        [ "$OPT_TV" = 1 ] || systemctl try-restart vuurwag-web >/dev/null 2>&1 || true
        [ "$OPT_MONITOR" = 1 ] || systemctl try-restart vuurwag-kiosk >/dev/null 2>&1 || true
    fi
    if [ "$OPT_MONITOR" = 1 ]; then
        setup_kiosk_user
    fi
    [ "$OPT_TV" = 0 ] || enable_web
    [ "$OPT_MONITOR" = 0 ] || enable_kiosk
    say "done"
    local port url
    port="$(env_get VUURWAG_PORT)"; url="$(env_get VUURWAG_PUBLIC_URL)"
    if [ "$OPT_TV" = 1 ]; then
        info "TV: open ${url:-http://${NODE_IP:-<node ip>}:${port}} in the TV's browser (a kiosk browser app survives restarts better)"
    fi
    if [ "$OPT_MONITOR" = 1 ]; then
        info "monitor: font size lives in ${KIOSK_HOME}/.config/foot/foot.ini (1080p -> size=11, 4K -> ~22); then systemctl restart vuurwag-kiosk"
    fi
    if [ "$OPT_TV" = 0 ] && [ "$OPT_MONITOR" = 0 ]; then next_steps; fi
    if [ "$FAILED" = 1 ]; then
        warn "something did not come up - see the messages above; rerun with --check for the full picture"
        return 1
    fi
}

main() {
    parse_args "$@"
    [ "$(id -u)" = 0 ] || die "run me as root on the Proxmox node (curl ... | bash, from a root shell)"
    trap on_exit EXIT
    if [ "$OPT_CHECK" = 1 ]; then do_check; return 0; fi
    if [ "$OPT_UNINSTALL" = 1 ]; then do_uninstall; return 0; fi
    do_install
}

# tests/test_install_sh.sh sources this file with VUURWAG_INSTALL_SOURCED=1 to reach the functions
if [ "${VUURWAG_INSTALL_SOURCED:-0}" != 1 ]; then
    main "$@"
fi
