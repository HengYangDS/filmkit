## Why

Two habits that decide whether a Change's checks hold stand only in a session's notes today. The step check of a
release reads a code step's focused tests from the test files its Change's tasks name, so a Change whose tasks name
none gets no focused test (20 November 2026). And a new check is proved on the films it will judge only when someone
remembers to run it there: on 2 November that run found two defects the tests had missed, and the adoption reader and
the still scan of 0.25.0 and 0.26.0 were accepted by it. OpenSpec's per-artifact rules are where such a rule reaches
every author of a Change; the repository paradigm requires only that its common rules come first, and a repository's
own rules follow them (`openspec_gaps` in ETHOS's `repository/paradigm/openspec.py`, read by the repository steward
on 21 November 2026 at ETHOS `e4d9d04d3`).

## What Changes

- `openspec/config.yaml`, `rules.tasks`, after the paradigm's three common rules and without touching them:
  - a task that verifies code names the test file that verifies it, as a path in backticks;
  - a Change that adds or changes a check carries an acceptance task that runs the check on its real consumers, the
    released films for an engine check, with the record under `build/evidence/<change>/`.

Considered: asking ETHOS to add both to the paradigm's common rules first. Not chosen now because the steward takes
them as candidates for the common rules once one repository has carried them through a lane; this repository is that
first consumer, and the films keep the common file until the paradigm carries the rules.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No engine behaviour or film output changes, so `.openspec.yaml` sets `skip_specs: true`.

## Impact

- `openspec/config.yaml` only. The rules guide the artifacts of later Changes; the Changes of this release already
  follow them.
- Out of scope: a new capability's `## Purpose`, which the archive refuses and strict validation does not, a parity
  gap of ETHOS's readiness that the steward passed to ETHOS's product session on 21 November 2026; the films'
  `openspec/config.yaml`; the form of a design decision, which ETHOS's direction carriers own.
