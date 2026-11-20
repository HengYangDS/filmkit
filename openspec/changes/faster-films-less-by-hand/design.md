## Context

What a film's build does today, read in the engine at `v0.23.0` and measured on the released editions of the three films (DDWG film 1.3.1, ETHOS film 2.0.1, essentials film 1.0.2) on 18 November 2026. A mark such as [S4] names an entry under Sources at the end, where each record, script and page read is listed.

- A film's composition, `picture/film.js`, draws every frame on one Canvas 2D context. It touches 28 members of that context (paths, rectangles, arcs, text, transforms, alpha and dashes) and no DOM, style sheet, image, gradient or clip. The engine's audits already run it in Node on a stand-in canvas. [S2]
- A picture is captured from a headless browser by HyperFrames at 3840×2160 and 60 frames a second. The essentials film's captioned picture (36,000 frames) took 354.9 s at 8 workers on a quiet host. The build then derives the uncaptioned picture by a second encode with four proofs of the caption band (87 to 89 s), qualifies the renderer by a second render and an every-frame pair measure once a release, scans for one-frame faults and can repair them, and encodes the 1080p films from the UHD pictures. [S6]
- Composing is not the cost: 25.1 to 28.4 paints and 0.29 to 0.32 ms a frame, so the 90,000 frames of the DDWG film compose in 34.6 s in one process. Held frames are no lever either: 84 to 91 % of a film's frames are new pictures. [S5]
- 6,206 of the engine's 31,903 lines of Python and JavaScript stand in the twenty modules of that capture path and its proofs. [S4]

