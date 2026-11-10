## Why

Renders occasionally hold a one-frame fault, and `compare-pictures` lets it through. On 2026-11-09 and 2026-11-10, sixteen pictures rendered with filmkit 0.18.0 (HyperFrames 0.9.9 with fast capture) for the DDWG, essentials and ETHOS films were compared with their twins over every frame: seven held a fault, nine faults in all. Each one is a rectangular fragment of one text glyph, 2 to 28 px wide, lit where the glyph has no ink or dark where it has ink, for exactly one frame, and it is in only one of the two pictures rendered from the same composition; its frame differs from the twin by 124 to 219 luma levels, while over two whole clean pairs no frame differs from its twin by more than 78 levels. `compare-pictures` decodes the pictures at every half second and every caption's start, middle and end frame, about one frame in twenty-two, so it passed all nine, and four of them reached a delivered film (the DDWG film's round 36). A fault inside the caption band, where the two pictures differ by design, is not compared at all.

## What Changes

- `compare-pictures` compares every frame of the two pictures outside the caption band and refuses a frame where any luma sample differs by more than 90 levels, or, for a one-frame difference that no one picture holds alone, as where two encodes draw a moving edge apart, by more than 120. The sampled tile and PSNR measures stay as they are.
- `compare-pictures` scans each picture's caption band for one-frame changes and refuses a frame where a luma sample differs by more than 90 levels from both neighbouring frames while those two agree within 30.
- A refusal names each faulty frame, the box it covers and the picture that holds it, the picture whose frame departs from its own neighbours, so only that picture is rendered again; the record lists them.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption-equivalence`: the encoded comparison covers every frame, the caption band is scanned for one-frame changes, and a refusal names the picture to render again.

## Impact

`src/filmkit/picture/equivalence.py` and a new module beside it for the full-frame scans, their tests, the README's paragraph on `compare-pictures` and the release notes. The comparison takes longer: the producer's prototype compared 90,000 frames of two UHD pictures in 9 min 35 s and scanned the caption band of 54,000 frames in about 3 min on an M5 Max. No rendered byte changes; a film adopts the release before its next comparison, and a picture it refuses is rendered again. The faults' cause, which the evidence places in rendering rather than encoding, stays outside this change.
