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

Open or restart the agent in the installation scope and ask:

> Please use free5gc-deploy to install free5GC.

The agent needs shell access to the target Ubuntu host, sudo permission, and
Internet access. A fresh host means no free5GC dependencies are preinstalled;
the agent and Node.js/npm used to install the skill are bootstrap prerequisites.

The agent prepares privileges once before installing components. It reuses
adequate existing passwordless sudo, or asks you to authorize a temporary sudo
lease for the deployment account on your dedicated VM. The lease grants
unrestricted root sudo for 120 minutes by default, supports separate agent
terminals, and is removed after completion or failure. An expiry rule and a
persistent cleanup timer cover an interrupted agent session.

If Ubuntu requires a password, enter it once in a supported terminal during
preparation. If the agent cannot accept terminal input, it supplies one concrete
bootstrap command for you to run; it then verifies access and automatically
continues installation, testing, cleanup, and startup. It should not stop after
the control plane and hand you a `privilege.sh` to finish deployment yourself.

Agent command approvals and Ubuntu sudo authentication are separate. Choose an
agent policy permitting host installation during preparation; a skill cannot
bypass remaining approval requirements. A lease that expires before completion
requires a new authorized window. For unattended evaluation, provision adequate
sudo access in the VM image. See the
[privilege workflow](skills/free5gc-deploy/references/privileges.md).

## Workflow

1. Prepare permissions once; inspect Ubuntu, kernel, network, and existing state.
2. Install dependencies, build free5GC/Webconsole, and troubleshoot failures.
3. Run the built-in `TestRegistration` and verify its actual result.
4. Remove the test subscriber and check for leftover test resources.
5. Configure the final core's N2/N3/N6 networking and DNN settings.
6. Start the core with `./run.sh` and Webconsole with `go run server.go` in their
   respective directories, open the page when a browser is available,
   revoke temporary sudo access, and provide login, simulator configuration,
   and next-step instructions.

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
| Privileges | Fresh-terminal sudo and sudo -v; early revoke; expiry/reboot cleanup; existing policy preserved |

Evaluate skill discovery and execution in both Codex and Claude Code. No
fresh-VM deployment or simulator ping has been certified by this repository yet.
The `owner/repo` installation requires these files to be published to GitHub.

References: [skills CLI](https://github.com/vercel-labs/skills),
[quick setup](https://free5gc.org/guide/quick-setup/),
[built-in tests](https://free5gc.org/guide/4-test-free5gc/).
