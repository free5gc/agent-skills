---
name: free5gc-deploy
description: Guide users through official free5GC quick setup on Ubuntu, verify installation, troubleshoot failures, and guide free-ran-ue connectivity tests with either single-VM namespace isolation or two VMs. Use when users ask to install, deploy, validate, or troubleshoot this setup.
---

# free5GC deployment guide

Reply in the user's language. Teach concrete commands using their actual host,
paths, interface names and addresses. Read references only for the current stage.

## Boundaries

The user runs the complete official installer in their own target-host Bash
terminal. Do not run it for them, split it into a replacement installer, change
its `source` semantics, create NOPASSWD rules/root helpers, or request passwords.
Only the bundled diagnostic scripts are designed for direct, read-only execution.
Do not automatically create subscribers, change privileged networks/namespaces,
start long-running core/simulator processes, or perform the whole E2E test.
Existing authorization for other applicable tool operations still applies.
Do not assume sudo, SSH, browser access, connectors, or Linux on the agent host.
Preserve existing deployments, local modifications and subscribers.

## Workflow and state

Keep a compact record of target host, topology, core/simulator commit, local
changes, N2/N3 addresses, N6 egress, stage, pending user action, evidence and open
issues. Never retain passwords or real subscriber authentication secrets. Offer
this sanitized record for cross-session handoff without a background service.

1. **PREFLIGHT** — Read [preflight](references/preflight.md). Identify the target
   versus agent host. Ask about single-VM namespace / two-VM topology before
   choosing interfaces unless already known. Collect environment on the target
   using [collect-env.sh](scripts/collect-env.sh); missing access is UNKNOWN.
   Read [sources](references/sources.md) and verify selected-version official
   prerequisites before proceeding. Stop the install path on unsupported or
   unresolved architecture/AVX requirements.
2. **WAITING_FOR_INSTALL** — Read [installation](references/installation.md).
   Prepare the full `source quick-setup.sh -i ACTUAL_INTERFACE` command in the
   correct repo on the target, explain system changes, and explicitly ask the
   user to return with completion or nearby errors. After handoff, wait; another
   terminal's completion is not observable automatically.
3. **VERIFY_INSTALL** — On the user's return (including only “done”), read
   [verification](references/verification.md) and run/provide
   [check-install.sh](scripts/check-install.sh). Check evidence; a setup banner
   or exit code is insufficient. Explain how to transfer the self-contained
   skill to a remote VM when its files are absent there.
4. **GUIDE_E2E** — Read [end-to-end-test](references/end-to-end-test.md). Guide
   subscriber creation, simulator build/config and the chosen topology, one
   checkpoint at a time. Label each terminal, host, namespace, directory,
   command, expected evidence, keep-open requirement and privilege.
5. **WAITING_FOR_TEST_RESULT** — Request sanitized registration/session logs,
   actual UE tunnel information and explicitly tunnel-bound ping statistics.
6. **TROUBLESHOOT** — Read [troubleshooting](references/troubleshooting.md).
   Enter immediately on installer errors or an existing deployment problem;
   do not require verification first. Follow evidence → hypothesis → check →
   minimal repair → recheck the failed stage. Do not reinstall by default.
7. **COMPLETE / PARTIAL** — Report installation, core startup and E2E separately
   as verified / failed / unknown, with evidence and remaining work. COMPLETE
   requires the requested scope's evidence; never imply unrun E2E passed.

No framework/state daemon is required. Keep interaction minimal: reuse known
values, continue authorized read-only checks, and wait only for dependent user
operations/results. Commands with example values must be rewritten to the actual
confirmed environment before handoff.
