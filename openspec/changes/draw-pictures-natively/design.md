## Context

The engine at `27e1027` renders a picture by staging a document and running HyperFrames on it in a headless browser. The draft `faster-films-less-by-hand` measured a native canvas on four whole editions and decided, in its decisions 1 and 2, that a picture is drawn by `@napi-rs/canvas` with the host's text renderer. [S1] This Change builds that, and decides what the draft left to its first slice: the encode, the spans, how a render ends, what a second render must equal, where the renderer reads its picture, and what a receipt names. A mark such as [S3] names an entry under Sources.

What the engine expects of a rendered picture, read in its sources [S2]:

- `validate-picture` asks `media.require_video` for every frame of the film at the film's frame rate, the picture's frame, a stream and a container duration within a microsecond of the film's, and no B-frame, and `media.video_cadence` for every packet on the frame rate's grid.
- The derived uncaptioned picture is encoded by x264 at preset `veryfast` and rate factor 12, with a keyframe at every 2 s, none at a scene cut, no B-frame and 4:2:0 chroma (`derivation.ENCODER`).
- The UHD films copy their picture's video stream, so the picture's encoding is the delivered film's; the 1080p films are encoded again on a declared 2 s keyframe grid (`production.Rendition`, `packaging.keyed_as_declared`).
- The delivered films must carry BT.709 primaries, transfer and matrix (`delivery/verification.py`).
- The geometry check and the cover load the staged document in the supplied browser and wait for its `__filmReady`; no source reads the timeline that the document builds for HyperFrames.
- A renderer leads a session of its own, its wait stands inside `child_processes.terminable`, and its process group is ended after every run.

## Goals / Non-Goals

**Goals:**

- Every render of the engine draws on the native canvas: the two pictures, the draft and the qualification's second render.
- A native picture passes every check the engine runs on a picture today, with the smallest change to the modules this slice does not own.
- A receipt that states what drew the picture, read when it runs.

**Non-Goals:**

- Removing the derivation, its proofs, the fault scan, the repair or the qualification's comparison. They are the draft's decision 3 and a later slice.
- Removing the browser from the supply. The geometry check, the whole-turn gate, the cover and the player check run it.
- A new look. The slice is accepted against the last build by the browser, and the owner sees the lowest frames first (tasks 5.1 and 5.2).

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **A rendered picture is encoded as the derived picture is: x264, `veryfast`, rate factor 12, a keyframe at every 2 s.**
   - **Rests on:** the engine's contract of a picture, above; spikes N1 and N2, whose 216,000 frames were compared with the releases from encodes at these settings.
   - **Considered:** (a) HyperFrames' own encoding of a captioned picture, rate factor 14, whose keyframe spacing the engine never declared; (b) the derived picture's settings, which the engine already validates and delivers for every uncaptioned UHD film; (c) the host's hardware encoder, faster and, by the films' records of 13 November 2026, off the keyframe grid under load. Those records were not read again for this slice.
   - **Chosen because:** (b). Both pictures of an edition are then encoded alike on one grid, and the measurements the decision rests on were made at these settings. The encoding has one definition, `picture/encoding.py`, which the derivation takes and the renderer's command hands to the Node module as its options; the module holds no setting of its own, and a test holds every option.
   - **Applies to:** every render: the pictures, the draft, and the qualification's second render. The frames go to FFmpeg as raw RGBA and are converted to 4:2:0 in limited range by a filter chain that states BT.709 as the matrix, the primaries and the transfer on each frame: FFmpeg 9.0.2 takes the primaries and the transfer from no output option once a filter has made the frames, and a picture encoded with those options alone stated neither [S10]. Validation holds a rendered picture to the keyframe grid, as it holds a derived one.
   - **Reopened when:** the encoder bounds a build's time on a whole film, a delivered UHD film's size matters, or a film's lowest frame against its release falls under the floor of a rebuilt picture because of the encode.
   - **Sources:** [S1] [S2] [S4].
