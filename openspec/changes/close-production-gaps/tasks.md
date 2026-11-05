# Tasks

## 1. Review rounds

- [x] 1.1 Split `review/round.py` by ownership into `review/files.py`, `review/prompts.py` and `review/set_aside.py`, keeping the command, the binding and the records in `round.py`; done when every module stays within the 500-line code-size limit and the moved tests pass unchanged apart from their module names.
- [x] 1.2 Write first-round prompts: `--previous` optional, `{previous_review}` citing the previous review or stating that none exists, `{previous}` and `{findings}` refused without a previous round, and `{previous_review}{scripts}` in the sample film's template; done when prompt tests write a first round, cite a previous round through the field, fill an old template with `--previous` and refuse it without.
- [x] 1.3 Set an unreviewed build aside with `--unreviewed --consumer` under `--round` or `--label`, and limit any set-aside with `--language` and `--without-picture [CODE ...]`; done when set-aside tests move a preview build bound by its consumer's copies, refuse a differing copy and a malformed label before moving anything, and move one edition without its picture through the command.

## 2. Voice clarity

- [x] 2.1 Measure the cepstral peak prominence of each soundtrack and each segment's voice in `review/clarity.py` and record it in `review.measurement`; done when tests on synthetic signals agree with the stated step-by-step method within 1e-9 dB, keep only the loud frames, and rank a clear voice above a breathy one.
- [x] 2.2 Declare `review.clarity_minimum_db`, record each value against its floor and state the floors in `{clarity}`; done when declaration tests refuse a missing edition, another edition and a 0 dB floor, a measurement test marks a segment below its floor, and the sample film declares 18 and 17 dB.
- [x] 2.3 Compare the measure with the reviewers' tool on the six current soundtracks of the three films, decoded once; done when every value agrees within 0.01 dB (design §4).

## 3. Opening title and resting contrast

- [x] 3.1 Trace every text of every frame in the frame audit (`TEXTS`); done when the frame-audit test reads six fields per row, the captions among them, and every row of the label trace.
- [x] 3.2 Measure the opening title and the runs of text below 4.5:1 in `picture/text_trace.py`, and refuse both in `check-picture`; done when measure tests show a title in parts and on two lines, an opening without it, a run at rest, a fade, a hidden text and a mark, and gate tests refuse each with its name.
- [x] 3.3 Run both measures on the current compositions of the three films and the ETHOS composition that lost its title; done when the counts stand in design §5 and §6 and the Changelog entry.

## 4. Pre-render check

- [x] 4.1 Bind the composition in the still scan's record and add `--language`, which writes `Edition.draft_stills`; done when still-scan tests read the three bindings and the edition's record.
- [x] 4.2 Add `produce preflight`, reusing the stage, cover, package, concept and gate owners, with `packaging.stale_bindings` shared by `resume_package`; done when preflight tests pass a current edition, name six stale inputs in one refusal, name a package of the current inputs, each kind of cover difference and a failing or missing draft scan.

## 5. Documentation and release notes

- [x] 5.1 Document the review-round options, the clarity floors and measure, the title and contrast gates, the text trace and the pre-render check in `README.md`; done when the README names each command, option and field.
- [x] 5.2 Set `VERSION` and the README pin to 0.10.0 and add a `[0.10.0] - UNRELEASED` entry to the Changelog; done when no tracked file outside the Changelog history names 0.9.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample.
- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: date the Changelog entry when the release is cut; `ethos land --release --tag v0.10.0`, the tag's publication and the source-only Release pages.
