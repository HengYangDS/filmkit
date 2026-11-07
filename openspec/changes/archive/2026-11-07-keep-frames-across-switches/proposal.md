# Proposal

## Why

The committee's essentials review found that every press of the player's captions control and every version switch paints the cover, the title card, for about four to five frames, and likely drops the voice, because the page reloads its one video element (M8-01, minor, which holds acceptance of every film). It also found two typographic slips on the engine's page (M8-08). Three engine defects that film rounds met belong in the same release: a caption term declared with a capital never binds, since the captions compare lowercased words; the renderer's browser can draw no ink for a clockwise arc that sweeps a whole turn from a start that is not a whole number of turns, which the headless audits, drawing arcs as the HTML specification does, never see; and `compare-pictures` refused the ETHOS film's Chinese pictures at one keyframe whose encoder noise, spread thinly over the frame, measured 49.76 dB against the 50 dB floor calibrated on the sample film's sparse frames.

## What Changes

- **A switch keeps the picture.** A version or captions switch makes the chosen film ready beside the shown one and shows it only once it holds its frame at the time it takes over. A paused film is shown again at its time; a playing film plays on until the chosen one takes over at the time it has reached. No switch paints the cover or a bare frame.
- **The readback watches each switch.** The real-browser player check records every frame the page paints from each switch's click until the switch settles, and fails a switch that paints the cover or a frame of one flat colour, a paused switch that moves the time by 0.02 s or more, and a playing one that jumps back before the click or ahead of the time that passed.
- **Player typography.** A Chinese size that follows a closing full-width bracket follows it without a space, and the English message for a film the browser cannot play sets a typographic apostrophe.
- **Caption terms ignore case.** The English caption phrasing compares a declared term's words with a caption's words in lowercase, so a term declared with capitals stays on one line; the declaration and the concept check keep each term as written.
- **A gated finding for an arc that vanishes.** `check-picture` draws each distinct start and end of every stroked clockwise arc that sweeps a whole turn or more from a start that is not a whole number of turns once on a scratch canvas in the renderer's browser. It refuses a line whose arc paints no ink there from one of its starts and records every other, each finding naming the scene, the times, the start and the line of `picture/film.js` that drew it, and the remedy: `ellipse(x, y, r, r, start, 0, 2 * Math.PI)`.
- **A PSNR floor below keyframe noise.** The encoded-level comparison refuses a frame under 45 dB instead of 50 dB. The tile limit of 4 levels stays the structural guard, which a missing label exceeds in its tile; the floor still refuses a difference spread across the frame, such as a uniform shift of 2 levels at 42.1 dB.
- **Output bytes.** Every film's pictures, soundtrack, captions and films stay byte for byte unless its declaration capitalises a caption term or its composition strokes such an arc that the browser paints without ink; each edition's player page changes.
- **Out of scope.** Moving a film to this release or changing its composition, which each film does in its own lane; measuring the voice across a switch, since the readback reads the picture and the media times.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-package`: a switch keeps a frame of the film on the screen, the readback watches what each switch paints and how it keeps the time, and the player's words follow its edition's typography.
- `caption-text`: a declared caption term stays on one line whatever the case of its words.
- `picture-gates`: `check-picture` refuses a stroked clockwise whole turn that the renderer's browser paints without ink and records the others.
- `caption-equivalence`: the encoded pictures' PSNR floor is 45 dB.

## Impact

- **Code.** `delivery/player.py` and the page's script, which moves to `delivery/player-page.js`; `delivery/player-read.mjs`, `delivery/player-verdict.mjs`, `delivery/player-check.mjs` and a new `delivery/player-frames.mjs`; `captions/english.py`; `picture/equivalence.py`; `picture/headless-composition.mjs`, `picture/frame-audit.mjs`, `picture/frame-audit/report.mjs`, a new tool `picture/whole-turns.mjs`, `tools.py` and `picture/gates.py`.
- **Films.** A film adopts the release by packaging its metadata again and reading its delivery back; its films and records stay. A film whose English edition declares a caption term with capitals sees that term kept on one line, which can move its caption lines, and a composition whose whole turn the browser paints without ink is refused until it draws the ellipse. ethos-film's and ddwg-film's `ring()` stroke whole turns from starts Chrome 152 paints, which are recorded, and ddwg-essentials-film's draws the ellipse already. A comparison refused only at a PSNR between 45 and 50 dB passes when run again.
