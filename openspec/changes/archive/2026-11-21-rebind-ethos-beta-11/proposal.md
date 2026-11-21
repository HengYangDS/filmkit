## Why

The repository declares and runs ETHOS 0.2.0-beta.10. The owner asked that every governed repository
run the latest ETHOS release. 0.2.0-beta.11 upgrades directly from 0.2.0-beta.10 and publishes its
own Mise declaration, whose platform checksums equal the release's `SHA256SUMS` and the published
asset digests.

What 0.2.0-beta.11 asks of a repository that 0.2.0-beta.10 did not:

- **Breaking: hosted CI artifacts expire after 14 days.** The common CI model declares the retention
  once, so the generated pipelines change: `retention-days: 14` on each GitHub upload step and
  `expire_in: 14 days` on each GitLab `artifacts` block. Only `ethos lane project --check` reports
  the old files as `generated_projection_drift:<path>`; neither `ethos prove` nor a commit refuses
  them, so the lane that binds the release applies the previewed patch with
  `ethos lane project --apply`.
- **Breaking: a release build's `ethos adopt` plans its own pin** in `.config/mise/config.toml`; a
  configuration that holds an `http:ethos` table is an `adoption_conflict` for that command. Binding
  this release through that table and `ethos hook install` works as before. The new
  `ethos lane repair-paradigm --pin` would replace the table with the release's bare pin; this
  rebind keeps the form the repository holds.
- **Breaking: the host contention gap reads** `host_admission_contended:<operation>:<pid>:<since>`
  and no longer prints a repository path.
- **Breaking: a wait for the host queue no longer ends at `timeout.admission_seconds`.** It ends at
  the admission ceiling, 36,000 seconds; `ethos host run --wait <seconds>` stays the caller's own
  total. The repository declares no lower bound, so only the length of a long wait changes.
- **Breaking: no result continues with `export ETHOS_ACTOR=<holder>`.** A result without an actor
  asks to rerun the command with `--actor <identity>`; the lane keeps `ETHOS_ACTOR` set for its
  commands.
- The package-docstring obligation reports and no longer blocks: a tracked `__init__.py` without an
  opening docstring appears under `reported_gaps`, not among the required gaps.
- A native gate provider's child no longer inherits a shell's `mise activate` state. A
  repository-declared command gate still runs in the proof's launch environment: launch a local
  proof from a clean environment that holds what the hosted job declares, or from the shell as it
  is, and never with the Mise activation state removed alone (a known open defect of the entry).
- `ethos lane format` and the source-format, Markdown, prose, link and configuration gates leave
  alone a path that a tracked `.gitattributes` marks `linguist-vendored` or `linguist-generated`. A
  mark that only the Git directory's `info/attributes` or a `core.attributesFile` gives takes no
  path out of these checks.
- The cleanup of the shared store at the end of `ethos hook install` keeps an installation whose
  consumer it cannot read. From 0.2.0-alpha.8 through 0.2.0-beta.10 it could delete an installation
  that a repository still selected.
- `ethos lane prewrite --patch` judges the files as the patch leaves them wherever the temporary
  directory lies; with 0.2.0-beta.10 the temporary directory had to stay outside every checkout.
- Its supply moves to the stable releases of 18 November 2026: Mise 2026.11.9 as the floor, npm
  12.2.3, `uv` 0.13.8 (0.13.9's Windows executable lacks the dependency data the release inventory
  reads), the OpenSpec CLI 2.0.0 (2.1.0 removes an internal ETHOS's reader imports), Vale 3.27.0,
  Python 3.14.10 (build 20261110), Prettier 3.10.1, markdownlint-cli2 0.24.1 and ESLint 10.15.0.
- A gate declaration names its provider by a catalog ID such as `provider.code-behavior`. A legacy
  `ethos.<module>:<callable>` name keeps resolving for one support window, and the gate's result
  carries the note `gate_provider_legacy_name` with the ID to declare. An earlier release refuses an
  ID, so this rebind keeps the legacy names while its rollback release is 0.2.0-beta.10.
- In a lane whose selected runtime is still 0.2.0-beta.10, the newer `ethos` console re-executes in
  the selected runtime, so a preview answers with the older build (a known open defect of the
  entry). Until the bind, preview with the new runtime's interpreter,
  `<runtime>/python/bin/python -B -I -m ethos.cli`, and read `summary.runtime`.

A copies run of `dev` under 0.2.0-beta.11's landed head e4d9d04d3 on 18 and 19 November 2026 found,
besides the pipeline retention, nothing to repair, and its full proof passed.

## What Changes

- Replace the 0.2.0-beta.10 declaration in `.config/mise/config.toml` with the declaration published
  with 0.2.0-beta.11, unchanged, keeping the `http:ethos` table form, and lock it again with native
  `mise lock`; the lock stays at version 3.
- Bind the repository family to the 0.2.0-beta.11 runtime through the locked console's
  `hook install`, keeping the 0.2.0-beta.10 runtime as the rollback.
- Regenerate both pipelines with `ethos lane project --apply`, which adds only the 14-day retention
  lines.
- Release the move as a rebind-only patch after 0.26.0: `VERSION`, the dated Changelog
  section and the README's install line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its packaging behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, both generated pipelines, `CHANGELOG.md`,
`VERSION`, the README's install line and the repository-common runtime selection. The hosted jobs'
Mise moves in the same lane's Change `move-hosted-mise-2026-11-10`. `tasks.md` is the sole progress
ledger.