2. **A picture is drawn in four spans of whole groups of frames and joined by stream copy; a draft in one process.**
   - **Rests on:** N2, which drew three whole editions in four spans (36,000 frames in 139 s, 54,000 in 205 s, 90,000 in 350 s); N1, which drew 36,000 frames in 341.9 s in one process and in 135.5 s in eight spans, under another load than N2's.
   - **Considered:** (a) one process; (b) four spans, a named constant; (c) eight spans, which N1 did not show to be faster than N2's four, the two not having run back to back; (d) a count derived from the host's cores.
   - **Chosen because:** (b), the count measured on the most whole films. Each span's encoder runs two threads, as N2's did. `FILMKIT_RENDER_SPANS` names another count for a measurement, as `FILMKIT_RENDER_WORKERS` did for workers, and the count changes no frame (decision 4). A draft, a sixth of the frames at a quarter of the frame, is drawn in one process at a lower priority so that it yields to other work.
   - **Applies to:** `picture/renderer.py` (`SPANS`, `DRAFT_SPANS`) and `picture/native-canvas.mjs`, which divides the film, starts one process of itself for each span and joins them. A film shorter than its spans is drawn in as many spans as it has groups.
   - **Reopened when:** another count is faster on a whole film with the baseline repeated in the same ticket.
   - **Sources:** [S1] [S4].
3. **A render ends as a renderer ends today: the engine ends the renderer's process group, and the renderer handles no signal.**
   - **Rests on:** `child_processes`: a held child, `terminable` round the wait, a stop of the group after every run; the requirement "No narration process and no renderer outlives its command", which this Change leaves as it is; a test of real processes in which a render in two spans is asked to end and leaves no span and no encoder.
   - **Considered:** (a) the Node module takes the request and ends its spans and encoders itself, as a tool that drives a browser closes it; (b) the spans and their encoders stay in the renderer's process group and the engine ends the group.
   - **Chosen because:** (b). The ending keeps one owner, the one that five review rounds of 0.23.0 examined, and a renderer holds nothing that a kill loses: an unfinished picture is of no use, and the spans' folder is removed when the next render starts. The renderer's report is a file read after the group has ended, so the wait reads no pipe.
   - **Applies to:** `renderer.run_renderer`, unchanged but for the browser's environment, which is gone; `native-canvas.mjs`, in which a span that fails ends the others. A failure is the module's own to end, since no request reaches it then: a draw that throws closes its encoder's input and kills the encoder before the process exits by its status. FFmpeg asked once to end still waits for its input; a first repair that only asked it to end left a render waiting to its deadline in the engine's own test [S10]. An encoder that ends with status 0 before it was given every frame of its span fails the span. The spans' folder holds nothing but what a render writes, and a folder that holds anything else is refused untouched.
   - **Reopened when:** a renderer comes to hold something that a kill loses.
   - **Sources:** [S2] [S5].
4. **A second render must draw the same frames, by a digest of the drawn pixels; its encoded bytes need not be equal.**
   - **Rests on:** N1, in which two draws of 600 frames were equal by hash; this slice's tests, in which one process and three spans state one digest; a smoke render whose one-span and two-span files state one digest and hold different bytes; the cost of a checksum of a UHD frame in the renderer's thread: 1.05 ms by CRC-32, 10.45 ms by SHA-256, 36.62 ms by MD5, where a frame takes about 9.5 ms to draw and encode in one process (341.9 s for 36,000 frames).
   - **Considered:** (a) equal files: the spans' encoders and the join differ with the span count, so two valid renders differ; (b) a SHA-256 of every frame, which costs more than drawing it; (c) the CRC-32 of every frame's pixels, four bytes each in the film's order, digested once by SHA-256; (d) only the comparison of the two decoded films, as today.
   - **Chosen because:** (c). It binds what was drawn, costs a tenth of a frame, and is the same for every span count. A CRC-32 is no defence against a forged frame; the claim it carries is that two draws by one program agree. `qualify-renderer` refuses two renders whose digests differ and keeps its comparison of the decoded films, (d), until the draft's decision 3 removes it.
   - **Applies to:** the report of `native-canvas.mjs`, every render receipt (`drawn_sha256`), the qualification record (`drawn_alike`).
   - **Reopened when:** two draws of one stage differ on a host a film builds on, or the frame that differs must be named, for which the spans' checksums would be kept.
   - **Sources:** [S1] [S5] [S7].
