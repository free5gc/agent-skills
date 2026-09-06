# Prepare a host for one-prompt deployment

The one-prompt path starts only after the owner has prepared both independent
permission layers below. Do this while creating the dedicated VM, before asking
the agent to deploy free5GC. Installing the agent and this skill is also host
preparation, not part of the deployment prompt.

## 1. Noninteractive Ubuntu administration

The deployment account needs noninteractive sudo for package installation,
kernel modules, network configuration, systemd, integration tests, and final
startup. The exact upstream commands vary by free5GC release and may invoke
shells or other programs as root. A rule that allows only `apt` or `systemctl`
is not adequate.

For a disposable, dedicated VM, the following cloud-init example prepares the
standard `ubuntu` account. Replace both occurrences of `ubuntu` if the image
uses another existing non-root deployment account:

```yaml
#cloud-config
write_files:
  - path: /etc/sudoers.d/90-free5gc-agent
    owner: root:root
    permissions: '0440'
    content: |
      # Owner-provisioned access for a dedicated free5GC deployment VM.
      Defaults:ubuntu verifypw=never, timestamp_timeout=0
      ubuntu ALL=(root) NOPASSWD: ALL
runcmd:
  - [visudo, -cf, /etc/sudoers.d/90-free5gc-agent]
```

This is persistent, unrestricted root access for that account, not a restricted
free5GC command allowlist. `ALL` also permits `sudo -E`; `verifypw=never` makes
the upstream `sudo -v` check noninteractive, and `timestamp_timeout=0` avoids
depending on a cached credential. Use it only where the account and VM are
trusted. The deployment agent treats this as preexisting owner policy: it must
not replace it, create a temporary lease, or remove it at handoff.

After first boot, the owner should validate the image from a fresh login:

```bash
sudo -K
sudo -n true
sudo -n -E true
sudo -n -v
sudo -n -l
```

The agent repeats the three noninteractive probes in its own fresh execution
contexts and verifies the real operations it needs. A successful `sudo -n true`
alone does not prove that a different, command-specific policy covers the full
deployment.

The owner controls this rule's lifecycle. After the deployment, remove it from
an administrator terminal if persistent unattended restart is not wanted, then
validate the remaining policy and clear cached credentials:

```bash
sudo rm -f /etc/sudoers.d/90-free5gc-agent
sudo visudo -c
sudo -K
```

Removing sudo access does not stop already-running processes. It can make later
network cleanup, restart, or an upstream signal handler interactive, so retain
the handoff's exact stop/restart instructions first.

## 2. Agent host-execution permission

Configure the agent through its supported approval settings so it can execute
commands on this target host, write outside its source checkout where required,
use the network, start long-running processes, and request `sudo` operations.
For a no-extra-chat evaluation, approve that deployment scope during VM/agent
preparation. Keep the normal approval system enabled; do not run the entire
agent as root and do not treat sudo policy as permission to escape a sandbox.

Verify from the same execution mode the agent will use. A sandbox error such as
`no new privileges` or a denied loopback setup must be resolved through the
agent's host-execution approval mechanism, not by adding another sudoers rule.
No custom MCP server is required.

If either layer is absent, use the interactive bootstrap fallback in
[privileges.md](privileges.md). That fallback may need one explicit lease
authorization or one owner-terminal command, so it is not the one-prompt path.

References: [cloud-init `write_files`](https://cloudinit.readthedocs.io/en/latest/reference/modules.html#write-files),
[sudoers command tags and password policy](https://www.sudo.ws/docs/man/sudoers.man/).
