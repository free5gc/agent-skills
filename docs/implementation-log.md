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
