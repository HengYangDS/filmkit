## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from `RENDERER_VERSION`, installs the browser build that `BROWSER` names and checks its SHA-256, and narrates each thought from a declared seed through mlx-audio's Qwen3-TTS in-context generator. A film adopts an engine release by tag and locks its own supply.

Read before any pin moved, on a clone outside the lane with nothing installed into the lane. A mark such as [S2] names an entry under Sources at the end:

- **Identity.** Each moved package resolves on the registry the locks already use, from the publisher it had: `mlx-audio` from `Blaizzy/mlx-audio` (MIT), `hyperframes` from `heygen-com/hyperframes` (Apache-2.0). [S2] [S4]
- **Install surface.** The npm lock moves two packages and adds none; neither has an install script, and the lock's one package with one, esbuild, is unchanged. The uv lock moves seven packages and adds four pure-Python ones. [S3]
- **Advisories.** `npm audit` on the moved lock reports none; PyPI lists none for any of the eleven moved or added versions. [S3]
- **What the releases change on the engine's paths.** mlx-audio 0.6.5: the trim of decoded audio counts a frame as valid when its first codebook id is at least 0 (it was above 0), the tokenizer's decoder uses its sliding window, and a sampler is fed log-probabilities so that `top_p` applies; 0.6.6: samplers sample from logits. `generate()` still raises an in-context repetition penalty below 1.5, and `_generate_icl`, which the engine calls for a cast that declares a lower one, keeps its parameters. HyperFrames 0.9.47 to 0.9.64: its release notes name no capture flag and no browser build; most entries restrict what a render may read or reach. [S4] [S5]
- **The engine's suite on the moved supply:** every command of the repository check passes on the clone, the suite with warnings as errors. [S3]

## Goals / Non-Goals

**Goals:**

- Narrate and render with the newest stable releases.
- Know, before a film adopts the release, what the moves change in the sample film's takes and frames.

**Non-Goals:**

- Moving the browser build, or `undici` to its 8 line.
- Qualifying the films' takes on the new mlx-audio; each film does that with the edition that adopts it.
- Changing any command, declaration, gate or output form.

## Decisions

1. **The moves ship together, as one release.**
   - **Considered:** (a) the renderer and the narration supply as two releases; (b) one release.
   - **Chosen because:** (b). A film adopts an engine release with an edition, and one adoption costs it one round; the comparison below tells the two apart, since takes and frames are compared separately.
   - **Reopened when:** one of the two moves fails the sample film and the other does not; the one that passes then ships alone.
   - **Sources:** [S1].
2. **Acceptance is two builds of the sample film in one lane, compared.**
   - **Considered:** (a) the repository check alone, which runs no model and no renderer; (b) the sample film built before and after through every gate of `mise run sample:build`, then each take compared sample for sample and each film frame for frame.
   - **Chosen because:** (b) is the only place the engine's own evidence meets a real model and a real render. A take that differs is expected and is reported with its length and its difference; a build that fails a gate on the new supply stops the Change until the cause is read. A frame can differ because the renderer moved or because a take's word times moved the cues, so the renderer is also compared alone: the baseline's sound, the picture rendered again on the new supply.
   - **Reopened when:** a film's own adoption shows a difference the sample film did not; the sample then gains what showed it.
   - **Sources:** [S6]; the archived Change `2026-11-14-take-hyperframes-0-9-46`, whose acceptance this repeats.
3. **The HyperFrames move is taken although the draft `faster-films-less-by-hand` removes the renderer.**
   - **Considered:** (a) holding HyperFrames at 0.9.46 until the native picture lands; (b) moving it now.
   - **Chosen because:** (b). The native picture is a draft with no date, the owner's rule on the latest stable supply stands meanwhile, and the releases between restrict what a render may read from the host, which a held pin would forgo.
   - **Reopened when:** the renderer compared alone moves a film under the measure the engine holds for two renders of one stage (`qualify-renderer`).
   - **Sources:** [S1] [S5]; the draft `faster-films-less-by-hand`.