5. **The renderer reads the stage; the picture's data stands there as `film.json`, beside the document that inlines it.**
   - **Rests on:** the geometry check and the cover, which paint the staged document in a browser; the bindings of the document's digest in receipts, the geometry report, the review and the reproduction, all outside this slice.
   - **Considered:** (a) cut the data out of the document's text; (b) have the renderer derive the data from the edition's timeline, a second derivation that could disagree with the document's; (c) write the data once, from the function whose result the document inlines, and check it at validation as the document is checked.
   - **Chosen because:** (c). One derivation feeds both readers, and `source_sha256` stays the document's digest, so no binding outside the slice moves. The template loses the GSAP script and the timeline it built for HyperFrames and keeps `__filmReady`, and a stage copies no timeline engine.
   - **Applies to:** `rendering.film_data`, `stage_picture`, `require_current_stage`; each film's `picture/index.html`.
   - **Reopened when:** the checks that paint the document leave the engine; the data's digest then binds a receipt.
   - **Sources:** [S2].
6. **A receipt names the native library its render loaded, by its bytes, and a release qualifies the build whose library the engine pins.**
   - **Rests on:** the draft's decisions 1 and 2 (the receipt names the package, its version and integrity, the text renderer and the operating system's version); the engine's rule that a record states what ran, read when it runs, and never the engine's constants; the canvas's loader, which takes the file `NAPI_RS_NATIVE_LIBRARY_PATH` names before the package's own, and then other places than the platform's package (`node_modules/@napi-rs/canvas/js-binding.js`); the review's run in which a copy named by that variable was the library the process held while npm's record still named the package [S10].
   - **Considered:** (a) the integrity npm recorded for the package and for its binary package, the unit a film's lock pins, which this slice first chose: it names what was installed, and the loader need not load it; (b) the SHA-256 of the library the process loaded, 28.9 MB read once a drawing process, which also sees a file changed after its install; (c) both.
   - **Chosen because:** (c), with (b) as what a gate rests on. Each drawing process reports the library it loaded: its path, its SHA-256 and the package whose manifest stands beside it. The receipt adds what npm recorded: the canvas package's version and integrity, and the integrity of the package the library belongs to. The engine pins the library's SHA-256 for the one platform a release qualifies, Apple silicon, beside the canvas package's integrity. Validation refuses a picture whose receipt names another package, version or text renderer; a derivation and the qualification's `pinned_build` further require the pinned integrity and the pinned library (`renderer.unqualified`), as a derivation required the pinned browser's bytes. Another platform's library, or a file that differs, is recorded as it is and is not the pinned build. The engine does not pass the loader's variable on to a render.
   - **Applies to:** `picture/renderer.py` and the module's report; the receipts' fields `renderer` (with `binary` and `text_renderer`), `operating_system`, `spans`, `frames` and `drawn_sha256` replace `capture`, `workers`, `browser` and `renderer_version`. `picture/browser.py` now holds only the checks' browser.
   - **Reopened when:** the engine builds on another platform, whose library it would pin too. The limit that stays: the JavaScript files of the canvas package are named by npm's record, so one changed after its install is not seen.
   - **Sources:** [S1] [S2] [S6] [S10].
7. **The declared capture stays, and decides only how the uncaptioned picture is made.**
   - **Rests on:** `derivation.uncaptioned_way` and `validate_binding`, which read `[picture] capture`; the bound of this slice, which leaves the derivation's logic alone.
   - **Considered:** (a) remove the declaration with the flags it set, which changes when a picture is derived and the film declaration's schema; (b) keep it for the one module that still reads it.
   - **Chosen because:** (b). The declaration leaves with the derivation, in the slice that draws both pictures.
   - **Applies to:** `film-engine` and `caption-equivalence`; no render command or receipt names a capture.
   - **Reopened when:** the draft's decision 3 is admitted.
   - **Sources:** [S1] [S2].
8. **HyperFrames, GSAP and the override of undici leave the supply; the browser and Puppeteer stay.**
   - **Rests on:** a search of the engine and the sample film for what loads each package: nothing but the render path loaded HyperFrames or GSAP, and with HyperFrames gone nothing in the lock needs undici; `headless-browser.mjs` launches the supplied browser through `puppeteer-core` for the geometry check, the whole-turn gate, the cover and the player check. The engine declares a minimum release age of zero hours, so a package published on 12 November 2026 is admitted.
   - **Considered:** (a) keep GSAP for the template; (b) remove what nothing loads.
   - **Chosen because:** (b). The lock goes from 129 packages to 39, `npm audit` reports no advisory, and no package of the lock runs an install script.
   - **Applies to:** `package.json`, `package-lock.json`, `NOTICE`.
   - **Reopened when:** the canvas package fails the engine's supply checks; `skia-canvas` is the draft's fallback.
   - **Sources:** [S1] [S6].
