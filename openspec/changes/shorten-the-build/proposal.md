## Why

A 25-minute film takes about 2 h 55 min of compute to rebuild on the host that builds the films (18 cores), and a change to one scene costs the same: narration 37 to 50 min, four UHD renders 61 min, two every-frame comparisons 30 min, packaging 22 min, verification 8 min. Almost none of that is recorded: only the render receipt holds a duration, so the figures had to be assembled from logs and file times. The repository owner asked on 17 November 2026 for a deep and complete optimization (01:19 CST: 「性能和效率非常重要，要求做深度和全面的优化」) and, after the first measurements and what they recommend, for all of it to be done (03:00 CST: 「继续，按你推荐的全部执行」).

Measured that night on a 120 s span of a film's UHD stages: the renderer's worker count changes no frame, and 16 workers take a tenth to a fifth less time than the engine's fixed 8; the uncaptioned picture, which the engine renders in full a second time and then proves equal to the first by decoding both at every frame, is the captioned picture with its caption band painted over, which one encode makes in 18 s with the band identical to the native render's. The 1080p films' hardware encoder left the keyframe grid six times since 13 November for a cause never found, each time ending a build.

## What Changes

- **Every production command and `narrate` write a duration record**: the command, when it started, its seconds, whether it completed and the seconds of each phase. A record stands beside the edition's evidence and inside no record that another record binds by SHA-256. `python -m filmkit.durations` prints a build's records and their sum. The verifier, which writes nothing, and the reproduction state each film's seconds in their reports.
- **The render's worker count is a measured setting**: the host's logical cores less two, never under 8 nor over 16, or what `FILMKIT_RENDER_WORKERS` names; the receipt records it. The fixed 8 goes.
- **`render-picture --uncaptioned` derives the uncaptioned picture from the captioned one for a film that declares `software` capture**, the capture the engine qualifies at each release; a film of any other capture keeps its render of the uncaptioned stage and the every-frame comparison. A derivation is one software encode of every frame with the caption band painted in the ground the captioned picture shows there. Before it encodes, it proves headlessly at every thirtieth of a second that the band holds caption paints and nothing else; after, that the captioned picture's band stood at the ground in every frame without a caption. `--native` renders the uncaptioned stage as before. **BREAKING** for a film whose composition draws anything but captions in the band's rows: the derivation refuses and names `--native`.
- **`compare-pictures` compares a derived pair by its derivation's record and decodes no picture**; a natively rendered pair is compared as before, at every frame.
- **The renderer's determinism is qualified once for each renderer supply, in the sample build**: the sample renders one stage twice and requires every decoded frame identical, and compares a natively rendered pair at every frame. A film no longer pays for that proof in every build, and can still ask for it.
- **The 1080p films are encoded by x264 with a keyframe forced at every 120th frame** and scene-cut keyframes off, not by VideoToolbox. The 1080p uncaptioned film of a derived pair is painted and scaled from the captioned picture in one pass, so it is one encode from the render. **BREAKING** for a rebuild of an earlier release: its 1080p films are other encodes of the same pictures, compared by measure as a rebuilt film already is.
- **Independent checks run side by side**: `check-picture`'s frame, motion and detail audits, and the verifier's films, up to four at once. Each reports and refuses what it does in sequence.
- **`render-picture --language all` makes both editions' pictures with one command**: two rendered pictures at the same time, the renderer's own lock off for those two renders alone, two derived pictures in a row. Each edition keeps its own receipt and duration record. A film's task list may use it and need not.
- **Narration divides the segments it has to generate among processes of the speech model**, two unless `FILMKIT_NARRATION_PROCESSES` names another count, and writes the one receipt as before. Every take keeps its bytes.
- **Exact small savings**: transcripts cached as alignments are, one decode for both phases of a still scan, the reproduction's film pairs side by side.

## Capabilities

### New Capabilities

- `build-time`: the duration records and the command that prints them, the render's worker count, the checks that run side by side, and narration in several processes.

### Modified Capabilities

- `caption-equivalence`: the uncaptioned picture is derived unless a native render is asked for; what a derivation proves; how a derived pair is compared; what packaging's comparison record binds.
- `film-engine`: a render's command differs from the earlier one by its worker count; one command may make both editions' pictures.
- `film-package`: the 1080p films' encoder and how it holds the keyframe grid.
- `sample-film`: the sample film declares `software` capture; its build renders both captioned pictures at once, qualifies the renderer and derives one edition's uncaptioned picture; a task prints its durations.

## Impact

- `src/filmkit/durations.py` (new), `produce.py`, `narration/narrate.py`, `picture/rendering.py`, `picture/derivation.py` and `picture/band-audit.mjs` (new), `picture/qualification.py` (new), `picture/equivalence.py`, `picture/gates.py`, `production.py`, `delivery/packaging.py`, `delivery/verification.py`, `delivery/reproduction.py`, `tools.py` and their tests; the sample film's tasks; the README and the Changelog.
- The budget this Change works towards, each figure to be measured on a film's build before and after with the durations command: a 25-minute film rebuilt in 90 minutes of compute or less. A change to one scene in 20 minutes or less needs span renders and is a later slice.
- An adopting film keeps its task list: `render-picture --uncaptioned`, `validate-picture --uncaptioned` and `compare-pictures` keep their names and decide by the receipt. Its 1080p films change bytes; its UHD uncaptioned film becomes an encode of the captioned picture.
- Out of scope, each named in the design with its reason: span renders and a segment cache for one-scene changes; narration in more than two processes by default, which waits for a measurement on a whole narration; a verification that does not decode again what was proven, which changes what the verifier claims and is the owner's decision; the reviewers' measuring tools shipped by the engine.
