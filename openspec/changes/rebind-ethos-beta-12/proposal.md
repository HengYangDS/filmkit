## Why

The repository declares and runs ETHOS 0.2.0-beta.11. The owner asked that every governed repository
run the latest ETHOS release, as the 0.2.0-beta.11 rebind records. 0.2.0-beta.12 was published on 27
November 2026 at 17:19 UTC and upgrades directly from 0.2.0-beta.11: its release binding at the tag
records `"0.2.0-beta.11" = "attested-main"` under `[release.upgrade_from]`, and its hosted journey
upgrades from 0.2.0-beta.11 on macOS arm64, Linux x64 and Linux arm64. It publishes its own Mise
declaration as the release asset `ethos-0.2.0-beta.12.mise.toml`, one row for each published
platform: `linux-arm64`, `linux-x64`, `macos-arm64`, `windows-arm64` and `windows-x64`. The
repository takes the three rows that are not Windows, as its pin has held since 0.34.1. The lane
binds the release on 29 November 2026 from 01:27 (UTC+8), once it has passed its 24-hour release
age, and reads the checksums from the release's `SHA256SUMS` then.

What 0.2.0-beta.12 asks of a repository that 0.2.0-beta.11 did not. The entry marks no item
Breaking.

- **One act that 0.2.0-beta.11 let through is refused:** the reference-transaction hook refuses the
  deletion of a legacy release ref that stands before the commit of its legacy table. It reaches
  only a repository that declares a legacy table; `.ethos/release.toml` declares none. Of the four
  new gap codes, `legacy_role_rename_history_unshared` concerns legacy role refs too, and the three
  `proof_attestation_plan_artifact_*` codes concern only a proof record that cites its plan by
  digest, which a record takes only when its plan is too large to carry. This lane changes a handful
  of paths, so its proof record carries its plan as before.
- **The commit grammar admits `style`.** A repository's own `subject_pattern` stays in force; this
  repository declares none, so `style` is admitted once the release is bound. Nothing to do.
- **A staged admission is judged by its staged tree.** The index-target preview of
  `ethos lane prewrite` and the commit's admission evaluate OpenSpec on the staged tree; a staged
  tree that does not pass is reported under `reported_gaps`, a key that every prewrite answer
  reaching the evaluation now carries, and the `pre-commit` hook prints one note for it. The
  obligation `staged-openspec-tree` is reporting, not armed. A note at a commit is expected.
- **New report fields, none of which changes a verdict, exit, required gap or Attestation:**
  `data.unexamined` on `ethos prove --readiness --execute`; `summary.environment` on an executed
  proof, with each declared command's `executable` and `supplier` (`declared`, `locked`,
  `host-baseline`, `launch-path` or `unresolved`); `data.gate_inputs`, whose records go under
  `gate-results/` in the Git-common store and which `ethos hook retire-records` retires; and
  `data.footprint`. The lane reads the `supplier` of the declared command gate `sample-sources` to
  confirm that the proof launched as the hosted job does (design).
- **Store budgets report and refuse nothing.** The preview of `ethos hook retire-records` reports
  the Git-common store against `retention.status_bytes`, and that of `ethos hook retire-supply` the
  host store against the new `retention.host_bytes`. No command refuses for bytes.
- **`ethos hook retire-supply --scan <root> --release-absent`** releases the host store's consumer
  records of absent repositories. It is the host's housekeeping, not a change to this repository.
- **A declared command may name `{scratch}`.** No command of `system/gates.toml` holds that text
  (read on 28 November 2026), and a registry names it only once every runtime that proves the
  repository reads it; 0.2.0-beta.11, the rollback, does not. Nothing to do.
- **The tool catalog admits sqlfluff** with the carrier `.config/checks/sqlfluff/.sqlfluff`. The
  repository has no sqlfluff file. Nothing to do.
