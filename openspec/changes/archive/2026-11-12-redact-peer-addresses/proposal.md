## Why

The owner decided on 12 November 2026 that the GitLab peer's address leaves this repository's
current tracked files, as it left DDWG's and web-ingestion-benchmark's, while published history
stays as it is. The 0.2.0-beta.8 move removed it from `.ethos/release.toml`. Two lines of the
archived Change `2026-11-01-refresh-repository-entry` still name it. `ethos lane redact
private-addresses` replaces each occurrence inside the effective record roots, which include the
archived Changes, with a keyed marker that only the owner's key can verify.

## What Changes

- Redact the two occurrences, one peer URL on each of two lines, with the owner's key, and verify
  the redaction.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its packaging behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`openspec/changes/archive/2026-11-01-refresh-repository-entry/proposal.md` and `tasks.md` only. No
commit is rewritten, and the remotes keep their history. `tasks.md` is the sole progress ledger.
