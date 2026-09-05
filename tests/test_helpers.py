"""Read-only helper regression tests; no installed free5GC or root required."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/free5gc-deploy/scripts"


def load_helper(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESULT = load_helper("check-test-result")
CONFIG = load_helper("check-config")
PASS_LOG = "=== RUN   TestRegistration\n--- PASS: TestRegistration (7.21s)\nPASS\nok\ttest\t7.23s\n"


class TestResultChecker(unittest.TestCase):
    def test_accepts_uncached_pass_with_color_and_cleanup_output(self):
        result = RESULT.check_result("\x1b[32m" + PASS_LOG + "\x1b[0mCleanup complete\n", 0)
        self.assertEqual(result["status"], "PASS")

    def test_rejects_false_success_variants(self):
        cases = {
            "masked failure": (PASS_LOG.replace("--- PASS:", "--- FAIL:"), 0),
            "cached": (PASS_LOG.replace("7.23s", "(cached)"), 0),
            "no test": ("testing: warning: no tests to run\nPASS\nok test 0.1s\n", 0),
            "skip": (PASS_LOG.replace("--- PASS:", "--- SKIP:"), 0),
            "other test": (PASS_LOG.replace("TestRegistration", "TestGUTIRegistration"), 0),
            "truncated": (PASS_LOG.split("\nPASS")[0], 0),
            "timeout after pass": (PASS_LOG, 124),
            "log capture failure": (PASS_LOG, 1),
            "package failure": (PASS_LOG + "FAIL test 8.00s\n", 0),
            "panic after pass": (PASS_LOG + "panic: worker crashed\n", 0),
            "combined attempts": (PASS_LOG + PASS_LOG, 0),
            "reordered": ("PASS\nok test 7.23s\n=== RUN   TestRegistration\n"
                          "--- PASS: TestRegistration (7.21s)\n", 0),
        }
        for label, (log, status) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(RESULT.check_result(log, status)["status"], "FAIL")

    def test_cli_reports_hash_and_propagates_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "test.log"
            log.write_text(PASS_LOG)
            for status, expected in ((0, 0), (124, 1)):
                run = subprocess.run([sys.executable, str(SCRIPTS / "check-test-result.py"),
                                      str(log), "--exit-code", str(status)],
                                     capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, expected)
                self.assertEqual(len(json.loads(run.stdout)["log_sha256"]), 64)


def configuration():
    snssai = {"sst": "1", "sd": "010203"}
    amf = {"configuration": {
        "ngapIpList": ["192.0.2.10"],
        "plmnSupportList": [{"plmnId": {"mcc": "208", "mnc": "093"},
                             "snssaiList": [snssai]}],
        "supportDnnList": ["internet"],
        "supportTaiList": [{"tac": "000001"}],
    }}
    smf = {"configuration": {
        "snssaiInfos": [{"sNssai": snssai, "dnnInfos": [{"dnn": "internet"}]}],
        "userplaneInformation": {
            "upNodes": {
                "gNB1": {"type": "AN"},
                "UPF": {"type": "UPF", "nodeID": "127.0.0.8", "addr": "127.0.0.8",
                        "interfaces": [{"interfaceType": "N3", "endpoints": ["192.0.2.10"],
                                        "networkInstances": ["internet"]}],
                        "sNssaiUpfInfos": [{"sNssai": snssai, "dnnUpfInfoList": [
                            {"dnn": "internet", "pools": [{"cidr": "10.60.0.0/16"}],
                             "staticPools": [{"cidr": "10.60.100.0/24"}]}]}]},
            },
            "links": [{"A": "gNB1", "B": "UPF"}],
        },
    }}
    upf = {"pfcp": {"nodeID": "127.0.0.8", "addr": "127.0.0.8"},
           "gtpu": {"ifList": [{"type": "N3", "addr": "192.0.2.10"}]},
           "dnnList": [{"dnn": "internet", "cidr": "10.60.0.0/16"}]}
    return amf, smf, upf


class TestConfigChecker(unittest.TestCase):
    def test_accepts_consistent_config_without_mutation(self):
        docs = configuration()
        before = copy.deepcopy(docs)
        result = CONFIG.check_config(*docs)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["slice_dnns"][0]["sd"], "010203")
        self.assertEqual(result["plmns"][0]["mnc"], "093")
        self.assertEqual(docs, before)

    def test_rejects_mismatches_that_break_session_setup(self):
        for mutation in ("n3", "pfcp", "pool", "dnn", "slice", "topology", "wildcard", "loopback"):
            with self.subTest(mutation=mutation):
                amf, smf, upf = configuration()
                node = smf["configuration"]["userplaneInformation"]["upNodes"]["UPF"]
                if mutation == "n3":
                    upf["gtpu"]["ifList"][0]["addr"] = "192.0.2.11"
                elif mutation == "pfcp":
                    node["nodeID"] = "127.0.0.9"
                elif mutation == "pool":
                    upf["dnnList"][0]["cidr"] = "10.61.0.0/16"
                elif mutation == "dnn":
                    node["interfaces"][0]["networkInstances"] = ["other"]
                elif mutation == "slice":
                    amf["configuration"]["plmnSupportList"][0]["snssaiList"] = [{"sst": "2"}]
                elif mutation == "topology":
                    smf["configuration"]["userplaneInformation"]["links"] = []
                elif mutation == "wildcard":
                    node["interfaces"][0]["endpoints"] = ["0.0.0.0"]
                else:
                    amf["configuration"]["ngapIpList"] = ["127.0.0.18"]
                with self.assertRaises(ValueError):
                    CONFIG.check_config(amf, smf, upf)

    def test_accepts_wildcard_listener_with_routable_advertisement(self):
        amf, smf, upf = configuration()
        upf["gtpu"]["ifList"][0]["addr"] = "0.0.0.0"
        self.assertEqual(CONFIG.check_config(amf, smf, upf)["status"], "PASS")

    def test_cli_preserves_yaml_identifiers_and_fails_unknown_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, document in zip(("amfcfg.yaml", "smfcfg.yaml", "upfcfg.yaml"), configuration()):
                (Path(directory) / name).write_text(yaml.safe_dump(document))
            command = [sys.executable, str(SCRIPTS / "check-config.py"), directory]
            run = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)["tracking_areas"][0]["tac"], "000001")
            (Path(directory) / "upfcfg.yaml").write_text("different_schema: true\n")
            run = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
