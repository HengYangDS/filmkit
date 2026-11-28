Every command named here is light, except the repository's check where a measurement under host rule
3 has not shown it light, and the full proof at the archived head: each of those runs as the child
of a host ticket, `ethos host run --wait 14400 --root <lane> -- <command>`, queued under host rules
2, 8 and 9. Until task 1.2 binds the release, an ETHOS preview runs with the new runtime's
interpreter, `<runtime>/python/bin/python -B -I -m ethos.cli`, and is read by its `summary.runtime`;
that interpreter never runs without `-B` (design, known open defects). The tasks start once the
release is published and read back: on 28 November 2026 the owner exempted every repository that
ETHOS governs from ETHOS's own 24-hour release age (item C-16 of the maintainer's record of the
owner's words).

## 1. Runtime

- [x] 1.1 Replace the 0.2.0-beta.11 declaration in `.config/mise/config.toml` with the rows
      `linux-arm64`, `linux-x64` and `macos-arm64` of the declaration published with 0.2.0-beta.12
      (`ethos-0.2.0-beta.12.mise.toml`), each checksum read from the release's `SHA256SUMS` and
      checked against the asset's published digest, under a comment that names the release and the
      rows it takes; then lock again with native `mise lock`. Done when each row equals
      the published row byte for byte, the lock holds 0.2.0-beta.12 for the same five platform
      entries for which it held 0.2.0-beta.11, no 0.2.0-beta.11 entry and no `windows-*` table
      remains, the lock's diff changes only `http:ethos`, and the lock keeps `lockfile_version = 3`.
      The three rows equal those of the published declaration (sha256 `094105e2…`) byte for byte,
      and each checksum equals the release's `SHA256SUMS` (sha256 `7579c21f…`); the maintainer
      read both files back on 28 November 2026 and found each equal to its published digest.
      `mise lock http:ethos` kept `lockfile_version = 3`, changed only `http:ethos`, and holds
      0.2.0-beta.12 for the same five platform entries, with no 0.2.0-beta.11 entry and no
      `windows-*` table.
- [x] 1.2 Install the locked supply with `mise install --locked` and bind the repository to the
      0.2.0-beta.12 runtime with the locked console's `hook install`, keeping 0.2.0-beta.11 as the
      rollback. Done when CURRENT names the 0.2.0-beta.12 runtime and ROLLBACK the 0.2.0-beta.11
      runtime, and `ethos status --json` in the lane reports the lane ready with `summary.runtime`
      naming 0.2.0-beta.12.
      `mise install --locked` found every locked tool installed; the 0.2.0-beta.12 console's
      `hook install` bound the family. CURRENT names the 0.2.0-beta.12 runtime `3e6b10f2…` and
      ROLLBACK the 0.2.0-beta.11 runtime `8c663b10…`; at `3b6ada1`, with this Change named,
      `ethos status --json` reports the lane ready and `summary.runtime` names 0.2.0-beta.12.
- [x] 1.3 Check both pipelines against the 0.2.0-beta.12 projection with
      `ethos lane project --check --json`. Done when it reports both projections conforming and
      neither `.github/workflows/ci.yml` nor `.gitlab-ci.yml` changes; a drift stops the task and is
      read before any patch is applied.
      At `3b6ada1` the check reports both projections conforming, two outputs and no edit, and
      neither file changed.
- [x] 1.4 Name the providers of `system/gates.toml` by catalog ID: `provider.code-static` for
      `native-static`, `provider.code-behavior` for `native-behavior` and
      `provider.source-integrity` for `source-integrity`. Done when `system/gates.toml` names no
      `ethos.<module>:<callable>` provider and `ethos prove --root <lane> --json` reports no
      required gap; the note `gate_provider_legacy_name`, which a provider gate raises when it runs,
      is read absent in the full proof at the archived head.
      The registry names the three IDs and no other provider. With the rename in the work tree at
      `e86d116`, the proof preview under 0.2.0-beta.12 reports `pass`, state `ready`, no required
      gap, 11 planned gates; both runtimes' catalogs map the three IDs to the former names.
- [x] 1.5 Record under `Changed` in the Changelog's `Unreleased` section that the repository runs
      ETHOS 0.2.0-beta.12 instead of 0.2.0-beta.11 and that its gate registry names ETHOS's
      providers by catalog ID. Done when `npm run format:markdown:check` passes.
      The `Unreleased` section holds one `Changed` item for both; after the lane's environments
      were synced from the frozen locks offline (`uv sync --frozen --offline`,
      `npm ci --offline`), `mise run check:dependencies` and `npm run format:markdown:check` pass.
- [x] 1.6 Run the repository's check on the lane head. Done when `mise run check` passes, and the
      count of Node and Python tests is recorded here.
      At `76fb2f8`, as the child of one host ticket that held 289 s, `mise run check` passes: 296
      Node tests pass, the Markdown check is clean, and 2,627 Python tests pass with 1 skipped.

## Workflow follow-up

The tasks stop before the release. This Change cuts no release of its own: it ships in filmkit
0.36.0 with the Change `document-the-engine`, and 0.36.0's release steps (`VERSION`, the dated
Changelog section holding both Changes' entries with its compare link, and the install line wherever
`document-the-engine` leaves it) follow once both Changes are committed.

- Archive this Change and prove the archived head once; no gate result carries the note
  `gate_provider_legacy_name`.
- After 0.36.0 is prepared, publish the proposal, wait for both forges' review jobs (the GitLab
  pipeline as the child of one host ticket until its last guest job ends, host rule 6), land,
  publish `dev` and `main`, and read the protected jobs back; then retire the lane.
