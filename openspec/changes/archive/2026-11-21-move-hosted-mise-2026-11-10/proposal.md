## Why

The hosted jobs install an older Mise than 2026.11.10, the latest stable release since 18
November 2026. The owner directed on 18 November 2026 that every governed repository take the latest
stable release of its supply. 2026.11.10 also fixes `mise exec` running Node's bundled npm instead
of the pinned npm when the inherited `PATH` already holds the tool (jdx/mise#15771, fixed by
jdx/mise#15838), the cause of a gate failure that ETHOS 0.2.0-beta.11's entry states as a known open
defect.

## What Changes

- Run the hosted jobs with Mise 2026.11.10 from `[supply] mise_version`.
- Generate the pipelines again from the common model.
- Record the move under Changed in the Changelog's Unreleased section.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The repository's checks and its publication behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/ci/verification.toml`, the generated pipelines and `CHANGELOG.md`. The lockfile stays at
version 3, and the Mise floor stays as it is. `tasks.md` is the sole progress ledger.
