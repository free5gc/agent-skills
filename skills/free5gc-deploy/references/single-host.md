# Inspect, install, and build

## Environment and source

Resolve the execution path in [privileges.md](privileges.md) before installing
anything. Inspect `/etc/os-release`, `uname -r`, architecture, CPU flags,
RAM/disk, default routes, addresses, existing listeners, and systemd.
Source/build files belong to the deployment user. Installing into `/usr/local`
needs elevated access; compiling Go code does not inherently require root.

Check CPU requirements of the selected MongoDB version (including AVX for
recent x86_64 versions), running-kernel headers, module loading/Secure Boot,
SCTP, and namespace support. A restricted container is not a fresh Ubuntu VM.
Do not silently replace the kernel or reboot the machine.

Use a user-specified release or existing suitable checkout. Otherwise resolve
the current stable free5GC release from its official releases page, clone it
into `~/free5gc` if unused, and record the exact commit. Initialize its recorded
submodules with `git submodule update --init --recursive`. Do not independently
pull submodule main branches. Preserve existing checkouts and user changes.

Read that release's `quick-setup.sh`, `Makefile`, `test.sh`, `test/go.mod`, NF
`go.mod` files, and Webconsole's frontend `package.json`/lockfile. Resolve Go,
gtp5g, MongoDB, Node.js, and Yarn/Corepack versions using those files and official
compatibility documentation. Main-branch scripts and documentation can disagree;
do not combine version numbers without checking the selected release. Keep
versions fixed during retries unless evidence requires a documented change.

Use `umask 077` and a fresh directory under `~/.local/state/free5gc-deploy/` for
logs, config backups, ownership records, and a short progress file. Record OS,
kernel, source/submodule commits, installed versions, paths, and successful
stages. Store no credentials in reports; sanitize credential-bearing Git URLs.
Never put target-host state in the installed skill directory.

## Ubuntu release handling

All four OS releases are evaluation targets; select packages from actual host
facts rather than a blanket unsupported-version exit.

| Host | Ubuntu suite | Dependency strategy |
| --- | --- | --- |
| 22.04 | jammy | Prefer official vendor packages for jammy |
| 24.04 | noble | Prefer official vendor packages for noble |
| 25.04 | plucky | Check archive availability and non-LTS vendor compatibility |
| 25.10 | questing | Check archive availability and non-LTS vendor compatibility |

At execution time, check whether the host release has moved to Ubuntu's EOL
archive. For archive-related 404 errors, back up the Ubuntu sources and change
only official Ubuntu archive/security URIs to `old-releases.ubuntu.com/ubuntu`,
preserving the original suite/components and signature verification. Handle
both `.list` and deb822 `.sources` files. Do not change plucky/questing into
noble or rewrite third-party repositories. Do not upgrade the OS implicitly.

MongoDB's Ubuntu packages target LTS releases; do not invent a plucky/questing
repository URL. For 25.04/25.10, first check current official vendor support.
If unavailable, evaluate the signed official noble package as a **compatibility
workaround**, scoped only to MongoDB's repository. Inspect package dependencies
and `apt-get --simulate install ...` before installing. Continue only if native
host packages satisfy dependencies without downgrading/replacing core system
libraries or removing unrelated packages. Verify the binary, service, and a
database query, and record the workaround. This is not a vendor-support claim.
If dependencies cannot be satisfied, report the exact blocker; do not force
broken packages or silently switch to a Docker deployment.

gtp5g compatibility depends on the running kernel, not just the Ubuntu number.
Start with the release-recommended gtp5g revision. If the build fails on a newer
kernel, check upstream for a compatible released revision/fix and record any
change. Do not treat an old kernel list in a manual as proof that a newer kernel
cannot work, or successful compilation as proof the module loaded.

## Dependencies and postconditions

Execute stages separately, checking exit status and actual postconditions.
Use `quick-setup.sh` as a reference; do not source the entire script as the sole
installation action. Execute required privileged stages through the verified
agent terminal/approval path; do not stop at the control plane and delegate the
rest to a user-run script.

1. **System/build tools.** Install packages actually required by the checkout,
   normally `git ca-certificates curl wget gnupg build-essential cmake autoconf
   libtool pkg-config libmnl-dev libyaml-dev iproute2 iptables python3
   python3-yaml psmisc`. Install headers matching `uname -r`. Add tools used by
   the selected scripts as needed. Docker and golangci-lint are not required.
2. **Go.** Obtain the required toolchain from official downloads and verify its
   published checksum. Inspect a preexisting installation before replacement.
   Set PATH explicitly in each build/test shell. Upstream `test.sh` can hard-code
   `/usr/local/go`; make that path resolve to the chosen toolchain. Sourcing
   `.bashrc` in one tool call does not configure subsequent calls.
3. **MongoDB.** Configure the signed official repository/key for the selected
   version and the strategy above; install server and shell. Start `mongod`,
   verify `systemctl is-active mongod`, and run a real query:
   `mongosh --quiet --eval 'if (db.adminCommand({ping: 1}).ok !== 1) quit(1)'`.
   Inspect logs on failure. A working `mongosh --version` is insufficient.
4. **gtp5g.** Clone the compatible tag/commit into an unused directory, build
   against running-kernel headers, install using upstream instructions, and
   verify `modinfo gtp5g`, `sudo modprobe gtp5g`, `lsmod`, and kernel logs. Check
   the loaded module's version, not only the file on disk. Ensure SCTP works.
5. **Webconsole tools.** Use the frontend's Node engines and package manager
   requirements. Install Node.js and Yarn/Corepack as needed, keeping the
   committed lockfile. Check `node --version` and the package manager in the
   same shell environment used by make. Do not assume Corepack is bundled with
   every Node version or overwrite the agent's Node installation unnecessarily.

Use [troubleshooting.md](troubleshooting.md) for errors. Build with `make all`
from the checkout using the selected Go on PATH. Check all binaries expected by
that release's `run.sh`, the Webconsole binary, and built frontend assets. Avoid
excessive parallelism if RAM is limited. A success counter is not a build check.

Next follow [verification.md](verification.md), before starting the final core.

## Sources

- [free5GC quick setup](https://free5gc.org/guide/quick-setup/)
- [Installation guide](https://free5gc.org/guide/3-install-free5gc/)
- [free5GC releases](https://github.com/free5gc/free5gc/releases)
- [gtp5g](https://github.com/free5gc/gtp5g)
- [Go downloads](https://go.dev/dl/)
- [MongoDB Ubuntu installation](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/)
- [MongoDB 8.0 platform requirements](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-ubuntu/)
- [Ubuntu release cycle](https://ubuntu.com/about/release-cycle)
- [Ubuntu EOL upgrades/archive guidance](https://help.ubuntu.com/community/EOLUpgrades)

Read only sources needed for the chosen versions or observed failure.
