## Context

See [proposal.md](proposal.md). ETHOS's gate `native-behavior` runs the Node suite once under c8 and requires each JavaScript file that it selects to appear in the coverage report [S2]. At `0b941b1` it selected 44 files, and the report lists 43 of them; `src/filmkit/picture/anchor-reads.mjs` is the one absent [S1]. The module is a command: at load it reads its arguments from `process.argv`, writes its report and ends the process with `process.exit`, and `filmkit.picture.anchor_reads` starts it with the film's timeline and a step.

## Goals / Non-Goals

**Goals:**

- Every line of `src/filmkit/picture/anchor-reads.mjs` runs in the run that the gate measures.

**Non-Goals:**

- Changing the tool, the gate's rule or the roles that the repository declares for its files.

## Decisions

1. **A test runs the tool as its caller runs it, a Node process started with a timeline and a step in a film's folder.**
   - **Rests on:** the proof's gap [S1]; the gate's rule [S2]; the new test's mutants and its measure [S3].
   - **Considered:** (a) running the tool as a command in a child Node process, as its caller does; (b) importing the module in the test's process; (c) declaring the file a carrier that owes no coverage, by an `ethos-role` attribute in `.gitattributes`; (d) splitting the module into an importable function and a thin command.
   - **Chosen because:** (a) holds the tool's interface, its arguments, report and exit status, and c8's measure of the test reports every line of the module run [S3]. (b) would run the module's top level with the test runner's arguments and end the runner's process with `process.exit`. (c) would declare authored engine code something else. (d) changes engine code in a repair that needs none.
   - **Applies to:** `tests/picture/anchor-reads.test.mjs`.
   - **Reopened when:** the gate stops measuring the processes a test starts, or the tool gains an importable interface.

## Risks / Trade-offs

- Another file could be missing from the report of the whole run. → The gate's report at `0b941b1` lists every other selected file [S1].
- The test starts five Node processes, so it costs more than an import. → Each takes tens of milliseconds [S3].
- The gate runs only in the full proof, and the readiness does not run it. → The repair is shown by the new test measured under ETHOS's c8 [S3]; the next proof decides.

## Sources

Read or measured on 23 November 2026. Paths under `build/evidence/run-the-anchor-reads-tool-in-its-tests/` are the canonical checkout's local evidence.

- **[S1] The proof:** ETHOS 0.2.0-beta.11 on `0b941b1`, queued at 16:30:53 and refused at 16:41:18 CST in its gate `native-behavior` with `quality_behavior_javascript_coverage_scope_incomplete` (`proof-0b941b1.err`). The gate's artifact in ETHOS's store of the canonical checkout's Git common directory holds its observation and its coverage summary; `gate-coverage-0b941b1.txt` lists the 44 selected files and the one of them absent from the summary.
- **[S2] The gate's rule:** ETHOS 0.2.0-beta.11, `ethos/adapters/gates/javascript/behavior.py` (`_observe_coverage`), which runs the Node suite under the c8 that ETHOS ships and reports the selected files that its coverage report lacks; the code's owner is `repository.policy` (`ethos/contracts/codes/gaps.toml`).
- **[S3] The new test:** `red-four-broken-copies.txt`, the test against four broken copies of the tool (1, 2, 1 and 1 of its five tests fail) and against the tool unbroken (5 passed); `green-c8-e660ace.txt`, the test under ETHOS's c8 at 17:03:26 (5 passed; `anchor-reads.mjs` 100 % of its lines, 93.75 % of its branches); the commit as a patch, `0001-test-picture-exercise-the-anchor-recorder-through-it.patch`.
