## Context

See [proposal.md](proposal.md). `openspec/config.yaml` carries OpenSpec's per-artifact rules, and
OpenSpec shows an artifact's rules to whoever writes that artifact, so a rule there reaches every
author of a later Change without a second document. Its `rules.tasks` begins with the repository
paradigm's three common rules, which the paradigm's report requires to come first.

## Goals / Non-Goals

**Goals:**

- State the two habits where a Change's tasks are written, after the paradigm's common rules.

**Non-Goals:**

- Changing the paradigm's common rules, another artifact's rules, or a film's `openspec/config.yaml`.
- A gate that refuses a task without a test path or a Change without an acceptance task.

## Decisions

- The two rules are appended to `rules.tasks` of this repository's `openspec/config.yaml`; the three
  common rules before them stay byte for byte as the paradigm ships them. Alternative considered:
  asking ETHOS to add both to the common rules first. Not taken now, for the reason the proposal
  gives: the steward takes them as candidates once one repository has carried them through a lane.
- `.openspec.yaml` sets `skip_specs: true`: the rules change no engine behaviour and no film output,
  so no capability's requirement changes.

## Risks / Trade-offs

- [A later paradigm release ships the same rules as common rules] → The repository's two rules are
  removed in the lane that adopts that release, so that each rule keeps one source.
- [A rule that no gate reads is forgotten] → No gate reads either rule. A task that names neither a
  test file nor a command is met by whoever lands or reviews its step, person or tool, who finds no
  focused test in the task; the acceptance task is read when the Change is reviewed.

## Migration Plan

Append the two rules, validate strictly and read the paradigm's report. To roll back, remove the two
rules.
