## Why

On 26 November 2026 at 05:49 the owner decided that Mise is used at its latest stable release, one release for all: 「统一用最新稳定版」. He said it to the session that onboards repositories to ETHOS, which relayed it to the engine's maintainer at about 05:54. At 06:08 he confirmed to that session the reading that every Mise pin of every repository ETHOS governs moves to that release (relayed at about 06:09; his words are in the record [S1]). That session upgraded the CI macOS guest's Mise to 2026.11.14 at 05:50 (relayed, not read first-hand).

Mise 2026.11.14, published on 24 November 2026 at 11:00 UTC, is Mise's latest stable release [S2]. It passed the repository's 24-hour release age at 11:00 UTC on 25 November [S3]. filmkit pins Mise's release in one place, the CI declaration's `[supply] mise_version`, at 2026.11.11; ETHOS's projection writes from it the version that the hosted GitHub job installs [S4].

## What Changes

- `[supply] mise_version` moves to 2026.11.14, and `ethos lane project` writes the CI files again. In `.github/workflows/ci.yml` only the `jdx/mise-action` step's `version` changes; `.gitlab-ci.yml` comes out byte-identical, since GitLab's jobs run the Mise of the runner they land on and the projection pins none.
- The Mise configuration's `min_version` stays at 2026.10.14: it is a floor, not a pin (design decision 2).
- The Mise lock does not change: Mise 2026.11.14's own `mise lock` writes it again byte for byte (task 1.2).
- The Changelog records the move under `Changed` in its `Unreleased` section.

Out of scope, each with its owner in the design: the floor's form, the GitLab guest's Mise, the films' pins and the lock's format.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement in force names Mise's release or where it comes from (design, Context), so `.openspec.yaml` sets `skip_specs: true`.

## Impact

- **Configuration:** `.config/ci/verification.toml` and the generated `.github/workflows/ci.yml`.
- **Text:** `CHANGELOG.md`.
- **Unchanged:** `.gitlab-ci.yml` (generated again, same bytes), `.config/mise/config.toml` with its `min_version`, `.config/mise/mise.lock`, `uv.lock`, `package-lock.json`, the README, `CONTRIBUTING.md`, and every file below `src/`, `tests/` and `examples/`.
- **Developers:** a checkout runs on any Mise from 2026.10.14, as before. This host's Mise, from Homebrew, is 2026.11.14 [S5].
- **Release:** a patch, 0.34.2, after 0.34.1.
- **Films:** none. Each film moves its own pins in its December lane [S1].

Owner: the engine's maintainer (the films session). The sources are listed in the design.
