# Design

## Context

Three films were produced on 2026-11-05 with filmkit 0.9.0, and each gap of the proposal was closed by hand for them:

- `review.round prompts` reads `previous/review-<code>.json` for every round, so each film's first production review was written by a bridge that replaced the template's previous-review line.
- `review.round set-aside` requires the round's reviews to bind the films. A preview the owner watched but nobody reviewed was set aside by a second bridge that reused `move_aside` and bound the films to their copies in the owner's Documents folder.
- The reviewers state the clarity computation step by step in each film's prompt, and a reference tool reproduces their figures; the floors (18 dB Chinese, 17 dB English) stand only in the `voice_quality` dimension's prose.
- The frame audit's label trace (`TRACE`) records only scene texts of role `label` that hold a letter, so it sees neither the title signature (role `title`, in or out of a scene) nor the running head and other texts; the contrast of DDWG's dimmed list was found by a reviewer and a scan of that trace.
- Each film's production chain ran the cover check, the draft still scan, the concept check and the gate record by its own scripts, and lost render slots when one of them refused after an earlier step had passed.

No bridge closed the seventh gap: two low thumps that the ETHOS film's sixth review measured in its Chinese thought pauses (§8).

`review/round.py` and `review/measurement.py` (417 and 442 effective lines) were near the 500-effective-line code-size limit that ETHOS's paradigm gate counts per module, tests included: physical lines that hold a token, with comments, blank lines and Python's docstrings and other bare strings left out (`ethos.measure`).

## Goals / Non-Goals

**Goals:**

- Close each gap in the engine with the owners that already decide it, so that no film needs a bridge.
- Measure clarity exactly as the reviewers state it, and gate the title and resting contrast before a render.
- Keep every existing film's output bytes, except a soundtrack where a take's codec onset is released (§8); only the gate verdicts, the review and assembly records and the round tools change.

**Non-Goals:**

- A native 10 fps draft render: the films render their drafts with their own tooling.
- Contrast against a panel behind a text, or a pixel scan of a rendered film.
- Gating clarity: the floors inform the review, which owns the verdict on the voice.

## Decisions

### 1. One prompt field states the previous review or the first round

`{previous_review}` renders one sentence: with `--previous`, that the previous review is in its two files with its findings and that each repair is to be verified; without it, that this is the first production review and none exists before it. The wording is review procedure, not film content, so the engine owns it, as it owns the sentence `{scripts}` renders. A template that cites `{previous}` or `{findings}` gets them as before when `--previous` is given, and is refused without it before any prompt is written, since a first round has no values for them. Alternatives: a second, first-round template that each film declares (two templates to keep in step), or conditional template syntax, which `str.format` lacks. The sample film's template moves to `{previous_review}{scripts}`. `{clarity}` states the declared floors, so a film can cite them instead of repeating them in a dimension's prose.

