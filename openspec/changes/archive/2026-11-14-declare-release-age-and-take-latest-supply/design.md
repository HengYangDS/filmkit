## Context

filmkit declares its tools in `.config/mise/config.toml` and pins its Python and npm dependencies
exactly. uv installs the environment, coverage measures the Python tests, and Prettier formats the
repository's own Markdown in `mise run check` and `mise run fix`.

## Goals / Non-Goals

**Goals:**

- State the release age where the tool that applies it reads it.
- Run filmkit's checks and proof on the latest stable releases and release them as 0.21.3.

**Non-Goals:**

- Moving transformers, the picture supply or mlx-audio, which the film session keeps for releases
  that compare takes and frames.
- Retiring `format:markdown`; it retires in a later release once its OpenSpec globs are gone.

## Decisions

### The age is one line of Mise configuration

Mise applies a release age to every tool it resolves and reads it from `minimum_release_age`.
filmkit uses no other update proposer, so that line is the age's only tracked home; the uv and npm
locks take their cutoff from the same value when they are refreshed.

### Each move goes through the native resolver or lock

uv moves through `mise lock`, refused unless only uv's entries change. The exact pins move in
`pyproject.toml` and `package.json` and lock through `uv lock` and `npm update --package-lock-only`
at the declared age; `npm ls --all --include=dev` must report a consistent tree.

### The narration path moves only with a take comparison

A lock refresh at 0 hours would take transformers 5.23.0, so the uv lock is not refreshed past the
coverage pin. The film session's next filmkit release moves transformers with mlx-audio and compares
the sample film's takes.

## Risks / Trade-offs

- [A release a few hours old is broken or withdrawn] → Both locks pin every hash, OSV is read for
  both, and `mise run check` and the full proof run before landing; restoring the previous
  declarations and locks rolls it back.
- [Prettier 3.10 and ETHOS's 3.9.10 disagree on a later edit] → Both accept today's tree; a later
  disagreement fails one check before a commit, and filmkit then holds the file to the form both
  accept.
