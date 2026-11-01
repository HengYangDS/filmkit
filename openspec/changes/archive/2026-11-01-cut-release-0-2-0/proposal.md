## Why

filmkit's latest release, v0.1.1, dates from 2026-10-30. Since then `Unreleased` has gathered a
breaking change: the assembly refuses thought takes that end abruptly. It also holds two fixes to
the endings review and the run-on audition, the move to ETHOS 0.2.0-alpha.25 and to the latest
stable engine supply, the `undici` override and a contributor guide. A film pins a tag, so these
reach films only through a release. Before 1.0.0 a breaking change takes a minor release: 0.2.0.

## What Changes

- Date the `Unreleased` notes as `[0.2.0] - 2026-11-01`, open an empty `Unreleased`, and point the
  history links at `v0.1.1...v0.2.0` and `v0.2.0...HEAD`.
- Set `VERSION` to 0.2.0 and the README's example pin to `v0.2.0`.

The engine does not change in this Change; the release then follows `CONTRIBUTING.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This Change edits release metadata only, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`CHANGELOG.md`, `VERSION` and `README.md` only. The signed `v0.2.0` tag, its publication to both
peers and the Release pages follow the landed source and are not tasks of this Change.
