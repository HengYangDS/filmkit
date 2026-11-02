# Proposal

## Why

The repository declares and runs ETHOS 0.2.0-alpha.25. The owner asked that every governed
repository run the latest ETHOS release, which is now 0.2.0-alpha.26. Its adopter-facing changes are
the paradigm root rules, which this repository already meets (`CONTRIBUTING.md` beside `AGENTS.md`
and `README.md`, and `LICENSE` because releases are tagged), formatters that run on the settings
ETHOS ships, and the `jdx/mise-action` v5.2.5 pin of the common CI model.

## What Changes

- Replace the 0.2.0-alpha.25 declaration in `.config/mise/config.toml` with the one published with
  0.2.0-alpha.26, lock it again with native `mise lock`, and bind the repository family to that
  runtime, keeping 0.2.0-alpha.25 as the rollback.
- Regenerate the CI projection, whose Mise action pin moves to v5.2.5.
- Record the move under `Unreleased` in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine behaves as before and no film's output changes, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `.github/workflows/ci.yml`, `CHANGELOG.md`
and the repository-common runtime selection. Films pin filmkit by tag, so none of them moves.
`tasks.md` is the sole progress ledger.
