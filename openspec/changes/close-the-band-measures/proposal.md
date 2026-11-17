## Why

The release proof of 0.23.0 failed in its behaviour gate on 18 November 2026. `ground_check`, which the Change `shorten-the-build` added to prove a derived picture's caption band, counts the frames of the band's measures from a file it opens and never closes. The proof runs the suite with warnings as errors (`pytest -q -W error`), and the unclosed file fails two tests of the derivation there, six on a host with FFmpeg on its path. The lane's own check runs the suite without that flag and passed on every head since the function was written on 17 November.

`shorten-the-build` is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- `ground_check` reads the band's measures inside a block that closes the file.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. What the ground check measures, refuses and records is unchanged, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`src/filmkit/picture/ground.py`. No requirement, gate, record or byte of a film changes, and the Changelog gains no entry: the function was never released without the repair. `tasks.md` is the sole progress ledger.
