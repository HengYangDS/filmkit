# Design

## Context

See proposal.md for why. A film's composition (`picture/film.js`) draws each frame from the timeline that staging inlines into the renderer document (`filmkit.picture.rendering.picture_html`). In ethos-film and ddwg-essentials-film the caption painter is `picture/film/framing/captions.js`, in ddwg-film `caption(t)` in `picture/film.js`, and in the sample film `caption(t)`: each paints one text per cue, outside every scene, `(c.display_text ?? c.text)` typeset and trimmed, with the layout role `caption`, and holds a cue through a gap of at most 0.3 s to the next one. Each is the only reader of the timeline's captions, so a picture staged with `captions: []` is the same film without its captions.

Packaging muxes the one rendered picture into the renditions of `production.RENDITIONS`, and the engine-built player switches between them with a hidden metadata track that marks the transcript's current paragraph.

## Goals / Non-Goals

**Goals**

- Render each edition's picture without captions from exactly the inputs of the captioned one, and prove before packaging that the two differ only by the captions, at the composition and in the encoded pictures.
- Deliver four films per edition with the same soundtrack, chapters, metadata and cover, and let a viewer turn the captions off and on in the player without losing the time or playback.
- Keep every film's existing outputs and records valid: a 0.12.0 render, stage record, package or release must not have to be made again only because 0.13.0 names pictures.

**Non-Goals**

- Captions burned in at packaging or shown as browser text tracks: the pictures draw them.
- Gating caption style or placement: the picture gates own them.

## Decisions

### Each picture has its own places, named by `Edition.rendered`

`Edition.rendered(captions)` returns the stage, file and receipt of the captioned picture or of the uncaptioned one: `final-delivery-<code>-uhd[-uncaptioned]`, `<slug>-final-picture[-uncaptioned].mp4` and `render/receipt[-uncaptioned].json`. `picture_stage`, `picture` and `render_receipt` stay the captioned picture's, so every reader of them keeps its meaning. A rendition names its picture by `captions`, and packaging muxes `edition.rendered(rendition.captions).file`.

The CLI adds `--uncaptioned` to `stage-picture`, `render-picture` and `validate-picture` rather than parallel commands, and refuses it on every other action. Staging the uncaptioned picture derives the same document with `data["captions"] = []` after the timeline is read, so the document differs from the captioned one only in the inlined caption list; `require_current_stage` derives it again to compare. Rendering runs the same command with the other stage and output. The render needs the same passing gate record as the captioned picture: the frame and motion audits judged the composition and timeline, and the equivalence gate proves the uncaptioned picture is their picture less its captions.

Each stage record and receipt carries `picture`. A record without it reads as the captioned picture's, since its places already bind it there; the uncaptioned picture's records always carry it, and a receipt read for the other picture is refused.

### The composition-level gate compares paints, in order, less the caption paints

`picture/caption-equivalence.mjs` opens the composition twice in one process (`headless-composition.mjs`), on the timeline and on the timeline with no captions, and renders both at the same instants in the same order: every 0.5 s and every caption's start, middle and end, so order-dependent state evolves alike. Each frame's paints are compared as the stand-in hands them over: kind, scene, opacity, colour, line width, dash, scale, subpaths, points and text.

The captioned frame's paints are walked in order against the uncaptioned frame's. A paint equal to the next uncaptioned paint is matched; otherwise it may be set aside only as a caption paint: a text painted outside every scene whose letters and digits equal those of the display text of the cue that started last at the instant or of the next cue, which the frame's layout also names in the `caption` role. The cue that started last covers a painter that holds a cue through a gap and the next cue one that leads into it; letters and digits ignore the typesetting of quotes and the trimming the films apply. Any other paint, a changed paint or a paint only the uncaptioned frame holds is a finding. Matching an equal paint first is optimal: setting aside a paint that equals the next one could only shift the match to a later equal paint.

Alternatives considered: identifying captions by the layout role alone trusts a label the film chooses; by text alone, a non-caption text that repeats a cue would be removable. Requiring all three, outside scenes, the cue's text and the caption role, admits only the caption painter and keeps a film that paints anything else from its captions refused. The tool reports the band of rows the caption paints cover, which the encoded level excludes.

### The encoded-level gate measures agreement outside the caption band against the encoder's noise

`picture/equivalence.py` decodes both pictures in two FFmpeg processes side by side, as raw 4:2:0 frames of the sampled frames only: every 0.5 s by its remainder and every caption's start, middle and end frame, selected by an expression summed as a balanced tree because FFmpeg parses at most 100 terms in a row. The band from the composition is widened by 24 rows of the 1080-row frame on each side and out to 16-pixel blocks, where the encoder's blocks around a caption differ. Outside it, each frame's measures are the largest mean absolute difference over 64-pixel luma and 32-pixel chroma tiles, and the PSNR of all compared samples.

The limits come from the sample film, whose two pictures are rendered by HyperFrames with `h264_videotoolbox`: the encoder's noise reached 1.51 levels and 60.2 dB at worst, at text edges in the middle of the frame, not beside the band. A picture missing one muted note outside the captions reached 17.2 and 24.8 levels, and a Chinese picture one frame off 11.0 levels and 47.8 dB. A tile limit of 4 levels and a PSNR floor of 50 dB leave the noise a margin of 2.6 times and 10 dB and refuse the missing note in every frame that shows it. The English picture one frame off stays within both limits, at 3.7 levels and 52.2 dB, since its sampled frames barely move: the stage comparison, which derives the document with render offset 0, and the frame cadence of `validate-picture` refuse such an offset before the comparison. The measurements are in `build/evidence/offer-captions-on-and-off/encoded-calibration.json`.

The record binds the composition, timeline, engine version and both pictures' stage documents, files and receipts. `package-film` and the verifier require it current and passing. The composition level runs first; when it finds a difference the pictures are not decoded.

### The player switches films, and the track stays hidden

The page opens on the 1080p captioned film. Each version button names its two films (`data-captioned`, `data-uncaptioned`); the captions control is `<button id="captions" aria-pressed="true">字幕<span aria-hidden="true">：开</span></button>`. Its words change with the state, and its accessible name stays the word for captions beside the pressed state, so a screen reader does not hear "captions off, not pressed". Both controls call one switch that keeps the time and whether the film plays, the version switching the page already had. The metadata track stays hidden on every film: the pictures draw the captions, and a showing track would double them.

The readback turns the captions off on the paused viewing film, plays that film, switches to the UHD version with them off, plays it, and turns them on while the UHD film plays. Each switch must reach the other film from the same time, paused or playing as before, with the control pressed as the captions show; every film plays at its size and duration at three seek points.

### Earlier builds and releases keep working

A set-aside moves the build's own films: the captioned films always, the uncaptioned films and picture when they are in place, so a round reviewed on a 0.12.0 build is set aside by its two films. A release manifest names either every edition's four films and `uncaptioned_stage_sha256`, or, published before 0.13.0, only the captioned films; the comparison then lists the rebuilt uncaptioned films as unpublished, and compares the rest.

## Risks / Trade-offs

- **The real films' encoder noise is not measured here.** The limits were calibrated on the 60-s sample; a full film's denser frames could show more noise. compare-pictures records each frame's measures, so the first full run of each film shows its margin; a limit change is an engine release.
- **Rendering time doubles.** Each edition renders a second UHD picture, about 30 minutes for a 25-minute film under load, and verification decodes four films.
- **Size.** Each edition adds a UHD and a 1080p film, about the size of the captioned ones.
