# Design

## Context

See [proposal.md](proposal.md). `.config/mise/config.toml` declares the ETHOS release that CI
installs, and the repository-common Git directory selects the runtime that every worktree of the
family runs. Both name 0.2.0-alpha.27 today.

## Goals / Non-Goals

**Goals:**

- Run every gate and lifecycle command of the family, locally and in CI, on 0.2.0-alpha.28.
- Keep the 0.2.0-alpha.27 runtime available as the rollback until the landing is accepted.

**Non-Goals:**

- Changing the engine, a gate, a film's output or the engine's other supply pins.
- A release of filmkit; a later release carries this move with the engine changes it ships.

## Decisions

- Copy the release's own declaration unchanged and lock it with native `mise lock`. Each platform
  checksum is checked against the release's `SHA256SUMS` and the published asset digests first.
- Bind through the locked 0.2.0-alpha.28 console, so the selected runtime is the one the lock
  declares.
- Check the CI projection against the common model with `ethos lane project`, which reports it
  conforming, instead of editing the workflow by hand.

## Risks / Trade-offs

- [A gate that passed under 0.2.0-alpha.27 fails under 0.2.0-alpha.28] → The lane runs the
  0.2.0-alpha.28 gates after the bind, and the full proof runs at the archived head before landing;
  a failure is repaired at its owner, or the family binds the retained 0.2.0-alpha.27 runtime again.
- [A feature lane of the repository opened under 0.2.0-alpha.27] → It refreshes onto the landed
  bind before it lands, as the repository's owner agreed.

## Migration Plan

Copy the declaration, lock it, install the locked supply, bind the runtime, check the CI
projection, run the gates, prove the archived head, land, close out and publish dev and main to both
peers. To roll back, restore the 0.2.0-alpha.27 declaration and lock and bind the retained runtime
with its own console's `hook install --runtime <0.2.0-alpha.27 runtime path>`.
