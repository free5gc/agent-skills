# Implementation record

Each stage is recorded in a local Conventional Commit. No remote publication is authorized.

## 1. Repository and requirements

- Read the supplied implementation specification and inspected all existing resources/callers.
- No applicable AGENTS.md found in the workspace or its parents.
- Starting tree: only the supplied specification was untracked; no tracked user edits.
- Preserve the existing Apache-2.0 LICENSE unchanged and preserve the specification.
- Replace the privilege-lease/prepared-host deployment model with a user-run official installer and read-only diagnostics. Existing helper tests describe the superseded model and will be replaced.
- Official source review uses commit-pinned source snapshots downloaded to a temporary directory, never executed.
- Development host installation, network changes, long-running core/simulator startup, push and publication are excluded.

## 2. Official source review and workflow refactor

- Read official quick setup, guide index, subscriber, troubleshooting, N6 NAT,
  simulator integration/build/namespace pages and commit-pinned source files.
- Added sources with actual review date, source pins and resolved documentation
  differences (N3 versus N6, ifList typo, managed NAT and namespace placement).
- Replaced the skill and references with user-run installer handoff, independent
  verification levels, test subscriber lesson and terminal-by-terminal topology
  guidance. Removed superseded privilege helper, prepared-host instructions,
  agent-specific metadata and obsolete tests; read-only replacements follow.
- Every source download was read-only; no upstream installer/Makefile executed.
- Git identity was supplied by the user and set only in this repository.

## 3. Read-only diagnostics

- Added Bash CLIs with quoted paths, stable classifications, explicit exit codes,
  bounded commands and no sudo/network/service/installer mutations.
- Added shared CLI support, inert version-scoped Makefile artifact inspection and
  adapted the previous useful YAML checker for sanitized FAIL/UNKNOWN reporting.
- Missing parser dependency, unsupported schemas, denied observation, inactive
  service and unloaded module cannot become deployment success.
- Initial Bash syntax validation passed. Fixture/static/real read-only validation
  and the public README are the next stage.

## 4. Regression tests and diagnostic hardening

- Added commit-pinned inert core fixtures and isolated command mocks; all 20
  unittest checks passed (9.5 seconds). No fixture Makefile or installer executed.
- Covered missing/denied commands and files, unavailable YAML dependency, paths
  with spaces, missing/non-executable/symlink artifacts, dynamic/unknown Makefiles,
  supported and unknown/malformed/duplicate-key configs, absent/unloaded/denied
  modules, inactive services, AVX/non-Ubuntu/ARM-like snapshots and real timeout.
- Added before/after fixture integrity, frontmatter, all Bash syntax and relative
  resource link checks; skill-creator validator and git diff --check passed.
- Hardened known missing-module classification, YAML duplicate-key rejection,
  permission handling and Makefile redefinition detection based on test review.
- Corrected an obsolete configuration URL after checking the official guide
  index. Recorded manual-versus-quick kernel/module versions and RAM guidance.
- CLI 1.5.18 discovered free5gc-deploy locally. Temporary project installation
  targeting Codex, Claude Code and GitHub Copilot succeeded; installed resources
  were byte-identical and both Bash --help commands resolved bundled dependencies.
  No existing agent settings were modified; temporary installation was removed.
- Development-host safe read-only runs: collect-env exit 2 (support unconfirmed);
  check-install against this skill repo exit 1 (core YAML absent), correctly not
  declaring a deployment. Existing host dependencies/services were observed only.
- ShellCheck is not present; it has not been run. Agent conversation and real
  single-/two-VM E2E results remain unverified. See final validation report.
