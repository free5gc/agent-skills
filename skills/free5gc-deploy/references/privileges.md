# Privilege preflight and bootstrap

Finish this preflight before any package, kernel, network, test, or startup
operation. Ubuntu sudo authentication and the agent's host-execution approval
are independent gates. A skill cannot supply a password, escape a sandbox, or
authorize its own sudoers change.

## Select the path before anything can prompt

Identify the non-root deployment account, the selected agent execution context,
and whether final processes will use a detached launch context. Use only
noninteractive probes at this point:

```bash
sudo -n true
sudo -n -E true
sudo -n -v
sudo -n -l
```

Run the first three probes again in a fresh tool terminal and through the actual
detached launch mechanism before using it. `test.sh` and `run.sh` may use both
`sudo -E` and `sudo -v`. Never omit `-n` during discovery: allocating a PTY does
not mean the user has a secure, accessible password-entry channel.

Read the selected release's `quick-setup.sh`, `test.sh`, and `run.sh`, enumerate
their privileged commands, and compare them with `sudo -n -l`. For a
command-specific policy, check the real command plus arguments with `sudo -n -l
-- <command> <arguments>` where supported. The three probes only establish
authentication behavior; even three successes do not prove that package,
module, network, test, and startup commands are authorized.

Choose exactly one path:

- **Prepared host / adequate preexisting access:** all probes work in every
  required context and policy covers the actual commands. Reuse it. Do not
  create a lease, ask for redundant permission, change the policy, or revoke it
  at handoff. Keep source, builds, logs, and Webconsole owned by the deployment
  account and elevate only operations that need root. See
  [prepared-host.md](prepared-host.md) for owner provisioning.
- **Existing helper lease:** lease artifacts exist from an earlier bootstrap.
  Do not rerun the create command. Follow **Resume an existing lease** below.
- **Missing access, secure direct input supported:** use the interactive
  bootstrap fallback below. Generate the plan first, obtain explicit consent,
  and authenticate only through the product's documented user-facing secret
  input attached to that exact process.
- **Missing access, no secure direct input:** use noninteractive sudo for agent
  attempts so no inaccessible prompt is opened. Present the reviewed owner
  bootstrap command, pause at the access boundary, and resume automatically
  after the owner runs it. This is not a successful one-prompt deployment.
- **Agent execution policy blocks host actions:** request the product's normal
  host-execution approval. Do not try to repair that boundary with sudoers.

Treat secure input as supported only when the interface explicitly exposes a
user-controlled, secret entry channel to the same waiting process. A PTY,
interactive shell flag, or visible `[sudo] password` text is not evidence. Never
ask for a password in chat or put one in command arguments, environment
variables, files, clipboard instructions, or logs.

## Interactive bootstrap fallback

Use this only on a dedicated host when existing access is inadequate. Resolve
`F5GC_SKILL_DIR` to this installed skill's absolute directory and
`F5GC_DEPLOY_USER` to the actual account. Read the helper implementation, then
generate its complete non-mutating plan before requesting authorization:

```bash
python3 "$F5GC_SKILL_DIR/scripts/prepare-privileges.py" \
  --user "$F5GC_DEPLOY_USER" --minutes 120 --dry-run
```

Present the relevant plan output and explain all of the following together:

- the exact account;
- unrestricted root sudo across that account's processes and terminals;
- the selected 15–240 minute duration and UTC expiry;
- the sudoers path, cleanup service/timer, automatic expiry, and explicit revoke
  command;
- whether authentication will use a verified secure direct-input channel or the
  owner's terminal.

Obtain explicit owner authorization before creating anything. The installation
request by itself, a tool approval, the dry-run, or
`--acknowledge-root-access` is not consent to alter sudoers. Reuse consent already
given in the conversation for the same account, unrestricted scope, and
duration; do not ask twice. Consent does not provide a password or bypass agent
execution approval.

After authorization, run the command once. With verified secure direct input,
attach this exact process to that channel. Otherwise show this exact command
with concrete absolute path, account, and duration for the owner to run in their
own terminal:

```bash
sudo /usr/bin/python3 -I "$F5GC_SKILL_DIR/scripts/prepare-privileges.py" \
  --user "$F5GC_DEPLOY_USER" --minutes 120 --acknowledge-root-access
```

This is the only owner-terminal deployment action. The agent performs the
installation, build, test, cleanup, networking, and startup after access is
verified. Do not replace those stages with a generated script.

The helper grants `NOPASSWD: ALL` with `NOTAFTER`, plus per-user
`verifypw=never` and `timestamp_timeout=0`. It validates sudoers, creates files
exclusively, arms a persistent systemd cleanup timer before exposing the grant,
rolls back failure, clears cached credentials during cleanup, and preserves
unrelated sudo policy. The timer bounds privilege cleanup, not Core lifetime.

## Resume an existing lease

After bootstrap, after an interrupted turn, or whenever matching artifacts
already exist, inspect instead of recreating them:

```bash
sudo -n /usr/bin/python3 -I "$F5GC_SKILL_DIR/scripts/prepare-privileges.py" \
  --user "$F5GC_DEPLOY_USER" --inspect
```

The inspection verifies root ownership, modes, exact account/rule/unit content,
timer state, UTC expiry, and remaining seconds without changing the host. Record
its JSON. Continue only when `status` is `ACTIVE`, the remaining time covers the
next bounded stage plus cleanup, the three probes succeed in fresh and detached
contexts, and policy covers the actual privileged commands. Resume the same
checkout and completed stages; do not restart the deployment.

For `EXPIRED`, `TIMER_INACTIVE`, missing, or mismatched artifacts, preserve the
diagnostics and stop new privileged stages. Clean only this attempt's resources
while valid access remains. Do not overwrite artifacts, rerun the helper, remove
unknown rules, or silently extend the authorized duration. If the lease no
longer permits inspection or cleanup, provide its recorded paths and exact owner
administrator action required. A new window requires new explicit scope and
authorization.

## Verify, deploy, then revoke a created lease

Immediately after lease creation or resumption:

1. Record inspection JSON and `systemctl status <unit>.timer`.
2. Run all three noninteractive probes from a new tool terminal and the actual
   detached launch context. Check actual command coverage as described above.
3. If verification fails, preserve evidence and use the printed revoke command
   while access exists; do not loosen unrelated policy.
4. Continue the autonomous deployment. Before long stages, compare their
   deadlines with `remaining_seconds`, leaving time for owned cleanup and
   revocation.

After successful readiness checks, or before returning with a failure:

1. On failure, stop owned test/partial processes and clean owned resources while
   privilege remains. On success, keep the final Core/Webconsole running.
2. Run the inspection's exact revoke command, for example
   `sudo -n /usr/bin/systemctl start free5gc-deploy-privileges-1000.service`, and
   wait for completion.
3. Verify the recorded sudoers path and both unit files are absent and the timer
   is inactive. Run `sudo -K` as the deployment user. Do not require all sudo
   commands to fail because preexisting owner access must remain.
4. Recheck Core/Webconsole readiness and record stop/restart commands that work
   after normal sudo authentication is restored. Upstream signal handlers may
   invoke sudo, so unattended Ctrl-C may not be a complete shutdown procedure.

Do not revoke access classified as prepared/preexisting. Removing a created
lease does not terminate already-running privileged processes. If the agent
crashes, `NOTAFTER` bounds new commands and the persistent timer catches up after
boot, but neither stops already-running root commands. Report incomplete cleanup
instead of claiming success.

References: [sudoers policy and date constraints](https://www.sudo.ws/docs/man/sudoers.man/),
[systemd persistent timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