- **The shipped Vale policy ignores the front-matter field `workaround`**, and the shipped
  markdownlint configuration names `defects/**/*.md` among its globs. No diagnostic is added; no
  file here has that field. The repair of the authored-name gap names `identifier_sources` as a
  third way out; no verdict changes. The Ruff and format-selection policy changes are ETHOS's own.
- **The Docs Registry gains "Decision records" and the governance documents the Writing Standard.**
  No command, schema or check changes; each keeper migrates its records through a lane of its own.
  The engine's documentation is the Change `document-the-engine`'s, not this one's.
- **Known open defects are recorded under ETHOS's `defects/`**, one file each (73 entries, 65 open
  at the tag), and no longer in the Changelog. The design names those a rebind lane can meet. One is
  stated in the entry too: branch names are fixed (`main`, `dev`, `candidate/dev`, `work/`,
  `proposal/`); this repository uses them.
- **Not qualified by this beta:** a rollback after the declaration repair (this lane keeps the table
  form and runs no `ethos lane repair-paradigm --pin`), the adopter journey on Windows, interruption
  recovery and uninstall while a consumer runs, and GitLab-hosted CI and GitLab publication. The
  repository's GitLab jobs are qualified only by its own pipelines, which are read before landing.
- **Windows is deprecated.** 0.2.0-beta.12 still builds and publishes the Windows archives; a later
  release removes them. The pin omits them already.
- **Fixed, and asking nothing of the repository's files:** ETHOS's locked install of its own tool
  supply takes each archive from the URL its lock records (this repository's CI installs its locked
  tools with its own `mise install --locked`); a heavy run keeps its place in the host queue after
  its holder is killed (`ethos host status` may list such a ticket as `holding` with `holder`
  `gone`); the `source-format`, `markdown-lint` and `config-quality` gates start each tool a fixed
  number of times (the registry declares none of the three); a full proof on a quiet host no longer
  waits one sampling interval; and the fixes to the reclamation of a runtime generation, to lane
  abandonment, to the accepted closeout of legacy release refs and to the record of a proof with
  many changed paths.
- **Gate providers by catalog ID.** 0.2.0-beta.11 introduced the catalog, and 0.2.0-beta.12 still
  resolves a legacy `ethos.<module>:<callable>` name with the note `gate_provider_legacy_name`. The
  0.2.0-beta.11 rebind kept the legacy names because its rollback, 0.2.0-beta.10, refused an ID, and
  placed the rename in this rebind. This rebind's rollback, 0.2.0-beta.11, resolves all three IDs
  the registry needs, so the rename is made now.
- The release keeps result schema 3. Before the tag ETHOS proved its candidate on disposable copies
  of 14 governed trees: 12 passed a full proof, and against 0.2.0-beta.11 it found no new required
  gap and no new refusal. The entry does not name the trees.

## What Changes

- Replace the 0.2.0-beta.11 declaration in `.config/mise/config.toml` with the three rows that are
  not Windows of the declaration published with 0.2.0-beta.12, keeping the `http:ethos` table form,
  and lock it again with native `mise lock`; the lock stays at version 3 and holds no Windows table.
- Bind the repository to the 0.2.0-beta.12 runtime through the locked console's `hook install`,
  keeping the 0.2.0-beta.11 runtime as the rollback.
- Check both generated pipelines with `ethos lane project --check`; the common CI model is the same
  at both tags, so neither file is expected to change.
- Name the three providers of `system/gates.toml` by their catalog IDs: `provider.code-static`,
  `provider.code-behavior` and `provider.source-integrity`.
- Record the move under `Changed` in the Changelog's `Unreleased` section.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The film kit, its commands and its packaging behave as before, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`.config/mise/config.toml`, `.config/mise/mise.lock`, `system/gates.toml`, `CHANGELOG.md` and the
repository-common runtime selection. Both generated pipelines are checked and expected unchanged.
This Change cuts no release: it ships in filmkit 0.36.0 with the Change `document-the-engine`, whose
release steps follow both Changes. `tasks.md` is the sole progress ledger.
