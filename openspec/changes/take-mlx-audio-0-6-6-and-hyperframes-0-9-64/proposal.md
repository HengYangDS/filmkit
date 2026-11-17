## Why

filmkit 0.23.0 narrates with mlx-audio 0.6.4 and renders with HyperFrames 0.9.46. Read on 18 November 2026, the newest stable releases are mlx-audio 0.6.6 (16 November) and HyperFrames 0.9.64 (17 November), with numpy 2.5.5, puppeteer-core 25.18.1, uv 0.13.9 and, in the uv lock, transformers 5.23.0, filelock 4.2.11, httpcore2 and httpx2 2.16.2 and regex 2026.11.15. The owner decided on 13 November 2026 that a governed repository takes the latest stable release of its supply; these moves were deferred twice, last to the release after 0.23.0.

Two of them change what a build produces or may produce. mlx-audio 0.6.5 keeps the frames whose first codebook id is 0 when it trims decoded audio, the fault that shortened takes by 80 ms a frame and that the README describes under "Whole endings"; the same release gives the speech tokenizer's decoder its sliding window, and 0.6.5 and 0.6.6 change how a sampler reads its inputs, so a take narrated from a seed is another take. HyperFrames draws every frame.

## What Changes

- Pin `mlx-audio` 0.6.6 and `numpy` 2.5.5 in `pyproject.toml` and refresh `uv.lock`, which also takes transformers 5.23.0, filelock 4.2.11, httpcore2 and httpx2 2.16.2 and regex 2026.11.15, and adds requests 2.34.2, urllib3 2.8.0, certifi 2026.10.23 and charset-normalizer 3.5.2, which mlx-audio 0.6.6 declares.
- Pin `hyperframes` 0.9.64 and `puppeteer-core` 25.18.1 in `package.json` and refresh `package-lock.json`; set the engine's `RENDERER_VERSION` to 0.9.64. HyperFrames 0.9.64 still declares Chrome Headless Shell 152.0.7977.30 and still pins undici 7.30.1, so the browser pin, its digest and the `undici` override stay.
- Declare uv 0.13.9 in `.config/mise/config.toml` and lock it again with `mise lock`.
- The README and `NOTICE` name the new versions, and the README's "Whole endings" says which release carries the upstream repair.
- **BREAKING** for a film's narration: a film that adopts this engine narrates its takes anew, since the same seed gives another take. A film that keeps its takes holds mlx-audio at its present version in its own lock, as the DDWG film does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine's commands, declarations, gates and output forms are unchanged, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

`pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, `.config/mise/config.toml`, `.config/mise/mise.lock`, `src/filmkit/picture/rendering.py`, two comments in `src/filmkit/narration/`, `README.md`, `NOTICE` and `CHANGELOG.md`. The sample film is built at 0.23.0's supply and again on the new one in the same lane, and the two builds are compared take by take and frame by frame. Out of scope: moving the browser build; `undici` 8, which HyperFrames does not declare; the native picture of the draft `faster-films-less-by-hand`, which will remove the renderer this Change moves. `tasks.md` is the sole progress ledger.
