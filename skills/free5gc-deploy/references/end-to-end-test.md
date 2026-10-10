# Guided end-to-end test

Sources and version differences: [sources](sources.md). This is a user-executed
lesson, not an automatic test. Read the selected simulator YAML/Makefile and core
run.sh before producing commands. Reuse known values and pause at each checkpoint
for the key result. Substitute every `ACTUAL_*` from confirmed paths, routes,
configuration and tunnel observations before handing commands to a novice.

## Common preparation

Confirm core and simulator commits and local modifications. Check core DN route,
external ICMP reachability, N6 interface, IPv4 forwarding in the **UPF namespace**,
NAT/return routes and applicable firewall forwarding. A root-namespace ping only
checks that namespace's own egress. The current UPF can manage NAT/FORWARD via
`dnnList[].natifname` (preferred) or `natIfCIDR`, with `ipForwardEnable`; these do
not set kernel forwarding. Do not append old broad MASQUERADE/ACCEPT rules on top.
For versions without managed NAT, inspect existing rules and route design first,
then teach only the necessary scoped UE-pool egress/return rules. Privileged
inspection/changes belong in the user's terminal, never the diagnostic scripts.

| Terminal | Host | Network | Directory | User command/action | Expected result | Keep open | Privilege |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P | core VM | actual UPF network (default for reviewed topology) | actual core repo | `ip -br -4 addr`; `ip -4 route get 8.8.8.8`; `cat /proc/sys/net/ipv4/ip_forward`; `ping -c 5 8.8.8.8`; `ping -c 5 1.1.1.1` | Egress exists, forwarding 1; identify a reachable DN target | no | ordinary |
| P | core VM | same UPF network | actual core repo | `sudo iptables -t nat -S POSTROUTING`; `sudo iptables -S FORWARD` | Review scoped rules and policy; pre-start absence of managed rules can be normal | no | sudo, user only |
| B | simulator VM (two VM) or shared VM (single) | default | confirmed unused parent, then simulator repo | `git clone https://github.com/free-ran-ue/free-ran-ue.git`; `cd` actual cloned directory; `go version`; `make` | build/free-ran-ue executable; selected go.mod matches toolchain | no | ordinary build |

The reviewed simulator go.mod requires Go 1.26.2. Do not automatically replace a
user's Go install; if missing/incompatible, explain a version-appropriate install
step for their architecture in their terminal. UE command source explicitly
requires root to create its tunnel; gNB can run ordinarily on two VMs, while
entering namespace requires sudo. Do not enable ignoreSetupTunnel to hide errors.
Checkpoint: build and core egress ready before startup/configuration.

## Subscriber lesson (test data only)

The core's quick setup builds Webconsole; use its selected startup entrypoint.
The reviewed quick guide/Makefile use `webconsole/bin/webconsole` (older docs use
`go run server.go`). Open `http://ACTUAL_CORE_IP:5000` only from an authorized,
reachable browser/network. Verify actual listen settings; do not expose this lab
console to the Internet. In a fresh unmodified lab the documented login is admin /
free5gc; existing credentials may differ. Never ask for them in chat.

Explain that a subscriber is the core's record of the simulated SIM identity,
authentication and allowed data service. Click **SUBSCRIBERS → CREATE**. First
check that the test SUPI is unused; do not overwrite or drop a database.

Use this explicit public **test-only** set in an isolated lab. If the SUPI exists,
choose another ten-digit MSIN and update the simulator consistently.

| Webconsole field/action | Test value | Simulator/core match |
| --- | --- | --- |
| Subscriber data number | 1 | one test UE |
| SUPI (IMSI) | imsi-208930000000001 (digits 208930000000001 where UI asks IMSI) | ue.plmnId mcc "208", mnc "93", ue.msin "0000000001" |
| PLMNID | 20893 | AMF supported PLMN/TAI, gNB plmnId and tai.broadcastPlmnId |
| GPSI (MSISDN) if required | msisdn-0900000001 | test-only identifier; no real phone data |
| Authentication Method | 5G_AKA | simulator AKA flow |
| Permanent Authentication Key | 8baf473f2f8fd09487cccbd7097c6862 | ue.authenticationSubscription.encPermanentKey |
| Operator Code Type | OPc | simulator consumes OPc, not an OP entered as OPc |
| Operator Code Value | 8e27b6af0e692e750f32667a3b14605d | ue.authenticationSubscription.encOpcKey |
| Authentication Management Field | 8000 | ue.authenticationSubscription.authenticationManagementField (not AMF NF IP) |
| SQN | 000000000023 | ue.authenticationSubscription.sequenceNumber initially; it advances during authentication |
| Network Slicing / SST, SD | 1, 010203 | ue.pduSession.snssai; gnb.snssai; AMF and SMF slice mappings |
| DNN Configuration | internet | ue.pduSession.dnn; AMF supportDnnList; SMF and UPF dnnList |
| Session type / QoS / AMBR | IPv4; default 5QI 9; retain lab default AMBR unless incompatible | core's selected DNN supports IPv4; no custom flow/charging needed for ICMP |

