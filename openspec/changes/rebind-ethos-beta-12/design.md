## Context

See [proposal.md](proposal.md). The move follows ETHOS's successor-first adopter cutover: bind the
release in the lane, prove, publish for review, land, and publish the accepted head. Between
0.2.0-beta.11 and 0.2.0-beta.12 no entry is marked Breaking; the one added refusal reaches only a
repository with a legacy table; the new report fields change no verdict; and Windows is deprecated.

What the release leaves alone, read at the two tags on 28 November 2026: the common CI model
`.config/ci/verification.cue` and the projection adapters below `src/ethos/adapters/projections/`
have no diff, so the generated pipelines should come out unchanged; and ETHOS's own supply pins
(Mise floor 2026.11.9, Node 26.13.1, Python 3.14.10, uv 0.13.8, Vale 3.27.0) are the same, so the
repository's Vale, which follows ETHOS's, stays at 3.27.0.

The published declaration. `tools/ci/delivery/release_assets.py` at the tag (`assemble`) writes
`ethos-<version>.mise.toml` from the archives that the release legs qualified, one row per platform
in sorted order, and the tag's GitHub workflow calls it with
`--required linux-x64,linux-arm64,macos-arm64 --optional windows-x64,windows-arm64`. ETHOS's own
readback of the release (forge metadata, read on 28 November 2026) lists the asset at 1,299 bytes,
the size that form gives for all five rows, and lists all five archives. The repository's table
takes three of them; on 29 November it reads as below, each checksum read from `SHA256SUMS` and
checked against the asset's published digest:

```toml
# The ETHOS release declaration published with v0.2.0-beta.12: its linux-arm64, linux-x64 and macos-arm64 rows.
[tools."http:ethos"]
version = "0.2.0-beta.12"

[tools."http:ethos".platforms]
linux-arm64 = { url = "https://github.com/HengYangDS/ethos/releases/download/v0.2.0-beta.12/ethos-0.2.0-beta.12-linux-arm64.tar.gz", checksum = "sha256:<SHA256SUMS>", bin_path = "ethos/bin" }
linux-x64 = { url = "https://github.com/HengYangDS/ethos/releases/download/v0.2.0-beta.12/ethos-0.2.0-beta.12-linux-x64.tar.gz", checksum = "sha256:<SHA256SUMS>", bin_path = "ethos/bin" }
macos-arm64 = { url = "https://github.com/HengYangDS/ethos/releases/download/v0.2.0-beta.12/ethos-0.2.0-beta.12-macos-arm64.tar.gz", checksum = "sha256:<SHA256SUMS>", bin_path = "ethos/bin" }
```

The known open defects under ETHOS's `defects/` at the tag that a rebind lane can meet, each with
its recorded workaround:

- `console-reexecutes-in-selected-runtime`: until the bind, the newer console answers with the
  selected 0.2.0-beta.11 build. Preview with the new runtime's interpreter,
  `<runtime>/python/bin/python -B -I -m ethos.cli`, and read `summary.runtime`.
- `installed-image-bytecode-refuses-hook-install`: one run of that interpreter without `-B` makes
  `hook install` answer `hook_install_failed:hook_runtime_payload_mismatch`. Never run it without
  `-B`; the repair is `mise uninstall` and `mise install` of the release.
- `command-gate-verdict-follows-launch-shell`: the declared command gate `sample-sources` runs in
  the proof's launch environment. Launch as the decision below says.
- `behavior-gate-uv-cache-missing-wheel`: on a host whose uv cache lacks a locked wheel, the
  behavior gate ends with `test_environment_sync_failed`; one online `uv sync --locked` by the
  pinned uv fills the cache.
- `lane-path-day-refusal-names-no-path`: a lane started before 08:00 on 29 November (UTC+8) carries
  the UTC day, 2026-11-28. A refused `--path` names no expected path; it is the `path` field of the
  `--json` result.

## Goals / Non-Goals

**Goals:**

- Run every gate and lifecycle command of the film kit, locally and in the hosted jobs, on
  0.2.0-beta.12.
- Name every gate provider of the registry by its catalog ID.
- Keep the 0.2.0-beta.11 runtime as the rollback until the landing is accepted.

**Non-Goals:**

