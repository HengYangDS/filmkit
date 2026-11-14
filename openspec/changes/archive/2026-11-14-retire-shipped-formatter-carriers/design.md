## Context

See [proposal.md](proposal.md). In ETHOS 0.2.0-beta.10 the format gate renders each file with the
shipped policy and, when the repository carries its own, with that one as well; a difference
between the two renderings is refused. A carrier that equals the shipped policy, or holds a subset
of it, therefore cannot change a result.

## Goals / Non-Goals

**Goals:**

- Keep one copy of the Prettier, Ruff and Taplo settings, the one installed ETHOS ships.
- Show in this lane that every check and the full proof give the same result without the carriers.

**Non-Goals:**

- Changing any formatting or linting setting, engine source, gate or pipeline.
- Cutting a release: the removal ships with the next one.

## Decisions

- Remove the three files in one Change, because one proof covers them and they have one reason.
- Accept the removal only on evidence from this lane: the format check, the configuration gates,
  the repository's own check and the full proof must pass at the head without the carriers. If any of them asks for a
  carrier, the lane is abandoned and the finding goes to the paradigm's owner.

## Risks / Trade-offs

- [A later ETHOS release changes a shipped setting and reformats files here] → That is the
  intended behavior of a common base; the bind lane of that release applies the format and shows
  the difference in review.
- [A tool outside ETHOS reads the removed files] → No tracked file names them; the repository's
  own Markdown check passes Prettier its settings on the command line, and `mise run check` runs
  in this lane without them.

## Migration Plan

Remove the three files, update the Changelog, run the checks, prove the archived head and qualify
it on both Forges. To roll back, restore the three files from Git history in a new Change.