Click CREATE, verify the test identity appears, then privately compare fields
with config/ue.yaml. Preserve leading zeros by quoting YAML identifiers. Existing
core PLMN/DNN/slices must either match this lab set or adapt all test values to
the confirmed core; never change production identities silently. No real K/OP/OPc,
subscriber dumps or credential screenshots are needed in chat. Checkpoint:
subscriber and simulator match before starting UE.

## Two VMs

Confirm VM networking supports core↔RAN traffic (bridged or routed/private shared
network; isolated hypervisor NAT may not). Record both actual IPs, routes and
reachability. Confirm SCTP N2 38412 and UDP N3 2152 plus simulator internal ports
31413/31414 where applicable; do not disable firewalls as a generic fix.

Set AMF `configuration.ngapIpList` to core's RAN-reachable N2 IP; SMF
`configuration.userplaneInformation.upNodes.UPF.interfaces` N3 endpoints and UPF
`gtpu.ifList[].addr` to the core N3 IP. Preserve PFCP/SBI loopbacks when all core
NFs are together. UPF `dnnList[].natifname` is the actual **N6 egress NIC**, which
may differ from N2/N3. In gnb.yaml, `gnb.amfN2Ip` / `upfN3Ip` point to core;
`ranN2Ip` / `ranN3Ip` are the simulator's respective NIC addresses. On the
simulator VM, set `gnb.ranControlPlaneIp` and `ranDataPlaneIp` to reachable local
addresses and match them in `ue.ranControlPlaneIp` and `ranDataPlaneIp`. Match
ports, PLMN/TAI (tac "000001" for this test) and slice. Update gnb.api.ip if used.
Read actual YAML before editing; these paths describe the reviewed revision.

| Terminal | Host | Network | Directory | User command | Expected result | Keep open | Privilege |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | core VM | default | actual core repo | `./run.sh` | Required NF logs/NRF registration; PFCP accepted; N2 listener | yes | script asks sudo; explain selected script's transient NF-profile DB cleanup |
| 2 | core VM | default | actual core repo/webconsole | `./bin/webconsole` | Console listening, DB reachable; follow subscriber lesson | yes | ordinary |
| 3 | simulator VM | default | actual simulator repo | `./build/free-ran-ue gnb -c config/gnb.yaml` | NG setup accepted, N2 connected | yes | ordinary |
| 4 | simulator VM | default | actual simulator repo | `sudo ./build/free-ran-ue ue -c config/ue.yaml` | Registration accepted, PDU session address, tunnel created | yes | sudo, user only |
| 5 | simulator VM | default | actual simulator repo | `ip -br addr`; then DN commands below | Identify actual tunnel/address and obtain replies through it | no | ordinary (ping capability needed) |

Checkpoint after core readiness, subscriber creation, gNB setup, and UE session;
when a checkpoint fails, diagnose that stage before continuing.

## Single VM with namespaces

The reviewed script keeps **core, MongoDB and Webconsole in the default/root
network namespace**, with RAN `free-ran-ns` and UE `free-ue-ns`. The guide's “three
namespaces” wording includes this default network; there is no created core-ns.
Its YAML example has `iifList`, a typo; the actual UPF key is `gtpu.ifList`.
This layout preserves core SBI/DB loopback reachability. If an existing deployment
puts the core in a separate namespace, stop and inspect its egress, forwarding,
NAT, DB/Webconsole reachability and every NF SBI/loopback address there; root
ping cannot verify that core namespace. Do not transplant this recipe unchanged.

