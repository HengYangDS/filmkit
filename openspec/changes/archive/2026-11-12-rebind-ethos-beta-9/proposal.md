## Why

The repository declares and runs ETHOS 0.2.0-beta.8. The owner asked that every governed repository
run the latest ETHOS release, and that every supply chain move to its latest stable release without
a separate confirmation. 0.2.0-beta.9 publishes its own Mise declaration, whose platform checksums
equal the release's `SHA256SUMS` and the published asset digests.

Its adopter-facing changes since 0.2.0-beta.8 are these:

- **Breaking: the embedded OpenSpec CLI moves to 2.0.0.** OpenSpec 2.0 installs its skills in
  `.agents/skills/` and records its own in `.agents/skills/.openspec-target`, and the skill
  portfolio routes those packages to OpenSpec. A repository that keeps skill or command copies from
  an older OpenSpec release runs `openspec update` once; this repository keeps none.
- **Breaking: the redaction, the push check and the keyless marker verifier share one scan,** which
  now also reads percent-encoded paths. Re-verifying an earlier redaction whose base held a crossing
  entry or a percent-encoded fed path reports `redaction_unverified`; recorded attestations stay
  valid.
- A handed-off Work Lane lands on its new holder's proof instead of refusing `contradiction`.
- The common CI model is unchanged, so the pipelines stay as they are.
- It upgrades directly from 0.2.0-beta.8 and keeps result schema 3. Its locks take Go 1.27.4, `syft`
  1.57.1 and `grype` 0.121.3; among its known open defects, Go's GO-2026-6859 still affects the
  bundled `cue`, `vale` and `shfmt`, which ETHOS runs only as local commands over repository files
  without starting an HTTP server.

## What Changes

- Replace the 0.2.0-beta.8 declaration in `.config/mise/config.toml` with the declaration published
  with 0.2.0-beta.9, unchanged, and lock it again with native `mise lock`; the lock stays at
  version 3.
- Bind the repository family to the 0.2.0-beta.9 runtime through the locked console's
  `hook install`, keeping the 0.2.0-beta.8 runtime as the rollback.
- Check both pipelines against the 0.2.0-beta.9 common model, which 0.2.0-beta.9 does not change.
- Record the move in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its packaging behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `CHANGELOG.md` and the repository-common
runtime selection. The generated pipelines and the hosted jobs' Mise stay as they are. `tasks.md` is
the sole progress ledger.
