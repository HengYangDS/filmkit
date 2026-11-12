## Why

The repository declares and runs ETHOS 0.2.0-alpha.29. The owner asked that every governed
repository run the latest ETHOS release, and that every supply chain move to its latest stable
release without a separate confirmation. 0.2.0-beta.8 is that release; it upgrades directly from
0.2.0-alpha.29, and its hosted journey passed that upgrade, its rollback and the reactivation on
macOS arm64 and Linux x64. It publishes its own Mise declaration, whose platform checksums equal the
release's `SHA256SUMS` and the published asset digests.

Its adopter-facing changes since 0.2.0-alpha.29 that reach this repository are these:

- **Breaking (0.2.0-beta.6): the publication declaration carries no peer coordinate and no
  unexecuted command.** `.ethos/release.toml` no longer takes `forge_repository` in a peer, nor
  `local_verification_command` and `local_installation_command` in `[publication]`; the loader
  refuses each, and `ethos lane repair-paradigm --apply` removes it without echoing its value.
  Review observation resolves a peer's web repository from the remote's `http` or `https` URL
  instead.
- **Breaking (0.2.0-beta.7): the root, `lane`, `hook`, `attestation` and `host run` commands select
  one declared catalog operation.** Negated flags, `--authorize` without `--apply` and several paths
  after one `--paths` exit 2, and usage errors exit 2 with `usage_refused`. This repository's
  tracked files name none of these forms.
- The CI model pins `jdx/mise-action` v5.2.7, so the GitHub workflow is generated again.
- Result schema 3 and the structured `next`, the catalog's `next.form`, the redaction verb with the
  profile's `record_roots`, two-space TOML in repaired files and the root community health files
  arrive with the intermediate releases; this repository uses none of them in this Change.
- Among 0.2.0-beta.8's known open defects, Go's GO-2026-6859 affects the bundled `cue`, `vale` and
  `shfmt`, which ETHOS runs only as local commands over repository files without starting an HTTP
  server.

## What Changes

- Replace the 0.2.0-alpha.29 declaration in `.config/mise/config.toml` with the declaration
  published with 0.2.0-beta.8, unchanged, and lock it again with native `mise lock`.
- Bind the repository family to the 0.2.0-beta.8 runtime through the locked console's `hook
  install`, keeping the 0.2.0-alpha.29 runtime as the rollback.
- Remove the retired declaration fields with `ethos lane repair-paradigm --apply`.
- Generate the pipelines again from the 0.2.0-beta.8 common model, which moves only the
  `jdx/mise-action` pin.
- Record the move in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its packaging behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `.ethos/release.toml`, the generated
`.github/workflows/ci.yml`, `CHANGELOG.md` and the repository-common runtime selection. No source,
test, film, tag or release changes. Two archived Changes still name the GitLab peer's web address;
removing it from those records is a later Change on the owner's decision. `tasks.md` is the sole
progress ledger.
