# free5GC Agent Skills

Skills for agents with Linux shell access, including Codex and Claude Code.

## Install

With Node.js/npm and an agent already available:

```bash
npx skills add free5gc/agent-skills --skill free5gc-deploy
```

Choose your agent in the installer. For a global installation:

```bash
npx skills add free5gc/agent-skills --skill free5gc-deploy -g -a codex
npx skills add free5gc/agent-skills --skill free5gc-deploy -g -a claude-code
```

## Prepared-host one-prompt path

Before opening the deployment task, the host owner prepares a dedicated Ubuntu
machine with:

- the agent and this skill installed for the non-root deployment account;
- Internet access and adequate disk/memory for a native source build;
- noninteractive sudo covering package, kernel-module, network, test, systemd,
  and startup operations; and
- the agent's supported execution/approval policy configured to permit those
  host operations, long-running processes, network access, and required writes.

For a disposable VM, the documented [cloud-init prepared-host
example](skills/free5gc-deploy/references/prepared-host.md) installs a persistent
`NOPASSWD: ALL` sudoers rule for the deployment account. This is ongoing,
unrestricted root capability, not a narrow free5GC allowlist. The owner controls
its lifecycle; the deployment agent reuses it and does not remove it. The same
document includes fresh-login probes, agent execution requirements, and owner
cleanup. Do not run the whole agent as root or disable its approval system.

After preparation, open or restart the agent in the installation scope and ask
only:

> Please use free5gc-deploy to install free5GC.

On a correctly prepared host, the agent reuses existing access without creating
a lease or asking for extra chat approval, then performs dependency installation,
the complete Core/Webconsole build, TestRegistration and subscriber cleanup,
network setup, final startup, and readiness checks.

## Interactive bootstrap fallback

If noninteractive access is absent, the exact one-prompt outcome is not
possible: a skill cannot know a sudo password or grant itself root. Before any
password-requiring command, the agent uses noninteractive probes and determines
whether the product has a documented secure direct password-entry channel. A
PTY by itself does not qualify.

When a temporary lease is appropriate, the agent first reads the helper and
generates its dry-run plan. It explains the account, unrestricted root scope,
15–240 minute duration, cleanup, and authentication route, then obtains explicit
owner authorization for that exact mutation. If direct secret input is not
supported, the owner runs one reviewed bootstrap command in their own terminal.
The agent then inspects the existing lease, timer, expiry, and remaining time and
resumes the same deployment automatically. It never asks for a password in chat
or hands the actual installation back as `privilege.sh`.

Agent command approval remains independent from sudo. A lease cannot repair a
sandbox or eliminate tool approvals. See the complete
[privilege workflow](skills/free5gc-deploy/references/privileges.md).

## Workflow

1. Prepare permissions once; inspect Ubuntu, kernel, network, and existing state.
2. Install dependencies, build free5GC/Webconsole, and troubleshoot failures.
3. Run the built-in `TestRegistration` and verify its actual result.
4. Remove the test subscriber and check for leftover test resources.
5. Configure the final core's N2/N3/N6 networking and DNN settings.
6. Start the core with `./run.sh` and Webconsole with `go run server.go` in their
   respective directories, open the page when a browser is available,
   revoke any lease created for this deployment, and provide login, simulator
   configuration, and next-step instructions.

The agent keeps both processes running without tmux. Webconsole's frontend is
built during installation; `go run server.go` starts its backend.

You then create a subscriber and install/configure a RAN/UE simulator to test
connectivity and ping through the intended DNN. The skill does not install a
simulator or claim that this later test has already passed. On a headless host,
it supplies a reachable URL or SSH forwarding instructions.

Evaluation targets: **Ubuntu 22.04, 24.04, 25.04, 25.10**, native single-host
x86_64. Non-LTS releases require checking package availability and kernel/module
compatibility. These are planned targets, not certified configurations.

## Development and validation

The portable entry point is [SKILL.md](skills/free5gc-deploy/SKILL.md).
Optional `agents/openai.yaml` supplies Codex UI metadata. No custom npm package
or MCP server is required.

```bash
npx skills add . --list
python3 -m unittest discover -s tests -v
```

Before a Codex behavioral evaluation, update the installed copy from the current
checkout and verify that it matches the source (Python bytecode caches may appear
only in the source tree after tests):

```bash
npx skills add . --skill free5gc-deploy -g -a codex
diff -qr skills/free5gc-deploy ~/.agents/skills/free5gc-deploy
```

The helper tests run without installing packages, changing sudoers/systemd,
loading modules, or starting free5GC. They require Python 3 and PyYAML
(`python3-yaml` with the system Python).
Privilege helper tests use temporary directories and simulated system commands;
they do not certify live sudo authentication or timer execution. Skill structure
validation and helper regression tests are available locally. Fresh-VM testing
is left to the maintainer; do not run deployment tests on an already configured
development host.

For each target OS, use a fresh VM snapshot and record:

| Check | Evidence |
| --- | --- |
| Installation | OS/kernel, free5GC/submodule commits, dependency versions |
| Built-in test | Fresh TestRegistration PASS, no cached/skipped result |
| Cleanup | Test subscriber absent, test processes/network resources removed |
| Handoff | Core readiness, Webconsole login page, configuration summary |
| Maintainer's simulator test | Registration/session result and actual DNN ping |
| Recovery | Resume after apt/test failure; no duplicate rules or processes |
| Privileges | All three fresh/detached-context probes; actual command coverage; early revoke; expiry/reboot cleanup; existing policy preserved |

Evaluate skill discovery and execution in both Codex and Claude Code. No
fresh-VM deployment or simulator ping has been certified by this repository yet.
The `owner/repo` installation requires these files to be published to GitHub.

References: [skills CLI](https://github.com/vercel-labs/skills),
[quick setup](https://free5gc.org/guide/quick-setup/),
[built-in tests](https://free5gc.org/guide/4-test-free5gc/).