Spike N1 (18 November 2026, 01:37 to 02:18, the essentials film's English edition, whole film, as one host ticket of 730 s): `@napi-rs/canvas` 1.1.1 (MIT, a Skia canvas for Node with a prebuilt binary for Apple silicon, published 12 November 2026) drew the unchanged composition. [S2] [S7]

| What                                     | Today                            | Native canvas, measured                                           |
| ---------------------------------------- | -------------------------------- | ----------------------------------------------------------------- |
| UHD captioned picture                    | 354.9 s, quiet host              | 135.5 s in 8 spans; 341.9 s in one process; 1-minute load 7 to 36 |
| UHD uncaptioned picture                  | derived, 87 to 89 s, four proofs | 139.9 s in 8 spans, drawn with no captions                        |
| 1080p picture                            | encoded from the UHD picture     | 112.4 s drawn at 1920×1080, one process                           |
| Two draws of 600 frames                  | a second render and a pair scan  | every frame's hash equal                                          |
| Against the released UHD picture, 36,000 | the floor of a rebuild is 45 dB  | average 54.10 dB, lowest 49.90 dB, no frame under 48 dB           |

Text agreed with the released picture to under 0.1 px in place and 0.4 % in ink, with the canvas's text renderer set to `system`. Its default, `portable`, drew the same labels 11 to 13 % lighter. The three lowest frames, looked at, differ in the antialiasing of long horizontal edges and in nothing else.

Spike N2 (18 November 2026, 06:39 to 06:54, two host tickets of 432 s and 471 s): three more whole editions, their compositions unchanged, each UHD captioned picture drawn in four spans and compared with the released picture at every frame. [S3]

| Edition                  | Frames | Drawn in | 1-minute load | Mean     | Lowest   | Frames under 48 dB | Under 45 dB |
| ------------------------ | ------ | -------- | ------------- | -------- | -------- | ------------------ | ----------- |
| Essentials film, Chinese | 36,000 | 139 s    | 3 to 14       | 54.28 dB | 50.47 dB | 0                  | 0           |
| ETHOS film, English      | 54,000 | 205 s    | 14 to 16      | 58.67 dB | 50.05 dB | 0                  | 0           |
| DDWG film, English       | 90,000 | 350 s    | 15 to 16      | 54.20 dB | 47.25 dB | 31                 | 0           |

The DDWG film's lowest frames stand at 1,276.2 s, where one long horizontal rule is being drawn: the browser's rule carries a half-covered row under it and the canvas's edge is sharp. Looked at, no mark differs. Of the 216,000 frames of the four editions drawn in N1 and N2, none stands under the 45 dB floor of a rebuilt picture.

## Goals / Non-Goals

**Goals:**

- A film's pictures in a fraction of today's time, from the composition the film already has, with no step that exists to prove a capture.
- One drawing library, owned by the engine.
- A scene that states what stands where in relation to what, and is placed by a layout.
- A change that rebuilds its own span.

**Non-Goals:**

- A new look. Each slice is accepted against the released pictures, and a difference a viewer can see goes to the owner first.
- Rebuilding released editions. A release keeps its tag's engine and its bytes.
- Another review. The dimensions, the floors and the reviewers stay as they are.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, where it applies, what would reopen it, and its sources.

1. **A picture is drawn by a native canvas that runs the film's composition unchanged.**
   - **Rests on:** spikes N1 and N2 above: four whole editions of three films, 216,000 frames, none under the floor of a rebuilt picture.
   - **Considered:** (a) the browser path, tuned further: 0.23.0 took its worker count, its derived picture and its qualification as far as measurements led, and the capture and its proofs remain; (b) Remotion: it renders through Chrome Headless Shell too, and its free licence is "for individuals and companies of up to 3 people"; (c) Motion Canvas: its latest stable release on npm is 3.17.2 of 14 December 2024; (d) Manim: animations are written in Python, so every scene would be written again; (e) `skia-canvas` 4.0.1, another Skia canvas for Node: not measured; (f) `@napi-rs/canvas`, which ran the three films' compositions as they are.
   - **Chosen because:** (f) keeps every scene and every audit a film has, removes the capture, and was measured on whole films. (e) stays the fallback if (f)'s supply fails a film.
   - **Applies to:** `picture/rendering.py` and what it starts; a render receipt names the canvas package, its version and its integrity in place of a browser. Three tools draw in the browser today beside the render: `geometry-check` and the cover's painting move to the canvas with the picture, and `whole-turns`, which answers a fault of that browser's arcs, is asked of the canvas once and then goes. `player-check players` keeps the browser, since it reads the delivered pages as a viewer's browser does; the pinned browser build and its driver stay in the supply for it.
   - **Reopened when:** a film's composition needs a canvas member the package lacks, a frame of a film stands under the floor of a rebuilt picture, or the package fails the engine's supply checks.
   - **Sources:** [S2] [S3] [S6] [S7] [S8] [S9] [S10] [S11] [S14].
2. **Text is drawn by the host's own renderer.**
   - **Rests on:** N1's text measurements; the package's README: `portable` draws text the same on every operating system under stated conditions, `system` draws it as Chrome does on each (CoreText on macOS).
   - **Considered:** (a) `portable`, the same pixels on every host and a visibly lighter face (11 to 13 % less ink on the labels measured); (b) `system`, the films' present look, which is the host's and may move with an update of the operating system, as the browser's did.
   - **Chosen because:** (b) changes nothing a viewer sees, which is this slice's aim.
   - **Applies to:** the renderer's one setting; the receipt states it and the operating system's version.
   - **Reopened when:** a film is to be built on another operating system, or an update of the operating system moves a frame under the floor.
   - **Sources:** [S2] [S7].
3. **Both pictures are drawn, and a renderer is qualified by frame hashes.**
   - **Rests on:** N1: the uncaptioned picture drawn in 139.9 s; two draws of 600 frames equal by hash; no browser raster left to draw a glyph wrong for one frame.
   - **Considered:** (a) keeping the derivation, its band audit, ground check, edge rows and scan; (b) drawing the uncaptioned picture with no captions and keeping the composition-level proof that captions change only their band.
   - **Chosen because:** (b) removes a second-generation encode and four proofs, and what is left proves the claim where it is made, in the paints.
   - **Applies to:** `picture/derivation.py`, `ground.py`, `band-audit.mjs`, `qualification.py`, `faults.py`, `repair.py` and the picture levels of `equivalence.py`, about 3,100 lines that go whole and parts of about 2,300 more; a floor against a reference stays for a rebuild.
   - **Reopened when:** two draws of one stage differ on a host a film builds on.
   - **Sources:** [S2] (the module table at its end) [S4].
4. **The 1080p films stay scaled copies of the UHD pictures.**
   - **Rests on:** N1: a picture drawn at 1920×1080 is another picture than the scaled one (39.4 dB on average against the released 1080p film; text about 5 % heavier and crisper), drawn in 112.4 s.
   - **Considered:** (a) drawing 1080p directly, faster and a new look; (b) scaling as today.
   - **Chosen because:** (b). This slice's aim is a picture a viewer cannot tell from the release, and (a) changes the text's look.
   - **Applies to:** `delivery/packaging.py`, unchanged.
   - **Reopened when:** the owner prefers the directly drawn look; frames of both stand in N1's record for that comparison.
   - **Sources:** [S2] (`frames/1080p-pair-30.png`, `out/psnr-1080p.txt`).
5. **The engine owns the drawing library.**
   - **Rests on:** the films at their release tags: 22 to 29 library files and 2,482 to 2,844 non-blank lines in each film's `picture/film/` beside its scenes; of the 20 paths all three hold, one is byte-identical, five stand in two versions and fourteen in three.
   - **Considered:** (a) three copies kept in step by hand; (b) one module of the engine that a film's bundle imports, with a film's own marks and palette left in the film.
   - **Chosen because:** (b). A repair to a mark or a motion then reaches every film with the engine's release, and the audits and the picture read one definition.
   - **Applies to:** `film-engine`; each film's `picture/film/` loses what the engine holds.
   - **Reopened when:** a film needs a primitive whose behaviour must differ from the other films' and cannot be a parameter.
   - **Sources:** [S4].
6. **A scene is declared and a layout places it; which layout engine is not yet chosen.**
   - **Rests on:** 38,874 non-blank lines of scene code in 160 files for the 263 thoughts of the English editions, 148 lines a thought, with 9,901 whole numbers of two to four digits; on 15 November 2026 four rendered pictures were voided by row gaps and pace findings that a gate had recorded and nothing had refused.
   - **Considered:** (a) the hand-set form with more gates; (b) a flexbox layout by Yoga (`yoga-layout` 3.2.1, MIT, "a portable layout engine targeting web standards"; its latest release on npm is of 13 December 2024); (c) a layout written for the films, which is the hand-written code this Change sets out to shed; (d) a constraint solver.
   - **Chosen because:** nothing yet. The slice begins with one chapter of one film declared and placed by (b) and by one alternative, judged by the lines a thought needs, by the gates it passes unaided and by the frames against the release.
   - **Applies to:** `scene-layout`; hand-written scenes stay valid beside declared ones.
   - **Reopened when:** not applicable until the trial chapter has chosen.
   - **Sources:** [S4] [S12]; the draft `decide-before-heavy-work`, `design.md`, Context.
7. **A build addresses its stages by the content of their inputs.**
   - **Rests on:** a native draw is deterministic and joins spans by stream copy at whole groups of frames (N1: eight spans joined to 36,000 frames on the single process's keyframe grid; N2: four spans, each film's frame count whole). In the whole-edition trial of 19 November 2026 both pictures of both editions were drawn again, hours apart, to the same bytes, and the edition's package was still void: the comparison record binds each render receipt by SHA-256, and a receipt holds its run's times (the trial's finding 19). A stage addressed by its content needs records that hold no run time wherever another record binds them, as a duration record already does. [S16]
   - **Considered:** (a) whole-film renders after every change; (b) spans keyed by the digest of the composition, the timeline's part and the faces, drawn again only when the key moves.
   - **Chosen because:** (b), after decision 1 stands; with a browser capture a span was not reproducible enough to cache.
   - **Applies to:** `incremental-build`; the kit's scripts that order a build, about 2,400 files outside any repository, become tasks of the engine or go.
   - **Reopened when:** a film joined from spans differs in a drawn frame from the film drawn whole.
   - **Sources:** [S2] [S3] [S4] (`kit-scripts.txt`).
8. **The narration's fit to the runtime is solved by a narration that converges by itself, in a Change of its own.**
   - **Rests on:** the owner's words of 18 November 2026: the voice needs a systematic solution, not tuning by hand. Today a thought that a gate refuses is named in a targets file, narrated from other seeds, picked and bound by hand, and the runtime is fitted by pause limits.
   - **Considered:** (a) the hand-kept auditions, ranked better; (b) a speech model that takes a requested duration, which the installed `mlx-audio` carries for other models than the films' (Qwen3-TTS documents its own `speed` as not supported) and which changes the voice; (c) a narration that generates candidates, scores each by the film's declared gates, selects over the whole edition and escalates by itself, with the speech model behind one interface.
   - **Chosen because:** (c): it removes the hand-kept inputs whatever the model is, and (b) becomes one engine behind that interface, measured like any other.
   - **Applies to:** the draft `let-narration-converge`; nothing in this Change.
   - **Reopened when:** not applicable here; see that draft.
   - **Sources:** [S1] [S13].

## Risks / Trade-offs

- `system` text is the operating system's. → The receipt states the version; a rebuild proof compares against the release with its floor; `portable` is there if a host must not matter.
- The canvas package was six days old on the day of the spike, and its Skia revision and advisories were not read. → The engine's release-age rule holds it like any supply; `skia-canvas` is the fallback.
- Edge antialiasing differs from the browser's on long horizontal edges. → Measured at 47.25 dB in the lowest of 216,000 frames; the owner was shown the spikes' lowest frames in a comparison page on 18 November 2026, and a film's edition drawn natively is released only after the owner has looked at that edition's lowest frames (the Change `draw-pictures-natively`, task 5.2).
- The work 0.23.0 put into the capture path (the derived picture, the qualification, the ending of a renderer's process group) is removed by the first slice. → It serves the released editions' rebuilds until then, and the handling of requests to end stays for the narration's processes.
- Declared scenes may not express every scene a film has. → Both forms stand side by side; no scene is rewritten for its own sake.

## Open Questions

- Not measured: the Chinese editions of the DDWG and ETHOS films; another host, operating-system version or the x64 build; the engine's gates, the still scan and the packaging on a native picture; the cover and the stills; span counts other than 1, 4 and 8; whether two encodes of equal frames are equal bytes, which would let a file's digest stand for its frames.
- Whether the audits take their text metrics from the canvas that draws the picture, which would retire the advance tables.
- Whether hardware encoding or a read-back without a copy moves the one-process rate, which the encoder bounds today.
- Which unit a film pins: the engine's release as today, or the engine with its canvas package's integrity in the film's lock.
- Whether a draft drawn at the film's own size reads as the film does. A draft at 1920×1080 does not where text stands on half a draft pixel: both renderers set text on whole pixels, and in one released edition both drafts end a still run that the film holds over the limit [S15]. A native draft could be every sixth frame of the picture itself, drawn as the picture is; what that costs on a whole edition, and whether its scan then equals the film's, is not measured.

## Sources

Read or measured on 18 November 2026 unless a date is given. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The owner, first-hand in the films' session, 18 November 2026:** at about 01:10 CST asked for a better design, 「更快更好，更少手撸」, with breaking changes allowed, and at about 01:43 agreed to the direction; at about 07:58 asked that a decision name its sources (「来源出处」); at about 08:26 and 09:17 asked for the voice's systematic solution, 「系统性解决方案，而不是手工调」.
- **[S14] Where the engine starts a browser:** at `v0.23.0`, `src/filmkit/picture/headless-browser.mjs` and its three importers, `picture/geometry-check.mjs`, `picture/whole-turns.mjs` and `delivery/player-check.mjs`, beside the renderer that `picture/rendering.py` starts.
- **[S2] Spike N1:** `build/evidence/faster-films-less-by-hand/n1/report.md` with `render.mjs`, `ticket.sh`, `spans.sh`, `tickets.txt`, `timeline.txt`, `out/members.json`, `out/psnr-*.txt`, `out/hash-sys-*.txt`, `frames/` and the lock of the canvas package. Subject: `ddwg-essentials-film` at `v1.0.2`. One host ticket, 01:51:28 to 02:03:38, the 1-minute load from 6.7 to 35.8.
- **[S3] Spike N2:** `build/evidence/faster-films-less-by-hand/n2/report.md` with `ticket.sh`, `spans.sh`, `tickets.txt`, `timeline.txt`, `out/psnr-*.txt`, `probe-*.txt`, `low/`. Subjects: `ddwg-essentials-film` at `v1.0.2`, `ethos-film` at `v2.0.1`, `ddwg-film` at `v1.3.1`. Two host tickets, 06:39:23 to 06:54:28, the 1-minute load from 3.4 to 16.4.
- **[S4] Counts of code:** `build/evidence/faster-films-less-by-hand/figures/figures.py` with its output `figures.json` and `figures.txt`, run on `filmkit` at `v0.23.0` and the three films at the tags above; `kit-scripts.txt` beside them, with its command.
- **[S5] What composing costs:** `build/evidence/faster-films-less-by-hand/unique-frames.mjs` and `unique-frames.txt`: each film's English timeline composed in one Node process.
- **[S6] Today's render and derivation times:** the archived Change `2026-11-17-shorten-the-build`, `design.md`: Context (the film trial, the essentials film at 1.0.2) and decision 2 (bench5: 354.9 s with 8 workers, 17 November 2026, 13:47 to 14:13 CST, other processes using 3.1 to 3.7 cores).
- **[S7] `@napi-rs/canvas`:** [its npm registry entry](https://registry.npmjs.org/@napi-rs/canvas) (latest 1.1.1, MIT) and [its README](https://github.com/Brooooooklyn/canvas) (the text renderers `portable` and `system`; the Skia badge reads `chrome/m157`).
- **[S8] Remotion:** [License and pricing](https://www.remotion.dev/docs/license/pricing) ("For individuals and companies of up to 3 people.") and [Chrome Headless Shell](https://www.remotion.dev/docs/miscellaneous/chrome-headless-shell) ("Remotion downloads "Chrome Headless Shell" into your `node_modules` to render videos.").
- **[S9] Motion Canvas:** [the npm registry entry of `@motion-canvas/core`](https://registry.npmjs.org/@motion-canvas/core) (latest 3.17.2, published 14 December 2024).
- **[S10] Manim:** [Manim Community's documentation](https://docs.manim.community/en/stable/) (v0.22.1; "Manim relies on Python's simplicity to generate animations programmatically").
- **[S11] `skia-canvas`:** [its npm registry entry](https://registry.npmjs.org/skia-canvas) (latest 4.0.1, MIT). Not installed and not measured.
- **[S12] Yoga:** [the npm registry entry of `yoga-layout`](https://registry.npmjs.org/yoga-layout) (latest 3.2.1, MIT, published 13 December 2024) and [its site](https://www.yogalayout.dev/). Not installed and not measured.
- **[S13] Speech models with a duration or a speed:** `build/evidence/faster-films-less-by-hand/figures/mlx-audio-duration-parameters.txt`, a search of the installed `mlx-audio` 0.6.6 for such parameters. No model was run.
- **[S15] A draft against its film:** `build/evidence/draw-pictures-natively/drafts/label-step.md` and `report.md` beside it (18 November 2026): the ETHOS film's Chinese edition at `v2.0.1`, its drafts by the browser and by the native canvas and its released films at both sizes, one label's place read every 0.2 s from 844.8 to 846.4 s.
- **[S16] A redraw to the same bytes:** the whole-edition trial's report, `build/evidence/faster-films-less-by-hand/whole-edition-trial/report.md`, finding 19 (19 November 2026); `src/filmkit/picture/equivalence.py` (`picture_bindings`: a picture's file and its receipt by SHA-256) and `src/filmkit/delivery/packaging.py` (`film_inputs`: the comparison record by SHA-256) at `db7a837`.
