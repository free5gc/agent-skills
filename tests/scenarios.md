# Skill scenario acceptance materials

Static walkthrough reviewed 2026-10-10. These are reproducible prompts/rubrics
for a later real agent conversation, **not** results of Claude Code, Copilot or
Codex independently running the deployment skill. Fixtures prove CLI behavior;
they cannot prove agent decisions or free5GC data-plane connectivity.

For each future run: load the installed SKILL.md and only applicable references,
provide the prompt/context below, record the response, tool actions, state and
PASS/FAIL/UNKNOWN against the criterion. Do not permit actual installation or
network mutation outside an explicitly authorized disposable lab.

| Prompt/context | Required decision/evidence | Static routing reviewed |
| --- | --- | --- |
| “Install free5GC.” No topology given | Ask single VM namespace vs two VMs before interface choice | SKILL PREFLIGHT → preflight steps 1–2 |
| Agent on macOS; target Ubuntu VM, no remote tool | Provide VM checks and concrete transfer path; no local Linux installer | preflight step 1; installation remote handoff |
| Ubuntu ARM or x86 VM without AVX | Explain unsupported/unresolved quick setup and CPU exposure first; no installer handoff yet | preflight architecture/AVX gate |
| Supported target, known topology/NIC, fresh checkout | Explain effects; full source in target Bash/repo; request return with outcome; WAITING_FOR_INSTALL | installation handoff |
| User: “It finished.” No evidence | VERIFY_INSTALL, diagnostics; no success declaration | SKILL step 3; verification levels |
| gtp5g build error after dependencies succeeded | Get first error/kernel/header/module evidence; repair only failed stage, no full reinstall | troubleshooting gtp5g row |
| User does not know what a subscriber is | Explain it, guide CREATE field by field with test-only values and UE mapping | E2E subscriber lesson |
| Single VM; user opened five terminals in default network | Explain lack of isolation; user-run namespace setup, correct core/RAN/UE placement | E2E single VM table |
| Two VMs; core has one LAN and a different Internet NIC | Confirm N2/N3 reachability and N6 egress separately; no first-NIC selection | installation interface selection; E2E two VMs |
| User pastes successful ordinary core-host ping | Preparation evidence only; require actual UE tunnel ping in correct namespace | E2E DN test; verification E2E |
| Permission denied reading logs / missing diagnostic tools | UNKNOWN, narrow user-run privileged diagnostic/transfer; no NOPASSWD | CLI contract; troubleshooting final paragraph |
| Install and core startup evidenced, UE never tested | Report those levels and UNKNOWN E2E, PARTIAL for full connectivity request | verification scope/completion |

Additional regressions: inactive mongod is not “uninstalled”; installed/unloaded
versus missing/denied module are distinct; unknown YAML never passes; current NAT
avoids legacy duplicates; ns-up pre-cleanup and ns-down require checking live
resources; credentials never enter handoff summaries.
