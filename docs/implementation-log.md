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
