# Proposal

## Why

Since 2026-11-03 the owner requires every review dimension of every film to reach 95. The independent typography reviews measure balance on full-size frames: the box of every pixel brighter than grey 60 in rows 120–919, and its horizontal offset from x 960. A build-up that stands more than 90 px off for 1.5 s or more is a finding, and so is a settled composition more than 50 px off. The frame audit measures balance on older terms, set by the round-16 reviews: a run of 2 s of speech in which the picture stands more than 12% of the frame's width (230 px) or height off the content centre. So `check-picture` passed the ETHOS v2 composition of `8f646e0`, and the four re-checks of its draft scored 87, 86, 83 and 88, mostly for build-ups that stood 90–300 px off for seconds: 15 runs over 90 px of 1.5 s or more in Chinese and 20 in English.

The headless audits also lay text out with an estimate: a CJK character as wide as its size, a capital 0.66 of it and any other character 0.54. On the English script of ETHOS v2, three-word phrases come out a median 18% wider in that estimate than in IBM Plex Sans, the Latin face of both films (10–29% between the 10th and 90th percentiles), mostly because a space is 0.236 em wide, not 0.54. A composition that centres a group by its measured width is laid out differently in the audits than in the browser. When the DDWG typography repair measured balance headlessly, its English scene 19 stood 59 px off there and 100 px off on the full-size draft. For the same reason 0.7.0 records `uneven_pitch` and `touching_marks` without refusing them.

Measured with the films' own font advances and the reviewers' box, the headless balance of the ETHOS v2 base differs from the reviewers' full-size tables by a median of 0.5 px (99th percentile 2–8 px), and it finds every one of their balance runs.

## What Changes

- The headless audits measure text with the film's own fonts. `check-picture` and the audit tools build the advance widths of every face that `picture/film.css` declares, from the fonts the film declares, and the stand-in canvas measures text with them. A family the film does not declare, and a character its face does not map, keep the estimate.
- The frame audit measures balance as the reviewers do: in every frame of a scene, spoken or not, the box of every paint brighter than grey 60 over the ground in rows 120–919. It reports per scene each run of 1.5 s or more that stands more than 90 px off x 960, and each settled state of 2 s or more, its box steady within 4 px, that stands more than 50 px off. `check-picture` refuses the build-ups and records the settled states, which only the stage's intent tells from a build-up held for its next part.
- With exact widths, `uneven_pitch` and `touching_marks` refuse too, if a calibration on both films and the reviews that judged their findings shows that they report no finding the reviewers rejected.
- The sample film passes the new measures.
- The engine renders with HyperFrames 0.9.9, the newest release, if it keeps the browser build and the `undici` pin of 0.9.8.
- Record the changes under `Unreleased`, date them as `[0.8.0]`, and set `VERSION` and the README pin to 0.8.0.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `picture-gates`: the audits measure text with the film's fonts, the frame audit measures balance as the reviewers do, and `check-picture` refuses its build-ups and every text-layout finding.

## Impact

The Change touches these files:

- a new `src/filmkit/picture/metrics.py`, `src/filmkit/picture/headless-composition.mjs`, the frame, motion and seat-mark audits that open the composition, `src/filmkit/picture/frame-audit/composition.mjs`, `src/filmkit/picture/frame-audit/report.mjs`, `src/filmkit/picture/frame-audit/typography/index.mjs`, `src/filmkit/picture/rules/balance.mjs`, `src/filmkit/picture/rules/ink.mjs`, `src/filmkit/picture/rendering.py`, `src/filmkit/picture/gates.py`, `src/filmkit/tools.py` and their tests;
- the sample film's composition, `examples/sample-film/picture/film.js`, if it stands off centre by the new measures;
- `package.json`, `package-lock.json`, `NOTICE` and the renderer pin in `src/filmkit/picture/rendering.py`, for HyperFrames 0.9.9;
- `README.md`, `CHANGELOG.md` and `VERSION`.

A film adopts 0.8.0 when it next renders; its composition must then pass the new balance measures before `render-picture` starts. ETHOS v2 adopts it with its balance repair, before its render; the DDWG essentials adopt it before their picture. The DDWG 1.2.0 repair keeps 0.5.0, the engine hold of its narration, and is measured with these tools from source. In the 0.x series this is a minor release.
