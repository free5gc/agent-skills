#!/usr/bin/env bash
# Read-only observations, not a support verdict.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd) || exit 64
# shellcheck source=common.sh
source "$script_dir/common.sh"
parse_args "$@"
context
# Parse only public OS metadata; never source /etc/os-release.
if [[ -r $system_root/etc/os-release ]] && os_metadata=$(bounded cat -- "$system_root/etc/os-release"); then
    os='' release=''
    while IFS='=' read -r key value; do
        value=${value//\"/}; value=${value//\'/}
        case "$key" in ID) os=$value;; VERSION_ID) release=$value;; esac
    done <<< "$os_metadata"
    if [[ $os == ubuntu ]]; then report PASS os "Ubuntu $release; verify selected-version support";
    else report UNKNOWN os "OS=$os version=$release; Ubuntu quick setup support not established"; fi
else report UNKNOWN os 'OS metadata absent/unreadable'; fi
if [[ -r $system_root/proc/cpuinfo ]]; then
    cpuinfo=$(bounded cat -- "$system_root/proc/cpuinfo")
    cpu_status=$?
    if ((cpu_status != 0)); then report UNKNOWN avx 'CPU flags observation unavailable';
    elif [[ $cpuinfo =~ (^|[[:space:]])avx([[:space:]]|$) ]]; then
        report PASS avx 'AVX exposed; architecture/official support still needs review'
    elif [[ $cpuinfo =~ (^|$'\n')flags[[:space:]]*: ]]; then report FAIL avx 'x86 CPU flags observed without AVX; resolve before quick setup';
    else report UNKNOWN avx 'no x86 flags; architecture/support requires review'; fi
else report UNKNOWN avx 'CPU metadata absent/unreadable'; fi
observe memory free -m
observe disk df -h -- "${repo:-.}"
observe addresses ip -br -4 addr
observe routes ip -4 route
observe dn-route ip -4 route get 8.8.8.8
for tool in git go make gcc node yarn mongosh; do
    case "$tool" in go) observe tool-go go version;; *) observe "tool-$tool" "$tool" --version;; esac
done
repo_observations
service_observations
report UNKNOWN support 'resource observations do not establish official compatibility'
finish
