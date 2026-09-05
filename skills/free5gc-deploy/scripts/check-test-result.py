#!/usr/bin/env python3
"""Check one fresh upstream TestRegistration log; never starts free5GC."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def check_result(output, exit_code, package="test"):
    # Strip terminal colors, but retain line boundaries for Go's result records.
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    lines = [line.rstrip("\r") for line in output.splitlines()]
    runs = [i for i, line in enumerate(lines)
            if re.fullmatch(r"=== RUN\s+TestRegistration", line)]
    passes = [i for i, line in enumerate(lines)
              if re.fullmatch(r"--- PASS: TestRegistration \([0-9.]+s\)", line)]
    finals = [i for i, line in enumerate(lines) if line == "PASS"]
    summaries = [i for i, line in enumerate(lines)
                 if re.fullmatch(r"ok\s+" + re.escape(package) + r"\s+[0-9.]+s", line)]
    failures = [line for line in lines if re.match(
        r"(?:\s*--- (?:FAIL|SKIP):|FAIL(?:\s|$)|panic:|fatal error:|"
        r"go: .*\[build failed\]|testing: warning: no tests to run)", line)]
    reasons = []
    if exit_code != 0:
        reasons.append(f"Test wrapper or log capture exited with status {exit_code}")
    if len(runs) != 1 or len(passes) != 1 or len(finals) != 1 or len(summaries) != 1:
        reasons.append("Expected one fresh RUN, exact test PASS, final PASS, and uncached package result")
    elif not runs[0] < passes[0] < finals[0] < summaries[0]:
        reasons.append("Go test result records are out of order")
    if failures:
        reasons.append("Log contains a failed, skipped, panicking, or missing test result")
    return {
        "test": "TestRegistration",
        "package": package,
        "status": "PASS" if not reasons else "FAIL",
        "wrapper_exit_code": exit_code,
        "reasons": reasons,
        "scope": "Built-in integration test only; cleanup and final service readiness require separate checks",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--exit-code", type=int, required=True,
                        help="Actual captured test-wrapper/pipeline status")
    parser.add_argument("--package", default="test", help="Module tested by test.sh")
    args = parser.parse_args()
    try:
        raw = args.log.read_bytes()
    except OSError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1
    result = check_result(raw.decode("utf-8", errors="replace"), args.exit_code, args.package)
    result["log"] = str(args.log.resolve())
    result["log_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
