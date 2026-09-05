# Diagnose and resume

Read the failing command's output and its postcondition. Fix the demonstrated
cause, record the change, then retry the affected stage with a fresh log. Do not
replace an upstream integration test with a weaker test to obtain success.

| Symptom | Investigation and bounded repair |
| --- | --- |
| Stops after the control plane and hands off `privilege.sh` | Inspect the actual sudo/sandbox failure and follow `privileges.md`. Resolve access first, then have the agent execute the remaining authorized stages and verify completion. The script's existence is not a successful deployment. |
| sudo requests a password / no terminal available | Complete the one-time preparation in `privileges.md`; if password input is unavailable, the owner runs only the initial lease helper in their terminal, then the agent verifies fresh-terminal access and continues. Do not capture the password or assume another terminal's credential is shared. |
| Lease expires / cleanup timer fails | Stop new privileged stages; inspect the recorded expiry and unit. Clean up owned resources and revoke through normal administrator access. Do not silently renew the lease or treat `NOTAFTER` as removal of its per-user Defaults. |
| sudo blocked by sandbox / no new privileges | Use the agent's normal approval/escalation mechanism for host execution. Changing a sudo password or generating another shell script does not resolve the sandbox boundary. |
| apt/dpkg lock | Identify the owner (`ps`, `fuser`, systemd apt timers). Allow an active update to finish with bounded checks. Do not delete lock files or kill a healthy package operation. |
| Interrupted dpkg / unmet dependencies | Check `dpkg --audit`, disk space, and package errors. After locks clear, use `dpkg --configure -a` or an inspected `apt-get --fix-broken install` plan. Review removals before applying. |
| Ubuntu archive 404 | Verify actual suite and current archive status; follow `single-host.md` for EOL archive URIs, preserving suite and signatures. |
| Third-party repo 404 / NO_PUBKEY / Signed-By conflict | Inspect the specific source, suite/version and key fingerprint against official vendor instructions. Back up and repair only that entry/key. Do not use `trusted=yes` or allow unauthenticated packages. |
| MongoDB repo unavailable on 25.xx | Follow the documented non-LTS compatibility evaluation; never invent a plucky/questing MongoDB URL or rewrite Ubuntu's suite to noble. |
| DNS / TLS / download failure | Inspect resolver, route, clock, proxy and CA certificates. Retry transient errors within a deadline. Keep TLS verification enabled. |
| MongoDB fails to start | Check journal, CPU instructions, permissions, configuration, ports and disk space. Verify both server availability and a query; shell installation is not server health. |
| Go or Corepack missing in a later shell | Reestablish the selected tool PATH; inspect upstream hard-coded tool paths and sudo environment. Do not depend on a prior `.bashrc` source. |
| gtp5g build/load failure | Compare running kernel, headers, compiler errors, upstream compatibility, module version, Secure Boot and kernel logs. Installing a module for a different kernel does not fix the current one. Record an upstream compatibility revision if needed. |
| Webconsole build killed | Inspect memory/OOM evidence; reduce build parallelism. Do not silently replace lockfiles or run dependency upgrades. |
| Test stalls or fails | Inspect exact assertion and NF logs, SCTP, MongoDB, module state, test network resources, source/submodule alignment and authentication data. Stop at the deadline, clean owned resources and diagnose before retry. |
| Shell returned 0 but no Go PASS | Treat as failure/unknown. Upstream cleanup may mask the test exit code. Use fresh output and `check-test-result.py`. |
| Test subscriber remains | Compare provisioning/deletion helpers, including Webconsole authentication data. Use pre-test absence evidence and exact identity filters; never drop the database. |
| Test passed but final Core fails | The test uses different configuration. Inspect final YAML consistency, ports, certificates, NF registration and PFCP association. Do not reuse test namespace addresses. |
| Webconsole unreachable | Check page/assets locally, bind address, port, persistent process, intended firewall and SSH forwarding. Distinguish remote localhost from the browser host. |

If no new evidence or repair is available, report the failing stage, concise
error, completed work, log path and precise action needed to resume. Additional
permissions or a reboot need their normal user/agent approval; the skill does
not grant powers the executing agent lacks.
