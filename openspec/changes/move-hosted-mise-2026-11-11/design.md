## Context

See [proposal.md](proposal.md). `.config/ci/verification.toml` holds the hosted jobs' Mise release,
and ETHOS's common model generates the pipelines from it. Mise 2026.11.11's release notes add
opt-in features (MacPorts and self-update in `mise bootstrap`, `version_order = "published_at"`,
`exclude-newer = false` per PyPI index, `if_pool` task locks) and change no default that the hosted
jobs use. Of its fixes, the one nearest these jobs verifies `http:` tools that declare a
`checksum_url` and records that checksum in `mise.lock`; ETHOS's `http:ethos` table declares an
inline `checksum` for each platform instead, so the locked install and the lock are not affected.

## Goals / Non-Goals

**Goals:**

- Install Mise 2026.11.11 in the hosted jobs that bootstrap Mise.

**Non-Goals:**

- Changing any gate, check, publication, runner declaration or tool release.
- Changing the lockfile format; no step runs `mise lock --upgrade`.
- Raising the Mise floor, which states the oldest Mise that reads this configuration.

## Decisions

- Move only `[supply] mise_version`; the native projection regenerates the pipelines. The Change
  rides in the repository's next lane, or in a lane of its own when none is open, so that one proof
  and one pair of hosted runs cover it.

## Risks / Trade-offs

- [Mise 2026.11.11 changes the hosted bootstrap] → The proposal's hosted runs on both Forges qualify
  it before landing; restoring the earlier parameter rolls it back.

## Migration Plan

Move the Mise parameter, generate the pipelines, prove the archived head and qualify it on both
Forges' jobs. To roll back, restore the earlier parameter.
