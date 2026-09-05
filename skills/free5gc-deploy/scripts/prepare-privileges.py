#!/usr/bin/env python3
"""Create a bounded sudo lease on a dedicated Ubuntu deployment host.

Run --dry-run unprivileged to review the exact policy and cleanup units first.
This does not install free5GC or alter agent sandbox/approval settings.
"""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys


def make_plan(user, uid, minutes, now=None):
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*[$]?", user) or uid <= 0:
        raise ValueError("Use a non-root deployment account with a simple Unix username")
    if not 15 <= minutes <= 240:
        raise ValueError("Lease duration must be between 15 and 240 minutes")
    now = now or datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=minutes)
    unit = f"free5gc-deploy-privileges-{uid}"
    rule = f"/etc/sudoers.d/zz-{unit}"
    service = f"/etc/systemd/system/{unit}.service"
    timer = f"/etc/systemd/system/{unit}.timer"
    return {
        "user": user,
        "expires_utc": expiry.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "rule": rule,
        "service": service,
        "timer": timer,
        "unit": unit,
        "policy": (
            "# Temporary free5GC deployment lease; removed by its cleanup timer.\n"
            f"Defaults:{user} verifypw=never, timestamp_timeout=0\n"
            f"{user} ALL=(root) NOTAFTER={expiry:%Y%m%d%H%M%SZ} NOPASSWD: ALL\n"
        ),
        "service_text": (
            "[Unit]\nDescription=Remove temporary free5GC sudo lease\n"
            "[Service]\nType=oneshot\n"
            f"ExecStart=/usr/bin/rm -f {rule}\n"
            f"ExecStartPost=/usr/sbin/runuser -u {user} -- /usr/bin/sudo -K\n"
            f"ExecStartPost=/usr/bin/systemctl disable {unit}.timer\n"
            f"ExecStartPost=/usr/bin/systemctl --no-block stop {unit}.timer\n"
            f"ExecStartPost=/usr/bin/rm -f {timer} {service}\n"
            "ExecStartPost=/usr/bin/systemctl daemon-reload\n"
        ),
        "timer_text": (
            "[Unit]\nDescription=Expire temporary free5GC sudo lease\n"
            "[Timer]\n"
            f"OnCalendar={expiry:%Y-%m-%d %H:%M:%S} UTC\n"
            "Persistent=true\nAccuracySec=1s\nRandomizedDelaySec=0\n"
            f"Unit={unit}.service\n"
            "[Install]\nWantedBy=timers.target\n"
        ),
        "revoke_command": f"sudo -n /usr/bin/systemctl start {unit}.service",
    }


def run(command):
    subprocess.run(command, check=True, timeout=60)


def trusted_directory(path):
    for entry in (path, *path.parents):
        info = entry.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError(f"Expected root-owned directory without group/other writes: {entry}")


def create_file(path, content, mode):
    # Exclusive creation rejects both existing files and symlinks.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(content)
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
    except BaseException:
        path.unlink()
        raise


def install(plan, root=Path("/"), runner=run, directory_check=trusted_directory):
    """root/runner injection is for isolated tests; CLI always uses the real host."""
    paths = {key: root / plan[key].lstrip("/") for key in ("rule", "service", "timer")}
    pending = paths["rule"].with_name(paths["rule"].name + ".pending")
    for parent in {path.parent for path in paths.values()}:
        directory_check(parent)
    for path in (*paths.values(), pending):
        if os.path.lexists(path):
            raise ValueError(f"Existing lease/artifact: {path}; inspect and revoke it before retrying")
    runner(["/usr/sbin/visudo", "-c"])
    runner(["/usr/bin/systemctl", "show", "--property=Version", "--value"])
    owned = []
    timer_attempted = False
    try:
        create_file(pending, plan["policy"], 0o440)
        owned.append(pending)
        runner(["/usr/sbin/visudo", "-cf", str(pending)])
        for key in ("service", "timer"):
            create_file(paths[key], plan[key + "_text"], 0o644)
            owned.append(paths[key])
        runner(["/usr/bin/systemctl", "daemon-reload"])
        timer_attempted = True
        runner(["/usr/bin/systemctl", "enable", "--now", plan["unit"] + ".timer"])
        runner(["/usr/bin/systemctl", "is-active", "--quiet", plan["unit"] + ".timer"])
        if datetime.now(timezone.utc) >= datetime.strptime(
            plan["expires_utc"], "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=timezone.utc):
            raise ValueError("Lease expired during preparation")
        # The grant becomes visible only after cleanup is armed. link is exclusive.
        os.link(pending, paths["rule"])
        owned.append(paths["rule"])
        runner(["/usr/sbin/visudo", "-c"])
    except BaseException:
        # Remove access before stopping cleanup, including on Ctrl-C.
        if paths["rule"] in owned:
            paths["rule"].unlink(missing_ok=True)
        if timer_attempted:
            try:
                runner(["/usr/bin/systemctl", "disable", "--now", plan["unit"] + ".timer"])
            except Exception as error:
                print(f"Cleanup timer removal needs inspection: {error}", file=sys.stderr)
        for path in reversed(owned):
            path.unlink(missing_ok=True)
        runner(["/usr/bin/systemctl", "daemon-reload"])
        raise
    finally:
        if pending in owned:
            pending.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", required=True)
    parser.add_argument("--minutes", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true", help="Print policy/units without host changes")
    parser.add_argument("--acknowledge-root-access", action="store_true",
                        help="Host owner approved temporary unrestricted root sudo for this account")
    args = parser.parse_args()
    try:
        plan = make_plan(args.user, pwd.getpwnam(args.user).pw_uid, args.minutes)
        if not args.dry_run:
            if os.geteuid() != 0 or not args.acknowledge_root_access:
                raise ValueError("Installation requires root and --acknowledge-root-access")
            install(plan)
        print(json.dumps(plan, indent=2))
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f"Privilege preparation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
