## 1. Supply

- [x] 1.1 Take `hyperframes`, `gsap` and the `undici` override out of `package.json`, pin `@napi-rs/canvas` 1.1.1 exactly, resolve the lock without installing or running a script, audit it and compare it with the base's; done when the audit reports no advisory and the comparison lists what entered and left. Evidence: `supply.log` and `supply-lockdiff.txt` of the slice's records (design, [S6]).
- [x] 1.2 Name the canvas package and its binary package in `NOTICE` with what each states and ships of a license, and remove HyperFrames, GSAP and undici from it; done when `NOTICE` names the four packages `package.json` declares and says only what was read in the installed packages. Evidence: `node_modules/@napi-rs/canvas/LICENSE`, the binary package's manifest and its bill of materials (design, [S6] [S10]).

## 2. Renderer

- [x] 2.1 Add the engine's Node module that draws a stage on the native canvas and encodes it, in one process or in spans joined by stream copy, with its report; done when its Node tests pass, among them one process and three spans stating one digest and writing the same keyframes. Evidence: `tests/picture/native-canvas.test.mjs`.
- [x] 2.2 Run that module from `render-picture`, `render-draft` and `qualify-renderer`, stage the picture's data as `film.json`, drop the timeline engine from a stage, and record the canvas, the operating system, the spans, the frames and the drawn digest in each receipt; done when the picture tests pass. Evidence: `tests/picture/test_rendering.py`, `test_renderer.py`, `test_draft.py`, `test_native_render.py`.
- [x] 2.3 Refuse at validation a picture whose receipt names another renderer, and derive only from a captioned picture that the pinned canvas build drew; done when both refusals are tested. Evidence: `tests/picture/test_rendering.py`, `test_uncaptioned_way.py`.
- [x] 2.4 Have `qualify-renderer` refuse two renders whose drawn digests differ and record the canvas that ran; done when its tests pass. Evidence: `tests/picture/test_qualification.py`.
- [x] 2.5 Keep the end of a render as it stands: a real render asked to end leaves no span process, no encoder and no picture; done when the test of real processes passes. Evidence: `tests/picture/test_native_render.py` (the real render); `test_real_renders.py` and `test_renderer_end.py` hold the run of a renderer with stand-ins.
- [x] 2.6 Read the stylesheet's faces with one reader and hand them to the renderer in the stage's record, with the language; done when a rule in another form is refused by name and a stage that names no faces is not drawn. Evidence: `tests/picture/test_faces.py`, `native-canvas.test.mjs`.
- [x] 2.7 Name in each receipt the native library the render loaded, pin its SHA-256, and keep the loader's variable from a render; done when another library is named as itself and derives nothing. Evidence: `tests/picture/test_renderer.py`, `test_uncaptioned_way.py`, `test_native_render.py`.
- [x] 2.8 End a render whose draw fails or whose encoder stops short, keep the spans' folder to spans, state the encoded colour on each frame and pass no line about the input's size; done when each has a test that failed before. Evidence: `native-canvas.test.mjs`, `tests/picture/test_native_render.py`.
- [x] 2.9 Name in a draft record what drew the draft and refuse a record of another renderer's draft in `preflight`; hold a rendered picture to the keyframe grid at validation; done when both refusals are tested. Evidence: `tests/picture/test_draft.py`, `test_renderer.py`.
- [x] 2.10 Draw the qualification's second render in another count of spans and record whether the pinned build ran; done when its tests pass. Evidence: `tests/picture/test_qualification.py`.

## 3. Sample film

- [x] 3.1 Remove the GSAP script and timeline from the sample's picture template and say in its declaration what the capture now decides; done when the picture tests and the template's substitutions pass. Evidence: `tests/picture/test_rendering.py`.

## 4. Checks

- [ ] 4.1 Run every command of `mise run check` as light work with warnings as errors on the slice's head; done when each passes and the suite measures light by both of the host's measures.

## 5. Acceptance on a whole build

- [ ] 5.1 Build the sample film on this slice as one host ticket and compare its films with the last build by the browser at every frame; done when `mise run sample:build` passes, the comparison states frame counts, identical frames and the lowest PSNR of each film, and the build's seconds stand beside the host's load and memory at its start and end.
- [ ] 5.4 Draw the six released editions' drafts natively and read their still scans run by run against the limit; done when each edition's longest fine run of speech and every run within 0.5 s of the limit stand in a record with what was looked at in the frames, before a film adopts this engine (design, Risks).
- [ ] 5.2 Show the owner the lowest frames of that comparison before the slice is released; done when the owner has answered.
- [ ] 5.3 Promote the slice's records to `build/evidence/draw-pictures-natively/` of the canonical checkout; done when every record the design's Sources name stands there.

## 6. Documents

- [ ] 6.1 State in the README what a film now provides (the canvas package, the template without a timeline engine, `FILMKIT_RENDER_SPANS`) and record the change in the Changelog; done when the Markdown check passes on both.
