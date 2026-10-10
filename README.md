# free5GC Agent Skills

An English, portable skill for guiding official free5GC quick setup on Ubuntu,
checking the result and teaching free-ran-ue connectivity tests. Conversations use
your language. Supports one VM with namespace isolation or two VMs.

## Install the skill

With Node.js/npm and a supported agent available:

```bash
npx skills add free5gc/agent-skills --skill free5gc-deploy
```

For use across projects:

```bash
npx skills add free5gc/agent-skills --skill free5gc-deploy -g
```

These commands install the **skill**, not free5GC. The remote commands require
this repository/version to be published on GitHub. No separate npm package is
needed. For a local checkout, preview discovery without installing:

```bash
npx skills add . --list
```

The generic skill format is intended for Codex, Claude Code and GitHub Copilot.
Local CLI discovery and isolated installation were verified with skills 1.5.18;
real conversations/automatic triggering in each agent remain unverified. Consult
[your agent's supported CLI options](https://github.com/vercel-labs/skills) if
selecting one explicitly.

## Use

Ask your agent:

> Help me install free5GC on my Ubuntu VM. I want a single-VM namespace test.

Or:

> My existing free5GC deployment fails during UE registration. Help diagnose it.

The skill confirms the target host and topology, gathers read-only evidence,
checks official version-specific requirements and gives you the complete official
`source quick-setup.sh -i` command to run in your own Bash terminal. Return with
its result so the agent can verify the installation and guide the next stage.
You create the test subscriber and run core/gNB/UE/network commands yourself.
The skill does not grant itself sudo access or request passwords in chat.

Installation, core startup and tunnel-bound UE connectivity are separate results.
An installation banner or ordinary host ping does not prove end-to-end success.
This project has not performed a real free5GC deployment during implementation.
It does not claim official endorsement.

## Read-only checks

From this checkout (replace the example core path with your actual directory):

```bash
bash skills/free5gc-deploy/scripts/collect-env.sh --repo "/your/core directory"
bash skills/free5gc-deploy/scripts/check-install.sh --repo "/your/core directory"
```

Both accept `--help`, avoid sudo and mutations, and bound external checks.
Python 3.9+ supports artifact inspection; PyYAML enables static core config
checks. Missing dependencies are reported as unavailable, not installed by the
scripts. See the [output contract and limits](skills/free5gc-deploy/references/verification.md).
All installed resources are self-contained; no fixed skill installation path is
required. Remote VMs need the full skill folder transferred or this repo cloned.

## Development and validation

```bash
python3 -m unittest discover -s tests -v
```

The tests require Python3/PyYAML and Bash and use inert fixtures/mocks. See the
[validation report](docs/validation.md), [scenario materials](tests/scenarios.md),
[implementation record](docs/implementation-log.md) and
[official source/version review](skills/free5gc-deploy/references/sources.md).
The existing [Apache-2.0 license](LICENSE) is retained.
