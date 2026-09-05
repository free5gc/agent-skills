# One-time privilege preparation

Complete permission preparation before installing components. Ubuntu sudo and
agent sandbox/command approval are independent gates. Use the agent's supported
host-execution policy; a skill cannot grant sandbox access or supply a password.
Do not disable approval settings or run the whole agent as root.

## Establish the deployment path

1. Identify the non-root deployment account and inspect existing sudo policy.
   In the agent's approved host execution context, check `sudo -n true`,
   `sudo -n -E true`, and `sudo -n -v`. The selected upstream `test.sh` and
   `run.sh` use both environment-preserving sudo and credential validation.
   Probe again in a fresh tool terminal and in the actual detached launch
   context if used. A single successful `true` does not establish all privileges.
2. Reuse existing adequate noninteractive sudo access without changing it. A
   command-specific policy may still deny actual installation operations;
   inspect that policy and resolve missing access before starting.
3. Otherwise, on a dedicated deployment VM, explain the one-time preparation:
   the named account will have **unrestricted root sudo**, across its processes
   and terminals, for a default 120 minutes (select 15–240 minutes based on the
   host). This permits adaptive package/kernel/network repairs. It is not a
   sandbox or a command allowlist. Get the host owner's explicit authorization
   for this temporary policy if it is not already present in the conversation.
   Bundle this with the initial installation permission preparation; do not ask
   again at each stage. Ordinary installation permission alone does not imply
   permission to change sudoers.
4. Review and run the helper below. If sudo requires a password, the user enters
   it directly into a supported terminal prompt once. Never ask for it in chat
   or place it in a tool argument, environment, file, or log. If the agent has no
   user-accessible password prompt, give the owner the single concrete helper
   command to run in their terminal, then verify access from the agent and
   continue the deployment. This is only the initial privilege bootstrap; the
   agent executes all installation, test, cleanup, and startup work.

A sandbox denial (`no new privileges`, blocked setuid, denied system paths) must
use the agent's normal host-execution approval mechanism. A sudo lease cannot
resolve that denial. The owner must select permissions suitable for deployment;
if the agent still requires individual command approvals, explain that limitation
instead of promising zero further approval prompts.

## Prepare a bounded lease

Resolve `F5GC_SKILL_DIR` to the installed skill's absolute directory and
`F5GC_DEPLOY_USER` to the actual non-root account. Read the helper before running
it. It uses Python 3, sudo/visudo, util-linux's `runuser`, and a running systemd
system manager (standard Ubuntu host tools).
First produce a reviewable plan without privilege or host changes:

```bash
python3 "$F5GC_SKILL_DIR/scripts/prepare-privileges.py" \
  --user "$F5GC_DEPLOY_USER" --minutes 120 --dry-run
```

Once the owner has authorized that scope, execute once through the approved
terminal, substituting concrete absolute paths/account values if handing the
bootstrap command to the owner:

```bash
sudo /usr/bin/python3 -I "$F5GC_SKILL_DIR/scripts/prepare-privileges.py" \
  --user "$F5GC_DEPLOY_USER" --minutes 120 --acknowledge-root-access
```

Record its printed expiry, rule path, timer/service names, and revoke command
in the private deployment record. The helper validates sudoers, refuses existing
lease artifacts, creates root-owned files, and arms a persistent systemd timer
before exposing the grant. The rule includes `NOTAFTER`; the timer removes the
rule and its per-user Defaults, clears the user's sudo credential cache, disables
itself, and removes its unit files.
`verifypw=never` allows upstream `sudo -v` even when preexisting password-based
rules exist; `timestamp_timeout=0` avoids relying on cached authentication.
These Defaults apply to the account until the rule is removed, so verify cleanup
rather than treating the command grant's expiry as full policy restoration.
The timer is for privilege cleanup only, not for running Core or Webconsole.

Immediately verify all three probes above from the agent's new execution
contexts and inspect `systemctl status <printed-timer-name>`. Policy precedence,
`requiretty`, or an inactive sudoers include may prevent effective access despite
valid syntax. If a probe fails, revoke the lease before pausing for assistance;
do not silently loosen unrelated policy. No installation begins until these
checks pass. If the helper fails, inspect its error and verify rollback before
retrying. Existing lease files may indicate another deployment: do not overwrite
or remove them without establishing ownership.

## Continue automatically, then revoke

Execute installation, TestRegistration, subscriber/resource cleanup, networking,
and final Core/Webconsole startup yourself. Keep builds and Webconsole under
the deployment user. Before a long stage, check time remaining against its
bounded deadline; leave time for cleanup. Do not silently renew the lease.
If the budget is insufficient, finish owned cleanup and revoke before requesting
another explicitly bounded window. Resume successful stages rather than
reinstalling everything.

After successful readiness checks, or before returning with a failure/cancellation:

1. On failure, first stop owned test/partial startup processes and clean up owned
   test resources while privilege is available. Preserve diagnostic logs. On
   success, retain the final Core/Webconsole processes.
2. Execute the helper's exact printed revoke command, for example
   `sudo -n /usr/bin/systemctl start free5gc-deploy-privileges-1000.service`.
   Use the actual UID. This starts a root cleanup process which removes only
   that lease and its units. Wait for it to complete.
3. Verify the printed sudoers path and unit files are absent and the timer is
   inactive; use `sudo -K` as the deployment user to remove cached credentials.
   Do not require all sudo commands to fail: preexisting grants must remain.
4. Recheck Core/Webconsole readiness after revocation. Running privileged
   processes are not terminated by removing sudo permission. Later restart or
   privileged shutdown returns to the owner's normal sudo authentication.
   Record concrete stop commands for owned processes: upstream signal handlers
   may themselves invoke sudo, so an unattended Ctrl-C is not a complete
   shutdown plan after lease removal.

If the agent crashes, the timer performs cleanup at expiry; when powered off at
expiry, its persistent calendar timer catches up after boot. `NOTAFTER` also
bounds the command grant independently of the timer. Expiry does not terminate
already-running root commands. The owner can run the printed revoke command
without `-n` using their normal sudo password if the lease has expired. Report
any incomplete cleanup explicitly; do not claim successful handoff with an
unremoved lease. A reboot or failed timer may require checking the recorded
paths and normal administrator cleanup before resuming.

For unattended VM evaluation, the owner can provision adequate noninteractive
sudo in the VM image/cloud-init and choose an agent policy allowing installation.
Do not add or revoke a lease when existing access already suffices. When resuming
an old `privilege.sh` attempt, inspect its completed stages and execute the
remaining authorized commands yourself after this preflight.

References: [sudoers policy and date constraints](https://www.sudo.ws/docs/man/sudoers.man/),
[systemd calendar and persistent timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
