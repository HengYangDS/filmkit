## Context

See [proposal.md](proposal.md). The move follows ETHOS's successor-first adopter cutover: bind the
release in the lane, prove, publish the proposal from the lane, then land and publish from the
canonical root. On 12 November 2026 a read-only preview of `fbe9843` under 0.2.0-beta.8, on a
disposable clone, found one repair edit, `.ethos/release.toml` losing six lines (`forge_repository`
in both peers, `local_installation_command` and `local_verification_command`), and no form of the
catalog change in the tracked files. A pre-check of `e62e799` under the 0.2.0-beta.8 candidate, with
those fields stripped from the clone, passed its bootstrap and full host proof.

## Goals / Non-Goals

**Goals:**

- Run every gate and lifecycle command of the family, locally and in the hosted macOS jobs, on
  0.2.0-beta.8.
- Remove the retired declaration fields, and with them the GitLab peer's address from the current
  declaration.
- Keep the 0.2.0-alpha.29 runtime as the rollback until the landing is accepted.

**Non-Goals:**

- Changing any source, test, film, check or runner declaration, or the hosted jobs' Mise.
- Redacting the GitLab peer's address from the archived Change
  `2026-11-01-refresh-repository-entry`, which waits for the owner's decision and a redaction key.
- A tag or a release.

## Decisions

- Copy the release's own declaration unchanged and lock it with native `mise lock`, after checking
  each platform checksum against the release's `SHA256SUMS` and the published asset digests.
- Bind first, then repair: the 0.2.0-beta.8 loader refuses the retired fields, and the repair
  removes them without echoing their values.
- Take the regenerated workflow only through `ethos lane project --apply`, so the `jdx/mise-action`
  pin comes from the release's common model.

## Risks / Trade-offs

- [A gate that passed under 0.2.0-alpha.29 fails under 0.2.0-beta.8] → The lane runs the gates after
  the bind, and the full proof runs at the archived head before landing. A failure is repaired at
  its owner, or the family returns to 0.2.0-alpha.29 as below.
- [The hosted jobs' Mise 2026.10.25 reads a lock written by a newer Mise] → The review jobs on both
  forges run on the proposal before landing; a refusal stops the landing.

## Migration Plan

Copy the declaration, lock it, install the locked supply, bind the runtime, repair the declaration,
generate the pipelines, run the gates, prove the archived head and qualify it on GitHub's and
GitLab's macOS jobs. To roll back, restore the 0.2.0-alpha.29 declaration, lock and the repaired
release declaration in a new Change first, since `hook install --runtime <older>` refuses while the
older runtime would refuse the repaired declaration, then bind the retained runtime.
