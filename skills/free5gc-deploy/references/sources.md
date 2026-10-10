# Official source index

Checked 2026-10-10 (Asia/Taipei). Web pages are moving documentation, without a
release pin. GitHub raw files below were fetched at immutable commits and read,
never executed. Recheck selected target checkout before preparing commands.
Network-offline use may run local checks but must label upstream version status
unconfirmed. Source review is not runtime deployment validation.

| Topic | Official entry | Reviewed details |
| --- | --- | --- |
| Prerequisites / installer / startup | [Quick setup](https://free5gc.org/guide/quick-setup/) | Ubuntu list, AVX, full source semantics, user terminals |
| Installer implementation | [quick-setup.sh](https://github.com/free5gc/free5gc/blob/ab1280ed772ad1900a0c6c00ac4f7852eb9d491d/quick-setup.sh) | Go 1.26.2 amd64, gtp5g v0.9.16, MongoDB 8.2, UFW/forwarding, NAT selector, build and interactions |
| Build outputs / core schema | [Makefile](https://github.com/free5gc/free5gc/blob/ab1280ed772ad1900a0c6c00ac4f7852eb9d491d/Makefile), [config](https://github.com/free5gc/free5gc/tree/ab1280ed772ad1900a0c6c00ac4f7852eb9d491d/config), [run.sh](https://github.com/free5gc/free5gc/blob/ab1280ed772ad1900a0c6c00ac4f7852eb9d491d/run.sh) | Current Go NF list, Webconsole outputs, N2/N3/PFCP and DNN pools; run.sh does transient NF-profile cleanup |
| Configuration / manual install | [Guide index](https://free5gc.org/guide/), [manual build](https://free5gc.org/guide/3-install-free5gc/), [configuration](https://free5gc.org/guide/4-configure-free5gc/) | Follow relevant selected-version topics from index |
| Subscriber | [Create Subscriber via Webconsole](https://free5gc.org/guide/Webconsole/Create-Subscriber-via-webconsole/) | UI workflow and field names; retain existing records |
| N6 NAT | [UPF N6 configuration](https://free5gc.org/guide/10-UPF-Config/), [pinned UPF source](https://github.com/free5gc/go-upf/tree/616a4ff6cbd2e7de2bccd39399f37425f373bcc8) | natifname/natIfCIDR, UPF-local rules, forwarding sysctl distinct from ipForwardEnable |
| Failure diagnosis | [Troubleshooting](https://free5gc.org/guide/Troubleshooting/) | Kernel/module and PFCP clues; historical destructive remedies not adopted |
| Simulator index | [User guide](https://free-ran-ue.github.io/doc-user-guide/) | Core integration, build, namespace links |
| Core integration | [free5GC](https://free-ran-ue.github.io/doc-user-guide/01-free5gc/) | Compare core YAML and subscriber; outdated broad rules not copied |
| Simulator build / gNB / UE / ICMP | [free-ran-ue](https://free-ran-ue.github.io/doc-user-guide/02-free-ran-ue/) | Go 1.26.2, 13e4063a1cf913f5606d57d42ab83a86f5001e04, tunnel-bound test |
| Single VM | [Namespace guide](https://free-ran-ue.github.io/doc-user-guide/03-namespace-free-ran-ue/), [script](https://github.com/free-ran-ue/free-ran-ue/blob/b09d394fd819da54e100080934e6764d411d4dca/script/namespace-script/free-ran-ue-namespace.sh) | Actual default-core + b09d394fd819da54e100080934e6764d411d4dca/UE networks, destructive setup pre-cleanup |
| Actual simulator schemas | [repo](https://github.com/free-ran-ue/free-ran-ue/tree/b09d394fd819da54e100080934e6764d411d4dca), [UE command](https://github.com/free-ran-ue/free-ran-ue/blob/b09d394fd819da54e100080934e6764d411d4dca/cmd/ue.go) | Makefile/go.mod, config/gnb.yaml and ue.yaml, root requirement, indexed tunnel name |
| Skill discovery / agents | [skills 13e4063a1cf913f5606d57d42ab83a86f5001e04](https://github.com/vercel-labs/skills/tree/13e4063a1cf913f5606d57d42ab83a86f5001e04) | local add --list, add --skill, global and agent flags; discovery does not prove agent invocation |

## Source pins

- free5gc/free5gc: `ab1280ed772ad1900a0c6c00ac4f7852eb9d491d` (HEAD snapshot, not a promised release).
- free-ran-ue/free-ran-ue: `b09d394fd819da54e100080934e6764d411d4dca` (HEAD snapshot, not a promised release).
- vercel-labs/skills: `13e4063a1cf913f5606d57d42ab83a86f5001e04` (HEAD snapshot, not a promised release).
- Core submodule NFs/upf → free5gc/go-upf: `616a4ff6cbd2e7de2bccd39399f37425f373bcc8`.
- Core submodule webconsole: `c40b94b6896109e90e46e59d57ebc5f7fa4c32a2`.

## Resolved documentation differences

- Integration calls gtpu.ifList.addr “N6”; core source marks it N3/N9. N6 is
  the DNN egress selector/routing, not that GTP-U bind address.
- Namespace guide shows `iifList`; actual config uses `ifList`. It refers to
  three networks, but the script creates only free-ran-ns and free-ue-ns; core,
  MongoDB and Webconsole stay in default network. `up` first tears resources down.
- Integration/namespace pages still prescribe broad manual iptables rules;
  selected quick-setup + go-upf configure UPF-managed per-DNN rules. Avoid duplicates.
- Subscriber page still uses go run server.go and legacy mongo/dropDatabase;
  selected quick guide builds/starts bin/webconsole. No database deletion adopted.
- MongoDB namespace instructions mention 7.0; selected quick setup uses 8.2
  packages and an 8.0 signing-key URL. This pairing is observed source behavior,
  not validated package-repository compatibility on every listed Ubuntu version.
- Web browsing could not render two simulator pages; their official HTML was
  fetched directly and read successfully. No inaccessible page is claimed reviewed.

Remaining runtime questions: selected Ubuntu/MongoDB combination, kernel/gtp5g
compatibility, VM routing/firewall and complete single-/two-VM E2E need authorized
lab validation. No mocks establish those outcomes.
