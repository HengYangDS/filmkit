## Why

The repository tracks three formatter carriers that repeat what installed ETHOS already ships.
`.config/checks/prettier/prettier.toml` sets `proseWrap` and `printWidth`,
`.config/checks/ruff/ruff.toml` sets `line-length` and `target-version`, and
`.config/checks/taplo/taplo.toml` sets `column_width`; the shipped Prettier, Ruff and Taplo
policies hold each of these settings with the same value. ETHOS always applies its shipped policy
and reads a repository carrier only as an increment on top of it, so these three files change
nothing; they are a second copy that can drift. The owner asked on 14 November 2026 that a repeated
mechanism in a governed repository give way to the common base.

`.config/checks/format-selection/policy.toml` stays: it declares this repository's own carriers.

## What Changes

- Remove `.config/checks/prettier/prettier.toml`, `.config/checks/ruff/ruff.toml` and
  `.config/checks/taplo/taplo.toml`.
- Record the removal in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Formatting and linting are decided by the same settings as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/checks/prettier/prettier.toml`, `.config/checks/ruff/ruff.toml`,
`.config/checks/taplo/taplo.toml` and `CHANGELOG.md`. No engine source, test, gate, pipeline or
release changes, and no version is cut. `tasks.md` is the sole progress ledger.
