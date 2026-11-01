# Proposal

## Why

The repository declares and runs ETHOS 0.2.0-alpha.21. The owner asked that every governed repository run the latest ETHOS release, now 0.2.0-alpha.25, and that every line ceiling be 500. Since 0.2.0-alpha.23 the code ceiling bounds JavaScript as well, and four files exceed it: `tests/picture/picture.test.mjs` at 1,359 effective lines, `src/filmkit/picture/frame-audit.mjs` at 772, `geometry-check.mjs` at 609 and `motion-audit.mjs` at 580. They are maintained engine code, so the repository splits them by what each part owns and declares no higher value. 0.2.0-alpha.25 also adds Ruff's unspecified-encoding rule to its managed configuration, which reports eight calls in the Python tests.

## What Changes

- Move the frame rules and the reviewers' measures that `geometry-check.mjs` holds to `src/filmkit/picture/rules/`, one module per concept: ink, balance, frame and names. `geometry-check.mjs` keeps the page instrumentation, the page program and its command.
- Split `frame-audit.mjs` below `src/filmkit/picture/frame-audit/` into the marks it reads, the composition measures and its report, and move `motion-audit.mjs`'s analysis and report to `src/filmkit/picture/motion-audit/report.mjs`. The tools keep their names, their entry paths and their output bytes.
- Split `tests/picture/picture.test.mjs` by subject: the rules, the headless composition, the geometry check, the frame audit, the motion audit, the seat check and the tools' invocations, over a shared sample-film helper.
- Name `encoding="utf-8"` at the eight calls that Ruff reports.
- Replace the 0.2.0-alpha.21 declaration in `.config/mise/config.toml` with the one published with 0.2.0-alpha.25, lock it, and bind the repository family to that runtime, keeping 0.2.0-alpha.21 as the rollback.
- Regenerate the CI projection, whose Mise action pin 0.2.0-alpha.25 moves.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine behaves as before and no film's output changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

- The picture tools' modules and their tests, `package.json`'s test command, three Python test files, `.config/mise/config.toml`, `.config/mise/mise.lock`, `.github/workflows/ci.yml`, `CHANGELOG.md` and the repository-common runtime selection.
- The change lands on the local `dev` only; public pushes of this repository wait for the user's approval. The films pin filmkit v0.1.1 by tag, so none of them moves until it adopts a later release under its own reproduction standard.
- `tasks.md` is the sole progress ledger.
