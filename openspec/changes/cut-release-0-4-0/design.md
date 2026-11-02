# Design

## Context

See [proposal.md](proposal.md). `refresh-renderer` moved HyperFrames to 0.9.3 and kept Chrome Headless Shell 152.0.7977.30 and the `undici` 7.30.1 override, because 0.9.3 still declares that build and pins `undici` 7.25.0 exactly. `CONTRIBUTING.md` keeps notes under `Unreleased` and dates the heading only when the release is cut. `ethos land --release` cuts a signed `v*` tag from the accepted head, and `ethos publish` sends the branches and the tag to GitHub and GitLab, each with a source-only Release page.

## Goals / Non-Goals

**Goals:**

- Each lock at the newest release that its declared ranges admit, with no advisory that OSV reports for a locked package.
- One dated `[0.4.0]` entry that a film owner reads as the release notes, and one version stated everywhere the repository names it.

**Non-Goals:**

- Changing the engine, its specifications, its checks or any declared range.
- Moving any film's pin. Each film moves its own when it adopts the release.

## Decisions

- **The native resolvers decide the locks.** `npm update --package-lock-only` and `uv lock --upgrade` move each package to the newest release its dependents' ranges admit. A newer major that a range excludes, such as `undici` 8, stays out until its dependent accepts it; the registry's newest release is not a target in itself.
- **The browser build and the override stay.** The build follows the renderer's declaration, and the override stays on the newest 7.x release until HyperFrames accepts a fixed `undici` itself.
- **Minor, not patch.** A film that adopts 0.4.0 must raise its own `hyperframes` pin to 0.9.3, because the engine refuses any other renderer, and the new renderer can change the frames a film renders. Until 1.0.0 a minor release carries such a change.
- **The sample film is built again.** The npm moves lie in the renderer's dependency tree, so the sample film is built and verified on the refreshed locks before the release.
- **Hosted checks precede the tag.** The release head goes to dev and main on both peers and passes their CI before `ethos land --release --tag v0.4.0` signs the tag, so the tag names a commit that both forges have verified.

## Risks / Trade-offs

- [The new renderer changes a film's frames] → The films pin filmkit by tag and move only after they build, compare and accept an edition, as `CONTRIBUTING.md` requires.
- [A hosted check fails after dev and main are published] → No tag exists yet; the fix lands as a normal change, and the tag goes to the fixed head.
- [GitLab's runners are being upgraded on the evening of the release] → The tag waits until the GitLab pipeline of the release head has passed.
