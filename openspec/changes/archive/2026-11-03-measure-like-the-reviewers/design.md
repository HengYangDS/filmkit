# Design

## Context

The frame audit and the motion audit run the composition headlessly on a canvas stand-in (`src/filmkit/picture/headless-composition.mjs`). The stand-in measures text by an estimate: a CJK character as wide as its size, a capital 0.66 of it and any other character 0.54, rising and falling from its baseline in proportion to the size. A composition that measures a name to place or centre it (both films do, through `measure()`) is laid out headlessly with those widths, and every measure that reads a text's extent reads them too. In the browser the same composition measures the film's fonts: Noto Sans CJK SC and IBM Plex Sans in DDWG and ETHOS v2, declared as `@font-face` rules of `picture/film.css` whose files the film lists under `picture.fonts`.

The frame audit's balance measures come from the round-16 reviews of DDWG, which measured a 480×270 grey frame: a lit mark rises above grey 48 at its share of a 4 px cell, a thought's picture may stand 12% off two seconds in and 8% off 70% through, and a run of 2 s of speech more than 12% of the width or height off the content centre is gated. Since round 29 the reviews measure the full-size frame instead, and more strictly: the box of every pixel brighter than grey 60 in rows 120–919 and its horizontal offset from x 960, with a build-up over 90 px for 1.5 s or more and a settled composition over 50 px each a finding, unless it is a lone mark centred where it stands.

A headless balance with the films' own advance widths and the reviewers' box, written for the ETHOS v2 balance repair, reproduces the reviewers' full-size per-frame tables of that film's base draft with a median difference of 0.5 px (99th percentile 2–8 px) over 16,785 frames, and finds every run they reported.

## Goals / Non-Goals

**Goals:**

- Lay text out headlessly with the widths the browser uses, for every face a film declares.
- Measure balance as the current reviews do, and refuse a picture that fails it before it renders.
- Keep a film without declared faces, and every measure that does not read text widths, unchanged.

**Non-Goals:**

- Shaping, kerning or ink bounds: the stand-in sums the fonts' advance widths, as `measure()` reads them; the vertical metrics keep their estimate.
- New typography measures, or a change to the measures of 0.7.0 other than the widths they read.
- Moving the DDWG 1.2.0 repair off its engine hold.

## Decisions

### 1. Advance widths from the declared faces

`filmkit.picture.metrics` reads the `@font-face` rules of `picture/film.css` and, for each family whose source file is one of the film's `picture.fonts`, reads the font with fontTools (already a dependency) and records its units per em and the advance of every character its character map holds, in em. A face's most frequent advance is recorded once as its default and only the others are listed, so a full CJK font's ideographs cost one entry. The table is written as JSON with the SHA-256 of `picture/film.css` and of each font it read.

The stand-in reads the table when the audit's caller names it in `FILMKIT_TEXT_METRICS`. A text's width is the sum of its characters' advances in its font's family, plus the letter spacing for each character, as a canvas measures it; a family the table does not hold, and a character its face does not map, use the estimate. The text's horizontal bounds follow its width and alignment; its vertical bounds keep the estimate. Alternatives considered: parsing the fonts in Node would need a font parser in the audits' JavaScript, and measuring in a real browser for every frame would make the 1/30 s audit as slow as a render.

`check-picture` builds the table into its work folder before it runs the audits and binds the stylesheet's and the fonts' SHA-256 in the gate record, so a render refuses a record measured with other fonts. `python -m filmkit.tools` names the same table to the frame and motion audits when the caller has not named one, so a measurement from the command line lays text out as the gate does.

### 2. Balance as the reviewers measure it

In every frame it exercises, spoken or not, the frame audit takes the box of every paint that is lit at full size: its colour, mixed over the ground at its opacity, brighter than grey 60 by the BT.601 luma the reviewers' PIL measure uses. Texts count by their box, strokes by their path widened by half their width and fills by their path, within rows 120–919. The box's horizontal offset is its centre minus 960.

