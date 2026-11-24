## Context

See [proposal.md](proposal.md). The preview's gap names the section of 0.31.0 [S1]; the text before its `### Added` is two paragraphs, and the paradigm places every entry of a release under a category [S2]. The release tool that wrote the section from `Unreleased` counted its entries under `Added` and `Changed` and did not read the paragraphs before them [S3].

## Goals / Non-Goals

**Goals:**

- The section of 0.31.0 holds nothing outside its categories, and says what it said.

**Non-Goals:**

- Rewording any entry, or changing the paradigm or the release tool's rule (the tool is the films session's, outside this repository).

## Decisions

1. **The two paragraphs become the first entries of `### Changed`, word for word.**
   - **Rests on:** the gap [S1] and the paradigm [S2].
   - **Considered:** (a) two entries at the head of `### Changed`; (b) the summary under `### Changed` and the adoption order under a category of its own, such as `### Migration`; (c) dropping the summary, whose content each entry below states.
   - **Chosen because:** (a) keeps every word in the category that describes what changes for a film, and the adoption order still precedes the entries it names as "below". (b) adds a category that Keep a Changelog does not have. (c) loses the list of what 0.23 to 0.30 ask of a film that pins 0.22.3, which no other entry states.
   - **Applies to:** `CHANGELOG.md`, the section of 0.31.0.
   - **Reopened when:** the paradigm admits a release summary outside its categories.

## Risks / Trade-offs

- An entry of two long sentences reads as a paragraph in a list. → Its words are unchanged; the films' adoption reads it either way.

## Sources

- [S1] The proof preview of `87ebbd4`, 24 November 2026 10:13 CST: `fkg-prove-preview block gapped ['repository_paradigm_changelog:CHANGELOG.md']`, next "correct CHANGELOG.md: release_changelog_content_uncategorized:0.31.0".
- [S2] ETHOS 0.2.0-beta.11's changelog paradigm, as the gap reports it: a release's content outside a category is a gap.
- [S3] The release content step of the films session, `chore(release): prepare 0.31.0` (`dfa034b`): "0.31.0: section of 25 lines, 16 entries under ['Added', 'Changed']".
