## Context

See [proposal.md](proposal.md). The proof's behaviour gate runs `python -m pytest -q -W error tests` in an environment of its own; `mise run check` runs the same suite without `-W error`. A `ResourceWarning` for a file left open is raised when the object is collected, so it fails the test during which the collection happens.

## Goals / Non-Goals

**Goals:**

- The suite passes with warnings as errors, as the proof runs it.

**Non-Goals:**

- Changing what `mise run check` runs. Whether the repository's check should hold the proof's line on warnings is decided with the hosted runs in view, in a later Change: a warning that only a hosted runner's environment raises would turn a release's runs red.

## Decisions

1. **The count reads the file inside a `with` block.**
   - **Rests on:** the proof's record of 18 November 2026 on `aa416b2` (2 failed, 1,477 passed, 130 skipped; the failures name `ground.py` line 305) and the same six tests failing and passing on a clone of that head with `-W error`, before and after the repair.
   - **Considered:** (a) reading the text whole with `read_text`, which holds a film's measures in memory, a line for each plane of each frame; (b) a `with` block round the generator.
   - **Chosen because:** (b) keeps the count streaming and closes the file where it was opened.
   - **Applies to:** `picture/ground.py`, `ground_check`. The module's other reader, `departures`, already reads inside a block.

## Risks / Trade-offs

- Another warning may stand in code the proof's environment skips (121 tests there need FFmpeg). → The whole suite was run with `-W error` on a host with FFmpeg after the repair, and no test failed on a warning.
