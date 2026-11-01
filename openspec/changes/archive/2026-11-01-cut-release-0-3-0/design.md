## Context

See proposal.md for why 0.3.0 is cut now. `CONTRIBUTING.md` keeps notes under `Unreleased` and
dates the heading only when the release is cut. `ethos land --release` cuts a signed `v*` tag from
the accepted head. `ethos publish` sends the branches and the tag to GitHub and GitLab, and each
gets a source-only Release page.

## Goals / Non-Goals

**Goals:**

- One dated `[0.3.0]` entry that a film owner reads as the release notes, and one version stated
  everywhere the repository names it.

**Non-Goals:**

- Changing the engine, its specifications or its checks.
- Rewriting earlier releases' notes, or moving any film's pin. Each film moves its own pin when it
  adopts the checks.

## Decisions

- **Minor, not patch.** The release adds two checks, a new declaration field and a dependency,
  `pypinyin` 0.55.0. No existing declaration changes meaning, so no film needs a migration to keep
  building; a minor release states that new behaviour is available.
- **The notes stay as landed.** Each entry was written when its change landed and still states the
  released behavior, including that a film without a concept contract and with a version 1
  pronunciation contract narrates as before. The Release pages repeat this section, as they did for
  0.2.0.
- **Hosted checks precede the tag.** The release head goes to dev and main on both peers and passes
  their CI before `ethos land --release --tag v0.3.0` signs the tag. The tag then names a commit
  that both forges have verified.

## Risks / Trade-offs

- [A film pins v0.3.0 and its narration refuses] → The checks refuse only a film that declares a
  concept contract or a version 2 pronunciation contract, and each refusal names every failing
  place; the film then completes its declarations before it narrates.
- [A hosted check fails after dev and main are published] → No tag exists yet. The fix lands as a
  normal change, and the tag goes to the fixed head.
