## Why

The engine's Node tests are named one by one in `package.json`'s `test` script: thirty files, kept by hand. A new test
file that is not added there never runs under `npm test`, and `npm test` does not say so; only the proof does, whose
JavaScript gate refuses a run that does not enter every test file it selects
(`javascript_native_test_scope_incomplete`). Node's own test runner finds test files by a pattern
(`node --test 'tests/**/*.test.mjs'`), which selects exactly the same thirty files today
(`build/evidence/tooling-assessment-2026-11-20/engine-plumbing.md`; run again on 22 November 2026, one file at a time:
235 tests in the same thirty files on either form). The 225 that the check of 20 November 2026 counted are the `test(`
call sites that start a line; five more stand in loops over two values and make ten tests.

## What Changes

- The `test` script runs `node --test 'tests/**/*.test.mjs'`: one pattern instead of a list.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `engine-distribution`: the engine's Node tests are the files the pattern finds.

## Impact

- `package.json`. ETHOS's JavaScript gate reads the recipe as `node --test` with one argument, its own native form.
  No film's bytes change.
