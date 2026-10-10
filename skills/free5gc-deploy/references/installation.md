# Installation and user handoff

Sources: [official quick setup](https://free5gc.org/guide/quick-setup/) and
[versioned source index](sources.md). All installer commands below are for the
user's own Bash terminal on the confirmed Ubuntu target.

## Version, directory and interface

For a new installation, confirm a writable parent directory and an unused child
path, then teach `git clone https://github.com/free5gc/free5gc.git` followed by
`cd` into that actual path. Do not clone over an existing directory. For an
existing repo, inspect `git status --short`, `git rev-parse HEAD` and
`git submodule status --recursive`; do not reset/checkout or discard changes.
The agent records the SHA without asking a novice to transcribe it. Inspect that
checkout's quick-setup.sh, Makefile and submodule revisions; main is not a synonym
for the installed version. Redact credentials from diagnostics; omit remote URLs.

Use topology, IP and route evidence to choose the installation interface. The
reviewed script selects the first IPv4 on the explicitly named interface and
uses it for AMF `configuration.ngapIpList`, SMF UPF N3 `interfaces[].endpoints`
and UPF `gtpu.ifList[].addr`; it sets every DNN's `natifname` to that interface.
UPF GTP-U is N3/N9, not N6 egress. On multiple NICs, document the needed later
N2/N3 address changes and preserve/select the actual N6 DNN egress separately.
Do not use a namespace veth that has not been created as the install interface:
install through the current host egress first, then configure E2E isolation.

## Explain effects and hand off

Before handing over commands, explain the selected script's behavior: stop and
disable UFW, set IPv4 forwarding (runtime sysctl), install system packages,
MongoDB (and enable/start mongod), Go (possibly replace /usr/local/go), gtp5g
v0.9.16 kernel module, Node/Yarn toolchain, update shell environment, initialize
submodules, build NFs/Webconsole and modify network YAML. UPF later manages NAT
when started. Optional Docker/lint flags are opt-in only. New versions require
reinspection. sudo authentication occurs only in the user's terminal, never in
chat or a command argument. Do not create privilege leases or root helpers.

Show a command block with the actual quoted repo directory and actual interface:

```bash
cd "/actual/confirmed/free5gc directory"
source quick-setup.sh -i ACTUAL_CONFIRMED_INTERFACE
```

The path and uppercase token above are documentation placeholders; replace them
from the user's confirmed directory and route/interface evidence before handoff.
Preserve `source`, its shell environment and interactions. Do not use `bash`,
`sh`, `sudo bash`, a pipeline, or add shell modes such as `set -e` to the official
installer. Do not split/reimplement its stages or execute it through agent tools.

Include: “When it finishes, return here and say ‘installation finished’. If it
fails, paste the output around the error, without secrets. I will check the
actual installation next; return even if you see Setup completed.” Set
WAITING_FOR_INSTALL and wait for a reply. Do not claim to monitor another
terminal. A failed stage may leave partial changes; there is no transactional
rollback. Diagnose that stage before deciding whether/how to retry.

## Resume and remote diagnostic files

On return, enter VERIFY_INSTALL and follow [verification](verification.md).
When the target is directly readable, run the bundled checks there. Otherwise
provide a concrete transfer method: have the user copy the whole installed
`free5gc-deploy` folder (scripts and references together) using their file transfer
method to a confirmed target path, or clone this agent-skills repository into a
new unused directory on the VM. Do not assume the VM already has the skill or
assume SSH authorization. Then give, with both actual paths substituted:

```bash
bash "/actual/transferred/free5gc-deploy/scripts/check-install.sh" --repo "/actual/core directory"
```

Ask for classified output, not complete YAML or subscriber databases. Scripts
never start NFs. Installation evidence does not establish runtime or E2E success.
