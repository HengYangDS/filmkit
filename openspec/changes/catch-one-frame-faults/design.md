## Context

`compare-pictures` (`src/filmkit/picture/equivalence.py`) proves at two levels that an edition's uncaptioned picture differs from its captioned one only by its captions. The composition level runs the composition headlessly at sampled instants. The encoded level decodes both rendered pictures at every half second and every caption's start, middle and end frame, and refuses a frame whose difference outside the caption band exceeds 4 levels on average over a tile or whose PSNR falls under 45 dB.

The producer's full-frame scans of 2026-11-09 and 2026-11-10 (evidence under `build/evidence/catch-one-frame-faults/`):

- Nine one-frame faults in seven of sixteen pictures. `faultbox.json` measures each: outside the caption rows, the samples more than 90 levels from the twin cover 2x2 to 28x15 px, peaking at 124 to 219 levels; the boxes do not keep to the encoder's 16-pixel grid. `sheet.png` shows each fault with the faulty picture's neighbouring frames and the twin: every one lies on a text glyph, as a rectangle inside the glyph's box that is lit where the glyph has no ink or dark where it has ink, and both neighbours equal the twin. That is the pattern of a glyph drawn from the wrong part of a glyph atlas, a rendering fault; a re-render from the same composition came out clean four times.
- Between clean twins the largest difference outside the caption rows is coding residue at the edges of marks: the faults' neighbouring frames peak at 0 to 55 levels, an independent reviewer of the ETHOS film's round 15 found at most 38 levels over its whole 54,000-frame Chinese pair averaged over 2x2 pixels, and at most 61 at full resolution in the 80 frames it examined there, and this change's scan of two delivered clean pairs at full resolution measured 78 levels over the English pair of that film (frame 52330) and 72 over the Chinese pair of the essentials film (36,000 frames, frame 28781), each at one or two samples on the edge of a glyph (`real/`).
- The prototypes `twinscan.py` (both pictures, rows 0 to 1720, a sample more than 90 levels apart) and `transcan.py` (one picture's caption rows, a sample more than 90 levels from both neighbours while they agree within 30) found every fault and nothing else: the latter finds frame 1998 of the faulty essentials picture with its exact box and nothing in its twin, and nothing in the caption rows of eight clean pictures (348,000 frames).

## Goals / Non-Goals

**Goals:** refuse a one-frame fault anywhere in either picture before packaging; name the picture to render again; keep the sampled measures, which catch a difference spread thinly over a frame.

**Non-Goals:** removing the fault's cause in the renderer (a HyperFrames or Chrome matter, recorded for a later change); repairing a frame without a render; scanning films already packaged.

## Decisions

### A per-sample threshold of 90 levels on every frame

The fault is one bright or dark fragment; averaged over a 64-pixel tile a 2x2 fragment falls below the tile limit, so the tile measure alone cannot be applied to every frame. A per-sample threshold is: 90 levels sits above the largest difference measured over two whole clean pairs, 78 levels, and below the weakest fault, 124 levels. Luma alone suffices, since every fault changes luma by at least 124 levels.

A one-frame difference that no one picture holds alone, where neither picture's frame departs from its own neighbouring frames, is refused only above a noise ceiling of 120 levels; the record keeps one within it as residue. Each of the nine render faults measured departs in one picture from its own neighbouring frames, which agree, by 124 to 219 levels, while outside the faults the largest difference that this change's scan found in four pairs was 93 levels, at one sample of a moving mark whose edge the DDWG film's two Chinese encodes of round 36 drew apart at frame 30306. 120 lies between them. A difference that one picture holds is still refused above 90 levels.

### FFmpeg reduces each frame before Python reads it

Decoding two UHD pictures and comparing them in NumPy would read 12 MB a frame. The comparison runs in one FFmpeg filter graph: both pictures to full-range grey, their absolute difference, a threshold at 90 and an area scale to 8-pixel cells, so Python reads one small plane a frame and records a frame with any lit cell, the box of its cells and its peak. The prototype ran 90,000 frame pairs in 9 min 35 s at nice 15.

### The caption band is scanned for one-frame changes in each picture

Inside the band the pictures differ by design, so the twin cannot judge it. A caption stands for seconds, so a glyph fault in it is a sample far from both neighbouring frames while they agree; a caption that appears or leaves changes once and passes, and a moving mark changes in every frame, so its neighbours disagree and it passes too. The scan reads the band's rows of each picture, a tenth of the frame, and keeps two frames in hand.

### The refusal names the picture to render again

A fault found by the twin comparison is in the picture whose frame departs from its own neighbours; the other picture's frame agrees with its neighbours. The record keeps, for each faulty frame, its time, box, peak and picture, and the refusal names the render command for that picture.

## Risks / Trade-offs

- [A legitimate one-frame flash in the caption band] → The picture gates already refuse a mark that pops for one frame; a film that needs one declares it there, and this scan would refuse it too, which is the intended strictness.
- [Longer builds] → About ten minutes per 25-minute edition; the alternative, a reviewer or viewer finding the fault, costs a review round.
- [Faults in both pictures at the same frame and place] → Never observed; two renders are independent, so the twin comparison and the per-picture band scan leave this case to a third render, which no build needs today.

## Migration Plan

Release as 0.19.0. A film adopts it before its next comparison; nothing it has packaged changes. Rollback pins 0.18.0.

## Open Questions

None.
