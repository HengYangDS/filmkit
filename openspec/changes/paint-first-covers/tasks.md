# Tasks

## 1. Covers named before they are painted

- [ ] 1.1 Let a declaration name covers that do not exist yet, and make packaging refuse an edition whose cover is missing, naming its field; verify with tests that such a declaration loads and that packaging refuses with the field's name.
- [ ] 1.2 Make the cover check write a painting that has no tracked cover, report it as uncompared and fail; verify with a test of the cover report.
- [ ] 1.3 Describe a new film's order in the README (declare, narrate, stage, paint and track the covers, package) and record 0.1.1 in `CHANGELOG.md` and `VERSION`; verify that the Markdown format check passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Tag `v0.1.1` and publish it with its Release pages on both forges after the user confirms.
