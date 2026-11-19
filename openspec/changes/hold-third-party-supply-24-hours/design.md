## Context

See [proposal.md](proposal.md). Three resolvers supply the engine, and each reads a release age from its own configuration: Mise for its tools, npm for the Node packages, uv for the Python ones. The Change before this one wrote the first two at 72 hours and left uv's for a Change of its own, to be written with a relock once every artifact of the lock was old enough [S5]. An age is met when a version is resolved: a version that a configuration pins exactly and a lock holds installs as before, whatever its age [S5].

## Goals / Non-Goals

**Goals:**

- Each of the three resolvers reads 24 hours from this repository's own configuration.
- The uv lock holds the same packages and artifacts as before.

**Non-Goals:**

- Moving any pin or any locked version. Nothing is resolved again to a newer or an older version here.
- The exemptions for the owner's own repositories and tools and for a security fix. None is declared in this repository, as before [S5]; their mechanism is with the ETHOS product session (see Open Questions).
- The films' declarations, which the repository steward writes in the films' own lanes.

## Decisions

1. **The age is 24 hours, written in this repository's own three configurations.**
   - **Rests on:** the owner's decisions of 19 November 2026, as relayed [S1]; the rule of the Change before this one that each resolver reads the age from its own configuration and that no test or script holds it [S5].
   - **Considered:** (a) writing no age and taking the default of ETHOS's base, which the owner's second decision allows; (b) writing the age here.
   - **Chosen because:** Mise's setting reaches only Mise. The lines that npm and uv read here were written by the Change before this one [S5], and no record shows ETHOS's base supplying either resolver; (b) states the age where each resolver is known to read it.
   - **Applies to:** `.config/mise/config.toml` (`"24h"`), `.config/npm/npmrc` (`1`: npm counts the age in days [S5]) and `pyproject.toml`.
   - **Reopened when:** the owner sets another age, or ETHOS's base comes to write these lines for a governed repository.
2. **uv's line is declared now, as a span, with its relock in the same commit.**
   - **Rests on:** the lock's upload times, the youngest 46.8 hours old on 19 November 2026 at 13:24 CST [S2]; uv's reference, which accepts a duration such as `24 hours` for `exclude-newer`, resolves it to a fixed number of seconds and compares it with each distribution file's upload time [S3]; the relock in a scratch clone of `4893228`, which resolved 59 packages before and after with the same names, versions and artifacts, and wrote two options into the lock: `exclude-newer-span = "PT24H"` and a placeholder date that uv states has no effect [S4].
   - **Considered:** (a) a fixed date, which a person moves at every relock; (b) the span.
   - **Chosen because:** (b) is the age itself and no value kept by hand; the lock records the span and not the day it was written, so `uv lock --check` passed again a minute later and has no date to fall behind [S4].
   - **Applies to:** `pyproject.toml` and `uv.lock`, in one commit: `uv lock --check` refuses a lock whose options differ from the configuration's [S5].
   - **Reopened when:** a lock check refuses the lock for its cutoff on a later day or on a hosted runner; the line then takes a date.

## Risks / Trade-offs

- A release taken after one day has been run by fewer people than one taken after three. → The owner's trade, of iteration against the wait [S1]. What bounds it here is unchanged: exact pins, three locks, and a pin moved only by a Change that reads the version's publication time.
- The span was checked twice, a minute apart, on one host [S4]. → `mise run check:dependencies` runs the lock check on every hosted run of this repository, with the uv this repository pins, so a refusal shows on the proposal's runs before anything is tagged.

## Open Questions

- The exemptions as a mechanism. On 19 November 2026 the owner asked that they become one; the repository steward sent an inventory and a sketch to the ETHOS product session the same hour (relayed by the steward; kept in no file here). Owner: the ETHOS product session. Next action here: none until ETHOS states the form; this repository then declares what the form asks. Read again: 2026-11-21, the day the steward plans this repository's rebind to the next ETHOS release (relayed).

## Sources

Read or measured on 19 November 2026. Paths under `build/evidence/` are the canonical checkout's local evidence.

- **[S1] The owner's decisions, as relayed:** heard first-hand by the repository steward's session on 19 November 2026 (13:09:15 CST: the waiting time for supply updates of every governed repository goes from 72 hours to 24, since 72 hours are too long and slow iteration; 13:15:45 CST: a repository writes its own age, and otherwise the default of ETHOS's common base, 24 hours, holds) and sent by it to the engine's maintainer within the half hour. The maintainer did not hear them first-hand; the relay is kept in the two sessions' conversations and in no file.
- **[S2] The lock's ages:** `build/evidence/hold-third-party-supply-24-hours/uv-lock-ages.txt`, written by `build/evidence/hold-third-party-supply-72-hours/uv-lock-ages.py` from the `upload-time` of each artifact in `uv.lock` at `4893228`: 58 packages with upload times; the youngest are `filelock` 4.2.11 (46.8 h), `mlx-audio` 0.6.6 (60.4 h) and `httpx2` 2.16.2 (67.2 h).
- **[S3] uv's reference:** <https://docs.astral.sh/uv/reference/settings/>, the setting `exclude-newer`, read on 19 November 2026: it accepts an RFC 3339 timestamp, a "friendly" duration (`24 hours`, `1 week`, `30 days`) or an ISO 8601 duration; durations are resolved to a fixed number of seconds with a day of 24 hours; the cutoff is compared with each distribution file's upload time. The page states no uv version; this repository pins uv 0.13.9.
- **[S4] The relock:** `build/evidence/hold-third-party-supply-24-hours/relock-in-a-scratch-clone.log`, `uv-lock.log` and `lines-and-lock.diff`: a clone of `4893228`, the three lines written, `uv lock` at 13:21:22 CST ("Resolving despite existing lockfile due to addition of global exclude newer"), the comparison of the two locks' packages and artifacts, `uv lock --check --offline` at 13:21:28 and 13:22:33, `mise run bootstrap`, `mise run check:dependencies`, and each reader's answer under Mise (`minimum_release_age` 24h; npm's `min-release-age` 1 from the repository's own file; `mise install --locked` with every tool installed). Beside them: `uv-version.txt` (uv 0.13.9, the pinned one, under Mise in that clone), and `markdown-check.txt` and `openspec-validate.txt`, the repository's Markdown check and the strict validation of this Change in the clone with the Changelog's entry and the artifacts in place.
- **[S5] The Change before this one:** `openspec/changes/archive/2026-11-19-hold-third-party-supply-72-hours/design.md`: decision 1 (each resolver's own configuration; no test or script holds the age), decision 2 (no exclusion declared here), decision 3 (uv's line with its relock in one commit, since a lock check refuses differing options) and decision 4 (npm's file and its unit of days), with the measurements they rest on (a locked exact version installs under the age; a new resolve of a younger version is refused).
