# Tasks

## 1. Caption text

- [x] 1.1 Keep each closing quotation mark or bracket that follows a punctuation mark on its Chinese caption line; done when a phrasing test sets 。” at the end of a line and starts the next with its own words, a timing test gives a brief line that ends in 。” its early start, no line of the ETHOS v2 Chinese script begins with a closing mark, and the sample film's and DDWG's Chinese lines are unchanged.
- [x] 1.2 Set straight double quotes as typographic ones in the display copy; done when a timing test shows an opening and a closing quote by position, an apostrophe as a right single quote, and a display copy as long as its text.

## 2. Documentation and release notes

- [x] 2.1 Record the fix under `Unreleased`, then date the notes as `[0.8.1]` with the `v0.8.0...v0.8.1` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.8.1; done when no tracked file outside the Changelog history names 0.8.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.8.1`, the tag's publication and the source-only Release pages.
