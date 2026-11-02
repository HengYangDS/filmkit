# Proposal

## Why

On 2 November 2026 the owner asked that every governed repository keep its supply at the latest stable releases. Since 0.4.0, mlx-audio 0.6.4 and HyperFrames 0.9.4 and 0.9.5 have been released. The npm lock's semver and the uv lock's filelock each also have a newer patch release. Every other declared package is current.

Producing the ETHOS and DDWG essentials films on 0.4.0 also turned up two defects that reach a film owner.

The first is in `python -m filmkit.review.round prompts`. It raises `KeyError` for a script whose voice performance declares no coda, inner pause cap or thought boundary ratio, although the pause policy makes each of them optional. `ddwg-essentials-film` declares no coda, because its thought pause is longer than the longest coda the policy allows.

The second is in mlx-audio's Qwen3-TTS decode. It counts a frame as valid only when its first codebook id is above 0, while the reference tokenizer pads with −1 and counts every id above that. In-context narration decodes the reference's codes together with the take's, so each id-0 frame in either one cuts 80 ms from the end of the take. A reference that holds such frames cuts every take, and the assembly then refuses most of them as ending inside their last syllable. The fix is proposed upstream as Blaizzy/mlx-audio#1116; no release carries it yet.

## What Changes

- The reviewer prompt names an absent coda, inner pause cap or thought boundary ratio as not declared, instead of raising.
- Raise mlx-audio to 0.6.4 and HyperFrames to 0.9.5, set `RENDERER_VERSION` to 0.9.5, and refresh both locks with their native resolvers.
- Document the decode defect and its upstream fix, and how auditions and run-on retakes keep endings whole until that fix is released.
- Record the changes under `Unreleased`, date them as `[0.5.0]`, and set `VERSION` and the README pin to 0.5.0.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The prompt fix keeps the engine's existing contract, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

The Change touches these files:

- `src/filmkit/review/round.py` and its tests;
- `pyproject.toml`, `uv.lock`, `package.json` and `package-lock.json`;
- `src/filmkit/picture/rendering.py`, and the narration comments that name the speech engine's version;
- `README.md`, `NOTICE`, `CHANGELOG.md` and `VERSION`.

A film adopts 0.5.0 only when it builds, reviews and accepts an edition on it, and it must raise its own `hyperframes` pin. The release is therefore minor.

The tag, its publication and the Release pages follow the landed source and are not tasks of this Change. `tasks.md` is the sole progress ledger.
