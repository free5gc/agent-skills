# Final network configuration and Webconsole handoff

TestRegistration uses a separate configuration. After it passes and its
resources are removed, configure the actual installation for the user's future
simulator. Core configuration and host routing must be ready even though the
user will perform the actual DNN ping later.

## Select addresses and preserve configuration

Determine the intended core address and N6 egress interface from `ip -j address`,
`ip route`, and the user's topology. Use the primary non-loopback address on a
single-interface fresh host. With multiple plausible interfaces or a private
DN, resolve the actual RAN/DN path; do not select the first interface listed.
The N2/N3 address must be reachable by the future gNB. Cloud public NAT addresses
are not necessarily addresses the host can bind.

Back up affected files and use a YAML-aware edit that preserves string forms
and leading zeroes (MCC/MNC, TAC, SD). Do not globally replace IP strings or
modify test configs to look like deployment configs. For the common schema:

- AMF: `configuration.ngapIpList` contains the intended N2 listen address.
- SMF: N3 `endpoints` under `configuration.userplaneInformation.upNodes` advertises
  the routable UPF N3 address, not `0.0.0.0` or a test namespace address.
- UPF: `gtpu.ifList` N3 listener binds that address (or wildcard with an explicit
  routable address advertised by SMF).
- Preserve valid local SBI/NRF and N4 PFCP addresses for a single-host core.
  SMF's UPF nodeID/address must match UPF's PFCP configuration.

Keep the release's default PLMN, slices, and DNN unless the user specifies
otherwise. Validate consistency among AMF supported PLMN/TAI/slices/DNNs, NSSF
selection, SMF `snssaiInfos`, UPF topology and `sNssaiUpfInfos`, SMF N3
`networkInstances`, and UPF `dnnList`. Every offered slice/DNN must have a usable
UPF and consistent UE pool. Check dynamic/static pool relationships without
rejecting deliberate static subranges. Avoid overlap with host LAN/VPN routes.
If changing a pool, update SMF, UPF, routes and NAT together.

Run the bundled read-only common-schema check:

```bash
python3 "$F5GC_SKILL_DIR/scripts/check-config.py" "$F5GC_ROOT/config"
```

It checks N2/N3 addresses, key slice/DNN/pool relationships and PFCP consistency,
and prints the values for handoff. It does not validate every NF schema, host
routing, or external reachability. Unknown configuration schemas need source
inspection, not bypassing a failed check.

## Prepare N6 for the later DNN test

A DNN names a data network; it is not itself a ping destination. If the user
specifies a DN target, inspect the route to that target. For the default Internet
DNN, use the actual default-route egress; report the destination as user-selected
if no specific target is known. Do not invent an already-passed ping.

1. Enable `net.ipv4.ip_forward=1`. Save the prior value. If persistence is
   configured, use a dedicated sysctl file rather than repeatedly appending to
   global files.
2. Check N6 return routing for **all configured UE pools**. For Internet/private
   DN access without explicit return routes, add MASQUERADE scoped to each UE
   source CIDR and its egress interface. If the DN explicitly routes back to the
   UE pools, use that topology instead of adding unnecessary NAT.
3. Allow forwarding from UE pools toward N6 and established/related return
   traffic. Check rule placement so earlier DROP/REJECT rules do not shadow the
   permit rules. Integrate with existing UFW/nftables/iptables management rather
   than flushing policy or disabling UFW. Make additions idempotent; use exact
   rule checks (`iptables -C` when using iptables) and record owned rules.
4. Check ingress for NGAP/SCTP and GTP-U/UDP from the intended RAN network
   (commonly 38412/SCTP and 2152/UDP; use configured ports). Do not expose all SBI,
   MongoDB, or PFCP listeners externally for a single-host deployment. Account
   for an external cloud firewall if the environment exposes one.
5. Inspect routes/interfaces created by UPF after startup. Leave UPF-managed
   tunnel resources under UPF control. For demonstrated routing trouble, inspect
   reverse-path filtering and encapsulation MTU before changing them; do not
   apply global sysctl changes on speculation. Record persistence limitations.

