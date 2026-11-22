## Context

See [proposal.md](proposal.md) and the `engine-distribution` delta. The `test` script of
`package.json` is what `mise run check`, the hosted jobs and ETHOS's JavaScript gate run for the
engine's Node tests.

## Goals / Non-Goals

**Goals:**

- A test file that follows the naming pattern runs without being added to a list.

**Non-Goals:**

- Moving, renaming or changing any test, or changing how a film's own tests are found.
- Changing the runner, its concurrency or its reporter.
- Running the script under a shell other than `sh`.

## Decisions

- Node's own runner expands the pattern (`node --test 'tests/**/*.test.mjs'`). The single quotes
  keep `sh`, the shell in which npm runs a script on macOS, from expanding it first; ETHOS's recipe
  reader starts Node with no shell and passes the pattern as one argument. Either way the runner's
  own expansion decides the selection. Alternatives considered: a generated list with a test that
  compares it with the folder, which keeps a second copy of one fact beside a check; and the
  runner's default discovery with no argument, which searches the whole repository by several name
  patterns and is not limited to `tests/`.
- The pattern is the one place that says which files are the engine's Node tests.

## Risks / Trade-offs

- [A helper named `*.test.mjs` below `tests/` would run as a test] → Helpers keep other names, as
  they do today.
- [A Node release that does not expand patterns] → The repository pins Node in Mise's lock, and the
  pinned release expands them.
- [Under `cmd.exe`, which npm's documentation names as its script shell on Windows, single quotes
  are no quotation; the pinned Node, given the pattern with its quotes kept, runs no test and exits
  0] → The engine runs on Apple-silicon macOS, and both forges' jobs run there; nothing runs the
  script under `cmd.exe`. A consumer on another shell changes the quotation with it.

## Migration Plan

Replace the list by the pattern and confirm that the run by the pattern selects the same files and
the same number of tests as the run by the list. To roll back, restore the list.
