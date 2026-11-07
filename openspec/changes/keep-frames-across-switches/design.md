# Design

## Context

See proposal.md for why. The player page (`filmkit.delivery.player`) holds one `<video id="film">`, and its script switches films by setting `src` and calling `load()`; from `emptied` until the first frame at the kept time decodes, that element has no frame, so the browser paints its poster. The readback (`delivery/player-read.mjs`, judged by `delivery/player-verdict.mjs`) records the film, time and play state after each switch, not what the page painted during it. The English phrasing (`captions/english.py`) binds a declared term by comparing `term.split()` with words it has lowercased. The headless stand-in (`picture/headless-composition.mjs`) samples an arc along the sweep the HTML specification gives in double precision, while Chrome Headless Shell 152.0.7977.30 brings a clockwise `arc()` to its end angle in single precision.

## Goals / Non-Goals

**Goals:**

- No switch paints the cover or a flat frame, in Chrome from disk and over the engine's media server, with the time exact when paused and continuous when playing.
- The readback fails a page that paints either during a switch, so delivery refuses it for every film.
- A declared term binds whatever its case, and an arc the renderer may not paint is refused before a render.

**Non-Goals:**

- Measuring the voice across a switch: the readback reads the picture and the media times, and the voice is inferred from them.
- Measuring browsers other than the renderer's Chrome.

## Decisions

### The page hands over between two videos

A switch clones the shown video without its `id`, `poster` and sources, gives the clone the chosen film and the hidden metadata track, and places it after the shown video in the same grid cell, hidden (`visibility: hidden`) and transparent. It aims the clone at the shown film's time when paused, or that time plus a lead of 0.25 s of film when playing. Once the clone has seeked and holds a frame (`readyState` 2 or more), the page waits until a playing film reaches the aim, shows the clone, plays it if the film played, and two animation frames later moves the `id`, volume and mute to it and removes the old video. A miss, the shown film already past the aim, doubles the lead and aims again; a seek, pause or play of the shown film aims again; a second switch first completes a clone already shown or abandons one still hidden.

The clone is hidden, not stacked beneath: measured in Chrome Headless Shell 152, a later video in the cell painted over an earlier one whatever their `z-index`, black until its first frame and then the chosen film before its hand-over. A hidden video still seeks and shows its frame as soon as it is visible, and it stays out of the accessibility tree and the focus order, so the page's keyboard and screen-reader behaviour is the shown video's and the controls' as before; focus on the old video moves to the new one. Readiness is `seeked` with `readyState` 2, since `requestVideoFrameCallback` never fired for a paused seek there, and the two frames of overlap cover the compositor's change of layers.

Alternatives considered: holding the last frame on a canvas over the video keeps the poster out of sight but hides the native controls while it shows and still stops the film, picture and voice, for the reload; pausing the shown film until the chosen one is ready paints no cover but freezes a playing film for the load, which reached 0.6 s for a UHD film on a cold cache. Both keep one element; the hand-over keeps the voice playing until the chosen film plays at the same time, one frame apart.

The page's script moves from a Python string into `delivery/player-page.js`, which `player.py` inlines byte for byte, so the behaviour runs in Node tests against a stand-in document whose videos paint as the measured browser paints them, and the static checks read it as JavaScript.

### The readback watches the screen

Around each switch the readback runs a screencast of the page (`Page.startScreencast`) from before its click until the chosen film shows and a little after (`delivery/player-frames.mjs`). Each frame is sampled on a 64 × 36 grid over the video's box, less its bottom 15 %, where the native controls lie, and compared with the frame before the click, the last frame and the delivered cover: a frame within 8 levels of the cover and 3 levels nearer it than both references paints the cover, and a frame whose samples lie within 10 levels of their median colour, at 99.5 % or more, while neither reference does, is flat. On the essentials films the cover frames lay 0.9 to 1.1 levels from the cover and the film's frames 14 to 15, and the film's own frames held 93 to 98 % of their samples in the ground. A switch whose frames could not be read is a problem of its own, so a failed capture never passes. The thresholds favour the film: a frame that is the film's, however close to its title card or its ground, is nearer one of the references than to the cover, and a film that is flat at the switch is flat in a reference too.

The times follow the switch's state: a paused switch keeps the time within 0.02 s, one frame at 50 fps, since the page sets it exactly; a playing one shows, once settled, a time no earlier than 0.05 s before the time at the click and no later than that time plus the time that has passed and 0.05 s. The readback finds the shown film by its `id`, `film`, and waits until it shows the chosen film.

### Caption terms are compared as the captions' words are

`FIXED_TERMS` normalises each declared term's words with the function that normalises each caption word, lowercase without outer punctuation, so the comparison has one owner. The declaration and the concept check, which already matches English case-insensitively, keep the term as written.

### The stand-in records each clockwise whole turn that does not start at one

The stand-in records each `arc()` drawn clockwise through 2π or more, less 1e-5 rad, from a start that is not within 1e-6 rad of a whole number of turns, with the innermost line of `film.js` on the call stack, the `arc()` call, and its module. A stroke carries its path's records; the frame audit reports each by scene and line with its first and last time and start, as `vanishing_arcs`, and `check-picture` gates it with the remedy. Measured in Chrome Headless Shell 152 with Metal and with SwiftShader alike (`build/evidence/keep-frames-across-switches/arcs.json`): 64 of 4000 starts drew no ink for a whole turn and 13 of 1000 for every longer clockwise sweep, since Chrome then sets the end to the start plus a single-precision turn; 28 of 1000 for a sweep 1e-6 short and none 3e-6 short; none for starts at whole turns from −6 to 6, none anticlockwise and none for `ellipse()` from any start. The gate therefore leaves anticlockwise arcs and ellipses alone and names the ellipse from 0 as the remedy, which draws the same dashes from the same start.

## Risks / Trade-offs

- [Two decoders during a switch] → They overlap only until the hand-over; a UHD film's decoder is released when its video is removed.
- [A playing switch answers after the lead, 0.25 s of film, or longer after a cold seek] → The shown film plays on meanwhile; a miss doubles the lead rather than show the chosen film early.
- [Other browsers are not measured] → The hand-over uses only standard media events and keeps the shown film on the screen until the chosen one shows its frame, so a browser that is slow to paint the clone shows the shown film's frame, not the cover.
- [The screencast classifier was calibrated on one film] → Its thresholds compare each frame with the film's own frames around the switch, and a capture that fails is reported.
- [The arc gate refuses an arc a film may have drawn correctly by chance] → The remedy draws the same ring; none of the three films' current compositions strokes one, as their scan records.

## Migration Plan

A film adopts the release by locking it, running `package-metadata` for each edition and reading its delivery back. Its films, pictures, captions and soundtrack are unchanged unless its declaration capitalises a caption term or its composition strokes such an arc, which it repairs before its next render.
