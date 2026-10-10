# Preflight

Source: [quick setup](https://free5gc.org/guide/quick-setup/), selected script and
version pins in [sources](sources.md). Run checks before any system mutation.

1. Establish whether this is the Ubuntu target or only the agent workstation.
   On macOS/Windows, use an already authorized remote tool or ask the user to
   run target-host commands; never run a Linux installer on the workstation.
2. If unknown, ask: “How will you run free5GC and free-ran-ue? (1) one Ubuntu VM
   with network namespace isolation; (2) two VMs, core and simulator; (3) undecided,
   share your VM layout.” Reuse an existing answer. Separate terminals alone do
   not isolate networking.
3. Run `bash ACTUAL_SKILL_DIR/scripts/collect-env.sh --repo ACTUAL_CORE_DIR`.
   Resolve both paths from the installed skill/target, quote paths with spaces;
   do not assume `~/free5gc`. See [installation](installation.md) for transfer.
4. Review OS/version, CPU architecture and exposed AVX, kernel, memory, disk,
   IPv4 addresses/routes, tools, existing repo/submodules and mongod/module state.
   Record the host and network namespace in which evidence was collected.

The reviewed guide lists Ubuntu 20.04/22.04/24.04/25.04 and AMD/Intel AVX CPUs.
The script downloads linux-amd64 Go and MongoDB 8.2 packages. Treat ARM as
unresolved for this quick-setup path, even on Ubuntu; do not infer support from
MongoDB's arm64 repository entry. When AVX is absent, investigate hypervisor CPU
exposure versus physical CPU capability before installation. Recommend a
supported VM CPU or a separately reviewed manual installation, not a silent
MongoDB downgrade. An unavailable CPU observation is UNKNOWN, not absence.

These are source-reviewed conditions, not claims that all combinations were
runtime tested. Recheck sources for a newer/different version. The [manual build guide](https://free5gc.org/guide/3-install-free5gc/) recommends
at least 2 GB RAM and warns Webconsole may fail below 1 GB; these are guidance,
not a universal hard rejection threshold. No reviewed hard disk minimum was
found: report capacity and discuss build/storage risk without inventing one. Check kernel headers match
`uname -r` when investigating gtp5g; do not assert every kernel is supported.

Choose interfaces only after topology: use `ip -br -4 addr`, `ip -4 route`, and
`ip -4 route get 8.8.8.8`, then confirm RAN reachability and the DN egress route.
Multiple defaults/addresses require an explicit choice. Existing repo changes,
services or listeners require inspection before reuse, not cleanup or overwrite.
No observation here authorizes firewall changes, packages or namespace setup.