4. **Version 0.23.1.** No declaration, command or output form changes; what changes is the supply and, through it, a film's takes when it adopts the release.
   - **Considered:** (a) 0.24.0, since a film's takes change; (b) 0.23.1, since nothing a film declares or runs changes.
   - **Chosen because:** (b); the break is in the bytes a film narrates anew, which the proposal marks and a film meets only with an edition.
   - **Reopened when:** not applicable.
   - **Sources:** the Changelog's releases 0.21.3 and 0.22.1, which moved supply as patch releases.

## Risks / Trade-offs

- The sample film's casts were auditioned on mlx-audio 0.6.4, and their seeds may give takes on 0.6.6 that a gate refuses. → The second build shows it; the casts are then auditioned again on the new supply inside this Change, or the narration moves are taken back and the renderer's ship alone.
- A film adopts 0.23.1 and expects its present takes. → The proposal marks the break; a film holds mlx-audio in its own lock to keep them.
- The decoder's change moves a take's samples and, by a few tenths of a decibel either way, its measured clarity (the sample film's Chinese soundtrack 20.23 to 19.95 dB, its English 16.68 to 16.85). → A film whose thoughts stand close above their line measures them again on adoption; the films' December editions narrate anew in any case. [S6]
- HyperFrames 0.9.64 was hours old when it was read. → The repository declares a release age of 0 hours by the owner's decision; the second build renders every frame of the sample film with it and compares them with the first.

## Migration Plan

A film that adopts 0.23.1 with a new narration bumps the engine and narrates; its auditions start again from its casts' seeds on the new supply. A film that keeps its takes pins `mlx-audio` 0.6.4 and `mlx` as its lock holds them, under `[tool.uv] override-dependencies`, and bumps only the engine and the npm packages. A released edition keeps its tag's engine and its bytes.

## Sources

Read or measured on 18 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence, here `build/evidence/take-mlx-audio-0-6-6-and-hyperframes-0-9-64/`.

- **[S1] The owner's rule on supply:** the archived Change `2026-11-14-declare-release-age-and-take-latest-supply`, `proposal.md` (the decision of 13 November 2026: the latest stable release, a release age of 0 hours), and its deferral of these moves.
- **[S2] The pins and the registries:** `registry.py` with its output `registry.json` and `registry.log` (PyPI's and npm's own entries for each direct pin: versions, upload times, licences, yanked and deprecated marks, install scripts); `outdated.sh` and `outdated.log` (uv's, npm's and Mise's own readings).
- **[S3] The moved locks on a clone:** `trial.sh` with `trial.log` and `lockdiff.py` (the npm lock resolved without installing, `npm audit`, the uv lock upgraded, each moved or added version asked of PyPI's advisories; the browser build HyperFrames 0.9.64 declares, read from its packed tarball); `trial-check.sh` with `trial-check.log` and `trial-check-light.log` (Mise's lock, the bootstrap and every command of the repository check on the clone).
- **[S4] mlx-audio:** [its releases](https://github.com/Blaizzy/mlx-audio/releases), v0.6.5 (pull requests 1116, 1117 and 1149) and v0.6.6 (1152); in the installed packages, `mlx_audio/tts/models/qwen3_tts/qwen3_tts.py` (the trim to the valid length; the in-context penalty's floor of 1.5) and `speech_tokenizer.py` (the decoder's window), 0.6.4 beside 0.6.6.
- **[S5] HyperFrames:** [its npm registry entry](https://registry.npmjs.org/hyperframes/latest) (0.9.64, Apache-2.0, no install script, `undici` 7.30.1) and [its releases](https://github.com/heygen-com/hyperframes/releases), v0.9.52 to v0.9.64; v0.9.47 to v0.9.51 stand on a page that was not read.
- **[S6] The two builds:** `build.sh`, `baseline-tickets.txt` and `moved-tickets.txt`; `compare-builds.py` with `compare-baseline-moved.txt` (takes, narrations, timelines, gates and every film at every frame), `compare-timelines.py` with `compare-timelines.txt` (the word times that moved), `compare-sound-gates.txt`; `renderer-only.sh` with `renderer-only-tickets.txt` and `compare-baseline-renderer-only.txt` (the baseline's sound rendered again on the new supply); `build/evidence/let-narration-converge/voice-spike/report.md`, arm 0 (the same codes from the same seed under both releases, another decode, 2 of 2 thoughts).
