## Context

See [proposal.md](proposal.md). ETHOS's gate `native-behavior` runs the Python suite once under coverage and requires each tracked `.py` or `.pyi` file that is not a test, and that declares no other role, to appear in the report [S2]. Of the 110 such files at `1e4d459`, all under `src/filmkit/`, collecting the suite imports 109; the one it does not is `src/filmkit/register/__main__.py` [S3]. Its three statements import `main` and call it when the module runs as `__main__`.

## Goals / Non-Goals

**Goals:**

- Every line of `src/filmkit/register/__main__.py` runs in the process the gate measures.

**Non-Goals:**

- Measuring child processes under coverage, or a coverage configuration of the repository's own.
- Changing the gate's rule or the roles that the repository declares for its files.

## Decisions

1. **A test runs the package with `runpy.run_module`, as `python -m` runs it, in the test's process.**
   - **Rests on:** the proof's gap [S1]; the gate's rule [S2]; the collection, which leaves this file alone unimported [S3]; the register tests measured before and after the test [S4].
   - **Considered:** (a) running the module in the test's process with `runpy`; (b) running `python -m filmkit.register` in a child and measuring child processes; (c) declaring the file a carrier that owes no coverage, by an `ethos-role` attribute in `.gitattributes`; (d) removing `__main__.py`.
   - **Chosen because:** (a) runs the file's three statements in the measured process and adds nothing but a test. (b) needs a coverage configuration that the repository does not have and changes the measure of every run, for three lines that (a) runs. (c) would declare authored engine code something else. (d) would remove the command `python -m filmkit.register`, which the README and the Changelog of 0.27.0 document.
   - **Applies to:** `tests/register/test_register_check.py`.
   - **Reopened when:** the engine gains another module that runs only as `__main__`, or the gate's scope rule changes.

## Risks / Trade-offs

- Another file could be missing from the report of the whole run. → The files the gate requires were listed from the tree at `1e4d459`, and collecting the suite imports each of them except this one [S3]; a module imported at collection is measured by the run that follows it.
- The test replaces `check`, so it does not run the check itself. → Other tests of `tests/register/` run `check` on the sample film; this test holds only that the module runs `main` and keeps its output and its refusal.
- The gate runs only in the full proof, and the readiness does not run it. → The repair is shown by the register tests measured as the gate measures [S4]; the next proof decides.

## Sources

Read or measured on 22 November 2026. Paths under `build/evidence/run-the-register-entry-in-its-tests/` are the canonical checkout's local evidence.

- **[S1] The proof:** ETHOS 0.2.0-beta.11 on `1e4d459`, queued 20:15:55 and refused 21:45:06 CST; its gate `native-behavior` ran 2217 tests (none failed, 150 skipped) with 90.95 % combined coverage and reported `quality_behavior_coverage_scope_incomplete`. The gate's record is held in ETHOS's store of the canonical checkout's Git common directory; it does not keep the coverage report.
- **[S2] The gate's rule:** ETHOS 0.2.0-beta.11, `ethos/adapters/gates/python_quality.py` (`_behavior_scope`, `_behavior_gap`, `_native_configuration`) and `ethos/repository/policy/code_subjects.py` (`requires_behavior`): the required files are the tracked Python files that are not tests and whose `ethos-role` is unset, `code` or `generated`; the run measures `--cov=.` from the repository's root, since the repository has no coverage configuration, and a required file absent from the report fails the gate.
- **[S3] The collection:** `required-subjects-1e4d459.txt`, the 110 required files as [S2] selects them from the tree at `1e4d459`; `collect-1e4d459.txt`, the suite collected at `1e4d459` under coverage of `src/filmkit/` (2217 tests): the report lists the same 110 files, and `src/filmkit/register/__main__.py` is the one with no line run.
- **[S4] The register tests measured:** at `1e4d459`, `red-register-1e4d459.txt` (`--cov=src/filmkit/register`: 94 passed; `__main__.py` 3 statements, none run) and `red-register-root-1e4d459.txt` (`--cov=.`, as the gate measures: no row for `__main__.py`); `mutation-entry-runs-nothing.txt`, the new test against an entry whose guard runs nothing (1 failed, 64 passed); with the new test, `green-register-scratch.txt` (95 passed; `__main__.py` 100 % of its lines) and `green-register-root-scratch.txt` (`__main__.py` in the report, every line run).
