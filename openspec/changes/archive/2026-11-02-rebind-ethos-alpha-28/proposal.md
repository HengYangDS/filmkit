# Proposal

## Why

The repository declares and runs ETHOS 0.2.0-alpha.27. The owner asked that every governed
repository run the latest ETHOS release, which is now 0.2.0-alpha.28. Its adopter-facing changes are
small. `ethos publish` of `dev` names the proposals that the accepted branch absorbed, so their
retirement is no longer left to memory. `ethos land` takes its authority from the Change that the
admitted proof carries. `ethos lane archive-change` previews the archive it would apply, so an
over-long merged requirement blocks the preview. Pushes run without Git's sparse pack walk. Its
bundled supply moves Vale to 3.26.0, and the common CI model is unchanged.

## What Changes

- Replace the 0.2.0-alpha.27 declaration in `.config/mise/config.toml` with the one published with
  0.2.0-alpha.28, lock it again with native `mise lock`, and bind the repository family to that
  runtime, keeping 0.2.0-alpha.27 as the rollback.
- Check the CI projection against the common model; it stays as it is.
- Record the move under `Unreleased` in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine behaves as before and no film's output changes, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `CHANGELOG.md`
and the repository-common runtime selection. Films pin filmkit by tag, so none of them moves.
`tasks.md` is the sole progress ledger.