These checks prepare data-plane configuration; actual packet forwarding is
verified later by the user's simulator test.

## Start directly and check readiness

Run the core from the free5GC checkout in the verified privileged-capable
terminal described in [privileges.md](privileges.md):

```bash
cd "$F5GC_ROOT"
./run.sh
```

In a second agent-managed terminal, run Webconsole as the deployment user:

```bash
cd "$F5GC_ROOT/webconsole"
go run server.go
```

Set the selected Go toolchain on PATH in that terminal. Keep the built frontend
assets available; `go run server.go` starts the backend and does not replace the
frontend build. Do not install/use tmux or create service units for these two
processes. System services such as MongoDB retain their normal service handling.

Keep both commands alive while checking readiness and handing off the URL. Use
the agent's long-running terminal support and retain its session identifiers.
The intended flow is ordinary core/server execution, not a new process-management
framework. If tool terminals are torn down when the task ends, use plain
`nohup` with redirected stdin/output and recorded process IDs for the same
commands, keeping the Webconsole invocation as `go run server.go`. Before any
detached core launch, verify its sudo commands can run in that detached context;
a foreground terminal's cached password may not be available there.

Record owned process/session IDs, working directories, logs and stop/restart
commands. `go run` has a launcher and a server child: track both, and verify the
actual listener when stopping or restarting. Read `run.sh`'s signal behavior
and terminate its owned children as required, without global process-name kills.
Reuse healthy owned processes on resume. Do not report deployment complete if
either command exited with its launching tool, and do not promise reboot autostart.

Use bounded readiness checks rather than fixed sleeps alone:

- MongoDB responds to a query.
- Every NF expected by this release's `run.sh` remains running.
- Required NF registrations are present at NRF; use the installed API/auth
  scheme, not an invented universal `/health` endpoint.
- AMF is listening on the configured N2 address; UPF has its configured N3
  listener, and SMF/UPF establish PFCP association.
- Startup logs contain no unresolved fatal configuration or bind error.
- Webconsole serves its login page and frontend assets at the intended URL.
  A process, open port, or unrelated HTTP 200 is insufficient.

After readiness succeeds, revoke the temporary sudo lease (if one was created)
using [privileges.md](privileges.md), verify its removal, then repeat readiness
checks. Leave the final Core and Webconsole running. Stop/restart instructions
must account for normal sudo authentication being restored, including privileged
cleanup in the selected `run.sh` signal handler.

## Browser and next steps

Read Webconsole's selected configuration for port/bind address and verify its
login instructions. Releases using the documented defaults use `admin` /
`free5gc`; preserve preexisting accounts rather than restoring defaults.

For same-host browser access, prefer loopback binding. On a remote headless
host, prefer SSH forwarding to the configured port. Provide a concrete command
using the real SSH target, e.g. `ssh -N -L 5000:127.0.0.1:5000 user@host`, then
`http://localhost:5000` in the user's computer browser. If direct LAN access is
desired, bind/allow the intended network and provide that reachable URL.

Use the agent's browser opener or the local desktop opener when available.
Only claim the page was opened when that action succeeded. Leave Core and
Webconsole running after the agent task ends.

Include a compact table of the actual core parameters needed by the user's
subscriber and simulator: PLMN, TAC, S-NSSAI, DNN, UE pool, N2/N3 address/port and
N6 interface. The user chooses their own SUPI/authentication values, matching
subscriber and simulator. Do not create another subscriber after cleanup.

Link [Create Subscriber](https://free5gc.org/guide/Webconsole/Create-Subscriber-via-webconsole/)
and the [RAN/UE simulator guide](https://free-ran-ue.github.io/doc-user-guide/02-free-ran-ue/).
For a later same-host simulator, link its
[namespace instructions](https://free-ran-ue.github.io/doc-user-guide/03-namespace-free-ran-ue/).
Explain that the later ping must originate through the UE's tunnel/namespace
toward the chosen DN target; a host-shell ping does not test the UE path.
