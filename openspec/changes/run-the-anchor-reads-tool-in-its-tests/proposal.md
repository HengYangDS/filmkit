## Why

The release proof of 0.30.0 on the lane's head `0b941b1` failed on 23 November 2026 in its gate `native-behavior`: the Node suite ran with none failed, and the gate reported `quality_behavior_javascript_coverage_scope_incomplete`. The gate requires every JavaScript file that it selects to appear in the c8 coverage report of one run of the Node suite. Of the 44 files it selected, 43 are in the report; the one that is not is `src/filmkit/picture/anchor-reads.mjs`, which `anchor-picture-cues-in-the-script` added. The check before narration runs it as a command from Python (`filmkit.picture.anchor_reads`), and no Node test runs it.

The Change that added the file is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- `tests/picture/anchor-reads.test.mjs` runs the tool as `filmkit.picture.anchor_reads` runs it, `node anchor-reads.mjs <timeline> <step>` in a film's folder, and holds the report it writes and the status it exits with.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement speaks of how a test runs a tool, and the tool's behaviour does not change, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`tests/picture/anchor-reads.test.mjs` only. No engine behaviour, gate, record or byte of a film changes, and the Changelog gains no entry: nothing a film or its maintainer meets changes. Out of scope: the gate's rule, which is ETHOS's. `tasks.md` is the sole progress ledger.