9. **The whole-turn gate stays, and its requirement says what it now guards: the checks' browser, not a film's frames.**
   - **Rests on:** two probes of the native canvas: 51 stroked whole turns from 17 starts at three sweeps, and the review's 12,000 (6,000 starts, the whole turn and the gate's lower bound), of which the lowest painted 99.47 % of a full ring's ink, so the fault the gate was written for was not seen on the canvas; the cover, which a browser still paints from the composition.
   - **Considered:** (a) remove the gate with the browser's render; (b) ask the canvas the gate's question for a film's own starts; (c) keep the gate for the cover and the document the geometry check reads, and say so in `picture-gates`.
   - **Chosen because:** (c), within this slice's bound. The canvas is not asked: 12,000 turns found no ring it leaves out. The requirement's "the renderer's browser" becomes "the browser that paints the cover", by a delta; a film's frames are the canvas's. A film is still refused for an arc that browser fails, because its cover is painted there.
   - **Applies to:** `picture-gates`, one requirement's words; no code.
   - **Reopened when:** the cover is drawn by the canvas; the gate goes with the browser then.
   - **Sources:** [S8] [S10].
10. **The stylesheet's faces have one reader, in the engine's Python, and a stage's record hands them to the renderer.**
    - **Rests on:** the review's run: a rule the first reader's expressions did not match (`src: local("B"), url(...)`, upper-case keywords, a comment before `url(`) registered nothing, and a family the canvas does not hold drew from an installed font without an error; no gate saw it, since the checks' browser parses the stylesheet itself and the audits' table used the same expressions [S10]. The three films' and the sample's rules, read on 18 November 2026: one family and one `url(...) format(...)` each, with `font-weight` and `font-display`.
    - **Considered:** (a) two readers held alike by a test, one in Python for the audits and one in the Node module; (b) a CSS parser as a dependency; (c) one reader in Python (`picture/faces.py`) that takes the rules it can hold a canvas to and refuses the rest by name, whose faces staging writes into the stage's record.
    - **Chosen because:** (c). The audits' table and the canvas then take every family from the same file by construction, and the module reads no stylesheet. A rule is read when it declares one family and one source, with or without a `format`, and beside them only `font-weight`, `font-style` or `font-display`, which choose nothing where every family names one file; two rules of one family, a source list, `local(...)`, `unicode-range` and any other descriptor are refused, because the canvas registers one file under one family and follows none of them. Every rule must name a declared font and every declared font a rule; the module refuses a stage that names no faces, as a stage of an earlier engine, and one that holds a font no face registers. The record also names the language, which the document and the canvas take from one function.
    - **Applies to:** `picture/faces.py`, `rendering.declared_faces`, `stage_picture`, `require_current_stage`, `metrics.declared_faces`, `native-canvas.mjs`.
    - **Reopened when:** a film needs two files under one family, or a descriptor the reader refuses.
    - **Sources:** [S10].
11. **An encoder's one line about the size of its input is dropped, and every other line goes on.**
    - **Rests on:** an experiment of 18 November 2026 with FFmpeg 9.0.2 and frames of 8.3 MB: fed from Node's stdio pipe, which is a socket, an encoder prints "Truncating packet of size 8294400 to 65536" at its error level before its first frame and then reads every frame whole; fed the same bytes from a shell's pipe it prints nothing. The sample build of 14:42 held 18 such lines, one an encoder, in a passing log [S10] [S11].
    - **Considered:** (a) leave the lines, so that every passing render prints errors; (b) lower FFmpeg's log level, which hides a real error; (c) feed the encoder through a named pipe, whose throughput at 33 MB a frame was not measured; (d) pass the encoder's error lines on but for that one line, once an encoder.
    - **Chosen because:** (d), the smallest change that leaves a passing render's log empty of errors.
    - **Applies to:** `native-canvas.mjs` (`passErrors`).
    - **Reopened when:** FFmpeg changes the line, or the frames come to be fed another way.
    - **Sources:** [S10].
12. **The qualification's second render is drawn in another count of spans than the first.**
    - **Rests on:** the digest's claim, that it does not depend on the spans a film was drawn in, which the tests show on 60 and 120 frames; a composition that carried state from one frame to the next would draw otherwise in a span that starts midway, and two renders in one count would agree on it.
    - **Considered:** (a) the same count for both, as this slice first had it; (b) one process for the second render where the first was drawn in several, and two spans where it was drawn in one.
    - **Chosen because:** (b): the sample film's release build then compares a film drawn in four spans with the same film drawn in one process, over every frame.
    - **Applies to:** `qualification.other_count`; a qualification's second render takes about the time of a one-process render.
    - **Reopened when:** the draft's decision 3 removes the second render.
    - **Sources:** [S5] [S10].

