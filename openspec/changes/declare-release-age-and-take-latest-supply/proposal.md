## Why

The owner decided on 13 November 2026 that every governed repository takes the latest stable release
of its supply with a release age of 0 hours, and that the age is declared configuration, in hours.
Mise hides a release younger than 24 hours unless a repository declares otherwise, so until now
filmkit waited a day without saying so anywhere. Its declared uv 0.13.7 trails 0.13.8, its exact
pins trail coverage 7.17.3 and Prettier 3.10.1, and its npm lock trails @hono/node-server 2.1.8 and
ws 8.23.0. None of them carries a security note. Each film adopts a filmkit release only at its next
edition, so the moves ship as a release of their own, 0.21.3, together with the ETHOS 0.2.0-beta.10
binding.

## What Changes

- Declare the release age: `minimum_release_age = "0h"` under `[settings]` in
  `.config/mise/config.toml`.
- Declare uv 0.13.8 there and lock it again with native `mise lock`; only uv's lock entries change
  and the lock stays at version 3.
- Move the exact pins to coverage 7.17.3 and Prettier 3.10.1, with their locks, and the npm lock to
  @hono/node-server 2.1.8 and ws 8.23.0.
- Keep transformers at 5.22.2. Release 5.23.0 is a few hours old and sits on the narration path,
  where a move is accepted by synthesizing the sample film's takes again and comparing them; it
  moves with the narration engine in the next filmkit release.
- Keep filmkit's own Markdown formatting, now on Prettier 3.10.1: ETHOS's Markdown format gate
  leaves an active Change's OpenSpec documents to the OpenSpec owner, so it checks fewer files than
  `format:markdown:check`. The step retires in a later release, after its OpenSpec globs go.
- Cut 0.21.3: `VERSION`, the dated Changelog section and the README's install line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its outputs behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `pyproject.toml`, `uv.lock`, `package.json`,
`package-lock.json`, `VERSION`, `CHANGELOG.md` and `README.md`. None of the moves reaches rendering,
narration or packaging, so acceptance is `mise run check`, `npm ls --all --include=dev` and the
proof, without a sample build. `tasks.md` is the sole progress ledger.
