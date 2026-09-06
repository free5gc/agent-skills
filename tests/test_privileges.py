"""Exercise sudo lease lifecycle in a temporary filesystem, never on the host."""

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = (Path(__file__).resolve().parents[1] /
          "skills/free5gc-deploy/scripts/prepare-privileges.py")
spec = importlib.util.spec_from_file_location("privileges", SCRIPT)
PRIV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PRIV)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("etc/sudoers.d", "etc/systemd/system"):
            (self.root / directory).mkdir(parents=True)
        self.plan = PRIV.make_plan("deploy", 1234, 120,
                                   datetime(2030, 1, 1, tzinfo=timezone.utc))
        self.calls = []
        self.existing = self.root / "etc/sudoers.d/existing"
        self.existing.write_text("preexisting host policy\n")

    def path(self, key):
        return self.root / self.plan[key].lstrip("/")

    def runner(self, command):
        self.calls.append(command)

    def install(self, runner=None):
        PRIV.install(self.plan, root=self.root, runner=runner or self.runner,
                     directory_check=lambda path: None)

    def assert_rolled_back(self):
        self.assertEqual(list((self.root / "etc/sudoers.d").iterdir()), [self.existing])
        self.assertEqual(list((self.root / "etc/systemd/system").iterdir()), [])
        self.assertEqual(self.existing.read_text(), "preexisting host policy\n")

    def test_arms_cleanup_before_grant_and_installs_restricted_files(self):
        def runner(command):
            self.runner(command)
            if command[1:2] in (["enable"], ["is-active"]):
                self.assertFalse(self.path("rule").exists())
                self.assertTrue(self.path("service").exists())
        self.install(runner)
        self.assertEqual(self.path("rule").read_text(), self.plan["policy"])
        self.assertEqual(stat.S_IMODE(self.path("rule").stat().st_mode), 0o440)
        self.assertEqual(stat.S_IMODE(self.path("service").stat().st_mode), 0o644)
        self.assertFalse(list(self.path("rule").parent.glob("*.pending")))
        self.assertIn("NOTAFTER=20300101020000Z", self.plan["policy"])
        self.assertIn("OnCalendar=2030-01-01 02:00:00 UTC", self.plan["timer_text"])
        self.assertIn("Persistent=true", self.plan["timer_text"])

    def test_rolls_back_each_system_command_failure(self):
        self.install()
        total = len(self.calls)
        for key in ("rule", "service", "timer"):
            self.path(key).unlink()
        for fail_at in range(total):
            with self.subTest(fail_at=fail_at):
                self.calls = []

                def runner(command):
                    self.runner(command)
                    if len(self.calls) == fail_at + 1:
                        raise subprocess.CalledProcessError(1, command)

                with self.assertRaises(subprocess.CalledProcessError):
                    self.install(runner)
                self.assert_rolled_back()

    def test_ctrl_c_after_grant_removes_access_before_disarming_timer(self):
        def runner(command):
            self.runner(command)
            if command == ["/usr/sbin/visudo", "-c"] and self.path("rule").exists():
                raise KeyboardInterrupt()
            if command[1:2] == ["disable"]:
                self.assertFalse(self.path("rule").exists())
                self.assertTrue(self.path("timer").exists())
        with self.assertRaises(KeyboardInterrupt):
            self.install(runner)
        self.assert_rolled_back()

    def test_cleanup_service_removes_only_lease_before_disabling_timer(self):
        self.install()
        destinations = {self.plan[key]: str(self.path(key))
                        for key in ("rule", "service", "timer")}
        for line in self.plan["service_text"].splitlines():
            if not line.startswith(("ExecStart=", "ExecStartPost=")):
                continue
            command = shlex.split(line.split("=", 1)[1])
            if command[:2] == ["/usr/bin/rm", "-f"]:
                # Execute deletion only after mapping every destination to the fixture.
                self.assertTrue(all(arg in destinations for arg in command[2:]))
                subprocess.run(command[:2] + [destinations[arg] for arg in command[2:]],
                               check=True)
            else:
                self.assertIn(command[0], ("/usr/bin/systemctl", "/usr/sbin/runuser"))
                if command[0] == "/usr/sbin/runuser":
                    self.assertEqual(command[1:], ["-u", "deploy", "--", "/usr/bin/sudo", "-K"])
                self.assertFalse(self.path("rule").exists())
                self.runner(command)
        self.assert_rolled_back()

    def test_does_not_replace_existing_or_symlinked_lease_artifacts(self):
        for key in ("rule", "service", "timer"):
            with self.subTest(key=key):
                self.path(key).symlink_to(self.existing)
                with self.assertRaises(ValueError):
                    self.install()
                self.assertTrue(self.path(key).is_symlink())
                self.path(key).unlink()
                self.assert_rolled_back()
        self.assertEqual(self.calls, [])

    def test_inspects_active_existing_lease_without_mutation(self):
        self.install()
        before = {key: self.path(key).read_bytes() for key in ("rule", "service", "timer")}
        states = []

        result = PRIV.inspect_existing(
            "deploy", 1234, root=self.root,
            now=datetime(2030, 1, 1, 1, 30, tzinfo=timezone.utc),
            owner_uid=os.getuid(), state_reader=lambda unit: states.append(unit) or "active",
        )

        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["remaining_seconds"], 30 * 60)
        self.assertTrue(result["artifacts_verified"])
        self.assertEqual(states, [self.plan["unit"]])
        self.assertEqual(before,
                         {key: self.path(key).read_bytes()
                          for key in ("rule", "service", "timer")})
        self.assertEqual(self.existing.read_text(), "preexisting host policy\n")

    def test_inspection_reports_expiry_and_inactive_timer(self):
        self.install()
        common = {"root": self.root, "owner_uid": os.getuid()}
        result = PRIV.inspect_existing(
            "deploy", 1234, now=datetime(2030, 1, 1, 2, 1, tzinfo=timezone.utc),
            state_reader=lambda unit: "inactive", **common,
        )
        self.assertEqual(result["status"], "EXPIRED")
        self.assertEqual(result["remaining_seconds"], 0)

        result = PRIV.inspect_existing(
            "deploy", 1234, now=datetime(2030, 1, 1, 1, tzinfo=timezone.utc),
            state_reader=lambda unit: "inactive", **common,
        )
        self.assertEqual(result["status"], "TIMER_INACTIVE")

    def test_inspection_rejects_tampered_or_untrusted_artifacts(self):
        self.install()
        self.path("service").write_text(self.plan["service_text"] + "# changed\n")
        with self.assertRaisesRegex(ValueError, "do not match"):
            PRIV.inspect_existing("deploy", 1234, root=self.root,
                                  owner_uid=os.getuid(), state_reader=lambda unit: "active")
        self.path("service").write_text(self.plan["service_text"])
        self.path("service").chmod(0o666)
        with self.assertRaisesRegex(ValueError, "Unexpected mode"):
            PRIV.inspect_existing("deploy", 1234, root=self.root,
                                  owner_uid=os.getuid(), state_reader=lambda unit: "active")

    def test_expired_preparation_never_grants_access(self):
        self.plan = PRIV.make_plan("deploy", 1234, 15,
                                   datetime(2000, 1, 1, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, "expired"):
            self.install()
        self.assert_rolled_back()

    def test_rejects_root_policy_injection_and_unbounded_duration(self):
        for user, uid, duration in (("root", 0, 120), ("ALL", 1000, 120),
                                    ("deploy\nALL", 1000, 120), ("a,b", 1000, 120),
                                    ("deploy", 1000, 0), ("deploy", 1000, 241)):
            with self.subTest(user=user, duration=duration):
                with self.assertRaises(ValueError):
                    PRIV.make_plan(user, uid, duration)

    def test_directory_guard_rejects_writable_or_symlinked_directory(self):
        unsafe = self.root / "unsafe"
        unsafe.mkdir(mode=0o777)
        unsafe.chmod(0o777)
        with self.assertRaises(ValueError):
            PRIV.trusted_directory(unsafe)
        link = self.root / "link"
        link.symlink_to(unsafe, target_is_directory=True)
        with self.assertRaises(ValueError):
            PRIV.trusted_directory(link)

    @unittest.skipUnless(shutil.which("visudo"), "visudo not installed")
    def test_real_visudo_accepts_generated_policy_without_installing_it(self):
        candidate = self.root / "candidate"
        candidate.write_text(self.plan["policy"])
        result = subprocess.run([shutil.which("visudo"), "-cf", str(candidate)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze not installed")
    def test_real_systemd_parser_accepts_cleanup_units(self):
        for key in ("service", "timer"):
            self.path(key).write_text(self.plan[key + "_text"])
        result = subprocess.run([shutil.which("systemd-analyze"), "verify",
                                 str(self.path("service")), str(self.path("timer"))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_dry_run_needs_no_root_and_mutation_requires_acknowledgment(self):
        import pwd
        user = pwd.getpwuid(os.getuid()).pw_name
        if os.getuid() == 0:
            self.skipTest("CLI test expects an ordinary deployment user")
        command = [sys.executable, "-I", str(SCRIPT), "--user", user]
        result = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["user"], user)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires root", result.stderr)
        result = subprocess.run(command + ["--inspect"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Inspection requires root", result.stderr)


if __name__ == "__main__":
    unittest.main()
