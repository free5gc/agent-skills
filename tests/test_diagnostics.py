"""Bounded, isolated checks; no real installer, service or network mutation."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/free5gc-deploy/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='free5gc tests ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'core with spaces'
        shutil.copytree(ROOT / 'tests/fixtures/core', self.repo)
        self.system = self.base / 'snapshot'
        (self.system / 'etc').mkdir(parents=True)
        (self.system / 'proc').mkdir()
        (self.system / 'etc/os-release').write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
        (self.system / 'proc/cpuinfo').write_text('flags : fpu sse avx avx2\n')
        (self.system / 'proc/modules').write_text('gtp5g 1 0 - Live 0\n')
        self.bin = self.base / 'mock-bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin), MOCK_SERVICE='active', MOCK_MODULE='present')
        # Delegate only timeout and python to known real executables; all system
        # inspection commands are mocked and reject unlisted operations.
        for name in ('timeout', 'python3', 'cat', 'dirname'):
            (self.bin / name).symlink_to(shutil.which(name))
        self.mock('hostname', 'echo mock-target')
        self.mock('uname', 'case "$1" in -r) echo fixture-kernel;; -m) echo x86_64;; *) exit 93;; esac')
        self.mock('readlink', 'echo "net:[fixture]"')
        self.mock('ip', 'case "$*" in "-br -4 addr"|"-4 route"|"-4 route get 8.8.8.8") echo mock-route;; *) exit 93;; esac')
        self.mock('systemctl', '[ "$*" = "is-active mongod" ] || exit 93; echo "$MOCK_SERVICE"; [ "$MOCK_SERVICE" = active ]')
        self.mock('modinfo', '[ "$*" = "-F filename gtp5g" ] || exit 93; case "$MOCK_MODULE" in present) echo /fixture/gtp5g.ko;; absent) echo "modinfo: ERROR: Module gtp5g not found." >&2; exit 1;; denied) echo denied >&2; exit 1;; esac')
        self.mock('git', 'echo fixture-git-observation')
        self.mock('go', '[ "$*" = version ] || exit 93; echo "go version go1.26.2 linux/amd64"')
        for name in ('free', 'df', 'make', 'gcc', 'node', 'yarn', 'mongosh', 'iptables'):
            self.mock(name, 'echo fixture-observation')
        for name in ('sudo', 'apt', 'apt-get', 'modprobe', 'sysctl'):
            self.mock(name, f'echo MUTATION_{name}; exit 93')
        self.artifacts()

    def mock(self, name, body):
        p = self.bin / name
        if p.is_symlink():
            p.unlink()
        p.write_text('#!/bin/bash\n' + body + '\n')
        p.chmod(0o755)

    def artifacts(self):
        checker = load('inspect-artifacts.py')
        for _, _, evidence in checker.inspect(self.repo):
            if evidence.startswith('missing '):
                p = self.repo / evidence.removeprefix('missing ')
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('inert fixture artifact\n')
                p.chmod(0o755)

    def run_cli(self, script, *args):
        result = subprocess.run(['/bin/bash', str(SCRIPTS / script), *args], env=self.env,
                                text=True, capture_output=True, timeout=15)
        self.assertNotIn('MUTATION_', result.stdout + result.stderr)
        return result

    def check(self):
        return self.run_cli('check-install.sh', '--repo', str(self.repo), '--system-root', str(self.system))

    def test_help_and_usage(self):
        for script in ('check-install.sh', 'collect-env.sh'):
            self.assertEqual(self.run_cli(script, '--help').returncode, 0)
            self.assertEqual(self.run_cli(script, '--repo').returncode, 64)
            self.assertEqual(self.run_cli(script, '--invalid').returncode, 64)
        self.assertEqual(self.run_cli('check-install.sh').returncode, 64)

    def test_spaces_and_scoped_success(self):
        r = self.check()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('PASS [config]', r.stdout)
        self.assertIn('PASS [gtp5g-installed]', r.stdout)
        self.assertIn('PASS [gtp5g-loaded]', r.stdout)
        self.assertIn('UNKNOWN [runtime]', r.stdout)
        self.assertNotIn('FAIL ', r.stdout)

    def test_missing_artifact_proven_failure(self):
        (self.repo / 'bin/amf').unlink()
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('FAIL [artifact] missing bin/amf', r.stdout)

    def test_missing_commands_and_timeout(self):
        for command in ('go', 'systemctl', 'modinfo'):
            (self.bin / command).unlink()
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNAVAILABLE [tool-go]', r.stdout)
        self.assertIn('UNAVAILABLE [mongod-service]', r.stdout)
        (self.bin / 'timeout').unlink()
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNAVAILABLE [check-config.py]', r.stdout)

    def test_inactive_service_is_unknown(self):
        for state in ('inactive', 'failed', 'activating', 'unrecognized'):
            with self.subTest(state=state):
                self.env['MOCK_SERVICE'] = state
                r = self.check()
                self.assertEqual(r.returncode, 2)
                self.assertNotIn('PASS [mongod-service]', r.stdout)

    def test_module_absent_unloaded_and_denied(self):
        (self.system / 'proc/modules').write_text('')
        self.env['MOCK_MODULE'] = 'absent'
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL [gtp5g-installed]', r.stdout)
        self.assertIn('UNKNOWN [gtp5g-loaded]', r.stdout)
        self.env['MOCK_MODULE'] = 'denied'
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNKNOWN [gtp5g-installed]', r.stdout)

    def test_permission_denied_command_and_file(self):
        self.mock('cat', 'echo private-secret >&2; exit 1')
        r = self.check()
        self.assertIn('UNKNOWN [gtp5g-loaded]', r.stdout)
        self.assertNotIn('private-secret', r.stdout + r.stderr)
        checker = load('inspect-artifacts.py')
        with patch.object(Path, 'read_text', side_effect=PermissionError('secret')):
            rows = checker.inspect(self.repo)
        self.assertEqual(rows[0][0], 'UNKNOWN')
        self.assertNotIn('secret', str(rows))

    def test_unknown_configuration_and_secret_redaction(self):
        (self.repo / 'config/amfcfg.yaml').write_text('secret: NEVER_PRINT_THIS\n')
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNKNOWN [config]', r.stdout)
        self.assertNotIn('NEVER_PRINT_THIS', r.stdout + r.stderr)
        (self.repo / 'config/amfcfg.yaml').write_text('invalid: [NEVER_PRINT_THIS\n')
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL [config]', r.stdout)
        self.assertNotIn('NEVER_PRINT_THIS', r.stdout + r.stderr)

    def test_yaml_dependency_unavailable(self):
        r = subprocess.run([shutil.which('python3'), '-S', str(SCRIPTS / 'check-config.py'), str(self.repo)],
                           text=True, capture_output=True, timeout=5)
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNAVAILABLE [config]', r.stdout)

    def test_config_mismatch_and_duplicate(self):
        p = self.repo / 'config/upfcfg.yaml'
        p.write_text(p.read_text().replace('addr: 127.0.0.8', 'addr: 127.0.0.9'))
        self.assertEqual(self.check().returncode, 1)
        shutil.copy(ROOT / 'tests/fixtures/core/config/upfcfg.yaml', p)
        p.write_text(p.read_text() + '\nversion: duplicate\n')
        self.assertEqual(self.check().returncode, 1)

    def test_unknown_makefile_never_executes(self):
        marker = self.base / 'must not exist'
        p = self.repo / 'Makefile'
        p.write_text(p.read_text().replace('GO_NF = ', f'GO_NF = $(shell touch "{marker}") '))
        r = self.check()
        self.assertIn('UNKNOWN [artifacts]', r.stdout)
        self.assertFalse(marker.exists())

    def test_artifact_list_follows_makefile_and_redefinition_unknown(self):
        p = self.repo / 'Makefile'
        p.write_text(p.read_text().replace('GO_NF = amf ', 'GO_NF = newnf amf '))
        r = self.check()
        self.assertIn('FAIL [artifact] missing bin/newnf', r.stdout)
        p.write_text(p.read_text() + '\nGO_NF += other\n')
        self.assertIn('UNKNOWN [artifacts]', self.check().stdout)

    def test_collect_non_ubuntu_avx_and_unreadable(self):
        (self.system / 'etc/os-release').write_text('ID=darwin\nVERSION_ID=26\n')
        r = self.run_cli('collect-env.sh', '--repo', str(self.repo), '--system-root', str(self.system))
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNKNOWN [os]', r.stdout)
        self.assertIn('PASS [avx]', r.stdout)
        (self.system / 'proc/cpuinfo').write_text('flags : fpu sse\n')
        r = self.run_cli('collect-env.sh', '--system-root', str(self.system))
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL [avx]', r.stdout)
        (self.system / 'proc/cpuinfo').unlink()
        r = self.run_cli('collect-env.sh', '--system-root', str(self.system))
        self.assertIn('UNKNOWN [avx]', r.stdout)

    def test_read_only_files_unchanged(self):
        before = {str(p): p.read_bytes() for root in (self.repo, self.system)
                  for p in root.rglob('*') if p.is_file()}
        self.check()
        self.run_cli('collect-env.sh', '--repo', str(self.repo), '--system-root', str(self.system))
        after = {str(p): p.read_bytes() for root in (self.repo, self.system)
                 for p in root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_config_permission_error_is_unknown(self):
        checker = load('check-config.py')
        with patch.object(Path, 'open', side_effect=PermissionError('NEVER_PRINT')), \
                patch('sys.argv', ['check-config.py', str(self.repo)]):
            from io import StringIO
            with patch('sys.stdout', new_callable=StringIO) as out:
                code = checker.main()
        self.assertEqual(code, 2)
        self.assertIn('UNKNOWN [config]', out.getvalue())
        self.assertNotIn('NEVER_PRINT', out.getvalue())

    def test_non_executable_and_outside_symlink(self):
        binary = self.repo / 'bin/amf'
        binary.chmod(0o644)
        self.assertIn('FAIL [artifact] not executable bin/amf', self.check().stdout)
        binary.unlink()
        binary.symlink_to(self.base / 'outside')
        self.assertIn('UNKNOWN [artifact] output symlink outside repo', self.check().stdout)

    def test_os_metadata_is_not_sourced_and_arm_is_unknown(self):
        marker = self.base / 'must not execute'
        (self.system / 'etc/os-release').write_text(
            'ID=ubuntu\nVERSION_ID="24.04"\nMALICIOUS=$(touch "' + str(marker) + '")\n')
        (self.system / 'proc/cpuinfo').write_text('Features : fp asimd\n')
        r = self.run_cli('collect-env.sh', '--system-root', str(self.system))
        self.assertEqual(r.returncode, 2)
        self.assertIn('UNKNOWN [avx]', r.stdout)
        self.assertFalse(marker.exists())

    def test_cli_bound_is_enforced(self):
        # Exercise a real timeout once rather than merely testing timeout text.
        self.mock('go', '/bin/sleep 20')
        r = self.check()
        self.assertIn('UNAVAILABLE [go-version]', r.stdout)
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
