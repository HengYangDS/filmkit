## Context

See [proposal.md](proposal.md). `.config/mise/config.toml` declares node, and
`.config/mise/mise.lock` pins its archive and checksum for each platform. Node runs filmkit's Node
tests, its Markdown formatter and the picture pipeline's renderer; the narration path runs in
Python.

## Goals / Non-Goals

**Goals:**

- Run filmkit on Node 26.13.1, the security release of the declared line.
- Ship the move as release 0.21.2.

**Non-Goals:**

- Moving any other tool or package; uv 0.13.8 becomes a day old on 14 November and moves in the next
  supply lane.
- Changing any source, test, film or runner declaration.

## Decisions

- Change only the declaration and let `mise lock` write the new archives and checksums; refuse the
  result unless only node's entries change, its platforms stay the same and the lockfile version
  holds, and compare its checksums with Node's `SHASUMS256.txt`.
- Accept the move with `mise run check` and a full `mise run sample:build`, which renders both
  editions through the picture pipeline on the new Node.
- Version 0.21.2 is a patch: no declaration, command or output changes.

## Risks / Trade-offs

- [Node 26.13.1 changes a test, a format or a render] → The check and the sample build fail before
  the commit; restoring the previous declaration and lock rolls it back.

## Migration Plan

Move node, check, build the sample film, prepare 0.21.2, prove the archived head, publish the
proposal, land, publish `dev` and `main`, tag v0.21.2 and publish its Releases. To roll back, revert
the lane's commits.
