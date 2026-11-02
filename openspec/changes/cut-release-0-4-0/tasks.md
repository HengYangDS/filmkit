# Tasks

## 1. Locks

- [x] 1.1 Refresh `package-lock.json` with `npm update --package-lock-only` and `uv.lock` with `uv lock --upgrade`; done when each lock holds the newest release its ranges admit, `undici` stays on the newest 7.x release, and OSV reports no advisory for any package either lock pins. On 2026-11-02 npm moved the seven packages the audit named, uv moved anyio to 4.16.0, `undici` 7.30.1 was the newest 7.x release, and OSV found no issue in the 127 npm and 54 uv packages.
- [x] 1.2 Build the sample film with `mise run sample:build` on the refreshed locks; done when `sample:verify` passes for both editions. On 2026-11-02 it passed for both editions on HyperFrames 0.9.3 and Chrome Headless Shell 152.0.7977.30, with 1,800 geometry frames each.

## 2. Release notes and version

- [ ] 2.1 Record the lock refresh under `Unreleased`, then date the notes as `[0.4.0] - 2026-11-02` with the `v0.3.0...v0.4.0` history link and open an empty `Unreleased`; done when every entry of the former `Unreleased` section stands unchanged under `[0.4.0]`.
- [ ] 2.2 Set `VERSION` to 0.4.0 and the README pin to `v0.4.0`; done when no tracked file outside the Changelog history names 0.3.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.4.0`, the tag's publication and the source-only Release pages.
