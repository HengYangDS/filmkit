# Design

## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from `RENDERER_VERSION`. `filmkit.supply` installs the browser build that the locked renderer pins and checks its executable against `BROWSER_SHA256`. The narration calls the speech engine's Qwen3-TTS generator, and calls the vendor's own ICL generator when a cast declares a repetition penalty below the public generator's floor. HyperFrames' only breaking change between 0.8.150 and 0.8.225 is in its inspector package (0.8.156), which the engine does not use.

## Goals / Non-Goals

**Goals:**

- Every declared package and tool stands at its latest stable release, within the Python 3.12 line that the films select.
- The sample film builds and verifies end to end on the new supply, in both editions.

**Non-Goals:**

- Changing the engine's contract, any declaration field or the films' own pins.
- Publishing, tagging or releasing this repository.

## Decisions

### One Change moves the whole supply

The renderer, its browser driver and the browser build move together, because the renderer depends on the driver and pins the build. The speech engine moves with the lock refresh, which would move MLX under it in any case. A single acceptance run covers all of them: the tests, then the sample build of both editions from supply to verification.

### The pins follow what the new releases ship

The renderer pin takes the version installed. The browser pin and `BROWSER_SHA256` take the build HyperFrames 0.8.225 declares, which is still Chrome Headless Shell 152.0.7977.30. The narration keeps its calls only where 0.6.3 keeps their signatures and behaviour. 0.6.3 still raises an ICL penalty below 1.5 in its public generator, and its private ICL generator takes the same arguments, so only the comments that name the version change.

### An override fixes the renderer's pinned HTTP client

HyperFrames 0.8.225 pins `undici` 7.25.0 exactly. 29 advisories affect that release, and 7.30.1, the latest 7.x release, fixes all of them. The repository's npm `overrides` select 7.30.1, the same major version HyperFrames asks for, until a HyperFrames release accepts a fixed `undici` itself. A film that declares HyperFrames needs the same override, so the README states it.

### The sample build is the acceptance

Unit tests use stand-ins for the renderer, the browser and the models. Only the sample build runs the real renderer, browser and speech models. It reads the models from its tool cache, filled by `filmkit.supply` from the pinned revisions, and it passes when `sample:verify` passes for both editions.

## Risks / Trade-offs

- [The new speech engine changes the narration a seed produces] → The sample regenerates its narration from its seeds. The films keep v0.1.1 until they accept an edition on the new engine, and the Changelog says so.
- [The renderer's capture changes the frames] → The sample's geometry check, cover check and validation run on the new frames; the films keep v0.1.1 as above.
- [A vendor's private generator changes its signature] → The installed 0.6.3 source is read before the call is kept, and the sample's Chinese cast exercises that path.

## Migration Plan

Edit the declarations, lock them, check the locks for advisories, install, adjust the pins and the narration to the installed releases, run the tests and the sample build, prove the archived head, land and close out. To roll back, restore the previous declarations and locks; the supply then reinstalls the previous browser build.
