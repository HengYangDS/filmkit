## Context

See [proposal.md](proposal.md). The gate `native-behavior` reads Node's coverage of the Node tests through c8 and refuses a report whose files are not exactly the production JavaScript files it selected [S2]; `src/filmkit/graph/opens.cjs` is among them [S1] and appears in no Node test's coverage [S4].

## Goals / Non-Goals

**Goals:**

- A Node test loads the recorder, so that its coverage is reported, and states what the recorder writes.

**Non-Goals:**

- Changing the recorder, its Python half or the gate's rule.

## Decisions

1. **Test the recorder in a child under the permission model and in the test's own process.**
   - **Rests on:** the gap [S1], the gate's rule [S2], the recorder [S3] and the missing coverage [S4].
   - **Considered:** (a) children only, as the engine starts Node; (b) the test's own process only; (c) both; (d) leaving the file out of the gate's selection.
   - **Chosen because:** (c) tests what the permission model publishes, which only a child under `--permission-audit` shows, and gives the coverage that such a child does not write. (a) leaves the report as it is. (b) never meets the permission model. (d) would hide production code from the behaviour gate.
   - **Applies to:** `tests/graph/opens.test.mjs`.
   - **Reopened when:** Node writes coverage from a child under the permission model, or the recorder changes its channel.

## Risks / Trade-offs

- Another production JavaScript file could be added without a Node test and fail only in the proof. → The films session's brief for code builders now asks that every production JavaScript file be loaded by a Node test before hand-back (outside this repository).
- The in-process test publishes on Node's own channel by hand, so a change in what Node publishes would not show there. → The child test reads what Node itself publishes.

## Sources

- [S1] The proof of `7f8d6b7`, 24 November 2026, released 19:30:06 CST: `gate_failed:native-behavior`, `quality_behavior_javascript_coverage_scope_incomplete`; its JavaScript selection names `src/filmkit/graph/opens.cjs`.
- [S2] ETHOS 0.2.0, `ethos/repository/policy/quality_reports.py`, `istanbul_coverage_report`: the report's files must equal the selected production files, or `javascript_coverage_scope_incomplete`.
- [S3] `src/filmkit/graph/opens.cjs`, added by `8deb8d9` (`record-every-run`).
- [S4] A c8 run over a child under `--permission-audit` on 24 November 2026: the raw coverage holds the test process's file and no file of the child.
