## Why

On 18 November 2026 the owner asked whether a better design exists for building the films: the same quality, faster to produce and to change, on mature tools, with less written by hand, and with breaking changes allowed. Measured that day on the three released films and on the engine at `f5087be`, the cost of a film does not lie where the engine has been optimizing:

- **Composing a picture is cheap and capturing it is not.** A frame is about 28 paints on one Canvas 2D context and takes 0.3 ms to compose: the 90,000 frames of a 25-minute film compose in 35 s in one Node process. The same film's captioned picture takes minutes to capture through a headless browser, and the build then spends a second render, a derived picture, every-frame comparisons and a second encode on proving that the capture went well. 6,206 of the engine's 31,903 lines exist for that path.
- **A scene is written by hand, in pixels.** The three films hold 38,874 non-blank lines of scene code in 160 files, 148 for each of the 263 thoughts their English editions narrate, with 9,901 whole numbers of two to four digits among them. Alignment, spacing and balance are then found by gates and reviewers after the fact, round after round.
- **Each film carries its own copy of the drawing library.** 22 to 29 files and 2,482 to 2,844 lines in each film; of the 20 paths all three share, one is byte-identical, five stand in two versions and fourteen in three.
- **The runtime is fitted by search.** A voice that reads slower than the film's length allows is fitted by narrating a thought several times and keeping the shortest sound take.
- **A change rebuilds everything.** A picture change renders every picture again, and about 2,400 script files outside any repository hold the order of work.

This draft holds the intent in the repository. It has no specs or tasks: each slice of it is admitted as a Change of its own, with its specs and tasks, once its evidence stands on whole films. The figures above and the sources of every decision are listed in `design.md` under Sources.

## What Changes

- **A picture is drawn by a native canvas, with no browser in the build.** The composition a film already has runs unchanged; its frames go from the canvas to the encoder. **BREAKING**: the browser, HyperFrames and the render path built round them leave the engine; a film's receipts name the canvas package in place of a browser.
- **Both pictures are drawn from paints.** The uncaptioned picture is drawn with no captions instead of being derived from the captioned one, so the derivation and the proofs of its band leave.
- **A renderer is qualified by frame hashes.** Two draws of one stage are equal byte for byte or the stage is refused; the second render, the every-frame pair measure, the one-frame fault scan and the repair leave with the fault they guard.
- **The engine owns the drawing library.** The films' three copies become one module of the engine that a film imports. **BREAKING** for each film's `picture/film/`.
- **A scene is declared, and a layout engine places it.** A scene names its objects, their relations and the words they appear on; positions, alignment and spacing come from the layout. Scenes written by hand stay valid beside declared ones.
- **A change rebuilds what depends on it.** Stages are addressed by the content of their inputs, so a changed thought draws its span again and nothing else.
- **Narration converges by itself**, in place of auditions kept by hand: stated in the draft `let-narration-converge`, a Change of its own.
- **The films' kit moves into the engine or goes.** What a build needs is a task of the engine; what it does not need is removed.

## Capabilities

### New Capabilities

- `native-picture`: a picture drawn by a native canvas from a film's composition, its text renderer, its determinism and its receipt.
- `scene-layout`: declared scenes and the layout that places them.
- `incremental-build`: stages addressed by their inputs' content.

### Modified Capabilities

- `film-engine`: the engine owns the drawing library a film imports.
- `caption-equivalence`: the captioned and the uncaptioned picture are both drawn; the comparison stays at the composition.
- `picture-gates`: the audits measure text with the canvas that draws the picture.
- `build-time`: the render, the qualification and the derivation as they stand in 0.23.0 are replaced.

## Impact

- `src/filmkit/picture/` (rendering, browser, qualification, faults, repair, derivation, ground, equivalence, draft, metrics and the Node modules that launch a browser), `delivery/packaging.py`, the sample film, the supply (one npm package with a prebuilt binary in place of a pinned browser, HyperFrames and Puppeteer) and their tests.
- Each film: its `picture/film/` library, its tasks, its receipts. A released edition keeps its tag's engine and its bytes; its rebuild proof is not reopened.
- Out of scope: the review's dimensions and floors, the films' texts and the chosen voices, the host's queue.

Owner: the engine's maintainer. Next action: admit the native picture as the first slice, as a Change of its own with its specs and tasks, once the engine's gates and its packaging have been run on a native picture. Read again: 2026-11-22.
