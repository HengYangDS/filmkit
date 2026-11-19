## Why

The release proof of 0.24.0 failed in its static gate on 19 November 2026. The gate lints every tracked JavaScript file with the ESLint that ETHOS ships, and `tests/picture/headless-composition.test.mjs` imports `fileURLToPath` and uses it nowhere: the commit that moved the picture to a native canvas removed the one line that used the name, the path of the animation library the browser loaded, and left the import. `mise run check` runs no JavaScript lint, and the gate, asked for alone, runs nothing, so every check of the lane had passed with the import in place.

The Change that brought that commit, `draw-pictures-natively`, is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- The test file no longer imports `fileURLToPath`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement speaks of a test file's imports, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`tests/picture/headless-composition.test.mjs`. No requirement, gate, record or byte of a film changes, and the Changelog gains no entry: the import was never released. `tasks.md` is the sole progress ledger.
