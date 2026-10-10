# Verification and diagnostic contract

Sources: selected [Makefile/script/configuration](sources.md),
[UPF NAT](https://free5gc.org/guide/10-UPF-Config/) and
[simulator test](https://free-ran-ue.github.io/doc-user-guide/02-free-ran-ue/).

| Level | Required evidence | Failure / unknown |
| --- | --- | --- |
| Installation verified | Selected Makefile's expected executable outputs, Webconsole frontend, appropriate tool versions, usable MongoDB, installed gtp5g for current kernel, parsed basic core config consistency, inspected local/submodule state | Missing expected artifacts or proven mismatch fails that check; unknown schema, unavailable tools or inaccessible state leaves the level unverified |
| Core startup verified | Required NFs from the selected run.sh/config, live processes **and** corresponding startup logs, NRF/SBI registration and SMF↔UPF PFCP association where applicable, AMF N2 listener | Processes alone do not prove readiness; bind/connect/auth errors fail affected stage; unreadable logs are unknown |
| E2E verified | UE registration accepted, matching successful PDU session and assigned address, actual tunnel with that address, ICMP replies explicitly via that tunnel in UE namespace/VM | A tunnel alone, host ping, install banner, success counter, exit code or binary alone cannot prove E2E |

Report each level independently, including evidence source, host/namespace and
observed time when available. Unrun registration/session/ping remain UNKNOWN.
A requested install-only scope can finish without E2E, explicitly unverified.
For a full connectivity request, use PARTIAL until E2E evidence is present.

## CLI contract

`collect-env.sh [--repo PATH]` and `check-install.sh --repo PATH` accept `--help`.
They are Bash, read-only, noninteractive, never sudo, never execute Makefiles,
source configs, start services, change routes/namespaces or install dependencies.
`--system-root PATH` selects an offline /etc,/proc snapshot for fixtures; command
observations still refer to the invoking host and are labeled separately.

Output is `PASS|FAIL|UNKNOWN|UNAVAILABLE [check-id] evidence`; UNAVAILABLE is an
UNKNOWN subtype. Summary counts are observations, not a deployment verdict.
Exit 0: all emitted checks PASS; 1: at least one proven FAIL (even with unknowns);
2: no FAIL but unknown/unavailable observations; 64: invalid CLI usage.
Commands have a five-second timeout; if `timeout` is unavailable they are skipped
as UNAVAILABLE. Missing command/read permission/timeout is never PASS. No raw
command stderr, config values, authentication secrets or DB documents are printed.

The artifact helper recognizes a conservative Go-NF Makefile shape and extracts
its own list/bin path. It never invokes make (even make -n can execute shell
expressions). Unknown/legacy C-UPF or changed rules are UNKNOWN: inspect that
version manually. Static YAML checks require Python3/PyYAML; no fragile grep
substitute. Supported scope is one UPF with AMF/SMF/UPF common schemas, matching
PLMN/slice/DNN/N3/PFCP/pools; runtime routing, NSSF/subscriber and NAT permissions
need separate evidence. PASS here is scoped, not complete configuration validation.

A recognized modinfo “module not found” result is FAIL for the running kernel;
other metadata errors are UNKNOWN. mongod `inactive`/`failed` means runtime unavailable for verification, not proof
that installation is absent. Inspect why via troubleshooting. Module installed,
loaded and inaccessible are distinct: an installed but unloaded module is an
unknown readiness observation. Restricted log access is UNKNOWN; offer specific
user-run diagnostics such as `sudo journalctl -u mongod -n 50 --no-pager` or
`sudo dmesg --level=err,warn` only for the relevant failure. Do not request a
wholesale sensitive log dump.
