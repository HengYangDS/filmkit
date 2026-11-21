## Context

See [proposal.md](proposal.md). `.config/ci/verification.toml` holds the hosted jobs' Mise release,
and ETHOS's common model generates the pipelines from it. Mise 2026.11.10's release notes add
`mise lock --check`, an `enable_backends` allowlist and `filter_bins` for `http:` tools, and change
two behaviours: `mise lock --dry-run` now resolves every tool, and a `[tool_config] locked = true`
lockfile is left alone after installs. Neither touches the locked install the hosted jobs run. Its
fixes include jdx/mise#15838: `mise x -- <cmd>` runs the pinned tool's binary again when the
inherited `PATH` already contains that tool.

## Goals / Non-Goals

**Goals:**

- Install Mise 2026.11.10 in the hosted jobs that bootstrap Mise.

**Non-Goals:**

- Changing any gate, check, publication, runner declaration or tool release.
- Changing the lockfile format; no step runs `mise lock --upgrade`.
- Raising the Mise floor, which states the oldest Mise that reads this configuration.

## Decisions

- Move only `[supply] mise_version`, as a second Change of the beta.11 rebind lane, so that one
  proof and one pair of hosted runs cover both moves; the native projection regenerates the
  pipelines.

## Risks / Trade-offs

- [Mise 2026.11.10 changes the hosted bootstrap] → The proposal's hosted runs on both Forges qualify
  it before landing; restoring the earlier parameter rolls it back.

## Migration Plan

Move the Mise parameter, generate the pipelines, prove the archived head and qualify it on both
Forges' jobs with the rebind. To roll back, restore the earlier parameter.
