## Why

`python -m filmkit.durations` states what a build took, and a budget is judged by it. A convergence narrates an edition more than once, with a judgment after each narration and a round of candidates between them, and writes no duration record of its own; each narration it runs replaces the record `narrate`, where the build's sum begins. So the sum of a converged edition starts at its last narration and leaves out everything before it. In the whole-edition trial of 19 November 2026 the essentials film's English edition showed 41.0 s for its narration where its convergence had held 343 s, and the build's counted commands came 369 s short of what its tickets held.

## What Changes

- **A convergence writes a duration record**, `converge`, with the seconds of its narrations, its judgments, its candidates and its count of the runtime as phases.
- **A build starts at the convergence that narrated it.** Where an edition's latest whole narration ran inside a convergence, the build's sum begins at that convergence's start and counts the convergence; the narration's own record is listed as inside it and is not added again. An edition narrated without a convergence is counted as before.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `build-time`: a convergence records how long it took, and a build's start and sum take the convergence that ran its narration.

## Impact

- `src/filmkit/narration/converge.py`, `src/filmkit/durations.py` and their tests; the README's paragraph on duration records and the Changelog.
- No film's bytes and no check's verdict depend on a duration record. A film that converges reads a larger and true sum from its next build.
- Out of scope: a budget's value, and what a convergence should take.
