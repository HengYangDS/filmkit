## Why

Since 18 November 2026 the engine holds third-party supply to a release age of 72 hours: Mise and npm each read it from their own configuration, and uv's line waited for its lock to be that old (`hold-third-party-supply-72-hours`). On 19 November 2026 the owner shortened the age to 24 hours for every governed repository, because three days slow each iteration, and added that a repository writes its own age and that ETHOS's base holds 24 hours for one that writes none. Both decisions reached this repository through the repository steward's session, which heard them first-hand.

With 24 hours, uv's line no longer has to wait: the youngest artifact of the uv lock was uploaded 46 hours before this Change was written.

## What Changes

- The Mise configuration declares `minimum_release_age = "24h"`, from `"72h"`.
- `.config/npm/npmrc` declares `min-release-age=1`, from `3`.
- `pyproject.toml` declares `exclude-newer = "24 hours"` under `[tool.uv]`, and the uv lock is written again in the same commit. The lock records the age as a span, and no package and no artifact of it changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement of the engine names a release age, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/npm/npmrc`, `pyproject.toml`, `uv.lock` and the Changelog. A version that a configuration pins exactly and a lock holds installs as before. No source file, test or script changes, and none holds the age: each resolver reads it from its own configuration. A film is not touched; the films' declarations are the repository steward's to write in their own lanes. `tasks.md` is the sole progress ledger.
