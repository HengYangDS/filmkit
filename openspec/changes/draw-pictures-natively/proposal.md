## Why

The draft `faster-films-less-by-hand` measured on four whole editions that a native canvas draws a film's composition unchanged, with no frame of 216,000 under the floor of a rebuilt picture, in well under half the time of a capture through a headless browser. Its next action is to admit the native picture as a Change of its own. This Change is that first slice, decisions 1 and 2 of the draft: the engine's renders draw by `@napi-rs/canvas` with the host's text renderer, and no render starts a browser.

It is kept narrow on purpose. The derivation of the uncaptioned picture, its proofs, the qualification's comparison of a rendered pair, the fault scan, the repair, the packaging and the checks that paint a document in a browser stay as they are and must keep working on a native picture; the draft's later slices remove what a native picture no longer needs.

## What Changes

- **A picture and a draft are drawn by the engine's own Node module on a native canvas.** `render-picture`, `render-picture --uncaptioned --native`, `render-draft` and `qualify-renderer` run it on the stage; the composition, the stylesheet and the fonts are the film's own, unchanged. **BREAKING**: HyperFrames and GSAP leave the supply, and a film installs `@napi-rs/canvas` 1.1.1 in their place.
- **A picture is drawn in four spans of whole groups of frames and joined by stream copy**, a draft in one process. `FILMKIT_RENDER_SPANS` names another count for a measurement. **BREAKING**: `FILMKIT_RENDER_WORKERS` is gone.
- **A render receipt names the canvas that drew the picture**: the package, its version and the integrity npm recorded for it, the native library the render loaded by its SHA-256, the text renderer, the operating system, the spans, the frames and a digest of the drawn frames, in place of a capture, a worker count, a browser and a renderer version. The engine pins that library's bytes. **BREAKING**: a picture whose receipt names no canvas does not validate; a film that adopts this engine renders its pictures again.
- **Two draws of one stage state one digest of their drawn frames**, whatever their span counts. `qualify-renderer` refuses when the digests differ; its comparison of the two films stays.
- **A stage holds the picture's data as `film.json`** beside the document that inlines it, and copies no timeline engine. **BREAKING** for a film's `picture/index.html`: the lines that load GSAP and build its timeline go, with the clip attributes they read.
- **The stylesheet's faces have one reader**, for the audits' table and for the stage's record from which the renderer registers them. **BREAKING** for a stylesheet whose `@font-face` rule is in a form the canvas cannot be held to: it is refused by name.
- **A render that fails ends at once**, by its draw or by its encoder, and a draft record names what drew its draft.
- **A film's declared capture decides only how its uncaptioned picture is made.** No render reads it.

## Capabilities

### New Capabilities

- `native-picture`: a picture drawn by a native canvas from a film's composition: its text renderer, its encoding, its spans, its receipt and the digest of what was drawn.

### Modified Capabilities

- `build-time`: the render's worker count is removed; the spans of `native-picture` take its place.
- `film-engine`: the capture declaration no longer sets a render's flags.
- `caption-equivalence`: a picture is derived only from a captioned picture that the pinned canvas build drew.
- `render-preflight`: a draft is drawn in one process with the pictures' encoding, and its record names what drew it.
- `picture-gates`: the whole-turn gate asks the checks' browser, which paints the cover and not a film's frames.
- `sample-film`: the sample build qualifies the canvas build the engine pins, by the digest of the drawn frames and by the comparison that stood.

## Impact

- `src/filmkit/picture/rendering.py` (the stage, the render commands, validation), the new `renderer.py` (what draws) and `native-canvas.mjs`, the new `encoding.py`, `faces.py` and `errors.py`, `browser.py` (the checks' browser alone), `draft.py`, `still_scan.py`, `qualification.py`, `derivation.py`, `metrics.py`, `headless-composition.mjs` (the scope a composition runs in), `preflight.py`, `supply.py` and `tools.py`, their tests, the sample film's template and declaration, `package.json`, `package-lock.json` and `NOTICE`.
- The npm supply: `hyperframes`, `gsap` and the `undici` override out, `@napi-rs/canvas` 1.1.1 in; 102 packages leave the lock and 12 enter it, and no package of the lock runs an install script. The pinned browser, `puppeteer-core` and `@puppeteer/browsers` stay for the geometry check, the whole-turn gate, the cover and the player check.
- Each film: its `package.json` and lock, its picture template, and a new render of its pictures. A released edition keeps its tag's engine and its bytes.
- Out of scope: the derivation and its proofs, the qualification's pair comparison, the fault scan, the repair, the equivalence, the packaging, the player check, narration and soundtrack; of the geometry check everything but where it takes its frame (design, decision 13).

An independent review of 18 November 2026 found no high finding, 4 medium and 20 low; the design states what its repairs decided (decisions 6 and 9 to 12, Sources [S10]).

Owner: the engine's maintainer. Next action: run the sample build on the tree as the review's repairs left it, as one host ticket with the baseline repeated in it (task 5.1), then the six released editions' drafts (task 5.4). Read again: 2026-11-22.
