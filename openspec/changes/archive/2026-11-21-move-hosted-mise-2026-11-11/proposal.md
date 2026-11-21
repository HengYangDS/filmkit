## Why

The hosted jobs install Mise 2026.11.10. Mise 2026.11.11, published on 20 November 2026 at 15:20
UTC, is the latest stable release, and it passes the 24-hour release age at 15:20 UTC on 21
November 2026. The owner directed on 18 November 2026 that every governed repository take the latest
stable release of its supply.

## What Changes

- Run the hosted jobs with Mise 2026.11.11 from `[supply] mise_version`.
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
