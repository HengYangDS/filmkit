## Context

See [proposal.md](proposal.md). The move follows ETHOS's successor-first adopter cutover: bind the
release in the lane, prove, publish the proposal from the lane, then land and publish from the
canonical root. Between 0.2.0-beta.8 and 0.2.0-beta.9 the embedded OpenSpec moves to 2.0.0 and the
redaction scan is shared; the common CI model is unchanged.

## Goals / Non-Goals

**Goals:**

- Run every gate and lifecycle command of the family, locally and in the hosted macOS jobs, on
  0.2.0-beta.9.
- Keep the 0.2.0-beta.8 runtime as the rollback until the landing is accepted.

**Non-Goals:**

- Changing any source, test, film, check or runner declaration, or the hosted jobs' Mise.
- Turning on `[peer_identity] mode = "required"`.

## Decisions

- Copy the release's own declaration unchanged and lock it with native `mise lock`, after checking
  each platform checksum against the release's `SHA256SUMS` and the published asset digests; the
  lock stays at version 3 because locking an existing lock again keeps its version.
- Check the pipelines with `ethos lane project --check`; a difference would come only from the
  release's common model and is taken through `ethos lane project --apply`.

## Risks / Trade-offs

- [A gate that passed under 0.2.0-beta.8 fails under 0.2.0-beta.9] → The lane runs the gates after
  the bind, and the full proof runs at the archived head before landing. A failure is repaired at
  its owner, or the family restores the 0.2.0-beta.8 declaration in a new Change and binds the
  retained runtime.

## Migration Plan

Copy the declaration, lock it, install the locked supply, bind the runtime, check the pipelines, run
the gates, prove the archived head and qualify it on GitHub's and GitLab's macOS jobs. To roll back,
restore the 0.2.0-beta.8 declaration and lock in a new Change, then bind the retained runtime with
the current console's `hook install --runtime <0.2.0-beta.8 runtime>`.
