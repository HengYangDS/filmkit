# Design

## Context

See [proposal.md](proposal.md). ETHOS reads the publication peers from `.ethos/release.toml`; a peer's `forge_repository` is the address its Forge API is reached at, and `git_remote` names the local remote that carries its objects. ETHOS's repository paradigm requires `AGENTS.md` and `README.md` and admits `CONTRIBUTING.md` as a root entry document. In an entry document, every command in a shell block must be one the repository declares.

## Goals / Non-Goals

**Goals:**

- The release declaration names each peer where it now lives.
- Current entry documents link to the DDWG film repository by its current name.
- A maintainer who has not worked on filmkit can prepare the tools, make and verify a change, commit it and release it from `CONTRIBUTING.md` alone, without reading Agent guidance.

**Non-Goals:**

- Rewriting history: released Changelog entries, archived Changes and the sample film keep the name they recorded.
- Repeating the README's account of the engine, its commands and a film's layout.
- Any engine, test or film output change.

## Decisions

**The guide states the repository's own contract and points to ETHOS for the rest.** It names the engine boundary from `AGENTS.md`, the declared Mise tasks, the full proof that `.ethos/release.toml` declares as the local verification, the commit grammar and signature ETHOS enforces, and the release order this repository has used. It does not restate ETHOS's command reference, which changes with each ETHOS release.

**Shell blocks hold only declared commands.** ETHOS checks every command in an entry document's shell blocks against the repository's declarations, so the guide's blocks use the Mise tasks, the Homebrew installation the README already shows, and the declared verification command. Other commands appear in prose.

**Historical references keep their names.** The sample film's source manifest and texts, and the 0.1.0 Changelog entry, describe `ddwg-film` at commit `37549a9`. Changing them would rewrite what those records observed and the sample film's output, while GitHub's redirect keeps the old address resolvable.

## Risks / Trade-offs

- [The guide drifts from the repository] → It names only declared tasks and commands, which the repository's checks read, and it defers ETHOS's procedures to ETHOS.
- [The private GitLab address is published] → It already appears in the published `.ethos/release.toml`; only its path changes.
