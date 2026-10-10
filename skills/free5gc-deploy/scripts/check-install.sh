#!/usr/bin/env bash
# No service startup, network mutation, installer execution or UE tests.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 64
# shellcheck source=common.sh
source "$script_dir/common.sh"
parse_args "$@"
[[ -n $repo ]] || { usage >&2; exit 64; }
context
repo_observations
for tool in git go make gcc node yarn mongosh ip iptables; do
    if command -v "$tool" >/dev/null 2>&1; then report PASS "tool-$tool" 'available; inspect selected-version requirements';
    else report UNAVAILABLE "tool-$tool" 'command missing'; fi
done
observe go-version go version
observe mongo-version mongosh --version
service_observations
# helpers emit only classified, sanitized evidence; never execute the Makefile.
for helper in inspect-artifacts.py check-config.py; do
    output=$(bounded python3 "$script_dir/$helper" "$repo")
    result=$?
    if ((result == 0 || result == 1 || result == 2)) && [[ -n $output ]]; then
        while IFS= read -r line; do
            case "$line" in
                PASS\ *) pass_count=$((pass_count + 1));;
                FAIL\ *) fail_count=$((fail_count + 1));;
                UNKNOWN\ *|UNAVAILABLE\ *) unknown_count=$((unknown_count + 1));;
                *) continue;;
            esac
            printf '%s\n' "$line"
        done <<< "$output"
    else report UNAVAILABLE "$helper" 'Python/helper unavailable, denied or timed out'; fi
done
report UNKNOWN runtime 'NF readiness, MongoDB connection, registration and UE ping not tested'
finish
