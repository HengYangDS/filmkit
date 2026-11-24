## Why

The release proof of 0.32.0 on the lane's head `7f8d6b7` failed on 24 November 2026 in its gate `native-behavior` with `quality_behavior_javascript_coverage_scope_incomplete` [S1]. The gate requires the JavaScript coverage report to name exactly the repository's production JavaScript files [S2]. `record-every-run` added `src/filmkit/graph/opens.cjs`, the Node half of the recorder of what a run opens [S3], and no Node test loads it: the Python tests run it in Node children under the permission model, and such a child writes no coverage of its own [S4]. So the report lacks it.

The Change that added the recorder is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- `tests/graph/opens.test.mjs` loads the recorder in two ways: as the engine loads it, in a child Node with `--permission-audit`, its allowances and the recorder by `--require`, where a read and a write outside the allowances are one entry each and a child without `FILMKIT_OPENS` writes no log; and in the test's own process, where the channel's messages are published by hand and each read and write is one entry while other permissions are none. The second is what Node's coverage sees.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes and no behaviour changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

One test file. No engine behaviour, record or byte of a film changes, and the Changelog gains no entry: nothing a film or its maintainer meets changes. Out of scope: the gate's rule, which is ETHOS's. `tasks.md` is the sole progress ledger.