Inspect `ip netns list`, active namespace PIDs (`sudo ip netns pids NAME`), current
veths and conflicting routes before setup. The official script's **up first
calls cleanup**, removing named namespaces/veths. Do not use it on live/unrelated
resources. Have the user stop affected processes first; choose an isolated VM
or reviewed adapted names/subnets if collisions exist. Setup changes the network
with sudo, but does not bring namespace loopback up; inspect `ip link show lo`
and have the user enable it only if their process requires loopback.

Reviewed connections: default `fnsHost` 10.0.1.1/24 ↔ RAN `fnsVeth` 10.0.1.2/24;
RAN `fnsGnb` 10.0.2.1/24 ↔ UE `fnsUe` 10.0.2.2/24. RAN default via 10.0.1.1;
UE default via 10.0.2.1. Check the host has no overlapping 10.0.1.0/24,
10.0.2.0/24 or selected UE pools. Host core retains its actual external N6 NIC.
Change core N2/N3 to **10.0.1.1** after setup, keeping DNN natifname on external
host egress, not fnsHost. Reviewed simulator default gnb.yaml/ue.yaml match these
links; still verify PLMN/slice/subscriber. No duplicate broad host NAT rules.

| Terminal | Host | Network | Directory | User command | Expected result | Keep open | Privilege |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S | shared Ubuntu VM | default | actual simulator repo | `make ns-up`; `ip netns list`; `ip -br addr` | Two named namespaces and documented veths/IPs, no unexpected removal | no | script invokes sudo, user only |
| 1 | shared VM | default (core) | actual core repo | `./run.sh` | Core readiness and PFCP; MongoDB/SBI in same network | yes | script asks sudo |
| 2 | shared VM | default (DB/console) | actual core repo/webconsole | `./bin/webconsole` | Reachable console; create test subscriber | yes | ordinary |
| 3 | shared VM | free-ran-ns | actual simulator repo | `make ns-ran`, then `./build/free-ran-ue gnb -c config/gnb.yaml` | Entered RAN shell; NG setup succeeds from 10.0.1.2 | yes | sudo for namespace entry |
| 4 | shared VM | free-ue-ns | actual simulator repo | `make ns-ue`, then `./build/free-ran-ue ue -c config/ue.yaml` | Entered privileged UE shell; registration/session and tunnel | yes | namespace shell is root |
| 5 | shared VM | free-ue-ns | actual simulator repo | `make ns-ue`, then `ip -br addr` and DN commands below | Tunnel observed in UE network; replies via it | no | sudo for entry |

`make ns-ran`/`ns-ue` enter a new Bash; confirm the working directory and namespace
in that shell before launch. Do not assume a different terminal means isolation.
Checkpoint: verify veth addresses/routes, default core egress, config alignment,
then each startup/subscriber/UE result in order.

## DN test and interpretation

At terminal 5 in the actual UE network, use ue.yaml `ue.ueTunnelDevice`, the UE
log, and `ip -br addr` to identify the created name. The reviewed command appends
an instance index (default base ueTun can become ueTun0); do not infer the final
name from a fixed example. Replace ACTUAL_UE_TUNNEL with the observed interface:

```bash
ip -4 addr show dev ACTUAL_UE_TUNNEL
ping -I ACTUAL_UE_TUNNEL -c 5 8.8.8.8
ping -I ACTUAL_UE_TUNNEL -c 5 1.1.1.1
```

In the single-VM case these commands run **inside free-ue-ns**, not default
network. Collect registration acceptance, PDU session acceptance/address, tunnel
information, ping interface/source and packet statistics. ICMP replies via the
explicit tunnel plus registration/session are E2E evidence; packet loss should
be reported, not hidden. If one DN blocks ICMP, compare the other reachable DN,
core egress and UPF counters before attributing failure. General host ping is
only preparation. Apply [verification](verification.md); route failed stages to
[troubleshooting](troubleshooting.md).

## Stop and cleanup

User stops UE first (Ctrl-C, check tunnel cleanup), gNB, then core/Webconsole;
exit namespace shells. Inspect remaining namespace PIDs and ask the user to stop
any that remain before `make ns-down` in the simulator repo/default network.
It deletes the documented veths/namespaces; never run teardown while in use.
Retain the test subscriber unless the user wants its deletion; delete only that
identified test record through Webconsole. Do not drop MongoDB, flush firewall
rules or kill unrelated processes.
