# Tasks

## 1. Supply

- [x] 1.1 Declare and lock ETHOS 0.2.0-alpha.29 and uv 0.13.7; done when `mise install --locked` reports every tool installed and `mise run bootstrap` passes.
- [x] 1.2 Project the CI workflow for `jdx/mise-action` 5.2.6; done when `lane project --check` conforms.
- [x] 1.3 Keep the code to alpha.29's Ruff policy with `DOC102`; done when that rule reports no finding on `src` and `tests`.

## 2. Continuity gates

- [x] 2.1 Refuse seats and unnamed speech and record held pictures in `check-picture`; done when gate tests refuse a seat and a run of unnamed speech by name and list a held picture in a passing record.
- [x] 2.2 Carry a stroke's dash through the stand-in and judge a dashed outline joined to a mark on its own; done when tests show a dashed paint, a seat at a dashed place on a link's end, and no seat for a solid card joined the same way.
- [x] 2.3 Name a frame by its contents only through a name; done when seat tests list a seat for a frame holding only a pictogram and none for a frame holding a named card.

## 3. Caption echoes

- [x] 3.1 List whole and partial caption echoes in the sync audit, refuse the first and record the second, and retire the frame audit's `caption_echoes`; done when tests list a cue drawn in one label, a cue drawn in two labels at 100% and no two-word cue, and gate tests refuse and record them.

## 4. Case of a set of names

- [x] 4.1 Report and refuse `mixed_case`; done when tests report three cards in mixed case, a set's names apart in a frame, and none for a smaller qualifier, a wrapped name's second line, an acronym or Chinese names, and a gate test refuses it.

## 5. Deliverables

- [x] 5.1 Typeset the transcript's title and headings, the chapter titles and the release's prose tags; done when tests show the part title in the transcript and the player's transcript, the chapter title in every chapter carrier and the synopsis tag set with typographic marks, and a Chinese script unchanged.
- [x] 5.2 Tag the chapter track with the edition's language and refuse a finished film with a track in another; done when tests write `zho` into a chapter track, leave the film's size unchanged and refuse an `eng` chapter track in the Chinese edition.
- [x] 5.3 Read the player's prose and the release's prose in the concept check; done when tests refuse a counterexample in each and pass one that stands only in the player's script.

## 6. Calibration

- [x] 6.1 Run the new gates on the ETHOS v2 lane at `f08e93d`, the seat-fixed copy and the sample film; done when the gates list the round-4 findings on the lane and nothing the reviewers did not find, the sample film passes `check-picture` on timelines staged from its scripts, and the counts stand in the Changelog entry and the decisions they settle in design.
- [x] 6.2 Run the document and packaging changes on the current inputs of DDWG, ETHOS v2 and the essentials film, and the concept check on each; done when the strings that change and any refusal stand in the Changelog entry.

## 7. Documentation and release notes

- [x] 7.1 Document the gates and the deliverable rules in `README.md`; done when it names each new finding and the chapter track's language.
- [x] 7.2 Set `VERSION` and the README pin to 0.9.0 and add an `UNRELEASED` 0.9.0 entry to the Changelog; done when no tracked file outside the Changelog history names 0.8.1 as the current version and `mise run check` passes.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample.
- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: date the Changelog entry when the release is cut; `ethos land --release --tag v0.9.0`, the tag's publication and the source-only Release pages.
