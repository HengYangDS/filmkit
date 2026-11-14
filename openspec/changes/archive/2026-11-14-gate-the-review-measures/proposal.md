## Why

The three films this engine builds passed their latest review rounds without a finding and with forty-six notes between them. More than half of those notes are lines the reviewers measure with their own scripts and the engine either records without refusing or does not measure at all: a clarity figure computed on another frame set than the reviewers', a phrase that stops without a fall, glides above their pace, names too close on a row, one-frame differences between an edition's two masters, straight apostrophes in the timeline. Each such line costs a note in every round until a film repairs it by hand, and a film cannot know before a review that it holds.

A local gate is worth its agreement with the acceptance authority. This Change brings those lines into the engine as the reviewers measure them, calibrated on the delivered films, so that a film meets them before it renders and the next editions of the three films can close their notes against the engine's own records.

## What Changes

- **New command `produce check-sound`**: judges the assembled soundtrack before the picture follows it and refuses a segment or soundtrack under the declared clarity floor, a thought that ends abruptly or is cut while voiced, and a phrase that stops without a heard fall. It writes `sound-gates.json`, bound to the soundtrack and timeline it judged.
- A film may declare a thought-level tolerance as tight as 0.25 dB (was 0.5 dB), so that adjacent thoughts at opposite edges stand at most half a decibel apart.
- **BREAKING**: a segment's voice clarity is measured on the frames of the whole soundtrack's grid whose centres fall inside the segment, kept by the whole soundtrack's energy threshold, as the reviewers measure it. Recorded segment figures change; a segment that passed by the old cut may stand under its floor.
- Each thought's clarity is recorded as its median over the frame grid's sixteen phases with its spread, and a short thought is marked as such.
- **BREAKING**: a caption cue in the timeline holds its typeset text, with no display copy beside it, and verification refuses a cue with a straight apostrophe or quote. The segment's narration and aligned words stay as the script and the aligner wrote them, because the picture and the verification hold them equal to the script.
- The geometry check records neighbouring names that stand closer than 1.5 em on one row and gates them for a film that asks with `--gate-row-gaps`; the motion audit records each stretch of glides and flows over 450 px/s and gates those over the `picture.motion.pace_limit` a film declares. Both are the film's to switch on, because reviews of two of the three films accepted closer names and faster glides than the third's reviewers hold it to.
- **BREAKING**: the comparison of an edition's two masters tests one-frame transients and edge slivers against a declared bound.
- `film:compare` does not decode a rebuilt film that holds its published film's bytes, and says that such a film calibrates no floor.

Out of scope: a general table of film-declared picture limits, and declared sync exceptions; a rate measure by sound between thoughts; release publication, which the common base owns.

## Capabilities

### New Capabilities

- `sound-gates`: the lines an assembled soundtrack must hold before the picture follows it, and the thought-level tolerance a film may declare.

### Modified Capabilities

- `voice-clarity`: the segment rule follows the whole soundtrack's grid and threshold; thoughts are measured over the grid's phases.
- `caption-text`: a cue's text is its typeset display copy.
- `picture-gates`: the geometry check records, and on request gates, the gap between neighbouring names on a row.
- `picture-motion`: the motion audit records glides and flows above the pace line, and a film may declare the limit that gates them.
- `caption-equivalence`: the comparison tests one-frame transients and edge slivers.
- `film-package`: a rebuilt film that holds the published bytes is not decoded.
- `sample-film`: the sample film runs the sound gate in its build.

## Impact

- `src/filmkit/soundtrack`, `src/filmkit/review/clarity.py`, `src/filmkit/captions`, `src/filmkit/picture`, `src/filmkit/delivery/reproduction.py`, `src/filmkit/produce.py` and their tests; the sample film's build and the README.
- Films that adopt this release add `check-sound` to their sound stage and may be refused by a new gate on a picture or soundtrack that the previous release accepted. Their delivered films are unaffected until their next edition.
- The release is 0.22.0.
