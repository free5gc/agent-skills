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

## Workflow

1. Inspect Ubuntu, kernel, network, and existing installation state.
2. Install dependencies, build free5GC/Webconsole, and troubleshoot failures.
3. Run the built-in `TestRegistration` and verify its actual result.
4. Remove the test subscriber and check for leftover test resources.
5. Configure the final core's N2/N3/N6 networking and DNN settings.
6. Start the core and Webconsole, open the page when a browser is available,
   and provide login, simulator configuration, and next-step instructions.

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

The helper tests run without installing packages, loading modules, or starting
free5GC. They require Python 3 and PyYAML (`python3-yaml` with the system Python).
Local CLI discovery, skill structure validation, and the seven helper tests
have passed. Fresh-VM testing is left to the maintainer; do not run deployment tests
on an already configured development host.

For each target OS, use a fresh VM snapshot and record:

| Check | Evidence |
| --- | --- |
| Installation | OS/kernel, free5GC/submodule commits, dependency versions |
| Built-in test | Fresh TestRegistration PASS, no cached/skipped result |
| Cleanup | Test subscriber absent, test processes/network resources removed |
| Handoff | Core readiness, Webconsole login page, configuration summary |
| Maintainer's simulator test | Registration/session result and actual DNN ping |
| Recovery | Resume after apt/test failure; no duplicate rules or processes |

Evaluate skill discovery and execution in both Codex and Claude Code. No
fresh-VM deployment or simulator ping has been certified by this repository yet.
The `owner/repo` installation requires these files to be published to GitHub.

References: [skills CLI](https://github.com/vercel-labs/skills),
[quick setup](https://free5gc.org/guide/quick-setup/),
[built-in tests](https://free5gc.org/guide/4-test-free5gc/).
