# Tasks

## 1. Motion continuity

- [x] 1.1 Name each paint's origin by the innermost line of scene code on its call stack, a scene's body or a module in a folder below `scenes/`, else by the innermost line of the composition, with the module where the bundle names one. Done when headless-composition tests trace a paint drawn by a shared helper to the scene line that called it, in a scene's body and in a bundled scene module with its module, and a paint outside scene code to its innermost line.
- [x] 1.2 Follow every mark across frames in `picture/motion-audit/`, and report each frame's halts, starts, races and pops outside stage cuts with their origins, and each scene's largest glide and flow speeds, in the motion report. Done when motion-audit tests on synthetic compositions follow a flow's dot, a link growing on a gliding mark, a counter's changing words and a dot wrapping by size without a finding, and report a halt, a start, a race and a pop at their times and lines, and no pop in a stage cut.
- [x] 1.3 Declare `[[picture.motion.exceptions]]` in `film.py` and refuse the grouped motion findings in `check-picture`. Done when gate tests refuse each kind of finding by name, record a declared exception by line and by module and refuse a stale one, and declaration tests refuse an unknown kind and two exceptions of one finding.
- [x] 1.4 Run the gate on the three films' committed compositions and on the sample film. Done when the findings per film, edition and kind, the probe's false positives each resolves and the threshold rationale are recorded under `build/evidence/judge-films-as-viewers/motion/` and summarized in the Changelog entry.
- [x] 1.5 Document the motion gate in `README.md`. Done when the README names the four findings and their thresholds, the stage cut, the attribution, `[[picture.motion.exceptions]]` and the recorded speeds.

## 2. Review levels

- [x] 2.1 Declare `[review.levels]` in `film.py`, the levels `信`, `达` and `雅` with what each asks and the dimensions it holds. Done when declaration tests refuse a dimension in no level or in two, and a level that names an unknown dimension.
- [x] 2.2 Fill `{levels}` in `review.round prompts`, and refuse a template that does not cite `{levels}` and `{sentences}` for a film that declares levels. Done when prompt tests state each level with its dimensions under it, refuse the template without the fields and keep a film without levels unchanged.
- [x] 2.3 Accept a review level by level in `review/record.py`, from `review.round record` and the verifier, and carry the levels in the production record. Done when tests refuse a missing level, a failing level, a level passed with a dimension below the floor or a material finding, and a finding without its level, and record and verify a passing review.
- [x] 2.4 Document `[review.levels]`, `{levels}` and level acceptance in `README.md`. Done when the README's declaration table and review section name them.

## 3. Every sentence judged

- [x] 3.1 Derive each edition's sentences from its timeline in `review/sentences.py`, and write them from `review.round prompts` as `sentences-<code>.json`, named in `{sentences}`. Done when tests split a thought of two sentences in each language, keep a quotation whole and give each sentence its id and timeline times.
- [x] 3.2 Refuse, at `review.round record` and in the verifier, a review of a film with levels that misses a sentence, names an unknown one or names a finding it does not hold, and carry the verdicts in the production record. Done when tests refuse each case and record and verify a complete review.
- [x] 3.3 Document the sentences file and the verdicts in `README.md`. Done when the README's review section names `{sentences}` and the verdicts.

## 4. Motion in the review's measurements

- [ ] 4.1 Record each edition's motion in `review.measurement` from its picture gate record, in `review/motion.py`. Done when measurement tests record the counts, declared findings, speeds and findings of a current record and refuse a record or report bound to another composition or timeline.
- [ ] 4.2 Document the motion measurement in `README.md`. Done when the README's measurement passage names it.

## 5. The sample film and the release

- [x] 5.1 Declare `[review.levels]` for the sample film and cite `{levels}` and `{sentences}` in its prompt. Done when the sample's prompts state its three levels and the suites pass on its declaration.
- [ ] 5.2 Set `VERSION` and the README pin to 0.12.0 and add a `[0.12.0] - Unreleased` Changelog entry that states the motion gate applies to every film from this release. Done when every `mise run check` command and `openspec validate judge-films-as-viewers --strict` pass.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample.
- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: date the Changelog entry when the release is cut; `ethos land --release --tag v0.12.0`, the tag's publication and the source-only Release pages.
