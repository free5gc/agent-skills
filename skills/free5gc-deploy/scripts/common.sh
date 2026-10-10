#!/usr/bin/env bash
# Shared read-only CLI support; sourced only from the bundled script directory.
export LC_ALL=C
export GIT_OPTIONAL_LOCKS=0
pass_count=0 fail_count=0 unknown_count=0
repo='' system_root='/'
report() {
    local state=$1 key=$2 evidence=$3
    printf '%s [%s] %s\n' "$state" "$key" "$evidence"
    case "$state" in
        PASS) pass_count=$((pass_count + 1));;
        FAIL) fail_count=$((fail_count + 1));;
        *) unknown_count=$((unknown_count + 1));;
    esac
}
finish() {
    printf 'SUMMARY pass=%d fail=%d unknown=%d (observations only)\n' "$pass_count" "$fail_count" "$unknown_count"
    ((fail_count > 0)) && return 1
    ((unknown_count > 0)) && return 2
    return 0
}
usage() {
    printf 'Usage: %s [--repo PATH] [--system-root PATH] [--help]\n' "${0##*/}"
    printf '%s\n' 'Read-only; commands bounded to 5 seconds; never sudo.' \
        'check-install.sh requires --repo. system-root reads offline etc/proc files only.' \
        'Exit: 0 all PASS; 1 any FAIL; 2 unknown without FAIL; 64 invalid arguments.'
}
parse_args() {
    while (($#)); do
        case "$1" in
            --help) usage; exit 0;;
            --repo|--system-root)
                if (($# < 2)) || [[ -z $2 || $2 == --* ]]; then usage >&2; exit 64; fi
                if [[ $1 == --repo ]]; then repo=$2; else system_root=$2; fi
                shift 2;;
            *) usage >&2; exit 64;;
        esac
    done
    [[ -d $system_root ]] || { usage >&2; exit 64; }
}
# Never print raw stderr: diagnostics can include secrets or terminal escapes.
bounded() {
    command -v "$1" >/dev/null 2>&1 || return 127
    command -v timeout >/dev/null 2>&1 || return 127
    timeout -k 1s 5s "$@" </dev/null 2>/dev/null
}
observe() {
    local key=$1 output
    shift
    if output=$(bounded "$@"); then
        report PASS "$key" "$output"
    else
        report UNAVAILABLE "$key" 'command missing, denied, failed or timed out; inspect on target'
    fi
}
read_observation() {
    local key=$1 path=$2 output
    if [[ -r $path ]] && output=$(bounded cat -- "$path"); then
        report PASS "$key" "$output"
    else
        report UNKNOWN "$key" 'file absent or unreadable'
    fi
}
context() {
    observe host hostname
    observe kernel uname -r
    observe architecture uname -m
    observe network-namespace readlink /proc/self/ns/net
    if [[ $system_root != / ]]; then
        report UNKNOWN snapshot 'etc/proc files are offline snapshot; commands describe invoking host'
    fi
}
repo_observations() {
    if [[ -z $repo ]]; then report UNKNOWN repo 'no repo supplied'; return; fi
    if [[ ! -d $repo ]]; then report FAIL repo 'specified directory absent'; return; fi
    observe repo-commit git -C "$repo" rev-parse HEAD
    observe repo-changes git -C "$repo" status --short --untracked-files=no
    observe submodules git -C "$repo" submodule status --recursive
}
service_observations() {
    local state info
    # is-active may return nonzero while still providing a meaningful state.
    state=$(bounded systemctl is-active mongod) || true
    case "$state" in
        active) report PASS mongod-service 'active (connection health still requires runtime evidence)';;
        inactive|failed|activating|deactivating) report UNKNOWN mongod-service "state=$state; diagnose, not proof installation absent";;
        *) report UNAVAILABLE mongod-service 'service state not observable';;
    esac
    if info=$(bounded modinfo -F filename gtp5g); then
        if [[ -n $info ]]; then report PASS gtp5g-installed 'module found for running kernel';
        else report UNKNOWN gtp5g-installed 'empty module metadata'; fi
    else
        # modinfo failure alone cannot distinguish denial from absent module.
        report UNKNOWN gtp5g-installed 'modinfo unavailable/failed; module absence not established'
    fi
    if [[ -r $system_root/proc/modules ]]; then
        local modules
        if modules=$(bounded cat -- "$system_root/proc/modules"); then
            if [[ $modules =~ (^|$'\n')gtp5g[[:space:]] ]]; then
                report PASS gtp5g-loaded 'listed in proc/modules'
            else report UNKNOWN gtp5g-loaded 'not loaded; inspect installation before user-run modprobe'; fi
        else report UNKNOWN gtp5g-loaded 'module observation denied'; fi
    else report UNKNOWN gtp5g-loaded 'proc/modules absent or unreadable'; fi
}
