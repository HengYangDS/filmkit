## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from `RENDERER_VERSION`, installs the browser build that `BROWSER` names and checks its SHA-256, and narrates each thought from a declared seed through mlx-audio's Qwen3-TTS in-context generator. A film adopts an engine release by tag and locks its own supply.

Read before any pin moved, on a clone outside the lane with nothing installed into the lane:

- **Identity.** Each moved package resolves on the registry the locks already use, from the publisher it had: `mlx-audio` from `Blaizzy/mlx-audio` (MIT), `hyperframes` from `heygen-com/hyperframes` (Apache-2.0).
- **Install surface.** The npm lock moves two packages and adds none; neither has an install script, and the lock's one package with one, esbuild, is unchanged. The uv lock moves seven packages and adds four pure-Python ones.
- **Advisories.** `npm audit` on the moved lock reports none; PyPI lists none for any of the eleven moved or added versions.
- **What the releases change on the engine's paths.** mlx-audio 0.6.5: the trim of decoded audio counts a frame as valid when its first codebook id is at least 0 (it was above 0), the tokenizer's decoder uses its sliding window, and a sampler is fed log-probabilities so that `top_p` applies; 0.6.6: samplers sample from logits. `generate()` still raises an in-context repetition penalty below 1.5, and `_generate_icl`, which the engine calls for a cast that declares a lower one, keeps its parameters. HyperFrames 0.9.47 to 0.9.64: its release notes name no capture flag and no browser build; most entries restrict what a render may read or reach.
- **The engine's suite on the moved supply:** every command of the repository check passes on the clone, the suite with warnings as errors.

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
2. **Acceptance is two builds of the sample film in one lane, compared.**
   - **Considered:** (a) the repository check alone, which runs no model and no renderer; (b) the sample film built before and after through every gate of `mise run sample:build`, then each take compared sample for sample and each film frame for frame.
   - **Chosen because:** (b) is the only place the engine's own evidence meets a real model and a real render. A take that differs is expected and is reported with its length and its difference; a build that fails a gate on the new supply stops the Change until the cause is read.
3. **The HyperFrames move is taken although the draft `faster-films-less-by-hand` removes the renderer.**
   - **Considered:** (a) holding HyperFrames at 0.9.46 until the native picture lands; (b) moving it now.
   - **Chosen because:** (b). The native picture is a draft with no date, the owner's rule on the latest stable supply stands meanwhile, and the eighteen releases between restrict what a render may read from the host, which a held pin would forgo.
4. **Version 0.23.1.** No declaration, command or output form changes; what changes is the supply and, through it, a film's takes when it adopts the release.

## Risks / Trade-offs

- The sample film's casts were auditioned on mlx-audio 0.6.4, and their seeds may give takes on 0.6.6 that a gate refuses. → The second build shows it; the casts are then auditioned again on the new supply inside this Change, or the narration moves are taken back and the renderer's ship alone.
- A film adopts 0.23.1 and expects its present takes. → The proposal marks the break; a film holds mlx-audio in its own lock to keep them.
- HyperFrames 0.9.64 was hours old when it was read. → The repository declares a release age of 0 hours by the owner's decision; the second build renders every frame of the sample film with it and compares them with the first.

## Migration Plan

A film that adopts 0.23.1 with a new narration bumps the engine and narrates; its auditions start again from its casts' seeds on the new supply. A film that keeps its takes pins `mlx-audio` 0.6.4 and `mlx` as its lock holds them, under `[tool.uv] override-dependencies`, and bumps only the engine and the npm packages. A released edition keeps its tag's engine and its bytes.
