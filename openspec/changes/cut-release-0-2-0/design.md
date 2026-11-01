## Context

See proposal.md for why 0.2.0 is cut now. `CONTRIBUTING.md` keeps notes under `Unreleased` and
dates the heading only when the release is cut. `ethos land --release` cuts a signed `v*` tag from
the accepted head. `ethos publish` sends the branches and the tag to GitHub and GitLab, and each
gets a source-only Release page.

## Goals / Non-Goals

**Goals:**

- One dated `[0.2.0]` entry that a film owner reads as the release notes, and one version stated
  everywhere the repository names it.

**Non-Goals:**

- Changing the engine, its specifications or its checks.
- Rewriting earlier releases' notes, or moving any film's pin. Each film moves its own pin after it
  rebuilds and compares.

## Decisions

- **Minor, not patch.** The refusal of abrupt thought takes is incompatible for a film that binds
  such a take. Until 1.0.0, `CONTRIBUTING.md` lets a minor release carry such a change, so the
  release is 0.2.0.
- **The notes stay as landed.** Each entry was written when its change landed and still states the
  released behavior. That includes the breaking entry's statement that a film whose takes all end
  naturally assembles the same soundtrack as before. The Release pages repeat this section, as
  they did for 0.1.1.
- **Hosted checks precede the tag.** The release head goes to dev and main on both peers and passes
  their CI before `ethos land --release --tag v0.2.0` signs the tag. The tag then names a commit
  that both forges have verified.

## Risks / Trade-offs

- [A film pins v0.2.0 without rebuilding] → The Changed entries state that the new renderer and
  speech engine change the frames and narration, and that a film keeps its pin until it accepts an
  edition on this engine.
- [A hosted check fails after dev and main are published] → No tag exists yet. The fix lands as a
  normal change, and the tag goes to the fixed head.