## Risks / Trade-offs

- A picture's receipt of an earlier engine does not validate. → Intended: a film that adopts this engine renders its pictures again, and a released edition keeps its tag's engine.
- `system` text is the operating system's, and a character that no registered face holds is taken from the host's installed fonts. → The receipt states the operating system's version; whether a film's audits guarantee that its faces hold every character it draws was not read for this slice.
- The canvas context is opaque, as the spikes' was, and the package's README says that opaque canvases on macOS draw LCD text under `system`. → The look is the one N1 and N2 measured against the releases; the sample build's comparison is the check on the engine's own film.
- The canvas package's JavaScript files are named by npm's record, not by their bytes (decision 6); the native library is named by its bytes.
- The still scan reads a native draft otherwise than a browser's. On the sample film's Chinese draft the fine rule's run from 3.0 s ends at 5.5 s on the browser's draft and at 7.2 s on the native one (3.32 s of speech against 2.3 s; the limit is 3.5 s), and the coarse runs are equal: a slow change stands at the fine rule's threshold, and the two renderers' frames fall on either side of it [S11]. → A draft record names what drew its draft, and `preflight` asks for a new draft where another renderer drew it. What decides the limits: the six released editions' drafts drawn natively and their scans read run by run, before a film adopts (task 5.4). Four are read: the drafts of both editions of the essentials and the ETHOS film, drawn by the browser and by the canvas, hold the same longest fine run of speech (2.54, 3.06, 2.86 and 2.90 s; none over the limit), and their 16 differing runs differ by at most 0.40 s of speech, at the fine rule's thresholds [S12]. The DDWG film's two editions are not read.
- A draft at half the film's size is not a small copy of the film, whatever draws it: both renderers set text on whole pixels of the size they draw at. In the ETHOS film's Chinese edition both drafts step one label by one pixel at 845.6 s, where the released film holds it still at both of its sizes; the drafts so end a still run that the film holds for 3.86 s of speech, over the limit of 3.5 s [S12]. → Not this slice's to repair: the draft's size is the capability `render-preflight`'s. The draft `faster-films-less-by-hand` holds it as an open question, since a native draft can be drawn at the film's own size.
- The whole-turn gate guards what the checks' browser paints, the cover, and no longer a film's frames (decision 9).
- A captioned UHD film's keyframes move to the 2 s grid, and its rate factor from 14 to 12. → Its bytes and its size change; the sizes are read from the sample build (task 5.1).
- The main spec `build-time` still names the render's worker count in its purpose line, which a delta cannot change. → It is corrected with the release's documents.

## Open Questions

- Not measured: a whole film of the three films on this engine, as distinct from the spikes' script; a sample build on the tree as the review's repairs left it (task 5.1; the build of 14:42 ran on the tree before them); the time of a render against a baseline repeated in the same ticket [S11]; span counts other than 1, 4 and 8, and 4 against 8 in one ticket; whether two encodes of equal frames in equal spans hold equal bytes; another host, operating-system version or architecture; the time of a render beside a narration or another build.
- Whether the qualification's second render is still worth its time once the digest stands for the drawn frames: the draft's decision 3.

## Sources

Read or measured on 18 November 2026 unless a date is given. Paths under `build/evidence/draw-pictures-natively/` are the canonical checkout's local evidence, to which task 5.3 promotes the slice's records.

