## Context

See [proposal.md](proposal.md). The gate `native-behavior` selects the repository's JavaScript and requires each file it selects to be a test, or to carry a declared role [S1]. The two files the proof names are modules that the Node tests import [S2]; the repository already declares two such modules as `ethos-role=tooling` [S3].

## Goals / Non-Goals

**Goals:**

- The two modules carry the role that the repository gives its other test modules.

**Non-Goals:**

- Changing a test, the modules or the gate's rule.

## Decisions

1. **Declare the two modules as `ethos-role=tooling`, as the two before them.**
   - **Rests on:** the gap [S1], the modules' use [S2] and the repository's declarations [S3].
   - **Considered:** (a) the same declaration as `tests/picture/sample-film.mjs`; (b) renaming each module so that the test runner runs it as a test; (c) folding each module into the tests that import it.
   - **Chosen because:** (a) states what the modules are, a test's support, in the place that states it for the others. (b) would run modules that hold no test. (c) repeats the sample film's binding in four tests and the lead words in one, where one module now states each once.
   - **Applies to:** `.gitattributes`.
   - **Reopened when:** the gate gives test modules another role.

## Risks / Trade-offs

- Another undeclared module could be added later and fail only in the proof. → The films session's release tool now asks, before the proof's ticket, that every JavaScript file below `tests/` that is not a test carries a role (outside this repository).

## Sources

- [S1] The proof of `e377a2d`, 24 November 2026, released 10:42:48 CST: `gate_failed:native-behavior`, `quality_behavior_javascript_native_test_scope_incomplete:tests/delivery/film.mjs,tests/picture/lead-words.mjs`.
- [S2] `tests/delivery/film.mjs`, imported by `tests/delivery/player.test.mjs`, `player-read.test.mjs`, `player-receipt.test.mjs` and `player-runtimes.test.mjs`; `tests/picture/lead-words.mjs`, imported by `tests/picture/breaks.test.mjs`.
- [S3] `.gitattributes` at `e377a2d`, lines 2 and 3.