Two kinds of run are reported per scene, a scene being the timeline segment the frame falls in, so a run ends where the next scene begins or where nothing is lit:

- `off_centre_builds`: a run of 1.5 s or more in which the box stands more than 90 px off.
- `off_centre_settled`: a run of 2 s or more in which the box stands more than 50 px off while its left and right edges each stay within 4 px of where they were when the run began. A still state that the picture then grows from, the next frame's box of the same scene containing it and reaching further, is a build-up held while its next part is still to come, and is left out.

Each run carries its start, end and largest offset in px. A lone mark centred where it stands needs no exception, because it stands within the limits. `check-picture` refuses `off_centre_builds`. It records `off_centre_settled` without refusing it: whether a still state is a finished composition or a build-up waiting for a part that arrives in another way, docking to a bar for instance, only the stage's intent tells, and the measure cannot read it. On the ETHOS v2 repair the one recorded run is such a state, the index centred with its first name before it docks (English 52.3–54.4 s, −53 px). The round-16 measures stay: they also bound the picture's vertical offset and its cover, which the new measures do not.

### 3. The measures that rested on estimated widths

`uneven_pitch` and `touching_marks` were recorded and not refused because they read estimated Latin widths. They are run with exact widths on both films' compositions and against the reviews that judged their findings, and they are refused only if they then report no finding the reviewers rejected and nothing on the repaired compositions; otherwise they stay recorded, and the reason is written here.

At the gate's step of 1/30 s with exact widths, neither reports anything on the ETHOS v2 balance repair (`c431d1a`, and `1eb45ae` with its English close laid out again) or on DDWG `0f91419` and its fourth repair `5c394db`, in either edition. On DDWG `b53453e`, the composition the third DDWG re-check judged, `uneven_pitch` reports nothing and `touching_marks` reports three touches: 实质风险 at 1.2 px, whose ink stood 3.6 px from the tick on the draft, and "Cannot prove what" at 1.3 px, with 3–4 px of ground on the draft, both real; and "Material risk" at 0.6 px, whose ink stood about 7 px clear above a tick that met its em box, and which the repair lifted with its Chinese twin. The estimate had reported, on the same composition, an uneven pitch of the scene 14 rail names that no review flagged and two touches the draft showed clear, "Any of these" at 22 px and "Names no subject" at 5–7 px; exact widths report none of them.

No finding the reviewers rejected remains, so `check-picture` refuses both. Their vertical extents keep the estimate, so a name without descenders can measure closer to a mark below it than its ink stands, as "Material risk" did; a stage that fails on that account gives the name a few more pixels.

### 4. The sample film

The sample film passes `check-picture`, its build and its verification on every release. If its picture stands off centre by the new measures, its composition is laid out again for what is on screen.

## Risks / Trade-offs

- [A film whose picture passed 0.7.0 is refused by 0.8.0] → That is the intent: the reviews find these runs and score them below 95. A film adopts 0.8.0 when it next renders and repairs its picture before the render.
- [Exact widths move the measures that already read text extents] → The round-16 cover and offset runs read the same texts, so they change too: the English close of the ETHOS v2 balance repair has one thin run, 804.37–807.07 s at 2.4% of the band, that the estimate's wider names hid. The film repairs it before it adopts 0.8.0.
- [Advance sums differ from shaped text by kerning] → A label's width can differ by a few pixels; the reviewers' tables agree with the advance-sum balance to a median of 0.5 px, and the limits are 50 and 90 px.
- [A font the stylesheet declares but the film does not list] → The family keeps the estimate and the table names no digest for it; the composition check reports undeclared fonts elsewhere.
- [Reading a full CJK font for each check] → fontTools reads the character map and the horizontal metrics only, in about a second per face.

## Migration Plan

ETHOS v2 adopts 0.8.0 with its balance repair and renders on it. The DDWG essentials adopt it before their picture. DDWG 1.2.0 keeps 0.5.0 and its gates; its picture is measured with these tools from source. Rollback is the previous pin; nothing a film tracks changes.

## Open Questions

None.
