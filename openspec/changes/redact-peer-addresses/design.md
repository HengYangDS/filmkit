## Context

See [proposal.md](proposal.md). The redaction verb works only inside the effective record roots:
the paradigm's immutable `openspec/changes/archive/` plus the profile's `record_roots`. On 12
November 2026 a keyless preview of `00939f5` under 0.2.0-beta.8 found two occurrences, one peer URL
on `proposal.md` line 9 and one on `tasks.md` line 5 of the archived Change
`2026-11-01-refresh-repository-entry`, both inside the roots. The verb derives the protected peer
from the checkout's local Git configuration, so it runs in the lane, a worktree of the canonical
checkout.

## Goals / Non-Goals

**Goals:**

- No current tracked file names the GitLab peer's host, port or project path.
- Every redacted occurrence carries a keyed marker that the owner's key verifies.

**Non-Goals:**

- Rewriting published history or any remote ref.
- Turning on `[peer_identity] mode = "required"`, which takes its own decision.
- Changing any other content of the archived Change.

## Decisions

- Read the owner's key from the login Keychain only into `--key-stdin`; it never reaches an
  argument, a log or a file.
- Commit the redaction alone, then verify with `--verify --key-stdin --base <base> --head <head>`
  from its parent, which re-derives the head and records the `redaction:private-peer` Attestation.

## Risks / Trade-offs

- [The verb meets an occurrence it cannot classify] → Apply refuses and changes nothing; the lane
  stops and the occurrence goes to ETHOS's owner.

## Migration Plan

Preview, apply, commit the redaction alone, preview for zero, verify, prove the archived head,
publish the proposal, land, publish `dev` and `main`, and retire the proposal refs and the lane.
To roll back, revert the lane's commits.
