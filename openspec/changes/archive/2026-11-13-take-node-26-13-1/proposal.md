## Why

Node 26.13.1, published on 10 November 2026, is a security release on the 26 line with nine fixes
rated high under seven CVE identifiers, mostly in its `http2` and `tls` modules, six rated medium
and three rated low. filmkit's Mise lock pins node 26.13.0, which runs its Node tests, its Markdown
formatting and the picture pipeline. 0.21.1 moved the uv and npm locks but left the Mise lock as it
was. Each film adopts a filmkit release only at its next edition, so the move ships as release
0.21.2.

## What Changes

- Declare node 26.13.1 in `.config/mise/config.toml` and lock it again with native `mise lock`; only
  node's lock entries change and the lock stays at version 3.
- Cut 0.21.2: `VERSION`, the dated Changelog section and the README's install line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its outputs behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `VERSION`, `CHANGELOG.md` and `README.md`. The
hosted GitHub jobs install the locked node through Mise; GitLab's macOS jobs do too, under their
runner's Mise. `tasks.md` is the sole progress ledger.