- **[S1] The draft `faster-films-less-by-hand`:** `openspec/changes/faster-films-less-by-hand/design.md`: its Context (spikes N1 and N2 with their tables), its decisions 1, 2, 3 and 7, and its Sources [S2], [S3] and [S7], which name the spikes' records and the canvas package's registry entry (published 12 November 2026, MIT). The owner's agreement to that direction is its [S1].
- **[S2] The engine at `27e1027`:** `src/filmkit/media.py` (`require_video`, `video_cadence`), `picture/derivation.py` (`ENCODER`, `KEYFRAME_SECONDS`, `uncaptioned_way`), `production.py` (`Rendition.keyframe_seconds`), `delivery/packaging.py` (`keyed_as_declared`), `delivery/verification.py` (the films' color tags), `child_processes.py`, `picture/rendering.py` (`run_renderer`), `picture/geometry-check.mjs`, `delivery/player-check.mjs` and `picture/headless-browser.mjs`. The search for what loads HyperFrames, GSAP and the document's timeline: `git grep` over `src`, `examples` and `.config` at that commit.
- **[S3] The spikes' code:** `render.mjs` and `spans.sh` of N1 and N2, from which `native-canvas.mjs` starts; read in the films' kit, where the draft's [S2] and [S3] name their promoted copies. The copies were not compared.
- **[S4] The spikes' times:** the draft's Context tables: N1 at a 1-minute load of 7 to 36, N2 at 3 to 16.
- **[S5] Draws that agree:** `tests/picture/native-canvas.test.mjs` (one process and three spans), `tests/picture/test_native_render.py` (the engine's contract of a picture on a film joined from spans; a render asked to end), and `build/evidence/draw-pictures-natively/smoke/` (`s1.json`, `s2.json` and the two files, 240 frames at 1920×1080 of the sample's composition).
- **[S6] The supply:** `build/evidence/draw-pictures-natively/supply.sh` with `supply.log`, `supply-npm-audit.json` and `supply-lockdiff.txt`: the lock resolved by `npm install --package-lock-only --ignore-scripts`, 12 packages added, 102 removed, none moved, no advisory, no install script. The licenses: the installed packages' record `node_modules/.package-lock.json` (both canvas packages MIT) and the binary package's `sbom.cdx.json` (CycloneDX 1.6, 138 components). The release age: `.config/mise/config.toml`, `minimum_release_age`.
- **[S7] The cost of a checksum:** `build/evidence/draw-pictures-natively/hash-bench.mjs` and `hash-bench.txt`: 30 buffers of 33,177,600 bytes each, Node 26.13.1, at 12:45 CST with a 1-minute load of 34.5.
- **[S8] Whole turns on the canvas:** `build/evidence/draw-pictures-natively/whole-turn-probe.mjs` and `whole-turn-probe.txt`, with `@napi-rs/canvas` 1.1.1 as the scratch clone installs it.
- **[S9] The canvas's text renderers:** the README of the installed package, `node_modules/@napi-rs/canvas/README.md` at 1.1.1, section `setTextRenderer()`.
- **[S10] The review and its repairs:** `build/evidence/draw-pictures-natively/review/`: the independent review of 18 November 2026 (`review-picture.md`: no high finding, 4 medium, 20 low) with its probes and their output (`probe-canvas.mjs`, `probe-loader.cjs`, `probe-turns.mjs`, `out/`), and the repair's record (`repair.md`: each finding's state and test; `out/node-test-no-ffmpeg.txt`, `out/node-test.txt`; the experiment with FFmpeg's input from Node's pipe and from a shell's, and with `setparams`). The loader's order: `node_modules/@napi-rs/canvas/js-binding.js` at 1.1.1. The films' rules: `picture/film.css` of `ddwg-film`, `ethos-film` and `ddwg-essentials-film` at their checkouts' heads.
- **[S11] The sample build of 14:42:** `build/evidence/draw-pictures-natively/native/result.md` with `sample-build.log`, `sample-durations.txt`, `compare.log` and `tickets.txt`: one host ticket, 14:30:29 to 14:42:38, the 1-minute load from 6.5 to 33.8; every gate passed, the twelve films and pictures stand between 52.88 and 53.71 dB at their lowest frame against the last browser build, and no time follows from it. It ran on the tree before the review's repairs.
- **[S12] Drafts of released editions by both renderers:** `build/evidence/draw-pictures-natively/drafts/report.md` with `records/table.md`, each edition's records under `records/<film>/<lang>/` (the browser's draft, the native draft and the released 1080p film, read by one scanner), `frames/`, and `label-step.md` with `frames/ethos-film-zh-845.6s-draft-against-final/label-centroid.py` and its output. Subjects: `ddwg-essentials-film` at `v1.0.2` and `ethos-film` at `v2.0.1`, both editions of each; the browser's drafts by each film's own engine (0.22.3 with HyperFrames 0.9.46), the native drafts by this slice as repaired. One host ticket, 18:17 to 19:01 CST, the 1-minute load 21 to 41; an edition's two drafts ran side by side, so no time of a renderer follows from it.
