---
name: free5gc-deploy
description: Install native single-host free5GC on Ubuntu, resolve installation problems, verify the built-in TestRegistration test, remove its test subscriber, and start the core network and Webconsole. Use when asked to install or deploy free5GC on a fresh host, or resume a failed installation. RAN/UE simulator installation and interoperability testing are separate follow-up tasks.
---

# free5GC Deploy

Deliver a running single-host free5GC installation with a successful upstream
`TestRegistration` run and an accessible Webconsole. Configure the core network
for the user's subsequent RAN/UE simulator and DNN connectivity test. The user
creates their own subscriber and installs the simulator after handoff; do not
install a simulator or add an end-to-end test to phase-one acceptance.

Use the user's language. Explain briefly that free5GC provides the core network,
Webconsole manages subscribers, and the built-in test supplies test-side
signaling. Standard shell, filesystem, and HTTPS access are sufficient. No
agent-specific MCP server, browser automation, or other skill is required.

## Execution contract

- Target Ubuntu 22.04, 24.04, 25.04, and 25.10 on a fresh x86_64 VM or physical
  host with sudo and Internet access. These are evaluation targets, not a claim
  of completed cross-version testing. Detect the actual OS and kernel; follow
  the non-LTS compatibility guidance in the installation reference.
- An installation request authorizes ordinary dependency, build, configuration,
  test, and startup steps within the agent's permissions. Continue through
  recoverable failures; ask only for missing access, consequential choices, or
  actions outside that scope. Do not ask for approval at every stage.
- Complete one-time privilege preparation before installing components:
  follow [privileges.md](references/privileges.md). Execute required sudo steps
  through the agent's approved tools. Reuse adequate existing access, or prepare
  an explicitly authorized, time-limited sudo lease with automatic cleanup.
  Do not finish after building only the control plane or hand the remaining
  installation to the user as `privilege.sh`.
  If access is blocked, report the exact permission failure and resume after
  it is resolved; a generated script is not a completed deployment.
- Read the selected checkout's scripts before execution. Use `quick-setup.sh`
  as a dependency reference; execute and verify its stages separately so an apt
  error cannot be hidden by a later success message.
- Resolve and record versions once per deployment. Keep the superproject's
  recorded submodule commits. Resume the same checkout after a failure.
- Keep source/build files owned by the deployment user. Escalate commands that
  require privileges. Do not disable package signature checks, clear the
  database, or flush the host firewall to make installation pass.
- On a nonempty host, identify existing NFs, subscribers, network resources, and
  working-tree changes. Upstream tests use fixed names and may terminate
  processes by name; do not run over an unrelated deployment.

## Workflow

1. **Check access, inspect, install, build.** Resolve
   [privileges.md](references/privileges.md) first, then follow
   [single-host.md](references/single-host.md).
   Record host, checkout, versions, relevant network settings, and successful
   stages in a private deployment directory outside the skill.
2. **Test before starting the final core.** Read
   [verification.md](references/verification.md), establish ownership of test
   subscriber data, then run `./test.sh TestRegistration` with a fresh log and
   a deadline. Validate the actual Go test result with
   [check-test-result.py](scripts/check-test-result.py); shell exit zero alone
   is insufficient. Do not change assertions or skip the test to obtain PASS.
3. **Clean up.** Whether the test passes or fails, check test processes, network
   resources, and subscriber records. Remove only resources created by this
   attempt. Verify the test subscriber is absent, including Webconsole
   authentication data. Cleanup failure leaves the deployment incomplete.
4. **Configure, start, and hand off.** After PASS and cleanup, follow
   [network-and-handoff.md](references/network-and-handoff.md). Check DNN/pool
   consistency, N2/N3 addresses, N6 routing/forwarding/NAT, then start the final
   core with `./run.sh` and Webconsole with `go run server.go` in their respective
   working directories. Keep both running without tmux. Verify readiness and
   open the login page, or provide a reachable URL and remote access instructions
   on a headless host. Revoke any lease created for this deployment and recheck
   readiness before handoff. On failure, clean up owned resources and revoke
   the lease before returning; the expiry timer covers an unexpected interruption.

When a stage fails, read the relevant entry in
[troubleshooting.md](references/troubleshooting.md), inspect evidence, repair the
cause, and rerun that stage. Record what changed. Stop repeating the same repair
when it makes no progress; explain the blocker and resumption point. Never
convert an unresolved failure into a success claim.

## Completion

Report success only after TestRegistration passes, subscriber cleanup is
verified, the configured final core and Webconsole are running, and any temporary
sudo lease created by this deployment has been removed. Provide:

- free5GC version/commit and install directory;
- `TestRegistration: PASS`, the fresh test log, and cleanup result;
- Webconsole URL and login instructions verified for the installed version;
- actual PLMN, TAC, S-NSSAI, DNN, UE pool, AMF N2 and UPF N3 addresses/ports,
  and N6 interface/route for the user's simulator setup;
- process stop/restart commands, logs, and any reboot/persistence limitations;
- temporary privilege cleanup result, or confirmation that existing access was reused;
- next steps: **create a subscriber**, then **install/configure a RAN/UE
  simulator and test DNN connectivity**, with the official documentation links.

Example, only after these checks have actually passed:

> free5GC has been deployed successfully. The built-in TestRegistration test
> passed, and the test subscriber has been removed.
> The core network and Webconsole are running: <reachable URL>.
> Create a subscriber in Webconsole, then install and configure a RAN/UE
> simulator using the core network parameters below to test connectivity and
> ping a destination in the selected DNN.

The acceptance scope is the built-in integration test plus deployment readiness.
Do not claim that external RAN/UE interoperability, DNN ping, or end-to-end
traffic through the final configuration has already been tested.
