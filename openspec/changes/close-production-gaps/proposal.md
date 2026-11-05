# Proposal

## Why

Producing three films on 2026-11-05/06 exposed seven gaps that the engine left to bridges or to the owner's eye:

- A film's first production review gets no prompts: `review.round prompts` requires a previous review.
- `review.round set-aside` refuses a build nobody reviewed, yet `package-film` refuses to extend a package bound to changed inputs, so a preview the owner watched blocks the next packaging.
- Voice clarity, the cepstral peak prominence the reviewers compute by a stated method, has no native measure, and its floors live only in prose.
- A composition refactor dropped the ETHOS title signature from the opening, and no gate noticed.
- Dimmed DDWG text rested below 4.5:1 against the ground, which only a review found.
- Before a render nothing checks the inputs that later steps refuse: the cover, an earlier package, the draft scan, the concepts and the gate record.
- Codec onsets after digital silence thump in two ETHOS thought pauses and block takes that open a recording.

## What Changes

- `review.round prompts` takes `--previous` as optional. A template's `{previous_review}` cites the previous review and its findings, or states that no earlier production review exists; templates citing `{previous}` and `{findings}` keep working with `--previous`. `{clarity}` states the declared clarity floors.
- `review.round set-aside --unreviewed --consumer <dir>` sets an unreviewed build aside like a reviewed one, bound by the consumer's byte-identical copies of its films and labelled `round-<n>` or by `--label`. `--language` limits it to one edition, and `--without-picture` names the editions whose picture stays.
- `review.measurement` records each edition's clarity over its soundtrack and each segment's voice, by the reviewers' method, against floors a film declares in `review.clarity_minimum_db`.
- `check-picture` refuses an opening that shows the declared title for less than 1 s before the first word, and each run of 0.7 s or more in which a text stands below 4.5:1 against the ground, from a new trace of every text.
- `produce preflight` reports every stale or missing input of a render at once and refuses while one remains. The draft still scan binds the composition, and `--language` writes the edition's draft record.
- The assembly releases a take's codec onset to digital silence: at a thought join, sound of at most 0.1 s between digital silence and the join's native quiet; where a recording heard from its first sample begins its clip, sound of at most 0.1 s before its first heard quiet and first word. Each join and each clip records the samples released. The audition proposes a take that opens its recording when the assembly would begin its clip in quiet.
- `VERSION` 0.10.0 and an `UNRELEASED` Changelog entry.

Out of scope: pixel scans of rendered films, contrast against panels, a native draft render, and repairs of any film.

## Capabilities

### New Capabilities

- `review-rounds`: first-round prompts, and setting an unreviewed build aside.
- `voice-clarity`: the clarity measure and its declared floors.
- `render-preflight`: the pre-render check and the draft scan's bindings.

### Modified Capabilities

- `picture-gates`: the opening title and the contrast of text at rest.
- `narration-endings`: a take's codec onset after digital silence, at a thought join and where a recording's clip begins.

## Impact

- `src/filmkit/review/` (`round.py` split into `files.py`, `prompts.py` and `set_aside.py`; new `clarity.py`), `preflight.py`, `delivery/packaging.py`, `picture/` (new `text_trace.py`, the gate, the still scan, the frame audit) and their tests.
- `src/filmkit/soundtrack/` (`pauses.py`, `assembly.py`), `narration/take_edges.py`, `narration/audition.py` and their tests. A soundtrack changes only where an onset is released; every assembly record gains the released onset samples, and timelines stay as they were.
- The sample film's declaration and prompt; `README.md`, `CHANGELOG.md`, `VERSION`.

**BREAKING** for a film whose opening lacks its title or whose text rests below 4.5:1: `check-picture` refuses it before its next render. A film's draft tooling moves to `still_scan --language`. In the 0.x series this is a minor release.
