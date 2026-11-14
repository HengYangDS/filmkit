## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from
`RENDERER_VERSION` in `src/filmkit/picture/rendering.py`, and copies GSAP's minified script from the
npm packages into each staged picture document. The supply task installs the browser build that
`BROWSER` names and checks its SHA-256. The films adopt filmkit releases by tag.

## Goals / Non-Goals

**Goals:**

- Render with the newest stable HyperFrames and its newest npm inputs.
- Know, before the films adopt it, whether the move changes a frame of the sample film.

**Non-Goals:**

- Moving the browser build, transformers, mlx-audio or any Python package; transformers stays at
  5.22.2 by the film session's decision.
- Moving undici to its 8 line, which HyperFrames 0.9.46 does not declare.
- Changing any command, declaration, gate or output form.

## Decisions

- Read the browser build that HyperFrames 0.9.46 declares from its package before moving it:
  `CHROME_VERSION` is 152.0.7977.30, as in 0.9.9, so `BROWSER` and `BROWSER_SHA256` stay.
- Keep the `undici` override: HyperFrames 0.9.46 pins undici 7.30.1, and 7.30.2 is the newest
  release on that line.
- Accept the move by building the sample film at v0.22.0 and again on the new inputs in the same
  lane, each through every gate of `mise run sample:build`, then comparing each film frame by frame:
  frame counts, the number of differing frames and the largest sampled channel difference.
- Version 0.22.1 is a patch: no declaration, command or output form changes.

## Risks / Trade-offs

- [The new renderer draws a frame differently] → The comparison names each differing film and
  frame; the film session decides whether 0.22.1 ships before any film adopts it.
- [A render input moves under a gate] → `mise run sample:build` fails before the commit; restoring
  `package.json`, the lock and `RENDERER_VERSION` rolls the move back.

## Migration Plan

Build the baseline, move the pins, check, build the candidate, compare, prepare 0.22.1, prove the
archived head, publish the proposal, land after the film session reads the comparison, publish
`dev` and `main`, tag v0.22.1 and publish its Releases. To roll back, revert the lane's commits.
