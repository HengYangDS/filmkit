## Why

Since 14 November 2026 the engine declares a release age of 0 hours (`minimum_release_age = "0h"` in the Mise configuration), so that a refresh takes the latest stable releases without a waiting day. On 18 November 2026 the owner set the age to 72 hours for the host and every governed repository, asked that no test or script hold the number, and exempted the owner's own repositories and tools. Both decisions reached this repository through the repository steward's session, which heard them first-hand; the common form of the declaration is the ETHOS product session's.

A release taken in its first hours is taken before anyone has run it. On 18 November this repository took `puppeteer-core` 25.18.1 and HyperFrames 0.9.64 less than a day after they were published, and `mlx-audio` 0.6.6 less than two.

## What Changes

- The Mise configuration declares `minimum_release_age = "72h"`: a tool that Mise resolves is taken only when its release is three days old. A version the configuration pins exactly and the lock holds is installed as before.
- `.npmrc` declares `min-release-age=3`: npm resolves no version younger than three days. `npm ci`, which installs the lock, is not affected.
- uv's line is not part of this Change. It is declared with a relock in one commit once every artifact of the uv lock is 72 hours old, which the lock's own upload times put at 20 November 2026, 14:35 CST; see `design.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement of the engine names a release age, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.npmrc` (new) and the Changelog. No source file, test or script changes, and none holds the age: each resolver reads it from its own configuration. A film is not touched; the films' declarations are the repository steward's to write in their own lanes. `tasks.md` is the sole progress ledger.
