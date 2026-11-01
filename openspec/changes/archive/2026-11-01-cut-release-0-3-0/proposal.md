## Why

filmkit's latest release, v0.2.0, dates from 2026-11-01. Since then `Unreleased` has gathered the
concept contract and its check, the readings check for pronunciation contracts of schema version 2
with the dictionary's proposals, and narration's refusal to start when either check fails. The
ETHOS and DDWG films need these checks before they narrate their newly approved scripts, and a film
pins a tag, so the checks reach films only through a release. A film that declares no concept
contract and keeps a version 1 pronunciation contract narrates as before, so the release adds
behaviour without breaking any film: 0.3.0.

## What Changes

- Date the `Unreleased` notes as `[0.3.0] - 2026-11-02`, open an empty `Unreleased`, and point the
  history links at `v0.2.0...v0.3.0` and `v0.3.0...HEAD`.
- Set `VERSION` to 0.3.0 and the README's example pin to `v0.3.0`.

The engine does not change in this Change; the release then follows `CONTRIBUTING.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This Change edits release metadata only, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`CHANGELOG.md`, `VERSION` and `README.md` only. The signed `v0.3.0` tag, its publication to both
peers and the Release pages follow the landed source and are not tasks of this Change.
