## Why

The engine's Node tests are named one by one in `package.json`'s `test` script: thirty files, kept by hand. A new test
file that is not added there never runs, and nothing says so. Node's own test runner finds test files by a pattern
(`node --test 'tests/**/*.test.mjs'`), which selects exactly the same thirty files today
(`build/evidence/tooling-assessment-2026-11-20/engine-plumbing.md`, checked again on 20 November 2026: 225 tests, the
same result on either form).

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
