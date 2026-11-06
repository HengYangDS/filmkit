# Tasks

## 1. Wrapped labels

- [ ] 1.1 Group each frame's layout records into wrapped labels and judge them at rest by the declared rules in `picture/frame-audit/typography/`. Done when typography tests refuse an English line ending on a lead word, a one-word last line in a three-word name, a short block line and a short last line among lines of one size, and a Chinese line opening on closing punctuation, and spare a name over its smaller gloss, a label below 0.9 opacity and a repeated name standing in two places.
- [ ] 1.2 Declare `[picture.wrapping]` (`line_share`, `last_share`, `lead_words`, `exceptions`) in `film.py` and gate wrapping findings in `check-picture`. Done when declaration tests refuse a share outside (0, 1], an exception without a reason and a stale exception, and gate tests record a declared exception and refuse an undeclared break by name.
- [ ] 1.3 Compare the audit's lines with a real-browser readback of every wrapped label on the current builds of the three films. Done when both readings give the same lines for every label, recorded under `build/evidence/acceptance/`.

## 2. Narration flow

- [ ] 2.1 Measure the heard pause at every word boundary, with its marks and script switch, in a new `narration/flow.py`, and record it in `review.measurement`. Done when tests on synthetic speech measure a 490 ms pause at a switch, a comma pause and no pause inside a word, and map hyphenated and apostrophised words to their marks.
- [ ] 2.2 Refuse an unmarked pause above its limit at selection and assembly, with `[narration.flow]` limits and exceptions in `film.py`, and rank candidates by it in the audition. Done when tests refuse a 0.49 s switch pause, pass a 0.36 s unmarked clause pause under the default limits, record a declared exception, refuse a stale one, and propose the fluent take of two.
- [ ] 2.3 Record rate, pitch and level steps between adjacent thoughts of a part in the measurement, and list the largest steps and the unmarked pauses from 0.15 s to their limits in the listening plan. Done when tests on synthetic thoughts measure a doubled rate, a 3-semitone step and a 2 dB step, and the plan lists them.

## 3. Term pronunciation

- [ ] 3.1 Declare `latin_terms` (term, IPA, reference occurrence per edition) in the pronunciation contract, and measure each occurrence's first-vowel formants in `narration/readings.py` or a module it calls. Done when tests on synthetic vowels separate /iː/ from /ɛ/ and refuse a stale reference.
- [ ] 3.2 Refuse an occurrence outside the reference's bounds at selection and on the soundtrack, and in the audition prefer a take whose occurrences pass. Done when tests refuse an /ɛ/ occurrence against an /iː/ reference by name and propose the passing take.

## 4. Review rounds

- [ ] 4.1 Require `--dispositions` for prompts with a previous round, and state the dispositions under `{dispositions}`. Done when prompt tests refuse a missing finding, an unknown finding and a disposition without evidence or reason, and write the three groups.
- [ ] 4.2 Refuse `assemble` and `refresh-captions` over films a review round's prompts bind until that round is set aside. Done when tests refuse assembly over a bound round by name and command, and proceed after its set-aside.

## 5. Acceptance, documentation and release notes

- [ ] 5.1 Run the wrapping, flow and term checks on the current builds of DDWG round 33, ETHOS round 8 and essentials round 4. Done when they flag EN33-1's English breaks, R33-zh-2's Chinese blocks, the 0.49 s ETHOS pause and the five ETHOS English vowels, with the counts recorded under `build/evidence/acceptance/` and in the Changelog entry.
- [ ] 5.2 Document the declarations, measures and refusals in `README.md`. Done when the README names `[picture.wrapping]`, `[narration.flow]`, `latin_terms`, `--dispositions` and the set-aside guard.
- [ ] 5.3 Set `VERSION` and the README pin to 0.11.0 and add a `[0.11.0] - UNRELEASED` Changelog entry. Done when no tracked file outside the Changelog history names 0.10.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample.
- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: date the Changelog entry when the release is cut; `ethos land --release --tag v0.11.0`, the tag's publication and the source-only Release pages.
