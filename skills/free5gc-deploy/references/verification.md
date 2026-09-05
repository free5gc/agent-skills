# TestRegistration acceptance and cleanup

## Before the test

Read the selected release's `test.sh`, `test/registration_test.go`, test NF setup,
and database helpers. The official test starts its own NFs and UPF, uses test
configuration, and may call `killall`. Run it before starting the final core.
If there are unrelated NFs or conflicting test resources, do not run over them.

Record the namespace names, veth names, loopback addresses, ports, and process
ownership before the run. In the inspected checkout these include `UPFns`,
`veth0`/`veth1`, and test addresses in `10.200.200.0/24` and `10.60.0.0/16`.
Verify the selected script rather than hard-coding these as universal values.
Apply any test-required forwarding/module settings documented by that release,
recording prior values and separating temporary test changes from the final
network configuration. Confirm sudo credentials are usable before the bounded
noninteractive test; a hidden password prompt must not consume its deadline.

Derive the test SUPI, PLMN, database URI/name, and collection/filter list from
the test's provisioning helpers. The inspected TestRegistration uses
`imsi-208930000007487` and PLMN `20893`; these are test identities, not the
subscriber the user will create later. Before the test, query for that SUPI in
every collection the test writes and record **counts only** in the run directory.
Do not log authentication keys or subscriber documents.

The selected test identity must be absent before running. If it already exists,
do not overwrite/delete it. For a retry, use this deployment's recorded proof
of prior absence to clean its leftovers first. Without ownership evidence,
resolve the identity/environment conflict before running the fixed test.

## Run and verify the actual result

Use a fresh log for every attempt and disable Go test caching. Set an execution
deadline, e.g. 15 minutes initially; compile/download progress may justify a
documented longer retry. Read `test.sh`'s signal/cleanup behavior first. The
example below belongs in a Bash shell with the release's Go available and
`F5GC_ROOT`, `F5GC_RUN_DIR`, and `F5GC_SKILL_DIR` set to absolute paths:

```bash
cd "$F5GC_ROOT"
umask 077
export GOFLAGS="${GOFLAGS:+$GOFLAGS }-count=1"
f5gc_test_log=$(mktemp "$F5GC_RUN_DIR/TestRegistration.XXXXXX.log")
# Capture pipeline statuses even when the caller normally uses errexit.
set +e
timeout --signal=INT --kill-after=30s 15m bash ./test.sh TestRegistration \
  2>&1 | tee "$f5gc_test_log"
f5gc_pipe_status=("${PIPESTATUS[@]}")
f5gc_test_status=${f5gc_pipe_status[0]}
if [ "${f5gc_pipe_status[1]}" -ne 0 ]; then
  f5gc_test_status=${f5gc_pipe_status[1]}
fi
python3 "$F5GC_SKILL_DIR/scripts/check-test-result.py" "$f5gc_test_log" \
  --exit-code "$f5gc_test_status" \
  --package "$(awk '$1 == "module" {print $2; exit}' test/go.mod)"
f5gc_check_status=$?
# Record this result, then perform the cleanup below even on failure.
```

Retain the log, checker JSON, checker status, command, timestamp, commit, and
test wrapper status. Run these in a dedicated shell rather than changing the
user's interactive shell options. Do not treat this example's last assignment
or an outer shell exit status as the checker result.

`test.sh` in some releases runs cleanup after `go test` without preserving the
Go process's exit status. Therefore require a fresh `=== RUN TestRegistration`,
its exact `--- PASS` result, a final Go `PASS`, and an uncached successful package
summary. Reject skipped, missing, truncated, failed, or timed-out results.
The bundled checker verifies those markers and the wrapper status. Inspect
unresolved runtime/setup errors too; the checker does not certify resource
cleanup or service readiness. Do not use a historical PASS or change tests to
hide an error. If upstream changes its output format, inspect the real result
and adapt the checker with evidence rather than relaxing acceptance blindly.

The acceptance criterion is **TestRegistration PASS**. No external simulator,
packet capture, or ICMP reply is required for this phase. This does not assert
end-to-end traffic through the final configuration.

## Subscriber cleanup, on success or failure

First let the test finish its cleanup and stop remaining owned test processes
so they cannot recreate data. Test helpers may exit early or leave records even
after a passing run. In source inspected at free5GC commit
`25480fa49640f2457f319523c0a3e7b93175f653`, provisioning writes
`subscriptionData.authenticationData.webAuthenticationSubscription`, but
`DelUeFromMongoDB` does not remove it. Inspect the selected release for changes.

That checkout writes these collections using an exact `ueId` field:

```text
subscriptionData.authenticationData.authenticationSubscription
subscriptionData.authenticationData.webAuthenticationSubscription
subscriptionData.provisionedData.amData
subscriptionData.provisionedData.smfSelectionSubscriptionData
subscriptionData.provisionedData.smData
policyData.ues.amData
policyData.ues.smData
policyData.ues.chargingData
policyData.ues.flowRule
policyData.ues.qosFlow
```

Build the actual cleanup list from the selected source, including any additional
subscriber-scoped runtime records. Before the test, inventory existing matching
records across database collections as well, so newly discovered leftovers can
be attributed safely. Use count queries with exact identity filters; never dump
the database or authentication documents.

For each recorded collection, only when pre-test absence/ownership is proven:

1. Query the exact test identity again.
2. Delete leftover records using an exact SUPI filter (and PLMN where required
   by that collection). For the listed schema, the essential filter is
   `{ueId: testSupi}`; never use `{}` or a SUPI prefix/regex.
3. Query again and require zero remaining records. Check Webconsole's subscriber
   listing when available. Retain counts and cleanup status without secrets.

Use a generated JavaScript file with `mongosh --file` for multi-line operations;
pass data as properly encoded values. Do not use `db.dropDatabase()`, drop whole
collections, delete administrator accounts, or remove another subscriber.
Unknown remaining data requires inspecting its owner/schema, not broad deletion.

## Process/network cleanup and retry

Compare against the pre-test inventory. Remove only this attempt's remaining
test namespace, links, loopback addresses, and processes. Use owned process
IDs/groups rather than `killall` in additional cleanup. A timeout can prevent
the upstream cleanup from finishing. Missing resources after successful upstream
cleanup are normal; conflicting unrelated resources must be preserved.

Once cleanup is verified, a failing test remains a failure: diagnose and retry
from the same release with a new log. Once PASS and cleanup are both established,
proceed to [network-and-handoff.md](network-and-handoff.md). Do not run tests
concurrently with the final core, or claim success while cleanup is incomplete.

Source: [official built-in test guide](https://free5gc.org/guide/4-test-free5gc/).
