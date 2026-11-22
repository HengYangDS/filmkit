## Why

The release proof of 0.27.0 on the lane's head `1e4d459` failed on 22 November 2026 in its gate `native-behavior`: 2217 tests ran and none failed, and the gate reported `quality_behavior_coverage_scope_incomplete`. The gate requires every tracked Python file that is not a test to appear in the coverage report of one run of the suite in its own process. `src/filmkit/register/__main__.py`, the repository's only `__main__.py`, which `check-the-formal-register` added, runs only under `python -m filmkit.register`, and no test runs it, in its own process or in a child; so the file is absent from the report. Collecting the suite imports each of the other 109 such files.

The Change that added the file is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- `tests/register/test_register_check.py` runs the package as `python -m filmkit.register` runs it, in the test's own process, and holds that the run prints the check's report and exits with the check's refusal.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement speaks of how a test runs a module, and the command's behaviour does not change, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`tests/register/test_register_check.py` only. No engine behaviour, gate, record or byte of a film changes, and the Changelog gains no entry: nothing a film or its maintainer meets changes. Out of scope: the gate's rule, which is ETHOS's, and measuring the tests' child processes. `tasks.md` is the sole progress ledger.
