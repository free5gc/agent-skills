# Validation and delivery

Date: 2026-10-10 (Asia/Taipei). Scope: local skill implementation, not deployment.

## Changed implementation

- Replaced automatic privileged deployment with the official full-source installer
  handoff, user-run E2E lesson and seven workflow states in SKILL.md.
- Added all six requested references: sources, preflight, installation,
  troubleshooting, verification and end-to-end-test. Detailed source pins and
  documentation differences are recorded in sources.md.
- Added collect-env.sh and check-install.sh, a shared Bash library and inert
  artifact/YAML helpers. Retained/adapted the useful prior static config logic.
- Removed temporary privilege provisioning, prepared-host/root instructions,
  obsolete helpers/tests and unnecessary agent-specific metadata.
- Added inert fixtures, command mocks, packaging checks and twelve scenario
  prompts/rubrics. Updated the English README and retained Apache-2.0 LICENSE.
- Preserved and committed the user's supplied specification unchanged.

## Executed checks

| Check | Result / evidence |
| --- | --- |
| Unit/fixture/packaging suite | 21 tests passed; about 10 seconds, including a real five-second timeout |
| Bash syntax | Each .sh individually checked with bash -n; passed |
| Frontmatter / skill name / resource links | Unit tests plus skill-creator quick_validate.py passed |
| YAML checker against official current core defaults | PASS for scoped single-UPF static consistency; no runtime conclusion |
| Safe local collect-env | Exit 2; observations collected, support UNKNOWN by design |
| Safe local check-install against this skill repo | Exit 1; required core YAML absent, Makefile scope UNKNOWN, runtime UNKNOWN; correctly does not treat agent-skills as installed core |
| CLI discovery | npx skills add . --list, skills 1.5.18: one skill, free5gc-deploy |
| Isolated CLI installation | Temporary project, local absolute source, --skill free5gc-deploy --agent codex claude-code github-copilot --copy --yes; exit 0 |
| Installed resource integrity | Both .agents/skills and .claude/skills copies byte-identical to source resources; both Bash --help commands resolved common.sh from installed paths |
| Fixture safety | Allowed inspection commands mocked; mutating commands rejected; before/after repo/snapshot bytes unchanged; malicious Makefile and OS metadata never evaluated |
| Whitespace errors | git diff --check passed |
| Scenario review | All twelve specification cases statically routed to explicit skill/reference guidance; not independent live agent conversation results |

Commands ran as an ordinary user. Development-host tools, MongoDB and gtp5g were
already present and were only observed. This task did not install them, change
network/firewall/sysctl state, create namespaces, start NFs/simulator, create
subscribers, push or publish. Source files were downloaded to temporary storage
and read; no upstream quick-setup or Makefile was executed. The npm download was
only the skills CLI for the requested packaging validation.

## Not verified and known limits

- ShellCheck was not installed in the execution environment and was not run.
- Real free5GC installation, core startup, registration, PDU session and tunnel
  ICMP in both single-/two-VM labs were not performed; mocks cannot replace them.
- Claude Code, Copilot and Codex live conversation behavior or automatic triggering
  was not tested. CLI installation only verifies discovery/resource delivery.
- Remote GitHub installation/global command remains unverified until the new
  repository version is published by an authorized maintainer.
- Architecture/OS/CPU/kernel compatibility for every advertised upstream
  combination remains unverified. Main was source-reviewed at a pinned snapshot;
  it is not a promise for future main or installed releases. Manual kernel/module
  guidance differs from quick setup, documented in sources.md.
- Makefile helper deliberately supports the recognized Go-only output layout;
  legacy C-UPF/dynamic/changed layouts are UNKNOWN and require manual inspection.
- Static config checker supports common single-UPF core schemas only. Runtime
  address ownership, NSSF, subscriber, SBI/DB reachability, NAT rules and route
  correctness require additional stage evidence. Missing PyYAML is UNAVAILABLE.
- Permission tests use denied command mocks/Python file-access failures; real
  remote sudo, restricted journal, hypervisor and network policy were not tested.
- Official simulator instructions have stale/contradictory fields and NAT rules;
  the lesson follows actual pinned sources and records the differences.

## Maintainer release steps (not executed)

1. Review the Conventional Commits and retained license/specification. Run the
   suite and ShellCheck on a machine where it is available:
   `shellcheck -x skills/free5gc-deploy/scripts/*.sh`.
2. Use tests/scenarios.md for real conversations in each intended agent. Record
   actual behavior and fix any observed unsafe/unhelpful handoff.
3. In authorized disposable Ubuntu labs, validate the selected upstream versions
   for single VM and two VMs, including actual subscriber, namespace, registration,
   session and tunnel-bound ICMP evidence. Preserve independent success levels.
4. Only an authorized maintainer pushes/merges the reviewed branch to the intended
   GitHub repo. No separate npm package or agent-skills installer is necessary.
5. In clean project and global scopes, verify remote `npx skills add
   free5gc/agent-skills --skill free5gc-deploy` and the `-g` variant, resource
   integrity and each agent's invocation. Do not advertise unverified outcomes.
