## Why

The release proof's preview of 0.31.0 on the lane's head `87ebbd4` stopped on 24 November 2026 with the gap `repository_paradigm_changelog` and the next step "correct CHANGELOG.md: release_changelog_content_uncategorized:0.31.0" [S1]. The section of 0.31.0 opened with two paragraphs before its first category: the release's summary and the order in which a film adopts it. ETHOS's paradigm for a changelog holds every entry of a release under one of its categories [S2].

The Change that wrote those paragraphs, `treat-languages-as-equals`, is archived on this lane, and an archive with a commit after it cannot be returned, so the repair is a Change of its own.

## What Changes

- The two paragraphs become the first two entries of the section's `### Changed`, each word as it stood.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement speaks of where a release note stands in the Changelog, and no behaviour changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`CHANGELOG.md` only. No engine behaviour, gate, record or byte of a film changes. Out of scope: the paradigm's rule, which is ETHOS's. `tasks.md` is the sole progress ledger.