`round.py` is split by ownership: `review/files.py` holds what every step reads (a round's directory, `present`, `cited`, `edition_review`), `review/prompts.py` the prompts and `review/set_aside.py` the set-aside; `round.py` keeps the command, the player-check binding and the records, and fell from 417 to 240 effective lines. The tests split the same way, and the round-review fixture moved to `tests/review/conftest.py`.

### 2. An unreviewed build is bound by its consumer's copies

A set-aside's manifest names the consumer that still needs the bytes it moves. For a reviewed round that is its review; for an unreviewed build it is the folder that holds copies of its films, such as a Documents preview, which `--consumer` names and which must hold both films of each edition byte-identical in `<dir>/<code>/`; the films' own folder holds no copy and is refused. The layout, the manifest's keys, the move and the readback are those of a reviewed round. The label is `round-<n>` or a `--label` of lowercase words; a reviewed set-aside keeps `--round`, since its reviews are found by it. `--language` limits a set-aside to one edition. `--without-picture` takes the editions whose picture stays, or all when it names none, which keeps the 0.9.0 flag's meaning: a re-rendered edition sets its picture aside, and an edition the next build does not re-render keeps it for its next package.

### 3. Clarity follows the stated method and records its floors

`review/clarity.py` implements the seven steps of the reviewers' method. FFmpeg decodes as the reviewers' command does (`-ac 1 -ar 16000 -f f32le`). The frames are a strided view of the samples, measured 4096 at a time, which bounds the memory a 25-minute soundtrack needs; the least-squares line is computed in closed form, which equals the solver's line to rounding. A segment's voice runs from its first word's start to its last word's end and is measured alone, with the 95th percentile of its own frames. A film declares `review.clarity_minimum_db = { zh = …, en = … }`, a floor for each edition between 0 and 60 dB; the measurement records each value to 0.01 dB beside its floor and judges it as recorded, so a reviewer can derive every verdict from the numbers shown. A value below its floor is recorded, not refused: the review owns the voice's score.

### 4. The measure agrees with the reviewers' tool

On the six current soundtracks of the three films, decoded once on 2026-11-05, the engine keeps the reference tool's frames and agrees with its medians, 17.35 to 19.64 dB, within 4e-15 dB (`build/evidence/close-production-gaps/clarity-comparison.json`). The unit tests compare the measure with a frame-by-frame transcription of the method on synthetic signals, not with these files.

### 5. The opening shows the declared title

The title is the one the edition's script declares, which the timeline carries. The frame audit writes a second trace, `TEXTS`, of every text of every frame with its scene, role, contrast, opacity and whole text; the label trace keeps its format for the sync audit and the films' tools. A frame before the first word shows the title when its texts at 3:1 or more, the legibility the sync audit reads, together repeat every title word, each text covering the words it repeats as one run, as the sync audit matches a caption cue with labels. So a title set in parts or on several lines counts, the author's name and a chip beside it do not matter, and a card whose wording departs from the declared title does not count, since its metadata and its card would then disagree. The gate requires such frames for at least 1 s. The six current editions show their titles for 2.40–4.00 s and the sample film, staged as its tests stage it, for 2.10 s; the ETHOS composition of `28a177a`, which dropped its title signature, shows none in either edition (`build/evidence/close-production-gaps/opening-titles.json`).

### 6. Text at rest is measured on the same trace

A text's contrast is the frame audit's reading load: WCAG relative luminance of its colour composited over the ground at its opacity, against the ground's. A text counts when it holds a letter or a digit and shows above 4% opacity, the frame audit's threshold for ink; a mark drawn as text, such as an arrow, is a graphic. Its instances in a frame are keyed by scene, role and whole text, and a frame counts as below 4.5:1 when any instance is. A run of such frames shorter than 0.7 s is a text entering or leaving the picture; a run of 0.7 s or more is at rest and refused. On the current compositions of the three films and the sample film's, no text of either edition rests below 4.5:1 and no fade runs as long. The DDWG composition before its legibility repair (`8a6b8f1^`, run on the current timelines with each cue the repaired text no longer says standing 0.5 s into its voice) holds 143 Chinese and 145 English runs: list items dimmed to 3.34, 3.62 and 4.23:1, refused names at 4.30:1, report-card values at 3.56:1 and the running head at 4.48:1, the levels its round-30 review measured (`build/evidence/close-production-gaps/text-gates.json`).

### 7. The pre-render check reuses each owner

`produce preflight` calls `require_current_stage`, the `player-check cover` tool on the current stage, `packaging.stale_bindings`, the draft record, `concepts.check` and `require_passing_gates`, and reports every finding together. `stale_bindings` is the comparison `resume_package` made inline; both now use it. An earlier package record is reported even when it binds every current input, because the render replaces the picture it binds and `package-film` would refuse it afterwards; the remedy is a set-aside. The cover is compared only on a current stage, since a stale stage paints another composition's cover. The check writes no record: the render's own gates stay its acceptance.

The draft record lives at `build/evidence/editions/<code>/draft-stills.json` beside the edition's other records. The still scan binds the composition as it stands when the scan runs, as the sync audit binds the composition its trace samples; a draft scanned as soon as it renders is bound to the composition it shows.

### 8. A take's codec onset after digital silence is released

The ETHOS film's round-6 Chinese soundtrack leaves digital silence on a step above −45 dBFS twice (`quiet_edges.left_with_a_step_above_minus_45_dbfs = 2`), each where a run-on retake (03.7, 08.9) follows a take that ends in digital silence. The retake opens with a codec transient from −31 to −39 dBFS (1 ms peak about −28 dBFS, 98–99 % of its energy below 500 Hz) that decays into its noise floor, about −84 dBFS, within 35–60 ms, and the join's native quiet follows. All 18 auditioned seeds of 03.7's text open with it, so a film cannot choose it away. Digital silence was treated only inside the native quiet, and here it lies before the transient.

At each complete-thought join, the sound between digital silence after the thought's last aligned word and the join's native quiet is released when it lasts at most 0.1 s. It holds no aligned word, since the native quiet lies in the join window and begins before the next thought's first word. The zeros then leave into the native quiet through the soft 10 ms fade that leaves digital silence inside a join, because a native quiet of up to PCM 260 still steps above −45 dBFS after the program gain. The two thumps sound 14.4 and 6.1 ms before the native quiet in the assembly's samples, and the onsets of the round-7 opening takes 10–60 ms before heard quiet, while a syllable lasts longer; 0.1 s covers them with margin, and a breath keeps its samples.

The same onset blocks a take that opens its recording, whose clip must begin in heard quiet at least 0.1 s before the first word. Only when no such quiet exists, the sound before the recording's first 10 ms heard as quiet is released if it lasts at most 0.1 s and ends by the first aligned word, and the clip begins in it; every clip the assembly already begins keeps its bytes. The audition judges each take by the same functions on its own alignment: `opens_quiet` keeps the raw first 10 ms, `onset_releasable` states the onset, and `clip_opens_quiet`, which a take opening its recording needs, whether the assembly would begin its clip in quiet. Each designed thought pause and each clip's boundary fades record `released_onset_samples`.

On the round-6 Chinese inputs the patched assembly changes exactly the joins 03.6>03.7 and 08.8>08.9, 693 and 293 samples released; the quiet edges then leave no digital silence above −45 dBFS, the runtime stays 900 s, the timeline is identical and every other sample is equal (`build/runtime/work/onset/comparison.txt`).

## Risks / Trade-offs

- [A title card that adds words to the declared title is refused] → The card and the release metadata should agree; the film corrects one of them.
- [Contrast is measured against the ground, not a panel] → A text on a lighter panel reads lower than measured; the reviewers' pixel scan of the rendered film stays the check for it.
- [The reading load assumes a text lighter than the ground] → Every film's ground is dark; a light ground would need the symmetric ratio.
- [The draft record binds the composition at scan time] → A composition edited between the draft's render and its scan is bound wrongly; the films render and scan in one step.
- [Existing films are refused by the new gates] → That is the intent; each adopts 0.10.0 with its next edition.
- [The aligner places words in 0.08 s steps] → A first word aligned at 0 s covers any opening onset, so its take stays refused by both the audition and the assembly; another seed is auditioned.
- [The audition judges a take alone, the assembly the take in its recording after the thought gain] → A first word aligned one step apart, or a frame moved across −55 dBFS, can judge a borderline opening differently; the assembly's refusal still names the segment.

## Migration Plan

A film adopts 0.10.0 with its next edition: its picture must pass the title and contrast gates before `render-picture` starts; its draft tooling scans with `still_scan --language`; its prompt template may move to `{previous_review}` and `{clarity}`; it may declare `review.clarity_minimum_db`; and it sets aside a watched preview with `set-aside --unreviewed --consumer`. A film whose takes hold a releasable onset assembles a different soundtrack with the same timeline and packages its films again. Rollback is the previous pin; nothing a film tracks changes.

## Open Questions

None.