- Changing any source, test or declared command of the film kit, or what any gate checks.
- Naming `{scratch}` in a declared command: 0.2.0-beta.11, the rollback, does not read it.
- The bare pin of `ethos lane repair-paradigm --pin`: the repository keeps the table form, and a
  rollback after that repair is not qualified by this beta.
- Releasing absent consumers of the host store (`ethos hook retire-supply --release-absent`): the
  host's housekeeping, not this repository's.
- Moving other supply. ETHOS's supply does not move with this release; a supply move is its own
  Change.
- The release. filmkit 0.36.0 carries this Change and `document-the-engine`.

## Decisions

- Copy the three rows of the published declaration that are not Windows, unchanged, into the
  `[tools."http:ethos"]` table, the form the repository holds, with a comment that names the release
  and the rows it takes, and lock with native `mise lock` after checking each checksum against
  `SHA256SUMS` and the published asset digest. The lock keeps `lockfile_version = 3`, and
  `lockfile_platforms` stays as 0.34.1 declared it, so the lock holds the same five platform entries
  for ETHOS as before and no Windows table.
- Name the providers by catalog ID in this rebind: `ethos.adapters.gates.code_quality:static_report`
  becomes `provider.code-static`, `...:behavior_report` becomes `provider.code-behavior`, and
  `ethos.adapters.gates.provenance.observation:integrity_report` becomes
  `provider.source-integrity`. Reason: the 0.2.0-beta.11 rebind deferred the rename to this one
  because its rollback refused an ID, and `src/ethos/contracts/gate-providers.toml` at
  `v0.2.0-beta.11` resolves all three IDs, so this rebind's rollback needs no legacy name. The
  legacy names still resolve under 0.2.0-beta.12, so the rename is a choice of one form, not a
  repair; it lands before `document-the-engine` adds its four documentation gates, which then take
  the IDs too (`provider.docs-registry`, `provider.markdown-links`, `provider.markdown-lint`,
  `provider.prose` in 0.2.0-beta.12's catalog).
- Check both pipelines with `ethos lane project --check` as a task of its own. A file that differs
  from the projection is `generated_projection_drift:<path>`; the generated files are never edited
  by hand. With the common model unchanged, any drift is a finding to read before anything is
  applied.
- Launch every local proof as the generated hosted job does: `mise exec --locked --` around the lane
  runtime's `ethos prove`, in the work tree, never with Mise's activation variables removed alone.
  Under 0.2.0-beta.12 the executed result states it: `summary.environment` names the locked tools
  that the launch path resolves outside their locked install, and the check of `sample-sources`,
  whose command starts `uv`, names its `supplier`: `locked` when the lock supplies `uv`, and
  `launch-path` or `unresolved` when the launch environment did, which is a finding.
- Cut no release. The Changelog's `Unreleased` section records the move, and filmkit 0.36.0 dates it
  together with `document-the-engine`, after both Changes are committed.

## Risks / Trade-offs

- [A gate that passed under 0.2.0-beta.11 fails under 0.2.0-beta.12] → ETHOS's copies run before the
  tag passed a full proof on 12 of 14 governed trees and found no new required gap; it does not name
  the trees, so this tree's result there is not known. If the lane meets a failure, it is repaired
  at its owner, or the repository restores the 0.2.0-beta.11 declaration in a new Change and binds
  the retained runtime.
- [A local verdict depends on the launch environment] → Launch as decided above; the hosted jobs of
  the proposal decide, and they are read before landing.
- [GitLab-hosted CI is not qualified by this beta] → The proposal's GitLab review job, run on this
  host's guest under a host ticket, qualifies it for this repository before landing.
- [A rollback after the bind is not qualified by 0.2.0-beta.12's journey] → A rollback restores the
  0.2.0-beta.11 declaration and lock in a new Change and runs the full proof before it lands. The
  catalog IDs stay, since 0.2.0-beta.11 resolves them.

## Migration Plan

Copy the declaration's rows and lock them, install the locked supply, bind the runtime, check the
pipelines, rename the providers, run the repository's check, archive the Change and prove the
archived head; then filmkit 0.36.0's release steps, after `document-the-engine` is committed. To
roll back, restore the 0.2.0-beta.11 declaration in a new Change, then bind the retained runtime
with the current console's `hook install --runtime <0.2.0-beta.11 runtime>`.
