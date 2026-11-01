# Proposal

## Why

A take that stops inside its last syllable can reach a finished film. Narration binds each thought's take from the cast's seed without judging its ending. The assembly then fades a take that is still heard where the silence after it begins over 60 ms, which hides the hard cut but still swallows the syllable. The review's measurement of delivered endings counts such a faded thought as ending naturally, and its check for a voice cut at full level looks 70–90 ms before the release. The `ethos-film` `v1.0.0` films were accepted and published with eighteen such thoughts, although the engine's own take measurement listed every one of them as abrupt.

## What Changes

- **BREAKING** The assembly refuses an edition when a bound thought take does not end naturally, unless the film declares a release for that thought's join. The refusal names every such thought. A film whose takes all end naturally assembles exactly as before.
- The review's measurement of delivered endings takes each thought's stop at the first digital silence after its last word begins, and judges a released thought where its release begins.
- A run-on take reads on into its following thought with a word space when the thought ends in Latin text without one, so an English thought that ends its segment can be read on and cut.

## Capabilities

### New Capabilities

- `narration-endings`: how a thought's spoken ending is kept whole from its take to the delivered soundtrack, and how the review measures it.

### Modified Capabilities

None.

## Impact

- `src/filmkit/soundtrack/assembly.py`, `src/filmkit/review/endings.py`, `src/filmkit/narration/run_on.py` and their tests; `CHANGELOG.md`.
- A film adopts this release only by narrating, assembling and accepting an edition on it. The DDWG films and the repaired `ethos-film` takes all end naturally, so their soundtracks do not change.
- Out of scope: choosing or synthesizing takes during narration, the take criterion itself, and the declared release policy.
