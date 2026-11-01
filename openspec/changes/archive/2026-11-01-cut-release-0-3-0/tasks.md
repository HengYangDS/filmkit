## 1. Release notes and version

- [x] 1.1 Date the `Unreleased` notes as `[0.3.0] - 2026-11-02` with the `v0.2.0...v0.3.0` history link, and open an empty `Unreleased`; done when every entry of the former `Unreleased` section stands unchanged under `[0.3.0]`. The cut moved the section whole and only added the heading and the link.
- [x] 1.2 Set `VERSION` to 0.3.0 and the README pin to `v0.3.0`; done when no tracked file outside the Changelog history names 0.2.0 as the current version and every `mise run check` command passes. Both pass, with 63 Node and 687 pytest tests.

## Workflow follow-up

- Resulting-HEAD proof, integration, official archive and exact lane retirement are native ETHOS and OpenSpec records.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.3.0`, the tag's publication and the source-only Release pages.
